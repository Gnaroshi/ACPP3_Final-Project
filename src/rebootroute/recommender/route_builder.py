from __future__ import annotations

from typing import Any

import pandas as pd

from rebootroute.config import load_config
from rebootroute.data.mock_data import load_raw_data
from rebootroute.database import get_progress_df
from rebootroute.modeling.predict import predict_stage_ml
from rebootroute.modeling.registry import load_metadata
from rebootroute.recommender.mini_project_generator import generate_mini_projects
from rebootroute.recommender.mission_recommender import rank_missions
from rebootroute.recommender.resource_recommender import rank_resources
from rebootroute.recommender.safety_guardrails import check_safety, safety_language_notice
from rebootroute.recommender.stage_rules import ROUTE_NAMES, classify_stage_rule_based


def _profile_dict(profile: Any) -> dict[str, Any]:
    if hasattr(profile, "model_dump"):
        return profile.model_dump(mode="json")
    if hasattr(profile, "dict"):
        return profile.dict()
    return dict(profile)


def _user_progress(user_id: str, raw_progress: pd.DataFrame) -> pd.DataFrame:
    frames = []
    try:
        db_progress = get_progress_df(user_id)
        if not db_progress.empty:
            frames.append(db_progress[["log_id", "user_id", "mission_id", "status", "user_note", "completed_at", "points_awarded"]])
    except Exception:
        pass
    if not raw_progress.empty and "user_id" in raw_progress.columns:
        sample_progress = raw_progress[raw_progress["user_id"] == user_id]
        if not sample_progress.empty:
            frames.append(sample_progress)
    if not frames:
        return pd.DataFrame(columns=["log_id", "user_id", "mission_id", "status", "user_note", "completed_at", "points_awarded"])
    return pd.concat(frames, ignore_index=True)


def analyze_profile(profile: Any) -> dict[str, Any]:
    cfg = load_config()
    p = _profile_dict(profile)
    safety = check_safety(p.get("free_text", ""))
    model_info = load_metadata()
    if safety["safety_flag"]:
        return {
            "recommended_stage": 0,
            "recommended_route_name": "안전 확인 우선",
            "burden_summary": "위험 표현이 감지되어 일반 미션 추천을 중단했습니다.",
            "explanation": safety["message"],
            "next_3_missions": [],
            "recommended_resources": [],
            "mini_project_candidates": [],
            "safety_flag": True,
            "risk_type": safety["risk_type"],
            "message": safety["message"],
            "safety_resources": safety["safety_resources"],
            "model_info": {
                "stage_model_version": model_info.get("stage_model_version", "untrained"),
                "data_version": model_info.get("data_version", "unknown"),
                "trained_at": model_info.get("trained_at"),
            },
            "contributing_factors": [],
        }

    data = load_raw_data()
    progress = _user_progress(str(p.get("user_id", "")), data["progress"])
    decision = classify_stage_rule_based(p, progress=progress, missions=data["missions"])
    ml_pred = predict_stage_ml(p, progress=progress, missions=data["missions"])
    missions = rank_missions(
        p,
        data["missions"],
        decision.recommended_stage,
        resources=data["resources"],
        progress=progress,
        top_n=cfg.default_top_missions,
    )
    resources = rank_resources(p, data["resources"], recommended_stage=decision.recommended_stage, top_n=cfg.default_top_resources)
    mini_projects = []
    if decision.recommended_stage >= 5:
        mini_projects = generate_mini_projects(p, pd.DataFrame(resources), limit=4)

    explanation = f"{decision.explanation} {safety_language_notice()}"
    return {
        "recommended_stage": decision.recommended_stage,
        "recommended_route_name": decision.recommended_route_name,
        "burden_summary": decision.burden_summary,
        "explanation": explanation,
        "next_3_missions": missions,
        "recommended_resources": resources,
        "mini_project_candidates": mini_projects,
        "safety_flag": False,
        "risk_type": None,
        "message": None,
        "safety_resources": [],
        "model_info": {
            "stage_model_version": model_info.get("stage_model_version", "untrained"),
            "data_version": model_info.get("data_version", "unknown"),
            "trained_at": model_info.get("trained_at"),
            "ml_predicted_stage": ml_pred.get("predicted_stage"),
        },
        "contributing_factors": list(dict.fromkeys(decision.contributing_factors + ml_pred.get("contributing_factors", []))),
    }


def recommend_full_route(profile: Any) -> dict[str, Any]:
    base = analyze_profile(profile)
    if base["safety_flag"]:
        return base
    data = load_raw_data()
    p = _profile_dict(profile)
    stages = []
    for stage in range(base["recommended_stage"], min(8, base["recommended_stage"] + 3)):
        missions = rank_missions(p, data["missions"], stage, data["resources"], top_n=3)
        resources = rank_resources(p, data["resources"], stage, top_n=3)
        stages.append(
            {
                "stage": stage,
                "route_name": ROUTE_NAMES[stage],
                "missions": missions,
                "resources": resources,
            }
        )
    base["route"] = stages
    base["current_stage"] = base["recommended_stage"]
    base["next_stage"] = min(7, base["recommended_stage"] + 1)
    return base

