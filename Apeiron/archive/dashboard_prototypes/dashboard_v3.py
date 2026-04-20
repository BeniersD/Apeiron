import streamlit as st
import plotly.graph_objects as go
import json
import os
import time

# --- CONFIGURATIE ---
st.set_page_config(
    page_title="Nexus v8.7 | Ontological Monitor",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark Mode Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

def get_state():
    """Haalt de huidige status op uit het JSON-bestand gegenereerd door de Engine."""
    path = "dashboard_state.json"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, PermissionError):
            # Voorkomt crash als het bestand op dat exacte moment wordt geschreven
            return None
    return None

# --- HEADER ---
st.title("🌌 Coherence Engine v8.7")
st.subheader("Real-time Ontologische Integratie Monitor")
st.divider()

# Placeholder voor de live-update loop
placeholder = st.empty()

# --- MAIN LOOP ---
while True:
    data = get_state()
    
    with placeholder.container():
        if data:
            # 1. METRICS RIJ
            # Gebruik .get() met defaults om 'KeyError' te voorkomen
            step = data.get('step', 0)
            coh = data.get('global_coherence', 0.0)
            sus = data.get('sustainability', 0.85)
            trans = data.get('transcendence', False)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Huidige Stap", step)
            m2.metric("Globale Coherentie", f"{coh:.2%}")
            m3.metric("Sustainability Index", f"{sus:.2%}")
            m4.metric("Status", "✨ TRANSCENDENT" if trans else "🔄 EVOLVING")

            # 2. VISUALISATIE (Radar & Progress)
            col_a, col_b = st.columns([2, 1])

            with col_a:
                st.write("### 🧠 Cognitieve Voetafdruk")
                fig = go.Figure()
                
                # De radarwaarden (gebruik defaults voor veiligheid)
                r_values = [
                    coh, 
                    sus, 
                    data.get('planetary_integration', 0.75), 
                    data.get('ethical_convergence', 0.90),
                    coh # Sluit de cirkel
                ]
                categories = ['Coherentie', 'Duurzaamheid', 'Planetair', 'Ethisch', 'Coherentie']
                
                fig.add_trace(go.Scatterpolar(
                    r=r_values,
                    theta=categories,
                    fill='toself',
                    line_color='#00fbff',
                    fillcolor='rgba(0, 251, 255, 0.2)'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 1], gridcolor="#30363d"),
                        angularaxis=dict(gridcolor="#30363d")
                    ),
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=450
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_b:
                st.write("### 📜 Laatste Activiteit")
                # We tonen de timestamp van de laatste update
                ts = data.get('timestamp', time.time())
                readable_ts = time.strftime('%H:%M:%S', time.localtime(ts))
                st.info(f"Laatste synchronisatie: **{readable_ts}**")
                
                st.write("De engine verwerkt momenteel data via de **Snowballing Research Module**. "
                         "Elke stap representeert een volledige integratie door de 17 lagen.")
                
                if coh > 0.9:
                    st.success("✅ Systeemstatus is optimaal. Absolute integratie bereikt.")
                elif coh < 0.3:
                    st.warning("⚠️ Lage coherentie gedetecteerd. Systeem herkalibreert...")

        else:
            st.warning("Wachten op data van `master_v8.py`... Zorg dat de engine draait.")
            st.info("Tip: Start de motor met `python master_v8.py` in je terminal.")

    # Snelheid van verversing (2 seconden is ideaal voor stabiliteit)
    time.sleep(2)