from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from rebootroute.config import load_config
from rebootroute.features.build_features import FEATURE_COLUMNS
from rebootroute.modeling.evaluate import binary_metrics
from rebootroute.modeling.mlflow_utils import log_model_candidate
from rebootroute.modeling.registry import save_model


def _candidate_models(seed: int) -> dict[str, Any]:
    return {
        "dummy_stratified": DummyClassifier(strategy="stratified", random_state=seed),
        "logistic_regression": Pipeline(
            [
                ("scale", StandardScaler()),
                ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ]
        ),
        "random_forest": RandomForestClassifier(n_estimators=140, max_depth=7, random_state=seed, class_weight="balanced"),
        "gradient_boosting": GradientBoostingClassifier(random_state=seed),
    }


def _score(model: Any, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    if hasattr(model, "decision_function"):
        raw = model.decision_function(X)
        return 1 / (1 + np.exp(-raw))
    return None


def train_mission_success_model(training: pd.DataFrame, data_version: str) -> dict[str, Any]:
    cfg = load_config()
    X = training[FEATURE_COLUMNS]
    y = training["synthetic_mission_success"].astype(int)
    stratify = y if y.value_counts().min() >= 2 and len(y.unique()) > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=cfg.random_seed, stratify=stratify)

    best_name = ""
    best_model = None
    best_metrics: dict[str, Any] = {}
    all_metrics: dict[str, Any] = {}
    for name, model in _candidate_models(cfg.random_seed).items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        scores = _score(model, X_test)
        metrics = binary_metrics(y_test, pred, scores)
        all_metrics[name] = metrics
        log_model_candidate("mission_success", name, metrics, data_version, FEATURE_COLUMNS)
        rank_metric = metrics.get("roc_auc") if metrics.get("roc_auc") is not None else metrics["macro_f1"]
        best_rank = best_metrics.get("roc_auc") if best_metrics.get("roc_auc") is not None else best_metrics.get("macro_f1", -np.inf)
        if best_model is None or rank_metric > best_rank:
            best_name = name
            best_model = model
            best_metrics = metrics

    model_path = save_model(best_model, "mission_success_model")
    return {
        "model_name": best_name,
        "model_path": str(model_path),
        "metrics": best_metrics,
        "all_candidate_metrics": all_metrics,
    }
