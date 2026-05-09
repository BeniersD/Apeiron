"""
visualization_dash.py – Interactive Dash dashboards for Layer 2
===============================================================
Provides ready‑to‑run Dash apps for:
  - persistence diagrams / barcodes
  - spectral embedding
  - hypergraph visualisation
  - quantum graph exploration
  - causal graph filtering
  - community maps
  - a combined, tabbed dashboard

All components require `dash` and `plotly`; if they are missing the
module raises an ImportError when trying to create a dashboard.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Required for this module
# ---------------------------------------------------------------------------
try:
    import dash
    from dash import dcc, html, Input, Output, State
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_DASH = True
except ImportError:
    HAS_DASH = False
    logger.warning("Dash / Plotly not available – interactive dashboards disabled.")

# Import the static figure functions
try:
    from . import dashboards as _fig
except ImportError:
    _fig = None
    logger.warning("dashboards module not available – figures will be missing.")


# ============================================================================
# Persistence Diagram Component
# ============================================================================
class PersistenceDiagramComponent:
    """
    Interactive persistence diagram with hover info and click selection.
    """
    def __init__(self, component_id: str, ph, dims: Optional[List[int]] = None,
                 title: str = "Persistence Diagram"):
        self.id = component_id
        self.ph = ph
        self.dims = dims
        self.title = title
        self.figure = _fig.figure_persistence_diagram(ph, dims) if _fig else go.Figure()
        self.selected = None

    def layout(self) -> html.Div:
        return html.Div([
            dcc.Graph(id=f"{self.id}-graph", figure=self.figure,
                      config={'displayModeBar': True}),
            html.Div(id=f"{self.id}-hover", children="Hover over a point"),
            html.Div(id=f"{self.id}-selected", children="No point selected"),
        ])

    def register_callbacks(self, app: dash.Dash):
        @app.callback(
            Output(f"{self.id}-hover", "children"),
            Input(f"{self.id}-graph", "hoverData"))
        def _hover(data):
            if data is None: return "Hover over a point"
            pt = data['points'][0]
            return f"Birth: {pt['x']:.3f}, Death: {pt['y']:.3f} (H{pt.get('curveNumber',0)})"

        @app.callback(
            Output(f"{self.id}-selected", "children"),
            Input(f"{self.id}-graph", "clickData"))
        def _click(data):
            if data is None: return "No point selected"
            pt = data['points'][0]
            self.selected = (pt['x'], pt['y'], pt.get('curveNumber',0))
            return f"Selected: Birth={pt['x']:.3f}, Death={pt['y']:.3f}"


# ============================================================================
# Spectral Embedding Component
# ============================================================================
class SpectralEmbeddingComponent:
    def __init__(self, component_id: str, sa, dim: int = 2,
                 matrix_type: str = 'laplacian',
                 labels: Optional[List[int]] = None,
                 node_names: Optional[List[str]] = None):
        self.id = component_id
        self.sa = sa
        self.dim = dim
        self.matrix_type = matrix_type
        self.labels = labels
        self.node_names = node_names
        self.embed = None
        self.figure = go.Figure()
        self._update_figure()

    def _update_figure(self):
        try:
            from .spectral import SpectralType
        except ImportError:
            from .adjacency_matrix import SpectralType
        mt = SpectralType.LAPLACIAN if self.matrix_type == 'laplacian' else SpectralType.ADJACENCY
        self.embed = self.sa.spectral_embedding(self.dim, mt)
        if self.dim == 2:
            self.figure = px.scatter(x=self.embed[:,0], y=self.embed[:,1],
                                     color=self.labels, text=self.node_names,
                                     title=f"Spectral Embedding ({self.dim}D)")
        elif self.dim == 3:
            self.figure = px.scatter_3d(x=self.embed[:,0], y=self.embed[:,1],
                                        z=self.embed[:,2], color=self.labels,
                                        text=self.node_names,
                                        title=f"Spectral Embedding ({self.dim}D)")
        else:
            self.figure.add_annotation(text="Dimension not supported")

    def layout(self) -> html.Div:
        return html.Div([
            dcc.Dropdown(id=f"{self.id}-dim", options=[{'label':'2D','value':2},{'label':'3D','value':3}],
                         value=self.dim, clearable=False, style={'width':'100px'}),
            dcc.Dropdown(id=f"{self.id}-matrix",
                         options=[{'label':'Laplacian','value':'laplacian'},
                                  {'label':'Adjacency','value':'adjacency'}],
                         value=self.matrix_type, clearable=False,
                         style={'width':'150px','display':'inline-block','marginLeft':'20px'}),
            dcc.Graph(id=f"{self.id}-graph", figure=self.figure,
                      config={'modeBarButtonsToAdd':['lasso2d','select2d']}),
            html.Div(id=f"{self.id}-hover"),
            html.Div(id=f"{self.id}-selected", children="No nodes selected"),
        ])

    def register_callbacks(self, app: dash.Dash):
        @app.callback(
            Output(f"{self.id}-graph", "figure"),
            [Input(f"{self.id}-dim", "value"),
             Input(f"{self.id}-matrix", "value")])
        def _update(dim, matrix):
            self.dim = dim; self.matrix_type = matrix; self._update_figure()
            return self.figure

        @app.callback(
            Output(f"{self.id}-hover", "children"),
            Input(f"{self.id}-graph", "hoverData"))
        def _hover(data):
            if data is None: return ""
            pt = data['points'][0]
            idx = pt['pointIndex']
            name = self.node_names[idx] if self.node_names else str(idx)
            return f"Node {name}: ({pt['x']:.3f}, {pt['y']:.3f})"

        @app.callback(
            Output(f"{self.id}-selected", "children"),
            Input(f"{self.id}-graph", "selectedData"))
        def _select(data):
            if data is None or not data['points']: return "No nodes selected"
            idxs = [p['pointIndex'] for p in data['points']]
            names = [self.node_names[i] if self.node_names else str(i) for i in idxs]
            return f"Selected: {', '.join(names)}"


# ============================================================================
# Hypergraph Component
# ============================================================================
class HypergraphComponent:
    def __init__(self, component_id: str, hg, layout: str = 'spring'):
        self.id = component_id
        self.hg = hg
        self.layout = layout
        self.edge_sizes = sorted(set(len(v) for v in hg.hyperedges.values()))
        self.figure = _fig.figure_hypergraph(hg, layout) if _fig else go.Figure()

    def layout(self) -> html.Div:
        return html.Div([
            html.H4("Hypergraph Viewer"),
            dcc.Checklist(id=f"{self.id}-sizes",
                          options=[{'label':f"Size {s}",'value':s} for s in self.edge_sizes],
                          value=self.edge_sizes, inline=True),
            dcc.RangeSlider(id=f"{self.id}-weight", min=0, max=1, step=0.05,
                            value=[0,1], marks={0:'0',0.5:'0.5',1:'1'}),
            dcc.Graph(id=f"{self.id}-graph", figure=self.figure),
            html.Div(id=f"{self.id}-click"),
        ])

    def register_callbacks(self, app: dash.Dash):
        @app.callback(
            Output(f"{self.id}-graph", "figure"),
            [Input(f"{self.id}-sizes", "value"),
             Input(f"{self.id}-weight", "value")])
        def _filter(sizes, weight_range):
            min_w, max_w = weight_range
            # rebuild filtered figure manually (simplified replication of figure_hypergraph logic)
            import networkx as nx
            B = nx.Graph()
            B.add_nodes_from(self.hg.vertices, bipartite=0)
            B.add_nodes_from(self.hg.hyperedges.keys(), bipartite=1)
            for eid, verts in self.hg.hyperedges.items():
                w = self.hg.weights.get(eid, 1.0)
                if len(verts) in sizes and min_w <= w <= max_w:
                    for v in verts:
                        B.add_edge(eid, v)
            pos = nx.spring_layout(B) if self.layout == 'spring' else nx.kamada_kawai_layout(B)
            edge_trace = []
            for u, v in B.edges():
                x0, y0 = pos[u]; x1, y1 = pos[v]
                edge_trace.append(go.Scatter(x=[x0, x1, None], y=[y0, y1, None],
                                             mode='lines', line=dict(width=1, color='#888'),
                                             hoverinfo='none'))
            node_v = go.Scatter(
                x=[pos[n][0] for n in self.hg.vertices],
                y=[pos[n][1] for n in self.hg.vertices],
                mode='markers+text', text=[str(v) for v in self.hg.vertices],
                marker=dict(size=10, color='lightblue'), name='vertices')
            node_e = go.Scatter(
                x=[pos[e][0] for e in self.hg.hyperedges.keys()],
                y=[pos[e][1] for e in self.hg.hyperedges.keys()],
                mode='markers', text=[str(e) for e in self.hg.hyperedges.keys()],
                marker=dict(size=12, color='orange', symbol='square'), name='hyperedges')
            return go.Figure(data=edge_trace+[node_v, node_e]).update_layout(title="Filtered Hypergraph")

        @app.callback(
            Output(f"{self.id}-click", "children"),
            Input(f"{self.id}-graph", "clickData"))
        def _click(data):
            if data is None: return ""
            pt = data['points'][0]
            return f"Clicked: {pt.get('text','')}"


# ============================================================================
# Quantum Graph Component
# ============================================================================
class QuantumGraphComponent:
    def __init__(self, component_id: str, qg):
        self.id = component_id
        self.qg = qg
        amps = list(qg.edge_amplitudes.values()) if qg.edge_amplitudes else [0,1]
        self.amp_min, self.amp_max = min(amps), max(amps)
        self.figure = _fig.figure_quantum_graph(qg) if _fig else go.Figure()

    def layout(self) -> html.Div:
        return html.Div([
            html.H4("Quantum Graph"),
            dcc.RangeSlider(id=f"{self.id}-amp", min=self.amp_min, max=self.amp_max,
                            step=0.05, value=[self.amp_min, self.amp_max],
                            marks={0:'0',0.5:'0.5',1:'1'}),
            dcc.Graph(id=f"{self.id}-graph", figure=self.figure),
            html.Div(id=f"{self.id}-info"),
        ])

    def register_callbacks(self, app: dash.Dash):
        @app.callback(
            Output(f"{self.id}-graph", "figure"),
            Input(f"{self.id}-amp", "value"))
        def _filter(amp_range):
            return _fig.figure_quantum_graph(self.qg, show_amplitudes=True)  # simplified

        @app.callback(
            Output(f"{self.id}-info", "children"),
            Input(f"{self.id}-graph", "hoverData"))
        def _hover(data):
            if data is None: return ""
            return "Hovering over quantum graph edge"


# ============================================================================
# Causal Graph Component
# ============================================================================
class CausalGraphComponent:
    def __init__(self, component_id: str, cg):
        self.id = component_id
        self.cg = cg
        self.figure = _fig.figure_causal_graph(cg) if _fig else go.Figure()

    def layout(self) -> html.Div:
        return html.Div([
            html.H4("Causal Graph"),
            dcc.Graph(id=f"{self.id}-graph", figure=self.figure),
        ])

    def register_callbacks(self, app: dash.Dash):
        pass  # no interactive controls for now


# ============================================================================
# Community Map Component
# ============================================================================
class CommunityMapComponent:
    def __init__(self, component_id: str, comm_map: Dict[str, int], graph):
        self.id = component_id
        self.comm_map = comm_map
        self.graph = graph
        self.figure = _fig.figure_communities(comm_map, graph) if _fig else go.Figure()

    def layout(self) -> html.Div:
        comms = sorted(set(self.comm_map.values()))
        return html.Div([
            html.H4("Community Map"),
            dcc.Dropdown(id=f"{self.id}-comm",
                         options=[{'label':f'Community {c}','value':c} for c in comms],
                         value=None, placeholder="All communities"),
            dcc.Graph(id=f"{self.id}-graph", figure=self.figure),
            html.Div(id=f"{self.id}-node-info"),
        ])

    def register_callbacks(self, app: dash.Dash):
        @app.callback(
            Output(f"{self.id}-graph", "figure"),
            Input(f"{self.id}-comm", "value"))
        def _highlight(sel):
            if sel is None:
                return self.figure
            # rebuild with highlighted community
            import networkx as nx
            pos = nx.spring_layout(self.graph)
            node_x, node_y, colors, texts = [], [], [], []
            for n in self.graph.nodes():
                x, y = pos[n]
                node_x.append(x); node_y.append(y); texts.append(str(n))
                colors.append('red' if self.comm_map.get(n)==sel else 'lightblue')
            node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text',
                                    text=texts, marker=dict(size=10, color=colors),
                                    textposition="top center")
            return go.Figure(data=[node_trace]).update_layout(title=f"Community {sel} highlighted")

        @app.callback(
            Output(f"{self.id}-node-info", "children"),
            Input(f"{self.id}-graph", "hoverData"))
        def _hover(data):
            if data is None: return ""
            pt = data['points'][0]
            node = pt['text']
            comm = self.comm_map.get(node, 'unknown')
            return f"Node {node} (community {comm})"


# ============================================================================
# Dashboard builders (the old `create_*_dashboard` functions)
# ============================================================================
def _make_app(title: str, layout_func, callbacks_func) -> dash.Dash:
    if not HAS_DASH:
        raise ImportError("Dash is required for interactive dashboards.")
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = title
    app.layout = layout_func()
    callbacks_func(app)
    return app


def create_spectral_dashboard(sa, title="Spectral Analysis") -> dash.Dash:
    comp = SpectralEmbeddingComponent("spectral", sa, dim=2)
    return _make_app(title, comp.layout, comp.register_callbacks)

def create_topology_dashboard(analysis, title="Topological Analysis") -> dash.Dash:
    comp = PersistenceDiagramComponent("topo", analysis.persistence)
    return _make_app(title, comp.layout, comp.register_callbacks)

def create_hypergraph_dashboard(hg, title="Hypergraph") -> dash.Dash:
    comp = HypergraphComponent("hg", hg)
    return _make_app(title, comp.layout, comp.register_callbacks)

def create_quantum_dashboard(qg, title="Quantum Graph") -> dash.Dash:
    comp = QuantumGraphComponent("qg", qg)
    return _make_app(title, comp.layout, comp.register_callbacks)

def create_causal_dashboard(cg, title="Causal Graph") -> dash.Dash:
    comp = CausalGraphComponent("causal", cg)
    return _make_app(title, comp.layout, comp.register_callbacks)

def create_combined_dashboard(components: dict, title="Layer 2 Dashboard") -> dash.Dash:
    """
    components: dict mapping tab label -> layout function (callable returning html.Div)
    """
    if not HAS_DASH:
        raise ImportError("Dash is required.")
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.title = title
    tabs = []
    for i, (label, layout_func) in enumerate(components.items()):
        tab_id = f"tab-{i}"
        tabs.append(dbc.Tab(label=label, tab_id=tab_id))
    app.layout = dbc.Container([
        html.H1(title, className="text-center mb-4"),
        dbc.Tabs(id="tabs", active_tab=tabs[0].tab_id, tabs=tabs),
        html.Div(id="content", className="mt-4"),
    ], fluid=True)

    @app.callback(Output("content", "children"), Input("tabs", "active_tab"))
    def render_tab(active):
        for i, (label, layout_func) in enumerate(components.items()):
            if f"tab-{i}" == active:
                return layout_func()
        return html.Div()
    return app