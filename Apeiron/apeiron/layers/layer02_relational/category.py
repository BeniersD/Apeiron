"""
category.py – Categorical structures for Layer 2 (Relational Dynamics)
========================================================================
Provides classes for categories, functors, natural transformations,
adjunctions, monads, limits, colimits, Kan extensions, Yoneda embedding,
and enriched categories.

All classes are pure data structures; verification of axioms is deferred
to `categorical_verification.py`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper import from sibling module (for morphism equality checks)
# ---------------------------------------------------------------------------
try:
    from .categorical_verification import _morphisms_equal
except ImportError:
    # Fallback if the verification module is not loaded (e.g., standalone tests)
    def _morphisms_equal(cat, f, g):
        return f is g or f == g
    logger.warning("categorical_verification not available; morphism equality is shallow.")


# ============================================================================
# Enums
# ============================================================================

class FunctorType(Enum):
    COVARIANT = "covariant"
    CONTRAVARIANT = "contravariant"
    MONOIDAL = "monoidal"
    ADJOINT = "adjoint"
    DERIVED = "derived"
    QUANTUM = "quantum"
    ENRICHED = "enriched"
    LAX = "lax"
    OPLAX = "oplax"


class NaturalTransformationType(Enum):
    ISOMORPHISM = "isomorphism"
    MONO = "mono"
    EPI = "epi"
    EQUIVALENCE = "equivalence"
    MODIFICATION = "modification"


class AdjunctionType(Enum):
    LEFT = "left"
    RIGHT = "right"
    MONOIDAL = "monoidal"
    QUANTUM = "quantum"


# ============================================================================
# RelationalCategory
# ============================================================================

@dataclass
class RelationalCategory:
    """
    A category with objects and morphisms.

    Morphisms are stored in hom_sets: (source, target) -> set of morphisms.
    Composition must be associative and unital.

    NOTE: Composition of general UltimateRelation objects is not semantically
    defined. The default composition works for numbers, lists, and callables;
    for other types a custom composition function should be supplied.
    """
    objects: Set[Any] = field(default_factory=set)
    hom_sets: Dict[Tuple[Any, Any], Set[Any]] = field(default_factory=dict)
    identities: Dict[Any, Any] = field(default_factory=dict)  # id_A
    composition: Optional[Callable] = None

    def __post_init__(self):
        if self.composition is None:
            self.composition = self._default_composition

    def _default_composition(
        self, f: Any, g: Any, source: Any, middle: Any, target: Any
    ) -> Any:
        """
        Default composition: if f and g are numbers, multiply;
        if lists, concatenate; if callables, compose.
        For UltimateRelation objects we return a placeholder string.
        """
        if isinstance(f, (int, float)) and isinstance(g, (int, float)):
            return f * g
        if isinstance(f, list) and isinstance(g, list):
            return f + g
        if callable(f) and callable(g):
            return lambda x: f(g(x))
        # Fallback for objects with id attribute
        if hasattr(f, 'id') and hasattr(g, 'id'):
            return f"{f.id}∘{g.id}"
        return None

    def add_object(self, obj: Any) -> None:
        self.objects.add(obj)
        if obj not in self.identities:
            identity = f"id_{obj}"
            self.identities[obj] = identity
            self.add_morphism(obj, obj, identity)

    def add_morphism(self, source: Any, target: Any, morphism: Any) -> None:
        key = (source, target)
        if key not in self.hom_sets:
            self.hom_sets[key] = set()
        self.hom_sets[key].add(morphism)

    def compose(
        self,
        f: Any,
        g: Any,
        f_source: Any,
        f_target: Any,
        g_target: Any,
    ) -> Optional[Any]:
        """
        Compose f: f_source → f_target and g: f_target → g_target.
        Returns g∘f: f_source → g_target, or None if composition fails.
        """
        if (f_source, f_target) not in self.hom_sets or f not in self.hom_sets[(f_source, f_target)]:
            return None
        if (f_target, g_target) not in self.hom_sets or g not in self.hom_sets[(f_target, g_target)]:
            return None
        return self.composition(f, g, f_source, f_target, g_target)

    def is_identity(self, morphism: Any) -> bool:
        return morphism in self.identities.values()


# ============================================================================
# RelationalFunctor
# ============================================================================

@dataclass
class RelationalFunctor:
    """
    A functor F: C → D between two categories.
    """
    name: str
    functor_type: FunctorType
    source_category: RelationalCategory
    target_category: RelationalCategory
    object_map: Dict[Any, Any]  # object in C -> object in D
    morphism_map: Dict[Any, Any] = field(default_factory=dict)  # (source, target, morphism) -> morphism in D

    def apply_to_object(self, obj: Any) -> Optional[Any]:
        return self.object_map.get(obj)

    def apply_to_morphism(self, source: Any, target: Any, morphism: Any) -> Optional[Any]:
        key = (source, target, morphism)
        return self.morphism_map.get(key)

    def __repr__(self) -> str:
        return f"RelationalFunctor({self.name})"


# ============================================================================
# NaturalTransformation
# ============================================================================

@dataclass
class NaturalTransformation:
    """
    A natural transformation η: F ⇒ G between two functors.
    For each object X in C, a morphism η_X: F(X) → G(X) in D.
    """
    name: str
    source_functor: RelationalFunctor
    target_functor: RelationalFunctor
    components: Dict[Any, Any]  # object in C -> morphism in D
    transformation_type: NaturalTransformationType = NaturalTransformationType.ISOMORPHISM

    def is_natural(self) -> bool:
        """Placeholder: full check is performed by categorical_verification."""
        return True


# ============================================================================
# MonoidalStructure
# ============================================================================

@dataclass
class MonoidalStructure:
    """
    Monoidal structure on a category: tensor product and unit object.
    """
    category: RelationalCategory
    tensor_product: Optional[Callable] = None  # (A, B) -> A⊗B
    unit_object: Any = None
    associator: Optional[NaturalTransformation] = None
    left_unitor: Optional[NaturalTransformation] = None
    right_unitor: Optional[NaturalTransformation] = None


# ============================================================================
# TwoCategory
# ============================================================================

@dataclass
class TwoCategory:
    """
    A 2‑category: objects, 1‑morphisms, and 2‑morphisms.
    """
    objects: Set[Any] = field(default_factory=set)
    one_morphisms: Dict[Tuple[Any, Any], Set[Any]] = field(default_factory=dict)  # (A,B) -> set of 1‑morphisms
    two_morphisms: Dict[Tuple[Any, Any, Any, Any], Set[Any]] = field(default_factory=dict)  # (f,g, A,B) -> set of 2‑morphisms
    vertical_composition: Optional[Callable] = None
    horizontal_composition: Optional[Callable] = None


# ============================================================================
# Adjunction
# ============================================================================

@dataclass
class Adjunction:
    """
    Adjunction F ⊣ G between two functors.
    """
    left_functor: RelationalFunctor   # F: C → D
    right_functor: RelationalFunctor  # G: D → C
    unit: NaturalTransformation        # η: Id_C ⇒ G∘F
    counit: NaturalTransformation      # ε: F∘G ⇒ Id_D

    def check_triangle_identities(self) -> bool:
        """Verify the two triangle identities."""
        C = self.left_functor.source_category
        D = self.left_functor.target_category

        for A in C.objects:
            FA = self.left_functor.apply_to_object(A)
            if FA is None:
                continue
            # (εF) ∘ (Fη) = id_F(A)
            eta_A = self.unit.components.get(A)
            if eta_A is None:
                return False
            F_eta_A = self.left_functor.apply_to_morphism(A, self.right_functor.apply_to_object(FA), eta_A)
            if F_eta_A is None:
                return False
            epsilon_FA = self.counit.components.get(FA)
            if epsilon_FA is None:
                return False
            comp = D.compose(
                F_eta_A, epsilon_FA,
                self.left_functor.apply_to_object(A),
                self.left_functor.apply_to_object(self.right_functor.apply_to_object(FA)),
                self.left_functor.apply_to_object(A),
            )
            if comp is None:
                return False
            id_FA = D.identities.get(FA)
            if not _morphisms_equal(D, comp, id_FA):
                return False

        for B in D.objects:
            GB = self.right_functor.apply_to_object(B)
            if GB is None:
                continue
            # (Gε) ∘ (ηG) = id_G(B)
            epsilon_B = self.counit.components.get(B)
            if epsilon_B is None:
                return False
            G_epsilon_B = self.right_functor.apply_to_morphism(GB, B, epsilon_B)
            if G_epsilon_B is None:
                return False
            eta_GB = self.unit.components.get(GB)
            if eta_GB is None:
                return False
            comp = C.compose(
                eta_GB, G_epsilon_B,
                self.right_functor.apply_to_object(B),
                self.right_functor.apply_to_object(self.left_functor.apply_to_object(GB)),
                self.right_functor.apply_to_object(B),
            )
            if comp is None:
                return False
            id_GB = C.identities.get(GB)
            if not _morphisms_equal(C, comp, id_GB):
                return False

        return True


# ============================================================================
# Monad
# ============================================================================

@dataclass
class Monad:
    """
    Monad (T, η, μ) on a category.
    """
    endofunctor: RelationalFunctor    # T: C → C
    unit: NaturalTransformation        # η: Id ⇒ T
    multiplication: NaturalTransformation # μ: T∘T ⇒ T

    def check_unit_laws(self) -> bool:
        """Verify μ ∘ Tη = id_T and μ ∘ ηT = id_T."""
        C = self.endofunctor.source_category
        for A in C.objects:
            TA = self.endofunctor.apply_to_object(A)
            if TA is None:
                continue
            TTA = self.endofunctor.apply_to_object(TA)

            # Tη_A: TA → TTA
            eta_A = self.unit.components.get(A)
            if eta_A is None:
                return False
            T_eta_A = self.endofunctor.apply_to_morphism(TA, TTA, eta_A)
            if T_eta_A is None:
                return False

            # μ_A: TTA → TA
            mu_A = self.multiplication.components.get(TA)
            if mu_A is None:
                return False

            # μ_A ∘ Tη_A
            left = C.compose(T_eta_A, mu_A, TA, TTA, TA)
            if left is None:
                return False
            id_TA = C.identities.get(TA)
            if not _morphisms_equal(C, left, id_TA):
                return False

            # η_{TA}: TA → TTA
            eta_TA = self.unit.components.get(TA)
            if eta_TA is None:
                return False

            # μ_A ∘ η_{TA}
            right = C.compose(eta_TA, mu_A, TA, TTA, TA)
            if right is None:
                return False
            if not _morphisms_equal(C, right, id_TA):
                return False

        return True

    def check_associativity(self) -> bool:
        """Verify μ ∘ Tμ = μ ∘ μT."""
        C = self.endofunctor.source_category
        for A in C.objects:
            TA = self.endofunctor.apply_to_object(A)
            if TA is None:
                continue
            TTA = self.endofunctor.apply_to_object(TA)
            TTTA = self.endofunctor.apply_to_object(TTA)

            # μ_A: TTA → TA
            mu_A = self.multiplication.components.get(TA)
            if mu_A is None:
                return False
            # μ_{TA}: TTTA → TTA
            mu_TA = self.multiplication.components.get(TTA)
            if mu_TA is None:
                return False

            # T(μ_A): TTTA → TTA
            T_mu_A = self.endofunctor.apply_to_morphism(TTA, TA, mu_A)
            if T_mu_A is None:
                return False

            # μ_A ∘ T(μ_A): TTTA → TTA → TA
            left = C.compose(T_mu_A, mu_A, TTTA, TTA, TA)
            if left is None:
                return False

            # μ_TA ∘ μ_A: TTTA → TTA → TA
            right = C.compose(mu_TA, mu_A, TTTA, TTA, TA)
            if right is None:
                return False

            if not _morphisms_equal(C, left, right):
                return False

        return True


# ============================================================================
# Comonad
# ============================================================================

@dataclass
class Comonad:
    """
    Comonad (L, ε, δ) on a category.
    """
    endofunctor: RelationalFunctor
    counit: NaturalTransformation        # ε: L ⇒ Id
    comultiplication: NaturalTransformation # δ: L ⇒ L∘L


# ============================================================================
# Limit / Colimit
# ============================================================================

@dataclass
class Limit:
    diagram: Dict[Any, Any]
    cone: Dict[Any, Any]
    universal_property: bool = False

    def is_limit(self, category: RelationalCategory) -> bool:
        logger.warning("Limit.is_limit not fully implemented – always returns True.")
        return True


@dataclass
class Colimit:
    diagram: Dict[Any, Any]
    cocone: Dict[Any, Any]
    universal_property: bool = False

    def is_colimit(self, category: RelationalCategory) -> bool:
        logger.warning("Colimit.is_colimit not fully implemented – always returns True.")
        return True


# ============================================================================
# KanExtension
# ============================================================================

@dataclass
class KanExtension:
    functor: RelationalFunctor
    extension: RelationalFunctor
    is_left: bool = True


# ============================================================================
# YonedaEmbedding
# ============================================================================

@dataclass
class YonedaEmbedding:
    category: RelationalCategory

    def embed(self, obj: str) -> Callable:
        def hom_functor(other: str) -> Set[Any]:
            return self.category.hom_sets.get((other, obj), set())
        return hom_functor


# ============================================================================
# EnrichedCategory
# ============================================================================

@dataclass
class EnrichedCategory:
    underlying_category: RelationalCategory
    enriching_category: MonoidalStructure
    hom_objects: Dict[Tuple[str, str], Any]
    composition_maps: Dict[Tuple[str, str, str], Any]
    identity_maps: Dict[str, Any]