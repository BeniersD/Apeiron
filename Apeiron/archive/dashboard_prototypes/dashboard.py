import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import time
import os

st.set_page_config(page_title="Coherence Engine v8 Dashboard", layout="wide")

st.title("🌌 Coherence Engine v8: Live Ontological Monitor")
st.write("Visualisatie van de 17-Layer Framework Integratie")

# Placeholder voor live statistieken
col1, col2, col3, col4 = st.columns(4)
metric_step = col1.empty()
metric_coh = col2.empty()
metric_sus = col3.empty()
metric_trans = col4.empty()

# Grafiek placeholder
chart_placeholder = st.empty()

def load_data():
    if os.path.exists("dashboard_state.json"):
        with open("dashboard_state.json", "r") as f:
            return json.load(f)
    return None

# Geschiedenis bijhouden voor de grafiek
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Step', 'Coherence', 'Sustainability'])

while True:
    data = load_data()
    if data:
        # Update Metrics
        metric_step.metric("Huidige Stap", data['step'])
        metric_coh.metric("Global Coherence", f"{data['global_coherence']:.2%}")
        metric_sus.metric("Sustainability Index", f"{data['sustainability']:.2%}")
        metric_trans.success("TRANSCENDENT ✨") if data['transcendence'] else metric_trans.info("Evolving... 🔄")

        # Update History
        new_row = {'Step': data['step'], 'Coherence': data['global_coherence'], 'Sustainability': data['sustainability']}
        if st.session_state.history.empty or data['step'] > st.session_state.history['Step'].max():
            st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([new_row])]).tail(50)

        # Plotly Radar Chart voor de 17-lagen status
        fig = go.Figure()
        categories = ['Coherence', 'Sustainability', 'Planetary', 'Ethical', 'Collective']
        values = [data['global_coherence'], data['sustainability'], data['planetary_integration'], 
                  data['ethical_convergence'], 0.8] # 0.8 als placeholder voor collective

        fig.add_trace(go.Scatterpolar(
              r=values,
              theta=categories,
              fill='toself',
              name='System State',
              line_color='cyan'
        ))

        fig.update_layout(
          polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
          showlegend=False,
          template="plotly_dark",
          title="Multidimensionale Coherentie (Lagen 11-17)"
        )

        chart_placeholder.plotly_chart(fig, use_container_width=True)

    time.sleep(1)