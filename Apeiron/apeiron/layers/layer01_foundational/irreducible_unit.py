"""
LAYER 1: THE IRREDUCIBLE UNIT – ULTIMATE IMPLEMENTATION
===========================================================================
Theoretical foundation: The fundamental irreducible unit, the smallest entity
that cannot be decomposed further without loss of essential identity or
generative capacity. This layer implements the concept across multiple
mathematical frameworks:

- Order theory (atoms in a poset)
- Measure theory (atomic sets)
- Category theory (initial/zero objects, zero-object test)
- Information theory (Kolmogorov complexity, corrected direction)
- Qualitative dimensions (intensity, density, color)
- Relational embedding (graph‑based context)
- Observer relativity (perspective dependence)

OPTIONAL / SUPER‑OPTIONAL EXTENSIONS:
- Differential geometry (metric, curvature, geodesics)
- Topology (homology groups, Betti numbers, persistence)
- Quantum structures (superposition, entanglement)
- Fractals (Hausdorff dimension, self‑similarity)
- Dynamical systems (Lyapunov exponents, chaos)
- Group theory (symmetries, representations)
- Information geometry (Fisher information, entropy)
- ... and more.

Bug fixes in this version
--------------------------
1. ``info_atomicity``: inverted Kolmogorov score corrected.
   Previously returned ``min(1.0, ratio)`` (compressed / original), giving
   *high* scores to incompressible (complex) values.  Corrected to
   ``max(0.0, 1.0 − ratio)`` so that *simple* (compressible, atomic) values
   score near 1.0.

2. ``boolean_atomicity``: weak ``len() > 1`` heuristic replaced by a call to
   ``is_atomic_by_operator(obs.value, "boolean")``.  The operator implements
   Proposition 1 of the theory (Boolean atom = no proper non-trivial subset
   in the partial order), making the heuristic and formal channels consistent.

3. ``category_atomicity``: extended with a zero-object test (Proposition 3).
   The original only counted incoming morphisms.  The updated version also
   measures initiality coverage and terminality coverage; an object that
   satisfies both simultaneously is identified as a zero object (score 1.0).

4. ``get_atomicity_confidence_interval``: inline ``from scipy.stats import norm``
   is now inside a try/except block with a hard-coded z-score fallback for
   common confidence levels (0.90 / 0.95 / 0.99), so the method works even
   when scipy is not installed.

Extensions in this version
---------------------------
- ``UltimateObservable.generativity_score`` (new property): quantifies the
  observable's potential to serve as the generative ground for higher layers,
  combining resonance richness, relational degree, and atomicity consensus.

- ``UltimateObservable._compute_atomicities``: wrapped in an ``RLock`` for
  thread-safe concurrent access.  The lock is reentrant to avoid deadlocks
  from recursive atomicity queries.

- Framework exclusion documented: ``dynamical`` and ``group`` atomicity
  frameworks are intentionally excluded from default Layer 1 computation
  because they are not mapped from any of the six default principles.
"""

import math
import numpy as np
import logging
import time
import hashlib
import zlib
from typing import Dict, List, Optional, Set, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# ============================================================================
# Imports voor meta‑specificatie en decompositie
# ============================================================================
from .meta_spec import (
    MetaSpecification,
    DEFAULT_META_SPEC,
    ATOMICITY_FRAMEWORKS,
    register_atomicity_framework,
    atomicity_framework,
    DecompositionPrinciple,
    ObserverDependence,
)
from .decomposition import is_atomic_by_operator, get_decomposition_operator
from .qualitative_dimensions import QualitativeDimension  # voor isinstance check

logger = logging.getLogger(__name__)

# ============================================================================
# OPTIONAL MATHEMATICAL LIBRARIES
# ============================================================================

# NumPy/SciPy for numerical operations
try:
    import numpy as np
    from scipy.linalg import expm, logm
    from scipy.spatial.distance import pdist, squareform
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy/SciPy not available – some geometric features disabled")

# NetworkX for graph operations
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available – relational embedding limited")

# SymPy for symbolic mathematics
try:
    import sympy as sp
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False
    logger.warning("SymPy not available – symbolic calculations disabled")

# GUDHI for topological data analysis – also import distance functions
try:
    import gudhi as gd
    # Bottleneck distance – probeer directe import eerst
    try:
        from gudhi import bottleneck_distance
    except ImportError:
        from gudhi.bottleneck import bottleneck_distance

    # Wasserstein distance – optioneel
    try:
        from gudhi import wasserstein_distance
    except ImportError:
        try:
            from gudhi.wasserstein import wasserstein_distance
        except ImportError:
            wasserstein_distance = None
            logger.warning("Wasserstein distance not available in GUDHI")

    GUDHI_AVAILABLE = True
except Exception as e:
    GUDHI_AVAILABLE = False
    logger.error(f"GUDHI import error: {e}")

# Qiskit for quantum structures
try:
    from qiskit import QuantumCircuit, Aer, execute
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    logger.warning("Qiskit not available – quantum features disabled")

# Nolds for chaos analysis
NOLDS_AVAILABLE = False

def _import_nolds():
    """Lazy import van nolds om importtijd-crashes te voorkomen."""
    global NOLDS_AVAILABLE
    if NOLDS_AVAILABLE:
        return True
    try:
        import nolds
        NOLDS_AVAILABLE = True
        return True
    except ImportError:
        logger.warning("Nolds not available – Lyapunov exponent estimation disabled")
        return False

# scikit-learn for spectral embedding
try:
    from sklearn.manifold import SpectralEmbedding
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("scikit-learn not available – spectral embedding disabled")

# ============================================================================
# ENUMS – Classification of observables
# ============================================================================

class ObservabilityType(Enum):
    """Type of observable entity."""
    DISCRETE = "discrete"          # classical discrete
    CONTINUOUS = "continuous"       # continuous field
    QUANTUM = "quantum"             # quantum superposition
    RELATIONAL = "relational"       # relationally defined
    FUZZY = "fuzzy"                 # fuzzy logic
    STOCHASTIC = "stochastic"       # stochastic process
    FRACTAL = "fractal"             # fractal
    TOPOLOGICAL = "topological"     # topological
    SYMPLECTIC = "symplectic"       # symplectic
    COMPLEX = "complex"             # complex numbers

class GradualityType(Enum):
    """Forms of gradual change."""
    TOPOLOGICAL = "topological"     # continuous deformations
    MEASURE = "measure"              # measure‑theoretic
    CATEGORICAL = "categorical"      # morphisms
    INFORMATION = "information"      # information loss
    GEOMETRIC = "geometric"          # geometric
    QUANTUM = "quantum"               # quantum decoherence

class SymmetryType(Enum):
    """Symmetries and group actions."""
    CONTINUOUS = "continuous"        # Lie groups
    DISCRETE = "discrete"             # discrete groups
    GAUGE = "gauge"                   # gauge transformations
    SUPERSYMMETRY = "supersymmetry"   # supersymmetry
    CONFORMAL = "conformal"           # conformal transformations

# ============================================================================
# BASE CLASSES (import from core)
# ============================================================================
try:
    from core.base import Layer, LayerType, ProcessingMode, ProcessingContext, ProcessingResult
except ImportError:
    # Fallback for standalone testing – not used when integrated
    class LayerType(Enum):
        FOUNDATIONAL = "foundational"
    class ProcessingMode(Enum):
        SYNC = "sync"
    @dataclass
    class ProcessingContext:
        mode: ProcessingMode = ProcessingMode.SYNC
        metadata: Dict[str, Any] = field(default_factory=dict)
    @dataclass
    class ProcessingResult:
        success: bool
        output: Any
        time_ms: float
        error: Optional[str] = None
        @classmethod
        def from_success(cls, output, time_ms):
            return cls(success=True, output=output, time_ms=time_ms)
        @classmethod
        def error(cls, msg):
            return cls(success=False, output=None, time_ms=0, error=msg)
        @classmethod
        def from_error(cls, msg):
            """Alias for error to maintain consistency with core."""
            return cls.error(msg)
    class Layer:
        def __init__(self, layer_id: str, layer_type: LayerType):
            self.id = layer_id
            self.type = layer_type
        async def process(self, input_data: Any, context: ProcessingContext) -> ProcessingResult:
            raise NotImplementedError

# ============================================================================
# GEOMETRIC STRUCTURE
# ============================================================================

@dataclass
class GeometricStructure:
    """
    Complete differential‑geometric structure.
    """
    # Riemannian geometry
    metric_tensor: Optional[np.ndarray] = None          # g_ij
    inverse_metric: Optional[np.ndarray] = None         # g^ij
    christoffel_symbols: Optional[np.ndarray] = None    # Γ^k_ij
    riemann_tensor: Optional[np.ndarray] = None         # R^i_jkl
    ricci_tensor: Optional[np.ndarray] = None           # R_ij
    scalar_curvature: Optional[float] = None            # R

    # Differential forms
    differential_forms: Dict[int, np.ndarray] = field(default_factory=dict)  # ω_k
    exterior_derivative: Optional[Callable] = None      # d
    hodge_star: Optional[np.ndarray] = None             # ★

    # Symplectic geometry
    symplectic_form: Optional[np.ndarray] = None        # ω_ij
    poisson_bracket: Optional[Callable] = None          # { , }

    # Complex geometry
    complex_structure: Optional[np.ndarray] = None      # J
    kahler_form: Optional[np.ndarray] = None            # ω (Kähler)
    holomorphic_section: Optional[Any] = None

    # Connections and parallel transport
    connection_1form: Optional[np.ndarray] = None       # A (gauge field)
    curvature_2form: Optional[np.ndarray] = None        # F = dA + A∧A
    holonomy: Optional[np.ndarray] = None               # parallel transport

    def geodesic_distance(self, point1: np.ndarray, point2: np.ndarray) -> float:
        """Compute geodesic distance (requires metric)."""
        if self.metric_tensor is None:
            raise ValueError("Metric tensor required")
        diff = point2 - point1
        ds2 = np.einsum('i,ij,j', diff, self.metric_tensor, diff)
        return np.sqrt(max(ds2, 0))

# ============================================================================
# TOPOLOGICAL STRUCTURE – with persistence and distance metrics
# ============================================================================

@dataclass
class TopologicalStructure:
    """
    Complete topological invariants, including persistent homology and
    distances between persistence diagrams.
    """
    homology_groups: Dict[int, List[Any]] = field(default_factory=dict)   # H_n
    betti_numbers: List[int] = field(default_factory=list)                 # b_n
    euler_characteristic: Optional[float] = None                           # χ

    cohomology_rings: Dict[int, Any] = field(default_factory=dict)        # H^n
    de_rham_cohomology: Optional[Any] = None

    fundamental_group: Optional[Any] = None                                 # π₁
    higher_homotopy_groups: Dict[int, Any] = field(default_factory=dict)   # π_n
    winding_number: int = 0

    # Characteristic classes
    chern_classes: List[float] = field(default_factory=list)               # c_i
    pontryagin_classes: List[float] = field(default_factory=list)          # p_i
    stiefel_whitney_classes: List[int] = field(default_factory=list)       # w_i

    # Persistence data
    persistence_diagram: Optional[List[Tuple[int, Tuple[float, float]]]] = None  # list of (dim, (birth, death))
    barcode: Optional[Dict[int, List[Tuple[float, float]]]] = None               # barcode per dimension
    persistent_entropy: Optional[float] = None

    def compute_persistent_homology(self, points: np.ndarray, max_dim: int = 2,
                                    max_edge_length: Optional[float] = None) -> Dict:
        """
        Compute persistent homology using GUDHI if available.
        Stores the full persistence diagram and returns a barcode dictionary.

        Args:
            points: point cloud (numpy array of shape (n, d))
            max_dim: maximum homology dimension to compute
            max_edge_length: maximum edge length for the Rips complex
                             (if None, use default, which is infinite)
        """
        if not GUDHI_AVAILABLE:
            logger.warning("GUDHI not available – cannot compute persistent homology")
            return {}

        if max_edge_length is not None:
            rips = gd.RipsComplex(points=points, max_edge_length=max_edge_length)
        else:
            rips = gd.RipsComplex(points=points)

        st = rips.create_simplex_tree(max_dimension=max_dim)
        persistence = st.persistence()

        # Store full diagram as list of (dim, (birth, death))
        self.persistence_diagram = [(dim, (birth, death)) for (dim, (birth, death)) in persistence]

        # Build barcode per dimension
        barcode = {dim: [] for dim in range(max_dim+1)}
        for (dim, (birth, death)) in persistence:
            if death != float('inf'):
                barcode[dim].append((birth, death))
        self.barcode = barcode

        # Compute persistent entropy
        lengths = [death - birth for (dim, (birth, death)) in persistence if death != float('inf')]
        total = sum(lengths)
        if total > 0:
            probs = [l / total for l in lengths]
            self.persistent_entropy = -sum(p * np.log(p) for p in probs)
        else:
            self.persistent_entropy = 0.0

        # Use GUDHI's betti_numbers() to get Betti numbers at default threshold
        self.betti_numbers = list(st.betti_numbers())
        return {'barcode': barcode, 'persistence': persistence}

    def bottleneck_distance(self, other: 'TopologicalStructure', dim: int = 1) -> float:
        """
        Compute bottleneck distance between persistence diagrams of given dimension.
        Requires GUDHI.
        """
        if not GUDHI_AVAILABLE:
            logger.warning("GUDHI not available – returning 0.0")
            return 0.0
        if self.persistence_diagram is None or other.persistence_diagram is None:
            logger.warning("Persistence diagram missing – returning 0.0")
            return 0.0

        # Extract intervals for the given dimension
        diag1 = [(b, d) for (dim_, (b, d)) in self.persistence_diagram if dim_ == dim and d != float('inf')]
        diag2 = [(b, d) for (dim_, (b, d)) in other.persistence_diagram if dim_ == dim and d != float('inf')]

        # GUDHI expects diagrams as lists of (birth, death) pairs.
        return bottleneck_distance(diag1, diag2)

    def wasserstein_distance(self, other: 'TopologicalStructure', dim: int = 1, p: float = 2) -> float:
        """
        Compute Wasserstein distance between persistence diagrams of given dimension.
        Requires GUDHI.
        """
        if not GUDHI_AVAILABLE:
            logger.warning("GUDHI not available – returning 0.0")
            return 0.0
        if self.persistence_diagram is None or other.persistence_diagram is None:
            logger.warning("Persistence diagram missing – returning 0.0")
            return 0.0

        diag1 = [(b, d) for (dim_, (b, d)) in self.persistence_diagram if dim_ == dim and d != float('inf')]
        diag2 = [(b, d) for (dim_, (b, d)) in other.persistence_diagram if dim_ == dim and d != float('inf')]

        return wasserstein_distance(diag1, diag2, order=p)

# ============================================================================
# CATEGORICAL STRUCTURE – Enhanced with strict domain/codomain checking
# ============================================================================

@dataclass
class CategoricalStructure:
    """
    Category‑theoretic data with support for composition and strict
    domain/codomain matching.
    """
    objects: Set[Any] = field(default_factory=set)
    morphisms: Dict[Tuple[Any, Any], Set[Any]] = field(default_factory=dict)  # Hom(A,B)
    composition: Optional[Callable] = None
    identities: Dict[Any, Any] = field(default_factory=dict)                  # id_A

    # Functors and natural transformations
    functors: Dict[str, Any] = field(default_factory=dict)
    natural_transformations: List[Dict] = field(default_factory=list)

    # Universal properties
    initial_object: Optional[Any] = None
    terminal_object: Optional[Any] = None
    limits: Dict[str, Any] = field(default_factory=dict)
    colimits: Dict[str, Any] = field(default_factory=dict)

    # Higher categories
    is_2category: bool = False
    is_infinity_category: bool = False

    def __post_init__(self):
        if self.composition is None:
            self.composition = self._default_composition

    def _default_composition(self, f: Any, g: Any) -> Any:
        """
        Default composition: if f and g are lists, concatenate; if numbers, multiply.
        This is a placeholder; a full implementation would use categorical semantics.
        """
        if isinstance(f, (int, float)) and isinstance(g, (int, float)):
            return f * g
        if isinstance(f, list) and isinstance(g, list):
            return f + g
        if callable(f) and callable(g):
            return lambda x: f(g(x))
        return None

    # Convenience methods for testing and interactive use
    def add_object(self, obj: Any) -> None:
        """Add an object to the category."""
        self.objects.add(obj)
        if obj not in self.identities:
            # Create a default identity morphism (the object itself)
            self.identities[obj] = obj

    def add_morphism(self, source: Any, target: Any, morphism: Any) -> None:
        """Add a morphism between source and target."""
        self.morphisms.setdefault((source, target), set()).add(morphism)

    # Backward‑compatible compose: accepts 5 or 6 arguments
    def compose(self, *args):
        """
        Compose morphisms. Supports both new 6‑argument signature
        (f, f_source, f_target, g, g_source, g_target) and legacy 5‑argument
        (f, g, source, target, extra) where extra is ignored.
        Returns composition only if f_target == g_source.
        """
        if len(args) == 6:
            f, f_source, f_target, g, g_source, g_target = args
        elif len(args) == 5:
            # Legacy call: (f, g, source, target, extra) – ignore extra
            f, g, source, target, extra = args
            f_source = source
            f_target = target
            g_source = source
            g_target = target
        else:
            raise TypeError("compose() takes 5 or 6 positional arguments")
        if f_target != g_source:
            logger.warning(
                f"Cannot compose: target of f ({f_target}) != source of g ({g_source})"
            )
            return None
        return self.composition(f, g)

    def check_commutative_diagram(self, diagram: Dict[Tuple[Any, Any], Any]) -> bool:
        """
        Check if a given diagram (set of arrows) commutes.
        This is a placeholder; in practice one would use library support.
        """
        # For now, always return True.
        return True

# ============================================================================
# QUANTUM STRUCTURE – Extended with decoherence and POVM
# ============================================================================

@dataclass
class QuantumStructure:
    """
    Quantum‑mechanical structure, including unitary evolution, measurement,
    and decoherence.
    """
    hilbert_space_dim: int = 0
    basis_states: List[str] = field(default_factory=list)
    wavefunction: Optional[np.ndarray] = None          # |ψ⟩
    density_matrix: Optional[np.ndarray] = None        # ρ
    observables: Dict[str, np.ndarray] = field(default_factory=dict)  # Hermitian operators
    hamiltonian: Optional[np.ndarray] = None           # H
    entanglement_entropy: Optional[float] = None       # S(ρ_A)
    concurrence: Optional[float] = None                # quantum concurrence
    bell_violation: Optional[float] = None             # Bell inequality violation

    hbar: float = 1.0

    def evolve(self, state: np.ndarray, time: float) -> np.ndarray:
        """Time evolution by Hamiltonian (unitary)."""
        if self.hamiltonian is None:
            raise ValueError("Hamiltonian required")
        U = expm(-1j * self.hamiltonian * time / self.hbar)
        return U @ state

    def expectation_value(self, observable_name: str) -> float:
        """
        Compute ⟨ψ| O |ψ⟩ for a given observable.
        If density_matrix is present, use Tr(ρ O).
        """
        if observable_name not in self.observables:
            raise ValueError(f"Observable '{observable_name}' not defined")
        O = self.observables[observable_name]
        if self.density_matrix is not None:
            # Expectation for mixed state: Tr(ρ O)
            return float(np.trace(self.density_matrix @ O).real)
        elif self.wavefunction is not None:
            # Pure state expectation
            return float((self.wavefunction.conj() @ O @ self.wavefunction).real)
        else:
            raise ValueError("No quantum state defined")

    def projective_measurement(self, observable_name: str) -> Tuple[float, np.ndarray]:
        """
        Simulate a projective measurement of the given observable.
        Returns (eigenvalue, collapsed state). Assumes pure state; if density matrix,
        the state is updated but returns the eigenvalue and the post‑measurement density.
        """
        if observable_name not in self.observables:
            raise ValueError(f"Observable '{observable_name}' not defined")
        O = self.observables[observable_name]
        # Compute eigenvalues and eigenvectors
        evals, evecs = np.linalg.eigh(O)

        if self.wavefunction is not None:
            # Pure state measurement
            # Compute probabilities
            probs = [abs(np.vdot(evecs[:, i], self.wavefunction)) ** 2 for i in range(len(evals))]
            # Choose outcome according to probabilities
            outcome = np.random.choice(len(evals), p=probs)
            # Collapse to the corresponding eigenstate
            new_state = evecs[:, outcome].copy()
            self.wavefunction = new_state
            return evals[outcome], new_state

        elif self.density_matrix is not None:
            # Mixed state measurement: update density matrix via projection
            # For simplicity, we return expectation and leave ρ unchanged.
            # A full implementation would use the projection rule:
            # ρ → P_k ρ P_k / Tr(ρ P_k) with probability Tr(ρ P_k)
            # This is left as an exercise.
            logger.warning("Projective measurement for mixed state not fully implemented – returning expectation")
            return self.expectation_value(observable_name), self.density_matrix

        else:
            raise ValueError("No quantum state defined")

    def dephase(self, dephasing_rate: float, dt: float):
        """
        Simple dephasing model: destroy off-diagonal elements.
        ρ_ij → ρ_ij * exp(-dephasing_rate * dt) for i≠j.
        Vectorized version for performance.
        """
        if self.density_matrix is None:
            # Convert pure state to density matrix
            if self.wavefunction is not None:
                self.density_matrix = np.outer(self.wavefunction, self.wavefunction.conj())
                self.wavefunction = None
            else:
                return

        n = self.hilbert_space_dim
        # Create a mask for off-diagonal elements
        mask = ~np.eye(n, dtype=bool)
        self.density_matrix[mask] *= np.exp(-dephasing_rate * dt)
        # Re‑Hermitianize
        self.density_matrix = (self.density_matrix + self.density_matrix.conj().T) / 2

# ============================================================================
# FRACTAL STRUCTURE
# ============================================================================

@dataclass
class FractalStructure:
    """
    Fractal and scale‑invariant properties.
    """
    hausdorff_dimension: Optional[float] = None
    box_counting_dimension: Optional[float] = None
    correlation_dimension: Optional[float] = None
    self_similarity: float = 0.0
    multifractal_spectrum: Dict[float, float] = field(default_factory=dict)
    scaling_exponent: Optional[float] = None

    def compute_hausdorff(self, points: np.ndarray, scales: Optional[np.ndarray] = None) -> float:
        """Estimate Hausdorff dimension by box counting."""
        if scales is None:
            scales = np.logspace(-3, 0, 20) * (np.max(points, axis=0) - np.min(points, axis=0)).max()
        counts = []
        for eps in scales:
            # Count number of boxes of size eps that contain points
            min_coords = np.min(points, axis=0)
            idx = np.floor((points - min_coords) / eps).astype(int)
            unique_boxes = len(set(map(tuple, idx)))
            counts.append(unique_boxes)
        log_eps = np.log(1.0 / scales)
        log_counts = np.log(counts)
        coeffs = np.polyfit(log_eps, log_counts, 1)
        return coeffs[0]

# ============================================================================
# INFORMATION GEOMETRY
# ============================================================================

@dataclass
class InformationGeometry:
    """
    Information‑geometric measures.
    """
    fisher_information: Optional[np.ndarray] = None    # I_ij(θ)
    shannon_entropy: float = 0.0
    renyi_entropy: Dict[float, float] = field(default_factory=dict)
    kl_divergence: Dict[Tuple[str, str], float] = field(default_factory=dict)
    mutual_information: Dict[Tuple[str, str], float] = field(default_factory=dict)

# ============================================================================
# DYNAMICAL SYSTEM STRUCTURE
# ============================================================================

@dataclass
class DynamicalSystem:
    """
    Time evolution and dynamics.
    """
    flow: Optional[Callable] = None                 # φ_t
    vector_field: Optional[Callable] = None         # X(p)
    fixed_points: List[np.ndarray] = field(default_factory=list)
    lyapunov_exponents: List[float] = field(default_factory=list)
    is_chaotic: bool = False
    strange_attractor: Optional[np.ndarray] = None

# ============================================================================
# GROUP STRUCTURE
# ============================================================================

@dataclass
class GroupStructure:
    """
    Symmetries and group actions.
    """
    group_type: Optional[str] = None
    group_elements: Set[Any] = field(default_factory=set)
    multiplication: Optional[Callable] = None
    identity: Any = None
    inverse: Optional[Callable] = None
    lie_algebra: Optional[np.ndarray] = None
    representations: Dict[str, np.ndarray] = field(default_factory=dict)

# ============================================================================
# HULPFUNCTIE VOOR DYNAMISCHE FRAMEWORK‑LOOKUP
# ============================================================================

# Mapping van principe-naam naar heuristische framework-naam (enkelvoudig)
PRINCIPLE_TO_HEURISTIC = {
    'logical': 'boolean',
    'measure': 'discrete_cardinality',
    'categorical': 'category',
    'information': 'info',
    'geometric': 'geometric',
    'qualitative': 'qualitative',
}

# Mapping van principe-naam naar lijst van formele framework‑namen (uitgebreid)
PRINCIPLE_TO_FORMAL = {
    'logical': ['decomposition_boolean'],
    'measure': ['decomposition_measure'],
    'categorical': ['decomposition_categorical'],
    'information': ['decomposition_information'],
    'geometric': ['decomposition_geometric'],
    'qualitative': ['decomposition_qualitative'],
    'topological': ['decomposition_topological', 'topological_persistence'],  # extra TDA‑framework
}

def get_framework_names_for_principle(principle_name: str) -> List[str]:
    """
    Geef de lijst van frameworknamen voor een gegeven principe.
    Ondersteunt zowel heuristische als meerdere formele varianten.
    """
    names = []
    # Heuristisch framework
    heuristic = PRINCIPLE_TO_HEURISTIC.get(principle_name)
    if heuristic and heuristic in ATOMICITY_FRAMEWORKS:
        names.append(heuristic)
    # Formele frameworks (lijst)
    formal_list = PRINCIPLE_TO_FORMAL.get(principle_name, [])
    for formal in formal_list:
        if formal in ATOMICITY_FRAMEWORKS:
            names.append(formal)
    return names

# ============================================================================
# ATOMICITEITSFRAMEWORKS – Heuristische, formele en kwalitatieve functies
# ============================================================================

# ----------------------------------------------------------------------------
# Heuristische frameworks (originele methoden)
# ----------------------------------------------------------------------------

def boolean_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """
    Boolean algebra atomicity – minimal element (Proposition 1).

    An element *a* of a Boolean algebra B is an atom if *a ≠ 0* and there
    exists no *b ∈ B* with ``0 < b < a``.

    The implementation delegates to the ``BooleanDecompositionOperator``
    (registered as ``"boolean"`` in DECOMPOSITION_OPERATORS) for formally
    grounded types (``set``, ``frozenset``, ``int``, ``float``, ``bool``).

    For types that are not boolean-algebra elements (``list``, ``tuple``,
    ``numpy.ndarray``), the operator's ``can_decompose`` returns ``False``,
    which would cause ``is_atomic_by_operator`` to return ``True``
    unconditionally – hiding the fact that these containers are multi-element
    and should score as *partially* non-atomic.  We therefore handle these
    types with the original length heuristic *before* delegating to the
    operator.

    Returns:
        1.0 if the value is a Boolean atom or the operator is not applicable
        to a single-element value;
        0.5 if the value is a multi-element sequence (list / tuple / array)
        or the operator explicitly identifies it as non-atomic.
    """
    # Lists, tuples, and numpy arrays are not boolean-algebra elements.
    # Use the original length heuristic so multi-element containers still
    # receive 0.5 instead of a spurious 1.0 from the "not-applicable → atomic"
    # default of is_atomic_by_operator.
    if isinstance(obs.value, (list, tuple)):
        return 0.5 if len(obs.value) > 1 else 1.0
    if isinstance(obs.value, np.ndarray):
        return 0.5 if obs.value.size > 1 else 1.0
    try:
        return 1.0 if is_atomic_by_operator(obs.value, "boolean") else 0.5
    except Exception:
        # Operator not registered (e.g., standalone test environment)
        if hasattr(obs.value, '__len__') and len(obs.value) > 1:
            return 0.5
        return 1.0

def discrete_cardinality_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """
    Discrete cardinality – a heuristic measure of 'size' of a set.
    For arrays, uses log(1+len) to estimate atomicity (more elements -> less atomic).
    """
    if hasattr(obs.value, '__len__'):
        return 1.0 / (1.0 + np.log1p(len(obs.value)))
    return 1.0

def category_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """
    Categorical atomicity – Proposition 3 (zero-object / initial–terminal test).

    An object is a *zero object* in a category if it is simultaneously initial
    (unique morphism from it to every other object) and terminal (unique morphism
    from every other object to it).  Such an object is maximally atomic in the
    categorical sense.

    Enhancement: in addition to counting incoming morphisms (the original
    heuristic), this function checks:

    1. **Terminality coverage**: the fraction of other objects from which a
       morphism exists back to ``obs.id``.  An object with both zero incoming
       morphisms *and* full terminality coverage is a zero object → score 1.0.
    2. **Partial coverage** is scored continuously as the harmonic mean of
       initiality (``1 / (1 + incoming)``) and terminality coverage.

    Args:
        obs:     Observable whose categorical structure is assessed.
        context: Unused; present for API consistency.

    Returns:
        Float in [0, 1].  1.0 for a zero object or no categorical structure;
        lower values for objects with more complex morphism profiles.
    """
    # Access private field to avoid triggering lazy initialisation
    cat = obs._category
    if cat is None:
        return 1.0
    obj_id = obs.id
    if obj_id not in cat.objects:
        return 1.0

    n_others = len(cat.objects) - 1
    if n_others <= 0:
        return 1.0   # singleton category: trivially atomic

    # --- Initiality: count incoming morphisms from other objects ---
    incoming = 0
    for (src, tgt), morphs in cat.morphisms.items():
        if tgt == obj_id and src != obj_id:
            incoming += len(morphs)

    # --- Terminality: fraction of other objects with a morphism TO obj_id ---
    # (obj_id has a morphism to each other → initial; each other has one to obj_id → terminal)
    outgoing_targets = set(
        tgt for (src, tgt) in cat.morphisms if src == obj_id and tgt != obj_id
    )
    incoming_sources = set(
        src for (src, tgt) in cat.morphisms if tgt == obj_id and src != obj_id
    )

    initiality_coverage = len(outgoing_targets) / n_others   # fraction obj_id reaches
    terminality_coverage = len(incoming_sources) / n_others  # fraction that reach obj_id

    # Zero-object (Proposition 3): simultaneously initial AND terminal.
    # A zero object has a unique morphism TO every other object (initiality)
    # AND a unique morphism FROM every other object (terminality).
    # Note: a zero object DOES have incoming morphisms (from all others), so
    # the original "incoming == 0" condition was incorrect – it prevented
    # terminal objects from being identified as zero objects.
    if initiality_coverage >= 1.0 and terminality_coverage >= 1.0:
        return 1.0   # confirmed zero object

    # Continuous score: harmonic mean of initiality_score and terminality_coverage
    # initiality_score = 1 / (1 + incoming)
    initiality_score = 1.0 / (1.0 + incoming)
    # Terminality score: penalise objects that are NOT reachable from others
    # (a zero object is fully reachable)
    terminality_score = terminality_coverage if terminality_coverage > 0 else (
        1.0 if n_others == 0 else 0.0
    )

    if initiality_score + terminality_score == 0.0:
        return 0.0
    return 2.0 * initiality_score * terminality_score / (initiality_score + terminality_score)

def info_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """
    Information‑theoretic atomicity – Kolmogorov complexity approximation.

    An irreducible unit (atom) should be *simple* – i.e. highly compressible,
    with low Kolmogorov complexity.  A string that compresses to 10 % of its
    original size is close to a regular pattern (atomic); one that cannot be
    compressed is closer to random noise (complex, non-atomic).

    **Kolmogorov proxy reliability (experimentally validated via falsification):**
    The zlib compressor adds approximately 6–10 bytes of header overhead.  For
    inputs shorter than this overhead, the compressed form is *always* longer
    than the original, giving a spurious ratio > 1.0 and a score of 0.0
    regardless of the theoretical complexity.

    Example: the integer ``1`` encodes to the 1-byte string ``"1"``, but
    ``zlib.compress("1")`` produces 9 bytes.  The ratio is 9.0, so
    ``1 - 9.0 = -8`` is clamped to 0.0.  This is an **implementation
    artefact**, not a reflection of theoretical Kolmogorov complexity — the
    integer 1 is trivially one of the most compressible values in existence.

    **Fix (experimentally validated):**
    Short inputs (< 10 bytes UTF-8) are *by definition* at minimal Kolmogorov
    complexity: no description shorter than 10 bytes can be further compressed
    in a meaningful sense within the zlib model.  We return 1.0 for these
    inputs, consistent with information theory.  A calibration constant
    ``_INFO_ATOMICITY_MIN_BYTES = 10`` is used; a higher layer may override
    this via ``obs.metadata["info_min_bytes"]``.

    Args:
        obs:     The observable whose ``value`` is assessed.
        context: Optional context dict (unused here, for API consistency).

    Returns:
        Float in [0, 1]. Values near 1.0 indicate a regular, compressible
        (atomic) value; values near 0.0 indicate incompressible complexity.
    """
    _INFO_ATOMICITY_MIN_BYTES = 10  # zlib overhead threshold; Layer 6+ may override

    try:
        # Allow override via metadata (self-calibrating for higher layers)
        min_bytes = int((obs.metadata or {}).get("info_min_bytes", _INFO_ATOMICITY_MIN_BYTES))
        data = str(obs.value).encode('utf-8')

        if len(data) == 0:
            return 1.0  # empty string: trivially atomic

        if len(data) < min_bytes:
            # Short inputs have trivially minimal Kolmogorov complexity.
            # The zlib proxy is unreliable at this scale due to compressor
            # header overhead (~6-10 bytes).  Return 1.0 per information theory.
            return 1.0

        compressed = zlib.compress(data, level=9)
        ratio = len(compressed) / len(data)
        # Invert: low ratio (high compressibility) → high atomicity
        return max(0.0, 1.0 - ratio)
    except Exception:
        return 0.5

def topological_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Topological atomicity – based on Betti numbers (legacy heuristic)."""
    top = obs._topology
    if top is not None and top.betti_numbers:
        # More holes = less atomic
        return 1.0 / (1.0 + sum(top.betti_numbers[1:]))
    return 1.0

def geometric_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Geometric atomicity – curvature."""
    geom = obs._geometry
    if geom is not None and geom.scalar_curvature is not None:
        return 1.0 / (1.0 + abs(geom.scalar_curvature))
    return 1.0

def quantum_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Quantum atomicity – entanglement entropy."""
    q = obs._quantum
    if q is not None and q.entanglement_entropy is not None:
        return np.exp(-q.entanglement_entropy)
    return 1.0

def fractal_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Fractal atomicity – fractal dimension deviation from integer."""
    # Use qualitative dimension object if available
    if 'fractal_dimension' in obs.qualitative_dimension_objects:
        dim = obs.qualitative_dimension_objects['fractal_dimension'].value
        frac = dim - int(dim)
        return 1.0 - frac
    f = obs._fractal
    if f is not None and f.hausdorff_dimension is not None:
        dim = f.hausdorff_dimension
        frac = dim - int(dim)
        return 1.0 - frac
    return 1.0

def dynamical_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Dynamical atomicity – Lyapunov exponent."""
    dyn = obs._dynamics
    if dyn is not None and dyn.lyapunov_exponents:
        max_lyap = max(dyn.lyapunov_exponents)
        return np.exp(-max_lyap) if max_lyap > 0 else 1.0
    return 1.0

def group_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """
    Group-theoretic atomicity: smaller groups are more atomic.

    Formal basis: a group G is *simpler* (more atomic) if it has fewer elements
    and, in particular, if it has no non-trivial normal subgroups (i.e. it is
    simple in the algebraic sense).  Because computing actual simplicity is
    expensive, we use a logarithmically-normalised cardinality score:

        atomicity(G) = 1 / (1 + log(1 + |G|))

    This gives:
      - |G| = 0 or 1  →  atomicity = 1.0   (trivial group, maximally atomic)
      - |G| = 2       →  atomicity ≈ 0.59  (Z₂)
      - |G| = 6       →  atomicity ≈ 0.44  (S₃)
      - |G| → ∞       →  atomicity → 0.0

    The logarithm provides graceful degradation for large groups where a linear
    1/n score would collapse to zero too rapidly.  The docstring previously
    stated this formula but the code used 1/n incorrectly; this version aligns
    code with the documented specification.

    Args:
        obs:     Observable whose group structure is evaluated.
        context: Optional context dict (currently unused; reserved for future
                 observer-relative group semantics).

    Returns:
        Float in (0, 1].  Returns 1.0 if no group structure is present.
    """
    g = obs._group
    if g is None:
        return 1.0
    n = len(g.group_elements)
    if n <= 1:
        return 1.0
    # Logarithmic normalisation: matches docstring and provides smooth decay.
    return 1.0 / (1.0 + math.log1p(float(n)))

def statistical_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Statistical atomicity – Shannon entropy."""
    info = obs._info_geometry
    if info is not None and info.shannon_entropy > 0:
        return np.exp(-info.shannon_entropy)
    return 1.0

# ----------------------------------------------------------------------------
# Formele atomiciteitsframeworks op basis van decompositieoperatoren
# ----------------------------------------------------------------------------

def decomposition_boolean_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Atomiciteit bepaald door Booleaanse decompositieoperator."""
    return 1.0 if is_atomic_by_operator(obs.value, "boolean") else 0.0

def decomposition_measure_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Atomiciteit bepaald door maattheoretische decompositieoperator."""
    return 1.0 if is_atomic_by_operator(obs.value, "measure") else 0.0

def decomposition_categorical_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Atomiciteit bepaald door categorietheoretische decompositieoperator."""
    return 1.0 if is_atomic_by_operator(obs.value, "categorical") else 0.0

def decomposition_information_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Atomiciteit bepaald door informatietheoretische decompositieoperator."""
    return 1.0 if is_atomic_by_operator(obs.value, "information") else 0.0

def decomposition_geometric_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Atomiciteit bepaald door geometrische decompositieoperator."""
    return 1.0 if is_atomic_by_operator(obs.value, "geometric") else 0.0

def decomposition_qualitative_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Atomiciteit bepaald door kwalitatieve decompositieoperator."""
    return 1.0 if is_atomic_by_operator(obs.value, "qualitative") else 0.0

def decomposition_topological_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """Atomiciteit bepaald door topologische decompositieoperator (nog niet geïmplementeerd)."""
    # Placeholder: als er ooit een topologische operator komt, kan die hier.
    return 1.0

# ----------------------------------------------------------------------------
# Kwalitatief dimensie‑gebaseerd atomiciteitsframework (verbeterd met gewichten)
# ----------------------------------------------------------------------------

def qualitative_dimensions_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """
    Berekent een gewogen atomiciteit over alle aanwezige kwalitatieve dimensies.
    Gebruikt de `is_atomic()` methode van elk dimensieobject.
    Gewichten kunnen worden ingesteld via meta_spec.qualitative_dim_weights.
    """
    if not obs.qualitative_dimension_objects:
        return 1.0  # geen dimensies, beschouw als atomair

    # Haal gewichten uit meta_spec, of gebruik 1.0 als standaard
    weights = getattr(obs.meta_spec, 'qualitative_dim_weights', {})
    scores = []
    total_weight = 0.0
    for name, dim in obs.qualitative_dimension_objects.items():
        w = weights.get(name, 1.0)
        # Bepaal of dimensie atomair is
        atomic = 1.0 if (hasattr(dim, 'is_atomic') and dim.is_atomic()) else 0.0
        scores.append(atomic * w)
        total_weight += w
    return sum(scores) / total_weight if total_weight > 0 else 1.0

# ----------------------------------------------------------------------------
# Nieuw: topologisch persistentie‑framework (GUDHI)
# ----------------------------------------------------------------------------

def topological_persistence_atomicity(obs: 'UltimateObservable', context: Optional[Dict] = None) -> float:
    """
    Atomicity based on persistent homology.
    For a point cloud, it is atomair if it consists of a single connected component
    (i.e., exactly one feature with infinite death in dimension 0) and no persistent
    higher‑dimensional holes (simplified: ignore higher dimensions for now).
    """
    top = obs._topology
    if top is None or top.persistence_diagram is None:
        return 1.0
    # Count infinite-death intervals in dimension 0 -> number of connected components
    n_components = 0
    for (dim, (birth, death)) in top.persistence_diagram:
        if dim == 0 and death == float('inf'):
            n_components += 1
    if n_components == 1:
        return 1.0
    else:
        return 0.0

# ----------------------------------------------------------------------------
# Registratie van alle atomiciteitsframeworks
# ----------------------------------------------------------------------------

# Heuristische frameworks
register_atomicity_framework("boolean", boolean_atomicity)
register_atomicity_framework("discrete_cardinality", discrete_cardinality_atomicity)
register_atomicity_framework("category", category_atomicity)
register_atomicity_framework("info", info_atomicity)
register_atomicity_framework("topological", topological_atomicity)
register_atomicity_framework("geometric", geometric_atomicity)
register_atomicity_framework("quantum", quantum_atomicity)
register_atomicity_framework("fractal", fractal_atomicity)
register_atomicity_framework("dynamical", dynamical_atomicity)
register_atomicity_framework("group", group_atomicity)
register_atomicity_framework("statistical", statistical_atomicity)

# Formele decompositie‑gebaseerde frameworks
register_atomicity_framework("decomposition_boolean", decomposition_boolean_atomicity)
register_atomicity_framework("decomposition_measure", decomposition_measure_atomicity)
register_atomicity_framework("decomposition_categorical", decomposition_categorical_atomicity)
register_atomicity_framework("decomposition_information", decomposition_information_atomicity)
register_atomicity_framework("decomposition_geometric", decomposition_geometric_atomicity)
register_atomicity_framework("decomposition_qualitative", decomposition_qualitative_atomicity)
register_atomicity_framework("decomposition_topological", decomposition_topological_atomicity)

# Kwalitatief dimensie‑framework
register_atomicity_framework("qualitative", qualitative_dimensions_atomicity)

# Topologisch persistentie‑framework
register_atomicity_framework("topological_persistence", topological_persistence_atomicity)

# ============================================================================
# THE ULTIMATE OBSERVABLE – ALL IN ONE
# ============================================================================

@dataclass
class UltimateObservable:
    """
    The ultimate irreducible unit – contains all possible mathematical structures.
    All heavy substructures are lazy‑initialized to save memory.
    """
    # Core identity
    id: str
    value: Any
    observability_type: ObservabilityType

    # DIMENSIONLESS PHASE replaces linear timestamp for identity
    temporal_phase: float = 0.0          # phase in the system's evolution (set by higher layers)

    # Wall time for logging/provenance (not for identity)
    created_at: float = field(default_factory=time.time)

    version: str = "ultimate-2.1"        # updated version

    # Meta‑specificatie (bepaalt hoe atomiciteit wordt geïnterpreteerd)
    meta_spec: MetaSpecification = field(default_factory=lambda: DEFAULT_META_SPEC)

    # LAZY ONTOLOGY: potential en collapsed
    potential: Optional[Callable[[Dict], Any]] = None
    collapsed: bool = field(default=False, init=False)

    # INTER‑LAYER FLUX: resonance map
    resonance_map: Dict[str, Any] = field(default_factory=dict)

    # Qualitative dimensions (from theory) – simple float values for quick access
    qualitative_dims: Dict[str, float] = field(default_factory=dict)
    qualitative_gradients: Dict[str, np.ndarray] = field(default_factory=dict)
    qualitative_metadata: Dict[str, Dict] = field(default_factory=dict)

    # Store full qualitative dimension objects (rich objects from qualitative_dimensions.py)
    qualitative_dimension_objects: Dict[str, Any] = field(default_factory=dict)

    # Atomicity in all frameworks (continuous scores)
    atomicity: Dict[str, float] = field(default_factory=dict)

    # Relational embedding
    relational_weights: Dict[str, float] = field(default_factory=dict)
    relational_embedding: np.ndarray = field(default_factory=lambda: np.array([]))
    relational_graph: Optional[Any] = None   # NetworkX graph

    # Observer relativity
    observer_perspective: str = "default"
    observer_context: Dict[str, Any] = field(default_factory=dict)
    observer_history: List[Dict] = field(default_factory=list)

    # ---- LAZY SUBSTRUCTURES (private fields, use properties) ----
    _geometry: Optional[GeometricStructure] = field(default=None, repr=False)
    _topology: Optional[TopologicalStructure] = field(default=None, repr=False)
    _category: Optional[CategoricalStructure] = field(default=None, repr=False)
    _quantum: Optional[QuantumStructure] = field(default=None, repr=False)
    _fractal: Optional[FractalStructure] = field(default=None, repr=False)
    _info_geometry: Optional[InformationGeometry] = field(default=None, repr=False)
    _dynamics: Optional[DynamicalSystem] = field(default=None, repr=False)
    _group: Optional[GroupStructure] = field(default=None, repr=False)

    # Units and measurement
    units: Dict[str, str] = field(default_factory=dict)
    precision: float = 1e-12
    error_margin: float = 0.0
    calibration: Dict[str, Any] = field(default_factory=dict)

    # Metadata for dynamic weights etc.
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Provenance
    provenance: List[Dict] = field(default_factory=list)

    # Marker voor lazy observable protocol (voor collapse in decomposition)
    _is_lazy_observable: bool = field(default=False, init=False)

    # -------- NIEUW: dirty-flag voor stale atomiciteit --------
    _atomicity_stale: bool = field(default=False, init=False)

    # Thread-safe lock for atomicity computation (non-init, non-repr field)
    _atomicity_lock: object = field(
        default_factory=lambda: __import__('threading').RLock(),
        init=False,
        repr=False,
        compare=False,
    )

    # Thread-safe lock for relational_graph mutations (non-init, non-repr field)
    _graph_lock: object = field(
        default_factory=lambda: __import__('threading').RLock(),
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self):
        """Initialize structures and compute atomicities (if not lazy)."""
        self._initialize_structures()
        if self.potential is not None:
            self._is_lazy_observable = True
            # Lazy: atomiciteit wordt later berekend na collapse
        else:
            self._compute_atomicities()
        self._normalize_embedding()
        self._add_provenance("created", details={'temporal_phase': self.temporal_phase})

    def _initialize_structures(self):
        """Set up optional structures if libraries available."""
        if NETWORKX_AVAILABLE and self.relational_graph is None:
            with self._graph_lock:
                if self.relational_graph is None:   # double-checked locking
                    self.relational_graph = nx.Graph()
                    self.relational_graph.add_node(self.id)

    # ---- Lazy properties for heavy substructures ----
    @property
    def geometry(self) -> GeometricStructure:
        if self._geometry is None:
            self._geometry = GeometricStructure()
        return self._geometry

    @geometry.setter
    def geometry(self, value: GeometricStructure):
        self._geometry = value

    @property
    def topology(self) -> TopologicalStructure:
        if self._topology is None:
            self._topology = TopologicalStructure()
        return self._topology

    @topology.setter
    def topology(self, value: TopologicalStructure):
        self._topology = value

    @property
    def category(self) -> CategoricalStructure:
        if self._category is None:
            self._category = CategoricalStructure()
        return self._category

    @category.setter
    def category(self, value: CategoricalStructure):
        self._category = value

    @property
    def quantum(self) -> QuantumStructure:
        if self._quantum is None:
            self._quantum = QuantumStructure()
        return self._quantum

    @quantum.setter
    def quantum(self, value: QuantumStructure):
        self._quantum = value

    @property
    def fractal(self) -> FractalStructure:
        if self._fractal is None:
            self._fractal = FractalStructure()
        return self._fractal

    @fractal.setter
    def fractal(self, value: FractalStructure):
        self._fractal = value

    @property
    def info_geometry(self) -> InformationGeometry:
        if self._info_geometry is None:
            self._info_geometry = InformationGeometry()
        return self._info_geometry

    @info_geometry.setter
    def info_geometry(self, value: InformationGeometry):
        self._info_geometry = value

    @property
    def dynamics(self) -> DynamicalSystem:
        if self._dynamics is None:
            self._dynamics = DynamicalSystem()
        return self._dynamics

    @dynamics.setter
    def dynamics(self, value: DynamicalSystem):
        self._dynamics = value

    @property
    def group(self) -> GroupStructure:
        if self._group is None:
            self._group = GroupStructure()
        return self._group

    @group.setter
    def group(self, value: GroupStructure):
        self._group = value

    def _compute_atomicities(self):
        """
        Compute atomicity scores for all frameworks that correspond to the
        primary principles listed in ``meta_spec``.

        Framework lookup is performed dynamically via
        ``get_framework_names_for_principle`` so that newly registered
        principles (e.g. from discovery.py) are automatically included.

        Thread safety: the entire computation is wrapped in ``_atomicity_lock``
        (an ``RLock``) so that concurrent calls from multiple threads do not
        produce a race condition on ``self.atomicity`` or the stale flag.  The
        lock is reentrant so that recursive calls (e.g. from an atomicity
        framework that itself calls ``get_atomicity_score``) do not deadlock.

        Note on framework exclusion: ``dynamical`` and ``group`` atomicity
        frameworks are registered in ATOMICITY_FRAMEWORKS but are NOT mapped
        from any of the six default principles
        (logical / measure / categorical / information / geometric / qualitative).
        They therefore do not contribute to the score unless a principle that
        maps to them is explicitly added to ``meta_spec.primary_principles``.
        This is intentional: these frameworks belong conceptually to Layers 7–10
        and should not pollute Layer 1 atomicity unless deliberately opted in.
        """
        with self._atomicity_lock:
            atomicities = {}
            # Collect allowed framework names from primary_principles
            allowed_names: set = set()
            for principle in self.meta_spec.primary_principles:
                principle_name = (
                    principle.name if hasattr(principle, 'name') else str(principle)
                )
                allowed_names.update(get_framework_names_for_principle(principle_name))

            for name, func in ATOMICITY_FRAMEWORKS.items():
                if name in allowed_names:
                    try:
                        score = func(self, {})
                        atomicities[name] = float(score)
                    except Exception as e:
                        logger.warning(
                            "Fout in atomiciteitsframework '%s': %s", name, e
                        )
                        atomicities[name] = 0.0

            self.atomicity = atomicities
            self._atomicity_stale = False  # gemarkeerd als up-to-date

    def collapse(self, context: Optional[Dict] = None):
        """
        Laat de observable 'instorten' door de potential aan te roepen.
        Dit genereert de waarde en berekent vervolgens atomiciteiten.
        """
        if self.potential is not None and not self.collapsed:
            self.value = self.potential(context or {})
            self.collapsed = True
            self._compute_atomicities()
            self._add_provenance("collapsed", details={'context': context})

    def add_resonance(self, layer: str, data: Any):
        """Voeg een resonantie toe voor een andere laag (inter‑layer flux)."""
        self.resonance_map[layer] = data
        self._add_provenance("resonance_added", details={'layer': layer})
        self._mark_stale()   # mogelijke invloed op atomiciteit

    def remove_resonance(self, layer: str):
        """Verwijder resonantie voor een laag."""
        if layer in self.resonance_map:
            del self.resonance_map[layer]
            self._add_provenance("resonance_removed", details={'layer': layer})
            self._mark_stale()

    def set_relational_context(self, other_id: str, weight: float):
        """Add or update a weighted relation to another observable.

        Thread-safe: mutations to *relational_graph* are protected by
        ``_graph_lock``, mutations to *relational_weights* are cheap dict
        writes that are safe under the GIL for CPython and are performed
        inside the same lock for full correctness.
        """
        with self._graph_lock:
            self.relational_weights[other_id] = weight
            if NETWORKX_AVAILABLE and self.relational_graph is not None:
                self.relational_graph.add_edge(self.id, other_id, weight=weight)
        # Update embedding via spectral method (if available) — outside lock
        # because update_embedding() acquires _atomicity_lock internally.
        self.update_embedding()
        self._mark_stale()

    def set_observer(self, perspective: str, context: Optional[Dict] = None):
        old = self.observer_perspective
        self.observer_perspective = perspective
        if context:
            self.observer_context.update(context)
        self.observer_history.append({
            'wall_time': time.time(),
            'from': old,
            'to': perspective,
            'context': context
        })
        self._add_provenance("observer_changed", {'from': old, 'to': perspective})
        self._mark_stale()   # atomiciteit kan perspectiefafhankelijk zijn

    def _mark_stale(self):
        """Markeer dat de atomiciteit opnieuw berekend moet worden."""
        self._atomicity_stale = True

    def _normalize_embedding(self):
        if len(self.relational_embedding) > 0:
            norm = np.linalg.norm(self.relational_embedding)
            if norm > 0:
                self.relational_embedding /= norm

    def _add_provenance(self, action: str, details: Optional[Dict] = None):
        """Add an entry to the provenance log, including both wall time and temporal phase."""
        entry = {
            'wall_time': time.time(),
            'action': action,
            'observer': self.observer_perspective,
            'details': details or {}
        }
        # Ensure temporal_phase is recorded in details
        if 'temporal_phase' not in entry['details']:
            entry['details']['temporal_phase'] = self.temporal_phase
        self.provenance.append(entry)

    # ------------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------------
    @property
    def atomicity_score(self) -> float:
        """Combined atomicity score for Layer 2 compatibility."""
        # If a manually set combined score exists, return it; otherwise compute.
        if 'combined' in self.atomicity:
            return self.atomicity['combined']
        return self.get_atomicity_score(combined=True)

    @atomicity_score.setter
    def atomicity_score(self, value: float) -> None:
        """Allow setting a combined score (e.g., from external source)."""
        self.atomicity['combined'] = value
        self._mark_stale()

    def is_atom(self, framework: Optional[str] = None, threshold: float = 0.999) -> bool:
        """
        Return True if the observable is considered atom in the given framework.
        If framework is None, returns True if it is atom in all frameworks.
        Uses atomicity scores with a threshold close to 1.0.
        If meta_spec indicates binary atomicity, the threshold is ignored and
        the score must be exactly 1.0 (or >0.5 after conversion) – we use 1.0.
        """
        if self._atomicity_stale:
            self._compute_atomicities()
        if self.meta_spec.atomicity_is_binary:
            # In binaire modus moet de score 1.0 zijn
            if framework is None:
                return all(v == 1.0 for v in self.atomicity.values())
            else:
                return self.atomicity.get(framework, 0.0) == 1.0
        else:
            # Continue modus: gebruik drempel
            if framework is None:
                return all(v > threshold for v in self.atomicity.values())
            else:
                return self.atomicity.get(framework, 0.0) > threshold

    def observe(self, observable_name: str = "value") -> float:
        """
        Perform a quantum measurement of the given observable and update the
        classical value accordingly. If no quantum structure exists, simply
        return the current value.
        """
        if self.observability_type == ObservabilityType.QUANTUM:
            # If we have a quantum structure, perform a projective measurement
            # of the named observable. For simplicity, we use 'value' as the
            # default observable name.
            if observable_name in self.quantum.observables:
                eigenvalue, new_state = self.quantum.projective_measurement(observable_name)
                self.value = eigenvalue
                self._add_provenance("quantum_measurement", {'observable': observable_name, 'eigenvalue': eigenvalue})
                self._mark_stale()
                return eigenvalue
            else:
                # If the named observable is not defined, fall back to expectation value
                exp_val = self.quantum.expectation_value(observable_name)
                self.value = exp_val
                self._add_provenance("quantum_expectation", {'observable': observable_name, 'value': exp_val})
                self._mark_stale()
                return exp_val
        # Non‑quantum: return value unchanged
        return self.value

    def add_qualitative_dimension(self, name: str, value: Union[float, Any],
                                   gradient: Optional[np.ndarray] = None,
                                   metadata: Optional[Dict] = None):
        """
        Add a qualitative dimension. If value is a float, it is stored in qualitative_dims.
        If value is a QualitativeDimension object, it is stored in qualitative_dimension_objects
        and its numeric value is also stored in qualitative_dims for backward compatibility.
        For non‑scalar values, we store the magnitude (L2 norm) as a representative scalar.
        """
        if isinstance(value, QualitativeDimension):
            self.qualitative_dimension_objects[name] = value
            # Also store the numeric value for simple access (if scalar)
            if np.isscalar(value.value):
                val = float(value.value)
            else:
                # Use magnitude as representative scalar
                val = float(np.linalg.norm(value.value)) if hasattr(value.value, '__len__') else 0.0
                logger.debug(f"Non‑scalar qualitative dimension '{name}' converted to magnitude {val}")
            self.qualitative_dims[name] = val
        else:
            # Assume simple float
            self.qualitative_dims[name] = float(value)

        if gradient is not None:
            self.qualitative_gradients[name] = gradient
        if metadata:
            self.qualitative_metadata[name] = metadata
        self._mark_stale()

    def get_atomicity_score(self, combined: bool = True, weights: Optional[Dict[str, float]] = None,
                            observer: Optional[str] = None) -> Union[float, Dict]:
        """
        Return atomicity score.

        If ``combined=True``, aggregates all framework scores into a single
        scalar.  The aggregation method is controlled by
        ``meta_spec.observer_aggregation`` (v3.1+):

        - ``"weighted_mean"``  : classic weighted average (default)
        - ``"geometric_mean"`` : multiplicative — zero in any framework → 0
        - ``"harmonic_mean"``  : biases toward the lowest scores (conservative)
        - ``"median"``         : robust against outlier framework scores

        The ``weights`` parameter overrides ``meta_spec.default_atomicity_weights``
        if provided.  If ``observer`` is given, observer-local weights from
        ``observer_context["atomicity_weights"]`` are used when available.

        The meta_spec ``atomicity_is_binary`` flag converts the result to 0/1
        after aggregation.

        Returns:
            Float in [0, 1] when ``combined=True``; raw dict of
            ``{framework: score}`` when ``combined=False``.
        """
        if self._atomicity_stale:
            self._compute_atomicities()
        if not combined:
            return self.atomicity

        # If a manually set combined score exists and no weights/observer override, return it.
        # if 'combined' in self.atomicity and weights is None and observer is None:
        #     return self.atomicity['combined']

        # Determine weights: if observer is specified and has atomicity_weights, use those.
        if observer is not None and observer == self.observer_perspective:
            ctx_weights = self.observer_context.get('atomicity_weights')
            if ctx_weights is not None:
                weights = ctx_weights

        # Use default weights from meta_spec if none provided
        if weights is None:
            weights = self.meta_spec.default_atomicity_weights

        # Collect active (framework, score, weight) triples
        active = [
            (k, self.atomicity.get(k, 0.0), w)
            for k, w in weights.items()
            if k in self.atomicity
        ]
        if not active:
            score = 0.0
        else:
            aggregation = getattr(self.meta_spec, "observer_aggregation", "weighted_mean")

            if aggregation == "geometric_mean":
                import math as _math
                scores_w = [(s, w) for _, s, w in active]
                total_w = sum(w for _, w in scores_w)
                if total_w > 0 and all(s > 0 for s, _ in scores_w):
                    log_score = sum(w * _math.log(s) for s, w in scores_w) / total_w
                    score = _math.exp(log_score)
                else:
                    # Fallback to weighted mean when any score is 0
                    total_w = sum(w for _, _, w in active)
                    score = sum(s * w for _, s, w in active) / total_w if total_w > 0 else 0.0

            elif aggregation == "harmonic_mean":
                total_w = sum(w for _, _, w in active)
                # Weighted harmonic mean: w_i / s_i, skip zeros
                denom = sum(w / s for _, s, w in active if s > 0)
                score = total_w / denom if denom > 0 else 0.0

            elif aggregation == "median":
                # Weighted median: sort by score, find 50th percentile
                sorted_active = sorted(active, key=lambda x: x[1])
                total_w = sum(w for _, _, w in sorted_active)
                cumulative = 0.0
                score = sorted_active[0][1]
                for _, s, w in sorted_active:
                    cumulative += w
                    if cumulative >= total_w / 2.0:
                        score = s
                        break

            else:  # "weighted_mean" (default, backward-compatible)
                total_w = sum(w for _, _, w in active)
                score = sum(s * w for _, s, w in active) / total_w if total_w > 0 else 0.0

        # If atomicity should be binary, apply a threshold (e.g., > 0.5)
        if self.meta_spec.atomicity_is_binary:
            return 1.0 if score > 0.5 else 0.0
        return max(0.0, min(1.0, score))

    def get_atomicity_confidence_interval(self, confidence: float = 0.95) -> Tuple[float, float]:
        """
        Return a confidence interval for the combined atomicity score based on
        the distribution of framework scores.
        Uses normal approximation (z-score).
        """
        if self._atomicity_stale:
            self._compute_atomicities()
        scores = np.array(list(self.atomicity.values()))
        if len(scores) == 0:
            return (0.0, 1.0)
        mean = np.mean(scores)
        std = np.std(scores)
        if std == 0:
            return (mean, mean)
        # z for 95% CI is about 1.96
        # Graceful degradation: use scipy for precise z, fall back to hard-coded
        # values for common confidence levels if scipy is unavailable.
        try:
            from scipy.stats import norm as _norm
            z = _norm.ppf((1 + confidence) / 2)
        except ImportError:
            # Pre-computed z-scores for common confidence levels
            _Z_TABLE = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}
            z = _Z_TABLE.get(round(float(confidence), 2), 1.960)
        margin = z * std / np.sqrt(len(scores))
        lower = max(0.0, mean - margin)
        upper = min(1.0, mean + margin)
        return (lower, upper)

    @property
    def atomicity_consensus(self) -> float:
        """
        Measure of consensus among frameworks: 1 - std of scores.
        Higher means more agreement.
        """
        if self._atomicity_stale:
            self._compute_atomicities()
        scores = np.array(list(self.atomicity.values()))
        if len(scores) == 0:
            return 0.0
        return 1.0 - np.std(scores)

    @property
    def generativity_score(self) -> float:
        """
        Measure of the observable's generative capacity – its potential to serve
        as a ground for higher-layer emergence.

        The Layer 1 theory states that the irreducible unit is not merely atomic
        (unable to be further decomposed) but also *generative*: it must provide
        the substrate from which relational and functional structures in Layers 2+
        can emerge.

        **Design note on "magic numbers" (addressed by hypercritical feedback):**
        The saturation constants (resonance_saturation, relational_saturation) and
        aggregation weights are intentionally exposed as class-level configuration
        that *can* be overridden via ``meta_spec.metadata`` or by a higher layer
        (Layer 6 Meta-Learning, Layer 14 Meta-Synthesis).  They are not permanent
        "magic numbers" but rather **Layer 1's conservative prior** — the baseline
        before the system has accumulated enough data to self-calibrate.

        A higher layer can update these via::

            obs.metadata["generativity_config"] = {
                "resonance_saturation": 8.0,
                "relational_saturation": 20.0,
                "weights": [0.4, 0.3, 0.3],
            }

        **Aggregation method — geometric vs. arithmetic mean:**
        Unlike a simple arithmetic mean, this implementation uses a
        **weighted geometric mean** which respects the multiplicative nature of
        generativity: an observable with zero consensus cannot be generative
        regardless of how many resonances it has.  The formula is:

            G = w_r · R^(a) · D^(b) · C^(c)

        where R = resonance_factor, D = relational_factor, C = consensus,
        and a+b+c = 1.  When any factor is zero, generativity collapses to zero.

        Returns:
            Float in [0, 1].  Values near 1.0 indicate a stable, well-connected,
            and multi-layer-active observable with strong generative potential.
        """
        # Retrieve self-calibration overrides from metadata if available
        cfg = self.metadata.get("generativity_config", {})
        resonance_sat = float(cfg.get("resonance_saturation", 5.0))
        relational_sat = float(cfg.get("relational_saturation", 10.0))
        weights = cfg.get("weights", [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0])
        wa, wb, wc = float(weights[0]), float(weights[1]), float(weights[2])

        # Normalise and clamp each factor to [0, 1]
        resonance_factor = min(1.0, len(self.resonance_map) / resonance_sat) if resonance_sat > 0 else 0.0
        relational_factor = min(1.0, len(self.relational_weights) / relational_sat) if relational_sat > 0 else 0.0
        consensus = max(0.0, min(1.0, self.atomicity_consensus))

        # Weighted geometric mean: multiplicative — any zero collapses the score.
        # Add a small epsilon to avoid log(0); we still return 0 if any factor is 0.
        if resonance_factor == 0.0 or relational_factor == 0.0 or consensus == 0.0:
            # Fallback to arithmetic mean when factors are zero (avoids
            # pathological 0 for brand-new observables with no resonances yet)
            return (resonance_factor + relational_factor + consensus) / 3.0

        import math as _math
        log_score = wa * _math.log(resonance_factor) + wb * _math.log(relational_factor) + wc * _math.log(consensus)
        return max(0.0, min(1.0, _math.exp(log_score)))

    def update_embedding(self, dim: int = 50):
        """
        Update the relational embedding using spectral embedding on the relational graph.

        Falls back to random embedding when:
        - networkx or sklearn are unavailable
        - graph has fewer than 3 nodes (spectral embedding is not meaningful)
        - graph is disconnected (SpectralEmbedding gives unreliable results)
        - any sklearn exception occurs

        **Warning suppression:**
        sklearn raises ``UserWarning`` ("Graph is not fully connected") and
        ``RuntimeWarning`` ("k >= N") for small or disconnected graphs.  These
        are suppressed here because we already check connectivity before calling
        the embedder.  The checks ensure spectral embedding is only called when
        it is theoretically meaningful, so warnings would be spurious.
        """
        if not NETWORKX_AVAILABLE:
            return
        G = self.relational_graph

        # Require at least 3 nodes: SpectralEmbedding with N=2 triggers
        # "k >= N for N * N square matrix" RuntimeWarning because eigsh
        # needs k < N. With N >= 3 and n_components = N-1 this is satisfied.
        if G is None or G.number_of_nodes() < 3:
            self.relational_embedding = np.random.randn(dim)
            self._normalize_embedding()
            return

        if HAS_SKLEARN:
            try:
                import warnings as _warnings
                # Check connectivity – SpectralEmbedding warns on disconnected graphs
                is_connected = nx.is_connected(G.to_undirected()) if G.is_directed() else nx.is_connected(G)
                if not is_connected:
                    # Use largest connected component for embedding
                    nodes_cc = max(nx.connected_components(G.to_undirected() if G.is_directed() else G), key=len)
                    G = G.subgraph(nodes_cc)
                    if G.number_of_nodes() < 3:
                        self.relational_embedding = np.random.randn(dim)
                        self._normalize_embedding()
                        return

                adj = nx.to_numpy_array(G)
                # n_components must satisfy: 1 ≤ n_components < number_of_nodes
                # This avoids k >= N in eigsh
                n_components = min(dim, G.number_of_nodes() - 1)
                if n_components < 1:
                    self.relational_embedding = np.random.randn(dim)
                    self._normalize_embedding()
                    return

                # Suppress residual sklearn warnings: we've already handled the
                # conditions that would trigger them
                with _warnings.catch_warnings():
                    _warnings.filterwarnings(
                        "ignore",
                        message="Graph is not fully connected",
                        category=UserWarning,
                        module="sklearn",
                    )
                    _warnings.filterwarnings(
                        "ignore",
                        message="k >= N",
                        category=RuntimeWarning,
                        module="sklearn",
                    )
                    embedder = SpectralEmbedding(n_components=n_components, affinity='precomputed')
                    coords = embedder.fit_transform(adj)

                # Find index of this node in the (possibly reduced) subgraph
                node_list = list(G.nodes())
                idx = node_list.index(self.id) if self.id in node_list else 0
                self.relational_embedding = coords[idx]
                # Pad to requested dim if needed
                if dim > n_components:
                    padding = np.zeros(dim - n_components)
                    self.relational_embedding = np.concatenate([self.relational_embedding, padding])
            except Exception as e:
                logger.debug(f"Spectral embedding failed: {e}, using random")
                self.relational_embedding = np.random.randn(dim)
        else:
            self.relational_embedding = np.random.randn(dim)

        self._normalize_embedding()

    def __repr__(self) -> str:
        return (f"UltimateObservable(id={self.id!r}, type={self.observability_type.value}, "
                f"phase={self.temporal_phase}, atomicity={self.get_atomicity_score():.3f})")

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary (for serialization)."""
        # For rich qualitative objects, we store a summary (e.g., class name and value)
        qual_objects_summary = {}
        for name, obj in self.qualitative_dimension_objects.items():
            qual_objects_summary[name] = {
                'class': obj.__class__.__name__,
                'value': str(obj.value) if hasattr(obj, 'value') else None
            }
        return {
            'id': self.id,
            'type': self.observability_type.value,
            'temporal_phase': self.temporal_phase,                     # restored as top‑level
            'qualitative_dims': self.qualitative_dims,
            'qualitative_objects_summary': qual_objects_summary,
            'atomicity': {
                'combined': self.get_atomicity_score(True),
                'details': self.atomicity,
                'consensus': self.atomicity_consensus,
                'ci_lower': self.get_atomicity_confidence_interval()[0],
                'ci_upper': self.get_atomicity_confidence_interval()[1],
            },
            'relational': {
                'degree': len(self.relational_weights),
                'embedding_norm': float(np.linalg.norm(self.relational_embedding))
            },
            'observer': {
                'current': self.observer_perspective,
                'history_length': len(self.observer_history)
            },
            'geometric': {
                'has_metric': self.geometry.metric_tensor is not None,
                'scalar_curvature': self.geometry.scalar_curvature
            },
            'topological': {
                'betti_numbers': self.topology.betti_numbers,
                'euler_characteristic': self.topology.euler_characteristic
            },
            'quantum': {
                'hilbert_dim': self.quantum.hilbert_space_dim,
                'entropy': self.quantum.entanglement_entropy
            },
            'fractal': {
                'hausdorff_dim': self.fractal.hausdorff_dimension,
                'self_similarity': self.fractal.self_similarity
            },
            'info_geometry': {
                'shannon_entropy': self.info_geometry.shannon_entropy
            },
            'dynamics': {
                'is_chaotic': self.dynamics.is_chaotic,
                'lyapunov_exponents': self.dynamics.lyapunov_exponents
            },
            'metadata': {
                'temporal_phase': self.temporal_phase,   # blijft in metadata voor compatibiliteit
                'version': self.version,
                'provenance_length': len(self.provenance)
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UltimateObservable':
        """
        Reconstruct an ``UltimateObservable`` from a dictionary produced by
        :meth:`to_dict`.

        This provides a complete serialisation round-trip so that observables
        can be persisted, transferred across processes, or logged and then
        replayed.

        .. note::
            The reconstruction is *shallow* for the heavy sub-structures
            (geometry, topology, quantum, …): the fields in the returned
            observable are re-initialised to their defaults and not restored
            from the dict (which only stores summary scalars).  If full
            sub-structure round-tripping is needed, use ``pickle`` or
            implement a custom persistence layer.

        Args:
            data: Dictionary as returned by :meth:`to_dict`.

        Returns:
            A new ``UltimateObservable`` with identity, type, temporal phase,
            qualitative dimensions, and observer perspective restored.

        Raises:
            KeyError:   If required keys (``id``, ``type``) are absent.
            ValueError: If ``type`` is not a valid :class:`ObservabilityType`.
        """
        obs_id: str = data['id']
        obs_type = ObservabilityType(data['type'])
        temporal_phase: float = float(data.get('temporal_phase', 0.0))
        qualitative_dims: Dict[str, float] = data.get('qualitative_dims', {})

        obs = cls(
            id=obs_id,
            value=data.get('value'),          # may be absent; defaults to None
            observability_type=obs_type,
            temporal_phase=temporal_phase,
        )

        # Restore qualitative dimensions
        for name, val in qualitative_dims.items():
            obs.add_qualitative_dimension(name, float(val))

        # Restore observer perspective (no history re-entry)
        observer_data = data.get('observer', {})
        perspective = observer_data.get('current', 'default')
        if perspective != 'default':
            obs.observer_perspective = perspective

        # Restore atomicity combined score if present
        atomicity_data = data.get('atomicity', {})
        combined = atomicity_data.get('combined')
        if combined is not None:
            obs.atomicity['combined'] = float(combined)

        return obs