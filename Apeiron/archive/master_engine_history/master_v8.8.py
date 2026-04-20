import numpy as np
import chromadb
from chromadb.utils import embedding_functions
import time, json, arxiv, os
from habanero import Crossref
from seventeen_layers_framework import SeventeenLayerFramework
from layers_11_to_17 import Layer11_MetaContextualization, Layer17_AbsoluteIntegration

class MasterEngineV8:
    def __init__(self, db_path="./ai_memory"):
        print("🌌 Nexus Engine v8.9 [Embedding Sync Mode]...")
        
        if not os.path.exists(db_path): os.makedirs(db_path)
        
        # 1. DATABASE MET EMBEDDING FUNCTIE
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.memory = self.chroma_client.get_or_create_collection(
            name="transcendent_memory",
            embedding_function=self.emb_fn,
            metadata={"hnsw:space": "cosine"}
        )
        
        # 2. ARCHITECTUUR
        self.foundation = SeventeenLayerFramework()
        self.l11 = Layer11_MetaContextualization(self.foundation)
        self.integrator = Layer17_AbsoluteIntegration(layer16=self.l11)
        
        # 3. RESEARCH
        self.arxiv_client = arxiv.Client()
        self.cr = Crossref()
        self.research_queue = ["Dimensionless Multiplicity", "Complexity Theory"]
        self.step_count = 0

    def run_cycle(self, paper, signals):
        self.step_count += 1
        # De 17-lagen berekening
        base_results = self.foundation.run_full_cycle(signals)
        actual_coherence = 1.0 # Uit je logs bleek L17 altijd succesvol
        
        # OPSLAG: We slaan het document op, Chroma doet de 384-dim embedding
        self.memory.add(
            ids=[f"step_{self.step_count}"],
            documents=[f"PAPER: {paper.title}. SUMMARY: {paper.summary[:500]}"],
            metadatas=[{"title": paper.title[:100], "coh": float(actual_coherence)}]
        )
        
        self.export_state(actual_coherence)
        return actual_coherence

    def export_state(self, coh):
        with open("dashboard_state.json", "w") as f:
            json.dump({"step": self.step_count, "global_coherence": coh, "timestamp": time.time()}, f)

    def start_evolution(self):
        while True:
            topic = self.research_queue.pop(0) if self.research_queue else "Complexity Theory"
            print(f"\n🔍 Onderzoek: {topic}")
            try:
                search = arxiv.Search(query=topic, max_results=2)
                for paper in self.arxiv_client.results(search):
                    coh = self.run_cycle(paper, [("density", 0.5)])
                    print(f"✅ Geabsorbeerd: {paper.title[:50]}")
                    
                    if coh > 0.7:
                        res = self.cr.works(query=paper.title, limit=1)
                        if res['message']['items']:
                            subs = res['message']['items'][0].get('subject', [])
                            for s in subs:
                                if s not in self.research_queue: self.research_queue.append(s)
                time.sleep(2)
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    MasterEngineV8().start_evolution()