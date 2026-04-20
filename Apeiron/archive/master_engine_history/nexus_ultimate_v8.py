"""
NEXUS ULTIMATE V7.0 - VOLLEDIGE V5 FUNCTIONALITEIT IN OCEAANVORM
MET DYNAMISCHE LAAG 16 - SPONTANE INTERFERENTIE
================================================================================================
BEHOUDT: 
- Document Tracking & Backtracing
- Cross-Domain Synthesis
- Ethical Research Assistant
- True Ontogenesis
- Chaos Detection & Safety
- ArXiv integratie
- Deep-dive PDF analyse
- Dashboard export

NIEUW IN LAAG 16:
- Dynamische stromingstypen (geen vaste categorieën)
- Spontane interferentie tussen stromingen
- Nieuwe types ontstaan uit interferentie
- Volledige integratie met oceanische architectuur
================================================================================================
"""

import numpy as np
import chromadb
import requests
import fitz  # PyMuPDF
import io
import sys
import yaml
import logging
import os
import asyncio
import time
import json
import arxiv
import random
import hashlib
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from chromadb.utils import embedding_functions
from habanero import Crossref

# ====================================================================
# IMPORTS VAN V5 (al je bestaande modules)
# ====================================================================

from document_tracker import DocumentTracker
from seventeen_layers_framework import SeventeenLayerFramework
from layers_11_to_17 import (
    Layer11_MetaContextualization,
    Layer12_Reconciliation,
    Layer13_Ontogenesis,
    Layer14_Worldbuilding,
    Layer15_EthicalConvergence,
    Layer16_Transcendence,
    Layer17_AbsoluteIntegration,
    Ontology
)
from cross_domain_synthesis import CrossDomainSynthesizer
from ethical_research_assistant import (
    EthicalResearchAssistant,
    ResearchProposal,
    ResearchDomain,
    RiskLevel
)
from true_ontogenesis import TrueOntogenesis, OntologicalGap
from chaos_detection import ChaosDetector, SystemState, SafetyLevel


# ====================================================================
# LOGGING (IDENTIEK AAN V5)
# ====================================================================

def setup_logging():
    """Configureer logging - IDENTIEK aan V5"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/nexus_ultimate_{timestamp}.log'
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)
    
    loggers = {
        'nexus': logging.getLogger('Nexus'),
        'safety': logging.getLogger('Safety'),
        'ethics': logging.getLogger('Ethics'),
        'ontology': logging.getLogger('Ontology'),
        'synthesis': logging.getLogger('Synthesis'),
        'memory': logging.getLogger('Memory'),
        'research': logging.getLogger('Research'),
        'tracking': logging.getLogger('DocumentTracking'),
        'ocean': logging.getLogger('Ocean'),
        'layer16': logging.getLogger('Layer16')  # NIEUW
    }
    
    print(f"\n📝 Logging geconfigureerd:")
    print(f"   - Console: ZICHTBAAR (INFO level)")
    print(f"   - Bestand: {log_file} (DEBUG level)\n")
    
    return loggers

loggers = setup_logging()


# ====================================================================
# DYNAMISCHE LAAG 16 IMPLEMENTATIE
# ====================================================================

@dataclass
class DynamischStroomType:
    """
    Een stromingstype dat dynamisch ontstaat uit de oceaan.
    Geen vaste enum - dit wordt tijdens runtime gecreëerd!
    """
    id: str
    naam: str
    geboorte_tijd: float
    ouder_stromingen: List[str]  # Waar komt dit type vandaan?
    
    # Karakteristieken van dit type (continue velden)
    concept_ruimte: np.ndarray  # De "smaak" van dit type
    intensiteits_profiel: np.ndarray  # Hoe gedraagt dit type zich?
    
    # Afstand tot andere types (voor clustering)
    affiniteiten: Dict[str, float] = field(default_factory=dict)
    
    @classmethod
    def uit_interferentie(cls, 
                         stroom_a: 'DynamischeStroom',
                         stroom_b: 'DynamischeStroom',
                         interferentie_veld: np.ndarray,
                         tijd: float) -> 'DynamischStroomType':
        """
        Creëer een nieuw type uit interferentie tussen twee stromingen.
        Dit is pure ontogenese - het type ontstaat uit de interactie.
        """
        # Genereer een unieke naam uit de interferentie
        naam = cls._genereer_naam(stroom_a, stroom_b, interferentie_veld)
        
        # De conceptruimte is de interferentie zelf
        concept_ruimte = interferentie_veld / np.linalg.norm(interferentie_veld)
        
        # Intensiteitsprofiel erf van beide ouders
        intensiteit = (stroom_a.type.intensiteits_profiel + stroom_b.type.intensiteits_profiel) / 2
        # Voeg een vleugje nieuwigheid toe
        intensiteit += np.random.randn(len(intensiteit)) * 0.1
        
        return cls(
            id=f"type_{hashlib.md5(naam.encode()).hexdigest()[:8]}",
            naam=naam,
            geboorte_tijd=tijd,
            ouder_stromingen=[stroom_a.id, stroom_b.id],
            concept_ruimte=concept_ruimte,
            intensiteits_profiel=intensiteit
        )
    
    @staticmethod
    def _genereer_naam(stroom_a: 'DynamischeStroom', 
                       stroom_b: 'DynamischeStroom',
                       veld: np.ndarray) -> str:
        """Genereer een organische naam uit de interferentie."""
        
        # Extract karakteristieke woorden uit beide stromingen
        a_kenmerken = stroom_a.type.naam.split('_') if hasattr(stroom_a.type, 'naam') else ['onbekend']
        b_kenmerken = stroom_b.type.naam.split('_') if hasattr(stroom_b.type, 'naam') else ['onbekend']
        
        # Neem de meest karakteristieke delen
        if a_kenmerken and b_kenmerken:
            voorvoegsel = a_kenmerken[0][:4]
            achtervoegsel = b_kenmerken[-1][:4]
            basis = f"{voorvoegsel}{achtervoegsel}"
        else:
            basis = "transcendent"
        
        # Voeg een unieke modifier toe gebaseerd op het veld
        modifier = hashlib.md5(veld.tobytes()).hexdigest()[:4]
        
        return f"{basis}_{modifier}"


@dataclass
class DynamischeStroom:
    """
    Een stroom met een dynamisch type dat tijdens runtime is ontstaan.
    """
    id: str
    type: DynamischStroomType  # Dynamisch, niet vast!
    naam: str
    
    # Continue velden
    intensiteit: float = 0.5
    coherentie: float = 0.7
    frequentie: float = 1.0
    fase: float = 0.0
    
    # Inhoud
    concept_veld: np.ndarray
    trend_richting: np.ndarray
    
    # Geschiedenis
    geschiedenis: List[float] = field(default_factory=list)
    
    def update(self, dt: float):
        """Update de stroom continu."""
        self.concept_veld += self.trend_richting * dt
        self.concept_veld /= np.linalg.norm(self.concept_veld)
        
        self.fase += self.frequentie * dt
        self.fase %= 2 * np.pi
        
        self.intensiteit += np.random.randn() * 0.01 * np.sqrt(dt)
        self.intensiteit = np.clip(self.intensiteit, 0.1, 1.0)
        
        self.geschiedenis.append(self.intensiteit)
        if len(self.geschiedenis) > 1000:
            self.geschiedenis.pop(0)


def creëer_zaadtype(naam: str, seed: int = None) -> DynamischStroomType:
    """Creëer een initieel type om mee te beginnen."""
    if seed:
        np.random.seed(seed)
    
    return DynamischStroomType(
        id=f"seed_{naam.lower()}",
        naam=naam,
        geboorte_tijd=0.0,
        ouder_stromingen=["oer_oceaan"],
        concept_ruimte=np.random.randn(50),
        intensiteits_profiel=np.random.randn(10) * 0.5 + 0.5
    )


class DynamischeStromingenManager:
    """
    Beheert stromingen waarvan de types tijdens runtime ontstaan.
    Dit is pure ontogenese - de oceaan creëert zijn eigen categorieën.
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger('Layer16')
        self.stromingen: Dict[str, DynamischeStroom] = {}
        self.types: Dict[str, DynamischStroomType] = {}  # Alle ontstane types
        
        # Zaadtypes (minimaal, alleen om te beginnen)
        self._initialiseer_zaadtypes()
        
        # Tracking
        self.type_ontstaan: List[Dict] = []
        self.interferentie_geschiedenis: List[Dict] = []
        
        self.logger.info("🌱 Dynamische stromingen manager geïnitialiseerd")
    
    def _initialiseer_zaadtypes(self):
        """Minimale initiële types - de rest ontstaat vanzelf."""
        zaad_namen = [
            "technologisch", "biologisch", "filosofisch", 
            "ecologisch", "cognitief"
        ]
        
        for naam in zaad_namen:
            type_obj = creëer_zaadtype(naam)
            self.types[type_obj.id] = type_obj
            
            # Maak een bijbehorende stroom
            stroom = self._creëer_stroom_van_type(type_obj)
            self.stromingen[stroom.id] = stroom
            
            self.logger.info(f"  → Zaadtype: {naam}")
    
    def _creëer_stroom_van_type(self, type_obj: DynamischStroomType) -> DynamischeStroom:
        """Creëer een stroom van een bepaald type."""
        return DynamischeStroom(
            id=f"stroom_{len(self.stromingen)}",
            type=type_obj,
            naam=f"{type_obj.naam}_stroom",
            concept_veld=type_obj.concept_ruimte.copy(),
            trend_richting=np.random.randn(50) * 0.01
        )
    
    def voeg_stroom_toe(self, type_obj: DynamischStroomType) -> DynamischeStroom:
        """Voeg een nieuwe stroom toe van een bestaand type."""
        stroom = self._creëer_stroom_van_type(type_obj)
        self.stromingen[stroom.id] = stroom
        return stroom
    
    async def detecteer_en_creëer(self, dt: float = 0.1):
        """
        Detecteer interferentie EN creëer nieuwe types/stroningen.
        Dit is de echte ontogenese-lus.
        """
        while True:
            # Update alle stromingen
            for stroom in self.stromingen.values():
                stroom.update(dt)
            
            # Detecteer interferentie
            if len(self.stromingen) >= 2:
                await self._check_interferentie()
            
            await asyncio.sleep(dt)
    
    async def _check_interferentie(self):
        """Check op interferentie en creëer nieuwe types."""
        stromen_lijst = list(self.stromingen.values())
        
        for _ in range(min(3, len(stromen_lijst))):
            i, j = random.sample(range(len(stromen_lijst)), 2)
            stroom_a = stromen_lijst[i]
            stroom_b = stromen_lijst[j]
            
            # Bereken interferentie
            fase_verschil = abs(stroom_a.fase - stroom_b.fase) % (2 * np.pi)
            fase_match = np.cos(fase_verschil)
            
            concept_overlap = np.dot(stroom_a.concept_veld, stroom_b.concept_veld)
            
            # Interferentie sterkte
            sterkte = fase_match * (1 - concept_overlap * 0.5)
            
            # Alleen bij significante interferentie
            if sterkte > 0.6 and random.random() < sterkte:
                # 🔥 HIER GEBEURT DE MAGIE!
                # Creëer een nieuw type uit de interferentie
                interferentie_veld = (stroom_a.concept_veld + stroom_b.concept_veld) / 2
                interferentie_veld += np.random.randn(50) * 0.2  # Creativiteit!
                
                nieuw_type = DynamischStroomType.uit_interferentie(
                    stroom_a, stroom_b, interferentie_veld, time.time()
                )
                
                # Voeg het nieuwe type toe
                self.types[nieuw_type.id] = nieuw_type
                
                # Creëer een nieuwe stroom van dit type
                nieuwe_stroom = self.voeg_stroom_toe(nieuw_type)
                
                # Track deze gebeurtenis
                event = {
                    'tijd': time.time(),
                    'type': 'type_ontstaan',
                    'ouders': [stroom_a.type.naam, stroom_b.type.naam],
                    'nieuw_type': nieuw_type.naam,
                    'sterkte': sterkte,
                    'stroom_a_id': stroom_a.id,
                    'stroom_b_id': stroom_b.id,
                    'nieuwe_stroom_id': nieuwe_stroom.id
                }
                self.type_ontstaan.append(event)
                
                self.logger.info(f"\n🌟 NIEUW TYPE ONTSTAAN!")
                self.logger.info(f"   Uit: {stroom_a.type.naam} × {stroom_b.type.naam}")
                self.logger.info(f"   → {nieuw_type.naam}")
                self.logger.info(f"   Sterkte: {sterkte:.2f}")
    
    def get_type_familie(self) -> Dict[str, List[str]]:
        """Bouw een stamboom van ontstane types."""
        familie = {}
        for type_id, type_obj in self.types.items():
            familie[type_obj.naam] = type_obj.ouder_stromingen
        return familie
    
    def get_stats(self) -> Dict[str, Any]:
        """Haal statistieken op."""
        return {
            'aantal_stromingen': len(self.stromingen),
            'aantal_types': len(self.types),
            'type_ontstaan': len(self.type_ontstaan),
            'type_familie': self.get_type_familie(),
            'recent': self.type_ontstaan[-5:] if self.type_ontstaan else []
        }


# ====================================================================
# KERN: DE OCEAAN (bevat ALLE V5 functionaliteit + Laag 16)
# ====================================================================

class OceanicNexusV7:
    """
    🌊 NEXUS ULTIMATE V7.0 - OCEANISCHE VERSIE VAN V5
    MET DYNAMISCHE LAAG 16
    
    Bevat ALLE functionaliteit van V5, maar nu als continue stroming:
    
    ✓ Document Tracking & Backtracing
    ✓ Cross-Domain Synthesis
    ✓ Ethical Research Assistant
    ✓ True Ontogenesis
    ✓ Chaos Detection & Safety
    ✓ ArXiv integratie
    ✓ Deep-dive PDF analyse
    ✓ Dashboard export
    ✓ 17-Lagen framework
    ✓ Dynamische Laag 16 - spontane interferentie 🌟 NIEUW
    
    MAAR: Alles stroomt continu, geen discrete cycli
    """
    
    def __init__(self, db_path="./nexus_memory", config_path="config.yaml"):
        # Logging
        self.log = loggers['nexus']
        self.safety_log = loggers['safety']
        self.ethics_log = loggers['ethics']
        self.ontology_log = loggers['ontology']
        self.synthesis_log = loggers['synthesis']
        self.memory_log = loggers['memory']
        self.research_log = loggers['research']
        self.tracking_log = loggers['tracking']
        self.ocean_log = loggers['ocean']
        self.layer16_log = loggers['layer16']
        
        self.log.info("="*100)
        self.log.info(" "*35 + "🌊 NEXUS ULTIMATE V7.0")
        self.log.info(" "*20 + "Oceanische Architectuur met ALLE V5 functionaliteit")
        self.log.info(" "*20 + "➕ Dynamische Laag 16 - Spontane Interferentie")
        self.log.info("="*100)
        
        # ====================================================================
        # CONFIGURATIE (IDENTIEK AAN V5)
        # ====================================================================
        
        self.config = self._load_config(config_path)
        db_path = self.config.get('memory', {}).get('path', db_path)
        
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        
        # ====================================================================
        # FASE 1: 17-LAGEN ARCHITECTUUR (IDENTIEK AAN V5)
        # ====================================================================
        
        self.log.info("Fase 1: Initialiseren 17-Lagen Architectuur...")
        self.framework = SeventeenLayerFramework()
        
        self.layer11 = Layer11_MetaContextualization(self.framework.layer10)
        self.layer12 = Layer12_Reconciliation(self.layer11)
        self.layer13 = Layer13_Ontogenesis(self.layer12)
        self.layer14 = Layer14_Worldbuilding(self.layer13)
        self.layer15 = Layer15_EthicalConvergence(self.layer14)
        self.layer16 = Layer16_Transcendence(self.layer15)
        self.layer17 = Layer17_AbsoluteIntegration(self.layer16)
        
        # Wereldbouw
        world_config = self.config.get('worldbuilding', {})
        self.primary_world = self.layer14.create_world(
            initial_agents=world_config.get('initial_agents', 25),
            normative_constraints=world_config.get(
                'normative_constraints',
                ['preserve_biodiversity', 'maintain_energy_balance', 'ensure_agent_welfare']
            )
        )
        
        # Collectief
        collective_config = self.config.get('collective', {})
        num_agents = collective_config.get('num_agents', 15)
        self.collective = self.layer16.form_collective(
            [f'research_agent_{i}' for i in range(num_agents)]
        )
        
        # ====================================================================
        # FASE 2: MEMORY (IDENTIEK AAN V5)
        # ====================================================================
        
        self.memory_log.info("Fase 2: Initialiseren Knowledge Systems...")
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        
        memory_config = self.config.get('memory', {})
        collection_name = memory_config.get('collection_name', "nexus_ultimate_memory")
        self.memory = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.emb_fn
        )
        
        # ====================================================================
        # FASE 3: KILLER FEATURES (IDENTIEK AAN V5)
        # ====================================================================
        
        self.log.info("Fase 3: Initialiseren Advanced Capabilities...")
        
        self.synthesizer = CrossDomainSynthesizer(
            layer12=self.layer12,
            layer13=self.layer13,
            memory=self.memory
        )
        
        self.ethics_assistant = EthicalResearchAssistant(
            layer15=self.layer15
        )
        
        # ====================================================================
        # FASE 4: THEORY-PRACTICE BRIDGES (IDENTIEK AAN V5)
        # ====================================================================
        
        self.log.info("Fase 4: Initialiseren Theory-Practice Bridges...")
        
        self.true_ontogenesis = TrueOntogenesis()
        
        safety_config = self.config.get('safety', {})
        self.chaos_detector = ChaosDetector(
            epsilon_threshold=safety_config.get('epsilon_threshold', 0.3),
            divergence_threshold=safety_config.get('divergence_threshold', 0.5),
            oscillation_threshold=safety_config.get('oscillation_threshold', 0.4),
            incoherence_threshold=safety_config.get('incoherence_threshold', 0.2)
        )
        
        # ====================================================================
        # FASE 5: RESEARCH INFRASTRUCTURE (IDENTIEK AAN V5)
        # ====================================================================
        
        self.research_log.info("Fase 5: Initialiseren Research Systems...")
        self.arxiv_client = arxiv.Client()
        self.crossref = Crossref()
        
        research_config = self.config.get('research', {})
        self.max_queue_size = research_config.get('max_queue_size', 30)
        self.synthesis_frequency = research_config.get('synthesis_frequency', 50)
        self.deep_dive_threshold = research_config.get('deep_dive_entropy_threshold', 0.75)
        self.max_papers_per_domain = research_config.get('max_papers_per_domain', 50)
        
        # Research queue (blijft bestaan, maar wordt anders gebruikt)
        self.explored_topics = set()
        self.research_queue = [self._generate_seed_topic()]
        
        # ====================================================================
        # FASE 6: DOCUMENT TRACKING (IDENTIEK AAN V5)
        # ====================================================================
        
        self.tracking_log.info("Fase 6: Initialiseren Document Tracking...")
        
        doc_tracking_config = self.config.get('document_tracking', {})
        tracking_db = doc_tracking_config.get('db_path', 'document_tracking.db')
        tracking_log = doc_tracking_config.get('log_file', 'verwerkte_documenten.json')
        
        self.doc_tracker = DocumentTracker(
            db_path=tracking_db,
            log_file=tracking_log
        )
        
        self.verwerkte_bestanden = self._laad_verwerkte_bestanden()
        
        # ====================================================================
        # FASE 7: STATE TRACKING (IDENTIEK AAN V5)
        # ====================================================================
        
        self.step_count = self._get_last_step()
        self.cycle_count = 0
        self.last_entropy = 0.5
        
        # Event tracking
        self.transcendence_events = []
        self.ethical_interventions = []
        self.synthesis_discoveries = []
        self.ontogenesis_events = []
        self.safety_events = []
        self.deep_dive_count = 0
        self.overgeslagen_documenten = 0
        
        # Domain tracking
        self.domain_papers = {}
        
        # Last known good state
        self.last_stable_state = None
        
        # ====================================================================
        # 🌊 NIEUW: OCEANISCHE LAGEN (continue velden)
        # ====================================================================
        
        self.ocean_log.info("Fase 8: Initialiseren Oceanische Lagen...")
        
        # Deze velden bevatten de continue toestand van alle V5 componenten
        self.ocean_fields = self._initialiseer_ocean_fields()
        
        # Oceanische tijd (continu)
        self.ocean_time = 0.0
        self.ocean_active = True
        
        # Oceanische geschiedenis (voor dashboard)
        self.ocean_history = defaultdict(list)
        
        # ====================================================================
        # 🌊 NIEUW: DYNAMISCHE LAAG 16
        # ====================================================================
        
        self.layer16_log.info("Fase 9: Initialiseren Dynamische Laag 16...")
        
        # Dynamische stromingen manager
        self.stromingen_manager = DynamischeStromingenManager(logger=self.layer16_log)
        
        # Achtergrondtaak voor stromingen
        self._stromingen_taak = None
        
        self.layer16_log.info(f"✓ Laag 16 actief - {len(self.stromingen_manager.stromingen)} initiële stromingen")
        
        self.log.info("="*100)
        self.log.info("✨ OCEANISCHE NEXUS V7.0: FULLY OPERATIONAL ✨")
        self.log.info(f"📊 Bevat ALLE V5 functionaliteiten + Dynamische Laag 16")
        self.log.info("="*100)
    
    # ========================================================================
    # OCEANISCHE LAGEN (nieuw)
    # ========================================================================
    
    def _initialiseer_ocean_fields(self) -> Dict[str, np.ndarray]:
        """Initialiseer continue velden voor alle V5 componenten."""
        fields = {}
        
        # Laag 1-17: continue versies van de framework lagen
        for i in range(1, 18):
            fields[f'layer_{i}_field'] = np.ones(10) * 0.5
        
        # V5 componenten als velden
        fields['coherence_field'] = np.ones(5) * 0.5
        fields['entropy_field'] = np.ones(5) * 0.5
        fields['synthesis_field'] = np.ones(8) * 0.5
        fields['ethics_field'] = np.ones(6) * 0.7
        fields['ontology_field'] = np.ones(12) * 0.4
        fields['chaos_field'] = np.ones(4) * 0.2
        
        # Document tracking veld
        fields['document_field'] = np.ones(20) * 0.0
        
        # Onderzoeksvelden
        fields['research_field'] = np.ones(15) * 0.3
        fields['discovery_field'] = np.ones(10) * 0.1
        
        return fields
    
    def _update_ocean_fields(self, dt: float):
        """
        Werk alle oceanische velden bij.
        Dit is waar V5's discrete logica continu wordt.
        """
        # Update coherence field op basis van framework
        if hasattr(self.framework, 'layer7') and hasattr(self.framework.layer7, 'synthesis'):
            coherence = self.framework.layer7.synthesis.coherence_score
            self.ocean_fields['coherence_field'] = coherence * np.ones(5) * 0.9 + \
                                                   self.ocean_fields['coherence_field'] * 0.1
        
        # Update entropy field
        self.ocean_fields['entropy_field'] = self.last_entropy * np.ones(5) * 0.8 + \
                                             self.ocean_fields['entropy_field'] * 0.2
        
        # Update discovery field op basis van nieuwe ontdekkingen
        if hasattr(self, 'synthesis_discoveries') and self.synthesis_discoveries:
            recent_count = len([d for d in self.synthesis_discoveries[-5:]])
            discovery_intensity = min(1.0, recent_count / 5)
            self.ocean_fields['discovery_field'] = discovery_intensity * np.ones(10) * 0.7 + \
                                                   self.ocean_fields['discovery_field'] * 0.3
        
        # Update document field
        if hasattr(self, 'doc_tracker'):
            try:
                cursor = self.doc_tracker.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM verwerkte_documenten")
                doc_count = cursor.fetchone()[0]
                doc_density = min(1.0, doc_count / 100)
                self.ocean_fields['document_field'] = doc_density * np.ones(20) * 0.8 + \
                                                      self.ocean_fields['document_field'] * 0.2
            except:
                pass
    
    # ========================================================================
    # ALLE V5 METHODES (IDENTIEK, MAAR NU OCEANISCH)
    # ========================================================================
    
    # === Configuratie ===
    
    def _load_config(self, config_path: str) -> dict:
        """IDENTIEK aan V5"""
        default_config = {
            'memory': {'path': './nexus_memory', 'collection_name': 'nexus_ultimate_memory'},
            'safety': {
                'epsilon_threshold': 0.3,
                'divergence_threshold': 0.5,
                'oscillation_threshold': 0.4,
                'incoherence_threshold': 0.2
            },
            'research': {
                'deep_dive_entropy_threshold': 0.75,
                'max_papers_per_domain': 50,
                'max_queue_size': 30,
                'synthesis_frequency': 50
            },
            'worldbuilding': {
                'initial_agents': 25,
                'normative_constraints': [
                    'preserve_biodiversity',
                    'maintain_energy_balance',
                    'ensure_agent_welfare'
                ]
            },
            'collective': {'num_agents': 15},
            'document_tracking': {
                'db_path': 'document_tracking.db',
                'log_file': 'verwerkte_documenten.json',
                'track_pdfs': True,
                'track_abstracts': True,
                'max_history': 1000
            }
        }
        
        if not os.path.exists(config_path):
            self.log.warning(f"⚠️ Configuratiebestand {config_path} niet gevonden. Gebruik standaardwaarden.")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
            return config
        except Exception as e:
            self.log.error(f"❌ Fout bij laden configuratie: {e}")
            return default_config
    
    # === Utility ===
    
    def _laad_verwerkte_bestanden(self) -> set:
        """IDENTIEK aan V5"""
        verwerkt = set()
        try:
            if os.path.exists('verwerkte_documenten.json'):
                with open('verwerkte_documenten.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for doc in data.get('documenten', []):
                        if 'bestandspad' in doc:
                            verwerkt.add(doc['bestandspad'])
        except Exception as e:
            self.tracking_log.warning(f"⚠️ Kon verwerkte documenten niet laden: {e}")
        return verwerkt
    
    def _get_last_step(self) -> int:
        """IDENTIEK aan V5"""
        try:
            return self.memory.count()
        except:
            return 0
    
    def _generate_seed_topic(self) -> str:
        """IDENTIEK aan V5 (dynamisch uit systeem)"""
        if not hasattr(self, 'explored_topics'):
            self.explored_topics = set()
        
        dynamische_domeinen = set()
        dynamische_concepten = set()
        
        # Uit ontologieën
        if hasattr(self, 'layer12') and hasattr(self.layer12, 'ontologies'):
            for ontology in self.layer12.ontologies.values():
                if hasattr(ontology, 'entities'):
                    for entity in list(ontology.entities)[:10]:
                        if len(entity) > 3:
                            if entity[0].isupper():
                                dynamische_domeinen.add(entity)
                            else:
                                dynamische_concepten.add(entity)
        
        # Uit memory
        if hasattr(self, 'memory'):
            try:
                results = self.memory.get(limit=100)
                if results and 'metadatas' in results:
                    for meta in results['metadatas']:
                        if meta and 'domain' in meta:
                            dynamische_domeinen.add(meta['domain'])
            except:
                pass
        
        # Genereer topic
        if dynamische_domeinen and dynamische_concepten:
            domein = random.choice(list(dynamische_domeinen))
            concept = random.choice(list(dynamische_concepten))
            return f"{domein} {concept}"
        elif dynamische_domeinen:
            domein = random.choice(list(dynamische_domeinen))
            return f"{domein} Research"
        else:
            return f"Exploration {datetime.now().strftime('%H%M%S')}"
    
    def _extract_next_topics(self, paper: arxiv.Result) -> List[str]:
        """IDENTIEK aan V5"""
        words = [w.strip("(),.;:\"") for w in paper.summary.split() if len(w) > 8]
        if len(words) < 2:
            return [self._generate_seed_topic()]
        
        keywords = random.sample(words, min(len(words), 3))
        
        for kw in keywords:
            seed = {
                'type': f'research_direction_{kw}',
                'stability_score': 0.8,
                'causal_efficacy': 0.85
            }
            novel = self.layer13.generate_novel_structure(seed)
            if novel:
                self.transcendence_events.append({
                    'type': 'novel_direction',
                    'source': paper.title,
                    'direction': novel.structure_type
                })
        
        return [f"{paper.primary_category} {kw}" for kw in keywords if paper.primary_category]
    
    def _calculate_entropy(self, current_title: str, past_context: str) -> float:
        """IDENTIEK aan V5"""
        if not past_context or "First" in past_context:
            return 0.8
        
        current_words = set(current_title.lower().split())
        past_words = set(past_context.lower().split())
        
        overlap = len(current_words & past_words)
        entropy = 1.0 - (overlap / max(len(current_words), 1))
        
        coherence_factor = self.framework.layer7.synthesis.coherence_score
        adjusted_entropy = entropy * (1 - 0.2 * coherence_factor)
        
        return max(0.1, min(adjusted_entropy, 0.95))
    
    def _deep_dive_analysis(self, paper_url: str, paper_id: str = None) -> Optional[str]:
        """IDENTIEK aan V5"""
        doc_id = paper_id or hashlib.md5(paper_url.encode()).hexdigest()
        pdf_url = paper_url.replace('/abs/', '/pdf/')
        
        self.research_log.info(f"🔬 DEEP-DIVE: Analyzing PDF from {pdf_url}")
        
        if hasattr(self, 'doc_tracker'):
            try:
                if self.doc_tracker.is_document_verwerkt(pdf_url):
                    self.research_log.info(f"⏭️ PDF al eerder verwerkt")
                    self.overgeslagen_documenten += 1
                    return None
            except:
                pass
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/pdf'}
            response = requests.get(pdf_url, timeout=30, headers=headers, stream=True)
            response.raise_for_status()
            
            with fitz.open(stream=io.BytesIO(response.content), filetype="pdf") as doc:
                full_text = ""
                total_pages = len(doc)
                pages_to_read = min(20, total_pages)
                
                for page_num in range(pages_to_read):
                    full_text += doc[page_num].get_text()
            
            self.deep_dive_count += 1
            
            if hasattr(self, 'doc_tracker'):
                try:
                    self.doc_tracker.document_verwerken(
                        bestandspad=pdf_url,
                        status="verwerkt",
                        opmerkingen=f"Deep dive, {len(full_text)} chars",
                        verwerking_type="deep_dive_pdf"
                    )
                except:
                    pass
            
            return full_text[:30000]
            
        except Exception as e:
            self.research_log.warning(f"⚠️ Deep-Dive failed: {e}")
            return None
    
    def _detect_domain(self, paper: arxiv.Result) -> ResearchDomain:
        """IDENTIEK aan V5"""
        category = paper.primary_category.lower() if paper.primary_category else ""
        title_lower = paper.title.lower()
        summary_lower = paper.summary.lower()
        
        if 'cs.ai' in category or 'cs.lg' in category or 'machine learning' in title_lower:
            return ResearchDomain.AI_ML
        elif 'q-bio' in category or 'bio' in category or 'genetic' in summary_lower:
            return ResearchDomain.BIOTECH
        elif 'surveillance' in title_lower or 'tracking' in title_lower:
            return ResearchDomain.SURVEILLANCE
        elif 'weapon' in title_lower or 'military' in title_lower:
            return ResearchDomain.WEAPONS
        elif 'autonomous' in title_lower or 'robot' in title_lower:
            return ResearchDomain.AUTONOMOUS
        
        observation = {
            'category': category,
            'title': title_lower,
            'summary': summary_lower[:200]
        }
        
        gap = self.true_ontogenesis.detect_ontological_gap(
            observation=observation,
            existing_structures=[d.value for d in ResearchDomain]
        )
        
        if gap and gap.gap_size > 0.7:
            self.ontogenesis_events.append({
                'type': 'new_domain',
                'gap': gap.id,
                'step': self.step_count
            })
        
        return ResearchDomain.GENERAL
    
    def _create_ontology_from_paper(self, paper: arxiv.Result) -> Ontology:
        """IDENTIEK aan V5"""
        words = set(w.lower() for w in paper.summary.split() if len(w) > 6)
        entities = set(list(words)[:10])
        
        relations = {}
        entity_list = list(entities)
        for i in range(min(5, len(entity_list)-1)):
            if i+1 < len(entity_list):
                relations[(entity_list[i], entity_list[i+1])] = 0.7
        
        categories = ['cs', 'physics', 'math', 'bio', 'econ']
        worldview = np.zeros(5)
        
        if paper.primary_category:
            for i, cat in enumerate(categories):
                if cat in paper.primary_category.lower():
                    worldview[i] = 1.0
        
        ontology = Ontology(
            id=f"paper_{self.step_count}",
            entities=entities,
            relations=relations,
            axioms=[paper.primary_category] if paper.primary_category else [],
            worldview_vector=worldview
        )
        
        self.layer12.register_ontology(ontology)
        return ontology
    
    def _save_stable_state(self):
        """IDENTIEK aan V5"""
        self.last_stable_state = {
            'step': self.step_count,
            'coherence': float(self.framework.layer7.synthesis.coherence_score),
            'ontologies': len(self.layer12.ontologies),
            'timestamp': time.time()
        }
    
    def toon_document_overzicht(self):
        """IDENTIEK aan V5"""
        if not hasattr(self, 'doc_tracker'):
            print("❌ Document tracker niet geïnitialiseerd")
            return
        
        self.doc_tracker.toon_overzicht()
        print(f"\n🔬 Deep-dive analyses: {self.deep_dive_count}")
        print(f"⏭️ Overgeslagen documenten: {self.overgeslagen_documenten}")
        print(f"🌉 Synthese ontdekkingen: {len(self.synthesis_discoveries)}")
    
    def _arxiv_request_with_backoff(self, topic: str, max_retries: int = 5) -> List:
        """IDENTIEK aan V5"""
        base_delay = 3
        max_delay = 60
        
        for attempt in range(max_retries):
            try:
                search = arxiv.Search(
                    query=topic,
                    max_results=3,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                return list(self.arxiv_client.results(search))
            except Exception as e:
                if '429' in str(e):
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    time.sleep(delay)
                else:
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (attempt + 1))
                    else:
                        return []
        return []
    
    def _run_cross_domain_synthesis(self):
        """IDENTIEK aan V5"""
        try:
            domain_list = sorted(self.domain_papers.items(), 
                                key=lambda x: len(x[1]), reverse=True)[:2]
            
            if len(domain_list) < 2:
                return
            
            domain_a, papers_a = domain_list[0]
            domain_b, papers_b = domain_list[1]
            
            self.synthesizer.build_domain_profile(domain_a, papers_a[-self.max_papers_per_domain:])
            self.synthesizer.build_domain_profile(domain_b, papers_b[-self.max_papers_per_domain:])
            
            bridges = self.synthesizer.find_bridges(domain_a, domain_b)
            
            if bridges:
                hypotheses = self.synthesizer.generate_hypotheses(bridges, max_hypotheses=3)
                self.synthesis_discoveries.append({
                    'domains': f"{domain_a} × {domain_b}",
                    'bridges': len(bridges),
                    'hypotheses': len(hypotheses),
                    'step': self.step_count
                })
        except Exception as e:
            self.synthesis_log.error(f"❌ Synthesis error: {e}")
    
    # ========================================================================
    # 🌊 OCEANISCHE VERSIE VAN RESEARCH CYCLE
    # ========================================================================
    
    async def _oceanic_flow(self):
        """
        Continue oceanische stroming.
        Dit vervangt de while loop in start_autonomous_evolution.
        """
        self.ocean_log.info("🌊 Oceanische stroming gestart - continu, geen cycli")
        
        while self.ocean_active:
            dt = 0.1  # Tijdstap
            
            # ================================================================
            # 1. Update oceanische velden
            # ================================================================
            self._update_ocean_fields(dt)
            
            # ================================================================
            # 2. Voer onderzoek uit ALS GOLF, niet als cyclus
            # ================================================================
            
            # Coherentie bepaalt onderzoeksintensiteit
            current_coherence = self.framework.layer7.synthesis.coherence_score
            
            # Hoge coherentie = diepgaand onderzoek
            if current_coherence > 0.8 and self.ocean_time % 5.0 < dt:
                await self._oceanic_research_wave(deep=True)
            
            # Lage coherentie = breed verkennend onderzoek
            elif current_coherence < 0.3 and self.ocean_time % 2.0 < dt:
                await self._oceanic_research_wave(deep=False)
            
            # Normaal onderzoek met tussenpozen
            elif self.ocean_time % 10.0 < dt:
                await self._oceanic_research_wave(deep=False)
            
            # ================================================================
            # 3. Continue processen (geen cycli!)
            # ================================================================
            
            # Chaos detectie (continu)
            if hasattr(self, 'chaos_detector'):
                system_metrics = {
                    'coherence': current_coherence,
                    'coherence_expected': 0.8,
                    'performance': 0.6,
                    'performance_expected': 0.7,
                    'complexity': len(self.framework.layer2.relations) / 1000.0,
                    'complexity_expected': 0.5
                }
                self.chaos_detector.run_safety_checks(system_metrics)
            
            # Collectieve cognitie (continu)
            if hasattr(self, 'layer16') and hasattr(self, 'collective'):
                self.layer16.collective_cognition_step(self.collective)
            
            # Wereld evolutie (continu)
            if hasattr(self, 'layer14') and hasattr(self, 'primary_world'):
                self.layer14.step_world(self.primary_world.id, timesteps=1)
            
            # Absolute integratie (continu)
            if hasattr(self, 'layer17'):
                meta_state = self.layer17.synthesize_absolute_integration()
                if meta_state.transcendence_achieved:
                    self.ocean_log.info(f"  ✨ TRANSCENDENTIE in stroming!")
            
            # ================================================================
            # 4. Update tijd en exporteer voor dashboard
            # ================================================================
            
            self.ocean_time += dt
            
            # Exporteer elke seconde voor dashboard
            if int(self.ocean_time) > int(self.ocean_time - dt):
                self._export_oceanic_state()
            
            await asyncio.sleep(dt)
    
    async def _oceanic_research_wave(self, deep: bool = False):
        """
        Een onderzoeksgolf in de oceaan.
        Dit vervangt run_research_cycle, maar gebruikt dezelfde logica.
        """
        if not self.research_queue:
            self.research_queue.append(self._generate_seed_topic())
        
        topic = self.research_queue.pop(0)
        
        if topic in self.explored_topics:
            self.research_queue.append(self._generate_seed_topic())
            return
        
        self.explored_topics.add(topic)
        self.ocean_log.info(f"🌊 Onderzoeksgolf: {topic} {'(diep)' if deep else '(breed)'}")
        
        try:
            papers = self._arxiv_request_with_backoff(topic)
            
            for paper in papers:
                # Check of al verwerkt
                if hasattr(self, 'doc_tracker') and self.doc_tracker.is_document_verwerkt(paper.entry_id):
                    self.overgeslagen_documenten += 1
                    continue
                
                # Registreer start
                if hasattr(self, 'doc_tracker'):
                    self.doc_tracker.document_verwerken(
                        bestandspad=paper.entry_id,
                        status="bezig",
                        opmerkingen=f"Start: {paper.title[:100]}",
                        verwerking_type="oceanic_wave"
                    )
                
                # Update step (voor compatibiliteit)
                self.step_count += 1
                
                # Bereken entropy
                past_context = "First integration."
                try:
                    results = self.memory.query(query_texts=[paper.title], n_results=1)
                    if results['documents'] and results['documents'][0]:
                        past_context = results['documents'][0][0][:400]
                except:
                    pass
                
                entropy = self._calculate_entropy(paper.title, past_context)
                self.last_entropy = entropy
                
                # Deep dive indien nodig
                analysis = paper.summary
                if deep and entropy > self.deep_dive_threshold:
                    full_text = self._deep_dive_analysis(paper.pdf_url)
                    if full_text:
                        analysis = full_text
                
                # Update framework
                observables = [("entropy", entropy), ("deep", 1.0 if deep else 0.0)]
                self.framework.run_full_cycle(observables, optimization_iterations=3)
                
                # Maak ontologie
                ontology = self._create_ontology_from_paper(paper)
                
                # Ethische evaluatie
                domain = self._detect_domain(paper)
                proposal = ResearchProposal(
                    title=paper.title,
                    description=paper.summary,
                    domain=domain,
                    objectives=[paper.title],
                    methods=["Computational", "Theoretical"],
                    potential_applications=["Research"],
                    stakeholders=['general_public', 'researchers']
                )
                ethical_eval = self.ethics_assistant.evaluate_proposal(proposal)
                
                if ethical_eval.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    self.ethical_interventions.append({
                        'paper': paper.title,
                        'risk': ethical_eval.overall_risk.value,
                        'step': self.step_count
                    })
                
                # Track domain
                domain_key = paper.primary_category.split('.')[0] if paper.primary_category else "unknown"
                if domain_key not in self.domain_papers:
                    self.domain_papers[domain_key] = []
                self.domain_papers[domain_key].append({'title': paper.title, 'id': paper.entry_id})
                
                # Sla op in memory
                self.memory.add(
                    ids=[f"step_{self.step_count}"],
                    documents=[f"STEP {self.step_count}: {paper.title}\n\n{analysis[:2500]}"],
                    metadatas=[{
                        "title": paper.title[:100],
                        "entropy": entropy,
                        "step": self.step_count,
                        "timestamp": datetime.now().isoformat(),
                        "domain": domain.value
                    }]
                )
                
                # Update document tracker
                if hasattr(self, 'doc_tracker'):
                    self.doc_tracker.document_verwerken(
                        bestandspad=paper.entry_id,
                        status="verwerkt",
                        verwerking_type="oceanic_wave_complete"
                    )
                
                # Genereer nieuwe topics
                new_topics = self._extract_next_topics(paper)
                self.research_queue.extend(new_topics)
                
                # Update cycle count (voor compatibiliteit)
                self.cycle_count += 1
                
                self.ocean_log.info(f"  ✓ Verwerkt: {paper.title[:60]}...")
                
                # Pauze tussen papers
                await asyncio.sleep(3)
            
            # Periodieke synthese
            if self.step_count % self.synthesis_frequency == 0:
                self._run_cross_domain_synthesis()
            
        except Exception as e:
            self.ocean_log.error(f"❌ Onderzoeksgolf error: {e}")
    
    def _export_oceanic_state(self):
        """Exporteer oceanische staat voor dashboard - inclusief Laag 16."""
        safety_status = self.chaos_detector.get_safety_status() if hasattr(self, 'chaos_detector') else {}
        ontogenesis_report = self.true_ontogenesis.examine_self() if hasattr(self, 'true_ontogenesis') else {}
        
        # Haal Laag 16 stats op
        layer16_stats = self.stromingen_manager.get_stats() if hasattr(self, 'stromingen_manager') else {}
        
        # Oceanische metrics
        state = {
            "step": self.step_count,
            "cycle": self.cycle_count,
            "ocean_time": self.ocean_time,
            "queue_size": len(self.research_queue),
            
            # Foundation metrics
            "observables": len(self.framework.layer1.observables),
            "relations": len(self.framework.layer2.relations),
            "functional_entities": len(self.framework.layer3.functional_entities),
            "global_coherence": float(self.framework.layer7.synthesis.coherence_score),
            
            # Higher layer metrics
            "ontology_count": len(self.layer12.ontologies),
            "world_sustainability": float(getattr(self.primary_world, 'sustainability_score', 0.0)),
            "collective_integration": float(getattr(self.collective, 'integration_level', 0.0)),
            
            # Layer 17
            "absolute_coherence": float(getattr(self.layer17, 'meta_world_state', 
                                                type('obj', (), {'global_coherence': 0.5})).global_coherence),
            "transcendence_achieved": getattr(self.layer17, 'meta_world_state', 
                                             type('obj', (), {'transcendence_achieved': False})).transcendence_achieved,
            
            # Research metrics
            "entropy": self.last_entropy,
            "deep_dive_count": self.deep_dive_count,
            "transcendence_events": len(self.transcendence_events),
            "ethical_interventions": len(self.ethical_interventions),
            "synthesis_discoveries": len(self.synthesis_discoveries),
            
            # Document tracking
            "document_tracking": {
                'overgeslagen': self.overgeslagen_documenten
            },
            
            # Ocean fields (samenvatting)
            "ocean_fields": {
                name: float(np.mean(field)) 
                for name, field in self.ocean_fields.items()
            },
            
            # Safety
            "safety": safety_status,
            
            # Ontogenesis
            "ontogenesis": ontogenesis_report,
            
            # 🌊 NIEUW: Laag 16 dynamische stromingen
            "layer16": {
                "aantal_stromingen": layer16_stats.get('aantal_stromingen', 0),
                "aantal_types": layer16_stats.get('aantal_types', 0),
                "type_ontstaan": layer16_stats.get('type_ontstaan', 0),
                "recent": [
                    {
                        'ouders': e.get('ouders', []),
                        'nieuw_type': e.get('nieuw_type', ''),
                        'sterkte': e.get('sterkte', 0.0)
                    }
                    for e in layer16_stats.get('recent', [])
                ]
            },
            
            "timestamp": time.time()
        }
        
        with open("nexus_ultimate_state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    # ========================================================================
    # MAIN OCEANISCHE LOOP
    # ========================================================================
    
    async def start_oceanic_evolution(self):
        """Start de oceanische evolutie met Laag 16."""
        self.log.info("="*100)
        self.log.info("🌊 OCEANISCHE NEXUS V7.0: EVOLUTIE GESTART")
        self.log.info("="*100)
        
        # Toon features
        self.log.info("Features (IDENTIEK aan V5):")
        self.log.info("  ✓ 17-Layer Intelligence")
        self.log.info("  ✓ Cross-Domain Synthesis")
        self.log.info("  ✓ Ethical Research Assistant")
        self.log.info("  ✓ Autopoietic World Simulation")
        self.log.info("  ✓ Collective Intelligence")
        self.log.info("  ✓ Deep-Dive PDF Analysis")
        self.log.info("  ✓ True Ontogenesis")
        self.log.info("  ✓ Chaos Detection & Safety")
        self.log.info("  ✓ Document Tracking & Backtracing")
        self.log.info("")
        self.log.info("🌊 NIEUW: Dynamische Laag 16 - Spontane Interferentie")
        self.log.info(f"   • {len(self.stromingen_manager.stromingen)} initiële stromingen")
        self.log.info(f"   • Nieuwe types ontstaan spontaan uit interferentie")
        self.log.info("="*100)
        
        # Start dynamische stromingen op achtergrond
        self._stromingen_taak = asyncio.create_task(
            self.stromingen_manager.detecteer_en_creëer()
        )
        
        try:
            await self._oceanic_flow()
        except KeyboardInterrupt:
            await self.stop_oceanic()
    
    async def stop_oceanic(self):
        """Stop de oceanische evolutie."""
        self.log.info("\n🛑 Oceaan tot rust brengen...")
        self.ocean_active = False
        
        if self._stromingen_taak:
            self._stromingen_taak.cancel()
        
        if hasattr(self, 'doc_tracker'):
            self.doc_tracker.close()
            self.toon_document_overzicht()
        
        self.log.info("✓ Oceaan rust")
    
    def cleanup(self):
        """Opruimen (voor compatibiliteit met V5)."""
        if hasattr(self, 'doc_tracker'):
            self.doc_tracker.close()


# ====================================================================
# MAIN - START OCEANISCHE NEXUS
# ====================================================================

async def main():
    """Start de oceanische Nexus."""
    nexus = OceanicNexusV7()
    
    try:
        await nexus.start_oceanic_evolution()
    except KeyboardInterrupt:
        await nexus.stop_oceanic()
        print("\n\n👋 Oceanische Nexus gestopt.")


def start_v8():
    """Start V8 (synchronous wrapper voor async)."""
    asyncio.run(main())


if __name__ == "__main__":
    start_v8()