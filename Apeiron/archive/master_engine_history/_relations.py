import
from
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
from

class Layer2_Relations:
    """
    Layer 2: Relational Emergence
    Establishes initial relational structures among observables.
    """
    def __init__(self, layer1: Layer1_Observables):
        self.layer1 = layer1
        self.relations: List[Relation] = []
        self.adjacency: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.metrics = {
            'total_relations': 0,
            'avg_strength': 0.0,
            'max_strength': 0.0
        }
        
    def compute_relations(self, threshold: float = 0.1):
        """
        Detect emergent relations between observables.
        Uses correlation and co-occurrence patterns.
        """
        observables = self.layer1.get_observables()
        self.relations = []
        self.adjacency.clear()
        
        strengths = []
        
        for i, obs1 in enumerate(observables):
            for obs2 in observables[i+1:]:
                # Simple correlation based on value similarity
                strength = self._compute_correlation(obs1, obs2)
                strengths.append(strength)
                
                if strength >= threshold:
                    relation = Relation(
                        source=obs1.id,
                        target=obs2.id,
                        strength=strength
                    )
                    self.relations.append(relation)
                    self.adjacency[obs1.id][obs2.id] = strength
                    self.adjacency[obs2.id][obs1.id] = strength
        
        # Update metrics
        self.metrics['total_relations'] = len(self.relations)
        if strengths:
            self.metrics['avg_strength'] = float(np.mean(strengths))
            self.metrics['max_strength'] = float(np.max(strengths))
        
        logger.info(f"Layer 2: Detected {len(self.relations)} relations")
        return self.relations
    
    def _compute_correlation(self, obs1: Observable, obs2: Observable) -> float:
        """Compute correlation strength between two observables."""
        try:
            if isinstance(obs1.value, (int, float)) and isinstance(obs2.value, (int, float)):
                # Normalize to [0, 1]
                diff = abs(obs1.value - obs2.value)
                max_val = max(abs(obs1.value), abs(obs2.value), 1.0)
                return max(0.0, 1.0 - (diff / max_val))
            return 0.0
        except:
            return 0.0
    
    def get_relations_for(self, obs_id: str) -> List[Relation]:
        """Get all relations involving a specific observable."""
        return [r for r in self.relations if r.source == obs_id or r.target == obs_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get layer statistics."""
        return {
            'metrics': self.metrics,
            'relations': len(self.relations),
            'density': len(self.relations) / (len(self.layer1.observables) ** 2 + 1)
        }


# ============================================================================
# LAYER 3: FUNCTIONAL EMERGENCE (UITGEBREID)
# ============================================================================

@dataclass