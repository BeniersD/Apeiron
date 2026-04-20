import numpy as np
import chromadb
from chromadb.utils import embedding_functions
import time, json, arxiv, os
from habanero import Crossref

# Importeer je 17-lagen architectuur
from seventeen_layers_framework import SeventeenLayerFramework
from layers_11_to_17 import Layer11_MetaContextualization, Layer17_AbsoluteIntegration

class MasterEngineV9_3:
    def __init__(self, db_path="./ai_memory"):
        print("🧠 Nexus v9.3: Cumulative Memory Mode Geactiveerd...")
        
        if not os.path.exists(db_path): os.makedirs(db_path)
        
        # 1. DATABASE & EMBEDDING (Bestaande kennis laden)
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

    def _get_last_step(self):
        try: return self.memory.count()
        except: return 0

    def run_cycle(self, paper, signals):
        self.step_count += 1
        
        # --- STAP A: RECALL (Kijk terug in het geheugen) ---
        past_context = "Eerste integratie."
        past_coh = 1.0
        try:
            # Zoek naar de meest relevante eerdere kennis op basis van de huidige titel
            results = self.memory.query(query_texts=[paper.title], n_results=1)
            if results['documents'] and results['documents'][0]:
                past_context = results['documents'][0][0][:400] # Pak essentie van vorige stap
                past_coh = results['metadatas'][0][0].get('coh', 1.0)
        except: pass

        # --- STAP B: CUMULATIEVE INPUT (Verrijk de signalen) ---
        # We voegen de coherentie van het verleden toe als signaal voor de toekomst
        enhanced_signals = signals + [
            ("historical_weight", 0.5), 
            ("cumulative_coherence", float(past_coh))
        ]
        
        # Draai de 17-lagen cyclus met herinnering
        base_results = self.foundation.run_full_cycle(enhanced_signals)
        
        metrics = base_results.get('complexity_metrics', {})
        invariants = base_results.get('invariants', [])

        # --- STAP C: SYNTHESE & OPSLAG ---
        transcendent_doc = (
            f"--- INTEGRATIE STAP {self.step_count} ---\n"
            f"CONCEPT: {paper.title}\n"
            f"CONTEXT: {paper.summary[:600]}\n"
            f"RELATIE MET VORIGE KENNIS: {past_context[:300]}...\n"
            f"SYNTHESE: De ontologie bevat nu {metrics.get('ontology_count', 1)} actieve entiteiten."
        )

        self.memory.add(
            ids=[f"step_{self.step_count}"],
            documents=[transcendent_doc],
            metadatas=[{
                "title": paper.title[:100],
                "coh": float(base_results.get('global_synthesis_coherence', 1.0)),
                "step": self.step_count
            }]
        )
        
        self.export_state(paper.title, metrics, invariants)

    def export_state(self, last_title, metrics, invariants):
        with open("dashboard_state.json", "w") as f:
            json.dump({
                "step": self.step_count, 
                "global_coherence": 1.0, 
                "last_paper": last_title[:50],
                "queue_size": len(self.research_queue),
                "ontology_count": metrics.get('ontology_count', 1),
                "temporal_depth": metrics.get('temporal_depth', 1),
                "invariants": invariants,
                "timestamp": time.time()
            }, f)

    def start_evolution(self):
        print(f"🚀 Evolutie hervat vanaf stap {self.step_count}. Geheugen is actief.")
        while True:
            if not self.research_queue: self.research_queue = ["Complexity Theory"]
            topic = self.research_queue.pop(0)
            print(f"📡 Analyseer: {topic}")
            
            try:
                search = arxiv.Search(query=topic, max_results=25)
                for paper in self.arxiv_client.results(search):
                    self.run_cycle(paper, [("density", 0.6)])
                    print(f"🔗 Gekoppeld: {paper.title[:50]}")
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ Error: {e}"); time.sleep(5)

if __name__ == "__main__":
    MasterEngineV9_3().start_evolution()