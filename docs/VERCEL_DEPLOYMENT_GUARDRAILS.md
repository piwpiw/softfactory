# Vercel Deployment Guardrails

Updated: 2026-03-06

## Purpose

Prevent repeat failures during Vercel deployment by enforcing a deterministic production deploy path for this repository.

## Root Causes Observed

1. Invalid or stale Vercel authentication caused production deploy to fail after the deploy command had already started.
2. Windows and WSL path conventions were mixed during fallback deploy attempts, so the fallback script path was not executable.
3. Packaging the whole repository pulled in locked or non-deployable directories such as `n8n-comfy/data/postgres`, which caused archive creation to fail.
4. Preview or production URLs were opened before the deployment had fully propagated, causing transient `404` responses that looked like deploy failures.

## Required Production Path

Use the repository script instead of running raw `vercel --prod` from the repo root.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\vercel_release.ps1 -Deploy
```

Use this when the frontend payload changed but the fingerprint has not:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\vercel_release.ps1 -Deploy -ForceDeploy
```

## What The Script Enforces

- Local static smoke check for key pages before deploy.
- Vercel authentication preflight with a clear failure message.
- Minimal deployment staging containing only:
  - `web/`
  - `api/proxy.js`
  - `api/_health.js`
  - `vercel.json`
  - `.vercel/project.json`
- Production deployment from the staged payload, not from the full repository.
- Remote verification with retries so propagation delay does not look like a broken deploy.

## Hard Rules

1. Do not deploy from repository root with `npx vercel --prod --yes` unless you are explicitly debugging the deploy mechanism itself.
2. Do not use WSL fallback scripts for normal production release on this Windows workspace.
3. Do not open the deployed URL until the remote verification loop has passed.
4. Keep `.vercelignore` aligned with repository growth so new heavy or locked directories never enter the Vercel payload.

## Preflight Checklist

1. `npx vercel whoami` succeeds.
2. `.vercel/project.json` exists and points to the intended Vercel project.
3. `vercel.json`, `api/proxy.js`, and `api/_health.js` exist.
4. `API_UPSTREAM_URL` or `VERCEL_API_UPSTREAM_URL` is configured in Vercel for production API routing.
5. `powershell -ExecutionPolicy Bypass -File .\scripts\vercel_release.ps1` passes local smoke checks before running with `-Deploy`.

## Failure Handling

### Auth Failure

Symptom:
- `The specified token is not valid`
- `No existing credentials found`

Action:

```powershell
npx vercel login
npx vercel whoami
powershell -ExecutionPolicy Bypass -File .\scripts\vercel_release.ps1 -Deploy
```

### Locked File Or Archive Failure

Symptom:
- `tar: ... Cannot open: Permission denied`

Action:
- Do not retry with raw root packaging.
- Re-run the guarded script. It deploys from `.deploy/vercel-stage` and excludes locked runtime directories.

### Remote 404 Immediately After Deploy

Symptom:
- Deployment URL exists but the first request returns `404`.

Action:
- Treat this as propagation until the guarded remote verification loop finishes.
- Only treat it as a real failure if the verification loop exhausts all retries.

## Related Files

- `scripts/vercel_release.ps1`
- `.vercelignore`
- `vercel.json`
- `README.md`
- `runbooks/DEPLOYMENT-QUICK-START.md`
