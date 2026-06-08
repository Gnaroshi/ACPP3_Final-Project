from __future__ import annotations

import os

import pandas as pd


def fetch_youth_programs() -> pd.DataFrame:
    """Future adapter for Incheon youth policy/program APIs.

    The MVP intentionally returns an empty frame when no API key is configured,
    so local demos never depend on external services.
    """
    if not os.getenv("INCHEON_YOUTH_API_KEY"):
        return pd.DataFrame()
    # TODO: Connect official Incheon youth program public-data endpoint.
    return pd.DataFrame()

