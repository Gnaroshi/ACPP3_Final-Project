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


def _overlap(profile_tags: list[str], tags: list[str]) -> float:
    if not profile_tags or not tags:
        return 0.0
    return len(set(profile_tags) & set(tags)) / max(len(set(profile_tags)), 1)


def _burden_fit(profile: dict[str, Any], resource: pd.Series) -> float:
    burden = int(resource["burden_level"])
    if bool(resource.get("outdoor_required", False)) and int(profile["outside_burden"]) >= 4:
        burden += 1
    if int(resource.get("social_contact_level", 0)) >= 3 and int(profile["social_burden"]) >= 4:
        burden += 1
    capacity = (int(profile["energy_level"]) + int(profile["daily_rhythm_level"])) / 2
    if burden <= capacity:
        return max(0.70, 1 - abs(capacity - burden) * 0.08)
    return max(0.0, 1 - (burden - capacity) / 5)


def _contact_fit(mode: str, resource: pd.Series) -> float:
    social = int(resource.get("social_contact_level", 0))
    online = bool(resource.get("online_available", False))
    if mode == "online":
        return 1.0 if online else 0.35
    if mode == "low_contact":
        return 1.0 if online or social <= 2 else 0.45
    if mode == "small_group":
        return 1.0 if social <= 3 else 0.65
    return 0.9 if social <= 5 else 0.5


def _cost_fit(budget: int, cost_type: str) -> float:
    if cost_type == "free":
        return 1.0
    if cost_type == "low_cost":
        return 0.95 if budget >= 5000 else 0.55
    if cost_type == "paid":
        return 0.75 if budget >= 20000 else 0.15
    return 0.60


def rank_resources(profile: Any, resources: pd.DataFrame, recommended_stage: int | None = None, top_n: int = 5) -> list[dict[str, Any]]:
    p = _profile_dict(profile)
    interests = p.get("interests", [])
    if not isinstance(interests, list):
        interests = parse_list(interests)
    rows: list[dict[str, Any]] = []
    for _, resource in resources.iterrows():
        career_tags = parse_list(resource.get("career_tags", ""))
        recovery_tags = parse_list(resource.get("recovery_tags", ""))
        district_match = 1.0 if str(resource["district"]) == str(p["district"]) else 0.45
        burden_fit = _burden_fit(p, resource)
        interest_fit = max(_overlap(interests, career_tags), _overlap(interests, recovery_tags))
        contact_mode_fit = _contact_fit(str(p["preferred_contact_mode"]), resource)
        cost_fit = _cost_fit(int(p.get("budget_limit", 0)), str(resource.get("cost_type", "unknown")))
        career_fit = _overlap(interests, career_tags)
        score = (
            district_match * 0.20
            + burden_fit * 0.25
            + interest_fit * 0.20
            + contact_mode_fit * 0.15
            + cost_fit * 0.10
            + career_fit * 0.10
        )
        if recommended_stage is not None:
            if recommended_stage <= 2 and int(resource.get("burden_level", 0)) >= 4:
                score *= 0.75
            if recommended_stage >= 5 and career_fit > 0:
                score += 0.05
        row = resource.to_dict()
        row["score"] = round(float(score), 4)
        row["career_tags"] = career_tags
        row["recovery_tags"] = recovery_tags
        rows.append(row)
    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows[:top_n]
