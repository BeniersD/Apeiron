import streamlit as st
import plotly.graph_objects as go
import json, os, time, chromadb
from chromadb.utils import embedding_functions

st.set_page_config(page_title="Nexus v8.9", layout="wide")

# EMBEDDING SYNC: Zorgt voor 384-dimensies
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

st.title("🌌 Nexus v8.9 Command Center")

# --- UI ---
data = get_state()
if data:
    c1, c2 = st.columns(2)
    c1.metric("Stap", data['step'])
    c2.metric("Coherentie", f"{data['global_coherence']:.2%}")

# --- CHATBOX ---
st.divider()
st.subheader("💬 De Nexus Chat")
if "messages" not in st.session_state: st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Vraag de Nexus wat hij heeft geleerd..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    # RAG SEARCH (Nu met 384-dim match)
    try:
        memory = init_db()
        results = memory.query(query_texts=[prompt], n_results=1)
        if results['documents'][0]:
            ans = f"Gevonden in geheugen: {results['documents'][0][0][:300]}..."
        else:
            ans = "Geen directe match gevonden."
    except Exception as e:
        ans = f"Chat Error: Er is nog niet genoeg data opgeslagen."

    with st.chat_message("assistant"): st.markdown(ans)
    st.session_state.messages.append({"role": "assistant", "content": ans})

# AUTO REFRESH
time.sleep(5)
st.rerun()