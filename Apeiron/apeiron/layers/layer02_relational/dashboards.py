"""
dashboards.py – Static Plotly figures for Layer 2
==================================================
Provides pure figure‑generating functions (no Dash apps) for:
  - persistence diagrams & barcodes
  - spectral eigenvalue distributions
  - spectral embedding scatter plots (2D / 3D)
  - hypergraph bipartite views
  - quantum graph amplitude views
  - causal graph views
  - motif count bar charts
  - community colour‑coded networks
"""

from typing import List, Optional, Dict, Any, Tuple

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


# ============================================================================
# Persistence diagram & barcode
# ============================================================================
def figure_persistence_diagram(ph, dims: Optional[List[int]] = None) -> go.Figure:
    """Scatter plot of birth vs. death per homology dimension."""
    fig = go.Figure()
    if not ph.diagrams:
        fig.add_annotation(text="No persistence data", showarrow=False)
        return fig
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    max_val = 0.0
    for dim, bars in ph.diagrams.items():
        if dims is not None and dim not in dims:
            continue
        births = [b for b, _ in bars]
        deaths = [d if d != float('inf') else None for _, d in bars]
        finite = [(b, d) for b, d in bars if d != float('inf')]
        if finite:
            max_val = max(max_val, max(d for _, d in finite))
        fig.add_trace(go.Scatter(
            x=births, y=deaths, mode='markers',
            marker=dict(color=colors[dim % len(colors)], size=8),
            name=f'H{dim}',
            hovertemplate='Birth: %{x}<br>Death: %{y}<extra></extra>'
        ))
    if max_val > 0:
        fig.add_trace(go.Scatter(
            x=[0, max_val], y=[0, max_val], mode='lines',
            line=dict(color='black', dash='dash'), name='diagonal', hoverinfo='none'
        ))
    fig.update_layout(title='Persistence Diagram', xaxis_title='Birth', yaxis_title='Death')
    return fig


def figure_barcode(ph, dims: Optional[List[int]] = None) -> go.Figure:
    """Horizontal bars for each persistence interval."""
    if not ph.diagrams:
        fig = go.Figure()
        fig.add_annotation(text="No barcode data", showarrow=False)
        return fig
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    dim_keys = sorted(ph.diagrams.keys())
    fig = make_subplots(rows=len(dim_keys), cols=1,
                        subplot_titles=[f'H{dim}' for dim in dim_keys],
                        shared_xaxes=True)
    for row, dim in enumerate(dim_keys, start=1):
        bars = ph.diagrams[dim]
        for i, (b, d) in enumerate(bars):
            if d == float('inf'):
                fig.add_trace(go.Scatter(
                    x=[b, b+1], y=[i, i], mode='lines',
                    line=dict(color=colors[dim % len(colors)], width=4),
                    showlegend=False, hoverinfo='none'
                ), row=row, col=1)
            else:
                fig.add_trace(go.Scatter(
                    x=[b, d], y=[i, i], mode='lines',
                    line=dict(color=colors[dim % len(colors)], width=4),
                    showlegend=False,
                    hovertemplate='Birth: %{x[0]}<br>Death: %{x[1]}<extra></extra>'
                ), row=row, col=1)
    fig.update_layout(title='Persistence Barcode', height=300*len(dim_keys))
    fig.update_xaxes(title_text='Filtration')
    return fig


# ============================================================================
# Spectral figures
# ============================================================================
def figure_spectrum(sa, matrix_type=None, nbins: int = 50) -> go.Figure:
    """Histogram of eigenvalues."""
    try:
        from .adjacency_matrix import SpectralType   # ou spectral
    except ImportError:
        from .spectral import SpectralType
    if matrix_type is None:
        matrix_type = SpectralType.LAPLACIAN
    eigvals, _ = sa.compute_eigensystem(matrix_type)
    fig = go.Figure(data=[go.Histogram(x=eigvals, nbinsx=nbins)])
    fig.update_layout(title=f'Eigenvalue spectrum ({matrix_type.value})',
                      xaxis_title='eigenvalue', yaxis_title='count')
    return fig


def figure_spectral_embedding(sa, dim: int = 2,
                              labels: Optional[List[int]] = None,
                              matrix_type=None) -> go.Figure:
    try:
        from .spectral import SpectralType
    except ImportError:
        from .adjacency_matrix import SpectralType as _; SpectralType = _
    if matrix_type is None:
        matrix_type = SpectralType.LAPLACIAN
    embed = sa.spectral_embedding(dim, matrix_type)
    if dim == 2:
        fig = px.scatter(x=embed[:,0], y=embed[:,1], color=labels,
                         title='Spectral Embedding (2D)')
    elif dim == 3:
        fig = px.scatter_3d(x=embed[:,0], y=embed[:,1], z=embed[:,2], color=labels,
                            title='Spectral Embedding (3D)')
    else:
        fig = go.Figure()
        fig.add_annotation(text=f"Dimension {dim} not supported", showarrow=False)
    return fig


# ============================================================================
# Hypergraph / Quantum graph / Causal graph figures
# ============================================================================
def figure_hypergraph(hg, layout: str = 'spring',
                      highlight_dims: Optional[List[int]] = None) -> go.Figure:
    if not HAS_NETWORKX:
        return go.Figure()
    B = nx.Graph()
    B.add_nodes_from(hg.vertices, bipartite=0)
    B.add_nodes_from(hg.hyperedges.keys(), bipartite=1)
    for eid, verts in hg.hyperedges.items():
        for v in verts:
            B.add_edge(eid, v)
    pos = nx.spring_layout(B) if layout == 'spring' else nx.kamada_kawai_layout(B)
    edge_colors = []
    for eid in hg.hyperedges.keys():
        dim = len(hg.hyperedges[eid]) - 1
        edge_colors.append('red' if (highlight_dims and dim in highlight_dims) else 'lightgreen')
    edge_trace = []
    for u, v in B.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        edge_trace.append(go.Scatter(x=[x0, x1, None], y=[y0, y1, None],
                                     mode='lines', line=dict(width=1, color='#888'),
                                     hoverinfo='none'))
    node_trace_v = go.Scatter(
        x=[pos[n][0] for n in hg.vertices],
        y=[pos[n][1] for n in hg.vertices],
        mode='markers+text', text=[str(v) for v in hg.vertices],
        marker=dict(size=10, color='lightblue'), name='vertices')
    node_trace_e = go.Scatter(
        x=[pos[e][0] for e in hg.hyperedges.keys()],
        y=[pos[e][1] for e in hg.hyperedges.keys()],
        mode='markers+text', text=[str(e) for e in hg.hyperedges.keys()],
        marker=dict(size=8, color=edge_colors), name='hyperedges')
    fig = go.Figure(data=edge_trace + [node_trace_v, node_trace_e])
    fig.update_layout(title='Hypergraph', showlegend=True)
    return fig


def figure_quantum_graph(qg, show_amplitudes: bool = False) -> go.Figure:
    if not HAS_NETWORKX or qg.graph is None:
        return go.Figure()
    pos = nx.spring_layout(qg.graph)
    edge_trace = []
    for u, v in qg.graph.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        amp = abs(qg.edge_amplitudes.get((u,v), 1.0)) if show_amplitudes else 1.0
        edge_trace.append(go.Scatter(x=[x0, x1, None], y=[y0, y1, None],
                                     mode='lines', line=dict(width=amp*5, color='blue'),
                                     hoverinfo='none'))
    node_trace = go.Scatter(
        x=[pos[n][0] for n in qg.graph.nodes()],
        y=[pos[n][1] for n in qg.graph.nodes()],
        mode='markers+text', text=[str(n) for n in qg.graph.nodes()],
        marker=dict(size=10, color='red'), name='nodes')
    return go.Figure(data=edge_trace + [node_trace])


def figure_causal_graph(cg) -> go.Figure:
    if not HAS_NETWORKX:
        return go.Figure()
    pos = nx.spring_layout(cg)
    edge_trace = []
    for u, v in cg.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        edge_trace.append(go.Scatter(x=[x0, x1, None], y=[y0, y1, None],
                                     mode='lines', line=dict(width=1, color='black'),
                                     hoverinfo='none'))
    node_trace = go.Scatter(
        x=[pos[n][0] for n in cg.nodes()],
        y=[pos[n][1] for n in cg.nodes()],
        mode='markers+text', text=[str(n) for n in cg.nodes()],
        marker=dict(size=10, color='orange'), name='nodes')
    return go.Figure(data=edge_trace + [node_trace])


def figure_motif_counts(motif_counts: Dict[str, int]) -> go.Figure:
    motifs = list(motif_counts.keys())
    counts = list(motif_counts.values())
    return px.bar(x=motifs, y=counts, labels={'x': 'Motif', 'y': 'Count'},
                  title='Motif Counts')


def figure_communities(comm_map: Dict[str, int], graph) -> go.Figure:
    if not HAS_NETWORKX:
        return go.Figure()
    pos = nx.spring_layout(graph)
    node_x = [pos[n][0] for n in graph.nodes()]
    node_y = [pos[n][1] for n in graph.nodes()]
    colors = [comm_map.get(n, 0) for n in graph.nodes()]
    fig = go.Figure(data=[go.Scatter(
        x=node_x, y=node_y, mode='markers',
        marker=dict(size=10, color=colors, colorscale='Viridis'),
        text=[str(n) for n in graph.nodes()],
        hovertemplate='Node: %{text}<br>Community: %{marker.color}<extra></extra>')])
    fig.update_layout(title='Community Detection')
    return fig