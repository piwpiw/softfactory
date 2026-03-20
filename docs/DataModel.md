# Growth Automation Data Model

## Core Tables
- `marketing_contacts`
- `marketing_consents`
- `marketing_events`
- `marketing_journey_states`
- `marketing_message_logs`
- `marketing_dlq`

## Identity Rule
- 외부 참조용 ID: `contact_uid` (UUID 문자열)
- 내부 FK: 정수 `id`

## Event Rule
- `event_id` unique
- `idempotency_key` unique
- `processing_status`: `pending|processed|failed`

## Journey Rule
- unique(`contact_id`,`journey_id`)
- 상태 전이는 워크플로/운영API에서만 갱신

## Message Rule
- 발송 결과는 반드시 `marketing_message_logs`에 적재

## DLQ Rule
- 워크플로 실패는 `marketing_dlq` 적재
- replay 시 `resolved` 전환 + 원 이벤트 `pending` 복원
