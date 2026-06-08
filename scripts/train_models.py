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
    "These labels are synthetic MVP labels and must be replaced with real program participation / "
    "mission completion / support outcome data before production use."
)
SYNTHETIC_WARNING_KO = (
    "현재 label은 MVP 시연을 위한 synthetic label입니다. 운영 환경에서는 실제 프로그램 참여, "
    "미션 완료, too-hard 피드백, 상담 준비도, 지원 결과 데이터로 반드시 교체해야 합니다."
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_reports(metadata: dict, row_count: int) -> None:
    cfg = load_config()
    cfg.reports_dir.mkdir(parents=True, exist_ok=True)
    data_card = f"""# RebootRoute 데이터 카드

## 데이터셋
- Synthetic MVP 프로필/진행 로그: {row_count}건
- 공식 출처 기반 인천 자원 seed: 인천청년포털, 인천문화재단, 인천아트플랫폼, 트라이보울 등
- 데이터 폴더는 DVC-compatible 형태인 `data/raw`, `data/processed`, `data/features`를 따릅니다.
- 사용자 profile과 label은 실제 사용자가 아니라 학습·테스트용 synthetic sample입니다.
- 자원 검색 화면의 정책·문화 자원은 공식 페이지 URL을 포함한 curated seed data입니다.

## Label 상태
{SYNTHETIC_WARNING_KO}

필수 원문 고지:
{SYNTHETIC_WARNING}

## 사용 목적
대학원 과제 MVP, 공공데이터·문화데이터 공모전 프로토타입, 오프라인 데모에 사용합니다.

## 사용하면 안 되는 목적
의학적 진단, 치료, 배제 목적의 위험 점수화, 운영 환경의 개입 의사결정에는 사용할 수 없습니다.

## 실제 데이터 교체 경로
synthetic label은 미션 시작/완료/건너뜀/too-hard 피드백, 프로그램 참여, 상담 준비도, 운영자 review, 검증된 미니 프로젝트 제출 같은 관측 결과로 교체해야 합니다.
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
현재는 운영 배포용이 아닙니다. 실제 배포 전에는 label 교체, 구/군 및 접근성 조건별 편향 점검, 운영자 검증, 지역 기관 연계 프로토콜 수립이 필요합니다.
"""
    (cfg.reports_dir / "data_card.md").write_text(data_card, encoding="utf-8")
    (cfg.reports_dir / "model_card.md").write_text(model_card, encoding="utf-8")


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
