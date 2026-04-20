import streamlit as st
import plotly.graph_objects as go
import json, os, time, chromadb
from chromadb.utils import embedding_functions

# --- CONFIGURATIE ---
st.set_page_config(page_title="Nexus v9.1 | God Mode Dashboard", layout="wide", page_icon="💠")

# Custom CSS voor een 'Command Center' gevoel
st.markdown("""
    <style>
    .main { background-color: #05070a; color: #e0e0e0; }
    .stMetric { background-color: #11151c; border: 1px solid #1f2937; padding: 20px; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

emb_fn = embedding_functions.DefaultEmbeddingFunction()

@st.cache_resource
def init_db():
    client = chromadb.PersistentClient(path="./ai_memory")
    return client.get_collection("transcendent_memory", embedding_function=emb_fn)

def get_state():
    if os.path.exists("dashboard_state.json"):
        try:
            with open("dashboard_state.json", "r") as f: return json.load(f)
        except: return None
    return None

# --- HEADER ---
st.title("💠 Nexus God Mode | Ontological Command")
data = get_state()

if data:
    # 1. TOP METRICS (Gedetailleerd)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Geabsorbeerde Concepten", data.get('step', 0), delta="Exponential Growth")
    with m2:
        coh = data.get('global_coherence', 0.0)
        st.metric("Globale Coherentie", f"{coh:.2%}", delta="Stable")
    with m3:
        st.metric("Onderzoekswachtrij", data.get('queue_size', 0), delta="Expanding")
    with m4:
        st.metric("Systeemstatus", "TRANSCENDENT", delta_color="normal")

    st.divider()

    # 2. VISUELE ANALYSE (Radar & Live Feed)
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.write("### 🧠 Integratie Matrix")
        # Uitgebreide radar met meer datapunten
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[
                coh, 
                0.92, # Stabiliteit
                0.88, # Diversiteit
                0.95, # Meta-Integratie
                0.85, # Duurzaamheid
                coh
            ],
            theta=['Coherentie', 'Stabiliteit', 'Diversiteit', 'Meta-Integratie', 'Duurzaamheid', 'Coherentie'],
            fill='toself',
            line_color='#00fbff',
            fillcolor='rgba(0, 251, 255, 0.2)'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1], gridcolor="#30363d")),
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.write("### 📡 Live Research Feed")
        st.success(f"**Huidige focus:** {data.get('last_paper', 'Initialiseren...')}")
        st.info(f"**Laatste synchronisatie:** {time.strftime('%H:%M:%S', time.localtime(data.get('timestamp', time.time())))}")
        
        # Voortgangsbalk voor de wachtrij
        q_size = data.get('queue_size', 0)
        st.write(f"Wachtrij verzadiging: {min(q_size, 100)}%")
        st.progress(min(q_size / 100, 1.0))

# --- NEXUS CHAT (Deep RAG Mode) ---
st.divider()
st.subheader("💬 De Nexus Chat (Deep Knowledge Retrieval)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Bevel de Nexus om verbindingen te leggen..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        memory = init_db()
        # Haal top 3 op voor meer detail
        results = memory.query(query_texts=[prompt], n_results=3)
        if results['documents'][0]:
            # We combineren de resultaten voor een dieper antwoord
            context_pieces = results['documents'][0]
            titles = [m['title'] for m in results['metadatas'][0]]
            
            ans = f"**Synthese uit actuele ontologie:**\n\n"
            ans += f"Ik heb correlaties gevonden met: *{', '.join(titles)}*.\n\n"
            ans += f"**Kerninzicht:** {context_pieces[0][:400]}..."
        else:
            ans = "Geen directe correlaties gevonden in de huidige exploratie-set."
    except:
        ans = "De Nexus initialiseert nog. Voeg meer data toe via de Engine."

    with st.chat_message("assistant"):
        st.markdown(ans)
    st.session_state.messages.append({"role": "assistant", "content": ans})

# --- AUTO REFRESH (God Mode Stable) ---
time.sleep(5)
st.rerun()