"""
CROSS-DOMAIN SYNTHESIS ENGINE - V12 COMPATIBLE
Find non-obvious connections between disparate research domains
Uses Layer 12 ontological reconciliation + Layer 13 novelty generation

Uitbreidingen:
- Volledige V12 integratie
- Logging en metrics
- Configuratie via bestand
- Hardware acceleration opties
- Batch processing
"""

import numpy as np
from typing import Dict, List, Tuple, Set, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from collections.abc import Iterable
import networkx as nx
from scipy.spatial.distance import cosine
import json
import logging
import time
import hashlib
from datetime import datetime
import os

# Import your layers
from layers_11_to_17 import (
    Ontology,
    Layer12_Reconciliation,
    Layer13_Ontogenesis,
    NovelStructure
)

# Optional V12 imports
try:
    from resonance_scout import ResonanceScout, StilleStroming
    from hardware_exceptions import handle_hardware_errors
    from hardware_factory import get_best_backend
    V12_AVAILABLE = True
except ImportError:
    V12_AVAILABLE = False
    # Fallback decorator
    def handle_hardware_errors(default_return=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"⚠️ Error: {e}")
                    return default_return
            return wrapper
        return decorator

logger = logging.getLogger(__name__)


@dataclass
class DomainProfile:
    """Represents a research domain with its characteristics."""
    name: str
    papers: List[Dict[str, Any]]
    key_concepts: Set[str]
    methodologies: Set[str]
    ontology: Ontology
    citation_network: nx.Graph
    temporal_trends: Dict[str, float]
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)


@dataclass
class BridgeConcept:
    """A concept that bridges two domains."""
    concept: str
    domain_a: str
    domain_b: str
    strength: float
    context_a: str
    context_b: str
    transformation_path: List[str]
    discovered_at: float = field(default_factory=time.time)
    confidence: float = 0.8
    
    @property
    def id(self) -> str:
        """Uniek ID voor deze bridge."""
        hash_input = f"{self.domain_a}{self.domain_b}{self.concept}".encode()
        return f"BRIDGE_{hashlib.md5(hash_input).hexdigest()[:8].upper()}"


@dataclass
class NovelHypothesis:
    """A novel hypothesis generated from cross-domain synthesis."""
    id: str
    description: str
    source_domains: List[str]
    bridge_concepts: List[str]
    novelty_score: float
    feasibility_score: float
    impact_potential: float
    supporting_evidence: List[str]
    required_resources: List[str]
    testability_score: float
    created_at: float = field(default_factory=time.time)
    status: str = "generated"  # generated, validated, rejected, implemented


class CrossDomainSynthesizer:
    """
    The killer feature: Find non-obvious connections between research domains.
    
    This uses Layer 12 to reconcile ontologies and Layer 13 to generate
    genuinely novel hypotheses from the bridges.
    
    V12 enhancements:
    - Integratie met ResonanceScout voor interferentie detectie
    - Hardware acceleration opties
    - Metrics tracking
    - Configuratie management
    - Batch processing
    """
    
    def __init__(self, layer12, layer13, memory, 
                 config_path: Optional[str] = None,
                 use_hardware: bool = False):
        """
        Initialize Cross-Domain Synthesizer.
        
        Args:
            layer12: Layer12_Reconciliation instance
            layer13: Layer13_Ontogenesis instance
            memory: ChromaDB memory instance
            config_path: Optional path to config file
            use_hardware: Use hardware acceleration if available
        """
        self.layer12 = layer12  # Layer12_Reconciliation
        self.layer13 = layer13  # Layer13_Ontogenesis
        self.memory = memory    # ChromaDB memory
        
        # Logging
        self.logger = logging.getLogger('CrossDomainSynthesis')
        
        # Hardware (optional)
        self.use_hardware = use_hardware
        self.hardware = None
        if use_hardware and V12_AVAILABLE:
            try:
                self.hardware = get_best_backend()
                self.logger.info(f"⚡ Hardware: {self.hardware.get_info()}")
            except Exception as e:
                self.logger.warning(f"⚠️ Hardware init failed: {e}")
        
        # Load configuration
        self._load_config(config_path)
        
        # Domain profiles
        self.domains: Dict[str, DomainProfile] = {}
        
        # Discovered bridges
        self.bridges: List[BridgeConcept] = []
        self.bridges_by_domain: Dict[str, List[BridgeConcept]] = defaultdict(list)
        
        # Generated hypotheses
        self.hypotheses: List[NovelHypothesis] = []
        self.hypotheses_by_domain: Dict[str, List[NovelHypothesis]] = defaultdict(list)
        
        # Bridge discovery history
        self.bridge_history: List[Dict] = []
        
        # Metrics tracking
        self.metrics = {
            'domains_profiled': 0,
            'bridges_found': 0,
            'hypotheses_generated': 0,
            'avg_bridge_strength': 0.0,
            'avg_novelty_score': 0.0,
            'total_processing_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Cache voor concept embeddings
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.max_cache_size = 100
        
        self.logger.info("="*80)
        self.logger.info("🌉 CROSS-DOMAIN SYNTHESIS ENGINE V12")
        self.logger.info("="*80)
        self.logger.info(f"Hardware: {'✓' if self.hardware else '✗'}")
        self.logger.info(f"Config: {self.config}")
        self.logger.info("="*80)
    
    def _load_config(self, config_path: Optional[str] = None):
        """Load configuration from file."""
        # Default configuration
        self.config = {
            'min_bridge_strength': 0.3,
            'max_concepts_per_domain': 20,
            'use_embeddings': True,
            'embedding_cache_size': 100,
            'batch_size': 5,
            'max_hypotheses_per_pair': 5,
            'similarity_threshold': 0.7,
            'include_methodologies': True,
            'include_temporal': True
        }
        
        if config_path and os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                synthesis_config = config.get('cross_domain_synthesis', {})
                self.config.update(synthesis_config)
                self.logger.info(f"📋 Config loaded from: {config_path}")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load config: {e}")
        
        # Update thresholds
        self.min_bridge_strength = self.config['min_bridge_strength']
        self.max_concepts_per_domain = self.config['max_concepts_per_domain']
        self.batch_size = self.config['batch_size']
    
    # ========================================================================
    # DOMAIN PROFILING
    # ========================================================================
    
    @handle_hardware_errors(default_return=None)
    def build_domain_profile(self, domain_name: str, 
                            papers: List[Dict]) -> DomainProfile:
        """
        Build a comprehensive profile of a research domain.
        
        Args:
            domain_name: Name of the domain (e.g., "Quantum Computing")
            papers: List of papers from that domain
            
        Returns:
            DomainProfile with extracted characteristics
        """
        start_time = time.time()
        
        self.logger.info(f"\n🔬 Building profile for domain: {domain_name}")
        self.logger.info(f"   Papers: {len(papers)}")
        
        # Extract key concepts from papers
        key_concepts = self._extract_concepts(papers)
        
        # Extract methodologies
        methodologies = self._extract_methodologies(papers)
        
        # Build ontology for this domain
        ontology = self._build_domain_ontology(domain_name, papers, key_concepts)
        
        # Build citation network
        citation_network = self._build_citation_network(papers)
        
        # Analyze temporal trends
        temporal_trends = self._analyze_temporal_trends(papers)
        
        profile = DomainProfile(
            name=domain_name,
            papers=papers,
            key_concepts=key_concepts,
            methodologies=methodologies,
            ontology=ontology,
            citation_network=citation_network,
            temporal_trends=temporal_trends
        )
        
        self.domains[domain_name] = profile
        self.metrics['domains_profiled'] += 1
        
        processing_time = time.time() - start_time
        self.metrics['total_processing_time'] += processing_time
        
        self.logger.info(f"  ✓ Extracted {len(key_concepts)} key concepts")
        self.logger.info(f"  ✓ Identified {len(methodologies)} methodologies")
        self.logger.info(f"  ✓ Built ontology with {len(ontology.entities)} entities")
        self.logger.info(f"  ⏱️  Time: {processing_time*1000:.1f}ms")
        
        return profile
    
    def _extract_concepts(self, papers: List[Dict]) -> Set[str]:
        """Extract key concepts from paper titles and abstracts."""
        concepts = set()
        word_freq = defaultdict(int)
        
        for paper in papers:
            # Extract from title
            title_words = [w.lower() for w in paper.get('title', '').split() 
                          if len(w) > 4]
            for w in title_words:
                word_freq[w] += 1
            
            # Extract from summary
            summary_words = [w.lower() for w in paper.get('summary', '').split() 
                           if len(w) > 5]
            for w in summary_words:
                word_freq[w] += 1
        
        # Take most frequent words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        concepts = {w for w, freq in sorted_words[:self.max_concepts_per_domain]}
        
        # Filter common stop words
        stop_words = {'using', 'based', 'approach', 'method', 'study', 
                     'analysis', 'results', 'paper', 'research', 'however',
                     'also', 'can', 'may', 'will', 'thus', 'therefore'}
        concepts = concepts - stop_words
        
        return concepts
    
    def _extract_methodologies(self, papers: List[Dict]) -> Set[str]:
        """Extract methodological approaches."""
        methodology_keywords = {
            'machine learning', 'deep learning', 'simulation', 'experiment',
            'theoretical', 'computational', 'statistical', 'optimization',
            'monte carlo', 'neural network', 'regression', 'classification',
            'clustering', 'reinforcement', 'supervised', 'unsupervised',
            'bayesian', 'maximum likelihood', 'gradient descent', 'backpropagation'
        }
        
        methodologies = set()
        
        for paper in papers:
            text = (paper.get('title', '') + ' ' + paper.get('summary', '')).lower()
            
            for method in methodology_keywords:
                if method in text:
                    methodologies.add(method)
        
        return methodologies
    
    def _build_domain_ontology(self, domain_name: str, papers: List[Dict],
                               concepts: Set[str]) -> Ontology:
        """Build an ontology representation of the domain."""
        
        # Create entities from concepts
        entities = set(list(concepts)[:self.max_concepts_per_domain])
        
        # Create relations based on co-occurrence
        relations = {}
        concept_list = list(entities)
        
        for i, c1 in enumerate(concept_list):
            for c2 in concept_list[i+1:]:
                # Check co-occurrence in papers
                co_occurrence = sum(
                    1 for p in papers 
                    if c1 in p.get('title', '').lower() + p.get('summary', '').lower()
                    and c2 in p.get('title', '').lower() + p.get('summary', '').lower()
                )
                
                if co_occurrence > 0:
                    strength = min(co_occurrence / len(papers), 1.0)
                    relations[(c1, c2)] = strength
        
        # Create worldview vector based on domain characteristics
        # Dimensions: [empirical, theoretical, computational, applied, fundamental]
        worldview = self._compute_domain_worldview(papers)
        
        ontology = Ontology(
            id=f"domain_{domain_name}_{int(time.time())}",
            entities=entities,
            relations=relations,
            axioms=[domain_name],
            worldview_vector=worldview
        )
        
        # Register with Layer 12
        self.layer12.register_ontology(ontology)
        
        return ontology
    
    def _compute_domain_worldview(self, papers: List[Dict]) -> np.ndarray:
        """Compute domain's worldview vector."""
        
        # Analyze papers to determine domain characteristics
        empirical_score = 0
        theoretical_score = 0
        computational_score = 0
        applied_score = 0
        fundamental_score = 0
        
        for paper in papers:
            text = (paper.get('title', '') + ' ' + paper.get('summary', '')).lower()
            
            # Empirical indicators
            if any(w in text for w in ['experiment', 'measurement', 'observation', 'data']):
                empirical_score += 1
            
            # Theoretical indicators
            if any(w in text for w in ['theorem', 'proof', 'theory', 'model']):
                theoretical_score += 1
            
            # Computational indicators
            if any(w in text for w in ['simulation', 'algorithm', 'computational']):
                computational_score += 1
            
            # Applied indicators
            if any(w in text for w in ['application', 'practical', 'implementation']):
                applied_score += 1
            
            # Fundamental indicators
            if any(w in text for w in ['fundamental', 'foundation', 'principle']):
                fundamental_score += 1
        
        # Normalize
        total = max(len(papers), 1)
        worldview = np.array([
            empirical_score / total,
            theoretical_score / total,
            computational_score / total,
            applied_score / total,
            fundamental_score / total
        ])
        
        return worldview
    
    def _build_citation_network(self, papers: List[Dict]) -> nx.Graph:
        """Build citation network (simplified - would need real citation data)."""
        G = nx.Graph()
        
        for paper in papers:
            paper_id = paper.get('id', paper.get('title', str(hash(paper.get('title', '')))))
            G.add_node(paper_id, title=paper.get('title', ''))
        
        return G
    
    def _analyze_temporal_trends(self, papers: List[Dict]) -> Dict[str, float]:
        """Analyze how concepts trend over time."""
        # Simplified - would need actual publication dates
        return {
            'recent_activity': 1.0,
            'growth_rate': 0.8,
            'stability': 0.7
        }
    
    # ========================================================================
    # BRIDGE DISCOVERY
    # ========================================================================
    
    @handle_hardware_errors(default_return=[])
    def find_bridges(self, domain_a: str, domain_b: str,
                    min_strength: Optional[float] = None) -> List[BridgeConcept]:
        """
        Find conceptual bridges between two domains.
        
        This is the CORE innovation - using Layer 12 reconciliation
        to find non-obvious connections.
        
        Args:
            domain_a: First domain name
            domain_b: Second domain name
            min_strength: Minimum bridge strength threshold (overrides config)
            
        Returns:
            List of discovered bridge concepts
        """
        start_time = time.time()
        
        if min_strength is None:
            min_strength = self.min_bridge_strength
        
        self.logger.info(f"\n🌉 Finding bridges: {domain_a} ↔ {domain_b}")
        self.logger.info(f"   Min strength: {min_strength}")
        
        if domain_a not in self.domains or domain_b not in self.domains:
            error_msg = f"Domain not profiled. Use build_domain_profile() first."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        profile_a = self.domains[domain_a]
        profile_b = self.domains[domain_b]
        
        # Step 1: Ontological reconciliation (Layer 12)
        self.logger.info("  📊 Reconciling ontologies...")
        bridge_ontology = self.layer12.reconcile([profile_a.ontology.id, 
                                                   profile_b.ontology.id])
        
        self.logger.info(f"  ✓ Bridge ontology coherence: {bridge_ontology.coherence_score:.3f}")
        
        # Step 2: Find shared concepts
        shared_concepts = profile_a.key_concepts.intersection(profile_b.key_concepts)
        self.logger.info(f"  ✓ Found {len(shared_concepts)} directly shared concepts")
        
        # Step 3: Find analogous concepts (semantic similarity)
        analogous_bridges = self._find_analogous_concepts(profile_a, profile_b)
        self.logger.info(f"  ✓ Found {len(analogous_bridges)} analogous concept pairs")
        
        # Step 4: Find methodological bridges
        method_bridges = set()
        if self.config.get('include_methodologies', True):
            method_bridges = self._find_methodological_bridges(profile_a, profile_b)
            self.logger.info(f"  ✓ Found {len(method_bridges)} methodological bridges")
        
        # Step 5: Create bridge concepts
        bridges = []
        
        # Direct bridges from shared concepts
        for concept in shared_concepts:
            bridge = BridgeConcept(
                concept=concept,
                domain_a=domain_a,
                domain_b=domain_b,
                strength=1.0,  # Maximum strength for direct match
                context_a=self._get_concept_context(concept, profile_a),
                context_b=self._get_concept_context(concept, profile_b),
                transformation_path=[concept],
                confidence=1.0
            )
            bridges.append(bridge)
        
        # Analogous bridges
        for (concept_a, concept_b, similarity) in analogous_bridges:
            if similarity >= min_strength:
                bridge = BridgeConcept(
                    concept=f"{concept_a} ≈ {concept_b}",
                    domain_a=domain_a,
                    domain_b=domain_b,
                    strength=similarity,
                    context_a=self._get_concept_context(concept_a, profile_a),
                    context_b=self._get_concept_context(concept_b, profile_b),
                    transformation_path=[concept_a, concept_b],
                    confidence=similarity
                )
                bridges.append(bridge)
        
        # Methodological bridges
        for method in method_bridges:
            bridge = BridgeConcept(
                concept=f"method:{method}",
                domain_a=domain_a,
                domain_b=domain_b,
                strength=0.8,
                context_a="methodology",
                context_b="methodology",
                transformation_path=[method],
                confidence=0.8
            )
            bridges.append(bridge)
        
        # Sort by strength
        bridges.sort(key=lambda b: b.strength, reverse=True)
        
        # Store bridges
        self.bridges.extend(bridges)
        self.bridges_by_domain[domain_a].extend(bridges)
        self.bridges_by_domain[domain_b].extend(bridges)
        
        # Update metrics
        self.metrics['bridges_found'] += len(bridges)
        if bridges:
            avg_strength = np.mean([b.strength for b in bridges])
            self.metrics['avg_bridge_strength'] = (
                (self.metrics['avg_bridge_strength'] * (self.metrics['bridges_found'] - len(bridges)) +
                 avg_strength * len(bridges)) / self.metrics['bridges_found']
            )
        
        # Record in history
        self.bridge_history.append({
            'domain_a': domain_a,
            'domain_b': domain_b,
            'bridges_found': len(bridges),
            'coherence': bridge_ontology.coherence_score,
            'strength': avg_strength if bridges else 0,
            'timestamp': time.time()
        })
        
        processing_time = time.time() - start_time
        self.metrics['total_processing_time'] += processing_time
        
        self.logger.info(f"\n✨ Total bridges discovered: {len(bridges)}")
        self.logger.info(f"  🔗 Top 3 strongest bridges:")
        for i, bridge in enumerate(bridges[:3]):
            self.logger.info(f"    {i+1}. {bridge.concept} (strength: {bridge.strength:.2f})")
        self.logger.info(f"  ⏱️  Time: {processing_time*1000:.1f}ms")
        
        return bridges
    
    def _find_analogous_concepts(self, profile_a: DomainProfile,
                                 profile_b: DomainProfile) -> List[Tuple[str, str, float]]:
        """Find concepts that are semantically similar across domains."""
        
        analogous = []
        checked_pairs = set()
        
        concepts_a = list(profile_a.key_concepts)[:self.max_concepts_per_domain]
        concepts_b = list(profile_b.key_concepts)[:self.max_concepts_per_domain]
        
        for concept_a in concepts_a:
            for concept_b in concepts_b:
                if concept_a == concept_b:
                    continue
                
                pair = tuple(sorted([concept_a, concept_b]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                
                # Check cache first
                cache_key = f"{concept_a}|{concept_b}"
                if cache_key in self.embedding_cache:
                    similarity = self.embedding_cache[cache_key]
                    self.metrics['cache_hits'] += 1
                else:
                    # Compute similarity
                    similarity = self._compute_concept_similarity(concept_a, concept_b)
                    self.embedding_cache[cache_key] = similarity
                    self.metrics['cache_misses'] += 1
                    
                    # Manage cache size
                    if len(self.embedding_cache) > self.max_cache_size:
                        # Remove oldest
                        oldest = next(iter(self.embedding_cache))
                        del self.embedding_cache[oldest]
                
                if similarity >= self.config.get('similarity_threshold', 0.7):
                    analogous.append((concept_a, concept_b, similarity))
        
        return analogous
    
    def _compute_concept_similarity(self, concept_a: str, concept_b: str) -> float:
        """Compute semantic similarity between two concepts."""
        try:
            # Use memory embeddings if available
            if self.memory and self.config.get('use_embeddings', True):
                results = self.memory.query(
                    query_texts=[concept_a],
                    n_results=1
                )
                
                # Simplified similarity based on text
                # In practice, would use actual embeddings
                common_chars = set(concept_a) & set(concept_b)
                return len(common_chars) / max(len(concept_a), len(concept_b))
            
        except Exception as e:
            self.logger.debug(f"Embedding error: {e}")
        
        # Fallback: character-based similarity
        common = len(set(concept_a) & set(concept_b))
        total = max(len(set(concept_a)), len(set(concept_b)))
        return common / total if total > 0 else 0.0
    
    def _find_methodological_bridges(self, profile_a: DomainProfile,
                                    profile_b: DomainProfile) -> Set[str]:
        """Find shared methodological approaches."""
        return profile_a.methodologies.intersection(profile_b.methodologies)
    
    def _get_concept_context(self, concept: str, profile: DomainProfile) -> str:
        """Get context of how a concept is used in a domain."""
        # Find papers containing this concept
        relevant_papers = [
            p for p in profile.papers
            if concept.lower() in p.get('title', '').lower() or 
               concept.lower() in p.get('summary', '').lower()
        ]
        
        if relevant_papers:
            # Return snippet from first relevant paper
            paper = relevant_papers[0]
            summary = paper.get('summary', '')
            # Find sentence containing concept
            sentences = summary.split('.')
            for sent in sentences:
                if concept.lower() in sent.lower():
                    return sent.strip()[:200]
        
        return f"Used in {profile.name}"
    
    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    
    def find_bridges_batch(self, domain_pairs: List[Tuple[str, str]]) -> Dict[Tuple[str, str], List[BridgeConcept]]:
        """
        Find bridges for multiple domain pairs in batch.
        
        Args:
            domain_pairs: List of (domain_a, domain_b) tuples
            
        Returns:
            Dictionary mapping domain pairs to bridge lists
        """
        results = {}
        
        for i in range(0, len(domain_pairs), self.batch_size):
            batch = domain_pairs[i:i+self.batch_size]
            self.logger.info(f"📦 Processing batch {i//self.batch_size + 1}/{(len(domain_pairs)-1)//self.batch_size + 1}")
            
            for domain_a, domain_b in batch:
                bridges = self.find_bridges(domain_a, domain_b)
                results[(domain_a, domain_b)] = bridges
        
        return results
    
    # ========================================================================
    # HYPOTHESIS GENERATION
    # ========================================================================
    
    @handle_hardware_errors(default_return=[])
    def generate_hypotheses(self, bridges: List[BridgeConcept],
                           max_hypotheses: Optional[int] = None) -> List[NovelHypothesis]:
        """
        Generate novel hypotheses from discovered bridges.
        
        This uses Layer 13 (Ontogenesis) to create genuinely new ideas
        from the bridge concepts.
        
        Args:
            bridges: List of discovered bridges
            max_hypotheses: Maximum number of hypotheses to generate
            
        Returns:
            List of novel hypotheses
        """
        start_time = time.time()
        
        if max_hypotheses is None:
            max_hypotheses = self.config.get('max_hypotheses_per_pair', 5) * len(set((b.domain_a, b.domain_b) for b in bridges))
        
        self.logger.info(f"\n💡 Generating hypotheses from {len(bridges)} bridges...")
        
        hypotheses = []
        
        # Group bridges by domain pair
        domain_pairs = defaultdict(list)
        for bridge in bridges:
            key = tuple(sorted([bridge.domain_a, bridge.domain_b]))
            domain_pairs[key].append(bridge)
        
        for (domain_a, domain_b), pair_bridges in domain_pairs.items():
            self.logger.info(f"\n  🔬 {domain_a} × {domain_b}")
            
            # Take top bridges by strength
            top_bridges = sorted(pair_bridges, key=lambda b: b.strength, reverse=True)[:self.config.get('max_hypotheses_per_pair', 5)]
            
            for bridge in top_bridges:
                # Generate hypothesis using Layer 13
                seed = {
                    'type': f'hypothesis_{domain_a}_{domain_b}',
                    'stability_score': bridge.strength,
                    'causal_efficacy': 0.8,
                    'bridge_concept': bridge.concept,
                    'domains': [domain_a, domain_b]
                }
                
                novel_structure = self.layer13.generate_novel_structure(seed)
                
                if novel_structure:
                    # Create hypothesis
                    hypothesis = self._create_hypothesis_from_bridge(
                        bridge, novel_structure, domain_a, domain_b
                    )
                    
                    hypotheses.append(hypothesis)
                    self.logger.info(f"    ✓ Generated: {hypothesis.description[:80]}...")
                    
                    if len(hypotheses) >= max_hypotheses:
                        break
            
            if len(hypotheses) >= max_hypotheses:
                break
        
        # Store hypotheses
        self.hypotheses.extend(hypotheses)
        for h in hypotheses:
            for domain in h.source_domains:
                self.hypotheses_by_domain[domain].append(h)
        
        # Update metrics
        self.metrics['hypotheses_generated'] += len(hypotheses)
        if hypotheses:
            avg_novelty = np.mean([h.novelty_score for h in hypotheses])
            self.metrics['avg_novelty_score'] = (
                (self.metrics['avg_novelty_score'] * (self.metrics['hypotheses_generated'] - len(hypotheses)) +
                 avg_novelty * len(hypotheses)) / self.metrics['hypotheses_generated']
            )
        
        processing_time = time.time() - start_time
        self.metrics['total_processing_time'] += processing_time
        
        self.logger.info(f"\n✨ Generated {len(hypotheses)} novel hypotheses")
        self.logger.info(f"  ⏱️  Time: {processing_time*1000:.1f}ms")
        
        return hypotheses
    
    def _create_hypothesis_from_bridge(self, bridge: BridgeConcept,
                                      novel_structure: NovelStructure,
                                      domain_a: str, domain_b: str) -> NovelHypothesis:
        """Create a hypothesis from a bridge and novel structure."""
        
        # Generate hypothesis description
        if "method:" in bridge.concept:
            method = bridge.concept.replace("method:", "")
            description = (
                f"Apply {method} from {domain_a} to solve problems in {domain_b}, "
                f"leveraging insights from {bridge.context_a[:100]}"
            )
        elif "≈" in bridge.concept:
            parts = bridge.concept.split(" ≈ ")
            description = (
                f"The concept of '{parts[0]}' in {domain_a} may be analogous to "
                f"'{parts[1]}' in {domain_b}, suggesting a unified framework"
            )
        else:
            description = (
                f"The shared concept '{bridge.concept}' bridges {domain_a} and {domain_b}, "
                f"enabling novel applications of {bridge.context_a[:100]} in {domain_b} context"
            )
        
        # Generate unique ID
        hash_input = f"{domain_a}{domain_b}{bridge.concept}{time.time()}".encode()
        hypothesis_id = f"HYP_{hashlib.md5(hash_input).hexdigest()[:8].upper()}"
        
        hypothesis = NovelHypothesis(
            id=hypothesis_id,
            description=description,
            source_domains=[domain_a, domain_b],
            bridge_concepts=[bridge.concept],
            novelty_score=novel_structure.stability_score,
            feasibility_score=bridge.strength * 0.8,
            impact_potential=novel_structure.causal_efficacy,
            supporting_evidence=[bridge.context_a[:200], bridge.context_b[:200]],
            required_resources=["interdisciplinary collaboration", "validation experiments"],
            testability_score=bridge.strength * 0.7
        )
        
        return hypothesis
    
    # ========================================================================
    # ANALYSIS & EXPORT
    # ========================================================================
    
    def rank_hypotheses(self, criteria: str = 'combined') -> List[NovelHypothesis]:
        """Rank hypotheses by various criteria."""
        
        criteria_map = {
            'impact': lambda h: h.impact_potential,
            'feasibility': lambda h: h.feasibility_score,
            'novelty': lambda h: h.novelty_score,
            'testability': lambda h: h.testability_score,
            'combined': lambda h: (h.impact_potential * h.feasibility_score * h.novelty_score) ** (1/3)
        }
        
        sort_key = criteria_map.get(criteria, criteria_map['combined'])
        return sorted(self.hypotheses, key=sort_key, reverse=True)
    
    def get_bridges_by_domain(self, domain: str) -> List[BridgeConcept]:
        """Get all bridges involving a specific domain."""
        return self.bridges_by_domain.get(domain, [])
    
    def get_hypotheses_by_domain(self, domain: str) -> List[NovelHypothesis]:
        """Get all hypotheses involving a specific domain."""
        return self.hypotheses_by_domain.get(domain, [])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get synthesis statistics."""
        return {
            'domains': len(self.domains),
            'bridges': len(self.bridges),
            'hypotheses': len(self.hypotheses),
            'metrics': self.metrics,
            'avg_bridge_strength': float(self.metrics['avg_bridge_strength']),
            'avg_novelty': float(self.metrics['avg_novelty_score']),
            'cache_efficiency': self.metrics['cache_hits'] / (self.metrics['cache_hits'] + self.metrics['cache_misses'] + 1)
        }
    
    def export_synthesis_report(self, output_file: str = "synthesis_report.json") -> Dict:
        """Export complete synthesis report."""
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'stats': self.get_stats(),
            'domains': {
                name: {
                    'name': name,
                    'papers': len(profile.papers),
                    'concepts': len(profile.key_concepts),
                    'methodologies': list(profile.methodologies),
                    'worldview': profile.ontology.worldview_vector.tolist(),
                    'created_at': profile.created_at,
                    'last_updated': profile.last_updated
                }
                for name, profile in self.domains.items()
            },
            'bridges': [
                {
                    'id': b.id,
                    'concept': b.concept,
                    'domains': f"{b.domain_a} ↔ {b.domain_b}",
                    'strength': b.strength,
                    'confidence': b.confidence,
                    'transformation': ' → '.join(b.transformation_path),
                    'discovered_at': b.discovered_at
                }
                for b in sorted(self.bridges, key=lambda x: x.strength, reverse=True)[:50]
            ],
            'hypotheses': [
                {
                    'id': h.id,
                    'description': h.description,
                    'domains': h.source_domains,
                    'novelty': h.novelty_score,
                    'feasibility': h.feasibility_score,
                    'impact': h.impact_potential,
                    'testability': h.testability_score,
                    'status': h.status,
                    'created_at': h.created_at
                }
                for h in self.rank_hypotheses('combined')[:20]
            ],
            'bridge_history': self.bridge_history[-50:]  # Last 50
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"\n📄 Synthesis report exported to: {output_file}")
        
        return report
    
    def print_top_discoveries(self, n: int = 5):
        """Print top discoveries in a nice format."""
        
        print("\n" + "="*80)
        print("CROSS-DOMAIN SYNTHESIS: TOP DISCOVERIES")
        print("="*80)
        
        # Stats
        stats = self.get_stats()
        print(f"\n📊 Statistics:")
        print(f"   Domains: {stats['domains']}")
        print(f"   Bridges: {stats['bridges']}")
        print(f"   Hypotheses: {stats['hypotheses']}")
        print(f"   Avg bridge strength: {stats['avg_bridge_strength']:.3f}")
        print(f"   Avg novelty: {stats['avg_novelty']:.3f}")
        print(f"   Cache efficiency: {stats['cache_efficiency']*100:.1f}%")
        
        # Top bridges
        print(f"\n🌉 TOP {n} BRIDGES:")
        print("-" * 80)
        top_bridges = sorted(self.bridges, key=lambda b: b.strength, reverse=True)[:n]
        for i, bridge in enumerate(top_bridges, 1):
            print(f"\n{i}. {bridge.concept}")
            print(f"   Domains: {bridge.domain_a} ↔ {bridge.domain_b}")
            print(f"   Strength: {bridge.strength:.2f}")
            print(f"   Confidence: {bridge.confidence:.2f}")
            print(f"   Context A: {bridge.context_a[:100]}...")
            print(f"   Context B: {bridge.context_b[:100]}...")
        
        # Top hypotheses
        print(f"\n\n💡 TOP {n} HYPOTHESES:")
        print("-" * 80)
        top_hypos = self.rank_hypotheses('combined')[:n]
        for i, hypo in enumerate(top_hypos, 1):
            print(f"\n{i}. {hypo.description[:150]}...")
            print(f"   Domains: {' × '.join(hypo.source_domains)}")
            print(f"   Novelty: {hypo.novelty_score:.2f} | "
                  f"Feasibility: {hypo.feasibility_score:.2f} | "
                  f"Impact: {hypo.impact_potential:.2f} | "
                  f"Testability: {hypo.testability_score:.2f}")
        
        print("\n" + "="*80)
    
    # ========================================================================
    # CLEANUP
    # ========================================================================
    
    def cleanup(self):
        """Clean up resources."""
        self.logger.info("🧹 Cleaning up CrossDomainSynthesizer...")
        
        # Clear caches
        self.embedding_cache.clear()
        
        # Export final report
        self.export_synthesis_report("synthesis_report_final.json")
        
        self.logger.info("✅ Cleanup complete")


# ========================================================================
# INTEGRATION EXAMPLE
# ========================================================================

def integrate_with_apeiron():
    """Example of how to integrate with Apeiron."""
    
    example_code = '''
# In apeiron.py, add to Apeiron class:

def enable_cross_domain_synthesis(self, config_path: Optional[str] = None):
    """Enable cross-domain synthesis capabilities."""
    from cross_domain_synthesis import CrossDomainSynthesizer
    
    self.synthesizer = CrossDomainSynthesizer(
        layer12=self.layer12,
        layer13=self.layer13,
        memory=self.memory,
        config_path=config_path,
        use_hardware=hasattr(self, 'hardware') and self.hardware is not None
    )
    
    self.log.info("✨ Cross-Domain Synthesis Engine enabled!")

def analyze_domain_connections(self, domain_a: str, domain_b: str):
    """Find bridges between two research domains."""
    
    # Get papers for each domain
    papers_a = self._get_domain_papers(domain_a)
    papers_b = self._get_domain_papers(domain_b)
    
    # Build domain profiles
    self.synthesizer.build_domain_profile(domain_a, papers_a)
    self.synthesizer.build_domain_profile(domain_b, papers_b)
    
    # Find bridges
    bridges = self.synthesizer.find_bridges(domain_a, domain_b)
    
    # Generate hypotheses
    hypotheses = self.synthesizer.generate_hypotheses(bridges)
    
    # Export report
    self.synthesizer.export_synthesis_report(
        f"synthesis_{domain_a}_{domain_b}_{int(time.time())}.json"
    )
    
    return bridges, hypotheses

def _get_domain_papers(self, domain: str, max_papers: int = 50):
    """Get papers for a specific domain from memory."""
    results = self.memory.query(
        query_texts=[domain],
        n_results=max_papers
    )
    
    papers = []
    if results['documents'] and results['metadatas']:
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            papers.append({
                'title': meta.get('title', ''),
                'summary': doc,
                'id': meta.get('step', 0),
                'published': meta.get('published', None)
            })
    
    return papers
'''
    
    print(example_code)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CROSS-DOMAIN SYNTHESIS ENGINE V12")
    print("="*80)
    print("\nThis module enables finding non-obvious connections between")
    print("disparate research domains using Layer 12 reconciliation")
    print("and Layer 13 novelty generation.")
    print("\nV12 enhancements:")
    print("  • Hardware acceleration")
    print("  • Metrics tracking")
    print("  • Config management")
    print("  • Batch processing")
    print("  • Caching")
    print("\nIntegration instructions:")
    print("="*80)
    integrate_with_apeiron()