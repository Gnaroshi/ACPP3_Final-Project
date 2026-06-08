from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


HUMAN_LABELS = {
    "outside_burden_score": "outside_burden high",
    "social_burden_score": "social_burden high",
    "energy_score": "energy_level low",
    "daily_rhythm_score": "daily_rhythm_level low",
    "employment_burden_score": "employment_burden high",
    "future_anxiety_score": "future_anxiety high",
    "preferred_contact_encoded": "preferred online/low-contact mode",
    "recent_success_rate": "recent mission success history",
    "recent_too_hard_rate": "recent too-hard feedback",
}


def _unwrap_model(model: Any) -> Any:
    if hasattr(model, "named_steps"):
        return list(model.named_steps.values())[-1]
    return model


def top_model_factors(model: Any, x_row: pd.DataFrame, feature_columns: list[str], top_n: int = 5) -> list[str]:
    if model is None or x_row.empty:
        return []
    estimator = _unwrap_model(model)
    values = x_row.iloc[0][feature_columns].astype(float).to_numpy()
    weights = None
    if hasattr(estimator, "feature_importances_"):
        weights = np.asarray(estimator.feature_importances_, dtype=float)
    elif hasattr(estimator, "coef_"):
        coef = np.asarray(estimator.coef_, dtype=float)
        weights = np.abs(coef).mean(axis=0) if coef.ndim > 1 else np.abs(coef)

    if weights is None or len(weights) != len(feature_columns):
        ranking = np.argsort(np.abs(values))[::-1]
    else:
        ranking = np.argsort(np.abs(weights * values))[::-1]

    factors: list[str] = []
    for idx in ranking[:top_n]:
        name = feature_columns[idx]
        value = values[idx]
        if name in {"energy_score", "daily_rhythm_score"} and value < 0.5:
            factors.append(HUMAN_LABELS[name])
        elif name.startswith("completed_stage_") and value > 0:
            factors.append(f"completed Stage {name.split('_')[-1]} missions")
        elif name.startswith("interest_") and value > 0:
            factors.append(f"interest in {name.replace('interest_', '')}")
        else:
            factors.append(HUMAN_LABELS.get(name, name))
    return list(dict.fromkeys(factors))

