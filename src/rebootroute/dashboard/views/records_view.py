from __future__ import annotations

import streamlit as st

from rebootroute.dashboard.components.cards import render_history_cards
from rebootroute.dashboard.state import cached_data, current_profile_and_analysis
from rebootroute.database import get_outcomes_df, get_progress_df


def render_records_view() -> None:
    profile, _ = current_profile_and_analysis()
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
