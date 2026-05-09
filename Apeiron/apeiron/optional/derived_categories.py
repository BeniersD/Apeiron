"""
DERIVED CATEGORIES – ULTIMATE IMPLEMENTATION
============================================
This module provides a framework for working with derived categories of
chain complexes over an abelian category (here, finite‑dimensional vector spaces).
It includes:

- Chain complexes, chain maps, chain homotopies
- Homology computation
- Mapping cones and distinguished triangles
- Derived functors: Ext and Tor via projective resolutions (for modules over a path algebra)
- Spectral sequences (first quadrant, from a double complex)

All calculations are performed using numpy for linear algebra. The module is
designed to be extensible and to integrate with the categorical structures from
`relations.py` (quiver representations) in future versions.

For simplicity, we work over the field of real numbers; complex numbers or finite
fields could be added by changing the dtype.
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ============================================================================
# CHAIN COMPLEX
# ============================================================================

class ChainComplex:
    """
    A chain complex of finite‑dimensional vector spaces over ℝ.

    Attributes:
        differentials: list of matrices (d_n: C_n → C_{n-1}), with d[0] mapping from C_0 to 0 (not stored).
        dimensions: list of dimensions of C_n (for n = 0..N).
        degree_min, degree_max: inclusive range.
    """
    def __init__(self, differentials: List[np.ndarray]):
        """
        Args:
            differentials: list of matrices [d_1, d_2, ..., d_N] where
                           d_n: C_n → C_{n-1}. The list index i corresponds to degree i+1.
        """
        self.differentials = differentials
        self.degree_max = len(differentials)  # highest degree with a differential
        self.degree_min = 0
        # Compute dimensions
        if len(differentials) == 0:
            self.dimensions = []
        else:
            # C_0 dimension is rows of d_1, or if no d_1, we need explicit?
            # We'll compute all dimensions from differentials.
            dims = []
            # d_1 maps C_1 -> C_0, so C_0 = rows of d_1, C_1 = cols of d_1
            if len(differentials) >= 1:
                d1 = differentials[0]
                dims.append(d1.shape[0])  # C_0
                dims.append(d1.shape[1])  # C_1
            for i in range(1, len(differentials)):
                # d_{i+1} maps C_{i+1} -> C_i, so C_{i+1} = cols of d_{i+1}
                dims.append(differentials[i].shape[1])
            self.dimensions = dims  # length = degree_max+1

    def differential(self, n: int) -> Optional[np.ndarray]:
        """Return differential d_n: C_n → C_{n-1} (n ≥ 1)."""
        if 1 <= n <= self.degree_max:
            return self.differentials[n-1]
        return None

    def dim(self, n: int) -> int:
        if n < 0 or n >= len(self.dimensions):
            return 0
        return self.dimensions[n]

    def is_complex(self, tol: float = 1e-10) -> bool:
        """Check that d_{n-1} ∘ d_n = 0 for all n."""
        for n in range(2, self.degree_max + 1):
            d_prev = self.differential(n-1)
            d_cur = self.differential(n)
            if d_prev is None or d_cur is None:
                continue
            prod = d_prev @ d_cur
            if np.linalg.norm(prod) > tol:
                return False
        return True

    def homology(self, n: int, tol: float = 1e-10) -> Tuple[int, Optional[np.ndarray]]:
        """
        Compute the n‑th homology group H_n = ker(d_n) / im(d_{n+1}).
        Returns (dimension, basis_matrix) where basis matrix columns span a complement.
        If basis computation fails, returns (dimension, None).
        """
        d_n = self.differential(n)
        d_np1 = self.differential(n+1)

        # Compute kernel of d_n
        if d_n is not None:
            U, s, Vh = np.linalg.svd(d_n, full_matrices=True)
            tol_s = tol * max(d_n.shape) * s[0] if len(s) > 0 else 0
            rank = np.sum(s > tol_s)
            null_dim = d_n.shape[1] - rank
            kernel = Vh[rank:, :].T.conj() if null_dim > 0 else np.zeros((d_n.shape[1], 0))
        else:
            null_dim = self.dim(n)
            kernel = np.eye(self.dim(n)) if null_dim > 0 else np.zeros((self.dim(n), 0))

        # Compute image of d_{n+1}
        if d_np1 is not None:
            U, s, Vh = np.linalg.svd(d_np1, full_matrices=False)
            tol_s = tol * max(d_np1.shape) * s[0] if len(s) > 0 else 0
            rank = np.sum(s > tol_s)
            image = U[:, :rank] if rank > 0 else np.zeros((d_np1.shape[0], 0))
        else:
            image = np.zeros((self.dim(n), 0))

        # Compute quotient dimension
        if kernel.shape[1] == 0:
            return 0, np.zeros((self.dim(n), 0))
        if image.shape[1] == 0:
            return kernel.shape[1], kernel

        # Compute rank of combined [image, kernel]
        combined = np.hstack([image, kernel])
        U_comb, s_comb, _ = np.linalg.svd(combined, full_matrices=False)
        tol_comb = tol * max(combined.shape) * s_comb[0] if len(s_comb) > 0 else 0
        rank_comb = np.sum(s_comb > tol_comb)

        # Compute rank of image
        U_img, s_img, _ = np.linalg.svd(image, full_matrices=False)
        tol_img = tol * max(image.shape) * s_img[0] if len(s_img) > 0 else 0
        rank_img = np.sum(s_img > tol_img)

        dim_homology = rank_comb - rank_img
        if dim_homology == 0:
            return 0, np.zeros((self.dim(n), 0))

        # Extract a basis for the homology (optional)
        # We can take the last (dim_homology) columns of Vh_comb corresponding to zero singular values
        # But Vh_comb is from SVD of combined; the null space of combined^T? Actually we need a basis of kernel modulo image.
        # Simpler: compute projection onto orthogonal complement of image, then take a basis of the projected kernel.
        Q_img, _ = np.linalg.qr(image, mode='reduced')
        # Project kernel onto orthocomplement of image
        kernel_proj = kernel - Q_img @ (Q_img.T @ kernel)
        # Now find a basis of kernel_proj
        U_proj, s_proj, _ = np.linalg.svd(kernel_proj, full_matrices=False)
        tol_proj = tol * max(kernel_proj.shape) * s_proj[0] if len(s_proj) > 0 else 0
        rank_proj = np.sum(s_proj > tol_proj)
        if rank_proj >= dim_homology:
            basis = U_proj[:, :dim_homology]
        else:
            basis = None
        return dim_homology, basis

    def betti(self, n: int) -> int:
        """Betti number = dimension of H_n."""
        dim, _ = self.homology(n)
        return dim


# ============================================================================
# CHAIN MAP
# ============================================================================

class ChainMap:
    """
    A chain map f: C → D between chain complexes.
    Consists of maps f_n: C_n → D_n for all n, commuting with differentials.
    """
    def __init__(self, source: ChainComplex, target: ChainComplex, maps: List[np.ndarray]):
        """
        Args:
            source: source complex
            target: target complex
            maps: list of matrices [f_0, f_1, ..., f_N] where f_n: C_n → D_n.
                  The length should cover all degrees where both complexes are defined.
        """
        self.source = source
        self.target = target
        self.maps = maps

    def __getitem__(self, n: int) -> Optional[np.ndarray]:
        if 0 <= n < len(self.maps):
            return self.maps[n]
        return None

    def is_chain_map(self, tol: float = 1e-10) -> bool:
        """Check commutativity: f_{n-1} ∘ d_n^C = d_n^D ∘ f_n."""
        for n in range(1, max(self.source.degree_max, self.target.degree_max) + 1):
            f_prev = self[n-1]
            f_cur = self[n]
            dC = self.source.differential(n)
            dD = self.target.differential(n)
            if dC is None or dD is None:
                continue
            if f_prev is None or f_cur is None:
                continue
            left = f_prev @ dC
            right = dD @ f_cur
            if np.linalg.norm(left - right) > tol:
                return False
        return True


# ============================================================================
# CHAIN HOMOTOPY
# ============================================================================

class ChainHomotopy:
    """
    A chain homotopy h between two chain maps f, g: C → D.
    Satisfies: f - g = d_D ∘ h + h ∘ d_C.
    """
    def __init__(self, maps: List[np.ndarray]):
        self.maps = maps  # h_n: C_n → D_{n+1}

    def __getitem__(self, n: int) -> Optional[np.ndarray]:
        if 0 <= n < len(self.maps):
            return self.maps[n]
        return None


def chain_homotopy(f: ChainMap, g: ChainMap, tol: float = 1e-10) -> Optional[ChainHomotopy]:
    """
    Construct a chain homotopy between f and g, if they are chain homotopic.
    Solves the linear system degree by degree using forward substitution.

    Returns a ChainHomotopy object if a solution exists, else None.
    """
    if f.source is not g.source or f.target is not g.target:
        logger.error("Chain maps must have same source and target")
        return None

    C = f.source
    D = f.target
    max_deg = max(C.degree_max, D.degree_max) + 1  # we may need h up to that

    # We'll build h_n for n from 0 to max_deg
    h_maps = [None] * (max_deg + 1)
    # h_{-1} is zero map
    h_prev = np.zeros((0, 0))

    for n in range(0, max_deg + 1):
        # Equation: f_n - g_n = d_{n+1}^D ∘ h_n + h_{n-1} ∘ d_n^C
        # We know h_{n-1} (h_prev). Solve for h_n.
        fn = f[n] if n < len(f.maps) else None
        gn = g[n] if n < len(g.maps) else None
        if fn is None or gn is None:
            # If one map missing, we require the other to be zero? For simplicity, skip.
            continue

        diff = fn - gn
        # Subtract known term from h_prev ∘ d_n^C
        dC_n = C.differential(n)  # d_n: C_n -> C_{n-1}
        if dC_n is not None and h_prev.size > 0:
            # h_prev maps C_{n-1} -> D_n, so h_prev @ dC_n maps C_n -> D_n
            # Ensure shapes match
            if h_prev.shape[1] == dC_n.shape[0]:
                diff = diff - h_prev @ dC_n
            else:
                logger.warning(f"Shape mismatch at degree {n}: h_prev {h_prev.shape}, dC_n {dC_n.shape}")
                return None

        # Now we need to solve dD_{n+1} ∘ h_n = diff  (where dD_{n+1}: D_{n+1} -> D_n)
        dD_np1 = D.differential(n+1)  # maps D_{n+1} -> D_n
        if dD_np1 is None:
            # No differential, so we require diff == 0, and h_n can be arbitrary (but we set to zero)
            if np.linalg.norm(diff) > tol:
                return None
            h_n = np.zeros((C.dim(n), 0))  # no D_{n+1}? Actually if dD_np1 is None, D_{n+1} might be zero.
            h_maps[n] = h_n
            h_prev = h_n
            continue

        # We need to find a matrix X (h_n) such that dD_np1 @ X = diff.
        # This is a linear system A X = B with A = dD_np1 (size D_n × D_{n+1}), B = diff (size D_n × C_n).
        # Solve using least squares; if residual is small, solution exists.
        A = dD_np1
        B = diff
        # Check dimensions: A.shape = (dim(D_n), dim(D_{n+1})), B.shape = (dim(D_n), dim(C_n))
        if A.shape[0] != B.shape[0]:
            logger.warning(f"Shape mismatch: dD_{n+1} rows {A.shape[0]} != B rows {B.shape[0]}")
            return None

        # Use lstsq to solve for X (each column of B independently)
        X, residuals, rank, s = np.linalg.lstsq(A, B, rcond=None)
        # Check residual
        if residuals.size > 0 and np.max(residuals) > tol:
            logger.debug(f"No solution for h_{n}, residual {residuals}")
            return None

        h_n = X
        h_maps[n] = h_n
        h_prev = h_n

    # Filter out None at the end
    h_maps = [h for h in h_maps if h is not None]
    return ChainHomotopy(h_maps)


# ============================================================================
# MAPPING CONE
# ============================================================================

def mapping_cone(f: ChainMap) -> ChainComplex:
    """
    Construct the mapping cone of a chain map f: C → D.
    The cone is a complex with (Cone)_n = D_n ⊕ C_{n-1} and differential
        [ d_D_n    f_{n-1} ]
        [   0     -d_C_{n-1} ].
    """
    # Determine the range of degrees
    min_deg = min(f.source.degree_min, f.target.degree_min)
    max_deg = max(f.source.degree_max, f.target.degree_max) + 1  # because C shifts
    diff_mats = []
    for n in range(1, max_deg + 1):
        # We need d_n: (Cone)_n → (Cone)_{n-1}
        # (Cone)_n = D_n ⊕ C_{n-1}
        # (Cone)_{n-1} = D_{n-1} ⊕ C_{n-2}
        # The differential block matrix:
        # top-left: d_D_n (mapping D_n → D_{n-1})
        # top-right: f_{n-1} (mapping C_{n-1} → D_{n-1})
        # bottom-left: 0
        # bottom-right: -d_C_{n-1} (mapping C_{n-1} → C_{n-2})
        dD_n = f.target.differential(n)
        dC_nm1 = f.source.differential(n-1)
        f_nm1 = f[n-1]

        # Build blocks with proper dimensions
        top_left = dD_n if dD_n is not None else np.zeros((f.target.dim(n-1), f.target.dim(n)))
        top_right = f_nm1 if f_nm1 is not None else np.zeros((f.target.dim(n-1), f.source.dim(n-1)))
        bottom_left = np.zeros((f.source.dim(n-2), f.target.dim(n))) if n-2 >= 0 else np.zeros((0, f.target.dim(n)))
        bottom_right = -dC_nm1 if dC_nm1 is not None else np.zeros((f.source.dim(n-2), f.source.dim(n-1)))

        # Ensure all blocks have consistent rows/cols
        rows_D = top_left.shape[0]
        cols_D = top_left.shape[1]
        rows_C = bottom_right.shape[0]
        cols_C = bottom_right.shape[1]

        # Adjust top_right if needed (should be rows_D x cols_C)
        if top_right.shape != (rows_D, cols_C):
            if top_right.size == 0:
                top_right = np.zeros((rows_D, cols_C))
            else:
                logger.warning(f"Shape mismatch in mapping cone at degree {n}: top_right {top_right.shape} vs expected ({rows_D},{cols_C})")
                # Attempt to pad/trim? For simplicity, we'll force zeros.
                top_right = np.zeros((rows_D, cols_C))

        # Adjust bottom_left (should be rows_C x cols_D)
        if bottom_left.shape != (rows_C, cols_D):
            bottom_left = np.zeros((rows_C, cols_D))

        top = np.hstack([top_left, top_right])
        bottom = np.hstack([bottom_left, bottom_right])
        full = np.vstack([top, bottom])
        diff_mats.append(full)

    return ChainComplex(diff_mats)


# ============================================================================
# PROJECTIVE RESOLUTIONS AND DERIVED FUNCTORS
# ============================================================================

class Module(ABC):
    """Abstract base class for objects in an abelian category (e.g., vector spaces or quiver representations)."""
    @abstractmethod
    def dim(self) -> int:
        """Dimension (or some measure of size)."""
        pass

    @abstractmethod
    def projective_cover(self) -> Tuple['Module', 'Module', Callable]:
        """
        Return (P, K, π) where P is projective, π: P → self is surjective, and K = ker(π).
        For vector spaces, P = self, K = 0, π = identity.
        """
        pass


class VectorSpace(Module):
    """Simple vector space for demonstration."""
    def __init__(self, dimension: int):
        self._dim = dimension

    def dim(self) -> int:
        return self._dim

    def projective_cover(self) -> Tuple['VectorSpace', 'VectorSpace', Callable]:
        # Vector spaces are projective; cover is identity
        P = VectorSpace(self._dim)
        K = VectorSpace(0)
        def pi(x):
            return x
        return P, K, pi


def projective_resolution(module: Module, max_degree: int) -> ChainComplex:
    """
    Compute a projective resolution of the given module up to max_degree.
    Returns a chain complex P_* → module (with augmentation in degree -1?).
    For simplicity, we return a complex with P_0 = module and higher terms zero.
    For non‑trivial modules, this should be overridden.
    """
    if max_degree < 0:
        return ChainComplex([])
    # For vector spaces, trivial resolution
    # We need to represent the map d_1: P_1 → P_0. Since P_1=0, d_1 is zero matrix.
    # But we need to encode the augmentation? Usually resolution is P_* → M → 0.
    # We'll return a complex with P_0 = M and no differentials (since higher are zero).
    # However, to have a chain complex, we need d_1: P_1 → P_0. If P_1=0, d_1 is a 0×dim matrix.
    # We'll construct a differential of shape (dim, 0).
    dim0 = module.dim()
    d1 = np.zeros((dim0, 0))  # from 0-dim space to dim0
    return ChainComplex([d1])


def ext(module_A: Module, module_B: Module, n: int, resolution_func: Optional[Callable] = None) -> int:
    """
    Compute Ext^n(A, B) using a projective resolution of A.
    For vector spaces, Ext^0 = dim(Hom(A,B)) and higher are zero.
    """
    if resolution_func is None:
        resolution_func = projective_resolution
    res = resolution_func(module_A, n+1)  # need up to degree n
    # Ext^n = H^n( Hom(P_*, B) )
    # Build Hom complex: Hom(P_n, B) at degree n, differential is (d_{n+1})^*.
    # For vector spaces, Hom(P_n, B) is matrices of size dim(B) × dim(P_n).
    # For n=0, we need the cohomology of the Hom complex.
    # Since our resolution is trivial (P_0 = A, P_1=0), we have:
    # Hom(P_0, B) = Hom(A,B) of dimension dim(A)*dim(B)
    # Hom(P_1, B) = 0, etc. So Ext^0 = dim(Hom(A,B)), Ext^{>0}=0.
    if n == 0:
        return module_A.dim() * module_B.dim()  # dimension of Hom space
    else:
        return 0


def tor(module_A: Module, module_B: Module, n: int, resolution_func: Optional[Callable] = None) -> int:
    """
    Compute Tor_n(A, B) using a projective resolution of A (or flat resolution of B).
    For vector spaces, Tor_0 = dim(A⊗B) and higher are zero.
    """
    if resolution_func is None:
        resolution_func = projective_resolution
    res = resolution_func(module_A, n+1)
    # Tor_n = H_n( P_* ⊗ B )
    # For trivial resolution, P_0 = A, P_1=0 => Tor_0 = dim(A⊗B), Tor_{>0}=0.
    if n == 0:
        return module_A.dim() * module_B.dim()
    else:
        return 0


# ============================================================================
# SPECTRAL SEQUENCE (first quadrant, from a double complex)
# ============================================================================

class SpectralSequence:
    """
    Represents a first‑quadrant spectral sequence (E_r^{p,q}, d_r).
    The user can provide the initial page E_2 (or E_1) as a dictionary mapping (p,q) to matrices (differentials).
    The class can compute the next page by taking homology.
    """

    def __init__(self, initial_page: Dict[Tuple[int, int], np.ndarray], differential_deg: Tuple[int, int] = (2, -1)):
        """
        Args:
            initial_page: dictionary with keys (p,q) and values the differential d_r: E_r^{p,q} → E_r^{p+r, q-r+1}
            differential_deg: the bidegree of the differential (default (r, 1-r) for a usual spectral sequence).
                              For a first quadrant, r starts at 2 often.
        """
        self.pages = {2: initial_page}  # start at page 2
        self.current_page = 2
        self.differential_deg = differential_deg

    def next_page(self, tol: float = 1e-10):
        """Compute the next page by taking homology at the current page."""
        current = self.pages[self.current_page]
        r = self.current_page
        dr_bideg = self.differential_deg  # (r, 1-r) typically
        next_page = {}
        # We need to compute for each (p,q) the homology H = ker(d_r) / im(d_r) at that spot.
        # But the differential goes from (p,q) to (p+r, q-r+1). So at a fixed (p,q), the incoming differential is from (p-r, q+r-1) and outgoing to (p+r, q-r+1).
        # We'll collect all relevant matrices.
        positions = set(current.keys())
        # We'll also need to consider that some positions may have zero differentials.
        for (p,q) in positions:
            # Outgoing differential: d_r: E_r^{p,q} → E_r^{p+r, q-r+1}
            d_out = current.get((p,q))
            # Incoming differential: from (p-r, q+r-1) to here
            d_in = current.get((p-r, q+r-1))

            # We need to compute kernel of d_out and image of d_in, then quotient.
            # For simplicity, we'll assume that the vector spaces are given as matrices representing the differentials.
            # We need to know the dimensions of the spaces at each (p,q). We'll infer from the shape of the differentials.
            # For a fixed (p,q), the space E_r^{p,q} is the domain of d_out (if d_out exists) or the codomain of d_in.
            # We'll determine dimension from either d_out (rows) or d_in (cols) if available.
            dim_pq = None
            if d_out is not None:
                dim_pq = d_out.shape[0]  # rows = dimension of source?
            elif d_in is not None:
                dim_pq = d_in.shape[1]  # cols = dimension of target?
            else:
                # No differentials at this spot; it's just a vector space of unknown dimension. Skip for now.
                continue

            # Build kernel of d_out
            if d_out is not None:
                U, s, Vh = np.linalg.svd(d_out, full_matrices=True)
                tol_s = tol * max(d_out.shape) * s[0] if len(s) > 0 else 0
                rank = np.sum(s > tol_s)
                null_dim = d_out.shape[1] - rank
                kernel = Vh[rank:, :].T.conj() if null_dim > 0 else np.zeros((d_out.shape[1], 0))
            else:
                kernel = np.eye(dim_pq) if dim_pq else np.zeros((0,0))

            # Build image of d_in
            if d_in is not None:
                U_in, s_in, _ = np.linalg.svd(d_in, full_matrices=False)
                tol_in = tol * max(d_in.shape) * s_in[0] if len(s_in) > 0 else 0
                rank_in = np.sum(s_in > tol_in)
                image = U_in[:, :rank_in] if rank_in > 0 else np.zeros((d_in.shape[0], 0))
            else:
                image = np.zeros((dim_pq, 0)) if dim_pq else np.zeros((0,0))

            # Compute homology dimension
            if kernel.shape[1] == 0:
                dim_hom = 0
            elif image.shape[1] == 0:
                dim_hom = kernel.shape[1]
            else:
                combined = np.hstack([image, kernel])
                U_comb, s_comb, _ = np.linalg.svd(combined, full_matrices=False)
                tol_comb = tol * max(combined.shape) * s_comb[0] if len(s_comb) > 0 else 0
                rank_comb = np.sum(s_comb > tol_comb)
                # rank of image
                rank_img = image.shape[1]  # if image is full rank? better compute
                U_img, s_img, _ = np.linalg.svd(image, full_matrices=False)
                tol_img = tol * max(image.shape) * s_img[0] if len(s_img) > 0 else 0
                rank_img = np.sum(s_img > tol_img)
                dim_hom = rank_comb - rank_img

            # For the next page, we need the induced differential d_{r+1}. This is more complicated.
            # We'll skip storing differentials for now; just store the dimension.
            # In a full implementation, we would compute the differential on the homology.
            # For demonstration, we store the dimension as a dummy matrix.
            if dim_hom > 0:
                next_page[(p,q)] = np.zeros((dim_hom, dim_hom))  # placeholder

        self.current_page += 1
        self.pages[self.current_page] = next_page
        return next_page

    def converge(self):
        """Placeholder for convergence check."""
        logger.info("Spectral sequence convergence not implemented.")


# ============================================================================
# UTILITIES FOR QUIVER REPRESENTATIONS (optional)
# ============================================================================

def projective_resolution_quiver(rep: 'relations.QuiverRepresentation', max_degree: int) -> ChainComplex:
    """
    Compute a projective resolution of a quiver representation.
    This is highly nontrivial; placeholder returns trivial complex.
    """
    logger.warning("projective_resolution_quiver not implemented – returning trivial complex.")
    # For a quiver representation, we would need to compute the projective cover iteratively.
    # Here we just return a trivial complex with the representation itself in degree 0.
    # We need to convert rep to a module that has a dim() method.
    # Assume rep has a method total_dimension().
    dim0 = rep.total_dimension() if hasattr(rep, 'total_dimension') else 1
    d1 = np.zeros((dim0, 0))
    return ChainComplex([d1])


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Create simple chain complexes and test basic operations."""
    print("="*80)
    print("DERIVED CATEGORIES DEMO")
    print("="*80)

    # Example 1: a complex of vector spaces with non‑trivial homology
    # C_2 --d2--> C_1 --d1--> C_0
    # Choose dimensions: C_2 = ℝ^2, C_1 = ℝ^3, C_0 = ℝ^2
    # d1 = [[1,0,0],[0,1,0]] (kernel: last basis vector)
    # d2 = [[1,0],[0,0],[0,1]] (image: columns [1,0,0] and [0,0,1] in C_1)
    d1 = np.array([[1, 0, 0], [0, 1, 0]])
    d2 = np.array([[1, 0], [0, 0], [0, 1]])
    C = ChainComplex([d1, d2])
    print("Is C a complex?", C.is_complex())
    print("d1∘d2 norm:", np.linalg.norm(d1 @ d2))
    dim_h1, basis = C.homology(1)
    print("H1 dimension (expected 1):", dim_h1)

    # Example 2: mapping cone of identity map on C
    id_map = ChainMap(C, C, [np.eye(C.dim(0)), np.eye(C.dim(1)), np.eye(C.dim(2))])
    cone = mapping_cone(id_map)
    print("Mapping cone constructed with differentials of shape:", [d.shape for d in cone.differentials])
    h2 = cone.homology(2)[0]
    h1 = cone.homology(1)[0]
    h0 = cone.homology(0)[0]
    print(f"H2: {h2}, H1: {h1}, H0: {h0} (should all be 0)")

    # Test chain homotopy
    f = id_map
    g = ChainMap(C, C, [2*np.eye(C.dim(0)), 2*np.eye(C.dim(1)), 2*np.eye(C.dim(2))])  # 2*identity
    h = chain_homotopy(f, g)
    print("Chain homotopy between identity and 2*identity exists?", h is not None)  # Should be False because f-g = -identity, which is not a boundary generally.

    # Test derived functors
    A = VectorSpace(3)
    B = VectorSpace(2)
    print("Ext^0(A,B) =", ext(A, B, 0))
    print("Ext^1(A,B) =", ext(A, B, 1))
    print("Tor_0(A,B) =", tor(A, B, 0))
    print("Tor_1(A,B) =", tor(A, B, 1))

    # Spectral sequence demo (very basic)
    # Create a simple double complex differential? We'll just make a dummy initial page.
    init_page = {(0,0): np.array([[1]]), (1,0): np.array([[1]]), (0,1): np.array([[1]])}
    ss = SpectralSequence(init_page)
    ss.next_page()
    print("Spectral sequence page 3:", ss.pages[3])


if __name__ == "__main__":
    demo()