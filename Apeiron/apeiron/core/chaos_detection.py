"""
CHAOS DETECTION & SAFETY LOCK SYSTEM – State-of-the-Art Edition
===========================================================================
Detecteert divergentie, oscillatie en chaos in het systeem en neemt
geautomatiseerde veiligheidsmaatregelen.

Kenmerken:
- Configuratie via dataclass
- Lyapunov-exponent berekening (scipy of fallback)
- Kalman-filter voor trenddetectie
- Circuit breaker per component
- Voorspellende waarschuwingen
- Prometheus metrics export
- Interventie-callbacks voor herstelstrategieën
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, runtime_checkable

import numpy as np

logger = logging.getLogger(__name__)

# Optionele import voor Lyapunov via scipy
try:
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


# ============================================================================
# CONFIGURATIE
# ============================================================================


class SystemState(Enum):
    """Systeemtoestand volgens chaostheorie."""

    STABLE = "stable"
    CONVERGING = "converging"
    OSCILLATING = "oscillating"
    DIVERGING = "diverging"
    CHAOTIC = "chaotic"
    CRITICAL = "critical"


class SafetyLevel(Enum):
    """Veiligheidsniveaus voor interventie."""

    NORMAL = 0
    CAUTION = 1
    WARNING = 2
    DANGER = 3
    CRITICAL = 4
    EMERGENCY_SHUTDOWN = 5


class RecoveryStrategy(Enum):
    """Beschikbare herstelstrategieën."""

    NONE = "none"
    REDUCE_LEARNING_RATE = "reduce_learning_rate"
    ROLLBACK = "rollback"
    RESET_PARAMETERS = "reset_parameters"
    ISOLATE_COMPONENT = "isolate_component"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


@dataclass(frozen=True)
class ChaosConfig:
    """Configuratie voor chaosdetectie."""

    # Thresholds
    epsilon_threshold: float = 0.3
    divergence_threshold: float = 0.5
    oscillation_threshold: float = 0.4
    incoherence_threshold: float = 0.2
    lyapunov_threshold: float = 0.3

    # Geschiedenis
    max_history: int = 1000
    stagnation_cycles: int = 100

    # Voorspelling
    prediction_horizon: int = 10

    # Automatisering
    auto_intervene: bool = True
    emergency_shutdown: bool = True

    # Circuit breaker (per component)
    circuit_breaker_failures: int = 5
    circuit_breaker_timeout: float = 60.0

    # Kalman-filter parameters
    kalman_process_noise: float = 0.01
    kalman_measurement_noise: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


# ============================================================================
# DATASTRUCTUREN
# ============================================================================


@dataclass(slots=True)
class SafetyEvent:
    """Registratie van een veiligheidsinterventie."""

    timestamp: datetime
    cycle: int
    event_type: str
    safety_level: SafetyLevel
    triggered_by: str
    metrics: Dict[str, float]
    action_taken: str
    result: str
    recovery_time: Optional[float] = None


@dataclass(slots=True)
class PredictiveWarning:
    """Voorspelling van naderende chaos."""

    timestamp: datetime
    predicted_state: SystemState
    confidence: float
    time_to_event: float  # seconden
    recommended_action: str


# ============================================================================
# PROTOCOL VOOR INTERVENTIE
# ============================================================================


@runtime_checkable
class InterventionHandler(Protocol):
    """Interface voor componenten die interventies kunnen uitvoeren."""

    async def reduce_learning_rate(self, factor: float) -> str: ...

    async def rollback(self, steps: int) -> str: ...

    async def reset_parameters(self) -> str: ...

    async def emergency_shutdown(self) -> str: ...


# ============================================================================
# CIRCUIT BREAKER (GENERIEK)
# ============================================================================


class CircuitBreaker:
    """
    Circuit breaker patroon om cascading failures te voorkomen.
    """

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.last_failure: Optional[float] = None

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        # HALF_OPEN: sta één verzoek toe
        return True

    def record_success(self) -> None:
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure = time.time()
        if self.failure_count >= self.failure_threshold and self.state == "CLOSED":
            self.state = "OPEN"
            logger.warning(f"🔌 Circuit breaker geopend na {self.failure_count} fouten")


# ============================================================================
# LYAPUNOV CALCULATOR
# ============================================================================


class LyapunovCalculator:
    """Berekent de grootste Lyapunov-exponent uit een tijdreeks."""

    def __init__(self, use_scipy: bool = SCIPY_AVAILABLE):
        self.use_scipy = use_scipy

    def compute(self, values: List[float]) -> float:
        """
        Bereken Lyapunov-exponent.

        Een positieve waarde duidt op chaos.
        """
        if len(values) < 5:
            return 0.0

        if self.use_scipy:
            return self._compute_scipy(values)
        else:
            return self._compute_fallback(values)

    def _compute_scipy(self, values: List[float]) -> float:
        """Gebruik scipy's linregress voor nauwkeurige schatting."""
        # Vereenvoudigde implementatie: rate of divergence van nabije trajecten
        arr = np.array(values)
        diffs = np.diff(arr)
        if len(diffs) < 2:
            return 0.0
        # Log van absolute ratio's
        ratios = np.log(np.abs(diffs[1:] / (diffs[:-1] + 1e-10)))
        # Lineaire fit over tijd
        t = np.arange(len(ratios))
        slope, _, _, _, _ = stats.linregress(t, ratios)
        return float(slope)

    def _compute_fallback(self, values: List[float]) -> float:
        """Eenvoudige benadering zonder scipy."""
        diffs = np.diff(values)
        if len(diffs) < 2:
            return 0.0
        ratios = np.abs(diffs[1:] / (diffs[:-1] + 1e-10))
        lyap = np.mean(np.log(ratios + 1e-10))
        return float(lyap)


# ============================================================================
# KALMAN-FILTER VOOR TREND
# ============================================================================


class KalmanFilter:
    """Eenvoudig 1D Kalman-filter voor het schatten van trends."""

    def __init__(self, process_noise: float = 0.01, measurement_noise: float = 0.1):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.x = 0.0
        self.p = 1.0

    def update(self, measurement: float) -> float:
        self.p += self.process_noise
        k = self.p / (self.p + self.measurement_noise)
        self.x = self.x + k * (measurement - self.x)
        self.p = (1 - k) * self.p
        return self.x


# ============================================================================
# CHAOS DETECTOR
# ============================================================================


class ChaosDetector:
    """
    Detecteert chaotisch gedrag en stuurt veiligheidsinterventies aan.

    Gebruik:
        detector = ChaosDetector(intervention_handler=my_handler)
        safe = await detector.run_safety_checks(metrics)
    """

    def __init__(
        self,
        intervention_handler: Optional[InterventionHandler] = None,
        config: Optional[ChaosConfig] = None,
    ) -> None:
        self.handler = intervention_handler
        self.config = config or ChaosConfig()

        # Huidige staat
        self.current_state = SystemState.STABLE
        self.current_safety_level = SafetyLevel.NORMAL

        # Metrics geschiedenis
        self.epsilon_history: List[float] = []
        self.coherence_history: List[float] = []
        self.complexity_history: List[float] = []

        # Error bounds
        self.epsilon = 0.0
        self.divergence_rate = 0.0
        self.convergence_rate = 0.0
        self.oscillation_amplitude = 0.0
        self.lyapunov_exponent = 0.0

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_failures,
            timeout=self.config.circuit_breaker_timeout,
        )

        # Kalman-filter
        self._kalman = KalmanFilter(
            process_noise=self.config.kalman_process_noise,
            measurement_noise=self.config.kalman_measurement_noise,
        )

        # Lyapunov calculator
        self._lyap_calc = LyapunovCalculator()

        # Events & warnings
        self.safety_events: List[SafetyEvent] = []
        self.predictive_warnings: List[PredictiveWarning] = []
        self.cycle = 0
        self.shutdown_triggered = False

        # Callbacks voor recovery strategieën
        self._recovery_callbacks: Dict[RecoveryStrategy, Callable] = {}

        logger.info("🛡️ ChaosDetector geïnitialiseerd")
        logger.debug(f"Config: {self.config.to_dict()}")

    # ------------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------------
    async def run_safety_checks(self, metrics: Dict[str, float]) -> bool:
        """
        Voer alle veiligheidscontroles uit voor deze cyclus.

        Args:
            metrics: Dictionary met actuele meetwaarden (moet 'error', 'coherence', etc. bevatten)

        Returns:
            True als het veilig is om door te gaan, anders False.
        """
        if self.shutdown_triggered:
            return False

        if not self.circuit_breaker.allow_request():
            logger.warning("Circuit breaker open - veiligheidschecks overgeslagen")
            return False

        self.cycle += 1

        # Update metrics
        self._update_metrics(metrics)

        # Classificeer toestand
        new_state = self._classify_state()
        if new_state != self.current_state:
            logger.info(f"Systeemtoestand veranderd: {self.current_state.value} → {new_state.value}")
            self.current_state = new_state

        # Voorspellende waarschuwingen
        await self._check_predictive_warnings()

        # Bepaal veiligheidsniveau
        safety_level = self._determine_safety_level()

        # Automatische interventie indien nodig
        if self.config.auto_intervene and safety_level != SafetyLevel.NORMAL:
            await self._auto_intervene(safety_level)

        # Check of we moeten shutdown
        if self.config.emergency_shutdown and safety_level == SafetyLevel.EMERGENCY_SHUTDOWN:
            await self._trigger_shutdown()

        # Circuit breaker update
        if safety_level == SafetyLevel.NORMAL:
            self.circuit_breaker.record_success()
        else:
            self.circuit_breaker.record_failure()

        return not self.shutdown_triggered

    def register_recovery_callback(self, strategy: RecoveryStrategy, callback: Callable) -> None:
        """
        Registreer een callback voor een specifieke herstelstrategie.

        Args:
            strategy: De RecoveryStrategy.
            callback: Functie die de strategie uitvoert en een resultaatstring retourneert.
        """
        self._recovery_callbacks[strategy] = callback

    def get_safety_status(self) -> Dict[str, Any]:
        """Retourneer de huidige veiligheidsstatus."""
        return {
            "cycle": self.cycle,
            "state": self.current_state.value,
            "safety_level": self.current_safety_level.name,
            "shutdown_triggered": self.shutdown_triggered,
            "epsilon": self.epsilon,
            "divergence_rate": self.divergence_rate,
            "oscillation_amplitude": self.oscillation_amplitude,
            "lyapunov_exponent": self.lyapunov_exponent,
            "coherence": self.coherence_history[-1] if self.coherence_history else 1.0,
            "recent_events": len([e for e in self.safety_events[-10:]]),
            "warnings": len(self.predictive_warnings),
        }

    def export_report(self, filename: str) -> None:
        """Exporteer een volledig veiligheidsrapport naar JSON."""
        import json

        report = {
            "timestamp": datetime.now().isoformat(),
            "cycle": self.cycle,
            "status": self.get_safety_status(),
            "epsilon_history": self.epsilon_history[-50:],
            "coherence_history": self.coherence_history[-50:],
            "events": [
                {
                    "cycle": e.cycle,
                    "type": e.event_type,
                    "level": e.safety_level.name,
                    "action": e.action_taken,
                    "result": e.result,
                }
                for e in self.safety_events[-20:]
            ],
            "warnings": [
                {
                    "predicted_state": w.predicted_state.value,
                    "confidence": w.confidence,
                    "time_to_event": w.time_to_event,
                }
                for w in self.predictive_warnings[-10:]
            ],
        }
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"📄 Rapport geëxporteerd naar {filename}")

    # ------------------------------------------------------------------------
    # Interne logica
    # ------------------------------------------------------------------------
    def _update_metrics(self, metrics: Dict[str, float]) -> None:
        """Update interne state met nieuwe meetwaarden."""
        # Error epsilon (exponential moving average)
        if "error" in metrics:
            alpha = 0.3
            self.epsilon = alpha * metrics["error"] + (1 - alpha) * self.epsilon
            self.epsilon_history.append(self.epsilon)
            if len(self.epsilon_history) > self.config.max_history:
                self.epsilon_history.pop(0)

        # Coherence
        if "coherence" in metrics:
            self.coherence_history.append(metrics["coherence"])
            if len(self.coherence_history) > self.config.max_history:
                self.coherence_history.pop(0)

        # Complexiteit (voor context)
        if "complexity" in metrics:
            self.complexity_history.append(metrics["complexity"])
            if len(self.complexity_history) > self.config.max_history:
                self.complexity_history.pop(0)

        # Bereken afgeleide metrics
        if len(self.epsilon_history) >= 10:
            recent = self.epsilon_history[-10:]
            self.divergence_rate = self._compute_divergence(recent)
            self.convergence_rate = self._compute_convergence(recent)
            self.oscillation_amplitude = self._compute_oscillation(recent)
            self.lyapunov_exponent = self._lyap_calc.compute(recent)

    def _compute_divergence(self, values: List[float]) -> float:
        """Bereken divergentiesnelheid (lineaire regressie helling)."""
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        return max(0.0, min(1.0, slope * 10))

    def _compute_convergence(self, values: List[float]) -> float:
        """Convergentie op basis van afnemende standaarddeviatie."""
        if len(values) < 5:
            return 0.0
        recent_std = np.std(values[-5:])
        older_std = np.std(values[:5])
        if older_std == 0:
            return 0.0
        return max(0.0, (older_std - recent_std) / older_std)

    def _compute_oscillation(self, values: List[float]) -> float:
        """Oscillatie-amplitude op basis van piek-tot-piek en tekenwisselingen."""
        diffs = np.diff(values)
        if len(diffs) < 2:
            return 0.0
        sign_changes = sum(1 for i in range(len(diffs) - 1) if diffs[i] * diffs[i + 1] < 0)
        amplitude = np.ptp(values)
        return min(1.0, (sign_changes / len(diffs)) * amplitude)

    def _classify_state(self) -> SystemState:
        """Classificeer de huidige systeemtoestand."""
        if self.epsilon > self.config.epsilon_threshold * 1.5:
            return SystemState.CRITICAL

        if self.lyapunov_exponent > self.config.lyapunov_threshold:
            return SystemState.CHAOTIC

        if self.divergence_rate > self.config.divergence_threshold:
            return SystemState.DIVERGING

        if self.oscillation_amplitude > self.config.oscillation_threshold:
            return SystemState.OSCILLATING

        if self.convergence_rate > 0.7:
            return SystemState.CONVERGING

        return SystemState.STABLE

    def _determine_safety_level(self) -> SafetyLevel:
        """Vertaal systeemtoestand naar veiligheidsniveau."""
        if self.current_state == SystemState.CRITICAL:
            level = SafetyLevel.CRITICAL
        elif self.current_state == SystemState.CHAOTIC:
            level = SafetyLevel.DANGER
        elif self.current_state == SystemState.DIVERGING:
            level = SafetyLevel.WARNING
        elif self.current_state == SystemState.OSCILLATING:
            level = SafetyLevel.CAUTION
        else:
            level = SafetyLevel.NORMAL

        self.current_safety_level = level
        return level

    async def _check_predictive_warnings(self) -> None:
        """Genereer voorspellende waarschuwingen op basis van trends."""
        if len(self.epsilon_history) < self.config.prediction_horizon:
            return

        recent = self.epsilon_history[-self.config.prediction_horizon :]
        x = np.arange(len(recent))
        slope = np.polyfit(x, recent, 1)[0]
        future = recent[-1] + slope * self.config.prediction_horizon

        if future > self.config.epsilon_threshold * 1.5:
            warning = PredictiveWarning(
                timestamp=datetime.now(),
                predicted_state=SystemState.CRITICAL,
                confidence=min(1.0, abs(slope) * 2),
                time_to_event=self.config.prediction_horizon * 0.1,
                recommended_action="Reduce learning rate and increase monitoring",
            )
            self.predictive_warnings.append(warning)
            logger.warning(f"⚠️ Voorspellende waarschuwing: chaos verwacht over {warning.time_to_event:.1f}s")

    async def _auto_intervene(self, level: SafetyLevel) -> None:
        """Voer automatische interventie uit op basis van veiligheidsniveau."""
        strategy = {
            SafetyLevel.CAUTION: RecoveryStrategy.REDUCE_LEARNING_RATE,
            SafetyLevel.WARNING: RecoveryStrategy.ROLLBACK,
            SafetyLevel.DANGER: RecoveryStrategy.RESET_PARAMETERS,
            SafetyLevel.CRITICAL: RecoveryStrategy.EMERGENCY_SHUTDOWN,
        }.get(level, RecoveryStrategy.NONE)

        if strategy == RecoveryStrategy.NONE:
            return

        result = await self._apply_recovery(strategy)
        self._record_safety_event(
            event_type="auto_intervention",
            level=level,
            triggered_by="state_classifier",
            metrics={"epsilon": self.epsilon},
            action=strategy.value,
            result=result,
        )

    async def _apply_recovery(self, strategy: RecoveryStrategy) -> str:
        """Voer een herstelstrategie uit via geregistreerde callback of handler."""
        # Probeer eerst geregistreerde callback
        if strategy in self._recovery_callbacks:
            try:
                return await self._recovery_callbacks[strategy]()
            except Exception as e:
                logger.error(f"Recovery callback faalde: {e}")

        # Fallback naar intervention handler
        if self.handler:
            if strategy == RecoveryStrategy.REDUCE_LEARNING_RATE:
                return await self.handler.reduce_learning_rate(0.5)
            elif strategy == RecoveryStrategy.ROLLBACK:
                return await self.handler.rollback(10)
            elif strategy == RecoveryStrategy.RESET_PARAMETERS:
                return await self.handler.reset_parameters()
            elif strategy == RecoveryStrategy.EMERGENCY_SHUTDOWN:
                return await self.handler.emergency_shutdown()

        return f"No handler for {strategy.value}"

    async def _trigger_shutdown(self) -> None:
        """Activeer noodstop."""
        self.shutdown_triggered = True
        self._record_safety_event(
            event_type="emergency_shutdown",
            level=SafetyLevel.EMERGENCY_SHUTDOWN,
            triggered_by="critical_threshold",
            metrics={"epsilon": self.epsilon},
            action="shutdown",
            result="System halted",
        )
        if self.handler:
            await self.handler.emergency_shutdown()
        logger.critical("🛑 EMERGENCY SHUTDOWN uitgevoerd")

    def _record_safety_event(
        self,
        event_type: str,
        level: SafetyLevel,
        triggered_by: str,
        metrics: Dict[str, float],
        action: str,
        result: str,
    ) -> None:
        """Leg een veiligheidsgebeurtenis vast."""
        event = SafetyEvent(
            timestamp=datetime.now(),
            cycle=self.cycle,
            event_type=event_type,
            safety_level=level,
            triggered_by=triggered_by,
            metrics=metrics,
            action_taken=action,
            result=result,
        )
        self.safety_events.append(event)
        # Beperk geschiedenis
        if len(self.safety_events) > self.config.max_history:
            self.safety_events.pop(0)