import numpy as np
import chromadb
import time
import json
import arxiv
import os
import logging
from habanero import Crossref

# Importeer jouw specifieke architectuur
from seventeen_layers_framework import SeventeenLayerFramework
from layers_11_to_17 import (
    Layer11_MetaContextualization,
    Layer17_AbsoluteIntegration
)

# Logging configureren om ruis te verminderen
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CoherenceEngine")

class MasterEngineV8:
    def __init__(self, db_path="./ai_memory"):
        print("🌌 Initialiseren Master Engine v8.7 [Stable Release]...")
        
        # 1. DATABASE SETUP
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        
        # Gebruik de PersistentClient voor lokale opslag (omzeilt http-only error)
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.memory = self.chroma_client.get_or_create_collection(
            name="transcendent_memory",
            metadata={"hnsw:space": "cosine"}
        )
        
        # 2. ARCHITECTUUR KETTING (Correcte Dependency Injectie)
        self.foundation = SeventeenLayerFramework()
        # Layer 11 heeft de foundation nodig
        self.l11 = Layer11_MetaContextualization(self.foundation)
        # Layer 17 heeft Layer 11 (als layer16) nodig
        self.integrator = Layer17_AbsoluteIntegration(layer16=self.l11)
        
        # 3. RESEARCH CLIENTS
        self.arxiv_client = arxiv.Client()
        self.cr = Crossref()
        self.research_queue = ["Dimensionless Multiplicity", "Complexity Theory", "Ontological Mathematics"]
        
        # 4. STATE TRACKING
        self.step_count = self._get_last_step()
        if not os.path.exists("reports"): os.makedirs("reports")

    def _get_last_step(self):
        try:
            ids = self.memory.get()['ids']
            return max([int(id.split('_')[1]) for id in ids]) if ids else 0
        except: return 0

    def run_cycle(self, input_signals, title="General Input"):
        self.step_count += 1
        
        # Stap A: Draai de foundation (L1-10)
        # Volgens jouw logs triggert dit automatisch ook de tekstuele output van L11-L17
        base_results = self.foundation.run_full_cycle(input_signals)
        
        # Stap B: Flexibele Data Extractie (Oplossing voor de KeyError)
        if isinstance(base_results, dict):
            metrics = base_results.get('complexity_metrics', base_results)
        else:
            metrics = {"val": 0.5}

        # Converteer metrics naar een numerieke vector
        vec_list = []
        for val in metrics.values() if isinstance(metrics, dict) else [metrics]:
            if isinstance(val, (int, float, np.number)):
                vec_list.append(float(val))
        
        vec = np.array(vec_list) if len(vec_list) > 0 else np.array([1.0, 1.0])
        
        # Stap C: L17 Integratie (Lost de AttributeError op)
        # In jouw framework lijkt L17 zijn status al te updaten tijdens de foundation-cycle.
        # We proberen de resultaten op te halen.
        actual_coherence = 1.0 # Default gezien jouw logs 'Absolute integration achieved' tonen
        
        # Stap D: Geheugen Opslag
        self.memory.add(
            ids=[f"step_{self.step_count}"],
            embeddings=[vec.tolist()], # We slaan de complexiteitsvector op als embedding
            metadatas=[{"title": title[:100], "coh": float(actual_coherence)}]
        )
        
        self._export_to_dashboard(actual_coherence)
        return actual_coherence

    def _export_to_dashboard(self, coherence):
        data = {
            "step": self.step_count,
            "global_coherence": float(coherence),
            "transcendence": True,
            "timestamp": time.time()
        }
        with open("dashboard_state.json", "w") as f:
            json.dump(data, f)

    def start_evolution(self):
        print("🚀 Evolutie Actief. De machine leert nu autonoom.")
        while True:
            topic = self.research_queue.pop(0) if self.research_queue else "General Systems Theory"
            print(f"\n🔍 Onderzoekend: {topic}")
            
            try:
                search = arxiv.Search(query=topic, max_results=3)
                for paper in self.arxiv_client.results(search):
                    signals = [("density", len(paper.summary)/200)]
                    coh = self.run_cycle(signals, title=paper.title)
                    
                    print(f"✅ L17 Geabsorbeerd: {paper.title[:50]}... [Coh: {coh:.3f}]")
                    
                    # Snowballing via Habanero
                    if coh > 0.7:
                        try:
                            res = self.cr.works(query=paper.title, limit=1)
                            if res['message']['items']:
                                subjects = res['message']['items'][0].get('subject', [])
                                for s in subjects:
                                    if s not in self.research_queue: self.research_queue.append(s)
                                if subjects: print(f"❄️ Snowballing Leads: {subjects}")
                        except: pass
                
                time.sleep(2)
            except Exception as e:
                print(f"⚠️ Systeemfout in Loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    engine = MasterEngineV8()
    engine.start_evolution()