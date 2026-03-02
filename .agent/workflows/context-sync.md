# Context Sync Workflow

> **Version:** 2026-03-02 | **Status:** ACTIVE | **Parent:** CLAUDE.md §10c
> **Trigger:** Any policy change in CLAUDE.md
> **Purpose:** Keep all `.agent/` docs synchronized with CLAUDE.md

---

## Pre-Sync Checklist

- [ ] Identify which CLAUDE.md sections changed (§0–§12)
- [ ] Document reason for change
- [ ] Check backward compatibility with existing handoffs

---

## Sync Matrix

Which `.agent/` doc to update when a CLAUDE.md section changes:

| CLAUDE.md Section | AGENT_SYSTEM.md | CONTEXT_ENGINE.md | AGENT_PROTOCOLS.md | COST_RULES.md |
|-------------------|:-:|:-:|:-:|:-:|
| §0 Meta Policy | ✓ version | ✓ version | ✓ version | ✓ version |
| §1 Imports | — | — | — | — |
| §2 Technical Context | ✓ MCP servers | ✓ file hierarchy | — | — |
| §3 MCP Runtime | — | ✓ window rules | — | ✓ read costs |
| §4 Context Loading | — | ✓ tag definitions | — | — |
| §5 Handoff Contract | — | — | ✓ payload schema | — |
| §5a Trigger Map | ✓ team routing | — | ✓ trigger table | — |
| §6 ReAct Cycle | ✓ lifecycle | — | — | — |
| §8 Governance Phase | ✓ lifecycle | — | ✓ phase transitions | — |
| §9 Roles/Escalation | ✓ escalation hierarchy | — | ✓ escalation chains, RACI | — |
| §10 Quality Gates | — | — | — | ✓ budget rules |
| §10a Output Schema | — | — | ✓ handoff schema | — |
| §10b Prohibited | ✓ error handling | ✓ prohibited loads | — | ✓ prohibited patterns |
| §12 15 Principles | (all — review alignment) | (all) | (all) | (all) |

---

## Sync Procedure

### Step 1: Update Versions
```
All .agent/*.md → update Version line to match CLAUDE.md version date
```

### Step 2: Update Affected Docs
Follow the sync matrix above. Only update docs where ✓ appears.

### Step 3: Verify Cross-References
- [ ] All `.agent/` docs reference correct CLAUDE.md section numbers
- [ ] No circular references between docs
- [ ] All `orchestrator/` references still valid
- [ ] All `shared-intelligence/` paths still exist

### Step 4: Verify Orchestrator Alignment
- [ ] `orchestrator/agent-registry.md` — team definitions match §5a
- [ ] `orchestrator/mcp-registry.md` — server list matches §2
- [ ] `orchestrator/phase-structure-v4.md` — phases match §8

### Step 5: Commit
```bash
git add CLAUDE.md .agent/
git commit -m "chore(governance): sync policy v[YYYY-MM-DD]"
```

---

## Post-Sync Validation

- [ ] All 4 `.agent/` docs internally consistent
- [ ] CLAUDE.md §0–§12 all have at least one `.agent/` doc referencing them
- [ ] Version timestamps match across all files
- [ ] No orphaned references (pointing to deleted sections)

---

## Rollback

If sync introduces inconsistency:
1. Revert commit: `git revert HEAD`
2. Document issue in `shared-intelligence/pitfalls.md`
3. Fix root cause before re-syncing

---

## Cross-References
- Trigger: `CLAUDE.md §10c`
- Agent docs: `.agent/AGENT_SYSTEM.md`, `CONTEXT_ENGINE.md`, `AGENT_PROTOCOLS.md`, `COST_RULES.md`
- Orchestrator docs: `orchestrator/agent-registry.md`, `mcp-registry.md`, `phase-structure-v4.md`
