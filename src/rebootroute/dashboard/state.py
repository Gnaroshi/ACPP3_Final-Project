from __future__ import annotations

import html
import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import streamlit as st

from rebootroute.data.mock_data import load_raw_data
from rebootroute.data.validation import parse_list
from rebootroute.database import log_feedback, log_outcome, log_progress
from rebootroute.recommender.route_builder import analyze_profile
from rebootroute.schemas import (
    ContactMode,
    FeedbackEvent,
    FeedbackEventType,
    OutcomeEvent,
    OutcomeStatus,
    OutcomeType,
    ProgressLog,
    ProgressStatus,
    UserProfile,
)


DISTRICTS = ["중구", "동구", "미추홀구", "연수구", "남동구", "부평구", "계양구", "서구", "강화군", "옹진군"]
INTERESTS = ["culture", "design", "writing", "IT", "public_policy", "planning", "library", "media", "craft", "data"]
INTEREST_LABELS = {
    "culture": "문화",
    "design": "디자인",
    "writing": "글쓰기",
    "IT": "IT",
    "public_policy": "공공정책",
    "planning": "기획",
    "library": "도서관",
    "media": "미디어",
    "craft": "공예",
    "data": "데이터",
}
CONTACT_LABELS = {
    "online": "온라인",
    "low_contact": "낮은 대면",
    "small_group": "소규모",
    "in_person": "대면 가능",
}
RESOURCE_TYPE_LABELS = {
    "youth_program": "청년 프로그램",
    "culture_event": "문화 행사",
    "culture_facility": "문화 시설",
    "support_program": "지원 정보",
}
RESOURCE_SCOPE_OPTIONS = {
    "전체": ["youth_program", "support_program", "culture_event", "culture_facility"],
    "정책·지원": ["support_program"],
    "청년 프로그램": ["youth_program"],
    "문화 행사": ["culture_event"],
    "공간·장소": ["culture_facility"],
}
ACCESS_MODE_OPTIONS = ["전체", "온라인 먼저 확인", "방문 가능한 장소 포함"]
COST_SCOPE_OPTIONS = {
    "무료/확인필요": ["free", "unknown"],
    "무료만": ["free"],
    "전체": ["free", "low_cost", "unknown", "paid"],
}
COST_LABELS = {
    "free": "무료",
    "low_cost": "저비용",
    "paid": "유료",
    "unknown": "확인 필요",
}
SOURCE_KIND_LABELS = {
    "open_api": "공식 API 수집",
    "html_scrape": "공식 페이지 수집",
    "fallback_seed": "검증용 기본 데이터",
    "manual_verified": "수동 검증",
}
STAGE_LABELS = {
    0: "오늘 컨디션 정리",
    1: "비대면 준비",
    2: "동선 계획",
    3: "짧은 외출",
    4: "저부담 참여",
    5: "관심 기반 기록",
    6: "작은 결과물 만들기",
    7: "지원 연결 준비",
}
DEFAULT_STATE = {
    "age": 27,
    "district": "연수구",
    "preferred_contact_mode": "online",
    "interests": ["culture", "writing", "design"],
    "budget_limit": 0,
    "has_support_person": False,
    "future_anxiety": 5,
    "employment_burden": 5,
    "outside_burden": 4,
    "social_burden": 5,
    "energy_level": 2,
    "daily_rhythm_level": 2,
    "max_outdoor_minutes": 20,
    "free_text": "취업해야 하는데 자신이 없고 사람 만나는 것도 부담돼요. 요즘은 거의 집에만 있어요.",
}
DEFAULT_RESOURCE_TYPES = ["youth_program", "support_program", "culture_event", "culture_facility"]
DEFAULT_COSTS = ["free", "low_cost", "unknown"]
ROUTE_RANGE_OPTIONS = ["집에서", "20분 외출", "1시간 가능", "상관없음"]
ROUTE_CONTACT_OPTIONS = ["비대면", "낮은 대면", "소규모", "상관없음"]
ROUTE_INTENT_OPTIONS = ["지원금", "청년공간", "문화행사", "프로그램"]
ROUTE_COST_OPTIONS = ["무료", "저비용 포함", "전체"]
ROUTE_RANGE_CONFIG = {
    "집에서": {"max_outdoor_minutes": 0, "outside_burden": 5, "resource_access_mode": "온라인 먼저 확인"},
    "20분 외출": {"max_outdoor_minutes": 20, "outside_burden": 4, "resource_access_mode": "전체"},
    "1시간 가능": {"max_outdoor_minutes": 60, "outside_burden": 3, "resource_access_mode": "방문 가능한 장소 포함"},
    "상관없음": {"max_outdoor_minutes": 120, "outside_burden": 2, "resource_access_mode": "전체"},
}
ROUTE_CONTACT_CONFIG = {
    "비대면": {"preferred_contact_mode": "online", "social_burden": 5, "resource_access_mode": "온라인 먼저 확인"},
    "낮은 대면": {"preferred_contact_mode": "low_contact", "social_burden": 4},
    "소규모": {"preferred_contact_mode": "small_group", "social_burden": 3},
    "상관없음": {"preferred_contact_mode": "in_person", "social_burden": 2},
}
ROUTE_INTENT_CONFIG = {
    "지원금": {"resource_scope": "정책·지원", "interests": ["public_policy", "data"]},
    "청년공간": {"resource_scope": "공간·장소", "interests": ["culture", "planning"]},
    "문화행사": {"resource_scope": "문화 행사", "interests": ["culture", "design"]},
    "프로그램": {"resource_scope": "청년 프로그램", "interests": ["planning", "writing"]},
}
ROUTE_COST_CONFIG = {
    "무료": {"resource_cost_scope": "무료만", "budget_limit": 0},
    "저비용 포함": {"resource_cost_scope": "무료/확인필요", "budget_limit": 10000},
    "전체": {"resource_cost_scope": "전체", "budget_limit": 50000},
}
LEVEL_OPTIONS = [1, 2, 3, 4, 5]
BURDEN_FILTER_OPTIONS = [0, 1, 2, 3, 4, 5]
TIME_OPTIONS = [0, 20, 40, 60, 90, 120, 180]
BUDGET_OPTIONS = [0, 5000, 10000, 30000, 50000, 100000]
DISTRICT_CENTERS = {
    "중구": (37.4737, 126.6219),
    "동구": (37.4739, 126.6427),
    "미추홀구": (37.4636, 126.6504),
    "연수구": (37.4104, 126.6783),
    "남동구": (37.4473, 126.7314),
    "부평구": (37.5070, 126.7219),
    "계양구": (37.5374, 126.7378),
    "서구": (37.5454, 126.6759),
    "강화군": (37.7465, 126.4878),
    "옹진군": (37.4469, 126.6368),
    "인천 전역": (37.4563, 126.7052),
}
OUTCOME_TYPE_LABELS = {
    "program_participation": "프로그램/공간 참여",
    "support_application": "지원 신청",
    "support_result": "지원 결과",
    "mini_project_submission": "미니 프로젝트 제출",
    "operator_review": "운영자 검토",
}
OUTCOME_STATUS_LABELS = {
    "planned": "예정",
    "applied": "신청 완료",
    "participated": "참여 완료",
    "submitted": "제출 완료",
    "accepted": "선정/통과",
    "rejected": "미선정",
    "not_eligible": "대상 아님",
    "needs_follow_up": "추가 확인 필요",
    "verified": "검토 완료",
    "rework_requested": "보완 필요",
    "unknown": "확인 전",
}
PROGRESS_STATUS_LABELS = {
    "recommended": "추천됨",
    "started": "시작",
    "completed": "완료",
    "skipped": "나중에",
    "too_hard": "너무 어려움",
}
MAP_BOUNDS = {
    "lat_min": 37.34,
    "lat_max": 37.78,
    "lon_min": 126.46,
    "lon_max": 126.82,
}


@st.cache_data(show_spinner=False)
def cached_data() -> dict[str, pd.DataFrame]:
    return load_raw_data()


def init_session_state() -> None:
    for key, value in DEFAULT_STATE.items():
        st.session_state.setdefault(key, value)
    st.session_state.setdefault("demo_user_id", "demo_user_rebootroute")
    st.session_state.setdefault("resource_query", "")
    st.session_state.setdefault("resource_district", "전체")
    st.session_state.setdefault("resource_scope", "전체")
    st.session_state.setdefault("resource_access_mode", "전체")
    st.session_state.setdefault("resource_cost_scope", "무료/확인필요")
    st.session_state.setdefault("resource_types", DEFAULT_RESOURCE_TYPES)
    st.session_state.setdefault("resource_costs", DEFAULT_COSTS)
    st.session_state.setdefault("resource_max_burden", 3)
    st.session_state.setdefault("resource_online_only", False)
    st.session_state.setdefault("rag_query", "연수구 무료 전시 청년 문화활동")
    st.session_state.setdefault("rag_result", None)
    st.session_state.setdefault("route_range_choice", "20분 외출")
    st.session_state.setdefault("route_contact_choice", "비대면")
    st.session_state.setdefault("route_intent_choice", "문화행사")
    st.session_state.setdefault("route_cost_choice", "저비용 포함")
    st.session_state.setdefault("show_advanced_controls", False)
    st.session_state.setdefault("show_more_candidates", False)
    st.session_state.setdefault("show_map_large", False)
    st.session_state.setdefault("show_record_panel", False)
    st.session_state.setdefault("manual_location", False)
    st.session_state.setdefault("location_mode", "구/군 중심")
    st.session_state.setdefault("support_mode", "혼자 확인")
    st.session_state.setdefault("user_latitude", DISTRICT_CENTERS[DEFAULT_STATE["district"]][0])
    st.session_state.setdefault("user_longitude", DISTRICT_CENTERS[DEFAULT_STATE["district"]][1])
    st.session_state.setdefault("outcome_type", "program_participation")
    st.session_state.setdefault("outcome_status", "planned")
    st.session_state.setdefault("outcome_note", "")
    st.session_state.setdefault("ui_theme_choice", "밝게")


def e(value: Any) -> str:
    return html.escape(str(value))


def widget_key(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in value)
    return safe[:90] or "item"


def resource_source_url(resource: dict[str, Any]) -> str:
    return display_text(resource.get("detail_url")) or display_text(resource.get("source_url"))


def display_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def source_kind_label(value: Any) -> str:
    text = display_text(value)
    return SOURCE_KIND_LABELS.get(text, text or "공식 출처")


def format_checked_at(value: Any) -> str:
    text = display_text(value)
    if not text:
        return "기록 없음"
    try:
        checked = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if checked.tzinfo is not None:
            checked = checked.astimezone(timezone(timedelta(hours=9)))
        return checked.strftime("%Y-%m-%d %H:%M KST")
    except ValueError:
        return text


def operator_mode_enabled() -> bool:
    value = st.query_params.get("operator", "")
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def current_theme_mode() -> str:
    return "dark" if st.session_state.get("ui_theme_choice") == "어둡게" else "light"


def display_minutes(value: Any) -> int:
    try:
        if pd.isna(value):
            return 0
        return int(value)
    except Exception:
        return 0


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def burden_text(level: int | float | str) -> str:
    labels = ["매우 낮음", "낮음", "낮음", "보통", "높음", "매우 높음"]
    try:
        return labels[max(0, min(5, int(level)))]
    except Exception:
        return "확인 필요"


def level_option_label(value: int) -> str:
    labels = {
        1: "1 낮음",
        2: "2 낮은 편",
        3: "3 보통",
        4: "4 높은 편",
        5: "5 매우 높음",
    }
    return labels.get(int(value), str(value))


def burden_filter_label(value: int) -> str:
    if int(value) == 5:
        return "5 이하 전체"
    return f"{int(value)} 이하"


def time_option_label(value: int) -> str:
    if int(value) == 0:
        return "집에서 확인"
    return f"{int(value)}분"


def budget_option_label(value: int) -> str:
    if int(value) == 0:
        return "무료만"
    return f"{int(value):,}원 이하"


def normalize_option_key(key: str, options: list[int], default: int) -> None:
    try:
        current = int(st.session_state.get(key, default))
    except Exception:
        current = default
    if current not in options:
        current = min(options, key=lambda option: abs(option - current))
    st.session_state[key] = current


def available_districts(resources: pd.DataFrame) -> list[str]:
    values = [display_text(value) for value in resources.get("district", pd.Series(dtype=str)).dropna().unique()]
    ordered = [district for district in ["전체", *DISTRICTS, "인천 전역"] if district == "전체" or district in values]
    extras = sorted(value for value in values if value and value not in ordered)
    return ordered + extras


def district_center(district: str) -> tuple[float, float]:
    return DISTRICT_CENTERS.get(district, DISTRICT_CENTERS["인천 전역"])


def current_user_location() -> tuple[float, float]:
    if st.session_state.get("manual_location"):
        return float(st.session_state["user_latitude"]), float(st.session_state["user_longitude"])
    return district_center(str(st.session_state["district"]))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def add_distance(resources: pd.DataFrame, user_lat: float, user_lon: float) -> pd.DataFrame:
    if resources.empty or "latitude" not in resources.columns or "longitude" not in resources.columns:
        return resources
    df = resources.copy()
    lat = pd.to_numeric(df["latitude"], errors="coerce")
    lon = pd.to_numeric(df["longitude"], errors="coerce")
    df["distance_km"] = [
        haversine_km(user_lat, user_lon, float(row_lat), float(row_lon)) if pd.notna(row_lat) and pd.notna(row_lon) else None
        for row_lat, row_lon in zip(lat, lon, strict=False)
    ]
    return df


def map_position(lat: float, lon: float) -> tuple[float, float]:
    left = (lon - MAP_BOUNDS["lon_min"]) / (MAP_BOUNDS["lon_max"] - MAP_BOUNDS["lon_min"]) * 100
    top = (MAP_BOUNDS["lat_max"] - lat) / (MAP_BOUNDS["lat_max"] - MAP_BOUNDS["lat_min"]) * 100
    return max(2, min(98, left)), max(2, min(98, top))


def filter_resources_for_user(
    resources: pd.DataFrame,
    *,
    query: str,
    district: str,
    resource_types: list[str],
    costs: list[str],
    max_burden: int,
    online_only: bool,
) -> pd.DataFrame:
    filtered = resources.copy()
    if resource_types:
        filtered = filtered[filtered["resource_type"].astype(str).isin(resource_types)]
    if costs:
        filtered = filtered[filtered["cost_type"].astype(str).isin(costs)]
    if district != "전체":
        filtered = filtered[filtered["district"].astype(str).isin([district, "인천 전역"])]
    filtered = filtered[filtered["burden_level"].astype(int) <= int(max_burden)]
    if online_only:
        online_mask = filtered["online_available"].map(as_bool)
        filtered = filtered[online_mask]
    query = query.strip().lower()
    if query:
        def row_text(row: pd.Series) -> str:
            tags = parse_list(row.get("career_tags", "")) + parse_list(row.get("recovery_tags", ""))
            fields = [
                row.get("name", ""),
                row.get("description", ""),
                row.get("district", ""),
                row.get("resource_type", ""),
                row.get("source_name", ""),
                " ".join(tags),
            ]
            return " ".join(display_text(value) for value in fields).lower()

        filtered = filtered[filtered.apply(lambda row: query in row_text(row), axis=1)]
    if filtered.empty:
        return filtered
    user_lat, user_lon = current_user_location()
    filtered = add_distance(filtered, user_lat, user_lon)
    cost_rank = {"free": 0, "low_cost": 1, "unknown": 2, "paid": 3}
    filtered = filtered.assign(
        _cost_rank=filtered["cost_type"].map(lambda value: cost_rank.get(str(value), 4)),
        _online_rank=filtered["online_available"].map(lambda value: 0 if as_bool(value) else 1),
        _distance_rank=filtered["distance_km"].fillna(999) if "distance_km" in filtered.columns else 999,
    )
    return filtered.sort_values(["burden_level", "_cost_rank", "_online_rank", "_distance_rank", "estimated_duration_minutes", "name"]).drop(
        columns=["_cost_rank", "_online_rank", "_distance_rank"]
    )


def format_period(resource: dict[str, Any]) -> str:
    start = display_text(resource.get("start_date"))
    end = display_text(resource.get("end_date"))
    if start and end:
        return f"{start} ~ {end}"
    if start:
        return f"{start}부터"
    if end:
        return f"{end}까지"
    return "상시/공식 페이지 확인"


def next_action_items(resource: dict[str, Any]) -> list[str]:
    name = display_text(resource.get("name")) or "선택한 자원"
    if as_bool(resource.get("online_available")):
        second = "신청하지 말고, 대상·비용·운영시간·마감 여부만 한 줄로 확인합니다."
    else:
        second = "방문하지 말고, 가장 짧은 이동 방법과 운영시간만 먼저 확인합니다."
    contact = display_text(resource.get("contact"))
    contact_action = f"문의가 필요하면 {contact} 정보를 메모합니다." if contact else "문의가 필요하면 공식 페이지의 문의처만 찾아둡니다."
    return [
        f"{name} 공식 페이지를 열어 현재 운영 여부를 확인합니다.",
        second,
        contact_action,
        "오늘 끝낼 결과물은 '내가 확인한 조건 1줄'이면 충분합니다.",
    ]


def profile_payload_from_state() -> dict[str, Any]:
    return {
        "user_id": st.session_state["demo_user_id"],
        "age": int(st.session_state["age"]),
        "district": str(st.session_state["district"]),
        "free_text": str(st.session_state["free_text"]),
        "future_anxiety": int(st.session_state["future_anxiety"]),
        "employment_burden": int(st.session_state["employment_burden"]),
        "outside_burden": int(st.session_state["outside_burden"]),
        "social_burden": int(st.session_state["social_burden"]),
        "energy_level": int(st.session_state["energy_level"]),
        "daily_rhythm_level": int(st.session_state["daily_rhythm_level"]),
        "preferred_contact_mode": ContactMode(str(st.session_state["preferred_contact_mode"])),
        "interests": list(st.session_state["interests"]),
        "max_outdoor_minutes": int(st.session_state["max_outdoor_minutes"]),
        "budget_limit": int(st.session_state["budget_limit"]),
        "has_support_person": bool(st.session_state["has_support_person"]),
    }


def build_profile_from_state() -> UserProfile:
    return UserProfile(**profile_payload_from_state())


def profile_signature(profile: UserProfile) -> str:
    payload = profile.model_dump(mode="python") if hasattr(profile, "model_dump") else profile.dict()
    payload = {key: getattr(value, "value", value) for key, value in payload.items()}
    payload.pop("created_at", None)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def current_profile_and_analysis(force: bool = False) -> tuple[UserProfile, dict[str, Any]]:
    profile = build_profile_from_state()
    signature = profile_signature(profile)
    if force or st.session_state.get("analysis_signature") != signature:
        st.session_state["analysis"] = analyze_profile(profile)
        st.session_state["analysis_signature"] = signature
    return profile, st.session_state["analysis"]


def reset_demo_state() -> None:
    for key, value in DEFAULT_STATE.items():
        st.session_state[key] = value
    st.session_state["manual_location"] = False
    st.session_state["location_mode"] = "구/군 중심"
    st.session_state["support_mode"] = "혼자 확인"
    st.session_state["resource_scope"] = "전체"
    st.session_state["resource_access_mode"] = "전체"
    st.session_state["resource_cost_scope"] = "무료/확인필요"
    st.session_state["resource_types"] = DEFAULT_RESOURCE_TYPES
    st.session_state["resource_costs"] = DEFAULT_COSTS
    st.session_state["resource_online_only"] = False
    st.session_state["resource_query"] = ""
    st.session_state["resource_max_burden"] = 3
    st.session_state["route_range_choice"] = "20분 외출"
    st.session_state["route_contact_choice"] = "비대면"
    st.session_state["route_intent_choice"] = "문화행사"
    st.session_state["route_cost_choice"] = "저비용 포함"
    st.session_state["show_advanced_controls"] = False
    st.session_state["show_more_candidates"] = False
    st.session_state["show_map_large"] = False
    st.session_state["show_record_panel"] = False
    st.session_state["user_latitude"], st.session_state["user_longitude"] = DISTRICT_CENTERS[DEFAULT_STATE["district"]]
    st.session_state["analysis_signature"] = ""
    st.session_state["rag_result"] = None


def record_mission_action(profile: UserProfile, mission: dict[str, Any], status: ProgressStatus, recommended_stage: int) -> None:
    event_by_status = {
        ProgressStatus.started: FeedbackEventType.start,
        ProgressStatus.completed: FeedbackEventType.complete,
        ProgressStatus.skipped: FeedbackEventType.skip,
        ProgressStatus.too_hard: FeedbackEventType.too_hard,
    }
    points = int(mission["reward_points"]) if status == ProgressStatus.completed else 0
    log_progress(
        ProgressLog(
            user_id=profile.user_id,
            mission_id=mission["mission_id"],
            status=status,
            completed_at=datetime.now(timezone.utc) if status == ProgressStatus.completed else None,
            points_awarded=points,
        )
    )
    log_feedback(
        FeedbackEvent(
            user_id=profile.user_id,
            event_type=event_by_status[status],
            mission_id=mission["mission_id"],
            recommended_stage=recommended_stage,
            burden_after=int(mission["burden_level"]) if status in {ProgressStatus.completed, ProgressStatus.too_hard} else None,
            policy_version="streamlit_demo",
        )
    )
    st.session_state["last_action_message"] = {
        ProgressStatus.started: "시작으로 기록했어요.",
        ProgressStatus.completed: "완료로 저장했어요.",
        ProgressStatus.skipped: "나중에로 저장했어요.",
        ProgressStatus.too_hard: "어려움으로 기록했어요.",
    }[status]
    st.rerun()


def record_outcome(
    profile: UserProfile,
    *,
    outcome_type: str,
    outcome_status: str,
    resource_id: str | None,
    mission_id: str | None,
    readiness_rating: int | None,
    burden_after: int | None,
    result_note: str | None,
    operator_review_status: str | None = None,
    operator_note: str | None = None,
) -> None:
    log_outcome(
        OutcomeEvent(
            user_id=profile.user_id,
            outcome_type=OutcomeType(outcome_type),
            outcome_status=OutcomeStatus(outcome_status),
            mission_id=mission_id,
            resource_id=resource_id,
            readiness_rating=readiness_rating,
            burden_after=burden_after,
            result_note=result_note,
            operator_review_status=operator_review_status,
            operator_note=operator_note,
            policy_version="streamlit_demo",
        )
    )
    log_feedback(
        FeedbackEvent(
            user_id=profile.user_id,
            event_type=FeedbackEventType.operator_review if outcome_type == "operator_review" else FeedbackEventType.resource_click,
            mission_id=mission_id,
            resource_id=resource_id,
            recommended_stage=None,
            burden_after=burden_after,
            appropriateness_rating=readiness_rating,
            user_note=result_note,
            policy_version="streamlit_demo",
        )
    )
    if outcome_type == "operator_review":
        st.session_state["last_action_message"] = "운영자 검토를 저장했어요."
    else:
        st.session_state["last_action_message"] = "결과를 저장했어요."
    st.rerun()


def technical_mission_frame(missions: list[dict[str, Any]]) -> pd.DataFrame:
    cols = ["mission_id", "stage", "title", "mission_type", "burden_level", "expected_minutes", "score"]
    return pd.DataFrame(missions)[[col for col in cols if col in pd.DataFrame(missions).columns]]


def technical_resource_frame(resources: list[dict[str, Any]]) -> pd.DataFrame:
    cols = ["resource_id", "resource_type", "name", "district", "cost_type", "burden_level", "score", "source_name", "source_url"]
    return pd.DataFrame(resources)[[col for col in cols if col in pd.DataFrame(resources).columns]]


def user_progress_frame(progress_df: pd.DataFrame, missions_df: pd.DataFrame) -> pd.DataFrame:
    if progress_df.empty:
        return progress_df
    mission_lookup = missions_df.set_index("mission_id")["title"].to_dict() if "mission_id" in missions_df.columns else {}
    view = progress_df.tail(20).copy()
    return pd.DataFrame(
        {
            "상태": view["status"].map(lambda value: PROGRESS_STATUS_LABELS.get(str(value), str(value))),
            "미션": view["mission_id"].map(lambda value: mission_lookup.get(value, "오늘 할 행동")),
            "메모": view["user_note"].map(display_text) if "user_note" in view.columns else "",
            "완료 시각": view["completed_at"].map(display_text) if "completed_at" in view.columns else "",
            "기록 시각": view["created_at"].map(display_text) if "created_at" in view.columns else "",
        }
    )


def user_outcome_frame(outcome_df: pd.DataFrame, resources_df: pd.DataFrame, missions_df: pd.DataFrame) -> pd.DataFrame:
    if outcome_df.empty:
        return outcome_df
    resource_lookup = resources_df.set_index("resource_id")["name"].to_dict() if "resource_id" in resources_df.columns else {}
    mission_lookup = missions_df.set_index("mission_id")["title"].to_dict() if "mission_id" in missions_df.columns else {}
    view = outcome_df.tail(20).copy()
    return pd.DataFrame(
        {
            "기록 종류": view["outcome_type"].map(lambda value: OUTCOME_TYPE_LABELS.get(str(value), str(value))),
            "결과": view["outcome_status"].map(lambda value: OUTCOME_STATUS_LABELS.get(str(value), str(value))),
            "활동/지원 대상": view["resource_id"].map(lambda value: resource_lookup.get(value, "직접 기록")),
            "연결 미션": view["mission_id"].map(lambda value: mission_lookup.get(value, "")),
            "진행 준비도": view["readiness_rating"].map(display_text),
            "진행 후 부담": view["burden_after"].map(display_text),
            "메모": view["result_note"].map(display_text),
            "기록 시각": view["created_at"].map(display_text),
        }
    )


def apply_route_choices_when_changed() -> None:
    signature = (
        st.session_state.get("route_range_choice"),
        st.session_state.get("route_contact_choice"),
        st.session_state.get("route_intent_choice"),
        st.session_state.get("route_cost_choice"),
    )
    if st.session_state.get("route_choice_signature") == signature:
        return
    range_config = ROUTE_RANGE_CONFIG[str(st.session_state["route_range_choice"])]
    contact_config = ROUTE_CONTACT_CONFIG[str(st.session_state["route_contact_choice"])]
    intent_config = ROUTE_INTENT_CONFIG[str(st.session_state["route_intent_choice"])]
    cost_config = ROUTE_COST_CONFIG[str(st.session_state["route_cost_choice"])]
    for config in [range_config, contact_config, intent_config, cost_config]:
        for key, value in config.items():
            st.session_state[key] = value
    st.session_state["resource_max_burden"] = 5 if st.session_state["route_range_choice"] == "상관없음" else 3
    st.session_state["route_choice_signature"] = signature


def sync_derived_resource_filters() -> None:
    st.session_state["resource_types"] = RESOURCE_SCOPE_OPTIONS.get(str(st.session_state["resource_scope"]), DEFAULT_RESOURCE_TYPES)
    st.session_state["resource_costs"] = COST_SCOPE_OPTIONS.get(str(st.session_state["resource_cost_scope"]), DEFAULT_COSTS)
    st.session_state["resource_online_only"] = st.session_state.get("resource_access_mode") == "온라인 먼저 확인"
    if st.session_state.get("manual_location"):
        return
    lat, lon = district_center(str(st.session_state["district"]))
    st.session_state["user_latitude"] = lat
    st.session_state["user_longitude"] = lon
