"""Configuración central del proyecto Fútbol Analytics.

Contiene rutas base, identificadores de la competición y constantes del
esquema de StatsBomb usadas a lo largo de todo el pipeline.
"""
import sys
from pathlib import Path

# En Windows la consola suele usar cp1252 y rompe al imprimir caracteres UTF-8
# (emojis, acentos en algunos casos). Forzamos UTF-8 de forma segura.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

# --------------------------------------------------------------------------- #
# Rutas base del proyecto
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

OUTPUTS_DIR = BASE_DIR / "outputs"
EXPORTS_DIR = OUTPUTS_DIR / "exports"
FIGURES_DIR = OUTPUTS_DIR / "figures"

# Base de datos SQLite
DB_PATH = OUTPUTS_DIR / "futbol.db"

# Crea las carpetas necesarias si no existen (idempotente)
for _dir in (RAW_DIR, PROCESSED_DIR, EXPORTS_DIR, FIGURES_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Identificadores de la competición (StatsBomb Open Data)
# Copa del Mundo 2022 — 64 partidos
# --------------------------------------------------------------------------- #
COMPETITION_ID = 43
SEASON_ID = 106

# --------------------------------------------------------------------------- #
# URLs de StatsBomb Open Data (acceso público, sin autenticación)
# --------------------------------------------------------------------------- #
STATSBOMB_BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
COMPETITIONS_URL = f"{STATSBOMB_BASE_URL}/competitions.json"
MATCHES_URL = f"{STATSBOMB_BASE_URL}/matches/{COMPETITION_ID}/{SEASON_ID}.json"
EVENTS_URL_TEMPLATE = f"{STATSBOMB_BASE_URL}/events/{{match_id}}.json"
LINEUPS_URL_TEMPLATE = f"{STATSBOMB_BASE_URL}/lineups/{{match_id}}.json"

# --------------------------------------------------------------------------- #
# Constantes del esquema StatsBomb (geometría de la cancha)
# --------------------------------------------------------------------------- #
PITCH_LENGTH = 120.0   # eje x (0 = arco propio, 120 = arco rival)
PITCH_WIDTH = 80.0     # eje y
GOAL_X = 120.0         # línea de gol rival
GOAL_CENTER_Y = 40.0   # centro del arco
GOAL_POST_LEFT_Y = 36.0    # palo izquierdo
GOAL_POST_RIGHT_Y = 44.0   # palo derecho
GOAL_WIDTH = GOAL_POST_RIGHT_Y - GOAL_POST_LEFT_Y  # 8 yardas

# Valor fijo de xG para penales (convención habitual en la literatura).
# Documentado en el README: los penales se modelan aparte con este valor.
PENALTY_XG = 0.79

# --------------------------------------------------------------------------- #
# Parámetros de red / descarga
# --------------------------------------------------------------------------- #
REQUEST_TIMEOUT = 30      # segundos
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0       # segundos (backoff exponencial base)
