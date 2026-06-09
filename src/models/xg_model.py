"""Modelo de goles esperados (xG) entrenado con scikit-learn.

Entrena y compara dos modelos sobre la tabla ``shots``:
- ``LogisticRegression`` (baseline interpretable).
- ``GradientBoostingClassifier`` (modelo de boosting).

Evaluación con validación cruzada estratificada (5 folds):
- **ROC-AUC** de cada modelo.
- **Correlación de Pearson** entre el xG predicho (out-of-fold) y el
  ``statsbomb_xg`` oficial.

Decisiones de modelado (documentadas en el README):
- Los **penales** se modelan aparte con un valor fijo (``config.PENALTY_XG`` ≈
  0.79), ya que su probabilidad de gol es prácticamente constante y no depende
  de la geometría del tiro. Por eso se excluyen del entrenamiento del modelo.
- Los **penales de tanda** (``period = 5``) se excluyen por completo: no son
  tiros en juego.

Salidas:
- Modelo entrenado serializado con ``joblib`` en ``outputs/exports/``.
- CSV con el xG predicho por tiro en ``outputs/exports/``.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import config

RANDOM_STATE = 42
N_SPLITS = 5

# Features usadas por el modelo (sin penales)
FEATURES = [
    "distance",        # distancia al centro del arco (120, 40)
    "angle",           # ángulo que abarca el arco (entre palos y=36/y=44)
    "dist_to_goal_line",  # distancia horizontal a la línea de gol (120 - x)
    "lateral_offset",  # cuán descentrado está el tiro (|y - 40|)
    "is_header",
    "is_free_kick",
    "is_corner",
    "under_pressure",
    "first_time",
    "n_defenders_in_cone",
    "gk_distance",
    "n_opponents",
    "n_teammates",
]
TARGET = "goal"


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega features geométricas derivadas de la ubicación del tiro.

    - ``dist_to_goal_line``: distancia horizontal a la línea de gol (120 - x).
    - ``lateral_offset``: distancia lateral al centro del arco (|y - 40|).
    """
    df = df.copy()
    df["dist_to_goal_line"] = config.PITCH_LENGTH - df["location_x"]
    df["lateral_offset"] = (df["location_y"] - config.GOAL_CENTER_Y).abs()
    return df


def load_shots(db_path: Path | None = None) -> pd.DataFrame:
    """Carga la tabla ``shots`` desde la base SQLite."""
    db_path = db_path or config.DB_PATH
    conn = sqlite3.connect(db_path)
    try:
        shots = pd.read_sql_query("SELECT * FROM shots", conn)
    finally:
        conn.close()
    return shots


def prepare_dataset(shots: pd.DataFrame) -> pd.DataFrame:
    """Prepara el dataset de modelado.

    - Excluye penales de tanda (``period == 5``) y penales normales.
    - Define el target ``goal`` (1 si fue gol).
    - Convierte flags booleanos a enteros.

    Returns:
        DataFrame de tiros en juego (sin penales), listo para entrenar.
    """
    df = shots.copy()
    # Excluir penales de tanda y penales normales (se modelan aparte)
    df = df[(df["period"] < 5) & (df["is_penalty"] == 0)].copy()
    df = add_engineered_features(df)
    df[TARGET] = df["is_goal"].astype(int)
    for col in ("under_pressure", "first_time"):
        df[col] = df[col].astype(int)
    # Quitar tiros sin ubicación (sin geometría utilizable)
    df = df.dropna(subset=["distance", "angle"]).reset_index(drop=True)
    return df


def _build_pipelines() -> dict[str, Pipeline]:
    """Construye los pipelines de los dos modelos a comparar."""
    # Imputación de NaN (p. ej. gk_distance sin arquero en el freeze frame)
    imputer = ColumnTransformer(
        [("num", SimpleImputer(strategy="median"), FEATURES)],
        remainder="drop",
    )

    logreg = Pipeline([
        ("impute", imputer),
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
    ])

    # Hiperparámetros regularizados: el dataset es chico (~1.4k tiros), así que
    # learning rate baja, árboles poco profundos y submuestreo evitan sobreajuste.
    gboost = Pipeline([
        ("impute", imputer),
        ("clf", GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=3,
            subsample=0.8,
            min_samples_leaf=20,
            random_state=RANDOM_STATE,
        )),
    ])

    return {"LogisticRegression": logreg, "GradientBoosting": gboost}


def evaluate_models(df: pd.DataFrame) -> dict[str, dict]:
    """Evalúa ambos modelos con validación cruzada estratificada.

    Returns:
        Dict ``nombre_modelo -> {roc_auc, roc_auc_std, pearson_r, oof_pred}``.
    """
    X = df[FEATURES]
    y = df[TARGET]
    sb_xg = df["statsbomb_xg"].values

    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    results: dict[str, dict] = {}

    print("=" * 60)
    print("MODELO xG — evaluación por validación cruzada (5 folds)")
    print("=" * 60)
    print(f"  Tiros en juego (sin penales): {len(df)}  |  goles: {int(y.sum())}")
    print(f"  Tasa de conversión base: {y.mean():.3f}\n")

    for name, pipe in _build_pipelines().items():
        auc_scores = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc")
        oof_pred = cross_val_predict(pipe, X, y, cv=cv, method="predict_proba")[:, 1]
        # Correlación de Pearson entre xG predicho (out-of-fold) y xG oficial
        r, _ = pearsonr(oof_pred, sb_xg)
        results[name] = {
            "roc_auc": auc_scores.mean(),
            "roc_auc_std": auc_scores.std(),
            "pearson_r": r,
            "oof_pred": oof_pred,
        }
        print(f"  {name:<20} ROC-AUC = {auc_scores.mean():.4f} "
              f"(±{auc_scores.std():.4f})  |  corr(xG, StatsBomb) = {r:.4f}")

    return results


def train_final_and_export(df: pd.DataFrame, shots_full: pd.DataFrame,
                           best_model_name: str) -> dict[str, float]:
    """Entrena el mejor modelo sobre todos los datos y exporta resultados.

    - Reentrena el modelo elegido con todo el dataset (sin penales).
    - Guarda el modelo con joblib.
    - Genera un CSV con el xG predicho por tiro: a los penales (no de tanda) se
      les asigna ``config.PENALTY_XG``; los de tanda quedan marcados aparte.

    Args:
        df: Dataset de modelado (tiros en juego sin penales).
        shots_full: Tabla completa de tiros (para el CSV de predicciones).
        best_model_name: Nombre del modelo ganador.

    Returns:
        Dict con métricas finales de referencia.
    """
    pipe = _build_pipelines()[best_model_name]
    pipe.fit(df[FEATURES], df[TARGET])

    model_path = config.EXPORTS_DIR / "xg_model.joblib"
    joblib.dump(pipe, model_path)
    print(f"\n  Modelo final ({best_model_name}) guardado en: {model_path.name}")

    # --- CSV con xG predicho por tiro ---
    out = add_engineered_features(shots_full)
    out["predicted_xg"] = np.nan

    # Penales de tanda: sin xG de modelo (se marcan)
    is_shootout = out["period"] == 5
    # Penales normales: valor fijo
    is_penalty = (out["is_penalty"] == 1) & (~is_shootout)
    out.loc[is_penalty, "predicted_xg"] = config.PENALTY_XG

    # Resto de tiros en juego con ubicación: predicción del modelo
    in_play = (~is_shootout) & (out["is_penalty"] == 0) & out["distance"].notna()
    out.loc[in_play, "predicted_xg"] = pipe.predict_proba(
        out.loc[in_play, FEATURES]
    )[:, 1]

    cols = ["event_id", "match_id", "team_name", "player_name", "minute",
            "shot_type", "is_goal", "statsbomb_xg", "predicted_xg",
            "distance", "angle"]
    csv_path = config.EXPORTS_DIR / "xg_predicciones.csv"
    out[cols].to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"  Predicciones por tiro exportadas: {csv_path.name} ({len(out)} tiros)")

    return {"penalty_xg": config.PENALTY_XG}


def run() -> dict[str, dict]:
    """Punto de entrada: entrena, evalúa y exporta el modelo de xG."""
    shots = load_shots()
    df = prepare_dataset(shots)
    results = evaluate_models(df)

    # Elegir el modelo con mejor ROC-AUC
    best = max(results, key=lambda k: results[k]["roc_auc"])
    print(f"\n  ► Mejor modelo por ROC-AUC: {best} "
          f"(AUC={results[best]['roc_auc']:.4f}, r={results[best]['pearson_r']:.4f})")

    train_final_and_export(df, shots, best)
    return results


if __name__ == "__main__":
    run()
