# Project D Memory — 2026-03-17
> **STATUS:** Memory system v3.1 complete | governance synced | all memory layers active

## Quick Reference (Tag Index)

| Tag | File | Purpose |
|-----|------|---------|
| `#phase` | `orchestrator/phase-structure-v4.md` | Current phase (-1 to 7), active agents |
| `#errors` | `shared-intelligence/pitfalls.md` | Known pitfalls PF-001+ with prevention |
| `#constraints` | `CLAUDE.md §10` | Quality gates, prohibited actions |
| `#decisions` | `shared-intelligence/decisions.md` | ADR-0001+ architectural decisions |
| `#patterns` | `shared-intelligence/patterns.md` | Reusable solutions PAT-001+ |
| `#cost` | `shared-intelligence/cost-log.md` | Token usage, budget status |
| `#handoff` | `shared-intelligence/handoffs/` | Structured handoff records |
| `#pitfalls` | `shared-intelligence/pitfalls.md` | Failure registry PF-001+ |

---

## Active Projects (M-003, M-004, M-005)

| ID | Name | Status | Stack | Target |
|----|------|--------|-------|--------|
| M-001 | Infrastructure | COMPLETE | Python agents | Done |
| M-002 | CooCook | 35% IN_PROGRESS | FastAPI+Next.js+PG | 2026-04-15 |
| M-003 | SoftFactory | RUNNING | Flask+SQLite | localhost:8000 |
| M-004 | JARVIS Bot | ACTIVE | Railway | Ongoing |
| M-005 | Sonolbot | ACTIVE | Python daemon | Running |

**SoftFactory (M-003) — Phase 1 Complete:**
- 366 API routes registered, 95%+ working
- Test data: 3 products, 1 subscription, 1 SNS account
- URL: http://localhost:8000 | Auth: JWT (test@example.com / Test123456!)
- DB: SQLite at D:/Project/platform.db

**JARVIS Bot (M-004):**
- Status: Telegram integration active
- Deployment: Railway platform
- Commands: /task-new, /task-activate, /task-list

**Sonolbot (M-005):**
- Location: D:/Project/daemon/ | venv: daemon/.venv/
- Start: `pythonw.exe daemon_control_panel.py`
- Bot ID: 8461725251 | Allowed user: 7910169750

---

## Governance v3.1 (2026-03-02)

**Framework Status:** ACTIVE (CLAUDE.md §0-§12)

**What's Included:**
- Policy root: `CLAUDE.md` (≤500 lines, status: ACTIVE)
- Implementation layer: `.agent/` (5 files)
  - `AGENT_SYSTEM.md` — Agent lifecycle, T↔PA mapping
  - `CONTEXT_ENGINE.md` — Context rules, tag definitions
  - `AGENT_PROTOCOLS.md` — Handoff format, escalation, RACI
  - `COST_RULES.md` — Token budget, model costs
  - `workflows/context-sync.md` — Policy sync procedure
- Governance runtime: `orchestrator/` (4 files + agent-registry)
- Shared intelligence: `shared-intelligence/` (patterns, decisions, pitfalls, cost-log, handoffs, checkpoints)

**15-Principle Framework (CLAUDE.md §12):**
1. Scope-First | 2. Function-Scope | 3. Evidence-Based | 4. Context-Minimal | 5. Batch-Efficient
6. Handoff-Complete | 7. Memory-Hierarchical | 8. Rollback-Safe | 9. Cost-Conscious | 10. Team-Routed
11. Escalation-Structured | 12. Quality-Gated | 13. Error-Documented | 14. Pattern-Shared | 15. Verification-Explicit

---

## Memory System (5 Layers)

**L1 Session:** Working memory (real-time)
**L2 Persistent:** `memory/MEMORY.md` (≤200 lines, updated session-end)
**L3 Shared:** `shared-intelligence/*.md` (patterns, decisions, pitfalls, cost-log)
**L4 Governance:** `.agent/*.md` + `orchestrator/*.md` (updated on policy change)
**L5 Archive:** `shared-intelligence/archive/` (monthly rotation)

**Memory Files Index:**
- **Core:** This file (MEMORY.md) — central index
- **Projects:** M002_PHASE4_SETUP_COMPLETE.md | M006_TEAM_H_API_JS_EXPANSION.md | TEAM_H_HANDOFF_T09.md
- **Shared Intelligence:** patterns.md, decisions.md, pitfalls.md, cost-log.md, handoffs/, checkpoints/
- **Governance:** CLAUDE.md, .agent/CONTEXT_ENGINE.md, .agent/AGENT_SYSTEM.md, .agent/AGENT_PROTOCOLS.md, .agent/COST_RULES.md

---

## Critical Tech Notes

**SoftFactory Architecture:**
```
start_platform.py → backend/app.py (port 8000)
backend/models.py (12 models) | backend/auth.py (JWT)
backend/services/ (5 services) | web/ (75 HTML pages)
```

**Tech Stack by Project:**
- **M-002 CooCook:** FastAPI + Next.js + PostgreSQL (prod)
- **M-003 SoftFactory:** Flask + SQLite (dev)
- **Backend:** Python monolith (Flask/FastAPI), SQLite → PostgreSQL
- **Frontend:** Vanilla JS / HTML / CSS (web/)
- **CI/CD:** GitHub Actions / Vercel / Docker
- **Agents:** Python (agents/01_dispatcher ~ 10_telegram_reporter)
- **Skills:** Python (skills/agile, api-first, ddd, tdd, owasp, etc.)
- **MCP Core:** filesystem, sqlite, fetch (see orchestrator/mcp-registry.md)

**Key Decisions (→ shared-intelligence/decisions.md):**
- ADR-0001: Clean Architecture + Modular Monolith (CooCook)
- ADR-0002: FastAPI for CooCook, Flask for SoftFactory
- ADR-0003: SQLite (dev) → PostgreSQL (prod)
- ADR-0004: Additive governance (no restructuring)
- ADR-0005: Markdown-first shared intelligence
- ADR-0016: AI cost optimization via Gemini blend

---

## Known Pitfalls (→ shared-intelligence/pitfalls.md)

- **PF-001:** Python decorators run bottom-to-top — @require_auth MUST be bottom
- **PF-002:** SQLite relative path creates duplicate DB — use absolute path
- **PF-003:** Demo token must be static string (no timestamp suffix)
- **PF-004:** Every SQLAlchemy model needs `to_dict()` or JSON 500 errors
- **PF-005:** Sonolbot fails silently if `.venv/Scripts/pythonw.exe` missing
- **PF-006:** MEMORY.md truncated at 200 lines — use topic files for details
- **PF-007:** Never append activity logs to CLAUDE.md — use handoffs/ instead

---

## Node.js + Claude Code CLI

| Item | Version/Path |
|------|-------------|
| Node.js | v22.22.0 LTS @ `C:\Users\piwpi\AppData\Local\Programs\nodejs\` |
| Claude Code | `C:\Users\piwpi\AppData\Roaming\npm\claude.cmd` |
| Update | `npm install -g @anthropic-ai/claude-code@latest` |

---

## Session Compaction Prevention Protocol

**Trigger:** Context approaching 180K tokens
**Action:** Create checkpoint file in `shared-intelligence/checkpoints/`
**Format:** `checkpoint-YYYY-MM-DD-HHmm.md` with:
- Current phase and active agents
- Last 3 handoffs (chain_id, trigger_event, status)
- Changed files since last checkpoint (if any)
- Token budget status

**Load on Session Start:** Check for latest checkpoint in `shared-intelligence/checkpoints/` and resume from there.

---

**Last Updated:** 2026-03-17 | **Next Review:** 2026-03-24
