from __future__ import annotations

from rebootroute.database import get_feedback_df, get_outcomes_df, log_feedback, log_outcome
from rebootroute.schemas import FeedbackEvent, FeedbackEventType, OutcomeEvent, OutcomeStatus, OutcomeType


def test_feedback_event_is_stored():
    event = FeedbackEvent(
        user_id="test_user_feedback",
        event_type=FeedbackEventType.too_hard,
        mission_id="mission_001",
        recommended_stage=1,
        burden_after=5,
        appropriateness_rating=2,
        risk_rating=1,
        user_note="생각보다 부담이 컸어요.",
        policy_version="test",
    )
    saved = log_feedback(event)
    assert saved["stored"] is True
    df = get_feedback_df("test_user_feedback")
    assert not df.empty
    assert event.event_id in set(df["event_id"])


def test_outcome_event_is_stored():
    event = OutcomeEvent(
        user_id="test_user_outcome",
        outcome_type=OutcomeType.support_application,
        outcome_status=OutcomeStatus.applied,
        mission_id="mission_007",
        resource_id="resource_004",
        readiness_rating=4,
        burden_after=3,
        result_note="지원 신청 완료",
        policy_version="test",
    )
    saved = log_outcome(event)
    assert saved["stored"] is True
    df = get_outcomes_df("test_user_outcome")
    assert not df.empty
    assert event.outcome_id in set(df["outcome_id"])
    assert "support_application" in set(df["outcome_type"])
