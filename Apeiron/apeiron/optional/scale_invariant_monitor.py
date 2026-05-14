#!/usr/bin/env python3
"""
Scale Invariant Monitor – Mereological Holonomy for APEIRON
=============================================================
Optional module for Layer 2.

Detects fractal self‑similarity in the knowledge hypergraph: whether
the topological laws at the micro‑scale (pixel‑level) also hold at the
macro‑scale (world‑model). Uses the Hodge decomposition over different
normalisation scales to compute a scale‑invariance score. When high,
the system can "scale" knowledge directly, leading to superadditive
learning speed.

Mathematical Foundation
-----------------------
Let H be a hypergraph. For a scale parameter λ > 0, define the scaled
hypergraph H_λ by normalising the weights with a factor that depends on
λ (e.g., thresholding edges with weight > λ). For each scale, compute
the Hodge decomposition of the normalised Laplacian and extract the
harmonic dimension h_λ = dim ker Δ_λ.

A hypergraph is scale‑invariant if h_λ is constant over a range of λ
(plateau), or if the function h(λ) follows a power law h(λ) ∝ λ^{-α}
with a stable exponent α. A plateau indicates that the number of
independent harmonic components is robust under coarse‑graining, a
signature of a fractal (self‑similar) knowledge structure.

The mereological holonomy monitor:
1. Computes h(λ) for a logarithmic grid of scales.
2. Fits a power law and extracts the exponent α.
3. Measures the plateau stability (fraction of scales where h is constant).
4. Returns a scale‑invariance score ∈ [0,1].

References
----------
.. [1] Beniers, D. "17 Layers AI Model" – Superadditivity (2025)
.. [2] Carlsson, G. "Topology and Data" (2009)
.. [3] Lim, L.-H. "Hodge Laplacians on Graphs" (2015)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

try:
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
except ImportError:
    Hypergraph = None

try:
    from apeiron.layers.layer02_relational.hodge_decomposition import (
        HypergraphHodgeDecomposer
    )
except ImportError:
    HypergraphHodgeDecomposer = None


@dataclass
class ScaleProfile:
    """Profile of Hodge harmonic dimension across scales."""
    scales: List[float]
    harmonic_dimensions: List[int]
    plateau_ranges: List[Tuple[int, int]]  # (start_idx, end_idx) of plateaus
    exponent: float
    scale_invariance_score: float
    description: str


class ScaleInvariantMonitor:
    """
    Monitors scale invariance of the knowledge hypergraph.

    Parameters
    ----------
    hypergraph : Hypergraph
        The hypergraph to analyze.
    n_scales : int
        Number of scales (logarithmically spaced).
    scale_min, scale_max : float
        Range of scale parameters.
    """

    def __init__(self, hypergraph,
                 n_scales: int = 20,
                 scale_min: float = 0.01,
                 scale_max: float = 1.0):
        if Hypergraph is None:
            raise ImportError("Hypergraph module is required.")
        self.hypergraph = hypergraph
        self.n_scales = n_scales
        self.scales = np.logspace(np.log10(scale_min), np.log10(scale_max), n_scales)
        self._profile = None

    def _scaled_hypergraph(self, scale: float) -> Any:
        """
        Create a scaled version of the hypergraph by thresholding edges
        with weight < scale. This simulates coarse‑graining: only strong
        relations survive.
        """
        from copy import deepcopy
        scaled = deepcopy(self.hypergraph)
        to_remove = []
        for eid, w in scaled.weights.items():
            if w < scale:
                to_remove.append(eid)
        for eid in to_remove:
            scaled.remove_hyperedge(eid)
        return scaled

    def _harmonic_dimension(self, hypergraph) -> int:
        """
        Compute the harmonic dimension (dim ker Δ₀) using the Hodge
        decomposer, if available, else fall back to the nullity of the
        graph Laplacian.
        """
        if HypergraphHodgeDecomposer is not None:
            try:
                hhd = HypergraphHodgeDecomposer(hypergraph)
                basis = hhd.get_harmonic_basis(k=0)
                return basis.shape[1]
            except Exception:
                pass
        # Fallback: number of connected components (0‑th Betti number)
        if hasattr(hypergraph, 'betti_numbers'):
            betti = hypergraph.betti_numbers()
            return betti.get(0, 1)
        return 1

    def compute_profile(self) -> ScaleProfile:
        """
        Compute the harmonic dimension over all scales and fit a power law.
        """
        harmonic_dims = []
        for scale in self.scales:
            scaled_hg = self._scaled_hypergraph(scale)
            h = self._harmonic_dimension(scaled_hg)
            harmonic_dims.append(h)

        harmonic_dims = np.array(harmonic_dims)

        # Detect plateaus: runs of identical values
        plateau_ranges = []
        start = 0
        for i in range(1, len(harmonic_dims)):
            if harmonic_dims[i] != harmonic_dims[start]:
                if i - start >= 3:  # require at least 3 points for a plateau
                    plateau_ranges.append((start, i - 1))
                start = i
        # Last segment
        if len(harmonic_dims) - start >= 3:
            plateau_ranges.append((start, len(harmonic_dims) - 1))

        # Fit power law: h(λ) = C * λ^{-α}
        log_scales = np.log(self.scales)
        log_dims = np.log(np.maximum(harmonic_dims, 1))
        # Linear regression
        A = np.vstack([log_scales, np.ones(len(log_scales))]).T
        coeffs, residuals, rank, singular = np.linalg.lstsq(A, log_dims, rcond=None)
        exponent = -coeffs[0]  # α

        # Scale invariance score:
        # - High if there are plateaus (stable harmonic structure)
        # - High if exponent is close to 0 (no scale dependence)
        plateau_fraction = sum(end - start + 1 for start, end in plateau_ranges) / max(len(harmonic_dims), 1)
        exponent_score = np.exp(-abs(exponent))  # 1 if exponent 0, decays otherwise
        score = 0.5 * plateau_fraction + 0.5 * exponent_score

        # Description
        if score > 0.8:
            desc = (f"Strong scale invariance detected (score={score:.2f}). "
                    f"The knowledge graph is fractal: micro‑level topology "
                    f"mirrors macro‑level topology. Direct knowledge scaling "
                    f"is warranted.")
        elif score > 0.5:
            desc = (f"Moderate scale invariance (score={score:.2f}). "
                    f"Partial self‑similarity; cautious scaling possible.")
        else:
            desc = (f"Weak scale invariance (score={score:.2f}). "
                    f"Knowledge structure varies with scale; no fractal pattern.")

        self._profile = ScaleProfile(
            scales=self.scales.tolist(),
            harmonic_dimensions=harmonic_dims.tolist(),
            plateau_ranges=plateau_ranges,
            exponent=float(exponent),
            scale_invariance_score=float(score),
            description=desc,
        )
        return self._profile

    def compare_scales(self, micro_scale: float = 0.01,
                       macro_scale: float = 1.0) -> Dict[str, Any]:
        """
        Directly compare the harmonic structure at two specific scales.

        Returns a similarity measure between the two Hodge decompositions.
        """
        hg_micro = self._scaled_hypergraph(micro_scale)
        hg_macro = self._scaled_hypergraph(macro_scale)
        h_micro = self._harmonic_dimension(hg_micro)
        h_macro = self._harmonic_dimension(hg_macro)
        similarity = min(h_micro, h_macro) / max(h_micro, h_macro, 1)
        return {
            'micro_scale': micro_scale,
            'macro_scale': macro_scale,
            'micro_harmonic_dim': h_micro,
            'macro_harmonic_dim': h_macro,
            'similarity': float(similarity),
            'is_self_similar': similarity > 0.8,
        }

    def superadditivity_potential(self) -> float:
        """
        Estimate the potential for superadditive learning: if the
        knowledge graph is strongly scale‑invariant, learning at one
        scale immediately transfers to all scales.
        """
        if self._profile is None:
            self.compute_profile()
        return self._profile.scale_invariance_score


# ============================================================================
# Factory
# ============================================================================

def scale_invariance_analysis(hypergraph) -> Dict[str, Any]:
    """
    Analyze the scale invariance of a hypergraph.

    Returns a summary with the scale profile and superadditivity estimate.
    """
    monitor = ScaleInvariantMonitor(hypergraph)
    profile = monitor.compute_profile()
    comparison = monitor.compare_scales()
    return {
        'scale_profile': {
            'scales': profile.scales,
            'harmonic_dimensions': profile.harmonic_dimensions,
            'exponent': profile.exponent,
            'score': profile.scale_invariance_score,
            'description': profile.description,
        },
        'micro_macro_comparison': comparison,
        'superadditivity_potential': profile.scale_invariance_score,
    }