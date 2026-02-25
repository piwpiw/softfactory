# Agent Skills Catalog
**Deca-Agent Ecosystem | Last Updated: 2026-02-22**

> Skill Levels: **AWARENESS** → **WORKING** → **PRACTITIONER** → **EXPERT**

---

## Agent 01 — Chief Dispatcher

| Skill | Category | Level | Key Outputs |
|-------|----------|-------|-------------|
| WSJF Prioritization | Process | EXPERT | WSJF Score Table |
| Conflict Resolution | Process | EXPERT | Conflict Resolution Report |
| Pipeline Orchestration | Process | EXPERT | Execution Plan, Dependency Graph |

**Primary Skill Module:** N/A (uses `core/consultation.py` directly)

---

## Agent 02 — Product Manager

| Skill | Category | Level | Key Outputs |
|-------|----------|-------|-------------|
| RICE Scoring | Product | EXPERT | RICE Score Table |
| Story Mapping | Product | EXPERT | Story Map, Release Plan |
| OKR Definition | Product | PRACTITIONER | OKR Board |
| PRD Writing | Product | EXPERT | PRD Document |
| MoSCoW Prioritization | Product | EXPERT | MoSCoW Table |

**Primary Skill Modules:** `skills/lean_startup.py`, `skills/agile_scrum.py`, `skills/design_thinking.py`
**Document Standard:** `docs/standards/PRD_TEMPLATE.md`

---

## Agent 03 — Market Analyst

| Skill | Category | Level | Key Outputs |
|-------|----------|-------|-------------|
| SWOT Analysis | Research | EXPERT | SWOT Matrix |
| PESTLE Analysis | Research | EXPERT | PESTLE Report |
| Porter's Five Forces | Research | EXPERT | Five Forces Diagram |
| TAM/SAM/SOM Sizing | Research | PRACTITIONER | Market Size Report |

**Primary Skill Module:** `skills/lean_startup.py`, `skills/ux_research.py`

---

## Agent 04 — Solution Architect

| Skill | Category | Level | Key Outputs |
|-------|----------|-------|-------------|
| ADR Writing | Design | EXPERT | ADR Document |
| C4 Model | Design | EXPERT | C4 Text Diagrams |
| Domain-Driven Design | Design | EXPERT | Domain Model, Context Map |
| OpenAPI Design | Design | EXPERT | openapi.yaml stub |
| Clean Architecture | Design | EXPERT | Layer Specification |

**Primary Skill Modules:** `skills/domain_driven_design.py`, `skills/clean_architecture.py`, `skills/api_first_design.py`
**Document Standard:** `docs/standards/ADR_TEMPLATE.md`, `docs/standards/RFC_TEMPLATE.md`

---

## Agent 05 — Backend Developer

| Skill | Category | Level | Key Outputs |
|-------|----------|-------|-------------|
| TDD Cycle | Backend | EXPERT | Test suite, Coverage report |
| Clean Architecture Implementation | Backend | EXPERT | Codebase structure |
| 12-Factor App | Backend | PRACTITIONER | Compliance checklist |
| API Implementation | Backend | EXPERT | REST endpoints |

**Primary Skill Modules:** `skills/tdd_bdd.py`, `skills/clean_architecture.py`, `skills/api_first_design.py`

---

## Agent 06 — Frontend Developer

| Skill | Category | Level | Key Outputs |
|-------|----------|-------|-------------|
| Atomic Design | Frontend | EXPERT | Component library |
| WCAG 2.1 Compliance | Frontend | PRACTITIONER | Accessibility Audit |
| BDD Frontend | Frontend | PRACTITIONER | Gherkin feature files |
| Performance Optimization | Frontend | WORKING | Performance Report |

**Primary Skill Modules:** `skills/tdd_bdd.py`, `skills/ux_research.py`

---

## Agent 07 — QA Engineer

| Skill | Category | Level | Key Outputs |
|-------|----------|-------|-------------|
| Test Pyramid | Quality | EXPERT | Test Plan, Coverage Metrics |
| Risk-Based Testing | Quality | EXPERT | Risk Matrix |
| Test Plan Writing | Quality | EXPERT | Test Plan Document |
| Bug Reporting | Quality | EXPERT | Bug Report |

**Primary Skill Modules:** `skills/tdd_bdd.py`, `skills/agile_scrum.py`
**Document Standards:** `docs/standards/TEST_PLAN_TEMPLATE.md`, `docs/standards/BUG_REPORT_TEMPLATE.md`

---

## Agent 08 — Security Auditor

| Skill | Category | Level | Key Outputs |
|-------|----------|-------|-------------|
| OWASP Top 10 | Security | EXPERT | Security Report |
| STRIDE Threat Modeling | Security | EXPERT | STRIDE Threat Model |
| CVSS 3.1 Scoring | Security | EXPERT | CVSS Score Sheet |
| GDPR Compliance | Security | PRACTITIONER | GDPR Checklist |

**Primary Skill Module:** `skills/owasp_security.py`
**Document Standard:** `docs/standards/SECURITY_REPORT_TEMPLATE.md`

---

## Agent 09 — DevOps Engineer

| Skill | Category | Level | Key Outputs |
|-------|----------|-------|-------------|
| SLO/SLI Definition | DevOps | EXPERT | SLO Dashboard |
| GitOps | DevOps | EXPERT | CD Pipeline |
| Blue-Green Deployment | DevOps | EXPERT | Deployment Runbook |
| IaC (Terraform/Ansible) | DevOps | PRACTITIONER | Terraform modules |
| Chaos Engineering | DevOps | AWARENESS | Chaos Experiment Report |

**Primary Skill Module:** `skills/devops_sre.py`
**Document Standard:** `docs/standards/DEPLOYMENT_RUNBOOK_TEMPLATE.md`

---

## Agent 10 — Telegram Reporter

| Skill | Category | Level | Key Outputs |
|-------|----------|-------|-------------|
| Event-Driven Notification | Process | EXPERT | Notification log |
| Report Summarization | Process | PRACTITIONER | Daily/Weekly digests |

**Primary Dependencies:** `core/consultation.py`, `core/mission_manager.py`

---

## Cross-Agent Skill Coverage Map

```
UX Research ────────────────→ 02 PM, 06 Frontend
Design Thinking ────────────→ 02 PM, 06 Frontend
Lean Startup ───────────────→ 02 PM, 03 Analyst
Agile Scrum ────────────────→ 01 Dispatcher, 02 PM, 07 QA
DDD ─────────────────────────→ 04 Architect, 05 Backend
TDD/BDD ─────────────────────→ 05 Backend, 06 Frontend, 07 QA
Clean Architecture ──────────→ 04 Architect, 05 Backend
OWASP Security ──────────────→ 08 Security, 05 Backend, 09 DevOps
API-First Design ────────────→ 04 Architect, 05 Backend, 06 Frontend
DevOps/SRE ──────────────────→ 09 DevOps
```

---

*Maintained by Deca-Agent ecosystem | Source of truth: `core/skills_registry.py`*
