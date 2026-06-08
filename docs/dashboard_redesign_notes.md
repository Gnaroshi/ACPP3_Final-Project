# Dashboard Redesign Notes

## 반영한 실제 서비스 패턴
이번 재디자인은 공공 정책/청년공간 서비스에서 반복되는 정보 구조를 기준으로 정리했습니다.

- GOV.UK Publishing Design Guide의 search filter 패턴: 필터는 검색 결과를 좁히는 용도로 쓰고, 모바일에서는 필터를 accordion으로 접어 결과 접근을 방해하지 않도록 합니다.
  - https://design-guide.publishing.service.gov.uk/patterns/search-filter/
- GOV.UK Design System patterns: 서비스 화면은 사용자 작업 중심의 패턴을 재사용하고, 맥락에 맞게 조합합니다.
  - https://design-system.service.gov.uk/patterns/
- Baymard Product List UX research: 목록/필터가 부실하면 사용자가 적합한 항목을 찾기 어렵고, 모바일 목록 UX 문제는 더 크게 드러납니다.
  - https://baymard.com/blog/current-state-product-list-and-filtering
- 인천청년포털 청년공간 페이지: 시설명, 주소, 이용대상, 운영시간, 문의처를 고정 구조로 보여줍니다.
  - https://youth.incheon.go.kr/youth/yeonsu.jsp
  - https://youth.incheon.go.kr/youth/gyeyang.jsp
- 인천청년포털 공간대관 목록: 전체/공간별 필터와 신청방법, 신청대상, 이용시간, 문의처, 공간명을 카드형으로 제공합니다.
  - https://youth.incheon.go.kr/youth/rental.jsp
- 온통청년 상담/정책 서비스: 맞춤형 상담, 예약/신청, 단계 안내를 명확한 순서와 CTA로 제공합니다.
  - https://www.youthcenter.go.kr/youthApply/ythApplyCounsel/ythCounselIntroMain
  - https://www.youthcenter.go.kr/youthApply/ythApplyCounsel/visitCounselMain

## 적용한 변경
- 기본 탭을 `내 루트`, `정책·문화 찾기`, `내 기록` 3개로 축소했습니다.
- 내부 검증 화면은 sidebar의 `운영자 도구 보기` toggle을 켰을 때만 나타납니다.
- 사용자 화면에서 stage 번호, mission/resource ID, score, point를 숨겼습니다.
- 정책/문화 자원 카드는 지역, 비용, 운영 기간, 확인 방식, 예상 시간, 거리, 문의, 출처를 같은 위치에 반복 표시합니다.
- 조건 입력은 핵심 조건을 먼저 보여주고, 세부 상태는 접어서 필요할 때만 열도록 했습니다.
- Streamlit theme primary color를 RebootRoute blue(`#0756A5`)로 고정해 slider, tab highlight, button 색상을 통일했습니다.
- Streamlit theme `base = "light"`를 명시하고 sidebar를 기본 접힘으로 설정했습니다.
- sidebar를 열어도 흰 배경과 진한 글자로 보이도록 dark/light 충돌을 CSS에서 차단했습니다.
- 모바일 폭에서 한 열로 쌓이도록 반응형 CSS를 보강했습니다.
- 첫 탭의 4단계 안내 카드를 제거하고 `조건 선택 -> 오늘 할 미션 -> 공식 자원 확인 -> 지도/기록 펼치기` 한 줄 흐름으로 축약했습니다.
- 기본 화면에는 현재 조건 요약만 두고, 위치·부담·에너지·시간·예산·관심사·검색 필터·상세 상태 수정은 접힌 `조건 바꾸기` 패널로 이동했습니다.
- 추천 결과는 대표 미션 1개를 첫 추천 카드에 직접 노출하고, 대표 공식 자원 1개만 함께 보여줍니다. 나머지 미션·자원·지도·결과 기록은 collapsed expander로 이동했습니다.
- 사용자 화면의 visible slider를 selectbox로 바꿔 모바일 세로 길이와 theme 색상 충돌을 줄였습니다.
- visual system을 다시 조정했습니다. 헤더는 진한 서비스 바, 미션은 blue accent, 다음 행동은 warm accent, 공식 자원은 teal accent로 역할별 색을 분리했습니다.
- 카드와 버튼에는 얕은 shadow와 일관된 8px radius를 적용해 Streamlit 기본 UI의 납작한 느낌을 줄였습니다.

## 검증
- Desktop 1440px: horizontal overflow 없음, low contrast 없음, 기본 탭 3개만 노출, 첫 화면에 조건·대표 미션·다음 행동·대표 자원 표시
- Mobile 390px: horizontal overflow 없음, low contrast 없음, visible slider 0개, 첫 화면에 조건 요약·대표 미션·시작 버튼 표시
- 사용자 화면의 slider는 selectbox/expander 구조로 교체했고 tab highlight는 `rgb(11, 92, 171)` 계열로 통일
- Sidebar: 기본 접힘, open 상태에서도 `#FFFFFF` 배경과 `#172033` 텍스트 적용
