# Growth Automation PRD

## Goal
운영 콘솔에 이벤트 기반 Growth Automation Hub를 추가해, 이벤트 수집부터 여정 상태전이·메시지 로깅·DLQ 재처리까지 일관된 MVP 운영 체계를 제공한다.

## North Star
주간 활성 사용자 중 `key_action_completed` 이벤트 달성률.

## KPI Tree
- Acquisition: `lead_captured` 수집량, UTM 정합률
- Activation: `signup_completed -> key_action_completed` 전환율
- Retention: 7/14/30일 재활성화율
- Revenue: `trial_to_paid` 전환율
- Ops Quality: 이벤트 중복률, DLQ open 건수, P95 처리지연

## In Scope
- 신규 페이지 `growth-automation/*`
- 이벤트 게이트웨이 `/api/v1/events`
- Growth 운영 API `/api/v1/growth/*`
- n8n 워크플로 8종(7개 캠페인 + 1개 에러핸들러)

## Out of Scope
- 외부 ESP/CRM 실계정 연동 고도화
- 실시간 개인화 모델링/ML
- 다국가 정책별 컴플라이언스 자동화

## Assumptions
- 기본 타임존 `Asia/Seoul`
- 로컬 SQLite, 운영 Postgres 호환
- 인증은 운영 API `require_auth + require_admin`
- 이벤트 수집은 `EVENT_INGEST_TOKEN` 선택 적용

## Release Strategy
1. Dark launch: API/DB만 활성화
2. Read-only UI 오픈
3. n8n 워크플로 활성화(알림 채널 우선)
4. 메시지 채널 순차 활성화
