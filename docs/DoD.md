# Growth Automation Definition of Done

## Functional
- [ ] `/api/v1/events` 유효성/중복 처리
- [ ] `/api/v1/growth/contacts|events|journeys|dlq` 조회 가능
- [ ] `/api/v1/growth/contacts/upsert` 동작
- [ ] `/api/v1/growth/queue/pending|ack|fail` 토큰 인증 동작
- [ ] 신규 페이지 4종에서 API 연동 가능

## Reliability
- [ ] 중복 이벤트 재수신 시 duplicate 응답
- [ ] 실패 이벤트 DLQ 적재
- [ ] DLQ replay 시 상태 복원

## Security
- [ ] 운영 API admin 보호
- [ ] queue API 토큰 검증
- [ ] ingest 토큰 옵션 검증

## Observability
- [ ] dashboard summary에 핵심 지표 노출
- [ ] ops 페이지에서 DLQ 및 처리상태 확인 가능
