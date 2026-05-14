#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hodge Decomposition for the APEIRON Framework
=============================================
Layer 2 — Relational Hypergraph (Hodge Theory Extension)

This module provides the discrete Helmholtz-Hodge decomposition on hypergraphs,
splitting any cochain into gradient, curl, and harmonic components. It implements
the Hodge Theorem for hypergraphs and provides the projection operators that
formalize the emergence of functional units (Layer 3) from the topological
structure of the relational layer.

Mathematical Foundation
-----------------------
Let H be a hypergraph with boundary operators ∂ₖ : Cₖ → Cₖ₋₁ and their
adjoints δₖ : Cₖ → Cₖ₊₁ (coboundary). The Hodge Laplacians are:
    Δₖ = ∂ₖ₊₁ δₖ + δₖ₋₁ ∂ₖ   (up to notational convention)

The Hodge decomposition theorem states that for any k-cochain ω:
    ω = dα + δβ + h
where dα is the gradient (exact), δβ is the curl (coexact), and h is harmonic
(Δh = 0). The three subspaces are mutually orthogonal with respect to the
inner product induced by the coboundary.

For a hypergraph sheaf, the decomposition applies to sheaf cochains, enabling
the measurement of global consistency (harmonic part) versus local flows
(gradient and curl). This directly formalizes the emergence principle:
functional units correspond to harmonic cochains in the sheaf Laplacian's kernel.

References
----------
.. [1] Beniers, D. "Functorial Emergence in the APEIRON Framework" (2025)
.. [2] Lim, L.-H. "Hodge Laplacians on Graphs" (2015)
.. [3] Schaub, M. et al. "Signal Processing on Hypergraphs" (2020)

Author: APEIRON Framework Contributors
Version: 2.0.0 — Hodge Decomposition
Date: 2026-05-14
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from itertools import combinations

try:
    from scipy.linalg import null_space, svd, orth
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


@dataclass
class HodgeDecomposition:
    """
    Result of the Helmholtz-Hodge decomposition of a cochain.

    Parameters
    ----------
    gradient : np.ndarray
        The exact component (dα).
    curl : np.ndarray
        The coexact component (δβ).
    harmonic : np.ndarray
        The harmonic component (kernel of Laplacian).
    original : np.ndarray
        The original cochain.
    residual : float
        The L² norm of the residual (original - decomposition).
    is_valid : bool
        True if the decomposition is exact (residual ≈ 0).
    """
    gradient: np.ndarray
    curl: np.ndarray
    harmonic: np.ndarray
    original: np.ndarray
    residual: float = 0.0
    is_valid: bool = True

    def __post_init__(self):
        """Verify the decomposition."""
        reconstructed = self.gradient + self.curl + self.harmonic
        self.residual = np.linalg.norm(self.original - reconstructed)
        self.is_valid = np.isclose(self.residual, 0, atol=1e-10)

    @property
    def gradient_norm(self) -> float:
        """L² norm of the gradient component."""
        return np.linalg.norm(self.gradient)

    @property
    def curl_norm(self) -> float:
        """L² norm of the curl component."""
        return np.linalg.norm(self.curl)

    @property
    def harmonic_norm(self) -> float:
        """L² norm of the harmonic component."""
        return np.linalg.norm(self.harmonic)

    @property
    def gradient_fraction(self) -> float:
        """Fraction of energy in the gradient component."""
        total = self.gradient_norm + self.curl_norm + self.harmonic_norm
        return self.gradient_norm / total if total > 1e-15 else 0.0

    @property
    def curl_fraction(self) -> float:
        """Fraction of energy in the curl component."""
        total = self.gradient_norm + self.curl_norm + self.harmonic_norm
        return self.curl_norm / total if total > 1e-15 else 0.0

    @property
    def harmonic_fraction(self) -> float:
        """Fraction of energy in the harmonic component."""
        total = self.gradient_norm + self.curl_norm + self.harmonic_norm
        return self.harmonic_norm / total if total > 1e-15 else 0.0

    def __repr__(self) -> str:
        return (
            f"HodgeDecomposition(grad={self.gradient_norm:.3f}, "
            f"curl={self.curl_norm:.3f}, "
            f"harm={self.harmonic_norm:.3f})"
        )


class HypergraphHodgeDecomposer:
    """
    Compute the Helmholtz-Hodge decomposition for cochains on a hypergraph.

    Given a hypergraph with boundary operators ∂ₖ and coboundary operators δₖ,
    this class decomposes any k-cochain into its orthogonal components:
    exact (gradient of a (k-1)-cochain), coexact (coboundary of a (k+1)-cochain),
    and harmonic (in the kernel of the Laplacian).

    The Hodge theorem guarantees that this decomposition is unique.

    Examples
    --------
    >>> # Create a simple hypergraph with 3 vertices and 1 hyperedge of size 3
    >>> from layers.layer02_relational.hypergraph import Hypergraph
    >>> hg = Hypergraph(edges=[{0,1,2}])
    >>> decomposer = HypergraphHodgeDecomposer(hg)
    >>> # Decompose a random 0-cochain (vertex signal)
    >>> signal = np.array([1.0, 2.0, 3.0])
    >>> decomp = decomposer.decompose_vertex_signal(signal)
    >>> decomp.is_valid
    True
    >>> # The harmonic component should be the projection onto the constant vector
    >>> np.allclose(decomp.harmonic, np.mean(signal) * np.ones(3))
    True
    """
    def __init__(self, hypergraph, sheaf=None):
        """
        Initialize the decomposer.

        Parameters
        ----------
        hypergraph : Hypergraph
            The hypergraph to decompose cochains on.
        sheaf : Optional[SheafHypergraph]
            An optional sheaf structure; if provided, decomposition uses
            sheaf coboundary operators.
        """
        self.hypergraph = hypergraph
        self.sheaf = sheaf

        # Build boundary operators from hypergraph
        self._build_boundary_operators()

    def _build_boundary_operators(self):
        """
        Build the boundary operators ∂ₖ for k=0,1,2 from the hypergraph's
        simplicial complex. The operators are stored as matrices.
        """
        # Extract the simplices (vertices, edges, triangles, ...)
        # For a hypergraph, edges are of various sizes; we'll consider the
        # clique complex of the 2-section graph.
        vertices = list(self.hypergraph.vertices)
        n_vertices = len(vertices)
        self.vertex_index = {v: i for i, v in enumerate(vertices)}

        # Build edge list from hyperedges (take all pairs within each hyperedge)
        edges_set = set()
        for edge in self.hypergraph.edges:
            for v1, v2 in combinations(edge, 2):
                edges_set.add((min(v1, v2), max(v1, v2)))
        edges = sorted(edges_set)
        n_edges = len(edges)
        self.edge_list = edges

        # Build triangle list from triples within hyperedges and 3-cliques in 2-section
        triangles_set = set()
        for edge in self.hypergraph.edges:
            if len(edge) >= 3:
                for triple in combinations(edge, 3):
                    triangles_set.add(tuple(sorted(triple)))
        # Also add triangles from 3-cliques across different hyperedges
        # For simplicity, only take triangles within the same hyperedge.
        triangles = sorted(triangles_set)
        n_triangles = len(triangles)
        self.triangle_list = triangles

        # Boundary ∂₁ : C₁ → C₀ (edges to vertices)
        boundary1 = np.zeros((n_vertices, n_edges))
        for j, (u, v) in enumerate(edges):
            i_u = self.vertex_index.get(u)
            i_v = self.vertex_index.get(v)
            if i_u is not None:
                boundary1[i_u, j] = -1  # standard orientation
            if i_v is not None:
                boundary1[i_v, j] = 1
        self.boundary1 = boundary1

        # Boundary ∂₂ : C₂ → C₁ (triangles to edges)
        if n_triangles > 0:
            boundary2 = np.zeros((n_edges, n_triangles))
            for k, (v1, v2, v3) in enumerate(triangles):
                # Edges of this triangle
                e1 = (min(v1, v2), max(v1, v2))
                e2 = (min(v2, v3), max(v2, v3))
                e3 = (min(v1, v3), max(v1, v3))
                for sign, e in [(1, e1), (1, e2), (-1, e3)]:
                    if e in self.edge_list:
                        j = self.edge_list.index(e)
                        boundary2[j, k] = sign
            self.boundary2 = boundary2
        else:
            self.boundary2 = np.zeros((n_edges, 0))

        # Coboundary operators: δₖ = ∂ₖ₊₁^T (up to sign)
        self.coboundary0 = self.boundary1.T  # δ₀ : C⁰ → C¹
        self.coboundary1 = self.boundary2.T  # δ₁ : C¹ → C²

        # Hodge Laplacians
        # Δ₀ = ∂₁ δ₀ = ∂₁ ∂₁^T (on vertices)
        self.laplacian0 = self.boundary1 @ self.boundary1.T
        # Δ₁ = δ₀ ∂₁ + ∂₂ δ₁ = ∂₁^T ∂₁ + ∂₂ ∂₂^T (on edges)
        if n_edges > 0:
            self.laplacian1 = self.boundary1.T @ self.boundary1 + self.boundary2 @ self.boundary2.T
        else:
            self.laplacian1 = np.zeros((0, 0))
        # Δ₂ = δ₁ ∂₂ = ∂₂^T ∂₂ (on triangles)
        self.laplacian2 = self.boundary2.T @ self.boundary2

    def decompose_vertex_signal(self, signal: np.ndarray) -> HodgeDecomposition:
        """
        Decompose a signal on vertices (0-cochain) into gradient, curl, and harmonic parts.

        For a 0-cochain ω, the decomposition is:
            ω = grad(φ) + h
        where h is harmonic (Δ₀h = 0) and grad(φ) = ∂₁ φ for some φ on edges.
        In fact, for 0-cochains, the curl component is always zero because
        δ₋₁ = 0. So the decomposition is simply gradient + harmonic.

        Parameters
        ----------
        signal : np.ndarray
            Array of length equal to the number of vertices.

        Returns
        -------
        HodgeDecomposition
        """
        n_vertices = len(self.hypergraph.vertices)
        if len(signal) != n_vertices:
            raise ValueError(f"Signal length {len(signal)} != number of vertices {n_vertices}")

        # Harmonic component: projection onto ker(Δ₀)
        # Solve Δ₀ x = 0 (i.e., find the harmonic space)
        harmonic = self._harmonic_projection(signal, self.laplacian0)

        # Gradient component: signal - harmonic (since δ₀ = ∂₁^T, grad = ∂₁ α for some α)
        gradient = signal - harmonic

        return HodgeDecomposition(
            gradient=gradient,
            curl=np.zeros_like(signal),
            harmonic=harmonic,
            original=signal,
        )

    def decompose_edge_signal(self, signal: np.ndarray) -> HodgeDecomposition:
        """
        Decompose a signal on edges (1-cochain) into gradient, curl, and harmonic parts.

        For a 1-cochain ω on edges:
            ω = grad(φ) + curl(ψ) + h
        where grad(φ) = ∂₁^T φ (coboundary of a 0-cochain),
        curl(ψ) = ∂₂ ψ (boundary of a 2-cochain),
        and h is harmonic (Δ₁h = 0).

        Parameters
        ----------
        signal : np.ndarray
            Array of length equal to the number of edges.

        Returns
        -------
        HodgeDecomposition
        """
        n_edges = self.boundary1.shape[1]
        if len(signal) != n_edges:
            raise ValueError(f"Signal length {len(signal)} != number of edges {n_edges}")

        # Gradient component: projection onto im(δ₀) = im(∂₁^T)
        gradient = self._project_onto_image(signal, self.coboundary0)

        # Curl component: projection onto im(∂₂)
        if self.boundary2.shape[1] > 0:
            curl = self._project_onto_image(signal, self.boundary2)
        else:
            curl = np.zeros_like(signal)

        # Harmonic component: projection onto ker(Δ₁)
        harmonic = self._harmonic_projection(signal, self.laplacian1)

        return HodgeDecomposition(
            gradient=gradient,
            curl=curl,
            harmonic=harmonic,
            original=signal,
        )

    def decompose_triangle_signal(self, signal: np.ndarray) -> HodgeDecomposition:
        """
        Decompose a signal on triangles (2-cochain).

        For 2-cochains, the gradient is zero (since δ₂ = 0), and the decomposition
        is curl (δ₁ ψ) + harmonic.

        Parameters
        ----------
        signal : np.ndarray
            Array of length equal to the number of triangles.

        Returns
        -------
        HodgeDecomposition
        """
        n_triangles = self.boundary2.shape[1]
        if len(signal) != n_triangles:
            raise ValueError(f"Signal length {len(signal)} != number of triangles {n_triangles}")

        # Curl component: projection onto im(δ₁) = im(∂₂^T)
        curl = self._project_onto_image(signal, self.coboundary1)

        # Harmonic component
        harmonic = self._harmonic_projection(signal, self.laplacian2)

        return HodgeDecomposition(
            gradient=np.zeros_like(signal),
            curl=curl,
            harmonic=harmonic,
            original=signal,
        )

    def decompose(self, signal: np.ndarray, k: int = 0) -> HodgeDecomposition:
        """
        General decomposition for a k-cochain.

        Parameters
        ----------
        signal : np.ndarray
            The k-cochain.
        k : int
            The degree (0 for vertices, 1 for edges, 2 for triangles).

        Returns
        -------
        HodgeDecomposition
        """
        if k == 0:
            return self.decompose_vertex_signal(signal)
        elif k == 1:
            return self.decompose_edge_signal(signal)
        elif k == 2:
            return self.decompose_triangle_signal(signal)
        else:
            raise ValueError(f"Unsupported cochain degree: {k}")

    def _harmonic_projection(self, signal: np.ndarray, laplacian: np.ndarray) -> np.ndarray:
        """
        Project a signal onto the kernel of the Laplacian (harmonic subspace).

        Parameters
        ----------
        signal : np.ndarray
        laplacian : np.ndarray
            The Hodge Laplacian matrix.

        Returns
        -------
        np.ndarray
        """
        if SCIPY_AVAILABLE:
            # Orthonormal basis for ker(Δ)
            kernel = null_space(laplacian)
        else:
            kernel = self._nullspace_qr(laplacian)

        if kernel.size == 0:
            return np.zeros_like(signal)

        # Project signal onto the kernel subspace
        coeffs = kernel.T @ signal
        return kernel @ coeffs

    def _project_onto_image(self, signal: np.ndarray, operator: np.ndarray) -> np.ndarray:
        """
        Project a signal onto the column space (image) of the given operator.

        Uses least squares: argmin_y ||operator @ y - signal||², then project = operator @ y.

        Parameters
        ----------
        signal : np.ndarray
        operator : np.ndarray
            Matrix whose image we project onto.

        Returns
        -------
        np.ndarray
        """
        if operator.shape[1] == 0:
            return np.zeros_like(signal)
        # Solve operator @ y ≈ signal
        y, _, _, _ = np.linalg.lstsq(operator, signal, rcond=None)
        return operator @ y

    def _nullspace_qr(self, A: np.ndarray) -> np.ndarray:
        """Compute nullspace using QR decomposition (fallback)."""
        if A.size == 0:
            return np.zeros((A.shape[0], 0))
        Q, R = np.linalg.qr(A.T)
        rank = np.sum(np.abs(np.diag(R)) > 1e-10)
        null_basis = Q[:, rank:]
        return null_basis

    def verify_hodge_theorem(self, k: int = 1, num_random_trials: int = 10) -> bool:
        """
        Empirically verify the Hodge decomposition theorem.

        Generates random k-cochains and checks:
        1. The decomposition sums to the original.
        2. The gradient is orthogonal to curl.
        3. The gradient is orthogonal to harmonic.
        4. The curl is orthogonal to harmonic.
        5. The harmonic part lies in the kernel of the Laplacian.

        Parameters
        ----------
        k : int
            The cochain degree to test.
        num_random_trials : int
            Number of random signals to test.

        Returns
        -------
        bool
        """
        np.random.seed(42)
        if k == 0:
            size = len(self.hypergraph.vertices)
        elif k == 1:
            size = self.boundary1.shape[1]
        elif k == 2:
            size = self.boundary2.shape[1]
        else:
            return False

        if size == 0:
            return True  # vacuously true

        for _ in range(num_random_trials):
            signal = np.random.randn(size)
            dec = self.decompose(signal, k)
            if not dec.is_valid:
                return False
            # Orthogonality checks
            dot_gc = np.dot(dec.gradient, dec.curl)
            dot_gh = np.dot(dec.gradient, dec.harmonic)
            dot_ch = np.dot(dec.curl, dec.harmonic)
            if not (abs(dot_gc) < 1e-10 and abs(dot_gh) < 1e-10 and abs(dot_ch) < 1e-10):
                return False
            # Harmonic check
            if k == 0:
                lap = self.laplacian0
            elif k == 1:
                lap = self.laplacian1
            else:
                lap = self.laplacian2
            if not np.allclose(lap @ dec.harmonic, 0, atol=1e-10):
                return False
        return True

    def get_harmonic_basis(self, k: int = 0) -> np.ndarray:
        """
        Return an orthonormal basis for the harmonic k-cochains (ker Δₖ).

        Parameters
        ----------
        k : int

        Returns
        -------
        np.ndarray
            Basis vectors as columns.
        """
        if k == 0:
            lap = self.laplacian0
        elif k == 1:
            lap = self.laplacian1
        elif k == 2:
            lap = self.laplacian2
        else:
            raise ValueError(f"Unsupported degree {k}")
        if SCIPY_AVAILABLE:
            return orth(null_space(lap))
        else:
            return self._nullspace_qr(lap)


# ============================================================================
# Integration with the APEIRON Layer 2
# ============================================================================

def hodge_decompose_hypergraph_signal(
    hypergraph, signal: np.ndarray, dimension: int = 0
) -> HodgeDecomposition:
    """
    Convenience function to compute Hodge decomposition on a hypergraph.

    Parameters
    ----------
    hypergraph : Hypergraph
    signal : np.ndarray
    dimension : int

    Returns
    -------
    HodgeDecomposition
    """
    decomposer = HypergraphHodgeDecomposer(hypergraph)
    return decomposer.decompose(signal, dimension)


def harmonic_analysis(hypergraph) -> Dict[str, Any]:
    """
    Compute harmonic spaces for all dimensions on a hypergraph.

    Returns
    -------
    Dict with keys 'dim0', 'dim1', 'dim2' giving harmonic basis dimensions.
    """
    decomposer = HypergraphHodgeDecomposer(hypergraph)
    return {
        'dim0': decomposer.get_harmonic_basis(0).shape[1],
        'dim1': decomposer.get_harmonic_basis(1).shape[1] if decomposer.boundary1.shape[1] > 0 else 0,
        'dim2': decomposer.get_harmonic_basis(2).shape[1] if decomposer.boundary2.shape[1] > 0 else 0,
    }


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)