#!/usr/bin/env python3
"""
Topos-Theoretic Logic for the APEIRON Framework
================================================
Layer 2 — Relational Hypergraph (Elementary Topos Extension)

Implements a subobject classifier and Heyting-algebra-valued truth on the
hypergraph, replacing binary logic with intuitionistic logic in the sheaf
topos Sh(H). This allows the AI to reason in contexts where the Law of
Excluded Middle does not hold, e.g., when integrating incommensurable
ontologies (Layer 12).

Mathematical Foundation
-----------------------
Given a hypergraph H, we construct the category of sheaves Sh(H) on the
Alexandrov topology of H (open sets = upward-closed sets of vertices under
the incidence preorder). The subobject classifier Ω is the sheaf that
assigns to each open set U the set of all sieves on U (or, equivalently,
the set of all open subsets of U). In the Alexandrov topology, Ω(U) is
the set of all open subsets of U, and the truth morphism true: 1 → Ω
picks the maximal element.

Truth values are elements of the Heyting algebra Ω(1), the set of global
sections of Ω, which corresponds to the set of all open sets of the whole
hypergraph. Logical connectives (∧, ∨, ⇒, ¬) are computed via the
Heyting algebra operations on open sets: intersection, union, relative
pseudocomplement (interior of set-theoretic complement), and pseudocomplement.

This enables the AI to assign non-binary truth values to propositions:
a proposition is "true to the extent" that it is supported by an open
neighborhood in the relational structure.

References
----------
.. [1] Mac Lane, S., Moerdijk, I. "Sheaves in Geometry and Logic" (1992)
.. [2] Goldblatt, R. "Topoi: The Categorial Analysis of Logic" (1984)
.. [3] Beniers, D. "Categorical Foundations of the APEIRON Framework" (2025)
"""

import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from itertools import combinations
import warnings

try:
    from .sheaf_hypergraph import SheafHypergraph
except ImportError:
    SheafHypergraph = None


# ============================================================================
# Open Sets and Topology on Hypergraph
# ============================================================================

class HypergraphTopology:
    """
    Alexandrov topology on a hypergraph derived from the incidence preorder.

    Vertices are ordered by: v ≤ w if there is a hyperedge containing both
    (or more generally, if they are connected). Open sets are upward-closed
    sets under this preorder.

    This topology makes the hypergraph into a poset, and sheaves on this
    poset correspond to functors from the poset to Set.
    """

    def __init__(self, hypergraph):
        self.hypergraph = hypergraph
        self._build_preorder()

    def _build_preorder(self):
        """Build the incidence preorder: v ≤ w if they co-occur in a hyperedge."""
        vertices = sorted(self.hypergraph.vertices)
        n = len(vertices)
        self.vertex_list = vertices
        self.vertex_index = {v: i for i, v in enumerate(vertices)}
        # Adjacency matrix of the preorder (reflexive + symmetric for now, but can be asymmetric)
        self.order_matrix = np.eye(n, dtype=bool)
        for edge in self.hypergraph.hyperedges.values():
            edge_verts = list(edge)
            for v in edge_verts:
                for w in edge_verts:
                    i = self.vertex_index.get(v)
                    j = self.vertex_index.get(w)
                    if i is not None and j is not None:
                        self.order_matrix[i, j] = True
        # Compute transitive closure (Warshall)
        for k in range(n):
            for i in range(n):
                if self.order_matrix[i, k]:
                    self.order_matrix[i, :] |= self.order_matrix[k, :]

    def is_open(self, subset: Set[Any]) -> bool:
        """
        Check if a subset of vertices is upward-closed.

        A set U is open if whenever v ∈ U and v ≤ w, then w ∈ U.
        """
        indices_in = [self.vertex_index[v] for v in subset if v in self.vertex_index]
        if not indices_in:
            return True
        # Get the upward closure of the subset
        upward = np.any(self.order_matrix[indices_in, :], axis=0)
        # The subset is open if its upward closure is exactly the subset (i.e., it contains all successors)
        # Equivalently, no vertex outside the subset is reachable from inside.
        indices_out = [i for i in range(len(self.vertex_list)) if i not in indices_in]
        # For each v in subset, check that all its successors are in subset
        for i in indices_in:
            successors = np.where(self.order_matrix[i, :])[0]
            if not all(s in indices_in for s in successors):
                return False
        return True

    def upward_closure(self, vertices: Set[Any]) -> Set[Any]:
        """Return the smallest open set containing the given vertices."""
        indices = [self.vertex_index[v] for v in vertices if v in self.vertex_index]
        if not indices:
            return set()
        upward_indices = set(np.where(np.any(self.order_matrix[indices, :], axis=0))[0])
        return {self.vertex_list[i] for i in upward_indices}

    def all_open_sets(self) -> List[Set[Any]]:
        """
        Return all open sets. In a finite poset, every open set is uniquely
        determined by its minimal elements. We enumerate all subsets of vertices
        and compute their upward closure (with duplicates removed).
        """
        open_sets = []
        seen = set()
        n = len(self.vertex_list)
        # Enumerate all possible sets of minimal elements (there are 2^n, which is finite)
        # In practice, we can cache but this is the theoretical definition.
        for mask in range(1 << n):
            subset = {self.vertex_list[i] for i in range(n) if (mask >> i) & 1}
            closure = self.upward_closure(subset)
            key = frozenset(closure)
            if key not in seen:
                seen.add(key)
                open_sets.append(closure)
        return open_sets


# ============================================================================
# Subobject Classifier (Ω) for the Sheaf Topos Sh(H)
# ============================================================================

class SubobjectClassifier:
    """
    The subobject classifier Ω in the sheaf topos Sh(H) for a hypergraph H.

    For each open set U (an upward-closed set of vertices), Ω(U) is the
    set of all open subsets of U (i.e., the set of sieves on U). The
    restriction map Ω(U) → Ω(V) for V ⊆ U sends a sieve on U to its
    intersection with V (or equivalently, the restriction of the open subset).

    The global sections Ω(1) form a Heyting algebra: the set of all open
    sets of the whole space. This is the algebra of truth values.

    Parameters
    ----------
    topology : HypergraphTopology
        The Alexandrov topology on the hypergraph.
    """

    def __init__(self, topology: HypergraphTopology):
        self.topology = topology
        # Global truth values = all open sets of the whole hypergraph
        self.global_truth_values = topology.all_open_sets()
        self._open_set_to_index = {frozenset(u): i for i, u in enumerate(self.global_truth_values)}
        # True (the maximal open set) = the whole set of vertices
        self.true_value = set(topology.vertex_list)
        # False (the minimal open set) = empty set (which is open? In Alexandrov topology, empty set is open)
        self.false_value = set()

    def evaluate_at(self, open_subset: Set[Any], sieve: Set[Any]) -> bool:
        """Check whether a sieve (open subset of U) belongs to Ω(U)."""
        # A sieve on U is an open subset S such that S ⊆ open_subset.
        return sieve.issubset(open_subset) and self.topology.is_open(sieve)

    def heyting_implication(self, P: Set[Any], Q: Set[Any]) -> Set[Any]:
        """
        Compute the Heyting implication P ⇒ Q in the algebra of open sets.
        P ⇒ Q = interior( (X \ P) ∪ Q ), but since we are in an Alexandrov
        topology, the interior of a set S is the largest open set contained in S.
        Equivalently, P ⇒ Q = the set of points x such that for all y ≥ x,
        if y ∈ P then y ∈ Q.
        """
        result = set()
        for v in self.topology.vertex_list:
            # Condition: for all w ≥ v, if w ∈ P then w ∈ Q
            idx_v = self.topology.vertex_index[v]
            successors = np.where(self.topology.order_matrix[idx_v, :])[0]
            all_ok = True
            for s in successors:
                w = self.topology.vertex_list[s]
                if w in P and w not in Q:
                    all_ok = False
                    break
            if all_ok:
                result.add(v)
        # Ensure it is open: take its upward closure (already upward-closed by construction)
        return result

    def heyting_negation(self, P: Set[Any]) -> Set[Any]:
        """¬P = P ⇒ ∅"""
        return self.heyting_implication(P, self.false_value)

    def conjunction(self, P: Set[Any], Q: Set[Any]) -> Set[Any]:
        """P ∧ Q = P ∩ Q (intersection of open sets is open)"""
        return P.intersection(Q)

    def disjunction(self, P: Set[Any], Q: Set[Any]) -> Set[Any]:
        """P ∨ Q = P ∪ Q (union of open sets is open in Alexandrov topology)"""
        return P.union(Q)

    def truth_degree(self, proposition: Set[Any]) -> float:
        """
        Compute a numerical degree of truth as the fraction of vertices
        covered by the open set representing the proposition.
        """
        total = len(self.topology.vertex_list)
        if total == 0:
            return 0.0
        return len(proposition.intersection(self.topology.vertex_list)) / total

    def __repr__(self):
        return f"SubobjectClassifier(|Ω| = {len(self.global_truth_values)} truth values)"


# ============================================================================
# Topos Logic Engine
# ============================================================================

class ToposLogic:
    """
    A reasoning engine based on the topos-theoretic truth values.

    This class evaluates propositions over the hypergraph and returns
    non-binary truth values (open sets). It can combine propositions
    using intuitionistic logic and detect when the Law of Excluded Middle
    fails for a given proposition.

    Parameters
    ----------
    classifier : SubobjectClassifier
        The subobject classifier built from the hypergraph topology.
    """

    def __init__(self, classifier: SubobjectClassifier):
        self.classifier = classifier

    def proposition(self, predicate: Dict[Any, bool]) -> Set[Any]:
        """
        Create a proposition (open set) from a predicate on vertices.
        The resulting set is the upward-closure of vertices where the predicate
        holds, ensuring openness.
        """
        subset = {v for v, holds in predicate.items() if holds}
        return self.classifier.topology.upward_closure(subset)

    def implies(self, P: Set[Any], Q: Set[Any]) -> Set[Any]:
        """Intuitionistic implication P ⇒ Q."""
        return self.classifier.heyting_implication(P, Q)

    def negate(self, P: Set[Any]) -> Set[Any]:
        """Intuitionistic negation ¬P."""
        return self.classifier.heyting_negation(P)

    def and_(self, P: Set[Any], Q: Set[Any]) -> Set[Any]:
        return self.classifier.conjunction(P, Q)

    def or_(self, P: Set[Any], Q: Set[Any]) -> Set[Any]:
        return self.classifier.disjunction(P, Q)

    def is_valid(self, P: Set[Any]) -> bool:
        """Check if P is globally true (equal to the whole space)."""
        return P == self.classifier.true_value

    def law_of_excluded_middle_holds(self, P: Set[Any]) -> bool:
        """Check whether P ∨ ¬P = ⊤ (classical logic holds for this proposition)."""
        not_P = self.negate(P)
        return self.classifier.disjunction(P, not_P) == self.classifier.true_value

    def topos_evaluate(self, proposition: Dict[Any, bool]) -> Dict[str, Any]:
        """
        Evaluate a proposition in the topos and return its truth status.

        Returns a dictionary with the open set, its numerical truth degree,
        and whether the Law of Excluded Middle holds.
        """
        P = self.proposition(proposition)
        not_P = self.negate(P)
        return {
            'open_set': P,
            'truth_degree': self.classifier.truth_degree(P),
            'is_globally_true': self.is_valid(P),
            'lem_holds': self.law_of_excluded_middle_holds(P),
            'negation': not_P,
            'double_negation': self.negate(not_P),
        }


# ============================================================================
# Factory for integration with existing Hypergraph
# ============================================================================

def topos_from_hypergraph(hypergraph) -> ToposLogic:
    """
    Build a ToposLogic engine from a Hypergraph instance.

    This is the recommended entry point for APEIRON Layer 2.
    """
    topology = HypergraphTopology(hypergraph)
    classifier = SubobjectClassifier(topology)
    return ToposLogic(classifier)


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)