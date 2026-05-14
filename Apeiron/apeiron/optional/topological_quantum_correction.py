#!/usr/bin/env python3
"""
Topological Quantum Correction – Error Correction for TQFT Partition Functions
================================================================================
Optional module for Layer 2.

Provides error‑correction algorithms for the partition function of a
topological quantum field theory (TQFT) on a hypergraph. When tensor
network contraction introduces numerical noise (e.g., due to floating‑point
precision or noisy quantum simulators), this module stabilises the
computed topological invariants using the fact that the partition function
is invariant under topology‑preserving deformations.

Mathematical Foundation
-----------------------
The partition function Z(M) of a TQFT on a hypergraph M is a topological
invariant: it depends only on the homotopy type of M. If a noisy
contraction yields Z_approx, we can improve the estimate by averaging
over a family of equivalent contractions (different tree decompositions,
or gauge transformations on the vertex Hilbert spaces). The true Z is
the maximum‑likelihood estimate under a noise model where each edge
contraction adds independent Gaussian noise with variance σ².

We also implement a simple repetition code for the TQFT: we compute Z
on several copies of the hypergraph (or on perturbed versions) and
majority‑vote the resulting Betti numbers or partition function phase.

References
----------
.. [1] Witten, E. "Topological Quantum Field Theory" (1988)
.. [2] Kitaev, A. "Fault‑tolerant quantum computation by anyons" (2003)
.. [3] Beniers, D. "Quantum Topology Module for APEIRON" (2025)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from itertools import combinations


@dataclass
class TopologicalErrorCorrector:
    """
    Error correction for TQFT invariants on a hypergraph.

    Parameters
    ----------
    hypergraph : Hypergraph
        The hypergraph on which the TQFT is defined.
    noise_variance : float
        Estimated variance of the contraction noise.
    n_repetitions : int
        Number of perturbed copies to average over.
    perturbation_strength : float
        Standard deviation of random perturbations applied to hypergraph
        weights to generate copies.
    """

    hypergraph: Any  # Hypergraph
    noise_variance: float = 0.01
    n_repetitions: int = 7
    perturbation_strength: float = 0.001

    def _perturb_hypergraph(self, seed: Optional[int] = None) -> Any:
        """
        Create a perturbed copy of the hypergraph by adding small Gaussian
        noise to the edge weights.
        """
        if seed is not None:
            np.random.seed(seed)
        # We rely on the hypergraph having a copy method or we manually copy
        from copy import deepcopy
        perturbed = deepcopy(self.hypergraph)
        for eid, w in perturbed.weights.items():
            new_w = max(0.0, w + np.random.normal(0, self.perturbation_strength))
            perturbed.weights[eid] = new_w
        return perturbed

    def _compute_partition_function(self, hypergraph) -> float:
        """
        Compute the partition function (vacuum amplitude) of the TQFT on
        the given hypergraph. Uses the HypergraphTQFT if available,
        otherwise a topological proxy (Euler characteristic).
        """
        try:
            from apeiron.layers.layer02_relational.quantum_topology import HypergraphTQFT
            tqft = HypergraphTQFT(hypergraph)
            return tqft.partition_function()
        except ImportError:
            # Fallback: use Euler characteristic as a topological proxy
            n_vertices = len(hypergraph.vertices)
            n_edges = len(hypergraph.edges)
            # Simplistic: Z ≈ exp(-|χ|) where χ = V - E (for a 1‑complex)
            chi = n_vertices - n_edges
            return float(np.exp(-abs(chi)))

    def _compute_betti_numbers(self, hypergraph) -> List[int]:
        """Compute Betti numbers (as a list) using the hypergraph's method."""
        if hasattr(hypergraph, 'betti_numbers'):
            betti_dict = hypergraph.betti_numbers()
            # Sort by dimension
            max_dim = max(betti_dict.keys()) if betti_dict else 0
            return [betti_dict.get(i, 0) for i in range(max_dim + 1)]
        return []

    def correct_partition_function(self) -> Dict[str, Any]:
        """
        Estimate the true partition function by averaging over perturbed
        copies and applying a Bayesian noise model.

        Returns a dict with 'Z_raw', 'Z_corrected', 'std_dev', 'all_estimates'.
        """
        estimates = [self._compute_partition_function(self.hypergraph)]
        for i in range(self.n_repetitions - 1):
            perturbed = self._perturb_hypergraph(seed=i)
            estimates.append(self._compute_partition_function(perturbed))
        estimates = np.array(estimates)
        # Bayesian correction: shrink towards the mean by a factor depending on
        # the noise variance and the sample variance.
        sample_var = np.var(estimates) if len(estimates) > 1 else 1e-12
        # James-Stein-like shrinkage
        shrinkage = self.noise_variance / (self.noise_variance + sample_var)
        Z_raw = estimates[0]  # original
        Z_mean = np.mean(estimates)
        Z_corrected = Z_mean + (1 - shrinkage) * (Z_raw - Z_mean)
        return {
            'Z_raw': float(Z_raw),
            'Z_corrected': float(Z_corrected),
            'std_dev': float(np.std(estimates)),
            'all_estimates': estimates.tolist(),
            'n_repetitions': self.n_repetitions,
        }

    def correct_betti_numbers(self) -> Dict[str, Any]:
        """
        Correct Betti numbers by majority voting over perturbed copies.

        Returns dict with 'betti_raw', 'betti_corrected', 'votes'.
        """
        betti_raw = self._compute_betti_numbers(self.hypergraph)
        all_betti = [betti_raw]
        for i in range(self.n_repetitions - 1):
            perturbed = self._perturb_hypergraph(seed=i)
            all_betti.append(self._compute_betti_numbers(perturbed))
        # Majority vote per dimension
        max_dim = max(len(b) for b in all_betti)
        corrected = []
        for d in range(max_dim):
            values = [b[d] if d < len(b) else 0 for b in all_betti]
            # Most frequent value
            unique, counts = np.unique(values, return_counts=True)
            majority = unique[np.argmax(counts)]
            corrected.append(int(majority))
        return {
            'betti_raw': betti_raw,
            'betti_corrected': corrected,
            'all_betti': all_betti,
            'votes': [int(max(set(values), key=values.count)) for values in zip(*all_betti)],
        }

    def full_correction(self) -> Dict[str, Any]:
        """
        Run both partition function and Betti number correction.
        """
        z = self.correct_partition_function()
        betti = self.correct_betti_numbers()
        return {
            'partition_function': z,
            'betti_numbers': betti,
        }


# ============================================================================
# Repetition Code for TQFT (simplified)
# ============================================================================

class TQFTRepetitionCode:
    """
    Simple repetition code for TQFT invariants.

    Computes the topological invariant on k copies of the hypergraph
    and returns the majority result, analogous to a classical repetition
    code for quantum error correction.
    """

    def __init__(self, hypergraph, n_copies: int = 3):
        self.hypergraph = hypergraph
        self.n_copies = n_copies

    def encode(self) -> List[Any]:
        """Create n_copies identical copies of the hypergraph."""
        return [self.hypergraph] * self.n_copies

    def measure_and_correct(self, observable: Callable[[Any], Any]) -> Any:
        """
        Measure the observable on all copies and return the majority result.

        Parameters
        ----------
        observable : callable
            A function taking a hypergraph and returning a value.

        Returns
        -------
        The majority value (or the first if no clear majority).
        """
        copies = self.encode()
        results = [observable(copy) for copy in copies]
        # Majority vote for hashable types; fallback to first result
        try:
            unique, counts = np.unique(results, return_counts=True)
            return unique[np.argmax(counts)]
        except TypeError:
            return results[0]


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)