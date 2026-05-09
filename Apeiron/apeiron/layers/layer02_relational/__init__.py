"""
Layer 2: Relational Dynamics – Public API (refactored v5.0)
============================================================
This module provides the core relational structures and analysis tools
for the APEIRON framework.

All heavy optional dependencies (quantum, RL, TDA, etc.) are imported
lazily or reside in subdirectories (e.g. optional/).
"""

# ---------------------------------------------------------------------------
# Core relation classes
# ---------------------------------------------------------------------------
from .relations_core import (
    UltimateRelation,
    Layer2_Relational_Ultimate,
    RelationType,
)

# ---------------------------------------------------------------------------
# Category theory
# ---------------------------------------------------------------------------
from .category import (
    RelationalCategory,
    RelationalFunctor,
    NaturalTransformation,
    MonoidalStructure,
    TwoCategory,
    Adjunction,
    Monad,
    Comonad,
    Limit,
    Colimit,
    KanExtension,
    YonedaEmbedding,
    EnrichedCategory,
    FunctorType,
    NaturalTransformationType,
    AdjunctionType,
)

# ---------------------------------------------------------------------------
# Quivers
# ---------------------------------------------------------------------------
from .quiver import (
    Quiver,
    QuiverRepresentation,
    QuiverRepresentationTheory,
    PathAlgebra,
)

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
from .metric import RelationalMetricSpace

# ---------------------------------------------------------------------------
# Spectral analysis
# ---------------------------------------------------------------------------
from .spectral import (
    SpectralGraphAnalysis,
    SpectralType,
    DynamicSpectralAnalysis,
    multiview_spectral_clustering,
)

# ---------------------------------------------------------------------------
# Hypergraphs & quantum graphs
# ---------------------------------------------------------------------------
from .hypergraph import Hypergraph
from .quantum_graph import QuantumGraph

# ---------------------------------------------------------------------------
# Motifs & TDA
# ---------------------------------------------------------------------------
from .motif_detection import (
    MotifCounter,
    PersistentHomology,
    TemporalMotifDetector,
    TopologicalNetworkAnalysis,
    GraphKernel,
    detect_communities_enhanced,
    compute_centralities_extended,
    find_paths,
    find_all_cycles,
    zigzag_persistence,
)

# ---------------------------------------------------------------------------
# Causal discovery
# ---------------------------------------------------------------------------
from .causal_discovery import CausalDiscovery

# ---------------------------------------------------------------------------
# Probabilistic models
# ---------------------------------------------------------------------------
from .probabilistic_models import (
    BayesianNetwork,
    MarkovRandomField,
    HiddenMarkovModel,
    ConditionalRandomField,
)

# ---------------------------------------------------------------------------
# Temporal networks
# ---------------------------------------------------------------------------
from .temporal_networks import (
    TemporalNetwork,
    TemporalGraph,
    dynamic_communities,
    community_persistence,
    community_transitions,
    forecast_next_snapshot,
    forecast_graph,
    temporal_motif_count,
    temporal_motif_significance,
)

# ---------------------------------------------------------------------------
# Layer‑1 bridge
# ---------------------------------------------------------------------------
from .layer1_bridge import (
    extract_feature_matrix,
    similarity_matrix,
    registry_to_graph,
    discretize_observable,
)

# ---------------------------------------------------------------------------
# Reinforcement learning (optional – may raise ImportError if gym missing)
# ---------------------------------------------------------------------------
try:
    from .graph_rl import (
        GraphEnv,
        ResourceCollectionEnv,
        GraphCoveringEnv,
        DeliveryEnv,
        HypergraphEnv,
        QLearningAgent,
        DQNAgent,
        RLAgent,
        train_agent,
        train_dqn,
    )
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Mapper (optional – may raise ImportError if kmapper missing)
# ---------------------------------------------------------------------------
try:
    from .mapper import Mapper
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Public API list
# ---------------------------------------------------------------------------
__all__ = [
    "UltimateRelation",
    "Layer2_Relational_Ultimate",
    "RelationType",
    "RelationalCategory",
    "RelationalFunctor",
    "NaturalTransformation",
    "MonoidalStructure",
    "TwoCategory",
    "Adjunction",
    "Monad",
    "Comonad",
    "Limit",
    "Colimit",
    "KanExtension",
    "YonedaEmbedding",
    "EnrichedCategory",
    "FunctorType",
    "NaturalTransformationType",
    "AdjunctionType",
    "Quiver",
    "QuiverRepresentation",
    "QuiverRepresentationTheory",
    "PathAlgebra",
    "RelationalMetricSpace",
    "SpectralGraphAnalysis",
    "SpectralType",
    "DynamicSpectralAnalysis",
    "multiview_spectral_clustering",
    "Hypergraph",
    "QuantumGraph",
    "MotifCounter",
    "PersistentHomology",
    "TemporalMotifDetector",
    "TopologicalNetworkAnalysis",
    "GraphKernel",
    "detect_communities_enhanced",
    "compute_centralities_extended",
    "find_paths",
    "find_all_cycles",
    "zigzag_persistence",
    "CausalDiscovery",
    "BayesianNetwork",
    "MarkovRandomField",
    "HiddenMarkovModel",
    "ConditionalRandomField",
    "TemporalNetwork",
    "TemporalGraph",
    "dynamic_communities",
    "community_persistence",
    "community_transitions",
    "forecast_next_snapshot",
    "forecast_graph",
    "temporal_motif_count",
    "temporal_motif_significance",
    "extract_feature_matrix",
    "similarity_matrix",
    "registry_to_graph",
    "discretize_observable",
]