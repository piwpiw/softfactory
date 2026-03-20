# Docs Overview

<!-- doc-metadata
id: docs-readme
type: documentation-redirect
owner: ops-engineering
status: active
updated: 2026-03-09
keywords: docs, overview, redirect, index
scope: documentation, navigation
-->

This file is a secondary landing page.
The canonical documentation entrypoint is [INDEX.md](INDEX.md).

## Use This Order

1. Read [INDEX.md](INDEX.md) for the active map.
2. Read [status/CURRENT.md](status/CURRENT.md) and [status/BACKLOG.md](status/BACKLOG.md) for shared project state.
3. Use [reference/active-paths.md](reference/active-paths.md) for canonical paths.
4. Use [reference/repo-layout.md](reference/repo-layout.md) for root and category rules.

## Verification

- Documentation indexing is generated into [CATALOG.json](CATALOG.json).
- Compatibility consumers may still read `docs/doc-index.json`, but new tooling should prefer `docs/CATALOG.json`.

## Change Control

- Do not add a competing "start here" document.
- Keep this file intentionally thin to avoid drift.
