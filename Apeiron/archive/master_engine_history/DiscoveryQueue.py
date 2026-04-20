from crossrefapi.crossref import Works
import time

class SnowballingGateway:
    def __init__(self):
        self.works = Works()

    def get_related_research(self, paper_title):
        """Vindt citaties en gerelateerd werk op basis van een titel."""
        print(f"❄️ Snowballing gestart voor: {paper_title}")
        # Zoek het paper op Crossref
        query = self.works.query(title=paper_title).sample(1)
        
        related_titles = []
        for item in query:
            # We halen de titels van gerelateerde werken of referenties op
            # (In een geavanceerde versie scannen we hier de 'reference' lijst)
            subj = item.get('subject', [])
            for s in subj:
                # Zoek nieuwe papers op basis van de onderwerpen van het huidige paper
                related_titles.append(s)
        
        return list(set(related_titles)) # Unieke onderwerpen om verder te zoeken

# INTEGRATIE IN DE MASTER ENGINE
def run_snowball_evolution(self, initial_topic):
    queue = [initial_topic]
    seen = set()

    while queue:
        current_topic = queue.pop(0)
        if current_topic in seen: continue
        seen.add(current_topic)

        # 1. Haal wetenschappelijke data op (ArXiv/Crossref)
        papers = self.research_gateway.fetch_papers(query=current_topic)
        
        for paper in papers:
            # 2. Verwerk door de 17 Lagen
            state = self.process_research_cycle(paper)
            
            # 3. Snowball conditie: 
            # Als de 'Novelty' (L13) hoog is, graaf dan dieper!
            if state.global_coherence < 0.7: 
                new_leads = self.snowball_gateway.get_related_research(paper['title'])
                queue.extend(new_leads)
                print(f"📈 Snowballing breidt uit naar: {new_leads}")

            # Voorkom API blocking
            time.sleep(2)