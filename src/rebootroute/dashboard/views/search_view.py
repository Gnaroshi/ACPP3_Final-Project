from __future__ import annotations

import pandas as pd
import streamlit as st

from rebootroute.dashboard.components.cards import render_map_preview, render_user_resource
from rebootroute.dashboard.state import (
    BURDEN_FILTER_OPTIONS,
    add_distance,
    available_districts,
    burden_filter_label,
    cached_data,
    current_user_location,
    e,
)
from rebootroute.rag.retriever import search_policy_culture_resources


def render_search_view() -> None:
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
    search_col, district_col, burden_col, action_col = st.columns([1.45, 0.68, 0.68, 0.52], gap="small")
    with search_col:
        st.text_input("검색 질문", key="rag_query")
    with district_col:
        rag_district = st.selectbox("구/군 필터", available_districts(data["resources"]), key="rag_district")
    with burden_col:
        rag_burden = st.selectbox("최대 부담도", BURDEN_FILTER_OPTIONS, index=3, format_func=burden_filter_label, key="rag_max_burden")
    with action_col:
        st.markdown('<div class="rr-search-action-spacer"></div>', unsafe_allow_html=True)
        if st.button("검색", key="rag_search", width="stretch"):
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
        answer_col, map_col = st.columns([0.58, 0.42], gap="small")
        with answer_col:
            st.markdown(
                f"""
                <div class="rr-panel rr-search-answer">
                  <div class="rr-card-eyebrow">검색 답변</div>
                  <div class="rr-card-title">공식 자료에서 찾은 요약</div>
                  <div class="rr-muted">{e(rag_result["answer"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if not rag_sources_df.empty:
            with map_col:
                render_map_preview(rag_sources_df, rag_sources_df.iloc[0].to_dict(), key_suffix="search")
        for idx, resource in enumerate(rag_sources_df.to_dict("records")):
            render_user_resource(resource, f"rag_{idx}")
