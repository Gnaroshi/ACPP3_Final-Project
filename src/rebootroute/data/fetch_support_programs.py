from __future__ import annotations

import os

import pandas as pd


def fetch_support_programs() -> pd.DataFrame:
    if not os.getenv("INCHEON_SUPPORT_API_KEY"):
        return pd.DataFrame()
    # TODO: Connect isolated-youth, one-person-household, and social relationship support data.
    return pd.DataFrame()

