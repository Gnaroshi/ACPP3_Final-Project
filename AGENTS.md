# AGENTS.md

## Product

RebootRoute is a Streamlit MVP that recommends low-burden next actions using official Incheon youth policy and culture resources.

The product is not a therapy app, not a diagnosis app, not a chatbot, and not a generic job-search portal.

The current dashboard flow is:

1. User reads the hero and project explanation.
2. User previews official Incheon resources before choosing conditions.
3. User selects today's available time, social burden, resource interest, and cost range.
4. App recommends a small mission, an official resource, and a map preview only after the required conditions are selected.
5. User records feedback through start / complete / later / too hard actions or outcome logging.

## UI source of truth

- `README.md` defines the product behavior.
- `docs/dashboard_redesign_notes.md` defines the dashboard UX direction.
- Do not invent a new product concept.
- Do not create a generic AI SaaS dashboard.

## Streamlit interaction rules

- Never replace functional Streamlit widgets with static HTML controls.
- Use `st.button`, `st.link_button`, `st.form_submit_button`, or other native Streamlit widgets for interactive controls.
- Use `st.session_state` or callbacks for persistent interaction state.
- Every important button must have a stable `key`.
- Do not create fake buttons with HTML, Markdown, or JavaScript-only interaction.

## Dashboard UX rules

The first screen must communicate:

- this is based on official Incheon youth policy, youth space, culture event, and program resources
- the user can preview official resources before selecting conditions
- choosing today's conditions produces a mission/resource/map route
- feedback and outcomes are recorded for later evaluation

Default users should not see:

- resource_id
- mission_id
- route_id
- score
- rag_score
- raw payload
- JSON payload
- model metadata
- operator/debug/admin information

Operator tools must be visible only with `?operator=1`.

## Visual design rules

Prefer:

- clear layout
- deliberate spacing
- calm colors
- readable cards
- one primary CTA
- clear secondary actions
- natural image placement
- useful map preview

Avoid:

- empty decorative hero sections
- excessive gradients
- glassmorphism
- meaningless empty space
- fake AI-dashboard aesthetics
- too many cards with equal visual weight
- buttons that look clickable but do not work

## Button hierarchy

Primary:

- 오늘 이걸로 시작

Secondary:

- 완료
- 공식 페이지 열기
- 길찾기
- 다시 추천받기

Tertiary:

- 나중에
- 어려움
- 세부 조건 더 조정하기
- 활동 결과 기록

Only one primary CTA should be visually dominant on the main route screen.

## Layout rules

- Page top padding should be compact.
- Section gap should generally be 16px to 24px.
- Card padding should generally be 16px to 20px.
- Advanced controls should be hidden behind progressive disclosure.
- Official resource preview should appear before the main tabs.
- Desktop 1280x720 should show the core flow without excessive scrolling.
- Mobile 390x844 should have no horizontal overflow.

## Validation

After UI changes, verify:

- app starts
- core buttons still work
- progress/feedback logging still works
- default URL hides operator tools
- `?operator=1` shows operator tools
- internal IDs and scores are hidden from the default user screen
- desktop and mobile layouts are usable

Do not claim validation was completed unless it was actually performed.
