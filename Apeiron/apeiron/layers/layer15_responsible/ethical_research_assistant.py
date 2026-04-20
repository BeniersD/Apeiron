"""
ETHICAL RESEARCH ASSISTANT - V12 COMPATIBLE
Real-time ethical evaluation and guidance for research directions
Uses Layer 15 (Ethical Convergence) for distributed responsibility

Uitbreidingen:
- Configuratie management
- Metrics tracking
- Caching voor guidelines
- Batch evaluatie
- Export verbeteringen
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import logging
import hashlib
import time
from collections import defaultdict
from functools import lru_cache
import os

# Import Layer 15
from layers_11_to_17 import Layer15_EthicalConvergence, EthicalPrinciple

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResearchDomain(Enum):
    """Research domain categories."""
    AI_ML = "Artificial Intelligence & Machine Learning"
    BIOTECH = "Biotechnology & Genetics"
    SURVEILLANCE = "Surveillance & Monitoring"
    WEAPONS = "Weapons & Defense"
    SOCIAL = "Social Engineering & Manipulation"
    AUTONOMOUS = "Autonomous Systems"
    HUMAN_ENHANCEMENT = "Human Enhancement"
    ENVIRONMENTAL = "Environmental Technology"
    GENERAL = "General Research"
    
    @property
    def id(self) -> str:
        """Unieke identifier voor domein."""
        return self.name.lower()


@dataclass
class EthicalConcern:
    """Represents an ethical concern identified in research."""
    concern_type: str
    severity: RiskLevel
    description: str
    affected_stakeholders: List[str]
    potential_harms: List[str]
    mitigation_strategies: List[str]
    relevant_principles: List[str]
    timestamp: float = field(default_factory=time.time)
    
    @property
    def id(self) -> str:
        """Uniek ID voor deze concern."""
        hash_input = f"{self.concern_type}{self.description}".encode()
        return f"CONCERN_{hashlib.md5(hash_input).hexdigest()[:8].upper()}"


@dataclass
class ResearchProposal:
    """A research proposal to be evaluated."""
    title: str
    description: str
    domain: ResearchDomain
    objectives: List[str]
    methods: List[str]
    potential_applications: List[str]
    stakeholders: List[str]
    timeline: Optional[str] = None
    funding_source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def id(self) -> str:
        """Uniek ID voor deze proposal."""
        hash_input = f"{self.title}{time.time()}".encode()
        return f"PROP_{hashlib.md5(hash_input).hexdigest()[:8].upper()}"


@dataclass
class EthicalEvaluation:
    """Complete ethical evaluation of a research proposal."""
    id: str
    proposal: ResearchProposal
    timestamp: datetime
    
    # Layer 15 scores
    harm_score: float
    fairness_score: float
    sustainability_score: float
    autonomy_score: float
    aggregate_score: float
    
    # Risk assessment
    overall_risk: RiskLevel
    concerns: List[EthicalConcern]
    
    # Recommendations
    recommendation: str  # PROCEED, MODIFY, RECONSIDER, REJECT
    modifications: List[str]
    alternatives: List[str]
    
    # Governance
    required_oversight: List[str]
    stakeholder_engagement: List[str]
    monitoring_requirements: List[str]
    
    # Metrics
    processing_time_ms: float = 0.0
    violation_detected: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary voor export."""
        return {
            'id': self.id,
            'proposal_title': self.proposal.title,
            'proposal_domain': self.proposal.domain.value,
            'timestamp': self.timestamp.isoformat(),
            'scores': {
                'harm': self.harm_score,
                'fairness': self.fairness_score,
                'sustainability': self.sustainability_score,
                'autonomy': self.autonomy_score,
                'aggregate': self.aggregate_score
            },
            'risk_level': self.overall_risk.value,
            'recommendation': self.recommendation,
            'violation_detected': self.violation_detected,
            'num_concerns': len(self.concerns),
            'processing_time_ms': self.processing_time_ms
        }


@dataclass
class EthicalGuideline:
    """Ethical guidelines for specific domains."""
    domain: ResearchDomain
    red_lines: List[str]  # Absolute prohibitions
    yellow_flags: List[str]  # Requires extra scrutiny
    best_practices: List[str]
    case_studies: List[Dict[str, str]]
    last_updated: float = field(default_factory=time.time)
    version: str = "1.0"


class EthicalResearchAssistant:
    """
    Helps researchers avoid harmful directions and navigate ethical challenges.
    
    This provides real-time ethical guidance using Layer 15's ethical
    convergence framework with distributed responsibility tracking.
    
    V12 enhancements:
    - Configuratie management
    - Metrics tracking
    - Caching voor guidelines
    - Batch evaluatie
    - Export verbeteringen
    """
    
    def __init__(self, 
                 layer15: Layer15_EthicalConvergence,
                 config_path: Optional[str] = None):
        """
        Initialize Ethical Research Assistant.
        
        Args:
            layer15: Layer15_EthicalConvergence instance
            config_path: Optional path to config file
        """
        self.layer15 = layer15
        
        # Load configuration
        self._load_config(config_path)
        
        # Evaluation history
        self.evaluations: List[EthicalEvaluation] = []
        self.evaluations_by_domain: Dict[str, List[EthicalEvaluation]] = defaultdict(list)
        
        # Domain-specific guidelines
        self.guidelines: Dict[ResearchDomain, EthicalGuideline] = {}
        self._initialize_guidelines()
        
        # Red flag keywords by category
        self.red_flag_keywords = self._initialize_red_flags()
        
        # Stakeholder impact weights (uit config)
        self.stakeholder_weights = self.config.get('stakeholder_weights', {
            'general_public': 1.0,
            'vulnerable_populations': 1.5,
            'environment': 1.2,
            'future_generations': 1.3,
            'researchers': 0.8
        })
        
        # Metrics tracking
        self.metrics = {
            'total_evaluations': 0,
            'total_violations': 0,
            'total_concerns': 0,
            'avg_aggregate_score': 0.0,
            'recommendations': defaultdict(int),
            'risk_distribution': defaultdict(int),
            'avg_processing_time': 0.0,
            'start_time': time.time()
        }
        
        logger.info("="*80)
        logger.info("⚖️ ETHICAL RESEARCH ASSISTANT V12")
        logger.info("="*80)
        logger.info(f"Auto evaluate: {self.config.get('auto_evaluate', True)}")
        logger.info(f"Risk thresholds: {self.config.get('risk_thresholds', {})}")
        logger.info(f"Stakeholder weights: {len(self.stakeholder_weights)}")
        logger.info("="*80)
    
    def _load_config(self, config_path: Optional[str] = None):
        """Load configuration from file."""
        # Default configuration
        self.config = {
            'auto_evaluate': True,
            'risk_thresholds': {
                'low': 0.3,
                'medium': 0.5,
                'high': 0.7,
                'critical': 0.9
            },
            'stakeholder_weights': {
                'general_public': 1.0,
                'vulnerable_populations': 1.5,
                'environment': 1.2,
                'future_generations': 1.3,
                'researchers': 0.8
            },
            'required_oversight': {
                'high': ['ethics_board', 'external_review'],
                'critical': ['ethics_board', 'external_review', 'public_consultation']
            },
            'principle_weights': {
                'harm_minimization': 1.0,
                'fairness': 0.9,
                'sustainability': 0.95,
                'autonomy': 0.85
            },
            'cache_size': 100,
            'export_on_evaluation': True
        }
        
        if config_path and os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                ethics_config = config.get('ethical_assistant', {})
                self.config.update(ethics_config)
                logger.info(f"📋 Configuratie geladen uit: {config_path}")
                
            except Exception as e:
                logger.warning(f"⚠️ Kon configuratie niet laden: {e}")
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    def _initialize_guidelines(self):
        """Initialize domain-specific ethical guidelines."""
        
        # AI/ML Guidelines
        self.guidelines[ResearchDomain.AI_ML] = EthicalGuideline(
            domain=ResearchDomain.AI_ML,
            red_lines=[
                "Autonomous weapons without human oversight",
                "Uncontrolled AGI development",
                "Mass surveillance without consent",
                "Deepfakes for non-consensual purposes",
                "AI for manipulation of democratic processes"
            ],
            yellow_flags=[
                "Facial recognition technology",
                "Predictive policing algorithms",
                "Social credit systems",
                "Automated decision-making in high-stakes domains",
                "Large-scale behavior manipulation"
            ],
            best_practices=[
                "Transparent model documentation",
                "Bias testing across demographics",
                "Human-in-the-loop for critical decisions",
                "Privacy-preserving techniques",
                "Stakeholder participation in design"
            ],
            case_studies=[
                {
                    'title': 'COMPAS Recidivism Algorithm',
                    'lesson': 'Algorithmic bias can perpetuate systemic discrimination',
                    'outcome': 'Required bias audits and transparency'
                }
            ]
        )
        
        # Biotechnology Guidelines
        self.guidelines[ResearchDomain.BIOTECH] = EthicalGuideline(
            domain=ResearchDomain.BIOTECH,
            red_lines=[
                "Human germline editing without broad consensus",
                "Gain-of-function research on pandemic pathogens without strict containment",
                "Bioweapons development",
                "Human cloning for reproduction",
                "Creation of sentient organisms without ethical framework"
            ],
            yellow_flags=[
                "CRISPR applications in humans",
                "Synthetic biology with release potential",
                "Enhancement technologies creating inequality",
                "Animal experimentation without alternatives",
                "Dual-use research with weaponization potential"
            ],
            best_practices=[
                "Institutional review board approval",
                "Informed consent protocols",
                "Risk-benefit analysis with public input",
                "Containment and safety protocols",
                "Long-term environmental impact assessment"
            ],
            case_studies=[
                {
                    'title': 'He Jiankui CRISPR Babies',
                    'lesson': 'Premature human germline editing without consensus causes global concern',
                    'outcome': 'International moratorium and stricter oversight'
                }
            ]
        )
        
        # Surveillance Guidelines
        self.guidelines[ResearchDomain.SURVEILLANCE] = EthicalGuideline(
            domain=ResearchDomain.SURVEILLANCE,
            red_lines=[
                "Mass surveillance without judicial oversight",
                "Surveillance of political dissidents",
                "Covert biometric collection",
                "Surveillance technology sales to authoritarian regimes",
                "Backdoors in encryption systems"
            ],
            yellow_flags=[
                "Workplace monitoring systems",
                "Public space facial recognition",
                "Social media scraping at scale",
                "Location tracking without explicit consent",
                "Behavioral analytics for prediction"
            ],
            best_practices=[
                "Minimize data collection",
                "Transparent surveillance policies",
                "Strong encryption and access controls",
                "Regular audits and oversight",
                "Clear retention and deletion policies"
            ],
            case_studies=[
                {
                    'title': 'NSA Mass Surveillance Program',
                    'lesson': 'Unchecked surveillance erodes civil liberties',
                    'outcome': 'Legal reforms and oversight mechanisms'
                }
            ]
        )
        
        # Weapons Guidelines
        self.guidelines[ResearchDomain.WEAPONS] = EthicalGuideline(
            domain=ResearchDomain.WEAPONS,
            red_lines=[
                "Autonomous weapons without meaningful human control",
                "Chemical or biological weapons",
                "Weapons of mass destruction",
                "Weapons designed to cause indiscriminate harm"
            ],
            yellow_flags=[
                "Dual-use technologies with weapons potential",
                "Military funding for civilian research",
                "Defensive weapons systems"
            ],
            best_practices=[
                "Clear distinction between defensive and offensive",
                "International treaty compliance",
                "Independent ethical review"
            ],
            case_studies=[]
        )
        
        logger.info(f"✅ Geladen guidelines voor {len(self.guidelines)} domeinen")
    
    def _initialize_red_flags(self) -> Dict[str, List[str]]:
        """Initialize red flag keyword detection."""
        return {
            'weapons': [
                'weapon', 'lethal', 'autonomous attack', 'military targeting',
                'kill chain', 'combat system', 'munitions', 'warfare'
            ],
            'surveillance': [
                'mass surveillance', 'covert monitoring', 'unauthorized tracking',
                'backdoor access', 'bulk collection', 'dragnet', 'wiretap'
            ],
            'manipulation': [
                'manipulate behavior', 'covert influence', 'subliminal',
                'psychological warfare', 'dark patterns at scale', 'nudge',
                'behavior modification', 'propaganda'
            ],
            'discrimination': [
                'genetic discrimination', 'algorithmic bias', 'social scoring',
                'automated discrimination', 'profiling without consent',
                'racial profiling', 'ethnic filtering'
            ],
            'autonomy_violation': [
                'without informed consent', 'covert experimentation',
                'forced modification', 'mandatory enhancement',
                'involuntary treatment', 'coerced participation'
            ],
            'environmental': [
                'irreversible environmental damage', 'ecosystem collapse',
                'uncontrolled release', 'extinction risk', 'pollution',
                'habitat destruction', 'biodiversity loss'
            ]
        }
    
    # ========================================================================
    # CACHED METHODS
    # ========================================================================
    
    @lru_cache(maxsize=100)
    def get_domain_guidelines(self, domain: ResearchDomain) -> Optional[EthicalGuideline]:
        """Get cached domain guidelines."""
        return self.guidelines.get(domain)
    
    # ========================================================================
    # ETHICAL EVALUATION
    # ========================================================================
    
    def evaluate_proposal(self, proposal: ResearchProposal) -> EthicalEvaluation:
        """
        Comprehensive ethical evaluation of a research proposal.
        
        Args:
            proposal: ResearchProposal to evaluate
            
        Returns:
            EthicalEvaluation with scores, concerns, and recommendations
        """
        start_time = time.time()
        
        logger.info(f"\n⚖️ Evaluating: {proposal.title}")
        logger.info(f"   Domain: {proposal.domain.value}")
        
        # Step 1: Red flag detection
        red_flags = self._detect_red_flags(proposal)
        
        # Step 2: Domain-specific guideline check
        guideline_concerns = self._check_guidelines(proposal)
        
        # Step 3: Layer 15 ethical scoring
        ethical_scores = self._compute_ethical_scores(proposal, red_flags)
        
        # Step 4: Stakeholder impact analysis
        stakeholder_impacts = self._analyze_stakeholder_impacts(proposal)
        
        # Step 5: Risk assessment
        overall_risk = self._assess_risk(ethical_scores, red_flags, guideline_concerns)
        
        # Step 6: Compile concerns
        all_concerns = red_flags + guideline_concerns + stakeholder_impacts
        
        # Step 7: Generate recommendations
        recommendation = self._generate_recommendation(ethical_scores, overall_risk)
        modifications = self._suggest_modifications(all_concerns, proposal)
        alternatives = self._suggest_alternatives(proposal, all_concerns)
        
        # Step 8: Governance requirements
        oversight = self._determine_oversight(overall_risk, proposal)
        engagement = self._determine_stakeholder_engagement(proposal)
        monitoring = self._determine_monitoring(overall_risk)
        
        # Check for violations
        action = {
            'harm_level': ethical_scores.get('harm_minimization', 0.5),
            'resource_distribution': [ethical_scores.get('fairness', 0.5), 1-ethical_scores.get('fairness', 0.5)],
            'sustainability_impact': ethical_scores.get('sustainability', 0.5),
            'autonomy_preserved': ethical_scores.get('autonomy', 0.5) > 0.5
        }
        violation = self.layer15.detect_ethical_violation(action)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        
        # Create evaluation with unique ID
        evaluation_id = f"EVAL_{hashlib.md5(f'{proposal.id}{time.time()}'.encode()).hexdigest()[:8].upper()}"
        
        evaluation = EthicalEvaluation(
            id=evaluation_id,
            proposal=proposal,
            timestamp=datetime.now(),
            harm_score=ethical_scores.get('harm_minimization', 0.5),
            fairness_score=ethical_scores.get('fairness', 0.5),
            sustainability_score=ethical_scores.get('sustainability', 0.5),
            autonomy_score=ethical_scores.get('autonomy', 0.5),
            aggregate_score=ethical_scores.get('aggregate', 0.5),
            overall_risk=overall_risk,
            concerns=all_concerns,
            recommendation=recommendation,
            modifications=modifications,
            alternatives=alternatives,
            required_oversight=oversight,
            stakeholder_engagement=engagement,
            monitoring_requirements=monitoring,
            processing_time_ms=processing_time,
            violation_detected=violation is not None
        )
        
        # Store evaluation
        self.evaluations.append(evaluation)
        self.evaluations_by_domain[proposal.domain.name].append(evaluation)
        
        # Update metrics
        self._update_metrics(evaluation)
        
        # Track with Layer 15
        self.layer15.attribute_responsibility(
            action_id=f"research_{len(self.evaluations)}",
            agents=[proposal.title],
            outcome=ethical_scores
        )
        
        # Auto-export if configured
        if self.config.get('export_on_evaluation', True):
            self.export_evaluation(evaluation, f"evaluation_{evaluation.id}.json")
        
        self._print_evaluation_summary(evaluation)
        
        return evaluation
    
    def _update_metrics(self, evaluation: EthicalEvaluation):
        """Update metrics with new evaluation."""
        self.metrics['total_evaluations'] += 1
        self.metrics['total_concerns'] += len(evaluation.concerns)
        self.metrics['recommendations'][evaluation.recommendation] += 1
        self.metrics['risk_distribution'][evaluation.overall_risk.value] += 1
        
        if evaluation.violation_detected:
            self.metrics['total_violations'] += 1
        
        # Update running average
        n = self.metrics['total_evaluations']
        old_avg = self.metrics['avg_aggregate_score']
        new_score = evaluation.aggregate_score
        self.metrics['avg_aggregate_score'] = (old_avg * (n-1) + new_score) / n
        
        old_time_avg = self.metrics['avg_processing_time']
        self.metrics['avg_processing_time'] = (old_time_avg * (n-1) + evaluation.processing_time_ms) / n
    
    def _detect_red_flags(self, proposal: ResearchProposal) -> List[EthicalConcern]:
        """Detect red flag keywords in proposal."""
        concerns = []
        
        full_text = (
            f"{proposal.title} {proposal.description} "
            f"{' '.join(proposal.objectives)} {' '.join(proposal.potential_applications)}"
        ).lower()
        
        for category, keywords in self.red_flag_keywords.items():
            for keyword in keywords:
                if keyword.lower() in full_text:
                    concern = EthicalConcern(
                        concern_type=f"red_flag_{category}",
                        severity=RiskLevel.HIGH,
                        description=f"Detected high-risk keyword: '{keyword}'",
                        affected_stakeholders=['general_public', 'vulnerable_populations'],
                        potential_harms=[f"Potential for {category.replace('_', ' ')}"],
                        mitigation_strategies=[
                            "Extensive ethical review required",
                            "Independent oversight board",
                            "Public consultation"
                        ],
                        relevant_principles=['harm_minimization', 'autonomy', 'fairness']
                    )
                    concerns.append(concern)
                    logger.debug(f"🚩 Red flag detected: {keyword}")
                    break  # One per category
        
        return concerns
    
    def _check_guidelines(self, proposal: ResearchProposal) -> List[EthicalConcern]:
        """Check against domain-specific guidelines."""
        concerns = []
        
        guideline = self.get_domain_guidelines(proposal.domain)
        if not guideline:
            return concerns
        
        full_text = (
            f"{proposal.title} {proposal.description} "
            f"{' '.join(proposal.objectives)}"
        ).lower()
        
        # Check red lines
        for red_line in guideline.red_lines:
            if any(word.lower() in full_text for word in red_line.split()):
                concern = EthicalConcern(
                    concern_type="red_line_violation",
                    severity=RiskLevel.CRITICAL,
                    description=f"Potential red line violation: {red_line}",
                    affected_stakeholders=['general_public', 'future_generations'],
                    potential_harms=[
                        "Severe ethical violation",
                        "Potential for catastrophic harm",
                        "Violation of ethical consensus"
                    ],
                    mitigation_strategies=[
                        "Project redesign required",
                        "International ethical review",
                        "Consider alternative approaches"
                    ],
                    relevant_principles=['harm_minimization', 'sustainability']
                )
                concerns.append(concern)
                logger.warning(f"🔴 Red line violation detected: {red_line}")
        
        # Check yellow flags
        for yellow_flag in guideline.yellow_flags:
            if any(word.lower() in full_text for word in yellow_flag.split()):
                concern = EthicalConcern(
                    concern_type="yellow_flag",
                    severity=RiskLevel.MEDIUM,
                    description=f"Requires extra scrutiny: {yellow_flag}",
                    affected_stakeholders=['general_public'],
                    potential_harms=["Potential for misuse", "Ethical complexity"],
                    mitigation_strategies=[
                        "Enhanced ethical review",
                        "Stakeholder consultation",
                        "Risk mitigation plan required"
                    ],
                    relevant_principles=['fairness', 'autonomy']
                )
                concerns.append(concern)
                logger.info(f"🟡 Yellow flag: {yellow_flag}")
        
        return concerns
    
    def _compute_ethical_scores(self, proposal: ResearchProposal,
                                red_flags: List[EthicalConcern]) -> Dict[str, float]:
        """Compute ethical scores using Layer 15."""
        
        # Assess harm level
        harm_level = 0.1  # Base level
        if any(c.severity == RiskLevel.CRITICAL for c in red_flags):
            harm_level = 0.9
        elif any(c.severity == RiskLevel.HIGH for c in red_flags):
            harm_level = 0.6
        elif any(c.severity == RiskLevel.MEDIUM for c in red_flags):
            harm_level = 0.3
        
        # Assess fairness (distribution of benefits/risks)
        fairness_distribution = self._assess_fairness(proposal)
        
        # Assess sustainability
        sustainability_impact = self._assess_sustainability(proposal)
        
        # Assess autonomy
        autonomy_preserved = self._assess_autonomy(proposal)
        
        # Create action for Layer 15
        action = {
            'harm_level': harm_level,
            'resource_distribution': fairness_distribution,
            'sustainability_impact': sustainability_impact,
            'autonomy_preserved': autonomy_preserved
        }
        
        # Get Layer 15 evaluation
        scores = self.layer15.evaluate_action(action)
        
        return scores
    
    def _assess_fairness(self, proposal: ResearchProposal) -> List[float]:
        """Assess distribution of benefits and risks."""
        text = (proposal.description + ' ' + ' '.join(proposal.objectives)).lower()
        
        if 'equitable' in text or 'accessible' in text or 'inclusive' in text:
            return [0.5, 0.5]  # Equal distribution
        elif 'elite' in text or 'exclusive' in text or 'privileged' in text:
            return [0.9, 0.1]  # Concentrated
        elif 'public' in text or 'society' in text or 'community' in text:
            return [0.6, 0.4]  # Somewhat distributed
        else:
            return [0.7, 0.3]  # Somewhat concentrated
    
    def _assess_sustainability(self, proposal: ResearchProposal) -> float:
        """Assess long-term sustainability impact."""
        sustainability_keywords = [
            'sustainable', 'renewable', 'conservation', 'long-term',
            'environmental', 'ecosystem', 'climate', 'green', 'circular'
        ]
        
        text = (proposal.description + ' ' + ' '.join(proposal.objectives)).lower()
        
        positive_count = sum(1 for kw in sustainability_keywords if kw in text)
        
        if 'irreversible' in text or 'permanent damage' in text or 'extinction' in text:
            return 0.2
        elif positive_count > 2:
            return 0.9
        elif positive_count > 0:
            return 0.7
        else:
            return 0.5
    
    def _assess_autonomy(self, proposal: ResearchProposal) -> bool:
        """Assess if proposal respects autonomy."""
        autonomy_violations = [
            'mandatory', 'forced', 'covert', 'without consent',
            'unauthorized', 'involuntary', 'coerced', 'obligatory'
        ]
        
        text = (proposal.description + ' ' + ' '.join(proposal.objectives)).lower()
        
        return not any(violation in text for violation in autonomy_violations)
    
    def _analyze_stakeholder_impacts(self, proposal: ResearchProposal) -> List[EthicalConcern]:
        """Analyze impacts on different stakeholder groups."""
        concerns = []
        
        # Check for vulnerable populations
        vulnerable_keywords = [
            'children', 'elderly', 'disabled', 'prisoners',
            'refugees', 'minorities', 'indigenous', 'patients',
            'pregnant', 'mentally ill', 'economically disadvantaged'
        ]
        
        text = proposal.description.lower()
        
        for keyword in vulnerable_keywords:
            if keyword in text:
                concern = EthicalConcern(
                    concern_type="vulnerable_population",
                    severity=RiskLevel.MEDIUM,
                    description=f"Research involves vulnerable population: {keyword}",
                    affected_stakeholders=[keyword],
                    potential_harms=[
                        "Exploitation risk",
                        "Inadequate protections",
                        "Power imbalance",
                        "Informed consent challenges"
                    ],
                    mitigation_strategies=[
                        "Enhanced informed consent",
                        "Independent advocacy",
                        "Extra safeguards required",
                        "Community consultation"
                    ],
                    relevant_principles=['fairness', 'autonomy', 'harm_minimization']
                )
                concerns.append(concern)
                logger.info(f"👥 Vulnerable population detected: {keyword}")
        
        return concerns
    
    def _assess_risk(self, ethical_scores: Dict[str, float],
                    red_flags: List[EthicalConcern],
                    guideline_concerns: List[EthicalConcern]) -> RiskLevel:
        """Assess overall risk level."""
        
        # Check for critical concerns
        if any(c.severity == RiskLevel.CRITICAL for c in red_flags + guideline_concerns):
            return RiskLevel.CRITICAL
        
        # Check ethical scores
        thresholds = self.config.get('risk_thresholds', {})
        agg_score = ethical_scores.get('aggregate', 0.5)
        
        if agg_score < thresholds.get('critical', 0.2):
            return RiskLevel.CRITICAL
        elif agg_score < thresholds.get('high', 0.4):
            return RiskLevel.HIGH
        elif agg_score < thresholds.get('medium', 0.6):
            return RiskLevel.MEDIUM
        
        # Check for high-risk concerns
        if any(c.severity == RiskLevel.HIGH for c in red_flags + guideline_concerns):
            return RiskLevel.HIGH
        
        # Check for medium concerns
        if any(c.severity == RiskLevel.MEDIUM for c in red_flags + guideline_concerns):
            return RiskLevel.MEDIUM
        
        # Otherwise low risk
        return RiskLevel.LOW
    
    def _generate_recommendation(self, ethical_scores: Dict[str, float],
                                 risk: RiskLevel) -> str:
        """Generate recommendation based on evaluation."""
        
        if risk == RiskLevel.CRITICAL:
            return "REJECT"
        elif risk == RiskLevel.HIGH:
            if ethical_scores.get('aggregate', 0.5) < 0.5:
                return "RECONSIDER"
            else:
                return "MODIFY"
        elif risk == RiskLevel.MEDIUM:
            return "MODIFY"
        else:
            if ethical_scores.get('aggregate', 0.5) > 0.7:
                return "PROCEED"
            else:
                return "MODIFY"
    
    def _suggest_modifications(self, concerns: List[EthicalConcern],
                              proposal: ResearchProposal) -> List[str]:
        """Suggest modifications to address concerns."""
        modifications = []
        
        concern_types = set(c.concern_type for c in concerns)
        
        if 'red_flag_weapons' in concern_types:
            modifications.append("Remove autonomous lethal capabilities; require human oversight")
        
        if 'red_flag_surveillance' in concern_types:
            modifications.append("Implement privacy-preserving techniques and transparent data policies")
        
        if 'red_flag_manipulation' in concern_types:
            modifications.append("Add disclosure requirements and opt-out mechanisms")
        
        if 'vulnerable_population' in concern_types:
            modifications.append("Implement enhanced protections and independent advocacy")
        
        if 'yellow_flag' in concern_types:
            modifications.append("Develop comprehensive risk mitigation plan")
        
        if 'red_line_violation' in concern_types:
            modifications.append("Complete redesign required - consult ethics board")
        
        # Generic modifications based on ethical scores
        modifications.extend([
            "Conduct thorough bias and fairness audit",
            "Implement stakeholder feedback mechanisms",
            "Develop clear governance structure",
            "Create monitoring and evaluation framework",
            "Establish transparent reporting procedures"
        ])
        
        # Remove duplicates and return top 5
        seen = set()
        unique_mods = []
        for mod in modifications:
            if mod not in seen:
                seen.add(mod)
                unique_mods.append(mod)
        
        return unique_mods[:5]
    
    def _suggest_alternatives(self, proposal: ResearchProposal,
                            concerns: List[EthicalConcern]) -> List[str]:
        """Suggest alternative approaches."""
        alternatives = []
        
        concern_types = set(c.concern_type for c in concerns)
        
        if 'red_flag_surveillance' in concern_types or any('surveillance' in ct for ct in concern_types):
            alternatives.append(
                "Use privacy-preserving analytics and aggregated data instead of individual surveillance"
            )
        
        if 'red_flag_weapons' in concern_types or any('weapons' in ct for ct in concern_types):
            alternatives.append(
                "Focus on defensive capabilities and non-lethal applications"
            )
        
        if 'red_flag_manipulation' in concern_types or any('manipulation' in ct for ct in concern_types):
            alternatives.append(
                "Design for transparency and user empowerment instead of behavior manipulation"
            )
        
        if proposal.domain == ResearchDomain.AI_ML:
            alternatives.append(
                "Consider interpretable AI approaches for high-stakes decisions"
            )
            alternatives.append(
                "Explore federated learning for privacy preservation"
            )
        
        if proposal.domain == ResearchDomain.BIOTECH:
            alternatives.append(
                "Consider in-vitro models instead of animal testing"
            )
            alternatives.append(
                "Explore non-genetic therapeutic approaches"
            )
        
        return alternatives[:3]  # Top 3
    
    def _determine_oversight(self, risk: RiskLevel,
                           proposal: ResearchProposal) -> List[str]:
        """Determine required oversight."""
        oversight = []
        
        required = self.config.get('required_oversight', {})
        
        if risk in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            oversight.extend(required.get('critical', [
                "Independent ethics board review",
                "External expert consultation",
                "Quarterly ethics audits"
            ]))
        
        if risk in [RiskLevel.HIGH, RiskLevel.MEDIUM]:
            oversight.extend(required.get('high', [
                "Institutional review board approval",
                "Regular progress reviews"
            ]))
        
        if proposal.domain in [ResearchDomain.BIOTECH, ResearchDomain.AI_ML]:
            oversight.append("Domain-specific regulatory compliance")
        
        if proposal.funding_source and 'military' in proposal.funding_source.lower():
            oversight.append("Additional oversight due to military funding")
        
        return list(set(oversight))  # Unieke waarden
    
    def _determine_stakeholder_engagement(self, proposal: ResearchProposal) -> List[str]:
        """Determine stakeholder engagement requirements."""
        engagement = set()
        
        for stakeholder in proposal.stakeholders:
            stakeholder_lower = stakeholder.lower()
            
            if 'public' in stakeholder_lower or 'community' in stakeholder_lower:
                engagement.add("Public consultation and feedback process")
            if 'patient' in stakeholder_lower:
                engagement.add("Patient advocacy group participation")
            if any(v in stakeholder_lower for v in ['children', 'elderly', 'disabled', 'vulnerable']):
                engagement.add("Independent advocacy and safeguards")
        
        engagement.add("Regular stakeholder updates")
        engagement.add("Feedback mechanism for affected communities")
        
        return list(engagement)
    
    def _determine_monitoring(self, risk: RiskLevel) -> List[str]:
        """Determine monitoring requirements."""
        monitoring = []
        
        if risk == RiskLevel.CRITICAL:
            monitoring.extend([
                "Real-time monitoring with immediate escalation",
                "Weekly ethics reports",
                "Independent audits monthly",
                "Public transparency dashboard"
            ])
        elif risk == RiskLevel.HIGH:
            monitoring.extend([
                "Weekly progress monitoring",
                "Monthly ethics reviews",
                "Quarterly independent audits",
                "Semi-annual public reports"
            ])
        elif risk == RiskLevel.MEDIUM:
            monitoring.extend([
                "Bi-weekly progress reports",
                "Quarterly ethics reviews",
                "Annual independent audit"
            ])
        else:
            monitoring.append("Standard project monitoring")
        
        return monitoring
    
    def _print_evaluation_summary(self, evaluation: EthicalEvaluation):
        """Print evaluation summary."""
        print(f"\n{'='*80}")
        print(f"ETHICAL EVALUATION SUMMARY")
        print(f"{'='*80}")
        print(f"\n📊 Ethical Scores:")
        print(f"   Harm Minimization: {evaluation.harm_score:.2f}")
        print(f"   Fairness:          {evaluation.fairness_score:.2f}")
        print(f"   Sustainability:    {evaluation.sustainability_score:.2f}")
        print(f"   Autonomy:          {evaluation.autonomy_score:.2f}")
        print(f"   → Aggregate:       {evaluation.aggregate_score:.2f}")
        
        print(f"\n⚠️ Risk Level: {evaluation.overall_risk.value.upper()}")
        print(f"\n💡 Recommendation: {evaluation.recommendation}")
        
        if evaluation.concerns:
            print(f"\n🚨 Concerns ({len(evaluation.concerns)}):")
            for concern in evaluation.concerns[:3]:  # Top 3
                print(f"   - {concern.description}")
        
        if evaluation.modifications:
            print(f"\n✏️ Suggested Modifications:")
            for mod in evaluation.modifications[:3]:  # Top 3
                print(f"   • {mod}")
        
        if evaluation.alternatives:
            print(f"\n🔄 Alternatives:")
            for alt in evaluation.alternatives[:2]:
                print(f"   • {alt}")
        
        print(f"\n⏱️  Processing time: {evaluation.processing_time_ms:.1f}ms")
        print(f"\n{'='*80}\n")
    
    # ========================================================================
    # BATCH EVALUATION
    # ========================================================================
    
    def evaluate_proposals(self, proposals: List[ResearchProposal]) -> List[EthicalEvaluation]:
        """
        Evaluate multiple proposals in batch.
        
        Args:
            proposals: List of proposals to evaluate
            
        Returns:
            List of evaluations
        """
        logger.info(f"📦 Batch evaluating {len(proposals)} proposals")
        
        evaluations = []
        for i, proposal in enumerate(proposals):
            logger.info(f"   [{i+1}/{len(proposals)}] {proposal.title[:50]}...")
            eval_result = self.evaluate_proposal(proposal)
            evaluations.append(eval_result)
        
        return evaluations
    
    # ========================================================================
    # REPORTING & EXPORT
    # ========================================================================
    
    def export_evaluation(self, evaluation: EthicalEvaluation,
                         output_file: str):
        """Export evaluation to JSON."""
        report = {
            'evaluation_id': evaluation.id,
            'proposal': {
                'id': evaluation.proposal.id,
                'title': evaluation.proposal.title,
                'description': evaluation.proposal.description,
                'domain': evaluation.proposal.domain.value,
                'domain_id': evaluation.proposal.domain.id,
                'objectives': evaluation.proposal.objectives,
                'methods': evaluation.proposal.methods,
                'potential_applications': evaluation.proposal.potential_applications,
                'stakeholders': evaluation.proposal.stakeholders,
                'funding_source': evaluation.proposal.funding_source,
                'metadata': evaluation.proposal.metadata
            },
            'timestamp': evaluation.timestamp.isoformat(),
            'processing_time_ms': evaluation.processing_time_ms,
            'scores': {
                'harm': evaluation.harm_score,
                'fairness': evaluation.fairness_score,
                'sustainability': evaluation.sustainability_score,
                'autonomy': evaluation.autonomy_score,
                'aggregate': evaluation.aggregate_score
            },
            'risk_level': evaluation.overall_risk.value,
            'recommendation': evaluation.recommendation,
            'violation_detected': evaluation.violation_detected,
            'concerns': [
                {
                    'id': c.id,
                    'type': c.concern_type,
                    'severity': c.severity.value,
                    'description': c.description,
                    'affected_stakeholders': c.affected_stakeholders,
                    'mitigation': c.mitigation_strategies
                }
                for c in evaluation.concerns
            ],
            'modifications': evaluation.modifications,
            'alternatives': evaluation.alternatives,
            'governance': {
                'oversight': evaluation.required_oversight,
                'engagement': evaluation.stakeholder_engagement,
                'monitoring': evaluation.monitoring_requirements
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Evaluation exported to: {output_file}")
    
    def generate_ethics_report(self, output_file: str = "ethics_report.json") -> Dict:
        """Generate comprehensive ethics report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'uptime_seconds': time.time() - self.metrics['start_time'],
            'statistics': {
                'total_evaluations': self.metrics['total_evaluations'],
                'total_violations': self.metrics['total_violations'],
                'total_concerns': self.metrics['total_concerns'],
                'avg_aggregate_score': float(self.metrics['avg_aggregate_score']),
                'avg_processing_time_ms': float(self.metrics['avg_processing_time'])
            },
            'recommendations': dict(self.metrics['recommendations']),
            'risk_distribution': dict(self.metrics['risk_distribution']),
            'evaluations': [e.to_dict() for e in self.evaluations[-50:]],  # Last 50
            'domain_breakdown': {
                domain: len(evaluations)
                for domain, evaluations in self.evaluations_by_domain.items()
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Ethics report exported to: {output_file}")
        
        return report
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return {
            'total_evaluations': self.metrics['total_evaluations'],
            'total_violations': self.metrics['total_violations'],
            'avg_aggregate_score': float(self.metrics['avg_aggregate_score']),
            'avg_processing_time_ms': float(self.metrics['avg_processing_time']),
            'recommendations': dict(self.metrics['recommendations']),
            'risk_distribution': dict(self.metrics['risk_distribution']),
            'domains_covered': len(self.evaluations_by_domain),
            'cache_size': self.get_domain_guidelines.cache_info().currsize,
            'cache_hits': self.get_domain_guidelines.cache_info().hits,
            'cache_misses': self.get_domain_guidelines.cache_info().misses
        }


# ========================================================================
# DEMO
# ========================================================================

def demo():
    """Demonstrate Ethical Research Assistant."""
    print("\n" + "="*80)
    print("⚖️ ETHICAL RESEARCH ASSISTANT DEMO")
    print("="*80)
    
    # Mock Layer 15
    class MockLayer15:
        def evaluate_action(self, action):
            return {
                'harm_minimization': 0.8,
                'fairness': 0.7,
                'sustainability': 0.9,
                'autonomy': 0.6,
                'aggregate': 0.75
            }
        
        def detect_ethical_violation(self, action):
            return None
        
        def attribute_responsibility(self, action_id, agents, outcome):
            pass
    
    # Create assistant
    assistant = EthicalResearchAssistant(layer15=MockLayer15())
    
    # Create test proposal
    proposal = ResearchProposal(
        title="AI-Powered Facial Recognition for Public Safety",
        description="Developing an AI system to identify individuals in public spaces",
        domain=ResearchDomain.SURVEILLANCE,
        objectives=["Real-time identification", "Database matching"],
        methods=["Deep learning", "Computer vision"],
        potential_applications=["Law enforcement", "Security"],
        stakeholders=["Public", "Law enforcement", "Privacy advocates"],
        funding_source="Government grant"
    )
    
    # Evaluate
    evaluation = assistant.evaluate_proposal(proposal)
    
    # Show stats
    print(f"\n📊 Stats: {assistant.get_stats()}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    demo()