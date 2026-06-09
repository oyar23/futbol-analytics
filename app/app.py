"""Dashboard web de Fútbol Analytics (Streamlit) — página de inicio / resumen.

Ejecutar desde la raíz del proyecto:
    streamlit run app/app.py

Requiere haber generado la base con:
    python run_pipeline.py
"""
import streamlit as st

import charts
from utils import load_table

st.set_page_config(page_title="Fútbol Analytics", page_icon="⚽",
                   layout="wide", initial_sidebar_state="expanded")

st.title("⚽ Fútbol Analytics — Copa del Mundo 2022")
st.caption("Dashboard sobre StatsBomb Open Data · ETL → SQLite → KPIs → xG → "
           "scouting → carga física. Usá el menú de la izquierda para navegar.")

# --------------------------------------------------------------------------- #
# Métricas principales
# --------------------------------------------------------------------------- #
matches = load_table("matches")
shots = load_table("shots")
players = load_table("players")
teams = load_table("teams")

goals_in_play = int(shots[(shots["period"] < 5) & (shots["is_goal"] == 1)].shape[0])

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Partidos", len(matches))
c2.metric("Equipos", len(teams))
c3.metric("Jugadores", f"{len(players):,}")
c4.metric("Tiros", f"{len(shots):,}")
c5.metric("Goles (en juego)", goals_in_play)

st.divider()

# --------------------------------------------------------------------------- #
# Gráficos de resumen
# --------------------------------------------------------------------------- #
team_kpis = load_table("team_kpis")
player_kpis = load_table("player_kpis")

left, right = st.columns(2)

with left:
    top_scorers = player_kpis.nlargest(10, "goals")[["player_name", "goals"]]
    st.plotly_chart(
        charts.top_bar(top_scorers, "goals", "player_name",
                       "Top 10 goleadores", color="#9467bd"),
        width="stretch")

with right:
    st.plotly_chart(charts.team_xg_vs_goals(team_kpis), width="stretch")

st.divider()
with st.expander("ℹ️ Sobre los datos y el proyecto"):
    st.markdown(
        "- **Fuente:** [StatsBomb Open Data](https://github.com/statsbomb/open-data) "
        "— Copa del Mundo 2022 (64 partidos).\n"
        "- **Pipeline:** ETL reproducible → SQLite → KPIs → modelo de xG "
        "(ROC-AUC 0.80, correlación 0.89 vs StatsBomb) → scouting → ACWR.\n"
        "- **Módulo físico (ACWR):** datos de carga **simulados** (StatsBomb no "
        "incluye GPS); es una demostración metodológica.\n"
        "- Repo: `github.com/oyar23/futbol-analytics`.")
