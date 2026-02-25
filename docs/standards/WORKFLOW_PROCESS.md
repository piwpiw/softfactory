# Unified Workflow Process
> **Version:** 2.0 | **Governance:** v3.0 | **Updated:** 2026-02-25

**Purpose:** Single source of truth for all agent workflows, task handoffs, and decision gates.

---

## 1. Project Initiation Workflow

### **Step 1: Project Proposal**
**Input:** User provides project description
**Owner:** Orchestrator Agent
**Time:** 5 minutes

```
IF user_input.clarity < HIGH:
  → Ask 2 clarifying questions
  → Wait max 3 minutes for response
ELSE:
  → Parse requirements
  → Identify risks
  → Estimate scope
  → Output: Structured brief
```

**Output Deliverable:**
- Structured requirements (JSON/markdown)
- Risk register (3-5 key risks)
- Estimated effort (hours)
- Recommended agent sequence

**Gate:** Orchestrator approves structured brief → advance

---

### **Step 2: Pre-Flight Checks**
**Owner:** Orchestrator + Security Auditor
**Time:** 10 minutes

```
PARALLEL checks:
├─ Tech stack validation (matches platform standards)
├─ Security threat model (OWASP Top 10)
├─ Token budget allocation (200K limit)
├─ Resource availability (all required agents ready)
└─ Database/external dependency review (MCP registry compliance)
```

**Blockers:**
- ❌ Unauthorized external API → Propose MCP wrapper or defer
- ❌ Security risk → Return to requirements phase
- ❌ Token budget exceeded → Offer scope reduction options

**Gate:** All checks PASS → advance to Phase 1

---

## 2. Requirements Phase Workflow (Agent A: Business Strategist)

### **Inputs**
- Structured brief (from orchestrator)
- Shared intelligence (pitfalls.md, patterns.md, decisions.md)
- Existing codebase (if enhancement project)

### **Core Tasks**
1. **Write PRD** (Product Requirements Document)
   - Problem statement
   - User personas (3-5)
   - User stories with acceptance criteria
   - Non-functional requirements (performance, security, scalability)
   - Success metrics (OKR format: Objective + Key Results)

2. **Create User Story Map**
   - Epic/Feature/Story hierarchy
   - Priority ranking (WSJF: Value/Size/Risk/Duration)
   - Dependency graph (which stories block others)

3. **Validate with Architecture** (Handoff-ready)
   - API contract overview (what endpoints needed)
   - Data entities (preliminary list)
   - Integration points (existing services)

### **Output Deliverable** (→ repo)
```
docs/
├── [project]/PRD.md
├── [project]/user-stories.md
└── [project]/success-metrics.md
```

### **Quality Gate**
- [ ] All user stories have acceptance criteria
- [ ] Non-functional requirements measurable
- [ ] OKR structure correct (1 Objective, 3-5 Key Results)
- [ ] Dependency graph complete

### **Handoff to Agent B**
- Write: `shared-intelligence/handoffs/requirements-to-architecture.md`
  - What's done (PRD, stories)
  - What's assumed (tech stack, constraints)
  - What needs validation (API contracts, data model feasibility)

**Gate:** Agent B reviews handoff → approves or returns for rework

---

## 3. Architecture & Design Workflow (Agent B: Architect)

### **Inputs**
- PRD + user stories (from Agent A)
- Handoff notes from Agent A
- Shared intelligence (past architecture decisions)

### **Core Tasks**
1. **System Architecture**
   - High-level component diagram
   - Data flow (request → response)
   - External integrations (MCP servers, APIs)
   - Deployment topology (Dev/Staging/Prod)

2. **API Specification**
   - REST endpoints (or GraphQL schema)
   - Request/response schemas (JSON examples)
   - Error handling (HTTP status codes, error messages)
   - Rate limiting & security (auth, CORS, encryption)

3. **Data Model**
   - Entity-relationship diagram
   - Database schema (tables, columns, constraints)
   - Indexing strategy
   - Migration plan (if existing DB modified)

4. **Security Threat Model**
   - OWASP Top 10 mapping
   - Data sensitivity classification
   - Access control matrix
   - Encryption requirements (at-rest, in-transit)

5. **Non-Functional Design**
   - Performance budget (response time, throughput)
   - Scalability plan (horizontal/vertical)
   - Reliability & disaster recovery
   - Monitoring & alerting strategy

### **Output Deliverable** (→ repo)
```
docs/
├── [project]/ARCHITECTURE.md
├── [project]/API_SPEC.md
├── [project]/DATABASE_SCHEMA.md
└── [project]/SECURITY_THREAT_MODEL.md
```

### **Quality Gate**
- [ ] System diagram is clear (can explain in 5 min)
- [ ] API spec is complete (every endpoint documented)
- [ ] Database schema is normalized
- [ ] Security model addresses OWASP Top 10

### **Handoff to Agent C**
- Write: `shared-intelligence/handoffs/architecture-to-development.md`
  - Architecture approved
  - API contracts finalized
  - Database schema ready (any special setup needed?)
  - Development priorities (core modules first)

**Gate:** Agent C reviews architecture → asks clarifying questions or begins coding

---

## 4. Development Workflow (Agent C: Development Lead)

### **Inputs**
- Architecture + API spec + database schema
- Handoff notes from Agent B
- Shared intelligence (coding patterns, pitfalls)

### **Core Tasks**
1. **Setup & Environment**
   - Initialize project structure
   - Install dependencies
   - Configure database (migrations, seed data)
   - Setup testing framework (pytest, Jest, etc.)

2. **Core Module Development** (Parallel/Sequential by dependency)
   ```
   For each module:
     ├─ Code implementation (15-25 min)
     ├─ Unit tests (5-10 min)
     ├─ Code review (self or peer) (5 min)
     ├─ Lint + type check (2 min)
     └─ Commit to feature branch

   After all modules:
     ├─ Integration testing (10 min)
     ├─ API endpoint validation (5 min)
     └─ Database integrity check (5 min)
   ```

3. **Quality Checklist Per Module**
   - [ ] Code follows project style guide (linting: 0 warnings)
   - [ ] Typed (TypeScript/Python type hints: 100%)
   - [ ] Unit tested (coverage ≥80%)
   - [ ] No hardcoded secrets or test data in code
   - [ ] Comments on complex logic
   - [ ] API errors documented

4. **Documentation**
   - Code comments (why, not what)
   - README for setup & running tests
   - API documentation (auto-generated from spec)
   - Known limitations (if any)

### **Output Deliverable** (→ repo)
```
src/               (Implementation)
tests/             (Unit & integration tests)
docs/
├── [project]/SETUP.md
├── [project]/API_DOCS.md
└── [project]/DEVELOPER_GUIDE.md
```

### **Integration Gate**
- [ ] All unit tests pass (100%)
- [ ] All lint checks pass (0 warnings)
- [ ] Type checking passes (no `any` types)
- [ ] Integration tests pass
- [ ] API endpoints match spec

### **Handoff to Agent D**
- Write: `shared-intelligence/handoffs/development-to-qa.md`
  - Code committed (branch + tag)
  - Test coverage report (% per module)
  - Known issues or TODOs (if any)
  - Setup instructions for QA (how to run tests, start server)

**Gate:** Agent D reviews code → runs tests locally → begins QA

---

## 5. Quality Assurance Workflow (Agent D: QA Engineer)

### **Inputs**
- Complete code implementation
- Test report (from Agent C)
- Handoff notes from Agent C
- PRD + acceptance criteria (from Agent A)

### **Core Tasks**
1. **Functional Testing**
   - Execute all acceptance criteria (from user stories)
   - Test happy path + edge cases + error scenarios
   - Database integrity (data consistency, constraints)
   - API response validation (schema, status codes)

2. **System Testing**
   - End-to-end workflows (simulating real user journeys)
   - Multi-step transactions
   - Concurrent user scenarios
   - Data cleanup & rollback

3. **Non-Functional Testing**
   - Performance (response time, throughput)
   - Security (input validation, SQL injection, XSS, CSRF)
   - Scalability (load testing, if applicable)
   - Accessibility (if web UI)

4. **Regression Testing**
   - Execute automated test suite (≥80% coverage)
   - No breaking changes to existing features
   - Database schema migration validation

### **Test Report** (→ repo)
```
docs/
├── [project]/TEST_REPORT.md
│   ├─ Functional tests: X/X PASSED
│   ├─ System tests: X/X PASSED
│   ├─ Bug report (Critical: 0, High: 0, Medium: N, Low: N)
│   └─ Coverage report
└── [project]/KNOWN_ISSUES.md (if any)
```

### **Quality Gate (MANDATORY)**
- [ ] 0 Critical bugs
- [ ] 0 High-priority bugs (unless explicitly deferred)
- [ ] Test coverage ≥80%
- [ ] All acceptance criteria met
- [ ] Performance within budget
- [ ] Security scan clean

### **Handoff to Agent E**
- Write: `shared-intelligence/handoffs/qa-to-devops.md`
  - Test report summary
  - Bug fixes applied (with commit hashes)
  - Deployment checklist (from QA perspective)
  - Known issues (if deferred)

**Gate:** Agent E reviews QA report → proceeds to deployment

---

## 6. Deployment Workflow (Agent E: DevOps)

### **Inputs**
- Tested & approved code
- QA report (from Agent D)
- Handoff notes from Agent D
- Shared infrastructure (MCP servers, databases)

### **Core Tasks**
1. **Staging Deployment**
   - Deploy to staging environment (replica of production)
   - Run smoke tests (critical path only)
   - Verify monitoring & alerting
   - Database migration validation (if applicable)

2. **Documentation**
   - Deployment runbook (step-by-step)
   - Rollback procedure (if needed)
   - Monitoring dashboard (what to watch)
   - Incident response (escalation path)

3. **Production Readiness**
   - Infrastructure-as-Code (Docker, Kubernetes, IaC)
   - Environment variables (dev vs. staging vs. prod)
   - Secrets management (encrypted, audited)
   - Backup & recovery plan

4. **Post-Deployment**
   - Health checks (is service up? Is DB reachable?)
   - Monitoring setup (logs, metrics, traces)
   - Alerting setup (thresholds, notification channels)

### **Deployment Artifact** (→ repo)
```
deploy/
├── Dockerfile
├── docker-compose.yml
├── kubernetes.yaml
├── runbook.md
└── monitoring-dashboard.json
```

### **Deployment Gate**
- [ ] Staging tests pass (100%)
- [ ] Runbook is clear & tested
- [ ] Rollback plan documented
- [ ] Monitoring is live
- [ ] Secrets are encrypted
- [ ] Team trained (if new service)

### **Handoff to Orchestrator**
- Write: `shared-intelligence/handoffs/devops-to-orchestrator.md`
  - Deployment status (ready for production)
  - Risk assessment (any known issues?)
  - Rollback readiness
  - Monitoring alarms configured

**Gate:** Orchestrator + Product Manager → Go/No-Go decision

---

## 7. Post-Deployment Workflow

### **Orchestrator Validation**
- [ ] All deliverables complete
- [ ] All quality gates passed
- [ ] Documentation is accurate
- [ ] Team knows how to operate service

### **Production Monitoring** (First 24-48 hours)
- Monitor error rates, latency, resource usage
- Have runbook ready for quick response
- Plan post-incident review (if any issues)

### **Success Closure**
- Update `shared-intelligence/decisions.md` with final outcomes
- Log lessons learned → `shared-intelligence/pitfalls.md`
- Promote reusable patterns → `shared-intelligence/patterns.md`
- Archive handoff notes

---

## 8. Handoff Protocol (Standard Template)

All handoffs follow this structure:

```markdown
# Handoff: [FROM_AGENT] → [TO_AGENT]
**Date:** [DATE] | **Project:** [NAME] | **Task:** [TASK_ID]

## What's Done
- [ ] [Deliverable 1]
- [ ] [Deliverable 2]
- [ ] [Deliverable 3]

## What's Assumed
- Assumption 1
- Assumption 2

## What Needs Validation
- Validation point 1
- Validation point 2

## Questions for Next Agent
- Q1: [Question]
- Q2: [Question]

## Artifacts
- [Location of PRD, code, tests, etc.]

## Blocking Issues (if any)
- [Issue description + recommended action]
```

---

## 9. Decision Gate Protocol

**Every major decision goes through:**

1. **Proposer writes:** One-page proposal (problem, options, recommendation)
2. **Stakeholders review:** 5-min async window
3. **Orchestrator decides:** Approve, ask more info, or reject
4. **Log in ADR:** `shared-intelligence/decisions.md` (ADR format)
5. **Notify affected agents:** Async message in consultation bus

**Time-critical decisions (>30 min impact):**
- Escalate immediately
- Orchestrator makes call
- Document "Decision made under time pressure"

---

## 10. Failure & Recovery Workflow

### **If Task Fails**
1. **Log failure** → `shared-intelligence/decisions.md` (root cause + context)
2. **Retry with modification** (max 3 retries)
3. **If still failing** → Escalate to orchestrator
4. **Orchestrator decides:** Fallback to backup agent, task deferral, or scope cut

### **If Quality Gate Fails**
1. **Agent fixes issue** (if agent-level problem)
2. **Re-run quality gate** (automated if possible)
3. **If persistent** → Escalate to Product Manager + Orchestrator

### **If Production Issue Post-Deployment**
1. **Incident lead:** Gather facts (what happened, user impact, timing)
2. **Rollback or hotfix?** (Orchestrator decision)
3. **Root cause analysis:** Log in `shared-intelligence/decisions.md`
4. **Prevention:** Add to `shared-intelligence/pitfalls.md`

---

## 11. Cross-Project Synchronization

**For dependent projects:**

```
Project A —[API]→ Project B
           \[Data]→ Project C

Sync points:
1. Project A: API spec + mock server (for B & C to test against)
2. Project B: Ready to integrate (calls A)
3. Project C: Ready to integrate (reads A data)
4. Integration test: All 3 projects together
```

**Protocol:**
- Spec-first: A must publish API spec before B/C development
- Mock first: A provides mock server for parallel development
- Integration late: Real integration only after both sides ready
- Test together: E2E tests must validate all 3 projects

---

## 12. Knowledge Preservation (Mandatory)

After EVERY task completion:

1. **Pitfall added** → `shared-intelligence/pitfalls.md`
   - What went wrong (if anything)
   - Prevention rule for future

2. **Pattern added** (if reusable) → `shared-intelligence/patterns.md`
   - Pattern name
   - Problem it solves
   - Code example (link to repo)

3. **Decision logged** → `shared-intelligence/decisions.md`
   - What was decided
   - Why (alternatives considered)
   - When + by whom
   - Reference to related artifacts

4. **Cost logged** → `shared-intelligence/cost-log.md`
   - Tokens used (per phase)
   - Estimated cost
   - Efficiency ratio (output value / cost)

---

**Version history:**
- v1.0: 2026-02-22 (Initial phase-based workflow)
- v2.0: 2026-02-25 (Governance v3.0 alignment — handoff protocol, shared intelligence obligations)

**Next:** Integrate with orchestrator automation engine
