from __future__ import annotations

from typing import Any

import streamlit as st

from rebootroute.dashboard.state import (
    ROUTE_CONTACT_OPTIONS,
    ROUTE_COST_OPTIONS,
    ROUTE_INTENT_OPTIONS,
    ROUTE_RANGE_OPTIONS,
    apply_route_choices_when_changed,
    e,
    record_mission_action,
    sync_derived_resource_filters,
    widget_key,
)
from rebootroute.schemas import ProgressStatus, UserProfile


def render_secondary_link(label: str, url: str, key: str) -> None:
    if not url:
        return
    with st.container(key=widget_key(key)):
        st.link_button(label, url, type="secondary", width="stretch")


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


def render_bottom_action_bar(profile: UserProfile, mission: dict[str, Any] | None, recommended_stage: int) -> None:
    if not mission:
        return
    with st.container(key="route_action_bar"):
        c1, c2, c3, c4 = st.columns([1.35, 0.85, 0.85, 0.85], gap="small")
        if c1.button("오늘 이걸로 시작", key="route_start_primary", width="stretch", type="primary"):
            record_mission_action(profile, mission, ProgressStatus.started, recommended_stage)
        if c2.button("완료", key="route_complete", width="stretch"):
            record_mission_action(profile, mission, ProgressStatus.completed, recommended_stage)
        if c3.button("나중에", key="route_skip", width="stretch", type="tertiary"):
            record_mission_action(profile, mission, ProgressStatus.skipped, recommended_stage)
        if c4.button("어려움", key="route_too_hard", width="stretch", type="tertiary"):
            record_mission_action(profile, mission, ProgressStatus.too_hard, recommended_stage)
