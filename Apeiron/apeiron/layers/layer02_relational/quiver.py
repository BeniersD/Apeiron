"""
quiver.py – Quivers and their representations for Layer 2
==========================================================
Provides:
  - Quiver: a directed multigraph with vertices and arrows
  - QuiverRepresentation: assigns vector spaces to vertices and
    linear maps to arrows
  - QuiverRepresentationTheory: placeholder for advanced classification
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
# QuiverRepresentationTheory
# ============================================================================

@dataclass
class QuiverRepresentationTheory:
    """
    Advanced classification of quiver representations (placeholders).

    In a full implementation this would provide:
      - enumeration of indecomposables
      - Auslander–Reiten quiver
      - dimension vector utilities
      - Schurian test
    """
    quiver: Quiver

    def indecomposables(self) -> List[QuiverRepresentation]:
        """Return a list of indecomposable representations (not implemented)."""
        logger.warning("indecomposables() not implemented.")
        return []

    def auslander_reiten_quiver(self) -> Quiver:
        """Build the Auslander–Reiten quiver (not implemented)."""
        logger.warning("auslander_reiten_quiver() not implemented.")
        return Quiver()

    def dimension_vector(self, rep: QuiverRepresentation) -> Dict[str, int]:
        return rep.dimension_vector

    def is_schurian(self, rep: QuiverRepresentation) -> bool:
        """Test whether the representation is Schurian (placeholder)."""
        return True


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
    field: Any = None  # Placeholder for field object

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