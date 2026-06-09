"""Orquestador end-to-end del pipeline de Fútbol Analytics.

Ejecuta todo el flujo con un solo comando, de forma idempotente
(no re-descarga datos si ya están cacheados):

    ETL → SQLite → KPIs → modelo xG → scouting → carga física → exports

Uso:
    python run_pipeline.py

Nota: los módulos se van conectando aquí a medida que se construyen.
"""


import config  # noqa: F401  (reconfigura stdout a UTF-8 en Windows)
from src.etl import extract, load, transform
from src.kpis import kpis
from src.models import xg_model


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


def main() -> None:
    """Ejecuta el pipeline completo en orden."""
    print("=" * 60)
    print("⚽  FÚTBOL ANALYTICS — PIPELINE")
    print("=" * 60)
    # 1. ETL (extract → transform → load)
    run_etl()
    # 2. KPIs + exports para BI
    run_kpis()
    # 3. Modelo de xG
    run_xg_model()
    # Próximos módulos (se irán conectando):
    # 4. Scouting
    # 5. Carga física (ACWR)
    print("\n✔ Pipeline finalizado.")


if __name__ == "__main__":
    main()
