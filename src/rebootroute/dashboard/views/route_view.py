from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from rebootroute.dashboard.components.buttons import render_bottom_action_bar, render_choice_chips, render_route_action_feedback
from rebootroute.dashboard.components.cards import (
    render_map_preview,
    render_route_secondary_controls,
    render_resource_spotlight,
    render_safety_branch,
    render_today_mission_card,
    resource_image_src,
    user_resource_summary,
)
from rebootroute.dashboard.components.layout import asset_data_uri
from rebootroute.dashboard.state import (
    ACCESS_MODE_OPTIONS,
    BURDEN_FILTER_OPTIONS,
    COST_SCOPE_OPTIONS,
    DISTRICTS,
    LEVEL_OPTIONS,
    RESOURCE_TYPE_LABELS,
    RESOURCE_SCOPE_OPTIONS,
    burden_filter_label,
    cached_data,
    current_profile_and_analysis,
    display_text,
    e,
    filter_resources_for_user,
    format_period,
    level_option_label,
    route_choices_complete,
    sync_derived_resource_filters,
)
from rebootroute.schemas import UserProfile


def render_advanced_toggle() -> None:
    toggle_label = "세부 조건 접기" if st.session_state["show_advanced_controls"] else "세부 조건 더 조정하기"
    if st.button(toggle_label, key="toggle_advanced_controls", type="tertiary"):
        st.session_state["show_advanced_controls"] = not st.session_state["show_advanced_controls"]
        st.session_state.pop("last_action_message", None)
        st.rerun()


def render_advanced_control_fields() -> None:
    if not st.session_state["show_advanced_controls"]:
        return
    st.markdown('<div class="rr-progressive-panel"><div class="rr-card-eyebrow">지역·조건 직접 조정</div>', unsafe_allow_html=True)
    st.markdown('<div class="rr-compact-controls">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.selectbox("내가 있는 곳", DISTRICTS, key="district")
    c2.selectbox("자료 종류", list(RESOURCE_SCOPE_OPTIONS.keys()), key="resource_scope")
    c3.selectbox("비용 범위", list(COST_SCOPE_OPTIONS.keys()), key="resource_cost_scope")
    c4.selectbox("최대 부담", BURDEN_FILTER_OPTIONS, format_func=burden_filter_label, key="resource_max_burden")
    c5, c6, c7, c8 = st.columns(4)
    c5.selectbox("먼저 볼 방식", ACCESS_MODE_OPTIONS, key="resource_access_mode")
    c6.selectbox("오늘 여유", LEVEL_OPTIONS, format_func=level_option_label, key="energy_level")
    c7.selectbox("취업 관련 부담", LEVEL_OPTIONS, format_func=level_option_label, key="employment_burden")
    c8.selectbox("새 활동 부담", LEVEL_OPTIONS, format_func=level_option_label, key="future_anxiety")
    st.text_input("추가 검색어", placeholder="예: 전시, 청년공간, 구직활동비", key="resource_query")
    st.text_area("원하는 조건 메모", height=64, key="free_text", placeholder="예: 오늘은 집에서 확인할 수 있는 활동만 보고 싶어요.")
    st.markdown("</div></div>", unsafe_allow_html=True)
    sync_derived_resource_filters()


def render_advanced_controls() -> None:
    render_advanced_toggle()
    render_advanced_control_fields()


def render_route_builder() -> None:
    compact_detail = route_choices_complete()
    with st.container(key="route_choice_panel"):
        with st.container(key="route_builder_heading"):
            if compact_detail:
                heading_col, action_col = st.columns([0.74, 0.26], gap="small")
                with heading_col:
                    st.markdown(
                        """
                    <div class="rr-route-heading-copy compact">
                      <div>오늘 조건</div>
                      <p>선택한 조건으로 오늘 확인할 공식 자료와 작은 행동을 계산했습니다.</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with action_col:
                    render_advanced_toggle()
            else:
                st.markdown(
                    """
                    <div class="rr-route-heading-copy">
                      <div>오늘의 조건</div>
                      <p>시간, 대면 부담, 관심 자료, 비용을 고르면 미션, 공식 페이지, 위치 안내가 한 화면에 열립니다.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        render_choice_chips()
        if not compact_detail:
            with st.container(key="route_detail_bar"):
                detail_copy, detail_action = st.columns([0.72, 0.28], gap="small")
                with detail_copy:
                    st.markdown(
                        """
                        <div class="rr-detail-copy">
                          <strong>세부 조건</strong>
                          <span>동네, 검색어, 부담도처럼 결과를 더 좁히고 싶을 때만 사용합니다.</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with detail_action:
                    render_advanced_toggle()
        render_advanced_control_fields()


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
        <div class="rr-results-heading">
          <span>오늘 루트</span>
          <h2>미션, 공식 자료, 장소를 한 번에 확인합니다</h2>
          <p>조건에 맞춰 고른 작은 행동과 가장 먼저 열어볼 공식 자료, 이동이 필요한 경우의 장소 안내를 같은 영역에 모았습니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="route_results_grid"):
        mission_col, resource_col, map_col = st.columns([1.05, 1.05, 0.9], gap="medium")
        with mission_col:
            render_today_mission_card(profile, top_mission, recommended_stage)
            render_bottom_action_bar(profile, top_mission, recommended_stage)
            render_route_action_feedback()
        with resource_col:
            render_resource_spotlight(top_resource)
        with map_col:
            render_map_preview(filtered_resources, top_resource)
    return top_mission, top_resource, recommended_stage


def _resource_summary(resource: dict[str, Any], *, max_chars: int = 96) -> str:
    resource_type = RESOURCE_TYPE_LABELS.get(str(resource.get("resource_type")), "공식 자료")
    value = display_text(user_resource_summary(resource, resource_type))
    if value:
        if len(value) > max_chars:
            return f"{value[:max_chars].rstrip()}..."
        return value
    return "공식 페이지에서 기간, 장소, 비용, 신청 가능 여부를 확인할 수 있는 인천 자료입니다."


def _compact_text(value: Any, *, max_chars: int) -> str:
    cleaned = " ".join(display_text(value).split())
    if len(cleaned) <= max_chars:
        return cleaned
    return f"{cleaned[: max_chars - 1].rstrip()}…"


def _resource_period_label(period: str) -> str:
    cleaned = " ".join(display_text(period).split())
    if not cleaned:
        return "일정은 공식 페이지에서 확인"
    if "/" in cleaned or "접수" in cleaned or "진행" in cleaned or len(cleaned) > 30:
        return "일정은 공식 페이지에서 확인"
    return f"일정 {cleaned}"


def _resource_meta(resource: dict[str, Any]) -> tuple[str, str, str, str]:
    name = display_text(resource.get("name")) or "공식 자료"
    resource_type = RESOURCE_TYPE_LABELS.get(str(resource.get("resource_type")), "공식 자료")
    district = display_text(resource.get("district")) or "인천"
    period = format_period(resource)
    return name, resource_type, district, period


def resource_preview_cards_html(resources: pd.DataFrame, *, limit: int = 8) -> str:
    preview_rows = []
    if not resources.empty:
        preferred_types = ["support_program", "culture_event", "culture_facility", "youth_program"]
        for resource_type in preferred_types:
            candidates = resources[resources["resource_type"].astype(str) == resource_type]
            if not candidates.empty:
                preview_rows.append(candidates.iloc[0].to_dict())
        if len(preview_rows) < limit:
            seen_ids = {str(row.get("resource_id")) for row in preview_rows}
            for row in resources.to_dict("records"):
                if str(row.get("resource_id")) not in seen_ids:
                    preview_rows.append(row)
                    seen_ids.add(str(row.get("resource_id")))
                if len(preview_rows) >= limit:
                    break
        if not preview_rows:
            preview_rows = resources.head(limit).to_dict("records")
        preview_rows = preview_rows[:limit]
    if not preview_rows:
        return ""
    cards = []
    for resource in preview_rows:
        name, resource_type, district, period = _resource_meta(resource)
        card_title = _compact_text(name, max_chars=36)
        summary = _resource_summary(resource, max_chars=86)
        period_label = _resource_period_label(period)
        image_src = resource_image_src(resource)
        cards.append(
            '<div class="rr-preview-resource-card standard">'
            f'<div class="rr-preview-resource-image" role="img" aria-label="{e(name)} 이미지" '
            f'style="background-image:url(&quot;{e(image_src)}&quot;);"></div>'
            f'<div class="rr-preview-resource-copy">'
            f'<span class="rr-resource-meta">{e(resource_type)} · {e(district)}</span>'
            f"<strong>{e(card_title)}</strong>"
            f"<p>{e(summary)}</p>"
            f'<small class="rr-preview-date">{e(period_label)}</small>'
            f"</div></div>"
        )
    return f'<div class="rr-preview-resource-list" aria-label="인천 공식 자료 carousel">{"".join(cards)}</div>'


def render_resource_preview_section(resources: pd.DataFrame, *, compact: bool = False) -> None:
    cards_html = resource_preview_cards_html(resources, limit=8)
    if not cards_html:
        return
    title = "조건 선택 전에 볼 공식 자료" if compact else "조건 선택에 참고할 자료"
    body = (
        "청년정책, 청년공간, 문화행사, 프로그램을 먼저 비교해 보세요. 조건을 고르면 오늘 확인하기 좋은 자원과 작은 행동을 연결합니다."
        if compact
        else "청년정책, 청년공간, 문화행사, 프로그램 중 바로 비교할 수 있는 항목입니다. 조건을 고르면 이 자료들 중 오늘 확인하기 좋은 자원과 작은 행동을 연결합니다."
    )
    with st.container(key="route_resource_preview"):
        header_col, action_col = st.columns([0.76, 0.24], gap="medium")
        with header_col:
            st.markdown(
                f"""
                <div class="rr-resource-showcase-header">
                  <span>인천 공식 자료</span>
                  <h2>{e(title)}</h2>
                  <p>{e(body)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with action_col:
            st.markdown('<div class="rr-resource-list-action">', unsafe_allow_html=True)
            show_list = bool(st.session_state.get("show_resource_preview_list", False))
            toggle_label = "목록 접기" if show_list else "전체 자료 보기"
            if st.button(toggle_label, key="toggle_resource_preview_list", type="tertiary"):
                st.session_state["show_resource_preview_list"] = not show_list
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        compact_class = " compact" if compact else ""
        st.markdown(f'<div class="rr-preview-resource-strip showcase{compact_class}">{cards_html}</div>', unsafe_allow_html=True)
        show_list = bool(st.session_state.get("show_resource_preview_list", False))
        if show_list:
            rows = resources.head(8).to_dict("records")
            cards = []
            for resource in rows:
                name, resource_type, district, period = _resource_meta(resource)
                card_title = _compact_text(name, max_chars=42)
                summary = _resource_summary(resource, max_chars=112)
                period_label = _resource_period_label(period)
                image_src = resource_image_src(resource)
                cards.append(
                    '<div class="rr-preview-list-card">'
                    f'<div class="rr-preview-list-image" role="img" aria-label="{e(name)} 이미지" '
                    f'style="background-image:url(&quot;{e(image_src)}&quot;);"></div>'
                    '<div class="rr-preview-list-copy">'
                    f"<span>{e(resource_type)} · {e(district)}</span>"
                    f"<strong>{e(card_title)}</strong>"
                    f"<p>{e(summary)}</p>"
                    f"<small>{e(period_label)}</small>"
                    "</div>"
                    "</div>"
                )
            st.markdown(f'<div class="rr-preview-list-panel">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_waiting_for_choices() -> None:
    guide_image = asset_data_uri("rebootroute_empty_planning.png")
    st.markdown(
        f"""
        <div class="rr-route-empty-state compact">
          <div class="rr-empty-copy">
            <span>추천 준비</span>
            <h3>네 가지 조건을 선택하면 결과 카드가 열립니다</h3>
            <p>선택 전에는 추천을 확정하지 않습니다. 위 공식 자료를 둘러본 뒤 오늘 가능한 시간, 대면 부담, 관심 분야, 비용을 고르면 작은 미션과 공식 페이지, 장소 안내가 함께 열립니다.</p>
          </div>
          <div class="rr-preview-hero-image" role="img" aria-label="오늘 루트 준비 이미지"
            style="background-image:url(&quot;{e(guide_image)}&quot;);"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_route_guide_panel() -> None:
    guide_image = asset_data_uri("rebootroute_empty_planning.png")
    st.markdown(
        f"""
        <section class="rr-route-guide-panel" aria-label="루트 생성 안내">
          <div class="rr-route-guide-copy">
            <span>루트 생성</span>
            <h2>자료를 보고, 조건을 고르면 오늘 루트가 열립니다</h2>
            <p>먼저 공식 자료의 종류를 훑어보고 오늘 가능한 범위를 정합니다. 선택이 끝나면 작은 미션, 공식 페이지, 위치 확인, 기록 버튼이 같은 화면에 나타납니다.</p>
          </div>
          <div class="rr-route-guide-steps">
            <div><em>1</em><strong>조건 선택</strong><span>시간·대면·관심·비용</span></div>
            <div><em>2</em><strong>자료 확인</strong><span>공식 페이지와 핵심 정보</span></div>
            <div><em>3</em><strong>기록 남기기</strong><span>시작·완료·나중에·어려움</span></div>
          </div>
          <div class="rr-route-guide-image" role="img" aria-label="루트 준비 이미지"
            style="background-image:url(&quot;{e(guide_image)}&quot;);"></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_route_view() -> None:
    data = cached_data()
    resources_df = data["resources"]
    if not route_choices_complete():
        with st.container(key="route_start_workspace"):
            render_route_builder()
        return
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
        render_route_secondary_controls(profile, filtered_resources, missions)
