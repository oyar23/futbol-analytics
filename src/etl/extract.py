"""Extracción de datos crudos de StatsBomb Open Data.

Descarga la lista de partidos de la Copa del Mundo 2022 y, para cada partido,
sus eventos y alineaciones. Todo se cachea en ``data/raw/`` para no volver a
descargar lo que ya existe (pipeline idempotente). Incluye reintentos con
backoff exponencial y manejo de errores.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

import config


def _download_json(url: str, dest: Path, *, force: bool = False) -> Any:
    """Descarga un JSON desde ``url`` y lo cachea en ``dest``.

    Si el archivo ya existe en disco y ``force`` es ``False``, lo lee de la
    caché en lugar de volver a descargarlo. Reintenta ante errores de red
    con backoff exponencial.

    Args:
        url: URL del recurso JSON.
        dest: Ruta local donde cachear el archivo.
        force: Si ``True``, fuerza la re-descarga aunque exista la caché.

    Returns:
        El contenido del JSON ya parseado (dict o list).

    Raises:
        requests.RequestException: Si fallan todos los reintentos.
    """
    if dest.exists() and not force:
        with dest.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    last_error: Exception | None = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False)
            return data
        except requests.RequestException as exc:  # red, timeout, HTTP error
            last_error = exc
            if attempt < config.MAX_RETRIES:
                wait = config.RETRY_BACKOFF * (2 ** (attempt - 1))
                print(f"  [retry {attempt}/{config.MAX_RETRIES}] {url} falló: {exc}. "
                      f"Reintentando en {wait:.0f}s...")
                time.sleep(wait)

    raise requests.RequestException(
        f"No se pudo descargar {url} tras {config.MAX_RETRIES} intentos: {last_error}"
    )


def fetch_matches(*, force: bool = False) -> list[dict]:
    """Descarga la lista de partidos del Mundial 2022.

    Args:
        force: Si ``True``, ignora la caché y vuelve a descargar.

    Returns:
        Lista de diccionarios, uno por partido.
    """
    dest = config.RAW_DIR / "matches" / f"{config.COMPETITION_ID}_{config.SEASON_ID}.json"
    matches = _download_json(config.MATCHES_URL, dest, force=force)
    print(f"Partidos descargados: {len(matches)}")
    return matches


def fetch_events(match_id: int, *, force: bool = False) -> list[dict]:
    """Descarga los eventos de un partido.

    Args:
        match_id: Identificador del partido en StatsBomb.
        force: Si ``True``, ignora la caché.

    Returns:
        Lista de eventos del partido.
    """
    url = config.EVENTS_URL_TEMPLATE.format(match_id=match_id)
    dest = config.RAW_DIR / "events" / f"{match_id}.json"
    return _download_json(url, dest, force=force)


def fetch_lineups(match_id: int, *, force: bool = False) -> list[dict]:
    """Descarga las alineaciones de un partido.

    Args:
        match_id: Identificador del partido en StatsBomb.
        force: Si ``True``, ignora la caché.

    Returns:
        Lista con las alineaciones de ambos equipos.
    """
    url = config.LINEUPS_URL_TEMPLATE.format(match_id=match_id)
    dest = config.RAW_DIR / "lineups" / f"{match_id}.json"
    return _download_json(url, dest, force=force)


def extract_all(*, force: bool = False) -> dict[str, Any]:
    """Descarga matches + (events, lineups) de todos los partidos.

    Args:
        force: Si ``True``, ignora la caché y re-descarga todo.

    Returns:
        Diccionario con claves ``matches`` (lista) y ``events`` / ``lineups``
        (dicts indexados por ``match_id``).
    """
    print("=" * 60)
    print("ETL · EXTRACT — StatsBomb Open Data (Mundial 2022)")
    print("=" * 60)

    matches = fetch_matches(force=force)
    match_ids = [m["match_id"] for m in matches]

    events: dict[int, list[dict]] = {}
    lineups: dict[int, list[dict]] = {}

    for i, match_id in enumerate(match_ids, start=1):
        events[match_id] = fetch_events(match_id, force=force)
        lineups[match_id] = fetch_lineups(match_id, force=force)
        if i % 10 == 0 or i == len(match_ids):
            print(f"  Descargados {i}/{len(match_ids)} partidos (events + lineups)")

    total_events = sum(len(ev) for ev in events.values())
    print(f"Extract completo: {len(matches)} partidos, {total_events} eventos crudos.")

    return {"matches": matches, "events": events, "lineups": lineups}


if __name__ == "__main__":
    extract_all()
