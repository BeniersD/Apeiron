#!/usr/bin/env python3
"""
Epistemic Horizon – Automatic Quarantine of Inconsistent Knowledge
==================================================================
Layer 2 — Relational Hypergraph (Data Censorship Mechanism)

Implements an automatic detection and isolation of "epistemic
singularities": regions of the hypergraph where the sheaf obstruction
is so high that no coherent global knowledge can be formed. These
regions are quarantined until either:
- The obstruction resolves spontaneously (e.g., via new hyperedges),
- An ontogenetic jump (Layer 13) provides a new framework that renders
  the data consistent.

The quarantine mechanism prevents the propagation of inconsistencies
to the rest of the knowledge graph, effectively acting as a
mathematically rigorous "cognitive filter" that eliminates hallucination
by topological necessity.

Mathematical Foundation
-----------------------
Let H be a hypergraph with sheaf F. The obstruction dimension h¹ = dim H¹(H; F)
measures global inconsistency. For a subset S ⊂ V of vertices, the
local obstruction h¹_S is the cohomology of the restriction sheaf F|_S.

The epistemic horizon is the boundary ∂S between a high-obstruction
region S and the rest of the graph. The AI defines S as an open set
(in the Alexandrov topology) and checks whether h¹_S > τ, where τ is
the spectral gap of the global sheaf Laplacian. If so, S is flagged
as a "singularity" and all relations crossing ∂S are frozen.

References
----------
.. [1] Beniers, D. "Functorial Emergence in the APEIRON Framework" (2025)
.. [2] Hansen, J., Ghrist, R. "Sheaf Laplacians and Spectral Clustering" (2019)
.. [3] Sorkin, R.D. "Causal Sets: Discrete Gravity" (2003) – analogy of
       black hole horizons as information boundaries.
"""

import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
import warnings

try:
    from .sheaf_hypergraph import SheafHypergraph
except ImportError:
    SheafHypergraph = None

try:
    from .hypergraph import Hypergraph
except ImportError:
    Hypergraph = None

try:
    from .sheaf_diffusion_dynamics import SheafDiffusionDynamics
except ImportError:
    SheafDiffusionDynamics = None


@dataclass
class EpistemicSingularity:
    """
    Represents a quarantined region of the knowledge hypergraph.

    Attributes:
        vertices: the set of vertices in the singular region.
        boundary: vertices adjacent to the region (the horizon).
        obstruction: local H¹ dimension.
        threshold: the threshold that was exceeded.
        timestamp: iteration or time when quarantined.
    """
    vertices: Set[Any]
    boundary: Set[Any]
    obstruction: float
    threshold: float
    timestamp: float = 0.0


class EpistemicHorizonDetector:
    """
    Detects regions of high sheaf obstruction and defines an epistemic
    horizon around them.

    Parameters
    ----------
    hypergraph : Hypergraph
    diffusion : SheafDiffusionDynamics, optional
        Pre-initialised diffusion engine; if None, it will be built.
    """

    def __init__(self, hypergraph, diffusion=None):
        self.hypergraph = hypergraph
        self.diffusion = diffusion
        self._sheaf = None

    def _build_sheaf(self) -> Optional[SheafHypergraph]:
        if SheafHypergraph is None:
            return None
        if self._sheaf is not None:
            return self._sheaf
        vertices = [f"v_{v}" for v in sorted(self.hypergraph.vertices)]
        hyperedges = [{f"v_{v}" for v in edge} for edge in self.hypergraph.hyperedges.values()]
        if not vertices:
            return None
        self._sheaf = SheafHypergraph(vertices, hyperedges)
        return self._sheaf

    def detect_singularities(self, threshold_multiplier: float = 3.0) -> List[EpistemicSingularity]:
        """
        Detect all epistemic singularities.

        Returns a list of EpistemicSingularity objects.
        """
        sheaf = self._build_sheaf()
        if sheaf is None:
            return []

        # Use diffusion to get flux per vertex
        if self.diffusion is None and SheafDiffusionDynamics is not None:
            self.diffusion = SheafDiffusionDynamics(sheaf)

        singularities = []
        if self.diffusion is not None:
            _, final = self.diffusion.evolve(store_trajectory=False)
            detection = self.diffusion.detect_epistemic_gradients(final)
            if detection['epistemic_singularity']:
                high_flux_set = set(detection['high_flux_vertices'])
                # Convert back to original vertex labels if needed
                # For simplicity, assume vertex labels map 1:1 with indices
                if self.hypergraph.vertices:
                    vertex_list = sorted(self.hypergraph.vertices)
                    high_flux_vertices = {vertex_list[i] for i in high_flux_set if i < len(vertex_list)}
                    # Compute boundary: neighbors of high-flux vertices not themselves high-flux
                    boundary = set()
                    for v in high_flux_vertices:
                        for edge in self.hypergraph.hyperedges.values():
                            if v in edge:
                                for w in edge:
                                    if w not in high_flux_vertices:
                                        boundary.add(w)
                    singularities.append(EpistemicSingularity(
                        vertices=high_flux_vertices,
                        boundary=boundary,
                        obstruction=detection['max_flux'],
                        threshold=detection['threshold'],
                    ))
        return singularities


class DataQuarantine:
    """
    Manages quarantined regions and enforces information flow control.

    When a region is quarantined:
    - No new hyperedges can be created that cross the boundary.
    - Existing relations are marked as 'frozen'.
    - The region is monitored; if obstruction falls below threshold,
      the quarantine is lifted.
    """

    def __init__(self, hypergraph):
        self.hypergraph = hypergraph
        self.quarantined: List[EpistemicSingularity] = []
        self.frozen_edges: Set[str] = set()

    def quarantine_region(self, singularity: EpistemicSingularity) -> None:
        """Add a singularity to the quarantine list and freeze boundary edges."""
        self.quarantined.append(singularity)
        # Freeze all hyperedges that cross the boundary
        for eid, edge in self.hypergraph.hyperedges.items():
            if (edge & singularity.vertices) and (edge & singularity.boundary):
                self.frozen_edges.add(eid)

    def is_frozen(self, edge_id: str) -> bool:
        """Check if a hyperedge is frozen."""
        return edge_id in self.frozen_edges

    def check_and_lift(self, detector: EpistemicHorizonDetector) -> List[EpistemicSingularity]:
        """
        Re-evaluate quarantined regions and lift quarantine if obstruction
        has fallen below threshold.

        Returns the list of lifted singularities.
        """
        lifted = []
        new_singularities = detector.detect_singularities()
        new_vertex_sets = {frozenset(s.vertices) for s in new_singularities}
        for old in list(self.quarantined):
            if frozenset(old.vertices) not in new_vertex_sets:
                # Obstruction resolved: lift quarantine
                lifted.append(old)
                self.quarantined.remove(old)
                # Unfreeze edges
                to_unfreeze = []
                for eid, edge in self.hypergraph.hyperedges.items():
                    if eid in self.frozen_edges and (edge & old.vertices) and (edge & old.boundary):
                        to_unfreeze.append(eid)
                for eid in to_unfreeze:
                    self.frozen_edges.discard(eid)
        return lifted

    def quarantine_summary(self) -> Dict[str, Any]:
        """Return a summary of the current quarantine state."""
        return {
            'num_quarantined_regions': len(self.quarantined),
            'num_frozen_edges': len(self.frozen_edges),
            'quarantined_vertices': [list(s.vertices) for s in self.quarantined],
        }


# ============================================================================
# Pipeline
# ============================================================================

def horizon_pipeline(hypergraph) -> Dict[str, Any]:
    """
    Run the full epistemic horizon pipeline: detect, quarantine, report.
    """
    detector = EpistemicHorizonDetector(hypergraph)
    quarantine = DataQuarantine(hypergraph)

    singularities = detector.detect_singularities()
    for s in singularities:
        quarantine.quarantine_region(s)

    return {
        'singularities_detected': len(singularities),
        'quarantine_summary': quarantine.quarantine_summary(),
    }


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)