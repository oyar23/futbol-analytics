"""Carga de las tablas transformadas a la base SQLite.

Crea la base ``outputs/futbol.db`` aplicando ``src/db/schema.sql`` (DDL con
claves e índices) y carga cada DataFrame en su tabla correspondiente.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

import config

SCHEMA_PATH = config.BASE_DIR / "src" / "db" / "schema.sql"

# Orden de carga respetando dependencias de claves foráneas
LOAD_ORDER = ["matches", "teams", "players", "lineups", "events", "shots"]


def _apply_schema(conn: sqlite3.Connection) -> None:
    """Aplica el DDL del esquema (recrea todas las tablas e índices)."""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)


def load_tables(tables: dict[str, pd.DataFrame],
                db_path: Path | None = None) -> Path:
    """Carga los DataFrames en la base SQLite.

    Args:
        tables: Dict ``nombre_tabla -> DataFrame`` (salida de ``transform_all``).
        db_path: Ruta de la base. Por defecto ``config.DB_PATH``.

    Returns:
        La ruta de la base creada.
    """
    db_path = db_path or config.DB_PATH
    print("=" * 60)
    print(f"ETL · LOAD — SQLite ({db_path.name})")
    print("=" * 60)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        _apply_schema(conn)
        for name in LOAD_ORDER:
            df = tables[name]
            df.to_sql(name, conn, if_exists="append", index=False)
            print(f"  Cargada tabla '{name}': {len(df):>6} filas")
        conn.commit()
    finally:
        conn.close()

    print(f"Base creada en: {db_path}")
    return db_path


def print_summary(db_path: Path | None = None) -> None:
    """Imprime un resumen de la base (partidos, eventos, tiros, jugadores)."""
    db_path = db_path or config.DB_PATH
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        n_matches = cur.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        n_teams = cur.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
        n_players = cur.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        n_events = cur.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        n_shots = cur.execute("SELECT COUNT(*) FROM shots").fetchone()[0]
        n_goals = cur.execute("SELECT COUNT(*) FROM shots WHERE is_goal=1").fetchone()[0]
    finally:
        conn.close()

    print("=" * 60)
    print("RESUMEN DE LA BASE")
    print("=" * 60)
    print(f"  Partidos : {n_matches}")
    print(f"  Equipos  : {n_teams}")
    print(f"  Jugadores: {n_players}")
    print(f"  Eventos  : {n_events}")
    print(f"  Tiros    : {n_shots}  (goles: {n_goals})")
    print("=" * 60)


if __name__ == "__main__":
    from src.etl import extract, transform
    raw = extract.extract_all()
    tbls = transform.transform_all(raw)
    load_tables(tbls)
    print_summary()
