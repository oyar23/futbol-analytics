"""Constructores de figuras Plotly para el dashboard (funciones puras).

No dependen de Streamlit: reciben DataFrames y devuelven figuras Plotly, lo que
permite testearlas de forma aislada.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Paleta y métricas del radar (alineadas con el módulo de scouting)
RADAR_METRICS = [
    ("xg_per90_pct", "xG / 90"),
    ("shots_per90_pct", "Tiros / 90"),
    ("key_passes_per90_pct", "Pases clave / 90"),
    ("passes_per90_pct", "Pases / 90"),
    ("pass_completion_pct_pct", "% Pase"),
    ("dribbles_per90_pct", "Regates / 90"),
    ("recoveries_per90_pct", "Recuperac. / 90"),
    ("def_actions_per90_pct", "Acc. def. / 90"),
]

RISK_COLORS = {
    "Subcarga": "#9e9e9e",
    "Óptimo": "#2ca02c",
    "Precaución": "#ff9800",
    "Riesgo alto": "#d62728",
    "Sin datos": "#cccccc",
}


def team_xg_vs_goals(team_kpis: pd.DataFrame) -> go.Figure:
    """Scatter de xG total vs goles reales por equipo (línea = esperado)."""
    fig = px.scatter(
        team_kpis, x="xg", y="goals", text="team_name",
        hover_data={"xg": ":.2f", "goals": True, "team_name": False},
        labels={"xg": "xG total", "goals": "Goles"},
    )
    fig.update_traces(textposition="top center", textfont_size=9,
                      marker=dict(size=11, color="#1f77b4"))
    lim = float(max(team_kpis["xg"].max(), team_kpis["goals"].max())) + 1
    fig.add_trace(go.Scatter(x=[0, lim], y=[0, lim], mode="lines",
                             line=dict(dash="dash", color="gray"),
                             showlegend=False, hoverinfo="skip"))
    fig.update_layout(title="xG total vs goles reales por equipo", height=520)
    return fig


def top_bar(df: pd.DataFrame, value_col: str, label_col: str,
            title: str, color: str = "#1f77b4") -> go.Figure:
    """Barra horizontal de ranking (mayor arriba)."""
    d = df.sort_values(value_col, ascending=True)
    fig = px.bar(d, x=value_col, y=label_col, orientation="h", title=title)
    fig.update_traces(marker_color=color)
    fig.update_layout(height=max(320, 26 * len(d)), yaxis_title="",
                      xaxis_title=value_col)
    return fig


def _add_pitch(fig: go.Figure) -> None:
    """Dibuja las líneas del campo (mitad de ataque) sobre una figura."""
    line = dict(color="rgba(80,80,80,0.6)", width=1)
    # Borde del campo (mitad de ataque)
    fig.add_shape(type="rect", x0=60, y0=0, x1=120, y1=80, line=line)
    # Área grande
    fig.add_shape(type="rect", x0=102, y0=18, x1=120, y1=62, line=line)
    # Área chica
    fig.add_shape(type="rect", x0=114, y0=30, x1=120, y1=50, line=line)
    # Arco
    fig.add_shape(type="line", x0=120, y0=36, x1=120, y1=44,
                  line=dict(color="black", width=4))
    # Punto de penal
    fig.add_shape(type="circle", x0=107.8, y0=39.8, x1=108.2, y1=40.2,
                  line=dict(color="rgba(80,80,80,0.6)"), fillcolor="rgba(80,80,80,0.6)")


def shot_map(shots: pd.DataFrame) -> go.Figure:
    """Mapa de tiros interactivo con hover (jugador, minuto, xG, desenlace).

    Los goles se muestran más grandes y en rojo; el resto, semitransparente.
    """
    fig = go.Figure()
    _add_pitch(fig)

    no_goal = shots[shots["is_goal"] == 0]
    goal = shots[shots["is_goal"] == 1]

    custom_cols = ["player_name", "team_name", "minute", "statsbomb_xg",
                   "outcome", "shot_type"]
    hovertemplate = (
        "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
        "Minuto %{customdata[2]} · %{customdata[5]}<br>"
        "xG: %{customdata[3]:.2f} · %{customdata[4]}<extra></extra>")

    fig.add_trace(go.Scatter(
        x=no_goal["location_x"], y=no_goal["location_y"], mode="markers",
        name="Sin gol", marker=dict(size=7, color="#1f77b4", opacity=0.35),
        customdata=no_goal[custom_cols].values, hovertemplate=hovertemplate))

    fig.add_trace(go.Scatter(
        x=goal["location_x"], y=goal["location_y"], mode="markers",
        name="Gol", marker=dict(size=12, color="#d62728",
                                line=dict(width=1, color="white")),
        customdata=goal[custom_cols].values, hovertemplate=hovertemplate))

    fig.update_xaxes(range=[60, 122], showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(range=[0, 80], showgrid=False, zeroline=False, visible=False,
                     scaleanchor="x", scaleratio=1)
    fig.update_layout(title="Mapa de tiros (pasá el mouse por un punto)",
                      height=620, legend=dict(orientation="h", y=1.02),
                      plot_bgcolor="rgba(240,245,240,1)")
    return fig


def radar(pa: pd.Series, pb: pd.Series) -> go.Figure:
    """Radar comparativo de percentiles entre dos jugadores."""
    labels = [lbl for _, lbl in RADAR_METRICS]
    cols = [c for c, _ in RADAR_METRICS]
    va = pa[cols].astype(float).tolist()
    vb = pb[cols].astype(float).tolist()
    # Cerrar el polígono
    labels_c = labels + labels[:1]
    va += va[:1]
    vb += vb[:1]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=va, theta=labels_c, fill="toself",
                                  name=f"{pa['player_name']} ({pa['team_name']})",
                                  line_color="#1f77b4"))
    fig.add_trace(go.Scatterpolar(r=vb, theta=labels_c, fill="toself",
                                  name=f"{pb['player_name']} ({pb['team_name']})",
                                  line_color="#d62728"))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="Comparativa de percentiles (dentro del grupo posicional)",
        height=560, legend=dict(orientation="h", y=-0.1))
    return fig


def acwr_figure(player_series: pd.DataFrame) -> go.Figure:
    """Carga diaria + medias móviles + ACWR con zonas de riesgo."""
    d = player_series.sort_values("date").copy()
    d["date"] = pd.to_datetime(d["date"])

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.6, 0.4], vertical_spacing=0.08,
                        subplot_titles=("Carga diaria (AU) y medias móviles",
                                        "ACWR (aguda 7d / crónica 28d)"))

    fig.add_trace(go.Bar(x=d["date"], y=d["load"], name="Carga diaria",
                         marker_color="#b0c4de"), row=1, col=1)
    fig.add_trace(go.Scatter(x=d["date"], y=d["acute_7d"], name="Aguda (7d)",
                             line=dict(color="#1f77b4")), row=1, col=1)
    fig.add_trace(go.Scatter(x=d["date"], y=d["chronic_28d"], name="Crónica (28d)",
                             line=dict(color="#2ca02c")), row=1, col=1)

    # Zonas de riesgo en el panel inferior
    fig.add_hrect(y0=0.0, y1=0.8, fillcolor="#9e9e9e", opacity=0.15,
                  line_width=0, row=2, col=1)
    fig.add_hrect(y0=0.8, y1=1.3, fillcolor="#2ca02c", opacity=0.18,
                  line_width=0, row=2, col=1)
    fig.add_hrect(y0=1.3, y1=1.5, fillcolor="#ff9800", opacity=0.20,
                  line_width=0, row=2, col=1)
    fig.add_hrect(y0=1.5, y1=2.5, fillcolor="#d62728", opacity=0.18,
                  line_width=0, row=2, col=1)
    fig.add_trace(go.Scatter(x=d["date"], y=d["acwr"], name="ACWR",
                             line=dict(color="black"), mode="lines+markers",
                             marker=dict(size=4)), row=2, col=1)
    fig.update_yaxes(range=[0, 2.2], row=2, col=1)
    fig.update_layout(height=620, legend=dict(orientation="h", y=1.08),
                      title="Monitor de carga y ACWR")
    return fig


def xg_scatter(pred: pd.DataFrame) -> go.Figure:
    """Scatter del xG del modelo propio vs el oficial de StatsBomb."""
    m = pred.dropna(subset=["predicted_xg", "statsbomb_xg"])
    m = m[m["shot_type"] != "Penalty"]
    r = float(np.corrcoef(m["predicted_xg"], m["statsbomb_xg"])[0, 1])

    fig = px.scatter(
        m, x="statsbomb_xg", y="predicted_xg",
        hover_data={"player_name": True, "team_name": True,
                    "statsbomb_xg": ":.2f", "predicted_xg": ":.2f"},
        labels={"statsbomb_xg": "StatsBomb xG", "predicted_xg": "xG modelo propio"},
        opacity=0.4)
    fig.update_traces(marker=dict(size=6, color="#1f77b4"))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines",
                             line=dict(dash="dash", color="red"),
                             showlegend=False, hoverinfo="skip"))
    fig.update_layout(title=f"xG modelo propio vs StatsBomb (r = {r:.3f})",
                      height=520)
    return fig, r
