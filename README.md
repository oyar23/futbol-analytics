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
- [x] **Módulo 2** — ETL multifuente (StatsBomb → SQLite)
- [x] **Módulo 3** — KPIs y dashboards
- [x] **Módulo 4** — Modelo de goles esperados (xG)
- [ ] **Módulo 5** — Scouting (percentiles + radares)
- [ ] **Módulo 6** — Carga física y ACWR
- [ ] **Módulo 7** — Orquestación + README final

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
