from __future__ import annotations

import pandas as pd

from rebootroute.data.official_sources import fetch_youth_rental_resources


def fetch_culture_facilities() -> pd.DataFrame:
    """Fetch official youth-space rental/facility cards from Incheon Youth Portal."""
    return fetch_youth_rental_resources()
