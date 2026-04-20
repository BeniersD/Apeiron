import numpy as np
import chromadb
from chromadb.config import Settings
import time
import json
import arxiv
from habanero import Crossref
import os

# Importeer jouw architectuur
from seventeen_layers_framework import SeventeenLayerFramework
from layers_11_to_17 import (
    Layer11_MetaContextualization,
    Layer17_AbsoluteIntegration
)

class MasterEngineV8:
    def __init__(self, db_path="./ai_memory"):
        print("🌌 Initialiseren Master Engine v8.5 (Deep Integration Mode)...")
        
        # 1. DATABASE FIX (Voorkomt de http-only client error)
        if not os.path.exists(db_path):
            os.makedirs(db_path)
            
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        
        self.memory = self.chroma_client.get_or_create_collection(
            name="transcendent_memory",
            metadata={"hnsw:space": "cosine"}
        )
        
        # 2. ARCHITECTUUR KETTING (Lost de missing positional argument op)
        # Stap A: De Fundering (Lagen 1-10)
        self.foundation = SeventeenLayerFramework()
        
        # Stap B: De brug bouwen naar L17
        # We gebruiken L11 als de meta-context voor de foundation
        self.l11 = Layer11_MetaContextualization(self.foundation)
        
        # Stap C: Layer 17 initialiseren
        # We geven de l11 mee als de 'voorganger' (layer16) die L17 verwacht
        # In jouw framework fungeert de l11/foundation keten als de input voor de absolute integratie
        self.integrator = Layer17_AbsoluteIntegration(layer16=self.l11)
        
        # 3. RESEARCH CLIENTS
        self.arxiv_client = arxiv.Client()
        self.cr = Crossref()
        self.research_queue = ["Dimensionless Multiplicity", "Ontological Mathematics", "Non-linear Coherence"]
        
        # 4. STATUS
        self.step_count = self._get_last_step()
        if not os.path.exists("reports"):
            os.makedirs("reports")

    def _get_last_step(self):
        ids = self.memory.get()['ids']
        return max([int(id.split('_')[1]) for id in ids]) if ids else 0

    def export_state(self, state):
        """Exporteert data naar het dashboard."""
        data = {
            "step": self.step_count,
            "global_coherence": float(state.global_coherence),
            "sustainability": float(state.sustainability_index),
            "transcendence": bool(state.transcendence_achieved),
            "planetary": float(state.planetary_integration),
            "ethical": float(state.ethical_convergence),
            "timestamp": time.time()
        }
        with open("dashboard_state.json", "w") as f:
            json.dump(data, f)

    def run_cycle(self, input_signals, title="General Input"):
        self.step_count += 1
        
        # Verwerking door de keten
        base_results = self.foundation.run_full_cycle(input_signals)
        # Omzetten naar vector voor de hogere lagen
        vec = np.array(list(base_results['complexity_metrics'].values()))
        
        # De absolute integratie (L17)
        state = self.integrator.integrate(vec)
        
        # Opslaan in het eeuwige geheugen
        self.memory.add(
            ids=[f"step_{self.step_count}"],
            embeddings=[state.vector.tolist()],
            metadatas=[{"title": title[:100], "coh": float(state.global_coherence)}]
        )
        
        self.export_state(state)
        return state

    def snowball_search(self, paper_title):
        """Vindt nieuwe onderzoekspaden via Habanero/Crossref."""
        try:
            res = self.cr.works(query=paper_title, limit=1)
            if res['message']['items']:
                subjects = res['message']['items'][0].get('subject', [])
                for s in subjects:
                    if s not in self.research_queue:
                        self.research_queue.append(s)
                return subjects
        except Exception as e:
            print(f"⚠️ Snowball Error: {e}")
        return []

    def start_evolution(self):
        print("🚀 Systeem is Live. Ontogenese begint nu.")
        while True:
            topic = self.research_queue.pop(0) if self.research_queue else "Complexity Theory"
            print(f"\n🔍 Onderzoek naar: {topic}")
            
            try:
                search = arxiv.Search(query=topic, max_results=2)
                for paper in self.arxiv_client.results(search):
                    # Simulatie van signalen op basis van paper-inhoud
                    signals = [
                        ("info_density", len(paper.summary)/250),
                        ("abstract_complexity", sum(ord(c) for c in paper.title) % 50 / 5.0)
                    ]
                    
                    state = self.run_cycle(signals, title=paper.title)
                    print(f"✅ Geabsorbeerd: {paper.title[:60]}... [COH: {state.global_coherence:.2f}]")
                    
                    if state.global_coherence > 0.4:
                        leads = self.snowball_search(paper.title)
                        if leads: print(f"❄️ Snowballing naar: {leads}")
                
                time.sleep(3)
            except Exception as e:
                print(f"⚠️ Loop Error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    engine = MasterEngineV8()
    engine.start_evolution()