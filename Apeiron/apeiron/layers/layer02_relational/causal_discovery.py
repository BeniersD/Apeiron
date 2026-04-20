"""
CAUSAL DISCOVERY – ULTIMATE IMPLEMENTATION
===========================================
This module provides advanced causal discovery and inference algorithms,
including constraint‑based, score‑based, and functional causal models.
It integrates with Layer 2's relational structures (UltimateRelation, etc.)
and can output causal graphs as NetworkX DiGraphs.

Algorithms covered (all optional, depending on installed libraries):
- PC, FCI, RFCI (causal‑learn)
- GES, FGES (causal‑learn)
- LiNGAM, DirectLiNGAM, VARLiNGAM (lingam)
- CAM (causal‑learn)
- NOTEARS (custom or from causal‑learn)
- CDNOD (causal‑learn)
- GIN (causal‑learn)
- ICALiNGAM (lingam)
- Causal inference: do‑calculus, counterfactuals, refutation (dowhy)

**NIEUWE UITBREIDINGEN (v5.2):**
- Classmethod `from_layer1_registry`: bouwt een datamatrix uit `qualitative_dims`
  van Layer 1 observables, en gebruikt `temporal_phase` voor tijdsvolgorde.
- `ingest_causal_graph`: zet een gevonden causale graaf om naar UltimateRelation‑objecten
  in een Layer 2‑instantie.
- `prior_from_atomicity`: genereert een prior‑matrix op basis van atomiciteitsscores
  om als voorkennis mee te geven aan algoritmen (bv. NOTEARS).

All classes and functions degrade gracefully if required libraries are missing.
"""

import logging
import numpy as np
from typing import Optional, List, Dict, Any, Tuple, Union, Callable
from collections import defaultdict

# ============================================================================
# OPTIONAL LIBRARIES – ALL HANDLED GRACEFULLY
# ============================================================================

# NetworkX for graph representation
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

# causal‑learn for most algorithms
try:
    from causallearn.search.ConstraintBased.PC import pc
    from causallearn.search.ConstraintBased.FCI import fci
    from causallearn.search.ConstraintBased.RFCI import rfci
    from causallearn.search.ConstraintBased.CDNOD import cdnod
    from causallearn.search.ScoreBased.GES import ges
    from causallearn.search.FCMBased import lingam as cl_lingam
    from causallearn.search.FCMBased.CAM import cam
    from causallearn.search.FCMBased.GIN import gin
    from causallearn.utils.GraphUtils import GraphUtils
    HAS_CAUSALLEARN = True
except ImportError:
    HAS_CAUSALLEARN = False

# lingam package (separate)
try:
    import lingam
    from lingam import DirectLiNGAM, ICALiNGAM, VARLiNGAM, BottomUpParceLiNGAM
    HAS_LINGAM = True
except ImportError:
    HAS_LINGAM = False

# NOTEARS (custom package)
try:
    import notears
    from notears.linear import notears_linear
    from notears.nonlinear import notears_nonlinear
    HAS_NOTEARS = True
except ImportError:
    HAS_NOTEARS = False

# DoWhy for causal inference
try:
    import dowhy
    from dowhy import CausalModel
    HAS_DOWHY = True
except ImportError:
    HAS_DOWHY = False

# Statsmodels for Granger causality
try:
    from statsmodels.tsa.stattools import grangercausalitytests
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _to_networkx(graph: Any, var_names: Optional[List[str]] = None) -> nx.DiGraph:
    """
    Convert a causal‑learn graph or adjacency matrix to a NetworkX DiGraph.
    """
    if not HAS_NETWORKX:
        raise ImportError("NetworkX required for graph conversion")
    G = nx.DiGraph()
    if var_names:
        G.add_nodes_from(var_names)
    else:
        G.add_nodes_from(range(graph.get_num_nodes())) if hasattr(graph, 'get_num_nodes') else G.add_nodes_from(range(len(graph)))

    if hasattr(graph, 'get_graph_edges'):
        # causal‑learn GeneralGraph
        for (i, j, _type) in graph.get_graph_edges():
            # _type: -1 directed i->j, 1 directed j->i, 0 undirected, etc.
            if _type == -1:
                src = var_names[i] if var_names else i
                tgt = var_names[j] if var_names else j
                G.add_edge(src, tgt)
            elif _type == 1:
                src = var_names[j] if var_names else j
                tgt = var_names[i] if var_names else i
                G.add_edge(src, tgt)
    elif isinstance(graph, np.ndarray):
        # adjacency matrix
        n = graph.shape[0]
        for i in range(n):
            for j in range(n):
                if graph[i, j] != 0:
                    src = var_names[i] if var_names else i
                    tgt = var_names[j] if var_names else j
                    G.add_edge(src, tgt)
    elif isinstance(graph, nx.DiGraph):
        G = graph
    return G


def _from_dataframe(df, var_names=None):
    """Convert pandas DataFrame to numpy array, extracting variable names."""
    import pandas as pd
    if isinstance(df, pd.DataFrame):
        data = df.values
        if var_names is None:
            var_names = list(df.columns)
        return data, var_names
    return df, var_names


# ============================================================================
# BASE CLASS
# ============================================================================

class CausalDiscovery:
    """
    Comprehensive causal discovery and inference class.
    Encapsulates data and variable names, and provides methods for various algorithms.
    """
    def __init__(self, data: np.ndarray, variable_names: Optional[List[str]] = None):
        """
        Args:
            data: n_samples × n_variables matrix.
            variable_names: list of variable names (optional).
        """
        self.data = data
        self.n_samples, self.n_vars = data.shape
        self.variable_names = variable_names or [f"X{i}" for i in range(self.n_vars)]
        self._graph = None  # last learned graph

    # ------------------------------------------------------------------------
    # Constraint‑based methods
    # ------------------------------------------------------------------------

    def pc(self, alpha: float = 0.05, indep_test: str = 'fisherz', **kwargs) -> nx.DiGraph:
        """
        PC algorithm (Peter‑Clark) for causal discovery.
        Returns a CPDAG (completed partially directed acyclic graph) as NetworkX DiGraph.
        """
        if not HAS_CAUSALLEARN:
            raise ImportError("causal‑learn is required for PC")
        from causallearn.search.ConstraintBased.PC import pc
        cg = pc(self.data, alpha, indep_test, **kwargs)
        self._graph = _to_networkx(cg.G, self.variable_names)
        return self._graph

    def fci(self, alpha: float = 0.05, indep_test: str = 'fisherz', **kwargs) -> nx.DiGraph:
        """
        Fast Causal Inference (FCI) algorithm – handles latent confounders.
        Returns a PAG (partial ancestral graph) as NetworkX DiGraph (edges with possible endpoints).
        """
        if not HAS_CAUSALLEARN:
            raise ImportError("causal‑learn is required for FCI")
        from causallearn.search.ConstraintBased.FCI import fci
        G, edges = fci(self.data, alpha, indep_test, **kwargs)
        self._graph = _to_networkx(G, self.variable_names)
        return self._graph

    def rfci(self, alpha: float = 0.05, indep_test: str = 'fisherz', **kwargs) -> nx.DiGraph:
        """RFCI – a faster version of FCI."""
        if not HAS_CAUSALLEARN:
            raise ImportError("causal‑learn is required for RFCI")
        from causallearn.search.ConstraintBased.RFCI import rfci
        G = rfci(self.data, alpha, indep_test, **kwargs)
        self._graph = _to_networkx(G, self.variable_names)
        return self._graph

    def cdnod(self, alpha: float = 0.05, indep_test: str = 'fisherz', c_indep_test: str = 'fisherz',
              background_knowledge=None, **kwargs) -> nx.DiGraph:
        """
        CDNOD (Causal Discovery from Nonstationary/heterogeneous Data).
        Requires additional information about data heterogeneity.
        """
        if not HAS_CAUSALLEARN:
            raise ImportError("causal‑learn is required for CDNOD")
        from causallearn.search.ConstraintBased.CDNOD import cdnod
        # cdnod requires C (index of domain variable) – we assume user provides it in kwargs
        C = kwargs.pop('C', None)
        if C is None:
            raise ValueError("CDNOD requires the index of the domain variable (C)")
        cg = cdnod(self.data, C, alpha, indep_test, c_indep_test, background_knowledge, **kwargs)
        self._graph = _to_networkx(cg.G, self.variable_names)
        return self._graph

    # ------------------------------------------------------------------------
    # Score‑based methods
    # ------------------------------------------------------------------------

    def ges(self, score_func: str = 'local_score_BIC', maxP: int = None,
            parameters: Optional[Dict] = None) -> nx.DiGraph:
        """
        Greedy Equivalence Search (GES).
        Returns a CPDAG.
        """
        if not HAS_CAUSALLEARN:
            raise ImportError("causal‑learn is required for GES")
        from causallearn.search.ScoreBased.GES import ges
        Record = ges(self.data, score_func, maxP, parameters)
        graph = Record['G'] if isinstance(Record, dict) else Record[0]
        self._graph = _to_networkx(graph, self.variable_names)
        return self._graph

    # ------------------------------------------------------------------------
    # Functional causal models
    # ------------------------------------------------------------------------

    def cam(self, score_func: str = 'r2', alpha: float = 0.05,
            cutoff: int = 3, numB: int = 100, use_sklearn: bool = True) -> nx.DiGraph:
        """
        Causal Additive Models (CAM).
        """
        if not HAS_CAUSALLEARN:
            raise ImportError("causal‑learn is required for CAM")
        from causallearn.search.FCMBased.CAM import cam
        graph = cam(self.data, score_func, alpha, cutoff, numB, use_sklearn)
        self._graph = _to_networkx(graph, self.variable_names)
        return self._graph

    def gin(self, indep_test: str = 'kernel', alpha: float = 0.05, **kwargs) -> nx.DiGraph:
        """
        GIN (Generalized Independent Noise) condition for causal discovery.
        """
        if not HAS_CAUSALLEARN:
            raise ImportError("causal‑learn is required for GIN")
        from causallearn.search.FCMBased.GIN import gin
        graph = gin(self.data, indep_test, alpha, **kwargs)
        self._graph = _to_networkx(graph, self.variable_names)
        return self._graph

    # ------------------------------------------------------------------------
    # LiNGAM family (lingam package)
    # ------------------------------------------------------------------------

    def lingam(self, method: str = 'ICALiNGAM', **kwargs) -> nx.DiGraph:
        """
        Linear Non‑Gaussian Acyclic Model (LiNGAM) and variants.
        Methods: 'ICALiNGAM', 'DirectLiNGAM', 'VARLiNGAM', 'BottomUpParceLiNGAM'.
        """
        if not HAS_LINGAM:
            raise ImportError("lingam package is required for LiNGAM")
        if method == 'ICALiNGAM':
            model = lingam.ICALiNGAM(**kwargs)
        elif method == 'DirectLiNGAM':
            model = lingam.DirectLiNGAM(**kwargs)
        elif method == 'VARLiNGAM':
            model = lingam.VARLiNGAM(**kwargs)
        elif method == 'BottomUpParceLiNGAM':
            model = lingam.BottomUpParceLiNGAM(**kwargs)
        else:
            raise ValueError(f"Unknown LiNGAM method: {method}")
        model.fit(self.data)
        # Adjacency matrix B where B[i,j] is effect of j on i (i <- j)
        # We transpose to get cause -> effect
        adj = model.adjacency_matrix_.T
        self._graph = _to_networkx(adj, self.variable_names)
        return self._graph

    # ------------------------------------------------------------------------
    # NOTEARS (continuous optimization)
    # ------------------------------------------------------------------------

    def notears(self, lambda1: float = 0.1, loss_type: str = 'l2', max_iter: int = 100,
                h_tol: float = 1e-8, rho_max: float = 1e+16, w_threshold: float = 0.3,
                nonlinear: bool = False, prior_matrix: Optional[np.ndarray] = None, **kwargs) -> nx.DiGraph:
        """
        NOTEARS algorithm (Non‑combinatorial Optimization via Trace Exponential and
        Augmented Lagrange for Structure learning). Uses the original `notears` package
        if available, otherwise falls back to a simple thresholded correlation matrix.

        Args:
            prior_matrix: Optional matrix of shape (n_vars, n_vars) giving prior weights
                          for each directed edge. Used by the notears package if supported.
        """
        if HAS_NOTEARS and not nonlinear:
            from notears.linear import notears_linear
            W_est = notears_linear(self.data, lambda1=lambda1, loss_type=loss_type,
                                    max_iter=max_iter, h_tol=h_tol, rho_max=rho_max,
                                    w_threshold=w_threshold, W_prior=prior_matrix, **kwargs)
            adj = (np.abs(W_est) > w_threshold).astype(float)
        elif HAS_NOTEARS and nonlinear:
            from notears.nonlinear import notears_nonlinear
            W_est = notears_nonlinear(self.data, lambda1=lambda1, **kwargs)
            adj = (np.abs(W_est) > w_threshold).astype(float)
        else:
            logger.warning("NOTEARS package not installed; using thresholded correlation matrix as fallback.")
            corr = np.corrcoef(self.data.T)
            adj = (np.abs(corr) > 0.5) & (np.abs(corr) < 1.0)
            np.fill_diagonal(adj, 0)
            adj = adj.astype(float)
        self._graph = _to_networkx(adj, self.variable_names)
        return self._graph

    # ------------------------------------------------------------------------
    # Granger causality (for time series)
    # ------------------------------------------------------------------------

    def granger_causality(self, idx_i: int, idx_j: int, max_lag: int = 5) -> Dict[str, float]:
        """
        Test if variable i Granger‑causes variable j.
        Returns F‑statistic and p‑value for the best lag.
        """
        if not HAS_STATSMODELS:
            raise ImportError("statsmodels required for Granger causality")
        data = np.column_stack([self.data[:, idx_j], self.data[:, idx_i]])  # test i -> j
        result = grangercausalitytests(data, max_lag, verbose=False)
        best_p = 1.0
        best_f = 0.0
        for lag in result:
            p = result[lag][0]['ssr_ftest'][1]
            if p < best_p:
                best_p = p
                best_f = result[lag][0]['ssr_ftest'][0]
        return {'f_stat': best_f, 'p_value': best_p}

    # ------------------------------------------------------------------------
    # Causal inference with DoWhy (fully implemented)
    # ------------------------------------------------------------------------

    def estimate_effect(self, treatment: str, outcome: str, graph: nx.DiGraph,
                        method: str = 'backdoor.linear_regression',
                        target_units: str = 'ate', **kwargs) -> float:
        """
        Estimate causal effect using DoWhy.

        Args:
            treatment: name of treatment variable.
            outcome: name of outcome variable.
            graph: causal graph (NetworkX DiGraph) representing the assumed structure.
            method: estimation method (e.g., 'backdoor.linear_regression',
                    'backdoor.distance_matching', 'iv.instrumental_variable', etc.)
            target_units: 'ate' (average treatment effect), 'att' (average treatment on treated), etc.
            **kwargs: additional arguments passed to the estimation method.

        Returns:
            Estimated effect value.

        Raises:
            ImportError: if DoWhy is not installed.
        """
        if not HAS_DOWHY:
            raise ImportError("DoWhy is required for causal effect estimation")

        import pandas as pd
        df = pd.DataFrame(self.data, columns=self.variable_names)

        # Create causal model
        model = CausalModel(
            data=df,
            treatment=treatment,
            outcome=outcome,
            graph=graph  # DoWhy accepts NetworkX graphs
        )

        # Identify the effect
        identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)

        # Estimate
        estimate = model.estimate_effect(identified_estimand,
                                         method_name=method,
                                         target_units=target_units,
                                         **kwargs)

        return estimate.value

    def counterfactual(self, treatment: str, outcome: str, graph: nx.DiGraph,
                       treatment_value: float, **kwargs) -> np.ndarray:
        """
        Compute counterfactual outcomes if treatment were set to treatment_value for all units.

        Args:
            treatment: name of treatment variable.
            outcome: name of outcome variable.
            graph: causal graph (NetworkX DiGraph).
            treatment_value: value to set the treatment to.
            **kwargs: additional arguments (e.g., method for estimation).

        Returns:
            Array of counterfactual outcomes for each sample (length = n_samples).

        Raises:
            ImportError: if DoWhy is not installed.
        """
        if not HAS_DOWHY:
            raise ImportError("DoWhy is required for counterfactual computation")

        import pandas as pd
        df = pd.DataFrame(self.data, columns=self.variable_names)

        # Create causal model
        model = CausalModel(
            data=df,
            treatment=treatment,
            outcome=outcome,
            graph=graph
        )

        # Identify the causal effect (required for counterfactual)
        identified_estimand = model.identify_effect()

        # Use DoWhy's counterfactual method (available in recent versions)
        # This returns a DataFrame with the original data and a new column for the counterfactual outcome.
        cf = model.counterfactual(
            treatment_values={treatment: treatment_value},
            method_name=kwargs.get('method', 'backdoor.linear_regression'),
            **kwargs
        )

        # The counterfactual outcome is typically stored in a column named after the outcome with a suffix.
        # We'll try to extract it.
        cf_col = f"{outcome}_cf"
        if cf_col in cf.columns:
            return cf[cf_col].values
        else:
            # Fallback: assume it's the last added column
            return cf.iloc[:, -1].values

    def refute_estimate(self, treatment: str, outcome: str, graph: nx.DiGraph,
                        method: str = 'backdoor.linear_regression',
                        refutation_method: str = 'random_common_cause',
                        **kwargs) -> Dict[str, Any]:
        """
        Perform a refutation test on an estimated causal effect using DoWhy.

        Args:
            treatment: name of treatment variable.
            outcome: name of outcome variable.
            graph: causal graph.
            method: estimation method.
            refutation_method: 'random_common_cause', 'placebo_treatment',
                               'data_subset_refuter', 'bootstrap_refuter', etc.
            **kwargs: additional arguments for the refuter.

        Returns:
            Dictionary with refutation results, including the new estimate and p-value.

        Raises:
            ImportError: if DoWhy is not installed.
        """
        if not HAS_DOWHY:
            raise ImportError("DoWhy is required for refutation")

        import pandas as pd
        df = pd.DataFrame(self.data, columns=self.variable_names)

        model = CausalModel(data=df, treatment=treatment, outcome=outcome, graph=graph)
        identified_estimand = model.identify_effect()
        estimate = model.estimate_effect(identified_estimand, method_name=method)

        # Choose refuter
        if refutation_method == 'random_common_cause':
            refuter = model.refute_estimate(identified_estimand, estimate,
                                            method_name="random_common_cause", **kwargs)
        elif refutation_method == 'placebo_treatment':
            refuter = model.refute_estimate(identified_estimand, estimate,
                                            method_name="placebo_treatment", **kwargs)
        elif refutation_method == 'data_subset_refuter':
            refuter = model.refute_estimate(identified_estimand, estimate,
                                            method_name="data_subset_refuter", **kwargs)
        elif refutation_method == 'bootstrap_refuter':
            refuter = model.refute_estimate(identified_estimand, estimate,
                                            method_name="bootstrap_refuter", **kwargs)
        else:
            raise ValueError(f"Unknown refutation method: {refutation_method}")

        # Return relevant info
        return {
            'refutation_method': refutation_method,
            'new_estimate': refuter.new_effect,
            'p_value': refuter.p_value,
            'original_estimate': estimate.value
        }

    # ------------------------------------------------------------------------
    # NEW: Build from Layer 1 registry
    # ------------------------------------------------------------------------

    @classmethod
    def from_layer1_registry(cls, registry: Dict[str, Any],
                             feature_source: str = 'qualitative_dims',
                             use_phase: bool = False,
                             phase_key: str = 'temporal_phase') -> 'CausalDiscovery':
        """
        Create a CausalDiscovery instance from a Layer 1 observable registry.

        Extracts feature vectors from each observable using the specified source
        (e.g., 'qualitative_dims', 'relational_embedding', or a callable).
        If `use_phase` is True, the rows are ordered by `temporal_phase` (ascending).
        The variable names become the observable IDs.

        Args:
            registry: dict mapping observable ID to observable object.
            feature_source: either a string ('qualitative_dims', 'relational_embedding')
                            or a callable that takes an observable and returns a 1D array.
            use_phase: if True, sort observables by `temporal_phase`.
            phase_key: attribute name for the temporal phase.

        Returns:
            A CausalDiscovery instance with data matrix and variable names.

        Raises:
            ValueError: if no features can be extracted.
        """
        ids = list(registry.keys())
        features = []
        valid_ids = []
        for obs_id in ids:
            obs = registry[obs_id]
            if feature_source == 'qualitative_dims' and hasattr(obs, 'qualitative_dims'):
                feat = list(obs.qualitative_dims.values())
            elif feature_source == 'relational_embedding' and hasattr(obs, 'relational_embedding'):
                emb = obs.relational_embedding
                if isinstance(emb, (list, np.ndarray)):
                    feat = emb if isinstance(emb, list) else emb.tolist()
                else:
                    continue
            elif callable(feature_source):
                feat = feature_source(obs)
                if feat is None:
                    continue
            else:
                continue
            features.append(feat)
            valid_ids.append(obs_id)

        if not features:
            raise ValueError("No features could be extracted from the registry.")

        data = np.array(features)
        n = data.shape[0]
        if data.ndim == 1:
            data = data.reshape(n, 1)

        # Sort by temporal phase if requested
        if use_phase:
            phases = []
            for obs_id in valid_ids:
                obs = registry[obs_id]
                phase = getattr(obs, phase_key, float('inf'))
                phases.append(phase)
            sort_idx = np.argsort(phases)
            data = data[sort_idx, :]
            valid_ids = [valid_ids[i] for i in sort_idx]

        return cls(data, variable_names=valid_ids)

    # ------------------------------------------------------------------------
    # NEW: Prior from atomicity
    # ------------------------------------------------------------------------

    def prior_from_atomicity(self, atomicity_scores: Dict[str, float],
                             inverse_temp: float = 1.0,
                             symmetric: bool = False) -> np.ndarray:
        """
        Generate a prior matrix for causal discovery based on atomicity scores.

        The idea: variables with higher atomicity are more fundamental and thus
        more likely to be causes than effects. This returns a matrix P of shape
        (n_vars, n_vars) where P[i, j] is the prior probability (or weight) that
        variable i causes variable j. If `symmetric` is True, returns an undirected
        prior (i.e., P[i,j] = P[j,i]).

        The prior is computed as:
            P[i,j] = sigmoid( inverse_temp * (atomicity_i - atomicity_j) )
        where atomicity_i is the score for variable i.

        Args:
            atomicity_scores: dict mapping variable name (as in self.variable_names) to score.
            inverse_temp: scaling factor for the sigmoid (higher means sharper distinction).
            symmetric: if True, return symmetric matrix (undirected prior).

        Returns:
            A numpy array of shape (n_vars, n_vars).
        """
        # Map variable names to indices
        idx_map = {name: i for i, name in enumerate(self.variable_names)}
        scores = np.zeros(self.n_vars)
        for name, score in atomicity_scores.items():
            if name in idx_map:
                scores[idx_map[name]] = score
            else:
                logger.warning(f"Variable {name} not in variable_names; ignoring atomicity score.")

        # Compute difference matrix
        diff = scores[:, None] - scores[None, :]  # i -> j: diff[i,j] = score_i - score_j
        # Sigmoid: 1 / (1 + exp(-x))
        prior = 1.0 / (1.0 + np.exp(-inverse_temp * diff))

        if symmetric:
            prior = (prior + prior.T) / 2

        # Zero out diagonal
        np.fill_diagonal(prior, 0.0)

        return prior

    # ------------------------------------------------------------------------
    # NEW: Ingest causal graph into Layer 2
    # ------------------------------------------------------------------------

    def ingest_causal_graph(self, layer2_instance: Any,
                            graph: Optional[nx.DiGraph] = None,
                            relation_type: str = 'causal',
                            weight_attribute: str = 'weight',
                            **kwargs) -> List[str]:
        """
        Convert a causal graph (NetworkX DiGraph) into UltimateRelation objects
        and add them to a Layer 2 instance. The graph's nodes must correspond to
        the variable names (observable IDs) used in this CausalDiscovery instance.

        If `graph` is None, uses the most recently learned graph (self._graph).

        Args:
            layer2_instance: An instance of Layer2_Relational_Ultimate (or any object
                             with a `create_relation` method).
            graph: The causal graph to ingest. If None, uses self._graph.
            relation_type: Type string to pass to `create_relation` (e.g., 'causal').
            weight_attribute: If edges have a weight attribute, use it as relation weight.
            **kwargs: Additional metadata passed to `create_relation`.

        Returns:
            List of created relation IDs.

        Raises:
            ValueError: if no graph is available.
        """
        if graph is None:
            if self._graph is None:
                raise ValueError("No graph available. Run a discovery method first or provide a graph.")
            graph = self._graph

        if not HAS_NETWORKX:
            raise ImportError("NetworkX required for graph ingestion")

        rel_ids = []
        for u, v, data in graph.edges(data=True):
            weight = data.get(weight_attribute, 1.0)
            # Ensure u and v are strings (observable IDs)
            u_str = str(u)
            v_str = str(v)
            # Create relation
            try:
                rel = layer2_instance.create_relation(
                    source_id=u_str,
                    target_id=v_str,
                    relation_type=relation_type,
                    weight=weight,
                    metadata={**kwargs, 'causal_edge': True}
                )
                rel_ids.append(rel.id)
            except Exception as e:
                logger.error(f"Failed to create relation from {u_str} to {v_str}: {e}")

        return rel_ids

    # ------------------------------------------------------------------------
    # Evaluation utilities (extended for multiple graphs)
    # ------------------------------------------------------------------------

    def evaluate(self, estimated_graph: nx.DiGraph, true_graph: nx.DiGraph) -> Dict[str, float]:
        """
        Compare estimated graph with true graph.
        Returns dictionary with metrics: SHD, precision, recall, F1, etc.
        """
        if not HAS_NETWORKX:
            raise ImportError("NetworkX required for evaluation")
        est_edges = set(estimated_graph.edges())
        true_edges = set(true_graph.edges())
        shd = len(est_edges.symmetric_difference(true_edges))

        # Skeleton metrics
        est_undirected = set((min(u, v), max(u, v)) for u, v in est_edges)
        true_undirected = set((min(u, v), max(u, v)) for u, v in true_edges)
        tp = len(est_undirected & true_undirected)
        fp = len(est_undirected - true_undirected)
        fn = len(true_undirected - est_undirected)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        # Directed metrics
        correct_oriented = len(est_edges & true_edges)
        dir_prec = correct_oriented / len(est_edges) if est_edges else 1.0
        dir_rec = correct_oriented / len(true_edges) if true_edges else 1.0
        dir_f1 = 2 * dir_prec * dir_rec / (dir_prec + dir_rec) if (dir_prec + dir_rec) > 0 else 0.0

        return {
            'shd': shd,
            'skeleton_precision': precision,
            'skeleton_recall': recall,
            'skeleton_f1': f1,
            'directed_precision': dir_prec,
            'directed_recall': dir_rec,
            'directed_f1': dir_f1,
            'tp_edges': tp,
            'fp_edges': fp,
            'fn_edges': fn,
            'est_edges_count': len(est_edges),
            'true_edges_count': len(true_edges)
        }

    def evaluate_multiple(self, estimated_graphs: List[nx.DiGraph],
                          true_graphs: List[nx.DiGraph]) -> Dict[str, List[float]]:
        """
        Evaluate a list of estimated graphs against a list of true graphs.
        Returns a dictionary of metric names mapped to lists of values (one per graph pair).
        If lengths differ, raises ValueError.
        """
        if len(estimated_graphs) != len(true_graphs):
            raise ValueError("Number of estimated and true graphs must match")
        results = defaultdict(list)
        for est, true in zip(estimated_graphs, true_graphs):
            eval_dict = self.evaluate(est, true)
            for k, v in eval_dict.items():
                results[k].append(v)
        return dict(results)

    # ------------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------------

    def get_last_graph(self) -> Optional[nx.DiGraph]:
        """Return the most recently learned graph."""
        return self._graph

    @staticmethod
    def generate_linear_gaussian(n_samples: int, n_vars: int, degree: int = 2,
                                  seed: int = 42, noise_scale: float = 0.1) -> Tuple[np.ndarray, nx.DiGraph]:
        """
        Generate synthetic linear Gaussian data from a random DAG.
        Returns (data, true_graph).
        """
        if not HAS_NETWORKX:
            raise ImportError("NetworkX required for data generation")
        np.random.seed(seed)
        # Generate a random DAG
        graph = nx.gnp_random_graph(n_vars, 0.3, directed=True, seed=seed)
        # Ensure it's a DAG by making it lower‑triangular after topological sort
        try:
            topo = list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            # Fallback: make it lower‑triangular by random order
            topo = list(range(n_vars))
            np.random.shuffle(topo)
        adj = np.zeros((n_vars, n_vars))
        for u, v in graph.edges():
            if topo.index(u) < topo.index(v):
                adj[u, v] = np.random.uniform(0.5, 2.0) * (1 if np.random.rand() > 0.5 else -1)
        # Generate data
        data = np.zeros((n_samples, n_vars))
        for t in range(n_samples):
            x = np.random.randn(n_vars) * noise_scale
            for i in topo:
                parents = np.where(adj[:, i] != 0)[0]
                for p in parents:
                    x[i] += adj[p, i] * x[p]
            data[t, :] = x
        true_graph = nx.DiGraph()
        for i in range(n_vars):
            for j in range(n_vars):
                if adj[i, j] != 0:
                    true_graph.add_edge(i, j)
        return data, true_graph


# ============================================================================
# INTEGRATION WITH LAYER 2 (UltimateRelation) – legacy helpers
# ============================================================================

def relation_to_causal_graph(relation: 'UltimateRelation') -> Optional[nx.DiGraph]:
    """
    Extract the causal graph stored in an UltimateRelation (if any).
    Assumes relation.causal_graph is a NetworkX DiGraph.
    """
    if hasattr(relation, 'causal_graph') and relation.causal_graph is not None:
        return relation.causal_graph
    return None


def add_causal_graph_to_relation(relation: 'UltimateRelation', graph: nx.DiGraph):
    """Attach a causal graph to an UltimateRelation."""
    relation.causal_graph = graph
    # If UltimateRelation has a stale marker, call it
    if hasattr(relation, '_mark_stale'):
        relation._mark_stale()


# ============================================================================
# DEMO (updated to show new features)
# ============================================================================

def demo():
    """Run a demonstration with synthetic data and new Layer 1 integration."""
    print("="*80)
    print("CAUSAL DISCOVERY DEMO")
    print("="*80)

    # Generate synthetic data
    data, true_graph = CausalDiscovery.generate_linear_gaussian(1000, 5, degree=2, seed=42)
    print("True graph edges:", list(true_graph.edges()))

    cd = CausalDiscovery(data, variable_names=[f"X{i}" for i in range(5)])

    # Test PC
    if HAS_CAUSALLEARN:
        print("\n--- PC ---")
        try:
            pc_graph = cd.pc(alpha=0.05)
            print("PC estimated edges:", list(pc_graph.edges()))
            eval_pc = cd.evaluate(pc_graph, true_graph)
            print(f"  SHD: {eval_pc['shd']}, F1: {eval_pc['skeleton_f1']:.3f}")
        except Exception as e:
            print(f"PC failed: {e}")

    # Test GES
    if HAS_CAUSALLEARN:
        print("\n--- GES ---")
        try:
            ges_graph = cd.ges()
            print("GES estimated edges:", list(ges_graph.edges()))
            eval_ges = cd.evaluate(ges_graph, true_graph)
            print(f"  SHD: {eval_ges['shd']}, F1: {eval_ges['skeleton_f1']:.3f}")
        except Exception as e:
            print(f"GES failed: {e}")

    # Test LiNGAM
    if HAS_LINGAM:
        print("\n--- LiNGAM (ICALiNGAM) ---")
        try:
            lingam_graph = cd.lingam(method='ICALiNGAM')
            print("LiNGAM estimated edges:", list(lingam_graph.edges()))
            eval_ling = cd.evaluate(lingam_graph, true_graph)
            print(f"  SHD: {eval_ling['shd']}, F1: {eval_ling['skeleton_f1']:.3f}")
        except Exception as e:
            print(f"LiNGAM failed: {e}")

    # Test NOTEARS with prior
    print("\n--- NOTEARS with atomicity prior ---")
    # Simulate atomicity scores
    atomicity = {f"X{i}": np.random.uniform(0, 1) for i in range(5)}
    prior = cd.prior_from_atomicity(atomicity, inverse_temp=2.0)
    try:
        notears_graph = cd.notears(w_threshold=0.3, prior_matrix=prior)
        print("NOTEARS estimated edges:", list(notears_graph.edges()))
        eval_nt = cd.evaluate(notears_graph, true_graph)
        print(f"  SHD: {eval_nt['shd']}, F1: {eval_nt['skeleton_f1']:.3f}")
    except Exception as e:
        print(f"NOTEARS failed: {e}")

    # Granger causality example
    if HAS_STATSMODELS:
        print("\n--- Granger causality (X0 -> X1) ---")
        gc = cd.granger_causality(0, 1)
        print(f"  F-stat: {gc['f_stat']:.3f}, p-value: {gc['p_value']:.3f}")

    # DoWhy inference example (if available)
    if HAS_DOWHY:
        print("\n--- DoWhy causal effect estimation ---")
        try:
            # Assume we have a graph (e.g., from PC)
            graph = pc_graph if HAS_CAUSALLEARN else nx.DiGraph()
            graph.add_edges_from([('X0', 'X1'), ('X1', 'X2'), ('X0', 'X2')])
            effect = cd.estimate_effect('X0', 'X2', graph, method='backdoor.linear_regression')
            print(f"Estimated effect of X0 on X2: {effect:.4f}")

            # Counterfactual
            cf = cd.counterfactual('X0', 'X2', graph, treatment_value=2.0)
            print(f"Counterfactual outcomes (first 5): {cf[:5]}")

            # Refutation
            ref = cd.refute_estimate('X0', 'X2', graph, refutation_method='random_common_cause')
            print(f"Refutation p-value: {ref['p_value']:.4f}")
        except Exception as e:
            print(f"DoWhy example failed: {e}")

    # New: from_layer1_registry demo (requires dummy registry)
    print("\n--- from_layer1_registry demo ---")
    # Create a dummy Layer 1 registry
    class DummyObs:
        def __init__(self, oid, dims, phase):
            self.id = oid
            self.qualitative_dims = dims
            self.temporal_phase = phase
    registry = {
        'A': DummyObs('A', {'f1': 0.1, 'f2': 0.2}, 0.0),
        'B': DummyObs('B', {'f1': 0.3, 'f2': 0.4}, 1.0),
        'C': DummyObs('C', {'f1': 0.5, 'f2': 0.6}, 2.0),
    }
    cd_layer1 = CausalDiscovery.from_layer1_registry(registry, use_phase=True)
    print(f"Data shape: {cd_layer1.data.shape}, variables: {cd_layer1.variable_names}")

    # Test ingest_causal_graph (requires a mock Layer2)
    class MockLayer2:
        def create_relation(self, source_id, target_id, relation_type, weight, metadata):
            print(f"Creating relation: {source_id} -> {target_id} (weight={weight})")
            class Rel: pass
            rel = Rel()
            rel.id = f"{source_id}_{target_id}"
            return rel
    mock_layer2 = MockLayer2()
    if HAS_CAUSALLEARN:
        pc_graph = cd_layer1.pc(alpha=0.05)  # just for demo
        cd_layer1.ingest_causal_graph(mock_layer2, graph=pc_graph)
    else:
        print("Skipping ingest demo because PC not available.")


if __name__ == "__main__":
    demo()