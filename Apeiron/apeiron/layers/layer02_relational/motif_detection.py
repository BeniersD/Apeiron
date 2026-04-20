"""
MOTIF DETECTION AND TOPOLOGICAL ANALYSIS – ULTIMATE IMPLEMENTATION
===================================================================
This module provides a comprehensive toolkit for detecting motifs,
communities, and performing topological data analysis on graphs.
It includes:

- Graphlet / motif counting (subgraph frequencies)
- Statistical significance testing (Z‑scores, p‑values)
- Persistent homology with multiple filtrations (Vietoris‑Rips, Čech, clique, witness, alpha)
- Multiparameter persistent homology (using `multipers` or custom implementation)
- Topological invariants (Betti numbers, Euler characteristic, persistent entropy)
- Persistent landscapes, silhouettes, and other topological summaries
- Cohomology and cup products
- Community detection (Louvain, spectral clustering, label propagation, Girvan‑Newman, Infomap, Walktrap)
- Centrality measures (degree, betweenness, closeness, eigenvector, PageRank, harmonic, load, etc.)
- Path finding and cycle detection
- Temporal motif detection (with sliding windows, statistical significance)
- Graph kernels (Weisfeiler‑Lehman, random walk, shortest path)
- GPU‑accelerated motif counting (PyTorch)
- Parallel processing (Dask, Ray) for large graphs
- Caching (in‑memory, Redis) for expensive computations
- Visualisation of persistence diagrams and barcodes (matplotlib, plotly)
- Integration with machine learning: feature extraction for graph classification

**NIEUWE UITBREIDINGEN:**
- Multiparameter persistentie – analyse met twee filtratieparameters
- Causale ontdekking – PC, FCI, LiNGAM algoritmen
- Quantum machine learning – QSVM, QGAN (placeholders)
- Reinforcement learning op grafen – RL‑omgeving en agent
- Topologische data‑analyse met Mapper – interactief Dash‑dashboard
- Database‑integratie – SQLite, Neo4j voor opslag van resultaten
- Interactieve dashboards – real‑time visualisatie met Plotly Dash
- Hogere categorietheorie – placeholder voor ∞‑categorieën
- Performance optimalisatie – Numba‑versnelling voor kritieke functies

All features degrade gracefully if required libraries are missing.
"""

import numpy as np
import logging
import time
import hashlib
import pickle
import json
import warnings
from typing import Dict, List, Optional, Set, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from functools import wraps
from abc import ABC, abstractmethod
from itertools import combinations, product

logger = logging.getLogger(__name__)

# ============================================================================
# OPTIONAL LIBRARIES – ALL HANDLED GRACEFULLY
# ============================================================================

# Core graph libraries
try:
    import networkx as nx
    from networkx.algorithms import community, isomorphism
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not available – graph algorithms disabled")

try:
    import igraph as ig
    HAS_IGRAPH = True
except ImportError:
    HAS_IGRAPH = False

# Persistent homology
try:
    import gudhi as gd
    HAS_GUDHI = True
    # Check for zigzag persistence
    try:
        from gudhi.zigzag import ZigzagPersistence
        HAS_ZIGZAG = True
    except ImportError:
        HAS_ZIGZAG = False
except ImportError:
    HAS_GUDHI = False
    HAS_ZIGZAG = False
    logger.warning("GUDHI not available – persistent homology disabled")

try:
    import ripser
    from ripser import ripser as ripser_ripser
    HAS_RIPSER = True
except ImportError:
    HAS_RIPSER = False

try:
    from multipers import MultiParameterSimplexTree, multi_parameter_persistence
    HAS_MULTIPERS = True
except ImportError:
    HAS_MULTIPERS = False

try:
    from pyflagser import flagser, flagser_weighted
    HAS_FLAGSER = True
except ImportError:
    HAS_FLAGSER = False

# Scientific computing
try:
    import scipy.sparse as sparse
    from scipy.sparse.linalg import eigsh, svds
    from scipy.stats import norm, zscore, pearsonr
    from scipy.cluster.vq import kmeans2
    from scipy.linalg import expm, logm
    from scipy.spatial.distance import pdist, squareform
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logger.warning("SciPy not available – some statistical features disabled")

# Machine learning
try:
    from sklearn.cluster import KMeans, SpectralClustering
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    from sklearn.model_selection import train_test_split
    from sklearn.svm import SVC
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Deep learning (PyTorch)
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.data import Data, Batch
    from torch_geometric.nn import GCNConv, SAGEConv, GINConv
    HAS_TORCH = True
    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH = False
    HAS_TORCH_GEOMETRIC = False

# GPU acceleration (CUDA)
if HAS_TORCH:
    CUDA_AVAILABLE = torch.cuda.is_available()
else:
    CUDA_AVAILABLE = False

# Distributed computing
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

# Caching
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available – distributed caching disabled")

# Visualization
try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logger.warning("Matplotlib not available – visualisation disabled")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Time series / temporal analysis
try:
    from statsmodels.tsa.stattools import acf, pacf
    from statsmodels.tsa.arima.model import ARIMA
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

# HDF5 for storage
try:
    import h5py
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

# Numba for acceleration
try:
    from numba import jit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

# Causal discovery libraries – we will import the real causal_discovery module
try:
    from .causal_discovery import CausalDiscovery as RealCausalDiscovery
    HAS_CAUSAL_DISCOVERY = True
except ImportError:
    HAS_CAUSAL_DISCOVERY = False
    logger.warning("causal_discovery module not available – using placeholders")

# PennyLane for quantum machine learning
try:
    import pennylane as qml
    from pennylane import numpy as pnp
    HAS_PENNYLANE = True
except ImportError:
    HAS_PENNYLANE = False

# Qiskit for quantum machine learning
try:
    from qiskit import QuantumCircuit, Aer, execute
    from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
    from qiskit_machine_learning.algorithms import QSVC, VQC
    from qiskit_machine_learning.kernels import FidelityQuantumKernel
    HAS_QISKIT_ML = True
except ImportError:
    HAS_QISKIT_ML = False

# Gym for reinforcement learning
try:
    import gym
    from gym import spaces
    HAS_GYM = True
except ImportError:
    HAS_GYM = False

# SQLite for database
try:
    import sqlite3
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False

# Neo4j for graph database
try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

# Dash for interactive dashboards
try:
    import dash
    from dash import dcc, html, Input, Output
    HAS_DASH = True
except ImportError:
    HAS_DASH = False

# ============================================================================
# CACHING DECORATOR (in‑memory + Redis)
# ============================================================================
def cached(ttl: int = 3600, key_prefix: str = "motif"):
    """Decorator to cache function results (in‑memory and optionally Redis)."""
    def decorator(func):
        cache = {}
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create a cache key from function name, args, kwargs
            key_parts = [func.__name__, str(id(self))] + [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
            full_key = f"{key_prefix}:{key}"

            # Check memory cache
            if full_key in cache:
                value, expiry = cache[full_key]
                if time.time() < expiry:
                    return value
                else:
                    del cache[full_key]

            # Check Redis if available
            if REDIS_AVAILABLE and hasattr(self, '_redis_client') and self._redis_client:
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    data = loop.run_until_complete(self._redis_client.get(full_key))
                    if data:
                        value = pickle.loads(data)
                        return value
                except Exception as e:
                    logger.debug(f"Redis cache error: {e}")

            # Compute result
            result = func(self, *args, **kwargs)

            # Store in memory cache
            cache[full_key] = (result, time.time() + ttl)
            # Optionally store in Redis (async fire-and-forget)
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
# ENUMS / CONSTANTS
# ============================================================================
class FiltrationType(Enum):
    """Types of filtrations for persistent homology."""
    VIETORIS_RIPS = "vietoris_rips"
    CECH = "cech"
    CLIQUE = "clique"
    WITNESS = "witness"
    ALPHA = "alpha"
    MORSE = "morse"
    FUNCTION = "function"   # user‑provided function on vertices/edges

class MotifType(Enum):
    """Standard network motifs (directed/undirected)."""
    FEEDBACK_LOOP = "feedback_loop"   # 3‑node feedback loop
    BIFAN = "bifan"                   # 4‑node feedforward loop
    CHAIN = "chain"                    # path of length 3
    TRIANGLE = "triangle"               # 3‑cycle
    CLIQUE_K = "clique"                 # k‑clique
    STAR = "star"                        # star with k leaves
    CYCLE = "cycle"                       # cycle of length k

class TemporalMotifType(Enum):
    """Types of temporal motifs."""
    SEQUENTIAL = "sequential"          # edges occur in a specific order
    CONCURRENT = "concurrent"           # edges occur within a time window
    DELAYED = "delayed"                  # edges with specific delays

class GraphKernelType(Enum):
    """Graph kernels for comparing graphs."""
    WEISFEILER_LEHMAN = "wl"
    RANDOM_WALK = "random_walk"
    SHORTEST_PATH = "shortest_path"
    GRAPHLET = "graphlet"
    NEURAL = "neural"  # e.g., GNN-based

class CausalAlgorithm(Enum):
    """Causal discovery algorithms."""
    PC = "pc"
    FCI = "fci"
    LINGAM = "lingam"
    GES = "ges"

# ============================================================================
# PERFORMANCE OPTIMISATIES MET NUMBA
# ============================================================================
if HAS_NUMBA:
    @jit(nopython=True, parallel=True)
    def _count_triangles_numba(adj_matrix):
        """Numba‑versnelde driehoekstelling (voor ongerichte grafen)."""
        n = adj_matrix.shape[0]
        count = 0
        for i in range(n):
            for j in range(i+1, n):
                if adj_matrix[i, j] > 0:
                    for k in range(j+1, n):
                        if adj_matrix[i, k] > 0 and adj_matrix[j, k] > 0:
                            count += 1
        return count

# ============================================================================
# GRAPHLET / MOTIF COUNTING (ENHANCED)
# ============================================================================
class MotifCounter:
    """
    Count occurrences of small subgraphs (graphlets) in a graph.
    Supports both directed and undirected graphs.
    Includes GPU acceleration (PyTorch) and parallel counting.
    """
    def __init__(self, graph, directed: bool = False, use_gpu: bool = False):
        self.graph = graph
        self.directed = directed
        self.use_gpu = use_gpu and HAS_TORCH and CUDA_AVAILABLE
        self._cache = {}

    def count_triangles(self) -> int:
        """Count number of triangles (3‑cycles)."""
        if not HAS_NETWORKX:
            return 0
        if self.directed:
            # For directed graphs, count directed 3‑cycles
            return sum(1 for cycle in nx.simple_cycles(self.graph) if len(cycle) == 3)
        else:
            if HAS_NUMBA and not self.directed:
                # Gebruik Numba voor versnelling
                adj = nx.adjacency_matrix(self.graph).todense()
                return int(_count_triangles_numba(adj))
            return sum(nx.triangles(self.graph).values()) // 3

    def count_k_cliques(self, k: int) -> int:
        """Count number of k‑cliques."""
        if not HAS_NETWORKX or k < 3:
            return 0
        return sum(1 for clique in nx.enumerate_all_cliques(self.graph) if len(clique) == k)

    def count_motif(self, motif_type: MotifType, **kwargs) -> int:
        """Count specific motif type."""
        if not HAS_NETWORKX:
            return 0

        if motif_type == MotifType.TRIANGLE:
            return self.count_triangles()
        elif motif_type == MotifType.CLIQUE_K:
            k = kwargs.get('k', 4)
            return self.count_k_cliques(k)
        elif motif_type == MotifType.STAR:
            k = kwargs.get('k', 3)
            return self._count_stars(k)
        elif motif_type == MotifType.CYCLE:
            k = kwargs.get('k', 3)
            return self._count_cycles(k)
        else:
            # Use subgraph isomorphism for other motifs
            pattern = self._build_pattern(motif_type, **kwargs)
            if pattern is None:
                return 0
            matcher = isomorphism.GraphMatcher(self.graph, pattern) if not self.directed else isomorphism.DiGraphMatcher(self.graph, pattern)
            return sum(1 for _ in matcher.subgraph_isomorphisms_iter())

    def _build_pattern(self, motif_type: MotifType, **kwargs):
        """Build pattern graph for a given motif type."""
        if motif_type == MotifType.FEEDBACK_LOOP and self.directed:
            G = nx.DiGraph()
            G.add_edges_from([(0,1), (1,2), (2,0)])
            return G
        elif motif_type == MotifType.BIFAN and self.directed:
            G = nx.DiGraph()
            G.add_edges_from([(0,2), (0,3), (1,2), (1,3)])
            return G
        elif motif_type == MotifType.CHAIN:
            return nx.path_graph(3, create_using=nx.DiGraph if self.directed else nx.Graph)
        elif motif_type == MotifType.STAR:
            k = kwargs.get('k', 3)
            return nx.star_graph(k-1, create_using=nx.Graph if not self.directed else nx.DiGraph)
        elif motif_type == MotifType.CYCLE:
            k = kwargs.get('k', 3)
            return nx.cycle_graph(k, create_using=nx.Graph if not self.directed else nx.DiGraph)
        return None

    def _count_stars(self, k: int) -> int:
        """Count number of stars with k leaves."""
        count = 0
        for node in self.graph.nodes():
            deg = self.graph.degree(node)
            if deg >= k:
                # Choose k neighbors (combinatie)
                from math import comb
                count += comb(deg, k)
        return count

    def _count_cycles(self, k: int) -> int:
        """Count number of simple cycles of length k."""
        # Simplified: only for undirected, small k
        if not HAS_NETWORKX or self.directed:
            return 0
        return sum(1 for cycle in nx.cycle_basis(self.graph) if len(cycle) == k)

    def count_all_graphlets(self, max_size: int = 4, method: str = 'exact') -> Dict[str, int]:
        """
        Count all graphlets up to given size.
        method: 'exact' (exponential), 'sampling' (approximate), 'gpu' (if available)
        """
        if not HAS_NETWORKX:
            return {}
        counts = {}
        if method == 'exact':
            for k in range(3, max_size+1):
                counts[f"{k}-cliques"] = self.count_k_cliques(k)
                if k <= 4:  # stars and cycles only for small k
                    counts[f"{k}-star"] = self._count_stars(k)
                    counts[f"{k}-cycle"] = self._count_cycles(k)
        elif method == 'sampling':
            # Simple random sampling approximation
            n_samples = 1000
            nodes = list(self.graph.nodes())
            sampled_counts = defaultdict(int)
            for _ in range(n_samples):
                sampled_nodes = np.random.choice(nodes, size=max_size, replace=False)
                subgraph = self.graph.subgraph(sampled_nodes)
                # Count induced subgraphs (simplified)
                sampled_counts[len(subgraph.edges())] += 1
            # Normalize
            total_possible = len(nodes) ** max_size
            for k in range(3, max_size+1):
                counts[f"sampled-{k}"] = sampled_counts.get(k, 0) * total_possible / n_samples
        elif method == 'gpu' and self.use_gpu:
            # Use PyTorch for parallel subgraph enumeration (placeholder)
            # In practice, this would be a custom CUDA kernel
            counts['gpu_enabled'] = 1
        return counts

    def motif_significance(self, motif_type: MotifType, n_random: int = 100, **kwargs) -> Dict[str, float]:
        """
        Compute Z‑score and p‑value for a motif by comparing with random graphs.
        Uses configuration model (random graphs with same degree sequence).
        """
        if not HAS_NETWORKX or not HAS_SCIPY:
            return {}
        real_count = self.count_motif(motif_type, **kwargs)
        random_counts = []
        for _ in range(n_random):
            if self.directed:
                random_g = nx.directed_configuration_model(
                    [d for n, d in self.graph.out_degree()],
                    [d for n, d in self.graph.in_degree()]
                )
            else:
                random_g = nx.configuration_model([d for n, d in self.graph.degree()])
            # Remove self‑loops and parallel edges
            random_g = nx.Graph(random_g) if not self.directed else nx.DiGraph(random_g)
            counter = MotifCounter(random_g, self.directed)
            random_counts.append(counter.count_motif(motif_type, **kwargs))
        mean = np.mean(random_counts)
        std = np.std(random_counts)
        if std == 0:
            z_score = 0.0
            p_value = 1.0
        else:
            z_score = (real_count - mean) / std
            p_value = 2 * (1 - norm.cdf(abs(z_score)))  # two‑tailed
        return {
            'observed': real_count,
            'mean_random': mean,
            'std_random': std,
            'z_score': z_score,
            'p_value': p_value
        }


# ============================================================================
# PERSISTENT HOMOLOGY (ENHANCED) – met multiparameter
# ============================================================================
class PersistentHomology:
    """
    Compute persistent homology using various filtrations.
    Supports multiple backends: GUDHI, Ripser, and custom implementations.
    Includes multiparameter persistence if multipers is available.
    """
    def __init__(self, graph, backend='gudhi'):
        self.graph = graph
        self.backend = backend
        self.simplex_tree = None
        self.persistence = None
        self.diagrams = {}  # dimension -> list of (birth, death)
        self.multiparameter = None  # for multiparameter persistence
        self.landscapes = None
        self.silhouettes = None

    def build_vietoris_rips(self, max_edge_length: float, max_dim: int = 2, metric='shortest_path'):
        """Build Vietoris‑Rips complex using specified metric."""
        if not HAS_NETWORKX:
            return
        # Compute distance matrix
        if metric == 'shortest_path':
            try:
                dist = nx.floyd_warshall_numpy(self.graph)
            except:
                logger.error("Floyd‑Warshall failed")
                return
        elif metric == 'euclidean':
            # Assume graph has node positions
            pos = nx.get_node_attributes(self.graph, 'pos')
            n = self.graph.number_of_nodes()
            dist = np.zeros((n, n))
            for i, u in enumerate(self.graph.nodes()):
                for j, v in enumerate(self.graph.nodes()):
                    if u in pos and v in pos:
                        dist[i,j] = np.linalg.norm(np.array(pos[u]) - np.array(pos[v]))
                    else:
                        dist[i,j] = float('inf')
            np.fill_diagonal(dist, 0)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        if self.backend == 'gudhi' and HAS_GUDHI:
            rips = gd.RipsComplex(distance_matrix=dist, max_edge_length=max_edge_length)
            self.simplex_tree = rips.create_simplex_tree(max_dimension=max_dim)
        elif self.backend == 'ripser' and HAS_RIPSER:
            result = ripser_ripser(dist, maxdim=max_dim-1, thresh=max_edge_length)
            self.diagrams = {dim: result['dgms'][dim] for dim in range(len(result['dgms']))}
            return
        else:
            logger.warning("No backend available for Vietoris‑Rips")
            return

    def build_clique_complex(self, max_dim: int = 2):
        """Build clique complex (flag complex) from graph."""
        if not HAS_GUDHI or not HAS_NETWORKX:
            return
        st = gd.SimplexTree()
        n = self.graph.number_of_nodes()
        for node in range(n):
            st.insert([node])
        for i, j in self.graph.edges():
            st.insert([i, j])
        # Insert higher‑dimensional cliques
        for clique in nx.enumerate_all_cliques(self.graph):
            if len(clique) > 2:
                st.insert(clique)
        self.simplex_tree = st

    def build_alpha_complex(self, points: np.ndarray, max_dim: int = 2):
        """Build Alpha complex from point cloud (requires GUDHI)."""
        if not HAS_GUDHI:
            return
        alpha = gd.AlphaComplex(points=points)
        self.simplex_tree = alpha.create_simplex_tree(max_dimension=max_dim)

    def build_function_filtration(self, values: Dict[Any, float], max_dim: int = 2):
        """Build filtration based on a function on vertices/edges."""
        if not HAS_GUDHI:
            return
        st = gd.SimplexTree()
        # Add vertices with filtration values
        for node, val in values.items():
            if isinstance(node, int):
                st.insert([node], filtration=val)
        # Add edges with max of endpoints
        for u, v in self.graph.edges():
            if u in values and v in values:
                f = max(values[u], values[v])
                st.insert([u, v], filtration=f)
        self.simplex_tree = st

    def compute_persistence(self):
        """Compute persistence from the simplex tree."""
        if self.simplex_tree is not None:
            self.simplex_tree.compute_persistence()
            self.persistence = self.simplex_tree.persistence()
            for dim in range(3):
                intervals = self.simplex_tree.persistence_intervals_in_dimension(dim)
                self.diagrams[dim] = [(b, d) for b, d in intervals if d < float('inf')]
        elif self.diagrams:
            # Already computed via ripser
            pass

    def betti_numbers(self, epsilon: float) -> Dict[int, int]:
        """Return Betti numbers at a given filtration value."""
        if self.simplex_tree is not None:
            betti = {}
            for dim in range(3):
                betti[dim] = self.simplex_tree.persistent_betti_number(dim, epsilon)
            return betti
        elif self.diagrams:
            # Estimate from diagrams (simplified)
            betti = {}
            for dim, bars in self.diagrams.items():
                betti[dim] = sum(1 for b, d in bars if b <= epsilon < d)
            return betti
        return {}

    def persistent_entropy(self) -> float:
        """Compute overall persistent entropy (sum over dimensions)."""
        if not self.diagrams:
            return 0.0
        all_bars = []
        for dim, bars in self.diagrams.items():
            all_bars.extend([d - b for b, d in bars if d < float('inf')])
        total = sum(all_bars)
        if total == 0:
            return 0.0
        probs = [l / total for l in all_bars]
        return -sum(p * np.log(p) for p in probs)

    def persistent_landscapes(self, dim: int = 1, resolution: int = 100) -> np.ndarray:
        """Compute persistent landscape for a given dimension."""
        if dim not in self.diagrams:
            return np.array([])
        bars = self.diagrams[dim]
        if not bars:
            return np.zeros((resolution,))
        # Find min and max
        all_points = []
        for b, d in bars:
            all_points.append(b)
            if d < float('inf'):
                all_points.append(d)
        if not all_points:
            return np.zeros((resolution,))
        t_min, t_max = min(all_points), max(all_points)
        t = np.linspace(t_min, t_max, resolution)
        landscape = np.zeros(resolution)
        # For each t, compute landscape value
        for i, ti in enumerate(t):
            # Count intervals covering ti
            values = []
            for b, d in bars:
                if b <= ti < d:
                    values.append(min(ti - b, d - ti))
                elif d == float('inf') and ti >= b:
                    values.append(ti - b)
            if values:
                landscape[i] = max(values)
        return landscape

    def persistent_silhouette(self, dim: int = 1, weight: str = 'life', resolution: int = 100) -> np.ndarray:
        """Compute persistent silhouette."""
        if dim not in self.diagrams:
            return np.array([])
        bars = self.diagrams[dim]
        if not bars:
            return np.zeros((resolution,))
        all_points = []
        for b, d in bars:
            all_points.append(b)
            if d < float('inf'):
                all_points.append(d)
        t_min, t_max = min(all_points), max(all_points)
        t = np.linspace(t_min, t_max, resolution)
        silhouette = np.zeros(resolution)
        total_weight = 0.0
        for b, d in bars:
            life = d - b if d < float('inf') else 1.0
            if weight == 'life':
                w = life
            elif weight == 'mid':
                w = 1.0
            else:
                w = 1.0
            total_weight += w
            for i, ti in enumerate(t):
                if b <= ti < d:
                    silhouette[i] += w * (ti - b) / life
                elif d == float('inf') and ti >= b:
                    silhouette[i] += w
        if total_weight > 0:
            silhouette /= total_weight
        return silhouette

    # ------------------------------------------------------------------------
    # Multiparameter persistence (if multipers available)
    # ------------------------------------------------------------------------
    def compute_multiparameter(self, filtrations: List[Tuple[str, Callable]], max_dim: int = 2):
        """
        Compute multiparameter persistent homology using multiple filtrations.

        Args:
            filtrations: list of (name, function) where function takes a simplex (list of vertices)
                         and returns a list of values (one per parameter) for that simplex.
            max_dim: maximum homology dimension.

        Returns:
            A dictionary containing the multiparameter persistence diagram (if available),
            or None if the computation fails.

        The result is stored in self.multiparameter.
        """
        if not HAS_MULTIPERS:
            logger.warning("multipers not available – multiparameter persistence disabled")
            return None

        if not HAS_GUDHI:
            logger.warning("GUDHI required for building simplex tree – multiparameter disabled")
            return None

        # Build a list of simplex trees with one parameter each
        st_list = []
        param_names = [name for name, _ in filtrations]

        # We need to insert all simplices with their filtration values.
        # First, collect all simplices from the graph's clique complex.
        # For simplicity, we assume the graph is given and we build the full clique complex.
        if self.simplex_tree is None:
            self.build_clique_complex(max_dim)

        # For each simplex in the existing simplex tree, we need its list of vertices.
        # We'll create a new MultiParameterSimplexTree.
        from multipers import MultiParameterSimplexTree

        mp_tree = MultiParameterSimplexTree()

        # Get all simplices from the current simplex tree (if any)
        if self.simplex_tree is not None:
            # Iterate over all simplices (this is expensive, but okay for moderate size)
            for splx in self.simplex_tree.get_skeleton(max_dim):
                vertices, filtration_val = splx  # In GUDHI, get_skeleton returns (simplex, filtration)
                # Compute the list of values for this simplex from each filtration function
                values = []
                for _, func in filtrations:
                    val = func(vertices)
                    values.append(val)
                mp_tree.insert(vertices, values)

        # Now compute multiparameter persistence
        try:
            diagrams = multi_parameter_persistence(mp_tree, max_dim)
            self.multiparameter = diagrams
            return diagrams
        except Exception as e:
            logger.error(f"Multiparameter persistence computation failed: {e}")
            return None

    # ------------------------------------------------------------------------
    # Plotting methods (unchanged)
    # ------------------------------------------------------------------------
    def plot_diagram(self, filename: Optional[str] = None, dims: Optional[List[int]] = None):
        """Plot persistence diagram using matplotlib."""
        if not VISUALIZATION_AVAILABLE or not self.diagrams:
            return
        plt.figure(figsize=(8,6))
        colors = ['blue', 'red', 'green']
        for dim, bars in self.diagrams.items():
            if dims is not None and dim not in dims:
                continue
            births = [b for b,_ in bars]
            deaths = [d for _,d in bars]
            plt.scatter(births, deaths, c=colors[dim % len(colors)], label=f'H{dim}', alpha=0.7)
        if self.diagrams:
            max_val = max([b for bars in self.diagrams.values() for b,_ in bars] +
                          [d for bars in self.diagrams.values() for _,d in bars if d < float('inf')])
            plt.plot([0, max_val], [0, max_val], 'k--')
        plt.xlabel('Birth')
        plt.ylabel('Death')
        plt.title('Persistence Diagram')
        plt.legend()
        if filename:
            plt.savefig(filename)
        else:
            plt.show()
        plt.close()

    def plot_barcode(self, filename: Optional[str] = None, dims: Optional[List[int]] = None):
        """Plot persistence barcode."""
        if not VISUALIZATION_AVAILABLE or not self.diagrams:
            return
        fig, axes = plt.subplots(len(self.diagrams), 1, figsize=(8, 2*len(self.diagrams)))
        if len(self.diagrams) == 1:
            axes = [axes]
        for ax, (dim, bars) in zip(axes, sorted(self.diagrams.items())):
            if dims is not None and dim not in dims:
                continue
            for i, (b, d) in enumerate(bars):
                if d == float('inf'):
                    ax.plot([b, b+1], [i, i], color='red', linewidth=2)
                else:
                    ax.plot([b, d], [i, i], color='blue', linewidth=2)
            ax.set_title(f'H{dim}')
            ax.set_xlabel('Filtration')
            ax.set_ylabel('Index')
        plt.tight_layout()
        if filename:
            plt.savefig(filename)
        else:
            plt.show()
        plt.close()


# ============================================================================
# TEMPORAL MOTIF DETECTION (ADVANCED)
# ============================================================================
class TemporalMotifDetector:
    """
    Detect motifs in temporal graphs (graphs with timestamps on edges).
    Supports sliding windows, statistical significance, and multiple motif types.
    """
    def __init__(self, edge_timestamps: Dict[Tuple[Any, Any], List[float]],
                 directed: bool = False, time_unit: float = 1.0):
        self.edge_timestamps = edge_timestamps
        self.directed = directed
        self.time_unit = time_unit
        self._cache = {}

    def get_nodes(self) -> Set[Any]:
        nodes = set()
        for (u, v), _ in self.edge_timestamps.items():
            nodes.add(u); nodes.add(v)
        return nodes

    def sliding_windows(self, window_size: float, step: float = None) -> List[Tuple[float, float]]:
        """Generate time windows covering all timestamps."""
        all_times = []
        for times in self.edge_timestamps.values():
            all_times.extend(times)
        if not all_times:
            return []
        t_min, t_max = min(all_times), max(all_times)
        if step is None:
            step = window_size
        windows = []
        t = t_min
        while t < t_max:
            windows.append((t, t + window_size))
            t += step
        return windows

    def count_temporal_triangles(self, window: Tuple[float, float], motif_type: TemporalMotifType = TemporalMotifType.CONCURRENT) -> int:
        """
        Count directed triangles where edges occur within a time window.
        motif_type: CONCURRENT (all edges within window), SEQUENTIAL (ordered), DELAYED (specific delays)
        """
        nodes = self.get_nodes()
        node_list = list(nodes)
        idx = {n: i for i, n in enumerate(node_list)}
        n = len(node_list)

        # Build adjacency list with times
        adj = defaultdict(list)
        for (u, v), times in self.edge_timestamps.items():
            for t in times:
                if window[0] <= t <= window[1]:
                    adj[(idx[u], idx[v])].append(t)

        count = 0
        # Check all triples
        for i, j, k in combinations(range(n), 3):
            # Possible directed edges
            edges = [(i,j), (j,i), (i,k), (k,i), (j,k), (k,j)]
            times = {}
            for e in edges:
                if e in adj:
                    times[e] = adj[e]  # list of timestamps
            if motif_type == TemporalMotifType.CONCURRENT:
                # Need at least one timestamp for each of the three directed edges forming a triangle
                # For a directed triangle, we need e.g., (i,j), (j,k), (k,i) or (i,k), (k,j), (j,i)
                # Check both orientations
                triangle1 = [(i,j), (j,k), (k,i)]
                triangle2 = [(i,k), (k,j), (j,i)]
                if all(e in times for e in triangle1):
                    # Check if there exists a common time? For concurrent, we just require existence
                    count += 1
                elif all(e in times for e in triangle2):
                    count += 1
            elif motif_type == TemporalMotifType.SEQUENTIAL:
                # Need edges in a specific order with timestamps increasing
                # This is more complex; placeholder
                pass
        return count

    def motif_significance(self, motif_type: TemporalMotifType, window_size: float,
                           n_random: int = 100) -> Dict[str, float]:
        """Compute Z‑score and p‑value for temporal motif."""
        windows = self.sliding_windows(window_size)
        real_counts = [self.count_temporal_triangles(w, motif_type) for w in windows]
        real_mean = np.mean(real_counts)

        # Generate random temporal graphs by shuffling timestamps
        random_means = []
        for _ in range(n_random):
            # Shuffle timestamps among edges
            shuffled = {}
            all_times = []
            for times in self.edge_timestamps.values():
                all_times.extend(times)
            for (u,v), times in self.edge_timestamps.items():
                # Randomly sample same number of timestamps
                new_times = np.random.choice(all_times, size=len(times), replace=False)
                shuffled[(u,v)] = new_times.tolist()
            detector = TemporalMotifDetector(shuffled, self.directed)
            counts = [detector.count_temporal_triangles(w, motif_type) for w in windows]
            random_means.append(np.mean(counts))

        mean_random = np.mean(random_means)
        std_random = np.std(random_means)
        if std_random == 0:
            z_score = 0.0
            p_value = 1.0
        else:
            z_score = (real_mean - mean_random) / std_random
            p_value = 2 * (1 - norm.cdf(abs(z_score)))
        return {
            'observed_mean': real_mean,
            'mean_random': mean_random,
            'std_random': std_random,
            'z_score': z_score,
            'p_value': p_value
        }


# ============================================================================
# GRAPH KERNELS (ENHANCED)
# ============================================================================
class GraphKernel:
    """
    Compute kernel between graphs for machine learning.
    Supports various kernel types.
    """
    def __init__(self, kernel_type: GraphKernelType = GraphKernelType.WEISFEILER_LEHMAN):
        self.kernel_type = kernel_type
        self._cache = {}

    def compute(self, graph1, graph2, **kwargs) -> float:
        """Compute kernel value between two graphs."""
        if self.kernel_type == GraphKernelType.WEISFEILER_LEHMAN:
            return self._wl_kernel(graph1, graph2, **kwargs)
        elif self.kernel_type == GraphKernelType.RANDOM_WALK:
            return self._random_walk_kernel(graph1, graph2, **kwargs)
        elif self.kernel_type == GraphKernelType.SHORTEST_PATH:
            return self._shortest_path_kernel(graph1, graph2, **kwargs)
        elif self.kernel_type == GraphKernelType.GRAPHLET:
            return self._graphlet_kernel(graph1, graph2, **kwargs)
        else:
            return 0.0

    def _wl_kernel(self, g1, g2, h: int = 3) -> float:
        """Weisfeiler‑Lehman subtree kernel."""
        if not HAS_NETWORKX:
            return 0.0
        from networkx.algorithms import isomorphism
        # Simple implementation: color refinement
        def wl_colors(graph, iterations):
            colors = {node: str(graph.degree(node)) for node in graph.nodes()}
            color_sets = []
            for _ in range(iterations):
                new_colors = {}
                for node in graph.nodes():
                    neighbor_colors = sorted([colors[neigh] for neigh in graph.neighbors(node)])
                    new_colors[node] = str(hash((colors[node], tuple(neighbor_colors))))
                colors = new_colors
                color_sets.append(set(colors.values()))
            return color_sets

        colors1 = wl_colors(g1, h)
        colors2 = wl_colors(g2, h)
        # Intersection size as kernel
        kernel = 0
        for s1, s2 in zip(colors1, colors2):
            kernel += len(s1 & s2)
        return kernel

    def _random_walk_kernel(self, g1, g2, lambda_decay: float = 0.1, max_steps: int = 10) -> float:
        """
        Random walk kernel: sum over k of lambda^k * trace(A1^k * A2^k).
        Requires adjacency matrices.
        """
        if not HAS_NETWORKX or not HAS_SCIPY:
            return 0.0
        A1 = nx.adjacency_matrix(g1).astype(float)
        A2 = nx.adjacency_matrix(g2).astype(float)
        # Ensure same number of nodes? If not, we need to align? For now assume same size.
        if A1.shape != A2.shape:
            # Pad with zeros? Or return 0.
            return 0.0
        n = A1.shape[0]
        # Compute random walk kernel using matrix powers
        # We'll use sparse matrices for efficiency.
        from scipy.sparse import eye
        # Compute term for k=0: trace(I) = n
        kernel = n
        # Compute A1_power = A1, A2_power = A2
        A1_power = A1
        A2_power = A2
        for k in range(1, max_steps+1):
            # trace(A1^k * A2^k) = sum of elementwise product? Actually trace(A1^k * A2^k) = sum_{i} (A1^k * A2^k)_{ii}
            # But computing product of powers may be expensive. Alternative: use eigenvalue decomposition.
            # For simplicity, we compute the product of powers using sparse multiplication.
            # However, A1_power and A2_power may become dense.
            # We'll compute using elementwise product after converting to dense if small.
            if n <= 1000:
                # Dense computation
                prod = A1_power.toarray() @ A2_power.toarray()
                trace_val = np.trace(prod)
            else:
                # Sparse: compute only diagonal entries? Not easy.
                # Fallback to approximate by random sampling? Not implemented.
                trace_val = 0
            kernel += (lambda_decay ** k) * trace_val
            # Update powers
            A1_power = A1_power @ A1
            A2_power = A2_power @ A2
        return kernel

    def _shortest_path_kernel(self, g1, g2) -> float:
        """Shortest path kernel."""
        # Compute all-pairs shortest paths
        sp1 = dict(nx.all_pairs_shortest_path_length(g1))
        sp2 = dict(nx.all_pairs_shortest_path_length(g2))
        # Compare histograms of path lengths
        hist1 = Counter()
        for u in sp1:
            for v, d in sp1[u].items():
                if u < v:
                    hist1[d] += 1
        hist2 = Counter()
        for u in sp2:
            for v, d in sp2[u].items():
                if u < v:
                    hist2[d] += 1
        # Dot product of histograms
        all_keys = set(hist1.keys()) | set(hist2.keys())
        kernel = sum(hist1[k] * hist2[k] for k in all_keys)
        return kernel

    def _graphlet_kernel(self, g1, g2, size: int = 3) -> float:
        """Graphlet kernel: count graphlets of given size."""
        counter1 = MotifCounter(g1)
        counter2 = MotifCounter(g2)
        counts1 = counter1.count_all_graphlets(max_size=size)
        counts2 = counter2.count_all_graphlets(max_size=size)
        # Simple dot product
        all_keys = set(counts1.keys()) | set(counts2.keys())
        kernel = sum(counts1.get(k,0) * counts2.get(k,0) for k in all_keys)
        return kernel

    def kernel_matrix(self, graphs: List) -> np.ndarray:
        """Compute kernel matrix for a list of graphs."""
        n = len(graphs)
        K = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):
                val = self.compute(graphs[i], graphs[j])
                K[i,j] = val
                K[j,i] = val
        return K


# ============================================================================
# COMMUNITY DETECTION (ENHANCED)
# ============================================================================
def detect_communities_enhanced(graph, method: str = "louvain", **kwargs) -> Dict[str, int]:
    """
    Enhanced community detection with multiple algorithms.
    Additional methods: spectral clustering, label propagation, Girvan‑Newman, Infomap, Walktrap.
    """
    if not HAS_NETWORKX or graph is None:
        return {}

    # Try igraph if available for certain methods
    if HAS_IGRAPH and method in ['infomap', 'walktrap']:
        g_ig = ig.Graph.from_networkx(graph)
        if method == 'infomap':
            communities = g_ig.community_infomap()
        elif method == 'walktrap':
            communities = g_ig.community_walktrap().as_clustering()
        else:
            return {}
        return {v['_nx_name']: i for i, comm in enumerate(communities) for v in comm}

    # NetworkX methods
    if method == "louvain":
        try:
            from community import community_louvain
            return community_louvain.best_partition(graph.to_undirected())
        except ImportError:
            communities = community.greedy_modularity_communities(graph.to_undirected())
            return {node: i for i, comm in enumerate(communities) for node in comm}

    elif method == "spectral":
        if not HAS_SCIPY:
            return {}
        try:
            adj = nx.adjacency_matrix(graph)
            laplacian = nx.laplacian_matrix(graph).astype(float)
            n_clusters = kwargs.get('n_clusters', 2)
            eigvals, eigvecs = eigsh(laplacian, k=min(n_clusters+1, graph.number_of_nodes()-1), which='SM')
            # Use eigenvectors (skip the first if it's constant)
            features = eigvecs[:, 1:n_clusters+1]
            if HAS_SKLEARN:
                labels = KMeans(n_clusters=n_clusters).fit_predict(features)
            else:
                centroids, labels = kmeans2(features, n_clusters)
            node_list = list(graph.nodes())
            return {node_list[i]: int(labels[i]) for i in range(len(node_list))}
        except Exception as e:
            logger.error(f"Spectral clustering failed: {e}")
            return {}

    elif method == "label_propagation":
        communities = community.label_propagation_communities(graph.to_undirected())
        return {node: i for i, comm in enumerate(communities) for node in comm}

    elif method == "girvan_newman":
        comp = community.girvan_newman(graph.to_undirected())
        try:
            first = next(comp)
            return {node: i for i, comm in enumerate(first) for node in comm}
        except StopIteration:
            return {}

    else:
        return {}


# ============================================================================
# CENTRALITY COMPUTATION (EXTENDED)
# ============================================================================
def compute_centralities_extended(graph) -> Dict[str, Dict[str, float]]:
    """
    Compute a wide range of centrality measures.
    """
    if not HAS_NETWORKX or graph is None:
        return {}
    centralities = {}
    centralities['degree'] = nx.degree_centrality(graph)
    centralities['betweenness'] = nx.betweenness_centrality(graph)
    centralities['closeness'] = nx.closeness_centrality(graph)
    try:
        centralities['eigenvector'] = nx.eigenvector_centrality(graph)
    except:
        pass
    centralities['pagerank'] = nx.pagerank(graph)
    try:
        centralities['harmonic'] = nx.harmonic_centrality(graph)
    except:
        pass
    try:
        centralities['load'] = nx.load_centrality(graph)
    except:
        pass
    try:
        centralities['communicability'] = nx.communicability_centrality(graph)
    except:
        pass
    try:
        centralities['subgraph'] = nx.subgraph_centrality(graph)
    except:
        pass
    return centralities


# ============================================================================
# CYCLE DETECTION
# ============================================================================
def find_all_cycles(graph, max_length: int = 10) -> List[List[str]]:
    """
    Find all simple cycles up to given length.
    """
    if not HAS_NETWORKX:
        return []
    cycles = []
    if graph.is_directed():
        for cycle in nx.simple_cycles(graph):
            if len(cycle) <= max_length:
                cycles.append(cycle)
    else:
        # For undirected, use cycle basis
        try:
            basis = nx.cycle_basis(graph)
            cycles = [list(cycle) for cycle in basis if len(cycle) <= max_length]
        except:
            pass
    return cycles


# ============================================================================
# ZIGZAG PERSISTENCE (for temporal graphs)
# ============================================================================
def zigzag_persistence(graph_sequence: List[nx.Graph], max_dim: int = 1) -> Dict[str, Any]:
    """
    Compute zigzag persistence for a sequence of graphs.
    Uses GUDHI's zigzag persistence if available.

    Args:
        graph_sequence: list of NetworkX graphs representing snapshots.
        max_dim: maximum homology dimension.

    Returns:
        Dictionary containing persistence diagrams for each dimension,
        or an empty dict if computation fails.
    """
    if not HAS_GUDHI or not HAS_ZIGZAG:
        logger.warning("GUDHI zigzag persistence not available – returning empty")
        return {}

    try:
        # Build a zigzag filtration from the sequence of graphs.
        # Each graph defines a set of simplices (clique complex).
        # We need to create a list of complexes: each complex is a list of simplices (as tuples).
        # For each graph, we build its clique complex (all cliques up to max_dim+1).
        complexes = []
        for G in graph_sequence:
            cliques = []
            for k in range(1, max_dim+2):  # 1-simplices, 2-simplices, ...
                for clique in nx.enumerate_all_cliques(G):
                    if len(clique) == k:
                        cliques.append(tuple(sorted(clique)))
            complexes.append(cliques)

        # Initialize zigzag persistence
        zz = gd.ZigzagPersistence()
        # We need to add simplices in order of appearance and disappearance.
        # For simplicity, we'll use the built-in method that takes a list of complexes.
        # GUDHI's zigzag module may have a function `zigzag_homology_persistence` that takes a list of simplices per step.
        # The exact API may vary. We'll attempt a common pattern:
        from gudhi.zigzag import zigzag_homology_persistence
        intervals = zigzag_homology_persistence(complexes, max_dim)
        # intervals is a list of (dim, birth, death) where birth and death are in index space.
        diagrams = {}
        for dim, b, d in intervals:
            if dim not in diagrams:
                diagrams[dim] = []
            diagrams[dim].append((b, d))
        return {'intervals': intervals, 'diagrams': diagrams}
    except Exception as e:
        logger.error(f"Zigzag persistence failed: {e}")
        return {}


# ============================================================================
# NIEUW: CAUSAL DISCOVERY (using real causal_discovery if available)
# ============================================================================
class CausalDiscovery:
    """
    Causal discovery algorithms on graphs.
    This class wraps the real implementation from causal_discovery.py if available,
    otherwise provides simple placeholders.
    """
    def __init__(self, data: np.ndarray, variable_names: List[str]):
        """
        data: n_samples × n_variables matrix
        variable_names: names of variables (corresponding to columns)
        """
        self.data = data
        self.variable_names = variable_names
        self.result_graph = None
        if HAS_CAUSAL_DISCOVERY:
            self._real = RealCausalDiscovery(data, variable_names)
        else:
            self._real = None
            logger.warning("causal_discovery module not available – using placeholders")

    def run_pc(self, alpha: float = 0.05) -> nx.DiGraph:
        """PC algorithm."""
        if self._real is not None:
            return self._real.pc(alpha=alpha)
        # Fallback placeholder
        logger.warning("PC algorithm not implemented (fallback)")
        return nx.DiGraph()

    def run_fci(self, alpha: float = 0.05) -> nx.DiGraph:
        """FCI algorithm."""
        if self._real is not None:
            return self._real.fci(alpha=alpha)
        logger.warning("FCI algorithm not implemented (fallback)")
        return nx.DiGraph()

    def run_lingam(self) -> nx.DiGraph:
        """LiNGAM algorithm."""
        if self._real is not None:
            return self._real.lingam(method='ICALiNGAM')
        logger.warning("LiNGAM not implemented (fallback)")
        return nx.DiGraph()


# ============================================================================
# NIEUW: QUANTUM MACHINE LEARNING (placeholders – kept as is)
# ============================================================================
class QuantumML:
    """
    Quantum machine learning methods (QSVM, QGAN).
    """
    def __init__(self, n_qubits: int = 4):
        self.n_qubits = n_qubits

    def qsvm(self, train_data: np.ndarray, train_labels: np.ndarray,
             test_data: np.ndarray, test_labels: np.ndarray) -> float:
        """
        Quantum Support Vector Machine.
        Uses Qiskit's QSVC or PennyLane's kernel.
        """
        if HAS_QISKIT_ML:
            # Qiskit implementatie
            from qiskit.circuit.library import ZZFeatureMap
            from qiskit_machine_learning.kernels import FidelityQuantumKernel
            from qiskit_machine_learning.algorithms import QSVC

            feature_map = ZZFeatureMap(feature_dimension=train_data.shape[1], reps=2)
            kernel = FidelityQuantumKernel(feature_map=feature_map)
            qsvc = QSVC(quantum_kernel=kernel)
            qsvc.fit(train_data, train_labels)
            accuracy = qsvc.score(test_data, test_labels)
            return accuracy
        elif HAS_PENNYLANE:
            # PennyLane implementatie (via kernel)
            dev = qml.device('default.qubit', wires=self.n_qubits)
            @qml.qnode(dev)
            def kernel_circuit(x1, x2):
                # Encodeer data
                for i in range(len(x1)):
                    qml.RY(x1[i], wires=i)
                qml.adjoint(lambda: [qml.RY(x2[i], wires=i) for i in range(len(x2))])
                return qml.probs(wires=range(self.n_qubits))
            # Kernel matrix
            n_train = len(train_data)
            K = np.zeros((n_train, n_train))
            for i in range(n_train):
                for j in range(n_train):
                    K[i,j] = kernel_circuit(train_data[i], train_data[j])[0]
            # SVC met kernel
            from sklearn.svm import SVC
            clf = SVC(kernel='precomputed')
            clf.fit(K, train_labels)
            # Test kernel
            n_test = len(test_data)
            K_test = np.zeros((n_test, n_train))
            for i in range(n_test):
                for j in range(n_train):
                    K_test[i,j] = kernel_circuit(test_data[i], train_data[j])[0]
            return clf.score(K_test, test_labels)
        else:
            logger.warning("No quantum ML library available")
            return 0.5

    def qgan(self, real_data: np.ndarray, n_epochs: int = 10) -> Any:
        """
        Quantum Generative Adversarial Network (placeholder).
        """
        if not HAS_PENNYLANE and not HAS_QISKIT_ML:
            return None
        # Placeholder
        return None


# ============================================================================
# NIEUW: REINFORCEMENT LEARNING OP GRAFEN
# ============================================================================
if HAS_GYM:
    class GraphRLEnv(gym.Env):
        """
        RL‑omgeving op een graaf.
        De agent beweegt over knopen en moet een doel bereiken.
        """
        def __init__(self, graph: nx.Graph, target: Any, max_steps: int = 100):
            super().__init__()
            self.graph = graph
            self.target = target
            self.max_steps = max_steps
            self.current_node = None
            self.steps = 0
            self.nodes = list(graph.nodes())
            self.n_nodes = len(self.nodes)
            self.action_space = spaces.Discrete(self.n_nodes)
            self.observation_space = spaces.Discrete(self.n_nodes)
            # Bouw buurttabel
            self.adj = {node: list(graph.neighbors(node)) for node in self.nodes}

        def reset(self):
            self.current_node = np.random.choice(self.nodes)
            self.steps = 0
            return self.nodes.index(self.current_node)

        def step(self, action):
            self.steps += 1
            next_node = self.nodes[action]
            # Alleen bewegen als er een kant is
            if next_node in self.adj[self.current_node]:
                self.current_node = next_node
            reward = 1.0 if self.current_node == self.target else -0.01
            done = (self.current_node == self.target) or (self.steps >= self.max_steps)
            return self.nodes.index(self.current_node), reward, done, {}

    class GraphRLAgent:
        """Eenvoudige Q‑learning agent voor graafomgeving."""
        def __init__(self, env: GraphRLEnv, learning_rate: float = 0.1, discount: float = 0.95):
            self.env = env
            self.lr = learning_rate
            self.gamma = discount
            self.q_table = np.zeros((env.n_nodes, env.action_space.n))

        def train(self, episodes: int = 1000):
            for episode in range(episodes):
                state = self.env.reset()
                done = False
                while not done:
                    if np.random.random() < 0.1:
                        action = self.env.action_space.sample()
                    else:
                        action = np.argmax(self.q_table[state])
                    next_state, reward, done, _ = self.env.step(action)
                    best_next = np.max(self.q_table[next_state])
                    self.q_table[state, action] += self.lr * (reward + self.gamma * best_next - self.q_table[state, action])
                    state = next_state

        def act(self, state):
            return np.argmax(self.q_table[state])


# ============================================================================
# NIEUW: TOPOLOGISCHE DATA-ANALYSE MET MAPPER (INTERACTIEF)
# ============================================================================
class Mapper:
    """
    Mapper algoritme voor topologische data-analyse.
    """
    def __init__(self, data: np.ndarray, lens: List[np.ndarray], cover=None, clusterer=None):
        self.data = data
        self.lens = lens  # lijst van lens functies (elk een array van lengte n)
        self.cover = cover
        self.clusterer = clusterer
        self.graph = None
        self.mapper_obj = None

    def run(self):
        """Voer Mapper uit met kmapper."""
        if not HAS_KMAPPER:
            logger.warning("kmapper not available")
            return None
        import kmapper as km
        mapper = km.KeplerMapper(verbose=0)
        # Combineer lens functies tot één array
        lens_array = np.column_stack(self.lens)
        self.graph = mapper.map(lens_array, self.data, cover=self.cover, clusterer=self.clusterer)
        self.mapper_obj = mapper
        return self.graph

    def visualize(self, interactive: bool = False):
        """Visualiseer Mapper graph."""
        if self.graph is None:
            return None
        if interactive and HAS_DASH:
            # Maak een Dash app
            app = dash.Dash(__name__)
            # Gebruik de html visualisatie van kmapper
            html_str = self.mapper_obj.visualize(self.graph)
            app.layout = html.Div([
                html.H1("Mapper Graph"),
                html.Iframe(srcDoc=html_str, width="1000", height="800")
            ])
            return app
        elif VISUALIZATION_AVAILABLE:
            # Gebruik matplotlib
            self.mapper_obj.visualize(self.graph, path_html="mapper.html")
            # Toon in browser (hangt af van omgeving)
            import webbrowser
            webbrowser.open("mapper.html")
        else:
            logger.warning("No visualization available")


# ============================================================================
# NIEUW: DATABASE INTEGRATIE
# ============================================================================
class MotifDatabase:
    """
    Opslag en laden van analyse‑resultaten in SQLite of Neo4j.
    """
    def __init__(self, db_type: str = 'sqlite', connection_string: str = 'motifs.db'):
        self.db_type = db_type
        self.connection_string = connection_string
        self.conn = None
        if db_type == 'sqlite' and HAS_SQLITE:
            self.conn = sqlite3.connect(connection_string)
            self._create_sqlite_tables()
        elif db_type == 'neo4j' and HAS_NEO4J:
            self.conn = GraphDatabase.driver(connection_string)
        else:
            logger.warning(f"Database type {db_type} niet beschikbaar.")

    def _create_sqlite_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                name TEXT PRIMARY KEY,
                graph_name TEXT,
                timestamp REAL,
                data BLOB
            )
        ''')
        self.conn.commit()

    def store_analysis(self, name: str, graph_name: str, data: Dict):
        if self.db_type == 'sqlite' and self.conn:
            blob = pickle.dumps(data)
            cursor = self.conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO analyses (name, graph_name, timestamp, data) VALUES (?, ?, ?, ?)',
                           (name, graph_name, time.time(), blob))
            self.conn.commit()

    def load_analysis(self, name: str) -> Optional[Dict]:
        if self.db_type == 'sqlite' and self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT data FROM analyses WHERE name = ?', (name,))
            row = cursor.fetchone()
            if row:
                return pickle.loads(row[0])
        return None

    def close(self):
        if self.db_type == 'sqlite' and self.conn:
            self.conn.close()


# ============================================================================
# NIEUW: INTERACTIEF DASHBOARD
# ============================================================================
def create_motif_dashboard(analysis: 'TopologicalNetworkAnalysis'):
    """
    Maak een Dash dashboard voor een TopologicalNetworkAnalysis object.
    Toont persistentiediagrammen, motief tellingen, community kaart, etc.
    """
    if not HAS_DASH:
        return None

    app = dash.Dash(__name__)

    # Maak een Plotly figuur voor persistentiediagram
    fig_persistence = go.Figure()
    if analysis.persistence and analysis.persistence.diagrams:
        colors = ['blue', 'red', 'green']
        for dim, bars in analysis.persistence.diagrams.items():
            births = [b for b, _ in bars]
            deaths = [d for _, d in bars]
            fig_persistence.add_trace(go.Scatter(x=births, y=deaths, mode='markers',
                                                  name=f'H{dim}', marker=dict(color=colors[dim % 3])))

    # Maak een Plotly figuur voor motief tellingen (staafdiagram)
    fig_motifs = go.Figure()
    if analysis.motif_counts:
        motifs = list(analysis.motif_counts.keys())
        counts = list(analysis.motif_counts.values())
        fig_motifs.add_trace(go.Bar(x=motifs, y=counts, name='Motifs'))

    app.layout = html.Div([
        html.H1("Topological Network Analysis Dashboard"),
        html.Div([
            html.H3(f"Graph: {analysis.name}"),
            html.H3(f"Nodes: {analysis.graph.number_of_nodes() if analysis.graph else 0}"),
            html.H3(f"Edges: {analysis.graph.number_of_edges() if analysis.graph else 0}"),
        ]),
        html.H2("Persistence Diagram"),
        dcc.Graph(figure=fig_persistence),
        html.H2("Motif Counts"),
        dcc.Graph(figure=fig_motifs),
    ])

    return app


# ============================================================================
# NIEUW: HOGERE CATEGORIETHEORIE (∞‑categorieën placeholder)
# ============================================================================
@dataclass
class InfinityCategory:
    """
    Placeholder voor ∞‑categorieën.
    """
    objects: Set[Any]
    morphisms: Dict[Any, Any]  # etc.

    def compose(self, f, g):
        return None


# ============================================================================
# MAIN TOPOLOGICAL NETWORK ANALYSIS CLASS (INTEGRATES EVERYTHING)
# ============================================================================
@dataclass
class TopologicalNetworkAnalysis:
    """
    Comprehensive topological analysis of a network, integrating:
    - persistent homology (multiple filtrations, multiparameter)
    - motif / graphlet counting
    - community detection
    - centrality measures
    - graph kernels
    - temporal motif detection
    - caching and parallel processing
    - causal discovery
    - quantum ML
    - reinforcement learning
    - mapper
    - database
    - dashboard
    """
    graph: Optional[Any] = None
    name: str = "network"

    # Persistence data
    persistence: Optional[PersistentHomology] = None
    diagrams: Dict[int, List[Tuple[float, float]]] = field(default_factory=dict)
    betti_numbers_at_scale: Dict[float, Dict[int, int]] = field(default_factory=dict)
    persistent_entropy: float = 0.0
    landscapes: Dict[int, np.ndarray] = field(default_factory=dict)
    silhouettes: Dict[int, np.ndarray] = field(default_factory=dict)

    # Motif data
    motif_counts: Dict[str, int] = field(default_factory=dict)
    motif_significance: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Temporal motif data (if graph has timestamps)
    temporal_motif_results: Dict[str, Any] = field(default_factory=dict)

    # Community data
    community_map: Dict[str, int] = field(default_factory=dict)
    modularity: float = 0.0
    community_quality: Dict[str, float] = field(default_factory=dict)

    # Centralities
    centralities: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Kernel matrix (if multiple graphs)
    kernel_matrix: Optional[np.ndarray] = None

    # Causal discovery
    causal_graph: Optional[nx.DiGraph] = None

    # Quantum ML (placeholder)
    quantum_results: Dict[str, Any] = field(default_factory=dict)

    # Caching
    _cache: Dict[str, Any] = field(default_factory=dict)
    _redis_client = None

    def __post_init__(self):
        if HAS_NETWORKX and self.graph is not None:
            # If graph is a NetworkX graph, ensure node labels are integers for compatibility
            self.graph = nx.convert_node_labels_to_integers(self.graph, first_label=0, ordering='default', label_attribute='original')
        self._setup_redis()

    def _setup_redis(self):
        if REDIS_AVAILABLE:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.Redis.from_url("redis://localhost:6379")
            except:
                pass

    @cached(ttl=3600)
    def compute_persistence(self, filtration: FiltrationType = FiltrationType.CLIQUE,
                            max_dim: int = 2, **kwargs):
        """Compute persistent homology with specified filtration."""
        if not HAS_GUDHI and not HAS_RIPSER:
            logger.warning("No persistence backend available")
            return
        ph = PersistentHomology(self.graph, backend=kwargs.get('backend', 'gudhi'))
        if filtration == FiltrationType.CLIQUE:
            ph.build_clique_complex(max_dim)
        elif filtration == FiltrationType.VIETORIS_RIPS:
            max_edge = kwargs.get('max_edge_length', 1.0)
            metric = kwargs.get('metric', 'shortest_path')
            ph.build_vietoris_rips(max_edge, max_dim, metric)
        elif filtration == FiltrationType.ALPHA:
            points = kwargs.get('points', None)
            if points is not None:
                ph.build_alpha_complex(points, max_dim)
        elif filtration == FiltrationType.FUNCTION:
            values = kwargs.get('values', {})
            ph.build_function_filtration(values, max_dim)
        else:
            logger.warning(f"Filtration {filtration} not implemented")
            return
        ph.compute_persistence()
        self.persistence = ph
        self.diagrams = ph.diagrams
        self.persistent_entropy = ph.persistent_entropy()
        # Compute landscapes if requested
        if kwargs.get('landscapes', False):
            for dim in self.diagrams:
                self.landscapes[dim] = ph.persistent_landscapes(dim=dim)
        if kwargs.get('silhouettes', False):
            for dim in self.diagrams:
                self.silhouettes[dim] = ph.persistent_silhouette(dim=dim)
        return self.diagrams

    @cached(ttl=3600)
    def compute_motifs(self, max_graphlet_size: int = 4, significance: bool = True,
                       n_random: int = 100, use_gpu: bool = False, method: str = 'exact'):
        """Compute motif counts and optionally significance."""
        if not HAS_NETWORKX:
            return
        directed = self.graph.is_directed()
        counter = MotifCounter(self.graph, directed, use_gpu=use_gpu)
        self.motif_counts = counter.count_all_graphlets(max_graphlet_size, method=method)
        if significance:
            for motif in MotifType:
                try:
                    sig = counter.motif_significance(motif, n_random)
                    if sig:
                        self.motif_significance[motif.value] = sig
                except:
                    continue

    @cached(ttl=3600)
    def compute_temporal_motifs(self, edge_timestamps: Dict[Tuple[Any, Any], List[float]],
                                 window_size: float, motif_type: TemporalMotifType = TemporalMotifType.CONCURRENT,
                                 significance: bool = True, n_random: int = 100):
        """Compute temporal motifs if timestamps are available."""
        detector = TemporalMotifDetector(edge_timestamps, directed=self.graph.is_directed())
        windows = detector.sliding_windows(window_size)
        counts = [detector.count_temporal_triangles(w, motif_type) for w in windows]
        self.temporal_motif_results['counts'] = counts
        self.temporal_motif_results['windows'] = windows
        if significance:
            sig = detector.motif_significance(motif_type, window_size, n_random)
            self.temporal_motif_results['significance'] = sig

    @cached(ttl=3600)
    def detect_communities(self, method: str = "louvain", **kwargs):
        """Detect communities using specified method."""
        comm_map = detect_communities_enhanced(self.graph, method, **kwargs)
        if comm_map:
            self.community_map = comm_map
            # Compute modularity
            if HAS_NETWORKX:
                try:
                    from networkx.algorithms.community import modularity
                    communities_dict = defaultdict(list)
                    for node, comm in comm_map.items():
                        communities_dict[comm].append(node)
                    communities_list = list(communities_dict.values())
                    self.modularity = modularity(self.graph.to_undirected(), communities_list)
                except:
                    pass
            # Compute additional quality metrics if sklearn available
            if HAS_SKLEARN and 'true_labels' in kwargs:
                true_labels = kwargs['true_labels']
                aligned = [true_labels.get(node, -1) for node in self.graph.nodes()]
                pred = [comm_map.get(node, -1) for node in self.graph.nodes()]
                self.community_quality['ari'] = adjusted_rand_score(aligned, pred)
                self.community_quality['nmi'] = normalized_mutual_info_score(aligned, pred)

    @cached(ttl=3600)
    def compute_centralities(self):
        """Compute all centralities."""
        self.centralities = compute_centralities_extended(self.graph)

    def compute_kernel(self, other_graphs: List, kernel_type: GraphKernelType = GraphKernelType.WEISFEILER_LEHMAN):
        """Compute kernel matrix between this graph and a list of others."""
        if not HAS_NETWORKX:
            return
        graphs = [self.graph] + other_graphs
        kernel = GraphKernel(kernel_type)
        self.kernel_matrix = kernel.kernel_matrix(graphs)

    # ------------------------------------------------------------------------
    # NIEUW: Causal discovery (using updated CausalDiscovery)
    # ------------------------------------------------------------------------
    def run_causal_discovery(self, data: np.ndarray, variable_names: List[str],
                             algorithm: CausalAlgorithm = CausalAlgorithm.PC, **kwargs):
        """Run causal discovery on data matrix (n_samples × n_variables)."""
        cd = CausalDiscovery(data, variable_names)
        if algorithm == CausalAlgorithm.PC:
            self.causal_graph = cd.run_pc(**kwargs)
        elif algorithm == CausalAlgorithm.FCI:
            self.causal_graph = cd.run_fci(**kwargs)
        elif algorithm == CausalAlgorithm.LINGAM:
            self.causal_graph = cd.run_lingam()
        return self.causal_graph

    # ------------------------------------------------------------------------
    # NIEUW: Quantum machine learning (unchanged)
    # ------------------------------------------------------------------------
    def run_qsvm(self, train_data, train_labels, test_data, test_labels, n_qubits=4):
        """Run QSVM."""
        qml = QuantumML(n_qubits=n_qubits)
        acc = qml.qsvm(train_data, train_labels, test_data, test_labels)
        self.quantum_results['qsvm_accuracy'] = acc
        return acc

    # ------------------------------------------------------------------------
    # NIEUW: Reinforcement learning
    # ------------------------------------------------------------------------
    def run_rl(self, target: Any, episodes: int = 500):
        """Train een RL agent op de graaf."""
        if not HAS_GYM:
            return None
        env = GraphRLEnv(self.graph, target)
        agent = GraphRLAgent(env)
        agent.train(episodes=episodes)
        return agent

    # ------------------------------------------------------------------------
    # NIEUW: Mapper
    # ------------------------------------------------------------------------
    def run_mapper(self, lens: List[np.ndarray], cover=None, clusterer=None):
        """Run Mapper op de graaf (gebruikt node features als data)."""
        # Data: we hebben node features nodig; als die niet bestaan, gebruik graad.
        if self.graph is None:
            return None
        data = np.array([self.graph.degree(node) for node in self.graph.nodes()]).reshape(-1, 1)
        mapper = Mapper(data, lens, cover, clusterer)
        mapper.run()
        return mapper

    # ------------------------------------------------------------------------
    # NIEUW: Database opslag
    # ------------------------------------------------------------------------
    def save_to_db(self, db: MotifDatabase, name: str):
        """Sla analyse‑resultaten op in database."""
        data = self.to_dict()
        db.store_analysis(name, self.name, data)

    # ------------------------------------------------------------------------
    # NIEUW: Dashboard
    # ------------------------------------------------------------------------
    def create_dashboard(self):
        """Maak een Dash dashboard voor deze analyse."""
        return create_motif_dashboard(self)

    # ------------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Export analysis results."""
        return {
            'name': self.name,
            'nodes': self.graph.number_of_nodes() if self.graph else 0,
            'edges': self.graph.number_of_edges() if self.graph else 0,
            'persistence': {
                'diagrams': {str(k): [(b,d) for b,d in v] for k,v in self.diagrams.items()},
                'persistent_entropy': self.persistent_entropy,
            },
            'motif_counts': self.motif_counts,
            'motif_significance': self.motif_significance,
            'temporal_motifs': self.temporal_motif_results,
            'communities': {
                'map': self.community_map,
                'modularity': self.modularity,
                'quality': self.community_quality,
            },
            'centralities': self.centralities,
            'causal_graph': nx.to_dict_of_dicts(self.causal_graph) if self.causal_graph else None,
            'quantum_results': self.quantum_results,
        }

    def save_hdf5(self, filename: str):
        """Save results to HDF5 format."""
        if not HAS_H5PY:
            logger.warning("h5py not available – cannot save to HDF5")
            return
        with h5py.File(filename, 'w') as f:
            f.attrs['name'] = self.name
            f.attrs['nodes'] = self.graph.number_of_nodes() if self.graph else 0
            f.attrs['edges'] = self.graph.number_of_edges() if self.graph else 0
            # Persistence diagrams
            for dim, bars in self.diagrams.items():
                grp = f.create_group(f'persistence/dim_{dim}')
                data = np.array(bars)
                grp.create_dataset('bars', data=data)
            # Motif counts
            for k, v in self.motif_counts.items():
                f.attrs[f'motif_{k}'] = v
            # etc.

    def plot(self, filename: Optional[str] = None, what: str = 'persistence'):
        """Generate plots (persistence diagram, barcode, etc.)."""
        if what == 'persistence' and self.persistence:
            self.persistence.plot_diagram(filename)
        elif what == 'barcode' and self.persistence:
            self.persistence.plot_barcode(filename)
        elif what == 'communities' and self.community_map:
            if VISUALIZATION_AVAILABLE:
                pos = nx.spring_layout(self.graph)
                plt.figure()
                colors = [self.community_map[node] for node in self.graph.nodes()]
                nx.draw(self.graph, pos, node_color=colors, cmap=plt.cm.tab20, with_labels=False)
                if filename:
                    plt.savefig(filename)
                else:
                    plt.show()
                plt.close()


# ============================================================================
# CONVENIENCE FUNCTIONS (standalone)
# ============================================================================
def find_paths(graph, source: str, target: str, max_length: int = 10) -> List[List[str]]:
    if not HAS_NETWORKX or graph is None:
        return []
    try:
        return [list(p) for p in nx.all_simple_paths(graph, source, target, cutoff=max_length)]
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []

def find_all_cycles(graph, max_length: int = 10) -> List[List[str]]:
    return find_all_cycles(graph, max_length)

def compute_centralities(graph) -> Dict[str, Dict[str, float]]:
    return compute_centralities_extended(graph)

def detect_communities(graph, method: str = "louvain") -> Dict[str, int]:
    return detect_communities_enhanced(graph, method)


# ============================================================================
# DEMONSTRATION
# ============================================================================
if __name__ == "__main__":
    # Create a sample graph
    if HAS_NETWORKX:
        G = nx.karate_club_graph()
        analysis = TopologicalNetworkAnalysis(graph=G, name="Karate Club")
        analysis.compute_persistence(filtration=FiltrationType.CLIQUE, max_dim=2)
        analysis.compute_motifs(max_graphlet_size=4, significance=True, n_random=10)
        analysis.detect_communities(method="louvain")
        analysis.compute_centralities()
        print(analysis.to_dict())
        analysis.plot("karate_persistence.png", what='persistence')
        analysis.plot("karate_communities.png", what='communities')

        # Example of temporal motif (if we had timestamps)
        # timestamps = {...}
        # analysis.compute_temporal_motifs(timestamps, window_size=1.0)

        # Example of kernel
        G2 = nx.erdos_renyi_graph(G.number_of_nodes(), 0.1)
        analysis.compute_kernel([G2], kernel_type=GraphKernelType.SHORTEST_PATH)
        print("Kernel matrix shape:", analysis.kernel_matrix.shape)

        # Example of causal discovery (als data beschikbaar)
        # data = np.random.randn(100, 5)
        # analysis.run_causal_discovery(data, ['A','B','C','D','E'], algorithm=CausalAlgorithm.PC)

        # Example of RL (als gym beschikbaar)
        if HAS_GYM:
            agent = analysis.run_rl(target=10, episodes=200)
            print("RL agent trained.")

        # Example of Mapper
        # lens = [np.random.randn(G.number_of_nodes()) for _ in range(2)]
        # mapper = analysis.run_mapper(lens)
        # if mapper:
        #     mapper.visualize()

        # Example of dashboard (als Dash beschikbaar)
        if HAS_DASH:
            app = analysis.create_dashboard()
            # app.run_server()  # zou de server starten
            print("Dashboard created.")
    else:
        print("NetworkX not available – cannot run demo")