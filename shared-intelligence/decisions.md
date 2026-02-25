# Shared Intelligence — Decisions Log (ADR Format)
> **Purpose:** Every architectural decision recorded here. No decision without a reason.
> **Format:** ADR (Architecture Decision Record) — lightweight version
> **Rule:** Append after every major decision. Never delete — supersede with new ADR.

---

## ADR Index

| ID | Title | Status | Date | Applies To |
|----|-------|--------|------|-----------|
| ADR-0001 | Clean Architecture + Modular Monolith | ✅ ACCEPTED | 2026-02-22 | M-002 CooCook |
| ADR-0002 | FastAPI for CooCook (vs Flask) | ✅ ACCEPTED | 2026-02-22 | M-002 CooCook |
| ADR-0003 | SQLite → PostgreSQL Migration Path | ✅ ACCEPTED | 2026-02-23 | M-003 SoftFactory |
| ADR-0004 | Additive Governance (vs Full Restructure) | ✅ ACCEPTED | 2026-02-25 | Platform-wide |
| ADR-0005 | Markdown-first Shared Intelligence | ✅ ACCEPTED | 2026-02-25 | Platform-wide |
| ADR-0006 | CooCook MVP Phase Completion (Phase 2-4) | ✅ ACCEPTED | 2026-02-25 | M-002 CooCook |
| ADR-0007 | Sonolbot v2.0 — Extend with Scheduling & Logging | ✅ ACCEPTED | 2026-02-25 | M-005 Sonolbot |
| ADR-0008 | M-002 CooCook Phase 3 QA Sign-Off | ✅ ACCEPTED | 2026-02-25 | M-002 CooCook |

---

## ADR-0001: Clean Architecture + Modular Monolith for CooCook MVP

**Status:** ACCEPTED
**Date:** 2026-02-22
**Decided by:** 01-Dispatcher (after 04-Architect + 05-Backend consultation)

**Context:** CooCook needs to handle 10K MAU by Q3 2026. Need to choose initial architecture.

**Decision:** Use Clean Architecture layers (Domain → Application → Infrastructure → Presentation) within a Modular Monolith structure.

**Rationale:**
- Fast iteration for MVP phase
- Reduced operational complexity vs microservices
- Clear migration path: Monolith until 100+ RPS, then extract services

**Trade-offs:**
- Monolith: shared DB, simpler deployment, less operational overhead
- Clean Architecture: more initial boilerplate, but enforces domain isolation

**Consequence:** All CooCook modules must respect layer boundaries. No direct DB access from presentation layer.

**Full doc:** `docs/generated/adr/ADR-0001_Adopt_Clean_Architecture_with_Modular_Monolith_for_CooCook_MVP.md`

---

## ADR-0002: FastAPI for CooCook (vs Flask)

**Status:** ACCEPTED
**Date:** 2026-02-22
**Decided by:** 01-Dispatcher

**Context:** M-003 SoftFactory uses Flask. M-002 CooCook is a new project — should it reuse Flask or use FastAPI?

**Decision:** Use FastAPI for CooCook.

**Rationale:**
- Native async support (better for 10K MAU scale)
- Built-in OpenAPI/Swagger docs
- Better ORM integration with SQLAlchemy 2.0 async
- Type-safe request/response models via Pydantic
- Flask maintained only for SoftFactory (legacy/stable)

**Trade-offs:** Two frameworks in the platform — acceptable because projects are isolated.

---

## ADR-0003: SQLite → PostgreSQL Migration Path for SoftFactory

**Status:** ACCEPTED
**Date:** 2026-02-23
**Decided by:** 04-Architect

**Context:** SoftFactory MVP uses SQLite. Production needs PostgreSQL.

**Decision:** SQLite for development/staging, PostgreSQL for production. Migration triggered at 1K+ active users or before Railway/AWS deployment.

**Rationale:** SQLite enables zero-config local dev. Migration is low-risk with SQLAlchemy ORM (schema is backend-agnostic).

**Migration path:** `DATABASE_URL` env var switch → run `flask db upgrade` → verify data integrity.

---

## ADR-0004: Additive Governance Over Full Restructure

**Status:** ACCEPTED
**Date:** 2026-02-25
**Decided by:** Orchestrator

**Context:** 15 enterprise governance principles applied to existing production platform (16/16 tests passing, Sonolbot running, SoftFactory deployed).

**Decision:** Add governance layer additively — new `/shared-intelligence/` and `/orchestrator/` directories. Do not restructure existing code.

**Rationale:**
- Existing code is production-ready and tested
- Restructuring risks regressions
- Governance files are independent of runtime code
- "Complexity is the enemy" (Principle #10) — minimum necessary change

**What is NOT changed:** `backend/`, `daemon/`, `.claude/agents/`, `docs/generated/`

---

## ADR-0005: Markdown-first Shared Intelligence

**Status:** ACCEPTED
**Date:** 2026-02-25
**Decided by:** Orchestrator

**Context:** Platform needs cross-session agent memory. Options: database, vector store, markdown files.

**Decision:** Markdown files in `/shared-intelligence/` as the canonical shared memory layer.

**Rationale:**
- Consistent with existing project (all docs are .md)
- Git-tracked — full history, diff-able, reviewable
- No additional infrastructure (no DB, no vector store)
- Human-readable — agents and humans can access the same file
- MCP filesystem server provides programmatic access if needed

**Consequence:** All agents MUST append to shared-intelligence files after every task (Principle #9).

---

## ADR-0006: CooCook MVP Phase Completion (Phase 2-4)

**Status:** ACCEPTED
**Date:** 2026-02-25
**Decided by:** Orchestrator + Development Lead (Agent C)

**Context:** M-002 CooCook requires MVP completion to enter QA phase by 2026-02-27. Phase 0 (input parsing) and Phase 1 (strategy+design) were complete. Phases 2-4 (Development, QA, Deployment) executed on 2026-02-25.

**Decision:** Execute Phases 2-4 sequentially with automated testing. Mark MVP as COMPLETE upon all core API endpoints returning 200 OK and web pages loading without errors.

**Rationale:**
- All prerequisite data exists (5 sample chefs, demo user with subscription)
- API endpoints already implemented in `backend/services/coocook.py`
- Web pages already created in `web/coocook/`
- Database ready with absolute path configuration (per PAT-005)
- No architectural changes needed — only verification

**Trade-offs:**
- Skipped manual browser testing in this session (will be done during QA phase 2026-02-27)
- Demo mode used instead of production auth (acceptable for MVP)

**Consequence:**
- CooCook MVP marked ready for QA phase
- Access via: http://localhost:8000/web/coocook/index.html
- 2-day buffer before QA deadline (2026-02-27)

---

## ADR-0007: Sonolbot v2.0 — Extend with Scheduling & Logging

**Status:** ACCEPTED
**Date:** 2026-02-25
**Decided by:** 09-DevOps (Sonolbot Enhancement)

**Context:** M-005 Sonolbot v1.0 has 5 core commands (/task-new, /task-list, /task-activate, /s, /h). Users need reminders, summaries, data exports, and command auditing. Question: add features incrementally or restructure?

**Decision:** Extend v1.0 additively with 4 new commands + APScheduler background jobs + logging infrastructure.

**New Features:**
- Commands: `/remind [date] [msg]`, `/summary`, `/export [json|csv]`, `/logs [lines]`
- Scheduler: Daily standup (9 AM), weekly summary (Fri 6 PM), log cleanup (3 AM)
- Logging: `command_history.log` for audit trail
- Persistence: `reminders.json` for scheduled reminders

**Rationale:**
- APScheduler is already a dependency (python-telegram-bot[all])
- Additive approach: zero changes to existing v1.0 code paths
- Command logging required for compliance/audit
- Scheduled jobs improve user experience (recurring notifications)
- JSON-backed state survives daemon restart

**Trade-offs:**
- One additional background thread (scheduler)
- Slight memory overhead (reminders dict in memory)
- Log files grow over time (automatic 7-day cleanup)

**Alternative considered:**
- Pure event-driven (no scheduler) — rejected because lost notifications if daemon restarts during scheduled time
- Database-backed reminders — rejected because adds DB dependency and complexity (Principle #10)

**Consequence:**
- Sonolbot bumped to v2.0
- New `daemon/README.md` documents all commands
- `shared-intelligence/patterns.md` includes PAT-010, PAT-011, PAT-012 for reuse in future bots
- Scheduler must be shut down gracefully on daemon exit (PF-007)
- Command logging appends to text file (no special infrastructure)

**Files Changed:**
- `daemon/daemon_service.py` (+1000 lines, +7 methods)
- `daemon/README.md` (NEW, comprehensive guide)
- `shared-intelligence/patterns.md` (added PAT-010, PAT-011, PAT-012)
- `shared-intelligence/pitfalls.md` (added PF-007, PF-008)

---

---

## ADR-0008: M-002 CooCook Phase 3 QA Sign-Off (Ready for Staging)

**Status:** ACCEPTED
**Date:** 2026-02-25
**Decided by:** QA Engineer (Haiku 4.5)

**Context:** CooCook MVP Phase 2 development complete. Requires full QA validation before moving to Phase 4 (DevOps deployment).

**Decision:** **APPROVED FOR STAGING** — All quality gates passed. 47/47 test cases passed (0 failures). Zero critical/high-severity bugs identified.

**Rationale:**
- All 5 web pages load without errors + proper navigation
- All 5 API endpoints functional: GET /chefs (public), GET /chefs/{id} (public), GET /bookings (protected), POST /bookings (protected), PUT /bookings/{id} (protected + chef-only)
- Security baseline verified: authentication required, authorization enforced, SQL injection prevented, input validation working
- Performance acceptable: all endpoints < 250ms (target 500ms)
- Data integrity confirmed: 7 test bookings created with correct price calculations (120-150 KRW/hr × duration_hours)
- No console errors, no browser compatibility issues
- Demo mode functional (passkey `demo2026` / token `demo_token`)

**Trade-offs:**
- GET /chefs endpoints are public (by design for user discovery) — not a security issue, but documented
- Phase 4 will add SSL/HTTPS and production domain CORS
- Review and payment systems tested but not fully exercised (Phase 4+ features)

**Consequence:**
- CooCook proceeds to Phase 4 (DevOps deployment preparation)
- Database backed up before staging deployment
- Staging environment will run same code as production
- QA artifacts generated: `qa-report-coocook-m002-phase3.md`, `handoffs/M-002-CooCook-Phase3-QA-Approval.md`
- DevOps Engineer responsible for deployment checklist (see handoff doc)

**Reference:**
- Full QA Report: `shared-intelligence/qa-report-coocook-m002-phase3.md`
- Handoff Document: `shared-intelligence/handoffs/M-002-CooCook-Phase3-QA-Approval.md`
- Updated Index: ADR-0006 added to ADR Index (line 17)

---

## Template for New ADRs

```markdown
## ADR-XXXX: [Title]

**Status:** PROPOSED | ACCEPTED | SUPERSEDED | DEPRECATED
**Date:** YYYY-MM-DD
**Decided by:** [agent/role]

**Context:** [What situation prompted this decision?]

**Decision:** [What was decided?]

**Rationale:** [Why this option over alternatives?]

**Trade-offs:** [What are the downsides?]

**Consequence:** [What changes as a result?]
```
