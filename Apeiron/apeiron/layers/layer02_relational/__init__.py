"""
Layer 2: Relational Dynamics – Public API (refactored v6.0)
============================================================
This module provides the core relational structures and analysis tools
for the APEIRON framework, including extreme theoretical extensions:
sheaf diffusion, topos logic, HoTT, derived learning, ontogenesis,
retrocausal dynamics, spectral triple, epistemic horizon, and
bio‑digital reaction functor.

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
    LazyNerve,
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
    zigzag_persistence_full,
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

# ===================================================================
# NEW MODULES (v5.1)
# ===================================================================

# Sheaf theory
try:
    from .sheaf_hypergraph import (
        SheafHypergraph,
        SheafStalk,
        RestrictionMap,
        SheafCohomologyResult,
    )
except ImportError:
    pass

# Categorical TDA
try:
    from .categorical_tda import (
        CategoricalTDA,
        PersistenceModule,
        MapperFunctor,
    )
except ImportError:
    pass

# Hodge decomposition
try:
    from .hodge_decomposition import (
        HypergraphHodgeDecomposer,
        HodgeDecomposition,
    )
except ImportError:
    pass

# Higher category theory
try:
    from .higher_category import (
        StrictTwoCategory,
        Bicategory,
        SimplicialSet,
    )
except ImportError:
    pass

# Spectral sheaf analysis
try:
    from .spectral_sheaf import (
        SheafSpectralAnalyzer,
        SheafSpectralResult,
    )
except ImportError:
    pass

# Endogenous time
try:
    from .endogenous_time import (
        EndogenousTimeGenerator,
        CausalPartialOrder,
        TimeCone,
    )
except ImportError:
    pass

# Formal verification (Z3 / Coq)
try:
    from .formal_layer2_verification import (
        Z3HypergraphVerifier,
        CoqCertificateGenerator,
        Layer2VerificationOrchestrator,
        VerificationResult,
    )
except ImportError:
    pass

# Quantum topology
try:
    from .quantum_topology import (
        QuantumBettiEstimator,
        QuantumTopologyResult,
        HypergraphTQFT,
        QuantumHodgeSolver,
    )
except ImportError:
    pass

# Unified API & coverage
try:
    from .layer2_unified_api import (
        Layer2UnifiedAPI,
        compute_theory_coverage,
        CoverageReport,
    )
except ImportError:
    pass

# ===================================================================
# EXTREME MODULES (v6.0)
# ===================================================================

# Sheaf diffusion dynamics (pain receptor)
try:
    from .sheaf_diffusion_dynamics import (
        SheafDiffusionDynamics,
        DiffusionState,
        AdaptiveThreshold as DiffusionAdaptiveThreshold,
    )
except ImportError:
    pass

# Topos-theoretic logic
try:
    from .topos_layer2 import (
        ToposLogic,
        SubobjectClassifier,
        HypergraphTopology,
        topos_from_hypergraph,
    )
except ImportError:
    pass

# Homotopy Type Theory unification
try:
    from .hott_category import (
        UnivalentCategory,
        Isomorphism,
        univalent_category_from_hypergraph,
    )
except ImportError:
    pass

# Derived learning (Ext / Tor error propagation)
try:
    from .derived_learning import (
        DerivedFunctor,
        ErrorPropagation,
        SheafModule,
        derived_learning_pipeline,
    )
except ImportError:
    pass

# Ontogenesis engine (autonomous layer growth)
try:
    from .ontogenesis_engine import (
        OntogenesisEngine,
        GapDetector,
        KanExtensionBuilder,
        EpistemicGap,
        ontogenesis_from_hypergraph,
    )
except ImportError:
    pass

# Retrocausal dynamics (variational knowledge evolution)
try:
    from .retrocausal_dynamics import (
        RetrocausalDynamics,
        RetrocausalState,
    )
except ImportError:
    pass

# Spectral triple (non-commutative geometry)
try:
    from .spectral_triple import (
        SpectralTriple,
        spectral_triple_from_hypergraph,
    )
except ImportError:
    pass

# Epistemic horizon (data quarantine)
try:
    from .epistemic_horizon import (
        EpistemicHorizonDetector,
        DataQuarantine,
        EpistemicSingularity,
        horizon_pipeline,
    )
except ImportError:
    pass

# Reaction functor (bio‑digital synthesis)
try:
    from .reaction_functor import (
        BioDigitalCompiler,
        ReactionCategory,
        ReactionFunctor,
        compile_hypergraph_to_gcode,
    )
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
    "LazyNerve",
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
    "zigzag_persistence_full",
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
    # v5.1
    "SheafHypergraph",
    "SheafStalk",
    "RestrictionMap",
    "SheafCohomologyResult",
    "CategoricalTDA",
    "PersistenceModule",
    "MapperFunctor",
    "HypergraphHodgeDecomposer",
    "HodgeDecomposition",
    "StrictTwoCategory",
    "Bicategory",
    "SimplicialSet",
    "SheafSpectralAnalyzer",
    "SheafSpectralResult",
    "EndogenousTimeGenerator",
    "CausalPartialOrder",
    "TimeCone",
    "Z3HypergraphVerifier",
    "CoqCertificateGenerator",
    "Layer2VerificationOrchestrator",
    "VerificationResult",
    "QuantumBettiEstimator",
    "QuantumTopologyResult",
    "HypergraphTQFT",
    "QuantumHodgeSolver",
    "Layer2UnifiedAPI",
    "compute_theory_coverage",
    "CoverageReport",
    # v6.0 extreme modules
    "SheafDiffusionDynamics",
    "DiffusionState",
    "DiffusionAdaptiveThreshold",
    "ToposLogic",
    "SubobjectClassifier",
    "HypergraphTopology",
    "topos_from_hypergraph",
    "UnivalentCategory",
    "Isomorphism",
    "univalent_category_from_hypergraph",
    "DerivedFunctor",
    "ErrorPropagation",
    "SheafModule",
    "derived_learning_pipeline",
    "OntogenesisEngine",
    "GapDetector",
    "KanExtensionBuilder",
    "EpistemicGap",
    "ontogenesis_from_hypergraph",
    "RetrocausalDynamics",
    "RetrocausalState",
    "SpectralTriple",
    "spectral_triple_from_hypergraph",
    "EpistemicHorizonDetector",
    "DataQuarantine",
    "EpistemicSingularity",
    "horizon_pipeline",
    "BioDigitalCompiler",
    "ReactionCategory",
    "ReactionFunctor",
    "compile_hypergraph_to_gcode",
]