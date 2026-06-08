from __future__ import annotations

import pandas as pd

from rebootroute.data.official_sources import fetch_ifac_event_resources


def fetch_culture_events() -> pd.DataFrame:
    """Fetch current culture events from Incheon Foundation for Arts and Culture."""
    return fetch_ifac_event_resources()
