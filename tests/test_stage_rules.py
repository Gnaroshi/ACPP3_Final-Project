from __future__ import annotations

from rebootroute.recommender.stage_rules import classify_stage_rule_based


def test_low_energy_high_burden_stays_early_stage():
    profile = {
        "age": 27,
        "district": "연수구",
        "free_text": "",
        "future_anxiety": 5,
        "employment_burden": 5,
        "outside_burden": 4,
        "social_burden": 5,
        "energy_level": 2,
        "daily_rhythm_level": 2,
        "preferred_contact_mode": "online",
        "interests": ["culture", "writing"],
        "max_outdoor_minutes": 20,
        "budget_limit": 0,
        "has_support_person": False,
    }
    decision = classify_stage_rule_based(profile)
    assert decision.recommended_stage in {0, 1}
    assert decision.recommended_stage < 7
    assert "진단" not in decision.explanation


def test_completed_stage_five_can_recommend_mini_work():
    profile = {
        "age": 31,
        "district": "부평구",
        "free_text": "",
        "future_anxiety": 3,
        "employment_burden": 3,
        "outside_burden": 2,
        "social_burden": 2,
        "energy_level": 4,
        "daily_rhythm_level": 4,
        "preferred_contact_mode": "small_group",
        "interests": ["design"],
        "max_outdoor_minutes": 60,
        "budget_limit": 10000,
        "has_support_person": True,
    }
    import pandas as pd

    progress = pd.DataFrame([{"mission_id": "m5", "status": "completed", "stage": 5}])
    decision = classify_stage_rule_based(profile, progress=progress)
    assert decision.recommended_stage == 6

