from __future__ import annotations

import html
import json
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
from rebootroute.database import get_feedback_df, get_progress_df, log_feedback, log_progress
from rebootroute.modeling.registry import load_metadata
from rebootroute.rag.retriever import search_policy_culture_resources
from rebootroute.recommender.mini_project_generator import generate_mini_projects
from rebootroute.recommender.mission_recommender import rank_missions
from rebootroute.recommender.resource_recommender import rank_resources
from rebootroute.recommender.route_builder import analyze_profile
from rebootroute.schemas import ContactMode, FeedbackEvent, FeedbackEventType, ProgressLog, ProgressStatus, UserProfile


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
    st.session_state.setdefault("rag_query", "연수구 무료 전시 청년 문화활동")
    st.session_state.setdefault("rag_result", None)


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


def burden_text(level: int | float | str) -> str:
    labels = ["매우 낮음", "낮음", "낮음", "보통", "높음", "매우 높음"]
    try:
        return labels[max(0, min(5, int(level)))]
    except Exception:
        return "확인 필요"


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
              {e("온라인 가능" if bool(resource.get("online_available")) else "현장 확인 필요")}
              · 예상 {e(str(duration))}분
              {(" · " + e(contact)) if contact else ""}
            </div>
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
profile, analysis = current_profile_and_analysis()

st.markdown(
    """
    <div class="rr-app-header">
      <div class="rr-app-title">RebootRoute</div>
      <p class="rr-app-subtitle">오늘 가능한 작은 다음 행동을 고릅니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("last_action_message"):
    st.success(st.session_state.pop("last_action_message"))

tabs = st.tabs(["오늘 루트", "인천 자원", "운영자", "평가"])

with tabs[0]:
    input_col, result_col = st.columns([0.92, 1.28], gap="large")

    with input_col:
        st.subheader("내 상태")
        st.number_input("나이", min_value=19, max_value=39, key="age")
        st.selectbox("거주 구/군", DISTRICTS, key="district")
        st.selectbox("선호 접촉 방식", list(CONTACT_LABELS.keys()), format_func=lambda x: CONTACT_LABELS[x], key="preferred_contact_mode")
        st.multiselect("관심 태그", INTERESTS, format_func=lambda x: INTEREST_LABELS[x], key="interests")
        st.number_input("예산 한도", min_value=0, max_value=100000, step=5000, key="budget_limit")
        st.checkbox("도움을 줄 수 있는 사람이 있음", key="has_support_person")

        st.markdown('<div class="rr-divider"></div>', unsafe_allow_html=True)
        st.slider("미래 불안", 1, 5, key="future_anxiety")
        st.slider("취업 부담", 1, 5, key="employment_burden")
        st.slider("외출 부담", 1, 5, key="outside_burden")
        st.slider("대면 부담", 1, 5, key="social_burden")
        st.slider("에너지 수준", 1, 5, key="energy_level")
        st.slider("생활 리듬", 1, 5, key="daily_rhythm_level")
        st.slider("가능한 외출 시간", 0, 180, step=5, key="max_outdoor_minutes")
        st.text_area("자유 입력", key="free_text", height=130)
        st.button("샘플 상태로 초기화", width="stretch", on_click=reset_demo_state)

    with result_col:
        profile, analysis = current_profile_and_analysis()
        if analysis["safety_flag"]:
            render_safety_branch(analysis)
        else:
            stage = int(analysis["recommended_stage"])
            st.markdown(
                f"""
                <div class="rr-panel rr-stage-panel">
                  <div class="rr-section-title">지금 시작점: {e(STAGE_LABELS.get(stage, "확인 필요"))}</div>
                  <div class="rr-muted"><strong>{e(analysis["recommended_route_name"])}</strong><br/>{e(analysis["burden_summary"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.subheader("오늘 할 일")
            for idx, mission in enumerate(analysis["next_3_missions"]):
                render_user_mission(profile, mission, stage, f"primary_{idx}")

            st.subheader("함께 볼 인천 자원")
            for idx, resource in enumerate(analysis["recommended_resources"][:3]):
                render_user_resource(resource, f"primary_{idx}")

            mini_projects = analysis.get("mini_project_candidates", [])
            if mini_projects:
                st.subheader("미니 일경험 후보")
                for idx, candidate in enumerate(mini_projects[:3]):
                    with st.container(border=True):
                        st.markdown(
                            f"""
                            <div class="rr-card-title">{e(candidate["title"])}</div>
                            <div class="rr-card-body">{e(candidate["description"])}</div>
                            {chip("관심 기반", "teal")}
                            {chip("포트폴리오 씨앗", "gold")}
                            """,
                            unsafe_allow_html=True,
                        )

with tabs[1]:
    st.subheader("인천 자원 찾기")
    search_col, filter_col = st.columns([1.2, 0.8], gap="large")
    with search_col:
        st.text_input("검색 질문", key="rag_query")
    with filter_col:
        rag_district = st.selectbox("구/군 필터", ["현재 거주지", "전체"] + DISTRICTS, key="rag_district")
        rag_burden = st.slider("최대 부담도", 0, 5, 3, key="rag_max_burden")
    if st.button("근거 자료 검색", width="stretch"):
        district_value = profile.district if rag_district == "현재 거주지" else None if rag_district == "전체" else rag_district
        st.session_state["rag_result"] = search_policy_culture_resources(
            st.session_state["rag_query"],
            district=district_value,
            max_burden_level=rag_burden,
            top_k=5,
        )

    rag_result = st.session_state.get("rag_result")
    if rag_result:
        st.markdown(
            f"""
            <div class="rr-panel">
              <div class="rr-section-title">검색 답변</div>
              <div class="rr-muted">{e(rag_result["answer"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for idx, resource in enumerate(rag_result.get("sources", [])):
            render_user_resource(resource, f"rag_{idx}")

with tabs[2]:
    st.subheader("운영자·연구자")
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
    log_col1, log_col2 = st.columns(2)
    with log_col1:
        st.caption("feedback_events")
        st.dataframe(feedback_df.tail(20), width="stretch", hide_index=True)
    with log_col2:
        st.caption("progress_logs")
        st.dataframe(progress_df.tail(20), width="stretch", hide_index=True)

    with st.expander("Raw analyze_profile payload"):
        st.json(analysis)

with tabs[3]:
    st.subheader("평가·모델")
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
    st.warning(metadata.get("synthetic_label_warning_ko", "현재 label은 MVP 시연용 synthetic label입니다."))
