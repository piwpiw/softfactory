# Docs Index

<!-- doc-metadata
id: docs-index
type: documentation-index
owner: ops-engineering
status: active
updated: 2026-03-09
keywords: docs, index, repo layout, catalog, active paths
scope: documentation, operations, repository-structure
-->

`docs/INDEX.md` is the canonical documentation entrypoint for this repository.
Use this file first, then follow links into the active document set.

## Start Here

- Runtime and top-level operations: [../README.md](../README.md)
- Current status snapshot: [../STATUS.md](../STATUS.md)
- Management dashboard: [status/repo-structure-management-dashboard.md](status/repo-structure-management-dashboard.md)
- Repository path policy: [reference/repo-layout.md](reference/repo-layout.md)
- Canonical path map: [reference/active-paths.md](reference/active-paths.md)
- Team/agent doc classification: [reference/team-agent-doc-classification.md](reference/team-agent-doc-classification.md)
- Machine-readable catalog: [CATALOG.json](CATALOG.json)

## Core Documents

- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Projects: [PROJECTS.md](PROJECTS.md)
- Team map: [TEAM.md](TEAM.md)
- Decisions: [DECISIONS.md](DECISIONS.md)
- Rules: [RULES.md](RULES.md)
- Quickstart: [SOFTFACTORY_QUICKSTART.md](SOFTFACTORY_QUICKSTART.md)
- Troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Structure Axes

- Product code: `backend/`, `web/`, `tests/`, `api/`
- Automation runtime: `agents/`, `daemon/`, `orchestrator/`, `shared-intelligence/`, `n8n/`
- Operations: `scripts/`, `monitoring/`, `nginx/`, `infrastructure/`, `.github/`
- Documentation: `docs/`
- Local workspace outputs: `.deploy/`, `artifacts/`, `logs/`, `tmp_logs/`, `htmlcov/`, `.pytest_cache/`, `.playwright-cli/`, `agent_workspaces/`, `node_modules/`, `nodejs/`, `nvm/`

## Active Documentation Zones

- Reference and policy: [reference/](reference/)
- Management and status: [status/README.md](status/README.md)
- Legacy reference landing zone: [reference/legacy-root/README.md](reference/legacy-root/README.md)
- Root reclassification manifest: [reference/root-reclassification-manifest-wave-a.json](reference/root-reclassification-manifest-wave-a.json)
- Wave B reclassification manifest: [reference/root-reclassification-manifest-wave-b.json](reference/root-reclassification-manifest-wave-b.json)
- Status landing zone: [status/README.md](status/README.md)
- Runbook landing zone: [runbooks/README.md](runbooks/README.md)
- Checklist landing zone: [checklists/README.md](checklists/README.md)
- Active plans landing zone: [plans/active/README.md](plans/active/README.md)
- Root legacy archive landing zone: [archive/root-legacy/README.md](archive/root-legacy/README.md)

## Verification

```bash
python scripts/check-repo-layout.py
powershell -ExecutionPolicy Bypass -File scripts/refresh-doc-index.ps1
```

- `scripts/check-repo-layout.py --strict` is reserved for enforcement after legacy root documents are reclassified.
- `scripts/refresh-doc-index.ps1` regenerates both `docs/CATALOG.json` and the compatibility file `docs/doc-index.json`.
- CI uploads a report-only layout artifact from `python scripts/check-repo-layout.py --json` on each workflow run.

## Change Control

- New start pages should not be added outside `README.md` and `docs/INDEX.md`.
- New canonical documentation should live under `docs/`, not at repository root.
- Validation and verification changes should update the catalog before merge.
