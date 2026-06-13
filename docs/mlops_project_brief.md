# RebootRoute MLOps Project Brief

## 1. One Sentence Problem Definition
우리는 인천 청년정책·문화활동 탐색 부담이 큰 청년을 위해 공식 자원 데이터와 사용자의 오늘 조건 입력을 사용하여 오늘 실행 가능한 낮은 부담의 루트와 미션을 제공한다.

## 2. Project Framing
- Team: RebootRoute
- Target user: 인천 거주 19-39세 고립·은둔 또는 고립 위험 청년과 지역 청년지원/문화기관 운영자
- Input data: 공식 HTML 수집 resource, synthetic MVP profile/progress/outcome, 사용자 현재 조건 입력, 미션/feedback/outcome log
- Output: stage 분류, mission success 확률 보조 예측, 공식 자원 랭킹, TF-IDF RAG 검색 결과, 오늘 할 미션
- ML task type: hybrid: rule-based recommendation + classification + ranking + local RAG retrieval

## 3. Data & Label
- Data source: 인천청년포털 청년정책/프로그램/공간대관 공개 HTML, 인천문화재단 문화행사 공개 HTML, 실제 사용자 데이터 대체 synthetic mock dataset
- Label definition: 현재 stage와 mission success label은 synthetic MVP placeholder입니다. production 전 실제 완료, too-hard, 참여/지원 결과, 운영자 review로 교체해야 합니다.
- Split strategy: one row per synthetic user, stratified train_test_split(test_size=0.25, random_seed=42)

## 4. Baseline & Experiments
- Baseline model: DummyClassifier
- Candidate models:
- DummyClassifier
- LogisticRegression
- RandomForestClassifier
- GradientBoostingClassifier

## 5. Metrics
- Primary metric: stage macro F1, mission ROC-AUC, mission macro F1, human rubric score
- Secondary metrics:
- accuracy
- confusion matrix
- reliability summary
- resource provenance validation

## 6. MLOps Plan
- Versioning: Git commit + config.yaml + data_version hash `d2a7440a96209a42` + model metadata. DVC remote는 아직 사용하지 않고 DVC-compatible 폴더 구조를 유지합니다.
- Serving: FastAPI /health, /recommend_route, /rag/search, /feedback/log, /progress/log, /outcomes/log + Streamlit dashboard
- Monitoring: batch validation, resource audit, MLflow run/metric logging, model/data card, error analysis, feedback/progress/outcome SQLite logs

## 7. Demo Path
make pipeline -> make dashboard -> hero/공식 자료 carousel 확인 -> 네 가지 조건 선택 -> 미션 전체폭 카드 확인 -> 추천 공식 자료 Top/지도 2열 확인 -> 추가 추천 자료의 장소 블록 확인 -> 시작/완료/too-hard/outcome 기록 -> 필요할 때만 ?operator=1 개발자/운영자 검증 확인

## 8. Main Risks
- synthetic label과 실제 사용자 행동의 차이
- 공식 페이지 DOM 변경으로 인한 수집 누락
- 개인정보/민감정보 저장 위험
- 추천을 상담/진단처럼 오해하는 safety risk
- 실제 운영 시 drift와 기관 outcome 연계 지연

## 9. MLOps Readiness Score
- Score: 26/26
- Level: A: 발표 준비 구조가 매우 좋음

## 10. Final Presentation Outline
- Problem: 인천 청년정책·문화활동 탐색 부담
- Data: 공식 HTML resource와 synthetic user mock의 분리
- ML Task: stage classification, mission success prediction, resource ranking, TF-IDF RAG
- Baseline: DummyClassifier와 후보 모델 비교
- Experiments: MLflow run, metric, metadata, model card
- XAI/Error: confusion matrix, reliability, 취약 stage, 실패 조건
- Serving/Demo: FastAPI + Streamlit + 지도/기록
- MLOps: Git/config/data_version/MLflow/artifacts/monitoring report
- Risks: synthetic label, privacy, safety, DOM drift
- Next Step: 실제 사용자/기관 outcome 연계와 production monitoring
