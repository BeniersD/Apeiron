"""
motif_detection.py – Motif and Topological Data Analysis for Layer 2
====================================================================
Provides motif counting, persistent homology, temporal motifs,
graph kernels, community detection, centrality measures, cycle
detection, and zigzag persistence.

All heavy dependencies are optional and degrade gracefully.
"""
from __future__ import annotations

import hashlib
import logging
import pickle
import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations, product
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Caching decorator (in‑memory only)
# ---------------------------------------------------------------------------
def cached(ttl: int = 3600):
    def decorator(func):
        _cache: Dict[str, Tuple[Any, float]] = {}
        def wrapper(self, *args, **kwargs):
            key = hashlib.md5(
                (func.__name__ + str(args) + str(sorted(kwargs.items()))).encode()
            ).hexdigest()
            if key in _cache:
                val, exp = _cache[key]
                if time.time() < exp:
                    return val
                del _cache[key]
            result = func(self, *args, **kwargs)
            _cache[key] = (result, time.time() + ttl)
            return result
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Optional imports – all handled gracefully
# ---------------------------------------------------------------------------
try:
    import networkx as nx
    from networkx.algorithms import community, isomorphism
    HAS_NETWORKX = True
except ImportError:
    nx = None
    HAS_NETWORKX = False

try:
    import gudhi as gd
    HAS_GUDHI = True
except ImportError:
    HAS_GUDHI = False

try:
    from scipy.stats import norm
    HAS_SCIPY_STATS = True
except ImportError:
    HAS_SCIPY_STATS = False

try:
    from scipy.cluster.vq import kmeans2
    from scipy.sparse.linalg import eigsh
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from statsmodels.tsa.stattools import grangercausalitytests
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    from numba import jit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False


# ============================================================================
# Enums
# ============================================================================
class FiltrationType(Enum):
    VIETORIS_RIPS = "vietoris_rips"
    CECH = "cech"
    CLIQUE = "clique"
    WITNESS = "witness"
    ALPHA = "alpha"
    FUNCTION = "function"

class MotifType(Enum):
    FEEDBACK_LOOP = "feedback_loop"
    BIFAN = "bifan"
    CHAIN = "chain"
    TRIANGLE = "triangle"
    CLIQUE_K = "clique"
    STAR = "star"
    CYCLE = "cycle"

class TemporalMotifType(Enum):
    SEQUENTIAL = "sequential"
    CONCURRENT = "concurrent"
    DELAYED = "delayed"

class GraphKernelType(Enum):
    WEISFEILER_LEHMAN = "wl"
    RANDOM_WALK = "random_walk"
    SHORTEST_PATH = "shortest_path"
    GRAPHLET = "graphlet"
    NEURAL = "neural"


# ============================================================================
# Motif counter (with Numba acceleration)
# ============================================================================
class MotifCounter:
    """Count occurrences of small subgraphs in a graph."""
    def __init__(self, graph, directed: bool = False, use_gpu: bool = False):
        self.graph = graph
        self.directed = directed
        self.use_gpu = use_gpu

    def count_triangles(self) -> int:
        if not HAS_NETWORKX:
            return 0
        if self.directed:
            return sum(1 for _ in nx.simple_cycles(self.graph) if len(_) == 3)
        # Undirected
        adj = nx.adjacency_matrix(self.graph).todense()
        if HAS_NUMBA and not self.directed:
            try:
                # inline Numba function
                @jit(nopython=True)
                def _triangles(A):
                    n = A.shape[0]
                    c = 0
                    for i in range(n):
                        for j in range(i+1, n):
                            if A[i, j]:
                                for k in range(j+1, n):
                                    if A[i, k] and A[j, k]:
                                        c += 1
                    return c
                return _triangles(np.array(adj))
            except Exception:
                pass
        return sum(nx.triangles(self.graph).values()) // 3

    def count_k_cliques(self, k: int) -> int:
        if not HAS_NETWORKX or k < 3:
            return 0
        return sum(1 for _ in nx.enumerate_all_cliques(self.graph) if len(_) == k)

    def count_motif(self, motif_type: MotifType, **kwargs) -> int:
        if not HAS_NETWORKX:
            return 0
        if motif_type == MotifType.TRIANGLE:
            return self.count_triangles()
        if motif_type == MotifType.CLIQUE_K:
            return self.count_k_cliques(kwargs.get('k', 4))
        if motif_type == MotifType.STAR:
            k = kwargs.get('k', 3)
            return self._count_stars(k)
        if motif_type == MotifType.CYCLE:
            k = kwargs.get('k', 3)
            return self._count_cycles(k)
        # use subgraph isomorphism for others
        pattern = self._build_pattern(motif_type, **kwargs)
        if pattern is None:
            return 0
        matcher = isomorphism.GraphMatcher(self.graph, pattern) if not self.directed else isomorphism.DiGraphMatcher(self.graph, pattern)
        return sum(1 for _ in matcher.subgraph_isomorphisms_iter())

    def _build_pattern(self, mt: MotifType, **kwargs):
        if mt == MotifType.FEEDBACK_LOOP and self.directed:
            G = nx.DiGraph()
            G.add_edges_from([(0,1),(1,2),(2,0)])
            return G
        if mt == MotifType.BIFAN and self.directed:
            G = nx.DiGraph()
            G.add_edges_from([(0,2),(0,3),(1,2),(1,3)])
            return G
        if mt == MotifType.CHAIN:
            return nx.path_graph(3, create_using=nx.DiGraph if self.directed else nx.Graph)
        if mt == MotifType.STAR:
            return nx.star_graph(kwargs.get('k',3)-1, create_using=nx.Graph if not self.directed else nx.DiGraph)
        if mt == MotifType.CYCLE:
            return nx.cycle_graph(kwargs.get('k',3), create_using=nx.Graph if not self.directed else nx.DiGraph)
        return None

    def _count_stars(self, k: int) -> int:
        from math import comb
        c = 0
        for node in self.graph.nodes():
            d = self.graph.degree(node)
            if d >= k:
                c += comb(d, k)
        return c

    def _count_cycles(self, k: int) -> int:
        if self.directed:
            return sum(1 for _ in nx.simple_cycles(self.graph) if len(_) == k)
        return sum(1 for _ in nx.cycle_basis(self.graph) if len(_) == k)

    def count_all_graphlets(self, max_size: int = 4, method: str = 'exact') -> Dict[str, int]:
        counts = {}
        for k in range(3, max_size+1):
            counts[f'{k}-cliques'] = self.count_k_cliques(k)
            if k <= 4:
                counts[f'{k}-star'] = self._count_stars(k)
                counts[f'{k}-cycle'] = self._count_cycles(k)
        return counts

    def motif_significance(self, motif_type: MotifType, n_random: int = 100, **kwargs) -> Dict[str, float]:
        if not HAS_NETWORKX or not HAS_SCIPY_STATS:
            return {}
        real = self.count_motif(motif_type, **kwargs)
        rand_vals = []
        for _ in range(n_random):
            if self.directed:
                rg = nx.directed_configuration_model(
                    [d for _, d in self.graph.out_degree()],
                    [d for _, d in self.graph.in_degree()])
            else:
                rg = nx.configuration_model([d for _, d in self.graph.degree()])
            rg = nx.DiGraph(rg) if self.directed else nx.Graph(rg)
            c = MotifCounter(rg, self.directed).count_motif(motif_type, **kwargs)
            rand_vals.append(c)
        mean = np.mean(rand_vals)
        std = np.std(rand_vals)
        if std == 0:
            return {'observed': real, 'mean_random': mean, 'z_score': 0.0, 'p_value': 1.0}
        z = (real - mean) / std
        p = 2 * (1 - norm.cdf(abs(z)))
        return {'observed': real, 'mean_random': mean, 'std_random': std, 'z_score': z, 'p_value': p}


# ============================================================================
# Persistent homology
# ============================================================================
class PersistentHomology:
    """Compute persistent homology using GUDHI or Ripser."""
    def __init__(self, graph, backend='gudhi'):
        self.graph = graph
        self.backend = backend
        self.simplex_tree = None
        self.persistence = None
        self.diagrams: Dict[int, List[Tuple[float, float]]] = {}

    def build_clique_complex(self, max_dim: int = 2):
        if not HAS_GUDHI or not HAS_NETWORKX:
            return
        st = gd.SimplexTree()
        for node in self.graph.nodes():
            st.insert([node])
        for u, v in self.graph.edges():
            st.insert([u, v])
        for clique in nx.enumerate_all_cliques(self.graph):
            if len(clique) > 2:
                st.insert(clique)
        self.simplex_tree = st

    def build_vietoris_rips(self, max_edge_length: float, max_dim: int = 2, metric='shortest_path'):
        if not HAS_NETWORKX or not HAS_GUDHI:
            return
        if metric == 'shortest_path':
            try:
                dist = nx.floyd_warshall_numpy(self.graph)
            except Exception:
                return
        else:
            return
        rips = gd.RipsComplex(distance_matrix=dist, max_edge_length=max_edge_length)
        self.simplex_tree = rips.create_simplex_tree(max_dimension=max_dim)

    def compute_persistence(self):
        if self.simplex_tree:
            self.simplex_tree.compute_persistence()
            self.persistence = self.simplex_tree.persistence()
            for dim in range(3):
                intervals = self.simplex_tree.persistence_intervals_in_dimension(dim)
                self.diagrams[dim] = [(b, d) for b, d in intervals if d < float('inf')]
        elif self.diagrams:
            pass

    def betti_numbers(self, epsilon: float) -> Dict[int, int]:
        if self.simplex_tree:
            return {dim: self.simplex_tree.persistent_betti_number(dim, epsilon) for dim in range(3)}
        return {}

    def persistent_entropy(self) -> float:
        all_bars = []
        for bars in self.diagrams.values():
            all_bars.extend(d - b for b, d in bars if d < float('inf'))
        if not all_bars:
            return 0.0
        total = sum(all_bars)
        probs = [l / total for l in all_bars]
        return -sum(p * np.log(p) for p in probs)


# ============================================================================
# Temporal motif detector
# ============================================================================
class TemporalMotifDetector:
    """Detect motifs in temporal graphs."""
    def __init__(self, edge_timestamps: Dict[Tuple[Any, Any], List[float]], directed: bool = False):
        self.edge_timestamps = edge_timestamps
        self.directed = directed

    def get_nodes(self) -> Set[Any]:
        nodes = set()
        for (u, v) in self.edge_timestamps:
            nodes.add(u); nodes.add(v)
        return nodes

    def sliding_windows(self, window_size: float, step: float = None) -> List[Tuple[float, float]]:
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
        nodes = self.get_nodes()
        node_list = list(nodes)
        idx = {n: i for i, n in enumerate(node_list)}
        adj = defaultdict(list)
        for (u, v), times in self.edge_timestamps.items():
            for t in times:
                if window[0] <= t <= window[1]:
                    adj[(idx[u], idx[v])].append(t)
        count = 0
        for i, j, k in combinations(range(len(node_list)), 3):
            edges = [(i,j), (j,i), (i,k), (k,i), (j,k), (k,j)]
            times = {e: adj[e] for e in edges if e in adj}
            if motif_type == TemporalMotifType.CONCURRENT:
                tri1 = [(i,j), (j,k), (k,i)]
                tri2 = [(i,k), (k,j), (j,i)]
                if all(e in times for e in tri1):
                    count += 1
                elif all(e in times for e in tri2):
                    count += 1
        return count

    def motif_significance(self, motif_type: TemporalMotifType, window_size: float, n_random: int = 100) -> Dict[str, float]:
        windows = self.sliding_windows(window_size)
        real_counts = [self.count_temporal_triangles(w, motif_type) for w in windows]
        real_mean = np.mean(real_counts)
        all_times = []
        for t in self.edge_timestamps.values():
            all_times.extend(t)
        rand_means = []
        for _ in range(n_random):
            shuffled = {}
            for (u,v), times in self.edge_timestamps.items():
                shuffled[(u,v)] = list(np.random.choice(all_times, size=len(times), replace=False))
            det = TemporalMotifDetector(shuffled, self.directed)
            counts = [det.count_temporal_triangles(w, motif_type) for w in windows]
            rand_means.append(np.mean(counts))
        mean = np.mean(rand_means)
        std = np.std(rand_means)
        if std == 0:
            return {'observed_mean': real_mean, 'mean_random': mean, 'z_score': 0.0, 'p_value': 1.0}
        z = (real_mean - mean) / std
        p = 2 * (1 - norm.cdf(abs(z)))
        return {'observed_mean': real_mean, 'mean_random': mean, 'std_random': std, 'z_score': z, 'p_value': p}


# ============================================================================
# Graph kernels
# ============================================================================
class GraphKernel:
    def __init__(self, kernel_type: GraphKernelType = GraphKernelType.WEISFEILER_LEHMAN):
        self.kernel_type = kernel_type

    def compute(self, g1, g2, **kwargs) -> float:
        if self.kernel_type == GraphKernelType.WEISFEILER_LEHMAN:
            return self._wl_kernel(g1, g2, **kwargs)
        if self.kernel_type == GraphKernelType.RANDOM_WALK:
            return self._rw_kernel(g1, g2, **kwargs)
        if self.kernel_type == GraphKernelType.SHORTEST_PATH:
            return self._sp_kernel(g1, g2)
        if self.kernel_type == GraphKernelType.GRAPHLET:
            return self._graphlet_kernel(g1, g2, **kwargs)
        return 0.0

    def _wl_kernel(self, g1, g2, h: int = 3) -> float:
        def wl_colors(g, it):
            col = {n: str(g.degree(n)) for n in g.nodes()}
            for _ in range(it):
                new = {}
                for n in g.nodes():
                    nb = sorted(col[m] for m in g.neighbors(n))
                    new[n] = str(hash((col[n], tuple(nb))))
                col = new
            return set(col.values())
        return len(wl_colors(g1, h) & wl_colors(g2, h))

    def _rw_kernel(self, g1, g2, lambda_decay=0.1, max_steps=10) -> float:
        A1 = nx.adjacency_matrix(g1).todense()
        A2 = nx.adjacency_matrix(g2).todense()
        if A1.shape != A2.shape:
            return 0.0
        n = A1.shape[0]
        K = n
        A1pow, A2pow = A1, A2
        for k in range(1, max_steps+1):
            K += (lambda_decay**k) * np.trace(A1pow @ A2pow.T)
            A1pow = A1pow @ A1
            A2pow = A2pow @ A2
        return K

    def _sp_kernel(self, g1, g2) -> float:
        sp1 = dict(nx.all_pairs_shortest_path_length(g1))
        sp2 = dict(nx.all_pairs_shortest_path_length(g2))
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
        return sum(hist1[k] * hist2[k] for k in set(hist1) | set(hist2))

    def _graphlet_kernel(self, g1, g2, size=3) -> float:
        c1 = MotifCounter(g1).count_all_graphlets(max_size=size)
        c2 = MotifCounter(g2).count_all_graphlets(max_size=size)
        return sum(c1.get(k,0) * c2.get(k,0) for k in set(c1) | set(c2))


# ============================================================================
# Community detection
# ============================================================================
def detect_communities_enhanced(graph, method: str = "louvain", **kwargs) -> Dict[str, int]:
    if not HAS_NETWORKX or graph is None:
        return {}
    if method == "louvain":
        try:
            from community import community_louvain
            return community_louvain.best_partition(graph.to_undirected())
        except ImportError:
            comp = community.greedy_modularity_communities(graph.to_undirected())
            return {node: i for i, c in enumerate(comp) for node in c}
    if method == "spectral":
        if not HAS_SCIPY:
            return {}
        L = nx.laplacian_matrix(graph).todense()
        n_clusters = kwargs.get('n_clusters', 2)
        _, eigvecs = eigsh(L, k=min(n_clusters+1, graph.number_of_nodes()-1), which='SM')
        features = eigvecs[:, 1:n_clusters+1]
        if HAS_SKLEARN:
            labels = KMeans(n_clusters=n_clusters).fit_predict(features)
        else:
            _, labels = kmeans2(features, n_clusters)
        node_list = list(graph.nodes())
        return {node_list[i]: int(labels[i]) for i in range(len(node_list))}
    if method == "label_propagation":
        comp = community.label_propagation_communities(graph.to_undirected())
        return {node: i for i, c in enumerate(comp) for node in c}
    return {}


# ============================================================================
# Centralities
# ============================================================================
def compute_centralities_extended(graph) -> Dict[str, Dict[str, float]]:
    if not HAS_NETWORKX or graph is None:
        return {}
    c = {}
    c['degree'] = nx.degree_centrality(graph)
    c['betweenness'] = nx.betweenness_centrality(graph)
    c['closeness'] = nx.closeness_centrality(graph)
    try:
        c['eigenvector'] = nx.eigenvector_centrality(graph)
    except:
        pass
    c['pagerank'] = nx.pagerank(graph)
    return c


# ============================================================================
# Cycle / path detection
# ============================================================================
def find_paths(graph, source: str, target: str, max_length: int = 10) -> List[List[str]]:
    if not HAS_NETWORKX or graph is None:
        return []
    try:
        return [list(p) for p in nx.all_simple_paths(graph, source, target, cutoff=max_length)]
    except:
        return []

def find_all_cycles(graph, max_length: int = 10) -> List[List[str]]:
    if not HAS_NETWORKX:
        return []
    if graph.is_directed():
        return [c for c in nx.simple_cycles(graph) if len(c) <= max_length]
    return [list(c) for c in nx.cycle_basis(graph) if len(c) <= max_length]


# ============================================================================
# Zigzag persistence (placeholder)
# ============================================================================
def zigzag_persistence(graph_sequence: List, max_dim: int = 1) -> Dict[str, Any]:
    if not HAS_GUDHI:
        logger.warning("GUDHI required for zigzag persistence")
        return {}
    try:
        from gudhi.zigzag import zigzag_homology_persistence
        complexes = []
        for G in graph_sequence:
            cliques = []
            for k in range(1, max_dim+2):
                for clique in nx.enumerate_all_cliques(G):
                    if len(clique) == k:
                        cliques.append(tuple(sorted(clique)))
            complexes.append(cliques)
        intervals = zigzag_homology_persistence(complexes, max_dim)
        diagrams = {}
        for dim, b, d in intervals:
            diagrams.setdefault(dim, []).append((b, d))
        return {'intervals': intervals, 'diagrams': diagrams}
    except Exception as e:
        logger.error(f"Zigzag persistence failed: {e}")
        return {}


# ============================================================================
# TopologicalNetworkAnalysis (aggregates all of the above)
# ============================================================================
@dataclass
class TopologicalNetworkAnalysis:
    graph: Optional[Any] = None
    name: str = "network"

    persistence: Optional[PersistentHomology] = None
    diagrams: Dict[int, List[Tuple[float, float]]] = field(default_factory=dict)
    betti_numbers_at_scale: Dict[float, Dict[int, int]] = field(default_factory=dict)
    persistent_entropy: float = 0.0

    motif_counts: Dict[str, int] = field(default_factory=dict)
    motif_significance: Dict[str, Dict[str, float]] = field(default_factory=dict)

    temporal_motif_results: Dict[str, Any] = field(default_factory=dict)

    community_map: Dict[str, int] = field(default_factory=dict)
    modularity: float = 0.0

    centralities: Dict[str, Dict[str, float]] = field(default_factory=dict)
    kernel_matrix: Optional[np.ndarray] = None

    @cached(ttl=3600)
    def compute_persistence(self, filtration: FiltrationType = FiltrationType.CLIQUE, max_dim: int = 2, **kwargs):
        if not HAS_GUDHI:
            return
        ph = PersistentHomology(self.graph, backend=kwargs.get('backend', 'gudhi'))
        if filtration == FiltrationType.CLIQUE:
            ph.build_clique_complex(max_dim)
        elif filtration == FiltrationType.VIETORIS_RIPS:
            ph.build_vietoris_rips(kwargs.get('max_edge_length', 1.0), max_dim, kwargs.get('metric', 'shortest_path'))
        else:
            return
        ph.compute_persistence()
        self.persistence = ph
        self.diagrams = ph.diagrams
        self.persistent_entropy = ph.persistent_entropy()

    @cached(ttl=3600)
    def compute_motifs(self, max_graphlet_size: int = 4, significance: bool = True, n_random: int = 100):
        if not HAS_NETWORKX:
            return
        directed = self.graph.is_directed()
        counter = MotifCounter(self.graph, directed)
        self.motif_counts = counter.count_all_graphlets(max_graphlet_size)
        if significance:
            for mt in MotifType:
                try:
                    sig = counter.motif_significance(mt, n_random)
                    if sig:
                        self.motif_significance[mt.value] = sig
                except:
                    continue

    @cached(ttl=3600)
    def detect_communities(self, method: str = "louvain", **kwargs):
        self.community_map = detect_communities_enhanced(self.graph, method, **kwargs)

    @cached(ttl=3600)
    def compute_centralities(self):
        self.centralities = compute_centralities_extended(self.graph)

    def compute_kernel(self, other_graphs: List, kernel_type: GraphKernelType = GraphKernelType.WEISFEILER_LEHMAN):
        if not HAS_NETWORKX:
            return
        graphs = [self.graph] + other_graphs
        kernel = GraphKernel(kernel_type)
        self.kernel_matrix = kernel.kernel_matrix(graphs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'nodes': self.graph.number_of_nodes() if self.graph else 0,
            'edges': self.graph.number_of_edges() if self.graph else 0,
            'persistence': {'diagrams': self.diagrams},
            'motifs': self.motif_counts,
            'communities': self.community_map,
        }