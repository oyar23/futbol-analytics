-- Esquema relacional de la base SQLite de Fútbol Analytics.
-- Se recrea desde cero en cada carga (idempotente).

DROP TABLE IF EXISTS shots;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS lineups;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS matches;

-- --------------------------------------------------------------------------
-- matches: un registro por partido
-- --------------------------------------------------------------------------
CREATE TABLE matches (
    match_id     INTEGER PRIMARY KEY,
    match_date   TEXT,
    stage        TEXT,
    match_week   INTEGER,
    home_team_id INTEGER,
    home_team    TEXT,
    away_team_id INTEGER,
    away_team    TEXT,
    home_score   INTEGER,
    away_score   INTEGER,
    stadium      TEXT,
    referee      TEXT
);

-- --------------------------------------------------------------------------
-- teams: equipos participantes
-- --------------------------------------------------------------------------
CREATE TABLE teams (
    team_id   INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL
);

-- --------------------------------------------------------------------------
-- players: jugadores
-- --------------------------------------------------------------------------
CREATE TABLE players (
    player_id       INTEGER PRIMARY KEY,
    player_name     TEXT NOT NULL,
    player_nickname TEXT,
    country         TEXT,
    team_id         INTEGER,
    team_name       TEXT,
    FOREIGN KEY (team_id) REFERENCES teams (team_id)
);

-- --------------------------------------------------------------------------
-- lineups: participación de cada jugador por partido (minutos jugados)
-- --------------------------------------------------------------------------
CREATE TABLE lineups (
    match_id       INTEGER,
    team_id        INTEGER,
    team_name      TEXT,
    player_id      INTEGER,
    player_name    TEXT,
    jersey_number  INTEGER,
    position       TEXT,
    minutes_played REAL,
    is_starter     INTEGER,
    played         INTEGER,
    FOREIGN KEY (match_id)  REFERENCES matches (match_id),
    FOREIGN KEY (team_id)   REFERENCES teams (team_id),
    FOREIGN KEY (player_id) REFERENCES players (player_id)
);

-- --------------------------------------------------------------------------
-- events: tabla genérica de eventos
-- --------------------------------------------------------------------------
CREATE TABLE events (
    event_id           TEXT PRIMARY KEY,
    match_id           INTEGER,
    "index"            INTEGER,
    period             INTEGER,
    minute             INTEGER,
    second             INTEGER,
    type_name          TEXT,
    team_id            INTEGER,
    team_name          TEXT,
    player_id          INTEGER,
    player_name        TEXT,
    position_name      TEXT,
    location_x         REAL,
    location_y         REAL,
    under_pressure     INTEGER,
    play_pattern       TEXT,
    possession         INTEGER,
    possession_team_id INTEGER,
    pass_recipient_id  INTEGER,
    pass_length        REAL,
    pass_complete      INTEGER,
    goal_assist        INTEGER,
    shot_assist        INTEGER,
    FOREIGN KEY (match_id)  REFERENCES matches (match_id),
    FOREIGN KEY (team_id)   REFERENCES teams (team_id),
    FOREIGN KEY (player_id) REFERENCES players (player_id)
);

-- --------------------------------------------------------------------------
-- shots: tabla derivada con todas las features de tiro (base del modelo xG)
-- --------------------------------------------------------------------------
CREATE TABLE shots (
    event_id            TEXT PRIMARY KEY,
    match_id            INTEGER,
    period              INTEGER,
    minute              INTEGER,
    second              INTEGER,
    team_id             INTEGER,
    team_name           TEXT,
    player_id           INTEGER,
    player_name         TEXT,
    position_name       TEXT,
    location_x          REAL,
    location_y          REAL,
    statsbomb_xg        REAL,
    outcome             TEXT,
    is_goal             INTEGER,
    shot_type           TEXT,
    is_penalty          INTEGER,
    is_free_kick        INTEGER,
    is_corner           INTEGER,
    is_open_play        INTEGER,
    body_part           TEXT,
    is_header           INTEGER,
    technique           TEXT,
    first_time          INTEGER,
    under_pressure      INTEGER,
    distance            REAL,
    angle               REAL,
    n_defenders_in_cone REAL,
    gk_distance         REAL,
    n_opponents         REAL,
    n_teammates         REAL,
    FOREIGN KEY (match_id)  REFERENCES matches (match_id),
    FOREIGN KEY (team_id)   REFERENCES teams (team_id),
    FOREIGN KEY (player_id) REFERENCES players (player_id)
);

-- --------------------------------------------------------------------------
-- Índices para acelerar joins y agregaciones de KPIs
-- --------------------------------------------------------------------------
CREATE INDEX idx_events_match   ON events (match_id);
CREATE INDEX idx_events_player  ON events (player_id);
CREATE INDEX idx_events_team    ON events (team_id);
CREATE INDEX idx_events_type    ON events (type_name);
CREATE INDEX idx_shots_player   ON shots (player_id);
CREATE INDEX idx_shots_team     ON shots (team_id);
CREATE INDEX idx_lineups_player ON lineups (player_id);
CREATE INDEX idx_lineups_match  ON lineups (match_id);
