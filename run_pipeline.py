"""Orquestador end-to-end del pipeline de Fútbol Analytics.

Ejecuta todo el flujo con un solo comando, de forma idempotente
(no re-descarga datos si ya están cacheados):

    ETL → SQLite → KPIs → modelo xG → scouting → carga física → exports

Uso:
    python run_pipeline.py

Nota: los módulos se van conectando aquí a medida que se construyen.
"""


import config  # noqa: F401  (reconfigura stdout a UTF-8 en Windows)


def main() -> None:
    """Ejecuta el pipeline completo en orden."""
    print("=" * 60)
    print("⚽  FÚTBOL ANALYTICS — PIPELINE")
    print("=" * 60)
    # Los pasos se irán agregando módulo a módulo:
    # 1. ETL (extract → transform → load)
    # 2. KPIs
    # 3. Modelo de xG
    # 4. Scouting
    # 5. Carga física (ACWR)
    print("Scaffolding inicial listo. Ejecutá los módulos a medida que se agregan.")


if __name__ == "__main__":
    main()
