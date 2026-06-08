from __future__ import annotations

import os

import pandas as pd


def fetch_contests() -> pd.DataFrame:
    if not os.getenv("INCHEON_CONTEST_API_KEY"):
        return pd.DataFrame()
    # TODO: Connect public contest, local activity, and work-experience opportunity APIs.
    return pd.DataFrame()

