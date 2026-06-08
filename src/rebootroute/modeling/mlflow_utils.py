from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from rebootroute.config import AppConfig, load_config

try:
    import mlflow
except Exception:  # pragma: no cover
    mlflow = None


def _write_fallback_run(
    cfg: AppConfig,
    task: str,
    model_type: str,
    metrics: dict[str, Any],
    data_version: str,
    feature_columns: list[str],
    error: str | None = None,
) -> None:
    cfg.mlruns_dir.mkdir(parents=True, exist_ok=True)
    fallback = cfg.mlruns_dir / "fallback_runs.jsonl"
    payload = {
        "task": task,
        "model_type": model_type,
        "data_version": data_version,
        "feature_columns": feature_columns,
        "metrics": metrics,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    if error:
        payload["mlflow_error"] = error
        payload["tracking_uri"] = cfg.mlflow_tracking_uri
    with fallback.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def log_model_candidate(
    task: str,
    model_type: str,
    metrics: dict[str, Any],
    data_version: str,
    feature_columns: list[str],
) -> None:
    cfg = load_config()
    if mlflow is None:
        _write_fallback_run(cfg, task, model_type, metrics, data_version, feature_columns)
        return

    try:
        mlflow.set_tracking_uri(cfg.mlflow_tracking_uri)
        mlflow.set_experiment(cfg.project_name)
        with mlflow.start_run(run_name=f"{task}_{model_type}"):
            mlflow.log_param("task", task)
            mlflow.log_param("model_type", model_type)
            mlflow.log_param("data_version", data_version)
            mlflow.log_param("feature_columns", json.dumps(feature_columns))
            for key in ["accuracy", "macro_f1", "roc_auc"]:
                value = metrics.get(key)
                if value is not None:
                    mlflow.log_metric(key, float(value))
            mlflow.log_text(json.dumps(metrics, ensure_ascii=False, indent=2), "metrics.json")
    except Exception as exc:  # pragma: no cover - depends on installed MLflow backend.
        _write_fallback_run(cfg, task, model_type, metrics, data_version, feature_columns, error=str(exc))
