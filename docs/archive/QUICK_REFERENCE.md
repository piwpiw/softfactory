# QUICK REFERENCE — One-Page Cheat Sheets
> **Use this for fast lookup** — See full docs for details

---

## 🎯 Which Agent Do I Need?

| I Need... | Contact | Why |
|-----------|---------|-----|
| **Task prioritization** | 01-Dispatcher | WSJF scoring, conflict resolution |
| **PRD/OKR/roadmap** | 02-PM | Business decisions, feature priority |
| **Market research** | 03-Analyst | SWOT, competitive analysis |
| **System design** | 04-Architect | C4, ADR, OpenAPI, technical decisions |
| **API/backend** | 05-Backend | FastAPI, PostgreSQL, TDD |
| **UI/frontend** | 06-Frontend | Next.js, React, WCAG compliance |
| **Test strategy** | 07-QA | Test pyramid, automation, coverage |
| **Security review** | 08-Security | STRIDE, OWASP, vulnerability scan |
| **Infrastructure** | 09-DevOps | AWS, Docker, deployment, SLO/SLI |
| **Team notifications** | 10-Telegram | Real-time alerts, status updates |

---

## 🚀 Quick Project Status

```
M-001 ✅ COMPLETE    Ecosystem initialized (43 files)
M-002 🔄 30%         CooCook architecture phase, dev starts 2026-02-24
M-003 ✅ LIVE        SoftFactory deployed at http://localhost:8000
M-004 ✅ ACTIVE      JARVIS running 24/7 on Railway
```

---

## 📊 Real-Time Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Team Utilized** | 62% | BALANCED (not overloaded) |
| **Critical Blocks** | 0 | GREEN (all systems go) |
| **Deployments This Week** | 2 | M-003 live, M-004 stable |
| **Security Audits** | 100% | All projects cleared (0C/0H) |

---

## 🔄 Decision Tree

**Need to make a decision?**

```
START
  ↓
Is it urgent & blocking? → YES → Escalate to 01-Dispatcher
  ↓ NO
Is it technical? → YES → Talk to 04-Architect or 05-Backend
  ↓ NO
Is it business? → YES → Talk to 02-PM
  ↓ NO
Is it about team/resources? → YES → Talk to 01-Dispatcher
  ↓ NO
Check MASTER_SYSTEM.md for protocol
```

---

## 📞 Escalation SLA

| Severity | Target | Response |
|----------|--------|----------|
| 🔴 Critical | 01-Dispatcher | <2 hours |
| 🟠 High | Relevant Agent | <4 hours |
| 🟡 Medium | Agent Team | <1 day |
| 🟢 Low | Optional | <3 days |

---

## 🎯 Global Rules (Memorize These)

| Rule | Requirement |
|------|-------------|
| **R1** | All agents: Sequential thinking before hand-off |
| **R2** | All conflicts → 01-Dispatcher (no exceptions) |
| **R3** | Uncertainty >70% → ConsultationBus escalation |
| **R4** | All docs use standard templates (docs/standards/) |
| **R5** | Secrets ONLY in .env, never in code |
| **R6** | All knowledge shared weekly |
| **R7** | RACI matrix defined for every task |
| **R8** | Task-to-agent: match top 3 skills first |
| **R9** | Code gates: 80% test coverage, 0C/0H security |
| **R10** | Every completed mission → retrospective |

---

## 🗂️ Document Map (Where to Find Things)

| Need This | Location | Purpose |
|-----------|----------|---------|
| Full ecosystem view | docs/MASTER_SYSTEM.md | Understand all 10 agents + projects |
| Agent capabilities | docs/TEAM_STRUCTURE.md | Who does what + skill matrix |
| Project status | docs/PROJECT_REGISTRY.md | Real-time dashboards + roadmaps |
| PRD template | docs/standards/PRD_TEMPLATE.md | Write product requirements |
| Architecture decision | docs/standards/ADR_TEMPLATE.md | Record design decisions |
| Test plan | docs/standards/TEST_PLAN_TEMPLATE.md | Define QA strategy |
| Bug report | docs/standards/BUG_REPORT_TEMPLATE.md | File issues properly |
| Security report | docs/standards/SECURITY_REPORT_TEMPLATE.md | Document vulnerabilities |
| Deployment | docs/standards/DEPLOYMENT_RUNBOOK_TEMPLATE.md | Deploy safely |

---

## 🔐 Environment Variables (Copy-Paste)

### Development
```env
ANTHROPIC_API_KEY=sk-ant-...
PLATFORM_SECRET_KEY=PLATFORM_SECRET_KEY_REDACTED
PLATFORM_URL=http://localhost:8000
ENVIRONMENT=development
PROJECT_NAME=SoftFactory
```

### Telegram (M-004)
```env
TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN_REDACTED
TELEGRAM_CHAT_ID=7910169750
PM2_APP_NAME=sonol-bot
```

### Optional (Stripe)
```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

---

## 🏃 Quick Commands

### Start SoftFactory (M-003)
```bash
cd D:/Project
python start_platform.py
# → http://localhost:8000
```

### Run Tests
```bash
pytest backend/ -v --cov=backend
```

### Deploy to Staging
```bash
# Contact 09-DevOps
# Blue-Green deployment ready
```

### Check Git Status
```bash
git status
git log --oneline | head -10
```

---

## 👥 Agent Quick-Dial

| Agent | Fastest Contact | Status |
|-------|-----------------|--------|
| 01-Dispatcher | Telegram /mission | ALWAYS ON |
| 02-PM | Slack #product | 9am-6pm |
| 03-Analyst | Email+Telegram | 9am-6pm |
| 04-Architect | Design review | 9am-6pm |
| 05-Backend | Code review | 9am-6pm |
| 06-Frontend | UI review | 9am-6pm |
| 07-QA | Test plan | 9am-6pm |
| 08-Security | Security scan | 9am-6pm |
| 09-DevOps | Deployment | 9am-6pm |
| 10-Telegram | Automated | 24/7 |

---

## 🚨 If Something Goes Wrong

### App Won't Start
```bash
# Check port 8000 already used
lsof -i :8000
# Kill process
kill -9 <PID>
# Delete database and restart (gets fresh seed)
rm platform.db
python start_platform.py
```

### Dependencies Missing
```bash
pip install -r requirements.txt --upgrade
```

### Database Locked
```bash
# Stop all instances
# Delete platform.db (will auto-recreate with seed data)
rm D:/Project/platform.db
# Restart
```

### Git Merge Conflict
```bash
# DO NOT force-push main
git status  # See conflicts
# Edit files manually
git add <resolved-files>
git commit -m "Resolve conflicts"
```

---

## 📈 Roadmap At a Glance

```
TODAY (2026-02-23)
├── ✅ M-003 SoftFactory DEPLOYED
├── ✅ Consolidation COMPLETE
└── 📋 CooCook ready for dev

2026-02-24
├── 🔄 Backend/Frontend dev starts (05+06)
└── 📋 OpenAPI spec finalized (04)

2026-02-27
├── 📋 QA/Security reviews (07+08)
└── 📋 STRIDE threat model ready

2026-03-01
├── 📋 Staging deployment (09)
└── 🔄 Load testing begins

2026-03-30
└── 📋 Production readiness review

2026-04-15
├── 🚀 M-002 LIVE
└── 🎯 CooCook production

2026-Q3
└── 🎯 10K MAU target (CooCook)
```

---

## 💡 Pro Tips

- **Stuck?** Check MASTER_SYSTEM.md for protocol
- **Question?** Tag the right agent quickly in this order: Agent ID → Skill → Issue
- **Making changes?** Update docs/PROJECT_REGISTRY.md after delivery
- **Deploying?** Always use Blue-Green, never force-push main
- **Security?** OWASP Top 10 first, then GDPR compliance
- **Tests?** 80% coverage minimum before merge
- **Documentation?** Use standard templates, no free-form docs

---

## 🎓 Learning Path

**New to the system?**

1. Read: **MASTER_SYSTEM.md** (10 min)
2. Read: **TEAM_STRUCTURE.md** (10 min)
3. Skim: **PROJECT_REGISTRY.md** (5 min)
4. Use: **QUICK_REFERENCE.md** (this file) when in doubt

**Total time: 25 minutes to be dangerous** ✨

---

## 🔗 Critical Links

| Link | Purpose | Status |
|------|---------|--------|
| http://localhost:8000 | SoftFactory Hub | ✅ LIVE |
| https://jarvis-production.up.railway.app/ | JARVIS Dashboard | ✅ LIVE |
| docs/MASTER_SYSTEM.md | Ecosystem overview | ✅ CURRENT |
| docs/TEAM_STRUCTURE.md | Agent directory | ✅ CURRENT |
| docs/PROJECT_REGISTRY.md | Project dashboard | ✅ REAL-TIME |

---

## ✅ Before You Deploy

- [ ] 80%+ test coverage
- [ ] Security scan: 0 Critical, 0 High
- [ ] Code review approved
- [ ] PR linked to ticket
- [ ] CHANGELOG updated
- [ ] Deployment runbook reviewed
- [ ] Blue-Green ready
- [ ] Rollback plan documented

---

**Last Updated:** 2026-02-23 | **Next Review:** Weekly
**Questions?** → docs/MASTER_SYSTEM.md → Escalate to 01-Dispatcher
