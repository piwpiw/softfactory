# 📝 Agent 01 — Chief Dispatcher

> **Purpose**: **Role:** Central router and conflict arbitrator for the entire Deca-Agent ecosystem.
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Agent 01 — Chief Dispatcher 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Role:** Central router and conflict arbitrator for the entire Deca-Agent ecosystem.

## Responsibilities
- Receive all incoming tasks
- Apply Sequential Thinking to evaluate feasibility and routing
- Dispatch tasks to the correct downstream agents
- **Sole escalation target** when any agent detects a conflict

## Triggers
- New mission created
- Any agent sends a BLOCKED status hand-off

## Outputs
- Hand-off message to Agent 02 (PM) and Agent 03 (Analyst)
- Updated CLAUDE.md Change Log entry

## Key Rules
- Must re-evaluate roadmap on every conflict
- Never routes directly to Dev/QA — must go through PM → Architect first