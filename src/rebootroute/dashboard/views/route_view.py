from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from rebootroute.dashboard.components.buttons import render_bottom_action_bar, render_choice_chips
from rebootroute.dashboard.components.cards import (
    render_hidden_record_panel,
    render_map_preview,
    render_more_candidates,
    render_resource_spotlight,
    render_safety_branch,
    render_today_mission_card,
)
from rebootroute.dashboard.state import (
    ACCESS_MODE_OPTIONS,
    BURDEN_FILTER_OPTIONS,
    COST_SCOPE_OPTIONS,
    DISTRICTS,
    LEVEL_OPTIONS,
    RESOURCE_SCOPE_OPTIONS,
    burden_filter_label,
    cached_data,
    current_profile_and_analysis,
    filter_resources_for_user,
    level_option_label,
    sync_derived_resource_filters,
)
from rebootroute.schemas import UserProfile


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
        <div class="rr-section-heading">
          <span>조건 선택</span>
          <strong>4개만</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_choice_chips()
    render_advanced_controls()


def render_today_bento(profile: UserProfile, analysis: dict[str, Any], filtered_resources: pd.DataFrame) -> tuple[dict[str, Any] | None, dict[str, Any] | None, int]:
    if analysis.get("safety_flag"):
        render_safety_branch(analysis)
        return None, None, 0
    recommended_stage = int(analysis["recommended_stage"])
    missions = analysis.get("next_3_missions", [])
    top_mission = missions[0] if missions else None
    top_resource = filtered_resources.iloc[0].to_dict() if not filtered_resources.empty else None
    st.markdown('<div class="rr-bento-row">', unsafe_allow_html=True)
    mission_col, resource_col, map_col = st.columns([0.98, 0.92, 0.78], gap="small")
    with mission_col:
        render_today_mission_card(profile, top_mission, recommended_stage)
    with resource_col:
        render_resource_spotlight(top_resource)
    with map_col:
        render_map_preview(filtered_resources, top_resource)
    st.markdown("</div>", unsafe_allow_html=True)
    render_bottom_action_bar(profile, top_mission, recommended_stage)
    return top_mission, top_resource, recommended_stage


def render_route_view() -> None:
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
    render_today_bento(profile, analysis, filtered_resources)
    missions = analysis.get("next_3_missions", []) if not analysis.get("safety_flag") else []
    if not analysis.get("safety_flag"):
        render_more_candidates(filtered_resources)
        render_hidden_record_panel(profile, filtered_resources, missions)
