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
