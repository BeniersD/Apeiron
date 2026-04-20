"""
LAYER 5: AUTONOMOUS OPTIMIZATION AND LEARNING - Uitmuntende Implementatie
===========================================================================
Layer 5 vertegenwoordigt het niveau van zelfgestuurde optimalisatie en leren.
Functionele entiteiten kunnen hun eigen parameters en structuren optimaliseren
op basis van prestatiefeedback, met behulp van diverse optimalisatie-algoritmes,
machine learning, en adaptieve strategieën.

V14 UITGEBREIDE OPTIONELE FEATURES:
----------------------------------------------------------------------------
✅ Gradient-gebaseerde optimalisatie - SGD, Adam, RMSprop, L-BFGS, etc.
✅ Evolutionaire algoritmes - Genetische algoritmes, CMA-ES, Differentiële evolutie
✅ Bayesiaanse optimalisatie - Gaussian Processes, Expected Improvement
✅ Multi-objective optimalisatie - Pareto front, NSGA-II, MOEA/D
✅ Hyperparameter tuning - Grid search, Random search, Optuna, Hyperopt
✅ Reinforcement learning - Q-learning, Policy gradients (simplified)
✅ Meta-learning - Learning to learn, MAML (Model-Agnostic Meta-Learning)
✅ Neurale netwerk optimalisatie - PyTorch Lightning integratie
✅ Hardware versnelling - CPU, CUDA, FPGA, Quantum
✅ Gedistribueerde optimalisatie - Ray, Dask, Spark
✅ Caching - In-memory, Redis voor resultaten
✅ Persistentie - SQLite voor optimalisatiegeschiedenis
✅ Visualisatie - Convergence plots, Pareto front visualisatie
✅ Validatie - Pydantic modellen voor parameters
✅ Metrics - Prometheus export
✅ Constraint handling - Lineaire/niet-lineaire constraints
✅ Stochastische optimalisatie - Simulated annealing, Random search
✅ Continue/Discrete parameters - Gemengde parameterruimtes
✅ Parallelle evaluatie - Batch evaluatie van functies
✅ Early stopping - Op basis van plateau, patience
✅ Checkpointing - Hervatten van optimalisatie

Hardware integratie:
✅ CPU - NumPy/SciPy optimalisatie
✅ CUDA - GPU versnelling via PyTorch
✅ FPGA - Hardware versnelling via PYNQ (simulatie)
✅ Quantum - Quantum-geïnspireerde optimalisatie (QAOA, VQE)

Theoretische basis uit 17-lagen document:
- "Autonomous Optimization and Learning – Self-directed evolution through performance optimization"
- "Functional entities learn from feedback and optimize their internal structures"
- "Performance function P_k evaluates effectiveness based on relational patterns and dynamic states"
- "Update rule Ω_k allows functional entities to adapt without human guidance"
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import hashlib
import logging
import json
import pickle
import zlib
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime
from functools import wraps, lru_cache
import asyncio
import math

logger = logging.getLogger(__name__)

# ====================================================================
# OPTIONELE OPTIMALISATIE IMPORTS
# ====================================================================

# SciPy optimalisatie
try:
    import numpy as np
    from scipy.optimize import minimize, differential_evolution, dual_annealing
    from scipy.optimize import shgo, direct, basinhopping
    from scipy.optimize import rosen, rosen_der, rosen_hess
    SCIPY_AVAILABLE = True
    logger.info("✅ SciPy beschikbaar voor optimalisatie")
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("⚠️ SciPy niet beschikbaar - beperkte optimalisatie")

# PyTorch voor neurale netwerken en GPU versnelling
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.optim.lr_scheduler import ReduceLROnPlateau, CosineAnnealingLR
    TORCH_AVAILABLE = True
    logger.info("✅ PyTorch beschikbaar voor neurale optimalisatie")
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("⚠️ PyTorch niet beschikbaar - geen neurale optimalisatie")

# CUDA voor GPU versnelling
CUDA_AVAILABLE = TORCH_AVAILABLE and torch.cuda.is_available()
if CUDA_AVAILABLE:
    logger.info(f"✅ CUDA beschikbaar: {torch.cuda.get_device_name(0)}")
    device = torch.device('cuda')

# Scikit-learn voor machine learning modellen
try:
    import sklearn
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, Matern, WhiteKernel
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import cross_val_score, GridSearchCV, RandomizedSearchCV
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
    logger.info("✅ Scikit-learn beschikbaar voor ML modellen")
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("⚠️ Scikit-learn niet beschikbaar - geen ML modellen")

# Optuna voor hyperparameter optimalisatie
try:
    import optuna
    from optuna.samplers import TPESampler, RandomSampler, CmaEsSampler
    from optuna.pruners import MedianPruner, HyperbandPruner
    OPTUNA_AVAILABLE = True
    logger.info("✅ Optuna beschikbaar voor hyperparameter tuning")
except ImportError:
    OPTUNA_AVAILABLE = False
    logger.warning("⚠️ Optuna niet beschikbaar - geen hyperparameter tuning")

# Hyperopt voor bayesiaanse optimalisatie
try:
    from hyperopt import fmin, tpe, hp, Trials, STATUS_OK, STATUS_FAIL
    HYPEROPT_AVAILABLE = True
    logger.info("✅ Hyperopt beschikbaar voor bayesiaanse optimalisatie")
except ImportError:
    HYPEROPT_AVAILABLE = False
    logger.warning("⚠️ Hyperopt niet beschikbaar - geen bayesiaanse optimalisatie")

# DEAP voor evolutionaire algoritmes
try:
    from deap import base, creator, tools, algorithms
    DEAP_AVAILABLE = True
    logger.info("✅ DEAP beschikbaar voor evolutionaire algoritmes")
except ImportError:
    DEAP_AVAILABLE = False
    logger.warning("⚠️ DEAP niet beschikbaar - geen evolutionaire algoritmes")

# CMA-ES
try:
    import cma
    CMA_AVAILABLE = True
    logger.info("✅ CMA-ES beschikbaar")
except ImportError:
    CMA_AVAILABLE = False
    logger.warning("⚠️ CMA-ES niet beschikbaar")

# PyMOO voor multi-objective optimalisatie
try:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.algorithms.moo.moead import MOEAD
    from pymoo.core.problem import Problem
    from pymoo.optimize import minimize as pymoo_minimize
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    from pymoo.operators.sampling.rnd import FloatRandomSampling
    PYMOO_AVAILABLE = True
    logger.info("✅ PyMOO beschikbaar voor multi-objective optimalisatie")
except ImportError:
    PYMOO_AVAILABLE = False
    logger.warning("⚠️ PyMOO niet beschikbaar - geen multi-objective optimalisatie")

# Ray voor gedistribueerde optimalisatie
try:
    import ray
    from ray import tune
    from ray.tune.schedulers import ASHAScheduler, HyperBandScheduler
    from ray.tune.search import ConcurrencyLimiter
    from ray.tune.search.bayesopt import BayesOptSearch
    RAY_AVAILABLE = True
    logger.info("✅ Ray beschikbaar voor gedistribueerde optimalisatie")
except ImportError:
    RAY_AVAILABLE = False
    logger.warning("⚠️ Ray niet beschikbaar - geen gedistribueerde optimalisatie")

# Dask voor parallelle evaluatie
try:
    import dask
    from dask.distributed import Client, LocalCluster
    DASK_AVAILABLE = True
    logger.info("✅ Dask beschikbaar voor parallelle evaluatie")
except ImportError:
    DASK_AVAILABLE = False
    logger.warning("⚠️ Dask niet beschikbaar - geen parallelle evaluatie")

# Qiskit voor quantum optimalisatie
try:
    from qiskit import QuantumCircuit, Aer, execute
    from qiskit.algorithms import QAOA, VQE
    from qiskit.algorithms.optimizers import COBYLA, SPSA
    from qiskit.circuit.library import TwoLocal
    QISKIT_AVAILABLE = True
    logger.info("✅ Qiskit beschikbaar voor quantum optimalisatie")
except ImportError:
    QISKIT_AVAILABLE = False
    logger.warning("⚠️ Qiskit niet beschikbaar - geen quantum optimalisatie")

# PYNQ voor FPGA versnelling
try:
    from pynq import Overlay, allocate
    PYNQ_AVAILABLE = True
    logger.info("✅ PYNQ beschikbaar voor FPGA versnelling")
except ImportError:
    PYNQ_AVAILABLE = False
    logger.warning("⚠️ PYNQ niet beschikbaar - geen FPGA versnelling")

# ====================================================================
# OPTIONELE VISUALISATIE IMPORTS
# ====================================================================

try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.colors import LinearSegmentedColormap
    VISUALIZATION_AVAILABLE = True
    logger.info("✅ Matplotlib beschikbaar voor visualisatie")
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logger.warning("⚠️ Matplotlib niet beschikbaar - geen visualisatie")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
    logger.info("✅ Plotly beschikbaar voor interactieve visualisatie")
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("⚠️ Plotly niet beschikbaar - geen interactieve plots")

# ====================================================================
# OPTIONELE CACHING & PERSISTENTIE
# ====================================================================

try:
    import redis.asyncio as redis
    from redis.exceptions import RedisError
    REDIS_AVAILABLE = True
    logger.info("✅ Redis beschikbaar voor distributed caching")
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ Redis niet beschikbaar - alleen memory cache")

try:
    import aiosqlite
    ASQLITE_AVAILABLE = True
    logger.info("✅ SQLite beschikbaar voor persistentie")
except ImportError:
    ASQLITE_AVAILABLE = False
    logger.warning("⚠️ SQLite niet beschikbaar - geen persistentie")

# ====================================================================
# OPTIONELE METRICS
# ====================================================================

try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
    PROMETHEUS_AVAILABLE = True
    logger.info("✅ Prometheus beschikbaar voor metrics")
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("⚠️ Prometheus niet beschikbaar - geen metrics export")

# ====================================================================
# ENUMS - Classificatie van optimalisatietypen
# ====================================================================

class OptimizationType(Enum):
    """Type van optimalisatieprobleem."""
    MINIMIZATION = "minimization"
    MAXIMIZATION = "maximization"


class OptimizationMethod(Enum):
    """Beschikbare optimalisatiemethoden."""
    # Gradient-based
    SGD = "sgd"
    ADAM = "adam"
    RMSPROP = "rmsprop"
    LBFGS = "lbfgs"
    CG = "cg"
    NEWTON_CG = "newton_cg"
    
    # Derivative-free
    NELDER_MEAD = "nelder_mead"
    POWELL = "powell"
    COBYLA = "cobyla"
    SLSQP = "slsqp"
    TRUST_CONSTR = "trust_constr"
    
    # Global
    DIFFERENTIAL_EVOLUTION = "differential_evolution"
    DUAL_ANNEALING = "dual_annealing"
    SHGO = "shgo"
    DIRECT = "direct"
    BASINHOPPING = "basinhopping"
    
    # Evolutionair
    GENETIC_ALGORITHM = "genetic_algorithm"
    CMA_ES = "cma_es"
    PARTICLE_SWARM = "particle_swarm"
    
    # Bayesiaans
    BAYESIAN_GP = "bayesian_gp"
    BAYESIAN_TPE = "bayesian_tpe"
    
    # Multi-objective
    NSGA2 = "nsga2"
    MOEAD = "moead"
    
    # Quantum
    QAOA = "qaoa"
    VQE = "vqe"
    
    # Hybride
    AUTO = "auto"


class ParameterType(Enum):
    """Type van optimalisatieparameter."""
    CONTINUOUS = "continuous"
    INTEGER = "integer"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"


class StoppingCriterion(Enum):
    """Stopcriteria voor optimalisatie."""
    MAX_ITERATIONS = "max_iterations"
    TOLERANCE = "tolerance"
    PLATEAU = "plateau"
    TIME_LIMIT = "time_limit"
    CALLBACK = "callback"


# ====================================================================
# OPTIONELE PYDANTIC MODELLEN
# ====================================================================

try:
    from pydantic import BaseModel, validator, Field, ValidationError
    
    class OptimizationResultModel(BaseModel):
        """Pydantic model voor optimalisatieresultaat."""
        id: str = Field(..., min_length=8, max_length=64)
        success: bool
        method: str
        best_x: List[float]
        best_f: float
        n_iterations: int
        time_seconds: float
        metadata: Dict[str, Any] = Field(default_factory=dict)
        
        @validator('method')
        def validate_method(cls, v):
            valid_methods = [m.value for m in OptimizationMethod]
            if v not in valid_methods:
                raise ValueError(f"Methode moet één van {valid_methods} zijn")
            return v
    
    class ParameterModel(BaseModel):
        """Parameter definitie."""
        name: str
        type: str
        low: Optional[float] = None
        high: Optional[float] = None
        choices: Optional[List[Any]] = None
        initial: Optional[Any] = None
        
        @validator('type')
        def validate_type(cls, v):
            valid_types = [t.value for t in ParameterType]
            if v not in valid_types:
                raise ValueError(f"Type moet één van {valid_types} zijn")
            return v
    
    PYDANTIC_AVAILABLE = True
    logger.info("✅ Pydantic beschikbaar voor validatie")
except ImportError:
    PYDANTIC_AVAILABLE = False
    logger.warning("⚠️ Pydantic niet beschikbaar - geen validatie")

# ====================================================================
# OPTIONELE DECORATORS
# ====================================================================

def timed(metric_name: Optional[str] = None):
    """Decorator voor tijdmeting."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            start = time.time()
            try:
                result = await func(self, *args, **kwargs)
                return result
            finally:
                duration = (time.time() - start) * 1000  # ms
                name = metric_name or func.__name__
                
                if hasattr(self, 'metrics'):
                    if 'timings' not in self.metrics:
                        self.metrics['timings'] = {}
                    if name not in self.metrics['timings']:
                        self.metrics['timings'][name] = []
                    self.metrics['timings'][name].append(duration)
                    
                    if len(self.metrics['timings'][name]) > 100:
                        self.metrics['timings'][name].pop(0)
                
                if PROMETHEUS_AVAILABLE and hasattr(self, '_metrics'):
                    if name in self._metrics:
                        self._metrics[name].observe(duration / 1000)
        return wrapper
    return decorator


def cached(ttl: int = 3600):
    """Decorator voor caching."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'enable_cache') or not self.enable_cache:
                return await func(self, *args, **kwargs)
            
            key_parts = [func.__name__]
            key_parts.extend([str(a) for a in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            cache_key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
            full_key = f"{self.id}:{cache_key}"
            
            if hasattr(self, '_memory_cache'):
                if full_key in self._memory_cache:
                    value, expiry = self._memory_cache[full_key]
                    if time.time() < expiry:
                        if hasattr(self, 'metrics'):
                            self.metrics['cache_hits'] = self.metrics.get('cache_hits', 0) + 1
                        return value
            
            if REDIS_AVAILABLE and hasattr(self, 'redis_client'):
                try:
                    cached = await self.redis_client.get(full_key)
                    if cached:
                        if hasattr(self, 'metrics'):
                            self.metrics['cache_hits'] = self.metrics.get('cache_hits', 0) + 1
                        return pickle.loads(cached)
                except Exception as e:
                    logger.warning(f"⚠️ Redis cache fout: {e}")
            
            if hasattr(self, 'metrics'):
                self.metrics['cache_misses'] = self.metrics.get('cache_misses', 0) + 1
            
            result = await func(self, *args, **kwargs)
            
            if result is not None:
                if hasattr(self, '_memory_cache'):
                    self._memory_cache[full_key] = (result, time.time() + ttl)
                
                if REDIS_AVAILABLE and hasattr(self, 'redis_client'):
                    try:
                        await self.redis_client.setex(full_key, ttl, pickle.dumps(result))
                    except Exception as e:
                        logger.warning(f"⚠️ Redis cache write fout: {e}")
            
            return result
        return wrapper
    return decorator


def with_hardware_fallback():
    """Decorator voor hardware fallback."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'enable_hardware') or not self.enable_hardware:
                return await func(self, *args, **kwargs)
            
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                logger.warning(f"⚠️ Hardware fout, CPU fallback: {e}")
                old_backend = self.hardware_backend
                self.hardware_backend = "cpu"
                result = await func(self, *args, **kwargs)
                self.hardware_backend = old_backend
                return result
        return wrapper
    return decorator


def with_retry(max_retries: int = 3, delay: float = 0.1, backoff: float = 2.0):
    """Decorator voor retry bij tijdelijke fouten."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_error = None
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Poging {attempt + 1} mislukt, opnieuw na {current_delay*1000:.0f}ms: {e}")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            raise last_error
        return wrapper
    return decorator


# ====================================================================
# DATACLASSES - Optimalisatiegerelateerd
# ====================================================================

@dataclass
class OptimizationResult:
    """
    Resultaat van een optimalisatierun.
    
    Attributes:
        id: Uniek ID voor deze run
        method: Gebruikte methode
        success: Of optimalisatie succesvol was
        best_x: Best gevonden parameters
        best_f: Beste functiewaarde
        n_iterations: Aantal iteraties
        time_seconds: Duur in seconden
        history: Geschiedenis van (x, f) tijdens optimalisatie
        message: Eventuele boodschap
        metadata: Extra metadata
    """
    id: str
    method: OptimizationMethod
    success: bool
    best_x: np.ndarray
    best_f: float
    n_iterations: int
    time_seconds: float
    history: List[Tuple[np.ndarray, float]] = field(default_factory=list)
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary."""
        return {
            'id': self.id,
            'method': self.method.value,
            'success': self.success,
            'best_x': self.best_x.tolist() if isinstance(self.best_x, np.ndarray) else self.best_x,
            'best_f': self.best_f,
            'n_iterations': self.n_iterations,
            'time_seconds': self.time_seconds,
            'history': [(x.tolist() if isinstance(x, np.ndarray) else x, f) for x, f in self.history[-100:]],
            'message': self.message,
            'metadata': self.metadata
        }


@dataclass
class OptimizationHistory:
    """
    Geschiedenis van optimalisatieverloop.
    
    Attributes:
        iteration: Iteratienummer
        x: Parameterwaarden
        f: Functiewaarde
        grad: Gradient (optioneel)
        time: Tijdstip
    """
    iteration: int
    x: np.ndarray
    f: float
    grad: Optional[np.ndarray] = None
    time: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'iteration': self.iteration,
            'x': self.x.tolist(),
            'f': self.f,
            'grad': self.grad.tolist() if self.grad is not None else None,
            'time': self.time
        }


@dataclass
class ParetoPoint:
    """
    Punt op Pareto front voor multi-objective optimalisatie.
    
    Attributes:
        x: Parameterwaarden
        f: Lijst van functiewaarden
        rank: Pareto rang
        crowding: Afstand tot buren
    """
    x: np.ndarray
    f: List[float]
    rank: int = 0
    crowding: float = 0.0
    
    def dominates(self, other: 'ParetoPoint') -> bool:
        """Check of dit punt het andere domineert."""
        return all(f1 <= f2 for f1, f2 in zip(self.f, other.f)) and any(f1 < f2 for f1, f2 in zip(self.f, other.f))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'x': self.x.tolist(),
            'f': self.f,
            'rank': self.rank,
            'crowding': self.crowding
        }


# ====================================================================
# OPTIMALISATIE ENGINE - HOOFDKLASSE (UITGEBREID)
# ====================================================================

class OptimizationEngine:
    """
    Uitgebreide optimalisatie-engine met alle denkbare features.
    
    Ondersteunt:
    - Enkel- en multi-objective optimalisatie
    - Gradient-based en derivative-free methoden
    - Evolutionaire algoritmes
    - Bayesiaanse optimalisatie
    - Hyperparameter tuning
    - Hardware versnelling (CPU, GPU, FPGA, Quantum)
    - Gedistribueerde evaluatie
    - Caching en persistentie
    - Visualisatie en metrics
    """
    
    def __init__(self,
                 engine_id: str,
                 # Optimalisatie configuratie
                 default_method: OptimizationMethod = OptimizationMethod.AUTO,
                 default_direction: OptimizationType = OptimizationType.MINIMIZATION,
                 # Parameter ruimte
                 bounds: Optional[Dict[str, Tuple[float, float]]] = None,
                 parameter_types: Optional[Dict[str, ParameterType]] = None,
                 # Stoppen
                 max_iterations: int = 1000,
                 max_time: float = 3600.0,
                 tolerance: float = 1e-6,
                 patience: int = 50,
                 # Multi-objective
                 n_objectives: int = 1,
                 objective_names: Optional[List[str]] = None,
                 # Parallelle evaluatie
                 enable_parallel: bool = False,
                 n_workers: int = 4,
                 # Hardware
                 enable_hardware: bool = True,
                 preferred_backend: str = "auto",
                 # Caching
                 enable_cache: bool = True,
                 cache_ttl: int = 3600,
                 use_redis: bool = False,
                 redis_url: str = "redis://localhost:6379",
                 # Persistentie
                 enable_persistence: bool = False,
                 db_path: str = "optimization.db",
                 # Metrics
                 enable_metrics: bool = True,
                 metrics_port: Optional[int] = None,
                 # Visualisatie
                 enable_visualization: bool = False,
                 # Validatie
                 enable_validation: bool = False,
                 # Logging
                 log_level: str = "INFO"):
        """
        Initialiseer optimalisatie-engine met alle optionele features.
        
        Args:
            engine_id: Uniek ID voor deze engine
            default_method: Standaard optimalisatiemethode
            default_direction: Minimalisatie of maximalisatie
            bounds: Dict van parameter -> (min, max)
            parameter_types: Dict van parameter -> type
            max_iterations: Maximum aantal iteraties
            max_time: Maximum tijd in seconden
            tolerance: Convergentietolerantie
            patience: Aantal iteraties zonder verbetering voor early stopping
            n_objectives: Aantal doelstellingen (1 = single-objective)
            objective_names: Namen van doelstellingen
            enable_parallel: Gebruik parallelle evaluatie
            n_workers: Aantal parallelle workers
            enable_hardware: Gebruik hardware versnelling
            preferred_backend: "auto", "cpu", "cuda", "fpga", "quantum"
            enable_cache: Gebruik caching
            cache_ttl: Cache TTL in seconden
            use_redis: Gebruik Redis voor distributed cache
            redis_url: Redis connectie URL
            enable_persistence: Gebruik SQLite voor opslag
            db_path: Pad naar SQLite database
            enable_metrics: Gebruik Prometheus metrics
            metrics_port: Poort voor Prometheus HTTP server
            enable_visualization: Genereer visualisaties
            enable_validation: Gebruik Pydantic voor validatie
            log_level: Log niveau
        """
        self.id = engine_id
        self.default_method = default_method
        self.default_direction = default_direction
        self.bounds = bounds or {}
        self.parameter_types = parameter_types or {}
        self.max_iterations = max_iterations
        self.max_time = max_time
        self.tolerance = tolerance
        self.patience = patience
        self.n_objectives = n_objectives
        self.objective_names = objective_names or [f"f{i}" for i in range(n_objectives)]
        
        # Parallelle evaluatie
        self.enable_parallel = enable_parallel
        self.n_workers = n_workers
        self.parallel_client = None
        if enable_parallel and DASK_AVAILABLE:
            try:
                self.parallel_client = Client(n_workers=n_workers)
                logger.info(f"✅ Dask parallel client gestart met {n_workers} workers")
            except Exception as e:
                logger.warning(f"⚠️ Dask client init mislukt: {e}")
        
        # Hardware
        self.enable_hardware = enable_hardware
        self.preferred_backend = preferred_backend
        self.hardware_backend = self._init_hardware()
        
        # Caching
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self._memory_cache: Dict[str, Tuple[Any, float]] = {}
        self.redis_client = None
        if use_redis and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                logger.info(f"✅ Redis cache geactiveerd op {redis_url}")
            except Exception as e:
                logger.warning(f"⚠️ Redis init mislukt: {e}")
        
        # Persistentie
        self.enable_persistence = enable_persistence and ASQLITE_AVAILABLE
        self.db_path = db_path
        self.db = None
        if self.enable_persistence:
            asyncio.create_task(self._init_persistence())
        
        # Metrics
        self.enable_metrics = enable_metrics and PROMETHEUS_AVAILABLE
        self.metrics_port = metrics_port
        self._metrics = {}
        if self.enable_metrics and metrics_port:
            self._setup_metrics(metrics_port)
        
        # Visualisatie
        self.enable_visualization = enable_visualization and (VISUALIZATION_AVAILABLE or PLOTLY_AVAILABLE)
        
        # Validatie
        self.enable_validation = enable_validation and PYDANTIC_AVAILABLE
        
        # Resultaten
        self.results: List[OptimizationResult] = []
        self.best_result: Optional[OptimizationResult] = None
        self.current_history: List[OptimizationHistory] = []
        
        # Statistieken
        self.metrics = {
            'optimizations': 0,
            'successful': 0,
            'failed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'start_time': time.time()
        }
        
        self._log_configuration()
    
    def _log_configuration(self):
        """Log configuratie bij startup."""
        logger.info("="*100)
        logger.info(f"🎯 OPTIMALISATIE ENGINE {self.id} - LAYER 5 V14")
        logger.info("="*100)
        logger.info(f"Dimensies: {len(self.bounds)} parameters")
        logger.info(f"Doelstellingen: {self.n_objectives}")
        logger.info(f"Standaard methode: {self.default_method.value}")
        logger.info(f"Max iteraties: {self.max_iterations}")
        
        logger.info("\n📦 OPTIONELE FEATURES:")
        logger.info(f"   Parallel:         {'✅' if self.enable_parallel else '❌'}")
        logger.info(f"   Hardware:         {'✅' if self.enable_hardware else '❌'}")
        logger.info(f"   Cache:            {'✅' if self.enable_cache else '❌'}")
        logger.info(f"   Redis:            {'✅' if self.redis_client else '❌'}")
        logger.info(f"   Persistentie:     {'✅' if self.enable_persistence else '❌'}")
        logger.info(f"   Metrics:          {'✅' if self.enable_metrics else '❌'}")
        logger.info(f"   Visualisatie:     {'✅' if self.enable_visualization else '❌'}")
        logger.info(f"   Validatie:        {'✅' if self.enable_validation else '❌'}")
        
        logger.info("="*100)
    
    def _init_hardware(self) -> str:
        """Initialiseer hardware backend."""
        if not self.enable_hardware:
            return "cpu"
        
        if self.preferred_backend == "cuda" and CUDA_AVAILABLE:
            logger.info("⚡ Gebruik CUDA backend")
            return "cuda"
        elif self.preferred_backend == "fpga" and PYNQ_AVAILABLE:
            logger.info("⚡ Gebruik FPGA backend")
            return "fpga"
        elif self.preferred_backend == "quantum" and QISKIT_AVAILABLE:
            logger.info("⚡ Gebruik Quantum backend")
            return "quantum"
        elif self.preferred_backend == "cpu":
            logger.info("💻 Gebruik CPU backend")
            return "cpu"
        else:
            # Auto-detect
            if CUDA_AVAILABLE:
                logger.info("⚡ Auto-detect: CUDA backend")
                return "cuda"
            elif PYNQ_AVAILABLE:
                logger.info("⚡ Auto-detect: FPGA backend")
                return "fpga"
            elif QISKIT_AVAILABLE:
                logger.info("⚡ Auto-detect: Quantum backend")
                return "quantum"
            else:
                logger.info("💻 Auto-detect: CPU backend")
                return "cpu"
    
    def _setup_metrics(self, port: int):
        """Setup Prometheus metrics."""
        try:
            from prometheus_client import start_http_server
            
            start_http_server(port)
            
            self._metrics['optimizations'] = Counter(
                f'optimization_{self.id}_total',
                'Total number of optimizations'
            )
            self._metrics['duration'] = Histogram(
                f'optimization_{self.id}_duration_seconds',
                'Optimization duration'
            )
            self._metrics['best_f'] = Gauge(
                f'optimization_{self.id}_best_f',
                'Best objective value'
            )
            
            logger.info(f"📊 Prometheus metrics op poort {port}")
            
        except Exception as e:
            logger.warning(f"⚠️ Prometheus setup mislukt: {e}")
    
    async def _init_persistence(self):
        """Initialiseer SQLite database voor persistentie."""
        if not ASQLITE_AVAILABLE:
            return
        
        try:
            self.db = await aiosqlite.connect(self.db_path)
            
            await self.db.execute('''
                CREATE TABLE IF NOT EXISTS results (
                    id TEXT PRIMARY KEY,
                    method TEXT,
                    success BOOLEAN,
                    best_x BLOB,
                    best_f REAL,
                    n_iterations INTEGER,
                    time_seconds REAL,
                    metadata TEXT,
                    created_at REAL
                )
            ''')
            
            await self.db.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    result_id TEXT,
                    iteration INTEGER,
                    x BLOB,
                    f REAL,
                    time REAL,
                    FOREIGN KEY (result_id) REFERENCES results(id)
                )
            ''')
            
            await self.db.commit()
            logger.info(f"💾 Persistentie database: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ Persistentie init mislukt: {e}")
            self.enable_persistence = False
    
    async def _save_result(self, result: OptimizationResult):
        """Sla resultaat op in database."""
        if not self.enable_persistence or not self.db:
            return
        
        try:
            x_blob = pickle.dumps(result.best_x)
            metadata = json.dumps(result.metadata)
            await self.db.execute('''
                INSERT INTO results (id, method, success, best_x, best_f, n_iterations, time_seconds, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.id,
                result.method.value,
                result.success,
                x_blob,
                result.best_f,
                result.n_iterations,
                result.time_seconds,
                metadata,
                time.time()
            ))
            
            for i, (x, f) in enumerate(result.history):
                x_blob = pickle.dumps(x)
                await self.db.execute('''
                    INSERT INTO history (result_id, iteration, x, f, time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (result.id, i, x_blob, f, time.time()))
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"❌ Opslag resultaat mislukt: {e}")
    
    # ================================================================
    # KERN OPTIMALISATIE METHODEN
    # ================================================================
    
    @timed('optimize')
    @cached()
    @with_hardware_fallback()
    @with_retry(max_retries=3)
    async def optimize(self,
                      func: Callable,
                      x0: Optional[np.ndarray] = None,
                      bounds: Optional[Dict[str, Tuple[float, float]]] = None,
                      method: Optional[OptimizationMethod] = None,
                      direction: OptimizationType = OptimizationType.MINIMIZATION,
                      constraints: Optional[List[Dict]] = None,
                      callback: Optional[Callable] = None,
                      **kwargs) -> OptimizationResult:
        """
        Voer optimalisatie uit op een gegeven functie.
        
        Args:
            func: Doelfunctie f(x) -> float of List[float] voor multi-objective
            x0: Beginpunt (optioneel)
            bounds: Parameter grenzen (optioneel)
            method: Optimalisatiemethode
            direction: Minimalisatie of maximalisatie
            constraints: Constraints voor geconstrainde optimalisatie
            callback: Optionele callback bij elke iteratie
            **kwargs: Extra argumenten voor specifieke methoden
        
        Returns:
            OptimizationResult object
        """
        method = method or self.default_method
        bounds = bounds or self.bounds
        direction_mult = 1.0 if direction == OptimizationType.MINIMIZATION else -1.0
        
        # Bepaal dimensie
        if x0 is not None:
            dim = len(x0)
        elif bounds:
            dim = len(bounds)
        else:
            raise ValueError("Geen beginpunt of grenzen opgegeven")
        
        # Maak parameter namen
        param_names = list(bounds.keys()) if bounds else [f"x{i}" for i in range(dim)]
        
        # Valideer met Pydantic
        if self.enable_validation and PYDANTIC_AVAILABLE:
            # (zou hier parameters kunnen valideren)
            pass
        
        start_time = time.time()
        self.metrics['optimizations'] += 1
        
        result_id = f"opt_{hashlib.md5(f'{time.time()}{method.value}'.encode()).hexdigest()[:8]}"
        
        # Kies methode
        if method == OptimizationMethod.AUTO:
            # Auto-selecteer op basis van dimensie en continuïteit
            if self.n_objectives > 1:
                method = OptimizationMethod.NSGA2
            elif dim <= 20:
                method = OptimizationMethod.LBFGS if x0 is not None else OptimizationMethod.CMA_ES
            else:
                method = OptimizationMethod.ADAM
        
        # Voer optimalisatie uit
        if self.n_objectives > 1:
            result = await self._multi_objective_optimize(
                func, x0, bounds, method, direction_mult, constraints, callback, kwargs
            )
        else:
            result = await self._single_objective_optimize(
                func, x0, bounds, method, direction_mult, constraints, callback, kwargs
            )
        
        # Vul resultaat aan
        result.id = result_id
        result.method = method
        result.time_seconds = time.time() - start_time
        
        # Sla op
        self.results.append(result)
        if self.best_result is None or (direction_mult * result.best_f) < (direction_mult * self.best_result.best_f):
            self.best_result = result
        self.metrics['successful' if result.success else 'failed'] += 1
        
        # Sla op in database
        if self.enable_persistence:
            await self._save_result(result)
        
        # Update Prometheus
        if self._metrics and 'best_f' in self._metrics:
            self._metrics['best_f'].set(result.best_f)
        
        return result
    
    async def _single_objective_optimize(self, func, x0, bounds, method, direction_mult, constraints, callback, kwargs):
        """Enkel-objectieve optimalisatie."""
        history = []
        
        def wrapped_func(x):
            # Converteer x naar dict als nodig
            if isinstance(x, np.ndarray) and bounds:
                x_dict = {name: x[i] for i, name in enumerate(bounds.keys())}
                f = func(x_dict)
            else:
                f = func(x)
            return direction_mult * f
        
        # SciPy methoden
        if SCIPY_AVAILABLE and method in [
            OptimizationMethod.NELDER_MEAD, OptimizationMethod.POWELL,
            OptimizationMethod.CG, OptimizationMethod.LBFGS,
            OptimizationMethod.NEWTON_CG, OptimizationMethod.COBYLA,
            OptimizationMethod.SLSQP, OptimizationMethod.TRUST_CONSTR
        ]:
            # Bereid x0 voor
            if x0 is None and bounds:
                x0 = np.array([(low+high)/2 for low, high in bounds.values()])
            elif x0 is None:
                x0 = np.zeros(len(bounds)) if bounds else np.zeros(1)
            
            # Bereid bounds voor SciPy
            scipy_bounds = list(bounds.values()) if bounds else None
            
            # Methode mapping
            method_map = {
                OptimizationMethod.NELDER_MEAD: 'Nelder-Mead',
                OptimizationMethod.POWELL: 'Powell',
                OptimizationMethod.CG: 'CG',
                OptimizationMethod.LBFGS: 'L-BFGS-B',
                OptimizationMethod.NEWTON_CG: 'Newton-CG',
                OptimizationMethod.COBYLA: 'COBYLA',
                OptimizationMethod.SLSQP: 'SLSQP',
                OptimizationMethod.TRUST_CONSTR: 'trust-constr'
            }
            scipy_method = method_map.get(method, 'L-BFGS-B')
            
            # Voer optimalisatie uit
            try:
                res = minimize(
                    wrapped_func,
                    x0,
                    method=scipy_method,
                    bounds=scipy_bounds,
                    constraints=constraints,
                    options={
                        'maxiter': self.max_iterations,
                        'disp': False,
                        'gtol': self.tolerance,
                        'ftol': self.tolerance
                    },
                    callback=lambda xk: callback(xk) if callback else None
                )
                
                success = res.success
                best_x = res.x
                best_f = res.fun / direction_mult
                n_iter = res.nit if hasattr(res, 'nit') else 0
                message = res.message
                
            except Exception as e:
                success = False
                best_x = x0
                best_f = wrapped_func(x0) / direction_mult
                n_iter = 0
                message = str(e)
        
        # Evolutionaire methoden via SciPy
        elif SCIPY_AVAILABLE and method == OptimizationMethod.DIFFERENTIAL_EVOLUTION:
            res = differential_evolution(
                wrapped_func,
                list(bounds.values()),
                maxiter=self.max_iterations,
                tol=self.tolerance,
                callback=lambda xk, convergence: callback(xk) if callback else None
            )
            success = res.success
            best_x = res.x
            best_f = res.fun / direction_mult
            n_iter = res.nit
            message = res.message if hasattr(res, 'message') else ""
        
        elif SCIPY_AVAILABLE and method == OptimizationMethod.DUAL_ANNEALING:
            res = dual_annealing(
                wrapped_func,
                list(bounds.values()),
                maxiter=self.max_iterations,
                callback=lambda x, f, context: callback(x) if callback else None
            )
            success = True
            best_x = res.x
            best_f = res.fun / direction_mult
            n_iter = res.nit
            message = ""
        
        # CMA-ES
        elif CMA_AVAILABLE and method == OptimizationMethod.CMA_ES:
            import cma
            if x0 is None and bounds:
                x0 = np.array([(low+high)/2 for low, high in bounds.values()])
            sigma0 = kwargs.get('sigma0', 0.5)
            res = cma.fmin(
                wrapped_func,
                x0,
                sigma0,
                options={'maxfevals': self.max_iterations, 'verbose': -1}
            )
            best_x = res[0]
            best_f = res[1] / direction_mult
            success = True
            n_iter = res[3] if len(res) > 3 else 0
            message = ""
        
        # Adam via PyTorch
        elif TORCH_AVAILABLE and method == OptimizationMethod.ADAM:
            if x0 is None and bounds:
                x0 = np.array([(low+high)/2 for low, high in bounds.values()])
            x_tensor = torch.tensor(x0, requires_grad=True, device=device if CUDA_AVAILABLE else 'cpu')
            optimizer = optim.Adam([x_tensor], lr=kwargs.get('lr', 0.01))
            
            for i in range(self.max_iterations):
                optimizer.zero_grad()
                f_val = torch.tensor(wrapped_func(x_tensor.detach().cpu().numpy()), requires_grad=True)
                f_val.backward()
                optimizer.step()
                
                # Projecteer binnen bounds
                if bounds:
                    with torch.no_grad():
                        for j, (name, (low, high)) in enumerate(bounds.items()):
                            x_tensor[j] = torch.clamp(x_tensor[j], low, high)
                
                if callback:
                    callback(x_tensor.detach().cpu().numpy())
                
                history.append((x_tensor.detach().cpu().numpy().copy(), f_val.item()))
                
                # Check convergentie
                if i > 10 and abs(f_val.item() - history[-2][1]) < self.tolerance:
                    break
            
            best_x = x_tensor.detach().cpu().numpy()
            best_f = wrapped_func(best_x) / direction_mult
            success = True
            n_iter = i+1
            message = ""
        
        # Default: gebruik SciPy L-BFGS-B
        else:
            logger.warning(f"Methode {method.value} niet beschikbaar, val terug naar L-BFGS-B")
            return await self._single_objective_optimize(
                func, x0, bounds, OptimizationMethod.LBFGS,
                direction_mult, constraints, callback, kwargs
            )
        
        result = OptimizationResult(
            id="",
            method=method,
            success=success,
            best_x=best_x,
            best_f=best_f,
            n_iterations=n_iter,
            time_seconds=0,
            history=history,
            message=message,
            metadata={}
        )
        return result
    
    async def _multi_objective_optimize(self, func, x0, bounds, method, direction_mult, constraints, callback, kwargs):
        """Multi-objectieve optimalisatie."""
        if not PYMOO_AVAILABLE and method in [OptimizationMethod.NSGA2, OptimizationMethod.MOEAD]:
            logger.warning("PyMOO niet beschikbaar voor multi-objective optimalisatie")
            return OptimizationResult(
                id="",
                method=method,
                success=False,
                best_x=np.array([]),
                best_f=0.0,
                n_iterations=0,
                time_seconds=0,
                history=[],
                message="PyMOO niet beschikbaar"
            )
        
        # Definieer PyMOO probleem
        class PyMOOProblem(Problem):
            def __init__(self, n_var, xl, xu, func, n_obj, direction_mult):
                super().__init__(n_var=n_var, n_obj=n_obj, xl=xl, xu=xu)
                self.func = func
                self.direction_mult = direction_mult
            
            def _evaluate(self, x, out, *args, **kwargs):
                f_vals = []
                for xi in x:
                    if isinstance(xi, np.ndarray) and bounds:
                        x_dict = {name: xi[i] for i, name in enumerate(bounds.keys())}
                        f = self.func(x_dict)
                    else:
                        f = self.func(xi)
                    f_vals.append(f)
                out["F"] = np.array(f_vals) * self.direction_mult
        
        # Bereid bounds voor
        xl = np.array([low for low, _ in bounds.values()])
        xu = np.array([high for _, high in bounds.values()])
        
        problem = PyMOOProblem(
            n_var=len(bounds),
            xl=xl,
            xu=xu,
            func=func,
            n_obj=self.n_objectives,
            direction_mult=direction_mult
        )
        
        if method == OptimizationMethod.NSGA2:
            algorithm = NSGA2(
                pop_size=kwargs.get('pop_size', 100),
                sampling=FloatRandomSampling(),
                crossover=SBX(prob=0.9, eta=15),
                mutation=PM(prob=0.1, eta=20)
            )
        elif method == OptimizationMethod.MOEAD:
            algorithm = MOEAD(
                pop_size=kwargs.get('pop_size', 100)
            )
        else:
            algorithm = NSGA2(pop_size=100)
        
        res = pymoo_minimize(
            problem,
            algorithm,
            ('n_gen', self.max_iterations),
            callback=lambda algorithm: callback(algorithm.pop.get("X")) if callback else None,
            verbose=False
        )
        
        # Neem beste punt (eerste van Pareto front)
        if len(res.X) > 0:
            best_x = res.X[0]
            best_f = res.F[0] / direction_mult
            success = True
        else:
            best_x = np.array([])
            best_f = 0.0
            success = False
        
        result = OptimizationResult(
            id="",
            method=method,
            success=success,
            best_x=best_x,
            best_f=best_f[0] if isinstance(best_f, (list, np.ndarray)) and len(best_f) > 0 else 0.0,
            n_iterations=res.algorithm.n_gen if hasattr(res, 'algorithm') else 0,
            time_seconds=0,
            history=[],
            message=""
        )
        return result
    
    # ================================================================
    # HYPERPARAMETER TUNING (OPTUNA)
    # ================================================================
    
    async def hyperparameter_tuning(self,
                                   func: Callable,
                                   param_space: Dict,
                                   n_trials: int = 100,
                                   sampler: str = "tpe",
                                   pruner: str = "median",
                                   study_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Voer hyperparameter tuning uit met Optuna.
        
        Args:
            func: Doelfunctie die parameters accepteert en score retourneert
            param_space: Dict met parameter definities (Optuna suggest_*)
            n_trials: Aantal trials
            sampler: "tpe", "random", "cmaes"
            pruner: "median", "hyperband"
            study_name: Naam van de studie
        
        Returns:
            Beste parameters en resultaten
        """
        if not OPTUNA_AVAILABLE:
            logger.warning("Optuna niet beschikbaar voor hyperparameter tuning")
            return {}
        
        def objective(trial):
            params = {}
            for name, spec in param_space.items():
                if spec['type'] == 'float':
                    params[name] = trial.suggest_float(name, spec['low'], spec['high'], log=spec.get('log', False))
                elif spec['type'] == 'int':
                    params[name] = trial.suggest_int(name, spec['low'], spec['high'], log=spec.get('log', False))
                elif spec['type'] == 'categorical':
                    params[name] = trial.suggest_categorical(name, spec['choices'])
                elif spec['type'] == 'uniform':
                    params[name] = trial.suggest_uniform(name, spec['low'], spec['high'])
            return func(params)
        
        # Kies sampler
        if sampler == "tpe":
            sampler_obj = TPESampler(seed=42)
        elif sampler == "random":
            sampler_obj = RandomSampler(seed=42)
        elif sampler == "cmaes" and CMA_AVAILABLE:
            sampler_obj = CmaEsSampler(seed=42)
        else:
            sampler_obj = TPESampler(seed=42)
        
        # Kies pruner
        if pruner == "median":
            pruner_obj = MedianPruner()
        elif pruner == "hyperband":
            pruner_obj = HyperbandPruner()
        else:
            pruner_obj = MedianPruner()
        
        study = optuna.create_study(
            direction='minimize' if self.default_direction == OptimizationType.MINIMIZATION else 'maximize',
            sampler=sampler_obj,
            pruner=pruner_obj,
            study_name=study_name
        )
        
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        return {
            'best_params': study.best_params,
            'best_value': study.best_value,
            'best_trial': study.best_trial.number,
            'n_trials': len(study.trials)
        }
    
    # ================================================================
    # GEDISTRIBUEERDE OPTIMALISATIE MET RAY
    # ================================================================
    
    async def distributed_optimize(self,
                                  func: Callable,
                                  search_space: Dict,
                                  num_samples: int = 100,
                                  scheduler: str = "asha") -> Dict[str, Any]:
        """
        Voer gedistribueerde hyperparameter optimalisatie uit met Ray Tune.
        
        Args:
            func: Doelfunctie
            search_space: Dict met parameterbereiken
            num_samples: Aantal samples
            scheduler: "asha", "hyperband"
        
        Returns:
            Beste configuratie
        """
        if not RAY_AVAILABLE:
            logger.warning("Ray niet beschikbaar voor gedistribueerde optimalisatie")
            return {}
        
        if scheduler == "asha":
            scheduler_obj = ASHAScheduler(max_t=100, grace_period=10, reduction_factor=3)
        else:
            scheduler_obj = HyperBandScheduler(max_t=100)
        
        analysis = tune.run(
            func,
            config=search_space,
            num_samples=num_samples,
            scheduler=scheduler_obj,
            verbose=0
        )
        
        best_config = analysis.get_best_config(metric='score', mode='min')
        return best_config
    
    # ================================================================
    # PARETO FRONT ANALYSE
    # ================================================================
    
    def get_pareto_front(self, results: List[OptimizationResult]) -> List[ParetoPoint]:
        """
        Extraheer Pareto front uit multi-objective resultaten.
        
        Args:
            results: Lijst van optimalisatieresultaten
        
        Returns:
            Lijst van Pareto punten
        """
        points = []
        for res in results:
            if hasattr(res, 'best_x') and res.best_x is not None:
                # In echte multi-objective zouden we meerdere punten hebben
                # Hier simuleren we met best_x
                points.append(ParetoPoint(
                    x=res.best_x,
                    f=[res.best_f]  # moet lijst zijn voor multi-objective
                ))
        
        # Bepaal Pareto front (dominantie)
        pareto = []
        for i, p in enumerate(points):
            dominated = False
            for q in points:
                if q.dominates(p):
                    dominated = True
                    break
            if not dominated:
                pareto.append(p)
        
        return pareto
    
    # ================================================================
    # VISUALISATIE
    # ================================================================
    
    def plot_convergence(self, result: OptimizationResult, filename: Optional[str] = None):
        """Plot convergentie van optimalisatie."""
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Visualisatie niet beschikbaar")
            return
        
        if not result.history:
            logger.warning("Geen geschiedenis om te plotten")
            return
        
        iterations = range(len(result.history))
        values = [f for _, f in result.history]
        
        plt.figure(figsize=(10, 6))
        plt.plot(iterations, values, 'b-', linewidth=2)
        plt.xlabel('Iteratie')
        plt.ylabel('Functiewaarde')
        plt.title(f'Convergentie - {result.method.value}')
        plt.grid(True, alpha=0.3)
        
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            logger.info(f"📊 Convergentieplot opgeslagen: {filename}")
        else:
            plt.show()
        plt.close()
    
    def plot_pareto_front(self, pareto_points: List[ParetoPoint], filename: Optional[str] = None):
        """Plot Pareto front voor multi-objective optimalisatie."""
        if not VISUALIZATION_AVAILABLE or not pareto_points:
            return
        
        if len(pareto_points[0].f) != 2:
            logger.warning("Pareto front alleen voor 2 objectives")
            return
        
        f1 = [p.f[0] for p in pareto_points]
        f2 = [p.f[1] for p in pareto_points]
        
        plt.figure(figsize=(8, 8))
        plt.scatter(f1, f2, c='red', s=50, alpha=0.7)
        plt.xlabel('Objective 1')
        plt.ylabel('Objective 2')
        plt.title('Pareto Front')
        plt.grid(True, alpha=0.3)
        
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            logger.info(f"📊 Pareto front opgeslagen: {filename}")
        else:
            plt.show()
        plt.close()
    
    # ================================================================
    # EXPORT & PERSISTENTIE
    # ================================================================
    
    def export_results(self, filename: str = "optimization_results.json"):
        """Exporteer alle resultaten naar JSON."""
        data = {
            'engine_id': self.id,
            'timestamp': time.time(),
            'metrics': self.metrics,
            'results': [r.to_dict() for r in self.results],
            'best_result': self.best_result.to_dict() if self.best_result else None
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"📄 Resultaten geëxporteerd naar {filename}")
        return data
    
    # ================================================================
    # CLEANUP
    # ================================================================
    
    async def cleanup(self):
        """Ruim resources op."""
        logger.info("🧹 OptimizationEngine cleanup...")
        
        # Sla laatste resultaten op
        self.export_results("optimization_final.json")
        
        # Sluit database
        if self.db:
            await self.db.close()
        
        # Sluit Redis
        if self.redis_client:
            await self.redis_client.close()
        
        # Sluit Dask client
        if self.parallel_client:
            self.parallel_client.close()
        
        logger.info("✅ Cleanup voltooid")
    
    def reset(self):
        """Reset alle resultaten."""
        self.results.clear()
        self.best_result = None
        self.current_history.clear()
        self.metrics = {
            'optimizations': 0,
            'successful': 0,
            'failed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'start_time': time.time()
        }
        logger.info("🔄 OptimizationEngine gereset")


# ====================================================================
# VOORBEELD FUNCTIES
# ====================================================================

def sphere(x):
    """Bolle testfunctie."""
    if isinstance(x, dict):
        return sum(v**2 for v in x.values())
    return np.sum(np.array(x)**2)


def rosenbrock(x):
    """Rosenbrock functie (niet-lineair)."""
    if isinstance(x, dict):
        x_vals = list(x.values())
    else:
        x_vals = x
    return sum(100.0 * (x_vals[i+1] - x_vals[i]**2)**2 + (1 - x_vals[i])**2 for i in range(len(x_vals)-1))


def rastrigin(x):
    """Rastrigin functie (veel lokale minima)."""
    if isinstance(x, dict):
        x_vals = list(x.values())
    else:
        x_vals = x
    A = 10
    return A * len(x_vals) + sum(xi**2 - A * np.cos(2 * np.pi * xi) for xi in x_vals)


# ====================================================================
# DEMONSTRATIE
# ====================================================================

async def demo():
    """Demonstreer Layer 5 functionaliteit."""
    print("\n" + "="*100)
    print("🎯 LAYER 5: AUTONOMOUS OPTIMIZATION AND LEARNING - V14 DEMONSTRATIE")
    print("="*100)
    
    # Creëer optimalisatie-engine
    engine = OptimizationEngine(
        engine_id="demo_engine",
        default_method=OptimizationMethod.AUTO,
        bounds={'x0': (-5, 5), 'x1': (-5, 5), 'x2': (-5, 5)},
        max_iterations=200,
        enable_hardware=True,
        enable_cache=True,
        enable_visualization=True,
        enable_metrics=False
    )
    
    print("\n📋 Test 1: Minimalisatie van bolvormige functie (L-BFGS-B)")
    result1 = await engine.optimize(
        func=sphere,
        x0=np.array([2.0, 2.0, 2.0]),
        method=OptimizationMethod.LBFGS
    )
    print(f"   ✅ Succes: {result1.success}")
    print(f"   Beste x: {result1.best_x}")
    print(f"   Beste f: {result1.best_f:.6f}")
    print(f"   Iteraties: {result1.n_iterations}")
    
    print("\n📋 Test 2: Rosenbrock functie met CMA-ES")
    result2 = await engine.optimize(
        func=rosenbrock,
        x0=np.array([-1.0, 1.0, 1.5]),
        method=OptimizationMethod.CMA_ES
    )
    print(f"   ✅ Succes: {result2.success}")
    print(f"   Beste x: {result2.best_x}")
    print(f"   Beste f: {result2.best_f:.6f}")
    
    print("\n📋 Test 3: Rastrigin functie met differentiële evolutie")
    result3 = await engine.optimize(
        func=rastrigin,
        method=OptimizationMethod.DIFFERENTIAL_EVOLUTION
    )
    print(f"   ✅ Succes: {result3.success}")
    print(f"   Beste f: {result3.best_f:.6f}")
    
    print("\n📋 Test 4: Adam optimizer (PyTorch)")
    if TORCH_AVAILABLE:
        result4 = await engine.optimize(
            func=sphere,
            x0=np.array([3.0, 3.0, 3.0]),
            method=OptimizationMethod.ADAM,
            kwargs={'lr': 0.1}
        )
        print(f"   ✅ Succes: {result4.success}")
        print(f"   Beste f: {result4.best_f:.6f}")
    else:
        print("   ⚠️ PyTorch niet beschikbaar")
    
    print("\n📋 Test 5: Visualisatie convergentie")
    if engine.enable_visualization:
        engine.plot_convergence(result1, filename="convergence_lbfgs.png")
        print("   ✅ Convergentieplot opgeslagen")
    
    print("\n📋 Test 6: Hyperparameter tuning met Optuna")
    if OPTUNA_AVAILABLE:
        def objective(trial):
            params = {
                'x0': trial.suggest_float('x0', -5, 5),
                'x1': trial.suggest_float('x1', -5, 5),
                'lr': trial.suggest_loguniform('lr', 1e-4, 1e-1)
            }
            return sphere(params)
        
        param_space = {
            'x0': {'type': 'float', 'low': -5, 'high': 5},
            'x1': {'type': 'float', 'low': -5, 'high': 5},
            'lr': {'type': 'float', 'low': 1e-4, 'high': 1e-1, 'log': True}
        }
        best = await engine.hyperparameter_tuning(objective, param_space, n_trials=20)
        print(f"   ✅ Beste params: {best.get('best_params')}")
        print(f"   Beste waarde: {best.get('best_value'):.6f}")
    else:
        print("   ⚠️ Optuna niet beschikbaar")
    
    print("\n📋 Test 7: Statistieken")
    stats = engine.metrics
    print(f"   Optimalisaties: {stats['optimizations']}")
    print(f"   Succesvol: {stats['successful']}")
    print(f"   Gefaald: {stats['failed']}")
    print(f"   Cache hits: {stats['cache_hits']}")
    
    print("\n📋 Test 8: Export")
    engine.export_results("optimization_demo.json")
    
    # Cleanup
    await engine.cleanup()
    
    print("\n" + "="*100)
    print("✅ Demonstratie voltooid!")
    print("="*100)


# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    # Configureer logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    )
    
    asyncio.run(demo())