from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

from rebootroute import __version__
from rebootroute.config import load_config
from rebootroute.data.mock_data import get_sample_profile, load_raw_data
from rebootroute.database import get_reboot_points, log_feedback, log_progress
from rebootroute.modeling.registry import load_metadata
from rebootroute.recommender.mission_recommender import rank_missions
from rebootroute.recommender.resource_recommender import rank_resources
from rebootroute.rag.retriever import search_policy_culture_resources
from rebootroute.recommender.route_builder import analyze_profile, recommend_full_route
from rebootroute.schemas import FeedbackEvent, ProgressLog, ProgressStatus, RAGSearchRequest, SimulationRequest, UserProfile


app = FastAPI(
    title="RebootRoute API",
    description="인천 청년정책·문화활동 RAG와 부담도 기반 미션 추천 MVP API입니다.",
    version=__version__,
)


def json_safe(value: Any) -> Any:
    if isinstance(value, BaseModel) and hasattr(value, "model_dump"):
        return json_safe(value.model_dump(mode="json"))
    if isinstance(value, BaseModel):
        return json_safe(value.dict())
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [json_safe(v) for v in value]
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if pd.isna(value) and not isinstance(value, (str, bool)):
        return None
    return value


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "rebootroute", "version": __version__}


@app.get("/metadata")
def metadata() -> dict[str, Any]:
    return json_safe(load_metadata())


@app.get("/sample_profile")
def sample_profile() -> dict[str, Any]:
    return json_safe(get_sample_profile())


@app.post("/analyze_intake")
def analyze_intake(profile: UserProfile) -> dict[str, Any]:
    return json_safe(analyze_profile(profile))


@app.post("/recommend_route")
def recommend_route(profile: UserProfile) -> dict[str, Any]:
    return json_safe(recommend_full_route(profile))


@app.post("/recommend_missions")
def recommend_missions(profile: UserProfile) -> dict[str, Any]:
    data = load_raw_data()
    analysis = analyze_profile(profile)
    missions = rank_missions(
        profile,
        data["missions"],
        int(analysis["recommended_stage"]),
        resources=data["resources"],
        top_n=10,
    )
    return json_safe({"recommended_stage": analysis["recommended_stage"], "missions": missions})


@app.post("/recommend_resources")
def recommend_resources(profile: UserProfile) -> dict[str, Any]:
    data = load_raw_data()
    analysis = analyze_profile(profile)
    resources = rank_resources(profile, data["resources"], recommended_stage=int(analysis["recommended_stage"]), top_n=10)
    return json_safe({"recommended_stage": analysis["recommended_stage"], "resources": resources})


@app.post("/rag/search")
def rag_search(request: RAGSearchRequest) -> dict[str, Any]:
    resource_types = [item.value if hasattr(item, "value") else str(item) for item in request.resource_types]
    return json_safe(
        search_policy_culture_resources(
            query=request.query,
            district=request.district,
            resource_types=resource_types,
            max_burden_level=request.max_burden_level,
            top_k=request.top_k,
        )
    )


@app.post("/feedback/log")
def feedback_log(event: FeedbackEvent) -> dict[str, Any]:
    return json_safe(log_feedback(event))


@app.post("/progress/log")
def progress_log(progress: ProgressLog) -> dict[str, Any]:
    data = load_raw_data()
    payload = progress
    if payload.status == ProgressStatus.completed and not payload.completed_at:
        payload.completed_at = datetime.now(timezone.utc)
    if payload.status == ProgressStatus.completed and payload.points_awarded == 0:
        match = data["missions"][data["missions"]["mission_id"] == payload.mission_id]
        if not match.empty:
            payload.points_awarded = int(match.iloc[0]["reward_points"])
    state = log_progress(payload)
    return json_safe({"log": payload, "state": state, "reboot_points": get_reboot_points(payload.user_id)})


@app.post("/simulate")
def simulate(request: SimulationRequest) -> dict[str, Any]:
    base = request.profile.model_dump() if hasattr(request.profile, "model_dump") else request.profile.dict()
    scenarios = []
    if not request.changes:
        return json_safe({"base": analyze_profile(request.profile), "scenarios": scenarios})
    for field, values in request.changes.items():
        for value in values:
            modified = dict(base)
            modified[field] = value
            profile = UserProfile(**modified)
            result = analyze_profile(profile)
            scenarios.append({"field": field, "value": value, "recommended_stage": result["recommended_stage"], "route_name": result["recommended_route_name"]})
    return json_safe({"base": analyze_profile(request.profile), "scenarios": scenarios})
