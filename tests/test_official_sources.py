from __future__ import annotations

import pandas as pd
import pytest

from rebootroute.data.official_sources import (
    RESOURCE_COLUMNS,
    parse_ifac_events_html,
    parse_youth_policies_html,
    parse_youth_programs_html,
    parse_youth_rentals_html,
)
from rebootroute.data.validation import validate_resources


def test_parse_youth_program_cards():
    html = """
    <ul class="galleryList">
      <li>
        <p class="cate"><span class="tag_state ir eng">접수중</span></p>
        <p class="img"><a href="/program/programInfoDetail.do?prgm_seq=1"><img src="/images/program/a.png" /></a></p>
        <div class="con">
          <p class="tit"><a href="/program/programInfoDetail.do?prgm_seq=1">마음 휴식: 예술로 채우다</a></p>
          <ul class="list_info">
            <li><span>신청기간</span>2026-06-08 ~ 2026-06-18</li>
            <li><span>진행기간</span>2026-06-22 ~ 2026-06-22</li>
          </ul>
          <div class="cate-box"><p class="location">연수청년자리</p><p>#문화예술</p></div>
        </div>
      </li>
    </ul>
    """
    rows = parse_youth_programs_html(html, checked_at="2026-06-08T00:00:00+00:00")
    assert len(rows) == 1
    assert rows[0]["name"] == "마음 휴식: 예술로 채우다"
    assert rows[0]["resource_type"] == "youth_program"
    assert rows[0]["district"] == "연수구"
    assert rows[0]["start_date"] == "2026-06-22"
    assert rows[0]["detail_url"].startswith("https://youth.incheon.go.kr/program/")
    assert rows[0]["thumbnail_url"].startswith("https://youth.incheon.go.kr/images/")


def test_parse_youth_policy_cards():
    html = """
    <ul class="boardList">
      <li>
        <div class="tag-box"><p class="local mc">미추홀구</p><p class="tag ing">접수중</p></div>
        <div class="con-box">
          <p class="tit">2026년 미추홀구 고립·은둔 청년 지원 프로그램</p>
          <ul>
            <li><strong>연령 :</strong><span>18세 ~ 39세</span></li>
            <li><strong>신청 :</strong><span>2026/04/14~2026/06/30</span></li>
            <li><strong>내용 :</strong><span>고립·은둔 청년에게 마음돌봄 프로그램을 제공합니다.</span></li>
          </ul>
        </div>
        <div class="btn-box"><a class="btn" href="/youthpolicy/youthPolicyInfoDetail.do?poly_seq=458">사업안내</a></div>
      </li>
    </ul>
    """
    rows = parse_youth_policies_html(html, checked_at="2026-06-08T00:00:00+00:00")
    assert len(rows) == 1
    assert rows[0]["resource_type"] == "support_program"
    assert rows[0]["district"] == "미추홀구"
    assert rows[0]["cost_type"] == "free"
    assert "고립·은둔" in rows[0]["official_summary"]


def test_parse_youth_rental_cards():
    html = """
    <div class="rental_list">
      <li>
        <p class="img"><img alt="1인 미디어방 사진" src="/images/rental/small/facility10.jpg" /></p>
        <div class="con">
          <p class="tit"><a href="/space/gyeyang/rental/rentalScheduleMonth.do?rental_seq=26">1인 미디어방</a></p>
          <ul class="lec_info">
            <li><span>신청방법</span>신청 후 승인</li>
            <li><span>신청대상</span>1~2명 (18~39세 청년)</li>
            <li><span>이용시간</span>(평일) 09~21시</li>
            <li><span>문  의  처</span>032-450-8356</li>
          </ul>
        </div>
      </li>
    </div>
    """
    rows = parse_youth_rentals_html(
        html,
        source_url="https://youth.incheon.go.kr/rental/rentalInfoList.do?inst_cd=gyeyang",
        space_name="계양청년마당",
        district="계양구",
        checked_at="2026-06-08T00:00:00+00:00",
    )
    assert len(rows) == 1
    assert rows[0]["resource_type"] == "culture_facility"
    assert rows[0]["name"] == "계양청년마당 1인 미디어방"
    assert rows[0]["contact"] == "032-450-8356"


def test_parse_ifac_event_cards():
    html = """
    <div class="thumbBoardGroup">
      <a href="#none" onclick="goView('13634');">
        <div class="img"><div class="tag"><span class="ongoing">진행중</span></div><img alt="전시" src="/common/image.do?key=224981" /></div>
        <div class="text">
          <p class="title">인천을 걷다</p>
          <ul class="info wMax75">
            <li><b>주최</b><span>인천광역시교육청평생학습관 갤러리다솜</span></li>
            <li><b>모임기간</b><span>2026.05.28 ~ 2026.06.10</span></li>
          </ul>
        </div>
      </a>
    </div>
    """
    rows = parse_ifac_events_html(html, checked_at="2026-06-08T00:00:00+00:00")
    assert len(rows) == 1
    assert rows[0]["resource_type"] == "culture_event"
    assert rows[0]["detail_url"].endswith("eventSn=13634")
    assert rows[0]["thumbnail_url"].startswith("https://www.ifac.or.kr/common/")


def test_resource_provenance_validation_rejects_fake_official_text():
    row = {column: "" for column in RESOURCE_COLUMNS}
    row.update(
        {
            "resource_id": "bad_001",
            "resource_type": "support_program",
            "name": "가짜 公式入口",
            "description": "공식처럼 보이는 잘못된 문구",
            "district": "인천 전역",
            "address": "인천",
            "cost_type": "free",
            "online_available": True,
            "social_contact_level": 1,
            "outdoor_required": False,
            "estimated_duration_minutes": 10,
            "burden_level": 1,
            "career_tags": "[]",
            "recovery_tags": "[]",
            "source_name": "인천청년포털",
            "source_url": "https://youth.incheon.go.kr/",
            "detail_url": "https://youth.incheon.go.kr/",
            "source_kind": "html_scrape",
            "crawl_status": "ok",
            "source_checked_at": "2026-06-08T00:00:00+00:00",
            "official_title": "가짜 公式入口",
            "official_summary": "잘못된 문구",
            "derived_reason": "test",
            "updated_at": "2026-06-08T00:00:00+00:00",
        }
    )
    with pytest.raises(ValueError, match="visible_text"):
        validate_resources(pd.DataFrame([row]))
