"""
INTERACTIVE DASHBOARDS – ULTIMATE IMPLEMENTATION
=================================================
This module provides interactive Dash dashboards for all major components of Layer 2:
spectral analysis, persistent homology, hypergraphs, quantum graphs, causal discovery,
motif analysis, and community detection. Each dashboard can be launched as a standalone
web application, and they can also be combined into a unified multi‑page dashboard.

All features degrade gracefully if required libraries (dash, plotly, etc.) are missing.
"""

import logging
import warnings
from typing import Optional, Any, Dict, List, Tuple, Callable

# ============================================================================
# OPTIONAL LIBRARIES – ALL HANDLED GRACEFULLY
# ============================================================================

# Dash and Plotly are essential for dashboards
try:
    import dash
    from dash import dcc, html, Input, Output, State, callback_context
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_DASH = True
    HAS_PLOTLY = True
except ImportError:
    HAS_DASH = False
    HAS_PLOTLY = False
    # Create dummy classes to avoid NameError
    class dash: pass
    class dcc: pass
    class html: pass
    class Input: pass
    class Output: pass
    class callback_context: pass
    class dbc: pass
    go = None
    px = None
    def make_subplots(*args, **kwargs): return None

# NetworkX for graph layout (optional, used for graph drawings)
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

# NumPy is almost always present
import numpy as np

# Import the analysis classes from Layer 2 (use relative imports)
from . import adjacency_matrix
from . import hypergraph_relations
from . import motif_detection
from . import relations

logger = logging.getLogger(__name__)


# ============================================================================
# Helper functions to convert internal data to Plotly figures
# ============================================================================

def figure_persistence_diagram(ph: motif_detection.PersistentHomology,
                               dims: Optional[List[int]] = None) -> go.Figure:
    """
    Create a Plotly figure for a persistence diagram.
    """
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
            x=births, y=deaths,
            mode='markers',
            marker=dict(color=colors[dim % len(colors)], size=8),
            name=f'H{dim}',
            hovertemplate='Birth: %{x}<br>Death: %{y}<extra></extra>'
        ))
    # Add diagonal line
    if max_val > 0:
        fig.add_trace(go.Scatter(
            x=[0, max_val], y=[0, max_val],
            mode='lines',
            line=dict(color='black', dash='dash'),
            name='diagonal',
            hoverinfo='none'
        ))
    fig.update_layout(
        title='Persistence Diagram',
        xaxis_title='Birth',
        yaxis_title='Death',
        hovermode='closest'
    )
    return fig


def figure_barcode(ph: motif_detection.PersistentHomology,
                   dims: Optional[List[int]] = None) -> go.Figure:
    """
    Create a Plotly figure for a persistence barcode.
    """
    if not ph.diagrams:
        fig = go.Figure()
        fig.add_annotation(text="No barcode data", showarrow=False)
        return fig

    fig = make_subplots(rows=len(ph.diagrams), cols=1,
                        subplot_titles=[f'H{dim}' for dim in sorted(ph.diagrams.keys())],
                        shared_xaxes=True)
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    row = 1
    for dim, bars in sorted(ph.diagrams.items()):
        if dims is not None and dim not in dims:
            continue
        y_pos = list(range(len(bars)))
        for i, (b, d) in enumerate(bars):
            if d == float('inf'):
                # infinite bar: draw an arrow or just a line to the right edge
                fig.add_trace(go.Scatter(
                    x=[b, b+1], y=[i, i],
                    mode='lines',
                    line=dict(color=colors[dim % len(colors)], width=4),
                    showlegend=False,
                    hoverinfo='none'
                ), row=row, col=1)
            else:
                fig.add_trace(go.Scatter(
                    x=[b, d], y=[i, i],
                    mode='lines',
                    line=dict(color=colors[dim % len(colors)], width=4),
                    showlegend=False,
                    hovertemplate='Birth: %{x[0]}<br>Death: %{x[1]}<extra></extra>'
                ), row=row, col=1)
        fig.update_yaxes(title_text='Index', row=row, col=1)
        row += 1
    fig.update_layout(title='Persistence Barcode', height=300*len(ph.diagrams))
    fig.update_xaxes(title_text='Filtration')
    return fig


def figure_spectrum(sa: adjacency_matrix.SpectralGraphAnalysis,
                    matrix_type: adjacency_matrix.SpectralType = adjacency_matrix.SpectralType.LAPLACIAN,
                    nbins: int = 50) -> go.Figure:
    """
    Histogram of eigenvalues.
    """
    eigvals, _ = sa.compute_eigensystem(matrix_type)
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=eigvals, nbinsx=nbins, name='eigenvalues'))
    fig.update_layout(
        title=f'Eigenvalue spectrum ({matrix_type.value})',
        xaxis_title='eigenvalue',
        yaxis_title='count'
    )
    return fig


def figure_spectral_embedding(sa: adjacency_matrix.SpectralGraphAnalysis,
                              dim: int = 2,
                              labels: Optional[List[int]] = None,
                              matrix_type: adjacency_matrix.SpectralType = adjacency_matrix.SpectralType.LAPLACIAN) -> go.Figure:
    """
    2D or 3D scatter plot of spectral embedding.
    """
    embed = sa.spectral_embedding(dim, matrix_type)
    if dim == 2:
        fig = px.scatter(x=embed[:,0], y=embed[:,1], color=labels,
                         title='Spectral Embedding (2D)')
    elif dim == 3:
        fig = px.scatter_3d(x=embed[:,0], y=embed[:,1], z=embed[:,2], color=labels,
                            title='Spectral Embedding (3D)')
    else:
        fig = go.Figure()
        fig.add_annotation(text=f"Embedding dimension {dim} not supported", showarrow=False)
    return fig


def figure_hypergraph(hg: hypergraph_relations.Hypergraph,
                      layout: str = 'spring',
                      highlight_dims: Optional[List[int]] = None) -> go.Figure:
    """
    Visualize a hypergraph as a bipartite network (nodes and hyperedges).
    """
    if not HAS_NETWORKX:
        fig = go.Figure()
        fig.add_annotation(text="NetworkX required for hypergraph layout", showarrow=False)
        return fig

    # Build bipartite graph
    B = nx.Graph()
    B.add_nodes_from(hg.vertices, bipartite=0)
    B.add_nodes_from(hg.hyperedges.keys(), bipartite=1)
    for eid, verts in hg.hyperedges.items():
        for v in verts:
            B.add_edge(eid, v)

    # Compute positions
    if layout == 'spring':
        pos = nx.spring_layout(B)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(B)
    else:
        pos = nx.spring_layout(B)

    # Determine colors for hyperedges based on dimension
    edge_colors = []
    for eid in hg.hyperedges.keys():
        dim = len(hg.hyperedges[eid]) - 1
        if highlight_dims and dim in highlight_dims:
            edge_colors.append('red')
        else:
            edge_colors.append('lightgreen')

    # Edge traces
    edge_x = []
    edge_y = []
    for u, v in B.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    edge_trace = go.Scatter(x=edge_x, y=edge_y,
                            mode='lines',
                            line=dict(width=1, color='#888'),
                            hoverinfo='none')

    # Node traces for vertices and hyperedges
    vertex_x = [pos[n][0] for n in hg.vertices]
    vertex_y = [pos[n][1] for n in hg.vertices]
    vertex_trace = go.Scatter(x=vertex_x, y=vertex_y,
                              mode='markers+text',
                              text=[str(v) for v in hg.vertices],
                              textposition="top center",
                              marker=dict(size=10, color='lightblue'),
                              name='vertices')

    hyperedge_x = [pos[e][0] for e in hg.hyperedges.keys()]
    hyperedge_y = [pos[e][1] for e in hg.hyperedges.keys()]
    hyperedge_trace = go.Scatter(x=hyperedge_x, y=hyperedge_y,
                                 mode='markers+text',
                                 text=[str(e) for e in hg.hyperedges.keys()],
                                 textposition="bottom center",
                                 marker=dict(size=8, color=edge_colors),
                                 name='hyperedges')

    fig = go.Figure(data=[edge_trace, vertex_trace, hyperedge_trace])
    fig.update_layout(title='Hypergraph (bipartite view)',
                      showlegend=True,
                      hovermode='closest')
    return fig


def figure_quantum_graph(qg: hypergraph_relations.QuantumGraph,
                         show_amplitudes: bool = False) -> go.Figure:
    """
    Visualize a quantum graph with amplitudes as edge widths.
    """
    if not HAS_NETWORKX or qg.graph is None:
        fig = go.Figure()
        fig.add_annotation(text="NetworkX required or no graph", showarrow=False)
        return fig

    G = qg.graph
    pos = nx.spring_layout(G)

    edge_x = []
    edge_y = []
    edge_widths = []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        if show_amplitudes:
            amp = qg.edge_amplitudes.get((u, v), 1.0)
            width = np.abs(amp) * 5
        else:
            width = 1
        edge_widths.extend([width, width, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y,
                            mode='lines',
                            line=dict(width=edge_widths, color='blue'),
                            hoverinfo='none')

    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_trace = go.Scatter(x=node_x, y=node_y,
                            mode='markers+text',
                            text=[str(n) for n in G.nodes()],
                            marker=dict(size=10, color='red'),
                            name='nodes')

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(title='Quantum Graph' + (' (edge width ∝ amplitude)' if show_amplitudes else ''),
                      showlegend=False)
    return fig


def figure_causal_graph(cg: nx.DiGraph) -> go.Figure:
    """
    Visualize a causal DAG.
    """
    if not HAS_NETWORKX:
        fig = go.Figure()
        fig.add_annotation(text="NetworkX required", showarrow=False)
        return fig

    pos = nx.spring_layout(cg)
    edge_x = []
    edge_y = []
    for u, v in cg.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y,
                            mode='lines',
                            line=dict(width=1, color='black'),
                            hoverinfo='none')

    node_x = [pos[n][0] for n in cg.nodes()]
    node_y = [pos[n][1] for n in cg.nodes()]
    node_trace = go.Scatter(x=node_x, y=node_y,
                            mode='markers+text',
                            text=[str(n) for n in cg.nodes()],
                            marker=dict(size=10, color='orange'),
                            name='nodes')

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(title='Causal Graph', showlegend=False)
    return fig


def figure_motif_counts(motif_counts: Dict[str, int]) -> go.Figure:
    """
    Bar chart of motif counts.
    """
    motifs = list(motif_counts.keys())
    counts = list(motif_counts.values())
    fig = px.bar(x=motifs, y=counts, labels={'x': 'Motif', 'y': 'Count'},
                 title='Motif Counts')
    return fig


def figure_communities(comm_map: Dict[str, int], graph: nx.Graph) -> go.Figure:
    """
    Visualize graph nodes colored by community.
    """
    if not HAS_NETWORKX:
        fig = go.Figure()
        fig.add_annotation(text="NetworkX required", showarrow=False)
        return fig

    pos = nx.spring_layout(graph)
    node_x = [pos[n][0] for n in graph.nodes()]
    node_y = [pos[n][1] for n in graph.nodes()]
    colors = [comm_map.get(n, 0) for n in graph.nodes()]

    fig = go.Figure(data=[go.Scatter(x=node_x, y=node_y,
                                      mode='markers',
                                      marker=dict(size=10, color=colors, colorscale='Viridis'),
                                      text=[str(n) for n in graph.nodes()],
                                      hovertemplate='Node: %{text}<br>Community: %{marker.color}<extra></extra>')])
    fig.update_layout(title='Community Detection')
    return fig


# ============================================================================
# Dashboard creators – each returns a Dash app
# ============================================================================

def create_spectral_dashboard(sa: adjacency_matrix.SpectralGraphAnalysis,
                              title: str = "Spectral Analysis Dashboard") -> Optional[dash.Dash]:
    """
    Dashboard for spectral graph analysis with interactive controls.
    """
    if not HAS_DASH:
        logger.warning("Dash not available – cannot create spectral dashboard")
        return None

    # Define available matrix types
    matrix_options = [
        {'label': 'Laplacian', 'value': adjacency_matrix.SpectralType.LAPLACIAN.value},
        {'label': 'Adjacency', 'value': adjacency_matrix.SpectralType.ADJACENCY.value},
        {'label': 'Normalized Laplacian', 'value': adjacency_matrix.SpectralType.NORMALIZED_LAPLACIAN.value},
        {'label': 'Signless Laplacian', 'value': adjacency_matrix.SpectralType.SIGNLESS_LAPLACIAN.value},
        {'label': 'Normalized Adjacency', 'value': adjacency_matrix.SpectralType.NORMALIZED_ADJACENCY.value},
    ]

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = title

    app.layout = dbc.Container([
        html.H1(title, className="text-center mb-4"),
        dbc.Row([
            dbc.Col([
                html.H5("Matrix Type"),
                dcc.Dropdown(
                    id='matrix-type',
                    options=matrix_options,
                    value=adjacency_matrix.SpectralType.LAPLACIAN.value,
                    clearable=False
                ),
            ], width=4),
            dbc.Col([
                html.H5("Embedding Dimension"),
                dcc.Dropdown(
                    id='embed-dim',
                    options=[2, 3],
                    value=2,
                    clearable=False
                ),
            ], width=2),
            dbc.Col([
                html.H5("Number of bins"),
                dcc.Slider(
                    id='nbins',
                    min=10, max=100, step=5, value=50,
                    marks={10: '10', 50: '50', 100: '100'}
                ),
            ], width=4),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                html.H4("Eigenvalue Spectrum"),
                dcc.Graph(id='spectrum-plot')
            ], width=6),
            dbc.Col([
                html.H4("Spectral Embedding (2D/3D)"),
                dcc.Graph(id='embedding-plot')
            ], width=6)
        ]),
        dbc.Row([
            dbc.Col([
                html.H4("Invariants"),
                html.Pre(id='invariants', style={'font-size': '14px'})
            ], width=12)
        ])
    ], fluid=True)

    @app.callback(
        [Output('spectrum-plot', 'figure'),
         Output('embedding-plot', 'figure'),
         Output('invariants', 'children')],
        [Input('matrix-type', 'value'),
         Input('embed-dim', 'value'),
         Input('nbins', 'value')]
    )
    def update_spectral(matrix_type_val, embed_dim, nbins):
        # Convert string to SpectralType
        for mt in adjacency_matrix.SpectralType:
            if mt.value == matrix_type_val:
                matrix_type = mt
                break
        else:
            matrix_type = adjacency_matrix.SpectralType.LAPLACIAN

        spec_fig = figure_spectrum(sa, matrix_type, nbins)
        embed_fig = figure_spectral_embedding(sa, dim=embed_dim, matrix_type=matrix_type)

        # Compute invariants (some depend on matrix type? but get_invariants uses fixed set)
        inv = sa.get_invariants()
        inv_text = "\n".join(f"{k}: {v}" for k, v in inv.items() if v is not None)

        return spec_fig, embed_fig, inv_text

    return app


def create_topology_dashboard(analysis: motif_detection.TopologicalNetworkAnalysis,
                              title: str = "Topological Analysis Dashboard") -> Optional[dash.Dash]:
    """
    Dashboard for topological data analysis with interactive controls.
    """
    if not HAS_DASH:
        logger.warning("Dash not available – cannot create topology dashboard")
        return None

    # Determine available persistence dimensions
    dim_options = []
    if analysis.persistence and analysis.persistence.diagrams:
        dim_options = [{'label': f'H{dim}', 'value': dim} for dim in analysis.persistence.diagrams.keys()]

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = title

    app.layout = dbc.Container([
        html.H1(title, className="text-center mb-4"),
        dbc.Row([
            dbc.Col([
                html.H5("Filtration Type"),
                dcc.Dropdown(
                    id='filtration-type',
                    options=[{'label': ft.value, 'value': ft.value} for ft in motif_detection.FiltrationType],
                    value='clique',
                    clearable=False
                ),
            ], width=4),
            dbc.Col([
                html.H5("Max Edge Length"),
                dcc.Input(id='max-edge', type='number', value=1.0, step=0.1),
            ], width=2),
            dbc.Col([
                html.H5("Dimensions to show"),
                dcc.Checklist(
                    id='dimensions',
                    options=dim_options,
                    value=[dim for dim in analysis.persistence.diagrams.keys()] if dim_options else [],
                    inline=True
                ),
            ], width=4),
        ], className="mb-4"),
        dbc.Tabs([
            dbc.Tab(label="Persistence", tab_id="tab-persistence"),
            dbc.Tab(label="Motifs", tab_id="tab-motifs"),
            dbc.Tab(label="Communities", tab_id="tab-communities"),
        ], id="tabs", active_tab="tab-persistence"),
        html.Div(id="tab-content", className="mt-4")
    ], fluid=True)

    @app.callback(
        Output("tab-content", "children"),
        [Input("tabs", "active_tab"),
         Input("filtration-type", "value"),
         Input("max-edge", "value"),
         Input("dimensions", "value")]
    )
    def render_tab(active_tab, filtration_type, max_edge, dims):
        if active_tab == "tab-persistence":
            # For simplicity, we ignore filtration_type and max_edge in this demo.
            # In a real implementation, you would recompute persistence with new parameters.
            # Here we just use the precomputed data.
            if not analysis.persistence or not analysis.persistence.diagrams:
                return html.Div("No persistence data available.")
            diag_fig = figure_persistence_diagram(analysis.persistence, dims)
            barcode_fig = figure_barcode(analysis.persistence, dims)
            return dbc.Row([
                dbc.Col(dcc.Graph(figure=diag_fig), width=6),
                dbc.Col(dcc.Graph(figure=barcode_fig), width=6)
            ])
        elif active_tab == "tab-motifs":
            if not analysis.motif_counts:
                return html.Div("No motif counts available.")
            motif_fig = figure_motif_counts(analysis.motif_counts)
            return dcc.Graph(figure=motif_fig)
        elif active_tab == "tab-communities":
            if not analysis.community_map or not HAS_NETWORKX:
                return html.Div("Community data or NetworkX missing.")
            comm_fig = figure_communities(analysis.community_map, analysis.graph)
            return dbc.Row([
                dbc.Col(dcc.Graph(figure=comm_fig), width=12)
            ])
        return html.Div()

    return app


def create_hypergraph_dashboard(hg: hypergraph_relations.Hypergraph,
                                title: str = "Hypergraph Dashboard") -> Optional[dash.Dash]:
    """
    Dashboard for hypergraph visualization with interactive controls.
    """
    if not HAS_DASH:
        logger.warning("Dash not available – cannot create hypergraph dashboard")
        return None

    # Determine available edge sizes for filtering
    edge_sizes = sorted(set(len(v) for v in hg.hyperedges.values()))
    size_options = [{'label': f'Size {s}', 'value': s} for s in edge_sizes]

    # Dimensions present
    all_dims = set(len(v)-1 for v in hg.hyperedges.values())
    dim_options = [{'label': f'Dim {d}', 'value': d} for d in sorted(all_dims)]

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = title

    app.layout = dbc.Container([
        html.H1(title, className="text-center mb-4"),
        dbc.Row([
            dbc.Col([
                html.H5("Layout"),
                dcc.Dropdown(
                    id='layout',
                    options=['spring', 'kamada_kawai'],
                    value='spring',
                    clearable=False
                ),
            ], width=3),
            dbc.Col([
                html.H5("Filter by edge size"),
                dcc.Checklist(
                    id='size-filter',
                    options=size_options,
                    value=edge_sizes,  # all selected by default
                    inline=True
                ),
            ], width=4),
            dbc.Col([
                html.H5("Highlight dimensions"),
                dcc.Dropdown(
                    id='highlight-dims',
                    options=dim_options,
                    multi=True,
                    value=[]
                ),
            ], width=3),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                html.H4("Hypergraph (bipartite view)"),
                dcc.Graph(id='hypergraph-plot')
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                html.H4("Statistics"),
                html.Pre(id='stats', style={'font-size': '14px'})
            ], width=12)
        ])
    ], fluid=True)

    @app.callback(
        [Output('hypergraph-plot', 'figure'),
         Output('stats', 'children')],
        [Input('layout', 'value'),
         Input('size-filter', 'value'),
         Input('highlight-dims', 'value')]
    )
    def update_hypergraph(layout, selected_sizes, highlight_dims):
        # Filter hypergraph by selected sizes (create a copy or filter on the fly)
        # We'll create a new Hypergraph object with only edges of selected sizes.
        filtered_hg = hypergraph_relations.Hypergraph()
        for eid, verts in hg.hyperedges.items():
            if len(verts) in selected_sizes:
                filtered_hg.add_hyperedge(eid, verts, weight=hg.weights.get(eid, 1.0))

        fig = figure_hypergraph(filtered_hg, layout=layout, highlight_dims=highlight_dims)
        betti = filtered_hg.betti_numbers()
        stats = f"Vertices: {len(filtered_hg.vertices)}\nHyperedges: {len(filtered_hg.hyperedges)}\nBetti numbers: {betti}"
        return fig, stats

    return app


def create_quantum_dashboard(qg: hypergraph_relations.QuantumGraph,
                             title: str = "Quantum Graph Dashboard") -> Optional[dash.Dash]:
    """
    Dashboard for quantum graph with interactive controls.
    """
    if not HAS_DASH:
        logger.warning("Dash not available – cannot create quantum dashboard")
        return None

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = title

    app.layout = dbc.Container([
        html.H1(title, className="text-center mb-4"),
        dbc.Row([
            dbc.Col([
                html.H5("Show amplitudes"),
                dcc.RadioItems(
                    id='show-amps',
                    options=[{'label': 'Yes', 'value': True}, {'label': 'No', 'value': False}],
                    value=False,
                    inline=True
                ),
            ], width=3),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                html.H4("Quantum Graph"),
                dcc.Graph(id='quantum-plot')
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                html.H4("Amplitudes"),
                html.Pre(id='amplitudes', style={'font-size': '14px'})
            ], width=12)
        ])
    ], fluid=True)

    @app.callback(
        [Output('quantum-plot', 'figure'),
         Output('amplitudes', 'children')],
        [Input('show-amps', 'value')]
    )
    def update_quantum(show_amps):
        fig = figure_quantum_graph(qg, show_amplitudes=show_amps)
        amps = "\n".join(f"{k}: {v}" for k, v in qg.edge_amplitudes.items())
        return fig, amps

    return app


def create_causal_dashboard(cg: nx.DiGraph,
                            title: str = "Causal Graph Dashboard") -> Optional[dash.Dash]:
    """
    Dashboard for causal graph.
    """
    if not HAS_DASH:
        logger.warning("Dash not available – cannot create causal dashboard")
        return None

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = title

    app.layout = dbc.Container([
        html.H1(title, className="text-center mb-4"),
        dbc.Row([
            dbc.Col([
                html.H5("Layout"),
                dcc.Dropdown(
                    id='layout',
                    options=['spring', 'kamada_kawai'],
                    value='spring',
                    clearable=False
                ),
            ], width=3),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                html.H4("Causal DAG"),
                dcc.Graph(id='causal-plot')
            ], width=12)
        ])
    ], fluid=True)

    @app.callback(
        Output('causal-plot', 'figure'),
        [Input('layout', 'value')]
    )
    def update_causal(layout):
        # Recompute layout based on selection
        if layout == 'spring':
            pos = nx.spring_layout(cg)
        elif layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(cg)
        else:
            pos = nx.spring_layout(cg)

        # Build figure manually with the chosen positions
        edge_x = []
        edge_y = []
        for u, v in cg.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(x=edge_x, y=edge_y,
                                mode='lines',
                                line=dict(width=1, color='black'),
                                hoverinfo='none')

        node_x = [pos[n][0] for n in cg.nodes()]
        node_y = [pos[n][1] for n in cg.nodes()]
        node_trace = go.Scatter(x=node_x, y=node_y,
                                mode='markers+text',
                                text=[str(n) for n in cg.nodes()],
                                marker=dict(size=10, color='orange'),
                                name='nodes')

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(title='Causal Graph', showlegend=False)
        return fig

    return app


def create_combined_dashboard(spectral=None, topology=None, hypergraph=None,
                              quantum=None, causal=None,
                              title: str = "Layer 2 Unified Dashboard") -> Optional[dash.Dash]:
    """
    Combined dashboard with tabs for each available analysis object.
    """
    if not HAS_DASH:
        logger.warning("Dash not available – cannot create combined dashboard")
        return None

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = title

    tabs = []
    tab_contents = {}

    if spectral is not None:
        tabs.append(dbc.Tab(label="Spectral", tab_id="tab-spectral"))
        tab_contents["tab-spectral"] = spectral
    if topology is not None:
        tabs.append(dbc.Tab(label="Topology", tab_id="tab-topology"))
        tab_contents["tab-topology"] = topology
    if hypergraph is not None:
        tabs.append(dbc.Tab(label="Hypergraph", tab_id="tab-hypergraph"))
        tab_contents["tab-hypergraph"] = hypergraph
    if quantum is not None:
        tabs.append(dbc.Tab(label="Quantum", tab_id="tab-quantum"))
        tab_contents["tab-quantum"] = quantum
    if causal is not None:
        tabs.append(dbc.Tab(label="Causal", tab_id="tab-causal"))
        tab_contents["tab-causal"] = causal

    app.layout = dbc.Container([
        html.H1(title, className="text-center mb-4"),
        dbc.Tabs(tabs, id="combined-tabs", active_tab=list(tab_contents.keys())[0] if tab_contents else None),
        html.Div(id="combined-content", className="mt-4")
    ], fluid=True)

    @app.callback(
        Output("combined-content", "children"),
        [Input("combined-tabs", "active_tab")]
    )
    def render_combined(active_tab):
        if active_tab is None or active_tab not in tab_contents:
            return html.Div("No data")
        obj = tab_contents[active_tab]
        # For each tab, we could embed the full interactive dashboard,
        # but for simplicity we just show the main figures with basic controls.
        # Here we return a placeholder; in a full implementation, you might
        # embed the entire dashboard's layout, but that's complex.
        # Instead, we'll just display the static figures.
        if active_tab == "tab-spectral":
            return html.Div([
                dcc.Graph(figure=figure_spectrum(obj)),
                dcc.Graph(figure=figure_spectral_embedding(obj, dim=2))
            ])
        elif active_tab == "tab-topology":
            if not obj.persistence:
                return html.Div("No persistence data")
            return html.Div([
                dcc.Graph(figure=figure_persistence_diagram(obj.persistence)),
                dcc.Graph(figure=figure_barcode(obj.persistence))
            ])
        elif active_tab == "tab-hypergraph":
            return dcc.Graph(figure=figure_hypergraph(obj))
        elif active_tab == "tab-quantum":
            return dcc.Graph(figure=figure_quantum_graph(obj))
        elif active_tab == "tab-causal":
            return dcc.Graph(figure=figure_causal_graph(obj))
        return html.Div()

    return app


# ============================================================================
# Utility to run a dashboard from command line (optional)
# ============================================================================

def run_dashboard(app: dash.Dash, debug: bool = False, port: int = 8050):
    """
    Run a Dash app.
    """
    if app is not None:
        app.run_server(debug=debug, port=port)
    else:
        logger.error("No dashboard to run")


# ============================================================================
# Demo / test if run as main
# ============================================================================

def demo():
    """
    Create a demo dashboard with synthetic data for all components.
    """
    if not HAS_DASH:
        print("Dash not installed – cannot run demo")
        return

    # Generate synthetic graph
    if HAS_NETWORKX:
        G = nx.erdos_renyi_graph(20, 0.2)
    else:
        G = None

    # Spectral
    sa = adjacency_matrix.SpectralGraphAnalysis(G) if G is not None else None

    # Topology
    top = motif_detection.TopologicalNetworkAnalysis(graph=G, name="demo")
    if G is not None:
        top.compute_persistence()
        top.compute_motifs(max_graphlet_size=3)

    # Hypergraph
    hg = hypergraph_relations.Hypergraph()
    if G is not None:
        for i, (u, v) in enumerate(G.edges()):
            hg.add_hyperedge(f"e{i}", {u, v}, weight=1.0)

    # Quantum graph
    qg = hypergraph_relations.QuantumGraph(graph=G)
    if G is not None:
        for u, v in G.edges():
            qg.edge_amplitudes[(u, v)] = np.random.random()

    # Causal graph
    if HAS_NETWORKX:
        cg = nx.DiGraph()
        cg.add_edges_from([(0,1), (1,2), (0,2), (3,4)])
    else:
        cg = None

    # For demo, launch the spectral dashboard as an example
    app = create_spectral_dashboard(sa, title="Spectral Analysis Demo")
    if app:
        run_dashboard(app)
    else:
        print("Could not create dashboard.")


if __name__ == "__main__":
    demo()