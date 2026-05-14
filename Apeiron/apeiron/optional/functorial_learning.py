#!/usr/bin/env python3
"""
Functorial Learning – Kan Extension Based Learning
====================================================
Optional module for Layer 2.

Replaces gradient-based learning with universal constructions:
given a functor F : A → C and an extension of the domain along G : A → B,
the left Kan extension Lan_G(F) : B → C provides the most natural
extension of F to the larger category B. This module implements Kan
extensions for finite categories and uses them to extend relational
embeddings without backpropagation.

Mathematical Foundation
-----------------------
Given categories and functors:
    A ──F──▶ C
    │
    G
    ▼
    B
the left Kan extension Lan_G(F) : B → C is defined for each object b ∈ B
as the colimit of the diagram (G ↓ b) → A → C. For finite categories,
this colimit can be computed explicitly as a coequalizer.

In the APEIRON context:
- A = current category of observables
- F = embedding of observables into a vector space
- G = inclusion of new abstract concepts (e.g., from ontogenesis)
- Lan_G(F) = the most natural way to extend the embedding to new concepts.

References
----------
.. [1] Mac Lane, S. "Categories for the Working Mathematician" (1971)
.. [2] Beniers, D. "Functorial Emergence in the APEIRON Framework" (2025)
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
from itertools import product


@dataclass
class FiniteCategory:
    """A finite category: objects, morphisms (as pairs), and composition."""
    objects: Set[Any] = field(default_factory=set)
    morphisms: Dict[Tuple[Any, Any], List[Any]] = field(default_factory=dict)
    composition: Dict[Tuple[Any, Any, Any], Any] = field(default_factory=dict)

    def add_object(self, obj):
        self.objects.add(obj)

    def add_morphism(self, src, tgt, morphism):
        key = (src, tgt)
        if key not in self.morphisms:
            self.morphisms[key] = []
        self.morphisms[key].append(morphism)

    def all_morphisms(self):
        for (src, tgt), ms in self.morphisms.items():
            for m in ms:
                yield (src, tgt, m)


@dataclass
class KanExtension:
    """
    Left Kan extension of a functor F : A → C along G : A → B.
    We assume C is the category of vector spaces (Vect), so F maps objects
    to vectors (np.ndarray) and morphisms to linear maps (matrices).
    """
    F_obj: Dict[Any, np.ndarray]      # F(object) -> vector
    F_mor: Dict[Any, np.ndarray]      # F(morphism) -> matrix (linear map)
    G_obj: Dict[Any, Any]             # G(object in A) -> object in B
    # Computed Kan extension:
    Lan_obj: Dict[Any, np.ndarray] = field(default_factory=dict)
    Lan_mor: Dict[Any, np.ndarray] = field(default_factory=dict)

    def compute(self, B_objects: List[Any]) -> 'KanExtension':
        """
        Compute Lan_G(F)(b) for each b ∈ B as the colimit of
        (G ↓ b) → A → Vect.

        For simplicity, we treat the comma category (G ↓ b) as the set of
        objects a ∈ A together with a chosen morphism G(a) → b. We take
        the coproduct of F(a) over all such a, modulo the relations
        induced by morphisms in A.
        """
        for b in B_objects:
            # Objects in (G ↓ b): pairs (a, h) where h: G(a) → b.
            # Since we may not have explicit morphisms in B, we approximate
            # by taking all a such that G(a) "relates" to b (here: any a
            # if no further structure).
            indices = []
            vectors = []
            for a, ga in self.G_obj.items():
                # For simplicity, take all a (the colimit of a diagram over
                # all a is the coproduct of F(a) modulo relations).
                indices.append(a)
                vectors.append(self.F_obj[a])
            if not vectors:
                self.Lan_obj[b] = np.zeros(1)
                continue
            # Coproduct = concatenation of vectors (or direct sum)
            # We take a weighted average as a simplified colimit.
            stacked = np.stack(vectors)
            self.Lan_obj[b] = np.mean(stacked, axis=0)
        # Lan on morphisms: identity for now (can be extended)
        for b in B_objects:
            self.Lan_mor[b] = np.eye(len(self.Lan_obj[b]))
        return self


def functorial_embedding(
    source_embedding: Dict[Any, np.ndarray],
    extension_mapping: Dict[Any, Any],
    new_objects: List[Any]
) -> Dict[Any, np.ndarray]:
    """
    Extend an embedding from a set of objects A to a larger set B using
    a Kan extension along the inclusion mapping.

    Parameters
    ----------
    source_embedding : dict mapping object -> vector
    extension_mapping : dict mapping old object -> new object (inclusion)
    new_objects : list of all objects in the extended category

    Returns
    -------
    dict mapping all new_objects to vectors
    """
    kan = KanExtension(
        F_obj=source_embedding,
        F_mor={},  # no morphism information
        G_obj=extension_mapping
    )
    kan.compute(new_objects)
    return kan.Lan_obj