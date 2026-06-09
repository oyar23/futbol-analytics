"""Página de scouting: comparador de jugadores por percentiles (radar)."""
import streamlit as st

import charts
from utils import load_table

st.set_page_config(page_title="Scouting · Fútbol Analytics", page_icon="🔍",
                   layout="wide")
st.title("🔍 Scouting — percentiles por posición")
st.caption("Compará dos jugadores de la **misma posición**. Los percentiles se "
           "calculan dentro de cada grupo posicional (GK/DEF/MID/FWD), sobre "
           "jugadores con ≥ 180 minutos.")

pct = load_table("scouting_percentiles")

GROUPS = {"FWD": "Delanteros", "MID": "Mediocampistas",
          "DEF": "Defensores", "GK": "Arqueros"}

f1, f2, f3 = st.columns(3)
group = f1.selectbox("Grupo posicional", list(GROUPS),
                     format_func=lambda g: f"{g} · {GROUPS[g]}")
pool = pct[pct["position_group"] == group].sort_values("player_name")
names = pool["player_name"].tolist()

if len(names) < 2:
    st.warning("No hay suficientes jugadores en este grupo.")
    st.stop()

# Defaults inteligentes para FWD: Mbappé vs Messi
def _default(idx_options, contains):
    for i, n in enumerate(idx_options):
        if contains.lower() in n.lower():
            return i
    return 0

a_default = _default(names, "Mbappé") if group == "FWD" else 0
b_default = _default(names, "Messi") if group == "FWD" else 1

player_a = f2.selectbox("Jugador A", names, index=a_default)
player_b = f3.selectbox("Jugador B", names, index=b_default)

pa = pool[pool["player_name"] == player_a].iloc[0]
pb = pool[pool["player_name"] == player_b].iloc[0]

st.plotly_chart(charts.radar(pa, pb), width="stretch")

# Tabla de percentiles lado a lado
st.subheader("Percentiles comparados")
rows = []
for col, label in charts.RADAR_METRICS:
    rows.append({"Métrica": label,
                 player_a: round(float(pa[col]), 0),
                 player_b: round(float(pb[col]), 0)})
import pandas as pd
st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

with st.expander("Ver tabla completa de percentiles del grupo"):
    st.dataframe(pool, width="stretch", hide_index=True)
