from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd

from rebootroute.config import ensure_directories, load_config


DISTRICTS = ["중구", "동구", "미추홀구", "연수구", "남동구", "부평구", "계양구", "서구", "강화군", "옹진군"]
CONTACT_MODES = ["online", "low_contact", "small_group", "in_person"]
INTERESTS = ["culture", "design", "writing", "IT", "public_policy", "planning", "library", "media", "craft", "data"]
SAMPLE_GENERATED_AT = "2026-06-08T00:00:00+00:00"
SAMPLE_GENERATED_AT_DT = datetime.fromisoformat(SAMPLE_GENERATED_AT)
OUTCOME_COLUMNS = [
    "outcome_id",
    "user_id",
    "outcome_type",
    "outcome_status",
    "mission_id",
    "resource_id",
    "readiness_rating",
    "burden_after",
    "result_note",
    "operator_review_status",
    "operator_note",
    "evidence_url",
    "policy_version",
    "created_at",
]

FREE_TEXT_TEMPLATES = [
    "취업해야 하는데 자신이 없고 사람 만나는 것도 부담돼요. 요즘은 거의 집에만 있어요.",
    "밖에 나가는 건 어렵지만 오늘 할 수 있는 작은 준비부터 해보고 싶어요.",
    "도서관이나 전시처럼 혼자 갈 수 있는 곳이면 조금 가능할 것 같아요.",
    "진로를 다시 생각해보고 싶은데 바로 교육 신청은 부담스럽습니다.",
    "짧은 글쓰기나 디자인 과제처럼 작은 결과물을 만들어보고 싶어요.",
    "가족이 걱정해서 도움을 알아보라고 했는데 상담부터 시작하기는 어렵습니다.",
    "청년공간이 궁금하지만 처음 방문하는 게 조금 어색합니다.",
    "문화행사나 공모전 주제로 작은 포트폴리오를 만들고 싶습니다.",
]


def _json_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def _now() -> str:
    return SAMPLE_GENERATED_AT


def _write_csv_atomic(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    df.to_csv(tmp_path, index=False)
    tmp_path.replace(path)


def generate_profiles(n: int = 180, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    for i in range(n):
        energy = rng.randint(1, 5)
        outside = min(5, max(1, rng.randint(1, 5) + (1 if energy <= 2 and rng.random() < 0.5 else 0)))
        social = min(5, max(1, rng.randint(1, 5) + (1 if outside >= 4 and rng.random() < 0.4 else 0)))
        employment = rng.randint(2, 5)
        anxiety = min(5, max(1, employment + rng.choice([-1, 0, 0, 1])))
        rhythm = min(5, max(1, energy + rng.choice([-1, 0, 1])))
        if outside >= 4 or social >= 4:
            contact = rng.choice(["online", "online", "low_contact", "small_group"])
        elif energy >= 4:
            contact = rng.choice(CONTACT_MODES)
        else:
            contact = rng.choice(["online", "low_contact", "small_group"])
        interests = rng.sample(INTERESTS, rng.randint(1, 4))
        rows.append(
            {
                "user_id": f"user_{i:04d}",
                "age": rng.randint(19, 39),
                "district": rng.choice(DISTRICTS),
                "free_text": rng.choice(FREE_TEXT_TEMPLATES),
                "future_anxiety": anxiety,
                "employment_burden": employment,
                "outside_burden": outside,
                "social_burden": social,
                "energy_level": energy,
                "daily_rhythm_level": rhythm,
                "preferred_contact_mode": contact,
                "interests": _json_list(interests),
                "max_outdoor_minutes": rng.choice([0, 10, 15, 20, 30, 45, 60, 90]),
                "budget_limit": rng.choice([0, 0, 5000, 10000, 20000]),
                "has_support_person": rng.random() < 0.35,
                "current_stage_label": "",
                "created_at": _now(),
            }
        )
    return pd.DataFrame(rows)


MISSION_SEEDS: list[dict[str, Any]] = [
    {"stage": 0, "title": "오늘 가능한 시간대 하나 고르기", "description": "10분만 쓸 수 있는 시간대를 하나 정합니다. 신청이나 방문은 하지 않습니다.", "mission_type": "micro_action", "minutes": 5, "outdoor": False, "social": False, "evidence": "text_note", "burden": 0, "tags": ["planning", "routine"]},
    {"stage": 0, "title": "덜 부담스러운 조건 2개 고르기", "description": "무료, 집에서 가능, 대면 없음, 20분 이하 중 오늘 덜 부담스러운 조건 2개를 고릅니다.", "mission_type": "micro_action", "minutes": 6, "outdoor": False, "social": False, "evidence": "text_note", "burden": 0, "tags": ["planning", "support"]},
    {"stage": 0, "title": "오늘 피할 조건 하나 적기", "description": "긴 이동, 갑작스러운 대면, 비용 지출처럼 오늘 피해야 할 조건 하나를 적습니다.", "mission_type": "micro_action", "minutes": 4, "outdoor": False, "social": False, "evidence": "text_note", "burden": 0, "tags": ["routine", "planning"]},
    {"stage": 1, "title": "문의 문장 초안 작성하기", "description": "보내지 않아도 됩니다. 운영시간이나 참여 조건을 물어보는 한 문장을 적습니다.", "mission_type": "micro_action", "minutes": 8, "outdoor": False, "social": False, "evidence": "text_note", "burden": 1, "tags": ["support", "planning", "writing"]},
    {"stage": 1, "title": "방문 전 체크리스트 3개 만들기", "description": "시간, 비용, 혼자 가능 여부처럼 방문 전 확인할 항목 3개를 적습니다.", "mission_type": "micro_action", "minutes": 8, "outdoor": False, "social": False, "evidence": "text_note", "burden": 1, "tags": ["culture", "library", "planning"]},
    {"stage": 1, "title": "온라인 신청 전 필요한 정보 정리하기", "description": "신청 버튼을 누르기 전 필요한 준비물, 마감일, 문의 방식을 한 줄로 정리합니다.", "mission_type": "micro_action", "minutes": 10, "outdoor": False, "social": False, "evidence": "text_note", "burden": 1, "tags": ["support", "public_policy", "planning"]},
    {"stage": 2, "title": "운영시간과 마감시간 한 줄로 적기", "description": "관심 있는 장소나 프로그램의 운영시간, 마감시간, 쉬는 날을 한 줄로 정리합니다.", "mission_type": "micro_action", "minutes": 8, "outdoor": False, "social": False, "evidence": "text_note", "burden": 1, "tags": ["planning"]},
    {"stage": 2, "title": "가장 짧은 이동 동선 하나 고르기", "description": "실제로 나가지 않아도 됩니다. 집 근처에서 가능한 짧은 동선을 하나 정합니다.", "mission_type": "micro_action", "minutes": 10, "outdoor": False, "social": False, "evidence": "text_note", "burden": 1, "tags": ["planning", "routine"]},
    {"stage": 2, "title": "오늘 가능해 보이는 것 한 문장 쓰기", "description": "완벽한 계획이 아니라 지금 덜 부담스러운 행동을 한 문장으로 남깁니다.", "mission_type": "micro_action", "minutes": 5, "outdoor": False, "social": False, "evidence": "text_note", "burden": 0, "tags": ["writing", "routine"]},
    {"stage": 3, "title": "도서관 근처까지 가보기", "description": "입장하지 않아도 충분합니다. 장소가 실제로 있다는 것만 확인합니다.", "mission_type": "short_outing", "minutes": 15, "outdoor": True, "social": False, "evidence": "checkin_optional", "burden": 2, "tags": ["library", "culture"]},
    {"stage": 3, "title": "청년공간 주변 산책하기", "description": "사람을 만나지 않아도 됩니다. 근처에서 10분만 머물러봅니다.", "mission_type": "short_outing", "minutes": 20, "outdoor": True, "social": False, "evidence": "photo_optional", "burden": 2, "tags": ["youth_space", "routine"]},
    {"stage": 3, "title": "무료 전시 장소 입구까지 가보기", "description": "오늘은 관람보다 입구까지 가보고 돌아오는 것이 목표입니다.", "mission_type": "short_outing", "minutes": 20, "outdoor": True, "social": False, "evidence": "checkin_optional", "burden": 2, "tags": ["culture", "design"]},
    {"stage": 4, "title": "무료 전시 20분 관람", "description": "대화하지 않아도 되는 전시를 짧게 둘러봅니다.", "mission_type": "low_contact_participation", "minutes": 25, "outdoor": True, "social": False, "evidence": "text_note", "burden": 3, "tags": ["culture", "design"]},
    {"stage": 4, "title": "도서관 자료실 방문", "description": "책을 빌리지 않아도 됩니다. 자료실 분위기만 확인합니다.", "mission_type": "low_contact_participation", "minutes": 20, "outdoor": True, "social": False, "evidence": "checkin_optional", "burden": 2, "tags": ["library", "routine"]},
    {"stage": 4, "title": "소규모 청년 프로그램 맛보기", "description": "참여 시간이 짧고 대화 부담이 낮은 프로그램을 살펴봅니다.", "mission_type": "program_participation", "minutes": 40, "outdoor": True, "social": True, "evidence": "text_note", "burden": 3, "tags": ["youth_program", "planning"]},
    {"stage": 5, "title": "전시 후기 5줄 작성", "description": "관람 경험이나 온라인 자료를 바탕으로 짧은 후기를 작성합니다.", "mission_type": "career_exploration", "minutes": 20, "outdoor": False, "social": False, "evidence": "text_note", "burden": 2, "tags": ["writing", "culture"]},
    {"stage": 5, "title": "홍보 문구 3개 만들기", "description": "청년 프로그램을 더 쉽게 알릴 수 있는 짧은 문구를 3개 적습니다.", "mission_type": "career_exploration", "minutes": 20, "outdoor": False, "social": False, "evidence": "text_note", "burden": 2, "tags": ["writing", "media"]},
    {"stage": 5, "title": "청년 프로그램 2개 비교하기", "description": "대상, 시간, 신청 부담을 비교하며 나에게 덜 부담스러운 선택지를 찾습니다.", "mission_type": "career_exploration", "minutes": 25, "outdoor": False, "social": False, "evidence": "text_note", "burden": 2, "tags": ["planning", "public_policy"]},
    {"stage": 5, "title": "문화공간 접근성 체크리스트 작성", "description": "처음 방문하는 청년 관점에서 안내, 동선, 비용, 분위기를 체크합니다.", "mission_type": "career_exploration", "minutes": 25, "outdoor": False, "social": False, "evidence": "text_note", "burden": 2, "tags": ["planning", "design"]},
    {"stage": 6, "title": "지역 축제 카드뉴스 초안 만들기", "description": "이미지 없이 제목, 핵심 문구, 순서만 구성해도 됩니다.", "mission_type": "mini_work_experience", "minutes": 45, "outdoor": False, "social": False, "evidence": "file_upload", "burden": 3, "tags": ["design", "media"]},
    {"stage": 6, "title": "청년공간 개선 제안 1쪽 작성", "description": "처음 이용하는 사람의 부담을 낮추는 아이디어를 정리합니다.", "mission_type": "mini_work_experience", "minutes": 40, "outdoor": False, "social": False, "evidence": "file_upload", "burden": 3, "tags": ["planning", "public_policy"]},
    {"stage": 6, "title": "문화행사 짧은 리뷰 콘텐츠 만들기", "description": "5문장 리뷰와 추천 대상을 함께 적어 포트폴리오 씨앗으로 남깁니다.", "mission_type": "mini_work_experience", "minutes": 35, "outdoor": False, "social": False, "evidence": "file_upload", "burden": 3, "tags": ["writing", "culture"]},
    {"stage": 6, "title": "간단한 이용자 경험 점검표 만들기", "description": "접근성, 안내문, 비용, 첫 방문 부담을 기준으로 점검표를 만듭니다.", "mission_type": "mini_work_experience", "minutes": 35, "outdoor": False, "social": False, "evidence": "file_upload", "burden": 3, "tags": ["design", "data"]},
    {"stage": 7, "title": "직무훈련 상담 질문 3개 정리", "description": "신청하지 않아도 됩니다. 대상, 시간, 문의 방식에 대해 물어볼 질문을 3개 적습니다.", "mission_type": "self_reliance_link", "minutes": 15, "outdoor": False, "social": False, "evidence": "text_note", "burden": 2, "tags": ["career", "support"]},
    {"stage": 7, "title": "상담 전 질문 하나 준비", "description": "상담을 예약하지 않아도 됩니다. 언젠가 물어볼 질문 하나만 적습니다.", "mission_type": "self_reliance_link", "minutes": 10, "outdoor": False, "social": False, "evidence": "text_note", "burden": 2, "tags": ["career", "planning"]},
    {"stage": 7, "title": "지역 일경험 기회 하나 살펴보기", "description": "지원 여부보다 부담 수준과 관심 직무가 맞는지 확인합니다.", "mission_type": "self_reliance_link", "minutes": 15, "outdoor": False, "social": False, "evidence": "link_click", "burden": 2, "tags": ["career", "mini_project"]},
]


def generate_missions(seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    for i, mission in enumerate(MISSION_SEEDS):
        tags = mission["tags"]
        career_tags = [tag for tag in tags if tag in {"writing", "design", "IT", "planning", "public_policy", "media", "data", "career"}]
        recovery_tags = [tag for tag in tags if tag not in career_tags]
        rows.append(
            {
                "mission_id": f"mission_{i:03d}",
                "stage": mission["stage"],
                "title": mission["title"],
                "description": mission["description"],
                "mission_type": mission["mission_type"],
                "expected_minutes": mission["minutes"],
                "outdoor_required": mission["outdoor"],
                "social_contact_required": mission["social"],
                "evidence_type": mission["evidence"],
                "burden_level": mission["burden"],
                "reward_points": 5 + mission["stage"] * 3 + rng.randint(0, 3),
                "career_tags": _json_list(career_tags),
                "recovery_tags": _json_list(recovery_tags),
            }
        )

    # Add deterministic variants to reach a richer 30-50 mission board.
    variant_titles = [
        ("오늘 가능한 조건 2개 체크하기", "micro_action", 0, False, False, "text_note", 0, ["support", "planning"]),
        ("문의 문장 한 줄 적기", "micro_action", 1, False, False, "text_note", 1, ["planning", "writing"]),
        ("방문 가능한 요일 하나 정하기", "micro_action", 2, False, False, "text_note", 1, ["routine"]),
        ("집 근처 공원 입구 확인하기", "short_outing", 3, True, False, "checkin_optional", 2, ["routine"]),
        ("짧은 문화 프로그램 후기 읽기", "low_contact_participation", 4, False, False, "text_note", 2, ["culture"]),
        ("청년정책 개선 아이디어 3개 적기", "career_exploration", 5, False, False, "text_note", 2, ["public_policy", "writing"]),
        ("지역 문제 해결 미니 제안서 만들기", "mini_work_experience", 6, False, False, "file_upload", 3, ["planning", "public_policy"]),
        ("취업지원센터 이용 방법 확인하기", "self_reliance_link", 7, False, False, "link_click", 2, ["career"]),
    ]
    start = len(rows)
    for idx, (title, mission_type, stage, outdoor, social, evidence, burden, tags) in enumerate(variant_titles * 2):
        career_tags = [tag for tag in tags if tag in {"writing", "design", "IT", "planning", "public_policy", "media", "data", "career"}]
        recovery_tags = [tag for tag in tags if tag not in career_tags]
        rows.append(
            {
                "mission_id": f"mission_{start + idx:03d}",
                "stage": stage,
                "title": title,
                "description": "부담을 낮춘 단계형 미션입니다. 오늘은 가능한 만큼만 진행해도 충분합니다.",
                "mission_type": mission_type,
                "expected_minutes": 8 + stage * 5,
                "outdoor_required": outdoor,
                "social_contact_required": social,
                "evidence_type": evidence,
                "burden_level": burden,
                "reward_points": 4 + stage * 3,
                "career_tags": _json_list(career_tags),
                "recovery_tags": _json_list(recovery_tags),
            }
        )
    return pd.DataFrame(rows)


REAL_RESOURCE_SEEDS: list[dict[str, Any]] = [
    {
        "resource_id": "resource_000",
        "resource_type": "youth_program",
        "name": "인천광역시 청년지원센터 유유기지",
        "description": "인천 청년이 무료로 이용할 수 있는 청년공간입니다. 코워킹, 소규모 회의, 청년교육 프로그램, 상담 연결 전 정보 확인에 적합합니다.",
        "district": "미추홀구",
        "address": "인천광역시 미추홀구 석정로 229 제물포스마트타운 14-15층",
        "latitude": 37.4773,
        "longitude": 126.6639,
        "start_date": "",
        "end_date": "",
        "cost_type": "free",
        "online_available": True,
        "social_contact_level": 2,
        "outdoor_required": True,
        "estimated_duration_minutes": 30,
        "burden_level": 2,
        "career_tags": ["planning", "writing", "public_policy"],
        "recovery_tags": ["youth_space", "low_contact", "routine"],
        "source_name": "인천청년포털",
        "source_url": "https://youth.incheon.go.kr/youth/incheon.jsp",
        "contact": "032-725-3061",
    },
    {
        "resource_id": "resource_001",
        "resource_type": "youth_program",
        "name": "유유기지 부평",
        "description": "부평권 청년이 무료로 이용할 수 있는 열린 청년공간입니다. 휴식, 학습, 회의실 대관, 프로그램 확인에 활용할 수 있습니다.",
        "district": "부평구",
        "address": "인천광역시 부평구 부평대로 301, 116호",
        "latitude": 37.5194,
        "longitude": 126.7049,
        "start_date": "",
        "end_date": "",
        "cost_type": "free",
        "online_available": True,
        "social_contact_level": 2,
        "outdoor_required": True,
        "estimated_duration_minutes": 30,
        "burden_level": 2,
        "career_tags": ["planning", "writing"],
        "recovery_tags": ["youth_space", "low_contact", "routine"],
        "source_name": "인천청년포털",
        "source_url": "https://youth.incheon.go.kr/youth/bupyeong.jsp",
        "contact": "032-363-3141",
    },
    {
        "resource_id": "resource_002",
        "resource_type": "youth_program",
        "name": "동구청년21",
        "description": "동구 청년공간입니다. 공간 위치와 운영 정보를 먼저 확인하고, 필요하면 프로그램 신청이나 방문 계획으로 이어갈 수 있습니다.",
        "district": "동구",
        "address": "인천광역시 동구 송림로 14",
        "latitude": 37.4739,
        "longitude": 126.6427,
        "start_date": "",
        "end_date": "",
        "cost_type": "free",
        "online_available": True,
        "social_contact_level": 2,
        "outdoor_required": True,
        "estimated_duration_minutes": 30,
        "burden_level": 2,
        "career_tags": ["planning", "public_policy"],
        "recovery_tags": ["youth_space", "low_contact"],
        "source_name": "인천청년포털",
        "source_url": "https://youth.incheon.go.kr/space/donggu/space/location.jsp",
        "contact": "032-766-6077",
    },
    {
        "resource_id": "resource_003",
        "resource_type": "youth_program",
        "name": "계양청년마당",
        "description": "계양구 청년공간입니다. 청년공간 위치, 프로그램 공지, 취업역량 강화 프로그램을 한 곳에서 확인할 수 있습니다.",
        "district": "계양구",
        "address": "인천광역시 계양구 계산새로 88 계양구청 2층",
        "latitude": 37.5375,
        "longitude": 126.7377,
        "start_date": "",
        "end_date": "",
        "cost_type": "free",
        "online_available": True,
        "social_contact_level": 2,
        "outdoor_required": True,
        "estimated_duration_minutes": 30,
        "burden_level": 2,
        "career_tags": ["planning", "public_policy"],
        "recovery_tags": ["youth_space", "low_contact"],
        "source_name": "인천청년포털",
        "source_url": "https://youth.incheon.go.kr/space/gyeyang/",
        "contact": "032-450-8356",
    },
    {
        "resource_id": "resource_004",
        "resource_type": "support_program",
        "name": "청년도전 지원사업",
        "description": "취업·교육·직업훈련 참여 이력이 적은 청년에게 상담, 자신감 회복, 진로탐색, 취업역량 강화 프로그램을 제공하는 인천 청년정책입니다.",
        "district": "인천 전역",
        "address": "인천광역시 남동구 정각로 29",
        "latitude": 37.4563,
        "longitude": 126.7052,
        "start_date": "2026-01-29",
        "end_date": "2026-09-30",
        "cost_type": "free",
        "online_available": True,
        "social_contact_level": 3,
        "outdoor_required": False,
        "estimated_duration_minutes": 20,
        "burden_level": 3,
        "career_tags": ["career", "planning", "public_policy"],
        "recovery_tags": ["support", "routine"],
        "source_name": "인천청년포털",
        "source_url": "https://youth.incheon.go.kr/job/challenge.jsp",
        "contact": "032-725-3080~4",
    },
    {
        "resource_id": "resource_005",
        "resource_type": "support_program",
        "name": "드림체크카드 구직활동비 지원",
        "description": "인천 거주 미취업 청년의 구직활동비를 지원하는 정책입니다. 접수 여부와 자격 조건은 공식 페이지에서 확인해야 합니다.",
        "district": "인천 전역",
        "address": "인천광역시 남동구 정각로 29",
        "latitude": 37.4563,
        "longitude": 126.7052,
        "start_date": "",
        "end_date": "",
        "cost_type": "free",
        "online_available": True,
        "social_contact_level": 1,
        "outdoor_required": False,
        "estimated_duration_minutes": 20,
        "burden_level": 2,
        "career_tags": ["career", "planning", "public_policy"],
        "recovery_tags": ["support"],
        "source_name": "인천청년포털",
        "source_url": "https://youth.incheon.go.kr/youthpolicy/youthPolicyInfoDetail.do?poly_seq=417",
        "contact": "공식 페이지 확인",
    },
    {
        "resource_id": "resource_006",
        "resource_type": "support_program",
        "name": "인천 청년도약기지",
        "description": "직무교육과 현장실무 중심 인턴십 과정을 결합한 청년 일경험·취업연계 정책입니다. 과정별 신청 가능 여부를 공식 페이지에서 확인합니다.",
        "district": "인천 전역",
        "address": "인천광역시 남동구 정각로 29",
        "latitude": 37.4563,
        "longitude": 126.7052,
        "start_date": "2026-03-01",
        "end_date": "2026-12-31",
        "cost_type": "free",
        "online_available": True,
        "social_contact_level": 3,
        "outdoor_required": False,
        "estimated_duration_minutes": 25,
        "burden_level": 3,
        "career_tags": ["career", "IT", "planning", "data"],
        "recovery_tags": ["support"],
        "source_name": "인천청년포털",
        "source_url": "https://youth.incheon.go.kr/job/leap.jsp",
        "contact": "공식 페이지 확인",
    },
    {
        "resource_id": "resource_007",
        "resource_type": "support_program",
        "name": "유유기지 인천 프로그램 신청",
        "description": "유유기지 인천에서 운영하는 프로그램 목록을 확인하는 공식 신청 화면입니다. 바로 신청하지 않고 관심 프로그램 조건만 확인하는 데 적합합니다.",
        "district": "미추홀구",
        "address": "인천광역시 미추홀구 석정로 229 제물포스마트타운",
        "latitude": 37.4773,
        "longitude": 126.6639,
        "start_date": "",
        "end_date": "",
        "cost_type": "free",
        "online_available": True,
        "social_contact_level": 2,
        "outdoor_required": False,
        "estimated_duration_minutes": 15,
        "burden_level": 1,
        "career_tags": ["planning", "writing", "public_policy"],
        "recovery_tags": ["youth_space", "low_contact"],
        "source_name": "인천청년포털",
        "source_url": "https://youth.incheon.go.kr/program/programInfoList.do?prgm_div=inuu&prgmdiv=all",
        "contact": "온라인 확인",
    },
    {
        "resource_id": "resource_008",
        "resource_type": "culture_facility",
        "name": "인천아트플랫폼",
        "description": "인천문화재단이 운영하는 문화예술 창작공간입니다. 전시, 공연, 교육 프로그램과 공간 정보를 확인할 수 있습니다.",
        "district": "중구",
        "address": "인천광역시 중구 제물량로218번길 3",
        "latitude": 37.472,
        "longitude": 126.6209,
        "start_date": "",
        "end_date": "",
        "cost_type": "unknown",
        "online_available": True,
        "social_contact_level": 2,
        "outdoor_required": True,
        "estimated_duration_minutes": 40,
        "burden_level": 2,
        "career_tags": ["design", "media", "writing"],
        "recovery_tags": ["culture", "low_contact"],
        "source_name": "인천아트플랫폼",
        "source_url": "https://inartplatform.kr/intro/about",
        "contact": "032-760-1000",
    },
    {
        "resource_id": "resource_009",
        "resource_type": "culture_facility",
        "name": "트라이보울",
        "description": "인천문화재단이 운영하는 복합문화예술공간입니다. 공연, 전시, 문화예술교육 일정을 확인할 수 있습니다.",
        "district": "연수구",
        "address": "인천광역시 연수구 인천타워대로 250",
        "latitude": 37.3953,
        "longitude": 126.6348,
        "start_date": "",
        "end_date": "",
        "cost_type": "unknown",
        "online_available": True,
        "social_contact_level": 2,
        "outdoor_required": True,
        "estimated_duration_minutes": 40,
        "burden_level": 2,
        "career_tags": ["design", "media", "planning"],
        "recovery_tags": ["culture", "low_contact"],
        "source_name": "트라이보울",
        "source_url": "https://tribowl.kr/_NBoard/page.php?hid=sub_0102",
        "contact": "032-832-7996",
    },
    {
        "resource_id": "resource_010",
        "resource_type": "culture_facility",
        "name": "인천생활문화센터 칠통마당",
        "description": "시민이 생활문화 활동과 프로그램을 경험할 수 있는 인천문화재단 운영 문화공간입니다.",
        "district": "중구",
        "address": "인천광역시 중구 제물량로218번길 3",
        "latitude": 37.472,
        "longitude": 126.6209,
        "start_date": "",
        "end_date": "",
        "cost_type": "unknown",
        "online_available": True,
        "social_contact_level": 2,
        "outdoor_required": True,
        "estimated_duration_minutes": 35,
        "burden_level": 2,
        "career_tags": ["craft", "planning", "media"],
        "recovery_tags": ["culture", "low_contact"],
        "source_name": "인천문화재단",
        "source_url": "https://www.ifac.or.kr/ifacintro/facilities/7tong.do?key=m2502106873483",
        "contact": "032-760-1007",
    },
    {
        "resource_id": "resource_011",
        "resource_type": "culture_facility",
        "name": "인천청년문화창작소 시작공간 일부",
        "description": "문화예술에 관심 있는 청년과 청년 창작자를 위한 공유 공간입니다. 네트워킹, 역량강화 프로그램, 아카이브 공간 정보를 확인할 수 있습니다.",
        "district": "중구",
        "address": "인천광역시 중구 참외전로 100",
        "latitude": 37.4777,
        "longitude": 126.6315,
        "start_date": "",
        "end_date": "",
        "cost_type": "unknown",
        "online_available": True,
        "social_contact_level": 3,
        "outdoor_required": True,
        "estimated_duration_minutes": 45,
        "burden_level": 3,
        "career_tags": ["design", "media", "planning", "writing"],
        "recovery_tags": ["culture", "youth_space"],
        "source_name": "인천문화재단",
        "source_url": "https://ifac.or.kr/ifacintro/facilities/space1bu.do?key=m2502106873697",
        "contact": "032-766-5976~8",
    },
    {
        "resource_id": "resource_012",
        "resource_type": "culture_facility",
        "name": "한국근대문학관",
        "description": "인천 개항장 일대 창고 건물을 리모델링한 문학관입니다. 상설전시, 기획전시, 교육프로그램을 확인할 수 있습니다.",
        "district": "중구",
        "address": "인천광역시 중구 신포로15번길 76",
        "latitude": 37.4727,
        "longitude": 126.6217,
        "start_date": "",
        "end_date": "",
        "cost_type": "unknown",
        "online_available": True,
        "social_contact_level": 1,
        "outdoor_required": True,
        "estimated_duration_minutes": 40,
        "burden_level": 2,
        "career_tags": ["writing", "media"],
        "recovery_tags": ["culture", "low_contact"],
        "source_name": "인천문화재단",
        "source_url": "https://www.ifac.or.kr/ifacintro/facilities/museum.do?key=m2502106873592",
        "contact": "공식 페이지 확인",
    },
    {
        "resource_id": "resource_013",
        "resource_type": "culture_event",
        "name": "인천문화재단 문화행사 정보",
        "description": "인천문화재단 문화행사 목록에서 공연, 전시, 행사·축제, 교육·체험 정보를 확인할 수 있습니다. 진행 상태와 일정은 공식 페이지에서 최신 상태로 확인합니다.",
        "district": "인천 전역",
        "address": "인천광역시 일대",
        "latitude": 37.4563,
        "longitude": 126.7052,
        "start_date": "",
        "end_date": "",
        "cost_type": "unknown",
        "online_available": True,
        "social_contact_level": 1,
        "outdoor_required": False,
        "estimated_duration_minutes": 15,
        "burden_level": 1,
        "career_tags": ["design", "media", "writing", "planning"],
        "recovery_tags": ["culture", "low_contact"],
        "source_name": "인천문화재단",
        "source_url": "https://www.ifac.or.kr/culturalInfo/cuturalEvents/performanceSrch/list.do?key=m2501152621396",
        "contact": "공식 페이지 확인",
    },
    {
        "resource_id": "resource_014",
        "resource_type": "contest",
        "name": "인천청년포털 청년정책검색",
        "description": "인천 청년정책을 분야별로 검색하는 공식 화면입니다. 공모전·지원사업·교육문화·일자리 정책을 비교할 때 사용합니다.",
        "district": "인천 전역",
        "address": "인천광역시 남동구 정각로 29",
        "latitude": 37.4563,
        "longitude": 126.7052,
        "start_date": "",
        "end_date": "",
        "cost_type": "free",
        "online_available": True,
        "social_contact_level": 0,
        "outdoor_required": False,
        "estimated_duration_minutes": 15,
        "burden_level": 1,
        "career_tags": ["public_policy", "planning", "data"],
        "recovery_tags": ["support", "low_contact"],
        "source_name": "인천청년포털",
        "source_url": "https://youth.incheon.go.kr/",
        "contact": "온라인 확인",
    },
    {
        "resource_id": "resource_015",
        "resource_type": "mini_project",
        "name": "문화공간 접근성 점검 미니 프로젝트",
        "description": "인천 공식 문화공간 정보를 바탕으로 첫 방문자가 확인해야 할 비용, 동선, 운영시간, 문의 방식을 1쪽 체크리스트로 정리하는 미니 프로젝트입니다.",
        "district": "인천 전역",
        "address": "인천 공식 문화공간",
        "latitude": 37.4563,
        "longitude": 126.7052,
        "start_date": "",
        "end_date": "",
        "cost_type": "free",
        "online_available": True,
        "social_contact_level": 0,
        "outdoor_required": False,
        "estimated_duration_minutes": 45,
        "burden_level": 2,
        "career_tags": ["design", "writing", "planning", "data"],
        "recovery_tags": ["culture", "low_contact"],
        "source_name": "RebootRoute curated from official source links",
        "source_url": "https://ifac.or.kr/index.do",
        "contact": "온라인 확인",
    },
]


def generate_resources(n: int | None = None, seed: int = 42) -> pd.DataFrame:
    del n, seed
    rows: list[dict[str, Any]] = []
    for item in REAL_RESOURCE_SEEDS:
        row = item.copy()
        row["career_tags"] = _json_list(list(row["career_tags"]))
        row["recovery_tags"] = _json_list(list(row["recovery_tags"]))
        row["updated_at"] = _now()
        rows.append(row)
    return pd.DataFrame(rows)


def generate_progress(profiles: pd.DataFrame, missions: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    mission_by_stage = {stage: group["mission_id"].tolist() for stage, group in missions.groupby("stage")}
    for _, profile in profiles.iterrows():
        readiness = (profile["energy_level"] + profile["daily_rhythm_level"] + (1 if profile["has_support_person"] else 0)) / 11
        max_stage = int(np.clip(round(readiness * 6 + rng.choice([-1, 0, 0, 1])), 0, 6))
        for stage in range(max_stage + 1):
            if rng.random() > 0.45:
                continue
            mission_id = rng.choice(mission_by_stage.get(stage, mission_by_stage[0]))
            status = rng.choices(["completed", "skipped", "too_hard", "started"], weights=[0.62, 0.12, 0.14, 0.12])[0]
            rows.append(
                {
                    "log_id": f"log_{len(rows):05d}",
                    "user_id": profile["user_id"],
                    "mission_id": mission_id,
                    "status": status,
                    "user_note": "샘플 진행 로그",
                    "completed_at": (SAMPLE_GENERATED_AT_DT - timedelta(days=rng.randint(0, 60))).isoformat() if status == "completed" else "",
                    "points_awarded": rng.randint(5, 25) if status == "completed" else 0,
                }
            )
    return pd.DataFrame(rows)


def generate_outcomes() -> pd.DataFrame:
    return pd.DataFrame(columns=OUTCOME_COLUMNS)


def save_mock_data(output_dir: Path | None = None, seed: int = 42) -> dict[str, Path]:
    cfg = load_config()
    ensure_directories(cfg)
    out_dir = output_dir or cfg.raw_data_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    profiles = generate_profiles(seed=seed)
    missions = generate_missions(seed=seed)
    resources = generate_resources(seed=seed)
    progress = generate_progress(profiles, missions, seed=seed)
    outcomes = generate_outcomes()
    paths = {
        "profiles": out_dir / "sample_profiles.csv",
        "missions": out_dir / "sample_missions.csv",
        "resources": out_dir / "sample_resources.csv",
        "progress": out_dir / "sample_progress.csv",
        "outcomes": out_dir / "sample_outcomes.csv",
    }
    _write_csv_atomic(profiles, paths["profiles"])
    _write_csv_atomic(missions, paths["missions"])
    _write_csv_atomic(resources, paths["resources"])
    _write_csv_atomic(progress, paths["progress"])
    _write_csv_atomic(outcomes, paths["outcomes"])
    return paths


def ensure_mock_data() -> dict[str, Path]:
    cfg = load_config()
    paths = {
        "profiles": cfg.raw_data_dir / "sample_profiles.csv",
        "missions": cfg.raw_data_dir / "sample_missions.csv",
        "resources": cfg.raw_data_dir / "sample_resources.csv",
        "progress": cfg.raw_data_dir / "sample_progress.csv",
        "outcomes": cfg.raw_data_dir / "sample_outcomes.csv",
    }
    if not all(path.exists() for path in paths.values()):
        return save_mock_data(cfg.raw_data_dir, cfg.random_seed)
    return paths


def load_raw_data() -> dict[str, pd.DataFrame]:
    paths = ensure_mock_data()
    return {name: pd.read_csv(path) for name, path in paths.items()}


def get_sample_profile() -> dict[str, Any]:
    paths = ensure_mock_data()
    df = pd.read_csv(paths["profiles"])
    sample = df.iloc[0].to_dict()
    sample["interests"] = json.loads(sample["interests"])
    return sample
