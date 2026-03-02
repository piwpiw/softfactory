# Context Engine & Memory Management

> **Version:** 2026-03-02 | **Status:** ACTIVE | **Parent:** CLAUDE.md §1 Import #3
> **Purpose:** Context preservation, memory hierarchy, tag-based retrieval — enforces CLAUDE.md §3–§4

---

## 1. Context Tags (Hashtag Search Protocol)

Per CLAUDE.md §4: **search tags first, full read never by default.**

| Tag | Location | Content |
|-----|----------|---------|
| `#phase` | `orchestrator/phase-structure-v4.md` | Current phase (-1 to 7), active agents |
| `#errors` | `shared-intelligence/pitfalls.md` | Known pitfalls PF-001+ with prevention |
| `#constraints` | `CLAUDE.md §10` | Quality gates, prohibited actions |
| `#file_functions` | Handoff payloads in `shared-intelligence/handoffs/` | Changed files + function names |
| `#decisions` | `shared-intelligence/decisions.md` | ADR-0001+ architectural decisions |
| `#handoff` | `shared-intelligence/handoffs/` | Structured handoff records |
| `#patterns` | `shared-intelligence/patterns.md` | Reusable solutions PAT-001+ |
| `#cost` | `shared-intelligence/cost-log.md` | Token usage, budget status |
| `#pitfalls` | `shared-intelligence/pitfalls.md` | Failure registry PF-001+ |

**Rule:** Always search by tag before reading a full file. Record which tag + line range was loaded in any memory update.

---

## 2. Document Hierarchy (Actual Project Paths)

```
D:/Project/
│
├── CLAUDE.md                          ← Policy root (≤500 lines, §0-§12)
│
├── .agent/                            ← Implementation layer
│   ├── AGENT_SYSTEM.md                ← Agent lifecycle, T↔PA mapping
│   ├── CONTEXT_ENGINE.md              ← This file (context rules)
│   ├── AGENT_PROTOCOLS.md             ← Handoff format, escalation
│   ├── COST_RULES.md                  ← Token budget, model costs
│   └── workflows/
│       └── context-sync.md            ← Policy sync procedure
│
├── orchestrator/                      ← Governance runtime
│   ├── agent-registry.md              ← PA-01~10, SA-01~08 definitions
│   ├── mcp-registry.md                ← MCP server inventory (11 servers)
│   ├── phase-structure-v4.md          ← 8-phase lifecycle (-1 to 7)
│   ├── lean-execution-protocol.md     ← Execution rules
│   └── prompt-templates.md            ← Agent prompt standards
│
├── shared-intelligence/               ← Cross-team knowledge base
│   ├── patterns.md                    ← PAT-001~023 reusable solutions
│   ├── pitfalls.md                    ← PF-001~049 failure registry
│   ├── decisions.md                   ← ADR-0001~0012+ decision log
│   ├── cost-log.md                    ← Token usage tracking
│   ├── handoffs/                      ← Completed handoff records
│   ├── checkpoints/                   ← Phase completion snapshots
│   └── archive/                       ← Historical items (>6 months)
│
├── memory/                            ← Auto-memory (persists across sessions)
│   └── MEMORY.md                      ← Index file (≤200 lines)
│
├── agents/                            ← Python agent implementations
│   ├── 01_dispatcher/ ~ 10_telegram_reporter/
│
└── skills/                            ← Python skill modules
    ├── agile_scrum.py ~ ux_research.py (10 files)
```

---

## 3. Context Window Rules

Per CLAUDE.md §3 (MCP Runtime Contract):

| Scope | Lines | When |
|-------|-------|------|
| **Tag search** | 0 (index only) | Always first step — find relevant tag |
| **Default window** | ≤120 lines around tag | Normal reads after tag match |
| **Section read** | Full section | Explicit reason documented |
| **Full file** | Entire file | Safety/incident reason only |

**Prohibited loads (CLAUDE.md §4):**
- ❌ Never load CONTEXT_ENGINE.md in full by default
- ❌ Never full-read `.agent/` files without tag search first
- ❌ No recursive context expansion beyond 2 levels
- ❌ No full-file reads without documented reason

---

## 4. Memory Hierarchy

| Layer | Path | Max Size | Update Frequency |
|-------|------|----------|-----------------|
| **L1: Session** | Working memory | N/A | Real-time |
| **L2: Persistent** | `memory/MEMORY.md` | ≤200 lines | Session end |
| **L3: Shared** | `shared-intelligence/*.md` | No limit (but use tags) | On discovery |
| **L4: Governance** | `.agent/*.md` + `orchestrator/*.md` | Per file | On policy change |
| **L5: Archive** | `shared-intelligence/archive/` | No limit | Monthly rotation |

**MEMORY.md Rules:**
- Index only — link to topic files for details
- Lines after 200 are truncated by system
- Update at session end, not during execution
- Never duplicate content already in shared-intelligence/

---

## 5. Auto-Sync Triggers

| Event | Action | Target |
|-------|--------|--------|
| Session start | Load MEMORY.md L1 cache | memory/MEMORY.md |
| Tag search | Return ≤120 lines around match | Any indexed file |
| Post-handoff | Load receiver's context tags | shared-intelligence/handoffs/ |
| Phase transition | Checkpoint current state | shared-intelligence/checkpoints/ |
| Policy change | Run context-sync workflow | .agent/workflows/context-sync.md |
| Session end | Update MEMORY.md if changes found | memory/MEMORY.md |

---

## 6. Search Priority Order

When looking for information, follow this order:

1. **MEMORY.md** — check if answer is already indexed
2. **Tag search** — `#errors`, `#patterns`, `#decisions` etc.
3. **Grep/Glob** — targeted file search with patterns
4. **Section read** — ≤120 lines around match
5. **Full read** — only with documented reason
6. **Explore agent** — for multi-file deep research

**Never skip to step 5 or 6 without trying steps 1–4 first.**

---

## Cross-References
- Tag source definitions: `CLAUDE.md §4`
- Window size rules: `CLAUDE.md §3`
- Prohibited actions: `CLAUDE.md §10b`
- Sync workflow: `.agent/workflows/context-sync.md`
- Cost of reads: `.agent/COST_RULES.md`
