"""Transformación de los JSON anidados de StatsBomb a tablas tabulares limpias.

Genera los DataFrames: ``matches``, ``teams``, ``players``, ``lineups``,
``events`` (genérica) y ``shots`` (derivada, con todas las features de tiro,
incluida ``statsbomb_xg`` y features geométricas del ``freeze_frame``).
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

import config

# --------------------------------------------------------------------------- #
# Helpers de geometría de tiro
# --------------------------------------------------------------------------- #


def _shot_distance(x: float, y: float) -> float:
    """Distancia euclídea desde (x, y) al centro del arco rival (120, 40)."""
    return math.hypot(config.GOAL_X - x, config.GOAL_CENTER_Y - y)


def _shot_angle(x: float, y: float) -> float:
    """Ángulo (en radianes) que abarca el arco visto desde (x, y).

    Usa la fórmula estándar de xG: ángulo entre las rectas que van desde el
    punto de tiro hasta cada palo (y=36 e y=44). A mayor ángulo, más arco
    visible y mayor probabilidad de gol.
    """
    g = config.GOAL_X
    # Vectores hacia cada palo
    v1 = (g - x, config.GOAL_POST_LEFT_Y - y)
    v2 = (g - x, config.GOAL_POST_RIGHT_Y - y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag = math.hypot(*v1) * math.hypot(*v2)
    if mag == 0:
        return 0.0
    cos_angle = max(-1.0, min(1.0, dot / mag))
    return math.acos(cos_angle)


def _point_in_triangle(p: tuple[float, float],
                       a: tuple[float, float],
                       b: tuple[float, float],
                       c: tuple[float, float]) -> bool:
    """Indica si el punto ``p`` cae dentro del triángulo (a, b, c).

    Usado para contar defensores dentro del cono de tiro hacia el arco.
    """
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    d1 = sign(p, a, b)
    d2 = sign(p, b, c)
    d3 = sign(p, c, a)
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (has_neg and has_pos)


def _freeze_frame_features(shot_x: float, shot_y: float,
                           freeze_frame: list[dict] | None) -> dict[str, Any]:
    """Calcula features a partir del ``freeze_frame`` de un tiro.

    Returns:
        Diccionario con:
        - ``n_defenders_in_cone``: defensores rivales dentro del triángulo
          (tiro → palo izq → palo der).
        - ``gk_distance``: distancia del arquero rival al punto de tiro
          (NaN si no aparece arquero en el freeze frame).
        - ``n_opponents``: total de rivales en el freeze frame.
        - ``n_teammates``: total de compañeros en el freeze frame.
    """
    cone = {
        "n_defenders_in_cone": 0,
        "gk_distance": np.nan,
        "n_opponents": 0,
        "n_teammates": 0,
    }
    if not freeze_frame:
        return cone

    post_left = (config.GOAL_X, config.GOAL_POST_LEFT_Y)
    post_right = (config.GOAL_X, config.GOAL_POST_RIGHT_Y)
    shot = (shot_x, shot_y)

    for player in freeze_frame:
        loc = player.get("location")
        if not loc or len(loc) < 2:
            continue
        px, py = loc[0], loc[1]
        is_teammate = player.get("teammate", False)
        if is_teammate:
            cone["n_teammates"] += 1
            continue
        # Rival
        cone["n_opponents"] += 1
        if _point_in_triangle((px, py), shot, post_left, post_right):
            cone["n_defenders_in_cone"] += 1
        # Arquero rival
        pos_name = (player.get("position") or {}).get("name", "")
        if pos_name == "Goalkeeper":
            cone["gk_distance"] = math.hypot(shot_x - px, shot_y - py)

    return cone


# --------------------------------------------------------------------------- #
# Transformaciones de tablas
# --------------------------------------------------------------------------- #


def transform_matches(matches: list[dict]) -> pd.DataFrame:
    """Aplana la lista de partidos a una tabla ``matches``."""
    rows = []
    for m in matches:
        rows.append({
            "match_id": m["match_id"],
            "match_date": m.get("match_date"),
            "stage": (m.get("competition_stage") or {}).get("name"),
            "match_week": m.get("match_week"),
            "home_team_id": m["home_team"]["home_team_id"],
            "home_team": m["home_team"]["home_team_name"],
            "away_team_id": m["away_team"]["away_team_id"],
            "away_team": m["away_team"]["away_team_name"],
            "home_score": m.get("home_score"),
            "away_score": m.get("away_score"),
            "stadium": (m.get("stadium") or {}).get("name"),
            "referee": (m.get("referee") or {}).get("name"),
        })
    return pd.DataFrame(rows).sort_values("match_id").reset_index(drop=True)


def transform_teams(matches: list[dict]) -> pd.DataFrame:
    """Extrae la tabla de equipos únicos a partir de los partidos."""
    teams: dict[int, str] = {}
    for m in matches:
        teams[m["home_team"]["home_team_id"]] = m["home_team"]["home_team_name"]
        teams[m["away_team"]["away_team_id"]] = m["away_team"]["away_team_name"]
    df = pd.DataFrame(
        [{"team_id": tid, "team_name": name} for tid, name in teams.items()]
    )
    return df.sort_values("team_id").reset_index(drop=True)


def transform_players(lineups: dict[int, list[dict]]) -> pd.DataFrame:
    """Extrae la tabla de jugadores únicos a partir de las alineaciones."""
    players: dict[int, dict] = {}
    for team_lineups in lineups.values():
        for team in team_lineups:
            for p in team["lineup"]:
                pid = p["player_id"]
                if pid not in players:
                    players[pid] = {
                        "player_id": pid,
                        "player_name": p["player_name"],
                        "player_nickname": p.get("player_nickname"),
                        "country": (p.get("country") or {}).get("name"),
                        "team_id": team["team_id"],
                        "team_name": team["team_name"],
                    }
    df = pd.DataFrame(list(players.values()))
    return df.sort_values("player_id").reset_index(drop=True)


def _parse_clock(value: str | None) -> float | None:
    """Convierte un reloj 'MM:SS' a minutos decimales."""
    if not value:
        return None
    try:
        mm, ss = value.split(":")
        return int(mm) + int(ss) / 60.0
    except (ValueError, AttributeError):
        return None


def transform_lineups(lineups: dict[int, list[dict]],
                      match_end_minutes: dict[int, float]) -> pd.DataFrame:
    """Aplana las alineaciones a una tabla ``lineups`` con minutos jugados.

    Los minutos jugados se derivan de los intervalos ``from``/``to`` de cada
    posición; si ``to`` es ``None`` (jugó hasta el final), se usa el minuto
    final del partido (``match_end_minutes``).

    Args:
        lineups: Dict ``match_id -> [lineup_equipo_local, lineup_visitante]``.
        match_end_minutes: Dict ``match_id -> minuto final del partido``.

    Returns:
        DataFrame con una fila por (partido, equipo, jugador).
    """
    rows = []
    for match_id, team_lineups in lineups.items():
        end_min = match_end_minutes.get(match_id, 90.0)
        for team in team_lineups:
            for p in team["lineup"]:
                positions = p.get("positions") or []
                minutes = 0.0
                is_starter = False
                main_position = None
                for pos in positions:
                    if pos.get("start_reason") == "Starting XI":
                        is_starter = True
                    if main_position is None:
                        main_position = pos.get("position")
                    start = _parse_clock(pos.get("from")) or 0.0
                    end = _parse_clock(pos.get("to"))
                    if end is None:
                        end = end_min
                    minutes += max(0.0, end - start)
                rows.append({
                    "match_id": match_id,
                    "team_id": team["team_id"],
                    "team_name": team["team_name"],
                    "player_id": p["player_id"],
                    "player_name": p["player_name"],
                    "jersey_number": p.get("jersey_number"),
                    "position": main_position,
                    "minutes_played": round(minutes, 1),
                    "is_starter": is_starter,
                    "played": len(positions) > 0,
                })
    return pd.DataFrame(rows)


def transform_events(events: dict[int, list[dict]]) -> pd.DataFrame:
    """Aplana los eventos de todos los partidos a una tabla genérica ``events``.

    Incluye campos comunes (tipo, equipo, jugador, minuto, x, y, presión...) y
    algunos flags útiles de pases (completado, asistencia de gol, pase clave).
    """
    rows = []
    for match_id, match_events in events.items():
        for e in match_events:
            location = e.get("location") or [None, None]
            x = location[0] if len(location) > 0 else None
            y = location[1] if len(location) > 1 else None
            pass_info = e.get("pass") or {}
            type_name = (e.get("type") or {}).get("name")
            rows.append({
                "event_id": e["id"],
                "match_id": match_id,
                "index": e.get("index"),
                "period": e.get("period"),
                "minute": e.get("minute"),
                "second": e.get("second"),
                "type_name": type_name,
                "team_id": (e.get("team") or {}).get("id"),
                "team_name": (e.get("team") or {}).get("name"),
                "player_id": (e.get("player") or {}).get("id"),
                "player_name": (e.get("player") or {}).get("name"),
                "position_name": (e.get("position") or {}).get("name"),
                "location_x": x,
                "location_y": y,
                "under_pressure": bool(e.get("under_pressure", False)),
                "play_pattern": (e.get("play_pattern") or {}).get("name"),
                "possession": e.get("possession"),
                "possession_team_id": (e.get("possession_team") or {}).get("id"),
                # Flags de pase
                "pass_recipient_id": (pass_info.get("recipient") or {}).get("id"),
                "pass_length": pass_info.get("length"),
                # Un pase es completo si no tiene 'outcome' (incompleto/out/etc.)
                "pass_complete": type_name == "Pass" and "outcome" not in pass_info,
                "goal_assist": bool(pass_info.get("goal_assist", False)),
                "shot_assist": bool(pass_info.get("shot_assist", False)),
            })
    return pd.DataFrame(rows)


def transform_shots(events: dict[int, list[dict]]) -> pd.DataFrame:
    """Construye la tabla ``shots`` con todas las features de tiro.

    Para cada evento de tipo ``Shot`` extrae: ubicación, ``statsbomb_xg``,
    desenlace (y si fue gol), tipo de jugada, parte del cuerpo, técnica,
    flags (``first_time``, ``under_pressure``), geometría (distancia y ángulo)
    y features derivadas del ``freeze_frame``.
    """
    rows = []
    for match_id, match_events in events.items():
        for e in match_events:
            if (e.get("type") or {}).get("name") != "Shot":
                continue
            shot = e.get("shot") or {}
            location = e.get("location") or [None, None]
            x = location[0] if len(location) > 0 else None
            y = location[1] if len(location) > 1 else None

            outcome = (shot.get("outcome") or {}).get("name")
            shot_type = (shot.get("type") or {}).get("name")  # Open Play, Penalty...
            body_part = (shot.get("body_part") or {}).get("name")

            ff = _freeze_frame_features(x, y, shot.get("freeze_frame")) \
                if x is not None and y is not None else {
                    "n_defenders_in_cone": np.nan, "gk_distance": np.nan,
                    "n_opponents": np.nan, "n_teammates": np.nan}

            rows.append({
                "event_id": e["id"],
                "match_id": match_id,
                "period": e.get("period"),
                "minute": e.get("minute"),
                "second": e.get("second"),
                "team_id": (e.get("team") or {}).get("id"),
                "team_name": (e.get("team") or {}).get("name"),
                "player_id": (e.get("player") or {}).get("id"),
                "player_name": (e.get("player") or {}).get("name"),
                "position_name": (e.get("position") or {}).get("name"),
                "location_x": x,
                "location_y": y,
                "statsbomb_xg": shot.get("statsbomb_xg"),
                "outcome": outcome,
                "is_goal": int(outcome == "Goal"),
                "shot_type": shot_type,
                "is_penalty": int(shot_type == "Penalty"),
                "is_free_kick": int(shot_type == "Free Kick"),
                "is_corner": int(shot_type == "Corner"),
                "is_open_play": int(shot_type == "Open Play"),
                "body_part": body_part,
                "is_header": int(body_part == "Head"),
                "technique": (shot.get("technique") or {}).get("name"),
                "first_time": bool(shot.get("first_time", False)),
                "under_pressure": bool(e.get("under_pressure", False)),
                "distance": _shot_distance(x, y) if x is not None else np.nan,
                "angle": _shot_angle(x, y) if x is not None else np.nan,
                "n_defenders_in_cone": ff["n_defenders_in_cone"],
                "gk_distance": ff["gk_distance"],
                "n_opponents": ff["n_opponents"],
                "n_teammates": ff["n_teammates"],
            })
    return pd.DataFrame(rows)


def compute_match_end_minutes(events: dict[int, list[dict]]) -> dict[int, float]:
    """Calcula el minuto final de cada partido (máximo minuto+segundo)."""
    end: dict[int, float] = {}
    for match_id, match_events in events.items():
        max_min = 0.0
        for e in match_events:
            m = e.get("minute") or 0
            s = e.get("second") or 0
            max_min = max(max_min, m + s / 60.0)
        end[match_id] = max_min
    return end


def transform_all(raw: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Ejecuta todas las transformaciones y devuelve los DataFrames.

    Args:
        raw: Salida de :func:`src.etl.extract.extract_all`.

    Returns:
        Dict con los DataFrames: ``matches``, ``teams``, ``players``,
        ``lineups``, ``events``, ``shots``.
    """
    print("=" * 60)
    print("ETL · TRANSFORM — aplanado a tablas")
    print("=" * 60)

    matches, events, lineups = raw["matches"], raw["events"], raw["lineups"]
    match_end = compute_match_end_minutes(events)

    tables = {
        "matches": transform_matches(matches),
        "teams": transform_teams(matches),
        "players": transform_players(lineups),
        "lineups": transform_lineups(lineups, match_end),
        "events": transform_events(events),
        "shots": transform_shots(events),
    }
    for name, df in tables.items():
        print(f"  Tabla '{name}': {len(df):>6} filas, {len(df.columns)} columnas")
    return tables


if __name__ == "__main__":
    from src.etl import extract
    raw_data = extract.extract_all()
    transform_all(raw_data)
