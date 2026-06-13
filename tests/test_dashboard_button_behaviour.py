from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

import rebootroute.dashboard.components.buttons as button_components
import rebootroute.dashboard.state as dashboard_state
import rebootroute.dashboard.views.route_view as route_view
from rebootroute.database import get_progress_df
from rebootroute.schemas import ContactMode, UserProfile


APP_PATH = Path(__file__).resolve().parents[1] / "src" / "rebootroute" / "dashboard" / "app.py"


class _FakeColumn:
    def __init__(self, clicked_key: str | None = None) -> None:
        self.clicked_key = clicked_key

    def button(self, _label: str, *, key: str, **_kwargs: Any) -> bool:
        return key == self.clicked_key

    def selectbox(self, *_args: Any, **_kwargs: Any) -> None:
        return None


class _StopRerun(RuntimeError):
    pass


class _FakeRouteStreamlit:
    def __init__(self, session_state: dict[str, Any], clicked_key: str | None = None) -> None:
        self.session_state = session_state
        self.clicked_key = clicked_key
        self.markdown_values: list[str] = []

    def button(self, _label: str, *, key: str, **_kwargs: Any) -> bool:
        return key == self.clicked_key

    def rerun(self) -> None:
        raise _StopRerun

    def markdown(self, value: str, **_kwargs: Any) -> None:
        self.markdown_values.append(value)

    def columns(self, count: int | list[Any], **_kwargs: Any) -> list[_FakeColumn]:
        size = count if isinstance(count, int) else len(count)
        return [_FakeColumn() for _ in range(size)]

    def text_input(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def text_area(self, *_args: Any, **_kwargs: Any) -> None:
        return None


def _profile() -> UserProfile:
    return UserProfile(
        user_id="button_test_user",
        age=27,
        district="연수구",
        free_text="오늘 테스트",
        future_anxiety=3,
        employment_burden=3,
        outside_burden=3,
        social_burden=3,
        energy_level=3,
        daily_rhythm_level=3,
        preferred_contact_mode=ContactMode.online,
        interests=["culture"],
        max_outdoor_minutes=20,
        budget_limit=0,
        has_support_person=False,
    )


def _mission() -> dict[str, Any]:
    return {
        "mission_id": "mission_button_test",
        "title": "버튼 테스트 미션",
        "reward_points": 1,
        "burden_level": 1,
    }


@pytest.mark.parametrize(
    ("button_key", "expected_status"),
    [
        ("route_start_primary", "started"),
        ("route_complete", "completed"),
        ("route_skip", "skipped"),
        ("route_too_hard", "too_hard"),
    ],
)
def test_bottom_action_buttons_write_progress_status(
    button_key: str,
    expected_status: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'dashboard_buttons.db'}")
    monkeypatch.setattr(button_components.st, "container", lambda **_kwargs: nullcontext())
    monkeypatch.setattr(
        button_components.st,
        "columns",
        lambda *_args, **_kwargs: [_FakeColumn(button_key), _FakeColumn(button_key), _FakeColumn(button_key), _FakeColumn(button_key)],
    )
    monkeypatch.setattr(dashboard_state.st, "rerun", lambda: None)

    button_components.render_bottom_action_bar(_profile(), _mission(), recommended_stage=2)

    progress = get_progress_df("button_test_user")
    assert progress["status"].tolist() == [expected_status]
    assert dashboard_state.st.session_state["last_route_action"]["status"] == expected_status


def test_advanced_controls_toggle_open_and_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    session_state = {"show_advanced_controls": False}
    fake_st = _FakeRouteStreamlit(session_state, clicked_key="toggle_advanced_controls")
    monkeypatch.setattr(route_view, "st", fake_st)

    with pytest.raises(_StopRerun):
        route_view.render_advanced_controls()
    assert session_state["show_advanced_controls"] is True
    assert "last_action_message" not in session_state

    with pytest.raises(_StopRerun):
        route_view.render_advanced_controls()
    assert session_state["show_advanced_controls"] is False
    assert "last_action_message" not in session_state


def test_advanced_controls_render_when_open(monkeypatch: pytest.MonkeyPatch) -> None:
    session_state = {"show_advanced_controls": True}
    fake_st = _FakeRouteStreamlit(session_state, clicked_key=None)
    monkeypatch.setattr(route_view, "st", fake_st)
    monkeypatch.setattr(route_view, "sync_derived_resource_filters", lambda: None)

    route_view.render_advanced_controls()

    assert "지역·조건 직접 조정" in " ".join(fake_st.markdown_values)


def test_operator_tab_is_hidden_on_default_url() -> None:
    app = AppTest.from_file(str(APP_PATH))
    app.run(timeout=20)

    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["내 루트", "정책·문화 찾기", "내 기록"]


def test_operator_tab_is_visible_only_with_operator_query_param() -> None:
    app = AppTest.from_file(str(APP_PATH))
    app.query_params["operator"] = "1"
    app.run(timeout=20)

    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["내 루트", "정책·문화 찾기", "내 기록"]
    assert any("엔지니어 검증" in str(markdown.value) for markdown in app.markdown)
