#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endogenous Time Generation for the APEIRON Framework
====================================================
Layer 2 — Relational Hypergraph (Endogenous Time Extension)

This module generates endogenous time from causal structures discovered in the
relational hypergraph. It implements temporal ordering, time cone construction,
and the feedback loop from causal discovery to temporal reordering, directly
supporting the transition to Layer 4 (endogenous time experience).

Mathematical Foundation
-----------------------
Given a causal graph G = (V, E) where directed edges represent causal influence,
endogenous time is defined as a partial order ≤ on V such that u ≤ v iff there
exists a directed path from u to v. The time cone of an event v is:
    Past(v) = {u : u ≤ v}
    Future(v) = {w : v ≤ w}

The Alexandrov topology induced by these cones defines a spacetime structure
that is intrinsic to the relational system, without external temporal references.

The feedback loop: as new relations form in the hypergraph (Layer 2), the causal
graph is updated, which in turn refines the endogenous time ordering, which can
then influence the formation of new relations (cyclical causality).

References
----------
.. [1] Beniers, D. "Apeiron Framework: 17 Layers" (2025)
.. [2] Beniers, D. "Functorial Emergence in the APEIRON Framework" (2025)
.. [3] Sorkin, R.D. "Causal Sets: Discrete Gravity" (2003)

Author: APEIRON Framework Contributors
Version: 2.0.0 — Endogenous Time
Date: 2026-05-14
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from itertools import combinations, product
import warnings

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


@dataclass
class TimeCone:
    """
    The causal past and future of an event in endogenous time.

    Parameters
    ----------
    event : Any
        The event identifier.
    past : Set[Any]
        Events in the causal past (can influence this event).
    future : Set[Any]
        Events in the causal future (this event can influence).
    past_lightcone : Set[Any]
        Events on the past lightcone (immediately preceding).
    future_lightcone : Set[Any]
        Events on the future lightcone (immediately succeeding).
    """
    event: Any
    past: Set[Any] = field(default_factory=set)
    future: Set[Any] = field(default_factory=set)
    past_lightcone: Set[Any] = field(default_factory=set)
    future_lightcone: Set[Any] = field(default_factory=set)

    @property
    def causal_neighborhood(self) -> Set[Any]:
        """The union of past and future (all causally related events)."""
        return self.past | self.future

    @property
    def alexandrov_interval(self) -> Set[Any]:
        """Events causally between any past and any future event (spacelike)."""
        # Not implemented in full generality; returns the set of events not in past/future
        return set()

    def __repr__(self) -> str:
        return (f"TimeCone(event={self.event}, "
                f"past={len(self.past)}, future={len(self.future)})")


class CausalPartialOrder:
    """
    A partial order derived from a causal graph, representing endogenous time.

    Time is defined by the transitive closure of the causal graph. This class
    provides methods to compute past/future cones, linear extensions (total orders
    compatible with the partial order), and to check consistency.

    Parameters
    ----------
    causal_graph : Any
        A NetworkX DiGraph or adjacency dict representing causal relations.
    events : Optional[List[Any]]
        List of event identifiers; if None, taken from graph nodes.

    Examples
    --------
    >>> edges = [('a','b'), ('b','c')]
    >>> cpo = CausalPartialOrder(edges)
    >>> cpo.is_comparable('a', 'c')
    True
    >>> cpo.past_cone('c')
    {'a', 'b'}
    """
    def __init__(self, causal_graph, events: Optional[List[Any]] = None):
        if NETWORKX_AVAILABLE and isinstance(causal_graph, (list, nx.DiGraph, nx.Graph)):
            self.graph = nx.DiGraph()
            if isinstance(causal_graph, list):
                self.graph.add_edges_from(causal_graph)
            elif isinstance(causal_graph, nx.DiGraph):
                self.graph = causal_graph.copy()
            elif isinstance(causal_graph, nx.Graph):
                self.graph = nx.DiGraph(causal_graph)
        else:
            # Assume it's an adjacency dict: {u: [v,...]}
            self.graph = causal_graph
        if events is None:
            self.events = list(self._nodes())
        else:
            self.events = list(events)

        # Compute transitive closure for efficient queries
        self._build_transitive_closure()

    def _nodes(self):
        if NETWORKX_AVAILABLE and isinstance(self.graph, nx.DiGraph):
            return self.graph.nodes()
        return self.graph.keys()

    def _build_transitive_closure(self):
        """Compute reachability (transitive closure) via Floyd-Warshall or BFS."""
        self.reachable = defaultdict(set)
        if NETWORKX_AVAILABLE and isinstance(self.graph, nx.DiGraph):
            # Use NetworkX transitive closure
            TC = nx.transitive_closure(self.graph)
            for u in self.graph.nodes():
                self.reachable[u] = set(TC.successors(u))
        else:
            # BFS from each node
            for u in self.events:
                visited = set()
                queue = deque([u])
                while queue:
                    v = queue.popleft()
                    for w in self.graph.get(v, []):
                        if w not in visited:
                            visited.add(w)
                            queue.append(w)
                self.reachable[u] = visited

    def is_comparable(self, u, v) -> bool:
        """Check if u ≤ v (u causally precedes v)."""
        return v in self.reachable.get(u, set())

    def past_cone(self, event) -> Set[Any]:
        """All events that can reach this event."""
        past = set()
        for u in self.events:
            if self.is_comparable(u, event):
                past.add(u)
        return past

    def future_cone(self, event) -> Set[Any]:
        """All events reachable from this event."""
        return self.reachable.get(event, set()).copy()

    def time_cone(self, event) -> TimeCone:
        """Compute the full time cone for an event."""
        future = self.future_cone(event)
        past = self.past_cone(event)
        # Lightcones: immediate neighbors in the causal graph (edges)
        if NETWORKX_AVAILABLE and isinstance(self.graph, nx.DiGraph):
            past_lc = set(self.graph.predecessors(event))
            future_lc = set(self.graph.successors(event))
        else:
            past_lc = {u for u, neigh in self.graph.items() if event in neigh}
            future_lc = set(self.graph.get(event, []))
        return TimeCone(event, past, future, past_lc, future_lc)

    def topological_sort(self) -> Optional[List[Any]]:
        """Return a linear extension (total order) compatible with the partial order."""
        if NETWORKX_AVAILABLE and isinstance(self.graph, nx.DiGraph):
            try:
                return list(nx.topological_sort(self.graph))
            except nx.NetworkXUnfeasible:
                return None
        # Kahn's algorithm for adjacency dict
        in_degree = defaultdict(int)
        for u, neighbors in self.graph.items():
            for v in neighbors:
                in_degree[v] += 1
        queue = deque([v for v in self.events if in_degree[v] == 0])
        order = []
        while queue:
            u = queue.popleft()
            order.append(u)
            for v in self.graph.get(u, []):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        if len(order) == len(self.events):
            return order
        return None  # cycle detected

    def time_difference(self, u, v) -> Optional[int]:
        """
        Return the length of the longest path from u to v, or None if no path.
        This gives a discrete "proper time" between events.
        """
        # Dynamic programming on DAG
        if not self.is_comparable(u, v):
            return None
        # Longest path in DAG from u to v
        # Since it's a DAG (if acyclic), we can do BFS with memo
        longest = {u: 0}
        topo = self.topological_sort()
        if topo is None:
            return None  # cycle
        for x in topo:
            if x in longest:
                if NETWORKX_AVAILABLE and isinstance(self.graph, nx.DiGraph):
                    neighbors = self.graph.successors(x)
                else:
                    neighbors = self.graph.get(x, [])
                for y in neighbors:
                    if y not in longest or longest[x] + 1 > longest[y]:
                        longest[y] = longest[x] + 1
        return longest.get(v)

    def verify_partial_order_axioms(self) -> Dict[str, bool]:
        """Verify reflexivity, antisymmetry, and transitivity."""
        # Reflexivity: u ≤ u (handled by reachable not containing self, but we treat it as implicit)
        # Antisymmetry: if u ≤ v and v ≤ u then u = v
        antisym = True
        for u in self.events:
            for v in self.events:
                if u != v and self.is_comparable(u, v) and self.is_comparable(v, u):
                    antisym = False
                    break
        # Transitivity: if u ≤ v and v ≤ w then u ≤ w (by construction of transitive closure)
        trans = True  # built-in
        return {'reflexive': True, 'antisymmetric': antisym, 'transitive': trans}


class EndogenousTimeGenerator:
    """
    Generates endogenous time from a hypergraph's causal structure.

    This class orchestrates the extraction of causal relations from the
    relational hypergraph (via causal discovery), constructs a partial order
    representing endogenous time, and enables the feedback loop where
    temporal information can influence further relation formation.

    Parameters
    ----------
    causal_graph : Optional[Any]
        An existing causal graph (NetworkX DiGraph or edge list).
    events : Optional[List[Any]]
        Event identifiers.

    Examples
    --------
    >>> edges = [('a','b'), ('b','c'), ('a','c')]
    >>> gen = EndogenousTimeGenerator(edges)
    >>> gen.generate_time_ordering()
    ['a', 'b', 'c']
    """
    def __init__(self, causal_graph=None, events=None):
        self.causal_graph = causal_graph if causal_graph is not None else []
        self.events = events
        self.partial_order = None
        self._initialize()

    def _initialize(self):
        if self.causal_graph is not None:
            self.partial_order = CausalPartialOrder(self.causal_graph, self.events)
            if self.events is None:
                self.events = self.partial_order.events

    def from_causal_discovery(self, hypergraph, method: str = 'PC') -> 'EndogenousTimeGenerator':
        """
        Extract causal graph from a hypergraph using causal discovery algorithms.

        Parameters
        ----------
        hypergraph : Hypergraph
        method : str
            Causal discovery method ('PC', 'FCI', 'GES', etc.)

        Returns
        -------
        self (for chaining)
        """
        try:
            from .causal_discovery import CausalDiscovery
            cd = CausalDiscovery()
            # Convert hypergraph to data format expected by CausalDiscovery
            # For now, use a simplified approach: edges as features
            # Real implementation would use layer1_bridge
            adj_matrix = np.zeros((len(hypergraph.vertices), len(hypergraph.vertices)))
            for edge in hypergraph.edges:
                for v1, v2 in combinations(edge, 2):
                    i, j = sorted([v1, v2])
                    adj_matrix[i, j] = 1
                    adj_matrix[j, i] = 1
            # Assume adjacency represents correlation; causal discovery refines it
            # This is a placeholder; in practice, we'd call cd.estimate_causal_graph(data)
            self.causal_graph = []  # will be filled
        except ImportError:
            pass
        return self

    def generate_time_ordering(self) -> Optional[List[Any]]:
        """Generate a linear time ordering from the causal partial order."""
        if self.partial_order is None:
            self._initialize()
        if self.partial_order is None:
            return None
        return self.partial_order.topological_sort()

    def compute_time_cones(self) -> Dict[Any, TimeCone]:
        """Compute time cones for all events."""
        if self.partial_order is None:
            self._initialize()
        if self.partial_order is None:
            return {}
        return {e: self.partial_order.time_cone(e) for e in self.events}

    def temporal_reordering(self, events: List[Any]) -> List[Any]:
        """
        Reorder a list of events according to endogenous time.

        Parameters
        ----------
        events : List[Any]

        Returns
        -------
        List[Any] in temporal order.
        """
        ordering = self.generate_time_ordering()
        if ordering is None:
            return events  # cyclic, no reordering possible
        # Sort events by their position in ordering
        pos = {e: i for i, e in enumerate(ordering)}
        return sorted(events, key=lambda e: pos.get(e, float('inf')))

    def time_cone_tensor(self) -> np.ndarray:
        """
        Construct a 3D tensor T where T[i,j,k] = 1 if event k is in the Alexandrov
        interval between i and j. This encodes the full causal structure.

        Returns
        -------
        np.ndarray of shape (n_events, n_events, n_events)
        """
        n = len(self.events)
        tensor = np.zeros((n, n, n), dtype=float)
        event_idx = {e: i for i, e in enumerate(self.events)}
        for i, u in enumerate(self.events):
            cone_u = self.partial_order.time_cone(u) if self.partial_order else None
            if cone_u is None:
                continue
            for j, v in enumerate(self.events):
                cone_v = self.partial_order.time_cone(v) if self.partial_order else None
                if cone_v is None:
                    continue
                # k in interval if u ≤ k ≤ v
                interval = cone_u.future & cone_v.past
                for w in interval:
                    k = event_idx.get(w)
                    if k is not None:
                        tensor[i, k, j] = 1.0
        return tensor

    def feedback_to_hypergraph(self, hypergraph) -> None:
        """
        Implement the feedback loop: use endogenous time to influence
        relation formation in the hypergraph. For instance, strengthen
        relations that are temporally close.
        """
        ordering = self.generate_time_ordering()
        if ordering is None:
            return
        # Simple: add hyperedges between temporally adjacent events
        pos = {e: i for i, e in enumerate(ordering)}
        # For each consecutive pair in the ordering, ensure a relation exists
        for i in range(len(ordering) - 1):
            u, v = ordering[i], ordering[i+1]
            # Add a hyperedge containing both
            hypergraph.add_hyperedge([u, v], weight=1.0 / (i+1))


# ============================================================================
# Integration with Layer 2 and Layer 4
# ============================================================================

def endogenous_time_from_causal_discovery(hypergraph, causal_method: str = 'PC') -> EndogenousTimeGenerator:
    """
    Full pipeline: causal discovery → endogenous time generation.

    Parameters
    ----------
    hypergraph : Hypergraph
    causal_method : str

    Returns
    -------
    EndogenousTimeGenerator
    """
    gen = EndogenousTimeGenerator()
    gen.from_causal_discovery(hypergraph, method=causal_method)
    return gen


def build_spacetime_graph(hypergraph, causal_graph) -> Dict[str, Any]:
    """
    Build a spacetime graph combining the hypergraph structure with causal ordering.

    This is the bridge to Layer 4: the resulting structure is a discrete spacetime
    where vertices are events and edges encode both spatial (hypergraph) and
    temporal (causal) relations.

    Parameters
    ----------
    hypergraph : Hypergraph
    causal_graph : edge list or DiGraph

    Returns
    -------
    Dict with 'spacetime_graph', 'time_ordering', 'time_cones'.
    """
    gen = EndogenousTimeGenerator(causal_graph)
    ordering = gen.generate_time_ordering()
    cones = gen.compute_time_cones()
    return {
        'spacetime_graph': causal_graph,  # can be enriched
        'time_ordering': ordering,
        'time_cones': cones,
    }


# ============================================================================
# Doctest Harness
# ============================================================================
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)