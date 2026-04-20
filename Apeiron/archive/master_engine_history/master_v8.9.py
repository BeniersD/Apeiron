import numpy as np
import chromadb
from chromadb.utils import embedding_functions
import time, json, arxiv, os
from habanero import Crossref
from seventeen_layers_framework import SeventeenLayerFramework
from layers_11_to_17 import Layer11_MetaContextualization, Layer17_AbsoluteIntegration

class MasterEngineV9:
    def __init__(self, db_path="./ai_memory"):
        print("⚡ GOD MODE ACTIVE: Nexus Engine v9.0 [Exponential Expansion]...")
        
        if not os.path.exists(db_path): os.makedirs(db_path)
        
        # 1. DATABASE MET SYNC EMBEDDING
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
        self.research_queue = ["Universal Topology", "Ontological Mathematics", "Quantum Cohomology"]
        self.step_count = 0

    def run_cycle(self, paper, signals):
        self.step_count += 1
        # L1-L17 verwerking
        self.foundation.run_full_cycle(signals)
        
        # GOD MODE: We slaan rijkere metadata op voor diepere RAG-chat
        transcendent_doc = (
            f"CONCEPT: {paper.title}\n"
            f"EVIDENCE: {paper.summary}\n"
            f"META-ANALYSIS: Dit concept is geintegreerd in stap {self.step_count}. "
            f"Het vormt een integraal onderdeel van de groeiende globale ontologie."
        )

        self.memory.add(
            ids=[f"step_{self.step_count}"],
            documents=[transcendent_doc],
            metadatas=[{
                "title": paper.title[:100], 
                "author": str(paper.authors[0]) if paper.authors else "Unknown",
                "url": paper.entry_id,
                "coh": 1.0
            }]
        )
        
        self.export_state(1.0, paper.title)
        return 1.0

    def export_state(self, coh, last_title):
        with open("dashboard_state.json", "w") as f:
            json.dump({
                "step": self.step_count, 
                "global_coherence": coh, 
                "last_paper": last_title[:50],
                "queue_size": len(self.research_queue),
                "timestamp": time.time()
            }, f)

    def start_evolution(self):
        while True:
            # Als de queue leeg dreigt te raken, voeg universele constanten toe
            if not self.research_queue:
                self.research_queue = ["Category Theory", "Neural Manifolds"]
                
            topic = self.research_queue.pop(0)
            print(f"📡 Scannen: {topic}")
            
            try:
                # GOD MODE: 15 resultaten per keer in plaats van 2
                search = arxiv.Search(query=topic, max_results=15)
                for paper in self.arxiv_client.results(search):
                    coh = self.run_cycle(paper, [("complexity", 0.95)])
                    print(f"💎 Geabsorbeerd: {paper.title[:60]}")
                    
                    # Diepe Snowballing via Crossref
                    if coh > 0.8:
                        res = self.cr.works(query=paper.title, limit=3)
                        if res['message']['items']:
                            for item in res['message']['items']:
                                # Voeg nieuwe onderwerpen toe
                                for s in item.get('subject', []):
                                    if s not in self.research_queue: self.research_queue.append(s)
                
                time.sleep(1) # Minimale vertraging
            except Exception as e:
                print(f"⚠️ Waarschuwing: {e}")
                time.sleep(5)

if __name__ == "__main__":
    MasterEngineV9().start_evolution()