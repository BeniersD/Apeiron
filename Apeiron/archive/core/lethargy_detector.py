"""
LETHARGY DETECTOR - Detecteer en doorbreek creativiteitsplateaus
================================================================================
Monitort de creativiteit van het systeem en forceert Stille Stroming
wanneer het in een lokaal minimum blijft hangen.

Kenmerken:
- Continue monitoring van creativiteitsmetrics
- Trenddetectie voor dalende creativiteit
- Geforceerde interferentie-injectie
- Cooldown mechanisme om over-injectie te voorkomen
- Integratie met event bus
"""

import asyncio
import logging
import time
import random
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class LethargyLevel(Enum):
    """Ernst van gedetecteerde lethargie."""
    NONE = 0
    MILD = 1      # Licht dalende trend
    MODERATE = 2  # Significante daling
    SEVERE = 3    # Crisis - onmiddellijke interventie nodig


@dataclass
class CreativitySnapshot:
    """Snapshot van creativiteitsmetrics."""
    timestamp: float
    complexity: float
    interference_rate: float
    new_structures: int
    resolved_gaps: int
    creativity_score: float
    trend: float


class LethargyDetector:
    """
    Detecteert wanneer de AI in een lokaal minimum van creativiteit zit.
    
    Gebruikt meerdere metrics:
    - Lempel-Ziv complexiteit van nieuwe structuren
    - Aantal nieuwe interferenties per tijdseenheid
    - Aantal opgeloste ontologische gaps
    - Trend in bovenstaande metrics
    """
    
    def __init__(self, nexus, event_bus, 
                 check_interval: float = 60.0,
                 intervention_cooldown: float = 300.0):
        """
        Initialiseer lethargy detector.
        
        Args:
            nexus: OceanicNexus instantie
            event_bus: OceanEventBus voor communicatie
            check_interval: Hoe vaak checken (seconden)
            intervention_cooldown: Minimale tijd tussen interventies
        """
        self.nexus = nexus
        self.event_bus = event_bus
        self.check_interval = check_interval
        self.intervention_cooldown = intervention_cooldown
        
        # Metrics
        self.history: List[CreativitySnapshot] = []
        self.max_history = 100
        
        # Drempelwaarden
        self.thresholds = {
            'creativity_min': 0.3,           # Minimum creativiteitsscore
            'trend_negative': -0.02,          # Dalende trend per check
            'interference_min': 0.1,          # Minimum interferenties per minuut
            'structures_min': 1                # Minimum nieuwe structuren per uur
        }
        
        # Interventie tracking
        self.last_intervention = 0
        self.intervention_count = 0
        self.current_level = LethargyLevel.NONE
        
        # Stats
        self.stats = {
            'checks_performed': 0,
            'interventions': 0,
            'mild_warnings': 0,
            'severe_warnings': 0,
            'avg_creativity': 0.0,
            'start_time': time.time()
        }
        
        logger.info("="*60)
        logger.info("🧠 LETHARGY DETECTOR V13 GEÏNITIALISEERD")
        logger.info("="*60)
        logger.info(f"Check interval: {check_interval}s")
        logger.info(f"Intervention cooldown: {intervention_cooldown}s")
        logger.info("="*60)
    
    async def start_monitoring(self):
        """Start de monitoring loop."""
        logger.info("🔍 Lethargy monitoring gestart")
        
        while True:
            try:
                await self._check_creativity()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                logger.info("🛑 Lethargy monitoring gestopt")
                break
            except Exception as e:
                logger.error(f"❌ Lethargy check fout: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_creativity(self):
        """Voer één creativiteitscheck uit."""
        self.stats['checks_performed'] += 1
        
        # Verzamel metrics
        complexity = self._get_current_complexity()
        interference_rate = self._get_interference_rate()
        new_structures = self._get_new_structures_count()
        resolved_gaps = self._get_resolved_gaps_count()
        
        # Bereken creativiteitsscore
        creativity = self._calculate_creativity(
            complexity, interference_rate, new_structures, resolved_gaps
        )
        
        # Bereken trend
        trend = self._calculate_trend()
        
        # Maak snapshot
        snapshot = CreativitySnapshot(
            timestamp=time.time(),
            complexity=complexity,
            interference_rate=interference_rate,
            new_structures=new_structures,
            resolved_gaps=resolved_gaps,
            creativity_score=creativity,
            trend=trend
        )
        
        self.history.append(snapshot)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        # Update gemiddelde
        self.stats['avg_creativity'] = (
            self.stats['avg_creativity'] * 0.95 + creativity * 0.05
        )
        
        # Detecteer lethargie
        level = self._detect_lethargy_level(snapshot)
        self.current_level = level
        
        if level != LethargyLevel.NONE:
            await self._handle_lethargy(level, snapshot)
        
        # Log status periodiek
        if self.stats['checks_performed'] % 10 == 0:
            self._log_status()
    
    def _calculate_creativity(self, complexity: float, interference_rate: float,
                             new_structures: int, resolved_gaps: int) -> float:
        """
        Bereken gecombineerde creativiteitsscore.
        
        Args:
            complexity: Lempel-Ziv complexiteit (0-1)
            interference_rate: Interferenties per minuut (0-1 genormaliseerd)
            new_structures: Nieuwe structuren in laatste uur
            resolved_gaps: Opgeloste gaps in laatste uur
        
        Returns:
            Creativiteitsscore (0-1)
        """
        # Normaliseer nieuwe structuren (max 10 per uur = 1.0)
        structures_norm = min(1.0, new_structures / 10.0)
        
        # Normaliseer opgeloste gaps (max 5 per uur = 1.0)
        gaps_norm = min(1.0, resolved_gaps / 5.0)
        
        # Gewogen gemiddelde
        creativity = (
            0.4 * complexity +
            0.3 * interference_rate +
            0.2 * structures_norm +
            0.1 * gaps_norm
        )
        
        return max(0.0, min(1.0, creativity))
    
    def _calculate_trend(self) -> float:
        """Bereken trend in creativiteit (positief = stijgend)."""
        if len(self.history) < 3:
            return 0.0
        
        # Gebruik laatste 5 snapshots of alle beschikbare
        n = min(5, len(self.history))
        recent = self.history[-n:]
        
        scores = [s.creativity_score for s in recent]
        
        # Lineaire regressie voor trend
        x = np.arange(len(scores))
        slope = np.polyfit(x, scores, 1)[0]
        
        return float(slope)
    
    def _detect_lethargy_level(self, snapshot: CreativitySnapshot) -> LethargyLevel:
        """
        Detecteer ernst van lethargie.
        
        Args:
            snapshot: Huidige snapshot
        
        Returns:
            Lethargy level
        """
        # Check of creativiteit onder minimum
        if snapshot.creativity_score < self.thresholds['creativity_min']:
            return LethargyLevel.SEVERE
        
        # Check trend
        if snapshot.trend < self.thresholds['trend_negative'] * 3:
            return LethargyLevel.SEVERE
        elif snapshot.trend < self.thresholds['trend_negative'] * 2:
            return LethargyLevel.MODERATE
        elif snapshot.trend < self.thresholds['trend_negative']:
            return LethargyLevel.MILD
        
        # Check interferentie rate
        if snapshot.interference_rate < self.thresholds['interference_min']:
            if snapshot.creativity_score < 0.5:
                return LethargyLevel.MODERATE
        
        return LethargyLevel.NONE
    
    async def _handle_lethargy(self, level: LethargyLevel, snapshot: CreativitySnapshot):
        """
        Handel gedetecteerde lethargie af.
        
        Args:
            level: Ernst van lethargie
            snapshot: Huidige snapshot
        """
        now = time.time()
        
        # Check cooldown
        if now - self.last_intervention < self.intervention_cooldown:
            logger.debug(f"⏳ Interventie in cooldown ({now - self.last_intervention:.0f}s resterend)")
            return
        
        # Update stats
        self.stats['interventions'] += 1
        if level == LethargyLevel.SEVERE:
            self.stats['severe_warnings'] += 1
        elif level == LethargyLevel.MODERATE:
            self.stats['mild_warnings'] += 1
        
        logger.warning(f"\n⚠️ LETHARGIE GEDETECTEERD - niveau {level.name}")
        logger.warning(f"   Creativiteit: {snapshot.creativity_score:.3f}")
        logger.warning(f"   Trend: {snapshot.trend:.4f}")
        logger.warning(f"   Complexiteit: {snapshot.complexity:.3f}")
        
        # Stuur event
        await self.event_bus.emit(
            'lethargy_detected',
            {
                'level': level.name,
                'creativity': snapshot.creativity_score,
                'trend': snapshot.trend,
                'snapshot': {
                    'complexity': snapshot.complexity,
                    'interference_rate': snapshot.interference_rate,
                    'new_structures': snapshot.new_structures,
                    'resolved_gaps': snapshot.resolved_gaps
                }
            },
            'lethargy_detector',
            ttl=300.0
        )
        
        # Voer interventie uit
        if level == LethargyLevel.SEVERE:
            await self._severe_intervention()
        elif level == LethargyLevel.MODERATE:
            await self._moderate_intervention()
        else:
            await self._mild_intervention()
        
        self.last_intervention = now
        self.intervention_count += 1
    
    async def _mild_intervention(self):
        """Milde interventie: verhoog scan intensiteit."""
        logger.info("🔄 Milde interventie: scan intensiteit verhogen")
        
        if hasattr(self.nexus, 'resonance_scout'):
            # Verlaag interference drempel tijdelijk
            original = self.nexus.resonance_scout.interferentie_drempel
            self.nexus.resonance_scout.interferentie_drempel = original * 0.8
            
            # Na 10 minuten terugzetten
            async def restore():
                await asyncio.sleep(600)
                self.nexus.resonance_scout.interferentie_drempel = original
                logger.info("🔄 Interference drempel hersteld")
            
            asyncio.create_task(restore())
    
    async def _moderate_intervention(self):
        """Matige interventie: forceer extra interferenties."""
        logger.info("⚡ Matige interventie: forceer extra interferenties")
        
        if not hasattr(self.nexus, 'resonance_scout'):
            return
        
        scout = self.nexus.resonance_scout
        
        # Forceer 3 kritische interferenties
        for i in range(3):
            fake_plek = self._create_fake_interference(f"moderate_{i}")
            await scout._verwerk_kritische_plek(fake_plek)
            await asyncio.sleep(1)  # Spreid in tijd
    
    async def _severe_intervention(self):
        """Ernstige interventie: forceer Stille Stroming en verhoog quantum ruis."""
        logger.warning("🔥 ERNSTIGE INTERVENTIE: forceer Stille Stroming")
        
        if not hasattr(self.nexus, 'resonance_scout'):
            return
        
        scout = self.nexus.resonance_scout
        
        # Forceer 5 kritische interferenties
        for i in range(5):
            fake_plek = self._create_fake_interference(f"severe_{i}")
            await scout._verwerk_kritische_plek(fake_plek)
            await asyncio.sleep(0.5)
        
        # Verhoog quantum ruis in blind exploration
        if hasattr(self.nexus, 'blind_engine'):
            # Tijdelijke aanpassing
            original = self.nexus.blind_engine.quantum_scanner.metrics.get('ruis_niveau', 0.1)
            self.nexus.blind_engine.quantum_scanner.metrics['ruis_niveau'] = 0.3
            
            async def restore():
                await asyncio.sleep(900)  # 15 minuten
                self.nexus.blind_engine.quantum_scanner.metrics['ruis_niveau'] = original
                logger.info("🔄 Quantum ruis hersteld")
            
            asyncio.create_task(restore())
    
    def _create_fake_interference(self, suffix: str):
        """Creëer een fake interferentie voor interventie."""
        from resonance_scout import InterferentiePlek
        
        return InterferentiePlek(
            id=f"forced_{time.time()}_{suffix}",
            stroom_a_id="lethargy_source_a",
            stroom_b_id="lethargy_source_b",
            fase_verschil=random.uniform(0.05, 0.15),
            afstand=0.05,  # Altijd kritisch
            stabiliteit_potentieel=0.9,
            locatie_veld=np.random.randn(50),
            tijdstip=time.time()
        )
    
    def _get_current_complexity(self) -> float:
        """Haal huidige Lempel-Ziv complexiteit op."""
        if hasattr(self.nexus, 'true_ontogenesis'):
            stats = self.nexus.true_ontogenesis.get_stats()
            return stats.get('avg_complexity', 0.5)
        return 0.5
    
    def _get_interference_rate(self) -> float:
        """Haal interferentie rate op (per minuut, genormaliseerd)."""
        if not hasattr(self.nexus, 'resonance_scout'):
            return 0.0
        
        metrics = self.nexus.resonance_scout.metrics
        total = metrics.get('interferenties_gevonden', 0)
        uptime = time.time() - metrics.get('start_tijd', time.time())
        
        if uptime < 60:
            return 0.5  # Default voor nieuwe systemen
        
        rate_per_minute = total / (uptime / 60)
        # Normaliseer (max 10 per minuut = 1.0)
        return min(1.0, rate_per_minute / 10.0)
    
    def _get_new_structures_count(self) -> int:
        """Haal aantal nieuwe structuren in laatste uur op."""
        if not hasattr(self.nexus, 'true_ontogenesis'):
            return 0
        
        stats = self.nexus.true_ontogenesis.get_stats()
        return stats.get('structures_created', 0)
    
    def _get_resolved_gaps_count(self) -> int:
        """Haal aantal opgeloste gaps in laatste uur op."""
        if not hasattr(self.nexus, 'true_ontogenesis'):
            return 0
        
        metrics = self.nexus.true_ontogenesis.metrics
        return metrics.get('gaps_resolved', 0)
    
    def _log_status(self):
        """Log huidige status."""
        if not self.history:
            return
        
        latest = self.history[-1]
        
        logger.info(f"\n📊 LETHARGY DETECTOR STATUS")
        logger.info(f"   Huidig niveau: {self.current_level.name}")
        logger.info(f"   Creativiteit: {latest.creativity_score:.3f}")
        logger.info(f"   Trend: {latest.trend:.4f}")
        logger.info(f"   Interventies: {self.stats['interventions']}")
        logger.info(f"   Cooldown: {max(0, self.intervention_cooldown - (time.time() - self.last_intervention)):.0f}s")
    
    def get_stats(self) -> Dict[str, Any]:
        """Haal statistieken op."""
        return {
            **self.stats,
            'current_level': self.current_level.name,
            'last_intervention': self.last_intervention,
            'intervention_count': self.intervention_count,
            'history_size': len(self.history),
            'thresholds': self.thresholds.copy()
        }
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Haal geschiedenis op."""
        return [
            {
                'timestamp': s.timestamp,
                'creativity': s.creativity_score,
                'trend': s.trend,
                'complexity': s.complexity,
                'interference_rate': s.interference_rate
            }
            for s in self.history
        ]