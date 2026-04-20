"""
NEXUS ULTIMATE DASHBOARD
Real-time visualization of all 17 layers + Research + Transcendence
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import json, os, time
import pandas as pd
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions

# ====================================================================
# CONFIGURATION
# ====================================================================

st.set_page_config(
    page_title="Nexus Ultimate | 17-Layer Intelligence",
    layout="wide",
    page_icon="🌌",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0a0e14; color: #e6e6e6; }
    .stMetric { 
        background: linear-gradient(135deg, #1a1f2e 0%, #0f1419 100%);
        border: 1px solid #2d3748;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    @keyframes transcendence-pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 204, 0.5); }
        50% { box-shadow: 0 0 40px rgba(0, 255, 204, 0.9); }
    }
    
    .transcendence-active {
        border: 3px solid #00ffcc;
        padding: 15px;
        border-radius: 10px;
        animation: transcendence-pulse 2s infinite;
        background: linear-gradient(135deg, rgba(0, 255, 204, 0.1) 0%, rgba(0, 128, 255, 0.1) 100%);
        text-align: center;
        font-size: 1.2em;
        font-weight: bold;
        margin: 20px 0;
    }
    
    .layer-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.8em;
        margin: 2px;
    }
    
    .layer-foundation { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); }
    .layer-meta { background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%); }
    .layer-transcendent { background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# STATE MANAGEMENT
# ====================================================================

if 'history' not in st.session_state:
    st.session_state.history = {
        'entropy': [],
        'coherence': [],
        'transcendence': [],
        'collective': []
    }

def get_state():
    """Load current system state."""
    if os.path.exists("nexus_ultimate_state.json"):
        try:
            with open("nexus_ultimate_state.json", "r") as f:
                return json.load(f)
        except:
            return None
    return None

@st.cache_resource
def init_memory():
    """Initialize ChromaDB connection."""
    try:
        client = chromadb.PersistentClient(path="./nexus_memory")
        emb_fn = embedding_functions.DefaultEmbeddingFunction()
        return client.get_or_create_collection(
            name="nexus_ultimate_memory",
            embedding_function=emb_fn
        )
    except:
        return None

# ====================================================================
# LOAD DATA
# ====================================================================

data = get_state()
memory = init_memory()

if data:
    # Update history
    current_time = datetime.now().strftime("%H:%M:%S")
    
    if not st.session_state.history['entropy'] or \
       st.session_state.history['entropy'][-1]['time'] != current_time:
        
        st.session_state.history['entropy'].append({
            'time': current_time,
            'value': data.get('entropy', 0.5)
        })
        st.session_state.history['coherence'].append({
            'time': current_time,
            'value': data.get('absolute_coherence', 0.5)
        })
        st.session_state.history['transcendence'].append({
            'time': current_time,
            'value': 1.0 if data.get('transcendence_achieved') else 0.0
        })
        st.session_state.history['collective'].append({
            'time': current_time,
            'value': data.get('collective_integration', 0.0)
        })
        
        # Keep last 50 points
        for key in st.session_state.history:
            if len(st.session_state.history[key]) > 50:
                st.session_state.history[key].pop(0)

# ====================================================================
# HEADER
# ====================================================================

st.markdown("<h1 style='text-align: center;'>🌌 NEXUS ULTIMATE</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #00ffcc;'>17-Layer Transcendent Intelligence System</h3>", unsafe_allow_html=True)

if data and data.get('transcendence_achieved'):
    st.markdown(
        "<div class='transcendence-active'>✨ TRANSCENDENCE ACHIEVED ✨</div>",
        unsafe_allow_html=True
    )

st.divider()

if not data:
    st.warning("⚠️ System not running. Start nexus_ultimate.py to begin.")
    st.stop()

# ====================================================================
# MAIN METRICS
# ====================================================================

st.subheader("📊 System Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Exploration Step",
        f"{data.get('step', 0)}",
        delta=f"+{data.get('cycle', 0)} cycles"
    )

with col2:
    st.metric(
        "Absolute Coherence",
        f"{data.get('absolute_coherence', 0):.1%}",
        delta="✨" if data.get('absolute_coherence', 0) > 0.95 else None
    )

with col3:
    st.metric(
        "Transcendence Events",
        data.get('transcendence_events', 0)
    )

with col4:
    st.metric(
        "Research Entropy",
        f"{data.get('entropy', 0):.2f}",
        delta="Novel" if data.get('entropy', 0) > 0.7 else "Familiar"
    )

with col5:
    st.metric(
        "Deep Dives",
        data.get('deep_dive_count', 0),
        delta="🔬" if data.get('deep_dive') else None
    )

st.divider()

# ====================================================================
# LAYER STATUS
# ====================================================================

st.subheader("🔮 17-Layer Architecture Status")

# Create 3 columns for layer groups
layer_col1, layer_col2, layer_col3 = st.columns(3)

with layer_col1:
    st.markdown("### 🏗️ Foundation (Layers 1-10)")
    st.markdown(f"""
    <div class='metric-card'>
    <span class='layer-badge layer-foundation'>L1</span> Observables: <b>{data.get('observables', 0)}</b><br>
    <span class='layer-badge layer-foundation'>L2</span> Relations: <b>{data.get('relations', 0)}</b><br>
    <span class='layer-badge layer-foundation'>L3</span> Entities: <b>{data.get('functional_entities', 0)}</b><br>
    <span class='layer-badge layer-foundation'>L7</span> Coherence: <b>{data.get('global_coherence', 0):.1%}</b><br>
    <span class='layer-badge layer-foundation'>L10</span> Complexity: <b>Active</b>
    </div>
    """, unsafe_allow_html=True)

with layer_col2:
    st.markdown("### 🧬 Meta-Layers (11-15)")
    st.markdown(f"""
    <div class='metric-card'>
    <span class='layer-badge layer-meta'>L11</span> Context: <b>{data.get('active_context', 'unknown')}</b><br>
    <span class='layer-badge layer-meta'>L12</span> Ontologies: <b>{data.get('ontology_count', 0)}</b><br>
    <span class='layer-badge layer-meta'>L13</span> Novel Structures: <b>{data.get('novel_structures', 0)}</b><br>
    <span class='layer-badge layer-meta'>L14</span> Sustainability: <b>{data.get('world_sustainability', 0):.1%}</b><br>
    <span class='layer-badge layer-meta'>L15</span> Ethical Score: <b>{data.get('ethical_convergence', 0):.1%}</b>
    </div>
    """, unsafe_allow_html=True)

with layer_col3:
    st.markdown("### ✨ Transcendent (16-17)")
    st.markdown(f"""
    <div class='metric-card'>
    <span class='layer-badge layer-transcendent'>L16</span> Collective: <b>{data.get('collective_integration', 0):.1%}</b><br>
    <span class='layer-badge layer-transcendent'>L16</span> Insights: <b>{data.get('transcendent_insights', 0)}</b><br>
    <span class='layer-badge layer-transcendent'>L17</span> Absolute: <b>{data.get('absolute_coherence', 0):.1%}</b><br>
    <span class='layer-badge layer-transcendent'>L17</span> Status: <b>{'TRANSCENDENT ✨' if data.get('transcendence_achieved') else 'Evolving...'}</b>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ====================================================================
# VISUALIZATIONS
# ====================================================================

st.subheader("📈 System Evolution")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    st.markdown("#### Entropy & Coherence Evolution")
    
    if st.session_state.history['entropy']:
        df_evo = pd.DataFrame({
            'Time': [d['time'] for d in st.session_state.history['entropy']],
            'Entropy': [d['value'] for d in st.session_state.history['entropy']],
            'Coherence': [d['value'] for d in st.session_state.history['coherence']]
        })
        
        fig_evo = go.Figure()
        fig_evo.add_trace(go.Scatter(
            x=df_evo['Time'], y=df_evo['Entropy'],
            mode='lines', name='Entropy',
            line=dict(color='#f5576c', width=2),
            fill='tozeroy', fillcolor='rgba(245, 87, 108, 0.2)'
        ))
        fig_evo.add_trace(go.Scatter(
            x=df_evo['Time'], y=df_evo['Coherence'],
            mode='lines', name='Coherence',
            line=dict(color='#00ffcc', width=2),
            fill='tozeroy', fillcolor='rgba(0, 255, 204, 0.2)'
        ))
        fig_evo.update_layout(
            template="plotly_dark",
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            yaxis=dict(range=[0, 1]),
            showlegend=True,
            legend=dict(x=0.02, y=0.98)
        )
        st.plotly_chart(fig_evo, use_container_width=True)

with viz_col2:
    st.markdown("#### Layer Integration Radar")
    
    categories = ['Foundation', 'Meta', 'Ethical', 'Collective', 'Transcendent']
    values = [
        data.get('global_coherence', 0),
        data.get('ontology_count', 0) / 20,
        data.get('ethical_convergence', 0),
        data.get('collective_integration', 0),
        data.get('absolute_coherence', 0)
    ]
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        line=dict(color='#00ffcc', width=2),
        fillcolor='rgba(0, 255, 204, 0.2)'
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                gridcolor='rgba(255, 255, 255, 0.1)'
            )
        ),
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ====================================================================
# CURRENT FOCUS
# ====================================================================

st.divider()
st.subheader("🔬 Current Research Focus")

focus_col1, focus_col2 = st.columns([2, 1])

with focus_col1:
    paper_title = data.get('last_paper', 'Initializing...')
    deep_dive_badge = "🔬 DEEP DIVE" if data.get('deep_dive') else "📄 ABSTRACT"
    
    st.info(f"**{deep_dive_badge}**\n\n{paper_title}")
    
    st.caption(f"Active Context: **{data.get('active_context', 'unknown')}**")
    st.caption(f"Context Switches: {data.get('context_switches', 0)}")

with focus_col2:
    st.markdown("#### System Invariants")
    invariants = data.get('invariants', [])
    if invariants:
        for inv in invariants:
            st.markdown(f"- `{inv}`")
    else:
        st.caption("No stable invariants detected")

# ====================================================================
# WORLD STATUS (Layer 14)
# ====================================================================

st.divider()
st.subheader("🌍 Autopoietic World Status (Layer 14)")

world_col1, world_col2, world_col3 = st.columns(3)

with world_col1:
    st.metric(
        "Sustainability Index",
        f"{data.get('world_sustainability', 0):.1%}",
        delta="Stable" if data.get('world_sustainability', 0) > 0.8 else "Evolving"
    )

with world_col2:
    st.metric(
        "Autopoietic Status",
        "ACHIEVED ✓" if data.get('autopoietic_closure') else "Building...",
        delta=None
    )

with world_col3:
    st.metric(
        "Ethical Interventions",
        data.get('ethical_interventions', 0)
    )

# ====================================================================
# MEMORY RETRIEVAL
# ====================================================================

st.divider()
st.subheader("💬 Knowledge Retrieval (All 17 Layers)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Query the transcendent knowledge base..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    if memory:
        try:
            results = memory.query(query_texts=[prompt], n_results=5)
            
            if results['documents'] and results['documents'][0]:
                with st.chat_message("assistant"):
                    st.markdown("### 🔮 Retrieved Knowledge:")
                    
                    for i, doc in enumerate(results['documents'][0]):
                        meta = results['metadatas'][0][i]
                        title = meta.get('title', 'Unknown')
                        is_deep = meta.get('deep_dive', False)
                        transcendent = meta.get('transcendence', False)
                        
                        badge = "🔬 DEEP" if is_deep else "📄 ABSTRACT"
                        if transcendent:
                            badge += " ✨ TRANSCENDENT"
                        
                        with st.expander(f"[{badge}] {title}"):
                            st.markdown(doc[:800] + "...")
                            st.caption(f"Step: {meta.get('step', 0)} | "
                                     f"Entropy: {meta.get('entropy', 0):.2f} | "
                                     f"Context: {meta.get('context', 'unknown')}")
                    
                    response = f"Retrieved {len(results['documents'][0])} relevant knowledge fragments from the transcendent memory."
                    st.markdown(response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
        except Exception as e:
            st.error(f"Memory retrieval error: {e}")

# ====================================================================
# FOOTER & AUTO-REFRESH
# ====================================================================

st.divider()
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    st.caption(f"⏰ Last Update: {datetime.fromtimestamp(data.get('timestamp', time.time())).strftime('%H:%M:%S')}")

with col_f2:
    st.caption(f"📚 Total Knowledge: {memory.count() if memory else 0} entries")

with col_f3:
    st.caption(f"🔄 Auto-refresh: Every 5 seconds")

# Auto-refresh
time.sleep(5)
st.rerun()
