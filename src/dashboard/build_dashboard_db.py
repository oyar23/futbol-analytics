"""Construye una base consolidada (``outputs/dashboard.db``) para un dashboard web.

Reúne en una sola base SQLite **todos los datos recopilados y derivados** del
proyecto, ya materializados como tablas reales (no vistas) e indexadas, de modo
que una aplicación web (Streamlit, Dash, Flask, FastAPI + frontend, etc.) pueda
consultarlos directamente sin tener que recalcular nada.

Fuentes:
- Tablas base desde ``outputs/futbol.db`` (matches, teams, players, lineups,
  events, shots).
- Datasets derivados desde ``outputs/exports/`` (KPIs, percentiles de scouting,
  predicciones de xG, serie y alertas de ACWR).

Resultado: ``outputs/dashboard.db`` con tablas listas para BI / web.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

import config

# Base de datos de salida para el dashboard
DASHBOARD_DB_PATH = config.OUTPUTS_DIR / "dashboard.db"

# Tablas base que se copian desde futbol.db
BASE_TABLES = ["matches", "teams", "players", "lineups", "events", "shots"]

# Datasets derivados: archivo CSV en exports/ -> nombre de tabla en el dashboard
DERIVED_SOURCES = {
    "kpis_equipos.csv": "team_kpis",
    "kpis_jugadores.csv": "player_kpis",
    "scouting_percentiles.csv": "scouting_percentiles",
    "xg_predicciones.csv": "xg_predictions",
    "acwr_serie.csv": "acwr_series",
    "acwr_alertas.csv": "acwr_alerts",
}

# Índices a crear (tabla -> lista de columnas) para acelerar el dashboard
INDEXES = {
    "shots": ["player_id", "team_id", "match_id"],
    "events": ["match_id", "player_id", "type_name"],
    "lineups": ["player_id", "match_id"],
    "player_kpis": ["player_id", "team_name"],
    "team_kpis": ["team_id", "team_name"],
    "scouting_percentiles": ["position_group"],
    "xg_predictions": ["player_name", "team_name"],
    "acwr_series": ["player_id", "risk_zone"],
    "acwr_alerts": ["player_name", "risk_zone"],
}


def _read_base_tables(source_db: Path) -> dict[str, pd.DataFrame]:
    """Lee las tablas base desde la base principal del pipeline."""
    if not source_db.exists():
        raise FileNotFoundError(
            f"No existe {source_db}. Corré primero el pipeline: python run_pipeline.py")
    conn = sqlite3.connect(source_db)
    try:
        tables = {}
        for name in BASE_TABLES:
            tables[name] = pd.read_sql_query(f"SELECT * FROM {name}", conn)
    finally:
        conn.close()
    return tables


def _read_derived_tables(exports_dir: Path) -> dict[str, pd.DataFrame]:
    """Lee los datasets derivados exportados por los módulos de análisis."""
    tables = {}
    for filename, table_name in DERIVED_SOURCES.items():
        path = exports_dir / filename
        if path.exists():
            tables[table_name] = pd.read_csv(path)
        else:
            print(f"  [aviso] Falta {filename} (¿corriste el pipeline completo?). "
                  f"Se omite la tabla '{table_name}'.")
    return tables


def build_dashboard_db(source_db: Path | None = None,
                       exports_dir: Path | None = None,
                       dest_db: Path | None = None) -> Path:
    """Arma la base consolidada del dashboard.

    Args:
        source_db: Base principal del pipeline (``futbol.db``).
        exports_dir: Carpeta con los CSV derivados.
        dest_db: Ruta de la base de salida (``dashboard.db``).

    Returns:
        La ruta de la base creada.
    """
    source_db = source_db or config.DB_PATH
    exports_dir = exports_dir or config.EXPORTS_DIR
    dest_db = dest_db or DASHBOARD_DB_PATH

    print("=" * 60)
    print(f"BD DASHBOARD — consolidando en {dest_db.name}")
    print("=" * 60)

    base = _read_base_tables(source_db)
    derived = _read_derived_tables(exports_dir)
    all_tables = {**base, **derived}

    # Recrear la base desde cero (idempotente)
    if dest_db.exists():
        dest_db.unlink()
    conn = sqlite3.connect(dest_db)
    try:
        for name, df in all_tables.items():
            df.to_sql(name, conn, if_exists="replace", index=False)
            print(f"  Tabla '{name}': {len(df):>6} filas, {len(df.columns)} columnas")

        # Índices
        cur = conn.cursor()
        existing = set(all_tables)
        for table, cols in INDEXES.items():
            if table not in existing:
                continue
            table_cols = set(all_tables[table].columns)
            for col in cols:
                if col in table_cols:
                    cur.execute(
                        f'CREATE INDEX IF NOT EXISTS idx_{table}_{col} '
                        f'ON {table} ("{col}")')
        conn.commit()
    finally:
        conn.close()

    size_mb = dest_db.stat().st_size / (1024 * 1024)
    print(f"  Base creada: {dest_db}  ({size_mb:.1f} MB, {len(all_tables)} tablas)")
    return dest_db


def run() -> Path:
    """Punto de entrada del módulo."""
    return build_dashboard_db()


if __name__ == "__main__":
    run()
