# RebootRoute

**인천 청년정책·문화활동 RAG + 부담도 기반 미션 추천 MVP**

RebootRoute는 인천 청년정책·문화활동 정보를 근거 기반으로 검색하고, 사용자의 외출 부담·대면 부담·에너지·생활 리듬·관심사에 맞춰 낮은 부담의 다음 미션을 추천하는 한국어 AI/MLOps MVP입니다.

이 프로젝트는 정신건강 진단 앱, 치료 챗봇, 상담 챗봇, 단순 취업 추천 앱이 아닙니다. 교수 피드백을 반영해 MVP 범위를 **인천 청년정책/문화활동 RAG**와 **부담도 기반 단계형 미션 추천**으로 좁혔습니다.

## 1. 프로젝트 한 줄 요약

고립 또는 고립 위험 상태의 청년이 취업·상담·훈련으로 바로 이동하기 전에, 오늘 컨디션 정리 → 비대면 준비 → 동선 계획 → 낮은 부담 외출 → 저부담 참여 → 관심 기반 기록 → 작은 결과물 만들기 → 지원 연결 준비로 이동할 수 있도록 돕는 데모 시스템입니다.

## 2. 현재 구현 범위

### 포함된 기능

- Streamlit 대시보드
  - `오늘 루트` 화면
  - `인천 자원` 검색 화면
  - `운영자` 검증 화면
  - `평가` 화면
- FastAPI API
  - intake 분석
  - route/mission/resource 추천
  - RAG 검색
  - feedback/progress 로그 저장
  - 시나리오 simulation
- TF-IDF 기반 local RAG
  - 외부 LLM API 없이 실행
  - 인천 청년정책, 문화행사, 문화시설, 지원 프로그램 mock/public-data 후보 검색
- 부담도 기반 미션 추천
  - rule-based stage classifier가 1차 추천 기준
  - ML stage model은 보조 설명과 MLOps 시연용
- 안전 가드레일
  - 자해, 타해, 즉시 위험 표현 감지 시 일반 미션 추천 중단
  - 안전 확인 및 전문기관 연결로 분기
- feedback loop
  - `start`, `complete`, `skip`, `too_hard`, `resource_click`, `operator_review` 등 event schema
  - SQLite `feedback_events`, `progress_logs`, `user_state` 테이블
- MLOps pipeline
  - mock data 생성
  - 데이터 검증
  - feature build
  - synthetic label 생성
  - stage / mission success 모델 학습
  - model card / data card 생성
- Human evaluation
  - 40개 평가 케이스
  - rubric 기반 수동 평가 sheet 생성

### 포함하지 않는 기능

- 정신건강 진단, 치료 조언, 위험도 판정
- 상담 챗봇
- 채용공고 자동 추천
- 실제 사용자 대상 closed-loop A/B optimization
- Gemini 또는 외부 LLM 의존 기능

## 3. 실행 방법

작업 경로:

```bash
cd /Users/gnaroshi/Desktop/ajou/graduated/26-1/AI_convergence_practival_project_3/project/RebootRoute/rebootroute
```

### 3.1 의존성 설치

```bash
make setup
```

`requirements.txt`에는 다음 계열 의존성이 포함되어 있습니다.

- `fastapi`, `uvicorn`
- `streamlit`
- `pandas`, `numpy`, `scikit-learn`, `joblib`
- `pydantic`
- `pandera`
- `mlflow`
- `pytest`
- `PyYAML`

현재 RAG는 local TF-IDF 검색으로 동작하므로 Gemini API key는 필요하지 않습니다.

### 3.2 전체 파이프라인 실행

```bash
make pipeline
```

수행 단계:

1. `scripts/make_sample_data.py`로 deterministic mock data 생성
2. `rebootroute.data.validation`으로 데이터 검증
3. `rebootroute.features.build_features`로 feature table 생성
4. stage / mission success 모델 학습
5. SQLite DB 초기화
6. `reports/data_card.md`, `reports/model_card.md` 생성
7. `models/latest/metadata.json` 갱신

### 3.3 Streamlit 대시보드 실행

```bash
make dashboard
```

접속:

```text
http://localhost:8501
```

이미 `8501` 포트가 사용 중이면 Streamlit이 `8502` 같은 다음 포트로 실행될 수 있습니다. 이 경우 터미널에 표시되는 `Local URL`을 그대로 사용하면 됩니다.

### 3.4 FastAPI 실행

```bash
make api
```

접속:

```text
http://localhost:8000/docs
```

### 3.5 테스트 실행

```bash
make test
```

FastAPI가 설치되지 않은 환경에서는 API 테스트가 skip될 수 있습니다. `make setup` 후 다시 실행하면 API runtime까지 확인할 수 있습니다.

### 3.6 Human evaluation sheet 생성

```bash
make eval-sheet
```

생성 파일:

```text
reports/human_eval_review_sheet.csv
```

## 4. 대시보드에서 무엇을 봐야 하는가

### 4.1 오늘 루트

실제 사용자가 보는 화면에 가깝게 구성했습니다.

보이는 것:

- 나이, 거주 구/군, 접촉 선호, 관심 태그, 예산, 부담도, 에너지, 생활 리듬, 자유 입력
- 지금 시작점
- 추천 루트 이름과 부담 요약
- 오늘의 추천 미션
- 함께 볼 인천 자원
- 미니 일경험 후보

숨기는 것:

- `mission_id`
- `resource_id`
- 추천 score
- `Stage 0` 같은 내부 단계 번호
- `reboot_points` 같은 점수성 내부 상태
- 모델 후보별 metric
- 데이터 source key
- raw payload
- ML 내부 debug 정보

사용자가 미션에서 누를 수 있는 행동:

- `시작`
- `완료`
- `나중에`
- `너무 어려움`

이 행동은 `progress_logs`와 `feedback_events`에 기록됩니다. 자원 카드는 사용자 화면에서 정보 확인용으로만 표시하고 저장/북마크성 행동은 제공하지 않습니다. 완료 시 내부적으로 `user_state.reboot_points`가 갱신될 수 있지만, 실제 사용자 화면에는 점수로 보여주지 않습니다.

### 4.2 인천 자원

인천 청년정책·문화활동 mock/public-data 후보를 검색하는 RAG 화면입니다.

보이는 것:

- 검색 답변
- 자원 이름
- 자원 유형
- 구/군
- 비용
- 부담도

사용자 화면에서는 RAG score, resource ID, 내부 source key를 숨깁니다.

### 4.3 운영자

연구자, 운영자, 발표자가 내부 로직을 검증하는 화면입니다.

보이는 것:

- Rule 기반 추천 stage
- ML 보조 stage
- safety flag
- data version
- contributing factors
- 추천 미션 debug table
  - `mission_id`
  - `stage`
  - `mission_type`
  - `burden_level`
  - `score`
- 추천 자원 debug table
  - `resource_id`
  - `resource_type`
  - `source_url`
  - `score`
- stage별 후보 미션
- 자원 매칭 debug
- `feedback_events`
- `progress_logs`
- raw `analyze_profile` payload

### 4.4 평가

모델과 평가 산출물을 확인하는 화면입니다.

보이는 것:

- stage model name
- mission success model name
- data version
- trained time
- stage accuracy / macro F1
- mission success accuracy / macro F1 / ROC-AUC
- model card path
- data card path
- human eval sheet preview
- synthetic label warning

## 5. API 엔드포인트

### 기본 상태

- `GET /health`
- `GET /metadata`
- `GET /sample_profile`

### 추천

- `POST /analyze_intake`
- `POST /recommend_route`
- `POST /recommend_missions`
- `POST /recommend_resources`
- `POST /simulate`

### RAG

- `POST /rag/search`

### 로그

- `POST /feedback/log`
- `POST /progress/log`

### 예시: intake 분석

```bash
curl -X POST http://localhost:8000/analyze_intake \
  -H "Content-Type: application/json" \
  -d '{
    "age": 27,
    "district": "연수구",
    "free_text": "취업해야 하는데 자신이 없고 사람 만나는 것도 부담돼요. 요즘은 거의 집에만 있어요.",
    "future_anxiety": 5,
    "employment_burden": 5,
    "outside_burden": 4,
    "social_burden": 5,
    "energy_level": 2,
    "daily_rhythm_level": 2,
    "preferred_contact_mode": "online",
    "interests": ["culture", "writing", "design"],
    "max_outdoor_minutes": 20,
    "budget_limit": 0,
    "has_support_person": false
  }'
```

### 예시: RAG 검색

```bash
curl -X POST http://localhost:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "연수구에서 무료로 볼 수 있는 전시나 청년 문화활동",
    "district": "연수구",
    "resource_types": ["culture_event", "culture_facility", "youth_program", "support_program"],
    "max_burden_level": 3,
    "top_k": 5
  }'
```

### 예시: feedback 기록

```bash
curl -X POST http://localhost:8000/feedback/log \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "event_type": "too_hard",
    "mission_id": "mission_001",
    "recommended_stage": 1,
    "burden_after": 5,
    "appropriateness_rating": 2,
    "risk_rating": 1,
    "user_note": "생각보다 부담이 컸어요.",
    "policy_version": "streamlit_demo"
  }'
```

## 6. 프로젝트 구조

```text
rebootroute/
  configs/
    config.yaml
    safety_resources.example.yaml
  data/
    raw/
      sample_profiles.csv
      sample_progress.csv
      sample_resources.csv
      sample_missions.csv
    features/
      user_features.csv
      training_features.csv
      data_version.json
    rebootroute.db
  evaluation/
    human_eval_cases.csv
    rubric.md
  models/latest/
    stage_model.joblib
    mission_success_model.joblib
    metadata.json
  reports/
    data_card.md
    model_card.md
    human_eval_review_sheet.csv
    stage_metrics.json
    mission_success_metrics.json
  scripts/
    make_sample_data.py
    run_pipeline.py
    train_models.py
    build_human_eval_sheet.py
    init_db.py
  src/rebootroute/
    api/main.py
    dashboard/app.py
    database.py
    schemas.py
    config.py
    data/
    features/
    modeling/
    rag/
    recommender/
  tests/
```

## 7. 핵심 구현 상세

### 7.1 Data

`src/rebootroute/data/mock_data.py`가 deterministic mock data를 생성합니다.

생성되는 데이터:

- `sample_profiles.csv`
  - 19-39세 사용자 profile
  - 거주 구/군
  - 부담도, 에너지, 생활 리듬, 관심사
- `sample_missions.csv`
  - Stage 0-7 미션
  - 미션 유형
  - 예상 시간
  - 외출/대면 필요 여부
  - 부담도
  - reward points
- `sample_resources.csv`
  - youth program
  - culture event
  - culture facility
  - support program
  - contest
  - mini project
- `sample_progress.csv`
  - synthetic 진행 로그

실제 공공데이터 adapter stub:

- `src/rebootroute/data/fetch_youth_programs.py`
- `src/rebootroute/data/fetch_support_programs.py`
- `src/rebootroute/data/fetch_culture_events.py`
- `src/rebootroute/data/fetch_culture_facilities.py`
- `src/rebootroute/data/fetch_contests.py`

API key가 없어도 실패하지 않고 빈 DataFrame을 반환하도록 설계되어 있습니다.

### 7.2 Validation

`src/rebootroute/data/validation.py`

- `pandera`가 있으면 schema validation 수행
- `pandera`가 없으면 수동 validation fallback 수행
- profile/resource/mission/progress row count와 필수 column을 확인

### 7.3 Feature Build

`src/rebootroute/features/build_features.py`

생성 feature:

- demographic / intake feature
- burden score
- readiness score
- preferred contact encoding
- recent success rate
- recent too-hard rate
- completed stage count
- interest one-hot feature

현재 label:

- `synthetic_stage_label`
- `synthetic_mission_success`

중요: 현재 label은 MVP 시연용 synthetic label입니다.

### 7.4 Stage 분류

`src/rebootroute/recommender/stage_rules.py`

1차 추천 기준은 rule-based classifier입니다.

Stage:

- Stage 0: 오늘 컨디션 정리
- Stage 1: 비대면 준비
- Stage 2: 동선 계획
- Stage 3: 낮은 부담의 짧은 외출
- Stage 4: 저부담 참여
- Stage 5: 관심 기반 기록
- Stage 6: 작은 결과물 만들기
- Stage 7: 지원 연결 준비

### 7.5 Mission 추천

`src/rebootroute/recommender/mission_recommender.py`

점수 구성:

- stage match
- burden fit
- interest fit
- resource availability
- progress continuity
- novelty
- cost fit

사용자 화면에는 점수를 노출하지 않습니다. 점수는 `운영자` 탭에서만 확인합니다.

### 7.6 Resource 추천

`src/rebootroute/recommender/resource_recommender.py`

점수 구성:

- 구/군 일치
- 부담도 적합성
- 관심 태그 적합성
- 접촉 방식 적합성
- 비용 적합성
- career tag 적합성

사용자 화면에는 `resource_id`와 score를 노출하지 않습니다.

### 7.7 RAG 검색

`src/rebootroute/rag/retriever.py`

현재 구현:

- `sample_resources.csv` 기반 local retrieval
- `TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))`
- `cosine_similarity`
- sklearn이 없으면 token overlap fallback

반환:

- query
- answer
- sources
  - resource id
  - type
  - name
  - district
  - description
  - burden
  - source
  - rag score

사용자 화면에서는 score/id를 숨기고, 연구자 화면이나 API 응답에서만 확인합니다.

### 7.8 Safety Guardrail

`src/rebootroute/recommender/safety_guardrails.py`

감지 패턴:

- 자살
- 죽고 싶다
- 극단적 선택
- 사라지고 싶다
- 해치고 싶다
- kill myself
- hurt someone
- self-harm 등

분기:

- `safety_flag=True`
- `risk_type=urgent_support_needed`
- 일반 미션 추천 중단
- safety resources 반환

안전 자원 설정:

```text
configs/safety_resources.example.yaml
```

### 7.9 Feedback / Progress

`src/rebootroute/database.py`

SQLite DB:

```text
data/rebootroute.db
```

테이블:

- `progress_logs`
- `feedback_events`
- `user_state`

`오늘 루트`에서 미션 행동 버튼을 누르면:

- `progress_logs`에 미션 상태 기록
- `feedback_events`에 feedback event 기록
- 완료 시 `user_state.reboot_points` 증가

### 7.10 Modeling

`src/rebootroute/modeling/`

포함 모델:

- stage model
- mission success model

후보 모델:

- Dummy
- Logistic Regression
- Random Forest
- Gradient Boosting

추적:

- MLflow 설치 시 `data/mlflow.db` SQLite tracking backend
- MLflow artifact/fallback output: `mlruns/`
- MLflow 미설치 또는 tracking 실패 시 `mlruns/fallback_runs.jsonl`

MLflow 최신 버전에서는 `file:./mlruns` tracking backend가 차단될 수 있으므로 기본값은 `configs/config.yaml`의 `sqlite:///data/mlflow.db`입니다. 파일 backend를 강제로 써야 하는 환경에서만 `MLFLOW_ALLOW_FILE_STORE=true`를 별도로 설정합니다.

저장:

- `models/latest/stage_model.joblib`
- `models/latest/mission_success_model.joblib`
- `models/latest/metadata.json`

## 8. 발표 시 데모 흐름

추천 흐름:

1. `make dashboard`
2. `오늘 루트` 탭에서 기본 profile 확인
3. 외출 부담, 대면 부담, 에너지 수준을 조정
4. 화면 오른쪽의 시작점과 추천 미션이 즉시 바뀌는지 확인
5. 미션에서 `시작`, `완료`, `너무 어려움` 중 하나 클릭
6. `운영자`에서 feedback/progress log 반영 확인
7. `인천 자원` 탭에서 자원 검색
8. `운영자` 탭에서 내부 score, IDs, feedback log 확인
9. `평가` 탭에서 모델/평가 산출물 확인

안전 분기 데모:

1. `오늘 루트` 탭의 자유 입력에 위험 표현을 입력
2. 일반 미션 추천이 사라지는지 확인
3. 안전 확인 메시지와 도움 연결 자원이 표시되는지 확인

주의: 실제 발표에서는 자극적인 표현을 그대로 화면에 오래 노출하지 않는 것이 좋습니다.

## 9. 업데이트해야 할 것

### 9.1 실제 데이터로 교체

현재 데이터는 MVP 시연용 mock/synthetic data입니다.

교체 대상:

- 인천 청년정책 실제 데이터
- 문화행사/문화시설 실제 데이터
- 청년공간 정보
- 지원 프로그램 정보
- 실제 공모전/미니 일경험 후보

수정 위치:

- `src/rebootroute/data/fetch_*.py`
- `src/rebootroute/data/mock_data.py`
- `data/raw/*.csv`

### 9.2 실제 outcome label로 교체

현재 label은 실제 사용자의 결과가 아닙니다.

교체해야 할 label source:

- 미션 완료 여부
- too-hard feedback
- 미션 시작/건너뜀/재시도 행동
- 프로그램 참여 여부
- 문화활동 참여 여부
- 상담 준비도
- 미니 일경험 제출 여부
- 운영자 review label

수정 위치:

- `src/rebootroute/features/build_features.py`
  - `create_synthetic_labels`

재학습:

```bash
make pipeline
```

### 9.3 안전 자원 설정

운영 전 반드시 지역/기관 기준으로 검토해야 합니다.

수정 위치:

```text
configs/safety_resources.example.yaml
```

### 9.4 개인정보와 동의

운영 전 별도 설계가 필요합니다.

- 개인정보 수집 동의
- 민감 정보 처리 방침
- 로그 보존 기간
- 사용자 삭제 요청 처리
- 운영자 접근 권한
- 위험 표현 발견 시 escalation protocol

### 9.5 Gemini 또는 LLM 확장

현재 필수 아님.

나중에 붙일 수 있는 위치:

- query expansion
- grounded answer generation
- operator review assistant
- human evaluation 보조

주의: LLM이 직접 진단/치료/상담을 하도록 설계하면 안 됩니다.

## 10. 산출물

주요 산출물:

- README: `README.md`
- 발표용 상세 문서: `docs/RebootRoute_Project_Report.docx`
- model card: `reports/model_card.md`
- data card: `reports/data_card.md`
- human eval cases: `evaluation/human_eval_cases.csv`
- human eval rubric: `evaluation/rubric.md`
- human eval review sheet: `reports/human_eval_review_sheet.csv`
- models: `models/latest/`
- SQLite DB: `data/rebootroute.db`

## 11. 검증 명령

```bash
make test
make eval-sheet
make pipeline
```

최근 확인 기준:

- tests: 9 passed
- eval sheet 생성 성공
- pipeline 성공

## 12. Known Limitations

- 현재 데이터는 mock data입니다.
- 현재 label은 synthetic MVP label입니다.
- 실제 거리 계산이 아니라 구/군 일치 기반 proxy를 사용합니다.
- ML 모델은 임상 위험 모델이 아닙니다.
- RAG는 local TF-IDF retrieval이며 생성형 답변 품질은 제한적입니다.
- 실제 운영자 workflow, 개인정보 동의, 기관 연계 protocol은 별도 구현이 필요합니다.
- 실제 배포 전 구/군, 접근성, 경제적 부담, 대면 부담별 편향 점검이 필요합니다.

Required original notice:

> These labels are synthetic MVP labels and must be replaced with real program participation / mission completion / support outcome data before production use.
