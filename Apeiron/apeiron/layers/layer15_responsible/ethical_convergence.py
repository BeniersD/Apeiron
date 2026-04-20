import
from
from
from
import
from
import
import
import
import
import
import
import
from
from

class Layer15_EthicalConvergence:
    """
    Layer 15: Ethical Convergence and Responsibility in Distributed Systems
    
    Implements distributed responsibility, multi-stakeholder ethics,
    and convergence of moral logics across heterogeneous agents.
    
    Uitbreidingen:
    - Principle thresholds
    - Violation severity
    - Convergence tracking
    - Export functionaliteit
    """
    
    def __init__(self, layer14, config: Optional[Dict] = None):
        self.layer14 = layer14
        self.ethical_principles: Dict[str, EthicalPrinciple] = {}
        self.responsibility_ledger: List[ResponsibilityTrace] = []
        self.ethical_violations: List[Dict] = []
        self.convergence_history: List[float] = []
        
        # Metrics
        self.metrics = {
            'actions_evaluated': 0,
            'violations_detected': 0,
            'responsibilities_attributed': 0,
            'avg_convergence': 0.0
        }
        
        # Configuratie
        self.config = config or {}
        self.violation_threshold = self.config.get('violation_threshold', 0.3)
        
        self._initialize_ethical_framework()
        
    def _initialize_ethical_framework(self):
        """Initialize core ethical principles."""
        
        self.ethical_principles['harm_minimization'] = EthicalPrinciple(
            id='harm_minimization',
            description='Minimize harm to individuals and collectives',
            weight=1.0,
            domain='individual',
            threshold=0.3
        )
        
        self.ethical_principles['fairness'] = EthicalPrinciple(
            id='fairness',
            description='Ensure equitable distribution of resources and opportunities',
            weight=0.9,
            domain='collective',
            threshold=0.3
        )
        
        self.ethical_principles['sustainability'] = EthicalPrinciple(
            id='sustainability',
            description='Preserve long-term viability of systems',
            weight=0.95,
            domain='planetary',
            threshold=0.3
        )
        
        self.ethical_principles['autonomy'] = EthicalPrinciple(
            id='autonomy',
            description='Respect agent self-determination',
            weight=0.85,
            domain='individual',
            threshold=0.3
        )
        
        logger.info(f"Layer 15: Initialized {len(self.ethical_principles)} ethical principles")
    
    def evaluate_action(self, action: Dict[str, Any]) -> Dict[str, float]:
        """
        Evaluate an action against all ethical principles.
        Returns scores for each principle.
        """
        self.metrics['actions_evaluated'] += 1
        
        scores = {}
        
        for principle_id, principle in self.ethical_principles.items():
            score = self._score_against_principle(action, principle)
            scores[principle_id] = score
        
        # Weighted aggregate
        weighted_score = sum(scores[pid] * p.weight 
                           for pid, p in self.ethical_principles.items())
        total_weight = sum(p.weight for p in self.ethical_principles.values())
        weighted_score /= total_weight if total_weight > 0 else 1
        
        scores['aggregate'] = weighted_score
        
        return scores
    
    def _score_against_principle(self, action: Dict, principle: EthicalPrinciple) -> float:
        """Score an action against a specific ethical principle."""
        
        if principle.id == 'harm_minimization':
            # Check if action causes harm
            harm_caused = action.get('harm_level', 0.0)
            return max(0, 1.0 - harm_caused)
        
        elif principle.id == 'fairness':
            # Check resource distribution
            distribution = action.get('resource_distribution', [0.5, 0.5])
            variance = np.var(distribution)
            return max(0, 1.0 - variance)
        
        elif principle.id == 'sustainability':
            # Check long-term impact
            sustainability = action.get('sustainability_impact', 0.5)
            return float(sustainability)
        
        elif principle.id == 'autonomy':
            # Check if action respects autonomy
            autonomy_preserved = action.get('autonomy_preserved', True)
            return 1.0 if autonomy_preserved else 0.0
        
        return 0.5  # Default neutral score
    
    def attribute_responsibility(self, action_id: str, agents: List[str], 
                                outcome: Dict[str, float]) -> ResponsibilityTrace:
        """
        Attribute responsibility for distributed actions.
        Implements distributed accountability across multiple agents.
        """
        self.metrics['responsibilities_attributed'] += 1
        
        # Compute contribution weights
        contributions = {}
        for agent in agents:
            # Simplified - in practice would track actual causal contributions
            contributions[agent] = 1.0 / len(agents)
        
        # Check for violations
        violation = self.detect_ethical_violation({'outcome': outcome})
        
        trace = ResponsibilityTrace(
            action_id=action_id,
            agents=agents,
            contributions=contributions,
            outcomes=outcome,
            timestamp=len(self.responsibility_ledger),
            violation=violation
        )
        
        self.responsibility_ledger.append(trace)
        
        logger.debug(f"Layer 15: Attributed responsibility for action '{action_id}' "
                    f"across {len(agents)} agents")
        
        return trace
    
    def detect_ethical_violation(self, action: Dict) -> Optional[Dict]:
        """Detect if an action violates ethical principles."""
        scores = self.evaluate_action(action)
        
        # Check if any principle severely violated
        for principle_id, score in scores.items():
            if principle_id != 'aggregate':
                principle = self.ethical_principles.get(principle_id)
                threshold = principle.threshold if principle else self.violation_threshold
                
                if score < threshold:
                    severity = 'high' if score < threshold * 0.5 else 'medium'
                    
                    violation = {
                        'action': action,
                        'violated_principle': principle_id,
                        'score': score,
                        'threshold': threshold,
                        'severity': severity,
                        'timestamp': time.time()
                    }
                    
                    self.ethical_violations.append(violation)
                    self.metrics['violations_detected'] += 1
                    
                    logger.warning(f"Layer 15: Ethical violation detected - {principle_id} "
                                 f"(score: {score:.2f}, threshold: {threshold:.2f})")
                    return violation
        
        return None
    
    def compute_ethical_convergence(self, agent_values: List[Dict[str, float]]) -> float:
        """
        Compute convergence of ethical values across agents.
        Measures alignment of moral frameworks.
        """
        if len(agent_values) < 2:
            return 1.0
        
        # Compute pairwise value similarity
        similarities = []
        for i, values_a in enumerate(agent_values):
            for values_b in agent_values[i+1:]:
                # Compare value vectors
                keys = set(values_a.keys()).union(values_b.keys())
                vec_a = np.array([values_a.get(k, 0.5) for k in keys])
                vec_b = np.array([values_b.get(k, 0.5) for k in keys])
                
                similarity = 1.0 - cosine(vec_a, vec_b)
                similarities.append(similarity)
        
        convergence = np.mean(similarities) if similarities else 1.0
        self.convergence_history.append(convergence)
        
        # Update average
        n = len(self.convergence_history)
        self.metrics['avg_convergence'] = (self.metrics['avg_convergence'] * (n-1) + convergence) / n
        
        logger.info(f"Layer 15: Ethical convergence = {convergence:.3f}")
        return convergence
    
    def apply_ethical_constraint(self, world_id: str, constraint_type: str):
        """
        Apply ethical constraints to world evolution.
        Operationalizes normative principles.
        """
        world = self.layer14.worlds.get(world_id)
        if not world:
            logger.error(f"World {world_id} not found")
            return
        
        if constraint_type == 'distributive_justice':
            # Redistribute resources more equitably
            if not world.agent_population:
                return
            
            total_energy = sum(a['energy'] for a in world.agent_population)
            fair_share = total_energy / len(world.agent_population)
            
            for agent in world.agent_population:
                if agent['energy'] < fair_share * 0.7:
                    # Transfer from world resources
                    supplement = min(fair_share * 0.3, world.resource_state['energy'] * 0.1)
                    agent['energy'] += supplement
                    world.resource_state['energy'] -= supplement
            
            logger.info(f"Layer 15: Applied distributive justice to world '{world_id}'")
    
    def get_stats(self) -> Dict[str, Any]:
        """Haal statistieken op."""
        return {
            'metrics': self.metrics,
            'principles': [
                {
                    'id': p.id,
                    'weight': p.weight,
                    'domain': p.domain,
                    'threshold': p.threshold
                }
                for p in self.ethical_principles.values()
            ],
            'recent_violations': self.ethical_violations[-10:],
            'convergence_trend': self.convergence_history[-20:] if self.convergence_history else []
        }


# ============================================================================
# LAYER 16: DYNAMISCHE STROMINGEN (UITGEBREID)
# ============================================================================

@dataclass