# Dashboard Redesign Notes

## Reference Sources

이번 재설계는 공공기관 웹사이트 스타일이 아니라, 젊은 사용자가 바로 행동을 고를 수 있는 모바일 앱형 route builder를 기준으로 정리했다.

- Composite UX Trends 2025: bento grid, layered surfaces, microinteractions
  - https://www.composite.global/news/top-ux-trends-in-2025
- Midrocket UI Trends 2026: modular bento layout, mature dark mode, restrained glass effect
  - https://midrocket.com/en/guides/ui-design-trends-2026/
- Muzli Mobile App Design Trends 2026: mobile-first adaptive UI, context-driven navigation
  - https://muz.li/blog/whats-changing-in-mobile-app-design-ui-patterns-that-matter-in-2026/
- UXPin Progressive Disclosure: 현재 필요한 선택만 먼저 보여주고 보조 조건은 접는 방식
  - https://www.uxpin.com/studio/blog/what-is-progressive-disclosure/

공식 데이터의 정보 구조와 원문 링크 검증에는 인천청년포털, 인천청년공간 대관, 인천문화재단 문화행사 페이지를 사용한다.

## Applied Principles

- 첫 화면은 `폼 + 결과 + 지도 + 기록` 나열이 아니라 `오늘의 루트 생성` 경험으로 구성한다.
- 핵심 선택지는 `오늘 가능한 범위`, `사람 만나는 정도`, `찾고 싶은 것`, `오늘 비용` 네 묶음으로 제한한다.
- 선택을 바꾸면 추천 미션, 공식 자원, 지도 후보가 즉시 갱신된다. 별도 `추천 루트` 버튼은 없다.
- 세부 조건은 `더 조정하기` 뒤에 숨긴다.
- 후보 목록과 결과 기록은 기본 화면에 펼치지 않고 progressive disclosure로 둔다.
- 사용자 화면에는 `resource_id`, `mission_id`, ranking score, RAG score, source_kind, source_checked_at, model metadata, raw payload를 노출하지 않는다.
- 운영자/연구자 정보는 `?operator=1`에서만 접근하는 `운영자 검증` 탭으로 분리한다.
- 라이트/다크 모드 모두 명시 색상 토큰을 사용해 버튼, segmented control, 카드 텍스트 대비를 유지한다.

## Current UI Structure

- 기본 탭: `내 루트`, `정책·문화 찾기`, `내 기록`
- 운영자 탭: `http://localhost:8501?operator=1`에서만 생성
- `내 루트` 첫 화면:
  - `RebootRoute`, `오늘 할 수 있는 인천 정책·문화 루트`, `4가지만 고르면 오늘 확인할 공식 정보와 작은 행동을 추천해요.` 상단 안내
  - 네 개의 segmented choice group
  - `더 조정하기` 세부 조건 버튼
  - 오늘의 작은 미션 카드
  - 가장 맞는 공식 자원 카드와 이미지, 공식 페이지 버튼
  - 위치 확인 지도 preview와 길찾기 버튼
  - 하단 고정 action bar: `오늘 이걸로 시작`, `완료`, `나중에`, `어려움`
- Desktop 1280x720:
  - 선택 영역 다음에 미션, 공식 자원, 지도 preview가 같은 줄에서 시작한다.
- Mobile 390x844:
  - 선택지는 한 줄 segmented control로 압축한다.
  - 하단 action bar는 한 줄 compact grid로 유지한다.
  - 자원 카드는 좌측 이미지, 우측 제목 구조로 첫 화면에서 일부라도 확인 가능하게 한다.

## Visual System

- Light background: `#F5F7FB`
- Light surface: `#FFFFFF`
- Light text: `#111827`
- Primary: `#2563EB`
- Secondary: `#14B8A6`
- Action accent: `#F97316`
- Dark background: `#0B1020`
- Dark surface: `#111827`
- Dark text: `#F8FAFC`
- Dark accents: `#60A5FA`, `#2DD4BF`, `#FB7185`
- Card radius: 16-18px
- Button radius: 999px
- Glass effect: selected choice, hero layer, bottom action only

## Validation Criteria

- 기본 사용자 URL에 `운영자 검증`, `Rule Stage`, `ML 보조 Stage`, `resource_id`, `mission_id`, `score`, `rag_score`, `html_scrape`, `source_checked_at`이 보이지 않아야 한다.
- `?operator=1`에서는 운영자 탭과 내부 지표가 보여야 한다.
- Desktop 1280x720에서 선택, 미션, 공식 자원, 지도 preview, primary CTA가 첫 화면에 들어와야 한다.
- Mobile 390x844에서 horizontal overflow가 0이어야 한다.
- 깨진 이미지가 없어야 한다.
- 다크 모드에서 segmented control 비선택/선택 텍스트가 모두 읽혀야 한다.
