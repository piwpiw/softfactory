# SUBPROJECT CLAUDE.md TEMPLATE
> **Scope-First Governance** | Version 1.0 | 2026-02-25

---

## HEADER (Fill this in FIRST)

Fill in these items before starting any work:

```
Project ID: M-XXX
Status: PLANNING | ACTIVE | COMPLETE | ARCHIVED
Start Date: [YYYY-MM-DD]
Target Completion: [YYYY-MM-DD]
Last Updated: [YYYY-MM-DD]

SCOPE IN (Explicitly included):
- Feature/Component A
- Feature/Component B

SCOPE OUT (Explicitly excluded):
- [Future phase feature]

Success Metrics:
- Metric 1: Target value
- Metric 2: Target value
```

---

## 1. IMPORTS (Mandatory)

Read these files first (in order):

1. D:/Project/CLAUDE.md (Master platform standard)
2. D:/Project/orchestrator/README.md (Enterprise architecture)
3. D:/Project/shared-intelligence/patterns.md (Reusable solutions)
4. D:/Project/shared-intelligence/decisions.md (ADR log)
5. D:/Project/shared-intelligence/pitfalls.md (Failure prevention)

---

## 2. TECHNOLOGY STACK

Define framework stack:
- Backend: [FastAPI | Flask]
- Frontend: [Next.js 15+ | Vanilla JS]
- Database: [PostgreSQL | SQLite (dev)]
- Cache: [Redis | None]
- Auth: [JWT HS256 | API Key]
- Testing: [pytest | Playwright]
- Deploy: [Docker | Railway]

---

## 3. GOVERNANCE PHASES

Each phase has owner, duration, and deliverables:

**Phase -1:** Discovery (1 week async)
**Phase 0:** Planning & Architecture (2-3 days)
**Phase 1:** Design & Specification (3-5 days)
**Phase 2:** Core Development (depends on scope)
**Phase 3:** Frontend Development (parallel or sequential)
**Phase 4:** Integration & System Testing (5-7 days)
**Phase 5:** Deployment & Operations (3-5 days)
**Phase 6:** Launch Preparation (2-3 days)

---

## 4. SUCCESS METRICS

Define SMART metrics:

| Metric | Definition | Target | Owner |
|--------|-----------|--------|-------|
| Feature Completeness | % complete | 100% | PM |
| Code Quality | Warnings | 0 | DevLead |
| Test Coverage | % tested | ≥80% | QA |
| Performance | API p99 | <200ms | DevOps |
| Security | Critical bugs | 0 | Security |
| Documentation | Complete | 100% | Tech Writer |
| Deployment Success | % pass | 100% | DevOps |

---

## 5. STAKEHOLDER ROLES

Define who has authority:

| Role | Name | Authority | Escalation |
|------|------|-----------|------------|
| Project Manager | [Name] | Scope, Features, Timeline | Orchestrator |
| Tech Lead | [Name] | Architecture, Tech Decisions | CTO |
| Backend Lead | [Name] | Backend design, quality | Tech Lead |
| Frontend Lead | [Name] | Frontend design, UX | Tech Lead |
| QA Lead | [Name] | Quality gates, tests | Orchestrator |
| DevOps Lead | [Name] | Deployment, infrastructure | CTO |
| Security Officer | [Name] | Security review | CTO |
| Orchestrator | [Name] | Timeline, conflict resolution | User |

---

## 6. AGENT COLLABORATION PROTOCOL

Handoff flow:

Agent A (Business) → PRD + OKR
Agent B (Architect) → System Design + API Spec
Agent C (Backend Dev) → Core Code + Tests
Agent D (Frontend Dev) → UI + E2E Tests
Agent E (QA Engineer) → Integration Tests
Agent F (Security Auditor) → Security Checklist
Agent G (DevOps) → Deployment + Monitoring

Each handoff requires:
- [ ] Owner approval
- [ ] Completeness check
- [ ] Quality gate pass
- [ ] Documentation updated
- [ ] Next agent sign-off

---

## 7. KNOWLEDGE INHERITANCE

Copy relevant items from shared intelligence:

**Patterns to apply:** (from shared-intelligence/patterns.md)
**Decisions to follow:** (from shared-intelligence/decisions.md)
**Pitfalls to avoid:** (from shared-intelligence/pitfalls.md)

---

## 8. COMMUNICATION PLAN

Daily standups: 10:00 AM (15 min or async)
Weekly syncs: Friday 10:00 AM (45 min)

Escalation:
- Blocker → Tech Lead (2hr response)
- Issue → Orchestrator (1hr response)
- Critical → User (immediate)

Channels:
- Slack: #project-M-xxx
- GitHub: PR discussions
- Email: Weekly summary

---

## 9. RISK MITIGATION

Top 5 risks (update weekly):

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|-----------|
| 1 | [Risk] | High | High | [Strategy] |
| 2 | [Risk] | High | Medium | [Strategy] |
| 3 | [Risk] | Medium | High | [Strategy] |
| 4 | [Risk] | Medium | Low | [Strategy] |
| 5 | [Risk] | Low | Low | [Strategy] |

---

## 10. HANDOFF PROTOCOL

Before passing to next agent:

- [ ] Phase 100% complete (no TODOs)
- [ ] All code committed to feature branch
- [ ] CI/CD passes (linting, tests, security)
- [ ] Documentation updated
- [ ] Handoff notes written
- [ ] Next agent confirms ready

---

## 11. QUICK START

Day 1:
- [ ] Fill in Header
- [ ] Customize technology stack
- [ ] Assign stakeholder roles
- [ ] Create GitHub project board
- [ ] Team kickoff meeting

Week 1:
- [ ] Complete Phase -1 (discovery)
- [ ] Confirm scope
- [ ] Create risk register
- [ ] Set up dev environment

Week 2+:
- [ ] Enter Phase 0/1
- [ ] Daily standups
- [ ] Weekly syncs
- [ ] Handoff to next phase

---

**Version:** 1.0 | **Updated:** 2026-02-25 | **Status:** ACTIVE
**Use:** Customize for each sub-project (M-002, M-003, etc.)
