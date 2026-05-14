#!/usr/bin/env python3
"""
HoTT Relations – Univalent Relationality for the APEIRON Framework
====================================================================
Optional module for Layer 2.

Treats every UltimateRelation not as a static edge but as a *path* in a
higher homotopy space. Implements the Univalence Axiom from Homotopy Type
Theory (HoTT) on the relational hypergraph: isomorphic observables are
identified, and relations transport along isomorphisms.

Mathematical Foundation
-----------------------
In HoTT, the identity type Id_A(a, b) is a space of paths. The univalence
axiom states that the canonical map (A =_U B) → (A ≃ B) is an equivalence.
This means equality is equivalent to isomorphism.

Applied to Apeiron:
- Each vertex corresponds to a type.
- Each UltimateRelation is a path (morphism) in the path space.
- If two vertices have isomorphic neighbourhoods, they are considered
  "judgmentally equal" and relations involving one are automatically
  transported to the other via the structure identity principle.
- The homotopy group π₁ of the resulting ∞-groupoid measures the
  "redundancy" of the knowledge representation.

References
----------
.. [1] Univalent Foundations Program. "Homotopy Type Theory" (2013)
.. [2] Ahrens, K., Kapulkin, K., Shulman, M. "Univalent categories
       and the Rezk completion" (2015)
.. [3] Beniers, D. "17 Layers AI Model" (2025)
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any, FrozenSet
from dataclasses import dataclass, field
from itertools import combinations
from collections import defaultdict

try:
    from apeiron.layers.layer02_relational.hypergraph import Hypergraph
except ImportError:
    Hypergraph = None


@dataclass
class Path:
    """
    A path in the homotopy space of the hypergraph.
    Represents a sequence of relations connecting source to target.
    """
    vertices: List[Any]       # ordered list of vertices along the path
    edges: List[Any]          # ordered list of relation identifiers

    @property
    def source(self) -> Any:
        return self.vertices[0] if self.vertices else None

    @property
    def target(self) -> Any:
        return self.vertices[-1] if self.vertices else None

    def concatenate(self, other: 'Path') -> Optional['Path']:
        """Concatenate two paths if the target of the first matches
        the source of the second."""
        if self.target != other.source:
            return None
        return Path(
            vertices=self.vertices + other.vertices[1:],
            edges=self.edges + other.edges
        )

    def reverse(self) -> 'Path':
        """Reverse a path."""
        return Path(
            vertices=list(reversed(self.vertices)),
            edges=list(reversed(self.edges))
        )

    def __repr__(self):
        return f"Path({' → '.join(str(v) for v in self.vertices)})"


class HomotopyGroupoid:
    """
    The fundamental groupoid of the hypergraph: vertices are objects,
    paths are morphisms, and path homotopy (equivalence up to
    "redundant" relations) defines the 2-cells.

    Two paths are homotopic if one can be transformed into the other
    by a sequence of "elementary moves": adding or removing a pair of
    inverse edges (retracing), or rerouting through a hyperedge
    (higher-order connection).
    """

    def __init__(self, hypergraph):
        if Hypergraph is None:
            raise ImportError("Hypergraph module is required.")
        self.hypergraph = hypergraph
        # Build adjacency from hyperedges
        self._adj: Dict[Any, Set[Any]] = defaultdict(set)
        for edge in hypergraph.hyperedges.values():
            for u, v in combinations(edge, 2):
                self._adj[u].add(v)
                self._adj[v].add(u)

    def neighbours(self, v: Any) -> Set[Any]:
        return self._adj.get(v, set())

    def find_all_paths(self, source: Any, target: Any,
                       max_length: int = 6) -> List[Path]:
        """Find all simple paths up to max_length between source and target."""
        if source == target:
            return [Path([source], [])]
        all_paths = []
        stack = [(source, [source], [])]  # current, vertices, edges
        while stack:
            cur, verts, edges = stack.pop()
            if len(verts) > max_length:
                continue
            for nb in self._adj.get(cur, set()):
                if nb == target:
                    all_paths.append(Path(verts + [nb], edges + [(cur, nb)]))
                elif nb not in verts:
                    stack.append((nb, verts + [nb], edges + [(cur, nb)]))
        return all_paths

    def are_homotopic(self, path1: Path, path2: Path) -> bool:
        """
        Check if two paths are homotopic.
        For a hypergraph, two paths are homotopic if they share the same
        endpoints and the union of their vertices forms a simply-connected
        subgraph (i.e., the loop formed by path1 followed by reverse(path2)
        bounds a 2‑dimensional face — a hyperedge of size ≥ 3).
        """
        if path1.source != path2.source or path1.target != path2.target:
            return False
        if path1.vertices == path2.vertices:
            return True
        # Construct the loop: path1 + reverse(path2)
        loop_verts = set(path1.vertices) | set(path2.vertices)
        # Check if the loop is contractible: the subgraph induced by loop_verts
        # should have a spanning tree that, together with the loop, forms a
        # cycle that can be filled by a hyperedge of size ≥ 3.
        # Simplification: two paths are homotopic if there exists a hyperedge
        # containing all vertices of the loop (i.e., a higher-order connection).
        for edge in self.hypergraph.hyperedges.values():
            if loop_verts.issubset(edge):
                return True
        # Alternative: if the two paths differ only by a single vertex
        # that is connected to both via a hyperedge, they are homotopic.
        sym_diff = loop_verts - (set(path1.vertices) & set(path2.vertices))
        if len(sym_diff) <= 2:
            return True
        return False

    def homotopy_classes(self, source: Any, target: Any) -> List[List[Path]]:
        """
        Group all paths between source and target into homotopy classes.
        Returns a list of equivalence classes (each class is a list of paths).
        """
        paths = self.find_all_paths(source, target)
        classes = []
        assigned = [False] * len(paths)
        for i, p in enumerate(paths):
            if assigned[i]:
                continue
            cls = [p]
            assigned[i] = True
            for j in range(i + 1, len(paths)):
                if not assigned[j] and self.are_homotopic(p, paths[j]):
                    cls.append(paths[j])
                    assigned[j] = True
            classes.append(cls)
        return classes

    def fundamental_group(self, basepoint: Any) -> List[List[Path]]:
        """
        Compute the fundamental group π₁(H, basepoint) as the set of
        homotopy classes of loops at basepoint.
        """
        return self.homotopy_classes(basepoint, basepoint)

    def is_simply_connected(self) -> bool:
        """Check if the hypergraph is simply connected (π₁ = 0 for all
        basepoints)."""
        for v in self.hypergraph.vertices:
            classes = self.homotopy_classes(v, v)
            # Trivial class is the identity loop [v]
            if len(classes) > 1:
                return False
        return True


class UnivalenceTransport:
    """
    Implements transport of relations along isomorphisms (paths that are
    equivalences, i.e., have an inverse up to homotopy).

    If vertex A and B are isomorphic (connected by a homotopy equivalence),
    any relation involving A can be "transported" to an equivalent relation
    involving B by conjugation.
    """

    def __init__(self, groupoid: HomotopyGroupoid):
        self.groupoid = groupoid

    def are_isomorphic(self, a: Any, b: Any) -> bool:
        """
        Two vertices are isomorphic if there exists a path p from a to b
        and a path q from b to a such that p∘q is homotopic to id_a and
        q∘p is homotopic to id_b.
        """
        paths_ab = self.groupoid.find_all_paths(a, b, max_length=4)
        paths_ba = self.groupoid.find_all_paths(b, a, max_length=4)
        if not paths_ab or not paths_ba:
            return False
        # Check existence of inverse pairs up to homotopy
        for p in paths_ab:
            for q in paths_ba:
                if (p.source == a and p.target == b and
                    q.source == b and q.target == a):
                    # Check if p∘q ≈ id_a (loop at a)
                    loop_a = p.concatenate(q)
                    id_a = Path([a], [])
                    if loop_a and self.groupoid.are_homotopic(loop_a, id_a):
                        loop_b = q.concatenate(p)
                        id_b = Path([b], [])
                        if loop_b and self.groupoid.are_homotopic(loop_b, id_b):
                            return True
        return False

    def transport_relation(self, relation: Any, source_isomorphic: Any,
                           target_isomorphic: Any) -> Optional[Any]:
        """
        Transport a relation from one vertex to another isomorphic vertex.

        If r : X → Y and X ≅ X', Y ≅ Y', we obtain a relation r' : X' → Y'
        by composing with the isomorphisms: r' = iso_Y⁻¹ ∘ r ∘ iso_X.

        For simplicity, we return a new edge label.
        """
        return f"transported_{relation}_from_{source_isomorphic}_to_{target_isomorphic}"

    def univalence_axiom_holds(self) -> bool:
        """
        Check whether the univalence axiom is satisfied: for any two
        isomorphic vertices, there is a bijection between their sets
        of relations.
        """
        verts = list(self.groupoid.hypergraph.vertices)
        for i in range(len(verts)):
            for j in range(i + 1, len(verts)):
                if self.are_isomorphic(verts[i], verts[j]):
                    # Check that they have the same number of incident hyperedges
                    edges_i = set()
                    edges_j = set()
                    for eid, edge in self.groupoid.hypergraph.hyperedges.items():
                        if verts[i] in edge:
                            edges_i.add(eid)
                        if verts[j] in edge:
                            edges_j.add(eid)
                    if len(edges_i) != len(edges_j):
                        return False
        return True


# ============================================================================
# Factory
# ============================================================================

def homotopy_analysis(hypergraph) -> Dict[str, Any]:
    """
    Perform homotopy analysis on a hypergraph.

    Returns
    -------
    dict with:
        - 'is_simply_connected': bool
        - 'num_isomorphism_classes': int
        - 'univalence_holds': bool
    """
    groupoid = HomotopyGroupoid(hypergraph)
    transport = UnivalenceTransport(groupoid)

    # Count isomorphism classes
    verts = list(hypergraph.vertices)
    classes = []
    assigned = set()
    for v in verts:
        if v in assigned:
            continue
        cls = {v}
        for w in verts:
            if w not in assigned and transport.are_isomorphic(v, w):
                cls.add(w)
                assigned.add(w)
        classes.append(cls)

    return {
        'is_simply_connected': groupoid.is_simply_connected(),
        'num_isomorphism_classes': len(classes),
        'univalence_holds': transport.univalence_axiom_holds(),
        'homotopy_group_order': len(groupoid.homotopy_classes(verts[0], verts[0])) if verts else 0,
    }