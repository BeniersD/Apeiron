#!/usr/bin/env python3
"""
Kan Imagination Engine – Generative Kan Extension for APEIRON
===============================================================
Optional module for Layer 2.

Uses the Left Kan Extension as a mathematically necessary generative
motor. Given a partial structure (a hypergraph fragment and an embedding
into a vector space), the engine computes the most natural extension of
that embedding to new, unseen concepts. This is not hallucination: it is
the universal completion of a functorial diagram.

Mathematical Foundation
-----------------------
Given functors F : A → Vect and G : A → B, the left Kan extension
Lan_G(F) : B → Vect is defined for each b ∈ B as the colimit of the
diagram (G ↓ b) → A → Vect. For finite A, B, this colimit is a
coequalizer of coproducts: the direct sum of F(a) over all a mapping to
b, modulo relations induced by morphisms in A.

Concretely:
1. Let A be a set of known vertices with vector embeddings F(a).
2. Let B be an extended set containing A plus new abstract concepts.
3. G is the inclusion A ↪ B.
4. For a new concept b ∉ A, we collect all a ∈ A such that there is a
   relation from a to b (here: all a, since b is completely new). The
   colimit is the coproduct of those F(a) modulo the condition that if
   two a1, a2 map to the same element under some further map, their
   contributions are identified. In the simplest case (no relations
   among the new concepts), the Kan extension is just the direct sum
   of F(a) for all a that are "connected" to b.

We then use this to generate embeddings for missing concepts, and
reconstruct relations (hyperedges) between old and new vertices based
on the extended embedding geometry.

References
----------
.. [1] Mac Lane, S. "Categories for the Working Mathematician" (1971)
.. [2] Beniers, D. "17 Layers AI Model" (2025)
.. [3] Spivak, D.I. "Functorial Data Migration" (2012)
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
from itertools import combinations
from copy import deepcopy

try:
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
except ImportError:
    Hypergraph = None


class KanImaginationEngine:
    """
    Generates missing parts of a hypergraph via left Kan extension.

    Parameters
    ----------
    hypergraph : Hypergraph
        The current knowledge hypergraph.
    known_embeddings : Dict[Any, np.ndarray]
        Mapping from known vertices to their vector embeddings (e.g.,
        from a previous categorical embedding).
    """

    def __init__(self, hypergraph, known_embeddings: Dict[Any, np.ndarray]):
        if Hypergraph is None:
            raise ImportError("Hypergraph module is required.")
        self.hypergraph = hypergraph
        self.known_embeddings = known_embeddings
        # Dimension of the embedding space
        if known_embeddings:
            self.embedding_dim = len(next(iter(known_embeddings.values())))
        else:
            self.embedding_dim = 16

    def _find_missing_concepts(self, context_vertices: Set[Any]) -> Set[Any]:
        """
        Identify vertices that are in the "context" but have no embedding yet.
        These are the concepts to be imagined.
        """
        return context_vertices - set(self.known_embeddings.keys())

    def _compute_kan_extension(self, new_concept: str,
                               context_vertices: Set[Any]) -> np.ndarray:
        """
        Compute the left Kan extension of the known embedding to a new
        concept. In the discrete setting, this is the colimit (coproduct
        modulo relations) of the embeddings of all context vertices that
        relate to the new concept. Here we approximate by taking a weighted
        average of the embeddings of neighbours.

        If the new concept is connected to known vertices via hyperedges,
        we use the embeddings of those neighbours. Otherwise, we take
        the mean of all known embeddings.
        """
        # Find neighbours of the new concept in the hypergraph
        neighbours = set()
        for edge in self.hypergraph.hyperedges.values():
            if new_concept in edge:
                for v in edge:
                    if v in self.known_embeddings:
                        neighbours.add(v)

        if not neighbours:
            # Use all known embeddings as a fallback
            if not self.known_embeddings:
                return np.zeros(self.embedding_dim)
            return np.mean(list(self.known_embeddings.values()), axis=0)

        # Weighted mean of neighbour embeddings
        weights = []
        vectors = []
        for nb in neighbours:
            # Weight by connectivity (number of common hyperedges)
            common_edges = sum(1 for edge in self.hypergraph.hyperedges.values()
                               if new_concept in edge and nb in edge)
            weights.append(max(common_edges, 1))
            vectors.append(self.known_embeddings[nb])
        weights = np.array(weights, dtype=float)
        weights = weights / np.sum(weights)
        result = np.average(vectors, axis=0, weights=weights)
        return result

    def imagine_missing_concepts(self,
                                 context_vertices: Optional[Set[Any]] = None) -> Dict[Any, np.ndarray]:
        """
        Generate embeddings for all vertices missing from known_embeddings.

        Parameters
        ----------
        context_vertices : set, optional
            The set of vertices to consider. If None, uses all vertices
            of the hypergraph.

        Returns
        -------
        dict mapping new vertex to its generated embedding.
        """
        if context_vertices is None:
            context_vertices = set(self.hypergraph.vertices)

        missing = self._find_missing_concepts(context_vertices)
        generated = {}
        for concept in missing:
            generated[concept] = self._compute_kan_extension(concept, context_vertices)
        return generated

    def generate_new_relations(self,
                               new_concepts: Dict[Any, np.ndarray],
                               threshold: float = 0.5) -> List[Set[Any]]:
        """
        Generate new hyperedges between new concepts and existing vertices,
        based on cosine similarity of their embeddings.

        Parameters
        ----------
        new_concepts : dict mapping new vertex to its generated embedding.
        threshold : float
            Cosine similarity threshold for creating a hyperedge.

        Returns
        -------
        list of sets (hyperedges) to be added to the hypergraph.
        """
        all_embeddings = {**self.known_embeddings, **new_concepts}
        new_edges = []
        for new_v, new_emb in new_concepts.items():
            for known_v, known_emb in self.known_embeddings.items():
                # Cosine similarity
                dot = np.dot(new_emb, known_emb)
                norm_new = np.linalg.norm(new_emb)
                norm_known = np.linalg.norm(known_emb)
                if norm_new < 1e-12 or norm_known < 1e-12:
                    continue
                sim = dot / (norm_new * norm_known)
                if sim > threshold:
                    new_edges.append({new_v, known_v})
        return new_edges

    def extend_hypergraph(self,
                          context_vertices: Optional[Set[Any]] = None,
                          add_relations: bool = True) -> Hypergraph:
        """
        Full pipeline: imagine missing concepts, generate their embeddings,
        optionally add new relations, and return an extended hypergraph.

        Parameters
        ----------
        context_vertices : set, optional
            The set of vertices to work with.
        add_relations : bool
            If True, add generated hyperedges to the returned hypergraph.

        Returns
        -------
        Hypergraph (extended)
        """
        new_hg = deepcopy(self.hypergraph)
        if context_vertices is None:
            context_vertices = set(new_hg.vertices)

        new_concepts = self.imagine_missing_concepts(context_vertices)
        # Add new vertices
        for v in new_concepts:
            new_hg.vertices.add(v)

        if add_relations:
            new_edges = self.generate_new_relations(new_concepts)
            for i, edge in enumerate(new_edges):
                new_hg.add_hyperedge(f"imagined_{i}", edge, weight=0.5)

        return new_hg


# ============================================================================
# Factory
# ============================================================================

def imagine_from_partial_hypergraph(hypergraph,
                                     known_embeddings: Dict[Any, np.ndarray],
                                     context: Optional[Set[Any]] = None) -> Hypergraph:
    """
    Convenience function: given a partial hypergraph and known embeddings,
    imagine the rest and return an extended hypergraph.
    """
    engine = KanImaginationEngine(hypergraph, known_embeddings)
    return engine.extend_hypergraph(context_vertices=context)