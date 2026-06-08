from __future__ import annotations

import os

import pandas as pd


def fetch_culture_events() -> pd.DataFrame:
    if not os.getenv("INCHEON_CULTURE_API_KEY"):
        return pd.DataFrame()
    # TODO: Connect Incheon culture/art event or festival public API.
    return pd.DataFrame()

