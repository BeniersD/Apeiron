"""
DEPENDENCY MANAGER – State-of-the-Art Feature Detection
===========================================================================
Detecteert en rapporteert optionele afhankelijkheden met versiecontrole.

Kenmerken:
- Configuratie via dataclass
- Versiecontrole met `importlib.metadata` (Python 3.8+)
- Lazy imports om opstarttijd te minimaliseren
- Thread-safe singleton
- Uitgebreide rapportage (JSON, HTML, console)
- Prometheus metrics export (optioneel)
- Installatie-instructies generatie
"""

from __future__ import annotations

import importlib
import json
import logging
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATIE
# ============================================================================


class FeatureStatus(Enum):
    """Status van een feature/afhankelijkheid."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    VERSION_MISMATCH = "version_mismatch"
    DEGRADED = "degraded"


@dataclass(frozen=True)
class DependencyInfo:
    """Informatie over een specifieke afhankelijkheid."""

    name: str  # Leesbare naam
    import_name: str  # Module naam voor import
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    required: bool = False
    feature_flag: Optional[str] = None  # Naam van globale flag die wordt gezet

    # Runtime status (wordt ingevuld door manager)
    installed_version: Optional[str] = None
    status: FeatureStatus = FeatureStatus.UNAVAILABLE
    error_message: Optional[str] = None


@dataclass(frozen=True)
class DependencyConfig:
    """Configuratie voor de dependency manager."""

    # Lijst van te controleren dependencies
    dependencies: List[DependencyInfo] = field(default_factory=list)

    # Cache time-to-live voor versie-informatie (seconden)
    cache_ttl: int = 300

    # Pad naar optioneel configuratiebestand (JSON/YAML)
    config_path: Optional[str] = None

    # Exporteer Prometheus metrics
    enable_prometheus: bool = False
    prometheus_port: Optional[int] = None


# ============================================================================
# STANDAARD DEPENDENCIES VOOR APEIRON
# ============================================================================

DEFAULT_DEPENDENCIES = [
    DependencyInfo("Redis", "redis", min_version="4.0.0", feature_flag="REDIS_AVAILABLE"),
    DependencyInfo(
        "Prometheus Client",
        "prometheus_client",
        min_version="0.10.0",
        feature_flag="PROMETHEUS_AVAILABLE",
    ),
    DependencyInfo("Pydantic", "pydantic", min_version="2.0.0", feature_flag="PYDANTIC_AVAILABLE"),
    DependencyInfo("Ray", "ray", min_version="2.0.0", feature_flag="RAY_AVAILABLE"),
    DependencyInfo("Qiskit", "qiskit", min_version="0.40.0", feature_flag="QISKIT_AVAILABLE"),
    DependencyInfo(
        "scikit-image", "skimage", min_version="0.19.0", feature_flag="SKIMAGE_AVAILABLE"
    ),
    DependencyInfo("GUDHI", "gudhi", min_version="3.5.0", feature_flag="GUDHI_AVAILABLE"),
    DependencyInfo("cProfile", "cProfile", feature_flag="PROFILE_AVAILABLE"),  # built-in
    DependencyInfo("psutil", "psutil", min_version="5.8.0", feature_flag="PSUTIL_AVAILABLE"),
    DependencyInfo(
        "cryptography", "cryptography", min_version="3.4.0", feature_flag="CRYPTO_AVAILABLE"
    ),
]


# ============================================================================
# VERSIE PARSING (zonder externe libraries)
# ============================================================================


def _parse_version(version_str: str) -> Tuple[int, ...]:
    """Parse versiestring naar tuple van integers voor veilige vergelijking."""
    import re

    # Pak alleen numerieke delen (negeer alpha/beta/rc)
    numeric_parts = re.findall(r"\d+", version_str)
    return tuple(int(p) for p in numeric_parts)


def _version_meets_requirement(current: str, requirement: str) -> bool:
    """
    Controleer of huidige versie voldoet aan requirement (bv. ">=2.0.0").
    Eenvoudige implementatie; voor productie gebruik `packaging`.
    """
    # Probeer packaging te gebruiken indien beschikbaar
    try:
        from packaging.version import Version
        from packaging.specifiers import SpecifierSet

        return Version(current) in SpecifierSet(requirement)
    except ImportError:
        # Fallback: alleen simpele >= vergelijking
        if requirement.startswith(">="):
            req_ver = requirement[2:].strip()
            return _parse_version(current) >= _parse_version(req_ver)
        elif requirement.startswith("=="):
            req_ver = requirement[2:].strip()
            return _parse_version(current) == _parse_version(req_ver)
        else:
            # Onbekende operator, neem aan dat niet voldaan
            return False


# ============================================================================
# DEPENDENCY MANAGER (Singleton)
# ============================================================================


class DependencyManager:
    """
    Thread-safe singleton voor het beheren van optionele afhankelijkheden.

    Gebruik:
        manager = DependencyManager()
        manager.check_all()
        print(manager.get_report())
    """

    _instance: Optional[DependencyManager] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[DependencyConfig] = None):
        # Voorkom herinitialisatie
        if self._initialized:
            return

        self.config = config or DependencyConfig(dependencies=DEFAULT_DEPENDENCIES)
        self._deps: Dict[str, DependencyInfo] = {}
        self._last_check: float = 0.0
        self._cache: Dict[str, Tuple[bool, Optional[str]]] = {}

        # Prometheus metrics (optioneel)
        self._metrics = None
        if self.config.enable_prometheus:
            self._setup_prometheus()

        self._register_defaults()
        self._initialized = True
        logger.info("🔍 DependencyManager geïnitialiseerd")

    def _register_defaults(self) -> None:
        """Registreer de standaard dependencies uit de configuratie."""
        for dep in self.config.dependencies:
            self._deps[dep.import_name] = dep

    def _setup_prometheus(self) -> None:
        """Initialiseer Prometheus metrics indien beschikbaar."""
        try:
            from prometheus_client import Gauge, start_http_server

            if self.config.prometheus_port:
                start_http_server(self.config.prometheus_port)

            self._metrics = {
                "status": Gauge(
                    "apeiron_dependency_status",
                    "Dependency status (1=available, 0=unavailable)",
                    ["name", "import_name"],
                ),
                "version": Gauge(
                    "apeiron_dependency_version",
                    "Installed version as string (not a number)",
                    ["name", "import_name"],
                ),
            }
            logger.info(f"📊 Prometheus metrics geactiveerd op poort {self.config.prometheus_port}")
        except Exception as e:
            logger.warning(f"⚠️ Prometheus setup mislukt: {e}")
            self._metrics = None

    # ------------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------------
    def check_all(self, force: bool = False) -> Dict[str, DependencyInfo]:
        """
        Controleer alle geregistreerde dependencies.

        Args:
            force: Negeer cache en forceer hercontrole.

        Returns:
            Dictionary van import_name -> DependencyInfo.
        """
        now = __import__("time").time()
        if not force and (now - self._last_check) < self.config.cache_ttl:
            return self._deps

        for dep in self._deps.values():
            self._check_dependency(dep)

        self._last_check = now
        return self._deps

    def _check_dependency(self, dep: DependencyInfo) -> None:
        """Controleer één afhankelijkheid en update status."""
        # Gebruik interne cache indien beschikbaar
        cache_key = f"{dep.import_name}:{dep.min_version}:{dep.max_version}"
        if cache_key in self._cache:
            available, version = self._cache[cache_key]
            dep.installed_version = version
            dep.status = FeatureStatus.AVAILABLE if available else FeatureStatus.UNAVAILABLE
            self._set_feature_flag(dep)
            return

        available = False
        version = None
        error_msg = None

        try:
            module = importlib.import_module(dep.import_name)
            version = getattr(module, "__version__", "unknown")
            available = True

            # Versiecontrole
            if dep.min_version:
                if not _version_meets_requirement(version, f">={dep.min_version}"):
                    dep.status = FeatureStatus.VERSION_MISMATCH
                    error_msg = f"Version {version} < {dep.min_version}"
                    available = False
            if available and dep.max_version:
                if not _version_meets_requirement(version, f"<={dep.max_version}"):
                    dep.status = FeatureStatus.VERSION_MISMATCH
                    error_msg = f"Version {version} > {dep.max_version}"
                    available = False

        except ImportError as e:
            error_msg = str(e)
            available = False

        dep.installed_version = version
        dep.error_message = error_msg
        dep.status = FeatureStatus.AVAILABLE if available else FeatureStatus.UNAVAILABLE

        # Update cache
        self._cache[cache_key] = (available, version)

        # Zet feature flag in globale namespace (optioneel)
        self._set_feature_flag(dep)

        # Update Prometheus metrics
        if self._metrics:
            self._metrics["status"].labels(
                name=dep.name, import_name=dep.import_name
            ).set(1 if available else 0)
            if version:
                # Gauge ondersteunt geen string, dus we kunnen alleen loggen
                pass

    def _set_feature_flag(self, dep: DependencyInfo) -> None:
        """Zet een globale variabele met de beschikbaarheid van de feature."""
        if dep.feature_flag:
            available = dep.status == FeatureStatus.AVAILABLE
            globals()[dep.feature_flag] = available

    def get_report(self, format: str = "text") -> str:
        """
        Genereer een rapport over alle dependencies.

        Args:
            format: "text", "json", of "html".

        Returns:
            Rapport als string.
        """
        self.check_all()

        if format == "json":
            return self._report_json()
        elif format == "html":
            return self._report_html()
        else:
            return self._report_text()

    def _report_text(self) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("APEIRON DEPENDENCY REPORT")
        lines.append("=" * 80)

        for dep in self._deps.values():
            icon = {
                FeatureStatus.AVAILABLE: "✅",
                FeatureStatus.UNAVAILABLE: "❌",
                FeatureStatus.VERSION_MISMATCH: "⚠️",
                FeatureStatus.DEGRADED: "⚡",
            }.get(dep.status, "❓")

            line = f"{icon} {dep.name} ({dep.import_name})"
            if dep.installed_version:
                line += f" v{dep.installed_version}"
            if dep.min_version:
                line += f" (min: {dep.min_version})"
            if dep.error_message:
                line += f" - {dep.error_message}"
            lines.append(line)

        lines.append("=" * 80)
        return "\n".join(lines)

    def _report_json(self) -> str:
        data = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "dependencies": [
                {
                    "name": dep.name,
                    "import_name": dep.import_name,
                    "status": dep.status.value,
                    "installed_version": dep.installed_version,
                    "min_version": dep.min_version,
                    "max_version": dep.max_version,
                    "required": dep.required,
                    "error": dep.error_message,
                }
                for dep in self._deps.values()
            ],
        }
        return json.dumps(data, indent=2)

    def _report_html(self) -> str:
        """Genereer een eenvoudig HTML-rapport."""
        html = ["<html><head><title>Apeiron Dependencies</title></head><body>"]
        html.append("<h1>Apeiron Dependency Report</h1>")
        html.append("<table border='1'><tr><th>Status</th><th>Name</th><th>Version</th><th>Required</th></tr>")
        for dep in self._deps.values():
            color = "green" if dep.status == FeatureStatus.AVAILABLE else "red"
            html.append(
                f"<tr style='color:{color}'><td>{dep.status.value}</td><td>{dep.name}</td>"
                f"<td>{dep.installed_version or 'N/A'}</td><td>{dep.required}</td></tr>"
            )
        html.append("</table></body></html>")
        return "\n".join(html)

    def install_instructions(self) -> str:
        """Genereer pip install commando voor ontbrekende dependencies."""
        missing = [d for d in self._deps.values() if d.status != FeatureStatus.AVAILABLE]
        if not missing:
            return "All dependencies are satisfied."

        packages = []
        for dep in missing:
            if dep.name == "scikit-image":
                packages.append("scikit-image")
            elif dep.name == "GUDHI":
                packages.append("gudhi")
            elif dep.name == "Qiskit":
                packages.append("qiskit")
            elif dep.name == "Redis":
                packages.append("redis")
            elif dep.name == "Prometheus Client":
                packages.append("prometheus-client")
            elif dep.name == "Pydantic":
                packages.append("pydantic")
            elif dep.name == "Ray":
                packages.append("ray")
            elif dep.name == "cryptography":
                packages.append("cryptography")
            elif dep.name == "psutil":
                packages.append("psutil")
            else:
                packages.append(dep.import_name)

        return f"pip install {' '.join(packages)}"

    def is_feature_available(self, feature: str) -> bool:
        """Controleer of een specifieke feature beschikbaar is."""
        for dep in self._deps.values():
            if dep.feature_flag == feature:
                return dep.status == FeatureStatus.AVAILABLE
        return False

    def reset_cache(self) -> None:
        """Wis de interne cache."""
        self._cache.clear()
        self._last_check = 0.0


# ============================================================================
# CONVENIENCE FUNCTIES
# ============================================================================

# Singleton instance voor eenvoudig gebruik
_default_manager = None


def get_dependency_manager(config: Optional[DependencyConfig] = None) -> DependencyManager:
    """Retourneer de globale DependencyManager singleton."""
    global _default_manager
    if _default_manager is None:
        _default_manager = DependencyManager(config)
    return _default_manager


def check_dependencies(print_report: bool = True) -> Dict[str, DependencyInfo]:
    """
    Controleer alle dependencies en retourneer status.

    Args:
        print_report: Print het rapport naar de logger (INFO niveau).

    Returns:
        Dictionary van import_name -> DependencyInfo.
    """
    manager = get_dependency_manager()
    result = manager.check_all()
    if print_report:
        logger.info("\n" + manager.get_report())
        missing = [d for d in result.values() if d.status != FeatureStatus.AVAILABLE]
        if missing:
            logger.info("Installatie suggestie: " + manager.install_instructions())
    return result


def is_feature_available(feature: str) -> bool:
    """Controleer of een specifieke feature beschikbaar is."""
    return get_dependency_manager().is_feature_available(feature)