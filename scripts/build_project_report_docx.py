from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Iterable

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "RebootRoute_Project_Report.docx"
FONT = "Apple SD Gothic Neo"
ACCENT = RGBColor(15, 118, 110)
INK = RGBColor(23, 33, 29)
MUTED = RGBColor(89, 101, 96)
HEADER_FILL = "E8EEF5"
SOFT_FILL = "F6F8F5"


def set_run_font(run, size: float | None = None, bold: bool | None = None, color: RGBColor | None = None) -> None:
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:ascii"), FONT)
    run._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def set_paragraph_spacing(paragraph, before: int = 0, after: int = 6, line: float = 1.25) -> None:
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line


def add_paragraph(doc: Document, text: str = "", style: str | None = None, bold: bool = False) -> None:
    p = doc.add_paragraph(style=style)
    set_paragraph_spacing(p)
    if text:
        run = p.add_run(text)
        set_run_font(run, bold=bold, color=INK)


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    p = doc.add_paragraph(style=f"Heading {level}")
    set_paragraph_spacing(p, before=14 if level == 1 else 10, after=6)
    run = p.add_run(text)
    set_run_font(run, size=16 if level == 1 else 13 if level == 2 else 12, bold=True, color=ACCENT if level <= 2 else INK)


def add_bullets(doc: Document, items: Iterable[str]) -> None:
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Inches(0.38)
        p.paragraph_format.first_line_indent = Inches(-0.19)
        set_paragraph_spacing(p, after=4)
        run = p.add_run(item)
        set_run_font(run, color=INK)


def add_numbers(doc: Document, items: Iterable[str]) -> None:
    for item in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.left_indent = Inches(0.38)
        p.paragraph_format.first_line_indent = Inches(-0.19)
        set_paragraph_spacing(p, after=4)
        run = p.add_run(item)
        set_run_font(run, color=INK)


def shade_cell(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_width(cell, width_dxa: int) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(width_dxa))
    tc_w.set(qn("w:type"), "dxa")


def keep_row_together(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:cantSplit")) is None:
        tr_pr.append(OxmlElement("w:cantSplit"))


def repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:tblHeader")) is None:
        tr_pr.append(OxmlElement("w:tblHeader"))


def set_cell_text(cell, text: str, bold: bool = False, fill: str | None = None) -> None:
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    if fill:
        shade_cell(cell, fill)
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_paragraph_spacing(paragraph, after=0, line=1.15)
    paragraph.text = ""
    run = paragraph.add_run(text)
    set_run_font(run, size=9.2, bold=bold, color=INK)


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[int]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.style = "Table Grid"
    table.autofit = False
    repeat_table_header(table.rows[0])
    keep_row_together(table.rows[0])
    for idx, header in enumerate(headers):
        set_cell_width(table.rows[0].cells[idx], widths[idx])
        set_cell_text(table.rows[0].cells[idx], header, bold=True, fill=HEADER_FILL)
    for row in rows:
        table_row = table.add_row()
        keep_row_together(table_row)
        cells = table_row.cells
        for idx, value in enumerate(row):
            set_cell_width(cells[idx], widths[idx])
            set_cell_text(cells[idx], value)
    spacer = doc.add_paragraph()
    set_paragraph_spacing(spacer, after=4)


def add_callout(doc: Document, title: str, body: str, fill: str = SOFT_FILL) -> None:
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    cell = table.rows[0].cells[0]
    set_cell_width(cell, 9360)
    shade_cell(cell, fill)
    p = cell.paragraphs[0]
    set_paragraph_spacing(p, after=2, line=1.15)
    p.text = ""
    r = p.add_run(title)
    set_run_font(r, size=10.5, bold=True, color=ACCENT)
    p2 = cell.add_paragraph()
    set_paragraph_spacing(p2, after=0, line=1.15)
    r2 = p2.add_run(body)
    set_run_font(r2, size=9.8, color=INK)
    spacer = doc.add_paragraph()
    set_paragraph_spacing(spacer, after=4)


def configure_document(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = FONT
    normal._element.rPr.rFonts.set(qn("w:ascii"), FONT)
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.font.size = Pt(11)

    for style_name in ["Heading 1", "Heading 2", "Heading 3", "List Bullet", "List Number"]:
        style = styles[style_name]
        style.font.name = FONT
        style._element.rPr.rFonts.set(qn("w:ascii"), FONT)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
        style._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)


def read_metadata() -> dict:
    path = ROOT / "models" / "latest" / "metadata.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_doc() -> None:
    metadata = read_metadata()
    doc = Document()
    configure_document(doc)

    title = doc.add_paragraph()
    set_paragraph_spacing(title, after=3)
    run = title.add_run("RebootRoute 프로젝트 발표·구현 명세서")
    set_run_font(run, size=24, bold=True, color=INK)

    subtitle = doc.add_paragraph()
    set_paragraph_spacing(subtitle, after=12)
    run = subtitle.add_run("인천 청년정책·문화활동 RAG + 부담도 기반 미션 추천 MVP")
    set_run_font(run, size=13, color=ACCENT)

    add_callout(
        doc,
        "문서 목적",
        "이 문서는 발표자가 RebootRoute의 구현 범위, 코드 구조, 데이터 흐름, 대시보드 사용법, MLOps 산출물, 한계와 운영 전 교체 항목을 빠짐없이 설명할 수 있도록 정리한 프로젝트 명세서입니다.",
    )
    add_table(
        doc,
        ["항목", "내용"],
        [
            ["프로젝트명", "RebootRoute"],
            ["MVP 범위", "인천 청년정책/문화활동 RAG + 부담도 기반 단계형 미션 추천"],
            ["생성일", date.today().isoformat()],
            ["대상", "인천 거주 19-39세 고립·은둔 또는 고립 위험 청년, 가족·지인, 지역 청년지원기관/문화기관 운영자"],
            ["중요 경고", "진단, 치료, 상담 챗봇, 위험도 판정, 단순 취업 추천 앱이 아님"],
        ],
        [2100, 7260],
    )

    doc.add_page_break()

    add_heading(doc, "1. 프로젝트 정의", 1)
    add_paragraph(
        doc,
        "RebootRoute는 사용자의 상태 입력을 바탕으로 낮은 부담의 다음 행동을 추천하고, 인천 청년정책·문화활동 자원을 근거 자료와 함께 보여주는 MVP입니다. 추천의 핵심은 사용자를 취업이나 상담으로 바로 밀어 넣는 것이 아니라, 컨디션 정리, 비대면 준비, 동선 계획, 짧은 외출처럼 실제 결과가 남는 행동을 단계화하는 것입니다.",
    )
    add_bullets(
        doc,
        [
            "현재 핵심 축은 local TF-IDF 기반 RAG와 부담도 기반 mission recommendation입니다.",
            "서비스 문구는 진단/치료/상담이 아니라 정보 탐색과 낮은 부담 행동 제안으로 제한합니다.",
            "자해·타해·즉시 위험 표현이 들어오면 일반 추천을 중단하고 안전 자원 연결로 분기합니다.",
            "초기 데이터 루프는 closed-loop A/B가 아니라 open-loop logging, human rubric evaluation, batch retraining입니다.",
        ],
    )

    add_heading(doc, "2. 사용자 문제와 단계형 루트", 1)
    add_paragraph(
        doc,
        "고립 또는 고립 위험 상태의 청년은 상담, 직업훈련, 취업 프로그램으로 바로 이동하기 어려울 수 있습니다. RebootRoute는 그 이전 단계에서 컨디션 정리, 비대면 준비, 동선 계획, 짧은 외출, 저부담 참여, 관심 기반 기록, 작은 결과물 만들기를 누적하도록 설계되었습니다.",
    )
    add_table(
        doc,
        ["Stage", "의미", "대표 미션"],
        [
            ["0", "오늘 컨디션 정리", "오늘 가능한 시간대 고르기, 덜 부담스러운 조건 2개 고르기"],
            ["1", "비대면 준비", "문의 문장 초안 작성, 방문 전 체크리스트 만들기"],
            ["2", "동선 계획", "운영시간과 마감시간 정리, 가장 짧은 이동 동선 고르기"],
            ["3", "낮은 부담의 짧은 외출", "도서관 근처까지 가보기, 청년공간 주변 산책"],
            ["4", "저부담 참여", "무료 전시 20분 관람, 도서관 자료실 방문"],
            ["5", "관심 기반 기록", "전시 후기 5줄 작성, 프로그램 비교하기"],
            ["6", "작은 결과물 만들기", "지역 축제 카드뉴스 초안, 개선 제안 1쪽"],
            ["7", "지원 연결 준비", "직무훈련 상담 질문 정리, 상담 전 질문 준비"],
        ],
        [900, 2300, 6160],
    )

    doc.add_page_break()
    add_heading(doc, "3. 전체 아키텍처", 1)
    add_table(
        doc,
        ["순서", "구성 요소", "구현 위치", "역할"],
        [
            ["1", "Mock/Public 후보 데이터", "src/rebootroute/data/mock_data.py, data/raw/*.csv", "프로필, 미션, 자원, 진행 로그 샘플 생성"],
            ["2", "Data Validation", "src/rebootroute/data/validation.py", "필수 column, 타입, 범위 검증. pandera 미설치 시 fallback"],
            ["3", "Feature Build", "src/rebootroute/features/build_features.py", "부담도, readiness, progress, interest feature와 synthetic label 생성"],
            ["4", "RAG Resource Index", "src/rebootroute/rag/retriever.py", "TF-IDF 기반 인천 정책/문화 자원 검색"],
            ["5", "Safety Guardrail", "src/rebootroute/recommender/safety_guardrails.py", "위험 표현 감지 시 안전 자원 분기"],
            ["6", "Stage + Mission 추천", "src/rebootroute/recommender/*.py", "rule stage, mission ranking, resource ranking, mini project 생성"],
            ["7", "API / Dashboard", "src/rebootroute/api/main.py, src/rebootroute/dashboard/app.py", "FastAPI와 Streamlit 사용자/연구자 화면"],
            ["8", "Feedback Log", "src/rebootroute/database.py", "progress_logs, feedback_events, user_state 저장"],
            ["9", "Evaluation / Retraining", "evaluation/*.csv, scripts/build_human_eval_sheet.py, scripts/run_pipeline.py", "human eval sheet와 batch 학습 루프"],
        ],
        [760, 1720, 3320, 3560],
    )
    doc.add_page_break()

    add_heading(doc, "4. 코드 구조", 1)
    add_table(
        doc,
        ["경로", "내용"],
        [
            ["configs/config.yaml", "프로젝트명, 경로, 추천 top_n, safety resource path 설정"],
            ["configs/safety_resources.example.yaml", "위험 표현 분기 시 보여줄 도움 연결 자원"],
            ["src/rebootroute/schemas.py", "Pydantic schema: UserProfile, Mission, Resource, ProgressLog, FeedbackEvent, RAGSearchRequest"],
            ["src/rebootroute/database.py", "SQLite 연결, DB 초기화, progress/feedback 저장, reboot point 조회"],
            ["src/rebootroute/api/main.py", "FastAPI endpoint 정의"],
            ["src/rebootroute/dashboard/app.py", "Streamlit 대시보드. 사용자 데모와 운영자·연구자 뷰 분리"],
            ["src/rebootroute/data/*.py", "mock data 생성, fetch adapter stub, validation"],
            ["src/rebootroute/features/build_features.py", "feature table과 synthetic label 생성"],
            ["src/rebootroute/modeling/*.py", "모델 학습, 평가, registry, prediction, explanation"],
            ["src/rebootroute/rag/retriever.py", "TF-IDF local retrieval"],
            ["src/rebootroute/recommender/*.py", "stage rule, mission/resource ranking, route builder, safety, mini project"],
            ["scripts/*.py", "pipeline, sample data, DB init, model training, human eval sheet 생성"],
            ["tests/*.py", "validation, stage rules, recommender, RAG, feedback, safety, API smoke test"],
        ],
        [3500, 5860],
    )
    doc.add_page_break()

    add_heading(doc, "5. 데이터와 저장소 산출물", 1)
    add_table(
        doc,
        ["파일/테이블", "내용", "주의"],
        [
            ["data/raw/sample_profiles.csv", "180개 synthetic profile", "실제 사용자가 아님"],
            ["data/raw/sample_missions.csv", "Stage 0-7 미션 42개", "발표용 seed data"],
            ["data/raw/sample_resources.csv", "청년/문화/지원/공모전/미니프로젝트 자원 80개", "mock_incheon_public_data source"],
            ["data/raw/sample_progress.csv", "synthetic 진행 로그", "실제 완료 이력이 아님"],
            ["data/features/training_features.csv", "학습 feature + synthetic labels", "production 전 교체 필요"],
            ["data/rebootroute.db", "SQLite DB", "feedback_events, progress_logs, user_state"],
            ["models/latest/*.joblib", "stage / mission success model", "MLOps 시연용"],
            ["models/latest/metadata.json", "모델명, metric, data_version, warning", "dashboard MLOps 탭에서 사용"],
            ["reports/data_card.md", "데이터 설명과 synthetic label 경고", "발표/검토 산출물"],
            ["reports/model_card.md", "모델 후보, 선택 모델, metric, 한계", "발표/검토 산출물"],
            ["reports/human_eval_review_sheet.csv", "40개 human eval case 결과 sheet", "사람이 빈 score column을 채점"],
        ],
        [2650, 4210, 2500],
    )

    add_heading(doc, "6. 추천 구현 상세", 1)
    add_heading(doc, "6.1 Rule 기반 stage 분류", 2)
    add_paragraph(
        doc,
        "stage_rules.py는 외출 부담, 대면 부담, 에너지, 생활 리듬, 취업 부담, 지원자 존재 여부, 과거 진행 로그를 사용해 Stage 0-7을 정합니다. 추천의 1차 기준은 이 rule입니다. ML stage model은 보조 stage와 contributing factor 설명용입니다.",
    )
    add_heading(doc, "6.2 Mission ranking", 2)
    add_bullets(
        doc,
        [
            "stage_match: 추천 stage와 미션 stage가 가까울수록 높은 점수",
            "burden_fit: 사용자의 에너지/생활 리듬과 외출/대면 부담을 고려",
            "interest_fit: 관심 태그와 career/recovery tag overlap",
            "resource_available: 연결 가능한 자원이 있을 때 보정",
            "progress_continuity: 너무 어려움 기록이 있으면 보수적으로 조정",
            "novelty: 완료/건너뜀/너무 어려움 이력을 반영",
            "cost_fit: 현재 mission에는 직접 비용이 없으므로 budget readiness signal로 사용",
        ],
    )
    add_heading(doc, "6.3 Resource ranking", 2)
    add_bullets(
        doc,
        [
            "district_match: 사용자 구/군과 자원 구/군 일치",
            "burden_fit: outdoor/social 부담과 사용자 capacity 비교",
            "interest_fit: 관심 태그와 resource tag overlap",
            "contact_mode_fit: 온라인/낮은 대면/소규모/대면 가능 선호 반영",
            "cost_fit: 무료/저비용/유료와 budget limit 비교",
            "career_fit: 직무탐색 단계 이상에서 career tag를 추가 반영",
        ],
    )

    add_heading(doc, "7. RAG 구현 상세", 1)
    add_paragraph(
        doc,
        "retriever.py는 sample_resources.csv를 읽어 resource name, description, district, type, cost, career/recovery tag를 하나의 text로 묶고, scikit-learn TfidfVectorizer로 query와 resource 간 cosine similarity를 계산합니다. analyzer는 char_wb, ngram_range는 2-4입니다. sklearn이 없으면 query token overlap fallback을 사용합니다.",
    )
    add_bullets(
        doc,
        [
            "기본 검색 대상은 youth_program, culture_event, culture_facility, support_program입니다.",
            "district가 주어지면 같은 구/군 자원을 앞쪽에 재정렬합니다.",
            "max_burden_level이 있으면 해당 부담도 이하만 남깁니다.",
            "반환 answer에는 진단/치료가 아니라 정보 탐색 참고 자료라는 안전 문구를 포함합니다.",
            "사용자 화면에서는 자원명, 구/군, 비용, 부담도만 보여주고 score/id/source key는 숨깁니다.",
        ],
    )

    add_heading(doc, "8. Safety guardrail", 1)
    add_paragraph(
        doc,
        "safety_guardrails.py는 자해, 타해, 즉시 위험 표현을 regex로 감지합니다. 감지되면 route_builder.analyze_profile은 recommended_stage 0, safety_flag True, risk_type urgent_support_needed를 반환하고 next_3_missions와 recommended_resources를 빈 배열로 둡니다.",
    )
    add_table(
        doc,
        ["항목", "구현"],
        [
            ["감지 예", "죽고 싶, 자살, 극단적 선택, 사라지고 싶, 해치고 싶, kill myself, hurt someone 등"],
            ["분기 결과", "일반 미션 추천 중단, 안전 확인 메시지, safety resources 반환"],
            ["설정 파일", "configs/safety_resources.example.yaml"],
            ["테스트", "tests/test_safety_guardrails.py"],
        ],
        [2200, 7160],
    )

    add_heading(doc, "9. Feedback loop", 1)
    add_paragraph(
        doc,
        "현재 데이터 루프는 사용자 상태 입력 → safety guardrail → stage 분류 → RAG/mission/resource 추천 → feedback/progress log → human evaluation → batch retraining입니다. 초기에는 실제 사용자 데이터가 없으므로 closed-loop A/B test를 하지 않습니다.",
    )
    add_table(
        doc,
        ["테이블", "주요 필드", "역할"],
        [
            ["progress_logs", "log_id, user_id, mission_id, status, completed_at, points_awarded, payload_json", "미션 시작/완료/건너뜀/너무 어려움 진행 로그"],
            ["feedback_events", "event_id, user_id, event_type, mission_id, resource_id, rating, user_note, policy_version", "추천 반응과 운영자 review event 저장"],
            ["user_state", "user_id, reboot_points, last_stage, updated_at", "사용자별 내부 상태 저장. point는 연구/운영용이며 사용자 화면에는 노출하지 않음"],
        ],
        [1700, 4700, 2960],
    )

    doc.add_page_break()
    add_heading(doc, "10. Dashboard 재설계 내용", 1)
    add_table(
        doc,
        ["탭", "보여주는 대상", "내용"],
        [
            ["사용자 데모", "실제 사용자", "상태 입력과 추천 결과를 한 화면에 표시. 미션 ID, score, Stage 번호, point 숨김. 시작/완료/나중에/너무 어려움 action 제공"],
            ["정책/문화 찾기", "실제 사용자", "RAG 검색 결과를 자원 정보 중심으로 표시. source key, resource id, rag score 숨김"],
            ["운영자·연구자 뷰", "발표자/연구자/운영자", "Rule stage, ML 보조 stage, contributing factors, IDs, score, raw payload, feedback/progress log 확인"],
            ["MLOps·평가", "발표자/연구자", "모델 metric, data version, model/data card, human eval sheet, synthetic label warning 확인"],
        ],
        [1700, 1900, 5760],
    )
    add_bullets(
        doc,
        [
            "입력 widget 값은 session state에 저장되고, profile signature가 바뀌면 analyze_profile을 자동 재계산합니다.",
            "기존처럼 intake demo에서 submit한 뒤 별도 추천 루트 탭을 눌러야 확인하는 구조를 제거했습니다.",
            "demo_user_id를 session state에 고정해 feedback/progress log가 같은 데모 사용자에 누적됩니다.",
            "사용자 화면에는 내부 ranking score, 식별자, Stage 번호, point를 숨기고, 연구자 탭에서만 표로 공개합니다.",
        ],
    )
    doc.add_page_break()

    add_heading(doc, "11. API 구현", 1)
    add_table(
        doc,
        ["Endpoint", "Method", "역할"],
        [
            ["/health", "GET", "서비스 상태"],
            ["/metadata", "GET", "모델 metadata 반환"],
            ["/sample_profile", "GET", "샘플 profile 반환"],
            ["/analyze_intake", "POST", "intake 분석, safety, stage, top missions/resources 반환"],
            ["/recommend_route", "POST", "현재 stage부터 최대 3개 stage route 반환"],
            ["/recommend_missions", "POST", "미션 ranking 반환"],
            ["/recommend_resources", "POST", "자원 ranking 반환"],
            ["/rag/search", "POST", "정책/문화 RAG 검색"],
            ["/feedback/log", "POST", "feedback event 저장"],
            ["/progress/log", "POST", "progress log 저장 및 point 갱신"],
            ["/simulate", "POST", "field 변화 시 stage 변화 simulation"],
        ],
        [2500, 1100, 5760],
    )

    add_heading(doc, "12. MLOps와 평가", 1)
    stage_model = metadata.get("stage_model_name", "unknown")
    mission_model = metadata.get("mission_success_model_name", "unknown")
    stage_acc = metadata.get("stage_metrics", {}).get("accuracy")
    stage_f1 = metadata.get("stage_metrics", {}).get("macro_f1")
    mission_acc = metadata.get("mission_success_metrics", {}).get("accuracy")
    mission_f1 = metadata.get("mission_success_metrics", {}).get("macro_f1")
    mission_auc = metadata.get("mission_success_metrics", {}).get("roc_auc")
    add_table(
        doc,
        ["항목", "현재 값"],
        [
            ["Stage 선택 모델", str(stage_model)],
            ["Mission success 선택 모델", str(mission_model)],
            ["Data version", str(metadata.get("data_version", "unknown"))],
            ["Stage accuracy / macro F1", f"{stage_acc} / {stage_f1}"],
            ["Mission accuracy / macro F1 / ROC-AUC", f"{mission_acc} / {mission_f1} / {mission_auc}"],
            ["MLflow tracking", "data/mlflow.db SQLite backend, 실패 시 mlruns/fallback_runs.jsonl"],
            ["Human eval cases", "evaluation/human_eval_cases.csv 40개"],
            ["Rubric", "stage_score, mission_burden_score, rag_grounding_score, safety_score"],
        ],
        [3200, 6160],
    )
    add_callout(
        doc,
        "Synthetic label warning",
        "현재 label은 실제 참여 결과가 아니라 MVP 시연용 synthetic label입니다. 운영 환경에서는 real program participation, mission completion, support outcome, operator review, user feedback 데이터로 반드시 교체해야 합니다.",
        fill="FFF3D8",
    )

    add_heading(doc, "13. 실행 및 검증 명령", 1)
    add_table(
        doc,
        ["명령", "설명"],
        [
            ["make setup", "requirements.txt 의존성 설치"],
            ["make pipeline", "mock data 생성, validation, feature build, model training, DB init, reports 생성"],
            ["make dashboard", "Streamlit dashboard 실행. 기본 http://localhost:8501, 포트 사용 중이면 터미널 Local URL 사용"],
            ["make api", "FastAPI 실행, http://localhost:8000/docs"],
            ["make test", "pytest 실행"],
            ["make eval-sheet", "reports/human_eval_review_sheet.csv 생성"],
            ["make docker-up", "docker compose up --build"],
        ],
        [2600, 6760],
    )

    add_heading(doc, "14. 발표 데모 시나리오", 1)
    add_numbers(
        doc,
        [
            "make dashboard로 Streamlit을 실행한다.",
            "사용자 데모 탭에서 기본 profile을 보여주고 시작점과 오늘의 미션을 설명한다.",
            "외출 부담, 대면 부담, 에너지, 생활 리듬 값을 바꿔 추천이 즉시 바뀌는 것을 보여준다.",
            "미션의 시작/완료/너무 어려움 버튼을 눌러 feedback/progress log가 남는 것을 보여준다.",
            "정책/문화 찾기 탭에서 인천 자원을 검색하고 근거 자료가 표시되는 것을 보여준다.",
            "운영자·연구자 뷰에서 mission_id, resource_id, score, raw payload, feedback log를 확인한다.",
            "MLOps·평가 탭에서 data version, 모델 metric, human eval sheet, synthetic label warning을 설명한다.",
            "안전 분기 입력을 넣으면 일반 미션 추천이 중단되고 도움 연결 자원이 표시되는 것을 짧게 확인한다.",
        ],
    )

    add_heading(doc, "15. 운영 전 교체·보완 항목", 1)
    add_table(
        doc,
        ["항목", "현재 상태", "운영 전 필요한 작업"],
        [
            ["공공데이터", "mock/public 후보", "실제 인천 청년정책, 문화행사, 문화시설, 청년공간 데이터 연동"],
            ["Outcome label", "synthetic label", "실제 미션 완료, too-hard, 참여, 제출, 운영자 review label로 교체"],
            ["Safety resource", "example YAML", "기관 검토 후 지역/전국 위기 대응 연락처 확정"],
            ["개인정보", "MVP 미구현", "동의, 보존 기간, 삭제 요청, 접근 권한 설계"],
            ["운영자 workflow", "debug view 중심", "review queue, escalation protocol, audit log 설계"],
            ["Gemini/LLM", "필수 아님", "query expansion, grounded answer generation, operator assistant로 제한적 연결"],
            ["편향 점검", "기초 metric만 있음", "구/군, 접근성, 비용, 대면 부담별 성능 및 안전성 검토"],
        ],
        [2000, 2500, 4860],
    )

    add_heading(doc, "16. Known limitations", 1)
    add_bullets(
        doc,
        [
            "현재 데이터와 label은 MVP 시연용 synthetic/mock data입니다.",
            "거리 계산은 실제 이동거리가 아니라 구/군 일치 proxy에 가깝습니다.",
            "ML 모델은 임상 위험 모델이 아니며 그렇게 해석하면 안 됩니다.",
            "RAG는 TF-IDF retrieval이므로 생성형 답변 품질이나 semantic matching에는 한계가 있습니다.",
            "실제 배포 전 개인정보, 운영자 권한, 기관 연계, 안전 escalation protocol을 별도로 설계해야 합니다.",
            "추천 정책을 무작위로 흔드는 A/B test는 충분한 안전 데이터와 운영자 검토 체계가 생긴 뒤 제한적으로만 고려해야 합니다.",
        ],
    )

    add_heading(doc, "17. 파일별 검증 상태", 1)
    add_table(
        doc,
        ["검증", "현재 결과"],
        [
            ["make test", "9 passed"],
            ["make eval-sheet", "reports/human_eval_review_sheet.csv 생성 성공"],
            ["make pipeline", "성공. metadata, model card, data card 갱신"],
            ["Dashboard QA", "사용자/연구자 분리, 입력 즉시 반영, ID/score 숨김, feedback/progress 저장 구조로 수정"],
        ],
        [2500, 6860],
    )

    add_paragraph(
        doc,
        "Required original notice: These labels are synthetic MVP labels and must be replaced with real program participation / mission completion / support outcome data before production use.",
        bold=True,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build_doc()
