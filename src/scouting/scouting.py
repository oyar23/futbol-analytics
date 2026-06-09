"""Scouting: métricas por 90 minutos, percentiles por posición y radares.

Calcula un conjunto de métricas por 90 minutos para cada jugador, los agrupa
por posición (GK / DEF / MID / FWD) y calcula percentiles dentro de cada grupo
posicional. Permite comparar dos jugadores de la misma posición con un radar.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")  # backend sin ventana (para guardar figuras en disco)
import matplotlib.pyplot as plt  # noqa: E402

import config  # noqa: E402

# Minutos mínimos para entrar en el grupo de comparación (percentiles)
MIN_MINUTES = 180

# Métricas del radar: (columna, etiqueta para mostrar)
RADAR_METRICS = [
    ("xg_per90", "xG / 90"),
    ("shots_per90", "Tiros / 90"),
    ("key_passes_per90", "Pases clave / 90"),
    ("passes_per90", "Pases / 90"),
    ("pass_completion_pct", "% Pase"),
    ("dribbles_per90", "Regates / 90"),
    ("recoveries_per90", "Recuperac. / 90"),
    ("def_actions_per90", "Acc. def. / 90"),
]


def _position_group(position: str | None) -> str:
    """Mapea una posición de StatsBomb a un grupo: GK / DEF / MID / FWD."""
    if not isinstance(position, str) or not position:
        return "UNK"
    if position == "Goalkeeper":
        return "GK"
    # "Wing Back" contiene "Back" → se clasifica como defensor (antes que Wing)
    if "Back" in position:
        return "DEF"
    if "Midfield" in position:
        return "MID"
    if "Wing" in position or "Forward" in position or "Striker" in position:
        return "FWD"
    return "UNK"


def build_player_metrics(db_path: Path | None = None) -> pd.DataFrame:
    """Construye la tabla de métricas por 90 por jugador.

    Returns:
        DataFrame con minutos, grupo posicional y métricas por 90.
    """
    db_path = db_path or config.DB_PATH
    conn = sqlite3.connect(db_path)
    try:
        # Minutos y posición principal (la de más minutos) por jugador
        lineups = pd.read_sql_query(
            "SELECT player_id, player_name, team_name, position, "
            "SUM(minutes_played) AS minutes FROM lineups "
            "GROUP BY player_id, player_name, team_name, position", conn)

        # Conteos de eventos por jugador y tipo
        events = pd.read_sql_query(
            "SELECT player_id, type_name, "
            "SUM(CASE WHEN type_name='Pass' THEN 1 ELSE 0 END) AS dummy "
            "FROM events GROUP BY player_id, type_name", conn)

        passes = pd.read_sql_query(
            "SELECT player_id, "
            "COUNT(*) AS passes, "
            "SUM(pass_complete) AS passes_completed, "
            "SUM(shot_assist) AS key_passes, "
            "SUM(goal_assist) AS assists "
            "FROM events WHERE type_name='Pass' GROUP BY player_id", conn)

        type_counts = pd.read_sql_query(
            "SELECT player_id, type_name, COUNT(*) AS n "
            "FROM events GROUP BY player_id, type_name", conn)

        shots = pd.read_sql_query(
            "SELECT player_id, COUNT(*) AS shots, SUM(is_goal) AS goals, "
            "SUM(statsbomb_xg) AS xg FROM shots WHERE period < 5 "
            "GROUP BY player_id", conn)
    finally:
        conn.close()

    # Posición principal = la de más minutos
    idx = lineups.groupby("player_id")["minutes"].idxmax()
    primary = lineups.loc[idx, ["player_id", "position"]].rename(
        columns={"position": "primary_position"})
    total_min = lineups.groupby(
        ["player_id", "player_name", "team_name"], as_index=False)["minutes"].sum()
    base = total_min.merge(primary, on="player_id", how="left")
    base["position_group"] = base["primary_position"].map(_position_group)

    # Conteos por tipo de evento → columnas
    pivot = type_counts.pivot_table(index="player_id", columns="type_name",
                                    values="n", fill_value=0).reset_index()

    def _col(df, name):
        return df[name] if name in df.columns else 0

    pivot["dribbles"] = _col(pivot, "Dribble")
    pivot["recoveries"] = _col(pivot, "Ball Recovery")
    pivot["def_actions"] = (_col(pivot, "Interception") + _col(pivot, "Clearance")
                            + _col(pivot, "Block") + _col(pivot, "Duel"))

    df = (base
          .merge(shots, on="player_id", how="left")
          .merge(passes, on="player_id", how="left")
          .merge(pivot[["player_id", "dribbles", "recoveries", "def_actions"]],
                 on="player_id", how="left"))

    count_cols = ["shots", "goals", "xg", "passes", "passes_completed",
                  "key_passes", "assists", "dribbles", "recoveries", "def_actions"]
    df[count_cols] = df[count_cols].fillna(0)

    # Métricas por 90
    per90 = df["minutes"] / 90.0
    per90 = per90.replace(0, np.nan)
    for raw, new in [("xg", "xg_per90"), ("shots", "shots_per90"),
                     ("key_passes", "key_passes_per90"), ("passes", "passes_per90"),
                     ("dribbles", "dribbles_per90"), ("recoveries", "recoveries_per90"),
                     ("def_actions", "def_actions_per90"), ("goals", "goals_per90"),
                     ("assists", "assists_per90")]:
        df[new] = (df[raw] / per90).round(3)

    df["pass_completion_pct"] = (
        100.0 * df["passes_completed"] / df["passes"].replace(0, np.nan)).round(1)
    df["pass_completion_pct"] = df["pass_completion_pct"].fillna(0)
    df["minutes"] = df["minutes"].round(0)

    return df


def compute_percentiles(df: pd.DataFrame,
                        min_minutes: int = MIN_MINUTES) -> pd.DataFrame:
    """Calcula percentiles de cada métrica dentro del grupo posicional.

    Solo se consideran jugadores con al menos ``min_minutes`` para que los
    percentiles sean representativos. Devuelve el DataFrame filtrado con una
    columna ``<metrica>_pct`` por cada métrica del radar.
    """
    pool = df[(df["minutes"] >= min_minutes) &
              (df["position_group"].isin(["GK", "DEF", "MID", "FWD"]))].copy()

    metric_cols = [m for m, _ in RADAR_METRICS]
    for col in metric_cols:
        pct_col = f"{col}_pct"
        pool[pct_col] = (pool.groupby("position_group")[col]
                         .rank(pct=True) * 100).round(1)
    return pool


def export_percentiles(pool: pd.DataFrame,
                       exports_dir: Path | None = None) -> None:
    """Exporta la tabla de percentiles a CSV."""
    exports_dir = exports_dir or config.EXPORTS_DIR
    cols = (["player_name", "team_name", "primary_position", "position_group",
             "minutes"]
            + [m for m, _ in RADAR_METRICS]
            + [f"{m}_pct" for m, _ in RADAR_METRICS])
    path = exports_dir / "scouting_percentiles.csv"
    pool[cols].sort_values(["position_group", "player_name"]).to_csv(
        path, index=False, encoding="utf-8-sig")
    print(f"  Percentiles exportados: {path.name} ({len(pool)} jugadores)")


def _find_player(pool: pd.DataFrame, name: str) -> pd.Series:
    """Busca un jugador por coincidencia parcial de nombre (case-insensitive)."""
    matches = pool[pool["player_name"].str.contains(name, case=False, na=False)]
    if matches.empty:
        raise ValueError(f"No se encontró ningún jugador que contenga '{name}' "
                         f"(con al menos {MIN_MINUTES} minutos).")
    return matches.iloc[0]


def compare_players(player_a: str, player_b: str,
                    pool: pd.DataFrame | None = None,
                    figures_dir: Path | None = None) -> Path:
    """Genera un radar comparativo de percentiles entre dos jugadores.

    Ambos deben pertenecer al mismo grupo posicional (los percentiles solo son
    comparables dentro de la misma posición).

    Args:
        player_a: Nombre (o parte) del primer jugador.
        player_b: Nombre (o parte) del segundo jugador.
        pool: Tabla de percentiles. Si es ``None``, se calcula al vuelo.
        figures_dir: Carpeta de salida. Por defecto ``config.FIGURES_DIR``.

    Returns:
        Ruta del PNG generado.
    """
    figures_dir = figures_dir or config.FIGURES_DIR
    if pool is None:
        pool = compute_percentiles(build_player_metrics())

    pa = _find_player(pool, player_a)
    pb = _find_player(pool, player_b)

    if pa["position_group"] != pb["position_group"]:
        raise ValueError(
            f"Los jugadores son de grupos distintos "
            f"({pa['player_name']}={pa['position_group']}, "
            f"{pb['player_name']}={pb['position_group']}). "
            f"El radar solo compara jugadores de la misma posición.")

    labels = [lbl for _, lbl in RADAR_METRICS]
    pct_cols = [f"{m}_pct" for m, _ in RADAR_METRICS]
    values_a = pa[pct_cols].astype(float).tolist()
    values_b = pb[pct_cols].astype(float).tolist()

    # Cerrar el polígono
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]
    values_a += values_a[:1]
    values_b += values_b[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=8, color="gray")

    color_a, color_b = "#1f77b4", "#d62728"
    ax.plot(angles, values_a, color=color_a, linewidth=2,
            label=f"{pa['player_name']} ({pa['team_name']})")
    ax.fill(angles, values_a, color=color_a, alpha=0.20)
    ax.plot(angles, values_b, color=color_b, linewidth=2,
            label=f"{pb['player_name']} ({pb['team_name']})")
    ax.fill(angles, values_b, color=color_b, alpha=0.20)

    group = pa["position_group"]
    ax.set_title(f"Comparativa de percentiles — {group}\n"
                 f"(Mundial 2022, jugadores con ≥ {MIN_MINUTES}' en su grupo)",
                 fontsize=13, pad=28)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), fontsize=10,
              ncol=1, frameon=True)

    # Nombre de archivo seguro
    def _slug(s: str) -> str:
        return "".join(ch if ch.isalnum() else "_" for ch in s).strip("_")[:25]

    path = figures_dir / f"radar_{_slug(pa['player_name'])}_vs_{_slug(pb['player_name'])}.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  Radar guardado: {path.name}")
    return path


def run() -> pd.DataFrame:
    """Punto de entrada: métricas, percentiles, export y radares de ejemplo."""
    print("=" * 60)
    print("SCOUTING — métricas por 90, percentiles por posición y radares")
    print("=" * 60)

    metrics = build_player_metrics()
    pool = compute_percentiles(metrics)
    print(f"  Jugadores en el pool (≥ {MIN_MINUTES}'): {len(pool)}")
    for grp in ["GK", "DEF", "MID", "FWD"]:
        print(f"    {grp}: {(pool['position_group'] == grp).sum()}")

    export_percentiles(pool)

    # Radares de ejemplo (jugadores de la misma posición)
    examples = [("Mbappé", "Messi"), ("Modrić", "Bellingham")]
    for a, b in examples:
        try:
            compare_players(a, b, pool=pool)
        except ValueError as exc:
            print(f"  [aviso] No se pudo generar radar {a} vs {b}: {exc}")

    return pool


if __name__ == "__main__":
    run()
