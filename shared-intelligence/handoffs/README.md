# 📝 Handoff Protocol

> **Purpose**: 1. **When to write:** Any task with a downstream dependency (Phase 1 → Phase 2, Agent A → Agent B)
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Handoff Protocol 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **Purpose:** Explicit handoff notes between agents on dependent task chains.
> **Requirement:** Write handoff notes before closing any task that has a downstream agent.
> **Format:** One file per task chain — `[task-id]-handoff.md`

---

## Handoff Rules

1. **When to write:** Any task with a downstream dependency (Phase 1 → Phase 2, Agent A → Agent B)
2. **What to include:**
   - What was completed (factual, no speculation)
   - Known blockers or open questions
   - Next agent's first action
   - Critical files changed
3. **Where:** This directory — `shared-intelligence/handoffs/[task-id]-handoff.md`
4. **When to read:** Every agent reads their incoming handoff BEFORE starting work

---

## Handoff Template

```markdown
# Handoff: [Task ID] → [Next Agent]
**From:** [agent]
**To:** [agent]
**Date:** YYYY-MM-DD HH:MM

## Completed
- [x] What was done

## Artifacts
- `path/to/file.py` — [what changed]

## Open Questions
- [ ] Question 1 (blocking / non-blocking)

## Next Agent's First Action
1. Read [specific file]
2. Run [specific command]
3. Continue from [specific point]

## Risks
- [Any known risks or gotchas]
```

---

## Active Handoffs

| Task ID | From | To | Status | Date |
|---------|------|----|--------|------|
| GOV-001 | Orchestrator | All agents | ✅ COMPLETE | 2026-02-25 |

---

## GOV-001: Governance v3.0 Handoff → All Agents

**From:** Orchestrator
**To:** All agents (read on next session start)
**Date:** 2026-02-25

### Completed
- [x] Created `/shared-intelligence/` with pitfalls.md, patterns.md, decisions.md, cost-log.md
- [x] Created `/orchestrator/` with mcp-registry.md, agent-registry.md
- [x] Updated CLAUDE.md with import chaining + Section 17 governance
- [x] Configured 4 hooks in `.claude/settings.local.json`
- [x] Updated all core docs to 2026-02-25

### Next Agent's First Action
1. Read `shared-intelligence/patterns.md` before writing any new code
2. Append to `shared-intelligence/pitfalls.md` after discovering any issue
3. Append to `shared-intelligence/cost-log.md` after completing any significant task
4. Check `orchestrator/mcp-registry.md` before adding any new external connection