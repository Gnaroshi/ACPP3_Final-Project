from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rebootroute.config import load_config
from rebootroute.database import init_db


def main() -> None:
    cfg = load_config()
    init_db(cfg.database_path)
    print(f"initialized sqlite database: {cfg.database_path}")


if __name__ == "__main__":
    main()

