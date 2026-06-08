from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rebootroute.config import load_config
from rebootroute.data.mock_data import save_mock_data


def main() -> None:
    cfg = load_config()
    paths = save_mock_data(cfg.raw_data_dir, cfg.random_seed)
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()

