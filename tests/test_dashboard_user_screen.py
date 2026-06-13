from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "src" / "rebootroute" / "dashboard" / "app.py"
DASHBOARD_DIR = APP_PATH.parent


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"style", "script"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"style", "script"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            text = data.strip()
            if text:
                self.parts.append(text)


def _extract_visible_text(html_text: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(html_text)
    return " ".join(parser.parts)


def _default_dashboard_text() -> str:
    app = AppTest.from_file(str(APP_PATH))
    app.run(timeout=20)
    assert not app.exception

    parts: list[str] = []
    for markdown in app.markdown:
        value = str(markdown.value)
        parts.append(_extract_visible_text(value))
    for collection_name in ["button", "tabs", "selectbox", "text_input"]:
        for element in getattr(app, collection_name):
            label = getattr(element, "label", "")
            if label:
                parts.append(str(label))
    return " ".join(parts)


def _dashboard_style_text() -> str:
    parts = [(DASHBOARD_DIR / "styles.py").read_text()]
    css_dir = DASHBOARD_DIR / "css"
    parts.extend(path.read_text() for path in sorted(css_dir.glob("*.css")))
    return "\n".join(parts)


def test_default_dashboard_explains_user_flow() -> None:
    visible_text = _default_dashboard_text()

    for expected in [
        "RebootRoute",
        "오늘 가능한 만큼만, 인천의 정책·문화 정보를 한 걸음으로 묶습니다.",
        "시간, 대면 부담, 관심 분야, 비용을 고르면 오늘 확인할 공식 자료와 바로 끝낼 작은 행동, 위치 확인을 함께 보여줍니다.",
        "조건 선택 전에 볼 공식 자료",
        "오늘의 조건",
        "오늘 쓸 수 있는 시간",
        "사람 만나는 부담",
        "먼저 보고 싶은 자료",
        "오늘 쓸 비용",
        "공식 자료",
        "전체 자료 보기",
    ]:
        assert expected in visible_text

    for hidden_until_ready in ["오늘 바로 할 행동", "가장 맞는 공식 자료", "장소 확인", "오늘 이걸로 시작"]:
        assert hidden_until_ready not in visible_text

    for raw_preview_fragment in [
        "공식 프로그램입니다. 접수중",
        "문화행사입니다. 진행중",
        "접수중 · 신청기간",
        "진행기간 2026",
        "신청 후 승인 · 2~6명",
        "(평일)14~21시",
        "(토요일)11~16시",
    ]:
        assert raw_preview_fragment not in visible_text


def test_default_dashboard_hides_internal_fields() -> None:
    visible_text = _default_dashboard_text()
    lower_text = visible_text.lower()

    hidden_terms = [
        "resource_id",
        "mission_id",
        "ranking score",
        "rag score",
        "score",
        "raw payload",
        "raw analyze_profile",
        "model metric",
        "metric",
        "source_kind",
        "source_checked_at",
        "operator",
        "debug",
        "운영자 검증",
        "엔지니어 검증",
        "운영자",
        "Rule Stage",
        "ML 보조 Stage",
    ]
    for term in hidden_terms:
        assert term.lower() not in lower_text


def test_dashboard_uses_streamlit_action_buttons_only() -> None:
    source = "\n".join(path.read_text() for path in DASHBOARD_DIR.rglob("*.py"))
    route_source = (DASHBOARD_DIR / "views" / "route_view.py").read_text()

    assert "<button" not in source
    assert "<a " not in source
    assert "onclick" not in source
    assert source.count('type="primary"') == 1
    assert 'button("오늘 이걸로 시작"' in source
    assert "rr-preview-resource-card featured" not in route_source


def test_dashboard_button_keys_and_style_hierarchy_are_explicit() -> None:
    source = "\n".join(path.read_text() for path in DASHBOARD_DIR.rglob("*.py"))
    styles = _dashboard_style_text()
    buttons_source = (DASHBOARD_DIR / "components" / "buttons.py").read_text()

    for line in source.splitlines():
        if "st.button(" in line or ".button(" in line or "form_submit_button(" in line:
            assert "key=" in line

    assert "with st.container(key=widget_key(key))" in buttons_source
    assert "st.link_button(" in buttons_source

    for expected_selector in [
        ".st-key-route_start_primary",
        ".st-key-route_complete",
        ".st-key-route_skip",
        ".st-key-route_too_hard",
        ".st-key-toggle_advanced_controls",
        "[class*=\"st-key-resource_source_\"]",
        "[class*=\"st-key-map_directions\"]",
    ]:
        assert expected_selector in styles


def test_dashboard_surgical_repair_layout_guards() -> None:
    styles = _dashboard_style_text()
    state_source = (DASHBOARD_DIR / "state.py").read_text()

    assert ".st-key-route_action_bar" in styles
    assert "position: static" in styles
    assert ".st-key-top_utility" in styles
    assert "position: fixed" in styles
    assert "position: sticky" not in styles
    assert "ellipsis" not in styles
    assert "text-overflow: clip" in styles
    assert ".st-key-route_secondary_actions" in styles
    assert 'ROUTE_RANGE_OPTIONS = ["전체", "집", "20분", "1시간"]' in state_source
    assert 'ROUTE_CONTACT_OPTIONS = ["전체", "비대면", "낮은 대면", "소규모"]' in state_source
    assert 'ROUTE_INTENT_OPTIONS = ["전체", "지원금", "청년공간", "문화행사", "프로그램"]' in state_source
    assert 'ROUTE_COST_OPTIONS = ["전체", "무료", "저비용"]' in state_source
