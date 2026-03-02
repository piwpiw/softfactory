# Token Cost Rules & Budget Management

> **Version:** 2026-03-02 | **Status:** ACTIVE | **Parent:** CLAUDE.md §1 Import #5
> **Purpose:** Token budgets, model selection, cost optimization — enforces CLAUDE.md §10, Principle #9

---

## 1. Model Cost Table

From `orchestrator/phase-structure-v4.md` §Model Strategy:

| Model | ID | Cost/1K tokens | Use Case |
|-------|----|----------------|----------|
| **Haiku 4.5** | `claude-haiku-4-5-20251001` | ~$0.003 | Default — all routine phases |
| **Sonnet 4.6** | `claude-sonnet-4-6` | ~$0.015 | Critical — requirements, security, deploy |
| **Opus 4.6** | `claude-opus-4-6` | ~$0.075 | Override — user-escalated only |

**Selection Rule:** Always start with Haiku. Upgrade to Sonnet only for phases marked CRITICAL. Opus requires explicit user request.

---

## 2. Session Budget

| Metric | Value | Source |
|--------|-------|--------|
| Total budget | 200,000 tokens | `shared-intelligence/cost-log.md` |
| Target completion | ≤150,000 tokens (75%) | CLAUDE.md Principle #9 |
| Warning threshold | >175,000 tokens (87.5%) | Trigger: simplify output |
| Hard limit | 200,000 tokens (100%) | System-enforced |

---

## 3. Model Selection Per Phase

From `orchestrator/phase-structure-v4.md`:

| Phase | Name | Default Model | Upgrade to Sonnet? |
|-------|------|--------------|-------------------|
| -1 | Research | Haiku | No |
| 0 | Planning | Haiku | No |
| 1 | Requirement | Haiku | **Yes — spec is source of truth** |
| 2 | Documentation | Haiku | **Yes — everyone relies on this** |
| 3 | Design | Haiku | No |
| 4 | Development | Haiku | No |
| 5 | Testing | Haiku | **Yes — security validation** |
| 6 | Finalization | Haiku | No |
| 7 | Delivery | Haiku | **Yes — before production** |

**Target mix:** 75% Haiku, 25% Sonnet → 76% cost reduction vs all-Sonnet.

---

## 4. Tool Cost Optimization

### Read Operations (highest token impact)
- ✅ Tag search first (`#phase`, `#errors` etc.) — 0 content tokens
- ✅ `Glob` / `Grep` for file search — returns paths or matches only
- ✅ `Read` with `offset` + `limit` — bounded window
- ✅ Max 120 lines per context window (CLAUDE.md §3)
- ❌ Never: `cat`, `head`, `tail`, `sed` via Bash
- ❌ Never: Full-file read without documented reason

### Edit Operations
- ✅ `Edit` tool (sends diff only) — minimal tokens
- ✅ Function/file scope (CLAUDE.md §3)
- ✅ Batch multiple edits in single message
- ❌ Never: `Write` for small changes (sends entire file)
- ❌ Never: Multiple sequential Edits when batchable

### Search Operations
- ✅ `Grep` with `head_limit` parameter
- ✅ `Glob` with specific patterns (`**/*.py`, not `**/*`)
- ✅ `output_mode: "files_with_matches"` (default, cheapest)
- ❌ Never: Manual `grep`/`rg` via Bash
- ❌ Never: Full-repo scan (CLAUDE.md §10b)

### Agent Operations
- ✅ `Explore` agent for multi-pass research
- ✅ Parallel agents for independent queries
- ✅ `model: "haiku"` on agent calls for quick tasks
- ❌ Never: Agent for single file reads
- ❌ Never: Nested agents (max depth: 1)

### Output Formatting
- ✅ Markdown tables (compact)
- ✅ Summary format, not exhaustive lists
- ✅ `file_path:line_number` references (not full code blocks)
- ❌ Never: Reproduce entire config files
- ❌ Never: Line-by-line code walkthroughs

---

## 5. Cost-Saving Patterns

From `shared-intelligence/patterns.md`:

| # | Pattern | Token Savings | Technique |
|---|---------|--------------|-----------|
| 1 | **Search-First** | ~60% | Grep → Read specific lines (not full file) |
| 2 | **Batch-Edit** | ~40% | Combine 3+ edits into 1 tool call |
| 3 | **Summary-First** | ~50% | Table output for large diffs |
| 4 | **Scope-Limit** | ~30% | File type filters in Grep (`glob: "*.py"`) |
| 5 | **Parallel-Agent** | ~25% latency | Independent queries in parallel |

---

## 6. Historical Cost Data

From `shared-intelligence/cost-log.md` (2026-02 Infrastructure Sprint):

| Team | Tokens | Cost | Deliverables | Tokens/Deliverable |
|------|--------|------|-------------|-------------------|
| Orchestrator | 45,230 | $0.136 | 1 (framework) | 45.2K |
| Team A | 12,450 | $0.037 | 4 (guidelines) | 3.1K |
| Team B | 18,900 | $0.057 | 5 (infrastructure) | 3.8K |
| Team C | 35,670 | $0.107 | 6 (error tracker) | 5.9K |
| Team G | 8,240 | $0.025 | 5 (performance) | 1.6K |
| Team H | 6,180 | $0.019 | 1 (telegram) | 6.2K |
| **Total** | **126,670** | **$0.381** | **22** | **~5.8K avg** |

**Benchmark:** Target ≤6K tokens per deliverable for routine work.

---

## 7. Budget Monitoring Protocol

| Usage % | Status | Action |
|---------|--------|--------|
| 0–75% | 🟢 Normal | Continue as planned |
| 75–87% | 🟡 Warning | Switch to summary-only output, reduce exploratory reads |
| 87–95% | 🟠 Critical | Complete current task only, no new exploration |
| 95–100% | 🔴 Emergency | Emit final handoff and stop |

---

## Cross-References
- Token policy: `CLAUDE.md §10`
- Prohibited actions: `CLAUDE.md §10b`
- Principle #9 (Cost-Conscious): `CLAUDE.md §12`
- Cost tracking: `shared-intelligence/cost-log.md`
- Model strategy: `orchestrator/phase-structure-v4.md §Model Strategy`
- Patterns library: `shared-intelligence/patterns.md`
