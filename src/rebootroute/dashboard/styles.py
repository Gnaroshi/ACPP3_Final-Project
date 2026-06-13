from __future__ import annotations

from pathlib import Path

import streamlit as st

from rebootroute.dashboard.state import current_theme_mode


CSS_DIR = Path(__file__).with_name("css")
CSS_FILES = (
    "base.css",
    "hero.css",
    "navigation.css",
    "resources.css",
    "route.css",
    "cards.css",
    "results.css",
    "footer.css",
    "responsive.css",
)


@st.cache_data(show_spinner=False)
def _load_css() -> str:
    return "\n\n".join((CSS_DIR / filename).read_text(encoding="utf-8") for filename in CSS_FILES)


def inject_global_css() -> None:
    st.markdown(f"<style>{_load_css()}</style>", unsafe_allow_html=True)


def apply_explicit_theme_css() -> None:
    dark = current_theme_mode() == "dark"
    palette = (
        {
            "bg": "#0b1020",
            "surface": "#111827",
            "surface_soft": "#162034",
            "ink": "#f8fafc",
            "muted": "#cbd5e1",
            "line": "rgba(148, 163, 184, 0.34)",
            "primary": "#a78bfa",
            "primary_dark": "#7c3aed",
            "accent": "#c084fc",
            "shadow": "0 24px 70px rgba(0, 0, 0, 0.35)",
        }
        if dark
        else {
            "bg": "#f7f4ff",
            "surface": "#ffffff",
            "surface_soft": "#f8fafc",
            "ink": "#111827",
            "muted": "#475569",
            "line": "rgba(148, 163, 184, 0.36)",
            "primary": "#7c3aed",
            "primary_dark": "#4c1d95",
            "accent": "#a855f7",
            "shadow": "0 24px 70px rgba(15, 23, 42, 0.10)",
        }
    )
    vars_css = "\n".join(f"    --rr-{key}: {value};" for key, value in palette.items())
    st.markdown(
        f"""
        <style>
          :root {{
        {vars_css}
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )
