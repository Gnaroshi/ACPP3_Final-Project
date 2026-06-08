from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


YOUTH_BASE_URL = "https://youth.incheon.go.kr"
YOUTH_PROGRAM_URL = f"{YOUTH_BASE_URL}/program/programInfoList.do?prgmdiv=all"
YOUTH_POLICY_URL = f"{YOUTH_BASE_URL}/youthpolicy/youthPolicyInfoList.do?acptrun=ing"
IFAC_EVENT_URL = "https://www.ifac.or.kr/culturalInfo/cuturalEvents/performanceSrch/list.do?key=m2501152621396"
IFAC_OPEN_API_URL = "https://ifac.or.kr/openAPI/real/search.do"

YOUTH_RENTAL_INSTS = {
    "inuu": ("유유기지 인천", "미추홀구"),
    "junggu": ("중구 청년내일기지", "중구"),
    "donggu": ("동구청년21", "동구"),
    "yeonsu": ("연수청년자리", "연수구"),
    "namdong": ("남동구 청년꿈터", "남동구"),
    "bupyeong": ("유유기지 부평", "부평구"),
    "gyeyang": ("계양청년마당", "계양구"),
    "seogu": ("청년센터 서구1939", "서구"),
}

DISTRICT_CENTERS = {
    "중구": (37.4737, 126.6219),
    "동구": (37.4739, 126.6427),
    "미추홀구": (37.4636, 126.6504),
    "연수구": (37.4104, 126.6783),
    "남동구": (37.4473, 126.7314),
    "부평구": (37.5070, 126.7219),
    "계양구": (37.5374, 126.7378),
    "서구": (37.5454, 126.6759),
    "강화군": (37.7465, 126.4878),
    "옹진군": (37.4469, 126.6368),
    "인천시": (37.4563, 126.7052),
    "인천 전역": (37.4563, 126.7052),
}

RESOURCE_COLUMNS = [
    "resource_id",
    "resource_type",
    "name",
    "description",
    "district",
    "address",
    "latitude",
    "longitude",
    "start_date",
    "end_date",
    "cost_type",
    "online_available",
    "social_contact_level",
    "outdoor_required",
    "estimated_duration_minutes",
    "burden_level",
    "career_tags",
    "recovery_tags",
    "source_name",
    "source_url",
    "detail_url",
    "thumbnail_url",
    "contact",
    "official_title",
    "official_summary",
    "official_period",
    "official_place",
    "source_kind",
    "crawl_status",
    "source_checked_at",
    "derived_reason",
    "updated_at",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text.replace("\xa0", " ")


def parse_period(text: str) -> tuple[str, str]:
    cleaned = clean_text(text).replace("/", "-").replace(".", "-")
    matches = re.findall(r"(20\d{2})[-.](\d{1,2})[-.](\d{1,2})", cleaned)
    if not matches:
        return "", ""
    values = [f"{year}-{int(month):02d}-{int(day):02d}" for year, month, day in matches[:2]]
    if len(values) == 1:
        return values[0], values[0]
    return values[0], values[1]


def infer_district(*texts: str) -> str:
    joined = " ".join(clean_text(text) for text in texts)
    space_to_district = {
        "유유기지 인천": "미추홀구",
        "중구 청년내일기지": "중구",
        "동구청년21": "동구",
        "연수청년자리": "연수구",
        "남동구 청년꿈터": "남동구",
        "유유기지 부평": "부평구",
        "계양청년마당": "계양구",
        "청년센터 서구1939": "서구",
        "유유기지 강화": "강화군",
    }
    for space_name, district in space_to_district.items():
        if space_name in joined:
            return district
    if "인천시" in joined or "인천광역시" in joined:
        return "인천 전역"
    for district in sorted(DISTRICT_CENTERS, key=len, reverse=True):
        if district != "인천시" and district in joined:
            return district
    return "인천 전역"


def district_location(district: str) -> tuple[float, float]:
    return DISTRICT_CENTERS.get(district, DISTRICT_CENTERS["인천 전역"])


def stable_resource_id(prefix: str, *parts: str) -> str:
    raw = "|".join(clean_text(part) for part in parts if clean_text(part))
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"


def tags_from_text(text: str) -> tuple[list[str], list[str]]:
    lowered = text.lower()
    career: set[str] = set()
    recovery: set[str] = set()
    if any(token in text for token in ["취업", "직무", "자격증", "채용", "창업", "구직", "인턴"]):
        career.update(["career", "planning"])
    if any(token in text for token in ["문화", "전시", "공연", "예술", "체험", "여행", "로컬"]):
        career.update(["culture", "planning"])
        recovery.add("culture")
    if any(token in text for token in ["글", "후기", "콘텐츠", "홍보"]):
        career.add("writing")
    if any(token in text for token in ["디자인", "드로잉", "미디어", "콘텐츠"]):
        career.update(["design", "media"])
    if any(token in text for token in ["데이터", "AI", "SW", "소프트웨어", "it"]):
        career.update(["IT", "data"])
    if any(token in text for token in ["정책", "지원", "월세", "복지", "수당", "청년"]):
        career.add("public_policy")
        recovery.add("support")
    if any(token in text for token in ["고립", "은둔", "마음", "휴식", "상담", "커뮤니티"]):
        recovery.update(["low_contact", "routine"])
    if "공간" in text or "대관" in text:
        recovery.update(["youth_space", "low_contact"])
    if "온라인" in lowered:
        recovery.add("low_contact")
    if not career:
        career.add("planning")
    if not recovery:
        recovery.add("low_contact")
    return sorted(career), sorted(recovery)


def contact_level_from_text(text: str, default: int = 2) -> int:
    if any(token in text for token in ["온라인", "비대면", "검색", "확인"]):
        return 1
    if any(token in text for token in ["박람회", "모임", "커뮤니티", "강의", "교육", "상담"]):
        return 3
    if any(token in text for token in ["공연", "전시", "공간", "대관", "체험"]):
        return 2
    return default


def burden_from(resource_type: str, contact_level: int, outdoor_required: bool) -> int:
    base = {"support_program": 1, "youth_program": 2, "culture_event": 2, "culture_facility": 2}.get(resource_type, 2)
    if contact_level >= 3:
        base += 1
    if not outdoor_required:
        base -= 1
    return max(0, min(5, base))


def normalize_resource(row: dict[str, Any], *, checked_at: str) -> dict[str, Any]:
    district = clean_text(row.get("district")) or "인천 전역"
    lat, lon = district_location(district)
    text = " ".join(
        clean_text(row.get(key))
        for key in ["name", "description", "official_summary", "official_place", "district"]
    )
    career_tags, recovery_tags = tags_from_text(text)
    resource_type = clean_text(row.get("resource_type")) or "support_program"
    contact_level = int(row.get("social_contact_level", contact_level_from_text(text)))
    outdoor_required = bool(row.get("outdoor_required", resource_type in {"youth_program", "culture_event", "culture_facility"}))
    source_url = clean_text(row.get("source_url"))
    detail_url = clean_text(row.get("detail_url")) or source_url
    name = clean_text(row.get("name") or row.get("official_title"))
    start_date = clean_text(row.get("start_date"))
    end_date = clean_text(row.get("end_date"))
    period = clean_text(row.get("official_period")) or (" ~ ".join(part for part in [start_date, end_date] if part))
    normalized = {
        "resource_id": clean_text(row.get("resource_id")) or stable_resource_id(resource_type, name, detail_url or source_url),
        "resource_type": resource_type,
        "name": name,
        "description": clean_text(row.get("description") or row.get("official_summary")),
        "district": district,
        "address": clean_text(row.get("address") or row.get("official_place") or district),
        "latitude": float(row.get("latitude") or lat),
        "longitude": float(row.get("longitude") or lon),
        "start_date": start_date,
        "end_date": end_date,
        "cost_type": clean_text(row.get("cost_type")) or "unknown",
        "online_available": bool(row.get("online_available", True)),
        "social_contact_level": contact_level,
        "outdoor_required": outdoor_required,
        "estimated_duration_minutes": int(row.get("estimated_duration_minutes", 20)),
        "burden_level": int(row.get("burden_level", burden_from(resource_type, contact_level, outdoor_required))),
        "career_tags": row.get("career_tags") or career_tags,
        "recovery_tags": row.get("recovery_tags") or recovery_tags,
        "source_name": clean_text(row.get("source_name")) or "공식 출처",
        "source_url": source_url,
        "detail_url": detail_url,
        "thumbnail_url": clean_text(row.get("thumbnail_url")),
        "contact": clean_text(row.get("contact")) or "공식 페이지 확인",
        "official_title": clean_text(row.get("official_title")) or name,
        "official_summary": clean_text(row.get("official_summary")) or clean_text(row.get("description")),
        "official_period": period,
        "official_place": clean_text(row.get("official_place") or row.get("address") or district),
        "source_kind": clean_text(row.get("source_kind")) or "html_scrape",
        "crawl_status": clean_text(row.get("crawl_status")) or "ok",
        "source_checked_at": clean_text(row.get("source_checked_at")) or checked_at,
        "derived_reason": clean_text(row.get("derived_reason"))
        or "공식 출처의 제목·기간·장소·문의 정보를 기준으로 RebootRoute 부담도/태그를 파생했습니다.",
        "updated_at": clean_text(row.get("updated_at")) or checked_at,
    }
    return {column: normalized.get(column, "") for column in RESOURCE_COLUMNS}


def http_get(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 RebootRoute/1.0 (+https://github.com/Gnaroshi/ACPP3_Final-Project)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding
    return response.text


def _li_key_values(parent: BeautifulSoup, key_selector: str = "span") -> dict[str, str]:
    values: dict[str, str] = {}
    for item in parent.select("li"):
        key_tag = item.select_one(key_selector)
        if not key_tag:
            continue
        key = clean_text(key_tag.get_text(" ", strip=True)).replace(":", "").strip()
        raw = clean_text(item.get_text(" ", strip=True))
        value = raw
        if value.startswith(key):
            value = value[len(key) :]
        value = clean_text(value.lstrip(" :"))
        values[key] = value
    return values


def parse_youth_programs_html(html: str, *, source_url: str = YOUTH_PROGRAM_URL, checked_at: str | None = None) -> list[dict[str, Any]]:
    checked_at = checked_at or utc_now_iso()
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    for card in soup.select("ul.galleryList > li"):
        title_tag = card.select_one("p.tit a")
        if not title_tag:
            continue
        title = clean_text(title_tag.get_text(" ", strip=True))
        detail_url = urljoin(YOUTH_BASE_URL, title_tag.get("href", ""))
        img = card.select_one("p.img img")
        thumbnail_url = urljoin(YOUTH_BASE_URL, img.get("src", "")) if img and img.get("src") else ""
        status = clean_text(card.select_one("p.cate").get_text(" ", strip=True) if card.select_one("p.cate") else "")
        info = _li_key_values(card.select_one("ul.list_info") or BeautifulSoup("", "html.parser"))
        apply_period = info.get("신청기간", "")
        run_period = info.get("진행기간", "")
        start_date, end_date = parse_period(run_period or apply_period)
        location = clean_text(card.select_one(".cate-box .location").get_text(" ", strip=True) if card.select_one(".cate-box .location") else "")
        category = clean_text(card.select_one(".cate-box p:not(.location)").get_text(" ", strip=True) if card.select_one(".cate-box p:not(.location)") else "")
        district = infer_district(location, title)
        official_summary = " · ".join(part for part in [status, f"신청기간 {apply_period}", f"진행기간 {run_period}", location, category] if part)
        description = f"{title} 공식 프로그램입니다. {official_summary}"
        contact_level = contact_level_from_text(f"{title} {category} {location}", default=2)
        rows.append(
            normalize_resource(
                {
                    "resource_type": "youth_program",
                    "name": title,
                    "description": description,
                    "district": district,
                    "address": location or district,
                    "start_date": start_date,
                    "end_date": end_date,
                    "cost_type": "unknown",
                    "online_available": True,
                    "social_contact_level": contact_level,
                    "outdoor_required": True,
                    "estimated_duration_minutes": 30,
                    "source_name": "인천청년포털 프로그램",
                    "source_url": source_url,
                    "detail_url": detail_url,
                    "thumbnail_url": thumbnail_url,
                    "contact": "공식 페이지 확인",
                    "official_title": title,
                    "official_summary": official_summary,
                    "official_period": run_period or apply_period,
                    "official_place": location,
                    "source_kind": "html_scrape",
                    "crawl_status": "ok",
                    "source_checked_at": checked_at,
                },
                checked_at=checked_at,
            )
        )
    return rows


def parse_youth_policies_html(html: str, *, source_url: str = YOUTH_POLICY_URL, checked_at: str | None = None) -> list[dict[str, Any]]:
    checked_at = checked_at or utc_now_iso()
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    for card in soup.select("ul.boardList > li"):
        title = clean_text(card.select_one(".con-box .tit").get_text(" ", strip=True) if card.select_one(".con-box .tit") else "")
        if not title:
            continue
        district = infer_district(clean_text(card.select_one(".tag-box .local").get_text(" ", strip=True) if card.select_one(".tag-box .local") else ""))
        status = clean_text(card.select_one(".tag-box .tag").get_text(" ", strip=True) if card.select_one(".tag-box .tag") else "")
        values: dict[str, str] = {}
        for item in card.select(".con-box li"):
            key = clean_text(item.select_one("strong").get_text(" ", strip=True) if item.select_one("strong") else "").replace(":", "").strip()
            value = clean_text(item.select_one("span").get_text(" ", strip=True) if item.select_one("span") else "")
            if key:
                values[key] = value
        apply_period = values.get("신청", "")
        start_date, end_date = parse_period(apply_period)
        summary = values.get("내용", "")
        detail_tag = card.select_one(".btn-box a.btn")
        detail_url = urljoin(YOUTH_BASE_URL, detail_tag.get("href", "")) if detail_tag else source_url
        text = f"{title} {summary}"
        contact_level = contact_level_from_text(text, default=1)
        official_summary = " · ".join(part for part in [status, values.get("연령", ""), f"신청 {apply_period}", summary] if part)
        rows.append(
            normalize_resource(
                {
                    "resource_type": "support_program",
                    "name": title,
                    "description": summary or official_summary,
                    "district": district,
                    "address": district,
                    "start_date": start_date,
                    "end_date": end_date,
                    "cost_type": "free",
                    "online_available": True,
                    "social_contact_level": contact_level,
                    "outdoor_required": False,
                    "estimated_duration_minutes": 20,
                    "source_name": "인천청년포털 청년정책",
                    "source_url": source_url,
                    "detail_url": detail_url,
                    "thumbnail_url": "",
                    "contact": "공식 페이지 확인",
                    "official_title": title,
                    "official_summary": official_summary,
                    "official_period": apply_period,
                    "official_place": district,
                    "source_kind": "html_scrape",
                    "crawl_status": "ok",
                    "source_checked_at": checked_at,
                },
                checked_at=checked_at,
            )
        )
    return rows


def parse_youth_rentals_html(
    html: str,
    *,
    source_url: str,
    space_name: str,
    district: str,
    checked_at: str | None = None,
) -> list[dict[str, Any]]:
    checked_at = checked_at or utc_now_iso()
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    for card in soup.select(".rental_list li"):
        title_tag = card.select_one(".con .tit a")
        if not title_tag:
            continue
        title = clean_text(title_tag.get_text(" ", strip=True))
        detail_url = urljoin(YOUTH_BASE_URL, title_tag.get("href", ""))
        img = card.select_one("p.img img")
        thumbnail_url = urljoin(YOUTH_BASE_URL, img.get("src", "")) if img and img.get("src") else ""
        info = _li_key_values(card.select_one("ul.lec_info") or BeautifulSoup("", "html.parser"))
        hours = info.get("이용시간", "")
        contact = info.get("문  의  처", "") or info.get("문 의 처", "") or info.get("문의처", "")
        target = info.get("신청대상", "")
        method = info.get("신청방법", "")
        official_summary = " · ".join(part for part in [space_name, method, target, hours, contact] if part)
        rows.append(
            normalize_resource(
                {
                    "resource_type": "culture_facility",
                    "name": f"{space_name} {title}",
                    "description": f"{space_name}의 공식 공간대관 자원입니다. {official_summary}",
                    "district": district,
                    "address": space_name,
                    "cost_type": "unknown",
                    "online_available": True,
                    "social_contact_level": 2,
                    "outdoor_required": True,
                    "estimated_duration_minutes": 30,
                    "source_name": "인천청년포털 공간대관",
                    "source_url": source_url,
                    "detail_url": detail_url,
                    "thumbnail_url": thumbnail_url,
                    "contact": contact or "공식 페이지 확인",
                    "official_title": title,
                    "official_summary": official_summary,
                    "official_period": hours,
                    "official_place": space_name,
                    "source_kind": "html_scrape",
                    "crawl_status": "ok",
                    "source_checked_at": checked_at,
                },
                checked_at=checked_at,
            )
        )
    return rows


def parse_ifac_events_html(html: str, *, source_url: str = IFAC_EVENT_URL, checked_at: str | None = None) -> list[dict[str, Any]]:
    checked_at = checked_at or utc_now_iso()
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, Any]] = []
    for card in soup.select(".thumbBoardGroup a"):
        title = clean_text(card.select_one(".text .title").get_text(" ", strip=True) if card.select_one(".text .title") else "")
        if not title:
            continue
        status = clean_text(card.select_one(".img .tag").get_text(" ", strip=True) if card.select_one(".img .tag") else "")
        values = _li_key_values(card.select_one(".text ul.info") or BeautifulSoup("", "html.parser"), key_selector="b")
        host_place = values.get("주최", "")
        period = values.get("모임기간", "")
        start_date, end_date = parse_period(period)
        onclick = card.get("onclick", "")
        event_match = re.search(r"goView\('([^']+)'\)", onclick)
        detail_url = source_url
        if event_match:
            detail_url = f"https://www.ifac.or.kr/culturalInfo/cuturalEvents/performanceSrch/view.do?key=m2501152621396&eventSn={event_match.group(1)}"
        img = card.select_one("img")
        thumbnail_url = urljoin("https://www.ifac.or.kr", img.get("src", "")) if img and img.get("src") else ""
        district = infer_district(host_place, title)
        official_summary = " · ".join(part for part in [status, host_place, period] if part)
        rows.append(
            normalize_resource(
                {
                    "resource_type": "culture_event",
                    "name": title,
                    "description": f"{title} 문화행사입니다. {official_summary}",
                    "district": district,
                    "address": host_place or district,
                    "start_date": start_date,
                    "end_date": end_date,
                    "cost_type": "unknown",
                    "online_available": True,
                    "social_contact_level": contact_level_from_text(title, default=2),
                    "outdoor_required": True,
                    "estimated_duration_minutes": 40,
                    "source_name": "인천문화재단 문화행사",
                    "source_url": source_url,
                    "detail_url": detail_url,
                    "thumbnail_url": thumbnail_url,
                    "contact": "공식 페이지 확인",
                    "official_title": title,
                    "official_summary": official_summary,
                    "official_period": period,
                    "official_place": host_place,
                    "source_kind": "html_scrape",
                    "crawl_status": "ok",
                    "source_checked_at": checked_at,
                },
                checked_at=checked_at,
            )
        )
    return rows


def fetch_youth_program_resources() -> pd.DataFrame:
    checked_at = utc_now_iso()
    return pd.DataFrame(parse_youth_programs_html(http_get(YOUTH_PROGRAM_URL), checked_at=checked_at), columns=RESOURCE_COLUMNS)


def fetch_youth_policy_resources() -> pd.DataFrame:
    checked_at = utc_now_iso()
    return pd.DataFrame(parse_youth_policies_html(http_get(YOUTH_POLICY_URL), checked_at=checked_at), columns=RESOURCE_COLUMNS)


def fetch_youth_rental_resources() -> pd.DataFrame:
    checked_at = utc_now_iso()
    rows: list[dict[str, Any]] = []
    for inst, (space_name, district) in YOUTH_RENTAL_INSTS.items():
        url = f"{YOUTH_BASE_URL}/rental/rentalInfoList.do?inst_cd={inst}"
        rows.extend(parse_youth_rentals_html(http_get(url), source_url=url, space_name=space_name, district=district, checked_at=checked_at))
    return pd.DataFrame(rows, columns=RESOURCE_COLUMNS)


def fetch_ifac_event_resources() -> pd.DataFrame:
    checked_at = utc_now_iso()
    api_key = os.getenv("IFAC_OPEN_API_KEY") or os.getenv("INCHEON_CULTURE_API_KEY")
    if api_key:
        try:
            return fetch_ifac_event_resources_from_api(api_key, checked_at=checked_at)
        except Exception:
            pass
    return pd.DataFrame(parse_ifac_events_html(http_get(IFAC_EVENT_URL), checked_at=checked_at), columns=RESOURCE_COLUMNS)


def fetch_ifac_event_resources_from_api(api_key: str, *, checked_at: str | None = None) -> pd.DataFrame:
    checked_at = checked_at or utc_now_iso()
    response = requests.get(
        IFAC_OPEN_API_URL,
        params={"key": api_key},
        headers={"User-Agent": "Mozilla/5.0 RebootRoute/1.0"},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    items = payload.get("items") or payload.get("data") or payload.get("list") or []
    if isinstance(items, dict):
        items = items.get("item") or items.get("rows") or []
    rows: list[dict[str, Any]] = []
    for item in items:
        title = clean_text(item.get("title") or item.get("TITLE"))
        if not title:
            continue
        start_date, end_date = parse_period(" ".join(clean_text(item.get(key)) for key in ["sdate", "edate", "SDATE", "EDATE"]))
        place = clean_text(item.get("place") or item.get("PLACE"))
        summary = clean_text(item.get("description") or item.get("DESCRIPTION"))
        rows.append(
            normalize_resource(
                {
                    "resource_type": "culture_event",
                    "name": title,
                    "description": summary or f"{title} 문화행사입니다.",
                    "district": infer_district(place, title),
                    "address": place,
                    "start_date": start_date,
                    "end_date": end_date,
                    "cost_type": "unknown",
                    "online_available": True,
                    "social_contact_level": contact_level_from_text(title, default=2),
                    "outdoor_required": True,
                    "estimated_duration_minutes": 40,
                    "source_name": "인천문화재단 Open API",
                    "source_url": IFAC_OPEN_API_URL,
                    "detail_url": clean_text(item.get("link") or item.get("LINK")) or IFAC_EVENT_URL,
                    "thumbnail_url": clean_text(item.get("poster") or item.get("POSTER")),
                    "contact": clean_text(item.get("tel") or item.get("TEL")) or "공식 페이지 확인",
                    "official_title": title,
                    "official_summary": summary,
                    "official_period": " ~ ".join(part for part in [start_date, end_date] if part),
                    "official_place": place,
                    "source_kind": "open_api",
                    "crawl_status": "ok",
                    "source_checked_at": checked_at,
                },
                checked_at=checked_at,
            )
        )
    return pd.DataFrame(rows, columns=RESOURCE_COLUMNS)


def fetch_all_official_resources() -> pd.DataFrame:
    frames = [
        fetch_youth_policy_resources(),
        fetch_youth_program_resources(),
        fetch_youth_rental_resources(),
        fetch_ifac_event_resources(),
    ]
    combined = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True)
    if combined.empty:
        return pd.DataFrame(columns=RESOURCE_COLUMNS)
    combined = combined.drop_duplicates(subset=["resource_id"]).reset_index(drop=True)
    return combined[RESOURCE_COLUMNS]
