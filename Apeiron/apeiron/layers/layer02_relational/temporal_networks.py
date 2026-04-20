"""
TEMPORAL NETWORKS – ULTIMATE IMPLEMENTATION
============================================
This module provides tools for representing and analyzing temporal networks
(graphs that change over time). It includes:

- `TemporalNetwork`: a collection of graph snapshots at discrete times
- `TemporalGraph`: an alternative representation with edge timestamps
- Sliding window aggregation and temporal motif counting (multiple motif types)
- Dynamic community detection (track communities over time)
- Evolution of graph statistics (density, clustering, etc.)
- Change point detection in time series of graph metrics
- Forecasting future graph structure using ARIMA or simple models
- Integration with the `UltimateRelation.temporal_evolution` field

All features degrade gracefully if required libraries are missing.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Set, Any, Tuple, Union, Callable
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations

# ============================================================================
# OPTIONAL LIBRARIES – ALL HANDLED GRACEFULLY
# ============================================================================

# NetworkX for graph operations
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

# Matplotlib for plotting
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Statsmodels for time series analysis (change point detection, forecasting)
try:
    from statsmodels.tsa.stattools import acf, pacf
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

# Scikit‑learn for change point detection (optional)
try:
    from sklearn.model_selection import train_test_split
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# ruptures for change point detection (optional)
try:
    import ruptures as rpt
    HAS_RUPTURES = True
except ImportError:
    HAS_RUPTURES = False

# SciPy for statistical functions (norm for motif significance)
try:
    from scipy.stats import norm
    HAS_SCIPY_STATS = True
except ImportError:
    HAS_SCIPY_STATS = False

logger = logging.getLogger(__name__)


# ============================================================================
# TEMPORAL NETWORK REPRESENTATIONS
# ============================================================================

class TemporalGraph:
    """
    A temporal graph where edges have timestamps (or lists of timestamps).
    This representation is memory‑efficient for sparse events.

    Attributes:
        nodes: set of nodes
        edge_timestamps: dict mapping (u, v) -> list of timestamps (ordered)
        directed: whether the graph is directed
        weighted: whether timestamps imply weight (default False)
    """
    def __init__(self, directed: bool = False, weighted: bool = False):
        self.nodes: Set[Any] = set()
        self.edge_timestamps: Dict[Tuple[Any, Any], List[float]] = defaultdict(list)
        self.directed = directed
        self.weighted = weighted

    def add_interaction(self, u: Any, v: Any, timestamp: float, weight: float = 1.0):
        """Add an interaction (edge occurrence) at given time."""
        self.nodes.update([u, v])
        key = (u, v) if self.directed else (min(u, v), max(u, v))
        self.edge_timestamps[key].append(timestamp)
        if self.weighted:
            # For weighted, we might store weight per timestamp, but not implemented here.
            pass

    def snapshot_at_time(self, t: float, delta: float = 0.0) -> nx.Graph:
        """
        Return a snapshot graph containing edges active at time t (within ±delta).
        Requires NetworkX.
        """
        if not HAS_NETWORKX:
            raise ImportError("NetworkX required for snapshot creation")
        G = nx.DiGraph() if self.directed else nx.Graph()
        G.add_nodes_from(self.nodes)
        for (u, v), times in self.edge_timestamps.items():
            for ts in times:
                if abs(ts - t) <= delta:
                    G.add_edge(u, v)
                    break
        return G

    def aggregate(self, start: float, end: float) -> nx.Graph:
        """Return a graph with edges that occurred in [start, end]."""
        if not HAS_NETWORKX:
            raise ImportError("NetworkX required for aggregation")
        G = nx.DiGraph() if self.directed else nx.Graph()
        G.add_nodes_from(self.nodes)
        for (u, v), times in self.edge_timestamps.items():
            if any(start <= ts <= end for ts in times):
                G.add_edge(u, v)
        return G


class TemporalNetwork:
    """
    A temporal network represented as a sequence of graph snapshots at discrete times.
    Each snapshot is a NetworkX graph (or dict of relations). Useful when data is naturally
    binned into time windows.

    Attributes:
        snapshots: list of graphs (or dicts) for each time step
        timestamps: list of time points (must match length of snapshots)
    """
    def __init__(self, snapshots: Optional[List] = None, timestamps: Optional[List[float]] = None):
        self.snapshots = snapshots if snapshots is not None else []
        self.timestamps = timestamps if timestamps is not None else []

    def __len__(self):
        return len(self.snapshots)

    def add_snapshot(self, graph, timestamp: float):
        """Add a snapshot at given time."""
        self.snapshots.append(graph)
        self.timestamps.append(timestamp)

    def get_graph_at_time(self, t: float, tolerance: float = 0.0) -> Optional[Any]:
        """Return the snapshot closest to t within tolerance."""
        if not self.timestamps:
            return None
        idx = np.argmin([abs(ts - t) for ts in self.timestamps])
        if abs(self.timestamps[idx] - t) <= tolerance:
            return self.snapshots[idx]
        return None

    def sliding_windows(self, window_size: int, step: int = 1) -> List['TemporalNetwork']:
        """
        Create overlapping windows of snapshots.
        Returns a list of TemporalNetwork objects (each with window_size snapshots).
        """
        windows = []
        for i in range(0, len(self) - window_size + 1, step):
            win_snap = self.snapshots[i:i+window_size]
            win_ts = self.timestamps[i:i+window_size]
            windows.append(TemporalNetwork(win_snap, win_ts))
        return windows


# ============================================================================
# DYNAMIC COMMUNITY DETECTION
# ============================================================================

def dynamic_communities(tn: TemporalNetwork, method: str = 'louvain', **kwargs) -> List[Dict[Any, int]]:
    """
    Detect communities in each snapshot of a temporal network.
    Returns a list of community maps (dict node -> community label) per snapshot.
    """
    if not HAS_NETWORKX:
        raise ImportError("NetworkX required for community detection")
    communities = []
    for G in tn.snapshots:
        if G is None or G.number_of_nodes() == 0:
            communities.append({})
            continue
        if method == 'louvain':
            try:
                from community import community_louvain
                comm = community_louvain.best_partition(G.to_undirected())
            except ImportError:
                # fallback to greedy modularity
                from networkx.algorithms import community
                comp = community.greedy_modularity_communities(G.to_undirected())
                comm = {node: i for i, c in enumerate(comp) for node in c}
        elif method == 'spectral':
            from networkx.algorithms import community
            # Not directly implemented; fallback to label propagation
            comp = community.label_propagation_communities(G.to_undirected())
            comm = {node: i for i, c in enumerate(comp) for node in c}
        else:
            raise ValueError(f"Unknown community method: {method}")
        communities.append(comm)
    return communities


def community_persistence(communities: List[Dict[Any, int]]) -> Dict[Any, List[int]]:
    """
    Track each node's community assignment over time.
    Returns dict node -> list of community labels (same length as number of snapshots).
    """
    if not communities:
        return {}
    nodes = set(communities[0].keys())
    persistence = {node: [] for node in nodes}
    for comm in communities:
        for node in nodes:
            persistence[node].append(comm.get(node, -1))
    return persistence


def community_transitions(communities: List[Dict[Any, int]]) -> Dict[Any, List[Tuple[int, int]]]:
    """
    For each node, list of times (snapshot indices) when its community changed.
    Returns dict node -> list of (from_community, to_community, time_index) ? Simpler: list of time indices.
    """
    transitions = defaultdict(list)
    for i in range(1, len(communities)):
        prev = communities[i-1]
        curr = communities[i]
        for node in set(prev.keys()) | set(curr.keys()):
            if prev.get(node, -1) != curr.get(node, -1):
                transitions[node].append(i)
    return dict(transitions)


# ============================================================================
# EVOLUTION OF GRAPH STATISTICS
# ============================================================================

def compute_statistics_series(tn: TemporalNetwork, stats_funcs: Dict[str, Callable]) -> Dict[str, List[float]]:
    """
    Compute a time series of graph statistics for each snapshot.
    stats_funcs: dict mapping name -> function(graph) -> float.
    Returns dict name -> list of values (aligned with timestamps).
    """
    series = {name: [] for name in stats_funcs}
    for G in tn.snapshots:
        for name, func in stats_funcs.items():
            try:
                val = func(G)
            except Exception:
                val = float('nan')
            series[name].append(val)
    return series


def detect_change_points(series: List[float], method: str = 'ruptures', **kwargs) -> List[int]:
    """
    Detect change points in a time series.
    Returns list of indices where changes occur (end of segments).
    """
    if method == 'ruptures' and HAS_RUPTURES:
        algo = rpt.Pelt(model="rbf").fit(np.array(series).reshape(-1,1))
        result = algo.predict(pen=kwargs.get('pen', 10))
        # result includes last index; often we remove it
        return [idx for idx in result if idx < len(series)]
    elif method == 'statsmodels':
        # Use ADF test or simple threshold on differences
        if not HAS_STATSMODELS:
            raise ImportError("statsmodels required for this method")
        changes = []
        # Simple: points where absolute difference exceeds threshold
        threshold = kwargs.get('threshold', 2 * np.std(series))
        for i in range(1, len(series)):
            if abs(series[i] - series[i-1]) > threshold:
                changes.append(i)
        return changes
    else:
        raise ValueError(f"Unknown change point method: {method}")


# ============================================================================
# TEMPORAL MOTIFS (multiple types)
# ============================================================================

def temporal_motif_count(tg: TemporalGraph, motif_type: str = 'triangle_concurrent', window: float = 1.0) -> int:
    """
    Count various temporal motifs in a TemporalGraph.
    Supported motif types:
        - 'triangle_concurrent': three edges forming a triangle within a time window.
        - 'star_concurrent': a node connected to two other nodes within window (degree-2 star).
        - 'directed_triangle': for directed graphs, a directed cycle of three edges within window.
        - 'path_consecutive': a path of length 2 (u-v, v-w) where the two edges occur within window.
        - 'burst': multiple occurrences of the same edge within window (count as 1 per edge?).
    """
    if motif_type == 'triangle_concurrent':
        # Find all unordered triples of nodes
        nodes = list(tg.nodes)
        count = 0
        for i, j, k in combinations(nodes, 3):
            edges = [(i, j), (j, k), (i, k)]
            times = []
            for u, v in edges:
                key = (u, v) if tg.directed else (min(u, v), max(u, v))
                if key in tg.edge_timestamps and tg.edge_timestamps[key]:
                    # take the earliest timestamp in the window? We'll check any timestamp within window.
                    # For triangle_concurrent, we need all three edges to have at least one timestamp within window.
                    # We'll check if there exists a triple of timestamps (one per edge) all within window.
                    # Simple: collect all timestamps for each edge, then see if we can pick one from each such that max-min <= window.
                    # This is expensive. We'll approximate by checking if the earliest timestamp of each edge is within window of each other.
                    # For simplicity, we'll just check the min of each edge and see if range <= window.
                    tmin = min(tg.edge_timestamps[key])
                    times.append(tmin)
                else:
                    times.append(None)
            if None in times:
                continue
            if max(times) - min(times) <= window:
                count += 1
        return count

    elif motif_type == 'star_concurrent':
        # For each node as center, count pairs of neighbors where interactions with both occur within window.
        count = 0
        for center in tg.nodes:
            neighbors = []
            for (u, v), times in tg.edge_timestamps.items():
                if u == center:
                    neighbors.append((v, times))
                elif v == center and not tg.directed:
                    neighbors.append((u, times))
            # For each pair of neighbors, check if there exist timestamps within window
            for (n1, t1), (n2, t2) in combinations(neighbors, 2):
                # find any t1_i, t2_j such that |t1_i - t2_j| <= window
                found = False
                for tt1 in t1:
                    for tt2 in t2:
                        if abs(tt1 - tt2) <= window:
                            count += 1
                            found = True
                            break
                    if found:
                        break
        return count

    elif motif_type == 'directed_triangle':
        if not tg.directed:
            return 0
        # Directed triangle: u->v, v->w, w->u within window.
        nodes = list(tg.nodes)
        count = 0
        for u, v, w in combinations(nodes, 3):
            edges = [(u, v), (v, w), (w, u)]
            times = []
            for u1, v1 in edges:
                key = (u1, v1)
                if key in tg.edge_timestamps and tg.edge_timestamps[key]:
                    tmin = min(tg.edge_timestamps[key])
                    times.append(tmin)
                else:
                    times.append(None)
            if None in times:
                continue
            if max(times) - min(times) <= window:
                count += 1
        return count

    elif motif_type == 'path_consecutive':
        # Path of length 2: u->v and v->w (if directed) or u-v and v-w (undirected) within window.
        count = 0
        for (u, v), times_uv in tg.edge_timestamps.items():
            # Find neighbors of v (excluding u)
            for (x, y), times_xy in tg.edge_timestamps.items():
                if (x == v or y == v) and (x, y) != (u, v) and (x, y) != (v, u):
                    # Determine the other endpoint w
                    if x == v:
                        w = y
                    else:
                        w = x
                    if w == u:
                        continue
                    # Check if any timestamp pair within window
                    for t1 in times_uv:
                        for t2 in times_xy:
                            if abs(t1 - t2) <= window:
                                count += 1
                                break
                        else:
                            continue
                        break
        return count

    elif motif_type == 'burst':
        # Count edges that have multiple occurrences within a sliding window of size window.
        # For each edge, count number of windows that contain at least two interactions.
        # Simplified: just check if any two timestamps on the same edge are within window.
        count = 0
        for times in tg.edge_timestamps.values():
            times_sorted = sorted(times)
            for i in range(len(times_sorted)):
                for j in range(i+1, len(times_sorted)):
                    if times_sorted[j] - times_sorted[i] <= window:
                        count += 1
                        break  # count each edge only once
                else:
                    continue
                break
        return count

    else:
        raise NotImplementedError(f"Motif type {motif_type} not implemented")


def temporal_motif_significance(tg: TemporalGraph, motif_type: str, n_random: int = 100,
                                window: float = 1.0) -> Dict[str, float]:
    """
    Compute Z‑score and p‑value for temporal motif by comparing with random
    time reshuffling (preserving edge occurrences but shuffling timestamps globally).
    """
    observed = temporal_motif_count(tg, motif_type, window=window)
    random_counts = []
    # Shuffle timestamps within each edge (preserve number of occurrences per edge)
    all_times = []
    for times in tg.edge_timestamps.values():
        all_times.extend(times)
    for _ in range(n_random):
        shuffled = TemporalGraph(directed=tg.directed, weighted=tg.weighted)
        shuffled.nodes = tg.nodes.copy()
        for (u, v), times in tg.edge_timestamps.items():
            # Randomly sample len(times) timestamps from all_times without replacement
            # (to preserve distribution but break temporal correlation)
            new_times = list(np.random.choice(all_times, size=len(times), replace=False))
            shuffled.edge_timestamps[(u, v)] = new_times
        random_counts.append(temporal_motif_count(shuffled, motif_type, window=window))
    mean = np.mean(random_counts)
    std = np.std(random_counts)
    if std == 0:
        z = 0.0
        p = 1.0
    else:
        z = (observed - mean) / std
        if HAS_SCIPY_STATS:
            p = 2 * (1 - norm.cdf(abs(z)))  # two‑tailed
        else:
            # approximate p from empirical distribution
            p = np.mean(np.abs(np.array(random_counts) - mean) >= abs(observed - mean))
    return {'observed': observed, 'mean': mean, 'std': std, 'z_score': z, 'p_value': p}


# ============================================================================
# FORECASTING
# ============================================================================

def forecast_next_snapshot(series: List[float], steps: int = 1, method: str = 'arima', **kwargs) -> np.ndarray:
    """
    Forecast future values of a time series using ARIMA or simple linear extrapolation.
    """
    if method == 'arima':
        if not HAS_STATSMODELS:
            raise ImportError("statsmodels required for ARIMA")
        order = kwargs.get('order', (1, 0, 0))
        model = ARIMA(series, order=order)
        fit = model.fit()
        forecast = fit.forecast(steps=steps)
        return forecast
    elif method == 'linear':
        # Simple linear regression on index
        x = np.arange(len(series))
        y = np.array(series)
        coeffs = np.polyfit(x, y, 1)
        poly = np.poly1d(coeffs)
        return poly(np.arange(len(series), len(series)+steps))
    else:
        raise ValueError(f"Unknown forecast method: {method}")


def forecast_graph(tn: TemporalNetwork, steps: int = 1,
                   method: str = 'arima', feature: str = 'density') -> List[float]:
    """
    Forecast a single graph statistic. Could be extended to forecast entire graph structure.
    """
    # Compute series of chosen feature
    if feature == 'density':
        if not HAS_NETWORKX:
            raise ImportError("NetworkX required for density computation")
        def density(G):
            n = G.number_of_nodes()
            if n <= 1:
                return 0.0
            m = G.number_of_edges()
            if G.is_directed():
                return m / (n * (n-1))
            else:
                return 2*m / (n * (n-1))
        series = [density(G) for G in tn.snapshots]
    elif feature == 'num_nodes':
        series = [G.number_of_nodes() for G in tn.snapshots]
    elif feature == 'num_edges':
        series = [G.number_of_edges() for G in tn.snapshots]
    else:
        raise ValueError(f"Unknown feature: {feature}")

    return forecast_next_snapshot(series, steps, method)


# ============================================================================
# INTEGRATION WITH ULTIMATE RELATION
# ============================================================================

# Define a minimal protocol for UltimateRelation (duck typing)
class UltimateRelationProtocol:
    """Minimal interface expected for UltimateRelation objects."""
    source_id: Any
    target_id: Any
    temporal_evolution: List[Tuple[float, float]]


def relation_temporal_series(relation: UltimateRelationProtocol) -> List[Tuple[float, float]]:
    """
    Extract the temporal evolution of a single relation as a time‑weight series.
    Assumes relation.temporal_evolution is list of (time, weight).
    """
    return relation.temporal_evolution


def aggregate_relations_temporal(relations: List[UltimateRelationProtocol],
                                 start: float, end: float) -> nx.Graph:
    """
    Build a graph from all relations active in [start, end].
    """
    if not HAS_NETWORKX:
        raise ImportError("NetworkX required")
    G = nx.Graph()
    for rel in relations:
        for t, w in rel.temporal_evolution:
            if start <= t <= end:
                G.add_edge(rel.source_id, rel.target_id, weight=w)
                break  # only need one timestamp within interval to add edge
    return G


# ============================================================================
# VISUALIZATION
# ============================================================================

def plot_statistics_series(series: Dict[str, List[float]], timestamps: List[float],
                           filename: Optional[str] = None):
    """
    Plot multiple time series.
    """
    if not HAS_MATPLOTLIB:
        logger.warning("Matplotlib not available – cannot plot")
        return
    plt.figure(figsize=(12, 6))
    for name, vals in series.items():
        plt.plot(timestamps, vals, label=name, marker='o')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title('Graph Statistics Over Time')
    plt.legend()
    if filename:
        plt.savefig(filename)
    else:
        plt.show()
    plt.close()


def plot_community_evolution(persistence: Dict[Any, List[int]], timestamps: List[float],
                             filename: Optional[str] = None):
    """
    Plot community assignments as a stacked area chart (simplified).
    """
    if not HAS_MATPLOTLIB:
        return
    # Determine number of communities
    all_comms = set()
    for node, labels in persistence.items():
        all_comms.update(labels)
    all_comms.discard(-1)
    if not all_comms:
        return
    comm_ids = sorted(all_comms)
    # Count nodes per community per time
    n_times = len(timestamps)
    counts = {c: [0]*n_times for c in comm_ids}
    for node, labels in persistence.items():
        for t, lab in enumerate(labels):
            if lab in counts:
                counts[lab][t] += 1
    plt.figure(figsize=(12, 6))
    bottom = np.zeros(n_times)
    for c in comm_ids:
        plt.bar(timestamps, counts[c], bottom=bottom, label=f'Comm {c}')
        bottom += np.array(counts[c])
    plt.xlabel('Time')
    plt.ylabel('Number of nodes')
    plt.title('Community Evolution')
    plt.legend()
    if filename:
        plt.savefig(filename)
    else:
        plt.show()
    plt.close()


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Run a simple demo with synthetic data."""
    if not HAS_NETWORKX or not HAS_MATPLOTLIB:
        print("NetworkX and Matplotlib required for demo.")
        return

    # Create a temporal network with 3 snapshots
    snapshots = []
    G1 = nx.erdos_renyi_graph(10, 0.2, seed=1)
    G2 = nx.erdos_renyi_graph(10, 0.3, seed=2)
    G3 = nx.erdos_renyi_graph(10, 0.4, seed=3)
    snapshots = [G1, G2, G3]
    timestamps = [0.0, 1.0, 2.0]
    tn = TemporalNetwork(snapshots, timestamps)

    # Compute statistics series
    if HAS_STATSMODELS:
        series = compute_statistics_series(tn, {
            'num_nodes': lambda G: G.number_of_nodes(),
            'num_edges': lambda G: G.number_of_edges(),
            'density': lambda G: nx.density(G)
        })
        plot_statistics_series(series, timestamps, filename="demo_stats.png")

        # Detect change points (should be at 1,2)
        changes = detect_change_points(series['num_edges'], method='statsmodels', threshold=5)
        print("Change points at indices:", changes)

        # Forecast next step
        forecast = forecast_next_snapshot(series['num_edges'], steps=2, method='linear')
        print("Forecast next 2 num_edges:", forecast)

    # Community evolution
    comms = dynamic_communities(tn, method='louvain')
    pers = community_persistence(comms)
    plot_community_evolution(pers, timestamps, filename="demo_communities.png")
    trans = community_transitions(comms)
    print("Community transitions:", trans)

    # TemporalGraph demo
    tg = TemporalGraph()
    tg.add_interaction(0, 1, 0.1)
    tg.add_interaction(1, 2, 0.2)
    tg.add_interaction(0, 2, 1.5)
    tg.add_interaction(0, 1, 0.5)  # burst on edge (0,1)
    # Test different motif types
    for motif in ['triangle_concurrent', 'star_concurrent', 'path_consecutive', 'burst']:
        count = temporal_motif_count(tg, motif_type=motif, window=1.0)
        print(f"Motif {motif}: {count}")
    # Significance test (may be slow)
    sig = temporal_motif_significance(tg, 'triangle_concurrent', n_random=50, window=1.0)
    print("Significance:", sig)


if __name__ == "__main__":
    demo()