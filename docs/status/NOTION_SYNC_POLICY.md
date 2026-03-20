# Notion Sync Policy

<!-- doc-metadata
id: notion-sync-policy
type: status-sync-policy
owner: ops-engineering
status: active
updated: 2026-03-20
keywords: notion, git, sync, history, policy
scope: documentation, operations, knowledge-management
-->

This project uses Git as the authoritative record and Notion as an optional derived publishing surface.

## Source Of Truth

- Git-tracked repository files are the audit trail.
- Notion pages are mirrors, summaries, or operational views.
- If Git and Notion disagree, Git wins unless an explicit document says otherwise.

## History Rule

- Git preserves file history for tracked files.
- Untracked files have no repository history and can disappear without an audit trail.
- Notion page history is not a replacement for repository history.

## Current Local Reality

As of 2026-03-20 in this workspace:

- `.env.n8n` is not present locally.
- Root `.env` does not define `NOTION_API_KEY` or `NOTION_DATABASE_ID`.
- Local `.n8n/database.sqlite` contains no configured credentials and no execution history.
- The repo contains Notion workflow templates, but there is no local evidence that Notion sync is active right now.

## Publish Rule

Publish to Notion only after:

1. The source file has a stable Git path.
2. The content is already accurate in Git.
3. The page is clearly marked as a mirror or derived summary if it is not the primary record.

## Reactivation Checklist

To reactivate automated Notion publishing safely:

1. Create `.env.n8n` from `n8n/environment-template.env`.
2. Set valid `NOTION_API_KEY` and `NOTION_DATABASE_ID`.
3. Import or activate the required n8n workflows.
4. Add the matching n8n credentials and verify a test page creation.
5. Record the successful sync date in Git-tracked documentation.

## Practical Decision

- Keep Git as the permanent system of record.
- Use Notion when a shared workspace view is useful for non-engineering stakeholders.
- Do not rely on Notion as the only copy of status, backlog, or decision history.
