# RebootRoute Final Presentation Outline

## Slide 1. Title and One-line Problem
- RebootRoute
- 인천 청년정책·문화활동 RAG + 부담도 기반 다음 행동 추천
- 문제: 정보는 있지만, 부담이 높은 사용자는 첫 행동을 고르기 어렵다.

## Slide 2. User Scenario and Non-goals
- 사용자: 인천 청년정책/문화활동을 찾고 싶은 청년 또는 지원자
- 시나리오: 오늘 가능한 조건을 고르면 공식 출처 기반 후보와 가장 작은 행동을 받는다.
- Non-goals: 진단, 치료, 상담 챗봇, 위험도 판정, 단순 취업 추천이 아니다.

## Slide 3. Data
- 공식 출처 resource seed: 인천청년포털, 유유기지, 인천문화재단, 인천아트플랫폼, 트라이보울 등
- Synthetic MVP data: profile, progress, mission label
- 실제 사용자 데이터 없음: 운영 전 실제 완료/too-hard/참여/지원 결과로 교체 필요
- Data card와 version strategy 제공

## Slide 4. System Architecture
- Streamlit dashboard
- FastAPI endpoint
- local TF-IDF RAG
- route/mission/resource recommender
- feedback/progress/outcome logging
- batch retraining pipeline
- MLflow tracking and report generation

## Slide 5. Modeling and Evaluation
- Stage classifier: dummy, logistic regression, random forest, gradient boosting
- Mission success predictor: dummy, logistic regression, random forest, gradient boosting
- Metric: macro F1, accuracy, ROC-AUC, confusion matrix
- Human evaluation: rubric + review sheet
- Error analysis: `reports/error_analysis.md`

## Slide 6. Live Demo Path
1. `make pipeline`
2. `make dashboard`
3. hero와 프로젝트 설명으로 서비스 범위 확인
4. 조건 선택 전에 볼 공식 자료 preview 확인
5. 내 루트 탭에서 오늘 쓸 수 있는 시간, 사람 만나는 부담, 먼저 볼 자료, 비용 범위 선택
6. 오늘 루트, 작은 미션, 자원 카드, 지도 확인
7. 시작/완료/too-hard 또는 outcome 기록
8. 기록 탭 확인 후, 필요할 때만 `?operator=1`로 개발자/운영자 검증 화면 확인

## Slide 7. What Is Implemented
- 공식 출처 기반 자원 검색
- local RAG
- 부담도 기반 추천
- 지도
- progress/feedback/outcome schema/API/dashboard
- model training pipeline
- MLflow tracking
- model/data/error analysis reports
- DOCX project report
- capstone requirement checklist

## Slide 8. Limitations and Next Steps
- 실제 사용자 행동 데이터 없음
- 공식 resource seed 자동 동기화 필요
- 개인정보 처리/삭제/권한 설계 필요
- 기관 outcome 연계 필요
- grounded answer generation은 추후 Gemini 등으로 확장 가능

## Slide 9. Closing
- RebootRoute는 사용자를 평가하는 앱이 아니라, 공식 정보를 부담도에 맞춰 실행 가능한 다음 행동으로 바꾸는 MVP다.
- 현재 단계의 핵심 검증은 closed-loop A/B가 아니라 human rubric evaluation과 batch retraining 준비도다.
