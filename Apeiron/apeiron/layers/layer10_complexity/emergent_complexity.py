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

class Layer10_EmergentComplexity:
    """Layer 10: Emergent Complexity and Systemic Self-Organization."""
    def __init__(self, layer9: Layer9_OntologicalCreation):
        self.layer9 = layer9
        self.complexity_metrics: Dict[str, float] = {}
        self.history: List[Dict] = []
        
    def measure_complexity(self) -> Dict[str, float]:
        """Measure emergent complexity in the system."""
        # Number of ontologies
        self.complexity_metrics["ontology_count"] = len(self.layer9.ontologies)
        
        # Temporele metrics
        if self.layer9.ontologies:
            coherenties = [o.get('temporele_coherentie', 0.0) for o in self.layer9.ontologies]
            self.complexity_metrics["avg_temporele_coherentie"] = float(np.mean(coherenties))
            
            entropieen = [o.get('temporele_entropie', 0.0) for o in self.layer9.ontologies]
            self.complexity_metrics["temporele_diversiteit"] = float(np.std(entropieen)) if len(entropieen) > 1 else 0.0
        
        # Coherence stability
        if hasattr(self.layer9.layer8, 'visualisatie_buffer') and len(self.layer9.layer8.visualisatie_buffer) > 1:
            coherences = [s['coherence'] for s in self.layer9.layer8.visualisatie_buffer]
            self.complexity_metrics["coherence_stability"] = 1.0 - float(np.std(coherences))
        
        # Add to history
        self.history.append({
            'timestamp': time.time(),
            'metrics': self.complexity_metrics.copy()
        })
        
        # Keep only last 100
        if len(self.history) > 100:
            self.history.pop(0)
        
        logger.info(f"Layer 10: Complexity metrics = {self.complexity_metrics}")
        return self.complexity_metrics
    
    def get_complexity_trend(self) -> Dict[str, float]:
        """Get trend in complexity metrics."""
        if len(self.history) < 2:
            return {}
        
        trends = {}
        first = self.history[0]['metrics']
        last = self.history[-1]['metrics']
        
        for key in set(first) & set(last):
            if first[key] != 0:
                trends[f"{key}_trend"] = (last[key] - first[key]) / first[key]
        
        return trends
    
    def get_stats(self) -> Dict[str, Any]:
        """Get layer statistics."""
        return {
            'metrics': self.complexity_metrics,
            'history_length': len(self.history),
            'trends': self.get_complexity_trend()
        }


# ============================================================================
# INTEGRATIE MET LAGEN 11-17 (indien beschikbaar)
# ============================================================================
