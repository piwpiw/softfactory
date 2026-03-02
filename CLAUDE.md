# claude.md

## 0) Meta Policy
- Status: ACTIVE
- Version: 2026-03-02
- Last Updated: 2026-03-02
- Scope IN: Agent workflow governance, MCP execution policy, handoff + token control, PR/review/build quality gates
- Scope OUT: Product feature specification writing
- Owner: T1/T2/T3/T4/T5/T6/T7/T8/T9/T10 governance
- Rule: Must stay at 500 lines or less
- T↔PA mapping: see `.agent/AGENT_SYSTEM.md §1`

## 1) Imports (Mandatory)
1. claude.md
2. .agent/AGENT_SYSTEM.md
3. .agent/CONTEXT_ENGINE.md
4. .agent/AGENT_PROTOCOLS.md
5. .agent/COST_RULES.md

## 1a) File Naming Rule
- Canonical policy file name is `claude.md`.
- Do not create or use `claud.md` alias files.

## 2) Technical Context
- Backend: Flask monolith (`backend/app.py`, `backend/services/`, `backend/models.py`)
- Frontend: Vanilla JS / HTML / CSS (`web/`)
- Data: SQLite dev (`platform.db`) → PostgreSQL prod, shared services in `backend/services/`
- CI/CD: GitHub Actions / Vercel / Docker
- Agents: Python implementations in `agents/01_dispatcher/` ~ `agents/10_telegram_reporter/`
- Skills: Python modules in `skills/` (10 files: agile, API-first, DDD, TDD, OWASP, etc.)
- MCP Core: filesystem, sqlite, fetch (see `orchestrator/mcp-registry.md`)

## 3) MCP Runtime Contract
- `mcp.search = true` (mandatory)
- `mcp.view_file`: hashtag search first, line range read second
- `mcp.edit_file`: function/file scoped edits only
- Default context window: <= 120 lines around matched tag
- Full-file read only with explicit reason in Memory Update

## 4) Context Loading Law
- Never load `CONTEXT_ENGINE.md` in full by default.
- Search tags first (`#phase`, `#errors`, `#constraints`, `#file_functions`, `#decisions`, `#patterns`).
- Read only the needed block and record window in memory update.
- Full read only when safety/incident reason is documented.

## 5) Handoff Contract (File + Function first)
- Required fields: `chain_id`, `trigger_event`, `from_team`, `to_team`, `status`, `payload.files`, `payload.changed_functions`
- `changed_functions`: `{ "path": "<file>", "name": "<functionName|unknown>" }`
- Emit after completion:
  - validate handoff
  - emit handoff
  - log to handoff ledger (`shared-intelligence/handoffs/`)

## 5a) Automation Trigger Map
- `BACKEND_API_CHANGED` -> `T5` (PA-05 Backend Dev)
- `FRONTEND_UI_CHANGED` -> `T6` (PA-06 Frontend), `T10` (PA-10 Telegram)
- `QA_FAILED` -> source team + `T7` (PA-07 QA)
- `SECURITY_RISK_FOUND` -> `T8` (PA-08 Security Auditor)
- `PHASE_READY_FOR_DEPLOY` -> `T9` (PA-09 DevOps)

## 6) ReAct Execution Cycle
Research -> Think -> Execute -> Observe -> Memory Update -> Report

## 7) PR / Build Automation
- PR review must run through `skills/pr-review`.
- Build checks must run through `skills/build-check`.
- Results returned with `file/function` scope, not only file path.

## 8) Governance Phase
- Phase -1 (Research) -> Phase 0 (Planning) -> Phase 1 (Requirement) -> Phase 2 (Documentation) -> Phase 3 (Design) -> Phase 4 (Development) -> Phase 5 (Testing) -> Phase 6 (Finalization) -> Phase 7 (Delivery)
- Details: `orchestrator/phase-structure-v4.md`

## 9) Roles and Escalation
- Source team acts first; unresolved risk passes through routing + to-handoff path.
- Escalation: self-repair -> related team -> governance (PA-01) -> user evidence pack.
- Blockers must include: symptom, evidence, decision, next action.
- Authority overrides: PA-04 (technical), PA-02 (product), PA-08 (security halt), PA-01 (priority)

## 10) Quality Gates
- Token policy: partial read, no full-surface scans by default
- PR gate: function-scoped findings + severity tags
- Build gate: minimal checks tied to changed scope
- Release gate: `T7` (QA) and `T9` (DevOps) handoff complete
- Pre-deploy local gate: app boots locally and `GET /health` returns `200`
- Note: local backend health endpoint is `/health`; `/api/health` may be proxy-only

## 10a) Required Output Schema
```json
{
  "status": "ok|needs_action|failed",
  "changed_files": ["backend/services/example.py"],
  "changed_functions": [
    {"path": "backend/services/example.py", "name": "run_example"}
  ],
  "validation": ["lint", "test", "build"]
}
```

## 10b) Prohibited Actions
- No full-repo scans unless explicitly requested.
- No repeated retries without new evidence.
- No out-of-scope mass edits.
- No secret exposure in code, logs, or docs.
- No appending activity logs to this file (use `shared-intelligence/handoffs/` instead).

## 10c) Sync Rule
- When policy changes, run `.agent/workflows/context-sync.md` and update related `.agent` docs in same change set.

## 11) Done Criteria
- Scope bounded
- Verification executed
- `#decisions` or `#errors` updated
- handoff payload emitted
- changed_functions logged

## 12) Enterprise 15-Principle Framework
1. **Scope-First:** Always bound scope before execution
2. **Function-Scope:** Document changes at function level, not file level
3. **Evidence-Based:** Every blocker includes symptom + evidence + decision
4. **Context-Minimal:** Load only necessary context (tag search first)
5. **Batch-Efficient:** Combine 3+ operations into single tool call
6. **Handoff-Complete:** Emit structured handoff with all required fields
7. **Memory-Hierarchical:** MEMORY.md index → topic files → archive
8. **Rollback-Safe:** All destructive ops confirmed before execution
9. **Cost-Conscious:** Monitor tokens; aim for ≤150K per session
10. **Team-Routed:** Use automation trigger map (§5a) for handoffs
11. **Escalation-Structured:** 4-level path (self-repair → team → governance → user)
12. **Quality-Gated:** Pre-deploy gate: app boots + GET /health → 200
13. **Error-Documented:** All errors logged in #errors tag with resolution
14. **Pattern-Shared:** New patterns added to shared-intelligence/patterns.md
15. **Verification-Explicit:** Done criteria (§11) met before marking complete
