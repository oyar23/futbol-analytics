"""Página del mapa de tiros interactivo (hover con jugador, minuto, xG)."""
import streamlit as st

import charts
from utils import load_table

st.set_page_config(page_title="Mapa de tiros · Fútbol Analytics", page_icon="🎯",
                   layout="wide")
st.title("🎯 Mapa de tiros interactivo")
st.caption("Pasá el mouse por cualquier punto para ver **quién** lo remató, en "
           "qué minuto, con qué xG y el desenlace. Usá los filtros para acotar.")

shots = load_table("shots")
# Solo tiros en juego con ubicación (sin tandas)
shots = shots[(shots["period"] < 5) & shots["location_x"].notna()].copy()

# --------------------------------------------------------------------------- #
# Filtros
# --------------------------------------------------------------------------- #
f1, f2, f3 = st.columns(3)
teams = sorted(shots["team_name"].dropna().unique())
team_sel = f1.multiselect("Equipo(s)", teams, default=[])

df = shots if not team_sel else shots[shots["team_name"].isin(team_sel)]

players = sorted(df["player_name"].dropna().unique())
player_sel = f2.multiselect("Jugador(es)", players, default=[])
if player_sel:
    df = df[df["player_name"].isin(player_sel)]

shot_types = sorted(df["shot_type"].dropna().unique())
type_sel = f3.multiselect("Tipo de jugada", shot_types, default=[])
if type_sel:
    df = df[df["shot_type"].isin(type_sel)]

only_goals = st.checkbox("Mostrar solo goles", value=False)
if only_goals:
    df = df[df["is_goal"] == 1]

# --------------------------------------------------------------------------- #
# Métricas + gráfico
# --------------------------------------------------------------------------- #
c1, c2, c3 = st.columns(3)
c1.metric("Tiros mostrados", f"{len(df):,}")
c2.metric("Goles", int(df["is_goal"].sum()))
c3.metric("xG total", f"{df['statsbomb_xg'].sum():.2f}")

if df.empty:
    st.warning("No hay tiros con los filtros seleccionados.")
else:
    st.plotly_chart(charts.shot_map(df), width="stretch")

    with st.expander("Ver tabla de tiros filtrados"):
        cols = ["player_name", "team_name", "minute", "shot_type", "body_part",
                "outcome", "statsbomb_xg", "distance"]
        st.dataframe(df[cols].sort_values("statsbomb_xg", ascending=False),
                     width="stretch", hide_index=True)
