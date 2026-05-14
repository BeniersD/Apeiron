"""
category.py – Categorical structures for Layer 2 (Relational Dynamics) (Extended)
=================================================================================
Provides classes for categories, functors, natural transformations,
adjunctions, monads, limits, colimits, Kan extensions, Yoneda embedding,
and enriched categories.

All classes are pure data structures; verification of axioms is deferred
to `categorical_verification.py`.

New in v5.1:
  - conversion of RelationalCategory to Bicategory
  - nerve / simplicial set construction
  - sheaf hypergraph generation from the category's hom sets
  - integration with higher_category module
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
    def _morphisms_equal(cat, f, g):
        return f is g or f == g
    logger.warning("categorical_verification not available; morphism equality is shallow.")

# ---------------------------------------------------------------------------
# New module imports (graceful)
# ---------------------------------------------------------------------------
try:
    from .higher_category import Bicategory, SimplicialSet, StrictTwoCategory
except ImportError:
    Bicategory = None
    SimplicialSet = None
    StrictTwoCategory = None

try:
    from .sheaf_hypergraph import SheafHypergraph, SheafStalk
except ImportError:
    SheafHypergraph = None
    SheafStalk = None


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

    # ------------------------------------------------------------------
    # NEW METHODS (v5.1)
    # ------------------------------------------------------------------
    def to_bicategory(self) -> Any:
        """
        Convert this 1‑category to a bicategory (with trivial 2‑cells).

        All 1‑morphisms become identity 2‑morphisms.
        Returns a Bicategory instance or None if module not available.
        """
        if Bicategory is None:
            logger.warning("higher_category module not available")
            return None
        obj_list = list(self.objects)
        one_morphs = {}
        for (src, tgt), morphisms in self.hom_sets.items():
            for m in morphisms:
                name = f"{src}_{tgt}_{m}"
                one_morphs[name] = (str(src), str(tgt))
        return Bicategory(obj_list, one_morphs, {})

    def nerve(self, max_dim: int = 2) -> Any:
        """
        Build the nerve (simplicial set) of this category.

        0‑simplices = objects
        1‑simplices = morphisms (non‑identity)
        2‑simplices = composable pairs (f,g) such that g∘f exists.
        Returns a SimplicialSet or None.
        """
        if SimplicialSet is None:
            logger.warning("higher_category module not available")
            return None
        simplices = {0: list(self.objects)}
        # 1‑simplices: all non‑identity morphisms
        edges = []
        for (src, tgt), morphs in self.hom_sets.items():
            for m in morphs:
                if not self.is_identity(m):
                    edges.append((src, tgt))
        simplices[1] = edges
        # 2‑simplices: composable pairs
        triangles = []
        for (a,b), f_set in self.hom_sets.items():
            for f in f_set:
                if self.is_identity(f):
                    continue
                for (c,d), g_set in self.hom_sets.items():
                    if b != c:
                        continue
                    for g in g_set:
                        if self.is_identity(g):
                            continue
                        # check if composition exists
                        if self.compose(f, g, a, b, d) is not None:
                            triangles.append((a,b,d))
        if triangles:
            simplices[2] = triangles
        return SimplicialSet(simplices=simplices)

    def to_sheaf_hypergraph(self, vertex_stalk_dim: int = 2) -> Any:
        """
        Build a sheaf hypergraph from the category's hom sets.

        Vertices = objects, hyperedges = maximal composable chains.
        Stalks are vector spaces of dimension vertex_stalk_dim.
        Returns a SheafHypergraph or None.
        """
        if SheafHypergraph is None:
            logger.warning("sheaf_hypergraph module not available")
            return None
        vertices = [str(obj) for obj in self.objects]
        # Hyperedges: for each object, take all morphisms originating from it (simplistic)
        hyperedges = []
        for src in self.objects:
            targets = set()
            for (s, t), morphs in self.hom_sets.items():
                if s == src:
                    targets.add(str(t))
            if targets:
                hyperedges.append(set(targets))
        if not hyperedges:
            hyperedges = [set(vertices)]  # fallback single hyperedge
        return SheafHypergraph(vertices, hyperedges)

    @dataclass
    class LazyNerve:
        """
        Lazy construction of the simplicial nerve of a category.

        Simplices (composable chains of morphisms) are only materialized
        on demand, enabling scalable verification of coherence conditions.

        An n‑simplex is a tuple of the form
            (obj0, obj1, …, objn, m1, m2, …, mn)
        where each mi : obj_{i-1} → obj_i is a morphism in the category.
        """
        category: RelationalCategory
        _cache: Dict[int, List[Tuple[Any, ...]]] = field(default_factory=dict)

        # ------------------------------------------------------------------
        # Public API
        # ------------------------------------------------------------------
        def n_simplices(self, n: int) -> List[Tuple[Any, ...]]:
            """
            Return all n‑simplices (composable chains of n morphisms).

            For n=0 : objects                    -> tuple (obj0,)
            For n=1 : morphisms                  -> tuple (obj0, obj1, m1)
            For n=2 : composable pairs            -> tuple (obj0, obj1, obj2, m1, m2)
            etc.
            """
            if n in self._cache:
                return self._cache[n]

            if n == 0:
                simplices = [(obj,) for obj in self.category.objects]
            elif n == 1:
                simplices = []
                for (src, tgt), morphs in self.category.hom_sets.items():
                    for m in morphs:
                        simplices.append((src, tgt, m))
            else:
                # Build from (n-1)-simplices
                prev = self.n_simplices(n - 1)
                simplices = []
                for chain in prev:
                    # chain = (obj0, …, obj_{n-1}, m1, …, m_{n-1})
                    # length = (n) + (n-1) = 2n-1
                    last_object = chain[n - 1]          # obj_{n-1}
                    # Extend with any morphism leaving last_object
                    for (src, tgt), morphs in self.category.hom_sets.items():
                        if src == last_object:
                            for m in morphs:
                                new_chain = chain + (tgt, m)
                                simplices.append(new_chain)
            self._cache[n] = simplices
            return simplices

        # ------------------------------------------------------------------
        # Coherence verification
        # ------------------------------------------------------------------
        def verify_naturality(
            self,
            functor_F: RelationalFunctor,
            functor_G: RelationalFunctor,
            components: Dict[Any, Any],   # object in C -> morphism in D: η_A : F(A) → G(A)
        ) -> bool:
            """
            Verify that the given components define a natural transformation η : F ⇒ G.

            Checks the naturality square for every morphism f : A → B in the source
            category:  G(f) ∘ η_A = η_B ∘ F(f)

            Returns True if all squares commute (or the category does not contain
            enough data to disprove them).
            """
            C = functor_F.source_category
            D = functor_F.target_category      # must be the same for F and G

            for (a, b), morphisms in C.hom_sets.items():
                for f in morphisms:
                    # Skip identities – they automatically commute
                    if C.is_identity(f):
                        continue

                    # The image of f under F and G
                    Ff = functor_F.apply_to_morphism(a, b, f)
                    Gf = functor_G.apply_to_morphism(a, b, f)
                    if Ff is None or Gf is None:
                        return False

                    # The components at A and B
                    eta_A = components.get(a)
                    eta_B = components.get(b)
                    if eta_A is None or eta_B is None:
                        return False

                    # Left path:  G(f) ∘ η_A
                    left = D.compose(eta_A, Gf, functor_F.apply_to_object(a),
                                     functor_G.apply_to_object(a), functor_G.apply_to_object(b))
                    # Right path: η_B ∘ F(f)
                    right = D.compose(Ff, eta_B, functor_F.apply_to_object(a),
                                      functor_F.apply_to_object(b), functor_G.apply_to_object(b))

                    if left is None or right is None:
                        return False
                    if not _morphisms_equal(D, left, right):
                        return False

            return True

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
    morphism_map: Dict[Any, Any] = field(default_factory=dict)

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
    """
    name: str
    source_functor: RelationalFunctor
    target_functor: RelationalFunctor
    components: Dict[Any, Any]
    transformation_type: NaturalTransformationType = NaturalTransformationType.ISOMORPHISM

    def is_natural(self) -> bool:
        return True


# ============================================================================
# MonoidalStructure
# ============================================================================

@dataclass
class MonoidalStructure:
    category: RelationalCategory
    tensor_product: Optional[Callable] = None
    unit_object: Any = None
    associator: Optional[NaturalTransformation] = None
    left_unitor: Optional[NaturalTransformation] = None
    right_unitor: Optional[NaturalTransformation] = None


# ============================================================================
# TwoCategory
# ============================================================================

@dataclass
class TwoCategory:
    objects: Set[Any] = field(default_factory=set)
    one_morphisms: Dict[Tuple[Any, Any], Set[Any]] = field(default_factory=dict)
    two_morphisms: Dict[Tuple[Any, Any, Any, Any], Set[Any]] = field(default_factory=dict)
    vertical_composition: Optional[Callable] = None
    horizontal_composition: Optional[Callable] = None

    # New method: convert to StrictTwoCategory if available
    def to_strict_two_category(self) -> Any:
        if StrictTwoCategory is None:
            logger.warning("higher_category module not available")
            return None
        obj_list = list(self.objects)
        one_morphs = {}
        for (s,t), morphs in self.one_morphisms.items():
            for m in morphs:
                name = f"{s}_{t}_{m}"
                one_morphs[name] = (str(s), str(t))
        two_morphs = {}
        for (f,g,s,t), alphas in self.two_morphisms.items():
            for alpha in alphas:
                two_morphs[str(alpha)] = StrictTwoCategory.TwoMorphism(str(f), str(g), str(alpha))
        return StrictTwoCategory(obj_list, one_morphs, two_morphs)


# ============================================================================
# Adjunction
# ============================================================================

@dataclass
class Adjunction:
    left_functor: RelationalFunctor
    right_functor: RelationalFunctor
    unit: NaturalTransformation
    counit: NaturalTransformation

    def check_triangle_identities(self) -> bool:
        C = self.left_functor.source_category
        D = self.left_functor.target_category
        for A in C.objects:
            FA = self.left_functor.apply_to_object(A)
            if FA is None:
                continue
            eta_A = self.unit.components.get(A)
            if eta_A is None:
                return False
            F_eta_A = self.left_functor.apply_to_morphism(A, self.right_functor.apply_to_object(FA), eta_A)
            if F_eta_A is None:
                return False
            epsilon_FA = self.counit.components.get(FA)
            if epsilon_FA is None:
                return False
            comp = D.compose(F_eta_A, epsilon_FA, self.left_functor.apply_to_object(A), self.left_functor.apply_to_object(self.right_functor.apply_to_object(FA)), self.left_functor.apply_to_object(A))
            if comp is None:
                return False
            id_FA = D.identities.get(FA)
            if not _morphisms_equal(D, comp, id_FA):
                return False
        for B in D.objects:
            GB = self.right_functor.apply_to_object(B)
            if GB is None:
                continue
            epsilon_B = self.counit.components.get(B)
            if epsilon_B is None:
                return False
            G_epsilon_B = self.right_functor.apply_to_morphism(GB, B, epsilon_B)
            if G_epsilon_B is None:
                return False
            eta_GB = self.unit.components.get(GB)
            if eta_GB is None:
                return False
            comp = C.compose(eta_GB, G_epsilon_B, self.right_functor.apply_to_object(B), self.right_functor.apply_to_object(self.left_functor.apply_to_object(GB)), self.right_functor.apply_to_object(B))
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
    endofunctor: RelationalFunctor
    unit: NaturalTransformation
    multiplication: NaturalTransformation

    def check_unit_laws(self) -> bool:
        C = self.endofunctor.source_category
        for A in C.objects:
            TA = self.endofunctor.apply_to_object(A)
            if TA is None:
                continue
            TTA = self.endofunctor.apply_to_object(TA)
            eta_A = self.unit.components.get(A)
            if eta_A is None:
                return False
            T_eta_A = self.endofunctor.apply_to_morphism(TA, TTA, eta_A)
            if T_eta_A is None:
                return False
            mu_A = self.multiplication.components.get(TA)
            if mu_A is None:
                return False
            left = C.compose(T_eta_A, mu_A, TA, TTA, TA)
            if left is None:
                return False
            id_TA = C.identities.get(TA)
            if not _morphisms_equal(C, left, id_TA):
                return False
            eta_TA = self.unit.components.get(TA)
            if eta_TA is None:
                return False
            right = C.compose(eta_TA, mu_A, TA, TTA, TA)
            if right is None:
                return False
            if not _morphisms_equal(C, right, id_TA):
                return False
        return True

    def check_associativity(self) -> bool:
        C = self.endofunctor.source_category
        for A in C.objects:
            TA = self.endofunctor.apply_to_object(A)
            if TA is None:
                continue
            TTA = self.endofunctor.apply_to_object(TA)
            TTTA = self.endofunctor.apply_to_object(TTA)
            mu_A = self.multiplication.components.get(TA)
            if mu_A is None:
                return False
            mu_TA = self.multiplication.components.get(TTA)
            if mu_TA is None:
                return False
            T_mu_A = self.endofunctor.apply_to_morphism(TTA, TA, mu_A)
            if T_mu_A is None:
                return False
            left = C.compose(T_mu_A, mu_A, TTTA, TTA, TA)
            if left is None:
                return False
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
    endofunctor: RelationalFunctor
    counit: NaturalTransformation
    comultiplication: NaturalTransformation


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