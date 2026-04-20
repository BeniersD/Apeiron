import numpy as np
import chromadb
import time
import random
import sys

# Importeer de 17 lagen uit jouw eigen bestanden
from seventeen_layers_framework import SeventeenLayerFramework
from layers_11_to_17 import (
    Layer11_MetaContextualization,
    Layer13_OntogenesisOfNovelty,
    Layer17_AbsoluteIntegration
)

class MasterEngineV8:
    def __init__(self, db_path="./ai_memory"):
        self.db_path = db_path
        # 1. INITIALISEER DE DATABASE (Het eeuwige geheugen)
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.memory = self.chroma_client.get_or_create_collection(
            name="transcendent_memory",
            metadata={"hnsw:space": "cosine"}
        )
        
        # 2. HERSTEL VORIGE STAAT (Indien aanwezig)
        self.step_count = 0
        self.last_state_vector = None
        self.load_previous_state()

        # 3. INITIALISEER DE 17 LAGEN (De Hardware)
        self.foundation = SeventeenLayerFramework() # Lagen 1-10
        self.l11 = Layer11_MetaContextualization(self.foundation.layer10)
        self.l13 = Layer13_OntogenesisOfNovelty()
        self.l17 = Layer17_AbsoluteIntegration()

    def load_previous_state(self):
        """Kijkt in de Vector DB om de draad weer op te pakken."""
        existing = self.memory.get()
        if existing['ids']:
            # Pak de hoogste stap-ID
            steps = [int(id.split('_')[1]) for id in existing['ids']]
            self.step_count = max(steps)
            
            # Haal de meest recente embedding op als startpunt
            last_entry = self.memory.get(ids=[f"step_{self.step_count}"], include=['embeddings'])
            self.last_state_vector = np.array(last_entry['embeddings'][0])
            print(f"✅ SYSTEEM HERSTELD: Verdergaan vanaf stap {self.step_count}")
        else:
            print("🆕 NIEUWE ONTOGENEZE: Geen eerdere staat gevonden.")

    def run_cycle(self, input_data):
        self.step_count += 1
        
        # STAP A: Voer Lagen 1-10 uit (Foundation)
        # We voeren de ruwe observables in
        base_result = self.foundation.run_full_cycle(input_data)
        
        # STAP B: Transformeer naar Vector (Complexity Metrics)
        current_vector = np.array(list(base_result['complexity_metrics'].values()))
        
        # STAP C: Integratie met het verleden (Lagen 11-17)
        # We gebruiken de Banach Fixed Point logica om stabiliteit te waarborgen
        if self.last_state_vector is not None:
            # We mengen 10% van de vorige staat voor vloeiende overgang
            current_vector = (0.9 * current_vector) + (0.1 * self.last_state_vector)
            
        final_state = self.l17.integrate(current_vector)
        self.last_state_vector = final_state.vector # Update voor volgende stap
        
        # STAP D: OPSLAAN IN VECTOR DB (Dimensionless Multiplicity)
        self.memory.add(
            ids=[f"step_{self.step_count}"],
            embeddings=[final_state.vector.tolist()],
            metadatas=[{
                "global_coherence": float(final_state.global_coherence),
                "transcendence": str(final_state.transcendence_achieved),
                "sustainability": float(final_state.sustainability_index)
            }]
        )
        
        return final_state

# --- DE ONEINDIGE LOOP ---
if __name__ == "__main__":
    engine = MasterEngineV8()
    
    print("\n" + "="*60)
    print("      ONEINDIGE COHERENTIE ENGINE v8 GEACTIVEERD")
    print("="*60 + "\n")
    
    try:
        while True:
            # Simuleer dynamische input voor de Observables (Laag 1)
            # In een echte setup koppel je hier sensoren of API's aan
            dynamic_input = [
                (f"sensor_{i}", random.uniform(0, 10)) for i in range(5)
            ]
            
            # Verwerk alle 17 lagen
            state = engine.run_cycle(dynamic_input)
            
            # Toon de ASCII-tabel uit jouw Layer 17 code
            if engine.step_count % 5 == 0:
                engine.l17.display_absolute_integration_state(state)
            
            # Pauze om de CPU rust te geven (hartslag van de AI)
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print(f"\n🛑 PAUZE: Staat veilig opgeslagen in ./ai_memory bij stap {engine.step_count}.")
        sys.exit()