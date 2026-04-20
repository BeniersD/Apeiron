import streamlit as st
import plotly.graph_objects as go
import json, os, time, chromadb
from chromadb.utils import embedding_functions

# --- CONFIGURATIE ---
st.set_page_config(page_title="Apeiron v10.1 | Autonomous Navigator", layout="wide", page_icon="🧠")

st.markdown("""
    <style>
    .main { background-color: #05070a; color: #e0e0e0; }
    .stMetric { background-color: #11151c; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

emb_fn = embedding_functions.DefaultEmbeddingFunction()

@st.cache_resource
def init_db():
    # Zorg dat het pad overeenkomt met je Engine
    client = chromadb.PersistentClient(path="./ai_memory")
    return client.get_or_create_collection(name="transcendent_memory", embedding_function=emb_fn)

def get_state():
    if os.path.exists("dashboard_state.json"):
        try:
            with open("dashboard_state.json", "r") as f: return json.load(f)
        except: return None
    return None

# --- UI START ---
st.title("🧠 Aperion v10.1: Autonomous Navigator")
data = get_state()

if data:
    # 1. HOOFD METRICS
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Exploratie Stap", data.get('step', 0))
    col2.metric("Ontologie Breedte", data.get('ontology_count', 1))
    
    # Research Queue met dynamische kleur-indicator
    q_size = data.get('queue_size', 0)
    col3.metric("Research Queue", q_size, delta="-10 (Schoonmaak)" if q_size == 15 else None)
    
    col4.metric("Huidige Entropy", f"{data.get('entropy', 0.5):.2f}")

    st.divider()

    # 2. VISUELE ANALYSE & ENTROPY
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.write("### 📊 Navigator Stabiliteit")
        # Dynamische schaal op basis van v10 metrics
        ont = min(data.get('ontology_count', 1) / 20, 1.0) # V10 groeit sneller
        temp = min(data.get('temporal_depth', 1) / 10, 1.0)
        stab = data.get('coherence_stability', 1.0)
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[ont, temp, stab, 0.8, ont],
            theta=['Ontologie', 'Diepte', 'Stabiliteit', 'Focus', 'Ontologie'],
            fill='toself', line_color='#00ffcc', fillcolor='rgba(0, 255, 204, 0.1)'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), template="plotly_dark", height=350)
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.write("### 🧬 Informatie Dichtheid (Entropy)")
        entropy = data.get('entropy', 0.5)
        
        if entropy < 0.25:
            st.error(f"⚠️ **KRITIEK: Herhalings-lus ({entropy:.2f})**")
            st.info("Engine initieert nu een 'Quantum Jump' naar een nieuw domein.")
        elif entropy > 0.75:
            st.success(f"🚀 **DOORBRAAK: Hoge Diversiteit ({entropy:.2f})**")
        else:
            st.warning(f"⚖️ **Navigatie Stabiel ({entropy:.2f})**")
        
        st.progress(entropy)
        
        st.divider()
        st.write("### 📡 Actuele Focus")
        st.success(f"**Analyseert nu:** {data.get('last_paper', 'Zoeken naar paden...')}")
        
        # Laat zien welke invarianten de Navigator vasthoudt
        inv = data.get('invariants', [])
        if inv:
            st.write("**Gedetecteerde Invarianten:**")
            st.caption(", ".join([f"`{i}`" for i in inv]))

# --- CHAT SECTIE ---
st.divider()
st.subheader("💬 Apeiron Deep Retrieval")
if "messages" not in st.session_state: st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Bevel de Apeiron om verbindingen te leggen..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    try:
        memory = init_db()
        results = memory.query(query_texts=[prompt], n_results=3)
        
        if results['documents'] and results['documents'][0]:
            with st.chat_message("assistant"):
                for i, doc in enumerate(results['documents'][0]):
                    title = results['metadatas'][0][i].get('title', 'Onbekend')
                    with st.expander(f"Geheugen-fragment {i+1}: {title}"):
                        st.markdown(doc)
                ans = "Synthese van autonome stappen voltooid."
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
        else:
            st.warning("Geen correlaties in autonoom geheugen.")
    except Exception as e:
        st.error(f"Geheugen-fout: {e}")

# --- AUTO-REFRESH ---
time.sleep(5)
st.rerun()