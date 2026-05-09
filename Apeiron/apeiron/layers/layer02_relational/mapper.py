"""
mapper.py – Mapper algorithm for topological data analysis
===========================================================
Provides the `Mapper` class, which applies the Mapper algorithm
(Singh, Mémoli, Carlsson) to a point cloud with one or more lens
functions.  The result is a graph (simplicial complex) that captures
the topological structure of the data.

If kmapper is available, the mapping is computed; otherwise the module
raises an informative ImportError when trying to run the algorithm.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports
# ---------------------------------------------------------------------------
try:
    import kmapper as km
    HAS_KMAPPER = True
except ImportError:
    HAS_KMAPPER = False
    logger.warning("kmapper not available – Mapper will not run.")

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    nx = None
    HAS_NETWORKX = False

try:
    import dash
    from dash import dcc, html
    HAS_DASH = True
except ImportError:
    HAS_DASH = False

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# ============================================================================
# Mapper
# ============================================================================

class Mapper:
    """
    Apply the Mapper algorithm to data.

    Parameters
    ----------
    data : 2D numpy array, shape (n_points, n_features)
        The data point cloud.
    lens : list of 1D numpy arrays
        One or more lens functions (filters) on the data; each must have
        length equal to the number of points.
    cover : optional
        A cover object (e.g. from kmapper) defining intervals.
    clusterer : optional
        A clustering object (e.g. sklearn.cluster.DBSCAN).
    """

    def __init__(
        self,
        data: np.ndarray,
        lens: List[np.ndarray],
        cover: Optional[Any] = None,
        clusterer: Optional[Any] = None,
    ) -> None:
        if not HAS_KMAPPER:
            raise ImportError(
                "kmapper is required to run the Mapper algorithm. "
                "Install with: pip install kmapper"
            )
        self.data = data
        self.lens = lens
        self.cover = cover
        self.clusterer = clusterer
        self.mapper_obj = None
        self.graph: Optional[Any] = None       # result graph from kmapper
        self._dash_app: Optional[Any] = None

    # ------------------------------------------------------------------------
    # Run the algorithm
    # ------------------------------------------------------------------------
    def run(self) -> Any:
        """
        Execute the Mapper algorithm and store the result.

        Returns the kmapper graph object.
        """
        mapper = km.KeplerMapper(verbose=0)
        # Stack lens functions into a 2D array (n_points, n_lenses)
        lens_array = np.column_stack(self.lens)
        self.graph = mapper.map(
            lens_array,
            self.data,
            cover=self.cover,
            clusterer=self.clusterer,
        )
        self.mapper_obj = mapper
        logger.info("Mapper algorithm completed successfully.")
        return self.graph

    # ------------------------------------------------------------------------
    # Visualisation
    # ------------------------------------------------------------------------
    def visualize(
        self,
        interactive: bool = False,
        path_html: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Visualise the Mapper graph.

        Parameters
        ----------
        interactive : bool
            If True, return a Dash app (if Dash available) or open in browser.
        path_html : str, optional
            When `interactive=False`, the static HTML file to save.
            If None, a temporary file is opened in the browser.

        Returns
        -------
        Dash app if interactive=True and Dash is available; otherwise None.
        """
        if self.graph is None or self.mapper_obj is None:
            logger.warning("No Mapper graph to visualise; call run() first.")
            return None

        if interactive and HAS_DASH:
            # Build a simple Dash app that displays the kmapper HTML
            html_str = self.mapper_obj.visualize(self.graph)
            app = dash.Dash(__name__)
            app.layout = html.Div([
                html.H1("Mapper Graph"),
                html.Iframe(srcDoc=html_str, width="100%", height="800"),
            ])
            self._dash_app = app
            return app

        # Non‑interactive: use kmapper's built‑in HTML export
        if path_html is None:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
                path_html = tmp.name
        self.mapper_obj.visualize(self.graph, path_html=path_html)
        logger.info(f"Mapper graph saved to {path_html}")
        # optionally open in browser (if in a notebook)
        try:
            import webbrowser
            webbrowser.open(path_html)
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------------
    # Static graph (NetworkX) for later analysis
    # ------------------------------------------------------------------------
    def to_networkx(self) -> Optional[Any]:
        """
        Convert the kmapper result graph to a NetworkX graph, if possible.
        The kmapper graph has 'nodes' and 'links'; we build an undirected
        graph with node attributes.
        """
        if self.graph is None:
            return None
        if not HAS_NETWORKX:
            logger.warning("NetworkX not available; cannot convert.")
            return None
        G = nx.Graph()
        for node_id, node_data in self.graph['nodes'].items():
            G.add_node(node_id, **node_data)
        for link in self.graph['links']:
            G.add_edge(link['source'], link['target'])
        return G