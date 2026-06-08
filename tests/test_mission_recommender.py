from __future__ import annotations

from rebootroute.data.mock_data import load_raw_data, save_mock_data
from rebootroute.recommender.mission_recommender import rank_missions


def test_rank_missions_returns_stage_aligned_results():
    save_mock_data()
    data = load_raw_data()
    profile = {
        "age": 27,
        "district": "연수구",
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
    missions = rank_missions(profile, data["missions"], recommended_stage=1, resources=data["resources"], top_n=3)
    assert len(missions) == 3
    assert missions[0]["score"] >= missions[-1]["score"]
    assert all("오늘" in mission["description"] or mission["stage"] <= 2 for mission in missions)

