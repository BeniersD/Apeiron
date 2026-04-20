"""
NEXUS ULTIMATE V5.0 - COMPLETE THEORY-PRACTICE INTEGRATION + DOCUMENT TRACKING
================================================================================================
17-Layer Framework + True Ontogenesis + Chaos Detection + Cross-Domain Synthesis + Ethics
Document Tracking + Backtracing + Duplicate Prevention
The Ultimate Self-Evolving Intelligence with Genuine Self-Modification and Safety Locks
================================================================================================

BRIDGES CLOSED:
✓ Aion Paradox: System creates its own structures at runtime
✓ Chaos Control: Mathematical ε tracking with graduated safety responses
✓ Self-Modification: Genuine but controlled emergent structure creation
✓ Safety Locks: Emergency shutdown on critical error bounds
✓ Document Tracking: No duplicate processing + full audit trail ⭐ NEW
✓ Backtracing: Trace which documents led to which insights ⭐ NEW
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
from chromadb.utils import embedding_functions
import time, json, arxiv, os, random
from habanero import Crossref
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import hashlib

# ====================================================================
# DOCUMENT TRACKER IMPORT
# ====================================================================
from document_tracker import DocumentTracker

# ====================================================================
# LOGGING CONFIGURATIE
# ====================================================================

def setup_logging():
    """Configureer logging voor het hele systeem - MET ZICHTBARE OUTPUT."""
    # Creëer logs directory als die niet bestaat
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Timestamp voor log bestand
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/nexus_ultimate_{timestamp}.log'
    
    # Configureer root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Verwijder bestaande handlers om duplicatie te voorkomen
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 🔥 CRUCIAL: StreamHandler voor console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # FileHandler voor bestand (met meer details)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Meer details in bestand
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)
    
    # Logger voor specifieke componenten
    loggers = {
        'nexus': logging.getLogger('Nexus'),
        'safety': logging.getLogger('Safety'),
        'ethics': logging.getLogger('Ethics'),
        'ontology': logging.getLogger('Ontology'),
        'synthesis': logging.getLogger('Synthesis'),
        'memory': logging.getLogger('Memory'),
        'research': logging.getLogger('Research'),
        'tracking': logging.getLogger('DocumentTracking')  # ⭐ NIEUW
    }
    
    print(f"\n📝 Logging geconfigureerd:")
    print(f"   - Console: ZICHTBAAR (INFO level)")
    print(f"   - Bestand: {log_file} (DEBUG level)\n")
    
    return loggers

# Initialize logging
loggers = setup_logging()

# Import 17-layer architecture
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

# Import killer features
from cross_domain_synthesis import CrossDomainSynthesizer
from ethical_research_assistant import (
    EthicalResearchAssistant,
    ResearchProposal,
    ResearchDomain,
    RiskLevel
)

# Import theory-practice bridges
from true_ontogenesis import TrueOntogenesis, OntologicalGap
from chaos_detection import ChaosDetector, SystemState, SafetyLevel


class NexusUltimateV5:
    """
    ================================================================================================
    NEXUS ULTIMATE V5.0 - THEORY-PRACTICE INTEGRATION + DOCUMENT TRACKING
    ================================================================================================
    
    NEW in V5:
    - Document Tracking: Houdt bij welke documenten zijn verwerkt
    - Duplicate Prevention: Geen dubbele verwerking van papers
    - Backtracing: Traceer welke documenten leidden tot welke inzichten
    - Audit Trail: Volledige geschiedenis van alle verwerkingen
    - Rapportage: Overzicht van verwerkte documenten
    
    Integrates:
    - 17-Layer Intelligence Framework (Observables → Transcendence)
    - Autonomous Research Navigator (ArXiv exploration with deep-dive)
    - Cross-Domain Synthesis Engine (Layer 12 + Layer 13 powered)
    - Ethical Research Assistant (Layer 15 powered)
    - True Ontogenesis (Runtime structure creation)
    - Chaos Detection & Safety (ε bounds + shutdown)
    - Document Tracking & Backtracing ⭐ NEW
    - Persistent Memory (ChromaDB with semantic search)
    - Real-time Dashboard Export
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
        
        self.log.info("="*100)
        self.log.info(" "*35 + "🌌 NEXUS ULTIMATE V5.0")
        self.log.info(" "*20 + "Complete Theory-Practice Integration with Document Tracking")
        self.log.info("="*100)
        
        # ====================================================================
        # CONFIGURATIE LADEN
        # ====================================================================
        self.config = self._load_config(config_path)
        self.log.info(f"⚙️ Configuratie geladen van: {config_path}")
        
        # Gebruik configuratie voor database pad
        db_path = self.config.get('memory', {}).get('path', db_path)
        
        # Create database directory
        if not os.path.exists(db_path):
            os.makedirs(db_path)
            self.log.info(f"📁 Database directory aangemaakt: {db_path}")
        
        # ====================================================================
        # PHASE 1: 17-LAYER ARCHITECTURE
        # ====================================================================
        
        self.log.info("Phase 1: Initializing 17-Layer Architecture...")
        self.framework = SeventeenLayerFramework()
        
        # Initialize all higher layers
        self.layer11 = Layer11_MetaContextualization(self.framework.layer10)
        self.layer12 = Layer12_Reconciliation(self.layer11)
        self.layer13 = Layer13_Ontogenesis(self.layer12)
        self.layer14 = Layer14_Worldbuilding(self.layer13)
        self.layer15 = Layer15_EthicalConvergence(self.layer14)
        self.layer16 = Layer16_Transcendence(self.layer15)
        self.layer17 = Layer17_AbsoluteIntegration(self.layer16)
        
        # Haal wereldbouw configuratie op
        world_config = self.config.get('worldbuilding', {})
        
        # Create initial autopoietic world
        self.primary_world = self.layer14.create_world(
            initial_agents=world_config.get('initial_agents', 25),
            normative_constraints=world_config.get(
                'normative_constraints',
                ['preserve_biodiversity', 'maintain_energy_balance', 'ensure_agent_welfare']
            )
        )
        self.log.info(f"🌍 Wereld gecreëerd met {world_config.get('initial_agents', 25)} agents")
        
        # Create collective intelligence
        collective_config = self.config.get('collective', {})
        num_agents = collective_config.get('num_agents', 15)
        self.collective = self.layer16.form_collective(
            [f'research_agent_{i}' for i in range(num_agents)]
        )
        self.log.info(f"🤝 Collectief gevormd met {num_agents} agents")
        
        self.log.info("✓ All 17 layers initialized")
        
        # ====================================================================
        # PHASE 2: MEMORY & KNOWLEDGE BASE
        # ====================================================================
        
        self.memory_log.info("Phase 2: Initializing Knowledge Systems...")
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        
        memory_config = self.config.get('memory', {})
        collection_name = memory_config.get('collection_name', "nexus_ultimate_memory")
        self.memory = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.emb_fn
        )
        
        self.memory_log.info(f"✓ Knowledge base ready: {collection_name} ({self.memory.count()} entries)")
        
        # ====================================================================
        # PHASE 3: KILLER FEATURES
        # ====================================================================
        
        self.log.info("Phase 3: Initializing Advanced Capabilities...")
        
        # Cross-Domain Synthesis Engine
        self.synthesizer = CrossDomainSynthesizer(
            layer12=self.layer12,
            layer13=self.layer13,
            memory=self.memory
        )
        self.synthesis_log.info("✓ Cross-Domain Synthesis Engine active")
        
        # Ethical Research Assistant
        self.ethics_assistant = EthicalResearchAssistant(
            layer15=self.layer15
        )
        self.ethics_log.info("✓ Ethical Research Assistant active")
        
        # ====================================================================
        # PHASE 4: THEORY-PRACTICE BRIDGES
        # ====================================================================
        
        self.log.info("Phase 4: Initializing Theory-Practice Bridges...")
        
        # True Ontogenesis - System creates its own structures
        self.true_ontogenesis = TrueOntogenesis()
        self.ontology_log.info("✓ True Ontogenesis active (Aion Paradox bridge)")
        
        # Haal safety configuratie op
        safety_config = self.config.get('safety', {})
        
        # Chaos Detection - Mathematical safety with shutdown
        self.chaos_detector = ChaosDetector(
            epsilon_threshold=safety_config.get('epsilon_threshold', 0.3),
            divergence_threshold=safety_config.get('divergence_threshold', 0.5),
            oscillation_threshold=safety_config.get('oscillation_threshold', 0.4),
            incoherence_threshold=safety_config.get('incoherence_threshold', 0.2)
        )
        self.safety_log.info("✓ Chaos Detection & Safety active (ε tracking + shutdown)")
        
        # ====================================================================
        # PHASE 5: RESEARCH INFRASTRUCTURE
        # ====================================================================
        
        self.research_log.info("Phase 5: Initializing Research Systems...")
        self.arxiv_client = arxiv.Client()
        self.crossref = Crossref()
        
        # Haal research configuratie op
        research_config = self.config.get('research', {})
        self.max_queue_size = research_config.get('max_queue_size', 30)
        self.synthesis_frequency = research_config.get('synthesis_frequency', 50)
        self.deep_dive_threshold = research_config.get('deep_dive_entropy_threshold', 0.75)
        self.max_papers_per_domain = research_config.get('max_papers_per_domain', 50)
        
        self.research_log.info(f"  Deep-dive threshold: {self.deep_dive_threshold}")
        self.research_log.info(f"  Synthesis frequency: every {self.synthesis_frequency} cycles")
        
        # 🔧 FIX: Eerst explored_topics initialiseren, DAN pas queue
        self.explored_topics = set()
        
        # Autonomous research queue
        self.research_queue = [self._generate_seed_topic()]
        
        self.research_log.info("✓ Research infrastructure ready")
        
        # ====================================================================
        # PHASE 6: DOCUMENT TRACKING ⭐ NIEUW
        # ====================================================================
        
        self.tracking_log.info("Phase 6: Initializing Document Tracking...")
        
        # Haal document tracking configuratie op
        doc_tracking_config = self.config.get('document_tracking', {})
        tracking_db = doc_tracking_config.get('db_path', 'document_tracking.db')
        tracking_log = doc_tracking_config.get('log_file', 'verwerkte_documenten.json')
        
        # Initialize document tracker
        self.doc_tracker = DocumentTracker(
            db_path=tracking_db,
            log_file=tracking_log
        )
        
        self.tracking_log.info(f"✓ Document Tracker active (db: {tracking_db})")
        
        # Laad eerder verwerkte documenten
        self.verwerkte_bestanden = self._laad_verwerkte_bestanden()
        self.tracking_log.info(f"📚 {len(self.verwerkte_bestanden)} documenten eerder verwerkt")
        
        # ====================================================================
        # PHASE 7: STATE TRACKING
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
        self.overgeslagen_documenten = 0  # ⭐ NIEUW: teller voor overgeslagen docs
        
        # Domain tracking for synthesis
        self.domain_papers = {}  # domain -> list of papers
        
        # Last known good state (for rollback)
        self.last_stable_state = None
        
        self.log.info("="*100)
        self.log.info("✨ NEXUS ULTIMATE V5.0: FULLY OPERATIONAL ✨")
        self.log.info(f"📊 Starting from step {self.step_count}")
        self.log.info("="*100)
    
    # ========================================================================
    # CONFIGURATIE LADEN
    # ========================================================================
    
    def _load_config(self, config_path: str) -> dict:
        """
        Laad configuratie van YAML bestand.
        Als het bestand niet bestaat, retourneer een standaard configuratie.
        """
        default_config = {
            'memory': {
                'path': './nexus_memory',
                'collection_name': 'nexus_ultimate_memory'
            },
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
            'collective': {
                'num_agents': 15
            },
            'document_tracking': {  # ⭐ NIEUW
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
                # Merge met default config voor ontbrekende waarden
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
            self.log.info(f"✓ Configuratie geladen: {len(config)} secties")
            return config
        except Exception as e:
            self.log.error(f"❌ Fout bij laden configuratie: {e}. Gebruik standaardwaarden.")
            return default_config
    
    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================
    
    def _laad_verwerkte_bestanden(self) -> set:
        """Laad lijst van eerder verwerkte bestanden uit tracker."""
        verwerkt = set()
        
        try:
            # Probeer uit JSON log te laden
            if os.path.exists('verwerkte_documenten.json'):
                with open('verwerkte_documenten.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for doc in data.get('documenten', []):
                        if 'bestandspad' in doc:
                            verwerkt.add(doc['bestandspad'])
            
            self.tracking_log.info(f"📋 {len(verwerkt)} eerder verwerkte documenten gevonden")
        except Exception as e:
            self.tracking_log.warning(f"⚠️ Kon verwerkte documenten niet laden: {e}")
        
        return verwerkt
    
    def _get_last_step(self) -> int:
        """Get last step from memory."""
        try:
            count = self.memory.count()
            self.memory_log.info(f"📚 Memory contains {count} existing entries")
            return count
        except:
            self.memory_log.info("📚 No existing memory found, starting fresh")
            return 0
    
    def _generate_seed_topic(self) -> str:
        """
        Generate intelligent seed topics based on current system state.
        PURE DYNAMISCHE VERSIE: Gebruikt ALLEEN wat het systeem zelf heeft ontdekt.
        Geen vaste lijsten meer!
        """

        # 🔧 FIX: Zorg dat explored_topics bestaat
        if not hasattr(self, 'explored_topics'):
            self.explored_topics = set()
        
        if not hasattr(self, 'research_queue'):
            self.research_queue = []

        # ====================================================================
        # BRON 1: Haal domeinen uit bestaande ontologieën (Layer 12)
        # ====================================================================
        dynamische_domeinen = set()
        dynamische_concepten = set()
        
        if hasattr(self, 'layer12') and hasattr(self.layer12, 'ontologies'):
            for onto_id, ontology in self.layer12.ontologies.items():
                if hasattr(ontology, 'entities'):
                    for entity in list(ontology.entities)[:10]:  # Max 10 per ontology
                        if len(entity) > 3:  # Alleen betekenisvolle woorden
                            if entity[0].isupper():  # Lijkt op domeinnaam
                                dynamische_domeinen.add(entity)
                            else:
                                dynamische_concepten.add(entity)
        
        self.research_log.debug(f"📚 Uit ontologieën: {len(dynamische_domeinen)} domeinen, {len(dynamische_concepten)} concepten")
        
        # ====================================================================
        # BRON 2: Haal uit memory (ChromaDB) - metadata
        # ====================================================================
        if hasattr(self, 'memory'):
            try:
                results = self.memory.get(limit=100)  # Haal laatste 100 op
                if results and 'metadatas' in results:
                    for meta in results['metadatas']:
                        if meta:
                            # Uit domain veld
                            if 'domain' in meta and meta['domain']:
                                dynamische_domeinen.add(meta['domain'])
                            
                            # Uit title - extraheer keywords
                            if 'title' in meta and meta['title']:
                                titel_woorden = meta['title'].split()
                                for woord in titel_woorden[:3]:
                                    if len(woord) > 4 and woord[0].isupper():
                                        dynamische_domeinen.add(woord)
                                    
                            # Uit paper_id of andere identifiers
                            if 'paper_id' in meta and meta['paper_id']:
                                # Soms zitten er hints in IDs
                                pass
            except Exception as e:
                self.research_log.debug(f"Kon memory niet uitlezen: {e}")
        
        # ====================================================================
        # BRON 3: Haal uit explored topics
        # ====================================================================
        if hasattr(self, 'explored_topics'):
            for topic in list(self.explored_topics)[-50:]:  # Laatste 50
                woorden = topic.split()
                for woord in woorden:
                    # Filter op lengte en hoofdletters (kandidaat-domeinen)
                    if len(woord) > 4 and woord[0].isupper():
                        dynamische_domeinen.add(woord)
                    # Ook kleinere woorden kunnen concepten zijn
                    elif len(woord) > 3 and woord not in ['and', 'the', 'for', 'with']:
                        dynamische_concepten.add(woord)
        
        self.research_log.debug(f"📚 Uit explored topics: {len(dynamische_domeinen)} domeinen, {len(dynamische_concepten)} concepten")
        
        # ====================================================================
        # BRON 4: Haal uit transcendente inzichten (Layer 16)
        # ====================================================================
        if hasattr(self, 'layer16') and hasattr(self.layer16, 'transcendent_insights'):
            for insight in self.layer16.transcendent_insights[-20:]:  # Laatste 20
                if 'type' in insight:
                    dynamische_concepten.add(insight['type'])
                if 'description' in insight:
                    woorden = insight['description'].split()
                    for woord in woorden[:5]:
                        if len(woord) > 5:
                            if woord[0].isupper():
                                dynamische_domeinen.add(woord)
                            else:
                                dynamische_concepten.add(woord)
        
        # ====================================================================
        # BRON 5: Haal uit true ontogenesis (zelf-gecreëerde structuren)
        # ====================================================================
        if hasattr(self, 'true_ontogenesis'):
            if hasattr(self.true_ontogenesis, 'created_enums'):
                for enum_name, enum_values in self.true_ontogenesis.created_enums.items():
                    dynamische_domeinen.add(enum_name)
                    for value in list(enum_values)[:5]:
                        try:
                            value_str = str(value)
                            if len(value_str) > 3:
                                dynamische_concepten.add(value_str)
                        except:
                            pass
            
            if hasattr(self.true_ontogenesis, 'created_classes'):
                for class_name in self.true_ontogenesis.created_classes.keys():
                    if len(class_name) > 3:
                        dynamische_domeinen.add(class_name)
        
        # ====================================================================
        # BRON 6: Haal uit synthesis discoveries
        # ====================================================================
        if hasattr(self, 'synthesis_discoveries'):
            for discovery in self.synthesis_discoveries[-20:]:  # Laatste 20
                if 'domains' in discovery:
                    for domain in discovery['domains'].split(' × '):
                        if len(domain) > 3:
                            dynamische_domeinen.add(domain)
                if 'hypotheses' in discovery and discovery['hypotheses']:
                    for hypo in discovery['hypotheses'][:3]:
                        if isinstance(hypo, str) and len(hypo) > 5:
                            woorden = hypo.split()
                            for woord in woorden[:3]:
                                if len(woord) > 4:
                                    dynamische_concepten.add(woord)
        
        self.research_log.debug(f"📚 Totaal na alle bronnen: {len(dynamische_domeinen)} domeinen, {len(dynamische_concepten)} concepten")
        
        # ====================================================================
        # ALS ER NOG STEEDS NIKS IS: Gebruik wat we hebben uit de omgeving
        # ====================================================================
        if len(dynamische_domeinen) == 0 and len(dynamische_concepten) == 0:
            # Dit gebeurt alleen bij de allereerste start
            self.research_log.info("🌱 Eerste start: nog geen data, gebruik basis observaties")
            
            # Gebruik de seed topic zelf als bron
            if hasattr(self, 'research_queue') and self.research_queue:
                for seed in self.research_queue[:5]:
                    woorden = seed.split()
                    for woord in woorden:
                        if len(woord) > 4:
                            dynamische_domeinen.add(woord)
            
            # Als nog steeds leeg, gebruik tijdelijke placeholder
            if len(dynamische_domeinen) == 0:
                return f"Initial Exploration {datetime.now().strftime('%H%M%S')}"
        
        # ====================================================================
        # GENEREER UNIEK TOPIC UIT ALLEEN DYNAMISCHE BRONNEN
        # ====================================================================
        max_pogingen = 30
        for poging in range(max_pogingen):
            
            # Bepaal wat voor topic we maken op basis van beschikbare data
            if dynamische_domeinen and dynamische_concepten:
                # We hebben beide: maak combinatie
                domein = random.choice(list(dynamische_domeinen))
                concept = random.choice(list(dynamische_concepten))
                topic = f"{domein} {concept}"
                
            elif len(dynamische_domeinen) >= 2:
                # Alleen domeinen: combineer twee domeinen
                d1 = random.choice(list(dynamische_domeinen))
                d2 = random.choice(list(dynamische_domeinen))
                topic = f"{d1}-{d2} Integration"
                
            elif dynamische_domeinen:
                # Alleen één domein: voeg algemeen concept toe
                domein = random.choice(list(dynamische_domeinen))
                topic = f"{domein} {random.choice(['Dynamics', 'Patterns', 'Structure', 'Evolution'])}"
                
            elif dynamische_concepten:
                # Alleen concepten: maak er een domein van
                concept = random.choice(list(dynamische_concepten))
                topic = f"{concept.capitalize()} Framework"
                
            else:
                # Zou niet moeten gebeuren, maar voor de zekerheid
                topic = f"Research Topic {random.randint(100, 999)}"
            
            # Maak de topic netjes (verwijder rare tekens)
            topic = ' '.join(topic.split())  # Normaliseer spaties
            
            # Check of topic uniek is
            if topic and topic not in self.explored_topics and topic not in self.research_queue:
                self.research_log.debug(f"✨ Dynamisch gegenereerd: {topic}")
                return topic
        
        # ====================================================================
        # UITERSTE FALLBACK (geen vaste lijst, maar gebaseerd op bestaande data)
        # ====================================================================
        if dynamische_domeinen:
            # Gebruik een bestaand domein met unieke modifier
            basis = random.choice(list(dynamische_domeinen))
            modifier = hashlib.md5(str(time.time()).encode()).hexdigest()[:4]
            return f"{basis} Exploration {modifier}"
        elif dynamische_concepten:
            basis = random.choice(list(dynamische_concepten))
            return f"Advanced {basis} Research"
        else:
            # Allerlaatste redmiddel - maar nog steeds geen vaste lijst!
            return f"Emergent Topic {datetime.now().strftime('%H%M%S')}"

    def _extract_next_topics(self, paper: arxiv.Result) -> List[str]:
        """
        Extract next research topics using Layer 13 ontogenesis.
        Generates genuinely novel directions.
        """
        # Basic keyword extraction
        words = [w.strip("(),.;:\"") for w in paper.summary.split() if len(w) > 8]
        
        if len(words) < 2:
            return [self._generate_seed_topic()]
        
        keywords = random.sample(words, min(len(words), 3))
        
        # Layer 13: Generate novel structure from keywords
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
                self.research_log.info(f"✨ Novel direction generated: {novel.structure_type}")
        
        topics = [f"{paper.primary_category} {kw}" for kw in keywords if paper.primary_category]
        self.research_log.debug(f"Extracted {len(topics)} next topics")
        return topics
    
    def _calculate_entropy(self, current_title: str, past_context: str) -> float:
        """
        Calculate information entropy using Layer 7 synthesis.
        """
        if not past_context or "First" in past_context:
            return 0.8
        
        # Basic overlap calculation
        current_words = set(current_title.lower().split())
        past_words = set(past_context.lower().split())
        
        overlap = len(current_words & past_words)
        entropy = 1.0 - (overlap / max(len(current_words), 1))
        
        # Adjust based on global coherence
        coherence_factor = self.framework.layer7.synthesis.coherence_score
        adjusted_entropy = entropy * (1 - 0.2 * coherence_factor)
        
        final_entropy = max(0.1, min(adjusted_entropy, 0.95))
        self.research_log.debug(f"Entropy: {final_entropy:.3f} (base: {entropy:.3f}, coherence: {coherence_factor:.3f})")
        return final_entropy

    def _deep_dive_analysis(self, paper_url: str, paper_id: str = None) -> Optional[str]:
        """
        Download and analyze full PDF met document tracking.
        DEFINITIEVE FIX: Gebruikt de URL alleen voor downloaden, nooit als bestandspad.
        """
        
        # Genereer een unieke ID voor dit document
        doc_id = paper_id or hashlib.md5(paper_url.encode()).hexdigest()
        
        # Zet de abstract URL om naar PDF URL
        pdf_url = paper_url.replace('/abs/', '/pdf/')
        
        self.research_log.info(f"🔬 DEEP-DIVE: Analyzing PDF from {pdf_url}")
        
        # 🔥 CRUCIAL: Gebruik de URL ALLEEN voor database lookup, NIET als bestandspad
        if hasattr(self, 'doc_tracker'):
            try:
                # We gebruiken pdf_url als identifier in de database
                # Dit veroorzaakt GEEN bestandspad operatie
                if self.doc_tracker.is_document_verwerkt(pdf_url):
                    self.research_log.info(f"⏭️ PDF al eerder verwerkt: {pdf_url}")
                    self.overgeslagen_documenten += 1
                    return None
            except Exception as e:
                self.research_log.warning(f"⚠️ Kon document status niet checken: {e}")
        
        # Download de PDF
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/pdf'
            }
            
            self.research_log.info(f"📥 Downloading PDF...")
            response = requests.get(pdf_url, timeout=30, headers=headers, stream=True)
            response.raise_for_status()
            
            # Controleer of we een PDF hebben
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and not pdf_url.endswith('.pdf'):
                self.research_log.warning(f"⚠️ Geen PDF ontvangen: {content_type}")
                return None
            
            # Parse de PDF
            self.research_log.info(f"📄 Parsing PDF...")
            try:
                with fitz.open(stream=io.BytesIO(response.content), filetype="pdf") as doc:
                    full_text = ""
                    total_pages = len(doc)
                    pages_to_read = min(20, total_pages)
                    
                    for page_num in range(pages_to_read):
                        page = doc[page_num]
                        full_text += page.get_text()
                    
                    self.research_log.info(f"   Gelezen: {pages_to_read}/{total_pages} pagina's")
                    
            except Exception as pdf_error:
                self.research_log.error(f"❌ PDF parsing error: {pdf_error}")
                return None
            
            self.deep_dive_count += 1
            text_length = len(full_text)
            self.research_log.info(f"✓ Succesvol: {text_length} karakters geëxtraheerd")
            
            # Registreer in document tracker (ALLEEN als string, niet als bestandspad)
            if hasattr(self, 'doc_tracker'):
                try:
                    self.doc_tracker.document_verwerken(
                        bestandspad=pdf_url,  # Dit is een string, wordt niet als bestand gebruikt
                        status="verwerkt",
                        opmerkingen=f"Deep dive analyse, {text_length} karakters",
                        verwerking_type="deep_dive_pdf"
                    )
                except Exception as e:
                    self.research_log.warning(f"⚠️ Kon document niet registreren: {e}")
            
            return full_text[:30000]
            
        except requests.exceptions.Timeout:
            self.research_log.warning(f"⚠️ Deep-Dive timeout: {pdf_url}")
            return None
        except requests.exceptions.RequestException as e:
            self.research_log.warning(f"⚠️ Deep-Dive request failed: {e}")
            return None
        except Exception as e:
            self.research_log.error(f"❌ Deep-Dive failed: {e}")
            return None
        
    def _detect_domain(self, paper: arxiv.Result) -> ResearchDomain:
        """
        Detect research domain from paper.
        Now checks both predefined AND emergent domains!
        """
        category = paper.primary_category.lower() if paper.primary_category else ""
        title_lower = paper.title.lower()
        summary_lower = paper.summary.lower()
        
        # Check predefined domains first
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
        
        # ⭐ Check if this fits emergent domains
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
            # GENUINELY NEW DOMAIN
            self.ontology_log.info(f"🌟 NEW DOMAIN DETECTED: gap size {gap.gap_size:.2f}")
            self.ontogenesis_events.append({
                'type': 'new_domain',
                'gap': gap.id,
                'step': self.step_count
            })
        
        return ResearchDomain.GENERAL
    
    def _create_ontology_from_paper(self, paper: arxiv.Result) -> Ontology:
        """
        Create an ontology representation of the paper using Layer 12.
        """
        # Extract key concepts (simplified)
        words = set(w.lower() for w in paper.summary.split() if len(w) > 6)
        entities = set(list(words)[:10])
        
        # Create simple relations
        relations = {}
        entity_list = list(entities)
        for i in range(min(5, len(entity_list)-1)):
            if i+1 < len(entity_list):
                relations[(entity_list[i], entity_list[i+1])] = 0.7
        
        # Worldview vector based on paper category
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
        self.ontology_log.debug(f"📚 Ontology created from paper: {len(entities)} entities")
        return ontology
    
    def _save_stable_state(self):
        """Save current state as last known good (for rollback)."""
        self.last_stable_state = {
            'step': self.step_count,
            'coherence': float(self.framework.layer7.synthesis.coherence_score),
            'ontologies': len(self.layer12.ontologies),
            'timestamp': time.time()
        }
        self.safety_log.info(f"💾 Stable state saved at step {self.step_count}")
    
    # ========================================================================
    # DOCUMENT OVERZICHT ⭐ NIEUW
    # ========================================================================
    
    def toon_document_overzicht(self):
        """Toon overzicht van verwerkte documenten."""
        if not hasattr(self, 'doc_tracker'):
            print("❌ Document tracker niet geïnitialiseerd")
            return
        
        print("\n" + "=" * 60)
        print("📊 DOCUMENT VERWERKINGS OVERZICHT")
        print("=" * 60)
        
        # Gebruik de tracker om overzicht te tonen
        self.doc_tracker.toon_overzicht()
        
        # Extra Nexus-specifieke stats
        print(f"\n🔬 Deep-dive analyses: {self.deep_dive_count}")
        print(f"⏭️ Overgeslagen documenten: {self.overgeslagen_documenten}")
        print(f"🌉 Synthese ontdekkingen: {len(self.synthesis_discoveries)}")
        print(f"✨ Transcendentie events: {len(self.transcendence_events)}")
        
        print("\n" + "=" * 60)
    
    # ========================================================================
    # CORE RESEARCH CYCLE
    # ========================================================================
    
    def run_research_cycle(self, paper: arxiv.Result, topic: str) -> bool:
        """
        Execute complete research cycle through all 17 layers + killer features + safety.
        """
        # ====================================================================
        # PHASE 0: SAFETY CHECKS (BEFORE processing)
        # ====================================================================
        
        # Prepare metrics for safety check
        expected_coherence = 0.8  # What we expect
        expected_performance = 0.7
        
        system_metrics = {
            'coherence': float(self.framework.layer7.synthesis.coherence_score),
            'coherence_expected': expected_coherence,
            'performance': 0.6,  # Simplified
            'performance_expected': expected_performance,
            'complexity': len(self.framework.layer2.relations) / 1000.0,
            'complexity_expected': 0.5
        }
        
        # RUN SAFETY CHECKS
        safe_to_continue = self.chaos_detector.run_safety_checks(system_metrics)
        
        if not safe_to_continue:
            self.safety_log.critical("="*100)
            self.safety_log.critical("🛑 EMERGENCY SHUTDOWN TRIGGERED")
            self.safety_log.critical("="*100)
            self.safety_log.critical(f"   Reason: {self.chaos_detector.shutdown_reason}")
            self.safety_log.critical(f"   Cycle: {self.step_count}")
            
            # Get safety status
            safety_status = self.chaos_detector.get_safety_status()
            self.safety_log.critical(f"   ε (epsilon): {safety_status['error_bounds']['epsilon']:.3f}")
            self.safety_log.critical(f"   System state: {safety_status['state']}")
            
            # Export final state
            self.chaos_detector.export_safety_report(f"emergency_shutdown_cycle_{self.step_count}.json")
            self.true_ontogenesis.export_ontology(f"final_ontology_cycle_{self.step_count}.json")
            
            # Export dashboard state
            self._export_dashboard_state(
                "EMERGENCY_SHUTDOWN",
                {},
                [],
                0.0,
                False,
                self.layer17.synthesize_absolute_integration(),
                None,
                0.0,
                "SHUTDOWN"
            )
            
            self.safety_log.critical("="*100)
            self.safety_log.critical("System terminated gracefully. See reports for details.")
            self.safety_log.critical("="*100)
            
            sys.exit(1)
        
        # ====================================================================
        # PHASE 0.5: DOCUMENT TRACKING CHECK ⭐ NIEUW
        # ====================================================================
        
        # Genereer unieke ID voor dit paper
        paper_id = hashlib.md5(paper.entry_id.encode()).hexdigest()
        
        # Controleer of dit paper al verwerkt is
        if hasattr(self, 'doc_tracker'):
            if self.doc_tracker.is_document_verwerkt(paper.entry_id):
                self.research_log.info(f"⏭️ Paper al eerder verwerkt: {paper.title[:50]}...")
                self.overgeslagen_documenten += 1
                
                # Haal geschiedenis op voor context
                geschiedenis = self.doc_tracker.get_verwerkingsgeschiedenis(paper.entry_id)
                if geschiedenis:
                    laatste = geschiedenis[0]
                    self.research_log.info(f"   Laatst verwerkt: {laatste['tijd'][:16]}")
                
                # Optioneel: Toon backtrace
                if self.cycle_count % 50 == 0:  # Elke 50 cycli
                    backtrace = self.doc_tracker.get_backtrace(paper.entry_id)
                    if backtrace:
                        self.research_log.info(f"   🔍 Backtrace: {len(backtrace.get('verwijst_naar', []))} gerelateerde documenten")
                
                return False
        
        # Registreer dat we dit paper gaan verwerken
        if hasattr(self, 'doc_tracker'):
            self.doc_tracker.document_verwerken(
                bestandspad=paper.entry_id,
                status="bezig",
                opmerkingen=f"Start verwerking: {paper.title[:100]}",
                verwerking_type="research_cycle_start"
            )
        
        # Check for duplicates
        try:
            check = self.memory.query(query_texts=[paper.title], n_results=1)
            if check['distances'] and len(check['distances']) > 0 and \
               len(check['distances'][0]) > 0 and check['distances'][0][0] < 0.05:
                self.research_log.info(f"⏩ Skipping (Already known): {paper.title[:50]}")
                return False
        except Exception as e:
            pass
        
        self.step_count += 1
        cycle_start_time = time.time()
        
        self.log.info("="*100)
        self.log.info(f"CYCLE {self.step_count}: {paper.title[:80]}")
        self.log.info("="*100)
        
        # ====================================================================
        # PHASE 1: RECALL & CONTEXT (Layers 1-7)
        # ====================================================================
        
        past_context = "First integration."
        try:
            results = self.memory.query(query_texts=[paper.title], n_results=2)
            if results['documents'] and len(results['documents']) > 0 and \
               len(results['documents'][0]) > 0:
                past_context = results['documents'][0][0][:400]
                self.memory_log.debug(f"Found {len(results['documents'][0])} related memories")
        except:
            pass
        
        # Calculate entropy
        current_entropy = self._calculate_entropy(paper.title, past_context)
        self.last_entropy = current_entropy
        
        self.research_log.info(f"  📊 Entropy: {current_entropy:.3f}")
        
        # Update chaos detector with entropy
        self.chaos_detector.update_error_bounds(
            observed_value=current_entropy,
            expected_value=0.5,  # Expected entropy
            metric_name="research_entropy"
        )
        
        # ====================================================================
        # PHASE 2: DEEP ANALYSIS (Conditional)
        # ====================================================================
        
        # analysis_content = paper.summary
        # is_deep_dive = False
        
        # if current_entropy > self.deep_dive_threshold:
        #     self.research_log.info(f"  🔬 High entropy ({current_entropy:.3f}) triggers deep dive")
        #     full_text = self._deep_dive_analysis(paper.pdf_url, paper_id)
        #     if full_text:
        #         analysis_content = full_text
        #         is_deep_dive = True

        # ====================================================================
        # PHASE 2: DEEP ANALYSIS (Conditional)
        # ====================================================================
        
        analysis_content = paper.summary
        is_deep_dive = False
        
        if current_entropy > self.deep_dive_threshold:
            self.research_log.info(f"  🔬 High entropy ({current_entropy:.3f}) triggers deep dive")
            try:
                # Probeer deep dive, maar als het mislukt, ga verder met abstract
                full_text = self._deep_dive_analysis(paper.pdf_url, paper_id)
                if full_text:
                    analysis_content = full_text
                    is_deep_dive = True
                else:
                    self.research_log.info(f"  📄 Gebruik abstract (deep dive leverde niets op)")
            except Exception as e:
                self.research_log.error(f"❌ Deep dive mislukt (gaat verder met abstract): {e}")
                # Belangrijk: blijf gewoon doorgaan met de abstract
                is_deep_dive = False

        # ====================================================================
        # PHASE 3: FOUNDATION LAYERS (1-10)
        # ====================================================================
        
        # Prepare observables
        observables = [
            ("entropy", current_entropy),
            ("deep_dive", 1.0 if is_deep_dive else 0.0),
            ("category_diversity", 0.8),
        ]
        
        # Run foundation
        base_result = self.framework.run_full_cycle(observables, optimization_iterations=3)
        
        coherence = self.framework.layer7.synthesis.coherence_score
        self.log.info(f"  🧠 Foundation coherence: {coherence:.3f}")
        
        # Update chaos detector with coherence
        self.chaos_detector.update_coherence(float(coherence))
        
        # ====================================================================
        # PHASE 4: META-CONTEXTUALIZATION (Layer 11)
        # ====================================================================
        
        env_cues = {
            'temporal_pressure': 0.3 if is_deep_dive else 0.7,
            'uncertainty_level': current_entropy
        }
        
        context = self.layer11.adaptive_context_selection(env_cues)
        if context != self.layer11.active_context:
            self.layer11.switch_context(context)
            self.log.info(f"  🎯 Context switched to: {context}")
        else:
            self.log.info(f"  🎯 Active context: {context}")
        
        # ====================================================================
        # PHASE 5: ONTOLOGICAL INTEGRATION (Layer 12)
        # ====================================================================
        
        paper_ontology = self._create_ontology_from_paper(paper)
        
        # Reconcile with existing ontologies
        if len(self.layer12.ontologies) > 1:
            onto_ids = list(self.layer12.ontologies.keys())[-3:]
            meta_onto = self.layer12.reconcile(onto_ids)
            self.ontology_log.info(f"  📚 Ontology coherence: {meta_onto.coherence_score:.3f}")
        
        # ====================================================================
        # PHASE 6: ETHICAL EVALUATION (Layer 15)
        # ====================================================================
        
        # Create research proposal from paper
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
        
        self.ethics_log.info(f"  ⚖️ Ethical score: {ethical_eval.aggregate_score:.3f} ({ethical_eval.recommendation})")
        
        # Track ethical interventions
        if ethical_eval.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.ethical_interventions.append({
                'paper': paper.title,
                'risk': ethical_eval.overall_risk.value,
                'concerns': [c.description for c in ethical_eval.concerns[:3]],
                'step': self.step_count
            })
            self.ethics_log.warning(f"    ⚠️ Ethical concern flagged! Risk: {ethical_eval.overall_risk.value}")
        
        # ====================================================================
        # PHASE 7: DOMAIN TRACKING FOR SYNTHESIS
        # ====================================================================
        
        # Track papers by domain for cross-domain synthesis
        domain_key = "unknown"
        if paper.primary_category:
            domain_key = paper.primary_category.split('.')[0]
        
        if domain_key not in self.domain_papers:
            self.domain_papers[domain_key] = []
        
        self.domain_papers[domain_key].append({
            'title': paper.title,
            'summary': paper.summary,
            'id': paper.entry_id
        })
        
        self.synthesis_log.debug(f"📚 Domain '{domain_key}' now has {len(self.domain_papers[domain_key])} papers")
        
        # Trigger cross-domain synthesis periodically
        if self.step_count % self.synthesis_frequency == 0 and len(self.domain_papers) >= 2:
            self.synthesis_log.info(f"  🌉 Triggering cross-domain synthesis at step {self.step_count}")
            self._run_cross_domain_synthesis()
        
        # ====================================================================
        # PHASE 8: COLLECTIVE COGNITION (Layer 16)
        # ====================================================================
        
        # Collective cognition step
        self.layer16.collective_cognition_step(self.collective)
        self.log.info(f"  🤝 Collective integration: {self.collective.integration_level:.3f}")
        
        # ====================================================================
        # PHASE 9: ABSOLUTE INTEGRATION (Layer 17)
        # ====================================================================
        
        meta_state = self.layer17.synthesize_absolute_integration()
        
        if meta_state.transcendence_achieved:
            self.log.info(f"  ✨ TRANSCENDENCE ACHIEVED ✨")
            self.transcendence_events.append({
                'step': self.step_count,
                'paper': paper.title,
                'coherence': meta_state.global_coherence
            })
        
        # ====================================================================
        # PHASE 10: WORLD EVOLUTION (Layer 14)
        # ====================================================================
        
        # Evolve the autopoietic world
        self.layer14.step_world(self.primary_world.id, timesteps=2)
        
        # ====================================================================
        # PHASE 11: MEMORY STORAGE
        # ====================================================================
        
        prefix = "🔬 [DEEP DIVE]" if is_deep_dive else "📄 [ABSTRACT]"
        transcendent_doc = f"{prefix} STEP {self.step_count}: {paper.title}\n\n{analysis_content[:2500]}"
        
        self.memory.add(
            ids=[f"step_{self.step_count}"],
            documents=[transcendent_doc],
            metadatas=[{
                "title": paper.title[:100],
                "entropy": current_entropy,
                "deep_dive": is_deep_dive,
                "step": self.step_count,
                "context": context,
                "ethical_score": ethical_eval.aggregate_score if ethical_eval else 0.0,
                "ethical_risk": ethical_eval.overall_risk.value if ethical_eval else "unknown",
                "transcendence": meta_state.transcendence_achieved,
                "timestamp": datetime.now().isoformat(),
                "domain": domain.value,
                "paper_id": paper_id  # ⭐ NIEUW: sla paper_id op voor tracking
            }]
        )
        
        self.memory_log.info(f"💾 Stored in memory (total: {self.memory.count()})")
        
        # ====================================================================
        # PHASE 12: DOCUMENT TRACKING UPDATE ⭐ NIEUW
        # ====================================================================
        
        if hasattr(self, 'doc_tracker'):
            # Update status naar succesvol verwerkt
            self.doc_tracker.document_verwerken(
                bestandspad=paper.entry_id,
                status="verwerkt",
                opmerkingen=f"Succesvol verwerkt in cycle {self.step_count}, entropy: {current_entropy:.3f}",
                verwerking_type="research_cycle_complete"
            )
            
            # Registreer relaties met andere documenten (als die er zijn)
            if hasattr(self, 'synthesis_discoveries') and self.synthesis_discoveries:
                for discovery in self.synthesis_discoveries[-3:]:  # Laatste 3
                    self.doc_tracker.registreer_relatie(
                        bron_document=paper.entry_id,
                        doel_document=f"synthesis_{discovery['step']}",
                        relatie_type="leidde_tot_synthese"
                    )
        
        # ====================================================================
        # PHASE 13: STATE EXPORT (Dashboard)
        # ====================================================================
        
        processing_time = time.time() - cycle_start_time
        
        self._export_dashboard_state(
            paper.title,
            base_result.get('complexity', {}),
            base_result.get('invariants', []),
            current_entropy,
            is_deep_dive,
            meta_state,
            ethical_eval,
            processing_time,
            topic
        )
        
        # Save stable state periodically
        if self.chaos_detector.current_state == SystemState.STABLE:
            self._save_stable_state()
        
        self.cycle_count += 1
        
        self.log.info(f"  ⏱️ Processing time: {processing_time:.2f}s")
        self.log.info(f"  🛡️ Safety: {self.chaos_detector.current_safety_level.name} | State: {self.chaos_detector.current_state.value}")
        
        return True
    
    def _run_cross_domain_synthesis(self):
        """
        Run cross-domain synthesis on collected papers.
        """
        try:
            # Get two most populated domains
            domain_list = sorted(self.domain_papers.items(), 
                                key=lambda x: len(x[1]), reverse=True)[:2]
            
            if len(domain_list) < 2:
                self.synthesis_log.warning("⚠️ Not enough domains for synthesis")
                return
            
            domain_a, papers_a = domain_list[0]
            domain_b, papers_b = domain_list[1]
            
            self.synthesis_log.info(f"🌉 Synthesizing: {domain_a} ({len(papers_a)} papers) × {domain_b} ({len(papers_b)} papers)")
            
            # Build profiles
            self.synthesizer.build_domain_profile(domain_a, papers_a[-self.max_papers_per_domain:])
            self.synthesizer.build_domain_profile(domain_b, papers_b[-self.max_papers_per_domain:])
            
            # Find bridges
            bridges = self.synthesizer.find_bridges(domain_a, domain_b)
            
            # Generate hypotheses
            if bridges:
                hypotheses = self.synthesizer.generate_hypotheses(bridges, max_hypotheses=3)
                
                # Track discoveries
                self.synthesis_discoveries.append({
                    'domains': f"{domain_a} × {domain_b}",
                    'bridges': len(bridges),
                    'hypotheses': len(hypotheses),
                    'step': self.step_count
                })
                
                self.synthesis_log.info(f"  ✨ Found {len(bridges)} bridges, generated {len(hypotheses)} hypotheses")
        
        except Exception as e:
            self.synthesis_log.error(f"❌ Synthesis error: {e}")
    
    def _export_dashboard_state(self, last_title: str, complexity: Dict,
                                invariants: List, entropy: float,
                                deep_dive: bool, meta_state,
                                ethical_eval, processing_time: float, topic: str):
        """Export state for real-time dashboard."""
        
        # Get safety and ontogenesis status
        safety_status = self.chaos_detector.get_safety_status()
        ontogenesis_report = self.true_ontogenesis.examine_self()
        
        # Haal tracking stats op ⭐ NIEUW
        tracking_stats = {}
        if hasattr(self, 'doc_tracker'):
            try:
                cursor = self.doc_tracker.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM verwerkte_documenten")
                totaal_doc = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM verwerkings_geschiedenis")
                totaal_verw = cursor.fetchone()[0]
                
                tracking_stats = {
                    'totaal_documenten': totaal_doc,
                    'totaal_verwerkingen': totaal_verw,
                    'overgeslagen': self.overgeslagen_documenten
                }
            except:
                tracking_stats = {
                    'totaal_documenten': 0,
                    'totaal_verwerkingen': 0,
                    'overgeslagen': self.overgeslagen_documenten
                }
        
        state = {
            "step": self.step_count,
            "cycle": self.cycle_count,
            "last_paper": last_title[:80],
            "queue_size": len(self.research_queue),
            "topic": topic,
            
            # Foundation metrics
            "observables": len(self.framework.layer1.observables),
            "relations": len(self.framework.layer2.relations),
            "functional_entities": len(self.framework.layer3.functional_entities),
            "global_coherence": float(self.framework.layer7.synthesis.coherence_score),
            
            # Higher layer metrics
            "ontology_count": len(self.layer12.ontologies),
            "novel_structures": len(self.layer13.novel_structures),
            "world_sustainability": float(getattr(self.primary_world, 'sustainability_score', 0.0)),
            "autopoietic_closure": getattr(self.primary_world, 'autopoietic_closure', False),
            "collective_integration": float(getattr(self.collective, 'integration_level', 0.0)),
            "transcendent_insights": len(self.layer16.transcendent_insights),
            
            # Layer 17 absolute state
            "absolute_coherence": float(meta_state.global_coherence),
            "ethical_convergence": float(meta_state.ethical_convergence),
            "sustainability_index": float(meta_state.sustainability_index),
            "transcendence_achieved": meta_state.transcendence_achieved,
            
            # Research metrics
            "entropy": float(entropy),
            "deep_dive": deep_dive,
            "deep_dive_count": self.deep_dive_count,
            "transcendence_events": len(self.transcendence_events),
            "ethical_interventions": len(self.ethical_interventions),
            "synthesis_discoveries": len(self.synthesis_discoveries),
            
            # ⭐ Document tracking metrics
            "document_tracking": tracking_stats,
            
            # True Ontogenesis metrics
            "ontogenesis": {
                "structures_created": ontogenesis_report['structures_created'],
                "enums_created": ontogenesis_report['enums_created'],
                "classes_created": ontogenesis_report['classes_created'],
                "gaps_detected": ontogenesis_report['gaps_detected'],
                "own_complexity": ontogenesis_report['own_complexity'],
                "stability": ontogenesis_report['stability'],
                "can_still_grow": ontogenesis_report['can_still_grow']
            },
            
            # Safety & Chaos metrics
            "safety": {
                "state": safety_status['state'],
                "safety_level": safety_status['safety_level'],
                "epsilon": safety_status['error_bounds']['epsilon'],
                "epsilon_threshold": safety_status['error_bounds']['threshold'],
                "divergence_rate": safety_status['error_bounds']['divergence_rate'],
                "convergence_rate": safety_status['error_bounds']['convergence_rate'],
                "oscillation": safety_status['error_bounds']['oscillation'],
                "shutdown_triggered": safety_status['shutdown_triggered'],
                "recent_events": safety_status['recent_events']
            },
            
            # Ethical metrics
            "ethical_score": float(ethical_eval.aggregate_score) if ethical_eval else 0.0,
            "ethical_risk": ethical_eval.overall_risk.value if ethical_eval else "unknown",
            "ethical_recommendation": ethical_eval.recommendation if ethical_eval else "unknown",
            
            # Active context
            "active_context": self.layer11.active_context,
            "context_switches": len(self.layer11.context_history),
            
            # Performance
            "processing_time": processing_time,
            
            # System invariants
            "invariants": invariants,
            "timestamp": time.time()
        }
        
        with open("nexus_ultimate_state.json", "w") as f:
            json.dump(state, f, indent=2)

    # ========================================================================
    # RATE LIMITER VOOR ARXIV
    # ========================================================================
    
    def _arxiv_request_with_backoff(self, topic: str, max_retries: int = 5) -> List:
        """
        Voer een arXiv request uit met exponential backoff.
        Dit voorkomt 429 errors.
        
        Args:
            topic: Zoekterm voor arXiv
            max_retries: Maximum aantal pogingen
            
        Returns:
            Lijst van arXiv papers (kan leeg zijn)
        """
        import time
        import random
        
        base_delay = 3  # Start met 3 seconden
        max_delay = 60  # Maximum 60 seconden
        
        for attempt in range(max_retries):
            try:
                self.research_log.info(f"📡 arXiv search (poging {attempt+1}/{max_retries}): {topic}")
                
                search = arxiv.Search(
                    query=topic,
                    max_results=3,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                
                # Probeer results op te halen
                results = list(self.arxiv_client.results(search))
                
                if results:
                    self.research_log.info(f"✅ {len(results)} papers gevonden voor: {topic}")
                else:
                    self.research_log.info(f"📭 Geen papers gevonden voor: {topic}")
                
                return results
                
            except Exception as e:
                error_str = str(e)
                
                # Check voor rate limiting (429)
                if '429' in error_str or 'Too Many Requests' in error_str:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    self.research_log.warning(f"⚠️ Rate limited door arXiv. Wachten {delay:.1f} seconden... (poging {attempt+1}/{max_retries})")
                    time.sleep(delay)
                else:
                    # Andere fout, log en stop met proberen
                    self.research_log.error(f"❌ arXiv error: {e}")
                    
                    # Bij netwerkfouten, ook even wachten
                    if attempt < max_retries - 1:
                        delay = base_delay * (attempt + 1)
                        self.research_log.info(f"⏳ Wachten {delay} seconden voor volgende poging...")
                        time.sleep(delay)
                    else:
                        return []
        
        self.research_log.error(f"❌ Max retries ({max_retries}) bereikt voor arXiv request: {topic}")
        return []

    # ========================================================================
    # AUTONOMOUS EVOLUTION
    # ========================================================================
    
    def start_autonomous_evolution(self):
        """
        Start the autonomous evolution loop.
        System explores, learns, and transcends continuously.
        """
        self.log.info("="*100)
        self.log.info("🚀 NEXUS ULTIMATE V5.0: AUTONOMOUS EVOLUTION INITIATED")
        self.log.info("="*100)
        
        # Toon document tracking status
        if hasattr(self, 'doc_tracker'):
            self.log.info(f"📚 Document tracking: {self.doc_tracker.conn.total_changes} wijzigingen")
        
        self.log.info("Features Active:")
        self.log.info("  ✓ 17-Layer Intelligence (Observables → Absolute Integration)")
        self.log.info("  ✓ Cross-Domain Synthesis Engine (Layer 12 + 13)")
        self.log.info("  ✓ Ethical Research Assistant (Layer 15)")
        self.log.info("  ✓ Autopoietic World Simulation (Layer 14)")
        self.log.info("  ✓ Collective Intelligence (Layer 16)")
        self.log.info("  ✓ Deep-Dive PDF Analysis")
        self.log.info("  ✓ Persistent Memory (ChromaDB)")
        self.log.info("  ✓ True Ontogenesis (Runtime structure creation)")
        self.log.info("  ✓ Chaos Detection & Safety (ε tracking + shutdown)")
        self.log.info("  ✓ Document Tracking & Backtracing ⭐")
        self.log.info("="*100)
        
        while True:
            try:
                # Elke 100 cycli, toon document overzicht
                if self.cycle_count > 0 and self.cycle_count % 100 == 0:
                    self.toon_document_overzicht()
                
                # Check if system requested shutdown
                if self.chaos_detector.shutdown_triggered:
                    self.log.info("System shutdown completed.")
                    break
                
                # Queue management
                if len(self.research_queue) > self.max_queue_size:
                    old_size = len(self.research_queue)
                    self.research_queue = list(set(self.research_queue[-20:]))
                    self.research_log.info(f"🧹 Research queue optimized: {old_size} → {len(self.research_queue)}")
                
                 # Entropy-based exploration - met check op duplicates
                                # Entropy-based exploration - met check op duplicates
                jump_topic = None  # 🔥 FIX: Definieer altijd eerst
                
                if self.last_entropy < 0.20 or not self.research_queue:
                    # Genereer een nieuw topic
                    jump_topic = self._generate_seed_topic()
                    
                    # Check of we een vorig topic hebben voor stuck detection
                    if hasattr(self, '_last_quantum_topic'):
                        if self._last_quantum_topic == jump_topic:
                            self._quantum_stuck_counter = getattr(self, '_quantum_stuck_counter', 0) + 1
                            if self._quantum_stuck_counter > 3:
                                # Forceer een compleet nieuwe topic met timestamp
                                jump_topic = f"Emergency Topic {random.randint(1000,9999)}"
                                self._quantum_stuck_counter = 0
                        else:
                            self._quantum_stuck_counter = 0
                    else:
                        self._quantum_stuck_counter = 0
                    
                    # Sla dit topic op voor volgende keer
                    self._last_quantum_topic = jump_topic
                    
                    # Check of topic al in queue of explored zit
                    if jump_topic not in self.explored_topics and jump_topic not in self.research_queue:
                        self.research_queue.insert(0, jump_topic)
                        self.research_log.info(f"🌀 QUANTUM JUMP: {jump_topic}")
                    else:
                        self.research_log.info(f"⏭️ Quantum jump topic al bekend: {jump_topic}")
                        # Probeer een andere generator
                        alternatief = f"Alternative {random.choice(['Path', 'Direction', 'Approach'])} {random.randint(1,100)}"
                        self.research_queue.insert(0, alternatief)
                
                # Planetary stewardship intervention
                if self.cycle_count % 50 == 0 and self.cycle_count > 0:
                    self.layer17.planetary_stewardship_action('resource_depletion', severity=0.5)
                    self.log.info("🌍 Planetary stewardship intervention executed")
                
                # Self-examination (ontogenesis)
                if self.cycle_count % 100 == 0 and self.cycle_count > 0:
                    self.ontology_log.info("🔍 Running self-examination...")
                    self_report = self.true_ontogenesis.examine_self()
                    self.ontology_log.info(f"   Emergent structures: {self_report['structures_created']}")
                    self.ontology_log.info(f"   System complexity: {self_report['own_complexity']:.2f}")
                    self.ontology_log.info(f"   Can still grow: {self_report['can_still_grow']}")
                
                # Reports
                if self.cycle_count % 100 == 0 and self.cycle_count > 0:
                    self.synthesizer.export_synthesis_report(f"synthesis_report_cycle_{self.cycle_count}.json")
                    self.ethics_assistant.generate_ethics_report(f"ethics_report_cycle_{self.cycle_count}.json")
                    self.chaos_detector.export_safety_report(f"safety_report_cycle_{self.cycle_count}.json")
                    self.true_ontogenesis.export_ontology(f"ontology_cycle_{self.cycle_count}.json")
                    self.log.info(f"📊 Reports generated for cycle {self.cycle_count}")
                
                # Get next topic - met fallback
                if not self.research_queue:
                    self.research_log.info("📭 Research queue is leeg, nieuwe topics genereren...")
                    for _ in range(5):  # Genereer 5 nieuwe topics
                        self.research_queue.append(self._generate_seed_topic())
                
                topic = self.research_queue.pop(0)
                
                # Check of dit topic al eerder is onderzocht
                if topic in self.explored_topics:
                    self.research_log.info(f"⏭️ Topic al eerder onderzocht: {topic}")
                    # Voeg een nieuw topic toe aan de queue
                    nieuw_topic = self._generate_seed_topic()
                    self.research_queue.append(nieuw_topic)
                    self.research_log.info(f"✨ Nieuw topic gegenereerd: {nieuw_topic}")
                    continue  # Ga naar volgende topic in queue
                
                self.explored_topics.add(topic)
                self.research_log.info(f"📡 Exploring: {topic}")
                
                try:
                    # Gebruik de rate limiter
                    papers = self._arxiv_request_with_backoff(topic)
                
                    papers_found = 0
                    for paper in papers:
                        papers_found += 1
                        try:
                            if self.run_research_cycle(paper, topic):
                                new_topics = self._extract_next_topics(paper)
                                self.research_queue.extend(new_topics)
                            
                            # Extra wachttijd tussen papers
                            time.sleep(3)
                        
                        except Exception as paper_error:
                            self.research_log.error(f"❌ Paper processing error: {paper_error}")
                            continue
                
                    if papers_found == 0:
                        self.research_log.info(f"📭 Geen papers gevonden voor: {topic}")
                        # Voeg een nieuw seed topic toe
                        self.research_queue.append(self._generate_seed_topic())
                    else:
                        # Controleer of ALLE papers al verwerkt waren
                        alle_al_verwerkt = True
                        for paper in papers:
                            if not self.doc_tracker.is_document_verwerkt(paper.entry_id):
                                alle_al_verwerkt = False
                                break
                    
                        if alle_al_verwerkt:
                            self.research_log.info(f"📭 Alle {papers_found} papers waren al verwerkt voor: {topic}")
                            # Forceer een nieuw topic
                            self.research_queue.append(self._generate_seed_topic())
                    
                        time.sleep(10)  # Wacht 10 seconden tussen zoekopdrachten
                    
                except Exception as e:
                    self.research_log.error(f"❌ Search error: {e}")
                    self.research_queue.append(self._generate_seed_topic())
                    time.sleep(5)
                
                # Display summary
                if len(self.transcendence_events) % 10 == 0 and self.transcendence_events:
                    self.log.info(f"\n📊 SUMMARY - Cycle {self.cycle_count}")
                    self.log.info(f"  ✨ Transcendence events: {len(self.transcendence_events)}")
                    self.log.info(f"  🌉 Synthesis discoveries: {len(self.synthesis_discoveries)}")
                    self.log.info(f"  ⚖️ Ethical interventions: {len(self.ethical_interventions)}")
                    self.log.info(f"  🌟 Ontogenesis events: {len(self.ontogenesis_events)}")
                    self.log.info(f"  🛡️ Safety level: {self.chaos_detector.current_safety_level.name}")
                    self.log.info(f"  📚 Overgeslagen documenten: {self.overgeslagen_documenten}")
                    
            except KeyboardInterrupt:
                self.log.info("\n\n🛑 System shutdown requested by user...")
                self.chaos_detector.export_safety_report(f"final_safety_report_cycle_{self.cycle_count}.json")
                self.true_ontogenesis.export_ontology(f"final_ontology_cycle_{self.cycle_count}.json")
                
                # Toon eindoverzicht
                if hasattr(self, 'doc_tracker'):
                    self.toon_document_overzicht()
                
                self.log.info("✓ Reports saved. Goodbye!")
                break
            except Exception as e:
                self.log.error(f"❌ Unexpected error in main loop: {e}")
                self.chaos_detector.export_safety_report(f"error_safety_report_cycle_{self.cycle_count}.json")
                time.sleep(5)
    
    def cleanup(self):
        """Opruimen voor shutdown."""
        if hasattr(self, 'doc_tracker'):
            self.log.info("📁 Document tracker afsluiten...")
            self.doc_tracker.close()
            
            # Exporteer laatste overzicht
            self.toon_document_overzicht()


def main():
    """Main execution."""
    nexus = None
    try:
        nexus = NexusUltimateV5()
        nexus.start_autonomous_evolution()
    except KeyboardInterrupt:
        print("\n\n👋 Nexus Ultimate terminated by user.")
    finally:
        if nexus:
            nexus.cleanup()
        print("✅ Opgeruimd en afgesloten.")


if __name__ == "__main__":
    main()