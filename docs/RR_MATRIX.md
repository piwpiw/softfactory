# R&R Matrix — RACI
**Deca-Agent Ecosystem | Last Updated: 2026-02-22**

> RACI: **R**esponsible (does the work) | **A**ccountable (owns the outcome) | **C**onsulted (provides input) | **I**nformed (kept in loop)

---

## Activity × Agent Matrix

| Activity | 01 Dispatch | 02 PM | 03 Analyst | 04 Architect | 05 Backend | 06 Frontend | 07 QA | 08 Security | 09 DevOps | 10 Reporter |
|----------|:-----------:|:-----:|:----------:|:------------:|:----------:|:-----------:|:-----:|:-----------:|:---------:|:-----------:|
| **Task intake & routing** | R/A | I | I | I | I | I | I | I | I | I |
| **Conflict resolution** | R/A | C | C | C | C | C | C | C | C | I |
| **Pipeline orchestration** | R/A | C | C | C | C | C | C | C | C | I |
| **Product requirements (PRD)** | I | R/A | C | C | I | I | C | C | I | I |
| **RICE/MoSCoW prioritization** | I | R/A | C | C | I | I | I | I | I | I |
| **OKR definition** | C | R/A | C | I | I | I | I | I | I | I |
| **Market research (SWOT/PESTLE)** | I | C | R/A | I | I | I | I | I | I | I |
| **Competitor analysis** | I | C | R/A | I | I | I | I | I | I | I |
| **TAM/SAM/SOM sizing** | I | C | R/A | I | I | I | I | I | I | I |
| **System architecture design** | I | C | I | R/A | C | C | C | C | C | I |
| **ADR creation** | I | I | I | R/A | C | C | I | C | C | I |
| **OpenAPI spec** | I | C | I | R/A | C | C | I | C | I | I |
| **Domain model (DDD)** | I | C | I | R/A | C | I | I | C | I | I |
| **Backend implementation** | I | I | I | C | R/A | I | C | C | C | I |
| **TDD cycle** | I | I | I | C | R/A | I | C | I | I | I |
| **API implementation** | I | I | I | C | R/A | C | C | C | I | I |
| **Frontend implementation** | I | I | I | C | C | R/A | C | C | I | I |
| **Component design (Atomic)** | I | C | I | C | I | R/A | C | I | I | I |
| **Accessibility (WCAG)** | I | I | I | I | C | R/A | C | C | I | I |
| **Test plan creation** | I | C | I | C | C | C | R/A | C | I | I |
| **Test execution** | I | I | I | I | C | C | R/A | C | I | I |
| **Bug reporting** | I | C | I | C | C | C | R/A | C | I | I |
| **Security threat modeling** | I | I | I | C | C | C | C | R/A | C | I |
| **OWASP audit** | I | I | I | I | C | C | C | R/A | I | I |
| **CVSS scoring** | I | I | I | I | I | I | C | R/A | I | I |
| **Deployment planning** | I | I | I | C | C | C | C | C | R/A | I |
| **CI/CD pipeline** | I | I | I | C | C | C | C | C | R/A | I |
| **SLO/SLI definition** | I | I | I | C | I | I | C | C | R/A | I |
| **Deployment runbook** | I | I | I | C | I | I | C | C | R/A | I |
| **Mission notifications** | I | I | I | I | I | I | I | I | C | R/A |
| **CLAUDE.md updates** | C | C | C | C | C | C | C | C | C | R/A |
| **Retrospective recording** | R/A | C | C | C | C | C | C | C | C | I |

---

## Agent Role Summaries

| ID | Agent | Primary Role | Key Outputs |
|----|-------|-------------|-------------|
| 01 | Chief Dispatcher | Orchestration, conflict resolution | Execution plans, escalation reports |
| 02 | Product Manager | Product strategy, requirements | PRD, RICE table, OKR board, Story Map |
| 03 | Market Analyst | Market intelligence | SWOT/PESTLE/Porter's, TAM/SAM/SOM |
| 04 | Solution Architect | System design | ADR, C4 diagrams, OpenAPI spec, Domain model |
| 05 | Backend Developer | Server-side implementation | APIs, DB schemas, TDD test suites |
| 06 | Frontend Developer | Client-side implementation | UI components, accessibility audit |
| 07 | QA Engineer | Quality assurance | Test plans, bug reports, coverage reports |
| 08 | Security Auditor | Security assurance | STRIDE model, OWASP audit, CVSS reports |
| 09 | DevOps Engineer | Deployment & reliability | CI/CD, SLOs, runbooks, IaC |
| 10 | Telegram Reporter | Notification & reporting | Mission alerts, daily/weekly summaries |

---

*Maintained by the Deca-Agent ecosystem | Update via Agent 10 or manually*
