"""
Layer 1: Foundational Observables – Ultimate Implementation
=============================================================
This module provides the core irreducible units (observables) and their
qualitative dimensions, as well as meta-specification, decomposition operators,
automatic discovery of new principles, density field for relational context,
and various utilities. All classes and functions from the submodules are
exported for easy access.

Graceful degradation: optional libraries (scikit-learn, scipy, gudhi, etc.)
are handled internally; missing dependencies do not crash the module.

Exported classes and functions
-------------------------------

Observables
    ``UltimateObservable``, ``ObservabilityType``, ``GeometricStructure``,
    ``TopologicalStructure``, ``CategoricalStructure``, ``QuantumStructure``,
    ``FractalStructure``, ``InformationGeometry``, ``DynamicalSystem``,
    ``GroupStructure``, ``GradualityType``, ``SymmetryType``, ``GUDHI_AVAILABLE``

Atomicity framework functions
    ``boolean_atomicity``, ``info_atomicity``,
    ``decomposition_boolean_atomicity``, ``qualitative_dimensions_atomicity``,
    ``category_atomicity``, ``group_atomicity``,
    ``topological_persistence_atomicity``,
    ``get_framework_names_for_principle``

Qualitative dimensions
    ``QualitativeDimension``, ``ScalarDimension``, ``IntensityDimension``,
    ``DensityDimension``, ``VectorDimension``, ``ColourDimension``,
    ``TensorDimension``, ``TextureDimension``, ``ComplexDimension``,
    ``QuaternionDimension``, ``FractalDimension``, ``PatternDimension``,
    ``MultiResolutionDimension``, ``GPUAcceleratedDimension``,
    ``DimensionType``, ``IntensityType``, ``DensityType``, ``ColourSpace``,
    ``TextureType``, ``PatternType``, ``ResonanceBridge``

Qualitative dimension utilities
    ``compute_gradient_numerical``, ``compute_hessian_numerical``,
    ``gradient_symbolic``, ``DimensionCache``, ``plot_dimension``

Layer
    ``Layer1_Observables``

Meta-specification
    ``MetaSpecification``, ``DecompositionPrinciple``, ``ObserverDependence``,
    ``DEFAULT_META_SPEC``, ``PRINCIPLE_OPERATOR_ALIASES``,
    ``LOGICAL``, ``MEASURE``, ``CATEGORICAL``, ``INFORMATION``,
    ``GEOMETRIC``, ``QUALITATIVE``,
    ``register_atomicity_framework``, ``atomicity_framework``,
    ``ATOMICITY_FRAMEWORKS``

Decomposition operators
    ``DecompositionOperator``, ``ListSplitOperator``, ``StringSplitOperator``,
    ``DictSplitOperator``, ``ArraySplitOperator``,
    ``BooleanDecompositionOperator``, ``MeasureDecompositionOperator``,
    ``CategoricalDecompositionOperator``, ``InformationDecompositionOperator``,
    ``GeometricDecompositionOperator``, ``GeometricPointOperator``,
    ``QualitativeDecompositionOperator``, ``PalindromeDecompositionOperator``,
    ``InverseLimitOperator``,
    ``register_decomposition_operator``, ``get_decomposition_operator``,
    ``is_atomic_by_operator``, ``DECOMPOSITION_OPERATORS``

Discovery
    ``EvolutionaryFeedbackLoop``, ``HeuristicDiscovery``, ``DiscoveryProposal``,
    ``auto_discovery_pipeline``, ``DensityBasedDecompositionOperator``,
    ``FrequencyDecompositionOperator``, ``EntropyDecompositionOperator``,
    ``SparsityDecompositionOperator``

Relational context
    ``DensityField``, ``InfluenceSample``
"""

# ============================================================================
# Core observable and structures
# ============================================================================
from .irreducible_unit import (
    UltimateObservable,
    ObservabilityType,
    GeometricStructure,
    TopologicalStructure,
    CategoricalStructure,
    QuantumStructure,
    FractalStructure,
    InformationGeometry,
    DynamicalSystem,
    GroupStructure,
    GradualityType,
    SymmetryType,
    GUDHI_AVAILABLE,
    # Atomicity framework functions (used directly in tests and higher layers)
    boolean_atomicity,
    info_atomicity,
    decomposition_boolean_atomicity,
    qualitative_dimensions_atomicity,
    category_atomicity,
    group_atomicity,
    topological_persistence_atomicity,
    get_framework_names_for_principle,
)

# ============================================================================
# Qualitative dimensions
# ============================================================================
from .qualitative_dimensions import (
    QualitativeDimension,
    ScalarDimension,
    IntensityDimension,
    IntensityType,
    DensityDimension,
    DensityType,
    VectorDimension,
    ColourDimension,
    ColourSpace,
    TensorDimension,
    TextureDimension,
    TextureType,
    ComplexDimension,
    QuaternionDimension,
    FractalDimension,
    PatternDimension,
    PatternType,
    MultiResolutionDimension,
    GPUAcceleratedDimension,
    DimensionType,
    ResonanceBridge,
    compute_gradient_numerical,
    compute_hessian_numerical,
    gradient_symbolic,
    DimensionCache,
    plot_dimension,
)

# ============================================================================
# Layer 1 manager
# ============================================================================
from .observables import (
    Layer1_Observables,
)

# ============================================================================
# Meta-specification and atomicity frameworks
# ============================================================================
from .meta_spec import (
    MetaSpecification,
    DecompositionPrinciple,
    ObserverDependence,
    DEFAULT_META_SPEC,
    PRINCIPLE_OPERATOR_ALIASES,
    # Pre-defined standard principles (check-or-create singletons)
    LOGICAL,
    MEASURE,
    CATEGORICAL,
    INFORMATION,
    GEOMETRIC,
    QUALITATIVE,
    register_atomicity_framework,
    atomicity_framework,
    ATOMICITY_FRAMEWORKS,
)

# ============================================================================
# Decomposition operators
# ============================================================================
from .decomposition import (
    DecompositionOperator,
    ListSplitOperator,
    StringSplitOperator,
    DictSplitOperator,
    ArraySplitOperator,
    BooleanDecompositionOperator,
    MeasureDecompositionOperator,
    CategoricalDecompositionOperator,
    InformationDecompositionOperator,
    GeometricDecompositionOperator,
    GeometricPointOperator,
    QualitativeDecompositionOperator,
    PalindromeDecompositionOperator,
    InverseLimitOperator,
    register_decomposition_operator,
    get_decomposition_operator,
    is_atomic_by_operator,
    DECOMPOSITION_OPERATORS,
)

# ============================================================================
# Autonomous discovery and evolution
# ============================================================================
from .discovery import (
    EvolutionaryFeedbackLoop,
    HeuristicDiscovery,
    DiscoveryProposal,
    auto_discovery_pipeline,
    DensityBasedDecompositionOperator,
    FrequencyDecompositionOperator,
    EntropyDecompositionOperator,
    SparsityDecompositionOperator,
)

# ============================================================================
# Relational density field
# ============================================================================
from .density_field import (
    DensityField,
    InfluenceSample,
)

# ============================================================================
# Self-proving atomicity (formal proof module)
# ============================================================================
from .self_proving import (
    SelfProvingAtomicity,
    TheoremProverType,
    ProofStatus,
    Proof,
    AtomicityTheoremGenerator,
    add_self_proving_capability,
    get_proven_atomicity,
    prove_and_summarise,
)

# ============================================================================
# Public API
# ============================================================================

__all__ = [
    # ---- irreducible_unit: structures ----
    "UltimateObservable",
    "ObservabilityType",
    "GeometricStructure",
    "TopologicalStructure",
    "CategoricalStructure",
    "QuantumStructure",
    "FractalStructure",
    "InformationGeometry",
    "DynamicalSystem",
    "GroupStructure",
    "GradualityType",
    "SymmetryType",
    "GUDHI_AVAILABLE",

    # ---- irreducible_unit: atomicity framework functions ----
    "boolean_atomicity",
    "info_atomicity",
    "decomposition_boolean_atomicity",
    "qualitative_dimensions_atomicity",
    "category_atomicity",
    "group_atomicity",
    "topological_persistence_atomicity",
    "get_framework_names_for_principle",

    # ---- qualitative_dimensions: dimension classes ----
    "QualitativeDimension",
    "ScalarDimension",
    "IntensityDimension",
    "IntensityType",
    "DensityDimension",
    "DensityType",
    "VectorDimension",
    "ColourDimension",
    "ColourSpace",
    "TensorDimension",
    "TextureDimension",
    "TextureType",
    "ComplexDimension",
    "QuaternionDimension",
    "FractalDimension",
    "PatternDimension",
    "PatternType",
    "MultiResolutionDimension",
    "GPUAcceleratedDimension",
    "DimensionType",
    "ResonanceBridge",

    # ---- qualitative_dimensions: utilities ----
    "compute_gradient_numerical",
    "compute_hessian_numerical",
    "gradient_symbolic",
    "DimensionCache",
    "plot_dimension",

    # ---- observables ----
    "Layer1_Observables",

    # ---- meta_spec ----
    "MetaSpecification",
    "DecompositionPrinciple",
    "ObserverDependence",
    "DEFAULT_META_SPEC",
    "PRINCIPLE_OPERATOR_ALIASES",
    "LOGICAL",
    "MEASURE",
    "CATEGORICAL",
    "INFORMATION",
    "GEOMETRIC",
    "QUALITATIVE",
    "register_atomicity_framework",
    "atomicity_framework",
    "ATOMICITY_FRAMEWORKS",

    # ---- decomposition ----
    "DecompositionOperator",
    "ListSplitOperator",
    "StringSplitOperator",
    "DictSplitOperator",
    "ArraySplitOperator",
    "BooleanDecompositionOperator",
    "MeasureDecompositionOperator",
    "CategoricalDecompositionOperator",
    "InformationDecompositionOperator",
    "GeometricDecompositionOperator",
    "GeometricPointOperator",
    "QualitativeDecompositionOperator",
    "PalindromeDecompositionOperator",
    "InverseLimitOperator",
    "register_decomposition_operator",
    "get_decomposition_operator",
    "is_atomic_by_operator",
    "DECOMPOSITION_OPERATORS",

    # ---- discovery ----
    "EvolutionaryFeedbackLoop",
    "HeuristicDiscovery",
    "DiscoveryProposal",
    "auto_discovery_pipeline",
    "DensityBasedDecompositionOperator",
    "FrequencyDecompositionOperator",
    "EntropyDecompositionOperator",
    "SparsityDecompositionOperator",

    # ---- density_field ----
    "DensityField",
    "InfluenceSample",

    # ---- self_proving ----
    "SelfProvingAtomicity",
    "TheoremProverType",
    "ProofStatus",
    "Proof",
    "AtomicityTheoremGenerator",
    "add_self_proving_capability",
    "get_proven_atomicity",
    "prove_and_summarise",
]

__version__ = "3.0.0"
__author__ = "Nexus Ultimate V17 – Layer 1 Foundational Observables"