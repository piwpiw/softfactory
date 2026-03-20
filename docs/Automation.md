# Growth Automation Workflows (n8n)

## Workflow Package
1. growth-01-lead-capture
2. growth-02-welcome-drip
3. growth-03-activation-trigger
4. growth-04-trial-to-paid
5. growth-05-reengagement
6. growth-06-churn-risk
7. growth-07-weekly-ops-report
8. growth-00-error-handler

## Interface Contract
- Pending Pull: `GET /api/v1/growth/queue/pending`
- Success Ack: `POST /api/v1/growth/queue/ack`
- Failure Ack: `POST /api/v1/growth/queue/fail`

## Required Transport Fields
- `event_id`
- `idempotency_key`
- `correlation_id`

## Error Handling
- 에러 워크플로는 실패 컨텍스트를 DLQ로 기록
- Slack/Telegram 알림은 에러 워크플로에서 처리

## Ops Rules
- 중복방지: `idempotency_key`
- 쿨다운: 동일 목적 메시지 최소 간격 보장
- 우선순위: 트랜잭션 > 온보딩 > 마케팅
