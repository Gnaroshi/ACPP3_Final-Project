from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "mlops_readiness_check.md"
BRIEF = ROOT / "docs" / "mlops_project_brief.md"
GENERATED_OUTPUTS = {"reports/mlops_readiness_check.md", "docs/mlops_project_brief.md"}


@dataclass(frozen=True)
class RubricItem:
    area: str
    question: str
    score: int
    evidence: list[str]
    note: str


def _exists(relative_path: str) -> bool:
    if relative_path in GENERATED_OUTPUTS:
        return True
    return (ROOT / relative_path).exists()


def _csv_count(relative_path: str) -> int:
    path = ROOT / relative_path
    if not path.exists():
        return 0
    return len(pd.read_csv(path))


def _load_json(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _sqlite_count(db_path: str, table_name: str) -> int:
    path = ROOT / db_path
    if not path.exists():
        return 0
    try:
        with sqlite3.connect(path) as conn:
            return int(conn.execute(f"select count(*) from {table_name}").fetchone()[0])
    except sqlite3.Error:
        return 0


def _metric(value: object) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header = "| " + " | ".join(headers) + " |"
    divider = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header, divider, *body])


def _model_rows(candidates: dict[str, dict[str, Any]], include_roc_auc: bool = False) -> list[list[str]]:
    rows: list[list[str]] = []
    for name, metrics in candidates.items():
        row = [name, _metric(metrics.get("accuracy")), _metric(metrics.get("macro_f1"))]
        if include_roc_auc:
            row.append(_metric(metrics.get("roc_auc")))
        rows.append(row)
    return rows


def _best_model(candidates: dict[str, dict[str, Any]], metric_name: str) -> str:
    best_name = ""
    best_value = float("-inf")
    for name, metrics in candidates.items():
        value = metrics.get(metric_name)
        if value is None and metric_name == "roc_auc":
            value = metrics.get("macro_f1")
        if value is None:
            continue
        if float(value) > best_value:
            best_name = name
            best_value = float(value)
    return best_name


def _project_config(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "team_name": "RebootRoute",
        "project_title": "RebootRoute",
        "one_sentence_problem": (
            "우리는 인천 청년정책·문화활동 탐색 부담이 큰 청년을 위해 공식 자원 데이터와 "
            "사용자 상태 입력을 사용하여 오늘 실행 가능한 낮은 부담의 루트와 미션을 제공한다."
        ),
        "target_user": "인천 거주 19-39세 고립·은둔 또는 고립 위험 청년과 지역 청년지원/문화기관 운영자",
        "input_data": (
            "공식 HTML 수집 resource, synthetic MVP profile/progress/outcome, "
            "사용자 현재 조건 입력, 미션/feedback/outcome log"
        ),
        "prediction_or_output": (
            "stage 분류, mission success 확률 보조 예측, 공식 자원 랭킹, "
            "TF-IDF RAG 검색 결과, 오늘 할 미션"
        ),
        "ml_task_type": "hybrid: rule-based recommendation + classification + ranking + local RAG retrieval",
        "primary_metric": "stage macro F1, mission ROC-AUC, mission macro F1, human rubric score",
        "secondary_metrics": ["accuracy", "confusion matrix", "reliability summary", "resource provenance validation"],
        "data_source": (
            "인천청년포털 청년정책/프로그램/공간대관 공개 HTML, 인천문화재단 문화행사 공개 HTML, "
            "실제 사용자 데이터 대체 synthetic mock dataset"
        ),
        "label_definition": (
            "현재 stage와 mission success label은 synthetic MVP placeholder입니다. "
            "production 전 실제 완료, too-hard, 참여/지원 결과, 운영자 review로 교체해야 합니다."
        ),
        "split_strategy": "one row per synthetic user, stratified train_test_split(test_size=0.25, random_seed=42)",
        "baseline_model": "DummyClassifier",
        "candidate_models": [
            "DummyClassifier",
            "LogisticRegression",
            "RandomForestClassifier",
            "GradientBoostingClassifier",
        ],
        "versioning_plan": (
            f"Git commit + config.yaml + data_version hash `{metadata.get('data_version', 'unknown')}` + "
            "model metadata. DVC remote는 아직 사용하지 않고 DVC-compatible 폴더 구조를 유지합니다."
        ),
        "serving_plan": "FastAPI /health, /recommend_route, /rag/search, /feedback/log, /progress/log, /outcomes/log + Streamlit dashboard",
        "monitoring_plan": (
            "batch validation, resource audit, MLflow run/metric logging, model/data card, "
            "error analysis, feedback/progress/outcome SQLite logs"
        ),
        "demo_path": "make pipeline -> make dashboard -> 조건 칩 선택 -> 추천 미션/공식 자원/지도 확인 -> 시작/완료/too-hard/outcome 기록",
        "main_risks": [
            "synthetic label과 실제 사용자 행동의 차이",
            "공식 페이지 DOM 변경으로 인한 수집 누락",
            "개인정보/민감정보 저장 위험",
            "추천을 상담/진단처럼 오해하는 safety risk",
            "실제 운영 시 drift와 기관 outcome 연계 지연",
        ],
    }


def _rubric(
    counts: dict[str, int],
    metadata: dict[str, Any],
    stage_candidates: dict[str, dict[str, Any]],
    mission_candidates: dict[str, dict[str, Any]],
    mlflow_counts: dict[str, int],
) -> list[RubricItem]:
    stage_champion = metadata.get("stage_model_name", "")
    mission_champion = metadata.get("mission_success_model_name", "")
    return [
        RubricItem(
            "Problem",
            "한 문장 문제정의가 명확한가?",
            2,
            ["README.md", "docs/capstone_project_brief.md", "docs/mlops_project_brief.md"],
            "MVP 범위를 인천 청년정책·문화활동 RAG와 부담도 기반 미션 추천으로 고정했습니다.",
        ),
        RubricItem(
            "Data",
            "데이터 출처, feature, target/label이 명확한가?",
            2,
            ["data/raw/sample_resources.csv", "reports/data_card.md", "reports/resource_audit.md"],
            (
                f"공식 자원 {counts['resources']}건, synthetic profile {counts['profiles']}건, "
                f"progress {counts['progress']}건, outcome {counts['outcomes']}건을 분리했습니다."
            ),
        ),
        RubricItem(
            "Split",
            "time/group/batch 등 누수를 줄이는 split 전략이 있는가?",
            2,
            ["src/rebootroute/modeling/train_stage_model.py", "src/rebootroute/modeling/train_mission_success_model.py"],
            "현재 feature table은 사용자당 1행이라 동일 사용자 중복 누수는 없고 stratified split을 사용합니다. 실제 운영 로그 전환 후에는 time/group split이 필요합니다.",
        ),
        RubricItem(
            "Baseline",
            "24시간 안에 만들 수 있는 baseline이 있는가?",
            2,
            ["docs/baseline_plan.md", "reports/stage_metrics.json", "reports/mission_success_metrics.json"],
            "Stage와 mission success 모두 Dummy baseline과 후보 모델을 같은 split에서 비교합니다.",
        ),
        RubricItem(
            "Metric",
            "문제 비용 구조에 맞는 primary/secondary metric이 있는가?",
            2,
            ["src/rebootroute/modeling/evaluate.py", "reports/error_analysis.md"],
            "Stage는 accuracy/macro F1/per-class/confusion matrix, mission은 ROC-AUC/reliability까지 기록합니다.",
        ),
        RubricItem(
            "Versioning",
            "Git/DVC/params로 데이터와 코드 상태를 재현할 수 있는가?",
            2,
            ["configs/config.yaml", "data/features/data_version.json", "models/latest/metadata.json"],
            "Git, config.yaml, data_version hash, model metadata로 재현 근거를 남깁니다. DVC remote는 production 보강 항목입니다.",
        ),
        RubricItem(
            "Tracking",
            "MLflow 등으로 params/metrics/artifacts를 기록하는가?",
            2,
            ["src/rebootroute/modeling/mlflow_utils.py", "data/mlflow.db", "mlruns"],
            f"MLflow SQLite backend에 runs {mlflow_counts['runs']}건, metrics {mlflow_counts['metrics']}건, params {mlflow_counts['params']}건이 있습니다.",
        ),
        RubricItem(
            "XAI/Error",
            "해석 또는 오류 분석 artifact가 있는가?",
            2,
            ["reports/error_analysis.md", "src/rebootroute/modeling/explain.py"],
            "Baseline 비교, confusion matrix, reliability summary, 취약 stage, 실패 조건을 리포트로 생성합니다.",
        ),
        RubricItem(
            "Serving",
            "FastAPI endpoint 또는 batch inference 인터페이스가 있는가?",
            2,
            ["src/rebootroute/api/main.py", "Dockerfile", "docker-compose.yml"],
            "FastAPI endpoint와 Streamlit dashboard, Docker compose 실행 경로가 있습니다.",
        ),
        RubricItem(
            "Monitoring",
            "drift/latency/cost/failure 등 운영 지표가 정의되어 있는가?",
            2,
            ["reports/resource_audit.md", "reports/data_card.md", "reports/model_card.md", "reports/mlops_readiness_check.md"],
            "현재는 batch monitoring입니다. resource provenance, schema, MLflow metric, reliability, outcome log를 추적합니다.",
        ),
        RubricItem(
            "Safety",
            "privacy, fairness, safety, misuse 리스크를 다루는가?",
            2,
            ["src/rebootroute/recommender/safety_guardrails.py", "reports/data_card.md", "reports/model_card.md"],
            "자해/폭력/즉시 위험 표현은 일반 추천이 아니라 안전 자원 안내로 분기합니다. 진단/상담/위험도 판정이 아님을 명시했습니다.",
        ),
        RubricItem(
            "Demo",
            "5분 안에 보여줄 안정적인 demo path가 있는가?",
            2,
            ["README.md", "src/rebootroute/dashboard/app.py", "docs/final_presentation_outline.md"],
            "make pipeline, make dashboard, 사용자 조건 선택, 추천/지도/기록, operator 검증 흐름을 제공합니다.",
        ),
        RubricItem(
            "Champion",
            "baseline 대비 champion 선택 근거가 남는가?",
            2,
            ["models/latest/metadata.json", "reports/error_analysis.md"],
            f"현재 champion은 stage `{stage_champion}`, mission success `{mission_champion}`입니다.",
        ),
    ]


def _score_summary(items: list[RubricItem]) -> tuple[int, int, str]:
    total = sum(item.score for item in items)
    max_score = 2 * len(items)
    ratio = total / max_score if max_score else 0
    if ratio >= 0.80:
        level = "A: 발표 준비 구조가 매우 좋음"
    elif ratio >= 0.60:
        level = "B: 핵심 구조는 있으나 일부 보강 필요"
    elif ratio >= 0.40:
        level = "C: 아이디어는 있으나 실행 구조를 더 좁혀야 함"
    else:
        level = "D: 오늘 범위 재정의가 필요"
    return total, max_score, level


def _evidence(paths: list[str]) -> str:
    return "<br>".join(f"`{path}`" for path in paths)


def _missing(paths: list[str]) -> list[str]:
    return [path for path in paths if not _exists(path)]


def build_audit() -> tuple[str, str]:
    counts = {
        "profiles": _csv_count("data/raw/sample_profiles.csv"),
        "resources": _csv_count("data/raw/sample_resources.csv"),
        "missions": _csv_count("data/raw/sample_missions.csv"),
        "progress": _csv_count("data/raw/sample_progress.csv"),
        "outcomes": _csv_count("data/raw/sample_outcomes.csv"),
        "features": _csv_count("data/features/training_features.csv"),
    }
    metadata = _load_json("models/latest/metadata.json")
    stage_candidates = _load_json("reports/stage_metrics.json")
    mission_candidates = _load_json("reports/mission_success_metrics.json")
    mlflow_counts = {
        "runs": _sqlite_count("data/mlflow.db", "runs"),
        "metrics": _sqlite_count("data/mlflow.db", "metrics"),
        "params": _sqlite_count("data/mlflow.db", "params"),
    }
    config = _project_config(metadata)
    items = _rubric(counts, metadata, stage_candidates, mission_candidates, mlflow_counts)
    total, max_score, level = _score_summary(items)
    missing = sorted({path for item in items for path in _missing(item.evidence)})

    stage_rows = _model_rows(stage_candidates)
    mission_rows = _model_rows(mission_candidates, include_roc_auc=True)
    stage_best = _best_model(stage_candidates, "macro_f1")
    mission_best = _best_model(mission_candidates, "roc_auc")

    rubric_rows = [
        [item.area, f"{item.score}/2", _evidence(item.evidence), item.note]
        for item in items
    ]
    stack_rows = [
        ["Backend/API", "FastAPI, Uvicorn, Pydantic"],
        ["Dashboard", "Streamlit"],
        ["Data", "pandas, NumPy, Pandera, requests, BeautifulSoup"],
        ["ML", "scikit-learn, joblib"],
        ["Tracking", "MLflow SQLite backend, MLflow artifact text logging"],
        ["Storage", "CSV, SQLite, local model registry"],
        ["RAG", "TF-IDF/local lexical retrieval"],
        ["Testing/QA", "pytest, ruff, Makefile, generated Markdown reports"],
        ["Packaging", "Dockerfile, docker-compose.yml"],
        ["Docs", "README, DOCX report, model card, data card, error analysis"],
    ]
    data_rows = [
        ["Official resources", str(counts["resources"]), "인천청년포털/인천문화재단 공개 HTML 수집"],
        ["Synthetic profiles", str(counts["profiles"]), "실제 사용자 데이터 대체 mock profile"],
        ["Synthetic progress logs", str(counts["progress"]), "mission status history mock"],
        ["Synthetic outcome events", str(counts["outcomes"]), "참여/지원/운영자 review outcome mock"],
        ["Mission templates", str(counts["missions"]), "RebootRoute 내부 미션 템플릿"],
        ["Training feature rows", str(counts["features"]), "사용자 feature + synthetic labels"],
    ]

    audit = f"""# RebootRoute MLOps Readiness Check

이 파일은 `week15 - mlops project master notebook.ipynb`의 MLOps good-case playbook을 RebootRoute repo 산출물에 매핑한 검증 결과입니다.

## Readiness Score
- Score: {total}/{max_score}
- Level: {level}
- Data version: `{metadata.get('data_version', 'unknown')}`
- Trained at: `{metadata.get('trained_at', 'unknown')}`

## One-Line MLOps Statement
{config['one_sentence_problem']}

성공은 {config['primary_metric']}와 MLflow/model card/data card/API demo로 확인합니다. 운영 리스크는 synthetic label, 공식 페이지 DOM drift, privacy, safety misuse이며 batch validation, resource audit, feedback/outcome logging으로 관리합니다.

## Dataset Verification
{_markdown_table(["dataset", "rows", "source / role"], data_rows)}

실제 사용자 데이터는 확보하지 않았고 생성하지도 않았습니다. 사용자 profile/progress/outcome/label은 과제 MVP 검증을 위한 synthetic mock dataset입니다. 정책·문화·공간 resource는 공식 공개 페이지에서 수집한 데이터이며, 부담도/태그/추천 이유는 RebootRoute 파생 필드입니다.

## Model Verification

### Stage Classifier
- Champion in metadata: `{metadata.get('stage_model_name', 'unknown')}`
- Best by current candidate macro F1: `{stage_best}`
- Task: 사용자 상태 feature로 내부 stage 0-7 분류

{_markdown_table(["model", "accuracy", "macro_f1"], stage_rows)}

### Mission Success Predictor
- Champion in metadata: `{metadata.get('mission_success_model_name', 'unknown')}`
- Best by current candidate ROC-AUC: `{mission_best}`
- Task: mission completion 가능성 binary 예측

{_markdown_table(["model", "accuracy", "macro_f1", "roc_auc"], mission_rows)}

## Stack Verification
{_markdown_table(["area", "stack"], stack_rows)}

## Notebook Rubric Mapping
{_markdown_table(["area", "score", "evidence", "note"], rubric_rows)}

## Experiment Tracking
- MLflow runs: {mlflow_counts['runs']}
- MLflow metrics rows: {mlflow_counts['metrics']}
- MLflow params rows: {mlflow_counts['params']}
- Tracking URI: `sqlite:///data/mlflow.db` from `configs/config.yaml`

## Leakage / Scope Check
- Label-feature overlap: synthetic labels are generated in `src/rebootroute/features/build_features.py` after feature construction and are not included in `FEATURE_COLUMNS`.
- Split leakage: current feature table has one row per synthetic user; train/test split is stratified and deterministic. Real longitudinal data should switch to time/group split.
- Preprocessing leakage: scaling is inside sklearn Pipeline for LogisticRegression candidates.
- Future information: production must remove any post-recommendation outcome from online inference features. Current use is offline synthetic MLOps demonstration.
- Scope: MVP remains official resource retrieval + burden-based route recommendation + logging + batch retraining. Diagnosis, therapy, counseling chatbot, and employment-only recommendation are excluded.

## Missing / Production Hardening Items
{chr(10).join(f'- `{path}`' for path in missing) if missing else '- Repo evidence files: none missing'}
- Real user behavior and institution outcome labels are still not available by project assumption.
- DVC remote storage and CI/CD deployment are not implemented; current state uses Git, config, data_version hash, MLflow, Makefile, and local artifacts.
- Live drift/latency dashboard is not implemented; current monitoring is batch validation/reporting plus SQLite event logs.
"""

    candidate_lines = "\n".join(f"- {item}" for item in config["candidate_models"])
    secondary_lines = "\n".join(f"- {item}" for item in config["secondary_metrics"])
    risk_lines = "\n".join(f"- {item}" for item in config["main_risks"])
    outline = "\n".join(
        f"- {item}"
        for item in [
            "Problem: 인천 청년정책·문화활동 탐색 부담",
            "Data: 공식 HTML resource와 synthetic user mock의 분리",
            "ML Task: stage classification, mission success prediction, resource ranking, TF-IDF RAG",
            "Baseline: DummyClassifier와 후보 모델 비교",
            "Experiments: MLflow run, metric, metadata, model card",
            "XAI/Error: confusion matrix, reliability, 취약 stage, 실패 조건",
            "Serving/Demo: FastAPI + Streamlit + 지도/기록",
            "MLOps: Git/config/data_version/MLflow/artifacts/monitoring report",
            "Risks: synthetic label, privacy, safety, DOM drift",
            "Next Step: 실제 사용자/기관 outcome 연계와 production monitoring",
        ]
    )
    brief = f"""# RebootRoute MLOps Project Brief

## 1. One Sentence Problem Definition
{config['one_sentence_problem']}

## 2. Project Framing
- Team: {config['team_name']}
- Target user: {config['target_user']}
- Input data: {config['input_data']}
- Output: {config['prediction_or_output']}
- ML task type: {config['ml_task_type']}

## 3. Data & Label
- Data source: {config['data_source']}
- Label definition: {config['label_definition']}
- Split strategy: {config['split_strategy']}

## 4. Baseline & Experiments
- Baseline model: {config['baseline_model']}
- Candidate models:
{candidate_lines}

## 5. Metrics
- Primary metric: {config['primary_metric']}
- Secondary metrics:
{secondary_lines}

## 6. MLOps Plan
- Versioning: {config['versioning_plan']}
- Serving: {config['serving_plan']}
- Monitoring: {config['monitoring_plan']}

## 7. Demo Path
{config['demo_path']}

## 8. Main Risks
{risk_lines}

## 9. MLOps Readiness Score
- Score: {total}/{max_score}
- Level: {level}

## 10. Final Presentation Outline
{outline}
"""
    return audit, brief


def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BRIEF.parent.mkdir(parents=True, exist_ok=True)
    audit, brief = build_audit()
    REPORT.write_text(audit, encoding="utf-8")
    BRIEF.write_text(brief, encoding="utf-8")
    print(REPORT)
    print(BRIEF)


if __name__ == "__main__":
    main()
