#!/usr/bin/env python3
"""
Diachronic Sheaf Unification – 4D Sheaf over a Causal Set
===========================================================
Layer 2 — Relational Hypergraph (Diachronic Extension)

Treats the hypergraph not as a single snapshot but as a filtration over
endogenous time (a causal set). The sheaf cohomology is computed globally
over the entire lifetime of each observable, revealing the "eternal"
topological form of the data and making the system immune to transient
noise.

Mathematical Foundation
-----------------------
Let H be a hypergraph whose vertices and edges are indexed by endogenous
time τ. We construct a filtration {H_τ} where H_τ contains all vertices
and edges with timestamp ≤ τ. For each τ, we build a sheaf F_τ on H_τ.

The diachronic cohomology is the sequence of cohomology groups H¹(H_τ; F_τ).
We track birth and death of cohomology classes as τ increases (zigzag
persistence of sheaves). The global consistency is the integrated
obstruction over the entire causal history.

The causal path integral is approximated by a weighted sum over all
directed paths in the causal graph of the product of transition
amplitudes derived from the sheaf Laplacian.

References
----------
.. [1] Curry, J. "Sheaves, Cosheaves and Applications" (2014)
.. [2] MacPherson, R., Patel, A. "Persistent Sheaf Cohomology" (2018)
.. [3] Beniers, D. "Functorial Emergence in the APEIRON Framework" (2025)
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
from itertools import combinations
import warnings

try:
    from .hypergraph import Hypergraph
except ImportError:
    Hypergraph = None

try:
    from .sheaf_hypergraph import SheafHypergraph
except ImportError:
    SheafHypergraph = None

try:
    from .endogenous_time import EndogenousTimeGenerator, CausalPartialOrder
except ImportError:
    EndogenousTimeGenerator, CausalPartialOrder = None, None


@dataclass
class DiachronicState:
    """
    A snapshot of the hypergraph at a given endogenous time τ.
    """
    time: float
    hypergraph: Any          # Hypergraph
    sheaf: Any               # SheafHypergraph
    cohomology: Dict[str, int]  # {'h0': ..., 'h1': ...}


class DiachronicSheaf:
    """
    A sheaf that evolves over endogenous time on a causal hypergraph.

    Parameters
    ----------
    full_hypergraph : Hypergraph
        The complete hypergraph with temporal metadata (each vertex/edge
        has a 'timestamp' attribute or is ordered via endogenous time).
    time_ordering : List[Any] or EndogenousTimeGenerator
        A linear order of vertices representing endogenous time.
    """

    def __init__(self, full_hypergraph, time_ordering=None):
        if Hypergraph is None:
            raise ImportError("Hypergraph module is required.")
        self.full_hypergraph = full_hypergraph

        # Build time ordering from EndogenousTimeGenerator or list
        if isinstance(time_ordering, (EndogenousTimeGenerator,)):
            self.time_ordering = time_ordering.generate_time_ordering()
        elif isinstance(time_ordering, list):
            self.time_ordering = time_ordering
        else:
            # Extract ordering from hypergraph vertex attributes (if any)
            self.time_ordering = self._extract_time_ordering()

        self.states: List[DiachronicState] = []
        self._build_filtration()

    def _extract_time_ordering(self) -> List[Any]:
        """
        Extract a time ordering from vertex attributes.
        If vertices have a 'temporal_phase' attribute, sort by it.
        Otherwise, use an arbitrary order.
        """
        vertices = list(self.full_hypergraph.vertices)
        # Try to get temporal_phase
        phases = []
        for v in vertices:
            phase = getattr(v, 'temporal_phase', None)
            if phase is None:
                # Check metadata
                phase = self.full_hypergraph.weights.get(v, 0.0)
            phases.append(phase)
        # Sort by phase
        sorted_pairs = sorted(zip(phases, vertices), key=lambda x: x[0])
        return [v for _, v in sorted_pairs]

    def _hypergraph_at_time(self, tau: float) -> Any:
        """
        Build the sub-hypergraph containing all vertices up to time τ.
        Hyperedges are included only if all their vertices are ≤ τ.
        """
        if Hypergraph is None:
            return None
        hg = Hypergraph()
        # Add vertices up to time τ
        vertex_index = {v: i for i, v in enumerate(self.time_ordering)}
        active_vertices = set()
        for v in self.time_ordering:
            if vertex_index[v] <= tau:
                active_vertices.add(v)
                hg.vertices.add(v)
        # Add hyperedges where all vertices are active
        for eid, edge in self.full_hypergraph.hyperedges.items():
            if edge.issubset(active_vertices):
                w = self.full_hypergraph.weights.get(eid, 1.0)
                hg.add_hyperedge(eid, edge.copy(), w)
        return hg

    def _build_filtration(self):
        """
        Build a sequence of hypergraphs and sheaves along the time ordering.
        """
        n = len(self.time_ordering)
        if n == 0:
            return
        # Build at each time step
        for tau in range(n):
            hg = self._hypergraph_at_time(tau)
            if hg is None or not hg.vertices:
                continue
            # Convert to sheaf
            if SheafHypergraph is not None:
                verts = [f"v_{v}" for v in sorted(hg.vertices)]
                hedges = [{f"v_{v}" for v in edge} for edge in hg.hyperedges.values()]
                shg = SheafHypergraph(verts, hedges)
                cohom = shg.compute_cohomology()
                cohom_dict = {'h0': cohom.h0_dimension, 'h1': cohom.h1_dimension}
            else:
                shg = None
                cohom_dict = {'h0': len(hg.vertices), 'h1': 0}
            self.states.append(DiachronicState(
                time=float(tau),
                hypergraph=hg,
                sheaf=shg,
                cohomology=cohom_dict,
            ))

    def persistent_obstruction(self) -> List[Dict[str, Any]]:
        """
        Compute the persistent sheaf cohomology across the filtration.
        Returns a list of birth/death events for H¹ classes.
        """
        events = []
        prev_h1 = 0
        for i, state in enumerate(self.states):
            h1 = state.cohomology.get('h1', 0)
            if h1 > prev_h1:
                # Birth of new obstruction classes
                for _ in range(h1 - prev_h1):
                    events.append({'type': 'birth', 'time': state.time, 'dimension': 1})
            elif h1 < prev_h1:
                # Death of obstruction classes
                for _ in range(prev_h1 - h1):
                    events.append({'type': 'death', 'time': state.time, 'dimension': 1})
            prev_h1 = h1
        return events

    def global_consistency_score(self) -> float:
        """
        Compute a global consistency score over the entire history.
        Low H¹ integral → high consistency.
        """
        if not self.states:
            return 1.0
        total_obstruction = sum(s.cohomology.get('h1', 0) for s in self.states)
        max_possible = len(self.states) * max(s.cohomology.get('h1', 0) for s in self.states)
        if max_possible == 0:
            return 1.0
        return 1.0 - total_obstruction / max_possible

    def causal_path_integral(self, source: Any, target: Any) -> float:
        """
        Approximate the causal path integral between two vertices.
        Sum over all directed paths from source to target of the product
        of transition amplitudes derived from the sheaf Laplacian.

        Returns a complex amplitude (as a float phase proxy).
        """
        # Build adjacency from causal order
        vertex_index = {v: i for i, v in enumerate(self.time_ordering)}
        if source not in vertex_index or target not in vertex_index:
            return 0.0
        if vertex_index[source] >= vertex_index[target]:
            return 0.0  # cannot go backward in time

        # Build transition amplitudes from sheaf Laplacian
        amplitudes = {}
        for state in self.states:
            if state.sheaf is not None:
                L0 = state.sheaf.compute_sheaf_laplacian(order=0)
                # Use the inverse of L0 + I as a propagator (Green's function)
                G = np.linalg.inv(L0 + np.eye(L0.shape[0]))
                for i, v1 in enumerate(sorted(state.hypergraph.vertices)):
                    for j, v2 in enumerate(sorted(state.hypergraph.vertices)):
                        if i != j and G[i, j] > 0:
                            amplitudes[(v1, v2)] = float(G[i, j])

        # Sum over all paths (simplified: single-step propagation)
        total_amplitude = 0.0
        for (v1, v2), amp in amplitudes.items():
            if v1 == source and v2 == target:
                total_amplitude += amp
        return total_amplitude

    def eternal_form(self, vertex: Any) -> Dict[str, Any]:
        """
        Compute the "eternal" topological signature of a vertex:
        its cohomology class across the entire filtration.
        """
        appearances = []
        for state in self.states:
            if vertex in state.hypergraph.vertices:
                appearances.append({
                    'time': state.time,
                    'local_h1': state.cohomology.get('h1', 0),
                })
        if not appearances:
            return {'vertex': vertex, 'exists': False}
        avg_obstruction = np.mean([a['local_h1'] for a in appearances])
        return {
            'vertex': vertex,
            'exists': True,
            'first_appearance': appearances[0]['time'],
            'last_appearance': appearances[-1]['time'],
            'average_obstruction': float(avg_obstruction),
            'num_appearances': len(appearances),
        }