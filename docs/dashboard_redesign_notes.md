# Dashboard Redesign Notes

이 문서는 RebootRoute Streamlit dashboard의 현재 구현 기준서입니다. 제품 정의는 "인천 청년정책·청년공간·문화행사·프로그램 공식 데이터를 오늘 확인할 수 있는 작은 행동으로 정리하는 MVP"입니다. 이 앱은 정신건강 진단, 치료, 상담 챗봇, 위험도 판정, 단순 취업 추천 앱이 아닙니다.

## 1. Design References

이번 재설계는 공공기관 홈페이지 복제가 아니라, 젊은 사용자가 공식 자료를 훑고 바로 조건을 좁힐 수 있는 현대적인 web app 흐름을 기준으로 정리했습니다.

- Composite UX Trends 2025: modular/bento layout, layered surfaces, restrained microinteractions
  - https://www.composite.global/news/top-ux-trends-in-2025
- Midrocket UI Trends 2026: modular bento layout, mature theme contrast, restrained glass effect
  - https://midrocket.com/en/guides/ui-design-trends-2026/
- Muzli Mobile App Design Trends 2026: mobile-first adaptive UI, context-driven navigation
  - https://muz.li/blog/whats-changing-in-mobile-app-design-ui-patterns-that-matter-in-2026/
- UXPin Progressive Disclosure: 현재 필요한 정보와 선택을 먼저 보여주고 보조 조건은 접는 방식
  - https://www.uxpin.com/studio/blog/what-is-progressive-disclosure/

공식 데이터의 정보 구조와 원문 링크 검증에는 인천청년포털, 인천청년공간 대관, 인천문화재단 문화행사 페이지를 사용합니다.

## 2. Current Information Architecture

기본 사용자 화면 순서:

1. Hero: `RebootRoute`와 서비스 범위를 크게 보여줍니다.
2. Project overview: 공식 자료 확인, 작은 행동 추천, 지도와 기록 연결을 설명합니다.
3. Official resource preview: 조건 선택 전에 수집된 인천 공식 자료를 먼저 비교합니다.
4. Tabs: `내 루트`, `정책·문화 찾기`, `내 기록`
5. Developer/operator panel: `?operator=1`에서만 기본 탭 아래에 표시됩니다.
6. Footer: 서비스 범위와 공식 페이지 최종 확인 원칙을 짧게 정리합니다.

`내 루트` 흐름:

1. 사용자가 오늘 쓸 수 있는 시간, 사람 만나는 부담, 먼저 보고 싶은 자료, 오늘 쓸 비용을 선택합니다.
2. 네 조건이 모두 선택되기 전에는 추천 결과를 확정 노출하지 않습니다.
3. 네 조건이 모두 선택되면 desktop에서는 조건 카드 4개가 한 줄로 유지됩니다. mobile에서는 한 장씩 세로로 쌓습니다.
4. 선택 완료 후 결과 영역은 오늘 할 작은 미션을 먼저 전체폭으로 보여주고, 그 아래에 가장 맞는 공식 자료와 지도 preview를 desktop 2열로 표시합니다.
5. `세부 조건 더 조정하기`는 동네, 검색어, 최대 부담도, 확인 방식처럼 결과를 더 좁히고 싶을 때만 엽니다.

`정책·문화 찾기` 흐름:

1. 사용자가 질문, 구/군, 최대 부담도를 입력합니다.
2. local TF-IDF RAG가 공식 자료 후보를 정렬합니다.
3. 검색 답변, 근거 카드, 공식 페이지 링크, 지도 preview를 보여줍니다.

`내 기록` 흐름:

1. 미션 시작/완료/나중에/too-hard progress log를 보여줍니다.
2. 프로그램 참여, 지원 신청, 지원 결과, 미니 프로젝트 제출 outcome log를 보여줍니다.
3. feedback event 개수를 확인합니다.

## 3. User / Operator Separation

기본 URL에서 숨기는 정보:

- `resource_id`
- `mission_id`
- ranking score
- RAG score
- source key, source kind, source checked timestamp
- model metric
- raw JSON payload
- operator/debug/admin information

`?operator=1`에서만 보이는 정보:

- rule-based stage
- ML 보조 stage
- safety flag
- data version
- contributing factors
- mission/resource debug table
- feedback/progress/outcome log
- model metadata
- model card/data card/human evaluation sheet preview
- operator review form

## 4. Visual System

현재 dashboard는 light theme을 기본으로 사용합니다.

- Page background: `#f7f4ff`
- Surface: `#ffffff`
- Main text: `#111827`
- Muted text: `#475569`
- Primary/nav ink: `#111827`
- Primary accent: `#7c3aed`
- Primary dark: `#4c1d95`
- Secondary accent: `#a855f7`
- Border: `rgba(148, 163, 184, 0.36)`
- Radius: cards 20-28px, buttons 999px

디자인 원칙:

- hero는 큰 타이틀, 설명, 실제 이미지가 있는 서비스 진입부로 사용하되 제목이 desktop에서 줄바꿈되지 않아야 합니다.
- 이미지가 필요한 곳에는 official thumbnail 또는 generated fallback image를 사용합니다.
- 선택 전 preview와 선택 후 result를 같은 시각 위계로 섞지 않습니다.
- 같은 역할의 card는 높이, padding, 이미지 비율, meta 위치를 맞춥니다.
- 버튼은 Streamlit native widget을 사용하고, CSS는 key/class 기반으로만 조정합니다.

## 5. Button Rules

기능 버튼은 반드시 Streamlit widget입니다.

- `st.button`
- `st.link_button`
- `st.form_submit_button`

Primary:

- `오늘 이걸로 시작`

Secondary:

- `완료`
- `공식 페이지 열기`
- `길찾기`
- `다시 추천받기`

Tertiary:

- `나중에`
- `어려움`
- `세부 조건 더 조정하기`
- `활동 결과 기록`
- `전체 자료 보기`

모든 중요 버튼은 stable key를 가져야 하며, 클릭 후 session state, database/API log, rerun 중 하나의 실제 동작을 수행해야 합니다.

## 6. CSS Structure

기존 단일 대형 CSS 문자열을 역할별 파일로 분리했습니다.

```text
src/rebootroute/dashboard/styles.py        # CSS file loader
src/rebootroute/dashboard/css/base.css     # page, typography, Streamlit base override
src/rebootroute/dashboard/css/hero.css     # hero, project overview
src/rebootroute/dashboard/css/navigation.css
src/rebootroute/dashboard/css/resources.css
src/rebootroute/dashboard/css/route.css
src/rebootroute/dashboard/css/cards.css
src/rebootroute/dashboard/css/results.css
src/rebootroute/dashboard/css/footer.css
src/rebootroute/dashboard/css/responsive.css
```

이미지 asset:

```text
src/rebootroute/dashboard/assets/rebootroute_hero_route.png
src/rebootroute/dashboard/assets/rebootroute_route_planning_scene.png
src/rebootroute/dashboard/assets/rebootroute_empty_planning.png
src/rebootroute/dashboard/assets/rebootroute_policy_support.png
src/rebootroute/dashboard/assets/rebootroute_culture_event.png
src/rebootroute/dashboard/assets/rebootroute_youth_space.png
src/rebootroute/dashboard/assets/rebootroute_map_preview.png
```

## 7. Validation Criteria

기능 검증:

- `오늘 이걸로 시작` 클릭 시 progress log에 `started`가 기록됩니다.
- `완료` 클릭 시 `completed`가 기록됩니다.
- `나중에` 클릭 시 `skipped`가 기록됩니다.
- `어려움` 클릭 시 `too_hard`가 기록됩니다.
- `세부 조건 더 조정하기` 클릭 시 advanced controls가 열리고 다시 클릭하면 접힙니다.
- 기본 URL에서는 개발자/운영자 정보가 보이지 않습니다.
- `?operator=1`에서만 개발자/운영자 검증 화면이 보입니다.

화면 검증:

- Desktop 1280px 이상에서 선택 완료 후 네 조건 카드가 한 줄로 정렬되어야 합니다.
- Desktop 1280px 이상에서 선택 완료 후 결과 영역은 `미션 전체폭 -> 공식 자료/지도 2열` 순서로 보여야 합니다.
- Desktop 1484px/1280px/1152px 폭에서 horizontal overflow가 0이어야 합니다.
- Mobile 390px 폭에서 horizontal overflow가 0이어야 합니다.
- Hero, project overview, official resource preview, tabs, route panel 순서가 유지되어야 합니다.
- 네 조건 선택 전에는 추천 결과가 확정 표시되지 않아야 합니다.
- 네 조건 선택 후 mission/resource/map/action이 같은 결과 영역에서 보여야 합니다.
- 사용자 화면에는 내부 ID, score, model metric, raw payload가 없어야 합니다.

최신 검증 결과:

- `uv run ruff check .`: passed
- `make test`: 29 passed
- Browser QA: desktop 1484/1152 and mobile 390 horizontal overflow 0
