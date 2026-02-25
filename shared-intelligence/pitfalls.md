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

---

## Docker / Migration

### PF-012: Docker Desktop Daemon Check Must Happen Before Compose Commands
- **Date:** 2026-02-25
- **Agent:** DevOps (M-002 Phase 4)
- **Task:** PostgreSQL Docker initialization
- **Pitfall:** Running `docker-compose up -d db` when Docker Desktop is not running silently fails with cryptic error: `Cannot connect to Docker daemon at npipe:////./pipe/dockerDesktopLinuxEngine`. User thinks compose syntax is wrong, when Docker daemon is actually offline.
- **Prevention:** **Always verify Docker daemon first:** `docker ps` (on Windows, this launches Docker Desktop if needed, but check output). If error mentions "pipe" or "daemon", start Docker Desktop GUI before retrying.
- **Workaround:** Windows GUI: Start → "Docker Desktop" → wait 60 seconds for taskbar icon to stabilize → retry compose commands.

### PF-013: PostgreSQL Container Initialization Time Not Awaited
- **Date:** 2026-02-25
- **Agent:** DevOps (M-002 Phase 4)
- **Task:** SQLite → PostgreSQL migration setup
- **Pitfall:** Running `docker-compose up -d db` followed immediately by `python scripts/migrate_to_postgres.py` fails with `Connection refused on port 5432`. PostgreSQL container is running, but `initdb` not yet complete (takes 10-15 seconds).
- **Prevention:** After `docker-compose up -d db`, wait 15+ seconds OR loop-check: `docker logs project_db_1 | grep "ready to accept connections"`. Migration script should include retry logic with exponential backoff.
- **Fixed in:** `scripts/migrate_to_postgres.py` v1.1 (adds 3 retry attempts with 5s delays)

### PF-014: SQLite Source DB Must Be Closed Before Migration
- **Date:** 2026-02-25
- **Agent:** DevOps (M-002 Phase 4)
- **Task:** SQLite → PostgreSQL migration
- **Pitfall:** If Flask or other process has `platform.db` file open, migration script cannot read it cleanly. Result: partial migration or "database is locked" error.
- **Prevention:** Ensure Flask is stopped: `docker-compose down` (if running). Check no other processes: `lsof | grep platform.db` (Linux/Mac) or Task Manager search `platform.db` (Windows). Then start fresh: `docker-compose up -d db && python scripts/migrate_to_postgres.py`.

### PF-015: PostgreSQL Volume Persists After Container Removal
- **Date:** 2026-02-25
- **Agent:** DevOps (M-002 Phase 4)
- **Task:** Docker cleanup after failed tests
- **Pitfall:** Running `docker-compose down` removes containers but NOT volumes. If you want a fresh database, the old `postgres_data` volume still exists, and `docker-compose up` reattaches it (with old data). User expects "fresh start" but gets stale database.
- **Prevention:** To fully reset: `docker-compose down -v` (removes volumes). To selectively remove: `docker volume rm project_postgres_data`. Always verify with `docker volume ls` before restart.

---

## Documentation / Deployment

### PF-016: Deployment Checklist Must Cover Docker Desktop Detection
- **Date:** 2026-02-25
- **Agent:** DevOps (M-002 Phase 4)
- **Task:** DEPLOYMENT_CHECKLIST.md creation
- **Pitfall:** Initial checklist assumed Docker Desktop was running. First time following it, user was confused why `docker ps` fails. Doesn't teach WHERE to start Docker.
- **Prevention:** Include explicit "Check Docker Desktop is Running" as Step 0 in all deployment guides. Provide screenshots or CLI commands to verify daemon status.
- **File Updated:** `DEPLOYMENT_CHECKLIST.md` Part 2 (includes GUI + CLI startup methods)

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

### PF-017: Missing Correlation IDs in Logs Makes Debugging Hard
- **Date:** 2026-02-25
- **Agent:** 04-DevOps / Monitoring
- **Task:** M-004 Production Monitoring Setup
- **Pitfall:** When an error occurs, logs for that request are scattered across many lines. Without a correlation ID (request_id), tracing a single user's request through database queries, API calls, and error handlers requires manual log grepping across timestamps. Result: 30-minute debugging that should take 5 minutes.
- **Prevention:** Every Flask request must generate a unique request_id (UUID or incrementing counter) in `@app.before_request`. Inject into all log entries. Include in response headers (X-Request-Id). When debugging, grep logs for that single request_id to see full request lifecycle.
- **Reference:** `backend/logging_config.py` — RequestIdFilter, request_logging_middleware functions
- **Files Fixed:** `backend/logging_config.py` (new), `backend/metrics.py` (new)

### PF-018: Prometheus Scrape Failures Silent When Metrics Endpoint Not Added
- **Date:** 2026-02-25
- **Agent:** 04-DevOps / Monitoring
- **Task:** M-004 Production Monitoring Setup
- **Pitfall:** Flask app running, all endpoints work, but Prometheus shows target as "DOWN" — seems to indicate service crash. Actually, the `/api/metrics/prometheus` endpoint was never registered. Prometheus retries silently every 15 seconds.
- **Prevention:** Always verify metrics endpoints exist before starting Prometheus scrape job. Test endpoint manually: `curl http://localhost:8000/api/metrics/prometheus`. If 404, check that `app.register_blueprint(metrics_bp)` is called in create_app().
- **Reference:** `backend/metrics.py` — Blueprint registration required
- **Status:** Caught in Step 6 of MONITORING-INTEGRATION.md

### PF-019: JSON Logs Without Proper Escaping Cause Kibana Parse Failures
- **Date:** 2026-02-25
- **Agent:** 04-DevOps / Monitoring
- **Task:** M-004 Production Monitoring Setup
- **Pitfall:** Application logs messages that contain newlines or quotes without escaping. Logstash attempts to parse as JSON but fails. Result: unparseable log entries in Elasticsearch, Kibana shows zero results.
- **Prevention:** Use python-json-logger package which auto-escapes. Never manually construct JSON strings in logs. Always use logger.info('message', extra={'key': 'value'}) pattern. Test: `echo "message with \"quotes\"" | python -m json.tool`
- **Reference:** `backend/logging_config.py` uses JSONFormatter from python-json-logger
- **Testing:** Run: `tail logs/app.log | python -m json.tool` — should parse without errors

### PF-020: Alert Rules With Wrong Metric Names Silent Fail
- **Date:** 2026-02-25
- **Agent:** 04-DevOps / Monitoring
- **Task:** M-004 Production Monitoring Setup
- **Pitfall:** Write alert rule like `expr: high_memory > 80` but metric is actually named `softfactory_memory_percent`. Prometheus silently evaluates to "no data" and never fires alert. No error in logs, no indication why alert not triggering.
- **Prevention:** Before adding alert rule, verify metric exists: `curl http://localhost:8000/api/metrics/prometheus | grep metric_name`. Test PromQL query in Prometheus UI (localhost:9090/graph) before adding to alert-rules.yml.
- **Reference:** `orchestrator/alert-rules.yml` — all metric names verified against actual exports
- **Testing:** Script in MONITORING-SETUP.md validates all rule metrics

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

## PF-008: Database Query N+1 Pattern (2026-02-25)
**Severity:** HIGH | **Impact:** 40-60% performance degradation | **Detection:** Automated tests

### Problem
Multiple endpoints execute N+1 queries instead of single JOIN queries:
- Campaign listing: 1 query + 12 COUNT queries (13 total, 42ms)
- Dashboard stats: 6 separate COUNT queries (58ms)
- SNS account counts: 1 query + 5 COUNT queries (25ms)

### Root Cause
Using nested loops with database queries:
```python
for campaign in campaigns:
    count = CampaignApplication.query.filter_by(campaign_id=campaign.id).count()
```

### Prevention (Now Standard)
1. Always use JOINs with GROUP BY for aggregations
2. Use `joinedload()` for eager loading relationships
3. Batch COUNT operations with single query
4. Automated tests verify query count == 1

### Reference
- Report: `docs/database-optimization-report.md`
- Quick fix: `docs/DATABASE_OPTIMIZATION_QUICKSTART.md`
- Examples: `backend/query_optimization_examples.py`
- Tests: `tests/test_database_performance.py`

