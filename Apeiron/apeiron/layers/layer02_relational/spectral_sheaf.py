#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spectral Sheaf Theory for the APEIRON Framework
===============================================
Layer 2 — Relational Hypergraph (Sheaf Spectral Extension)

This module implements spectral analysis on sheaf hypergraphs, including the
sheaf Laplacian, sheaf spectral clustering, and sheaf diffusion operators.
It extends the existing spectral.py module to the sheaf-theoretic setting,
enabling the detection of emergent structures through harmonic analysis
of the sheaf coboundary.

Mathematical Foundation
-----------------------
Given a sheaf F on a hypergraph H with coboundary δ, the sheaf Laplacians are:
    L⁰ = δ^T δ : C⁰(H; F) → C⁰(H; F)
    L¹ = δ δ^T : C¹(H; F) → C¹(H; F)

The spectrum of L⁰ encodes global consistency: the kernel dimension equals
dim H⁰, and the spectral gap (first nonzero eigenvalue) measures the
algebraic connectivity of the sheaf. Sheaf spectral clustering uses the
eigenvectors of L⁰ to partition vertices into globally consistent substructures.

Sheaf diffusion is governed by the heat equation ∂u/∂t = -L⁰ u, whose
solution u(t) = exp(-t L⁰) u(0) converges to the harmonic projection
as t → ∞, providing a dynamical perspective on emergence.

References
----------
.. [1] Hansen, J., Ghrist, R. "Sheaf Laplacians and Spectral Clustering" (2019)
.. [2] Beniers, D. "Categorical Foundations of the APEIRON Framework" (2025)
.. [3] Schaub, M. et al. "Signal Processing on Hypergraphs" (2020)

Author: APEIRON Framework Contributors
Version: 2.0.0 — Spectral Sheaf Theory
Date: 2026-05-14
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from itertools import combinations

try:
    from scipy.linalg import eigh, eigvalsh
    from scipy.sparse.linalg import eigsh
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.cluster import KMeans, SpectralClustering
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Try importing from within the layer
try:
    from .sheaf_hypergraph import SheafHypergraph, SheafCohomologyResult
except ImportError:
    # Standalone fallback
    SheafHypergraph = None
    SheafCohomologyResult = None


@dataclass
class SheafSpectralResult:
    """
    Result of spectral sheaf analysis.

    Parameters
    ----------
    eigenvalues : np.ndarray
        Eigenvalues of L⁰ (sorted ascending).
    eigenvectors : np.ndarray
        Corresponding eigenvectors as columns.
    harmonic_dim : int
        Dimension of the harmonic space (multiplicity of zero eigenvalue).
    spectral_gap : float
        First nonzero eigenvalue (algebraic connectivity).
    clustering_labels : Optional[np.ndarray]
        Vertex cluster assignments from spectral clustering.
    diffusion_state : Optional[np.ndarray]
        Final state after diffusion if computed.
    """
    eigenvalues: np.ndarray
    eigenvectors: np.ndarray
    harmonic_dim: int
    spectral_gap: float
    clustering_labels: Optional[np.ndarray] = None
    diffusion_state: Optional[np.ndarray] = None

    @property
    def is_connected(self) -> bool:
        """True if the sheaf is spectrally connected (exactly one zero eigenvalue)."""
        return self.harmonic_dim == 1

    def __repr__(self) -> str:
        return (
            f"SheafSpectralResult(λ₁={self.spectral_gap:.4f}, "
            f"harmonic_dim={self.harmonic_dim})"
        )


class SheafSpectralAnalyzer:
    """
    Spectral analyzer for sheaf hypergraphs.

    Computes the sheaf Laplacian spectrum, performs sheaf spectral clustering,
    and simulates sheaf diffusion. This class extends the hypergraph spectral
    analysis to account for the sheaf structure, yielding more refined
    insights into global consistency and emergent clustering.

    Parameters
    ----------
    sheaf : SheafHypergraph
        The sheaf hypergraph to analyze.

    Examples
    --------
    >>> # Assume we have a SheafHypergraph 'shg' with 3 vertices and 1 hyperedge
    >>> from layers.layer02_relational.sheaf_hypergraph import SheafHypergraph
    >>> shg = SheafHypergraph(["v1","v2","v3"], [{"v1","v2"}])
    >>> analyzer = SheafSpectralAnalyzer(shg)
    >>> result = analyzer.analyze()
    >>> result.harmonic_dim >= 1
    True
    >>> result.spectral_gap >= 0
    True
    """
    def __init__(self, sheaf):
        if SheafHypergraph is not None and not isinstance(sheaf, SheafHypergraph):
            raise TypeError("Expected a SheafHypergraph instance")
        self.sheaf = sheaf

    def analyze(self, k: int = 10) -> SheafSpectralResult:
        """
        Perform full spectral analysis of the sheaf.

        Parameters
        ----------
        k : int
            Number of eigenvalues/eigenvectors to compute (if using iterative methods).

        Returns
        -------
        SheafSpectralResult
        """
        # Get L⁰ from the sheaf
        L0 = self.sheaf.compute_sheaf_laplacian(order=0)
        n = L0.shape[0]

        if n == 0:
            return SheafSpectralResult(
                eigenvalues=np.array([]),
                eigenvectors=np.array([]),
                harmonic_dim=0,
                spectral_gap=0.0,
            )

        # Compute eigenvalues and eigenvectors
        if SCIPY_AVAILABLE:
            if n > 500:
                # Use sparse iterative method for large systems
                try:
                    from scipy.sparse import csr_matrix
                    L0_sparse = csr_matrix(L0)
                    eigenvalues, eigenvectors = eigsh(L0_sparse, k=min(k, n-1), which='SM')
                except Exception:
                    eigenvalues, eigenvectors = eigh(L0)
            else:
                eigenvalues, eigenvectors = eigh(L0)
        else:
            eigenvalues, eigenvectors = np.linalg.eigh(L0)

        # Harmonic dimension: number of (approximately) zero eigenvalues
        tol = 1e-10
        harmonic_dim = int(np.sum(eigenvalues < tol))

        # Spectral gap: first nonzero eigenvalue
        nonzero = eigenvalues[eigenvalues > tol]
        spectral_gap = nonzero[0] if len(nonzero) > 0 else 0.0

        return SheafSpectralResult(
            eigenvalues=eigenvalues,
            eigenvectors=eigenvectors,
            harmonic_dim=harmonic_dim,
            spectral_gap=spectral_gap,
        )

    def spectral_clustering(self, n_clusters: int, use_harmonic: bool = True) -> np.ndarray:
        """
        Perform sheaf spectral clustering.

        Uses the eigenvectors of L⁰ corresponding to the smallest non-harmonic
        eigenvalues to embed vertices, then applies k-means. The harmonic
        subspace is ignored if use_harmonic=False to focus on connectivity
        structure rather than global consistency.

        Parameters
        ----------
        n_clusters : int
            Number of clusters.
        use_harmonic : bool
            If True, include harmonic eigenvectors; if False, skip them
            to focus on the connectivity structure.

        Returns
        -------
        np.ndarray
            Cluster labels for each vertex cochain dimension.

        Examples
        --------
        >>> from layers.layer02_relational.sheaf_hypergraph import SheafHypergraph
        >>> shg = SheafHypergraph(["v1","v2","v3"], [{"v1","v2"}, {"v2","v3"}])
        >>> analyzer = SheafSpectralAnalyzer(shg)
        >>> labels = analyzer.spectral_clustering(2)
        >>> len(labels) == 3  # one per vertex (1-dim stalks)
        True
        """
        result = self.analyze()
        eigenvalues = result.eigenvalues
        eigenvectors = result.eigenvectors

        # Determine number of eigenvectors to use
        # Skip zero eigenvalues (harmonic) if desired
        if use_harmonic:
            start_idx = 0
        else:
            start_idx = result.harmonic_dim

        n_features = min(n_clusters, len(eigenvalues) - start_idx)
        if n_features <= 0:
            return np.zeros(eigenvectors.shape[0], dtype=int)

        embedding = eigenvectors[:, start_idx:start_idx + n_features]

        # Cluster using k-means (or spectral clustering if preferred)
        if SKLEARN_AVAILABLE:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embedding)
        else:
            # Simple clustering: project onto first eigenvector and threshold
            vec = embedding[:, 0]
            threshold = np.median(vec)
            labels = (vec > threshold).astype(int)

        return labels

    def sheaf_diffusion(self, initial_signal: np.ndarray, t: float = 1.0, steps: int = 100) -> np.ndarray:
        """
        Simulate sheaf diffusion (heat equation) on the 0-cochains.

        Solves ∂u/∂t = -L⁰ u using the matrix exponential or Euler integration.

        Parameters
        ----------
        initial_signal : np.ndarray
            Initial 0-cochain (length = dim C⁰).
        t : float
            Total diffusion time.
        steps : int
            Number of Euler steps (for the integration method).

        Returns
        -------
        np.ndarray
            Diffused cochain at time t.

        Examples
        --------
        >>> from layers.layer02_relational.sheaf_hypergraph import SheafHypergraph
        >>> shg = SheafHypergraph(["v1","v2","v3"], [{"v1","v2"}])
        >>> analyzer = SheafSpectralAnalyzer(shg)
        >>> signal = np.array([1.0, -1.0, 0.0])
        >>> diffused = analyzer.sheaf_diffusion(signal, t=10.0)
        >>> diffused.shape == signal.shape
        True
        >>> # Diffusion should bring signal towards harmonic (constant on connected components)
        >>> np.allclose(diffused, np.mean(signal), atol=0.1)
        True
        """
        L0 = self.sheaf.compute_sheaf_laplacian(order=0)
        n = L0.shape[0]
        if n == 0:
            return initial_signal.copy()

        # Use matrix exponential if scipy is available
        if SCIPY_AVAILABLE:
            from scipy.linalg import expm
            exp_Lt = expm(-t * L0)
            return exp_Lt @ initial_signal

        # Fallback: Euler integration
        dt = t / steps
        u = initial_signal.copy()
        for _ in range(steps):
            u = u - dt * (L0 @ u)
        return u

    def harmonic_projection(self, signal: np.ndarray) -> np.ndarray:
        """
        Project a signal onto the harmonic subspace (kernel of L⁰).

        This is the limit of diffusion as t → ∞.

        Parameters
        ----------
        signal : np.ndarray

        Returns
        -------
        np.ndarray
        """
        result = self.analyze()
        harm_dim = result.harmonic_dim
        if harm_dim == 0:
            return np.zeros_like(signal)
        V_harm = result.eigenvectors[:, :harm_dim]
        coeffs = V_harm.T @ signal
        return V_harm @ coeffs

    def compute_sheaf_spectral_invariants(self) -> Dict[str, float]:
        """
        Compute a set of spectral invariants for the sheaf.

        Includes:
        - harmonic dimension
        - spectral gap
        - total energy (sum of eigenvalues)
        - spectral complexity (entropy of normalized eigenvalues)
        - condition number (λ_max / λ_min nonzero)

        Returns
        -------
        Dict
        """
        result = self.analyze()
        ev = result.eigenvalues
        n = len(ev)
        if n == 0:
            return {}
        nonzero = ev[ev > 1e-12]
        invariants = {
            'harmonic_dim': result.harmonic_dim,
            'spectral_gap': result.spectral_gap,
            'total_energy': float(np.sum(ev)),
            'spectral_radius': float(np.max(ev)),
            'mean_eigenvalue': float(np.mean(ev)),
        }
        if len(nonzero) >= 2:
            invariants['condition_number'] = float(np.max(nonzero) / nonzero[0])
        else:
            invariants['condition_number'] = float('inf') if len(nonzero) == 0 else 1.0

        # Spectral entropy
        if np.sum(ev) > 1e-15:
            p = ev / np.sum(ev)
            # Avoid log(0)
            p = p[p > 0]
            invariants['spectral_entropy'] = float(-np.sum(p * np.log(p)))
        else:
            invariants['spectral_entropy'] = 0.0

        return invariants


# ============================================================================
# Integration with existing spectral.py
# ============================================================================

def combine_spectral_and_sheaf_analysis(
    hypergraph,  # Hypergraph
    sheaf: Optional[Any] = None,  # SheafHypergraph
) -> Dict[str, Any]:
    """
    Combine ordinary spectral analysis with sheaf spectral analysis.

    Parameters
    ----------
    hypergraph : Hypergraph
        The hypergraph (for standard spectral analysis).
    sheaf : Optional[SheafHypergraph]
        The sheaf structure; if None, constructs a trivial sheaf.

    Returns
    -------
    Dict with 'standard' and 'sheaf' keys.
    """
    # Standard spectral analysis (from existing spectral.py)
    try:
        from .spectral import SpectralGraphAnalysis
        sga = SpectralGraphAnalysis(hypergraph)
        standard = {
            'eigenvalues': sga.spectral_decomposition().get('eigenvalues', np.array([])).tolist(),
            'connectivity': sga.algebraic_connectivity(),
        }
    except Exception:
        standard = {'error': 'spectral analysis failed'}

    # Sheaf analysis
    if sheaf is None:
        # Create trivial sheaf with 1-dim stalks
        if SheafHypergraph is not None:
            vertices = [f"v_{v}" for v in hypergraph.vertices]
            hyperedges = [
                {f"v_{v}" for v in edge} for edge in hypergraph.edges
            ]
            sheaf = SheafHypergraph(vertices, hyperedges)
        else:
            sheaf = None

    if sheaf is not None:
        analyzer = SheafSpectralAnalyzer(sheaf)
        sheaf_inv = analyzer.compute_sheaf_spectral_invariants()
    else:
        sheaf_inv = {}

    return {
        'standard': standard,
        'sheaf': sheaf_inv,
    }


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)