from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlencode

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from rebootroute.dashboard.components.buttons import render_mission_action_buttons, render_secondary_link
from rebootroute.dashboard.state import (
    ACCESS_MODE_OPTIONS,
    BUDGET_OPTIONS,
    BURDEN_FILTER_OPTIONS,
    CONTACT_LABELS,
    COST_LABELS,
    COST_SCOPE_OPTIONS,
    DEFAULT_STATE,
    DISTRICTS,
    LEVEL_OPTIONS,
    OUTCOME_STATUS_LABELS,
    OUTCOME_TYPE_LABELS,
    RESOURCE_SCOPE_OPTIONS,
    RESOURCE_TYPE_LABELS,
    STAGE_LABELS,
    TIME_OPTIONS,
    as_bool,
    budget_option_label,
    burden_filter_label,
    burden_text,
    current_theme_mode,
    current_user_location,
    display_minutes,
    display_text,
    district_center,
    e,
    format_checked_at,
    format_period,
    level_option_label,
    map_position,
    next_action_items,
    normalize_option_key,
    record_outcome,
    reset_demo_state,
    resource_source_url,
    source_kind_label,
    time_option_label,
    user_outcome_frame,
    user_progress_frame,
)
from rebootroute.schemas import UserProfile


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"


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
        return asset_data_uri("rebootroute_culture_event.png")
    if resource_type == "culture_facility":
        return asset_data_uri("rebootroute_youth_space.png")
    if resource_type == "support_program":
        return asset_data_uri("rebootroute_policy_support.png")
    return asset_data_uri("rebootroute_empty_planning.png")


def resource_image_src(resource: dict[str, Any]) -> str:
    thumbnail_url = display_text(resource.get("thumbnail_url"))
    if thumbnail_url.startswith(("https://", "http://")):
        return thumbnail_url
    return fallback_image_for_resource(str(resource.get("resource_type", "")))


def resource_art_html(resource: dict[str, Any], class_name: str) -> str:
    image_src = resource_image_src(resource)
    name = display_text(resource.get("name")) or "공식 자원"
    thumbnail_url = display_text(resource.get("thumbnail_url"))
    if thumbnail_url.startswith(("https://", "http://")):
        return (
            f'<div class="{e(class_name)} has-image" role="img" aria-label="{e(name)} 공식 이미지" '
            f'style="background-image:url(&quot;{e(image_src)}&quot;);">'
            '<span>공식 이미지</span>'
            "</div>"
        )
    return (
        f'<div class="{e(class_name)} no-image" role="img" aria-label="{e(name)} 이미지 없음">'
        "<span>공식 이미지 없음</span>"
        "</div>"
    )


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


def resource_destination_label(resource: dict[str, Any]) -> str:
    parts = [
        display_text(resource.get("official_place")),
        display_text(resource.get("address")),
        display_text(resource.get("district")),
        display_text(resource.get("name")),
    ]
    for part in parts:
        if part:
            return part
    return "장소는 공식 페이지에서 확인"


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
        f3.selectbox("먼저 볼 방식", ACCESS_MODE_OPTIONS, key="resource_access_mode")
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
        st.text_area("원하는 조건 메모", height=68, key="free_text", placeholder="예: 오늘은 집에서 먼저 확인할 수 있는 활동만 보고 싶어요.")
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
          <div class="rr-section-title">오늘의 작은 미션</div>
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
    online_text = "온라인 확인 가능" if as_bool(resource.get("online_available")) else "방문 전 공식 페이지 확인"
    distance = resource.get("distance_km")
    distance_text = f" · 내 위치에서 약 {float(distance):.1f}km" if distance is not None and pd.notna(distance) else ""
    official_place = display_text(resource.get("official_place")) or address
    st.markdown(
        f"""
        <div class="rr-resource-card">
          <div class="rr-card-with-media">
            {resource_art_html(resource, "rr-resource-thumb")}
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
    official_place = display_text(resource.get("official_place")) or display_text(resource.get("address"))
    period = format_period(resource)
    st.markdown(
        f"""
        <div class="rr-featured-resource">
          <div class="rr-card-with-media">
            {resource_art_html(resource, "rr-resource-thumb")}
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


def fact(text: str) -> str:
    return f'<span class="rr-mini-fact">{e(text)}</span>'


def compact_description(text: Any, limit: int = 115) -> str:
    clean = " ".join(display_text(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "..."


def _has_raw_schedule_parts(text: str) -> bool:
    return any(marker in text for marker in ["접수중", "진행중", "신청기간", "진행기간", "특강 접수중", " · #", "· #"])


def _drop_raw_schedule_parts(text: str) -> str:
    parts = [part.strip() for part in text.split("·") if part.strip()]
    keep = [
        part
        for part in parts
        if "접수" not in part
        and "진행중" not in part
        and "신청기간" not in part
        and "진행기간" not in part
        and not part.startswith("#")
        and "문  의" not in part
        and "문의" not in part
    ]
    return " · ".join(keep).strip()


def user_resource_summary(resource: dict[str, Any], resource_type: str) -> str:
    description = display_text(resource.get("description"))
    official_summary = display_text(resource.get("official_summary"))
    if resource.get("resource_type") == "culture_event":
        return f"{resource_type}입니다. 일정, 장소, 관람 조건은 공식 페이지에서 확인하세요."
    if "공식 프로그램입니다" in description or resource.get("resource_type") == "youth_program":
        return f"{resource_type}입니다. 장소와 참여 조건은 공식 페이지에서 확인하세요."
    if (
        "공식 공간대관 자원입니다" in description
        or "공간대관" in description
        or "신청 후 승인" in description
        or resource.get("resource_type") == "culture_facility"
    ):
        return f"{resource_type}입니다. 이용 방법과 위치는 공식 페이지에서 확인하세요."
    if "문화행사입니다" in description:
        return compact_description(description.split("·", 1)[0], limit=92)
    if _has_raw_schedule_parts(description):
        cleaned = _drop_raw_schedule_parts(description)
        if cleaned and cleaned != description:
            return compact_description(cleaned, limit=92)
    if description:
        return description
    if official_summary:
        cleaned = _drop_raw_schedule_parts(official_summary)
        if cleaned:
            return compact_description(cleaned, limit=92)
    return "대상, 장소, 참여 조건은 공식 페이지에서 확인하세요."


def render_today_mission_card(profile: UserProfile, mission: dict[str, Any] | None, recommended_stage: int) -> None:
    if not mission:
        st.markdown(
            """
            <div class="rr-bento-card mission">
              <div class="rr-card-eyebrow">오늘 바로 할 행동</div>
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
          <div class="rr-card-eyebrow">오늘 바로 할 행동</div>
          <div class="rr-bento-title">{e(mission["title"])}</div>
          <div class="rr-mission-detail-grid">
            <div>
              <span>오늘 할 일</span>
              <strong>{e(mission["description"])}</strong>
            </div>
            <div>
              <span>완료 기준</span>
              <strong>공식 페이지에서 시간·장소·비용 중 하나를 확인하면 완료입니다.</strong>
            </div>
          </div>
          <div class="rr-mini-facts">
            {fact("부담 " + burden_text(mission["burden_level"]))}
            {fact("예상 " + str(int(mission["expected_minutes"])) + "분")}
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
    source_name = display_text(resource.get("source_name")) or "공식 출처"
    source_url = resource_source_url(resource)
    resource_type = RESOURCE_TYPE_LABELS.get(str(resource.get("resource_type")), display_text(resource.get("resource_type")) or "공식 자료")
    cost_text = COST_LABELS.get(str(resource.get("cost_type")), display_text(resource.get("cost_type")) or "공식 페이지 확인")
    online_text = "온라인 확인 가능" if as_bool(resource.get("online_available")) else "방문 전 공식 페이지 확인"
    period = format_period(resource)
    place = resource_destination_label(resource)
    district = display_text(resource.get("district")) or "인천"
    description = user_resource_summary(resource, resource_type)
    st.markdown(
        f"""
        <div class="rr-bento-card resource rr-resource-spotlight">
          {resource_art_html(resource, "rr-resource-art-large")}
          <div class="rr-resource-copy">
            <div class="rr-card-eyebrow">추천 공식 자료 Top</div>
            <div class="rr-bento-title">{e(display_text(resource.get("name")) or "공식 자료")}</div>
            <div class="rr-resource-kind">{e(resource_type)} · {e(district)}</div>
            <div class="rr-resource-summary">{e(description)}</div>
            <div class="rr-resource-quickfacts">
              <div><span>기간</span><strong>{e(period)}</strong></div>
              <div><span>장소</span><strong>{e(place)}</strong></div>
              <div><span>비용</span><strong>{e(cost_text)}</strong></div>
              <div><span>확인 방식</span><strong>{e(online_text)}</strong></div>
            </div>
            <div class="rr-official-line">공식 출처: {e(source_name)}</div>
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


def render_google_map_preview(resource: dict[str, Any], *, expanded: bool, key_suffix: str) -> None:
    dark = current_theme_mode() == "dark"
    card_bg = "#182235" if dark else "#FFFFFF"
    card_border = "#3B4A60" if dark else "#D6DEEA"
    ink = "#F8FAFC" if dark else "#111827"
    muted = "#D1D5DB" if dark else "#374151"
    iframe_height = 420 if expanded else 260
    card_height = iframe_height + 142
    name = display_text(resource.get("name")) or "활동 장소"
    destination = resource_destination_label(resource)
    embed_url = google_maps_embed_url(resource)
    components.html(
        f"""
        <div style="
          box-sizing:border-box;
          width:100%;
          min-height:{card_height}px;
          padding:12px;
          border:1px solid {card_border};
          border-radius:16px;
          background:{card_bg};
          color:{ink};
          font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
        ">
          <div style="font-size:12px;font-weight:760;line-height:1.2;margin:0 0 6px;color:{muted};">장소 확인</div>
          <div style="font-size:16px;font-weight:820;line-height:1.35;margin:0 0 10px;color:{ink};word-break:keep-all;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">{e(name)}</div>
          <iframe
            title="Google Maps - {e(name)}"
            src="{e(embed_url)}"
            width="100%"
            height="{iframe_height}"
            style="display:block;border:0;border-radius:16px;background:#eef2f7;"
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
            allowfullscreen>
          </iframe>
          <div style="display:flex;align-items:center;gap:8px;margin-top:10px;">
            <span style="
              min-width:0;
              overflow:visible;
              white-space:normal;
              word-break:keep-all;
              color:{muted};
              font-size:12px;
              font-weight:700;
              line-height:1.35;
              display:-webkit-box;
              -webkit-line-clamp:2;
              -webkit-box-orient:vertical;
            ">{e(destination)}</span>
          </div>
        </div>
        """,
        height=card_height + 8,
    )
    render_secondary_link("길찾기", google_maps_directions_url(resource), f"map_directions_{key_suffix}")


def render_resource_candidates(resources: pd.DataFrame, *, max_items: int = 8) -> None:
    if len(resources) <= 1:
        return
    candidate_rows = resources.iloc[1 : max_items + 1].to_dict("records")
    total = max(0, len(resources) - 1)
    st.markdown(
        f"""
        <div class="rr-candidate-section">
          <div class="rr-candidate-heading">
            <div>
              <span>추가 추천 자료</span>
              <strong>Top 자료와 함께 볼 공식 자료 {total}건</strong>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for idx, resource in enumerate(candidate_rows, start=1):
        resource_type = RESOURCE_TYPE_LABELS.get(str(resource.get("resource_type")), display_text(resource.get("resource_type")) or "공식 자료")
        cost_text = COST_LABELS.get(str(resource.get("cost_type")), display_text(resource.get("cost_type")) or "공식 페이지 확인")
        online_text = "온라인 확인 가능" if as_bool(resource.get("online_available")) else "공식 페이지 확인"
        source_name = display_text(resource.get("source_name")) or "공식 출처"
        period = format_period(resource)
        place = display_text(resource.get("official_place")) or display_text(resource.get("address")) or str(resource.get("district", "인천"))
        distance = resource.get("distance_km")
        distance_text = f"{float(distance):.1f}km" if distance is not None and pd.notna(distance) else "위치 확인"
        description = user_resource_summary(resource, resource_type)
        st.markdown(
            f"""
            <div class="rr-candidate-card">
              {resource_art_html(resource, "rr-candidate-thumb")}
              <div class="rr-candidate-copy">
                <div class="rr-card-eyebrow">{e(resource_type)} · {e(display_text(resource.get("district")) or "인천")}</div>
                <div class="rr-candidate-title">{e(display_text(resource.get("name")) or "공식 자료")}</div>
                <div class="rr-candidate-description">{e(description)}</div>
                <div class="rr-candidate-meta compact">
                  <div><span>일정</span><strong>{e(period)}</strong></div>
                  <div><span>비용·확인</span><strong>{e(cost_text)} · {e(online_text)}</strong></div>
                </div>
                <div class="rr-official-line">공식 출처: {e(source_name)}</div>
              </div>
              <div class="rr-candidate-place">
                <span>장소 확인</span>
                <strong>{e(place)}</strong>
                <small>{e(distance_text)}</small>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_secondary_link("공식 페이지 열기", resource_source_url(resource), f"resource_source_candidate_{display_text(resource.get('resource_id'))}_{idx}")


def render_map_preview(resources: pd.DataFrame, top_resource: dict[str, Any] | None = None, *, key_suffix: str = "route") -> None:
    expanded = False
    if top_resource:
        render_google_map_preview(top_resource, expanded=expanded, key_suffix=key_suffix)
    else:
        map_class = "expanded" if expanded else "compact"
        max_items = 8 if expanded else 5
        st.markdown(
            f"""
            <div class="rr-bento-card map">
              <div class="rr-card-eyebrow">장소 확인</div>
              <div class="rr-map {map_class}">{map_markers(resources, max_items)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


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


def render_hidden_record_panel(profile: UserProfile, resources: pd.DataFrame, missions: list[dict[str, Any]]) -> None:
    if st.button("활동 결과 기록", key="toggle_record_panel", width="stretch", type="tertiary"):
        st.session_state["show_record_panel"] = not st.session_state["show_record_panel"]
        st.session_state["last_action_message"] = "활동 결과 기록을 열었어요." if st.session_state["show_record_panel"] else "활동 결과 기록을 닫았어요."
        st.rerun()
    if st.session_state["show_record_panel"]:
        st.markdown('<div class="rr-progressive-panel">', unsafe_allow_html=True)
        render_outcome_form(profile, resources, missions, "today")
        st.markdown("</div>", unsafe_allow_html=True)


def render_route_secondary_controls(profile: UserProfile, resources: pd.DataFrame, missions: list[dict[str, Any]]) -> None:
    if len(resources) <= 1 and resources.empty:
        return
    with st.container(key="route_secondary_actions"):
        record_col, spacer_col = st.columns([0.36, 0.64], gap="small")
        if not resources.empty and record_col.button("참여/지원 결과 남기기", key="toggle_record_panel", width="stretch", type="tertiary"):
            st.session_state["show_record_panel"] = not st.session_state["show_record_panel"]
            st.session_state["last_action_message"] = "활동 결과 기록을 열었어요." if st.session_state["show_record_panel"] else "활동 결과 기록을 닫았어요."
            st.rerun()
        spacer_col.empty()
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
