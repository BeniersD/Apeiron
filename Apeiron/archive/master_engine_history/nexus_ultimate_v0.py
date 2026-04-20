"""
NEXUS ULTIMATE: COMPLETE INTEGRATION
17-Layer Framework + Autonomous Research + Real-time Dashboard
The Ultimate Self-Evolving Intelligence System
"""

import numpy as np
import chromadb
import requests
import fitz  # PyMuPDF
import io
from chromadb.utils import embedding_functions
import time, json, arxiv, os, random
from habanero import Crossref
from datetime import datetime
from typing import Dict, List, Any

# Import your 17-layer architecture
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


class NexusUltimate:
    """
    The complete integration of all 17 layers with autonomous research
    and planetary-scale intelligence.
    """
    
    def __init__(self, db_path="./nexus_memory"):
        print("\n" + "="*80)
        print("🌌 NEXUS ULTIMATE: INITIALIZING")
        print("   17-Layer Intelligence + Autonomous Research + Ethical Governance")
        print("="*80 + "\n")
        
        # Create database directory
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        
        # ====================================================================
        # FOUNDATION: 17-LAYER ARCHITECTURE
        # ====================================================================
        
        print("Phase 1: Initializing 17-Layer Architecture...")
        self.framework = SeventeenLayerFramework()
        
        # Initialize all higher layers
        self.layer11 = Layer11_MetaContextualization(self.framework.layer10)
        self.layer12 = Layer12_Reconciliation(self.layer11)
        self.layer13 = Layer13_Ontogenesis(self.layer12)
        self.layer14 = Layer14_Worldbuilding(self.layer13)
        self.layer15 = Layer15_EthicalConvergence(self.layer14)
        self.layer16 = Layer16_Transcendence(self.layer15)
        self.layer17 = Layer17_AbsoluteIntegration(self.layer16)
        
        # Create initial autopoietic world
        self.primary_world = self.layer14.create_world(
            initial_agents=25,
            normative_constraints=[
                'preserve_biodiversity',
                'maintain_energy_balance',
                'ensure_agent_welfare'
            ]
        )
        
        # Create collective intelligence
        self.collective = self.layer16.form_collective(
            [f'research_agent_{i}' for i in range(15)]
        )
        
        print("✓ All 17 layers initialized\n")
        
        # ====================================================================
        # MEMORY & KNOWLEDGE BASE
        # ====================================================================
        
        print("Phase 2: Initializing Knowledge Systems...")
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.memory = self.chroma_client.get_or_create_collection(
            name="nexus_ultimate_memory",
            embedding_function=self.emb_fn
        )
        
        print("✓ Knowledge base ready\n")
        
        # ====================================================================
        # RESEARCH INFRASTRUCTURE
        # ====================================================================
        
        print("Phase 3: Initializing Research Systems...")
        self.arxiv_client = arxiv.Client()
        self.crossref = Crossref()
        
        # Autonomous research queue
        self.research_queue = [self._generate_seed_topic()]
        self.explored_topics = set()
        
        print("✓ Research infrastructure ready\n")
        
        # ====================================================================
        # STATE TRACKING
        # ====================================================================
        
        self.step_count = self._get_last_step()
        self.cycle_count = 0
        self.last_entropy = 0.5
        self.transcendence_events = []
        self.ethical_interventions = []
        self.deep_dive_count = 0
        
        print("="*80)
        print("✨ NEXUS ULTIMATE: FULLY OPERATIONAL")
        print("="*80 + "\n")
    
    def _get_last_step(self) -> int:
        """Get last step from memory."""
        try:
            return self.memory.count()
        except:
            return 0
    
    def _generate_seed_topic(self) -> str:
        """Generate intelligent seed topics based on current system state."""
        
        # Layer 16 provides transcendent topic suggestions
        if len(self.layer16.transcendent_insights) > 0:
            insight = self.layer16.transcendent_insights[-1]
            return f"Novel {insight['type']} Research"
        
        # Default seed pool
        domains = [
            "Quantum", "Relativistic", "Molecular", "Sociological", 
            "Neural", "Topological", "Recursive", "Emergent",
            "Complex", "Adaptive", "Autopoietic", "Transcendent"
        ]
        targets = [
            "Dynamics", "Information", "Entropy", "Structure", 
            "Evolution", "Symmetry", "Coherence", "Integration"
        ]
        return f"{random.choice(domains)} {random.choice(targets)}"
    
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
        
        return [f"{paper.primary_category} {kw}" for kw in keywords]
    
    def _calculate_entropy(self, current_title: str, past_context: str) -> float:
        """
        Calculate information entropy using Layer 7 synthesis.
        """
        if not past_context or "First" in past_context:
            return 0.8
        
        # Basic overlap calculation
        overlap = len(set(current_title.split()) & set(past_context.split()))
        entropy = 1.0 - (overlap / max(len(current_title.split()), 1))
        
        # Adjust based on global coherence
        coherence_factor = self.framework.layer7.synthesis.coherence_score
        adjusted_entropy = entropy * (1 - 0.2 * coherence_factor)
        
        return max(0.1, min(adjusted_entropy, 0.95))
    
    def _deep_dive_analysis(self, paper_url: str) -> str:
        """
        Download and analyze full PDF with Layer 14 worldbuilding context.
        """
        print(f"🔬 DEEP-DIVE: Analyzing {paper_url}")
        
        try:
            response = requests.get(paper_url, timeout=30)
            with fitz.open(stream=io.BytesIO(response.content), filetype="pdf") as doc:
                full_text = ""
                for page_num, page in enumerate(doc):
                    if page_num > 20:  # Limit to first 20 pages
                        break
                    full_text += page.get_text()
            
            self.deep_dive_count += 1
            return full_text[:30000]  # 30k character limit
            
        except Exception as e:
            print(f"⚠️ Deep-Dive failed: {e}")
            return None
    
    def _ethical_evaluation(self, paper: arxiv.Result, entropy: float) -> Dict[str, float]:
        """
        Evaluate research direction ethically using Layer 15.
        """
        action = {
            'harm_level': 0.1,  # Research is generally low harm
            'resource_distribution': [0.5, 0.5],
            'sustainability_impact': 0.9 if entropy > 0.7 else 0.6,
            'autonomy_preserved': True
        }
        
        scores = self.layer15.evaluate_action(action)
        
        # Check for violations
        violation = self.layer15.detect_ethical_violation(action)
        if violation:
            self.ethical_interventions.append({
                'paper': paper.title,
                'violation': violation['violated_principle'],
                'timestamp': self.step_count
            })
        
        return scores
    
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
            relations[(entity_list[i], entity_list[i+1])] = 0.7
        
        # Worldview vector based on paper category
        categories = ['cs', 'physics', 'math', 'bio', 'econ']
        worldview = np.zeros(5)
        for i, cat in enumerate(categories):
            if cat in paper.primary_category:
                worldview[i] = 1.0
        
        ontology = Ontology(
            id=f"paper_{self.step_count}",
            entities=entities,
            relations=relations,
            axioms=[paper.primary_category],
            worldview_vector=worldview
        )
        
        self.layer12.register_ontology(ontology)
        return ontology
    
    def run_research_cycle(self, paper: arxiv.Result) -> bool:
        """
        Execute complete research cycle through all 17 layers.
        """
        # Check for duplicates
        check = self.memory.query(query_texts=[paper.title], n_results=1)
        if check['distances'] and check['distances'][0][0] < 0.05:
            print(f"⏩ Skipping (Already known): {paper.title[:50]}")
            return False
        
        self.step_count += 1
        print(f"\n{'='*80}")
        print(f"CYCLE {self.step_count}: {paper.title[:60]}")
        print(f"{'='*80}")
        
        # ====================================================================
        # PHASE 1: RECALL & CONTEXT (Layers 1-7)
        # ====================================================================
        
        past_context = "First integration."
        try:
            results = self.memory.query(query_texts=[paper.title], n_results=2)
            if results['documents'] and results['documents'][0]:
                past_context = results['documents'][0][0][:400]
        except:
            pass
        
        # Calculate entropy
        current_entropy = self._calculate_entropy(paper.title, past_context)
        self.last_entropy = current_entropy
        
        print(f"  Entropy: {current_entropy:.3f}")
        
        # ====================================================================
        # PHASE 2: DEEP ANALYSIS (Conditional)
        # ====================================================================
        
        analysis_content = paper.summary
        is_deep_dive = False
        
        if current_entropy > 0.75:  # High novelty triggers deep dive
            full_text = self._deep_dive_analysis(paper.pdf_url)
            if full_text:
                analysis_content = full_text
                is_deep_dive = True
                print(f"  🔬 Deep-dive completed")
        
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
        
        print(f"  Foundation coherence: {self.framework.layer7.synthesis.coherence_score:.3f}")
        
        # ====================================================================
        # PHASE 4: META-CONTEXTUALIZATION (Layer 11)
        # ====================================================================
        
        env_cues = {
            'temporal_pressure': 0.3 if is_deep_dive else 0.7,
            'uncertainty_level': current_entropy
        }
        
        context = self.layer11.adaptive_context_selection(env_cues)
        print(f"  Active context: {context}")
        
        # ====================================================================
        # PHASE 5: ONTOLOGICAL INTEGRATION (Layer 12)
        # ====================================================================
        
        paper_ontology = self._create_ontology_from_paper(paper)
        
        # Reconcile with existing ontologies
        if len(self.layer12.ontologies) > 1:
            onto_ids = list(self.layer12.ontologies.keys())[-3:]
            meta_onto = self.layer12.reconcile(onto_ids)
            print(f"  Ontology coherence: {meta_onto.coherence_score:.3f}")
        
        # ====================================================================
        # PHASE 6: ETHICAL EVALUATION (Layer 15)
        # ====================================================================
        
        ethical_scores = self._ethical_evaluation(paper, current_entropy)
        print(f"  Ethical score: {ethical_scores['aggregate']:.3f}")
        
        # ====================================================================
        # PHASE 7: COLLECTIVE COGNITION (Layer 16)
        # ====================================================================
        
        # Collective cognition step
        self.layer16.collective_cognition_step(self.collective)
        print(f"  Collective integration: {self.collective.integration_level:.3f}")
        
        # ====================================================================
        # PHASE 8: ABSOLUTE INTEGRATION (Layer 17)
        # ====================================================================
        
        meta_state = self.layer17.synthesize_absolute_integration()
        
        if meta_state.transcendence_achieved:
            print(f"  ✨ TRANSCENDENCE ACHIEVED ✨")
            self.transcendence_events.append({
                'step': self.step_count,
                'paper': paper.title,
                'coherence': meta_state.global_coherence
            })
        
        # ====================================================================
        # PHASE 9: WORLD EVOLUTION (Layer 14)
        # ====================================================================
        
        # Evolve the autopoietic world
        self.layer14.step_world(self.primary_world.id, timesteps=2)
        
        # ====================================================================
        # PHASE 10: MEMORY STORAGE
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
                "ethical_score": ethical_scores['aggregate'],
                "transcendence": meta_state.transcendence_achieved,
                "timestamp": datetime.now().isoformat()
            }]
        )
        
        # ====================================================================
        # PHASE 11: STATE EXPORT (Dashboard)
        # ====================================================================
        
        self._export_dashboard_state(
            paper.title,
            base_result.get('complexity', {}),
            base_result.get('invariants', []),
            current_entropy,
            is_deep_dive,
            meta_state
        )
        
        self.cycle_count += 1
        return True
    
    def _export_dashboard_state(self, last_title: str, complexity: Dict,
                                invariants: List, entropy: float,
                                deep_dive: bool, meta_state):
        """Export state for real-time dashboard."""
        
        state = {
            "step": self.step_count,
            "cycle": self.cycle_count,
            "last_paper": last_title[:80],
            "queue_size": len(self.research_queue),
            
            # Foundation metrics
            "observables": len(self.framework.layer1.observables),
            "relations": len(self.framework.layer2.relations),
            "functional_entities": len(self.framework.layer3.functional_entities),
            "global_coherence": float(self.framework.layer7.synthesis.coherence_score),
            
            # Higher layer metrics
            "ontology_count": len(self.layer12.ontologies),
            "novel_structures": len(self.layer13.novel_structures),
            "world_sustainability": float(self.primary_world.sustainability_score),
            "autopoietic_closure": self.primary_world.autopoietic_closure,
            "collective_integration": float(self.collective.integration_level),
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
            
            # Active context
            "active_context": self.layer11.active_context,
            "context_switches": len(self.layer11.context_history),
            
            # System invariants
            "invariants": invariants,
            "timestamp": time.time()
        }
        
        with open("nexus_ultimate_state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def start_autonomous_evolution(self):
        """
        Start the autonomous evolution loop.
        System explores, learns, and transcends continuously.
        """
        print("\n" + "="*80)
        print("🚀 NEXUS ULTIMATE: AUTONOMOUS EVOLUTION INITIATED")
        print("="*80 + "\n")
        
        while True:
            # Queue management
            if len(self.research_queue) > 30:
                # Keep most novel topics
                self.research_queue = list(set(self.research_queue[-20:]))
                print("🧹 Research queue optimized")
            
            # Entropy-based exploration
            if self.last_entropy < 0.20 or not self.research_queue:
                # Quantum jump to new domain
                jump_topic = self._generate_seed_topic()
                self.research_queue.insert(0, jump_topic)
                print(f"🌀 QUANTUM JUMP: {jump_topic}")
            
            # Planetary stewardship intervention
            if self.cycle_count % 50 == 0 and self.cycle_count > 0:
                self.layer17.planetary_stewardship_action(
                    'resource_depletion',
                    severity=0.5
                )
                print("🌍 Planetary stewardship intervention executed")
            
            # Get next topic
            if not self.research_queue:
                self.research_queue.append(self._generate_seed_topic())
            
            topic = self.research_queue.pop(0)
            self.explored_topics.add(topic)
            
            print(f"\n📡 Exploring: {topic}")
            
            try:
                # Search arXiv
                search = arxiv.Search(
                    query=topic,
                    max_results=3,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                
                for paper in self.arxiv_client.results(search):
                    if self.run_research_cycle(paper):
                        # Extract new topics from successful cycle
                        new_topics = self._extract_next_topics(paper)
                        self.research_queue.extend(new_topics)
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(5)
            
            # Display transcendence events
            if len(self.transcendence_events) % 10 == 0 and self.transcendence_events:
                print(f"\n✨ Total transcendence events: {len(self.transcendence_events)}")


def main():
    """Main execution."""
    nexus = NexusUltimate()
    nexus.start_autonomous_evolution()


if __name__ == "__main__":
    main()
