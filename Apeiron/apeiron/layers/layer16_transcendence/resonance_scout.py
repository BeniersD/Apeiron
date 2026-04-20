"""
RESONANCESCOUT MODULE - Interferentie Jager - V12 UITGEBREID
================================================================================================
De ResonanceScout werkt niet met zoektermen, maar met fase-verschillen in de vectoren van de oceaan.

Functionaliteit:
- Interferentie Monitoring: Scant de OceanicFlow op plekken waar twee stromingen bijna raken
- Stille Stroming (Silent Stream): Creëert virtuele stromingen in Quantum Backend zonder document
- Resonantie Check: Bij hoge stability_score in Laag 17 → gerichte zoekopdracht naar invullende data

UITBREIDINGEN:
- Geavanceerde caching met statistics
- Export functionaliteit
- Reset mogelijkheid
- Health checks
- Meer matching algoritmes
- Uitgebreide metrics
- Performance profiling
"""

import numpy as np
import asyncio
import logging
import hashlib
import arxiv
import time
import yaml
import os
import json
import psutil
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from enum import Enum

logger = logging.getLogger(__name__)

# ====================================================================
# OPTIONELE ERROR HANDLING INTEGRATIE
# ====================================================================

try:
    from hardware_exceptions import handle_hardware_errors
    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False
    # Fallback decorator
    def handle_hardware_errors(default_return=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.debug(f"Error in {func.__name__}: {e}")
                    return default_return
            return wrapper
        return decorator


# ====================================================================
# ENUMS
# ====================================================================

class MatchAlgorithm(Enum):
    """Beschikbare matching algoritmes."""
    EMBEDDING = "embedding"          # ChromaDB embeddings (standaard)
    HEURISTIEK = "heuristiek"        # Keyword-based heuristiek
    HYBRID = "hybrid"                 # Combinatie van beide
    TITEL = "titel"                   # Alleen titel matching
    ABSTRACT = "abstract"             # Alleen abstract matching
    GEMIDDELD = "gemiddeld"           # Gewogen gemiddelde van meerdere


class InterferentieType(Enum):
    """Types van interferentie."""
    KRITISCH = "kritisch"             # Zeer kleine afstand (<0.1)
    STABIEL = "stabiel"               # Potentieel voor stabiliteit
    VOORBIJGAAND = "voorbijgaand"     # Tijdelijke interferentie
    RESONANT = "resonant"              # Hoge resonantie


# ====================================================================
# DATACLASSES (UITGEBREID)
# ====================================================================

@dataclass
class CacheStats:
    """Statistics voor caching."""
    hits: int = 0
    misses: int = 0
    size: int = 0
    max_size: int = 100
    evictions: int = 0
    
    @property
    def hit_ratio(self) -> float:
        """Bereken hit ratio."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'size': self.size,
            'max_size': self.max_size,
            'evictions': self.evictions,
            'hit_ratio': self.hit_ratio
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics voor operaties."""
    gem_update_tijd: float = 0.0
    gem_match_tijd: float = 0.0
    max_update_tijd: float = 0.0
    max_match_tijd: float = 0.0
    total_updates: int = 0
    total_matches: int = 0
    
    def update_match_tijd(self, tijd: float):
        """Update met nieuwe match tijd."""
        self.total_matches += 1
        self.gem_match_tijd = (self.gem_match_tijd * (self.total_matches - 1) + tijd) / self.total_matches
        self.max_match_tijd = max(self.max_match_tijd, tijd)
    
    def update_update_tijd(self, tijd: float):
        """Update met nieuwe update tijd."""
        self.total_updates += 1
        self.gem_update_tijd = (self.gem_update_tijd * (self.total_updates - 1) + tijd) / self.total_updates
        self.max_update_tijd = max(self.max_update_tijd, tijd)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary."""
        return {
            'gem_update_tijd_ms': self.gem_update_tijd * 1000,
            'gem_match_tijd_ms': self.gem_match_tijd * 1000,
            'max_update_tijd_ms': self.max_update_tijd * 1000,
            'max_match_tijd_ms': self.max_match_tijd * 1000,
            'total_updates': self.total_updates,
            'total_matches': self.total_matches
        }


@dataclass
class InterferentiePlek:
    """
    Een plek in de oceaan waar twee stromingen bijna interfereren.
    """
    id: str
    stroom_a_id: str
    stroom_b_id: str
    fase_verschil: float
    afstand: float
    stabiliteit_potentieel: float
    locatie_veld: np.ndarray
    tijdstip: float
    type: InterferentieType = InterferentieType.VOORBIJGAAND
    verwerkt: bool = False
    
    @property
    def is_kritisch(self) -> bool:
        """Plekken met zeer kleine afstand zijn kritisch."""
        kritisch = self.afstand < 0.1 and self.fase_verschil < 0.2
        if kritisch:
            self.type = InterferentieType.KRITISCH
        return kritisch
    
    @property
    def is_stabiel(self) -> bool:
        """Check of plek potentieel stabiel is."""
        return self.stabiliteit_potentieel > 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary voor export."""
        return {
            'id': self.id,
            'stroom_a': self.stroom_a_id[:8],
            'stroom_b': self.stroom_b_id[:8],
            'afstand': self.afstand,
            'fase_verschil': self.fase_verschil,
            'type': self.type.value,
            'tijdstip': self.tijdstip,
            'verwerkt': self.verwerkt
        }


@dataclass
class StilleStroming:
    """
    Een virtuele stroming zonder onderliggend document.
    Leeft alleen in het quantum veld.
    """
    id: str
    naam: str
    geboorte_tijd: float
    
    # Wiskundige handtekening (geen menselijke labels!)
    fase: float
    frequentie: float
    resonantie_veld: np.ndarray
    
    # Metingen in Laag 17
    stability_score: float = 0.0
    coherentie_score: float = 0.0
    
    # Heeft geleid tot een zoekopdracht?
    heeft_zoekopdracht_gegeven: bool = False
    zoekopdracht_id: Optional[str] = None
    
    # Data die uiteindelijk deze leegte heeft gevuld
    gevuld_door: Optional[str] = None
    vulling_tijdstip: Optional[float] = None
    
    # Extra metrics
    aantal_interferenties: int = 0
    laatste_update: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary voor export."""
        return {
            'id': self.id,
            'naam': self.naam,
            'fase': self.fase,
            'frequentie': self.frequentie,
            'stability': self.stability_score,
            'coherentie': self.coherentie_score,
            'heeft_zoekopdracht': self.heeft_zoekopdracht_gegeven,
            'gevuld_door': self.gevuld_door,
            'geboorte_tijd': self.geboorte_tijd,
            'aantal_interferenties': self.aantal_interferenties
        }


@dataclass
class ZoekOpdracht:
    """
    Een gerichte opdracht om data te vinden die een stille stroming invult.
    """
    id: str
    stille_stroming_id: str
    aanmaak_tijd: float
    
    # De 'zoekterm' is geen tekst, maar een wiskundig profiel
    doel_spectrum: np.ndarray
    doel_fase: float
    doel_frequentie: float
    
    # Resultaten
    is_uitgevoerd: bool = False
    gevonden_papers: List[Dict[str, Any]] = field(default_factory=list)
    beste_match: Optional[Dict[str, Any]] = None
    beste_match_score: float = 0.0
    uitvoer_tijd: Optional[float] = None
    algoritme: MatchAlgorithm = MatchAlgorithm.EMBEDDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary voor export."""
        return {
            'id': self.id,
            'stille_stroming': self.stille_stroming_id[:8],
            'aanmaak_tijd': self.aanmaak_tijd,
            'uitgevoerd': self.is_uitgevoerd,
            'beste_match_score': self.beste_match_score,
            'beste_match_titel': self.beste_match.get('title', '')[:50] if self.beste_match else None,
            'aantal_papers': len(self.gevonden_papers),
            'algoritme': self.algoritme.value
        }


# ====================================================================
# RESONANCESCOUT KERN (UITGEBREID)
# ====================================================================

class ResonanceScout:
    """
    🌊 RESONANCESCOUT - Jaagt op interferentie in de oceaan.
    
    Werkt principieel anders dan traditionele zoekmachines:
    - Geen zoektermen, maar fase-verschillen
    - Creëert virtuele stromingen uit 'bijna-rakingen'
    - Laat Laag 17 bepalen of de leegte interessant is
    - Genereert pas bij hoge stabiliteit een gerichte zoekopdracht
    
    V12 UITBREIDINGEN:
    - Geavanceerde caching met statistics
    - Export functionaliteit
    - Reset mogelijkheid
    - Health checks
    - Meerdere matching algoritmes
    - Uitgebreide metrics
    - Performance profiling
    """
    
    def __init__(self, nexus, laag16_manager, laag17_integratie, 
                 quantum_backend=None, emb_fn: Optional[Callable] = None,
                 config_path: Optional[str] = None):
        """
        Initialiseer de ResonanceScout.
        
        Args:
            nexus: De Nexus instantie
            laag16_manager: Dynamische stromingen manager
            laag17_integratie: Absolute integratie manager
            quantum_backend: Optionele quantum backend
            emb_fn: Optionele embedding functie voor match scores
            config_path: Pad naar configuratie bestand (optioneel)
        """
        self.nexus = nexus
        self.laag16 = laag16_manager
        self.laag17 = laag17_integratie
        self.quantum_backend = quantum_backend
        
        # Embedding functie (uit nexus of los meegegeven)
        self.emb_fn = emb_fn
        if self.emb_fn is None and hasattr(nexus, 'emb_fn'):
            self.emb_fn = nexus.emb_fn
        
        self.logger = logging.getLogger('ResonanceScout')
        
        # Gevonden interferentieplekken
        self.interferentie_plekken: List[InterferentiePlek] = []
        
        # Virtuele stromingen
        self.stille_stromingen: Dict[str, StilleStroming] = {}
        
        # Zoekopdrachten
        self.zoekopdrachten: Dict[str, ZoekOpdracht] = {}
        
        # Metrics tracking (uitgebreid)
        self.metrics = {
            'scans_uitgevoerd': 0,
            'interferenties_gevonden': 0,
            'kritische_interferenties': 0,
            'stabiele_interferenties': 0,
            'stille_stromingen_gecreëerd': 0,
            'zoekopdrachten_gegenereerd': 0,
            'zoekopdrachten_uitgevoerd': 0,
            'matches_gevonden': 0,
            'gemiddelde_match_score': 0.0,
            'papers_verwerkt': 0,
            'errors': 0,
            'start_tijd': time.time(),
            'laatste_scan': 0,
            'laatste_match': 0
        }
        
        # Performance metrics
        self.performance = PerformanceMetrics()
        
        # Cache voor embeddings met statistics
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.cache_stats = CacheStats(max_size=100)
        
        # Configuratie (wordt geladen uit bestand)
        self._load_config(config_path)
        
        # Export directory
        self.export_dir = "resonance_exports"
        os.makedirs(self.export_dir, exist_ok=True)
        
        self.logger.info("="*80)
        self.logger.info("🌊 RESONANCESCOUT V12 GEÏNITIALISEERD (UITGEBREID)")
        self.logger.info("="*80)
        self.logger.info("Geen zoektermen - alleen fase-verschillen")
        self.logger.info(f"Interferentie drempel: {self.interferentie_drempel}")
        self.logger.info(f"Stabiliteits drempel: {self.stabiliteits_drempel}")
        self.logger.info(f"Scan interval: {self.scan_interval}s")
        self.logger.info(f"Max plek leeftijd: {self.max_plek_leeftijd/3600:.1f} uur")
        self.logger.info(f"Embedding functie: {'✔️' if self.emb_fn else '❌ (fallback naar heuristiek)'}")
        self.logger.info(f"Match algoritme: {self.default_algoritme.value}")
        self.logger.info(f"Error handling: {'✔️' if ERROR_HANDLING_AVAILABLE else '❌ (basic)'}")
        self.logger.info(f"Export directory: {self.export_dir}")
        self.logger.info("="*80)
    
    def _load_config(self, config_path: Optional[str] = None):
        """
        Laad configuratie uit YAML bestand.
        
        Args:
            config_path: Pad naar configuratie bestand
        """
        # Standaard configuratie
        self.interferentie_drempel = 0.15
        self.stabiliteits_drempel = 0.85
        self.scan_interval = 2.0
        self.max_plek_leeftijd = 3600  # 1 uur
        self.use_embeddings = True
        self.fallback_to_heuristiek = True
        self.max_zoekresultaten = 10
        self.match_drempel = 0.7
        self.batch_size = 5
        self.default_algoritme = MatchAlgorithm.EMBEDDING
        self.cache_size = 100
        self.auto_export = True
        self.export_interval = 600  # 10 minuten
        self.health_check_interval = 60  # 1 minuut
        self.profiling = False
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                scout_config = config.get('resonance_scout', {})
                
                # Update configuratie
                self.interferentie_drempel = scout_config.get('interferentie_drempel', self.interferentie_drempel)
                self.stabiliteits_drempel = scout_config.get('stabiliteits_drempel', self.stabiliteits_drempel)
                self.scan_interval = scout_config.get('scan_interval', self.scan_interval)
                self.max_plek_leeftijd = scout_config.get('max_plek_leeftijd', self.max_plek_leeftijd)
                self.use_embeddings = scout_config.get('use_embeddings', self.use_embeddings)
                self.fallback_to_heuristiek = scout_config.get('fallback_to_heuristiek', self.fallback_to_heuristiek)
                self.max_zoekresultaten = scout_config.get('max_zoekresultaten', self.max_zoekresultaten)
                self.match_drempel = scout_config.get('match_drempel', self.match_drempel)
                self.batch_size = scout_config.get('batch_size', self.batch_size)
                
                # Nieuwe configuratie opties
                algoritme_str = scout_config.get('default_algoritme', 'embedding')
                self.default_algoritme = MatchAlgorithm(algoritme_str)
                self.cache_size = scout_config.get('cache_size', 100)
                self.auto_export = scout_config.get('auto_export', True)
                self.export_interval = scout_config.get('export_interval', 600)
                self.health_check_interval = scout_config.get('health_check_interval', 60)
                self.profiling = scout_config.get('profiling', False)
                
                # Update cache max size
                self.cache_stats.max_size = self.cache_size
                
                self.logger.info(f"📋 Configuratie geladen uit: {config_path}")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Kon configuratie niet laden: {e}")
        else:
            self.logger.info("📋 Gebruik standaard configuratie")
    
    # ====================================================================
    # 1. INTERFERENTIE MONITORING (UITGEBREID)
    # ====================================================================
    
    async def scan_interferentie(self):
        """
        Continu scannen van de oceaan op interferentieplekken.
        Dit is de hoofdloop van de ResonanceScout.
        """
        self.logger.info("🔍 Interferentie scanning gestart...")
        
        last_export = time.time()
        last_health_check = time.time()
        
        while True:
            try:
                scan_start = time.time()
                
                # Update metrics
                self.metrics['scans_uitgevoerd'] += 1
                self.metrics['laatste_scan'] = scan_start
                
                # Haal alle actieve stromingen op uit Laag 16
                stromingen = list(self.laag16.stromingen.values())
                
                if len(stromingen) >= 2:
                    # Vind plekken waar stromingen bijna raken
                    nieuwe_plekken = self._vind_interferentieplekken(stromingen)
                    
                    # Voeg nieuwe plekken toe
                    for plek in nieuwe_plekken:
                        if plek not in self.interferentie_plekken:
                            self.interferentie_plekken.append(plek)
                            self.metrics['interferenties_gevonden'] += 1
                            
                            # Classificeer type
                            if plek.is_stabiel:
                                self.metrics['stabiele_interferenties'] += 1
                            
                            self.logger.info(f"📍 Nieuwe interferentieplek: {plek.stroom_a_id[:8]} ↔ {plek.stroom_b_id[:8]} (afstand: {plek.afstand:.3f}, type: {plek.type.value})")
                            
                            # Check of dit een kritische plek is
                            if plek.is_kritisch:
                                self.metrics['kritische_interferenties'] += 1
                                await self._verwerk_kritische_plek(plek)
                
                # Oude plekken opschonen
                self._opschonen_oude_plekken()
                
                # Toon status om de 10 scans
                if self.metrics['scans_uitgevoerd'] % 10 == 0:
                    self._log_status()
                
                # Auto-export indien ingeschakeld
                if self.auto_export and time.time() - last_export > self.export_interval:
                    self.export_state()
                    last_export = time.time()
                
                # Health check
                if time.time() - last_health_check > self.health_check_interval:
                    health = await self.health_check()
                    if not health['healthy']:
                        self.logger.warning(f"⚠️ Health check warnings: {health['issues']}")
                    last_health_check = time.time()
                
                # Update performance
                scan_time = time.time() - scan_start
                self.performance.update_update_tijd(scan_time)
                
            except Exception as e:
                self.metrics['errors'] += 1
                self.logger.error(f"Fout tijdens interferentie scan: {e}")
            
            await asyncio.sleep(self.scan_interval)
    
    @handle_hardware_errors(default_return=[])
    def _vind_interferentieplekken(self, stromingen: List) -> List[InterferentiePlek]:
        """
        Vind plekken waar twee stromingen bijna raken.
        Dit is de kern van de interferentie detectie.
        """
        plekken = []
        
        for i, a in enumerate(stromingen):
            for b in stromingen[i+1:]:
                # Bereken afstand in de conceptruimte
                if hasattr(a, 'concept_veld') and hasattr(b, 'concept_veld'):
                    afstand = 1 - np.dot(a.concept_veld, b.concept_veld)
                    
                    # Bereken fase-verschil
                    fase_verschil = abs(a.fase - b.fase) % (2 * np.pi)
                    fase_verschil = min(fase_verschil, 2*np.pi - fase_verschil) / (2*np.pi)
                    
                    # Check of ze 'bijna raken'
                    if afstand < self.interferentie_drempel:
                        # Bereken potentieel voor stabiliteit
                        stabiliteit = (1 - afstand) * (1 - fase_verschil)
                        
                        # Bepaal locatie (gemiddelde van beide velden)
                        locatie = (a.concept_veld + b.concept_veld) / 2
                        locatie = locatie / np.linalg.norm(locatie)
                        
                        # Maak uniek ID
                        hash_input = f"{a.id}{b.id}{time.time()}".encode()
                        plek_id = f"INT_{hashlib.md5(hash_input).hexdigest()[:8].upper()}"
                        
                        # Bepaal type
                        if afstand < 0.1 and fase_verschil < 0.2:
                            type_ = InterferentieType.KRITISCH
                        elif stabiliteit > 0.8:
                            type_ = InterferentieType.STABIEL
                        else:
                            type_ = InterferentieType.VOORBIJGAAND
                        
                        plek = InterferentiePlek(
                            id=plek_id,
                            stroom_a_id=a.id,
                            stroom_b_id=b.id,
                            fase_verschil=fase_verschil,
                            afstand=afstand,
                            stabiliteit_potentieel=stabiliteit,
                            locatie_veld=locatie,
                            tijdstip=time.time(),
                            type=type_
                        )
                        
                        plekken.append(plek)
        
        return plekken
    
    def _opschonen_oude_plekken(self):
        """Verwijder interferentieplekken ouder dan max_leeftijd."""
        nu = time.time()
        oud_aantal = len(self.interferentie_plekken)
        
        self.interferentie_plekken = [
            p for p in self.interferentie_plekken 
            if nu - p.tijdstip < self.max_plek_leeftijd
        ]
        
        if len(self.interferentie_plekken) < oud_aantal:
            self.logger.debug(f"🧹 {oud_aantal - len(self.interferentie_plekken)} oude plekken opgeruimd")
    
    # ====================================================================
    # 2. STILLE STROMINGEN (SILENT STREAMS)
    # ====================================================================
    
    async def _verwerk_kritische_plek(self, plek: InterferentiePlek):
        """
        Verwerk een kritische interferentieplek.
        Dit is waar de magie gebeurt - we creëren een virtuele stroming.
        """
        self.logger.info(f"\n✨ KRITISCHE INTERFERENTIE GEDETECTEERD!")
        self.logger.info(f"   Plek: {plek.id}")
        self.logger.info(f"   Tussen: {plek.stroom_a_id[:8]} en {plek.stroom_b_id[:8]}")
        self.logger.info(f"   Afstand: {plek.afstand:.4f}")
        self.logger.info(f"   Fase-verschil: {plek.fase_verschil:.4f}")
        
        # Markeer als verwerkt
        plek.verwerkt = True
        
        # Creëer stille stroming
        stille = await self._creëer_stille_stroming(plek)
        
        if stille:
            self.metrics['stille_stromingen_gecreëerd'] += 1
            
            self.logger.info(f"\n🌀 STILLE STROMING GECREËERD")
            self.logger.info(f"   ID: {stille.id}")
            self.logger.info(f"   Naam: {stille.naam}")
            self.logger.info(f"   Fase: {stille.fase:.3f}")
            self.logger.info(f"   Frequentie: {stille.frequentie:.3f}")
            
            # Laat Laag 17 de stabiliteit bepalen
            await self._meet_stabiliteit_in_laag17(stille)
    
    async def _creëer_stille_stroming(self, plek: InterferentiePlek) -> Optional[StilleStroming]:
        """
        Creëer een virtuele stroming uit een interferentieplek.
        Gebruikt quantum backend voor maximale resonantie.
        """
        # Genereer naam uit de betrokken stromingen
        naam = f"silent_{plek.stroom_a_id[:4]}{plek.stroom_b_id[:4]}"
        
        # Bepaal fase en frequentie uit de plek
        fase = (plek.fase_verschil * 2 * np.pi) % (2 * np.pi)
        frequentie = 1.0 + plek.stabiliteit_potentieel * 2.0  # 1.0 - 3.0
        
        # Gebruik quantum backend voor veld-creatie (indien beschikbaar)
        if self.quantum_backend and hasattr(self.quantum_backend, 'create_continuous_field'):
            resonantie_veld = self.quantum_backend.create_continuous_field(50)
            # Verrijk met de locatie van de plek
            resonantie_veld = resonantie_veld * 0.7 + plek.locatie_veld * 0.3
            resonantie_veld = resonantie_veld / np.linalg.norm(resonantie_veld)
        else:
            # Fallback naar klassiek
            resonantie_veld = plek.locatie_veld.copy()
            # Voeg quantum-ruis toe (simulatie)
            resonantie_veld += np.random.randn(50) * 0.1
            resonantie_veld = resonantie_veld / np.linalg.norm(resonantie_veld)
        
        # Genereer uniek ID
        hash_input = f"{naam}{time.time()}".encode()
        stille_id = f"SILENT_{hashlib.sha256(hash_input).hexdigest()[:8].upper()}"
        
        stille = StilleStroming(
            id=stille_id,
            naam=naam,
            geboorte_tijd=time.time(),
            fase=fase,
            frequentie=frequentie,
            resonantie_veld=resonantie_veld
        )
        
        self.stille_stromingen[stille.id] = stille
        return stille
    
    async def _meet_stabiliteit_in_laag17(self, stille: StilleStroming):
        """
        Laat Laag 17 de stabiliteit van de stille stroming meten.
        Alleen bij hoge stabiliteit wordt een zoekopdracht gegenereerd.
        """
        # Creëer een test-interferentie voor Laag 17
        test_interferentie = {
            'id': f"test_{stille.id}",
            'ouders': ['silent_stream', 'quantum_veld'],
            'sterkte': 0.9,  # Hoge potentie
            'resonantie': 1.0,
            'concept_veld': stille.resonantie_veld,
            'fase': stille.fase,
            'frequentie': stille.frequentie
        }
        
        # Laat Laag 17 evalueren
        fundament = self.laag17.evalueer_interferentie(
            test_interferentie, 
            time.time()
        )
        
        if fundament:
            # De stille stroming heeft stabiliteit getoond!
            stille.stability_score = fundament.stabiliteit
            stille.coherentie_score = self.laag17.coherentie
            
            self.logger.info(f"\n📊 LAAG 17 EVALUATIE")
            self.logger.info(f"   Stability score: {stille.stability_score:.3f}")
            self.logger.info(f"   Coherentie: {stille.coherentie_score:.3f}")
            
            # Check of het de drempel haalt
            if stille.stability_score > self.stabiliteits_drempel:
                await self._genereer_zoekopdracht(stille)
        else:
            # Niet stabiel genoeg - blijft voorlopig alleen in quantum veld
            stille.stability_score = 0.3  # Lage score
            self.logger.info(f"📉 Stille stroming {stille.id[:8]} niet stabiel genoeg (onder drempel)")
    
    # ====================================================================
    # 3. RESONANTIE CHECK & ZOEKOPDRACHTEN (UITGEBREID)
    # ====================================================================
    
    async def _genereer_zoekopdracht(self, stille: StilleStroming):
        """
        Genereer een gerichte zoekopdracht voor een stabiele stille stroming.
        Dit is het moment waarop de Scout actief data gaat zoeken.
        """
        self.logger.info(f"\n🔍 GENEREREN ZOEKOPDRACHT voor {stille.id}")
        self.logger.info(f"   Stabiliteit: {stille.stability_score:.3f} ≥ {self.stabiliteits_drempel}")
        
        # Maak zoekopdracht aan
        zoek_id = f"SEARCH_{hashlib.md5(f'{stille.id}{time.time()}'.encode()).hexdigest()[:8].upper()}"
        
        zoek = ZoekOpdracht(
            id=zoek_id,
            stille_stroming_id=stille.id,
            aanmaak_tijd=time.time(),
            doel_spectrum=self._bereken_doel_spectrum(stille),
            doel_fase=stille.fase,
            doel_frequentie=stille.frequentie,
            algoritme=self.default_algoritme
        )
        
        self.zoekopdrachten[zoek.id] = zoek
        stille.zoekopdracht_id = zoek.id
        stille.heeft_zoekopdracht_gegeven = True
        
        self.metrics['zoekopdrachten_gegenereerd'] += 1
        
        self.logger.info(f"   Zoekopdracht ID: {zoek.id}")
        self.logger.info(f"   Doel fase: {zoek.doel_fase:.3f}")
        self.logger.info(f"   Doel frequentie: {zoek.doel_frequentie:.3f}")
        self.logger.info(f"   Algoritme: {zoek.algoritme.value}")
        
        # Voer zoekopdracht uit (in aparte task)
        asyncio.create_task(self._voer_zoekopdracht_uit(zoek))
    
    def _bereken_doel_spectrum(self, stille: StilleStroming) -> np.ndarray:
        """Bereken het doel-spectrum voor de zoekopdracht."""
        # FFT van resonantie veld
        spectrum = np.abs(np.fft.fft(stille.resonantie_veld))
        # Normaliseer
        return spectrum / np.linalg.norm(spectrum)
    
    def _get_embedding_cached(self, text: str) -> np.ndarray:
        """
        Gecachte embedding voor betere performance met statistics.
        
        Args:
            text: Tekst om embedding van te berekenen
            
        Returns:
            Embedding vector
        """
        if self.emb_fn is None:
            return np.array([])
        
        # Maak cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        # Check cache
        if cache_key in self.embedding_cache:
            self.cache_stats.hits += 1
            return self.embedding_cache[cache_key]
        
        self.cache_stats.misses += 1
        
        try:
            start_time = time.time()
            embedding = np.array(self.emb_fn([text])[0])
            embedding = embedding / np.linalg.norm(embedding)
            
            # Update cache
            if len(self.embedding_cache) >= self.cache_stats.max_size:
                # Verwijder oudste (simpele strategie)
                oldest = next(iter(self.embedding_cache))
                del self.embedding_cache[oldest]
                self.cache_stats.evictions += 1
            
            self.embedding_cache[cache_key] = embedding
            self.cache_stats.size = len(self.embedding_cache)
            
            if self.profiling:
                self.logger.debug(f"Embedding berekend in {(time.time()-start_time)*1000:.1f}ms")
            
            return embedding
            
        except Exception as e:
            self.logger.debug(f"Embedding fout: {e}")
            return np.array([])
    
    async def _batch_zoekopdrachten(self, zoekopdrachten: List[ZoekOpdracht]):
        """
        Voer meerdere zoekopdrachten parallel uit.
        
        Args:
            zoekopdrachten: Lijst van zoekopdrachten
        """
        self.logger.info(f"📦 Batch verwerken van {len(zoekopdrachten)} zoekopdrachten")
        tasks = [self._voer_zoekopdracht_uit(z) for z in zoekopdrachten]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log resultaten
        success = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - success
        self.logger.info(f"📦 Batch voltooid: {success} success, {failed} failed")
    
    async def _voer_zoekopdracht_uit(self, zoek: ZoekOpdracht):
        """
        Voer een zoekopdracht uit op ArXiv.
        Dit is de enige plek waar menselijke taal voorkomt - en dan nog
        alleen om de wiskundige leegte te vullen met bestaande papers.
        """
        self.logger.info(f"\n📡 UITVOEREN ZOEKOPDRACHT {zoek.id}")
        start_time = time.time()
        
        try:
            # Converteer wiskundig profiel naar zoektermen
            zoektermen = self._converteer_naar_zoektermen(zoek)
            
            self.logger.info(f"   Zoektermen: {', '.join(zoektermen[:3])}...")
            
            # Voer ArXiv search uit
            client = arxiv.Client()
            search = arxiv.Search(
                query=" AND ".join(zoektermen),
                max_results=self.max_zoekresultaten,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            results = list(client.results(search))
            zoek.is_uitgevoerd = True
            zoek.uitvoer_tijd = time.time()
            
            self.metrics['zoekopdrachten_uitgevoerd'] += 1
            self.metrics['papers_verwerkt'] += len(results)
            self.metrics['laatste_match'] = time.time()
            
            self.logger.info(f"   Gevonden: {len(results)} papers")
            
            # Verwerk resultaten met gekozen algoritme
            beste_score = 0.0
            beste_paper = None
            
            for paper in results:
                match_score = await self._bereken_match_score(paper, zoek)
                
                paper_info = {
                    'title': paper.title,
                    'summary': paper.summary[:500] + "..." if len(paper.summary) > 500 else paper.summary,
                    'pdf_url': paper.pdf_url,
                    'entry_id': paper.entry_id,
                    'published': paper.published.isoformat() if paper.published else None,
                    'match_score': match_score
                }
                
                zoek.gevonden_papers.append(paper_info)
                
                if match_score > beste_score:
                    beste_score = match_score
                    beste_paper = paper_info
            
            zoek.beste_match_score = beste_score
            zoek.beste_match = beste_paper
            
            # Update gemiddelde match score
            if beste_score > 0:
                total = self.metrics['matches_gevonden'] * self.metrics['gemiddelde_match_score']
                self.metrics['matches_gevonden'] += 1
                self.metrics['gemiddelde_match_score'] = (total + beste_score) / self.metrics['matches_gevonden']
            
            # Als er een goede match is, koppel deze aan de stille stroming
            if beste_paper and beste_score > self.match_drempel:
                await self._koppel_aan_stroming(zoek)
            
            # Update performance
            match_time = time.time() - start_time
            self.performance.update_match_tijd(match_time)
            
            self.logger.info(f"   Beste match score: {beste_score:.3f} (tijd: {match_time*1000:.1f}ms)")
            if beste_paper:
                self.logger.info(f"   Beste match: {beste_paper['title'][:80]}...")
            
        except Exception as e:
            self.metrics['errors'] += 1
            self.logger.error(f"   Fout bij zoekopdracht: {e}")
            zoek.is_uitgevoerd = False
    
    def _converteer_naar_zoektermen(self, zoek: ZoekOpdracht) -> List[str]:
        """
        Converteer een wiskundig profiel naar zoektermen voor ArXiv.
        Dit is de brug tussen de wiskundige en menselijke wereld.
        """
        termen = []
        
        # Gebruik frequentie om domein te bepalen
        if 1.0 <= zoek.doel_frequentie < 1.5:
            termen.extend(['quantum', 'physics'])
        elif 1.5 <= zoek.doel_frequentie < 2.0:
            termen.extend(['machine learning', 'neural'])
        elif 2.0 <= zoek.doel_frequentie < 2.5:
            termen.extend(['biology', 'evolution'])
        else:
            termen.extend(['mathematics', 'topology'])
        
        # Gebruik fase voor specifiekere termen
        if zoek.doel_fase < np.pi/2:
            termen.append('theory')
        elif zoek.doel_fase < np.pi:
            termen.append('application')
        elif zoek.doel_fase < 3*np.pi/2:
            termen.append('experiment')
        else:
            termen.append('simulation')
        
        # Voeg algemene termen toe op basis van spectrum
        spectrum_mean = np.mean(zoek.doel_spectrum)
        if spectrum_mean > 0.5:
            termen.append('dynamics')
        if np.std(zoek.doel_spectrum) > 0.3:
            termen.append('complex')
        
        return list(set(termen))  # Unieke termen
    
    async def _bereken_match_score(self, paper: arxiv.Result, zoek: ZoekOpdracht) -> float:
        """
        Bereken match score op basis van gekozen algoritme.
        
        Args:
            paper: ArXiv paper
            zoek: Zoekopdracht met algoritme
            
        Returns:
            Match score (0-1)
        """
        if zoek.algoritme == MatchAlgorithm.EMBEDDING:
            return await self._bereken_match_score_embedding(paper, zoek)
        elif zoek.algoritme == MatchAlgorithm.HEURISTIEK:
            return self._bereken_match_score_heuristisch(paper, zoek)
        elif zoek.algoritme == MatchAlgorithm.TITEL:
            return await self._bereken_match_score_titel(paper, zoek)
        elif zoek.algoritme == MatchAlgorithm.ABSTRACT:
            return await self._bereken_match_score_abstract(paper, zoek)
        elif zoek.algoritme == MatchAlgorithm.GEMIDDELD:
            return await self._bereken_match_score_gemiddeld(paper, zoek)
        else:  # HYBRID
            return await self._bereken_match_score_hybrid(paper, zoek)
    
    async def _bereken_match_score_embedding(self, paper: arxiv.Result, zoek: ZoekOpdracht) -> float:
        """Match score op basis van embeddings."""
        try:
            if self.emb_fn is None or not self.use_embeddings:
                return self._bereken_match_score_heuristisch(paper, zoek)
            
            tekst = paper.title + " " + paper.summary
            embedding = self._get_embedding_cached(tekst)
            
            if len(embedding) == 0:
                return self._bereken_match_score_heuristisch(paper, zoek) if self.fallback_to_heuristiek else 0.0
            
            # Doel-spectrum in zelfde dimensies brengen
            doel = zoek.doel_spectrum[:len(embedding)]
            doel = doel / np.linalg.norm(doel)
            
            # Cosine gelijkenis = resonantie
            resonantie = float(np.dot(embedding, doel))
            
            return max(0.0, min(1.0, resonantie))
            
        except Exception as e:
            self.logger.debug(f"Embedding match error: {e}")
            if self.fallback_to_heuristiek:
                return self._bereken_match_score_heuristisch(paper, zoek)
            return 0.0
    
    async def _bereken_match_score_titel(self, paper: arxiv.Result, zoek: ZoekOpdracht) -> float:
        """Match score alleen op basis van titel."""
        try:
            if self.emb_fn is None:
                return 0.5
            
            embedding = self._get_embedding_cached(paper.title)
            
            if len(embedding) == 0:
                return 0.5
            
            doel = zoek.doel_spectrum[:len(embedding)]
            doel = doel / np.linalg.norm(doel)
            
            return float(np.dot(embedding, doel))
            
        except Exception:
            return 0.5
    
    async def _bereken_match_score_abstract(self, paper: arxiv.Result, zoek: ZoekOpdracht) -> float:
        """Match score alleen op basis van abstract."""
        try:
            if self.emb_fn is None:
                return 0.5
            
            embedding = self._get_embedding_cached(paper.summary[:1000])
            
            if len(embedding) == 0:
                return 0.5
            
            doel = zoek.doel_spectrum[:len(embedding)]
            doel = doel / np.linalg.norm(doel)
            
            return float(np.dot(embedding, doel))
            
        except Exception:
            return 0.5
    
    async def _bereken_match_score_gemiddeld(self, paper: arxiv.Result, zoek: ZoekOpdracht) -> float:
        """Gewogen gemiddelde van titel en abstract."""
        titel_score = await self._bereken_match_score_titel(paper, zoek)
        abstract_score = await self._bereken_match_score_abstract(paper, zoek)
        
        # Titel weegt zwaarder (40%), abstract 60%
        return 0.4 * titel_score + 0.6 * abstract_score
    
    async def _bereken_match_score_hybrid(self, paper: arxiv.Result, zoek: ZoekOpdracht) -> float:
        """Hybride score: embedding + heuristiek."""
        embedding_score = await self._bereken_match_score_embedding(paper, zoek)
        heuristiek_score = self._bereken_match_score_heuristisch(paper, zoek)
        
        # Embedding weegt 70%, heuristiek 30%
        return 0.7 * embedding_score + 0.3 * heuristiek_score

    def _bereken_match_score_heuristisch(self, paper: arxiv.Result, zoek: ZoekOpdracht) -> float:
        """Fallback heuristiek als embeddings niet werken."""
        tekst = (paper.title + " " + paper.summary).lower()
        score = 0.5
    
        wiskunde_termen = ['quantum', 'topological', 'manifold', 'homology', 'algebraic', 
                          'differential', 'geometry', 'category', 'functor', 'morphism']
        for term in wiskunde_termen:
            if term in tekst:
                score += 0.05
    
        if 'quantum' in tekst and zoek.doel_frequentie < 1.5:
            score += 0.15
        if 'neural' in tekst and 1.5 <= zoek.doel_frequentie < 2.0:
            score += 0.15
        if 'biology' in tekst and 2.0 <= zoek.doel_frequentie:
            score += 0.15
        if 'topology' in tekst and zoek.doel_frequentie >= 2.5:
            score += 0.15
    
        return min(1.0, score)    

    async def _koppel_aan_stroming(self, zoek: ZoekOpdracht):
        """
        Koppel een gevonden paper aan de oorspronkelijke stille stroming.
        Dit vervult de wiskundige leegte met concrete data.
        """
        stille = self.stille_stromingen.get(zoek.stille_stroming_id)
        if not stille:
            return
        
        stille.zoekopdracht_id = zoek.id
        stille.heeft_zoekopdracht_gegeven = True
        stille.aantal_interferenties += 1
        
        if zoek.beste_match:
            stille.gevuld_door = zoek.beste_match['entry_id']
            stille.vulling_tijdstip = time.time()
            
            self.logger.info(f"\n🌟 WISKUNDIGE LEEGTE GEVULD!")
            self.logger.info(f"   Stille stroming: {stille.id}")
            self.logger.info(f"   Gevuld door: {zoek.beste_match['title'][:80]}...")
            self.logger.info(f"   Match score: {zoek.beste_match_score:.3f}")
            self.logger.info(f"   Algoritme: {zoek.algoritme.value}")
    
    # ====================================================================
    # 4. EXPORT FUNCTIONALITEIT
    # ====================================================================
    
    def export_state(self, filename: Optional[str] = None) -> str:
        """
        Exporteer volledige staat voor debugging en analyse.
        
        Args:
            filename: Optionele bestandsnaam
            
        Returns:
            Pad naar geëxporteerd bestand
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.export_dir}/resonance_scout_{timestamp}.json"
        
        state = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'metrics': self.metrics,
            'performance': self.performance.to_dict(),
            'cache': self.cache_stats.to_dict(),
            'config': self.get_status()['config'],
            'interferenties': {
                'totaal': len(self.interferentie_plekken),
                'recent': [p.to_dict() for p in self.interferentie_plekken[-20:]]
            },
            'stromingen': {
                'totaal': len(self.stille_stromingen),
                'recent': [s.to_dict() for s in list(self.stille_stromingen.values())[-20:]]
            },
            'zoekopdrachten': {
                'totaal': len(self.zoekopdrachten),
                'recent': [z.to_dict() for z in list(self.zoekopdrachten.values())[-20:]]
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        self.logger.info(f"📄 Staat geëxporteerd naar: {filename}")
        return filename
    
    # ====================================================================
    # 5. RESET FUNCTIONALITEIT
    # ====================================================================
    
    def reset(self, hard: bool = False):
        """
        Reset alle data (voor testing).
        
        Args:
            hard: True voor volledige reset inclusief metrics
        """
        self.logger.warning(f"🔄 ResonanceScout reset ({'hard' if hard else 'soft'})")
        
        self.interferentie_plekken.clear()
        self.stille_stromingen.clear()
        self.zoekopdrachten.clear()
        self.embedding_cache.clear()
        
        self.cache_stats = CacheStats(max_size=self.cache_size)
        
        if hard:
            self.metrics = {k: 0 for k in self.metrics}
            self.metrics['start_tijd'] = time.time()
            self.performance = PerformanceMetrics()
            self.logger.info("   Volledige reset uitgevoerd")
        else:
            # Behoud sommige metrics
            self.metrics['interferenties_gevonden'] = 0
            self.metrics['kritische_interferenties'] = 0
            self.metrics['stabiele_interferenties'] = 0
            self.metrics['stille_stromingen_gecreëerd'] = 0
            self.metrics['zoekopdrachten_gegenereerd'] = 0
            self.metrics['zoekopdrachten_uitgevoerd'] = 0
            self.metrics['matches_gevonden'] = 0
            self.metrics['papers_verwerkt'] = 0
            self.logger.info("   Alleen data gereset, metrics behouden")
    
    # ====================================================================
    # 6. HEALTH CHECKS
    # ====================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Controleer of ResonanceScout gezond is.
        
        Returns:
            Dict met health status en eventuele issues
        """
        status = {
            'healthy': True,
            'issues': [],
            'warnings': [],
            'metrics': {}
        }
        
        # 1. Check of er nog geüpdatet wordt
        if time.time() - self.metrics['start_tijd'] > 60 and self.metrics['scans_uitgevoerd'] == 0:
            status['healthy'] = False
            status['issues'].append("Geen scans uitgevoerd sinds start")
        elif time.time() - self.metrics['laatste_scan'] > self.scan_interval * 3:
            status['warnings'].append(f"Laatste scan {time.time()-self.metrics['laatste_scan']:.0f}s geleden")
        
        # 2. Check cache efficiency
        if self.cache_stats.hit_ratio < 0.3 and self.cache_stats.misses > 10:
            status['warnings'].append(f"Lage cache efficiency: {self.cache_stats.hit_ratio:.1%}")
        
        # 3. Check error rate
        if self.metrics['scans_uitgevoerd'] > 0:
            error_rate = self.metrics['errors'] / self.metrics['scans_uitgevoerd']
            if error_rate > 0.1:
                status['warnings'].append(f"Hoge error rate: {error_rate:.1%}")
        
        # 4. Check performance
        if self.performance.gem_match_tijd > 5.0:  # > 5 seconden
            status['warnings'].append(f"Trage matches: {self.performance.gem_match_tijd*1000:.0f}ms")
        
        # 5. Check geheugengebruik
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        status['metrics']['memory_mb'] = memory_mb
        
        if memory_mb > 500:  # > 500MB
            status['warnings'].append(f"Hoog geheugengebruik: {memory_mb:.0f}MB")
        
        # 6. Check of embedding functie nog werkt
        if self.emb_fn is not None:
            try:
                test = self.emb_fn(["test"])[0]
                if len(test) == 0:
                    status['warnings'].append("Embedding functie geeft lege resultaten")
            except Exception as e:
                status['warnings'].append(f"Embedding functie error: {e}")
        
        status['healthy'] = len(status['issues']) == 0
        
        return status
    
    # ====================================================================
    # 5. STATUS & RAPPORTAGE (UITGEBREID)
    # ====================================================================
    
    def _log_status(self):
        """Log huidige status (voor periodieke updates)."""
        uptime = time.time() - self.metrics['start_tijd']
        
        self.logger.info(f"\n📊 RESONANCESCOUT STATUS (na {uptime:.0f}s)")
        self.logger.info(f"   Scans: {self.metrics['scans_uitgevoerd']}")
        self.logger.info(f"   Interferenties: {self.metrics['interferenties_gevonden']} (kritisch: {self.metrics['kritische_interferenties']})")
        self.logger.info(f"   Stille stromingen: {self.metrics['stille_stromingen_gecreëerd']}")
        self.logger.info(f"   Zoekopdrachten: {self.metrics['zoekopdrachten_gegenereerd']} (uitgevoerd: {self.metrics['zoekopdrachten_uitgevoerd']})")
        self.logger.info(f"   Matches: {self.metrics['matches_gevonden']}")
        if self.metrics['matches_gevonden'] > 0:
            self.logger.info(f"   Gem. match score: {self.metrics['gemiddelde_match_score']:.3f}")
        self.logger.info(f"   Performance: {self.performance.gem_update_tijd*1000:.1f}ms/scan, {self.performance.gem_match_tijd*1000:.1f}ms/match")
        self.logger.info(f"   Cache: {self.cache_stats.hit_ratio:.1%} hit ratio ({self.cache_stats.size}/{self.cache_stats.max_size})")
    
    def get_status(self) -> Dict[str, Any]:
        """Haal uitgebreide status op voor dashboard."""
        uptime = time.time() - self.metrics['start_tijd']
        
        # Bereken slagingspercentage
        success_rate = 0
        if self.metrics['zoekopdrachten_uitgevoerd'] > 0:
            success_rate = self.metrics['matches_gevonden'] / self.metrics['zoekopdrachten_uitgevoerd']
        
        return {
            'interferentie_plekken': len(self.interferentie_plekken),
            'stille_stromingen': len(self.stille_stromingen),
            'zoekopdrachten': {
                'totaal': len(self.zoekopdrachten),
                'uitgevoerd': sum(1 for z in self.zoekopdrachten.values() if z.is_uitgevoerd),
                'met_resultaat': sum(1 for z in self.zoekopdrachten.values() if z.beste_match is not None),
                'slagingspercentage': success_rate
            },
            'gevulde_leegtes': sum(1 for s in self.stille_stromingen.values() if s.gevuld_door is not None),
            'metrics': self.metrics,
            'performance': self.performance.to_dict(),
            'cache': self.cache_stats.to_dict(),
            'uptime': uptime,
            'config': {
                'interferentie_drempel': self.interferentie_drempel,
                'stabiliteits_drempel': self.stabiliteits_drempel,
                'scan_interval': self.scan_interval,
                'max_plek_leeftijd': self.max_plek_leeftijd,
                'use_embeddings': self.use_embeddings,
                'match_drempel': self.match_drempel,
                'algoritme': self.default_algoritme.value
            }
        }
    
    def print_rapport(self):
        """Print een uitgebreid rapport."""
        uptime = time.time() - self.metrics['start_tijd']
        uren = int(uptime // 3600)
        minuten = int((uptime % 3600) // 60)
        seconden = int(uptime % 60)
        
        # Haal health status
        import asyncio
        health = asyncio.run(self.health_check())
        
        print("\n" + "="*80)
        print("🌊 RESONANCESCOUT RAPPORT (UITGEBREID)")
        print("="*80)
        
        print(f"\n⏱️  Uptime: {uren}u {minuten}m {seconden}s")
        print(f"🩺 Health: {'✅' if health['healthy'] else '⚠️'}")
        if health['warnings']:
            print("   Warnings:")
            for w in health['warnings']:
                print(f"   • {w}")
        
        print(f"\n📍 Interferentie plekken: {len(self.interferentie_plekken)}")
        print(f"   • Kritisch: {self.metrics['kritische_interferenties']}")
        print(f"   • Stabiel potentieel: {self.metrics['stabiele_interferenties']}")
        
        if self.interferentie_plekken:
            print("   Recente plekken:")
            for p in sorted(self.interferentie_plekken[-5:], key=lambda x: x.afstand):
                print(f"   • {p.id}: {p.stroom_a_id[:8]} ↔ {p.stroom_b_id[:8]} (afstand: {p.afstand:.3f}, type: {p.type.value})")
        
        print(f"\n🌀 Stille stromingen: {len(self.stille_stromingen)}")
        stabiel = sum(1 for s in self.stille_stromingen.values() if s.stability_score > self.stabiliteits_drempel)
        print(f"   • Stabiel (> {self.stabiliteits_drempel}): {stabiel}")
        print(f"   • Geleid tot zoekopdracht: {sum(1 for s in self.stille_stromingen.values() if s.heeft_zoekopdracht_gegeven)}")
        print(f"   • Gevuld met data: {sum(1 for s in self.stille_stromingen.values() if s.gevuld_door is not None)}")
        
        print(f"\n🔍 Zoekopdrachten: {len(self.zoekopdrachten)}")
        print(f"   • Gegenereerd: {self.metrics['zoekopdrachten_gegenereerd']}")
        print(f"   • Uitgevoerd: {self.metrics['zoekopdrachten_uitgevoerd']}")
        print(f"   • Matches gevonden: {self.metrics['matches_gevonden']}")
        if self.metrics['matches_gevonden'] > 0:
            print(f"   • Gem. match score: {self.metrics['gemiddelde_match_score']:.3f}")
            print(f"   • Slagingspercentage: {self.metrics['matches_gevonden']/self.metrics['zoekopdrachten_uitgevoerd']*100:.1f}%")
        
        if self.zoekopdrachten:
            print("\n   Recente resultaten:")
            for z in list(self.zoekopdrachten.values())[-3:]:
                status = "✓" if z.is_uitgevoerd else "⏳"
                if z.beste_match:
                    print(f"   {status} {z.id}: match {z.beste_match_score:.2f} ({z.algoritme.value}) - {z.beste_match['title'][:60]}...")
                else:
                    print(f"   {status} {z.id}: geen match ({z.algoritme.value})")
        
        print(f"\n⚡ Performance:")
        print(f"   • Gem. scan tijd: {self.performance.gem_update_tijd*1000:.1f}ms")
        print(f"   • Gem. match tijd: {self.performance.gem_match_tijd*1000:.1f}ms")
        print(f"   • Max scan tijd: {self.performance.max_update_tijd*1000:.1f}ms")
        print(f"   • Max match tijd: {self.performance.max_match_tijd*1000:.1f}ms")
        
        print(f"\n💾 Cache:")
        print(f"   • Grootte: {self.cache_stats.size}/{self.cache_stats.max_size}")
        print(f"   • Hits: {self.cache_stats.hits}")
        print(f"   • Misses: {self.cache_stats.misses}")
        print(f"   • Hit ratio: {self.cache_stats.hit_ratio:.1%}")
        print(f"   • Evictions: {self.cache_stats.evictions}")
        
        print(f"\n⚙️  Configuratie:")
        for key, value in self.get_status()['config'].items():
            print(f"   • {key}: {value}")
        
        print("\n" + "="*80)


# ====================================================================
# INTEGRATIE MET NEXUS ULTIMATE V12
# ====================================================================

def integreer_resonancescout_in_nexus(nexus_class):
    """
    Voegt de ResonanceScout toe aan de OceanicNexusV12 class.
    Dit is een monkey-patch die je kunt toepassen.
    """
    
    def _initialiseer_resonancescout(self, config_path: Optional[str] = None):
        """Initialiseer de ResonanceScout."""
        from resonance_scout import ResonanceScout
        
        self.resonance_scout = ResonanceScout(
            nexus=self,
            laag16_manager=self.stromingen_manager,
            laag17_integratie=self.absolute_integratie,
            quantum_backend=self.hardware if hasattr(self, 'hardware') else None,
            emb_fn=self.emb_fn if hasattr(self, 'emb_fn') else None,
            config_path=config_path
        )
        
        self.log.info("🌊 ResonanceScout geïnitialiseerd - Jaagt op interferentie!")
        return self.resonance_scout
    
    async def start_resonance_scanning(self, config_path: Optional[str] = None):
        """Start de ResonanceScout scanning."""
        if not hasattr(self, 'resonance_scout'):
            self._initialiseer_resonancescout(config_path)
        
        self.log.info("\n" + "="*80)
        self.log.info("🔍 RESONANCESCOUT SCANNING GESTART")
        self.log.info("="*80)
        self.log.info("Geen zoektermen - alleen fase-verschillen in de oceaan")
        self.log.info("Virtuele stromingen uit interferentieplekken")
        self.log.info("Laag 17 bepaalt welke leegtes interessant zijn")
        self.log.info("="*80)
        
        asyncio.create_task(self.resonance_scout.scan_interferentie())
    
    def export_resonance_state(self, filename: Optional[str] = None) -> str:
        """Exporteer ResonanceScout staat."""
        if hasattr(self, 'resonance_scout'):
            return self.resonance_scout.export_state(filename)
        return ""
    
    def reset_resonance_scout(self, hard: bool = False):
        """Reset ResonanceScout."""
        if hasattr(self, 'resonance_scout'):
            self.resonance_scout.reset(hard)
    
    async def resonance_health_check(self) -> Dict[str, Any]:
        """Voer health check uit op ResonanceScout."""
        if hasattr(self, 'resonance_scout'):
            return await self.resonance_scout.health_check()
        return {'healthy': False, 'issues': ['ResonanceScout niet geïnitialiseerd']}
    
    # Voeg methodes toe aan de class
    nexus_class._initialiseer_resonancescout = _initialiseer_resonancescout
    nexus_class.start_resonance_scanning = start_resonance_scanning
    nexus_class.export_resonance_state = export_resonance_state
    nexus_class.reset_resonance_scout = reset_resonance_scout
    nexus_class.resonance_health_check = resonance_health_check
    
    return nexus_class


# ====================================================================
# DEMONSTRATIE (UITGEBREID)
# ====================================================================

async def demo():
    """Demonstreer de ResonanceScout met alle features."""
    print("\n" + "="*80)
    print("🌊 RESONANCESCOUT V12 DEMONSTRATIE (UITGEBREID)")
    print("="*80)
    
    # Maak mock objecten voor demonstratie
    class MockLaag16:
        class Stroom:
            def __init__(self, id, fase, frequentie):
                self.id = id
                self.fase = fase
                self.frequentie = frequentie
                self.concept_veld = np.random.randn(50)
                self.concept_veld = self.concept_veld / np.linalg.norm(self.concept_veld)
        
        def __init__(self):
            self.stromingen = {
                'stroom_1': self.Stroom('stroom_1', 0.5, 1.2),
                'stroom_2': self.Stroom('stroom_2', 1.8, 1.5),
                'stroom_3': self.Stroom('stroom_3', 3.2, 2.1),
                'stroom_4': self.Stroom('stroom_4', 2.4, 1.8),
                'stroom_5': self.Stroom('stroom_5', 0.9, 2.3),
            }
    
    class MockLaag17:
        def evalueer_interferentie(self, interferentie, tijd):
            # Simuleer evaluatie - geef soms een fundament terug
            if np.random.random() > 0.5:
                class MockFundament:
                    def __init__(self):
                        self.stabiliteit = np.random.uniform(0.6, 0.95)
                return MockFundament()
            return None
        
        @property
        def coherentie(self):
            return np.random.uniform(0.6, 0.9)
    
    class MockNexus:
        def __init__(self):
            self.hardware = None
            self.log = logging.getLogger('Nexus')
            self.emb_fn = None  # Mock embedding functie
    
    # Creëer scout met test config
    scout = ResonanceScout(
        nexus=MockNexus(),
        laag16_manager=MockLaag16(),
        laag17_integratie=MockLaag17()
    )
    
    # Toon configuratie
    print("\n📋 Configuratie:")
    for key, value in scout.get_status()['config'].items():
        print(f"   {key}: {value}")
    
    # Simuleer een paar scans
    print("\n🔍 Simuleer 5 scans...\n")
    for i in range(5):
        print(f"\n--- Scan {i+1} ---")
        await scout.scan_interferentie()
        await asyncio.sleep(0.5)
    
    # Toon status
    scout._log_status()
    
    # Toon health check
    print("\n🩺 Health check:")
    health = await scout.health_check()
    print(f"   Healthy: {health['healthy']}")
    if health['warnings']:
        print("   Warnings:")
        for w in health['warnings']:
            print(f"   • {w}")
    
    # Exporteer staat
    print("\n📄 Exporteren...")
    filename = scout.export_state()
    print(f"   Geëxporteerd naar: {filename}")
    
    # Toon uitgebreid rapport
    scout.print_rapport()
    
    # Test reset
    print("\n🔄 Test reset...")
    scout.reset(hard=False)
    print(f"   Na reset: {len(scout.interferentie_plekken)} interferenties")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Configureer logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    asyncio.run(demo())