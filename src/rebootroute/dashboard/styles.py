from __future__ import annotations

import streamlit as st

from rebootroute.dashboard.state import current_theme_mode


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
          :root {
            --rr-bg: #eef3f7;
            --rr-surface: #ffffff;
            --rr-surface-2: #f6f9fc;
            --rr-ink: #142033;
            --rr-muted: #475569;
            --rr-soft: #64748b;
            --rr-line: #d4dce8;
            --rr-line-strong: #aebbc9;
            --rr-primary: #0b5cab;
            --rr-primary-strong: #063d78;
            --rr-primary-soft: #e6f0fb;
            --rr-info: #16746a;
            --rr-info-soft: #e8f5f2;
            --rr-warm: #9a5700;
            --rr-warm-soft: #fff4df;
            --rr-danger: #a33a32;
            --rr-danger-soft: #fff1ee;
            --rr-shadow: 0 10px 28px rgba(20, 32, 51, 0.08);
            --rr-shadow-soft: 0 5px 14px rgba(20, 32, 51, 0.06);
          }
    
          html, body, .stApp, .stMarkdown, .stText, .stCaption, li, label,
          [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
          [data-testid="stExpander"] summary, [data-testid="stForm"], [data-testid="stAlert"] {
            color: var(--rr-ink) !important;
          }
    
          html, body, .stApp,
          [data-testid="stAppViewContainer"],
          [data-testid="stMain"],
          [data-testid="stMainBlockContainer"],
          section.main {
            background-color: var(--rr-bg) !important;
          }
    
          .stApp {
            background: var(--rr-bg);
          }
    
          .block-container {
            padding-top: 0.8rem;
            padding-bottom: 2.2rem;
            max-width: 1120px;
          }
    
          h1, h2, h3, h4 {
            color: var(--rr-ink) !important;
            letter-spacing: 0 !important;
            line-height: 1.25 !important;
          }
    
          [data-testid="stHeader"],
          [data-testid="stToolbar"],
          [data-testid="stDecoration"],
          [data-testid="stStatusWidget"] {
            display: none !important;
          }
    
          [data-testid="stSidebar"],
          [data-testid="stSidebarContent"],
          section[data-testid="stSidebar"] {
            background: var(--rr-surface) !important;
            color: var(--rr-ink) !important;
            border-right: 1px solid var(--rr-line) !important;
          }
    
          [data-testid="stSidebar"] *,
          [data-testid="stSidebarContent"] * {
            color: var(--rr-ink) !important;
          }
    
          [data-testid="stSidebar"] p,
          [data-testid="stSidebar"] .stCaption,
          [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: var(--rr-muted) !important;
          }
    
          [data-testid="stSidebarCollapsedControl"],
          [data-testid="collapsedControl"] {
            background: var(--rr-surface) !important;
            border: 1px solid var(--rr-line) !important;
            border-radius: 8px !important;
            color: var(--rr-ink) !important;
          }
    
          a, a:visited { color: var(--rr-primary) !important; }
    
          svg {
            color: var(--rr-muted) !important;
            fill: currentColor !important;
          }
    
          input, textarea, [contenteditable="true"],
          [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
            color: var(--rr-ink) !important;
            background: var(--rr-surface) !important;
            caret-color: var(--rr-primary) !important;
          }
    
          [data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
            background: var(--rr-surface) !important;
            border-color: var(--rr-line) !important;
            color: var(--rr-ink) !important;
            border-radius: 8px !important;
          }
    
          [data-baseweb="input"]:focus-within,
          [data-baseweb="select"]:focus-within > div,
          [data-baseweb="textarea"]:focus-within {
            border-color: var(--rr-primary) !important;
            box-shadow: 0 0 0 2px rgba(29, 78, 216, 0.12) !important;
          }
    
          [data-baseweb="select"] span, [data-baseweb="select"] div,
          [data-baseweb="popover"] li, [role="option"] {
            color: var(--rr-ink) !important;
          }
    
          [data-testid="stCheckbox"],
          [data-testid="stCheckbox"] *,
          [data-testid="stMultiSelect"] *,
          [data-baseweb="tag"] * {
            color: var(--rr-ink) !important;
          }
    
          [data-baseweb="tag"] {
            background: var(--rr-primary-soft) !important;
            border: 1px solid #bfd0ff !important;
          }
    
          [data-baseweb="slider"] div, [data-testid="stThumbValue"] {
            color: var(--rr-ink) !important;
          }
    
          [data-baseweb="slider"] [role="slider"] {
            background: var(--rr-primary) !important;
            border-color: var(--rr-primary) !important;
            box-shadow: 0 0 0 2px #ffffff, 0 0 0 4px rgba(7, 86, 165, 0.2) !important;
          }
    
          [data-baseweb="slider"] [aria-valuenow] {
            background: var(--rr-primary) !important;
          }
    
          [data-baseweb="slider"] > div > div {
            background-color: #d8dee8 !important;
          }
    
          [data-baseweb="slider"] > div > div > div {
            background-color: var(--rr-primary) !important;
          }
    
          [data-testid="stNumberInput"] button,
          [data-testid="stNumberInput"] button:hover,
          [data-testid="stNumberInput"] button:focus {
            background: #f8fafc !important;
            color: var(--rr-primary) !important;
            border-color: var(--rr-line) !important;
          }
    
          [data-testid="stNumberInput"] button * {
            color: var(--rr-primary) !important;
          }
    
          [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--rr-surface) !important;
            border-color: var(--rr-line) !important;
            border-radius: 8px !important;
            box-shadow: var(--rr-shadow-soft) !important;
          }
    
          div[data-testid="stMetric"] {
            background: var(--rr-surface);
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            padding: 0.8rem 0.9rem;
          }
    
          div[data-testid="stMetric"] label,
          [data-testid="stMetricLabel"] {
            color: var(--rr-muted) !important;
          }
    
          [data-testid="stMetricValue"] {
            color: var(--rr-ink) !important;
            font-size: 1.15rem !important;
          }
    
          .stButton > button {
            min-height: 2.48rem;
            border-radius: 8px;
            border: 1px solid var(--rr-primary) !important;
            background: #ffffff !important;
            color: var(--rr-primary) !important;
            font-weight: 800 !important;
            line-height: 1.2 !important;
            white-space: normal !important;
            box-shadow: 0 2px 6px rgba(11, 92, 171, 0.08) !important;
          }
    
          .stButton > button * {
            color: inherit !important;
          }
    
          .stButton > button:hover,
          .stButton > button:focus {
            background: var(--rr-primary-soft) !important;
            border-color: var(--rr-primary-strong) !important;
            color: var(--rr-primary-strong) !important;
          }
    
          [data-testid="stBaseButton-primary"],
          .stFormSubmitButton > button {
            background: var(--rr-primary) !important;
            border-color: var(--rr-primary) !important;
            color: #ffffff !important;
          }
    
          [data-testid="stBaseButton-primary"] *,
          .stFormSubmitButton > button * {
            color: #ffffff !important;
          }
    
          [data-testid="stBaseButton-primary"]:hover,
          .stFormSubmitButton > button:hover {
            background: var(--rr-primary-strong) !important;
            border-color: var(--rr-primary-strong) !important;
            color: #ffffff !important;
          }
    
          [data-baseweb="tab-list"] {
            gap: 0.35rem;
            border-bottom: 1px solid var(--rr-line);
            padding-bottom: 0.28rem;
          }
    
          [data-baseweb="tab-highlight"] {
            background-color: var(--rr-primary) !important;
          }
    
          [data-baseweb="tab-border"] {
            background-color: var(--rr-line) !important;
          }
    
          [data-baseweb="tab"] {
            color: var(--rr-muted) !important;
            border-radius: 999px;
            padding: 0.58rem 0.92rem;
            min-width: max-content;
          }
    
          [data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            background: var(--rr-primary) !important;
            border: 1px solid var(--rr-primary);
            font-weight: 800;
          }
    
          [data-baseweb="tab"][aria-selected="true"] * {
            color: #ffffff !important;
          }
    
          [data-testid="stDataFrame"], [data-testid="stTable"] {
            color: var(--rr-ink) !important;
          }
    
          .rr-topbar {
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            color: var(--rr-muted) !important;
            font-size: 0.78rem;
            line-height: 1.45;
            margin: 0 0 0.25rem;
          }
    
          .rr-app-header {
            background: #14324b;
            border: 1px solid #14324b;
            border-left: 6px solid #1fb39f;
            border-radius: 8px;
            padding: 0.82rem 0.95rem;
            margin-bottom: 0.62rem;
            box-shadow: var(--rr-shadow);
          }
    
          .rr-app-header,
          .rr-app-header * {
            color: #ffffff !important;
          }
    
          .rr-app-title {
            font-size: 1.42rem;
            line-height: 1.2;
            font-weight: 850;
            color: #ffffff !important;
            margin: 0 0 0.16rem 0;
          }
    
          .rr-app-subtitle {
            color: #d8e5ee !important;
            margin: 0;
            font-size: 0.9rem;
            line-height: 1.45;
          }
    
          .rr-header-grid {
            display: grid;
            grid-template-columns: minmax(0, 1fr);
            gap: 1rem;
            align-items: center;
          }
    
          .rr-header-badges {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 0.35rem;
          }
    
          .rr-page-title {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 1rem;
            margin: 0.16rem 0 0.45rem;
          }
    
          .rr-page-title h2 {
            margin: 0 !important;
            font-size: 1.18rem !important;
          }
    
          .rr-page-title p {
            margin: 0.2rem 0 0;
            color: var(--rr-muted) !important;
            font-size: 0.86rem;
            line-height: 1.42;
          }
    
          .rr-panel {
            background: var(--rr-surface);
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            padding: 0.82rem;
            margin: 0.45rem 0;
            box-shadow: var(--rr-shadow-soft);
          }
    
          .rr-filter-panel {
            background: var(--rr-surface);
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.8rem;
          }
    
          .rr-summary-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.5rem;
            margin: 0.5rem 0 0.65rem;
          }
    
          .rr-summary-item {
            background: #f8fafc;
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            padding: 0.54rem 0.62rem;
          }
    
          .rr-summary-item span {
            display: block;
            color: var(--rr-soft) !important;
            font-size: 0.76rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
          }
    
          .rr-summary-item strong {
            display: block;
            color: var(--rr-ink) !important;
            font-size: 0.92rem;
            line-height: 1.35;
          }
    
          .rr-step-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.75rem 0 1rem;
          }
    
          .rr-step {
            background: var(--rr-surface);
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            padding: 0.85rem;
          }
    
          .rr-step-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.55rem;
            height: 1.55rem;
            border-radius: 999px;
            background: var(--rr-primary);
            color: #ffffff !important;
            font-weight: 800;
            margin-right: 0.35rem;
          }
    
          .rr-step strong {
            color: var(--rr-ink) !important;
          }
    
          .rr-step p {
            color: var(--rr-muted) !important;
            font-size: 0.9rem;
            line-height: 1.55;
            margin: 0.45rem 0 0;
          }
    
          .rr-stage-panel {
            background: #ffffff;
            border-color: #9bc1eb;
            border-left: 6px solid var(--rr-primary);
          }
    
          .rr-primary-mission {
            margin-bottom: 0.55rem;
          }
    
          .rr-primary-mission .rr-card-title {
            font-size: 1.1rem;
          }
    
          .rr-section-title {
            color: var(--rr-ink) !important;
            font-size: 0.98rem;
            font-weight: 800;
            margin-bottom: 0.34rem;
          }
    
          .rr-muted {
            color: var(--rr-muted) !important;
            font-size: 0.92rem;
            line-height: 1.6;
          }
    
          .rr-chip {
            display: inline-block;
            padding: 0.18rem 0.52rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 780;
            margin: 0 0.25rem 0.25rem 0;
            border: 1px solid transparent;
          }
    
          .rr-chip.teal { background: var(--rr-primary-soft); color: var(--rr-primary-strong) !important; border-color: #b8d3f0; }
          .rr-chip.blue { background: var(--rr-info-soft); color: var(--rr-info) !important; border-color: #b9ddd7; }
          .rr-chip.gold { background: var(--rr-warm-soft); color: var(--rr-warm) !important; border-color: #f0c894; }
          .rr-chip.gray { background: #edf2f4; color: #3f4e5f !important; border-color: #d4dde1; }
          .rr-chip.rose { background: var(--rr-danger-soft); color: var(--rr-danger) !important; border-color: #f2c2bd; }
    
          .rr-card-title {
            font-size: 0.98rem;
            font-weight: 800;
            color: var(--rr-ink) !important;
            margin-bottom: 0.28rem;
            line-height: 1.35;
          }
    
          .rr-card-body {
            color: var(--rr-muted) !important;
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 0.45rem;
          }
    
          .rr-resource-card {
            background: var(--rr-surface);
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            padding: 0.82rem;
            margin: 0.55rem 0;
          }
    
          .rr-info-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.55rem;
            margin: 0.65rem 0;
          }
    
          .rr-info-item {
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            padding: 0.55rem 0.6rem;
            background: #f8fafc;
            min-height: 3.25rem;
          }
    
          .rr-info-item span {
            display: block;
            color: var(--rr-soft) !important;
            font-size: 0.72rem;
            font-weight: 750;
            margin-bottom: 0.18rem;
          }
    
          .rr-info-item strong {
            color: var(--rr-ink) !important;
            font-size: 0.86rem;
            line-height: 1.3;
          }
    
          .rr-next-action {
            background: var(--rr-warm-soft);
            border: 1px solid #f0d29a;
            border-left: 6px solid #c47700;
            border-radius: 8px;
            padding: 0.78rem;
            margin: 0.5rem 0;
            box-shadow: var(--rr-shadow-soft);
          }
    
          .rr-route-strip {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.4rem;
            margin: 0.12rem 0 0.58rem;
            color: var(--rr-muted) !important;
            font-size: 0.84rem;
            font-weight: 700;
          }
    
          .rr-route-strip span {
            background: #ffffff;
            border: 1px solid var(--rr-line);
            border-radius: 999px;
            padding: 0.22rem 0.55rem;
            color: var(--rr-ink) !important;
            box-shadow: 0 1px 4px rgba(20, 32, 51, 0.05);
          }
    
          .rr-control-note {
            color: var(--rr-muted) !important;
            font-size: 0.82rem;
            line-height: 1.4;
            margin: -0.15rem 0 0.4rem;
          }
    
          .rr-condition-bar {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.5rem;
            margin: 0.1rem 0 0.45rem;
          }
    
          .rr-condition-pill {
            background: var(--rr-surface-2);
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            padding: 0.5rem 0.58rem;
          }
    
          .rr-condition-pill span {
            display: block;
            color: var(--rr-soft) !important;
            font-size: 0.72rem;
            font-weight: 750;
            margin-bottom: 0.12rem;
          }
    
          .rr-condition-pill strong {
            display: block;
            color: var(--rr-ink) !important;
            font-size: 0.9rem;
            line-height: 1.25;
          }
    
          .rr-featured-resource {
            background: #ffffff;
            border: 1px solid #b9ddd7;
            border-left: 6px solid var(--rr-info);
            border-radius: 8px;
            padding: 0.82rem;
            margin: 0.5rem 0;
            box-shadow: var(--rr-shadow-soft);
          }
    
          .rr-featured-resource .rr-info-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            margin-bottom: 0.35rem;
          }
    
          .rr-compact-list {
            margin: 0.45rem 0 0;
            padding-left: 1rem;
          }
    
          .rr-compact-list li {
            color: var(--rr-ink) !important;
            margin: 0.25rem 0;
            line-height: 1.42;
            font-size: 0.9rem;
          }
    
          .rr-resource-meta {
            color: var(--rr-soft) !important;
            font-size: 0.86rem;
            line-height: 1.5;
            margin-top: 0.2rem;
          }
    
          .rr-divider { height: 1px; background: var(--rr-line); margin: 1rem 0; }
    
          .rr-action-list {
            margin: 0.55rem 0 0;
            padding-left: 1.15rem;
          }
    
          .rr-action-list li {
            color: var(--rr-ink) !important;
            margin: 0.35rem 0;
            line-height: 1.55;
          }
    
          .rr-source-link {
            display: inline-block;
            margin-top: 0.45rem;
            font-weight: 800;
            border: 1px solid #b9ddd7;
            background: var(--rr-info-soft);
            color: #0f5f57 !important;
            border-radius: 8px;
            padding: 0.36rem 0.58rem;
            text-decoration: none !important;
          }
    
          .rr-warning {
            background: #fff7ed;
            border: 1px solid #fed7aa;
            border-radius: 8px;
            padding: 1rem;
            color: #7c2d12;
          }
    
          .rr-warning strong { color: #7c2d12; }
    
          .rr-empty-note {
            border: 1px dashed var(--rr-line-strong);
            border-radius: 8px;
            padding: 0.9rem;
            color: var(--rr-muted);
            background: #ffffff;
          }
    
          .rr-flow {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.6rem;
            margin: 0.75rem 0 1rem;
          }
    
          .rr-flow-step {
            background: var(--rr-surface);
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            padding: 0.75rem;
            min-height: 5.1rem;
          }
    
          .rr-flow-step strong {
            display: block;
            color: var(--rr-ink) !important;
            font-size: 0.92rem;
            line-height: 1.35;
            margin-bottom: 0.25rem;
          }
    
          .rr-flow-step span {
            color: var(--rr-muted) !important;
            font-size: 0.84rem;
            line-height: 1.45;
          }
    
          .rr-map {
            position: relative;
            height: 360px;
            overflow: hidden;
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            background:
              linear-gradient(90deg, rgba(29, 78, 216, 0.08) 1px, transparent 1px),
              linear-gradient(rgba(29, 78, 216, 0.08) 1px, transparent 1px),
              linear-gradient(135deg, #eef7f5 0%, #f8fafc 42%, #eef2ff 100%);
            background-size: 52px 52px, 52px 52px, auto;
          }
    
          .rr-map::before {
            content: "INCHEON";
            position: absolute;
            right: 1rem;
            bottom: 0.75rem;
            color: rgba(17, 24, 39, 0.16);
            font-weight: 900;
            letter-spacing: 0.08rem;
          }
    
          .rr-map-marker {
            position: absolute;
            transform: translate(-50%, -50%);
            width: 0.95rem;
            height: 0.95rem;
            border-radius: 999px;
            border: 2px solid #ffffff;
            box-shadow: 0 4px 12px rgba(17, 24, 39, 0.2);
          }
    
          .rr-map-marker.user {
            width: 1.25rem;
            height: 1.25rem;
            background: var(--rr-primary);
          }
    
          .rr-map-marker.place {
            background: var(--rr-info);
          }
    
          .rr-map-label {
            position: absolute;
            transform: translate(0.55rem, -0.6rem);
            min-width: 6.4rem;
            max-width: 11rem;
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.96);
            color: var(--rr-ink) !important;
            font-size: 0.76rem;
            line-height: 1.3;
            font-weight: 800;
            padding: 0.28rem 0.42rem;
          }
    
          .rr-map-label small {
            display: block;
            color: var(--rr-muted) !important;
            font-size: 0.7rem;
            font-weight: 650;
            margin-top: 0.1rem;
          }
    
          .rr-map-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.55rem;
            color: var(--rr-muted) !important;
            font-size: 0.86rem;
          }
    
          .rr-dot {
            display: inline-block;
            width: 0.72rem;
            height: 0.72rem;
            border-radius: 999px;
            margin-right: 0.25rem;
            vertical-align: -0.08rem;
          }
    
          .rr-dot.user { background: var(--rr-primary); }
          .rr-dot.place { background: var(--rr-info); }
    
          @media (max-width: 760px) {
            .block-container {
              padding: 0.75rem 0.85rem 2rem;
            }
    
            .rr-app-header {
              padding: 0.72rem;
            }
    
            .rr-app-title {
              font-size: 1.24rem;
            }
    
            .rr-app-subtitle {
              font-size: 0.9rem;
            }
    
            div[data-testid="column"] {
              width: 100% !important;
              min-width: 100% !important;
              flex: 1 1 100% !important;
            }
    
            [data-testid="stHorizontalBlock"] {
              gap: 0.65rem !important;
            }
    
            [data-baseweb="tab-list"] {
              overflow-x: auto;
              flex-wrap: nowrap;
              scrollbar-width: thin;
            }
    
            [data-baseweb="tab"] {
              padding: 0.65rem 0.75rem;
              font-size: 0.9rem;
            }
    
            .stButton > button {
              min-height: 2.75rem;
              padding-left: 0.65rem;
              padding-right: 0.65rem;
            }
    
            div[data-testid="stMetric"] {
              padding: 0.7rem 0.8rem;
            }
    
            .rr-step-grid {
              grid-template-columns: 1fr;
            }
    
            .rr-flow {
              grid-template-columns: 1fr;
            }
    
            .rr-header-grid,
            .rr-page-title,
            .rr-featured-resource .rr-info-grid,
            .rr-condition-bar,
            .rr-summary-grid,
            .rr-info-grid {
              grid-template-columns: 1fr;
            }
    
            .rr-condition-bar {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
    
            .rr-header-badges {
              justify-content: flex-start;
            }
    
            .rr-map {
              height: 320px;
            }
    
            .rr-map-label {
              max-width: 8.5rem;
              font-size: 0.7rem;
            }
          }
    
          .block-container {
            max-width: 1280px;
            padding-top: 0.45rem;
          }
    
          .rr-app-header {
            background: #ffffff !important;
            border: 1px solid var(--rr-line) !important;
            border-top: 5px solid var(--rr-primary) !important;
            border-left: 1px solid var(--rr-line) !important;
            padding: 0.78rem 0.95rem !important;
            margin-bottom: 0.48rem !important;
          }
    
          .rr-app-header,
          .rr-app-header * {
            color: var(--rr-ink) !important;
          }
    
          .rr-app-subtitle {
            color: var(--rr-muted) !important;
          }
    
          .rr-topbar {
            margin-top: 0;
            font-weight: 750;
          }
    
          .rr-route-strip {
            margin: 0.2rem 0 0.45rem;
          }
    
          .rr-flow-compact {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.45rem;
            margin: 0.4rem 0 0.58rem;
          }
    
          .rr-flow-compact div {
            background: #ffffff;
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            padding: 0.48rem 0.58rem;
            min-height: 3.2rem;
          }
    
          .rr-flow-compact strong {
            display: block;
            color: var(--rr-ink) !important;
            font-size: 0.86rem;
            line-height: 1.25;
          }
    
          .rr-flow-compact span {
            color: var(--rr-muted) !important;
            font-size: 0.78rem;
            line-height: 1.3;
          }
    
          .rr-data-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            align-items: center;
            margin: 0.25rem 0 0.55rem;
          }
    
          .rr-data-strip span {
            border: 1px solid #b9ddd7;
            background: #f1faf8;
            color: #0f5f57 !important;
            border-radius: 999px;
            padding: 0.24rem 0.55rem;
            font-size: 0.78rem;
            font-weight: 800;
          }
    
          .rr-control-card {
            background: #ffffff;
            border: 1px solid var(--rr-line);
            border-radius: 8px;
            padding: 0.78rem;
            box-shadow: var(--rr-shadow-soft);
          }
    
          .rr-control-card .rr-section-title {
            margin-bottom: 0.15rem;
          }
    
          .rr-control-card [data-testid="stWidgetLabel"] p {
            font-size: 0.78rem !important;
            font-weight: 800 !important;
          }
    
          .rr-card-with-media {
            display: grid;
            grid-template-columns: 150px minmax(0, 1fr);
            gap: 0.72rem;
            align-items: stretch;
          }
    
          .rr-featured-resource .rr-card-with-media {
            grid-template-columns: 175px minmax(0, 1fr);
          }
    
          .rr-resource-thumb {
            width: 100%;
            height: 100%;
            min-height: 132px;
            max-height: 182px;
            object-fit: cover;
            border-radius: 7px;
            border: 1px solid var(--rr-line);
            background: #f8fafc;
          }
    
          .rr-proof {
            margin-top: 0.38rem;
            color: #334155 !important;
            font-size: 0.78rem;
            line-height: 1.4;
          }
    
          .rr-proof strong {
            color: #0f172a !important;
          }
    
          .rr-featured-resource,
          .rr-resource-card,
          .rr-next-action,
          .rr-panel {
            padding: 0.7rem !important;
            margin: 0.38rem 0 !important;
          }
    
          .rr-info-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.42rem;
            margin: 0.48rem 0;
          }
    
          .rr-info-item {
            min-height: 2.7rem;
            padding: 0.42rem 0.5rem;
          }
    
          .rr-map {
            height: 255px;
          }
    
          .rr-map-label {
            max-width: 9.4rem;
          }
    
          .rr-inline-card-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.55rem;
            margin-top: 0.4rem;
          }
    
          .rr-source-link {
            padding: 0.32rem 0.52rem;
          }
    
          @media (max-width: 760px) {
            .block-container {
              padding: 0.55rem 0.72rem 1.5rem;
            }
    
            .rr-flow-compact {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
    
            .rr-card-with-media,
            .rr-featured-resource .rr-card-with-media,
            .rr-inline-card-grid {
              grid-template-columns: 1fr;
            }
    
            .rr-resource-thumb {
              min-height: 138px;
              max-height: 180px;
            }
    
            .rr-map {
              height: 230px;
            }
    
            .rr-data-strip span {
              font-size: 0.74rem;
            }
          }
    
          /* 2026 mobile-app redesign layer */
          :root {
            --rr-bg: #f5f7fb;
            --rr-surface: #ffffff;
            --rr-surface-raised: rgba(255, 255, 255, 0.82);
            --rr-ink: #111827;
            --rr-muted: #667085;
            --rr-soft: #8a94a6;
            --rr-line: #dce3ee;
            --rr-primary: #2563eb;
            --rr-primary-strong: #1d4ed8;
            --rr-primary-soft: #e9efff;
            --rr-info: #14b8a6;
            --rr-info-soft: #e7fbf7;
            --rr-action: #f97316;
            --rr-action-soft: #fff1e7;
            --rr-danger: #dc2626;
            --rr-danger-soft: #fff1f2;
            --rr-radius-xl: 18px;
            --rr-radius-lg: 16px;
            --rr-radius-md: 12px;
            --rr-glass: rgba(255, 255, 255, 0.72);
            --rr-shadow: 0 18px 48px rgba(15, 23, 42, 0.12);
            --rr-shadow-soft: 0 8px 22px rgba(15, 23, 42, 0.08);
          }
    
          @media (prefers-color-scheme: dark) {
            :root {
              --rr-bg: #0b1020;
              --rr-surface: #111827;
              --rr-surface-raised: rgba(17, 24, 39, 0.82);
              --rr-ink: #f8fafc;
              --rr-muted: #cbd5e1;
              --rr-soft: #94a3b8;
              --rr-line: #273449;
              --rr-primary: #60a5fa;
              --rr-primary-strong: #93c5fd;
              --rr-primary-soft: rgba(96, 165, 250, 0.18);
              --rr-info: #2dd4bf;
              --rr-info-soft: rgba(45, 212, 191, 0.14);
              --rr-action: #fb7185;
              --rr-action-soft: rgba(251, 113, 133, 0.14);
              --rr-danger: #fca5a5;
              --rr-danger-soft: rgba(252, 165, 165, 0.14);
              --rr-glass: rgba(17, 24, 39, 0.68);
              --rr-shadow: 0 18px 48px rgba(0, 0, 0, 0.36);
              --rr-shadow-soft: 0 8px 22px rgba(0, 0, 0, 0.22);
            }
          }
    
          .stApp,
          [data-testid="stAppViewContainer"],
          [data-testid="stMain"],
          [data-testid="stMainBlockContainer"],
          section.main {
            background:
              radial-gradient(circle at 18% 0%, rgba(37, 99, 235, 0.12), transparent 28rem),
              radial-gradient(circle at 100% 18%, rgba(20, 184, 166, 0.13), transparent 24rem),
              var(--rr-bg) !important;
          }
    
          #MainMenu,
          footer,
          [data-testid="stToolbar"],
          [data-testid="stDecoration"] {
            display: none !important;
          }
    
          .block-container {
            max-width: 1180px !important;
            padding: 0.42rem 1.05rem 5.4rem !important;
          }
    
          [data-testid="stVerticalBlock"] {
            gap: 0.58rem !important;
          }
    
          .rr-topbar,
          .rr-app-header,
          .rr-page-title,
          .rr-flow-compact,
          .rr-data-strip,
          .rr-control-card {
            display: none !important;
          }
    
          .rr-app-shell {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.9rem;
            margin: 0.1rem 0 0.5rem;
          }
    
          .rr-brand-lockup {
            display: flex;
            flex-direction: column;
            gap: 0.05rem;
          }
    
          .rr-brand-name {
            color: var(--rr-ink) !important;
            font-size: 1.08rem;
            font-weight: 900;
            line-height: 1.1;
          }
    
          .rr-brand-sub {
            color: var(--rr-muted) !important;
            font-size: 0.78rem;
            font-weight: 760;
            line-height: 1.35;
          }
    
          .rr-session-pill {
            display: inline-flex;
            align-items: center;
            border: 1px solid var(--rr-line);
            background: var(--rr-glass);
            color: var(--rr-ink) !important;
            backdrop-filter: blur(18px) saturate(1.2);
            border-radius: 999px;
            padding: 0.38rem 0.68rem;
            font-size: 0.78rem;
            font-weight: 850;
            box-shadow: var(--rr-shadow-soft);
          }
    
          [data-baseweb="tab-list"] {
            gap: 0.35rem !important;
            border-bottom: 0 !important;
            margin-bottom: 0.45rem;
            padding: 0.24rem !important;
            border-radius: 999px;
            background: color-mix(in srgb, var(--rr-surface) 88%, transparent);
            box-shadow: inset 0 0 0 1px var(--rr-line);
          }
    
          [data-baseweb="tab"] {
            border-radius: 999px !important;
            min-height: 2.35rem !important;
            padding: 0.54rem 0.9rem !important;
            font-weight: 850 !important;
            color: var(--rr-muted) !important;
            transition: background 180ms ease, color 180ms ease, transform 180ms ease;
          }
    
          [data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            background: linear-gradient(135deg, var(--rr-primary), var(--rr-info)) !important;
            border: 0 !important;
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.24);
          }
    
          [data-baseweb="tab-highlight"],
          [data-baseweb="tab-border"] {
            display: none !important;
          }
    
          .rr-route-hero {
            position: relative;
            overflow: hidden;
            border: 1px solid color-mix(in srgb, var(--rr-primary) 18%, var(--rr-line));
            border-radius: 20px;
            background:
              linear-gradient(135deg, rgba(37, 99, 235, 0.15), rgba(20, 184, 166, 0.08) 42%, rgba(249, 115, 22, 0.1)),
              var(--rr-surface);
            padding: 0.74rem 0.86rem;
            box-shadow: var(--rr-shadow);
            margin-bottom: 0.38rem;
          }
    
          .rr-route-hero::after {
            content: "";
            position: absolute;
            inset: auto -4rem -5rem auto;
            width: 12rem;
            height: 12rem;
            border-radius: 999px;
            background: rgba(37, 99, 235, 0.12);
            filter: blur(28px);
            pointer-events: none;
          }
    
          .rr-hero-kicker {
            color: var(--rr-primary-strong) !important;
            font-size: 0.76rem;
            font-weight: 900;
            letter-spacing: 0;
            margin-bottom: 0.16rem;
          }
    
          .rr-hero-title {
            color: var(--rr-ink) !important;
            font-size: 1.38rem;
            font-weight: 950;
            line-height: 1.15;
            margin-bottom: 0.22rem;
          }
    
          .rr-hero-copy {
            max-width: 42rem;
            color: var(--rr-muted) !important;
            font-size: 0.86rem;
            font-weight: 680;
            line-height: 1.48;
            margin: 0;
          }
    
          .rr-choice-row {
            margin-top: 0.26rem;
          }
    
          .rr-choice-label {
            color: var(--rr-ink) !important;
            font-size: 0.82rem;
            font-weight: 900;
            line-height: 1.25;
            margin-bottom: 0.36rem;
          }
    
          .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: var(--rr-radius-lg) !important;
            border-color: color-mix(in srgb, var(--rr-line) 82%, transparent) !important;
            background: var(--rr-glass) !important;
            box-shadow: var(--rr-shadow-soft) !important;
            backdrop-filter: blur(18px) saturate(1.12);
            padding: 0.08rem !important;
          }
    
          .stButton > button {
            border-radius: 999px !important;
            min-height: 2.24rem !important;
            border: 1px solid var(--rr-line) !important;
            background: color-mix(in srgb, var(--rr-surface) 92%, transparent) !important;
            color: var(--rr-ink) !important;
            font-weight: 900 !important;
            transition: transform 160ms ease, box-shadow 180ms ease, border-color 180ms ease, background 180ms ease;
          }
    
          .stButton > button p,
          .stButton > button span {
            color: var(--rr-ink) !important;
          }
    
          .stButton > button:hover {
            transform: translateY(-1px);
            border-color: var(--rr-primary) !important;
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.12);
          }
    
          [data-testid="stSegmentedControl"] {
            width: 100% !important;
          }
    
          [data-testid="stSegmentedControl"] > div {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 0.35rem !important;
            width: 100% !important;
          }
    
          [data-testid="stSegmentedControl"] button {
            border-radius: 999px !important;
            min-height: 2.24rem !important;
            border: 1px solid var(--rr-line) !important;
            background: color-mix(in srgb, var(--rr-surface) 92%, transparent) !important;
            color: var(--rr-ink) !important;
            font-weight: 900 !important;
            transition: transform 160ms ease, box-shadow 180ms ease, border-color 180ms ease, background 180ms ease;
          }
    
          [data-testid="stSegmentedControl"] button p,
          [data-testid="stSegmentedControl"] button span {
            color: var(--rr-ink) !important;
          }
    
          [data-testid="stSegmentedControl"] button:hover {
            transform: translateY(-1px);
            border-color: var(--rr-primary) !important;
          }
    
          [data-testid="stSegmentedControl"] button[aria-pressed="true"],
          [data-testid="stSegmentedControl"] button[aria-checked="true"],
          [data-testid="stSegmentedControl"] button[data-selected="true"] {
            background: linear-gradient(135deg, var(--rr-primary), var(--rr-info)) !important;
            color: #ffffff !important;
            border-color: transparent !important;
            box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
          }
    
          [data-testid="stSegmentedControl"] button[aria-pressed="true"] p,
          [data-testid="stSegmentedControl"] button[aria-pressed="true"] span,
          [data-testid="stSegmentedControl"] button[aria-checked="true"] p,
          [data-testid="stSegmentedControl"] button[aria-checked="true"] span,
          [data-testid="stSegmentedControl"] button[data-selected="true"] p,
          [data-testid="stSegmentedControl"] button[data-selected="true"] span {
            color: #ffffff !important;
          }
    
          [data-testid="stBaseButton-segmented_control"] {
            border-radius: 999px !important;
            border: 1px solid var(--rr-line) !important;
            background: color-mix(in srgb, var(--rr-surface) 92%, transparent) !important;
            color: var(--rr-ink) !important;
            font-weight: 900 !important;
          }
    
          [data-testid="stBaseButton-segmented_control"] *,
          [data-testid="stBaseButton-segmented_control"] p,
          [data-testid="stBaseButton-segmented_control"] span {
            color: var(--rr-ink) !important;
          }
    
          [data-testid="stBaseButton-segmented_controlActive"] {
            border-radius: 999px !important;
            border: 1px solid transparent !important;
            background: linear-gradient(135deg, var(--rr-primary), var(--rr-info)) !important;
            color: #ffffff !important;
            font-weight: 950 !important;
            box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
          }
    
          [data-testid="stBaseButton-segmented_controlActive"] *,
          [data-testid="stBaseButton-segmented_controlActive"] p,
          [data-testid="stBaseButton-segmented_controlActive"] span {
            color: #ffffff !important;
          }
    
          [data-testid="stBaseButton-primary"],
          button[kind="primary"] {
            background: linear-gradient(135deg, var(--rr-primary), var(--rr-info)) !important;
            color: #ffffff !important;
            border-color: transparent !important;
            box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
          }
    
          [data-testid="stBaseButton-primary"] p,
          [data-testid="stBaseButton-primary"] span,
          button[kind="primary"] p,
          button[kind="primary"] span {
            color: #ffffff !important;
          }
    
          .rr-bento-row {
            margin-top: 0.62rem;
          }
    
          .rr-bento-card {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--rr-line);
            border-radius: var(--rr-radius-xl);
            background: var(--rr-surface);
            padding: 0.78rem;
            box-shadow: var(--rr-shadow-soft);
          }
    
          .rr-bento-card.mission {
            min-height: 14.6rem;
            background:
              linear-gradient(160deg, rgba(37, 99, 235, 0.11), transparent 52%),
              var(--rr-surface);
          }
    
          .rr-bento-card.resource {
            min-height: 7.9rem;
            background:
              linear-gradient(145deg, rgba(20, 184, 166, 0.11), transparent 54%),
              var(--rr-surface);
          }
    
          .rr-bento-card.map {
            min-height: 10rem;
            padding: 0.62rem;
            margin-top: 0;
          }
    
          .rr-card-eyebrow {
            color: var(--rr-soft) !important;
            font-size: 0.73rem;
            font-weight: 920;
            margin-bottom: 0.25rem;
          }
    
          .rr-bento-title {
            color: var(--rr-ink) !important;
            font-size: 1.1rem;
            font-weight: 950;
            line-height: 1.22;
            margin-bottom: 0.34rem;
          }
    
          .rr-bento-card.resource .rr-bento-title {
            display: -webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
            overflow: hidden;
            font-size: 1rem;
            margin-bottom: 0.26rem;
          }
    
          .rr-bento-body {
            color: var(--rr-muted) !important;
            font-size: 0.85rem;
            line-height: 1.44;
            margin-bottom: 0.48rem;
          }
    
          .rr-bento-card.resource .rr-bento-body {
            display: none;
          }
    
          .rr-mini-facts {
            display: flex;
            flex-wrap: wrap;
            gap: 0.3rem;
            margin-top: 0.42rem;
          }
    
          .rr-mini-fact {
            display: inline-flex;
            align-items: center;
            min-height: 2rem;
            border-radius: 999px;
            border: 1px solid var(--rr-line);
            background: color-mix(in srgb, var(--rr-surface) 88%, transparent);
            color: var(--rr-ink) !important;
            padding: 0.24rem 0.58rem;
            font-size: 0.78rem;
            font-weight: 860;
          }
    
          .rr-resource-layout {
            display: grid;
            grid-template-columns: minmax(0, 1fr);
            gap: 0.54rem;
            align-items: stretch;
          }
    
          .rr-resource-art {
            width: 100%;
            height: 5.2rem;
            min-height: 5.2rem;
            border-radius: var(--rr-radius-lg);
            object-fit: cover;
            border: 1px solid var(--rr-line);
            background: var(--rr-primary-soft);
          }
    
          .rr-official-line {
            color: var(--rr-soft) !important;
            font-size: 0.76rem;
            font-weight: 760;
            line-height: 1.36;
            margin-top: 0.28rem;
          }
    
          .rr-map.compact {
            height: 7.2rem;
            border-radius: var(--rr-radius-lg);
            margin-top: 0.38rem;
          }
    
          .rr-map.expanded {
            height: 20rem;
            border-radius: var(--rr-radius-xl);
          }
    
          .rr-map.compact .rr-map-label {
            display: none;
          }
    
          .rr-action-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.44rem;
            margin-top: 0.62rem;
          }
    
          .rr-action-row .stButton > button,
          .rr-floating-action .stButton > button,
          .st-key-route_action_bar .stButton > button {
            border-radius: 999px !important;
            min-height: 2.7rem !important;
            font-weight: 920 !important;
            transition: transform 160ms ease, box-shadow 180ms ease, background 180ms ease;
          }
    
          .rr-action-row .stButton > button:hover,
          .rr-floating-action .stButton > button:hover,
          .st-key-route_action_bar .stButton > button:hover {
            transform: translateY(-1px);
          }
    
          .st-key-route_action_bar {
            position: fixed;
            left: max(1rem, calc((100vw - 1180px) / 2 + 1rem));
            right: max(1rem, calc((100vw - 1180px) / 2 + 1rem));
            bottom: 0.36rem;
            z-index: 20;
            margin-top: 0.72rem;
            padding: 0.34rem;
            width: auto !important;
            max-width: calc(100vw - 2rem) !important;
            box-sizing: border-box !important;
            border: 1px solid color-mix(in srgb, var(--rr-primary) 18%, var(--rr-line));
            border-radius: 999px;
            background: var(--rr-glass);
            backdrop-filter: blur(22px) saturate(1.18);
            box-shadow: var(--rr-shadow);
          }
    
          .rr-floating-action {
            position: sticky;
            bottom: 0.7rem;
            z-index: 20;
            display: grid;
            grid-template-columns: minmax(0, 1.3fr) minmax(0, 0.85fr) minmax(0, 0.85fr) minmax(0, 0.85fr);
            gap: 0.46rem;
            margin-top: 0.8rem;
            padding: 0.5rem;
            border: 1px solid color-mix(in srgb, var(--rr-primary) 18%, var(--rr-line));
            border-radius: 999px;
            background: var(--rr-glass);
            backdrop-filter: blur(22px) saturate(1.18);
            box-shadow: var(--rr-shadow);
          }
    
          .rr-floating-action [data-testid="stBaseButton-primary"],
          .st-key-route_action_bar [data-testid="stBaseButton-primary"] {
            background: linear-gradient(135deg, var(--rr-action), var(--rr-primary)) !important;
            border: 0 !important;
          }
    
          .st-key-route_action_bar .stButton > button {
            min-height: 2.36rem !important;
          }
    
          .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: minmax(0, 1.35fr) repeat(3, minmax(0, 0.85fr)) !important;
            gap: 0.46rem !important;
          }
    
          .st-key-route_action_bar [data-testid="column"] {
            width: 100% !important;
            min-width: 0 !important;
          }
    
          .rr-progressive-panel {
            border: 1px solid var(--rr-line);
            border-radius: var(--rr-radius-xl);
            background: var(--rr-surface);
            padding: 0.78rem;
            margin-top: 0.62rem;
            box-shadow: var(--rr-shadow-soft);
          }
    
          .rr-compact-controls {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.48rem;
          }
    
          .rr-compact-controls [data-testid="stWidgetLabel"] p {
            font-size: 0.75rem !important;
            font-weight: 850 !important;
            color: var(--rr-muted) !important;
          }
    
          .rr-history-list {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.62rem;
          }
    
          .rr-history-card {
            border: 1px solid var(--rr-line);
            border-radius: var(--rr-radius-lg);
            background: var(--rr-surface);
            padding: 0.78rem;
            box-shadow: var(--rr-shadow-soft);
          }
    
          .rr-history-card strong {
            display: block;
            color: var(--rr-ink) !important;
            font-size: 0.94rem;
            line-height: 1.35;
            margin-bottom: 0.18rem;
          }
    
          .rr-history-card span {
            color: var(--rr-muted) !important;
            font-size: 0.82rem;
            line-height: 1.45;
          }
    
          @media (prefers-color-scheme: dark) {
            .rr-route-hero,
            .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"],
            .rr-bento-card,
            .rr-progressive-panel,
            .rr-history-card,
            .rr-resource-card,
            .rr-panel {
              background-color: var(--rr-surface) !important;
            }
    
            .rr-map {
              background:
                linear-gradient(90deg, rgba(96, 165, 250, 0.12) 1px, transparent 1px),
                linear-gradient(rgba(96, 165, 250, 0.12) 1px, transparent 1px),
                linear-gradient(135deg, #101827 0%, #111827 50%, #0f172a 100%) !important;
            }
    
            .rr-map-label {
              background: rgba(15, 23, 42, 0.92) !important;
            }
          }
    
          @media (max-width: 860px) {
            .block-container {
              padding: 0.42rem 0.72rem 5.5rem !important;
            }
    
            .rr-app-shell {
              align-items: flex-start;
            }
    
            .rr-session-pill {
              display: none;
            }
    
            .rr-route-hero {
              border-radius: 18px;
              padding: 0.68rem;
            }
    
            .rr-hero-title {
              font-size: 1.18rem;
            }
    
            .rr-hero-copy {
              font-size: 0.86rem;
            }
    
            .rr-choice-row {
              margin-top: 0.48rem;
            }
    
            .rr-bento-card {
              border-radius: 18px;
              padding: 0.76rem;
            }
    
            .rr-bento-card.mission {
              min-height: auto;
            }
    
            .rr-resource-art {
              min-height: 5.8rem;
            }
    
            .rr-compact-controls {
              grid-template-columns: 1fr 1fr;
            }
    
            .rr-history-list {
              grid-template-columns: 1fr;
            }
    
            .rr-floating-action,
            .st-key-route_action_bar {
              border-radius: 24px;
            }
    
            .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
              grid-template-columns: 1fr 1fr !important;
              gap: 0.34rem !important;
            }
    
            .rr-floating-action > div:nth-child(3),
            .rr-floating-action > div:nth-child(4) {
              grid-column: span 1;
            }
          }
    
          @media (max-width: 430px) {
            [data-testid="stVerticalBlock"] {
              gap: 0.42rem !important;
            }
    
            .rr-app-shell {
              margin-bottom: 0.14rem;
            }
    
            .rr-brand-name {
              font-size: 0.98rem;
            }
    
            .rr-brand-sub {
              font-size: 0.72rem;
            }
    
            [data-baseweb="tab"] {
              padding: 0.48rem 0.62rem !important;
              min-height: 2.1rem !important;
              font-size: 0.82rem !important;
            }
    
            [data-baseweb="tab-list"] {
              margin-bottom: 0.22rem;
            }
    
            .rr-route-hero {
              padding: 0.56rem 0.64rem;
              margin-bottom: 0.1rem;
            }
    
            .rr-hero-kicker {
              font-size: 0.68rem;
              margin-bottom: 0.08rem;
            }
    
            .rr-hero-title {
              font-size: 1.06rem;
              margin-bottom: 0.1rem;
            }
    
            .rr-hero-copy {
              font-size: 0.78rem;
              line-height: 1.34;
            }
    
            .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"] {
              padding: 0 !important;
            }
    
            .rr-choice-label {
              margin-bottom: 0.22rem;
              font-size: 0.76rem;
            }
    
            .stButton > button {
              min-height: 2rem !important;
              font-size: 0.78rem !important;
              padding: 0.28rem 0.52rem !important;
            }
    
            [data-testid="stBaseButton-segmented_control"],
            [data-testid="stBaseButton-segmented_controlActive"] {
              min-height: 1.86rem !important;
              padding: 0.2rem 0.42rem !important;
              font-size: 0.74rem !important;
            }
    
            .rr-bento-title {
              font-size: 1.08rem;
            }
    
            .rr-bento-body {
              font-size: 0.84rem;
              line-height: 1.45;
            }
    
            .rr-resource-layout {
              grid-template-columns: 4.8rem minmax(0, 1fr);
              align-items: center;
            }
    
            .rr-resource-art {
              height: 5.2rem;
              min-height: 5.2rem;
            }
    
            .rr-bento-card.resource .rr-bento-title {
              font-size: 0.92rem;
            }
    
            .rr-bento-card.resource .rr-source-link {
              display: none;
            }
    
            .rr-mini-facts {
              gap: 0.28rem;
            }
    
            .rr-mini-fact {
              min-height: 1.8rem;
              font-size: 0.72rem;
              padding: 0.2rem 0.44rem;
            }
    
            .rr-floating-action,
            .st-key-route_action_bar {
              bottom: 0.5rem;
              padding: 0.38rem;
              gap: 0.34rem;
            }
    
            .rr-floating-action .stButton > button,
            .st-key-route_action_bar .stButton > button {
              min-height: 2.42rem !important;
              font-size: 0.8rem !important;
            }
    
            .st-key-route_action_bar {
              padding: 0.28rem;
            }
    
            .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
              grid-template-columns: minmax(0, 1.35fr) repeat(3, minmax(0, 0.9fr)) !important;
              gap: 0.28rem !important;
            }
    
            .st-key-route_action_bar .stButton > button {
              min-height: 2.22rem !important;
              font-size: 0.69rem !important;
              padding: 0.16rem 0.2rem !important;
            }
          }
    
          /* final readability and flow correction */
          :root {
            --rr-bg: #f6f8fc;
            --rr-surface: #ffffff;
            --rr-surface-raised: #ffffff;
            --rr-ink: #111827;
            --rr-muted: #4b5563;
            --rr-soft: #64748b;
            --rr-line: #d7deea;
            --rr-primary: #1d4ed8;
            --rr-primary-strong: #1e40af;
            --rr-primary-soft: #e8f0ff;
            --rr-info: #0f766e;
            --rr-info-soft: #e7f7f4;
            --rr-action: #c2410c;
            --rr-action-soft: #fff1e7;
            --rr-glass: #ffffff;
            --rr-shadow: 0 14px 34px rgba(15, 23, 42, 0.10);
            --rr-shadow-soft: 0 6px 18px rgba(15, 23, 42, 0.08);
          }
    
          @media (prefers-color-scheme: dark) {
            :root {
              --rr-bg: #0f172a;
              --rr-surface: #182235;
              --rr-surface-raised: #1f2937;
              --rr-ink: #f8fafc;
              --rr-muted: #d1d5db;
              --rr-soft: #b6c2d3;
              --rr-line: #3b4a60;
              --rr-primary: #7dd3fc;
              --rr-primary-strong: #bae6fd;
              --rr-primary-soft: rgba(125, 211, 252, 0.18);
              --rr-info: #5eead4;
              --rr-info-soft: rgba(94, 234, 212, 0.16);
              --rr-action: #fb923c;
              --rr-action-soft: rgba(251, 146, 60, 0.18);
              --rr-glass: #182235;
              --rr-shadow: 0 16px 38px rgba(0, 0, 0, 0.32);
              --rr-shadow-soft: 0 8px 22px rgba(0, 0, 0, 0.24);
            }
          }
    
          .stApp,
          [data-testid="stAppViewContainer"],
          [data-testid="stMain"],
          [data-testid="stMainBlockContainer"],
          section.main {
            background: var(--rr-bg) !important;
          }
    
          .block-container {
            max-width: 1100px !important;
            padding: 0.72rem 1rem 1.4rem !important;
          }
    
          [data-testid="stVerticalBlock"] {
            gap: 0.48rem !important;
          }
    
          .rr-app-shell {
            margin: 0 0 0.46rem !important;
          }
    
          .rr-brand-name {
            font-size: 1.18rem !important;
          }
    
          .rr-brand-sub,
          .rr-session-pill {
            color: var(--rr-muted) !important;
          }
    
          [data-baseweb="tab-list"] {
            background: var(--rr-surface) !important;
            border: 1px solid var(--rr-line) !important;
            box-shadow: var(--rr-shadow-soft) !important;
            padding: 0.22rem !important;
            margin-bottom: 0.58rem !important;
          }
    
          [data-baseweb="tab"] {
            color: var(--rr-muted) !important;
            font-size: 0.92rem !important;
          }
    
          [data-baseweb="tab"][aria-selected="true"] {
            background: var(--rr-primary) !important;
            color: #ffffff !important;
            box-shadow: none !important;
          }
    
          .rr-route-hero {
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) minmax(18rem, 0.9fr) !important;
            column-gap: 0.8rem !important;
            align-items: center !important;
            border-radius: 18px !important;
            background: var(--rr-surface) !important;
            border: 1px solid var(--rr-line) !important;
            box-shadow: var(--rr-shadow-soft) !important;
            padding: 0.68rem 0.82rem !important;
            margin-bottom: 0.58rem !important;
          }
    
          .rr-hero-kicker,
          .rr-hero-title,
          .rr-hero-copy {
            grid-column: 1 !important;
            word-break: keep-all !important;
          }
    
          .rr-use-guide {
            grid-column: 2 !important;
            grid-row: 1 / span 3 !important;
          }
    
          .rr-route-hero::after {
            display: none !important;
          }
    
          .rr-hero-kicker {
            color: var(--rr-primary-strong) !important;
          }
    
          .rr-hero-title {
            color: var(--rr-ink) !important;
            font-size: 1.32rem !important;
          }
    
          .rr-hero-copy {
            color: var(--rr-muted) !important;
            font-size: 0.9rem !important;
          }
    
          .rr-use-guide {
            display: grid;
            grid-template-columns: 1fr;
            gap: 0.42rem;
            margin-top: 0;
          }
    
          .rr-use-guide span {
            display: flex;
            align-items: center;
            gap: 0.38rem;
            border: 1px solid var(--rr-line);
            border-radius: 999px;
            background: var(--rr-surface-raised);
            color: var(--rr-ink) !important;
            padding: 0.36rem 0.52rem;
            font-size: 0.8rem;
            font-weight: 850;
            white-space: nowrap;
          }
    
          .rr-use-guide b {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 1.35rem;
            height: 1.35rem;
            border-radius: 999px;
            background: var(--rr-primary);
            color: #ffffff !important;
            font-size: 0.75rem;
          }
    
          .rr-choice-row {
            margin-top: 0 !important;
          }
    
          .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"],
          .rr-bento-card,
          .rr-progressive-panel,
          .rr-history-card,
          .rr-resource-card,
          .rr-panel {
            background: var(--rr-surface) !important;
            border: 1px solid var(--rr-line) !important;
            border-radius: 16px !important;
            box-shadow: var(--rr-shadow-soft) !important;
          }
    
          .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0.28rem !important;
          }
    
          .rr-choice-label {
            color: var(--rr-ink) !important;
            font-size: 0.84rem !important;
            margin-bottom: 0.32rem !important;
          }
    
          [data-testid="stBaseButton-segmented_control"],
          [data-testid="stBaseButton-segmented_controlActive"],
          .stButton > button {
            white-space: nowrap !important;
            word-break: keep-all !important;
            min-height: 2.18rem !important;
            border-radius: 999px !important;
            font-size: 0.88rem !important;
          }
    
          [data-testid="stBaseButton-segmented_control"] {
            color: var(--rr-ink) !important;
            background: var(--rr-surface-raised) !important;
            border-color: var(--rr-line) !important;
          }
    
          [data-testid="stBaseButton-segmented_control"] *,
          [data-testid="stBaseButton-segmented_control"] p,
          [data-testid="stBaseButton-segmented_control"] span {
            color: var(--rr-ink) !important;
          }
    
          [data-testid="stBaseButton-segmented_controlActive"] {
            background: var(--rr-primary) !important;
            color: #ffffff !important;
            border-color: var(--rr-primary) !important;
            box-shadow: none !important;
          }
    
          [data-testid="stBaseButton-segmented_controlActive"] *,
          [data-testid="stBaseButton-segmented_controlActive"] p,
          [data-testid="stBaseButton-segmented_controlActive"] span {
            color: #ffffff !important;
          }
    
          .rr-bento-row {
            margin-top: 0.56rem !important;
          }
    
          .rr-bento-card {
            padding: 0.82rem !important;
          }
    
          .rr-bento-card.mission,
          .rr-bento-card.resource,
          .rr-bento-card.map {
            min-height: 0 !important;
          }
    
          .rr-bento-title {
            color: var(--rr-ink) !important;
          }
    
          .rr-bento-body {
            color: var(--rr-muted) !important;
            margin-bottom: 0.4rem !important;
          }
    
          .rr-mini-fact,
          .rr-chip {
            color: var(--rr-ink) !important;
            background: var(--rr-surface-raised) !important;
            border-color: var(--rr-line) !important;
          }
    
          .rr-official-line,
          .rr-card-eyebrow {
            color: var(--rr-soft) !important;
          }
    
          .rr-resource-art {
            height: 6.2rem !important;
            min-height: 6.2rem !important;
          }
    
          .rr-resource-layout {
            grid-template-columns: 7.2rem minmax(0, 1fr) !important;
            gap: 0.64rem !important;
            align-items: center !important;
          }
    
          .rr-source-link {
            background: var(--rr-primary) !important;
            border-color: var(--rr-primary) !important;
            color: #ffffff !important;
            padding: 0.42rem 0.7rem !important;
          }
    
          .rr-map {
            border-color: var(--rr-line) !important;
            background:
              linear-gradient(90deg, rgba(29, 78, 216, 0.09) 1px, transparent 1px),
              linear-gradient(rgba(29, 78, 216, 0.09) 1px, transparent 1px),
              linear-gradient(135deg, #eef6ff 0%, #f8fafc 55%, #ecfdf5 100%) !important;
          }
    
          .rr-map.compact {
            height: 6.9rem !important;
          }
    
          .rr-map-label {
            background: rgba(255, 255, 255, 0.96) !important;
            color: #111827 !important;
          }
    
          .rr-map-label small {
            color: #475569 !important;
          }
    
          .st-key-route_action_bar {
            position: static !important;
            left: auto !important;
            right: auto !important;
            bottom: auto !important;
            width: 100% !important;
            max-width: none !important;
            margin: 0.58rem 0 0 !important;
            padding: 0.58rem !important;
            border-radius: 20px !important;
            background: var(--rr-surface) !important;
            border: 1px solid var(--rr-line) !important;
            box-shadow: var(--rr-shadow-soft) !important;
          }
    
          .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 0.42rem !important;
          }
    
          .st-key-route_action_bar [data-testid="column"] {
            width: 100% !important;
            min-width: 0 !important;
          }
    
          .st-key-route_action_bar .stButton > button {
            min-height: 2.44rem !important;
            padding: 0.48rem 0.72rem !important;
            font-size: 0.9rem !important;
            line-height: 1.15 !important;
          }
    
          .st-key-route_action_bar [data-testid="stBaseButton-primary"] {
            background: var(--rr-action) !important;
            border-color: var(--rr-action) !important;
            color: #ffffff !important;
          }
    
          .rr-progressive-panel {
            margin-top: 0.58rem !important;
          }
    
          @media (prefers-color-scheme: dark) {
            [data-baseweb="tab"][aria-selected="true"],
            [data-testid="stBaseButton-segmented_controlActive"] {
              background: #e0f2fe !important;
              color: #082f49 !important;
            }
    
            [data-baseweb="tab"][aria-selected="true"] *,
            [data-testid="stBaseButton-segmented_controlActive"] *,
            [data-testid="stBaseButton-segmented_controlActive"] p,
            [data-testid="stBaseButton-segmented_controlActive"] span {
              color: #082f49 !important;
            }
    
            .rr-use-guide b {
              background: #e0f2fe !important;
              color: #082f49 !important;
            }
    
            .rr-source-link,
            .st-key-route_action_bar [data-testid="stBaseButton-primary"] {
              background: #f97316 !important;
              border-color: #f97316 !important;
              color: #111827 !important;
            }
    
            .rr-source-link *,
            .st-key-route_action_bar [data-testid="stBaseButton-primary"] * {
              color: #111827 !important;
            }
    
            .rr-map {
              background:
                linear-gradient(90deg, rgba(125, 211, 252, 0.10) 1px, transparent 1px),
                linear-gradient(rgba(125, 211, 252, 0.10) 1px, transparent 1px),
                linear-gradient(135deg, #1e293b 0%, #111827 58%, #0f172a 100%) !important;
            }
          }
    
          @media (max-width: 860px) {
            .block-container {
              padding: 0.62rem 0.72rem 1.2rem !important;
            }
    
            .rr-use-guide {
              grid-template-columns: 1fr !important;
              grid-column: 1 !important;
              grid-row: auto !important;
            }
    
            .rr-route-hero {
              grid-template-columns: 1fr !important;
            }
    
            .rr-use-guide span {
              white-space: normal !important;
            }
    
            .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"] {
              margin-bottom: 0.34rem !important;
            }
    
            .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
              grid-template-columns: 1fr 1fr !important;
              gap: 0.42rem !important;
            }
          }
    
          @media (max-width: 430px) {
            .block-container {
              padding: 0.52rem 0.62rem 1.1rem !important;
            }
    
            .rr-hero-title {
              font-size: 1.08rem !important;
            }
    
            .rr-hero-copy {
              font-size: 0.8rem !important;
            }
    
            [data-baseweb="tab-list"] {
              overflow-x: auto !important;
              border-radius: 18px !important;
            }
    
            [data-testid="stBaseButton-segmented_control"],
            [data-testid="stBaseButton-segmented_controlActive"],
            .stButton > button {
              font-size: 0.78rem !important;
              min-height: 2.12rem !important;
            }
    
            .rr-bento-card {
              padding: 0.72rem !important;
            }
    
            .rr-map.compact {
              height: 6.8rem !important;
            }
    
            .st-key-route_action_bar {
              border-radius: 18px !important;
            }
    
            .st-key-route_action_bar [data-testid="stHorizontalBlock"] {
              grid-template-columns: 1fr 1fr !important;
            }
    
            .st-key-route_action_bar .stButton > button {
              font-size: 0.78rem !important;
              min-height: 2.34rem !important;
              padding: 0.38rem 0.4rem !important;
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )



def apply_explicit_theme_css() -> None:
    dark = current_theme_mode() == "dark"
    palette = {
        "mode": "dark" if dark else "light",
        "bg": "#0F172A" if dark else "#F6F8FC",
        "page_top": "#111827" if dark else "#FFFFFF",
        "surface": "#182235" if dark else "#FFFFFF",
        "surface_raised": "#1F2937" if dark else "#F9FBFF",
        "ink": "#F8FAFC" if dark else "#111827",
        "muted": "#D1D5DB" if dark else "#374151",
        "soft": "#B6C2D3" if dark else "#64748B",
        "line": "#3B4A60" if dark else "#D6DEEA",
        "primary": "#7DD3FC" if dark else "#1D4ED8",
        "primary_strong": "#BAE6FD" if dark else "#1E40AF",
        "primary_soft": "rgba(125, 211, 252, 0.16)" if dark else "#E8F0FF",
        "info": "#5EEAD4" if dark else "#0F766E",
        "info_soft": "rgba(94, 234, 212, 0.16)" if dark else "#E7F7F4",
        "action": "#FB923C" if dark else "#C2410C",
        "action_soft": "rgba(251, 146, 60, 0.18)" if dark else "#FFF1E7",
        "active_fg": "#082F49" if dark else "#FFFFFF",
        "action_fg": "#111827" if dark else "#FFFFFF",
        "shadow": "0 16px 38px rgba(0, 0, 0, 0.32)" if dark else "0 14px 34px rgba(15, 23, 42, 0.10)",
        "shadow_soft": "0 8px 22px rgba(0, 0, 0, 0.24)" if dark else "0 6px 18px rgba(15, 23, 42, 0.08)",
        "map_bg": "#111827" if dark else "#FFFFFF",
        "map_line": "#334155" if dark else "#D6DEEA",
        "select_hover": "#24324A" if dark else "#EAF1FF",
        "select_active": "#0B3551" if dark else "#DBEAFE",
    }
    st.markdown(
        f"""
        <style>
          :root {{
            --rr-bg: {palette["bg"]};
            --rr-page-top: {palette["page_top"]};
            --rr-surface: {palette["surface"]};
            --rr-surface-raised: {palette["surface_raised"]};
            --rr-ink: {palette["ink"]};
            --rr-muted: {palette["muted"]};
            --rr-soft: {palette["soft"]};
            --rr-line: {palette["line"]};
            --rr-primary: {palette["primary"]};
            --rr-primary-strong: {palette["primary_strong"]};
            --rr-primary-soft: {palette["primary_soft"]};
            --rr-info: {palette["info"]};
            --rr-info-soft: {palette["info_soft"]};
            --rr-action: {palette["action"]};
            --rr-action-soft: {palette["action_soft"]};
            --rr-glass: {palette["surface"]};
            --rr-shadow: {palette["shadow"]};
            --rr-shadow-soft: {palette["shadow_soft"]};
            --rr-space-xs: 4px;
            --rr-space-sm: 8px;
            --rr-space-md: 12px;
            --rr-space-lg: 16px;
            --rr-space-xl: 24px;
            --rr-space-2xl: 32px;
            --rr-space-3xl: 40px;
          }}

          html, body, .stApp {{
            color-scheme: {palette["mode"]} !important;
          }}

          .stApp,
          [data-testid="stAppViewContainer"],
          [data-testid="stMain"],
          [data-testid="stMainBlockContainer"],
          section.main {{
            background: var(--rr-bg) !important;
            color: var(--rr-ink) !important;
          }}

          .block-container {{
            max-width: 1120px !important;
            padding: var(--rr-space-lg) var(--rr-space-xl) var(--rr-space-2xl) !important;
          }}

          [data-testid="stVerticalBlock"] {{
            gap: var(--rr-space-lg) !important;
          }}

          .rr-app-shell {{
            display: block !important;
            margin: 0 0 var(--rr-space-lg) !important;
            padding: var(--rr-space-lg) var(--rr-space-xl) !important;
            max-height: 120px !important;
            background: var(--rr-surface) !important;
            border: 1px solid var(--rr-line) !important;
            border-radius: 16px !important;
            box-shadow: var(--rr-shadow-soft) !important;
          }}

          .rr-brand-name {{
            color: var(--rr-ink) !important;
            font-size: 1.22rem !important;
            line-height: 1.15 !important;
            font-weight: 930 !important;
            margin-bottom: var(--rr-space-xs) !important;
          }}

          .rr-brand-tagline {{
            color: var(--rr-ink) !important;
            font-size: 1rem !important;
            line-height: 1.35 !important;
            font-weight: 850 !important;
            margin-bottom: var(--rr-space-xs) !important;
          }}

          .rr-brand-sub,
          .rr-session-pill,
          .rr-theme-toggle-label {{
            color: var(--rr-muted) !important;
          }}

          .rr-theme-toggle-label {{
            font-size: 0.72rem !important;
            font-weight: 850 !important;
            text-align: right !important;
            margin-bottom: var(--rr-space-xs) !important;
          }}

          .rr-route-hero {{
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) auto !important;
            gap: var(--rr-space-lg) !important;
            align-items: center !important;
            padding: var(--rr-space-lg) !important;
            margin-bottom: var(--rr-space-lg) !important;
            background: var(--rr-surface) !important;
            border: 1px solid var(--rr-line) !important;
            border-radius: 16px !important;
            box-shadow: var(--rr-shadow-soft) !important;
            overflow: hidden !important;
            max-height: 120px !important;
          }}

          .rr-hero-copyblock {{
            min-width: 0 !important;
            align-self: center !important;
          }}

          .rr-hero-kicker {{
            color: var(--rr-primary-strong) !important;
            font-size: 0.78rem !important;
            font-weight: 920 !important;
            margin-bottom: var(--rr-space-xs) !important;
          }}

          .rr-hero-title,
          .rr-bento-title,
          .rr-section-title,
          h1, h2, h3, h4,
          p, li, label,
          [data-testid="stMarkdownContainer"],
          [data-testid="stWidgetLabel"] {{
            color: var(--rr-ink) !important;
          }}

          .rr-hero-copy,
          .rr-bento-body,
          .rr-muted {{
            color: var(--rr-muted) !important;
          }}

          .rr-hero-title {{
            margin: 0 0 var(--rr-space-sm) !important;
          }}

          .rr-hero-copy {{
            margin: 0 !important;
          }}

          .rr-use-guide {{
            display: flex !important;
            flex-wrap: wrap !important;
            justify-content: flex-end !important;
            gap: var(--rr-space-sm) !important;
            min-width: 18rem !important;
            margin: 0 !important;
          }}

          .rr-use-guide span {{
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: var(--rr-space-xs) !important;
            min-height: 32px !important;
            border-radius: 999px !important;
            border: 1px solid var(--rr-line) !important;
            background: var(--rr-surface-raised) !important;
            color: var(--rr-ink) !important;
            font-size: 0.76rem !important;
            font-weight: 880 !important;
            white-space: nowrap !important;
            padding: var(--rr-space-xs) var(--rr-space-sm) !important;
          }}

          .rr-use-guide b {{
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 1.2rem !important;
            height: 1.2rem !important;
            border-radius: 999px !important;
            background: var(--rr-primary) !important;
            color: {palette["active_fg"]} !important;
            font-size: 0.7rem !important;
          }}

          .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"],
          .rr-bento-card,
          .rr-progressive-panel,
          .rr-history-card,
          .rr-resource-card,
          .rr-panel,
          .st-key-route_action_bar {{
            background: var(--rr-surface) !important;
            border-color: var(--rr-line) !important;
            box-shadow: var(--rr-shadow-soft) !important;
          }}

          .rr-choice-row {{
            margin: 0 0 var(--rr-space-lg) !important;
          }}

          .rr-section-heading {{
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            gap: var(--rr-space-md) !important;
            margin: 0 0 var(--rr-space-sm) !important;
          }}

          .rr-section-heading span {{
            color: var(--rr-ink) !important;
            font-size: 1rem !important;
            font-weight: 930 !important;
          }}

          .rr-section-heading strong {{
            color: var(--rr-primary-strong) !important;
            font-size: 0.82rem !important;
            font-weight: 900 !important;
            border: 1px solid var(--rr-line) !important;
            background: var(--rr-surface-raised) !important;
            border-radius: 999px !important;
            padding: var(--rr-space-xs) var(--rr-space-sm) !important;
          }}

          .rr-choice-row [data-testid="stVerticalBlockBorderWrapper"] {{
            padding: var(--rr-space-md) !important;
          }}

          .rr-choice-label {{
            margin-bottom: var(--rr-space-sm) !important;
          }}

          .rr-use-guide b,
          [data-baseweb="tab"][aria-selected="true"],
          [data-testid="stBaseButton-segmented_controlActive"] {{
            background: var(--rr-primary) !important;
            border-color: var(--rr-primary) !important;
            color: {palette["active_fg"]} !important;
          }}

          .rr-use-guide b *,
          [data-baseweb="tab"][aria-selected="true"] *,
          [data-testid="stBaseButton-segmented_controlActive"] *,
          [data-testid="stBaseButton-segmented_controlActive"] p,
          [data-testid="stBaseButton-segmented_controlActive"] span {{
            color: {palette["active_fg"]} !important;
          }}

          [data-testid="stBaseButton-segmented_control"],
          [data-testid="stBaseButton-secondary"],
          .stButton > button {{
            background: var(--rr-surface-raised) !important;
            border-color: var(--rr-line) !important;
            color: var(--rr-ink) !important;
            transition: transform 160ms ease, background 160ms ease, border-color 160ms ease, box-shadow 160ms ease !important;
          }}

          [data-testid="stBaseButton-segmented_control"] *,
          [data-testid="stBaseButton-secondary"] *,
          .stButton > button * {{
            color: inherit !important;
          }}

          [data-testid="stBaseButton-segmented_control"]:hover,
          [data-testid="stBaseButton-secondary"]:hover,
          .stButton > button:hover {{
            border-color: var(--rr-primary) !important;
            box-shadow: 0 0 0 3px var(--rr-primary-soft) !important;
            transform: translateY(-1px) !important;
          }}

          [data-testid="stBaseButton-primary"],
          .st-key-route_action_bar [data-testid="stBaseButton-primary"] {{
            background: var(--rr-action) !important;
            border-color: var(--rr-action) !important;
            color: {palette["action_fg"]} !important;
            box-shadow: 0 10px 22px color-mix(in srgb, var(--rr-action) 24%, transparent) !important;
          }}

          [data-testid="stBaseButton-primary"] *,
          .st-key-route_action_bar [data-testid="stBaseButton-primary"] * {{
            color: {palette["action_fg"]} !important;
          }}

          .st-key-route_start_primary .stButton > button {{
            background: var(--rr-action) !important;
            border-color: var(--rr-action) !important;
            color: {palette["action_fg"]} !important;
            font-weight: 920 !important;
          }}

          .st-key-route_complete .stButton > button,
          [class*="st-key-resource_source_"] a,
          [class*="st-key-featured_source_"] a,
          .st-key-map_directions a {{
            background: var(--rr-primary) !important;
            border-color: var(--rr-primary) !important;
            color: {palette["active_fg"]} !important;
            border-radius: 999px !important;
            font-weight: 850 !important;
            text-decoration: none !important;
          }}

          .st-key-route_skip .stButton > button,
          .st-key-route_too_hard .stButton > button,
          .st-key-toggle_advanced_controls .stButton > button,
          .st-key-toggle_more_candidates .stButton > button,
          .st-key-toggle_record_panel .stButton > button,
          .st-key-reset_conditions .stButton > button {{
            background: transparent !important;
            border-color: var(--rr-line) !important;
            color: var(--rr-muted) !important;
            box-shadow: none !important;
          }}

          [data-baseweb="tab-list"],
          [data-baseweb="input"],
          [data-baseweb="select"] > div,
          [data-baseweb="textarea"],
          input, textarea {{
            background: var(--rr-surface) !important;
            border-color: var(--rr-line) !important;
            color: var(--rr-ink) !important;
          }}

          [data-baseweb="select"] *,
          [data-baseweb="input"] *,
          [data-baseweb="textarea"] *,
          input::placeholder,
          textarea::placeholder {{
            color: var(--rr-ink) !important;
          }}

          [data-baseweb="popover"],
          [data-baseweb="popover"] > div,
          [data-baseweb="menu"],
          [role="listbox"] {{
            background: var(--rr-surface) !important;
            border: 1px solid var(--rr-line) !important;
            color: var(--rr-ink) !important;
            box-shadow: var(--rr-shadow) !important;
          }}

          [data-baseweb="popover"] *,
          [data-baseweb="menu"] *,
          [role="listbox"] *,
          [role="option"],
          [role="option"] * {{
            color: var(--rr-ink) !important;
          }}

          [data-baseweb="menu"] li,
          [role="option"] {{
            background: var(--rr-surface) !important;
            color: var(--rr-ink) !important;
          }}

          [data-baseweb="menu"] li:hover,
          [role="option"]:hover,
          [role="option"][aria-selected="true"] {{
            background: {palette["select_hover"]} !important;
            color: var(--rr-ink) !important;
          }}

          [data-baseweb="menu"] li[aria-selected="true"],
          [role="option"][aria-selected="true"] {{
            background: {palette["select_active"]} !important;
          }}

          .rr-bento-row {{
            margin-top: var(--rr-space-lg) !important;
          }}

          .rr-results-header {{
            display: flex !important;
            align-items: end !important;
            justify-content: space-between !important;
            gap: var(--rr-space-md) !important;
            margin: var(--rr-space-lg) 0 var(--rr-space-sm) !important;
          }}

          .rr-results-header span {{
            color: var(--rr-primary-strong) !important;
            font-size: 0.78rem !important;
            font-weight: 920 !important;
          }}

          .rr-results-header strong {{
            color: var(--rr-ink) !important;
            font-size: 1rem !important;
            font-weight: 930 !important;
            text-align: right !important;
          }}

          .rr-bento-card {{
            padding: var(--rr-space-lg) !important;
            border-radius: 16px !important;
          }}

          .rr-card-eyebrow {{
            margin-bottom: var(--rr-space-sm) !important;
          }}

          .rr-bento-title {{
            margin-bottom: var(--rr-space-sm) !important;
          }}

          .rr-bento-body {{
            margin-bottom: var(--rr-space-md) !important;
          }}

          .rr-mini-facts {{
            gap: var(--rr-space-sm) !important;
            margin-top: var(--rr-space-md) !important;
          }}

          .rr-resource-layout {{
            display: grid !important;
            grid-template-columns: 7.2rem minmax(0, 1fr) !important;
            gap: var(--rr-space-md) !important;
            align-items: center !important;
          }}

          .rr-resource-art {{
            width: 100% !important;
            height: 96px !important;
            min-height: 96px !important;
            border-radius: 12px !important;
            object-fit: cover !important;
            background: var(--rr-primary-soft) !important;
            border: 1px solid var(--rr-line) !important;
          }}

          .rr-source-link {{
            background: var(--rr-primary) !important;
            border-color: var(--rr-primary) !important;
            color: {palette["active_fg"]} !important;
          }}

          .rr-source-link * {{
            color: {palette["active_fg"]} !important;
          }}

          .rr-map {{
            background: {palette["map_bg"]} !important;
            border-color: {palette["map_line"]} !important;
          }}

          .rr-map.compact {{
            height: 120px !important;
          }}

          .rr-map.expanded {{
            height: 21rem !important;
          }}

          .rr-map-label {{
            background: var(--rr-surface) !important;
            color: var(--rr-ink) !important;
            border: 1px solid var(--rr-line) !important;
          }}

          .rr-map-label small,
          .rr-official-line,
          .rr-card-eyebrow {{
            color: var(--rr-soft) !important;
          }}

          .st-key-route_action_bar {{
            position: sticky !important;
            bottom: var(--rr-space-sm) !important;
            z-index: 20 !important;
            margin-top: var(--rr-space-md) !important;
            padding: var(--rr-space-md) !important;
            border-radius: 16px !important;
          }}

          .st-key-route_action_bar [data-testid="stHorizontalBlock"] {{
            display: grid !important;
            grid-template-columns: minmax(0, 1.35fr) repeat(3, minmax(0, 0.85fr)) !important;
            gap: var(--rr-space-sm) !important;
          }}

          .st-key-route_action_bar [data-testid="column"] {{
            width: 100% !important;
            min-width: 0 !important;
          }}

          @media (max-width: 860px) {{
            .block-container {{
              padding: var(--rr-space-md) var(--rr-space-md) var(--rr-space-xl) !important;
            }}

            .rr-app-shell {{
              grid-template-columns: 1fr !important;
              gap: var(--rr-space-sm) !important;
              margin-bottom: var(--rr-space-md) !important;
              padding: var(--rr-space-md) !important;
            }}

            .rr-theme-toggle-label {{
              text-align: left !important;
            }}

            .rr-route-hero,
            .rr-choice-row,
            .rr-bento-row {{
              grid-template-columns: 1fr !important;
            }}

            .rr-use-guide {{
              display: none !important;
            }}

            .rr-resource-art {{
              height: 88px !important;
              min-height: 88px !important;
            }}

            .st-key-route_action_bar [data-testid="stHorizontalBlock"] {{
              grid-template-columns: minmax(0, 1.25fr) repeat(3, minmax(0, 0.8fr)) !important;
              gap: var(--rr-space-sm) !important;
            }}
          }}

          @media (max-width: 430px) {{
            .block-container {{
              padding: var(--rr-space-sm) var(--rr-space-sm) var(--rr-space-lg) !important;
            }}

            .rr-route-hero {{
              padding: var(--rr-space-md) !important;
              margin-bottom: var(--rr-space-lg) !important;
            }}

            .rr-app-shell {{
              padding: var(--rr-space-md) !important;
            }}

            .rr-brand-name {{
              font-size: 1.08rem !important;
            }}

            .rr-brand-tagline {{
              font-size: 0.9rem !important;
            }}

            .rr-brand-sub {{
              font-size: 0.78rem !important;
              line-height: 1.35 !important;
            }}

            .rr-hero-title {{
              font-size: 1rem !important;
              line-height: 1.25 !important;
              margin-bottom: var(--rr-space-xs) !important;
            }}

            .rr-hero-copy {{
              font-size: 0.78rem !important;
              line-height: 1.35 !important;
            }}

            .rr-results-header {{
              align-items: start !important;
              flex-direction: column !important;
              gap: var(--rr-space-xs) !important;
              margin: var(--rr-space-lg) 0 var(--rr-space-sm) !important;
            }}

            .rr-results-header strong {{
              text-align: left !important;
            }}

            .rr-resource-layout {{
              grid-template-columns: 5.8rem minmax(0, 1fr) !important;
              gap: var(--rr-space-sm) !important;
            }}

            .rr-resource-art {{
              height: 80px !important;
              min-height: 80px !important;
            }}

            .st-key-route_action_bar {{
              padding: var(--rr-space-sm) !important;
            }}

            .st-key-route_action_bar [data-testid="stHorizontalBlock"] {{
              grid-template-columns: minmax(0, 1.15fr) repeat(3, minmax(0, 0.8fr)) !important;
              gap: var(--rr-space-xs) !important;
            }}

            .st-key-route_action_bar .stButton > button {{
              font-size: 0.72rem !important;
              padding: var(--rr-space-xs) var(--rr-space-xs) !important;
            }}
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )
