# Repo Layout Policy

<!-- doc-metadata
id: repo-layout-policy
type: repository-policy
owner: ops-engineering
status: active
updated: 2026-03-10
keywords: repo layout, root policy, documentation, workspace, validation
scope: repository-structure, governance
-->

This policy defines the repository layout rules for the no-side-effect cleanup path.
Phase 1 established indexing and policy. Phase 2 reclassified low-risk root documents.
Phase 3 keeps runtime paths fixed while isolating local temp/log outputs into `.workspace/`.
Phase 4 continues exception reduction by moving remaining low-risk root docs and redirecting generated outputs away from root.

## Root Rules

- Repository root is for entrypoints, manifests, and top-level product folders only.
- New reports, checklists, summaries, logs, and generated artifacts must not be added at root.
- New documentation should be created under `docs/`.
- New runtime outputs should be created under local workspace paths, not tracked at root.
- Local runtime logs should default to `.workspace/logs/` unless an external platform overrides `LOG_FILE`.
- Generated local reports should default to `.workspace/reports/` unless they are intentionally committed as canonical docs.
- Root compatibility wrappers are allowed only when the canonical implementation lives under `scripts/` and the wrapper is a pure passthrough.
- `platform.db` remains a fixed local runtime exception until the SQLite development path is retired.

## Logical Structure

| Axis | Canonical paths |
| --- | --- |
| Product | `backend/`, `web/`, `tests/`, `api/` |
| Automation | `agents/`, `daemon/`, `orchestrator/`, `shared-intelligence/`, `n8n/` |
| Operations | `scripts/`, `monitoring/`, `nginx/`, `infrastructure/`, `.github/` |
| Documentation | `docs/` |
| Local workspace | `.workspace/`, `.workspace/logs/`, `.workspace/reports/`, `.deploy/`, `artifacts/`, `logs/`, `tmp_logs/`, `htmlcov/`, `.pytest_cache/`, `.playwright-cli/`, `agent_workspaces/`, `node_modules/`, `nodejs/`, `nvm/` |

## Safety Zones

- Red: fixed paths with high reference density, no move in phase 1
- Amber: logical reclassification only, no direct path rename
- Green: generated outputs and local artifacts that can be isolated immediately

## Documentation Rules

- `README.md` and `docs/INDEX.md` are the only top-level start pages.
- `docs/CATALOG.json` is the canonical machine-readable catalog.
- `docs/doc-index.json` remains a compatibility alias during the transition.
- Root legacy document reclassification targets are:
  - `docs/runbooks/`
  - `docs/status/`
  - `docs/checklists/`
  - `docs/reference/legacy-root/`
  - `docs/archive/root-legacy/`
- `docs/reference/root-reclassification-manifest-wave-a.json` and `docs/reference/root-reclassification-manifest-wave-b.json` are the tracked move manifests for the executed cleanup waves.
- `docs/plans/active/` is the intended home for tracked active plans.
- `docs/plans/execution/` is treated as local execution output, not canonical docs.
- Stale root temp/log artifacts should be quarantined into `.workspace/root-artifacts/` via `scripts/quarantine-root-artifacts.py`.

## Compose and Runtime Rules

- Keep `docker-compose.yml` and `docker-compose.production.yml` as the official compose files.
- Keep `start_server.py`, `start_platform.py`, and `run.py` unchanged in phase 1.
- Keep root wrapper scripts minimal and route them to the canonical `scripts/` path.

## Verification

```bash
python scripts/check-repo-layout.py
python scripts/check-repo-layout.py --strict
powershell -ExecutionPolicy Bypass -File scripts/refresh-doc-index.ps1
```

- Report mode is required before any structural cleanup.
- Strict mode should only be enabled after root legacy files are reclassified.
- CI uses report-only layout audit output (`python scripts/check-repo-layout.py --json`) and uploads it as an artifact.
