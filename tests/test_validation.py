from __future__ import annotations

from rebootroute.data.mock_data import save_mock_data
from rebootroute.data.validation import validate_all


def test_validate_all_mock_data():
    save_mock_data()
    result = validate_all()
    assert result["profiles"] >= 100
    assert result["resources"] >= 50
    assert result["missions"] >= 30

