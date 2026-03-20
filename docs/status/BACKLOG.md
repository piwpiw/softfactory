# Prioritized Backlog

<!-- doc-metadata
id: prioritized-backlog
type: status-backlog-summary
owner: ops-engineering
status: active
updated: 2026-03-20
keywords: backlog, priorities, remaining work
scope: documentation, status, operations, qa
-->

This is the shared backlog summary for active work that remains after the current verified baseline.

## P0 Operational Follow-Ups

- Restore the local Docker daemon and rerun container-based verification for `api + postgres + redis`.
- Recheck container `GET /health` and `GET /api/health` plus key static pages after Docker recovery.
- Rotate the exposed production Neon credentials and verify Vercel environment alignment after rotation.
- Resolve long-lived local detached server instability for browser automation sessions.

## P1 Product And UX Follow-Ups

- Finish the remaining CooCook top-copy and page polish tasks still called out in `STATUS.md`.
- Work through the short-term page queue in [execution-queue-followups.md](execution-queue-followups.md).
- Continue the overnight UI cleanup items in [overnight-screen-work-queue.md](overnight-screen-work-queue.md).

## P2 Long-Running Follow-Ups

- Real SNS account-link verification across external platforms
- Multi-channel publish result capture and verification
- Real `n8n` webhook integration from `sns-auto/create.html`
- Auth-included browser smoke automation
- Large-scale CooCook combination and performance benchmarking
- Service-to-service AI contract cleanup across `ai-automation`, `sns-auto`, and `instagram-cardnews`

## Queue Map

- Short-term execution queue: [execution-queue-followups.md](execution-queue-followups.md)
- Long-running follow-ups: [long-running-followups.md](long-running-followups.md)
- UI inspection queue: [overnight-screen-work-queue.md](overnight-screen-work-queue.md)
- Live evidence journal: [../../STATUS.md](../../STATUS.md)

## Update Rule

- Update this file when priority or ownership changes.
- Keep supporting queue docs more detailed than this file.
- Do not use model-specific adapter docs as backlog containers.
