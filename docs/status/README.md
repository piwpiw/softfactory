# Status Docs

<!-- doc-metadata
id: status-docs-landing
type: status-landing
owner: ops-engineering
status: active
updated: 2026-03-10
keywords: status, reports, health, current state
scope: documentation, status
-->

Use this directory for tracked status reports that belong under `docs/`.

## Canonical Status Sources

- Current shared snapshot: [CURRENT.md](CURRENT.md)
- Prioritized backlog: [BACKLOG.md](BACKLOG.md)
- Live root status journal: [../../STATUS.md](../../STATUS.md)
- Notion sync policy: [NOTION_SYNC_POLICY.md](NOTION_SYNC_POLICY.md)
- Docs entrypoint: [../INDEX.md](../INDEX.md)
- Management dashboard: [repo-structure-management-dashboard.md](repo-structure-management-dashboard.md)
- Structure baseline: [repo-layout-baseline.md](repo-layout-baseline.md)
- Long-running follow-ups: [long-running-followups.md](long-running-followups.md)
- Execution queue: [execution-queue-followups.md](execution-queue-followups.md)
- Overnight screen queue: [overnight-screen-work-queue.md](overnight-screen-work-queue.md)
- Actual functionality audit: [actual-functionality-audit.md](actual-functionality-audit.md)

## Intended Use

- place curated status summaries here
- keep `CURRENT.md` as the shared snapshot and `BACKLOG.md` as the shared queue summary
- keep root `STATUS.md` as the live detailed journal instead of the only current-state entrypoint
- avoid creating new root status markdown files
- use the management dashboard for quick repository structure briefings
- use the long-running follow-up backlog for tasks that should be deferred to later or parallel execution
- use the execution queue when the deferred backlog needs to be scheduled into concrete next actions
- use the overnight screen queue when the priority is fast UI inspection and page-quality work
- use the actual functionality audit when the question is whether pages really save, reload, and produce fact-based results
- treat Notion as a derived mirror, not the canonical record
