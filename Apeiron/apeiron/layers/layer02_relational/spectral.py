"""
spectral.py – Spectral graph analysis for Layer 2
==================================================
Provides:
  - SpectralGraphAnalysis: eigen decomposition, invariants, clustering,
    embedding, and Chebyshev filtering on graphs.
  - DynamicSpectralAnalysis: analysis of graph spectra over time,
    change point detection, forecasting, and Layer‑1 integration.
  - multiview_spectral_clustering: multi‑graph spectral clustering.
  - Convenience functions to build from NetworkX, igraph, graph‑tool.

All heavy dependencies (GPU, Dask, Numba, Redis) are optional.
"""

from __future__ import annotations

import hashlib
import logging
import pickle
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional libraries – graceful degradation
# ---------------------------------------------------------------------------

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    nx = None
    HAS_NETWORKX = False

try:
    import scipy.sparse as sp
    from scipy.sparse.linalg import eigsh, eigs, svds
    from scipy.linalg import eigh, expm
    from scipy.sparse.csgraph import laplacian as csgraph_laplacian
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import torch
    HAS_TORCH = True
    CUDA_AVAILABLE = torch.cuda.is_available() if hasattr(torch, 'cuda') else False
except ImportError:
    HAS_TORCH = False
    CUDA_AVAILABLE = False

try:
    from dask.distributed import Client, get_client
    HAS_DASK = True
except ImportError:
    HAS_DASK = False

try:
    from numba import jit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# ---------------------------------------------------------------------------
# New Layer‑2 module imports (graceful degradation)
# ---------------------------------------------------------------------------
try:
    from .sheaf_hypergraph import SheafHypergraph
except ImportError:
    SheafHypergraph = None

try:
    from .spectral_sheaf import SheafSpectralAnalyzer, SheafSpectralResult
except ImportError:
    SheafSpectralAnalyzer, SheafSpectralResult = None, None

try:
    from .quantum_topology import QuantumBettiEstimator
except ImportError:
    QuantumBettiEstimator = None

try:
    from .endogenous_time import EndogenousTimeGenerator
except ImportError:
    EndogenousTimeGenerator = None


# Lazy import for Layer‑1 integration
def _get_ultimate_observable():
    """Lazy import of UltimateObservable to avoid circular dependencies."""
    try:
        from apeiron.layers.layer01_foundational.irreducible_unit import UltimateObservable
        return UltimateObservable
    except ImportError:
        logger.warning("UltimateObservable not available – Layer‑1 integration disabled.")
        return None


# ============================================================================
# Enums
# ============================================================================

class SpectralType(Enum):
    """Types of graph matrices for spectral analysis."""
    ADJACENCY = "adjacency"
    LAPLACIAN = "laplacian"
    NORMALIZED_LAPLACIAN = "normalized_laplacian"
    SIGNLESS_LAPLACIAN = "signless_laplacian"
    RANDOM_WALK = "random_walk"
    MODULARITY = "modularity"
    NORMALIZED_ADJACENCY = "normalized_adjacency"
    IN_OUT_LAPLACIAN = "in_out_laplacian"

class GraphType(Enum):
    """Type of graph (directedness, weight)."""
    UNDIRECTED = "undirected"
    DIRECTED = "directed"
    WEIGHTED = "weighted"
    UNWEIGHTED = "unweighted"


# ============================================================================
# Caching decorator (in‑memory + optional Redis)
# ============================================================================

def cached(ttl: int = 3600, key_prefix: str = "spectral"):
    """Decorator to cache function results with optional Redis backend."""
    def decorator(func):
        _cache: Dict[str, Tuple[Any, float]] = {}
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            key_parts = [func.__name__, str(getattr(self, "graph_id", ""))] + \
                        [str(a) for a in args] + \
                        [f"{k}={v}" for k, v in sorted(kwargs.items())]
            key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            full_key = f"{key_prefix}:{key}"

            # Memory cache
            if full_key in _cache:
                val, exp = _cache[full_key]
                if time.time() < exp:
                    return val
                del _cache[full_key]

            # Redis cache (if available and client is set)
            if REDIS_AVAILABLE and hasattr(self, "_redis_client") and self._redis_client:
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    data = loop.run_until_complete(self._redis_client.get(full_key))
                    if data:
                        val = pickle.loads(data)
                        return val
                except Exception as e:
                    logger.debug(f"Redis cache error: {e}")

            result = func(self, *args, **kwargs)
            _cache[full_key] = (result, time.time() + ttl)

            if REDIS_AVAILABLE and hasattr(self, "_redis_client") and self._redis_client:
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    loop.create_task(self._redis_client.setex(full_key, ttl, pickle.dumps(result)))
                except Exception as e:
                    logger.debug(f"Redis cache write error: {e}")

            return result
        return wrapper
    return decorator


# ============================================================================
# Numba‑accelerated Chebyshev filter (optional)
# ============================================================================

if HAS_NUMBA:
    @jit(nopython=True, parallel=True)
    def _chebyshev_filter_numba(M_scaled, signal, order, cutoff):
        """Numba‑accelerated Chebyshev filter on graph."""
        n = len(signal)
        f = np.zeros(n, dtype=np.float64)
        f_prev = signal.copy()
        f_prev2 = np.zeros(n, dtype=np.float64)
        for i in range(order + 1):
            if i == 0:
                c = 2 / np.pi * (np.arcsin(cutoff) - cutoff * np.sqrt(1 - cutoff**2))
            elif i == 1:
                c = 2 / np.pi * (cutoff * np.sqrt(1 - cutoff**2))
            else:
                c = 0.0
            for j in prange(n):
                f[j] += c * f_prev[j]
            # Compute f_next = 2 * (M_scaled @ f_prev) - f_prev2
            f_next = np.zeros(n, dtype=np.float64)
            for j in range(n):
                s = 0.0
                for k in range(n):
                    s += M_scaled[j, k] * f_prev[k]
                f_next[j] = 2 * s - f_prev2[j]
            f_prev2 = f_prev
            f_prev = f_next
        return f


# ============================================================================
# SpectralGraphAnalysis
# ============================================================================

@dataclass
class SpectralGraphAnalysis:
    """
    Comprehensive spectral analysis of a graph.

    Supports graphs from NetworkX, igraph, graph‑tool, or raw adjacency
    matrices. Provides matrix construction, eigenvalue decomposition,
    invariants (algebraic connectivity, spectral radius, Estrada index,
    spanning trees, von Neumann entropy, graph energy, Kirchhoff index,
    spectral complexity, skewness, kurtosis), embedding, clustering,
    Chebyshev filtering, and Layer‑1 integration helpers.

    Attributes:
        graph: input graph (NetworkX, scipy sparse, or numpy array).
        graph_id: unique ID for caching.
        directed, weighted: graph properties (auto‑detected for NetworkX).
    """
    graph: Any
    graph_id: str = field(default_factory=lambda: f"graph_{time.time()}")
    directed: bool = False
    weighted: bool = False
    _matrices: Dict[str, Any] = field(default_factory=dict)
    _eigen: Dict[str, Tuple[np.ndarray, np.ndarray]] = field(default_factory=dict)
    _invariants: Dict[str, Any] = field(default_factory=dict)
    _redis_client = None

    def __post_init__(self):
        if HAS_NETWORKX and isinstance(self.graph, nx.Graph):
            self.directed = self.graph.is_directed()
            self.weighted = nx.is_weighted(self.graph)
        elif isinstance(self.graph, (np.ndarray, sp.spmatrix if HAS_SCIPY else None)):
            pass  # flags are user‑provided
        self._setup_redis()

    def _setup_redis(self):
        if REDIS_AVAILABLE:
            try:
                self._redis_client = redis.Redis.from_url("redis://localhost:6379")
            except Exception:
                pass

    def __repr__(self) -> str:
        n = self.get_matrix(SpectralType.ADJACENCY).shape[0] if self._matrices else 0
        return f"SpectralGraphAnalysis(id={self.graph_id}, nodes={n})"

    # ------------------------------------------------------------------------
    # Matrix construction
    # ------------------------------------------------------------------------
    def _get_adjacency(self) -> np.ndarray:
        if 'adjacency' in self._matrices:
            return self._matrices['adjacency']
        if HAS_NETWORKX and isinstance(self.graph, nx.Graph):
            A = nx.adjacency_matrix(self.graph, weight='weight' if self.weighted else None).todense()
        elif isinstance(self.graph, np.ndarray):
            A = self.graph
        elif HAS_SCIPY and sp.issparse(self.graph):
            A = self.graph.todense()
        else:
            raise ValueError("Cannot construct adjacency matrix from given graph")
        self._matrices['adjacency'] = A
        return A

    def _get_degrees(self) -> Tuple[np.ndarray, ...]:
        A = self._get_adjacency()
        if self.directed:
            out_deg = np.array(A.sum(axis=1)).flatten()
            in_deg = np.array(A.sum(axis=0)).flatten()
            return out_deg, in_deg
        else:
            deg = np.array(A.sum(axis=1)).flatten()
            return deg

    def get_matrix(self, matrix_type: SpectralType) -> np.ndarray:
        key = matrix_type.value
        if key in self._matrices:
            return self._matrices[key]
        A = self._get_adjacency()
        if not self.directed:
            deg = self._get_degrees()
            if matrix_type == SpectralType.LAPLACIAN:
                L = np.diag(deg) - A
            elif matrix_type == SpectralType.NORMALIZED_LAPLACIAN:
                with np.errstate(divide='ignore'):
                    d_inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0)
                L_norm = np.eye(A.shape[0]) - d_inv_sqrt[:, None] * A * d_inv_sqrt[None, :]
            elif matrix_type == SpectralType.SIGNLESS_LAPLACIAN:
                Q = np.diag(deg) + A
            elif matrix_type == SpectralType.RANDOM_WALK:
                with np.errstate(divide='ignore'):
                    d_inv = np.where(deg > 0, 1.0 / deg, 0)
                P = d_inv[:, None] * A
            elif matrix_type == SpectralType.NORMALIZED_ADJACENCY:
                with np.errstate(divide='ignore'):
                    d_inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0)
                A_norm = d_inv_sqrt[:, None] * A * d_inv_sqrt[None, :]
            elif matrix_type == SpectralType.MODULARITY:
                m = A.sum() / 2
                deg_outer = np.outer(deg, deg)
                B = A - deg_outer / (2 * m)
            else:
                raise ValueError(f"Unsupported matrix type: {matrix_type}")
            self._matrices[key] = locals()[key.split('.')[0]]  # hack: variable name = key
            return self._matrices[key]
        else:
            out_deg, in_deg = self._get_degrees()
            if matrix_type == SpectralType.IN_OUT_LAPLACIAN:
                L = np.diag(out_deg) - A
                self._matrices[key] = L
                return L
            else:
                raise ValueError(f"Matrix type {matrix_type} not defined for directed graphs")

    # ------------------------------------------------------------------------
    # Eigenvalue decomposition
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def compute_eigensystem(
        self,
        matrix_type: SpectralType = SpectralType.LAPLACIAN,
        k: Optional[int] = None,
        which: str = 'LM',
        use_gpu: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray]:
        M = self.get_matrix(matrix_type)
        n = M.shape[0]
        k = k or n

        if use_gpu and HAS_TORCH and CUDA_AVAILABLE:
            try:
                M_t = torch.tensor(M, dtype=torch.float64, device='cuda')
                if k == n:
                    eigvals, eigvecs = torch.linalg.eigh(M_t)
                else:
                    eigvals, eigvecs = torch.lobpcg(M_t, k=k, largest=(which != 'SM'))
                eigvals = eigvals.cpu().numpy()
                eigvecs = eigvecs.cpu().numpy()
                self._eigen[matrix_type.value] = (eigvals, eigvecs)
                return eigvals, eigvecs
            except Exception as e:
                logger.warning(f"GPU eigensolver failed, falling back to CPU: {e}")

        if HAS_SCIPY:
            if sp.issparse(M):
                M_sp = sp.csr_matrix(M)
                if k < n:
                    eigvals, eigvecs = eigsh(M_sp, k=k, which=which, sigma=1e-5 if which == 'SM' else None)
                else:
                    eigvals, eigvecs = np.linalg.eigh(M)
            else:
                if k == n:
                    eigvals, eigvecs = np.linalg.eigh(M)
                else:
                    eigvals, eigvecs = eigh(M, subset_by_index=(0, k - 1))
        else:
            eigvals, eigvecs = np.linalg.eigh(M)
            if k < n:
                eigvals = eigvals[:k]
                eigvecs = eigvecs[:, :k]

        self._eigen[matrix_type.value] = (eigvals, eigvecs)
        return eigvals, eigvecs

    # ======================================================================
    # Integration with extended Layer‑2 modules
    # ======================================================================
    def to_sheaf_spectral_analyzer(self) -> Any:
        """
        Convert this graph's adjacency structure into a SheafHypergraph
        and return a SheafSpectralAnalyzer for further analysis.

        Returns
        -------
        SheafSpectralAnalyzer or None
        """
        if SheafHypergraph is None or SheafSpectralAnalyzer is None:
            logger.warning("Sheaf modules not available")
            return None
        # Build vertices and edges from adjacency
        A = self._get_adjacency()
        n = A.shape[0]
        vertices = [f"v_{i}" for i in range(n)]
        edges = []
        for i in range(n):
            for j in range(i+1, n):
                if A[i, j] != 0:
                    edges.append({f"v_{i}", f"v_{j}"})
        if not edges:
            edges = [set(vertices)]  # fallback
        shg = SheafHypergraph(vertices, edges)
        return SheafSpectralAnalyzer(shg)

    def sheaf_spectral_invariants(self) -> Dict[str, Any]:
        """
        Compute spectral invariants using the sheaf Laplacian.

        Returns
        -------
        dict
        """
        analyzer = self.to_sheaf_spectral_analyzer()
        if analyzer is None:
            return {}
        return analyzer.compute_sheaf_spectral_invariants()

    def sheaf_spectral_clustering(self, n_clusters: int) -> Any:
        """
        Perform spectral clustering based on the sheaf Laplacian.

        Parameters
        ----------
        n_clusters : int

        Returns
        -------
        labels array or None
        """
        analyzer = self.to_sheaf_spectral_analyzer()
        if analyzer is None:
            return None
        return analyzer.spectral_clustering(n_clusters, use_harmonic=True)

    def quantum_eigenvalue_estimate(self, k: int = 5) -> Any:
        """
        Use quantum topology module to estimate low‑lying eigenvalues
        of the Hodge Laplacian.

        Returns
        -------
        QuantumTopologyResult or None
        """
        if QuantumBettiEstimator is None:
            logger.warning("Quantum topology module not available")
            return None
        # Create a hypergraph from this graph's adjacency
        try:
            from .hypergraph import Hypergraph
        except ImportError:
            return None
        hg = Hypergraph()
        hg.vertices = set(range(self._get_adjacency().shape[0]))
        A = self._get_adjacency()
        for i in range(A.shape[0]):
            for j in range(i+1, A.shape[1]):
                if A[i, j] != 0:
                    hg.add_hyperedge(f"e_{i}_{j}", {i, j})
        est = QuantumBettiEstimator(hg, backend='classical')
        return est.estimate_betti_numbers()

    def track_endogenous_time_spectrum(
        self,
        causal_edges: Optional[List[Tuple[Any, Any]]] = None
    ) -> Any:
        """
        Build endogenous time from causal edges (or default to directed
        interpretation of the adjacency) and compute spectral evolution
        along that time ordering.

        Returns
        -------
        list of eigenvalues per time step or None
        """
        if EndogenousTimeGenerator is None:
            logger.warning("Endogenous time module not available")
            return None
        A = self._get_adjacency()
        n = A.shape[0]
        if causal_edges is None:
            # treat every non-zero entry as directed (if graph is directed)
            if self.directed:
                causal_edges = [(i, j) for i in range(n) for j in range(n) if A[i, j] != 0]
            else:
                causal_edges = [(i, j) for i in range(n) for j in range(i+1, n) if A[i, j] != 0]
        gen = EndogenousTimeGenerator(causal_edges)
        ordering = gen.generate_time_ordering()
        if ordering is None:
            return None
        # Build a sequence of graphs: after each event in the ordering,
        # take the subgraph induced by vertices up to that point
        # and compute the spectrum.
        spectra = []
        for step in range(1, len(ordering) + 1):
            sub_vertices = ordering[:step]
            idx = [i for i, v in enumerate(range(n)) if v in sub_vertices]
            if len(idx) < 2:
                spectra.append(np.array([]))
                continue
            sub_A = A[idx][:, idx]
            sa = SpectralGraphAnalysis(sub_A, directed=self.directed, weighted=self.weighted)
            eigvals, _ = sa.compute_eigensystem(SpectralType.LAPLACIAN)
            spectra.append(eigvals)
        return spectra

    # ------------------------------------------------------------------------
    # Invariants (lazy, cached)
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def algebraic_connectivity(self) -> float:
        if self.directed:
            return 0.0
        eigvals, _ = self.compute_eigensystem(SpectralType.LAPLACIAN, k=2, which='SM')
        return float(eigvals[1]) if len(eigvals) >= 2 else 0.0

    @cached(ttl=3600)
    def spectral_gap(self) -> float:
        if self.directed:
            eigvals, _ = self.compute_eigensystem(SpectralType.ADJACENCY, k=2, which='LM')
            return float(eigvals[0] - eigvals[1]) if len(eigvals) >= 2 else 0.0
        eigvals, _ = self.compute_eigensystem(SpectralType.LAPLACIAN, k=2, which='SM')
        return float(eigvals[1] - eigvals[0]) if len(eigvals) >= 2 else 0.0

    @cached(ttl=3600)
    def spectral_radius(self) -> float:
        eigvals, _ = self.compute_eigensystem(SpectralType.ADJACENCY, k=1, which='LM')
        return float(abs(eigvals[0]))

    @cached(ttl=3600)
    def estrada_index(self) -> float:
        A = self.get_matrix(SpectralType.ADJACENCY)
        if HAS_SCIPY:
            expA = expm(A)
        else:
            eigvals, eigvecs = self.compute_eigensystem(SpectralType.ADJACENCY)
            expA = eigvecs @ np.diag(np.exp(eigvals)) @ eigvecs.T
        return float(np.trace(expA))

    @cached(ttl=3600)
    def number_of_spanning_trees(self) -> float:
        if self.directed:
            return 0.0
        L = self.get_matrix(SpectralType.LAPLACIAN)
        L_minor = L[1:, 1:]
        return float(np.linalg.det(L_minor))

    @cached(ttl=3600)
    def effective_resistance(self, i: int, j: int) -> float:
        if self.directed:
            return 0.0
        L = self.get_matrix(SpectralType.LAPLACIAN)
        eigvals, eigvecs = self.compute_eigensystem(SpectralType.LAPLACIAN)
        non_zero = eigvals > 1e-12
        L_pinv = eigvecs[:, non_zero] @ np.diag(1.0 / eigvals[non_zero]) @ eigvecs[:, non_zero].T
        return float(L_pinv[i, i] + L_pinv[j, j] - 2 * L_pinv[i, j])

    @cached(ttl=3600)
    def von_neumann_entropy(
        self, matrix_type: SpectralType = SpectralType.NORMALIZED_LAPLACIAN
    ) -> float:
        eigvals, _ = self.compute_eigensystem(matrix_type)
        eigvals = eigvals[eigvals > 1e-12]
        if len(eigvals) == 0:
            return 0.0
        p = eigvals / np.sum(eigvals)
        return -np.sum(p * np.log(p))

    def graph_energy(self) -> float:
        eigvals, _ = self.compute_eigensystem(SpectralType.ADJACENCY)
        return float(np.sum(np.abs(eigvals)))

    def spectral_moment(
        self, k: int, matrix_type: SpectralType = SpectralType.ADJACENCY
    ) -> float:
        eigvals, _ = self.compute_eigensystem(matrix_type)
        return float(np.sum(eigvals**k))

    def kirchhoff_index(self) -> float:
        if self.directed:
            return 0.0
        n = self.get_matrix(SpectralType.LAPLACIAN).shape[0]
        total = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                total += self.effective_resistance(i, j)
        return total

    def spectral_complexity(
        self, matrix_type: SpectralType = SpectralType.NORMALIZED_LAPLACIAN
    ) -> float:
        eigvals, _ = self.compute_eigensystem(matrix_type)
        eigvals = eigvals[eigvals > 1e-12]
        if len(eigvals) == 0:
            return 0.0
        p = eigvals / np.sum(eigvals)
        return -np.sum(p * np.log(p))

    def spectral_skewness(
        self, matrix_type: SpectralType = SpectralType.LAPLACIAN
    ) -> float:
        eigvals, _ = self.compute_eigensystem(matrix_type)
        if len(eigvals) < 3:
            return 0.0
        mean = np.mean(eigvals)
        std = np.std(eigvals)
        return float(np.mean((eigvals - mean) ** 3) / std**3) if std > 0 else 0.0

    def spectral_kurtosis(
        self, matrix_type: SpectralType = SpectralType.LAPLACIAN
    ) -> float:
        eigvals, _ = self.compute_eigensystem(matrix_type)
        if len(eigvals) < 4:
            return 0.0
        mean = np.mean(eigvals)
        std = np.std(eigvals)
        return float(np.mean((eigvals - mean) ** 4) / std**4 - 3) if std > 0 else 0.0

    def spectral_distribution_entropy(
        self, matrix_type: SpectralType = SpectralType.LAPLACIAN, bins: int = 50
    ) -> float:
        eigvals, _ = self.compute_eigensystem(matrix_type)
        hist, _ = np.histogram(eigvals, bins=bins, density=True)
        hist = hist[hist > 0]
        return -np.sum(hist * np.log(hist))

    # ------------------------------------------------------------------------
    # Spectral embedding
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def spectral_embedding(
        self, dim: int = 2, matrix_type: SpectralType = SpectralType.LAPLACIAN
    ) -> np.ndarray:
        if matrix_type in [SpectralType.LAPLACIAN, SpectralType.NORMALIZED_LAPLACIAN]:
            which, k = 'SM', dim + 1
        else:
            which, k = 'LM', dim
        _, eigvecs = self.compute_eigensystem(matrix_type, k=k, which=which)
        if matrix_type in [SpectralType.LAPLACIAN, SpectralType.NORMALIZED_LAPLACIAN]:
            return eigvecs[:, 1:dim + 1]
        return eigvecs[:, :dim]

    # ------------------------------------------------------------------------
    # Graph Fourier transform
    # ------------------------------------------------------------------------
    def gft(self, signal: np.ndarray, matrix_type: SpectralType = SpectralType.LAPLACIAN) -> np.ndarray:
        _, eigvecs = self.compute_eigensystem(matrix_type)
        return eigvecs.T @ signal

    def igft(self, coeffs: np.ndarray, matrix_type: SpectralType = SpectralType.LAPLACIAN) -> np.ndarray:
        _, eigvecs = self.compute_eigensystem(matrix_type)
        return eigvecs @ coeffs

    # ------------------------------------------------------------------------
    # Spectral clustering
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def spectral_clustering(
        self, n_clusters: Optional[int] = None,
        matrix_type: SpectralType = SpectralType.LAPLACIAN,
    ) -> List[int]:
        if n_clusters is None:
            eigvals, _ = self.compute_eigensystem(matrix_type, k=min(20, self.get_matrix(matrix_type).shape[0]))
            if matrix_type in [SpectralType.LAPLACIAN, SpectralType.NORMALIZED_LAPLACIAN]:
                gaps = np.diff(eigvals[1:])
                n_clusters = np.argmax(gaps) + 2 if len(gaps) > 0 else 1
            else:
                gaps = np.diff(eigvals)
                n_clusters = np.argmax(gaps) + 1 if len(gaps) > 0 else 1
        embed = self.spectral_embedding(dim=n_clusters, matrix_type=matrix_type)
        from scipy.cluster.vq import kmeans2
        _, labels = kmeans2(embed, n_clusters)
        return labels.tolist()

    # ------------------------------------------------------------------------
    # Chebyshev filter
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def chebyshev_filter(
        self,
        signal: np.ndarray,
        cutoff: float,
        order: int = 10,
        matrix_type: SpectralType = SpectralType.LAPLACIAN,
        use_numba: bool = True,
    ) -> np.ndarray:
        if not HAS_SCIPY:
            return signal
        M = self.get_matrix(matrix_type)
        lmax = self.spectral_radius() * 1.01
        M_scaled = (2 / lmax) * M - np.eye(M.shape[0])
        if use_numba and HAS_NUMBA:
            return _chebyshev_filter_numba(M_scaled, signal, order, cutoff)
        # Pure Python fallback
        f = np.zeros_like(signal)
        f_prev = signal
        f_prev2 = np.zeros_like(signal)
        for i in range(order + 1):
            if i == 0:
                c = 2 / np.pi * (np.arcsin(cutoff) - cutoff * np.sqrt(1 - cutoff**2))
            elif i == 1:
                c = 2 / np.pi * (cutoff * np.sqrt(1 - cutoff**2))
            else:
                c = 0
            f += c * f_prev
            f_next = 2 * (M_scaled @ f_prev) - f_prev2
            f_prev2, f_prev = f_prev, f_next
        return f

    # ------------------------------------------------------------------------
    # Heat kernel
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def heat_kernel(
        self, t: float, matrix_type: SpectralType = SpectralType.LAPLACIAN
    ) -> np.ndarray:
        eigvals, eigvecs = self.compute_eigensystem(matrix_type)
        return eigvecs @ np.diag(np.exp(-t * eigvals)) @ eigvecs.T

    def heat_kernel_trace(
        self, t: float, matrix_type: SpectralType = SpectralType.LAPLACIAN
    ) -> float:
        eigvals, _ = self.compute_eigensystem(matrix_type)
        return float(np.sum(np.exp(-t * eigvals)))

    # ------------------------------------------------------------------------
    # Spectral alignment / modularity gap
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def spectral_alignment(
        self, other: SpectralGraphAnalysis, dim: int = 10,
        matrix_type: SpectralType = SpectralType.LAPLACIAN,
    ) -> float:
        _, vecs1 = self.compute_eigensystem(matrix_type, k=dim, which='SM' if matrix_type in [SpectralType.LAPLACIAN] else 'LM')
        _, vecs2 = other.compute_eigensystem(matrix_type, k=dim, which='SM' if matrix_type in [SpectralType.LAPLACIAN] else 'LM')
        min_dim = min(dim, vecs1.shape[1], vecs2.shape[1])
        for i in range(min_dim):
            if np.dot(vecs1[:, i], vecs2[:, i]) < 0:
                vecs2[:, i] *= -1
        diff = vecs1[:, :min_dim] - vecs2[:, :min_dim]
        return float(np.linalg.norm(diff))

    @cached(ttl=3600)
    def spectral_modularity_gap(self) -> float:
        B = self.get_matrix(SpectralType.MODULARITY)
        eigvals, _ = self.compute_eigensystem(SpectralType.MODULARITY, k=2, which='LM')
        return float(eigvals[0] - eigvals[1]) if len(eigvals) >= 2 else 0.0

    # ------------------------------------------------------------------------
    # Distance between spectra
    # ------------------------------------------------------------------------
    @staticmethod
    def spectral_distance(
        graph1: SpectralGraphAnalysis,
        graph2: SpectralGraphAnalysis,
        matrix_type: SpectralType = SpectralType.LAPLACIAN,
        k: int = 10,
    ) -> float:
        eig1, _ = graph1.compute_eigensystem(matrix_type, k=k, which='SM' if matrix_type in [SpectralType.LAPLACIAN] else 'LM')
        eig2, _ = graph2.compute_eigensystem(matrix_type, k=k, which='SM' if matrix_type in [SpectralType.LAPLACIAN] else 'LM')
        min_len = min(len(eig1), len(eig2))
        return float(np.linalg.norm(eig1[:min_len] - eig2[:min_len]))

    # ------------------------------------------------------------------------
    # Parallel computation (Dask)
    # ------------------------------------------------------------------------
    @staticmethod
    def parallel_compute_eigensystem(
        graphs: List[Any],
        matrix_type: SpectralType = SpectralType.LAPLACIAN,
        k: Optional[int] = None,
        which: str = 'LM',
        use_dask: bool = True,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        if not HAS_DASK or not use_dask:
            return [SpectralGraphAnalysis(g).compute_eigensystem(matrix_type, k, which) for g in graphs]
        from dask.distributed import get_client
        try:
            client = get_client()
        except Exception:
            client = Client()
        def _compute_one(g):
            sa = SpectralGraphAnalysis(g)
            return sa.compute_eigensystem(matrix_type, k, which)
        futures = client.map(_compute_one, graphs)
        return client.gather(futures)

    # ------------------------------------------------------------------------
    # Layer‑1 integration helpers
    # ------------------------------------------------------------------------
    @classmethod
    def from_layer1_registry(
        cls,
        registry: Dict[str, Any],
        similarity_threshold: float = 0.1,
        similarity_func: Optional[Callable[[Any, Any], float]] = None,
        weight_by_atomicity: bool = False,
        **kwargs,
    ) -> SpectralGraphAnalysis:
        UltimateObservable = _get_ultimate_observable()
        if not HAS_NETWORKX:
            logger.warning("NetworkX required; returning empty analysis.")
            return cls(np.zeros((0, 0)))
        ids = list(registry.keys())
        n = len(ids)
        G = nx.Graph()
        for i, id1 in enumerate(ids):
            for j in range(i + 1, len(ids)):
                id2 = ids[j]
                obs1, obs2 = registry[id1], registry[id2]
                sim = (similarity_func(obs1, obs2) if similarity_func else 0.0)
                if sim >= similarity_threshold:
                    G.add_edge(id1, id2, weight=sim)
            if weight_by_atomicity and hasattr(registry[id1], 'atomicity_score'):
                G.nodes[id1]['atomicity'] = registry[id1].atomicity_score
        return cls(G, **kwargs)

    def compute_atomicity_laplacian(
        self, atomicity_weights: Optional[Dict[Any, float]] = None
    ) -> np.ndarray:
        if HAS_NETWORKX and isinstance(self.graph, nx.Graph):
            if atomicity_weights is None:
                atomicity_weights = {
                    node: data.get('atomicity', 0.0)
                    for node, data in self.graph.nodes(data=True)
                }
            A = self.get_matrix(SpectralType.ADJACENCY)
            nodes = list(self.graph.nodes())
            idx = {node: i for i, node in enumerate(nodes)}
            D_atomic = np.diag([atomicity_weights.get(node, 0.0) for node in nodes])
            return D_atomic - A
        else:
            if atomicity_weights is None:
                raise ValueError("atomicity_weights required for non‑NetworkX graphs.")
            n = self.get_matrix(SpectralType.ADJACENCY).shape[0]
            D = np.diag([atomicity_weights.get(i, 0.0) for i in range(n)])
            return D - self.get_matrix(SpectralType.ADJACENCY)

    # ------------------------------------------------------------------------
    # Plotting (stubs – detailed plots are in dashboards module)
    # ------------------------------------------------------------------------
    def plot_spectrum(self, *args, **kwargs):
        logger.info("Plotting delegated to dashboards module – not implemented here.")

    def plot_embedding(self, *args, **kwargs):
        logger.info("Plotting delegated to dashboards module – not implemented here.")

    # ------------------------------------------------------------------------
    # Convenience: all invariants as dict
    # ------------------------------------------------------------------------
    def get_invariants(self) -> Dict[str, Any]:
        inv = {}
        for method in [
            'algebraic_connectivity', 'spectral_gap', 'spectral_radius',
            'estrada_index', 'number_of_spanning_trees', 'von_neumann_entropy',
            'graph_energy', 'kirchhoff_index', 'spectral_complexity',
            'spectral_skewness', 'spectral_kurtosis', 'spectral_distribution_entropy',
        ]:
            try:
                val = getattr(self, method)()
                inv[method] = val
            except Exception:
                inv[method] = None
        return inv


# ============================================================================
# DynamicSpectralAnalysis
# ============================================================================

class DynamicSpectralAnalysis:
    """Analyse the evolution of graph spectra over time."""

    def __init__(self) -> None:
        self.timestamps: List[float] = []
        self.graphs: List[Any] = []
        self.spectral_objects: List[SpectralGraphAnalysis] = []
        self.eigenvalue_evolution: Dict[SpectralType, List[np.ndarray]] = {}
        self._multiparameter_persistence = None

    def __repr__(self) -> str:
        return f"DynamicSpectralAnalysis(num_graphs={len(self.graphs)})"

    def add_graph(self, graph: Any, timestamp: Optional[float] = None) -> None:
        if timestamp is None:
            timestamp = time.time()
        self.timestamps.append(timestamp)
        self.graphs.append(graph)
        sa = SpectralGraphAnalysis(graph)
        self.spectral_objects.append(sa)

    def snapshot_from_phase(
        self,
        registry: Dict[str, Any],
        phase: float,
        phase_key: str = 'temporal_phase',
        tolerance: float = 1e-6,
        **kwargs,
    ) -> Optional[SpectralGraphAnalysis]:
        filtered_ids = [
            oid for oid, obs in registry.items()
            if hasattr(obs, phase_key) and abs(getattr(obs, phase_key) - phase) <= tolerance
        ]
        if not filtered_ids:
            return None
        filtered_registry = {oid: registry[oid] for oid in filtered_ids}
        return SpectralGraphAnalysis.from_layer1_registry(filtered_registry, **kwargs)

    def compute_eigenvalue_evolution(
        self,
        matrix_type: SpectralType = SpectralType.LAPLACIAN,
        k: Optional[int] = None,
        use_parallel: bool = False,
    ) -> List[np.ndarray]:
        if use_parallel and HAS_DASK:
            from dask.distributed import get_client
            try:
                client = get_client()
            except Exception:
                client = Client()
            def _compute_one(sa):
                return sa.compute_eigensystem(matrix_type, k=k, which='SM' if matrix_type in [SpectralType.LAPLACIAN] else 'LM')[0]
            futures = client.map(_compute_one, self.spectral_objects)
            evolutions = client.gather(futures)
        else:
            evolutions = [
                sa.compute_eigensystem(matrix_type, k=k, which='SM' if matrix_type in [SpectralType.LAPLACIAN] else 'LM')[0]
                for sa in self.spectral_objects
            ]
        self.eigenvalue_evolution[matrix_type] = evolutions
        return evolutions

    def detect_change_points(
        self,
        matrix_type: SpectralType = SpectralType.LAPLACIAN,
        threshold: float = 0.1,
    ) -> List[int]:
        if matrix_type not in self.eigenvalue_evolution:
            self.compute_eigenvalue_evolution(matrix_type)
        evo = self.eigenvalue_evolution[matrix_type]
        if len(evo) < 2:
            return []
        changes = []
        for i in range(1, len(evo)):
            prev, curr = np.mean(evo[i-1]), np.mean(evo[i])
            if abs(curr - prev) / (abs(prev) + 1e-12) > threshold:
                changes.append(i)
        return changes

    def compute_sheaf_spectral_evolution(
        self,
        matrix_type: SpectralType = SpectralType.LAPLACIAN,
        k: int = 5,
    ) -> List[Dict]:
        """
        For each snapshot, build a sheaf hypergraph and compute its
        sheaf spectral invariants.
        """
        results = []
        for sa in self.spectral_objects:
            try:
                inv = sa.sheaf_spectral_invariants()
            except Exception:
                inv = {}
            results.append(inv)
        return results

    def forecast_eigenvalues(
        self,
        matrix_type: SpectralType = SpectralType.LAPLACIAN,
        steps: int = 1,
        method: str = 'linear',
    ) -> Optional[np.ndarray]:
        if matrix_type not in self.eigenvalue_evolution:
            self.compute_eigenvalue_evolution(matrix_type)
        evo = self.eigenvalue_evolution[matrix_type]
        if len(evo) < 2:
            return None
        n_vals = len(evo[0])
        forecasts = []
        for i in range(n_vals):
            series = [e[i] for e in evo]
            if method == 'linear':
                x = np.arange(len(series))
                coeff = np.polyfit(x, series, 1)
                poly = np.poly1d(coeff)
                f = poly(len(series) + steps - 1)
            elif method == 'arima':
                try:
                    from statsmodels.tsa.arima.model import ARIMA
                    model = ARIMA(series, order=(1, 0, 0))
                    fit = model.fit()
                    f = fit.forecast(steps=steps)[-1]
                except ImportError:
                    f = series[-1]
            else:
                f = series[-1]
            forecasts.append(f)
        return np.array(forecasts)


# ============================================================================
# Multiview spectral clustering
# ============================================================================

def multiview_spectral_clustering(
    graphs: List[Union[nx.Graph, SpectralGraphAnalysis, np.ndarray]],
    n_clusters: int = 2,
    fusion: str = 'average',
    weights: Optional[List[float]] = None,
    **kwargs,
) -> List[int]:
    laplacians = []
    n_nodes = None
    for g in graphs:
        if isinstance(g, SpectralGraphAnalysis):
            L = g.get_matrix(SpectralType.NORMALIZED_LAPLACIAN)
        elif isinstance(g, np.ndarray):
            deg = np.sum(g, axis=1)
            with np.errstate(divide='ignore'):
                d_inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0)
            L = np.eye(g.shape[0]) - d_inv_sqrt[:, None] * g * d_inv_sqrt[None, :]
        else:  # NetworkX
            L = nx.normalized_laplacian_matrix(g).todense()
        if n_nodes is None:
            n_nodes = L.shape[0]
        elif L.shape[0] != n_nodes:
            raise ValueError("All views must have the same number of nodes.")
        laplacians.append(L)
    if fusion == 'average':
        if weights is None:
            weights = [1.0 / len(laplacians)] * len(laplacians)
        combined = sum(w * L for w, L in zip(weights, laplacians))
        sa = SpectralGraphAnalysis(combined)
        return sa.spectral_clustering(n_clusters=n_clusters, **kwargs)
    elif fusion == 'product':
        combined = laplacians[0]
        for L in laplacians[1:]:
            combined = np.kron(combined, L)
        sa = SpectralGraphAnalysis(combined)
        return sa.spectral_clustering(n_clusters=n_clusters, **kwargs)
    else:
        raise ValueError(f"Unknown fusion method: {fusion}")


# ============================================================================
# Convenience factory functions
# ============================================================================

def spectral_analysis_from_networkx(graph: nx.Graph, **kwargs) -> SpectralGraphAnalysis:
    return SpectralGraphAnalysis(graph, **kwargs)

def spectral_analysis_from_adjacency(
    adj: np.ndarray, directed: bool = False, weighted: bool = False
) -> SpectralGraphAnalysis:
    return SpectralGraphAnalysis(adj, directed=directed, weighted=weighted, graph_id="matrix")