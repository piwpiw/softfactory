# Repo Layout Baseline

<!-- doc-metadata
id: repo-layout-baseline
type: status-report
owner: ops-engineering
status: active
updated: 2026-03-10
keywords: repo layout, baseline, root cleanup, structure audit
scope: repository-structure, status
-->

This report captures the repository structure baseline after the phase 4
compatibility-wrapper pass, workspace-output isolation, and Wave B root-document reclassification.

## Verification

Command used:

```bash
python scripts/check-repo-layout.py
```

Observed baseline on 2026-03-10:

- root files present: `46`
- disallowed root files present: `0`
- tracked root files: `241`
- legacy root documents present: `0`
- temp root files present: `0`
- missing link targets: `0`
- deprecated paths present: `0`
- Wave A manifest: `docs/reference/root-reclassification-manifest-wave-a.json`
- Wave B manifest: `docs/reference/root-reclassification-manifest-wave-b.json`
- Root artifact quarantine: `.workspace/root-artifacts/20260309-131554`

## Interpretation

- The repository now has a canonical docs entrypoint, a machine-readable catalog, tracked Wave A and Wave B move manifests, and a workspace quarantine path for stale root artifacts.
- The deferred root legacy backlog has been reduced to `0` live root manifest items while compatibility wrappers preserve existing command paths.
- Root temp/log clutter has been reduced to `0` live files at repository root.
- Strict enforcement can now be enabled because the deprecated compatibility alias backlog has been cleared.

## Next Safe Moves

- deprecated compatibility alias backlog is currently `0`
- keep new local runtime outputs pointed at `.workspace/`
- consider removing root wrapper scripts only after downstream docs and user habits have fully migrated to `scripts/`
