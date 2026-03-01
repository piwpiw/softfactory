# 📝 Consultation Protocol

> **Purpose**: **ConsultationBus Specification | Deca-Agent Ecosystem**
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Consultation Protocol 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**ConsultationBus Specification | Deca-Agent Ecosystem**

---

## Overview

The `ConsultationBus` enables bidirectional, asynchronous consultations between agents.
All consultations are logged to `logs/consultations.jsonl` for audit and retrospective review.

```
Agent A ──(CLARIFICATION)──→ Agent B
         ←──(RESPONSE)──────

Agent A ──(REVIEW)──────────→ Agent B, C, D (broadcast)
         ←──(RESPONSE)────── (from each)

Agent X ──(ESCALATION)──────→ 01/Dispatcher (always)
         ←──(RESPONSE)──────
```

---

## Consultation Types

| Type | When to Use | Escalates to |
|------|-------------|-------------|
| `CLARIFICATION` | Need definition or requirement clarity | Stays bilateral |
| `REVIEW` | Peer review of an output artifact | Stays bilateral |
| `DEPENDENCY` | Blocked waiting on another agent's output | Stays bilateral |
| `ESCALATION` | Unresolvable conflict or critical blocker | Always → 01/Dispatcher |

---

## Priority Levels

| Priority | Use Case | Expected Response |
|----------|----------|-------------------|
| `LOW` | Non-blocking background question | Async, next available |
| `MEDIUM` | Standard inter-agent consultation | Within same mission cycle |
| `HIGH` | Blocking progress on mission | Immediate (current cycle) |
| `URGENT` | Critical blocker / security issue | Immediate (override) |

---

## API Reference

### `consult(from_agent, to_agent, question, context, priority, type)`
Single bilateral consultation.

```python
from core import get_bus, ConsultationType, ConsultationPriority

bus = get_bus()
response = bus.consult(
    from_agent="02/Product-Manager",
    to_agent="03/Market-Analyst",
    question="What is the estimated TAM for food-tech in SEA in 2026?",
    context="Preparing PRD Section 3 for CooCook M-002",
    priority=ConsultationPriority.HIGH,
    consultation_type=ConsultationType.CLARIFICATION,
)
print(response.answer)
```

### `broadcast(from_agent, question, target_agents, context)`
Broadcast same question to multiple agents.

```python
responses = bus.broadcast(
    from_agent="04/Solution-Architect",
    question="Does this API design satisfy your requirements?",
    target_agents=["02/Product-Manager", "05/Backend-Developer", "06/Frontend-Developer"],
    context="Reviewing openapi.yaml for CooCook M-002",
)
for r in responses:
    print(f"{r.from_agent}: {r.answer}")
```

### `escalate(from_agent, conflict)`
Escalate conflict to Dispatcher. Always priority URGENT. Bypasses circular detection.

```python
response = bus.escalate(
    from_agent="07/QA-Engineer",
    conflict="Security audit found CRITICAL finding. Deployment must be blocked. Dispatcher decision required.",
)
```

---

## Circular Consultation Detection

The bus tracks active consultation chains. If A→B and B tries to consult A on the same chain:

```
A → B → A   # BLOCKED: ConsultationLoopError raised
A → B → C   # ALLOWED: no loop detected
```

Escalations always bypass circular detection (they terminate at Dispatcher).

---

## Consultation Log Format (`logs/consultations.jsonl`)

Each line is a JSON object:

```json
{"type": "REQUEST",  "request_id": "abc12345", "from_agent": "02/Product-Manager", "to_agent": "03/Market-Analyst", "question": "...", "context": "...", "priority": "HIGH", "consultation_type": "CLARIFICATION", "timestamp": "2026-02-22T10:00:00"}
{"type": "RESPONSE", "request_id": "abc12345", "from_agent": "03/Market-Analyst",  "to_agent": "02/Product-Manager", "answer": "...", "confidence": 0.9, "sources": ["..."], "timestamp": "2026-02-22T10:00:01"}
```

---

## Rule 11 Trigger (`.clauderules`)

> If uncertainty > 70%, the agent **MUST** consult relevant agents via ConsultationBus.

### Uncertainty Estimation Guidelines

| Scenario | Estimated Uncertainty | Action |
|----------|----------------------|--------|
| Clear requirements, familiar domain | < 30% | No consultation needed |
| Partially defined requirements | 30–70% | Optional consultation |
| Ambiguous requirements / new domain | > 70% | **MANDATORY** consultation |
| Security / legal implications | Any | Always consult 08/Security |
| Architectural decision | Any | Always consult 04/Architect |

---

## Examples by Agent

### PM (02) consults Analyst (03)
```python
# Before finalizing PRD — need market validation
bus.consult("02/Product-Manager", "03/Market-Analyst",
    "Validate: 'Digital nomad food-travel app in SEA is a $2B TAM'. Confirm or correct.",
    consultation_type=ConsultationType.CLARIFICATION)
```

### Architect (04) consults Backend (05)
```python
# Review API design feasibility
bus.consult("04/Solution-Architect", "05/Backend-Developer",
    "Can we implement WebSocket-based real-time chef availability with current stack?",
    consultation_type=ConsultationType.REVIEW)
```

### Security (08) escalates to Dispatcher (01)
```python
bus.escalate("08/Security-Auditor",
    "SQL injection vulnerability in Recipe Search API. CVSS 9.8. Deployment must halt.")
```

---

*Maintained by the Deca-Agent ecosystem | Source: `core/consultation.py`*