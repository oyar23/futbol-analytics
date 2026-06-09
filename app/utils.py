"""Utilidades del dashboard: localización de la base y consultas cacheadas.

El dashboard lee de ``outputs/dashboard.db`` (generada por
``python run_pipeline.py``). Las consultas se cachean con Streamlit para que la
app sea fluida.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


def find_db() -> Path:
    """Busca ``outputs/dashboard.db`` subiendo desde la ubicación de este archivo."""
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "outputs" / "dashboard.db"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "No se encontró outputs/dashboard.db. Generá la base con:\n"
        "    python run_pipeline.py")


DB_PATH = find_db()


def _query(sql: str, params: tuple | None = None) -> pd.DataFrame:
    """Ejecuta una consulta y devuelve un DataFrame (sin caché)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


@st.cache_data(ttl=3600, show_spinner=False)
def query(sql: str, params: tuple | None = None) -> pd.DataFrame:
    """Versión cacheada de :func:`_query`."""
    return _query(sql, params)


@st.cache_data(ttl=3600, show_spinner=False)
def load_table(name: str) -> pd.DataFrame:
    """Carga una tabla completa de la base (cacheada)."""
    return _query(f"SELECT * FROM {name}")
