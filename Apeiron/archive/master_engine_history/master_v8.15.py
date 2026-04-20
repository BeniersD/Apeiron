import numpy as np
import chromadb
import requests
import fitz  # PyMuPDF
import io
from chromadb.utils import embedding_functions
import time, json, arxiv, os, random
from habanero import Crossref

# Behoud van jouw 17-lagen architectuur
from seventeen_layers_framework import SeventeenLayerFramework
from layers_11_to_17 import Layer11_MetaContextualization, Layer17_AbsoluteIntegration

class MasterEngineV10:
    def __init__(self, db_path="./ai_memory"):
        print("🌌 Nexus v10.2: HYBRIDE AUTONOMIE (Abstract + Deep-Dive)")
        
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
        
        # 3. AUTONOME PARAMETERS
        self.arxiv_client = arxiv.Client()
        self.cr = Crossref()
        self.research_queue = [self.get_random_seed()]
        self.step_count = self._get_last_step()
        self.last_entropy = 0.5

    def _get_last_step(self):
        try: return self.memory.count()
        except: return 0

    def get_random_seed(self):
        seeds = ["Quantum", "Relativistic", "Molecular", "Sociological", "Neural", "Topological", "Recursive"]
        targets = ["Dynamics", "Information", "Entropy", "Structure", "Evolution", "Symmetry"]
        return f"{random.choice(seeds)} {random.choice(targets)}"

    def extract_next_topics(self, paper):
        words = [w.strip("(),.;:\"") for w in paper.summary.split() if len(w) > 8]
        if len(words) < 2: return [self.get_random_seed()]
        keywords = random.sample(words, min(len(words), 2))
        return [f"{paper.primary_category} {kw}" for kw in keywords]

    def calculate_entropy(self, current_title, past_context):
        if not past_context or "Eerste" in past_context:
            return 0.8
        overlap = len(set(current_title.split()) & set(past_context.split()))
        entropy = 1.0 - (overlap / max(len(current_title.split()), 1))
        return max(0.1, min(entropy, 0.95))

    def deep_dive_analysis(self, paper_url):
        """Downloadt en analyseert de volledige PDF van een paper."""
        print(f"🔬 HYBRIDE ACTIE: Deep-Dive gestart op {paper_url}")
        try:
            response = requests.get(paper_url)
            with fitz.open(stream=io.BytesIO(response.content), filetype="pdf") as doc:
                full_text = ""
                for page in doc:
                    full_text += page.get_text()
            return full_text[:25000] # Limiet om context window te bewaken
        except Exception as e:
            print(f"⚠️ Deep-Dive mislukt: {e}")
            return None

    def run_cycle(self, paper, signals):
        # DUPLICATE FILTER
        check = self.memory.query(query_texts=[paper.title], n_results=1)
        if check['distances'] and check['distances'][0][0] < 0.05:
            print(f"⏩ Overslaan (Reeds bekend): {paper.title[:40]}")
            return False

        self.step_count += 1
        
        # RECALL
        past_context = "Eerste integratie."
        try:
            results = self.memory.query(query_texts=[paper.title], n_results=1)
            if results['documents'] and results['documents'][0]:
                past_context = results['documents'][0][0][:400]
        except: pass

        # ENTROPY BEREKENING
        current_entropy = self.calculate_entropy(paper.title, past_context)
        self.last_entropy = current_entropy
        
        # --- HYBRIDE LOGICA ---
        # Bij hoge entropy (>0.8) downloaden we de PDF voor diepere evaluatie
        analysis_content = paper.summary
        is_deep = False
        
        if current_entropy > 0.80:
            full_text = self.deep_dive_analysis(paper.pdf_url)
            if full_text:
                analysis_content = full_text
                is_deep = True

        # DRAAI JOUW 17-LAGEN MOTOR
        enhanced_signals = signals + [
            ("entropy", float(current_entropy)),
            ("deep_dive_active", 1.0 if is_deep else 0.0)
        ]
        
        base_results = self.foundation.run_full_cycle(enhanced_signals)
        metrics = base_results.get('complexity_metrics', {})

        # OPSLAG IN CHROMADB
        prefix = "🔬 [DEEP DIVE] " if is_deep else "📄 [ABSTRACT] "
        transcendent_doc = f"{prefix} STAP {self.step_count}: {paper.title}\n{analysis_content[:2000]}"
        
        self.memory.add(
            ids=[f"step_{self.step_count}"],
            documents=[transcendent_doc],
            metadatas=[{
                "title": paper.title[:100], 
                "entropy": current_entropy, 
                "deep_dive": is_deep,
                "step": self.step_count
            }]
        )
        
        self.export_state(paper.title, metrics, base_results.get('invariants', []), current_entropy, is_deep)
        return True

    def export_state(self, last_title, metrics, invariants, entropy, is_deep):
        with open("dashboard_state.json", "w") as f:
            json.dump({
                "step": self.step_count, 
                "last_paper": last_title[:50],
                "queue_size": len(self.research_queue),
                "ontology_count": metrics.get('ontology_count', 1),
                "temporal_depth": metrics.get('temporal_depth', 1),
                "coherence_stability": float(metrics.get('coherence_stability', 1.0)),
                "entropy": float(entropy),
                "deep_dive": is_deep,
                "invariants": invariants,
                "timestamp": time.time()
            }, f)

    def start_evolution(self):
        print(f"🚀 Navigator v10.2 (Hybride) actief.")
        while True:
            if len(self.research_queue) > 25:
                self.research_queue = list(set(self.research_queue[-15:]))
                print("🧹 Queue opgeschoond.")

            if self.last_entropy < 0.25 or not self.research_queue:
                jump = self.get_random_seed()
                self.research_queue.insert(0, jump)
                print(f"🌀 Quantum Jump naar: {jump}")

            topic = self.research_queue.pop(0)
            print(f"📡 Navigeert naar: {topic}")
            
            try:
                search = arxiv.Search(query=topic, max_results=3, sort_by=arxiv.SortCriterion.Relevance)
                for paper in self.arxiv_client.results(search):
                    if self.run_cycle(paper, [("density", 0.6)]):
                        new_paths = self.extract_next_topics(paper)
                        self.research_queue.extend(new_paths)
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ Error: {e}"); time.sleep(5)

if __name__ == "__main__":
    MasterEngineV10().start_evolution()