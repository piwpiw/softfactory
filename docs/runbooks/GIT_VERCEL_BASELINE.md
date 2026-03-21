# Git And Vercel Baseline

<!-- doc-metadata
id: git-vercel-baseline
type: runbook
owner: ops-engineering
status: active
updated: 2026-03-21
keywords: git, vercel, baseline, push, deploy
scope: operations, release, source-control
-->

This runbook records the stable Git and Vercel path that was re-established on 2026-03-21.

## Baseline

- Primary branch: `main`
- Canonical remote: `https://github.com/piwpiw/softfactory.git`
- Production site: `https://softfactory-platform.vercel.app`
- Production deploy entrypoint: `powershell -ExecutionPolicy Bypass -File .\scripts\vercel_release.ps1 -Deploy`
- Baseline checkpoint commit: `fbd4487`

## Required Rules

- Do not use GitHub URL rewrite rules that inject a username into `https://github.com/`.
- Do not treat Vercel production as the source of truth. Git `main` remains the source of truth.
- Do not run raw `npx vercel --prod --yes` from the repo root for normal releases.
- Do not leave production deploys uncommitted after verification.

## Stable Git Configuration

The working Git configuration is:

```powershell
git config --global credential.helper manager
git config --global credential.useHttpPath true
git remote set-url origin https://github.com/piwpiw/softfactory.git
```

The broken pattern that must stay removed is:

```powershell
git config --global --unset-all url.https://piwpiw99@github.com/.insteadof
```

## Normal Release Sequence

1. Make the code changes.
2. Run local verification for the affected area.
3. Deploy with `scripts/vercel_release.ps1`.
4. Verify production endpoints and key pages.
5. Commit the deployed baseline.
6. Push `main` to `origin`.
7. Update `docs/status/CURRENT.md` if the shared operating state changed.

## Recovery Checks

If push fails again:

```powershell
git remote -v
git config --global --list
gh auth status
```

If Vercel deploy succeeds but Git push fails, fix Git auth first and keep the deployed state recorded in `CURRENT.md` until the matching commit is pushed.
