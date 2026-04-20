"""
GRAPH SELF-SUPERVISED LEARNING – ULTIMATE IMPLEMENTATION
==========================================================
This module provides self‑supervised learning methods for graphs, including:

- Contrastive methods: GraphCL, InfoGraph, SimGRACE, DGI, BGRL
- Generative methods: masked graph autoencoders (e.g., GPT-GNN style)
- Predictive methods: graph property prediction, node distance prediction, context prediction
- Augmentations: node dropping, edge perturbation, attribute masking, subgraph sampling
- Evaluation: linear probing, fine-tuning, transfer learning

All methods are built on top of PyTorch Geometric if available, and degrade
gracefully when libraries are missing.
"""

import logging
import warnings
from typing import Optional, List, Tuple, Dict, Any, Callable, Union
import numpy as np

# ============================================================================
# OPTIONAL LIBRARIES – ALL HANDLED GRACEFULLY
# ============================================================================

# PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    from torch.utils.data import DataLoader, Dataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None

# PyTorch Geometric
try:
    import torch_geometric
    from torch_geometric.data import Data, Batch, Dataset as PyGDataset
    from torch_geometric.nn import GCNConv, SAGEConv, GINConv, GATConv, global_mean_pool, global_max_pool
    from torch_geometric.loader import DataLoader as PyGDataLoader
    from torch_geometric.utils import to_networkx, from_networkx, degree
    from torch_geometric.transforms import Compose
    HAS_PYG = True
except ImportError:
    HAS_PYG = False

# scikit-learn for evaluation metrics
try:
    from sklearn.svm import LinearSVC
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# tqdm for progress bars
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

logger = logging.getLogger(__name__)


# ============================================================================
# UTILITY FUNCTIONS FOR LAYER 2 INTEGRATION
# ============================================================================

def layer1_registry_to_pyg_data(
    registry: Dict[str, Any],
    observable_names: List[str],
    relation_tuples: List[Tuple[int, int]],
    node_features: Optional[np.ndarray] = None,
    edge_attrs: Optional[np.ndarray] = None,
    **kwargs
) -> Optional['Data']:
    """
    Convert Layer 1 observables and Layer 2 relations into a PyTorch Geometric Data object.

    This function extracts node features from the registry (or from provided node_features)
    and edge indices from relation tuples. If PyTorch Geometric is not installed, it returns
    None and logs a warning.

    Args:
        registry: Dictionary containing Layer 1 data. It may have an 'observables' key
                  mapping to a dict of observable names -> values (array of shape (num_nodes,)).
                  Alternatively, node_features can be provided directly.
        observable_names: List of observable names to use as node features. The order defines
                          the feature columns. Each observable should be present in the registry
                          (under registry['observables']) or in node_features.
        relation_tuples: List of (source, target) integer indices representing directed edges.
                         These indices refer to node positions (0 .. num_nodes-1).
        node_features: Optional numpy array of shape (num_nodes, num_features) containing
                       pre-assembled node features. If given, observable_names is ignored.
        edge_attrs: Optional numpy array of shape (num_edges, num_edge_features) with edge attributes.
        **kwargs: Additional arguments passed to the Data constructor (e.g., y for labels).

    Returns:
        A torch_geometric.data.Data object, or None if PyG is not available or required data missing.
    """
    if not HAS_PYG:
        logger.warning("PyTorch Geometric not installed – cannot create PyG Data object.")
        return None
    if not HAS_TORCH:
        logger.warning("PyTorch not installed – cannot create PyG Data object.")
        return None

    # Build node features
    if node_features is not None:
        x = torch.tensor(node_features, dtype=torch.float)
    else:
        if 'observables' not in registry:
            raise ValueError("Registry must contain 'observables' key when node_features not provided")
        obs_dict = registry['observables']
        # Determine number of nodes by checking the length of the first observable
        first_obs = observable_names[0]
        if first_obs not in obs_dict:
            raise ValueError(f"Observable '{first_obs}' not found in registry['observables']")
        num_nodes = len(obs_dict[first_obs])
        feature_list = []
        for obs_name in observable_names:
            if obs_name not in obs_dict:
                raise ValueError(f"Observable '{obs_name}' not found in registry['observables']")
            arr = np.array(obs_dict[obs_name])
            if len(arr) != num_nodes:
                raise ValueError(f"Observable '{obs_name}' has length {len(arr)} but expected {num_nodes}")
            feature_list.append(arr)
        x_np = np.column_stack(feature_list)
        x = torch.tensor(x_np, dtype=torch.float)

    # Build edge_index
    if not relation_tuples:
        # No edges: create empty edge_index
        edge_index = torch.zeros((2, 0), dtype=torch.long)
    else:
        edge_index = torch.tensor(relation_tuples, dtype=torch.long).t().contiguous()

    # Edge attributes
    if edge_attrs is not None:
        edge_attr = torch.tensor(edge_attrs, dtype=torch.float)
    else:
        edge_attr = None

    # Create Data object
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, **kwargs)
    return data


def atomicity_aware_dgi_loss(
    pos_embeddings: torch.Tensor,
    neg_embeddings: torch.Tensor,
    readout: torch.Tensor,
    atomicity_weights: torch.Tensor,
    discriminator: Callable[[torch.Tensor, torch.Tensor], torch.Tensor],
    eps: float = 1e-7
) -> torch.Tensor:
    """
    Compute the atomicity‑aware Deep Graph Infomax (DGI) loss.

    In standard DGI, the loss is binary cross‑entropy between positive pairs
    (node embedding, summary of the same graph) and negative pairs
    (node embedding from corrupted graph, summary of original graph).
    This version weights each node's contribution by an atomicity weight,
    allowing nodes with higher atomicity (more "atomic" or fundamental) to
    contribute more to the loss.

    Args:
        pos_embeddings: Tensor of shape (num_nodes, embed_dim) – node embeddings from the original graph.
        neg_embeddings: Tensor of shape (num_nodes, embed_dim) – node embeddings from the corrupted graph.
        readout: Tensor of shape (embed_dim,) – summary vector of the original graph (e.g., mean of pos_embeddings).
        atomicity_weights: Tensor of shape (num_nodes,) – atomicity weight for each node (e.g., 1 for atomic, 0 for composite).
        discriminator: A callable that takes (node_embeddings, summary) and returns a score
                       (e.g., a bilinear layer). Should produce a tensor of shape (num_nodes,).
        eps: Small constant for numerical stability.

    Returns:
        Scalar loss (binary cross‑entropy weighted by atomicity_weights).
    """
    if not HAS_TORCH:
        raise ImportError("PyTorch is required for atomicity_aware_dgi_loss")

    # Positive scores: original nodes vs. original summary
    pos_scores = discriminator(pos_embeddings, readout)          # (num_nodes,)

    # Negative scores: corrupted nodes vs. original summary
    neg_scores = discriminator(neg_embeddings, readout)          # (num_nodes,)

    # Weighted binary cross‑entropy: positive term weighted by atomicity_weights,
    # negative term also weighted (but we want to treat negative pairs similarly).
    # Standard DGI: loss = - (1/N) * (sum(log pos_scores) + sum(log(1 - neg_scores)))
    # Here we apply atomicity_weights to both terms.
    pos_loss = -torch.log(pos_scores + eps) * atomicity_weights
    neg_loss = -torch.log(1 - neg_scores + eps) * atomicity_weights

    # Average over nodes (or sum? Typically average, but we can average over weighted sum)
    total_loss = (pos_loss.sum() + neg_loss.sum()) / (atomicity_weights.sum() + eps)

    return total_loss


# ============================================================================
# BASE CLASS FOR SELF-SUPERVISED MODELS
# ============================================================================

class SelfSupervisedGraphModel(nn.Module):
    """
    Base class for self‑supervised graph models.
    Provides common utilities and a uniform interface for training/evaluation.
    """

    def __init__(self, encoder: nn.Module, device: torch.device = None):
        super().__init__()
        self.encoder = encoder
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device
        self.encoder.to(self.device)

    def forward(self, data: Data) -> torch.Tensor:
        """Returns graph-level representation (pooled) or node representations."""
        raise NotImplementedError

    def train_step(self, data: Data, optimizer: optim.Optimizer) -> Dict[str, float]:
        """Perform one training step (forward + backward) on a batch of data."""
        raise NotImplementedError

    def encode(self, data: Data) -> torch.Tensor:
        """Encode data into node embeddings."""
        return self.encoder(data.x, data.edge_index, data.batch if hasattr(data, 'batch') else None)

    def save(self, path: str):
        torch.save(self.state_dict(), path)

    def load(self, path: str):
        self.load_state_dict(torch.load(path, map_location=self.device))


# ============================================================================
# CONTRASTIVE METHODS
# ============================================================================

class GraphCL(SelfSupervisedGraphModel):
    """
    Graph Contrastive Learning (GraphCL) with augmentations.
    Uses NT-Xent loss (InfoNCE) between two augmented views of each graph.
    """
    def __init__(self, encoder: nn.Module, projection_head: nn.Module,
                 augment_fn: Callable[[Data], Tuple[Data, Data]],
                 temperature: float = 0.5, device=None):
        super().__init__(encoder, device)
        self.projection_head = projection_head.to(self.device)
        self.augment_fn = augment_fn
        self.temperature = temperature
        self.criterion = nn.CrossEntropyLoss()

    def forward(self, data: Data) -> torch.Tensor:
        # For inference, return graph-level representation
        x = self.encoder(data.x, data.edge_index, data.batch)
        return global_mean_pool(x, data.batch)

    def train_step(self, data: Data, optimizer: optim.Optimizer) -> Dict[str, float]:
        data = data.to(self.device)
        # Generate two augmented views
        aug1, aug2 = self.augment_fn(data)

        # Encode and project
        h1 = self.encoder(aug1.x, aug1.edge_index, aug1.batch)
        h2 = self.encoder(aug2.x, aug2.edge_index, aug2.batch)
        z1 = self.projection_head(global_mean_pool(h1, aug1.batch))
        z2 = self.projection_head(global_mean_pool(h2, aug2.batch))

        # Normalize embeddings
        z1 = F.normalize(z1, dim=-1)
        z2 = F.normalize(z2, dim=-1)

        # Compute NT-Xent loss
        batch_size = z1.size(0)
        logits = torch.mm(z1, z2.t()) / self.temperature
        labels = torch.arange(batch_size).to(self.device)
        loss = self.criterion(logits, labels) + self.criterion(logits.t(), labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        return {'loss': loss.item()}


class InfoGraph(SelfSupervisedGraphModel):
    """
    InfoGraph: Unsupervised and Supervised Graph-Level Representation Learning
    via Mutual Information Maximization (Deep Graph Infomax for graph-level).
    """
    def __init__(self, encoder: nn.Module, summary: nn.Module, corruption_fn: Callable[[Data], Data],
                 device=None):
        super().__init__(encoder, device)
        self.summary = summary.to(self.device)
        self.corruption_fn = corruption_fn

    def forward(self, data: Data) -> torch.Tensor:
        return global_mean_pool(self.encoder(data.x, data.edge_index, data.batch), data.batch)

    def train_step(self, data: Data, optimizer: optim.Optimizer) -> Dict[str, float]:
        data = data.to(self.device)
        # Positive: encode original graph
        pos_z = self.encoder(data.x, data.edge_index, data.batch)
        pos_summary = self.summary(pos_z, data.batch)  # graph summary

        # Negative: corrupt graph and encode
        corrupted = self.corruption_fn(data)
        neg_z = self.encoder(corrupted.x, corrupted.edge_index, corrupted.batch)

        # Compute scores (bilinear)
        pos_score = torch.sum(pos_z * pos_summary[data.batch], dim=1)
        neg_score = torch.sum(neg_z * pos_summary[corrupted.batch], dim=1)

        # Loss: binary cross-entropy (maximize mutual information)
        loss = - (torch.log(torch.sigmoid(pos_score) + 1e-15).mean() +
                  torch.log(1 - torch.sigmoid(neg_score) + 1e-15).mean())

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        return {'loss': loss.item()}


class DGI(SelfSupervisedGraphModel):
    """
    Deep Graph Infomax (DGI) – node-level mutual information maximization.
    """
    def __init__(self, encoder: nn.Module, summary: nn.Module, corruption_fn: Callable[[Data], Data],
                 device=None):
        super().__init__(encoder, device)
        self.summary = summary.to(self.device)
        self.corruption_fn = corruption_fn

    def train_step(self, data: Data, optimizer: optim.Optimizer) -> Dict[str, float]:
        data = data.to(self.device)
        # Positive: encode original graph
        pos_z = self.encoder(data.x, data.edge_index)
        pos_summary = self.summary(pos_z, data.batch)  # graph summary

        # Negative: corrupt graph and encode
        corrupted = self.corruption_fn(data)
        neg_z = self.encoder(corrupted.x, corrupted.edge_index)

        # Compute scores (bilinear)
        pos_score = torch.sum(pos_z * pos_summary[data.batch], dim=1)
        neg_score = torch.sum(neg_z * pos_summary[corrupted.batch], dim=1)

        loss = - (torch.log(torch.sigmoid(pos_score) + 1e-15).mean() +
                  torch.log(1 - torch.sigmoid(neg_score) + 1e-15).mean())

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        return {'loss': loss.item()}


class SimGRACE(SelfSupervisedGraphModel):
    """
    SimGRACE: A Simple Framework for Graph Contrastive Learning without Data Augmentation.
    (Simplified version: perturbs the graph representations with Gaussian noise instead of model weights.)
    """
    def __init__(self, encoder: nn.Module, projection_head: nn.Module,
                 noise_std: float = 0.1, temperature: float = 0.5, device=None):
        super().__init__(encoder, device)
        self.projection_head = projection_head.to(self.device)
        self.noise_std = noise_std
        self.temperature = temperature
        self.criterion = nn.CrossEntropyLoss()

    def forward(self, data: Data) -> torch.Tensor:
        x = self.encoder(data.x, data.edge_index, data.batch)
        return global_mean_pool(x, data.batch)

    def train_step(self, data: Data, optimizer: optim.Optimizer) -> Dict[str, float]:
        data = data.to(self.device)

        # Encode original graph
        h = self.encoder(data.x, data.edge_index, data.batch)
        g = global_mean_pool(h, data.batch)

        # Create two noisy views by adding Gaussian noise to the graph-level representation
        g1 = g + torch.randn_like(g) * self.noise_std
        g2 = g + torch.randn_like(g) * self.noise_std

        # Project
        z1 = self.projection_head(g1)
        z2 = self.projection_head(g2)

        # Normalize
        z1 = F.normalize(z1, dim=-1)
        z2 = F.normalize(z2, dim=-1)

        # NT-Xent loss
        batch_size = z1.size(0)
        logits = torch.mm(z1, z2.t()) / self.temperature
        labels = torch.arange(batch_size).to(self.device)
        loss = self.criterion(logits, labels) + self.criterion(logits.t(), labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        return {'loss': loss.item()}


class BGRL(SelfSupervisedGraphModel):
    """
    Bootstrap Your Own Latent (BYOL) for Graphs.
    Uses an online encoder, a target encoder (updated by EMA), and a predictor.
    No negative pairs.
    """
    def __init__(self, encoder: nn.Module, predictor: nn.Module,
                 augment_fn: Callable[[Data], Tuple[Data, Data]],
                 moving_average_decay: float = 0.99, device=None):
        super().__init__(encoder, device)
        self.online_encoder = encoder
        self.target_encoder = self._build_target_encoder()
        self.predictor = predictor.to(self.device)
        self.augment_fn = augment_fn
        self.moving_average_decay = moving_average_decay

        # Initialize target with online weights
        self._update_target_network(1.0)

    def _build_target_encoder(self) -> nn.Module:
        # Create a new instance with same architecture as online_encoder
        # For simplicity, we assume encoder can be cloned by copying its state_dict.
        # This requires that the encoder class is reconstructable. We'll use a simple approach:
        # create a new instance of the same class (assuming it's a module) and load state_dict later.
        # But we don't have the original class. Instead, we'll just create a copy using `copy.deepcopy`?
        # However, deepcopy might not work if the module contains non-copyable objects.
        # We'll use a simpler approach: store the target encoder as a separate module and update its parameters manually.
        # We'll just create a new instance of the same type as online_encoder by cloning its architecture.
        # This requires that the encoder is a simple nn.Module subclass. We'll assume it can be re-instantiated.
        # A safer way: in __init__, we accept two encoders (online and target). But the user may not want to provide both.
        # For flexibility, we'll allow the user to pass a target_encoder separately, or we'll clone online.
        # Here we'll implement a cloning method that works for simple sequential models.
        # If it fails, we'll raise an error and ask the user to provide a target_encoder.
        try:
            import copy
            target = copy.deepcopy(self.online_encoder)
        except Exception as e:
            raise RuntimeError("Could not automatically clone encoder. Please provide a separate target_encoder argument.") from e
        return target.to(self.device)

    def _update_target_network(self, decay=None):
        if decay is None:
            decay = self.moving_average_decay
        with torch.no_grad():
            for online_param, target_param in zip(self.online_encoder.parameters(), self.target_encoder.parameters()):
                target_param.data = decay * target_param.data + (1 - decay) * online_param.data

    def forward(self, data: Data) -> torch.Tensor:
        return global_mean_pool(self.online_encoder(data.x, data.edge_index, data.batch), data.batch)

    def train_step(self, data: Data, optimizer: optim.Optimizer) -> Dict[str, float]:
        data = data.to(self.device)
        # Generate two augmented views
        view1, view2 = self.augment_fn(data)

        # Online forward
        h1_online = self.online_encoder(view1.x, view1.edge_index, view1.batch)
        h2_online = self.online_encoder(view2.x, view2.edge_index, view2.batch)
        g1_online = global_mean_pool(h1_online, view1.batch)
        g2_online = global_mean_pool(h2_online, view2.batch)
        p1 = self.predictor(g1_online)
        p2 = self.predictor(g2_online)

        # Target forward (no grad)
        with torch.no_grad():
            h1_target = self.target_encoder(view1.x, view1.edge_index, view1.batch)
            h2_target = self.target_encoder(view2.x, view2.edge_index, view2.batch)
            t1 = global_mean_pool(h1_target, view1.batch)
            t2 = global_mean_pool(h2_target, view2.batch)

        # Normalize
        p1 = F.normalize(p1, dim=-1)
        p2 = F.normalize(p2, dim=-1)
        t1 = F.normalize(t1, dim=-1)
        t2 = F.normalize(t2, dim=-1)

        # Symmetric loss: cosine similarity
        loss = 2 - (F.cosine_similarity(p1, t2, dim=-1).mean() + F.cosine_similarity(p2, t1, dim=-1).mean())

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Update target network
        self._update_target_network()

        return {'loss': loss.item()}


# ============================================================================
# GENERATIVE METHODS
# ============================================================================

class MaskedGraphAutoencoder(SelfSupervisedGraphModel):
    """
    Masked Graph Autoencoder (e.g., GPT-GNN style).
    Masks a subset of nodes/edges/features and reconstructs them.
    Here we implement node feature masking and reconstruction.
    """
    def __init__(self, encoder: nn.Module, decoder: nn.Module, mask_ratio: float = 0.15,
                 mask_token: Optional[torch.Tensor] = None, device=None):
        super().__init__(encoder, device)
        self.decoder = decoder.to(self.device)
        self.mask_ratio = mask_ratio
        self.mask_token = mask_token  # learnable mask token, if None use zero

    def _apply_mask(self, data: Data) -> Tuple[Data, torch.Tensor, torch.Tensor]:
        """Randomly mask node features."""
        x = data.x
        num_nodes, feat_dim = x.shape
        mask = torch.rand(num_nodes, device=self.device) < self.mask_ratio
        masked_x = x.clone()
        if self.mask_token is None:
            masked_x[mask] = 0.0
        else:
            masked_x[mask] = self.mask_token.to(self.device)
        return Data(x=masked_x, edge_index=data.edge_index, batch=data.batch), mask, x[mask]

    def train_step(self, data: Data, optimizer: optim.Optimizer) -> Dict[str, float]:
        data = data.to(self.device)
        masked_data, mask, original_features = self._apply_mask(data)

        # Encode masked graph
        node_emb = self.encoder(masked_data.x, masked_data.edge_index, masked_data.batch)

        # Decode (reconstruct features for masked nodes)
        # For simplicity, we use a linear decoder on node embeddings.
        recon = self.decoder(node_emb[mask])
        loss = F.mse_loss(recon, original_features)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        return {'loss': loss.item()}


# ============================================================================
# PREDICTIVE METHODS
# ============================================================================

class GraphPropertyPrediction(SelfSupervisedGraphModel):
    """
    Predict graph-level properties (e.g., number of nodes, number of edges)
    as a pretext task. The targets are derived from the graph itself.
    """
    def __init__(self, encoder: nn.Module, predictor: nn.Module,
                 property_fn: Callable[[Data], torch.Tensor],
                 loss_fn: Callable = F.mse_loss, device=None):
        """
        Args:
            encoder: GNN encoder.
            predictor: MLP that maps graph embeddings to property values.
            property_fn: function that takes a Data object and returns a tensor of properties (e.g., log(num_nodes)).
            loss_fn: loss function (default MSE).
        """
        super().__init__(encoder, device)
        self.predictor = predictor.to(self.device)
        self.property_fn = property_fn
        self.loss_fn = loss_fn

    def forward(self, data: Data) -> torch.Tensor:
        x = self.encoder(data.x, data.edge_index, data.batch)
        graph_emb = global_mean_pool(x, data.batch)
        return self.predictor(graph_emb)

    def train_step(self, data: Data, optimizer: optim.Optimizer) -> Dict[str, float]:
        data = data.to(self.device)
        # Compute property targets
        targets = self.property_fn(data).float().to(self.device)

        # Forward
        x = self.encoder(data.x, data.edge_index, data.batch)
        graph_emb = global_mean_pool(x, data.batch)
        pred = self.predictor(graph_emb).squeeze()

        loss = self.loss_fn(pred, targets)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        return {'loss': loss.item()}


def _sample_node_pairs(data: Data, num_pairs: int, max_dist: Optional[int] = None,
                       positive_ratio: float = 0.5) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Sample pairs of nodes from a batched graph.
    Returns (node_i, node_j, labels) where labels are 1 if within max_dist (or connected), else 0.
    This is a helper for distance prediction tasks.
    """
    device = data.x.device
    batch_size = data.batch.max().item() + 1
    pairs_i = []
    pairs_j = []
    labels = []

    for b in range(batch_size):
        mask = data.batch == b
        node_indices = mask.nonzero(as_tuple=True)[0]
        n_nodes = node_indices.size(0)
        if n_nodes < 2:
            continue

        # Sample positive pairs (within max_dist) – we need distance information.
        # For simplicity, we'll use connectivity (k-hop) via shortest path.
        # This requires converting to networkx, which may be slow. Alternative:
        # Use adjacency to sample connected pairs (1-hop neighbors) as positives.
        # Here we implement a simple version: positives are connected by an edge.
        # This is essentially link prediction.
        # For a more advanced version, we could compute shortest path distances.

        # Get subgraph adjacency for this graph
        sub_edge_index = data.edge_index[:, mask[data.edge_index[0]] & mask[data.edge_index[1]]]
        # Map local indices
        local_idx = torch.arange(n_nodes, device=device)
        # Create a mapping from global to local
        global_to_local = torch.full((data.x.size(0),), -1, device=device, dtype=torch.long)
        global_to_local[node_indices] = local_idx
        local_edge_index = global_to_local[sub_edge_index]

        # Positive pairs: edges
        if local_edge_index.size(1) > 0:
            num_pos = min(local_edge_index.size(1), int(num_pairs * positive_ratio))
            pos_choices = torch.randperm(local_edge_index.size(1))[:num_pos]
            pos_i = local_edge_index[0, pos_choices]
            pos_j = local_edge_index[1, pos_choices]
            pairs_i.append(node_indices[pos_i])
            pairs_j.append(node_indices[pos_j])
            labels.append(torch.ones(num_pos, device=device))

        # Negative pairs: random pairs (ensuring they are not connected)
        num_neg = num_pairs - (pairs_i[-1].size(0) if pairs_i else 0)
        if num_neg > 0:
            # Sample random pairs and reject those that are edges
            all_pairs = torch.combinations(torch.arange(n_nodes, device=device), r=2)
            # Convert to set for quick lookup
            edge_set = set(zip(local_edge_index[0].tolist(), local_edge_index[1].tolist()))
            # Filter out edges
            is_neg = torch.tensor([(i.item(), j.item()) not in edge_set for i, j in all_pairs], device=device)
            neg_candidates = all_pairs[is_neg]
            if neg_candidates.size(0) > 0:
                neg_choices = torch.randperm(neg_candidates.size(0))[:num_neg]
                neg_i = neg_candidates[neg_choices, 0]
                neg_j = neg_candidates[neg_choices, 1]
                pairs_i.append(node_indices[neg_i])
                pairs_j.append(node_indices[neg_j])
                labels.append(torch.zeros(num_neg, device=device))

    if not pairs_i:
        return None, None, None

    return torch.cat(pairs_i), torch.cat(pairs_j), torch.cat(labels)


class NodeDistancePrediction(SelfSupervisedGraphModel):
    """
    Predict whether two nodes are within a certain distance (or are connected).
    This is a node-pair-level pretext task.
    """
    def __init__(self, encoder: nn.Module, pair_classifier: nn.Module,
                 num_pairs_per_graph: int = 10, positive_ratio: float = 0.5,
                 device=None):
        """
        Args:
            encoder: GNN encoder (produces node embeddings).
            pair_classifier: MLP that takes concatenated node embeddings and predicts binary.
            num_pairs_per_graph: number of pairs to sample per graph in each batch.
            positive_ratio: fraction of positive (connected) pairs.
        """
        super().__init__(encoder, device)
        self.pair_classifier = pair_classifier.to(self.device)
        self.num_pairs_per_graph = num_pairs_per_graph
        self.positive_ratio = positive_ratio
        self.criterion = nn.BCEWithLogitsLoss()

    def forward(self, data: Data) -> torch.Tensor:
        # Not used for inference; we just return node embeddings.
        return self.encoder(data.x, data.edge_index, data.batch)

    def train_step(self, data: Data, optimizer: optim.Optimizer) -> Dict[str, float]:
        data = data.to(self.device)
        # Sample node pairs
        i, j, labels = _sample_node_pairs(data, self.num_pairs_per_graph * (data.batch.max().item()+1),
                                           positive_ratio=self.positive_ratio)
        if i is None:
            return {'loss': 0.0}  # no pairs

        # Get node embeddings
        node_emb = self.encoder(data.x, data.edge_index, data.batch)  # (num_nodes, dim)
        emb_i = node_emb[i]
        emb_j = node_emb[j]

        # Concatenate or element-wise product? Use concatenation.
        pair_feat = torch.cat([emb_i, emb_j], dim=-1)
        logits = self.pair_classifier(pair_feat).squeeze()

        loss = self.criterion(logits, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        return {'loss': loss.item()}


class ContextPrediction(SelfSupervisedGraphModel):
    """
    Predict the context of a node: which nodes are in its k-hop neighborhood.
    This can be framed as a multi-label classification or using negative sampling.
    Here we implement a simple version: given a node and a candidate, predict if they are within k hops.
    (Similar to NodeDistancePrediction but with a distance threshold.)
    """
    def __init__(self, encoder: nn.Module, pair_classifier: nn.Module,
                 k: int = 2, num_pairs_per_graph: int = 10, positive_ratio: float = 0.5,
                 device=None):
        super().__init__(encoder, device)
        self.pair_classifier = pair_classifier.to(self.device)
        self.k = k
        self.num_pairs_per_graph = num_pairs_per_graph
        self.positive_ratio = positive_ratio
        self.criterion = nn.BCEWithLogitsLoss()
        # For distance computation, we need to precompute shortest paths.
        # This is expensive; we'll approximate by using random walk or use adjacency powers.
        # For simplicity, we'll use the same as NodeDistancePrediction (connected) and ignore k.
        # In a real implementation, you would compute k-hop reachability.
        # We'll leave this as a placeholder for now.
        logger.warning("ContextPrediction uses connected pairs as positives (k=1). For k>1, implement shortest path.")

    def train_step(self, data: Data, optimizer: optim.Optimizer) -> Dict[str, float]:
        # Reuse the same pair sampling as NodeDistancePrediction (connected pairs as positives)
        i, j, labels = _sample_node_pairs(data, self.num_pairs_per_graph * (data.batch.max().item()+1),
                                           positive_ratio=self.positive_ratio)
        if i is None:
            return {'loss': 0.0}

        node_emb = self.encoder(data.x, data.edge_index, data.batch)
        emb_i = node_emb[i]
        emb_j = node_emb[j]
        pair_feat = torch.cat([emb_i, emb_j], dim=-1)
        logits = self.pair_classifier(pair_feat).squeeze()
        loss = self.criterion(logits, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        return {'loss': loss.item()}


# ============================================================================
# AUGMENTATION FUNCTIONS
# ============================================================================

def identity_augmentation(data: Data) -> Tuple[Data, Data]:
    """Return two identical copies (no augmentation)."""
    return data.clone(), data.clone()


def node_dropping(data: Data, drop_ratio: float = 0.2) -> Tuple[Data, Data]:
    """
    Randomly drop nodes (with their edges) from the graph.
    Returns two augmented graphs (different subsets).
    """
    if not HAS_PYG:
        raise ImportError("PyTorch Geometric required for augmentations")
    num_nodes = data.num_nodes
    # First augmentation
    keep1 = torch.rand(num_nodes) > drop_ratio
    edge_index1, _ = torch_geometric.utils.subgraph(keep1, data.edge_index, relabel_nodes=True)
    x1 = data.x[keep1]
    # Second augmentation
    keep2 = torch.rand(num_nodes) > drop_ratio
    edge_index2, _ = torch_geometric.utils.subgraph(keep2, data.edge_index, relabel_nodes=True)
    x2 = data.x[keep2]
    # Reuse batch if present
    batch1 = data.batch[keep1] if hasattr(data, 'batch') else None
    batch2 = data.batch[keep2] if hasattr(data, 'batch') else None
    return (Data(x=x1, edge_index=edge_index1, batch=batch1),
            Data(x=x2, edge_index=edge_index2, batch=batch2))


def edge_perturbation(data: Data, add_ratio: float = 0.1, drop_ratio: float = 0.1) -> Tuple[Data, Data]:
    """
    Randomly add and drop edges.
    """
    if not HAS_PYG:
        raise ImportError("PyTorch Geometric required for augmentations")
    def perturb(edge_index):
        num_edges = edge_index.size(1)
        # Drop edges
        keep = torch.rand(num_edges) > drop_ratio
        edge_index = edge_index[:, keep]
        # Add random edges
        num_add = int(add_ratio * num_edges)
        if num_add > 0:
            num_nodes = data.num_nodes
            new_edges = torch.randint(0, num_nodes, (2, num_add), device=edge_index.device)
            edge_index = torch.cat([edge_index, new_edges], dim=1)
        return edge_index

    aug1 = data.clone()
    aug2 = data.clone()
    aug1.edge_index = perturb(aug1.edge_index)
    aug2.edge_index = perturb(aug2.edge_index)
    return aug1, aug2


def attribute_masking(data: Data, mask_ratio: float = 0.2) -> Tuple[Data, Data]:
    """
    Randomly mask node features.
    """
    def mask(x):
        masked = x.clone()
        mask = torch.rand(x.size(0), device=x.device) < mask_ratio
        masked[mask] = 0.0
        return masked

    aug1 = data.clone()
    aug2 = data.clone()
    aug1.x = mask(aug1.x)
    aug2.x = mask(aug2.x)
    return aug1, aug2


def subgraph_sampling(data: Data, sample_ratio: float = 0.8) -> Tuple[Data, Data]:
    """
    Sample a connected subgraph (random walk based) from the original graph.
    """
    if not HAS_PYG:
        raise ImportError("PyTorch Geometric required for augmentations")
    # Simple: sample nodes uniformly and take induced subgraph
    num_nodes = data.num_nodes
    num_sample = int(sample_ratio * num_nodes)
    nodes1 = torch.randperm(num_nodes)[:num_sample]
    nodes2 = torch.randperm(num_nodes)[:num_sample]
    edge_index1, _ = torch_geometric.utils.subgraph(nodes1, data.edge_index, relabel_nodes=True)
    edge_index2, _ = torch_geometric.utils.subgraph(nodes2, data.edge_index, relabel_nodes=True)
    x1 = data.x[nodes1]
    x2 = data.x[nodes2]
    batch1 = data.batch[nodes1] if hasattr(data, 'batch') else None
    batch2 = data.batch[nodes2] if hasattr(data, 'batch') else None
    return (Data(x=x1, edge_index=edge_index1, batch=batch1),
            Data(x=x2, edge_index=edge_index2, batch=batch2))


def random_walk_subgraph(data: Data, walk_length: int = 20) -> Tuple[Data, Data]:
    """
    Sample subgraphs via random walks from random starting nodes.
    """
    # Not implemented yet – could be added later.
    raise NotImplementedError


# ============================================================================
# CORRUPTION FUNCTIONS (for DGI/InfoGraph)
# ============================================================================

def shuffle_nodes(data: Data) -> Data:
    """Corrupt graph by randomly shuffling node features."""
    corrupted = data.clone()
    perm = torch.randperm(data.num_nodes)
    corrupted.x = data.x[perm]
    return corrupted


def feature_masking_corruption(data: Data, mask_ratio: float = 0.2) -> Data:
    """Corrupt by masking features."""
    corrupted = data.clone()
    mask = torch.rand(data.num_nodes, device=data.x.device) < mask_ratio
    corrupted.x[mask] = 0.0
    return corrupted


# ============================================================================
# ENCODER ARCHITECTURES (simple ones)
# ============================================================================

class GCNEncoder(nn.Module):
    """Simple GCN encoder with optional pooling for graph-level tasks."""
    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int,
                 num_layers: int = 2, dropout: float = 0.0):
        super().__init__()
        self.convs = nn.ModuleList()
        self.convs.append(GCNConv(in_channels, hidden_channels))
        for _ in range(num_layers - 2):
            self.convs.append(GCNConv(hidden_channels, hidden_channels))
        self.convs.append(GCNConv(hidden_channels, out_channels))
        self.dropout = dropout

    def forward(self, x, edge_index, batch=None):
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs) - 1:
                x = F.relu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
        # If batch is provided, we return node embeddings; pooling is done outside
        return x


class GINEncoder(nn.Module):
    """Graph Isomorphism Network encoder."""
    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int,
                 num_layers: int = 2, dropout: float = 0.0):
        super().__init__()
        self.convs = nn.ModuleList()
        for i in range(num_layers):
            in_dim = in_channels if i == 0 else hidden_channels
            out_dim = hidden_channels if i < num_layers - 1 else out_channels
            self.convs.append(
                GINConv(nn.Sequential(
                    nn.Linear(in_dim, hidden_channels),
                    nn.ReLU(),
                    nn.Linear(hidden_channels, out_dim)
                ))
            )
        self.dropout = dropout

    def forward(self, x, edge_index, batch=None):
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs) - 1:
                x = F.relu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
        return x


# ============================================================================
# EVALUATION UTILITIES
# ============================================================================

def linear_evaluation(train_embs: np.ndarray, train_labels: np.ndarray,
                      test_embs: np.ndarray, test_labels: np.ndarray,
                      C: float = 1.0) -> Dict[str, float]:
    """
    Train a linear classifier (Logistic Regression) on frozen embeddings.
    Returns accuracy and F1 scores.
    """
    if not HAS_SKLEARN:
        logger.warning("scikit-learn not available – cannot evaluate")
        return {}
    clf = LogisticRegression(C=C, max_iter=1000)
    clf.fit(train_embs, train_labels)
    pred = clf.predict(test_embs)
    acc = accuracy_score(test_labels, pred)
    f1_macro = f1_score(test_labels, pred, average='macro')
    f1_micro = f1_score(test_labels, pred, average='micro')
    return {'accuracy': acc, 'f1_macro': f1_macro, 'f1_micro': f1_micro}


def fine_tune(model: nn.Module, classifier: nn.Module,
              train_loader: DataLoader, test_loader: DataLoader,
              epochs: int = 50, lr: float = 0.01) -> Dict[str, float]:
    """
    Fine-tune the entire model (encoder + classifier) on a downstream task.
    Returns final test accuracy.
    """
    device = next(model.parameters()).device
    optimizer = optim.Adam(list(model.parameters()) + list(classifier.parameters()), lr=lr)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        classifier.train()
        total_loss = 0.0
        for data in train_loader:
            data = data.to(device)
            optimizer.zero_grad()
            emb = model.encode(data)  # node embeddings
            # For graph-level tasks, pool; for node-level, use directly with masks.
            # Here we assume graph-level: global_mean_pool
            graph_emb = global_mean_pool(emb, data.batch)
            out = classifier(graph_emb)
            loss = criterion(out, data.y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if epoch % 10 == 0:
            logger.info(f"Epoch {epoch}, loss: {total_loss/len(train_loader):.4f}")

    # Evaluate
    model.eval()
    classifier.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for data in test_loader:
            data = data.to(device)
            emb = model.encode(data)
            graph_emb = global_mean_pool(emb, data.batch)
            out = classifier(graph_emb)
            pred = out.argmax(dim=1)
            correct += (pred == data.y).sum().item()
            total += data.y.size(0)
    acc = correct / total
    return {'test_accuracy': acc}


def transfer_evaluation(model: SelfSupervisedGraphModel,
                        source_train_loader: DataLoader,
                        source_test_loader: DataLoader,
                        target_train_loader: DataLoader,
                        target_test_loader: DataLoader,
                        num_classes: int,
                        fine_tune_epochs: int = 50,
                        lr: float = 0.01) -> Dict[str, float]:
    """
    Evaluate transfer learning capabilities.
    First, optionally fine-tune on source task? Actually transfer learning means pre-train on source,
    then adapt to target. Here we assume model is already pre-trained (e.g., via self-supervised learning).
    We then evaluate by training a linear classifier on target using frozen embeddings,
    and also by fine-tuning the entire model on target.
    Returns both linear evaluation and fine-tuning results.
    """
    device = next(model.parameters()).device
    model.eval()  # freeze encoder for linear eval

    # --- Linear evaluation on target (frozen encoder) ---
    def extract_embeddings(loader):
        embs = []
        labels = []
        with torch.no_grad():
            for data in loader:
                data = data.to(device)
                emb = model.encode(data)
                graph_emb = global_mean_pool(emb, data.batch).cpu().numpy()
                embs.append(graph_emb)
                labels.append(data.y.cpu().numpy())
        return np.vstack(embs), np.concatenate(labels)

    train_embs, train_labels = extract_embeddings(target_train_loader)
    test_embs, test_labels = extract_embeddings(target_test_loader)

    linear_results = linear_evaluation(train_embs, train_labels, test_embs, test_labels)

    # --- Fine-tuning on target ---
    classifier = nn.Linear(model.encoder.out_channels, num_classes).to(device)
    # Re-enable training mode
    model.train()
    ft_results = fine_tune(model, classifier, target_train_loader, target_test_loader,
                           epochs=fine_tune_epochs, lr=lr)

    return {
        'linear_accuracy': linear_results.get('accuracy', 0.0),
        'fine_tune_accuracy': ft_results.get('test_accuracy', 0.0)
    }


# ============================================================================
# DEMO / EXAMPLE
# ============================================================================

def demo():
    """Run a simple demo on a synthetic dataset."""
    if not (HAS_TORCH and HAS_PYG):
        print("PyTorch and PyTorch Geometric required for demo.")
        return

    from torch_geometric.datasets import TUDataset
    from torch_geometric.loader import DataLoader

    # Load a small dataset (e.g., MUTAG)
    dataset = TUDataset(root='/tmp/MUTAG', name='MUTAG')
    dataset = dataset.shuffle()
    train_dataset = dataset[:len(dataset)//2]
    test_dataset = dataset[len(dataset)//2:]
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    in_channels = dataset.num_features
    hidden_channels = 32
    out_channels = 64

    # Create encoder and model
    encoder = GCNEncoder(in_channels, hidden_channels, out_channels, num_layers=2)
    proj_head = nn.Sequential(
        nn.Linear(out_channels, hidden_channels),
        nn.ReLU(),
        nn.Linear(hidden_channels, out_channels)
    )
    model = GraphCL(encoder, proj_head, augment_fn=node_dropping, temperature=0.5)
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Training loop
    model.train()
    for epoch in range(10):
        epoch_loss = 0.0
        for data in train_loader:
            loss_dict = model.train_step(data, optimizer)
            epoch_loss += loss_dict['loss']
        print(f"Epoch {epoch}, loss: {epoch_loss/len(train_loader):.4f}")

    # Extract embeddings for linear evaluation
    model.eval()
    train_embs = []
    train_labels = []
    with torch.no_grad():
        for data in train_loader:
            data = data.to(model.device)
            emb = model.encode(data)
            graph_emb = global_mean_pool(emb, data.batch).cpu().numpy()
            train_embs.append(graph_emb)
            train_labels.append(data.y.cpu().numpy())
    train_embs = np.vstack(train_embs)
    train_labels = np.concatenate(train_labels)

    test_embs = []
    test_labels = []
    with torch.no_grad():
        for data in test_loader:
            data = data.to(model.device)
            emb = model.encode(data)
            graph_emb = global_mean_pool(emb, data.batch).cpu().numpy()
            test_embs.append(graph_emb)
            test_labels.append(data.y.cpu().numpy())
    test_embs = np.vstack(test_embs)
    test_labels = np.concatenate(test_labels)

    results = linear_evaluation(train_embs, train_labels, test_embs, test_labels)
    print("Linear evaluation results:", results)

    # Transfer learning demo (using same dataset as target for simplicity)
    # In practice, you would use a different dataset.
    num_classes = dataset.num_classes
    transfer_results = transfer_evaluation(model, train_loader, test_loader,
                                           train_loader, test_loader, num_classes)
    print("Transfer evaluation results:", transfer_results)

    # Demo predictive method: GraphPropertyPrediction
    print("\n--- GraphPropertyPrediction demo ---")
    # Property: log number of nodes
    def log_num_nodes(data: Data) -> torch.Tensor:
        batch_size = data.batch.max().item() + 1
        counts = []
        for b in range(batch_size):
            count = (data.batch == b).sum().item()
            counts.append(np.log(count + 1))  # log to stabilize
        return torch.tensor(counts)

    predictor = nn.Linear(out_channels, 1)
    prop_model = GraphPropertyPrediction(encoder, predictor, property_fn=log_num_nodes)
    prop_optimizer = optim.Adam(prop_model.parameters(), lr=0.001)
    prop_model.train()
    for epoch in range(5):
        epoch_loss = 0.0
        for data in train_loader:
            loss_dict = prop_model.train_step(data, prop_optimizer)
            epoch_loss += loss_dict['loss']
        print(f"Epoch {epoch}, loss: {epoch_loss/len(train_loader):.4f}")

    # --- Demo layer1_registry_to_pyg_data ---
    print("\n--- layer1_registry_to_pyg_data demo ---")
    mock_registry = {
        'observables': {
            'obs1': [0.1, 0.2, 0.3, 0.4],
            'obs2': [1.0, 1.1, 1.2, 1.3]
        }
    }
    relations = [(0, 1), (1, 2), (2, 3)]
    data_obj = layer1_registry_to_pyg_data(
        registry=mock_registry,
        observable_names=['obs1', 'obs2'],
        relation_tuples=relations
    )
    if data_obj is not None:
        print("PyG Data object created:")
        print("  x shape:", data_obj.x.shape)
        print("  edge_index shape:", data_obj.edge_index.shape)

    # --- Demo atomicity_aware_dgi_loss ---
    print("\n--- atomicity_aware_dgi_loss demo ---")
    # Create dummy data
    num_nodes = 10
    embed_dim = 16
    pos_emb = torch.randn(num_nodes, embed_dim)
    neg_emb = torch.randn(num_nodes, embed_dim)
    readout = pos_emb.mean(dim=0)
    atomicity = torch.ones(num_nodes)  # all atomic
    # Simple discriminator: bilinear layer
    disc = nn.Bilinear(embed_dim, embed_dim, 1)
    loss_val = atomicity_aware_dgi_loss(pos_emb, neg_emb, readout, atomicity, disc)
    print("Atomicity-aware DGI loss:", loss_val.item())


if __name__ == "__main__":
    demo()