# RebootRoute Data Version Strategy

## 1. Directory Contract
RebootRoute는 PDF에서 제시한 raw/processed/features 구조를 사용합니다.

- `data/raw`: 원천 또는 seed 데이터
- `data/processed`: 중간 가공 산출물 위치
- `data/features`: 학습 feature table과 data version
- `models/latest`: 최신 모델 artifact와 metadata
- `reports`: data card, model card, metrics, error analysis
- `artifacts`: 발표/실험 보조 artifact 저장 위치

## 2. Current Data Sources
공식 출처 기반 resource seed:

- `data/raw/sample_resources.csv`
- seed definition: `src/rebootroute/data/mock_data.py`

Synthetic MVP data:

- `data/raw/sample_profiles.csv`
- `data/raw/sample_missions.csv`
- `data/raw/sample_progress.csv`
- `data/raw/sample_outcomes.csv`

이 synthetic 데이터는 실제 사용자를 나타내지 않습니다.

## 3. Version Hash
`src/rebootroute/features/build_features.py`는 raw input과 feature output을 기반으로 data version을 생성하고 다음 파일에 저장합니다.

- `data/features/data_version.json`
- `models/latest/metadata.json`

모델 version은 data version과 모델 이름을 포함합니다.

예:

- `stage-{data_version}-{stage_model_name}`
- `mission-success-{data_version}-{mission_success_model_name}`

## 4. Rebuild Procedure
데이터 seed를 수정하면 다음 명령으로 재생성합니다.

```bash
make pipeline
make eval-sheet
make capstone-check
make test
```

확인해야 할 파일:

- `data/features/training_features.csv`
- `data/features/user_features.csv`
- `data/features/data_version.json`
- `models/latest/metadata.json`
- `reports/data_card.md`
- `reports/model_card.md`
- `reports/error_analysis.md`

## 5. Replacement Path for Production
운영 전 교체 대상:

- synthetic profile -> 실제 동의 기반 사용자 상태 입력 또는 익명화된 운영 로그
- synthetic progress -> 실제 mission started/completed/skipped/too-hard log
- synthetic outcome -> 실제 프로그램 참여, 지원 신청, 지원 결과, 미니 프로젝트 검증 결과
- manual seed -> 공식 API/기관 제공 파일/운영자가 검수한 최신 resource table

교체 후에도 raw 데이터는 `data/raw`, feature는 `data/features`, 보고서는 `reports`에 남겨 같은 재현 경로를 유지합니다.
