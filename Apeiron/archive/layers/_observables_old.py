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

class Layer1_Observables:
    """
    Layer 1: Foundational Observables
    The elementary field of observables - discrete, dimensionless entities.
    """
    def __init__(self):
        self.observables: Dict[str, Observable] = {}
        self.observation_count = 0
        self.metrics = {
            'total_recorded': 0,
            'unique_ids': 0
        }
        
    def record(self, obs_id: str, value: Any, context: Optional[Dict] = None, 
               metadata: Optional[Dict] = None) -> Observable:
        """Record a new observable in the system."""
        obs = Observable(
            id=obs_id,
            value=value,
            context=context or {},
            timestamp=self.observation_count,
            metadata=metadata or {}
        )
        self.observables[obs_id] = obs
        self.observation_count += 1
        self.metrics['total_recorded'] += 1
        self.metrics['unique_ids'] = len(self.observables)
        
        logger.debug(f"Layer 1: Recorded observable {obs_id}")
        return obs
    
    def get_observables(self) -> List[Observable]:
        """Retrieve all observables."""
        return list(self.observables.values())
    
    def get_observable(self, obs_id: str) -> Optional[Observable]:
        """Retrieve a specific observable by ID."""
        return self.observables.get(obs_id)
    
    def clear(self):
        """Clear all observables (for testing)."""
        self.observables.clear()
        self.observation_count = 0
        self.metrics['total_recorded'] = 0
        self.metrics['unique_ids'] = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get layer statistics."""
        return {
            'metrics': self.metrics,
            'observables': len(self.observables),
            'last_id': self.observation_count
        }


# ============================================================================
# LAYER 2: RELATIONAL EMERGENCE (UITGEBREID)
# ============================================================================

@dataclass