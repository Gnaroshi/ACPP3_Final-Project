from __future__ import annotations

from rebootroute.database import get_feedback_df, log_feedback
from rebootroute.schemas import FeedbackEvent, FeedbackEventType


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
