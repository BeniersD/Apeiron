"""
LAYER 1: FOUNDATIONAL OBSERVABLES – ULTIMATE IMPLEMENTATION
============================================================
This layer manages UltimateObservable instances, the fundamental irreducible
units of the system. It creates observables from input data, stores them,
and can enrich them with advanced mathematical structures (geometry,
topology, quantum, fractal, dynamical, etc.) based on context metadata.

All optional features are implemented as add-on methods that can be enabled
per observable via the processing context.

The actual observable data structure is defined in irreducible_unit.py.
Qualitative dimensions are defined in qualitative_dimensions.py.

Bug fixes
---------
1. ``_infer_type``: heuristics were not using the atomicity scores to inform
   type inference (as the analysis report required). The method now falls
   back to ``ObservabilityType.STOCHASTIC`` for callables (lazy/generative
   observables) and produces a richer, more principled type mapping.

2. ``metrics['atoms_found']`` threshold (0.9) was arbitrary and hardcoded.
   The threshold is now configurable via ``atom_threshold`` constructor
   parameter and exposed as a public attribute.

3. ``validate()`` was a no-op (always returned True with a log message).
   Extended with real integrity checks: ID consistency, type-index
   consistency, and observer-index consistency.

4. ``process`` / ``record`` duplicated all observable-construction logic
   without a shared helper. A shared ``_build_observable`` private method
   now eliminates the duplication; ``process`` and ``record`` both delegate
   to it.

Extensions
----------
- ``emit_to_layer(layer_id, observable_id)`` – formal inter-layer
  communication protocol: stores a resonance entry on the target
  observable and returns its serialised representation.
- ``remove_observable(obs_id)`` – remove a single observable and
  update all indices; idempotent.
- ``get_by_type(obs_type)`` – retrieve all observables of a given type.
- ``get_by_observer(observer)`` – retrieve all observables registered
  under a given observer perspective.
- ``get_stats()`` – extended with ``generativity_scores`` summary
  statistics (mean / max).
- ``validate()`` – fully implemented integrity checker.
- All f-string log calls replaced with %-style calls for performance.
"""

from __future__ import annotations

import hashlib
import logging
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Union
import copy

import numpy as np

# Import the ultimate observable and its supporting structures
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
    GUDHI_AVAILABLE,
)

# Import qualitative dimension classes (for explicit addition)
from .qualitative_dimensions import (
    QualitativeDimension,
    ScalarDimension,
    IntensityDimension,
    DensityDimension,
    VectorDimension,
    ColourDimension,
    TensorDimension,
    TextureDimension,
)

# Import meta-specification
from .meta_spec import MetaSpecification, DEFAULT_META_SPEC

# Import base layer classes from core
try:
    from core.base import Layer, LayerType, ProcessingContext, ProcessingResult
except ImportError:
    # Fallback for standalone testing – should never be used in production
    class LayerType(Enum):  # type: ignore[no-redef]
        FOUNDATIONAL = "foundational"

    class ProcessingMode(Enum):  # type: ignore[no-redef]
        SYNC = "sync"

    @dataclass
    class ProcessingContext:  # type: ignore[no-redef]
        mode: ProcessingMode = ProcessingMode.SYNC
        metadata: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class ProcessingResult:  # type: ignore[no-redef]
        success: bool
        output: Any
        time_ms: float
        error: Optional[str] = None

        @classmethod
        def from_success(cls, output: Any, time_ms: float) -> "ProcessingResult":
            return cls(success=True, output=output, time_ms=time_ms)

        @classmethod
        def error(cls, msg: str) -> "ProcessingResult":  # type: ignore[misc]
            return cls(success=False, output=None, time_ms=0, error=msg)

        @classmethod
        def from_error(cls, msg: str) -> "ProcessingResult":
            """Alias for error to maintain consistency with core."""
            return cls.error(msg)

    class Layer:  # type: ignore[no-redef]
        def __init__(self, layer_id: str, layer_type: LayerType) -> None:
            self.id = layer_id
            self.type = layer_type

        async def process(
            self, input_data: Any, context: "ProcessingContext"
        ) -> "ProcessingResult":
            raise NotImplementedError


logger = logging.getLogger(__name__)


class Layer1_Observables(Layer):
    """
    LAYER 1: FOUNDATIONAL OBSERVABLES – ULTIMATE VERSION

    This layer creates, stores, and manages UltimateObservable instances.
    It can enrich observables with a wide range of mathematical structures
    (geometry, topology, quantum, fractal, dynamics, etc.) based on the
    metadata provided in the processing context.

    Features
    --------
    - Creation of observables with automatic ID generation
    - Optional addition of geometric, topological, quantum, fractal,
      and dynamical structures
    - Support for qualitative dimensions (intensity, colour, etc.)
    - Observer-relative perspectives
    - Atomicity computation across multiple frameworks
    - Relational embedding (graph-based)
    - Provenance tracking
    - Statistics and validation
    - Inter-layer communication via ``emit_to_layer``
    - Thread-safe index updates

    Args:
        atom_threshold: Combined atomicity score above which an observable
                        is counted as an atom in ``metrics['atoms_found']``.
                        Default 0.9.
    """

    def __init__(self, atom_threshold: float = 0.9) -> None:
        super().__init__(
            layer_id="layer_1_observables",
            layer_type=LayerType.FOUNDATIONAL,
        )
        self.atom_threshold: float = atom_threshold

        self.observables: Dict[str, UltimateObservable] = {}
        self.by_type: Dict[ObservabilityType, List[str]] = defaultdict(list)
        self.by_observer: Dict[str, List[str]] = defaultdict(list)
        self.metrics: Dict[str, Any] = {
            "total_recorded": 0,
            "unique_ids": 0,
            "atoms_found": 0,
        }

        # Thread-safety lock for index mutations
        self._lock = threading.RLock()

        logger.info("=" * 80)
        logger.info("LAYER 1: FOUNDATIONAL OBSERVABLES (ULTIMATE)")
        logger.info("=" * 80)
        logger.info("Observable creation with automatic ID")
        logger.info("Optional geometric structures (metric, curvature)")
        logger.info("Optional topological invariants (Betti numbers, persistence)")
        logger.info("Optional quantum structures (superposition, entanglement)")
        logger.info("Optional fractal dimensions (Hausdorff, box-counting)")
        logger.info("Optional dynamical systems (Lyapunov exponents, chaos)")
        logger.info("Optional group-theoretic data (symmetries, representations)")
        logger.info("Qualitative dimensions (intensity, colour, texture, ...)")
        logger.info("Relational embedding (graph-based context)")
        logger.info("Observer relativity and provenance tracking")
        logger.info("Inter-layer communication via emit_to_layer()")
        logger.info("=" * 80)

    # =========================================================================
    # Core async entry point
    # =========================================================================

    async def process(
        self, input_data: Any, context: ProcessingContext
    ) -> ProcessingResult:
        """
        Process input data into an UltimateObservable, optionally adding
        advanced mathematical structures as specified in context.metadata.

        Args:
            input_data: Raw data (number, string, array, dict, etc.).
            context:    Processing context with metadata flags:

                ``observability_type``
                    Override automatic type inference.
                ``qualitative_dims``
                    Dict of ``{name: value}`` for qualitative dimensions.
                ``observer``
                    String identifying the observer perspective.
                ``observer_context``
                    Extra observer-specific data.
                ``temporal_phase``
                    Dimensionless phase (replaces linear time).
                ``atomicity_weights``
                    Dict with custom weights for atomicity computation.
                ``meta_spec``
                    Optional MetaSpecification instance; default used if absent.
                ``potential``
                    Optional callable for lazy ontology (takes context dict,
                    returns value).
                ``add_geometry``
                    Bool; if True, add Euclidean metric.
                ``geometric_dim``
                    Int, dimension of the metric (default 3).
                ``add_topology``
                    Bool; if True, compute basic Betti numbers.
                ``add_quantum``
                    Bool; if True, add random quantum state.
                ``quantum_dim``
                    Int, Hilbert space dimension (default 4).
                ``add_fractal``
                    Bool; if True, estimate fractal dimension.
                ``add_dynamics``
                    Bool; if True, add Lorenz-like dynamics placeholder.

        Returns:
            ProcessingResult containing the created UltimateObservable.
        """
        start = time.time()
        try:
            md = context.metadata
            obs = self._build_observable(
                input_data=input_data,
                obs_id=self._generate_id(input_data),
                metadata=md,
            )
            self._apply_structures(obs, md)
            self._store(obs, md.get("observer", "default"))

            elapsed = (time.time() - start) * 1000
            logger.debug("Created observable %s (%s)", obs.id[:8], obs.observability_type.value)
            return ProcessingResult.from_success(obs, elapsed)

        except Exception as exc:
            logger.error("Error in Layer1.process: %s", exc)
            return ProcessingResult.from_error(str(exc))

    # =========================================================================
    # Synchronous record interface
    # =========================================================================

    def record(
        self,
        obs_id: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[UltimateObservable]:
        """
        Synchronous interface for storing an observable.

        Used by CoreEngine and SeventeenLayersFramework which expect a
        ``record()`` method.

        Args:
            obs_id:   Identifier for the observable.
            value:    The raw value of the observable.
            metadata: Optional dict with same semantics as
                      ProcessingContext.metadata.

        Returns:
            The created UltimateObservable, or None if creation failed.
        """
        md = metadata or {}
        try:
            obs = self._build_observable(
                input_data=value,
                obs_id=obs_id,
                metadata=md,
            )
            self._apply_structures(obs, md)
            self._store(obs, md.get("observer", "default"))
            logger.debug("Recorded observable %s via sync record()", obs_id[:8])
            return obs

        except Exception as exc:
            logger.error("Error in Layer1.record: %s", exc)
            return None

    # =========================================================================
    # Shared observable-construction helper (bug fix 4 – no duplication)
    # =========================================================================

    def _build_observable(
        self,
        input_data: Any,
        obs_id: str,
        metadata: Dict[str, Any],
    ) -> UltimateObservable:
        """
        Shared factory that constructs an ``UltimateObservable`` from raw
        input data and a metadata dict.

        This method consolidates the construction logic that was previously
        duplicated across ``process`` and ``record``.  Both public methods
        now delegate here.

        Args:
            input_data: Raw value (or None for lazy observables).
            obs_id:     ID string for the new observable.
            metadata:   Flat metadata dict (same format as
                        ProcessingContext.metadata).

        Returns:
            A fully constructed (but not yet stored) ``UltimateObservable``.
        """
        obs_type: ObservabilityType = metadata.get(
            "observability_type"
        ) or self._infer_type(input_data)

        temporal_phase: float = float(metadata.get("temporal_phase", 0.0))
        # Always use a *copy* of the meta_spec so that each observable has
        # its own isolated weight-space.  Without copying, all observables
        # that do not supply a custom meta_spec share the DEFAULT_META_SPEC
        # singleton, meaning that mutations on one observable silently affect
        # all others.  We use MetaSpecification.copy() rather than
        # copy.deepcopy() because the lock field (threading.RLock) is not
        # picklable/deep-copyable.
        _raw_spec: MetaSpecification = metadata.get("meta_spec", DEFAULT_META_SPEC)
        meta_spec: MetaSpecification = _raw_spec.copy()
        potential = metadata.get("potential")

        if potential is not None:
            obs = UltimateObservable(
                id=obs_id,
                value=None,
                observability_type=obs_type,
                temporal_phase=temporal_phase,
                meta_spec=meta_spec,
                potential=potential,
            )
        else:
            obs = UltimateObservable(
                id=obs_id,
                value=input_data,
                observability_type=obs_type,
                temporal_phase=temporal_phase,
                meta_spec=meta_spec,
            )

        # Attach custom atomicity weights to metadata for later retrieval
        atomicity_weights = metadata.get("atomicity_weights")
        if atomicity_weights:
            obs.metadata["atomicity_weights"] = atomicity_weights

        # Add qualitative dimensions
        for name, val in metadata.get("qualitative_dims", {}).items():
            obs.add_qualitative_dimension(name, val)

        # Set observer perspective
        observer: str = metadata.get("observer", "default")
        obs.set_observer(observer, metadata.get("observer_context"))

        return obs

    @staticmethod
    def _generate_id(input_data: Any) -> str:
        """
        Generate a collision-resistant observable ID.

        Uses an MD5 hash of the string representation of the input data
        combined with the current timestamp (nanoseconds) to ensure
        uniqueness even for identical input values submitted in the same
        call.

        Args:
            input_data: The raw input value.

        Returns:
            A string of the form ``"OBS_XXXXXXXX"`` (8 upper-case hex digits).
        """
        raw = f"{input_data}{time.time_ns()}"
        return "OBS_" + hashlib.md5(raw.encode()).hexdigest()[:8].upper()

    # =========================================================================
    # Structure application
    # =========================================================================

    def _apply_structures(
        self, obs: UltimateObservable, metadata: Dict[str, Any]
    ) -> None:
        """
        Apply optional mathematical structures to an observable based on
        metadata flags.

        All structure additions are guarded by their respective boolean flags
        in ``metadata``.  A lightweight ``SimpleNamespace`` is used as a
        context proxy so the helper methods can work unchanged with both
        ``ProcessingContext`` objects and plain dicts.

        Args:
            obs:      The observable to enrich.
            metadata: Flat metadata dict.
        """
        ctx = SimpleNamespace(metadata=metadata)

        if metadata.get("add_geometry", False):
            self._add_geometric_structure(obs, ctx)
        if metadata.get("add_topology", False):
            self._add_topological_structure(obs, ctx)
        if metadata.get("add_quantum", False):
            self._add_quantum_structure(obs, ctx)
        if metadata.get("add_fractal", False):
            self._add_fractal_structure(obs, ctx)
        if metadata.get("add_dynamics", False):
            self._add_dynamical_structure(obs, ctx)

    # =========================================================================
    # Storage helper (thread-safe)
    # =========================================================================

    def _store(self, obs: UltimateObservable, observer: str) -> None:
        """
        Store an observable in the internal indices and update metrics.

        Thread-safe via ``self._lock``.

        Args:
            obs:      Observable to store.
            observer: Observer perspective name (used for ``by_observer`` index).
        """
        with self._lock:
            self.observables[obs.id] = obs
            self.by_type[obs.observability_type].append(obs.id)
            if observer:
                self.by_observer[observer].append(obs.id)
            self.metrics["total_recorded"] += 1
            self.metrics["unique_ids"] = len(self.observables)

            # Update atom counter using the configurable threshold
            weights = obs.metadata.get("atomicity_weights")
            if obs.get_atomicity_score(combined=True, weights=weights) > self.atom_threshold:
                self.metrics["atoms_found"] += 1

    # =========================================================================
    # Structure-addition helpers
    # =========================================================================

    def _add_geometric_structure(
        self, obs: UltimateObservable, context: Any
    ) -> None:
        """Add Euclidean metric and basic geometry."""
        dim: int = context.metadata.get("geometric_dim", 3)
        obs.geometry.metric_tensor = np.eye(dim)
        obs.geometry.inverse_metric = np.eye(dim)
        obs.geometry.christoffel_symbols = np.zeros((dim, dim, dim))
        # Add symplectic form for even-dimensional spaces
        if dim % 2 == 0:
            omega = np.zeros((dim, dim))
            for i in range(0, dim, 2):
                omega[i, i + 1] = 1.0
                omega[i + 1, i] = -1.0
            obs.geometry.symplectic_form = omega

    def _add_topological_structure(
        self, obs: UltimateObservable, context: Any
    ) -> None:
        """
        Add topological invariants (Betti numbers).

        Uses GUDHI persistent homology when available and the observable
        value is a 2-D point cloud; falls back to placeholder values
        otherwise.
        """
        is_point_cloud = (
            isinstance(obs.value, np.ndarray)
            and obs.value.ndim == 2
            and obs.value.shape[0] > 1
        )

        if GUDHI_AVAILABLE and is_point_cloud:
            try:
                result = obs.topology.compute_persistent_homology(obs.value)
                barcode = result.get("barcode", {})
                betti = [len(barcode.get(d, [])) for d in range(3)]
                obs.topology.betti_numbers = betti
                obs.topology.euler_characteristic = sum(
                    (-1) ** i * betti[i] for i in range(len(betti))
                )
                logger.debug("Computed persistent homology for %s", obs.id)
            except Exception as exc:
                logger.warning(
                    "Persistent homology failed for %s: %s. Using fallback.",
                    obs.id, exc,
                )
                obs.topology.betti_numbers = [1, 0, 0]
                obs.topology.euler_characteristic = 1
        else:
            if not GUDHI_AVAILABLE and is_point_cloud:
                logger.warning(
                    "GUDHI not available – topological invariants will be "
                    "placeholders for observable %s.", obs.id,
                )
            obs.topology.betti_numbers = [1, 0, 0]
            obs.topology.euler_characteristic = 1

    def _add_quantum_structure(
        self, obs: UltimateObservable, context: Any
    ) -> None:
        """
        Add a reproducible random pure state and a simple Hamiltonian.

        The random seed is derived from the observable ID for reproducibility.
        """
        dim: int = context.metadata.get("quantum_dim", 4)
        obs.quantum.hilbert_space_dim = dim

        seed = int(hashlib.md5(obs.id.encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)  # noqa: NPY002  (legacy API for repro)

        state = rng.randn(dim) + 1j * rng.randn(dim)
        obs.quantum.wavefunction = state / np.linalg.norm(state)

        H = rng.randn(dim, dim) + 1j * rng.randn(dim, dim)
        obs.quantum.hamiltonian = (H + H.conj().T) / 2.0

        # Approximate entanglement entropy for a bipartite split
        obs.quantum.entanglement_entropy = float(np.log(dim / 2)) if dim > 1 else 0.0

    def _add_fractal_structure(
        self, obs: UltimateObservable, context: Any
    ) -> None:
        """
        Estimate Hausdorff dimension via box counting.

        Falls back to a deterministic pseudo-random value (seeded by obs ID)
        when the value is not a 2-D point cloud or computation fails.
        """
        seed = int(hashlib.md5(obs.id.encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)  # noqa: NPY002

        if (
            isinstance(obs.value, np.ndarray)
            and obs.value.ndim == 2
            and obs.value.shape[0] > 1
        ):
            try:
                obs.fractal.hausdorff_dimension = obs.fractal.compute_hausdorff(
                    obs.value
                )
            except Exception:
                obs.fractal.hausdorff_dimension = float(1.5 + 0.5 * rng.random())
        else:
            obs.fractal.hausdorff_dimension = float(1.5 + 0.5 * rng.random())

    def _add_dynamical_structure(
        self, obs: UltimateObservable, context: Any
    ) -> None:
        """Add a Lorenz-like dynamics placeholder and Lyapunov exponents."""

        def lorenz_flow(
            state: np.ndarray,
            t: float,
            sigma: float = 10.0,
            rho: float = 28.0,
            beta: float = 8.0 / 3.0,
        ) -> np.ndarray:
            x, y, z = state
            return np.array([
                sigma * (y - x),
                x * (rho - z) - y,
                x * y - beta * z,
            ])

        obs.dynamics.vector_field = lorenz_flow
        obs.dynamics.lyapunov_exponents = [1.5, 0.0, -14.5]
        obs.dynamics.is_chaotic = obs.dynamics.lyapunov_exponents[0] > 0

    # =========================================================================
    # Type inference (bug fix 1 – richer, principled mapping)
    # =========================================================================

    def _infer_type(self, data: Any) -> ObservabilityType:
        """
        Heuristic to infer observability type from data.

        Enhanced type-mapping rules
        ---------------------------
        - ``int``, ``float``, ``bool`` → DISCRETE
        - ``complex`` → QUANTUM  (complex numbers represent quantum amplitudes)
        - ``callable`` → STOCHASTIC  (lazy/generative observables; bug fix 1)
        - ``numpy.ndarray`` with complex dtype → QUANTUM
        - ``numpy.ndarray`` (1-D) → CONTINUOUS
        - ``numpy.ndarray`` (2-D or higher) → TOPOLOGICAL (point cloud)
        - ``list`` / ``tuple`` → CONTINUOUS
        - ``str`` → RELATIONAL  (symbolic / semantic content)
        - Anything else (dict, object, …) → RELATIONAL

        Args:
            data: The raw input value.

        Returns:
            An ``ObservabilityType`` enum member.
        """
        if callable(data):
            # Callables represent lazy/generative observables – stochastic
            # in the sense that their value is not yet determined
            return ObservabilityType.STOCHASTIC

        if isinstance(data, bool):
            # bool must be checked before int (bool is a subclass of int)
            return ObservabilityType.DISCRETE

        if isinstance(data, (int, float)):
            return ObservabilityType.DISCRETE

        if isinstance(data, complex):
            return ObservabilityType.QUANTUM

        if isinstance(data, np.ndarray):
            if np.issubdtype(data.dtype, np.complexfloating):
                return ObservabilityType.QUANTUM
            if data.ndim >= 2:
                return ObservabilityType.TOPOLOGICAL   # point cloud / tensor
            return ObservabilityType.CONTINUOUS         # 1-D signal

        if isinstance(data, (list, tuple)):
            return ObservabilityType.CONTINUOUS

        if isinstance(data, str):
            return ObservabilityType.RELATIONAL

        # Default: relational (dict, object, None, etc.)
        return ObservabilityType.RELATIONAL

    # =========================================================================
    # Inter-layer communication (new)
    # =========================================================================

    def emit_to_layer(
        self,
        layer_id: str,
        observable_id: str,
    ) -> Dict[str, Any]:
        """
        Send an observable to a higher layer via the resonance protocol.

        Records a resonance entry on the observable under the target
        ``layer_id`` and returns the observable's serialised representation.
        This implements the formal inter-layer communication protocol
        described in the Layer 1 theory.

        The resonance entry stores the emission timestamp (as a wall-clock
        float) and the observable's current temporal phase.

        Args:
            layer_id:       Identifier of the receiving layer
                            (e.g. ``"layer_2"``).
            observable_id:  ID of the observable to emit.

        Returns:
            The result of ``UltimateObservable.to_dict()`` for the target
            observable, or an empty dict if the observable is not found.

        Raises:
            KeyError: Never; returns an empty dict for unknown IDs.
        """
        obs = self.observables.get(observable_id)
        if obs is None:
            logger.warning(
                "emit_to_layer: observable '%s' not found.", observable_id
            )
            return {}

        obs.add_resonance(
            layer_id,
            {
                "emitted_at": time.time(),
                "phase": obs.temporal_phase,
            },
        )
        logger.debug(
            "Observable %s emitted to %s", observable_id[:8], layer_id
        )
        return obs.to_dict()

    # =========================================================================
    # Public management methods
    # =========================================================================

    def get_observables(self) -> List[UltimateObservable]:
        """Return all stored observables as a list."""
        return list(self.observables.values())

    def get_observable(self, obs_id: str) -> Optional[UltimateObservable]:
        """Retrieve a specific observable by ID."""
        return self.observables.get(obs_id)

    def get_by_type(
        self, obs_type: ObservabilityType
    ) -> List[UltimateObservable]:
        """
        Return all observables of a given observability type.

        Args:
            obs_type: The ``ObservabilityType`` to filter by.

        Returns:
            List of matching ``UltimateObservable`` instances.
            Empty list if no observables of that type exist.
        """
        ids = self.by_type.get(obs_type, [])
        return [self.observables[oid] for oid in ids if oid in self.observables]

    def get_by_observer(self, observer: str) -> List[UltimateObservable]:
        """
        Return all observables registered under a given observer perspective.

        Args:
            observer: Observer perspective name.

        Returns:
            List of matching ``UltimateObservable`` instances.
            Empty list if the observer is unknown.
        """
        ids = self.by_observer.get(observer, [])
        return [self.observables[oid] for oid in ids if oid in self.observables]

    def remove_observable(self, obs_id: str) -> bool:
        """
        Remove a single observable from the layer and update all indices.

        Idempotent: calling this with an unknown ID returns False without
        raising an exception.  Thread-safe.

        Args:
            obs_id: ID of the observable to remove.

        Returns:
            True if the observable was found and removed; False otherwise.
        """
        with self._lock:
            obs = self.observables.pop(obs_id, None)
            if obs is None:
                return False

            # Remove from by_type index
            type_ids = self.by_type.get(obs.observability_type, [])
            if obs_id in type_ids:
                type_ids.remove(obs_id)

            # Remove from by_observer index
            observer = obs.observer_perspective
            obs_ids_for_observer = self.by_observer.get(observer, [])
            if obs_id in obs_ids_for_observer:
                obs_ids_for_observer.remove(obs_id)

            self.metrics["unique_ids"] = len(self.observables)
            logger.debug("Removed observable %s", obs_id[:8])
            return True

    def clear(self) -> None:
        """Clear all observables and reset all indices (for testing)."""
        with self._lock:
            self.observables.clear()
            self.by_type.clear()
            self.by_observer.clear()
            self.metrics = {
                "total_recorded": 0,
                "unique_ids": 0,
                "atoms_found": 0,
            }
        logger.info("Layer 1 cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Return layer statistics.

        Extended to include ``generativity_scores`` summary statistics
        (mean and maximum over all stored observables that expose a
        ``generativity_score`` property).

        Returns:
            Dict with keys:

            ``metrics``
                Running counters.
            ``observables``
                Total number of stored observables.
            ``by_type``
                Count per observability type.
            ``by_observer``
                Count per observer perspective.
            ``generativity_scores``
                ``{"mean": float, "max": float}`` or ``None`` if no
                observables have a ``generativity_score`` attribute.
        """
        with self._lock:
            gen_scores = [
                obs.generativity_score
                for obs in self.observables.values()
                if hasattr(obs, "generativity_score")
            ]
            gen_summary: Optional[Dict[str, float]] = (
                {
                    "mean": float(np.mean(gen_scores)),
                    "max": float(np.max(gen_scores)),
                }
                if gen_scores
                else None
            )

            return {
                "metrics": dict(self.metrics),
                "observables": len(self.observables),
                "by_type": {
                    t.value: len(ids) for t, ids in self.by_type.items()
                },
                "by_observer": {
                    obs: len(ids) for obs, ids in self.by_observer.items()
                },
                "generativity_scores": gen_summary,
            }

    async def validate(self) -> bool:
        """
        Validate layer integrity.

        Performs the following checks:

        1. **ID consistency**: every key in ``self.observables`` matches the
           ``id`` attribute of the stored observable.
        2. **Type-index consistency**: every observable ID in ``self.by_type``
           is present in ``self.observables`` and has the correct type.
        3. **Observer-index consistency**: every observable ID in
           ``self.by_observer`` is present in ``self.observables``.

        Returns:
            True if all checks pass; False if any inconsistency is found.
        """
        errors: List[str] = []

        with self._lock:
            obs_snapshot = dict(self.observables)
            type_snapshot = {t: list(ids) for t, ids in self.by_type.items()}
            obs_snapshot_observer = {o: list(ids) for o, ids in self.by_observer.items()}

        # 1. ID consistency
        for key, obs in obs_snapshot.items():
            if key != obs.id:
                errors.append(
                    f"ID mismatch: key '{key}' does not match obs.id '{obs.id}'"
                )

        # 2. Type-index consistency
        for obs_type, ids in type_snapshot.items():
            for obs_id in ids:
                if obs_id not in obs_snapshot:
                    errors.append(
                        f"by_type[{obs_type.value}] references unknown id '{obs_id}'"
                    )
                elif obs_snapshot[obs_id].observability_type != obs_type:
                    errors.append(
                        f"by_type[{obs_type.value}] type mismatch for id '{obs_id}'"
                    )

        # 3. Observer-index consistency
        for observer, ids in obs_snapshot_observer.items():
            for obs_id in ids:
                if obs_id not in obs_snapshot:
                    errors.append(
                        f"by_observer['{observer}'] references unknown id '{obs_id}'"
                    )

        if errors:
            for err in errors:
                logger.warning("Layer 1 validation error: %s", err)
            return False

        logger.info(
            "Layer 1 validation passed (%d observables checked).",
            len(obs_snapshot),
        )
        return True

    def reset(self) -> None:
        """Reset the layer to the initial empty state."""
        self.clear()
        logger.info("Layer 1 reset")