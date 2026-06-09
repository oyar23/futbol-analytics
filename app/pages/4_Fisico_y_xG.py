"""Página de carga física (ACWR) y validación del modelo de xG."""
import streamlit as st

import charts
from utils import load_table

st.set_page_config(page_title="Físico y xG · Fútbol Analytics", page_icon="🏃",
                   layout="wide")
st.title("🏃 Carga física (ACWR) y modelo de xG")

tab_acwr, tab_xg = st.tabs(["🏃 Monitor de carga (ACWR)", "🤖 Modelo de xG"])

# --------------------------------------------------------------------------- #
# ACWR
# --------------------------------------------------------------------------- #
with tab_acwr:
    st.warning("⚠️ **Datos de carga SIMULADOS** — StatsBomb no incluye GPS. "
               "Es una demostración metodológica del monitoreo de carga (ACWR).")

    series = load_table("acwr_series")
    alerts = load_table("acwr_alerts")

    names = sorted(series["player_name"].dropna().unique())
    default = next((i for i, n in enumerate(names) if "Messi" in n), 0)
    player = st.selectbox("Jugador", names, index=default)

    pdata = series[series["player_name"] == player]
    st.plotly_chart(charts.acwr_figure(pdata), width="stretch")

    st.subheader(f"Alertas de riesgo — {player}")
    pa = alerts[alerts["player_name"] == player]
    if pa.empty:
        st.success("Sin días fuera de la zona óptima para este jugador.")
    else:
        st.dataframe(pa[["date", "acute_7d", "chronic_28d", "acwr", "risk_zone"]],
                     width="stretch", hide_index=True)

    st.divider()
    st.subheader("Alertas de 'Riesgo alto' en todo el plantel")
    high = alerts[alerts["risk_zone"] == "Riesgo alto"]
    st.caption(f"{len(high)} días-jugador en riesgo alto (ACWR > 1.5).")
    st.dataframe(high[["player_name", "team_name", "date", "acwr", "risk_zone"]],
                 width="stretch", hide_index=True)

# --------------------------------------------------------------------------- #
# Modelo de xG
# --------------------------------------------------------------------------- #
with tab_xg:
    st.markdown("Comparación de nuestro modelo de xG (LogisticRegression) contra "
                "el xG oficial de StatsBomb, sobre los tiros en juego.")

    pred = load_table("xg_predictions")
    fig, r = charts.xg_scatter(pred)

    c1, c2 = st.columns([1, 3])
    c1.metric("Correlación de Pearson", f"{r:.3f}")
    c1.metric("ROC-AUC (CV 5-fold)", "0.802")
    c1.caption("El modelo reproduce de cerca un xG profesional usando solo "
               "features públicas.")
    c2.plotly_chart(fig, width="stretch")

    with st.expander("Ver tiros con mayor xG predicho"):
        cols = ["player_name", "team_name", "minute", "shot_type", "is_goal",
                "statsbomb_xg", "predicted_xg"]
        top = pred.dropna(subset=["predicted_xg"]).nlargest(20, "predicted_xg")
        st.dataframe(top[cols], width="stretch", hide_index=True)
