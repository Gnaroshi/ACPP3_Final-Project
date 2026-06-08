from __future__ import annotations

import os

import pandas as pd


def fetch_culture_facilities() -> pd.DataFrame:
    if not os.getenv("INCHEON_FACILITY_API_KEY"):
        return pd.DataFrame()
    # TODO: Connect museum, gallery, library, and culture facility datasets.
    return pd.DataFrame()

