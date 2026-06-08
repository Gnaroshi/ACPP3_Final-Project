from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rebootroute.config import ensure_directories, load_config
from rebootroute.features.build_features import FEATURE_COLUMNS, build_feature_tables
from rebootroute.modeling.registry import save_metadata
from rebootroute.modeling.train_mission_success_model import train_mission_success_model
from rebootroute.modeling.train_stage_model import train_stage_model


SYNTHETIC_WARNING = (
    "The current training labels are synthetic placeholders for user behavior and institution outcome labels. "
    "The logging, review, and retraining pipeline is implemented, but real observed mission completion, "
    "too-hard feedback, program participation, and support outcome labels must be collected or imported before production use."
)
SYNTHETIC_WARNING_KO = (
    "현재 학습 label은 사용자 행동과 기관 결과를 대신한 synthetic placeholder입니다. "
    "로그 수집, 운영자 검토, 재학습 구조는 구현되어 있지만, 실제 미션 완료, too-hard 피드백, "
    "프로그램 참여, 지원 결과처럼 관측이 필요한 outcome label은 운영 또는 기관 연계 후 수집·import해야 합니다."
)
STAGE_LABELS = {
    0: "방 안/온라인 확인",
    1: "저부담 정보 확인",
    2: "온라인 신청 준비",
    3: "짧은 외출",
    4: "저접촉 참여",
    5: "프로그램 참여",
    6: "미니 일경험",
    7: "지원 결과/자립 연결",
}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _metric_cell(value: object) -> str:
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


def _candidate_rows(candidates: dict[str, dict], include_roc_auc: bool = False) -> list[list[str]]:
    rows: list[list[str]] = []
    for name, metrics in candidates.items():
        row = [
            name,
            _metric_cell(metrics.get("accuracy")),
            _metric_cell(metrics.get("macro_f1")),
        ]
        if include_roc_auc:
            row.append(_metric_cell(metrics.get("roc_auc")))
        rows.append(row)
    return rows


def _confusion_matrix_table(matrix: list[list[int]], labels: list[str]) -> str:
    headers = ["actual \\ predicted", *labels]
    rows = [[labels[idx], *[str(value) for value in values]] for idx, values in enumerate(matrix)]
    return _markdown_table(headers, rows)


def _weakest_classes(metrics: dict, limit: int = 3) -> list[list[str]]:
    per_class = metrics.get("per_class", {})
    rows: list[list[str]] = []
    for label, values in per_class.items():
        if not isinstance(values, dict) or label in {"accuracy", "macro avg", "weighted avg"}:
            continue
        try:
            label_int = int(label)
        except ValueError:
            label_int = -1
        rows.append(
            [
                STAGE_LABELS.get(label_int, label),
                _metric_cell(values.get("precision")),
                _metric_cell(values.get("recall")),
                _metric_cell(values.get("f1-score")),
                _metric_cell(values.get("support")),
            ]
        )
    return sorted(rows, key=lambda row: float(row[3]) if row[3] != "n/a" else 0.0)[:limit]


def _write_error_analysis(metadata: dict) -> None:
    cfg = load_config()
    stage_metrics = metadata["stage_metrics"]
    mission_metrics = metadata["mission_success_metrics"]
    stage_candidates = metadata["all_stage_candidate_metrics"]
    mission_candidates = metadata["all_mission_success_candidate_metrics"]
    stage_labels = [str(idx) for idx in range(8)]
    mission_labels = ["not completed", "completed"]
    weakest_stage_rows = _weakest_classes(stage_metrics)
    reliability_rows = [
        [
            f"{row['prob_low']:.1f}-{row['prob_high']:.1f}",
            _metric_cell(row["mean_predicted_probability"]),
            _metric_cell(row["observed_success_rate"]),
            str(row["count"]),
        ]
        for row in mission_metrics.get("reliability_summary", [])
    ]

    report = f"""# RebootRoute 오류분석 및 해석 리포트

## 목적
이 리포트는 capstone 발표에서 요구하는 baseline 비교, 모델 성능 해석, confusion matrix, 실패 조건, 한계 설명을 한 파일에서 확인하기 위한 산출물입니다.

## 학습 산출물
- Data version: `{metadata['data_version']}`
- Stage model: `{metadata['stage_model_name']}`
- Mission success model: `{metadata['mission_success_model_name']}`
- Feature columns: {len(metadata['feature_columns'])}개

## Baseline 비교

### Stage classifier
{_markdown_table(["model", "accuracy", "macro_f1"], _candidate_rows(stage_candidates))}

### Mission success predictor
{_markdown_table(["model", "accuracy", "macro_f1", "roc_auc"], _candidate_rows(mission_candidates, include_roc_auc=True))}

## Confusion matrix

### Stage classifier
Stage 번호는 API/검증 화면의 내부 단계입니다. 사용자 화면에는 단계 번호를 노출하지 않습니다.

{_confusion_matrix_table(stage_metrics.get("confusion_matrix", []), stage_labels)}

### Mission success predictor
{_confusion_matrix_table(mission_metrics.get("confusion_matrix", []), mission_labels)}

## 취약 구간
{_markdown_table(["stage", "precision", "recall", "f1", "support"], weakest_stage_rows)}

## Mission success reliability summary
{_markdown_table(["probability bin", "mean predicted", "observed success", "count"], reliability_rows)}

## 해석 관점
- 추천의 1차 기준은 rule-based stage classifier와 공식 자원 속성입니다.
- ML 모델은 MLOps 시연, 내부 검증, 설명 요인 보조 목적으로 사용합니다.
- 주요 feature는 부담도, 에너지, 생활 리듬, 선호 접촉 방식, 최근 완료/too-hard 로그, 관심 분야입니다.
- 높은 `recent_too_hard_rate`, 높은 외출/대면 부담, 낮은 에너지/생활 리듬은 낮은 부담의 다음 행동으로 보내는 신호입니다.

## 주요 실패 조건
- 현재 stage label과 mission success label은 실제 사용자 관측값이 아니라 synthetic MVP label입니다.
- support가 작은 stage는 macro F1 변동이 큽니다. 특히 상위 단계는 표본이 적어 confusion matrix에서 오분류가 크게 보입니다.
- TF-IDF RAG는 `sample_resources.csv`에 수집된 공식 자원 안에서만 검색합니다. 수집되지 않았거나 DOM 변경으로 빠진 프로그램은 추천하지 못합니다.
- 거리 계산은 수집 자원의 위도/경도 또는 구/군 중심 좌표와 사용자의 데모 위치 입력을 기반으로 한 근사값입니다.
- 안전 표현이 감지되면 일반 추천이 아니라 안전 안내로 분기해야 하며, 이 흐름은 성능 지표가 아니라 정책/안전 요구사항입니다.

## 발표 시 해석 문장
현재 모델 성능은 "운영 성능"이 아니라 "파이프라인이 baseline보다 의미 있는 신호를 학습할 수 있는지"를 보여주는 MVP 검증 결과입니다. 실제 배포 전에는 미션 완료, too-hard 피드백, 프로그램 참여, 지원 결과, 운영자 review를 실제 관측 데이터로 교체하고 같은 리포트를 재생성해야 합니다.

## 필수 고지
{metadata['synthetic_label_warning_ko']}
"""
    (cfg.reports_dir / "error_analysis.md").write_text(report, encoding="utf-8")


def _write_reports(metadata: dict, row_count: int) -> None:
    cfg = load_config()
    cfg.reports_dir.mkdir(parents=True, exist_ok=True)

    def raw_count(filename: str) -> int:
        path = cfg.raw_data_dir / filename
        if not path.exists():
            return 0
        return len(pd.read_csv(path))

    profile_count = raw_count("sample_profiles.csv")
    progress_count = raw_count("sample_progress.csv")
    outcome_count = raw_count("sample_outcomes.csv")
    resource_count = raw_count("sample_resources.csv")
    data_card = f"""# RebootRoute 데이터 카드

## 데이터셋
- Synthetic MVP profile: {profile_count}건
- Synthetic MVP progress log: {progress_count}건
- Synthetic MVP outcome event: {outcome_count}건
- 학습 feature row: {row_count}건
- 공식 출처 기반 인천 자원: {resource_count}건, 인천청년포털 청년정책/프로그램/공간대관, 인천문화재단 문화행사
- 데이터 폴더는 DVC-compatible 형태인 `data/raw`, `data/processed`, `data/features`를 따릅니다.
- 사용자 profile/progress/outcome과 label은 실제 사용자가 아니라 학습·테스트용 synthetic mock sample입니다.
- 자원 검색 화면의 정책·문화 자원은 `make official-data`로 수집한 공개 공식 HTML 데이터입니다. 네트워크 없는 테스트에서는 `fallback_seed`가 사용될 수 있습니다.

## Label 상태
{SYNTHETIC_WARNING_KO}

필수 원문 고지:
{SYNTHETIC_WARNING}

## 사용 목적
대학원 과제 MVP, 공공데이터·문화데이터 공모전 프로토타입, 오프라인 데모에 사용합니다.

## 사용하면 안 되는 목적
의학적 진단, 치료, 배제 목적의 위험 점수화, 운영 환경의 개입 의사결정에는 사용할 수 없습니다.

## 구현된 것과 실제 관측이 필요한 것
- 구현됨: 공식 출처 HTML 수집기, resource provenance validation, feedback/progress/outcome schema, `/feedback/log`, `/progress/log`, `/outcomes/log`, 검증 view, 운영자 review 입력, human eval sheet, batch retraining pipeline
- 실제 관측 필요: 미션 시작/완료/건너뜀/too-hard, 프로그램 참여, 지원 결과, 운영자 review, 검증된 미니 프로젝트 제출 outcome
"""
    model_card = f"""# RebootRoute 모델 카드

## 모델
- Stage classifier: `{metadata['stage_model_name']}`
- Mission success predictor: `{metadata['mission_success_model_name']}`

## 학습 데이터
- Data version: `{metadata['data_version']}`
- 학습 시각: `{metadata['trained_at']}`

## 지표
- Stage macro F1: `{metadata['stage_metrics'].get('macro_f1')}`
- Stage accuracy: `{metadata['stage_metrics'].get('accuracy')}`
- Mission success macro F1: `{metadata['mission_success_metrics'].get('macro_f1')}`
- Mission success ROC-AUC: `{metadata['mission_success_metrics'].get('roc_auc')}`

## 안전성과 해석 가능성
추천의 1차 기준은 rule-based stage classifier입니다. ML 모델은 MLOps 시연과 보조 설명 요인 제공을 위해 포함합니다.

## Label 상태
{SYNTHETIC_WARNING_KO}

필수 원문 고지:
{SYNTHETIC_WARNING}

## 운영 배포 준비도
현재는 운영 배포용이 아닙니다. 실제 배포 전에는 사용자 행동·기관 outcome label 수집/연계, 구/군 및 접근성 조건별 편향 점검, 운영자 검증, 지역 기관 연계 프로토콜 수립이 필요합니다.
"""
    (cfg.reports_dir / "data_card.md").write_text(data_card, encoding="utf-8")
    (cfg.reports_dir / "model_card.md").write_text(model_card, encoding="utf-8")
    _write_error_analysis(metadata)


def train_all() -> dict:
    cfg = load_config()
    ensure_directories(cfg)
    feature_result = build_feature_tables()
    training = pd.read_csv(feature_result["training_path"])
    data_version = feature_result["data_version"]

    stage_result = train_stage_model(training, data_version)
    mission_result = train_mission_success_model(training, data_version)
    trained_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "project_name": cfg.project_name,
        "stage_model_version": f"stage-{data_version}-{stage_result['model_name']}",
        "mission_success_model_version": f"mission-success-{data_version}-{mission_result['model_name']}",
        "stage_model_name": stage_result["model_name"],
        "mission_success_model_name": mission_result["model_name"],
        "data_version": data_version,
        "trained_at": trained_at,
        "feature_columns": FEATURE_COLUMNS,
        "stage_model_path": stage_result["model_path"],
        "mission_success_model_path": mission_result["model_path"],
        "stage_metrics": stage_result["metrics"],
        "mission_success_metrics": mission_result["metrics"],
        "all_stage_candidate_metrics": stage_result["all_candidate_metrics"],
        "all_mission_success_candidate_metrics": mission_result["all_candidate_metrics"],
        "synthetic_label_warning": SYNTHETIC_WARNING,
        "synthetic_label_warning_ko": SYNTHETIC_WARNING_KO,
    }
    save_metadata(metadata)
    _write_json(cfg.reports_dir / "stage_metrics.json", stage_result["all_candidate_metrics"])
    _write_json(cfg.reports_dir / "mission_success_metrics.json", mission_result["all_candidate_metrics"])
    _write_reports(metadata, len(training))
    return metadata


def main() -> None:
    metadata = train_all()
    print(json.dumps({k: metadata[k] for k in ["stage_model_version", "mission_success_model_version", "data_version", "trained_at"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
