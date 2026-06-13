from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from rebootroute.dashboard.state import operator_mode_enabled, route_choices_complete


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"


@st.cache_data(show_spinner=False)
def asset_data_uri(filename: str) -> str:
    path = ASSET_DIR / filename
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_top_utility() -> None:
    with st.container(key="top_utility"):
        if operator_mode_enabled():
            st.link_button("사용자 화면", "/", type="secondary")
        else:
            st.link_button("개발자 모드", "?operator=1", type="secondary")


def render_app_shell() -> None:
    hero_src = asset_data_uri("rebootroute_route_planning_scene.png") or asset_data_uri("rebootroute_hero_route.png")
    compact = route_choices_complete()
    with st.container(key="app_hero"):
        copy_col, image_col = st.columns([0.64, 0.36] if compact else [0.55, 0.45], gap="medium")
        with copy_col:
            st.markdown(
                f"""
                <div class="rr-hero-copy-block {'compact' if compact else ''}">
                  <h1>RebootRoute</h1>
                  <p class="rr-hero-subtitle">오늘 가능한 만큼만, 인천의 정책·문화 정보를 한 걸음으로 묶습니다.</p>
                  <p class="rr-hero-lead">시간, 대면 부담, 관심 분야, 비용을 고르면 오늘 확인할 공식 자료와 바로 끝낼 작은 행동, 위치 확인을 함께 보여줍니다.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with image_col:
            st.markdown(
                f"""
                <div class="rr-hero-visual {'compact' if compact else ''}" role="img" aria-label="RebootRoute 서비스 이미지"
                  style="background-image:url(&quot;{hero_src}&quot;);"></div>
                """,
                unsafe_allow_html=True,
            )


def render_project_overview() -> None:
    overview_src = asset_data_uri("rebootroute_route_planning_scene.png")
    with st.container(key="project_overview"):
        st.markdown(
            f"""
            <section class="rr-project-overview" aria-label="RebootRoute 설명">
              <div class="rr-project-visual" role="img" aria-label="공식 자료와 오늘 루트를 정리하는 장면"
                style="background-image:url(&quot;{overview_src}&quot;);">
                <div class="rr-project-floating-card">
                  <h2>인천 정보를<br>오늘 할 순서로 정리합니다</h2>
                  <p>먼저 공식 자료를 훑고, 지금 가능한 시간과 대면 부담, 비용 조건을 고르면 오늘 확인할 자료와 10~20분 안에 끝낼 작은 행동을 연결합니다.</p>
                </div>
              </div>
              <div class="rr-project-points" aria-label="서비스 사용 방식">
                <div>
                  <strong>공식 자료 확인</strong>
                  <span>신청 기간, 장소, 비용, 참여 조건은 연결된 인천 공식 페이지에서 최종 확인하도록 안내합니다.</span>
                </div>
                <div>
                  <strong>작은 행동 추천</strong>
                  <span>집에서 가능한 문의 문장 작성부터 짧은 방문 동선 확인까지 부담을 낮춘 다음 단계를 제안합니다.</span>
                </div>
                <div>
                  <strong>지도와 기록 연결</strong>
                  <span>장소가 있는 자료는 위치를 함께 보고 시작, 완료, 나중에, 어려움 기록으로 다음 추천에 반영합니다.</span>
                </div>
              </div>
            </section>
            """,
            unsafe_allow_html=True,
        )


def render_footer() -> None:
    st.markdown(
        """
        <footer class="rr-footer">
          <div class="rr-footer-brand">
            <strong>RebootRoute</strong>
            <span>인천 청년정책·청년공간·문화행사 정보를 오늘 확인할 수 있는 작은 행동으로 정리하는 MVP입니다.</span>
          </div>
          <div class="rr-footer-card">
            <strong>공식 정보 확인</strong>
            <span>신청 기간, 장소, 비용, 참여 조건은 연결된 인천 공식 페이지에서 최종 확인하도록 설계했습니다.</span>
          </div>
          <div class="rr-footer-card">
            <strong>서비스 범위</strong>
            <span>진단, 치료, 상담 챗봇이 아닙니다. 자해·폭력·즉시 위험 표현은 일반 추천 대신 전문기관 안내로 전환합니다.</span>
          </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )
