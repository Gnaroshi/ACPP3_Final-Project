from __future__ import annotations

from typing import Any

import pandas as pd

from rebootroute.data.mock_data import load_raw_data
from rebootroute.data.validation import parse_list

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover
    TfidfVectorizer = None
    cosine_similarity = None


def _resource_text(row: pd.Series) -> str:
    tags = parse_list(row.get("career_tags", "")) + parse_list(row.get("recovery_tags", ""))
    fields = [
        row.get("name", ""),
        row.get("description", ""),
        row.get("district", ""),
        row.get("resource_type", ""),
        row.get("cost_type", ""),
        " ".join(tags),
    ]
    return " ".join(str(value) for value in fields if pd.notna(value))


def _fallback_score(query: str, text: str) -> float:
    q_tokens = {token.lower() for token in query.split() if token.strip()}
    t_tokens = {token.lower() for token in text.split() if token.strip()}
    if not q_tokens or not t_tokens:
        return 0.0
    return len(q_tokens & t_tokens) / len(q_tokens)


def search_policy_culture_resources(
    query: str,
    district: str | None = None,
    resource_types: list[str] | None = None,
    max_burden_level: int | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    data = load_raw_data()
    resources = data["resources"].copy()
    allowed_default = {"youth_program", "culture_event", "culture_facility", "support_program"}
    if resource_types:
        resources = resources[resources["resource_type"].isin(resource_types)]
    else:
        resources = resources[resources["resource_type"].isin(allowed_default)]
    if district:
        district_match = resources["district"].astype(str).eq(str(district))
        resources = pd.concat([resources[district_match], resources[~district_match]], ignore_index=True)
    if max_burden_level is not None:
        resources = resources[resources["burden_level"].astype(int) <= int(max_burden_level)]
    if resources.empty:
        return {"query": query, "answer": "조건에 맞는 인천 청년정책·문화활동 자료를 찾지 못했습니다.", "sources": []}

    texts = resources.apply(_resource_text, axis=1).tolist()
    if TfidfVectorizer is not None and cosine_similarity is not None:
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1)
        matrix = vectorizer.fit_transform(texts + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    else:
        scores = [_fallback_score(query, text) for text in texts]
    resources = resources.assign(rag_score=scores)
    ranked = resources.sort_values(["rag_score", "burden_level"], ascending=[False, True]).head(top_k)
    sources: list[dict[str, Any]] = []
    for _, row in ranked.iterrows():
        sources.append(
            {
                "resource_id": row["resource_id"],
                "resource_type": row["resource_type"],
                "name": row["name"],
                "district": row["district"],
                "description": row["description"],
                "burden_level": int(row["burden_level"]),
                "cost_type": row["cost_type"],
                "source_name": row.get("source_name"),
                "source_url": row.get("source_url"),
                "rag_score": round(float(row["rag_score"]), 4),
            }
        )
    names = ", ".join(source["name"] for source in sources[:3])
    answer = (
        "아래 인천 청년정책·문화활동 자료를 근거로 낮은 부담 후보를 찾았습니다. "
        "이 결과는 진단이나 치료가 아니라 정보 탐색을 돕는 참고 자료입니다. "
        f"우선 확인해볼 수 있는 후보는 {names}입니다."
    )
    return {"query": query, "answer": answer, "sources": sources}
