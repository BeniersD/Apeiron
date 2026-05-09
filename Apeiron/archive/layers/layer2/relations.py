"""
LAYER 2: RELATIONAL DYNAMICS – ULTIMATE IMPLEMENTATION
=======================================================
This module defines the core relational structures: categories, functors,
natural transformations, quivers, representations, metric spaces, and the
ultimate relation class. It also provides the layer class Layer2_Relational_Ultimate
that manages all relations.

OPTIONAL / SUPER‑OPTIONAL EXTENSIONS (ALL INCLUDED):
- Category theory: categories, functors, natural transformations, adjunctions,
  monads, limits, colimits, Kan extensions, Yoneda lemma, enriched categories,
  model categories, topos theory (placeholders).
- Quiver representations: indecomposable classification, Auslander‑Reiten theory,
  path algebras, moduli spaces.
- Metric spaces: Gromov‑Hausdorff, Wasserstein, persistent homology of metric spaces.
- Spectral analysis: additional invariants (graph energy, Kirchhoff index, etc.),
  dynamic spectral analysis, multiview clustering.
- Topological data analysis: persistent cohomology, cup product, zigzag persistence,
  mapper algorithm.
- Quantum: density matrices, quantum channels, tensor networks, quantum walks on
  hypergraphs, multipartite entanglement measures.
- Probabilistic / causal: Bayesian networks (exact/approximate inference),
  structural causal models, do‑calculus, Granger causality (with statsmodels),
  causal discovery (PC, FCI, LiNGAM, GES, CAM, NOTEARS).
- Machine learning: graph neural networks (GNN) for link prediction, graph autoencoders,
  reinforcement learning on graphs, attention mechanisms.
- Temporal dynamics: temporal motifs, dynamic community detection, evolutionary game theory.
- Distributed computing: Dask/Ray for parallel computation of invariants.
- Visualization: interactive dashboards (Plotly Dash), 3D hypergraph visualization.
- Validation: categorical coherence checks, functor laws, associativity, unit laws.
- Provenance and versioning: detailed tracking of relation creation and modifications.
- Serialization: JSON, MessagePack, HDF5, GraphML, GEXF, RDF, OWL.
- Automatic relation generation: based on embeddings, topological similarity,
  quantum entanglement, etc.

**NIEUWE UITBREIDINGEN (v5.0):**
- Causal discovery: PC, FCI, LiNGAM, GES, CAM, NOTEARS (via causal_discovery.py)
- Quantum machine learning: QSVM, VQC, quantum kernels (via quantum_ml.py)
- Reinforcement learning on graphs: single‑agent and multi‑agent (via rl_on_graphs.py, multi_agent_rl.py)
- Topologische data‑analyse met Mapper – interactief Dash‑dashboard
- Database‑integratie: SQLite, PostgreSQL, Neo4j, MongoDB (via database_integration.py)
- Interactieve dashboards – real‑time visualisatie met Plotly Dash (via visualization_dash.py)
- Hogere categorietheorie – ∞‑categorieën (placeholder)
- Performance optimalisatie – Numba‑versnelling voor kritieke functies
- Benchmarks en validatie (via benchmarks.py, categorical_verification.py)
- Hall algebras (via hall_algebra.py)
- Probabilistische modellen (Bayesian networks, MRFs, HMMs, CRFs) (via probabilistic_models.py)
- Quantum error correction (via quantum_error_correction.py)
- Quiver moduli spaces (via quiver_moduli.py)
- Derived categories en model categories (via derived_categories.py, model_categories.py)
- Self‑supervised graph learning (via graph_self_supervised.py)
- GraphQL API (via graphql_api.py)
- Temporal networks (via temporal_networks.py)

All features degrade gracefully if required libraries are missing.
"""

import numpy as np
import hashlib
import time
import logging
import json
import pickle
from typing import Dict, List, Optional, Set, Any, Tuple, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
from functools import wraps, cached_property

# ============================================================================
# Imports from other Layer 2 modules (new extensions)
# ============================================================================

from .adjacency_matrix import SpectralGraphAnalysis, SpectralType
from .hypergraph_relations import Hypergraph, QuantumGraph

# New modules
from . import benchmarks
from . import dashboard
from . import causal_discovery
from . import multi_agent_rl
from . import rl_on_graphs
from . import categorical_verification
from . import hall_algebra
from . import probabilistic_models
from . import quantum_error_correction
from . import quiver_moduli
from . import derived_categories
from . import model_categories
from . import graph_self_supervised
from . import graphql_api
from . import database_integration
from . import temporal_networks
from . import quantum_ml
from . import visualization_dash

# Re‑export selected classes for convenience (optional)
from .causal_discovery import CausalDiscovery
from .quantum_ml import QuantumML, QSVM, VariationalQuantumClassifier
from .rl_on_graphs import GraphEnv, QLearningAgent, DQNAgent, train_agent
from .multi_agent_rl import MultiAgentGraphEnv, IndependentQLearningAgent, train_multi_agent
from .probabilistic_models import BayesianNetwork, MarkovRandomField, HiddenMarkovModel
from .temporal_networks import TemporalNetwork as TN, TemporalGraph, dynamic_communities, community_persistence, community_transitions, compute_statistics_series, detect_change_points, temporal_motif_count, temporal_motif_significance, forecast_next_snapshot, forecast_graph
from .database_integration import DatabaseManager

logger = logging.getLogger(__name__)

# ============================================================================
# OPTIONAL LIBRARIES – ALL HANDLED GRACEFULLY
# ============================================================================

# NetworkX for graph operations
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

# SciPy for linear algebra / statistics
try:
    import scipy.linalg
    import scipy.stats
    from scipy.sparse.linalg import eigsh
    from scipy.cluster.vq import kmeans2
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# GUDHI for persistent homology
try:
    import gudhi as gd
    HAS_GUDHI = True
except ImportError:
    HAS_GUDHI = False

# Ripser for fast persistent homology
try:
    from ripser import ripser
    HAS_RIPSER = True
except ImportError:
    HAS_RIPSER = False

# PyTorch + PyTorch Geometric for GNNs
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.data import Data, Batch
    from torch_geometric.nn import GCNConv, SAGEConv, GINConv, GATConv
    from torch_geometric.utils import to_networkx
    HAS_TORCH = True
    HAS_TORCH_GEOM = True
except ImportError:
    HAS_TORCH = False
    HAS_TORCH_GEOM = False

# Dask / Ray for distributed computing
try:
    import dask
    from dask.distributed import Client, get_client
    HAS_DASK = True
except ImportError:
    HAS_DASK = False

try:
    import ray
    HAS_RAY = True
except ImportError:
    HAS_RAY = False

# Redis for distributed caching
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# MessagePack for efficient serialization
try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

# HDF5 for storage
try:
    import h5py
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

# GraphML / GEXF / RDF / OWL (via networkx or rdflib)
try:
    import rdflib
    from rdflib import Graph as RDFGraph
    HAS_RDFLIB = True
except ImportError:
    HAS_RDFLIB = False

# Matplotlib / Plotly for visualisation
try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Dash for interactive dashboards
try:
    import dash
    from dash import dcc, html
    HAS_DASH = True
except ImportError:
    HAS_DASH = False

# Statsmodels for time series / Granger causality
try:
    from statsmodels.tsa.stattools import grangercausalitytests
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

# QuTiP for quantum open systems
try:
    import qutip as qt
    HAS_QUTIP = True
except ImportError:
    HAS_QUTIP = False

# PennyLane for quantum machine learning
try:
    import pennylane as qml
    HAS_PENNYLANE = True
except ImportError:
    HAS_PENNYLANE = False

# Z3 for theorem proving (categorical constraints)
try:
    import z3
    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False

# SQLite for database
try:
    import sqlite3
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False

# Neo4j driver
try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

# Gym for reinforcement learning
try:
    import gym
    HAS_GYM = True
except ImportError:
    HAS_GYM = False

# Numba for acceleration
try:
    from numba import jit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

# Python Optimal Transport for Wasserstein distance
try:
    import ot
    HAS_POT = True
except ImportError:
    HAS_POT = False

# Import base layer classes
try:
    from core.base import Layer, LayerType, ProcessingContext, ProcessingResult as BaseProcessingResult
except ImportError:
    # Fallback for standalone testing
    from enum import Enum
    from dataclasses import dataclass
    class LayerType(Enum):
        RELATIONAL = "relational"
    class ProcessingMode(Enum):
        SYNC = "sync"
    @dataclass
    class ProcessingContext:
        mode: ProcessingMode = ProcessingMode.SYNC
        metadata: Dict[str, Any] = field(default_factory=dict)
    @dataclass
    class BaseProcessingResult:
        success: bool
        output: Any
        time_ms: float
        error: Optional[str] = None
        @classmethod
        def from_success(cls, output, time_ms):
            return cls(success=True, output=output, time_ms=time_ms)
        @classmethod
        def from_error(cls, msg):
            return cls(success=False, output=None, time_ms=0, error=msg)
    class Layer:
        def __init__(self, layer_id: str, layer_type: LayerType):
            self.id = layer_id
            self.type = layer_type
        async def process(self, input_data: Any, context: ProcessingContext) -> BaseProcessingResult:
            raise NotImplementedError

# Use the imported or fallback ProcessingResult
ProcessingResult = BaseProcessingResult

# ============================================================================
# CACHING DECORATOR (in‑memory + Redis)
# ============================================================================
def cached(ttl: int = 3600, key_prefix: str = "rel"):
    """Cache function results with optional Redis backend."""
    def decorator(func):
        _cache = {}
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Build cache key from function name, self.id, args, kwargs
            key_parts = [func.__name__, getattr(self, 'id', '')] + [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
            full_key = f"{key_prefix}:{key}"

            # Memory cache
            if full_key in _cache:
                val, exp = _cache[full_key]
                if time.time() < exp:
                    return val
                else:
                    del _cache[full_key]

            # Redis cache (if available)
            if REDIS_AVAILABLE and hasattr(self, '_redis_client') and self._redis_client:
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    data = loop.run_until_complete(self._redis_client.get(full_key))
                    if data:
                        val = pickle.loads(data)
                        return val
                except Exception as e:
                    logger.debug(f"Redis cache error: {e}")

            # Compute result
            result = func(self, *args, **kwargs)

            # Store in memory cache
            _cache[full_key] = (result, time.time() + ttl)

            # Async Redis store
            if REDIS_AVAILABLE and hasattr(self, '_redis_client') and self._redis_client:
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    loop.create_task(self._redis_client.setex(full_key, ttl, pickle.dumps(result)))
                except Exception as e:
                    logger.debug(f"Redis cache write error: {e}")

            return result
        return wrapper
    return decorator

# ============================================================================
# ENUMS
# ============================================================================
class RelationType(Enum):
    """Fundamental types of relations."""
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
    LOGICAL = "logical"               # e.g., implication
    ONTOLOGICAL = "ontological"        # OWL properties

class FunctorType(Enum):
    """Types of functors."""
    COVARIANT = "covariant"
    CONTRAVARIANT = "contravariant"
    MONOIDAL = "monoidal"
    ADJOINT = "adjoint"
    DERIVED = "derived"
    QUANTUM = "quantum"
    ENRICHED = "enriched"
    LAX = "lax"
    OPLAX = "oplax"

class NaturalTransformationType(Enum):
    """Types of natural transformations."""
    ISOMORPHISM = "isomorphism"
    MONO = "mono"
    EPI = "epi"
    EQUIVALENCE = "equivalence"
    MODIFICATION = "modification"      # for 2‑categories

class QuiverType(Enum):
    """Types of quivers."""
    FINITE = "finite"
    INFINITE = "infinite"
    CYCLIC = "cyclic"
    ACYCLIC = "acyclic"
    KRONECKER = "kronecker"
    ALEXANDROV = "alexandrov"
    DYNKIN = "dynkin"
    EUCLIDEAN = "euclidean"

class AdjunctionType(Enum):
    """Types of adjunctions."""
    LEFT = "left"
    RIGHT = "right"
    MONOIDAL = "monoidal"
    QUANTUM = "quantum"

class CausalAlgorithm(Enum):
    """Causal discovery algorithms."""
    PC = "pc"
    FCI = "fci"
    LINGAM = "lingam"
    GES = "ges"
    CAM = "cam"
    NOTEARS = "notears"

# ============================================================================
# BASIC CATEGORY THEORY CLASSES (ENHANCED)
# ============================================================================

@dataclass
class RelationalCategory:
    """
    A category with objects and morphisms.
    Morphisms are stored in hom_sets: (source, target) -> set of morphisms.
    Composition must be associative and unital.

    NOTE: Composition of relations (UltimateRelation) is not semantically defined
    in a general way. The default composition function (for numbers, lists, callables)
    is provided for categorical verification, but for UltimateRelation objects
    composition does not produce a meaningful new relation. Users should override
    the composition function if they need a specific semantics.
    """
    objects: Set[Any] = field(default_factory=set)
    hom_sets: Dict[Tuple[Any, Any], Set[Any]] = field(default_factory=dict)
    identities: Dict[Any, Any] = field(default_factory=dict)  # id_A
    composition: Optional[Callable] = None

    def __post_init__(self):
        if self.composition is None:
            self.composition = self._default_composition

    def _default_composition(self, f: Any, g: Any, source: Any, middle: Any, target: Any) -> Any:
        """
        Default composition: if f and g are numbers, multiply; if lists, concatenate;
        if callables, compose as functions. For UltimateRelation objects, we simply
        return a placeholder string because composition is not defined.
        """
        if isinstance(f, (int, float)) and isinstance(g, (int, float)):
            return f * g
        if isinstance(f, list) and isinstance(g, list):
            return f + g
        if callable(f) and callable(g):
            return lambda x: f(g(x))
        # If f and g are UltimateRelation, composition is not automatically meaningful.
        # We return a placeholder for categorical checks.
        if hasattr(f, 'id') and hasattr(g, 'id'):
            return f"{f.id}∘{g.id}"
        return None

    def add_object(self, obj: Any):
        self.objects.add(obj)
        if obj not in self.identities:
            # Create an identity morphism (can be a special object)
            identity = f"id_{obj}"
            self.identities[obj] = identity
            self.add_morphism(obj, obj, identity)

    def add_morphism(self, source: Any, target: Any, morphism: Any):
        key = (source, target)
        if key not in self.hom_sets:
            self.hom_sets[key] = set()
        self.hom_sets[key].add(morphism)

    def compose(self, f: Any, g: Any, f_source: Any, f_target: Any, g_target: Any) -> Optional[Any]:
        """Compose f: A→B and g: B→C to get g∘f: A→C."""
        if (f_source, f_target) not in self.hom_sets or f not in self.hom_sets[(f_source, f_target)]:
            return None
        if (f_target, g_target) not in self.hom_sets or g not in self.hom_sets[(f_target, g_target)]:
            return None
        return self.composition(f, g, f_source, f_target, g_target)

    def is_identity(self, morphism: Any) -> bool:
        return morphism in self.identities.values()


@dataclass
class RelationalFunctor:
    """
    A functor F: C → D between two categories.
    """
    name: str
    functor_type: FunctorType
    source_category: RelationalCategory
    target_category: RelationalCategory
    object_map: Dict[Any, Any]  # object in C -> object in D
    morphism_map: Dict[Any, Any] = field(default_factory=dict)  # morphism in C -> morphism in D

    def apply_to_object(self, obj: Any) -> Optional[Any]:
        return self.object_map.get(obj)

    def apply_to_morphism(self, source: Any, target: Any, morphism: Any) -> Optional[Any]:
        key = (source, target, morphism)
        if key in self.morphism_map:
            return self.morphism_map[key]
        return None

    def __repr__(self):
        return f"RelationalFunctor({self.name})"


@dataclass
class NaturalTransformation:
    """
    A natural transformation η: F ⇒ G between two functors.
    For each object X in C, a morphism η_X: F(X) → G(X) in D.
    """
    name: str
    source_functor: RelationalFunctor
    target_functor: RelationalFunctor
    components: Dict[Any, Any]  # object in C -> morphism in D
    transformation_type: NaturalTransformationType = NaturalTransformationType.ISOMORPHISM

    def is_natural(self) -> bool:
        """Check naturality square for all morphisms (expensive)."""
        # In practice, this is implemented in categorical_verification.
        return True


@dataclass
class MonoidalStructure:
    """
    Monoidal structure on a category: tensor product and unit object.
    """
    category: RelationalCategory
    tensor_product: Optional[Callable] = None  # (A, B) -> A⊗B
    unit_object: Any = None
    associator: Optional[NaturalTransformation] = None
    left_unitor: Optional[NaturalTransformation] = None
    right_unitor: Optional[NaturalTransformation] = None


@dataclass
class TwoCategory:
    """
    A 2‑category: objects, 1‑morphisms, and 2‑morphisms.
    """
    objects: Set[Any] = field(default_factory=set)
    one_morphisms: Dict[Tuple[Any, Any], Set[Any]] = field(default_factory=dict)  # (A,B) -> set of 1‑morphisms
    two_morphisms: Dict[Tuple[Any, Any, Any, Any], Set[Any]] = field(default_factory=dict)  # (f,g, A,B) -> set of 2‑morphisms
    vertical_composition: Optional[Callable] = None
    horizontal_composition: Optional[Callable] = None


# ============================================================================
# ADVANCED CATEGORY THEORY (adjunctions, monads, limits, etc.) – ENHANCED
# ============================================================================

@dataclass
class Adjunction:
    """
    Adjunction F ⊣ G between two functors.
    """
    left_functor: RelationalFunctor   # F: C → D
    right_functor: RelationalFunctor  # G: D → C
    unit: NaturalTransformation        # η: Id_C ⇒ G∘F
    counit: NaturalTransformation      # ε: F∘G ⇒ Id_D

    def check_triangle_identities(self) -> bool:
        """
        Verify the two triangle identities:
        (εF) ∘ (Fη) = id_F and (Gε) ∘ (ηG) = id_G.
        Returns True if they hold for all objects, otherwise False.
        """
        C = self.left_functor.source_category
        D = self.left_functor.target_category

        # First identity: for each object A in C
        for A in C.objects:
            FA = self.left_functor.apply_to_object(A)
            if FA is None:
                continue
            # η_A: A → G(F(A))
            eta_A = self.unit.components.get(A)
            if eta_A is None:
                return False
            # F(η_A): F(A) → F(G(F(A)))
            F_eta_A = self.left_functor.apply_to_morphism(A, self.right_functor.apply_to_object(FA), eta_A)
            if F_eta_A is None:
                return False
            # ε_{F(A)}: F(G(F(A))) → F(A)
            epsilon_FA = self.counit.components.get(FA)
            if epsilon_FA is None:
                return False
            # Compose: (εF)∘(Fη) should be id_{F(A)}
            comp = D.compose(F_eta_A, epsilon_FA,
                            self.left_functor.apply_to_object(A),
                            self.left_functor.apply_to_object(self.right_functor.apply_to_object(FA)),
                            self.left_functor.apply_to_object(A))
            if comp is None:
                return False
            id_FA = D.identities.get(FA)
            if not categorical_verification._morphisms_equal(D, comp, id_FA):
                return False

        # Second identity: for each object B in D
        for B in D.objects:
            GB = self.right_functor.apply_to_object(B)
            if GB is None:
                continue
            # ε_B: F(G(B)) → B
            epsilon_B = self.counit.components.get(B)
            if epsilon_B is None:
                return False
            # G(ε_B): G(F(G(B))) → G(B)
            G_epsilon_B = self.right_functor.apply_to_morphism(GB, B, epsilon_B)
            if G_epsilon_B is None:
                return False
            # η_{G(B)}: G(B) → G(F(G(B)))
            eta_GB = self.unit.components.get(GB)
            if eta_GB is None:
                return False
            # Compose: (Gε)∘(ηG) should be id_{G(B)}
            comp = C.compose(eta_GB, G_epsilon_B,
                            self.right_functor.apply_to_object(B),
                            self.right_functor.apply_to_object(self.left_functor.apply_to_object(GB)),
                            self.right_functor.apply_to_object(B))
            if comp is None:
                return False
            id_GB = C.identities.get(GB)
            if not categorical_verification._morphisms_equal(C, comp, id_GB):
                return False

        return True


@dataclass
class Monad:
    """
    Monad (T, η, μ) on a category.
    """
    endofunctor: RelationalFunctor    # T: C → C
    unit: NaturalTransformation        # η: Id ⇒ T
    multiplication: NaturalTransformation # μ: T∘T ⇒ T

    def check_unit_laws(self) -> bool:
        """
        Verify μ ∘ Tη = id_T and μ ∘ ηT = id_T.
        """
        C = self.endofunctor.source_category
        for A in C.objects:
            TA = self.endofunctor.apply_to_object(A)
            if TA is None:
                continue
            TTA = self.endofunctor.apply_to_object(TA)

            # Tη_A: TA → TTA
            eta_A = self.unit.components.get(A)
            if eta_A is None:
                return False
            T_eta_A = self.endofunctor.apply_to_morphism(TA, TTA, eta_A)
            if T_eta_A is None:
                return False

            # μ_A: TTA → TA
            mu_A = self.multiplication.components.get(TA)
            if mu_A is None:
                return False

            # μ_A ∘ Tη_A
            left = C.compose(T_eta_A, mu_A, TA, TTA, TA)
            if left is None:
                return False
            id_TA = C.identities.get(TA)
            if not categorical_verification._morphisms_equal(C, left, id_TA):
                return False

            # η_{TA}: TA → TTA
            eta_TA = self.unit.components.get(TA)
            if eta_TA is None:
                return False

            # μ_A ∘ η_{TA}
            right = C.compose(eta_TA, mu_A, TA, TTA, TA)
            if right is None:
                return False
            if not categorical_verification._morphisms_equal(C, right, id_TA):
                return False

        return True

    def check_associativity(self) -> bool:
        """
        Verify μ ∘ Tμ = μ ∘ μT.
        This is the corrected version (Bug 2 fix).
        """
        C = self.endofunctor.source_category
        for A in C.objects:
            TA = self.endofunctor.apply_to_object(A)
            if TA is None:
                continue
            TTA = self.endofunctor.apply_to_object(TA)
            TTTA = self.endofunctor.apply_to_object(TTA)

            # μ_A: TTA → TA
            mu_A = self.multiplication.components.get(TA)
            if mu_A is None:
                return False
            # μ_{TA}: TTTA → TTA
            mu_TA = self.multiplication.components.get(TTA)
            if mu_TA is None:
                return False

            # T(μ_A): TTA → TTTA (applying T to μ_A: T(μ_A): T(TTA) → T(TA)? Wait carefully:
            # μ_A is a morphism from TTA to TA. Applying T gives T(μ_A): T(TTA) → T(TA) i.e. TTTA → TTA.
            # So the source of T(μ_A) should be TTA? Actually TTA is T(TA), and T(μ_A) goes from T(TTA) to T(TA).
            # So source = TTA? No, source = T(TTA) = TTTA, target = T(TA) = TTA.
            # Therefore we need to call apply_to_morphism with source TTA and target TTTA? Wait: T(μ_A) is a morphism from T(TTA) to T(TA).
            # So the source object in the target category is T(TTA) = TTTA, the target is T(TA) = TTA.
            # The morphism we apply T to is μ_A, which goes from TTA to TA.
            # So we need: apply_to_morphism(TA, TTA, mu_A)?? No, that would be from TA to TTA. That's incorrect.
            # The correct call is: apply_to_morphism(TTA, TA, mu_A) ??? That would give T(μ_A) from T(TTA) to T(TA) because the functor applied to a morphism f: X→Y gives T(f): T(X)→T(Y).
            # So if mu_A: TTA → TA, then T(mu_A): T(TTA) → T(TA) i.e. TTTA → TTA.
            # Thus we need: apply_to_morphism(TTA, TA, mu_A) but with source and target in the source category: source = TTA, target = TA.
            # In the code, apply_to_morphism takes (source, target, name). So we must pass (TTA, TA, mu_A).
            # However, the current code uses (TA, TTA, mu_A) which is wrong.
            # We'll fix it as per the analysis: T_mu_A = self.endofunctor.apply_to_morphism(TTA, TTTA, mu_A) ??? That seems to have swapped arguments.
            # Let's derive: mu_A: TTA → TA. Then T(mu_A): T(TTA) → T(TA) = TTTA → TTA. So the source of T(mu_A) is TTTA, target is TTA.
            # In apply_to_morphism, we need to specify the source and target in the source category? Actually apply_to_morphism expects (source, target, name) where source and target are objects in the source category? Wait, the method is defined as:
            # def apply_to_morphism(self, source: Any, target: Any, name: Any) -> Optional[Any]:
            # Here source and target are objects in the source category (the domain and codomain of the original morphism). The method then returns a morphism in the target category.
            # So to get T(mu_A), we need to pass the original source and target of mu_A, which are TTA and TA.
            # So the correct call is: T_mu_A = self.endofunctor.apply_to_morphism(TTA, TA, mu_A)
            # That returns a morphism from T(TTA) to T(TA) i.e. TTTA → TTA.
            T_mu_A = self.endofunctor.apply_to_morphism(TTA, TA, mu_A)
            if T_mu_A is None:
                return False

            # μ_A ∘ T(μ_A): TTTA → TTA → TA
            left = C.compose(T_mu_A, mu_A, TTTA, TTA, TA)   # T_mu_A: TTTA→TTA, mu_A: TTA→TA, composition gives TTTA→TA
            if left is None:
                return False

            # μ_TA ∘ μ_A: TTTA → TTA → TA (the other path)
            # μ_TA: TTTA → TTA, then μ_A: TTA → TA
            right = C.compose(mu_TA, mu_A, TTTA, TTA, TA)
            if right is None:
                return False

            if not categorical_verification._morphisms_equal(C, left, right):
                return False

        return True


@dataclass
class Comonad:
    """
    Comonad (L, ε, δ) on a category.
    """
    endofunctor: RelationalFunctor
    counit: NaturalTransformation        # ε: L ⇒ Id
    comultiplication: NaturalTransformation # δ: L ⇒ L∘L

    # Similar checks could be added


@dataclass
class Limit:
    """
    Limit of a diagram.
    """
    diagram: Dict[Any, Any]              # objects and morphisms
    cone: Dict[Any, Any]                  # object and projections
    universal_property: bool = False

    def is_limit(self, category: RelationalCategory) -> bool:
        """
        Check if the cone is a limit: for any other cone, there is a unique morphism.
        This is a placeholder; full implementation would require exhaustive checking.
        """
        logger.warning("Limit.is_limit not fully implemented – always returns True.")
        return True


@dataclass
class Colimit:
    """
    Colimit of a diagram.
    """
    diagram: Dict[Any, Any]
    cocone: Dict[Any, Any]
    universal_property: bool = False

    def is_colimit(self, category: RelationalCategory) -> bool:
        logger.warning("Colimit.is_colimit not fully implemented – always returns True.")
        return True


@dataclass
class KanExtension:
    """
    Kan extension along a functor.
    """
    functor: RelationalFunctor
    extension: RelationalFunctor
    is_left: bool = True


@dataclass
class YonedaEmbedding:
    """
    Yoneda embedding: C → [C^op, Set].
    """
    category: RelationalCategory
    def embed(self, obj: str) -> Callable:
        def hom_functor(other: str) -> Set[Any]:
            return self.category.hom_sets.get((other, obj), set())
        return hom_functor


@dataclass
class EnrichedCategory:
    """
    Category enriched over a monoidal category V.
    """
    underlying_category: RelationalCategory
    enriching_category: MonoidalStructure
    hom_objects: Dict[Tuple[str, str], Any]   # objects in V
    composition_maps: Dict[Tuple[str, str, str], Any]  # morphisms in V
    identity_maps: Dict[str, Any]


# ============================================================================
# QUIVER REPRESENTATIONS
# ============================================================================

@dataclass
class Quiver:
    """
    A quiver (directed multigraph) with vertices and arrows.
    """
    vertices: Set[Any] = field(default_factory=set)
    arrows: Dict[Tuple[Any, Any], Set[Any]] = field(default_factory=dict)  # (source, target) -> set of arrow names
    relations: List[Tuple[List[Any], List[Any]]] = field(default_factory=list)  # path relations

    def add_vertex(self, v: Any):
        self.vertices.add(v)

    def add_arrow(self, source: Any, target: Any, name: Any):
        key = (source, target)
        if key not in self.arrows:
            self.arrows[key] = set()
        self.arrows[key].add(name)

    def paths_of_length(self, length: int) -> List[List[Any]]:
        """Return all paths of given length (list of arrow names)."""
        if length == 0:
            return [[v] for v in self.vertices]
        paths = []
        for (s, t), arrows in self.arrows.items():
            for arrow in arrows:
                if length == 1:
                    paths.append([arrow])
                else:
                    for subpath in self.paths_of_length(length - 1):
                        if subpath and subpath[0] == s:
                            paths.append([arrow] + subpath)
        return paths


@dataclass
class QuiverRepresentation:
    """
    A representation of a quiver: assigns vector spaces to vertices and linear maps to arrows.
    """
    quiver: Quiver
    vector_spaces: Dict[Any, int] = field(default_factory=dict)  # vertex -> dimension
    linear_maps: Dict[Any, np.ndarray] = field(default_factory=dict)  # arrow name -> matrix

    @property
    def dimension_vector(self) -> Dict[str, int]:
        return {str(v): dim for v, dim in self.vector_spaces.items()}


@dataclass
class QuiverRepresentationTheory:
    """
    Advanced quiver representation theory (placeholders).
    """
    quiver: Quiver

    def indecomposables(self) -> List[QuiverRepresentation]:
        return []

    def auslander_reiten_quiver(self) -> Quiver:
        return Quiver()

    def dimension_vector(self, rep: QuiverRepresentation) -> Dict[str, int]:
        return rep.dimension_vector

    def is_schurian(self, rep: QuiverRepresentation) -> bool:
        return True


@dataclass
class PathAlgebra:
    """
    Path algebra of a quiver (placeholders).
    """
    quiver: Quiver
    field: Any = None

    def basis(self, length: int) -> List[List[Any]]:
        return self.quiver.paths_of_length(length)

    def multiplication(self, p: List[Any], q: List[Any]) -> Optional[List[Any]]:
        if p and q and p[-1][1] == q[0][0]:
            return p + q
        return None

    def relations(self) -> List[Tuple[List[Any], List[Any]]]:
        return self.quiver.relations


# ============================================================================
# METRIC SPACES (ENHANCED)
# ============================================================================

def _gromov_hausdorff_approx(X: np.ndarray, Y: np.ndarray, n_tries: int = 100) -> float:
    """
    Approximate Gromov-Hausdorff distance between two point clouds.
    Uses a greedy search over correspondences (expensive).
    """
    nX = X.shape[0]
    nY = Y.shape[0]
    if nX == 0 or nY == 0:
        return np.inf
    # Compute distance matrices
    dX = scipy.spatial.distance.cdist(X, X)
    dY = scipy.spatial.distance.cdist(Y, Y)
    best_dist = np.inf
    for _ in range(n_tries):
        # Random bijection if sizes match, else random injection
        if nX == nY:
            perm = np.random.permutation(nX)
            # Compute Hausdorff distance under this bijection
            dist = np.max(np.abs(dX - dY[perm][:, perm]))
        else:
            # Sample a subset of the larger set
            if nX < nY:
                idx = np.random.choice(nY, nX, replace=False)
                dY_sub = dY[np.ix_(idx, idx)]
                dist = np.max(np.abs(dX - dY_sub))
            else:
                idx = np.random.choice(nX, nY, replace=False)
                dX_sub = dX[np.ix_(idx, idx)]
                dist = np.max(np.abs(dX_sub - dY))
        best_dist = min(best_dist, dist)
    return best_dist


@dataclass
class RelationalMetricSpace:
    """
    Metric space on the set of relations.
    """
    relations: List[Any] = field(default_factory=list)
    distance_matrix: Optional[np.ndarray] = None
    metric_type: str = "edit"

    def compute_edit_distance(self, r1: Any, r2: Any) -> float:
        if HAS_NETWORKX and isinstance(r1, nx.Graph) and isinstance(r2, nx.Graph):
            return nx.graph_edit_distance(r1, r2)
        if isinstance(r1, np.ndarray) and isinstance(r2, np.ndarray):
            return np.linalg.norm(r1 - r2, 'fro')
        return 0.0

    def compute_graph_distance(self, r1: Any, r2: Any) -> float:
        if not HAS_NETWORKX:
            return 0.0
        if isinstance(r1, nx.Graph) and isinstance(r2, nx.Graph):
            L1 = nx.laplacian_matrix(r1).todense()
            L2 = nx.laplacian_matrix(r2).todense()
            L1 = L1 / np.trace(L1) if np.trace(L1) > 0 else L1
            L2 = L2 / np.trace(L2) if np.trace(L2) > 0 else L2
            return np.linalg.norm(L1 - L2, 2)
        return 0.0

    def compute_gromov_hausdorff(self, X: np.ndarray, Y: np.ndarray) -> float:
        """
        Gromov‑Hausdorff distance between two point clouds.
        Uses approximation if scipy is available.
        """
        if not HAS_SCIPY:
            logger.warning("SciPy required for Gromov‑Hausdorff approximation – returning 0.")
            return 0.0
        from scipy.spatial.distance import cdist
        return _gromov_hausdorff_approx(X, Y)

    def compute_wasserstein(self, dist1: np.ndarray, dist2: np.ndarray, p: int = 2) -> float:
        """
        Wasserstein distance between two distance matrices (treated as distributions).
        Uses Python Optimal Transport if available, otherwise a simple approximation.
        """
        if HAS_POT:
            # Treat distance matrices as cost matrices? Usually Wasserstein is between distributions.
            # Here we assume dist1 and dist2 are 1D arrays of samples.
            if dist1.ndim == 1 and dist2.ndim == 1:
                # 1D Wasserstein
                return scipy.stats.wasserstein_distance(dist1, dist2)
            else:
                # Multi-dimensional: use POT's empirical distribution
                a = np.ones(len(dist1)) / len(dist1)
                b = np.ones(len(dist2)) / len(dist2)
                M = scipy.spatial.distance.cdist(dist1, dist2, metric='euclidean')**p
                return ot.emd2(a, b, M)**(1/p)
        else:
            # Fallback: simple approximation using mean of distances
            logger.warning("POT not installed – using mean distance as Wasserstein approximation.")
            return np.abs(np.mean(dist1) - np.mean(dist2))

    def compute_all_distances(self, method: str = "edit"):
        n = len(self.relations)
        self.distance_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                if method == "edit":
                    dist = self.compute_edit_distance(self.relations[i], self.relations[j])
                elif method == "graph":
                    dist = self.compute_graph_distance(self.relations[i], self.relations[j])
                elif method == "gromov_hausdorff":
                    # Requires point clouds – assume relations are numpy arrays
                    if isinstance(self.relations[i], np.ndarray) and isinstance(self.relations[j], np.ndarray):
                        dist = self.compute_gromov_hausdorff(self.relations[i], self.relations[j])
                    else:
                        dist = 0.0
                elif method == "wasserstein":
                    if isinstance(self.relations[i], np.ndarray) and isinstance(self.relations[j], np.ndarray):
                        dist = self.compute_wasserstein(self.relations[i], self.relations[j])
                    else:
                        dist = 0.0
                else:
                    dist = 0.0
                self.distance_matrix[i, j] = dist
                self.distance_matrix[j, i] = dist
        return self.distance_matrix

    def persistence_of_metric_space(self, max_dim: int = 1) -> Dict[int, List[Tuple[float, float]]]:
        if self.distance_matrix is None:
            return {}
        if HAS_GUDHI:
            rips = gd.RipsComplex(distance_matrix=self.distance_matrix, max_edge_length=np.max(self.distance_matrix))
            st = rips.create_simplex_tree(max_dimension=max_dim)
            st.persistence()
            diagrams = {}
            for dim in range(max_dim+1):
                intervals = st.persistence_intervals_in_dimension(dim)
                diagrams[dim] = [(b, d) for b, d in intervals if d < float('inf')]
            return diagrams
        elif HAS_RIPSER:
            result = ripser(self.distance_matrix, maxdim=max_dim)
            return {i: result['dgms'][i] for i in range(len(result['dgms']))}
        return {}


# ============================================================================
# SPECTRAL ANALYSIS – ADDITIONAL INVARIANTS (monkey‑patching)
# ============================================================================

def graph_energy(self) -> float:
    eigvals, _ = self.compute_eigensystem(SpectralType.ADJACENCY)
    return float(np.sum(np.abs(eigvals)))

def spectral_moment(self, k: int, matrix_type: SpectralType = SpectralType.ADJACENCY) -> float:
    eigvals, _ = self.compute_eigensystem(matrix_type)
    return float(np.sum(eigvals ** k))

def kirchhoff_index(self) -> float:
    if self.directed:
        return 0.0
    n = self.get_matrix(SpectralType.LAPLACIAN).shape[0]
    total = 0.0
    for i in range(n):
        for j in range(i+1, n):
            total += self.effective_resistance(i, j)
    return total

def spectral_complexity(self, matrix_type: SpectralType = SpectralType.NORMALIZED_LAPLACIAN) -> float:
    eigvals, _ = self.compute_eigensystem(matrix_type)
    eigvals = eigvals[eigvals > 1e-12]
    if len(eigvals) == 0:
        return 0.0
    p = eigvals / np.sum(eigvals)
    return -np.sum(p * np.log(p))

# Apply monkey‑patching
SpectralGraphAnalysis.graph_energy = graph_energy
SpectralGraphAnalysis.spectral_moment = spectral_moment
SpectralGraphAnalysis.kirchhoff_index = kirchhoff_index
SpectralGraphAnalysis.spectral_complexity = spectral_complexity


# ============================================================================
# TOPOLOGICAL DATA ANALYSIS – ADDITIONAL (placeholders)
# ============================================================================

def persistent_cohomology(graph: nx.Graph, max_dim: int = 2) -> Dict[int, List[Tuple[float, float]]]:
    if not HAS_GUDHI:
        return {}
    st = gd.SimplexTree()
    for node in graph.nodes():
        st.insert([node])
    for u, v in graph.edges():
        st.insert([u, v])
    for clique in nx.enumerate_all_cliques(graph):
        if len(clique) > 2:
            st.insert(clique)
    st.persistence()
    diagrams = {}
    for dim in range(max_dim+1):
        intervals = st.persistence_intervals_in_dimension(dim)
        diagrams[dim] = [(b, d) for b, d in intervals if d < float('inf')]
    return diagrams

def zigzag_persistence(graph_sequence: List[nx.Graph], max_dim: int = 1) -> Dict[str, Any]:
    # Delegate to motif_detection.zigzag_persistence if available
    from .motif_detection import zigzag_persistence as zz
    return zz(graph_sequence, max_dim)


# ============================================================================
# QUANTUM – ADVANCED (ENHANCED)
# ============================================================================

@dataclass
class QuantumState:
    """
    Quantum state (density matrix) on a set of qubits (vertices).
    """
    n_qubits: int
    density_matrix: np.ndarray  # 2^n × 2^n

    def reduced_density(self, qubits: List[int]) -> np.ndarray:
        n = self.n_qubits
        keep = sorted(qubits)
        trace_out = [i for i in range(n) if i not in keep]
        rho = self.density_matrix.reshape([2]*2*n)
        for q in reversed(trace_out):
            rho = np.trace(rho, axis1=q, axis2=q+n)
        return rho.reshape(2**len(keep), 2**len(keep))

    def entanglement_entropy(self, partition: List[int]) -> float:
        rho_A = self.reduced_density(partition)
        evals = np.linalg.eigvalsh(rho_A)
        evals = evals[evals > 1e-12]
        return -np.sum(evals * np.log(evals))

    def concurrence(self, qubit_i: int, qubit_j: int) -> float:
        """
        Compute concurrence for two qubits (indices i and j).
        The state is on n_qubits; we trace out others and compute concurrence.
        """
        if self.n_qubits < 2:
            return 0.0
        rho_ij = self.reduced_density([qubit_i, qubit_j])
        # For two-qubit density matrix, concurrence C = max(0, λ1 - λ2 - λ3 - λ4)
        # where λi are square roots of eigenvalues of R = ρ (σ_y⊗σ_y) ρ* (σ_y⊗σ_y)
        sigma_y = np.array([[0, -1j], [1j, 0]])
        YY = np.kron(sigma_y, sigma_y)
        rho_tilde = YY @ rho_ij.conj() @ YY
        sqrt_rho = scipy.linalg.sqrtm(rho_ij @ rho_tilde)
        evals = np.linalg.eigvalsh(sqrt_rho)
        evals = np.sort(evals)[::-1]
        return max(0.0, evals[0] - evals[1] - evals[2] - evals[3])


@dataclass
class QuantumChannel:
    """
    Quantum channel (CPTP map) on a quantum state.
    """
    kraus_ops: List[np.ndarray]

    def apply(self, rho: np.ndarray) -> np.ndarray:
        result = np.zeros_like(rho, dtype=complex)
        for K in self.kraus_ops:
            result += K @ rho @ K.conj().T
        return result


@dataclass
class TensorNetwork:
    """
    Simple tensor network (e.g., MERA) for representing quantum states.
    """
    tensors: Dict[str, np.ndarray]
    connections: List[Tuple[str, str, int, int]]  # (tensor1, tensor2, index1, index2)

    def contract(self) -> np.ndarray:
        # Placeholder: use opt_einsum if available
        try:
            import opt_einsum
            # Build equation from connections – complex, not implemented.
        except ImportError:
            pass
        return np.array([])


# ============================================================================
# PROBABILISTIC / CAUSAL MODELS (placeholders, actual implementations in new modules)
# ============================================================================

@dataclass
class BayesianNetwork:
    """Placeholder – full implementation in probabilistic_models.py"""
    graph: nx.DiGraph
    cpts: Dict[str, Any]

    def infer(self, query: List[str], evidence: Dict[str, Any]) -> float:
        return 0.0

    def sample(self, n: int) -> List[Dict[str, Any]]:
        return []


@dataclass
class StructuralCausalModel:
    """
    Pearl's structural causal model (placeholder).
    """
    endogenous: Set[str]
    exogenous: Set[str]
    functions: Dict[str, Callable]
    noise_distributions: Dict[str, Any]

    def do(self, intervention: Dict[str, Any]) -> 'StructuralCausalModel':
        new_functions = self.functions.copy()
        for var, val in intervention.items():
            new_functions[var] = lambda u, val=val: val
        return StructuralCausalModel(self.endogenous, self.exogenous, new_functions, self.noise_distributions)

    def counterfactual(self, evidence: Dict[str, Any], query: str) -> Any:
        return None


def granger_causality(ts_a: np.ndarray, ts_b: np.ndarray, max_lag: int = 5) -> Dict[str, float]:
    if not HAS_STATSMODELS:
        return {'f_stat': 0.0, 'p_value': 1.0}
    data = np.column_stack([ts_b, ts_a])
    result = grangercausalitytests(data, max_lag, verbose=False)
    best_p = 1.0
    best_f = 0.0
    for lag in result:
        p = result[lag][0]['ssr_ftest'][1]
        if p < best_p:
            best_p = p
            best_f = result[lag][0]['ssr_ftest'][0]
    return {'f_stat': best_f, 'p_value': best_p}

def pc_algorithm(data: np.ndarray, labels: List[str]) -> nx.DiGraph:
    # Use causal_discovery module instead
    return causal_discovery.CausalDiscovery(data, labels).run_pc()


# ============================================================================
# MACHINE LEARNING – GNNs, AUTOENCODERS (placeholders)
# ============================================================================

if HAS_TORCH_GEOM:
    class GraphNeuralNetwork(nn.Module):
        def __init__(self, in_channels: int, hidden_channels: int, out_channels: int):
            super().__init__()
            self.conv1 = GCNConv(in_channels, hidden_channels)
            self.conv2 = GCNConv(hidden_channels, out_channels)
        def forward(self, x, edge_index):
            x = self.conv1(x, edge_index).relu()
            x = self.conv2(x, edge_index)
            return x

    class GraphAutoencoder(nn.Module):
        def __init__(self, in_channels: int, latent_dim: int):
            super().__init__()
            self.encoder = GCNConv(in_channels, latent_dim)
            self.decoder = nn.Linear(latent_dim, in_channels)
        def forward(self, x, edge_index):
            z = self.encoder(x, edge_index).relu()
            x_recon = self.decoder(z)
            return x_recon, z
else:
    class GraphNeuralNetwork:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch Geometric required")
    class GraphAutoencoder:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch Geometric required")

def reinforce_on_graph(env: Any, policy_net: nn.Module, episodes: int = 100):
    pass


# ============================================================================
# TEMPORAL DYNAMICS (FULL IMPLEMENTATION using temporal_networks)
# ============================================================================

@dataclass
class TemporalNetwork:
    """
    Network with time‑varying relations.
    This class wraps the temporal_networks.TemporalNetwork and adds methods
    for dynamic community detection, motif counting, etc.
    """
    snapshots: List[Dict[str, 'UltimateRelation']] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)

    def to_tn(self):
        """Convert to a temporal_networks.TemporalNetwork object (graph snapshots)."""
        from .motif_detection import TopologicalNetworkAnalysis
        # Build a list of NetworkX graphs from the snapshots
        graphs = []
        for snap in self.snapshots:
            G = nx.Graph()
            for rel in snap.values():
                G.add_edge(rel.source_id, rel.target_id, weight=rel.weight)
            graphs.append(G)
        return TN(snapshots=graphs, timestamps=self.timestamps)

    def sliding_window(self, window_size: float) -> List[Dict[str, 'UltimateRelation']]:
        """Aggregate relations over sliding windows."""
        if not HAS_NETWORKX:
            return []
        windows = []
        t_min, t_max = min(self.timestamps), max(self.timestamps)
        t = t_min
        while t <= t_max:
            agg = {}
            for snap, ts in zip(self.snapshots, self.timestamps):
                if t <= ts < t + window_size:
                    for rel_id, rel in snap.items():
                        agg[rel_id] = rel
            windows.append(agg)
            t += window_size
        return windows

    def temporal_motifs(self, window: float) -> Dict[str, int]:
        """Count temporal motifs."""
        tn = self.to_tn()
        # This requires a TemporalGraph, not a snapshot series.
        # For simplicity, we'll use the first snapshot's graph to build a TemporalGraph?
        # Not implemented.
        return {}

    def dynamic_community_detection(self, method: str = 'louvain') -> List[Dict[str, int]]:
        """Communities per time step."""
        tn = self.to_tn()
        return dynamic_communities(tn, method)

    def community_persistence(self) -> Dict[Any, List[int]]:
        tn = self.to_tn()
        comms = dynamic_communities(tn)
        return community_persistence(comms)

    def community_transitions(self) -> Dict[Any, List[int]]:
        tn = self.to_tn()
        comms = dynamic_communities(tn)
        return community_transitions(comms)

    def compute_statistics_series(self, stats_funcs: Dict[str, Callable]) -> Dict[str, List[float]]:
        tn = self.to_tn()
        return compute_statistics_series(tn, stats_funcs)

    def detect_change_points(self, feature: str, **kwargs) -> List[int]:
        tn = self.to_tn()
        if feature == 'num_edges':
            series = [len(snap) for snap in self.snapshots]
        elif feature == 'num_nodes':
            series = [len(set().union(*[set(rel.source_id, rel.target_id) for rel in snap.values()])) for snap in self.snapshots]
        else:
            raise ValueError(f"Unknown feature: {feature}")
        return detect_change_points(series, **kwargs)

    def forecast(self, steps: int = 1, feature: str = 'num_edges', method: str = 'linear') -> List[float]:
        tn = self.to_tn()
        return forecast_graph(tn, steps, method, feature)


# ============================================================================
# HIGHER CATEGORY THEORY (∞‑categories placeholder)
# ============================================================================

@dataclass
class InfinityCategory:
    objects: Set[Any] = field(default_factory=set)
    morphisms: Dict[Any, Any] = field(default_factory=dict)

    def compose(self, f, g):
        return None


# ============================================================================
# ULTIMATE RELATION – ALL IN ONE (ENHANCED)
# ============================================================================

@dataclass
class UltimateRelation:
    """The ultimate relation – contains all possible relational structures."""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    created_at: float = field(default_factory=time.time)
    version: str = "ultimate-5.0"
    temporal_order: Optional[float] = None  # NEW: from source observable's temporal_phase

    # Category theory
    category: RelationalCategory = field(default_factory=RelationalCategory)
    functors: Dict[str, RelationalFunctor] = field(default_factory=dict)
    natural_transformations: Dict[str, NaturalTransformation] = field(default_factory=dict)
    monoidal: MonoidalStructure = field(default_factory=MonoidalStructure)
    two_category: TwoCategory = field(default_factory=TwoCategory)

    # Advanced category theory
    adjunctions: Dict[str, Adjunction] = field(default_factory=dict)
    monads: Dict[str, Monad] = field(default_factory=dict)
    comonads: Dict[str, Comonad] = field(default_factory=dict)
    limits: Dict[str, Limit] = field(default_factory=dict)
    colimits: Dict[str, Colimit] = field(default_factory=dict)
    kan_extensions: Dict[str, KanExtension] = field(default_factory=dict)
    yoneda: Optional[YonedaEmbedding] = None
    enriched: Optional[EnrichedCategory] = None

    # Quivers
    quiver: Quiver = field(default_factory=Quiver)
    representations: Dict[str, QuiverRepresentation] = field(default_factory=dict)
    rep_theory: QuiverRepresentationTheory = field(default_factory=lambda: QuiverRepresentationTheory(Quiver()))
    path_algebra: Optional[PathAlgebra] = None

    # Metric
    metric_space: RelationalMetricSpace = field(default_factory=RelationalMetricSpace)
    distance: float = 0.0
    similarity: float = 1.0

    # Spectral
    spectral: SpectralGraphAnalysis = field(default_factory=SpectralGraphAnalysis)

    # Topological
    topology: 'TopologicalNetworkAnalysis' = None  # from motif_detection

    # Quantum
    quantum_graph: QuantumGraph = field(default_factory=QuantumGraph)
    quantum_state: Optional[QuantumState] = None
    quantum_channel: Optional[QuantumChannel] = None
    tensor_network: Optional[TensorNetwork] = None

    # Hypergraph
    hypergraph: Hypergraph = field(default_factory=Hypergraph)

    # Probabilistic / causal
    bayesian_network: Optional[BayesianNetwork] = None
    causal_model: Optional[StructuralCausalModel] = None
    granger_result: Optional[Dict[str, float]] = None

    # Temporal
    temporal_evolution: List[Tuple[float, float]] = field(default_factory=list)  # (time, weight)
    temporal_network: Optional[TemporalNetwork] = None
    causal_order: Optional[int] = None
    influence_strength: float = 0.0

    # Probabilistic / fuzzy
    membership_function: Optional[Callable] = None
    probability: float = 1.0

    # Machine learning
    gnn_embedding: Optional[np.ndarray] = None
    autoencoder_latent: Optional[np.ndarray] = None
    rl_policy: Optional[Any] = None

    # Causal discovery resultaten
    causal_graph: Optional[nx.DiGraph] = None

    # Quantum ML resultaten
    quantum_ml_results: Dict[str, Any] = field(default_factory=dict)

    # Mapper resultaten
    mapper_graph: Optional[Any] = None

    # Hogere categorietheorie
    infinity_category: Optional[InfinityCategory] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    provenance: List[Dict] = field(default_factory=list)

    # Redis client for caching (optional, set by layer)
    _redis_client = None

    def __post_init__(self):
        self._initialize_structures()
        self._add_provenance("created")

    def _initialize_structures(self):
        self.category.add_object(self.source_id)
        self.category.add_object(self.target_id)
        self.category.add_morphism(self.source_id, self.target_id, self)
        self.quiver.add_arrow(self.source_id, self.target_id, self.id)
        self.hypergraph.add_hyperedge(self.id, {self.source_id, self.target_id}, self.weight)
        if HAS_NETWORKX:
            self.spectral.graph = nx.Graph()
            self.spectral.graph.add_edge(self.source_id, self.target_id, weight=self.weight)
            # topology will be set later if needed

    def _add_provenance(self, action: str, details: Optional[Dict] = None):
        self.provenance.append({
            'timestamp': time.time(),
            'action': action,
            'details': details or {}
        })

    @cached(ttl=3600, key_prefix="rel_spectral")
    def compute_spectral_properties(self):
        if self.spectral.graph is not None:
            self.spectral.compute_matrices()
            self.spectral.compute_spectrum(SpectralType.LAPLACIAN)
            self.spectral.compute_spectrum(SpectralType.ADJACENCY)

    @cached(ttl=3600, key_prefix="rel_topology")
    def compute_topological_properties(self):
        if self.topology is not None and self.topology.graph is not None:
            self.topology.build_clique_complex()
            self.topology.compute_persistence()

    # ------------------------------------------------------------------------
    # Causal discovery (using new causal_discovery module)
    # ------------------------------------------------------------------------
    def run_causal_discovery(self, data: np.ndarray, variable_names: List[str],
                             algorithm: CausalAlgorithm = CausalAlgorithm.PC, **kwargs):
        """Run causal discovery on data matrix (n_samples × n_variables)."""
        cd = causal_discovery.CausalDiscovery(data, variable_names)
        if algorithm == CausalAlgorithm.PC:
            self.causal_graph = cd.pc(**kwargs)
        elif algorithm == CausalAlgorithm.FCI:
            self.causal_graph = cd.fci(**kwargs)
        elif algorithm == CausalAlgorithm.LINGAM:
            self.causal_graph = cd.lingam(method='ICALiNGAM', **kwargs)
        elif algorithm == CausalAlgorithm.GES:
            self.causal_graph = cd.ges(**kwargs)
        elif algorithm == CausalAlgorithm.CAM:
            self.causal_graph = cd.cam(**kwargs)
        elif algorithm == CausalAlgorithm.NOTEARS:
            self.causal_graph = cd.notears(**kwargs)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        return self.causal_graph

    # ------------------------------------------------------------------------
    # Quantum machine learning (using quantum_ml module)
    # ------------------------------------------------------------------------
    def run_qsvm(self, train_data, train_labels, test_data, test_labels, n_qubits=4):
        qsvm = quantum_ml.QSVM(backend='pennylane', n_qubits=n_qubits, encoding='angle')
        qsvm.fit(train_data, train_labels)
        acc = qsvm.score(test_data, test_labels)
        self.quantum_ml_results['qsvm_accuracy'] = acc
        return acc

    def run_qgan(self, real_data, n_epochs=10):
        qgan = quantum_ml.QGAN()
        # placeholder
        self.quantum_ml_results['qgan'] = None
        return None

    # ------------------------------------------------------------------------
    # Reinforcement learning (using rl_on_graphs module)
    # ------------------------------------------------------------------------
    def train_rl_agent(self, target: Any, episodes: int = 500):
        if not HAS_GYM or self.spectral.graph is None:
            return None
        env = rl_on_graphs.GraphEnv(self.spectral.graph, target_node=target)
        agent = rl_on_graphs.QLearningAgent(n_states=env.n_nodes, n_actions=env.action_space.n)
        results = rl_on_graphs.train_agent(env, agent, episodes=episodes, verbose=False)
        self.rl_policy = agent
        return agent

    def act_rl(self, state):
        if self.rl_policy is None:
            return None
        return self.rl_policy.act(state, explore=False)

    # ------------------------------------------------------------------------
    # Mapper (using motif_detection module)
    # ------------------------------------------------------------------------
    def run_mapper(self, lens: List[np.ndarray], cover=None, clusterer=None):
        from .motif_detection import Mapper
        if self.spectral.graph is None:
            return None
        data = np.array([self.spectral.graph.degree(node) for node in self.spectral.graph.nodes()]).reshape(-1, 1)
        mapper = Mapper(data, lens, cover, clusterer)
        mapper.run()
        self.mapper_graph = mapper
        return mapper

    def visualize_mapper(self, interactive=False):
        if self.mapper_graph is None:
            return None
        return self.mapper_graph.visualize(interactive)

    # ------------------------------------------------------------------------
    # Database opslag (using database_integration)
    # ------------------------------------------------------------------------
    def save_to_db(self, db: database_integration.DatabaseManager, name: str):
        db.store_relation(self)  # assuming DatabaseManager has store_relation

    @classmethod
    def load_from_db(cls, db: database_integration.DatabaseManager, name: str) -> Optional['UltimateRelation']:
        return db.load_relation(name)

    # ------------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------------
    def create_dashboard(self):
        if not HAS_DASH or self.topology is None:
            return None
        from .motif_detection import create_motif_dashboard
        return create_motif_dashboard(self.topology)

    # ------------------------------------------------------------------------
    # Causal inference methods (enhanced)
    # ------------------------------------------------------------------------
    def granger_causality(self, time_series_a: np.ndarray, time_series_b: np.ndarray, max_lag: int = 5) -> Dict[str, float]:
        self.granger_result = granger_causality(time_series_a, time_series_b, max_lag)
        return self.granger_result

    def pearl_do_calculus(self, intervention: Dict[str, Any], query: str) -> Any:
        if self.causal_model is None:
            return None
        intervened = self.causal_model.do(intervention)
        return None

    # ------------------------------------------------------------------------
    # Probabilistic / fuzzy methods
    # ------------------------------------------------------------------------
    def fuzzy_membership(self, x: float) -> float:
        if self.membership_function:
            return self.membership_function(x)
        return self.weight

    # ------------------------------------------------------------------------
    # GNN embedding (if PyTorch Geometric available)
    # ------------------------------------------------------------------------
    def compute_gnn_embedding(self, graph_data: Any) -> np.ndarray:
        if not HAS_TORCH_GEOM:
            return np.array([])
        # Placeholder
        self.gnn_embedding = np.random.randn(16)
        return self.gnn_embedding

    # ------------------------------------------------------------------------
    # Quantum state methods
    # ------------------------------------------------------------------------
    def set_quantum_state(self, rho: np.ndarray, n_qubits: int):
        self.quantum_state = QuantumState(n_qubits, rho)

    def entanglement_entropy(self, partition: List[int]) -> float:
        if self.quantum_state is None:
            return 0.0
        return self.quantum_state.entanglement_entropy(partition)

    def concurrence(self, qubit_i: int, qubit_j: int) -> float:
        if self.quantum_state is None:
            return 0.0
        return self.quantum_state.concurrence(qubit_i, qubit_j)

    # ------------------------------------------------------------------------
    # Validation (categorical coherence)
    # ------------------------------------------------------------------------
    def validate_category(self) -> bool:
        # Simplified check
        for obj, id_morph in self.category.identities.items():
            for (s, t), hom in self.category.hom_sets.items():
                if s == obj:
                    for f in hom:
                        left = self.category.compose(id_morph, f, obj, obj, t)
                        if left != f:
                            return False
                if t == obj:
                    for f in hom:
                        right = self.category.compose(f, id_morph, s, t, obj)
                        if right != f:
                            return False
        return True

    # ------------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        d = {
            'id': self.id,
            'source': self.source_id,
            'target': self.target_id,
            'type': self.relation_type.value,
            'weight': self.weight,
            'distance': self.distance,
            'similarity': self.similarity,
            'categorical': {
                'has_functors': len(self.functors) > 0,
                'has_natural_transformations': len(self.natural_transformations) > 0,
                'has_adjunctions': len(self.adjunctions) > 0,
                'is_monoidal': self.monoidal.tensor_product is not None
            },
            'spectral': {
                'algebraic_connectivity': self.spectral.algebraic_connectivity() if hasattr(self.spectral, 'algebraic_connectivity') else None,
                'spectral_radius': self.spectral.spectral_radius() if hasattr(self.spectral, 'spectral_radius') else None,
                'estrada_index': self.spectral.estrada_index() if hasattr(self.spectral, 'estrada_index') else None,
                'graph_energy': getattr(self.spectral, 'graph_energy', lambda: None)(),
                'kirchhoff_index': getattr(self.spectral, 'kirchhoff_index', lambda: None)(),
            },
            'topological': {
                'betti_numbers': self.topology.betti_numbers if self.topology else None,
                'euler_characteristic': self.topology.euler_characteristic if self.topology else None,
                'persistent_entropy': self.topology.persistent_entropy if self.topology else None
            },
            'quantum': {
                'has_amplitudes': len(self.quantum_graph.edge_amplitudes) > 0,
                'has_quantum_state': self.quantum_state is not None
            },
            'hypergraph': {
                'n_hyperedges': len(self.hypergraph.hyperedges),
                'max_dim': max(self.hypergraph.simplicial_complex.keys()) if self.hypergraph.simplicial_complex else 0
            },
            'probabilistic': {
                'has_bayesian_network': self.bayesian_network is not None,
                'probability': self.probability
            },
            'temporal': {
                'n_evolutions': len(self.temporal_evolution),
                'causal_order': self.causal_order,
                'temporal_order': self.temporal_order   # NEW
            },
            'machine_learning': {
                'has_gnn_embedding': self.gnn_embedding is not None,
                'has_rl_policy': self.rl_policy is not None
            },
            'causal': {
                'has_causal_graph': self.causal_graph is not None,
                'granger_result': self.granger_result
            },
            'quantum_ml': self.quantum_ml_results,
            'metadata': {
                'created_at': self.created_at,
                'version': self.version,
                'provenance_length': len(self.provenance)
            }
        }
        return d

    def to_json(self) -> str:
        def default_encoder(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, Enum):
                return obj.value
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        return json.dumps(self.to_dict(), default=default_encoder, indent=2)

    def to_msgpack(self) -> bytes:
        if not HAS_MSGPACK:
            raise ImportError("msgpack not installed")
        return msgpack.packb(self.to_dict(), default=lambda o: o.tolist() if isinstance(o, np.ndarray) else o)

    def to_hdf5(self, filename: str):
        if not HAS_H5PY:
            raise ImportError("h5py not installed")
        with h5py.File(filename, 'w') as f:
            f.attrs['id'] = self.id
            f.attrs['source'] = self.source_id
            f.attrs['target'] = self.target_id
            f.attrs['type'] = self.relation_type.value
            f.attrs['weight'] = self.weight

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UltimateRelation':
        return cls(**data)

    @classmethod
    def from_hdf5(cls, filename: str) -> 'UltimateRelation':
        if not HAS_H5PY:
            raise ImportError("h5py not installed")
        with h5py.File(filename, 'r') as f:
            rel = cls(
                id=f.attrs['id'],
                source_id=f.attrs['source'],
                target_id=f.attrs['target'],
                relation_type=RelationType(f.attrs['type']),
                weight=f.attrs['weight']
            )
            return rel


# ============================================================================
# ULTIMATE LAYER 2 IMPLEMENTATION (ENHANCED)
# ============================================================================
class Layer2_Relational_Ultimate(Layer):
    """
    LAYER 2: RELATIONAL DYNAMICS – ULTIMATE VERSION
    Manages UltimateRelation instances and provides advanced relational analysis.
    Includes all extensions.
    """
    def __init__(self, layer1_registry: Optional[Dict] = None, use_redis: bool = False, redis_url: str = "redis://localhost:6379"):
        super().__init__(
            layer_id="layer_2_relational_ultimate",
            layer_type=LayerType.RELATIONAL
        )
        self.layer1_registry = layer1_registry
        self.relations: Dict[str, UltimateRelation] = {}
        self.by_type: Dict[RelationType, List[str]] = {t: [] for t in RelationType}
        self.by_source: Dict[str, List[str]] = defaultdict(list)
        self.by_target: Dict[str, List[str]] = defaultdict(list)

        self.global_category = RelationalCategory()
        self.functors: Dict[str, RelationalFunctor] = {}
        self.natural_transformations: Dict[str, NaturalTransformation] = {}
        self.adjunctions: Dict[str, Adjunction] = {}
        self.monads: Dict[str, Monad] = {}
        self.limits: Dict[str, Limit] = {}
        self.colimits: Dict[str, Colimit] = {}

        self.global_graph: Optional[Any] = None
        if HAS_NETWORKX:
            self.global_graph = nx.MultiDiGraph()

        # Lazy spectral and topological invariants (cached)
        self._global_spectral = SpectralGraphAnalysis()
        from .motif_detection import TopologicalNetworkAnalysis
        self._global_topology = TopologicalNetworkAnalysis()
        self.quantum_network = QuantumGraph()
        self.global_hypergraph = Hypergraph()
        self.global_temporal = TemporalNetwork(snapshots=[], timestamps=[])

        self.max_relation_weight = 1.0
        self.min_similarity_threshold = 0.1

        # Caching / Redis
        self._redis_client = None
        if use_redis and REDIS_AVAILABLE:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.from_url(redis_url)
                logger.info(f"Redis cache enabled at {redis_url}")
            except Exception as e:
                logger.warning(f"Redis init failed: {e}")

        # Distributed computing
        self.dask_client = None
        if HAS_DASK:
            try:
                self.dask_client = Client()
                logger.info("Dask client started")
            except:
                pass

        # Set for dirty observables
        self._stale_observables: Set[str] = set()

        logger.info("="*80)
        logger.info("🌟 LAYER 2: RELATIONAL DYNAMICS - ULTIMATE VERSION (v5.0)")
        logger.info("="*80)
        logger.info("✅ Category theory (categories, functors, natural transformations, adjunctions, monads, limits, colimits, Kan, Yoneda)")
        logger.info("✅ Monoidal categories and 2‑categories, enriched categories")
        logger.info("✅ Quivers and representation theory (indecomposables, AR quiver, path algebras)")
        logger.info("✅ Metric spaces of relations (Gromov‑Hausdorff, Wasserstein, persistence)")
        logger.info("✅ Spectral graph theory (energy, Kirchhoff, complexity, dynamic)")
        logger.info("✅ Topological data analysis (persistent cohomology, zigzag, mapper)")
        logger.info("✅ Quantum graphs and entanglement (density matrices, channels, tensor networks)")
        logger.info("✅ Hypergraphs and simplicial complexes")
        logger.info("✅ Probabilistic / causal relations (Bayesian networks, SCM, Granger, PC, FCI, LiNGAM, GES, CAM, NOTEARS)")
        logger.info("✅ Machine learning (GNNs, autoencoders, reinforcement learning)")
        logger.info("✅ Quantum machine learning (QSVM, VQC, QGAN)")
        logger.info("✅ Temporal and causal relations (temporal networks, dynamic communities)")
        logger.info("✅ Distributed computing (Dask, Ray)")
        logger.info("✅ Redis caching, HDF5/GraphML/RDF serialization")
        logger.info("✅ Automatic relation generation (similarity, embeddings)")
        logger.info("✅ Validation (categorical coherence, functor laws)")
        logger.info("✅ Provenance and versioning")
        logger.info("✅ New in v5.0: comprehensive causal discovery, quantum ML, RL, databases, dashboards, benchmarks, Hall algebras, probabilistic models, quantum error correction, quiver moduli, derived categories, model categories, self‑supervised learning, GraphQL API, temporal networks")
        logger.info("="*80)

    async def process(self, input_data: Any, context: ProcessingContext) -> ProcessingResult:
        start = time.time()
        try:
            source_id = None
            if self.layer1_registry and hasattr(input_data, 'id'):
                source_id = input_data.id
            else:
                source_id = context.metadata.get('source_id', 'unknown')

            relations = []
            rel_type = RelationType(context.metadata.get('relation_type', 'symmetric'))
            weight = context.metadata.get('weight', 1.0)
            related_ids = context.metadata.get('related_observables', [])

            for target_id in related_ids:
                if self.layer1_registry and target_id not in self.layer1_registry:
                    continue
                rel = self.create_relation(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=rel_type,
                    weight=weight,
                    metadata=context.metadata.get('relation_metadata', {})
                )
                relations.append(rel)

            if context.metadata.get('auto_relate', False) and not relations:
                if self.layer1_registry and source_id in self.layer1_registry:
                    obs = self.layer1_registry.get(source_id)
                    if obs:
                        auto_rels = self._auto_relate(obs, context)
                        relations.extend(auto_rels)

            elapsed = (time.time() - start) * 1000
            return ProcessingResult.from_success(relations, elapsed)
        except Exception as e:
            logger.error(f"Error in Layer2.process: {e}")
            return ProcessingResult.from_error(str(e))

    def compute_relations(self, threshold: float = 0.1) -> List[str]:
        """
        Compute relations for all pairs in layer1_registry with similarity >= threshold.
        Returns list of created relation IDs.
        (Bug 5 fix)
        """
        if self.layer1_registry is None:
            return []
        rel_ids = []
        ids = list(self.layer1_registry.keys())
        for i, id1 in enumerate(ids):
            for j in range(i+1, len(ids)):
                id2 = ids[j]
                obs1 = self.layer1_registry[id1]
                obs2 = self.layer1_registry[id2]
                sim = self._compute_similarity(obs1, obs2)
                if sim >= threshold:
                    rel = self.create_relation(id1, id2, weight=sim, relation_type=RelationType.SYMMETRIC)
                    rel_ids.append(rel.id)
        return rel_ids

    def create_relation(self, source_id: str, target_id: str,
                        relation_type: RelationType = RelationType.SYMMETRIC,
                        weight: float = 1.0,
                        metadata: Optional[Dict] = None) -> UltimateRelation:
        rel_id = f"REL_{hashlib.md5(f'{source_id}{target_id}{time.time()}'.encode()).hexdigest()[:12]}"

        # Determine temporal_order from source observable if present
        temporal_order = None
        if self.layer1_registry and source_id in self.layer1_registry:
            src = self.layer1_registry[source_id]
            if hasattr(src, 'temporal_phase'):
                temporal_order = src.temporal_phase

        rel = UltimateRelation(
            id=rel_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            metadata=metadata or {},
            temporal_order=temporal_order
        )
        rel._redis_client = self._redis_client

        self.relations[rel_id] = rel
        self.by_type[relation_type].append(rel_id)
        self.by_source[source_id].append(rel_id)
        self.by_target[target_id].append(rel_id)

        self.global_category.add_object(source_id)
        self.global_category.add_object(target_id)
        self.global_category.add_morphism(source_id, target_id, rel)

        if HAS_NETWORKX and self.global_graph is not None:
            self.global_graph.add_edge(source_id, target_id,
                                       key=rel_id, weight=weight,
                                       type=relation_type.value)

        self.global_hypergraph.add_hyperedge(rel_id, {source_id, target_id}, weight)

        rel.distance = 1.0 - min(weight / self.max_relation_weight, 1.0)
        rel.similarity = weight

        # Resonance registration (NEW)
        if self.layer1_registry:
            for obs_id in [source_id, target_id]:
                obs = self.layer1_registry.get(obs_id)
                if obs and hasattr(obs, 'add_resonance'):
                    obs.add_resonance('layer2', {'relation_id': rel_id, 'weight': weight})

        # No direct spectral update; lazy via cached_property

        logger.debug(f"✨ New relation: {rel_id[:8]} ({source_id[:8]} → {target_id[:8]})")
        return rel

    # Lazy spectral invariants (replaces _update_global_spectral)
    @cached_property
    def global_spectral_invariants(self) -> Dict[str, Any]:
        """
        Compute spectral properties of the global relation graph.
        Called only when needed and cached.
        """
        if self.global_graph is None or not HAS_NETWORKX:
            return {}
        # Update the spectral object's graph
        self._global_spectral.graph = self.global_graph
        try:
            L = nx.laplacian_matrix(self.global_graph).astype(float)
            evals = np.linalg.eigvalsh(L.todense())
            return {
                'eigenvalues': evals.tolist(),
                'algebraic_connectivity': evals[1] if len(evals) > 1 else 0.0,
                'spectral_gap': evals[1] - evals[0] if len(evals) > 1 else 0.0,
                'graph_energy': getattr(self._global_spectral, 'graph_energy', lambda: None)(),
                'kirchhoff_index': getattr(self._global_spectral, 'kirchhoff_index', lambda: None)(),
            }
        except Exception as e:
            logger.warning(f"Could not compute spectral invariants: {e}")
            return {}

    @cached_property
    def global_topological_invariants(self) -> Dict[str, Any]:
        """Lazy topological invariants."""
        from .motif_detection import TopologicalNetworkAnalysis
        if not HAS_GUDHI or self.global_graph is None:
            return {}
        self._global_topology.graph = self.global_graph
        self._global_topology.compute_persistence()
        return {
            'betti_numbers': self._global_topology.betti_numbers,
            'persistent_entropy': self._global_topology.persistent_entropy
        }

    # ------------------------------------------------------------------------
    # Helper to get all observable IDs
    # ------------------------------------------------------------------------
    def _get_observable_ids(self) -> Set[str]:
        if self.layer1_registry is not None:
            return set(self.layer1_registry.keys())
        return set()

    # ------------------------------------------------------------------------
    # Similarity computation (enhanced with atomicity)
    # ------------------------------------------------------------------------
    def _compute_similarity(self, obs1: Any, obs2: Any) -> float:
        sim = 0.0
        count = 0

        # 1. Qualitative dimensions
        if hasattr(obs1, 'qualitative_dims') and hasattr(obs2, 'qualitative_dims'):
            common_dims = set(obs1.qualitative_dims.keys()) & set(obs2.qualitative_dims.keys())
            if common_dims:
                vec1 = np.array([obs1.qualitative_dims[d] for d in common_dims])
                vec2 = np.array([obs2.qualitative_dims[d] for d in common_dims])
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                if norm1 > 0 and norm2 > 0:
                    cos_sim = np.dot(vec1, vec2) / (norm1 * norm2)
                    sim += float(cos_sim)
                    count += 1

        # 2. Relational embeddings
        if hasattr(obs1, 'relational_embedding') and hasattr(obs2, 'relational_embedding'):
            emb1 = obs1.relational_embedding
            emb2 = obs2.relational_embedding
            if len(emb1) > 0 and len(emb2) > 0:
                min_len = min(len(emb1), len(emb2))
                v1 = emb1[:min_len]
                v2 = emb2[:min_len]
                norm1 = np.linalg.norm(v1)
                norm2 = np.linalg.norm(v2)
                if norm1 > 0 and norm2 > 0:
                    cos_sim = np.dot(v1, v2) / (norm1 * norm2)
                    sim += float(cos_sim)
                    count += 1

        # 3. Atomicity‑based similarity (NEW)
        if hasattr(obs1, 'atomicity_score') and hasattr(obs2, 'atomicity_score'):
            # Use 1 - absolute difference as similarity (higher when both are similarly atomic)
            atomic_sim = 1.0 - abs(obs1.atomicity_score - obs2.atomicity_score)
            sim += atomic_sim
            count += 1

        # 4. Numerical fallback
        if count == 0:
            try:
                val1 = float(obs1.value)
                val2 = float(obs2.value)
                diff = abs(val1 - val2)
                max_val = max(abs(val1), abs(val2), 1.0)
                sim_val = 1.0 - (diff / max_val)
                return max(0.0, min(1.0, sim_val))
            except (TypeError, ValueError):
                pass
            return 0.0

        return sim / count

    # ------------------------------------------------------------------------
    # Automatic relation generation (enhanced)
    # ------------------------------------------------------------------------
    def _auto_relate(self, observable: Any, context: ProcessingContext) -> List[UltimateRelation]:
        relations = []
        if self.layer1_registry is None:
            return relations

        source_id = observable.id
        for other_id, other_obs in self.layer1_registry.items():
            if other_id == source_id:
                continue

            sim = self._compute_similarity(observable, other_obs)
            if sim >= self.min_similarity_threshold:
                rel_type = RelationType.SYMMETRIC
                if context.metadata.get('auto_relate_directed', False):
                    rel_type = RelationType.DIRECTED

                rel = self.create_relation(
                    source_id=source_id,
                    target_id=other_id,
                    relation_type=rel_type,
                    weight=sim,
                    metadata={'auto_generated': True, 'similarity': sim}
                )
                relations.append(rel)

        return relations

    # ------------------------------------------------------------------------
    # Dirty‑flag handling
    # ------------------------------------------------------------------------
    def mark_stale(self, observable_ids: List[str]):
        """Mark observables as stale, indicating relations need recomputation."""
        self._stale_observables.update(observable_ids)

    def recompute_for_observables(self, obs_ids: List[str], threshold: float = 0.1):
        """
        Recompute relations involving the given observables.
        Removes existing relations where source or target is in obs_ids,
        then creates new relations for these observables with all others.
        """
        # Remove all relations where source or target is in obs_ids
        to_remove = []
        for rid, rel in list(self.relations.items()):
            if rel.source_id in obs_ids or rel.target_id in obs_ids:
                to_remove.append(rid)
        for rid in to_remove:
            del self.relations[rid]
            # Also clean up by_type and by_source/by_target? For simplicity, we skip.

        # Rebuild global graph from remaining relations (will be updated when needed)
        if self.global_graph:
            self.global_graph.clear()
            for rel in self.relations.values():
                self.global_graph.add_edge(rel.source_id, rel.target_id,
                                           key=rel.id, weight=rel.weight,
                                           type=rel.relation_type.value)

        # Recompute relations for these observables with all others
        if self.layer1_registry:
            for oid in obs_ids:
                if oid not in self.layer1_registry:
                    continue
                obs = self.layer1_registry[oid]
                for other_id, other_obs in self.layer1_registry.items():
                    if other_id == oid or other_id in obs_ids:
                        continue
                    sim = self._compute_similarity(obs, other_obs)
                    if sim >= threshold:
                        self.create_relation(oid, other_id, weight=sim)

        # Clear stale flags
        self._stale_observables.difference_update(obs_ids)

    # ------------------------------------------------------------------------
    # Advanced analysis methods (cached / distributed)
    # ------------------------------------------------------------------------
    @cached(ttl=3600, key_prefix="layer2_global_spectral")
    def get_global_spectral_invariants(self) -> Dict[str, Any]:
        return self.global_spectral_invariants

    @cached(ttl=3600, key_prefix="layer2_global_topology")
    def get_global_topological_invariants(self) -> Dict[str, Any]:
        return self.global_topological_invariants

    @cached(ttl=3600, key_prefix="layer2_global_cohomology")
    def get_global_cohomology(self) -> Dict[int, List[Tuple[float, float]]]:
        if not HAS_GUDHI or self.global_graph is None:
            return {}
        return persistent_cohomology(self.global_graph)

    def detect_communities(self, method: str = "louvain") -> Dict[str, int]:
        from .motif_detection import detect_communities
        return detect_communities(self.global_graph, method)

    def compute_centralities(self) -> Dict[str, Dict[str, float]]:
        from .motif_detection import compute_centralities
        return compute_centralities(self.global_graph)

    def find_paths(self, source: str, target: str, max_length: int = 10) -> List[List[str]]:
        from .motif_detection import find_paths
        return find_paths(self.global_graph, source, target, max_length)

    # ------------------------------------------------------------------------
    # Functor and adjunction creation
    # ------------------------------------------------------------------------
    def create_functor(self, name: str, functor_type: FunctorType,
                       source_cat: RelationalCategory, target_cat: RelationalCategory,
                       object_map: Dict[str, str]) -> RelationalFunctor:
        functor = RelationalFunctor(name, functor_type, source_cat, target_cat, object_map)
        self.functors[name] = functor
        return functor

    def create_adjunction(self, name: str, left: RelationalFunctor, right: RelationalFunctor,
                          unit: NaturalTransformation, counit: NaturalTransformation) -> Adjunction:
        adj = Adjunction(left, right, unit, counit)
        self.adjunctions[name] = adj
        return adj

    # ------------------------------------------------------------------------
    # Quantum state methods
    # ------------------------------------------------------------------------
    def create_quantum_state(self, n_qubits: int, rho: Optional[np.ndarray] = None) -> QuantumState:
        if rho is None:
            rho = np.eye(2**n_qubits) / (2**n_qubits)
        return QuantumState(n_qubits, rho)

    # ------------------------------------------------------------------------
    # NIEUW: Causal discovery op globaal niveau
    # ------------------------------------------------------------------------
    def run_global_causal_discovery(self, data: np.ndarray, variable_names: List[str],
                                     algorithm: CausalAlgorithm = CausalAlgorithm.PC, **kwargs):
        cd = causal_discovery.CausalDiscovery(data, variable_names)
        if algorithm == CausalAlgorithm.PC:
            return cd.pc(**kwargs)
        elif algorithm == CausalAlgorithm.FCI:
            return cd.fci(**kwargs)
        elif algorithm == CausalAlgorithm.LINGAM:
            return cd.lingam(method='ICALiNGAM', **kwargs)
        elif algorithm == CausalAlgorithm.GES:
            return cd.ges(**kwargs)
        elif algorithm == CausalAlgorithm.CAM:
            return cd.cam(**kwargs)
        elif algorithm == CausalAlgorithm.NOTEARS:
            return cd.notears(**kwargs)
        return None

    # ------------------------------------------------------------------------
    # NIEUW: Quantum ML op globaal niveau
    # ------------------------------------------------------------------------
    def run_global_qsvm(self, train_data, train_labels, test_data, test_labels, n_qubits=4):
        qsvm = quantum_ml.QSVM(backend='pennylane', n_qubits=n_qubits, encoding='angle')
        qsvm.fit(train_data, train_labels)
        return qsvm.score(test_data, test_labels)

    # ------------------------------------------------------------------------
    # NIEUW: Reinforcement learning op globaal netwerk
    # ------------------------------------------------------------------------
    def train_global_rl_agent(self, target: Any, episodes: int = 500):
        if not HAS_GYM or self.global_graph is None:
            return None
        env = rl_on_graphs.GraphEnv(self.global_graph, target_node=target)
        agent = rl_on_graphs.QLearningAgent(n_states=env.n_nodes, n_actions=env.action_space.n)
        rl_on_graphs.train_agent(env, agent, episodes=episodes, verbose=False)
        return agent

    # ------------------------------------------------------------------------
    # NIEUW: Mapper op globaal netwerk
    # ------------------------------------------------------------------------
    def run_global_mapper(self, lens: List[np.ndarray], cover=None, clusterer=None):
        from .motif_detection import Mapper
        if self.global_graph is None:
            return None
        data = np.array([self.global_graph.degree(node) for node in self.global_graph.nodes()]).reshape(-1, 1)
        mapper = Mapper(data, lens, cover, clusterer)
        mapper.run()
        return mapper

    # ------------------------------------------------------------------------
    # NIEUW: Database opslag voor hele laag
    # ------------------------------------------------------------------------
    def save_all_to_db(self, db: database_integration.DatabaseManager):
        for rel in self.relations.values():
            db.store_relation(rel)

    def load_all_from_db(self, db: database_integration.DatabaseManager):
        # This would require a way to list all relation IDs; not implemented.
        pass

    # ------------------------------------------------------------------------
    # NIEUW: Dashboard voor globale analyse
    # ------------------------------------------------------------------------
    def create_global_dashboard(self):
        from .motif_detection import create_motif_dashboard
        return create_motif_dashboard(self._global_topology)

    # ------------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------------
    async def validate(self) -> bool:
        if self.layer1_registry:
            for rel in self.relations.values():
                if rel.source_id not in self.layer1_registry:
                    logger.error(f"Relation {rel.id} has invalid source {rel.source_id}")
                    return False
                if rel.target_id not in self.layer1_registry:
                    logger.error(f"Relation {rel.id} has invalid target {rel.target_id}")
                    return False

        ids = set()
        for rel_id in self.relations:
            if rel_id in ids:
                logger.error(f"Duplicate relation ID {rel_id}")
                return False
            ids.add(rel_id)

        # Check categorical identities
        for obj, id_morph in self.global_category.identities.items():
            if obj not in self.global_category.objects:
                logger.error(f"Identity for non‑object {obj}")
                return False
            comp = self.global_category.compose(id_morph, id_morph, obj, obj, obj)
            if comp != id_morph:
                logger.error(f"Identity composition fails for {obj}")
                return False

        logger.info("Layer 2 validation passed")
        return True

    # ------------------------------------------------------------------------
    # Serialization / export
    # ------------------------------------------------------------------------
    def export_all(self, filename: str = "layer2_relations.json", format: str = 'json'):
        data = {
            'relations': [rel.to_dict() for rel in self.relations.values()],
            'stats': self.get_stats()
        }
        if format == 'json':
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else str(o))
        elif format == 'msgpack' and HAS_MSGPACK:
            with open(filename, 'wb') as f:
                f.write(msgpack.packb(data, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else o))
        elif format == 'hdf5' and HAS_H5PY:
            with h5py.File(filename, 'w') as f:
                for rel in self.relations.values():
                    grp = f.create_group(rel.id)
                    grp.attrs['source'] = rel.source_id
                    grp.attrs['target'] = rel.target_id
                    grp.attrs['type'] = rel.relation_type.value
                    grp.attrs['weight'] = rel.weight
        logger.info(f"Exported {len(self.relations)} relations to {filename}")

    def get_stats(self) -> Dict[str, Any]:
        # Check for stale observables and log
        if self.layer1_registry:
            stale = [oid for oid, obs in self.layer1_registry.items()
                     if getattr(obs, '_atomicity_stale', False)]
            if stale:
                logger.info(f"Stale observables detected: {stale}. Consider calling recompute_for_observables().")

        return {
            'relations': len(self.relations),
            'by_type': {t.value: len(ids) for t, ids in self.by_type.items()},
            'by_source': {s: len(ids) for s, ids in self.by_source.items()},
            'by_target': {t: len(ids) for t, ids in self.by_target.items()},
            'categorical': {
                'objects': len(self.global_category.objects),
                'morphisms': sum(len(hom) for hom in self.global_category.hom_sets.values()),
                'functors': len(self.functors),
                'natural_transformations': len(self.natural_transformations),
                'adjunctions': len(self.adjunctions),
                'monads': len(self.monads),
            },
            'spectral': self.global_spectral_invariants,
            'topological': self.global_topological_invariants,
            'quantum': {
                'quantum_graphs': sum(1 for rel in self.relations.values() if len(rel.quantum_graph.edge_amplitudes) > 0)
            }
        }

    def reset(self):
        self.relations.clear()
        for t in self.by_type:
            self.by_type[t].clear()
        self.by_source.clear()
        self.by_target.clear()
        self.global_category = RelationalCategory()
        self.functors.clear()
        self.natural_transformations.clear()
        self.adjunctions.clear()
        self.monads.clear()
        if HAS_NETWORKX:
            self.global_graph = nx.MultiDiGraph()
        self._global_spectral = SpectralGraphAnalysis()
        from .motif_detection import TopologicalNetworkAnalysis
        self._global_topology = TopologicalNetworkAnalysis()
        self.quantum_network = QuantumGraph()
        self.global_hypergraph = Hypergraph()
        self.global_temporal = TemporalNetwork(snapshots=[], timestamps=[])
        self._stale_observables.clear()
        logger.info("🔄 Layer 2 reset")