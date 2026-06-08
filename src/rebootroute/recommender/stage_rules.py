from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


ROUTE_NAMES = {
    0: "오늘 가능한 행동을 고르는 루트",
    1: "비대면으로 방문·문의 준비하는 루트",
    2: "동선과 시간을 정하는 루트",
    3: "혼자 가능한 짧은 외출 루트",
    4: "낮은 부담 참여 루트",
    5: "관심 기반 기록·탐색 루트",
    6: "작은 결과물 포트폴리오 루트",
    7: "지원기관 연결 준비 루트",
}


@dataclass
class StageDecision:
    recommended_stage: int
    recommended_route_name: str
    burden_summary: str
    explanation: str
    contributing_factors: list[str]


def _profile_dict(profile: Any) -> dict[str, Any]:
    if hasattr(profile, "model_dump"):
        return profile.model_dump(mode="json")
    if hasattr(profile, "dict"):
        return profile.dict()
    return dict(profile)


def _completed_by_stage(progress: pd.DataFrame | None, missions: pd.DataFrame | None = None) -> dict[int, int]:
    counts = {stage: 0 for stage in range(8)}
    if progress is None or progress.empty:
        return counts
    df = progress.copy()
    if missions is not None and "stage" not in df.columns:
        df = df.merge(missions[["mission_id", "stage"]], on="mission_id", how="left")
    if "stage" not in df.columns:
        return counts
    completed = df[df["status"] == "completed"]
    for stage, count in completed.groupby("stage").size().items():
        if pd.notna(stage):
            counts[int(stage)] = int(count)
    return counts


def _burden_summary(p: dict[str, Any]) -> str:
    parts = []
    if int(p["outside_burden"]) >= 4:
        parts.append("외출 부담이 높은 편")
    if int(p["social_burden"]) >= 4:
        parts.append("대면 부담이 높은 편")
    if int(p["employment_burden"]) >= 4:
        parts.append("취업 관련 압박이 큰 편")
    if int(p["energy_level"]) <= 2:
        parts.append("에너지가 낮은 편")
    if not parts:
        parts.append("낮은 부담 활동부터 확장 가능한 상태")
    return ", ".join(parts) + "입니다."


def classify_stage_rule_based(profile: Any, progress: pd.DataFrame | None = None, missions: pd.DataFrame | None = None) -> StageDecision:
    p = _profile_dict(profile)
    completed = _completed_by_stage(progress, missions)
    energy = int(p["energy_level"])
    outside = int(p["outside_burden"])
    social = int(p["social_burden"])
    employment = int(p["employment_burden"])
    rhythm = int(p["daily_rhythm_level"])
    contact = str(p["preferred_contact_mode"])
    interests = p.get("interests", [])
    if not isinstance(interests, list):
        interests = []

    factors: list[str] = []
    stage = 2
    explanation = "현재 입력값을 바탕으로 바로 큰 참여보다 동선과 시간을 정하는 준비 행동이 적합하다고 판단했습니다."

    if completed[6] >= 1 and energy >= 4 and rhythm >= 3 and employment <= 4:
        stage = 7
        factors += ["completed Stage 6 missions", "energy_level high", "daily_rhythm_level stable"]
        explanation = "작은 결과물 미션을 한 번 이상 완료했고 생활 리듬과 에너지가 받쳐주므로 지원기관 연결을 준비하는 단계가 가능합니다."
    elif completed[5] >= 1 and energy >= 3 and len(interests) >= 1:
        stage = 6
        factors += ["completed Stage 5 missions", "clear interest tags"]
        explanation = "관심 기반 기록·탐색 미션을 완료한 이력이 있어 작은 결과물을 만드는 단계로 연결할 수 있습니다."
    elif completed[3] + completed[4] >= 3:
        stage = 5
        factors += ["completed Stage 3/4 missions"]
        explanation = "짧은 외출 또는 낮은 부담 참여 경험이 누적되어 관심사를 직무탐색 과제로 바꾸기 좋은 시점입니다."
    elif energy <= 2 and outside >= 4 and social >= 4:
        stage = 0 if completed[0] == 0 and contact == "online" else 1
        factors += ["energy_level low", "outside_burden high", "social_burden high", f"preferred {contact} mode"]
        explanation = "에너지와 외출·대면 부담을 고려해 신청이나 방문보다 오늘 가능한 조건을 정하고 비대면 준비를 하는 단계가 적합합니다."
    elif outside >= 4:
        stage = 1
        factors += ["outside_burden high"]
        explanation = "외출 부담이 높으므로 방문이나 참여 전에 문의 문장, 비용, 시간, 대체 동선을 정리하는 단계가 적합합니다."
    elif energy >= 3 and outside <= 3 and social >= 4:
        stage = 2 if int(p.get("max_outdoor_minutes", 0)) < 20 else 3
        factors += ["social_burden high", "outside_burden manageable", "solo activity preferred"]
        explanation = "외출은 어느 정도 가능하지만 대면 부담이 높아 혼자 가능한 준비나 짧은 문화공간 확인이 적합합니다."
    elif energy >= 3 and outside <= 3 and social <= 3:
        stage = 4 if int(p.get("max_outdoor_minutes", 0)) >= 30 else 3
        factors += ["energy_level moderate", "outside_burden manageable", "social_burden manageable"]
        explanation = "에너지와 외출 부담이 비교적 안정적이어서 짧은 외출 또는 낮은 부담 참여까지 시도할 수 있습니다."
    elif employment >= 4 and energy >= 3:
        stage = 3
        factors += ["employment_burden high", "energy_level moderate"]
        explanation = "취업 압박이 크지만 바로 직무훈련보다 지역 활동과 작은 성공 경험을 먼저 만드는 단계가 적합합니다."

    if stage >= 7 and not (completed[6] >= 1 and energy >= 4):
        stage = 6
        explanation = "지원기관 연결 단계로 바로 이동하지 않고, 작은 결과물을 만드는 단계로 한 번 더 연결합니다."
    return StageDecision(
        recommended_stage=int(stage),
        recommended_route_name=ROUTE_NAMES[int(stage)],
        burden_summary=_burden_summary(p),
        explanation=explanation,
        contributing_factors=list(dict.fromkeys(factors)),
    )
