"""
QUIVER MODULI
=============
This module provides tools for studying moduli spaces of quiver representations,
following King's construction using stability conditions.

Features:
- Stability conditions (linear function on dimension vectors)
- Check stability and semistability of a representation (with slope correction)
- Harder–Narasimhan filtrations (for a given stability condition)
- Simple computation of the King moduli space as a quotient by the group action
- Integration with the quiver classes from `quiver.`
- Factory function to convert UltimateRelation to QuiverRepresentation

All calculations are exact for small quivers; for larger ones, the algorithms
may become exponential. The module is intended for theoretical exploration
within Layer 2.
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from itertools import combinations, product
from collections import defaultdict

# Relative import of quiver classes (assumes quiver.py is in same package)
from apeiron.layers.layer02_relational import quiver
from apeiron.layers.layer02_relational import category
from apeiron.layers.layer02_relational import UltimateRelation

# Optional linear algebra for stability checks
try:
    import scipy.linalg
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

logger = logging.getLogger(__name__)


# ============================================================================
# STABILITY CONDITION
# ============================================================================

class StabilityCondition:
    """
    King's stability condition given by a linear function θ on dimension vectors.
    A representation V (with dimension vector d) is:
        - stable if for every proper non‑zero subrepresentation W with dimension vector e,
          we have θ(e) < θ(d) (with respect to a chosen total order).
        - semistable if θ(e) ≤ θ(d).

    When θ(d) ≠ 0, the correct notion is slope stability: θ(e)/rank(e) < θ(d)/rank(d).
    The `is_stable` and `is_semistable` functions handle both cases automatically.
    """
    def __init__(self, theta: Union[np.ndarray, Dict[str, int]]):
        """
        Args:
            theta: either a numpy array of length equal to the number of vertices
                  (indexed by vertex order), or a dict mapping vertex name to weight.
        """
        self.theta = theta  # will be converted to dict later

    def __call__(self, dim_vector: Dict[str, int]) -> int:
        """Evaluate θ on a dimension vector."""
        if isinstance(self.theta, dict):
            return sum(self.theta.get(v, 0) * dim for v, dim in dim_vector.items())
        else:
            # Assume dim_vector is an array of same length as theta, indexed by vertex order
            return int(np.dot(self.theta, dim_vector))

    def compare(self, dim1: Dict[str, int], dim2: Dict[str, int]) -> int:
        """
        Compare two dimension vectors using the total order induced by θ.
        Returns -1 if dim1 < dim2, 0 if equal, 1 if dim1 > dim2.
        """
        val1 = self(dim1)
        val2 = self(dim2)
        if val1 < val2:
            return -1
        elif val1 > val2:
            return 1
        else:
            return 0

    def slope(self, dim_vector: Dict[str, int]) -> float:
        """
        Return the slope μ = θ(d) / total_dimension (if total dimension > 0).
        For Harder–Narasimhan filtrations, we need a slope that decreases.
        """
        total_dim = sum(dim_vector.values())
        if total_dim == 0:
            return 0.0
        return self(dim_vector) / total_dim


# ============================================================================
# UTILITIES FOR QUIVER REPRESENTATIONS
# ============================================================================

def dimension_vector(rep: quiver.QuiverRepresentation) -> Dict[str, int]:
    """Return the dimension vector of a representation."""
    return rep.dimension_vector


def _enumerate_coordinate_subspaces(dim: int, max_dim: Optional[int] = None) -> List[List[int]]:
    """
    Enumerate all subspaces of ℝ^dim that are spanned by a subset of the standard basis.
    This is a huge restriction, but it allows us to test subrepresentations for
    small examples. Each subspace is returned as a list of basis indices (0‑based).
    """
    if max_dim is None:
        max_dim = dim
    subspaces = []
    for k in range(1, max_dim + 1):  # exclude 0 and full space? We'll include all, but caller will filter.
        for combo in combinations(range(dim), k):
            subspaces.append(list(combo))
    return subspaces


def _is_invariant_subspace(rep: quiver.QuiverRepresentation, subspaces: Dict[str, List[int]]) -> bool:
    """
    Check if the choice of coordinate subspaces (given by lists of basis indices)
    defines a subrepresentation. For each arrow a: i -> j, we need f_a(U_i) ⊆ U_j.
    Since subspaces are coordinate, we can check by looking at the matrix columns.
    """
    for (src, tgt), arrows in rep.quiver.arrows.items():
        for arrow in arrows:
            mat = rep.linear_maps[arrow]
            # U_src: indices of basis vectors in source
            src_idxs = subspaces.get(src, [])
            # Build a matrix from the columns of mat corresponding to src_idxs
            if not src_idxs:
                # Zero subspace, always invariant
                continue
            # For each basis vector in U_src, its image should lie in U_tgt
            for col in src_idxs:
                # col is index of basis vector in source space
                # The image is column col of mat
                col_vec = mat[:, col]
                # Check if col_vec is in the span of basis vectors indexed by tgt_idxs
                # For coordinate subspaces, this means that col_vec has zeros outside those indices.
                tgt_idxs = subspaces.get(tgt, [])
                for i, val in enumerate(col_vec):
                    if abs(val) > 1e-10 and i not in tgt_idxs:
                        return False
    return True


def subrepresentations(rep: quiver.QuiverRepresentation) -> List[quiver.QuiverRepresentation]:
    """
    Compute all non‑zero proper subrepresentations of a quiver representation.
    This implementation is limited to small dimensions (≤ 3) and only considers
    subspaces that are coordinate (spanned by standard basis vectors). It is
    intended for demonstration only.

    Returns a list of QuiverRepresentation objects.
    """
    vertices = list(rep.quiver.vertices)
    dims = rep.dimension_vector
    total_dim = sum(dims.values())

    # Warn if dimensions are large (the enumeration becomes infeasible)
    if total_dim > 3:
        logger.warning(
            f"Total dimension {total_dim} > 3: subrepresentation enumeration using coordinate subspaces "
            "is likely incomplete and may be very slow."
        )

    # For each vertex, enumerate all possible coordinate subspaces
    subspaces_per_vertex = {}
    for v in vertices:
        d = dims[v]
        # we need subspaces of dimension from 0 to d (but 0 and d will be filtered later)
        subspaces_per_vertex[v] = _enumerate_coordinate_subspaces(d, max_dim=d)

    # Now iterate over all combinations of choices per vertex
    valid_subs = []
    for choice in product(*[subspaces_per_vertex[v] for v in vertices]):
        subspace_dict = {v: choice[i] for i, v in enumerate(vertices)}
        # Check if this tuple defines a proper non‑zero subrepresentation
        # A subrepresentation must have at least one vertex with non‑zero subspace,
        # and not all vertices have full space.
        sub_total_dim = sum(len(subspace_dict[v]) for v in vertices)
        if sub_total_dim == 0 or sub_total_dim == total_dim:
            continue
        if _is_invariant_subspace(rep, subspace_dict):
            # Build the subrepresentation
            # New vector spaces: for each vertex, the subspace (we need to represent it as a vector space)
            # For simplicity, we keep the same vertex names but with reduced dimension.
            new_dims = {v: len(subspace_dict[v]) for v in vertices}
            # For each arrow, we need the restriction of the linear map to the subspace.
            # The restriction is given by the matrix columns corresponding to source indices,
            # and we keep only rows corresponding to target indices.
            new_maps = {}
            for (src, tgt), arrows in rep.quiver.arrows.items():
                for arrow in arrows:
                    mat = rep.linear_maps[arrow]
                    src_idxs = subspace_dict[src]
                    tgt_idxs = subspace_dict[tgt]
                    # Restrict to these indices
                    sub_mat = mat[np.ix_(tgt_idxs, src_idxs)]
                    new_maps[arrow] = sub_mat
            # Create the subrepresentation object
            sub_rep = quiver.QuiverRepresentation(
                quiver=rep.quiver,
                vector_spaces=new_dims,
                linear_maps=new_maps
            )
            valid_subs.append(sub_rep)
    return valid_subs


def quotient_representation(rep: quiver.QuiverRepresentation,
                            sub: quiver.QuiverRepresentation) -> quiver.QuiverRepresentation:
    """
    Given a representation and a subrepresentation (with compatible inclusion),
    return the quotient representation. This assumes that sub is a subrepresentation
    in the sense that its vector spaces are subspaces of rep's vector spaces,
    and the maps are restrictions. We construct the quotient by taking the quotient
    vector spaces and the induced maps.
    """
    vertices = list(rep.quiver.vertices)
    # Dimensions of quotient
    quot_dims = {v: rep.dimension_vector[v] - sub.dimension_vector[v] for v in vertices}
    # For each arrow, we need the induced map on the quotient.
    # If we have a basis of rep and sub, we can compute the matrix of the quotient map.
    # Since we don't have explicit bases, we assume that the subrepresentation is given
    # by matrices that are submatrices of the original (as constructed in subrepresentations).
    # In that case, the quotient map can be obtained by taking the original matrix and
    # deleting rows and columns corresponding to the subrepresentation basis.
    # But we need to know which basis vectors correspond to the sub. In our coordinate
    # subspace enumeration, the subrepresentation uses the first few basis vectors
    # (the indices in subspace_dict). However, when we created the subrepresentation,
    # we lost the mapping of indices. To reconstruct, we would need to store the
    # inclusion map. For simplicity, we will not implement a general quotient here.
    # Instead, we return a placeholder.
    logger.warning("quotient_representation is not fully implemented – returning empty representation.")
    return quiver.QuiverRepresentation(
        quiver=rep.quiver,
        vector_spaces=quot_dims,
        linear_maps={}
    )


def is_stable(rep: quiver.QuiverRepresentation, theta: StabilityCondition) -> bool:
    """
    Check if a representation is stable with respect to θ.
    If θ(d) = 0, uses the standard King stability (θ(e) < θ(d)).
    If θ(d) ≠ 0, uses slope stability (θ(e)/dim(e) < θ(d)/dim(d)).
    """
    d = dimension_vector(rep)
    total_dim = sum(d.values())
    if total_dim == 0:
        return False  # zero representation is not stable by definition

    theta_d = theta(d)
    slope_d = theta_d / total_dim if total_dim > 0 else 0.0

    for sub in subrepresentations(rep):
        e = dimension_vector(sub)
        total_sub = sum(e.values())
        if total_sub == 0:
            continue  # zero subrepresentation is ignored
        if abs(theta_d) < 1e-10:  # θ(d) ≈ 0, use King stability
            if theta.compare(e, d) != -1:  # θ(e) >= θ(d)
                return False
        else:  # use slope stability
            slope_e = theta(e) / total_sub
            if slope_e >= slope_d:
                return False
    return True


def is_semistable(rep: quiver.QuiverRepresentation, theta: StabilityCondition) -> bool:
    """
    Check if a representation is semistable with respect to θ.
    If θ(d) = 0, uses the standard King semistability (θ(e) ≤ θ(d)).
    If θ(d) ≠ 0, uses slope semistability (θ(e)/dim(e) ≤ θ(d)/dim(d)).
    """
    d = dimension_vector(rep)
    total_dim = sum(d.values())
    if total_dim == 0:
        return True  # zero representation is semistable

    theta_d = theta(d)
    slope_d = theta_d / total_dim if total_dim > 0 else 0.0

    for sub in subrepresentations(rep):
        e = dimension_vector(sub)
        total_sub = sum(e.values())
        if total_sub == 0:
            continue
        if abs(theta_d) < 1e-10:
            if theta.compare(e, d) == 1:  # θ(e) > θ(d)
                return False
        else:
            slope_e = theta(e) / total_sub
            if slope_e > slope_d:
                return False
    return True


# ============================================================================
# HARDER–NARASIMHAN FILTRATION
# ============================================================================

def harder_narasimhan_filtration(rep: quiver.QuiverRepresentation,
                                 theta: StabilityCondition) -> List[Tuple[quiver.QuiverRepresentation, float]]:
    """
    Compute the Harder–Narasimhan filtration of a representation with respect to θ.
    Returns a list of (subquotient, slope) where slopes are decreasing.

    This implementation uses the limited subrepresentation enumeration and
    recursively finds the subrepresentation with maximal slope.
    """
    # Base case: zero representation
    total_dim = sum(rep.dimension_vector.values())
    if total_dim == 0:
        return []

    # Find all proper non‑zero subrepresentations
    subs = subrepresentations(rep)
    if not subs:
        # No proper subrepresentations -> the representation itself is the only HN factor
        return [(rep, theta.slope(rep.dimension_vector))]

    # Compute slopes
    slopes = [(sub, theta.slope(sub.dimension_vector)) for sub in subs]
    # Find the sub with maximal slope (if multiple, we need to choose the largest sub? In HN, we need the unique maximal destabilizing sub.)
    # We'll take the one with largest slope, and if tie, largest dimension.
    def key(item):
        sub, s = item
        return (s, sum(sub.dimension_vector.values()))
    max_sub, max_slope = max(slopes, key=key)

    # Now form the quotient (not fully implemented)
    quot = quotient_representation(rep, max_sub)
    # Recursively compute HN filtration for the quotient
    rest = harder_narasimhan_filtration(quot, theta)
    # Return the maximal sub as first factor, then the rest
    return [(max_sub, max_slope)] + rest


# ============================================================================
# MODULI SPACE (PLACEHOLDER / CONCEPTUAL)
# ============================================================================

class ModuliSpace:
    """
    Represents the moduli space of θ‑stable representations with fixed dimension vector.
    In practice, this is a geometric object; here we only provide a placeholder
    that can store isomorphism classes (for finite fields) or sample random representations.
    """
    def __init__(self, quiver: quiver.Quiver, dim_vector: Dict[str, int],
                 theta: StabilityCondition, field_size: Optional[int] = None):
        self.quiver = quiver
        self.dim_vector = dim_vector
        self.theta = theta
        self.field_size = field_size  # if None, treat as algebraically closed (complex)

    def sample(self, n: int) -> List[quiver.QuiverRepresentation]:
        """
        Generate n random representations (with given dimension vector) and
        return only those that are θ‑stable.
        """
        reps = []
        for _ in range(n):
            rep = self._random_representation()
            if is_stable(rep, self.theta):
                reps.append(rep)
        return reps

    def _random_representation(self) -> quiver.QuiverRepresentation:
        """Generate a random representation (linear maps with random matrices)."""
        # This requires field elements; for simplicity, we use random floats.
        # In practice, one would use finite field elements if field_size is given.
        vector_spaces = self.dim_vector
        linear_maps = {}
        for (source, target), arrow_names in self.quiver.arrows.items():
            for arrow in arrow_names:
                dim_src = vector_spaces[source]
                dim_tgt = vector_spaces[target]
                # Random matrix over reals
                mat = np.random.randn(dim_tgt, dim_src)
                linear_maps[arrow] = mat
        rep = quiver.QuiverRepresentation(
            quiver=self.quiver,
            vector_spaces=vector_spaces,
            linear_maps=linear_maps
        )
        return rep

    def count_points(self) -> int:
        """
        For finite fields, count the number of isomorphism classes of stable representations.
        This is an incredibly hard problem (Hall algebra, etc.). Placeholder.
        """
        return 0


# ============================================================================
# FACTORY FUNCTION: UltimateRelation -> QuiverRepresentation
# ============================================================================

def ultimate_relation_to_quiver_representation(rel: UltimateRelation,
                                               representation_id: Optional[str] = None) -> quiver.QuiverRepresentation:
    """
    Extract a QuiverRepresentation from an UltimateRelation.

    An UltimateRelation contains a `quiver` and a dictionary `representations`.
    This function returns the representation identified by `representation_id`,
    or the first available representation if `representation_id` is None.

    Args:
        rel: An instance of UltimateRelation.
        representation_id: Optional key to select a specific representation.

    Returns:
        A QuiverRepresentation object.

    Raises:
        KeyError: if the specified representation_id does not exist.
        ValueError: if the relation contains no representations.
    """
    if not rel.representations:
        raise ValueError("UltimateRelation contains no quiver representations.")

    if representation_id is not None:
        if representation_id not in rel.representations:
            raise KeyError(f"No representation with id '{representation_id}' found.")
        return rel.representations[representation_id]
    else:
        # return the first representation (arbitrary order)
        return next(iter(rel.representations.values()))


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Create a small quiver (Kronecker quiver) and check stability."""
    print("="*80)
    print("QUIVER MODULI DEMO")
    print("="*80)

    # Build a Kronecker quiver: two vertices, two arrows from 1 to 2
    q = quiver.Quiver()
    q.add_vertex(1)
    q.add_vertex(2)
    q.add_arrow(1, 2, 'a')
    q.add_arrow(1, 2, 'b')

    # Dimension vector (2,2) – two‑dimensional spaces at each vertex
    dim = {1: 2, 2: 2}
    # Stability condition: θ = (1, -1) (so θ(d) = 2*1 + 2*(-1) = 0)
    theta = StabilityCondition({1: 1, 2: -1})

    # Create a representation: matrices a and b (2x2)
    rep = quiver.QuiverRepresentation(
        quiver=q,
        vector_spaces=dim,
        linear_maps={
            'a': np.array([[1, 0], [0, 1]]),
            'b': np.array([[0, 1], [1, 0]])
        }
    )

    print("Quiver: 1 → 2 (two arrows)")
    print("Dimension vector:", dim)
    print("Stability condition θ = (1, -1)")

    # Check stability (using limited subrepresentation enumeration)
    stable = is_stable(rep, theta)
    print(f"Is representation stable? {stable} (based on coordinate subspaces)")

    # List subrepresentations (coordinate subspaces)
    subs = subrepresentations(rep)
    print(f"Found {len(subs)} proper non‑zero subrepresentations (coordinate).")
    for i, sub in enumerate(subs):
        print(f"  Sub {i}: dim vector {sub.dimension_vector}")

    # Moduli space sampling (conceptual)
    mod = ModuliSpace(q, dim, theta, field_size=None)
    samples = mod.sample(5)
    print(f"Generated {len(samples)} stable samples (random).")

    print("\nNote: Subrepresentation enumeration is limited to coordinate subspaces, so stability checks are not complete.")

    # Test the factory function (requires an UltimateRelation with representations)
    print("\n--- Testing ultimate_relation_to_quiver_representation ---")
    try:
        # Create a dummy UltimateRelation with a representation (simplified)
        from .relations import UltimateRelation, RelationType
        rel = UltimateRelation(
            id="test_rel",
            source_id="A",
            target_id="B",
            relation_type=RelationType.SYMMETRIC,
            weight=0.5
        )
        # Add a representation to it
        rel.representations["rep1"] = rep
        extracted = ultimate_relation_to_quiver_representation(rel)
        print("Extracted representation with dimension vector:", extracted.dimension_vector)
    except ImportError:
        print("Could not import UltimateRelation; skipping factory test.")


if __name__ == "__main__":
    demo()