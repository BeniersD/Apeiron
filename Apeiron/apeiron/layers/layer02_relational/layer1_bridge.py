"""
LAYER 1 BRIDGE – CONVERSIONS BETWEEN LAYER 1 AND LAYER 2
===========================================================
This module provides utility functions to convert Layer 1 data (observables, registries)
into formats suitable for Layer 2 processing.

Core functionalities:
- registry_to_graph: Build a NetworkX graph from a Layer 1 registry.
- similarity_matrix: Compute pairwise similarity/distance matrices.
- observable_to_vector: Convert observable data to a standard vector format.
- discretize_observable: Bin continuous values into discrete categories.
- normalize: Normalize observable vectors.
- extract_feature_matrix: Assemble a feature matrix from multiple observables.

All functions degrade gracefully if optional libraries (networkx, sklearn, scipy) are missing.
"""

import logging
from typing import Optional, List, Dict, Any, Union, Tuple, Callable
import numpy as np

# Optional imports – handled gracefully
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None

try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, KBinsDiscretizer
    from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from scipy.spatial.distance import pdist, squareform
    from scipy.stats import zscore
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

logger = logging.getLogger(__name__)


# ============================================================================
# Helper functions
# ============================================================================

def _check_networkx():
    """Raise ImportError if networkx is not available."""
    if not HAS_NETWORKX:
        raise ImportError("networkx is required for this function.")


def _check_sklearn():
    """Raise ImportError if sklearn is not available."""
    if not HAS_SKLEARN:
        raise ImportError("scikit-learn is required for this function.")


def _check_scipy():
    """Raise ImportError if scipy is not available."""
    if not HAS_SCIPY:
        raise ImportError("scipy is required for this function.")


# ============================================================================
# Core conversion functions
# ============================================================================

def observable_to_vector(
    observable: Union[List, np.ndarray],
    normalize: bool = False,
    method: str = 'none'
) -> np.ndarray:
    """
    Convert an observable (list of values) to a standard numpy vector.
    Optionally apply normalization.

    Args:
        observable: List or array of numeric values.
        normalize: If True, apply normalization.
        method: Normalization method: 'none', 'standard' (z‑score), 'minmax', 'l2', or 'unit'.
                Ignored if normalize=False.

    Returns:
        1D numpy array.
    """
    vec = np.asarray(observable, dtype=float).flatten()
    if not normalize or method == 'none':
        return vec

    if method == 'standard':
        if HAS_SCIPY:
            return zscore(vec)
        elif HAS_SKLEARN:
            scaler = StandardScaler()
            return scaler.fit_transform(vec.reshape(-1, 1)).flatten()
        else:
            raise ImportError("Neither scipy nor sklearn available for standard normalization.")
    elif method == 'minmax':
        if HAS_SKLEARN:
            scaler = MinMaxScaler()
            return scaler.fit_transform(vec.reshape(-1, 1)).flatten()
        else:
            # Manual min-max
            minv, maxv = vec.min(), vec.max()
            if maxv - minv < 1e-12:
                return vec - minv
            return (vec - minv) / (maxv - minv)
    elif method == 'l2':
        norm = np.linalg.norm(vec)
        if norm > 1e-12:
            return vec / norm
        return vec
    elif method == 'unit':
        # Scale to [0,1] (same as minmax)
        minv, maxv = vec.min(), vec.max()
        if maxv - minv < 1e-12:
            return vec - minv
        return (vec - minv) / (maxv - minv)
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def extract_feature_matrix(
    registry: Dict[str, Any],
    observable_names: List[str],
    normalize: bool = False,
    norm_method: str = 'none'
) -> np.ndarray:
    """
    Extract a feature matrix from a Layer 1 registry.
    Each row corresponds to a node (entity), each column to an observable.

    Args:
        registry: Dictionary with at least an 'observables' key mapping to
                  a dict of observable_name -> list of values.
        observable_names: List of observable names to include (order defines columns).
        normalize: Whether to normalize each observable column.
        norm_method: Normalization method per observable (applied column‑wise).

    Returns:
        2D numpy array of shape (num_nodes, len(observable_names)).
    """
    if 'observables' not in registry:
        raise ValueError("Registry must contain 'observables' key.")

    obs_dict = registry['observables']
    # Determine number of nodes from the first observable
    if not observable_names:
        raise ValueError("observable_names cannot be empty.")
    first = observable_names[0]
    if first not in obs_dict:
        raise ValueError(f"Observable '{first}' not found in registry.")
    num_nodes = len(obs_dict[first])

    matrix = np.zeros((num_nodes, len(observable_names)))
    for i, name in enumerate(observable_names):
        if name not in obs_dict:
            raise ValueError(f"Observable '{name}' not found in registry.")
        arr = np.asarray(obs_dict[name], dtype=float)
        if len(arr) != num_nodes:
            raise ValueError(f"Observable '{name}' has length {len(arr)} but expected {num_nodes}.")
        matrix[:, i] = observable_to_vector(arr, normalize=normalize, method=norm_method)
    return matrix


def registry_to_graph(
    registry: Dict[str, Any],
    node_ids: Optional[List] = None,
    edge_definition: Union[str, Callable] = 'threshold',
    threshold: float = 0.5,
    metric: str = 'euclidean',
    similarity_fn: Optional[Callable] = None,
    node_attrs: Optional[List[str]] = None,
    add_observables_as_attrs: bool = True,
    **kwargs
) -> 'nx.Graph':
    """
    Convert a Layer 1 registry to a NetworkX graph.

    Nodes correspond to entities (the indices of observables). Edges are created
    based on a similarity/distance measure between the observable vectors.

    Args:
        registry: Dictionary with 'observables' mapping to dict of lists.
        node_ids: Optional list of node identifiers (length = num_nodes). If None,
                  nodes are labelled by integer indices.
        edge_definition: How to create edges:
            - 'threshold': add edge if similarity > threshold (or distance < threshold).
            - 'knn': connect each node to its k nearest neighbours (k given as `k` in kwargs).
            - 'full': fully connected graph (all pairwise edges).
            - callable: custom function that takes a similarity/distance matrix and returns
                        edge list as list of (u, v, weight) tuples.
        threshold: Threshold value for 'threshold' method.
        metric: Distance/similarity metric: 'euclidean', 'cosine', 'correlation', or a callable.
                If metric is 'cosine' or 'correlation', similarity is used (higher = closer).
                For 'euclidean', distance is used (lower = closer).
        similarity_fn: Optional custom function that takes two vectors and returns a similarity.
                       If provided, overrides metric.
        node_attrs: List of observable names to add as node attributes (if add_observables_as_attrs is True).
        add_observables_as_attrs: If True, store observable values as node attributes.
        **kwargs: Additional arguments for edge_definition:
            - k (int): number of neighbours for 'knn'.
            - sym (bool): whether to make the k‑nn graph symmetric (default True).

    Returns:
        A NetworkX Graph (undirected by default, but can be overridden).
    """
    _check_networkx()

    # Extract feature matrix
    obs_names = list(registry['observables'].keys())
    X = extract_feature_matrix(registry, obs_names, normalize=False)  # we can apply normalization later if needed

    num_nodes = X.shape[0]
    if node_ids is None:
        node_ids = list(range(num_nodes))
    elif len(node_ids) != num_nodes:
        raise ValueError("Length of node_ids must match number of nodes.")

    # Compute pairwise similarity/distance matrix
    if similarity_fn is not None:
        # User‑supplied similarity function
        sim_mat = np.zeros((num_nodes, num_nodes))
        for i in range(num_nodes):
            for j in range(num_nodes):
                sim_mat[i, j] = similarity_fn(X[i], X[j])
        # Determine if it's similarity (higher = better) or distance
        # We'll assume similarity by default; user must handle threshold accordingly.
        use_similarity = True
    else:
        if metric == 'euclidean':
            if HAS_SCIPY:
                dist_mat = squareform(pdist(X, metric='euclidean'))
                use_similarity = False
                mat = dist_mat
            elif HAS_SKLEARN:
                dist_mat = euclidean_distances(X)
                use_similarity = False
                mat = dist_mat
            else:
                raise ImportError("Need scipy or sklearn for euclidean distance.")
        elif metric == 'cosine':
            if HAS_SKLEARN:
                sim_mat = cosine_similarity(X)
                use_similarity = True
                mat = sim_mat
            else:
                raise ImportError("sklearn required for cosine similarity.")
        elif metric == 'correlation':
            if HAS_SCIPY:
                # Pearson correlation
                corr_mat = np.corrcoef(X)
                # correlation is similarity (1 = identical)
                use_similarity = True
                mat = corr_mat
            else:
                raise ImportError("scipy required for correlation.")
        elif callable(metric):
            # metric is a distance/similarity function that takes two vectors
            mat = np.zeros((num_nodes, num_nodes))
            for i in range(num_nodes):
                for j in range(num_nodes):
                    mat[i, j] = metric(X[i], X[j])
            # We cannot automatically know if it's similarity or distance; assume distance by default.
            use_similarity = False
            logger.warning("Custom metric provided; assuming it returns distance (lower = closer).")
        else:
            raise ValueError(f"Unsupported metric: {metric}")

    # Create graph
    G = nx.Graph()
    G.add_nodes_from(node_ids)

    # Add node attributes (observables)
    if add_observables_as_attrs:
        for i, node in enumerate(node_ids):
            attrs = {name: X[i, idx] for idx, name in enumerate(obs_names)}
            G.nodes[node].update(attrs)

    # Add edges according to edge_definition
    if edge_definition == 'full':
        # Add all edges
        for i in range(num_nodes):
            for j in range(i+1, num_nodes):
                if use_similarity:
                    weight = mat[i, j]
                else:
                    weight = mat[i, j]
                G.add_edge(node_ids[i], node_ids[j], weight=weight)

    elif edge_definition == 'threshold':
        # Add edge if similarity > threshold or distance < threshold
        for i in range(num_nodes):
            for j in range(i+1, num_nodes):
                val = mat[i, j]
                if (use_similarity and val > threshold) or (not use_similarity and val < threshold):
                    G.add_edge(node_ids[i], node_ids[j], weight=val)

    elif edge_definition == 'knn':
        k = kwargs.get('k', 5)
        symmetric = kwargs.get('sym', True)
        # For each node, find k nearest neighbours (closest if distance, highest if similarity)
        edges = set()
        for i in range(num_nodes):
            # Get indices sorted by value
            if use_similarity:
                # Higher similarity is better → sort descending
                neighbours = np.argsort(mat[i])[::-1]
            else:
                # Lower distance is better → sort ascending
                neighbours = np.argsort(mat[i])
            # Exclude self (first element is itself)
            for j in neighbours[1:k+1]:
                if (i, j) not in edges and (j, i) not in edges:
                    edges.add((i, j))
        if symmetric:
            # Ensure symmetry: for each (i,j) add both directions
            for (i, j) in list(edges):
                edges.add((j, i))
        for i, j in edges:
            val = mat[i, j]
            G.add_edge(node_ids[i], node_ids[j], weight=val)

    elif callable(edge_definition):
        # Custom function that returns list of edges
        edge_list = edge_definition(mat, node_ids, use_similarity, **kwargs)
        for u, v, w in edge_list:
            G.add_edge(u, v, weight=w)

    else:
        raise ValueError(f"Unknown edge_definition: {edge_definition}")

    return G


def similarity_matrix(
    data: Union[np.ndarray, Dict[str, Any]],
    method: str = 'cosine',
    normalize: bool = False,
    norm_method: str = 'none',
    observable_names: Optional[List[str]] = None
) -> np.ndarray:
    """
    Compute a pairwise similarity matrix between samples (rows) or variables (columns).

    Args:
        data: Either a 2D numpy array (samples × features) or a Layer 1 registry.
        method: Similarity/distance metric: 'cosine', 'euclidean', 'correlation',
                'manhattan', or a callable that returns a matrix.
        normalize: Whether to normalize features before computation.
        norm_method: Normalization method (passed to observable_to_vector).
        observable_names: If data is a registry, list of observables to use (default all).

    Returns:
        2D numpy array of shape (n_samples, n_samples) (or n_features, n_features if transpose?).
         By default it computes sample‑sample similarity.
    """
    if isinstance(data, dict):
        # Assume it's a registry
        if 'observables' not in data:
            raise ValueError("Registry must contain 'observables' key.")
        if observable_names is None:
            observable_names = list(data['observables'].keys())
        X = extract_feature_matrix(data, observable_names, normalize=normalize, norm_method=norm_method)
    else:
        X = np.asarray(data, dtype=float)
        if normalize:
            X = observable_to_vector(X.T, normalize=True, method=norm_method).T  # apply column‑wise

    n = X.shape[0]

    if callable(method):
        # Custom function should return a full matrix
        return method(X)

    if method == 'cosine':
        if HAS_SKLEARN:
            return cosine_similarity(X)
        else:
            # Manual cosine
            norms = np.linalg.norm(X, axis=1, keepdims=True)
            norms[norms == 0] = 1
            X_norm = X / norms
            return X_norm @ X_norm.T

    elif method == 'euclidean':
        if HAS_SCIPY:
            return squareform(pdist(X, metric='euclidean'))
        elif HAS_SKLEARN:
            return euclidean_distances(X)
        else:
            # Manual Euclidean
            dist = np.zeros((n, n))
            for i in range(n):
                for j in range(i+1, n):
                    d = np.linalg.norm(X[i] - X[j])
                    dist[i, j] = d
                    dist[j, i] = d
            return dist

    elif method == 'correlation':
        if HAS_SCIPY:
            # Pearson correlation
            return np.corrcoef(X)
        else:
            raise ImportError("scipy required for correlation.")

    elif method == 'manhattan':
        if HAS_SCIPY:
            return squareform(pdist(X, metric='cityblock'))
        else:
            # Manual Manhattan
            dist = np.zeros((n, n))
            for i in range(n):
                for j in range(i+1, n):
                    d = np.sum(np.abs(X[i] - X[j]))
                    dist[i, j] = d
                    dist[j, i] = d
            return dist

    else:
        raise ValueError(f"Unknown method: {method}")


def discretize_observable(
    observable: Union[List, np.ndarray],
    n_bins: int = 5,
    strategy: str = 'uniform',
    return_edges: bool = False
) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
    """
    Discretize a continuous observable into integer bins.

    Args:
        observable: 1D array of values.
        n_bins: Number of bins.
        strategy: 'uniform' (equal width), 'quantile' (equal frequency), or 'kmeans'.
        return_edges: If True, also return the bin edges.

    Returns:
        Integer codes (0 .. n_bins-1). If return_edges, returns (codes, edges).
    """
    vec = np.asarray(observable).flatten()
    if HAS_SKLEARN:
        enc = KBinsDiscretizer(n_bins=n_bins, encode='ordinal', strategy=strategy)
        codes = enc.fit_transform(vec.reshape(-1, 1)).flatten().astype(int)
        if return_edges:
            edges = enc.bin_edges_[0]
            return codes, edges
        return codes
    else:
        # Manual binning
        if strategy == 'uniform':
            minv, maxv = vec.min(), vec.max()
            if maxv - minv < 1e-12:
                edges = np.array([minv - 1, minv + 1])
            else:
                edges = np.linspace(minv, maxv, n_bins + 1)
            codes = np.digitize(vec, edges[:-1]) - 1
            codes = np.clip(codes, 0, n_bins - 1)
        elif strategy == 'quantile':
            percentiles = np.linspace(0, 100, n_bins + 1)[1:-1]
            edges = np.percentile(vec, percentiles)
            edges = np.concatenate(([vec.min()], edges, [vec.max() + 1e-12]))
            codes = np.digitize(vec, edges[:-1]) - 1
            codes = np.clip(codes, 0, n_bins - 1)
        else:
            raise ValueError(f"Strategy '{strategy}' not supported without sklearn.")
        if return_edges:
            return codes, edges
        return codes


def normalize_observables(
    registry: Dict[str, Any],
    method: str = 'standard',
    inplace: bool = False
) -> Dict[str, Any]:
    """
    Normalize all observables in a registry.

    Args:
        registry: Dictionary with 'observables' key.
        method: Normalization method (see observable_to_vector).
        inplace: If True, modify the registry in place; otherwise return a new copy.

    Returns:
        Updated registry (new copy or in‑place modified).
    """
    if 'observables' not in registry:
        raise ValueError("Registry must contain 'observables' key.")

    obs_dict = registry['observables']
    if inplace:
        new_dict = obs_dict
    else:
        new_dict = obs_dict.copy()
        registry = registry.copy()
        registry['observables'] = new_dict

    for name, values in obs_dict.items():
        new_dict[name] = observable_to_vector(values, normalize=True, method=method).tolist()

    return registry


# ============================================================================
# Demo
# ============================================================================

def demo():
    """Simple demonstration of the module's functions."""
    print("="*60)
    print("LAYER 1 BRIDGE DEMO")
    print("="*60)

    # Create a synthetic registry
    np.random.seed(42)
    n_nodes = 10
    registry = {
        'observables': {
            'temperature': np.random.randn(n_nodes).tolist(),
            'pressure': np.random.rand(n_nodes).tolist(),
            'humidity': np.random.randint(0, 100, n_nodes).tolist()
        }
    }
    print("Registry created with observables:", list(registry['observables'].keys()))

    # 1. observable_to_vector
    vec = observable_to_vector(registry['observables']['temperature'], normalize=True, method='standard')
    print("\nNormalized temperature (first 5):", vec[:5])

    # 2. extract_feature_matrix
    X = extract_feature_matrix(registry, ['temperature', 'pressure'])
    print("\nFeature matrix shape:", X.shape)

    # 3. similarity_matrix
    sim = similarity_matrix(registry, method='cosine')
    print("Cosine similarity matrix (first 3 rows):\n", sim[:3, :3])

    # 4. discretize_observable
    disc, edges = discretize_observable(registry['observables']['temperature'], n_bins=3, strategy='quantile', return_edges=True)
    print("\nDiscretized temperature (first 5):", disc[:5])
    print("Bin edges:", edges)

    # 5. registry_to_graph (if networkx available)
    if HAS_NETWORKX:
        G = registry_to_graph(registry, edge_definition='knn', k=3, metric='euclidean')
        print(f"\nGraph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    else:
        print("\nNetworkX not available – skipping graph creation.")

    print("\nDemo finished.")


if __name__ == "__main__":
    demo()