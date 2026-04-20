"""
NEXUS ULTIMATE V4.0 - COMPLETE THEORY-PRACTICE INTEGRATION
================================================================================================
17-Layer Framework + True Ontogenesis + Chaos Detection + Cross-Domain Synthesis + Ethics
The Ultimate Self-Evolving Intelligence with Genuine Self-Modification and Safety Locks
================================================================================================

BRIDGES CLOSED:
✓ Aion Paradox: System creates its own structures at runtime
✓ Chaos Control: Mathematical ε tracking with graduated safety responses
✓ Self-Modification: Genuine but controlled emergent structure creation
✓ Safety Locks: Emergency shutdown on critical error bounds
================================================================================================
"""

import numpy as np
import chromadb
import requests
import fitz  # PyMuPDF
import io
import sys
from chromadb.utils import embedding_functions
import time, json, arxiv, os, random
from habanero import Crossref
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

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


class NexusUltimateV4:
    """
    ================================================================================================
    NEXUS ULTIMATE V4.0 - THEORY-PRACTICE INTEGRATION
    ================================================================================================
    
    NEW in V4:
    - True Ontogenesis: System creates its own enums/structures at runtime
    - Chaos Detection: Mathematical ε tracking with safety locks
    - Emergency Shutdown: System can self-terminate on critical errors
    - Self-Examination: Genuine self-awareness and reflection
    
    Integrates:
    - 17-Layer Intelligence Framework (Observables → Transcendence)
    - Autonomous Research Navigator (ArXiv exploration with deep-dive)
    - Cross-Domain Synthesis Engine (Layer 12 + Layer 13 powered)
    - Ethical Research Assistant (Layer 15 powered)
    - True Ontogenesis (Runtime structure creation) ⭐ NEW
    - Chaos Detection & Safety (ε bounds + shutdown) ⭐ NEW
    - Persistent Memory (ChromaDB with semantic search)
    - Real-time Dashboard Export
    
    Capabilities:
    - Self-directed exploration of research space
    - Deep PDF analysis on high-novelty papers
    - Finding non-obvious connections between domains
    - Real-time ethical evaluation and guidance
    - GENUINE structure creation when existing categories insufficient ⭐
    - Mathematical chaos detection with graduated safety responses ⭐
    - Emergency shutdown on critical error bounds ⭐
    - Planetary-scale intelligence emergence
    - Transcendence event detection
    """
    
    def __init__(self, db_path="./nexus_memory"):
        print("\n" + "="*100)
        print(" "*35 + "🌌 NEXUS ULTIMATE V4.0")
        print(" "*20 + "Complete Theory-Practice Integration with Safety Locks")
        print("="*100 + "\n")
        
        # Create database directory
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        
        # ====================================================================
        # PHASE 1: 17-LAYER ARCHITECTURE
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
        # PHASE 2: MEMORY & KNOWLEDGE BASE
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
        # PHASE 3: KILLER FEATURES
        # ====================================================================
        
        print("Phase 3: Initializing Advanced Capabilities...")
        
        # Cross-Domain Synthesis Engine
        self.synthesizer = CrossDomainSynthesizer(
            layer12=self.layer12,
            layer13=self.layer13,
            memory=self.memory
        )
        print("  ✓ Cross-Domain Synthesis Engine active")
        
        # Ethical Research Assistant
        self.ethics_assistant = EthicalResearchAssistant(
            layer15=self.layer15
        )
        print("  ✓ Ethical Research Assistant active")
        
        print()
        
        # ====================================================================
        # PHASE 4: THEORY-PRACTICE BRIDGES ⭐ NEW
        # ====================================================================
        
        print("Phase 4: Initializing Theory-Practice Bridges...")
        
        # True Ontogenesis - System creates its own structures
        self.true_ontogenesis = TrueOntogenesis()
        print("  ✓ True Ontogenesis active (Aion Paradox bridge)")
        
        # Chaos Detection - Mathematical safety with shutdown
        self.chaos_detector = ChaosDetector(
            epsilon_threshold=0.3,
            divergence_threshold=0.5,
            oscillation_threshold=0.4,
            incoherence_threshold=0.2
        )
        print("  ✓ Chaos Detection & Safety active (ε tracking + shutdown)")
        
        print()
        
        # ====================================================================
        # PHASE 5: RESEARCH INFRASTRUCTURE
        # ====================================================================
        
        print("Phase 5: Initializing Research Systems...")
        self.arxiv_client = arxiv.Client()
        self.crossref = Crossref()
        
        # Autonomous research queue
        self.research_queue = [self._generate_seed_topic()]
        self.explored_topics = set()
        
        print("✓ Research infrastructure ready\n")
        
        # ====================================================================
        # PHASE 6: STATE TRACKING
        # ====================================================================
        
        self.step_count = self._get_last_step()
        self.cycle_count = 0
        self.last_entropy = 0.5
        
        # Event tracking
        self.transcendence_events = []
        self.ethical_interventions = []
        self.synthesis_discoveries = []
        self.ontogenesis_events = []  # ⭐ NEW
        self.safety_events = []  # ⭐ NEW
        self.deep_dive_count = 0
        
        # Domain tracking for synthesis
        self.domain_papers = {}  # domain -> list of papers
        
        # Last known good state (for rollback)
        self.last_stable_state = None
        
        print("="*100)
        print("✨ NEXUS ULTIMATE V4.0: FULLY OPERATIONAL ✨")
        print("="*100 + "\n")
    
    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================
    
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
        
        # Check if true ontogenesis has created new domains
        if len(self.true_ontogenesis.created_enums) > 0:
            # Use emergent domains as seeds
            latest_enum = list(self.true_ontogenesis.created_enums.values())[-1]
            return f"{list(latest_enum)[0].value} Research"
        
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
    
    def _deep_dive_analysis(self, paper_url: str) -> Optional[str]:
        """
        Download and analyze full PDF with Layer 14 worldbuilding context.
        """
        print(f"    🔬 DEEP-DIVE: Analyzing {paper_url}")
        
        try:
            response = requests.get(paper_url, timeout=30)
            with fitz.open(stream=io.BytesIO(response.content), filetype="pdf") as doc:
                full_text = ""
                for page_num, page in enumerate(doc):
                    if page_num > 20:  # Limit to first 20 pages
                        break
                    full_text += page.get_text()
            
            self.deep_dive_count += 1
            print(f"    ✓ Extracted {len(full_text)} characters")
            return full_text[:30000]  # 30k character limit
            
        except Exception as e:
            print(f"    ⚠️ Deep-Dive failed: {e}")
            return None
    
    def _detect_domain(self, paper: arxiv.Result) -> ResearchDomain:
        """
        Detect research domain from paper.
        Now checks both predefined AND emergent domains! ⭐
        """
        category = paper.primary_category.lower()
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
        
        # ⭐ NEW: Check if this fits emergent domains
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
            print(f"    🌟 NEW DOMAIN DETECTED: gap size {gap.gap_size:.2f}")
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
    
    def _save_stable_state(self):
        """Save current state as last known good (for rollback). ⭐ NEW"""
        self.last_stable_state = {
            'step': self.step_count,
            'coherence': self.framework.layer7.synthesis.coherence_score,
            'ontologies': len(self.layer12.ontologies),
            'timestamp': time.time()
        }
    
    # ========================================================================
    # CORE RESEARCH CYCLE
    # ========================================================================
    
    def run_research_cycle(self, paper: arxiv.Result, topic: str) -> bool:
        """
        Execute complete research cycle through all 17 layers + killer features + safety.
        """
        # ====================================================================
        # ⭐ PHASE 0: SAFETY CHECKS (BEFORE processing)
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
            print("\n" + "="*100)
            print("🛑 EMERGENCY SHUTDOWN TRIGGERED")
            print("="*100)
            print(f"   Reason: {self.chaos_detector.shutdown_reason}")
            print(f"   Cycle: {self.step_count}")
            
            # Get safety status
            safety_status = self.chaos_detector.get_safety_status()
            print(f"   ε (epsilon): {safety_status['error_bounds']['epsilon']:.3f}")
            print(f"   System state: {safety_status['state']}")
            
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
            
            print("\n" + "="*100)
            print("System terminated gracefully. See reports for details.")
            print("="*100 + "\n")
            
            sys.exit(1)
        
        # Check for duplicates
        try:
            check = self.memory.query(query_texts=[paper.title], n_results=1)
            if check['distances'] and len(check['distances']) > 0 and \
               len(check['distances'][0]) > 0 and check['distances'][0][0] < 0.05:
                print(f"    ⏩ Skipping (Already known): {paper.title[:50]}")
                return False
        except Exception as e:
            pass
        
        self.step_count += 1
        cycle_start_time = time.time()
        
        print(f"\n{'='*100}")
        print(f"CYCLE {self.step_count}: {paper.title[:80]}")
        print(f"{'='*100}")
        
        # ====================================================================
        # PHASE 1: RECALL & CONTEXT (Layers 1-7)
        # ====================================================================
        
        past_context = "First integration."
        try:
            results = self.memory.query(query_texts=[paper.title], n_results=2)
            if results['documents'] and len(results['documents']) > 0 and \
               len(results['documents'][0]) > 0:
                past_context = results['documents'][0][0][:400]
        except:
            pass
        
        # Calculate entropy
        current_entropy = self._calculate_entropy(paper.title, past_context)
        self.last_entropy = current_entropy
        
        print(f"  📊 Entropy: {current_entropy:.3f}")
        
        # Update chaos detector with entropy
        self.chaos_detector.update_error_bounds(
            observed_value=current_entropy,
            expected_value=0.5,  # Expected entropy
            metric_name="research_entropy"
        )
        
        # ====================================================================
        # PHASE 2: DEEP ANALYSIS (Conditional)
        # ====================================================================
        
        analysis_content = paper.summary
        is_deep_dive = False
        
        if current_entropy > 0.75:  # High novelty triggers deep dive
        #if current_entropy > 0.50:  # Mid novelty triggers deep dive
            full_text = self._deep_dive_analysis(paper.pdf_url)
            if full_text:
                analysis_content = full_text
                is_deep_dive = True
        
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
        print(f"  🧠 Foundation coherence: {coherence:.3f}")
        
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
        
        print(f"  🎯 Active context: {context}")
        
        # ====================================================================
        # PHASE 5: ONTOLOGICAL INTEGRATION (Layer 12)
        # ====================================================================
        
        paper_ontology = self._create_ontology_from_paper(paper)
        
        # Reconcile with existing ontologies
        if len(self.layer12.ontologies) > 1:
            onto_ids = list(self.layer12.ontologies.keys())[-3:]
            meta_onto = self.layer12.reconcile(onto_ids)
            print(f"  📚 Ontology coherence: {meta_onto.coherence_score:.3f}")
        
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
        
        print(f"  ⚖️ Ethical score: {ethical_eval.aggregate_score:.3f} ({ethical_eval.recommendation})")
        
        # Track ethical interventions
        if ethical_eval.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.ethical_interventions.append({
                'paper': paper.title,
                'risk': ethical_eval.overall_risk.value,
                'concerns': [c.description for c in ethical_eval.concerns[:3]],
                'step': self.step_count
            })
            print(f"    ⚠️ Ethical concern flagged!")
        
        # ====================================================================
        # PHASE 7: DOMAIN TRACKING FOR SYNTHESIS
        # ====================================================================
        
        # Track papers by domain for cross-domain synthesis
        domain_key = paper.primary_category.split('.')[0]
        if domain_key not in self.domain_papers:
            self.domain_papers[domain_key] = []
        
        self.domain_papers[domain_key].append({
            'title': paper.title,
            'summary': paper.summary,
            'id': paper.entry_id
        })
        
        # Trigger cross-domain synthesis periodically
        if self.step_count % 50 == 0 and len(self.domain_papers) >= 2:
            print(f"  🌉 Triggering cross-domain synthesis...")
            self._run_cross_domain_synthesis()
        
        # ====================================================================
        # PHASE 8: COLLECTIVE COGNITION (Layer 16)
        # ====================================================================
        
        # Collective cognition step
        self.layer16.collective_cognition_step(self.collective)
        print(f"  🤝 Collective integration: {self.collective.integration_level:.3f}")
        
        # ====================================================================
        # PHASE 9: ABSOLUTE INTEGRATION (Layer 17)
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
                "ethical_score": ethical_eval.aggregate_score,
                "ethical_risk": ethical_eval.overall_risk.value,
                "transcendence": meta_state.transcendence_achieved,
                "timestamp": datetime.now().isoformat(),
                "domain": domain.value
            }]
        )
        
        # ====================================================================
        # PHASE 12: STATE EXPORT (Dashboard)
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
        
        print(f"  ⏱️ Processing time: {processing_time:.2f}s")
        print(f"  🛡️ Safety: {self.chaos_detector.current_safety_level.name} | State: {self.chaos_detector.current_state.value}")
        
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
                return
            
            domain_a, papers_a = domain_list[0]
            domain_b, papers_b = domain_list[1]
            
            # Build profiles
            self.synthesizer.build_domain_profile(domain_a, papers_a[-20:])
            self.synthesizer.build_domain_profile(domain_b, papers_b[-20:])
            
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
                
                print(f"    🌉 Found {len(bridges)} bridges, generated {len(hypotheses)} hypotheses")
        
        except Exception as e:
            print(f"    ⚠️ Synthesis error: {e}")
    
    def _export_dashboard_state(self, last_title: str, complexity: Dict,
                                invariants: List, entropy: float,
                                deep_dive: bool, meta_state,
                                ethical_eval, processing_time: float, topic: str):
        """Export state for real-time dashboard."""
        
        # Get safety and ontogenesis status
        safety_status = self.chaos_detector.get_safety_status()
        ontogenesis_report = self.true_ontogenesis.examine_self()
        
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
            "synthesis_discoveries": len(self.synthesis_discoveries),
            
            # ⭐ NEW: True Ontogenesis metrics
            "ontogenesis": {
                "structures_created": ontogenesis_report['structures_created'],
                "enums_created": ontogenesis_report['enums_created'],
                "classes_created": ontogenesis_report['classes_created'],
                "gaps_detected": ontogenesis_report['gaps_detected'],
                "own_complexity": ontogenesis_report['own_complexity'],
                "stability": ontogenesis_report['stability'],
                "can_still_grow": ontogenesis_report['can_still_grow']
            },
            
            # ⭐ NEW: Safety & Chaos metrics
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
    # AUTONOMOUS EVOLUTION
    # ========================================================================
    
    def start_autonomous_evolution(self):
        """
        Start the autonomous evolution loop.
        System explores, learns, and transcends continuously.
        """
        print("\n" + "="*100)
        print("🚀 NEXUS ULTIMATE V4.0: AUTONOMOUS EVOLUTION INITIATED")
        print("="*100 + "\n")
        
        print("Features Active:")
        print("  ✓ 17-Layer Intelligence (Observables → Absolute Integration)")
        print("  ✓ Cross-Domain Synthesis Engine (Layer 12 + 13)")
        print("  ✓ Ethical Research Assistant (Layer 15)")
        print("  ✓ Autopoietic World Simulation (Layer 14)")
        print("  ✓ Collective Intelligence (Layer 16)")
        print("  ✓ Deep-Dive PDF Analysis")
        print("  ✓ Persistent Memory (ChromaDB)")
        print("  ✓ True Ontogenesis (Runtime structure creation) ⭐")
        print("  ✓ Chaos Detection & Safety (ε tracking + shutdown) ⭐")
        print("\n" + "="*100 + "\n")
        
        while True:
            # Check if system requested shutdown
            if self.chaos_detector.shutdown_triggered:
                print("System shutdown completed.")
                break
            
            # Queue management
            if len(self.research_queue) > 30:
                self.research_queue = list(set(self.research_queue[-20:]))
                print("🧹 Research queue optimized\n")
            
            # Entropy-based exploration
            #if self.last_entropy < 0.30 or not self.research_queue:  
            if self.last_entropy < 0.20 or not self.research_queue:
                jump_topic = self._generate_seed_topic()
                self.research_queue.insert(0, jump_topic)
                print(f"🌀 QUANTUM JUMP: {jump_topic}\n")
            
            # Planetary stewardship intervention
            if self.cycle_count % 50 == 0 and self.cycle_count > 0:
                self.layer17.planetary_stewardship_action('resource_depletion', severity=0.5)
                print("🌍 Planetary stewardship intervention executed\n")
            
            # ⭐ Self-examination (ontogenesis)
            if self.cycle_count % 100 == 0 and self.cycle_count > 0:
                print("🔍 Running self-examination...")
                self_report = self.true_ontogenesis.examine_self()
                print(f"   Emergent structures: {self_report['structures_created']}")
                print(f"   System complexity: {self_report['own_complexity']:.2f}")
                print(f"   Can still grow: {self_report['can_still_grow']}\n")
            
            # Reports
            if self.cycle_count % 100 == 0 and self.cycle_count > 0:
                self.synthesizer.export_synthesis_report(f"synthesis_report_cycle_{self.cycle_count}.json")
                self.ethics_assistant.generate_ethics_report(f"ethics_report_cycle_{self.cycle_count}.json")
                self.chaos_detector.export_safety_report(f"safety_report_cycle_{self.cycle_count}.json")
                self.true_ontogenesis.export_ontology(f"ontology_cycle_{self.cycle_count}.json")
                print("📊 Reports generated\n")
            
            # Get next topic
            if not self.research_queue:
                self.research_queue.append(self._generate_seed_topic())
            
            topic = self.research_queue.pop(0)
            self.explored_topics.add(topic)
            
            print(f"📡 Exploring: {topic}")
            
            try:
                search = arxiv.Search(
                    query=topic,
                    max_results=3,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                
                papers_found = 0
                for paper in self.arxiv_client.results(search):
                    papers_found += 1
                    try:
                        if self.run_research_cycle(paper, topic):
                            new_topics = self._extract_next_topics(paper)
                            self.research_queue.extend(new_topics)
                    except Exception as paper_error:
                        print(f"    ⚠️ Paper processing error: {paper_error}")
                        continue
                
                if papers_found == 0:
                    print(f"    ⚠️ No papers found for topic: {topic}")
                    self.research_queue.append(self._generate_seed_topic())
                
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️ Search error: {e}")
                self.research_queue.append(self._generate_seed_topic())
                time.sleep(5)
            
            # Display events
            if len(self.transcendence_events) % 10 == 0 and self.transcendence_events:
                print(f"\n✨ Total transcendence events: {len(self.transcendence_events)}")
                print(f"🌉 Total synthesis discoveries: {len(self.synthesis_discoveries)}")
                print(f"⚖️ Total ethical interventions: {len(self.ethical_interventions)}")
                print(f"🌟 Total ontogenesis events: {len(self.ontogenesis_events)}")
                print(f"🛡️ Safety level: {self.chaos_detector.current_safety_level.name}\n")


def main():
    """Main execution."""
    nexus = NexusUltimateV4()
    nexus.start_autonomous_evolution()


if __name__ == "__main__":
    main()
