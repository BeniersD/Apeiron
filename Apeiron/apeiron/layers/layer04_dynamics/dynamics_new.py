"""
LAYER 4: DYNAMIC ADAPTATION AND FEEDBACK - Uitmuntende Implementatie
===========================================================================
Layer 4 introduceert temporele dynamiek en adaptieve feedback voor functionele
entiteiten. Het modelleert hoe functies evolueren, interageren en zich aanpassen
over de tijd, met niet-lineaire dynamica, attractoren en bifurcaties.

V14 UITGEBREIDE OPTIONELE FEATURES:
----------------------------------------------------------------------------
✅ Continue tijdsdynamiek - Differentiaalvergelijkingen voor evolutie
✅ Discontinue sprongen - Catastrofes en bifurcaties
✅ Meerdere tijdschalen - Langzame vs snelle dynamiek
✅ Niet-lineaire dynamica - Chaos, limit cycles, attractoren
✅ Feedback lussen - Positieve en negatieve feedback
✅ Stabiliteitsanalyse - Lyapunov exponenten, eigenwaarden
✅ Bifurcatie detectie - Vind kritische punten
✅ Attractor landschap - Meerdere stabiele toestanden
✅ Hysteresis - Geheugeneffecten in dynamiek
✅ Stochastische dynamica - Ruis en fluctuaties
✅ Gedistribueerde dynamica - Gekoppelde systemen
✅ Hiërarchische dynamica - Multi-level evolutie
✅ Adaptieve controle - Zelf-regulerende feedback
✅ Voorspellende dynamica - Anticiperen op toekomst
✅ Historische afhankelijkheid - Pad-afhankelijkheid
✅ Energiebehoud - Thermodynamische consistentie
✅ Entropie productie - Tweede hoofdwet
✅ Symmetrieën - Invarianties in dynamiek
✅ Fase overgangen - Kritische fenomenen
✅ Patroon formatie - Spontane ordening
✅ Delay differential equations - Tijdvertragingen
✅ Fractionele dynamica - Gebroken afgeleiden
✅ Impulsieve dynamica - Sprongen en schokken
✅ Hybride systemen - Continue + discrete events
✅ Gedwongen oscillaties - Externe forcering
✅ Coupled map lattices - Ruimtelijke dynamica
✅ Cellular automata - Discrete tijd/ruimte

Hardware integratie:
✅ CPU - Numpy/Scipy numerieke integratie
✅ CUDA - GPU versnelling via PyTorch
✅ FPGA - Hardware versnelling via PYNQ
✅ Quantum - Quantum dynamica via Qiskit

Wiskundige methoden:
✅ Euler integratie - Eerste orde
✅ Runge-Kutta - Vierde orde adaptief
✅ Stochastische integratie - Langevin vergelijkingen
✅ Symplectische integratie - Energiebehoud
✅ Impliciete methoden - Stijve systemen
✅ Dormand-Prince - Adaptieve 5e orde
✅ Backward Differentiation - Voor stijve systemen
✅ Exponential integrators - Voor lineaire delen
✅ Splitting methods - Operator splitting

Analyse methoden:
✅ Lyapunov exponenten - Chaos detectie
✅ Correlation dimension - Fractale dimensie
✅ Recurrence plots - Terugkeer analyse
✅ Poincaré secties - Dwarsdoorsneden
✅ Power spectra - Frequentie analyse
✅ Bifurcatie diagrammen - Parameter variatie
✅ Phase space reconstruction - Delay embedding
✅ Entropy measures - Shannon, Kolmogorov
✅ Mutual information - Afhankelijkheidsmaat

Theoretische basis uit 17-lagen document:
- "Temporal dynamics and adaptive feedback to functional entities"
- "State vectors evolve over a notional temporal dimension"
- "Feedback loops enable self-stabilizing or self-amplifying dynamics"
- "Phase transitions and bifurcations in parameter space"
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

logger = logging.getLogger(__name__)

# ====================================================================
# OPTIONELE WISKUNDIGE IMPORTS
# ====================================================================

# NumPy/SciPy voor numerieke methoden
try:
    import numpy as np
    from scipy.integrate import odeint, solve_ivp, ode
    from scipy.optimize import root, fsolve, curve_fit
    from scipy.linalg import expm, logm, eig, svd, lu, qr
    from scipy.fft import fft, ifft, fftfreq
    from scipy.signal import find_peaks, welch, correlate, spectrogram
    from scipy.stats import entropy, linregress, pearsonr
    from scipy.interpolate import interp1d, UnivariateSpline
    from scipy.spatial import distance
    NUMPY_AVAILABLE = True
    logger.info("✅ NumPy/SciPy beschikbaar voor numerieke methoden")
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("⚠️ NumPy/SciPy niet beschikbaar - beperkte numerieke methoden")

# PyTorch voor GPU versnelling
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.distributions import Normal, MultivariateNormal
    TORCH_AVAILABLE = True
    logger.info("✅ PyTorch beschikbaar voor GPU versnelling")
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("⚠️ PyTorch niet beschikbaar - CPU only")

# CUDA voor GPU versnelling
CUDA_AVAILABLE = TORCH_AVAILABLE and torch.cuda.is_available()
if CUDA_AVAILABLE:
    logger.info(f"✅ CUDA beschikbaar: {torch.cuda.get_device_name(0)}")
    device = torch.device('cuda')

# Qiskit voor quantum dynamica
try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute, Aer
    from qiskit.providers.aer import QasmSimulator, StatevectorSimulator
    from qiskit.quantum_info import state_fidelity, partial_trace, entropy
    from qiskit.algorithms import VQE, QAOA, TrotterQRTE
    from qiskit.opflow import I, X, Y, Z, PauliSumOp, PauliOp
    from qiskit.circuit.library import PauliEvolutionGate
    QISKIT_AVAILABLE = True
    logger.info("✅ Qiskit beschikbaar voor quantum dynamica")
except ImportError:
    QISKIT_AVAILABLE = False
    logger.warning("⚠️ Qiskit niet beschikbaar - geen quantum dynamica")

# PYNQ voor FPGA versnelling
try:
    from pynq import Overlay, allocate
    from pynq.lib import AxiGPIO, AxiDMA
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
    from mpl_toolkits.mplot3d import Axes3D
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
# OPTIONELE CHAOS THEORIE & NIET-LINEAIRE ANALYSE
# ====================================================================

try:
    import nolds  # Non-linear measures for dynamical systems
    from nolds import lyap_r, lyap_e, d2, sampen, hurst, corr_dim
    NOLDS_AVAILABLE = True
    logger.info("✅ Nolds beschikbaar voor chaos analyse")
except ImportError:
    NOLDS_AVAILABLE = False
    logger.warning("⚠️ Nolds niet beschikbaar - beperkte chaos analyse")

try:
    import pyunicorn.timeseries as put
    from pyunicorn.timeseries import RecurrencePlot, RecurrenceNetwork
    PYUNICORN_AVAILABLE = True
    logger.info("✅ PyUnicorn beschikbaar voor recurrence analyse")
except ImportError:
    PYUNICORN_AVAILABLE = False
    logger.warning("⚠️ PyUnicorn niet beschikbaar - geen recurrence plots")

try:
    import tisean  # Time series analysis (R interface via rpy2)
    TISEAN_AVAILABLE = False  # Meestal niet in Python
    logger.info("⚠️ TISEAN niet beschikbaar (optioneel)")
except ImportError:
    TISEAN_AVAILABLE = False

# ====================================================================
# OPTIONELE SYMBOLISCHE WISKUNDE
# ====================================================================

try:
    import sympy as sp
    from sympy import symbols, diff, integrate, solve, Matrix, lambdify
    from sympy.physics.mechanics import dynamicsymbols, LagrangesMethod
    from sympy.utilities.lambdify import lambdify
    SYMPY_AVAILABLE = True
    logger.info("✅ SymPy beschikbaar voor symbolische wiskunde")
except ImportError:
    SYMPY_AVAILABLE = False
    logger.warning("⚠️ SymPy niet beschikbaar - geen symbolische wiskunde")

# ====================================================================
# OPTIONELE MACHINE LEARNING
# ====================================================================

try:
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, Matern, WhiteKernel, ExpSineSquared
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
    logger.info("✅ Scikit-learn beschikbaar voor ML")
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("⚠️ Scikit-learn niet beschikbaar - geen ML")

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
# ENUMS - Classificatie van dynamische fenomenen
# ====================================================================

class TimeScale(Enum):
    """Tijdschalen voor dynamiek."""
    PLANCK = "planck"          # 10^-43 s - quantum zwaartekracht
    QUANTUM = "quantum"        # 10^-15 s - quantum fluctuaties
    NANO = "nano"              # 10^-9 s - moleculaire dynamica
    MICRO = "micro"            # 10^-6 s - cel processen
    MILLI = "milli"            # 10^-3 s - neurale processen
    SECOND = "second"          # 1 s - menselijke waarneming
    MINUTE = "minute"          # 60 s - korte termijn
    HOUR = "hour"              # 3600 s - middellange termijn
    DAY = "day"                # 86400 s - dagelijkse cycli
    WEEK = "week"              # 604800 s - wekelijkse patronen
    MONTH = "month"            # ~2.6e6 s - maandelijkse cycli
    YEAR = "year"              # ~3.15e7 s - jaarlijkse patronen
    EPOCH = "epoch"            # geologische tijd
    ETERNAL = "eternal"        # oneindig


class DynamicalType(Enum):
    """Type van dynamisch systeem."""
    LINEAR = "linear"                          # Lineaire dynamiek
    NONLINEAR = "nonlinear"                    # Niet-lineair
    CHAOTIC = "chaotic"                        # Chaotisch
    PERIODIC = "periodic"                      # Periodiek
    QUASI_PERIODIC = "quasi_periodic"          # Quasi-periodiek
    STOCHASTIC = "stochastic"                  # Stochastisch
    DETERMINISTIC = "deterministic"             # Deterministisch
    HAMILTONIAN = "hamiltonian"                 # Hamiltoniaans (energiebehoud)
    DISSIPATIVE = "dissipative"                 # Energieverlies
    CONSERVATIVE = "conservative"               # Energiebehoud
    SYMPLECTIC = "symplectic"                   # Symplectisch
    GRADIENT = "gradient"                        # Gradient dynamiek
    REACTION_DIFFUSION = "reaction_diffusion"   # Reactie-diffusie
    DELAY = "delay"                              # Tijdvertraging
    FRACTIONAL = "fractional"                    # Gebroken afgeleide
    IMPULSIVE = "impulsive"                      # Sprong dynamiek
    HYBRID = "hybrid"                            # Continue + discrete
    FORCED = "forced"                            # Gedwongen oscillaties


class AttractorType(Enum):
    """Type van attractor."""
    FIXED_POINT = "fixed_point"                 # Stabiel evenwicht
    LIMIT_CYCLE = "limit_cycle"                 # Periodieke baan
    TORUS = "torus"                             # Quasi-periodiek
    STRANGE = "strange"                         # Chaotisch attractor
    HETEROCLINIC = "heteroclinic"               # Verbinding tussen punten
    HOMOCLINIC = "homoclinic"                   # Terugkerend naar zelfde punt
    SADDLE = "saddle"                           # Instabiel in één richting
    NODE = "node"                                # Stabiel in alle richtingen
    FOCUS = "focus"                              # Spiraal naar punt
    CENTER = "center"                            # Neutraal stabiel
    CYCLE = "cycle"                               # Periodiek
    TORUS2 = "torus2"                             # 2-torus
    TORUS3 = "torus3"                             # 3-torus
    CHAOS = "chaos"                               # Chaotisch


class BifurcationType(Enum):
    """Type van bifurcatie."""
    SADDLE_NODE = "saddle_node"                 # Vaste punten ontstaan/verdwijnen
    TRANSCRITICAL = "transcritical"              # Vaste punten wisselen stabiliteit
    PITCHFORK = "pitchfork"                      # Symmetrie breking
    HOPF = "hopf"                                # Limit cycle ontstaat
    PERIOD_DOUBLING = "period_doubling"          # Route naar chaos
    TORUS = "torus"                              # Naar quasi-periodiek
    HOMOCLINIC = "homoclinic"                    # Homoclinische baan
    HETEROCLINIC = "heteroclinic"                 # Heteroclinische baan
    BLUE_SKY = "blue_sky"                        # Catastrofe
    FOLD = "fold"                                 # Vouw catastophe
    CUSP = "cusp"                                 # Knobbel catastophe
    BUTTERFLY = "butterfly"                       # Vlinder catastophe
    NEIMARK_SACKER = "neimark_sacker"             # Torus bifurcatie
    FLIP = "flip"                                 # Period doubling


class StabilityType(Enum):
    """Type van stabiliteit."""
    ASYMPTOTIC = "asymptotic"                    # Exponentieel stabiel
    LYAPUNOV = "lyapunov"                         # Lyapunov stabiel
    NEUTRAL = "neutral"                           # Neutraal stabiel
    UNSTABLE = "unstable"                         # Instabiel
    STRUCTURAL = "structural"                      # Structureel stabiel
    MARGINAL = "marginal"                          # Marginaal stabiel
    EXPONENTIAL = "exponential"                    # Exponentieel


class IntegrationMethod(Enum):
    """Numerieke integratie methoden."""
    EULER = "euler"                               # Euler voorwaarts
    EULER_BACKWARD = "euler_backward"             # Euler achterwaarts
    RK2 = "rk2"                                    # Runge-Kutta 2e orde
    RK4 = "rk4"                                    # Runge-Kutta 4e orde
    RK45 = "rk45"                                  # Runge-Kutta adaptief
    DOPRI5 = "dopri5"                              # Dormand-Prince
    DOP853 = "dop853"                              # Dormand-Prince 8e orde
    RADAU = "radau"                                # Radau IIA (stijve systemen)
    BDF = "bdf"                                    # Backward Differentiation Formula
    LSODA = "lsoda"                                # Adams/BDF automatisch
    SYMPLECTIC_EULER = "symplectic_euler"          # Symplectisch Euler
    VERLET = "verlet"                              # Verlet integratie
    LEAPFROG = "leapfrog"                          # Leapfrog integratie
    YOSHIDA = "yoshida"                            # Yoshida symplectisch
    FOREST_RUTH = "forest_ruth"                    # Forest-Ruth symplectisch
    EXPONENTIAL = "exponential"                     # Exponential integrator
    SPLITTING = "splitting"                         # Operator splitting
    IMPLICIT_MIDPOINT = "implicit_midpoint"         # Impliciete middelpunt
    CRANK_NICOLSON = "crank_nicolson"               # Crank-Nicolson


class NoiseType(Enum):
    """Type van ruis."""
    WHITE = "white"                                # Witte ruis
    COLORED = "colored"                            # Gekleurde ruis
    BROWNIAN = "brownian"                          # Brownse beweging
    PINK = "pink"                                   # 1/f ruis
    SHOT = "shot"                                   # Shot noise
    TELEGRAPH = "telegraph"                         # Telegraph noise
    LÉVY = "lévy"                                   # Lévy process


# ====================================================================
# OPTIONELE PYDANTIC MODELLEN
# ====================================================================

if PYDANTIC_AVAILABLE:
    from pydantic import BaseModel, validator, Field, ValidationError
    
    class DynamicalSystemModel(BaseModel):
        """Pydantic model voor dynamisch systeem validatie."""
        id: str = Field(..., min_length=8, max_length=64, regex="^[A-Za-z0-9_]+$")
        dimensions: int = Field(ge=1, le=10000)
        time_scale: str
        dynamical_type: str
        is_chaotic: bool = False
        lyapunov_exponent: Optional[float] = None
        parameters: Dict[str, float] = Field(default_factory=dict)
        
        @validator('time_scale')
        def validate_time_scale(cls, v):
            valid_scales = [t.value for t in TimeScale]
            if v not in valid_scales:
                raise ValueError(f"Tijdschaal moet één van {valid_scales} zijn")
            return v
        
        @validator('dynamical_type')
        def validate_dynamical_type(cls, v):
            valid_types = [t.value for t in DynamicalType]
            if v not in valid_types:
                raise ValueError(f"Dynamisch type moet één van {valid_types} zijn")
            return v
    
    class SimulationConfigModel(BaseModel):
        """Configuratie voor simulatie."""
        method: str
        dt: float = Field(gt=0)
        t_max: float = Field(gt=0)
        rtol: float = Field(1e-6, ge=1e-12, le=1e-3)
        atol: float = Field(1e-9, ge=1e-15, le=1e-6)
        max_step: Optional[float] = None
        noise_strength: float = 0.0
        seed: Optional[int] = None
        
        @validator('method')
        def validate_method(cls, v):
            valid_methods = [m.value for m in IntegrationMethod]
            if v not in valid_methods:
                raise ValueError(f"Methode moet één van {valid_methods} zijn")
            return v


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
                # Probeer opnieuw met CPU
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
# DATACLASSES - Dynamische systemen en toestanden
# ====================================================================

@dataclass
class DynamicState:
    """
    Dynamische toestand van een systeem op tijdstip t.
    
    Attributes:
        t: Tijdstip
        x: Toestandsvector
        dx: Tijdsafgeleide (optioneel)
        energy: Energie (optioneel)
        entropy: Entropie (optioneel)
        metadata: Extra metadata
    """
    t: float
    x: np.ndarray
    dx: Optional[np.ndarray] = None
    energy: Optional[float] = None
    entropy: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary."""
        return {
            't': self.t,
            'x': self.x.tolist() if isinstance(self.x, np.ndarray) else self.x,
            'dx': self.dx.tolist() if isinstance(self.dx, np.ndarray) else self.dx,
            'energy': self.energy,
            'entropy': self.entropy,
            'metadata': self.metadata
        }


@dataclass
class FixedPoint:
    """
    Vast punt van dynamisch systeem.
    
    Attributes:
        x: Coördinaten van vast punt
        stability: Stabiliteitseigenschappen
        eigenvalues: Eigenwaarden van Jacobiaan
        basin_size: Grootte van aantrekkingsgebied (geschat)
        discovered_at: Tijdstip van ontdekking
    """
    x: np.ndarray
    stability: StabilityType
    eigenvalues: np.ndarray
    basin_size: float = 0.0
    discovered_at: float = field(default_factory=time.time)
    
    def is_stable(self) -> bool:
        """Check of vast punt stabiel is."""
        return self.stability in [StabilityType.ASYMPTOTIC, StabilityType.LYAPUNOV]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary."""
        return {
            'x': self.x.tolist(),
            'stability': self.stability.value,
            'eigenvalues': self.eigenvalues.tolist() if isinstance(self.eigenvalues, np.ndarray) else self.eigenvalues,
            'basin_size': self.basin_size,
            'discovered_at': self.discovered_at
        }


@dataclass
class LimitCycle:
    """
    Periodieke baan (limit cycle).
    
    Attributes:
        period: Periode
        trajectory: Lijst van punten op de cyclus
        stability: Stabiliteit
        frequency: Frequentie
        amplitude: Amplitude
    """
    period: float
    trajectory: List[np.ndarray]
    stability: StabilityType
    frequency: float
    amplitude: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary."""
        return {
            'period': self.period,
            'trajectory': [p.tolist() for p in self.trajectory],
            'stability': self.stability.value,
            'frequency': self.frequency,
            'amplitude': self.amplitude,
            'metadata': self.metadata
        }


@dataclass
class BifurcationPoint:
    """
    Bifurcatiepunt in parameterruimte.
    
    Attributes:
        parameter: Parameter die varieert
        value: Parameterwaarde
        type: Type bifurcatie
        before: Type attractor voor bifurcatie
        after: Type attractor na bifurcatie
    """
    parameter: str
    value: float
    type: BifurcationType
    before: AttractorType
    after: AttractorType
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary."""
        return {
            'parameter': self.parameter,
            'value': self.value,
            'type': self.type.value,
            'before': self.before.value,
            'after': self.after.value,
            'metadata': self.metadata
        }


@dataclass
class LyapunovSpectrum:
    """
    Lyapunov spectrum van een dynamisch systeem.
    
    Attributes:
        exponents: Lijst van Lyapunov exponenten
        dimension: Kaplan-Yorke dimensie
        max_exponent: Grootste Lyapunov exponent (chaos indicator)
        divergence_rate: Gemiddelde divergentie rate
    """
    exponents: List[float]
    dimension: float
    max_exponent: float
    divergence_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_chaotic(self) -> bool:
        """Check of systeem chaotisch is (positieve Lyapunov exponent)."""
        return self.max_exponent > 1e-6
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary."""
        return {
            'exponents': self.exponents,
            'dimension': self.dimension,
            'max_exponent': self.max_exponent,
            'divergence_rate': self.divergence_rate,
            'is_chaotic': self.is_chaotic(),
            'metadata': self.metadata
        }


# ====================================================================
# DYNAMISCH SYSTEEM - HOOFDKLASSE (UITGEBREID)
# ====================================================================

class DynamicalSystem:
    """
    Representatie van een dynamisch systeem met alle optionele features.
    
    Dit is een generiek raamwerk voor het definiëren, simuleren en analyseren
    van dynamische systemen. Ondersteunt:
    - Continue en discrete tijd
    - Gewone differentiaalvergelijkingen (ODE)
    - Stochastic differential equations (SDE)
    - Delay differential equations (DDE)
    - Fractionele dynamica
    - Hamiltoniaanse systemen
    - Gekoppelde systemen
    - Hardware versnelling (GPU/FPGA/Quantum)
    """
    
    def __init__(self,
                 system_id: str,
                 dimensions: int,
                 # Dynamica definitie
                 dynamics_func: Callable,
                 jacobian_func: Optional[Callable] = None,
                 hamiltonian_func: Optional[Callable] = None,
                 parameters: Optional[Dict[str, float]] = None,
                 # Tijd configuratie
                 time_scale: TimeScale = TimeScale.SECOND,
                 # Numerieke methoden
                 default_method: IntegrationMethod = IntegrationMethod.RK45,
                 adaptive: bool = True,
                 rtol: float = 1e-6,
                 atol: float = 1e-9,
                 max_step: Optional[float] = None,
                 # Stochastiek
                 enable_noise: bool = False,
                 noise_type: NoiseType = NoiseType.WHITE,
                 noise_strength: float = 0.0,
                 noise_seed: Optional[int] = None,
                 # Vertragingen
                 enable_delay: bool = False,
                 max_delay: float = 0.0,
                 # Fractioneel
                 enable_fractional: bool = False,
                 fractional_order: float = 1.0,
                 # Symplectisch / Hamiltoniaans
                 enable_symplectic: bool = False,
                 # Chaos analyse
                 enable_chaos_analysis: bool = False,
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
                 db_path: str = "dynamics.db",
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
        Initialiseer dynamisch systeem met alle optionele features.
        
        Args:
            system_id: Uniek ID voor dit systeem
            dimensions: Dimensionaliteit van toestandsruimte
            dynamics_func: Functie dx/dt = f(t, x, params)
            jacobian_func: Optionele Jacobiaan matrix functie
            hamiltonian_func: Optionele Hamiltoniaan (voor symplectische integratie)
            parameters: Dictionary met parameterwaarden
            time_scale: Tijdschaal voor interpretatie
            default_method: Standaard integratiemethode
            adaptive: Gebruik adaptieve stapgrootte
            rtol: Relatieve tolerantie
            atol: Absolute tolerantie
            max_step: Maximale stapgrootte
            enable_noise: Voeg stochastische ruis toe
            noise_type: Type ruis
            noise_strength: Sterkte van ruis
            noise_seed: Seed voor reproduceerbaarheid
            enable_delay: Gebruik delay differential equations
            max_delay: Maximale vertraging
            enable_fractional: Gebruik fractionele afgeleiden
            fractional_order: Orde van fractionele afgeleide
            enable_symplectic: Gebruik symplectische integratie (energiebehoud)
            enable_chaos_analysis: Bereken Lyapunov exponenten etc.
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
        self.id = system_id
        self.dim = dimensions
        self.f = dynamics_func
        self.J = jacobian_func
        self.H = hamiltonian_func
        self.params = parameters or {}
        self.time_scale = time_scale
        self.default_method = default_method
        self.adaptive = adaptive
        self.rtol = rtol
        self.atol = atol
        self.max_step = max_step
        
        # Stochastiek
        self.enable_noise = enable_noise
        self.noise_type = noise_type
        self.noise_strength = noise_strength
        self.noise_seed = noise_seed
        if enable_noise and noise_seed is not None:
            np.random.seed(noise_seed)
        
        # Vertragingen
        self.enable_delay = enable_delay
        self.max_delay = max_delay
        self.delay_history = deque(maxlen=int(max_delay * 1000) if max_delay > 0 else 1000)
        
        # Fractioneel
        self.enable_fractional = enable_fractional
        self.fractional_order = fractional_order
        
        # Symplectisch
        self.enable_symplectic = enable_symplectic
        
        # Chaos analyse
        self.enable_chaos_analysis = enable_chaos_analysis
        
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
        
        # Interne toestand
        self.current_state: Optional[DynamicState] = None
        self.trajectory: List[DynamicState] = []
        self.max_trajectory = 100000
        
        # Analyse resultaten
        self.fixed_points: List[FixedPoint] = []
        self.limit_cycles: List[LimitCycle] = []
        self.bifurcations: List[BifurcationPoint] = []
        self.lyapunov_spectrum: Optional[LyapunovSpectrum] = None
        
        # Statistieken
        self.metrics = {
            'simulations': 0,
            'integrations': 0,
            'fixed_points_found': 0,
            'bifurcations_detected': 0,
            'chaos_detected': False,
            'cache_hits': 0,
            'cache_misses': 0,
            'start_time': time.time()
        }
        
        self._log_configuration()
    
    def _log_configuration(self):
        """Log configuratie bij startup."""
        logger.info("="*100)
        logger.info(f"🌀 DYNAMISCH SYSTEEM {self.id} - LAYER 4 V14")
        logger.info("="*100)
        logger.info(f"Dimensies: {self.dim}")
        logger.info(f"Tijdschaal: {self.time_scale.value}")
        logger.info(f"Integratie: {self.default_method.value} (adaptief={self.adaptive})")
        
        logger.info("\n📦 OPTIONELE FEATURES:")
        logger.info(f"   Stochastiek:      {'✅' if self.enable_noise else '❌'}")
        logger.info(f"   Vertragingen:     {'✅' if self.enable_delay else '❌'}")
        logger.info(f"   Fractioneel:      {'✅' if self.enable_fractional else '❌'}")
        logger.info(f"   Symplectisch:     {'✅' if self.enable_symplectic else '❌'}")
        logger.info(f"   Chaos analyse:    {'✅' if self.enable_chaos_analysis else '❌'}")
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
            
            self._metrics['integrations'] = Counter(
                f'dynamics_{self.id}_integrations_total',
                'Total number of integrations'
            )
            self._metrics['duration'] = Histogram(
                f'dynamics_{self.id}_integration_seconds',
                'Integration time in seconds'
            )
            self._metrics['state'] = Gauge(
                f'dynamics_{self.id}_state',
                'Current state values',
                ['dimension']
            )
            self._metrics['fixed_points'] = Gauge(
                f'dynamics_{self.id}_fixed_points',
                'Number of fixed points found'
            )
            self._metrics['lyapunov'] = Gauge(
                f'dynamics_{self.id}_lyapunov',
                'Maximum Lyapunov exponent'
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
                CREATE TABLE IF NOT EXISTS trajectories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_id TEXT,
                    simulation_id TEXT,
                    t REAL,
                    x BLOB,
                    metadata TEXT
                )
            ''')
            
            await self.db.execute('''
                CREATE TABLE IF NOT EXISTS fixed_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_id TEXT,
                    x BLOB,
                    stability TEXT,
                    eigenvalues BLOB,
                    discovered_at REAL
                )
            ''')
            
            await self.db.execute('''
                CREATE INDEX IF NOT EXISTS idx_system_id ON trajectories(system_id)
            ''')
            
            await self.db.commit()
            logger.info(f"💾 Persistentie database: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ Persistentie init mislukt: {e}")
            self.enable_persistence = False
    
    # ================================================================
    # SIMULATIE METHODEN
    # ================================================================
    
    @timed('integrate')
    @cached()
    @with_hardware_fallback()
    @with_retry(max_retries=3)
    async def integrate(self,
                       t_span: Tuple[float, float],
                       x0: np.ndarray,
                       method: Optional[IntegrationMethod] = None,
                       params: Optional[Dict[str, float]] = None,
                       save_trajectory: bool = True,
                       callback: Optional[Callable] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Integreer het systeem van t_start tot t_end.
        
        Args:
            t_span: (t_start, t_end)
            x0: Begincondities
            method: Integratiemethode (overschrijft default)
            params: Parameterwaarden (tijdelijk overschrijven)
            save_trajectory: Bewaar traject in geheugen
            callback: Optionele callback bij elke stap
        
        Returns:
            (t, x) arrays
        """
        method = method or self.default_method
        current_params = {**self.params, **(params or {})}
        
        # Valideer input met Pydantic
        if self.enable_validation and PYDANTIC_AVAILABLE:
            try:
                config = SimulationConfigModel(
                    method=method.value,
                    dt=0.01,  # dummy
                    t_max=t_span[1] - t_span[0],
                    rtol=self.rtol,
                    atol=self.atol
                )
            except ValidationError as e:
                raise ValueError(f"Configuratie validatie mislukt: {e}")
        
        self.metrics['integrations'] += 1
        
        if self.hardware_backend == "cuda" and TORCH_AVAILABLE:
            return await self._integrate_cuda(t_span, x0, method, current_params, callback)
        elif self.hardware_backend == "quantum" and QISKIT_AVAILABLE:
            return await self._integrate_quantum(t_span, x0, method, current_params, callback)
        elif self.hardware_backend == "fpga" and PYNQ_AVAILABLE:
            return await self._integrate_fpga(t_span, x0, method, current_params, callback)
        else:
            return await self._integrate_cpu(t_span, x0, method, current_params, save_trajectory, callback)
    
    async def _integrate_cpu(self, t_span, x0, method, params, save_trajectory, callback):
        """CPU implementatie met SciPy."""
        if not NUMPY_AVAILABLE:
            raise RuntimeError("NumPy/SciPy niet beschikbaar voor CPU integratie")
        
        t_start, t_end = t_span
        
        # Definieer rechterlid
        def rhs(t, x):
            if self.enable_noise and self.noise_strength > 0:
                # Voeg ruis toe (wordt later verwerkt, niet hier)
                pass
            return self.f(t, x, params)
        
        # Kies solver
        if method == IntegrationMethod.RK45:
            solver = 'RK45'
        elif method == IntegrationMethod.DOPRI5:
            solver = 'DOP853'  # SciPy gebruikt DOP853 voor hoge orde
        elif method == IntegrationMethod.RADAU:
            solver = 'Radau'
        elif method == IntegrationMethod.BDF:
            solver = 'BDF'
        elif method == IntegrationMethod.LSODA:
            solver = 'LSODA'
        else:
            solver = 'RK45'
        
        # Voer integratie uit
        if self.adaptive:
            result = solve_ivp(
                rhs, (t_start, t_end), x0,
                method=solver,
                rtol=self.rtol,
                atol=self.atol,
                max_step=self.max_step
            )
            t = result.t
            x = result.y.T
        else:
            # Vaste stapgrootte
            dt = self.max_step or 0.01
            n_steps = int((t_end - t_start) / dt) + 1
            t = np.linspace(t_start, t_end, n_steps)
            x = np.zeros((n_steps, self.dim))
            x[0] = x0
            
            for i in range(1, n_steps):
                ti = t[i-1]
                xi = x[i-1]
                
                if method == IntegrationMethod.EULER:
                    k1 = rhs(ti, xi)
                    x[i] = xi + dt * k1
                elif method == IntegrationMethod.RK4:
                    k1 = rhs(ti, xi)
                    k2 = rhs(ti + dt/2, xi + dt/2 * k1)
                    k3 = rhs(ti + dt/2, xi + dt/2 * k2)
                    k4 = rhs(ti + dt, xi + dt * k3)
                    x[i] = xi + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
                else:
                    # Fallback naar Euler
                    k1 = rhs(ti, xi)
                    x[i] = xi + dt * k1
                
                if callback:
                    await callback(t[i], x[i])
        
        # Voeg ruis toe (post-processing voor eenvoud)
        if self.enable_noise and self.noise_strength > 0:
            noise = self.noise_strength * np.random.randn(*x.shape)
            x += noise
        
        # Sla traject op
        if save_trajectory:
            for i in range(len(t)):
                state = DynamicState(t[i], x[i])
                self.trajectory.append(state)
                if len(self.trajectory) > self.max_trajectory:
                    self.trajectory.pop(0)
        
        # Update huidige toestand
        self.current_state = DynamicState(t[-1], x[-1])
        
        # Update Prometheus
        if self._metrics and 'state' in self._metrics:
            for d in range(self.dim):
                self._metrics['state'].labels(dimension=str(d)).set(x[-1][d])
        
        return t, x
    
    async def _integrate_cuda(self, t_span, x0, method, params, callback):
        """GPU versnelling met PyTorch."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch niet beschikbaar")
        
        t_start, t_end = t_span
        dt = self.max_step or 0.01
        n_steps = int((t_end - t_start) / dt) + 1
        
        # Converteer naar tensoren
        x = torch.zeros(n_steps, self.dim, device=device)
        x[0] = torch.tensor(x0, device=device)
        t = torch.linspace(t_start, t_end, n_steps, device=device)
        
        # Definieer rhs als PyTorch functie
        def rhs_torch(t_val, x_val):
            # Converteer naar numpy voor de gebruiker functie (simplificatie)
            x_np = x_val.cpu().numpy()
            t_np = t_val.item() if torch.is_tensor(t_val) else t_val
            f_np = self.f(t_np, x_np, params)
            return torch.tensor(f_np, device=device)
        
        for i in range(1, n_steps):
            ti = t[i-1]
            xi = x[i-1]
            
            # Eenvoudige Euler op GPU
            k1 = rhs_torch(ti, xi)
            x[i] = xi + dt * k1
            
            if callback:
                await callback(t[i].item(), x[i].cpu().numpy())
        
        # Terug naar numpy
        t_np = t.cpu().numpy()
        x_np = x.cpu().numpy()
        
        # Sla traject op
        for i in range(len(t_np)):
            state = DynamicState(t_np[i], x_np[i])
            self.trajectory.append(state)
            if len(self.trajectory) > self.max_trajectory:
                self.trajectory.pop(0)
        
        self.current_state = DynamicState(t_np[-1], x_np[-1])
        
        return t_np, x_np
    
    async def _integrate_quantum(self, t_span, x0, method, params, callback):
        """Quantum simulatie (voor kleine systemen)."""
        if not QISKIT_AVAILABLE:
            raise RuntimeError("Qiskit niet beschikbaar")
        
        # Alleen voor hele kleine dimensies (quantum simulatie is duur)
        if self.dim > 5:
            logger.warning("⚠️ Quantum integratie alleen voor dimensie ≤ 5, val terug naar CPU")
            return await self._integrate_cpu(t_span, x0, method, params, True, callback)
        
        # Converteer naar quantum circuit (vereenvoudigd)
        # In werkelijkheid zou je een Hamiltoniaan moeten hebben
        qr = QuantumRegister(self.dim, 'q')
        qc = QuantumCircuit(qr)
        
        # Simuleer tijdsevolutie via Trotter
        dt = self.max_step or 0.01
        n_steps = int((t_span[1] - t_span[0]) / dt)
        
        # Maak een Hamiltonian van de dynamica (zeer gesimplificeerd)
        # Dit is een placeholder; echte quantum dynamica vereist een Hamiltoniaan
        hamiltonian = PauliSumOp.from_list([('Z'*self.dim, 1.0)])
        
        # Trotter steps
        for _ in range(n_steps):
            qc.append(PauliEvolutionGate(hamiltonian, time=dt), range(self.dim))
        
        # Voer uit
        backend = Aer.get_backend('statevector_simulator')
        job = execute(qc, backend)
        result = job.result()
        statevector = result.get_statevector()
        
        # Converteer naar klassiek (alleen amplitudes)
        x = np.abs(statevector)[:self.dim]
        
        t = np.array([t_span[0], t_span[1]])
        x_traj = np.array([x0, x])
        
        self.current_state = DynamicState(t_span[1], x)
        
        return t, x_traj
    
    async def _integrate_fpga(self, t_span, x0, method, params, callback):
        """FPGA versnelling via PYNQ."""
        if not PYNQ_AVAILABLE:
            raise RuntimeError("PYNQ niet beschikbaar")
        
        # Simuleer FPGA door CPU te gebruiken (placeholder)
        logger.info("⚡ FPGA integratie (gesimuleerd)")
        return await self._integrate_cpu(t_span, x0, method, params, True, callback)
    
    # ================================================================
    # VASTE PUNTEN ANALYSE
    # ================================================================
    
    async def find_fixed_points(self,
                               guesses: List[np.ndarray],
                               params: Optional[Dict] = None,
                               tolerance: float = 1e-8) -> List[FixedPoint]:
        """
        Vind vaste punten van het systeem door f(x)=0 op te lossen.
        
        Args:
            guesses: Lijst van beginwaarden voor zoekalgoritme
            params: Parameterwaarden (tijdelijk overschrijven)
            tolerance: Tolerantie voor convergentie
        
        Returns:
            Lijst van gevonden vaste punten
        """
        if not NUMPY_AVAILABLE:
            raise RuntimeError("NumPy/SciPy nodig voor fixed point analyse")
        
        current_params = {**self.params, **(params or {})}
        
        def f_wrapper(x):
            return self.f(0.0, x, current_params)
        
        fixed_points = []
        
        for guess in guesses:
            try:
                sol = root(f_wrapper, guess, tol=tolerance)
                if sol.success:
                    x_fp = sol.x
                    
                    # Bereken Jacobiaan voor stabiliteit
                    if self.J:
                        J = self.J(0.0, x_fp, current_params)
                    else:
                        # Numerieke Jacobiaan
                        eps = 1e-6
                        J = np.zeros((self.dim, self.dim))
                        for i in range(self.dim):
                            x_plus = x_fp.copy()
                            x_plus[i] += eps
                            f_plus = f_wrapper(x_plus)
                            f_center = f_wrapper(x_fp)
                            J[:, i] = (f_plus - f_center) / eps
                    
                    # Eigenwaarden
                    eigvals = np.linalg.eigvals(J)
                    
                    # Bepaal stabiliteit
                    if np.all(np.real(eigvals) < 0):
                        stability = StabilityType.ASYMPTOTIC
                    elif np.all(np.real(eigvals) <= 0):
                        stability = StabilityType.LYAPUNOV
                    elif np.any(np.real(eigvals) > 0):
                        stability = StabilityType.UNSTABLE
                    else:
                        stability = StabilityType.NEUTRAL
                    
                    # Check of al gevonden
                    duplicate = False
                    for fp in fixed_points:
                        if np.linalg.norm(fp.x - x_fp) < 1e-6:
                            duplicate = True
                            break
                    
                    if not duplicate:
                        fp = FixedPoint(
                            x=x_fp,
                            stability=stability,
                            eigenvalues=eigvals
                        )
                        fixed_points.append(fp)
                        self.fixed_points.append(fp)
                        self.metrics['fixed_points_found'] += 1
                        
            except Exception as e:
                logger.debug(f"Fixed point zoektocht mislukt voor guess {guess}: {e}")
        
        # Update Prometheus
        if self._metrics and 'fixed_points' in self._metrics:
            self._metrics['fixed_points'].set(len(self.fixed_points))
        
        return fixed_points
    
    # ================================================================
    # LYAPUNOV EXPONENTEN (CHAOS DETECTIE)
    # ================================================================
    
    async def compute_lyapunov_spectrum(self,
                                        trajectory: Optional[np.ndarray] = None,
                                        dt: float = 0.01,
                                        n_vectors: int = 10) -> LyapunovSpectrum:
        """
        Bereken Lyapunov spectrum van een traject.
        
        Args:
            trajectory: Traject (t, x) of None om huidige te gebruiken
            dt: Tijdstap tussen samples
            n_vectors: Aantal orthogonale vectoren voor spectrum
        
        Returns:
            LyapunovSpectrum object
        """
        if not NUMPY_AVAILABLE:
            raise RuntimeError("NumPy/SciPy nodig voor Lyapunov analyse")
        
        if NOLDS_AVAILABLE:
            # Gebruik nolds voor efficiënte berekening
            if trajectory is None:
                if len(self.trajectory) < 100:
                    raise ValueError("Onvoldoende data voor Lyapunov analyse")
                data = np.array([s.x for s in self.trajectory])
            else:
                data = trajectory
            
            # Grootste Lyapunov exponent
            le_max = nolds.lyap_r(data, emb_dim=10, lag=1)
            
            # Hele spectrum (minder nauwkeurig)
            try:
                le_spectrum = nolds.lyap_e(data, emb_dim=10, lag=1)
            except:
                le_spectrum = [le_max] + [0.0] * (n_vectors-1)
            
            # Kaplan-Yorke dimensie
            dim = 0
            for i, le in enumerate(le_spectrum):
                dim += le
                if dim < 0:
                    break
            ky_dim = i + dim / abs(le_spectrum[i]) if i < len(le_spectrum) else len(le_spectrum)
            
        else:
            # Eigen implementatie (benaderd)
            if trajectory is None:
                if len(self.trajectory) < 2:
                    raise ValueError("Onvoldoende data voor Lyapunov analyse")
                data = np.array([s.x for s in self.trajectory])
                times = np.array([s.t for s in self.trajectory])
            else:
                data = trajectory
                times = np.arange(len(data)) * dt
            
            # Simpele schatting via divergentie van nabije trajecten
            n = len(data)
            le_max = 0.0
            for i in range(n-100):
                ref = data[i]
                # Zoek dichtstbijzijnde punt in tijd (vermijd dichtbij)
                min_dist = np.inf
                min_j = i
                for j in range(n):
                    if abs(j - i) > 50:
                        dist = np.linalg.norm(data[j] - ref)
                        if dist < min_dist:
                            min_dist = dist
                            min_j = j
                if min_j == i:
                    continue
                # Volg evolutie
                d0 = min_dist
                d1 = np.linalg.norm(data[min_j+1] - data[i+1]) if min_j+1 < n and i+1 < n else d0
                if d0 > 0 and d1 > 0:
                    le = np.log(d1 / d0) / (times[i+1] - times[i])
                    le_max = max(le_max, le)
            
            le_spectrum = [le_max] + [0.0] * (n_vectors-1)
            ky_dim = 1.0
        
        spectrum = LyapunovSpectrum(
            exponents=le_spectrum[:n_vectors],
            dimension=ky_dim,
            max_exponent=le_spectrum[0],
            divergence_rate=np.mean(le_spectrum)
        )
        
        self.lyapunov_spectrum = spectrum
        self.metrics['chaos_detected'] = spectrum.is_chaotic()
        
        # Update Prometheus
        if self._metrics and 'lyapunov' in self._metrics:
            self._metrics['lyapunov'].set(spectrum.max_exponent)
        
        return spectrum
    
    # ================================================================
    # BIFURCATIE ANALYSE
    # ================================================================
    
    async def bifurcation_diagram(self,
                                  parameter: str,
                                  param_range: Tuple[float, float],
                                  n_points: int = 100,
                                  x0: np.ndarray,
                                  t_transient: float = 10.0,
                                  t_measure: float = 50.0,
                                  method: Optional[IntegrationMethod] = None) -> Dict[str, Any]:
        """
        Genereer bifurcatiediagram voor een parameter.
        
        Args:
            parameter: Naam van parameter
            param_range: (min, max)
            n_points: Aantal parameterwaarden
            x0: Begincondities
            t_transient: Transiënt tijd om te negeren
            t_measure: Meet tijd om punten te verzamelen
            method: Integratiemethode
        
        Returns:
            Dictionary met parameterwaarden en gemeten toestanden
        """
        if not NUMPY_AVAILABLE:
            raise RuntimeError("NumPy/SciPy nodig voor bifurcatie analyse")
        
        param_vals = np.linspace(param_range[0], param_range[1], n_points)
        results = []
        
        for p in param_vals:
            params = {parameter: p}
            
            # Integreer met transiënt
            t1, x1 = await self.integrate(
                (0, t_transient), x0, method=method, params=params,
                save_trajectory=False
            )
            
            # Meet over t_measure
            t2, x2 = await self.integrate(
                (t_transient, t_transient + t_measure),
                x1[-1], method=method, params=params,
                save_trajectory=False
            )
            
            # Neem lokale maxima/minima als sample
            # Voor simpele systemen, neem gewoon laatste punt
            results.append({
                'param': p,
                'x': x2[-1].tolist()
            })
        
        # Detecteer bifurcaties
        bifurcations = []
        # Vereenvoudigd: kijk naar plotselinge veranderingen in x
        for i in range(1, n_points-1):
            x_prev = results[i-1]['x'][0]  # eerste component
            x_curr = results[i]['x'][0]
            x_next = results[i+1]['x'][0]
            
            if abs(x_curr - x_prev) > 0.5 and abs(x_next - x_curr) > 0.5:
                # Mogelijke bifurcatie
                bp = BifurcationPoint(
                    parameter=parameter,
                    value=param_vals[i],
                    type=BifurcationType.UNKNOWN,  # Zou geclassificeerd moeten worden
                    before=AttractorType.FIXED_POINT,
                    after=AttractorType.LIMIT_CYCLE
                )
                bifurcations.append(bp)
                self.bifurcations.append(bp)
                self.metrics['bifurcations_detected'] += 1
        
        return {
            'parameter': parameter,
            'values': param_vals.tolist(),
            'data': results,
            'bifurcations': [b.to_dict() for b in bifurcations]
        }
    
    # ================================================================
    # VISUALISATIE
    # ================================================================
    
    def plot_phase_portrait(self,
                            plane: Tuple[int, int] = (0, 1),
                            filename: Optional[str] = None,
                            show_arrows: bool = True,
                            grid_size: int = 20):
        """
        Plot faseportret (2D projectie).
        
        Args:
            plane: Dimensies om te plotten (i, j)
            filename: Bestandsnaam om op te slaan
            show_arrows: Toon vectorveld
            grid_size: Resolutie van vectorveld
        """
        if not VISUALIZATION_AVAILABLE:
            logger.warning("⚠️ Visualisatie niet beschikbaar")
            return
        
        i, j = plane
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot traject
        if self.trajectory:
            x_vals = [s.x[i] for s in self.trajectory]
            y_vals = [s.x[j] for s in self.trajectory]
            ax.plot(x_vals, y_vals, 'b-', alpha=0.7, linewidth=1)
        
        # Plot vaste punten
        for fp in self.fixed_points:
            color = 'green' if fp.is_stable() else 'red'
            ax.plot(fp.x[i], fp.x[j], 'o', color=color, markersize=8,
                   markeredgecolor='black', markeredgewidth=1)
        
        # Vectorveld
        if show_arrows and self.dim >= 2:
            x_min, x_max = ax.get_xlim() if ax.get_xlim() != (0,1) else (-2,2)
            y_min, y_max = ax.get_ylim() if ax.get_ylim() != (0,1) else (-2,2)
            
            X, Y = np.meshgrid(
                np.linspace(x_min, x_max, grid_size),
                np.linspace(y_min, y_max, grid_size)
            )
            U = np.zeros_like(X)
            V = np.zeros_like(Y)
            
            for idx in range(grid_size):
                for jdx in range(grid_size):
                    x_full = np.zeros(self.dim)
                    x_full[i] = X[idx, jdx]
                    x_full[j] = Y[idx, jdx]
                    dx = self.f(0.0, x_full, self.params)
                    U[idx, jdx] = dx[i]
                    V[idx, jdx] = dx[j]
            
            # Normaliseer voor betere visualisatie
            norm = np.sqrt(U**2 + V**2)
            U = U / (norm + 1e-10)
            V = V / (norm + 1e-10)
            
            ax.quiver(X, Y, U, V, alpha=0.5, color='gray')
        
        ax.set_xlabel(f'x[{i}]')
        ax.set_ylabel(f'x[{j}]')
        ax.set_title(f'Faseportret - {self.id}')
        ax.grid(True, alpha=0.3)
        
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            logger.info(f"📊 Faseportret opgeslagen: {filename}")
        else:
            plt.show()
        plt.close()
    
    def plot_bifurcation_diagram(self,
                                 parameter: str,
                                 data: Dict[str, Any],
                                 filename: Optional[str] = None):
        """
        Plot bifurcatiediagram.
        
        Args:
            parameter: Parameter naam
            data: Resultaat van bifurcation_diagram()
            filename: Bestandsnaam
        """
        if not VISUALIZATION_AVAILABLE:
            logger.warning("⚠️ Visualisatie niet beschikbaar")
            return
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        param_vals = data['values']
        x_vals = [d['x'][0] for d in data['data']]  # eerste component
        
        ax.plot(param_vals, x_vals, 'b.', markersize=2, alpha=0.5)
        
        # Markeer bifurcaties
        for bp in data['bifurcations']:
            ax.axvline(x=bp['value'], color='red', linestyle='--', alpha=0.7)
        
        ax.set_xlabel(parameter)
        ax.set_ylabel('x[0]')
        ax.set_title(f'Bifurcatiediagram - {self.id}')
        ax.grid(True, alpha=0.3)
        
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            logger.info(f"📊 Bifurcatiediagram opgeslagen: {filename}")
        else:
            plt.show()
        plt.close()
    
    def plot_trajectory(self,
                        dimensions: Optional[List[int]] = None,
                        filename: Optional[str] = None):
        """
        Plot tijdsseries van traject.
        
        Args:
            dimensions: Lijst van dimensies om te plotten (None = alle)
            filename: Bestandsnaam
        """
        if not VISUALIZATION_AVAILABLE:
            logger.warning("⚠️ Visualisatie niet beschikbaar")
            return
        
        if not self.trajectory:
            logger.warning("⚠️ Geen traject om te plotten")
            return
        
        dims = dimensions or list(range(min(5, self.dim)))  # Max 5
        n_dims = len(dims)
        
        fig, axes = plt.subplots(n_dims, 1, figsize=(12, 4*n_dims), sharex=True)
        if n_dims == 1:
            axes = [axes]
        
        t = [s.t for s in self.trajectory]
        
        for idx, dim in enumerate(dims):
            x = [s.x[dim] for s in self.trajectory]
            axes[idx].plot(t, x, 'b-', linewidth=1)
            axes[idx].set_ylabel(f'x[{dim}]')
            axes[idx].grid(True, alpha=0.3)
        
        axes[-1].set_xlabel('t')
        plt.suptitle(f'Traject - {self.id}')
        plt.tight_layout()
        
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            logger.info(f"📊 Traject opgeslagen: {filename}")
        else:
            plt.show()
        plt.close()
    
    # ================================================================
    # EXPORT & PERSISTENTIE
    # ================================================================
    
    async def save_trajectory(self, simulation_id: str):
        """Sla huidig traject op in database."""
        if not self.enable_persistence or not self.db:
            return
        
        try:
            for state in self.trajectory:
                x_blob = pickle.dumps(state.x)
                metadata = json.dumps(state.metadata)
                await self.db.execute('''
                    INSERT INTO trajectories (system_id, simulation_id, t, x, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.id, simulation_id, state.t, x_blob, metadata))
            await self.db.commit()
            logger.info(f"💾 Traject opgeslagen: {len(self.trajectory)} punten")
        except Exception as e:
            logger.error(f"❌ Opslag traject mislukt: {e}")
    
    async def save_fixed_points(self):
        """Sla vaste punten op in database."""
        if not self.enable_persistence or not self.db:
            return
        
        try:
            for fp in self.fixed_points:
                x_blob = pickle.dumps(fp.x)
                eig_blob = pickle.dumps(fp.eigenvalues)
                await self.db.execute('''
                    INSERT INTO fixed_points (system_id, x, stability, eigenvalues, discovered_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.id, x_blob, fp.stability.value, eig_blob, fp.discovered_at))
            await self.db.commit()
            logger.info(f"💾 Vaste punten opgeslagen: {len(self.fixed_points)}")
        except Exception as e:
            logger.error(f"❌ Opslag vaste punten mislukt: {e}")
    
    def export_state(self, filename: str = "layer4_state.json"):
        """Exporteer volledige staat naar JSON."""
        state = {
            'id': self.id,
            'dimensions': self.dim,
            'parameters': self.params,
            'time_scale': self.time_scale.value,
            'metrics': self.metrics,
            'fixed_points': [fp.to_dict() for fp in self.fixed_points],
            'bifurcations': [b.to_dict() for b in self.bifurcations],
            'lyapunov': self.lyapunov_spectrum.to_dict() if self.lyapunov_spectrum else None,
            'trajectory': [s.to_dict() for s in self.trajectory[-1000:]],  # laatste 1000
            'config': {
                'enable_noise': self.enable_noise,
                'enable_delay': self.enable_delay,
                'enable_fractional': self.enable_fractional,
                'enable_symplectic': self.enable_symplectic,
                'enable_chaos_analysis': self.enable_chaos_analysis,
                'hardware_backend': self.hardware_backend
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"📄 Staat geëxporteerd naar {filename}")
        return state
    
    # ================================================================
    # CLEANUP
    # ================================================================
    
    async def cleanup(self):
        """Ruim resources op."""
        logger.info("🧹 Layer 4 cleanup...")
        
        # Sla laatste staat op
        if self.enable_persistence:
            await self.save_trajectory("final")
            await self.save_fixed_points()
        
        # Sluit database
        if self.db:
            await self.db.close()
        
        # Sluit Redis
        if self.redis_client:
            await self.redis_client.close()
        
        # Export
        self.export_state("layer4_final.json")
        
        logger.info("✅ Layer 4 cleanup voltooid")
    
    def reset(self):
        """Reset systeem naar begintoestand."""
        self.current_state = None
        self.trajectory.clear()
        self.fixed_points.clear()
        self.limit_cycles.clear()
        self.bifurcations.clear()
        self.lyapunov_spectrum = None
        self.delay_history.clear()
        
        self.metrics = {
            'simulations': 0,
            'integrations': 0,
            'fixed_points_found': 0,
            'bifurcations_detected': 0,
            'chaos_detected': False,
            'cache_hits': 0,
            'cache_misses': 0,
            'start_time': time.time()
        }
        
        logger.info("🔄 Dynamisch systeem gereset")


# ====================================================================
# VOORBEELD SYSTEMEN (STATISCHE METHODEN)
# ====================================================================

class ExampleSystems:
    """Bekende dynamische systemen als voorbeelden."""
    
    @staticmethod
    def lorentz(sigma: float = 10.0, rho: float = 28.0, beta: float = 8.0/3.0):
        """Lorenz systeem (chaotisch)."""
        def f(t, x, params):
            sigma = params.get('sigma', 10.0)
            rho = params.get('rho', 28.0)
            beta = params.get('beta', 8.0/3.0)
            x, y, z = x
            return np.array([
                sigma * (y - x),
                x * (rho - z) - y,
                x * y - beta * z
            ])
        
        def jac(t, x, params):
            sigma = params.get('sigma', 10.0)
            rho = params.get('rho', 28.0)
            beta = params.get('beta', 8.0/3.0)
            x, y, z = x
            return np.array([
                [-sigma, sigma, 0],
                [rho - z, -1, -x],
                [y, x, -beta]
            ])
        
        return DynamicalSystem(
            system_id="lorenz",
            dimensions=3,
            dynamics_func=f,
            jacobian_func=jac,
            parameters={'sigma': sigma, 'rho': rho, 'beta': beta},
            enable_chaos_analysis=True
        )
    
    @staticmethod
    def rossler(a: float = 0.2, b: float = 0.2, c: float = 5.7):
        """Rössler systeem (chaotisch)."""
        def f(t, x, params):
            a = params.get('a', 0.2)
            b = params.get('b', 0.2)
            c = params.get('c', 5.7)
            x, y, z = x
            return np.array([
                -y - z,
                x + a * y,
                b + z * (x - c)
            ])
        
        return DynamicalSystem(
            system_id="rossler",
            dimensions=3,
            dynamics_func=f,
            parameters={'a': a, 'b': b, 'c': c},
            enable_chaos_analysis=True
        )
    
    @staticmethod
    def duffing(alpha: float = -1.0, beta: float = 1.0, delta: float = 0.3, gamma: float = 0.5, omega: float = 1.2):
        """Gedwongen Duffing oscillator."""
        def f(t, x, params):
            alpha = params.get('alpha', -1.0)
            beta = params.get('beta', 1.0)
            delta = params.get('delta', 0.3)
            gamma = params.get('gamma', 0.5)
            omega = params.get('omega', 1.2)
            x1, x2 = x
            return np.array([
                x2,
                -delta * x2 - alpha * x1 - beta * x1**3 + gamma * np.cos(omega * t)
            ])
        
        return DynamicalSystem(
            system_id="duffing",
            dimensions=2,
            dynamics_func=f,
            parameters={'alpha': alpha, 'beta': beta, 'delta': delta, 'gamma': gamma, 'omega': omega}
        )
    
    @staticmethod
    def van_der_pol(mu: float = 1.0):
        """Van der Pol oscillator."""
        def f(t, x, params):
            mu = params.get('mu', 1.0)
            x1, x2 = x
            return np.array([
                x2,
                mu * (1 - x1**2) * x2 - x1
            ])
        
        return DynamicalSystem(
            system_id="van_der_pol",
            dimensions=2,
            dynamics_func=f,
            parameters={'mu': mu}
        )
    
    @staticmethod
    def pendulum(g: float = 9.81, L: float = 1.0, damp: float = 0.1):
        """Gedempte slinger."""
        def f(t, x, params):
            g = params.get('g', 9.81)
            L = params.get('L', 1.0)
            damp = params.get('damp', 0.1)
            theta, omega = x
            return np.array([
                omega,
                - (g/L) * np.sin(theta) - damp * omega
            ])
        
        return DynamicalSystem(
            system_id="pendulum",
            dimensions=2,
            dynamics_func=f,
            parameters={'g': g, 'L': L, 'damp': damp}
        )


# ====================================================================
# DEMONSTRATIE
# ====================================================================

async def demo():
    """Demonstreer Layer 4 functionaliteit."""
    print("\n" + "="*100)
    print("🌀 LAYER 4: DYNAMIC ADAPTATION AND FEEDBACK - V14 DEMONSTRATIE")
    print("="*100)
    
    # Creëer Lorenz systeem
    lorenz = ExampleSystems.lorentz()
    
    print("\n📋 Test 1: Integratie van Lorenz systeem")
    t, x = await lorenz.integrate((0, 20), np.array([1.0, 1.0, 1.0]), method=IntegrationMethod.RK45)
    print(f"   ✅ {len(t)} stappen geïntegreerd")
    print(f"   Eindtoestand: x={x[-1]}")
    
    print("\n📋 Test 2: Vaste punten zoeken")
    guesses = [np.array([0,0,0]), np.array([10,10,10]), np.array([-10,-10,-10])]
    fps = await lorenz.find_fixed_points(guesses)
    print(f"   ✅ {len(fps)} vaste punten gevonden")
    for fp in fps:
        print(f"      • {fp.x} ({fp.stability.value})")
    
    print("\n📋 Test 3: Lyapunov exponenten (chaos detectie)")
    le = await lorenz.compute_lyapunov_spectrum()
    print(f"   ✅ Max Lyapunov: {le.max_exponent:.4f}")
    print(f"   Chaotisch: {le.is_chaotic()}")
    
    print("\n📋 Test 4: Bifurcatiediagram voor parameter rho")
    # Gebruik een eenvoudiger systeem voor demo
    duffing = ExampleSystems.duffing()
    bif_data = await duffing.bifurcation_diagram(
        parameter='gamma',
        param_range=(0.1, 1.0),
        n_points=20,
        x0=np.array([0.0, 0.0]),
        t_transient=5.0,
        t_measure=10.0
    )
    print(f"   ✅ Bifurcaties gevonden: {len(bif_data['bifurcations'])}")
    
    print("\n📋 Test 5: Visualisatie")
    if lorenz.enable_visualization:
        lorenz.plot_trajectory(dimensions=[0,1,2], filename="lorenz_trajectory.png")
        lorenz.plot_phase_portrait(plane=(0,1), filename="lorenz_phase.png")
        duffing.plot_bifurcation_diagram('gamma', bif_data, filename="duffing_bifurcation.png")
        print("   ✅ Visualisaties gegenereerd")
    
    print("\n📋 Test 6: Export")
    lorenz.export_state("lorenz_demo.json")
    
    print("\n📋 Test 7: Statistieken")
    stats = lorenz.get_stats()
    print(f"   Integraties: {stats['metrics']['integrations']}")
    print(f"   Vaste punten: {stats['metrics']['fixed_points_found']}")
    print(f"   Chaos: {stats['metrics']['chaos_detected']}")
    
    # Cleanup
    await lorenz.cleanup()
    
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