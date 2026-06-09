"""Carga física simulada + ACWR (Acute:Chronic Workload Ratio) + alertas.

⚠️  IMPORTANTE — MÓDULO METODOLÓGICO (DATOS SIMULADOS)
------------------------------------------------------
StatsBomb Open Data **NO** incluye datos de GPS / carga física. Por lo tanto,
este módulo **genera datos de carga simulados** de forma realista, derivados de:
  - los minutos efectivamente jugados por cada jugador en cada partido,
  - la intensidad del partido (mayor en fase de eliminación),
  - sesiones de entrenamiento sintéticas (pre-torneo y entre partidos).

No son datos reales: el objetivo es **demostrar la metodología** de monitoreo de
carga (ACWR) y alertas de riesgo de lesión, tal como se haría en un club con
datos reales de GPS.

Metodología ACWR:
  - Carga aguda  = media móvil de 7 días.
  - Carga crónica = media móvil de 28 días.
  - ACWR = carga aguda / carga crónica.
  - Zonas de riesgo (literatura de carga deportiva):
        ACWR < 0.8        → Subcarga (riesgo por falta de estímulo)
        0.8 ≤ ACWR ≤ 1.3  → Zona óptima ("sweet spot")
        1.3 < ACWR ≤ 1.5  → Precaución
        ACWR > 1.5        → Riesgo alto de lesión
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import config  # noqa: E402

# Mínimo de minutos en el torneo para incluir a un jugador en la simulación
MIN_MINUTES = 180

# Parámetros de la simulación de carga (unidades arbitrarias, "AU")
MATCH_INTENSITY_PER_MIN = 9.0      # AU por minuto jugado en partido
KNOCKOUT_BONUS = 1.5               # intensidad extra en eliminación directa
CHRONIC_WINDOW = 28                # días (carga crónica)
ACUTE_WINDOW = 7                   # días (carga aguda)

KNOCKOUT_STAGES = {
    "Round of 16", "Quarter-finals", "Semi-finals", "Final",
    "3rd Place Final",
}


def _load_participation(db_path: Path) -> pd.DataFrame:
    """Carga la participación por partido (minutos + fecha + etapa)."""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            """
            SELECT l.player_id, l.player_name, l.team_name,
                   l.minutes_played, m.match_date, m.stage
            FROM lineups l
            JOIN matches m ON l.match_id = m.match_id
            WHERE l.minutes_played > 0
            """, conn)
    finally:
        conn.close()
    df["match_date"] = pd.to_datetime(df["match_date"])
    return df


def _simulate_player_load(player_matches: pd.DataFrame,
                          rng: np.random.Generator) -> pd.DataFrame:
    """Simula la serie diaria de carga de un jugador.

    Combina la carga de los partidos (según minutos e intensidad) con sesiones
    de entrenamiento sintéticas. El rango temporal empieza 28 días antes del
    primer partido (para construir una línea base de carga crónica) y termina
    en el último partido.

    Args:
        player_matches: Filas de participación del jugador (1 por partido).
        rng: Generador aleatorio (sembrado por jugador → reproducible).

    Returns:
        DataFrame diario con columnas ``date``, ``load`` y ``session_type``.
    """
    match_days = {
        row.match_date.normalize(): row
        for row in player_matches.itertuples(index=False)
    }
    first = min(match_days)
    last = max(match_days)
    start = first - pd.Timedelta(days=CHRONIC_WINDOW)
    dates = pd.date_range(start=start, end=last, freq="D")

    rows = []
    for d in dates:
        d_norm = d.normalize()
        if d_norm in match_days:
            row = match_days[d_norm]
            intensity = MATCH_INTENSITY_PER_MIN
            if row.stage in KNOCKOUT_STAGES:
                intensity += KNOCKOUT_BONUS
            load = row.minutes_played * intensity + rng.normal(0, 20)
            session = "Partido"
        else:
            # Proximidad al partido más cercano define el tipo de sesión
            nearest = min(abs((d_norm - md).days) for md in match_days)
            prev_match = any((d_norm - md).days == 1 for md in match_days)
            next_match = any((md - d_norm).days == 1 for md in match_days)
            weekday = d_norm.dayofweek

            # Rampa de pretemporada: en el camp previo al torneo la carga
            # arranca baja y sube progresivamente (línea base de carga crónica
            # realista: los jugadores llegan tras el parate de clubes).
            if d_norm < first:
                days_to_first = (first - d_norm).days
                ramp = 0.50 + 0.50 * (1 - days_to_first / CHRONIC_WINDOW)
            else:
                ramp = 1.0

            if prev_match:
                # Día posterior al partido: recuperación / descanso
                load = rng.uniform(80, 200)
                session = "Recuperación"
            elif next_match:
                # Víspera de partido: activación ligera
                load = rng.uniform(250, 380)
                session = "Activación"
            elif weekday == 0 and nearest > 2:
                # Día de descanso semanal
                load = 0.0
                session = "Descanso"
            else:
                # Entrenamiento normal (con rampa en pretemporada)
                load = rng.uniform(420, 620) * ramp
                session = "Entrenamiento"
        rows.append({"date": d_norm, "load": round(max(0.0, load), 1),
                     "session_type": session})

    out = pd.DataFrame(rows)
    out["player_id"] = player_matches["player_id"].iloc[0]
    out["player_name"] = player_matches["player_name"].iloc[0]
    out["team_name"] = player_matches["team_name"].iloc[0]
    return out


def simulate_daily_load(db_path: Path | None = None) -> pd.DataFrame:
    """Genera la serie diaria de carga simulada para todos los jugadores.

    Returns:
        DataFrame con una fila por (jugador, día).
    """
    db_path = db_path or config.DB_PATH
    part = _load_participation(db_path)

    # Filtrar a jugadores con minutos suficientes en el torneo
    totals = part.groupby("player_id")["minutes_played"].sum()
    keep = totals[totals >= MIN_MINUTES].index
    part = part[part["player_id"].isin(keep)]

    frames = []
    for pid, grp in part.groupby("player_id"):
        rng = np.random.default_rng(int(pid))  # semilla reproducible por jugador
        frames.append(_simulate_player_load(grp, rng))
    return pd.concat(frames, ignore_index=True)


def _classify_risk(acwr: float) -> str:
    """Clasifica un valor de ACWR en su zona de riesgo."""
    if np.isnan(acwr):
        return "Sin datos"
    if acwr < 0.8:
        return "Subcarga"
    if acwr <= 1.3:
        return "Óptimo"
    if acwr <= 1.5:
        return "Precaución"
    return "Riesgo alto"


def compute_acwr(load_df: pd.DataFrame) -> pd.DataFrame:
    """Calcula carga aguda, crónica, ACWR y zona de riesgo por jugador.

    Args:
        load_df: Salida de :func:`simulate_daily_load`.

    Returns:
        El mismo DataFrame con columnas ``acute_7d``, ``chronic_28d``,
        ``acwr`` y ``risk_zone``.
    """
    result = load_df.sort_values(["player_id", "date"]).copy()

    # Medias móviles por jugador con transform (preserva columnas e índice)
    grouped_load = result.groupby("player_id")["load"]
    result["acute_7d"] = grouped_load.transform(
        lambda s: s.rolling(ACUTE_WINDOW, min_periods=ACUTE_WINDOW).mean()).round(1)
    result["chronic_28d"] = grouped_load.transform(
        lambda s: s.rolling(CHRONIC_WINDOW, min_periods=CHRONIC_WINDOW).mean()).round(1)
    result["acwr"] = (result["acute_7d"] / result["chronic_28d"]).round(2)
    result["risk_zone"] = result["acwr"].apply(_classify_risk)
    return result


def generate_alerts(acwr_df: pd.DataFrame) -> pd.DataFrame:
    """Genera alertas de riesgo de lesión (ACWR fuera de la zona óptima).

    Returns:
        DataFrame con los días en zona de riesgo (Precaución / Riesgo alto /
        Subcarga), ordenado por severidad y fecha.
    """
    risky = acwr_df[acwr_df["risk_zone"].isin(
        ["Riesgo alto", "Precaución", "Subcarga"])].copy()
    severity = {"Riesgo alto": 0, "Precaución": 1, "Subcarga": 2}
    risky["severity"] = risky["risk_zone"].map(severity)
    cols = ["player_name", "team_name", "date", "acute_7d", "chronic_28d",
            "acwr", "risk_zone"]
    return (risky.sort_values(["severity", "date"])[cols]
            .reset_index(drop=True))


def plot_player_acwr(acwr_df: pd.DataFrame, player_name: str,
                     figures_dir: Path | None = None) -> Path:
    """Grafica la carga diaria y el ACWR de un jugador con zonas de riesgo.

    Returns:
        Ruta del PNG generado.
    """
    figures_dir = figures_dir or config.FIGURES_DIR
    grp = acwr_df[acwr_df["player_name"].str.contains(
        player_name, case=False, na=False)]
    if grp.empty:
        raise ValueError(f"No se encontró el jugador '{player_name}'.")
    name = grp["player_name"].iloc[0]
    grp = grp[grp["player_id"] == grp["player_id"].iloc[0]].sort_values("date")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1.5]})

    # Carga diaria + medias móviles
    ax1.bar(grp["date"], grp["load"], width=0.8, color="#b0c4de",
            label="Carga diaria (AU)")
    ax1.plot(grp["date"], grp["acute_7d"], color="#1f77b4", lw=2,
             label="Carga aguda (7d)")
    ax1.plot(grp["date"], grp["chronic_28d"], color="#2ca02c", lw=2,
             label="Carga crónica (28d)")
    ax1.set_ylabel("Carga (AU)")
    ax1.set_title(f"Carga física simulada y ACWR — {name}\n"
                  f"(DATOS SIMULADOS · demostración metodológica)", fontsize=12)
    ax1.legend(loc="upper left", fontsize=9)

    # ACWR con zonas de riesgo
    ax2.axhspan(0.8, 1.3, color="#c8e6c9", alpha=0.6, label="Zona óptima")
    ax2.axhspan(1.3, 1.5, color="#fff3c4", alpha=0.7, label="Precaución")
    ax2.axhspan(1.5, 2.5, color="#ffcdd2", alpha=0.7, label="Riesgo alto")
    ax2.axhspan(0.0, 0.8, color="#e0e0e0", alpha=0.6, label="Subcarga")
    ax2.plot(grp["date"], grp["acwr"], color="black", lw=2, marker="o", ms=3)
    ax2.axhline(1.0, color="gray", ls="--", lw=0.8)
    ax2.set_ylim(0, 2.2)
    ax2.set_ylabel("ACWR")
    ax2.set_xlabel("Fecha")
    ax2.legend(loc="upper left", fontsize=8, ncol=2)

    fig.autofmt_xdate()
    fig.tight_layout()

    def _slug(s: str) -> str:
        return "".join(ch if ch.isalnum() else "_" for ch in s).strip("_")[:25]

    path = figures_dir / f"acwr_{_slug(name)}.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  Gráfico ACWR guardado: {path.name}")
    return path


def run() -> pd.DataFrame:
    """Punto de entrada: simula carga, calcula ACWR, alerta y exporta."""
    print("=" * 60)
    print("CARGA FÍSICA (SIMULADA) + ACWR + ALERTAS")
    print("=" * 60)
    print("  ⚠ Datos de carga SIMULADOS (StatsBomb no incluye GPS).")

    load_df = simulate_daily_load()
    print(f"  Serie diaria simulada: {len(load_df)} filas "
          f"({load_df['player_id'].nunique()} jugadores)")

    acwr_df = compute_acwr(load_df)
    alerts = generate_alerts(acwr_df)

    n_high = (acwr_df["risk_zone"] == "Riesgo alto").sum()
    n_caution = (acwr_df["risk_zone"] == "Precaución").sum()
    print(f"  Días en 'Riesgo alto': {n_high}  |  'Precaución': {n_caution}")
    print(f"  Alertas generadas: {len(alerts)}")

    # Exports
    config.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    acwr_path = config.EXPORTS_DIR / "acwr_serie.csv"
    cols = ["player_id", "player_name", "team_name", "date", "session_type",
            "load", "acute_7d", "chronic_28d", "acwr", "risk_zone"]
    acwr_df[cols].to_csv(acwr_path, index=False, encoding="utf-8-sig")
    print(f"  Serie ACWR exportada: {acwr_path.name}")

    alerts_path = config.EXPORTS_DIR / "acwr_alertas.csv"
    alerts.to_csv(alerts_path, index=False, encoding="utf-8-sig")
    print(f"  Alertas exportadas: {alerts_path.name}")

    # Gráfico de ejemplo (un jugador con muchos partidos)
    try:
        plot_player_acwr(acwr_df, "Messi")
    except ValueError:
        # fallback: el primer jugador disponible
        plot_player_acwr(acwr_df, acwr_df["player_name"].iloc[0])

    return acwr_df


if __name__ == "__main__":
    run()
