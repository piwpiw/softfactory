# MASTER SYSTEM — Unified Organization Framework
> **Last Updated:** 2026-02-23 | **Owner:** System Architecture | **Status:** ACTIVE

---

## 🎯 Mission

**Single source of truth** for all projects, teams, skills, and operations. Eliminate duplication. Maximum visibility. Minimal friction.

---

## 📊 Active Ecosystem

### 10 Core Agent Roles (Deca-Agent Architecture)

| ID | Role | Folder | Status | Key Skills | Current Project |
|----|----|--------|--------|-----------|-----------------|
| **01** | Chief Dispatcher | `agents/01_dispatcher/` | ACTIVE | WSJF, Conflict Resolution, Pipeline Orchestration | M-002 (CooCook) |
| **02** | Product Manager | `agents/02_product_manager/` | ACTIVE | RICE, Story Map, OKR, PRD | M-002 (CooCook) |
| **03** | Market Analyst | `agents/03_market_analyst/` | ACTIVE | SWOT, PESTLE, Porter's 5 Forces | M-002 (CooCook) |
| **04** | Solution Architect | `agents/04_architect/` | ACTIVE | ADR, C4 Model, DDD, OpenAPI, Clean Architecture | M-002 (CooCook) |
| **05** | Backend Developer | `agents/05_backend_dev/` | ACTIVE | TDD, Clean Architecture, FastAPI/Flask, PostgreSQL | M-002 (CooCook) + M-003 (SoftFactory) |
| **06** | Frontend Developer | `agents/06_frontend_dev/` | ACTIVE | Atomic Design, WCAG 2.1, BDD, React/Next.js | M-002 (CooCook) + M-003 (SoftFactory) |
| **07** | QA Engineer | `agents/07_qa_engineer/` | ACTIVE | Test Pyramid, Risk-Based Testing, Automation | M-002 (CooCook) |
| **08** | Security Auditor | `agents/08_security_auditor/` | ACTIVE | STRIDE, CVSS 3.1, OWASP Top 10, GDPR | M-002 (CooCook) |
| **09** | DevOps Engineer | `agents/09_devops/` | ACTIVE | SLO/SLI, GitOps, Blue-Green, IaC, AWS ECS | M-002 (CooCook) |
| **10** | Telegram Reporter | `agents/10_telegram_reporter/` | ACTIVE | Event Notifications, Daily Summaries, Retrospectives | All Missions |

---

## 🗂️ Active Projects

| ID | Name | Status | Phase | Owner | Stack | Started | Key Metrics |
|----|------|--------|-------|-------|-------|---------|------------|
| **M-001** | Initial Infrastructure | ✅ COMPLETE | REPORTING | 01-Dispatcher | N/A | 2026-02-22 | 43 files created |
| **M-002** | CooCook (Chef Marketplace) | 🔄 IN_PROGRESS | ARCHITECTURE | 02-PM + 03-Analyst | FastAPI + Next.js 15 + PostgreSQL 16 + Redis + AWS | 2026-02-22 | 10K MAU by Q3 2026 |
| **M-003** | SoftFactory Hub (Multi-SaaS) | ✅ COMPLETE | DEPLOYED | 05-Backend + 06-Frontend | Flask + SQLAlchemy + SQLite + Tailwind | 2026-02-23 | 3 services live |
| **M-004** | JARVIS Telegram Bot | ✅ ACTIVE | OPERATIONAL | 10-Reporter | Python-Telegram-Bot + FastAPI | 2026-02-22 | 24/7 notifications |

---

## 🔄 Communication & Decision Pipeline

```
[NEW TASK INPUT]
       ↓
01_DISPATCHER (WSJF scoring)
       ├─→ Conflict? → escalate back ↩️
       ↓
Parallel Track:
    02_PM (RICE/OKR/PRD)  ←→ ConsultationBus ←→  03_ANALYST (SWOT/PESTLE)
       ↓
04_ARCHITECT (C4/ADR/OpenAPI/DDD)
       ↓
Parallel Track:
    05_BACKEND (TDD/Clean Arch)  ←→ ConsultationBus ←→  06_FRONTEND (Atomic/WCAG)
       ↓
Parallel Track:
    07_QA (Risk-Based Testing)  ←→ ConsultationBus ←→  08_SECURITY (STRIDE)
       ↓
09_DEVOPS (SLO/Blue-Green/IaC)
       ↓
10_REPORTER (notification + retro trigger)
       ↓
[DELIVERY + MONITORING]
```

**Key Rules:**
- All agents apply **Sequential Thinking** before hand-off
- Uncertainty > 70% → **mandatory ConsultationBus escalation**
- All formal outputs use **standard templates** (docs/standards/)
- Conflicts → escalate to **01_Dispatcher immediately**
- Secrets only in `.env` — never committed
- Every completed mission → mandatory retrospective

---

## 📋 Shared Infrastructure

### Core Modules (Unified)

| Module | Path | Purpose | Dependencies |
|--------|------|---------|--------------|
| **ConsultationBus** | `core/consultation.py` | Bidirectional agent consultation + loop detection | N/A |
| **SkillsRegistry** | `core/skills_registry.py` | Agent skill catalog + task matching | N/A |
| **MissionManager** | `core/mission_manager.py` | Mission lifecycle state machine | SkillsRegistry |
| **DocumentEngine** | `core/document_engine.py` | Template-based document generation | N/A |

### Skills Library (Reusable)

| Skill | Path | Used By | Status |
|-------|------|---------|--------|
| Design Thinking | `skills/design_thinking.py` | 02, 06 | ✅ READY |
| Lean Startup | `skills/lean_startup.py` | 02, 03 | ✅ READY |
| Agile Scrum | `skills/agile_scrum.py` | 01, 02, 07 | ✅ READY |
| Domain-Driven Design | `skills/domain_driven_design.py` | 04, 05 | ✅ READY |
| TDD/BDD | `skills/tdd_bdd.py` | 05, 06, 07 | ✅ READY |
| Clean Architecture | `skills/clean_architecture.py` | 04, 05 | ✅ READY |
| OWASP Security | `skills/owasp_security.py` | 08 | ✅ READY |
| API-First Design | `skills/api_first_design.py` | 04, 05, 06 | ✅ READY |
| DevOps/SRE | `skills/devops_sre.py` | 09 | ✅ READY |
| UX Research | `skills/ux_research.py` | 02, 06 | ✅ READY |

### Document Standards (Single Template Set)

| Document Type | Template | Owner | Status |
|---|---|---|---|
| **PRD** | `docs/standards/PRD_TEMPLATE.md` | 02-PM | ✅ |
| **ADR** | `docs/standards/ADR_TEMPLATE.md` | 04-Architect | ✅ |
| **RFC** | `docs/standards/RFC_TEMPLATE.md` | Any | ✅ |
| **Test Plan** | `docs/standards/TEST_PLAN_TEMPLATE.md` | 07-QA | ✅ |
| **Bug Report** | `docs/standards/BUG_REPORT_TEMPLATE.md` | 07-QA | ✅ |
| **Security Report** | `docs/standards/SECURITY_REPORT_TEMPLATE.md` | 08-Security | ✅ |
| **Deployment Runbook** | `docs/standards/DEPLOYMENT_RUNBOOK_TEMPLATE.md` | 09-DevOps | ✅ |

---

## 🚀 Current Project Status (Real-Time)

### M-002: CooCook (Chef Marketplace)
- **Status:** IN_PROGRESS
- **Current Phase:** Architecture & Planning (Waiting for M-003 patterns)
- **Stack:** FastAPI + Next.js 15 + PostgreSQL 16 + Redis + AWS ECS
- **Owner:** 02-PM + 03-Analyst lead, 04-Architect designing, 05+06 standby
- **Next Milestone:** ADR-0001 approval, OpenAPI 3.1 spec finalized
- **Blockers:** None currently
- **OKR:** 10,000 MAU by Q3 2026; 15% booking conversion; 40% day-7 retention; NPS > 50

### M-003: SoftFactory Hub (Multi-SaaS Platform)
- **Status:** ✅ COMPLETE (Phase: DEPLOYED)
- **Services:** 3 live (CooCook mini, SNS Auto, Review Campaigns)
- **Stack:** Flask + SQLAlchemy + SQLite + Tailwind CSS
- **Code:** ~2500 lines backend, ~3000 lines frontend, 15 pages
- **Live:** http://localhost:8000
- **Completion:** 2026-02-23 (3-hour sprint)
- **Demo:** admin@softfactory.com / admin123
- **Next Phase:** Add service #4+ (10-30 min each)

### M-004: JARVIS Telegram Bot
- **Status:** ✅ ACTIVE (Operational)
- **Endpoint:** https://jarvis-production.up.railway.app/
- **Features:** /pages, /status, /deploy, /mission, /report, /help
- **Token:** 8461725251:AAELKRbZkpa3u6WK24q4k-RGkzedHxjTLiM
- **Uptime:** 24/7

---

## 📦 Unified Environment Variables

### Core (Always Required)
```env
ANTHROPIC_API_KEY=sk-ant-...
PROJECT_NAME=SoftFactory
ENVIRONMENT=development
LOG_LEVEL=WARNING
```

### JARVIS + Telegram
```env
TELEGRAM_BOT_TOKEN=8461725251:AAELKRbZkpa3u6WK24q4k-RGkzedHxjTLiM
TELEGRAM_CHAT_ID=7910169750
PM2_APP_NAME=sonol-bot
```

### SoftFactory Platform
```env
PLATFORM_SECRET_KEY=softfactory-dev-secret-key-2026
PLATFORM_URL=http://localhost:8000
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Search & Research
```env
GOOGLE_SEARCH_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_CX=your_custom_search_engine_id_here
```

---

## ✅ Unified Global Rules

| Rule # | Name | Description | Enforcement |
|--------|------|-------------|------------|
| **R1** | Sequential Thinking | All agents think step-by-step before hand-off | Mandatory |
| **R2** | Conflict Escalation | All conflicts → 01_Dispatcher immediately | Automatic |
| **R3** | Consultation Protocol | Uncertainty > 70% → ConsultationBus | Automatic |
| **R4** | Template Compliance | All formal outputs use standard templates | Pre-commit |
| **R5** | Secret Management | Secrets only in `.env`, never committed | Git hooks |
| **R6** | Knowledge Sharing | All discoveries → Master System weekly | Mandatory |
| **R7** | RACI Clarity | Every task has clear owner + stakeholders | Defined |
| **R8** | Skill-First Matching | Match tasks to agent's top 3 skills | Algorithm |
| **R9** | Code Quality Gates | TDD minimum 80% coverage, Security scan 0C/0H | CI/CD |
| **R10** | Retrospectives | Every completed mission → retro session | Mandatory |

---

## 📊 Team Availability Matrix

### Current Allocation (as of 2026-02-23)

| Agent | Project | Utilization | Availability | Notes |
|-------|---------|------------|--------------|-------|
| 01-Dispatcher | All | 40% | HIGH | Ready for M-004+ |
| 02-PM | M-002 | 60% | MEDIUM | Waiting for architect input |
| 03-Analyst | M-002 | 60% | MEDIUM | Research phase |
| 04-Architect | M-002 | 70% | MEDIUM | ADR finalization |
| 05-Backend | M-002 + M-003 | 80% | LOW | Just completed M-003 |
| 06-Frontend | M-002 + M-003 | 75% | LOW | Just completed M-003 |
| 07-QA | M-002 | 50% | HIGH | Ready for new projects |
| 08-Security | M-002 | 40% | HIGH | Ready for new projects |
| 09-DevOps | M-002 | 50% | MEDIUM | Awaiting deployment green-light |
| 10-Reporter | All | 100% | MONITORING | Always active |

---

## 🔗 Quick Links to Project Docs

| Project | Key Docs | Status |
|---------|----------|--------|
| **CooCook (M-002)** | ADR-0001, C4 Diagram, OpenAPI Spec | In Progress |
| **SoftFactory (M-003)** | SOFTFACTORY_README.md | Complete |
| **JARVIS (M-004)** | Telegram Bot Manual | Operational |
| **Agent System** | CLAUDE.md | Active |

---

## 🎯 Next Actions (Priority Order)

1. **Immediate (Today)**
   - [ ] Approve ADR-0001 for CooCook architecture
   - [ ] Finalize OpenAPI 3.1 spec
   - [ ] QA passes Recipe Discovery API

2. **This Week**
   - [ ] Deploy CooCook v0.1.0 to staging (Blue-Green)
   - [ ] Security audit CooCook API (STRIDE)
   - [ ] SoftFactory: Add Service #4 (30 min)

3. **Next Week**
   - [ ] CooCook production deployment
   - [ ] M-005 kickoff (if scheduled)
   - [ ] Deca-Agent retrospective

---

## 📝 Change Log (Recent)

| Date | Agent | Action | Status |
|------|-------|--------|--------|
| 2026-02-23 | 05+06-Dev | Completed M-003 (SoftFactory) — 15 pages, 3 services | ✅ COMPLETE |
| 2026-02-22 | 09-DevOps | Deployed CooCook v0.1.0 staging (Blue-Green) | ✅ COMPLETE |
| 2026-02-22 | 08-Security | Security audit — 0 Critical, 0 High | ✅ CLEARED |
| 2026-02-22 | 07-QA | QA PASSED Recipe Discovery API | ✅ PASSED |
| 2026-02-22 | 04-Architect | ADR-0001 ACCEPTED (Clean Arch + Modular Monolith) | ✅ APPROVED |
| 2026-02-22 | All | Deca-Agent ecosystem initialized | ✅ COMPLETE |

---

## 🔐 Security & Compliance

**All projects follow:**
- ✅ OWASP Top 10 mitigations
- ✅ GDPR data handling
- ✅ Zero credentials in code
- ✅ Secrets in `.env` only
- ✅ CI/CD security gates
- ✅ Regular security audits (STRIDE)

---

## 🎓 Unified Learning

All agents have access to:
- Skills library (10 reusable modules)
- Document templates (7 standard types)
- Consultation protocol (for cross-agent help)
- RACI matrix (clear ownership)
- Mission lifecycle state machine

---

**This document is the single source of truth. Update only if conditions change.**
