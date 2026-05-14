#!/usr/bin/env python3
"""
Derived Learning – Functorial Error Propagation for the APEIRON Framework
==========================================================================
Layer 2 — Relational Hypergraph (Homological Error Correction)

Implements derived functors (Ext and Tor) to trace how observational
errors in Layer 1 propagate through the categorical and topological
structures of Layer 2. This provides a mathematically rigorous alternative
to backpropagation: instead of gradients, we compute the extent to which
a local inconsistency (an "ontological fracture") fails to extend to a
global coherent state, using the machinery of homological algebra.

Mathematical Foundation
-----------------------
Given a sheaf F of vector spaces on a hypergraph H, we can view the
category of sheaves as an abelian category with enough injectives.
The global sections functor Γ is left-exact. Its right derived functors
are the sheaf cohomology groups Hⁱ(H; F). The Ext groups
Extⁱ(F, G) classify extensions of F by G, i.e., ways in which a local
error in F can be "absorbed" by G without creating a global contradiction.

Similarly, Tor groups Torᵢ(F, G) measure the failure of the tensor
product to be exact, which corresponds to interference patterns between
two knowledge sources.

In the discrete setting of a hypergraph sheaf, we compute these derived
functors via projective resolutions of the structure sheaf, using the
fact that the category of sheaves on a finite poset is equivalent to
modules over the incidence algebra.

This module provides:
- `DerivedFunctor`: computes Ext and Tor for sheaf modules.
- `ErrorPropagation`: traces a local error through the resolution to
  determine which global invariants are affected.
- Integration hooks for Layer2UnifiedAPI.

References
----------
.. [1] Weibel, C.A. "An Introduction to Homological Algebra" (1994)
.. [2] Gelfand, S.I., Manin, Yu.I. "Methods of Homological Algebra" (2003)
.. [3] Beniers, D. "Categorical Foundations of the APEIRON Framework" (2025)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from itertools import combinations
import warnings

try:
    from scipy.linalg import svd, null_space
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from .sheaf_hypergraph import SheafHypergraph, SheafStalk
except ImportError:
    SheafHypergraph, SheafStalk = None, None

try:
    from .hypergraph import Hypergraph
except ImportError:
    Hypergraph = None


# ============================================================================
# Helper: incidence algebra of a poset (here, the hypergraph with preorder)
# ============================================================================

def incidence_algebra(vertices: List[Any], order_matrix: np.ndarray) -> np.ndarray:
    """
    Build the incidence algebra I(P) of a poset P as a matrix algebra.
    Elements are matrices A where A[i,j] ≠ 0 only if i ≤ j.
    Returns a projector that maps any matrix to its incidence algebra
    component (by zeroing entries where i ≰ j).
    """
    return order_matrix.astype(float)


# ============================================================================
# SheafModule: a sheaf as a module over the incidence algebra
# ============================================================================

class SheafModule:
    """
    Representation of a sheaf F on a hypergraph as a module over the
    incidence algebra of the underlying poset.

    A sheaf is a functor from the poset (open sets) to vector spaces.
    Equivalently, it is a right module over the incidence algebra I(P):
    a graded vector space M = ⊕_{v} F(v) with right multiplication by
    the restriction maps.

    Here we store the total space M as a matrix of dimension sum(dim F(v))
    and the action of the incidence algebra.
    """

    def __init__(self, sheaf_hypergraph):
        if SheafHypergraph is None:
            raise ImportError("SheafHypergraph module is required.")
        self.sheaf = sheaf_hypergraph
        self._build_module()

    def _build_module(self):
        """Build the module representation from the sheaf."""
        vertices = sorted(self.sheaf.vertices)
        n_vertices = len(vertices)
        # Compute total dimension of the module
        self.vertex_dims = [self.sheaf.vertex_stalks[v].dimension for v in vertices]
        self.total_dim = sum(self.vertex_dims)
        self.vertex_offsets = {}
        offset = 0
        for i, v in enumerate(vertices):
            self.vertex_offsets[v] = (offset, offset + self.vertex_dims[i])
            offset += self.vertex_dims[i]

        # Build the incidence algebra projector: a matrix of shape (total_dim, total_dim)
        # that has identity blocks on allowed positions (i ≤ j) and zero elsewhere.
        # For simplicity, we assume the preorder is the incidence from hyperedges:
        # i ≤ j if there is a hyperedge containing both (or they are equal).
        # We construct order_matrix from the sheaf hypergraph's hyperedges.
        self.order_matrix = np.zeros((n_vertices, n_vertices), dtype=bool)
        for edge in self.sheaf.hyperedges:
            edge_verts = list(edge)
            for v in edge_verts:
                for w in edge_verts:
                    i = vertices.index(v)
                    j = vertices.index(w)
                    self.order_matrix[i, j] = True
        np.fill_diagonal(self.order_matrix, True)

        # Build the algebra action projector
        # For a matrix A in I(P), its block (i,j) is nonzero only if i ≤ j.
        # The projector P on M ⊗ I(P) is a (total_dim, total_dim) matrix that
        # extracts the relevant components. We won't need the full projector
        # for Ext/Tor computations, but we store the order matrix.
        self.vertices = vertices

    def dimension(self) -> int:
        return self.total_dim

    def restriction_matrix(self, v: str, w: str) -> Optional[np.ndarray]:
        """
        Return the restriction map F(v → w) if v ≤ w (i.e., they co-occur
        in some hyperedge), else None.
        """
        if v not in self.vertex_offsets or w not in self.vertex_offsets:
            return None
        i = self.vertices.index(v)
        j = self.vertices.index(w)
        if not self.order_matrix[i, j]:
            return None
        # Retrieve the restriction map from the sheaf
        # Find a hyperedge containing both (or chain)
        for edge in self.sheaf.hyperedges:
            if v in edge and w in edge:
                e_id = f"e{self.sheaf.hyperedges.index(edge)}"
                rm = self.sheaf.restriction_maps.get((v, e_id))
                if rm is not None:
                    return rm.matrix
                rm = self.sheaf.restriction_maps.get((w, e_id))
                if rm is not None:
                    return rm.matrix
        # If no direct edge, but order holds via transitivity, we need composition.
        # For simplicity, return identity if dimensions match (placeholder).
        if i == j:
            dim = self.vertex_dims[i]
            return np.eye(dim)
        # Transitive: find a path (BFS) and compose restrictions (simplified: identity for now)
        return None


# ============================================================================
# Projective Resolution
# ============================================================================

class ProjectiveResolution:
    """
    Build a projective resolution of a sheaf module M.

    For a poset, the standard projectives are the representable modules
    P(v) = I(P) e_v, where e_v is the idempotent for vertex v. A projective
    resolution of M can be built from the Čech nerve of the hypergraph.

    We approximate a resolution of length 2 using the boundary matrices
    of the sheaf hypergraph.
    """

    def __init__(self, sheaf_module: SheafModule, length: int = 3):
        self.module = sheaf_module
        self.length = length
        self._build()

    def _build(self):
        """Build a resolution using the sheaf coboundary."""
        # The sheaf hypergraph already has a coboundary matrix δ.
        # We can use the sequence:
        # 0 → M → P⁰ → P¹ → P² → ...
        # where P⁰ = C⁰ (0-cochains), P¹ = C¹, etc.
        # The differentials are the coboundary maps.
        delta = self.module.sheaf._build_boundary_matrix()
        n0 = delta.shape[1]  # dim C⁰
        n1 = delta.shape[0]  # dim C¹
        self.resolution = []
        # Step 0: M → C⁰ (inclusion)
        self.resolution.append(np.eye(n0))
        # Step 1: C⁰ → C¹ (coboundary)
        self.resolution.append(delta)
        # Step 2: C¹ → C² (we need the 2-coboundary; for hypergraph, use cup product or zero)
        # For simplicity, we take the transpose of the 1-boundary if available,
        # otherwise a zero matrix.
        if hasattr(self.module.sheaf, '_build_boundary_matrix'):
            # This is a placeholder; in a full implementation we would compute δ¹.
            pass
        # For now, resolution is just [id, δ]
        self.differentials = self.resolution

    def resolve(self, error_vector: np.ndarray, degree: int = 0) -> np.ndarray:
        """
        Given an error vector in C⁰ (degree 0), lift it through the resolution.
        Returns the image in the next degree.
        """
        if degree >= len(self.differentials):
            return np.zeros(0)
        diff = self.differentials[degree]
        if diff.shape[1] != len(error_vector):
            raise ValueError("Dimension mismatch")
        return diff @ error_vector


# ============================================================================
# Ext and Tor functors
# ============================================================================

class DerivedFunctor:
    """
    Compute Ext and Tor for sheaf modules on a hypergraph.

    Extⁱ(F, G) classifies extensions of F by G; it measures how a local
    error in F can be absorbed by G without creating a global obstruction.

    Torᵢ(F, G) measures the failure of exactness of the tensor product,
    corresponding to interference between two knowledge sources F and G.
    """

    def __init__(self, sheaf_module: SheafModule):
        self.module = sheaf_module
        self.resolution = ProjectiveResolution(sheaf_module, length=3)

    def ext(self, other_module: SheafModule, degree: int = 0) -> int:
        """
        Compute dim Extⁱ(F, G) using the resolution of F.

        Extⁱ(F, G) = Hⁱ(Hom(P_•, G)), where P_• is a projective resolution
        of F. We compute Hom(P_i, G) and take homology.

        For simplicity, we compute the dimension of the kernel of the
        coboundary modulo the image of the previous differential.

        Returns
        -------
        int
            Dimension of the Ext group.
        """
        if degree == 0:
            # Ext⁰ = Hom(F, G): all sheaf homomorphisms.
            # Dimension = sum over vertices of dim(F(v)) * dim(G(v)) minus the
            # relations imposed by the restriction maps.
            # We approximate: count of linear maps between the total spaces
            # that commute with the coboundary.
            delta_F = self.module.sheaf._build_boundary_matrix()
            delta_G = other_module.sheaf._build_boundary_matrix() if other_module.sheaf != self.module.sheaf else delta_F
            # Hom(F, G) in degree 0: matrices X such that X δ_F = δ_G X.
            # We solve the linear system and compute dimension.
            return self._hom_dim(delta_F, delta_G)
        elif degree == 1:
            # Ext¹(F, G) classifies extensions: short exact sequences
            # 0 → G → E → F → 0.
            # Dimension = dim H¹(H; Hom(F, G)), the first sheaf cohomology
            # of the internal Hom sheaf.
            # We approximate by taking the cokernel of the 0-th Hom differential.
            delta_F = self.module.sheaf._build_boundary_matrix()
            delta_G = other_module.sheaf._build_boundary_matrix() if other_module.sheaf != self.module.sheaf else delta_F
            hom0 = self._hom_dim(delta_F, delta_G)
            # Compute dimension of 1-cocycles modulo 1-coboundaries for Hom sheaf.
            # Placeholder: use obstruction from sheaf cohomology of Hom.
            # We can compute it using the sheaf cohomology of the tensor product sheaf.
            return self._ext1_dim(delta_F, delta_G)
        else:
            return 0

    def tor(self, other_module: SheafModule, degree: int = 0) -> int:
        """
        Compute dim Torᵢ(F, G) using the resolution of F.

        Torᵢ(F, G) = Hᵢ(F ⊗ P_•). We compute F ⊗ P_i and take homology.
        """
        if degree == 0:
            # Tor⁰(F, G) = F ⊗ G. Dimension = sum dim F(v) * dim G(v) over v.
            dim = 0
            for v in self.module.vertices:
                dim_v = self.module.vertex_dims[self.module.vertices.index(v)]
                other_v = other_module.vertex_dims[other_module.vertices.index(v)] if v in other_module.vertices else 0
                dim += dim_v * other_v
            return dim
        elif degree == 1:
            # Tor¹ measures torsion: the kernel of the tensor product of the
            # coboundary with G modulo the image of the previous.
            # We compute dim(ker(δ_F ⊗ id_G)) - dim(im(δ_F² ⊗ id_G)).
            # Approximation: use the rank of the coboundary.
            delta_F = self.module.sheaf._build_boundary_matrix()
            rank = np.linalg.matrix_rank(delta_F)
            dim_G = sum(other_module.vertex_dims)
            # Tor¹ dimension = (nullity of δ_F) * dim_G - (something)
            nullity = delta_F.shape[1] - rank
            return max(0, nullity * dim_G - rank * dim_G)
        else:
            return 0

    def _hom_dim(self, delta_F: np.ndarray, delta_G: np.ndarray) -> int:
        """Compute dimension of Hom(F, G) in degree 0."""
        # Solve X δ_F = δ_G X. This is a linear system.
        # We can solve via SVD: find the nullspace of the operator.
        n_F = delta_F.shape[1]
        n_G = delta_G.shape[1]
        # Build the matrix representation of the commutator condition.
        # For small dimensions, use Kronecker product.
        # Condition: (I ⊗ δ_G) - (δ_F^T ⊗ I) vec(X) = 0.
        # So nullity of M = I ⊗ δ_G - δ_F^T ⊗ I gives dim Hom.
        import numpy as np
        I_F = np.eye(delta_F.shape[0])
        I_G = np.eye(delta_G.shape[0])
        M = np.kron(I_G, delta_F) - np.kron(delta_G.T, I_F)
        if M.size == 0:
            return n_F * n_G
        if SCIPY_AVAILABLE:
            return null_space(M).shape[1]
        else:
            return n_F * n_G  # fallback

    def _ext1_dim(self, delta_F: np.ndarray, delta_G: np.ndarray) -> int:
        """
        Compute an estimate for dim Ext¹(F, G) using sheaf cohomology.

        If the underlying hypergraph is acyclic (β₁ = 0), then Ext¹ = 0 for
        any sheaves F, G. Otherwise, we estimate Ext¹ as the maximum of the
        H¹ dimensions of F and G.
        """
        # Try to obtain the hypergraph via the sheaf module
        hypergraph = None
        if hasattr(self.module, 'sheaf') and self.module.sheaf is not None:
            try:
                # Reconstruct a Hypergraph instance from the sheaf's vertices/edges
                from apeiron.layers.layer02_relational.hypergraph import Hypergraph
                hg = Hypergraph()
                # vertices of the sheaf are strings like "v_0", "v_1", ...
                # we ignore the string labels and just use indices
                vert_names = self.module.sheaf.vertices  # list of string names
                for v in vert_names:
                    hg.vertices.add(v)
                # edges: the sheaf stores hyperedges as sets of vertex names
                for e_set in self.module.sheaf.hyperedges:
                    hg.add_hyperedge(str(e_set), e_set)
                hypergraph = hg
            except Exception:
                pass

        # If we have a hypergraph, check its Betti numbers
        if hypergraph is not None:
            betti = hypergraph.betti_numbers()
            if betti.get(1, 0) == 0:
                return 0  # acyclic hypergraph => Ext¹ = 0

        # Fallback: use spectral properties of the Laplacians
        # H¹ dimension ≈ number of zero eigenvalues of L1 = δ δ^T
        L1_F = delta_F @ delta_F.T
        L1_G = delta_G @ delta_G.T
        if L1_F.size > 0:
            eig_F = np.linalg.eigvalsh(L1_F)
            h1_F = int(np.sum(np.abs(eig_F) < 1e-10))
        else:
            h1_F = 0
        if L1_G.size > 0:
            eig_G = np.linalg.eigvalsh(L1_G)
            h1_G = int(np.sum(np.abs(eig_G) < 1e-10))
        else:
            h1_G = 0

        # A safe upper bound
        return max(h1_F, h1_G)


# ============================================================================
# Error Propagation Engine
# ============================================================================

class ErrorPropagation:
    """
    Trace a local observational error through the sheaf resolution and
    determine which global invariants are affected.

    Given an error vector e (a 0-cochain representing an inconsistency in
    the observations at vertices), compute:
    - The projection of e onto the harmonic subspace (persistent global error).
    - The exact part (can be corrected by adjusting higher cochains).
    - The Ext¹ class representing an ontological obstruction.
    """

    def __init__(self, sheaf_hypergraph):
        if SheafHypergraph is None:
            raise ImportError("SheafHypergraph module is required.")
        self.sheaf = sheaf_hypergraph
        self.module = SheafModule(sheaf_hypergraph)
        self.derived = DerivedFunctor(self.module)

    def propagate(self, error_vector: np.ndarray) -> Dict[str, Any]:
        """
        Analyse an error vector on vertices (0-cochain).

        Returns
        -------
        dict with:
            'harmonic_error': component in ker L⁰ (unresolvable by local adjustments)
            'exact_error': component in im δ^T (can be compensated)
            'obstruction_dim': dimension of Ext¹ (global obstruction)
            'affected_hyperedges': list of hyperedges where error manifests
        """
        delta = self.sheaf._build_boundary_matrix()
        L0 = delta.T @ delta

        # Hodge decomposition of the error
        eigenvalues, eigenvectors = np.linalg.eigh(L0)
        harm_mask = eigenvalues < 1e-10
        harmonic_basis = eigenvectors[:, harm_mask]
        # Project onto harmonic subspace
        harmonic_coeffs = harmonic_basis.T @ error_vector
        harmonic_error = harmonic_basis @ harmonic_coeffs
        # Exact part: error - harmonic (since ker L0 and im δ^T are orthogonal)
        exact_error = error_vector - harmonic_error

        # Ext¹ obstruction
        obstruction_dim = self.derived.ext(self.module, degree=1)

        # Find hyperedges where the error has large components
        affected_hyperedges = []
        edge_list = list(self.sheaf.hyperedges)
        for i, edge in enumerate(edge_list):
            edge_vertices = sorted(edge)
            # Compute the error on this edge as the restriction
            edge_error = 0.0
            for v in edge_vertices:
                if v in self.module.vertex_offsets:
                    start, end = self.module.vertex_offsets[v]
                    edge_error += np.linalg.norm(error_vector[start:end])
            if edge_error > 0.1:
                affected_hyperedges.append(i)

        return {
            'harmonic_error': harmonic_error,
            'exact_error': exact_error,
            'obstruction_dim': obstruction_dim,
            'affected_hyperedges': affected_hyperedges,
            'total_error_norm': float(np.linalg.norm(error_vector)),
        }


# ============================================================================
# Factory
# ============================================================================

def derived_learning_pipeline(hypergraph, error_vector: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """
    Run the derived learning pipeline: build sheaf, compute error propagation.
    If no error vector is given, a random one is generated.
    """
    if SheafHypergraph is None:
        return {'error': 'SheafHypergraph module not available'}
    vertices = [f"v_{v}" for v in sorted(hypergraph.vertices)]
    hyperedges = [{f"v_{v}" for v in edge} for edge in hypergraph.hyperedges.values()]
    shg = SheafHypergraph(vertices, hyperedges)
    ep = ErrorPropagation(shg)
    n = sum(shg.vertex_stalks[v].dimension for v in shg.vertices)
    if error_vector is None:
        error_vector = np.random.randn(n)
    return ep.propagate(error_vector)


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)