"""Exporta los datos del proyecto a JSON para el frontend en React.

Lee de ``outputs/dashboard.db`` y escribe archivos JSON compactos en
``web/public/data/`` que la app React consume de forma estática (sin servidor).
Pensado para un deploy gratuito en Vercel / Netlify / GitHub Pages.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

import config

# Destino: carpeta public/data del front React
WEB_DATA_DIR = config.BASE_DIR / "web" / "public" / "data"
DASHBOARD_DB = config.OUTPUTS_DIR / "dashboard.db"


def _write(df: pd.DataFrame, name: str, out_dir: Path) -> None:
    """Escribe un DataFrame como JSON (orient=records) redondeando floats."""
    df = df.copy()
    for col in df.select_dtypes(include=["float"]).columns:
        df[col] = df[col].round(3)
    path = out_dir / f"{name}.json"
    path.write_text(df.to_json(orient="records", force_ascii=False),
                    encoding="utf-8")
    size_kb = path.stat().st_size / 1024
    print(f"  {name}.json: {len(df):>5} filas ({size_kb:.0f} KB)")


def export_json(db_path: Path | None = None, out_dir: Path | None = None) -> Path:
    """Exporta todos los datasets necesarios para el dashboard React.

    Returns:
        La carpeta donde se escribieron los JSON.
    """
    db_path = db_path or DASHBOARD_DB
    out_dir = out_dir or WEB_DATA_DIR
    if not db_path.exists():
        raise FileNotFoundError(
            f"No existe {db_path}. Corré primero: python run_pipeline.py")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"EXPORT JSON → {out_dir.relative_to(config.BASE_DIR)}")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    try:
        team_kpis = pd.read_sql_query("SELECT * FROM team_kpis", conn)
        player_kpis = pd.read_sql_query("SELECT * FROM player_kpis", conn)
        shots = pd.read_sql_query(
            "SELECT player_name, team_name, minute, location_x, location_y, "
            "statsbomb_xg, outcome, is_goal, shot_type, body_part, distance "
            "FROM shots WHERE period < 5 AND location_x IS NOT NULL", conn)
        percentiles = pd.read_sql_query("SELECT * FROM scouting_percentiles", conn)
        acwr_series = pd.read_sql_query(
            "SELECT player_name, team_name, date, load, acute_7d, chronic_28d, "
            "acwr, risk_zone FROM acwr_series WHERE acwr IS NOT NULL", conn)
        acwr_alerts = pd.read_sql_query("SELECT * FROM acwr_alerts", conn)
        xg_pred = pd.read_sql_query(
            "SELECT player_name, team_name, minute, shot_type, is_goal, "
            "statsbomb_xg, predicted_xg FROM xg_predictions "
            "WHERE predicted_xg IS NOT NULL", conn)

        # Resumen para el hero / home
        n_matches = pd.read_sql_query("SELECT COUNT(*) n FROM matches", conn)["n"][0]
        n_players = pd.read_sql_query("SELECT COUNT(*) n FROM players", conn)["n"][0]
        n_teams = pd.read_sql_query("SELECT COUNT(*) n FROM teams", conn)["n"][0]
    finally:
        conn.close()

    goals_in_play = int(shots["is_goal"].sum())
    summary = {
        "matches": int(n_matches),
        "teams": int(n_teams),
        "players": int(n_players),
        "shots": int(len(shots)),
        "goals": goals_in_play,
        "model": {"roc_auc": 0.802, "pearson_r": 0.885},
    }

    # Escribir todos los archivos
    _write(team_kpis, "team_kpis", out_dir)
    _write(player_kpis, "player_kpis", out_dir)
    _write(shots, "shots", out_dir)
    _write(percentiles, "scouting_percentiles", out_dir)
    _write(acwr_series, "acwr_series", out_dir)
    _write(acwr_alerts, "acwr_alerts", out_dir)
    _write(xg_pred, "xg_predictions", out_dir)

    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False), encoding="utf-8")
    print(f"  summary.json: {summary}")

    print(f"JSON exportado en: {out_dir}")
    return out_dir


def run() -> Path:
    """Punto de entrada del módulo."""
    return export_json()


if __name__ == "__main__":
    run()
