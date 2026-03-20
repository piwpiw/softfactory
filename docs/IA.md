# Growth Automation IA and Screen Design Spec

Updated: 2026-03-07
Status: active
Owner: product + frontend + backend + ops

## 1. Purpose

이 문서는 Growth Automation 화면 설계의 기준 문서다.
목표는 화면이 단지 데이터를 나열하는 수준을 넘어서, 운영자가 상황을 해석하고 다음 액션을 결정하고 결과를 검증할 수 있게 만드는 것이다.

이 문서는 프론트엔드 50 / 백엔드 50 비율로 읽히도록 구성한다.

- 프론트엔드 관점
  - 어떤 화면이 필요한가
  - 어떤 정보가 먼저 보여야 하는가
  - 어떤 컴포넌트가 어떤 행동을 유도하는가
  - 반응형과 시각 계층은 어떻게 유지되는가
- 백엔드 관점
  - 어떤 데이터와 상태가 화면의 근거가 되는가
  - 어떤 API와 이벤트가 화면 계약을 지지하는가
  - 어떤 실패 상태가 UI에 노출되어야 하는가

## 2. Linked Documents

화면 관련 변경은 아래 문서와 함께 움직여야 한다.

- Product intent and KPI source: [docs/PRD.md](/d:/Project/docs/PRD.md)
- Workflow and queue contract: [docs/Automation.md](/d:/Project/docs/Automation.md)
- Parallel build/update log: [docs/GROWTH_AUTOMATION_PARALLEL_UPDATE_2026-03-07.md](/d:/Project/docs/GROWTH_AUTOMATION_PARALLEL_UPDATE_2026-03-07.md)
- Responsive rules: [web/RESPONSIVE_DESIGN_GUIDE_CLEAN.md](/d:/Project/web/RESPONSIVE_DESIGN_GUIDE_CLEAN.md)
- Dashboard implementation note: [web/platform/DASHBOARD_IMPLEMENTATION_CLEAN.md](/d:/Project/web/platform/DASHBOARD_IMPLEMENTATION_CLEAN.md)
- Definition of done: [docs/DoD.md](/d:/Project/docs/DoD.md)

연동 규칙:

1. 화면 구조가 바뀌면 `docs/IA.md`를 갱신한다.
2. 반응형, 시각 구조, 구현 패턴 중 하나가 바뀌면 대응 문서를 같이 갱신한다.
3. 새 액션이나 상태가 생기면 PRD 또는 Automation 문서 중 하나에서 근거를 남긴다.

## 3. Product Meaning

Growth Automation의 제품 목표는 이벤트 수집부터 연락처 축적, 여정 상태 전이, 메시지 실행, 실패 복구까지를 한 화면 체계 안에서 운영 가능하게 만드는 것이다.

North star:

- Weekly active users who reach `key_action_completed`

이 지표를 중심에 두는 이유:

- `lead_captured`는 유입 시작 신호다.
- `signup_completed`는 등록 완료 신호다.
- `key_action_completed`는 실제 제품 가치 도달 신호다.

## 4. Design Principles

### 4.1 Screen philosophy

모든 화면은 아래 순서를 따른다.

1. Context
2. Decision
3. Action
4. Evidence

즉, 먼저 상황을 읽게 하고, 그 다음 판단하게 하며, 바로 행동하게 하고, 마지막에 그 행동의 근거와 결과를 검증하게 한다.

### 4.2 Layout hierarchy

기본 계층:

1. Hero
2. Summary
3. Main action area
4. Evidence area
5. Feedback or detail area

계층 의미:

- Hero: 이 페이지를 왜 보고 있는지 5초 안에 이해시킨다.
- Summary: 지금 운영 상태를 빠르게 읽게 한다.
- Main action area: 가장 중요한 액션을 바로 실행하게 한다.
- Evidence area: 숫자와 리스트, 테이블로 근거를 제공한다.
- Feedback/detail area: 실행 결과와 drill-down을 확인하게 한다.

### 4.3 Visual rules

- 상태는 `stable / pending / warning / failed`가 즉시 구분되어야 한다.
- KPI 카드는 2초 안에 훑어볼 수 있어야 한다.
- Primary action은 secondary action보다 시각적으로 우선해야 한다.
- 표는 단순 목록이 아니라 판단 근거를 읽는 도구여야 한다.
- 빈 상태는 다음 액션을 직접 제안해야 한다.

### 4.4 Responsive contract

세부 규칙은 [web/RESPONSIVE_DESIGN_GUIDE_CLEAN.md](/d:/Project/web/RESPONSIVE_DESIGN_GUIDE_CLEAN.md)를 따른다.

Growth Automation 공통 해석:

- Mobile
  - 1-column
  - 버튼은 세로 스택 허용
  - 표는 가로 스크롤 또는 요약 카드 대체 허용
- Tablet
  - summary와 action을 병렬 유지 가능
- Desktop
  - summary, action, evidence를 동시에 보여준다

추가 규칙:

- replay, seed event, filter는 hover 의존 패턴을 쓰지 않는다.
- 운영 액션은 모바일에서도 바로 눌릴 수 있어야 한다.

## 5. Backend Evidence Principles

화면의 모든 판단은 최소 한 개 이상의 근거 모델에 연결되어야 한다.

근거 타입:

- API endpoint
- Event name
- Queue contract
- State model
- Workflow rule

주요 도메인 객체:

| Domain Object | Primary Screen | UI Meaning | Example Fields |
|---|---|---|---|
| MarketingContact | Contacts | 유입 대상과 세그먼트 분포를 본다 | `contact_uid`, `email`, `phone`, `status`, `lifecycle_stage` |
| MarketingEvent | Hub, Ops, Journeys | 이벤트 유입과 처리 상태를 본다 | `event_name`, `event_ts`, `processing_status`, `idempotency_key` |
| MarketingJourneyState | Journeys, Hub | 전환 상태와 다음 액션 근거를 본다 | `journey_id`, `state`, `entered_at`, `last_action_at`, `cooldown_until` |
| MarketingDLQ | Ops, Hub | 실패 복구 우선순위를 판단한다 | `id`, `workflow_name`, `status`, `retry_count` |
| MarketingMessageLog | Hub, Ops | 메시지 실행 성과를 확인한다 | `status`, `created_at` |

주요 API:

| Endpoint | Screen | UI Role |
|---|---|---|
| `GET /api/v1/growth/dashboard/summary` | Hub, Contacts, Journeys, Ops | summary, baseline, compare |
| `GET /api/v1/growth/events` | Hub, Journeys, Ops | recent signal and evidence table |
| `GET /api/v1/growth/contacts` | Contacts | contact list and segment view |
| `GET /api/v1/growth/journeys` | Journeys | journey state table |
| `GET /api/v1/growth/dlq` | Ops | recovery target list |
| `POST /api/v1/growth/dlq/{id}/replay` | Ops | recovery action |
| `POST /api/v1/events` | Hub, Contacts, Journeys | simulation and progression action |

## 6. Canonical User Questions

### 6.1 Hub

- 오늘 가장 먼저 봐야 하는 운영 이슈는 무엇인가
- 지금 병목은 유입, 전환, 실패 중 어디에 있는가
- 지금 바로 실행할 액션은 무엇인가

### 6.2 Contacts

- 최근 유입은 실제로 연락처로 축적되고 있는가
- Lead, Active, At Risk 비중은 어떻게 바뀌는가
- 새 리드를 만들었을 때 시스템에 정상 반영되는가

### 6.3 Journeys

- 사용자가 어느 단계에 가장 많이 머무르는가
- lead에서 signup, signup에서 active로 실제 전환이 일어나는가
- at_risk가 늘고 있다면 어느 구간에서 생기는가

### 6.4 Ops

- 실패 이벤트와 DLQ 중 무엇이 더 시급한가
- replay 후 상태가 실제로 해소되는가
- pending과 failed 흐름은 이전 구간보다 개선되고 있는가

## 7. Screen Blueprint

### 7.1 Hub

목적:

- 전체 운영 상태를 가장 먼저 요약한다.

프론트엔드 구성:

- Hero
- summary cards
- today focus
- recommendation cards
- recent evidence tables

백엔드 근거:

- `dashboard/summary`
- `events`
- bootstrap fallback

핵심 액션:

- seed event 실행
- recommendation 확인

성공 기준:

- 운영자가 오늘의 우선순위를 10초 안에 이해한다.

### 7.2 Contacts

목적:

- 리드 생성, 연락처 축적, 세그먼트 변화를 같은 화면에서 다룬다.

프론트엔드 구성:

- 리드 생성 composer
- summary cards
- saved filters
- segment chips
- trend strip
- compare cards
- contact table
- detail panel

백엔드 근거:

- `contacts`
- `dashboard/summary`
- `events`

핵심 액션:

- 리드 생성
- 목록 새로고침
- 상태별 필터 전환

성공 기준:

- 리드 생성 후 연락처 목록과 세그먼트 변화가 즉시 확인된다.

### 7.3 Journeys

목적:

- 여정 전진, 상태 전이, 전환 병목을 직접 확인한다.

프론트엔드 구성:

- progression action panel
- action checklist
- stage cards
- saved filters
- trend strip
- compare cards
- journey table
- recent event table
- detail panel

백엔드 근거:

- `journeys`
- `events`
- `dashboard/summary`

핵심 액션:

- `lead_captured`
- `signup_completed`
- `key_action_completed`
- `payment_failed`

성공 기준:

- 이벤트 실행 후 상태 카드, 테이블, 힌트 영역이 함께 갱신된다.

### 7.4 Ops

목적:

- 실패 이벤트와 DLQ를 분리해서 읽고, replay까지 즉시 수행한다.

프론트엔드 구성:

- status feedback
- saved filters
- compare cards
- trend strip
- failed event table
- DLQ table
- severity badge
- two detail panels

백엔드 근거:

- `events`
- `dlq`
- `dashboard/summary`
- replay endpoint

핵심 액션:

- replay
- failed / pending / open DLQ 필터 전환

성공 기준:

- 복구 대상이 우선순위대로 읽히고, replay 후 상태 변화를 바로 검증할 수 있다.

## 8. Component Contract

### 8.1 Summary card

- Inform: 현재 수치와 상태 톤
- Act: 세부 표나 다음 섹션으로 시선을 유도
- Verify: 아래 evidence 영역에서 근거 확인

### 8.2 Recommendation card

- Inform: 왜 지금 이것이 우선순위인지
- Act: 어느 화면에서 무엇을 해야 하는지
- Verify: 이후 summary, event table, journey table에서 확인

### 8.3 Trend strip

- Inform: 최근 3개 시간 구간의 방향성
- Act: 이상 징후 발견 시 compare 또는 table 확인
- Verify: baseline과 recent rows 비교

### 8.4 Compare card

- Inform: 현재 mix와 prior 7d 대비 증감
- Act: 악화된 항목 drill-down
- Verify: table filter와 detail panel

### 8.5 Detail panel

- Inform: 선택 항목의 핵심 필드
- Act: replay나 후속 분석
- Verify: 원본 행과 API 응답

## 9. Action to Outcome Matrix

| Action | Trigger | Backend Effect | Visible Feedback | Verification Surface |
|---|---|---|---|---|
| Create lead | Contacts `leadCreateBtn` | upsert attempt + `lead_captured` | feedback message + table refresh | contact list, segments |
| Seed event | Hub/Journeys buttons | `POST /api/v1/events` | status hint update | summary, events table |
| Journey progression | Journeys action buttons | new event and state transition | hint update + stage refresh | journey cards, journey table |
| Replay DLQ | Ops replay button | `POST /api/v1/growth/dlq/{id}/replay` | feedback message | DLQ table, event table |
| Change filter | saved filter chips | client-side or endpoint refetch | active chip + changed rows | table + compare card |

## 10. P0 / P1 / P2 Priorities

### P0

- Hub summary and recommendation
- Contacts lead creation and segment visibility
- Journeys progression control
- Ops replay and failure visibility

### P1

- detail drawer or detail panel
- severity badge
- compare cards
- trend strip
- saved filters

### P2

- richer time-window selector
- historical inline charts
- saved views
- cohort compare expansion

## 11. Acceptance Criteria

### Hub

- 오늘의 운영 포인트가 항상 보인다.
- 추천 영역이 최소 한 개 이상 노출된다.
- 최근 이벤트와 여정 상태가 함께 보인다.

### Contacts

- 빠른 리드 생성이 동작한다.
- 연락처 목록과 세그먼트가 함께 보인다.
- 선택한 연락처 상세가 노출된다.

### Journeys

- 주요 progression 버튼이 동작한다.
- 단계별 카드와 표가 동시에 보인다.
- 선택한 여정 상세가 노출된다.

### Ops

- failed / pending / open DLQ를 필터링할 수 있다.
- severity가 시각적으로 구분된다.
- replay 이후 피드백이 보인다.

## 12. Validation

구현 검증은 아래 레이어를 모두 포함한다.

1. 정적 DOM 계약
2. 프론트 런타임 카피 정상화
3. 주요 integration tests
4. 가능 환경에서는 browser-session smoke

연결 테스트:

- [tests/e2e/test_growth_ui_smoke.py](/d:/Project/tests/e2e/test_growth_ui_smoke.py)
- [tests/integration/test_growth_event_gateway.py](/d:/Project/tests/integration/test_growth_event_gateway.py)
- [tests/integration/test_growth_journey_flow.py](/d:/Project/tests/integration/test_growth_journey_flow.py)

## 13. Current Implementation Link

현재 구현 기준 화면 파일:

- [web/growth-automation/index.html](/d:/Project/web/growth-automation/index.html)
- [web/growth-automation/contacts.html](/d:/Project/web/growth-automation/contacts.html)
- [web/growth-automation/journeys.html](/d:/Project/web/growth-automation/journeys.html)
- [web/growth-automation/ops.html](/d:/Project/web/growth-automation/ops.html)
- [web/growth-automation/app.js](/d:/Project/web/growth-automation/app.js)

현재 구현 결과와 병렬 작업 로그:

- [docs/GROWTH_AUTOMATION_PARALLEL_UPDATE_2026-03-07.md](/d:/Project/docs/GROWTH_AUTOMATION_PARALLEL_UPDATE_2026-03-07.md)
