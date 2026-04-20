"""
CORE BASE - Abstracte basis voor alle 17 lagen (Professional Edition)
===========================================================================
State-of-the-art fundament met optionele enterprise features.

Kenmerken:
- Volledig getypeerd (mypy strict)
- Dataclass-configuratie met validatie
- Protocol-gebaseerde hardware-abstractie
- Uitgebreide timing/profiling utilities
- Retry & circuit breaker decorators
- Prometheus metrics integratie
- Health checks met pluggable validators
- Ondersteuning voor asynchrone en synchrone operaties
- Lazy imports voor snelle opstarttijd
"""

from __future__ import annotations

import asyncio
import contextlib
import cProfile
import hashlib
import inspect
import json
import logging
import pickle
import pstats
import time
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from io import StringIO
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    runtime_checkable,
)

# Type variables
T = TypeVar("T")  # Input type
U = TypeVar("U")  # Output type
V = TypeVar("V")  # Cache value type
R = TypeVar("R")  # Return type

logger = logging.getLogger(__name__)

# ============================================================================
# OPTIONELE IMPORTS (met lazy loading)
# ============================================================================

_import_cache: Dict[str, Any] = {}


def _lazy_import(module: str, name: str) -> Any:
    """Lazy import om opstarttijd te minimaliseren en circulaire imports te voorkomen."""
    key = f"{module}.{name}"
    if key not in _import_cache:
        try:
            mod = __import__(module, fromlist=[name])
            _import_cache[key] = getattr(mod, name)
        except ImportError:
            _import_cache[key] = None
    return _import_cache[key]


def _is_prometheus_available() -> bool:
    return _lazy_import("prometheus_client", "Counter") is not None


def _is_redis_available() -> bool:
    return _lazy_import("redis.asyncio", "Redis") is not None


def _is_pydantic_available() -> bool:
    return _lazy_import("pydantic", "BaseModel") is not None


def _is_ray_available() -> bool:
    return _lazy_import("ray", "init") is not None


def _is_qiskit_available() -> bool:
    return _lazy_import("qiskit", "QuantumCircuit") is not None


# ============================================================================
# CONFIGURATIE DATACLASSES
# ============================================================================


@dataclass(frozen=True)
class CacheConfig:
    """Configuratie voor caching."""

    enabled: bool = True
    strategy: Literal["memory", "redis", "hybrid"] = "hybrid"
    ttl: int = 3600  # seconden
    max_size: int = 1000
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    compression: bool = False
    compression_threshold: int = 1024

    def to_dict(self) -> Dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


@dataclass(frozen=True)
class HardwareConfig:
    """Configuratie voor hardware acceleratie."""

    enabled: bool = True
    fallback_to_cpu: bool = True
    timeout: float = 30.0
    backend: str = "auto"  # auto, cpu, cuda, fpga, quantum
    device_id: int = 0
    memory_fraction: float = 0.8


@dataclass(frozen=True)
class MetricsConfig:
    """Configuratie voor metrics/monitoring."""

    enabled: bool = True
    prometheus_port: Optional[int] = 9090
    enable_profiling: bool = False
    profiling_output: str = "profiles"
    enable_health_checks: bool = True
    health_check_interval: int = 60


@dataclass(frozen=True)
class DistributedConfig:
    """Configuratie voor gedistribueerde verwerking."""

    enabled: bool = False
    ray_address: Optional[str] = None
    num_cpus: Optional[int] = None
    num_gpus: Optional[int] = None


@dataclass(frozen=True)
class QuantumConfig:
    """Configuratie voor quantum computing."""

    enabled: bool = False
    backend: str = "aer_simulator"
    shots: int = 1000
    optimization_level: int = 1


@dataclass(frozen=True)
class LayerConfig:
    """Volledige configuratie voor een laag."""

    layer_id: str
    layer_type: "LayerType"
    mode: "ProcessingMode" = "ProcessingMode.ASYNCHRONOUS"
    cache: CacheConfig = field(default_factory=CacheConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    distributed: DistributedConfig = field(default_factory=DistributedConfig)
    quantum: QuantumConfig = field(default_factory=QuantumConfig)
    max_retries: int = 3
    validation_enabled: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayerConfig":
        """Creëer config uit dictionary (bijv. uit YAML)."""
        # Recursieve dataclass parsing
        return cls(
            layer_id=data["layer_id"],
            layer_type=LayerType(data["layer_type"]),
            mode=ProcessingMode(data.get("mode", "async")),
            cache=CacheConfig(**data.get("cache", {})),
            hardware=HardwareConfig(**data.get("hardware", {})),
            metrics=MetricsConfig(**data.get("metrics", {})),
            distributed=DistributedConfig(**data.get("distributed", {})),
            quantum=QuantumConfig(**data.get("quantum", {})),
            max_retries=data.get("max_retries", 3),
            validation_enabled=data.get("validation_enabled", False),
        )


# ============================================================================
# ENUMS
# ============================================================================


class LayerType(Enum):
    """Type van de laag binnen de architectuur."""

    FOUNDATIONAL = "foundational"  # Lagen 1-4
    ADAPTIVE = "adaptive"  # Lagen 5-7
    ONTOLOGICAL = "ontological"  # Lagen 8-13
    WORLDBUILDING = "worldbuilding"  # Lagen 14-17


class ProcessingMode(Enum):
    """Verwerkingsmodus."""

    SYNCHRONOUS = "sync"
    ASYNCHRONOUS = "async"
    BATCH = "batch"
    STREAM = "stream"
    QUANTUM = "quantum"


# ============================================================================
# PROTOCOLLEN VOOR PLUGINS
# ============================================================================


@runtime_checkable
class HardwareBackendProtocol(Protocol):
    """Interface voor hardware backends."""

    async def initialize(self, config: Dict[str, Any]) -> bool: ...

    async def process(self, data: Any) -> Any: ...

    def get_info(self) -> Dict[str, Any]: ...

    async def cleanup(self) -> None: ...


@runtime_checkable
class CacheBackendProtocol(Protocol):
    """Interface voor cache backends."""

    async def get(self, key: str) -> Optional[Any]: ...

    async def set(self, key: str, value: Any, ttl: Optional[int]) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def clear(self) -> None: ...


# ============================================================================
# DATASTRUCTUREN
# ============================================================================


@dataclass(frozen=True, slots=True)
class ProcessingContext:
    """Context die meereist met elke verwerkingsstap."""

    cycle: int
    timestamp: float = field(default_factory=time.time)
    mode: ProcessingMode = ProcessingMode.ASYNCHRONOUS
    depth: int = 0
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def next_cycle(self) -> "ProcessingContext":
        return ProcessingContext(
            cycle=self.cycle + 1,
            mode=self.mode,
            depth=self.depth,
            parent_id=self.parent_id,
            metadata=self.metadata.copy(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "timestamp": self.timestamp,
            "mode": self.mode.value,
            "depth": self.depth,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessingContext":
        return cls(
            cycle=data["cycle"],
            timestamp=data.get("timestamp", time.time()),
            mode=ProcessingMode(data.get("mode", "async")),
            depth=data.get("depth", 0),
            parent_id=data.get("parent_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass(slots=True)
class ProcessingResult(Generic[U]):
    """Gestandaardiseerd resultaat van een laag."""

    output: Optional[U] = None
    success: bool = True
    processing_time_ms: float = 0.0
    confidence: float = 1.0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def error(cls, message: str, time_ms: float = 0.0) -> "ProcessingResult[U]":
        return cls(success=False, errors=[message], processing_time_ms=time_ms)

    @classmethod
    def success_result(
        cls, output: U, time_ms: float, confidence: float = 1.0
    ) -> "ProcessingResult[U]":
        return cls(
            output=output, success=True, processing_time_ms=time_ms, confidence=confidence
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "processing_time_ms": self.processing_time_ms,
            "confidence": self.confidence,
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class LayerMetrics:
    """Verzamelde statistieken voor een laag."""

    cycles_processed: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    error_count: int = 0
    warning_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hardware_errors: int = 0
    quantum_ops: int = 0
    distributed_calls: int = 0
    created_at: float = field(default_factory=time.time)

    def update(self, result: ProcessingResult[Any]) -> None:
        self.cycles_processed += 1
        self.total_time_ms += result.processing_time_ms
        # EMA update
        alpha = 0.3
        self.avg_time_ms = (
            alpha * result.processing_time_ms + (1 - alpha) * self.avg_time_ms
        )
        self.min_time_ms = min(self.min_time_ms, result.processing_time_ms)
        self.max_time_ms = max(self.max_time_ms, result.processing_time_ms)
        if result.errors:
            self.error_count += len(result.errors)
        if result.warnings:
            self.warning_count += len(result.warnings)


@dataclass(slots=True)
class HealthStatus:
    """Gezondheidsstatus van een laag."""

    healthy: bool = True
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    last_check: float = field(default_factory=time.time)
    response_time_ms: float = 0.0
    memory_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "healthy": self.healthy,
            "issues": self.issues,
            "warnings": self.warnings,
            "last_check": self.last_check,
            "response_time_ms": self.response_time_ms,
            "memory_mb": self.memory_mb,
        }


# ============================================================================
# DECORATORS
# ============================================================================


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator voor exponentiële backoff retries.

    Args:
        max_attempts: Maximaal aantal pogingen (inclusief eerste).
        delay: Basis wachttijd in seconden.
        backoff: Factor waarmee delay vermenigvuldigd wordt.
        exceptions: Tuple van excepties waarop retry moet plaatsvinden.
        on_retry: Callback die wordt aangeroepen voor elke retry.

    Example:
        @retry(max_attempts=5, exceptions=(ConnectionError,))
        async def fetch_data():
            ...
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> R:
            last_exc: Optional[Exception] = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt == max_attempts - 1:
                        raise
                    wait = delay * (backoff**attempt)
                    if on_retry:
                        on_retry(e, attempt + 1)
                    await asyncio.sleep(wait)
            raise last_exc  # type: ignore

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> R:
            last_exc: Optional[Exception] = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt == max_attempts - 1:
                        raise
                    wait = delay * (backoff**attempt)
                    if on_retry:
                        on_retry(e, attempt + 1)
                    time.sleep(wait)
            raise last_exc  # type: ignore

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

def cached(ttl: int = 3600):
    """
    Decorator voor caching van asynchrone methodes met TTL.
    
    Vereist dat de klasse een `_memory_cache` attribuut en `enable_cache` vlag heeft.
    De cache sleutel wordt gegenereerd op basis van functienaam en argumenten.
    
    Args:
        ttl: Time-to-live in seconden (default: 3600)
        
    Returns:
        Decorator functie
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not getattr(self, 'enable_cache', False):
                return await func(self, *args, **kwargs)
            
            # Genereer unieke cache sleutel
            key_parts = [func.__name__] + [str(a) for a in args]
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
            
            # Check in-memory cache
            if hasattr(self, '_memory_cache') and cache_key in self._memory_cache:
                value, expiry = self._memory_cache[cache_key]
                if time.time() < expiry:
                    if hasattr(self, 'metrics'):
                        self.metrics.cache_hits += 1
                    return value
                else:
                    # Verlopen item verwijderen
                    del self._memory_cache[cache_key]
            
            if hasattr(self, 'metrics'):
                self.metrics.cache_misses += 1
            
            # Voer originele functie uit
            result = await func(self, *args, **kwargs)
            
            # Sla op in cache indien resultaat niet None
            if result is not None and hasattr(self, '_memory_cache'):
                self._memory_cache[cache_key] = (result, time.time() + ttl)
            
            return result
        return wrapper
    return decorator

def profile(
    enabled: bool = True,
    sort_by: str = "cumulative",
    output_file: Optional[str] = None,
) -> Callable:
    """
    Decorator voor cProfile performance analyse.

    Args:
        enabled: Schakel profiling in/uit.
        sort_by: Sorteercriterium voor stats ('cumulative', 'time', 'calls').
        output_file: Bestand om stats naar weg te schrijven (optioneel).
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not enabled:
                return func(*args, **kwargs)

            profiler = cProfile.Profile()
            profiler.enable()
            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()
                s = StringIO()
                stats = pstats.Stats(profiler, stream=s).sort_stats(sort_by)
                stats.print_stats(20)
                logger.debug(f"Profile voor {func.__name__}:\n{s.getvalue()}")
                if output_file:
                    stats.dump_stats(output_file)
            return result

        return wrapper

    return decorator


# ============================================================================
# TIMING UTILITY
# ============================================================================

@dataclass
class TimingResult:
    """Resultaat van een timing meting met ondersteuning voor nesting."""

    operation: str
    duration: float
    start_time: float
    end_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List["TimingResult"] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        return self.duration * 1000.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "duration": self.duration,
            "duration_ms": self.duration_ms,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "metadata": self.metadata,
            "children": [c.to_dict() for c in self.children],
        }


class _TimingContext:
    _stack: List["_TimingContext"] = []

    def __init__(
        self,
        operation: str,
        logger: Optional[logging.Logger] = None,
        log_level: int = logging.DEBUG,
        use_prometheus: bool = True,
        prometheus_labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        on_exit: Optional[Callable[[TimingResult], None]] = None,
    ):
        self.operation = operation
        self.logger = logger or logging.getLogger(__name__)
        self.log_level = log_level
        self.use_prometheus = use_prometheus and _is_prometheus_available()
        self.prometheus_labels = prometheus_labels or {}
        self.metadata = metadata or {}
        self.on_exit = on_exit

        self.start_time: Optional[float] = None
        self.result: Optional[TimingResult] = None
        self.parent: Optional[_TimingContext] = None
        self.children: List[TimingResult] = []

    def __enter__(self) -> TimingResult:
        if self._stack:
            self.parent = self._stack[-1]
        self._stack.append(self)

        self.start_time = time.perf_counter()
        self.result = TimingResult(
            operation=self.operation,
            duration=0.0,
            start_time=self.start_time,
            end_time=0.0,
            metadata=self.metadata.copy(),
            children=self.children,
        )
        return self.result

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.result.end_time = time.perf_counter()
        self.result.duration = self.result.end_time - self.start_time
        self._stack.pop()

        if self.parent:
            self.parent.children.append(self.result)

        status = "failed" if exc_type else "success"
        self.logger.log(
            self.log_level,
            f"[TIMING] {self.operation}: {self.result.duration_ms:.3f}ms ({status})",
        )

        if self.use_prometheus:
            Histogram = _lazy_import("prometheus_client", "Histogram")
            if Histogram:
                labels = {
                    "operation": self.operation,
                    "layer_id": self.prometheus_labels.get("layer_id", "unknown"),
                    "status": status,
                }
                Histogram(
                    "apeiron_operation_duration_seconds",
                    "Duration of operations",
                    labelnames=list(labels.keys()),
                ).labels(**labels).observe(self.result.duration)

        if self.on_exit:
            try:
                self.on_exit(self.result)
            except Exception as e:
                self.logger.error(f"on_exit callback failed: {e}")

        return False  # Geen exceptie onderdrukken


@contextlib.contextmanager
def measure_time(
    operation: str,
    logger: Optional[logging.Logger] = None,
    log_level: int = logging.DEBUG,
    use_prometheus: bool = True,
    prometheus_labels: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    on_exit: Optional[Callable[[TimingResult], None]] = None,
) -> TimingResult:
    """
    Context manager voor het meten van uitvoeringstijd met uitgebreide functionaliteit.

    Gebruik:
        with measure_time("data_processing", logger=my_logger, metadata={'batch_size': 32}) as timing:
            result = process_data()
            timing.metadata['records'] = len(result)

    Args:
        operation: Naam van de operatie (voor logging/metrics)
        logger: Logger instantie (default: module logger)
        log_level: Logging niveau (default: DEBUG)
        use_prometheus: Of Prometheus histogram moet worden gebruikt
        prometheus_labels: Extra labels voor Prometheus (bv. {'layer_id': 'L1'})
        metadata: Initiële metadata dictionary
        on_exit: Callback die wordt aangeroepen met het TimingResult na afloop

    Returns:
        Een TimingResult object dat tijdens de context kan worden aangevuld.
    """
    ctx = _TimingContext(
        operation=operation,
        logger=logger,
        log_level=log_level,
        use_prometheus=use_prometheus,
        prometheus_labels=prometheus_labels,
        metadata=metadata,
        on_exit=on_exit,
    )
    with ctx as result:
        yield result


def timed(
    operation: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    log_level: int = logging.DEBUG,
    use_prometheus: bool = True,
    prometheus_labels: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    on_exit: Optional[Callable[[TimingResult], None]] = None,
) -> Callable:
    """
    Decorator voor het meten van uitvoeringstijd van functies/methoden.

    Kan zowel met als zonder argumenten worden gebruikt:

        @timed
        def my_func():
            pass

        @timed(operation="custom_name", log_level=logging.INFO)
        async def my_async_func():
            pass

    Args:
        operation: Naam van de operatie (default: functienaam)
        logger: Logger instantie
        log_level: Logging niveau
        use_prometheus: Of Prometheus histogram moet worden gebruikt
        prometheus_labels: Extra labels voor Prometheus
        metadata: Initiële metadata dictionary
        on_exit: Callback die wordt aangeroepen met het TimingResult na afloop

    Returns:
        Decorator functie
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation or f"{func.__module__}.{func.__qualname__}"

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with measure_time(
                operation=op_name,
                logger=logger,
                log_level=log_level,
                use_prometheus=use_prometheus,
                prometheus_labels=prometheus_labels,
                metadata=metadata,
                on_exit=on_exit,
            ):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with measure_time(
                operation=op_name,
                logger=logger,
                log_level=log_level,
                use_prometheus=use_prometheus,
                prometheus_labels=prometheus_labels,
                metadata=metadata,
                on_exit=on_exit,
            ):
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    if callable(operation):
        # Geval: @timed
        return decorator(operation)
    return decorator


# ============================================================================
# ABSTRACTE LAAG
# ============================================================================


class Layer(ABC, Generic[T, U]):
    """
    Abstracte basis voor alle 17 lagen in de architectuur.

    Definieert de verplichte interface en biedt optionele integraties
    voor hardware acceleratie, caching, profiling, metrics, validatie,
    distributed processing en quantum computing.

    Type Parameters:
        T: Het type van de input data
        U: Het type van de output data
    """

    def __init__(self, config: LayerConfig) -> None:
        """
        Initialiseer een nieuwe laag.

        Args:
            config: Volledige configuratie voor deze laag.
        """
        self.config = config
        self.id = config.layer_id
        self.type = config.layer_type
        self.mode = config.mode

        # Metrics initialisatie
        self.metrics = LayerMetrics()

        # Feature vlaggen
        self.enable_hardware = config.hardware.enabled
        self.enable_cache = config.cache.enabled
        self.enable_profiling = config.metrics.enable_profiling
        self.enable_metrics = config.metrics.enabled
        self.enable_validation = config.validation_enabled
        self.enable_distributed = config.distributed.enabled
        self.enable_quantum = config.quantum.enabled

        # Hardware backend (lazy init)
        self._hardware: Optional[HardwareBackendProtocol] = None

        # Cache backends (lazy init)
        self._cache: Optional[CacheBackendProtocol] = None
        self._memory_cache: Dict[str, Tuple[Any, float]] = {}
        self._redis_client: Any = None
        if config.cache.enabled and config.cache.strategy in ("redis", "hybrid"):
            if _is_redis_available():
                Redis = _lazy_import("redis.asyncio", "Redis")
                self._redis_client = Redis(
                    host=config.cache.redis_host,
                    port=config.cache.redis_port,
                    db=config.cache.redis_db,
                )

        # Quantum backend (lazy init)
        self._quantum_backend: Any = None

        # Ray initialisatie
        self._ray_actor: Any = None
        if config.distributed.enabled and _is_ray_available():
            ray = _lazy_import("ray", None)
            if not ray.is_initialized():
                ray.init(
                    address=config.distributed.ray_address,
                    num_cpus=config.distributed.num_cpus,
                    num_gpus=config.distributed.num_gpus,
                    ignore_reinit_error=True,
                )

        # Event subscribers
        self._subscribers: Dict[str, List[Callable]] = {}

        # Hiërarchie
        self.parent: Optional[Layer] = None
        self.children: List[Layer] = []

        # Health checks
        self.health_status = HealthStatus()
        self._health_check_task: Optional[asyncio.Task] = None
        if config.metrics.enable_health_checks:
            self._start_health_checks()

        # Prometheus metrics server (optioneel)
        if config.metrics.enabled and config.metrics.prometheus_port:
            self._setup_prometheus_server(config.metrics.prometheus_port)

        logger.info("=" * 80)
        logger.info(f"🌱 LAAG {self.id} ({self.type.value}) GEÏNITIALISEERD")
        logger.info("=" * 80)
        logger.info(f"   Hardware: {'✅' if self.enable_hardware else '❌'}")
        logger.info(f"   Cache: {'✅' if self.enable_cache else '❌'} ({config.cache.strategy})")
        logger.info(f"   Metrics: {'✅' if self.enable_metrics else '❌'}")
        logger.info(f"   Distributed: {'✅' if self.enable_distributed else '❌'}")
        logger.info(f"   Quantum: {'✅' if self.enable_quantum else '❌'}")
        logger.info("=" * 80)

    def _setup_prometheus_server(self, port: int) -> None:
        """Start Prometheus metrics server indien gewenst."""
        try:
            start_http_server = _lazy_import("prometheus_client", "start_http_server")
            if start_http_server:
                start_http_server(port)
                logger.info(f"📊 Prometheus metrics server gestart op poort {port}")
        except Exception as e:
            logger.warning(f"⚠️ Kon Prometheus server niet starten: {e}")

    # ------------------------------------------------------------------------
    # Verplichte abstracte methoden
    # ------------------------------------------------------------------------
    @abstractmethod
    async def process(self, input_data: T, context: ProcessingContext) -> ProcessingResult[U]:
        """
        Verwerk input data en produceer een resultaat.

        Deze methode moet worden geïmplementeerd door elke concrete laag.

        Args:
            input_data: De input data van type T
            context: De verwerkingscontext met metadata

        Returns:
            Een ProcessingResult object met de uitvoer en metadata.
        """
        ...

    @abstractmethod
    async def validate(self) -> bool:
        """
        Valideer de interne staat van de laag.

        Wordt gebruikt voor health checks.

        Returns:
            True als de laag gezond is, anders False.
        """
        ...

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        Retourneer de interne staat van de laag voor serialisatie.

        Returns:
            Dictionary die de volledige staat representeert.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """
        Reset de laag naar initiële staat.
        """
        ...

    # ------------------------------------------------------------------------
    # Hardware abstractie
    # ------------------------------------------------------------------------
    async def _get_hardware(self) -> Optional[HardwareBackendProtocol]:
        """Lazy initialisatie van hardware backend."""
        if self._hardware is None and self.enable_hardware:
            # Lazy import van hardware factory
            from apeiron.hardware import get_best_backend

            loop = asyncio.get_event_loop()
            self._hardware = await loop.run_in_executor(
                None,
                lambda: get_best_backend(
                    backend=self.config.hardware.backend,
                    fallback_to_cpu=self.config.hardware.fallback_to_cpu,
                ),
            )
            if self._hardware:
                await self._hardware.initialize(
                    {
                        "device_id": self.config.hardware.device_id,
                        "memory_fraction": self.config.hardware.memory_fraction,
                    }
                )
                logger.info(f"⚡ Hardware backend geladen: {self._hardware.get_info()}")
        return self._hardware

    async def _cpu_fallback(self, *args: Any, **kwargs: Any) -> Any:
        """
        Fallback methode voor CPU verwerking wanneer hardware faalt.
        Moet worden overschreven door subklassen die hardware acceleratie gebruiken.
        """
        raise NotImplementedError(f"Geen CPU fallback voor {self.id}")

    # ------------------------------------------------------------------------
    # Caching helpers
    # ------------------------------------------------------------------------
    async def _cache_get(self, key: str) -> Optional[Any]:
        if not self.enable_cache:
            return None
        # Check memory cache
        if key in self._memory_cache:
            value, expiry = self._memory_cache[key]
            if time.time() < expiry:
                self.metrics.cache_hits += 1
                return value
            else:
                del self._memory_cache[key]
        self.metrics.cache_misses += 1
        # Check Redis
        if self._redis_client:
            data = await self._redis_client.get(key)
            if data:
                value = pickle.loads(data)
                self._memory_cache[key] = (value, time.time() + self.config.cache.ttl)
                return value
        return None

    async def _cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self.enable_cache:
            return
        ttl = ttl or self.config.cache.ttl
        self._memory_cache[key] = (value, time.time() + ttl)
        if self._redis_client:
            await self._redis_client.setex(key, ttl, pickle.dumps(value))

    def clear_cache(self) -> None:
        self._memory_cache.clear()
        if self._redis_client:
            asyncio.create_task(self._redis_client.flushdb())

    # ------------------------------------------------------------------------
    # Quantum methodes
    # ------------------------------------------------------------------------
    async def process_quantum(self, input_data: T, context: ProcessingContext) -> ProcessingResult[U]:
        if not self.enable_quantum:
            return ProcessingResult.error("Quantum verwerking niet ingeschakeld")
        try:
            start = time.perf_counter()
            circuit = self._to_quantum_circuit(input_data)
            backend = await self._get_quantum_backend()
            job = backend.run(circuit, shots=self.config.quantum.shots)
            result = job.result()
            output = self._from_quantum_result(result)
            duration = (time.perf_counter() - start) * 1000
            self.metrics.quantum_ops += 1
            return ProcessingResult.success_result(output, duration)
        except Exception as e:
            logger.error(f"❌ Quantum verwerking fout: {e}")
            return ProcessingResult.error(str(e))

    async def _get_quantum_backend(self) -> Any:
        if self._quantum_backend is None and _is_qiskit_available():
            Aer = _lazy_import("qiskit", "Aer")
            if Aer:
                self._quantum_backend = Aer.get_backend(self.config.quantum.backend)
        return self._quantum_backend

    def _to_quantum_circuit(self, data: Any) -> Any:
        raise NotImplementedError("_to_quantum_circuit moet worden geïmplementeerd")

    def _from_quantum_result(self, result: Any) -> Any:
        raise NotImplementedError("_from_quantum_result moet worden geïmplementeerd")

    # ------------------------------------------------------------------------
    # Distributed processing
    # ------------------------------------------------------------------------
    async def process_distributed(self, input_data: T, context: ProcessingContext) -> ProcessingResult[U]:
        if not self.enable_distributed:
            return ProcessingResult.error("Distributed verwerking niet ingeschakeld")
        # Implementatie afhankelijk van Ray
        # ...

    # ------------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------------
    def _start_health_checks(self) -> None:
        async def loop() -> None:
            while True:
                await asyncio.sleep(self.config.metrics.health_check_interval)
                try:
                    start = time.perf_counter()
                    healthy = await self.validate()
                    duration = (time.perf_counter() - start) * 1000
                    self.health_status.last_check = time.time()
                    self.health_status.response_time_ms = duration
                    self.health_status.healthy = healthy
                    if not healthy:
                        self.health_status.issues.append(
                            f"Health check failed at {datetime.now().isoformat()}"
                        )
                    # Geheugengebruik bijwerken
                    try:
                        import psutil

                        process = psutil.Process()
                        self.health_status.memory_mb = process.memory_info().rss / 1024 / 1024
                    except ImportError:
                        pass
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"❌ Health check fout: {e}")

        self._health_check_task = asyncio.create_task(loop())

    async def get_health_status(self) -> HealthStatus:
        return self.health_status

    # ------------------------------------------------------------------------
    # Hiërarchie management
    # ------------------------------------------------------------------------
    def add_child(self, layer: "Layer") -> None:
        self.children.append(layer)
        layer.parent = self

    def remove_child(self, layer_id: str) -> bool:
        for i, child in enumerate(self.children):
            if child.id == layer_id:
                child.parent = None
                self.children.pop(i)
                return True
        return False

    def get_ancestors(self) -> List["Layer"]:
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self) -> List["Layer"]:
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    # ------------------------------------------------------------------------
    # Metrics & status
    # ------------------------------------------------------------------------
    def get_metrics(self) -> Dict[str, Any]:
        return {
            "layer_id": self.id,
            "layer_type": self.type.value,
            "mode": self.mode.value,
            "metrics": {
                "cycles": self.metrics.cycles_processed,
                "avg_time_ms": self.metrics.avg_time_ms,
                "min_time_ms": self.metrics.min_time_ms if self.metrics.min_time_ms != float("inf") else 0,
                "max_time_ms": self.metrics.max_time_ms,
                "errors": self.metrics.error_count,
                "warnings": self.metrics.warning_count,
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "hardware_errors": self.metrics.hardware_errors,
                "quantum_ops": self.metrics.quantum_ops,
                "distributed_calls": self.metrics.distributed_calls,
                "uptime": time.time() - self.metrics.created_at,
            },
            "children": len(self.children),
            "health": self.health_status.to_dict(),
            "features": {
                "hardware": self.enable_hardware,
                "cache": self.enable_cache,
                "profiling": self.enable_profiling,
                "metrics": self.enable_metrics,
                "validation": self.enable_validation,
                "distributed": self.enable_distributed,
                "quantum": self.enable_quantum,
            },
        }

    def get_config_dict(self) -> Dict[str, Any]:
        return {
            "layer_id": self.id,
            "layer_type": self.type.value,
            "mode": self.mode.value,
            "max_retries": self.config.max_retries,
            "cache": self.config.cache.to_dict(),
            "hardware": {f.name: getattr(self.config.hardware, f.name) for f in fields(self.config.hardware)},
            "metrics": {f.name: getattr(self.config.metrics, f.name) for f in fields(self.config.metrics)},
            "distributed": {f.name: getattr(self.config.distributed, f.name) for f in fields(self.config.distributed)},
            "quantum": {f.name: getattr(self.config.quantum, f.name) for f in fields(self.config.quantum)},
        }

    # ------------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------------
    async def cleanup(self) -> None:
        """Ruim resources op: stop health checks, sluit verbindingen, cleanup kinderen."""
        logger.info(f"🧹 Cleanup voor {self.id}")
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        if self._redis_client:
            await self._redis_client.close()
        if self._hardware and hasattr(self._hardware, "cleanup"):
            await self._hardware.cleanup()
        for child in self.children:
            await child.cleanup()
        logger.info(f"✅ Cleanup voltooid voor {self.id}")

    def __repr__(self) -> str:
        return f"Layer(id='{self.id}', type={self.type.value})"

    def __str__(self) -> str:
        return f"🌱 {self.id} ({self.type.value})"

    