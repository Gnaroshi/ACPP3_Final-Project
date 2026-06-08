# RebootRoute MLOps Readiness Check

이 파일은 `week15 - mlops project master notebook.ipynb`의 MLOps good-case playbook을 RebootRoute repo 산출물에 매핑한 검증 결과입니다.

## Readiness Score
- Score: 26/26
- Level: A: 발표 준비 구조가 매우 좋음
- Data version: `d2a7440a96209a42`
- Trained at: `2026-06-08T16:04:42.033400+00:00`

## One-Line MLOps Statement
우리는 인천 청년정책·문화활동 탐색 부담이 큰 청년을 위해 공식 자원 데이터와 사용자 상태 입력을 사용하여 오늘 실행 가능한 낮은 부담의 루트와 미션을 제공한다.

성공은 stage macro F1, mission ROC-AUC, mission macro F1, human rubric score와 MLflow/model card/data card/API demo로 확인합니다. 운영 리스크는 synthetic label, 공식 페이지 DOM drift, privacy, safety misuse이며 batch validation, resource audit, feedback/outcome logging으로 관리합니다.

## Dataset Verification
| dataset | rows | source / role |
| --- | --- | --- |
| Official resources | 73 | 인천청년포털/인천문화재단 공개 HTML 수집 |
| Synthetic profiles | 1000 | 실제 사용자 데이터 대체 mock profile |
| Synthetic progress logs | 1948 | mission status history mock |
| Synthetic outcome events | 1302 | 참여/지원/운영자 review outcome mock |
| Mission templates | 42 | RebootRoute 내부 미션 템플릿 |
| Training feature rows | 1000 | 사용자 feature + synthetic labels |

실제 사용자 데이터는 확보하지 않았고 생성하지도 않았습니다. 사용자 profile/progress/outcome/label은 과제 MVP 검증을 위한 synthetic mock dataset입니다. 정책·문화·공간 resource는 공식 공개 페이지에서 수집한 데이터이며, 부담도/태그/추천 이유는 RebootRoute 파생 필드입니다.

## Model Verification

### Stage Classifier
- Champion in metadata: `random_forest`
- Best by current candidate macro F1: `random_forest`
- Task: 사용자 상태 feature로 내부 stage 0-7 분류

| model | accuracy | macro_f1 |
| --- | --- | --- |
| dummy_most_frequent | 0.288 | 0.056 |
| logistic_regression | 0.660 | 0.610 |
| random_forest | 0.856 | 0.809 |
| gradient_boosting | 0.860 | 0.785 |

### Mission Success Predictor
- Champion in metadata: `logistic_regression`
- Best by current candidate ROC-AUC: `logistic_regression`
- Task: mission completion 가능성 binary 예측

| model | accuracy | macro_f1 | roc_auc |
| --- | --- | --- | --- |
| dummy_stratified | 0.568 | 0.566 | 0.566 |
| logistic_regression | 0.840 | 0.839 | 0.922 |
| random_forest | 0.836 | 0.835 | 0.906 |
| gradient_boosting | 0.820 | 0.819 | 0.907 |

## Stack Verification
| area | stack |
| --- | --- |
| Backend/API | FastAPI, Uvicorn, Pydantic |
| Dashboard | Streamlit |
| Data | pandas, NumPy, Pandera, requests, BeautifulSoup |
| ML | scikit-learn, joblib |
| Tracking | MLflow SQLite backend, MLflow artifact text logging |
| Storage | CSV, SQLite, local model registry |
| RAG | TF-IDF/local lexical retrieval |
| Testing/QA | pytest, ruff, Makefile, generated Markdown reports |
| Packaging | Dockerfile, docker-compose.yml |
| Docs | README, DOCX report, model card, data card, error analysis |

## Notebook Rubric Mapping
| area | score | evidence | note |
| --- | --- | --- | --- |
| Problem | 2/2 | `README.md`<br>`docs/capstone_project_brief.md`<br>`docs/mlops_project_brief.md` | MVP 범위를 인천 청년정책·문화활동 RAG와 부담도 기반 미션 추천으로 고정했습니다. |
| Data | 2/2 | `data/raw/sample_resources.csv`<br>`reports/data_card.md`<br>`reports/resource_audit.md` | 공식 자원 73건, synthetic profile 1000건, progress 1948건, outcome 1302건을 분리했습니다. |
| Split | 2/2 | `src/rebootroute/modeling/train_stage_model.py`<br>`src/rebootroute/modeling/train_mission_success_model.py` | 현재 feature table은 사용자당 1행이라 동일 사용자 중복 누수는 없고 stratified split을 사용합니다. 실제 운영 로그 전환 후에는 time/group split이 필요합니다. |
| Baseline | 2/2 | `docs/baseline_plan.md`<br>`reports/stage_metrics.json`<br>`reports/mission_success_metrics.json` | Stage와 mission success 모두 Dummy baseline과 후보 모델을 같은 split에서 비교합니다. |
| Metric | 2/2 | `src/rebootroute/modeling/evaluate.py`<br>`reports/error_analysis.md` | Stage는 accuracy/macro F1/per-class/confusion matrix, mission은 ROC-AUC/reliability까지 기록합니다. |
| Versioning | 2/2 | `configs/config.yaml`<br>`data/features/data_version.json`<br>`models/latest/metadata.json` | Git, config.yaml, data_version hash, model metadata로 재현 근거를 남깁니다. DVC remote는 production 보강 항목입니다. |
| Tracking | 2/2 | `src/rebootroute/modeling/mlflow_utils.py`<br>`data/mlflow.db`<br>`mlruns` | MLflow SQLite backend에 runs 128건, metrics 320건, params 512건이 있습니다. |
| XAI/Error | 2/2 | `reports/error_analysis.md`<br>`src/rebootroute/modeling/explain.py` | Baseline 비교, confusion matrix, reliability summary, 취약 stage, 실패 조건을 리포트로 생성합니다. |
| Serving | 2/2 | `src/rebootroute/api/main.py`<br>`Dockerfile`<br>`docker-compose.yml` | FastAPI endpoint와 Streamlit dashboard, Docker compose 실행 경로가 있습니다. |
| Monitoring | 2/2 | `reports/resource_audit.md`<br>`reports/data_card.md`<br>`reports/model_card.md`<br>`reports/mlops_readiness_check.md` | 현재는 batch monitoring입니다. resource provenance, schema, MLflow metric, reliability, outcome log를 추적합니다. |
| Safety | 2/2 | `src/rebootroute/recommender/safety_guardrails.py`<br>`reports/data_card.md`<br>`reports/model_card.md` | 자해/폭력/즉시 위험 표현은 일반 추천이 아니라 안전 자원 안내로 분기합니다. 진단/상담/위험도 판정이 아님을 명시했습니다. |
| Demo | 2/2 | `README.md`<br>`src/rebootroute/dashboard/app.py`<br>`docs/final_presentation_outline.md` | make pipeline, make dashboard, 사용자 조건 선택, 추천/지도/기록, operator 검증 흐름을 제공합니다. |
| Champion | 2/2 | `models/latest/metadata.json`<br>`reports/error_analysis.md` | 현재 champion은 stage `random_forest`, mission success `logistic_regression`입니다. |

## Experiment Tracking
- MLflow runs: 128
- MLflow metrics rows: 320
- MLflow params rows: 512
- Tracking URI: `sqlite:///data/mlflow.db` from `configs/config.yaml`

## Leakage / Scope Check
- Label-feature overlap: synthetic labels are generated in `src/rebootroute/features/build_features.py` after feature construction and are not included in `FEATURE_COLUMNS`.
- Split leakage: current feature table has one row per synthetic user; train/test split is stratified and deterministic. Real longitudinal data should switch to time/group split.
- Preprocessing leakage: scaling is inside sklearn Pipeline for LogisticRegression candidates.
- Future information: production must remove any post-recommendation outcome from online inference features. Current use is offline synthetic MLOps demonstration.
- Scope: MVP remains official resource retrieval + burden-based route recommendation + logging + batch retraining. Diagnosis, therapy, counseling chatbot, and employment-only recommendation are excluded.

## Missing / Production Hardening Items
- Repo evidence files: none missing
- Real user behavior and institution outcome labels are still not available by project assumption.
- DVC remote storage and CI/CD deployment are not implemented; current state uses Git, config, data_version hash, MLflow, Makefile, and local artifacts.
- Live drift/latency dashboard is not implemented; current monitoring is batch validation/reporting plus SQLite event logs.
