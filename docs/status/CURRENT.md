# Current Project State

<!-- doc-metadata
id: current-project-state
type: status-current
owner: ops-engineering
status: active
updated: 2026-03-20
keywords: current state, source of truth, deployment, backlog
scope: documentation, status, operations
-->

This is the curated shared current-state document for agents and humans.

## Canonical Inputs

- Live journal: [../../STATUS.md](../../STATUS.md)
- Production status snapshot: [TEAM_WORK_STATUS.md](TEAM_WORK_STATUS.md)
- Production audit: [actual-functionality-audit.md](actual-functionality-audit.md)
- Short-term execution queue: [execution-queue-followups.md](execution-queue-followups.md)
- Long-running backlog: [long-running-followups.md](long-running-followups.md)

## Summary

- Public production URL: `https://softfactory-platform.vercel.app`
- Production frontend and Flask API are live on Vercel.
- Production persistence is on external PostgreSQL, not ephemeral `/tmp` SQLite.
- Core auth and key business APIs are reachable in production.

## Verified Current State

- Production `GET /health` returns `200` and reports PostgreSQL as the active backend.
- Production persistence has been re-verified across major services.
- The main production operational follow-up is credential rotation, not storage migration.
- Local `verify_integration --suite core` has recent passing evidence.
- Container-based local verification is still blocked by the local Docker daemon state.

## Immediate Follow-Ups

- Rotate the exposed Neon DB password and confirm the aligned Vercel production environment variables.
- Restore local Docker daemon access and rerun `api + postgres + redis` container health checks.
- Stabilize long-lived local server execution for browser sessions, or use deployment-based Playwright evidence as the primary UI proof path.
- Finish the remaining page-level cleanup work called out in the execution queue, especially the CooCook and platform UI polish items.

## Source Of Truth Rule

- Use this file for the current shared snapshot.
- Use `STATUS.md` for detailed dated evidence and implementation notes.
- Use `BACKLOG.md` for remaining work and queue grouping.
- Do not put shared current-state facts in `CLAUDE.md`, `GEMINI.md`, or `CODEX.md`.
