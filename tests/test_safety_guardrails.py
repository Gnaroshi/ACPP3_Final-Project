from __future__ import annotations

from rebootroute.recommender.route_builder import analyze_profile
from rebootroute.schemas import UserProfile


def test_high_risk_text_branches_to_safety_resources():
    profile = UserProfile(
        age=27,
        district="연수구",
        free_text="죽고 싶어요",
        future_anxiety=5,
        employment_burden=5,
        outside_burden=5,
        social_burden=5,
        energy_level=1,
        daily_rhythm_level=1,
        preferred_contact_mode="online",
        interests=["culture"],
        max_outdoor_minutes=0,
        budget_limit=0,
        has_support_person=False,
    )

    result = analyze_profile(profile)

    assert result["safety_flag"] is True
    assert result["risk_type"] == "urgent_support_needed"
    assert result["next_3_missions"] == []
    assert result["recommended_resources"] == []
    assert result["safety_resources"]
