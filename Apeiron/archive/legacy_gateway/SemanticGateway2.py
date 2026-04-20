import feedparser
import numpy as np
import time
import sys
from master_v8 import MasterEngineV8 # Veronderstelt dat je vorige code MasterEngineV8 heet

class GlobalAwareEngine(MasterEngineV8):
    def __init__(self):
        super().__init__()
        self.rss_feeds = [
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://www.theguardian.com/world/rss",
            "https://news.un.org/feed/subscribe/en/news/all/rss.xml"
        ]

    def fetch_latest_news(self):
        """Haalt koppen op en zet ze om in betekenisvolle input."""
        all_titles = []
        for url in self.rss_feeds:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: # Pak de top 3 van elke bron
                all_titles.append(entry.title)
        return all_titles

    def run_live_evolution(self):
        print("🌍 Koppeling met wereldwijde datastroom actief...")
        try:
            while True:
                news_items = self.fetch_latest_news()
                
                for title in news_items:
                    # Zet tekstlengte en sentiment-ruis om in observables (L1)
                    # Hier wordt de wereld 'data' voor de 17 lagen
                    semantic_input = [
                        ("news_complexity", len(title)),
                        ("entropy", sum(ord(c) for c in title) % 100 / 10.0),
                        ("planetary_pulse", time.time() % 1)
                    ]
                    
                    # Verwerk door de 17 lagen
                    state = self.run_cycle(semantic_input)
                    
                    print(f"\n📰 Verwerkt: {title[:60]}...")
                    if self.step_count % 3 == 0:
                        self.l17.display_absolute_integration_state(state)
                    
                print("\n💤 Wachten op nieuwe wereldontwikkelingen (60s)...")
                time.sleep(60)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Gestopt. Laatste stap was {self.step_count}.")

if __name__ == "__main__":
    engine = GlobalAwareEngine()
    engine.run_live_evolution()