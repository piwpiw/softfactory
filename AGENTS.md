# AGENTS.md

## Purpose

This is the shared project policy for any coding agent working in this repository.

- `AGENTS.md` owns common project rules.
- `CLAUDE.md`, `GEMINI.md`, and `CODEX.md` are adapter docs only.
- If a shared doc and a model-specific doc disagree, the shared doc wins.

## Canonical Sources

Use this order when facts conflict:

1. Runtime code in `backend/`, `web/`, `scripts/`, and `tests/`
2. CI/CD and deployment config in `.github/workflows/`, `vercel.json`, `docker-compose*.yml`
3. Shared policy in `AGENTS.md`
4. Curated current state in `docs/status/CURRENT.md`
5. Prioritized open work in `docs/status/BACKLOG.md`
6. Live implementation journal in `STATUS.md`

## Documentation Roles

- `AGENTS.md`: shared operating rules for all agents
- `CLAUDE.md`, `GEMINI.md`, `CODEX.md`: tool or model adapters only
- `docs/status/CURRENT.md`: current shared status snapshot
- `docs/status/BACKLOG.md`: prioritized remaining work
- `STATUS.md`: append-only live journal and evidence log
- `docs/status/*.md`: supporting audits, queues, and detailed reports

## Working Rules

- Do not store project status, backlog ownership, or release truth in model-specific docs.
- Put shared status changes in `docs/status/CURRENT.md`, `docs/status/BACKLOG.md`, or `STATUS.md`.
- Keep model-specific docs limited to tool behavior, prompt/runtime constraints, or context-loading hints.
- Prefer updating one shared source instead of repeating the same fact in multiple files.
- Keep secrets out of docs, commits, and generated reports.
- Keep `origin` on the canonical remote URL: `https://github.com/piwpiw/softfactory.git`.
- Do not add GitHub URL rewrite rules such as `url.https://<user>@github.com/.insteadof=https://github.com/`.
- Use `scripts/vercel_release.ps1` for Vercel production deploys instead of ad hoc `vercel --prod` commands.
- Treat Vercel production state and `main` as a matched pair: deploy, verify, then commit and push the same baseline.

## History And Sync

- Git-tracked files are the audit trail.
- Notion is a derived publishing surface unless a doc explicitly says otherwise.
- If a page exists in Notion but not in Git, treat it as a copy, not the source of truth.
- If a file is untracked in Git, its history is not protected by repository history.

## Change Control

- When shared policy changes, update `AGENTS.md` and any affected adapter docs in the same change set.
- When current facts change, update `docs/status/CURRENT.md` and optionally append evidence to `STATUS.md`.
- When priorities change, update `docs/status/BACKLOG.md` and the supporting queue docs that implement it.
- When Git or Vercel auth gets repaired, document the stable path in `docs/status/CURRENT.md` so the next operator starts from the fixed baseline.
