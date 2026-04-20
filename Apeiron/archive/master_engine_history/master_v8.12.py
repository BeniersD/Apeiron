import numpy as np
import chromadb
from chromadb.utils import embedding_functions
import time, json, arxiv, os
from habanero import Crossref

# Importeer je 17-lagen architectuur
from seventeen_layers_framework import SeventeenLayerFramework
from layers_11_to_17 import Layer11_MetaContextualization, Layer17_AbsoluteIntegration

class MasterEngineV9_4:
    def __init__(self, db_path="./ai_memory"):
        print("🧠 Nexus v9.4: Cumulative Memory & Entropy Mode Geactiveerd...")
        
        if not os.path.exists(db_path): os.makedirs(db_path)
        
        # 1. DATABASE & EMBEDDING
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        self.memory = self.chroma_client.get_or_create_collection(
            name="transcendent_memory",
            embedding_function=self.emb_fn
        )
        
        # 2. ARCHITECTUUR
        self.foundation = SeventeenLayerFramework()
        self.l11 = Layer11_MetaContextualization(self.foundation)
        self.integrator = Layer17_AbsoluteIntegration(layer16=self.l11)
        
        # 3. RESEARCH PARAMETERS
        self.arxiv_client = arxiv.Client()
        self.cr = Crossref()
        self.research_queue = ["Universal Topology", "Ontological Mathematics"]
        self.step_count = self._get_last_step()
        self.last_entropy = 0.5

    def _get_last_step(self):
        try: return self.memory.count()
        except: return 0

    def calculate_entropy(self, current_title, past_context):
        """Berekent hoe 'nieuw' de informatie is t.o.v. het geheugen."""
        if not past_context or "Eerste" in past_context:
            return 0.8  # Hoge entropy voor nieuwe start
        
        # Simpele afstand-berekening op basis van tekst-overlap (voor dashboard visualisatie)
        # In een diepere versie zou je hier de vector-distance gebruiken
        overlap = len(set(current_title.split()) & set(past_context.split()))
        entropy = 1.0 - (overlap / max(len(current_title.split()), 1))
        return max(0.1, min(entropy, 0.95))

    def run_cycle(self, paper, signals):
        # --- STAP 0: DUPLICATE FILTER (Strikter dan v9.3) ---
        check = self.memory.query(query_texts=[paper.title], n_results=1)
        if check['distances'] and check['distances'][0][0] < 0.05:
            print(f"⏩ Overslaan (Reeds in database): {paper.title[:40]}")
            return False

        self.step_count += 1
        
        # --- STAP A: RECALL ---
        past_context = "Eerste integratie."
        past_coh = 1.0
        try:
            results = self.memory.query(query_texts=[paper.title], n_results=1)
            if results['documents'] and results['documents'][0]:
                past_context = results['documents'][0][0][:400]
                past_coh = results['metadatas'][0][0].get('coh', 1.0)
        except: pass

        # --- STAP B: ENTROPY & SIGNALS ---
        current_entropy = self.calculate_entropy(paper.title, past_context)
        self.last_entropy = current_entropy
        
        enhanced_signals = signals + [
            ("historical_weight", 0.5), 
            ("entropy", float(current_entropy)),
            ("cumulative_coherence", float(past_coh))
        ]
        
        base_results = self.foundation.run_full_cycle(enhanced_signals)
        metrics = base_results.get('complexity_metrics', {})
        invariants = base_results.get('invariants', [])

        # --- STAP C: SYNTHESE & OPSLAG ---
        transcendent_doc = (
            f"--- INTEGRATIE STAP {self.step_count} ---\n"
            f"CONCEPT: {paper.title}\n"
            f"CONTEXT: {paper.summary[:600]}\n"
            f"RELATIE MET VORIGE KENNIS: {past_context[:300]}...\n"
            f"SYNTHESE: Ontologie bevat nu {metrics.get('ontology_count', 1)} entiteiten."
        )

        self.memory.add(
            ids=[f"step_{self.step_count}"],
            documents=[transcendent_doc],
            metadatas=[{
                "title": paper.title[:100],
                "coh": float(base_results.get('global_synthesis_coherence', 1.0)),
                "entropy": float(current_entropy),
                "step": self.step_count
            }]
        )
        
        self.export_state(paper.title, metrics, invariants, current_entropy)
        return True

    def export_state(self, last_title, metrics, invariants, entropy):
        with open("dashboard_state.json", "w") as f:
            json.dump({
                "step": self.step_count, 
                "global_coherence": 1.0, 
                "last_paper": last_title[:50],
                "queue_size": len(self.research_queue),
                "ontology_count": metrics.get('ontology_count', 1),
                "temporal_depth": metrics.get('temporal_depth', 1),
                "coherence_stability": float(metrics.get('coherence_stability', 1.0)),
                "entropy": float(entropy),
                "invariants": invariants,
                "timestamp": time.time()
            }, f)

    def start_evolution(self):
        print(f"🚀 Evolutie actief. Stap {self.step_count}. Entropy-bewaking aan.")
        while True:
            # DIVERSITEITS-LOGICA: Als de queue leeg is of te eenzijdig
            if len(self.research_queue) < 3:
                new_topics = ["Information Geometry", "Neural Thermodynamics", "Topological Insulators"]
                self.research_queue.extend(new_topics)
                print("🌀 Diversiteits-injectie: Nieuwe onderzoeksvelden toegevoegd.")

            topic = self.research_queue.pop(0)
            print(f"📡 Analyseer: {topic} (Queue: {len(self.research_queue)})")
            
            try:
                search = arxiv.Search(query=topic, max_results=5, sort_by=arxiv.SortCriterion.Relevance)
                for paper in self.arxiv_client.results(search):
                    success = self.run_cycle(paper, [("density", 0.6)])
                    if success:
                        print(f"🔗 Gekoppeld (Entropy: {self.last_entropy:.2f}): {paper.title[:50]}")
                
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ Error: {e}"); time.sleep(5)

if __name__ == "__main__":
    MasterEngineV9_4().start_evolution()