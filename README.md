# RebootRoute

**인천 청년정책·문화활동 RAG + 저부담 다음 행동 추천 MVP**

RebootRoute는 인천의 실제 청년정책·문화공간·문화행사 정보를 공식 출처 기반으로 보여주고, 사용자가 오늘 바로 끝낼 수 있는 작은 다음 행동을 제안하는 한국어 AI/MLOps MVP입니다.

이 프로젝트는 정신건강 진단, 치료, 상담 챗봇, 위험도 판정, 단순 취업 추천 앱이 아닙니다. 발표용 MVP의 초점은 다음 두 가지입니다.

- 인천청년포털, 인천문화재단, 인천아트플랫폼, 트라이보울 등 공식 출처 기반 자원 검색
- 비용, 대면 부담, 온라인 확인 가능 여부, 소요시간을 고려한 낮은 부담의 다음 행동 제안

## 1. 현재 결론

사용자 데이터를 실제로 확보할 수 없으므로, 현재 대시보드의 입력은 저장되지 않는 데모 세션 상태입니다. 대시보드 첫 화면은 다음 순서로 동작합니다.

1. 내 위치, 외출 가능 시간, 비용, 대면 부담, 관심 분야 입력
2. 현재 부담도에 맞는 추천 루트와 오늘 할 미션 확인
3. 지도에서 내 위치와 활동 장소를 함께 확인
4. 미션 시작/완료/too-hard 및 프로그램 참여, 지원 신청, 지원 결과, 미니 프로젝트 제출 기록

Synthetic profile과 synthetic label은 모델 학습, API 호환성, 검증, MLOps 시연을 위해서만 남아 있습니다. 실제 사용자 화면의 주 데이터는 공식 출처 기반 resource seed이며, 데모 중 남기는 progress/outcome은 SQLite에 기록됩니다.

## 2. 실행 방법

작업 경로:

```bash
cd /Users/gnaroshi/Desktop/ajou/graduated/26-1/AI_convergence_practival_project_3/project/RebootRoute/rebootroute
```

의존성 설치:

```bash
make setup
```

전체 파이프라인 실행:

```bash
make pipeline
```

Streamlit 대시보드 실행:

```bash
make dashboard
```

접속:

```text
http://localhost:8501
```

FastAPI 실행:

```bash
make api
```

API 문서:

```text
http://localhost:8000/docs
```

테스트:

```bash
make test
```

Human evaluation sheet 생성:

```bash
make eval-sheet
```

생성 파일:

```text
reports/human_eval_review_sheet.csv
```

Capstone PDF 요구사항 점검표 생성:

```bash
make capstone-check
```

생성 파일:

```text
reports/capstone_requirements_check.md
```

## 3. 대시보드에서 보는 순서

### 3.1 오늘 루트

실제 사용자에게 보여주는 메인 화면입니다.

보이는 것:

- 현재 위치 또는 직접 입력한 위도/경도
- 외출 부담, 대면 부담, 에너지, 생활 리듬, 관심 분야
- 추천 루트 이름과 설명
- 오늘 할 미션 카드
- 공식 출처 기반 인천 자원 카드
- 자원명, 설명, 구/군, 비용, 부담도
- 내 위치 기준 대략 거리
- 온라인 확인 가능 여부
- 예상 확인 시간
- 운영 기간 또는 공식 페이지 확인 필요 안내
- 주소, 문의처, 공식 출처 링크
- 오늘의 가장 작은 행동
- 지도 위 내 위치와 활동 장소
- 미션 시작, 완료, 나중에, 너무 어려움 버튼
- 프로그램 참여, 지원 신청, 지원 결과, 미니 프로젝트 제출 기록 폼

보이지 않는 것:

- `resource_id`
- `mission_id`
- ranking score
- RAG score
- reboot point
- model metric
- raw payload

사용자는 먼저 내 조건을 고릅니다. 조건을 바꾸면 추천 루트, 미션, 자원 후보, 지도 위치가 즉시 다시 계산됩니다. 별도의 업데이트 버튼이나 추천 루트 버튼을 누르지 않습니다.

그 다음 자원 종류를 고릅니다. 예시는 다음과 같습니다.

- 청년 프로그램
- 문화 행사
- 문화 시설
- 지원 정보
- 공모전
- 미니 일경험

자원 후보는 구/군, 비용, 최대 부담도, 온라인 확인 가능 여부, 내 위치와의 거리 기준으로 정렬됩니다.

### 3.2 자원·지도

TF-IDF 기반 local RAG 검색 화면입니다.

입력:

- 검색 질문
- 구/군 필터
- 최대 부담도

출력:

- 검색 답변
- 근거 자원 카드
- 공식 출처 링크
- 내 위치와 검색 결과 장소 지도

현재 RAG는 Gemini API key 없이 동작합니다. `src/rebootroute/rag/retriever.py`가 `data/raw/sample_resources.csv`를 읽고, `TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))` 기반 cosine similarity로 후보를 정렬합니다. scikit-learn을 사용할 수 없는 환경에서는 token overlap fallback을 사용합니다.

### 3.3 기록

데모 세션에서 사용자가 남긴 로그를 확인하는 화면입니다.

보이는 것:

- 미션 시작/완료/나중에/too-hard 진행 로그
- 프로그램 참여, 지원 신청, 지원 결과, 미니 프로젝트 제출 outcome 로그
- feedback event 개수

### 3.4 검증

내부 검증용 화면입니다. 실제 사용자에게 보여주는 화면이 아닙니다.

보이는 것:

- rule-based stage
- ML 보조 stage
- safety flag
- data version
- contributing factors
- 추천 미션 debug table
- 추천 자원 debug table
- feedback/progress/outcome 로그
- 운영자 검토 입력 폼
- raw `analyze_profile` payload
- stage model 이름
- mission success model 이름
- data version
- 학습 시각
- stage/mission metric
- model card 경로
- data card 경로
- human evaluation sheet preview
- synthetic label warning

여기에는 내부 ID와 score가 표시될 수 있습니다. 사용자 화면에서 숨긴 정보가 검증용으로만 남아 있는 구조입니다.

## 4. 데이터 구성

주요 파일:

```text
data/raw/sample_profiles.csv
data/raw/sample_missions.csv
data/raw/sample_resources.csv
data/raw/sample_progress.csv
data/raw/sample_outcomes.csv
data/features/training_features.csv
reports/data_card.md
reports/model_card.md
reports/human_eval_review_sheet.csv
models/latest/metadata.json
```

### 4.1 사용자 데이터

현재 실제 사용자 데이터는 없습니다.

`sample_profiles.csv`와 `sample_progress.csv`는 synthetic MVP sample입니다. 모델 학습, API 테스트, 운영자 점검을 위한 더미 데이터이며 실제 사용자 상태나 실제 완료 이력이 아닙니다.

이미 구현된 구조:

- 공식 출처 기반 resource seed
- feedback/progress schema와 SQLite table
- outcome schema와 SQLite table
- `/feedback/log` API
- `/progress/log` API
- `/outcomes/log`, `/outcomes` API
- 검증 view와 운영자 review 입력
- human eval sheet
- batch retraining pipeline

실제 관측이 필요한 label:

- 실제 미션 시작/완료/건너뜀/too-hard
- 실제 프로그램 참여 여부
- 실제 지원 결과
- 실제 운영자 review
- 검증된 미니 프로젝트 제출 여부

위 항목은 기능 구현 문제가 아니라 관측 데이터 문제입니다. 사용자 데이터와 기관 연계 데이터 없이 임의로 만들면 다시 synthetic label이 됩니다.

### 4.2 실제 자원 데이터

`sample_resources.csv`는 공식 출처 기반 curated seed입니다.

현재 포함된 출처 예:

- 인천청년포털
- 인천광역시 청년지원센터 유유기지
- 유유기지 부평
- 동구청년21
- 계양청년마당
- 청년도전 지원사업
- 드림체크카드
- 인천 청년도약기지
- 인천문화재단
- 인천아트플랫폼
- 트라이보울
- 인천생활문화센터 칠통마당
- 인천청년문화창작소 시작공간 일부
- 한국근대문학관

생성 로직:

```text
src/rebootroute/data/mock_data.py
```

함수명은 기존 호환성 때문에 `save_mock_data`, `ensure_mock_data`를 유지하지만, resource seed는 더 이상 `example.com` 기반 mock이 아닙니다.

## 5. API

FastAPI entrypoint:

```text
src/rebootroute/api/main.py
```

주요 endpoint:

```text
GET  /health
GET  /metadata
GET  /sample_profile
POST /analyze_intake
POST /recommend_route
POST /recommend_missions
POST /recommend_resources
POST /simulate
POST /rag/search
POST /feedback/log
POST /progress/log
POST /outcomes/log
GET  /outcomes
```

### POST /rag/search

요청 예:

```json
{
  "query": "연수구 무료 전시 청년 문화활동",
  "district": "연수구",
  "resource_types": ["culture_facility", "culture_event"],
  "max_burden_level": 3,
  "top_k": 5
}
```

응답에는 내부 확인을 위한 `rag_score`가 포함될 수 있습니다. 대시보드 사용자 화면은 score를 표시하지 않습니다.

### POST /feedback/log

요청 예:

```json
{
  "user_id": "demo_user_rebootroute",
  "event_type": "complete",
  "mission_id": "mission_001",
  "recommended_stage": 1,
  "burden_after": 2,
  "policy_version": "streamlit_demo"
}
```

현재 실제 사용자 화면에서는 개인정보성 feedback 수집을 강조하지 않습니다. 이 endpoint는 운영 전 데이터 루프 설계와 내부 테스트를 위해 유지합니다.

### POST /outcomes/log

요청 예:

```json
{
  "user_id": "demo_user_rebootroute",
  "outcome_type": "support_application",
  "outcome_status": "applied",
  "mission_id": "mission_014",
  "resource_id": "resource_004",
  "readiness_rating": 4,
  "burden_after": 3,
  "result_note": "지원 신청 완료",
  "policy_version": "streamlit_demo"
}
```

지원하는 outcome:

- `program_participation`
- `support_application`
- `support_result`
- `mini_project_submission`
- `operator_review`

## 6. 추천 로직

### 6.1 사용자 화면

현재 사용자 화면은 데모 세션 profile과 공식 자원 속성을 함께 사용합니다.

정렬 기준:

- 부담도 낮음
- 비용 낮음
- 온라인 확인 가능
- 내 위치와 가까움
- 예상 확인 시간 짧음
- 이름 순

다음 행동 예:

- 공식 페이지에서 현재 운영 여부 확인
- 대상, 비용, 운영시간, 마감 여부를 한 줄로 확인
- 문의처만 메모
- 오늘 결과물을 조건 1줄로 끝내기

### 6.2 내부 추천/API

기존 stage classifier와 mission recommender는 API와 운영자 점검용으로 남아 있습니다.

관련 파일:

```text
src/rebootroute/recommender/stage_rules.py
src/rebootroute/recommender/mission_recommender.py
src/rebootroute/recommender/resource_recommender.py
src/rebootroute/recommender/route_builder.py
```

Rule-based classifier가 1차 기준이고 ML model은 보조 설명 및 MLOps 시연용입니다.

## 7. 안전 가드레일

관련 파일:

```text
src/rebootroute/recommender/safety_guardrails.py
```

자해, 타해, 즉시 위험 표현이 들어오면 일반 미션 추천을 중단하고 안전 확인 안내 및 전문기관 연결로 분기합니다.

이 프로젝트는 위험도를 점수화하거나 진단하지 않습니다.

## 8. MLOps와 평가

Pipeline:

```bash
make pipeline
```

수행 단계:

1. synthetic profile/progress, outcome import template, 공식 출처 기반 resource seed 생성
2. 데이터 검증
3. feature table 생성
4. stage model 학습
5. mission success model 학습
6. SQLite DB 초기화
7. model card, data card, error analysis, metadata 생성

Baseline과 tracking:

- Stage classifier 후보: `dummy_most_frequent`, `logistic_regression`, `random_forest`, `gradient_boosting`
- Mission success 후보: `dummy_stratified`, `logistic_regression`, `random_forest`, `gradient_boosting`
- Tracking: MLflow SQLite backend (`data/mlflow.db`)와 `mlruns/`
- 최신 모델 metadata: `models/latest/metadata.json`
- Baseline 계획: `docs/baseline_plan.md`
- 오류분석/해석 리포트: `reports/error_analysis.md`
- 데이터 버전 전략: `docs/data_version_strategy.md`

Human evaluation:

```bash
make eval-sheet
```

입력:

```text
evaluation/human_eval_cases.csv
evaluation/rubric.md
```

출력:

```text
reports/human_eval_review_sheet.csv
```

초기에는 closed-loop A/B test가 아니라 open-loop + human rubric evaluation + batch retraining이 적절합니다. 실제 사용자 completion/outcome data가 없기 때문입니다.

Capstone workshop/PDF 대응 산출물:

```text
docs/capstone_project_brief.md
docs/baseline_plan.md
docs/data_version_strategy.md
docs/final_presentation_outline.md
docs/RebootRoute_Project_Report.docx
reports/capstone_requirements_check.md
reports/error_analysis.md
```

## 9. 무엇을 업데이트해야 하는가

### 실제 자원 업데이트

수정 파일:

```text
src/rebootroute/data/mock_data.py
```

수정 대상:

```text
REAL_RESOURCE_SEEDS
```

추가 또는 갱신해야 하는 필드:

- `name`
- `description`
- `district`
- `address`
- `latitude`
- `longitude`
- `start_date`
- `end_date`
- `cost_type`
- `online_available`
- `social_contact_level`
- `outdoor_required`
- `estimated_duration_minutes`
- `burden_level`
- `career_tags`
- `recovery_tags`
- `source_name`
- `source_url`
- `contact`

수정 후 실행:

```bash
make pipeline
make test
```

### Dashboard 문구/화면 업데이트

수정 파일:

```text
src/rebootroute/dashboard/app.py
```

사용자 화면에 노출하면 안 되는 것:

- 내부 ID
- score
- stage 번호
- point
- raw payload
- ML metric
- synthetic profile 설명

검증 탭에는 내부 확인을 위해 위 정보가 남아 있을 수 있습니다.

### RAG 검색 업데이트

수정 파일:

```text
src/rebootroute/rag/retriever.py
```

현재는 local TF-IDF 검색입니다. Gemini는 필수가 아닙니다. 나중에 붙인다면 다음 용도로 제한하는 것이 적절합니다.

- query expansion
- grounded answer generation
- 운영자 평가 보조

사용자-facing 답변에는 반드시 공식 출처 링크가 남아야 합니다.

## 10. 검증 명령

기본 검증:

```bash
make pipeline
make test
make eval-sheet
make capstone-check
```

대시보드 실행 후 확인할 것:

- 오늘 루트가 내 조건 → 추천 루트 → 지도 → 결과 기록 순서로 보이는지
- 공식 출처 링크가 보이는지
- 지도에서 내 위치와 활동 장소가 함께 보이는지
- ID/score/point가 사용자 카드에 보이지 않는지
- 필터 변경 시 결과가 즉시 바뀌는지
- 미션 시작/완료/too-hard와 outcome 기록이 SQLite에 저장되는지
- 모바일 폭에서 탭, 카드, 버튼, 글자가 겹치지 않는지
- 글자색이 배경과 충분히 대비되는지

## 11. 프로젝트 구조

```text
src/rebootroute/
  api/
    main.py
  dashboard/
    app.py
  data/
    mock_data.py
    validation.py
  features/
    build_features.py
  modeling/
    predict.py
    registry.py
    train_mission_success_model.py
    train_stage_model.py
  rag/
    retriever.py
  recommender/
    mission_recommender.py
    resource_recommender.py
    route_builder.py
    safety_guardrails.py
    stage_rules.py
  schemas.py
  database.py
scripts/
  run_pipeline.py
  train_models.py
  build_human_eval_sheet.py
  build_capstone_checklist.py
  build_project_report_docx.py
evaluation/
  human_eval_cases.csv
  rubric.md
reports/
  data_card.md
  model_card.md
  error_analysis.md
  capstone_requirements_check.md
  human_eval_review_sheet.csv
docs/
  capstone_project_brief.md
  baseline_plan.md
  data_version_strategy.md
  final_presentation_outline.md
  RebootRoute_Project_Report.docx
artifacts/
  .gitkeep
notebooks/
  .gitkeep
```

## 12. 발표 시 핵심 메시지

- RebootRoute는 진단/치료/상담 챗봇이 아니다.
- 실제 사용자 데이터가 없으므로 사용자-facing 데모는 개인정보 입력을 요구하지 않는다.
- 현재 사용자 화면은 공식 출처 기반 인천 정책·문화 자원을 보여주고, 오늘 할 수 있는 최소 행동을 제안한다.
- 내 위치와 활동 장소를 함께 보여주는 지도를 포함한다.
- Synthetic profile/label은 MLOps 파이프라인과 API 검증을 위한 내부 샘플이다.
- progress/feedback/outcome logging과 retraining 구조는 구현되어 있다.
- 실제 참여, 완료, too-hard, 운영자 review, 지원 결과는 사용자 또는 기관 관측이 있어야 실제 label이 된다.
- 초기 검증은 closed-loop A/B가 아니라 human rubric evaluation과 batch retraining이 맞다.

발표자가 열어볼 파일:

- 전체 구현 명세: `docs/RebootRoute_Project_Report.docx`
- 발표 outline: `docs/final_presentation_outline.md`
- PDF 요구사항 체크: `reports/capstone_requirements_check.md`
- 오류분석/해석: `reports/error_analysis.md`
- 데이터 카드: `reports/data_card.md`
- 모델 카드: `reports/model_card.md`

## 13. 현재 한계

- 실제 사용자 행동 데이터 없음
- 실제 사용자 또는 기관 관측 기반 mission completion/outcome label 없음
- 공식 자원 seed는 curated list이며 자동 크롤링/공공 API 동기화는 아직 없음
- RAG는 TF-IDF 기반 검색이며 grounded generation은 없음
- 운영기관 연계, 개인정보 처리, 삭제 요청 처리, 접근성 검증 프로세스는 production 전 별도 설계 필요

## 14. 최근 검증 기준

수정 후 최소 통과해야 하는 기준:

```text
make pipeline
make test
make eval-sheet
make capstone-check
```

대시보드는 desktop/mobile에서 글자 대비, overflow, 탭 표시, 카드 표시를 확인해야 합니다.
