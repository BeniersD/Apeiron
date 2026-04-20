import numpy as np
import chromadb
import time
import random
import json
import feedparser
import sys
import os

# Importeer jouw 17-lagen architectuur
from seventeen_layers_framework import SeventeenLayerFramework
from layers_11_to_17 import Layer17_AbsoluteIntegration

class MasterEngineV8:
    def __init__(self, db_path="./ai_memory"):
        print("🌌 Initialiseren van de 17-Layer Coherence Engine...")
        
        # 1. Database Setup
        self.db_path = db_path
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.memory = self.chroma_client.get_or_create_collection(
            name="transcendent_memory",
            metadata={"hnsw:space": "cosine"}
        )
        
        # 2. Herstel vorige staat
        self.step_count = self._recover_step_count()
        self.last_vector = None

        # 3. Lagen initialiseren
        self.foundation = SeventeenLayerFramework() # Lagen 1-10
        self.integrator = Layer17_AbsoluteIntegration() # Lagen 11-17
        
        # 4. Nieuwsbronnen
        self.rss_feeds = [
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://news.un.org/feed/subscribe/en/news/all/rss.xml"
        ]

    def _recover_step_count(self):
        existing = self.memory.get()
        if existing['ids']:
            return max([int(id.split('_')[1]) for id in existing['ids']])
        return 0

    def export_for_dashboard(self, state):
        """Exporteert de huidige staat naar JSON voor het Streamlit dashboard."""
        dashboard_data = {
            "step": self.step_count,
            "global_coherence": float(state.global_coherence),
            "sustainability": float(state.sustainability_index),
            "transcendence": bool(state.transcendence_achieved),
            "planetary_integration": float(state.planetary_integration),
            "ethical_convergence": float(state.ethical_convergence),
            "timestamp": time.time()
        }
        with open("dashboard_state.json", "w") as f:
            json.dump(dashboard_data, f)

    def process_news_cycle(self):
        """Hoofdloop: Nieuws -> 17 Lagen -> Geheugen."""
        print(f"🌍 Verbinding maken met wereldstromen (Stap {self.step_count})...")
        
        while True:
            for url in self.rss_feeds:
                feed = feedparser.parse(url)
                for entry in feed.entries[:3]: # Pak de nieuwste 3 koppen
                    self.step_count += 1
                    
                    # Layer 1: Observables maken van nieuws
                    input_signals = [
                        ("news_length", len(entry.title)),
                        ("news_entropy", sum(ord(c) for c in entry.title) % 100 / 10.0),
                        ("planetary_pulse", time.time() % 10)
                    ]
                    
                    # Lagen 1-10
                    base = self.foundation.run_full_cycle(input_signals)
                    current_vec = np.array(list(base['complexity_metrics'].values()))
                    
                    # Lagen 11-17
                    state = self.integrator.integrate(current_vec)
                    
                    # Opslaan in Vector DB
                    self.memory.add(
                        ids=[f"step_{self.step_count}"],
                        embeddings=[state.vector.tolist()],
                        metadatas=[{"title": entry.title[:50], "coh": float(state.global_coherence)}]
                    )
                    
                    # Dashboard & Console update
                    self.export_for_dashboard(state)
                    print(f"📰 [{self.step_count}] Verwerkt: {entry.title[:60]}...")
                    
                    time.sleep(2) # Korte pauze tussen nieuwsberichten
            
            print("\n💤 Wachten op nieuwe data (120s)...")
            time.sleep(120)

if __name__ == "__main__":
    engine = MasterEngineV8()
    try:
        engine.process_news_cycle()
    except KeyboardInterrupt:
        print(f"\n🛑 Systeem gepauzeerd op stap {engine.step_count}.")