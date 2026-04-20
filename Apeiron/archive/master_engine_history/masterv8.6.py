import numpy as np
import chromadb
import time
import json
import arxiv
import os
from habanero import Crossref

# Importeer jouw specifieke architectuur
from seventeen_layers_framework import SeventeenLayerFramework
from layers_11_to_17 import (
    Layer11_MetaContextualization,
    Layer17_AbsoluteIntegration
)

class MasterEngineV8:
    def __init__(self, db_path="./ai_memory"):
        print("🌌 Initialiseren Master Engine v8.6 [Definitieve Versie]...")
        
        # 1. Database Setup (Local Persistence Mode)
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.memory = self.chroma_client.get_or_create_collection(
            name="transcendent_memory",
            metadata={"hnsw:space": "cosine"}
        )
        
        # 2. Architectuur Koppeling (Chain of Command)
        self.foundation = SeventeenLayerFramework()
        self.l11 = Layer11_MetaContextualization(self.foundation)
        self.integrator = Layer17_AbsoluteIntegration(layer16=self.l11)
        
        # 3. Research Clients
        self.arxiv_client = arxiv.Client()
        self.cr = Crossref()
        self.research_queue = ["Dimensionless Multiplicity", "Complexity Theory", "Ontological Mathematics"]
        
        # 4. State Tracking
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
        base_results = self.foundation.run_full_cycle(input_signals)
        
        # Stap B: Flexibele Data Extractie (Oplossing voor de KeyError)
        # We zoeken naar de numerieke metrics in de output van je framework
        if isinstance(base_results, dict):
            # Als 'complexity_metrics' erin zit, pak die, anders pak de hele dict
            metrics = base_results.get('complexity_metrics', base_results)
        else:
            metrics = {"default": 0.5}

        # Converteer metrics naar een numerieke vector voor de hogere lagen (L11-17)
        vec_list = []
        for val in metrics.values() if isinstance(metrics, dict) else [metrics]:
            if isinstance(val, (int, float, np.number)):
                vec_list.append(float(val))
            elif isinstance(val, dict): # Dieper graven indien nodig
                for subval in val.values():
                    if isinstance(subval, (int, float, np.number)):
                        vec_list.append(float(subval))
        
        # Zorg voor een stabiele vectorlengte voor L17
        vec = np.array(vec_list) if len(vec_list) > 0 else np.array([0.5, 0.5, 0.5])
        
        # Stap C: Absolute Integratie (L17)
        state = self.integrator.integrate(vec)
        
        # Stap D: Geheugen Opslag
        self.memory.add(
            ids=[f"step_{self.step_count}"],
            embeddings=[state.vector.tolist() if hasattr(state.vector, 'tolist') else [0.5]*10],
            metadatas=[{"title": title[:100], "coh": float(state.global_coherence)}]
        )
        
        self._export_to_dashboard(state)
        return state

    def _export_to_dashboard(self, state):
        data = {
            "step": self.step_count,
            "global_coherence": float(state.global_coherence),
            "sustainability": float(state.sustainability_index) if hasattr(state, 'sustainability_index') else 0.8,
            "transcendence": bool(state.transcendence_achieved),
            "timestamp": time.time()
        }
        with open("dashboard_state.json", "w") as f:
            json.dump(data, f)

    def start_evolution(self):
        print("🚀 Evolutie Actief. Snowballing door wetenschappelijke libraries...")
        while True:
            topic = self.research_queue.pop(0) if self.research_queue else "General Systems Theory"
            print(f"\n🔍 Onderzoekend: {topic}")
            
            try:
                search = arxiv.Search(query=topic, max_results=3)
                for paper in self.arxiv_client.results(search):
                    signals = [("density", len(paper.summary)/200), ("entropy", 0.5)]
                    state = self.run_cycle(signals, title=paper.title)
                    
                    print(f"✅ L17 Geabsorbeerd: {paper.title[:50]}... [Coh: {state.global_coherence:.3f}]")
                    
                    # Snowballing via Crossref (Habanero)
                    if state.global_coherence > 0.7:
                        res = self.cr.works(query=paper.title, limit=1)
                        if res['message']['items']:
                            subjects = res['message']['items'][0].get('subject', [])
                            for s in subjects:
                                if s not in self.research_queue: self.research_queue.append(s)
                            if subjects: print(f"❄️ Snowballing Leads: {subjects}")
                
                time.sleep(2)
            except Exception as e:
                print(f"⚠️ Systeemfout in Loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    engine = MasterEngineV8()
    engine.start_evolution()