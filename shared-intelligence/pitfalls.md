# Shared Intelligence — Pitfalls Registry
> **Purpose:** Every task appends here — zero silent failures, zero repeated mistakes.
> **Format:** Date | Agent | Task | Pitfall | Prevention
> **Requirement:** Mandatory update per Governance Principle #9

---

## Python / Backend

### PF-001: Python Decorator Execution Order
- **Date:** 2026-02-23
- **Agent:** 05-Backend
- **Task:** M-003 SoftFactory API routes
- **Pitfall:** Decorators execute bottom-to-top. Writing `@require_subscription('x') @require_auth` causes `@require_auth` to run first — but `@require_subscription` was checking `user_id` before auth ran, causing `AttributeError`.
- **Prevention:** Always place `@require_auth` on the innermost (bottom) position. Rule: auth decorators go LAST in source order.
- **Files Fixed:** `backend/services/coocook.py`, `sns_auto.py`, `review.py`, `ai_automation.py` (17 routes total)

### PF-002: SQLite Relative Path Fails on Process Restart
- **Date:** 2026-02-23
- **Agent:** 05-Backend
- **Task:** M-003 DB initialization
- **Pitfall:** `sqlite:///platform.db` resolves relative to CWD — if Flask is started from a different directory, a second database file is created silently.
- **Prevention:** Always use absolute path: `sqlite:///D:/Project/platform.db`. Set via `os.path.abspath()` in `app.py`.

### PF-003: Demo Token Format Inconsistency
- **Date:** 2026-02-24
- **Agent:** 05-Backend
- **Task:** M-003 API testing
- **Pitfall:** Demo token was generated as `'demo_token_' + timestamp` but `@require_auth` checked for static string `'demo_token'`. Caused 401 on all demo requests.
- **Prevention:** Standardize demo token as static string `'demo_token'`. Never append dynamic suffixes to static-check tokens.

### PF-004: Missing `to_dict()` on SQLAlchemy Models
- **Date:** 2026-02-24
- **Agent:** 05-Backend
- **Task:** M-003 AI Automation endpoints
- **Pitfall:** `AIEmployee` and `Scenario` models lacked `to_dict()` — returning raw SQLAlchemy objects caused `TypeError: Object of type AIEmployee is not JSON serializable`.
- **Prevention:** Every SQLAlchemy model MUST implement `to_dict()`. Add to model template and code review checklist.

---

## Infrastructure / DevOps

### PF-005: Virtual Environment Path Breaks Sonolbot
- **Date:** 2026-02-23
- **Agent:** 09-DevOps
- **Task:** M-005 Sonolbot daemon setup
- **Pitfall:** Sonolbot daemon fails silently with "missing venv python runtime" if `.venv/Scripts/pythonw.exe` is absent or path is wrong.
- **Prevention:** Always verify `daemon/.venv/Scripts/pythonw.exe` exists before starting daemon. Control panel checks on launch.

---

## Documentation

### PF-006: MEMORY.md Line Limit (200 lines)
- **Date:** 2026-02-25
- **Agent:** Orchestrator
- **Task:** Session memory management
- **Pitfall:** `MEMORY.md` grew to 365 lines — only first 200 loaded into context. Critical project info was being silently truncated.
- **Prevention:** Keep MEMORY.md ≤200 lines. Extract detail into topic files (e.g., `memory/project-status.md`). MEMORY.md is an index, not a dump.

---

## Template for New Entries

```markdown
### PF-XXX: [Short Title]
- **Date:** YYYY-MM-DD
- **Agent:** [agent-id]
- **Task:** [project/task]
- **Pitfall:** [what went wrong and why]
- **Prevention:** [concrete rule to prevent recurrence]
- **Files Fixed:** [if applicable]
```
