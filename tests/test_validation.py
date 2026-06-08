from __future__ import annotations

import pandas as pd

from rebootroute.data.mock_data import save_mock_data
from rebootroute.data.validation import validate_all


def test_validate_all_sample_data():
    paths = save_mock_data()
    result = validate_all()
    assert result["profiles"] >= 100
    assert result["resources"] >= 10
    assert result["missions"] >= 30

    resources = pd.read_csv(paths["resources"])
    assert resources["source_url"].str.startswith("https://").all()
    assert not resources["source_url"].str.contains("example.com").any()
