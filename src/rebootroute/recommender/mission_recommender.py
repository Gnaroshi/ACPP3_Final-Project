from __future__ import annotations

from typing import Any

import pandas as pd

from rebootroute.data.validation import parse_list


def _profile_dict(profile: Any) -> dict[str, Any]:
    if hasattr(profile, "model_dump"):
        return profile.model_dump(mode="json")
    if hasattr(profile, "dict"):
        return profile.dict()
    return dict(profile)


def _fit_overlap(a: list[str], b: list[str]) -> float:
    if not a or not b:
        return 0.0
    return len(set(a) & set(b)) / max(len(set(a)), 1)


def _burden_fit(profile: dict[str, Any], burden: int) -> float:
    energy_capacity = (int(profile["energy_level"]) + int(profile["daily_rhythm_level"])) / 2
    burden_pressure = (int(profile["outside_burden"]) + int(profile["social_burden"])) / 2
    capacity = max(0.5, energy_capacity - max(0, burden_pressure - 3) * 0.6)
    if burden <= capacity:
        return max(0.65, 1 - abs(capacity - burden) * 0.08)
    return max(0.0, 1 - (burden - capacity) / 4)


def _cost_fit(profile: dict[str, Any], mission: pd.Series) -> float:
    # Mission rows do not carry direct cost, so use budget as a soft readiness signal.
    budget = int(profile.get("budget_limit", 0))
    return 1.0 if budget >= 0 else 0.8


def _progress_sets(progress: pd.DataFrame | None) -> tuple[set[str], set[str], set[str]]:
    if progress is None or progress.empty:
        return set(), set(), set()
    completed = set(progress.loc[progress["status"] == "completed", "mission_id"].astype(str))
    skipped = set(progress.loc[progress["status"] == "skipped", "mission_id"].astype(str))
    too_hard = set(progress.loc[progress["status"] == "too_hard", "mission_id"].astype(str))
    return completed, skipped, too_hard


def rank_missions(
    profile: Any,
    missions: pd.DataFrame,
    recommended_stage: int,
    resources: pd.DataFrame | None = None,
    progress: pd.DataFrame | None = None,
    top_n: int = 3,
) -> list[dict[str, Any]]:
    p = _profile_dict(profile)
    interests = p.get("interests", [])
    if not isinstance(interests, list):
        interests = parse_list(interests)
    completed, skipped, too_hard = _progress_sets(progress)
    resource_available = 1.0 if resources is not None and not resources.empty else 0.5
    rows: list[dict[str, Any]] = []
    for _, mission in missions.iterrows():
        mission_id = str(mission["mission_id"])
        if mission_id in completed:
            novelty = 0.0
        elif mission_id in skipped:
            novelty = 0.4
        elif mission_id in too_hard:
            novelty = 0.2
        else:
            novelty = 1.0

        stage_delta = abs(int(mission["stage"]) - recommended_stage)
        stage_match = 1.0 if stage_delta == 0 else 0.65 if stage_delta == 1 else 0.15
        burden_fit = _burden_fit(p, int(mission["burden_level"]))
        interest_fit = max(
            _fit_overlap(interests, parse_list(mission.get("career_tags", ""))),
            _fit_overlap(interests, parse_list(mission.get("recovery_tags", ""))),
        )
        progress_continuity = 1.0 if int(mission["stage"]) >= recommended_stage and mission_id not in too_hard else 0.45
        score = (
            stage_match * 0.30
            + burden_fit * 0.25
            + interest_fit * 0.15
            + resource_available * 0.10
            + progress_continuity * 0.10
            + novelty * 0.05
            + _cost_fit(p, mission) * 0.05
        )
        row = mission.to_dict()
        row["score"] = round(float(score), 4)
        row["career_tags"] = parse_list(row.get("career_tags", ""))
        row["recovery_tags"] = parse_list(row.get("recovery_tags", ""))
        rows.append(row)
    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows[:top_n]
