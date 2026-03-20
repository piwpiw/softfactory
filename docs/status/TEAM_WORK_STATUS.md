# Team Work Status
<!-- doc-metadata
id: team-work-status
type: status-report
owner: ops-engineering
status: active
updated: 2026-03-13
keywords: implementation status, deployment status, postgres, vercel
scope: backend, frontend, deployment, qa
-->

## Summary

- Public production URL: `https://softfactory-platform.vercel.app`
- Public deployment now runs as `static frontend + Vercel Python Flask API`.
- Production database is now external PostgreSQL, not `/tmp` SQLite.
- Core auth and business APIs are live on the public deployment.

## Current Status

| Area | Status | Notes |
| --- | --- | --- |
| Public frontend | complete | Public pages deployed and reachable |
| Public API routing | complete | `/api/*` served by Vercel Python runtime |
| Authentication flow | complete | Login issues resolved on live deployment |
| PostgreSQL migration | complete | `DATABASE_URL` configured in Vercel production |
| Persistence verification | complete | Create -> re-login -> read verified on production |
| Root/link audit | complete | Prior deployed link checks passed |

## Key Implementation Files

- Vercel runtime
  - [api/runtime.py](/d:/Project/api/runtime.py)
  - [vercel.json](/d:/Project/vercel.json)
- Runtime filesystem support
  - [backend/runtime_paths.py](/d:/Project/backend/runtime_paths.py)
  - [backend/caching_config.py](/d:/Project/backend/caching_config.py)
- Runtime DB diagnostics
  - [backend/config.py](/d:/Project/backend/config.py)
  - [backend/app.py](/d:/Project/backend/app.py)
- Real service paths
  - [backend/services/instagram_cardnews.py](/d:/Project/backend/services/instagram_cardnews.py)
  - [web/platform/api.js](/d:/Project/web/platform/api.js)
- Verification
  - [scripts/verify_postgres_persistence.py](/d:/Project/scripts/verify_postgres_persistence.py)

## Latest Verification

- Production health check:
  - `GET /health`
  - Result: `200 OK`
  - Confirmed: `"database_backend": "postgresql"`

- Production persistence verification:
  - Script: [verify_postgres_persistence.py](/d:/Project/scripts/verify_postgres_persistence.py)
  - Result: passed with `--require-postgres`
  - Verified services:
    - Instagram Cardnews template
    - SNS Auto account
    - AI Automation employee
    - CooCook booking
    - Approval queue item

- Cleanup:
  - Production verification records created during validation were removed after the check.

## Important Reality

- The public API is live and backed by PostgreSQL in production.
- Production no longer depends on ephemeral Vercel `/tmp` SQLite for core persistence.
- Neon credentials were exposed in chat during setup, so DB password rotation is still recommended.

## Related Documents

- [actual-functionality-audit.md](/d:/Project/docs/status/actual-functionality-audit.md)
- [repo-structure-management-dashboard.md](/d:/Project/docs/status/repo-structure-management-dashboard.md)
