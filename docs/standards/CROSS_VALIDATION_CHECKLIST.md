# Cross-Validation Checklist (Master Template)
> **Version:** 2.0 | **Governance:** v3.0 | **Updated:** 2026-02-25

**Purpose:** Single universal checklist for validating all project deliverables across all phases and agents. Use this to catch issues early.

---

## Pre-Execution Checklist

**Owner:** Orchestrator | **When:** Before project phase starts
**Time:** 5 minutes | **Gate:** PASS = advance, FAIL = escalate

### **Governance**
- [ ] Project has valid CLAUDE.md (inherited from master)
- [ ] All required agents assigned (with authority matrix)
- [ ] Scope is clearly defined (scope-in vs. scope-out)
- [ ] Success metrics are measurable

### **Resources**
- [ ] Token budget allocated (verified against 200K limit)
- [ ] All required MCP servers available (per `orchestrator/mcp-registry.md`)
- [ ] No unauthorized external APIs
- [ ] Database/infrastructure ready

### **Risks**
- [ ] Risk register created (3-5 risks identified)
- [ ] Mitigation plans documented
- [ ] Security pre-review scheduled (if applicable)
- [ ] Escalation path defined

---

## Phase 1: Requirements Validation

**Owner:** Agent A (Business Strategist) + Agent B (Architect) review
**When:** After Agent A completes PRD and user stories
**Time:** 10 minutes | **Gate:** All checks PASS or defer to Phase 2

### **PRD Quality**
- [ ] **Clarity:** Problem statement is 1-2 sentences (clear intent)
- [ ] **Completeness:** All major features listed (no ambiguity)
- [ ] **User-centric:** At least 3-5 personas defined
- [ ] **Measurable:** Success metrics in OKR format (Objective + 3-5 KRs)

### **User Stories**
- [ ] **Format correct:** "As a [persona], I want [feature], so that [benefit]"
- [ ] **Acceptance criteria:** Each story has 3-5 clear, testable criteria
- [ ] **Priority ranked:** WSJF (Value/Size/Risk/Duration) applied
- [ ] **Dependencies mapped:** Which stories block others?

### **Non-Functional Requirements**
- [ ] **Performance:** Response time target (e.g., < 200ms)
- [ ] **Scalability:** Expected users + concurrent sessions
- [ ] **Security:** Data classification + encryption requirements
- [ ] **Availability:** Uptime SLA (if applicable)

### **Assumptions**
- [ ] **Tech stack:** Approved against platform standards
- [ ] **Integrations:** All external services listed (MCP-approved)
- [ ] **Constraints:** Budget, timeline, team size realistic
- [ ] **Unknowns:** Any risky assumptions documented

**If FAIL:** Return to Agent A for rework, re-check in 30 min

---

## Phase 2: Architecture Validation

**Owner:** Agent B (Architect) + Agent C (Dev Lead) + Agent E (DevOps) review
**When:** After Agent B completes architecture, API spec, data model
**Time:** 15 minutes | **Gate:** All checks PASS

### **System Architecture**
- [ ] **Diagram clear:** Can explain in 5 minutes to someone unfamiliar
- [ ] **Component decoupling:** Modules have clear boundaries
- [ ] **External integrations:** All MCP servers listed (no ad-hoc APIs)
- [ ] **Deployment topology:** Dev/Staging/Prod architecture shown
- [ ] **High-availability plan:** If critical service, redundancy clear

### **API Design**
- [ ] **REST compliant:** Proper use of HTTP methods (GET, POST, PUT, DELETE)
- [ ] **Versioning:** API version strategy (v1, v2, etc.)
- [ ] **Error handling:** Standard error codes (400, 401, 403, 404, 500)
- [ ] **Security:** Auth (JWT/OAuth), CORS, rate limiting defined
- [ ] **Documentation:** Every endpoint has request/response schema

### **Data Model**
- [ ] **Normalization:** Database schema follows normalization rules (no redundancy)
- [ ] **Indexing:** Critical queries have indexes
- [ ] **Constraints:** Primary keys, foreign keys, unique constraints present
- [ ] **Scalability:** Schema supports projected data growth (2x, 10x)
- [ ] **Migration plan:** If modifying existing DB, migration script ready

### **Security Threat Model**
- [ ] **OWASP Top 10:** All 10 risks addressed
  - [ ] Broken Access Control (auth/authorization clear)
  - [ ] Cryptographic Failures (encryption at-rest, in-transit)
  - [ ] Injection (SQL, NoSQL, command injection mitigations)
  - [ ] Insecure Design (threat model documented)
  - [ ] Security Misconfiguration (hardening checklist)
  - [ ] Vulnerable Components (dependency versions tracked)
  - [ ] Authentication Failures (password policy, MFA, session mgmt)
  - [ ] Software & Data Integrity (code signing, supply chain)
  - [ ] Logging & Monitoring (audit trails, alerting)
  - [ ] SSRF (server-side request forgery mitigation)
- [ ] **Data sensitivity:** Classification (public, internal, confidential, restricted)
- [ ] **Compliance:** GDPR, HIPAA, PCI-DSS, etc. (if applicable)

### **Performance & Scalability**
- [ ] **Response time:** API endpoints within budget (e.g., < 200ms p95)
- [ ] **Throughput:** Expected requests/second documented
- [ ] **Resource usage:** Memory, CPU, disk footprint estimated
- [ ] **Caching strategy:** Redis/CDN/browser cache used where applicable
- [ ] **Load testing plan:** Performance validation approach

**If FAIL:** Return to Agent B, re-validate with Agent C, re-check in 1 hour

---

## Phase 3: Development Validation (Per Module)

**Owner:** Agent C (Dev Lead) + Code review peer
**When:** After each module implementation
**Time:** 5 minutes per module | **Gate:** Code passes before merge

### **Code Quality**
- [ ] **Linting:** `npm run lint` or equivalent = 0 warnings
- [ ] **Typing:** No `any` types, 100% typed (TypeScript/Python)
- [ ] **Style:** Follows project style guide (indentation, naming)
- [ ] **Comments:** Complex logic has "why" comments (not "what")
- [ ] **DRY:** No copy-paste code (≤5% duplication)

### **Testing**
- [ ] **Unit tests:** Coverage ≥80% for module
- [ ] **Test quality:** Tests are isolated, deterministic, fast
- [ ] **Mocking:** External dependencies (DB, API) are mocked
- [ ] **Edge cases:** Null, empty, negative, max value tested
- [ ] **Error scenarios:** Exception handling tested

### **Security**
- [ ] **Secrets:** No hardcoded secrets, API keys, passwords
- [ ] **Input validation:** User input sanitized + validated
- [ ] **SQL injection:** Parameterized queries or ORM used
- [ ] **XSS prevention:** Output escaped (if web UI)
- [ ] **CSRF tokens:** Present if state-changing operations

### **Performance**
- [ ] **Complexity:** Cyclomatic complexity ≤10
- [ ] **Algorithms:** Efficient (no N² loops, no unnecessary recursion)
- [ ] **DB queries:** Indexed, no N+1 problems
- [ ] **Memory:** No obvious leaks (reasonable allocation)

### **Documentation**
- [ ] **Function signatures:** Docstring with params, return, exceptions
- [ ] **Architecture decisions:** WHY this approach (link to ADR)
- [ ] **Setup & testing:** README explains how to run tests
- [ ] **API docs:** Auto-generated from spec (no manual out-of-sync docs)

**If FAIL:** Agent C fixes issue, re-runs checklist, then commits

---

## Phase 4: Integration Validation

**Owner:** Agent C (Dev Lead)
**When:** After all modules complete
**Time:** 10 minutes | **Gate:** All integration tests PASS

### **Module Integration**
- [ ] **API contract:** All endpoints match spec exactly
- [ ] **Database:** Schema migrates successfully, no data loss
- [ ] **Authentication:** Auth flow works end-to-end
- [ ] **Error propagation:** Errors are properly handled (no silent failures)
- [ ] **Configuration:** Dev/staging/prod configs work correctly

### **System Integration**
- [ ] **MCP servers:** All required servers are reachable
- [ ] **External services:** Integrations with 3rd-party APIs work (or mocked)
- [ ] **Event propagation:** Async events/webhooks work
- [ ] **Concurrency:** Multiple simultaneous requests handled correctly
- [ ] **Data consistency:** Database transactions are ACID

### **Performance Baseline**
- [ ] **Response time:** API endpoints meet p95 target
- [ ] **Throughput:** Load test shows expected requests/second capacity
- [ ] **Resource usage:** CPU, memory within acceptable limits
- [ ] **Monitoring:** Metrics/logs are being collected

**If FAIL:** Agent C debugs + fixes, re-runs checklist

---

## Phase 5: QA Validation

**Owner:** Agent D (QA Engineer)
**When:** After integration tests pass
**Time:** 15 minutes | **Gate:** All tests PASS, 0 critical bugs

### **Functional Testing**
- [ ] **Happy path:** All primary user workflows work
- [ ] **Acceptance criteria:** Every user story's criteria verified
- [ ] **Edge cases:** Boundary conditions tested (0, -1, max int, etc.)
- [ ] **Error scenarios:** Invalid input, network failures, permission denied tested
- [ ] **Data integrity:** Database constraints enforced (no corrupt data)

### **System Testing**
- [ ] **End-to-end workflows:** Multi-step user journeys tested
- [ ] **Concurrent users:** Multiple simultaneous users don't interfere
- [ ] **Transactions:** Multi-step operations are atomic
- [ ] **Recovery:** System recovers from network/DB failures
- [ ] **Upgrades:** Schema migrations from previous versions work

### **Non-Functional Testing**
- [ ] **Performance:** Load test shows >= target throughput
- [ ] **Security:** SQL injection, XSS, CSRF test vectors repelled
- [ ] **Accessibility:** (If web) WCAG 2.1 AA compliance checked
- [ ] **Localization:** (If multi-language) All strings translated
- [ ] **Browser/device support:** Works on target browsers/devices

### **Regression Testing**
- [ ] **Existing features:** No regressions (automated test suite passes)
- [ ] **Database:** Existing data still valid post-migration
- [ ] **Integrations:** External service integrations unaffected

### **Bug Tracking**
- [ ] **Critical (blocker):** 0 (if any found, fix before approval)
- [ ] **High (major feature broken):** 0 (if any found, fix or defer with approval)
- [ ] **Medium (minor feature issue):** Max 3 (logged for backlog)
- [ ] **Low (nice-to-have fixes):** Max 5 (logged for backlog)

### **Test Report**
- [ ] **Coverage:** Summary of what was tested
- [ ] **Results:** Pass/fail counts per test suite
- [ ] **Known issues:** Documented (if deferred)
- [ ] **Recommendations:** Any cleanup/optimization suggestions

**If FAIL (critical/high bugs):** Return to Agent C, fix, re-test

---

## Phase 6: Security Validation

**Owner:** Agent E-Security (or external auditor)
**When:** After Phase 5 QA passes
**Time:** 15 minutes | **Gate:** 0 critical vulnerabilities

### **OWASP Top 10 Re-Verification**
- [ ] **A01: Broken Access Control** → Auth matrix correct, no privilege escalation
- [ ] **A02: Cryptographic Failures** → Encryption in-transit (HTTPS), at-rest
- [ ] **A03: Injection** → Parameterized queries, no eval/exec on user input
- [ ] **A04: Insecure Design** → Threat model reviewed, risks mitigated
- [ ] **A05: Security Misconfiguration** → Security headers present (HSTS, CSP, X-Frame-Options)
- [ ] **A06: Vulnerable & Outdated Components** → Dependency audit (npm audit, snyk)
- [ ] **A07: Identification & Authentication Failures** → Password policy, session timeout, MFA
- [ ] **A08: Software & Data Integrity Failures** → Code signed, dependencies verified
- [ ] **A09: Logging & Monitoring Failures** → Audit trail present, alerts configured
- [ ] **A10: SSRF** → External URL validation implemented

### **Secrets Management**
- [ ] **No hardcoded secrets** in code/config (secret scan passed)
- [ ] **Env var rotation:** Secrets rotated per environment
- [ ] **Access control:** Only authorized services/humans can access secrets

### **Compliance**
- [ ] **GDPR** (if applicable): Data minimization, consent, right-to-delete
- [ ] **HIPAA** (if applicable): Encryption, audit logs, access control
- [ ] **PCI-DSS** (if applicable): Card data never stored/logged
- [ ] **Industry-specific:** Any other standards met

### **Incident Response**
- [ ] **Runbook:** How to respond to security incidents documented
- [ ] **Escalation:** Security issue escalation path clear
- [ ] **Post-incident:** Root cause analysis & prevention plan process defined

**If FAIL:** Blocking issue, must fix before deployment

---

## Phase 7: Deployment Validation

**Owner:** Agent E (DevOps) + Agent D (QA for smoke tests)
**When:** After all previous phases pass
**Time:** 15 minutes | **Gate:** Staging deployment successful

### **Staging Deployment**
- [ ] **Infrastructure:** Docker/IaC tested (infrastructure valid)
- [ ] **Database:** Migrations tested (data integrity post-migration)
- [ ] **Secrets:** Encrypted secrets deployed correctly
- [ ] **Monitoring:** Logs, metrics, traces being collected
- [ ] **Smoke tests:** Critical path works end-to-end

### **Runbook & Documentation**
- [ ] **Deployment steps:** Clear, tested, no manual guess work
- [ ] **Rollback plan:** How to revert if issues found
- [ ] **Configuration:** All config variables documented (dev vs. prod differences)
- [ ] **Team training:** Team knows how to operate service

### **Monitoring & Alerting**
- [ ] **Health checks:** Service liveness endpoint working
- [ ] **Metrics:** CPU, memory, request rate, error rate visible
- [ ] **Alerts:** Thresholds set (>5% error rate, >2s latency, etc.)
- [ ] **Dashboard:** Operations team has visibility into service

### **Production Readiness**
- [ ] **Capacity:** Server has enough resources (2x load expected)
- [ ] **Backup/recovery:** Backup strategy in place
- [ ] **Disaster recovery:** RTO/RPO (recovery time/point objectives) defined
- [ ] **Compliance:** Prod environment meets all regulatory requirements

**If FAIL:** Return to Agent E, fix infrastructure/config, re-test

---

## Post-Deployment Validation

**Owner:** Orchestrator + Ops team
**When:** After production deployment, monitor for 24-48 hours
**Time:** Continuous | **Gate:** No critical issues, normal error rates

### **Health Check (First 1 hour)**
- [ ] **Service up:** Health check endpoint returns 200
- [ ] **Databases:** All DB connections healthy
- [ ] **External services:** Integrations working
- [ ] **Error rate:** Normal (<0.1% errors)
- [ ] **Latency:** P95 response time within budget

### **Monitoring (First 24 hours)**
- [ ] **Trends:** CPU/memory stable (no memory leak)
- [ ] **Alerts:** No false positives
- [ ] **User feedback:** No complaints in tickets/chat
- [ ] **Logs:** No unexpected errors or warnings
- [ ] **Database size:** Growing at expected rate (not exploding)

### **Success Closure**
- [ ] **Feature flag:** If using feature flags, gradually ramp up (25% → 50% → 100%)
- [ ] **Incident log:** Any issues encountered + resolutions documented
- [ ] **Root cause analysis:** If problems, RCA done + preventive measures added to pitfalls
- [ ] **Metrics:** Actual vs. expected performance compared
- [ ] **Team debrief:** Lessons learned captured → shared-intelligence

---

## Checklist Administration

### **Using This Checklist**

1. **Select phase:** Choose the relevant phase above
2. **Copy relevant section:** Copy into your task description
3. **Fill in as you go:** Check off items as you validate
4. **When complete:** PASS = advance, FAIL = log issue + rework
5. **Archive:** Keep completed checklist in `docs/[project]/` for reference

### **Customization Per Project**

- **New items:** Add project-specific checks (append, don't delete defaults)
- **Remove irrelevant:** Delete items not applicable to your project (document why)
- **Adjust timing:** Update time estimates if your project is larger
- **Update gate criteria:** Modify PASS/FAIL thresholds for your risk tolerance

### **Integration with Workflow**

Each phase in `WORKFLOW_PROCESS.md` references this checklist:
- Phase 1 → Use "Phase 1: Requirements Validation"
- Phase 2 → Use "Phase 2: Architecture Validation"
- Phase 3 → Use "Phase 3: Development Validation"
- etc.

---

## Common Failure Patterns (Meta-Checklist)

If you find yourself failing the same check repeatedly:

1. **Check is too strict?** → Adjust for your context (document decision in ADR)
2. **Process is broken?** → Add prevention rule to `shared-intelligence/pitfalls.md`
3. **Tool missing?** → Add to project setup (e.g., linter not configured)
4. **Skill gap?** → Add reference material to `shared-intelligence/patterns.md`

---

**Version history:**
- v1.0: 2026-02-22 (Phase-based checklists)
- v2.0: 2026-02-25 (Governance v3.0 alignment — OWASP, shared intelligence link-through)

**Next:** Automate checklist validation via CI/CD pipeline
