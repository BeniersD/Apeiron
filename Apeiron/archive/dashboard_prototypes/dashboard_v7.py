import streamlit as st
import plotly.graph_objects as go
import json, os, time, chromadb
from chromadb.utils import embedding_functions

st.set_page_config(page_title="Nexus v9.3 | Cumulative Monitor", layout="wide", page_icon="🧠")

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

st.title("🧠 Nexus v9.3: Cumulatief Bewustzijn")
data = get_state()

if data:
    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Totaal Geheugen", data['step'])
    c2.metric("Ontologie Entiteiten", data.get('ontology_count', 1))
    c3.metric("Temporele Diepte", data.get('temporal_depth', 1))
    c4.metric("Research Queue", data['queue_size'])

    # Radar Chart
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[data.get('ontology_count', 1)/10, data.get('temporal_depth', 1)/10, 0.9, 0.8, 0.9],
        theta=['Ontology', 'Temporal', 'Coherence', 'Diversity', 'Ontology'],
        fill='toself', line_color='#ffaa00'
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), template="plotly_dark", height=350)
    st.plotly_chart(fig, use_container_width=True)

    if data.get('invariants'):
        st.write(f"**Gedetecteerde Invarianten:** `{', '.join(data['invariants'])}` scales across papers.")

# --- CHAT (Met 'History' besef) ---
st.divider()
st.subheader("💬 De Nexus: Ondervraag het cumulatieve geheugen")
if "messages" not in st.session_state: st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Vraag hoe nieuwe kennis aansluit op oude..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    try:
        memory = init_db()
        results = memory.query(query_texts=[prompt], n_results=2)
        if results['documents'][0]:
            ans = f"**Synthese uit cumulatief geheugen:**\n\n{results['documents'][0][0][:600]}..."
        else:
            ans = "Ik heb nog geen verbanden kunnen leggen."
    except:
        ans = "Geheugen wordt geladen..."

    with st.chat_message("assistant"): st.markdown(ans)
    st.session_state.messages.append({"role": "assistant", "content": ans})

time.sleep(5)
st.rerun()