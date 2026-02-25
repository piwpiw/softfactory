# Orchestrator — Agent Registry & Authority Matrix
> **Purpose:** All agents declared here with explicit authority boundaries.
> **Rule:** No agent acts outside its defined authority matrix (Governance Principle #2).
> **Last updated:** 2026-02-25

---

## Claude Code Sub-Agents (.claude/agents/)

| ID | Agent | File | Scope In | Scope Out | Escalate To |
|----|-------|------|---------|-----------|-------------|
| SA-01 | Orchestrator | `orchestrator.md` | Full project coordination, agent assignment, phase management | Code implementation, direct DB write | (top-level) |
| SA-02 | Business Strategist | `business-strategist.md` | PRD, OKR, user stories, business metrics | Technical decisions, code review | SA-01 |
| SA-03 | Architecture Designer | `architect.md` | System design, API spec, data modeling, ADR | Business strategy, deployment | SA-01 |
| SA-04 | Development Lead | `dev-lead.md` | Code implementation, unit tests, integration | Architecture design, deployment pipelines | SA-03 |
| SA-05 | QA Engineer | `qa-engineer.md` | Test planning, test execution, bug reports | Code implementation, deployment | SA-04 |
| SA-06 | DevOps | `devops.md` | CI/CD, Docker, IaC, monitoring setup | Application logic, test design | SA-01 |
| SA-07 | Security Auditor | `security-auditor.md` | OWASP audit, secrets scan, auth review | Product decisions, UI design | SA-01 |
| SA-08 | Performance Analyzer | `performance-analyzer.md` | Token analysis, load testing, optimization | Feature development | SA-01 |

---

## Python Agent Implementations (agents/)

| ID | Agent | Dir | Primary Responsibility | Consumed APIs | Authority Boundary |
|----|-------|-----|----------------------|---------------|-------------------|
| PA-01 | Chief Dispatcher | `01_dispatcher/` | Orchestration, priority, conflict resolution | All internal | Global scope |
| PA-02 | Product Manager | `02_product_manager/` | PRD, roadmap, stakeholder comms | ConsultationBus, DocumentEngine | M-002 product |
| PA-03 | Market Analyst | `03_market_analyst/` | Market research, SWOT, competitive analysis | BraveSearch MCP, ConsultationBus | Research only |
| PA-04 | Architect | `04_architect/` | Technical design, ADR, OpenAPI spec | ConsultationBus, DocumentEngine | Architecture decisions |
| PA-05 | Backend Dev | `05_backend_dev/` | API implementation, DB models, auth | ConsultationBus, SQLite MCP | backend/ dir |
| PA-06 | Frontend Dev | `06_frontend_dev/` | HTML/JS/CSS, API integration | ConsultationBus, filesystem MCP | web/ dir |
| PA-07 | QA Engineer | `07_qa_engineer/` | Test execution, bug filing, sign-off | Puppeteer MCP, fetch MCP | tests/ dir |
| PA-08 | Security Auditor | `08_security_auditor/` | Vuln scan, secrets audit, OWASP | ConsultationBus | Read-only audit |
| PA-09 | DevOps | `09_devops/` | Deployment, CI/CD, monitoring | GitHub MCP, ConsultationBus | scripts/ dir |
| PA-10 | Telegram Reporter | `10_telegram_reporter/` | Status notifications, milestone alerts | Telegram API (bot token) | Notifications only |

---

## Authority Rules

### Escalation Hierarchy
```
PA-10 (Notification) → PA-01 (Dispatcher)
PA-07 (QA) → PA-05 (Backend) → PA-04 (Architect) → PA-01 (Dispatcher)
PA-08 (Security) → PA-04 (Architect) → PA-01 (Dispatcher)
PA-09 (DevOps) → PA-04 (Architect) → PA-01 (Dispatcher)
```

### Conflict Resolution (Principle #11)
- **Technical disagreement:** PA-04 Architect has final say
- **Product disagreement:** PA-02 PM has final say
- **Security override:** PA-08 can halt any task (immediate escalation to PA-01)
- **Priority dispute:** PA-01 Dispatcher is final arbiter

### RACI Matrix (abbreviated)
| Decision | R (Responsible) | A (Accountable) | C (Consulted) | I (Informed) |
|----------|----------------|-----------------|---------------|--------------|
| Architecture change | PA-04 | PA-01 | PA-05, PA-06 | PA-07, PA-09 |
| Feature priority | PA-02 | PA-01 | PA-03 | All |
| Security block | PA-08 | PA-01 | PA-04, PA-05 | All |
| Deployment | PA-09 | PA-01 | PA-04, PA-07 | PA-10 |
| New agent onboarding | SA-01 | PA-01 | All | All |

---

## New Agent Onboarding Checklist (Principle #11)
- [ ] Create `/sub-projects/[name]/CLAUDE.md` from master template
- [ ] Define scope-in (one sentence)
- [ ] Define scope-out (one sentence)
- [ ] Declare all consumed main-service APIs
- [ ] Assign authority boundaries in this registry
- [ ] Inherit all `/shared-intelligence/` knowledge
- [ ] Confirm tech stack matches platform standards
- [ ] Set measurable success metrics before first commit
- [ ] Register in this file
