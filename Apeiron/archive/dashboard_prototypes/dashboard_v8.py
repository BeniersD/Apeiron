import streamlit as st
import plotly.graph_objects as go
import json, os, time, chromadb
from chromadb.utils import embedding_functions

# --- CONFIGURATIE ---
st.set_page_config(page_title="Nexus v9.3 | Full Detail", layout="wide", page_icon="🧠")

st.markdown("""
    <style>
    .main { background-color: #05070a; color: #e0e0e0; }
    .stMetric { background-color: #11151c; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
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

# --- UI START ---
st.title("🧠 Nexus v9.3: Deep Ontological Monitor")
data = get_state()

if data:
    # 1. HOOFD METRICS (De details die je miste)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totaal Geheugen", data.get('step', 0))
    col2.metric("Ontologie Entiteiten", data.get('ontology_count', 1))
    col3.metric("Temporele Diepte", data.get('temporal_depth', 1))
    col4.metric("Research Queue", data.get('queue_size', 0))

    st.divider()

    # 2. VISUELE ANALYSE
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.write("### 📊 Lagen Analyse (Radar)")
        # Dynamische schaal op basis van data
        ont = min(data.get('ontology_count', 1) / 10, 1.0)
        temp = min(data.get('temporal_depth', 1) / 10, 1.0)
        stab = data.get('coherence_stability', 1.0)
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[ont, temp, stab, 0.8, ont],
            theta=['Ontologie', 'Temporele Diepte', 'Stabiliteit', 'Cumulatieve Kracht', 'Ontologie'],
            fill='toself', line_color='#ffaa00', fillcolor='rgba(255, 170, 0, 0.2)'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), template="plotly_dark", height=350)
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.write("### 🧬 Systeem Invarianten")
        inv = data.get('invariants', [])
        if inv:
            for i in inv:
                st.write(f"✅ `{i}`")
        else:
            st.info("Nog geen stabiele invarianten gedetecteerd over meerdere papers.")
        
        st.write("### 📡 Actuele Focus")
        st.success(f"**Bezig met:** {data.get('last_paper', 'Zoeken...')}")

# --- CHAT SECTIE ---
st.divider()
st.subheader("💬 De Nexus Chat (Deep Memory Retrieval)")
if "messages" not in st.session_state: st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Vraag naar de cumulatieve kennis..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    try:
        memory = init_db()
        results = memory.query(query_texts=[prompt], n_results=2)
        if results['documents'][0]:
            ans = f"**Synthese uit geheugen:**\n\n{results['documents'][0][0][:600]}..."
        else:
            ans = "Ik heb deze informatie nog niet cumulatief kunnen koppelen."
    except:
        ans = "Geheugen wordt geraadpleegd..."

    with st.chat_message("assistant"): st.markdown(ans)
    st.session_state.messages.append({"role": "assistant", "content": ans})

# --- AUTO-REFRESH ---
time.sleep(5)
st.rerun()