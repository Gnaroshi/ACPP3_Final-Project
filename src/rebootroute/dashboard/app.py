from __future__ import annotations

import html
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

SRC_ROOT = Path(__file__).resolve().parents[2]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from rebootroute.config import load_config
from rebootroute.data.mock_data import load_raw_data
from rebootroute.data.validation import parse_list
from rebootroute.database import get_feedback_df, get_outcomes_df, get_progress_df, log_feedback, log_outcome, log_progress
from rebootroute.modeling.registry import load_metadata
from rebootroute.rag.retriever import search_policy_culture_resources
from rebootroute.recommender.mission_recommender import rank_missions
from rebootroute.recommender.resource_recommender import rank_resources
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


st.set_page_config(page_title="RebootRoute", page_icon="RR", layout="wide")


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
    "mini_project": "미니 일경험",
    "contest": "공모전",
}
COST_LABELS = {
    "free": "무료",
    "low_cost": "저비용",
    "paid": "유료",
    "unknown": "확인 필요",
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
MAP_BOUNDS = {
    "lat_min": 37.34,
    "lat_max": 37.78,
    "lon_min": 126.46,
    "lon_max": 126.82,
}


st.markdown(
    """
    <style>
      :root {
        --rr-bg: #f6f7fb;
        --rr-surface: #ffffff;
        --rr-surface-2: #eef2f7;
        --rr-ink: #111827;
        --rr-muted: #374151;
        --rr-soft: #4b5563;
        --rr-line: #d1d7e0;
        --rr-line-strong: #aeb8c6;
        --rr-primary: #1d4ed8;
        --rr-primary-strong: #1e3a8a;
        --rr-primary-soft: #e8efff;
        --rr-info: #0f766e;
        --rr-info-soft: #e6f3f1;
        --rr-warm: #9a4d00;
        --rr-warm-soft: #fff1df;
        --rr-danger: #b42318;
        --rr-danger-soft: #fff0ee;
      }

      html, body, .stApp, .stMarkdown, .stText, .stCaption, li, label,
      [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
      [data-testid="stExpander"] summary, [data-testid="stForm"], [data-testid="stAlert"] {
        color: var(--rr-ink) !important;
      }

      html, body, .stApp,
      [data-testid="stAppViewContainer"],
      [data-testid="stMain"],
      [data-testid="stMainBlockContainer"],
      section.main {
        background-color: var(--rr-bg) !important;
      }

      .stApp {
        background: var(--rr-bg);
      }

      .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1180px;
      }

      h1, h2, h3, h4 {
        color: var(--rr-ink) !important;
        letter-spacing: 0 !important;
        line-height: 1.25 !important;
      }

      [data-testid="stHeader"],
      [data-testid="stToolbar"],
      [data-testid="stDecoration"],
      [data-testid="stStatusWidget"] {
        display: none !important;
      }

      a, a:visited { color: var(--rr-primary) !important; }

      svg {
        color: var(--rr-muted) !important;
        fill: currentColor !important;
      }

      input, textarea, [contenteditable="true"],
      [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
        color: var(--rr-ink) !important;
        background: var(--rr-surface) !important;
        caret-color: var(--rr-primary) !important;
      }

      [data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
        background: var(--rr-surface) !important;
        border-color: var(--rr-line) !important;
        color: var(--rr-ink) !important;
      }

      [data-baseweb="input"]:focus-within,
      [data-baseweb="select"]:focus-within > div,
      [data-baseweb="textarea"]:focus-within {
        border-color: var(--rr-primary) !important;
        box-shadow: 0 0 0 2px rgba(29, 78, 216, 0.12) !important;
      }

      [data-baseweb="select"] span, [data-baseweb="select"] div,
      [data-baseweb="popover"] li, [role="option"] {
        color: var(--rr-ink) !important;
      }

      [data-testid="stCheckbox"],
      [data-testid="stCheckbox"] *,
      [data-testid="stMultiSelect"] *,
      [data-baseweb="tag"] * {
        color: var(--rr-ink) !important;
      }

      [data-baseweb="tag"] {
        background: var(--rr-primary-soft) !important;
        border: 1px solid #bfd0ff !important;
      }

      [data-baseweb="slider"] div, [data-testid="stThumbValue"] {
        color: var(--rr-ink) !important;
      }

      [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--rr-surface) !important;
        border-color: var(--rr-line) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
      }

      div[data-testid="stMetric"] {
        background: var(--rr-surface);
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 0.8rem 0.9rem;
      }

      div[data-testid="stMetric"] label,
      [data-testid="stMetricLabel"] {
        color: var(--rr-muted) !important;
      }

      [data-testid="stMetricValue"] {
        color: var(--rr-ink) !important;
        font-size: 1.15rem !important;
      }

      .stButton > button {
        min-height: 2.55rem;
        border-radius: 8px;
        border: 1px solid var(--rr-primary) !important;
        background: var(--rr-primary) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        white-space: normal !important;
      }

      .stButton > button * {
        color: #ffffff !important;
      }

      .stButton > button:hover,
      .stButton > button:focus {
        background: var(--rr-primary-strong) !important;
        border-color: var(--rr-primary-strong) !important;
        color: #ffffff !important;
      }

      [data-baseweb="tab-list"] {
        gap: 0.25rem;
        border-bottom: 1px solid var(--rr-line);
      }

      [data-baseweb="tab"] {
        color: var(--rr-muted) !important;
        border-radius: 8px 8px 0 0;
        padding: 0.72rem 0.9rem;
        min-width: max-content;
      }

      [data-baseweb="tab"][aria-selected="true"] {
        color: var(--rr-primary) !important;
        background: var(--rr-surface) !important;
        border: 1px solid var(--rr-line);
        border-bottom-color: var(--rr-surface);
        font-weight: 800;
      }

      [data-testid="stDataFrame"], [data-testid="stTable"] {
        color: var(--rr-ink) !important;
      }

      .rr-app-header {
        background: var(--rr-surface);
        border: 1px solid var(--rr-line);
        border-left: 5px solid var(--rr-primary);
        border-radius: 8px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.85rem;
      }

      .rr-app-title {
        font-size: 1.75rem;
        line-height: 1.2;
        font-weight: 850;
        color: var(--rr-ink) !important;
        margin: 0 0 0.35rem 0;
      }

      .rr-app-subtitle {
        color: var(--rr-muted) !important;
        margin: 0;
        font-size: 0.98rem;
        line-height: 1.6;
      }

      .rr-panel {
        background: var(--rr-surface);
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.65rem 0;
      }

      .rr-step-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.75rem 0 1rem;
      }

      .rr-step {
        background: var(--rr-surface);
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 0.85rem;
      }

      .rr-step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.55rem;
        height: 1.55rem;
        border-radius: 999px;
        background: var(--rr-primary);
        color: #ffffff !important;
        font-weight: 800;
        margin-right: 0.35rem;
      }

      .rr-step strong {
        color: var(--rr-ink) !important;
      }

      .rr-step p {
        color: var(--rr-muted) !important;
        font-size: 0.9rem;
        line-height: 1.55;
        margin: 0.45rem 0 0;
      }

      .rr-stage-panel {
        background: var(--rr-surface);
        border-color: #b6c8f3;
        border-left: 5px solid var(--rr-primary);
      }

      .rr-section-title {
        color: var(--rr-ink) !important;
        font-size: 1.05rem;
        font-weight: 800;
        margin-bottom: 0.45rem;
      }

      .rr-muted {
        color: var(--rr-muted) !important;
        font-size: 0.92rem;
        line-height: 1.6;
      }

      .rr-chip {
        display: inline-block;
        padding: 0.16rem 0.48rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 650;
        margin: 0 0.25rem 0.25rem 0;
        border: 1px solid transparent;
      }

      .rr-chip.teal { background: var(--rr-primary-soft); color: var(--rr-primary-strong) !important; border-color: #bfd0ff; }
      .rr-chip.blue { background: var(--rr-info-soft); color: var(--rr-info) !important; border-color: #b9ddd7; }
      .rr-chip.gold { background: var(--rr-warm-soft); color: var(--rr-warm) !important; border-color: #f0c894; }
      .rr-chip.gray { background: #edf1ef; color: var(--rr-muted) !important; border-color: #d2dcd6; }
      .rr-chip.rose { background: var(--rr-danger-soft); color: var(--rr-danger) !important; border-color: #f2c2bd; }

      .rr-card-title {
        font-size: 1.03rem;
        font-weight: 800;
        color: var(--rr-ink) !important;
        margin-bottom: 0.28rem;
        line-height: 1.35;
      }

      .rr-card-body {
        color: var(--rr-muted) !important;
        line-height: 1.6;
        margin-bottom: 0.55rem;
      }

      .rr-resource-meta {
        color: var(--rr-soft) !important;
        font-size: 0.86rem;
        line-height: 1.5;
        margin-top: 0.2rem;
      }

      .rr-divider { height: 1px; background: var(--rr-line); margin: 1rem 0; }

      .rr-action-list {
        margin: 0.55rem 0 0;
        padding-left: 1.15rem;
      }

      .rr-action-list li {
        color: var(--rr-ink) !important;
        margin: 0.35rem 0;
        line-height: 1.55;
      }

      .rr-source-link {
        display: inline-block;
        margin-top: 0.45rem;
        font-weight: 800;
      }

      .rr-warning {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 8px;
        padding: 1rem;
        color: #7c2d12;
      }

      .rr-warning strong { color: #7c2d12; }

      .rr-empty-note {
        border: 1px dashed var(--rr-line-strong);
        border-radius: 8px;
        padding: 0.9rem;
        color: var(--rr-muted);
        background: #fbfcfb;
      }

      .rr-flow {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.6rem;
        margin: 0.75rem 0 1rem;
      }

      .rr-flow-step {
        background: var(--rr-surface);
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 0.75rem;
        min-height: 5.1rem;
      }

      .rr-flow-step strong {
        display: block;
        color: var(--rr-ink) !important;
        font-size: 0.92rem;
        line-height: 1.35;
        margin-bottom: 0.25rem;
      }

      .rr-flow-step span {
        color: var(--rr-muted) !important;
        font-size: 0.84rem;
        line-height: 1.45;
      }

      .rr-map {
        position: relative;
        height: 420px;
        overflow: hidden;
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        background:
          linear-gradient(90deg, rgba(29, 78, 216, 0.08) 1px, transparent 1px),
          linear-gradient(rgba(29, 78, 216, 0.08) 1px, transparent 1px),
          linear-gradient(135deg, #eef7f5 0%, #f8fafc 42%, #eef2ff 100%);
        background-size: 52px 52px, 52px 52px, auto;
      }

      .rr-map::before {
        content: "INCHEON";
        position: absolute;
        right: 1rem;
        bottom: 0.75rem;
        color: rgba(17, 24, 39, 0.16);
        font-weight: 900;
        letter-spacing: 0.08rem;
      }

      .rr-map-marker {
        position: absolute;
        transform: translate(-50%, -50%);
        width: 0.95rem;
        height: 0.95rem;
        border-radius: 999px;
        border: 2px solid #ffffff;
        box-shadow: 0 4px 12px rgba(17, 24, 39, 0.2);
      }

      .rr-map-marker.user {
        width: 1.25rem;
        height: 1.25rem;
        background: var(--rr-primary);
      }

      .rr-map-marker.place {
        background: var(--rr-info);
      }

      .rr-map-label {
        position: absolute;
        transform: translate(0.55rem, -0.6rem);
        min-width: 6.4rem;
        max-width: 11rem;
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.96);
        color: var(--rr-ink) !important;
        font-size: 0.76rem;
        line-height: 1.3;
        font-weight: 800;
        padding: 0.28rem 0.42rem;
      }

      .rr-map-label small {
        display: block;
        color: var(--rr-muted) !important;
        font-size: 0.7rem;
        font-weight: 650;
        margin-top: 0.1rem;
      }

      .rr-map-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-top: 0.55rem;
        color: var(--rr-muted) !important;
        font-size: 0.86rem;
      }

      .rr-dot {
        display: inline-block;
        width: 0.72rem;
        height: 0.72rem;
        border-radius: 999px;
        margin-right: 0.25rem;
        vertical-align: -0.08rem;
      }

      .rr-dot.user { background: var(--rr-primary); }
      .rr-dot.place { background: var(--rr-info); }

      @media (max-width: 760px) {
        .block-container {
          padding: 0.75rem 0.85rem 2rem;
        }

        .rr-app-header {
          padding: 0.95rem;
        }

        .rr-app-title {
          font-size: 1.42rem;
        }

        .rr-app-subtitle {
          font-size: 0.9rem;
        }

        div[data-testid="column"] {
          width: 100% !important;
          min-width: 100% !important;
          flex: 1 1 100% !important;
        }

        [data-testid="stHorizontalBlock"] {
          gap: 0.65rem !important;
        }

        [data-baseweb="tab-list"] {
          overflow-x: auto;
          flex-wrap: nowrap;
          scrollbar-width: thin;
        }

        [data-baseweb="tab"] {
          padding: 0.65rem 0.75rem;
          font-size: 0.9rem;
        }

        .stButton > button {
          min-height: 2.75rem;
          padding-left: 0.65rem;
          padding-right: 0.65rem;
        }

        div[data-testid="stMetric"] {
          padding: 0.7rem 0.8rem;
        }

        .rr-step-grid {
          grid-template-columns: 1fr;
        }

        .rr-flow {
          grid-template-columns: 1fr;
        }

        .rr-map {
          height: 360px;
        }

        .rr-map-label {
          max-width: 8.5rem;
          font-size: 0.7rem;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def cached_data() -> dict[str, pd.DataFrame]:
    return load_raw_data()


def init_session_state() -> None:
    for key, value in DEFAULT_STATE.items():
        st.session_state.setdefault(key, value)
    st.session_state.setdefault("demo_user_id", "demo_user_rebootroute")
    st.session_state.setdefault("resource_query", "")
    st.session_state.setdefault("resource_district", "전체")
    st.session_state.setdefault("resource_types", DEFAULT_RESOURCE_TYPES)
    st.session_state.setdefault("resource_costs", DEFAULT_COSTS)
    st.session_state.setdefault("resource_max_burden", 3)
    st.session_state.setdefault("resource_online_only", False)
    st.session_state.setdefault("rag_query", "연수구 무료 전시 청년 문화활동")
    st.session_state.setdefault("rag_result", None)
    st.session_state.setdefault("manual_location", False)
    st.session_state.setdefault("user_latitude", DISTRICT_CENTERS[DEFAULT_STATE["district"]][0])
    st.session_state.setdefault("user_longitude", DISTRICT_CENTERS[DEFAULT_STATE["district"]][1])
    st.session_state.setdefault("outcome_type", "program_participation")
    st.session_state.setdefault("outcome_status", "planned")
    st.session_state.setdefault("outcome_note", "")


def e(value: Any) -> str:
    return html.escape(str(value))


def chip(text: str, tone: str = "gray") -> str:
    return f'<span class="rr-chip {tone}">{e(text)}</span>'


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


def render_location_map(resources: pd.DataFrame, *, title: str, max_items: int = 8) -> None:
    user_lat, user_lon = current_user_location()
    points = resources.copy()
    if not points.empty:
        points["latitude"] = pd.to_numeric(points["latitude"], errors="coerce")
        points["longitude"] = pd.to_numeric(points["longitude"], errors="coerce")
        points = points.dropna(subset=["latitude", "longitude"]).head(max_items)
    user_left, user_top = map_position(user_lat, user_lon)
    markers = [
        (
            f'<div class="rr-map-marker user" style="left:{user_left:.2f}%; top:{user_top:.2f}%;" title="내 위치"></div>'
            f'<div class="rr-map-label" style="left:{user_left:.2f}%; top:{user_top:.2f}%;">'
            f"내 위치<small>{e('직접 입력' if st.session_state.get('manual_location') else str(st.session_state['district']) + ' 중심')}</small>"
            "</div>"
        )
    ]
    for _, row in points.iterrows():
        left, top = map_position(float(row["latitude"]), float(row["longitude"]))
        name = display_text(row.get("name")) or "활동 장소"
        district = display_text(row.get("district"))
        distance = row.get("distance_km")
        distance_text = f"{float(distance):.1f}km" if distance is not None and pd.notna(distance) else "거리 확인"
        markers.append(
            (
                f'<div class="rr-map-marker place" style="left:{left:.2f}%; top:{top:.2f}%;" title="{e(name)}"></div>'
                f'<div class="rr-map-label" style="left:{left:.2f}%; top:{top:.2f}%;">'
                f"{e(name)}<small>{e(district)} · {e(distance_text)}</small>"
                "</div>"
            )
        )
    st.markdown(f'<div class="rr-section-title">{e(title)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rr-map">{"".join(markers)}</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="rr-map-legend">
          <span><span class="rr-dot user"></span>내 위치</span>
          <span><span class="rr-dot place"></span>정책·문화 활동 장소</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def render_step_guide() -> None:
    st.markdown(
        """
        <div class="rr-flow">
          <div class="rr-flow-step">
            <strong>1. 내 조건</strong>
            <span>위치, 외출 가능 시간, 비용, 대면 부담을 고릅니다.</span>
          </div>
          <div class="rr-flow-step">
            <strong>2. 추천 루트</strong>
            <span>현재 부담도에 맞는 단계와 오늘 할 미션을 바로 확인합니다.</span>
          </div>
          <div class="rr-flow-step">
            <strong>3. 위치 확인</strong>
            <span>내 위치와 활동 장소를 같은 지도에서 봅니다.</span>
          </div>
          <div class="rr-flow-step">
            <strong>4. 결과 기록</strong>
            <span>시작, 완료, 너무 어려움, 참여/지원 결과를 남깁니다.</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
        ProgressStatus.started: "미션을 시작 상태로 기록했습니다.",
        ProgressStatus.completed: "미션 완료를 기록했습니다.",
        ProgressStatus.skipped: "이번 미션은 나중에 보도록 기록했습니다.",
        ProgressStatus.too_hard: "너무 어려움 피드백을 기록했습니다.",
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
    st.session_state["last_action_message"] = "활동/지원 결과를 기록했습니다."
    st.rerun()


def render_profile_controls() -> None:
    st.markdown('<div class="rr-section-title">1. 내 조건</div>', unsafe_allow_html=True)
    st.selectbox("현재 위치", DISTRICTS, key="district")
    st.checkbox("위도/경도 직접 입력", key="manual_location")
    if st.session_state.get("manual_location"):
        loc1, loc2 = st.columns(2)
        loc1.number_input("위도", min_value=33.0, max_value=39.0, step=0.0001, format="%.4f", key="user_latitude")
        loc2.number_input("경도", min_value=124.0, max_value=132.0, step=0.0001, format="%.4f", key="user_longitude")
    else:
        lat, lon = district_center(str(st.session_state["district"]))
        st.session_state["user_latitude"] = lat
        st.session_state["user_longitude"] = lon
        st.caption(f"지도에는 {st.session_state['district']} 중심 좌표를 내 위치로 표시합니다.")

    st.text_area("오늘 상태", height=90, key="free_text")
    col1, col2 = st.columns(2)
    col1.slider("외출 부담", 1, 5, key="outside_burden")
    col2.slider("대면 부담", 1, 5, key="social_burden")
    col3, col4 = st.columns(2)
    col3.slider("에너지", 1, 5, key="energy_level")
    col4.slider("생활 리듬", 1, 5, key="daily_rhythm_level")
    col5, col6 = st.columns(2)
    col5.slider("취업 부담", 1, 5, key="employment_burden")
    col6.slider("미래 불안", 1, 5, key="future_anxiety")
    st.selectbox("선호 방식", list(CONTACT_LABELS.keys()), format_func=lambda x: CONTACT_LABELS[x], key="preferred_contact_mode")
    st.multiselect("관심 분야", INTERESTS, format_func=lambda x: INTEREST_LABELS.get(x, x), key="interests")
    col7, col8 = st.columns(2)
    col7.number_input("외출 가능 시간(분)", min_value=0, max_value=360, step=5, key="max_outdoor_minutes")
    col8.number_input("오늘 예산(원)", min_value=0, max_value=100000, step=1000, key="budget_limit")
    st.checkbox("함께 확인해줄 사람이 있음", key="has_support_person")
    if st.button("기본값으로 되돌리기", width="stretch"):
        reset_demo_state()
        st.rerun()


def render_outcome_form(profile: UserProfile, resources: pd.DataFrame, missions: list[dict[str, Any]], key_prefix: str) -> None:
    st.markdown('<div class="rr-section-title">4. 활동/지원 결과 기록</div>', unsafe_allow_html=True)
    if resources.empty:
        st.markdown('<div class="rr-empty-note">기록할 자원이 없습니다. 조건을 완화해 후보를 먼저 확인하세요.</div>', unsafe_allow_html=True)
        return
    resource_records = resources.head(10).to_dict("records")
    resource_options = {f"{row['name']} · {row['district']}": row["resource_id"] for row in resource_records}
    mission_options = {"미션 연결 안 함": None}
    mission_options.update({mission["title"]: mission["mission_id"] for mission in missions})
    with st.form(f"{key_prefix}_outcome_form", clear_on_submit=False):
        selected_resource_label = st.selectbox("활동/지원 대상", list(resource_options.keys()))
        selected_type = st.selectbox(
            "기록 종류",
            list(OUTCOME_TYPE_LABELS.keys()),
            format_func=lambda value: OUTCOME_TYPE_LABELS[value],
            key=f"{key_prefix}_outcome_type",
        )
        selected_status = st.selectbox(
            "현재 결과",
            list(OUTCOME_STATUS_LABELS.keys()),
            format_func=lambda value: OUTCOME_STATUS_LABELS[value],
            key=f"{key_prefix}_outcome_status",
        )
        selected_mission_label = st.selectbox("연결 미션", list(mission_options.keys()))
        readiness = st.slider("상담/지원 준비도", 1, 5, 3)
        burden_after = st.slider("진행 후 부담도", 1, 5, 3)
        note = st.text_area("메모", placeholder="예: 공식 페이지 확인 후 신청 대상 조건을 확인함 / 프로그램에 참여함 / 결과 대기 중")
        submitted = st.form_submit_button("결과 저장", use_container_width=True)
    if submitted:
        record_outcome(
            profile,
            outcome_type=selected_type,
            outcome_status=selected_status,
            resource_id=resource_options[selected_resource_label],
            mission_id=mission_options[selected_mission_label],
            readiness_rating=readiness,
            burden_after=burden_after,
            result_note=note,
        )


def render_user_mission(profile: UserProfile, mission: dict[str, Any], recommended_stage: int, key_prefix: str) -> None:
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="rr-card-title">{e(mission["title"])}</div>
            <div class="rr-card-body">{e(mission["description"])}</div>
            {chip("예상 " + str(int(mission["expected_minutes"])) + "분", "teal")}
            {chip("부담도 " + burden_text(mission["burden_level"]), "gold")}
            {chip("외출 필요" if bool(mission["outdoor_required"]) else "집에서 가능", "gray")}
            {chip("대면 있음" if bool(mission["social_contact_required"]) else "대면 없음", "gray")}
            """,
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        mission_key = f"{key_prefix}_{mission['mission_id']}"
        if c1.button("시작", key=f"start_{mission_key}", width="stretch"):
            record_mission_action(profile, mission, ProgressStatus.started, recommended_stage)
        if c2.button("완료", key=f"complete_{mission_key}", width="stretch"):
            record_mission_action(profile, mission, ProgressStatus.completed, recommended_stage)
        if c3.button("나중에", key=f"skip_{mission_key}", width="stretch"):
            record_mission_action(profile, mission, ProgressStatus.skipped, recommended_stage)
        if c4.button("너무 어려움", key=f"hard_{mission_key}", width="stretch"):
            record_mission_action(profile, mission, ProgressStatus.too_hard, recommended_stage)


def render_user_resource(resource: dict[str, Any], key_prefix: str) -> None:
    contact = display_text(resource.get("contact"))
    duration = display_minutes(resource.get("estimated_duration_minutes"))
    source_url = display_text(resource.get("source_url"))
    source_name = display_text(resource.get("source_name")) or "공식 출처"
    address = display_text(resource.get("address"))
    period = format_period(resource)
    online_text = "온라인 확인 가능" if as_bool(resource.get("online_available")) else "현장 정보 확인 필요"
    distance = resource.get("distance_km")
    distance_text = f" · 내 위치에서 약 {float(distance):.1f}km" if distance is not None and pd.notna(distance) else ""
    source_link = (
        f'<a class="rr-source-link" href="{e(source_url)}" target="_blank" rel="noopener noreferrer">{e(source_name)} 열기</a>'
        if source_url
        else ""
    )
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="rr-card-title">{e(resource["name"])}</div>
            <div class="rr-card-body">{e(resource["description"])}</div>
            {chip(RESOURCE_TYPE_LABELS.get(str(resource["resource_type"]), str(resource["resource_type"])), "teal")}
            {chip(str(resource["district"]), "gray")}
            {chip(COST_LABELS.get(str(resource["cost_type"]), str(resource["cost_type"])), "gold")}
            {chip("부담도 " + burden_text(resource["burden_level"]), "gray")}
            <div class="rr-resource-meta">
              {e(online_text)}
              · 예상 {e(str(duration))}분
              · {e(period)}
              {e(distance_text)}
              {(" · " + e(contact)) if contact else ""}
              {("<br/>" + e(address)) if address else ""}
            </div>
            {source_link}
            """,
            unsafe_allow_html=True,
        )


def render_safety_branch(analysis: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="rr-warning">
          <strong>안전 확인이 우선입니다.</strong><br/>
          {e(analysis.get("message") or "지금은 일반 미션 추천보다 안전 확인이 먼저입니다.")}
        </div>
        """,
        unsafe_allow_html=True,
    )
    resources = analysis.get("safety_resources", [])
    for idx, resource in enumerate(resources):
        with st.container(border=True):
            st.markdown(
                f"**{resource.get('name', '도움 연결')}**  \n"
                f"연락처: `{resource.get('contact', '')}`  \n"
                f"{resource.get('description', '')}"
            )


def technical_mission_frame(missions: list[dict[str, Any]]) -> pd.DataFrame:
    cols = ["mission_id", "stage", "title", "mission_type", "burden_level", "expected_minutes", "score"]
    return pd.DataFrame(missions)[[col for col in cols if col in pd.DataFrame(missions).columns]]


def technical_resource_frame(resources: list[dict[str, Any]]) -> pd.DataFrame:
    cols = ["resource_id", "resource_type", "name", "district", "cost_type", "burden_level", "score", "source_name", "source_url"]
    return pd.DataFrame(resources)[[col for col in cols if col in pd.DataFrame(resources).columns]]


init_session_state()

st.markdown(
    """
    <div class="rr-app-header">
      <div class="rr-app-title">RebootRoute</div>
      <p class="rr-app-subtitle">내 위치와 부담도에 맞춰 인천의 실제 정책·문화 활동을 찾고, 오늘 할 행동과 결과까지 기록합니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("last_action_message"):
    st.success(st.session_state.pop("last_action_message"))

tabs = st.tabs(["오늘 루트", "자원·지도", "기록", "검증"])

with tabs[0]:
    data = cached_data()
    resources_df = data["resources"]
    st.subheader("오늘 루트")
    render_step_guide()

    input_col, route_col = st.columns([0.88, 1.32], gap="large")
    with input_col:
        render_profile_controls()
        st.markdown('<div class="rr-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="rr-section-title">자원 조건</div>', unsafe_allow_html=True)
        st.multiselect("자원 종류", list(RESOURCE_TYPE_LABELS.keys()), format_func=lambda x: RESOURCE_TYPE_LABELS[x], key="resource_types")
        st.multiselect("비용", list(COST_LABELS.keys()), format_func=lambda x: COST_LABELS[x], key="resource_costs")
        st.slider("최대 부담도", 0, 5, key="resource_max_burden")
        st.checkbox("온라인으로 먼저 확인 가능한 자원만 보기", key="resource_online_only")
        st.text_input("검색어", placeholder="예: 유유기지, 전시, 구직활동비, 청년공간", key="resource_query")

    profile, analysis = current_profile_and_analysis()
    with route_col:
        if analysis.get("safety_flag"):
            render_safety_branch(analysis)
        stage = int(analysis["recommended_stage"])
        st.markdown(
            f"""
            <div class="rr-panel rr-stage-panel">
              <div class="rr-section-title">2. 추천 루트</div>
              <div class="rr-card-title">{e(STAGE_LABELS.get(stage, '추천 단계'))}</div>
              <div class="rr-card-body">{e(analysis.get("burden_summary", ""))}</div>
              {chip("자동 반영", "teal")}
              {chip("Stage " + str(stage), "gray")}
            </div>
            """,
            unsafe_allow_html=True,
        )
        filtered_resources = filter_resources_for_user(
            resources_df,
            query=st.session_state["resource_query"],
            district=str(st.session_state["district"]),
            resource_types=list(st.session_state["resource_types"]),
            costs=list(st.session_state["resource_costs"]),
            max_burden=int(st.session_state["resource_max_burden"]),
            online_only=bool(st.session_state["resource_online_only"]),
        )
        st.markdown('<div class="rr-section-title">오늘 할 미션</div>', unsafe_allow_html=True)
        missions = analysis.get("next_3_missions", [])
        if missions:
            for idx, mission in enumerate(missions):
                render_user_mission(profile, mission, stage, f"today_{idx}")
        else:
            st.markdown('<div class="rr-empty-note">현재 조건에서는 일반 미션 대신 안전 확인 또는 조건 완화가 필요합니다.</div>', unsafe_allow_html=True)

        if filtered_resources.empty:
            st.markdown(
                """
                <div class="rr-empty-note">
                  조건에 맞는 공식 자원이 없습니다. 최대 부담도를 한 단계 높이거나 자원 종류를 넓혀 확인하세요.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="rr-section-title">3. 위치와 활동 장소</div>', unsafe_allow_html=True)
            render_location_map(filtered_resources, title="내 위치와 추천 장소", max_items=6)
            top_resource = filtered_resources.iloc[0].to_dict()
            st.markdown(
                f"""
                <div class="rr-panel rr-stage-panel">
                  <div class="rr-section-title">가장 작은 다음 행동</div>
                  <div class="rr-muted"><strong>{e(display_text(top_resource.get("name")))}</strong>의 공식 페이지에서 현재 운영 여부와 조건 1줄만 확인합니다.</div>
                  <ol class="rr-action-list">
                    {''.join(f"<li>{e(item)}</li>" for item in next_action_items(top_resource))}
                  </ol>
                </div>
                """,
                unsafe_allow_html=True,
            )
            for idx, resource in enumerate(filtered_resources.head(6).to_dict("records")):
                render_user_resource(resource, f"official_{idx}")
            render_outcome_form(profile, filtered_resources, missions, "today")

with tabs[1]:
    st.subheader("자원·지도")
    data = cached_data()
    st.markdown('<div class="rr-section-title">공식 자원 검색</div>', unsafe_allow_html=True)
    search_col, filter_col = st.columns([1.15, 0.85], gap="large")
    with search_col:
        st.text_input("검색 질문", key="rag_query")
    with filter_col:
        rag_district = st.selectbox("구/군 필터", available_districts(data["resources"]), key="rag_district")
        rag_burden = st.slider("최대 부담도", 0, 5, 3, key="rag_max_burden")
    if st.button("근거 자료 검색", width="stretch"):
        district_value = None if rag_district == "전체" else rag_district
        st.session_state["rag_result"] = search_policy_culture_resources(
            st.session_state["rag_query"],
            district=district_value,
            max_burden_level=rag_burden,
            top_k=5,
        )

    rag_result = st.session_state.get("rag_result")
    if rag_result:
        rag_sources_df = add_distance(pd.DataFrame(rag_result.get("sources", [])), *current_user_location())
        st.markdown(
            f"""
            <div class="rr-panel">
              <div class="rr-section-title">검색 답변</div>
              <div class="rr-muted">{e(rag_result["answer"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not rag_sources_df.empty:
            render_location_map(rag_sources_df, title="내 위치와 검색 결과", max_items=8)
        for idx, resource in enumerate(rag_sources_df.to_dict("records")):
            render_user_resource(resource, f"rag_{idx}")

with tabs[2]:
    profile, analysis = current_profile_and_analysis()
    st.subheader("기록")
    st.markdown(
        """
        <div class="rr-panel">
          <div class="rr-section-title">현재 데모 세션 기록</div>
          <div class="rr-muted">시작/완료/너무 어려움은 progress log에, 프로그램 참여·지원 신청·지원 결과·미니 프로젝트 제출은 outcome log에 저장됩니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    progress_df = get_progress_df(profile.user_id)
    outcome_df = get_outcomes_df(profile.user_id)
    feedback_df = get_feedback_df(profile.user_id)
    m1, m2, m3 = st.columns(3)
    m1.metric("미션 로그", len(progress_df))
    m2.metric("활동/지원 결과", len(outcome_df))
    m3.metric("피드백 이벤트", len(feedback_df))
    st.markdown("#### 미션 진행")
    if progress_df.empty:
        st.markdown('<div class="rr-empty-note">아직 시작/완료/너무 어려움 기록이 없습니다.</div>', unsafe_allow_html=True)
    else:
        user_progress = progress_df[["status", "mission_id", "user_note", "completed_at", "points_awarded", "created_at"]].tail(20)
        st.dataframe(user_progress, width="stretch", hide_index=True)
    st.markdown("#### 활동·지원 결과")
    if outcome_df.empty:
        st.markdown('<div class="rr-empty-note">아직 참여/지원 결과 기록이 없습니다. 오늘 루트 탭에서 결과를 저장하세요.</div>', unsafe_allow_html=True)
    else:
        view = outcome_df[
            [
                "outcome_type",
                "outcome_status",
                "resource_id",
                "mission_id",
                "readiness_rating",
                "burden_after",
                "result_note",
                "created_at",
            ]
        ].tail(20)
        st.dataframe(view, width="stretch", hide_index=True)

with tabs[3]:
    st.subheader("검증")
    profile, analysis = current_profile_and_analysis()
    data = cached_data()
    stage = int(analysis["recommended_stage"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rule Stage", stage)
    c2.metric("ML 보조 Stage", analysis["model_info"].get("ml_predicted_stage", "N/A"))
    c3.metric("Safety", "분기" if analysis["safety_flag"] else "정상")
    c4.metric("Data Version", analysis["model_info"].get("data_version", "unknown"))

    if analysis.get("contributing_factors"):
        st.markdown("**기여 요인**")
        st.write(", ".join(analysis["contributing_factors"]))

    st.markdown("#### 추천 미션 Debug")
    missions_debug = analysis.get("next_3_missions", [])
    if missions_debug:
        st.dataframe(technical_mission_frame(missions_debug), width="stretch", hide_index=True)

    st.markdown("#### 추천 자원 Debug")
    resources_debug = analysis.get("recommended_resources", [])
    if resources_debug:
        st.dataframe(technical_resource_frame(resources_debug), width="stretch", hide_index=True)

    st.markdown("#### Stage별 후보 미션")
    selected_stage = st.selectbox("검토할 Stage", list(range(8)), index=stage)
    ranked = rank_missions(profile, data["missions"], selected_stage, data["resources"], top_n=12)
    st.dataframe(technical_mission_frame(ranked), width="stretch", hide_index=True)

    st.markdown("#### 자원 매칭 Debug")
    resource_filter_col1, resource_filter_col2, resource_filter_col3 = st.columns(3)
    district_filter = resource_filter_col1.selectbox("구/군", ["전체"] + DISTRICTS, key="research_district")
    max_burden = resource_filter_col2.slider("최대 부담도", 0, 5, 3, key="research_max_burden")
    contact_mode = resource_filter_col3.selectbox("접촉 방식", list(CONTACT_LABELS.keys()), format_func=lambda x: CONTACT_LABELS[x], key="research_contact")
    resources = data["resources"].copy()
    if district_filter != "전체":
        resources = resources[resources["district"] == district_filter]
    resources = resources[resources["burden_level"] <= max_burden]
    if hasattr(profile, "model_copy"):
        research_profile = profile.model_copy(deep=True)
    elif hasattr(profile, "copy"):
        research_profile = profile.copy(deep=True)
    else:
        research_profile = UserProfile(**profile.model_dump())
    research_profile.preferred_contact_mode = ContactMode(contact_mode)
    ranked_resources = rank_resources(research_profile, resources, recommended_stage=stage, top_n=20)
    st.dataframe(technical_resource_frame(ranked_resources), width="stretch", hide_index=True)

    st.markdown("#### Feedback / Progress 로그")
    feedback_df = get_feedback_df(profile.user_id)
    progress_df = get_progress_df(profile.user_id)
    outcome_df = get_outcomes_df(profile.user_id)
    log_col1, log_col2, log_col3 = st.columns(3)
    with log_col1:
        st.caption("feedback_events")
        st.dataframe(feedback_df.tail(20), width="stretch", hide_index=True)
    with log_col2:
        st.caption("progress_logs")
        st.dataframe(progress_df.tail(20), width="stretch", hide_index=True)
    with log_col3:
        st.caption("outcome_events")
        st.dataframe(outcome_df.tail(20), width="stretch", hide_index=True)

    st.markdown("#### 운영자 검토 입력")
    with st.form("operator_review_form", clear_on_submit=True):
        review_status = st.selectbox("검토 결과", ["verified", "needs_follow_up", "rework_requested"], format_func=lambda value: OUTCOME_STATUS_LABELS[value])
        operator_note = st.text_area("운영자 메모", placeholder="예: 미션 난이도 적합, 다음에는 부담도 1 낮춘 미션 권장")
        submitted_review = st.form_submit_button("검토 저장", width="stretch")
    if submitted_review:
        record_outcome(
            profile,
            outcome_type="operator_review",
            outcome_status=review_status,
            resource_id=None,
            mission_id=None,
            readiness_rating=None,
            burden_after=None,
            result_note=None,
            operator_review_status=review_status,
            operator_note=operator_note,
        )

    with st.expander("Raw analyze_profile payload"):
        st.json(analysis)

    st.markdown("#### 평가·모델")
    cfg = load_config()
    metadata = load_metadata()
    cols = st.columns(4)
    cols[0].metric("Stage 모델", metadata.get("stage_model_name", "untrained"))
    cols[1].metric("Mission 모델", metadata.get("mission_success_model_name", "untrained"))
    cols[2].metric("Data Version", metadata.get("data_version", "unknown"))
    cols[3].metric("학습 시각", metadata.get("trained_at") or "N/A")

    metrics = {
        "Stage accuracy": metadata.get("stage_metrics", {}).get("accuracy"),
        "Stage macro F1": metadata.get("stage_metrics", {}).get("macro_f1"),
        "Mission accuracy": metadata.get("mission_success_metrics", {}).get("accuracy"),
        "Mission macro F1": metadata.get("mission_success_metrics", {}).get("macro_f1"),
        "Mission ROC-AUC": metadata.get("mission_success_metrics", {}).get("roc_auc"),
    }
    st.dataframe(pd.DataFrame([metrics]), width="stretch", hide_index=True)

    st.markdown("#### 산출물")
    st.markdown(
        f"""
        - 모델 메타데이터: `{cfg.model_dir / "metadata.json"}`
        - 모델 카드: `{cfg.reports_dir / "model_card.md"}`
        - 데이터 카드: `{cfg.reports_dir / "data_card.md"}`
        - Human eval sheet: `{cfg.reports_dir / "human_eval_review_sheet.csv"}`
        """
    )

    eval_path = cfg.reports_dir / "human_eval_review_sheet.csv"
    if eval_path.exists():
        st.markdown("#### Human Evaluation 샘플")
        st.dataframe(pd.read_csv(eval_path).head(10), width="stretch", hide_index=True)

    st.markdown("#### Synthetic label 경고")
    st.warning(
        metadata.get(
            "synthetic_label_warning_ko",
            "현재 학습 label은 synthetic placeholder입니다. 실제 관측 outcome label은 운영 또는 기관 연계 후 수집·import해야 합니다.",
        )
    )
