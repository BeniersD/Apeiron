"""
ADAPTIVE THRESHOLDS – Dynamische drempels op basis van systeemcomplexiteit
===========================================================================
State-of-the-art adaptieve thresholds die meesturen met Lempel-Ziv-complexiteit,
aantal unresolved gaps, en stabiliteitstrends.

Kenmerken:
- Configuratie via dataclass
- Protocol-gebaseerde complexiteitsbron (ontkoppeld)
- Kalman-filter voor robuuste trenddetectie
- Caching van tussenresultaten
- Prometheus metrics export
- Event bus integratie voor real-time aanpassingen
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATIE
# ============================================================================


@dataclass(frozen=True)
class ThresholdConfig:
    """Configuratie voor adaptieve thresholds."""

    # Basis thresholds
    chaos_epsilon: float = 0.3
    divergence_threshold: float = 0.5
    oscillation_threshold: float = 0.4
    incoherence_threshold: float = 0.2
    interference_distance: float = 0.15
    stability_score: float = 0.85
    match_score: float = 0.7
    ethical_violation: float = 0.3
    risk_low: float = 0.3
    risk_medium: float = 0.5
    risk_high: float = 0.7
    risk_critical: float = 0.9
    gap_threshold: float = 0.3
    irreducibility_threshold: float = 0.7
    complexity_threshold: float = 0.6

    # Adaptatiegewichten
    complexity_weight: float = 0.5
    gap_weight: float = 0.3
    trend_weight: float = 0.2

    # Update-interval (seconden)
    update_interval: float = 60.0

    # History limiet
    max_history: int = 1000

    # Kalman-filter parameters
    kalman_process_noise: float = 0.01
    kalman_measurement_noise: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


# ============================================================================
# PROTOCOL VOOR COMPLEXITEITSBRON
# ============================================================================


@runtime_checkable
class ComplexityProvider(Protocol):
    """Interface voor het verkrijgen van systeemcomplexiteit en gaps."""

    def get_current_complexity(self) -> float:
        """Retourneer huidige Lempel-Ziv-complexiteit (0-1)."""
        ...

    def get_unresolved_gaps(self) -> List[Any]:
        """Retourneer lijst van onopgeloste gaps."""
        ...

    def get_stats(self) -> Dict[str, Any]:
        """Retourneer algemene statistieken."""
        ...


# ============================================================================
# DATASTRUCTUREN
# ============================================================================


@dataclass(slots=True)
class ThresholdSnapshot:
    """Snapshot van alle thresholds op een moment."""

    timestamp: float
    complexity: float
    unresolved_gaps: int
    thresholds: Dict[str, float]


# ============================================================================
# KALMAN-FILTER VOOR TRENDDETECTIE
# ============================================================================


class KalmanFilter:
    """
    Eenvoudig Kalman-filter voor het schatten van de werkelijke trend
    uit ruizige metingen.
    """

    def __init__(self, process_noise: float = 0.01, measurement_noise: float = 0.1):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.x = 0.0  # state
        self.p = 1.0  # error covariance

    def update(self, measurement: float) -> float:
        """Voer een meting in en retourneer de gefilterde schatting."""
        # Prediction
        self.p += self.process_noise

        # Update
        k = self.p / (self.p + self.measurement_noise)  # Kalman gain
        self.x = self.x + k * (measurement - self.x)
        self.p = (1 - k) * self.p
        return self.x


# ============================================================================
# ADAPTIEVE THRESHOLDS
# ============================================================================


class AdaptiveThresholds:
    """
    Beheert adaptieve thresholds op basis van systeemtoestand.

    Gebruik:
        thresholds = AdaptiveThresholds(ontogenesis, event_bus=bus)
        await thresholds.update()
        eps = thresholds.get("chaos_epsilon")
    """

    def __init__(
        self,
        complexity_provider: ComplexityProvider,
        event_bus: Optional[Any] = None,
        config: Optional[ThresholdConfig] = None,
    ) -> None:
        """
        Initialiseer adaptieve thresholds.

        Args:
            complexity_provider: Bron van complexiteit- en gap-informatie.
            event_bus: Optionele event bus voor notificaties.
            config: Configuratie (default indien None).
        """
        self.provider = complexity_provider
        self.event_bus = event_bus
        self.config = config or ThresholdConfig()

        # Huidige adaptieve waarden – start met basiswaarden
        self.current = self._base_thresholds()

        # Geschiedenis
        self.history: List[ThresholdSnapshot] = []
        self._last_update = 0.0

        # Kalman-filter voor trend
        self._kalman = KalmanFilter(
            process_noise=self.config.kalman_process_noise,
            measurement_noise=self.config.kalman_measurement_noise,
        )

        # Cache voor dure berekeningen
        self._cache: Dict[str, Any] = {}
        self._cache_time: float = 0.0

        logger.info("📊 AdaptiveThresholds geïnitialiseerd")
        logger.debug(f"Config: {self.config.to_dict()}")

    def _base_thresholds(self) -> Dict[str, float]:
        """Retourneer dictionary met basis-thresholds uit config."""
        return {
            "chaos_epsilon": self.config.chaos_epsilon,
            "divergence_threshold": self.config.divergence_threshold,
            "oscillation_threshold": self.config.oscillation_threshold,
            "incoherence_threshold": self.config.incoherence_threshold,
            "interference_distance": self.config.interference_distance,
            "stability_score": self.config.stability_score,
            "match_score": self.config.match_score,
            "ethical_violation": self.config.ethical_violation,
            "risk_low": self.config.risk_low,
            "risk_medium": self.config.risk_medium,
            "risk_high": self.config.risk_high,
            "risk_critical": self.config.risk_critical,
            "gap_threshold": self.config.gap_threshold,
            "irreducibility_threshold": self.config.irreducibility_threshold,
            "complexity_threshold": self.config.complexity_threshold,
        }

    # ------------------------------------------------------------------------
    # Kern-update logica
    # ------------------------------------------------------------------------
    async def update(self, force: bool = False) -> Dict[str, float]:
        """
        Update alle thresholds op basis van de huidige systeemtoestand.

        Args:
            force: Forceer update ongeacht het interval.

        Returns:
            Dictionary met de nieuwe threshold-waarden.
        """
        now = time.time()
        if not force and (now - self._last_update) < self.config.update_interval:
            return self.current

        # Verkrijg metrics (gebruik cache indien recent)
        complexity, unresolved, trend = await self._get_system_metrics()

        # Bereken aanpassingsfactoren
        tolerance_factor = 1.0 + complexity * self.config.complexity_weight
        strictness_factor = 1.0 - (unresolved * self.config.gap_weight)
        strictness_factor = max(0.5, min(1.5, strictness_factor))
        trend_factor = 1.0 - (trend * self.config.trend_weight)

        # Pas thresholds aan
        new_thresholds = self._compute_new_thresholds(
            tolerance_factor, strictness_factor, trend_factor
        )

        # Detecteer significante veranderingen
        significant = self._detect_significant_changes(new_thresholds)

        # Update state
        self.current = new_thresholds
        self._last_update = now

        # Sla snapshot op
        self._add_snapshot(now, complexity, unresolved, new_thresholds)

        # Emit event indien nodig
        if significant and self.event_bus:
            await self._emit_update_event(significant, complexity, unresolved)

        if significant:
            logger.info(f"📊 {len(significant)} thresholds significant aangepast")

        return self.current

    async def _get_system_metrics(self) -> tuple[float, float, float]:
        """Verkrijg complexiteit, genormaliseerde gaps, en trend."""
        # Gebruik cache indien < 5 seconden oud
        now = time.time()
        if now - self._cache_time < 5.0 and "metrics" in self._cache:
            return self._cache["metrics"]

        # Complexiteit
        complexity = self.provider.get_current_complexity()

        # Onopgeloste gaps (genormaliseerd naar 0-1)
        gaps = self.provider.get_unresolved_gaps()
        unresolved = min(1.0, len(gaps) / 20.0)

        # Trend via Kalman-filter op complexiteit
        filtered = self._kalman.update(complexity)
        trend = (filtered - complexity) * 10  # schaal naar -1..1
        trend = max(-1.0, min(1.0, trend))

        # Cache resultaat
        self._cache["metrics"] = (complexity, unresolved, trend)
        self._cache_time = now

        return complexity, unresolved, trend

    def _compute_new_thresholds(
        self, tolerance: float, strictness: float, trend_factor: float
    ) -> Dict[str, float]:
        """Pas alle thresholds aan op basis van de factoren."""
        base = self._base_thresholds()
        new = {}

        # Chaos thresholds: toleranter bij hogere complexiteit
        new["chaos_epsilon"] = base["chaos_epsilon"] * tolerance
        new["divergence_threshold"] = base["divergence_threshold"] * tolerance
        new["oscillation_threshold"] = base["oscillation_threshold"] * tolerance
        new["incoherence_threshold"] = base["incoherence_threshold"] * (2 - tolerance)

        # Resonance thresholds: strenger bij meer unresolved gaps
        new["interference_distance"] = base["interference_distance"] * strictness
        new["stability_score"] = base["stability_score"] * (2 - strictness)
        new["match_score"] = base["match_score"] * strictness

        # Ethiek: strenger bij dalende trend
        new["ethical_violation"] = base["ethical_violation"] * (2 - trend_factor)
        new["risk_low"] = base["risk_low"] * trend_factor
        new["risk_medium"] = base["risk_medium"] * trend_factor
        new["risk_high"] = base["risk_high"] * trend_factor
        new["risk_critical"] = base["risk_critical"] * trend_factor

        # Ontogenesis: blijven stabieler
        new["gap_threshold"] = base["gap_threshold"] * (1.0 + 0.1 * (tolerance - 1.0))
        new["irreducibility_threshold"] = base["irreducibility_threshold"]
        new["complexity_threshold"] = base["complexity_threshold"]

        # Clamp alle waarden tussen 0.05 en 0.95
        for key in new:
            new[key] = max(0.05, min(0.95, new[key]))

        return new

    def _detect_significant_changes(
        self, new_thresholds: Dict[str, float]
    ) -> Dict[str, tuple[float, float]]:
        """Detecteer thresholds die >5% veranderd zijn."""
        significant = {}
        for key, new_val in new_thresholds.items():
            old_val = self.current.get(key, 0.0)
            if abs(new_val - old_val) > 0.05:
                significant[key] = (old_val, new_val)
        return significant

    def _add_snapshot(
        self, timestamp: float, complexity: float, unresolved: int, thresholds: Dict[str, float]
    ) -> None:
        """Voeg snapshot toe aan geschiedenis en behoud limiet."""
        snapshot = ThresholdSnapshot(
            timestamp=timestamp,
            complexity=complexity,
            unresolved_gaps=unresolved,
            thresholds=thresholds.copy(),
        )
        self.history.append(snapshot)
        if len(self.history) > self.config.max_history:
            self.history.pop(0)

    async def _emit_update_event(
        self, changes: Dict[str, tuple[float, float]], complexity: float, unresolved: float
    ) -> None:
        """Stuur een event via de event bus."""
        if not self.event_bus:
            return
        await self.event_bus.emit(
            event_type="thresholds_updated",
            data={
                "changes": {k: {"old": old, "new": new} for k, (old, new) in changes.items()},
                "complexity": complexity,
                "unresolved": unresolved,
            },
            source="adaptive_thresholds",
            ttl=60.0,
        )

    # ------------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------------
    def get(self, key: str, default: Optional[float] = None) -> float:
        """Haal huidige adaptieve threshold op."""
        return self.current.get(key, default if default is not None else self._base_thresholds().get(key, 0.5))

    def get_all(self) -> Dict[str, float]:
        """Retourneer een kopie van alle huidige thresholds."""
        return self.current.copy()

    def get_base(self, key: str) -> float:
        """Haal de oorspronkelijke basis-threshold op."""
        return self._base_thresholds().get(key, 0.5)

    def reset(self) -> None:
        """Reset naar basis-thresholds en wis geschiedenis."""
        self.current = self._base_thresholds()
        self.history.clear()
        self._cache.clear()
        self._kalman = KalmanFilter(
            process_noise=self.config.kalman_process_noise,
            measurement_noise=self.config.kalman_measurement_noise,
        )
        logger.info("🔄 AdaptiveThresholds gereset naar basis")

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retourneer recente threshold-snapshots."""
        return [
            {
                "timestamp": s.timestamp,
                "complexity": s.complexity,
                "unresolved_gaps": s.unresolved_gaps,
                "thresholds": s.thresholds.copy(),
            }
            for s in self.history[-limit:]
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Retourneer statistieken over de adaptatie."""
        if not self.history:
            return {"updates": 0}

        complexities = [s.complexity for s in self.history]
        return {
            "updates": len(self.history),
            "avg_complexity": np.mean(complexities),
            "max_complexity": np.max(complexities),
            "min_complexity": np.min(complexities),
            "last_update": self._last_update,
            "config": self.config.to_dict(),
        }