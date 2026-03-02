# Agent Protocols & Communication

> **Version:** 2026-03-02 | **Status:** ACTIVE | **Parent:** CLAUDE.md §1 Import #4
> **Purpose:** Handoff format, escalation paths, phase transitions — enforces CLAUDE.md §5, §5a, §9

---

## 1. Handoff Payload Schema

Per CLAUDE.md §5 (required fields) + §10a (output schema):

```json
{
  "chain_id": "UUID-v4",
  "trigger_event": "BACKEND_API_CHANGED",
  "from_team": "T5",
  "from_agent": "PA-05",
  "to_team": ["T6", "T10"],
  "to_agents": ["PA-06", "PA-10"],
  "status": "pending|executing|complete|failed",
  "timestamp": "2026-03-02T12:30:00Z",
  "payload": {
    "files": ["backend/services/example.py"],
    "changed_functions": [
      {"path": "backend/services/example.py", "name": "run_example"}
    ],
    "context": "Brief summary of what changed and why",
    "blockers": null,
    "validation": ["lint", "test", "build"]
  }
}
```

**Storage:** `shared-intelligence/handoffs/{chain_id}.json`

---

## 2. Automation Trigger Map

Per CLAUDE.md §5a. Columns show T-number, PA-ID, and role for clarity:

| Trigger Event | Receiver T-ID | Receiver PA-ID | Role | Action |
|---------------|---------------|----------------|------|--------|
| `BACKEND_API_CHANGED` | T5 | PA-05 | Backend Dev | Review API change, update integration |
| `FRONTEND_UI_CHANGED` | T6, T10 | PA-06, PA-10 | Frontend, Telegram | UI sync, notify stakeholders |
| `QA_FAILED` | Source + T7 | Source + PA-07 | Source team + QA | Fix root cause, re-test |
| `SECURITY_RISK_FOUND` | T8 | PA-08 | Security Auditor | Immediate audit, can halt pipeline |
| `PHASE_READY_FOR_DEPLOY` | T9 | PA-09 | DevOps | Deploy preparation, runbook execution |

**Note:** T↔PA mapping defined in `.agent/AGENT_SYSTEM.md §1`.

---

## 3. Escalation Protocol

Per CLAUDE.md §9 + `orchestrator/agent-registry.md` §Authority Rules:

### Escalation Levels

| Level | Action | Owner | SLA |
|-------|--------|-------|-----|
| L1 | Self-repair (auto-retry with new evidence) | Executing agent | Immediate |
| L2 | Horizontal handoff to related team | Next in hierarchy | Within phase |
| L3 | Vertical escalation to governance | PA-01 Dispatcher | End of phase |
| L4 | User evidence pack (human intervention) | User | Session boundary |

### Escalation Chains (from agent-registry.md)

```
PA-10 (Telegram) ──→ PA-01 (Dispatcher)
PA-06 (Frontend) ──→ PA-05 (Backend) ──→ PA-04 (Architect) ──→ PA-01
PA-07 (QA)       ──→ PA-05 (Backend) ──→ PA-04 (Architect) ──→ PA-01
PA-08 (Security) ──→ PA-04 (Architect) ──→ PA-01
PA-09 (DevOps)   ──→ PA-04 (Architect) ──→ PA-01
PA-03 (Market)   ──→ PA-02 (PM) ──→ PA-01
```

### Authority Overrides

| Scenario | Authority | Rule |
|----------|-----------|------|
| Technical disagreement | PA-04 Architect | Final say on design |
| Product disagreement | PA-02 PM | Final say on features |
| Security override | PA-08 Security | Can halt ANY task immediately |
| Priority dispute | PA-01 Dispatcher | Final arbiter |

---

## 4. Blocker Format

Per CLAUDE.md §9 — every blocker MUST include all 4 fields:

```markdown
**Blocker:** [Component / File / Function]
- **Symptom:** What is observably wrong (error message, test failure, unexpected behavior)
- **Evidence:** Specific log lines, stack traces, test output, or screenshots
- **Decision:** Root cause analysis or hypothesis
- **Next Action:** Concrete next step with owner assignment
```

**Rule:** No blocker without evidence. No escalation without a blocker.

---

## 5. Phase Transition Protocol

From `orchestrator/phase-structure-v4.md` (8 phases):

| Phase | Name | Lead Agent | Parallel? | Sync Point |
|-------|------|-----------|-----------|------------|
| -1 | Research | PA-03 Market | Yes | All research → shared-intelligence/ |
| 0 | Planning | PA-02 PM | Sequential | 3 docs reviewed, feasibility confirmed |
| 1 | Requirement | PA-02 PM | Sequential | API spec + user stories + QA review |
| 2 | Documentation | Doc Lead | Yes | All docs complete, coverage checked |
| 3 | Design | PA-04 Architect | Sequential | Security review passed → green light |
| 4 | Development | PA-05 Backend | Yes (modules) | Peer review per module |
| 5 | Testing | PA-07 QA | Yes | All reports pass |
| 6 | Finalization | PA-05 Backend | Sequential | READY_FOR_DEPLOY.md created |
| 7 | Delivery | PA-09 DevOps | Sequential | PR merged, deployed |

**Transition rule:** No phase advances until its sync point is met.

---

## 6. RACI Matrix (Key Decisions)

From `orchestrator/agent-registry.md`:

| Decision | R (Responsible) | A (Accountable) | C (Consulted) | I (Informed) |
|----------|----------------|-----------------|---------------|--------------|
| Architecture change | PA-04 | PA-01 | PA-05, PA-06 | PA-07, PA-09 |
| Feature priority | PA-02 | PA-01 | PA-03 | All |
| Security block | PA-08 | PA-01 | PA-04, PA-05 | All |
| Deployment | PA-09 | PA-01 | PA-04, PA-07 | PA-10 |
| New agent onboarding | PA-01 | PA-01 | All | All |

---

## 7. Handoff Execution Sequence

Per CLAUDE.md §5 and §11 (Done Criteria):

```
1. SCOPE       → Bound the task scope
2. EXECUTE     → Implement within scope
3. VALIDATE    → Run lint/test/build (§10a validation array)
4. DOCUMENT    → Update #decisions or #errors tags
5. EMIT        → Write handoff payload to shared-intelligence/handoffs/
6. LOG         → Record changed_functions in handoff
7. VERIFY      → Confirm all done criteria (§11) met
```

**Prohibited:** Skipping steps 4–7. Every task must complete the full sequence.

---

## Cross-References
- Handoff required fields: `CLAUDE.md §5`
- Trigger map: `CLAUDE.md §5a`
- Output schema: `CLAUDE.md §10a`
- Escalation rules: `CLAUDE.md §9`
- Done criteria: `CLAUDE.md §11`
- Team mapping: `.agent/AGENT_SYSTEM.md §1`
- Full agent authority: `orchestrator/agent-registry.md`
- Phase details: `orchestrator/phase-structure-v4.md`
