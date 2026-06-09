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


def test_default_dashboard_explains_user_flow() -> None:
    visible_text = _default_dashboard_text()

    for expected in [
        "RebootRoute",
        "오늘 할 수 있는 인천 정책·문화 루트",
        "4가지만 고르면 오늘 확인할 공식 정보와 작은 행동을 추천해요.",
        "조건 선택",
        "오늘 가능한 범위",
        "사람 만나는 정도",
        "찾고 싶은 것",
        "오늘 비용",
        "오늘의 작은 미션",
        "가장 맞는 공식 자원",
        "위치 확인",
        "오늘 이걸로 시작",
        "완료",
        "나중에",
        "어려움",
    ]:
        assert expected in visible_text


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
        "운영자",
        "Rule Stage",
        "ML 보조 Stage",
    ]
    for term in hidden_terms:
        assert term.lower() not in lower_text


def test_dashboard_uses_streamlit_action_buttons_only() -> None:
    source = "\n".join(path.read_text() for path in DASHBOARD_DIR.rglob("*.py"))

    assert "<button" not in source
    assert "<a " not in source
    assert "onclick" not in source
    assert source.count('type="primary"') == 1
    assert 'button("오늘 이걸로 시작"' in source
