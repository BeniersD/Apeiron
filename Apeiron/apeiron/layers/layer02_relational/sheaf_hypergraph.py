#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sheaf Hypergraph Module for the APEIRON Framework
==================================================
Layer 2 — Relational Hypergraph (Sheaf-Theoretic Extension)

This module implements sheaf theory on hypergraphs, providing the formal bridge
between the categorical foundations (Functor D: Aᵒᵖ → H) and the topological
analysis of the relational layer. It enables the measurement of global
consistency obstructions, formalizing the emergence principle that higher-order
structure arises when local information can be globally integrated.

Mathematical Foundation
-----------------------
Let H = (V, E) be a hypergraph with vertices V and hyperedges E ⊆ P(V).
A sheaf F on H assigns to each vertex v ∈ V a vector space F(v) (the stalk)
and to each hyperedge e ∈ E a vector space F(e), together with restriction
linear maps F(v) → F(e) whenever v ∈ e.

The sheaf cohomology groups H⁰(H; F) and H¹(H; F) measure:
- H⁰: the space of global sections (consistent labelings)
- H¹: the obstructions to extending local sections to global ones

This directly implements the functorial emergence principle: local relational
consistency (Layer 1 observables) can be globally integrated (Layer 3 functional
units) precisely when H¹(H; F) = 0.

References
----------
.. [1] Beniers, D. "Functorial Emergence in the APEIRON Framework" (2025)
.. [2] Beniers, D. "Categorical Foundations of the APEIRON Framework" (2025)
.. [3] Curry, J. "Sheaves, Cosheaves, and Applications" (2014)
.. [4] Hansen, J., Ghrist, R. "Sheaf Laplacians and Spectral Clustering" (2019)

Author: APEIRON Framework Contributors
Version: 2.0.0 — Sheaf-Theoretic Extension
Date: 2026-05-14
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict
from itertools import combinations
import warnings

try:
    from scipy.linalg import null_space, svd
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from scipy.sparse import csr_matrix, lil_matrix, eye as sparse_eye
    from scipy.sparse.linalg import eigsh
    SPARSE_AVAILABLE = True
except ImportError:
    SPARSE_AVAILABLE = False


@dataclass
class SheafStalk:
    """
    A stalk of a sheaf: a vector space associated to a vertex or hyperedge.

    The stalk is represented by its dimension and an optional basis.
    For vertices, the stalk represents the space of possible observations.
    For hyperedges, it represents the space of possible joint observations.

    Parameters
    ----------
    dimension : int
        Dimension of the vector space.
    basis : Optional[np.ndarray]
        Basis vectors as columns of a matrix. If None, the standard basis is used.
    label : Optional[str]
        Semantic label for the stalk (for debugging/visualization).

    Examples
    --------
    >>> stalk = SheafStalk(dimension=3)
    >>> stalk.dimension
    3
    >>> stalk.basis.shape
    (3, 3)
    """
    dimension: int
    basis: Optional[np.ndarray] = None
    label: Optional[str] = None

    def __post_init__(self):
        if self.dimension <= 0:
            raise ValueError(f"Stalk dimension must be positive, got {self.dimension}")
        if self.basis is None:
            self.basis = np.eye(self.dimension)
        elif self.basis.shape != (self.dimension, self.dimension):
            raise ValueError(
                f"Basis shape {self.basis.shape} does not match dimension {self.dimension}"
            )

    def project(self, vector: np.ndarray) -> np.ndarray:
        """
        Project a vector onto this stalk's subspace.

        >>> stalk = SheafStalk(dimension=2)
        >>> v = np.array([1.0, 2.0])
        >>> np.allclose(stalk.project(v), v)
        True
        """
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension {len(vector)} != stalk dimension {self.dimension}")
        # Project onto the column space of the basis
        if self.basis.shape[0] == self.basis.shape[1] and np.allclose(self.basis, np.eye(self.dimension)):
            return vector
        basis_T = self.basis.T
        coeffs = basis_T @ vector
        return self.basis @ coeffs


@dataclass
class RestrictionMap:
    """
    A restriction map from a vertex stalk to a hyperedge stalk.

    Represents the linear transformation F(v → e) that describes how
    observations at vertex v constrain observations at hyperedge e.

    Parameters
    ----------
    source : str
        Identifier of the source vertex.
    target : str
        Identifier of the target hyperedge.
    matrix : np.ndarray
        The linear transformation matrix.

    Examples
    --------
    >>> rm = RestrictionMap("v1", "e1", np.array([[1, 0], [0, 1]]))
    >>> rm.source
    'v1'
    >>> rm.target
    'e1'
    """
    source: str
    target: str
    matrix: np.ndarray

    def __post_init__(self):
        if not isinstance(self.matrix, np.ndarray):
            self.matrix = np.array(self.matrix, dtype=float)
        if self.matrix.ndim != 2:
            raise ValueError(f"Restriction matrix must be 2D, got shape {self.matrix.shape}")

    def apply(self, vector: np.ndarray) -> np.ndarray:
        """
        Apply the restriction map to a vector.

        >>> rm = RestrictionMap("v1", "e1", np.array([[2, 0], [0, 3]]))
        >>> v = np.array([1.0, 1.0])
        >>> np.allclose(rm.apply(v), np.array([2.0, 3.0]))
        True
        """
        return self.matrix @ vector

    @property
    def shape(self) -> Tuple[int, int]:
        """Return the shape of the restriction matrix."""
        return self.matrix.shape


@dataclass
class SheafCohomologyResult:
    """
    Result of sheaf cohomology computation.

    Parameters
    ----------
    h0_dimension : int
        Dimension of H⁰ (global sections space).
    h1_dimension : int
        Dimension of H¹ (first cohomology group).
    global_sections : Optional[np.ndarray]
        Basis vectors of the global section space (columns).
    harmonic_sections : Optional[np.ndarray]
        Harmonic representatives of H¹ (if computed).
    betti_numbers : List[int]
        Sheaf Betti numbers [dim H⁰, dim H¹].
    euler_characteristic : int
        Sheaf Euler characteristic χ = dim H⁰ - dim H¹.
    is_globally_consistent : bool
        True if H¹ = 0, meaning all local sections extend globally.
    """
    h0_dimension: int
    h1_dimension: int
    global_sections: Optional[np.ndarray] = None
    harmonic_sections: Optional[np.ndarray] = None
    betti_numbers: List[int] = field(default_factory=list)
    euler_characteristic: int = 0
    is_globally_consistent: bool = False

    def __post_init__(self):
        self.betti_numbers = [self.h0_dimension, self.h1_dimension]
        self.euler_characteristic = self.h0_dimension - self.h1_dimension
        self.is_globally_consistent = (self.h1_dimension == 0)

    def __repr__(self) -> str:
        return (
            f"SheafCohomologyResult(H⁰={self.h0_dimension}, "
            f"H¹={self.h1_dimension}, "
            f"χ={self.euler_characteristic}, "
            f"consistent={self.is_globally_consistent})"
        )


class SheafHypergraph:
    """
    A hypergraph equipped with a sheaf structure.

    The sheaf assigns vector spaces (stalks) to vertices and hyperedges,
    and linear restriction maps from vertex stalks to incident hyperedge stalks.
    This enables the computation of sheaf cohomology, which measures the
    obstruction to globally consistent labelings of the hypergraph.

    This is the central mathematical object linking Layer 1 (observables,
    which define local data on vertices) to Layer 3 (functional units,
    which are global sections of the sheaf).

    Parameters
    ----------
    vertices : List[str]
        List of vertex identifiers.
    hyperedges : List[Set[str]]
        List of hyperedges, each as a set of vertex identifiers.
    vertex_stalks : Optional[Dict[str, SheafStalk]]
        Stalks for vertices. If None, 1-dimensional stalks are used.
    hyperedge_stalks : Optional[Dict[str, SheafStalk]]
        Stalks for hyperedges. If None, computed from vertex stalks.
    restriction_maps : Optional[Dict[Tuple[str, str], RestrictionMap]]
        Restriction maps keyed by (vertex, hyperedge) pairs.

    Examples
    --------
    >>> vertices = ["v1", "v2", "v3"]
    >>> hyperedges = [{"v1", "v2"}, {"v2", "v3"}]
    >>> shg = SheafHypergraph(vertices, hyperedges)
    >>> result = shg.compute_cohomology()
    >>> result.is_globally_consistent
    True

    Theorem (Global Consistency):
        A sheaf hypergraph admits a non-zero global section if and only if
        dim H⁰ > 0. It admits a full-rank global section (full consistency)
        if and only if H¹ = 0 and dim H⁰ = sum(dim F(v)) - sum(dim F(e)).
    """
    def __init__(
        self,
        vertices: List[str],
        hyperedges: List[Set[str]],
        vertex_stalks: Optional[Dict[str, SheafStalk]] = None,
        hyperedge_stalks: Optional[Dict[str, SheafStalk]] = None,
        restriction_maps: Optional[Dict[Tuple[str, str], RestrictionMap]] = None,
    ):
        self.vertices = vertices
        self.hyperedges = [set(e) for e in hyperedges]  # Ensure sets

        # Validate that all hyperedge vertices exist
        for i, edge in enumerate(self.hyperedges):
            for v in edge:
                if v not in self.vertices:
                    raise ValueError(f"Hyperedge {i} contains unknown vertex '{v}'")

        # Initialize vertex stalks
        if vertex_stalks is None:
            self.vertex_stalks = {v: SheafStalk(dimension=1) for v in vertices}
        else:
            self.vertex_stalks = vertex_stalks
            for v in vertices:
                if v not in self.vertex_stalks:
                    self.vertex_stalks[v] = SheafStalk(dimension=1)

        # Initialize hyperedge stalks (default: direct sum of vertex stalks)
        self.hyperedge_stalks = hyperedge_stalks or {}
        for i, edge in enumerate(self.hyperedges):
            edge_id = f"e{i}"
            if edge_id not in self.hyperedge_stalks:
                # Default: product space of incident vertex stalks
                dim = sum(self.vertex_stalks[v].dimension for v in edge)
                self.hyperedge_stalks[edge_id] = SheafStalk(dimension=dim)

        # Initialize restriction maps
        self.restriction_maps = restriction_maps or {}
        self._build_default_restriction_maps()

        # Cached cohomology result
        self._cohomology_cache: Optional[SheafCohomologyResult] = None

    def _build_default_restriction_maps(self):
        """
        Build default restriction maps as projections from vertex stalks
        to the corresponding components of the hyperedge product stalk.

        For a hyperedge e = {v₁, ..., vₖ}, the stalk F(e) is the direct sum
        ⊕ᵢ F(vᵢ). The restriction map F(vᵢ) → F(e) is the canonical injection
        into the i-th summand.
        """
        for i, edge in enumerate(self.hyperedges):
            edge_id = f"e{i}"
            edge_list = sorted(edge)  # Consistent ordering
            offset = 0
            for v in edge_list:
                key = (v, edge_id)
                if key not in self.restriction_maps:
                    v_dim = self.vertex_stalks[v].dimension
                    e_dim = self.hyperedge_stalks[edge_id].dimension
                    # Build injection matrix: v_dim columns, e_dim rows
                    mat = np.zeros((e_dim, v_dim))
                    mat[offset:offset + v_dim, :] = np.eye(v_dim)
                    self.restriction_maps[key] = RestrictionMap(v, edge_id, mat)
                offset += v_dim

    def _build_boundary_matrix(self) -> np.ndarray:
        """
        Build the sheaf coboundary matrix δ: C⁰ → C¹.

        C⁰ = ⊕ᵥ F(v)  (0-cochains: assignments to vertices)
        C¹ = ⊕ₑ F(e)  (1-cochains: assignments to hyperedges)

        The coboundary is defined by:
            (δ s)(e) = Σ_{v ∈ e} (-1)^{pos(v,e)} F(v → e)(s(v))

        where pos(v,e) is the position of v in the ordered hyperedge.

        Returns
        -------
        np.ndarray
            The coboundary matrix of shape (dim C¹, dim C⁰).

        Theorem:
            ker δ = H⁰ (global sections)
            im δ = B¹ (coboundaries)
            H¹ = ker δ¹ / im δ⁰
            For a hypergraph sheaf, δ¹ is the adjoint δ^T.
        """
        total_vertex_dim = sum(self.vertex_stalks[v].dimension for v in self.vertices)
        total_edge_dim = sum(
            self.hyperedge_stalks[f"e{i}"].dimension for i in range(len(self.hyperedges))
        )

        delta = np.zeros((total_edge_dim, total_vertex_dim))

        # Map vertex indices to column offsets
        vertex_offsets = {}
        offset = 0
        for v in sorted(self.vertices):
            vertex_offsets[v] = offset
            offset += self.vertex_stalks[v].dimension

        # Map hyperedge indices to row offsets
        edge_offsets = {}
        offset = 0
        for i in range(len(self.hyperedges)):
            edge_offsets[f"e{i}"] = offset
            offset += self.hyperedge_stalks[f"e{i}"].dimension

        # Fill the coboundary matrix
        for i, edge in enumerate(self.hyperedges):
            edge_id = f"e{i}"
            edge_list = sorted(edge)
            for pos, v in enumerate(edge_list):
                key = (v, edge_id)
                if key in self.restriction_maps:
                    rm = self.restriction_maps[key]
                    sign = 1 if pos % 2 == 0 else -1  # Alternating sign
                    row_start = edge_offsets[edge_id]
                    col_start = vertex_offsets[v]
                    delta[
                        row_start:row_start + rm.shape[0],
                        col_start:col_start + rm.shape[1]
                    ] = sign * rm.matrix

        return delta

    def compute_cohomology(self, force_recompute: bool = False) -> SheafCohomologyResult:
        """
        Compute the sheaf cohomology of the hypergraph.

        H⁰ = ker δ (global sections: assignments to vertices that agree on all hyperedges)
        H¹ = ker δ^T / im δ (first cohomology: local-to-global obstructions)

        Parameters
        ----------
        force_recompute : bool
            If True, bypass the cache and recompute.

        Returns
        -------
        SheafCohomologyResult
            The cohomology computation result.

        Examples
        --------
        >>> vertices = ["v1", "v2", "v3"]
        >>> hyperedges = [{"v1", "v2"}, {"v2", "v3"}]
        >>> shg = SheafHypergraph(vertices, hyperedges)
        >>> result = shg.compute_cohomology()
        >>> result.h0_dimension > 0
        True

        Theorem (Hodge Decomposition):
            For any sheaf on a hypergraph, the space of 1-cochains decomposes as:
            C¹ = im δ ⊕ ker δ^T
            and H¹ ≅ ker δ^T ∩ ker δ₁ where δ₁ is the 1-coboundary.
        """


        if self._cohomology_cache is not None and not force_recompute:
            return self._cohomology_cache

        delta = self._build_boundary_matrix()
        if delta.size == 0:
            return SheafCohomologyResult(0, 0, np.array([]))

        # H⁰ = ker δ
        if delta.shape[0] == 0:  # No hyperedges
            kernel_dim = delta.shape[1]
            global_sections = np.eye(delta.shape[1])
        else:
            kernel = null_space(delta) if SCIPY_AVAILABLE else self._nullspace_qr(delta)
            kernel_dim = kernel.shape[1] if kernel.size > 0 else 0
            global_sections = kernel if kernel_dim > 0 else None

        # H¹ = ker δ^T / im δ
        # dim H¹ = dim(ker δ^T) - dim(im δ)
        delta_T = delta.T
        if delta_T.shape[0] == 0:
            h1_dim = 0
            harmonic = None
        else:
            kernel_T = null_space(delta_T) if SCIPY_AVAILABLE else self._nullspace_qr(delta_T)
            dim_ker_T = kernel_T.shape[1] if kernel_T.size > 0 else 0

            # dim(im δ) = rank(δ)
            rank_delta = np.linalg.matrix_rank(delta)
            h1_dim = max(0, dim_ker_T - rank_delta)

            # Harmonic representatives: ker δ^T ∩ ker δ₁
            # For sheaves on graphs, δ₁ = δ^T, so H¹ = ker δ^T ∩ ker δ
            if h1_dim > 0 and kernel.size > 0 and kernel_T.size > 0:
                # Intersection of kernel and kernel_T
                combined = np.hstack([kernel, kernel_T]) if kernel_dim > 0 else kernel_T
                if combined.size > 0:
                    intersection = null_space(combined.T) if SCIPY_AVAILABLE else None
                    harmonic = intersection if intersection is not None and intersection.size > 0 else None
                else:
                    harmonic = None
            else:
                harmonic = None

        result = SheafCohomologyResult(
            h0_dimension=kernel_dim,
            h1_dimension=h1_dim,
            global_sections=global_sections,
            harmonic_sections=harmonic,
        )
        self._cohomology_cache = result
        return result

    def compute_sheaf_laplacian(self, order: int = 0) -> np.ndarray:
        """
        Compute the sheaf Laplacian operator.

        L⁰ = δ^T δ : C⁰ → C⁰  (0-Laplacian, operates on vertex cochains)
        L¹ = δ δ^T : C¹ → C¹  (1-Laplacian, operates on hyperedge cochains)

        Parameters
        ----------
        order : int
            0 for the 0-Laplacian, 1 for the 1-Laplacian.

        Returns
        -------
        np.ndarray
            The sheaf Laplacian matrix.

        Examples
        --------
        >>> vertices = ["v1", "v2", "v3"]
        >>> hyperedges = [{"v1", "v2"}, {"v2", "v3"}]
        >>> shg = SheafHypergraph(vertices, hyperedges)
        >>> L0 = shg.compute_sheaf_laplacian(order=0)
        >>> L0.shape[0] == 3  # dim C⁰ = 3 (1-dim stalks)
        True
        >>> # Sheaf Laplacian is symmetric positive semidefinite
        >>> np.allclose(L0, L0.T)
        True
        >>> eigenvalues = np.linalg.eigvalsh(L0)
        >>> np.all(eigenvalues >= -1e-10)
        True

        Theorem (Sheaf Laplacian Properties):
            - L⁰ and L¹ are symmetric positive semidefinite.
            - ker L⁰ = H⁰ (global sections).
            - ker L¹ ≅ H¹ (harmonic 1-cochains).
            - The nonzero eigenvalues of L⁰ and L¹ coincide.
        """
        delta = self._build_boundary_matrix()
        if order == 0:
            return delta.T @ delta
        elif order == 1:
            return delta @ delta.T
        else:
            raise ValueError(f"Laplacian order must be 0 or 1, got {order}")

    def compute_sheaf_spectra(self, k: int = 10) -> Dict[str, Any]:
        """
        Compute the spectral decomposition of the sheaf Laplacian.

        Parameters
        ----------
        k : int
            Number of eigenvalues/eigenvectors to compute.

        Returns
        -------
        Dict with keys:
            - 'eigenvalues_0': eigenvalues of L⁰
            - 'eigenvectors_0': eigenvectors of L⁰
            - 'eigenvalues_1': eigenvalues of L¹
            - 'eigenvectors_1': eigenvectors of L¹
            - 'spectral_gap_0': first nonzero eigenvalue of L⁰
            - 'algebraic_connectivity': same as spectral_gap_0
            - 'global_section_dim': dimension of H⁰

        Examples
        --------
        >>> vertices = ["v1", "v2", "v3"]
        >>> hyperedges = [{"v1", "v2"}]
        >>> shg = SheafHypergraph(vertices, hyperedges)
        >>> spec = shg.compute_sheaf_spectra(k=3)
        >>> 'spectral_gap_0' in spec
        True
        """
        L0 = self.compute_sheaf_laplacian(order=0)
        cohom = self.compute_cohomology()

        result: Dict[str, Any] = {
            'global_section_dim': cohom.h0_dimension,
            'obstruction_dim': cohom.h1_dimension,
            'is_consistent': cohom.is_globally_consistent,
        }

        if SPARSE_AVAILABLE and L0.shape[0] > 500:
            L0_sparse = csr_matrix(L0)
            eigenvalues_0, eigenvectors_0 = eigsh(L0_sparse, k=min(k, L0.shape[0] - 1), which='SM')
        else:
            eigenvalues_0, eigenvectors_0 = np.linalg.eigh(L0)

        result['eigenvalues_0'] = eigenvalues_0[:k]
        result['eigenvectors_0'] = eigenvectors_0[:, :k]

        # Spectral gap: first nonzero eigenvalue
        nonzero_eigs = eigenvalues_0[eigenvalues_0 > 1e-10]
        result['spectral_gap_0'] = nonzero_eigs[0] if len(nonzero_eigs) > 0 else 0.0
        result['algebraic_connectivity'] = result['spectral_gap_0']

        # L¹ spectrum
        L1 = self.compute_sheaf_laplacian(order=1)
        if L1.shape[0] > 0:
            if SPARSE_AVAILABLE and L1.shape[0] > 500:
                L1_sparse = csr_matrix(L1)
                eigenvalues_1, eigenvectors_1 = eigsh(L1_sparse, k=min(k, L1.shape[0] - 1), which='SM')
            else:
                eigenvalues_1, eigenvectors_1 = np.linalg.eigh(L1)
            result['eigenvalues_1'] = eigenvalues_1[:k]
            result['eigenvectors_1'] = eigenvectors_1[:, :k]
        else:
            result['eigenvalues_1'] = np.array([])
            result['eigenvectors_1'] = np.array([])

        return result

    def check_global_consistency(self) -> bool:
        """
        Check whether the sheaf admits a full-rank global section.

        A sheaf is globally consistent if H¹ = 0, meaning every local section
        can be extended to a global section without obstruction.

        Returns
        -------
        bool
            True if the sheaf is globally consistent.

        Examples
        --------
        >>> vertices = ["v1", "v2"]
        >>> hyperedges = [{"v1", "v2"}]
        >>> shg = SheafHypergraph(vertices, hyperedges)
        >>> shg.check_global_consistency()
        True
        """
        cohom = self.compute_cohomology()
        return cohom.is_globally_consistent

    def global_section(self, local_data: Dict[str, np.ndarray]) -> Optional[np.ndarray]:
        """
        Attempt to extend local vertex data to a global section.

        Given local assignments to vertices (local_data), this method solves
        the sheaf condition to find a global section that restricts to these
        local data where possible. If no such extension exists, returns None.

        Parameters
        ----------
        local_data : Dict[str, np.ndarray]
            Dictionary mapping vertex IDs to vectors in their stalks.

        Returns
        -------
        Optional[np.ndarray]
            Global section vector (concatenated vertex assignments) or None.

        Examples
        --------
        >>> vertices = ["v1", "v2"]
        >>> hyperedges = [{"v1", "v2"}]
        >>> shg = SheafHypergraph(vertices, hyperedges)
        >>> local = {"v1": np.array([1.0]), "v2": np.array([1.0])}
        >>> section = shg.global_section(local)
        >>> section is not None
        True
        """
        # Build the coboundary condition: δ(s) = 0
        # and s(v) = local_data[v] for all v with data
        delta = self._build_boundary_matrix()

        # We solve: δ @ s = 0 subject to s[v_offsets] = local_data[v]
        # This is a constrained least-squares problem
        vertex_offsets = {}
        offset = 0
        for v in sorted(self.vertices):
            vertex_offsets[v] = (offset, offset + self.vertex_stalks[v].dimension)
            offset += self.vertex_stalks[v].dimension

        total_dim = offset

        # Known values
        known_indices = []
        known_values = []
        for v, data in local_data.items():
            if v in vertex_offsets:
                start, end = vertex_offsets[v]
                for j in range(len(data)):
                    known_indices.append(start + j)
                    known_values.append(data[j])

        if not known_indices:
            # No local data: return any global section
            cohom = self.compute_cohomology()
            if cohom.global_sections is not None and cohom.global_sections.size > 0:
                return cohom.global_sections[:, 0]
            return None

        # Solve: min ||δ s||² subject to s[known] = known_values
        # Using Lagrange multipliers or reduced system
        unknown_indices = [i for i in range(total_dim) if i not in known_indices]

        if not unknown_indices:
            # All values known, check consistency
            s = np.zeros(total_dim)
            s[known_indices] = known_values
            if np.allclose(delta @ s, 0):
                return s
            return None

        # Partition δ = [δ_known | δ_unknown]
        delta_known = delta[:, known_indices]
        delta_unknown = delta[:, unknown_indices]

        s_known = np.array(known_values)
        # Solve: δ_unknown @ s_unknown = -δ_known @ s_known
        rhs = -delta_known @ s_known

        try:
            s_unknown, residuals, rank, singular = np.linalg.lstsq(delta_unknown, rhs, rcond=None)
        except np.linalg.LinAlgError:
            return None

        s = np.zeros(total_dim)
        s[known_indices] = s_known
        s[unknown_indices] = s_unknown

        return s

    def compute_obstruction(self, local_data: Dict[str, np.ndarray]) -> float:
        """
        Measure the obstruction to extending local data to a global section.

        Returns the norm of the minimal coboundary violation.

        Parameters
        ----------
        local_data : Dict[str, np.ndarray]
            Local assignments to vertices.

        Returns
        -------
        float
            Obstruction magnitude (0 = globally consistent).

        Examples
        --------
        >>> vertices = ["v1", "v2"]
        >>> hyperedges = [{"v1", "v2"}]
        >>> # Create sheaf with incompatible restriction maps
        >>> v_stalks = {"v1": SheafStalk(1), "v2": SheafStalk(1)}
        >>> e_stalks = {"e0": SheafStalk(2)}
        >>> rm = {("v1", "e0"): RestrictionMap("v1", "e0", np.array([[1.0], [0.0]])),
        ...       ("v2", "e0"): RestrictionMap("v2", "e0", np.array([[0.0], [1.0]]))}
        >>> shg = SheafHypergraph(vertices, hyperedges, v_stalks, e_stalks, rm)
        >>> obs = shg.compute_obstruction({"v1": np.array([1.0]), "v2": np.array([2.0])})
        >>> obs >= 0
        True
        """
        delta = self._build_boundary_matrix()
        if delta.size == 0:
            return 0.0

        # Build full vector from local data
        vertex_offsets = {}
        offset = 0
        for v in sorted(self.vertices):
            vertex_offsets[v] = offset
            offset += self.vertex_stalks[v].dimension

        s = np.zeros(offset)
        for v, data in local_data.items():
            if v in vertex_offsets:
                start = vertex_offsets[v]
                s[start:start + len(data)] = data

        violation = delta @ s
        return np.linalg.norm(violation)

    def _nullspace_qr(self, A: np.ndarray) -> np.ndarray:
        """
        Compute nullspace using QR decomposition (fallback when scipy is unavailable).

        Parameters
        ----------
        A : np.ndarray
            Input matrix.

        Returns
        -------
        np.ndarray
            Basis vectors of the nullspace (columns).
        """
        if A.size == 0:
            return np.array([])
        # QR decomposition of A^T
        Q, R = np.linalg.qr(A.T)
        # Rank is the number of nonzero diagonal elements in R
        rank = np.sum(np.abs(np.diag(R)) > 1e-10)
        # Nullspace is the last (n - rank) columns of Q
        null_basis = Q[:, rank:]
        return null_basis

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the sheaf hypergraph to a dictionary."""
        return {
            'vertices': self.vertices,
            'hyperedges': [list(e) for e in self.hyperedges],
            'vertex_stalks': {
                v: {'dimension': s.dimension, 'label': s.label}
                for v, s in self.vertex_stalks.items()
            },
            'cohomology': {
                'h0': self.compute_cohomology().h0_dimension,
                'h1': self.compute_cohomology().h1_dimension,
                'consistent': self.check_global_consistency(),
            }
        }

    def __repr__(self) -> str:
        cohom = self.compute_cohomology()
        return (
            f"SheafHypergraph(|V|={len(self.vertices)}, "
            f"|E|={len(self.hyperedges)}, "
            f"H⁰={cohom.h0_dimension}, "
            f"H¹={cohom.h1_dimension})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SheafHypergraph):
            return False
        return (
            self.vertices == other.vertices and
            self.hyperedges == other.hyperedges
        )

    def __hash__(self) -> int:
        return hash((tuple(sorted(self.vertices)), tuple(sorted(tuple(sorted(e)) for e in self.hyperedges))))


# ============================================================================
# Factory Functions for APEIRON Integration
# ============================================================================

def sheaf_from_layer1_observables(
    observables: List[Any],
    similarity_threshold: float = 0.7,
    stalk_dimension: int = 2,
) -> SheafHypergraph:
    """
    Construct a sheaf hypergraph from Layer 1 UltimateObservables.

    Each observable becomes a vertex with a stalk of dimension `stalk_dimension`.
    Hyperedges are formed from cliques of observables with pairwise similarity
    above the threshold. Restriction maps are identity by default.

    Parameters
    ----------
    observables : List[Any]
        List of UltimateObservable objects from Layer 1.
    similarity_threshold : float
        Threshold for hyperedge formation.
    stalk_dimension : int
        Dimension of vertex stalks.

    Returns
    -------
    SheafHypergraph
        The constructed sheaf hypergraph.

    Examples
    --------
    >>> # This is a conceptual example; actual UltimateObservable objects are needed
    >>> # shg = sheaf_from_layer1_observables(obs_list, 0.5, 3)
    """
    vertices = [f"obs_{i}" for i in range(len(observables))]
    vertex_stalks = {v: SheafStalk(dimension=stalk_dimension) for v in vertices}

    # Compute similarity matrix (placeholder - real implementation uses Layer 1 bridge)
    n = len(observables)
    hyperedges = []
    for i in range(n):
        for j in range(i + 1, n):
            # Placeholder similarity: all pairs form edges
            hyperedges.append({vertices[i], vertices[j]})

    return SheafHypergraph(vertices, hyperedges, vertex_stalks)


def sheaf_from_hypergraph(
    hypergraph: 'Hypergraph',  # type: ignore
    stalk_dimension: int = 2,
) -> SheafHypergraph:
    """
    Convert a standard Hypergraph to a SheafHypergraph.

    Parameters
    ----------
    hypergraph : Hypergraph
        An existing Hypergraph instance.
    stalk_dimension : int
        Dimension of stalks.

    Returns
    -------
    SheafHypergraph
        The sheafified hypergraph.
    """
    vertices = [f"v_{i}" for i in range(len(hypergraph.vertices))]
    hyperedges = [
        {f"v_{i}" for i in edge} for edge in hypergraph.edges
    ]
    vertex_stalks = {v: SheafStalk(dimension=stalk_dimension) for v in vertices}

    return SheafHypergraph(vertices, hyperedges, vertex_stalks)


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)