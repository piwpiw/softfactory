# 📝 🎯 CooCook Operations Protocol — Core Keywords & Workflow

> **Purpose**: **Document:** Core keywords for daily operations
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 🎯 CooCook Operations Protocol — Core Keywords & Workflow 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Document:** Core keywords for daily operations
**Version:** 1.0
**Date:** 2026-02-23
**Purpose:** Define clear language for Telegram-based company operations

---

## 🔑 CORE KEYWORDS (Essential Concepts)

### 1. **MISSION** (큰 목표)
**Definition:** Quarter-long strategic objective (OKR level)
**Format:** M-### (M-001, M-002, M-003...)
**Example:** M-002 "CooCook Market Analysis & Launch"
**Lifecycle:**
- IDEATION → PLANNING → EXECUTION → REVIEW → COMPLETE
**Owner:** Chief Dispatcher (Team 01)

```
/mission create "Implement user authentication"
→ Creates M-004
→ Auto-assigns to appropriate teams
```

---

### 2. **SPRINT** (2-week development cycle)
**Definition:** Fixed 2-week iteration for delivering features
**Format:** S-### (S-001, S-002, S-003...)
**Example:** S-001 "Auth System Sprint"
**Capacity:** 40 story points per sprint
**Velocity:** Track team performance

```
/sprint new "API Integration Sprint"
→ Creates S-005
→ Start date: 2026-02-23
→ End date: 2026-03-08
```

---

### 3. **TASK** (Individual work unit)
**Definition:** Atomic unit of work (1-3 days)
**Format:** T-### (T-001, T-002, T-003...)
**Example:** T-042 "Implement JWT authentication"
**Size:** 3, 5, 8, 13 story points (Fibonacci)
**Owner:** Individual team member or team

```
/task create T-042
  title: "Implement JWT authentication"
  points: 5
  team: 05
  sprint: S-005
```

---

### 4. **SKILL** (Capability/Competency)
**Definition:** Team or individual capability
**Categories:** Technical, Domain, Process
**Status:** Active (✅) | InProgress (⏳) | Blocked (❌)
**Installation:** Auto-detected by JARVIS, can be manually triggered

```
/skill install 05 "Redis Caching"
→ Shows progress: 25% 50% 75% 100%
→ Updates Team 05 skill level
```

---

### 5. **TEAM** (Group responsibility)
**Definition:** Cross-functional unit (01-10)
**Team 01:** Chief Dispatcher (Orchestration)
**Team 02:** Product Manager (Strategy)
**Team 03:** Market Analyst (Research)
**Team 04:** Solution Architect (Design)
**Team 05:** Backend Developer (Implementation)
**Team 06:** Frontend Developer (UI/UX)
**Team 07:** QA Engineer (Quality)
**Team 08:** Security Auditor (Security)
**Team 09:** DevOps Engineer (Infrastructure)
**Team 10:** Telegram Reporter (Communication)

```
/team 05 status
→ Shows Team 05: Backend Developer
→ Skills, capacity, current tasks
```

---

### 6. **STATUS** (Task Progress State)
**Definition:** Current position in workflow
**States:**
- 🔵 **BACKLOG** — Not started, waiting
- 🟡 **IN_PROGRESS** — Active development
- 🟠 **REVIEW** — Code/design review phase
- 🟢 **DONE** — Completed & merged
- 🔴 **BLOCKED** — Waiting for dependency

```
/status
→ Shows all tasks grouped by status
→ BACKLOG (12) | IN_PROGRESS (7) | REVIEW (3) | DONE (42)
```

---

### 7. **PRIORITY** (Urgency & Importance)
**Definition:** Task importance level
**Levels:**
- 🚨 **CRITICAL** — Must ship today (P0)
- 🔥 **HIGH** — Ship this sprint (P1)
- ⚡ **MEDIUM** — Ship this month (P2)
- 💤 **LOW** — Backlog (P3)

```
/priority T-042 CRITICAL
→ Task T-042 elevated to critical
→ Auto-notifies Team 05
→ Blocks lower-priority tasks if same owner
```

---

### 8. **DEPLOY** (Release cycle)
**Definition:** Moving code from dev → staging → production
**Stages:**
- 👷 **BUILD** — Compilation & unit tests pass
- 🧪 **STAGING** — Integration tests in pre-prod
- 🚀 **PRODUCTION** — Live for users
- 📊 **MONITOR** — 24h post-deploy monitoring

```
/deploy staging v1.2.3
→ Deploys v1.2.3 to staging
→ Runs smoke tests
→ Notifies Team 09 (DevOps)
→ Awaits approval for prod

/deploy prod v1.2.3
→ Blue-green deployment
→ Auto-rollback if error rate > 1%
→ Sends success report to all teams
```

---

### 9. **STANDUP** (Daily synchronization)
**Definition:** 5-minute daily team sync
**Time:** 09:00 UTC every weekday
**Format:**
```
Standup Report [Date]
━━━━━━━━━━━━━━━━━━━━
✅ Yesterday: [what was completed]
🔄 Today: [what will be done]
🚨 Blockers: [any issues]
━━━━━━━━━━━━━━━━━━━━
```

```
/standup
→ Collects all team standups
→ Shows 10 teams' status
→ Identifies blockers for dispatcher
→ Triggers auto-escalation if needed
```

---

### 10. **RELEASE** (Version deployment)
**Definition:** Public product release
**Format:** v[Major].[Minor].[Patch]
**Example:** v1.2.3, v1.3.0, v2.0.0
**Cadence:** Daily releases (v1.2.23, v1.2.24...)
**Changelog:** Auto-generated from merged PRs

```
/release create v1.2.24
→ Tags commit
→ Generates changelog
→ Creates release notes
→ Schedules deployment
→ Notifies users
```

---

## 📋 WORKFLOW STATE MACHINE

```
MISSION Creation
    ↓
├─→ Team 01 (Dispatcher): WSJF Prioritization
    ↓
├─→ Team 02 (PM): Create PRD & OKRs
    ↓
├─→ Team 03 (Analyst): Market validation
    ↓
└─→ Team 04 (Architect): Design & ADR
    ↓
SPRINT Planning
    ↓
├─→ Team 05 (Backend): Implement APIs
    ├─→ Team 06 (Frontend): Build UI
    ├─→ Team 07 (QA): Test features
    └─→ Team 08 (Security): Security review
    ↓
CODE REVIEW
    ↓
    ├─→ Approve → MERGE
    └─→ Reject → ITERATE
    ↓
DEPLOY to Staging
    ↓
├─→ Team 09 (DevOps): Infrastructure
    ├─→ Team 07 (QA): UAT
    └─→ Team 08 (Security): Security test
    ↓
DEPLOY to Production
    ↓
├─→ Blue-Green deployment
    ├─→ Health checks
    ├─→ Monitor for 24h
    └─→ Auto-rollback if issues
    ↓
RELEASE & ANNOUNCE
    ↓
Team 10 (Reporter): Send notifications
    ↓
POST-MORTEM & RETROSPECTIVE
```

---

## 📊 DAILY OPERATION RHYTHM

### 9:00 AM UTC — **STANDUP**
```
/standup
→ All teams report
→ Blockers identified
→ Dispatcher routes help
```

### 10:00 AM UTC — **NEW PROJECT LAUNCH**
```
/mission create "Today's feature"
→ Auto-routed to teams
→ Skills auto-checked
→ Missing skills auto-installed
```

### 1:00 PM UTC — **SPRINT REVIEW**
```
/sprint review
→ Progress: 12/40 points done
→ On track? Yes/No
→ Blockers? None
→ Velocity: 8.5 pts/day avg
```

### 3:00 PM UTC — **DEPLOY STAGING**
```
/deploy staging v1.2.24
→ Builds & deploys
→ Runs tests
→ Reports: ✅ Ready for production
```

### 4:30 PM UTC — **PRODUCTION DEPLOY**
```
/deploy prod v1.2.24
→ Blue-green switch
→ Monitors: ✅ 0 errors
→ Success! Live for 10.2K users
```

### 6:00 PM UTC — **DAILY SUMMARY**
```
/summary
→ Deployed: 1 feature (v1.2.24)
→ Users affected: 10,234
→ Bugs fixed: 3
→ New PRs: 12
→ Team velocity: 94% of target
→ Incidents: 0
→ NPS impact: +2 points
```

---

## 🎯 COMMAND SYNTAX RULES

### Rule 1: Clear Intent
✅ GOOD: `/deploy prod v1.2.24`
❌ BAD: `deploy please`

### Rule 2: Specify WHAT & WHY
✅ GOOD: `/task create "Fix login bug" priority:CRITICAL`
❌ BAD: `/task create "fix"`

### Rule 3: Include MEASUREMENTS
✅ GOOD: `/sprint review shows 25/40 points done`
❌ BAD: `/sprint review`

### Rule 4: Use KEYWORDS consistently
✅ GOOD: `/mission create [name]`, `/sprint new [name]`, `/task create [name]`
❌ BAD: Mixed terminology

### Rule 5: Auto-confirm CRITICAL actions
✅ Good: `/deploy prod v1.2.24` → JARVIS asks "Confirm deploy?" → User says "yes"
❌ Bad: Deploy without confirmation

---

## 🚨 PRIORITY LEVELS IN ACTION

### 🔴 CRITICAL (P0)
- Security vulnerability found
- Production down (0 availability)
- Data loss risk
- **Action:** Immediate deploy, notify all teams
```
🚨 CRITICAL: SQL injection vulnerability
→ All hands on deck
→ Deploy fix in < 1 hour
→ Notify customers
```

### 🟠 HIGH (P1)
- Major feature broken for 50%+ users
- Significant performance degradation
- Revenue-impacting bug
- **Action:** Deploy in sprint
```
🔥 HIGH: Login broken for 30% of users
→ Team 05 + 06 prioritize
→ Deploy today if possible
```

### 🟡 MEDIUM (P2)
- Feature not working as designed
- Minor performance issue
- Cosmetic bug
- **Action:** Plan for next sprint
```
⚡ MEDIUM: UI button misaligned
→ Add to sprint backlog
→ Estimate: 3 points
```

### 🟢 LOW (P3)
- Nice-to-have feature
- Documentation improvements
- Technical debt refactoring
- **Action:** Backlog
```
💤 LOW: Optimize cache hit rate
→ Backlog for future
→ Non-blocking
```

---

## 📈 METRICS TRACKED

### Team Metrics
- Velocity (points/sprint)
- Bug escape rate (bugs in prod)
- Code review time (avg hours)
- Skill completion rate

### Project Metrics
- Sprint burndown (points completed)
- Release frequency (features/day)
- Mean time to deploy (hours)
- Mean time to recovery (minutes)

### Quality Metrics
- Error rate (%)
- NPS score (0-100)
- Customer satisfaction (%)
- Uptime (%)

---

## 🔗 INTEGRATION POINTS

### With GitHub
```
/github link repo
→ Auto-syncs PRs
→ Auto-closes issues when merged
→ Auto-creates tasks from issues
```

### With Slack
```
/slack webhook
→ Notifies #deployments on deploy
→ Notifies #incidents on errors
→ Notifies #standup for team reports
```

### With Monitoring
```
/monitor setup
→ Links DataDog/NewRelic
→ Auto-creates incident task on alert
→ Auto-escalates if SLO breached
```

---

## 📚 COMMAND QUICK REFERENCE

| Keyword | Command | Example |
|---------|---------|---------|
| **MISSION** | `/mission create [name]` | `/mission create "v2.0 Launch"` |
| **SPRINT** | `/sprint new [name]` | `/sprint new "Auth Sprint"` |
| **TASK** | `/task create [name]` | `/task create "JWT auth"` |
| **SKILL** | `/skill install [team] [skill]` | `/skill install 05 Redis` |
| **TEAM** | `/team [id] status` | `/team 05 status` |
| **STATUS** | `/status` | `/status` |
| **PRIORITY** | `/priority [task] [level]` | `/priority T-042 CRITICAL` |
| **DEPLOY** | `/deploy [env] [version]` | `/deploy prod v1.2.24` |
| **STANDUP** | `/standup` | `/standup` |
| **RELEASE** | `/release create [version]` | `/release create v1.3.0` |
| **SUMMARY** | `/summary` | `/summary` |

---

## ✅ PROTOCOL ADHERENCE CHECKLIST

Before every Telegram command:
- [ ] Use correct KEYWORD (MISSION/SPRINT/TASK/etc)
- [ ] Include SPECIFIC details (not vague)
- [ ] State PRIORITY level
- [ ] Assign to TEAM
- [ ] Set expected TIMELINE
- [ ] Include MEASUREMENT criteria

---

**This protocol is the single source of truth for CooCook operations.**

Every command, decision, and action flows through these keywords.