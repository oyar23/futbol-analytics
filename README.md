# ⚽ Fútbol Analytics

Pipeline de datos y analítica de fútbol profesional construido sobre los datos
abiertos de **StatsBomb** (Copa del Mundo 2022). El proyecto cubre el flujo
completo de un equipo de datos / BI en un club: extracción de datos crudos,
modelado en una base relacional, cálculo de KPIs, un modelo de **goles esperados
(xG)** propio, scouting por percentiles y un módulo de carga física (ACWR).

> Proyecto de portfolio orientado a roles de **Analista de Datos / BI** en el
> ámbito deportivo. Todo el código es reproducible end-to-end con un solo comando.

### 🌐 [Ver el dashboard en vivo →](https://oyar23.github.io/futbol-analytics/)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange)
![SQLite](https://img.shields.io/badge/SQLite-DB-green)
![React](https://img.shields.io/badge/React-Vite-61dafb)
![StatsBomb](https://img.shields.io/badge/data-StatsBomb%20Open-red)

**Dataset procesado (Mundial 2022):** 64 partidos · 234.637 eventos · 1.494 tiros
· 829 jugadores · 32 equipos. El pipeline completo corre en **~35 segundos** con
los datos cacheados.

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

# 3. Ejecutar el pipeline completo (idempotente; usa la caché de datos)
python run_pipeline.py

# Forzar la re-descarga de los datos de StatsBomb:
python run_pipeline.py --force
```

> La primera ejecución descarga los 128 archivos JSON de StatsBomb (eventos +
> alineaciones de 64 partidos) y los cachea en `data/raw/`. Las siguientes
> ejecuciones reutilizan esa caché.

---

## 🧩 Arquitectura del pipeline

El flujo es un pipeline lineal e idempotente orquestado por `run_pipeline.py`:

```
StatsBomb Open Data (JSON)
        │  extract.py  (descarga + caché en data/raw/)
        ▼
   transform.py  (aplana eventos → tablas; geometría y freeze frame de tiros)
        │
        ▼
   load.py + schema.sql  →  SQLite (outputs/futbol.db)
        │
        ├──► kpis.py       → KPIs equipo/jugador  → CSV + Excel (Power BI)
        ├──► xg_model.py   → modelo de xG          → joblib + CSV
        ├──► scouting.py   → percentiles + radares → CSV + PNG
        ├──► acwr.py       → carga simulada + ACWR → CSV + PNG
        │
        └──► build_dashboard_db.py
                 → consolida TODO en outputs/dashboard.db (web dashboard)
```

> **Exploración:** los notebooks de EDA en `notebooks/` analizan el dataset y el
> modelo de xG sobre la base ya construida.

Cada módulo es ejecutable por separado (`python -m src.<paquete>.<modulo>`) o todo
junto con `python run_pipeline.py`.

### Módulos

- [x] **Módulo 1** — Scaffolding + Git
- [x] **Módulo 2** — ETL multifuente (StatsBomb → SQLite)
- [x] **Módulo 3** — KPIs y dashboards
- [x] **Módulo 4** — Modelo de goles esperados (xG)
- [x] **Módulo 5** — Scouting (percentiles + radares)
- [x] **Módulo 6** — Carga física y ACWR
- [x] **Módulo 7** — Orquestación + README final

---

## 📊 Conectar Power BI / Looker Studio

Tras ejecutar el pipeline, en `outputs/exports/` quedan los datasets listos para BI:

| Archivo | Contenido |
|---------|-----------|
| `kpis_equipos.csv` | KPIs por equipo (goles, tiros, xG, % pase, posesión proxy) |
| `kpis_jugadores.csv` | KPIs por jugador (minutos, goles, asistencias, xG, xG/90) |
| `tiros.csv` | Tabla de tiros con todas las features |
| `kpis_futbol.xlsx` | Las tres tablas en un único Excel multi-hoja |

**Power BI Desktop:**
1. *Obtener datos → Texto/CSV* (o *Excel*) y elegir el archivo de `outputs/exports/`.
2. *Cargar* cada tabla. Para el Excel, seleccionar las hojas `kpis_equipos`,
   `kpis_jugadores` y `tiros` en el Navegador.
3. En la vista *Modelo*, relacionar `tiros[team_name]` con `kpis_equipos[team_name]`
   y `tiros[player_name]` con `kpis_jugadores[player_name]` si se quieren cruzar.
4. Construir visuales (ranking de goleadores, xG vs goles, mapa de tiros con
   `location_x` / `location_y`, etc.).

**Looker Studio:** *Crear → Fuente de datos → Subida de archivos (CSV)* y subir
los `.csv`. Los archivos usan codificación `utf-8-sig` para que los acentos se
vean correctamente.

> Los exports se versionan en el repositorio, así que el dashboard puede
> reproducirse sin necesidad de re-ejecutar todo el pipeline.

---

## 🤖 Modelo de goles esperados (xG)

Se entrena un modelo propio de xG sobre los **1.430 tiros en juego** del Mundial
(excluyendo penales) y se compara contra el xG oficial de StatsBomb.

**Features:** distancia y ángulo al arco, distancia a la línea de gol, descentrado
lateral, parte del cuerpo (cabeza), tipo de jugada (tiro libre / córner), presión,
remate de primera, y features del *freeze frame* (defensores en el cono de tiro,
distancia del arquero, nº de rivales y compañeros).

**Evaluación** (validación cruzada estratificada, 5 folds — valores reales):

| Modelo | ROC-AUC | Correlación de Pearson con StatsBomb xG |
|--------|:-------:|:---------------------------------------:|
| **LogisticRegression** (elegido) | **0.802** | **0.885** |
| GradientBoosting | 0.759 | 0.739 |

> El modelo logístico, además de ser el más interpretable, obtuvo el mejor
> ROC-AUC. La **correlación de 0.885** con el xG oficial de StatsBomb indica que
> reproduce muy de cerca un modelo profesional usando solo features públicas.

**Decisión sobre penales:** se modelan **aparte** con un valor fijo de
`xG = 0.79` (probabilidad de conversión histórica de un penal), ya que su
resultado no depende de la geometría del tiro. Los **penales de tanda**
(`period = 5`) se excluyen por completo: no son tiros en juego.

**Salidas:** `outputs/exports/xg_model.joblib` (modelo entrenado) y
`outputs/exports/xg_predicciones.csv` (xG predicho por tiro vs StatsBomb).

---

## 🔍 Scouting (percentiles por posición + radares)

Se calculan métricas **por 90 minutos** para cada jugador y se obtienen
**percentiles dentro de su grupo posicional** (GK / DEF / MID / FWD), sobre un
pool de **345 jugadores** con al menos 180 minutos. La función
`compare_players(player_a, player_b)` genera un radar comparativo entre dos
jugadores de la misma posición.

Métricas del radar: xG/90, tiros/90, pases clave/90, pases/90, % de pase
completado, regates/90, recuperaciones/90 y acciones defensivas/90.

| Mbappé vs Messi (FWD) | Modrić vs Bellingham (MID) |
|:---:|:---:|
| ![Radar Mbappé vs Messi](outputs/figures/radar_Kylian_Mbappé_Lottin_vs_Lionel_Andrés_Messi_Cucci.png) | ![Radar Modrić vs Bellingham](outputs/figures/radar_Luka_Modrić_vs_Jude_Bellingham.png) |

**Salida:** `outputs/exports/scouting_percentiles.csv` y los radares en
`outputs/figures/`.

---

## 🏃 Carga física y ACWR — ⚠️ módulo metodológico (datos simulados)

> **StatsBomb Open Data NO incluye datos de GPS / carga física.** Por eso este
> módulo **genera datos de carga simulados** de forma realista (a partir de los
> minutos jugados, la intensidad del partido y sesiones de entrenamiento
> sintéticas, con una rampa de pretemporada). **No son datos reales:** el objetivo
> es demostrar la **metodología** de monitoreo de carga que se aplicaría en un
> club con datos reales de GPS.

Se calcula el **ACWR** (Acute:Chronic Workload Ratio):

```
ACWR = carga aguda (media móvil 7 días) / carga crónica (media móvil 28 días)
```

Y se clasifica en zonas de riesgo, generando alertas de riesgo de lesión:

| Zona | Rango ACWR | Interpretación |
|------|:----------:|----------------|
| Subcarga | `< 0.8` | Estímulo insuficiente |
| **Óptima** | `0.8 – 1.3` | *Sweet spot* |
| Precaución | `1.3 – 1.5` | Carga elevándose |
| **Riesgo alto** | `> 1.5` | Riesgo de lesión |

**Salidas:** `outputs/exports/acwr_serie.csv` (serie diaria con ACWR y zona),
`outputs/exports/acwr_alertas.csv` (días en zona de riesgo) y un gráfico de
ejemplo en `outputs/figures/`:

![ACWR Messi](outputs/figures/acwr_Lionel_Andrés_Messi_Cucci.png)

---

## 📓 Notebooks de EDA

En `notebooks/` hay dos notebooks de análisis exploratorio (ya ejecutados, con
los gráficos embebidos), que trabajan sobre la base generada por el pipeline:

| Notebook | Contenido |
|----------|-----------|
| `01_eda_general.ipynb` | Panorama del dataset, goles por partido y fase, equipos (xG vs goles reales), goleadores, minutos y líderes de xG/90. |
| `02_eda_tiros_xg.ipynb` | Desenlaces y tipos de tiro, **mapa de tiros**, drivers de conversión (distancia / parte del cuerpo / presión), geometría y comparación de nuestro xG vs StatsBomb. |

Para abrirlos: `jupyter notebook` (o VS Code) tras correr el pipeline.

---

## 🌐 Base de datos para dashboard web

`src/dashboard/build_dashboard_db.py` consolida **todos los datos recopilados y
derivados** en una única base SQLite **`outputs/dashboard.db`**, con las tablas
ya materializadas e indexadas para que una app web las consulte sin recalcular:

| Tabla | Descripción |
|-------|-------------|
| `matches`, `teams`, `players`, `lineups`, `events`, `shots` | Datos base del torneo |
| `team_kpis`, `player_kpis` | KPIs agregados de equipo y jugador |
| `scouting_percentiles` | Percentiles por posición |
| `xg_predictions` | xG predicho por tiro (modelo propio vs StatsBomb) |
| `acwr_series`, `acwr_alerts` | Serie de carga/ACWR y alertas de riesgo |

Se genera en el último paso de `python run_pipeline.py`. Al ser una base SQLite
autocontenida, se conecta fácil desde **Streamlit, Dash, Flask/FastAPI** o
cualquier frontend. Ejemplo de consulta:

```python
import sqlite3, pandas as pd
conn = sqlite3.connect("outputs/dashboard.db")
top = pd.read_sql_query(
    "SELECT player_name, goals, xg, xg_per_90 FROM player_kpis "
    "ORDER BY goals DESC LIMIT 10", conn)
```

---

## 🖥️ Dashboard web interactivo (Streamlit)

Sobre `dashboard.db` corre un dashboard en **Streamlit + Plotly** (carpeta `app/`):

```bash
# Tras correr el pipeline (que genera outputs/dashboard.db):
streamlit run app/app.py
```

Páginas:

| Página | Qué muestra |
|--------|-------------|
| **Resumen** | Métricas del torneo, top goleadores y xG vs goles por equipo. |
| **📊 KPIs** | Rankings de equipos y jugadores con filtros (equipo, minutos mínimos, métrica). |
| **🎯 Mapa de tiros** | Scatter **interactivo**: pasás el mouse por un tiro y ves jugador, minuto, xG y desenlace. Filtros por equipo / jugador / tipo / solo goles. |
| **🔍 Scouting** | Comparador de dos jugadores por **radar de percentiles** dentro de su posición. |
| **🏃 Físico y xG** | Monitor de **ACWR** por jugador con alertas, y validación del modelo de xG vs StatsBomb. |

> El mapa de tiros usa hover de Plotly: **identificar quién ejecutó cada tiro** se
> hace pasando el cursor por el punto, sin tocar código.

---

## 🎨 Dashboard a medida en React (Qatar 2022)

Además del dashboard de Streamlit, hay un **frontend propio en React + Vite**
(carpeta `web/`) con identidad visual del Mundial Qatar 2022 (granate + dorado),
navbar con autor, hero explicativo y gráficos interactivos con **Recharts**.

Es **100 % estático**: consume archivos JSON exportados desde la base, así que se
deploya **gratis** en Vercel / Netlify / GitHub Pages (sin servidor).

```bash
# 1) Generar los JSON desde la base (paso del pipeline)
python -m src.dashboard.export_json     # → web/public/data/*.json

# 2) Levantar el frontend en desarrollo
cd web
npm install
npm run dev                              # http://localhost:5173

# 3) Build de producción (genera web/dist/ listo para deploy)
npm run build
```

Páginas: **Inicio** (hero + features + resumen), **KPIs**, **Mapa de tiros**
(hover con jugador/minuto/xG), **Scouting** (radar de percentiles) y
**Físico & xG** (ACWR + validación del modelo). El `export_json.py` está integrado
como último paso de `python run_pipeline.py`.

**Deploy (GitHub Pages):** el sitio está publicado en
[oyar23.github.io/futbol-analytics](https://oyar23.github.io/futbol-analytics/).
Para volver a publicar tras un cambio:

```bash
cd web
npm run deploy     # build + push de dist/ a la rama gh-pages
```

---

## 📁 Estructura del repositorio

```
futbol-analytics/
├── config.py                 # rutas, IDs de competición, constantes StatsBomb
├── run_pipeline.py           # orquesta ETL → DB → KPIs → modelo → scouting → físico
├── requirements.txt
├── data/                     # (ignorado por git)
│   ├── raw/                  # JSON descargados de StatsBomb (caché)
│   └── processed/            # intermedios
├── src/
│   ├── etl/
│   │   ├── extract.py        # descarga matches/events/lineups con caché y reintentos
│   │   ├── transform.py      # aplana JSON → tablas; geometría + freeze frame de tiros
│   │   └── load.py           # carga a SQLite + resumen
│   ├── db/
│   │   └── schema.sql        # DDL (tablas, claves, índices)
│   ├── kpis/
│   │   └── kpis.py           # KPIs equipo/jugador (vistas SQL) + exports BI
│   ├── models/
│   │   └── xg_model.py       # modelo de xG (LogReg vs GradientBoosting)
│   ├── scouting/
│   │   └── scouting.py       # percentiles por posición + radares
│   ├── physical/
│   │   └── acwr.py           # carga simulada + ACWR + alertas
│   └── dashboard/
│       └── build_dashboard_db.py  # consolida todo en dashboard.db
├── app/                      # dashboard web (Streamlit)
│   ├── app.py                # página de inicio / resumen
│   ├── utils.py              # conexión a la base + caché
│   ├── charts.py             # figuras Plotly (mapa de tiros, radar, ACWR…)
│   └── pages/                # KPIs, mapa de tiros, scouting, físico/xG
├── web/                      # dashboard a medida (React + Vite)
│   ├── src/
│   │   ├── components/       # Navbar, Hero, Emblem, UI, Footer
│   │   └── pages/            # Home, Kpis, ShotMap, Scouting, Physical
│   └── public/data/          # JSON exportado desde la base (versionado ✔)
├── outputs/
│   ├── futbol.db             # base del pipeline      (ignorada por git)
│   ├── dashboard.db          # base para dashboard web (ignorada por git)
│   ├── exports/              # CSV/Excel para BI  (versionados ✔)
│   └── figures/              # radares y gráficos (versionados ✔)
└── notebooks/
    ├── 01_eda_general.ipynb  # EDA: partidos, equipos, jugadores
    └── 02_eda_tiros_xg.ipynb # EDA: tiros y modelo de xG
```

---

## 🗃️ Esquema de la base de datos

| Tabla | Filas | Descripción |
|-------|------:|-------------|
| `matches` | 64 | Un registro por partido |
| `teams` | 32 | Equipos participantes |
| `players` | 829 | Jugadores |
| `lineups` | 3.244 | Participación por partido (minutos, titularidad) |
| `events` | 234.637 | Eventos (tipo, equipo, jugador, x/y, presión, flags de pase) |
| `shots` | 1.494 | Tabla derivada con todas las features de tiro y `statsbomb_xg` |

---

## ✍️ Convenciones

- Código y *docstrings* en **inglés**; comentarios y documentación en **español**.
- *Conventional Commits* (`feat`, `chore`, `docs`, …) por módulo.
- Datos crudos y base de datos **fuera de git** (`.gitignore`); los exports y
  figuras pequeñas **sí se versionan** para que el repo se vea completo.
