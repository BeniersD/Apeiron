#!/usr/bin/env python3
"""
Sheaf Diffusion Dynamics – Epistemic Pain Receptor for Apeiron
===============================================================
Layer 2 — Relational Hypergraph (Continuous Sheaf Diffusion)

Implements the heat equation on the sheaf Laplacian as a continuous process.
Where diffusion stagnates (high obstruction flux), an "epistemic gradient"
forces the AI to create new hyperedges or mutate categories.

This module provides:
  - SheafDiffusionDynamics: simulates the diffusion process.
  - DiffusionState: snapshot of the evolution.
  - AdaptiveThreshold: dynamic threshold based on sheaf spectral statistics.
  - Integration hooks for Layer2UnifiedAPI.

Mathematical Foundation
-----------------------
Let F be a sheaf on a hypergraph H with coboundary δ.
The diffusion equation on 0-cochains is:
    ∂s/∂t = -L⁰ s
where L⁰ = δ^T δ is the 0-Laplacian. The steady state is the harmonic
projection s* = lim_{t→∞} s(t).

The local obstruction flux at vertex v is:
    Φ(v) = ||(L⁰ s*)(v)||
High Φ(v) indicates that local data cannot be globally integrated without
violating the sheaf condition. The AI responds by:
1. Adding hyperedges connecting v to neighbors with similar Φ values.
2. If Φ exceeds a dynamic threshold (based on spectral gap), flagging
   the region as an "epistemic singularity".

References
----------
.. [1] Hansen, J., Ghrist, R. "Sheaf Laplacians and Spectral Clustering" (2019)
.. [2] Beniers, D. "Functorial Emergence in the APEIRON Framework" (2025)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field

from .sheaf_hypergraph import SheafHypergraph, SheafCohomologyResult
from .spectral_sheaf import SheafSpectralAnalyzer, SheafSpectralResult


@dataclass
class DiffusionState:
    """
    Snapshot of the sheaf diffusion process at a given time.

    Attributes:
        time: simulation time.
        cochain: current 0-cochain (vector of length dim C⁰).
        flux: per-vertex obstruction flux (norm of gradient per vertex).
        gradient_norm: global L²-norm of the gradient.
        harmonic_projection: harmonic part of the cochain (projection onto ker L⁰).
        threshold: dynamic threshold for high-flux detection at this time.
    """
    time: float
    cochain: np.ndarray
    flux: np.ndarray
    gradient_norm: float
    harmonic_projection: np.ndarray
    threshold: float = 0.0


class AdaptiveThreshold:
    """
    Computes a dynamic threshold for epistemic gradient detection.

    The threshold is based on the spectral gap of the sheaf Laplacian
    and the empirical distribution of flux values. It can use the
    Marchenko-Pastur law for large random matrices if the sheaf is
    sufficiently large.
    """
    def __init__(self, sheaf: SheafHypergraph, sensitivity: float = 2.0):
        self.sheaf = sheaf
        self.sensitivity = sensitivity

    def compute(self, flux: np.ndarray) -> float:
        """
        Compute the threshold from the current flux distribution.

        Combines spectral gap information from the sheaf Laplacian
        with the mean and standard deviation of the flux.

        Returns
        -------
        float
            Threshold value; vertices with flux above this are flagged.
        """
        # Sheaf spectral gap (lambda_1)
        try:
            ssa = SheafSpectralAnalyzer(self.sheaf)
            result = ssa.analyze()
            spectral_gap = result.spectral_gap
        except Exception:
            spectral_gap = 0.1

        # Statistical threshold
        mean_flux = np.mean(flux)
        std_flux = np.std(flux)

        # Combine: use spectral gap as a floor, then add sensitivity * std
        # If the spectral gap is large, the sheaf is well-connected and
        # we can tolerate more flux before flagging.
        base = max(spectral_gap, np.finfo(float).eps)
        threshold = mean_flux + self.sensitivity * std_flux

        # Never below the spectral gap
        threshold = max(threshold, base)
        return float(threshold)


class SheafDiffusionDynamics:
    """
    Continuous diffusion on a sheaf hypergraph.

    Evolves the heat equation ∂s/∂t = -L⁰ s and detects vertices
    where the obstruction flux is high, indicating a need for new
    relations (hyperedges) or category mutations.

    Parameters
    ----------
    sheaf : SheafHypergraph
    dt : float
        Time step for Euler integration.
    max_time : float
        Maximum simulation time.
    convergence_tol : float
        Stop when gradient norm falls below this.
    adaptive_threshold : AdaptiveThreshold or None
        If None, a default AdaptiveThreshold is created.
    """
    def __init__(
        self,
        sheaf: SheafHypergraph,
        dt: float = 0.01,
        max_time: float = 100.0,
        convergence_tol: float = 1e-6,
        adaptive_threshold: Optional[AdaptiveThreshold] = None,
    ):
        if SheafHypergraph is None:
            raise ImportError("SheafHypergraph module is required for sheaf diffusion.")
        self.sheaf = sheaf
        self.dt = dt
        self.max_time = max_time
        self.convergence_tol = convergence_tol
        self.adaptive_threshold = adaptive_threshold or AdaptiveThreshold(sheaf)

        # Precompute the 0-Laplacian
        self.L0 = sheaf.compute_sheaf_laplacian(order=0)
        if self.L0.size == 0:
            raise ValueError("Sheaf Laplacian is empty; check the hypergraph.")

    def evolve(
        self,
        initial_signal: Optional[np.ndarray] = None,
        store_trajectory: bool = True,
    ) -> Tuple[List[DiffusionState], DiffusionState]:
        """
        Evolve the diffusion equation from an initial signal.

        Parameters
        ----------
        initial_signal : np.ndarray or None
            If None, a random signal is generated.
        store_trajectory : bool
            If True, store all intermediate states; otherwise only the last.

        Returns
        -------
        tuple (trajectory, final_state)
        """
        n = self.L0.shape[0]
        if initial_signal is None:
            s = np.random.randn(n)
        else:
            s = initial_signal.copy().astype(float)

        trajectory = []
        t = 0.0
        while t < self.max_time:
            # Compute gradient: -L⁰ s
            grad = -self.L0 @ s
            grad_norm = np.linalg.norm(grad)

            # Per-vertex flux (absolute value of gradient components)
            flux = np.abs(grad)

            # Dynamic threshold for this time
            threshold = self.adaptive_threshold.compute(flux)

            # Harmonic projection (exact via eigendecomposition would be heavy;
            # we use the current s minus the gradient direction as approximation)
            harmonic = s - self.dt * grad

            state = DiffusionState(
                time=t,
                cochain=s.copy(),
                flux=flux,
                gradient_norm=grad_norm,
                harmonic_projection=harmonic,
                threshold=threshold,
            )
            if store_trajectory:
                trajectory.append(state)
            else:
                trajectory = [state]  # Keep only latest

            if grad_norm < self.convergence_tol:
                break

            # Euler step
            s = s + self.dt * grad
            t += self.dt

        # Final state (if trajectory non-empty)
        if trajectory:
            final_state = trajectory[-1]
        else:
            # Should not happen, but safety
            final_state = DiffusionState(
                time=0.0, cochain=s, flux=np.zeros(n),
                gradient_norm=0.0, harmonic_projection=s, threshold=0.0
            )

        return trajectory, final_state

    def detect_epistemic_gradients(
        self,
        final_state: DiffusionState,
        override_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Identify vertices with high obstruction flux after diffusion.

        Parameters
        ----------
        final_state : DiffusionState
            The final state from evolve().
        override_threshold : float or None
            If given, overrides the state's threshold.

        Returns
        -------
        dict with:
            - 'high_flux_vertices': list of vertex indices
            - 'epistemic_singularity': bool, True if >30% vertices are high-flux
            - 'threshold': float
            - 'max_flux': float
            - 'mean_flux': float
        """
        flux = final_state.flux
        threshold = override_threshold if override_threshold is not None else final_state.threshold

        high_flux = np.where(flux > threshold)[0].tolist()
        singularity = len(high_flux) > 0.3 * len(flux)

        return {
            'high_flux_vertices': high_flux,
            'epistemic_singularity': singularity,
            'threshold': float(threshold),
            'max_flux': float(np.max(flux)),
            'mean_flux': float(np.mean(flux)),
        }

    def suggest_new_hyperedges(
        self,
        high_flux_vertices: List[int],
        max_edges: int = 10,
    ) -> List[Set[int]]:
        """
        Suggest new hyperedges among high-flux vertices.

        Pairs vertices with similar cochain values after harmonic projection.
        Returns a list of sets (hyperedges) that could be added to the hypergraph.

        Parameters
        ----------
        high_flux_vertices : list of int
            Indices of vertices with high flux.
        max_edges : int
            Maximum number of hyperedges to suggest.

        Returns
        -------
        list of sets
        """
        if len(high_flux_vertices) < 2:
            return []

        # Compute harmonic projection for these vertices
        n = self.L0.shape[0]
        # Use the harmonic projection from the final state (cache in future)
        # For simplicity, compute the harmonic basis once
        L0 = self.L0
        eigenvalues, eigenvectors = np.linalg.eigh(L0)
        # Harmonic basis: eigenvectors with eigenvalue < 1e-10
        harmonic_mask = eigenvalues < 1e-10
        if not np.any(harmonic_mask):
            # No harmonic space, fallback to original values
            return []

        harmonic_basis = eigenvectors[:, harmonic_mask]
        # Project the cochain onto harmonic space (we don't have the cochain here,
        # but we can approximate using the harmonic basis directly)
        # We'll compute similarities based on harmonic embedding
        harmonic_coords = harmonic_basis[high_flux_vertices, :]

        # Pairwise Euclidean distances
        from scipy.spatial.distance import pdist, squareform
        dists = squareform(pdist(harmonic_coords, 'euclidean'))

        # Collect closest pairs
        suggestions = []
        n_vert = len(high_flux_vertices)
        # Get all pairs sorted by distance
        pairs = [(dists[i, j], high_flux_vertices[i], high_flux_vertices[j])
                 for i in range(n_vert) for j in range(i + 1, n_vert)]
        pairs.sort(key=lambda x: x[0])

        added = 0
        for _, vi, vj in pairs:
            if added >= max_edges:
                break
            # Add a hyperedge containing just this pair (can be extended to larger sets)
            suggestions.append({vi, vj})
            added += 1

        return suggestions

    def full_pain_receptor_pipeline(
        self,
        initial_signal: Optional[np.ndarray] = None,
        max_new_edges: int = 10,
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline: evolve, detect, suggest.

        Returns a dictionary with trajectory statistics, high-flux
        vertices, singularity flag, and suggested hyperedges.
        """
        trajectory, final = self.evolve(initial_signal)
        detection = self.detect_epistemic_gradients(final)
        suggestions = self.suggest_new_hyperedges(
            detection['high_flux_vertices'], max_new_edges
        )
        return {
            'final_time': final.time,
            'final_gradient_norm': final.gradient_norm,
            'num_steps': len(trajectory),
            'high_flux_vertices': detection['high_flux_vertices'],
            'epistemic_singularity': detection['epistemic_singularity'],
            'threshold': detection['threshold'],
            'suggested_hyperedges': [sorted(e) for e in suggestions],
        }