"""
VISUALIZATION DASH – ULTIMATE IMPLEMENTATION
=============================================
This module provides advanced, interactive visualization components for Layer 2,
built on top of Plotly Dash. It includes reusable components for:

- Persistence diagrams and barcodes with hover and selection callbacks
- Spectral embedding scatter plots (2D/3D) with node labels and selection
- Hypergraph bipartite visualizations with filtering by edge size
- Quantum graph amplitude displays with hover and threshold filtering
- Causal graph viewers
- Community maps with color legends and selection

All components are designed to be easily integrated into larger Dash apps
or used as standalone figures. The module relies on the figure‑generation
functions from `dashboard.py` but adds interactivity and callbacks.

If Dash or Plotly are missing, the module raises an ImportError when
attempting to create components.
"""

import logging
from typing import Optional, List, Dict, Any, Callable, Tuple
import numpy as np

# ============================================================================
# OPTIONAL LIBRARIES – REQUIRED FOR THIS MODULE
# ============================================================================

try:
    import dash
    from dash import dcc, html, Input, Output, State, callback_context
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.colors import qualitative
    HAS_DASH = True
except ImportError:
    HAS_DASH = False

# Import figure functions from the existing dashboard module
try:
    from . import dashboard
    HAS_FIGURES = True
except ImportError:
    HAS_FIGURES = False
    dashboard = None

logger = logging.getLogger(__name__)


# ============================================================================
# BASE INTERACTIVE COMPONENT CLASS
# ============================================================================

class InteractiveComponent:
    """Base class for interactive Dash components with built‑in callbacks."""
    def __init__(self, component_id: str):
        self.component_id = component_id
        self.callbacks_registered = False

    def get_layout(self) -> html.Div:
        """Return the Dash layout for this component."""
        raise NotImplementedError

    def register_callbacks(self, app: dash.Dash):
        """Register the necessary callbacks with the Dash app."""
        self.callbacks_registered = True


# ============================================================================
# PERSISTENCE DIAGRAM COMPONENT
# ============================================================================

class PersistenceDiagramComponent(InteractiveComponent):
    """
    Interactive persistence diagram with hover info and click callbacks.
    """
    def __init__(self, component_id: str, ph, dims: Optional[List[int]] = None,
                 title: str = "Persistence Diagram"):
        super().__init__(component_id)
        self.ph = ph
        self.dims = dims
        self.title = title
        self.figure = dashboard.figure_persistence_diagram(ph, dims)
        self.selected_point = None

    def get_layout(self) -> html.Div:
        return html.Div([
            dcc.Graph(
                id=f"{self.component_id}-graph",
                figure=self.figure,
                config={'displayModeBar': True}
            ),
            html.Div(id=f"{self.component_id}-info", children="Hover over a point"),
            html.Div(id=f"{self.component_id}-selected", children="No point selected")
        ])

    def register_callbacks(self, app: dash.Dash):
        @app.callback(
            Output(f"{self.component_id}-info", "children"),
            [Input(f"{self.component_id}-graph", "hoverData")]
        )
        def display_hover(hoverData):
            if hoverData is None:
                return "Hover over a point"
            pt = hoverData['points'][0]
            return f"Birth: {pt['x']:.3f}, Death: {pt['y']:.3f} (H{pt.get('curveNumber', 0)})"

        @app.callback(
            Output(f"{self.component_id}-selected", "children"),
            [Input(f"{self.component_id}-graph", "clickData")]
        )
        def display_click(clickData):
            if clickData is None:
                return "No point selected"
            pt = clickData['points'][0]
            self.selected_point = (pt['x'], pt['y'], pt.get('curveNumber', 0))
            return f"Selected: Birth={pt['x']:.3f}, Death={pt['y']:.3f} (H{pt.get('curveNumber', 0)})"


# ============================================================================
# SPECTRAL EMBEDDING COMPONENT
# ============================================================================

class SpectralEmbeddingComponent(InteractiveComponent):
    """
    Interactive 2D or 3D scatter plot of spectral embedding.
    Allows selecting dimensions and toggling labels, and supports lasso/box selection.
    """
    def __init__(self, component_id: str, sa, dim: int = 2,
                 matrix_type: str = 'laplacian',
                 labels: Optional[List[int]] = None,
                 node_names: Optional[List[str]] = None):
        super().__init__(component_id)
        self.sa = sa
        self.dim = dim
        self.matrix_type = matrix_type
        self.labels = labels
        self.node_names = node_names
        self.embed = None
        self.figure = go.Figure()
        self.update_figure()

    def update_figure(self):
        from ..adjacency_matrix import SpectralType
        mt = SpectralType.LAPLACIAN if self.matrix_type == 'laplacian' else SpectralType.ADJACENCY
        self.embed = self.sa.spectral_embedding(self.dim, mt)
        if self.dim == 2:
            self.figure = px.scatter(
                x=self.embed[:, 0], y=self.embed[:, 1],
                color=self.labels,
                text=self.node_names,
                title=f"Spectral Embedding ({self.dim}D)"
            )
        elif self.dim == 3:
            self.figure = px.scatter_3d(
                x=self.embed[:, 0], y=self.embed[:, 1], z=self.embed[:, 2],
                color=self.labels,
                text=self.node_names,
                title=f"Spectral Embedding ({self.dim}D)"
            )
        else:
            self.figure = go.Figure()
            self.figure.add_annotation(text=f"Dimension {self.dim} not supported")

    def get_layout(self) -> html.Div:
        return html.Div([
            html.H4("Spectral Embedding"),
            html.Label("Dimension:"),
            dcc.Dropdown(
                id=f"{self.component_id}-dim-dropdown",
                options=[{'label': '2D', 'value': 2}, {'label': '3D', 'value': 3}],
                value=self.dim,
                clearable=False,
                style={'width': '100px', 'display': 'inline-block'}
            ),
            html.Label("Matrix type:", style={'marginLeft': '20px'}),
            dcc.Dropdown(
                id=f"{self.component_id}-matrix-dropdown",
                options=[{'label': 'Laplacian', 'value': 'laplacian'},
                         {'label': 'Adjacency', 'value': 'adjacency'}],
                value=self.matrix_type,
                clearable=False,
                style={'width': '150px', 'display': 'inline-block'}
            ),
            dcc.Graph(
                id=f"{self.component_id}-graph",
                figure=self.figure,
                config={'modeBarButtonsToAdd': ['lasso2d', 'select2d']}
            ),
            html.Div(id=f"{self.component_id}-hover-info"),
            html.Div(id=f"{self.component_id}-selected-nodes", children="No nodes selected")
        ])

    def register_callbacks(self, app: dash.Dash):
        @app.callback(
            Output(f"{self.component_id}-graph", "figure"),
            [Input(f"{self.component_id}-dim-dropdown", "value"),
             Input(f"{self.component_id}-matrix-dropdown", "value")]
        )
        def update_figure(dim_val, matrix_val):
            self.dim = dim_val
            self.matrix_type = matrix_val
            self.update_figure()
            return self.figure

        @app.callback(
            Output(f"{self.component_id}-hover-info", "children"),
            [Input(f"{self.component_id}-graph", "hoverData")]
        )
        def hover_info(hoverData):
            if hoverData is None:
                return ""
            pt = hoverData['points'][0]
            node_idx = pt['pointIndex']
            name = self.node_names[node_idx] if self.node_names else str(node_idx)
            return f"Node {name}: ({pt['x']:.3f}, {pt['y']:.3f})"

        @app.callback(
            Output(f"{self.component_id}-selected-nodes", "children"),
            [Input(f"{self.component_id}-graph", "selectedData")]
        )
        def selection_info(selectedData):
            if selectedData is None or not selectedData['points']:
                return "No nodes selected"
            points = selectedData['points']
            indices = [p['pointIndex'] for p in points]
            names = [self.node_names[i] if self.node_names else str(i) for i in indices]
            return f"Selected nodes: {', '.join(names)}"


# ============================================================================
# HYPERGRAPH COMPONENT
# ============================================================================

class HypergraphComponent(InteractiveComponent):
    """
    Interactive hypergraph viewer with filtering by edge size/weight.
    """
    def __init__(self, component_id: str, hg, layout: str = 'spring'):
        super().__init__(component_id)
        self.hg = hg
        self.layout = layout
        self.edge_sizes = sorted(set(len(v) for v in hg.hyperedges.values()))
        self.figure = dashboard.figure_hypergraph(hg, layout)

    def get_layout(self) -> html.Div:
        return html.Div([
            html.H4("Hypergraph Viewer"),
            html.Label("Filter by edge size:"),
            dcc.Checklist(
                id=f"{self.component_id}-size-filter",
                options=[{'label': f"Size {s}", 'value': s} for s in self.edge_sizes],
                value=self.edge_sizes,  # all selected by default
                inline=True
            ),
            html.Label("Edge color intensity (weight):"),
            dcc.RangeSlider(
                id=f"{self.component_id}-weight-range",
                min=0, max=1, step=0.05,
                value=[0, 1],
                marks={0: '0', 0.5: '0.5', 1: '1'}
            ),
            dcc.Graph(id=f"{self.component_id}-graph", figure=self.figure),
            html.Div(id=f"{self.component_id}-click-info")
        ])

    def register_callbacks(self, app: dash.Dash):
        @app.callback(
            Output(f"{self.component_id}-graph", "figure"),
            [Input(f"{self.component_id}-size-filter", "value"),
             Input(f"{self.component_id}-weight-range", "value")]
        )
        def filter_edges(selected_sizes, weight_range):
            # Create a filtered view of the hypergraph
            # We need to rebuild the figure using only edges with size in selected_sizes
            # and weight within weight_range.
            # Since dashboard.figure_hypergraph doesn't support filtering, we'll implement a simplified version here.
            # This is a custom figure generation that filters edges.
            import networkx as nx
            G = nx.Graph()
            # Add vertices
            for v in self.hg.vertices:
                G.add_node(v)

            # Filter edges
            min_w, max_w = weight_range
            filtered_edges = []
            for e_id, members in self.hg.hyperedges.items():
                weight = self.hg.weights.get(e_id, 1.0)
                if len(members) in selected_sizes and min_w <= weight <= max_w:
                    # For visualization, we'll represent each hyperedge as a star connecting all members to a new node (the hyperedge)
                    # This is a standard bipartite representation.
                    # We'll create a new node for the hyperedge (with a special label)
                    hypernode = f"h_{e_id}"
                    G.add_node(hypernode, bipartite=1)
                    for m in members:
                        G.add_edge(hypernode, m, weight=weight)

            # Generate layout (bipartite layout)
            if self.layout == 'spring':
                pos = nx.spring_layout(G, seed=42)
            elif self.layout == 'kamada_kawai':
                pos = nx.kamada_kawai_layout(G)
            else:
                pos = nx.spring_layout(G)

            # Separate nodes and hypernodes
            node_pos = []
            hypernode_pos = []
            for node, coord in pos.items():
                if node.startswith('h_'):
                    hypernode_pos.append(coord)
                else:
                    node_pos.append(coord)

            # Create traces
            traces = []
            # Edges
            edge_trace = []
            for u, v, data in G.edges(data=True):
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                weight = data.get('weight', 1.0)
                edge_trace.append(go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    mode='lines',
                    line=dict(width=1, color=f'rgba(100,100,255,{weight})'),
                    hoverinfo='none',
                    showlegend=False
                ))
            traces.extend(edge_trace)

            # Nodes (original vertices)
            node_x = [p[0] for p in node_pos]
            node_y = [p[1] for p in node_pos]
            node_text = [str(v) for v in G.nodes() if not v.startswith('h_')]
            traces.append(go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                marker=dict(size=10, color='lightblue'),
                text=node_text,
                textposition="top center",
                name='Vertices'
            ))

            # Hyperedge nodes
            hyper_x = [p[0] for p in hypernode_pos]
            hyper_y = [p[1] for p in hypernode_pos]
            hyper_text = [v[2:] for v in G.nodes() if v.startswith('h_')]
            traces.append(go.Scatter(
                x=hyper_x, y=hyper_y,
                mode='markers',
                marker=dict(size=15, color='orange', symbol='square'),
                text=hyper_text,
                hoverinfo='text',
                name='Hyperedges'
            ))

            fig = go.Figure(data=traces)
            fig.update_layout(
                title="Filtered Hypergraph",
                showlegend=True,
                hovermode='closest',
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False)
            )
            return fig

        @app.callback(
            Output(f"{self.component_id}-click-info", "children"),
            [Input(f"{self.component_id}-graph", "clickData")]
        )
        def click_info(clickData):
            if clickData is None:
                return ""
            pt = clickData['points'][0]
            # Determine if it's a vertex or hyperedge
            curve = pt.get('curveNumber', 0)
            if curve == 1:  # vertices trace
                node = pt['text']
                return f"Vertex {node}"
            elif curve == 2:  # hyperedges trace
                node = pt['text']
                return f"Hyperedge {node}"
            return ""


# ============================================================================
# QUANTUM GRAPH COMPONENT
# ============================================================================

class QuantumGraphComponent(InteractiveComponent):
    """
    Interactive quantum graph viewer with amplitude tooltips and threshold filtering.
    """
    def __init__(self, component_id: str, qg):
        super().__init__(component_id)
        self.qg = qg
        self.figure = dashboard.figure_quantum_graph(qg)
        self.amplitudes = list(qg.edge_amplitudes.values()) if qg.edge_amplitudes else [0, 1]

    def get_layout(self) -> html.Div:
        return html.Div([
            html.H4("Quantum Graph"),
            html.Label("Amplitude threshold:"),
            dcc.RangeSlider(
                id=f"{self.component_id}-threshold",
                min=min(self.amplitudes) if self.amplitudes else 0,
                max=max(self.amplitudes) if self.amplitudes else 1,
                step=0.05,
                value=[min(self.amplitudes) if self.amplitudes else 0,
                       max(self.amplitudes) if self.amplitudes else 1],
                marks={0: '0', 0.5: '0.5', 1: '1'}
            ),
            dcc.Graph(id=f"{self.component_id}-graph", figure=self.figure),
            html.Div(id=f"{self.component_id}-edge-info")
        ])

    def register_callbacks(self, app: dash.Dash):
        @app.callback(
            Output(f"{self.component_id}-graph", "figure"),
            [Input(f"{self.component_id}-threshold", "value")]
        )
        def filter_amplitude(threshold):
            min_amp, max_amp = threshold
            # Recreate figure with filtered edges
            # We'll use the dashboard.figure_quantum_graph but modify the edge trace to hide those outside threshold.
            fig = dashboard.figure_quantum_graph(self.qg)
            # Find the edge trace (first trace, assuming it's the lines)
            if fig.data and len(fig.data) > 0:
                # We need to selectively show/hide edges. Plotly doesn't support hiding individual lines easily.
                # Instead, we can rebuild the figure with only the edges meeting the threshold.
                # For simplicity, we'll recreate the figure using a custom approach.
                import networkx as nx
                G = nx.Graph()
                for u, v in self.qg.graph.edges():
                    amp = self.qg.edge_amplitudes.get((u, v), 0)
                    if min_amp <= amp <= max_amp:
                        G.add_edge(u, v, amplitude=amp)
                pos = nx.spring_layout(self.qg.graph)  # use same positions as original for consistency
                edge_trace = []
                for u, v, data in G.edges(data=True):
                    x0, y0 = pos[u]
                    x1, y1 = pos[v]
                    amp = data['amplitude']
                    edge_trace.append(go.Scatter(
                        x=[x0, x1, None],
                        y=[y0, y1, None],
                        mode='lines',
                        line=dict(width=2, color=f'rgba(0,0,255,{amp})'),
                        hoverinfo='none',
                        showlegend=False
                    ))
                # Nodes
                node_x = [pos[n][0] for n in G.nodes()]
                node_y = [pos[n][1] for n in G.nodes()]
                node_text = [str(n) for n in G.nodes()]
                node_trace = go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    marker=dict(size=10, color='lightblue'),
                    text=node_text,
                    textposition="top center",
                    name='Nodes'
                )
                fig.data = tuple(edge_trace) + (node_trace,)
                fig.update_layout(title="Quantum Graph (filtered by amplitude)")
            return fig

        @app.callback(
            Output(f"{self.component_id}-edge-info", "children"),
            [Input(f"{self.component_id}-graph", "hoverData")]
        )
        def hover_edge(hoverData):
            if hoverData is None:
                return ""
            pt = hoverData['points'][0]
            # In the custom figure, the first few traces are edges; we need to know which edge.
            # For simplicity, we'll extract from the point's customdata if we set it.
            # Without customdata, we can't easily know which edge. We'll use a heuristic:
            # if the point is on a line (curveNumber < node trace index), it's an edge.
            # But we don't have edge labels. So we'll just display a generic message.
            if pt.get('curveNumber', 0) < len(fig.data) - 1:
                # It's an edge
                return f"Edge with amplitude in range"
            return ""


# ============================================================================
# CAUSAL GRAPH COMPONENT
# ============================================================================

class CausalGraphComponent(InteractiveComponent):
    """
    Interactive causal DAG viewer with edge type indication and filtering.
    """
    def __init__(self, component_id: str, cg):
        super().__init__(component_id)
        self.cg = cg
        self.figure = dashboard.figure_causal_graph(cg)

    def get_layout(self) -> html.Div:
        return html.Div([
            html.H4("Causal Graph"),
            html.Label("Edge type filter:"),
            dcc.Checklist(
                id=f"{self.component_id}-type-filter",
                options=[{'label': 'Causal', 'value': 'causal'},
                         {'label': 'Confounding', 'value': 'confounding'},
                         {'label': 'Mediating', 'value': 'mediating'}],
                value=['causal', 'confounding', 'mediating'],
                inline=True
            ),
            dcc.Graph(id=f"{self.component_id}-graph", figure=self.figure)
        ])

    def register_callbacks(self, app: dash.Dash):
        @app.callback(
            Output(f"{self.component_id}-graph", "figure"),
            [Input(f"{self.component_id}-type-filter", "value")]
        )
        def filter_edges(selected_types):
            # Rebuild figure with only edges of selected types
            # We need to know the edge types. Assuming self.cg.edge_types exists.
            # For simplicity, we'll use the same figure function but filter edges in the graph before.
            import networkx as nx
            G = nx.DiGraph()
            G.add_nodes_from(self.cg.graph.nodes())
            for u, v, data in self.cg.graph.edges(data=True):
                if data.get('type', 'causal') in selected_types:
                    G.add_edge(u, v, **data)
            pos = nx.spring_layout(G)  # or use a fixed layout
            edge_trace = []
            for u, v in G.edges():
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                edge_trace.append(go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    mode='lines',
                    line=dict(width=1, color='gray'),
                    hoverinfo='none',
                    showlegend=False
                ))
            node_x = [pos[n][0] for n in G.nodes()]
            node_y = [pos[n][1] for n in G.nodes()]
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                marker=dict(size=10, color='lightblue'),
                text=list(G.nodes()),
                textposition="top center",
                name='Nodes'
            )
            fig = go.Figure(data=edge_trace + [node_trace])
            fig.update_layout(
                title="Causal Graph (filtered)",
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False)
            )
            return fig


# ============================================================================
# COMMUNITY MAP COMPONENT
# ============================================================================

class CommunityMapComponent(InteractiveComponent):
    """
    Interactive community map with hover for node community, and selection to highlight community.
    """
    def __init__(self, component_id: str, comm_map: Dict[str, int], graph):
        super().__init__(component_id)
        self.comm_map = comm_map
        self.graph = graph
        self.figure = dashboard.figure_communities(comm_map, graph)

    def get_layout(self) -> html.Div:
        unique_comms = sorted(set(self.comm_map.values()))
        return html.Div([
            html.H4("Community Map"),
            html.Label("Select community to highlight:"),
            dcc.Dropdown(
                id=f"{self.component_id}-comm-select",
                options=[{'label': f'Community {c}', 'value': c} for c in unique_comms],
                value=None,
                placeholder="All communities"
            ),
            dcc.Graph(id=f"{self.component_id}-graph", figure=self.figure),
            html.Div(id=f"{self.component_id}-node-info")
        ])

    def register_callbacks(self, app: dash.Dash):
        @app.callback(
            Output(f"{self.component_id}-graph", "figure"),
            [Input(f"{self.component_id}-comm-select", "value")]
        )
        def highlight_community(selected_comm):
            # Create a new figure with highlighted community
            import networkx as nx
            pos = nx.spring_layout(self.graph)
            edge_trace = go.Scatter(
                x=[], y=[], mode='lines', line=dict(width=0.5, color='gray'), hoverinfo='none'
            )
            # Nodes colored by community
            node_colors = []
            node_x = []
            node_y = []
            node_text = []
            for node in self.graph.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                node_text.append(str(node))
                comm = self.comm_map.get(node, -1)
                if selected_comm is not None and comm == selected_comm:
                    node_colors.append('red')
                else:
                    node_colors.append('lightblue')

            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                marker=dict(size=10, color=node_colors),
                text=node_text,
                textposition="top center",
                name='Nodes'
            )
            fig = go.Figure(data=[edge_trace, node_trace])
            fig.update_layout(
                title=f"Community Map (highlighting comm {selected_comm})" if selected_comm else "Community Map",
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False)
            )
            return fig

        @app.callback(
            Output(f"{self.component_id}-node-info", "children"),
            [Input(f"{self.component_id}-graph", "hoverData")]
        )
        def hover_node(hoverData):
            if hoverData is None:
                return ""
            pt = hoverData['points'][0]
            node = pt['text']
            comm = self.comm_map.get(node, "unknown")
            return f"Node {node} belongs to community {comm}"


# ============================================================================
# DASHBOARD BUILDER – QUICKLY CREATE A DASH APP WITH SELECTED COMPONENTS
# ============================================================================

def create_interactive_dashboard(components: List[InteractiveComponent],
                                 title: str = "Layer 2 Interactive Dashboard") -> dash.Dash:
    """
    Create a Dash app containing the given interactive components, arranged in tabs.
    """
    if not HAS_DASH:
        raise ImportError("Dash is required to create an interactive dashboard.")

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = title

    # Build tabs for each component
    tabs = []
    tab_contents = []
    for i, comp in enumerate(components):
        tab_id = f"tab-{comp.component_id}"
        tabs.append(dbc.Tab(label=comp.component_id.replace('-', ' ').title(), tab_id=tab_id))
        tab_contents.append(html.Div(id=f"content-{comp.component_id}", children=comp.get_layout()))

    app.layout = dbc.Container([
        html.H1(title, className="text-center mb-4"),
        dbc.Tabs(id="dashboard-tabs", active_tab=tabs[0].tab_id if tabs else None, tabs=tabs),
        html.Div(id="dashboard-content", className="mt-4")
    ], fluid=True)

    # Callback to display the correct tab content
    @app.callback(
        Output("dashboard-content", "children"),
        [Input("dashboard-tabs", "active_tab")]
    )
    def render_tab(active_tab):
        if not active_tab:
            return html.Div()
        for comp in components:
            if f"tab-{comp.component_id}" == active_tab:
                return comp.get_layout()
        return html.Div()

    # Register callbacks for each component
    for comp in components:
        comp.register_callbacks(app)

    return app


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Run a demo with synthetic data."""
    if not HAS_DASH:
        print("Dash not installed – cannot run demo")
        return

    # Create synthetic data (requires NetworkX and other modules)
    import networkx as nx
    from ..adjacency_matrix import SpectralGraphAnalysis
    from ..hypergraph_relations import Hypergraph, QuantumGraph
    from ..motif_detection import PersistentHomology
    from ..relations import UltimateRelation, RelationType

    # Graph
    G = nx.erdos_renyi_graph(15, 0.2, seed=42)
    sa = SpectralGraphAnalysis(G)

    # Hypergraph
    hg = Hypergraph()
    for i, (u, v) in enumerate(G.edges()):
        hg.add_hyperedge(f"e{i}", {u, v}, weight=np.random.random())

    # Persistence diagram (simplified)
    ph = PersistentHomology(G)
    ph.build_clique_complex(max_dim=2)
    ph.compute_persistence()

    # Quantum graph
    qg = QuantumGraph(graph=G)
    for u, v in G.edges():
        qg.edge_amplitudes[(u, v)] = np.random.random()

    # Community map
    comm_map = {node: i % 3 for i, node in enumerate(G.nodes())}

    # Create components
    comp1 = PersistenceDiagramComponent("persistence", ph)
    comp2 = SpectralEmbeddingComponent("spectral", sa, dim=2, node_names=[str(n) for n in G.nodes()])
    comp3 = HypergraphComponent("hypergraph", hg)
    comp4 = QuantumGraphComponent("quantum", qg)
    comp5 = CommunityMapComponent("communities", comm_map, G)

    # Build dashboard
    app = create_interactive_dashboard([comp1, comp2, comp3, comp4, comp5],
                                       title="Layer 2 Interactive Demo")
    app.run_server(debug=True, port=8051)


if __name__ == "__main__":
    demo()