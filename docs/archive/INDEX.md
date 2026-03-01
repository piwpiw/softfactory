# 📝 📖 MASTER INDEX — Start Here

> **Purpose**: **Start here if you're new to the system or don't know where to begin.**
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 📖 MASTER INDEX — Start Here 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **Everything you need is on this page.** Choose your path below.

---

## 🎯 I Want To...

### Understand the Big Picture
**Start here if you're new to the system or don't know where to begin.**

1. **MASTER_SYSTEM.md** (15 min read)
   - What is this organization?
   - How do 10 agents work together?
   - What are the 4 active projects?
   - What are the global rules?

2. **QUICK_REFERENCE.md** (5 min)
   - Memorize the decision tree
   - Know who to contact for what
   - Understand the global rules (R1-R10)

**→ Next:** Pick a role or project from the sections below

---

### Find the Right Person to Talk To
**I need help with something specific.**

Go to: **docs/TEAM_STRUCTURE.md**

Quick lookup:
- **Business/Strategy?** → 02-Product Manager or 01-Dispatcher
- **Technical Design?** → 04-Solution Architect
- **Backend API?** → 05-Backend Developer
- **Frontend UI?** → 06-Frontend Developer
- **Testing?** → 07-QA Engineer
- **Security?** → 08-Security Auditor
- **DevOps/Deployment?** → 09-DevOps Engineer
- **Team Notifications?** → 10-Telegram Reporter

**Agent Directory:**
- Role descriptions
- Current projects
- Skills & expertise
- Contact channels
- Response time SLAs

---

### Track Project Progress
**Which project should I work on? What's the status?**

Go to: **docs/PROJECT_REGISTRY.md**

Current Projects:
- **M-001** ✅ Infrastructure (COMPLETE) — [Learn more](#m-001-infrastructure-setup)
- **M-002** 🔄 CooCook (IN_PROGRESS) — [Learn more](#m-002-coocook-chef-marketplace)
- **M-003** ✅ SoftFactory (DEPLOYED) — [Learn more](#m-003-softfactory-multi-saas)
- **M-004** ✅ JARVIS Bot (ACTIVE) — [Learn more](#m-004-jarvis-telegram-bot)

For each project:
- Real-time status
- Team assignments
- Critical path to completion
- Blockers & risks
- Success criteria

---

### Write Documentation
**I need to create a PRD, ADR, Test Plan, etc.**

Go to: **docs/standards/**

Available Templates:
- `PRD_TEMPLATE.md` — Product requirements
- `ADR_TEMPLATE.md` — Architecture decisions
- `RFC_TEMPLATE.md` — Request for comments
- `TEST_PLAN_TEMPLATE.md` — QA strategy
- `BUG_REPORT_TEMPLATE.md` — Issue tracking
- `SECURITY_REPORT_TEMPLATE.md` — Vulnerabilities
- `DEPLOYMENT_RUNBOOK_TEMPLATE.md` — Release steps

**Rule:** All formal outputs must use these templates. No free-form documents.

---

### Understand Architecture Decisions
**What design patterns are we using? Why?**

Go to: **docs/standards/ADR_TEMPLATE.md**

For CooCook specifically: **ADR-0001 ACCEPTED**
- Pattern: Clean Architecture + Modular Monolith
- Trade-off: Monolith until 100+ RPS, then microservices
- Rationale: Rapid iteration, reduced complexity

---

### Access Source Code
**Where are the actual files?**

**SoftFactory (M-003) — Complete, Deployed**
```
backend/
├── app.py (Flask app factory)
├── models.py (SQLAlchemy models)
├── auth.py (JWT authentication)
├── payment.py (Stripe integration)
├── platform.py (Platform routes)
└── services/
    ├── coocook.py
    ├── sns_auto.py
    └── review.py

web/
├── platform/ (hub pages: login, dashboard, billing, admin)
├── coocook/ (chef booking pages)
├── sns-auto/ (social media automation pages)
└── review/ (campaign pages)

start_platform.py (entry point)
docs/SOFTFACTORY_README.md (setup guide)
```

**Live:** http://localhost:8000
**Demo:** admin@softfactory.com / admin123

---

### Set Up Local Development
**How do I get the system running?**

1. **Start SoftFactory (M-003)**
   ```bash
   cd D:/Project
   pip install -r requirements.txt
   python start_platform.py
   ```
   → http://localhost:8000

2. **For CooCook (M-002) — Coming 2026-02-24**
   - FastAPI setup
   - PostgreSQL database
   - Docker containers
   - See docs/PROJECT_REGISTRY.md for details

3. **JARVIS Bot (M-004) — Already Running**
   - Deployed to Railway
   - Active on Telegram
   - Commands: /pages, /status, /deploy, /mission, /report, /help

---

### Learn the System Rules
**What are the non-negotiables?**

Go to: **MASTER_SYSTEM.md → Unified Global Rules**

10 Rules (R1-R10):
1. Sequential Thinking (all agents, before hand-off)
2. Conflict Escalation (→ 01-Dispatcher)
3. Consultation Protocol (Uncertainty > 70%)
4. Template Compliance (standard docs only)
5. Secret Management (.env only, never in code)
6. Knowledge Sharing (weekly updates)
7. RACI Clarity (clear ownership)
8. Skill-First Matching (match to top 3 skills)
9. Code Quality Gates (80% coverage, 0C/0H security)
10. Retrospectives (every completed mission)

---

### See Real-Time Team Status
**Who's available? What's their utilization?**

Go to: **docs/TEAM_STRUCTURE.md → Team Matrix**

Current Allocation (62% utilized, BALANCED):
- 05-Backend + 06-Frontend: 75-80% (recovering from M-003)
- 02-PM + 03-Analyst + 04-Architect: 60-70% (M-002 research)
- 07-QA + 08-Security: 40-50% (standby, ready)
- 09-DevOps: 50% (awaiting signal)
- 01-Dispatcher + 10-Reporter: Always active

---

### Check If Something's Broken
**Troubleshooting guide for common issues.**

Go to: **QUICK_REFERENCE.md → If Something Goes Wrong**

Common Issues:
- App won't start → Check port 8000
- Dependencies missing → pip install -r requirements.txt --upgrade
- Database locked → Delete platform.db (auto-recreates)
- Git merge conflict → DO NOT force-push, resolve manually

---

### Make a Decision or Resolve Conflict
**Who decides? How do we handle disputes?**

Decision Process (see MASTER_SYSTEM.md):
1. **Routine decisions** → Relevant agent makes call
2. **Technical conflicts** → 04-Architect decides
3. **Business conflicts** → 02-PM decides
4. **Ambiguous conflicts** → 01-Dispatcher decides (final authority)

Escalation Path:
- Need immediate decision? → Telegram 01-Dispatcher
- Need consultation? → ConsultationBus protocol (docs/standards/)
- Need conflict resolution? → 01-Dispatcher

---

---

## 📊 Quick Status Dashboard

```
ECOSYSTEM HEALTH: 🟢 GREEN

Projects:
├── M-001 Infrastructure ✅ COMPLETE (2026-02-22)
├── M-002 CooCook 🔄 30% (dev starts 2026-02-24)
├── M-003 SoftFactory ✅ DEPLOYED (http://localhost:8000)
└── M-004 JARVIS 🟢 ACTIVE (24/7 notifications)

Team: 10 agents, 62% utilized, BALANCED
Critical Blocks: 0 (GREEN)
Security Audits: 100% passed (0C/0H)
Deployment Pipeline: Blue-Green ready
Uptime: 99.9%+ (M-004 JARVIS)
```

---

## 🗺️ Document Map (Complete Directory)

### Core Docs (Read These First)
| Doc | Purpose | Time |
|-----|---------|------|
| **MASTER_SYSTEM.md** | Ecosystem overview | 15 min |
| **TEAM_STRUCTURE.md** | Agent directory + matrix | 15 min |
| **PROJECT_REGISTRY.md** | Real-time project dashboard | 20 min |
| **QUICK_REFERENCE.md** | One-page cheat sheets | 5 min |

### Templates (Use for All Docs)
| Template | Use When | Owner |
|----------|----------|-------|
| PRD_TEMPLATE.md | Writing product requirements | 02-PM |
| ADR_TEMPLATE.md | Recording architecture decisions | 04-Architect |
| RFC_TEMPLATE.md | Requesting feedback on ideas | Any |
| TEST_PLAN_TEMPLATE.md | Planning QA strategy | 07-QA |
| BUG_REPORT_TEMPLATE.md | Reporting issues | 07-QA |
| SECURITY_REPORT_TEMPLATE.md | Documenting vulnerabilities | 08-Security |
| DEPLOYMENT_RUNBOOK_TEMPLATE.md | Planning deployments | 09-DevOps |

### Project Docs
| Doc | Project | Status |
|-----|---------|--------|
| CLAUDE.md | M-001 | Original ecosystem ledger |
| SOFTFACTORY_README.md | M-003 | Setup + API reference |
| docs/RACI_MATRIX.md | All | Responsibility matrix |
| docs/AGENT_SKILLS.md | All | Skill catalog |
| docs/CONSULTATION_PROTOCOL.md | All | Cross-agent help process |
| docs/MISSION_LIFECYCLE.md | All | Project workflow |

---

## 🚀 Next Steps (By Role)

### If You're a Developer (05 or 06)
1. Read: TEAM_STRUCTURE.md (yourself)
2. Read: MASTER_SYSTEM.md (understand pipeline)
3. Check: PROJECT_REGISTRY.md (M-002 CooCook details)
4. Action: Development starts 2026-02-24

### If You're a Manager (01, 02, or 03)
1. Read: MASTER_SYSTEM.md (full overview)
2. Read: PROJECT_REGISTRY.md (status tracking)
3. Read: TEAM_STRUCTURE.md (allocations)
4. Action: Schedule team sync

### If You're New to the Team
1. Read: QUICK_REFERENCE.md (5 min)
2. Read: MASTER_SYSTEM.md (15 min)
3. Skim: TEAM_STRUCTURE.md (5 min)
4. Use: QUICK_REFERENCE.md going forward

### If You're Creating Something New
1. Check: docs/standards/ for the right template
2. Follow: The template exactly (no deviations)
3. File: In correct folder (docs/standards/ for formal, project folder for project-specific)
4. Update: PROJECT_REGISTRY.md with your work

---

## 🎓 Learning Tracks

**Track 1: Executive Overview (25 min)**
1. MASTER_SYSTEM.md (10 min)
2. QUICK_REFERENCE.md (5 min)
3. PROJECT_REGISTRY.md skim (10 min)

**Track 2: Individual Contributor (45 min)**
1. MASTER_SYSTEM.md (15 min)
2. TEAM_STRUCTURE.md (15 min)
3. Relevant project from PROJECT_REGISTRY.md (15 min)

**Track 3: Project Manager (60 min)**
1. MASTER_SYSTEM.md (15 min)
2. TEAM_STRUCTURE.md (15 min)
3. PROJECT_REGISTRY.md (20 min)
4. RACI_MATRIX.md (10 min)

**Track 4: Deep Dive (2 hours)**
1. All core docs (45 min)
2. All templates (30 min)
3. Project-specific docs (30 min)
4. CLAUDE.md history (15 min)

---

## 🔐 Critical Security Rules (Don't Forget!)

1. ✅ **Secrets in .env ONLY** — Never commit credentials
2. ✅ **Test coverage minimum 80%** — Before merge
3. ✅ **Security audit 0C/0H** — Before production
4. ✅ **OWASP Top 10 mitigations** — Every project
5. ✅ **Git best practices** — No force-push main
6. ✅ **Blue-Green deployments** — Always use this pattern

See: docs/standards/SECURITY_REPORT_TEMPLATE.md

---

## 📞 When to Escalate

| Situation | Action | Timeline |
|-----------|--------|----------|
| 🔴 **Blocker** | → 01-Dispatcher immediately | <2h |
| 🟠 **Conflict** | → Relevant agent + 01-Dispatcher | <4h |
| 🟡 **Question** | → QUICK_REFERENCE.md first, then agent | <1d |
| 🟢 **FYI** | → MASTER_SYSTEM.md, no escalation needed | N/A |

---

## ✨ Pro Tips

- **Bookmark:** QUICK_REFERENCE.md (use it daily)
- **Update:** PROJECT_REGISTRY.md after delivering work
- **Check:** TEAM_STRUCTURE.md before adding work (who's available?)
- **Review:** MASTER_SYSTEM.md rules before making decisions
- **Use:** Standard templates for ALL formal documents

---

## 🎯 Bottom Line

**This system has:**
- ✅ Single source of truth (no duplicates)
- ✅ Clear decision authority (01-Dispatcher)
- ✅ Shared infrastructure (10 skill modules)
- ✅ Real-time visibility (PROJECT_REGISTRY.md)
- ✅ Standard templates (docs/standards/)
- ✅ Clear RACI matrix (no ambiguous ownership)
- ✅ Communication protocol (ConsultationBus)
- ✅ Agent skill matrix (cross-training ready)

**Your job:** Use it, update it, follow the rules.

---

## 🗺️ File Locations

```
D:/Project/
├── docs/
│   ├── INDEX.md (you are here)
│   ├── MASTER_SYSTEM.md ⭐
│   ├── TEAM_STRUCTURE.md ⭐
│   ├── PROJECT_REGISTRY.md ⭐
│   ├── QUICK_REFERENCE.md ⭐
│   ├── standards/
│   │   ├── PRD_TEMPLATE.md
│   │   ├── ADR_TEMPLATE.md
│   │   ├── RFC_TEMPLATE.md
│   │   ├── TEST_PLAN_TEMPLATE.md
│   │   ├── BUG_REPORT_TEMPLATE.md
│   │   ├── SECURITY_REPORT_TEMPLATE.md
│   │   └── DEPLOYMENT_RUNBOOK_TEMPLATE.md
│   ├── RACI_MATRIX.md
│   ├── AGENT_SKILLS.md
│   ├── CONSULTATION_PROTOCOL.md
│   └── MISSION_LIFECYCLE.md
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── auth.py
│   ├── payment.py
│   ├── platform.py
│   └── services/
├── web/
│   ├── platform/
│   ├── coocook/
│   ├── sns-auto/
│   └── review/
├── agents/ (10 agent folders)
├── scripts/ (JARVIS bot)
├── CLAUDE.md (original ecosystem ledger)
├── SOFTFACTORY_README.md
├── requirements.txt
├── .env
└── platform.db (auto-created)
```

⭐ = **Read these first**

---

## 🎉 You're Ready!

**You now have:**
1. ✅ Single source of truth
2. ✅ Clear roles & responsibilities
3. ✅ Real-time project tracking
4. ✅ Standard templates
5. ✅ Quick reference guides
6. ✅ Team visibility
7. ✅ Decision protocols
8. ✅ Communication pipeline

**Next:** Pick your starting point from **I Want To...** section above.

---

**Last Updated:** 2026-02-23 | **Status:** LIVE ✅ | **Questions?** → QUICK_REFERENCE.md