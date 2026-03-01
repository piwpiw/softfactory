# Orchestrator MCP Registry (Reality-Based)

This file is the single source of truth for MCP usage status in this repository.

Updated: 2026-02-28
Owner: Orchestrator

## Classification Rules

- `Used`: there is executable integration evidence in project code or automation flow.
- `Configured`: present in `.mcp.json`, `.mcp.core.json`, or `.mcp.optional.json` depending on activation profile.
- `Ready`: required environment variables are present in local `.env` (key presence only).
- `Decision`:
  - `Keep-Core`: keep in default profile.
  - `Keep-Optional`: keep, but not required for day-to-day engineering.
  - `On-Demand`: enable only for specific missions.
  - `Remove-Candidate`: no current value or no owner.

## Current Registry

| ID | Server | Configured | Ready | Used | Decision | Notes |
|----|--------|------------|-------|------|----------|-------|
| MCP-01 | filesystem | Yes | N/A | Governance-only | Keep-Core | Required for agent file operations in `D:/Project` |
| MCP-02 | sequential-thinking | No | N/A | No executable evidence | Remove-Candidate | Candidate only in historical plan; not active in any current MCP profile |
| MCP-03 | memory | No | N/A | No executable evidence | Remove-Candidate | Keep only if cross-session memory workflow is reintroduced |
| MCP-04 | sqlite | Yes | N/A | Governance-only | Keep-Core | Useful for DB inspection against `platform.db` |
| MCP-05 | github | Yes | No (`GITHUB_TOKEN` missing) | No executable evidence | On-Demand | Enabled via `.mcp.optional.json` when PR/issue automation is active |
| MCP-06 | brave-search | No | No (`BRAVE_API_KEY` missing) | No executable evidence | Remove-Candidate | Removed from active profiles and optional profile due lack of use |
| MCP-07 | google-search | Yes | No (`GOOGLE_SEARCH_*` missing) | Agent note only | On-Demand | Referenced by Market Analyst docs, enabled via `.mcp.optional.json` |
| MCP-08 | puppeteer | Yes | N/A | Governance-only | Keep-Optional | Useful for browser QA; not currently auto-wired |
| MCP-09 | fetch | Yes | N/A | Governance-only | Keep-Core | Useful for API smoke and integration checks |
| MCP-10 | postgres | Yes | Yes (`DATABASE_URL` present) | No executable evidence | On-Demand | Standby for production PostgreSQL tasks |
| MCP-11 | claude | Yes | Yes (`ANTHROPIC_API_KEY` present) | No executable MCP flow | Keep-Optional | Enabled via `.mcp.optional.json` |

## Practical Outcome

- Core profile recommendation:
  - `filesystem`, `sqlite`, `fetch`
- Optional profile recommendation:
  - `puppeteer`, `claude`, `postgres`
- Remove candidates:
  - `sequential-thinking`, `memory`, `brave-search`
- On-demand:
  - `github`, `google-search`, `postgres`

Profile files:

- `.mcp.core.json` for minimal day-to-day operations
- `.mcp.optional.json` for optional and mission-specific servers
- `.mcp.json` is the default core profile

## Evidence Sources

- Config source: `.mcp.json` / `.mcp.core.json` / `.mcp.optional.json`
- Env readiness source: local `.env` key presence (`GITHUB_TOKEN`, `BRAVE_API_KEY`, `GOOGLE_SEARCH_API_KEY`, `GOOGLE_SEARCH_CX`, `DATABASE_URL`, `ANTHROPIC_API_KEY`)
- Governance references:
  - `orchestrator/agent-registry.md`
  - `orchestrator/README.md`
  - `shared-intelligence/INFRASTRUCTURE_REPORT.md`

## Enforcement Notes

- Do not treat `Configured` as `Used`.
- Any server moved to `Keep-Core` must have:
  - a defined owner,
  - a reproducible workflow step,
  - and a documented failure mode in runbooks.
