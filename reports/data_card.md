# RebootRoute 데이터 카드

## 데이터셋
- Synthetic MVP 프로필/진행 로그: 180건
- 공식 출처 기반 인천 자원 seed: 인천청년포털, 인천문화재단, 인천아트플랫폼, 트라이보울 등
- 데이터 폴더는 DVC-compatible 형태인 `data/raw`, `data/processed`, `data/features`를 따릅니다.
- 사용자 profile과 label은 실제 사용자가 아니라 학습·테스트용 synthetic sample입니다.
- 자원 검색 화면의 정책·문화 자원은 공식 페이지 URL을 포함한 curated seed data입니다.

## Label 상태
현재 label은 MVP 시연을 위한 synthetic label입니다. 운영 환경에서는 실제 프로그램 참여, 미션 완료, too-hard 피드백, 상담 준비도, 지원 결과 데이터로 반드시 교체해야 합니다.

필수 원문 고지:
These labels are synthetic MVP labels and must be replaced with real program participation / mission completion / support outcome data before production use.

## 사용 목적
대학원 과제 MVP, 공공데이터·문화데이터 공모전 프로토타입, 오프라인 데모에 사용합니다.

## 사용하면 안 되는 목적
의학적 진단, 치료, 배제 목적의 위험 점수화, 운영 환경의 개입 의사결정에는 사용할 수 없습니다.

## 실제 데이터 교체 경로
synthetic label은 미션 시작/완료/건너뜀/too-hard 피드백, 프로그램 참여, 상담 준비도, 운영자 review, 검증된 미니 프로젝트 제출 같은 관측 결과로 교체해야 합니다.
