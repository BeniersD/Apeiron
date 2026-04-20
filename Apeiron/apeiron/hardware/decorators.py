"""
apeiron.hardware.decorators - Professionele foutafhandeling voor hardware operaties.
Bevat decorators met ingebouwde retries, circuit breaking, fallback en observability.
"""

import asyncio
import functools
import logging
import time
from typing import Type, Callable, Optional, Union, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Probeer optionele metrics
try:
    from prometheus_client import Counter, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Excepties importeren (relatief, pas aan naar jouw structuur)
from .exceptions import HardwareError, HardwareNotAvailableError, HardwareTimeoutError


class CircuitState(Enum):
    """
    Toestanden voor circuit breaker patroon.
    """
    CLOSED = "closed"       # Normale operatie
    OPEN = "open"           # Falen, geen aanroepen
    HALF_OPEN = "half_open" # Testen of herstel mogelijk is


@dataclass
class CircuitBreaker:
    """
    Circuit breaker voor hardware aanroepen.
    Voorkomt cascading failures door tijdelijke blokkade.
    """
    failure_threshold: int = 5
    timeout: float = 60.0
    max_retries: int = 3
    
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    
    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_success_time = time.time()
    
    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        # HALF_OPEN: sta een verzoek toe om te testen
        return True


@dataclass
class ErrorHandlingConfig:
    """
    Configuratie voor foutafhandeling.
    """
    retry_count: int = 3
    retry_delay: float = 0.5
    retry_backoff: float = 2.0
    retry_on: Tuple[Type[Exception], ...] = (HardwareError,)
    fallback_function: Optional[Callable] = None
    circuit_breaker: Optional[CircuitBreaker] = None
    log_level: int = logging.ERROR
    raise_original: bool = False
    prometheus_labels: Dict[str, str] = field(default_factory=dict)


# Prometheus metrics (indien beschikbaar)
if PROMETHEUS_AVAILABLE:
    hardware_errors_total = Counter(
        'apeiron_hardware_errors_total',
        'Total number of hardware errors',
        ['operation', 'error_type', 'layer_id']
    )
    hardware_retries_total = Counter(
        'apeiron_hardware_retries_total',
        'Total number of retry attempts',
        ['operation', 'layer_id']
    )
    hardware_calls_duration = Histogram(
        'apeiron_hardware_calls_duration_seconds',
        'Duration of hardware calls',
        ['operation', 'layer_id', 'status']
    )
else:
    hardware_errors_total = None
    hardware_retries_total = None
    hardware_calls_duration = None


def handle_hardware_errors(
    operation: Optional[str] = None,
    config: Optional[ErrorHandlingConfig] = None,
    **kwargs
) -> Callable:
    """
    Ultra-professionele decorator voor hardware foutafhandeling.
    
    Kenmerken:
    - Automatische retries met exponentiele backoff
    - Circuit breaker om overbelasting te voorkomen
    - Fallback naar opgegeven functie (bijv. CPU-emulatie)
    - Volledige logging met context
    - Prometheus metrics voor observability
    - Ondersteuning voor zowel synchrone als asynchrone functies
    
    Gebruik:
        @handle_hardware_errors(operation="cuda_matmul", retry_count=5)
        def cuda_matmul(a, b):
            ...
    
        @handle_hardware_errors(fallback_function=cpu_fallback)
        async def gpu_intensive_task(data):
            ...
    
    Args:
        operation: Naam van de operatie (voor logging/metrics)
        config: Volledige ErrorHandlingConfig instantie
        **kwargs: Individuele configuratieparameters (overschrijven config)
    
    Returns:
        Decorator functie
    """
    if config is None:
        config = ErrorHandlingConfig()
    else:
        # Maak een kopie om mutatie te voorkomen
        config = ErrorHandlingConfig(**config.__dict__)
    
    # Overschrijf met expliciete kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    op_name = operation or "unknown"
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Bepaal layer_id uit self als het een methode is
            layer_id = _extract_layer_id(args)
            
            # Circuit breaker check
            if config.circuit_breaker and not config.circuit_breaker.allow_request():
                logger.warning(f"Circuit breaker open voor {op_name}, aanroep geblokkeerd")
                if config.fallback_function:
                    return await _invoke_fallback(config.fallback_function, *args, **kwargs)
                raise HardwareError(f"Circuit breaker open for {op_name}")
            
            last_exception = None
            for attempt in range(config.retry_count + 1):
                start_time = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    
                    # Succes metrics en circuit breaker
                    duration = time.perf_counter() - start_time
                    _record_success(op_name, layer_id, duration)
                    if config.circuit_breaker:
                        config.circuit_breaker.record_success()
                    
                    return result
                    
                except config.retry_on as e:
                    last_exception = e
                    duration = time.perf_counter() - start_time
                    _record_failure(op_name, layer_id, type(e).__name__, duration)
                    
                    if config.circuit_breaker:
                        config.circuit_breaker.record_failure()
                    
                    if attempt < config.retry_count:
                        delay = config.retry_delay * (config.retry_backoff ** attempt)
                        logger.warning(
                            f"Hardware fout in {op_name} (poging {attempt+1}/{config.retry_count+1}): {e}. "
                            f"Retry over {delay:.2f}s"
                        )
                        _increment_retry_metric(op_name, layer_id)
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"Alle {config.retry_count+1} pogingen gefaald voor {op_name}: {e}"
                        )
                
                except Exception as e:
                    # Onverwachte exceptie: geen retry, direct afhandelen
                    duration = time.perf_counter() - start_time
                    _record_failure(op_name, layer_id, type(e).__name__, duration)
                    logger.exception(f"Onverwachte fout in {op_name}")
                    raise
            
            # Alle retries gefaald
            if config.fallback_function:
                logger.info(f"Uitvoeren fallback voor {op_name}")
                try:
                    return await _invoke_fallback(config.fallback_function, *args, **kwargs)
                except Exception as fb_e:
                    logger.error(f"Fallback ook gefaald: {fb_e}")
                    raise HardwareError(f"Zowel primaire als fallback faalden voor {op_name}") from last_exception
            
            if config.raise_original and last_exception:
                raise last_exception
            raise HardwareError(f"Hardware operatie {op_name} gefaald na {config.retry_count+1} pogingen") from last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            layer_id = _extract_layer_id(args)
            
            if config.circuit_breaker and not config.circuit_breaker.allow_request():
                logger.warning(f"Circuit breaker open voor {op_name}, aanroep geblokkeerd")
                if config.fallback_function:
                    return _invoke_fallback_sync(config.fallback_function, *args, **kwargs)
                raise HardwareError(f"Circuit breaker open for {op_name}")
            
            last_exception = None
            for attempt in range(config.retry_count + 1):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    
                    duration = time.perf_counter() - start_time
                    _record_success(op_name, layer_id, duration)
                    if config.circuit_breaker:
                        config.circuit_breaker.record_success()
                    
                    return result
                    
                except config.retry_on as e:
                    last_exception = e
                    duration = time.perf_counter() - start_time
                    _record_failure(op_name, layer_id, type(e).__name__, duration)
                    
                    if config.circuit_breaker:
                        config.circuit_breaker.record_failure()
                    
                    if attempt < config.retry_count:
                        delay = config.retry_delay * (config.retry_backoff ** attempt)
                        logger.warning(
                            f"Hardware fout in {op_name} (poging {attempt+1}/{config.retry_count+1}): {e}. "
                            f"Retry over {delay:.2f}s"
                        )
                        _increment_retry_metric(op_name, layer_id)
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Alle {config.retry_count+1} pogingen gefaald voor {op_name}: {e}"
                        )
                except Exception as e:
                    duration = time.perf_counter() - start_time
                    _record_failure(op_name, layer_id, type(e).__name__, duration)
                    logger.exception(f"Onverwachte fout in {op_name}")
                    raise
            
            if config.fallback_function:
                logger.info(f"Uitvoeren fallback voor {op_name}")
                try:
                    return _invoke_fallback_sync(config.fallback_function, *args, **kwargs)
                except Exception as fb_e:
                    logger.error(f"Fallback ook gefaald: {fb_e}")
                    raise HardwareError(f"Zowel primaire als fallback faalden voor {op_name}") from last_exception
            
            if config.raise_original and last_exception:
                raise last_exception
            raise HardwareError(f"Hardware operatie {op_name} gefaald na {config.retry_count+1} pogingen") from last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    # Sta gebruik zonder haakjes toe
    if callable(operation):
        func = operation
        operation = None
        return decorator(func)
    return decorator


# ========== Helper functies ==========

def _extract_layer_id(args: Tuple) -> str:
    """
    Probeer layer_id uit self (eerste argument) te halen.
    """
    if args and hasattr(args[0], 'id'):
        return getattr(args[0], 'id', 'unknown')
    return 'unknown'


async def _invoke_fallback(fallback: Callable, *args, **kwargs):
    """
    Roep fallback aan (ondersteunt async).
    """
    if asyncio.iscoroutinefunction(fallback):
        return await fallback(*args, **kwargs)
    else:
        # Voer synchrone fallback uit in thread om event loop niet te blokkeren
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: fallback(*args, **kwargs))


def _invoke_fallback_sync(fallback: Callable, *args, **kwargs):
    """
    Roep fallback aan (synchroon).
    """
    return fallback(*args, **kwargs)


def _record_success(operation: str, layer_id: str, duration: float):
    """
    Registreer succesvolle hardware aanroep in metrics.
    """
    if PROMETHEUS_AVAILABLE and hardware_calls_duration:
        try:
            hardware_calls_duration.labels(
                operation=operation,
                layer_id=layer_id,
                status='success'
            ).observe(duration)
        except Exception:
            pass


def _record_failure(operation: str, layer_id: str, error_type: str, duration: float):
    """
    Registreer gefaalde hardware aanroep in metrics.
    """
    if PROMETHEUS_AVAILABLE:
        if hardware_errors_total:
            try:
                hardware_errors_total.labels(
                    operation=operation,
                    error_type=error_type,
                    layer_id=layer_id
                ).inc()
            except Exception:
                pass
        if hardware_calls_duration:
            try:
                hardware_calls_duration.labels(
                    operation=operation,
                    layer_id=layer_id,
                    status='error'
                ).observe(duration)
            except Exception:
                pass


def _increment_retry_metric(operation: str, layer_id: str):
    if PROMETHEUS_AVAILABLE and hardware_retries_total:
        try:
            hardware_retries_total.labels(
                operation=operation,
                layer_id=layer_id
            ).inc()
        except Exception:
            pass