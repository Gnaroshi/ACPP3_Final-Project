# RebootRoute Capstone Project Brief

## 1. Problem
인천 청년정책, 문화공간, 문화행사, 지원사업 정보는 흩어져 있고, 외출·대면·비용 부담이 있는 청년에게는 "무엇부터 확인할지" 자체가 높은 진입 장벽이 됩니다.

RebootRoute는 사용자의 오늘 가능한 조건을 기준으로 공식 출처 기반 인천 자원을 좁혀 보여주고, 부담이 낮은 다음 행동을 제안하는 MVP입니다.

## 2. Scope
포함하는 것:

- 인천 청년정책·문화활동 resource seed 검색
- TF-IDF 기반 local RAG 검색
- 부담도 기반 추천 루트와 오늘 할 미션
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
사용자는 대시보드에서 내 위치, 이동 가능 시간, 비용, 대면 부담, 관심 분야를 선택합니다. 화면은 즉시 추천 루트, 오늘 할 행동, 공식 출처 기반 자원 후보, 지도 위치를 보여줍니다. 사용자는 미션을 시작/완료/too-hard로 기록하거나, 프로그램 참여·지원 신청·지원 결과·미니 프로젝트 제출 outcome을 남길 수 있습니다.

## 4. Input and Output
입력:

- 현재 위치 또는 직접 입력한 위도/경도
- 외출 부담, 대면 부담, 에너지, 생활 리듬
- 관심 분야, 비용 한도, 이동 가능 시간
- 자원 종류, 구/군, 최대 부담도, 온라인 확인 가능 여부

출력:

- 사용자용 추천 루트
- 오늘 할 미션
- 공식 출처 기반 자원 카드
- 내 위치와 활동 장소 지도
- progress/feedback/outcome log
- 내부 검증용 stage, score, metric, raw payload

## 5. Success Criteria
기능 기준:

- `make pipeline`이 sample data 생성, 검증, feature build, 학습, DB 초기화, report 생성을 완료한다.
- `make test`가 API, 추천, RAG, feedback/outcome, safety guardrail 테스트를 통과한다.
- `make eval-sheet`가 human evaluation review sheet를 생성한다.
- Streamlit dashboard에서 사용자 흐름이 입력 -> 추천 -> 지도 -> 기록 순서로 동작한다.
- FastAPI `/rag/search`, `/feedback/log`, `/progress/log`, `/outcomes/log` endpoint가 동작한다.

평가 기준:

- Stage classifier와 mission success predictor가 dummy baseline보다 높은 지표를 보인다.
- Human rubric evaluation에서 공식 출처 근거, 부담도 적합성, 안전 분기, 사용자 화면 명확성을 평가할 수 있다.
- `reports/error_analysis.md`에서 confusion matrix와 실패 조건을 확인할 수 있다.

## 6. Data
실제 데이터:

- `data/raw/sample_resources.csv`: 공식 출처 기반 curated seed
- 출처 예: 인천청년포털, 인천광역시 청년지원센터 유유기지, 유유기지 부평, 동구청년21, 계양청년마당, 청년도전 지원사업, 드림체크카드, 인천문화재단, 인천아트플랫폼, 트라이보울, 인천생활문화센터 칠통마당, 한국근대문학관

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
3. 오늘 루트 탭에서 위치/부담/관심 분야 입력
4. 추천 루트, 오늘 할 미션, 공식 자원, 지도 확인
5. 미션 완료 또는 outcome 기록
6. 기록 탭에서 로그 확인
7. 검증 탭에서 모델/데이터/평가 산출물 확인

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
- 공식 자원 seed는 curated list이며 자동 동기화가 아님
- RAG는 local TF-IDF 검색이며 grounded generation은 아직 없음
- 개인정보 처리, 운영자 권한, 삭제 요청, 기관 연계 프로세스는 production 전 별도 설계 필요
