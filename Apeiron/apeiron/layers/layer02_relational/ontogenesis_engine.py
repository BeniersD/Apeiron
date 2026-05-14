#!/usr/bin/env python3
"""
Ontogenesis Engine – Autonomous Layer Genesis for the APEIRON Framework
========================================================================
Layer 2 — Relational Hypergraph (Self-Extending Structure)

Implements the automated detection of topological singularities in the
knowledge hypergraph and the generation of new categorical layers via
Kan extensions. When the AI encounters a persistent gap in its knowledge
(a homology class that cannot be resolved within the current layer), it
autonomously triggers an "ontogenetic jump": it constructs a Kan extension
that adds a new dimension to the categorical structure, effectively
growing a new layer in the 17-layer hierarchy.

Mathematical Foundation
-----------------------
Let H be the current hypergraph (Layer 2). Its sheaf cohomology H¹(H; F)
measures global obstructions. If H¹ is non-zero and persistent under
zigzag persistence over time, the AI treats this as an "epistemic gap".

A Kan extension is the most natural way to extend a functor along another
functor. Given a diagram of categories and functors:

    A ──F──▶ C
    │
    G
    ▼
    B

the left Kan extension Lan_G(F) : B → C is the universal functor that
extends F along G. In our context, A is the current category of
observables, B is an enriched category containing new abstract concepts
(generated from the gap), and F is the current embedding into the
knowledge category C. The left Kan extension produces new relations
that bridge the gap.

We implement a simplified, finite version: given a set of "gap vertices"
(high obstruction flux points), we construct a new category object
representing the gap, and extend all existing functors to it via Kan
extension formulas.

References
----------
.. [1] Mac Lane, S. "Categories for the Working Mathematician" (1971)
       Chapter X: Kan Extensions
.. [2] Beniers, D. "17 Layers AI Model" – Ideation Document (2025)
.. [3] Beniers, D. "Functorial Emergence in the APEIRON Framework" (2025)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
import warnings

try:
    from .hypergraph import Hypergraph
except ImportError:
    Hypergraph = None

try:
    from .sheaf_hypergraph import SheafHypergraph, SheafCohomologyResult
except ImportError:
    SheafHypergraph, SheafCohomologyResult = None, None

try:
    from .category import RelationalCategory, RelationalFunctor
except ImportError:
    RelationalCategory, RelationalFunctor = None, None

try:
    from .sheaf_diffusion_dynamics import SheafDiffusionDynamics, AdaptiveThreshold
except ImportError:
    SheafDiffusionDynamics, AdaptiveThreshold = None, None


# ============================================================================
# Gap Detector
# ============================================================================

@dataclass
class EpistemicGap:
    """
    An epistemic gap detected in the knowledge hypergraph.

    Attributes:
        vertices: the set of vertices where the gap is localised.
        obstruction: the H¹ dimension (or flux) at the gap.
        persistence: whether the gap persists over time (zigzag persistence).
        description: human-readable label for logging.
    """
    vertices: Set[Any]
    obstruction: float
    persistence: bool = False
    description: str = ""


class GapDetector:
    """
    Detect epistemic gaps using sheaf cohomology and sheaf diffusion dynamics.

    A gap exists when:
    1. The sheaf cohomology H¹(H; F) is non-zero, OR
    2. The sheaf diffusion dynamics flags an epistemic singularity (high-flux
       region).
    """

    def __init__(self, hypergraph):
        self.hypergraph = hypergraph

    def detect_gaps(self) -> List[EpistemicGap]:
        """
        Detect all epistemic gaps in the current hypergraph.

        Returns a list of EpistemicGap objects (may be empty).
        """
        gaps = []

        # Method 1: Sheaf cohomology
        if SheafHypergraph is not None:
            try:
                vertices = [f"v_{v}" for v in sorted(self.hypergraph.vertices)]
                hyperedges = [{f"v_{v}" for v in edge} for edge in self.hypergraph.hyperedges.values()]
                if vertices and hyperedges:
                    shg = SheafHypergraph(vertices, hyperedges)
                    cohom = shg.compute_cohomology()
                    if cohom.h1_dimension > 0:
                        # The obstruction is global; we localise it by checking
                        # which vertices have high flux in the diffusion.
                        if SheafDiffusionDynamics is not None:
                            try:
                                diff = SheafDiffusionDynamics(shg)
                                _, final = diff.evolve(store_trajectory=False)
                                detection = diff.detect_epistemic_gradients(final)
                                if detection['epistemic_singularity']:
                                    gap_vertices = set(detection['high_flux_vertices'])
                                    gaps.append(EpistemicGap(
                                        vertices=gap_vertices,
                                        obstruction=cohom.h1_dimension,
                                        persistence=True,
                                        description=f"Epistemic singularity with H¹={cohom.h1_dimension}"
                                    ))
                            except Exception:
                                # Fallback: use all vertices
                                gaps.append(EpistemicGap(
                                    vertices=set(self.hypergraph.vertices),
                                    obstruction=cohom.h1_dimension,
                                    persistence=True,
                                    description=f"Global obstruction H¹={cohom.h1_dimension}"
                                ))
            except Exception:
                pass

        # Method 2: Simple disconnected components as gaps
        try:
            from .hypergraph import Hypergraph as HG
            n_components = HG._connected_components(self.hypergraph)
            if n_components > 1:
                gaps.append(EpistemicGap(
                    vertices=set(self.hypergraph.vertices),
                    obstruction=float(n_components - 1),
                    persistence=False,
                    description=f"{n_components} disconnected components"
                ))
        except Exception:
            pass

        return gaps


# ============================================================================
# Kan Extension Builder
# ============================================================================

class KanExtensionBuilder:
    """
    Construct a left Kan extension to bridge an epistemic gap.

    Given an existing functor F : A → C (the current knowledge embedding)
    and a new object * (representing the gap), we extend A to A' by adding
    *, and extend F to a functor F' : A' → C where F'(*) is the colimit
    (or limit, for right Kan extension) of the relevant diagram.

    In practice, we create a new vertex in the hypergraph that connects
    to all gap vertices, and define new morphisms such that the universal
    property is satisfied (approximately).
    """

    def __init__(self, hypergraph, category: Optional[RelationalCategory] = None):
        self.hypergraph = hypergraph
        self.category = category

    def build_left_kan_extension(self, gap: EpistemicGap) -> Dict[str, Any]:
        """
        Build a left Kan extension that adds a new object to the category
        and connects it to the gap vertices.

        The new object 'Gap_*' is the colimit of the diagram formed by
        the gap vertices and their relations. In the hypergraph, this
        translates to adding a new vertex and hyperedges that make it
        the "join" of the gap vertices.

        Returns a dict with the new hyperedges and morphisms to add.
        """
        gap_vertices = sorted(gap.vertices)
        new_object = f"Gap_{hash(frozenset(gap_vertices)) % 10000}"

        # New hyperedges: connect the new object to all gap vertices
        new_hyperedges = []
        for v in gap_vertices:
            new_hyperedges.append({new_object, v})

        # New morphisms in the category:
        # For each gap vertex v, we add a morphism v → new_object (the coprojection)
        new_morphisms = []
        for v in gap_vertices:
            new_morphisms.append({
                'source': v,
                'target': new_object,
                'morphism': f"coproj_{v}_to_{new_object}"
            })

        # Also add morphisms from new_object to anything that all gap vertices
        # map to (the universal property). For simplicity, we connect to
        # any common target of the gap vertices.
        if self.category is not None:
            common_targets = None
            for v in gap_vertices:
                targets = set(t for (s, t) in self.category.hom_sets.keys() if s == v)
                if common_targets is None:
                    common_targets = targets
                else:
                    common_targets &= targets
            if common_targets:
                for t in common_targets:
                    new_morphisms.append({
                        'source': new_object,
                        'target': t,
                        'morphism': f"univ_{new_object}_to_{t}"
                    })

        return {
            'new_object': new_object,
            'new_hyperedges': new_hyperedges,
            'new_morphisms': new_morphisms,
            'gap_vertices': gap_vertices,
        }


# ============================================================================
# Ontogenesis Engine
# ============================================================================

class OntogenesisEngine:
    """
    Orchestrator for autonomous layer genesis.

    Combines gap detection and Kan extension construction to automatically
    grow the knowledge hypergraph when epistemic singularities are detected.

    Parameters
    ----------
    hypergraph : Hypergraph
        The current state of knowledge.
    category : RelationalCategory, optional
        The current category structure (if available).
    auto_apply : bool
        If True, automatically apply Kan extensions to the hypergraph.
    max_jumps : int
        Maximum number of ontogenetic jumps per run.
    """

    def __init__( self, hypergraph: Any, category: Optional[Any] = None, auto_apply: bool = False, max_jumps: int = 5,):
        self.hypergraph = hypergraph
        self.category = category
        self.auto_apply = auto_apply
        self.max_jumps = max_jumps

        self.detector = GapDetector(hypergraph)
        self.builder = KanExtensionBuilder(hypergraph, category)
        self.jump_history: List[Dict[str, Any]] = []

    def check_and_evolve(self) -> Dict[str, Any]:
        """
        Check for epistemic gaps and perform ontogenetic jumps if any.

        Returns a summary of actions taken.
        """
        gaps = self.detector.detect_gaps()
        if not gaps:
            return {
                'status': 'stable',
                'message': 'No epistemic gaps detected.',
                'jumps_performed': 0,
            }

        jumps = []
        for gap in gaps[:self.max_jumps]:
            extension = self.builder.build_left_kan_extension(gap)
            jumps.append(extension)

            if self.auto_apply:
                self._apply_extension(extension)

        self.jump_history.extend(jumps)

        return {
            'status': 'evolved',
            'message': f'Performed {len(jumps)} ontogenetic jumps.',
            'jumps_performed': len(jumps),
            'jumps': jumps,
            'total_gaps_detected': len(gaps),
        }

    def _apply_extension(self, extension: Dict[str, Any]) -> None:
        """Apply a Kan extension to the hypergraph and category."""
        new_object = extension['new_object']
        # Add the new vertex
        self.hypergraph.vertices.add(new_object)

        # Add new hyperedges
        for edge in extension['new_hyperedges']:
            self.hypergraph.add_hyperedge(
                f"onto_{new_object}_{len(self.hypergraph.hyperedges)}",
                edge,
                weight=0.8
            )

        # Add new morphisms to the category
        if self.category is not None:
            self.category.add_object(new_object)
            for morph in extension.get('new_morphisms', []):
                self.category.add_morphism(
                    morph['source'],
                    morph['target'],
                    morph['morphism']
                )

    def get_ontogenetic_history(self) -> List[Dict[str, Any]]:
        """Return the history of all ontogenetic jumps."""
        return self.jump_history


# ============================================================================
# Factory
# ============================================================================

def ontogenesis_from_hypergraph(hypergraph, **kwargs) -> OntogenesisEngine:
    """
    Build an OntogenesisEngine from a Hypergraph.

    Parameters
    ----------
    hypergraph : Hypergraph
    **kwargs : passed to OntogenesisEngine constructor

    Returns
    -------
    OntogenesisEngine
    """
    category = None
    if RelationalCategory is not None:
        category = RelationalCategory()
        for v in hypergraph.vertices:
            category.add_object(v)
        for eid, verts in hypergraph.hyperedges.items():
            verts_list = list(verts)
            for i in range(len(verts_list)):
                for j in range(i + 1, len(verts_list)):
                    category.add_morphism(verts_list[i], verts_list[j], f"m_{eid}_{verts_list[i]}_{verts_list[j]}")
    return OntogenesisEngine(hypergraph, category=category, **kwargs)


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)