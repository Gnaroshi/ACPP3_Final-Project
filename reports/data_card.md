# RebootRoute 데이터 카드

## 데이터셋
- Synthetic MVP profile: 1000건
- Synthetic MVP progress log: 1948건
- Synthetic MVP outcome event: 1302건
- 학습 feature row: 1000건
- 공식 출처 기반 인천 자원: 73건, 인천청년포털 청년정책/프로그램/공간대관, 인천문화재단 문화행사
- 데이터 폴더는 DVC-compatible 형태인 `data/raw`, `data/processed`, `data/features`를 따릅니다.
- 사용자 profile/progress/outcome과 label은 실제 사용자가 아니라 학습·테스트용 synthetic mock sample입니다.
- 자원 검색 화면의 정책·문화 자원은 `make official-data`로 수집한 공개 공식 HTML 데이터입니다. 네트워크 없는 테스트에서는 `fallback_seed`가 사용될 수 있습니다.

## Label 상태
현재 학습 label은 사용자 행동과 기관 결과를 대신한 synthetic placeholder입니다. 로그 수집, 운영자 검토, 재학습 구조는 구현되어 있지만, 실제 미션 완료, too-hard 피드백, 프로그램 참여, 지원 결과처럼 관측이 필요한 outcome label은 운영 또는 기관 연계 후 수집·import해야 합니다.

필수 원문 고지:
The current training labels are synthetic placeholders for user behavior and institution outcome labels. The logging, review, and retraining pipeline is implemented, but real observed mission completion, too-hard feedback, program participation, and support outcome labels must be collected or imported before production use.

## 사용 목적
대학원 과제 MVP, 공공데이터·문화데이터 공모전 프로토타입, 오프라인 데모에 사용합니다.

## 사용하면 안 되는 목적
의학적 진단, 치료, 배제 목적의 위험 점수화, 운영 환경의 개입 의사결정에는 사용할 수 없습니다.

## 구현된 것과 실제 관측이 필요한 것
- 구현됨: 공식 출처 HTML 수집기, resource provenance validation, feedback/progress/outcome schema, `/feedback/log`, `/progress/log`, `/outcomes/log`, 검증 view, 운영자 review 입력, human eval sheet, batch retraining pipeline
- 실제 관측 필요: 미션 시작/완료/건너뜀/too-hard, 프로그램 참여, 지원 결과, 운영자 review, 검증된 미니 프로젝트 제출 outcome
