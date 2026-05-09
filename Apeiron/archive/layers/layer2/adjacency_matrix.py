"""
ADJACENCY MATRIX AND SPECTRAL ANALYSIS – ULTIMATE IMPLEMENTATION
=================================================================
This module provides a comprehensive toolkit for spectral graph analysis,
including:

- Construction of graph matrices (adjacency, Laplacian, normalized Laplacian,
  signless Laplacian, random walk Laplacian, modularity matrix, etc.)
- Eigenvalue decomposition (dense / sparse, CPU / GPU)
- Spectral invariants (algebraic connectivity, spectral gap, Estrada index,
  number of spanning trees, effective resistance, von Neumann entropy)
- Spectral clustering (with automatic k selection via eigengap)
- Spectral embedding for graph visualisation
- Graph Fourier transform (GFT) and spectral filtering (Chebyshev)
- Heat kernel and heat kernel trace
- Spectral distances and alignment between graphs
- Handling of directed and weighted graphs
- Support for multiple graph libraries: NetworkX, igraph, graph-tool (optional)
- Parallel / distributed computation for large graphs (via Dask or Ray – optional)
- Caching of results (in‑memory / Redis)
- Visualisation with matplotlib and Plotly
- Integration with Layer 1: build graph from registry with atomicity weights,
  atomicity‑weighted Laplacian, and snapshot from temporal phase.

**NIEUWE UITBREIDINGEN:**
- Multiview spectral clustering – combineer meerdere grafweergaven voor clustering
- Dynamische spectrale analyse – evolutie van spectra over tijd, change point detectie
- Extra spectrale invarianten – graafenergie, spectrale momenten, Kirchhoff‑index, spectrale complexiteit
- **Multiparameter spectrale persistentie** – analyse van eigenwaardereeksen over twee parameters (tijd + schaal)
- **Causale analyse van eigenwaardereeksen** – Granger‑causaliteit tussen eigenwaarden
- **Performance optimalisatie** – Numba‑versnelling voor intensieve functies
- **Database‑integratie** – opslag en laden van spectra in HDF5, SQLite, Neo4j
- **Interactieve dashboards** – real‑time visualisatie met Plotly Dash
- **Layer 1 integratie** – `from_layer1_registry`, `compute_atomicity_laplacian`, `snapshot_from_phase`

All features degrade gracefully if required libraries are missing.
"""

import numpy as np
import logging
import time
import hashlib
import pickle
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)

# ============================================================================
# OPTIONAL LIBRARIES – HANDLED WITH GRACE
# ============================================================================

# NetworkX for graph handling
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not available – graph input must be precomputed matrices")

# igraph (optional)
try:
    import igraph as ig
    HAS_IGRAPH = True
except ImportError:
    HAS_IGRAPH = False

# graph-tool (optional)
try:
    import graph_tool as gt
    from graph_tool.spectral import adjacency as gt_adjacency
    HAS_GRAPHTOOL = True
except ImportError:
    HAS_GRAPHTOOL = False

# SciPy for dense / sparse linear algebra
try:
    import scipy.sparse as sp
    from scipy.sparse.linalg import eigsh, eigs, svds
    from scipy.linalg import eigh, expm, logm, sqrtm
    from scipy.sparse.csgraph import laplacian as csgraph_laplacian
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logger.warning("SciPy not available – advanced linear algebra disabled")

# PyTorch for GPU acceleration (optional)
try:
    import torch
    HAS_TORCH = True
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    HAS_TORCH = False
    CUDA_AVAILABLE = False
    logger.warning("PyTorch not available – GPU acceleration disabled")

# Dask / Ray for distributed computing (optional)
try:
    import dask
    from dask.distributed import Client, get_client
    HAS_DASK = True
except ImportError:
    HAS_DASK = False

try:
    import ray
    HAS_RAY = True
except ImportError:
    HAS_RAY = False

# Redis for distributed caching
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available – distributed caching disabled")

# Matplotlib for visualisation (optional)
try:
    import matplotlib.pyplot as plt
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logger.warning("Matplotlib not available – visualisation disabled")

# Plotly for interactive visualisation (optional)
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available – interactive plots disabled")

# Statsmodels voor tijdreeksanalyse (optioneel)
try:
    from statsmodels.tsa.stattools import grangercausalitytests
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

# ARIMA voor forecasting
try:
    from statsmodels.tsa.arima.model import ARIMA
    HAS_ARIMA = True
except ImportError:
    HAS_ARIMA = False

# Numba voor versnelling (optioneel)
try:
    from numba import jit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

# Multipers voor multiparameter persistentie (optioneel)
try:
    from multipers import MultiparameterPersistence, Bifiltration
    HAS_MULTIPERS = True
except ImportError:
    HAS_MULTIPERS = False

# GUDHI als alternatief voor persistentie
try:
    import gudhi as gd
    HAS_GUDHI = True
except ImportError:
    HAS_GUDHI = False

# SQLite voor database opslag
try:
    import sqlite3
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False

# Neo4j driver (optioneel)
try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

# Dash voor interactieve dashboards (optioneel)
try:
    import dash
    from dash import dcc, html, Input, Output
    HAS_DASH = True
except ImportError:
    HAS_DASH = False

# ============================================================================
# ENUMS – Matrix Types and Options
# ============================================================================
class SpectralType(Enum):
    """Types of graph matrices for spectral analysis."""
    ADJACENCY = "adjacency"                     # A
    LAPLACIAN = "laplacian"                     # L = D - A
    NORMALIZED_LAPLACIAN = "normalized_laplacian"  # L_norm = I - D^{-1/2} A D^{-1/2}
    SIGNLESS_LAPLACIAN = "signless_laplacian"   # Q = D + A
    RANDOM_WALK = "random_walk"                  # P = D^{-1} A
    MODULARITY = "modularity"                    # B = A - (d d^T)/(2m)
    NORMALIZED_ADJACENCY = "normalized_adjacency" # A_norm = D^{-1/2} A D^{-1/2}
    IN_OUT_LAPLACIAN = "in_out_laplacian"        # for directed graphs

class GraphType(Enum):
    """Type of graph (directedness, weight)."""
    UNDIRECTED = "undirected"
    DIRECTED = "directed"
    WEIGHTED = "weighted"
    UNWEIGHTED = "unweighted"

# ============================================================================
# CACHING DECORATOR
# ============================================================================
def cached(ttl: int = 3600, key_prefix: str = "spectral"):
    """Decorator to cache results (in‑memory + optional Redis)."""
    def decorator(func):
        _cache = {}
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Build cache key
            key_parts = [func.__name__, str(self.graph_id)] + [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
            full_key = f"{key_prefix}:{key}"

            # Memory cache
            if full_key in _cache:
                val, exp = _cache[full_key]
                if time.time() < exp:
                    return val
                else:
                    del _cache[full_key]

            # Redis cache
            if REDIS_AVAILABLE and hasattr(self, '_redis_client') and self._redis_client:
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    data = loop.run_until_complete(self._redis_client.get(full_key))
                    if data:
                        val = pickle.loads(data)
                        return val
                except Exception as e:
                    logger.debug(f"Redis cache error: {e}")

            # Compute
            result = func(self, *args, **kwargs)

            # Store in memory
            _cache[full_key] = (result, time.time() + ttl)

            # Async Redis store
            if REDIS_AVAILABLE and hasattr(self, '_redis_client') and self._redis_client:
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
# PERFORMANCE OPTIMISATIES MET NUMBA
# ============================================================================
if HAS_NUMBA:
    @jit(nopython=True, parallel=True)
    def _chebyshev_filter_numba(M_scaled, signal, order, cutoff):
        """Numba‑versnelde Chebyshev‑filter."""
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
            # f += c * f_prev
            for j in prange(n):
                f[j] += c * f_prev[j]
            # Recurrence: f_next = 2 * (M_scaled @ f_prev) - f_prev2
            f_next = np.zeros(n, dtype=np.float64)
            # Matrix-vector product (dense)
            for j in range(n):
                s = 0.0
                for k in range(n):
                    s += M_scaled[j, k] * f_prev[k]
                f_next[j] = 2 * s - f_prev2[j]
            f_prev2 = f_prev
            f_prev = f_next
        return f

# ============================================================================
# SPECTRAL GRAPH ANALYSIS – MAIN CLASS
# ============================================================================
@dataclass
class SpectralGraphAnalysis:
    """
    Comprehensive spectral analysis of graphs.

    Attributes:
        graph: a graph object from NetworkX, igraph, graph-tool, or adjacency matrix as numpy/scipy array
        graph_id: unique identifier for caching
        directed: whether the graph is directed
        weighted: whether the graph has edge weights
        matrices: dictionary of precomputed matrices (lazy)
        eigenvalues: dictionary of eigenvalues for each matrix type
        eigenvectors: dictionary of eigenvectors (columns)
        invariants: dictionary of computed invariants
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
        # Detect graph type and set directed/weighted flags
        if HAS_NETWORKX and isinstance(self.graph, nx.Graph):
            self.directed = self.graph.is_directed()
            self.weighted = nx.is_weighted(self.graph)
        elif HAS_IGRAPH and isinstance(self.graph, ig.Graph):
            self.directed = self.graph.is_directed()
            self.weighted = 'weight' in self.graph.edge_attributes()
        elif HAS_GRAPHTOOL and isinstance(self.graph, gt.Graph):
            self.directed = self.graph.is_directed()
            self.weighted = False  # user must set manually
        elif isinstance(self.graph, (np.ndarray, sp.spmatrix)):
            pass  # assume flags are set by user
        else:
            logger.warning("Unknown graph type; assuming directed/weighted flags are correctly set by user.")
        self._setup_redis()

    def _setup_redis(self):
        if REDIS_AVAILABLE:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.Redis.from_url("redis://localhost:6379")
            except:
                pass

    def __repr__(self) -> str:
        n = self.get_matrix(SpectralType.ADJACENCY).shape[0] if hasattr(self, '_matrices') else 0
        return f"SpectralGraphAnalysis(id={self.graph_id}, nodes={n}, directed={self.directed}, weighted={self.weighted})"

    # ------------------------------------------------------------------------
    # Matrix construction
    # ------------------------------------------------------------------------
    def _get_adjacency(self) -> np.ndarray:
        """Return adjacency matrix as dense numpy array."""
        if 'adjacency' in self._matrices:
            return self._matrices['adjacency']
        # Try NetworkX first
        if HAS_NETWORKX and isinstance(self.graph, nx.Graph):
            A = nx.adjacency_matrix(self.graph, weight='weight' if self.weighted else None).todense()
        # Then igraph
        elif HAS_IGRAPH and isinstance(self.graph, ig.Graph):
            if self.weighted:
                weights = self.graph.es['weight'] if 'weight' in self.graph.edge_attributes() else None
                A = self.graph.get_adjacency_sparse(attribute='weight' if weights else None).todense()
            else:
                A = self.graph.get_adjacency_sparse().todense()
        # Then graph-tool
        elif HAS_GRAPHTOOL and isinstance(self.graph, gt.Graph):
            from graph_tool.spectral import adjacency
            A = adjacency(self.graph).todense()
        elif isinstance(self.graph, np.ndarray):
            A = self.graph
        elif isinstance(self.graph, sp.spmatrix):
            A = self.graph.todense()
        else:
            raise ValueError("Cannot construct adjacency matrix from given graph")
        self._matrices['adjacency'] = A
        return A

    def _get_degrees(self) -> np.ndarray:
        """Return degree vector (out-degree for directed)."""
        A = self._get_adjacency()
        if self.directed:
            out_deg = np.array(A.sum(axis=1)).flatten()
            in_deg = np.array(A.sum(axis=0)).flatten()
            return out_deg, in_deg
        else:
            deg = np.array(A.sum(axis=1)).flatten()
            return deg

    def get_matrix(self, matrix_type: SpectralType) -> np.ndarray:
        """Return requested matrix, computing if necessary."""
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
                self._matrices[key] = L_norm
                return L_norm
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
                self._matrices[key] = A_norm
                return A_norm
            elif matrix_type == SpectralType.MODULARITY:
                m = A.sum() / 2
                deg_outer = np.outer(deg, deg)
                B = A - deg_outer / (2 * m)
            else:
                raise ValueError(f"Unsupported matrix type for undirected graph: {matrix_type}")
        else:
            # Directed graph
            out_deg, in_deg = self._get_degrees()
            if matrix_type == SpectralType.ADJACENCY:
                M = A
            elif matrix_type == SpectralType.IN_OUT_LAPLACIAN:
                # Out‑degree Laplacian: L_out = D_out - A
                L = np.diag(out_deg) - A
                M = L
            else:
                raise ValueError(f"Matrix type {matrix_type} not defined for directed graphs")
        self._matrices[key] = M
        return M

    # ------------------------------------------------------------------------
    # Eigenvalue decomposition (with GPU support)
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def compute_eigensystem(self, matrix_type: SpectralType = SpectralType.LAPLACIAN,
                            k: Optional[int] = None, which: str = 'LM',
                            use_gpu: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute eigenvalues and eigenvectors.

        Args:
            matrix_type: type of matrix to decompose
            k: number of eigenvalues to compute (None = all)
            which: which eigenvalues (e.g., 'LM' largest magnitude, 'SM' smallest)
            use_gpu: use PyTorch GPU if available

        Returns:
            eigenvalues (1D array), eigenvectors (columns as eigenvectors)
        """
        M = self.get_matrix(matrix_type)
        n = M.shape[0]
        if k is None or k >= n:
            k = n

        # Try GPU first if requested and available
        if use_gpu and HAS_TORCH and CUDA_AVAILABLE:
            try:
                M_t = torch.tensor(M, dtype=torch.float64, device='cuda')
                if k == n:
                    eigvals, eigvecs = torch.linalg.eigh(M_t)
                else:
                    if which == 'SM':
                        eigvals, eigvecs = torch.lobpcg(M_t, k=k, largest=False)
                    else:
                        eigvals, eigvecs = torch.lobpcg(M_t, k=k, largest=True)
                eigvals = eigvals.cpu().numpy()
                eigvecs = eigvecs.cpu().numpy()
                self._eigen[matrix_type.value] = (eigvals, eigvecs)
                return eigvals, eigvecs
            except Exception as e:
                logger.warning(f"GPU eigensolver failed, falling back to CPU: {e}")

        # CPU with SciPy
        if HAS_SCIPY:
            if sp.issparse(M):
                M_sp = sp.csr_matrix(M)
                if k < n:
                    if which in ['LM', 'SM']:
                        if matrix_type in [SpectralType.LAPLACIAN, SpectralType.NORMALIZED_LAPLACIAN,
                                           SpectralType.SIGNLESS_LAPLACIAN, SpectralType.NORMALIZED_ADJACENCY]:
                            sigma = None
                            if which == 'SM':
                                sigma = 1e-5
                            eigvals, eigvecs = eigsh(M_sp, k=k, which=which, sigma=sigma)
                        else:
                            eigvals, eigvecs = eigs(M_sp, k=k, which=which)
                            eigvals = eigvals.real
                    else:
                        eigvals, eigvecs = np.linalg.eigh(M)
                else:
                    eigvals, eigvecs = np.linalg.eigh(M)
            else:
                if k == n:
                    eigvals, eigvecs = np.linalg.eigh(M)
                else:
                    if matrix_type in [SpectralType.LAPLACIAN, SpectralType.NORMALIZED_LAPLACIAN,
                                       SpectralType.SIGNLESS_LAPLACIAN, SpectralType.NORMALIZED_ADJACENCY]:
                        eigvals, eigvecs = eigh(M, subset_by_index=(0, k-1))
                    else:
                        eigvals, eigvecs = np.linalg.eig(M)
                        idx = np.argsort(eigvals)
                        eigvals = eigvals[idx][:k]
                        eigvecs = eigvecs[:, idx][:, :k]
        else:
            eigvals, eigvecs = np.linalg.eigh(M)
            if k < n:
                eigvals = eigvals[:k]
                eigvecs = eigvecs[:, :k]

        self._eigen[matrix_type.value] = (eigvals, eigvecs)
        return eigvals, eigvecs

    # ------------------------------------------------------------------------
    # Spectral invariants
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def algebraic_connectivity(self) -> float:
        """Second smallest eigenvalue of Laplacian (for undirected)."""
        if self.directed:
            logger.warning("Algebraic connectivity not defined for directed graphs; using symmetrized Laplacian.")
        eigvals, _ = self.compute_eigensystem(SpectralType.LAPLACIAN, k=2, which='SM')
        if len(eigvals) >= 2:
            return float(eigvals[1])
        return 0.0

    @cached(ttl=3600)
    def spectral_gap(self) -> float:
        """Difference between two smallest eigenvalues (or largest if directed)."""
        if self.directed:
            eigvals, _ = self.compute_eigensystem(SpectralType.ADJACENCY, k=2, which='LM')
            if len(eigvals) >= 2:
                return float(eigvals[0] - eigvals[1])
            return 0.0
        else:
            eigvals, _ = self.compute_eigensystem(SpectralType.LAPLACIAN, k=2, which='SM')
            if len(eigvals) >= 2:
                return float(eigvals[1] - eigvals[0])
            return 0.0

    @cached(ttl=3600)
    def spectral_radius(self) -> float:
        """Largest absolute eigenvalue of adjacency matrix."""
        eigvals, _ = self.compute_eigensystem(SpectralType.ADJACENCY, k=1, which='LM')
        return float(abs(eigvals[0]))

    @cached(ttl=3600)
    def estrada_index(self) -> float:
        """Sum of diagonal entries of exp(A)."""
        A = self.get_matrix(SpectralType.ADJACENCY)
        if HAS_SCIPY:
            expA = expm(A)
        else:
            eigvals, eigvecs = self.compute_eigensystem(SpectralType.ADJACENCY)
            expA = eigvecs @ np.diag(np.exp(eigvals)) @ eigvecs.T
        return float(np.trace(expA))

    @cached(ttl=3600)
    def number_of_spanning_trees(self) -> float:
        """Kirchhoff's theorem: any cofactor of Laplacian."""
        if self.directed:
            return 0.0
        L = self.get_matrix(SpectralType.LAPLACIAN)
        L_minor = L[1:, 1:]
        return float(np.linalg.det(L_minor))

    @cached(ttl=3600)
    def effective_resistance(self, i: int, j: int) -> float:
        """Effective resistance between nodes i and j using pseudoinverse of Laplacian."""
        if self.directed:
            return 0.0
        L = self.get_matrix(SpectralType.LAPLACIAN)
        if HAS_SCIPY:
            L_pinv = np.linalg.pinv(L)
        else:
            eigvals, eigvecs = self.compute_eigensystem(SpectralType.LAPLACIAN)
            non_zero = eigvals > 1e-12
            L_pinv = eigvecs[:, non_zero] @ np.diag(1.0 / eigvals[non_zero]) @ eigvecs[:, non_zero].T
        return float(L_pinv[i, i] + L_pinv[j, j] - 2 * L_pinv[i, j])

    # ------------------------------------------------------------------------
    # Von Neumann entropy
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def von_neumann_entropy(self, matrix_type: SpectralType = SpectralType.NORMALIZED_LAPLACIAN) -> float:
        """
        Compute the von Neumann entropy of the graph:
            S = - Tr(ρ log ρ)  with ρ = exp(-τ L) / Z  (here τ = 1)
        For the normalized Laplacian, the entropy is - Σ λ_i log λ_i (with 0 log 0 = 0).
        """
        eigvals, _ = self.compute_eigensystem(matrix_type)
        eigvals = eigvals[eigvals > 1e-12]
        if len(eigvals) == 0:
            return 0.0
        p = eigvals / np.sum(eigvals)
        return -np.sum(p * np.log(p))

    # ------------------------------------------------------------------------
    # Chebyshev filter (met Numba optimalisatie)
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def chebyshev_filter(self, signal: np.ndarray, cutoff: float, order: int = 10,
                         matrix_type: SpectralType = SpectralType.LAPLACIAN,
                         use_numba: bool = True) -> np.ndarray:
        """
        Apply a Chebyshev low‑pass filter to a graph signal.
        Uses the Chebyshev polynomial approximation of the filter function.
        (Requires scipy.sparse for efficient matrix‑vector products.)
        """
        if not HAS_SCIPY:
            logger.warning("Chebyshev filter requires SciPy – returning original signal")
            return signal
        M = self.get_matrix(matrix_type)
        lmax = self.spectral_radius() * 1.01
        M_scaled = (2 / lmax) * M - np.eye(M.shape[0])

        if use_numba and HAS_NUMBA:
            return _chebyshev_filter_numba(M_scaled, signal, order, cutoff)
        else:
            a0 = 2 / lmax
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
                f_prev2 = f_prev
                f_prev = f_next
            return f

    # ------------------------------------------------------------------------
    # Heat kernel and heat kernel trace
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def heat_kernel(self, t: float, matrix_type: SpectralType = SpectralType.LAPLACIAN) -> np.ndarray:
        """
        Compute the heat kernel matrix K = exp(-t L).
        """
        eigvals, eigvecs = self.compute_eigensystem(matrix_type)
        return eigvecs @ np.diag(np.exp(-t * eigvals)) @ eigvecs.T

    @cached(ttl=3600)
    def heat_kernel_trace(self, t: float, matrix_type: SpectralType = SpectralType.LAPLACIAN) -> float:
        """Trace of the heat kernel = Σ exp(-t λ_i)."""
        eigvals, _ = self.compute_eigensystem(matrix_type)
        return float(np.sum(np.exp(-t * eigvals)))

    # ------------------------------------------------------------------------
    # Spectral modularity gap
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def spectral_modularity_gap(self) -> float:
        """
        Gap between the largest and second‑largest eigenvalues of the modularity matrix.
        A large gap often indicates a strong community structure.
        """
        try:
            B = self.get_matrix(SpectralType.MODULARITY)
        except ValueError:
            logger.warning("Modularity matrix not defined for this graph")
            return 0.0
        eigvals, _ = self.compute_eigensystem(SpectralType.MODULARITY, k=2, which='LM')
        if len(eigvals) < 2:
            return 0.0
        return float(eigvals[0] - eigvals[1])

    # ------------------------------------------------------------------------
    # Spectral alignment between two graphs
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def spectral_alignment(self, other: 'SpectralGraphAnalysis', dim: int = 10,
                           matrix_type: SpectralType = SpectralType.LAPLACIAN) -> float:
        """
        Compute a simple spectral alignment score between two graphs.
        Uses the first `dim` eigenvectors and computes the Frobenius norm of their difference
        after aligning signs (since eigenvectors are defined up to sign).
        """
        eig1, vecs1 = self.compute_eigensystem(matrix_type, k=dim, which='SM' if matrix_type in [SpectralType.LAPLACIAN] else 'LM')
        eig2, vecs2 = other.compute_eigensystem(matrix_type, k=dim, which='SM' if matrix_type in [SpectralType.LAPLACIAN] else 'LM')
        min_dim = min(dim, vecs1.shape[1], vecs2.shape[1])
        for i in range(min_dim):
            if np.dot(vecs1[:, i], vecs2[:, i]) < 0:
                vecs2[:, i] *= -1
        diff = vecs1[:, :min_dim] - vecs2[:, :min_dim]
        return float(np.linalg.norm(diff))

    # ------------------------------------------------------------------------
    # SPECTRAL INVARIANTS (new methods)
    # ------------------------------------------------------------------------
    def graph_energy(self) -> float:
        """
        Graph energy: sum of absolute eigenvalues of the adjacency matrix.
        """
        eigvals, _ = self.compute_eigensystem(SpectralType.ADJACENCY)
        return float(np.sum(np.abs(eigvals)))

    def spectral_moment(self, k: int, matrix_type: SpectralType = SpectralType.ADJACENCY) -> float:
        """
        k‑th spectral moment: sum of λ_i^k.
        """
        eigvals, _ = self.compute_eigensystem(matrix_type)
        return float(np.sum(eigvals ** k))

    def kirchhoff_index(self) -> float:
        """
        Kirchhoff index: sum of effective resistances over all pairs.
        """
        if self.directed:
            logger.warning("Kirchhoff index not defined for directed graphs")
            return 0.0
        n = self.get_matrix(SpectralType.LAPLACIAN).shape[0]
        total = 0.0
        for i in range(n):
            for j in range(i+1, n):
                total += self.effective_resistance(i, j)
        return total

    def spectral_complexity(self, matrix_type: SpectralType = SpectralType.NORMALIZED_LAPLACIAN) -> float:
        """
        Spectral complexity: - Σ p_i log p_i with p_i = λ_i / Σ λ.
        """
        eigvals, _ = self.compute_eigensystem(matrix_type)
        eigvals = eigvals[eigvals > 1e-12]
        if len(eigvals) == 0:
            return 0.0
        p = eigvals / np.sum(eigvals)
        return -np.sum(p * np.log(p))

    def spectral_skewness(self, matrix_type: SpectralType = SpectralType.LAPLACIAN) -> float:
        """
        Skewness of eigenvalue distribution (third standardized moment).
        """
        eigvals, _ = self.compute_eigensystem(matrix_type)
        if len(eigvals) < 3:
            return 0.0
        mean = np.mean(eigvals)
        std = np.std(eigvals)
        if std == 0:
            return 0.0
        return float(np.mean((eigvals - mean)**3) / std**3)

    def spectral_kurtosis(self, matrix_type: SpectralType = SpectralType.LAPLACIAN) -> float:
        """
        Kurtosis of eigenvalue distribution (fourth standardized moment).
        (Excess kurtosis, i.e., minus 3 for normal distribution.)
        """
        eigvals, _ = self.compute_eigensystem(matrix_type)
        if len(eigvals) < 4:
            return 0.0
        mean = np.mean(eigvals)
        std = np.std(eigvals)
        if std == 0:
            return 0.0
        return float(np.mean((eigvals - mean)**4) / std**4 - 3)

    def spectral_distribution_entropy(self, matrix_type: SpectralType = SpectralType.LAPLACIAN,
                                       bins: int = 50) -> float:
        """
        Shannon entropy of the eigenvalue distribution (discretized histogram).
        """
        eigvals, _ = self.compute_eigensystem(matrix_type)
        hist, _ = np.histogram(eigvals, bins=bins, density=True)
        hist = hist[hist > 0]
        if len(hist) == 0:
            return 0.0
        return float(-np.sum(hist * np.log(hist)))

    # ------------------------------------------------------------------------
    # Spectral embedding
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def spectral_embedding(self, dim: int = 2, matrix_type: SpectralType = SpectralType.LAPLACIAN) -> np.ndarray:
        """
        Compute low‑dimensional embedding using eigenvectors.
        For Laplacian, use smallest non‑zero eigenvectors.
        For adjacency, use largest eigenvectors.
        """
        if matrix_type in [SpectralType.LAPLACIAN, SpectralType.NORMALIZED_LAPLACIAN]:
            which = 'SM'
            k = dim + 1
        else:
            which = 'LM'
            k = dim
        eigvals, eigvecs = self.compute_eigensystem(matrix_type, k=k, which=which)
        if matrix_type in [SpectralType.LAPLACIAN, SpectralType.NORMALIZED_LAPLACIAN]:
            embed = eigvecs[:, 1:dim+1]
        else:
            embed = eigvecs[:, :dim]
        return embed

    # ------------------------------------------------------------------------
    # Graph Fourier transform
    # ------------------------------------------------------------------------
    def gft(self, signal: np.ndarray, matrix_type: SpectralType = SpectralType.LAPLACIAN) -> np.ndarray:
        """Graph Fourier transform: project signal onto eigenvectors."""
        eigvals, eigvecs = self.compute_eigensystem(matrix_type)
        return eigvecs.T @ signal

    def igft(self, coeffs: np.ndarray, matrix_type: SpectralType = SpectralType.LAPLACIAN) -> np.ndarray:
        """Inverse GFT."""
        eigvals, eigvecs = self.compute_eigensystem(matrix_type)
        return eigvecs @ coeffs

    # ------------------------------------------------------------------------
    # Spectral clustering (with automatic k)
    # ------------------------------------------------------------------------
    @cached(ttl=3600)
    def spectral_clustering(self, n_clusters: Optional[int] = None,
                            matrix_type: SpectralType = SpectralType.LAPLACIAN) -> List[int]:
        """
        Perform spectral clustering.

        Args:
            n_clusters: number of clusters (if None, estimate via eigengap)
            matrix_type: matrix to use for embedding (typically Laplacian)

        Returns:
            list of cluster labels for each node (in order of original graph)
        """
        if n_clusters is None:
            eigvals, _ = self.compute_eigensystem(matrix_type, k=min(20, self.get_matrix(matrix_type).shape[0]))
            if matrix_type in [SpectralType.LAPLACIAN, SpectralType.NORMALIZED_LAPLACIAN]:
                gaps = np.diff(eigvals[1:])
                if len(gaps) == 0:
                    n_clusters = 1
                else:
                    n_clusters = np.argmax(gaps) + 2
            else:
                gaps = np.diff(eigvals)
                if len(gaps) == 0:
                    n_clusters = 1
                else:
                    n_clusters = np.argmax(gaps) + 1

        embed = self.spectral_embedding(dim=n_clusters, matrix_type=matrix_type)
        if HAS_SCIPY:
            from scipy.cluster.vq import kmeans2
            centroids, labels = kmeans2(embed, n_clusters)
        else:
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=n_clusters, n_init=10)
            labels = kmeans.fit_predict(embed)
        return labels.tolist()

    # ------------------------------------------------------------------------
    # Spectral distance between graphs
    # ------------------------------------------------------------------------
    @staticmethod
    def spectral_distance(graph1: 'SpectralGraphAnalysis', graph2: 'SpectralGraphAnalysis',
                          matrix_type: SpectralType = SpectralType.LAPLACIAN,
                          k: int = 10) -> float:
        """
        Compute spectral distance between two graphs as L2 difference of their
        first k eigenvalues.
        """
        eig1, _ = graph1.compute_eigensystem(matrix_type, k=k, which='SM' if matrix_type in [SpectralType.LAPLACIAN] else 'LM')
        eig2, _ = graph2.compute_eigensystem(matrix_type, k=k, which='SM' if matrix_type in [SpectralType.LAPLACIAN] else 'LM')
        min_len = min(len(eig1), len(eig2))
        return float(np.linalg.norm(eig1[:min_len] - eig2[:min_len]))

    # ------------------------------------------------------------------------
    # Parallel computation for multiple graphs (using Dask)
    # ------------------------------------------------------------------------
    @staticmethod
    def parallel_compute_eigensystem(graphs: List[Any], matrix_type: SpectralType = SpectralType.LAPLACIAN,
                                      k: Optional[int] = None, which: str = 'LM',
                                      use_dask: bool = True) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Compute eigensystems for multiple graphs in parallel using Dask (if available).
        Returns list of (eigenvalues, eigenvectors) for each graph.
        """
        if not HAS_DASK or not use_dask:
            results = []
            for g in graphs:
                sa = SpectralGraphAnalysis(g)
                results.append(sa.compute_eigensystem(matrix_type, k, which))
            return results

        from dask.distributed import get_client
        try:
            client = get_client()
        except:
            client = Client()

        def compute_one(g):
            sa = SpectralGraphAnalysis(g)
            return sa.compute_eigensystem(matrix_type, k, which)

        futures = client.map(compute_one, graphs)
        results = client.gather(futures)
        return results

    # ------------------------------------------------------------------------
    # I/O and helpers
    # ------------------------------------------------------------------------
    def get_invariants(self) -> Dict[str, Any]:
        """Compute and return all invariants as a dictionary."""
        inv = {}
        try: inv['algebraic_connectivity'] = self.algebraic_connectivity()
        except: inv['algebraic_connectivity'] = None
        try: inv['spectral_gap'] = self.spectral_gap()
        except: inv['spectral_gap'] = None
        try: inv['spectral_radius'] = self.spectral_radius()
        except: inv['spectral_radius'] = None
        try: inv['estrada_index'] = self.estrada_index()
        except: inv['estrada_index'] = None
        try: inv['number_of_spanning_trees'] = self.number_of_spanning_trees()
        except: inv['number_of_spanning_trees'] = None
        try: inv['von_neumann_entropy'] = self.von_neumann_entropy()
        except: inv['von_neumann_entropy'] = None
        try: inv['graph_energy'] = self.graph_energy()
        except: inv['graph_energy'] = None
        try: inv['kirchhoff_index'] = self.kirchhoff_index()
        except: inv['kirchhoff_index'] = None
        try: inv['spectral_complexity'] = self.spectral_complexity()
        except: inv['spectral_complexity'] = None
        try: inv['spectral_skewness'] = self.spectral_skewness()
        except: inv['spectral_skewness'] = None
        try: inv['spectral_kurtosis'] = self.spectral_kurtosis()
        except: inv['spectral_kurtosis'] = None
        try: inv['spectral_distribution_entropy'] = self.spectral_distribution_entropy()
        except: inv['spectral_distribution_entropy'] = None
        return inv

    def plot_spectrum(self, matrix_type: SpectralType = SpectralType.LAPLACIAN,
                      filename: Optional[str] = None):
        """Plot eigenvalue distribution using matplotlib."""
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Visualisation not available")
            return
        eigvals, _ = self.compute_eigensystem(matrix_type)
        plt.figure(figsize=(8,4))
        plt.hist(eigvals, bins=50, alpha=0.7)
        plt.xlabel('eigenvalue')
        plt.ylabel('count')
        plt.title(f'Eigenvalue spectrum ({matrix_type.value})')
        if filename:
            plt.savefig(filename)
        else:
            plt.show()
        plt.close()

    def plot_spectrum_plotly(self, matrix_type: SpectralType = SpectralType.LAPLACIAN,
                              filename: Optional[str] = None):
        """Interactive spectrum plot using Plotly (if available)."""
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available – falling back to matplotlib")
            self.plot_spectrum(matrix_type, filename)
            return
        eigvals, _ = self.compute_eigensystem(matrix_type)
        fig = go.Figure(data=[go.Histogram(x=eigvals, nbinsx=50)])
        fig.update_layout(title=f'Eigenvalue spectrum ({matrix_type.value})',
                          xaxis_title='eigenvalue',
                          yaxis_title='count')
        if filename:
            fig.write_html(filename)
        else:
            fig.show()

    def plot_embedding(self, dim: int = 2, matrix_type: SpectralType = SpectralType.LAPLACIAN,
                       labels: Optional[List[int]] = None, filename: Optional[str] = None):
        """Plot spectral embedding (2D or 3D) using matplotlib."""
        if not VISUALIZATION_AVAILABLE:
            return
        embed = self.spectral_embedding(dim, matrix_type)
        if dim == 2:
            plt.figure(figsize=(8,6))
            if labels is not None:
                plt.scatter(embed[:,0], embed[:,1], c=labels, cmap='tab20', alpha=0.7)
            else:
                plt.scatter(embed[:,0], embed[:,1], alpha=0.7)
            plt.xlabel('eigenvector 1')
            plt.ylabel('eigenvector 2')
            plt.title('Spectral embedding')
        elif dim == 3:
            from mpl_toolkits.mplot3d import Axes3D
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            if labels is not None:
                ax.scatter(embed[:,0], embed[:,1], embed[:,2], c=labels, cmap='tab20', alpha=0.7)
            else:
                ax.scatter(embed[:,0], embed[:,1], embed[:,2], alpha=0.7)
            ax.set_xlabel('v1'); ax.set_ylabel('v2'); ax.set_zlabel('v3')
        if filename:
            plt.savefig(filename)
        else:
            plt.show()
        plt.close()

    # ------------------------------------------------------------------------
    # Layer 1 integration methods
    # ------------------------------------------------------------------------
    @classmethod
    def from_layer1_registry(cls, registry: Dict[str, Any],
                              similarity_threshold: float = 0.1,
                              similarity_func: Optional[Callable[[Any, Any], float]] = None,
                              weight_by_atomicity: bool = False,
                              **kwargs) -> 'SpectralGraphAnalysis':
        """
        Build a weighted graph from a Layer 1 registry.

        Nodes are the observable IDs in the registry. Edges are created between
        two observables if their similarity (computed by `similarity_func`) exceeds
        `similarity_threshold`. Edge weights are set to the similarity value.
        If `weight_by_atomicity` is True, node weights (atomicity scores) are stored
        as a node attribute for later use in `compute_atomicity_laplacian`.

        Args:
            registry: dict mapping observable ID to observable object. Observables should have
                      attributes like `qualitative_dims`, `relational_embedding`, `atomicity_score`.
            similarity_threshold: minimum similarity to create an edge.
            similarity_func: function that takes two observables and returns a float similarity.
                             If None, a default similarity combining qualitative_dims and relational_embedding is used.
            weight_by_atomicity: if True, store atomicity scores as node attributes 'atomicity'.
            **kwargs: passed to the SpectralGraphAnalysis constructor.

        Returns:
            A SpectralGraphAnalysis instance containing a NetworkX graph (if available) or an adjacency matrix.
        """
        if not HAS_NETWORKX:
            logger.warning("NetworkX not available; building adjacency matrix directly.")
            ids = list(registry.keys())
            n = len(ids)
            A = np.zeros((n, n))
            for i, id1 in enumerate(ids):
                for j, id2 in enumerate(ids):
                    if i == j:
                        continue
                    sim = cls._default_similarity(registry[id1], registry[id2]) if similarity_func is None else similarity_func(registry[id1], registry[id2])
                    if sim >= similarity_threshold:
                        A[i, j] = sim
                        if not kwargs.get('directed', False):
                            A[j, i] = sim
            return cls(A, directed=kwargs.get('directed', False), weighted=True, **kwargs)
        else:
            G = nx.Graph()
            ids = list(registry.keys())
            for id1 in ids:
                G.add_node(id1)
                if weight_by_atomicity and hasattr(registry[id1], 'atomicity_score'):
                    G.nodes[id1]['atomicity'] = registry[id1].atomicity_score
            for i, id1 in enumerate(ids):
                for j in range(i+1, len(ids)):
                    id2 = ids[j]
                    sim = cls._default_similarity(registry[id1], registry[id2]) if similarity_func is None else similarity_func(registry[id1], registry[id2])
                    if sim >= similarity_threshold:
                        G.add_edge(id1, id2, weight=sim)
            return cls(G, **kwargs)

    @staticmethod
    def _default_similarity(obs1, obs2) -> float:
        """Default similarity combining qualitative_dims and relational_embedding."""
        sim = 0.0
        count = 0
        if hasattr(obs1, 'qualitative_dims') and hasattr(obs2, 'qualitative_dims'):
            d1 = list(obs1.qualitative_dims.values())
            d2 = list(obs2.qualitative_dims.values())
            if d1 and d2:
                v1 = np.array(d1, dtype=float)
                v2 = np.array(d2, dtype=float)
                if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                    sim += np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                    count += 1
        if hasattr(obs1, 'relational_embedding') and hasattr(obs2, 'relational_embedding'):
            e1 = np.array(obs1.relational_embedding, dtype=float).flatten()
            e2 = np.array(obs2.relational_embedding, dtype=float).flatten()
            if e1.size > 0 and e2.size > 0 and np.linalg.norm(e1) > 0 and np.linalg.norm(e2) > 0:
                sim += np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2))
                count += 1
        if count == 0:
            return 0.0
        return sim / count

    def compute_atomicity_laplacian(self, atomicity_weights: Optional[Dict[Any, float]] = None) -> np.ndarray:
        """
        Compute an atomicity‑weighted Laplacian. If `atomicity_weights` is not provided,
        the method attempts to read node attributes 'atomicity' from the graph (if NetworkX is used).
        The weighted Laplacian is defined as L_atomicity = D_atomicity - A, where D_atomicity is
        a diagonal matrix with atomicity scores (or zero for nodes without score).

        Returns:
            numpy array: the atomicity‑weighted Laplacian matrix.
        """
        if HAS_NETWORKX and isinstance(self.graph, nx.Graph):
            if atomicity_weights is None:
                atomicity_weights = {}
                for node in self.graph.nodes():
                    if 'atomicity' in self.graph.nodes[node]:
                        atomicity_weights[node] = self.graph.nodes[node]['atomicity']
            A = self.get_matrix(SpectralType.ADJACENCY)
            nodes = list(self.graph.nodes())
            idx_map = {node: i for i, node in enumerate(nodes)}
            D_atomicity = np.zeros((len(nodes), len(nodes)))
            for node, weight in atomicity_weights.items():
                if node in idx_map:
                    D_atomicity[idx_map[node], idx_map[node]] = weight
            return D_atomicity - A
        else:
            if atomicity_weights is None:
                raise ValueError("atomicity_weights must be provided when graph is a plain matrix.")
            n = self.get_matrix(SpectralType.ADJACENCY).shape[0]
            D = np.diag([atomicity_weights.get(i, 0.0) for i in range(n)])
            A = self.get_matrix(SpectralType.ADJACENCY)
            return D - A


# ============================================================================
# NEW FUNCTIONS AND CLASSES
# ============================================================================

# ----------------------------------------------------------------------------
# Multiview spectral clustering
# ----------------------------------------------------------------------------
def multiview_spectral_clustering(
    graphs: List[Union[nx.Graph, SpectralGraphAnalysis, np.ndarray]],
    n_clusters: int = 2,
    fusion: str = 'average',
    weights: Optional[List[float]] = None,
    **kwargs
) -> List[int]:
    """
    Perform multiview spectral clustering on a list of graphs or matrices.

    Args:
        graphs: List of graphs (NetworkX, SpectralGraphAnalysis, or adjacency matrices)
        n_clusters: Number of clusters
        fusion: Fusion method ('average', 'product', 'co-training')
        weights: Optional weights for each view (only for 'average')
        **kwargs: Passed to individual spectral clustering

    Returns:
        List of cluster labels for the nodes (number of nodes must be consistent across views)
    """
    if not graphs:
        return []

    laplacians = []
    n_nodes = None
    for g in graphs:
        if isinstance(g, SpectralGraphAnalysis):
            L = g.get_matrix(SpectralType.NORMALIZED_LAPLACIAN)
        elif isinstance(g, nx.Graph):
            L = nx.normalized_laplacian_matrix(g).todense()
        elif isinstance(g, np.ndarray):
            deg = np.sum(g, axis=1)
            with np.errstate(divide='ignore'):
                d_inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0)
            L = np.eye(g.shape[0]) - d_inv_sqrt[:, None] * g * d_inv_sqrt[None, :]
        else:
            raise TypeError(f"Unknown graph type: {type(g)}")

        if n_nodes is None:
            n_nodes = L.shape[0]
        else:
            if L.shape[0] != n_nodes:
                raise ValueError("All views must have the same number of nodes")
        laplacians.append(L)

    if fusion == 'average':
        if weights is None:
            weights = [1.0 / len(laplacians)] * len(laplacians)
        else:
            weights = np.array(weights) / np.sum(weights)
        combined = np.zeros_like(laplacians[0])
        for L, w in zip(laplacians, weights):
            combined += w * L
        sa = SpectralGraphAnalysis(combined)
        return sa.spectral_clustering(n_clusters=n_clusters, matrix_type=SpectralType.NORMALIZED_LAPLACIAN, **kwargs)

    elif fusion == 'product':
        combined = laplacians[0]
        for L in laplacians[1:]:
            combined = np.kron(combined, L)
        sa = SpectralGraphAnalysis(combined)
        return sa.spectral_clustering(n_clusters=n_clusters, matrix_type=SpectralType.NORMALIZED_LAPLACIAN, **kwargs)

    elif fusion == 'co-training':
        labels = None
        for i, L in enumerate(laplacians):
            sa = SpectralGraphAnalysis(L)
            new_labels = sa.spectral_clustering(n_clusters=n_clusters, **kwargs)
            if labels is None:
                labels = new_labels
            else:
                labels = new_labels  # simplistic: take last view
        return labels

    else:
        raise ValueError(f"Unknown fusion method: {fusion}")


# ----------------------------------------------------------------------------
# Dynamic spectral analysis
# ----------------------------------------------------------------------------
class DynamicSpectralAnalysis:
    """
    Analyse the evolution of graph spectra over time.
    """

    def __init__(self):
        self.timestamps: List[float] = []
        self.graphs: List[Any] = []
        self.spectral_objects: List[SpectralGraphAnalysis] = []
        self.eigenvalue_evolution: Dict[SpectralType, List[np.ndarray]] = {}
        self._multiparameter_persistence = None

    def __repr__(self) -> str:
        return f"DynamicSpectralAnalysis(num_graphs={len(self.graphs)}, timestamps={len(self.timestamps)})"

    def add_graph(self, graph: Union[nx.Graph, np.ndarray], timestamp: Optional[float] = None):
        """Add a graph at a given timestamp."""
        if timestamp is None:
            timestamp = time.time()
        self.timestamps.append(timestamp)
        self.graphs.append(graph)
        sa = SpectralGraphAnalysis(graph)
        self.spectral_objects.append(sa)

    def snapshot_from_phase(self, registry: Dict[str, Any], phase: float,
                            phase_key: str = 'temporal_phase', tolerance: float = 1e-6,
                            **kwargs) -> Optional[SpectralGraphAnalysis]:
        """
        Build a graph snapshot from all observables whose temporal_phase is within
        `tolerance` of `phase`. The graph nodes are the observable IDs, and edges are
        created according to similarity (using the same method as `from_layer1_registry`).

        Args:
            registry: Layer 1 registry mapping observable ID to observable object.
            phase: target temporal phase.
            phase_key: attribute name of the temporal phase.
            tolerance: tolerance for phase matching.
            **kwargs: passed to `from_layer1_registry` (e.g., similarity_threshold).

        Returns:
            A SpectralGraphAnalysis instance containing the snapshot graph, or None if no
            observables match the phase.
        """
        filtered_ids = []
        for obs_id, obs in registry.items():
            if hasattr(obs, phase_key):
                p = getattr(obs, phase_key)
                if abs(p - phase) <= tolerance:
                    filtered_ids.append(obs_id)
        if not filtered_ids:
            return None
        filtered_registry = {oid: registry[oid] for oid in filtered_ids}
        return SpectralGraphAnalysis.from_layer1_registry(filtered_registry, **kwargs)

    def compute_eigenvalue_evolution(self, matrix_type: SpectralType = SpectralType.LAPLACIAN, k: Optional[int] = None,
                                      use_parallel: bool = False):
        """
        Compute the evolution of the first k eigenvalues over time.
        Result is stored in eigenvalue_evolution[matrix_type].
        If use_parallel=True and Dask available, computations are done in parallel.
        """
        if use_parallel and HAS_DASK:
            from dask.distributed import get_client
            try:
                client = get_client()
            except:
                client = Client()

            def compute_one(sa):
                return sa.compute_eigensystem(matrix_type, k=k, which='SM' if matrix_type in [SpectralType.LAPLACIAN, SpectralType.NORMALIZED_LAPLACIAN] else 'LM')[0]

            futures = client.map(compute_one, self.spectral_objects)
            evolutions = client.gather(futures)
        else:
            evolutions = []
            for sa in self.spectral_objects:
                eigvals, _ = sa.compute_eigensystem(matrix_type, k=k, which='SM' if matrix_type in [SpectralType.LAPLACIAN, SpectralType.NORMALIZED_LAPLACIAN] else 'LM')
                evolutions.append(eigvals)
        self.eigenvalue_evolution[matrix_type] = evolutions
        return evolutions

    def detect_change_points(self, matrix_type: SpectralType = SpectralType.LAPLACIAN, threshold: float = 0.1) -> List[int]:
        """
        Detect time points where a significant change in the spectrum occurs.
        Uses a simple threshold on the difference in eigenvalues.
        """
        if matrix_type not in self.eigenvalue_evolution:
            self.compute_eigenvalue_evolution(matrix_type)
        evo = self.eigenvalue_evolution[matrix_type]
        if len(evo) < 2:
            return []
        changes = []
        for i in range(1, len(evo)):
            prev = np.mean(evo[i-1])
            curr = np.mean(evo[i])
            if abs(curr - prev) / (abs(prev) + 1e-12) > threshold:
                changes.append(i)
        return changes

    def forecast_eigenvalues(self, matrix_type: SpectralType = SpectralType.LAPLACIAN, steps: int = 1, method: str = 'linear'):
        """
        Forecast future eigenvalues based on historical evolution.
        method: 'linear' (linear extrapolation per eigenvalue) or 'arima' (if statsmodels available)
        """
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
                if len(series) >= 2:
                    x = np.arange(len(series))
                    z = np.polyfit(x, series, 1)
                    p = np.poly1d(z)
                    forecast = p(len(series) + steps - 1)
                else:
                    forecast = series[-1]
            elif method == 'arima' and HAS_ARIMA:
                try:
                    model = ARIMA(series, order=(1,0,0))
                    model_fit = model.fit()
                    forecast = model_fit.forecast(steps=steps)[-1]
                except:
                    forecast = series[-1]
            else:
                forecast = series[-1]
            forecasts.append(forecast)
        return np.array(forecasts)

    # ------------------------------------------------------------------------
    # Multiparameter persistence of eigenvalue series
    # ------------------------------------------------------------------------
    def compute_multiparameter_persistence(self, matrix_type: SpectralType = SpectralType.LAPLACIAN,
                                           second_parameter_func: Optional[Callable[[int], float]] = None,
                                           max_dim: int = 1):
        """
        Compute multiparameter persistence of the eigenvalue series.
        The first parameter is time (index). The second parameter can be a function that
        assigns a second filter value to each time point (e.g., a scale parameter, variance, etc.).
        Requires `multipers` library; otherwise a NotImplementedError is raised.

        Returns:
            Dictionary with persistence diagrams per dimension (in 2D) or None.
        """
        if not HAS_MULTIPERS:
            raise NotImplementedError("Multiparameter persistence requires the 'multipers' library. Install with: pip install multipers")

        if matrix_type not in self.eigenvalue_evolution:
            self.compute_eigenvalue_evolution(matrix_type)
        evo = self.eigenvalue_evolution[matrix_type]
        if len(evo) == 0:
            return None

        n_times = len(evo)
        # Build a point cloud: for each time we have (t, s)
        points = []
        for t_idx in range(n_times):
            t_val = self.timestamps[t_idx] if self.timestamps else t_idx
            if second_parameter_func is not None:
                s_val = second_parameter_func(t_idx)
            else:
                s_val = np.mean(evo[t_idx])
            points.append([t_val, s_val])

        # Use multipers to build a bifiltration and compute persistence
        try:
            # Create a Bifiltration object from the point cloud using a 2D Rips complex
            bif = Bifiltration(points=points)
            # Compute 2D persistence
            dgms = bif.compute_persistence(max_dim=max_dim)
            self._multiparameter_persistence = dgms
            return dgms
        except Exception as e:
            logger.warning(f"Multiparameter persistence computation failed: {e}")
            self._multiparameter_persistence = None
            return None

    def plot_multiparameter_persistence(self, filename: Optional[str] = None):
        """
        Visualise the multiparameter persistence diagrams (if computed).
        For 2D persistence, this plots the birth and death points as a scatter plot.
        """
        if self._multiparameter_persistence is None:
            logger.warning("No multiparameter persistence data available.")
            return
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Matplotlib not available – cannot plot.")
            return

        # The persistence diagrams from multipers are dictionaries with dimension keys,
        # each containing a list of (birth, death) pairs, where birth and death are 2D points.
        # We'll extract birth and death coordinates.
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')
        for dim, bars in self._multiparameter_persistence.items():
            births_x = [b[0] for b, _ in bars]
            births_y = [b[1] for b, _ in bars]
            deaths_x = [d[0] for _, d in bars]
            deaths_y = [d[1] for _, d in bars]
            # Plot as scatter points: each bar is a point in 4D? We'll plot birth and death in 2D with dimension as z.
            # For simplicity, plot birth points (blue) and death points (red) with offset in z.
            ax.scatter(births_x, births_y, [dim]*len(births_x), c='blue', label=f'H{dim} birth')
            ax.scatter(deaths_x, deaths_y, [dim]*len(deaths_x), c='red', label=f'H{dim} death')
        ax.set_xlabel('Parameter 1 (time)')
        ax.set_ylabel('Parameter 2 (scale)')
        ax.set_zlabel('Dimension')
        plt.legend()
        plt.title('Multiparameter persistence diagram')
        if filename:
            plt.savefig(filename)
        else:
            plt.show()
        plt.close()

    # ------------------------------------------------------------------------
    # Granger causality between eigenvalue series
    # ------------------------------------------------------------------------
    def granger_causality(self, idx_i: int, idx_j: int, matrix_type: SpectralType = SpectralType.LAPLACIAN,
                          max_lag: int = 5) -> Dict[str, float]:
        """
        Test if eigenvalue i Granger‑causes eigenvalue j.
        Uses the time series of eigenvalues.
        Returns dict with 'f_stat' and 'p_value'.
        """
        if matrix_type not in self.eigenvalue_evolution:
            self.compute_eigenvalue_evolution(matrix_type)
        evo = self.eigenvalue_evolution[matrix_type]
        if len(evo) < 2:
            return {'f_stat': 0.0, 'p_value': 1.0}
        series_i = np.array([e[idx_i] for e in evo if idx_i < len(e)])
        series_j = np.array([e[idx_j] for e in evo if idx_j < len(e)])
        if len(series_i) != len(series_j) or len(series_i) < max_lag+1:
            return {'f_stat': 0.0, 'p_value': 1.0}
        if not HAS_STATSMODELS:
            return {'f_stat': 0.0, 'p_value': 1.0}
        data = np.column_stack([series_j, series_i])
        result = grangercausalitytests(data, max_lag, verbose=False)
        best_p = 1.0
        best_f = 0.0
        for lag in result:
            p = result[lag][0]['ssr_ftest'][1]
            if p < best_p:
                best_p = p
                best_f = result[lag][0]['ssr_ftest'][0]
        return {'f_stat': best_f, 'p_value': best_p}

    # Alias for backward compatibility
    granger_causality_between_eigenvalues = granger_causality


# ----------------------------------------------------------------------------
# Database integration (SQLite, Neo4j)
# ----------------------------------------------------------------------------
class SpectralDatabase:
    """
    Store and load spectra in databases.
    Supports SQLite and Neo4j.
    """
    def __init__(self, db_type: str = 'sqlite', connection_string: str = 'spectral.db'):
        self.db_type = db_type
        self.connection_string = connection_string
        self.conn = None
        if db_type == 'sqlite' and HAS_SQLITE:
            self.conn = sqlite3.connect(connection_string)
            self._create_sqlite_tables()
        elif db_type == 'neo4j' and HAS_NEO4J:
            self.conn = GraphDatabase.driver(connection_string)
        else:
            logger.warning(f"Database type {db_type} not available.")

    def _create_sqlite_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spectra (
                graph_id TEXT,
                timestamp REAL,
                matrix_type TEXT,
                eigenvalues BLOB,
                eigenvectors BLOB
            )
        ''')
        self.conn.commit()

    def store_spectrum(self, graph_id: str, timestamp: float, matrix_type: str,
                       eigenvalues: np.ndarray, eigenvectors: np.ndarray):
        if self.db_type == 'sqlite' and self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO spectra (graph_id, timestamp, matrix_type, eigenvalues, eigenvectors)
                VALUES (?, ?, ?, ?, ?)
            ''', (graph_id, timestamp, matrix_type, pickle.dumps(eigenvalues), pickle.dumps(eigenvectors)))
            self.conn.commit()
        elif self.db_type == 'neo4j' and self.conn:
            with self.conn.session() as session:
                session.run(
                    "CREATE (s:Spectrum {graph_id: $graph_id, timestamp: $timestamp, matrix_type: $matrix_type}) "
                    "SET s.eigenvalues = $eigenvalues, s.eigenvectors = $eigenvectors",
                    graph_id=graph_id, timestamp=timestamp, matrix_type=matrix_type,
                    eigenvalues=eigenvalues.tolist(), eigenvectors=eigenvectors.tolist()
                )

    def load_spectra(self, graph_id: str, matrix_type: str) -> List[Tuple[float, np.ndarray, np.ndarray]]:
        if self.db_type == 'sqlite' and self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT timestamp, eigenvalues, eigenvectors FROM spectra
                WHERE graph_id = ? AND matrix_type = ?
                ORDER BY timestamp
            ''', (graph_id, matrix_type))
            rows = cursor.fetchall()
            result = []
            for ts, evals_blob, evecs_blob in rows:
                evals = pickle.loads(evals_blob)
                evecs = pickle.loads(evecs_blob)
                result.append((ts, evals, evecs))
            return result
        elif self.db_type == 'neo4j' and self.conn:
            with self.conn.session() as session:
                result = session.run(
                    "MATCH (s:Spectrum {graph_id: $graph_id, matrix_type: $matrix_type}) "
                    "RETURN s.timestamp AS timestamp, s.eigenvalues AS eigenvalues, s.eigenvectors AS eigenvectors "
                    "ORDER BY timestamp",
                    graph_id=graph_id, matrix_type=matrix_type
                )
                data = []
                for record in result:
                    ts = record['timestamp']
                    evals = np.array(record['eigenvalues'])
                    evecs = np.array(record['eigenvectors'])
                    data.append((ts, evals, evecs))
                return data
        return []

    def close(self):
        if self.db_type == 'sqlite' and self.conn:
            self.conn.close()
        elif self.db_type == 'neo4j' and self.conn:
            self.conn.close()


# ----------------------------------------------------------------------------
# Interactive dashboard with Dash
# ----------------------------------------------------------------------------
def create_spectral_dashboard(dsa: DynamicSpectralAnalysis, matrix_type: SpectralType = SpectralType.LAPLACIAN):
    """
    Create a Plotly Dash dashboard for real‑time visualisation of spectra.
    Requires that dsa already has data.
    """
    if not HAS_DASH:
        logger.warning("Dash not available – cannot create dashboard.")
        return None

    if matrix_type not in dsa.eigenvalue_evolution:
        dsa.compute_eigenvalue_evolution(matrix_type)

    evo = dsa.eigenvalue_evolution[matrix_type]
    timestamps = dsa.timestamps if dsa.timestamps else list(range(len(evo)))

    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.H1("Spectral Evolution Dashboard"),
        dcc.Graph(id='spectral-evolution'),
        dcc.Interval(id='interval', interval=1000)  # update every second (placeholder)
    ])

    @app.callback(
        Output('spectral-evolution', 'figure'),
        [Input('interval', 'n_intervals')]
    )
    def update_graph(n):
        fig = go.Figure()
        n_vals = len(evo[0]) if evo else 0
        for i in range(n_vals):
            values = [e[i] for e in evo]
            fig.add_trace(go.Scatter(x=timestamps, y=values, mode='lines+markers', name=f'λ_{i}'))
        fig.update_layout(title=f'Spectral evolution ({matrix_type.value})',
                          xaxis_title='Time',
                          yaxis_title='Eigenvalue')
        return fig

    return app


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================
def spectral_analysis_from_networkx(graph: nx.Graph, **kwargs) -> SpectralGraphAnalysis:
    """Create a SpectralGraphAnalysis object from a NetworkX graph."""
    return SpectralGraphAnalysis(graph, **kwargs)

def spectral_analysis_from_igraph(graph: ig.Graph, **kwargs) -> SpectralGraphAnalysis:
    """Create a SpectralGraphAnalysis object from an igraph graph."""
    return SpectralGraphAnalysis(graph, **kwargs)

def spectral_analysis_from_graphtool(graph: gt.Graph, **kwargs) -> SpectralGraphAnalysis:
    """Create a SpectralGraphAnalysis object from a graph-tool graph."""
    return SpectralGraphAnalysis(graph, **kwargs)

def spectral_analysis_from_adjacency(adj: np.ndarray, directed: bool = False, weighted: bool = False) -> SpectralGraphAnalysis:
    """Create from adjacency matrix."""
    return SpectralGraphAnalysis(adj, directed=directed, weighted=weighted, graph_id="matrix")


# ============================================================================
# DEMONSTRATION
# ============================================================================
if __name__ == "__main__":
    # Create a small test graph
    if HAS_NETWORKX:
        G = nx.karate_club_graph()
        sa = spectral_analysis_from_networkx(G)
        print("Algebraic connectivity:", sa.algebraic_connectivity())
        print("Spectral gap:", sa.spectral_gap())
        print("Spectral radius:", sa.spectral_radius())
        print("Estrada index:", sa.estrada_index())
        print("Number of spanning trees:", sa.number_of_spanning_trees())
        print("Effective resistance (0,1):", sa.effective_resistance(0,1))
        print("Von Neumann entropy:", sa.von_neumann_entropy())
        print("Graph energy:", sa.graph_energy())
        print("Kirchhoff index:", sa.kirchhoff_index())
        print("Spectral complexity:", sa.spectral_complexity())
        print("Spectral skewness:", sa.spectral_skewness())
        print("Spectral kurtosis:", sa.spectral_kurtosis())
        print("Spectral distribution entropy:", sa.spectral_distribution_entropy())
        embed = sa.spectral_embedding(dim=2)
        print("Embedding shape:", embed.shape)
        clusters = sa.spectral_clustering(n_clusters=3)
        print("Clusters (first 10):", clusters[:10])
        sa.plot_spectrum()
        sa.plot_embedding(labels=clusters, filename="karate_embedding.png")
        # Test new methods
        signal = np.random.randn(G.number_of_nodes())
        filtered = sa.chebyshev_filter(signal, cutoff=0.2, order=5)
        print("Chebyshev filter output norm:", np.linalg.norm(filtered))
        print("Heat kernel trace at t=1:", sa.heat_kernel_trace(1.0))
        print("Spectral modularity gap:", sa.spectral_modularity_gap())
        # Create another graph for alignment
        G2 = nx.erdos_renyi_graph(G.number_of_nodes(), 0.1)
        sa2 = spectral_analysis_from_networkx(G2)
        align = sa.spectral_alignment(sa2, dim=5)
        print("Spectral alignment score:", align)
        # Test multiview clustering (voorbeeld met twee views)
        if HAS_SCIPY:
            labels_mv = multiview_spectral_clustering([G, G2], n_clusters=3, fusion='average')
            print("Multiview clustering labels (first 10):", labels_mv[:10])
        # Test dynamische analyse
        dsa = DynamicSpectralAnalysis()
        dsa.add_graph(G, timestamp=0)
        dsa.add_graph(G2, timestamp=1)
        evo = dsa.compute_eigenvalue_evolution(k=5)
        print("Eigenvalue evolution:", [e[:3] for e in evo])
        changes = dsa.detect_change_points()
        print("Change points:", changes)
        forecast = dsa.forecast_eigenvalues(steps=2)
        print("Forecast:", forecast)
        # Test Granger causality (als statsmodels beschikbaar)
        if HAS_STATSMODELS and len(evo) >= 2 and len(evo[0]) >= 2:
            gc = dsa.granger_causality(0, 1)
            print("Granger causality (λ0 → λ1):", gc)
        # Test database
        db = SpectralDatabase()
        db.store_spectrum("karate", 0, "laplacian", evo[0], None)
        db.close()
        # Test dashboard (alleen als Dash beschikbaar)
        if HAS_DASH:
            app = create_spectral_dashboard(dsa)
            # In een echte run zou je app.run_server() doen, maar in demo niet
            print("Dashboard aangemaakt (niet gestart).")
        # Plotly spectrum if available
        sa.plot_spectrum_plotly()

        # Test new Layer 1 integration
        print("\n--- Layer 1 integration demo ---")
        class DummyObs:
            def __init__(self, oid, dims, emb, atomicity):
                self.id = oid
                self.qualitative_dims = dims
                self.relational_embedding = emb
                self.atomicity_score = atomicity
        registry = {
            'A': DummyObs('A', {'x': 0.1, 'y': 0.2}, [0.5, 0.6], 0.8),
            'B': DummyObs('B', {'x': 0.15, 'y': 0.25}, [0.55, 0.65], 0.7),
            'C': DummyObs('C', {'x': 0.9, 'y': 0.8}, [0.9, 0.95], 0.3),
        }
        sa_layer1 = SpectralGraphAnalysis.from_layer1_registry(registry, similarity_threshold=0.5, weight_by_atomicity=True)
        print("Built graph from registry with nodes:", list(sa_layer1.graph.nodes()))
        L_atomic = sa_layer1.compute_atomicity_laplacian()
        print("Atomicity-weighted Laplacian shape:", L_atomic.shape)
        # Test snapshot from phase
        dsa_layer1 = DynamicSpectralAnalysis()
        snap = dsa_layer1.snapshot_from_phase(registry, phase=0.0, similarity_threshold=0.5)
        if snap:
            print("Snapshot graph has", snap.graph.number_of_nodes(), "nodes")
        else:
            print("No snapshot for phase 0.0")
    else:
        # Use a random matrix
        adj = np.random.rand(10,10)
        adj = (adj + adj.T)/2
        np.fill_diagonal(adj, 0)
        sa = spectral_analysis_from_adjacency(adj)
        print("Spectral radius:", sa.spectral_radius())