# Dashboard Redesign Notes

## 반영한 실제 서비스 패턴
이번 재디자인은 공공 정책/청년공간 서비스에서 반복되는 정보 구조를 기준으로 정리했습니다.

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
- 모바일 폭에서 한 열로 쌓이도록 반응형 CSS를 보강했습니다.

## 검증
- Desktop 1440px: horizontal overflow 없음, low contrast 없음, 기본 탭 3개만 노출
- Mobile 390px: horizontal overflow 없음, 기본 탭 3개만 노출, 지도/다음 행동/자원 카드 렌더링 확인
- Slider와 tab highlight: `rgb(7, 86, 165)`로 통일
