# 📝 Mission Lifecycle

> **Purpose**: **Deca-Agent Ecosystem | Mission Management Specification**
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Mission Lifecycle 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Deca-Agent Ecosystem | Mission Management Specification**

---

## Mission States

```
    ┌─────────────────────────────────────────────────────┐
    │                  MISSION LIFECYCLE                   │
    └─────────────────────────────────────────────────────┘

    [INPUT]
       │
       ▼
  ┌─────────┐    Dispatcher    ┌─────────────┐
  │ PENDING │ ───routes────→  │ IN_PROGRESS │
  └─────────┘                  └──────┬──────┘
                                      │
                         ┌────────────┴──────────────┐
                         │                           │
                    conflict?                   advancing?
                         │                           │
                         ▼                           ▼
                   ┌─────────┐              ┌──────────────┐
                   │ BLOCKED │              │  Phase Loop  │
                   └────┬────┘              └──────┬───────┘
                        │                         │
                   resolved?              all phases done?
                        │                         │
                        ▼                         ▼
                   IN_PROGRESS              ┌──────────┐
                                            │ COMPLETE │
                                            └────┬─────┘
                                                 │
                                         retro recorded?
                                                 │
                                                 ▼
                                          ┌──────────┐
                                          │ ARCHIVED │
                                          └──────────┘
```

---

## Mission Phases

| Phase | Owner | Activities | Exit Condition |
|-------|-------|-----------|----------------|
| PLANNING | 01 Dispatcher | Task intake, routing, WSJF | Execution plan issued |
| RESEARCH | 02 PM + 03 Analyst | Market analysis, requirements | PRD drafted |
| DESIGN | 04 Architect | ADR, domain model, OpenAPI | Architecture approved |
| DEVELOPMENT | 05 Backend + 06 Frontend | Parallel implementation | Code review passed |
| VALIDATION | 07 QA + 08 Security | Test execution, security audit | All P0/P1 resolved |
| DEPLOYMENT | 09 DevOps | CI/CD, blue-green, runbook | Health checks pass |
| REPORTING | 10 Reporter | Telegram notifications, summary | Stakeholders notified |

---

## Phase Transitions

### PLANNING → RESEARCH
**Trigger:** Dispatcher issues `HandOffMessage` to PM + Analyst
**Gate:** WSJF score calculated, execution plan documented

### RESEARCH → DESIGN
**Trigger:** PM + Analyst complete and merge outputs (PRD + Market Analysis)
**Gate:** PRD status = REVIEW or APPROVED

### DESIGN → DEVELOPMENT
**Trigger:** Architect delivers ADR + OpenAPI spec
**Gate:** Architecture reviewed by Backend + Frontend; no blockers

### DEVELOPMENT → VALIDATION
**Trigger:** Backend + Frontend complete implementation
**Gate:** Code review passed; dev environment stable

### VALIDATION → DEPLOYMENT
**Trigger:** QA + Security complete parallel audit
**Gate:** Zero P0/P1 bugs; no CRITICAL/HIGH security findings

### DEPLOYMENT → REPORTING
**Trigger:** DevOps confirms successful deployment + health checks
**Gate:** All SLO targets met; rollback not triggered

### REPORTING → COMPLETE
**Trigger:** Reporter sends mission completion notification
**Gate:** Telegram notification confirmed sent

### COMPLETE → ARCHIVED
**Trigger:** Retrospective recorded (Rule 12)
**Gate:** Retrospective document in `logs/missions.jsonl`

---

## API Reference

```python
from core import get_manager, MissionPhase

mgr = get_manager()

# Create
m = mgr.create("M-003", "CooCook MVP Launch", "02/Product-Manager")

# Start
mgr.start("M-003", "01/Chief-Dispatcher")

# Advance phases
mgr.advance_phase("M-003", MissionPhase.RESEARCH, "02/Product-Manager")
mgr.advance_phase("M-003", MissionPhase.DESIGN, "04/Solution-Architect")
mgr.advance_phase("M-003", MissionPhase.DEVELOPMENT, "05/Backend-Developer")

# Block (conflict)
mgr.block("M-003", "Security critical finding — deployment halted", "08/Security-Auditor")

# Unblock
mgr.unblock("M-003", "01/Chief-Dispatcher")

# Complete
mgr.complete("M-003", "09/DevOps-Engineer")

# Retrospective (Rule 12 mandatory)
mgr.record_retrospective(
    "M-003",
    what_went_well=["ConsultationBus prevented 3 conflicts"],
    what_to_improve=["Design phase needs 1 extra day buffer"],
    action_items=["Add OpenAPI review gate to pipeline"],
    recorded_by="01/Chief-Dispatcher",
)
```

---

## Event Log Format (`logs/missions.jsonl`)

```json
{"event_type": "CREATED",     "mission_id": "M-003", "status": "PENDING",     "phase": "PLANNING", "timestamp": "..."}
{"event_type": "IN_PROGRESS", "mission_id": "M-003", "status": "IN_PROGRESS", "phase": "PLANNING", "timestamp": "..."}
{"event_type": "PHASE:DESIGN","mission_id": "M-003", "status": "IN_PROGRESS", "phase": "DESIGN",   "timestamp": "..."}
{"event_type": "COMPLETED",   "mission_id": "M-003", "status": "COMPLETE",    "phase": "REPORTING","timestamp": "..."}
{"event_type": "RETROSPECTIVE","mission_id":"M-003", "retrospective": {...},                        "timestamp": "..."}
```

---

## Rule 12 — Retrospective Obligation

Every completed mission MUST have a retrospective recorded.
Retrospective format: **Start / Stop / Continue** (Agile standard).

| Dimension | Question |
|-----------|---------|
| What went well? | Continue doing these |
| What to improve? | Stop or change these |
| Action items? | Start doing these next mission |

Retrospectives are queryable from `logs/missions.jsonl` for cross-mission learning.

---

*Maintained by the Deca-Agent ecosystem | Source: `core/mission_manager.py`*