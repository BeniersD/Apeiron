"""
hypergraph.py – Hypergraph structures for Layer 2 (Extended)
=============================================================
Provides the `Hypergraph` class: a higher‑order relational structure
where an edge (hyperedge) can connect an arbitrary number of vertices.

Features (existing):
  - simplicial complex construction
  - Betti numbers (simplicial, persistent, Hodge)
  - Hodge Laplacian and its eigenvalues
  - cohomology cup product
  - random walks (clique expansion and higher‑order)
  - hypergraph generators (Erdős–Rényi, preferential attachment)
  - persistent homology (multiple filtrations)
  - Mapper algorithm integration
  - serialisation to/from HDF5
  - Layer‑1 integration via resonance maps
  - visualisation (matplotlib / plotly)

New in v5.1:
  - conversion to SheafHypergraph
  - Hodge decomposition via HypergraphHodgeDecomposer
  - quantum Betti number estimation
  - categorical TDA interface
  - endogenous time generation
  - unified analysis shortcut
"""

from __future__ import annotations

import hashlib
import itertools
import logging
import pickle
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports – all handled gracefully
# ---------------------------------------------------------------------------
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    nx = None
    HAS_NETWORKX = False

try:
    import scipy.linalg
    from scipy.sparse.linalg import eigsh
    from scipy.sparse import csr_matrix, diags
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import gudhi as gd
    HAS_GUDHI = True
except ImportError:
    HAS_GUDHI = False

try:
    import kmapper as km
    HAS_KMAPPER = True
except ImportError:
    HAS_KMAPPER = False

try:
    import matplotlib.pyplot as plt
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import dash
    from dash import dcc, html
    HAS_DASH = True
except ImportError:
    HAS_DASH = False

try:
    import h5py
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

# ---------------------------------------------------------------------------
# New Layer‑2 module imports (graceful degradation)
# ---------------------------------------------------------------------------
try:
    from .sheaf_hypergraph import SheafHypergraph, SheafCohomologyResult
except ImportError:
    SheafHypergraph = None
    SheafCohomologyResult = None

try:
    from .hodge_decomposition import HypergraphHodgeDecomposer, HodgeDecomposition
except ImportError:
    HypergraphHodgeDecomposer = None
    HodgeDecomposition = None

try:
    from .categorical_tda import CategoricalTDA, PersistenceModule
except ImportError:
    CategoricalTDA = None
    PersistenceModule = None

try:
    from .spectral_sheaf import SheafSpectralAnalyzer, SheafSpectralResult
except ImportError:
    SheafSpectralAnalyzer = None
    SheafSpectralResult = None

try:
    from .endogenous_time import EndogenousTimeGenerator, TimeCone
except ImportError:
    EndogenousTimeGenerator = None
    TimeCone = None

try:
    from .quantum_topology import QuantumBettiEstimator, QuantumTopologyResult
except ImportError:
    QuantumBettiEstimator = None
    QuantumTopologyResult = None

try:
    from .layer2_unified_api import Layer2UnifiedAPI
except ImportError:
    Layer2UnifiedAPI = None


# ============================================================================
# Caching decorator (in‑memory + optional Redis)
# ============================================================================
def cached(ttl: int = 3600, key_prefix: str = "hyper"):
    """Simple in‑memory cache with optional Redis (if available)."""
    def decorator(func):
        _cache: Dict[str, Tuple[Any, float]] = {}
        def wrapper(self, *args, **kwargs):
            key = hashlib.md5(
                (func.__name__ + str(args) + str(sorted(kwargs.items()))).encode()
            ).hexdigest()
            full_key = f"{key_prefix}:{key}"
            if full_key in _cache:
                val, exp = _cache[full_key]
                if time.time() < exp:
                    return val
                del _cache[full_key]
            result = func(self, *args, **kwargs)
            _cache[full_key] = (result, time.time() + ttl)
            return result
        return wrapper
    return decorator


# ============================================================================
# Enums
# ============================================================================
class HomologyType(Enum):
    SIMPLICIAL = "simplicial"
    PERSISTENT = "persistent"
    HODGE = "hodge"
    QUANTUM = "quantum"          # new option


class FiltrationType(Enum):
    VIETORIS_RIPS = "vietoris_rips"
    CECH = "cech"
    CLIQUE = "clique"
    DISTANCE = "distance"
    WEIGHT = "weight"


# ============================================================================
# Hypergraph
# ============================================================================
@dataclass
class Hypergraph:
    """
    A hypergraph: a set of vertices and a collection of hyperedges, each
    connecting a subset of vertices. Weights can be assigned to hyperedges.

    Attributes:
        vertices: set of vertex identifiers.
        hyperedges: dict mapping hyperedge ID → set of vertices.
        weights: dict mapping hyperedge ID → float weight.
        simplicial_complex: dict mapping dimension → list of simplices (sets).
    """
    vertices: Set[Any] = field(default_factory=set)
    hyperedges: Dict[str, Set[Any]] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=dict)
    simplicial_complex: Dict[int, List[Set[Any]]] = field(default_factory=dict)
    _cache: Dict[str, Any] = field(default_factory=dict)
    _lazy_simplices: Optional[Dict[int, List[Set[Any]]]] = None   # on-demand per dim
    _simplex_materialised: Set[int] = field(default_factory=set)   # welke dims zijn al gebouwd
    _simplex_max_dim: int = 5  # harde cap om explosie te voorkomen

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------
    def add_hyperedge(self, edge_id: str, vertices: Set[Any], weight: float = 1.0) -> None:
        """Add a hyperedge and update the simplicial complex."""
        self.hyperedges[edge_id] = vertices
        self.weights[edge_id] = weight
        self.vertices.update(vertices)
        self._update_simplicial_complex(vertices)
        self._cache.clear()
        # Invalidate lazy cache (v5.2)
        if self._lazy_simplices is not None:
            self._simplex_materialised.clear()

    def remove_hyperedge(self, edge_id: str) -> None:
        """Remove a hyperedge and rebuild the simplicial complex."""
        if edge_id in self.hyperedges:
            del self.hyperedges[edge_id]
            del self.weights[edge_id]
        self.simplicial_complex.clear()
        for verts in self.hyperedges.values():
            self._update_simplicial_complex(verts)
        self._cache.clear()
        # Invalidate lazy cache (v5.2)
        if self._lazy_simplices is not None:
            self._lazy_simplices.clear()
            self._simplex_materialised.clear()

    def _update_simplicial_complex(self, vertices: Set[Any]) -> None:
        """Insert all faces of the hyperedge into the simplicial complex."""
        verts_list = sorted(vertices)
        dim = len(verts_list) - 1
        self.simplicial_complex.setdefault(dim, [])
        simplex = set(verts_list)
        if simplex not in self.simplicial_complex[dim]:
            self.simplicial_complex[dim].append(simplex)
        for k in range(dim):
            for face in itertools.combinations(verts_list, k + 1):
                face_set = set(face)
                self.simplicial_complex.setdefault(k, [])
                if face_set not in self.simplicial_complex[k]:
                    self.simplicial_complex[k].append(face_set)

                        def _ensure_simplices(self, dim: int) -> List[Set[Any]]:
        """
        Lazy, on‑demand materialisation of simplices for dimension `dim`.
        Only builds faces of hyperedges up to the requested dimension,
        never higher, and caches them in `_lazy_simplices`.

        Falls back to the eager `simplicial_complex` dict if the lazy
        structures have not been initialised.
        """
        # If the lazy store is not yet initialised, use the eager dict
        if self._lazy_simplices is None:
            self._lazy_simplices = dict(self.simplicial_complex)

        if dim in self._simplex_materialised:
            return self._lazy_simplices.get(dim, [])

        # Materialise all dimensions ≤ dim that are still missing
        for d in range(0, dim + 1):
            if d in self._simplex_materialised:
                continue
            if d not in self._lazy_simplices:
                self._lazy_simplices[d] = list(self.simplicial_complex.get(d, []))
            self._simplex_materialised.add(d)

        return self._lazy_simplices.get(dim, [])

    def get_simplices(self, dim: int) -> List[Set[Any]]:
        """
        Public API for lazy simplex retrieval.  Returns all simplices
        of the given dimension, materialising them if necessary.

        Parameters
        ----------
        dim : int
            Dimension to query.

        Returns
        -------
        list of sets
        """
        if dim > self._simplex_max_dim:
            logger.warning(
                f"Requested dim {dim} exceeds MAX_SIMPLEX_DIM {self._simplex_max_dim}; "
                f"returning empty list."
            )
            return []
        return self._ensure_simplices(dim)

    def set_max_simplex_dim(self, max_dim: int) -> None:
        """Set the hard cap on simplex dimension (prevents combinatorial explosion)."""
        self._simplex_max_dim = max_dim

    def categorical_embedding(self, dimension: int = 16, learning_rate: float = 0.01, epochs: int = 100, regularization: float = 0.001) -> Dict[str, Any]:
        """
        Learn an embedding that preserves commutativity of categorical diagrams,
        not merely pairwise distances.

        Minimizes L = Σ_{(f,g) composable} || emb(cod(g)) - T_g(emb(dom(f))) ||²
        where T_f is a linear map associated with morphism f, subject to
        T_g ∘ T_f ≈ T_{g∘f} for composable pairs.
        """
        vertices = list(self.vertices)
        n = len(vertices)
        if n == 0:
            return {'embedding': np.array([]), 'loss': 0.0}

        # Initialize embeddings and morphism linear maps
        embedding = np.random.randn(n, dimension) * 0.1
        morphisms = []
        T_maps = {}
        vertex_idx = {v: i for i, v in enumerate(vertices)}

        for edge in self.hyperedges.values():
            edge_list = sorted(edge, key=lambda v: vertex_idx.get(v, 0))
            for i in range(len(edge_list)):
                for j in range(i + 1, len(edge_list)):
                    s, t = vertex_idx[edge_list[i]], vertex_idx[edge_list[j]]
                    morphisms.append((s, t))
                    T_maps[(s, t)] = np.eye(dimension) + np.random.randn(dimension, dimension) * 0.01

        if not morphisms:
            return {'embedding': embedding, 'loss': 0.0}

        best_loss = float('inf')
        best_embedding = embedding.copy()

        for epoch in range(epochs):
            total_loss = 0.0
            count = 0

            # Commutative diagram enforcement
            for (s, t) in morphisms:
                T_st = T_maps[(s, t)]
                delta_target = embedding[t] - embedding[s]
                predicted = T_st @ delta_target
                # Reconstruction loss
                loss = np.sum((predicted - delta_target) ** 2)
                total_loss += loss
                count += 1

                # Gradient step
                grad_emb_t = 2 * (T_st.T @ (predicted - delta_target) - (predicted - delta_target))
                grad_emb_s = -2 * (T_st.T @ (predicted - delta_target) - (predicted - delta_target))
                embedding[t] -= learning_rate * grad_emb_t
                embedding[s] -= learning_rate * grad_emb_s
                grad_T = 2 * np.outer(predicted - delta_target, delta_target)
                T_maps[(s, t)] -= learning_rate * (grad_T + regularization * T_maps[(s, t)])

            # Commutative composition: T_{(s,u)} ≈ T_{(t,u)} ∘ T_{(s,t)}
            for (s, t) in morphisms:
                for (t2, u) in morphisms:
                    if t == t2 and (s, u) in T_maps:
                        T_su = T_maps[(s, u)]
                        T_st = T_maps[(s, t)]
                        T_tu = T_maps[(t2, u)]
                        composed = T_tu @ T_st
                        comp_loss = np.sum((T_su - composed) ** 2)
                        total_loss += comp_loss * 0.1
                        count += 1

            avg_loss = total_loss / max(count, 1)
            if avg_loss < best_loss:
                best_loss = avg_loss
                best_embedding = embedding.copy()

            if epoch % 50 == 0:
                pass  # logging hook

        return {
            'embedding': best_embedding,
            'loss': best_loss,
            'morphisms': morphisms,
            'T_maps': T_maps,
            'epochs': epochs
        }

    # ------------------------------------------------------------------
    # Homology and Betti numbers
    # ------------------------------------------------------------------
    @cached(ttl=3600)
    def betti_numbers(self, method: HomologyType = HomologyType.SIMPLICIAL) -> Dict[int, int]:
        if method == HomologyType.SIMPLICIAL:
            return self._simplicial_betti()
        elif method == HomologyType.PERSISTENT and HAS_GUDHI:
            return self._persistent_betti()
        elif method == HomologyType.HODGE:
            return self._hodge_betti()
        elif method == HomologyType.QUANTUM:
            return self._quantum_betti()
        return {}

    def _simplicial_betti(self) -> Dict[int, int]:
        if not self.simplicial_complex:
            return {}
        max_dim = max(self.simplicial_complex.keys())
        betti = {}
        for dim in range(max_dim + 1):
            B_down = self._boundary_matrix(dim)
            B_up = self._boundary_matrix(dim + 1) if dim + 1 <= max_dim else None
            if B_down is not None and HAS_SCIPY:
                rank = np.linalg.matrix_rank(B_down)
                nullity = B_down.shape[1] - rank
                if B_up is not None:
                    rank_up = np.linalg.matrix_rank(B_up)
                    betti[dim] = nullity - rank_up
                else:
                    betti[dim] = nullity
            else:
                betti[dim] = 0
        # Adjust dim 0 with connected components
        betti[0] = self._connected_components()
        return betti

    def _persistent_betti(self) -> Dict[int, int]:
        if not HAS_GUDHI:
            return {}
        st = gd.SimplexTree()
        for dim, simplices in self.simplicial_complex.items():
            for s in simplices:
                st.insert(list(s))
        st.persistence()
        betti = {}
        for dim in range(3):
            intervals = st.persistence_intervals_in_dimension(dim)
            betti[dim] = sum(1 for _, d in intervals if d == float('inf'))
        return betti

    def _hodge_betti(self) -> Dict[int, int]:
        betti = {}
        max_dim = max(self.simplicial_complex.keys()) if self.simplicial_complex else 0
        for dim in range(max_dim + 1):
            L = self.hodge_laplacian(dim)
            if L is not None and HAS_SCIPY:
                eigvals = np.linalg.eigvalsh(L)
                betti[dim] = np.sum(np.abs(eigvals) < 1e-10)
            else:
                betti[dim] = 0
        return betti

    def _quantum_betti(self) -> Dict[int, int]:
        """Use QuantumBettiEstimator to estimate Betti numbers."""
        if QuantumBettiEstimator is not None:
            try:
                est = QuantumBettiEstimator(self, backend='classical')
                result = est.estimate_betti_numbers()
                # Convert to dict
                return {i: b for i, b in enumerate(result.betti_numbers)}
            except Exception as e:
                logger.warning(f"Quantum Betti estimation failed: {e}")
        return {}

    def _boundary_matrix(self, dim: int) -> Optional[np.ndarray]:
        """Return the boundary matrix ∂_dim : C_dim → C_{dim-1}."""
        if dim not in self.simplicial_complex or dim == 0:
            return None
        k_simplices = self.simplicial_complex[dim]
        kminus1 = self.simplicial_complex[dim - 1]
        idx_map = {frozenset(s): i for i, s in enumerate(kminus1)}
        B = np.zeros((len(kminus1), len(k_simplices)))
        for j, simplex in enumerate(k_simplices):
            verts = sorted(simplex)
            for i, v in enumerate(verts):
                face = frozenset(verts[:i] + verts[i+1:])
                if face in idx_map:
                    B[idx_map[face], j] = (-1) ** i
        return B

    def _connected_components(self) -> int:
        if not self.vertices:
            return 0
        if not HAS_NETWORKX:
            return 1
        G = nx.Graph()
        G.add_nodes_from(self.vertices)
        for edge in self.simplicial_complex.get(1, []):
            v1, v2 = list(edge)[:2]
            G.add_edge(v1, v2)
        return nx.number_connected_components(G)

    # ------------------------------------------------------------------
    # Hodge Laplacian
    # ------------------------------------------------------------------
    def hodge_laplacian(self, dim: int, normalized: bool = False) -> Optional[np.ndarray]:
        if dim == 0:
            if not HAS_NETWORKX:
                return None
            G = nx.Graph()
            G.add_nodes_from(self.vertices)
            for edge in self.simplicial_complex.get(1, []):
                v1, v2 = list(edge)[:2]
                G.add_edge(v1, v2)
            L = nx.laplacian_matrix(G).todense()
            if normalized:
                deg = np.array(L.diagonal()).flatten()
                with np.errstate(divide='ignore'):
                    d_inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0)
                I = np.eye(L.shape[0])
                L = I - d_inv_sqrt[:, None] * (np.diag(deg) - L) * d_inv_sqrt[None, :]
            return L
        B_down = self._boundary_matrix(dim)
        B_up = self._boundary_matrix(dim + 1)
        n = len(self.simplicial_complex.get(dim, []))
        L = np.zeros((n, n))
        if B_up is not None:
            L += B_up @ B_up.T
        if B_down is not None:
            L += B_down.T @ B_down
        return L

    def hodge_eigenvalues(self, dim: int, k: int = 5, normalized: bool = False) -> np.ndarray:
        L = self.hodge_laplacian(dim, normalized)
        if L is None or not HAS_SCIPY:
            return np.array([])
        if L.shape[0] < k:
            k = L.shape[0]
        if L.shape[0] > 100:
            L_sp = csr_matrix(L)
            eigvals, _ = eigsh(L_sp, k=k, which='SM')
            return eigvals
        else:
            return np.linalg.eigvalsh(L)[:k]

    # ------------------------------------------------------------------
    # Cohomology / cup product
    # ------------------------------------------------------------------
    def cup_product(
        self,
        cochain1: Dict[Set[Any], float],
        cochain2: Dict[Set[Any], float],
        dim1: int,
        dim2: int,
    ) -> Dict[Set[Any], float]:
        result = {}
        target_dim = dim1 + dim2
        for simplex in self.simplicial_complex.get(target_dim, []):
            verts = sorted(simplex)
            val = 0.0
            for split in range(len(verts) - dim1 + 1):
                front = set(verts[:split + dim1 + 1])
                back = set(verts[split + dim1 + 1:])
                if len(front) == dim1 + 1 and len(back) == dim2 + 1:
                    v1 = cochain1.get(frozenset(front), 0.0)
                    v2 = cochain2.get(frozenset(back), 0.0)
                    val += v1 * v2
            if val != 0.0:
                result[frozenset(simplex)] = val
        return result

    # ------------------------------------------------------------------
    # Random walks
    # ------------------------------------------------------------------
    def random_walk(self, start: Any, steps: int) -> List[Any]:
        """Simple random walk on the 1‑skeleton (clique expansion)."""
        if not HAS_NETWORKX:
            return [start]
        G = nx.Graph()
        G.add_nodes_from(self.vertices)
        for edge in self.hyperedges.values():
            for u, v in itertools.combinations(edge, 2):
                G.add_edge(u, v)
        cur = start
        path = [cur]
        for _ in range(steps):
            nb = list(G.neighbors(cur))
            if not nb:
                break
            cur = np.random.choice(nb)
            path.append(cur)
        return path

    def higher_order_random_walk(
        self, start: Any, steps: int, order: int = 2
    ) -> List[Any]:
        """
        Walk on simplices of given order; project onto vertices.
        order=2 => walk on triangles, etc.
        """
        if order < 2 or order not in self.simplicial_complex:
            return self.random_walk(start, steps)
        simplices = list(self.simplicial_complex[order])
        if not simplices:
            return [start]
        # Build adjacency of simplices sharing a face of dimension order-1
        idx_map = {frozenset(s): i for i, s in enumerate(simplices)}
        adj: Dict[int, List[int]] = {i: [] for i in range(len(simplices))}
        for i, s1 in enumerate(simplices):
            for j, s2 in enumerate(simplices):
                if i != j and len(s1 & s2) >= order:
                    adj[i].append(j)
        # Find starting simplex containing `start`
        cur_idx = next((i for i, s in enumerate(simplices) if start in s), None)
        if cur_idx is None:
            return [start]
        path = [start]
        for _ in range(steps):
            nbs = adj[cur_idx]
            if not nbs:
                break
            cur_idx = np.random.choice(nbs)
            common = simplices[cur_idx] & simplices[path[-1]] if path else simplices[cur_idx]
            next_vertex = next(iter(common)) if common else next(iter(simplices[cur_idx]))
            path.append(next_vertex)
        return path

    # ------------------------------------------------------------------
    # Persistent homology (multiple filtrations)
    # ------------------------------------------------------------------
    def persistent_homology(
        self,
        max_dim: int = 2,
        filtration: FiltrationType = FiltrationType.CLIQUE,
    ) -> Dict[str, Any]:
        if not HAS_GUDHI:
            return {}
        if filtration == FiltrationType.CLIQUE:
            G = nx.Graph()
            G.add_nodes_from(self.vertices)
            for edge in self.hyperedges.values():
                for u, v in itertools.combinations(edge, 2):
                    G.add_edge(u, v)
            st = gd.SimplexTree()
            for node in G.nodes():
                st.insert([node])
            for u, v in G.edges():
                st.insert([u, v])
            for clique in nx.enumerate_all_cliques(G):
                if len(clique) > 2:
                    st.insert(clique)
        elif filtration == FiltrationType.DISTANCE:
            G = nx.Graph()
            G.add_nodes_from(self.vertices)
            for edge in self.hyperedges.values():
                for u, v in itertools.combinations(edge, 2):
                    G.add_edge(u, v)
            try:
                dist = nx.floyd_warshall_numpy(G)
            except Exception:
                return {}
            rips = gd.RipsComplex(distance_matrix=dist, max_edge_length=1.0)
            st = rips.create_simplex_tree(max_dimension=max_dim)
        else:
            return {}
        st.persistence()
        diagrams = {}
        for dim in range(max_dim + 1):
            intervals = st.persistence_intervals_in_dimension(dim)
            diagrams[dim] = [(b, d) for b, d in intervals if d < float('inf')]
        betti = {dim: sum(1 for _, d in intervals if d == float('inf'))
                 for dim, intervals in diagrams.items()}
        return {'persistence': st.persistence(), 'diagrams': diagrams, 'betti_numbers': betti}

    # ------------------------------------------------------------------
    # Generators
    # ------------------------------------------------------------------
    @classmethod
    def erdos_renyi(cls, n: int, p: float, seed: Optional[int] = None) -> Hypergraph:
        """Random hypergraph: each possible subset included with probability p."""
        import random
        if seed is not None:
            random.seed(seed)
        h = cls()
        vertices = list(range(n))
        h.vertices = set(vertices)
        for size in range(2, n + 1):
            for comb in itertools.combinations(vertices, size):
                if random.random() < p:
                    eid = f"e_{len(h.hyperedges)}"
                    h.add_hyperedge(eid, set(comb), weight=1.0)
        return h

    @classmethod
    def preferential_attachment(cls, n: int, m: int, seed: Optional[int] = None) -> Hypergraph:
        """Preferential attachment hypergraph (simplified to edges)."""
        if not HAS_NETWORKX:
            raise ImportError("NetworkX required for preferential attachment")
        G = nx.barabasi_albert_graph(n, m, seed=seed)
        h = cls()
        h.vertices = set(G.nodes())
        for i, (u, v) in enumerate(G.edges()):
            h.add_hyperedge(f"e{i}", {u, v}, weight=1.0)
        return h

    # ------------------------------------------------------------------
    # Mapper (topological data analysis)
    # ------------------------------------------------------------------
    def mapper(
        self,
        lens: List[np.ndarray],
        cover: Optional[Any] = None,
        clusterer: Optional[Any] = None,
        interactive: bool = False,
    ) -> Optional[Any]:
        if not HAS_KMAPPER or not HAS_NETWORKX:
            return None
        G = nx.Graph()
        G.add_nodes_from(self.vertices)
        for edge in self.simplicial_complex.get(1, []):
            v1, v2 = list(edge)[:2]
            G.add_edge(v1, v2)
        data = np.column_stack(lens) if lens else np.array([[G.degree(v)] for v in sorted(G.nodes())])
        mapper = km.KeplerMapper(verbose=0)
        graph = mapper.map(data, cover=cover, clusterer=clusterer)
        if interactive and HAS_DASH:
            app = dash.Dash(__name__)
            app.layout = html.Div([
                html.H1("Mapper Graph"),
                html.Iframe(srcDoc=mapper.visualize(graph), width="1000", height="800"),
            ])
            return app
        return graph

    # ------------------------------------------------------------------
    # Serialisation (HDF5)
    # ------------------------------------------------------------------
    def to_hdf5(self, filename: str) -> None:
        if not HAS_H5PY:
            logger.warning("h5py not available")
            return
        with h5py.File(filename, 'w') as f:
            f.attrs['n_vertices'] = len(self.vertices)
            f.attrs['n_hyperedges'] = len(self.hyperedges)
            for v in self.vertices:
                f.create_dataset(f"v/{v}", data=v)
            for eid, verts in self.hyperedges.items():
                f.create_dataset(f"e/{eid}", data=list(verts))
            for eid, w in self.weights.items():
                f.create_dataset(f"w/{eid}", data=w)

    @classmethod
    def from_hdf5(cls, filename: str) -> Hypergraph:
        if not HAS_H5PY:
            raise ImportError("h5py not available")
        h = cls()
        with h5py.File(filename, 'r') as f:
            for key in f['v']:
                v = f[f'v/{key}'][()]
                h.vertices.add(v)
            for key in f['e']:
                verts = set(f[f'e/{key}'][()])
                h.hyperedges[key] = verts
            for key in f['w']:
                h.weights[key] = f[f'w/{key}'][()]
        # Rebuild simplicial complex
        for verts in h.hyperedges.values():
            h._update_simplicial_complex(verts)
        return h

    # ------------------------------------------------------------------
    # Visualisation
    # ------------------------------------------------------------------
    def visualize(
        self,
        filename: Optional[str] = None,
        interactive: bool = False,
        layout: str = 'spring',
        highlight_dims: Optional[List[int]] = None,
    ) -> None:
        if not HAS_NETWORKX:
            return
        B = nx.Graph()
        B.add_nodes_from(self.vertices, bipartite=0)
        B.add_nodes_from(self.hyperedges.keys(), bipartite=1)
        for eid, verts in self.hyperedges.items():
            for v in verts:
                B.add_edge(eid, v)
        if layout == 'spring':
            pos = nx.spring_layout(B)
        elif layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(B)
        else:
            pos = nx.spring_layout(B)
        if interactive and PLOTLY_AVAILABLE:
            edge_trace = []
            for u, v in B.edges():
                x0, y0 = pos[u]; x1, y1 = pos[v]
                edge_trace.append(go.Scatter(x=[x0, x1, None], y=[y0, y1, None],
                                             mode='lines', line=dict(width=1, color='#888')))
            node_trace = go.Scatter(
                x=[pos[n][0] for n in B.nodes()],
                y=[pos[n][1] for n in B.nodes()],
                mode='markers+text',
                text=list(B.nodes()),
                marker=dict(size=10, color=['lightblue' if n in self.vertices else 'lightgreen'
                                            for n in B.nodes()]),
            )
            fig = go.Figure(data=edge_trace + [node_trace])
            if filename:
                fig.write_html(filename)
            else:
                fig.show()
        elif VISUALIZATION_AVAILABLE:
            plt.figure(figsize=(12, 10))
            nx.draw_networkx_nodes(B, pos, nodelist=self.vertices, node_color='lightblue', node_size=500)
            nx.draw_networkx_edges(B, pos, alpha=0.5)
            nx.draw_networkx_labels(B, pos, font_size=10)
            if filename:
                plt.savefig(filename)
            else:
                plt.show()
            plt.close()

    # ------------------------------------------------------------------
    # Layer‑1 integration: build from resonance maps
    # ------------------------------------------------------------------
    @classmethod
    def build_from_resonance_maps(
        cls,
        registry: Dict[str, Any],
        layer_key: str = 'layer2',
        resonance_key: str = 'resonance',
    ) -> Hypergraph:
        """
        Create a hypergraph from Layer‑1 observables' resonance maps.

        All observables sharing the same value under `layer_key` and
        `resonance_key` are grouped into a hyperedge.
        """
        hg = cls()
        resonance_to_obs: Dict[str, Set[str]] = {}
        for obs_id, obs in registry.items():
            if not hasattr(obs, 'resonance_map'):
                continue
            data = obs.resonance_map.get(layer_key)
            if data is None:
                continue
            if resonance_key is not None and isinstance(data, dict):
                val = data.get(resonance_key)
            else:
                val = data
            if val is not None:
                key = str(val)
                resonance_to_obs.setdefault(key, set()).add(obs_id)
        for key, obs_set in resonance_to_obs.items():
            if len(obs_set) >= 2:
                hg.add_hyperedge(f"resonance_{key}", obs_set, weight=1.0)
        return hg

    # ==================================================================
    # NEW METHODS (v5.1) – Integration with extended Layer‑2 modules
    # ==================================================================

    def to_sheaf_hypergraph(self, vertex_stalks: Optional[Dict[str, Any]] = None) -> Any:
        """
        Convert this hypergraph to a SheafHypergraph.

        Parameters
        ----------
        vertex_stalks : optional dict mapping vertex ID to SheafStalk

        Returns
        -------
        SheafHypergraph or None
        """
        if SheafHypergraph is None:
            logger.warning("SheafHypergraph module not available")
            return None
        vert_ids = [f"v_{v}" for v in sorted(self.vertices)]
        edge_sets = [{f"v_{v}" for v in edge} for edge in self.hyperedges.values()]
        return SheafHypergraph(vert_ids, edge_sets)

    def hodge_decompose(self, signal: Optional[np.ndarray] = None, k: int = 0) -> Any:
        """
        Compute Hodge decomposition of a signal on this hypergraph.

        Parameters
        ----------
        signal : np.ndarray, optional
            Cochain values. If None, a random signal is generated.
        k : int
            Degree of cochain (0=vertices, 1=edges, 2=triangles).

        Returns
        -------
        HodgeDecomposition or None
        """
        if HypergraphHodgeDecomposer is None:
            logger.warning("Hodge decomposition module not available")
            return None
        decomp = HypergraphHodgeDecomposer(self)
        if signal is None:
            n = len(self.vertices) if k == 0 else len(self.simplicial_complex.get(k, []))
            signal = np.random.randn(n)
        return decomp.decompose(signal, k)

    def categorical_tda_analysis(self) -> Any:
        """
        Run categorical topological data analysis on this hypergraph.

        Returns
        -------
        PersistenceModule or None
        """
        if CategoricalTDA is None:
            logger.warning("CategoricalTDA module not available")
            return None
        ctda = CategoricalTDA(self)
        return ctda.persistence_module()

    def sheaf_spectral_analysis(self) -> Any:
        """
        Perform sheaf spectral analysis on this hypergraph (requires conversion).

        Returns
        -------
        SheafSpectralResult or None
        """
        if SheafSpectralAnalyzer is None:
            logger.warning("Spectral sheaf module not available")
            return None
        shg = self.to_sheaf_hypergraph()
        if shg is None:
            return None
        analyzer = SheafSpectralAnalyzer(shg)
        return analyzer.analyze()

    def generate_endogenous_time(self, causal_edges: Optional[List[Tuple[Any, Any]]] = None) -> Any:
        """
        Create an endogenous time ordering from causal edges.

        Parameters
        ----------
        causal_edges : list of (source, target) pairs; if None, uses directed
            interpretation of hyperedges (first two vertices as source→target).

        Returns
        -------
        TimeCone dict or None
        """
        if EndogenousTimeGenerator is None:
            logger.warning("Endogenous time module not available")
            return None
        if causal_edges is None:
            causal_edges = []
            for eid, verts in self.hyperedges.items():
                vlist = list(verts)
                if len(vlist) >= 2:
                    causal_edges.append((vlist[0], vlist[1]))
        gen = EndogenousTimeGenerator(causal_edges)
        return gen.compute_time_cones()

    def full_analysis(self, observables: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Run the complete Layer‑2 analysis via the unified API.

        Returns
        -------
        dict
        """
        if Layer2UnifiedAPI is None:
            return {"error": "Unified API not available"}
        api = Layer2UnifiedAPI(self, observables=observables or [])
        return api.full_analysis()