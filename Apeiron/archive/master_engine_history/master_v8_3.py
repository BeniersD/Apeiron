import arxiv
from crossrefapi.crossref import Works
import numpy as np
import time
import json

# Importeer de Master Engine
from master_v8 import MasterEngineV8

class SnowballResearchEngine(MasterEngineV8):
    def __init__(self):
        super().__init__()
        self.arxiv_client = arxiv.Client()
        self.crossref = Works()
        self.research_queue = []
        self.processed_dois = set()

    def add_to_queue(self, topics):
        """Voegt nieuwe onderwerpen of titels toe aan de snowball-wachtrij."""
        for t in topics:
            if t not in self.research_queue:
                self.research_queue.append(t)

    def fetch_and_integrate_research(self, query):
        """Haalt papers op en voedt ze aan de 17 lagen."""
        print(f"🔬 Onderzoek naar: {query}")
        search = arxiv.Search(query=query, max_results=3, sort_by=arxiv.SortCriterion.Relevance)
        
        results = list(self.arxiv_client.results(search))
        for paper in results:
            # Layer 1 Input: Zet paper-metadata om in observables
            paper_complexity = len(paper.summary)
            semantic_entropy = sum(ord(c) for c in paper.title) % 100 / 10.0
            
            input_signals = [
                ("paper_density", paper_complexity / 100),
                ("semantic_weight", semantic_entropy),
                ("citation_depth", self.step_count % 10)
            ]
            
            # Verwerk door 17 lagen
            state = self.run_cycle(input_signals)
            
            print(f"📖 Geabsorbeerd: {paper.title[:60]}...")
            
            # SNOWBALL LOGIC:
            # Als dit paper de coherentie verhoogt, haal dan gerelateerde termen op via Crossref
            if state.global_coherence > 0.5:
                # We zoeken op Crossref naar onderwerpen (subjects) van dit paper
                try:
                    works = self.works.query(title=paper.title).sample(1)
                    for work in works:
                        subjects = work.get('subject', [])
                        self.add_to_queue(subjects)
                        print(f"❄️ Snowballing: Nieuwe onderwerpen gevonden: {subjects}")
                except:
                    pass
            
            self.export_for_dashboard(state)
            time.sleep(1)

    def start_infinite_research(self, seed_topic):
        self.add_to_queue([seed_topic])
        
        try:
            while True:
                if not self.research_queue:
                    print("📭 Wachtrij leeg. Terug naar basis-onderzoek...")
                    self.add_to_queue(["Artificial General Intelligence", "Ontological Mathematics"])
                
                current_topic = self.research_queue.pop(0)
                self.fetch_and_integrate_research(current_topic)
                
                # Systeem-rust om API-blocks te voorkomen
                time.sleep(5)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Onderzoek gepauzeerd. Wachtrij bevroren op {len(self.research_queue)} items.")

if __name__ == "__main__":
    # Start de engine met een fundamenteel onderwerp uit jouw paper
    engine = SnowballResearchEngine()
    engine.start_infinite_research("Dimensionless Multiplicity AI")