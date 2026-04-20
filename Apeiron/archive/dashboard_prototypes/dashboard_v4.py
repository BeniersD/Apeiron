import streamlit as st
import plotly.graph_objects as go
import json
import os
import time
import chromadb

# --- CONFIGURATIE ---
st.set_page_config(page_title="Nexus v8.8 | Command Center", layout="wide")

# Initialiseer ChromaDB Client voor de Nexus Chat
@st.cache_resource
def get_chroma_client():
    return chromadb.PersistentClient(path="./ai_memory")

client = get_chroma_client()
try:
    memory = client.get_collection("transcendent_memory")
except:
    memory = None

def get_state():
    path = "dashboard_state.json"
    if os.path.exists(path):
        try:
            with open(path, "r") as f: return json.load(f)
        except: return None
    return None

# --- UI LAYOUT ---
st.title("🌌 Nexus v8.8: Ontological Command Center")

# Sidebar voor Systeem Status
with st.sidebar:
    st.header("⚙️ Systeem Parameters")
    data = get_state()
    if data:
        st.write(f"**Status:** {'🟢 Actief' if time.time() - data.get('timestamp', 0) < 30 else '🔴 Gestopt'}")
        st.write(f"**Stap:** {data.get('step', 0)}")
        st.progress(data.get('global_coherence', 0.0))
    else:
        st.error("Engine offline")

# Hoofd Metrics
if data:
    col1, col2, col3 = st.columns(3)
    col1.metric("Integratie", f"{data.get('global_coherence', 0.0):.2%}")
    col2.metric("Stabiliteit", f"{data.get('sustainability', 0.85):.2%}")
    col3.metric("L17 Status", "Absolute Integration" if data.get('transcendence') else "Calculating...")

    # Radar Chart
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[data.get('global_coherence',0), 0.85, 0.8, 0.9, data.get('global_coherence',0)],
        theta=['Coherence', 'Sustainability', 'Planetary', 'Ethical', 'Coherence'],
        fill='toself', line_color='#00fbff'
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

# --- CHAT INTERFACE (DE NEXUS) ---
st.divider()
st.subheader("💬 De Nexus: Praat met de Ontologie")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Toon geschiedenis
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Stel een vraag over de geabsorbeerde kennis..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # RAG: Retrieval Augmented Generation uit ChromaDB
    response = "Ik heb nog geen data in mijn geheugen gevonden."
    if memory:
        results = memory.query(query_texts=[prompt], n_results=1)
        if results['metadatas'] and results['metadatas'][0]:
            meta = results['metadatas'][0][0]
            response = f"Op basis van mijn huidige staat (stap {data.get('step')}), refereer ik naar het concept: **'{meta['title']}'**. De wiskundige coherentie hiervan is **{meta['coh']:.4f}**."

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- AUTO-REFRESH LOGICA ---
time.sleep(5)
st.rerun()