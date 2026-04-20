"""
HARDWARE EXCEPTIONS - UITGEBREIDE VERSIE
================================================================================
Biedt een hiërarchie van exceptions voor alle hardware-gerelateerde fouten.
Ondersteunt contextuele informatie zoals backend naam, operatie, en timeout waarden.

Uitbreidingen:
- Error codes en categorieën
- Logging integratie
- Retry strategieën
- Error aggregatie
- Metrics tracking
"""

import time
import logging
from typing import Optional, Dict, Any, List, Callable, Type
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categorieën van hardware fouten."""
    AVAILABILITY = "availability"
    INITIALIZATION = "initialization"
    TIMEOUT = "timeout"
    SYNCHRONIZATION = "synchronization"
    MEMORY = "memory"
    RESOURCE = "resource"
    DATA = "data"
    TRANSFER = "transfer"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Ernst van de fout."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    FATAL = 5


@dataclass
class ErrorMetrics:
    """Metrics voor error tracking."""
    count: int = 0
    first_occurrence: float = field(default_factory=time.time)
    last_occurrence: float = field(default_factory=time.time)
    contexts: List[Dict] = field(default_factory=list)
    
    def update(self, context: Dict):
        """Update metrics met nieuwe occurrence."""
        self.count += 1
        self.last_occurrence = time.time()
        if len(self.contexts) < 10:  # Houd laatste 10 bij
            self.contexts.append(context)


class HardwareError(Exception):
    """
    Basis exception voor alle hardware-gerelateerde fouten.
    
    Attributes:
        message: Mens-leesbare foutmelding
        backend: Naam van de backend waar de fout optrad
        timestamp: Tijdstip van de fout
        context: Extra context informatie
        category: Categorie van de fout
        severity: Ernst van de fout
        error_code: Optionele error code
        recoverable: Of de fout herstelbaar is
    """
    
    # Class-level metrics tracking
    _metrics: Dict[Type, ErrorMetrics] = {}
    
    def __init__(self, 
                 message: str, 
                 backend: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None,
                 category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 error_code: Optional[int] = None,
                 recoverable: bool = False):
        """
        Initialiseer hardware error.
        
        Args:
            message: Foutmelding
            backend: Naam van de backend
            context: Extra context informatie
            category: Categorie van de fout
            severity: Ernst van de fout
            error_code: Optionele error code
            recoverable: Of de fout herstelbaar is
        """
        self.backend = backend or "Onbekend"
        self.timestamp = time.time()
        self.context = context or {}
        self.category = category
        self.severity = severity
        self.error_code = error_code
        self.recoverable = recoverable
        
        # Update metrics
        self._update_metrics()
        
        # Formateer bericht met backend info
        formatted_message = f"[{self.backend}] {message}"
        
        parts = []
        if error_code is not None:
            parts.append(f"code={error_code}")
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            parts.append(context_str)
        if parts:
            formatted_message += f" ({', '.join(parts)})"
        
        # Log de error
        self._log_error(formatted_message)
        
        super().__init__(formatted_message)
    
    def _update_metrics(self):
        """Update class-level metrics."""
        cls = self.__class__
        if cls not in self._metrics:
            self._metrics[cls] = ErrorMetrics()
        self._metrics[cls].update(self.context)
    
    def _log_error(self, formatted_message: str):
        """Log de error met juiste severity."""
        if self.severity == ErrorSeverity.DEBUG:
            logger.debug(formatted_message)
        elif self.severity == ErrorSeverity.INFO:
            logger.info(formatted_message)
        elif self.severity == ErrorSeverity.WARNING:
            logger.warning(formatted_message)
        elif self.severity == ErrorSeverity.ERROR:
            logger.error(formatted_message)
        elif self.severity >= ErrorSeverity.CRITICAL:
            logger.critical(formatted_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer exception naar dictionary voor logging."""
        return {
            'type': self.__class__.__name__,
            'backend': self.backend,
            'message': str(self),
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'category': self.category.value,
            'severity': self.severity.value,
            'error_code': self.error_code,
            'recoverable': self.recoverable,
            'context': self.context
        }
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """Haal metrics op voor deze exception class."""
        metrics = cls._metrics.get(cls)
        if metrics:
            return {
                'count': metrics.count,
                'first_occurrence': metrics.first_occurrence,
                'last_occurrence': metrics.last_occurrence,
                'recent_contexts': metrics.contexts
            }
        return {'count': 0}
    
    @classmethod
    def reset_metrics(cls):
        """Reset metrics voor deze class."""
        if cls in cls._metrics:
            del cls._metrics[cls]


# ====================================================================
# INITIALISATIE & BESCHIKBAARHEID (UITGEBREID)
# ====================================================================

class HardwareNotAvailableError(HardwareError):
    """
    Hardware is niet beschikbaar.
    
    Voorbeelden:
    - Geen FPGA board gevonden
    - CUDA niet geïnstalleerd
    - Quantum backend niet bereikbaar
    """
    
    def __init__(self, 
                 backend: Optional[str] = None,
                 reason: Optional[str] = None,
                 required_drivers: Optional[List[str]] = None,
                 required_version: Optional[str] = None):
        """
        Args:
            backend: Naam van de backend
            reason: Specifieke reden waarom niet beschikbaar
            required_drivers: Benodigde drivers die ontbreken
            required_version: Benodigde versie
        """
        message = f"Hardware niet beschikbaar"
        if reason:
            message += f": {reason}"
        
        context = {}
        if required_drivers:
            context['required_drivers'] = required_drivers
        if required_version:
            context['required_version'] = required_version
        
        super().__init__(
            message, 
            backend, 
            context,
            category=ErrorCategory.AVAILABILITY,
            severity=ErrorSeverity.ERROR,
            recoverable=False
        )


class HardwareInitializationError(HardwareError):
    """
    Hardware kan niet worden geïnitialiseerd.
    
    Voorbeelden:
    - Bitstream laden mislukt
    - Geheugen allocatie faalt
    - Device niet responsief
    """
    
    def __init__(self,
                 backend: Optional[str] = None,
                 component: Optional[str] = None,
                 error_code: Optional[int] = None,
                 details: Optional[str] = None,
                 recoverable: bool = True):
        """
        Args:
            backend: Naam van de backend
            component: Specifiek component dat faalt
            error_code: Hardware error code
            details: Extra details
            recoverable: Of herinitialisatie mogelijk is
        """
        message = f"Initialisatie mislukt"
        if component:
            message += f" voor {component}"
        if details:
            message += f": {details}"
        
        context = {}
        if error_code is not None:
            context['error_code'] = error_code
        if component:
            context['component'] = component
        
        super().__init__(
            message, 
            backend, 
            context,
            category=ErrorCategory.INITIALIZATION,
            severity=ErrorSeverity.ERROR,
            error_code=error_code,
            recoverable=recoverable
        )


# ====================================================================
# TIMEOUT & SYNCHRONISATIE (UITGEBREID)
# ====================================================================

class HardwareTimeoutError(HardwareError):
    """
    Hardware operatie timeout.
    
    Voorbeelden:
    - FPGA interrupt blijft uit
    - Quantum circuit duurt te lang
    - DMA transfer haalt deadline niet
    """
    
    def __init__(self,
                 operation: str,
                 timeout: float,
                 backend: Optional[str] = None,
                 actual_time: Optional[float] = None,
                 retry_possible: bool = True):
        """
        Args:
            operation: Naam van de operatie
            timeout: Timeout waarde in seconden
            backend: Naam van de backend
            actual_time: Werkelijke tijd voordat timeout
            retry_possible: Of herpoging mogelijk is
        """
        message = f"Timeout na {timeout:.2f}s bij {operation}"
        
        context = {
            'operation': operation,
            'timeout': timeout
        }
        if actual_time is not None:
            context['actual_time'] = actual_time
        
        severity = ErrorSeverity.WARNING if retry_possible else ErrorSeverity.ERROR
        
        super().__init__(
            message, 
            backend, 
            context,
            category=ErrorCategory.TIMEOUT,
            severity=severity,
            recoverable=retry_possible
        )


class HardwareSynchronizationError(HardwareError):
    """
    Synchronisatie met hardware mislukt.
    
    Voorbeelden:
    - Interrupt niet ontvangen
    - Status register geeft fout
    - Data race detectie
    """
    
    def __init__(self,
                 sync_point: str,
                 backend: Optional[str] = None,
                 expected_state: Optional[str] = None,
                 actual_state: Optional[str] = None,
                 error_code: Optional[int] = None):
        """
        Args:
            sync_point: Waar synchronisatie mislukte
            backend: Naam van de backend
            expected_state: Verwachtte hardware status
            actual_state: Werkelijke hardware status
            error_code: Hardware error code
        """
        message = f"Synchronisatie mislukt bij {sync_point}"
        
        context = {'sync_point': sync_point}
        if expected_state:
            context['expected'] = expected_state
        if actual_state:
            context['actual'] = actual_state
        if error_code is not None:
            context['error_code'] = error_code
        
        super().__init__(
            message, 
            backend, 
            context,
            category=ErrorCategory.SYNCHRONIZATION,
            severity=ErrorSeverity.ERROR,
            error_code=error_code,
            recoverable=True
        )


# ====================================================================
# GEHEUGEN & RESOURCES (UITGEBREID)
# ====================================================================

class HardwareMemoryError(HardwareError):
    """
    Geheugen gerelateerde fouten.
    
    Voorbeelden:
    - Onvoldoende GPU geheugen
    - FPGA BRAM vol
    - DMA buffer allocatie mislukt
    """
    
    def __init__(self,
                 required: int,
                 available: int,
                 unit: str = "bytes",
                 backend: Optional[str] = None,
                 memory_type: Optional[str] = None,
                 fragmentation: Optional[float] = None):
        """
        Args:
            required: Benodigd geheugen
            available: Beschikbaar geheugen
            unit: Eenheid (bytes, MB, GB, etc.)
            backend: Naam van de backend
            memory_type: Type geheugen (VRAM, BRAM, DDR, etc.)
            fragmentation: Geheugen fragmentatie (0-1)
        """
        message = f"Onvoldoende geheugen: nodig {required} {unit}, beschikbaar {available} {unit}"
        
        context = {
            'required': required,
            'available': available,
            'unit': unit
        }
        if memory_type:
            context['memory_type'] = memory_type
        if fragmentation is not None:
            context['fragmentation'] = fragmentation
        
        super().__init__(
            message, 
            backend, 
            context,
            category=ErrorCategory.MEMORY,
            severity=ErrorSeverity.ERROR,
            recoverable=True
        )


class HardwareResourceError(HardwareError):
    """
    Resource uitputting (niet-geheugen).
    
    Voorbeelden:
    - Geen DMA kanalen vrij
    - Te veel parallelle operaties
    - Hardware slots vol
    """
    
    def __init__(self,
                 resource_type: str,
                 required: int,
                 available: int,
                 backend: Optional[str] = None,
                 details: Optional[str] = None,
                 max_capacity: Optional[int] = None):
        """
        Args:
            resource_type: Type resource (DMA channels, slots, etc.)
            required: Aantal benodigd
            available: Aantal beschikbaar
            backend: Naam van de backend
            details: Extra details
            max_capacity: Maximale capaciteit
        """
        message = f"Resource tekort: {resource_type} nodig {required}, beschikbaar {available}"
        if details:
            message += f" ({details})"
        
        context = {
            'resource_type': resource_type,
            'required': required,
            'available': available
        }
        if max_capacity is not None:
            context['max_capacity'] = max_capacity
        
        super().__init__(
            message, 
            backend, 
            context,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.WARNING,
            recoverable=True
        )


# ====================================================================
# DATA & FORMAT (UITGEBREID)
# ====================================================================

class HardwareDataError(HardwareError):
    """
    Data-gerelateerde fouten.
    
    Voorbeelden:
    - Ongeldige data format
    - Corrupte DMA transfer
    - Verkeerde dimensionaliteit
    """
    
    def __init__(self,
                 reason: str,
                 backend: Optional[str] = None,
                 expected_shape: Optional[tuple] = None,
                 actual_shape: Optional[tuple] = None,
                 data_type: Optional[str] = None,
                 corrupted: bool = False):
        """
        Args:
            reason: Reden van data fout
            backend: Naam van de backend
            expected_shape: Verwachtte dimensies
            actual_shape: Werkelijke dimensies
            data_type: Verwacht data type
            corrupted: Of data corrupt is
        """
        message = f"Data fout: {reason}"
        
        context = {'reason': reason}
        if expected_shape:
            context['expected_shape'] = expected_shape
        if actual_shape:
            context['actual_shape'] = actual_shape
        if data_type:
            context['data_type'] = data_type
        if corrupted:
            context['corrupted'] = True
        
        super().__init__(
            message, 
            backend, 
            context,
            category=ErrorCategory.DATA,
            severity=ErrorSeverity.ERROR if corrupted else ErrorSeverity.WARNING,
            recoverable=not corrupted
        )


class HardwareTransferError(HardwareError):
    """
    Data transfer fouten.
    
    Voorbeelden:
    - DMA transfer mislukt
    - PCIe error
    - Corruptie tijdens transfer
    """
    
    def __init__(self,
                 transfer_type: str,
                 size: int,
                 backend: Optional[str] = None,
                 error_code: Optional[int] = None,
                 bytes_transferred: Optional[int] = None,
                 retry_count: int = 0):
        """
        Args:
            transfer_type: Type transfer (DMA, PCIe, etc.)
            size: Grootte van transfer in bytes
            backend: Naam van de backend
            error_code: Hardware error code
            bytes_transferred: Werkelijk aantal bytes overgezet
            retry_count: Aantal herpogingen
        """
        message = f"Transfer mislukt: {transfer_type} ({size} bytes)"
        
        context = {
            'transfer_type': transfer_type,
            'size': size
        }
        if error_code is not None:
            context['error_code'] = error_code
        if bytes_transferred is not None:
            context['bytes_transferred'] = bytes_transferred
        if retry_count > 0:
            context['retry_count'] = retry_count
        
        super().__init__(
            message, 
            backend, 
            context,
            category=ErrorCategory.TRANSFER,
            severity=ErrorSeverity.ERROR,
            error_code=error_code,
            recoverable=retry_count < 3
        )


# ====================================================================
# HARDWARE SPECIFIEKE FOUTEN (UITGEBREID)
# ====================================================================

class FPGAError(HardwareError):
    """FPGA-specifieke fouten."""
    
    def __init__(self,
                 message: str,
                 register_values: Optional[Dict[str, int]] = None,
                 bitstream: Optional[str] = None,
                 temperature: Optional[float] = None,
                 power_consumption: Optional[float] = None,
                 error_code: Optional[int] = None):
        """
        Args:
            message: Foutmelding
            register_values: Waarden van FPGA registers
            bitstream: Geladen bitstream
            temperature: FPGA temperatuur in °C
            power_consumption: Power verbruik in W
            error_code: Hardware error code
        """
        context = {}
        if register_values:
            context['registers'] = register_values
        if bitstream:
            context['bitstream'] = bitstream
        if temperature is not None:
            context['temperature'] = temperature
        if power_consumption is not None:
            context['power'] = power_consumption
        
        super().__init__(
            message, 
            "FPGA", 
            context,
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            error_code=error_code
        )


class QuantumError(HardwareError):
    """Quantum-specifieke fouten."""
    
    def __init__(self,
                 message: str,
                 circuit_name: Optional[str] = None,
                 qubit_indices: Optional[List[int]] = None,
                 error_mitigation: Optional[str] = None,
                 fidelity: Optional[float] = None,
                 shots_completed: Optional[int] = None):
        """
        Args:
            message: Foutmelding
            circuit_name: Naam van quantum circuit
            qubit_indices: Betrokken qubits
            error_mitigation: Toegepaste error mitigation
            fidelity: Gemeten fidelity
            shots_completed: Aantal voltooide shots
        """
        context = {}
        if circuit_name:
            context['circuit'] = circuit_name
        if qubit_indices:
            context['qubits'] = qubit_indices
        if error_mitigation:
            context['error_mitigation'] = error_mitigation
        if fidelity is not None:
            context['fidelity'] = fidelity
        if shots_completed is not None:
            context['shots_completed'] = shots_completed
        
        super().__init__(
            message, 
            "Quantum", 
            context,
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR
        )


class CUDAError(HardwareError):
    """CUDA/GPU-specifieke fouten."""
    
    CUDA_ERROR_CODES = {
        1: "Missing CUDA driver",
        2: "Invalid device",
        3: "Out of memory",
        4: "Not initialized",
        5: "Deinitialized",
        6: "No device",
        7: "Invalid value",
        8: "Invalid pitch",
        9: "Invalid symbol",
        10: "Map failed"
    }
    
    def __init__(self,
                 message: str,
                 cuda_error_code: Optional[int] = None,
                 device_id: Optional[int] = None,
                 memory_info: Optional[Dict[str, int]] = None,
                 gpu_temperature: Optional[float] = None,
                 utilization: Optional[float] = None):
        """
        Args:
            message: Foutmelding
            cuda_error_code: CUDA error code
            device_id: GPU device ID
            memory_info: Geheugen informatie
            gpu_temperature: GPU temperatuur in °C
            utilization: GPU gebruik (0-1)
        """
        context = {}
        if cuda_error_code is not None:
            context['cuda_error'] = cuda_error_code
            if cuda_error_code in self.CUDA_ERROR_CODES:
                context['cuda_error_desc'] = self.CUDA_ERROR_CODES[cuda_error_code]
        if device_id is not None:
            context['device_id'] = device_id
        if memory_info:
            context['memory'] = memory_info
        if gpu_temperature is not None:
            context['temperature'] = gpu_temperature
        if utilization is not None:
            context['utilization'] = utilization
        
        super().__init__(
            message, 
            "CUDA", 
            context,
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            error_code=cuda_error_code
        )


# ====================================================================
# ERROR HANDLER MET RETRY STRATEGIE
# ====================================================================

class RetryStrategy:
    """Strategie voor herpogingen bij hardware fouten."""
    
    def __init__(self,
                 max_retries: int = 3,
                 base_delay: float = 0.1,
                 max_delay: float = 5.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True,
                 retry_on: Optional[List[Type[HardwareError]]] = None):
        """
        Args:
            max_retries: Maximum aantal herpogingen
            base_delay: Basis wachttijd in seconden
            max_delay: Maximale wachttijd
            exponential_base: Base voor exponential backoff
            jitter: Voeg random jitter toe
            retry_on: Lijst van errors waarop herpoging moet
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on or [HardwareTimeoutError, HardwareSynchronizationError]
        
        self.retry_count = 0
        self.last_error = None
    
    def should_retry(self, error: Exception) -> bool:
        """Bepaal of herpoging zinvol is."""
        if self.retry_count >= self.max_retries:
            return False
        
        for error_type in self.retry_on:
            if isinstance(error, error_type):
                return getattr(error, 'recoverable', True)
        
        return False
    
    def get_delay(self) -> float:
        """Bereken wachttijd voor volgende poging."""
        delay = self.base_delay * (self.exponential_base ** self.retry_count)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay
    
    def execute(self, func: Callable, *args, **kwargs):
        """Voer functie uit met retry strategie."""
        self.retry_count = 0
        self.last_error = None
        
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.last_error = e
                
                if not self.should_retry(e):
                    raise
                
                self.retry_count += 1
                delay = self.get_delay()
                
                logger.warning(f"Poging {self.retry_count} mislukt, "
                             f"opnieuw na {delay:.2f}s: {e}")
                
                time.sleep(delay)


# ====================================================================
# ERROR AGGREGATOR
# ====================================================================

class HardwareErrorAggregator:
    """Aggregeert hardware errors voor monitoring."""
    
    def __init__(self, window_seconds: int = 3600):
        """
        Args:
            window_seconds: Tijdsvenster voor aggregatie
        """
        self.window_seconds = window_seconds
        self.errors: List[HardwareError] = []
        self.by_type: Dict[str, int] = {}
        self.by_backend: Dict[str, int] = {}
        self.by_category: Dict[str, int] = {}
    
    def add_error(self, error: HardwareError):
        """Voeg error toe aan aggregator."""
        current_time = time.time()
        
        # Verwijder oude errors
        self.errors = [e for e in self.errors 
                      if current_time - e.timestamp < self.window_seconds]
        
        self.errors.append(error)
        
        # Update counters
        error_type = error.__class__.__name__
        self.by_type[error_type] = self.by_type.get(error_type, 0) + 1
        
        backend = error.backend
        self.by_backend[backend] = self.by_backend.get(backend, 0) + 1
        
        category = error.category.value
        self.by_category[category] = self.by_category.get(category, 0) + 1
    
    def get_report(self) -> Dict[str, Any]:
        """Genereer rapport van geaggregeerde errors."""
        return {
            'total_errors': len(self.errors),
            'window_seconds': self.window_seconds,
            'by_type': self.by_type,
            'by_backend': self.by_backend,
            'by_category': self.by_category,
            'recent_errors': [e.to_dict() for e in self.errors[-10:]]
        }
    
    def clear(self):
        """Wis alle errors."""
        self.errors.clear()
        self.by_type.clear()
        self.by_backend.clear()
        self.by_category.clear()


# ====================================================================
# GLOBAL ERROR HANDLER
# ====================================================================

class HardwareErrorHandler:
    """Globale error handler met callbacks."""
    
    _instance = None
    _handlers: Dict[Type[HardwareError], List[Callable]] = {}
    _aggregator = HardwareErrorAggregator()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_handler(cls, error_type: Type[HardwareError], 
                        handler: Callable[[HardwareError], None]):
        """Registreer handler voor specifiek error type."""
        if error_type not in cls._handlers:
            cls._handlers[error_type] = []
        cls._handlers[error_type].append(handler)
    
    @classmethod
    def handle_error(cls, error: HardwareError):
        """Verwerk error met geregistreerde handlers."""
        # Voeg toe aan aggregator
        cls._aggregator.add_error(error)
        
        # Roep handlers aan
        for error_type, handlers in cls._handlers.items():
            if isinstance(error, error_type):
                for handler in handlers:
                    try:
                        handler(error)
                    except Exception as e:
                        logger.error(f"Fout in error handler: {e}")
        
        # Standaard logging
        logger.error(f"Hardware error: {error}")
    
    @classmethod
    def get_aggregator(cls) -> HardwareErrorAggregator:
        """Haal error aggregator op."""
        return cls._aggregator

def hardware_fallback(fallback_func=None):
    """
    Decorator die automatisch naar een fallback functie gaat bij hardware fouten.
    
    Args:
        fallback_func: Fallback functie om aan te roepen bij fout
    
    Usage:
        @hardware_fallback(fallback_func=my_cpu_implementation)
        def my_fpga_method(self):
            # FPGA code
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HardwareError as e:
                # Gebruik globale handler
                HardwareErrorHandler.handle_error(e)
                
                if fallback_func:
                    logger.warning(f"Hardware fout, gebruik fallback: {e}")
                    return fallback_func(*args, **kwargs)
                raise
        return wrapper
    return decorator


# ====================================================================
# CONTEXT MANAGER (UITGEBREID)
# ====================================================================

class hardware_error_handling:
    """
    Context manager voor tijdelijke hardware error onderdrukking.
    
    Usage:
        with hardware_error_handling(suppress_timeout=True, max_retries=3):
            # Code die soms timeout
            result = ctx.retry_on_error(flaky_function)
    """
    
    def __init__(self, 
                 suppress_timeout: bool = False,
                 suppress_memory: bool = False,
                 suppress_init: bool = False,
                 max_retries: int = 3,
                 log_errors: bool = True):
        """
        Args:
            suppress_timeout: Onderdruk timeout errors
            suppress_memory: Onderdruk geheugen errors
            suppress_init: Onderdruk initialisatie errors
            max_retries: Maximum aantal herpogingen
            log_errors: Log errors wel/niet
        """
        self.suppress_timeout = suppress_timeout
        self.suppress_memory = suppress_memory
        self.suppress_init = suppress_init
        self.max_retries = max_retries
        self.log_errors = log_errors
        self.retry_count = 0
        self.errors = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            return True
        
        should_suppress = False
        
        # Check of we deze error moeten onderdrukken
        if self.suppress_timeout and isinstance(exc_value, HardwareTimeoutError):
            should_suppress = True
        elif self.suppress_memory and isinstance(exc_value, HardwareMemoryError):
            should_suppress = True
        elif self.suppress_init and isinstance(exc_value, HardwareInitializationError):
            should_suppress = True
        
        if should_suppress:
            if self.log_errors:
                logger.warning(f"Error onderdrukt: {exc_value}")
            self.errors.append(exc_value)
            return True
        
        return False
    
    def retry_on_error(self, func, *args, **kwargs):
        """
        Voer functie opnieuw uit bij bepaalde errors.
        """
        strategy = RetryStrategy(
            max_retries=self.max_retries,
            retry_on=[HardwareTimeoutError, HardwareSynchronizationError]
        )
        
        try:
            return strategy.execute(func, *args, **kwargs)
        except Exception as e:
            self.errors.append(e)
            raise
    
    def get_errors(self) -> List[Exception]:
        """Haal onderdrukte errors op."""
        return self.errors


# ====================================================================
# DEMONSTRATIE (UITGEBREID)
# ====================================================================

def demo():
    """Demonstreer hardware exceptions."""
    print("\n" + "="*80)
    print("🔧 HARDWARE EXCEPTIONS DEMONSTRATIE (UITGEBREID)")
    print("="*80)
    
    # Basis error
    print("\n📋 Basis HardwareError:")
    try:
        raise HardwareError(
            "Algemene hardware fout", 
            "FPGA",
            context={'register': 0xFF, 'state': 'error'},
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            error_code=0xDEAD
        )
    except HardwareError as e:
        print(f"   {e}")
        print(f"   Dict: {e.to_dict()}")
    
    # Not available error
    print("\n📋 HardwareNotAvailableError:")
    try:
        raise HardwareNotAvailableError(
            backend="Quantum",
            reason="Geen qubits beschikbaar",
            required_drivers=["qiskit", "ibmq-provider"],
            required_version="0.43.0"
        )
    except HardwareError as e:
        print(f"   {e}")
    
    # Timeout error
    print("\n📋 HardwareTimeoutError:")
    try:
        raise HardwareTimeoutError(
            operation="quantum_circuit_execution",
            timeout=5.0,
            backend="Quantum",
            actual_time=6.2,
            retry_possible=True
        )
    except HardwareError as e:
        print(f"   {e}")
    
    # Memory error
    print("\n📋 HardwareMemoryError:")
    try:
        raise HardwareMemoryError(
            required=8_000_000_000,
            available=4_000_000_000,
            unit="bytes",
            backend="CUDA",
            memory_type="VRAM",
            fragmentation=0.3
        )
    except HardwareError as e:
        print(f"   {e}")
    
    # Decorator demo met retry
    print("\n📋 Decorator met retry demo:")
    
    @handle_hardware_errors(default_return=None, 
                           retry_strategy=RetryStrategy(max_retries=2))
    def flaky_function():
        import random
        if random.random() < 0.7:  # 70% kans op fout
            raise HardwareTimeoutError("test", 1.0, "FPGA")
        return "success"
    
    result = flaky_function()
    print(f"   Resultaat: {result}")
    
    # Context manager demo
    print("\n📋 Context manager demo:")
    
    with hardware_error_handling(suppress_timeout=True, max_retries=2) as ctx:
        # Deze error wordt onderdrukt
        raise HardwareTimeoutError("test", 1.0, "FPGA")
        
        # Deze wordt opnieuw geprobeerd
        def failing():
            raise HardwareTimeoutError("test", 1.0, "FPGA")
        
        try:
            ctx.retry_on_error(failing)
        except Exception as e:
            print(f"   Uiteindelijk gefaald: {e}")
    
    print(f"   {len(ctx.get_errors())} errors onderdrukt")
    
    # Error aggregator demo
    print("\n📋 Error aggregator demo:")
    handler = HardwareErrorHandler()
    
    for i in range(5):
        error = HardwareTimeoutError(f"test_{i}", 1.0, "FPGA")
        handler.handle_error(error)
    
    report = handler.get_aggregator().get_report()
    print(f"   Total errors: {report['total_errors']}")
    print(f"   By type: {report['by_type']}")
    
    # Metrics demo
    print("\n📋 Metrics demo:")
    metrics = HardwareTimeoutError.get_metrics()
    print(f"   HardwareTimeoutError count: {metrics['count']}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Configureer logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    demo()