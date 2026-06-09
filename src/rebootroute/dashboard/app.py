from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

SRC_ROOT = Path(__file__).resolve().parents[2]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from rebootroute.dashboard.components.layout import render_app_shell
from rebootroute.dashboard.state import init_session_state, operator_mode_enabled
from rebootroute.dashboard.styles import apply_explicit_theme_css, inject_global_css
from rebootroute.dashboard.views.operator_view import render_operator_panel
from rebootroute.dashboard.views.records_view import render_records_view
from rebootroute.dashboard.views.route_view import render_route_view
from rebootroute.dashboard.views.search_view import render_search_view


st.set_page_config(page_title="RebootRoute", page_icon="RR", layout="wide", initial_sidebar_state="collapsed")


def main() -> None:
    inject_global_css()
    init_session_state()
    show_operator_tools = operator_mode_enabled()
    render_app_shell()
    apply_explicit_theme_css()

    if st.session_state.get("last_action_message"):
        st.success(st.session_state.pop("last_action_message"))

    tab_labels = ["내 루트", "정책·문화 찾기", "내 기록"]
    if show_operator_tools:
        tab_labels.append("운영자 검증")
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        render_route_view()
    with tabs[1]:
        render_search_view()
    with tabs[2]:
        render_records_view()
    if show_operator_tools:
        with tabs[3]:
            render_operator_panel()


main()
