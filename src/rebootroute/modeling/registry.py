from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib

from rebootroute.config import load_config


def metadata_path() -> Path:
    return load_config().model_dir / "metadata.json"


def model_path(model_name: str) -> Path:
    return load_config().model_dir / f"{model_name}.joblib"


def save_model(model: Any, model_name: str) -> Path:
    path = model_path(model_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(model_name: str) -> Any | None:
    path = model_path(model_name)
    if not path.exists():
        return None
    return joblib.load(path)


def save_metadata(metadata: dict[str, Any]) -> Path:
    path = metadata_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata.setdefault("saved_at", datetime.now(timezone.utc).isoformat())
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_metadata() -> dict[str, Any]:
    path = metadata_path()
    if not path.exists():
        return {
            "stage_model_version": "untrained",
            "mission_success_model_version": "untrained",
            "data_version": "unknown",
            "trained_at": None,
            "feature_columns": [],
            "stage_metrics": {},
            "mission_success_metrics": {},
        }
    return json.loads(path.read_text(encoding="utf-8"))

