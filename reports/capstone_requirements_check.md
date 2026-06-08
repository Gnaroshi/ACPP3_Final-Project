# Capstone PDF 요구사항 체크

이 파일은 `week15 - capstone project workshop.pdf`의 Week 16 ML system 발표 요구사항을 RebootRoute repo 산출물에 매핑한 점검표입니다.

| 요구사항 | 상태 | 근거 파일 | 비고 |
| --- | --- | --- | --- |
| 문제 정의와 사용자 시나리오 | 충족 | `README.md`<br>`docs/capstone_project_brief.md` | 인천 청년정책/문화활동 탐색 부담을 낮추는 MVP로 범위를 고정했습니다. |
| 입력/출력/성공 기준 | 충족 | `README.md`<br>`docs/capstone_project_brief.md`<br>`evaluation/rubric.md` | 데모 입력, 추천 출력, human rubric, 모델 지표, 실행 검증 기준을 문서화했습니다. |
| 데이터 소스와 접근 전략 | 충족 | `data/raw/sample_resources.csv`<br>`reports/data_card.md`<br>`docs/data_version_strategy.md` | 공식 HTML 수집 resource와 synthetic MVP label의 경계를 분리했습니다. |
| Repo 기본 구조 | 충족 | `data/raw`<br>`data/processed`<br>`notebooks`<br>`src`<br>`configs`<br>`reports`<br>`artifacts`<br>`README.md` | PDF 예시 구조를 추적 가능한 디렉터리와 실제 산출물로 맞췄습니다. |
| Baseline과 모델 학습 | 충족 | `scripts/train_models.py`<br>`reports/stage_metrics.json`<br>`reports/mission_success_metrics.json`<br>`docs/baseline_plan.md` | Dummy baseline과 후보 모델을 같은 split에서 비교합니다. |
| Experiment tracking | 충족 | `src/rebootroute/modeling/mlflow_utils.py`<br>`mlruns/.gitkeep`<br>`data/mlflow.db` | MLflow tracking URI를 SQLite로 설정하고 후보 모델 metric을 기록합니다. |
| Model card/data card | 충족 | `reports/model_card.md`<br>`reports/data_card.md` | 학습 데이터, label 상태, 사용 금지 목적, 운영 전 조건을 명시했습니다. |
| 오류분석과 해석 가능성 | 충족 | `src/rebootroute/modeling/explain.py`<br>`reports/error_analysis.md` | Baseline 비교, confusion matrix, reliability, 취약 구간, 실패 조건을 리포트로 생성합니다. |
| Serving/API | 충족 | `src/rebootroute/api/main.py`<br>`Dockerfile`<br>`docker-compose.yml` | FastAPI, Streamlit, Docker compose 실행 경로를 제공합니다. |
| Dashboard demo | 충족 | `src/rebootroute/dashboard/app.py`<br>`README.md` | 사용자 화면과 내부 검증 화면을 탭 흐름으로 분리하고 지도/결과 기록을 포함합니다. |
| Human evaluation | 충족 | `evaluation/human_eval_cases.csv`<br>`evaluation/rubric.md`<br>`reports/human_eval_review_sheet.csv` | Cold-start 평가를 open-loop human rubric 방식으로 구성했습니다. |
| 발표 산출물 | 충족 | `docs/RebootRoute_Project_Report.docx`<br>`docs/final_presentation_outline.md` | DOCX 명세서와 최종 발표 outline을 제공합니다. |
| 팀 역할과 운영 계획 | 충족 | `docs/capstone_project_brief.md`<br>`README.md` | Data, modeling, serving/MLOps, presentation/docs 역할을 명시했습니다. |

## 누락 항목
- 없음

## 최종 판단
누락 항목이 `없음`이면 PDF가 요구한 발표/구현/검증 산출물은 repo 안에서 확인 가능합니다. 단, 실제 사용자 데이터와 기관 outcome 데이터는 과제 환경에서 확보할 수 없으므로 synthetic MVP label과 공식 HTML 수집 resource의 경계를 README와 report에 명시했습니다.
