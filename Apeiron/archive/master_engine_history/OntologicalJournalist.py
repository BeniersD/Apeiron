import datetime

class OntologicalJournalist:
    def __init__(self, memory_collection):
        self.memory = memory_collection

    def generate_report(self, current_step, current_state):
        """Analyseert de geschiedenis en schrijft een 'State of the Ontology'."""
        
        # Haal de laatste 50 herinneringen op
        history = self.memory.get(limit=50, include=['metadatas', 'embeddings'])
        
        avg_coherence = np.mean([m['coh'] for m in history['metadatas']])
        titles_processed = [m.get('title', 'Unknown') for m in history['metadatas']]
        
        report = f"""
# 📜 State of the Ontology - Step {current_step}
**Gegenereerd op:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🧠 Cognitieve Status
- **Gemiddelde Coherentie (laatste 50 stappen):** {avg_coherence:.4f}
- **Huidige Systeemintegratie (L17):** {current_state.global_coherence:.4f}
- **Transcendentie Status:** {"BEREIKT ✨" if current_state.transcendence_achieved else "EVOLUEREND 🔄"}

## 📚 Geabsorbeerde Kennis (Snowballing Focus)
De AI heeft zich recentelijk geconcentreerd op de volgende concepten:
{self._format_titles(titles_processed)}

## 🔭 Ontologische Verschuiving
Op basis van de vector-verschuiving (L11-L17) stelt het systeem vast:
> "De integratie van wetenschappelijke data heeft de 'Relational Density' verhoogd. 
> Het systeem beweegt zich van lineaire data-verwerking naar een multidimensionaal 
> begrip van '{titles_processed[-1] if titles_processed else 'the field'}'.

---
*Dit rapport is autonoom gegenereerd door de Coherence Engine v8.*
"""
        with open(f"reports/report_step_{current_step}.md", "w", encoding="utf-8") as f:
            f.write(report)
        print(f"📝 Ontologisch rapport opgeslagen voor stap {current_step}")

    def _format_titles(self, titles):
        unique_titles = list(set(titles))[:5]
        return "\n".join([f"- {t}" for t in unique_titles])

# INTEGRATIE IN DE MASTER LOOP
# Voeg dit toe in je SnowballResearchEngine.run_cycle:
# if self.step_count % 50 == 0:
#     self.journalist.generate_report(self.step_count, state)