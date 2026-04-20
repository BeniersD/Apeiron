"""
THERMODYNAMIC ETHICS - Energie-efficiëntie als ethische maatstaf
================================================================================
Koppelt CPU/GPU-temperatuur en stroomverbruik aan ethische evaluatie.

Theoretische basis:
- Landauer's principe: informatie heeft minimale energiecost
- Biologisch rendement: elegante oplossingen zijn efficiënter
- Entropy feedback: hoge entropie = hoge kosten = laag rendement
"""

import psutil
import time
import numpy as np
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ThermodynamicEthics:
    """
    Evalueert de energetische kosten van ontdekkingen.
    
    Als een ontdekking veel energie kost maar weinig complexiteit
    oplevert (lage Lempel-Ziv), wordt deze als "biologisch onrendabel"
    beschouwd en afgewezen.
    """
    
    def __init__(self, efficiency_threshold: float = 0.1):
        self.efficiency_threshold = efficiency_threshold
        self.energy_history = []
        self.temp_history = []
        self.rejected_count = 0
        self.approved_count = 0
        
        # Power monitoring
        try:
            import pynvml
            self.nvml_available = True
            pynvml.nvmlInit()
            self.nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            logger.info("✅ NVIDIA NVML geïnitialiseerd voor power monitoring")
        except:
            self.nvml_available = False
    
    async def evaluate_discovery(self, 
                                discovery: Any,
                                computation_time: float,
                                complexity_score: float) -> Tuple[bool, Dict[str, float]]:
        """
        Evalueer of een ontdekking energetisch rendabel is.
        
        Args:
            discovery: De ontdekte structuur
            computation_time: Rekentijd in seconden
            complexity_score: Lempel-Ziv complexiteit (0-1)
        
        Returns:
            (goedgekeurd, metrics)
        """
        # Meet energieverbruik
        energy = await self._measure_energy(computation_time)
        
        # Meet temperatuur (als proxy voor entropie)
        temp = self._measure_temperature()
        
        # Bereken rendement (complexiteit per Joule)
        efficiency = complexity_score / (energy + 1e-10)
        
        # Update histories
        self.energy_history.append(energy)
        self.temp_history.append(temp)
        
        # Beperk historie
        if len(self.energy_history) > 100:
            self.energy_history.pop(0)
        if len(self.temp_history) > 100:
            self.temp_history.pop(0)
        
        metrics = {
            'energy_joules': energy,
            'temperature_c': temp,
            'complexity': complexity_score,
            'efficiency': efficiency
        }
        
        # Beslissing
        if efficiency >= self.efficiency_threshold:
            self.approved_count += 1
            logger.info(f"✅ Ontdekking goedgekeurd: efficiëntie={efficiency:.4f}")
            return True, metrics
        else:
            self.rejected_count += 1
            logger.warning(f"❌ Ontdekking afgekeurd: efficiëntie={efficiency:.4f} < {self.efficiency_threshold}")
            return False, metrics
    
    async def _measure_energy(self, computation_time: float) -> float:
        """Meet energieverbruik in Joules."""
        power = 0.0
        
        # CPU power
        cpu_percent = psutil.cpu_percent(interval=0.1)
        power += 65.0 * (cpu_percent / 100.0)  # 65W max CPU
        
        # GPU power (indien beschikbaar)
        if self.nvml_available:
            try:
                import pynvml
                gpu_power = pynvml.nvmlDeviceGetPowerUsage(self.nvml_handle) / 1000.0
                power += gpu_power
            except:
                pass
        
        return power * computation_time
    
    def _measure_temperature(self) -> float:
        """Meet CPU temperatuur."""
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return temps['coretemp'][0].current
        except:
            pass
        
        # Fallback: schatting op basis van CPU gebruik
        cpu_percent = psutil.cpu_percent()
        return 40.0 + cpu_percent * 0.3  # 40°C base + 0.3°C per % CPU
    
    def get_stats(self) -> Dict[str, Any]:
        """Haal statistieken op."""
        return {
            'approved': self.approved_count,
            'rejected': self.rejected_count,
            'avg_energy': np.mean(self.energy_history) if self.energy_history else 0,
            'avg_temp': np.mean(self.temp_history) if self.temp_history else 0,
            'efficiency_threshold': self.efficiency_threshold
        }


# ====================================================================
# INTEGRATIE MET ETHICAL RESEARCH ASSISTANT
# ====================================================================

class EthicalThermodynamicAssistant:
    """
    Uitbreiding van EthicalResearchAssistant met thermodynamische evaluatie.
    """
    
    def __init__(self, base_assistant, thermodynamic_ethics):
        self.base = base_assistant
        self.thermo = thermodynamic_ethics
    
    async def evaluate_proposal(self, proposal: Any, computation_time: float) -> Dict[str, Any]:
        """
        Evalueer een voorstel op zowel ethische als thermodynamische gronden.
        """
        # Ethische evaluatie (bestaand)
        ethical_result = self.base.evaluate_proposal(proposal)
        
        # Thermodynamische evaluatie
        complexity = self._estimate_complexity(proposal)
        thermo_approved, thermo_metrics = await self.thermo.evaluate_discovery(
            proposal, computation_time, complexity
        )
        
        # Gecombineerde beslissing
        overall_approved = ethical_result.get('approved', True) and thermo_approved
        
        result = {
            'approved': overall_approved,
            'ethical': ethical_result,
            'thermodynamic': thermo_metrics,
            'reason': self._generate_reason(ethical_result, thermo_approved)
        }
        
        return result
    
    def _estimate_complexity(self, proposal: Any) -> float:
        """Schat complexiteit van voorstel."""
        # Gebruik Lempel-Ziv op beschrijving
        import zlib
        
        desc = str(proposal)
        compressed = zlib.compress(desc.encode(), level=9)
        ratio = len(compressed) / len(desc)
        
        return 1.0 - min(1.0, ratio)
    
    def _generate_reason(self, ethical_result: Dict, thermo_approved: bool) -> str:
        """Genereer reden voor beslissing."""
        reasons = []
        
        if not ethical_result.get('approved', True):
            reasons.append(f"Ethisch: {ethical_result.get('reason', 'onbekend')}")
        
        if not thermo_approved:
            reasons.append("Thermodynamisch: onvoldoende rendement")
        
        return " | ".join(reasons) if reasons else "Goedgekeurd op alle criteria"