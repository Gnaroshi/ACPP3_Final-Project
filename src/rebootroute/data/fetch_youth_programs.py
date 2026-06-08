from __future__ import annotations

import pandas as pd

from rebootroute.data.official_sources import fetch_youth_program_resources


def fetch_youth_programs() -> pd.DataFrame:
    """Fetch current public youth program cards from Incheon Youth Portal."""
    return fetch_youth_program_resources()
