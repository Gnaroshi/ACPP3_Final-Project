from __future__ import annotations

from typing import Any

import pandas as pd

from rebootroute.recommender.resource_recommender import rank_resources


def recommend_contests(profile: Any, resources: pd.DataFrame, top_n: int = 3) -> list[dict]:
    contests = resources[resources["resource_type"].isin(["contest", "mini_project"])].copy()
    if contests.empty:
        return []
    return rank_resources(profile, contests, recommended_stage=6, top_n=top_n)

