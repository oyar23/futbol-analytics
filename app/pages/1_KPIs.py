"""Página de KPIs: rankings de equipos y jugadores con filtros."""
import streamlit as st

import charts
from utils import load_table

st.set_page_config(page_title="KPIs · Fútbol Analytics", page_icon="📊",
                   layout="wide")
st.title("📊 KPIs de equipos y jugadores")

tab_teams, tab_players = st.tabs(["🏳️ Equipos", "👤 Jugadores"])

# --------------------------------------------------------------------------- #
# Equipos
# --------------------------------------------------------------------------- #
with tab_teams:
    team_kpis = load_table("team_kpis")
    metric_options = {
        "Goles": "goals", "Tiros": "shots", "Tiros al arco": "shots_on_target",
        "xG total": "xg", "Pases": "passes", "% Pase": "pass_completion_pct",
        "Posesión (proxy)": "possession_pct",
    }
    metric_label = st.selectbox("Métrica a rankear", list(metric_options),
                                key="team_metric")
    col = metric_options[metric_label]
    top_n = st.slider("Cantidad de equipos", 5, 32, 12, key="team_top")

    top = team_kpis.nlargest(top_n, col)[["team_name", col]]
    st.plotly_chart(
        charts.top_bar(top, col, "team_name", f"Equipos por {metric_label}",
                       color="#d62728"),
        width="stretch")

    st.subheader("Tabla completa de KPIs por equipo")
    st.dataframe(team_kpis.sort_values(col, ascending=False),
                 width="stretch", hide_index=True)

# --------------------------------------------------------------------------- #
# Jugadores
# --------------------------------------------------------------------------- #
with tab_players:
    player_kpis = load_table("player_kpis")

    f1, f2, f3 = st.columns(3)
    teams = ["(Todos)"] + sorted(player_kpis["team_name"].dropna().unique())
    team_sel = f1.selectbox("Equipo", teams, key="pl_team")
    min_minutes = f2.slider("Minutos mínimos", 0, 700, 180, step=30, key="pl_min")
    pmetric_options = {
        "Goles": "goals", "Asistencias": "assists", "Pases clave": "key_passes",
        "xG": "xg", "xG por 90": "xg_per_90", "Tiros": "shots", "Minutos": "minutes",
    }
    pmetric_label = f3.selectbox("Métrica a rankear", list(pmetric_options),
                                 key="pl_metric")
    pcol = pmetric_options[pmetric_label]

    df = player_kpis[player_kpis["minutes"] >= min_minutes]
    if team_sel != "(Todos)":
        df = df[df["team_name"] == team_sel]

    top_p = df.nlargest(12, pcol)[["player_name", pcol]]
    st.plotly_chart(
        charts.top_bar(top_p, pcol, "player_name",
                       f"Jugadores por {pmetric_label}", color="#9467bd"),
        width="stretch")

    st.subheader("Tabla de KPIs por jugador")
    st.caption(f"{len(df)} jugadores con ≥ {min_minutes} minutos"
               + (f" · {team_sel}" if team_sel != '(Todos)' else ""))
    st.dataframe(df.sort_values(pcol, ascending=False),
                 width="stretch", hide_index=True)
