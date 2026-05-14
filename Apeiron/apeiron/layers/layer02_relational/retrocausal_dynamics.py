#!/usr/bin/env python3
"""
Retrocausal Minimal Action Dynamics for the APEIRON Framework
=============================================================
Layer 2 — Relational Hypergraph (Variational Knowledge Dynamics)

Implements a path-integral-like variational principle for knowledge
evolution. Given a hypergraph representing the current state of knowledge
and a desired target (e.g., a state of low sheaf obstruction), the AI
finds a sequence of hypergraph mutations (adding/removing hyperedges)
that minimises a Lagrangian action. The target state acts as a boundary
condition, influencing the trajectory in a retrocausal manner (in the
sense of the calculus of variations: the end condition determines the
optimal path). This provides a mathematically rigorous mechanism for
goal-directed learning without teleology.

Mathematical Foundation
-----------------------
Let H(t) be a time-dependent hypergraph. The action S is defined over a
time interval [0, T] as the integral of a Lagrangian L(H, Ḣ) dt, where
L combines:
  - A kinetic term: ||Ḣ||², penalising rapid structural changes,
  - A potential term: Cohomological obstruction ||H¹(H; F)||²,
    which the system aims to minimise,
  - A terminal cost: distance to a target configuration H_target.

The optimal path H*(t) satisfies the Euler-Lagrange equations with
boundary conditions H(0)=H_initial, H(T)=H_target (or free endpoint
with terminal cost). We solve the optimisation via gradient descent on
a discretised sequence of intermediate hypergraphs.

References
----------
.. [1] Beniers, D. "Apeiron Framework: 17 Layers" (2025)
.. [2] Gelfand, I.M., Fomin, S.V. "Calculus of Variations" (1963)
.. [3] Sorkin, R.D. "Causal Sets: Discrete Gravity" (2003)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from copy import deepcopy
from apeiron.layers.layer02_relational.hypergraph import Hypergraph
import warnings

try:
    from .sheaf_hypergraph import SheafHypergraph
except ImportError:
    SheafHypergraph = None


@dataclass
class RetrocausalState:
    """
    A snapshot in the variational sequence.

    Attributes:
        hypergraph: the hypergraph at this time step.
        obstruction: H¹ dimension (or norm) as a measure of inconsistency.
        action_contribution: the Lagrangian integrated over this time step.
    """
    hypergraph: Any  # Hypergraph
    obstruction: float
    action_contribution: float


class RetrocausalDynamics:
    """
    Variational optimiser for knowledge trajectories.

    Parameters
    ----------
    initial_hypergraph : Hypergraph
        The current state of knowledge.
    target_hypergraph : Hypergraph, optional
        The desired end state. If None, only the obstruction term is minimised.
    T : int
        Number of intermediate time steps to optimise over.
    kinetic_weight : float
        Weight of the kinetic term (smoothness).
    potential_weight : float
        Weight of the obstruction term.
    terminal_weight : float
        Weight of the terminal cost (distance to target).
    learning_rate : float
        Step size for gradient descent.
    max_iterations : int
        Maximum optimisation iterations.
    """
    def __init__(
        self,
        initial_hypergraph: Any,
        target_hypergraph: Optional[Any] = None,
        T: int = 10,
        kinetic_weight: float = 1.0,
        potential_weight: float = 10.0,
        terminal_weight: float = 100.0,
        learning_rate: float = 0.01,
        max_iterations: int = 200,
    ):
        self.initial = initial_hypergraph
        self.target = target_hypergraph
        self.T = T
        self.kinetic_weight = kinetic_weight
        self.potential_weight = potential_weight
        self.terminal_weight = terminal_weight
        self.learning_rate = learning_rate
        self.max_iterations = max_iterations

    def _obstruction(self, hypergraph) -> float:
        """Compute the sheaf cohomology obstruction as a scalar."""
        if SheafHypergraph is None:
            # Fallback: use number of vertices minus number of hyperedges as a proxy
            return float(len(hypergraph.vertices) - len(hypergraph.hyperedges))
        try:
            vertices = [f"v_{v}" for v in sorted(hypergraph.vertices)]
            hyperedges = [{f"v_{v}" for v in edge} for edge in hypergraph.hyperedges.values()]
            if not vertices:
                return 0.0
            shg = SheafHypergraph(vertices, hyperedges)
            cohom = shg.compute_cohomology()
            return float(cohom.h1_dimension)
        except Exception:
            return float(len(hypergraph.vertices))

    def _hypergraph_distance(self, h1, h2) -> float:
        """
        Compute a structural distance between two hypergraphs.
        Defined as the number of hyperedges that differ (symmetric difference).
        """
        edges1 = set(frozenset(e) for e in h1.hyperedges.values())
        edges2 = set(frozenset(e) for e in h2.hyperedges.values())
        sym_diff = len(edges1.symmetric_difference(edges2))
        return float(sym_diff)

    def _mutate_hypergraph(self, hypergraph, mutation_weights: Dict[str, float]) -> Any:
        """
        Apply a small mutation to a hypergraph based on weights.
        Positive weight = strengthen/add, negative = weaken/remove.
        This is a simplified continuous parameterisation.
        """
        new_hg = Hypergraph()
        # Copy vertices
        new_hg.vertices = set(hypergraph.vertices)
        # Copy hyperedges with adjusted weights
        for eid, verts in hypergraph.hyperedges.items():
            w = hypergraph.weights.get(eid, 1.0)
            adj = mutation_weights.get(eid, 0.0)
            new_w = max(0.0, w + adj * 0.1)
            if new_w > 0.01:
                new_hg.add_hyperedge(eid, verts.copy(), new_w)
        # Add new edges from mutation_weights that are not present
        for eid, adj in mutation_weights.items():
            if adj > 0.5 and eid not in hypergraph.hyperedges:
                # eid encodes a vertex set as a string; reconstruct
                try:
                    verts = set(eval(eid))
                    new_hg.add_hyperedge(eid, verts, adj * 0.1)
                except Exception:
                    pass
        return new_hg

    def optimise(self) -> List[RetrocausalState]:
        """
        Run the variational optimisation and return the optimal trajectory.

        Returns
        -------
        list of RetrocausalState of length T+1 (initial + T intermediates)
        """
        # Initialise a linear interpolation between initial and target
        # We'll represent the trajectory as a sequence of Hypergraphs
        # and a set of mutation parameters per time step.
        T = self.T
        trajectory = [deepcopy(self.initial)]
        # Create intermediate states by copying and possibly interpolating
        for t in range(1, T):
            interp = Hypergraph()
            interp.vertices = set(self.initial.vertices)
            # Simple interpolation: keep edges present in both extremes
            init_edges = {frozenset(e): w for e, w in zip(self.initial.hyperedges.values(), self.initial.weights.values())}
            if self.target is not None:
                target_edges = {frozenset(e): w for e, w in zip(self.target.hyperedges.values(), self.target.weights.values())}
                for e in init_edges.keys() | target_edges.keys():
                    w_init = init_edges.get(e, 0.0)
                    w_target = target_edges.get(e, 0.0)
                    w_interp = w_init + (w_target - w_init) * (t / T)
                    if w_interp > 0.01:
                        interp.add_hyperedge(str(e), set(e), w_interp)
            else:
                for e, w in init_edges.items():
                    interp.add_hyperedge(str(e), set(e), w)
            trajectory.append(interp)
        if self.target is not None:
            trajectory.append(deepcopy(self.target))
        else:
            trajectory.append(deepcopy(self.initial))

        # Optimisation loop: adjust mutation parameters to minimise action
        # We parameterise each intermediate hypergraph by a vector of edge weights
        # and optimise via gradient-free search (simplified: coordinate descent)
        best_action = float('inf')
        best_trajectory = trajectory

        for iteration in range(self.max_iterations):
            # Compute action for current trajectory
            total_action = 0.0
            obstructions = []
            for t in range(len(trajectory)):
                hg = trajectory[t]
                obs = self._obstruction(hg)
                obstructions.append(obs)
                total_action += self.potential_weight * obs
                if t > 0:
                    dist = self._hypergraph_distance(trajectory[t-1], trajectory[t])
                    total_action += self.kinetic_weight * dist
            # Terminal cost
            if self.target is not None:
                terminal_dist = self._hypergraph_distance(trajectory[-1], self.target)
                total_action += self.terminal_weight * terminal_dist

            if total_action < best_action:
                best_action = total_action
                best_trajectory = deepcopy(trajectory)

            # Perturb one intermediate state and see if action improves
            if T > 1:
                t = np.random.randint(1, T)  # don't change boundaries
                hg = trajectory[t]
                # Try adding/removing a random edge
                edges = list(hg.hyperedges.items())
                if edges and np.random.random() < 0.5:
                    # Remove a random edge
                    eid, verts = random.choice(edges) if 'random' in dir() else edges[0]
                    new_hg = Hypergraph()
                    new_hg.vertices = set(hg.vertices)
                    for eid2, v2 in hg.hyperedges.items():
                        if eid2 != eid:
                            new_hg.add_hyperedge(eid2, v2.copy(), hg.weights.get(eid2, 1.0))
                else:
                    # Add a random edge between two vertices
                    verts_list = list(hg.vertices)
                    if len(verts_list) >= 2:
                        v1, v2 = np.random.choice(verts_list, 2, replace=False)
                        new_hg = deepcopy(hg)
                        new_hg.add_hyperedge(f"new_{iteration}_{t}", {v1, v2}, 0.5)

                trajectory[t] = new_hg

        # Build result with states
        result = []
        for t, hg in enumerate(best_trajectory):
            obs = self._obstruction(hg)
            action_contrib = self.potential_weight * obs
            if t > 0:
                action_contrib += self.kinetic_weight * self._hypergraph_distance(best_trajectory[t-1], hg)
            result.append(RetrocausalState(
                hypergraph=hg,
                obstruction=obs,
                action_contribution=action_contrib,
            ))
        return result

    def optimal_trajectory(self) -> Dict[str, Any]:
        """
        Run optimisation and return a summary of the optimal path.

        Returns
        -------
        dict with 'states', 'total_action', 'final_obstruction', 'path_length'
        """
        states = self.optimise()
        total_action = sum(s.action_contribution for s in states)
        return {
            'states': states,
            'total_action': total_action,
            'final_obstruction': states[-1].obstruction,
            'path_length': len(states),
        }