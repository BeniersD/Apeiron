"""
ATOMICITY VISUALISATIONS – STATIC PLOTS FOR ATOMICITY ANALYSIS
===============================================================
This module provides static visualisation functions for atomicity data,
commonly used in Layer 2 (Relational Dynamics) to display atomicity weights,
distributions, comparisons, and network‑based atomicity.

Functions include:
- plot_atomicity_heatmap: 2D heatmap of atomicity values (matrix or per node).
- plot_atomicity_distribution: histogram or boxplot of atomicity values.
- plot_atomicity_comparison: bar chart comparing atomicity across groups.
- plot_atomicity_timeline: line plot of atomicity over time.
- plot_atomicity_network: graph visualisation with nodes coloured by atomicity.

NEW LAYER 1 INTEGRATION FUNCTIONS:
- atomicity_from_registry: Extract atomicity scores from a Layer 1 registry.
- plot_atomicity_distribution_from_registry: Plot distribution of atomicity in a registry.
- plot_atomicity_comparison_from_registry: Compare atomicity across groups (e.g., observer).
- plot_atomicity_network_from_registry: Build a graph from a registry and colour nodes by atomicity.
- plot_atomicity_timeline_from_registry: Plot atomicity over temporal phase.

All functions gracefully degrade if optional plotting libraries (matplotlib, seaborn, plotly, pandas)
are missing. They accept both matplotlib and plotly backends (where applicable) via a `backend` parameter.
"""

import logging
from typing import Optional, List, Dict, Any, Union, Tuple, Callable
import numpy as np

# Optional libraries – handled gracefully
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    sns = None

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    go = None
    px = None

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

# For Layer 1 integration we may need to import UltimateObservable
# To avoid circular imports we import only when needed, but we can also use duck typing.
try:
    from apeiron.layers.layer01_foundational.irreducible_unit import UltimateObservable
    HAS_ULTIMATE_OBS = True
except ImportError:
    HAS_ULTIMATE_OBS = False

logger = logging.getLogger(__name__)


# ============================================================================
# Helper functions
# ============================================================================

def _check_backend(backend: str, allow_plotly: bool = True) -> bool:
    """
    Check if the requested backend is available.
    Returns True if available, otherwise logs a warning and returns False.
    """
    if backend == 'matplotlib':
        if not HAS_MATPLOTLIB:
            logger.warning("matplotlib is not installed – cannot use matplotlib backend.")
            return False
        return True
    elif backend == 'plotly' and allow_plotly:
        if not HAS_PLOTLY:
            logger.warning("plotly is not installed – cannot use plotly backend.")
            return False
        return True
    else:
        logger.warning(f"Unknown backend '{backend}' or backend not allowed.")
        return False


def _ensure_atomicity_array(atomicity: Union[np.ndarray, List[float], Dict]) -> np.ndarray:
    """Convert various input types to a 1D numpy array of floats."""
    if isinstance(atomicity, dict):
        # Assume dict maps node IDs to atomicity; return values as array.
        return np.array(list(atomicity.values()), dtype=float)
    return np.asarray(atomicity, dtype=float).flatten()


# ============================================================================
# Main visualisation functions (unchanged, but improved pandas fallback)
# ============================================================================

def plot_atomicity_heatmap(
    atomicity_matrix: np.ndarray,
    x_labels: Optional[List[str]] = None,
    y_labels: Optional[List[str]] = None,
    title: str = "Atomicity Heatmap",
    cmap: str = "viridis",
    backend: str = "matplotlib",
    show: bool = True,
    filename: Optional[str] = None,
    figsize: Tuple[int, int] = (8, 6)
) -> Optional[Any]:
    """
    Plot a heatmap of atomicity values (e.g., node‑by‑node or node‑by‑sample).

    Args:
        atomicity_matrix: 2D numpy array of atomicity values.
        x_labels: Optional list of labels for the x‑axis.
        y_labels: Optional list of labels for the y‑axis.
        title: Title of the plot.
        cmap: Colormap name (matplotlib) or colorscale (plotly).
        backend: 'matplotlib' or 'plotly'.
        show: Whether to display the plot immediately.
        filename: If given, save the plot to this file (format inferred from extension).
        figsize: Figure size (only for matplotlib).

    Returns:
        If backend is 'plotly', returns the figure object; otherwise None.
    """
    if not _check_backend(backend):
        return None

    if atomicity_matrix.ndim != 2:
        raise ValueError("atomicity_matrix must be a 2D array")

    if backend == 'matplotlib':
        if not HAS_MATPLOTLIB:
            return None
        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(atomicity_matrix, cmap=cmap, aspect='auto', interpolation='nearest')
        plt.colorbar(im, ax=ax, label='Atomicity')
        ax.set_title(title)
        ax.set_xlabel('Samples / Columns')
        ax.set_ylabel('Nodes / Rows')
        if x_labels:
            ax.set_xticks(range(len(x_labels)))
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
        if y_labels:
            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels(y_labels)
        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        if show:
            plt.show()
        else:
            plt.close(fig)
        return None

    elif backend == 'plotly':
        if not HAS_PLOTLY:
            return None
        fig = go.Figure(data=go.Heatmap(
            z=atomicity_matrix,
            x=x_labels,
            y=y_labels,
            colorscale=cmap,
            colorbar=dict(title='Atomicity')
        ))
        fig.update_layout(
            title=title,
            xaxis_title='Samples / Columns',
            yaxis_title='Nodes / Rows'
        )
        if filename:
            fig.write_image(filename) if filename.endswith(('.png', '.jpg', '.pdf')) else fig.write_html(filename)
        if show:
            fig.show()
        return fig

    return None


def plot_atomicity_distribution(
    atomicity: Union[np.ndarray, List[float], Dict],
    plot_type: str = 'hist',
    bins: int = 20,
    title: str = "Atomicity Distribution",
    xlabel: str = "Atomicity",
    ylabel: str = "Frequency",
    backend: str = "matplotlib",
    show: bool = True,
    filename: Optional[str] = None,
    figsize: Tuple[int, int] = (8, 6)
) -> Optional[Any]:
    """
    Plot the distribution of atomicity values (histogram or boxplot).

    Args:
        atomicity: 1D array, list, or dict of atomicity values.
        plot_type: 'hist' for histogram, 'box' for boxplot.
        bins: Number of bins (for histogram).
        title, xlabel, ylabel: Plot labels.
        backend: 'matplotlib' or 'plotly'.
        show, filename, figsize: As in heatmap.

    Returns:
        Plotly figure object if backend='plotly', else None.
    """
    if not _check_backend(backend):
        return None

    data = _ensure_atomicity_array(atomicity)

    if backend == 'matplotlib':
        if not HAS_MATPLOTLIB:
            return None
        fig, ax = plt.subplots(figsize=figsize)
        if plot_type == 'hist':
            ax.hist(data, bins=bins, edgecolor='black', alpha=0.7)
            ax.set_ylabel(ylabel)
        elif plot_type == 'box':
            ax.boxplot(data, vert=True)
            ax.set_ylabel('Atomicity')
            ax.set_xticks([1])
            ax.set_xticklabels(['Atomicity'])
        else:
            raise ValueError("plot_type must be 'hist' or 'box'")
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        if show:
            plt.show()
        else:
            plt.close(fig)
        return None

    elif backend == 'plotly':
        if not HAS_PLOTLY:
            return None
        if plot_type == 'hist':
            fig = px.histogram(x=data, nbins=bins, title=title, labels={'x': xlabel, 'y': ylabel})
        elif plot_type == 'box':
            fig = px.box(y=data, title=title, labels={'y': 'Atomicity'})
            fig.update_xaxes(title_text='')
        else:
            raise ValueError("plot_type must be 'hist' or 'box'")
        if filename:
            fig.write_image(filename) if filename.endswith(('.png', '.jpg', '.pdf')) else fig.write_html(filename)
        if show:
            fig.show()
        return fig

    return None


def plot_atomicity_comparison(
    group_data: Dict[str, Union[np.ndarray, List[float]]],
    title: str = "Atomicity Comparison",
    ylabel: str = "Atomicity",
    backend: str = "matplotlib",
    show: bool = True,
    filename: Optional[str] = None,
    figsize: Tuple[int, int] = (8, 6)
) -> Optional[Any]:
    """
    Compare atomicity across groups using a bar chart (mean ± std) or box plots.

    Args:
        group_data: Dictionary mapping group names to arrays/lists of atomicity values.
        title, ylabel: Plot labels.
        backend, show, filename, figsize: As before.

    Returns:
        Plotly figure object if backend='plotly', else None.
    """
    if not _check_backend(backend):
        return None

    # Convert each group to numpy array
    groups = {name: _ensure_atomicity_array(vals) for name, vals in group_data.items()}
    group_names = list(groups.keys())
    means = [np.mean(groups[name]) for name in group_names]
    stds = [np.std(groups[name]) for name in group_names]

    if backend == 'matplotlib':
        if not HAS_MATPLOTLIB:
            return None
        fig, ax = plt.subplots(figsize=figsize)
        x_pos = np.arange(len(group_names))
        ax.bar(x_pos, means, yerr=stds, align='center', alpha=0.7, capsize=5)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(group_names, rotation=45, ha='right')
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        if show:
            plt.show()
        else:
            plt.close(fig)
        return None

    elif backend == 'plotly':
        if not HAS_PLOTLY:
            return None

        # Use plotly.graph_objects to avoid pandas dependency
        fig = go.Figure()
        for i, (name, vals) in enumerate(groups.items()):
            # Create a box trace for each group
            fig.add_trace(go.Box(y=vals, name=name, boxmean='sd'))
        fig.update_layout(title=title, yaxis_title=ylabel)
        if filename:
            fig.write_image(filename) if filename.endswith(('.png', '.jpg', '.pdf')) else fig.write_html(filename)
        if show:
            fig.show()
        return fig

    return None


def plot_atomicity_timeline(
    times: np.ndarray,
    atomicity_series: Union[np.ndarray, List[float]],
    title: str = "Atomicity Over Time",
    xlabel: str = "Time",
    ylabel: str = "Atomicity",
    backend: str = "matplotlib",
    show: bool = True,
    filename: Optional[str] = None,
    figsize: Tuple[int, int] = (8, 6)
) -> Optional[Any]:
    """
    Plot atomicity as a function of time (line plot).

    Args:
        times: 1D array of time points.
        atomicity_series: 1D array of atomicity values at each time point.
        title, xlabel, ylabel: Plot labels.
        backend, show, filename, figsize: As before.

    Returns:
        Plotly figure object if backend='plotly', else None.
    """
    if not _check_backend(backend):
        return None

    times = np.asarray(times).flatten()
    values = _ensure_atomicity_array(atomicity_series)

    if len(times) != len(values):
        raise ValueError("times and atomicity_series must have the same length")

    if backend == 'matplotlib':
        if not HAS_MATPLOTLIB:
            return None
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(times, values, marker='o', linestyle='-')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        if show:
            plt.show()
        else:
            plt.close(fig)
        return None

    elif backend == 'plotly':
        if not HAS_PLOTLY:
            return None
        fig = px.line(x=times, y=values, title=title, markers=True)
        fig.update_xaxes(title=xlabel)
        fig.update_yaxes(title=ylabel)
        if filename:
            fig.write_image(filename) if filename.endswith(('.png', '.jpg', '.pdf')) else fig.write_html(filename)
        if show:
            fig.show()
        return fig

    return None


def plot_atomicity_network(
    graph: 'nx.Graph',
    atomicity: Union[np.ndarray, Dict],
    title: str = "Network Coloured by Atomicity",
    node_size: int = 300,
    cmap: str = "viridis",
    backend: str = "matplotlib",
    show: bool = True,
    filename: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 8)
) -> Optional[Any]:
    """
    Draw a graph with nodes coloured according to atomicity values.

    Args:
        graph: A NetworkX graph.
        atomicity: Array or dict mapping node to atomicity. If array, order must match graph.nodes().
        title: Title of the plot.
        node_size: Size of nodes.
        cmap: Colormap (matplotlib) or colorscale (plotly).
        backend: 'matplotlib' or 'plotly'.
        show, filename, figsize: As before.

    Returns:
        Plotly figure object if backend='plotly', else None.
    """
    if not _check_backend(backend, allow_plotly=True):
        return None
    if not HAS_NETWORKX:
        logger.warning("networkx is not installed – cannot plot network.")
        return None

    # Map atomicity to nodes in the same order as graph.nodes()
    nodes = list(graph.nodes())
    if isinstance(atomicity, dict):
        values = np.array([atomicity.get(node, 0.0) for node in nodes])
    else:
        values = _ensure_atomicity_array(atomicity)
        if len(values) != len(nodes):
            raise ValueError("Length of atomicity array must match number of nodes")

    if backend == 'matplotlib':
        if not HAS_MATPLOTLIB:
            return None
        pos = nx.spring_layout(graph, seed=42)  # deterministic layout
        fig, ax = plt.subplots(figsize=figsize)
        sc = nx.draw_networkx_nodes(graph, pos, node_color=values, cmap=cmap, node_size=node_size, ax=ax)
        nx.draw_networkx_edges(graph, pos, alpha=0.5, ax=ax)
        nx.draw_networkx_labels(graph, pos, font_size=8, ax=ax)
        plt.colorbar(sc, ax=ax, label='Atomicity')
        ax.set_title(title)
        ax.axis('off')
        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        if show:
            plt.show()
        else:
            plt.close(fig)
        return None

    elif backend == 'plotly':
        if not HAS_PLOTLY:
            return None
        # Use plotly's network graph capabilities (scatter for nodes, lines for edges)
        pos = nx.spring_layout(graph, seed=42)
        edge_trace = []
        for u, v in graph.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_trace.append(go.Scatter(x=[x0, x1, None], y=[y0, y1, None],
                                         mode='lines', line=dict(width=1, color='#888'), hoverinfo='none'))
        node_x = [pos[node][0] for node in nodes]
        node_y = [pos[node][1] for node in nodes]
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=nodes,
            textposition="top center",
            hoverinfo='text',
            marker=dict(
                size=node_size/10,
                color=values,
                colorscale=cmap,
                colorbar=dict(title='Atomicity'),
                showscale=True
            )
        )
        fig = go.Figure(data=edge_trace + [node_trace],
                        layout=go.Layout(
                            title=title,
                            showlegend=False,
                            hovermode='closest',
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                        ))
        if filename:
            fig.write_image(filename) if filename.endswith(('.png', '.jpg', '.pdf')) else fig.write_html(filename)
        if show:
            fig.show()
        return fig

    return None


# ============================================================================
# NEW: Layer 1 integration helper functions
# ============================================================================

def atomicity_from_registry(
    registry: Dict[str, Any],
    combined: bool = True,
    weights: Optional[Dict[str, float]] = None,
    observer: Optional[str] = None
) -> Tuple[np.ndarray, List[str]]:
    """
    Extract atomicity scores from a Layer 1 registry (dictionary mapping ID to UltimateObservable).
    Returns a 1D array of atomicity scores and a list of IDs in the same order.

    Args:
        registry: dict mapping observable ID to UltimateObservable instance.
        combined: whether to return the combined atomicity score (True) or a dictionary of scores per framework (False).
        weights: custom weights for combination (passed to get_atomicity_score).
        observer: observer perspective for observer‑dependent atomicity.

    Returns:
        (atomicity_array, observable_ids) where atomicity_array is a 1D numpy array of scores.
        If combined=False, returns a list of dicts (one per observable) instead of a single array.
    """
    ids = list(registry.keys())
    if not combined:
        # Return list of dicts per observable
        scores = []
        for obs_id in ids:
            obs = registry[obs_id]
            if hasattr(obs, 'get_atomicity_score'):
                sc = obs.get_atomicity_score(combined=False, weights=weights, observer=observer)
            else:
                # Fallback: assume obs.atomicity is a dict
                sc = getattr(obs, 'atomicity', {})
            scores.append(sc)
        return scores, ids
    else:
        # Return single array of combined scores
        scores = []
        for obs_id in ids:
            obs = registry[obs_id]
            if hasattr(obs, 'get_atomicity_score'):
                sc = obs.get_atomicity_score(combined=True, weights=weights, observer=observer)
            else:
                # Fallback: look for atomicity_score attribute
                sc = getattr(obs, 'atomicity_score', 0.0)
            scores.append(sc)
        return np.array(scores), ids


def plot_atomicity_distribution_from_registry(
    registry: Dict[str, Any],
    combined: bool = True,
    weights: Optional[Dict[str, float]] = None,
    observer: Optional[str] = None,
    **kwargs
) -> Optional[Any]:
    """
    Plot the distribution of atomicity scores for all observables in a Layer 1 registry.

    Args:
        registry: dict mapping ID to UltimateObservable.
        combined: if True, use combined score; if False, use a specific framework (see `framework` kwarg).
        weights: custom weights for combination.
        observer: observer perspective for atomicity calculation.
        **kwargs: passed to plot_atomicity_distribution (e.g., plot_type, bins, title, backend).

    Returns:
        See plot_atomicity_distribution.
    """
    scores, _ = atomicity_from_registry(registry, combined=combined, weights=weights, observer=observer)
    if not combined:
        # If we have a list of dicts, we need to pick one framework. We'll assume user wants a specific framework.
        # For simplicity, if a 'framework' keyword is given, use that; otherwise raise.
        framework = kwargs.pop('framework', None)
        if framework is None:
            raise ValueError("When combined=False, you must provide 'framework' keyword argument to select which framework to plot.")
        # Convert list of dicts to list of scores for that framework
        scores = [sc.get(framework, 0.0) for sc in scores]
        scores = np.array(scores)
    # Call the generic plotting function
    return plot_atomicity_distribution(scores, **kwargs)


def plot_atomicity_comparison_from_registry(
    registry: Dict[str, Any],
    group_by: str = 'observer_perspective',
    combined: bool = True,
    weights: Optional[Dict[str, float]] = None,
    observer: Optional[str] = None,
    **kwargs
) -> Optional[Any]:
    """
    Compare atomicity across groups of observables in a registry.

    Args:
        registry: dict mapping ID to UltimateObservable.
        group_by: attribute name to group by (e.g., 'observer_perspective', 'observability_type').
        combined: if True, use combined score; if False, use a specific framework (see `framework` kwarg).
        weights: custom weights for combination.
        observer: observer perspective for atomicity calculation.
        **kwargs: passed to plot_atomicity_comparison.

    Returns:
        See plot_atomicity_comparison.
    """
    group_data = {}
    for obs_id, obs in registry.items():
        if hasattr(obs, group_by):
            group = getattr(obs, group_by)
        else:
            group = 'unknown'
        # Get atomicity score
        if combined:
            score = obs.get_atomicity_score(combined=True, weights=weights, observer=observer)
        else:
            # Use a specific framework if provided
            framework = kwargs.pop('framework', None)
            if framework is None:
                raise ValueError("When combined=False, you must provide 'framework' keyword argument.")
            score = obs.get_atomicity_score(combined=False, weights=weights, observer=observer).get(framework, 0.0)
        group_data.setdefault(str(group), []).append(score)
    return plot_atomicity_comparison(group_data, **kwargs)


def plot_atomicity_network_from_registry(
    registry: Dict[str, Any],
    similarity_threshold: float = 0.1,
    similarity_func: Optional[Callable[[Any, Any], float]] = None,
    weight_by_atomicity: bool = True,
    node_size: int = 300,
    cmap: str = "viridis",
    backend: str = "matplotlib",
    show: bool = True,
    filename: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 8),
    **kwargs
) -> Optional[Any]:
    """
    Build a graph from a Layer 1 registry and plot it with nodes coloured by atomicity.

    The graph is built using a similarity measure (default combines qualitative dimensions
    and relational embeddings). Edges are created if similarity exceeds the threshold.

    Args:
        registry: dict mapping ID to UltimateObservable.
        similarity_threshold: minimum similarity to create an edge.
        similarity_func: custom similarity function; if None, uses a default.
        weight_by_atomicity: if True, store atomicity scores as node attributes.
        node_size, cmap, backend, show, filename, figsize: passed to plot_atomicity_network.
        **kwargs: additional arguments passed to plot_atomicity_network.

    Returns:
        See plot_atomicity_network.
    """
    if not HAS_NETWORKX:
        logger.warning("NetworkX not installed – cannot create graph.")
        return None

    # Build graph using a simple method (we could use SpectralGraphAnalysis.from_layer1_registry,
    # but we want to avoid a circular import. We'll implement a simple version here.)
    G = nx.Graph()
    ids = list(registry.keys())
    for oid in ids:
        G.add_node(oid)
        if weight_by_atomicity and hasattr(registry[oid], 'atomicity_score'):
            G.nodes[oid]['atomicity'] = registry[oid].atomicity_score

    # Default similarity function (mimics SpectralGraphAnalysis._default_similarity)
    def default_sim(obs1, obs2):
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

    sim_func = similarity_func if similarity_func is not None else default_sim

    # Add edges
    for i, id1 in enumerate(ids):
        for j in range(i+1, len(ids)):
            id2 = ids[j]
            sim = sim_func(registry[id1], registry[id2])
            if sim >= similarity_threshold:
                G.add_edge(id1, id2, weight=sim)

    # Get atomicity scores for nodes (in the order of graph.nodes)
    atomicity_dict = {node: G.nodes[node].get('atomicity', 0.0) for node in G.nodes()}
    return plot_atomicity_network(G, atomicity_dict, node_size=node_size, cmap=cmap,
                                   backend=backend, show=show, filename=filename,
                                   figsize=figsize, **kwargs)


def plot_atomicity_timeline_from_registry(
    registry: Dict[str, Any],
    phase_key: str = 'temporal_phase',
    binning: str = 'phase',   # 'phase' for exact phase, or 'bins' for grouped
    bins: Optional[int] = None,
    combined: bool = True,
    weights: Optional[Dict[str, float]] = None,
    observer: Optional[str] = None,
    **kwargs
) -> Optional[Any]:
    """
    Plot the evolution of atomicity over temporal phase.

    Args:
        registry: dict mapping ID to UltimateObservable.
        phase_key: attribute name for the temporal phase (default 'temporal_phase').
        binning: 'phase' to use exact phases (sorted), 'bins' to bin into discrete windows.
        bins: number of bins if binning='bins'.
        combined: if True, use combined score; if False, use a specific framework (see `framework` kwarg).
        weights: custom weights for combination.
        observer: observer perspective for atomicity calculation.
        **kwargs: passed to plot_atomicity_timeline (e.g., title, xlabel, ylabel, backend).

    Returns:
        See plot_atomicity_timeline.
    """
    # Collect (phase, atomicity) pairs
    phases = []
    scores = []
    framework = kwargs.pop('framework', None) if not combined else None

    for obs_id, obs in registry.items():
        if hasattr(obs, phase_key):
            phase = getattr(obs, phase_key)
        else:
            # If phase is missing, skip or assign 0
            continue
        if combined:
            score = obs.get_atomicity_score(combined=True, weights=weights, observer=observer)
        else:
            if framework is None:
                raise ValueError("When combined=False, you must provide 'framework' keyword argument.")
            score = obs.get_atomicity_score(combined=False, weights=weights, observer=observer).get(framework, 0.0)
        phases.append(phase)
        scores.append(score)

    if not phases:
        logger.warning("No observables with temporal phase found.")
        return None

    # Sort by phase
    sorted_pairs = sorted(zip(phases, scores), key=lambda x: x[0])
    sorted_phases, sorted_scores = zip(*sorted_pairs)

    if binning == 'bins':
        if bins is None:
            bins = max(1, len(sorted_phases) // 10)  # heuristic
        # Bin phases
        phase_array = np.array(sorted_phases)
        score_array = np.array(sorted_scores)
        bin_edges = np.linspace(phase_array.min(), phase_array.max(), bins+1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        binned_scores = []
        for i in range(bins):
            mask = (phase_array >= bin_edges[i]) & (phase_array < bin_edges[i+1])
            if np.any(mask):
                binned_scores.append(np.mean(score_array[mask]))
            else:
                binned_scores.append(np.nan)
        # Use bin centers as x
        x = bin_centers
        y = np.array(binned_scores)
    else:
        x = np.array(sorted_phases)
        y = np.array(sorted_scores)

    return plot_atomicity_timeline(x, y, **kwargs)


# ============================================================================
# Demo / Example usage
# ============================================================================

def demo():
    """Run a simple demonstration of all visualisation functions."""
    print("="*60)
    print("Atomicity Visualisations Demo")
    print("="*60)

    # Generate synthetic atomicity data
    np.random.seed(42)
    n_nodes = 20
    n_samples = 10
    atomicity_matrix = np.random.rand(n_nodes, n_samples)
    atomicity_1d = np.random.rand(n_nodes)
    group_data = {
        'Group A': np.random.rand(30),
        'Group B': np.random.rand(25),
        'Group C': np.random.rand(35)
    }
    times = np.linspace(0, 10, 50)
    time_series = 0.5 + 0.5 * np.sin(times) + 0.1 * np.random.randn(50)

    # Create a small network
    if HAS_NETWORKX:
        G = nx.erdos_renyi_graph(n_nodes, 0.2, seed=42)
        node_atomicity = {i: np.random.rand() for i in range(n_nodes)}
    else:
        G = None
        node_atomicity = None

    # Try matplotlib backend
    print("\n--- matplotlib backend ---")
    plot_atomicity_heatmap(atomicity_matrix, title="Heatmap (matplotlib)", backend='matplotlib', show=False)
    plot_atomicity_distribution(atomicity_1d, plot_type='hist', title="Histogram (matplotlib)", backend='matplotlib', show=False)
    plot_atomicity_comparison(group_data, title="Group Comparison (matplotlib)", backend='matplotlib', show=False)
    plot_atomicity_timeline(times, time_series, title="Timeline (matplotlib)", backend='matplotlib', show=False)
    if G is not None:
        plot_atomicity_network(G, node_atomicity, title="Network (matplotlib)", backend='matplotlib', show=False)

    # Try plotly backend if available
    if HAS_PLOTLY:
        print("\n--- plotly backend ---")
        fig1 = plot_atomicity_heatmap(atomicity_matrix, title="Heatmap (plotly)", backend='plotly', show=False)
        fig2 = plot_atomicity_distribution(atomicity_1d, plot_type='box', title="Boxplot (plotly)", backend='plotly', show=False)
        fig3 = plot_atomicity_comparison(group_data, title="Group Comparison (plotly)", backend='plotly', show=False)
        fig4 = plot_atomicity_timeline(times, time_series, title="Timeline (plotly)", backend='plotly', show=False)
        if G is not None:
            fig5 = plot_atomicity_network(G, node_atomicity, title="Network (plotly)", backend='plotly', show=False)
        # Optionally display one of them
        if fig1 is not None:
            print("Plotly figures created successfully.")
    else:
        print("\nPlotly not installed – skipping plotly demo.")

    # Test Layer 1 integration (create a dummy registry)
    if HAS_ULTIMATE_OBS:
        from .irreducible_unit import UltimateObservable, ObservabilityType
        registry = {}
        for i in range(10):
            obs = UltimateObservable(
                id=f"obs_{i}",
                value=i,
                observability_type=ObservabilityType.DISCRETE,
                temporal_phase=i * 0.1
            )
            # Set a custom atomicity to have variation (override computed)
            obs.atomicity = {'qualitative': i/10.0, 'boolean': (i%2)}
            obs._atomicity_stale = False
            registry[f"obs_{i}"] = obs
        print("\n--- Layer 1 integration demo ---")
        scores, ids = atomicity_from_registry(registry, combined=True)
        print(f"Atomicity scores (first 5): {scores[:5]}")
        plot_atomicity_distribution_from_registry(registry, combined=True, title="Atomicity from Registry", show=False)
        plot_atomicity_comparison_from_registry(registry, group_by='observability_type', combined=True, title="Comparison by Type", show=False)
        plot_atomicity_timeline_from_registry(registry, phase_key='temporal_phase', title="Atomicity over Temporal Phase", show=False)
        if HAS_NETWORKX:
            plot_atomicity_network_from_registry(registry, similarity_threshold=0.5, title="Network from Registry", show=False)
        print("Layer 1 integration plots created (not displayed).")
    else:
        print("\nUltimateObservable not available – skipping Layer 1 integration demo.")

    print("\nDemo finished. Plots were not displayed (show=False).")


if __name__ == "__main__":
    demo()