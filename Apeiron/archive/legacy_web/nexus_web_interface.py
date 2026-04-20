"""
NEXUS ULTIMATE V5.0 - WEB INTERFACE
=====================================
Real-time artikel overzicht + interactieve prompt in één!
Uitgebreid met caching, threading fix, en extra features
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import time
import json
import os
import sys
import hashlib
import base64
from pathlib import Path

# ====================================================================
# PAGE CONFIG - MOET ALS EERSTE
# ====================================================================
st.set_page_config(
    page_title="Nexus Ultimate V5.0",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================================================================
# CUSTOM CSS MET DONKERE MODUS ONDERSTEUNING
# ====================================================================
st.markdown("""
<style>
    /* Algemene styling */
    .main-header {
        font-size: 2.5rem;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2196F3;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        color: white;
        transition: transform 0.3s;
    }
    .stat-box:hover {
        transform: translateY(-5px);
    }
    .article-card {
        background: white;
        border-left: 4px solid #4CAF50;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    .article-card:hover {
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        transform: translateX(5px);
    }
    .response-box {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        white-space: pre-wrap;
        margin-top: 20px;
        border-left: 4px solid #4CAF50;
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border-bottom: 3px solid #4CAF50;
    }
    /* Donkere modus ondersteuning */
    @media (prefers-color-scheme: dark) {
        .article-card {
            background: #2d2d2d;
            color: #ffffff;
            border-left-color: #6c5ce7;
        }
        .metric-card {
            background: #2d2d2d;
            color: #ffffff;
        }
    }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# CONSTANTEN
# ====================================================================
VERSION = "5.0.0"
CACHE_DURATION = 5  # Standaard cache duur in seconden
MAX_HISTORY = 50    # Maximale chat geschiedenis
DEFAULT_PAPERS = 20 # Standaard aantal papers om te tonen

# ====================================================================
# VEILIGE DATABASE FUNCTIES
# ====================================================================

def veilige_database_query(query_func, *args, **kwargs):
    """
    Voer een database query uit met een nieuwe connectie.
    Dit is een generieke wrapper voor alle database operaties.
    """
    try:
        from document_tracker import DocumentTracker
        tracker = DocumentTracker()
        try:
            result = query_func(tracker, *args, **kwargs)
            return result
        finally:
            try:
                tracker.close()
            except:
                pass
    except Exception as e:
        st.error(f"❌ Database fout: {e}")
        return None

def get_verwerkingsgeschiedenis_veilig(limiet=100):
    """Veilige versie van get_verwerkingsgeschiedenis"""
    def _query(tracker):
        return tracker.get_verwerkingsgeschiedenis()
    
    result = veilige_database_query(_query)
    return result[:limiet] if result else []

def get_document_statistieken():
    """Haal statistieken op over verwerkte documenten"""
    def _query(tracker):
        cursor = tracker.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM verwerkte_documenten")
        totaal = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM verwerkings_geschiedenis")
        verwerkingen = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT bestandspad) FROM verwerkte_documenten")
        uniek = cursor.fetchone()[0]
        
        return {
            'totaal': totaal,
            'verwerkingen': verwerkingen,
            'uniek': uniek
        }
    
    return veilige_database_query(_query)

# ====================================================================
# NEXUS INTEGRATIE
# ====================================================================

try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from nexus_ultimate_v5 import NexusUltimateV5
    from document_tracker import DocumentTracker
    NEXUS_AVAILABLE = True
except ImportError as e:
    NEXUS_AVAILABLE = False
    st.error(f"❌ Kan Nexus niet importeren: {e}")

# ====================================================================
# SESSION STATE INITIALISATIE
# ====================================================================

def init_session_state():
    """Initialiseer alle session state variabelen"""
    
    defaults = {
        'nexus': None,
        'tracker': None,
        'auto_refresh': True,
        'last_refresh': time.time(),
        'chat_history': [],
        'dark_mode': False,
        'show_notifications': True,
        'cache': {},
        'favorite_queries': [],
        'export_format': 'json',
        'stats_history': [],
        'last_stats_update': 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ====================================================================
# HELPER FUNCTIES
# ====================================================================

def format_timestamp(timestamp):
    """Format timestamp naar leesbare tijd"""
    if not timestamp:
        return "Onbekend"
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(timestamp)[:16]

def create_download_link(data, filename, text):
    """Maak een download link voor data export"""
    if isinstance(data, (dict, list)):
        data = json.dumps(data, indent=2, default=str)
    b64 = base64.b64encode(data.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}">{text}</a>'
    return href

def init_nexus():
    """Initialiseer Nexus (als die nog niet draait)"""
    if st.session_state.nexus is None and NEXUS_AVAILABLE:
        with st.spinner("🔄 Nexus wordt gestart... Dit kan even duren..."):
            try:
                st.session_state.nexus = NexusUltimateV5()
                st.session_state.tracker = DocumentTracker()
                return True
            except Exception as e:
                st.error(f"❌ Fout bij starten Nexus: {e}")
                return False
    return st.session_state.nexus is not None

# ====================================================================
# DATABASE FUNCTIES MET CACHE
# ====================================================================

def laad_artikelen(limiet=100):
    """Laad artikelen uit database - met veilige database queries"""
    
    geschiedenis = []
    try:
        result = get_verwerkingsgeschiedenis_veilig(limiet * 2)  # Laad extra voor filtering
        if result:
            geschiedenis = result
    except Exception as e:
        st.sidebar.warning(f"⚠️ Fout bij laden: {e}")
    
    nexus_artikelen = []
    try:
        if st.session_state.nexus and hasattr(st.session_state.nexus, 'memory'):
            results = st.session_state.nexus.memory.get(limit=limiet)
            if results and 'metadatas' in results:
                nexus_artikelen = results['metadatas']
    except Exception as e:
        pass
    
    return geschiedenis[:limiet], nexus_artikelen[:limiet]

def laad_artikelen_met_cache(limiet=100, gebruik_cache=True, cache_tijd=CACHE_DURATION):
    """
    Laad artikelen met caching om database queries te beperken.
    """
    cache_key = f"artikelen_{limiet}"
    
    # Check cache
    if gebruik_cache and cache_key in st.session_state.cache:
        cache = st.session_state.cache[cache_key]
        if time.time() - cache['tijd'] < cache_tijd:
            return cache['geschiedenis'], cache['nexus_artikelen']
    
    # Laad nieuwe data
    geschiedenis, nexus_artikelen = laad_artikelen(limiet)
    
    # Sla op in cache
    st.session_state.cache[cache_key] = {
        'geschiedenis': geschiedenis,
        'nexus_artikelen': nexus_artikelen,
        'tijd': time.time()
    }
    
    return geschiedenis, nexus_artikelen

def zoek_artikelen(vraag, aantal=5):
    """Zoek relevante artikelen bij een vraag"""
    if st.session_state.nexus and hasattr(st.session_state.nexus, 'memory'):
        try:
            results = st.session_state.nexus.memory.query(
                query_texts=[vraag],
                n_results=aantal
            )
            return results
        except Exception as e:
            st.error(f"❌ Zoekfout: {e}")
            return None
    return None

def genereer_antwoord(vraag, results):
    """
    Genereer een MENSELIJK leesbaar antwoord op basis van gevonden artikelen.
    Geen ruwe data dumps, maar een vloeiend, behulpzaam antwoord.
    """
    
    if not results or not results['documents'] or not results['documents'][0]:
        return "Ik kon geen relevante artikelen vinden over dit onderwerp in mijn database."
    
    # Basis informatie
    aantal = len(results['documents'][0])
    beste_match = results['documents'][0][0]
    beste_meta = results['metadatas'][0][0]
    beste_score = max(0, min(1, 1 - results['distances'][0][0]))
    
    # ====================================================================
    # BOUW EEN MENSELIJK ANTWOORD
    # ====================================================================
    
    antwoord = f"### 💬 Antwoord op uw vraag\n\n"
    
    # Inleiding - context geven
    antwoord += f"Op basis van mijn analyse van **{aantal} relevant{'e' if aantal > 1 else ''} artikel{'en' if aantal > 1 else ''}** "
    antwoord += f"kan ik het volgende vertellen over **'{vraag}'**:\n\n"
    
    # ====================================================================
    # HET ECHTE ANTWOORD - GEBASEERD OP DE BESTE BRON
    # ====================================================================
    
    if beste_match:
        # Maak de tekst schoon (verwijder overmatige newlines)
        schone_tekst = ' '.join(beste_match.replace('\n', ' ').split())
        
        # Pak de eerste 2-3 zinnen voor een introductie
        zinnen = schone_tekst.split('. ')
        intro = '. '.join(zinnen[:2]) + '.'
        
        antwoord += f"{intro}\n\n"
        
        # Als er een duidelijke conclusie is, voeg die toe
        if len(zinnen) > 4:
            # Probeer een conclusie te vinden (laatste 2 zinnen)
            conclusie = '. '.join(zinnen[-2:]) + '.'
            if len(conclusie) < 300:  # Niet te lang
                antwoord += f"**Belangrijkste inzicht:** {conclusie}\n\n"
    
    # ====================================================================
    # KERNPUNTEN UIT HET ARTIKEL (ALS BESCHIKBAAR)
    # ====================================================================
    
    if beste_match and len(beste_match) > 500:
        antwoord += f"### 📌 Kernpunten uit het onderzoek\n\n"
        
        # Extraheer mogelijke kernpunten (zoek naar bullet points of genummerde lijsten)
        tekst = beste_match
        kernpunten = []
        
        # Zoek naar genummerde lijsten (1., 2., etc.)
        lines = tekst.split('\n')
        for line in lines[:20]:  # Alleen eerste 20 regels doorzoeken
            line = line.strip()
            if line and (line[0].isdigit() and line[1:3] in ['. ', ') ']):
                kernpunten.append(line)
        
        # Zoek naar bullet points (*, -, •)
        if not kernpunten:
            for line in lines[:20]:
                line = line.strip()
                if line and line[0] in ['*', '-', '•']:
                    kernpunten.append(line)
        
        # Als we kernpunten hebben gevonden, toon ze
        if kernpunten:
            for punt in kernpunten[:5]:  # Max 5 punten
                antwoord += f"• {punt}\n"
            antwoord += "\n"
        else:
            # Anders, toon een samenvattende alinea
            samenvatting = '. '.join(zinnen[2:5]) if len(zinnen) > 4 else '. '.join(zinnen)
            antwoord += f"{samenvatting}\n\n"
    
    # ====================================================================
    # EXTRA CONTEXT UIT ANDERE BRONNEN
    # ====================================================================
    
    if aantal > 1:
        antwoord += f"### 📚 Ook relevant\n\n"
        antwoord += f"Naast het hoofdartikel zijn er nog **{aantal-1} andere artikelen** die mogelijk interessant zijn:\n\n"
        
        for i in range(1, min(4, aantal)):  # Max 3 extra bronnen
            meta = results['metadatas'][0][i]
            titel = meta.get('title', 'Onbekend')
            relevantie = max(0, min(1, 1 - results['distances'][0][i]))
            
            antwoord += f"• **{titel[:80]}** (relevantie: {relevantie:.0%})\n"
        antwoord += "\n"
    
    # ====================================================================
    # BRONVERMELDING (INGEKORT, MENSELIJK)
    # ====================================================================
    
    antwoord += f"### 📖 Meer informatie\n\n"
    antwoord += f"Dit antwoord is voornamelijk gebaseerd op:\n"
    antwoord += f"• **Titel**: {beste_meta.get('title', 'Onbekend')}\n"
    if 'timestamp' in beste_meta:
        antwoord += f"• **Datum**: {beste_meta['timestamp'][:10]}\n"
    if 'domain' in beste_meta:
        antwoord += f"• **Vakgebied**: {beste_meta['domain']}\n"
    antwoord += f"• **Relevantie**: {beste_score:.0%}\n"
    
    # ====================================================================
    # VERVOLGVRAGEN (INTERACTIEF)
    # ====================================================================
    
    antwoord += f"\n### 💡 Vervolgvragen\n\n"
    antwoord += f"Wilt u meer weten over:\n"
    
    # Genereer relevante vervolgvragen op basis van de huidige vraag
    if 'verschil' in vraag.lower() or 'verschillen' in vraag.lower():
        antwoord += f"• De **technische implementatie** van deze architecturen?\n"
        antwoord += f"• **Praktische toepassingen** van deze technologie?\n"
        antwoord += f"• **Benchmark resultaten** die deze benaderingen vergelijken?\n"
    elif 'wat is' in vraag.lower():
        antwoord += f"• De **geschiedenis** van deze ontwikkeling?\n"
        antwoord += f"• **Toekomstige verwachtingen** voor dit vakgebied?\n"
        antwoord += f"• **Belangrijke onderzoekers** op dit gebied?\n"
    else:
        antwoord += f"• De **technische details** van dit onderzoek?\n"
        antwoord += f"• Andere **gerelateerde ontwikkelingen**?\n"
        antwoord += f"• **Specifieke toepassingen** van deze technologie?\n"
    
    return antwoord


def _genereer_vergelijkend_antwoord(vraag, results):
    """
    Speciale versie voor vergelijkende vragen (verschillen, vs, versus)
    """
    return genereer_antwoord(vraag, results)  # Gebruik dezelfde menselijke versie


def _genereer_definitie_antwoord(vraag, results):
    """
    Speciale versie voor definitie-vragen (wat is, definieer)
    """
    return genereer_antwoord(vraag, results)  # Gebruik dezelfde menselijke versie


def _genereer_uitleg_antwoord(vraag, results):
    """
    Speciale versie voor uitleg-vragen (hoe werkt, hoe functioneert)
    """
    return genereer_antwoord(vraag, results)  # Gebruik dezelfde menselijke versie


def _genereer_standaard_antwoord(vraag, results):
    """
    Standaard antwoord generator (gebruikt de menselijke versie)
    """
    return genereer_antwoord(vraag, results)

# ====================================================================
# SIDEBAR
# ====================================================================

with st.sidebar:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    with col2:
        st.title("Nexus V5.0")
    
    st.markdown(f"<small>Versie {VERSION}</small>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Systeem Status
    st.subheader("📊 Systeem Status")
    
    nexus_actief = init_nexus()
    
    if nexus_actief:
        st.success("✅ Nexus actief")
        
        if st.session_state.nexus:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Cycli", st.session_state.nexus.cycle_count)
            with col2:
                st.metric("Stappen", st.session_state.nexus.step_count)
            
            # Extra metrics in expander
            with st.expander("📈 Meer metrics"):
                if hasattr(st.session_state.nexus, 'deep_dive_count'):
                    st.metric("Deep dives", st.session_state.nexus.deep_dive_count)
                if hasattr(st.session_state.nexus, 'overgeslagen_documenten'):
                    st.metric("Overgeslagen", st.session_state.nexus.overgeslagen_documenten)
                if hasattr(st.session_state.nexus, 'transcendence_events'):
                    st.metric("Transcendentie", len(st.session_state.nexus.transcendence_events))
    else:
        st.warning("⏳ Nexus niet gestart")
        if st.button("🔄 Probeer opnieuw"):
            st.rerun()
    
    st.markdown("---")
    
    # Auto-refresh instellingen
    st.subheader("🔄 Auto-refresh")
    st.session_state.auto_refresh = st.checkbox("Automatisch verversen", value=True)
    refresh_interval = st.slider("Interval (seconden)", 2, 30, 5)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Nu verversen", use_container_width=True):
            st.session_state.last_refresh = 0
            st.rerun()
    with col2:
        if st.button("🗑️ Wis cache", use_container_width=True):
            st.session_state.cache = {}
            st.success("Cache gewist!")
            time.sleep(1)
            st.rerun()
    
    st.markdown("---")
    
    # Filters en instellingen
    st.subheader("🔍 Filters")
    zoek_term = st.text_input("Zoek in artikelen", placeholder="Typ om te filteren...")
    toon_aantal = st.slider("Aantal artikelen", 5, 100, DEFAULT_PAPERS)
    
    # Export opties
    with st.expander("📥 Export opties"):
        st.session_state.export_format = st.selectbox(
            "Format", 
            ["json", "csv", "txt"],
            format_func=lambda x: x.upper()
        )
        
        if st.button("Exporteer artikelen"):
            geschiedenis, _ = laad_artikelen_met_cache(toon_aantal, gebruik_cache=False)
            if geschiedenis:
                filename = f"nexus_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{st.session_state.export_format}"
                
                if st.session_state.export_format == "json":
                    data = json.dumps(geschiedenis, indent=2, default=str)
                elif st.session_state.export_format == "csv":
                    import pandas as pd
                    df = pd.DataFrame(geschiedenis)
                    data = df.to_csv(index=False)
                else:
                    data = "\n\n".join([str(item) for item in geschiedenis])
                
                st.markdown(create_download_link(data, filename, "📥 Download"), unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption(f"🕒 Laatste update: {datetime.now().strftime('%H:%M:%S')}")

# ====================================================================
# AUTO-REFRESH LOGICA
# ====================================================================
if st.session_state.auto_refresh and time.time() - st.session_state.last_refresh > refresh_interval:
    st.session_state.last_refresh = time.time()
    st.rerun()

# ====================================================================
# TABS
# ====================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📚 Artikelen", 
    "💬 Prompt Test", 
    "📊 Statistieken",
    "⚙️ Instellingen"
])

# ====================================================================
# TAB 1: ARTIKELEN
# ====================================================================
with tab1:
    st.markdown("<h1 class='main-header'>📚 Geladen Artikelen</h1>", unsafe_allow_html=True)
    
    # Laad artikelen met cache
    geschiedenis, nexus_artikelen = laad_artikelen_met_cache(
        limiet=toon_aantal, 
        gebruik_cache=True,
        cache_tijd=refresh_interval
    )
    
    # Filter op zoekterm
    if zoek_term and geschiedenis:
        geschiedenis = [
            item for item in geschiedenis 
            if zoek_term.lower() in str(item).lower()
        ]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totaal verwerkt", len(geschiedenis))
    with col2:
        st.metric("In Nexus memory", len(nexus_artikelen))
    with col3:
        unieke_domeinen = len(set([item.get('type', '') for item in geschiedenis if item.get('type')]))
        st.metric("Unieke domeinen", unieke_domeinen)
    
    if geschiedenis:
        # DataFrame overzicht
        st.markdown("### 📊 Overzicht")
        data = []
        for item in geschiedenis:
            data.append({
                "Tijd": format_timestamp(item.get('tijd', '')),
                "Document": os.path.basename(item.get('bestandspad', 'Onbekend'))[:40],
                "Type": item.get('type', '')[:20],
                "Details": item.get('details', '')[:50]
            })
        
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, height=300)
        
        # Detail kaarten
        st.markdown("### 📋 Details")
        
        # Sorteer opties
        sort_by = st.selectbox(
            "Sorteer op",
            ["tijd (nieuwste)", "tijd (oudste)", "type", "document"],
            key="sort_articles"
        )
        
        if sort_by == "tijd (nieuwste)":
            geschiedenis.sort(key=lambda x: x.get('tijd', ''), reverse=True)
        elif sort_by == "tijd (oudste)":
            geschiedenis.sort(key=lambda x: x.get('tijd', ''))
        elif sort_by == "type":
            geschiedenis.sort(key=lambda x: x.get('type', ''))
        else:
            geschiedenis.sort(key=lambda x: x.get('bestandspad', ''))
        
        for item in geschiedenis[:10]:
            with st.container():
                st.markdown(f"""
                <div class='article-card'>
                    <b>📄 {os.path.basename(item.get('bestandspad', 'Onbekend'))}</b><br>
                    🕒 {format_timestamp(item.get('tijd', ''))}<br>
                    🔖 Type: {item.get('type', 'onbekend')}<br>
                    📝 {item.get('details', '')}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("📭 Nog geen artikelen verwerkt. Start eerst research cycles in Nexus.")
    
    # Nexus memory artikelen
    if nexus_artikelen:
        with st.expander(f"🔬 {len(nexus_artikelen)} artikelen in Nexus memory"):
            for meta in nexus_artikelen[:10]:
                st.markdown(f"""
                - **{meta.get('title', 'Onbekend')[:80]}**
                  - Entropy: {meta.get('entropy', 0.0):.2f}
                  - Domein: {meta.get('domain', 'onbekend')}
                  - Deep dive: {"✅" if meta.get('deep_dive') else "❌"}
                """)

# ====================================================================
# TAB 2: PROMPT TEST
# ====================================================================
with tab2:
    st.markdown("<h1 class='main-header'>💬 Interactieve Prompt Test</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Favoriete queries
        if st.session_state.favorite_queries:
            with st.expander("⭐ Favoriete queries"):
                for fav in st.session_state.favorite_queries[-5:]:
                    if st.button(f"📌 {fav[:50]}...", key=f"fav_{fav}"):
                        prompt = fav
        
        # Prompt input
        prompt = st.text_area(
            "Stel je vraag aan Nexus:",
            value=prompt if 'prompt' in locals() else "",
            placeholder="Bijv: Wat zijn de nieuwste ontwikkelingen in quantum computing?",
            height=100,
            key="prompt_input"
        )
        
        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            aantal_results = st.number_input("Aantal", min_value=1, max_value=10, value=5)
        with col1_2:
            toon_bronnen = st.checkbox("Toon bronnen", value=True)
        with col1_3:
            bewaar_geschiedenis = st.checkbox("Bewaar", value=True)
        
        col_buttons = st.columns(3)
        with col_buttons[0]:
            verzend = st.button("🚀 Vraag verzenden", use_container_width=True)
        with col_buttons[1]:
            if st.button("⭐ Toevoegen aan favorieten", use_container_width=True):
                if prompt and prompt not in st.session_state.favorite_queries:
                    st.session_state.favorite_queries.append(prompt)
                    st.success("Toegevoegd aan favorieten!")
        with col_buttons[2]:
            if st.button("🗑️ Wis geschiedenis", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        
        if verzend and prompt:
            with st.spinner("🔍 Zoeken in database..."):
                results = zoek_artikelen(prompt, aantal_results)
                
                if results:
                    antwoord = genereer_antwoord(prompt, results)
                    
                    if bewaar_geschiedenis:
                        st.session_state.chat_history.append({
                            "vraag": prompt,
                            "antwoord": antwoord,
                            "tijd": datetime.now().isoformat(),
                            "results": results
                        })
                    
                    # Beperk geschiedenis
                    if len(st.session_state.chat_history) > MAX_HISTORY:
                        st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY:]
                    
                    # Toon antwoord
                    st.markdown("<div class='response-box'>" + antwoord.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
                    
                    if toon_bronnen and results and results['documents'] and results['documents'][0]:
                        with st.expander("📚 Gebruikte bronnen"):
                            for i, (doc, meta, dist) in enumerate(zip(
                                results['documents'][0],
                                results['metadatas'][0],
                                results['distances'][0]
                            )):
                                relevantie = 1 - dist
                                st.markdown(f"""
                                **{i+1}. {meta.get('title', 'Onbekend')}** (relevantie: {relevantie:.1%})
                                - 📅 {format_timestamp(meta.get('timestamp', ''))}
                                - 🏷️ Domein: {meta.get('domain', 'onbekend')}
                                - 📊 Entropy: {meta.get('entropy', 0.0):.2f}
                                - 🔬 Deep dive: {"✅" if meta.get('deep_dive') else "❌"}
                                - 📝 Snippet: {doc[:200]}...
                                """)
                else:
                    st.warning("Geen relevante artikelen gevonden.")
    
    with col2:
        st.markdown("### 📜 Geschiedenis")
        if st.session_state.chat_history:
            for i, item in enumerate(reversed(st.session_state.chat_history[-10:])):
                with st.expander(f"❓ {item['vraag'][:50]}..."):
                    st.markdown(f"**Tijd:** {format_timestamp(item['tijd'])}")
                    st.markdown("**Antwoord:**")
                    st.markdown(item['antwoord'][:300] + "...")
                    if st.button(f"Herhaal #{i}", key=f"repeat_{i}"):
                        prompt = item['vraag']
                        st.rerun()
        else:
            st.info("Nog geen vragen gesteld.")

# ====================================================================
# TAB 3: STATISTIEKEN
# ====================================================================
with tab3:
    st.markdown("<h1 class='main-header'>📊 Systeem Statistieken</h1>", unsafe_allow_html=True)
    
    if st.session_state.nexus:
        # Update statistieken elke 10 seconden
        if time.time() - st.session_state.last_stats_update > 10:
            stats = get_document_statistieken()
            if stats:
                st.session_state.stats_history.append({
                    'tijd': time.time(),
                    'data': stats
                })
            st.session_state.last_stats_update = time.time()
        
        # Hoofd metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
            st.metric("Cycli", st.session_state.nexus.cycle_count)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
            st.metric("Stappen", st.session_state.nexus.step_count)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
            st.metric("Deep Dives", st.session_state.nexus.deep_dive_count)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col4:
            st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
            st.metric("Overgeslagen", st.session_state.nexus.overgeslagen_documenten)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Document statistieken
        doc_stats = get_document_statistieken()
        if doc_stats:
            st.markdown("### 📚 Document Statistieken")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Totaal documenten", doc_stats.get('totaal', 0))
            with col2:
                st.metric("Verwerkingen", doc_stats.get('verwerkingen', 0))
            with col3:
                st.metric("Uniek", doc_stats.get('uniek', 0))
        
        # Grafieken
        st.markdown("### 📈 Verwerking over tijd")
        
        # Genereer data uit geschiedenis
        if st.session_state.stats_history:
            times = [datetime.fromtimestamp(item['tijd']) for item in st.session_state.stats_history]
            totals = [item['data'].get('totaal', 0) for item in st.session_state.stats_history]
            
            df = pd.DataFrame({
                'tijd': times,
                'documenten': totals
            })
            
            fig = px.line(df, x='tijd', y='documenten', 
                         title="Documenten verwerking over tijd")
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Simuleer data voor demo
            data = pd.DataFrame({
                'tijd': pd.date_range(start='2024-01-01', periods=20, freq='D'),
                'documenten': np.random.randint(5, 30, 20),
                'deep_dives': np.random.randint(0, 10, 20)
            })
            
            fig = px.line(data, x='tijd', y=['documenten', 'deep_dives'], 
                         title="Artikel verwerking per dag (demo data)")
            st.plotly_chart(fig, use_container_width=True)
        
        # Coherence metrics
        if hasattr(st.session_state.nexus, 'framework') and hasattr(st.session_state.nexus.framework, 'layer7'):
            st.markdown("### 🧠 Coherence Metrics")
            coherence = st.session_state.nexus.framework.layer7.synthesis.coherence_score
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=coherence,
                title={'text': "Global Coherence"},
                gauge={
                    'axis': {'range': [0, 1]},
                    'bar': {'color': "green"},
                    'steps': [
                        {'range': [0, 0.3], 'color': "red"},
                        {'range': [0.3, 0.7], 'color': "yellow"},
                        {'range': [0.7, 1], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.8
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start eerst Nexus om statistieken te zien.")
        if st.button("🚀 Start Nexus nu"):
            init_nexus()
            st.rerun()

# ====================================================================
# TAB 4: INSTELLINGEN
# ====================================================================
with tab4:
    st.markdown("<h1 class='main-header'>⚙️ Instellingen</h1>", unsafe_allow_html=True)
    
    st.markdown("### 🎨 Weergave")
    st.session_state.dark_mode = st.toggle("Donkere modus", st.session_state.dark_mode)
    st.session_state.show_notifications = st.toggle("Toon notificaties", st.session_state.show_notifications)
    
    st.markdown("### 🔧 Cache instellingen")
    col1, col2 = st.columns(2)
    with col1:
        new_cache_duration = st.number_input("Cache duur (seconden)", 
                                            min_value=1, max_value=60, 
                                            value=CACHE_DURATION)
    with col2:
        if st.button("🗑️ Wis alle cache"):
            st.session_state.cache = {}
            st.success("Cache gewist!")
    
    st.markdown("### 📊 Database")
    if st.button("📊 Toon database info"):
        stats = get_document_statistieken()
        if stats:
            st.json(stats)
    
    st.markdown("### 🧹 Opruimen")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🗑️ Wis chat geschiedenis"):
            st.session_state.chat_history = []
            st.success("Chat geschiedenis gewist!")
    with col2:
        if st.button("⭐ Wis favorieten"):
            st.session_state.favorite_queries = []
            st.success("Favorieten gewist!")
    with col3:
        if st.button("📊 Wis statistieken"):
            st.session_state.stats_history = []
            st.success("Statistieken gewist!")
    
    st.markdown("### ℹ️ Systeem informatie")
    st.markdown(f"""
    - **Versie:** {VERSION}
    - **Python:** {sys.version}
    - **Streamlit:** {st.__version__}
    - **Nexus beschikbaar:** {NEXUS_AVAILABLE}
    - **Cache items:** {len(st.session_state.cache)}
    - **Chat geschiedenis:** {len(st.session_state.chat_history)}
    - **Favorieten:** {len(st.session_state.favorite_queries)}
    """)

# ====================================================================
# FOOTER
# ====================================================================
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"© 2024 Nexus Ultimate V5.0")
with col2:
    st.caption(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col3:
    st.caption(f"📊 {len(st.session_state.cache)} items in cache")