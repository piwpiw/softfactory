# Orchestrator — MCP Server Registry
> **Rule:** All external connections via MCP only. No ad-hoc API calls, no direct DB access, no undeclared dependencies.
> **Governance Principle #3**
> **Maintained by:** 01-Dispatcher (Orchestrator)
> **Last updated:** 2026-02-25

---

## Registry

| ID | Server | Transport | Status | Capabilities | Auth |
|----|--------|-----------|--------|--------------|------|
| MCP-01 | filesystem | stdio | ✅ ACTIVE | File R/W within project root | None (scoped path) |
| MCP-02 | sequential-thinking | stdio | ✅ ACTIVE | Structured reasoning chains | None |
| MCP-03 | memory | stdio | ✅ ACTIVE | Cross-session key-value memory | None |
| MCP-04 | sqlite | stdio | ✅ ACTIVE | Direct SQL queries on platform.db | None (local file) |
| MCP-05 | github | stdio | ✅ ACTIVE | PR, issues, code management | GITHUB_TOKEN (env) |
| MCP-06 | brave-search | stdio | ✅ ACTIVE | Web search for market research | BRAVE_API_KEY (env) |
| MCP-07 | google-search | stdio | ✅ ACTIVE | Google search (backup) | GOOGLE_API_KEY (env) |
| MCP-08 | puppeteer | stdio | ✅ ACTIVE | Browser automation, E2E testing | None |
| MCP-09 | fetch | stdio | ✅ ACTIVE | HTTP requests, API testing | None |
| MCP-10 | postgres | stdio | ⚠️ STANDBY | PostgreSQL production DB | DATABASE_URL (env) |

---

## Server Details

### MCP-01: filesystem
```
transport: stdio
scope: D:/Project/** (read + write)
purpose: Agent file access within project
restrictions: Cannot access outside project root
config: .mcp.json → "filesystem"
```

### MCP-02: sequential-thinking
```
transport: stdio
scope: reasoning only (no side effects)
purpose: Structured multi-step reasoning for complex decisions
config: .mcp.json → "sequential-thinking"
```

### MCP-03: memory
```
transport: stdio
scope: key-value store (persistent across sessions)
purpose: Cross-session agent state retention
note: Use shared-intelligence/ for human-readable memory; use this for machine state
config: .mcp.json → "memory"
```

### MCP-04: sqlite
```
transport: stdio
target: D:/Project/platform.db
purpose: Direct SQL queries for debugging/reporting without Flask app
restriction: READ-ONLY in production sessions; writes only via Flask app
config: .mcp.json → "sqlite"
```

### MCP-05: github
```
transport: stdio
scope: Repository: piwpiw/Project (or equivalent)
purpose: PR creation, issue management, code review automation
auth: GITHUB_TOKEN in .env (never committed)
config: .mcp.json → "github"
```

### MCP-06: brave-search
```
transport: stdio
purpose: Market research, competitor analysis, technical documentation lookup
quota: Review monthly API usage in Brave dashboard
auth: BRAVE_API_KEY in .env
config: .mcp.json → "brave-search"
```

### MCP-07: google-search
```
transport: stdio
purpose: Backup search when Brave unavailable; Google-specific results
auth: GOOGLE_API_KEY + GOOGLE_CSE_ID in .env
config: .mcp.json → "google-search"
```

### MCP-08: puppeteer
```
transport: stdio
purpose: E2E testing, browser automation, screenshot capture, form testing
note: Used by 07-QA agent for SoftFactory UI testing
config: .mcp.json → "puppeteer"
```

### MCP-09: fetch
```
transport: stdio
purpose: HTTP requests for API testing, webhook simulation, external API calls
note: Used for 16/16 API endpoint testing (2026-02-24)
config: .mcp.json → "fetch"
```

### MCP-10: postgres
```
transport: stdio
status: STANDBY — activated when PostgreSQL production DB available
purpose: Production database access (replaces SQLite at scale)
auth: DATABASE_URL in .env (format: postgresql://user:pass@host/db)
activation: Triggered when SQLite → PostgreSQL migration executed (ADR-0003)
config: .mcp.json → "postgres"
```

---

## Adding a New MCP Server

**Process (Principle #3):**
1. Review `modelcontextprotocol.io` spec for the server
2. Check `docs/generated/adr/` for any prior decision
3. Add entry to this registry with full details
4. Update `.mcp.json` with server config
5. Create ADR entry in `shared-intelligence/decisions.md`
6. Test connection before first agent use

**Required fields for new entry:** ID, transport, status, capabilities, auth method, restrictions
