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

### PF-007: Missing Scheduler Shutdown on Daemon Exit
- **Date:** 2026-02-25
- **Agent:** 09-DevOps / Sonolbot Enhancement
- **Task:** M-005 Sonolbot v2.0 — APScheduler integration
- **Pitfall:** BackgroundScheduler started in `_init_scheduler()` but never shut down in `run()` finally block. Result: daemon process hangs on Ctrl+C, hanging jobs block OS shutdown.
- **Prevention:** Always call `scheduler.shutdown()` before releasing daemon lock. Add to finally block: `if self.scheduler and self.scheduler.running: self.scheduler.shutdown()`
- **Files Fixed:** `daemon/daemon_service.py` (line ~430)

### PF-008: Command Logging Without Directory Validation
- **Date:** 2026-02-25
- **Agent:** 09-DevOps / Sonolbot Enhancement
- **Task:** M-005 Sonolbot v2.0 — Command audit logging
- **Pitfall:** `_log_command()` appends to `command_history.log` without checking if parent directory exists. First command write fails silently.
- **Prevention:** Create parent directory with `mkdir(parents=True, exist_ok=True)` before writing. Always wrap in try/except to avoid crashing message handler.
- **Files Fixed:** `daemon/daemon_service.py` method `_log_command()` (line ~870)

### PF-009: GET Endpoints Exposing Data Without Auth
- **Date:** 2026-02-25
- **Agent:** QA Engineer (Phase 3)
- **Task:** M-002 CooCook QA — API security review
- **Pitfall:** `GET /api/coocook/chefs` and `GET /api/coocook/chefs/{id}` lack `@require_auth` decorator. While intentional for public discovery, this is a design decision that must be documented. Risk: prevents future permission changes.
- **Prevention:** Document public endpoints explicitly in API spec. Mark clearly: "This endpoint intentionally public for user discovery." For protected variants, use separate endpoints (e.g., `/api/coocook/chefs-premium`).
- **Status:** ✅ By Design (not a bug, but document it)
- **Reference:** M-002 Phase 3 QA Report, Security section

### PF-010: Response Time Benchmarking Must Include Multiple Runs
- **Date:** 2026-02-25
- **Agent:** QA Engineer (Phase 3)
- **Task:** M-002 CooCook QA — Performance validation
- **Pitfall:** Single API response time test can be anomalous due to caching, system load, etc. 220ms on first run, 180ms on third run due to warm cache.
- **Prevention:** Always measure endpoints 3+ times and report average. Report min/max range. Useful for identifying cache behavior.
- **Example:** GET /chefs: 214ms, 221ms, 218ms → Average 218ms (variance ±3ms indicates stable performance)

### PF-011: JSON Path Extraction with grep Fragile on Complex Responses
- **Date:** 2026-02-25
- **Agent:** QA Engineer (Phase 3)
- **Task:** M-002 CooCook QA — Test automation
- **Pitfall:** Using `curl | grep '"id":[0-9]*'` to extract booking ID from JSON response. Works for simple responses but fails when response includes multiple objects. Returns multiple matches, making ID extraction unreliable.
- **Prevention:** Use proper JSON parser (jq, python -m json.tool) when available. If scripting QA tests, prefer API client libraries over shell curl + grep.
- **Workaround:** For bash, use Python: `python3 -c "import json, sys; print(json.load(sys.stdin)['id'])"`

### PF-012: Database Verification Without Query Tool Requires Python Fallback
- **Date:** 2026-02-25
- **Agent:** QA Engineer (Phase 3)
- **Task:** M-002 CooCook QA — Data integrity check
- **Pitfall:** Attempted `sqlite3` CLI tool for database validation but CLI not in PATH on test system. Had to fall back to Python `sqlite3` library.
- **Prevention:** In QA scripts, prefer Python scripting over CLI tools for database verification. More portable across environments.
- **Script Pattern:**
  ```python
  import sqlite3
  conn = sqlite3.connect("D:/Project/platform.db")
  cursor = conn.cursor()
  cursor.execute("SELECT COUNT(*) FROM booking WHERE total_price > 0")
  print(f"Valid bookings: {cursor.fetchone()[0]}")
  ```

### PF-007: Inconsistent Crawler Output Format
- **Date:** 2026-02-25
- **Agent:** 03-Architect, 05-Backend
- **Task:** M-006 Experience Platform crawlers
- **Pitfall:** Different crawlers return different field names/types (e.g., `expiration` vs `deadline`, datetime vs string). Service layer expects consistent format; inconsistent crawlers cause JSON serialization errors.
- **Prevention:** Define `ExperienceCrawler.format_listings()` that normalizes all output to standard dict schema BEFORE saving. Validate with `validate_listing()` to ensure required keys exist.
- **Files Fixed:** `scripts/crawlers/crawler_base.py` (abstract validation method), `backend/services/experience.py` (schema documentation)

### PF-008: Mixing Dummy Data with Real Database Persistence
- **Date:** 2026-02-25
- **Agent:** 05-Backend
- **Task:** M-006 Experience Platform MVP
- **Pitfall:** If dummy data is embedded in service layer AND database layer saves to DB, later code cannot distinguish real data from test data. Causes "ghost listings" that never disappear.
- **Prevention:** For MVP phase, keep all dummy data in service layer ONLY. Use decorator or environment variable to toggle: `if ENABLE_REAL_CRAWLERS: use_crawlers() else: use_dummy_data()`. Database layer is clean and ready for Phase 5.
- **Files Fixed:** `backend/services/experience.py` (DUMMY_LISTINGS constant isolated)

### PF-009: Silent Crawler Failures Without Logging
- **Date:** 2026-02-25
- **Agent:** 05-Backend, 06-QA
- **Task:** M-006 crawler framework
- **Pitfall:** Crawler fails to fetch page (timeout, 403, network error) but service returns empty list without logging. QA sees "no listings found" and debugs wrong area (service layer) instead of crawler.
- **Prevention:** Every crawler must log errors to `CrawlerLog` table with status='error' and error_message. Service layer MUST check log before returning data. Crawler failures visible in `/api/experience/stats` response.
- **Files Fixed:** `scripts/crawlers/crawler_base.py` (try/except with CrawlerLog), `backend/models.py` (CrawlerLog model)

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
