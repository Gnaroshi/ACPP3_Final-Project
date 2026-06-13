# RebootRoute Capstone Project Brief

## 1. Problem
인천 청년정책, 문화공간, 문화행사, 지원사업 정보는 흩어져 있고, 외출·대면·비용 부담이 있는 청년에게는 "무엇부터 확인할지" 자체가 높은 진입 장벽이 됩니다.

RebootRoute는 사용자의 오늘 가능한 조건을 기준으로 공식 출처 기반 인천 자원을 좁혀 보여주고, 부담이 낮은 다음 행동을 제안하는 MVP입니다.

## 2. Scope
포함하는 것:

- 인천 청년정책·문화활동 resource seed 검색
- TF-IDF 기반 local RAG 검색
- 부담도 기반 오늘 루트와 오늘 할 미션
- 내 위치와 활동 장소를 함께 보여주는 지도
- progress, feedback, outcome logging
- stage classifier와 mission success predictor 학습/평가/추적
- human rubric evaluation sheet

포함하지 않는 것:

- 정신건강 진단/치료
- 상담 챗봇
- 위험도 판정
- 단순 취업 추천
- 실제 사용자 개인정보 수집

## 3. User Scenario
사용자는 먼저 hero와 프로젝트 설명에서 RebootRoute가 진단/상담 서비스가 아니라 인천 공식 자료를 오늘 할 작은 행동으로 정리하는 도구임을 확인합니다. 그 다음 조건 선택 전에 볼 공식 자료 carousel에서 청년정책, 청년공간, 문화행사, 프로그램을 훑어본 뒤 오늘 쓸 수 있는 시간, 사람 만나는 부담, 먼저 보고 싶은 자료, 오늘 쓸 비용을 선택합니다. Desktop에서는 네 조건 카드가 한 줄로 정렬되고, 선택이 끝나면 오늘 할 작은 미션이 먼저 전체폭으로 열립니다. 그 아래에는 공식 출처 기반 자원 카드와 지도 위치가 2열로 표시됩니다. 사용자는 미션을 시작/완료/too-hard로 기록하거나, 프로그램 참여·지원 신청·지원 결과·미니 프로젝트 제출 outcome을 남길 수 있습니다.

## 4. Input and Output
입력:

- 오늘 쓸 수 있는 시간
- 사람 만나는 부담
- 먼저 보고 싶은 공식 자료 종류
- 오늘 쓸 비용 범위
- 필요할 때만 여는 세부 조건: 현재 위치, 구/군, 검색어, 최대 부담도, 온라인 확인 가능 여부, 에너지/취업 부담/불안 메모

출력:

- 사용자용 오늘 루트
- 오늘 할 미션
- 공식 출처 기반 자원 카드
- 내 위치와 활동 장소 지도
- progress/feedback/outcome log
- `?operator=1`에서만 보이는 내부 검증용 stage, score, metric, raw payload

## 5. Success Criteria
기능 기준:

- `make pipeline`이 sample data 생성, 검증, feature build, 학습, DB 초기화, report 생성을 완료한다.
- `make test`가 API, 추천, RAG, feedback/outcome, safety guardrail 테스트를 통과한다.
- `make eval-sheet`가 human evaluation review sheet를 생성한다.
- Streamlit dashboard에서 사용자 흐름이 hero -> 공식 자료 preview -> 조건 선택 -> 추천/지도 -> 기록 순서로 동작한다.
- FastAPI `/rag/search`, `/feedback/log`, `/progress/log`, `/outcomes/log` endpoint가 동작한다.

평가 기준:

- Stage classifier와 mission success predictor가 dummy baseline보다 높은 지표를 보인다.
- Human rubric evaluation에서 공식 출처 근거, 부담도 적합성, 안전 분기, 사용자 화면 명확성을 평가할 수 있다.
- `reports/error_analysis.md`에서 confusion matrix와 실패 조건을 확인할 수 있다.

## 6. Data
실제 데이터:

- `data/raw/sample_resources.csv`: 인천청년포털 청년정책/프로그램/공간대관과 인천문화재단 문화행사 공개 HTML 수집 결과
- `reports/resource_audit.md`: 출처별 건수, 수집 시각, suspicious text 점검 결과

Synthetic MVP data:

- `data/raw/sample_profiles.csv`
- `data/raw/sample_progress.csv`
- `data/raw/sample_missions.csv`
- `data/raw/sample_outcomes.csv`

현재 label은 실제 사용자 관측값이 아닙니다. 실제 배포 전에는 미션 완료, too-hard 피드백, 프로그램 참여, 지원 결과, 운영자 review를 관측 데이터로 교체해야 합니다.

## 7. Modeling
Stage classifier:

- 후보: dummy most frequent, logistic regression, random forest, gradient boosting
- metric: accuracy, macro F1, per-class report, confusion matrix

Mission success predictor:

- 후보: dummy stratified, logistic regression, random forest, gradient boosting
- metric: accuracy, macro F1, ROC-AUC, reliability summary, confusion matrix

Tracking:

- MLflow candidate logging
- `models/latest/metadata.json`
- `reports/stage_metrics.json`
- `reports/mission_success_metrics.json`
- `reports/error_analysis.md`

## 8. Serving and Demo
Serving:

- FastAPI: `src/rebootroute/api/main.py`
- Streamlit: `src/rebootroute/dashboard/app.py`
- Docker: `Dockerfile`, `docker-compose.yml`

Demo path:

1. `make pipeline`
2. `make dashboard`
3. hero, 프로젝트 설명, 공식 자료 carousel 확인
4. 내 루트 탭에서 네 가지 조건 선택
5. 오늘 루트에서 미션 전체폭 카드, 공식 자원 카드, 지도 카드 확인
6. 미션 완료 또는 outcome 기록
7. 기록 탭에서 로그 확인
8. 필요할 때만 `?operator=1`로 개발자/운영자 검증 화면을 열어 모델/데이터/평가 산출물 확인

## 9. Team Roles
Data role:

- 공식 출처 resource seed 관리
- data validation schema 관리
- data card와 data version strategy 관리

Modeling role:

- stage/mission model 후보 학습
- baseline 비교
- error analysis와 model card 관리

MLOps/serving role:

- FastAPI endpoint
- Streamlit dashboard
- SQLite logging
- Docker/Makefile 실행 경로

Presentation/docs role:

- README
- DOCX report
- final presentation outline
- human evaluation rubric
- capstone requirement checklist

## 10. Current Limitations
- 실제 사용자 행동 데이터 없음
- 실제 기관 outcome 데이터 없음
- 공식 자원은 공개 HTML 수집 기반이며, 사이트 DOM 변경 시 파서를 갱신해야 함
- RAG는 local TF-IDF 검색이며 grounded generation은 아직 없음
- 개인정보 처리, 운영자 권한, 삭제 요청, 기관 연계 프로세스는 production 전 별도 설계 필요
