from __future__ import annotations

import html
import base64
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlencode

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

SRC_ROOT = Path(__file__).resolve().parents[2]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

ASSET_DIR = Path(__file__).resolve().parent / "assets"

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


st.set_page_config(page_title="RebootRoute", page_icon="RR", layout="wide", initial_sidebar_state="collapsed")


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


st.markdown(
    """
    <style>
      :root {
        --rr-bg: #eef3f7;
        --rr-surface: #ffffff;
        --rr-surface-2: #f6f9fc;
        --rr-ink: #142033;
        --rr-muted: #475569;
        --rr-soft: #64748b;
        --rr-line: #d4dce8;
        --rr-line-strong: #aebbc9;
        --rr-primary: #0b5cab;
        --rr-primary-strong: #063d78;
        --rr-primary-soft: #e6f0fb;
        --rr-info: #16746a;
        --rr-info-soft: #e8f5f2;
        --rr-warm: #9a5700;
        --rr-warm-soft: #fff4df;
        --rr-danger: #a33a32;
        --rr-danger-soft: #fff1ee;
        --rr-shadow: 0 10px 28px rgba(20, 32, 51, 0.08);
        --rr-shadow-soft: 0 5px 14px rgba(20, 32, 51, 0.06);
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
        padding-top: 0.8rem;
        padding-bottom: 2.2rem;
        max-width: 1120px;
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

      [data-testid="stSidebar"],
      [data-testid="stSidebarContent"],
      section[data-testid="stSidebar"] {
        background: var(--rr-surface) !important;
        color: var(--rr-ink) !important;
        border-right: 1px solid var(--rr-line) !important;
      }

      [data-testid="stSidebar"] *,
      [data-testid="stSidebarContent"] * {
        color: var(--rr-ink) !important;
      }

      [data-testid="stSidebar"] p,
      [data-testid="stSidebar"] .stCaption,
      [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: var(--rr-muted) !important;
      }

      [data-testid="stSidebarCollapsedControl"],
      [data-testid="collapsedControl"] {
        background: var(--rr-surface) !important;
        border: 1px solid var(--rr-line) !important;
        border-radius: 8px !important;
        color: var(--rr-ink) !important;
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
        border-radius: 8px !important;
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

      [data-baseweb="slider"] [role="slider"] {
        background: var(--rr-primary) !important;
        border-color: var(--rr-primary) !important;
        box-shadow: 0 0 0 2px #ffffff, 0 0 0 4px rgba(7, 86, 165, 0.2) !important;
      }

      [data-baseweb="slider"] [aria-valuenow] {
        background: var(--rr-primary) !important;
      }

      [data-baseweb="slider"] > div > div {
        background-color: #d8dee8 !important;
      }

      [data-baseweb="slider"] > div > div > div {
        background-color: var(--rr-primary) !important;
      }

      [data-testid="stNumberInput"] button,
      [data-testid="stNumberInput"] button:hover,
      [data-testid="stNumberInput"] button:focus {
        background: #f8fafc !important;
        color: var(--rr-primary) !important;
        border-color: var(--rr-line) !important;
      }

      [data-testid="stNumberInput"] button * {
        color: var(--rr-primary) !important;
      }

      [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--rr-surface) !important;
        border-color: var(--rr-line) !important;
        border-radius: 8px !important;
        box-shadow: var(--rr-shadow-soft) !important;
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
        min-height: 2.48rem;
        border-radius: 8px;
        border: 1px solid var(--rr-primary) !important;
        background: #ffffff !important;
        color: var(--rr-primary) !important;
        font-weight: 800 !important;
        line-height: 1.2 !important;
        white-space: normal !important;
        box-shadow: 0 2px 6px rgba(11, 92, 171, 0.08) !important;
      }

      .stButton > button * {
        color: inherit !important;
      }

      .stButton > button:hover,
      .stButton > button:focus {
        background: var(--rr-primary-soft) !important;
        border-color: var(--rr-primary-strong) !important;
        color: var(--rr-primary-strong) !important;
      }

      [data-testid="stBaseButton-primary"],
      .stFormSubmitButton > button {
        background: var(--rr-primary) !important;
        border-color: var(--rr-primary) !important;
        color: #ffffff !important;
      }

      [data-testid="stBaseButton-primary"] *,
      .stFormSubmitButton > button * {
        color: #ffffff !important;
      }

      [data-testid="stBaseButton-primary"]:hover,
      .stFormSubmitButton > button:hover {
        background: var(--rr-primary-strong) !important;
        border-color: var(--rr-primary-strong) !important;
        color: #ffffff !important;
      }

      [data-baseweb="tab-list"] {
        gap: 0.35rem;
        border-bottom: 1px solid var(--rr-line);
        padding-bottom: 0.28rem;
      }

      [data-baseweb="tab-highlight"] {
        background-color: var(--rr-primary) !important;
      }

      [data-baseweb="tab-border"] {
        background-color: var(--rr-line) !important;
      }

      [data-baseweb="tab"] {
        color: var(--rr-muted) !important;
        border-radius: 999px;
        padding: 0.58rem 0.92rem;
        min-width: max-content;
      }

      [data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        background: var(--rr-primary) !important;
        border: 1px solid var(--rr-primary);
        font-weight: 800;
      }

      [data-baseweb="tab"][aria-selected="true"] * {
        color: #ffffff !important;
      }

      [data-testid="stDataFrame"], [data-testid="stTable"] {
        color: var(--rr-ink) !important;
      }

      .rr-topbar {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        color: var(--rr-muted) !important;
        font-size: 0.78rem;
        line-height: 1.45;
        margin: 0 0 0.25rem;
      }

      .rr-app-header {
        background: #14324b;
        border: 1px solid #14324b;
        border-left: 6px solid #1fb39f;
        border-radius: 8px;
        padding: 0.82rem 0.95rem;
        margin-bottom: 0.62rem;
        box-shadow: var(--rr-shadow);
      }

      .rr-app-header,
      .rr-app-header * {
        color: #ffffff !important;
      }

      .rr-app-title {
        font-size: 1.42rem;
        line-height: 1.2;
        font-weight: 850;
        color: #ffffff !important;
        margin: 0 0 0.16rem 0;
      }

      .rr-app-subtitle {
        color: #d8e5ee !important;
        margin: 0;
        font-size: 0.9rem;
        line-height: 1.45;
      }

      .rr-header-grid {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 1rem;
        align-items: center;
      }

      .rr-header-badges {
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-end;
        gap: 0.35rem;
      }

      .rr-page-title {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        gap: 1rem;
        margin: 0.16rem 0 0.45rem;
      }

      .rr-page-title h2 {
        margin: 0 !important;
        font-size: 1.18rem !important;
      }

      .rr-page-title p {
        margin: 0.2rem 0 0;
        color: var(--rr-muted) !important;
        font-size: 0.86rem;
        line-height: 1.42;
      }

      .rr-panel {
        background: var(--rr-surface);
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 0.82rem;
        margin: 0.45rem 0;
        box-shadow: var(--rr-shadow-soft);
      }

      .rr-filter-panel {
        background: var(--rr-surface);
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
      }

      .rr-summary-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.5rem;
        margin: 0.5rem 0 0.65rem;
      }

      .rr-summary-item {
        background: #f8fafc;
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 0.54rem 0.62rem;
      }

      .rr-summary-item span {
        display: block;
        color: var(--rr-soft) !important;
        font-size: 0.76rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
      }

      .rr-summary-item strong {
        display: block;
        color: var(--rr-ink) !important;
        font-size: 0.92rem;
        line-height: 1.35;
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
        background: #ffffff;
        border-color: #9bc1eb;
        border-left: 6px solid var(--rr-primary);
      }

      .rr-primary-mission {
        margin-bottom: 0.55rem;
      }

      .rr-primary-mission .rr-card-title {
        font-size: 1.1rem;
      }

      .rr-section-title {
        color: var(--rr-ink) !important;
        font-size: 0.98rem;
        font-weight: 800;
        margin-bottom: 0.34rem;
      }

      .rr-muted {
        color: var(--rr-muted) !important;
        font-size: 0.92rem;
        line-height: 1.6;
      }

      .rr-chip {
        display: inline-block;
        padding: 0.18rem 0.52rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 780;
        margin: 0 0.25rem 0.25rem 0;
        border: 1px solid transparent;
      }

      .rr-chip.teal { background: var(--rr-primary-soft); color: var(--rr-primary-strong) !important; border-color: #b8d3f0; }
      .rr-chip.blue { background: var(--rr-info-soft); color: var(--rr-info) !important; border-color: #b9ddd7; }
      .rr-chip.gold { background: var(--rr-warm-soft); color: var(--rr-warm) !important; border-color: #f0c894; }
      .rr-chip.gray { background: #edf2f4; color: #3f4e5f !important; border-color: #d4dde1; }
      .rr-chip.rose { background: var(--rr-danger-soft); color: var(--rr-danger) !important; border-color: #f2c2bd; }

      .rr-card-title {
        font-size: 0.98rem;
        font-weight: 800;
        color: var(--rr-ink) !important;
        margin-bottom: 0.28rem;
        line-height: 1.35;
      }

      .rr-card-body {
        color: var(--rr-muted) !important;
        font-size: 0.9rem;
        line-height: 1.5;
        margin-bottom: 0.45rem;
      }

      .rr-resource-card {
        background: var(--rr-surface);
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 0.82rem;
        margin: 0.55rem 0;
      }

      .rr-info-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.55rem;
        margin: 0.65rem 0;
      }

      .rr-info-item {
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 0.55rem 0.6rem;
        background: #f8fafc;
        min-height: 3.25rem;
      }

      .rr-info-item span {
        display: block;
        color: var(--rr-soft) !important;
        font-size: 0.72rem;
        font-weight: 750;
        margin-bottom: 0.18rem;
      }

      .rr-info-item strong {
        color: var(--rr-ink) !important;
        font-size: 0.86rem;
        line-height: 1.3;
      }

      .rr-next-action {
        background: var(--rr-warm-soft);
        border: 1px solid #f0d29a;
        border-left: 6px solid #c47700;
        border-radius: 8px;
        padding: 0.78rem;
        margin: 0.5rem 0;
        box-shadow: var(--rr-shadow-soft);
      }

      .rr-route-strip {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.4rem;
        margin: 0.12rem 0 0.58rem;
        color: var(--rr-muted) !important;
        font-size: 0.84rem;
        font-weight: 700;
      }

      .rr-route-strip span {
        background: #ffffff;
        border: 1px solid var(--rr-line);
        border-radius: 999px;
        padding: 0.22rem 0.55rem;
        color: var(--rr-ink) !important;
        box-shadow: 0 1px 4px rgba(20, 32, 51, 0.05);
      }

      .rr-control-note {
        color: var(--rr-muted) !important;
        font-size: 0.82rem;
        line-height: 1.4;
        margin: -0.15rem 0 0.4rem;
      }

      .rr-condition-bar {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.5rem;
        margin: 0.1rem 0 0.45rem;
      }

      .rr-condition-pill {
        background: var(--rr-surface-2);
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 0.5rem 0.58rem;
      }

      .rr-condition-pill span {
        display: block;
        color: var(--rr-soft) !important;
        font-size: 0.72rem;
        font-weight: 750;
        margin-bottom: 0.12rem;
      }

      .rr-condition-pill strong {
        display: block;
        color: var(--rr-ink) !important;
        font-size: 0.9rem;
        line-height: 1.25;
      }

      .rr-featured-resource {
        background: #ffffff;
        border: 1px solid #b9ddd7;
        border-left: 6px solid var(--rr-info);
        border-radius: 8px;
        padding: 0.82rem;
        margin: 0.5rem 0;
        box-shadow: var(--rr-shadow-soft);
      }

      .rr-featured-resource .rr-info-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        margin-bottom: 0.35rem;
      }

      .rr-compact-list {
        margin: 0.45rem 0 0;
        padding-left: 1rem;
      }

      .rr-compact-list li {
        color: var(--rr-ink) !important;
        margin: 0.25rem 0;
        line-height: 1.42;
        font-size: 0.9rem;
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
        border: 1px solid #b9ddd7;
        background: var(--rr-info-soft);
        color: #0f5f57 !important;
        border-radius: 8px;
        padding: 0.36rem 0.58rem;
        text-decoration: none !important;
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
        background: #ffffff;
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
        height: 360px;
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
          padding: 0.72rem;
        }

        .rr-app-title {
          font-size: 1.24rem;
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

        .rr-header-grid,
        .rr-page-title,
        .rr-featured-resource .rr-info-grid,
        .rr-condition-bar,
        .rr-summary-grid,
        .rr-info-grid {
          grid-template-columns: 1fr;
        }

        .rr-condition-bar {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .rr-header-badges {
          justify-content: flex-start;
        }

        .rr-map {
          height: 320px;
        }

        .rr-map-label {
          max-width: 8.5rem;
          font-size: 0.7rem;
        }
      }

      .block-container {
        max-width: 1280px;
        padding-top: 0.45rem;
      }

      .rr-app-header {
        background: #ffffff !important;
        border: 1px solid var(--rr-line) !important;
        border-top: 5px solid var(--rr-primary) !important;
        border-left: 1px solid var(--rr-line) !important;
        padding: 0.78rem 0.95rem !important;
        margin-bottom: 0.48rem !important;
      }

      .rr-app-header,
      .rr-app-header * {
        color: var(--rr-ink) !important;
      }

      .rr-app-subtitle {
        color: var(--rr-muted) !important;
      }

      .rr-topbar {
        margin-top: 0;
        font-weight: 750;
      }

      .rr-route-strip {
        margin: 0.2rem 0 0.45rem;
      }

      .rr-flow-compact {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.45rem;
        margin: 0.4rem 0 0.58rem;
      }

      .rr-flow-compact div {
        background: #ffffff;
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 0.48rem 0.58rem;
        min-height: 3.2rem;
      }

      .rr-flow-compact strong {
        display: block;
        color: var(--rr-ink) !important;
        font-size: 0.86rem;
        line-height: 1.25;
      }

      .rr-flow-compact span {
        color: var(--rr-muted) !important;
        font-size: 0.78rem;
        line-height: 1.3;
      }

      .rr-data-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        align-items: center;
        margin: 0.25rem 0 0.55rem;
      }

      .rr-data-strip span {
        border: 1px solid #b9ddd7;
        background: #f1faf8;
        color: #0f5f57 !important;
        border-radius: 999px;
        padding: 0.24rem 0.55rem;
        font-size: 0.78rem;
        font-weight: 800;
      }

      .rr-control-card {
        background: #ffffff;
        border: 1px solid var(--rr-line);
        border-radius: 8px;
        padding: 0.78rem;
        box-shadow: var(--rr-shadow-soft);
      }

      .rr-control-card .rr-section-title {
        margin-bottom: 0.15rem;
      }

      .rr-control-card [data-testid="stWidgetLabel"] p {
        font-size: 0.78rem !important;
        font-weight: 800 !important;
      }

      .rr-card-with-media {
        display: grid;
        grid-template-columns: 150px minmax(0, 1fr);
        gap: 0.72rem;
        align-items: stretch;
      }

      .rr-featured-resource .rr-card-with-media {
        grid-template-columns: 175px minmax(0, 1fr);
      }

      .rr-resource-thumb {
        width: 100%;
        height: 100%;
        min-height: 132px;
        max-height: 182px;
        object-fit: cover;
        border-radius: 7px;
        border: 1px solid var(--rr-line);
        background: #f8fafc;
      }

      .rr-proof {
        margin-top: 0.38rem;
        color: #334155 !important;
        font-size: 0.78rem;
        line-height: 1.4;
      }

      .rr-proof strong {
        color: #0f172a !important;
      }

      .rr-featured-resource,
      .rr-resource-card,
      .rr-next-action,
      .rr-panel {
        padding: 0.7rem !important;
        margin: 0.38rem 0 !important;
      }

      .rr-info-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.42rem;
        margin: 0.48rem 0;
      }

      .rr-info-item {
        min-height: 2.7rem;
        padding: 0.42rem 0.5rem;
      }

      .rr-map {
        height: 255px;
      }

      .rr-map-label {
        max-width: 9.4rem;
      }

      .rr-inline-card-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.55rem;
        margin-top: 0.4rem;
      }

      .rr-source-link {
        padding: 0.32rem 0.52rem;
      }

      @media (max-width: 760px) {
        .block-container {
          padding: 0.55rem 0.72rem 1.5rem;
        }

        .rr-flow-compact {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .rr-card-with-media,
        .rr-featured-resource .rr-card-with-media,
        .rr-inline-card-grid {
          grid-template-columns: 1fr;
        }

        .rr-resource-thumb {
          min-height: 138px;
          max-height: 180px;
        }

        .rr-map {
          height: 230px;
        }

        .rr-data-strip span {
          font-size: 0.74rem;
        }
      }

      /* 2026 mobile-app redesign layer */
      :root {
        --rr-bg: #f5f7fb;
        --rr-surface: #ffffff;
        --rr-surface-raised: rgba(255, 255, 255, 0.82);
        --rr-ink: #111827;
        --rr-muted: #667085;
        --rr-soft: #8a94a6;
        --rr-line: #dce3ee;
        --rr-primary: #2563eb;
        --rr-primary-strong: #1d4ed8;
        --rr-primary-soft: #e9efff;
        --rr-info: #14b8a6;
        --rr-info-soft: #e7fbf7;
        --rr-action: #f97316;
        --rr-action-soft: #fff1e7;
        --rr-danger: #dc2626;
        --rr-danger-soft: #fff1f2;
        --rr-radius-xl: 18px;
        --rr-radius-lg: 16px;
        --rr-radius-md: 12px;
        --rr-glass: rgba(255, 255, 255, 0.72);
        --rr-shadow: 0 18px 48px rgba(15, 23, 42, 0.12);
        --rr-shadow-soft: 0 8px 22px rgba(15, 23, 42, 0.08);
      }

      @media (prefers-color-scheme: dark) {
        :root {
          --rr-bg: #0b1020;
          --rr-surface: #111827;
          --rr-surface-raised: rgba(17, 24, 39, 0.82);
          --rr-ink: #f8fafc;
          --rr-muted: #cbd5e1;
          --rr-soft: #94a3b8;
          --rr-line: #273449;
          --rr-primary: #60a5fa;
          --rr-primary-strong: #93c5fd;
          --rr-primary-soft: rgba(96, 165, 250, 0.18);
          --rr-info: #2dd4bf;
          --rr-info-soft: rgba(45, 212, 191, 0.14);
          --rr-action: #fb7185;
          --rr-action-soft: rgba(251, 113, 133, 0.14);
          --rr-danger: #fca5a5;
          --rr-danger-soft: rgba(252, 165, 165, 0.14);
          --rr-glass: rgba(17, 24, 39, 0.68);
          --rr-shadow: 0 18px 48px rgba(0, 0, 0, 0.36);
          --rr-shadow-soft: 0 8px 22px rgba(0, 0, 0, 0.22);
        }
      }

      .stApp,
      [data-testid="stAppViewContainer"],
      [data-testid="stMain"],
      [data-testid="stMainBlockContainer"],
      section.main {
        background:
          radial-gradient(circle at 18% 0%, rgba(37, 99, 235, 0.12), transparent 28rem),
          radial-gradient(circle at 100% 18%, rgba(20, 184, 166, 0.13), transparent 24rem),
          var(--rr-bg) !important;
      }

      #MainMenu,
      footer,
      [data-testid="stToolbar"],
      [data-testid="stDecoration"] {
        display: none !important;
      }

      .block-container {
        max-width: 1180px !important;
        padding: 0.42rem 1.05rem 5.4rem !important;
      }

      [data-testid="stVerticalBlock"] {
        gap: 0.58rem !important;
      }

      .rr-topbar,
      .rr-app-header,
      .rr-page-title,
      .rr-flow-compact,
      .rr-data-strip,
      .rr-control-card {
        display: none !important;
      }

      .rr-app-shell {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.9rem;
        margin: 0.1rem 0 0.5rem;
      }

      .rr-brand-lockup {
        display: flex;
        flex-direction: column;
        gap: 0.05rem;
      }

      .rr-brand-name {
        color: var(--rr-ink) !important;
        font-size: 1.08rem;
        font-weight: 900;
        line-height: 1.1;
      }

      .rr-brand-sub {
        color: var(--rr-muted) !important;
        font-size: 0.78rem;
        font-weight: 760;
        line-height: 1.35;
      }

      .rr-session-pill {
        display: inline-flex;
        align-items: center;
        border: 1px solid var(--rr-line);
        background: var(--rr-glass);
        color: var(--rr-ink) !important;
        backdrop-filter: blur(18px) saturate(1.2);
        border-radius: 999px;
        padding: 0.38rem 0.68rem;
        font-size: 0.78rem;
        font-weight: 850;
        box-shadow: var(--rr-shadow-soft);
      }

      [data-baseweb="tab-list"] {
        gap: 0.35rem !important;
        border-bottom: 0 !important;
        margin-bottom: 0.45rem;
        padding: 0.24rem !important;
        border-radius: 999px;
        background: color-mix(in srgb, var(--rr-surface) 88%, transparent);
        box-shadow: inset 0 0 0 1px var(--rr-line);
      }

      [data-baseweb="tab"] {
        border-radius: 999px !important;
        min-height: 2.35rem !important;
        padding: 0.54rem 0.9rem !important;
        font-weight: 850 !important;
        color: var(--rr-muted) !important;
        transition: background 180ms ease, color 180ms ease, transform 180ms ease;
      }

      [data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        background: linear-gradient(135deg, var(--rr-primary), var(--rr-info)) !important;
        border: 0 !important;
        box-shadow: 0 8px 18px rgba(37, 99, 235, 0.24);
      }

      [data-baseweb="tab-highlight"],
      [data-baseweb="tab-border"] {
        display: none !important;
      }

      .rr-route-hero {
        position: relative;
        overflow: hidden;
        border: 1px solid color-mix(in srgb, var(--rr-primary) 18%, var(--rr-line));
        border-radius: 20px;
        background:
          linear-gradient(135deg, rgba(37, 99, 235, 0.15), rgba(20, 184, 166, 0.08) 42%, rgba(249, 115, 22, 0.1)),
          var(--rr-surface);
        padding: 0.74rem 0.86rem;
        box-shadow: var(--rr-shadow);
        margin-bottom: 0.38rem;
      }

      .rr-route-hero::after {
        content: "";
        position: absolute;
        inset: auto -4rem -5rem auto;
        width: 12rem;
        height: 12rem;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.12);
        filter: blur(28px);
        pointer-events: none;
      }

      .rr-hero-kicker {
        color: var(--rr-primary-strong) !important;
        font-size: 0.76rem;
        font-weight: 900;
        letter-spacing: 0;
        margin-bottom: 0.16rem;
      }

      .rr-hero-title {
        color: var(--rr-ink) !important;
        font-size: 1.38rem;
        font-weight: 950;
        line-height: 1.15;
        margin-bottom: 0.22rem;
      }

      .rr-hero-copy {
        max-width: 42rem;
        color: var(--rr-muted) !important;
        font-size: 0.86rem;
        font-weight: 680;
        line-height: 1.48;
        margin: 0;
      }

      .rr-choice-row {
        margin-top: 0.26rem;
      }

      .rr-choice-label {
        color: var(--rr-ink) !important;
        font-size: 0.82rem;
        font-weight: 900;
        line-height: 1.25;
        margin-bottom: 0.36rem;
      }

      .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: var(--rr-radius-lg) !important;
        border-color: color-mix(in srgb, var(--rr-line) 82%, transparent) !important;
        background: var(--rr-glass) !important;
        box-shadow: var(--rr-shadow-soft) !important;
        backdrop-filter: blur(18px) saturate(1.12);
        padding: 0.08rem !important;
      }

      .stButton > button {
        border-radius: 999px !important;
        min-height: 2.24rem !important;
        border: 1px solid var(--rr-line) !important;
        background: color-mix(in srgb, var(--rr-surface) 92%, transparent) !important;
        color: var(--rr-ink) !important;
        font-weight: 900 !important;
        transition: transform 160ms ease, box-shadow 180ms ease, border-color 180ms ease, background 180ms ease;
      }

      .stButton > button p,
      .stButton > button span {
        color: var(--rr-ink) !important;
      }

      .stButton > button:hover {
        transform: translateY(-1px);
        border-color: var(--rr-primary) !important;
        box-shadow: 0 8px 18px rgba(37, 99, 235, 0.12);
      }

      [data-testid="stSegmentedControl"] {
        width: 100% !important;
      }

      [data-testid="stSegmentedControl"] > div {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 0.35rem !important;
        width: 100% !important;
      }

      [data-testid="stSegmentedControl"] button {
        border-radius: 999px !important;
        min-height: 2.24rem !important;
        border: 1px solid var(--rr-line) !important;
        background: color-mix(in srgb, var(--rr-surface) 92%, transparent) !important;
        color: var(--rr-ink) !important;
        font-weight: 900 !important;
        transition: transform 160ms ease, box-shadow 180ms ease, border-color 180ms ease, background 180ms ease;
      }

      [data-testid="stSegmentedControl"] button p,
      [data-testid="stSegmentedControl"] button span {
        color: var(--rr-ink) !important;
      }

      [data-testid="stSegmentedControl"] button:hover {
        transform: translateY(-1px);
        border-color: var(--rr-primary) !important;
      }

      [data-testid="stSegmentedControl"] button[aria-pressed="true"],
      [data-testid="stSegmentedControl"] button[aria-checked="true"],
      [data-testid="stSegmentedControl"] button[data-selected="true"] {
        background: linear-gradient(135deg, var(--rr-primary), var(--rr-info)) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
      }

      [data-testid="stSegmentedControl"] button[aria-pressed="true"] p,
      [data-testid="stSegmentedControl"] button[aria-pressed="true"] span,
      [data-testid="stSegmentedControl"] button[aria-checked="true"] p,
      [data-testid="stSegmentedControl"] button[aria-checked="true"] span,
      [data-testid="stSegmentedControl"] button[data-selected="true"] p,
      [data-testid="stSegmentedControl"] button[data-selected="true"] span {
        color: #ffffff !important;
      }

      [data-testid="stBaseButton-segmented_control"] {
        border-radius: 999px !important;
        border: 1px solid var(--rr-line) !important;
        background: color-mix(in srgb, var(--rr-surface) 92%, transparent) !important;
        color: var(--rr-ink) !important;
        font-weight: 900 !important;
      }

      [data-testid="stBaseButton-segmented_control"] *,
      [data-testid="stBaseButton-segmented_control"] p,
      [data-testid="stBaseButton-segmented_control"] span {
        color: var(--rr-ink) !important;
      }

      [data-testid="stBaseButton-segmented_controlActive"] {
        border-radius: 999px !important;
        border: 1px solid transparent !important;
        background: linear-gradient(135deg, var(--rr-primary), var(--rr-info)) !important;
        color: #ffffff !important;
        font-weight: 950 !important;
        box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
      }

      [data-testid="stBaseButton-segmented_controlActive"] *,
      [data-testid="stBaseButton-segmented_controlActive"] p,
      [data-testid="stBaseButton-segmented_controlActive"] span {
        color: #ffffff !important;
      }

      [data-testid="stBaseButton-primary"],
      button[kind="primary"] {
        background: linear-gradient(135deg, var(--rr-primary), var(--rr-info)) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
      }

      [data-testid="stBaseButton-primary"] p,
      [data-testid="stBaseButton-primary"] span,
      button[kind="primary"] p,
      button[kind="primary"] span {
        color: #ffffff !important;
      }

      .rr-bento-row {
        margin-top: 0.62rem;
      }

      .rr-bento-card {
        position: relative;
        overflow: hidden;
        border: 1px solid var(--rr-line);
        border-radius: var(--rr-radius-xl);
        background: var(--rr-surface);
        padding: 0.78rem;
        box-shadow: var(--rr-shadow-soft);
      }

      .rr-bento-card.mission {
        min-height: 14.6rem;
        background:
          linear-gradient(160deg, rgba(37, 99, 235, 0.11), transparent 52%),
          var(--rr-surface);
      }

      .rr-bento-card.resource {
        min-height: 7.9rem;
        background:
          linear-gradient(145deg, rgba(20, 184, 166, 0.11), transparent 54%),
          var(--rr-surface);
      }

      .rr-bento-card.map {
        min-height: 10rem;
        padding: 0.62rem;
        margin-top: 0;
      }

      .rr-card-eyebrow {
        color: var(--rr-soft) !important;
        font-size: 0.73rem;
        font-weight: 920;
        margin-bottom: 0.25rem;
      }

      .rr-bento-title {
        color: var(--rr-ink) !important;
        font-size: 1.1rem;
        font-weight: 950;
        line-height: 1.22;
        margin-bottom: 0.34rem;
      }

      .rr-bento-card.resource .rr-bento-title {
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        overflow: hidden;
        font-size: 1rem;
        margin-bottom: 0.26rem;
      }

      .rr-bento-body {
        color: var(--rr-muted) !important;
        font-size: 0.85rem;
        line-height: 1.44;
        margin-bottom: 0.48rem;
      }

      .rr-bento-card.resource .rr-bento-body {
        display: none;
      }

      .rr-mini-facts {
        display: flex;
        flex-wrap: wrap;
        gap: 0.3rem;
        margin-top: 0.42rem;
      }

      .rr-mini-fact {
        display: inline-flex;
        align-items: center;
        min-height: 2rem;
        border-radius: 999px;
        border: 1px solid var(--rr-line);
        background: color-mix(in srgb, var(--rr-surface) 88%, transparent);
        color: var(--rr-ink) !important;
        padding: 0.24rem 0.58rem;
        font-size: 0.78rem;
        font-weight: 860;
      }

      .rr-resource-layout {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 0.54rem;
        align-items: stretch;
      }

      .rr-resource-art {
        width: 100%;
        height: 5.2rem;
        min-height: 5.2rem;
        border-radius: var(--rr-radius-lg);
        object-fit: cover;
        border: 1px solid var(--rr-line);
        background: var(--rr-primary-soft);
      }

      .rr-official-line {
        color: var(--rr-soft) !important;
        font-size: 0.76rem;
        font-weight: 760;
        line-height: 1.36;
        margin-top: 0.28rem;
      }

      .rr-map.compact {
        height: 7.2rem;
        border-radius: var(--rr-radius-lg);
        margin-top: 0.38rem;
      }

      .rr-map.expanded {
        height: 20rem;
        border-radius: var(--rr-radius-xl);
      }

      .rr-map.compact .rr-map-label {
        display: none;
      }

      .rr-action-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.44rem;
        margin-top: 0.62rem;
      }

      .rr-action-row .stButton > button,
      .rr-floating-action .stButton > button,
      .st-key-route_action_bar .stButton > button {
        border-radius: 999px !important;
        min-height: 2.7rem !important;
        font-weight: 920 !important;
        transition: transform 160ms ease, box-shadow 180ms ease, background 180ms ease;
      }

      .rr-action-row .stButton > button:hover,
      .rr-floating-action .stButton > button:hover,
      .st-key-route_action_bar .stButton > button:hover {
        transform: translateY(-1px);
      }

      .st-key-route_action_bar {
        position: fixed;
        left: max(1rem, calc((100vw - 1180px) / 2 + 1rem));
        right: max(1rem, calc((100vw - 1180px) / 2 + 1rem));
        bottom: 0.36rem;
        z-index: 20;
        margin-top: 0.72rem;
        padding: 0.34rem;
        width: auto !important;
        max-width: calc(100vw - 2rem) !important;
        box-sizing: border-box !important;
        border: 1px solid color-mix(in srgb, var(--rr-primary) 18%, var(--rr-line));
        border-radius: 999px;
        background: var(--rr-glass);
        backdrop-filter: blur(22px) saturate(1.18);
        box-shadow: var(--rr-shadow);
      }

      .rr-floating-action {
        position: sticky;
        bottom: 0.7rem;
        z-index: 20;
        display: grid;
        grid-template-columns: minmax(0, 1.3fr) minmax(0, 0.85fr) minmax(0, 0.85fr) minmax(0, 0.85fr);
        gap: 0.46rem;
        margin-top: 0.8rem;
        padding: 0.5rem;
        border: 1px solid color-mix(in srgb, var(--rr-primary) 18%, var(--rr-line));
        border-radius: 999px;
        background: var(--rr-glass);
        backdrop-filter: blur(22px) saturate(1.18);
        box-shadow: var(--rr-shadow);
      }

      .rr-floating-action [data-testid="stBaseButton-primary"],
      .st-key-route_action_bar [data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, var(--rr-action), var(--rr-primary)) !important;
        border: 0 !important;
      }

      .st-key-route_action_bar .stButton > button {
        min-height: 2.36rem !important;
      }

      .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: minmax(0, 1.35fr) repeat(3, minmax(0, 0.85fr)) !important;
        gap: 0.46rem !important;
      }

      .st-key-route_action_bar [data-testid="column"] {
        width: 100% !important;
        min-width: 0 !important;
      }

      .rr-progressive-panel {
        border: 1px solid var(--rr-line);
        border-radius: var(--rr-radius-xl);
        background: var(--rr-surface);
        padding: 0.78rem;
        margin-top: 0.62rem;
        box-shadow: var(--rr-shadow-soft);
      }

      .rr-compact-controls {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.48rem;
      }

      .rr-compact-controls [data-testid="stWidgetLabel"] p {
        font-size: 0.75rem !important;
        font-weight: 850 !important;
        color: var(--rr-muted) !important;
      }

      .rr-history-list {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.62rem;
      }

      .rr-history-card {
        border: 1px solid var(--rr-line);
        border-radius: var(--rr-radius-lg);
        background: var(--rr-surface);
        padding: 0.78rem;
        box-shadow: var(--rr-shadow-soft);
      }

      .rr-history-card strong {
        display: block;
        color: var(--rr-ink) !important;
        font-size: 0.94rem;
        line-height: 1.35;
        margin-bottom: 0.18rem;
      }

      .rr-history-card span {
        color: var(--rr-muted) !important;
        font-size: 0.82rem;
        line-height: 1.45;
      }

      @media (prefers-color-scheme: dark) {
        .rr-route-hero,
        .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"],
        .rr-bento-card,
        .rr-progressive-panel,
        .rr-history-card,
        .rr-resource-card,
        .rr-panel {
          background-color: var(--rr-surface) !important;
        }

        .rr-map {
          background:
            linear-gradient(90deg, rgba(96, 165, 250, 0.12) 1px, transparent 1px),
            linear-gradient(rgba(96, 165, 250, 0.12) 1px, transparent 1px),
            linear-gradient(135deg, #101827 0%, #111827 50%, #0f172a 100%) !important;
        }

        .rr-map-label {
          background: rgba(15, 23, 42, 0.92) !important;
        }
      }

      @media (max-width: 860px) {
        .block-container {
          padding: 0.42rem 0.72rem 5.5rem !important;
        }

        .rr-app-shell {
          align-items: flex-start;
        }

        .rr-session-pill {
          display: none;
        }

        .rr-route-hero {
          border-radius: 18px;
          padding: 0.68rem;
        }

        .rr-hero-title {
          font-size: 1.18rem;
        }

        .rr-hero-copy {
          font-size: 0.86rem;
        }

        .rr-choice-row {
          margin-top: 0.48rem;
        }

        .rr-bento-card {
          border-radius: 18px;
          padding: 0.76rem;
        }

        .rr-bento-card.mission {
          min-height: auto;
        }

        .rr-resource-art {
          min-height: 5.8rem;
        }

        .rr-compact-controls {
          grid-template-columns: 1fr 1fr;
        }

        .rr-history-list {
          grid-template-columns: 1fr;
        }

        .rr-floating-action,
        .st-key-route_action_bar {
          border-radius: 24px;
        }

        .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
          grid-template-columns: 1fr 1fr !important;
          gap: 0.34rem !important;
        }

        .rr-floating-action > div:nth-child(3),
        .rr-floating-action > div:nth-child(4) {
          grid-column: span 1;
        }
      }

      @media (max-width: 430px) {
        [data-testid="stVerticalBlock"] {
          gap: 0.42rem !important;
        }

        .rr-app-shell {
          margin-bottom: 0.14rem;
        }

        .rr-brand-name {
          font-size: 0.98rem;
        }

        .rr-brand-sub {
          font-size: 0.72rem;
        }

        [data-baseweb="tab"] {
          padding: 0.48rem 0.62rem !important;
          min-height: 2.1rem !important;
          font-size: 0.82rem !important;
        }

        [data-baseweb="tab-list"] {
          margin-bottom: 0.22rem;
        }

        .rr-route-hero {
          padding: 0.56rem 0.64rem;
          margin-bottom: 0.1rem;
        }

        .rr-hero-kicker {
          font-size: 0.68rem;
          margin-bottom: 0.08rem;
        }

        .rr-hero-title {
          font-size: 1.06rem;
          margin-bottom: 0.1rem;
        }

        .rr-hero-copy {
          font-size: 0.78rem;
          line-height: 1.34;
        }

        .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"] {
          padding: 0 !important;
        }

        .rr-choice-label {
          margin-bottom: 0.22rem;
          font-size: 0.76rem;
        }

        .stButton > button {
          min-height: 2rem !important;
          font-size: 0.78rem !important;
          padding: 0.28rem 0.52rem !important;
        }

        [data-testid="stBaseButton-segmented_control"],
        [data-testid="stBaseButton-segmented_controlActive"] {
          min-height: 1.86rem !important;
          padding: 0.2rem 0.42rem !important;
          font-size: 0.74rem !important;
        }

        .rr-bento-title {
          font-size: 1.08rem;
        }

        .rr-bento-body {
          font-size: 0.84rem;
          line-height: 1.45;
        }

        .rr-resource-layout {
          grid-template-columns: 4.8rem minmax(0, 1fr);
          align-items: center;
        }

        .rr-resource-art {
          height: 5.2rem;
          min-height: 5.2rem;
        }

        .rr-bento-card.resource .rr-bento-title {
          font-size: 0.92rem;
        }

        .rr-bento-card.resource .rr-source-link {
          display: none;
        }

        .rr-mini-facts {
          gap: 0.28rem;
        }

        .rr-mini-fact {
          min-height: 1.8rem;
          font-size: 0.72rem;
          padding: 0.2rem 0.44rem;
        }

        .rr-floating-action,
        .st-key-route_action_bar {
          bottom: 0.5rem;
          padding: 0.38rem;
          gap: 0.34rem;
        }

        .rr-floating-action .stButton > button,
        .st-key-route_action_bar .stButton > button {
          min-height: 2.42rem !important;
          font-size: 0.8rem !important;
        }

        .st-key-route_action_bar {
          padding: 0.28rem;
        }

        .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
          grid-template-columns: minmax(0, 1.35fr) repeat(3, minmax(0, 0.9fr)) !important;
          gap: 0.28rem !important;
        }

        .st-key-route_action_bar .stButton > button {
          min-height: 2.22rem !important;
          font-size: 0.69rem !important;
          padding: 0.16rem 0.2rem !important;
        }
      }

      /* final readability and flow correction */
      :root {
        --rr-bg: #f6f8fc;
        --rr-surface: #ffffff;
        --rr-surface-raised: #ffffff;
        --rr-ink: #111827;
        --rr-muted: #4b5563;
        --rr-soft: #64748b;
        --rr-line: #d7deea;
        --rr-primary: #1d4ed8;
        --rr-primary-strong: #1e40af;
        --rr-primary-soft: #e8f0ff;
        --rr-info: #0f766e;
        --rr-info-soft: #e7f7f4;
        --rr-action: #c2410c;
        --rr-action-soft: #fff1e7;
        --rr-glass: #ffffff;
        --rr-shadow: 0 14px 34px rgba(15, 23, 42, 0.10);
        --rr-shadow-soft: 0 6px 18px rgba(15, 23, 42, 0.08);
      }

      @media (prefers-color-scheme: dark) {
        :root {
          --rr-bg: #0f172a;
          --rr-surface: #182235;
          --rr-surface-raised: #1f2937;
          --rr-ink: #f8fafc;
          --rr-muted: #d1d5db;
          --rr-soft: #b6c2d3;
          --rr-line: #3b4a60;
          --rr-primary: #7dd3fc;
          --rr-primary-strong: #bae6fd;
          --rr-primary-soft: rgba(125, 211, 252, 0.18);
          --rr-info: #5eead4;
          --rr-info-soft: rgba(94, 234, 212, 0.16);
          --rr-action: #fb923c;
          --rr-action-soft: rgba(251, 146, 60, 0.18);
          --rr-glass: #182235;
          --rr-shadow: 0 16px 38px rgba(0, 0, 0, 0.32);
          --rr-shadow-soft: 0 8px 22px rgba(0, 0, 0, 0.24);
        }
      }

      .stApp,
      [data-testid="stAppViewContainer"],
      [data-testid="stMain"],
      [data-testid="stMainBlockContainer"],
      section.main {
        background: var(--rr-bg) !important;
      }

      .block-container {
        max-width: 1100px !important;
        padding: 0.72rem 1rem 1.4rem !important;
      }

      [data-testid="stVerticalBlock"] {
        gap: 0.48rem !important;
      }

      .rr-app-shell {
        margin: 0 0 0.46rem !important;
      }

      .rr-brand-name {
        font-size: 1.18rem !important;
      }

      .rr-brand-sub,
      .rr-session-pill {
        color: var(--rr-muted) !important;
      }

      [data-baseweb="tab-list"] {
        background: var(--rr-surface) !important;
        border: 1px solid var(--rr-line) !important;
        box-shadow: var(--rr-shadow-soft) !important;
        padding: 0.22rem !important;
        margin-bottom: 0.58rem !important;
      }

      [data-baseweb="tab"] {
        color: var(--rr-muted) !important;
        font-size: 0.92rem !important;
      }

      [data-baseweb="tab"][aria-selected="true"] {
        background: var(--rr-primary) !important;
        color: #ffffff !important;
        box-shadow: none !important;
      }

      .rr-route-hero {
        display: grid !important;
        grid-template-columns: minmax(0, 1fr) minmax(18rem, 0.9fr) !important;
        column-gap: 0.8rem !important;
        align-items: center !important;
        border-radius: 18px !important;
        background: var(--rr-surface) !important;
        border: 1px solid var(--rr-line) !important;
        box-shadow: var(--rr-shadow-soft) !important;
        padding: 0.68rem 0.82rem !important;
        margin-bottom: 0.58rem !important;
      }

      .rr-hero-kicker,
      .rr-hero-title,
      .rr-hero-copy {
        grid-column: 1 !important;
        word-break: keep-all !important;
      }

      .rr-use-guide {
        grid-column: 2 !important;
        grid-row: 1 / span 3 !important;
      }

      .rr-route-hero::after {
        display: none !important;
      }

      .rr-hero-kicker {
        color: var(--rr-primary-strong) !important;
      }

      .rr-hero-title {
        color: var(--rr-ink) !important;
        font-size: 1.32rem !important;
      }

      .rr-hero-copy {
        color: var(--rr-muted) !important;
        font-size: 0.9rem !important;
      }

      .rr-use-guide {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.42rem;
        margin-top: 0;
      }

      .rr-use-guide span {
        display: flex;
        align-items: center;
        gap: 0.38rem;
        border: 1px solid var(--rr-line);
        border-radius: 999px;
        background: var(--rr-surface-raised);
        color: var(--rr-ink) !important;
        padding: 0.36rem 0.52rem;
        font-size: 0.8rem;
        font-weight: 850;
        white-space: nowrap;
      }

      .rr-use-guide b {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 1.35rem;
        height: 1.35rem;
        border-radius: 999px;
        background: var(--rr-primary);
        color: #ffffff !important;
        font-size: 0.75rem;
      }

      .rr-choice-row {
        margin-top: 0 !important;
      }

      .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"],
      .rr-bento-card,
      .rr-progressive-panel,
      .rr-history-card,
      .rr-resource-card,
      .rr-panel {
        background: var(--rr-surface) !important;
        border: 1px solid var(--rr-line) !important;
        border-radius: 16px !important;
        box-shadow: var(--rr-shadow-soft) !important;
      }

      .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.28rem !important;
      }

      .rr-choice-label {
        color: var(--rr-ink) !important;
        font-size: 0.84rem !important;
        margin-bottom: 0.32rem !important;
      }

      [data-testid="stBaseButton-segmented_control"],
      [data-testid="stBaseButton-segmented_controlActive"],
      .stButton > button {
        white-space: nowrap !important;
        word-break: keep-all !important;
        min-height: 2.18rem !important;
        border-radius: 999px !important;
        font-size: 0.88rem !important;
      }

      [data-testid="stBaseButton-segmented_control"] {
        color: var(--rr-ink) !important;
        background: var(--rr-surface-raised) !important;
        border-color: var(--rr-line) !important;
      }

      [data-testid="stBaseButton-segmented_control"] *,
      [data-testid="stBaseButton-segmented_control"] p,
      [data-testid="stBaseButton-segmented_control"] span {
        color: var(--rr-ink) !important;
      }

      [data-testid="stBaseButton-segmented_controlActive"] {
        background: var(--rr-primary) !important;
        color: #ffffff !important;
        border-color: var(--rr-primary) !important;
        box-shadow: none !important;
      }

      [data-testid="stBaseButton-segmented_controlActive"] *,
      [data-testid="stBaseButton-segmented_controlActive"] p,
      [data-testid="stBaseButton-segmented_controlActive"] span {
        color: #ffffff !important;
      }

      .rr-bento-row {
        margin-top: 0.56rem !important;
      }

      .rr-bento-card {
        padding: 0.82rem !important;
      }

      .rr-bento-card.mission,
      .rr-bento-card.resource,
      .rr-bento-card.map {
        min-height: 0 !important;
      }

      .rr-bento-title {
        color: var(--rr-ink) !important;
      }

      .rr-bento-body {
        color: var(--rr-muted) !important;
        margin-bottom: 0.4rem !important;
      }

      .rr-mini-fact,
      .rr-chip {
        color: var(--rr-ink) !important;
        background: var(--rr-surface-raised) !important;
        border-color: var(--rr-line) !important;
      }

      .rr-official-line,
      .rr-card-eyebrow {
        color: var(--rr-soft) !important;
      }

      .rr-resource-art {
        height: 6.2rem !important;
        min-height: 6.2rem !important;
      }

      .rr-resource-layout {
        grid-template-columns: 7.2rem minmax(0, 1fr) !important;
        gap: 0.64rem !important;
        align-items: center !important;
      }

      .rr-source-link {
        background: var(--rr-primary) !important;
        border-color: var(--rr-primary) !important;
        color: #ffffff !important;
        padding: 0.42rem 0.7rem !important;
      }

      .rr-map {
        border-color: var(--rr-line) !important;
        background:
          linear-gradient(90deg, rgba(29, 78, 216, 0.09) 1px, transparent 1px),
          linear-gradient(rgba(29, 78, 216, 0.09) 1px, transparent 1px),
          linear-gradient(135deg, #eef6ff 0%, #f8fafc 55%, #ecfdf5 100%) !important;
      }

      .rr-map.compact {
        height: 6.9rem !important;
      }

      .rr-map-label {
        background: rgba(255, 255, 255, 0.96) !important;
        color: #111827 !important;
      }

      .rr-map-label small {
        color: #475569 !important;
      }

      .st-key-route_action_bar {
        position: static !important;
        left: auto !important;
        right: auto !important;
        bottom: auto !important;
        width: 100% !important;
        max-width: none !important;
        margin: 0.58rem 0 0 !important;
        padding: 0.58rem !important;
        border-radius: 20px !important;
        background: var(--rr-surface) !important;
        border: 1px solid var(--rr-line) !important;
        box-shadow: var(--rr-shadow-soft) !important;
      }

      .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        gap: 0.42rem !important;
      }

      .st-key-route_action_bar [data-testid="column"] {
        width: 100% !important;
        min-width: 0 !important;
      }

      .st-key-route_action_bar .stButton > button {
        min-height: 2.44rem !important;
        padding: 0.48rem 0.72rem !important;
        font-size: 0.9rem !important;
        line-height: 1.15 !important;
      }

      .st-key-route_action_bar [data-testid="stBaseButton-primary"] {
        background: var(--rr-action) !important;
        border-color: var(--rr-action) !important;
        color: #ffffff !important;
      }

      .rr-progressive-panel {
        margin-top: 0.58rem !important;
      }

      @media (prefers-color-scheme: dark) {
        [data-baseweb="tab"][aria-selected="true"],
        [data-testid="stBaseButton-segmented_controlActive"] {
          background: #e0f2fe !important;
          color: #082f49 !important;
        }

        [data-baseweb="tab"][aria-selected="true"] *,
        [data-testid="stBaseButton-segmented_controlActive"] *,
        [data-testid="stBaseButton-segmented_controlActive"] p,
        [data-testid="stBaseButton-segmented_controlActive"] span {
          color: #082f49 !important;
        }

        .rr-use-guide b {
          background: #e0f2fe !important;
          color: #082f49 !important;
        }

        .rr-source-link,
        .st-key-route_action_bar [data-testid="stBaseButton-primary"] {
          background: #f97316 !important;
          border-color: #f97316 !important;
          color: #111827 !important;
        }

        .rr-source-link *,
        .st-key-route_action_bar [data-testid="stBaseButton-primary"] * {
          color: #111827 !important;
        }

        .rr-map {
          background:
            linear-gradient(90deg, rgba(125, 211, 252, 0.10) 1px, transparent 1px),
            linear-gradient(rgba(125, 211, 252, 0.10) 1px, transparent 1px),
            linear-gradient(135deg, #1e293b 0%, #111827 58%, #0f172a 100%) !important;
        }
      }

      @media (max-width: 860px) {
        .block-container {
          padding: 0.62rem 0.72rem 1.2rem !important;
        }

        .rr-use-guide {
          grid-template-columns: 1fr !important;
          grid-column: 1 !important;
          grid-row: auto !important;
        }

        .rr-route-hero {
          grid-template-columns: 1fr !important;
        }

        .rr-use-guide span {
          white-space: normal !important;
        }

        .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"] {
          margin-bottom: 0.34rem !important;
        }

        .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
          grid-template-columns: 1fr 1fr !important;
          gap: 0.42rem !important;
        }
      }

      @media (max-width: 430px) {
        .block-container {
          padding: 0.52rem 0.62rem 1.1rem !important;
        }

        .rr-hero-title {
          font-size: 1.08rem !important;
        }

        .rr-hero-copy {
          font-size: 0.8rem !important;
        }

        [data-baseweb="tab-list"] {
          overflow-x: auto !important;
          border-radius: 18px !important;
        }

        [data-testid="stBaseButton-segmented_control"],
        [data-testid="stBaseButton-segmented_controlActive"],
        .stButton > button {
          font-size: 0.78rem !important;
          min-height: 2.12rem !important;
        }

        .rr-bento-card {
          padding: 0.72rem !important;
        }

        .rr-map.compact {
          height: 6.8rem !important;
        }

        .st-key-route_action_bar {
          border-radius: 18px !important;
        }

        .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
          grid-template-columns: 1fr 1fr !important;
        }

        .st-key-route_action_bar .stButton > button {
          font-size: 0.78rem !important;
          min-height: 2.34rem !important;
          padding: 0.38rem 0.4rem !important;
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


def render_secondary_link(label: str, url: str, key: str) -> None:
    if not url:
        return
    with st.container(key=widget_key(key)):
        st.link_button(label, url, type="secondary", width="stretch")


def chip(text: str, tone: str = "gray") -> str:
    return f'<span class="rr-chip {tone}">{e(text)}</span>'


@st.cache_data(show_spinner=False)
def asset_data_uri(filename: str) -> str:
    path = ASSET_DIR / filename
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def fallback_image_for_resource(resource_type: str) -> str:
    if resource_type == "culture_event":
        return asset_data_uri("resource_culture.png")
    if resource_type == "culture_facility":
        return asset_data_uri("resource_space.png")
    if resource_type == "support_program":
        return asset_data_uri("resource_policy.png")
    return asset_data_uri("resource_route.png")


def resource_image_src(resource: dict[str, Any]) -> str:
    thumbnail_url = display_text(resource.get("thumbnail_url"))
    if thumbnail_url.startswith("https://"):
        return thumbnail_url
    return fallback_image_for_resource(str(resource.get("resource_type", "")))


def resource_source_url(resource: dict[str, Any]) -> str:
    return display_text(resource.get("detail_url")) or display_text(resource.get("source_url"))


def google_maps_api_key() -> str:
    secret_key = ""
    try:
        secret_key = str(st.secrets.get("GOOGLE_MAPS_API_KEY", "") or st.secrets.get("google_maps_api_key", "")).strip()
    except Exception:
        secret_key = ""
    return secret_key or os.getenv("GOOGLE_MAPS_API_KEY", "").strip()


def float_or_none(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def resource_destination_query(resource: dict[str, Any]) -> str:
    lat = float_or_none(resource.get("latitude"))
    lon = float_or_none(resource.get("longitude"))
    if lat is not None and lon is not None:
        return f"{lat:.6f},{lon:.6f}"
    parts = [
        display_text(resource.get("official_place")),
        display_text(resource.get("address")),
        display_text(resource.get("name")),
        display_text(resource.get("district")),
        "인천",
    ]
    deduped = list(dict.fromkeys(part for part in parts if part))
    return " ".join(deduped)


def google_maps_embed_url(resource: dict[str, Any]) -> str:
    destination = resource_destination_query(resource)
    api_key = google_maps_api_key()
    if api_key:
        user_lat, user_lon = current_user_location()
        return "https://www.google.com/maps/embed/v1/directions?" + urlencode(
            {
                "key": api_key,
                "origin": f"{user_lat:.6f},{user_lon:.6f}",
                "destination": destination,
                "mode": "walking",
                "language": "ko",
                "region": "KR",
            }
        )
    return f"https://maps.google.com/maps?q={quote_plus(destination)}&z=14&output=embed"


def google_maps_directions_url(resource: dict[str, Any]) -> str:
    user_lat, user_lon = current_user_location()
    return "https://www.google.com/maps/dir/?" + urlencode(
        {
            "api": "1",
            "origin": f"{user_lat:.6f},{user_lon:.6f}",
            "destination": resource_destination_query(resource),
            "travelmode": "walking",
        }
    )


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


def apply_explicit_theme_css() -> None:
    dark = current_theme_mode() == "dark"
    palette = {
        "mode": "dark" if dark else "light",
        "bg": "#0F172A" if dark else "#F6F8FC",
        "page_top": "#111827" if dark else "#FFFFFF",
        "surface": "#182235" if dark else "#FFFFFF",
        "surface_raised": "#1F2937" if dark else "#F9FBFF",
        "ink": "#F8FAFC" if dark else "#111827",
        "muted": "#D1D5DB" if dark else "#374151",
        "soft": "#B6C2D3" if dark else "#64748B",
        "line": "#3B4A60" if dark else "#D6DEEA",
        "primary": "#7DD3FC" if dark else "#1D4ED8",
        "primary_strong": "#BAE6FD" if dark else "#1E40AF",
        "primary_soft": "rgba(125, 211, 252, 0.16)" if dark else "#E8F0FF",
        "info": "#5EEAD4" if dark else "#0F766E",
        "info_soft": "rgba(94, 234, 212, 0.16)" if dark else "#E7F7F4",
        "action": "#FB923C" if dark else "#C2410C",
        "action_soft": "rgba(251, 146, 60, 0.18)" if dark else "#FFF1E7",
        "active_fg": "#082F49" if dark else "#FFFFFF",
        "action_fg": "#111827" if dark else "#FFFFFF",
        "shadow": "0 16px 38px rgba(0, 0, 0, 0.32)" if dark else "0 14px 34px rgba(15, 23, 42, 0.10)",
        "shadow_soft": "0 8px 22px rgba(0, 0, 0, 0.24)" if dark else "0 6px 18px rgba(15, 23, 42, 0.08)",
        "map_bg": "#111827" if dark else "#FFFFFF",
        "map_line": "#334155" if dark else "#D6DEEA",
        "select_hover": "#24324A" if dark else "#EAF1FF",
        "select_active": "#0B3551" if dark else "#DBEAFE",
    }
    st.markdown(
        f"""
        <style>
          :root {{
            --rr-bg: {palette["bg"]};
            --rr-page-top: {palette["page_top"]};
            --rr-surface: {palette["surface"]};
            --rr-surface-raised: {palette["surface_raised"]};
            --rr-ink: {palette["ink"]};
            --rr-muted: {palette["muted"]};
            --rr-soft: {palette["soft"]};
            --rr-line: {palette["line"]};
            --rr-primary: {palette["primary"]};
            --rr-primary-strong: {palette["primary_strong"]};
            --rr-primary-soft: {palette["primary_soft"]};
            --rr-info: {palette["info"]};
            --rr-info-soft: {palette["info_soft"]};
            --rr-action: {palette["action"]};
            --rr-action-soft: {palette["action_soft"]};
            --rr-glass: {palette["surface"]};
            --rr-shadow: {palette["shadow"]};
            --rr-shadow-soft: {palette["shadow_soft"]};
          }}

          html, body, .stApp {{
            color-scheme: {palette["mode"]} !important;
          }}

          .stApp,
          [data-testid="stAppViewContainer"],
          [data-testid="stMain"],
          [data-testid="stMainBlockContainer"],
          section.main {{
            background: var(--rr-bg) !important;
            color: var(--rr-ink) !important;
          }}

          .block-container {{
            max-width: 1120px !important;
            padding: 1rem 1.15rem 2rem !important;
          }}

          [data-testid="stVerticalBlock"] {{
            gap: 0.74rem !important;
          }}

          .rr-app-shell {{
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) auto !important;
            gap: 0.85rem !important;
            align-items: center !important;
            margin: 0 0 0.65rem !important;
            padding: 0.1rem 0 !important;
          }}

          .rr-brand-name {{
            color: var(--rr-ink) !important;
            font-size: 1.22rem !important;
            line-height: 1.15 !important;
          }}

          .rr-brand-sub,
          .rr-session-pill,
          .rr-theme-toggle-label {{
            color: var(--rr-muted) !important;
          }}

          .rr-theme-toggle-label {{
            font-size: 0.72rem !important;
            font-weight: 850 !important;
            text-align: right !important;
            margin-bottom: 0.24rem !important;
          }}

          .rr-route-hero {{
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) auto !important;
            gap: 0.8rem !important;
            align-items: center !important;
            padding: 0.78rem 0.9rem !important;
            margin-bottom: 0.68rem !important;
            background: var(--rr-surface) !important;
            border: 1px solid var(--rr-line) !important;
            border-radius: 18px !important;
            box-shadow: var(--rr-shadow-soft) !important;
            overflow: hidden !important;
          }}

          .rr-hero-copyblock {{
            min-width: 0 !important;
            align-self: center !important;
          }}

          .rr-hero-kicker {{
            color: var(--rr-primary-strong) !important;
            font-size: 0.78rem !important;
            font-weight: 920 !important;
            margin-bottom: 0.18rem !important;
          }}

          .rr-hero-title,
          .rr-bento-title,
          .rr-section-title,
          h1, h2, h3, h4,
          p, li, label,
          [data-testid="stMarkdownContainer"],
          [data-testid="stWidgetLabel"] {{
            color: var(--rr-ink) !important;
          }}

          .rr-hero-copy,
          .rr-bento-body,
          .rr-muted {{
            color: var(--rr-muted) !important;
          }}

          .rr-use-guide {{
            display: flex !important;
            flex-wrap: wrap !important;
            justify-content: flex-end !important;
            gap: 0.38rem !important;
            min-width: 18rem !important;
            margin: 0 !important;
          }}

          .rr-use-guide span {{
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.3rem !important;
            min-height: 2rem !important;
            border-radius: 999px !important;
            border: 1px solid var(--rr-line) !important;
            background: var(--rr-surface-raised) !important;
            color: var(--rr-ink) !important;
            font-size: 0.76rem !important;
            font-weight: 880 !important;
            white-space: nowrap !important;
            padding: 0.26rem 0.55rem !important;
          }}

          .rr-use-guide b {{
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 1.2rem !important;
            height: 1.2rem !important;
            border-radius: 999px !important;
            background: var(--rr-primary) !important;
            color: {palette["active_fg"]} !important;
            font-size: 0.7rem !important;
          }}

          .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"],
          .rr-bento-card,
          .rr-progressive-panel,
          .rr-history-card,
          .rr-resource-card,
          .rr-panel,
          .st-key-route_action_bar {{
            background: var(--rr-surface) !important;
            border-color: var(--rr-line) !important;
            box-shadow: var(--rr-shadow-soft) !important;
          }}

          .rr-use-guide b,
          [data-baseweb="tab"][aria-selected="true"],
          [data-testid="stBaseButton-segmented_controlActive"] {{
            background: var(--rr-primary) !important;
            border-color: var(--rr-primary) !important;
            color: {palette["active_fg"]} !important;
          }}

          .rr-use-guide b *,
          [data-baseweb="tab"][aria-selected="true"] *,
          [data-testid="stBaseButton-segmented_controlActive"] *,
          [data-testid="stBaseButton-segmented_controlActive"] p,
          [data-testid="stBaseButton-segmented_controlActive"] span {{
            color: {palette["active_fg"]} !important;
          }}

          [data-testid="stBaseButton-segmented_control"],
          [data-testid="stBaseButton-secondary"],
          .stButton > button {{
            background: var(--rr-surface-raised) !important;
            border-color: var(--rr-line) !important;
            color: var(--rr-ink) !important;
            transition: transform 160ms ease, background 160ms ease, border-color 160ms ease, box-shadow 160ms ease !important;
          }}

          [data-testid="stBaseButton-segmented_control"] *,
          [data-testid="stBaseButton-secondary"] *,
          .stButton > button * {{
            color: inherit !important;
          }}

          [data-testid="stBaseButton-segmented_control"]:hover,
          [data-testid="stBaseButton-secondary"]:hover,
          .stButton > button:hover {{
            border-color: var(--rr-primary) !important;
            box-shadow: 0 0 0 3px var(--rr-primary-soft) !important;
            transform: translateY(-1px) !important;
          }}

          [data-testid="stBaseButton-primary"],
          .st-key-route_action_bar [data-testid="stBaseButton-primary"] {{
            background: var(--rr-action) !important;
            border-color: var(--rr-action) !important;
            color: {palette["action_fg"]} !important;
            box-shadow: 0 10px 22px color-mix(in srgb, var(--rr-action) 24%, transparent) !important;
          }}

          [data-testid="stBaseButton-primary"] *,
          .st-key-route_action_bar [data-testid="stBaseButton-primary"] * {{
            color: {palette["action_fg"]} !important;
          }}

          .st-key-route_start_primary .stButton > button {{
            background: var(--rr-action) !important;
            border-color: var(--rr-action) !important;
            color: {palette["action_fg"]} !important;
            font-weight: 920 !important;
          }}

          .st-key-route_complete .stButton > button,
          [class*="st-key-resource_source_"] a,
          [class*="st-key-featured_source_"] a,
          .st-key-map_directions a {{
            background: var(--rr-primary) !important;
            border-color: var(--rr-primary) !important;
            color: {palette["active_fg"]} !important;
            border-radius: 999px !important;
            font-weight: 850 !important;
            text-decoration: none !important;
          }}

          .st-key-route_skip .stButton > button,
          .st-key-route_too_hard .stButton > button,
          .st-key-toggle_advanced_controls .stButton > button,
          .st-key-toggle_more_candidates .stButton > button,
          .st-key-toggle_record_panel .stButton > button,
          .st-key-reset_conditions .stButton > button {{
            background: transparent !important;
            border-color: var(--rr-line) !important;
            color: var(--rr-muted) !important;
            box-shadow: none !important;
          }}

          [data-baseweb="tab-list"],
          [data-baseweb="input"],
          [data-baseweb="select"] > div,
          [data-baseweb="textarea"],
          input, textarea {{
            background: var(--rr-surface) !important;
            border-color: var(--rr-line) !important;
            color: var(--rr-ink) !important;
          }}

          [data-baseweb="select"] *,
          [data-baseweb="input"] *,
          [data-baseweb="textarea"] *,
          input::placeholder,
          textarea::placeholder {{
            color: var(--rr-ink) !important;
          }}

          [data-baseweb="popover"],
          [data-baseweb="popover"] > div,
          [data-baseweb="menu"],
          [role="listbox"] {{
            background: var(--rr-surface) !important;
            border: 1px solid var(--rr-line) !important;
            color: var(--rr-ink) !important;
            box-shadow: var(--rr-shadow) !important;
          }}

          [data-baseweb="popover"] *,
          [data-baseweb="menu"] *,
          [role="listbox"] *,
          [role="option"],
          [role="option"] * {{
            color: var(--rr-ink) !important;
          }}

          [data-baseweb="menu"] li,
          [role="option"] {{
            background: var(--rr-surface) !important;
            color: var(--rr-ink) !important;
          }}

          [data-baseweb="menu"] li:hover,
          [role="option"]:hover,
          [role="option"][aria-selected="true"] {{
            background: {palette["select_hover"]} !important;
            color: var(--rr-ink) !important;
          }}

          [data-baseweb="menu"] li[aria-selected="true"],
          [role="option"][aria-selected="true"] {{
            background: {palette["select_active"]} !important;
          }}

          .rr-bento-row {{
            margin-top: 0.82rem !important;
          }}

          .rr-results-header {{
            display: flex !important;
            align-items: end !important;
            justify-content: space-between !important;
            gap: 0.7rem !important;
            margin: 1rem 0 0.2rem !important;
          }}

          .rr-results-header span {{
            color: var(--rr-primary-strong) !important;
            font-size: 0.78rem !important;
            font-weight: 920 !important;
          }}

          .rr-results-header strong {{
            color: var(--rr-ink) !important;
            font-size: 1rem !important;
            font-weight: 930 !important;
            text-align: right !important;
          }}

          .rr-bento-card {{
            padding: 1rem !important;
            border-radius: 18px !important;
          }}

          .rr-resource-layout {{
            display: grid !important;
            grid-template-columns: 7.2rem minmax(0, 1fr) !important;
            gap: 0.68rem !important;
            align-items: center !important;
          }}

          .rr-resource-art {{
            width: 100% !important;
            height: 6.4rem !important;
            min-height: 6.4rem !important;
            border-radius: 14px !important;
            object-fit: cover !important;
            background: var(--rr-primary-soft) !important;
            border: 1px solid var(--rr-line) !important;
          }}

          .rr-source-link {{
            background: var(--rr-primary) !important;
            border-color: var(--rr-primary) !important;
            color: {palette["active_fg"]} !important;
          }}

          .rr-source-link * {{
            color: {palette["active_fg"]} !important;
          }}

          .rr-map {{
            background: {palette["map_bg"]} !important;
            border-color: {palette["map_line"]} !important;
          }}

          .rr-map.compact {{
            height: 7.4rem !important;
          }}

          .rr-map.expanded {{
            height: 21rem !important;
          }}

          .rr-map-label {{
            background: var(--rr-surface) !important;
            color: var(--rr-ink) !important;
            border: 1px solid var(--rr-line) !important;
          }}

          .rr-map-label small,
          .rr-official-line,
          .rr-card-eyebrow {{
            color: var(--rr-soft) !important;
          }}

          .st-key-route_action_bar {{
            position: sticky !important;
            bottom: 0.55rem !important;
            z-index: 20 !important;
            margin-top: 0.62rem !important;
            padding: 0.58rem !important;
            border-radius: 20px !important;
          }}

          @media (max-width: 860px) {{
            .block-container {{
              padding: 0.82rem 0.82rem 1.3rem !important;
            }}

            .rr-app-shell {{
              grid-template-columns: 1fr !important;
              gap: 0.55rem !important;
            }}

            .rr-theme-toggle-label {{
              text-align: left !important;
            }}

            .rr-route-hero,
            .rr-choice-row,
            .rr-bento-row {{
              grid-template-columns: 1fr !important;
            }}

            .rr-use-guide {{
              justify-content: flex-start !important;
              min-width: 0 !important;
            }}

            .rr-resource-art {{
              height: 6rem !important;
              min-height: 6rem !important;
            }}
          }}

          @media (max-width: 430px) {{
            .block-container {{
              padding: 0.72rem 0.68rem 1.15rem !important;
            }}

            .rr-route-hero {{
              padding: 0.9rem !important;
            }}

            .rr-hero-title {{
              font-size: 1.24rem !important;
            }}

            .rr-results-header {{
              align-items: start !important;
              flex-direction: column !important;
              gap: 0.15rem !important;
            }}

            .rr-results-header strong {{
              text-align: left !important;
            }}

            .rr-resource-layout {{
              grid-template-columns: 5.8rem minmax(0, 1fr) !important;
              gap: 0.58rem !important;
            }}

            .rr-resource-art {{
              height: 5.3rem !important;
              min-height: 5.3rem !important;
            }}
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def display_minutes(value: Any) -> int:
    try:
        if pd.isna(value):
            return 0
        return int(value)
    except Exception:
        return 0


def render_data_status(resources: pd.DataFrame) -> None:
    if resources.empty:
        st.markdown('<div class="rr-data-strip"><span>공식 자원 0건</span></div>', unsafe_allow_html=True)
        return
    source_kinds = ", ".join(
        sorted(source_kind_label(value) for value in resources.get("source_kind", pd.Series(dtype=str)).dropna().unique())
    )
    checked = format_checked_at(resources.get("source_checked_at", pd.Series([""])).dropna().max())
    source_count = resources.get("source_name", pd.Series(dtype=str)).nunique()
    st.markdown(
        f"""
        <div class="rr-data-strip">
          <span>공식 자원 {len(resources)}건</span>
          <span>출처 {source_count}개</span>
          <span>수집 방식 {e(source_kinds or '확인 필요')}</span>
          <span>확인 시각 {e(checked)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def render_compact_route_controls() -> None:
    normalize_option_key("outside_burden", LEVEL_OPTIONS, DEFAULT_STATE["outside_burden"])
    normalize_option_key("social_burden", LEVEL_OPTIONS, DEFAULT_STATE["social_burden"])
    normalize_option_key("energy_level", LEVEL_OPTIONS, DEFAULT_STATE["energy_level"])
    normalize_option_key("daily_rhythm_level", LEVEL_OPTIONS, DEFAULT_STATE["daily_rhythm_level"])
    normalize_option_key("employment_burden", LEVEL_OPTIONS, DEFAULT_STATE["employment_burden"])
    normalize_option_key("future_anxiety", LEVEL_OPTIONS, DEFAULT_STATE["future_anxiety"])
    normalize_option_key("max_outdoor_minutes", TIME_OPTIONS, DEFAULT_STATE["max_outdoor_minutes"])
    normalize_option_key("budget_limit", BUDGET_OPTIONS, DEFAULT_STATE["budget_limit"])
    normalize_option_key("resource_max_burden", BURDEN_FILTER_OPTIONS, 3)

    with st.container():
        st.markdown(
            f"""
            <div class="rr-control-card">
            <div class="rr-section-title">1. 조건 입력</div>
            <div class="rr-muted">오늘 가능한 범위만 고르면 추천 미션, 공식 자원, 지도 위치가 바로 갱신됩니다.</div>
            <div class="rr-condition-bar">
              <div class="rr-condition-pill"><span>위치</span><strong>{e(str(st.session_state["district"]))}</strong></div>
              <div class="rr-condition-pill"><span>외출 부담</span><strong>{e(level_option_label(int(st.session_state["outside_burden"])))}</strong></div>
              <div class="rr-condition-pill"><span>대면 부담</span><strong>{e(level_option_label(int(st.session_state["social_burden"])))}</strong></div>
              <div class="rr-condition-pill"><span>에너지</span><strong>{e(level_option_label(int(st.session_state["energy_level"])))}</strong></div>
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        c1.selectbox("현재 위치", DISTRICTS, key="district")
        c2.selectbox("위치 기준", ["구/군 중심", "직접 좌표 입력"], key="location_mode")
        st.session_state["manual_location"] = st.session_state["location_mode"] == "직접 좌표 입력"
        if st.session_state["manual_location"]:
            loc1, loc2 = st.columns(2)
            loc1.number_input("위도", min_value=33.0, max_value=39.0, step=0.0001, format="%.4f", key="user_latitude")
            loc2.number_input("경도", min_value=124.0, max_value=132.0, step=0.0001, format="%.4f", key="user_longitude")
        else:
            lat, lon = district_center(str(st.session_state["district"]))
            st.session_state["user_latitude"] = lat
            st.session_state["user_longitude"] = lon

        b1, b2, b3 = st.columns(3)
        b1.selectbox("외출 부담", LEVEL_OPTIONS, format_func=level_option_label, key="outside_burden")
        b2.selectbox("대면 부담", LEVEL_OPTIONS, format_func=level_option_label, key="social_burden")
        b3.selectbox("오늘 에너지", LEVEL_OPTIONS, format_func=level_option_label, key="energy_level")

        s1, s2 = st.columns(2)
        s1.selectbox("가능 시간", TIME_OPTIONS, format_func=time_option_label, key="max_outdoor_minutes")
        s2.selectbox("오늘 예산", BUDGET_OPTIONS, format_func=budget_option_label, key="budget_limit")

        f1, f2 = st.columns(2)
        f1.selectbox("자료 범위", list(RESOURCE_SCOPE_OPTIONS.keys()), key="resource_scope")
        f2.selectbox("비용 범위", list(COST_SCOPE_OPTIONS.keys()), key="resource_cost_scope")
        st.session_state["resource_types"] = RESOURCE_SCOPE_OPTIONS[st.session_state["resource_scope"]]
        st.session_state["resource_costs"] = COST_SCOPE_OPTIONS[st.session_state["resource_cost_scope"]]

        f3, f4 = st.columns(2)
        f3.selectbox("확인 방식", ACCESS_MODE_OPTIONS, key="resource_access_mode")
        f4.selectbox("최대 부담도", BURDEN_FILTER_OPTIONS, format_func=burden_filter_label, key="resource_max_burden")
        st.session_state["resource_online_only"] = st.session_state["resource_access_mode"] == "온라인 먼저 확인"

        st.text_input("찾고 싶은 활동", placeholder="예: 전시, 청년공간, 구직활동비", key="resource_query")

        d1, d2 = st.columns(2)
        d1.selectbox("선호 방식", list(CONTACT_LABELS.keys()), format_func=lambda x: CONTACT_LABELS[x], key="preferred_contact_mode")
        d2.selectbox("도움 여부", ["혼자 확인", "함께 확인 가능"], key="support_mode")
        st.session_state["has_support_person"] = st.session_state["support_mode"] == "함께 확인 가능"

        detail1, detail2, detail3 = st.columns(3)
        detail1.selectbox("생활 리듬", LEVEL_OPTIONS, format_func=level_option_label, key="daily_rhythm_level")
        detail2.selectbox("취업 부담", LEVEL_OPTIONS, format_func=level_option_label, key="employment_burden")
        detail3.selectbox("미래 불안", LEVEL_OPTIONS, format_func=level_option_label, key="future_anxiety")
        st.text_area("오늘 상태 메모", height=68, key="free_text", placeholder="예: 오늘은 집에서 먼저 확인할 수 있는 활동만 보고 싶어요.")
        if st.button("조건 초기화", key="reset_conditions", width="stretch", type="tertiary"):
            reset_demo_state()
            st.session_state["last_action_message"] = "조건을 초기화했어요."
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
        readiness = st.selectbox("진행 준비도", LEVEL_OPTIONS, index=2, format_func=level_option_label)
        burden_after = st.selectbox("진행 후 부담도", LEVEL_OPTIONS, index=2, format_func=level_option_label)
        note = st.text_area("메모", placeholder="예: 공식 페이지 확인 후 신청 대상 조건을 확인함 / 프로그램에 참여함 / 결과 대기 중")
        submitted = st.form_submit_button("결과 저장", key=f"{key_prefix}_outcome_submit", use_container_width=True)
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


def render_mission_action_buttons(profile: UserProfile, mission: dict[str, Any], recommended_stage: int, mission_key: str) -> None:
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("시작", key=f"start_{mission_key}", width="stretch"):
        record_mission_action(profile, mission, ProgressStatus.started, recommended_stage)
    if c2.button("완료", key=f"complete_{mission_key}", width="stretch"):
        record_mission_action(profile, mission, ProgressStatus.completed, recommended_stage)
    if c3.button("나중에", key=f"skip_{mission_key}", width="stretch", type="tertiary"):
        record_mission_action(profile, mission, ProgressStatus.skipped, recommended_stage)
    if c4.button("어려움", key=f"hard_{mission_key}", width="stretch", type="tertiary"):
        record_mission_action(profile, mission, ProgressStatus.too_hard, recommended_stage)


def render_primary_mission(
    profile: UserProfile,
    mission: dict[str, Any],
    recommended_stage: int,
    candidate_count: int,
    key_prefix: str,
) -> None:
    st.markdown(
        f"""
        <div class="rr-panel rr-stage-panel rr-primary-mission">
          <div class="rr-section-title">2. 오늘 할 미션</div>
          <div class="rr-card-title">{e(mission["title"])}</div>
          <div class="rr-card-body">{e(mission["description"])}</div>
          {chip(STAGE_LABELS.get(recommended_stage, "추천 단계"), "teal")}
          {chip("조건에 맞는 공식 자원 " + str(candidate_count) + "건", "gray")}
          {chip(time_option_label(int(st.session_state["max_outdoor_minutes"])), "gray")}
          {chip(budget_option_label(int(st.session_state["budget_limit"])), "gray")}
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_mission_action_buttons(profile, mission, recommended_stage, f"{key_prefix}_{mission['mission_id']}")


def render_user_mission(profile: UserProfile, mission: dict[str, Any], recommended_stage: int, key_prefix: str) -> None:
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="rr-card-title">{e(mission["title"])}</div>
            <div class="rr-card-body">{e(mission["description"])}</div>
            {chip("예상 " + str(int(mission["expected_minutes"])) + "분", "teal")}
            {chip("부담 " + burden_text(mission["burden_level"]), "gold")}
            {chip("외출 필요" if bool(mission["outdoor_required"]) else "집에서 가능", "gray")}
            {chip("대면 있음" if bool(mission["social_contact_required"]) else "대면 없음", "gray")}
            """,
            unsafe_allow_html=True,
        )
        render_mission_action_buttons(profile, mission, recommended_stage, f"{key_prefix}_{mission['mission_id']}")


def render_user_resource(resource: dict[str, Any], key_prefix: str) -> None:
    contact = display_text(resource.get("contact"))
    duration = display_minutes(resource.get("estimated_duration_minutes"))
    source_url = resource_source_url(resource)
    source_name = display_text(resource.get("source_name")) or "공식 출처"
    address = display_text(resource.get("address"))
    period = format_period(resource)
    online_text = "온라인 확인 가능" if as_bool(resource.get("online_available")) else "현장 정보 확인 필요"
    distance = resource.get("distance_km")
    distance_text = f" · 내 위치에서 약 {float(distance):.1f}km" if distance is not None and pd.notna(distance) else ""
    image_src = resource_image_src(resource)
    fallback_src = fallback_image_for_resource(str(resource.get("resource_type", "")))
    official_place = display_text(resource.get("official_place")) or address
    st.markdown(
        f"""
        <div class="rr-resource-card">
          <div class="rr-card-with-media">
            <img class="rr-resource-thumb" src="{e(image_src)}" alt="{e(resource['name'])} 이미지" loading="lazy" onerror="this.onerror=null;this.src='{e(fallback_src)}';" />
            <div>
              <div class="rr-card-title">{e(resource["name"])}</div>
              <div class="rr-card-body">{e(resource["description"])}</div>
              {chip(RESOURCE_TYPE_LABELS.get(str(resource["resource_type"]), str(resource["resource_type"])), "teal")}
              {chip(COST_LABELS.get(str(resource["cost_type"]), str(resource["cost_type"])), "gray")}
              <div class="rr-info-grid">
                <div class="rr-info-item"><span>지역</span><strong>{e(str(resource["district"]))}</strong></div>
                <div class="rr-info-item"><span>기간</span><strong>{e(period)}</strong></div>
                <div class="rr-info-item"><span>확인</span><strong>{e(online_text)}</strong></div>
                <div class="rr-info-item"><span>거리</span><strong>{e(distance_text.replace(' · 내 위치에서 약 ', '') or '위치 확인')}</strong></div>
                <div class="rr-info-item"><span>소요</span><strong>{e(str(duration))}분</strong></div>
                <div class="rr-info-item"><span>문의</span><strong>{e(contact or '공식 페이지 확인')}</strong></div>
              </div>
              <div class="rr-resource-meta">{e(official_place) if official_place else "장소는 공식 페이지에서 확인하세요."}</div>
              <div class="rr-proof"><strong>공식 출처</strong> · {e(source_name)}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_secondary_link("공식 페이지 열기", source_url, f"resource_source_{key_prefix}")


def render_featured_resource(resource: dict[str, Any]) -> None:
    source_url = resource_source_url(resource)
    source_name = display_text(resource.get("source_name")) or "공식 출처"
    distance = resource.get("distance_km")
    distance_text = f"{float(distance):.1f}km" if distance is not None and pd.notna(distance) else "위치 확인"
    image_src = resource_image_src(resource)
    fallback_src = fallback_image_for_resource(str(resource.get("resource_type", "")))
    official_place = display_text(resource.get("official_place")) or display_text(resource.get("address"))
    period = format_period(resource)
    st.markdown(
        f"""
        <div class="rr-featured-resource">
          <div class="rr-card-with-media">
            <img class="rr-resource-thumb" src="{e(image_src)}" alt="{e(resource['name'])} 이미지" loading="lazy" onerror="this.onerror=null;this.src='{e(fallback_src)}';" />
            <div>
              <div class="rr-section-title">3. 공식 자원</div>
              <div class="rr-card-title">{e(resource["name"])}</div>
              <div class="rr-card-body">{e(resource["description"])}</div>
              {chip(RESOURCE_TYPE_LABELS.get(str(resource["resource_type"]), str(resource["resource_type"])), "teal")}
              {chip(COST_LABELS.get(str(resource["cost_type"]), str(resource["cost_type"])), "gray")}
              <div class="rr-info-grid">
                <div class="rr-info-item"><span>지역</span><strong>{e(str(resource["district"]))}</strong></div>
                <div class="rr-info-item"><span>거리</span><strong>{e(distance_text)}</strong></div>
                <div class="rr-info-item"><span>기간</span><strong>{e(period)}</strong></div>
                <div class="rr-info-item"><span>장소</span><strong>{e(official_place or '공식 페이지 확인')}</strong></div>
              </div>
              <div class="rr-proof"><strong>공식 출처</strong> · {e(source_name)}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_secondary_link("공식 페이지 열기", source_url, f"featured_source_{display_text(resource.get('resource_id'))}")


def render_next_action(top_resource: dict[str, Any]) -> None:
    items = next_action_items(top_resource)
    st.markdown(
        f"""
        <div class="rr-next-action">
          <div class="rr-section-title">가장 작은 다음 행동</div>
          <div class="rr-muted"><strong>{e(display_text(top_resource.get("name")))}</strong>의 공식 페이지에서 현재 운영 여부와 조건 한 줄만 확인합니다.</div>
          <ol class="rr-compact-list">
            {''.join(f"<li>{e(item)}</li>" for item in items)}
          </ol>
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


def render_app_shell() -> None:
    shell_col, theme_col = st.columns([1, 0.34], gap="medium")
    with shell_col:
        st.markdown(
            """
            <div class="rr-app-shell">
              <div class="rr-brand-lockup">
                <div class="rr-brand-name">RebootRoute</div>
                <div class="rr-brand-sub">오늘 가능한 한 가지 행동과 공식 자원을 바로 찾습니다.</div>
              </div>
              <div class="rr-session-pill">진단·상담 서비스 아님</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with theme_col:
        st.markdown('<div class="rr-theme-toggle-label">화면 모드</div>', unsafe_allow_html=True)
        st.segmented_control(
            "화면 모드",
            ["밝게", "어둡게"],
            key="ui_theme_choice",
            label_visibility="collapsed",
            width="stretch",
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


def render_choice_chips() -> None:
    st.markdown('<div class="rr-choice-row">', unsafe_allow_html=True)
    cols = st.columns(4, gap="small")
    groups = [
        ("오늘 가능한 범위", ROUTE_RANGE_OPTIONS, "route_range_choice", "20분 외출"),
        ("사람 만나는 정도", ROUTE_CONTACT_OPTIONS, "route_contact_choice", "비대면"),
        ("찾고 싶은 것", ROUTE_INTENT_OPTIONS, "route_intent_choice", "문화행사"),
        ("오늘 비용", ROUTE_COST_OPTIONS, "route_cost_choice", "저비용 포함"),
    ]
    for col, (label, options, key, fallback) in zip(cols, groups, strict=False):
        with col:
            with st.container(border=True):
                if st.session_state.get(key) not in options:
                    st.session_state[key] = fallback
                st.markdown(f'<div class="rr-choice-label">{e(label)}</div>', unsafe_allow_html=True)
                value = st.segmented_control(
                    label,
                    options,
                    selection_mode="single",
                    key=key,
                    label_visibility="collapsed",
                    width="stretch",
                )
                if value is None:
                    st.session_state[key] = fallback
    st.markdown("</div>", unsafe_allow_html=True)
    apply_route_choices_when_changed()
    sync_derived_resource_filters()


def render_advanced_controls() -> None:
    toggle_label = "세부 조건 닫기" if st.session_state["show_advanced_controls"] else "더 조정하기"
    if st.button(toggle_label, key="toggle_advanced_controls", width="stretch", type="tertiary"):
        st.session_state["show_advanced_controls"] = not st.session_state["show_advanced_controls"]
        st.session_state["last_action_message"] = "세부 조건을 열었어요." if st.session_state["show_advanced_controls"] else "세부 조건을 닫았어요."
        st.rerun()
    if not st.session_state["show_advanced_controls"]:
        return
    st.markdown('<div class="rr-progressive-panel"><div class="rr-card-eyebrow">세부 조건</div>', unsafe_allow_html=True)
    st.markdown('<div class="rr-compact-controls">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.selectbox("위치", DISTRICTS, key="district")
    c2.selectbox("범위", list(RESOURCE_SCOPE_OPTIONS.keys()), key="resource_scope")
    c3.selectbox("비용", list(COST_SCOPE_OPTIONS.keys()), key="resource_cost_scope")
    c4.selectbox("부담도", BURDEN_FILTER_OPTIONS, format_func=burden_filter_label, key="resource_max_burden")
    c5, c6, c7, c8 = st.columns(4)
    c5.selectbox("확인 방식", ACCESS_MODE_OPTIONS, key="resource_access_mode")
    c6.selectbox("에너지", LEVEL_OPTIONS, format_func=level_option_label, key="energy_level")
    c7.selectbox("취업 부담", LEVEL_OPTIONS, format_func=level_option_label, key="employment_burden")
    c8.selectbox("불안", LEVEL_OPTIONS, format_func=level_option_label, key="future_anxiety")
    st.text_input("찾고 싶은 활동", placeholder="예: 전시, 청년공간, 구직활동비", key="resource_query")
    st.text_area("오늘 상태 메모", height=64, key="free_text", placeholder="예: 오늘은 집에서 확인할 수 있는 활동만 보고 싶어요.")
    st.markdown("</div></div>", unsafe_allow_html=True)
    sync_derived_resource_filters()


def render_route_builder() -> None:
    st.markdown(
        """
        <div class="rr-route-hero">
          <div class="rr-hero-copyblock">
            <div class="rr-hero-kicker">오늘의 루트 만들기</div>
            <div class="rr-hero-title">조건을 고르면 인천 공식 자원과 작은 행동을 추천합니다</div>
            <p class="rr-hero-copy">선택은 즉시 반영됩니다. 추천 버튼을 따로 누를 필요가 없습니다.</p>
          </div>
          <div class="rr-use-guide">
            <span><b>1</b>조건 선택</span>
            <span><b>2</b>미션 확인</span>
            <span><b>3</b>공식 자원 보기</span>
            <span><b>4</b>시작 기록</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_choice_chips()
    render_advanced_controls()


def fact(text: str) -> str:
    return f'<span class="rr-mini-fact">{e(text)}</span>'


def compact_description(text: Any, limit: int = 115) -> str:
    clean = " ".join(display_text(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "..."


def render_today_mission_card(profile: UserProfile, mission: dict[str, Any] | None, recommended_stage: int) -> None:
    if not mission:
        st.markdown(
            """
            <div class="rr-bento-card mission">
              <div class="rr-card-eyebrow">오늘 할 미션</div>
              <div class="rr-bento-title">조건을 조금 낮춰볼까요?</div>
              <div class="rr-bento-body">현재 선택으로는 바로 추천할 미션이 없습니다. 가능한 범위를 한 단계 넓혀보세요.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        f"""
        <div class="rr-bento-card mission">
          <div class="rr-card-eyebrow">오늘 할 미션</div>
          <div class="rr-bento-title">{e(mission["title"])}</div>
          <div class="rr-bento-body">{e(mission["description"])}</div>
          <div class="rr-mini-facts">
            {fact(STAGE_LABELS.get(recommended_stage, "오늘 루트"))}
            {fact(str(int(mission["expected_minutes"])) + "분")}
            {fact("부담 " + burden_text(mission["burden_level"]))}
            {fact("조건 맞춤")}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_resource_spotlight(resource: dict[str, Any] | None) -> None:
    if not resource:
        st.markdown(
            """
            <div class="rr-bento-card resource">
              <div class="rr-card-eyebrow">공식 자원</div>
              <div class="rr-bento-title">맞는 자원이 없습니다</div>
              <div class="rr-bento-body">비용이나 부담도 조건을 조금 넓히면 후보를 다시 찾을 수 있습니다.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    image_src = resource_image_src(resource)
    fallback_src = fallback_image_for_resource(str(resource.get("resource_type", "")))
    source_name = display_text(resource.get("source_name")) or "공식 출처"
    source_url = resource_source_url(resource)
    distance = resource.get("distance_km")
    distance_text = f"{float(distance):.1f}km" if distance is not None and pd.notna(distance) else "위치 확인"
    st.markdown(
        f"""
        <div class="rr-bento-card resource">
          <div class="rr-resource-layout">
            <img class="rr-resource-art" src="{e(image_src)}" alt="{e(resource['name'])} 이미지" loading="lazy" onerror="this.onerror=null;this.src='{e(fallback_src)}';" />
            <div>
              <div class="rr-card-eyebrow">가장 맞는 공식 자원</div>
              <div class="rr-bento-title">{e(compact_description(resource["name"], 52))}</div>
              <div class="rr-mini-facts">
                {fact(RESOURCE_TYPE_LABELS.get(str(resource["resource_type"]), str(resource["resource_type"])))}
                {fact(str(resource["district"]))}
                {fact(distance_text)}
              </div>
              <div class="rr-official-line">공식 출처: {e(source_name)}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_secondary_link("공식 페이지 열기", source_url, f"resource_source_spotlight_{display_text(resource.get('resource_id'))}")


def map_markers(resources: pd.DataFrame, max_items: int) -> str:
    user_lat, user_lon = current_user_location()
    points = resources.copy()
    if not points.empty:
        points["latitude"] = pd.to_numeric(points["latitude"], errors="coerce")
        points["longitude"] = pd.to_numeric(points["longitude"], errors="coerce")
        points = points.dropna(subset=["latitude", "longitude"]).head(max_items)
    user_left, user_top = map_position(user_lat, user_lon)
    markers = [
        f'<div class="rr-map-marker user" style="left:{user_left:.2f}%; top:{user_top:.2f}%;" title="내 위치"></div>'
    ]
    for _, row in points.iterrows():
        left, top = map_position(float(row["latitude"]), float(row["longitude"]))
        name = display_text(row.get("name")) or "활동 장소"
        district = display_text(row.get("district"))
        distance = row.get("distance_km")
        distance_text = f"{float(distance):.1f}km" if distance is not None and pd.notna(distance) else "거리 확인"
        markers.append(
            f'<div class="rr-map-marker place" style="left:{left:.2f}%; top:{top:.2f}%;" title="{e(name)}"></div>'
            f'<div class="rr-map-label" style="left:{left:.2f}%; top:{top:.2f}%;">{e(name)}<small>{e(district)} · {e(distance_text)}</small></div>'
        )
    return "".join(markers)


def render_google_map_preview(resource: dict[str, Any], *, expanded: bool) -> None:
    dark = current_theme_mode() == "dark"
    card_bg = "#182235" if dark else "#FFFFFF"
    card_border = "#3B4A60" if dark else "#D6DEEA"
    ink = "#F8FAFC" if dark else "#111827"
    muted = "#D1D5DB" if dark else "#374151"
    iframe_height = 280 if expanded else 118
    card_height = iframe_height + 92
    name = compact_description(resource.get("name"), 60)
    destination = resource_destination_query(resource)
    embed_url = google_maps_embed_url(resource)
    st.markdown('<div class="rr-card-eyebrow">내 위치와 활동 장소</div>', unsafe_allow_html=True)
    components.html(
        f"""
        <div style="
          box-sizing:border-box;
          width:100%;
          min-height:{card_height}px;
          padding:10px;
          border:1px solid {card_border};
          border-radius:18px;
          background:{card_bg};
          color:{ink};
          font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
        ">
          <div style="font-size:14px;font-weight:850;line-height:1.35;margin:0 0 8px;color:{ink};">{e(name)}</div>
          <iframe
            title="Google Maps - {e(name)}"
            src="{e(embed_url)}"
            width="100%"
            height="{iframe_height}"
            style="display:block;border:0;border-radius:15px;background:#eef2f7;"
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
            allowfullscreen>
          </iframe>
          <div style="display:flex;align-items:center;gap:8px;margin-top:10px;">
            <span style="
              min-width:0;
              overflow:hidden;
              text-overflow:ellipsis;
              white-space:nowrap;
              color:{muted};
              font-size:12px;
              font-weight:700;
            ">{e(destination)}</span>
          </div>
        </div>
        """,
        height=card_height + 8,
    )
    render_secondary_link("길찾기", google_maps_directions_url(resource), "map_directions")


def render_map_preview(resources: pd.DataFrame, top_resource: dict[str, Any] | None = None) -> None:
    expanded = bool(st.session_state["show_map_large"])
    if top_resource:
        render_google_map_preview(top_resource, expanded=expanded)
    else:
        map_class = "expanded" if expanded else "compact"
        max_items = 8 if expanded else 5
        st.markdown(
            f"""
            <div class="rr-bento-card map">
              <div class="rr-card-eyebrow">내 위치와 활동 장소</div>
              <div class="rr-map {map_class}">{map_markers(resources, max_items)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if st.button("지도 접기" if expanded else "지도에서 보기", key="toggle_map_large", width="stretch"):
        st.session_state["show_map_large"] = not expanded
        st.session_state["last_action_message"] = "지도를 크게 열었어요." if st.session_state["show_map_large"] else "지도 미리보기로 접었어요."
        st.rerun()


def render_today_bento(profile: UserProfile, analysis: dict[str, Any], filtered_resources: pd.DataFrame) -> tuple[dict[str, Any] | None, dict[str, Any] | None, int]:
    if analysis.get("safety_flag"):
        render_safety_branch(analysis)
        return None, None, 0
    recommended_stage = int(analysis["recommended_stage"])
    missions = analysis.get("next_3_missions", [])
    top_mission = missions[0] if missions else None
    top_resource = filtered_resources.iloc[0].to_dict() if not filtered_resources.empty else None
    st.markdown(
        """
        <div class="rr-results-header">
          <span>오늘 추천 루트</span>
          <strong>하나만 확인하고 바로 시작하세요</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="rr-bento-row">', unsafe_allow_html=True)
    mission_col, resource_col, map_col = st.columns([0.98, 0.92, 0.78], gap="small")
    with mission_col:
        render_today_mission_card(profile, top_mission, recommended_stage)
        render_bottom_action_bar(profile, top_mission, recommended_stage)
    with resource_col:
        render_resource_spotlight(top_resource)
    with map_col:
        render_map_preview(filtered_resources, top_resource)
    st.markdown("</div>", unsafe_allow_html=True)
    return top_mission, top_resource, recommended_stage


def render_more_candidates(filtered_resources: pd.DataFrame) -> None:
    if len(filtered_resources) <= 1:
        return
    if st.button("다른 후보 숨기기" if st.session_state["show_more_candidates"] else "다른 후보 보기", key="toggle_more_candidates", width="stretch", type="tertiary"):
        st.session_state["show_more_candidates"] = not st.session_state["show_more_candidates"]
        st.session_state["last_action_message"] = "다른 후보를 열었어요." if st.session_state["show_more_candidates"] else "다른 후보를 닫았어요."
        st.rerun()
    if not st.session_state["show_more_candidates"]:
        return
    st.markdown('<div class="rr-progressive-panel"><div class="rr-card-eyebrow">다른 공식 후보</div>', unsafe_allow_html=True)
    for idx, resource in enumerate(filtered_resources.iloc[1:3].to_dict("records"), start=1):
        render_user_resource(resource, f"candidate_{idx}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_bottom_action_bar(profile: UserProfile, mission: dict[str, Any] | None, recommended_stage: int) -> None:
    if not mission:
        return
    with st.container(key="route_action_bar"):
        c1, c2 = st.columns([1.25, 0.75], gap="small")
        if c1.button("오늘 이걸로 시작", key="route_start_primary", width="stretch", type="primary"):
            record_mission_action(profile, mission, ProgressStatus.started, recommended_stage)
        if c2.button("완료", key="route_complete", width="stretch"):
            record_mission_action(profile, mission, ProgressStatus.completed, recommended_stage)
        c3, c4 = st.columns(2, gap="small")
        if c3.button("나중에", key="route_skip", width="stretch", type="tertiary"):
            record_mission_action(profile, mission, ProgressStatus.skipped, recommended_stage)
        if c4.button("어려움", key="route_too_hard", width="stretch", type="tertiary"):
            record_mission_action(profile, mission, ProgressStatus.too_hard, recommended_stage)


def render_hidden_record_panel(profile: UserProfile, resources: pd.DataFrame, missions: list[dict[str, Any]]) -> None:
    if st.button("활동 결과 기록", key="toggle_record_panel", width="stretch", type="tertiary"):
        st.session_state["show_record_panel"] = not st.session_state["show_record_panel"]
        st.session_state["last_action_message"] = "활동 결과 기록을 열었어요." if st.session_state["show_record_panel"] else "활동 결과 기록을 닫았어요."
        st.rerun()
    if st.session_state["show_record_panel"]:
        st.markdown('<div class="rr-progressive-panel">', unsafe_allow_html=True)
        render_outcome_form(profile, resources, missions, "today")
        st.markdown("</div>", unsafe_allow_html=True)


def render_history_cards(progress_df: pd.DataFrame, outcome_df: pd.DataFrame, resources_df: pd.DataFrame, missions_df: pd.DataFrame) -> None:
    progress_view = user_progress_frame(progress_df, missions_df) if not progress_df.empty else pd.DataFrame()
    outcome_view = user_outcome_frame(outcome_df, resources_df, missions_df) if not outcome_df.empty else pd.DataFrame()
    if progress_view.empty and outcome_view.empty:
        st.markdown(
            """
            <div class="rr-empty-note">아직 기록이 없습니다. 내 루트에서 오늘 할 행동을 시작하면 여기에 남습니다.</div>
            """,
            unsafe_allow_html=True,
        )
        return
    st.markdown('<div class="rr-history-list">', unsafe_allow_html=True)
    for _, row in progress_view.tail(4).iterrows():
        st.markdown(
            f"""
            <div class="rr-history-card">
              <strong>{e(row.get("미션", "오늘 할 행동"))}</strong>
              <span>{e(row.get("상태", ""))} · {e(row.get("기록 시각", ""))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    for _, row in outcome_view.tail(4).iterrows():
        st.markdown(
            f"""
            <div class="rr-history-card">
              <strong>{e(row.get("활동/지원 대상", "활동 기록"))}</strong>
              <span>{e(row.get("결과", ""))} · {e(row.get("기록 시각", ""))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_operator_panel() -> None:
    st.subheader("운영자 검증")
    profile, analysis = current_profile_and_analysis()
    data = cached_data()
    stage = int(analysis["recommended_stage"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rule Stage", stage)
    c2.metric("ML 보조 Stage", analysis["model_info"].get("ml_predicted_stage", "N/A"))
    c3.metric("Safety", "분기" if analysis["safety_flag"] else "정상")
    c4.metric("Data Version", analysis["model_info"].get("data_version", "unknown"))

    resources_df = data["resources"]
    source_kinds = ", ".join(sorted(source_kind_label(value) for value in resources_df.get("source_kind", pd.Series(dtype=str)).dropna().unique()))
    checked = format_checked_at(resources_df.get("source_checked_at", pd.Series([""])).dropna().max())
    st.markdown("#### 데이터 수집 상태")
    o1, o2, o3, o4 = st.columns(4)
    o1.metric("공식 자원", len(resources_df))
    o2.metric("출처", resources_df.get("source_name", pd.Series(dtype=str)).nunique())
    o3.metric("수집 방식", source_kinds or "확인 필요")
    o4.metric("확인 시각", checked)

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
    contact_mode = resource_filter_col3.selectbox(
        "접촉 방식",
        list(CONTACT_LABELS.keys()),
        format_func=lambda x: CONTACT_LABELS[x],
        key="research_contact",
    )
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
        review_status = st.selectbox(
            "검토 결과",
            ["verified", "needs_follow_up", "rework_requested"],
            format_func=lambda value: OUTCOME_STATUS_LABELS[value],
        )
        operator_note = st.text_area("운영자 메모", placeholder="예: 미션 난이도 적합, 다음에는 부담도 1 낮춘 미션 권장")
        submitted_review = st.form_submit_button("검토 저장", key="operator_review_submit", width="stretch")
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
        "stage_metrics": metadata.get("stage_metrics", {}),
        "mission_success_metrics": metadata.get("mission_success_metrics", {}),
    }
    st.json(metrics)
    st.markdown(f"- Reports: `{cfg.reports_dir}`")
    st.markdown(f"- Models: `{cfg.model_dir}`")


init_session_state()
show_operator_tools = operator_mode_enabled()
render_app_shell()
apply_explicit_theme_css()

if st.session_state.get("last_action_message"):
    st.success(st.session_state.pop("last_action_message"))

tab_labels = ["내 루트", "정책·문화 찾기", "내 기록"]
if show_operator_tools:
    tab_labels.append("운영자 검증")
tabs = st.tabs(tab_labels)

with tabs[0]:
    data = cached_data()
    resources_df = data["resources"]
    render_route_builder()
    profile, analysis = current_profile_and_analysis()
    filtered_resources = filter_resources_for_user(
        resources_df,
        query=st.session_state["resource_query"],
        district=str(st.session_state["district"]),
        resource_types=list(st.session_state["resource_types"]),
        costs=list(st.session_state["resource_costs"]),
        max_burden=int(st.session_state["resource_max_burden"]),
        online_only=bool(st.session_state["resource_online_only"]),
    )
    top_mission, _, recommended_stage = render_today_bento(profile, analysis, filtered_resources)
    missions = analysis.get("next_3_missions", []) if not analysis.get("safety_flag") else []
    if not analysis.get("safety_flag"):
        render_more_candidates(filtered_resources)
        render_hidden_record_panel(profile, filtered_resources, missions)

with tabs[1]:
    st.markdown(
        """
        <div class="rr-page-title">
          <div>
            <h2>정책·문화 찾기</h2>
            <p>공식 출처 기반 자원을 질문으로 검색하고, 결과의 위치와 확인 방법을 봅니다.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    data = cached_data()
    st.markdown('<div class="rr-section-title">공식 자료 검색</div>', unsafe_allow_html=True)
    search_col, filter_col = st.columns([1.15, 0.85], gap="large")
    with search_col:
        st.text_input("검색 질문", key="rag_query")
    with filter_col:
        rag_district = st.selectbox("구/군 필터", available_districts(data["resources"]), key="rag_district")
        rag_burden = st.selectbox("최대 부담도", BURDEN_FILTER_OPTIONS, index=3, format_func=burden_filter_label, key="rag_max_burden")
    if st.button("공식 자료 검색", key="rag_search", width="stretch"):
        district_value = None if rag_district == "전체" else rag_district
        st.session_state["rag_result"] = search_policy_culture_resources(
            st.session_state["rag_query"],
            district=district_value,
            max_burden_level=rag_burden,
            top_k=5,
        )
        st.session_state["last_action_message"] = "공식 자료 검색 결과를 갱신했어요."
        st.rerun()

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
    data = cached_data()
    st.markdown(
        """
        <div class="rr-route-hero">
          <div class="rr-hero-kicker">내 기록</div>
          <div class="rr-hero-title">오늘 남긴 행동만 모아봅니다.</div>
          <p class="rr-hero-copy">시작한 미션과 확인한 공식 자원을 카드로 정리합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    progress_df = get_progress_df(profile.user_id)
    outcome_df = get_outcomes_df(profile.user_id)
    render_history_cards(progress_df, outcome_df, data["resources"], data["missions"])

if show_operator_tools:
    with tabs[3]:
        render_operator_panel()
