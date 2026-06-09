from __future__ import annotations

import streamlit as st


def render_app_shell() -> None:
    st.markdown(
        """
        <div class="rr-app-shell">
          <div class="rr-brand-lockup">
            <div class="rr-brand-name">RebootRoute</div>
            <div class="rr-brand-tagline">오늘 할 수 있는 인천 정책·문화 루트</div>
            <div class="rr-brand-sub">4가지만 고르면 오늘 확인할 공식 정보와 작은 행동을 추천해요.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
