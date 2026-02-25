# 7-Team Infrastructure Improvement — Charter Reference
> **Project:** Infrastructure Cleanup + Error Tracking System
> **Authority:** CLAUDE.md Section 17 (15 Enterprise Governance Principles)
> **Duration:** 5 hours | **Mode:** Parallel execution with sync checkpoints

---

## Quick Reference: What Each Team Does

### Team A — Business Strategist (Orchestrator Role)
**Responsibility:** Define scope, metrics, success criteria; coordinate all teams; escalation hub

**Deliverables:**
- Infrastructure improvement scope (1 doc)
- Success metrics + OKR (measurable, time-bound)
- Team charters (define each team's scope-in/out)
- Daily escalation reviews (if blockers detected)

**Duration:** Hour 0-1 (scope definition) + ongoing (orchestration)

**Authority:** Can request rework from Teams B-H if misaligned with scope

**Key Rule:** Must read shared-intelligence/ before approving new patterns

---

### Team B — Infrastructure Lead
**Responsibility:** Design new structure; create sub-project governance template; cleanup existing architecture

**Deliverables:**
1. **SUBPROJECT_CLAUDE_TEMPLATE.md** (gates Team C) — Template for future M-005+ projects with:
   - Mandatory `# LAYER X:` import chaining
   - Authority boundary definition
   - Inherited shared-intelligence/ structure
   - Tech stack checklist
   - Success metrics section

2. **Infrastructure structure cleanup** — Reorganize codebase:
   - Consolidate fragmented configs
   - Establish standard module layout
   - Update documentation links

3. **Shared intelligence updates** (mandatory post-task)

**Duration:** Hour 1-2 (template) + Hour 2-3 (cleanup)

**Authority:** Defines technical structure for error tracker (Team C inherits)

**Key Gates:**
- SUBPROJECT_CLAUDE_TEMPLATE.md must be complete before Team C starts
- Team D validates template completeness (11 required sections)

**Key Rule:** Zero breaking changes to existing services (M-001 to M-003 untouched)

---

### Team C — Error Tracking System Implementation
**Responsibility:** Build error tracking/prevention system; verify MCP-only compliance

**Deliverables:**
1. **error_tracker_service.py** — Core error tracking logic:
   - Integrates with backend error logging
   - Analyzes error patterns
   - Prevention recommendations

2. **error_tracker_audit.md** (mandatory QA checkpoint) — Shows:
   - MCP connection diagram (only MCP used)
   - Zero direct SQLite/requests/http imports
   - Test coverage ≥80%

3. **Integration with backend/app.py** — Error tracking endpoint

4. **Shared intelligence updates** (mandatory post-task)

**Duration:** Hour 2-4 (implementation + testing)

**Dependency:** Waits for Team B (SUBPROJECT_CLAUDE_TEMPLATE.md)

**Authority:** Owns error tracking feature; escalates architecture questions to Team B

**Key Gates:**
- **MCP Compliance (Principle #3):** Must pass error_tracker_audit.md validation
- **Quality Gates (Principle #6):** Test coverage ≥80%, lint 0 warnings, type check pass
- **Team D Cross-Validation:** Team D verifies MCP audit before merge

**Key Rule:** Use only MCP connections (no direct DB imports). If need direct DB, request via MCP-04.

---

### Team D — Cross-Validation & Governance
**Responsibility:** Validate all teams' output against governance principles; enforce quality gates; sign-off before merge

**Deliverables:**
1. **QUALITY_GATE_CHECKLIST.md** — Reusable checklist for all teams (shared at Hour 1)

2. **GOVERNANCE_VALIDATION_RUBRIC.md** — Scoring framework (0-3 scale per principle)

3. **TEAM_D_VALIDATION_LOG.md** (shared-intelligence/) — Daily validation records + escalations

4. **Cross-validation reports** — Per-team governance scores + recommendations

5. **Shared intelligence updates** (mandatory post-task)

**Duration:** Hour 2-5 (concurrent with Teams A-G implementation)

**Authority:**
- Can reject merge if governance non-compliant
- Can require rework on Teams A-G
- Escalates unresolvable conflicts to Orchestrator (Team A)

**Key Responsibilities:**
- Hour 2: Deliver checklist + rubric to Teams A-G
- Hour 3: Begin validating Team B (template) + Team C (error tracker)
- Hour 4: Validate Teams E, F, G + integrate merge
- Hour 5: Final approval before Supervisor (you) sign-off

**Key Gates (Cannot Bypass):**
- Principle #3 (MCP-only): Zero direct imports
- Principle #6 (Quality): Coverage ≥80%, lint 0, type check pass
- Principle #9 (Shared Intel): All 4 files updated
- Principle #15 (Reuse-First): Evidence of pattern checking

**Key Rule:** Governance is non-negotiable. If team can't comply, escalate immediately (don't wait until merge).

---

### Team E — CI/CD Hardening & Monitoring
**Responsibility:** Strengthen deployment pipeline; ensure quality gates; setup monitoring for error tracker

**Deliverables:**
1. **CI_CD_POLICY.md** — Security guardrails for pipeline:
   - No `--dangerously-skip-permissions` except isolated environments
   - All quality gates enforced before deploy
   - Secret scan + vulnerability check mandatory

2. **Monitoring setup** — Integration with error tracker:
   - Alert rules for critical errors
   - Dashboard linking error tracking to CI/CD metrics

3. **GitHub Actions hardening** — Secure pipeline config

4. **Shared intelligence updates** (mandatory post-task)

**Duration:** Hour 2-4 (parallel with Team C)

**Dependency:** Works with Team C (error tracker deployment pipeline)

**Authority:** Can block deployment if security gates fail

**Key Gates:**
- Quality gates (Team D validates)
- No secrets in configs
- GitHub Actions signed + verified

**Key Rule:** Every deployment must pass: lint + test + secret scan + governance check. No exceptions.

---

### Team F — Security Audit & Error Log Protection
**Responsibility:** Audit error tracker for security issues; ensure error logs protected (no sensitive data leakage)

**Deliverables:**
1. **Security audit report** — Error tracker security assessment:
   - OWASP Top 10 review
   - Authentication/authorization check
   - Input validation review
   - Secrets in error logs? (check for leaked API keys, passwords)

2. **Error log sanitization rules** — Filter sensitive data from logs:
   - PII removal (names, emails, phone numbers)
   - Credentials masking (API keys, tokens)
   - Payment data filtering (credit cards, SSNs)

3. **Shared intelligence updates** (mandatory post-task)

**Duration:** Hour 3-4 (parallel with implementation)

**Dependency:** Works with Team C (error tracker code review)

**Authority:** Can require code changes if security issues found

**Key Gates:**
- Zero critical vulnerabilities
- Zero PII in error logs
- No unmasked credentials

**Key Rule:** Error logs are sensitive. Review every error message for potential data leakage.

---

### Team G — Cost-Log Restructuring & Performance Analysis
**Responsibility:** Restructure cost-log.md for visibility; optimize token usage; track cost per team

**Deliverables:**
1. **cost-log-summary.md** (new file) — Dashboard view:
   ```
   | Team | Task | Duration (min) | Tokens | Cost | Status |
   |------|------|----------------|--------|------|--------|
   | A | PRD + OKR | 30 | 12,500 | $0.19 | PASS |
   | B | Structure | 120 | 45,000 | $0.68 | IN_PROGRESS |
   ```

2. **cost-log.md archive** — Keep raw append-only log (reference)

3. **Performance analysis** — Token efficiency recommendations:
   - Which tasks were efficient? (tokens/output ratio)
   - Where can future projects optimize?

4. **Shared intelligence updates** (mandatory post-task)

**Duration:** Hour 3-5 (background task, lower priority)

**Dependency:** Consumes cost-log.md entries from hook outputs (PreToolUse, PostToolUse)

**Authority:** Reports to Team A (Orchestrator) if cost overrun detected

**Key Gates:**
- cost-log-summary.md human-readable
- Per-team cost breakdown visible
- Total cost <5% over budget

**Key Rule:** Cost discipline = efficiency. If team over budget, flag early so Team A can adjust scope.

---

### Team H — Telegram Bot Integration (Background Task)
**Responsibility:** Consolidate JARVIS bot + Sonolbot daemon; ensure Telegram notifications work

**Deliverables:**
1. **Consolidation plan** — How to merge JARVIS (Railway) + Sonolbot (local daemon)
   - Single bot token? Or separate?
   - Message routing logic
   - Status notifications for this 7-team project

2. **Integration test** — Verify bot receives notifications from all teams

3. **Shared intelligence updates** (mandatory post-task)

**Duration:** Hour 3-5 (background, lower blocking priority than Teams A-G)

**Dependency:** No hard dependencies; works alongside main teams

**Authority:** Reports status to Team A (Orchestrator)

**Key Gates:**
- Bot responds to commands
- Notifications received from Teams A-G
- No duplicate messages

**Key Rule:** This is background task. Don't let it block main infrastructure work.

---

## Governance Rules (All Teams Read This)

### Rule 1: Read CLAUDE.md Before Any Action
**Requirement:** All teams must read CLAUDE.md Sections 1-6 + Section 17 (15 principles) before starting

**Why:** You're operating under enterprise governance. No exceptions.

**Checklist:**
- [ ] Read CLAUDE.md (this file) — REQUIRED
- [ ] Read orchestrator/README.md — RECOMMENDED
- [ ] Read GOVERNANCE_VALIDATION_REPORT.md — RECOMMENDED
- [ ] Read shared-intelligence/patterns.md — BEFORE implementing (reuse first!)

---

### Rule 2: Update Shared Intelligence Post-Task (Mandatory)
**Requirement:** After every task (Hour 1, 2, 3, 4, 5), update:

1. **shared-intelligence/pitfalls.md**
   - New failure modes discovered: `PF-XXX: [title] — [description] → [prevention]`
   - Example: `PF-007: Error tracker infinite loop — logs same error repeatedly → add deduplication logic`

2. **shared-intelligence/patterns.md**
   - Reusable solutions: `PAT-XXX: [pattern name] — [when to use] → [code/link]`
   - Example: `PAT-009: Error sanitization — remove PII from logs → use regex filters in error_tracker_service.py`

3. **shared-intelligence/decisions.md**
   - Architecture decisions: `ADR-XXXX: [title] — [context] → [decision] → [consequences]`
   - Example: `ADR-0006: MCP-only error tracking — all external connections via MCP → zero direct DB imports`

4. **shared-intelligence/handoffs/[team].md**
   - 1-page summary for next team: "Here's what we did, here's what you need to know"

**Deadline:** Before merging your feature branch (Team D validates)

---

### Rule 3: Governance Compliance = Non-Negotiable
**The 15 Principles are Law:**

- ✅ Principle #2: CLAUDE.md authority (all imports required)
- ✅ Principle #3: MCP-only connections (Team C critical)
- ✅ Principle #6: Quality gates (lint, test, type check)
- ✅ Principle #9: Shared intelligence updates (all teams)
- ✅ Principle #15: Reuse-first (check patterns.md before building)

**If you violate:** Team D will reject merge + request rework. No exceptions.

---

### Rule 4: Feature Branches (Not Worktrees) for This Project
**Requirement:** Create feature branch per team:

```bash
git checkout -b feature/team-a-guidelines
git checkout -b feature/team-b-infrastructure
git checkout -b feature/team-c-error-tracker
# ... etc (7 branches)
```

**Why:** Synchronous infrastructure work is easier to integrate with branches (not worktrees).

**Merge Strategy:**
- No squash (preserve commit history)
- No ff (maintain merge commits for visibility)
- Team D validates + merges each branch

---

### Rule 5: Escalation Path (If Blocked)
**Chain of Command:**

```
You (blocked in Team X)
  ↓ escalate to
Team A (Orchestrator)
  ↓ decides
  ├─ Option 1: Rework (with timeline extension)
  ├─ Option 2: Cut feature (scope reduction)
  ├─ Option 3: Add resources (parallel effort)
  └─ Option 4: Escalate to Supervisor (you) for override
```

**Escalation Template:**
```
To: Team A (Orchestrator)
Subject: [BLOCKED] [Team X] — [Issue]

Status: BLOCKED since [Time]
Blocker: [Specific issue preventing progress]
Root Cause: [Why it happened]
Attempted Solutions: [What we tried]
Recommendation: [Fix needed to unblock]

ETA for resolution: [Estimate]
Impact to timeline: [X hours delay]
```

---

### Rule 6: Quality Gates Before Merge
**Checklist (from Team D):**

- [ ] Code lint: 0 warnings
- [ ] Type check: pass (mypy, tsc)
- [ ] Test coverage: ≥80%
- [ ] Secrets scan: clean (no hardcoded credentials)
- [ ] CLAUDE.md imports: present + complete
- [ ] Shared intelligence: updated (pitfalls, patterns, decisions, handoff)
- [ ] MCP audit (if applicable): completed + zero violations
- [ ] Orchestrator approval: obtained

**If ANY fail:** Cannot merge. Team D will request rework.

---

### Rule 7: Token Budget Discipline
**Total Budget:** 200K tokens (for all 7 teams)

**Allocation (estimate):**
- Team A (Orchestrator): 10K tokens
- Team B (Infrastructure): 30K tokens
- Team C (Error Tracker): 50K tokens (main feature)
- Team D (Cross-Validation): 20K tokens
- Team E (CI/CD): 25K tokens
- Team F (Security): 20K tokens
- Team G (Cost-Log): 20K tokens
- Team H (Telegram Bot): 10K tokens
- **Reserve:** 15K tokens (buffer for rework)

**Rule:** If team exceeds allocation by >10%, escalate to Team A (Orchestrator).

---

## Timeline Overview

```
Hour 0-1: Team A (Orchestrator) defines scope + charters
Hour 1-2: Team B creates SUBPROJECT_CLAUDE_TEMPLATE.md (gates Team C)
Hour 2-3: Team C starts error tracker (with MCP audit)
Hour 2-5: Teams D, E, F, G work in parallel
Hour 4-5: Team D cross-validates all outputs
Hour 5-6: Final merge + Supervisor approval

Sync Checkpoints:
  Hour 2: Team B template must be complete
  Hour 3: Team C error tracker code + audit
  Hour 4: Final quality gate validation
  Hour 5: Ready for merge + deployment
```

---

## Emergency Contacts (Escalation)

| Role | Team | Escalates To | If Blocked |
|------|------|--------------|-----------|
| Team A | Orchestrator | You (Supervisor) | Timeline/scope decision |
| Team B | Infrastructure | Team A | Structure conflict with error tracker |
| Team C | Error Tracker | Team B | Structure doesn't fit design |
| Team D | Cross-Validation | Team A | Governance conflict unresolvable |
| Team E | CI/CD | Team A | Pipeline security issue |
| Team F | Security | Team A | Critical vulnerability found |
| Team G | Cost-Log | Team A | Budget overrun detected |
| Team H | Telegram Bot | Team A | Integration not working |

---

## Success Criteria (Final Sign-Off)

Supervisor (you) approves deployment IF:

✅ All 7 teams delivered + passed Team D validation
✅ All shared-intelligence files updated (pitfalls, patterns, decisions, cost-log)
✅ Zero critical governance violations (Principles 2, 3, 6, 9, 15)
✅ Test coverage ≥80% across all teams
✅ Cost <5% over budget
✅ Error tracker fully integrated + tested
✅ Documentation complete (README, deployment guide, API docs)

---

**Document:** TEAM_CHARTER_001
**Authority:** CLAUDE.md Section 17 (15 Enterprise Governance Principles)
**Status:** READY FOR PARALLEL EXECUTION
**Last Updated:** 2026-02-25
