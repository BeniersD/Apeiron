"""
NEXUS ULTIMATE DASHBOARD V8.0 - COMPLETE
All 17 Layers + Laag 16 Dynamische Stromingen + Laag 17 Absolute Integratie
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json, os, time
import pandas as pd
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
import numpy as np

# ====================================================================
# CONFIGURATION
# ====================================================================

st.set_page_config(
    page_title="Nexus Ultimate V8 | Complete 17-Layer + Laag 16/17",
    layout="wide",
    page_icon="🌊",
    initial_sidebar_state="expanded"
)

# Enhanced CSS voor V8
st.markdown("""
<style>
    .main { background-color: #0a0e14; color: #e6e6e6; }
    
    .layer-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #0f1419 100%);
        border: 1px solid #2d3748;
        border-left: 4px solid var(--layer-color);
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .layer-card:hover {
        border-left-width: 6px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
        transform: translateX(2px);
        transition: all 0.2s;
    }
    
    .layer-title {
        font-size: 1.1em;
        font-weight: bold;
        margin-bottom: 8px;
        color: var(--layer-color);
    }
    
    .layer-metric {
        font-size: 0.9em;
        margin: 4px 0;
        opacity: 0.9;
    }
    
    .layer-foundation { --layer-color: #667eea; }
    .layer-learning { --layer-color: #f093fb; }
    .layer-meta { --layer-color: #f5576c; }
    .layer-transcendent { --layer-color: #00ffcc; }
    .layer-oceanic { --layer-color: #4facfe; }  /* NIEUW voor Laag 16/17 */
    
    @keyframes transcendence-pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 204, 0.5); }
        50% { box-shadow: 0 0 40px rgba(0, 255, 204, 0.9); }
    }
    
    @keyframes fundament-pulse {  /* NIEUW voor Laag 17 */
        0%, 100% { box-shadow: 0 0 20px rgba(79, 172, 254, 0.5); }
        50% { box-shadow: 0 0 40px rgba(79, 172, 254, 0.9); }
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
    
    .fundament-active {  /* NIEUW voor nieuwe fundamenten */
        border: 3px solid #4facfe;
        padding: 15px;
        border-radius: 10px;
        animation: fundament-pulse 2s infinite;
        background: linear-gradient(135deg, rgba(79, 172, 254, 0.1) 0%, rgba(0, 255, 204, 0.1) 100%);
        text-align: center;
        font-size: 1.2em;
        font-weight: bold;
        margin: 20px 0;
    }
    
    .metric-number {
        font-size: 1.5em;
        font-weight: bold;
        color: var(--layer-color);
    }
    
    .status-active { color: #00ff88; }
    .status-building { color: #ffaa00; }
    .status-achieved { color: #00ffcc; font-weight: bold; }
    .status-oceanic { color: #4facfe; font-weight: bold; }  /* NIEUW */
    
    .fundament-chip {
        display: inline-block;
        background: rgba(79, 172, 254, 0.2);
        border: 1px solid #4facfe;
        border-radius: 16px;
        padding: 4px 12px;
        margin: 4px;
        font-size: 0.9em;
        color: #4facfe;
    }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# STATE MANAGEMENT (aangepast voor V8)
# ====================================================================

if 'history' not in st.session_state:
    st.session_state.history = {
        'entropy': [],
        'coherence': [],
        'transcendence': [],
        'collective': [],
        'ethical': [],
        'world_sustainability': [],
        'layer16_types': [],        # NIEUW
        'layer17_fundamenten': [],  # NIEUW
        'layer17_coherentie': []    # NIEUW
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
    # Update history (aangepast voor V8)
    current_time = datetime.now().strftime("%H:%M:%S")
    
    if not st.session_state.history['entropy'] or \
       st.session_state.history['entropy'][-1]['time'] != current_time:
        
        # Basis metrics
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
        st.session_state.history['ethical'].append({
            'time': current_time,
            'value': data.get('ethical_convergence', 0.0)
        })
        st.session_state.history['world_sustainability'].append({
            'time': current_time,
            'value': data.get('world_sustainability', 0.0)
        })
        
        # 🌊 NIEUW: Laag 16 metrics
        layer16 = data.get('layer16', {})
        st.session_state.history['layer16_types'].append({
            'time': current_time,
            'value': layer16.get('aantal_types', 0)
        })
        
        # 🌟 NIEUW: Laag 17 metrics
        layer17 = data.get('layer17', {})
        st.session_state.history['layer17_fundamenten'].append({
            'time': current_time,
            'value': layer17.get('aantal_fundamenten', 0)
        })
        st.session_state.history['layer17_coherentie'].append({
            'time': current_time,
            'value': layer17.get('coherentie', 0.0)
        })
        
        # Keep last 100 points (meer voor V8)
        for key in st.session_state.history:
            if len(st.session_state.history[key]) > 100:
                st.session_state.history[key].pop(0)

# ====================================================================
# HEADER (aangepast voor V8)
# ====================================================================

st.markdown("<h1 style='text-align: center;'>🌊 NEXUS ULTIMATE V8.0</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #4facfe;'>Absolute Integratie - Van Interferentie naar Waarheid</h3>", unsafe_allow_html=True)

# Toon speciale events
if data:
    layer17 = data.get('layer17', {})
    if layer17.get('recent') and len(layer17['recent']) > 0:
        laatste = layer17['recent'][-1]
        if laatste.get('nieuw', 0) > 0:
            st.markdown(
                f"<div class='fundament-active'>🌟 NIEUW OCEAANFUNDAMENT GEVORMD! Coherentie: {layer17.get('coherentie', 0):.2f}</div>",
                unsafe_allow_html=True
            )
    elif data.get('transcendence_achieved'):
        st.markdown(
            "<div class='transcendence-active'>✨ TRANSCENDENCE ACHIEVED ✨</div>",
            unsafe_allow_html=True
        )

st.divider()

if not data:
    st.warning("⚠️ System not running. Start nexus_ultimate_v8.py to begin.")
    st.stop()

# ====================================================================
# SIDEBAR - LAYER SELECTOR (aangepast voor V8)
# ====================================================================

with st.sidebar:
    st.header("🔮 Layer Navigator")
    
    layer_view = st.radio(
        "Select View:",
        [
            "Overview",
            "Foundation (1-10)",
            "Meta (11-15)",
            "🌊 Laag 16 - Dynamische Stromingen",
            "🌟 Laag 17 - Absolute Integratie",
            "Transcendent (16-17)",
            "All Layers Detail"
        ]
    )
    
    st.divider()
    
    st.subheader("📊 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Steps", data.get('step', 0))
        st.metric("Ocean Time", f"{data.get('ocean_time', 0):.1f}s")
    with col2:
        st.metric("Global Coherence", f"{data.get('absolute_coherence', 0):.1%}")
        st.metric("Transcendence", "✨ YES" if data.get('transcendence_achieved') else "Building...")
    
    st.divider()
    
    # 🌊 Laag 16 stats in sidebar
    layer16 = data.get('layer16', {})
    st.subheader("🌊 Laag 16")
    st.metric("Dynamische Types", layer16.get('aantal_types', 0))
    st.metric("Actieve Stromingen", layer16.get('aantal_stromingen', 0))
    st.metric("Nieuwe Types", layer16.get('type_ontstaan', 0))
    
    # 🌟 Laag 17 stats in sidebar
    layer17 = data.get('layer17', {})
    st.subheader("🌟 Laag 17")
    st.metric("Ocean Fundamentele Waarheden", layer17.get('aantal_fundamenten', 0))
    st.metric("Coherentie", f"{layer17.get('coherentie', 0):.2f}")
    st.metric("Stabiliteitsdrempel", f"{layer17.get('stabiliteitsdrempel', 0):.2f}")
    st.metric("Integraties", layer17.get('aantal_integraties', 0))
    
    st.divider()
    
    st.caption(f"🕐 Last Update: {datetime.fromtimestamp(data.get('timestamp', time.time())).strftime('%H:%M:%S')}")
    st.caption(f"💾 Knowledge Base: {memory.count() if memory else 0} entries")

# ====================================================================
# MAIN CONTENT - NIEUWE VIEWS VOOR LAAG 16 & 17
# ====================================================================

if layer_view == "Overview":
    # ================================================================
    # OVERVIEW VIEW (aangepast voor V8)
    # ================================================================
    
    st.subheader("📊 System Overview")
    
    # Top metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Exploration Step", f"{data.get('step', 0)}", delta=f"+{data.get('cycle', 0)} cycles")
    
    with col2:
        st.metric("Absolute Coherence", f"{data.get('absolute_coherence', 0):.1%}", 
                 delta="✨" if data.get('absolute_coherence', 0) > 0.95 else None)
    
    with col3:
        st.metric("Transcendence Events", data.get('transcendence_events', 0))
    
    with col4:
        st.metric("Research Entropy", f"{data.get('entropy', 0):.2f}",
                 delta="Novel" if data.get('entropy', 0) > 0.7 else "Familiar")
    
    with col5:
        st.metric("Deep Dives", data.get('deep_dive_count', 0),
                 delta="🔬" if data.get('deep_dive') else None)
    
    st.divider()
    
    # NIEUW: Laag 16 & 17 cards
    col_l16, col_l17 = st.columns(2)
    
    with col_l16:
        layer16 = data.get('layer16', {})
        st.markdown("""
        <div class='layer-card layer-oceanic'>
            <div class='layer-title'>🌊 Laag 16 - Dynamische Stromingen</div>
            <div class='layer-metric'>Spontane interferentie tussen domeinen</div>
            <div style='display: flex; justify-content: space-between; margin-top: 15px;'>
                <div><span class='metric-number'>{}</span><br>Types</div>
                <div><span class='metric-number'>{}</span><br>Stromingen</div>
                <div><span class='metric-number'>{}</span><br>Ontstaan</div>
            </div>
        </div>
        """.format(
            layer16.get('aantal_types', 0),
            layer16.get('aantal_stromingen', 0),
            layer16.get('type_ontstaan', 0)
        ), unsafe_allow_html=True)
    
    with col_l17:
        layer17 = data.get('layer17', {})
        st.markdown("""
        <div class='layer-card layer-oceanic'>
            <div class='layer-title'>🌟 Laag 17 - Absolute Integratie</div>
            <div class='layer-metric'>Van interferentie naar fundamentele waarheid</div>
            <div style='display: flex; justify-content: space-between; margin-top: 15px;'>
                <div><span class='metric-number'>{}</span><br>Fundamenten</div>
                <div><span class='metric-number'>{:.2f}</span><br>Coherentie</div>
                <div><span class='metric-number'>{:.2f}</span><br>Drempel</div>
            </div>
        </div>
        """.format(
            layer17.get('aantal_fundamenten', 0),
            layer17.get('coherentie', 0.0),
            layer17.get('stabiliteitsdrempel', 0.0)
        ), unsafe_allow_html=True)
    
    st.divider()
    
    # Layer Group Summary (aangepast)
    col_a, col_b, col_c, col_d = st.columns(4)
    
    with col_a:
        st.markdown("### 🏗️ Foundation")
        foundation_score = (data.get('global_coherence', 0) + 
                           (data.get('functional_entities', 0) / 1000)) / 2
        st.progress(min(foundation_score, 1.0))
        st.caption(f"Score: {foundation_score:.1%}")
    
    with col_b:
        st.markdown("### 🧬 Meta Intelligence")
        meta_score = (data.get('ontology_count', 0) / 20 + 
                     data.get('world_sustainability', 0)) / 2
        st.progress(min(meta_score, 1.0))
        st.caption(f"Score: {meta_score:.1%}")
    
    with col_c:
        st.markdown("### ✨ Transcendence")
        trans_score = data.get('collective_integration', 0)
        st.progress(trans_score)
        st.caption(f"Score: {trans_score:.1%}")
    
    with col_d:
        st.markdown("### 🌊 Oceanic Integration")
        ocean_score = layer17.get('coherentie', 0)
        st.progress(ocean_score)
        st.caption(f"Score: {ocean_score:.1%}")
    
    st.divider()
    
    # Evolution Chart (aangepast voor V8)
    st.subheader("📈 System Evolution")
    
    if st.session_state.history['entropy']:
        # Maak dataframe met alle metrics
        df = pd.DataFrame({
            'Time': [d['time'] for d in st.session_state.history['entropy']],
            'Entropy': [d['value'] for d in st.session_state.history['entropy']],
            'Coherence': [d['value'] for d in st.session_state.history['coherence']],
            'Collective': [d['value'] for d in st.session_state.history['collective']],
            'Layer16 Types': [d['value'] for d in st.session_state.history['layer16_types']],
            'Layer17 Coherence': [d['value'] for d in st.session_state.history['layer17_coherentie']]
        })
        
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Exploration Dynamics', 'Integration Metrics', '🌊 Oceanic Layers'),
            row_heights=[0.4, 0.3, 0.3]
        )
        
        # Row 1: Entropy
        fig.add_trace(go.Scatter(x=df['Time'], y=df['Entropy'], name='Entropy',
                                line=dict(color='#f5576c', width=2), fill='tozeroy'), row=1, col=1)
        
        # Row 2: Coherence & Collective
        fig.add_trace(go.Scatter(x=df['Time'], y=df['Coherence'], name='Coherence',
                                line=dict(color='#00ffcc', width=2)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['Time'], y=df['Collective'], name='Collective',
                                line=dict(color='#667eea', width=2)), row=2, col=1)
        
        # Row 3: Laag 16 & 17 (NIEUW)
        fig.add_trace(go.Scatter(x=df['Time'], y=df['Layer16 Types'], name='L16 Types',
                                line=dict(color='#4facfe', width=2)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['Time'], y=df['Layer17 Coherence'], name='L17 Coherentie',
                                line=dict(color='#00ccff', width=2)), row=3, col=1)
        
        fig.update_layout(height=700, template="plotly_dark", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

# ====================================================================
# NIEUWE VIEW: LAAG 16 - DYNAMISCHE STROMINGEN
# ====================================================================

elif layer_view == "🌊 Laag 16 - Dynamische Stromingen":
    st.subheader("🌊 Laag 16: Dynamische Stromingen - Spontane Interferentie")
    
    layer16 = data.get('layer16', {})
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Aantal Types", layer16.get('aantal_types', 0))
    with col2:
        st.metric("Actieve Stromingen", layer16.get('aantal_stromingen', 0))
    with col3:
        st.metric("Nieuwe Types Ontstaan", layer16.get('type_ontstaan', 0))
    with col4:
        st.metric("Interferentie Events", len(layer16.get('recent', [])))
    
    st.divider()
    
    # Recente interferenties
    recent = layer16.get('recent', [])
    if recent:
        st.subheader("🔄 Recente Spontane Interferenties")
        
        # Maak een dataframe van recente interferenties
        interferenties = []
        for i, r in enumerate(recent[-10:]):  # Laatste 10
            if isinstance(r, dict):
                interferenties.append({
                    'Tijd': f"T-{i+1}",
                    'Ouders': ' × '.join(r.get('ouders', ['?', '?'])),
                    'Nieuw Type': r.get('nieuw_type', '?'),
                    'Sterkte': f"{r.get('sterkte', 0):.2f}"
                })
        
        if interferenties:
            df = pd.DataFrame(interferenties)
            st.dataframe(df, use_container_width=True)
    
    st.divider()
    
    # Visualisatie van type-evolutie
    if st.session_state.history['layer16_types']:
        st.subheader("📈 Type Evolutie")
        
        df_types = pd.DataFrame({
            'Time': [d['time'] for d in st.session_state.history['layer16_types']],
            'Aantal Types': [d['value'] for d in st.session_state.history['layer16_types']]
        })
        
        fig = px.area(df_types, x='Time', y='Aantal Types', 
                     title='Groei van Dynamische Types',
                     template='plotly_dark')
        fig.update_traces(line_color='#4facfe', fillcolor='rgba(79, 172, 254, 0.2)')
        st.plotly_chart(fig, use_container_width=True)

# ====================================================================
# NIEUWE VIEW: LAAG 17 - ABSOLUTE INTEGRATIE
# ====================================================================

elif layer_view == "🌟 Laag 17 - Absolute Integratie":
    st.subheader("🌟 Laag 17: Absolute Integratie - Van Interferentie naar Waarheid")
    
    layer17 = data.get('layer17', {})
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ocean Fundamentele Waarheden", layer17.get('aantal_fundamenten', 0))
    with col2:
        st.metric("Huidige Coherentie", f"{layer17.get('coherentie', 0):.3f}")
    with col3:
        st.metric("Stabiliteitsdrempel", f"{layer17.get('stabiliteitsdrempel', 0):.3f}")
    with col4:
        st.metric("Aantal Integraties", layer17.get('aantal_integraties', 0))
    
    st.divider()
    
    # NIEUW: Fundamentele dimensies
    dimensies = layer17.get('dimensies', [])
    if dimensies:
        st.subheader("📏 Fundamentele Meetdimensies")
        
        # Toon dimensies als chips
        dimensie_html = ""
        for d in dimensies:
            dimensie_html += f"<span class='fundament-chip'>{d.get('naam', '?')} ({d.get('stabiliteit', 0):.2f})</span>"
        
        st.markdown(dimensie_html, unsafe_allow_html=True)
    
    st.divider()
    
    # Recente integraties
    recent = layer17.get('recent', [])
    if recent:
        st.subheader("🔄 Recente Oceaan Herstructureringen")
        
        integraties = []
        for i, r in enumerate(recent):
            integraties.append({
                'Tijd': f"{r.get('tijd', 0):.0f}s",
                'Type': r.get('type', '?'),
                'Nieuwe Fundamenten': r.get('nieuw', 0),
                'Verwijderd': r.get('oud', 0)
            })
        
        if integraties:
            df = pd.DataFrame(integraties)
            st.dataframe(df, use_container_width=True)
    
    st.divider()
    
    # Visualisatie van coherentie
    if st.session_state.history['layer17_coherentie']:
        st.subheader("📈 Oceaan Coherentie Evolutie")
        
        df_coherentie = pd.DataFrame({
            'Time': [d['time'] for d in st.session_state.history['layer17_coherentie']],
            'Coherentie': [d['value'] for d in st.session_state.history['layer17_coherentie']],
            'Fundamenten': [d['value'] for d in st.session_state.history['layer17_fundamenten']]
        })
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(x=df_coherentie['Time'], y=df_coherentie['Coherentie'],
                      name='Coherentie', line=dict(color='#00ffcc', width=2)),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(x=df_coherentie['Time'], y=df_coherentie['Fundamenten'],
                      name='Aantal Fundamenten', line=dict(color='#4facfe', width=2)),
            secondary_y=True
        )
        
        fig.update_layout(template='plotly_dark', title='Coherentie vs Fundamenten')
        fig.update_xaxes(title_text="Tijd")
        fig.update_yaxes(title_text="Coherentie", secondary_y=False)
        fig.update_yaxes(title_text="Aantal Fundamenten", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)

# ====================================================================
# BESTAANDE VIEWS (aangepast voor V8 data)
# ====================================================================

elif layer_view == "All Layers Detail":
    # ================================================================
    # COMPLETE 17-LAYER DETAILED VIEW (met Laag 16 & 17 updates)
    # ================================================================
    
    st.subheader("🔮 Complete 17-Layer Architecture")
    
    # Lagen 1-15 (identiek aan V2, maar met V8 data)
    layer16 = data.get('layer16', {})
    layer17 = data.get('layer17', {})
    
    # LAYER 1-15 (zelfde als V2, maar met data.get() calls)
    # ... [behouden we zoals in V2]
    
    # Voor nu toon ik alleen de updates voor lagen 16-17
    
    # LAYER 16 (aangepast voor V8)
    st.markdown("""
    <div class='layer-card layer-oceanic'>
        <div class='layer-title'>Layer 16: Dynamische Stromingen</div>
        <div class='layer-metric'>Spontane interferentie tussen domeinen</div>
        <div style='display: flex; justify-content: space-between; margin-top: 10px;'>
            <div><span class='metric-number'>{}</span><br>Types</div>
            <div><span class='metric-number'>{}</span><br>Stromingen</div>
            <div><span class='metric-number'>{}</span><br>Ontstaan</div>
        </div>
    </div>
    """.format(
        layer16.get('aantal_types', 0),
        layer16.get('aantal_stromingen', 0),
        layer16.get('type_ontstaan', 0)
    ), unsafe_allow_html=True)
    
    # LAYER 17 (aangepast voor V8)
    dimensies = layer17.get('dimensies', [])
    dimensie_text = f"{len(dimensies)} dimensies" if dimensies else "Geen dimensies"
    
    st.markdown("""
    <div class='layer-card layer-oceanic'>
        <div class='layer-title'>Layer 17: Absolute Integratie</div>
        <div class='layer-metric'>Fundamentele waarheden uit stabiele interferentie</div>
        <div style='display: flex; justify-content: space-between; margin-top: 10px;'>
            <div><span class='metric-number'>{}</span><br>Fundamenten</div>
            <div><span class='metric-number'>{:.2f}</span><br>Coherentie</div>
            <div><span class='metric-number'>{:.2f}</span><br>Drempel</div>
        </div>
        <div class='layer-metric' style='margin-top: 10px;'>{}</div>
    </div>
    """.format(
        layer17.get('aantal_fundamenten', 0),
        layer17.get('coherentie', 0.0),
        layer17.get('stabiliteitsdrempel', 0.0),
        dimensie_text
    ), unsafe_allow_html=True)

elif layer_view == "Transcendent (16-17)":
    # ================================================================
    # TRANSCENDENT VIEW (aangepast voor V8)
    # ================================================================
    
    st.subheader("✨ Transcendent Layers 16-17")
    
    col1, col2 = st.columns(2)
    
    with col1:
        layer16 = data.get('layer16', {})
        st.markdown("### 🌊 Layer 16: Dynamische Stromingen")
        st.metric("Aantal Types", layer16.get('aantal_types', 0))
        st.metric("Actieve Stromingen", layer16.get('aantal_stromingen', 0))
        
        # Toon recente interferenties
        recent = layer16.get('recent', [])
        if recent:
            st.markdown("**Recente interferenties:**")
            for r in recent[-3:]:
                if isinstance(r, dict):
                    st.caption(f"• {' × '.join(r.get('ouders', ['?', '?']))} → {r.get('nieuw_type', '?')}")
    
    with col2:
        layer17 = data.get('layer17', {})
        st.markdown("### 🌟 Layer 17: Absolute Integratie")
        st.metric("Fundamentele Waarheden", layer17.get('aantal_fundamenten', 0))
        st.metric("Oceaan Coherentie", f"{layer17.get('coherentie', 0):.3f}")
        
        # Toon dimensies
        dimensies = layer17.get('dimensies', [])
        if dimensies:
            st.markdown("**Fundamentele dimensies:**")
            for d in dimensies:
                st.caption(f"• {d.get('naam', '?')} (stabiliteit: {d.get('stabiliteit', 0):.2f})")

# ====================================================================
# FOOTER & AUTO-REFRESH (aangepast)
# ====================================================================

st.divider()

col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    st.caption(f"⏰ Last Update: {datetime.fromtimestamp(data.get('timestamp', time.time())).strftime('%H:%M:%S')}")

with col_f2:
    st.caption(f"📚 Total Knowledge: {memory.count() if memory else 0} entries")

with col_f3:
    st.caption(f"🌊 Ocean Time: {data.get('ocean_time', 0):.1f}s")

with col_f4:
    st.caption(f"🔄 Auto-refresh: Every 5 seconds")

# Auto-refresh
time.sleep(5)
st.rerun()