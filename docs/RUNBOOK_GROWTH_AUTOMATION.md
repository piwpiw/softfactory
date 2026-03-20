# Growth Automation Runbook

## Health Checks
- API: `GET /api/v1/growth/dashboard/summary`
- Queue Pull: `GET /api/v1/growth/queue/pending?limit=1`

## Incident Triage
1. `processing_status=failed` 이벤트 수 확인
2. `marketing_dlq.status=open` 증가 여부 확인
3. 최근 워크플로 실행 ID와 에러 step 확인

## Replay Procedure
1. 대상 DLQ ID 확인
2. `POST /api/v1/growth/dlq/{id}/replay`
3. 이벤트가 `pending`으로 복원되었는지 확인

## Alert Thresholds
- `error_rate > 5%`
- `duplicate_rate > 3%`
- `p95_latency > 2s`
- `dlq_open_count > 20`

## Rollback
- `GROWTH_AUTOMATION_ENABLED=false`
- n8n growth 워크플로 비활성화
- 신규 UI는 read-only 공지
