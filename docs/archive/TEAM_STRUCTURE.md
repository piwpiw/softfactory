# TEAM STRUCTURE — Agent Roles & Capabilities
> **Last Updated:** 2026-02-23 | **Authority:** System Architecture | **Status:** ACTIVE

---

## 📍 Agent Directory (One Place to Know Everything)

### 01 — CHIEF DISPATCHER
**Role:** Strategic traffic controller + conflict resolver
**Status:** ✅ ACTIVE | **Current Projects:** All
**Utilization:** 40% | **Availability:** HIGH

**Primary Responsibilities:**
- WSJF scoring & prioritization
- Task routing to correct agents
- Conflict resolution (escalation point)
- Pipeline orchestration
- Mission approval

**Decision Authority:** Full (can override recommendations)

**Required Skills:**
- Strategic prioritization (WSJF)
- Conflict mediation
- System thinking
- Stakeholder management

**Current Load:**
- M-001: ✅ COMPLETE
- M-002: 📋 AWAITING input (CooCook design approved)
- M-003: ✅ COMPLETE (SoftFactory live)
- M-004: 📊 MONITORING (JARVIS active)

**When to Escalate Here:**
- Resource conflicts
- Priority disputes
- Go/no-go decisions
- Cross-project dependencies

---

### 02 — PRODUCT MANAGER
**Role:** Vision keeper + requirements translator
**Status:** ✅ ACTIVE | **Current Projects:** M-002 (CooCook)
**Utilization:** 60% | **Availability:** MEDIUM

**Primary Responsibilities:**
- PRD creation & maintenance
- RICE scoring
- OKR definition
- Roadmap planning
- Stakeholder communication

**Deliverables Owned:**
- Product Requirements Documents (PRD_TEMPLATE.md)
- OKR alignment (10K MAU, 15% conversion, 40% retention, NPS > 50)
- Story mapping
- Release planning

**Current Focus (M-002 CooCook):**
- Target: Leisure travelers (25-40), digital nomads
- Value prop: "Airbnb for local food experiences"
- AI personalization core feature
- Q3 2026 launch

**When to Involve:**
- Feature prioritization
- User research questions
- Release planning
- Business metrics tracking

---

### 03 — MARKET ANALYST
**Role:** External intelligence + research validator
**Status:** ✅ ACTIVE | **Current Projects:** M-002 (CooCook)
**Utilization:** 60% | **Availability:** MEDIUM

**Primary Responsibilities:**
- Market analysis (SWOT, PESTLE, Porter's 5 Forces)
- Competitive landscape
- TAM/SAM/SOM calculations
- Trend research
- Risk assessment

**Deliverables Owned:**
- Market analysis reports
- Competitive matrix
- Opportunity assessment
- Risk register

**Current Focus (M-002 CooCook):**
- Chef marketplace TAM/SAM/SOM
- Competitor analysis (Airbnb, Withlocals, etc.)
- Regional expansion strategy
- Pricing strategy

**When to Involve:**
- Business viability questions
- Competitive positioning
- Market trends
- Risk identification

---

### 04 — SOLUTION ARCHITECT
**Role:** Blueprint creator + technical vision
**Status:** ✅ ACTIVE | **Current Projects:** M-002 (CooCook)
**Utilization:** 70% | **Availability:** MEDIUM

**Primary Responsibilities:**
- System design (C4 Model)
- ADR (Architecture Decision Records)
- OpenAPI spec creation
- Domain-Driven Design
- Tech stack recommendations

**Deliverables Owned:**
- ADR documents
- C4 diagrams (Context, Container, Component, Code)
- OpenAPI 3.1 specifications
- Architecture decision log

**Current Focus (M-002 CooCook):**
- ✅ ADR-0001: Clean Architecture + Modular Monolith ACCEPTED
- 📊 C4 diagrams (4 levels)
- 📋 OpenAPI 3.1 specification (in progress)
- Event-driven messaging architecture

**Stack Recommendations:**
- Backend: FastAPI (async) + PostgreSQL 16
- Frontend: Next.js 15 (SSR/SSG)
- Cache: Redis
- Hosting: AWS ECS (containerized)
- AI: Claude Sonnet 4.6 for personalization

**When to Involve:**
- Technical design questions
- Stack evaluation
- Scalability concerns
- Tech debt assessment

---

### 05 — BACKEND DEVELOPER
**Role:** API builder + data engineer
**Status:** ✅ ACTIVE | **Current Projects:** M-002 (CooCook) + M-003 (SoftFactory COMPLETE)
**Utilization:** 80% | **Availability:** LOW

**Primary Responsibilities:**
- REST/GraphQL API development
- Database schema design
- Authentication & authorization
- Integration testing
- Performance optimization

**Core Skills:**
- FastAPI / Flask
- SQLAlchemy / Django ORM
- PostgreSQL / MySQL / SQLite
- TDD (80%+ coverage minimum)
- Clean Architecture patterns
- API-First design
- RESTful principles (Level 3 HATEOAS)

**Recent Deliverables:**
- ✅ M-003 SoftFactory backend (2500+ lines)
  - Flask + SQLAlchemy models
  - JWT auth system
  - Stripe payment integration
  - 7 services (Platform, CooCook, SNS, Review)
  - 3 database migrations (users, products, bookings)

**Current Focus (M-002):**
- FastAPI project setup
- PostgreSQL 16 schema
- Authentication (JWT + OAuth2 optional)
- Chef discovery API
- Booking transaction logic

**Code Quality Standards:**
- Minimum 80% test coverage
- Type hints on all functions
- Docstrings required
- Security scan: 0C/0H

**When to Involve:**
- API design
- Database questions
- Performance issues
- Integration testing

---

### 06 — FRONTEND DEVELOPER
**Role:** UI builder + UX implementer
**Status:** ✅ ACTIVE | **Current Projects:** M-002 (CooCook) + M-003 (SoftFactory COMPLETE)
**Utilization:** 75% | **Availability:** LOW

**Primary Responsibilities:**
- UI component development
- Responsive design
- Accessibility (WCAG 2.1)
- User interaction
- Performance optimization
- BDD frontend testing

**Core Skills:**
- React / Next.js
- Tailwind CSS / styled-components
- TypeScript
- Atomic Design patterns
- WCAG 2.1 AA compliance
- BDD testing
- Responsive mobile-first

**Recent Deliverables:**
- ✅ M-003 SoftFactory frontend (3000+ lines)
  - 15 pages (Platform hub + 3 services)
  - Common API module (350 lines)
  - Responsive Tailwind UI
  - Authentication flows
  - Demo admin/user accounts

**Current Focus (M-002):**
- Next.js 15 setup (SSR/SSG)
- Component library (Atomic Design)
- Chef discovery UI
- Booking flow
- User dashboard

**Accessibility Standards:**
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader support
- Color contrast >= 4.5:1
- All interactive elements labeled

**When to Involve:**
- UI/UX design
- Accessibility issues
- Component architecture
- Performance optimization

---

### 07 — QA ENGINEER
**Role:** Quality assurance + test strategist
**Status:** ✅ ACTIVE | **Current Projects:** M-002 (CooCook)
**Utilization:** 50% | **Availability:** HIGH

**Primary Responsibilities:**
- Test planning & strategy
- Test automation
- Risk-based testing
- Regression testing
- Performance testing
- Bug tracking & triage

**Core Skills:**
- Test Pyramid methodology
- Risk-based testing
- Test automation frameworks
- Performance testing
- Load testing
- BDD/TDD
- Test management

**Deliverables Owned:**
- TEST_PLAN_TEMPLATE.md
- BUG_REPORT_TEMPLATE.md
- Test automation scripts
- Quality metrics & reports

**Current Status (M-002):**
- ✅ Recipe Discovery API: QA PASSED
- 📋 Full test suite pending (arch approval)

**Test Coverage Standards:**
- Minimum 80% code coverage
- End-to-end tests for critical paths
- Performance benchmarks
- Security regression tests

**When to Involve:**
- Test planning
- Quality gates
- Performance baselines
- Bug severity assessment

---

### 08 — SECURITY AUDITOR
**Role:** Risk manager + compliance officer
**Status:** ✅ ACTIVE | **Current Projects:** M-002 (CooCook)
**Utilization:** 40% | **Availability:** HIGH

**Primary Responsibilities:**
- Threat modeling (STRIDE)
- Vulnerability assessment
- OWASP Top 10 mitigation
- GDPR/compliance checks
- Security testing
- Incident response

**Core Skills:**
- STRIDE threat modeling
- CVSS 3.1 scoring
- OWASP Top 10 + OWASP API Top 10
- GDPR compliance
- Penetration testing
- Cryptography
- Authentication/Authorization

**Deliverables Owned:**
- SECURITY_REPORT_TEMPLATE.md
- Threat models (STRIDE)
- Risk register
- Compliance checklists

**Current Status (M-002):**
- ✅ Recipe Discovery API: CLEARED (0C/0H)
- 📋 Full API security audit pending

**Security Standards:**
- All secrets in `.env` only
- CI/CD security gates
- CVSS score < 4.0 (Medium)
- Regular penetration testing
- Dependency scanning (weekly)

**When to Involve:**
- Design reviews
- Security questions
- Compliance questions
- Incident triage

---

### 09 — DEVOPS ENGINEER
**Role:** Infrastructure builder + deployment master
**Status:** ✅ ACTIVE | **Current Projects:** M-002 (CooCook)
**Utilization:** 50% | **Availability:** MEDIUM

**Primary Responsibilities:**
- Infrastructure as Code (IaC)
- CI/CD pipeline setup
- Deployment strategy
- Monitoring & alerting
- Incident response
- Scaling & optimization

**Core Skills:**
- AWS (ECS, RDS, S3, Lambda)
- Kubernetes (optional)
- Terraform / CloudFormation
- Docker / Containerization
- CI/CD (GitHub Actions, GitLab CI)
- SLO/SLI definition
- Blue-Green deployments
- Database migration

**Deliverables Owned:**
- DEPLOYMENT_RUNBOOK_TEMPLATE.md
- Infrastructure code
- Deployment playbooks
- Monitoring dashboards

**Current Status (M-002):**
- ✅ Staging deployment: Blue-Green ready
- 📋 Production deployment: Pending security clearance

**Deployment Strategy (M-002):**
- Blue-Green deployments
- Zero-downtime updates
- Database migration strategy
- Rollback procedures
- SLO: 99.9% uptime

**When to Invoke:**
- Infrastructure questions
- Deployment strategy
- Scaling needs
- Incident response

---

### 10 — TELEGRAM REPORTER
**Role:** Communication hub + event monitor
**Status:** ✅ ACTIVE | **Current Projects:** All
**Utilization:** 100% | **Availability:** MONITORING (24/7)

**Primary Responsibilities:**
- Real-time notifications
- Daily summaries
- Milestone alerts
- Retrospective triggering
- Status updates
- Incident alerts

**Core Skills:**
- Event-driven architecture
- Message formatting
- Notification automation
- Retrospective facilitation
- Status aggregation

**Deliverables Owned:**
- Daily Telegram summaries
- Real-time alerts
- Milestone notifications
- Retrospective reports

**Current Status (M-004 JARVIS):**
- ✅ Bot ACTIVE (TELEGRAM_BOT_TOKEN_REDACTED)
- ✅ Notifications 24/7
- ✅ Railway deployment stable

**Commands Available:**
- `/pages` → All web pages with inline buttons
- `/status` → System status (3-line format)
- `/deploy env version` → Deployment trigger
- `/mission name` → New project
- `/report` → Monitoring report
- `/help` → Command list

**When to Involve:**
- Status updates needed
- Team notifications
- Milestone celebrations
- Incident alerts

---

## 👥 Team Matrix (At a Glance)

```
ROLE               STATUS    PROJECT        UTIL   AVAILABLE  BLOCKING?
────────────────────────────────────────────────────────────────────
01 Dispatcher      ✅ ACTIVE  All            40%    HIGH       No
02 Product Mgr     ✅ ACTIVE  M-002          60%    MEDIUM     No (waiting)
03 Analyst         ✅ ACTIVE  M-002          60%    MEDIUM     No (waiting)
04 Architect       ✅ ACTIVE  M-002          70%    MEDIUM     ADR-0001 done, OpenAPI pending
05 Backend Dev     ✅ ACTIVE  M-002+M-003    80%    LOW        No (resting after M-003)
06 Frontend Dev    ✅ ACTIVE  M-002+M-003    75%    LOW        No (resting after M-003)
07 QA Engineer     ✅ ACTIVE  M-002          50%    HIGH       No (ready)
08 Security        ✅ ACTIVE  M-002          40%    HIGH       No (ready)
09 DevOps          ✅ ACTIVE  M-002          50%    MEDIUM     Awaiting go-live signal
10 Telegram        ✅ ACTIVE  All            100%   24/7       No (always on)
────────────────────────────────────────────────────────────────────
TEAM TOTAL:        10/10     4 projects     62%    BALANCED   No critical blocks
```

---

## 🔄 Skill Cross-Training Matrix

Who can cover for whom if needed?

| Primary | Secondary Backup | Tertiary | Notes |
|---------|------------------|----------|-------|
| 02-PM | 01-Dispatcher | 03-Analyst | Can handle business decisions |
| 03-Analyst | 02-PM | 01-Dispatcher | Can do market analysis |
| 04-Architect | 05-Backend | 06-Frontend | Can review code architecture |
| 05-Backend | 04-Architect | 09-DevOps | Can do infrastructure code |
| 06-Frontend | 04-Architect | 05-Backend | Can do responsive design |
| 07-QA | N/A | 05-Backend | Can write automation tests |
| 08-Security | 04-Architect | 09-DevOps | Can do threat modeling |
| 09-DevOps | 05-Backend | 08-Security | Can do IaC review |

---

## 📅 Typical Project Team Composition

### Small Project (10-30 days)
- 01-Dispatcher (5%)
- 02-PM or 03-Analyst (50%)
- 04-Architect (30%)
- 05-Backend + 06-Frontend (50% each)
- 07-QA (50%)
- 08-Security (20%)
- 09-DevOps (20%)

**Total FTE: ~4.5**

### Medium Project (30-90 days, like M-002)
- 01-Dispatcher (20%)
- 02-PM + 03-Analyst (60% each)
- 04-Architect (60%)
- 05-Backend + 06-Frontend (70% each)
- 07-QA (50%)
- 08-Security (40%)
- 09-DevOps (50%)
- 10-Reporter (100%)

**Total FTE: ~7**

### Large Project (90+ days)
- All 10 agents at varying capacity
- Potential external contractors for specific skills
- Cross-project resource sharing via Dispatcher

---

## 🎯 How to Request Help

**Format: Tag + Skill + Context**

```
@02-PM 🎯 Priority assessment — new CooCook feature request
@04-Architect 🏗️ Design review — suggest Stack for M-005
@05-Backend 💻 Code review — complex transaction logic
@08-Security 🔐 Threat model review — payment flow
```

**Response Time SLA:**
- Critical (blocker): < 2 hours
- High: < 4 hours
- Medium: < 1 day
- Low: < 3 days

---

## 📊 Skill Depth Chart

### Level Definitions
- **Expert (E)** — Can teach others, 10+ years
- **Advanced (A)** — Independent work, 5+ years
- **Intermediate (I)** — With guidance, 2+ years
- **Novice (N)** — Learning, < 2 years

| Skill | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 |
|-------|----|----|----|----|----|----|----|----|----|----|
| Python | N | I | I | I | E | N | I | A | A | E |
| JavaScript | N | N | N | N | I | E | I | N | I | I |
| Database Design | N | I | I | E | E | N | I | I | A | N |
| Security | N | N | N | I | I | I | I | E | A | I |
| DevOps/IaC | N | N | N | N | I | N | I | I | E | N |
| Product Strategy | E | E | E | A | N | N | N | N | N | N |
| System Design | E | I | I | E | A | I | N | I | A | N |

---

## ✅ Performance Metrics (Per Agent)

Tracked monthly in retrospectives:

| Metric | Target | Current Status |
|--------|--------|----------------|
| Delivery on time | 90%+ | ✅ 95% (M-001, M-003) |
| Quality gates passed | 100% | ✅ 100% |
| Cross-agent consultation rate | 5-10% | ✅ 8% (healthy) |
| Escalations to Dispatcher | < 5% | ✅ 2% (normal) |
| Code review time | < 24h | ✅ 6h avg |
| Documentation compliance | 100% | ✅ 100% |

---

## 🚀 Next Team Actions

**Immediate:**
- [ ] 04-Architect: Finalize OpenAPI 3.1 spec (deadline today)
- [ ] 05-Backend: Start FastAPI setup for M-002
- [ ] 06-Frontend: Begin Next.js 15 component library

**This Week:**
- [ ] All: ADR-0001 architecture discussion (45 min sync)
- [ ] 09-DevOps: Prepare AWS ECS deployment playbook
- [ ] 08-Security: Full STRIDE threat model for M-002

**Next Week:**
- [ ] Team retrospective (M-001 + M-003 complete)
- [ ] M-005 planning kickoff (if scheduled)
- [ ] Skill cross-training session

---

**This document is the single source of truth for team structure. Update weekly.**
