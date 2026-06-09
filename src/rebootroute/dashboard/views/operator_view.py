from __future__ import annotations

import pandas as pd
import streamlit as st

from rebootroute.config import load_config
from rebootroute.dashboard.state import (
    CONTACT_LABELS,
    DISTRICTS,
    OUTCOME_STATUS_LABELS,
    UserProfile,
    cached_data,
    current_profile_and_analysis,
    format_checked_at,
    record_outcome,
    source_kind_label,
    technical_mission_frame,
    technical_resource_frame,
)
from rebootroute.database import get_feedback_df, get_outcomes_df, get_progress_df
from rebootroute.modeling.registry import load_metadata
from rebootroute.recommender.mission_recommender import rank_missions
from rebootroute.recommender.resource_recommender import rank_resources
from rebootroute.schemas import ContactMode


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
