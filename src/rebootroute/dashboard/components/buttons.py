from __future__ import annotations

from typing import Any

import streamlit as st

from rebootroute.dashboard.components.layout import asset_data_uri
from rebootroute.dashboard.state import (
    ROUTE_CONTACT_OPTIONS,
    ROUTE_COST_OPTIONS,
    ROUTE_INTENT_OPTIONS,
    ROUTE_RANGE_OPTIONS,
    apply_route_choices_when_changed,
    e,
    record_mission_action,
    route_choices_complete,
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
    compact = route_choices_complete()
    with st.container(key="route_choices"):
        groups = [
            (
                "오늘 쓸 수 있는 시간",
                "집에서만 확인할지, 짧게 이동할 수 있는지 정합니다.",
                ROUTE_RANGE_OPTIONS,
                "route_range_choice",
                "rebootroute_map_preview.png",
            ),
            (
                "사람 만나는 부담",
                "비대면 확인부터 소규모 참여까지 가능한 범위를 정합니다.",
                ROUTE_CONTACT_OPTIONS,
                "route_contact_choice",
                "rebootroute_youth_space.png",
            ),
            (
                "먼저 보고 싶은 자료",
                "지원금, 청년공간, 문화행사, 프로그램 중 우선순위를 고릅니다.",
                ROUTE_INTENT_OPTIONS,
                "route_intent_choice",
                "rebootroute_policy_support.png",
            ),
            (
                "오늘 쓸 비용",
                "무료만 볼지, 저비용 활동까지 포함할지 정합니다.",
                ROUTE_COST_OPTIONS,
                "route_cost_choice",
                "rebootroute_culture_event.png",
            ),
        ]
        row_size = 4 if compact else 2
        for start in range(0, len(groups), row_size):
            cols = st.columns(row_size, gap="small")
            for offset, (col, (label, caption, options, key, image_name)) in enumerate(zip(cols, groups[start : start + row_size], strict=False), start=1):
                with col:
                    current = st.session_state.get(key)
                    index = options.index(current) if current in options else None
                    step_number = start + offset
                    image_src = asset_data_uri(image_name)
                    st.markdown(
                        f"""
                        <div class="rr-choice-copy {'compact' if compact else ''}">
                          <div class="rr-choice-thumb" role="img" aria-label="{e(label)} 이미지" style="background-image:url(&quot;{e(image_src)}&quot;);"></div>
                          <span><em>{step_number}</em>{e(label)}</span>
                          <small>{e(caption)}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.selectbox(
                        label,
                        options,
                        index=index,
                        key=key,
                        placeholder="선택",
                        label_visibility="collapsed",
                        width="stretch",
                    )
    apply_route_choices_when_changed()
    sync_derived_resource_filters()


def render_bottom_action_bar(profile: UserProfile, mission: dict[str, Any] | None, recommended_stage: int) -> None:
    if not mission:
        return
    with st.container(key="route_action_bar"):
        action_cols = st.columns([1.75, 0.9, 0.9, 0.9], gap="small")
        c1, c2, c3, c4 = action_cols[:4]
        if c1.button("오늘 이걸로 시작", key="route_start_primary", width="stretch", type="primary"):
            record_mission_action(profile, mission, ProgressStatus.started, recommended_stage)
        if c2.button("완료", key="route_complete", width="stretch"):
            record_mission_action(profile, mission, ProgressStatus.completed, recommended_stage)
        if c3.button("나중에", key="route_skip", width="stretch", type="tertiary"):
            record_mission_action(profile, mission, ProgressStatus.skipped, recommended_stage)
        if c4.button("어려움", key="route_too_hard", width="stretch", type="tertiary"):
            record_mission_action(profile, mission, ProgressStatus.too_hard, recommended_stage)


def render_route_action_feedback() -> None:
    feedback = st.session_state.get("last_route_action")
    if not isinstance(feedback, dict):
        return
    status = e(feedback.get("status", "started"))
    label = e(feedback.get("label", "기록 저장"))
    title = e(feedback.get("title", "기록했습니다."))
    message = e(feedback.get("message", "내 기록에서 확인할 수 있습니다."))
    next_step = e(feedback.get("next", "다음 행동을 이어서 선택하세요."))
    st.markdown(
        f"""
        <div class="rr-action-feedback {status}" role="status" aria-live="polite">
          <div class="rr-action-feedback-label">{label}</div>
          <div class="rr-action-feedback-copy">
            <strong>{title}</strong>
            <span>{message}</span>
            <small>{next_step}</small>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.pop("last_route_action", None)
    st.session_state.pop("last_action_message", None)
