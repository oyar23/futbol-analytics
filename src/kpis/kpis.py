"""KPIs de equipo y jugador calculados con SQL sobre la base SQLite.

Crea vistas SQL reutilizables (``v_team_kpis``, ``v_player_kpis``) y exporta
los datasets resultantes a ``outputs/exports/`` en CSV y en un único Excel
multi-hoja, listos para conectar desde Power BI / Looker Studio.

Notas metodológicas:
- Las KPIs de tiro/gol excluyen los penales de tanda (``period = 5``) para que
  reflejen el juego real; los goles de tanda no cuentan como goles de partido.
- "Tiros al arco" = desenlaces Goal, Saved o Saved to Post.
- "Posesión (proxy)" = % de pases del equipo sobre el total de pases jugados en
  los partidos que disputó (aproximación habitual cuando no hay tracking).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

import config

# --------------------------------------------------------------------------- #
# Definiciones SQL de las vistas
# --------------------------------------------------------------------------- #

# Tiros al arco (on target)
ON_TARGET = "('Goal', 'Saved', 'Saved to Post')"

TEAM_KPIS_VIEW = f"""
DROP VIEW IF EXISTS v_team_kpis;
CREATE VIEW v_team_kpis AS
WITH shooting AS (
    SELECT
        team_id,
        team_name,
        COUNT(*)                                              AS shots,
        SUM(is_goal)                                          AS goals,
        SUM(CASE WHEN outcome IN {ON_TARGET} THEN 1 ELSE 0 END) AS shots_on_target,
        ROUND(SUM(statsbomb_xg), 2)                           AS xg
    FROM shots
    WHERE period < 5                       -- excluye penales de tanda
    GROUP BY team_id, team_name
),
passing AS (
    SELECT
        team_id,
        COUNT(*)                                              AS passes,
        SUM(pass_complete)                                    AS passes_completed
    FROM events
    WHERE type_name = 'Pass'
    GROUP BY team_id
)
SELECT
    s.team_id,
    s.team_name,
    s.goals,
    s.shots,
    s.shots_on_target,
    s.xg,
    p.passes,
    p.passes_completed,
    ROUND(100.0 * p.passes_completed / NULLIF(p.passes, 0), 1) AS pass_completion_pct
FROM shooting s
LEFT JOIN passing p ON s.team_id = p.team_id
ORDER BY s.goals DESC, s.xg DESC;
"""

PLAYER_KPIS_VIEW = """
DROP VIEW IF EXISTS v_player_kpis;
CREATE VIEW v_player_kpis AS
WITH minutes AS (
    SELECT player_id, player_name, team_name,
           ROUND(SUM(minutes_played), 0) AS minutes
    FROM lineups
    GROUP BY player_id, player_name, team_name
),
shooting AS (
    SELECT player_id,
           COUNT(*)                    AS shots,
           SUM(is_goal)                AS goals,
           ROUND(SUM(statsbomb_xg), 2) AS xg
    FROM shots
    WHERE period < 5
    GROUP BY player_id
),
passing AS (
    SELECT player_id,
           SUM(goal_assist) AS assists,
           SUM(shot_assist) AS key_passes
    FROM events
    WHERE type_name = 'Pass'
    GROUP BY player_id
)
SELECT
    m.player_id,
    m.player_name,
    m.team_name,
    m.minutes,
    COALESCE(sh.goals, 0)       AS goals,
    COALESCE(pa.assists, 0)     AS assists,
    COALESCE(pa.key_passes, 0)  AS key_passes,
    COALESCE(sh.shots, 0)       AS shots,
    COALESCE(sh.xg, 0)          AS xg,
    ROUND(COALESCE(sh.xg, 0) * 90.0 / NULLIF(m.minutes, 0), 2) AS xg_per_90
FROM minutes m
LEFT JOIN shooting sh ON m.player_id = sh.player_id
LEFT JOIN passing pa  ON m.player_id = pa.player_id
WHERE m.minutes > 0
ORDER BY goals DESC, xg DESC;
"""


def _possession_proxy(conn: sqlite3.Connection) -> pd.DataFrame:
    """Calcula la posesión proxy (% de pases del equipo en sus partidos)."""
    query = """
    WITH team_passes AS (
        SELECT match_id, team_id, COUNT(*) AS passes
        FROM events WHERE type_name = 'Pass'
        GROUP BY match_id, team_id
    ),
    match_totals AS (
        SELECT match_id, SUM(passes) AS total_passes
        FROM team_passes GROUP BY match_id
    )
    SELECT tp.team_id,
           ROUND(100.0 * SUM(tp.passes) / SUM(mt.total_passes), 1) AS possession_pct
    FROM team_passes tp
    JOIN match_totals mt ON tp.match_id = mt.match_id
    GROUP BY tp.team_id;
    """
    return pd.read_sql_query(query, conn)


def build_views(conn: sqlite3.Connection) -> None:
    """Crea/recrea las vistas SQL de KPIs en la base."""
    conn.executescript(TEAM_KPIS_VIEW)
    conn.executescript(PLAYER_KPIS_VIEW)
    conn.commit()


def compute_kpis(db_path: Path | None = None) -> dict[str, pd.DataFrame]:
    """Construye las vistas y devuelve los DataFrames de KPIs y tiros.

    Returns:
        Dict con ``kpis_equipos``, ``kpis_jugadores`` y ``tiros``.
    """
    db_path = db_path or config.DB_PATH
    print("=" * 60)
    print("KPIs — equipo / jugador (SQL)")
    print("=" * 60)

    conn = sqlite3.connect(db_path)
    try:
        build_views(conn)

        team_kpis = pd.read_sql_query("SELECT * FROM v_team_kpis", conn)
        possession = _possession_proxy(conn)
        team_kpis = team_kpis.merge(possession, on="team_id", how="left")

        player_kpis = pd.read_sql_query("SELECT * FROM v_player_kpis", conn)
        shots = pd.read_sql_query("SELECT * FROM shots", conn)
    finally:
        conn.close()

    print(f"  KPIs equipos  : {len(team_kpis)} filas")
    print(f"  KPIs jugadores: {len(player_kpis)} filas")
    print(f"  Tiros         : {len(shots)} filas")
    return {
        "kpis_equipos": team_kpis,
        "kpis_jugadores": player_kpis,
        "tiros": shots,
    }


def export_kpis(datasets: dict[str, pd.DataFrame],
                exports_dir: Path | None = None) -> None:
    """Exporta los datasets a CSV y a un Excel multi-hoja para Power BI.

    Args:
        datasets: Dict ``nombre -> DataFrame``.
        exports_dir: Carpeta de salida. Por defecto ``config.EXPORTS_DIR``.
    """
    exports_dir = exports_dir or config.EXPORTS_DIR
    exports_dir.mkdir(parents=True, exist_ok=True)

    # CSV individuales
    for name, df in datasets.items():
        path = exports_dir / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  CSV exportado: {path.name}")

    # Excel multi-hoja
    xlsx_path = exports_dir / "kpis_futbol.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        for name, df in datasets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    print(f"  Excel exportado: {xlsx_path.name} (hojas: {', '.join(datasets)})")


def run() -> dict[str, pd.DataFrame]:
    """Punto de entrada del módulo: calcula y exporta los KPIs."""
    datasets = compute_kpis()
    export_kpis(datasets)
    return datasets


if __name__ == "__main__":
    run()
