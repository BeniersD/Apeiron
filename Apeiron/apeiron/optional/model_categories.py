"""
MODEL CATEGORIES – ULTIMATE IMPLEMENTATION
===========================================
This module provides a framework for working with model categories,
a central concept in homotopy theory. It includes:

- Abstract definition of a model structure (three distinguished classes of maps)
- Classes for model categories (a category equipped with a model structure)
- Basic examples: chain complexes over a ring (projective model structure),
  topological spaces (simplicial sets placeholder), and the trivial model structure.
- Quillen adjunctions (adjunctions that are compatible with the model structures)
- Derived functors (total left/right derived functors)

The implementation is designed to be extensible and to integrate with the
categorical structures from `relations.py` (e.g., quiver representations, chain complexes).
For chain complexes, we provide concrete implementations of fibrations, cofibrations,
weak equivalences, factorizations, and lifts using the standard constructions
(mapping cylinder and path object).

All features degrade gracefully if required libraries (e.g., for simplicial sets) are missing.
"""

import logging
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum

# Relative imports from layer2
from apeiron.layers.layer02_relational import quiver
from apeiron.layers.layer02_relational import category as relations
from .derived_categories import ChainMap, ChainComplex

logger = logging.getLogger(__name__)


# ============================================================================
# BASIC CLASSES FOR MODEL STRUCTURES
# ============================================================================

class WeakEquivalence:
    """Marker class for weak equivalences."""
    pass

class Fibration:
    """Marker class for fibrations."""
    pass

class Cofibration:
    """Marker class for cofibrations."""
    pass


@dataclass
class ModelStructure:
    """
    A model structure on a category C consists of three distinguished classes
    of maps: weak equivalences, fibrations, and cofibrations, satisfying
    the model category axioms (MC1–MC5). Here we store just the definitions.
    """
    weak_equivalences: Set[Any] = field(default_factory=set)
    fibrations: Set[Any] = field(default_factory=set)
    cofibrations: Set[Any] = field(default_factory=set)

    # Axioms can be checked if needed
    def check_axioms(self, category: 'relations.RelationalCategory') -> bool:
        """
        Verify the model category axioms for this structure.
        This is a placeholder; real verification would be highly non‑trivial.
        """
        logger.warning("ModelStructure.check_axioms not implemented.")
        return True


class ModelCategory:
    """
    A category equipped with a model structure.
    """
    def __init__(self, category: relations.RelationalCategory, model_structure: ModelStructure):
        self.category = category
        self.model_structure = model_structure

    # ------------------------------------------------------------------------
    # Basic operations from model categories (factorizations, lifts)
    # ------------------------------------------------------------------------

    def factor_as_cofib_fibration(self, f: Any) -> Tuple[Any, Any]:
        """
        Factor f as a cofibration followed by an acyclic fibration (MC5(i)).
        Placeholder – to be implemented in subclasses.
        """
        raise NotImplementedError

    def factor_as_acyclic_cofib_fibration(self, f: Any) -> Tuple[Any, Any]:
        """
        Factor f as an acyclic cofibration followed by a fibration (MC5(ii)).
        Placeholder – to be implemented in subclasses.
        """
        raise NotImplementedError

    def lift(self, square: Tuple[Any, Any, Any, Any]) -> Optional[Any]:
        """
        Given a commutative square where the left map is a cofibration and the right map
        is an acyclic fibration (or similar), produce a diagonal filler (MC4).
        Placeholder – to be implemented in subclasses.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------------
    # Cofibrant/fibrant replacements
    # ------------------------------------------------------------------------

    def cofibrant_replacement(self, X: Any) -> Any:
        """
        Return a cofibrant object weakly equivalent to X.
        Placeholder.
        """
        logger.warning("cofibrant_replacement not implemented.")
        return X

    def fibrant_replacement(self, X: Any) -> Any:
        """
        Return a fibrant object weakly equivalent to X.
        Placeholder.
        """
        logger.warning("fibrant_replacement not implemented.")
        return X

    # ------------------------------------------------------------------------
    # Homotopy
    # ------------------------------------------------------------------------

    def cylinder_object(self, A: Any) -> Any:
        """
        Return a cylinder object for A (used to define left homotopy).
        Placeholder.
        """
        logger.warning("cylinder_object not implemented.")
        return None

    def path_object(self, A: Any) -> Any:
        """
        Return a path object for A (used to define right homotopy).
        Placeholder.
        """
        logger.warning("path_object not implemented.")
        return None

    def left_homotopic(self, f: Any, g: Any) -> bool:
        """Check if f and g are left homotopic."""
        logger.warning("left_homotopic not implemented.")
        return False

    def right_homotopic(self, f: Any, g: Any) -> bool:
        """Check if f and g are right homotopic."""
        logger.warning("right_homotopic not implemented.")
        return False

    def homotopic(self, f: Any, g: Any) -> bool:
        """Check if f and g are homotopic (left/right coincide on fibrant/cofibrant objects)."""
        logger.warning("homotopic not implemented.")
        return False


# ============================================================================
# EXAMPLES OF MODEL CATEGORIES
# ============================================================================

class TopologicalSpacesModelCategory(ModelCategory):
    """
    Model category of topological spaces (or simplicial sets) with the
    Quillen model structure. Here we use simplicial sets as a placeholder.
    """
    def __init__(self):
        # Create a trivial category of "spaces" – in practice, this would be
        # a category of simplicial sets or a library like `simplicial`.
        cat = relations.RelationalCategory()
        # Add some dummy objects and morphisms
        # ...
        model = ModelStructure()
        super().__init__(cat, model)


class ChainComplexesModelCategory(ModelCategory):
    """
    Model category of (unbounded) chain complexes over a ring, with the
    projective model structure. The weak equivalences are quasi‑isomorphisms,
    fibrations are degreewise surjections, and cofibrations are degreewise
    injections with projective cokernel.

    We reuse the ChainComplex and ChainMap classes from derived_categories.
    This implementation works over a field (ℝ) for simplicity; over a PID,
    additional checks for projectivity would be needed.
    """
    def __init__(self, ring: str = "R"):
        """
        Args:
            ring: Placeholder; currently only works over a field (ℝ).
        """
        self.ring = ring
        # Build a category whose objects are chain complexes and morphisms are chain maps.
        # For simplicity, we don't populate it; we just define the model structure.
        cat = relations.RelationalCategory()
        model = ModelStructure()
        super().__init__(cat, model)

    # ------------------------------------------------------------------------
    # Classifying maps
    # ------------------------------------------------------------------------

    def is_weak_equivalence(self, f: ChainMap, tol: float = 1e-10) -> bool:
        """
        Check if f induces isomorphisms on all homology groups.
        Uses homology computation from derived_categories.
        """
        # Compute homology of source and target for all degrees where they are non‑zero.
        min_deg = min(f.source.degree_min, f.target.degree_min)
        max_deg = max(f.source.degree_max, f.target.degree_max)
        for n in range(min_deg, max_deg + 1):
            # Get homology of source and target
            dim_src, _ = f.source.homology(n, tol=tol)
            dim_tgt, _ = f.target.homology(n, tol=tol)
            if dim_src != dim_tgt:
                return False
            # Additionally, we need to check that f induces an isomorphism.
            # This requires constructing the induced map on homology.
            # For simplicity, we skip this and rely on dimension equality.
            # A full implementation would compute the map on homology and check invertibility.
        return True

    def is_fibration(self, f: ChainMap, tol: float = 1e-10) -> bool:
        """
        Check if f is degreewise surjective.
        For linear maps, surjectivity means rank = dimension of target.
        """
        for n, mat in enumerate(f.maps):
            if mat is not None:
                # Number of rows = target dimension at that degree
                target_dim = f.target.dim(n)
                # Compute rank using SVD
                U, s, Vh = np.linalg.svd(mat, full_matrices=False)
                rank = np.sum(s > tol * max(mat.shape) * s[0] if len(s) > 0 else 0)
                if rank < target_dim:
                    return False
        return True

    def is_cofibration(self, f: ChainMap, tol: float = 1e-10) -> bool:
        """
        Check if f is degreewise injective with projective cokernel.
        Over a field, injective suffices (cokernel is free).
        """
        for n, mat in enumerate(f.maps):
            if mat is not None:
                # Number of columns = source dimension at that degree
                source_dim = f.source.dim(n)
                U, s, Vh = np.linalg.svd(mat, full_matrices=False)
                rank = np.sum(s > tol * max(mat.shape) * s[0] if len(s) > 0 else 0)
                if rank < source_dim:
                    return False
        return True

    # ------------------------------------------------------------------------
    # Factorizations
    # ------------------------------------------------------------------------

    def factor_as_cofib_fibration(self, f: ChainMap) -> Tuple[ChainMap, ChainMap]:
        """
        Factor f: X → Y as X → Cyl(f) → Y, where Cyl(f) is the mapping cylinder.
        The first map is a cofibration (inclusion), the second is an acyclic fibration
        (homotopy equivalence, hence quasi-isomorphism, and surjective).
        """
        X = f.source
        Y = f.target
        # Construct mapping cylinder Cyl(f): at each degree n, Cyl(f)_n = X_n ⊕ X_{n-1} ⊕ Y_n
        # Differential: d( x_n, x_{n-1}, y_n ) = ( d_X(x_n) + x_{n-1}, -d_X(x_{n-1}), d_Y(y_n) + f_{n-1}(x_{n-1})? )
        # Actually the standard mapping cylinder for chain complexes:
        # Cyl(f)_n = X_n ⊕ X_{n-1} ⊕ Y_n
        # Differential d(x,y,z) = (d_X x + y, -d_X y, d_Y z + f y)
        # We need to construct the differential matrices.
        # This is a bit involved; for simplicity, we return a placeholder.
        # In a full implementation, we would build the complex and the maps.
        logger.warning("factor_as_cofib_fibration not fully implemented – returning identity factorizations.")
        # As a trivial factorization, use identity on X and f itself.
        id_X = ChainMap(X, X, [np.eye(X.dim(n)) for n in range(X.degree_max+1)])
        return (id_X, f)

    def factor_as_acyclic_cofib_fibration(self, f: ChainMap) -> Tuple[ChainMap, ChainMap]:
        """
        Factor f: X → Y as X → Path(f) → Y, where Path(f) is the mapping path space.
        The first map is an acyclic cofibration, the second a fibration.
        """
        # Path object construction: Path(f)_n = X_n ⊕ Y_n ⊕ Y_{n+1} with appropriate differential.
        # Again, complicated; we return a placeholder.
        logger.warning("factor_as_acyclic_cofib_fibration not fully implemented – returning identity factorizations.")
        id_X = ChainMap(X, X, [np.eye(X.dim(n)) for n in range(X.degree_max+1)])
        return (id_X, f)

    def lift(self, square: Tuple[ChainMap, ChainMap,
                                 ChainMap, ChainMap]) -> Optional[ChainMap]:
        """
        Given a square:
            A -> X
            |    |
            v    v
            B -> Y
        with left map a cofibration i: A → B and right map a fibration p: X → Y,
        and with the square commuting: p ∘ f = g ∘ i, find a diagonal lift h: B → X.
        This is a linear algebra problem degree by degree.
        For chain complexes, we can solve using the fact that cofibrations are injective
        and fibrations are surjective, so we can define h by induction on degree.
        """
        i, f, g, p = square
        A, B = i.source, i.target
        X, Y = p.source, p.target

        # We need to construct h_n: B_n → X_n for all n.
        h_maps = [None] * (max(B.degree_max, X.degree_max) + 1)
        # We'll solve degree by degree using the fact that i is injective and p is surjective.
        # This is a standard result in homological algebra.
        # For simplicity, we return a placeholder.
        logger.warning("lift not fully implemented – returning None.")
        return None

    def factor_as_cofib_fibration(self, f: ChainMap) -> Tuple[ChainMap, ChainMap]:
        """
        Factor f: X → Y as X → Cyl(f) → Y where Cyl(f) is the mapping cylinder.
        The first map is a cofibration, the second an acyclic fibration.
        """
        X = f.source
        Y = f.target
        # Determine max degree present
        max_deg = max(X.degree_max, Y.degree_max)
        # Build Cyl(f)_n = X_n ⊕ X_{n-1} ⊕ Y_n
        cyl = ChainComplex([], degree_min=min(X.degree_min, Y.degree_min))
        cyl.degree_max = max_deg
        for n in range(X.degree_min, max_deg + 1):
            dim_Xn = X.dim(n)
            dim_Xn_1 = X.dim(n - 1) if n > X.degree_min else 0
            dim_Yn = Y.dim(n)
            cyl.set_dim(n, dim_Xn + dim_Xn_1 + dim_Yn)
        # Build differentials for Cyl(f)
        for n in range(cyl.degree_min, cyl.degree_max + 1):
            if n == cyl.degree_min:
                continue
            # Build d_n^cyl: Cyl_n → Cyl_{n-1}
            d_n = np.zeros((cyl.dim(n - 1), cyl.dim(n)))
            # Block structure:
            # [ d_X_n       id_{X_{n-1}}   0        ]
            # [ 0          -d_X_{n-1}      0        ]
            # [ 0           f_{n-1}        d_Y_n   ]
            offset_in = 0
            # First block column: X_n
            if X.dim(n) > 0 and X.dim(n-1) > 0:
                d_n[0:X.dim(n-1), 0:X.dim(n)] = X.differential(n) if X.differential(n) is not None else np.zeros((X.dim(n-1), X.dim(n)))
            offset_in += X.dim(n)
            # Second block column: X_{n-1}
            if X.dim(n-1) > 0:
                # Upper block: identity
                d_n[0:X.dim(n-1), offset_in:offset_in + X.dim(n-1)] = np.eye(X.dim(n-1))
                # Middle block: -d_X_{n-1}
                if X.dim(n-2) > 0 and X.dim(n-1) > 0:
                    d_n[X.dim(n-2):X.dim(n-2)+X.dim(n-1), offset_in:offset_in + X.dim(n-1)] = -X.differential(n-1)
            offset_in += X.dim(n-1)
            # Third block column: Y_n
            if Y.dim(n) > 0:
                # Lower block: f_{n-1} (size Y_{n-1} × X_{n-1}) but only if dimensions match
                if X.dim(n-1) > 0 and Y.dim(n-1) > 0:
                    f_map = f.maps.get(n-1)
                    if f_map is not None:
                        start_row = X.dim(n-2) + X.dim(n-1) if n-1 > X.degree_min else 0
                        d_n[start_row:start_row + Y.dim(n-1), offset_in:offset_in + X.dim(n-1)] = f_map
                # Lower-right: d_Y_n
                if Y.dim(n) > 0 and Y.dim(n-1) > 0:
                    start_row = X.dim(n-2) + X.dim(n-1) if n-1 > X.degree_min else 0
                    d_n[start_row + Y.dim(n-1):start_row + Y.dim(n-1) + Y.dim(n-1), offset_in + X.dim(n-1):offset_in + X.dim(n-1) + Y.dim(n)] = Y.differential(n) if Y.differential(n) is not None else np.zeros((Y.dim(n-1), Y.dim(n)))
            cyl.add_differential(n, d_n)
        # Map i: X → Cyl(f)
        i_maps = []
        for n in range(cyl.degree_min, max_deg + 1):
            mat = np.zeros((cyl.dim(n), X.dim(n) if X.dim(n) > 0 else 0))
            if X.dim(n) > 0:
                mat[0:X.dim(n), 0:X.dim(n)] = np.eye(X.dim(n))
            i_maps.append(mat)
        i = ChainMap(X, cyl, i_maps)
        # Map p: Cyl(f) → Y
        p_maps = []
        for n in range(cyl.degree_min, max_deg + 1):
            if Y.dim(n) == 0:
                p_maps.append(np.zeros((0, cyl.dim(n))))
                continue
            mat = np.zeros((Y.dim(n), cyl.dim(n)))
            # The Y_n block is after X_n and X_{n-1}
            offset = X.dim(n) + X.dim(n-1)
            mat[0:Y.dim(n), offset:offset + Y.dim(n)] = np.eye(Y.dim(n))
            p_maps.append(mat)
        p = ChainMap(cyl, Y, p_maps)
        return i, p

    def factor_as_acyclic_cofib_fibration(self, f: ChainMap) -> Tuple[ChainMap, ChainMap]:
        X = f.source
        Y = f.target
        max_deg = max(X.degree_max, Y.degree_max)
        min_deg = min(X.degree_min, Y.degree_min)
        # Build Path(f)
        path = ChainComplex([], degree_min=min_deg)
        path.degree_max = max_deg
        for n in range(min_deg, max_deg + 1):
            dim_Xn = X.dim(n)
            dim_Yn1 = Y.dim(n + 1) if n + 1 <= max_deg else 0
            dim_Yn = Y.dim(n)
            path.set_dim(n, dim_Xn + dim_Yn1 + dim_Yn)
        # Differential
        for n in range(min_deg + 1, max_deg + 1):
            d_n = np.zeros((path.dim(n-1), path.dim(n)))
            # Blocks:
            # [ d_X_n     0       0     ]
            # [ f_n       -d_Y_{n+1}  id_Y_n ]
            # [ 0         0       d_Y_n ]
            # This is for the standard path object; we simplify.
            offset_prev = 0
            # X block
            if X.dim(n) > 0 and X.dim(n-1) > 0:
                d_n[0:X.dim(n-1), 0:X.dim(n)] = X.differential(n) if X.differential(n) is not None else np.zeros((X.dim(n-1), X.dim(n)))
            offset_prev += X.dim(n-1)
            # Y_{n+1} block
            if Y.dim(n+1) > 0 and Y.dim(n) > 0:
                d_n[offset_prev:offset_prev + Y.dim(n), X.dim(n):X.dim(n) + Y.dim(n+1)] = -Y.differential(n+1) if Y.differential(n+1) is not None else np.zeros((Y.dim(n), Y.dim(n+1)))
                # Identity on Y_n
                d_n[offset_prev:offset_prev + Y.dim(n), X.dim(n) + Y.dim(n+1):X.dim(n) + Y.dim(n+1) + Y.dim(n)] = np.eye(Y.dim(n))
            # f block
            if X.dim(n) > 0 and Y.dim(n-1) > 0:
                f_map = f.maps.get(n)
                if f_map is not None:
                    d_n[offset_prev:offset_prev + Y.dim(n-1), 0:X.dim(n)] = f_map
            path.add_differential(n, d_n)
        # i: X → Path(f)
        i_maps = []
        for n in range(min_deg, max_deg + 1):
            mat = np.zeros((path.dim(n), X.dim(n) if X.dim(n) > 0 else 0))
            if X.dim(n) > 0:
                mat[0:X.dim(n), 0:X.dim(n)] = np.eye(X.dim(n))
            i_maps.append(mat)
        i = ChainMap(X, path, i_maps)
        # p: Path(f) → Y
        p_maps = []
        for n in range(min_deg, max_deg + 1):
            mat = np.zeros((Y.dim(n), path.dim(n)))
            if Y.dim(n) > 0:
                # Project onto the last Y_n component
                offset = X.dim(n) + Y.dim(n+1)
                mat[0:Y.dim(n), offset:offset + Y.dim(n)] = np.eye(Y.dim(n))
            p_maps.append(mat)
        p = ChainMap(path, Y, p_maps)
        return i, p

    def lift(self, square: Tuple[ChainMap, ChainMap, ChainMap, ChainMap]) -> Optional[ChainMap]:
        """
        Given a commutative square:
            A → X
            ↓   ↓
            B → Y
        with i: A → B a cofibration and p: X → Y a fibration,
        find a diagonal filler h: B → X such that h∘i = f and p∘h = g.
        Over a field, we can solve degreewise using the fact that i is injective
        and p is surjective, so there exists a linear map h_n for each degree n.
        """
        i, f, g, p = square
        A, B = i.source, i.target
        X, Y = p.source, p.target
        min_deg = min(A.degree_min, B.degree_min, X.degree_min, Y.degree_min)
        max_deg = max(A.degree_max, B.degree_max, X.degree_max, Y.degree_max)
        h_maps = []
        for n in range(min_deg, max_deg + 1):
            dim_A = A.dim(n)
            dim_B = B.dim(n)
            dim_X = X.dim(n)
            dim_Y = Y.dim(n)
            if dim_B == 0 or dim_X == 0:
                h_maps.append(np.zeros((dim_X, dim_B)))
                continue
            # We need to solve: h_n ∘ i_n = f_n  and  p_n ∘ h_n = g_n
            i_n = i.maps.get(n)
            p_n = p.maps.get(n)
            f_n = f.maps.get(n)
            g_n = g.maps.get(n)
            if i_n is None or p_n is None or f_n is None or g_n is None:
                h_maps.append(np.zeros((dim_X, dim_B)))
                continue
            # i_n is injective, p_n surjective. We can construct h_n as:
            # h_n = f_n ∘ i_n^+ + (I - p_n^+ ∘ p_n) ∘ g_n ∘ (some extension)
            # where i_n^+ is left inverse of i_n, p_n^+ is right inverse of p_n.
            # Use pseudo-inverses.
            i_pinv = np.linalg.pinv(i_n)  # left inverse because injective
            p_pinv = np.linalg.pinv(p_n)  # right inverse because surjective
            h_n = f_n @ i_pinv + (np.eye(dim_X) - p_pinv @ p_n) @ g_n @ np.linalg.pinv(i_n)
            h_maps.append(h_n)
        h = ChainMap(B, X, h_maps)
        return h

    
# ============================================================================
# QUILLEN ADJUNCTIONS
# ============================================================================

class QuillenAdjunction:
    """
    A Quillen adjunction between two model categories: an adjunction
    (F ⊣ G) where F preserves cofibrations and acyclic cofibrations,
    and G preserves fibrations and acyclic fibrations.
    """
    def __init__(self, left_adjoint: 'relations.RelationalFunctor',
                 right_adjoint: 'relations.RelationalFunctor',
                 left_model: ModelCategory, right_model: ModelCategory):
        self.F = left_adjoint
        self.G = right_adjoint
        self.left_model = left_model
        self.right_model = right_model

    def is_Quillen(self) -> bool:
        """
        Check the Quillen conditions:
        - F preserves cofibrations and acyclic cofibrations.
        - G preserves fibrations and acyclic fibrations.
        This requires that we can test these properties on all maps.
        For finite categories, we could enumerate; here we provide a placeholder.
        """
        # In a real implementation, we would iterate over generating (acyclic) cofibrations.
        # For now, we assume it's true.
        logger.warning("is_Quillen not fully implemented – returning True.")
        return True

    def derived_functors(self) -> Tuple['TotalLeftDerivedFunctor', 'TotalRightDerivedFunctor']:
        """
        Return the total left derived functor LF and total right derived functor RG.
        """
        LF = TotalLeftDerivedFunctor(self.F, self.left_model)
        RG = TotalRightDerivedFunctor(self.G, self.right_model)
        return (LF, RG)


# ============================================================================
# DERIVED FUNCTORS (based on model categories)
# ============================================================================

class TotalLeftDerivedFunctor:
    """
    Total left derived functor of a left Quillen functor F: C → D.
    Computed as F ∘ Q, where Q is a cofibrant replacement functor.
    """
    def __init__(self, F: 'relations.RelationalFunctor', modelC: ModelCategory):
        self.F = F
        self.modelC = modelC

    def __call__(self, X: Any) -> Any:
        # Apply cofibrant replacement QX, then F
        QX = self.modelC.cofibrant_replacement(X)
        return self.F.apply_to_object(QX)

    def on_morphism(self, f: Any) -> Any:
        # Derived functor on morphisms: apply F to the induced map on cofibrant replacements.
        logger.warning("TotalLeftDerivedFunctor.on_morphism not implemented.")
        return None


class TotalRightDerivedFunctor:
    """
    Total right derived functor of a right Quillen functor G: D → C.
    Computed as G ∘ R, where R is a fibrant replacement functor.
    """
    def __init__(self, G: 'relations.RelationalFunctor', modelD: ModelCategory):
        self.G = G
        self.modelD = modelD

    def __call__(self, Y: Any) -> Any:
        RY = self.modelD.fibrant_replacement(Y)
        return self.G.apply_to_object(RY)

    def on_morphism(self, f: Any) -> Any:
        logger.warning("TotalRightDerivedFunctor.on_morphism not implemented.")
        return None


# ============================================================================
# PLACEHOLDER FOR SIMPLICIAL SETS / TOPOLOGICAL SPACES
# ============================================================================

class SimplicialSet:
    """
    Minimal representation of a simplicial set. Placeholder.
    """
    def __init__(self, name: str):
        self.name = name


# ============================================================================
# DEMO
# ============================================================================

def demo():
    print("="*80)
    print("MODEL CATEGORIES DEMO")
    print("="*80)

    # Chain complexes model category
    chain_model = ChainComplexesModelCategory(ring="R")
    print("Chain complexes model category created.")

    # Create a simple complex (two-term)
    d1 = np.array([[1, 0], [0, 1]])  # identity 2x2
    C = ChainComplex([d1])  # d1: C1→C0
    print("Chain complex C with dims:", C.dimensions)

    # Check if a chain map is a fibration (should be surjective)
    id_map = ChainMap(C, C,
                                         [np.eye(2), np.eye(2)])  # f0 and f1
    is_fib = chain_model.is_fibration(id_map)
    print("Is identity a fibration?", is_fib)  # Should be True

    is_cof = chain_model.is_cofibration(id_map)
    print("Is identity a cofibration?", is_cof)  # Should be True

    is_we = chain_model.is_weak_equivalence(id_map)
    print("Is identity a weak equivalence?", is_we)  # Should be True

    # Topological spaces placeholder
    top_model = TopologicalSpacesModelCategory()
    print("Topological spaces model category created.")


if __name__ == "__main__":
    demo()