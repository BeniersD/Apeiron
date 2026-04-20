import streamlit as st
import plotly.graph_objects as go
import json
import os
import time
import chromadb

st.set_page_config(page_title="Apeiron v8 Interface", layout="wide", initial_sidebar_state="collapsed")

# Styling
st.markdown("""<style> .main { background-color: #0e1117; color: #ffffff; } </style>""", unsafe_allow_html=True)

def get_state():
    if os.path.exists("dashboard_state.json"):
        with open("dashboard_state.json", "r") as f: return json.load(f)
    return None

# --- UI LAYOUT ---
st.title("🌌 Apeiron v8: Ontological Command Center")

data = get_state()
if data:
    # 1. Metrics Bar
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Step", data['step'])
    c2.metric("Coherence", f"{data['global_coherence']:.2%}")
    c3.metric("Sustainability", f"{data['sustainability']:.2%}")
    c4.write("✨ TRANSCENDENT" if data['transcendence'] else "🔄 EVOLVING")

    # 2. Radar Chart (17-Layers Visualization)
    fig = go.Figure()
    categories = ['Coherence', 'Sustainability', 'Planetary', 'Ethical', 'Logic']
    values = [data['global_coherence'], data['sustainability'], data['planetary'], data['ethical'], 0.85]
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', line_color='#00fbff'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

# 3. Apeiron Chat Interface
st.divider()
st.subheader("💬 The Apeiron Interface")
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Bevel de Ontologie..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    # Apeiron Memory Retrieval Logic
    client = chromadb.PersistentClient(path="./ai_memory")
    mem = client.get_collection("transcendent_memory")
    results = mem.query(query_texts=[prompt], n_results=1)
    
    response = f"Mijn huidige staat is gebaseerd op de integratie van: '{results['metadatas'][0][0]['title']}'. "
    response += f"Met een coherentie van {results['metadatas'][0][0]['coh']:.2f} adviseer ik voortzetting van de huidige koers."
    
    with st.chat_message("assistant"): st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

time.sleep(2)
st.rerun()