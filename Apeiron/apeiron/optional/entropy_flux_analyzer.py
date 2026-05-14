#!/usr/bin/env python3
"""
Entropy Flux Analyzer – Thermodynamic Causality for the APEIRON Framework
==========================================================================
Optional module for Layer 2.

Couples the Sheaf Laplacian to entropy production. A causal arrow is only
drawn if it reduces the local free energy of the hypergraph. Time becomes
the direction in which the hypergraph "cools" towards a stable functional
unit (Layer 3). This provides a physical, observer-independent criterion
for causal directionality.

Mathematical Foundation
-----------------------
Let H be a hypergraph with sheaf F. The sheaf Laplacian L⁰ = δ^T δ acts
on 0‑cochains. The "temperature" of a vertex v is defined as the local
obstruction flux Φ(v) = ||(L⁰ s)(v)|| where s is a global section.

The free energy of the hypergraph is:
    F = U - θ S
where:
- U = Σ_v Φ(v)² (internal energy from obstruction)
- S = -Σ_v p(v) log p(v) (entropy of the attention distribution p ∝ Φ)
- θ is a parameter analogous to temperature (here, the inverse spectral gap)

A proposed causal edge e : u → v is thermodynamically valid if adding it
to the hypergraph strictly lowers the free energy: F(H ∪ {e}) < F(H).

This yields a selection principle for causal discovery that is grounded
in the intrinsic topology of the knowledge graph, not in external
statistical tests.

References
----------
.. [1] Friston, K. "The free-energy principle: a unified brain theory?"
       Nature Reviews Neuroscience (2010)
.. [2] Beniers, D. "Functorial Emergence in the APEIRON Framework" (2025)
.. [3] Hansen, J., Ghrist, R. "Sheaf Laplacians" (2019)
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
from itertools import combinations

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


@dataclass
class ThermodynamicState:
    """Thermodynamic description of a hypergraph configuration."""
    internal_energy: float
    entropy: float
    free_energy: float
    temperature: float
    flux: np.ndarray
    vertex_probabilities: np.ndarray


class EntropyFluxAnalyzer:
    """
    Analyzes causal edges through the lens of thermodynamic free energy.

    Parameters
    ----------
    hypergraph : Hypergraph
        The current knowledge hypergraph.
    theta : float, optional
        Inverse temperature (1/kT). If None, uses the inverse of the
        sheaf Laplacian spectral gap.
    """

    def __init__(self, hypergraph, theta: Optional[float] = None):
        if Hypergraph is None:
            raise ImportError("Hypergraph module is required.")
        self.hypergraph = hypergraph
        self.theta = theta  # will be set from spectral gap if None
        self._sheaf = None
        self._diffusion = None

    def _build_sheaf(self) -> SheafHypergraph:
        if self._sheaf is not None:
            return self._sheaf
        if SheafHypergraph is None:
            raise ImportError("SheafHypergraph module is required.")
        vertices = [f"v_{v}" for v in sorted(self.hypergraph.vertices)]
        hyperedges = [{f"v_{v}" for v in edge} for edge in self.hypergraph.hyperedges.values()]
        self._sheaf = SheafHypergraph(vertices, hyperedges)
        return self._sheaf

    def _build_diffusion(self) -> SheafDiffusionDynamics:
        if self._diffusion is not None:
            return self._diffusion
        if SheafDiffusionDynamics is None:
            raise ImportError("SheafDiffusionDynamics module is required.")
        self._diffusion = SheafDiffusionDynamics(self._build_sheaf())
        return self._diffusion

    def _compute_theta(self) -> float:
        """Compute the inverse temperature from the spectral gap."""
        if self.theta is not None:
            return self.theta
        try:
            from apeiron.layers.layer02_relational.spectral_sheaf import SheafSpectralAnalyzer
            ssa = SheafSpectralAnalyzer(self._build_sheaf())
            result = ssa.analyze()
            gap = result.spectral_gap
            return 1.0 / max(gap, 1e-12)
        except Exception:
            return 1.0

    def _compute_thermodynamics(self, hypergraph=None) -> ThermodynamicState:
        """
        Compute internal energy, entropy, and free energy from the
        sheaf obstruction flux.
        """
        hg = hypergraph if hypergraph is not None else self.hypergraph
        vertices = [f"v_{v}" for v in sorted(hg.vertices)]
        hyperedges = [{f"v_{v}" for v in edge} for edge in hg.hyperedges.values()]
        if not vertices:
            return ThermodynamicState(0.0, 0.0, 0.0, 1.0, np.array([]), np.array([]))

        sheaf = SheafHypergraph(vertices, hyperedges)
        diff = SheafDiffusionDynamics(sheaf)
        _, final = diff.evolve(store_trajectory=False)
        flux = final.flux

        # Internal energy U = Σ Φ(v)²
        U = float(np.sum(flux ** 2))

        # Entropy S = -Σ p(v) log p(v) where p(v) ∝ Φ(v)
        if np.sum(flux) > 1e-12:
            p = flux / np.sum(flux)
            p = p[p > 0]
            S = -float(np.sum(p * np.log(p)))
        else:
            S = 0.0
            p = np.ones(len(flux)) / max(len(flux), 1)

        theta = self._compute_theta()
        F = U - theta * S

        return ThermodynamicState(
            internal_energy=U,
            entropy=S,
            free_energy=F,
            temperature=1.0 / theta,
            flux=flux,
            vertex_probabilities=p if isinstance(p, np.ndarray) else np.array([]),
        )

    def validate_causal_edge(self, source: Any, target: Any) -> Dict[str, Any]:
        """
        Test whether adding a directed causal edge source → target is
        thermodynamically valid (lowers the free energy).

        Parameters
        ----------
        source, target : vertex identifiers

        Returns
        -------
        dict with 'valid', 'free_energy_before', 'free_energy_after',
        'delta_F', 'reason'
        """
        # Compute free energy of current hypergraph
        before = self._compute_thermodynamics(self.hypergraph)

        # Build a copy with the proposed edge added
        from copy import deepcopy
        new_hg = deepcopy(self.hypergraph)
        new_hg.add_hyperedge(f"causal_{source}_{target}_{len(new_hg.hyperedges)}",
                             {source, target}, weight=1.0)

        after = self._compute_thermodynamics(new_hg)

        delta_F = after.free_energy - before.free_energy
        valid = delta_F < 0  # edge must lower free energy

        return {
            'valid': valid,
            'free_energy_before': before.free_energy,
            'free_energy_after': after.free_energy,
            'delta_F': delta_F,
            'temperature': before.temperature,
            'reason': (
                'Edge reduces free energy — thermodynamically valid'
                if valid else
                'Edge would increase free energy — rejected'
            ),
        }

    def causal_flux_ordering(self, candidate_edges: List[Tuple[Any, Any]]) -> List[Dict[str, Any]]:
        """
        Rank candidate causal edges by their free energy reduction.
        Only edges with negative delta_F are considered valid.

        Returns a sorted list (most valid first).
        """
        results = []
        for src, tgt in candidate_edges:
            result = self.validate_causal_edge(src, tgt)
            results.append({
                'source': src,
                'target': tgt,
                **result,
            })
        # Sort: most negative delta_F first
        results.sort(key=lambda r: r['delta_F'])
        return results

    def thermodynamic_arrow_of_time(self) -> Dict[str, Any]:
        """
        Determine the global arrow of time: the direction in which the
        hypergraph's free energy spontaneously decreases.

        Returns the direction (as a list of (source, target) edges) and
        the total free energy reduction achievable.
        """
        # Try all possible directed edges between currently connected vertices
        candidate_edges = []
        for edge in self.hypergraph.hyperedges.values():
            verts = sorted(edge)
            for i in range(len(verts)):
                for j in range(i + 1, len(verts)):
                    candidate_edges.append((verts[i], verts[j]))
                    candidate_edges.append((verts[j], verts[i]))

        # Deduplicate
        candidate_edges = list(set(candidate_edges))

        ranking = self.causal_flux_ordering(candidate_edges)
        valid_edges = [r for r in ranking if r['valid']]

        total_reduction = sum(r['delta_F'] for r in valid_edges)

        return {
            'valid_edges': valid_edges,
            'total_free_energy_reduction': total_reduction,
            'num_candidates': len(candidate_edges),
            'num_valid': len(valid_edges),
            'temperature': ranking[0]['temperature'] if ranking else None,
        }


# ============================================================================
# Factory
# ============================================================================

def entropy_flux_causal_discovery(hypergraph) -> Dict[str, Any]:
    """
    Perform causal discovery using the entropy flux analyzer.

    Returns a ranked list of thermodynamically valid causal edges.
    """
    analyzer = EntropyFluxAnalyzer(hypergraph)
    return analyzer.thermodynamic_arrow_of_time()