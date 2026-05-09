"""
metric.py – Relational metric spaces for Layer 2
=================================================
Provides:
  - RelationalMetricSpace: computes distances between relations
    (edit, graph Laplacian, Gromov‑Hausdorff, Wasserstein) and
    persistent homology of the resulting distance matrix.

All heavy dependencies are optional; missing libraries result in
log warnings and fallback values.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports – graceful degradation
# ---------------------------------------------------------------------------

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    nx = None
    HAS_NETWORKX = False

try:
    from scipy.spatial.distance import cdist
    import scipy.linalg
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import ot  # Python Optimal Transport
    HAS_POT = True
except ImportError:
    HAS_POT = False

try:
    import gudhi as gd
    HAS_GUDHI = True
except ImportError:
    HAS_GUDHI = False

try:
    from ripser import ripser
    HAS_RIPSER = True
except ImportError:
    HAS_RIPSER = False


# ============================================================================
# Helper: approximate Gromov‑Hausdorff distance
# ============================================================================

def _gromov_hausdorff_approx(
    X: np.ndarray,
    Y: np.ndarray,
    n_tries: int = 100,
) -> float:
    """
    Approximate Gromov‑Hausdorff distance between two point clouds.

    Uses random correspondences to find a minimum over n_tries random
    bijections / injections.

    Args:
        X: shape (nX, d)
        Y: shape (nY, d)
        n_tries: number of random correspondences to evaluate.

    Returns:
        Estimated Gromov‑Hausdorff distance.
    """
    if X.shape[0] == 0 or Y.shape[0] == 0:
        return float("inf")

    dX = cdist(X, X) if HAS_SCIPY else np.linalg.norm(X[:, None] - X[None, :], axis=-1)
    dY = cdist(Y, Y) if HAS_SCIPY else np.linalg.norm(Y[:, None] - Y[None, :], axis=-1)
    best_dist = float("inf")

    nX, nY = X.shape[0], Y.shape[0]
    for _ in range(n_tries):
        if nX == nY:
            perm = np.random.permutation(nX)
            dist = np.max(np.abs(dX - dY[perm][:, perm]))
        else:
            # Subsample the larger set
            if nX < nY:
                idx = np.random.choice(nY, nX, replace=False)
                dY_sub = dY[np.ix_(idx, idx)]
                dist = np.max(np.abs(dX - dY_sub))
            else:
                idx = np.random.choice(nX, nY, replace=False)
                dX_sub = dX[np.ix_(idx, idx)]
                dist = np.max(np.abs(dX_sub - dY))
        best_dist = min(best_dist, dist)
    return best_dist


# ============================================================================
# RelationalMetricSpace
# ============================================================================

@dataclass
class RelationalMetricSpace:
    """
    A metric space on a set of relations.

    Attributes:
        relations: list of objects between which distances are computed.
        distance_matrix: (n,n) numpy array of pairwise distances (computed
                         via `compute_all_distances`).
        metric_type: default distance method ('edit', 'graph', 'gromov_hausdorff',
                     'wasserstein').
    """
    relations: List[Any] = field(default_factory=list)
    distance_matrix: Optional[np.ndarray] = None
    metric_type: str = "edit"

    # ------------------------------------------------------------------------
    # Individual distance methods
    # ------------------------------------------------------------------------

    @staticmethod
    def _edit_distance(r1: Any, r2: Any) -> float:
        """Graph edit distance if r1,r2 are NetworkX graphs; Frobenius norm for arrays."""
        if HAS_NETWORKX and isinstance(r1, nx.Graph) and isinstance(r2, nx.Graph):
            try:
                return float(nx.graph_edit_distance(r1, r2))
            except Exception:
                pass
        if isinstance(r1, np.ndarray) and isinstance(r2, np.ndarray):
            return float(np.linalg.norm(r1 - r2, 'fro'))
        return 0.0

    @staticmethod
    def _graph_distance(r1: Any, r2: Any) -> float:
        """Distance based on normalized Laplacian matrices (requires NetworkX)."""
        if not HAS_NETWORKX:
            return 0.0
        if isinstance(r1, nx.Graph) and isinstance(r2, nx.Graph):
            L1 = nx.laplacian_matrix(r1).todense()
            L2 = nx.laplacian_matrix(r2).todense()
            tr1 = np.trace(L1)
            tr2 = np.trace(L2)
            if tr1 > 0:
                L1 = L1 / tr1
            if tr2 > 0:
                L2 = L2 / tr2
            return float(np.linalg.norm(L1 - L2, 2))
        return 0.0

    def _gromov_hausdorff(self, X: np.ndarray, Y: np.ndarray) -> float:
        """Wrapper around the approximation helper."""
        if not HAS_SCIPY:
            logger.warning("SciPy required for Gromov‑Hausdorff – returning 0.")
            return 0.0
        return _gromov_hausdorff_approx(X, Y)

    def _wasserstein(self, dist1: np.ndarray, dist2: np.ndarray, p: int = 2) -> float:
        """
        Wasserstein distance between two distributions (1D or 2D).

        For 1D arrays, uses scipy's wasserstein_distance; for 2D uses POT.
        """
        if not HAS_SCIPY:
            return float("inf")
        if dist1.ndim == 1 and dist2.ndim == 1:
            from scipy.stats import wasserstein_distance
            return wasserstein_distance(dist1, dist2)
        if HAS_POT:
            a = np.ones(len(dist1)) / len(dist1)
            b = np.ones(len(dist2)) / len(dist2)
            M = cdist(dist1, dist2, metric='euclidean') ** p
            return ot.emd2(a, b, M) ** (1 / p)
        logger.warning("POT not installed – using mean distance as fallback.")
        return abs(np.mean(dist1) - np.mean(dist2))

    # ------------------------------------------------------------------------
    # Compute all pairwise distances
    # ------------------------------------------------------------------------

    def compute_all_distances(self, method: Optional[str] = None) -> np.ndarray:
        """
        Compute the pairwise distance matrix for all stored relations.

        Args:
            method: distance method; if None, uses self.metric_type.

        Returns:
            (n,n) numpy array of distances.
        """
        method = method or self.metric_type
        n = len(self.relations)
        self.distance_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                ri, rj = self.relations[i], self.relations[j]
                if method == "edit":
                    dist = self._edit_distance(ri, rj)
                elif method == "graph":
                    dist = self._graph_distance(ri, rj)
                elif method == "gromov_hausdorff":
                    if isinstance(ri, np.ndarray) and isinstance(rj, np.ndarray):
                        dist = self._gromov_hausdorff(ri, rj)
                    else:
                        dist = 0.0
                elif method == "wasserstein":
                    if isinstance(ri, np.ndarray) and isinstance(rj, np.ndarray):
                        dist = self._wasserstein(ri, rj)
                    else:
                        dist = 0.0
                else:
                    dist = 0.0
                self.distance_matrix[i, j] = dist
                self.distance_matrix[j, i] = dist

        return self.distance_matrix

    # ------------------------------------------------------------------------
    # Persistent homology of the metric space
    # ------------------------------------------------------------------------

    def persistence_of_metric_space(
        self, max_dim: int = 1
    ) -> Dict[int, List[Tuple[float, float]]]:
        """
        Compute persistent homology of the distance matrix.

        Requires GUDHI or Ripser.

        Args:
            max_dim: maximum homology dimension.

        Returns:
            dict mapping dimension -> list of (birth, death) tuples.
        """
        if self.distance_matrix is None:
            logger.warning("Distance matrix not computed yet. Call compute_all_distances() first.")
            return {}

        if HAS_GUDHI:
            rips = gd.RipsComplex(
                distance_matrix=self.distance_matrix,
                max_edge_length=np.max(self.distance_matrix),
            )
            st = rips.create_simplex_tree(max_dimension=max_dim)
            st.persistence()
            diagrams = {}
            for dim in range(max_dim + 1):
                intervals = st.persistence_intervals_in_dimension(dim)
                diagrams[dim] = [(b, d) for b, d in intervals if d < float("inf")]
            return diagrams

        if HAS_RIPSER:
            result = ripser(self.distance_matrix, maxdim=max_dim)
            return {dim: result['dgms'][dim].tolist() for dim in range(len(result['dgms']))}

        logger.warning("Neither GUDHI nor Ripser available – persistent homology skipped.")
        return {}