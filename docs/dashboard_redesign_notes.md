# Dashboard Redesign Notes

## Reference Sources

이번 재디자인은 공공 서비스의 검색/필터/신청 흐름과 실제 인천 공식 사이트의 정보 구조를 기준으로 정리했다.

- GOV.UK Search filter pattern: 필터는 결과를 좁히는 도구이며, 핵심 결과 접근을 방해하지 않아야 한다.
  - https://design-system.service.gov.uk/patterns/search-filter/
- GOV.UK Accordion component: 중요한 내용을 accordion 안에 숨기지 않고, 숨겨도 되는 보조 정보에만 사용한다.
  - https://design-system.service.gov.uk/components/accordion/
- Department for Education filter component: desktop에서는 필터 영역과 결과 목록을 분리하고, mobile에서는 필터를 간결하게 유지한다.
  - https://design-system.service.gov.uk/community/design-system-backlog/filter-a-list-of-results/
- 인천청년포털 프로그램 목록: 신청기간, 진행기간, 공간명, 카테고리를 카드 반복 구조로 제공한다.
  - https://youth.incheon.go.kr/program/programInfoList.do?prgmdiv=all
- 인천청년포털 공간대관 목록: 신청방법, 신청대상, 이용시간, 문의처, 예약 링크를 카드에 고정 배치한다.
  - https://youth.incheon.go.kr/rental/rentalInfoList.do?inst_cd=gyeyang
- 인천문화재단 문화행사 목록: 진행상태, 행사명, 장소/주최, 기간, poster 이미지를 반복 카드로 제공한다.
  - https://www.ifac.or.kr/culturalInfo/cuturalEvents/performanceSrch/list.do?key=m2501152621396

## Applied Principles

- 사용자 화면에는 내부 ID, ranking score, RAG score, model metric, raw payload를 노출하지 않는다.
- 조건 입력, 추천 미션, 공식 자원, 지도, 기록을 같은 흐름에서 바로 볼 수 있게 한다.
- 핵심 정보는 expander 안에 숨기지 않는다.
- toggle/checkbox 남발 대신 selectbox 기반의 명확한 선택지로 줄인다.
- 공식 이미지 URL이 있으면 우선 사용하고, 없으면 프로젝트 내부 fallback 이미지를 사용한다.
- 다크 모드/라이트 모드 충돌을 피하기 위해 Streamlit theme를 light로 고정하고, CSS에서 표면/텍스트 대비를 명시한다.
- 모바일에서는 1열 구조로 쌓고, 카드 이미지와 텍스트가 겹치지 않게 한다.

## Current UI Structure

- 기본 탭: `내 루트`, `정책·문화 찾기`, `내 기록`
- 내부 검증 탭: URL에 `?operator=1`을 붙였을 때만 표시
- `내 루트` desktop 구조:
  - 왼쪽: 조건 입력 패널
  - 오른쪽: 오늘 할 미션, 공식 자원 카드, 가장 작은 다음 행동, 지도, 기록 폼
- `내 루트` mobile 구조:
  - 4단계 흐름
  - 데이터 상태 strip
  - 조건 입력
  - 오늘 할 미션
  - 공식 자원 카드
  - 지도
  - 기록
- 카드 이미지:
  - 공식 `thumbnail_url` 또는 `poster`가 있으면 원격 URL 표시
  - 없으면 `src/rebootroute/dashboard/assets/resource_*.png` fallback 사용

## Validation Criteria

- 사용자 화면에 `mission_id`, `resource_id`, `score`, `rag_score`가 보이지 않아야 한다.
- 첫 화면에서 사용자가 해야 할 순서가 `조건 입력 -> 오늘 할 미션 -> 공식 자원 -> 지도·기록`으로 보여야 한다.
- 공식 자원 카드에는 출처명, 상세 URL, 수집 시각이 있어야 한다.
- Desktop과 mobile 모두 글자 대비가 충분해야 하며, 기본 사용자 화면에는 sidebar를 쓰지 않는다.
- Mobile 390px 폭에서 horizontal overflow가 없어야 한다.
- visible user-facing expander는 사용하지 않는다. 운영자 debug의 raw payload만 expander로 허용한다.
