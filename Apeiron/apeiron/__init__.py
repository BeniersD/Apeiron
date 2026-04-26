"""
Apeiron Framework – Non‑antropocentrische kennisgenese.
De hardwaremodule wordt alleen geladen indien beschikbaar; bij afwezigheid wordt
een waarschuwing gegeven en blijven alle overige componenten functioneel.
"""

import logging
import sys
import os
from typing import Dict, List, Optional, Any

__version__ = "1.0.0"
__all__ = [
    'get_best_backend',
    'get_backend_by_name',
    'cleanup_hardware',
    'HardwareFactory',
    'HardwareConfig',
    'HardwareError',
    '__version__',
]

def _setup_logging() -> logging.Logger:
    logger = logging.getLogger('apeiron')
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

_logger = _setup_logging()

# ---------------------------------------------------------------------------
# Hardwarelaag – optioneel laden, zonder crash
# ---------------------------------------------------------------------------
try:
    from .hardware import (
        get_best_backend,
        get_backend_by_name,
        cleanup_hardware,
        HardwareFactory,
        HardwareConfig,
        HardwareError,
    )
    _logger.debug("Hardware module geladen")
except ImportError as e:
    _logger.warning(f"Hardware module niet beschikbaar: {e}")

    def get_best_backend(*args, **kwargs):
        raise NotImplementedError("Hardware module niet beschikbaar")

    def get_backend_by_name(*args, **kwargs):
        raise NotImplementedError("Hardware module niet beschikbaar")

    def cleanup_hardware(*args, **kwargs):
        pass

    HardwareFactory = None
    HardwareConfig = None
    HardwareError = None

# ---------------------------------------------------------------------------
# Optionele modules – importeren zonder fatale fout
# ---------------------------------------------------------------------------
try:
    from .layers.layer01_foundational import (
        UltimateObservable,
        ObservabilityType,
        Layer1_Observables,
    )
    __all__.extend(['UltimateObservable', 'ObservabilityType', 'Layer1_Observables'])
    _logger.debug("Layer 1 module geladen")
except ImportError as e:
    _logger.debug(f"Layer 1 module niet beschikbaar: {e}")

def initialize(db_path: Optional[str] = None) -> Dict[str, Any]:
    status = {
        'success': True,
        'hardware_available': HardwareFactory is not None,
        'layer1_available': 'UltimateObservable' in globals(),
        'version': __version__,
    }
    _logger.info(f"Apeiron framework v{__version__} geïnitialiseerd")
    return status

if os.environ.get('APEIRON_AUTO_INIT', 'true').lower() == 'true':
    initialize()