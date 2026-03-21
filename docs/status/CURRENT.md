# Current Project State

<!-- doc-metadata
id: current-project-state
type: status-current
owner: ops-engineering
status: active
updated: 2026-03-21
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
- Git `main`, `origin/main`, and the current Vercel production baseline were re-aligned on `2026-03-21`.
- Baseline checkpoint commit: `fbd4487`

## Verified Current State

- Production `GET /health` returns `200` and reports PostgreSQL as the active backend.
- Production `GET /api/health` returns `200`.
- Production `GET /api/ping` returns `200` through the Python Vercel runtime.
- Production persistence has been re-verified across major services.
- The main production operational follow-up is credential rotation, not storage migration.
- Local `verify_integration --suite core` has recent passing evidence.
- Container-based local verification is still blocked by the local Docker daemon state.
- Git remote and deploy path were normalized to the shared baseline documented in [../runbooks/GIT_VERCEL_BASELINE.md](../runbooks/GIT_VERCEL_BASELINE.md).

## Immediate Follow-Ups

- Rotate the exposed Neon DB password and confirm the aligned Vercel production environment variables.
- Restore local Docker daemon access and rerun `api + postgres + redis` container health checks.
- Stabilize long-lived local server execution for browser sessions, or use deployment-based Playwright evidence as the primary UI proof path.
- Finish the remaining page-level cleanup work called out in the execution queue, especially the CooCook and platform UI polish items.

## Source Of Truth Rule

- Use this file for the current shared snapshot.
- Use `STATUS.md` for detailed dated evidence and implementation notes.
- Use `BACKLOG.md` for remaining work and queue grouping.
- Use [../runbooks/GIT_VERCEL_BASELINE.md](../runbooks/GIT_VERCEL_BASELINE.md) for the stable Git and Vercel operational path.
- Do not put shared current-state facts in `CLAUDE.md`, `GEMINI.md`, or `CODEX.md`.
