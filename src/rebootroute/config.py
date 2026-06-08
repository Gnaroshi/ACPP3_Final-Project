from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - local fallback before dependencies are installed.
    yaml = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "rebootroute"


@dataclass(frozen=True)
class AppConfig:
    project_name: str
    subtitle: str
    random_seed: int
    raw_data_dir: Path
    processed_data_dir: Path
    feature_data_dir: Path
    model_dir: Path
    reports_dir: Path
    mlruns_dir: Path
    mlflow_tracking_uri: str
    database_path: Path
    safety_resources_path: Path
    default_top_missions: int
    default_top_resources: int


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if yaml is None:
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(config_path: str | Path | None = None) -> AppConfig:
    config_file = Path(config_path) if config_path else PROJECT_ROOT / "configs" / "config.yaml"
    raw = _load_yaml(config_file)
    paths = raw.get("paths", {})
    recommendation = raw.get("recommendation", {})
    safety = raw.get("safety", {})

    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("sqlite:///"):
        database_path = Path(database_url.replace("sqlite:///", "", 1))
    else:
        database_path = Path(paths.get("database", "data/rebootroute.db"))

    def resolve(relative_path: str | Path) -> Path:
        path = Path(relative_path)
        return path if path.is_absolute() else PROJECT_ROOT / path

    default_mlflow_tracking_uri = paths.get("mlflow_tracking_uri", "sqlite:///data/mlflow.db")
    raw_mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI") or default_mlflow_tracking_uri
    if raw_mlflow_tracking_uri.startswith("file:") and not os.getenv("MLFLOW_ALLOW_FILE_STORE"):
        raw_mlflow_tracking_uri = default_mlflow_tracking_uri

    def resolve_tracking_uri(uri: str) -> str:
        if uri.startswith("sqlite:///"):
            db_path = Path(uri.replace("sqlite:///", "", 1))
            return f"sqlite:///{resolve(db_path)}"
        if uri.startswith("file:"):
            file_path = Path(uri.replace("file:", "", 1))
            return f"file:{resolve(file_path)}"
        return uri

    return AppConfig(
        project_name=raw.get("project_name", "RebootRoute"),
        subtitle=raw.get("subtitle", ""),
        random_seed=int(raw.get("random_seed", 42)),
        raw_data_dir=resolve(paths.get("raw_data", "data/raw")),
        processed_data_dir=resolve(paths.get("processed_data", "data/processed")),
        feature_data_dir=resolve(paths.get("feature_data", "data/features")),
        model_dir=resolve(paths.get("models", "models/latest")),
        reports_dir=resolve(paths.get("reports", "reports")),
        mlruns_dir=resolve(paths.get("mlruns", "mlruns")),
        mlflow_tracking_uri=resolve_tracking_uri(str(raw_mlflow_tracking_uri)),
        database_path=resolve(database_path),
        safety_resources_path=resolve(safety.get("resources_path", "configs/safety_resources.example.yaml")),
        default_top_missions=int(recommendation.get("default_top_missions", 3)),
        default_top_resources=int(recommendation.get("default_top_resources", 5)),
    )


def ensure_directories(config: AppConfig | None = None) -> None:
    cfg = config or load_config()
    for path in [
        cfg.raw_data_dir,
        cfg.processed_data_dir,
        cfg.feature_data_dir,
        cfg.model_dir,
        cfg.reports_dir,
        cfg.mlruns_dir,
        cfg.database_path.parent,
    ]:
        path.mkdir(parents=True, exist_ok=True)
    if cfg.mlflow_tracking_uri.startswith("sqlite:///"):
        Path(cfg.mlflow_tracking_uri.replace("sqlite:///", "", 1)).parent.mkdir(parents=True, exist_ok=True)
