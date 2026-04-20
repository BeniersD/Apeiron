"""
Hardware Abstractielaag voor Apeiron.
Biedt automatische hardwaredetectie en backend‑selectie.
"""

from .factory import (
    HardwareFactory,
    get_hardware_factory,
    get_best_backend,
    get_backend_by_name,
    cleanup_hardware,
)
from .config import HardwareConfig, load_hardware_config
from .exceptions import (
    HardwareError,
    HardwareNotAvailableError,
    HardwareInitializationError,
    HardwareTimeoutError,
    HardwareMemoryError,
    HardwareResourceError,
    HardwareDataError,
    HardwareTransferError,
    HardwareSynchronizationError,
    FPGAError,
    QuantumError,
    CUDAError,
    # RetryStrategy en HardwareErrorHandler blijven hier
    RetryStrategy,
    HardwareErrorHandler,
)

# Importeer de VERBETERDE decorator uit decorators.py
from .decorators import handle_hardware_errors, ErrorHandlingConfig, CircuitBreaker

__all__ = [
    # Factory functies
    'HardwareFactory',
    'get_hardware_factory',
    'get_best_backend',
    'get_backend_by_name',
    'cleanup_hardware',
    # Configuratie
    'HardwareConfig',
    'load_hardware_config',
    # Excepties
    'HardwareError',
    'HardwareNotAvailableError',
    'HardwareInitializationError',
    'HardwareTimeoutError',
    'HardwareMemoryError',
    'HardwareResourceError',
    'HardwareDataError',
    'HardwareTransferError',
    'HardwareSynchronizationError',
    'FPGAError',
    'QuantumError',
    'CUDAError',
    # Decorators & hulpklassen
    'handle_hardware_errors',
    'ErrorHandlingConfig',
    'CircuitBreaker',
    # Retry strategie (uit exceptions)
    'RetryStrategy',
    'HardwareErrorHandler',
]