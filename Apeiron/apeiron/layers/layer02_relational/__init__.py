"""
Layer 2: Relational Dynamics – Ultimate Implementation
=======================================================
This module provides the core relational structures and the layer class.
All optional features (spectral analysis, hypergraphs, quantum graphs,
motif detection, category theory, probabilistic models, etc.) are available
via the exported classes and functions.

**NEW IN VERSION 5.0:**
- Comprehensive causal discovery (PC, FCI, GES, LiNGAM, NOTEARS, CAM)
- Quantum machine learning (QSVM, VQC, quantum kernels)
- Single‑agent and multi‑agent reinforcement learning on graphs
- Interactive dashboards with advanced Plotly components
- Database integration (SQLite, PostgreSQL, Neo4j, MongoDB)
- Temporal networks and time‑series analysis
- Self‑supervised graph learning (GraphCL, InfoGraph, DGI)
- Derived categories, model categories, and Hall algebras
- Probabilistic graphical models (Bayesian networks, MRFs, HMMs, CRFs)
- Quantum error correction codes (repetition, Shor, Steane, surface)
- GraphQL API for querying Layer 2 objects
- Comprehensive benchmarking and validation tools

All classes degrade gracefully if optional libraries are missing.
"""

# ============================================================================
# Existing modules (core)
# ============================================================================

from .adjacency_matrix import (
    SpectralGraphAnalysis,
    SpectralType,
    GraphType,
    spectral_analysis_from_networkx,
    spectral_analysis_from_igraph,
    spectral_analysis_from_graphtool,
    spectral_analysis_from_adjacency,
    multiview_spectral_clustering,
    DynamicSpectralAnalysis,
    SpectralDatabase
)

from .hypergraph_relations import (
    Hypergraph,
    QuantumGraph,
    HomologyType,
    QuantumWalkType,
    Sheaf,
    MultiParameterPersistence,
    QuantumState,
    QuantumChannel,
    TensorNetwork,
    HypergraphEnv,
    RLAgent,
    HypergraphDatabase,
    create_hypergraph_dashboard,
    InfinityCategory as HyperInfinityCategory
)

from .motif_detection import (
    TopologicalNetworkAnalysis,
    FiltrationType,
    MotifType,
    MotifCounter,
    PersistentHomology,
    TemporalMotifDetector,
    # CausalDiscovery is superseded by causal_discovery.CausalDiscovery – kept for compatibility
    CausalDiscovery as CausalDiscoveryMotif,
    GraphNeuralNetwork,
    GraphAutoencoder,
    GraphRL,
    GraphKernel,
    CausalAlgorithm,
    QuantumML as QuantumMLPlaceholder,
    GraphRLEnv,
    GraphRLAgent,
    Mapper,
    MotifDatabase,
    create_motif_dashboard,
    granger_causality,
    pc_algorithm,
    persistent_cohomology,
    zigzag_persistence,
    find_paths,
    find_all_cycles,
    detect_communities,
    compute_centralities,
    InfinityCategory as MotifInfinityCategory
)

from .relations import (
    RelationType,
    FunctorType,
    NaturalTransformationType,
    QuiverType,
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
    Quiver,
    QuiverRepresentation,
    QuiverRepresentationTheory,
    PathAlgebra,
    RelationalMetricSpace,
    BayesianNetwork,
    MarkovRandomField,
    UltimateRelation,
    Layer2_Relational_Ultimate,
    InfinityCategory as RelInfinityCategory
)

# ============================================================================
# NEW MODULES (ultimate extensions)
# ============================================================================

# Benchmarks
from .benchmarks import (
    BenchmarkSuite,
    BenchmarkResult,
    BenchmarkDataGenerator
)

# Dashboard (static figures)
from .dashboard import (
    figure_persistence_diagram,
    figure_barcode,
    figure_spectrum,
    figure_spectral_embedding,
    figure_hypergraph,
    figure_quantum_graph,
    figure_causal_graph,
    figure_motif_counts,
    figure_communities,
    create_spectral_dashboard,
    create_topology_dashboard,
    create_hypergraph_dashboard as create_hypergraph_dash,
    create_quantum_dashboard,
    create_causal_dashboard,
    create_combined_dashboard,
    run_dashboard
)

# Interactive visualization components
from .visualization_dash import (
    InteractiveComponent,
    PersistenceDiagramComponent,
    SpectralEmbeddingComponent,
    HypergraphComponent,
    QuantumGraphComponent,
    CausalGraphComponent,
    CommunityMapComponent,
    create_interactive_dashboard
)

# Causal discovery (comprehensive)
from .causal_discovery import (
    CausalDiscovery
)

# Multi‑agent reinforcement learning
from .multi_agent_rl import (
    MultiAgentGraphEnv,
    IndependentQLearningAgent,
    DQNAgent as MultiAgentDQN,
    train_multi_agent,
    plot_trajectories,
    PettingZooMultiAgentGraphEnv,
    RLLibMultiAgentGraphEnv
)

# Single‑agent reinforcement learning on graphs
from .rl_on_graphs import (
    GraphEnv,
    QLearningAgent,
    DQNAgent as SingleAgentDQN,
    train_agent,
    plot_rewards,
    plot_trajectory,
    create_sb3_model,
    train_sb3
)

# Categorical verification
from .categorical_verification import (
    verify_category,
    verify_functor,
    verify_natural_transformation,
    verify_adjunction,
    verify_monad,
    verify_all
)

# Hall algebra
from .hall_algebra import (
    Partition,
    HallAlgebra,
    JordanHallAlgebra,
    littlewood_richardson
)

# Probabilistic models
from .probabilistic_models import (
    BayesianNetwork,
    MarkovRandomField,
    ConditionalRandomField,
    HiddenMarkovModel,
    ProbabilisticModel
)

# Quantum error correction
from .quantum_error_correction import (
    QuantumErrorCorrectionCode,
    RepetitionCode,
    ShorCode,
    SteaneCode,
    FiveQubitCode,
    SurfaceCode,
    LookupTableDecoder,
    ErrorCorrectedQuantumChannel
)

# Quiver moduli
from .quiver_moduli import (
    StabilityCondition,
    ModuliSpace,
    is_stable,
    is_semistable
)

# Derived categories
from .derived_categories import (
    ChainComplex,
    ChainMap,
    ChainHomotopy,
    mapping_cone,
    Ext,
    Tor,
    SpectralSequence
)

# Model categories
from .model_categories import (
    ModelCategory,
    ChainComplexesModelCategory,
    TopologicalSpacesModelCategory,
    QuillenAdjunction,
    TotalLeftDerivedFunctor,
    TotalRightDerivedFunctor
)

# Self‑supervised graph learning
from .graph_self_supervised import (
    SelfSupervisedGraphModel,
    GraphCL,
    InfoGraph,
    DGI,
    MaskedGraphAutoencoder,
    GCNEncoder,
    GINEncoder,
    node_dropping,
    edge_perturbation,
    attribute_masking,
    subgraph_sampling,
    shuffle_nodes,
    linear_evaluation,
    fine_tune
)

# GraphQL API
from .graphql_api import (
    schema,
    create_graphql_router,
    run_server
)

# Database integration
from .database_integration import (
    DatabaseManager,
    SQLiteBackend,
    PostgreSQLBackend,
    Neo4jBackend,
    MongoBackend
)

# Temporal networks
from .temporal_networks import (
    TemporalGraph,
    TemporalNetwork,
    dynamic_communities,
    community_persistence,
    community_transitions,
    compute_statistics_series,
    detect_change_points,
    temporal_motif_count,
    temporal_motif_significance,
    forecast_next_snapshot,
    forecast_graph,
    plot_statistics_series,
    plot_community_evolution
)

# Quantum machine learning
from .quantum_ml import (
    QuantumMLModel,
    QuantumKernel,
    QSVM,
    VariationalQuantumClassifier,
    QuantumCircuitLearner,
    QGAN,
    angle_encoding,
    amplitude_encoding
)

# ============================================================================
# Resolve naming conflicts: export a single InfinityCategory (from relations)
# ============================================================================
InfinityCategory = RelInfinityCategory

# ============================================================================
# Export all
# ============================================================================

__all__ = [
    # adjacency_matrix
    "SpectralGraphAnalysis",
    "SpectralType",
    "GraphType",
    "spectral_analysis_from_networkx",
    "spectral_analysis_from_igraph",
    "spectral_analysis_from_graphtool",
    "spectral_analysis_from_adjacency",
    "multiview_spectral_clustering",
    "DynamicSpectralAnalysis",
    "SpectralDatabase",

    # hypergraph_relations
    "Hypergraph",
    "QuantumGraph",
    "HomologyType",
    "QuantumWalkType",
    "Sheaf",
    "MultiParameterPersistence",
    "QuantumState",
    "QuantumChannel",
    "TensorNetwork",
    "HypergraphEnv",
    "RLAgent",
    "HypergraphDatabase",
    "create_hypergraph_dashboard",

    # motif_detection (legacy)
    "TopologicalNetworkAnalysis",
    "FiltrationType",
    "MotifType",
    "MotifCounter",
    "PersistentHomology",
    "TemporalMotifDetector",
    "CausalDiscoveryMotif",
    "GraphNeuralNetwork",
    "GraphAutoencoder",
    "GraphRL",
    "GraphKernel",
    "CausalAlgorithm",
    "QuantumMLPlaceholder",
    "GraphRLEnv",
    "GraphRLAgent",
    "Mapper",
    "MotifDatabase",
    "create_motif_dashboard",
    "granger_causality",
    "pc_algorithm",
    "persistent_cohomology",
    "zigzag_persistence",
    "find_paths",
    "find_all_cycles",
    "detect_communities",
    "compute_centralities",

    # relations
    "RelationType",
    "FunctorType",
    "NaturalTransformationType",
    "QuiverType",
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
    "Quiver",
    "QuiverRepresentation",
    "QuiverRepresentationTheory",
    "PathAlgebra",
    "RelationalMetricSpace",
    "BayesianNetwork",
    "MarkovRandomField",
    "UltimateRelation",
    "Layer2_Relational_Ultimate",
    "InfinityCategory",

    # benchmarks
    "BenchmarkSuite",
    "BenchmarkResult",
    "BenchmarkDataGenerator",

    # dashboard (static)
    "figure_persistence_diagram",
    "figure_barcode",
    "figure_spectrum",
    "figure_spectral_embedding",
    "figure_hypergraph",
    "figure_quantum_graph",
    "figure_causal_graph",
    "figure_motif_counts",
    "figure_communities",
    "create_spectral_dashboard",
    "create_topology_dashboard",
    "create_hypergraph_dash",
    "create_quantum_dashboard",
    "create_causal_dashboard",
    "create_combined_dashboard",
    "run_dashboard",

    # visualization_dash (interactive)
    "InteractiveComponent",
    "PersistenceDiagramComponent",
    "SpectralEmbeddingComponent",
    "HypergraphComponent",
    "QuantumGraphComponent",
    "CausalGraphComponent",
    "CommunityMapComponent",
    "create_interactive_dashboard",

    # causal_discovery
    "CausalDiscovery",

    # multi_agent_rl
    "MultiAgentGraphEnv",
    "IndependentQLearningAgent",
    "MultiAgentDQN",
    "train_multi_agent",
    "plot_trajectories",
    "PettingZooMultiAgentGraphEnv",
    "RLLibMultiAgentGraphEnv",

    # rl_on_graphs
    "GraphEnv",
    "QLearningAgent",
    "SingleAgentDQN",
    "train_agent",
    "plot_rewards",
    "plot_trajectory",
    "create_sb3_model",
    "train_sb3",

    # categorical_verification
    "verify_category",
    "verify_functor",
    "verify_natural_transformation",
    "verify_adjunction",
    "verify_monad",
    "verify_all",

    # hall_algebra
    "Partition",
    "HallAlgebra",
    "JordanHallAlgebra",
    "littlewood_richardson",

    # probabilistic_models
    "BayesianNetwork",
    "MarkovRandomField",
    "ConditionalRandomField",
    "HiddenMarkovModel",
    "ProbabilisticModel",

    # quantum_error_correction
    "QuantumErrorCorrectionCode",
    "RepetitionCode",
    "ShorCode",
    "SteaneCode",
    "FiveQubitCode",
    "SurfaceCode",
    "LookupTableDecoder",
    "ErrorCorrectedQuantumChannel",

    # quiver_moduli
    "StabilityCondition",
    "ModuliSpace",
    "is_stable",
    "is_semistable",

    # derived_categories
    "ChainComplex",
    "ChainMap",
    "ChainHomotopy",
    "mapping_cone",
    "Ext",
    "Tor",
    "SpectralSequence",

    # model_categories
    "ModelCategory",
    "ChainComplexesModelCategory",
    "TopologicalSpacesModelCategory",
    "QuillenAdjunction",
    "TotalLeftDerivedFunctor",
    "TotalRightDerivedFunctor",

    # graph_self_supervised
    "SelfSupervisedGraphModel",
    "GraphCL",
    "InfoGraph",
    "DGI",
    "MaskedGraphAutoencoder",
    "GCNEncoder",
    "GINEncoder",
    "node_dropping",
    "edge_perturbation",
    "attribute_masking",
    "subgraph_sampling",
    "shuffle_nodes",
    "linear_evaluation",
    "fine_tune",

    # graphql_api
    "schema",
    "create_graphql_router",
    "run_server",

    # database_integration
    "DatabaseManager",
    "SQLiteBackend",
    "PostgreSQLBackend",
    "Neo4jBackend",
    "MongoBackend",

    # temporal_networks
    "TemporalGraph",
    "TemporalNetwork",
    "dynamic_communities",
    "community_persistence",
    "community_transitions",
    "compute_statistics_series",
    "detect_change_points",
    "temporal_motif_count",
    "temporal_motif_significance",
    "forecast_next_snapshot",
    "forecast_graph",
    "plot_statistics_series",
    "plot_community_evolution",

    # quantum_ml
    "QuantumMLModel",
    "QuantumKernel",
    "QSVM",
    "VariationalQuantumClassifier",
    "QuantumCircuitLearner",
    "QGAN",
    "angle_encoding",
    "amplitude_encoding",
]

__version__ = "5.0.0"
__author__ = "Nexus Team"