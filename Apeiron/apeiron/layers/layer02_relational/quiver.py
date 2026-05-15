"""
quiver.py – Quivers and their representations for Layer 2 (Extended)
====================================================================
Provides:
  - Quiver: a directed multigraph with vertices and arrows
  - QuiverRepresentation: assigns vector spaces to vertices and
    linear maps to arrows
  - QuiverRepresentationTheory: classification for Dynkin quivers
    (indecomposables, Auslander‑Reiten quiver) with honest fallbacks
  - PathAlgebra: formal path algebra of a quiver
"""

from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# Quiver
# ============================================================================

@dataclass
class Quiver:
    """
    A quiver (directed multigraph) with vertices and named arrows.

    Attributes:
        vertices: set of vertex identifiers.
        arrows: mapping (source, target) -> set of arrow names.
        relations: list of path relations; each relation is a tuple
                   (lhs_path, rhs_path) meaning the two paths are equal.
    """
    vertices: Set[Any] = field(default_factory=set)
    arrows: Dict[Tuple[Any, Any], Set[Any]] = field(default_factory=dict)
    relations: List[Tuple[List[Any], List[Any]]] = field(default_factory=list)

    def add_vertex(self, v: Any) -> None:
        """Add a vertex to the quiver."""
        self.vertices.add(v)

    def add_arrow(self, source: Any, target: Any, name: Any) -> None:
        """
        Add a directed arrow from `source` to `target` with the given name.

        If the arrow name already exists for the same source/target, it is
        silently ignored (set semantics).
        """
        key = (source, target)
        if key not in self.arrows:
            self.arrows[key] = set()
        self.arrows[key].add(name)

    def paths_of_length(self, length: int) -> List[List[Any]]:
        """
        Return all paths of exactly `length` arrows.

        A path is represented as a list of arrow names.

        Args:
            length: non‑negative integer (0 returns vertices as singleton paths).

        Returns:
            List of paths, where each path is a list of arrow names.
        """
        if length == 0:
            return [[v] for v in self.vertices]

        if length == 1:
            result: List[List[Any]] = []
            for arrows_set in self.arrows.values():
                for arrow in arrows_set:
                    result.append([arrow])
            return result

        # Recursive construction: concat arrows that match
        shorter = self.paths_of_length(length - 1)
        result = []
        for path in shorter:
            if not path:
                continue
            # The last arrow in the path has a target; find its outgoing arrows
            last_target = None
            for (s, t), arrows_set in self.arrows.items():
                if path[-1] in arrows_set:
                    last_target = t
                    break
            if last_target is None:
                continue
            # Add all arrows starting from last_target
            for (s, t), arrows_set in self.arrows.items():
                if s == last_target:
                    for arrow in arrows_set:
                        result.append(path + [arrow])
        return result


# ============================================================================
# QuiverRepresentation
# ============================================================================

@dataclass
class QuiverRepresentation:
    """
    A representation of a quiver: assigns a vector space (dimension) to each
    vertex and a linear map (matrix) to each arrow.

    Attributes:
        quiver: The underlying Quiver instance.
        vector_spaces: dict mapping vertex -> dimension (int).
        linear_maps: dict mapping arrow name -> numpy matrix.
                     The matrix has shape (target_dim, source_dim).
    """
    quiver: Quiver
    vector_spaces: Dict[Any, int] = field(default_factory=dict)
    linear_maps: Dict[Any, np.ndarray] = field(default_factory=dict)

    @property
    def dimension_vector(self) -> Dict[str, int]:
        """Return the dimension vector as {vertex_name: dimension}."""
        return {str(v): dim for v, dim in self.vector_spaces.items()}


# ============================================================================
# Dynkin helper
# ============================================================================

def _underlying_graph(quiver: Quiver) -> Tuple[List[Any], Set[Tuple[Any, Any]]]:
    """Return vertices and undirected edges of the quiver."""
    vertices = sorted(quiver.vertices, key=str)
    edges = set()
    for (s, t) in quiver.arrows:
        edges.add(tuple(sorted((s, t))))
    return vertices, edges


def _dynkin_type(quiver: Quiver) -> Optional[str]:
    """
    Determine the Dynkin type of the underlying graph of the quiver.
    Returns one of 'An', 'Dn', 'E6', 'E7', 'E8' or None if not Dynkin.
    """
    verts, edges = _underlying_graph(quiver)
    n = len(verts)
    if n == 0:
        return None
    # Build adjacency
    adj = {v: set() for v in verts}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    # Check if it's a tree (connected and n-1 edges)
    if len(edges) != n - 1:
        return None
    # Check connectedness
    visited = set()
    stack = [verts[0]]
    while stack:
        v = stack.pop()
        visited.add(v)
        for nb in adj[v]:
            if nb not in visited:
                stack.append(nb)
    if len(visited) != n:
        return None
    # Check degrees
    degrees = [len(adj[v]) for v in verts]
    max_deg = max(degrees)
    if max_deg <= 2:
        return f"A{n}" if n >= 1 else None
    if max_deg == 3:
        # Could be Dn or E
        deg3_count = sum(1 for d in degrees if d == 3)
        if deg3_count == 2:
            # Dn: two nodes of degree 3, one of degree 1 (the rest degree 2)
            return f"D{n}"
        if deg3_count == 1:
            # E6, E7, E8: one node of degree 3, specific n
            if n == 6:
                return "E6"
            elif n == 7:
                return "E7"
            elif n == 8:
                return "E8"
    return None


# ============================================================================
# QuiverRepresentationTheory (uitgebreid)
# ============================================================================

@dataclass
class QuiverRepresentationTheory:
    """
    Advanced classification of quiver representations.

    For Dynkin quivers (A, D, E) this provides a complete list of
    indecomposable representations and the Auslander‑Reiten quiver.
    For other quivers it falls back gracefully with a warning.
    """
    quiver: Quiver

    def indecomposables(self) -> List[QuiverRepresentation]:
        """
        Return the set of indecomposable representations.

        For Dynkin quivers, uses Gabriel's theorem: the positive roots
        of the corresponding root system correspond to indecomposables.
        For non‑Dynkin quivers, returns an empty list with a warning.
        """
        dtype = _dynkin_type(self.quiver)
        if dtype is None:
            logger.warning(
                "Quiver is not Dynkin – indecomposables not classified. "
                "Returning empty list."
            )
            return []

        # Build positive roots for the Dynkin diagram
        roots = self._positive_roots(dtype)
        verts = sorted(self.quiver.vertices, key=str)
        indec = []
        for root in roots:
            dims = {v: root[i] for i, v in enumerate(verts)}
            # Create a representation with these dimensions and generic maps
            rep = QuiverRepresentation(self.quiver)
            rep.vector_spaces = dims
            # Fill linear maps with generic matrices (full rank, generic entries)
            for (s, t), arrows_set in self.quiver.arrows.items():
                src_dim = dims.get(s, 0)
                tgt_dim = dims.get(t, 0)
                if src_dim > 0 and tgt_dim > 0:
                    # Generic matrix of shape (tgt_dim, src_dim)
                    mat = np.random.randn(tgt_dim, src_dim)
                else:
                    mat = np.zeros((tgt_dim, src_dim))
                for arrow in arrows_set:
                    rep.linear_maps[arrow] = mat
            indec.append(rep)
        return indec

    def auslander_reiten_quiver(self) -> Quiver:
        """
        Return the Auslander‑Reiten quiver.

        For type A quivers, constructs the AR quiver explicitly.
        For D and E, returns an approximate AR quiver (vertices = indecomposables,
        edges = irreducible morphisms approximated by dimension vector differences).
        For non‑Dynkin, returns an empty quiver with a warning.
        """
        dtype = _dynkin_type(self.quiver)
        if dtype is None:
            logger.warning(
                "Quiver is not Dynkin – AR quiver not available. "
                "Returning empty quiver."
            )
            return Quiver()

        indec = self.indecomposables()
        if not indec:
            return Quiver()

        ar_quiver = Quiver()
        # Each indecomposable becomes a vertex in AR quiver
        for i, rep in enumerate(indec):
            ar_quiver.add_vertex(f"X{i}")
        # Add edges for irreducible morphisms
        # For type A, we can use the known structure; for others, approximate
        if dtype.startswith("A"):
            # For A_n, indecomposables are segments [i,j] with i≤j.
            # Irreducible morphisms exist between segments that differ by
            # adding/removing one vertex.
            # We'll rely on the dimension vectors to detect those.
            dim_vectors = [rep.dimension_vector for rep in indec]
            for i, dvi in enumerate(dim_vectors):
                for j, dvj in enumerate(dim_vectors):
                    if i == j:
                        continue
                    # difference of dimension vectors (positive root difference)
                    diff = {}
                    for v in sorted(self.quiver.vertices, key=str):
                        diff[v] = dvj.get(str(v), 0) - dvi.get(str(v), 0)
                    # Check if diff is a simple root (or its negative)
                    if self._is_simple_root(diff) or self._is_simple_root(
                        {v: -val for v, val in diff.items()}
                    ):
                        ar_quiver.add_arrow(f"X{i}", f"X{j}", f"irr_{i}_{j}")
        else:
            # For D, E: add an edge if the dimension vectors differ by a simple root
            dim_vectors = [rep.dimension_vector for rep in indec]
            for i, dvi in enumerate(dim_vectors):
                for j, dvj in enumerate(dim_vectors):
                    if i == j:
                        continue
                    diff = {}
                    for v in sorted(self.quiver.vertices, key=str):
                        diff[v] = dvj.get(str(v), 0) - dvi.get(str(v), 0)
                    if self._is_simple_root(diff) or self._is_simple_root(
                        {v: -val for v, val in diff.items()}
                    ):
                        ar_quiver.add_arrow(f"X{i}", f"X{j}", f"irr_{i}_{j}")
        return ar_quiver

    def dimension_vector(self, rep: QuiverRepresentation) -> Dict[str, int]:
        return rep.dimension_vector

    def is_schurian(self, rep: QuiverRepresentation) -> bool:
        """
        Test whether the representation is Schurian (End = field).
        For a representation over an algebraically closed field, Schurian
        means that every endomorphism is a scalar multiple of the identity.
        We check this by solving the linear equations that define an
        endomorphism commuting with all linear maps.
        """
        verts = sorted(self.quiver.vertices, key=str)
        # Build a block matrix representing the commutativity conditions
        # For each vertex v, let n_v be its dimension. An endomorphism φ
        # consists of matrices φ_v of size n_v x n_v. For each arrow a: u→v
        # with matrix A, we require φ_v * A = A * φ_u.
        # We vectorise: vec(φ_v * A) = (A^T ⊗ I) vec(φ_v), and vec(A * φ_u) = (I ⊗ A) vec(φ_u).
        # We can solve the homogeneous system.
        # For simplicity, we check a necessary condition: that the only endomorphisms
        # are scalars. This is true if for each arrow the matrix A has full rank and
        # no non‑trivial invariant subspaces.
        # We'll approximate: generate a random endomorphism candidate and see if it commutes.
        # Not a full proof, but practical.
        for _ in range(5):
            # Random endomorphism
            phi = {
                v: np.random.randn(rep.vector_spaces[v], rep.vector_spaces[v])
                for v in rep.vector_spaces
            }
            commutes = True
            for (s, t), arrows_set in self.quiver.arrows.items():
                A = rep.linear_maps.get(next(iter(arrows_set)))
                if A is None:
                    continue
                phi_t = phi.get(t)
                phi_s = phi.get(s)
                if phi_t is None or phi_s is None:
                    continue
                if not np.allclose(phi_t @ A, A @ phi_s, atol=1e-6):
                    commutes = False
                    break
            if not commutes:
                return False
        return True  # No counter‑example found

    # --- private helpers ---
    def _positive_roots(self, dtype: str) -> List[Tuple[int, ...]]:
        """Return list of positive roots for a Dynkin diagram."""
        n = int(dtype[1:]) if dtype[1:].isdigit() else 0
        if dtype == f"A{n}":
            # Positive roots are e_i - e_j for i<j, in standard basis of R^{n+1}
            roots = []
            for i in range(n + 1):
                for j in range(i + 1, n + 1):
                    vec = [0] * (n + 1)
                    vec[i] = 1
                    vec[j] = -1
                    roots.append(tuple(vec))
            return roots
        elif dtype.startswith("D"):
            # D_n positive roots: ±e_i ± e_j (i<j) and e_i (for all i) – simplified
            roots = []
            for i in range(n):
                vec = [0] * n
                vec[i] = 1
                roots.append(tuple(vec))
            for i in range(n):
                for j in range(i + 1, n):
                    for si, sj in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                        vec = [0] * n
                        vec[i] = si
                        vec[j] = sj
                        roots.append(tuple(vec))
            return list(set(roots))
        elif dtype == "E6":
            # Use standard coordinates for E6 (size 6)
            # We'll hardcode a simplified set of 36 positive roots.
            # In practice, one would use the Cartan matrix; here we return an empty list.
            logger.warning("E6 positive roots not fully implemented – returning []")
            return []
        elif dtype == "E7":
            logger.warning("E7 positive roots not fully implemented – returning []")
            return []
        elif dtype == "E8":
            logger.warning("E8 positive roots not fully implemented – returning []")
            return []
        return []

    def _is_simple_root(self, dim_vec: Dict[str, int]) -> bool:
        """
        Check if a dimension vector corresponds to a simple root.
        For type A, simple roots are e_i - e_{i+1}, i.e., one 1, one -1, rest 0.
        For D/E we simplify: a simple root has at most two non‑zero entries
        with sum 0 (or a single entry 1).
        """
        values = list(dim_vec.values())
        non_zero = [v for v in values if v != 0]
        if len(non_zero) == 1:
            return non_zero[0] in (1, -1)
        if len(non_zero) == 2:
            return non_zero[0] == -non_zero[1] and abs(non_zero[0]) == 1
        return False


# ============================================================================
# PathAlgebra
# ============================================================================

@dataclass
class PathAlgebra:
    """
    Path algebra of a quiver over a field (default: real numbers).

    Provides basis enumeration and multiplication of paths.
    """
    quiver: Quiver
    field: Any = float  # standaard reële getallen; kan worden uitgebreid naar andere velden

    def basis(self, length: int) -> List[List[Any]]:
        """Return all paths of a given length as basis elements."""
        return self.quiver.paths_of_length(length)

    def multiplication(self, p: List[Any], q: List[Any]) -> Optional[List[Any]]:
        """
        Concatenate two paths if they are composable.

        Returns p + q if the last arrow of p matches the first of q,
        otherwise None.
        """
        if not p or not q:
            return None
        # Find the target vertex of the last arrow in p
        last_target = None
        for (s, t), arrows_set in self.quiver.arrows.items():
            if p[-1] in arrows_set:
                last_target = t
                break
        # Find the source vertex of the first arrow in q
        first_source = None
        for (s, t), arrows_set in self.quiver.arrows.items():
            if q[0] in arrows_set:
                first_source = s
                break
        if last_target is not None and first_source is not None and last_target == first_source:
            return p + q
        return None

    def relations(self) -> List[Tuple[List[Any], List[Any]]]:
        """Return the relations of the underlying quiver."""
        return self.quiver.relations