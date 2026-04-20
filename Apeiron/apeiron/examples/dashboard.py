"""
APEIRON DASHBOARD V12 - RESONANCESCOUT & OCEANIC INTEGRATION
====================================================================
All 17 Layers + Laag 16 Dynamische Stromingen + Laag 17 Absolute Integratie
+ ResonanceScout interferentie tracking + Hardware metrics + Chaos Detection

NIEUW IN V12:
- 🔍 ResonanceScout metrics (interferentieplekken, stille stromingen)
- ⚡ Hardware backend status en performance
- 🛡️ Chaos Detection safety levels
- 📊 Document tracking overzicht
- 🌊 Uitgebreide Laag 16/17 visualisaties
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
import time
import pandas as pd
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# ====================================================================
# CONFIGURATIE & DATACLASSES (V12 UITGEBREID)
# ====================================================================

@dataclass
class ResonanceScoutMetrics:
    """Data voor ResonanceScout (nieuw in V12)"""
    interferentie_plekken: int = 0
    stille_stromingen: int = 0
    zoekopdrachten_totaal: int = 0
    zoekopdrachten_uitgevoerd: int = 0
    zoekopdrachten_met_resultaat: int = 0
    gevulde_leegtes: int = 0
    gem_match_score: float = 0.0
    recente_interferenties: List[Dict] = None

@dataclass
class HardwareMetrics:
    """Hardware backend metrics (nieuw in V12)"""
    backend: str = "CPU"
    beschikbaar: bool = True
    velden: int = 0
    updates: int = 0
    gem_update_tijd_ms: float = 0.0
    error_count: int = 0

@dataclass
class ChaosMetrics:
    """Chaos Detection metrics (nieuw in V12)"""
    state: str = "STABLE"
    safety_level: str = "NORMAL"
    epsilon: float = 0.0
    divergentie_rate: float = 0.0
    oscillatie: float = 0.0
    shutdown_triggered: bool = False
    events: int = 0

@dataclass
class DocumentMetrics:
    """Document tracking metrics (nieuw in V12)"""
    totaal_documenten: int = 0
    totaal_verwerkingen: int = 0
    unieke_documenten: int = 0
    relaties: int = 0
    cache_hit_ratio: float = 0.0

@dataclass
class Layer16Metrics:
    """Gestructureerde data voor Laag 16"""
    aantal_types: int = 0
    aantal_stromingen: int = 0
    type_ontstaan: int = 0
    recent: List[Dict] = None
    
@dataclass
class Layer17Metrics:
    """Gestructureerde data voor Laag 17"""
    aantal_fundamenten: int = 0
    coherentie: float = 0.0
    stabiliteitsdrempel: float = 0.0
    aantal_integraties: int = 0
    dimensies: List[Dict] = None
    recent: List[Dict] = None

@dataclass
class SystemMetrics:
    """Complete systeem metrics (V12 uitgebreid)"""
    step: int = 0
    cycle: int = 0
    absolute_coherence: float = 0.0
    transcendence_achieved: bool = False
    transcendence_events: int = 0
    entropy: float = 0.0
    deep_dive_count: int = 0
    global_coherence: float = 0.0
    functional_entities: int = 0
    ontology_count: int = 0
    world_sustainability: float = 0.0
    collective_integration: float = 0.0
    ocean_time: float = 0.0
    timestamp: float = 0.0
    mode: str = "blind_exploration_v12"
    
    # Nieuwe V12 metrics
    resonance_scout: Optional[ResonanceScoutMetrics] = None
    hardware: Optional[HardwareMetrics] = None
    chaos: Optional[ChaosMetrics] = None
    document_tracking: Optional[DocumentMetrics] = None
    layer16: Optional[Layer16Metrics] = None
    layer17: Optional[Layer17Metrics] = None

# ====================================================================
# PAGE CONFIG
# ====================================================================

st.set_page_config(
    page_title="Apeiron V12 | ResonanceScout & Oceanic Integration",
    layout="wide",
    page_icon="🌊",
    initial_sidebar_state="expanded"
)

# ====================================================================
# OPTIMIZED CSS (met V12 toevoegingen)
# ====================================================================

st.markdown("""
<style>
    /* Base styling */
    .main { background-color: #0a0e14; color: #e6e6e6; }
    
    /* Layer cards met CSS variabelen voor kleuren */
    .layer-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #0f1419 100%);
        border: 1px solid #2d3748;
        border-left: 4px solid var(--layer-color);
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        transition: all 0.2s ease;
    }
    
    .layer-card:hover {
        border-left-width: 6px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
        transform: translateX(2px);
    }
    
    /* Kleurenschema */
    .layer-foundation { --layer-color: #667eea; }
    .layer-learning { --layer-color: #f093fb; }
    .layer-meta { --layer-color: #f5576c; }
    .layer-transcendent { --layer-color: #00ffcc; }
    .layer-oceanic { --layer-color: #4facfe; }
    .layer-resonance { --layer-color: #ffaa00; }  /* Nieuw voor ResonanceScout */
    
    /* Animaties gecombineerd */
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(var(--pulse-color), 0.5); }
        50% { box-shadow: 0 0 40px rgba(var(--pulse-color), 0.9); }
    }
    
    .transcendence-active {
        --pulse-color: 0, 255, 204;
        border: 3px solid #00ffcc;
        padding: 15px;
        border-radius: 10px;
        animation: pulse 2s infinite;
        background: linear-gradient(135deg, rgba(0, 255, 204, 0.1) 0%, rgba(0, 128, 255, 0.1) 100%);
        text-align: center;
        font-size: 1.2em;
        font-weight: bold;
        margin: 20px 0;
    }
    
    .fundament-active {
        --pulse-color: 79, 172, 254;
        border: 3px solid #4facfe;
        padding: 15px;
        border-radius: 10px;
        animation: pulse 2s infinite;
        background: linear-gradient(135deg, rgba(79, 172, 254, 0.1) 0%, rgba(0, 255, 204, 0.1) 100%);
        text-align: center;
        font-size: 1.2em;
        font-weight: bold;
        margin: 20px 0;
    }
    
    .interference-active {
        --pulse-color: 255, 170, 0;
        border: 3px solid #ffaa00;
        padding: 15px;
        border-radius: 10px;
        animation: pulse 2s infinite;
        background: linear-gradient(135deg, rgba(255, 170, 0, 0.1) 0%, rgba(255, 85, 0, 0.1) 100%);
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
    .status-oceanic { color: #4facfe; font-weight: bold; }
    .status-resonance { color: #ffaa00; font-weight: bold; }
    .status-danger { color: #ff5555; font-weight: bold; }
    
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
    
    .interference-chip {
        display: inline-block;
        background: rgba(255, 170, 0, 0.2);
        border: 1px solid #ffaa00;
        border-radius: 16px;
        padding: 4px 12px;
        margin: 4px;
        font-size: 0.9em;
        color: #ffaa00;
    }
    
    /* Verbeterde tooltips */
    [data-tooltip] {
        position: relative;
        cursor: help;
    }
    
    [data-tooltip]:before {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        padding: 4px 8px;
        background: #1a1f2e;
        border: 1px solid #4facfe;
        border-radius: 4px;
        font-size: 12px;
        white-space: nowrap;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.2s;
        z-index: 1000;
    }
    
    [data-tooltip]:hover:before {
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# OPTIMIZED STATE MANAGEMENT (V12 UITGEBREID)
# ====================================================================

class HistoryManager:
    """Gecentraliseerd history management"""
    
    MAX_HISTORY = 100
    METRICS = [
        'entropy', 'coherence', 'transcendence', 'collective',
        'ethical', 'world_sustainability', 'layer16_types',
        'layer17_fundamenten', 'layer17_coherentie',
        # Nieuwe V12 metrics
        'interferentie_plekken', 'stille_stromingen', 'zoekopdrachten',
        'epsilon', 'safety_level'
    ]
    
    def __init__(self):
        if 'history' not in st.session_state:
            self.reset()
    
    def reset(self):
        """Initialiseer of reset history"""
        st.session_state.history = {
            metric: [] for metric in self.METRICS
        }
    
    def add_snapshot(self, data: Dict[str, Any]):
        """Voeg een nieuwe snapshot toe"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Check duplicate
        if (self._get_last_time('entropy') == current_time):
            return
        
        # Haal ResonanceScout data
        rs = data.get('resonance_scout', {})
        rs_config = rs.get('config', {})
        rs_zoek = rs.get('zoekopdrachten', {})
        
        # Haal Chaos data
        chaos = data.get('safety', {})
        error_bounds = chaos.get('error_bounds', {})
        
        snapshots = {
            'entropy': data.get('entropy', 0.5),
            'coherence': data.get('absolute_coherence', 0.5),
            'transcendence': 1.0 if data.get('transcendence_achieved') else 0.0,
            'collective': data.get('collective_integration', 0.0),
            'ethical': data.get('ethical_convergence', 0.0),
            'world_sustainability': data.get('world_sustainability', 0.0),
            'layer16_types': data.get('layer16', {}).get('aantal_types', 0),
            'layer17_fundamenten': data.get('layer17', {}).get('aantal_fundamenten', 0),
            'layer17_coherentie': data.get('layer17', {}).get('coherentie', 0.0),
            # Nieuwe V12 metrics
            'interferentie_plekken': rs.get('interferentie_plekken', 0),
            'stille_stromingen': rs.get('stille_stromingen', 0),
            'zoekopdrachten': rs_zoek.get('totaal', 0),
            'epsilon': error_bounds.get('epsilon', 0.0),
            'safety_level': 1.0 if chaos.get('safety_level') == 'WARNING' else 0.0
        }
        
        for metric, value in snapshots.items():
            st.session_state.history[metric].append({
                'time': current_time,
                'value': value
            })
            
            # Maintain max length
            if len(st.session_state.history[metric]) > self.MAX_HISTORY:
                st.session_state.history[metric].pop(0)
    
    def _get_last_time(self, metric: str) -> Optional[str]:
        """Haal laatste timestamp op voor metric"""
        if st.session_state.history[metric]:
            return st.session_state.history[metric][-1]['time']
        return None
    
    def get_dataframe(self) -> pd.DataFrame:
        """Converteer history naar DataFrame"""
        if not st.session_state.history['entropy']:
            return pd.DataFrame()
        
        return pd.DataFrame({
            'Time': [d['time'] for d in st.session_state.history['entropy']],
            'Entropy': [d['value'] for d in st.session_state.history['entropy']],
            'Coherence': [d['value'] for d in st.session_state.history['coherence']],
            'Collective': [d['value'] for d in st.session_state.history['collective']],
            'Ethical': [d['value'] for d in st.session_state.history['ethical']],
            'Sustainability': [d['value'] for d in st.session_state.history['world_sustainability']],
            'Layer16 Types': [d['value'] for d in st.session_state.history['layer16_types']],
            'Layer17 Fundamenten': [d['value'] for d in st.session_state.history['layer17_fundamenten']],
            'Layer17 Coherentie': [d['value'] for d in st.session_state.history['layer17_coherentie']],
            # Nieuwe V12 metrics
            'Interferentie': [d['value'] for d in st.session_state.history['interferentie_plekken']],
            'Stille Stromingen': [d['value'] for d in st.session_state.history['stille_stromingen']],
            'Zoekopdrachten': [d['value'] for d in st.session_state.history['zoekopdrachten']],
            'Epsilon': [d['value'] for d in st.session_state.history['epsilon']]
        })

# ====================================================================
# DATA LOADING FUNCTIONS (V12 UITGEBREID)
# ====================================================================

@st.cache_data(ttl=1)  # Cache voor 1 seconde
def load_system_state() -> Optional[Dict]:
    """Load system state met caching voor performance"""
    try:
        if os.path.exists("apeiron_state.json"):
            with open("apeiron_state.json", "r") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading state: {e}")
    return None

@st.cache_resource
def init_memory():
    """Initialize ChromaDB connection."""
    try:
        client = chromadb.PersistentClient(path="./apeiron_memory")
        emb_fn = embedding_functions.DefaultEmbeddingFunction()
        return client.get_or_create_collection(
            name="apeiron_ultimate_memory",
            embedding_function=emb_fn
        )
    except Exception as e:
        st.warning(f"Memory init failed: {e}")
        return None

def parse_resonance_scout(data: Dict) -> Optional[ResonanceScoutMetrics]:
    """Parse ResonanceScout data (nieuw in V12)"""
    rs = data.get('resonance_scout', {})
    zoek = rs.get('zoekopdrachten', {})
    
    return ResonanceScoutMetrics(
        interferentie_plekken=rs.get('interferentie_plekken', 0),
        stille_stromingen=rs.get('stille_stromingen', 0),
        zoekopdrachten_totaal=zoek.get('totaal', 0),
        zoekopdrachten_uitgevoerd=zoek.get('uitgevoerd', 0),
        zoekopdrachten_met_resultaat=zoek.get('met_resultaat', 0),
        gevulde_leegtes=rs.get('gevulde_leegtes', 0),
        gem_match_score=rs.get('metrics', {}).get('gemiddelde_match_score', 0.0),
        recente_interferenties=rs.get('metrics', {}).get('recent', [])
    )

def parse_hardware(data: Dict) -> Optional[HardwareMetrics]:
    """Parse hardware metrics (nieuw in V12)"""
    # Hardware info zit mogelijk in verschillende formats
    hw = data.get('hardware_backend', 'CPU')
    if isinstance(hw, dict):
        return HardwareMetrics(
            backend=hw.get('name', 'CPU'),
            beschikbaar=hw.get('is_available', True),
            velden=hw.get('active_fields', 0),
            updates=hw.get('total_updates', 0),
            gem_update_tijd_ms=hw.get('avg_update_time', 0) * 1000,
            error_count=hw.get('error_count', 0)
        )
    else:
        return HardwareMetrics(backend=str(hw))

def parse_chaos(data: Dict) -> Optional[ChaosMetrics]:
    """Parse chaos detection metrics (nieuw in V12)"""
    safety = data.get('safety', {})
    error_bounds = safety.get('error_bounds', {})
    
    return ChaosMetrics(
        state=safety.get('state', 'STABLE'),
        safety_level=safety.get('safety_level', 'NORMAL'),
        epsilon=error_bounds.get('epsilon', 0.0),
        divergentie_rate=error_bounds.get('divergence_rate', 0.0),
        oscillatie=error_bounds.get('oscillation', 0.0),
        shutdown_triggered=safety.get('shutdown_triggered', False),
        events=safety.get('recent_events', 0)
    )

def parse_document_tracking(data: Dict) -> Optional[DocumentMetrics]:
    """Parse document tracking metrics (nieuw in V12)"""
    dt = data.get('document_tracking', {})
    
    return DocumentMetrics(
        totaal_documenten=dt.get('totaal_documenten', 0),
        totaal_verwerkingen=dt.get('totaal_verwerkingen', 0),
        unieke_documenten=dt.get('unieke_documenten', 0),
        relaties=dt.get('totaal_relaties', 0),
        cache_hit_ratio=dt.get('cache_hit_ratio', 0.0)
    )

def parse_layer16(data: Dict) -> Layer16Metrics:
    """Parse Layer 16 data naar dataclass"""
    layer16 = data.get('layer16', {})
    return Layer16Metrics(
        aantal_types=layer16.get('aantal_types', 0),
        aantal_stromingen=layer16.get('aantal_stromingen', 0),
        type_ontstaan=layer16.get('type_ontstaan', 0),
        recent=layer16.get('recent', [])
    )

def parse_layer17(data: Dict) -> Layer17Metrics:
    """Parse Layer 17 data naar dataclass"""
    layer17 = data.get('layer17', {})
    return Layer17Metrics(
        aantal_fundamenten=layer17.get('aantal_fundamenten', 0),
        coherentie=layer17.get('coherentie', 0.0),
        stabiliteitsdrempel=layer17.get('stabiliteitsdrempel', 0.0),
        aantal_integraties=layer17.get('aantal_integraties', 0),
        dimensies=layer17.get('dimensies', []),
        recent=layer17.get('recent', [])
    )

def parse_system_data(data: Dict) -> SystemMetrics:
    """Parse complete systeem data (V12 uitgebreid)"""
    return SystemMetrics(
        step=data.get('step', 0),
        cycle=data.get('cycle', 0),
        absolute_coherence=data.get('absolute_coherence', 0.0),
        transcendence_achieved=data.get('transcendence_achieved', False),
        transcendence_events=data.get('transcendence_events', 0),
        entropy=data.get('entropy', 0.0),
        deep_dive_count=data.get('deep_dive_count', 0),
        global_coherence=data.get('global_coherence', 0.0),
        functional_entities=data.get('functional_entities', 0),
        ontology_count=data.get('ontology_count', 0),
        world_sustainability=data.get('world_sustainability', 0.0),
        collective_integration=data.get('collective_integration', 0.0),
        ocean_time=data.get('ocean_time', 0.0),
        timestamp=data.get('timestamp', time.time()),
        mode=data.get('mode', 'blind_exploration_v12'),
        # Nieuwe V12 metrics
        resonance_scout=parse_resonance_scout(data),
        hardware=parse_hardware(data),
        chaos=parse_chaos(data),
        document_tracking=parse_document_tracking(data),
        layer16=parse_layer16(data),
        layer17=parse_layer17(data)
    )

# ====================================================================
# VISUALIZATION COMPONENTS (V12 UITGEBREID)
# ====================================================================

class DashboardComponents:
    """Herbruikbare dashboard componenten"""
    
    @staticmethod
    def metric_card(title: str, value: Any, delta: str = None, tooltip: str = None, color: str = "#4facfe"):
        """Verbeterde metric card met tooltip"""
        tooltip_attr = f'data-tooltip="{tooltip}"' if tooltip else ''
        delta_html = f'<br><small>{delta}</small>' if delta else ''
        return f"""
        <div {tooltip_attr} style="background: #1a1f2e; padding: 15px; border-radius: 8px; 
              border-left: 3px solid {color}; margin: 5px 0;">
            <div style="color: #888; font-size: 0.9em;">{title}</div>
            <div style="font-size: 1.8em; font-weight: bold; color: {color};">{value}</div>
            {delta_html}
        </div>
        """
    
    @staticmethod
    def create_evolution_chart(df: pd.DataFrame):
        """Maak gecombineerde evolutie chart (V12 uitgebreid)"""
        if df.empty:
            return None
        
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=('Exploration Dynamics', 'Integration Metrics', 
                          '🌊 Oceanic Layers', '🔍 ResonanceScout & Safety'),
            row_heights=[0.3, 0.25, 0.25, 0.2],
            vertical_spacing=0.08
        )
        
        # Row 1: Entropy & Coherence
        fig.add_trace(
            go.Scatter(x=df['Time'], y=df['Entropy'], name='Entropy',
                      line=dict(color='#f5576c', width=2), fill='tozeroy'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Time'], y=df['Coherence'], name='Coherence',
                      line=dict(color='#00ffcc', width=2)),
            row=1, col=1
        )
        
        # Row 2: Collective & Ethical
        fig.add_trace(
            go.Scatter(x=df['Time'], y=df['Collective'], name='Collective',
                      line=dict(color='#667eea', width=2)),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Time'], y=df['Ethical'], name='Ethical',
                      line=dict(color='#f093fb', width=2)),
            row=2, col=1
        )
        
        # Row 3: Oceanic layers
        fig.add_trace(
            go.Scatter(x=df['Time'], y=df['Layer16 Types'], name='L16 Types',
                      line=dict(color='#4facfe', width=2)),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Time'], y=df['Layer17 Coherentie'], name='L17 Coherentie',
                      line=dict(color='#00ccff', width=2)),
            row=3, col=1
        )
        
        # Row 4: ResonanceScout metrics (indien beschikbaar)
        if 'Interferentie' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['Time'], y=df['Interferentie'], name='Interferentie',
                          line=dict(color='#ffaa00', width=2)),
                row=4, col=1
            )
        if 'Epsilon' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['Time'], y=df['Epsilon'], name='Epsilon (ε)',
                          line=dict(color='#ff5555', width=2)),
                row=4, col=1
            )
        
        fig.update_layout(
            height=900,
            template="plotly_dark",
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def resonance_chart(rs: ResonanceScoutMetrics):
        """Visualiseer ResonanceScout data"""
        if not rs:
            return None
        
        # Bereid data voor
        categories = ['Interferentie', 'Stille Stromingen', 'Zoekopdrachten', 'Gevuld']
        values = [
            rs.interferentie_plekken,
            rs.stille_stromingen,
            rs.zoekopdrachten_totaal,
            rs.gevulde_leegtes
        ]
        
        fig = go.Figure(data=[
            go.Bar(x=categories, y=values, marker_color=['#ffaa00', '#ffbb33', '#ffcc66', '#44ff44'],
                  marker_line_color='#ffffff', marker_line_width=1.5)
        ])
        
        fig.update_layout(
            title='🔍 ResonanceScout Status',
            template='plotly_dark',
            xaxis_title='Categorie',
            yaxis_title='Aantal',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def hardware_gauge(hw: HardwareMetrics):
        """Visualiseer hardware status als gauge"""
        if not hw:
            return None
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = hw.gem_update_tijd_ms,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"⚡ {hw.backend} - Update tijd (ms)"},
            delta = {'reference': 10},
            gauge = {
                'axis': {'range': [None, 50]},
                'bar': {'color': "#4facfe"},
                'steps': [
                    {'range': [0, 10], 'color': "#00ff88"},
                    {'range': [10, 25], 'color': "#ffaa00"},
                    {'range': [25, 50], 'color': "#ff5555"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 30
                }
            }
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=250
        )
        
        return fig
    
    @staticmethod
    def layer16_chart(layer16: Layer16Metrics):
        """Visualiseer Layer 16 data"""
        if not layer16 or not layer16.recent:
            return None
        
        # Bereid data voor
        types = [f"T-{i+1}" for i in range(min(10, len(layer16.recent)))]
        sterktes = [r.get('sterkte', 0) for r in layer16.recent[-10:]]
        
        fig = go.Figure(data=[
            go.Bar(x=types, y=sterktes, marker_color='#4facfe',
                  marker_line_color='#00ffcc', marker_line_width=1.5)
        ])
        
        fig.update_layout(
            title='Recente Interferentie Sterktes',
            template='plotly_dark',
            xaxis_title='Tijd',
            yaxis_title='Sterkte',
            showlegend=False
        )
        
        return fig

# ====================================================================
# MAIN APP (V12)
# ====================================================================

def main():
    """Hoofdfunctie van de dashboard app"""
    
    # Initialize
    history_mgr = HistoryManager()
    memory = init_memory()
    
    # Load data
    raw_data = load_system_state()
    
    if not raw_data:
        st.warning("⚠️ Systeem niet actief. Start apeiron_v12.py om te beginnen.")
        st.info("💡 Het dashboard blijft automatisch refreshen zodra het systeem actief is.")
        
        # Toon leeg dashboard met instructies
        col1, col2, col3 = st.columns(3)
        with col2:
            st.image("https://via.placeholder.com/400x200/0a0e14/4facfe?text=APEIRON+V12", 
                    use_container_width=True)
            st.markdown("""
            ### 🌊 Wachten op systeem...
            
            Het dashboard wordt automatisch geüpdatet zodra het systeem start.
            
            **Verwachte bestanden:**
            - `apeiron_state.json` - Systeem status
            - `./apeiron_memory/` - Kennisbank directory
            - `document_tracking.db` - Document tracking database
            """)
        
        # Auto-refresh
        time.sleep(3)
        st.rerun()
        return
    
    # Parse data
    data = parse_system_data(raw_data)
    history_mgr.add_snapshot(raw_data)
    
    # Check special events
    if data.resonance_scout and data.resonance_scout.gevulde_leegtes > 0:
        st.markdown(
            f"<div class='interference-active'>🔍 NIEUWE WISKUNDIGE LEEGTE GEVULD! "
            f"Match score: {data.resonance_scout.gem_match_score:.2f}</div>",
            unsafe_allow_html=True
        )
    elif data.layer17 and data.layer17.recent:
        laatste = data.layer17.recent[-1]
        if laatste.get('nieuw', 0) > 0:
            st.markdown(
                f"<div class='fundament-active'>🌟 NIEUW OCEAANFUNDAMENT GEVORMD! "
                f"Coherentie: {data.layer17.coherentie:.2f}</div>",
                unsafe_allow_html=True
            )
    elif data.transcendence_achieved:
        st.markdown(
            "<div class='transcendence-active'>✨ TRANSCENDENCE ACHIEVED ✨</div>",
            unsafe_allow_html=True
        )
    
    # Header
    st.markdown("<h1 style='text-align: center;'>🌊 APEIRON V12 DASHBOARD</h1>", 
            unsafe_allow_html=True)

    st.markdown(
        "<h3 style='text-align: center; color: #4facfe;'>"
        "ResonanceScout - De AI ontdekt waar kennis ontbreekt</h3>",
        unsafe_allow_html=True
    )    
    
    st.divider()
    
    # Sidebar
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
                "🔍 ResonanceScout",
                "⚡ Hardware Status",
                "🛡️ Chaos Detection",
                "📊 Document Tracking",
                "Transcendent (16-17)",
                "All Layers Detail"
            ],
            index=0
        )
        
        st.divider()
        
        # Quick stats
        st.subheader("📊 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Steps", data.step)
            st.metric("Ocean Time", f"{data.ocean_time:.1f}s")
            if data.resonance_scout:
                st.metric("🔍 Interferenties", data.resonance_scout.interferentie_plekken)
        with col2:
            st.metric("Global Coherence", f"{data.absolute_coherence:.1%}")
            st.metric("Transcendence", "✨ YES" if data.transcendence_achieved else "🌀 Building...")
            if data.resonance_scout:
                st.metric("💫 Stille Stromingen", data.resonance_scout.stille_stromingen)
        
        st.divider()
        
        # Hardware status
        if data.hardware:
            st.subheader(f"⚡ Hardware: {data.hardware.backend}")
            st.caption(f"Updates: {data.hardware.updates}")
            st.caption(f"Gem tijd: {data.hardware.gem_update_tijd_ms:.1f}ms")
            if data.hardware.error_count > 0:
                st.caption(f"⚠️ Errors: {data.hardware.error_count}")
        
        # Chaos status
        if data.chaos:
            st.subheader(f"🛡️ Safety: {data.chaos.safety_level}")
            state_color = {
                "STABLE": "🟢",
                "CONVERGING": "🟡",
                "OSCILLATING": "🟠",
                "DIVERGING": "🔴",
                "CHAOTIC": "💀",
                "CRITICAL": "🔥"
            }.get(data.chaos.state, "⚪")
            st.caption(f"{state_color} State: {data.chaos.state}")
            st.caption(f"ε: {data.chaos.epsilon:.3f}")
        
        # Laag 16 stats
        if data.layer16:
            st.subheader("🌊 Laag 16")
            st.metric("Dynamische Types", data.layer16.aantal_types)
            st.metric("Actieve Stromingen", data.layer16.aantal_stromingen)
        
        # Laag 17 stats
        if data.layer17:
            st.subheader("🌟 Laag 17")
            st.metric("Fundamentele Waarheden", data.layer17.aantal_fundamenten)
            st.metric("Coherentie", f"{data.layer17.coherentie:.2f}")
        
        st.divider()
        
        st.caption(f"🕐 Last Update: {datetime.fromtimestamp(data.timestamp).strftime('%H:%M:%S')}")
        st.caption(f"💾 Knowledge Base: {memory.count() if memory else 0} entries")
        st.caption(f"🌌 Mode: {data.mode}")
    
    # Main content based on view
    df = history_mgr.get_dataframe()
    
    if layer_view == "Overview":
        show_overview(data, df)
    elif layer_view == "🌊 Laag 16 - Dynamische Stromingen":
        show_layer16(data.layer16, df)
    elif layer_view == "🌟 Laag 17 - Absolute Integratie":
        show_layer17(data.layer17, df)
    elif layer_view == "🔍 ResonanceScout":
        show_resonance_scout(data.resonance_scout, df)
    elif layer_view == "⚡ Hardware Status":
        show_hardware(data.hardware)
    elif layer_view == "🛡️ Chaos Detection":
        show_chaos(data.chaos, df)
    elif layer_view == "📊 Document Tracking":
        show_document_tracking(data.document_tracking)
    elif layer_view == "Transcendent (16-17)":
        show_transcendent(data)
    elif layer_view == "All Layers Detail":
        show_all_layers(data)
    elif layer_view in ["Foundation (1-10)", "Meta (11-15)"]:
        st.info(f"📋 {layer_view} view - Behoudt originele functionaliteit")
    
    # Footer
    st.divider()
    show_footer(data, memory)
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

def show_overview(data: SystemMetrics, df: pd.DataFrame):
    """Overview view (V12 uitgebreid)"""
    st.subheader("📊 System Overview")
    
    # Top metrics - 6 kolommen voor V12
    cols = st.columns(6)
    metrics = [
        ("Exploration Step", data.step, f"+{data.cycle} cycles"),
        ("Absolute Coherence", f"{data.absolute_coherence:.1%}", 
         "✨" if data.absolute_coherence > 0.95 else None),
        ("Transcendence Events", data.transcendence_events, None),
        ("Research Entropy", f"{data.entropy:.2f}",
         "Novel" if data.entropy > 0.7 else "Familiar"),
        ("Deep Dives", data.deep_dive_count, "🔬" if data.deep_dive_count > 0 else None),
        ("Ocean Time", f"{data.ocean_time:.1f}s", None)
    ]
    
    for col, (title, value, delta) in zip(cols, metrics):
        with col:
            st.metric(title, value, delta)
    
    st.divider()
    
    # V12 metrics cards
    col_rs, col_hw, col_chaos, col_doc = st.columns(4)
    
    with col_rs:
        if data.resonance_scout:
            st.markdown(DashboardComponents.metric_card(
                "🔍 ResonanceScout",
                f"{data.resonance_scout.interferentie_plekken} int",
                f"{data.resonance_scout.stille_stromingen} silent",
                "Interferentieplekken en stille stromingen",
                color="#ffaa00"
            ), unsafe_allow_html=True)
    
    with col_hw:
        if data.hardware:
            st.markdown(DashboardComponents.metric_card(
                "⚡ Hardware",
                data.hardware.backend,
                f"{data.hardware.gem_update_tijd_ms:.1f}ms",
                f"Updates: {data.hardware.updates}",
                color="#4facfe"
            ), unsafe_allow_html=True)
    
    with col_chaos:
        if data.chaos:
            color = "#00ff88" if data.chaos.safety_level == "NORMAL" else "#ffaa00" if data.chaos.safety_level == "WARNING" else "#ff5555"
            st.markdown(DashboardComponents.metric_card(
                "🛡️ Safety",
                data.chaos.safety_level,
                f"ε={data.chaos.epsilon:.3f}",
                f"State: {data.chaos.state}",
                color=color
            ), unsafe_allow_html=True)
    
    with col_doc:
        if data.document_tracking:
            st.markdown(DashboardComponents.metric_card(
                "📊 Documents",
                data.document_tracking.totaal_documenten,
                f"{data.document_tracking.unieke_documenten} unique",
                f"Cache: {data.document_tracking.cache_hit_ratio:.1%}",
                color="#f093fb"
            ), unsafe_allow_html=True)
    
    st.divider()
    
    # Layer cards
    col_l16, col_l17 = st.columns(2)
    
    with col_l16:
        if data.layer16:
            st.markdown(f"""
            <div class='layer-card layer-oceanic'>
                <div class='layer-title'>🌊 Laag 16 - Dynamische Stromingen</div>
                <div class='layer-metric'>Spontane interferentie tussen domeinen</div>
                <div style='display: flex; justify-content: space-between; margin-top: 15px;'>
                    <div><span class='metric-number'>{data.layer16.aantal_types}</span><br>Types</div>
                    <div><span class='metric-number'>{data.layer16.aantal_stromingen}</span><br>Stromingen</div>
                    <div><span class='metric-number'>{data.layer16.type_ontstaan}</span><br>Ontstaan</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_l17:
        if data.layer17:
            st.markdown(f"""
            <div class='layer-card layer-oceanic'>
                <div class='layer-title'>🌟 Laag 17 - Absolute Integratie</div>
                <div class='layer-metric'>Van interferentie naar fundamentele waarheid</div>
                <div style='display: flex; justify-content: space-between; margin-top: 15px;'>
                    <div><span class='metric-number'>{data.layer17.aantal_fundamenten}</span><br>Fundamenten</div>
                    <div><span class='metric-number'>{data.layer17.coherentie:.2f}</span><br>Coherentie</div>
                    <div><span class='metric-number'>{data.layer17.stabiliteitsdrempel:.2f}</span><br>Drempel</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Layer group scores
    cols = st.columns(5)
    scores = [
        ("🏗️ Foundation", (data.global_coherence + data.functional_entities/1000) / 2),
        ("🧬 Meta", (data.ontology_count/20 + data.world_sustainability) / 2),
        ("✨ Transcendence", data.collective_integration),
        ("🌊 Oceanic", data.layer17.coherentie if data.layer17 else 0),
        ("🔍 Resonance", data.resonance_scout.gem_match_score if data.resonance_scout else 0)
    ]
    
    for col, (title, score) in zip(cols, scores):
        with col:
            st.markdown(f"### {title}")
            st.progress(min(score, 1.0))
            st.caption(f"Score: {score:.1%}")
    
    st.divider()
    
    # Evolution chart
    if not df.empty:
        st.subheader("📈 System Evolution")
        fig = DashboardComponents.create_evolution_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

def show_resonance_scout(rs: Optional[ResonanceScoutMetrics], df: pd.DataFrame):
    """🔍 ResonanceScout detail view"""
    st.subheader("🔍 ResonanceScout - Interferentie Jager")
    
    if not rs:
        st.info("Geen ResonanceScout data beschikbaar")
        return
    
    # Metrics
    cols = st.columns(5)
    with cols[0]:
        st.metric("Interferentie Plekken", rs.interferentie_plekken)
    with cols[1]:
        st.metric("Stille Stromingen", rs.stille_stromingen)
    with cols[2]:
        st.metric("Zoekopdrachten", rs.zoekopdrachten_totaal)
    with cols[3]:
        st.metric("Uitgevoerd", rs.zoekopdrachten_uitgevoerd)
    with cols[4]:
        st.metric("Match Score", f"{rs.gem_match_score:.2f}")
    
    st.divider()
    
    # Visualisaties
    col1, col2 = st.columns(2)
    
    with col1:
        fig = DashboardComponents.resonance_chart(rs)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if rs.recente_interferenties:
            st.subheader("🔄 Recente Interferenties")
            df_int = pd.DataFrame(rs.recente_interferenties[-10:])
            st.dataframe(df_int, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Evolutie
    if not df.empty and 'Interferentie' in df.columns:
        st.subheader("📈 Interferentie Evolutie")
        fig = px.area(df, x='Time', y='Interferentie', 
                     title='Groei van Interferentieplekken',
                     template='plotly_dark')
        fig.update_traces(line_color='#ffaa00', fillcolor='rgba(255, 170, 0, 0.2)')
        st.plotly_chart(fig, use_container_width=True)

def show_hardware(hw: Optional[HardwareMetrics]):
    """⚡ Hardware status view"""
    st.subheader("⚡ Hardware Status")
    
    if not hw:
        st.info("Geen hardware data beschikbaar")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### Actieve backend: **{hw.backend}**")
        st.metric("Beschikbaar", "✅" if hw.beschikbaar else "❌")
        st.metric("Actieve velden", hw.velden)
        st.metric("Totaal updates", hw.updates)
        st.metric("Error count", hw.error_count)
    
    with col2:
        fig = DashboardComponents.hardware_gauge(hw)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Hardware info per type
    st.subheader("📊 Backend Informatie")
    
    backend_info = {
        "CPU": "💻 Werkt overal, numpy implementatie",
        "CUDA": "🎯 GPU versnelling - massief parallel",
        "FPGA": "⚡ Echte parallelle hardware - geen discretisatie",
        "Quantum": "🌀 Superpositie en verstrengeling"
    }
    
    st.info(backend_info.get(hw.backend, "Onbekende backend"))

def show_chaos(chaos: Optional[ChaosMetrics], df: pd.DataFrame):
    """🛡️ Chaos Detection view"""
    st.subheader("🛡️ Chaos Detection & Safety")
    
    if not chaos:
        st.info("Geen chaos detection data beschikbaar")
        return
    
    # Status kleuren
    state_colors = {
        "STABLE": "🟢",
        "CONVERGING": "🟡",
        "OSCILLATING": "🟠",
        "DIVERGING": "🔴",
        "CHAOTIC": "💀",
        "CRITICAL": "🔥"
    }
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"### Status")
        st.markdown(f"**State:** {state_colors.get(chaos.state, '⚪')} {chaos.state}")
        st.markdown(f"**Safety Level:** {chaos.safety_level}")
        st.markdown(f"**Shutdown:** {'✅' if chaos.shutdown_triggered else '❌'}")
        st.markdown(f"**Events:** {chaos.events}")
    
    with col2:
        st.markdown(f"### Error Bounds")
        st.metric("Epsilon (ε)", f"{chaos.epsilon:.3f}")
        st.metric("Divergentie Rate", f"{chaos.divergentie_rate:.3f}")
        st.metric("Oscillatie", f"{chaos.oscillatie:.3f}")
    
    with col3:
        # Safety level indicator
        level_value = {"NORMAL": 0, "CAUTION": 1, "WARNING": 2, "DANGER": 3, "CRITICAL": 4, "EMERGENCY_SHUTDOWN": 5}
        current = level_value.get(chaos.safety_level, 0)
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = current,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Safety Level"},
            gauge = {
                'axis': {'range': [None, 5], 'tickvals': [0,1,2,3,4,5], 
                        'ticktext': ['N','C','W','D','CR','EM']},
                'bar': {'color': "#ff5555" if current >= 3 else "#ffaa00" if current >= 2 else "#00ff88"},
                'steps': [
                    {'range': [0, 1], 'color': "#00ff88"},
                    {'range': [1, 2], 'color': "#aaff00"},
                    {'range': [2, 3], 'color': "#ffaa00"},
                    {'range': [3, 4], 'color': "#ff5555"},
                    {'range': [4, 5], 'color': "#ff0000"}
                ]
            }
        ))
        
        fig.update_layout(height=250, template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Evolutie
    if not df.empty and 'Epsilon' in df.columns:
        st.subheader("📈 Epsilon Evolutie")
        fig = px.line(df, x='Time', y='Epsilon', 
                     title='Error Bound (ε) Over Tijd',
                     template='plotly_dark')
        fig.add_hline(y=0.3, line_dash="dash", line_color="red", 
                     annotation_text="Threshold")
        st.plotly_chart(fig, use_container_width=True)

def show_document_tracking(dt: Optional[DocumentMetrics]):
    """📊 Document Tracking view"""
    st.subheader("📊 Document Tracking - Dubbele Verwerking Voorkomen")
    
    if not dt:
        st.info("Geen document tracking data beschikbaar")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Totaal Documenten", dt.totaal_documenten)
        st.metric("Unieke Documenten", dt.unieke_documenten)
    
    with col2:
        st.metric("Totaal Verwerkingen", dt.totaal_verwerkingen)
        st.metric("Gem. per document", f"{dt.totaal_verwerkingen / max(dt.unieke_documenten, 1):.1f}x")
    
    with col3:
        st.metric("Document Relaties", dt.relaties)
        st.metric("Cache Hit Ratio", f"{dt.cache_hit_ratio:.1%}")
    
    st.divider()
    
    # Uitleg
    st.markdown("""
    ### Hoe werkt Document Tracking?
    
    De DocumentTracker voorkomt dubbele verwerking door:
    
    1. **SQLite database** - Houdt bij welke documenten zijn verwerkt
    2. **URL vs local file** - Aparte behandeling voor URLs en bestanden
    3. **Backtracing** - Registreert relaties tussen documenten
    4. **JSON export** - Voor dashboard integratie
    5. **Caching** - Snelle lookups met cache hit ratio
    """)

def show_layer16(layer16: Layer16Metrics, df: pd.DataFrame):
    """🌊 Laag 16 detail view (ongewijzigd)"""
    st.subheader("🌊 Laag 16: Dynamische Stromingen - Spontane Interferentie")
    
    # Metrics
    cols = st.columns(4)
    with cols[0]:
        st.metric("Aantal Types", layer16.aantal_types)
    with cols[1]:
        st.metric("Actieve Stromingen", layer16.aantal_stromingen)
    with cols[2]:
        st.metric("Nieuwe Types Ontstaan", layer16.type_ontstaan)
    with cols[3]:
        st.metric("Interferentie Events", len(layer16.recent) if layer16.recent else 0)
    
    st.divider()
    
    # Visualisatie
    if layer16.recent:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("📊 Interferentie Analyse")
            fig = DashboardComponents.layer16_chart(layer16)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🔄 Recente Interferenties")
            interferenties = []
            for i, r in enumerate(layer16.recent[-10:]):
                if isinstance(r, dict):
                    interferenties.append({
                        'Tijd': f"T-{i+1}",
                        'Ouders': ' × '.join(r.get('ouders', ['?', '?'])),
                        'Nieuw Type': r.get('nieuw_type', '?')[:15] + "..." if len(r.get('nieuw_type', '')) > 15 else r.get('nieuw_type', '?'),
                        'Sterkte': f"{r.get('sterkte', 0):.2f}"
                    })
            
            if interferenties:
                st.dataframe(pd.DataFrame(interferenties), use_container_width=True, hide_index=True)
    else:
        st.info("Geen interferentie events geregistreerd")
    
    # Type evolutie
    if not df.empty:
        st.divider()
        st.subheader("📈 Type Evolutie")
        
        fig = px.area(df, x='Time', y='Layer16 Types', 
                     title='Groei van Dynamische Types',
                     template='plotly_dark')
        fig.update_traces(line_color='#4facfe', fillcolor='rgba(79, 172, 254, 0.2)')
        st.plotly_chart(fig, use_container_width=True)

def show_layer17(layer17: Layer17Metrics, df: pd.DataFrame):
    """🌟 Laag 17 detail view (ongewijzigd)"""
    st.subheader("🌟 Laag 17: Absolute Integratie - Van Interferentie naar Waarheid")
    
    # Metrics
    cols = st.columns(4)
    with cols[0]:
        st.metric("Ocean Fundamentele Waarheden", layer17.aantal_fundamenten)
    with cols[1]:
        st.metric("Huidige Coherentie", f"{layer17.coherentie:.3f}")
    with cols[2]:
        st.metric("Stabiliteitsdrempel", f"{layer17.stabiliteitsdrempel:.3f}")
    with cols[3]:
        st.metric("Aantal Integraties", layer17.aantal_integraties)
    
    st.divider()
    
    # Dimensies
    if layer17.dimensies:
        st.subheader("📏 Fundamentele Meetdimensies")
        
        # Toon dimensies als chips
        dimensie_html = ""
        for d in layer17.dimensies:
            dimensie_html += f"<span class='fundament-chip'>{d.get('naam', '?')} ({d.get('stabiliteit', 0):.2f})</span>"
        
        st.markdown(dimensie_html, unsafe_allow_html=True)
        st.divider()
    
    # Recente integraties
    if layer17.recent:
        st.subheader("🔄 Recente Oceaan Herstructureringen")
        
        integraties = []
        for i, r in enumerate(layer17.recent):
            integraties.append({
                'Tijd': f"{r.get('tijd', 0):.0f}s",
                'Type': r.get('type', '?'),
                'Nieuwe Fundamenten': r.get('nieuw', 0),
                'Verwijderd': r.get('oud', 0)
            })
        
        if integraties:
            st.dataframe(pd.DataFrame(integraties), use_container_width=True, hide_index=True)
        st.divider()
    
    # Visualisatie
    if not df.empty:
        st.subheader("📈 Oceaan Coherentie Evolutie")
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(x=df['Time'], y=df['Layer17 Coherentie'],
                      name='Coherentie', line=dict(color='#00ffcc', width=2)),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(x=df['Time'], y=df['Layer17 Fundamenten'],
                      name='Aantal Fundamenten', line=dict(color='#4facfe', width=2)),
            secondary_y=True
        )
        
        fig.update_layout(
            template='plotly_dark',
            title='Coherentie vs Fundamenten',
            hovermode='x unified'
        )
        fig.update_xaxes(title_text="Tijd")
        fig.update_yaxes(title_text="Coherentie", secondary_y=False)
        fig.update_yaxes(title_text="Aantal Fundamenten", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)

def show_transcendent(data: SystemMetrics):
    """✨ Transcendent layers view (uitgebreid met Resonance)"""
    st.subheader("✨ Transcendent Layers 16-17 & Resonance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if data.layer16:
            st.markdown("### 🌊 Layer 16: Dynamische Stromingen")
            st.metric("Aantal Types", data.layer16.aantal_types)
            st.metric("Actieve Stromingen", data.layer16.aantal_stromingen)
            
            if data.layer16.recent:
                st.markdown("**Recente interferenties:**")
                for r in data.layer16.recent[-3:]:
                    if isinstance(r, dict):
                        ouders = ' × '.join(r.get('ouders', ['?', '?']))
                        st.caption(f"• {ouders} → {r.get('nieuw_type', '?')}")
    
    with col2:
        if data.layer17:
            st.markdown("### 🌟 Layer 17: Absolute Integratie")
            st.metric("Fundamentele Waarheden", data.layer17.aantal_fundamenten)
            st.metric("Oceaan Coherentie", f"{data.layer17.coherentie:.3f}")
            
            if data.layer17.dimensies:
                st.markdown("**Fundamentele dimensies:**")
                for d in data.layer17.dimensies[:5]:
                    st.caption(f"• {d.get('naam', '?')} (stabiliteit: {d.get('stabiliteit', 0):.2f})")
    
    with col3:
        if data.resonance_scout:
            st.markdown("### 🔍 ResonanceScout")
            st.metric("Interferentieplekken", data.resonance_scout.interferentie_plekken)
            st.metric("Stille Stromingen", data.resonance_scout.stille_stromingen)
            st.metric("Gevulde Leegtes", data.resonance_scout.gevulde_leegtes)
            st.metric("Match Score", f"{data.resonance_scout.gem_match_score:.2f}")

def show_all_layers(data: SystemMetrics):
    """🔮 Complete 17-layer view (uitgebreid met V12)"""
    st.subheader("🔮 Complete 17-Layer Architecture")
    
    # Lagen 1-15 (samengevat)
    st.markdown("""
    <div class='layer-card layer-foundation'>
        <div class='layer-title'>Lagen 1-10: Foundation</div>
        <div class='layer-metric'>Basis exploratie en patroonherkenning</div>
    </div>
    <div class='layer-card layer-meta'>
        <div class='layer-title'>Lagen 11-15: Meta Intelligence</div>
        <div class='layer-metric'>Ontologieën en ethische convergentie</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Laag 16
    if data.layer16:
        st.markdown(f"""
        <div class='layer-card layer-oceanic'>
            <div class='layer-title'>Layer 16: Dynamische Stromingen</div>
            <div class='layer-metric'>Spontane interferentie tussen domeinen</div>
            <div style='display: flex; justify-content: space-between; margin-top: 10px;'>
                <div><span class='metric-number'>{data.layer16.aantal_types}</span><br>Types</div>
                <div><span class='metric-number'>{data.layer16.aantal_stromingen}</span><br>Stromingen</div>
                <div><span class='metric-number'>{data.layer16.type_ontstaan}</span><br>Ontstaan</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Laag 17
    if data.layer17:
        dimensie_text = f"{len(data.layer17.dimensies)} dimensies" if data.layer17.dimensies else "Geen dimensies"
        st.markdown(f"""
        <div class='layer-card layer-oceanic'>
            <div class='layer-title'>Layer 17: Absolute Integratie</div>
            <div class='layer-metric'>Fundamentele waarheden uit stabiele interferentie</div>
            <div style='display: flex; justify-content: space-between; margin-top: 10px;'>
                <div><span class='metric-number'>{data.layer17.aantal_fundamenten}</span><br>Fundamenten</div>
                <div><span class='metric-number'>{data.layer17.coherentie:.2f}</span><br>Coherentie</div>
                <div><span class='metric-number'>{data.layer17.stabiliteitsdrempel:.2f}</span><br>Drempel</div>
            </div>
            <div class='layer-metric' style='margin-top: 10px;'>{dimensie_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ResonanceScout (als aparte laag)
    if data.resonance_scout:
        st.markdown(f"""
        <div class='layer-card layer-resonance'>
            <div class='layer-title'>🔍 ResonanceScout</div>
            <div class='layer-metric'>Interferentie-gestuurde exploratie</div>
            <div style='display: flex; justify-content: space-between; margin-top: 10px;'>
                <div><span class='metric-number'>{data.resonance_scout.interferentie_plekken}</span><br>Interferenties</div>
                <div><span class='metric-number'>{data.resonance_scout.stille_stromingen}</span><br>Stille Stromingen</div>
                <div><span class='metric-number'>{data.resonance_scout.zoekopdrachten_totaal}</span><br>Zoekopdrachten</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_footer(data: SystemMetrics, memory):
    """Unified footer (V12 uitgebreid)"""
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    
    with col_f1:
        st.caption(f"⏰ Last Update: {datetime.fromtimestamp(data.timestamp).strftime('%H:%M:%S')}")
    with col_f2:
        st.caption(f"📚 Knowledge: {memory.count() if memory else 0} entries")
    with col_f3:
        st.caption(f"🌊 Ocean Time: {data.ocean_time:.1f}s")
    with col_f4:
        st.caption(f"🔄 Auto-refresh: Every 5 seconds")
    with col_f5:
        st.caption(f"🌌 Mode: {data.mode}")

if __name__ == "__main__":
    main()