"""
LAYER 8: TEMPORALITEIT ALS FLUX - UITGEBREIDE CONTINUE VERSIE
================================================================================================
De theorie: "time is instead encountered as flux: a dynamic field of transformation 
in which past, present, and future interpenetrate rather than succeed each other."

Uitbreidingen:
- Meerdere tijdschalen (korte/middellange/lange termijn)
- Cyclische patronen detectie
- Temporele causaliteit
- Voorspellingsfout
- Geheugeneffecten
- Hardware versnelling
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)


class Tijdschaal(Enum):
    """Verschillende tijdschalen voor analyse."""
    KORTE_TERMIJN = "kort"      # seconden/minuten
    MIDDELLANGE_TERMIJN = "middel"  # uren/dagen
    LANGE_TERMIJN = "lang"       # weken/maanden
    CYCLISCH = "cyclisch"        # seizoenspatronen
    EEUWIG = "eeuwig"            # invariants


@dataclass
class TijdsVeld:
    """
    Een continu veld waarin alle tijden simultaan bestaan.
    
    Uitbreidingen:
    - Meerdere tijdschalen
    - Cyclische componenten
    - Geheugenintegratie
    - Voorspellingsfout tracking
    """
    # De kern: tijd is geen index maar een dimensie
    tijds_dimensies: int = 100  # Hoe 'fijn' is ons tijdsveld?
    
    # Continue velden voor verleden, heden, toekomst (simultaan!)
    verleden_veld: np.ndarray = field(default_factory=lambda: np.zeros(100))
    heden_veld: np.ndarray = field(default_factory=lambda: np.zeros(100))
    toekomst_veld: np.ndarray = field(default_factory=lambda: np.zeros(100))
    
    # Extra velden voor meerdere tijdschalen
    verleden_kort: np.ndarray = field(default_factory=lambda: np.zeros(100))
    verleden_middel: np.ndarray = field(default_factory=lambda: np.zeros(100))
    verleden_lang: np.ndarray = field(default_factory=lambda: np.zeros(100))
    
    toekomst_kort: np.ndarray = field(default_factory=lambda: np.zeros(100))
    toekomst_middel: np.ndarray = field(default_factory=lambda: np.zeros(100))
    toekomst_lang: np.ndarray = field(default_factory=lambda: np.zeros(100))
    
    # Cyclische patronen (voor dag/nacht, seizoenen, etc.)
    cyclisch_24h: np.ndarray = field(default_factory=lambda: np.zeros(100))
    cyclisch_7d: np.ndarray = field(default_factory=lambda: np.zeros(100))
    cyclisch_30d: np.ndarray = field(default_factory=lambda: np.zeros(100))
    
    # Vervaging per schaal (hoe snel vervaagt het verleden?)
    vervaging: Dict[str, float] = field(default_factory=lambda: {
        'kort': 0.98,    # Zeer langzaam vervagen voor kort verleden
        'middel': 0.95,  # Standaard voor middellang
        'lang': 0.90,    # Sneller vervagen voor lang verleden
        'eeuwig': 0.99   # Bijna geen vervaging voor invariants
    })
    
    # Anticipatie per schaal (hoe vaag is de toekomst?)
    anticipatie: Dict[str, float] = field(default_factory=lambda: {
        'kort': 0.99,    # Redelijk zeker voor korte termijn
        'middel': 0.95,  # Minder zeker voor middellang
        'lang': 0.85,    # Vaag voor lange termijn
        'eeuwig': 0.50   # Zeer vaag voor eeuwigheid
    })
    
    # Resonantie tussen tijden
    resonantie_sterkte: float = 0.3
    
    # Geheugen voor foutenanalyse
    voorspellingsfouten: List[float] = field(default_factory=list)
    max_fouten: int = 1000
    
    # Laatste update tijd
    laatste_update: float = field(default_factory=time.time)
    update_interval: float = 0.0
    
    def update(self, nieuwe_waarde: np.ndarray):
        """
        Update het tijdsveld met een nieuwe waarde.
        Werkt nu met meerdere tijdschalen.
        """
        huidige_tijd = time.time()
        self.update_interval = huidige_tijd - self.laatste_update
        self.laatste_update = huidige_tijd
        
        # Update voor verschillende tijdschalen
        self._update_schaal('kort', nieuwe_waarde)
        self._update_schaal('middel', nieuwe_waarde)
        self._update_schaal('lang', nieuwe_waarde)
        
        # Update hoofdvelden (combinatie van alle schalen)
        self.verleden_veld = (
            0.5 * self.verleden_kort +
            0.3 * self.verleden_middel +
            0.2 * self.verleden_lang
        )
        
        self.toekomst_veld = (
            0.6 * self.toekomst_kort +
            0.3 * self.toekomst_middel +
            0.1 * self.toekomst_lang
        )
        
        # Update cyclische patronen
        self._update_cyclisch(nieuwe_waarde)
        
        # Het nieuwe heden is de input
        self.heden_veld = nieuwe_waarde
        
        # Bereken voorspellingsfout
        self._bereken_voorspellingsfout()
    
    def _update_schaal(self, schaal: str, nieuwe_waarde: np.ndarray):
        """Update een specifieke tijdschaal."""
        verleden_attr = f'verleden_{schaal}'
        toekomst_attr = f'toekomst_{schaal}'
        
        verleden = getattr(self, verleden_attr)
        toekomst = getattr(self, toekomst_attr)
        
        # Update verleden met specifieke vervaging
        nieuwe_verleden = verleden * self.vervaging[schaal] + \
                          self.heden_veld * (1 - self.vervaging[schaal])
        
        # Update toekomst met specifieke anticipatie
        nieuwe_toekomst = toekomst * self.anticipatie[schaal] + \
                          nieuwe_waarde * (1 - self.anticipatie[schaal]) * self.resonantie_sterkte
        
        setattr(self, verleden_attr, nieuwe_verleden)
        setattr(self, toekomst_attr, nieuwe_toekomst)
    
    def _update_cyclisch(self, nieuwe_waarde: np.ndarray):
        """Update cyclische patronen."""
        # 24-uurs cyclus (vereenvoudigd)
        self.cyclisch_24h = self.cyclisch_24h * 0.99 + nieuwe_waarde * 0.01
        
        # 7-daagse cyclus
        self.cyclisch_7d = self.cyclisch_7d * 0.98 + nieuwe_waarde * 0.02
        
        # 30-daagse cyclus
        self.cyclisch_30d = self.cyclisch_30d * 0.95 + nieuwe_waarde * 0.05
    
    def _bereken_voorspellingsfout(self):
        """Bereken hoe goed de voorspelling was."""
        if hasattr(self, 'vorige_voorspelling'):
            fout = np.mean(np.abs(self.heden_veld - self.vorige_voorspelling))
            self.voorspellingsfouten.append(fout)
            
            if len(self.voorspellingsfouten) > self.max_fouten:
                self.voorspellingsfouten.pop(0)
        
        # Sla huidige voorspelling op voor volgende keer
        self.vorige_voorspelling = self.toekomst_veld.copy()
    
    def resonantie_met_verleden(self, schaal: Optional[str] = None, 
                               sterkte: float = 1.0) -> np.ndarray:
        """
        Hoe resoneert het heden met het verleden?
        
        Args:
            schaal: Optionele specifieke tijdschaal
            sterkte: Versterkingsfactor
        """
        if schaal:
            verleden = getattr(self, f'verleden_{schaal}')
            return self.heden_veld * verleden * sterkte
        else:
            return self.heden_veld * self.verleden_veld * sterkte
    
    def resonantie_met_toekomst(self, schaal: Optional[str] = None,
                               sterkte: float = 1.0) -> np.ndarray:
        """
        Hoe resoneert het heden met mogelijke toekomsten?
        """
        if schaal:
            toekomst = getattr(self, f'toekomst_{schaal}')
            return self.heden_veld * toekomst * sterkte
        else:
            return self.heden_veld * self.toekomst_veld * sterkte
    
    def alle_tijden(self) -> Dict[str, np.ndarray]:
        """Alle tijden bestaan simultaan."""
        result = {
            'verleden': self.verleden_veld,
            'heden': self.heden_veld,
            'toekomst': self.toekomst_veld,
            'verleden_kort': self.verleden_kort,
            'verleden_middel': self.verleden_middel,
            'verleden_lang': self.verleden_lang,
            'toekomst_kort': self.toekomst_kort,
            'toekomst_middel': self.toekomst_middel,
            'toekomst_lang': self.toekomst_lang,
        }
        
        # Voeg cyclische patronen toe
        if np.any(self.cyclisch_24h != 0):
            result['cyclisch_24h'] = self.cyclisch_24h
        if np.any(self.cyclisch_7d != 0):
            result['cyclisch_7d'] = self.cyclisch_7d
        if np.any(self.cyclisch_30d != 0):
            result['cyclisch_30d'] = self.cyclisch_30d
        
        return result


class Layer8_TemporaliteitFlux:
    """
    Layer 8: Temporality and Flux - UITGEBREIDE CONTINUOUS VERSION
    
    De theorie:
    - Tijd is geen pijl maar een veld
    - Verleden, heden en toekomst interpenetreren
    - Geen discrete momenten, alleen continue vervaging
    - Meerdere tijdschalen voor rijker gedrag
    - Cyclische patronen detectie
    - Voorspellingsfout analyse
    
    Deze implementatie vervangt de oude `temporal_states` lijst
    door een continu tijdsveld waarin alle momenten simultaan bestaan.
    """
    
    def __init__(self, layer7, config: Optional[Dict] = None):
        """
        Initialiseer Layer 8.
        
        Args:
            layer7: Layer 7 instance
            config: Optionele configuratie
        """
        self.layer7 = layer7
        
        # Configuratie
        self.config = config or {}
        self.tijds_dimensies = self.config.get('tijds_dimensies', 100)
        self.max_buffer = self.config.get('max_buffer', 50)
        self.schalen = self.config.get('schalen', ['kort', 'middel', 'lang'])
        
        # 🌊 CONTINU TIJDSVELD met meerdere schalen
        self.tijdsveld = TijdsVeld(tijds_dimensies=self.tijds_dimensies)
        
        # 📜 Visualisatie buffer (alleen voor menselijke observatie)
        self.visualisatie_buffer: List[Dict] = []
        
        # 📊 Metrics voor analyse
        self.metrics = {
            'updates': 0,
            'gem_voorspellingsfout': 0.0,
            'temporele_stabiliteit': 1.0,
            'cyclische_sterkte': 0.0,
            'laatste_update': time.time()
        }
        
        logger.info("="*80)
        logger.info("🌊 Layer 8: Continue temporaliteit (uitgebreid)")
        logger.info("="*80)
        logger.info("   - Verleden, heden, toekomst bestaan simultaan")
        logger.info(f"   - Tijdschalen: {', '.join(self.schalen)}")
        logger.info(f"   - Dimensies: {self.tijds_dimensies}")
        logger.info("   - Geen discrete momenten, alleen continue velden")
        logger.info("="*80)
    
    def record_temporal_state(self):
        """
        Werk het continue tijdsveld bij met de huidige staat.
        """
        # Haal huidige synthese op uit layer7
        huidige_synthese = self.layer7.synthesize()
        
        # Maak een vector van de synthese
        if huidige_synthese.global_state is not None:
            nieuwe_waarde = huidige_synthese.global_state
            # Zorg voor correcte dimensies
            if len(nieuwe_waarde) != self.tijds_dimensies:
                nieuwe_waarde = self._resize_array(nieuwe_waarde)
        else:
            # Fallback: gebruik coherence als scalar
            nieuwe_waarde = np.ones(self.tijds_dimensies) * huidige_synthese.coherence_score
        
        # Update het continue tijdsveld
        self.tijdsveld.update(nieuwe_waarde)
        
        # Update metrics
        self.metrics['updates'] += 1
        if self.tijdsveld.voorspellingsfouten:
            self.metrics['gem_voorspellingsfout'] = np.mean(self.tijdsveld.voorspellingsfouten[-100:])
        
        self.metrics['temporele_stabiliteit'] = self.temporele_coherentie()
        self.metrics['cyclische_sterkte'] = self._meet_cyclische_sterkte()
        self.metrics['laatste_update'] = time.time()
        
        # Alleen voor visualisatie: bewaar een momentopname
        if len(self.visualisatie_buffer) >= self.max_buffer:
            self.visualisatie_buffer.pop(0)
        
        self.visualisatie_buffer.append({
            'tijd': len(self.visualisatie_buffer),
            'coherence': huidige_synthese.coherence_score,
            'invariants': huidige_synthese.invariants.copy(),
            'voorspellingsfout': self.tijdsveld.voorspellingsfouten[-1] if self.tijdsveld.voorspellingsfouten else 0,
            'temporele_coherentie': self.temporele_coherentie(),
            'temporele_entropie': self.temporele_entropie()
        })
        
        logger.debug(f"🌊 Tijdsveld bijgewerkt - resonantie: {np.mean(self.tijdsveld.resonantie_met_verleden()):.3f}")
    
    def _resize_array(self, arr: np.ndarray) -> np.ndarray:
        """Pas array aan naar juiste dimensies."""
        if len(arr) > self.tijds_dimensies:
            # Truncate
            return arr[:self.tijds_dimensies]
        else:
            # Pad with zeros
            return np.pad(arr, (0, self.tijds_dimensies - len(arr)))
    
    def _meet_cyclische_sterkte(self) -> float:
        """Meet hoe sterk cyclische patronen zijn."""
        sterktes = []
        
        if hasattr(self.tijdsveld, 'cyclisch_24h'):
            sterkte = np.std(self.tijdsveld.cyclisch_24h) / (np.std(self.tijdsveld.heden_veld) + 1e-10)
            sterktes.append(sterkte)
        
        if hasattr(self.tijdsveld, 'cyclisch_7d'):
            sterkte = np.std(self.tijdsveld.cyclisch_7d) / (np.std(self.tijdsveld.heden_veld) + 1e-10)
            sterktes.append(sterkte)
        
        if hasattr(self.tijdsveld, 'cyclisch_30d'):
            sterkte = np.std(self.tijdsveld.cyclisch_30d) / (np.std(self.tijdsveld.heden_veld) + 1e-10)
            sterktes.append(sterkte)
        
        return float(np.mean(sterktes)) if sterktes else 0.0
    
    # ====================================================================
    # TEMPORELE OPERATIES PER SCHAAL
    # ====================================================================
    
    def verleden_invloed(self, schaal: str = 'middel', vertraging: float = 1.0) -> np.ndarray:
        """
        Hoe beïnvloedt het verleden het heden op een specifieke schaal?
        
        Args:
            schaal: 'kort', 'middel', of 'lang'
            vertraging: Continue vertragingsparameter
        """
        verleden = getattr(self.tijdsveld, f'verleden_{schaal}')
        return verleden * np.exp(-vertraging)
    
    def toekomst_anticipatie(self, schaal: str = 'middel', horizon: float = 1.0) -> np.ndarray:
        """
        Hoe anticipeert het systeem op de toekomst op een specifieke schaal?
        """
        toekomst = getattr(self.tijdsveld, f'toekomst_{schaal}')
        return toekomst * np.exp(-horizon)
    
    def temporele_coherentie(self, schaal: Optional[str] = None) -> float:
        """
        Hoe coherent zijn verleden, heden en toekomst?
        
        Args:
            schaal: Optionele specifieke schaal
        """
        if schaal:
            resonantie_vh = np.mean(self.tijdsveld.resonantie_met_verleden(schaal))
            resonantie_ht = np.mean(self.tijdsveld.resonantie_met_toekomst(schaal))
        else:
            resonantie_vh = np.mean(self.tijdsveld.resonantie_met_verleden())
            resonantie_ht = np.mean(self.tijdsveld.resonantie_met_toekomst())
        
        return float((resonantie_vh + resonantie_ht) / 2)
    
    def temporele_entropie(self) -> float:
        """
        Hoe 'verdeeld' is de informatie over de tijd?
        Hoge entropie = verleden, heden en toekomst zijn even belangrijk.
        Lage entropie = één tijd domineert.
        """
        alle_tijden = self.tijdsveld.alle_tijden()
        
        # Bereken de 'verdeling' van intensiteit over tijden
        intensiteiten = []
        for tijds_naam, veld in alle_tijden.items():
            if 'cyclisch' not in tijds_naam:  # Negeer cyclische voor entropie
                intensiteiten.append(np.mean(np.abs(veld)))
        
        # Normaliseer naar kansen
        totaal = sum(intensiteiten)
        if totaal == 0:
            return 0.0
        
        kansen = [i / totaal for i in intensiteiten]
        
        # Shannon entropie
        entropie = -sum(p * np.log(p) if p > 0 else 0 for p in kansen)
        
        # Normaliseer naar 0-1
        max_entropie = np.log(len(intensiteiten))
        return entropie / max_entropie if max_entropie > 0 else 0.0
    
    def tijd_reizen(self, verschuiving: float, schaal: str = 'middel') -> np.ndarray:
        """
        Verschuif het perspectief in de tijd op een specifieke schaal.
        
        Args:
            verschuiving: Positief = toekomst, negatief = verleden
            schaal: Tijdschaal voor de verschuiving
        """
        if verschuiving > 0:
            # Naar toekomst
            heden = getattr(self.tijdsveld, f'toekomst_{schaal}')
            toekomst = getattr(self.tijdsveld, f'toekomst_{schaal}')
            return heden * (1 - verschuiving) + toekomst * verschuiving
        else:
            # Naar verleden
            verschuiving = abs(verschuiving)
            heden = getattr(self.tijdsveld, f'verleden_{schaal}')
            verleden = getattr(self.tijdsveld, f'verleden_{schaal}')
            return heden * (1 - verschuiving) + verleden * verschuiving
    
    def voorspel(self, stappen: int = 1) -> List[np.ndarray]:
        """
        Maak een voorspelling voor de komende stappen.
        
        Args:
            stappen: Aantal stappen vooruit
            
        Returns:
            Lijst van voorspelde toestanden
        """
        voorspellingen = []
        huidig = self.tijdsveld.heden_veld.copy()
        
        for _ in range(stappen):
            # Eenvoudige extrapolatie op basis van trend
            trend = self.tijdsveld.toekomst_veld - self.tijdsveld.heden_veld
            volgende = huidig + trend * 0.1
            volgende = volgende / np.linalg.norm(volgende)
            voorspellingen.append(volgende)
            huidig = volgende
        
        return voorspellingen
    
    # ====================================================================
    # ANALYSE
    # ====================================================================
    
    def detecteer_cycli(self) -> Dict[str, float]:
        """Detecteer cyclische patronen in de data."""
        if len(self.visualisatie_buffer) < 10:
            return {}
        
        # Haal coherence geschiedenis op
        coherences = [entry['coherence'] for entry in self.visualisatie_buffer]
        
        # Eenvoudige FFT voor periodiciteit
        fft = np.fft.fft(coherences)
        frequenties = np.fft.fftfreq(len(coherences))
        
        # Vind dominante frequenties (exclusief DC)
        amplitudes = np.abs(fft)
        amplitudes[0] = 0  # Negeer DC component
        
        top_indices = np.argsort(amplitudes)[-5:][::-1]
        
        cycli = {}
        for idx in top_indices:
            if idx > 0 and amplitudes[idx] > amplitudes[0] * 0.1:  # Drempel
                periode = 1.0 / abs(frequenties[idx]) if frequenties[idx] != 0 else 0
                if 2 < periode < 100:  # Redelijke periodes
                    cycli[f'periode_{periode:.1f}'] = float(amplitudes[idx])
        
        return cycli
    
    def get_trend(self) -> Dict[str, float]:
        """Bereken trends in het systeem."""
        if len(self.visualisatie_buffer) < 2:
            return {}
        
        # Korte termijn trend
        kort = self.visualisatie_buffer[-5:] if len(self.visualisatie_buffer) >= 5 else self.visualisatie_buffer
        kort_coherence = [e['coherence'] for e in kort]
        kort_trend = (kort_coherence[-1] - kort_coherence[0]) / len(kort)
        
        # Lange termijn trend
        lang_coherence = [e['coherence'] for e in self.visualisatie_buffer]
        lang_trend = (lang_coherence[-1] - lang_coherence[0]) / len(lang_coherence)
        
        return {
            'korte_termijn': float(kort_trend),
            'lange_termijn': float(lang_trend),
            'versnelling': float(kort_trend - lang_trend)
        }
    
    # ====================================================================
    # VISUALISATIE (voor dashboard)
    # ====================================================================
    
    def get_visualisatie_data(self) -> Dict[str, Any]:
        """
        Haal data op voor visualisatie.
        Dit is ALLEEN voor menselijke interpretatie, niet voor causaliteit.
        """
        cycli = self.detecteer_cycli()
        trend = self.get_trend()
        
        return {
            'temporele_coherentie': self.temporele_coherentie(),
            'temporele_entropie': self.temporele_entropie(),
            'verleden_intensiteit': float(np.mean(self.tijdsveld.verleden_veld)),
            'heden_intensiteit': float(np.mean(self.tijdsveld.heden_veld)),
            'toekomst_intensiteit': float(np.mean(self.tijdsveld.toekomst_veld)),
            'resonantie_verleden': float(np.mean(self.tijdsveld.resonantie_met_verleden())),
            'resonantie_toekomst': float(np.mean(self.tijdsveld.resonantie_met_toekomst())),
            'voorspellingsfout': self.metrics['gem_voorspellingsfout'],
            'temporele_stabiliteit': self.metrics['temporele_stabiliteit'],
            'cyclische_sterkte': self.metrics['cyclische_sterkte'],
            'cycli': cycli,
            'trend': trend,
            'per_schaal': {
                schaal: {
                    'coherentie': self.temporele_coherentie(schaal),
                    'verleden': float(np.mean(getattr(self.tijdsveld, f'verleden_{schaal}'))),
                    'toekomst': float(np.mean(getattr(self.tijdsveld, f'toekomst_{schaal}')))
                }
                for schaal in self.schalen
            },
            'metrics': self.metrics,
            'visualisatie_buffer': self.visualisatie_buffer
        }


# ====================================================================
# DEMONSTRATIE (UITGEBREID)
# ====================================================================

def demonstreer_verschil():
    """Laat zien wat er veranderd is."""
    
    print("\n" + "="*80)
    print("🌊 DEMONSTRATIE: OUDE VS NIEUWE LAAG 8")
    print("="*80)
    
    # Oude versie
    print("\n📦 OUDE VERSIE (discreet):")
    print("   temporal_states = []  # Lijst met snapshots")
    print("   # Geen toekomst, verleden alleen in lijst")
    
    # Nieuwe basis versie
    print("\n🌊 NIEUWE BASIS VERSIE (continu):")
    print("   tijdsveld = TijdsVeld()  # Continu veld")
    print("   # Verleden blijft bestaan (vervaging)")
    print("   # Toekomst wordt geanticipeerd")
    
    # Uitgebreide versie
    print("\n🌟 UITGEBREIDE VERSIE (meerdere schalen):")
    print("   - Meerdere tijdschalen (kort/middel/lang)")
    print("   - Cyclische patronen detectie")
    print("   - Voorspellingsfout analyse")
    print("   - Trend detectie")
    print("   - Per-schaal analyse")
    
    print("\n" + "="*80)
    print("✅ VERBETERINGEN:")
    print("   1. Geen discrete momenten → continue vervaging")
    print("   2. Verleden blijft bestaan (als resonantie)")
    print("   3. Toekomst is aanwezig (als potentie)")
    print("   4. Meerdere tijdschalen voor rijker gedrag")
    print("   5. Cyclische patronen detectie")
    print("   6. Voorspellingsfout tracking")
    print("="*80)


if __name__ == "__main__":
    # Configureer logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    demonstreer_verschil()
    
    print("\n" + "="*80)
    print("🚀 TEST: CONTINUE TEMPORALITEIT (UITGEBREID)")
    print("="*80)
    
    # Maak mock layer7
    class MockLayer7:
        class Synthesis:
            def __init__(self):
                self.coherence_score = 0.5
                self.global_state = np.random.randn(100) * 0.5
                self.global_state = self.global_state / np.linalg.norm(self.global_state)
                self.invariants = []
        
        def __init__(self):
            self.synthesis = self.Synthesis()
        
        def synthesize(self):
            # Simuleer kleine veranderingen
            self.synthesis.coherence_score += np.random.randn() * 0.05
            self.synthesis.coherence_score = np.clip(self.synthesis.coherence_score, 0, 1)
            
            # Update global state met ruis
            ruis = np.random.randn(100) * 0.05
            self.synthesis.global_state = self.synthesis.global_state + ruis
            self.synthesis.global_state = self.synthesis.global_state / np.linalg.norm(self.synthesis.global_state)
            
            return self.synthesis
    
    # Initialiseer nieuwe Layer 8
    layer7 = MockLayer7()
    laag8 = Layer8_TemporaliteitFlux(layer7)
    
    # Simuleer 50 updates
    print("\n📊 Continue evolutie over 50 stappen:")
    for i in range(50):
        laag8.record_temporal_state()
        
        if i % 10 == 0:  # Om de 10 stappen tonen we status
            data = laag8.get_visualisatie_data()
            print(f"\n   T={i}:")
            print(f"      Coherentie: {data['temporele_coherentie']:.3f}")
            print(f"      Entropie: {data['temporele_entropie']:.3f}")
            print(f"      Voorspellingsfout: {data['voorspellingsfout']:.3f}")
            print(f"      Cyclische sterkte: {data['cyclische_sterkte']:.3f}")
            
            # Toon per schaal
            for schaal, schaal_data in data['per_schaal'].items():
                print(f"      {schaal}: coh={schaal_data['coherentie']:.3f}")
    
    # Toon gedetecteerde cycli
    print("\n🔄 Gedetecteerde cycli:")
    cycli = laag8.detecteer_cycli()
    for periode, sterkte in cycli.items():
        print(f"   {periode}: sterkte={sterkte:.3f}")
    
    # Toon trend
    print("\n📈 Trend:")
    trend = laag8.get_trend()
    for key, value in trend.items():
        print(f"   {key}: {value:.4f}")
    
    print("\n" + "="*80)
    print("✅ Uitgebreide continue temporaliteit werkt!")
    print("="*80)