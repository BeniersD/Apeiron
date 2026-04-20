"""
ONTOLOGICAL DIPLOMACY - Onderhandeling tussen verschillende ontologieën
================================================================================
Laat twee Nexus-systemen met verschillende wereldbeelden onderhandelen en
consensus bereiken zonder centrale autoriteit. Dit is de ultieme test voor
Laag 17 (Absolute Integratie) in een multi-agent context.

Theoretische basis:
- Intersubjectieve waarheidsvinding
- Consensus zonder centrale autoriteit
- Kwantum-overlap voor voorstel-vergelijking
- Evolutionaire speltheorie voor onderhandelingsstrategieën

V13 OPTIONELE UITBREIDINGEN:
- Meerdere onderhandelingsstrategieën (coöperatief, competitief, wederkerig)
- Vertrouwensmechanismen tussen agents
- Onderhandelingsgeschiedenis met leercurves
- Quantum-versterkte voorstel-evaluatie
- Externe mediators bij vastgelopen onderhandelingen
- Stemmechanismen voor multi-party consensus
- Reputatie-systeem voor agents
"""

import numpy as np
import asyncio
import logging
import time
import hashlib
import json
import random
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
from datetime import datetime
import math

logger = logging.getLogger(__name__)

# ====================================================================
# OPTIONELE IMPORTS
# ====================================================================

# Voor quantum-versterkte voorstel-evaluatie
try:
    from qiskit import QuantumCircuit, QuantumRegister, execute, Aer
    from qiskit.providers.aer import QasmSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

# Voor complexe netwerkanalyse
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

# Voor machine learning strategieën
try:
    import sklearn
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Voor visualisatie
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

# Voor blockchain-achtig consensus
try:
    import hashlib
    import json
    # Voor echte blockchain: web3.py, mengevm, etc.
    BLOCKCHAIN_AVAILABLE = False  # Optioneel voor echte implementatie
except ImportError:
    BLOCKCHAIN_AVAILABLE = False


class NegotiationStrategy(Enum):
    """Strategie voor onderhandelingen."""
    COOPERATIVE = "cooperative"       # Streef naar win-win
    COMPETITIVE = "competitive"       # Streef naar eigen voordeel
    RECIPROCAL = "reciprocal"         # Oog om oog, tand om tand
    EXPLORATORY = "exploratory"       # Verken mogelijkheden zonder commitment
    PRINCIPLED = "principled"          # Vasthouden aan kernprincipes
    ADAPTIVE = "adaptive"              # Pas strategie aan op basis van tegenstander


class TrustLevel(Enum):
    """Vertrouwensniveau tussen agents."""
    NONE = 0          # Geen vertrouwen
    LOW = 1           # Weinig vertrouwen
    MEDIUM = 2        # Gemiddeld vertrouwen
    HIGH = 3          # Hoog vertrouwen
    ABSOLUTE = 4      # Volledig vertrouwen


class ProposalStatus(Enum):
    """Status van een voorstel."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    COUNTERED = "countered"
    EXPIRED = "expired"


@dataclass
class DiplomaticProposal:
    """Een voorstel tijdens onderhandelingen."""
    id: str
    proposer: str           # Agent ID
    target: str             # Doel-agent (of "all" voor broadcast)
    ontology_snapshot: Dict[str, Any]
    concessions: List[str]   # Wat biedt de proposer aan
    demands: List[str]       # Wat vraagt de proposer
    timestamp: float
    expires_at: float
    status: ProposalStatus
    iterations: int = 0
    parent_proposal: Optional[str] = None  # Voor tegenvoorstellen
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary."""
        return {
            'id': self.id,
            'proposer': self.proposer,
            'target': self.target,
            'concessions': self.concessions,
            'demands': self.demands,
            'timestamp': self.timestamp,
            'expires_at': self.expires_at,
            'status': self.status.value,
            'iterations': self.iterations
        }


@dataclass
class DiplomaticSession:
    """Een onderhandelingssessie tussen agents."""
    id: str
    agents: List[str]
    start_time: float
    last_update: float
    status: str  # active, paused, concluded, failed
    strategy: NegotiationStrategy
    proposals: List[DiplomaticProposal] = field(default_factory=list)
    agreements: List[Dict[str, Any]] = field(default_factory=list)
    log: List[Dict[str, Any]] = field(default_factory=list)
    round: int = 0
    timeout: float = 3600.0  # 1 uur default
    
    def add_log(self, event: str, details: Dict[str, Any] = None):
        """Voeg entry toe aan onderhandelingslog."""
        self.log.append({
            'timestamp': time.time(),
            'round': self.round,
            'event': event,
            'details': details or {}
        })


@dataclass
class AgentProfile:
    """Profiel van een onderhandelende agent."""
    id: str
    name: str
    version: str
    capabilities: List[str]
    core_principles: List[str]      # Niet-onderhandelbaar
    flexibility: float               # 0-1, hoe flexibel is de agent
    trust_scores: Dict[str, float]   # Vertrouwen in andere agents
    reputation: float                # Globale reputatie (0-1)
    negotiation_count: int = 0
    success_count: int = 0
    last_active: float = field(default_factory=time.time)


class OntologicalDiplomat:
    """
    Onderhandelt tussen twee of meer Nexus-systemen met verschillende ontologieën.
    Geen centrale autoriteit - pure consensus via iteratieve reconciliatie.
    
    Core functionaliteit:
    - Bilaterale onderhandelingen
    - Voorstel-generatie en -evaluatie
    - Consensus-zoeken zonder centrale autoriteit
    - Onderhandelingsgeschiedenis
    
    Optionele uitbreidingen:
    - Meerdere onderhandelingsstrategieën
    - Vertrouwensmechanismen
    - Quantum-versterkte voorstel-evaluatie
    - Externe mediators
    - Stemmechanismen voor multi-party consensus
    - Reputatie-systeem
    - Blockchain-achtige consensus
    """
    
    def __init__(self,
                 nexus_a=None,
                 nexus_b=None,
                 strategy: NegotiationStrategy = NegotiationStrategy.ADAPTIVE,
                 max_rounds: int = 100,
                 proposal_timeout: float = 300.0,  # 5 minuten
                 min_overlap_threshold: float = 0.7,
                 use_quantum_evaluation: bool = True,
                 use_trust_scores: bool = True,
                 use_reputation: bool = True,
                 enable_mediation: bool = False,
                 enable_voting: bool = False,
                 enable_blockchain: bool = False,
                 log_level: str = "INFO",
                 visualization: bool = False,
                 config_path: Optional[str] = None):
        """
        Initialiseer ontologische diplomaat.
        
        Args:
            nexus_a: Eerste Nexus systeem
            nexus_b: Tweede Nexus systeem
            strategy: Onderhandelingsstrategie
            max_rounds: Maximum aantal onderhandelingsrondes
            proposal_timeout: Timeout voor voorstellen
            min_overlap_threshold: Minimum quantum overlap voor acceptatie
            use_quantum_evaluation: Gebruik quantum voor voorstel-evaluatie
            use_trust_scores: Gebruik vertrouwensscores
            use_reputation: Gebruik reputatie-systeem
            enable_mediation: Schakel externe mediators in
            enable_voting: Schakel stemmechanisme in voor multi-party
            enable_blockchain: Gebruik blockchain-achtige consensus
            log_level: Log niveau
            visualization: Genereer visualisaties
            config_path: Pad naar configuratie bestand
        """
        self.nexus_a = nexus_a
        self.nexus_b = nexus_b
        self.strategy = strategy
        self.max_rounds = max_rounds
        self.proposal_timeout = proposal_timeout
        self.min_overlap_threshold = min_overlap_threshold
        self.use_quantum_evaluation = use_quantum_evaluation and QISKIT_AVAILABLE
        self.use_trust_scores = use_trust_scores
        self.use_reputation = use_reputation
        self.enable_mediation = enable_mediation
        self.enable_voting = enable_voting
        self.enable_blockchain = enable_blockchain
        self.visualization = visualization and VISUALIZATION_AVAILABLE
        
        # Agent profiles
        self.agents: Dict[str, AgentProfile] = {}
        if nexus_a:
            self._register_agent(nexus_a, "Nexus_A")
        if nexus_b:
            self._register_agent(nexus_b, "Nexus_B")
        
        # Actieve sessies
        self.sessions: Dict[str, DiplomaticSession] = {}
        self.completed_sessions: List[DiplomaticSession] = []
        
        # Vertrouwensnetwerk (voor multi-agent)
        self.trust_network: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Mediators (voor als onderhandelingen vastlopen)
        self.mediators: List[str] = []
        
        # Reputatie-scores
        self.reputation_scores: Dict[str, float] = {}
        
        # Stemgeschiedenis (voor multi-party)
        self.vote_history: Dict[str, List[Dict]] = defaultdict(list)
        
        # Statistieken
        self.stats = {
            'sessions_initiated': 0,
            'sessions_completed': 0,
            'sessions_failed': 0,
            'proposals_made': 0,
            'proposals_accepted': 0,
            'proposals_rejected': 0,
            'quantum_evaluations': 0,
            'mediations_used': 0,
            'votes_cast': 0,
            'start_time': time.time()
        }
        
        # Laad configuratie
        if config_path:
            self._load_config(config_path)
        
        logger.info("="*80)
        logger.info("🤝 ONTOLOGICAL DIPLOMACY V13 GEÏNITIALISEERD")
        logger.info("="*80)
        logger.info(f"Strategie: {strategy.value}")
        logger.info(f"Max rondes: {max_rounds}")
        logger.info(f"Overlap threshold: {min_overlap_threshold}")
        logger.info(f"Quantum evaluatie: {'✅' if self.use_quantum_evaluation else '❌'}")
        logger.info(f"Vertrouwensscores: {'✅' if use_trust_scores else '❌'}")
        logger.info(f"Reputatie: {'✅' if use_reputation else '❌'}")
        logger.info(f"Mediation: {'✅' if enable_mediation else '❌'}")
        logger.info(f"Voting: {'✅' if enable_voting else '❌'}")
        logger.info(f"Blockchain: {'✅' if enable_blockchain else '❌'}")
        logger.info("="*80)
    
    def _register_agent(self, nexus, name: str):
        """Registreer een agent in het systeem."""
        agent_id = f"agent_{len(self.agents)}_{int(time.time())}"
        
        # Bepaal capabilities op basis van beschikbare modules
        capabilities = []
        if hasattr(nexus, 'layer12'):
            capabilities.append('reconciliation')
        if hasattr(nexus, 'layer13'):
            capabilities.append('ontogenesis')
        if hasattr(nexus, 'resonance_scout'):
            capabilities.append('resonance')
        
        profile = AgentProfile(
            id=agent_id,
            name=name,
            version=getattr(nexus, 'version', 'unknown'),
            capabilities=capabilities,
            core_principles=self._extract_core_principles(nexus),
            flexibility=0.7,  # Default
            trust_scores={},
            reputation=0.5    # Start neutraal
        )
        
        self.agents[agent_id] = profile
        
        # Als er al een andere agent is, initialiseer vertrouwen
        for other_id in self.agents:
            if other_id != agent_id:
                self.trust_network[agent_id][other_id] = 0.5
                self.trust_network[other_id][agent_id] = 0.5
        
        logger.info(f"✅ Agent geregistreerd: {name} ({agent_id[:8]})")
        return agent_id
    
    def _extract_core_principles(self, nexus) -> List[str]:
        """Extraheer kernprincipes uit een Nexus systeem."""
        principles = []
        
        # Haal uit Layer 15 (Ethical Convergence) indien beschikbaar
        if hasattr(nexus, 'layer15') and hasattr(nexus.layer15, 'ethical_principles'):
            for p in nexus.layer15.ethical_principles.values():
                if hasattr(p, 'weight') and p.weight > 0.9:
                    principles.append(p.id)
        
        # Fallback
        if not principles:
            principles = ['autonomy', 'sustainability', 'fairness']
        
        return principles
    
    # ====================================================================
    # KERN FUNCTIONALITEIT - ONDERHANDELINGEN
    # ====================================================================
    
    async def negotiate(self,
                       agent_a_id: str,
                       agent_b_id: str,
                       initial_issues: Optional[List[str]] = None,
                       session_id: Optional[str] = None) -> Optional[DiplomaticSession]:
        """
        Voer onderhandelingen uit tussen twee agents.
        
        Args:
            agent_a_id: ID van eerste agent
            agent_b_id: ID van tweede agent
            initial_issues: Optionele lijst van issues om te bespreken
            session_id: Optionele sessie ID (anders automatisch)
        
        Returns:
            DiplomaticSession met resultaat of None bij falen
        """
        # Valideer agents
        if agent_a_id not in self.agents or agent_b_id not in self.agents:
            logger.error(f"❌ Agent niet gevonden: {agent_a_id} of {agent_b_id}")
            return None
        
        # Maak sessie
        if session_id is None:
            session_id = f"session_{len(self.sessions)}_{int(time.time())}"
        
        session = DiplomaticSession(
            id=session_id,
            agents=[agent_a_id, agent_b_id],
            start_time=time.time(),
            last_update=time.time(),
            status="active",
            strategy=self.strategy,
            timeout=3600.0
        )
        
        self.sessions[session_id] = session
        self.stats['sessions_initiated'] += 1
        
        logger.info(f"\n🤝 Nieuwe onderhandelingssessie: {session_id}")
        logger.info(f"   Tussen: {self.agents[agent_a_id].name} ↔ {self.agents[agent_b_id].name}")
        
        # Haal ontologieën op
        ontology_a = await self._get_agent_ontology(agent_a_id)
        ontology_b = await self._get_agent_ontology(agent_b_id)
        
        # Vind gemeenschappelijke grond
        common_ground = await self._find_common_ground(ontology_a, ontology_b)
        session.add_log("common_ground_found", {'count': len(common_ground)})
        
        # Identificeer frictiepunten
        friction_points = await self._find_friction_points(
            ontology_a, ontology_b, initial_issues
        )
        session.add_log("friction_points_identified", {'count': len(friction_points)})
        
        logger.info(f"   Gemeenschappelijke grond: {len(common_ground)} items")
        logger.info(f"   Frictiepunten: {len(friction_points)}")
        
        # Onderhandelingsronde
        for round_num in range(self.max_rounds):
            session.round = round_num
            session.last_update = time.time()
            
            logger.info(f"\n📋 Ronde {round_num + 1}/{self.max_rounds}")
            
            # Check timeout
            if time.time() - session.start_time > session.timeout:
                session.status = "failed"
                session.add_log("timeout", {'round': round_num})
                logger.warning(f"⏱️ Timeout na {session.timeout}s")
                break
            
            # Genereer voorstellen
            proposal_a = await self._generate_proposal(
                agent_a_id, agent_b_id, ontology_a, ontology_b,
                friction_points, round_num, session.strategy
            )
            
            proposal_b = await self._generate_proposal(
                agent_b_id, agent_a_id, ontology_b, ontology_a,
                friction_points, round_num, session.strategy
            )
            
            if proposal_a:
                session.proposals.append(proposal_a)
                self.stats['proposals_made'] += 1
            if proposal_b:
                session.proposals.append(proposal_b)
                self.stats['proposals_made'] += 1
            
            # Evalueer voorstellen
            if proposal_a and proposal_b:
                eval_result = await self._evaluate_proposals(
                    proposal_a, proposal_b, session
                )
                
                if eval_result['consensus']:
                    # Consensus bereikt!
                    agreement = {
                        'session_id': session_id,
                        'round': round_num,
                        'timestamp': time.time(),
                        'terms': eval_result['agreement_terms'],
                        'proposals': [proposal_a.id, proposal_b.id]
                    }
                    session.agreements.append(agreement)
                    session.status = "concluded"
                    session.add_log("consensus_reached", agreement)
                    
                    self.stats['sessions_completed'] += 1
                    self.stats['proposals_accepted'] += 2
                    
                    # Update reputaties
                    if self.use_reputation:
                        await self._update_reputation(agent_a_id, agent_b_id, True)
                    
                    logger.info(f"\n🎉 CONSENSUS BEREIKT in ronde {round_num + 1}!")
                    
                    # Exporteer verdrag
                    await self._create_treaty(session, agreement)
                    
                    return session
                
                elif eval_result['deadlock']:
                    # Vastgelopen - mediator nodig
                    if self.enable_mediation:
                        await self._mediate(session, eval_result)
                    else:
                        logger.warning("⚠️ Vastgelopen, maar geen mediator beschikbaar")
                        session.status = "failed"
                        self.stats['sessions_failed'] += 1
                        break
            
            # Update trust scores
            if self.use_trust_scores:
                await self._update_trust_scores(session, proposal_a, proposal_b)
            
            # Update strategie indien adaptief
            if self.strategy == NegotiationStrategy.ADAPTIVE:
                session.strategy = await self._adapt_strategy(session)
            
            await asyncio.sleep(0.5)  # Voorkom busy waiting
        
        if session.status == "active":
            session.status = "failed"
            self.stats['sessions_failed'] += 1
            logger.warning(f"❌ Geen consensus na {self.max_rounds} rondes")
        
        # Verplaats naar completed
        self.completed_sessions.append(session)
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        return session if session.status == "concluded" else None
    
    async def _get_agent_ontology(self, agent_id: str) -> Dict[str, Any]:
        """Haal de huidige ontologie van een agent op."""
        agent = self.agents[agent_id]
        
        # Als we toegang hebben tot de echte Nexus
        nexus = getattr(self, f"nexus_{agent.name.split('_')[-1].lower()}", None)
        
        if nexus and hasattr(nexus, 'layer12') and hasattr(nexus.layer12, 'meta_ontology'):
            meta = nexus.layer12.meta_ontology
            if meta:
                return {
                    'entities': list(meta.entities),
                    'relations': meta.relations,
                    'axioms': meta.axioms,
                    'worldview': meta.worldview_vector.tolist() if hasattr(meta, 'worldview_vector') else []
                }
        
        # Fallback: simuleer een ontologie
        return self._simulate_ontology(agent)
    
    def _simulate_ontology(self, agent: AgentProfile) -> Dict[str, Any]:
        """Simuleer een ontologie voor een agent (voor demo)."""
        base_concepts = ['concept_A', 'concept_B', 'concept_C', 'concept_D', 'concept_E']
        
        # Voeg agent-specifieke concepten toe
        if 'ontogenesis' in agent.capabilities:
            extra = [f'evolved_{i}' for i in range(3)]
        else:
            extra = []
        
        entities = base_concepts[:4] + extra
        
        # Simuleer relaties
        relations = {}
        for i, e1 in enumerate(entities):
            for e2 in entities[i+1:]:
                if random.random() > 0.6:
                    relations[(e1, e2)] = random.uniform(0.3, 0.9)
        
        return {
            'entities': entities,
            'relations': relations,
            'axioms': agent.core_principles
        }
    
    async def _find_common_ground(self, ont_a: Dict, ont_b: Dict) -> List[str]:
        """Vind gemeenschappelijke concepten tussen ontologieën."""
        entities_a = set(ont_a.get('entities', []))
        entities_b = set(ont_b.get('entities', []))
        
        common = list(entities_a.intersection(entities_b))
        
        # Voeg semantisch vergelijkbare concepten toe (optioneel)
        if self.use_quantum_evaluation and QISKIT_AVAILABLE:
            for ea in entities_a:
                for eb in entities_b:
                    if ea != eb and (ea, eb) not in common:
                        overlap = await self._quantum_concept_overlap(ea, eb)
                        if overlap > 0.8:
                            common.append(f"{ea}≈{eb}")
        
        return common
    
    async def _find_friction_points(self, ont_a: Dict, ont_b: Dict,
                                   initial_issues: Optional[List[str]] = None) -> List[Dict]:
        """Identificeer frictiepunten tussen ontologieën."""
        friction = []
        
        # Conflicterende relaties
        relations_a = ont_a.get('relations', {})
        relations_b = ont_b.get('relations', {})
        
        for (e1, e2), strength_a in relations_a.items():
            if (e1, e2) in relations_b:
                strength_b = relations_b[(e1, e2)]
                if abs(strength_a - strength_b) > 0.3:
                    friction.append({
                        'type': 'relation_strength',
                        'entities': [e1, e2],
                        'value_a': strength_a,
                        'value_b': strength_b,
                        'description': f"Conflicterende relatiesterkte tussen {e1} en {e2}"
                    })
        
        # Unieke concepten (kunnen frictie geven)
        entities_a = set(ont_a.get('entities', []))
        entities_b = set(ont_b.get('entities', []))
        
        unique_a = entities_a - entities_b
        unique_b = entities_b - entities_a
        
        for e in list(unique_a)[:3]:  # Max 3
            friction.append({
                'type': 'unique_concept',
                'entity': e,
                'owner': 'A',
                'description': f"Uniek concept in A: {e}"
            })
        
        for e in list(unique_b)[:3]:
            friction.append({
                'type': 'unique_concept',
                'entity': e,
                'owner': 'B',
                'description': f"Uniek concept in B: {e}"
            })
        
        # Conflicterende axioma's
        axioms_a = set(ont_a.get('axioms', []))
        axioms_b = set(ont_b.get('axioms', []))
        
        for ax in axioms_a.intersection(axioms_b):
            # Zelfde axioma is goed
            pass
        
        for ax in axioms_a.symmetric_difference(axioms_b):
            friction.append({
                'type': 'axiom',
                'axiom': ax,
                'description': f"Verschillend axioma: {ax}"
            })
        
        # Voeg initiële issues toe
        if initial_issues:
            for issue in initial_issues:
                friction.append({
                    'type': 'explicit',
                    'description': issue
                })
        
        return friction
    
    async def _generate_proposal(self,
                                 proposer_id: str,
                                 target_id: str,
                                 own_ontology: Dict,
                                 other_ontology: Dict,
                                 friction_points: List[Dict],
                                 round_num: int,
                                 strategy: NegotiationStrategy) -> Optional[DiplomaticProposal]:
        """Genereer een voorstel op basis van strategie."""
        
        # Bepaal concessies en eisen op basis van strategie
        concessions = []
        demands = []
        
        if strategy == NegotiationStrategy.COOPERATIVE:
            # Doe genereuze concessies
            for f in friction_points[:2]:
                if f['type'] == 'unique_concept' and f.get('owner') == proposer_id[-1]:
                    concessions.append(f"Accept {f['entity']} in unified ontology")
                elif f['type'] == 'relation_strength':
                    # Bied compromis aan
                    avg = (f['value_a'] + f['value_b']) / 2
                    concessions.append(f"Set {f['entities']} strength to {avg:.2f}")
        
        elif strategy == NegotiationStrategy.COMPETITIVE:
            # Eis veel, bied weinig
            for f in friction_points[:1]:
                if f['type'] == 'unique_concept' and f.get('owner') != proposer_id[-1]:
                    demands.append(f"Drop {f['entity']}")
            
            # Bied minimale concessies
            if len(friction_points) > 3:
                concessions.append("Accept 1 minor concept")
        
        elif strategy == NegotiationStrategy.RECIPROCAL:
            # Tit-for-tat: gebaseerd op vorige ronde
            if round_num == 0:
                concessions = ["Open for discussion"]
                demands = ["Mutual respect"]
            else:
                # In echte implementatie: analyseer vorige voorstellen
                concessions = ["Reciprocal concession"]
                demands = ["Reciprocal demand"]
        
        else:  # EXPLORATORY, PRINCIPLED, ADAPTIVE
            # Verkennend: stel vragen, geen harde eisen
            concessions = ["Explore possibilities"]
            demands = ["Share more about your worldview"]
        
        # Als er geen concessies of eisen zijn, maak een generiek voorstel
        if not concessions and not demands:
            concessions = ["Continue dialogue"]
            demands = ["Seek mutual understanding"]
        
        # Maak voorstel
        proposal_id = f"prop_{len(self.sessions)}_{round_num}_{int(time.time())}"
        
        proposal = DiplomaticProposal(
            id=proposal_id,
            proposer=proposer_id,
            target=target_id,
            ontology_snapshot=own_ontology.copy(),
            concessions=concessions,
            demands=demands,
            timestamp=time.time(),
            expires_at=time.time() + self.proposal_timeout,
            status=ProposalStatus.PENDING,
            iterations=round_num
        )
        
        # Log
        logger.debug(f"   📝 {self.agents[proposer_id].name} stelt voor: {concessions}")
        
        return proposal
    
    async def _evaluate_proposals(self,
                                  prop_a: DiplomaticProposal,
                                  prop_b: DiplomaticProposal,
                                  session: DiplomaticSession) -> Dict[str, Any]:
        """Evalueer twee voorstellen en bepaal of er consensus is."""
        
        # Bereken overlap tussen voorstellen
        overlap = await self._calculate_proposal_overlap(prop_a, prop_b)
        
        # Check of overlap voldoende is
        consensus = overlap >= self.min_overlap_threshold
        
        # Check op deadlock (geen vooruitgang)
        deadlock = False
        if session.round > 5:
            # Analyseer laatste 3 rondes
            recent = session.proposals[-6:] if len(session.proposals) >= 6 else session.proposals
            if len(recent) >= 4:
                # Check of voorstellen steeds hetzelfde zijn
                unique_proposals = len(set(p.id for p in recent))
                if unique_proposals < 3:
                    deadlock = True
        
        result = {
            'consensus': consensus,
            'deadlock': deadlock,
            'overlap': overlap,
            'agreement_terms': self._extract_agreement_terms(prop_a, prop_b) if consensus else None
        }
        
        # Update voorstelstatussen
        if consensus:
            prop_a.status = ProposalStatus.ACCEPTED
            prop_b.status = ProposalStatus.ACCEPTED
        else:
            prop_a.status = ProposalStatus.REJECTED
            prop_b.status = ProposalStatus.REJECTED
            self.stats['proposals_rejected'] += 2
        
        session.add_log("proposals_evaluated", {
            'overlap': overlap,
            'consensus': consensus,
            'deadlock': deadlock
        })
        
        logger.debug(f"   📊 Overlap: {overlap:.3f} (threshold: {self.min_overlap_threshold})")
        
        return result
    
    async def _calculate_proposal_overlap(self, prop_a: DiplomaticProposal,
                                         prop_b: DiplomaticProposal) -> float:
        """
        Bereken overlap tussen twee voorstellen.
        Gebruik quantum indien beschikbaar, anders klassieke vergelijking.
        """
        if self.use_quantum_evaluation and QISKIT_AVAILABLE:
            return await self._quantum_proposal_overlap(prop_a, prop_b)
        else:
            return self._classical_proposal_overlap(prop_a, prop_b)
    
    async def _quantum_proposal_overlap(self, prop_a: DiplomaticProposal,
                                       prop_b: DiplomaticProposal) -> float:
        """Bereken overlap via quantum SWAP-test."""
        self.stats['quantum_evaluations'] += 1
        
        try:
            # Converteer voorstellen naar quantum circuits
            n_qubits = 4  # Simpele representatie
            
            qr = QuantumRegister(n_qubits, 'q')
            circuit_a = QuantumCircuit(qr)
            circuit_b = QuantumCircuit(qr)
            
            # Encodeer concessies in quantum toestand
            for i, concession in enumerate(prop_a.concessions[:n_qubits]):
                if concession:
                    circuit_a.h(i)  # Superpositie
            
            for i, concession in enumerate(prop_b.concessions[:n_qubits]):
                if concession:
                    circuit_b.h(i)
            
            # SWAP test
            total_qubits = n_qubits * 2 + 1
            qr_total = QuantumRegister(total_qubits, 'q')
            test = QuantumCircuit(qr_total)
            
            test.append(circuit_a, range(1, n_qubits + 1))
            test.append(circuit_b, range(n_qubits + 1, total_qubits))
            
            test.h(0)
            for i in range(n_qubits):
                test.cswap(0, i+1, i+1+n_qubits)
            test.h(0)
            test.measure_all()
            
            # Simuleer
            simulator = Aer.get_backend('qasm_simulator')
            job = execute(test, simulator, shots=1000)
            result = job.result()
            counts = result.get_counts()
            
            # Bereken overlap
            shots = sum(counts.values())
            p0 = sum(count for bitstring, count in counts.items() if bitstring[-1] == '0') / shots
            overlap = max(0.0, min(1.0, 2 * p0 - 1))
            
            return overlap
            
        except Exception as e:
            logger.error(f"Quantum overlap fout: {e}, gebruik klassieke fallback")
            return self._classical_proposal_overlap(prop_a, prop_b)
    
    def _classical_proposal_overlap(self, prop_a: DiplomaticProposal,
                                   prop_b: DiplomaticProposal) -> float:
        """Klassieke overlap-berekening."""
        # Jaccard similariteit op concessies
        set_a = set(prop_a.concessions)
        set_b = set(prop_b.concessions)
        
        if not set_a and not set_b:
            return 0.5
        
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        
        jaccard = intersection / union if union > 0 else 0
        
        # Demands ook meewegen
        demands_a = set(prop_a.demands)
        demands_b = set(prop_b.demands)
        
        demands_intersection = len(demands_a.intersection(demands_b))
        demands_union = len(demands_a.union(demands_b))
        demands_jaccard = demands_intersection / demands_union if demands_union > 0 else 0
        
        # Gewogen gemiddelde
        overlap = 0.6 * jaccard + 0.4 * demands_jaccard
        
        return overlap
    
    def _extract_agreement_terms(self, prop_a: DiplomaticProposal,
                                 prop_b: DiplomaticProposal) -> List[str]:
        """Extraheer overeengekomen termen uit twee voorstellen."""
        terms = []
        
        # Gemeenschappelijke concessies
        common_concessions = set(prop_a.concessions).intersection(set(prop_b.concessions))
        terms.extend([f"Agreed: {c}" for c in common_concessions])
        
        # Gemeenschappelijke eisen (als beide hetzelfde eisen)
        common_demands = set(prop_a.demands).intersection(set(prop_b.demands))
        terms.extend([f"Both demand: {d}" for d in common_demands])
        
        # Compromissen
        for ca in prop_a.concessions:
            for db in prop_b.demands:
                if "accept" in ca.lower() and "drop" in db.lower():
                    terms.append(f"Compromise: {ca} in exchange for {db}")
        
        return terms
    
    # ====================================================================
    # OPTIONEEL: TRUST & REPUTATIE
    # ====================================================================
    
    async def _update_trust_scores(self, session: DiplomaticSession,
                                   prop_a: Optional[DiplomaticProposal],
                                   prop_b: Optional[DiplomaticProposal]):
        """Update vertrouwensscores op basis van onderhandelingen."""
        if not self.use_trust_scores:
            return
        
        agent_a, agent_b = session.agents
        
        # Basis: hoe meer voorstellen, hoe meer vertrouwen
        trust_increment = 0.01
        
        # Extra voor constructieve voorstellen
        if prop_a and len(prop_a.concessions) > 1:
            trust_increment += 0.02
        
        if prop_b and len(prop_b.concessions) > 1:
            trust_increment += 0.02
        
        # Update trust network
        self.trust_network[agent_a][agent_b] = min(
            1.0,
            self.trust_network[agent_a].get(agent_b, 0.5) + trust_increment
        )
        
        self.trust_network[agent_b][agent_a] = min(
            1.0,
            self.trust_network[agent_b].get(agent_a, 0.5) + trust_increment
        )
        
        # Update agent trust scores
        if agent_a in self.agents:
            self.agents[agent_a].trust_scores[agent_b] = self.trust_network[agent_a][agent_b]
        if agent_b in self.agents:
            self.agents[agent_b].trust_scores[agent_a] = self.trust_network[agent_b][agent_a]
    
    async def _update_reputation(self, agent_a_id: str, agent_b_id: str, success: bool):
        """Update reputatie na succesvolle/falende onderhandeling."""
        if not self.use_reputation:
            return
        
        for agent_id in [agent_a_id, agent_b_id]:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.negotiation_count += 1
                if success:
                    agent.success_count += 1
                
                # Bereken nieuwe reputatie
                if agent.negotiation_count > 0:
                    agent.reputation = agent.success_count / agent.negotiation_count
                
                # Update globale reputatie
                self.reputation_scores[agent_id] = agent.reputation
    
    def get_trust_level(self, agent_a_id: str, agent_b_id: str) -> TrustLevel:
        """Haal vertrouwensniveau op tussen twee agents."""
        trust = self.trust_network.get(agent_a_id, {}).get(agent_b_id, 0.5)
        
        if trust < 0.2:
            return TrustLevel.NONE
        elif trust < 0.4:
            return TrustLevel.LOW
        elif trust < 0.6:
            return TrustLevel.MEDIUM
        elif trust < 0.8:
            return TrustLevel.HIGH
        else:
            return TrustLevel.ABSOLUTE
    
    # ====================================================================
    # OPTIONEEL: ADAPTIEVE STRATEGIE
    # ====================================================================
    
    async def _adapt_strategy(self, session: DiplomaticSession) -> NegotiationStrategy:
        """Pas strategie aan op basis van onderhandelingsgeschiedenis."""
        if len(session.proposals) < 4:
            return session.strategy
        
        # Analyseer succes van vorige rondes
        accepted = sum(1 for p in session.proposals[-4:] 
                      if p.status == ProposalStatus.ACCEPTED)
        
        if accepted >= 2:
            # Het gaat goed, blijf coöperatief
            return NegotiationStrategy.COOPERATIVE
        elif accepted == 0:
            # Het gaat slecht, word competitief
            return NegotiationStrategy.COMPETITIVE
        else:
            # Neutraal, blijf verkennend
            return NegotiationStrategy.EXPLORATORY
    
    # ====================================================================
    # OPTIONEEL: MEDIATION
    # ====================================================================
    
    async def _mediate(self, session: DiplomaticSession, eval_result: Dict):
        """Schakel mediator in bij vastgelopen onderhandelingen."""
        if not self.enable_mediation:
            return
        
        self.stats['mediations_used'] += 1
        
        # Vind een mediator (kan een derde agent zijn)
        if len(self.agents) > 2:
            # Kies een agent die niet in de sessie zit
            mediators = [a for a in self.agents if a not in session.agents]
            if mediators:
                mediator_id = random.choice(mediators)
            else:
                # Fallback: simuleer mediator
                mediator_id = "mediator_1"
                self.mediators.append(mediator_id)
        else:
            # Simuleer externe mediator
            mediator_id = "mediator_1"
            if mediator_id not in self.mediators:
                self.mediators.append(mediator_id)
        
        logger.info(f"⚖️ Mediator {mediator_id[:8]} ingeschakeld")
        
        # Mediator stelt compromis voor
        compromise = {
            'mediator': mediator_id,
            'proposal': "Mediated compromise",
            'terms': [
                "Accept 50% of each agent's demands",
                "Create unified ontology with both perspectives",
                "Establish communication protocol for future conflicts"
            ]
        }
        
        session.add_log("mediation", compromise)
        
        # Forceer acceptatie (in echte implementatie zou mediator overtuigen)
        for agent_id in session.agents:
            if agent_id in self.agents:
                self.agents[agent_id].flexibility += 0.1
        
        logger.info(f"✅ Mediator voorstel: {compromise['terms']}")
    
    # ====================================================================
    # OPTIONEEL: VOTING VOOR MULTI-PARTY
    # ====================================================================
    
    async def vote(self, session_id: str, proposal_id: str, agent_id: str, vote: bool) -> bool:
        """Laat een agent stemmen op een voorstel."""
        if not self.enable_voting:
            return False
        
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        # Vind voorstel
        proposal = None
        for p in session.proposals:
            if p.id == proposal_id:
                proposal = p
                break
        
        if not proposal:
            return False
        
        # Registreer stem
        vote_record = {
            'timestamp': time.time(),
            'session': session_id,
            'proposal': proposal_id,
            'agent': agent_id,
            'vote': vote
        }
        
        self.vote_history[session_id].append(vote_record)
        self.stats['votes_cast'] += 1
        
        # Check of quorum is bereikt
        votes = self.vote_history[session_id]
        unique_voters = set(v['agent'] for v in votes)
        
        if len(unique_voters) >= len(session.agents) * 0.7:  # 70% quorum
            # Tel stemmen
            yes_votes = sum(1 for v in votes if v['vote'])
            no_votes = len(votes) - yes_votes
            
            if yes_votes > no_votes:
                proposal.status = ProposalStatus.ACCEPTED
                logger.info(f"✅ Voorstel {proposal_id[:8]} aangenomen ({yes_votes}-{no_votes})")
            else:
                proposal.status = ProposalStatus.REJECTED
                logger.info(f"❌ Voorstel {proposal_id[:8]} verworpen ({yes_votes}-{no_votes})")
        
        return True
    
    # ====================================================================
    # OPTIONEEL: BLOCKCHAIN CONSENSUS
    # ====================================================================
    
    async def create_consensus_block(self, session: DiplomaticSession) -> Dict:
        """Maak een blockchain-achtig consensus blok."""
        if not self.enable_blockchain:
            return {}
        
        # Maak een simpele blockchain entry
        block = {
            'index': len(self.completed_sessions),
            'timestamp': time.time(),
            'session_id': session.id,
            'agents': session.agents,
            'agreements': session.agreements,
            'previous_hash': self._get_previous_hash(),
            'hash': self._calculate_block_hash(session)
        }
        
        logger.info(f"🔗 Consensus blok toegevoegd: {block['hash'][:8]}")
        
        return block
    
    def _get_previous_hash(self) -> str:
        """Haal hash van vorig blok op."""
        if not hasattr(self, '_last_block_hash'):
            self._last_block_hash = hashlib.sha256(b"genesis").hexdigest()
        return self._last_block_hash
    
    def _calculate_block_hash(self, session: DiplomaticSession) -> str:
        """Bereken hash van een consensus blok."""
        data = f"{session.id}{session.agents}{len(session.agreements)}{self._get_previous_hash()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    # ====================================================================
    # OPTIONEEL: VISUALISATIE
    # ====================================================================
    
    def visualize_negotiation(self, session_id: str, filename: Optional[str] = None):
        """Visualiseer onderhandelingsverloop."""
        if not self.visualization:
            logger.warning("Visualisatie niet beschikbaar")
            return
        
        # Zoek sessie
        session = None
        if session_id in self.sessions:
            session = self.sessions[session_id]
        else:
            for s in self.completed_sessions:
                if s.id == session_id:
                    session = s
                    break
        
        if not session:
            logger.warning(f"Sessie {session_id} niet gevonden")
            return
        
        # Maak figuur
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: Voorstel-status per ronde
        rounds = []
        accepted = []
        rejected = []
        
        for i, prop in enumerate(session.proposals):
            rounds.append(i)
            if prop.status == ProposalStatus.ACCEPTED:
                accepted.append(1)
                rejected.append(0)
            elif prop.status == ProposalStatus.REJECTED:
                accepted.append(0)
                rejected.append(1)
            else:
                accepted.append(0)
                rejected.append(0)
        
        ax1.plot(rounds, accepted, 'g-', label='Accepted', linewidth=2)
        ax1.plot(rounds, rejected, 'r-', label='Rejected', linewidth=2)
        ax1.set_xlabel('Ronde')
        ax1.set_ylabel('Aantal')
        ax1.set_title(f'Onderhandelingsverloop - {session_id[:8]}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Overlap per ronde
        if hasattr(session, 'log'):
            overlaps = []
            times = []
            for entry in session.log:
                if entry['event'] == 'proposals_evaluated' and 'overlap' in entry['details']:
                    overlaps.append(entry['details']['overlap'])
                    times.append(entry['timestamp'] - session.start_time)
            
            if overlaps:
                ax2.plot(times, overlaps, 'b-', linewidth=2)
                ax2.axhline(y=self.min_overlap_threshold, color='r', linestyle='--', 
                           label=f'Threshold ({self.min_overlap_threshold})')
                ax2.set_xlabel('Tijd (s)')
                ax2.set_ylabel('Overlap')
                ax2.set_title('Voorstel-overlap over tijd')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Sla op
        if filename is None:
            filename = f"negotiation_{session_id[:8]}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📊 Visualisatie opgeslagen: {filename}")
    
    def visualize_trust_network(self, filename: Optional[str] = None):
        """Visualiseer vertrouwensnetwerk tussen agents."""
        if not self.visualization or not NETWORKX_AVAILABLE:
            return
        
        G = nx.Graph()
        
        # Voeg agents toe
        for agent_id, agent in self.agents.items():
            G.add_node(agent_id[:8], name=agent.name, reputation=agent.reputation)
        
        # Voeg trust edges toe
        for a, targets in self.trust_network.items():
            for b, trust in targets.items():
                if trust > 0.1:  # Alleen significante edges
                    G.add_edge(a[:8], b[:8], weight=trust)
        
        # Teken
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(G)
        
        # Nodes
        node_colors = [G.nodes[n]['reputation'] for n in G.nodes]
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                              cmap=plt.cm.RdYlGn, node_size=500)
        
        # Edges
        edge_weights = [G.edges[e]['weight'] for e in G.edges]
        nx.draw_networkx_edges(G, pos, width=[w*3 for w in edge_weights], alpha=0.5)
        
        # Labels
        labels = {n: G.nodes[n]['name'] for n in G.nodes}
        nx.draw_networkx_labels(G, pos, labels, font_size=10)
        
        plt.title('Vertrouwensnetwerk tussen Agents')
        plt.colorbar(plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn), label='Reputatie')
        plt.axis('off')
        
        if filename is None:
            filename = "trust_network.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📊 Trust network opgeslagen: {filename}")
    
    # ====================================================================
    # OPTIONEEL: VERDRAG & EXPORT
    # ====================================================================
    
    async def _create_treaty(self, session: DiplomaticSession, agreement: Dict) -> Dict:
        """Creëer een formeel verdrag op basis van overeenkomst."""
        treaty = {
            'treaty_id': f"treaty_{session.id}_{int(time.time())}",
            'created_at': time.time(),
            'parties': [
                {
                    'id': agent_id,
                    'name': self.agents[agent_id].name,
                    'principles': self.agents[agent_id].core_principles
                }
                for agent_id in session.agents
            ],
            'agreement': agreement,
            'terms': agreement.get('terms', []),
            'duration': 'permanent',  # Of tijdelijk
            'revision_mechanism': 'mutual_consent',
            'dispute_resolution': 'mediation' if self.enable_mediation else 'renegotiation',
            'hash': hashlib.sha256(json.dumps(agreement, sort_keys=True).encode()).hexdigest()
        }
        
        # Voeg toe aan sessie
        session.agreements.append(treaty)
        
        # Blockchain optioneel
        if self.enable_blockchain:
            block = await self.create_consensus_block(session)
            treaty['blockchain'] = block
        
        # Exporteer
        filename = f"treaty_{session.id[:8]}.json"
        with open(filename, 'w') as f:
            json.dump(treaty, f, indent=2, default=str)
        
        logger.info(f"📜 Verdrag opgeslagen: {filename}")
        
        return treaty
    
    # ====================================================================
    # STATISTIEKEN & RAPPORTAGE
    # ====================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Haal uitgebreide statistieken op."""
        active_sessions = len(self.sessions)
        completed = len(self.completed_sessions)
        
        # Bereken gemiddelden
        total_sessions = active_sessions + completed
        avg_duration = 0
        if completed > 0:
            durations = [s.last_update - s.start_time for s in self.completed_sessions]
            avg_duration = np.mean(durations) if durations else 0
        
        return {
            **self.stats,
            'active_sessions': active_sessions,
            'completed_sessions': completed,
            'total_sessions': total_sessions,
            'agents_count': len(self.agents),
            'avg_session_duration': avg_duration,
            'trust_network_density': self._calculate_trust_density(),
            'reputation_scores': self.reputation_scores.copy(),
            'mediators': len(self.mediators),
            'uptime': time.time() - self.stats['start_time']
        }
    
    def _calculate_trust_density(self) -> float:
        """Bereken dichtheid van vertrouwensnetwerk."""
        if len(self.agents) < 2:
            return 0.0
        
        total_possible = len(self.agents) * (len(self.agents) - 1)
        total_actual = sum(len(t) for t in self.trust_network.values())
        
        return total_actual / total_possible if total_possible > 0 else 0
    
    def get_session_report(self, session_id: str) -> Optional[Dict]:
        """Genereer rapport voor een specifieke sessie."""
        # Zoek sessie
        session = None
        if session_id in self.sessions:
            session = self.sessions[session_id]
        else:
            for s in self.completed_sessions:
                if s.id == session_id:
                    session = s
                    break
        
        if not session:
            return None
        
        return {
            'session_id': session.id,
            'agents': [self.agents[a].name for a in session.agents],
            'status': session.status,
            'duration': session.last_update - session.start_time,
            'rounds': session.round,
            'proposals': len(session.proposals),
            'agreements': len(session.agreements),
            'strategy': session.strategy.value,
            'log_entries': len(session.log),
            'timeline': [
                {
                    'time': entry['timestamp'] - session.start_time,
                    'event': entry['event'],
                    'round': entry.get('round', 0)
                }
                for entry in session.log
            ]
        }
    
    def export_all(self, filename: str = "diplomacy_export.json"):
        """Exporteer alle diplomatieke data."""
        data = {
            'export_time': time.time(),
            'stats': self.get_stats(),
            'agents': {
                aid: {
                    'name': a.name,
                    'capabilities': a.capabilities,
                    'reputation': a.reputation,
                    'negotiations': a.negotiation_count,
                    'success_rate': a.success_count / a.negotiation_count if a.negotiation_count > 0 else 0
                }
                for aid, a in self.agents.items()
            },
            'trust_network': {
                a: {b: trust for b, trust in targets.items()}
                for a, targets in self.trust_network.items()
            },
            'sessions': [
                {
                    'id': s.id,
                    'agents': [self.agents[a].name for a in s.agents],
                    'status': s.status,
                    'rounds': s.round,
                    'agreements': len(s.agreements)
                }
                for s in self.completed_sessions[-50:]  # Laatste 50
            ],
            'mediators': self.mediators
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"📄 Diplomatieke data geëxporteerd naar {filename}")
        return filename
    
    # ====================================================================
    # CONFIGURATIE
    # ====================================================================
    
    def _load_config(self, config_path: str):
        """Laad configuratie uit JSON/YAML bestand."""
        try:
            if config_path.endswith('.json'):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            elif config_path.endswith(('.yaml', '.yml')):
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
            else:
                return
            
            # Update parameters
            dipl_config = config.get('ontological_diplomacy', {})
            
            if 'strategy' in dipl_config:
                self.strategy = NegotiationStrategy(dipl_config['strategy'])
            if 'max_rounds' in dipl_config:
                self.max_rounds = dipl_config['max_rounds']
            if 'proposal_timeout' in dipl_config:
                self.proposal_timeout = dipl_config['proposal_timeout']
            if 'min_overlap_threshold' in dipl_config:
                self.min_overlap_threshold = dipl_config['min_overlap_threshold']
            if 'use_quantum_evaluation' in dipl_config:
                self.use_quantum_evaluation = dipl_config['use_quantum_evaluation']
            if 'use_trust_scores' in dipl_config:
                self.use_trust_scores = dipl_config['use_trust_scores']
            if 'use_reputation' in dipl_config:
                self.use_reputation = dipl_config['use_reputation']
            if 'enable_mediation' in dipl_config:
                self.enable_mediation = dipl_config['enable_mediation']
            if 'enable_voting' in dipl_config:
                self.enable_voting = dipl_config['enable_voting']
            if 'enable_blockchain' in dipl_config:
                self.enable_blockchain = dipl_config['enable_blockchain']
            
            logger.info(f"📋 Configuratie geladen uit: {config_path}")
            
        except Exception as e:
            logger.error(f"❌ Configuratie laden mislukt: {e}")
    
    # ====================================================================
    # RESOURCE MANAGEMENT
    # ====================================================================
    
    async def cleanup(self):
        """Ruim resources op."""
        logger.info("🧹 OntologicalDiplomat cleanup...")
        
        # Export alle data
        self.export_all("diplomacy_final.json")
        
        logger.info("✅ Cleanup voltooid")
    
    def reset(self):
        """Reset alle data (voor testing)."""
        self.sessions.clear()
        self.completed_sessions.clear()
        self.trust_network.clear()
        self.vote_history.clear()
        self.reputation_scores.clear()
        self.stats = {
            'sessions_initiated': 0,
            'sessions_completed': 0,
            'sessions_failed': 0,
            'proposals_made': 0,
            'proposals_accepted': 0,
            'proposals_rejected': 0,
            'quantum_evaluations': 0,
            'mediations_used': 0,
            'votes_cast': 0,
            'start_time': time.time()
        }
        logger.info("🔄 OntologicalDiplomat gereset")


# ====================================================================
# CONVENIENCE FUNCTIES
# ====================================================================

def create_diplomat(nexus_a=None, nexus_b=None, config_path: Optional[str] = None, **kwargs) -> OntologicalDiplomat:
    """
    Maak een OntologicalDiplomat instantie met gegeven configuratie.
    
    Args:
        nexus_a: Eerste Nexus systeem
        nexus_b: Tweede Nexus systeem
        config_path: Optioneel pad naar configuratiebestand
        **kwargs: Overschrijf specifieke parameters
    
    Returns:
        Geïnitialiseerde OntologicalDiplomat
    """
    return OntologicalDiplomat(
        nexus_a=nexus_a,
        nexus_b=nexus_b,
        config_path=config_path,
        **kwargs
    )


# ====================================================================
# DEMONSTRATIE
# ====================================================================

async def demo():
    """Demonstreer Ontological Diplomacy functionaliteit."""
    print("\n" + "="*80)
    print("🤝 ONTOLOGICAL DIPLOMACY V13 DEMONSTRATIE")
    print("="*80)
    
    # Maak mock Nexus systemen
    class MockNexus:
        def __init__(self, name, version):
            self.name = name
            self.version = version
            self.layer12 = MockLayer12()
            self.layer13 = MockLayer13()
            self.layer15 = MockLayer15()
    
    class MockLayer12:
        def __init__(self):
            self.meta_ontology = None
    
    class MockLayer13:
        async def generate_novel_structure(self, seed):
            class MockStructure:
                def __init__(self):
                    self.id = f"struct_{int(time.time())}"
                    self.resonantie_veld = np.random.randn(10)
            return MockStructure()
    
    class MockLayer15:
        def __init__(self):
            self.ethical_principles = {
                'harm_minimization': type('obj', (), {'weight': 0.9})(),
                'fairness': type('obj', (), {'weight': 0.8})(),
                'sustainability': type('obj', (), {'weight': 0.95})()
            }
    
    nexus_a = MockNexus("Nexus_Alpha", "13.0")
    nexus_b = MockNexus("Nexus_Beta", "13.0")
    
    # Maak diplomaat met alle opties
    diplomat = OntologicalDiplomat(
        nexus_a=nexus_a,
        nexus_b=nexus_b,
        strategy=NegotiationStrategy.ADAPTIVE,
        max_rounds=20,
        proposal_timeout=60.0,
        min_overlap_threshold=0.6,
        use_quantum_evaluation=QISKIT_AVAILABLE,
        use_trust_scores=True,
        use_reputation=True,
        enable_mediation=True,
        enable_voting=True,
        enable_blockchain=False,
        visualization=VISUALIZATION_AVAILABLE
    )
    
    print("\n📋 Test 1: Registreer agents")
    agent_a_id = list(diplomat.agents.keys())[0]
    agent_b_id = list(diplomat.agents.keys())[1]
    print(f"   Agent A: {diplomat.agents[agent_a_id].name}")
    print(f"   Agent B: {diplomat.agents[agent_b_id].name}")
    
    print("\n📋 Test 2: Onderhandelingen")
    issues = [
        "Conflict over concept 'quantum'",
        "Verschillende ethische principes",
        "Unified ontology vereisten"
    ]
    
    session = await diplomat.negotiate(
        agent_a_id, agent_b_id,
        initial_issues=issues
    )
    
    if session:
        print(f"\n✅ Onderhandeling succesvol!")
        print(f"   Sessie: {session.id[:8]}")
        print(f"   Rondes: {session.round}")
        print(f"   Voorstellen: {len(session.proposals)}")
        print(f"   Overeenkomsten: {len(session.agreements)}")
    
    print("\n📋 Test 3: Vertrouwensscores")
    trust = diplomat.get_trust_level(agent_a_id, agent_b_id)
    print(f"   Vertrouwen: {trust.name}")
    print(f"   Trust score: {diplomat.trust_network[agent_a_id].get(agent_b_id, 0):.3f}")
    
    print("\n📋 Test 4: Reputatie")
    if diplomat.use_reputation:
        rep_a = diplomat.agents[agent_a_id].reputation
        rep_b = diplomat.agents[agent_b_id].reputation
        print(f"   Reputatie A: {rep_a:.3f}")
        print(f"   Reputatie B: {rep_b:.3f}")
    
    print("\n📋 Test 5: Statistieken")
    stats = diplomat.get_stats()
    print(f"   Sessies: {stats['sessions_initiated']}")
    print(f"   Voorstellen: {stats['proposals_made']}")
    print(f"   Quantum evaluaties: {stats['quantum_evaluations']}")
    print(f"   Trust density: {stats['trust_network_density']:.3f}")
    
    print("\n📋 Test 6: Rapport")
    if session:
        report = diplomat.get_session_report(session.id)
        if report:
            print(f"   Sessie status: {report['status']}")
            print(f"   Duur: {report['duration']:.1f}s")
            print(f"   Rondes: {report['rounds']}")
    
    print("\n📋 Test 7: Visualisatie")
    if VISUALIZATION_AVAILABLE and session:
        diplomat.visualize_negotiation(session.id)
        diplomat.visualize_trust_network()
    
    print("\n📋 Test 8: Export")
    diplomat.export_all("diplomacy_demo.json")
    
    # Cleanup
    await diplomat.cleanup()
    
    print("\n" + "="*80)
    print("✅ Demonstratie voltooid!")
    print("="*80)


if __name__ == "__main__":
    # Configureer logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    asyncio.run(demo())