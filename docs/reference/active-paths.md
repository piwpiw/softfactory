# Active Paths

<!-- doc-metadata
id: active-paths
type: path-registry
owner: ops-engineering
status: active
updated: 2026-03-10
keywords: paths, canonical, deprecated, runtime, compose
scope: repository-structure, operations
-->

This document defines which paths are canonical, which remain fixed during
phase 4 cleanup, and which are secondary or deprecated.

## Canonical Entrypoints

| Area | Canonical path | Notes |
| --- | --- | --- |
| Root runtime | `start_server.py` | API dev mode, fixed path |
| Root runtime | `start_platform.py` | Integrated demo mode, fixed path |
| Root runtime | `run.py` | Compatibility entrypoint, fixed path |
| Root docs | `README.md` | Canonical root entry |
| Docs | `docs/INDEX.md` | Canonical docs entry |
| Status | `STATUS.md` | Canonical live status |
| Catalog | `docs/CATALOG.json` | Canonical machine index |

## Fixed Paths (No Move in Phase 2)

- `backend/`
- `web/`
- `tests/`
- `scripts/`
- `agents/`
- `daemon/`
- `orchestrator/`
- `shared-intelligence/`
- `n8n/`
- `CLAUDE.md`
- `access_whitelist.json`
- `start_server.py`
- `start_platform.py`
- `run.py`

## Canonical Standards

| Topic | Canonical path | Secondary / legacy |
| --- | --- | --- |
| Compose development | `docker-compose.yml` | none |
| Compose production | `docker-compose.production.yml` | none |
| Docker image | `Dockerfile` | none |
| Production Docker image | `Dockerfile.prod` | none |
| Docs catalog | `docs/CATALOG.json` | `docs/doc-index.json` |
| Docs landing page | `docs/INDEX.md` | `docs/README.md` |

## Canonical Utility Scripts

| Utility | Canonical path | Compatibility path |
| --- | --- | --- |
| Deployment execution | `scripts/DEPLOYMENT_EXECUTION_SCRIPT.sh` | `DEPLOYMENT_EXECUTION_SCRIPT.sh` |
| Continuous improvement | `scripts/continuous_improvement.sh` | `continuous_improvement.sh` |
| Deployment verification | `scripts/deploy-verify.sh` | `deploy-verify.sh` |
| Browser page opener | `scripts/open_all_pages.bat` | `open_all_pages.bat` |
| M-002 verify (bash) | `scripts/verify_m002_phase4_setup.sh` | `verify_m002_phase4_setup.sh` |
| M-002 verify (bat) | `scripts/verify_m002_phase4_setup.bat` | `verify_m002_phase4_setup.bat` |
| Local SQLite db | `platform.db` | fixed runtime compatibility path |

## Canonical Reclassification Targets

| Class | Canonical path | Notes |
| --- | --- | --- |
| Runbooks | `docs/runbooks/` | Deployment, docker, quick-start, operational guides |
| Status docs | `docs/status/` | Curated status and validation snapshots |
| Checklists | `docs/checklists/` | Checklist-style operational docs |
| Legacy reference docs | `docs/reference/legacy-root/` | Useful reference docs kept outside current canonical set |
| Historical root docs | `docs/archive/root-legacy/` | Reports, summaries, finals, phase records |
| Wave A manifest | `docs/reference/root-reclassification-manifest-wave-a.json` | Source-to-target mapping for phase 2 Wave A |
| Wave B manifest | `docs/reference/root-reclassification-manifest-wave-b.json` | Source-to-target mapping for phase 3 Wave B |

## Local Workspace Paths

These paths are intentionally treated as local outputs or runtime artifacts.

- `.workspace/`
- `.workspace/logs/`
- `.workspace/reports/`
- `.workspace/root-artifacts/`
- `.deploy/`
- `.playwright-cli/`
- `.pytest_cache/`
- `agent_workspaces/`
- `artifacts/`
- `docs/plans/execution/`
- `htmlcov/`
- `logs/`
- `tmp_logs/`
- `node_modules/`
- `nodejs/`
- `nvm/`
- `.n8n/`

## Verification

```bash
python scripts/check-repo-layout.py
```

- Report mode is the default while legacy root files are still being reclassified.
- Strict mode is deferred until root documentation cleanup is complete.
- CI runs `python scripts/check-repo-layout.py --json` and uploads a report artifact without gating on legacy root/temp backlog.
- Local stale root temp/log outputs can be quarantined with `python scripts/quarantine-root-artifacts.py --execute`.
