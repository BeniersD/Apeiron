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

class Layer3_Functions:
    """
    Layer 3: Functional Emergence
    Identifies functional entities from relational patterns.
    """
    def __init__(self, layer2: Layer2_Relations):
        self.layer2 = layer2
        self.functional_entities: List[FunctionalEntity] = []
        self.metrics = {
            'total_entities': 0,
            'avg_coherence': 0.0,
            'max_coherence': 0.0,
            'min_coherence': 1.0
        }
        
    def identify_functions(self, min_cluster_size: int = 2):
        """Identify functional clusters using graph analysis."""
        self.functional_entities = []
        
        # Build graph from relations
        G = nx.Graph()
        for relation in self.layer2.relations:
            G.add_edge(relation.source, relation.target, weight=relation.strength)
        
        # Find communities/clusters
        if len(G.nodes()) > 0:
            try:
                communities = nx.community.greedy_modularity_communities(G)
            except:
                # Fallback voor kleine grafen
                communities = [set(G.nodes())]
            
            coherences = []
            for idx, community in enumerate(communities):
                if len(community) >= min_cluster_size:
                    # Compute internal coherence
                    coherence = self._compute_coherence(community, G)
                    coherences.append(coherence)
                    
                    entity = FunctionalEntity(
                        id=f"func_{idx}_{int(time.time())}",
                        observables=set(community),
                        internal_coherence=coherence
                    )
                    self.functional_entities.append(entity)
            
            # Update metrics
            self.metrics['total_entities'] = len(self.functional_entities)
            if coherences:
                self.metrics['avg_coherence'] = float(np.mean(coherences))
                self.metrics['max_coherence'] = float(np.max(coherences))
                self.metrics['min_coherence'] = float(np.min(coherences))
        
        logger.info(f"Layer 3: Identified {len(self.functional_entities)} functional entities")
        return self.functional_entities
    
    def _compute_coherence(self, community: Set[str], graph: nx.Graph) -> float:
        """Compute internal coherence of a functional entity."""
        if len(community) < 2:
            return 1.0
        
        edges_in_community = 0
        total_weight = 0.0
        
        for node1 in community:
            for node2 in community:
                if node1 != node2 and graph.has_edge(node1, node2):
                    edges_in_community += 1
                    total_weight += graph[node1][node2]['weight']
        
        max_edges = len(community) * (len(community) - 1) / 2
        if max_edges == 0:
            return 0.0
        
        connectivity = edges_in_community / max_edges
        avg_weight = total_weight / max(edges_in_community, 1)
        
        return connectivity * avg_weight
    
    def get_entity(self, entity_id: str) -> Optional[FunctionalEntity]:
        """Get a specific functional entity by ID."""
        for entity in self.functional_entities:
            if entity.id == entity_id:
                return entity
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get layer statistics."""
        return {
            'metrics': self.metrics,
            'entities': len(self.functional_entities),
            'total_observables': sum(len(e.observables) for e in self.functional_entities)
        }


# ============================================================================
# LAYER 4: DYNAMIC ADAPTATION (UITGEBREID)
# ============================================================================

@dataclass