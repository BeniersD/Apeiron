"""
relations_core.py – Core relational structures for Layer 2
===========================================================
Provides the two central classes of the relational layer:

  - UltimateRelation : a richly structured edge connecting two observables.
  - Layer2_Relational_Ultimate : the manager that creates, stores, and
    analyses all UltimateRelations.

Everything else (category theory, quivers, metrics, spectral analysis, …)
is imported from the sibling modules created during the Layer‑2 refactoring.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# ---------------------------------------------------------------------------
# Layer‑2 submodules (refactored)
# ---------------------------------------------------------------------------
from .category import (
    Adjunction,
    AdjunctionType,
    Colimit,
    Comonad,
    EnrichedCategory,
    FunctorType,
    KanExtension,
    Limit,
    Monad,
    MonoidalStructure,
    NaturalTransformation,
    NaturalTransformationType,
    RelationalCategory,
    RelationalFunctor,
    TwoCategory,
    YonedaEmbedding,
)
from .hypergraph import Hypergraph
from .metric import RelationalMetricSpace
from .quiver import (
    PathAlgebra,
    Quiver,
    QuiverRepresentation,
    QuiverRepresentationTheory,
)
from .quantum_graph import QuantumGraph
from .spectral import SpectralGraphAnalysis

# Optional imports that are not always needed
try:
    from .motif_detection import TopologicalNetworkAnalysis
except ImportError:
    TopologicalNetworkAnalysis = None

try:
    from .temporal_networks import TemporalNetwork
except ImportError:
    TemporalNetwork = None

logger = logging.getLogger(__name__)


# ============================================================================
# Relation type enum
# ============================================================================

class RelationType(Enum):
    SYMMETRIC = "symmetric"
    DIRECTED = "directed"
    BIDIRECTIONAL = "bidirectional"
    WEIGHTED = "weighted"
    FUZZY = "fuzzy"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    QUANTUM = "quantum"
    HYPER = "hyper"
    HETEROGENEOUS = "heterogeneous"
    PROBABILISTIC = "probabilistic"
    LOGICAL = "logical"
    ONTOLOGICAL = "ontological"


# ============================================================================
# UltimateRelation – the fundamental relational unit
# ============================================================================

@dataclass
class UltimateRelation:
    """
    An edge connecting two observables with an extensive set of attached
    mathematical and computational structures.

    Attributes
    ----------
    id : str
        Unique identifier.
    source_id, target_id : str
        IDs of the source and target observables (from Layer 1).
    relation_type : RelationType
        The kind of relation.
    weight : float
        Strength of the relation (0–1).
    temporal_order : float or None
        If the source has a ``temporal_phase``, it is stored here.
    metadata : dict
        Free‑form metadata.
    """

    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    created_at: float = field(default_factory=time.time)
    version: str = "5.0"

    # Temporal information from Layer 1
    temporal_order: Optional[float] = None

    # -----------------------------------------------------------------
    # Embedded mathematical structures (all optional)
    # -----------------------------------------------------------------
    category: RelationalCategory = field(default_factory=RelationalCategory)
    functors: Dict[str, RelationalFunctor] = field(default_factory=dict)
    natural_transformations: Dict[str, NaturalTransformation] = field(default_factory=dict)
    monoidal: MonoidalStructure = field(default_factory=lambda: MonoidalStructure(RelationalCategory()))
    two_category: TwoCategory = field(default_factory=TwoCategory)

    adjunctions: Dict[str, Adjunction] = field(default_factory=dict)
    monads: Dict[str, Monad] = field(default_factory=dict)
    comonads: Dict[str, Comonad] = field(default_factory=dict)
    limits: Dict[str, Limit] = field(default_factory=dict)
    colimits: Dict[str, Colimit] = field(default_factory=dict)
    kan_extensions: Dict[str, KanExtension] = field(default_factory=dict)

    quiver: Quiver = field(default_factory=Quiver)
    representations: Dict[str, QuiverRepresentation] = field(default_factory=dict)
    rep_theory: QuiverRepresentationTheory = field(default_factory=lambda: QuiverRepresentationTheory(Quiver()))

    metric_space: RelationalMetricSpace = field(default_factory=RelationalMetricSpace)
    distance: float = 0.0
    similarity: float = 1.0

    spectral: SpectralGraphAnalysis = field(default_factory=lambda: SpectralGraphAnalysis(np.zeros((0,0))))
    topology: Optional[TopologicalNetworkAnalysis] = None

    quantum_graph: QuantumGraph = field(default_factory=QuantumGraph)

    hypergraph: Hypergraph = field(default_factory=Hypergraph)

    temporal_evolution: List[Tuple[float, float]] = field(default_factory=list)

    # Causal / probabilistic
    probability: float = 1.0

    # Metadata and provenance
    metadata: Dict[str, Any] = field(default_factory=dict)
    provenance: List[Dict] = field(default_factory=list)

    # -----------------------------------------------------------------
    # Initialisation helpers
    # -----------------------------------------------------------------
    def __post_init__(self):
        # Register source and target in the embedded category
        self.category.add_object(self.source_id)
        self.category.add_object(self.target_id)
        self.category.add_morphism(self.source_id, self.target_id, self.id)
        # Add arrow to the quiver
        self.quiver.add_arrow(self.source_id, self.target_id, self.id)
        # Create a minimal 2‑vertex hypergraph edge
        self.hypergraph.add_hyperedge(self.id, {self.source_id, self.target_id}, self.weight)
        # If NetworkX is available, build a minimal graph for spectral analysis
        try:
            import networkx as nx
            self.spectral.graph = nx.Graph()
            self.spectral.graph.add_edge(self.source_id, self.target_id, weight=self.weight)
        except ImportError:
            pass
        self._add_provenance("created")

    def _add_provenance(self, action: str, details: Optional[Dict] = None):
        self.provenance.append({
            'timestamp': time.time(),
            'action': action,
            'details': details or {},
        })

    # -----------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON‑serialisable summary (without heavy numeric data)."""
        return {
            'id': self.id,
            'source': self.source_id,
            'target': self.target_id,
            'type': self.relation_type.value,
            'weight': self.weight,
            'distance': self.distance,
            'similarity': self.similarity,
            'temporal_order': self.temporal_order,
            'metadata': self.metadata,
        }
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UltimateRelation:
        """Reconstruct an UltimateRelation from a dictionary created by to_dict()."""
        return cls(
            id=data["id"],
            source_id=data["source"],
            target_id=data["target"],
            relation_type=RelationType(data["type"]),
            weight=data.get("weight", 1.0),
            temporal_order=data.get("temporal_order"),
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# Layer2_Relational_Ultimate – manager for all relations
# ============================================================================

class Layer2_Relational_Ultimate:
    """
    Manages the creation, storage, and analysis of ``UltimateRelation``
    instances.

    It typically receives a reference to the Layer 1 observables registry,
    which allows automatic similarity‑based relation generation.
    """

    def __init__(
        self,
        layer1_registry: Optional[Dict[str, Any]] = None,
        use_redis: bool = False,
        redis_url: str = "redis://localhost:6379",
    ) -> None:
        self.layer1_registry = layer1_registry

        # All relations indexed by ID
        self.relations: Dict[str, UltimateRelation] = {}
        # Secondary indices
        self.by_type: Dict[RelationType, List[str]] = {t: [] for t in RelationType}
        self.by_source: Dict[str, List[str]] = defaultdict(list)
        self.by_target: Dict[str, List[str]] = defaultdict(list)

        # Global categorical context
        self.global_category = RelationalCategory()

        # Global graph (NetworkX) for visualisation / centralities
        self.global_graph: Optional[Any] = None
        try:
            import networkx as nx
            self.global_graph = nx.MultiDiGraph()
        except ImportError:
            pass

        # Lazy spectral / topological summaries
        self._global_spectral: Optional[SpectralGraphAnalysis] = None
        self._global_topology: Optional[TopologicalNetworkAnalysis] = None

        # Hypergraph and quantum network placeholders
        self.global_hypergraph = Hypergraph()
        self.quantum_network = QuantumGraph()

        # Minimum similarity for automatic relation generation
        self.min_similarity_threshold = 0.1
        self.max_relation_weight = 1.0

        # Redis cache (optional)
        self._redis_client = None
        if use_redis:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Redis init failed: {e}")

        logger.info("Layer2_Relational_Ultimate initialised (v5.0 refactored).")

    # -----------------------------------------------------------------
    # Relation creation
    # -----------------------------------------------------------------
    def create_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType = RelationType.SYMMETRIC,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UltimateRelation:
        """Create a new relation and register it in all indices."""
        rel_id = f"REL_{hashlib.md5(f'{source_id}{target_id}{time.time()}'.encode()).hexdigest()[:12]}"

        # Try to inherit temporal order from the source observable
        temporal_order = None
        if self.layer1_registry and source_id in self.layer1_registry:
            src = self.layer1_registry[source_id]
            temporal_order = getattr(src, 'temporal_phase', None)

        rel = UltimateRelation(
            id=rel_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            metadata=metadata or {},
            temporal_order=temporal_order,
        )

        # Store
        self.relations[rel_id] = rel
        self.by_type[relation_type].append(rel_id)
        self.by_source[source_id].append(rel_id)
        self.by_target[target_id].append(rel_id)

        # Update global structures
        self.global_category.add_object(source_id)
        self.global_category.add_object(target_id)
        self.global_category.add_morphism(source_id, target_id, rel.id)

        if self.global_graph is not None:
            self.global_graph.add_edge(
                source_id, target_id,
                key=rel_id, weight=weight,
                type=relation_type.value,
            )

        self.global_hypergraph.add_hyperedge(rel_id, {source_id, target_id}, weight)

        # Set distance and similarity based on weight
        rel.distance = 1.0 - min(weight / max(self.max_relation_weight, 1e-6), 1.0)
        rel.similarity = weight

        # Resonance: notify observables (if they support it)
        if self.layer1_registry:
            for obs_id in (source_id, target_id):
                obs = self.layer1_registry.get(obs_id)
                if obs is not None and hasattr(obs, 'add_resonance'):
                    obs.add_resonance('layer2', {'relation_id': rel_id, 'weight': weight})

        logger.debug(f"New relation: {rel_id[:8]} ({source_id[:8]} → {target_id[:8]})")
        return rel

    # -----------------------------------------------------------------
    # Automatic relation generation
    # -----------------------------------------------------------------
    def compute_relations(self, threshold: float = 0.1) -> List[str]:
        """
        Create relations between all pairs of observables whose similarity
        exceeds `threshold`.  Similarity uses qualitative dimensions,
        relational embeddings, and atomicity scores where available.
        """
        if self.layer1_registry is None:
            return []
        rel_ids = []
        ids = list(self.layer1_registry.keys())
        for i, id1 in enumerate(ids):
            for j in range(i + 1, len(ids)):
                id2 = ids[j]
                sim = self._compute_similarity(self.layer1_registry[id1],
                                               self.layer1_registry[id2])
                if sim >= threshold:
                    rel = self.create_relation(id1, id2, weight=sim,
                                               relation_type=RelationType.SYMMETRIC)
                    rel_ids.append(rel.id)
        return rel_ids

    def _compute_similarity(self, obs1: Any, obs2: Any) -> float:
        """Heuristic that combines several observable attributes."""
        sim = 0.0
        count = 0
        # qualitative dimensions
        if hasattr(obs1, 'qualitative_dims') and hasattr(obs2, 'qualitative_dims'):
            common = set(obs1.qualitative_dims) & set(obs2.qualitative_dims)
            if common:
                v1 = np.array([obs1.qualitative_dims[d] for d in common])
                v2 = np.array([obs2.qualitative_dims[d] for d in common])
                n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
                if n1 > 0 and n2 > 0:
                    sim += np.dot(v1, v2) / (n1 * n2)
                    count += 1
        # relational embedding
        if hasattr(obs1, 'relational_embedding') and hasattr(obs2, 'relational_embedding'):
            e1 = np.asarray(obs1.relational_embedding).flatten()
            e2 = np.asarray(obs2.relational_embedding).flatten()
            if e1.size > 0 and e2.size > 0:
                n1, n2 = np.linalg.norm(e1), np.linalg.norm(e2)
                if n1 > 0 and n2 > 0:
                    sim += np.dot(e1, e2) / (n1 * n2)
                    count += 1
        # atomicity scores
        if hasattr(obs1, 'atomicity_score') and hasattr(obs2, 'atomicity_score'):
            sim += 1.0 - abs(obs1.atomicity_score - obs2.atomicity_score)
            count += 1
        if count == 0:
            return 0.0
        return sim / count

    # -----------------------------------------------------------------
    # Statistics
    # -----------------------------------------------------------------
    def get_stats(self) -> Dict[str, Any]:
        return {
            'relations': len(self.relations),
            'by_type': {t.value: len(ids) for t, ids in self.by_type.items()},
            'by_source': {s: len(ids) for s, ids in self.by_source.items()},
            'by_target': {t: len(ids) for t, ids in self.by_target.items()},
        }

    # -----------------------------------------------------------------
    # Reset
    # -----------------------------------------------------------------
    def reset(self) -> None:
        self.relations.clear()
        for t in self.by_type:
            self.by_type[t].clear()
        self.by_source.clear()
        self.by_target.clear()
        self.global_category = RelationalCategory()
        if self.global_graph is not None:
            self.global_graph.clear()
        self.global_hypergraph = Hypergraph()
        self.quantum_network = QuantumGraph()
        self._global_spectral = None
        self._global_topology = None
        logger.info("Layer2_Relational_Ultimate reset.")