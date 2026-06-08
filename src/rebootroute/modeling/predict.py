from __future__ import annotations

from typing import Any

import pandas as pd

from rebootroute.features.build_features import FEATURE_COLUMNS, profile_to_feature_frame
from rebootroute.modeling.explain import top_model_factors
from rebootroute.modeling.registry import load_metadata, load_model


def predict_stage_ml(profile: dict[str, Any], progress: pd.DataFrame | None = None, missions: pd.DataFrame | None = None) -> dict[str, Any]:
    model = load_model("stage_model")
    metadata = load_metadata()
    x_row = profile_to_feature_frame(profile, progress=progress, missions=missions)
    if model is None:
        return {
            "predicted_stage": None,
            "probabilities": {},
            "contributing_factors": [],
            "model_info": metadata,
        }
    pred = int(model.predict(x_row)[0])
    probabilities: dict[str, float] = {}
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x_row)[0]
        classes = getattr(model, "classes_", list(range(len(proba))))
        probabilities = {str(int(cls)): float(prob) for cls, prob in zip(classes, proba)}
    return {
        "predicted_stage": pred,
        "probabilities": probabilities,
        "contributing_factors": top_model_factors(model, x_row, FEATURE_COLUMNS),
        "model_info": metadata,
    }

