from __future__ import annotations

from typing import Any

import pandas as pd

from rebootroute.data.validation import parse_list


TEMPLATES = [
    {
        "title": "전시 후기 5줄 작성",
        "description": "관람 또는 온라인 자료 확인 후 5문장 리뷰를 작성해 포트폴리오 씨앗으로 남깁니다.",
        "career_tags": ["writing", "culture"],
        "expected_minutes": 25,
    },
    {
        "title": "청년 대상 홍보 문구 3개 만들기",
        "description": "청년공간이나 지원 프로그램을 부담 낮게 소개하는 카피를 3개 작성합니다.",
        "career_tags": ["writing", "media"],
        "expected_minutes": 20,
    },
    {
        "title": "문화공간 접근성 체크리스트 작성",
        "description": "처음 방문하는 청년 관점에서 안내, 비용, 동선, 대면 부담을 점검합니다.",
        "career_tags": ["planning", "design"],
        "expected_minutes": 30,
    },
    {
        "title": "지역 축제 카드뉴스 초안 만들기",
        "description": "제목, 핵심 메시지, 4장 구성만 잡아도 충분한 카드뉴스 초안을 만듭니다.",
        "career_tags": ["design", "media"],
        "expected_minutes": 45,
    },
    {
        "title": "청년 프로그램 개선 제안 작성",
        "description": "첫 참여 부담을 낮추기 위한 안내 방식, 신청 절차, 공간 분위기 개선안을 정리합니다.",
        "career_tags": ["public_policy", "planning"],
        "expected_minutes": 40,
    },
]


def generate_mini_projects(profile: Any, resources: pd.DataFrame | None = None, limit: int = 4) -> list[dict[str, Any]]:
    if hasattr(profile, "model_dump"):
        p = profile.model_dump(mode="json")
    elif hasattr(profile, "dict"):
        p = profile.dict()
    else:
        p = dict(profile)
    interests = p.get("interests", [])
    if not isinstance(interests, list):
        interests = parse_list(interests)
    rows: list[dict[str, Any]] = []
    resource_names = resources["name"].head(3).tolist() if resources is not None and not resources.empty else []
    for idx, template in enumerate(TEMPLATES):
        overlap = len(set(interests) & set(template["career_tags"]))
        score = 0.55 + overlap * 0.20
        if resource_names:
            score += 0.05
        candidate = dict(template)
        candidate["mini_project_id"] = f"mini_project_candidate_{idx:02d}"
        candidate["score"] = round(min(score, 1.0), 4)
        candidate["suggested_resource_context"] = resource_names[0] if resource_names else None
        candidate["evidence_type"] = "file_upload"
        rows.append(candidate)
    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows[:limit]
