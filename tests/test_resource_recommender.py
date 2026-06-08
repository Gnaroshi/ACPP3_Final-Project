from __future__ import annotations

from rebootroute.data.mock_data import load_raw_data, save_mock_data
from rebootroute.recommender.resource_recommender import rank_resources


def test_rank_resources_prefers_compatible_resources():
    save_mock_data(preserve_resources=True)
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
        "interests": ["culture", "writing", "design"],
        "max_outdoor_minutes": 20,
        "budget_limit": 0,
        "has_support_person": False,
    }
    resources = rank_resources(profile, data["resources"], recommended_stage=1, top_n=5)
    assert len(resources) == 5
    assert resources[0]["score"] >= resources[-1]["score"]
    assert all(resource["burden_level"] <= 5 for resource in resources)
