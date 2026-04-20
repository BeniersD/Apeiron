"""
Apeiron Core - Fundamentele abstracties en optionele uitbreidingen.
====================================================================
State-of-the-art core module met lazy loading, feature detection en
centrale configuratie.

Exports:
- Basis Layer abstractie en bijbehorende dataclasses
- EventBus voor asynchrone communicatie
- Optionele modules (adaptive thresholds, chaos detection, etc.)
"""

import importlib
import logging
import os
import sys
from typing import Dict, Any, Optional, List, Callable

__version__ = "1.0.0"

# ---------------------------------------------------------------------------
# Logging setup (kan worden overruled door applicatie)
# ---------------------------------------------------------------------------
def _setup_core_logging(level: str = "INFO") -> logging.Logger:
    """Configureer logging voor de core module."""
    logger = logging.getLogger("apeiron.core")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


logger = _setup_core_logging()

# ---------------------------------------------------------------------------
# Lazy loader voor optionele modules om opstarttijd te minimaliseren
# ---------------------------------------------------------------------------
class _LazyModule:
    """Lazy laadt een module pas bij eerste toegang."""
    def __init__(self, module_name: str, package: Optional[str] = None):
        self._module_name = module_name
        self._package = package
        self._module = None

    def __getattr__(self, name: str) -> Any:
        if self._module is None:
            try:
                self._module = importlib.import_module(
                    self._module_name, package=self._package
                )
            except ImportError as e:
                logger.debug(f"Module {self._module_name} niet beschikbaar: {e}")
                raise AttributeError(f"Module {self._module_name} not available") from e
        return getattr(self._module, name)


# ---------------------------------------------------------------------------
# Kern abstracties (verplicht)
# ---------------------------------------------------------------------------
try:
    from .base import (
        Layer,
        LayerType,
        ProcessingMode,
        ProcessingContext,
        ProcessingResult,
        LayerMetrics,
        LayerConfig,
        CacheConfig,
        HardwareConfig,
        MetricsConfig,
        DistributedConfig,
        QuantumConfig,
        cached,
        measure_time,
        timed,
        retry,
        profile,
    )
    _base_available = True
except ImportError as e:
    _base_available = False
    logger.error(f"Base module niet geladen: {e}")
    # Placeholders voor type checking
    Layer = None  # type: ignore
    ProcessingContext = None  # type: ignore
    ProcessingResult = None  # type: ignore

# ---------------------------------------------------------------------------
# Optionele modules (lazy loading)
# ---------------------------------------------------------------------------
_event_bus = _LazyModule(".event_bus", package="apeiron.core")
_adaptive_thresholds = _LazyModule(".adaptive_thresholds", package="apeiron.core")
_chaos_detection = _LazyModule(".chaos_detection", package="apeiron.core")
_document_tracker = _LazyModule(".document_tracker", package="apeiron.core")
_thermodynamic_cost = _LazyModule(".thermodynamic_cost", package="apeiron.core")
_thermodynamic_ethics = _LazyModule(".thermodynamic_ethics", package="apeiron.core")
_dependencies = _LazyModule(".dependencies", package="apeiron.core")

# Voor directe import (indien module beschikbaar)
EventBus = getattr(_event_bus, "EventBus", None)
Event = getattr(_event_bus, "Event", None)
EventPriority = getattr(_event_bus, "EventPriority", None)

AdaptiveThresholds = getattr(_adaptive_thresholds, "AdaptiveThresholds", None)
ChaosDetector = getattr(_chaos_detection, "ChaosDetector", None)
DocumentTracker = getattr(_document_tracker, "DocumentTracker", None)
ThermodynamicCost = getattr(_thermodynamic_cost, "ThermodynamicCost", None)
ThermodynamicEthics = getattr(_thermodynamic_ethics, "ThermodynamicEthics", None)
DependencyManager = getattr(_dependencies, "DependencyManager", None)

# ---------------------------------------------------------------------------
# Export lijst
# ---------------------------------------------------------------------------
__all__ = [
    "__version__",
    # Base
    "Layer",
    "LayerType",
    "ProcessingMode",
    "ProcessingContext",
    "ProcessingResult",
    "LayerMetrics",
    "LayerConfig",
    "CacheConfig",
    "HardwareConfig",
    "MetricsConfig",
    "DistributedConfig",
    "QuantumConfig",
    "cached",
    "measure_time",
    "timed",
    "retry",
    "profile",
    # Event bus
    "EventBus",
    "Event",
    "EventPriority",
    # Optionele modules (indien beschikbaar)
    "AdaptiveThresholds",
    "ChaosDetector",
    "DocumentTracker",
    "ThermodynamicCost",
    "ThermodynamicEthics",
    "DependencyManager",
]

# Verwijder None waarden uit __all__ (voor modules die niet geladen zijn)
__all__ = [name for name in __all__ if globals().get(name) is not None]


# ---------------------------------------------------------------------------
# Helper functies
# ---------------------------------------------------------------------------
def get_available_modules() -> Dict[str, bool]:
    """Retourneer een dictionary met de beschikbaarheid van optionele modules."""
    return {
        "base": _base_available,
        "event_bus": EventBus is not None,
        "adaptive_thresholds": AdaptiveThresholds is not None,
        "chaos_detection": ChaosDetector is not None,
        "document_tracker": DocumentTracker is not None,
        "thermodynamic_cost": ThermodynamicCost is not None,
        "thermodynamic_ethics": ThermodynamicEthics is not None,
        "dependencies": DependencyManager is not None,
    }


def initialize_core(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Initialiseer de core module en retourneer status.

    Args:
        config: Optionele configuratie dictionary.

    Returns:
        Status dictionary met versie en beschikbare modules.
    """
    status = {
        "success": _base_available,
        "version": __version__,
        "modules": get_available_modules(),
    }
    if _base_available:
        logger.info(f"Apeiron Core v{__version__} geïnitialiseerd")
        logger.info(f"Beschikbare modules: {sum(status['modules'].values())}")
    return status


# Automatische initialisatie tenzij expliciet uitgeschakeld
if os.environ.get("APEIRON_CORE_AUTO_INIT", "true").lower() == "true":
    initialize_core()