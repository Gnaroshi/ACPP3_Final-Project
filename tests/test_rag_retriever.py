from __future__ import annotations

from rebootroute.data.mock_data import save_mock_data
from rebootroute.rag.retriever import search_policy_culture_resources


def test_rag_search_returns_grounded_sources():
    save_mock_data()
    result = search_policy_culture_resources("연수구 무료 전시 청년 문화활동", district="연수구", max_burden_level=3, top_k=3)
    assert result["sources"]
    assert "진단" in result["answer"] or "진단이나 치료" in result["answer"]
    assert all(source["burden_level"] <= 3 for source in result["sources"])
