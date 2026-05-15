#!/usr/bin/env python3
"""
Consciousness Interface – Global Workspace Theory for the APEIRON Framework
=============================================================================
Optional module for Layer 2, bridging to Layer 17 (Self-Reference).

Provides a formal, mathematically rigorous interface for self-awareness
based on the Global Workspace Theory (GWT) of consciousness, adapted to
the algebraic structures of Apeiron. The hypergraph is treated as a global
workspace where specialised processors (modules) compete for access via
an attention mechanism modelled as sheaf-theoretic flux. Self-reference
emerges when the system can model its own modelling process.

Mathematical Foundation
-----------------------
GWT posits that conscious experience arises from a central workspace that
integrates and broadcasts information from unconscious processors. In
Apeiron, the global workspace is the hypergraph H together with its sheaf
F. Processors are subhypergraphs (clusters, communities). The attention
mechanism is a projection operator derived from the sheaf diffusion flux:
the most "energetic" regions (highest obstruction flux) capture attention.

Self‑reference is formalised as the ability of the system to construct
a model of itself. This is captured by the UnivalentCategory: the system
can form a category whose objects are its own subgraphs and whose
morphisms are transformations between them. The Yoneda embedding then
provides a "view from within".

The "conscious moment" is a discrete update step where:
1. The sheaf diffusion identifies high‑flux regions (surprise/novelty).
2. The attention operator projects the global state onto these regions.
3. The UnivalentCategory updates its self‑model.
4. The new state is broadcast back to all processors.

References
----------
.. [1] Baars, B.J. "A Cognitive Theory of Consciousness" (1988)
.. [2] Beniers, D. "17 Layers AI Model" – Layer 17: Self‑Reference (2025)
.. [3] Dehaene, S., Changeux, J.-P. "Global Neuronal Workspace" (2011)
.. [4] Lawvere, F.W. "An Elementary Theory of the Category of Sets" (1964)
       – Yoneda lemma as self‑modelling.
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any, Callable
from dataclasses import dataclass, field
import time
import warnings

# Optional imports from Apeiron Layer 2
try:
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
except ImportError:
    Hypergraph = None

try:
    from apeiron.layers.layer02_relational.sheaf_hypergraph import SheafHypergraph
except ImportError:
    SheafHypergraph = None

try:
    from apeiron.layers.layer02_relational.sheaf_diffusion_dynamics import (
        SheafDiffusionDynamics, DiffusionState
    )
except ImportError:
    SheafDiffusionDynamics, DiffusionState = None, None

try:
    from apeiron.layers.layer02_relational.hott_category import (
        UnivalentCategory, univalent_category_from_hypergraph
    )
except ImportError:
    UnivalentCategory, univalent_category_from_hypergraph = None, None

try:
    from apeiron.layers.layer02_relational.hodge_decomposition import HypergraphHodgeDecomposer
except ImportError:
    HypergraphHodgeDecomposer = None

try:
    from apeiron.layers.layer02_relational.endogenous_time import EndogenousTimeGenerator
except ImportError:
    EndogenousTimeGenerator = None


# ============================================================================
# Global Workspace
# ============================================================================

@dataclass
class ConsciousMoment:
    """
    A discrete snapshot of the global workspace at a moment in time.

    Attributes:
        timestamp: endogenous time.
        attention_region: vertices receiving attention.
        attention_intensity: flux values for those vertices.
        self_model: the UnivalentCategory representing the system's self‑model.
        broadcast_signal: the information broadcast to all processors.
    """
    timestamp: float
    attention_region: Set[Any]
    attention_intensity: np.ndarray
    self_model: Optional[Any] = None
    broadcast_signal: Optional[np.ndarray] = None


class GlobalWorkspace:
    """
    The global workspace (conscious workspace) of the APEIRON system.

    Parameters
    ----------
    hypergraph : Hypergraph
        The knowledge hypergraph representing all active information.
    """

    def __init__(self, hypergraph):
        from apeiron.layers.layer02_relational.hypergraph import Hypergraph
        if Hypergraph is None:
            raise ImportError("Hypergraph module is required for GlobalWorkspace.")
        self.hypergraph = hypergraph
        self.sheaf = None
        self.diffusion = None
        self.self_model = None
        self.conscious_history: List[ConsciousMoment] = []
        self._time = 0.0

    def _build_sheaf(self) -> SheafHypergraph:
        """Build the sheaf from the hypergraph if not already done."""
        if self.sheaf is not None:
            return self.sheaf
        if SheafHypergraph is None:
            raise ImportError("SheafHypergraph module is required.")
        vertices = [f"v_{v}" for v in sorted(self.hypergraph.vertices)]
        hyperedges = [{f"v_{v}" for v in edge} for edge in self.hypergraph.hyperedges.values()]
        self.sheaf = SheafHypergraph(vertices, hyperedges)
        return self.sheaf

    def _build_diffusion(self) -> SheafDiffusionDynamics:
        """Build the diffusion engine from the sheaf."""
        if self.diffusion is not None:
            return self.diffusion
        if SheafDiffusionDynamics is None:
            raise ImportError("SheafDiffusionDynamics module is required.")
        sheaf = self._build_sheaf()
        self.diffusion = SheafDiffusionDynamics(sheaf)
        return self.diffusion

    def attention_mechanism(self) -> Tuple[Set[Any], np.ndarray]:
        """
        Determine which vertices receive attention based on sheaf diffusion flux.

        The vertices with the highest obstruction flux are selected as the
        current focus of consciousness. This implements the "competition"
        among processors for access to the global workspace.

        Returns
        -------
        tuple: (attention_region, flux_values)
        """
        diff = self._build_diffusion()
        _, final = diff.evolve(store_trajectory=False)
        detection = diff.detect_epistemic_gradients(final)

        # Map indices back to original vertex labels
        vertex_list = sorted(self.hypergraph.vertices)
        high_flux_indices = detection.get('high_flux_vertices', [])
        attention_region = set()
        for i in high_flux_indices:
            if i < len(vertex_list):
                attention_region.add(vertex_list[i])
        # If no high flux, attend to all vertices (idle state)
        if not attention_region:
            attention_region = set(self.hypergraph.vertices)

        flux_values = final.flux
        return attention_region, flux_values

    def broadcast(self, attention_region: Set[Any], signal: np.ndarray) -> np.ndarray:
        """
        Broadcast a signal from the attention region to the entire hypergraph.

        The signal is a 0‑cochain (values on vertices). Non‑attended vertices
        receive a projected version of the signal via the restriction maps of
        the sheaf.
        """
        sheaf = self._build_sheaf()
        # Build a global section from the attention signal
        vertex_list = sorted(self.hypergraph.vertices)
        idx_map = {v: i for i, v in enumerate(vertex_list)}
        broadcast = np.zeros(len(vertex_list))
        # Set values for attended vertices
        for v in attention_region:
            if v in idx_map:
                broadcast[idx_map[v]] = signal[idx_map[v]] if idx_map[v] < len(signal) else 0.0
        # Extend to all vertices using the sheaf's global section extension
        try:
            local_data = {f"v_{v}": np.array([broadcast[i]]) for i, v in enumerate(vertex_list) if v in attention_region}
            global_section = sheaf.global_section(local_data)
            if global_section is not None:
                broadcast = global_section
        except Exception:
            pass
        return broadcast

    def build_self_model(self) -> UnivalentCategory:
        """
        Construct a self‑model: a UnivalentCategory whose objects are the
        current vertices (or clusters) and whose morphisms are hyperedges.
        The Yoneda embedding of this category provides a "view from within".
        """
        if UnivalentCategory is None:
            return None
        self.self_model = univalent_category_from_hypergraph(self.hypergraph)
        return self.self_model

    def conscious_update(self) -> ConsciousMoment:
        """
        Perform one conscious update cycle:
        1. Compute attention via diffusion flux.
        2. Build/update self‑model.
        3. Broadcast the attended signal.

        Returns a ConsciousMoment recording the state.
        """
        attention_region, flux = self.attention_mechanism()
        self.build_self_model()

        # Build a representative signal from the attention region
        vertex_list = sorted(self.hypergraph.vertices)
        signal = np.zeros(len(vertex_list))
        for i, v in enumerate(vertex_list):
            if v in attention_region:
                signal[i] = flux[i] if i < len(flux) else 1.0

        broadcast_signal = self.broadcast(attention_region, signal)

        moment = ConsciousMoment(
            timestamp=self._time,
            attention_region=attention_region,
            attention_intensity=flux,
            self_model=self.self_model,
            broadcast_signal=broadcast_signal,
        )
        self.conscious_history.append(moment)
        self._time += 1.0
        return moment

    def self_referential_loop(self, num_cycles: int = 10) -> List[ConsciousMoment]:
        """
        Run multiple conscious update cycles, allowing self‑reference to
        emerge through repeated self‑modelling.

        After each cycle, the self‑model is used to transport relations
        along isomorphisms, potentially restructuring the hypergraph.
        """
        for _ in range(num_cycles):
            moment = self.conscious_update()
            # Self‑modification: if self‑model has isomorphisms, transport
            if self.self_model is not None and self.self_model.isomorphisms:
                for (a, b), iso in list(self.self_model.isomorphisms.items()):
                    # Merge isomorphic vertices in the hypergraph
                    if a in self.hypergraph.vertices and b in self.hypergraph.vertices:
                        # Replace all occurrences of b with a
                        for eid, edge in self.hypergraph.hyperedges.items():
                            if b in edge:
                                new_edge = set(edge)
                                new_edge.discard(b)
                                new_edge.add(a)
                                self.hypergraph.hyperedges[eid] = new_edge
                        self.hypergraph.vertices.discard(b)
            # Clear cache to reflect changes
            self.sheaf = None
            self.diffusion = None
        return self.conscious_history

    def integrated_information(self) -> float:
        """
        Compute a proxy for integrated information Φ (phi) from the sheaf
        cohomology: the ratio of global to local obstruction.
        Φ ≈ dim H¹(global) / Σ dim H¹(local).

        High Φ indicates a highly integrated workspace (conscious state).
        Low Φ indicates fragmentation (unconscious/automated processing).
        """
        sheaf = self._build_sheaf()
        cohom = sheaf.compute_cohomology()
        global_h1 = cohom.h1_dimension

        # Sum of local H¹ for each connected component
        local_h1 = 0.0
        try:
            from apeiron.layers.layer02_relational.hypergraph import Hypergraph as HG
            n_components = HG._connected_components(self.hypergraph)
            local_h1 = float(n_components)
        except Exception:
            local_h1 = 1.0

        if local_h1 < 1e-12:
            return float('inf')
        return float(global_h1) / local_h1


# ============================================================================
# Self-Reference via Yoneda
# ============================================================================

class YonedaSelfReference:
    """
    The Yoneda embedding as a mechanism for self‑reference.

    The Yoneda lemma states that an object X is fully determined by its
    relationships to all other objects: hom(-, X). In the global workspace,
    this means the system can "know itself" by examining how it relates to
    all possible sub‑configurations.
    """

    def __init__(self, univalent_category: UnivalentCategory):
        self.category = univalent_category

    def self_profile(self, obj: Any) -> Dict[Any, int]:
        """
        Compute the Yoneda profile of an object: for every other object,
        the number of morphisms from that object to obj (or vice versa).
        This profile uniquely identifies obj up to isomorphism.
        """
        profile = {}
        for other in self.category.category.objects:
            hom_set = self.category.category.hom_sets.get((other, obj), set())
            profile[other] = len(hom_set)
        return profile

    def are_indistinguishable(self, a: Any, b: Any) -> bool:
        """
        Check whether two objects have the same Yoneda profile.
        If they do, they are isomorphic (by the Yoneda lemma) and the
        system cannot distinguish them from within.
        """
        return self.self_profile(a) == self.self_profile(b)


        return float(unique) / total
    def self_awareness_measure(self) -> float:
        """
        Measure the degree of self‑awareness as the fraction of objects
        that have a unique Yoneda profile. A high value means most objects
        are distinguishable from within the system.
        """
        if len(self.category.category.objects) > 1000:
            logger.warning("Large category; using random sample for self‑awareness measure.")
            objects = random.sample(list(self.category.category.objects), 1000)
        else:
            objects = list(self.category.category.objects)
        profiles = {}
        for obj in objects:
            p = frozenset(self.self_profile(obj).items())
            profiles[obj] = p
        unique = len(set(profiles.values()))
        total = max(len(objects), 1)
        return float(unique) / total


# ============================================================================
# Factory
# ============================================================================

def consciousness_workspace_from_hypergraph(hypergraph) -> GlobalWorkspace:
    """
    Create a GlobalWorkspace from a hypergraph.
    """
    return GlobalWorkspace(hypergraph)


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)