# Agent System Architecture

> **Version:** 2026-03-02 | **Status:** ACTIVE | **Parent:** CLAUDE.md §1 Import #2
> **Purpose:** Agent lifecycle, team routing, execution modes — grounded in `orchestrator/agent-registry.md`

---

## 1. Team ↔ Agent ID Mapping

CLAUDE.md uses T-numbers for governance routing (§5a, §9).
`orchestrator/agent-registry.md` uses PA-numbers for implementation.
This table is the canonical mapping:

| T-ID | PA-ID | SA-ID | Role | Directory | Scope |
|------|-------|-------|------|-----------|-------|
| T1 | PA-01 | SA-01 | Chief Dispatcher | `agents/01_dispatcher/` | Full project coordination, priority, conflict resolution |
| T2 | PA-02 | SA-02 | Product Manager | `agents/02_product_manager/` | PRD, roadmap, stakeholder comms |
| T3 | PA-03 | — | Market Analyst | `agents/03_market_analyst/` | Market research, SWOT, competitive analysis |
| T4 | PA-04 | SA-03 | Architect | `agents/04_architect/` | System design, API spec, ADR |
| T5 | PA-05 | SA-04 | Backend Developer | `agents/05_backend_dev/` | `backend/` dir — API, models, auth |
| T6 | PA-06 | — | Frontend Developer | `agents/06_frontend_dev/` | `web/` dir — HTML, JS, CSS |
| T7 | PA-07 | SA-05 | QA Engineer | `agents/07_qa_engineer/` | `tests/` dir — test execution, bug filing |
| T8 | PA-08 | SA-07 | Security Auditor | `agents/08_security_auditor/` | Read-only audit, OWASP, secrets scan |
| T9 | PA-09 | SA-06 | DevOps Engineer | `agents/09_devops/` | `scripts/` dir — CI/CD, Docker, monitoring |
| T10 | PA-10 | — | Telegram Reporter | `agents/10_telegram_reporter/` | Notifications only — status alerts |

**Note:** SA-08 (Performance Analyzer) has no T-number or PA equivalent — it is a Claude Code sub-agent only.

---

## 2. Agent Lifecycle

```
Session Init → Context Load → Phase Assignment → Execution → Validation → Handoff → Cleanup
                    ↓                                              ↓
            CONTEXT_ENGINE.md                              AGENT_PROTOCOLS.md
            (tag search first)                             (structured handoff)
```

Phase assignments follow `orchestrator/phase-structure-v4.md` (8 phases: -1 to 7).

---

## 3. Execution Modes (Model Strategy)

Per `orchestrator/phase-structure-v4.md` §Model Strategy:

| Mode | Model | When | Cost |
|------|-------|------|------|
| **Default** | Haiku 4.5 | Phases -1 to 6 (routine work) | $0.003/1K tokens |
| **Critical** | Sonnet 4.6 | Phase 1 (Requirement), Phase 2 (Documentation), Phase 5 (Security), Phase 7 (Deploy) | ~$0.015/1K tokens |
| **Override** | Opus 4.6 | User-escalated only — complex architecture, incident response | ~$0.075/1K tokens |

**Selection rule:** Start Haiku. Upgrade to Sonnet only for phases marked CRITICAL in phase-structure-v4.md. Never auto-select Opus.

---

## 4. Escalation Hierarchy

From `orchestrator/agent-registry.md` §Authority Rules:

```
PA-10 (Telegram) ──→ PA-01 (Dispatcher)
PA-07 (QA)       ──→ PA-05 (Backend) ──→ PA-04 (Architect) ──→ PA-01 (Dispatcher)
PA-08 (Security) ──→ PA-04 (Architect) ──→ PA-01 (Dispatcher)
PA-09 (DevOps)   ──→ PA-04 (Architect) ──→ PA-01 (Dispatcher)
PA-06 (Frontend) ──→ PA-05 (Backend) ──→ PA-04 (Architect) ──→ PA-01 (Dispatcher)
```

**Conflict Resolution (Governance Principle #11):**
- Technical disagreement → PA-04 Architect has final say
- Product disagreement → PA-02 PM has final say
- Security override → PA-08 can halt any task (immediate escalation to PA-01)
- Priority dispute → PA-01 Dispatcher is final arbiter

---

## 5. Error Handling

| Severity | Action | Owner |
|----------|--------|-------|
| Recoverable | Auto-retry (max 2, with new evidence) | Executing agent |
| Blocking | Escalate with blocker format (CLAUDE.md §9) | Next in hierarchy |
| Security | Immediate halt + PA-08 audit | PA-08 Security |
| Critical | User notification + evidence pack | PA-01 Dispatcher |

**Prohibited (CLAUDE.md §10b):** No repeated retries without new evidence. No brute-force.

---

## 6. Active MCP Servers

From `.mcp.json` (core profile):

| Server | Status | Purpose |
|--------|--------|---------|
| `filesystem` | ACTIVE | File operations in `D:/Project` |
| `sqlite` | ACTIVE | DB inspection against `platform.db` |
| `fetch` | ACTIVE | HTTP/API validation |

Optional (`.mcp.optional.json`): `puppeteer`, `claude`, `postgres`, `github`, `google-search`
See `orchestrator/mcp-registry.md` for full registry.

---

## 7. Skills Registry

From `skills/` directory (Python implementations):

| Skill | File | Used By |
|-------|------|---------|
| Agile/Scrum | `agile_scrum.py` | PA-02 PM |
| API-First Design | `api_first_design.py` | PA-04 Architect |
| Clean Architecture | `clean_architecture.py` | PA-05 Backend |
| Design Thinking | `design_thinking.py` | PA-02 PM |
| DevOps/SRE | `devops_sre.py` | PA-09 DevOps |
| DDD | `domain_driven_design.py` | PA-04 Architect |
| Lean Startup | `lean_startup.py` | PA-03 Market |
| OWASP Security | `owasp_security.py` | PA-08 Security |
| TDD/BDD | `tdd_bdd.py` | PA-07 QA |
| UX Research | `ux_research.py` | PA-06 Frontend |

---

## Cross-References
- Team routing triggers: `CLAUDE.md §5a`
- Handoff protocol: `.agent/AGENT_PROTOCOLS.md`
- Context loading: `.agent/CONTEXT_ENGINE.md`
- Token budget: `.agent/COST_RULES.md`
- Full agent details: `orchestrator/agent-registry.md`
- Phase lifecycle: `orchestrator/phase-structure-v4.md`
