from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from rebootroute.api.main import app
from rebootroute.data.mock_data import save_mock_data


def test_sample_profile_and_analyze_intake():
    save_mock_data()
    client = TestClient(app)
    sample = client.get("/sample_profile")
    assert sample.status_code == 200
    payload = {
        "age": 27,
        "district": "연수구",
        "free_text": "취업해야 하는데 자신이 없고 사람 만나는 것도 부담돼요. 요즘은 거의 집에만 있어요.",
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
    response = client.post("/analyze_intake", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["recommended_stage"] in range(8)
    assert body["next_3_missions"]
    assert body["recommended_resources"]
    assert body["safety_flag"] is False
    assert "model_info" in body

