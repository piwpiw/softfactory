# claude.md

## 0) Meta Policy
- Status: ACTIVE
- Version: 2026-03-01
- Last Updated: 2026-03-01
- Scope IN: Agent workflow governance, MCP execution policy, handoff + token control, PR/review/build quality gates
- Scope OUT: Product feature specification writing
- Owner: T1/T2/T3/T4/T5/T6/T7/T8/T9/T10 governance
- Rule: Must stay at 500 lines or less

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
- Backend: Flask monolith
- Frontend: Vanilla JS / HTML / CSS
- Data: PostgreSQL, shared services in backend/services
- CI/CD: GitHub Actions / Vercel / Docker

## 3) MCP Runtime Contract
- `mcp.search = true` (mandatory)
- `mcp.view_file`: hashtag search first, line range read second
- `mcp.edit_file`: function/file scoped edits only
- Default context window: <= 120 lines around matched tag
- Full-file read only with explicit reason in Memory Update

## 4) Context Loading Law
- Never load `CONTEXT_ENGINE.md` in full by default.
- Search tags first (`#phase`, `#errors`, `#constraints`, `#file_functions`).
- Read only the needed block and record window in memory update.
- Full read only when safety/incident reason is documented.

## 5) Handoff Contract (File + Function first)
- Required fields: `chain_id`, `trigger_event`, `from_team`, `to_team`, `status`, `payload.files`, `payload.changed_functions`
- `changed_functions`: `{ "path": "<file>", "name": "<functionName|unknown>" }`
- Emit after completion:
  - validate handoff
  - emit handoff
  - log to handoff ledger

## 5a) Automation Trigger Map
- `BACKEND_API_CHANGED` -> `T2`
- `FRONTEND_UI_CHANGED` -> `T6`, `T10`
- `QA_FAILED` -> source team + `T7`
- `SECURITY_RISK_FOUND` -> `T9`
- `PHASE_READY_FOR_DEPLOY` -> `T8`

## 6) ReAct Execution Cycle
Research -> Think -> Execute -> Observe -> Memory Update -> Report

## 7) PR / Build Automation
- PR review must run through `skills/pr-review`.
- Build checks must run through `skills/build-check`.
- Results returned with `file/function` scope, not only file path.

## 8) Governance Phase
- Discovery -> Planning -> Implementation -> Validation -> Deployment -> Post-deploy review

## 9) Roles and Escalation
- Source team acts first; unresolved risk passes through routing + to-handoff path.
- Escalation: self-repair -> related team -> user evidence pack.
- Blockers must include: symptom, evidence, decision, next action.

## 10) Quality Gates
- Token policy: partial read, no full-surface scans by default
- PR gate: function-scoped findings + severity tags
- Build gate: minimal checks tied to changed scope
- Release gate: `T7` and `T8` handoff complete
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

## 10c) Sync Rule
- When policy changes, run `.agent/workflows/context-sync.md` and update related `.agent` docs in same change set.

## 11) Done Criteria
- Scope bounded
- Verification executed
- `#decisions` or `#errors` updated
- handoff payload emitted
- changed_functions logged
