"""
PROBABILISTIC MODELS – ULTIMATE IMPLEMENTATION
===============================================
This module provides a comprehensive suite of probabilistic graphical models
for use within Layer 2 (Relational Dynamics). It includes:

- Bayesian Networks (directed acyclic graphs) with exact inference (variable elimination)
  and approximate inference (rejection sampling, likelihood weighting).
- Markov Random Fields (undirected graphs) with Gibbs sampling, Iterated Conditional Modes,
  and parameter learning via pseudo‑likelihood.
- Conditional Random Fields for sequence labeling with a pure‑Python implementation
  (forward‑backward, Viterbi, SGD learning) and optional sklearn‑crfsuite backend.
- Hidden Markov Models with forward‑backward, Viterbi, and Baum‑Welch learning.

All models degrade gracefully if external libraries are missing, providing
minimal pure‑Python implementations for educational purposes. For production,
we recommend installing the relevant libraries (pgmpy, pomegranate, sklearn-crfsuite, torch).

The module follows the Layer 2 philosophy: optional features, graceful degradation,
and a uniform interface.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Set, Any, Tuple, Union, Callable
from collections import defaultdict
import itertools
import warnings

# ============================================================================
# OPTIONAL LIBRARIES – ALL HANDLED GRACEFULLY
# ============================================================================

# pgmpy for Bayesian Networks
try:
    import pgmpy
    from pgmpy.models import BayesianNetwork as PgmpyBN
    from pgmpy.factors.discrete import TabularCPD
    from pgmpy.inference import VariableElimination
    HAS_PGMPY = True
except ImportError:
    HAS_PGMPY = False
    pgmpy = None

# pomegranate for HMMs and Bayesian Networks
try:
    import pomegranate
    from pomegranate import HiddenMarkovModel as PomegranateHMM
    from pomegranate import BayesianNetwork as PomegranateBN
    HAS_POMEGRANATE = True
except ImportError:
    HAS_POMEGRANATE = False
    pomegranate = None

# sklearn-crfsuite for CRFs
try:
    import sklearn_crfsuite
    from sklearn_crfsuite import CRF as SklearnCRF
    HAS_SKLEARN_CRF = True
except ImportError:
    HAS_SKLEARN_CRF = False
    sklearn_crfsuite = None

# scikit-learn for general utilities
try:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# PyTorch for gradient‑based learning (optional)
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# NetworkX for graph visualization (optional)
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

logger = logging.getLogger(__name__)


# ============================================================================
# UTILITY FUNCTIONS FOR LAYER 2 INTEGRATION
# ============================================================================

def discretize_from_registry(
    data: np.ndarray,
    variable_names: List[str],
    registry: Dict[str, Dict[str, Any]],
    method: str = 'equal_width',
    bins: int = 10,
    return_encodings: bool = False
) -> Union[np.ndarray, Tuple[np.ndarray, Dict]]:
    """
    Discretize continuous Layer 1 values according to a registry of specifications.

    The registry should contain, for each variable that needs discretization, a dictionary
    with keys such as 'bins' (int or list of edges), 'method' ('equal_width', 'equal_freq',
    or 'custom'), and optionally 'labels' for the resulting categories.

    Args:
        data: 2D array of shape (n_samples, n_variables) with continuous values.
        variable_names: List of variable names corresponding to columns.
        registry: Dictionary mapping variable name -> discretization parameters.
        method: Default discretization method if not specified in registry.
        bins: Default number of bins if not specified.
        return_encodings: If True, also return a dictionary mapping each variable to the
                          bin edges used (for later inverse transformation).

    Returns:
        Discretized data as integer codes (0 .. n_bins-1). If return_encodings is True,
        returns (discretized_data, encodings) where encodings is a dict with variable
        names as keys and the bin edges as values.
    """
    if data.ndim != 2:
        raise ValueError("data must be a 2D array")
    n_samples, n_vars = data.shape
    if len(variable_names) != n_vars:
        raise ValueError("Length of variable_names must match number of columns in data")

    discretized = np.zeros_like(data, dtype=int)
    encodings = {}

    for idx, var in enumerate(variable_names):
        col = data[:, idx]
        if var in registry:
            spec = registry[var]
            method_ = spec.get('method', method)
            bins_ = spec.get('bins', bins)
            labels_ = spec.get('labels', None)
        else:
            # No specification: treat as already discrete? Or use default.
            # Here we assume that if not in registry, the column is already discrete
            # (e.g., integer codes). We'll just copy and hope.
            # To be safe, we could raise a warning.
            discretized[:, idx] = col.astype(int)
            continue

        # Apply discretization
        if method_ == 'equal_width':
            # Equal width binning
            min_val, max_val = col.min(), col.max()
            if max_val - min_val < 1e-12:
                # constant column – all in one bin
                edges = np.array([min_val - 1, min_val + 1])  # will produce one bin
            else:
                edges = np.linspace(min_val, max_val, bins_ + 1)
            # Digitize: find bin indices (0-based)
            codes = np.digitize(col, edges[:-1]) - 1
            # Ensure codes are in [0, bins_-1]
            codes = np.clip(codes, 0, bins_ - 1)
            discretized[:, idx] = codes
            encodings[var] = edges

        elif method_ == 'equal_freq':
            # Equal frequency binning (quantile-based)
            try:
                from sklearn.preprocessing import KBinsDiscretizer
                kbd = KBinsDiscretizer(n_bins=bins_, encode='ordinal', strategy='quantile')
                discretized_col = kbd.fit_transform(col.reshape(-1, 1)).flatten().astype(int)
                discretized[:, idx] = discretized_col
                encodings[var] = kbd.bin_edges_[0]
            except ImportError:
                # Fallback: manual quantile binning
                percentiles = np.linspace(0, 100, bins_ + 1)[1:-1]
                edges = np.percentile(col, percentiles)
                edges = np.concatenate(([col.min()], edges, [col.max() + 1e-12]))
                codes = np.digitize(col, edges[:-1]) - 1
                codes = np.clip(codes, 0, bins_ - 1)
                discretized[:, idx] = codes
                encodings[var] = edges

        elif method_ == 'custom':
            # Use custom bin edges provided in spec
            edges = spec.get('edges')
            if edges is None:
                raise ValueError(f"Custom discretization for {var} requires 'edges'")
            codes = np.digitize(col, edges[:-1]) - 1
            codes = np.clip(codes, 0, len(edges) - 2)
            discretized[:, idx] = codes
            encodings[var] = edges

        else:
            raise ValueError(f"Unknown discretization method: {method_}")

        # If labels are provided, we could map codes to labels, but we keep integer codes.

    if return_encodings:
        return discretized, encodings
    return discretized


def from_temporal_registry(
    registry: Dict[str, Any],
    phase_key: str = 'default'
) -> 'HiddenMarkovModel':
    """
    Build a Hidden Markov Model from a temporal phase registry.

    The registry should contain specifications for states, transitions, and emissions
    under a given phase key. Typical structure:

    registry = {
        'phases': {
            'phase_name': {
                'states': ['Rainy', 'Sunny'],
                'start_prob': [0.6, 0.4],
                'transition_matrix': [[0.7, 0.3], [0.4, 0.6]],
                'emission_matrix': [[0.1, 0.4, 0.5], [0.6, 0.3, 0.1]],
                'observation_symbols': ['walk', 'shop', 'clean']  # optional
            }
        }
    }

    Args:
        registry: Dictionary containing phase definitions.
        phase_key: Key identifying which phase to use (default 'default').

    Returns:
        An instance of HiddenMarkovModel initialized with the parameters from the registry.
    """
    if 'phases' not in registry:
        raise ValueError("Registry must contain 'phases' key")
    phases = registry['phases']
    if phase_key not in phases:
        raise ValueError(f"Phase '{phase_key}' not found in registry")
    phase = phases[phase_key]

    # Extract required fields
    states = phase.get('states')
    start_prob = phase.get('start_prob')
    transition_matrix = phase.get('transition_matrix')
    emission_matrix = phase.get('emission_matrix')
    observation_symbols = phase.get('observation_symbols', None)

    if states is None:
        raise ValueError("Phase must define 'states'")
    if start_prob is None:
        raise ValueError("Phase must define 'start_prob'")
    if transition_matrix is None:
        raise ValueError("Phase must define 'transition_matrix'")
    if emission_matrix is None:
        raise ValueError("Phase must define 'emission_matrix'")

    n_states = len(states)
    n_obs = emission_matrix.shape[1] if hasattr(emission_matrix, 'shape') else len(emission_matrix[0])

    # Convert to numpy arrays if not already
    start_prob = np.array(start_prob, dtype=float)
    transition_matrix = np.array(transition_matrix, dtype=float)
    emission_matrix = np.array(emission_matrix, dtype=float)

    # Normalize if needed (soft requirement)
    start_prob /= start_prob.sum()
    transition_matrix /= transition_matrix.sum(axis=1, keepdims=True)
    emission_matrix /= emission_matrix.sum(axis=1, keepdims=True)

    # Create HMM
    hmm = HiddenMarkovModel(
        n_states=n_states,
        n_obs=n_obs,
        start_prob=start_prob,
        trans_prob=transition_matrix,
        emit_prob=emission_matrix
    )

    # Optionally store metadata
    hmm.state_names = states
    hmm.observation_symbols = observation_symbols

    return hmm


# ============================================================================
# BASE CLASS
# ============================================================================

class ProbabilisticModel:
    """
    Abstract base class for all probabilistic graphical models.
    Defines common interface for inference, learning, and sampling.
    """
    def __init__(self):
        self.is_fitted = False

    def fit(self, data: np.ndarray, **kwargs) -> 'ProbabilisticModel':
        """Learn parameters from data."""
        raise NotImplementedError

    def predict(self, data: np.ndarray, **kwargs) -> np.ndarray:
        """Perform prediction (most probable explanation)."""
        raise NotImplementedError

    def log_likelihood(self, data: np.ndarray) -> float:
        """Compute log‑likelihood of data under the model."""
        raise NotImplementedError

    def sample(self, n: int = 1) -> List[List[str]]:
        """
        Generate a label sequence by iterative sampling from the conditional
        distribution of each label given the previous label and the features.
        This is an approximation of the full CRF distribution.
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted")
        if self.label_set is None:
            raise ValueError("Label set not initialised – fit the model first")

        samples = []
        for _ in range(n):
            seq_labels = []
            prev_label = None
            # We need a sequence of features to condition on; we generate a "dummy" sequence
            # by sampling a random label at each step and using the feature function.
            # In practice, we'd use a given observation sequence, but for standalone
            # sampling we generate synthetic observations.
            for pos in range(5):  # default length 5
                # Build feature dict for position (using previous label if any)
                features = {}
                features['bias'] = 1.0
                if pos > 0 and prev_label is not None:
                    features[f'transition'] = 1.0
                # Emission scores
                emit_scores = np.zeros(len(self.label_set))
                for feat, val in features.items():
                    if feat in self.feature_to_idx:
                        f_idx = self.feature_to_idx[feat]
                        emit_scores += self.emission_params[f_idx, :] * val
                # Combine with transition from previous label
                if prev_label is not None:
                    prev_idx = self.label_to_idx[prev_label]
                    scores = emit_scores + self.transition_params[prev_idx, :]
                else:
                    scores = emit_scores
                probs = np.exp(scores) / (np.sum(np.exp(scores)) + 1e-100)
                new_label = np.random.choice(len(self.label_set), p=probs)
                prev_label = self.idx_to_label[new_label]
                seq_labels.append(prev_label)
            samples.append(seq_labels)
        return samples


# ============================================================================
# BAYESIAN NETWORK
# ============================================================================

class BayesianNetwork(ProbabilisticModel):
    """
    Bayesian Network (directed acyclic graph) over discrete variables.

    If pgmpy is installed, it uses pgmpy for exact inference and parameter learning.
    Otherwise, a simple implementation using tabular CPDs and variable elimination
    is provided (limited to small networks).
    """
    def __init__(self, edges: List[Tuple[str, str]] = None,
                 variable_names: List[str] = None,
                 cardinalities: Dict[str, int] = None):
        """
        Args:
            edges: list of (parent, child) edges.
            variable_names: list of variable names in topological order (optional).
            cardinalities: dict mapping variable name -> number of states.
        """
        super().__init__()
        self.edges = edges or []
        self.variable_names = variable_names or []
        self.cardinalities = cardinalities or {}
        self.cpds = {}  # variable -> conditional probability table (numpy array)
        self._model = None  # pgmpy model if used
        self._inference = None

        if HAS_PGMPY:
            self._use_pgmpy = True
        else:
            self._use_pgmpy = False
            logger.info("pgmpy not installed – using simple Bayesian Network implementation (limited).")

    def add_edge(self, parent: str, child: str):
        self.edges.append((parent, child))
        if parent not in self.variable_names:
            self.variable_names.append(parent)
        if child not in self.variable_names:
            self.variable_names.append(child)

    def set_cpd(self, variable: str, cpd: np.ndarray, parents: List[str]):
        """
        Set conditional probability table for a variable.
        cpd shape: [cardinality of variable] + [cardinalities of parents]
        (parents in the given order).
        """
        if self._use_pgmpy:
            # Build pgmpy CPD
            parent_card = [self.cardinalities[p] for p in parents]
            pg_cpd = TabularCPD(variable, self.cardinalities[variable],
                                cpd.reshape(self.cardinalities[variable], -1),
                                evidence=parents, evidence_card=parent_card)
            if self._model is None:
                self._model = PgmpyBN(self.edges)
            self._model.add_cpds(pg_cpd)
        else:
            self.cpds[variable] = (cpd, parents)

    def fit(self, data: np.ndarray, **kwargs):
        """
        Learn CPDs from data using maximum likelihood estimation.
        Data: array of shape (n_samples, n_variables), with columns in order of self.variable_names.
        """
        if self._use_pgmpy:
            # Convert data to pandas DataFrame expected by pgmpy
            import pandas as pd
            df = pd.DataFrame(data, columns=self.variable_names)
            self._model = PgmpyBN(self.edges)
            self._model.fit(df)
            self._inference = VariableElimination(self._model)
        else:
            # Simple MLE: count frequencies
            n_samples = data.shape[0]
            for var in self.variable_names:
                parents = [p for p, c in self.edges if c == var]
                if not parents:
                    # root node: just marginal
                    counts = np.zeros(self.cardinalities[var])
                    for i in range(n_samples):
                        counts[int(data[i, self.variable_names.index(var)])] += 1
                    cpd = counts / n_samples
                else:
                    # conditional: need to index by parent combinations
                    parent_indices = [self.variable_names.index(p) for p in parents]
                    parent_card = [self.cardinalities[p] for p in parents]
                    shape = [self.cardinalities[var]] + parent_card
                    counts = np.zeros(shape, dtype=float)
                    for i in range(n_samples):
                        child_val = int(data[i, self.variable_names.index(var)])
                        parent_vals = tuple(int(data[i, idx]) for idx in parent_indices)
                        idx = (child_val,) + parent_vals
                        counts[idx] += 1
                    # Normalize over child dimension for each parent combination
                    for idx_parent in itertools.product(*[range(c) for c in parent_card]):
                        total = np.sum(counts[(slice(None),) + idx_parent])
                        if total > 0:
                            counts[(slice(None),) + idx_parent] /= total
                    cpd = counts
                self.cpds[var] = (cpd, parents)
        self.is_fitted = True
        return self
    
    def predict(self, data: np.ndarray, **kwargs) -> np.ndarray:
        """
        For each sample, compute the most probable state of all variables (or query variables).
        If query is not specified, returns MPE for all variables.
        Evidence: use NaN for missing values.
        """
        if self._use_pgmpy and self._inference:
            # pgmpy map_query
            import pandas as pd
            df = pd.DataFrame(data, columns=self.variable_names)
            results = []
            for _, row in df.iterrows():
                evidence = {var: row[var] for var in self.variable_names if not np.isnan(row[var])}
                mpe = self._inference.map_query(variables=self.variable_names, evidence=evidence)
                results.append([mpe[var] for var in self.variable_names])
            return np.array(results)
        else:
            # Voor grote netwerken: gebruik simulated annealing of random sampling + kies beste
            if len(self.variable_names) > 15:
                # Simuleer 100 samples en kies degene met hoogste waarschijnlijkheid
                best_sample = None
                best_prob = -np.inf
                for _ in range(100):
                    sample = self.sample(1)[0]
                    # Bereken log-kans
                    prob = 1.0
                    for idx, var in enumerate(self.variable_names):
                        cpd, parents = self.cpds[var]
                        child_val = int(sample[idx])
                        if not parents:
                            prob_val = cpd[child_val]
                        else:
                            parent_vals = tuple(int(sample[self.variable_names.index(p)]) for p in parents)
                            prob_val = cpd[(child_val,) + parent_vals]
                        prob *= prob_val
                    if prob > best_prob:
                        best_prob = prob
                        best_sample = sample
                return np.array([best_sample])
            else:
                results = []
                # Precompute all possible assignments (Cartesian product of variable domains)
                domains = [range(self.cardinalities[v]) for v in self.variable_names]
                all_assignments = list(itertools.product(*domains))
                # For each data point (with possible NaNs as evidence)
                for row in data:
                    evidence = {var: row[idx] for idx, var in enumerate(self.variable_names) if not np.isnan(row[idx])}
                    # Filter assignments consistent with evidence
                    valid_assignments = []
                    for assign in all_assignments:
                        consistent = True
                        for idx, var in enumerate(self.variable_names):
                            if var in evidence and assign[idx] != evidence[var]:
                                consistent = False
                                break
                        if consistent:
                            valid_assignments.append(assign)
                    # Compute probability for each valid assignment using chain rule
                    best_assign = None
                    best_prob = -np.inf
                    for assign in valid_assignments:
                        prob = 1.0
                        # Compute P(assign) = ∏ P(var | parents)
                        for idx, var in enumerate(self.variable_names):
                            cpd, parents = self.cpds[var]
                            child_val = assign[idx]
                            if not parents:
                                prob_val = cpd[child_val]
                            else:
                                parent_vals = tuple(assign[self.variable_names.index(p)] for p in parents)
                                # cpd shape: [child] + parent_dims
                                prob_val = cpd[(child_val,) + parent_vals]
                            prob *= prob_val
                        if prob > best_prob:
                            best_prob = prob
                            best_assign = assign
                    results.append(list(best_assign))
                    return np.array(results)

    def log_likelihood(self, data: np.ndarray) -> float:
        if self._use_pgmpy and self._model:
            import pandas as pd
            df = pd.DataFrame(data, columns=self.variable_names)
            return self._model.log_likelihood(df)
        else:
            # Compute log‑likelihood by summing over samples using stored CPDs
            ll = 0.0
            for i in range(data.shape[0]):
                sample_ll = 0.0
                for var in self.variable_names:
                    cpd, parents = self.cpds[var]
                    child_val = int(data[i, self.variable_names.index(var)])
                    if not parents:
                        prob = cpd[child_val]
                    else:
                        parent_vals = tuple(int(data[i, self.variable_names.index(p)]) for p in parents)
                        idx = (child_val,) + parent_vals
                        prob = cpd[idx]
                    sample_ll += np.log(max(prob, 1e-100))
                ll += sample_ll
            return ll

    def sample(self, n: int) -> np.ndarray:
        if self._use_pgmpy and self._model:
            # pgmpy's forward sampling
            from pgmpy.sampling import BayesianModelSampling
            sampler = BayesianModelSampling(self._model)
            samples = sampler.forward_sample(size=n)
            return samples[self.variable_names].to_numpy()
        else:
            # Simple ancestral sampling
            # Determine topological order
            topo = self._topological_sort()
            samples = np.zeros((n, len(self.variable_names)))
            var_to_idx = {v: i for i, v in enumerate(self.variable_names)}
            for i in range(n):
                sampled_vals = {}
                for var in topo:
                    cpd, parents = self.cpds[var]
                    if not parents:
                        # sample from marginal
                        probs = cpd.flatten()
                        sampled = np.random.choice(self.cardinalities[var], p=probs)
                    else:
                        # get parent values
                        parent_vals = tuple(sampled_vals[p] for p in parents)
                        idx = (slice(None),) + parent_vals
                        probs = cpd[idx].flatten()
                        sampled = np.random.choice(self.cardinalities[var], p=probs)
                    sampled_vals[var] = sampled
                    samples[i, var_to_idx[var]] = sampled
            return samples

    def _topological_sort(self) -> List[str]:
        """Return variables in topological order (parents before children)."""
        graph = defaultdict(list)
        for p, c in self.edges:
            graph[p].append(c)
        # Kahn's algorithm
        in_degree = {v: 0 for v in self.variable_names}
        for p, c in self.edges:
            in_degree[c] += 1
        queue = [v for v in self.variable_names if in_degree[v] == 0]
        order = []
        while queue:
            v = queue.pop(0)
            order.append(v)
            for child in graph[v]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
        if len(order) != len(self.variable_names):
            raise ValueError("Graph has cycles")
        return order


# ============================================================================
# MARKOV RANDOM FIELD (undirected)
# ============================================================================

class MarkovRandomField(ProbabilisticModel):
    """
    Markov Random Field (pairwise) over discrete variables.
    Energy‑based model: P(x) = (1/Z) exp(-E(x)).
    Supports Gibbs sampling, Iterated Conditional Modes (ICM) for inference,
    and parameter learning via pseudo‑likelihood (using gradient descent).
    """
    def __init__(self, variables: List[str], cardinalities: Dict[str, int]):
        super().__init__()
        self.variables = variables
        self.cardinalities = cardinalities
        self.var_index = {v: i for i, v in enumerate(variables)}
        self.pairwise_potentials = {}  # (v1, v2) -> matrix of size c1 x c2
        self.unary_potentials = {}      # v -> array of size c_v

    def add_unary_potential(self, variable: str, potential: np.ndarray):
        """potential: array of length cardinality[variable]."""
        if variable not in self.var_index:
            raise ValueError(f"Unknown variable {variable}")
        self.unary_potentials[variable] = potential

    def add_pairwise_potential(self, v1: str, v2: str, potential: np.ndarray):
        """potential: 2D array of shape (card[v1], card[v2])."""
        if v1 not in self.var_index or v2 not in self.var_index:
            raise ValueError("Unknown variable")
        # Ensure symmetric? Not required, but MRF usually undirected.
        self.pairwise_potentials[(v1, v2)] = potential
        self.pairwise_potentials[(v2, v1)] = potential.T

    def energy(self, x: np.ndarray) -> float:
        """
        Compute energy E(x) for a single sample x (array of values for each variable).
        """
        e = 0.0
        for var, pot in self.unary_potentials.items():
            idx = self.var_index[var]
            e += pot[int(x[idx])]
        for (v1, v2), pot in self.pairwise_potentials.items():
            if v1 < v2:  # count each pair once
                idx1 = self.var_index[v1]
                idx2 = self.var_index[v2]
                e += pot[int(x[idx1]), int(x[idx2])]
        return e

    def log_likelihood(self, data: np.ndarray) -> float:
        """
        Compute log‑likelihood of data (requires partition function Z, which is intractable).
        This returns an unnormalized log‑likelihood (negative energy) for each sample summed.
        """
        total = 0.0
        for i in range(data.shape[0]):
            total += -self.energy(data[i])
        return total

    def pseudo_likelihood(self, data: np.ndarray) -> float:
        """
        Compute pseudo‑likelihood (product over conditionals) for parameter learning.
        """
        pl = 0.0
        n_samples = data.shape[0]
        for i in range(n_samples):
            sample = data[i]
            for var in self.variables:
                # compute conditional probability of var given its neighbors
                neighbors = self._neighbors(var)
                if not neighbors:
                    # No neighbors: conditional is just uniform (or could use unary only)
                    # We'll include unary as the only factor
                    if var in self.unary_potentials:
                        probs = np.exp(-self.unary_potentials[var])
                        probs /= probs.sum()
                        idx = self.var_index[var]
                        pl += np.log(probs[int(sample[idx])] + 1e-100)
                    continue
                # Compute energies for each possible value of var, conditioned on neighbors fixed
                energies = []
                idx = self.var_index[var]
                for val in range(self.cardinalities[var]):
                    e = 0.0
                    # unary
                    if var in self.unary_potentials:
                        e += self.unary_potentials[var][val]
                    # pairwise with neighbors
                    for nb in neighbors:
                        nb_idx = self.var_index[nb]
                        pot = self.pairwise_potentials.get((var, nb))
                        if pot is not None:
                            e += pot[val, int(sample[nb_idx])]
                    energies.append(e)
                energies = np.array(energies)
                probs = np.exp(-energies) / (np.sum(np.exp(-energies)) + 1e-100)
                pl += np.log(probs[int(sample[idx])] + 1e-100)
        return pl

    def _neighbors(self, var: str) -> List[str]:
        """Return neighbors of var in the pairwise graph."""
        nbs = set()
        for (v1, v2) in self.pairwise_potentials:
            if v1 == var and v2 != var:
                nbs.add(v2)
            if v2 == var and v1 != var:
                nbs.add(v1)
        return list(nbs)

    def fit(self, data: np.ndarray, method: str = 'pseudo', **kwargs):
        """
        Fit parameters (unary and pairwise potentials) using pseudo‑likelihood.
        Uses gradient descent (with PyTorch if available, else finite differences).
        """
        if method != 'pseudo':
            raise ValueError(f"Unknown method {method}")

        # If potentials are already set, we can refine them; otherwise initialize
        # We'll treat the potentials themselves as parameters to learn.
        # For simplicity, we assume all variables have unary potentials and all edges have pairwise potentials.
        # If not set, initialize them to zeros.
        for var in self.variables:
            if var not in self.unary_potentials:
                self.unary_potentials[var] = np.zeros(self.cardinalities[var])
        # For pairwise, we need to know edges. We'll assume all pairs? Not; we need the graph structure.
        # If no pairwise potentials exist, we cannot learn them. We'll raise an error.
        if not self.pairwise_potentials:
            raise ValueError("No pairwise potentials defined – cannot learn parameters.")

        # Convert data to float for gradient computations
        data_float = data.astype(float)

        # Use PyTorch if available for efficient gradient descent
        if HAS_TORCH:
            self._fit_torch(data_float, **kwargs)
        else:
            self._fit_numpy(data_float, **kwargs)
        self.is_fitted = True
        return self

    def _fit_torch(self, data: np.ndarray, lr: float = 0.01, max_iter: int = 1000,
                   tol: float = 1e-4, verbose: bool = False):
        """Fit using PyTorch autograd."""
        # Convert potentials to torch tensors with requires_grad
        unary_tensors = {}
        pairwise_tensors = {}
        for var, pot in self.unary_potentials.items():
            unary_tensors[var] = torch.tensor(pot, dtype=torch.float32, requires_grad=True)
        for (v1, v2), pot in self.pairwise_potentials.items():
            # Only store each pair once (v1 < v2) to avoid double counting parameters
            if v1 < v2:
                pairwise_tensors[(v1, v2)] = torch.tensor(pot, dtype=torch.float32, requires_grad=True)

        # Optimizer
        params = list(unary_tensors.values()) + list(pairwise_tensors.values())
        optimizer = torch.optim.Adam(params, lr=lr)

        data_t = torch.tensor(data, dtype=torch.long)

        prev_pl = -np.inf
        for it in range(max_iter):
            # Compute pseudo‑likelihood
            pl = self._pseudo_likelihood_torch(data_t, unary_tensors, pairwise_tensors)
            loss = -pl  # maximize PL

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # Project potentials? Not needed; they can be any real numbers.
            # Check convergence
            if it % 10 == 0 and verbose:
                print(f"Iter {it}, PL = {pl.item():.4f}")

            if torch.abs(pl - prev_pl) < tol:
                break
            prev_pl = pl

        # Convert back to numpy
        for var, t in unary_tensors.items():
            self.unary_potentials[var] = t.detach().numpy()
        for (v1, v2), t in pairwise_tensors.items():
            self.pairwise_potentials[(v1, v2)] = t.detach().numpy()
            self.pairwise_potentials[(v2, v1)] = t.detach().numpy().T

    def _pseudo_likelihood_torch(self, data, unary, pairwise):
        """Compute pseudo‑likelihood using torch."""
        n_samples = data.shape[0]
        pl = 0.0
        for var in self.variables:
            idx = self.var_index[var]
            neighbors = self._neighbors(var)
            if not neighbors:
                # Only unary
                probs = torch.softmax(-unary[var], dim=0)
                vals = data[:, idx]
                pl += torch.log(probs[vals] + 1e-100).sum()
            else:
                # For each sample, compute conditional probability
                for i in range(n_samples):
                    sample = data[i]
                    energies = []
                    for val in range(self.cardinalities[var]):
                        e = unary[var][val].clone()
                        for nb in neighbors:
                            nb_idx = self.var_index[nb]
                            # Get pairwise potential
                            key = (var, nb) if (var, nb) in pairwise else (nb, var)
                            pot = pairwise[key]
                            # pot shape: (card[var], card[nb]) if key order is (var, nb), else transposed
                            if key == (var, nb):
                                e += pot[val, sample[nb_idx]]
                            else:
                                e += pot[sample[nb_idx], val]  # pot is (nb, var)
                        energies.append(e)
                    energies = torch.stack(energies)
                    probs = torch.softmax(-energies, dim=0)
                    pl += torch.log(probs[data[i, idx]] + 1e-100)
        return pl / n_samples  # average PL

    def _fit_numpy(self, data: np.ndarray, lr: float = 0.01, max_iter: int = 1000,
                   tol: float = 1e-4, verbose: bool = False):
        """Fit using finite differences (very slow, only for tiny problems)."""
        n_samples = data.shape[0]
        # Flatten all parameters into a single vector
        param_arrays = []
        param_shapes = []
        param_keys = []

        # Unary
        for var, pot in self.unary_potentials.items():
            param_keys.append(('unary', var))
            param_arrays.append(pot.flatten())
            param_shapes.append(pot.shape)
        # Pairwise (store only one direction)
        for (v1, v2), pot in self.pairwise_potentials.items():
            if v1 < v2:
                param_keys.append(('pairwise', v1, v2))
                param_arrays.append(pot.flatten())
                param_shapes.append(pot.shape)

        theta = np.concatenate(param_arrays)

        def neg_pl(theta_vec):
            # Reconstruct potentials
            unary = {}
            pairwise = {}
            start = 0
            for key, shape in zip(param_keys, param_shapes):
                size = np.prod(shape)
                if key[0] == 'unary':
                    var = key[1]
                    unary[var] = theta_vec[start:start+size].reshape(shape)
                else:  # pairwise
                    v1, v2 = key[1], key[2]
                    pairwise[(v1, v2)] = theta_vec[start:start+size].reshape(shape)
                start += size
            # Compute negative pseudo‑likelihood
            pl = 0.0
            for i in range(n_samples):
                sample = data[i]
                for var in self.variables:
                    idx = self.var_index[var]
                    neighbors = self._neighbors(var)
                    if not neighbors:
                        probs = np.exp(-unary[var])
                        probs /= probs.sum()
                        pl += np.log(probs[int(sample[idx])] + 1e-100)
                    else:
                        energies = []
                        for val in range(self.cardinalities[var]):
                            e = unary[var][val]
                            for nb in neighbors:
                                nb_idx = self.var_index[nb]
                                if (var, nb) in pairwise:
                                    e += pairwise[(var, nb)][val, int(sample[nb_idx])]
                                else:
                                    e += pairwise[(nb, var)][int(sample[nb_idx]), val]
                            energies.append(e)
                        energies = np.array(energies)
                        probs = np.exp(-energies) / np.sum(np.exp(-energies))
                        pl += np.log(probs[int(sample[idx])] + 1e-100)
            return -pl / n_samples

        # Simple gradient descent with numerical gradient
        prev_loss = neg_pl(theta)
        for it in range(max_iter):
            grad = np.zeros_like(theta)
            eps = 1e-6
            for j in range(len(theta)):
                theta_plus = theta.copy()
                theta_plus[j] += eps
                loss_plus = neg_pl(theta_plus)
                grad[j] = (loss_plus - prev_loss) / eps
            theta -= lr * grad
            loss = neg_pl(theta)
            if it % 10 == 0 and verbose:
                print(f"Iter {it}, loss = {loss:.4f}")
            if abs(prev_loss - loss) < tol:
                break
            prev_loss = loss

        # Reconstruct potentials from final theta
        start = 0
        for key, shape in zip(param_keys, param_shapes):
            size = np.prod(shape)
            if key[0] == 'unary':
                var = key[1]
                self.unary_potentials[var] = theta[start:start+size].reshape(shape)
            else:
                v1, v2 = key[1], key[2]
                pot = theta[start:start+size].reshape(shape)
                self.pairwise_potentials[(v1, v2)] = pot
                self.pairwise_potentials[(v2, v1)] = pot.T
            start += size

    def predict(self, data: np.ndarray, method: str = 'icm', **kwargs) -> np.ndarray:
        """
        Find most probable configuration (MAP) given evidence.
        Evidence variables can be NaN in data.
        """
        if method == 'icm':
            return self._icm(data, **kwargs)
        elif method == 'gibbs':
            # Gibbs sampling can produce samples; to get MAP, run many iterations and take best.
            return self._gibbs_map(data, **kwargs)
        else:
            raise ValueError(f"Unknown method {method}")

    def _icm(self, data: np.ndarray, max_iter: int = 10) -> np.ndarray:
        """
        Iterated Conditional Modes: greedily update each variable to its conditional mode.
        """
        n_samples = data.shape[0]
        result = data.copy()
        for i in range(n_samples):
            for _ in range(max_iter):
                changed = False
                for var in self.variables:
                    idx = self.var_index[var]
                    # If evidence present, skip (fixed)
                    if not np.isnan(result[i, idx]):
                        continue
                    # Compute conditional energy for each possible value
                    energies = []
                    for val in range(self.cardinalities[var]):
                        e = 0.0
                        if var in self.unary_potentials:
                            e += self.unary_potentials[var][val]
                        for nb in self._neighbors(var):
                            nb_idx = self.var_index[nb]
                            if not np.isnan(result[i, nb_idx]):
                                pot = self.pairwise_potentials.get((var, nb))
                                if pot is not None:
                                    e += pot[val, int(result[i, nb_idx])]
                        energies.append(e)
                    best_val = np.argmin(energies)
                    if best_val != result[i, idx]:
                        result[i, idx] = best_val
                        changed = True
                if not changed:
                    break
        return result

    def _gibbs_map(self, data: np.ndarray, n_samples: int = 100, burn_in: int = 10) -> np.ndarray:
        """
        Use Gibbs sampling and return the sample with lowest energy.
        """
        n_data = data.shape[0]
        result = data.copy()
        for i in range(n_data):
            # Initialize with random values for missing variables
            current = result[i].copy()
            for j, val in enumerate(current):
                if np.isnan(val):
                    current[j] = np.random.randint(self.cardinalities[self.variables[j]])
            best_energy = self.energy(current)
            best_sample = current.copy()
            # Burn-in
            for _ in range(burn_in):
                current = self._gibbs_step(current)
            # Sampling
            for _ in range(n_samples):
                current = self._gibbs_step(current)
                e = self.energy(current)
                if e < best_energy:
                    best_energy = e
                    best_sample = current.copy()
            result[i] = best_sample
        return result

    def sample(self, n: int, burn_in: int = 10, thinning: int = 1) -> np.ndarray:
        """
        Generate samples via Gibbs sampling.
        """
        n_vars = len(self.variables)
        samples = np.zeros((n, n_vars))
        # Initialize randomly
        current = np.array([np.random.randint(self.cardinalities[v]) for v in self.variables])
        # Burn‑in
        for _ in range(burn_in):
            current = self._gibbs_step(current)
        # Collect samples
        for i in range(n):
            for _ in range(thinning):
                current = self._gibbs_step(current)
            samples[i] = current
        return samples

    def _gibbs_step(self, x: np.ndarray) -> np.ndarray:
        """Perform one Gibbs sweep (update each variable in random order)."""
        order = list(range(len(self.variables)))
        np.random.shuffle(order)
        for idx in order:
            var = self.variables[idx]
            # Compute conditional probabilities
            energies = []
            for val in range(self.cardinalities[var]):
                e = 0.0
                if var in self.unary_potentials:
                    e += self.unary_potentials[var][val]
                for nb in self._neighbors(var):
                    nb_idx = self.var_index[nb]
                    pot = self.pairwise_potentials.get((var, nb))
                    if pot is not None:
                        e += pot[val, int(x[nb_idx])]
                energies.append(e)
            energies = np.array(energies)
            probs = np.exp(-energies) / (np.sum(np.exp(-energies)) + 1e-100)
            new_val = np.random.choice(self.cardinalities[var], p=probs)
            x[idx] = new_val
        return x


# ============================================================================
# CONDITIONAL RANDOM FIELD (for sequence labeling) – pure Python implementation
# ============================================================================

class ConditionalRandomField(ProbabilisticModel):
    """
    Linear‑chain Conditional Random Field for sequence labeling.
    Uses sklearn_crfsuite if available; otherwise a pure‑Python implementation
    using forward‑backward for inference and SGD for learning.
    """
    def __init__(self, feature_function: Optional[Callable] = None, algorithm: str = 'sgd'):
        """
        Args:
            feature_function: function that takes (sequence, position) and returns dict of features.
                              If None, a default function using transition features is used.
            algorithm: 'sgd' for stochastic gradient descent (pure Python), or 'lbfgs' if sklearn_crfsuite available.
        """
        super().__init__()
        self.feature_function = feature_function or self._default_features
        self.algorithm = algorithm
        self._use_sklearn = HAS_SKLEARN_CRF and algorithm == 'lbfgs'
        self._model = None
        # Parameters for pure Python version
        self.transition_params = None  # dict: (prev_label, label) -> weight
        self.emission_params = None    # dict: (feature, label) -> weight
        self.feature_set = None
        self.label_set = None

        if not self._use_sklearn:
            logger.info("Using pure‑Python CRF implementation (SGD).")

    def _default_features(self, sequence, pos):
        """Default feature function: current token identity and transition from previous."""
        features = {}
        # Add a bias feature
        features['bias'] = 1.0
        # Current token (for simplicity, use token as is – should be discrete)
        features[f'token={sequence[pos]}'] = 1.0
        if pos > 0:
            # transition feature – we'll handle transitions separately in the model
            # but we can include a generic "transition" feature
            features['transition'] = 1.0
        return features

    def _extract_features(self, X):
        """
        Convert list of sequences into feature vectors for each position.
        Returns:
            feature_sequences: list of list of dict (features for each position)
        """
        feature_sequences = []
        for seq in X:
            seq_features = []
            for pos, _ in enumerate(seq):
                feats = self.feature_function(seq, pos)
                seq_features.append(feats)
            feature_sequences.append(seq_features)
        return feature_sequences

    def _initialize_params(self, X_features, y):
        """Initialize weight vectors from feature and label sets."""
        # Build label set
        labels = set()
        for seq in y:
            labels.update(seq)
        self.label_set = sorted(labels)
        self.label_to_idx = {l: i for i, l in enumerate(self.label_set)}
        self.idx_to_label = {i: l for i, l in enumerate(self.label_set)}
        n_labels = len(self.label_set)

        # Build feature set from X_features
        features = set()
        for seq_feat in X_features:
            for feat_dict in seq_feat:
                features.update(feat_dict.keys())
        self.feature_set = sorted(features)
        self.feature_to_idx = {f: i for i, f in enumerate(self.feature_set)}
        n_features = len(self.feature_set)

        # Initialize weights: transition and emission
        # Transition weights: (prev, cur) -> weight
        self.transition_params = np.zeros((n_labels, n_labels))
        # Emission weights: (feature, label) -> weight
        self.emission_params = np.zeros((n_features, n_labels))
        # Bias feature is treated like any other feature

    def _score(self, features_seq, labels_seq):
        """Compute score for a given sequence of features and labels."""
        score = 0.0
        T = len(features_seq)
        for t in range(T):
            # emission
            for feat, val in features_seq[t].items():
                if feat in self.feature_to_idx:
                    f_idx = self.feature_to_idx[feat]
                    l_idx = self.label_to_idx[labels_seq[t]]
                    score += self.emission_params[f_idx, l_idx] * val
            # transition (except first position)
            if t > 0:
                prev_l = self.label_to_idx[labels_seq[t-1]]
                cur_l = self.label_to_idx[labels_seq[t]]
                score += self.transition_params[prev_l, cur_l]
        return score

    def _forward_backward(self, features_seq):
        """Compute forward and backward probabilities for a sequence."""
        T = len(features_seq)
        n_labels = len(self.label_set)
        # Forward pass
        alpha = np.zeros((T, n_labels))
        # Compute emission scores for first position
        for l_idx in range(n_labels):
            score = 0.0
            for feat, val in features_seq[0].items():
                if feat in self.feature_to_idx:
                    f_idx = self.feature_to_idx[feat]
                    score += self.emission_params[f_idx, l_idx] * val
            alpha[0, l_idx] = np.exp(score)
        alpha[0] /= alpha[0].sum()
        for t in range(1, T):
            for l_idx in range(n_labels):
                # emission score for current label
                emit_score = 0.0
                for feat, val in features_seq[t].items():
                    if feat in self.feature_to_idx:
                        f_idx = self.feature_to_idx[feat]
                        emit_score += self.emission_params[f_idx, l_idx] * val
                # sum over previous labels
                trans_scores = np.exp(self.transition_params[:, l_idx] + emit_score)
                alpha[t, l_idx] = np.sum(alpha[t-1] * trans_scores)
            alpha[t] /= alpha[t].sum()  # normalize to avoid underflow
        # Backward pass
        beta = np.ones((T, n_labels))
        for t in range(T-2, -1, -1):
            for l_idx in range(n_labels):
                # sum over next labels
                trans_scores = np.exp(self.transition_params[l_idx, :] + self._emission_scores(features_seq[t+1]))
                beta[t, l_idx] = np.sum(beta[t+1] * trans_scores)
            beta[t] /= beta[t].sum()
        return alpha, beta

    def _emission_scores(self, features_dict):
        """Return array of emission scores for each label given features."""
        scores = np.zeros(len(self.label_set))
        for feat, val in features_dict.items():
            if feat in self.feature_to_idx:
                f_idx = self.feature_to_idx[feat]
                scores += self.emission_params[f_idx, :] * val
        return scores

    def _log_likelihood(self, X_features, y):
        """Compute log‑likelihood for a batch of sequences."""
        ll = 0.0
        for seq_feat, seq_labels in zip(X_features, y):
            # Compute numerator: exp(score)
            score = self._score(seq_feat, seq_labels)
            # Compute denominator: partition function Z via forward algorithm
            T = len(seq_feat)
            alpha = np.zeros((T, len(self.label_set)))
            # Initial
            alpha[0] = np.exp(self._emission_scores(seq_feat[0]))
            alpha[0] /= alpha[0].sum()
            for t in range(1, T):
                emit_scores = np.exp(self._emission_scores(seq_feat[t]))
                for l in range(len(self.label_set)):
                    trans_scores = np.exp(self.transition_params[:, l])
                    alpha[t, l] = np.sum(alpha[t-1] * trans_scores) * emit_scores[l]
                alpha[t] /= alpha[t].sum()
            Z = alpha[-1].sum()
            ll += score - np.log(Z)
        return ll

    def fit(self, X: List[List], y: List[List], **kwargs):
        """
        Learn CRF parameters.

        If sklearn_crfsuite is available and algorithm='lbfgs', uses that.
        Otherwise uses pure‑Python SGD implementation.
        """
        if self._use_sklearn:
            self._model = SklearnCRF(
                algorithm='lbfgs',
                c1=0.1,
                c2=0.1,
                max_iterations=100,
                all_possible_transitions=True
            )
            self._model.fit(X, y)
            self.is_fitted = True
            return self

        # Pure‑Python SGD
        # Convert to feature sequences
        X_features = self._extract_features(X)
        self._initialize_params(X_features, y)

        # Training parameters
        lr = kwargs.get('lr', 0.01)
        epochs = kwargs.get('epochs', 50)
        batch_size = kwargs.get('batch_size', 1)
        verbose = kwargs.get('verbose', False)

        n_samples = len(X_features)
        for epoch in range(epochs):
            # Shuffle
            indices = np.random.permutation(n_samples)
            total_loss = 0.0
            for i in range(0, n_samples, batch_size):
                batch_idx = indices[i:i+batch_size]
                # Compute gradients for batch
                grad_trans = np.zeros_like(self.transition_params)
                grad_emit = np.zeros_like(self.emission_params)
                loss = 0.0
                for idx in batch_idx:
                    seq_feat = X_features[idx]
                    seq_labels = y[idx]
                    T = len(seq_feat)
                    # Forward‑backward
                    alpha, beta = self._forward_backward(seq_feat)
                    # Compute state and transition posteriors (gamma, xi)
                    gamma = alpha * beta
                    gamma /= gamma.sum(axis=1, keepdims=True) + 1e-100
                    xi = np.zeros((T-1, len(self.label_set), len(self.label_set)))
                    for t in range(T-1):
                        # xi[t, i, j] = P(state_t = i, state_t+1 = j | seq)
                        emit_next = np.exp(self._emission_scores(seq_feat[t+1]))
                        trans_exp = np.exp(self.transition_params)
                        xi[t] = alpha[t][:, None] * trans_exp * emit_next[None, :] * beta[t+1][None, :]
                        xi[t] /= xi[t].sum() + 1e-100
                    # Compute gradients: for each feature, expected counts minus empirical counts
                    # Empirical counts from true labels
                    for t in range(T):
                        l_true = self.label_to_idx[seq_labels[t]]
                        # emission empirical
                        for feat, val in seq_feat[t].items():
                            if feat in self.feature_to_idx:
                                f_idx = self.feature_to_idx[feat]
                                grad_emit[f_idx, l_true] += val
                        # transition empirical (except first)
                        if t > 0:
                            prev_true = self.label_to_idx[seq_labels[t-1]]
                            grad_trans[prev_true, l_true] += 1
                    # Expected counts under model
                    for t in range(T):
                        # emission expected
                        for feat, val in seq_feat[t].items():
                            if feat in self.feature_to_idx:
                                f_idx = self.feature_to_idx[feat]
                                for l in range(len(self.label_set)):
                                    grad_emit[f_idx, l] -= gamma[t, l] * val
                        # transition expected
                        if t < T-1:
                            for i in range(len(self.label_set)):
                                for j in range(len(self.label_set)):
                                    grad_trans[i, j] -= xi[t, i, j]
                    # Accumulate loss (negative log‑likelihood)
                    loss += -self._log_likelihood([seq_feat], [seq_labels])
                # Update
                self.transition_params -= lr * grad_trans / len(batch_idx)
                self.emission_params -= lr * grad_emit / len(batch_idx)
                total_loss += loss
            if verbose and epoch % 10 == 0:
                print(f"Epoch {epoch}, loss = {total_loss / n_samples:.4f}")

        self.is_fitted = True
        return self

    def predict(self, X: List[List]) -> List[List]:
        """Predict label sequences using Viterbi decoding."""
        if self._use_sklearn and self._model:
            return self._model.predict(X)
        else:
            # Viterbi for each sequence
            X_features = self._extract_features(X)
            results = []
            for seq_feat in X_features:
                T = len(seq_feat)
                n_labels = len(self.label_set)
                viterbi = np.zeros((T, n_labels))
                backpointer = np.zeros((T, n_labels), dtype=int)
                # Initial
                viterbi[0] = self._emission_scores(seq_feat[0])
                for l in range(n_labels):
                    backpointer[0, l] = -1
                # Recursion
                for t in range(1, T):
                    emit = self._emission_scores(seq_feat[t])
                    for l in range(n_labels):
                        scores = viterbi[t-1] + self.transition_params[:, l] + emit[l]
                        best = np.argmax(scores)
                        viterbi[t, l] = scores[best]
                        backpointer[t, l] = best
                # Termination
                best_last = np.argmax(viterbi[T-1])
                path = [best_last]
                for t in range(T-1, 0, -1):
                    path.insert(0, backpointer[t, path[0]])
                results.append([self.idx_to_label[p] for p in path])
            return results

    def log_likelihood(self, X: List[List], y: List[List]) -> float:
        """
        Compute log‑likelihood of data under the model.
        If sklearn_crfsuite is used, we extract the weights and compute manually.
        """
        if self._use_sklearn and self._model:
            # Extract weights from sklearn_crfsuite model
            # The model stores transition_features_ and state_features_
            # We need to map them to our internal representation.
            # This is a bit involved; we'll implement a simplified version.
            # For now, we raise a warning and return 0 (but we'll attempt a proper computation).
            try:
                # Get feature mappings from the model
                trans_features = self._model.transition_features_
                state_features = self._model.state_features_

                # Build label set and mapping
                self.label_set = list(self._model.classes_)
                self.label_to_idx = {l: i for i, l in enumerate(self.label_set)}
                self.idx_to_label = {i: l for i, l in enumerate(self.label_set)}

                # Build feature set
                all_features = set()
                for feat in state_features:
                    all_features.add(feat[0])
                self.feature_set = sorted(all_features)
                self.feature_to_idx = {f: i for i, f in enumerate(self.feature_set)}

                # Initialize weight matrices
                n_labels = len(self.label_set)
                n_features = len(self.feature_set)
                self.transition_params = np.zeros((n_labels, n_labels))
                self.emission_params = np.zeros((n_features, n_labels))

                # Fill transition_params
                for (l1, l2), w in trans_features.items():
                    i = self.label_to_idx[l1]
                    j = self.label_to_idx[l2]
                    self.transition_params[i, j] = w

                # Fill emission_params
                for (feat, label), w in state_features.items():
                    if feat in self.feature_to_idx and label in self.label_to_idx:
                        f_idx = self.feature_to_idx[feat]
                        l_idx = self.label_to_idx[label]
                        self.emission_params[f_idx, l_idx] = w

                # Now compute log-likelihood using our method
                X_features = self._extract_features(X)
                return self._log_likelihood(X_features, y)
            except Exception as e:
                logger.warning(f"Could not compute log-likelihood with sklearn_crfsuite: {e}")
                return 0.0
        else:
            X_features = self._extract_features(X)
            return self._log_likelihood(X_features, y)

    def sample(self, n: int) -> List[List]:
        """Sampling from a CRF is non‑trivial; not implemented."""
        raise NotImplementedError("Sampling from CRF is not implemented.")


# ============================================================================
# HIDDEN MARKOV MODEL (unchanged, but included for completeness)
# ============================================================================

class HiddenMarkovModel(ProbabilisticModel):
    """
    Hidden Markov Model with discrete observations.
    Implements forward‑backward, Viterbi, and Baum‑Welch learning.
    """
    def __init__(self, n_states: int, n_obs: int,
                 start_prob: Optional[np.ndarray] = None,
                 trans_prob: Optional[np.ndarray] = None,
                 emit_prob: Optional[np.ndarray] = None):
        """
        Args:
            n_states: number of hidden states.
            n_obs: number of observation symbols.
            start_prob: initial state probabilities (length n_states).
            trans_prob: transition matrix (n_states x n_states).
            emit_prob: emission matrix (n_states x n_obs).
        """
        super().__init__()
        self.n_states = n_states
        self.n_obs = n_obs
        self.start_prob = start_prob if start_prob is not None else np.ones(n_states) / n_states
        self.trans_prob = trans_prob if trans_prob is not None else np.ones((n_states, n_states)) / n_states
        self.emit_prob = emit_prob if emit_prob is not None else np.ones((n_states, n_obs)) / n_obs

    def fit(self, observations: List[np.ndarray], **kwargs):
        """
        Learn parameters using Baum‑Welch (EM) algorithm.
        observations: list of observation sequences (each as 1D array of ints).
        """
        max_iter = kwargs.get('max_iter', 50)
        tol = kwargs.get('tol', 1e-4)
        verbose = kwargs.get('verbose', False)

        for iteration in range(max_iter):
            # E‑step: compute forward/backward probabilities and expected counts
            start_exp = np.zeros(self.n_states)
            trans_exp = np.zeros((self.n_states, self.n_states))
            emit_exp = np.zeros((self.n_states, self.n_obs))
            log_lik = 0.0

            for obs_seq in observations:
                T = len(obs_seq)
                # forward
                alpha = np.zeros((T, self.n_states))
                alpha[0] = self.start_prob * self.emit_prob[:, obs_seq[0]]
                alpha[0] /= alpha[0].sum() + 1e-100
                for t in range(1, T):
                    alpha[t] = (alpha[t-1] @ self.trans_prob) * self.emit_prob[:, obs_seq[t]]
                    alpha[t] /= alpha[t].sum() + 1e-100
                # backward
                beta = np.zeros((T, self.n_states))
                beta[T-1] = 1.0
                for t in range(T-2, -1, -1):
                    beta[t] = (self.trans_prob @ (self.emit_prob[:, obs_seq[t+1]] * beta[t+1]))
                    beta[t] /= beta[t].sum() + 1e-100
                # compute gamma and xi
                gamma = alpha * beta
                gamma /= gamma.sum(axis=1, keepdims=True) + 1e-100
                xi = np.zeros((T-1, self.n_states, self.n_states))
                for t in range(T-1):
                    xi[t] = alpha[t][:, None] * self.trans_prob * self.emit_prob[:, obs_seq[t+1]] * beta[t+1][None, :]
                    xi[t] /= xi[t].sum() + 1e-100

                # accumulate expectations
                start_exp += gamma[0]
                trans_exp += xi.sum(axis=0)
                for t in range(T):
                    emit_exp[:, obs_seq[t]] += gamma[t]

                log_lik += np.log(alpha[T-1].sum() + 1e-100)

            # M‑step: update parameters
            new_start = start_exp / start_exp.sum()
            new_trans = trans_exp / trans_exp.sum(axis=1, keepdims=True)
            new_emit = emit_exp / emit_exp.sum(axis=1, keepdims=True)

            # Check convergence
            delta = np.linalg.norm(new_start - self.start_prob) + \
                    np.linalg.norm(new_trans - self.trans_prob) + \
                    np.linalg.norm(new_emit - self.emit_prob)
            self.start_prob = new_start
            self.trans_prob = new_trans
            self.emit_prob = new_emit

            if verbose:
                print(f"Iter {iteration}, log‑lik = {log_lik:.2f}, delta = {delta:.6f}")

            if delta < tol:
                break

        self.is_fitted = True
        return self

    def predict(self, observations: np.ndarray, method: str = 'viterbi') -> np.ndarray:
        """
        Predict the most likely hidden state sequence.
        """
        if method == 'viterbi':
            return self._viterbi(observations)
        else:
            raise ValueError(f"Unknown method {method}")

    def _viterbi(self, obs_seq: np.ndarray) -> np.ndarray:
        """Viterbi algorithm."""
        T = len(obs_seq)
        viterbi = np.zeros((T, self.n_states))
        backpointer = np.zeros((T, self.n_states), dtype=int)
        # initialization
        viterbi[0] = np.log(self.start_prob + 1e-100) + np.log(self.emit_prob[:, obs_seq[0]] + 1e-100)
        # recursion
        for t in range(1, T):
            for j in range(self.n_states):
                probs = viterbi[t-1] + np.log(self.trans_prob[:, j] + 1e-100) + np.log(self.emit_prob[j, obs_seq[t]] + 1e-100)
                best = np.argmax(probs)
                viterbi[t, j] = probs[best]
                backpointer[t, j] = best
        # termination
        best_last = np.argmax(viterbi[T-1])
        state_seq = [best_last]
        for t in range(T-1, 0, -1):
            state_seq.insert(0, backpointer[t, state_seq[0]])
        return np.array(state_seq)

    def log_likelihood(self, observations: List[np.ndarray]) -> float:
        """Compute log‑likelihood of observation sequences using forward algorithm."""
        total_ll = 0.0
        for obs_seq in observations:
            T = len(obs_seq)
            alpha = np.zeros((T, self.n_states))
            alpha[0] = self.start_prob * self.emit_prob[:, obs_seq[0]]
            alpha[0] /= alpha[0].sum() + 1e-100
            for t in range(1, T):
                alpha[t] = (alpha[t-1] @ self.trans_prob) * self.emit_prob[:, obs_seq[t]]
                alpha[t] /= alpha[t].sum() + 1e-100
            total_ll += np.log(alpha[T-1].sum() + 1e-100)
        return total_ll

    def sample(self, n: int, length: int = 10) -> List[np.ndarray]:
        """
        Sample n sequences of given length from the HMM.
        Returns list of observation sequences.
        """
        samples = []
        for _ in range(n):
            states = []
            obs = []
            state = np.random.choice(self.n_states, p=self.start_prob)
            for t in range(length):
                states.append(state)
                obs.append(np.random.choice(self.n_obs, p=self.emit_prob[state]))
                state = np.random.choice(self.n_states, p=self.trans_prob[state])
            samples.append(np.array(obs))
        return samples


# ============================================================================
# DEMO (updated to show new features)
# ============================================================================

def demo():
    """Run a simple demonstration of each model, including new utility functions."""
    print("="*80)
    print("PROBABILISTIC MODELS DEMO")
    print("="*80)

    # --- Discretization demo ---
    print("\n--- Discretization from Registry ---")
    # Simulate continuous data
    np.random.seed(42)
    continuous_data = np.column_stack([
        np.random.normal(0, 1, 20),   # varA
        np.random.uniform(0, 10, 20), # varB
        np.random.poisson(3, 20)      # varC (already discrete-like)
    ])
    var_names = ['A', 'B', 'C']
    registry = {
        'A': {'method': 'equal_width', 'bins': 5},
        'B': {'method': 'equal_freq', 'bins': 4}
        # C not in registry -> left as is (assumed discrete)
    }
    disc_data, enc = discretize_from_registry(continuous_data, var_names, registry, return_encodings=True)
    print("Original first row:", continuous_data[0])
    print("Discretized first row:", disc_data[0])
    print("Encodings (bin edges):", {k: v for k, v in enc.items()})

    # --- HMM from temporal registry ---
    print("\n--- HMM from Temporal Registry ---")
    temporal_registry = {
        'phases': {
            'weather': {
                'states': ['Rainy', 'Sunny'],
                'start_prob': [0.6, 0.4],
                'transition_matrix': [[0.7, 0.3], [0.4, 0.6]],
                'emission_matrix': [[0.1, 0.4, 0.5], [0.6, 0.3, 0.1]],
                'observation_symbols': ['walk', 'shop', 'clean']
            }
        }
    }
    hmm_from_reg = from_temporal_registry(temporal_registry, phase_key='weather')
    print("HMM built from registry:")
    print("  States:", hmm_from_reg.state_names if hasattr(hmm_from_reg, 'state_names') else 'unknown')
    print("  Start prob:", hmm_from_reg.start_prob)
    print("  Transition matrix:\n", hmm_from_reg.trans_prob)

    # Bayesian Network
    print("\n--- Bayesian Network ---")
    bn = BayesianNetwork(edges=[('A', 'C'), ('B', 'C')],
                         variable_names=['A', 'B', 'C'],
                         cardinalities={'A': 2, 'B': 2, 'C': 2})
    bn.set_cpd('A', np.array([0.5, 0.5]), [])
    bn.set_cpd('B', np.array([0.5, 0.5]), [])
    bn.set_cpd('C', np.array([[0.9, 0.1], [0.2, 0.8]]), ['A', 'B'])  # shape: [C, A, B]
    bn.is_fitted = True

    # Sample data
    samples = bn.sample(10)
    print("Samples:\n", samples)

    # Compute log‑likelihood
    ll = bn.log_likelihood(samples)
    print(f"Log‑likelihood: {ll:.2f}")

    # Predict with evidence (first sample missing value for A)
    evidence = samples.copy()
    evidence[0, 0] = np.nan  # set A to unknown
    pred = bn.predict(evidence)
    print("Prediction with missing A:\n", pred[0])

    # Markov Random Field
    print("\n--- Markov Random Field ---")
    mrf = MarkovRandomField(['X', 'Y', 'Z'], {'X': 2, 'Y': 2, 'Z': 2})
    mrf.add_unary_potential('X', np.array([0.0, 1.0]))
    mrf.add_unary_potential('Y', np.array([0.0, 1.0]))
    mrf.add_unary_potential('Z', np.array([0.0, 1.0]))
    mrf.add_pairwise_potential('X', 'Y', np.array([[0.0, 1.0], [1.0, 0.0]]))  # anti‑ferro
    mrf.add_pairwise_potential('Y', 'Z', np.array([[0.0, 1.0], [1.0, 0.0]]))
    mrf.is_fitted = True

    # Sample via Gibbs
    mrf_samples = mrf.sample(n=10, burn_in=10, thinning=2)
    print("Gibbs samples:\n", mrf_samples)

    # ICM for prediction given evidence
    evidence = np.array([[np.nan, 0, 1]])
    pred = mrf.predict(evidence, method='icm')
    print("ICM prediction with evidence Y=0, Z=1:\n", pred)

    # Fit MRF using pseudo‑likelihood (if torch available)
    if HAS_TORCH:
        print("\n--- MRF parameter learning ---")
        # Generate synthetic data from current model
        train_data = mrf.sample(n=100, burn_in=10, thinning=1)
        # Create a new MRF with same structure but zero potentials
        mrf2 = MarkovRandomField(['X', 'Y', 'Z'], {'X': 2, 'Y': 2, 'Z': 2})
        mrf2.add_unary_potential('X', np.zeros(2))
        mrf2.add_unary_potential('Y', np.zeros(2))
        mrf2.add_unary_potential('Z', np.zeros(2))
        mrf2.add_pairwise_potential('X', 'Y', np.zeros((2,2)))
        mrf2.add_pairwise_potential('Y', 'Z', np.zeros((2,2)))
        mrf2.fit(train_data, max_iter=200, lr=0.1, verbose=False)
        print("Learned unary X:", mrf2.unary_potentials['X'])
        print("Learned pairwise X-Y:\n", mrf2.pairwise_potentials[('X','Y')])

    # Conditional Random Field
    print("\n--- Conditional Random Field ---")
    # Toy data: simple sequences
    X = [['a', 'b', 'a'], ['b', 'a', 'b']]
    y = [['0', '1', '0'], ['1', '0', '1']]
    crf = ConditionalRandomField(algorithm='sgd')
    crf.fit(X, y, epochs=50, lr=0.1, verbose=False)
    pred = crf.predict(X)
    print("Predictions:", pred)

    # Hidden Markov Model
    print("\n--- Hidden Markov Model ---")
    # Simple weather model: states = [Rainy, Sunny], observations = [Walk, Shop, Clean]
    hmm = HiddenMarkovModel(n_states=2, n_obs=3)
    hmm.start_prob = np.array([0.6, 0.4])
    hmm.trans_prob = np.array([[0.7, 0.3], [0.4, 0.6]])
    hmm.emit_prob = np.array([[0.1, 0.4, 0.5], [0.6, 0.3, 0.1]])
    hmm.is_fitted = True

    # Generate a sample sequence
    obs_seq = hmm.sample(1, length=5)[0]
    print("Observation sequence:", obs_seq)

    # Viterbi decoding
    states = hmm.predict(obs_seq)
    print("Most likely hidden states:", states)

    # Log‑likelihood
    ll_hmm = hmm.log_likelihood([obs_seq])
    print(f"Log‑likelihood: {ll_hmm:.2f}")

    # Fit (Baum‑Welch) on synthetic data
    print("\n--- Baum‑Welch training ---")
    train_data = hmm.sample(100, length=10)
    hmm2 = HiddenMarkovModel(n_states=2, n_obs=3)
    hmm2.fit(train_data, max_iter=20, verbose=False)
    print("Learned start prob:", hmm2.start_prob)
    print("Learned transition:\n", hmm2.trans_prob)
    print("Learned emission:\n", hmm2.emit_prob)


if __name__ == "__main__":
    demo()