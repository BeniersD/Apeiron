import streamlit as st
import plotly.graph_objects as go
import json, os, time, chromadb
import pandas as pd
from chromadb.utils import embedding_functions
from datetime import datetime

# --- CONFIGURATIE ---
st.set_page_config(page_title="Apeiron v10.2 | Deep-Dive Navigator", layout="wide", page_icon="🔬")

# Custom CSS voor extra flair en de "Deep Dive" pulse
st.markdown("""
    <style>
    .main { background-color: #05070a; color: #e0e0e0; }
    .stMetric { background-color: #11151c; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 255, 204, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(0, 255, 204, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 255, 204, 0); }
    }
    .deep-dive-active { 
        border: 2px solid #00ffcc; 
        padding: 10px; 
        border-radius: 5px; 
        animation: pulse 2s infinite;
        background-color: rgba(0, 255, 204, 0.1);
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

emb_fn = embedding_functions.DefaultEmbeddingFunction()

@st.cache_resource
def init_db():
    client = chromadb.PersistentClient(path="./ai_memory")
    return client.get_or_create_collection(name="transcendent_memory", embedding_function=emb_fn)

def get_state():
    if os.path.exists("dashboard_state.json"):
        try:
            with open("dashboard_state.json", "r") as f: return json.load(f)
        except: return None
    return None

# State management voor de Entropy-geschiedenis
if 'entropy_history' not in st.session_state:
    st.session_state.entropy_history = []

# --- UI START ---
data = get_state()

# Update geschiedenis
if data:
    current_time = datetime.now().strftime("%H:%M:%S")
    if not st.session_state.entropy_history or st.session_state.entropy_history[-1]['time'] != current_time:
        st.session_state.entropy_history.append({"time": current_time, "entropy": data.get('entropy', 0.5)})
        if len(st.session_state.entropy_history) > 30: # Max 30 punten
            st.session_state.entropy_history.pop(0)

# Header met Deep-Dive Status
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("🧠 Apeiron v10.2: Hybride Navigator")
with col_t2:
    if data and data.get('deep_dive'):
        st.markdown('<div class="deep-dive-active">🔬 DEEP-DIVE MODUS ACTIEF</div>', unsafe_allow_html=True)

if data:
    # 1. HOOFD METRICS
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Exploratie Stap", data.get('step', 0))
    col2.metric("Ontologie Breedte", data.get('ontology_count', 1))
    col3.metric("Research Queue", data.get('queue_size', 0), delta="-10 (Schoonmaak)" if data.get('queue_size') == 15 else None)
    col4.metric("Huidige Entropy", f"{data.get('entropy', 0.5):.2f}")

    st.divider()

    # 2. VISUELE ANALYSE & GESCHIEDENIS
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.write("### 📊 Navigator Radar")
        ont = min(data.get('ontology_count', 1) / 20, 1.0)
        temp = min(data.get('temporal_depth', 1) / 10, 1.0)
        stab = data.get('coherence_stability', 1.0)
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=[ont, temp, stab, 0.8, ont],
            theta=['Ontologie', 'Diepte', 'Stabiliteit', 'Focus', 'Ontologie'],
            fill='toself', line_color='#00ffcc', fillcolor='rgba(0, 255, 204, 0.1)'
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), template="plotly_dark", height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_radar, use_container_width=True)

    with c_right:
        st.write("### 📈 Entropy Verloop (Nieuwsgierigheid)")
        if st.session_state.entropy_history:
            df_ent = pd.DataFrame(st.session_state.entropy_history)
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=df_ent['time'], y=df_ent['entropy'], mode='lines+markers', line=dict(color='#00ffcc', width=2), fill='tozeroy'))
            fig_line.update_layout(template="plotly_dark", height=300, margin=dict(l=20, r=20, t=20, b=20), yaxis=dict(range=[0, 1]))
            st.plotly_chart(fig_line, use_container_width=True)

    st.divider()

    # 3. FOCUS & INVARIANTEN
    f_col1, f_col2 = st.columns([2, 1])
    with f_col1:
        st.write("### 📡 Actuele Focus")
        st.info(f"**Analyseert:** {data.get('last_paper', '...')}")
    with f_col2:
        st.write("### 🧬 Systeem Invarianten")
        inv = data.get('invariants', [])
        if inv:
            st.caption(", ".join([f"`{i}`" for i in inv]))
        else:
            st.write("Geen stabiele invarianten.")

# --- CHAT SECTIE ---
st.divider()
st.subheader("💬 Apeiron Deep Retrieval")
if "messages" not in st.session_state: st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Vraag de Apeiron naar de synthese..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    try:
        memory = init_db()
        results = memory.query(query_texts=[prompt], n_results=3)
        
        if results['documents'] and results['documents'][0]:
            with st.chat_message("assistant"):
                for i, doc in enumerate(results['documents'][0]):
                    meta = results['metadatas'][0][i]
                    title = meta.get('title', 'Onbekend')
                    is_deep = meta.get('deep_dive', False)
                    
                    # Badge toevoegen voor Deep-Dive bronnen
                    label = "🔬 DEEP-DIVE" if is_deep else "📄 ABSTRACT"
                    with st.expander(f"[{label}] {title}"):
                        st.markdown(doc)
                
                ans = "De synthese bevat zowel gescande abstracts als diepgaande PDF-analyses."
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
    except Exception as e:
        st.error(f"Geheugen-fout: {e}")

# --- AUTO-REFRESH ---
time.sleep(5)
st.rerun()