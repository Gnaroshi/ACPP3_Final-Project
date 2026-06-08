from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from rebootroute.config import ensure_directories, load_config
from rebootroute.data.mock_data import save_mock_data
from rebootroute.data.validation import validate_all
from rebootroute.database import init_db
from rebootroute.features.build_features import build_feature_tables
from scripts.train_models import train_all


def main() -> None:
    cfg = load_config()
    ensure_directories(cfg)
    print("1/7 generating sample profiles and official resource seed data")
    paths = save_mock_data(cfg.raw_data_dir, cfg.random_seed)
    print({name: str(path) for name, path in paths.items()})

    print("2/7 validating data")
    validation = validate_all()
    print(validation)

    print("3/7 building features")
    features = build_feature_tables()
    print({k: str(v) for k, v in features.items() if k != "feature_columns"})

    print("4/7 training models and tracking candidates")
    metadata = train_all()

    print("5/7 initializing sqlite database")
    init_db(cfg.database_path)

    print("6/7 writing reports")
    report_paths = {
        "data_card": str(cfg.reports_dir / "data_card.md"),
        "model_card": str(cfg.reports_dir / "model_card.md"),
        "error_analysis": str(cfg.reports_dir / "error_analysis.md"),
        "metadata": str(cfg.model_dir / "metadata.json"),
    }

    print("7/7 pipeline complete")
    print(json.dumps({"validation": validation, "metadata": metadata, "reports": report_paths}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
