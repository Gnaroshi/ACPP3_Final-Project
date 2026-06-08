from __future__ import annotations

import pandas as pd

from rebootroute.data.official_sources import fetch_youth_policy_resources


def fetch_support_programs() -> pd.DataFrame:
    """Fetch currently open youth policy/support rows from Incheon Youth Portal."""
    return fetch_youth_policy_resources()
