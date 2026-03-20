# Growth Automation Event Spec

## Ingest Endpoint
- `POST /api/v1/events`

## Required Fields
- `event_name`

## Optional Fields
- `event_id` (없으면 서버 생성)
- `ts`
- `identity.contact_id|email|phone|anonymous_id`
- `context`
- `props`
- `idempotency_key`

## Standard Names
- `lead_captured`
- `signup_completed`
- `key_action_completed`
- `trial_expiring`
- `payment_failed`
- `reengagement_eligible`
- `churn_risk_detected`

## Response
- `{ accepted, duplicate, event_id, idempotency_key }`

## Security
- `EVENT_INGEST_TOKEN` 존재 시 `X-Event-Token` 또는 Bearer 필요
