# Actual Functionality Audit
<!-- doc-metadata
id: actual-functionality-audit
type: status-report
owner: ops-engineering
status: active
updated: 2026-03-13
keywords: actual functionality, audit, deployment, postgres, persistence
scope: product, backend, frontend
-->

Updated: 2026-03-13

## Summary

- The public deployment at `https://softfactory-platform.vercel.app` is using the real Flask API on Vercel.
- Production persistence has been moved to external PostgreSQL.
- The prior state where production effectively relied on `/tmp` SQLite is no longer the current operating state.

## Verified Public Deployment

Base URL:
- `https://softfactory-platform.vercel.app`

Verified endpoints:
- `POST /api/auth/login`
  - Result: `200`
  - Real access token and refresh token issued
- `GET /api/platform/products`
  - Result: `200`
  - Real product list returned
- `GET /api/instagram-cardnews/templates`
  - Result: `200`
- `POST /api/instagram-cardnews/templates`
  - Result: `201`
- `GET /health`
  - Result: `200`
  - Confirmed `database_backend = postgresql`

## Persistence Verification

Production persistence was verified with:
- [verify_postgres_persistence.py](/d:/Project/scripts/verify_postgres_persistence.py)

Verification method:
- create data on production
- obtain a fresh login session
- read the created data back from production
- require PostgreSQL backend explicitly

Verified data paths:
- Instagram Cardnews template persistence
- SNS Auto account persistence
- AI Automation employee persistence
- CooCook booking persistence
- Platform approval queue persistence

Result:
- passed on production with `--require-postgres`

## Cleanup Status

- Verification records created during the production check were removed from the production database after validation.
- Cleanup covered:
  - `PG Verify Template %`
  - `verify_%` SNS accounts
  - `Verifier %` AI employees
  - `verification-%` CooCook bookings
  - `verify-approval-%` approval queue items and events

## Key Files Behind the Current State

1. [api/runtime.py](/d:/Project/api/runtime.py)
   - blocks silent fallback to `/tmp` SQLite in Vercel production

2. [vercel.json](/d:/Project/vercel.json)
   - rewrites `/api/*` and health routes to the Python runtime

3. [backend/config.py](/d:/Project/backend/config.py)
   - normalizes `DATABASE_URL`
   - exposes backend type diagnostics

4. [backend/app.py](/d:/Project/backend/app.py)
   - publishes runtime health with DB backend information

5. [scripts/verify_postgres_persistence.py](/d:/Project/scripts/verify_postgres_persistence.py)
   - validates production persistence across major services

## Remaining Operational Notes

- PostgreSQL migration is complete for production runtime.
- Secrets hygiene still matters:
  - rotate the exposed Neon DB password
  - confirm Vercel production env vars stay aligned after rotation

## Conclusion

- The current production deployment is using real API execution and real PostgreSQL persistence.
- The main remaining operational follow-up is credential rotation, not storage migration.
