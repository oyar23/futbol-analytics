"""Orquestador end-to-end del pipeline de Fútbol Analytics.

Ejecuta todo el flujo con un solo comando, de forma idempotente
(no re-descarga los datos crudos si ya están cacheados en ``data/raw/``):

    ETL → SQLite → KPIs → modelo xG → scouting → carga física → BD dashboard

Uso:
    python run_pipeline.py            # ejecuta todo (usa caché de datos)
    python run_pipeline.py --force    # fuerza la re-descarga de StatsBomb
"""
from __future__ import annotations

import argparse
import time

import config
from src.dashboard import build_dashboard_db, export_json
from src.etl import extract, load, transform
from src.kpis import kpis
from src.models import xg_model
from src.physical import acwr
from src.scouting import scouting


def run_etl(*, force: bool = False) -> None:
    """Paso 1: ETL completo (extract → transform → load → resumen)."""
    raw = extract.extract_all(force=force)
    tables = transform.transform_all(raw)
    load.load_tables(tables)
    load.print_summary()


def run_kpis() -> None:
    """Paso 2: KPIs de equipo/jugador + exports para BI."""
    kpis.run()


def run_xg_model() -> None:
    """Paso 3: entrena y evalúa el modelo de xG."""
    xg_model.run()


def run_scouting() -> None:
    """Paso 4: percentiles por posición + radares comparativos."""
    scouting.run()


def run_physical() -> None:
    """Paso 5: carga física simulada + ACWR + alertas de riesgo."""
    acwr.run()


def run_dashboard_db() -> None:
    """Paso 6: consolida todo en una base lista para un dashboard web."""
    build_dashboard_db.run()


def run_export_json() -> None:
    """Paso 7: exporta los datos a JSON para el frontend React (web/)."""
    export_json.run()


def _print_outputs() -> None:
    """Lista los archivos generados en outputs/ al finalizar."""
    print("\n" + "=" * 60)
    print("ARCHIVOS GENERADOS")
    print("=" * 60)
    print(f"  Base pipeline : {config.DB_PATH.relative_to(config.BASE_DIR)}")
    dash_db = config.OUTPUTS_DIR / "dashboard.db"
    if dash_db.exists():
        print(f"  Base dashboard: {dash_db.relative_to(config.BASE_DIR)}")
    for sub in ("exports", "figures"):
        folder = config.OUTPUTS_DIR / sub
        files = sorted(p.name for p in folder.glob("*") if p.name != ".gitkeep")
        print(f"  outputs/{sub}/ ({len(files)} archivos):")
        for name in files:
            print(f"      - {name}")


def main(force: bool = False) -> None:
    """Ejecuta el pipeline completo en orden, midiendo el tiempo de cada paso.

    Args:
        force: Si ``True``, fuerza la re-descarga de los datos de StatsBomb.
    """
    print("=" * 60)
    print("⚽  FÚTBOL ANALYTICS — PIPELINE END-TO-END")
    print("=" * 60)

    steps = [
        ("ETL (extract → transform → load)", lambda: run_etl(force=force)),
        ("KPIs + exports BI", run_kpis),
        ("Modelo de xG", run_xg_model),
        ("Scouting (percentiles + radares)", run_scouting),
        ("Carga física simulada (ACWR)", run_physical),
        ("BD consolidada para dashboard web", run_dashboard_db),
        ("Export JSON para frontend React", run_export_json),
    ]

    t0 = time.perf_counter()
    timings: list[tuple[str, float]] = []
    for i, (name, fn) in enumerate(steps, start=1):
        print(f"\n>>> Paso {i}/{len(steps)}: {name}")
        start = time.perf_counter()
        fn()
        timings.append((name, time.perf_counter() - start))

    _print_outputs()

    print("\n" + "=" * 60)
    print("TIEMPOS POR PASO")
    print("=" * 60)
    for name, secs in timings:
        print(f"  {name:<40} {secs:6.1f}s")
    print(f"  {'TOTAL':<40} {time.perf_counter() - t0:6.1f}s")
    print("\n✔ Pipeline finalizado correctamente.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de Fútbol Analytics")
    parser.add_argument("--force", action="store_true",
                        help="Fuerza la re-descarga de los datos de StatsBomb")
    args = parser.parse_args()
    main(force=args.force)
