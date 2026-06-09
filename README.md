# ⚽ Fútbol Analytics

Pipeline de datos y analítica de fútbol profesional construido sobre los datos
abiertos de **StatsBomb** (Copa del Mundo 2022). El proyecto cubre el flujo
completo de un equipo de datos / BI en un club: extracción de datos crudos,
modelado en una base relacional, cálculo de KPIs, un modelo de **goles esperados
(xG)** propio, scouting por percentiles y un módulo de carga física (ACWR).

> Proyecto de portfolio orientado a roles de **Analista de Datos / BI** en el
> ámbito deportivo. Todo el código es reproducible end-to-end con un solo comando.

---

## 🎯 Objetivos

- Construir un **ETL reproducible** desde una fuente real y pública (StatsBomb Open Data).
- Modelar los datos en **SQLite** con un esquema relacional limpio.
- Calcular **KPIs** de equipo y jugador y exportarlos listos para **Power BI / Looker Studio**.
- Entrenar un **modelo de xG** y validarlo contra el xG oficial de StatsBomb.
- Generar **informes de scouting** (percentiles por posición + radares).
- Demostrar metodología de **carga física (ACWR)** y alertas de riesgo de lesión.

---

## 🧱 Stack técnico

| Área | Herramientas |
|------|--------------|
| Lenguaje | Python 3.10+ |
| Datos | pandas, numpy |
| Machine Learning | scikit-learn |
| Visualización | matplotlib |
| Descarga | requests |
| Base de datos | SQLite (`sqlite3` / SQLAlchemy) |
| Exportaciones BI | CSV y Excel (`openpyxl`) |

**Fuente de datos:** [StatsBomb Open Data](https://github.com/statsbomb/open-data) —
Copa del Mundo 2022 (`competition_id=43`, `season_id=106`, 64 partidos).

---

## 🚀 Instalación y uso

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar el pipeline completo (idempotente)
python run_pipeline.py
```

---

## 📦 Estado del proyecto

Este README se irá completando a medida que se construyen los módulos:

- [x] **Módulo 1** — Scaffolding + Git
- [ ] **Módulo 2** — ETL multifuente (StatsBomb → SQLite)
- [ ] **Módulo 3** — KPIs y dashboards
- [ ] **Módulo 4** — Modelo de goles esperados (xG)
- [ ] **Módulo 5** — Scouting (percentiles + radares)
- [ ] **Módulo 6** — Carga física y ACWR
- [ ] **Módulo 7** — Orquestación + README final

---

## 📁 Estructura del repositorio

```
futbol-analytics/
├── config.py                 # rutas, IDs de competición, constantes
├── run_pipeline.py           # orquesta ETL → DB → KPIs → exports end-to-end
├── data/                     # JSON crudos e intermedios (ignorados por git)
├── src/
│   ├── etl/                  # extract, transform, load
│   ├── db/                   # schema.sql
│   ├── kpis/                 # KPIs en SQL
│   ├── models/               # modelo de xG
│   ├── scouting/             # percentiles + radares
│   └── physical/             # ACWR y alertas
├── outputs/
│   ├── exports/              # CSV/Excel para BI (versionados)
│   └── figures/              # gráficos (versionados)
└── notebooks/                # exploración
```
