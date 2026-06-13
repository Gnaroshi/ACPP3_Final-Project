from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "capstone_requirements_check.md"


@dataclass(frozen=True)
class Requirement:
    area: str
    evidence: list[str]
    note: str


REQUIREMENTS = [
    Requirement(
        "문제 정의와 사용자 시나리오",
        ["README.md", "docs/capstone_project_brief.md"],
        "인천 청년정책/문화활동 탐색 부담을 낮추는 MVP로 범위를 고정했습니다.",
    ),
    Requirement(
        "입력/출력/성공 기준",
        ["README.md", "docs/capstone_project_brief.md", "evaluation/rubric.md"],
        "데모 입력, 추천 출력, human rubric, 모델 지표, 실행 검증 기준을 문서화했습니다.",
    ),
    Requirement(
        "데이터 소스와 접근 전략",
        ["data/raw/sample_resources.csv", "reports/data_card.md", "docs/data_version_strategy.md"],
        "공식 HTML 수집 resource와 synthetic MVP label의 경계를 분리했습니다.",
    ),
    Requirement(
        "Repo 기본 구조",
        ["data/raw", "data/processed", "notebooks", "src", "configs", "reports", "artifacts", "README.md"],
        "PDF 예시 구조를 추적 가능한 디렉터리와 실제 산출물로 맞췄습니다.",
    ),
    Requirement(
        "Baseline과 모델 학습",
        ["scripts/train_models.py", "reports/stage_metrics.json", "reports/mission_success_metrics.json", "docs/baseline_plan.md"],
        "Dummy baseline과 후보 모델을 같은 split에서 비교합니다.",
    ),
    Requirement(
        "Experiment tracking",
        ["src/rebootroute/modeling/mlflow_utils.py", "mlruns/.gitkeep", "data/mlflow.db"],
        "MLflow tracking URI를 SQLite로 설정하고 후보 모델 metric을 기록합니다.",
    ),
    Requirement(
        "Model card/data card",
        ["reports/model_card.md", "reports/data_card.md"],
        "학습 데이터, label 상태, 사용 금지 목적, 운영 전 조건을 명시했습니다.",
    ),
    Requirement(
        "오류분석과 해석 가능성",
        ["src/rebootroute/modeling/explain.py", "reports/error_analysis.md"],
        "Baseline 비교, confusion matrix, reliability, 취약 구간, 실패 조건을 리포트로 생성합니다.",
    ),
    Requirement(
        "Serving/API",
        ["src/rebootroute/api/main.py", "Dockerfile", "docker-compose.yml"],
        "FastAPI, Streamlit, Docker compose 실행 경로를 제공합니다.",
    ),
    Requirement(
        "Dashboard demo",
        ["src/rebootroute/dashboard/app.py", "README.md"],
        "Hero, 공식 자료 preview, 내 루트 조건 선택, 지도/결과 기록, ?operator=1 개발자 검증 흐름을 포함합니다.",
    ),
    Requirement(
        "Human evaluation",
        ["evaluation/human_eval_cases.csv", "evaluation/rubric.md", "reports/human_eval_review_sheet.csv"],
        "Cold-start 평가를 open-loop human rubric 방식으로 구성했습니다.",
    ),
    Requirement(
        "발표 산출물",
        ["docs/RebootRoute_Project_Report.docx", "docs/final_presentation_outline.md"],
        "DOCX 명세서와 최종 발표 outline을 제공합니다.",
    ),
    Requirement(
        "팀 역할과 운영 계획",
        ["docs/capstone_project_brief.md", "README.md"],
        "Data, modeling, serving/MLOps, presentation/docs 역할을 명시했습니다.",
    ),
]


def _exists(path: str) -> bool:
    return (ROOT / path).exists()


def _status(requirement: Requirement) -> str:
    return "충족" if all(_exists(path) for path in requirement.evidence) else "보강 필요"


def _evidence_list(paths: list[str]) -> str:
    return "<br>".join(f"`{path}`" for path in paths)


def build_report() -> str:
    rows = []
    missing: list[str] = []
    for requirement in REQUIREMENTS:
        status = _status(requirement)
        if status != "충족":
            missing.extend(path for path in requirement.evidence if not _exists(path))
        rows.append(
            "| "
            + " | ".join(
                [
                    requirement.area,
                    status,
                    _evidence_list(requirement.evidence),
                    requirement.note,
                ]
            )
            + " |"
        )

    table = "\n".join(
        [
            "| 요구사항 | 상태 | 근거 파일 | 비고 |",
            "| --- | --- | --- | --- |",
            *rows,
        ]
    )
    missing_block = "\n".join(f"- `{path}`" for path in sorted(set(missing))) if missing else "- 없음"
    return f"""# Capstone PDF 요구사항 체크

이 파일은 `week15 - capstone project workshop.pdf`의 Week 16 ML system 발표 요구사항을 RebootRoute repo 산출물에 매핑한 점검표입니다.

{table}

## 누락 항목
{missing_block}

## 최종 판단
누락 항목이 `없음`이면 PDF가 요구한 발표/구현/검증 산출물은 repo 안에서 확인 가능합니다. 단, 실제 사용자 데이터와 기관 outcome 데이터는 과제 환경에서 확보할 수 없으므로 synthetic MVP label과 공식 HTML 수집 resource의 경계를 README와 report에 명시했습니다.
"""


def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(build_report(), encoding="utf-8")
    print(REPORT)


if __name__ == "__main__":
    main()
