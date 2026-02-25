# Orchestrator — Complete Governance & Execution System
> **Master Reference** for all governance, architecture, and execution rules
> **Version**: 3.0 | **Updated**: 2026-02-25 | **Status**: PRODUCTION

---

## 📋 **Document Hierarchy** (Read in Order)

```
1. CLAUDE.md (root)
   ├─ Project standards & principles (15 governance principles)
   ├─ Role definitions (Supervisor/Approver/Integrator)
   └─ Import chain (read these first)
       │
       ├─> shared-intelligence/patterns.md (reusable patterns)
       ├─> shared-intelligence/decisions.md (all ADRs)
       ├─> shared-intelligence/pitfalls.md (failure prevention)
       │
       └─> orchestrator/ (governance layer — THIS DIR)
           ├─ README.md (this file — integration guide)
           ├─ mcp-registry.md (10 external connections)
           ├─ agent-registry.md (authority matrix)
           │
           ├─ phase-structure-v4.md (7 phases: Research→Plan→Req→Doc→Design→Code→Test)
           │  └─ Maps to: Prompt Templates (below)
           │
           ├─ prompt-templates.md (7 fixed prompts, parameter injection)
           │  └─ Applied in each phase
           │
           ├─ orchestration-engine.md (task dependency graph, smart parallelization)
           │  └─ Uses: core/mission_manager.py
           │
           ├─ lean-execution-protocol.md (append-only docs, context auto-compact)
           │  └─ Applied to all documentation
           │
           └─ token-budget-strategy.md (prediction, allocation, recovery)
               └─ Monitored via: shared-intelligence/cost-log.md

2. core/ (Python execution layer)
   ├─ agent_spawner.py (dynamic agent creation, recursive)
   ├─ consultation_bus.py (inter-agent communication)
   ├─ mission_manager.py (task state machine, dependencies)
   └─ AGENT_COLLABORATION_LAYER.md (integration guide)
```

---

## 🔄 **Execution Flow**

```
User Request
    ↓
CLAUDE.md (Check IMPORTS)
    ↓
orchestrator/ (Governance rules)
├─ phase-structure-v4.md (which phases?)
├─ prompt-templates.md (which prompts?)
├─ orchestration-engine.md (parallel or serial?)
├─ mcp-registry.md (which tools?)
└─ agent-registry.md (which agents?)
    ↓
core/ (Python implementation)
├─ agent_spawner (create agents)
├─ consultation_bus (coordinate)
└─ mission_manager (track missions)
    ↓
Project Execution
    ↓
shared-intelligence/
├─ decisions.md (log all decisions) ← ADR-0001, ADR-0002, ...
├─ patterns.md (catalog successful patterns)
├─ pitfalls.md (record failures)
└─ cost-log.md (track tokens)
    ↓
CLAUDE.md (Update import chain for next project)
```

---

## 📄 **File Reference Guide**

### **Phase Structure v4.0**
- **What**: 7-phase execution model (Research through Delivery)
- **Why**: Spec-first, doc-first, review-heavy architecture
- **How**: Each phase has research, planning, coding, testing, deployment
- **Links**:
  - Maps to prompt-templates.md (each phase has a template)
  - Uses mission_manager.py (dependency tracking)
  - Subject to lean-execution-protocol.md (patch-only updates)

### **Prompt Templates v1.0**
- **What**: 7 reusable phase prompts (no repetition)
- **Why**: Eliminate 500-word custom prompts per project
- **How**: Template (200 words) + parameters (50 words) = complete prompt
- **Links**:
  - Implements phase-structure-v4.md (each phase template)
  - Uses: orchestration-engine.md (task assignment)
  - Archived in: shared-intelligence/decisions.md (as ADR-XXX)

### **Orchestration Engine v2.0**
- **What**: Task dependency graph + smart parallelization
- **Why**: Maximize parallelism, eliminate bottlenecks
- **How**: Auto-detect parallel groups, sequential dependencies
- **Links**:
  - Implements: phase-structure-v4.md (phase sequencing)
  - Uses: core/mission_manager.py (execute)
  - Uses: core/agent_spawner.py (spawn agents)
  - Controlled by: token-budget-strategy.md (resource limits)

### **Lean Execution Protocol v1.0**
- **What**: Append-only documentation, delta-based reviews
- **Why**: Reduce context overhead, eliminate full rewrites
- **How**: Core doc (v1.0) + PATCH LOG (v1.1, v1.2, ...)
- **Links**:
  - Applied to: ALL shared-intelligence/ documents
  - Applied to: ALL orchestrator/ documents
  - Saves: 46% tokens per iteration (65K → 35K)

### **Token Budget Strategy**
- **What**: Prediction, allocation, monitoring, recovery
- **Why**: Prevent budget overruns, enable proactive decisions
- **How**: Phase-based multiplier model, per-agent limits, auto-recovery
- **Links**:
  - Monitored in: shared-intelligence/cost-log.md
  - Tracked via: scripts/project_reporter.py
  - Dashboard: Sonolbot /report command

### **MCP Registry**
- **What**: 10 external tool connections (filesystem, GitHub, search, etc.)
- **Why**: Declare all external dependencies, prevent ad-hoc API calls
- **How**: MCP stdio + SSE transport, scoped permissions
- **Links**:
  - Enforced by: agent-registry.md (authority matrix)
  - Validated in: orchestration-engine.md (task execution)

### **Agent Registry**
- **What**: Authority matrix (who can do what)
- **Why**: Prevent unauthorized actions, enforce governance
- **How**: Role-based access control, scoped actions per agent
- **Links**:
  - Implemented by: core/agent_spawner.py (spawn with authority)
  - Checked by: core/consultation_bus.py (message validation)
  - Enforced by: CLAUDE.md Section 17 (15 principles)

---

## 🎯 **Key Design Principles** (Summarized)

1. **Spec-First**: Document before code (phase-structure-v4.md)
2. **Doc-First**: Design before development (prompt-templates.md)
3. **Review-Heavy**: 2-3 agents review each artifact (phase-structure-v4.md #overlapping-responsibility)
4. **Lean Iteration**: Append-only docs, patch-only updates (lean-execution-protocol.md)
5. **Token-Aware**: Budget prediction & monitoring (token-budget-strategy.md)
6. **Agent-Generated**: Agents spawn agents, coordinate via bus (AGENT_COLLABORATION_LAYER.md)
7. **Auto-Parallel**: Tasks parallelize automatically (orchestration-engine.md)
8. **Failure-Tolerant**: Max 3 retries, fallback agents (mission_manager.py)

---

## ⚡ **Quick Reference**

| Need | See | Priority |
|------|-----|----------|
| **Start new project** | phase-structure-v4.md | Phase -1 |
| **Write phase prompt** | prompt-templates.md | Phase X |
| **Run tasks in parallel** | orchestration-engine.md | Real-time |
| **Track decisions** | shared-intelligence/decisions.md | After each decision |
| **Record lessons** | shared-intelligence/pitfalls.md | After each failure |
| **Check reusable patterns** | shared-intelligence/patterns.md | Before designing |
| **Monitor budget** | shared-intelligence/cost-log.md | Per task |
| **Update documentation** | lean-execution-protocol.md | Append-only |
| **Create agent** | core/agent_spawner.py | On demand |
| **Coordinate agents** | core/consultation_bus.py | Real-time |
| **Track missions** | core/mission_manager.py | Per phase |

---

## 🔗 **Cross-References**

**Phase Structure ↔ Prompt Templates**
```
Phase -1 (Research) ← Template: Phase -1 RESEARCH PROMPT
Phase 0 (Planning) ← Template: Phase 0 PLANNING PROMPT
Phase 1 (Requirement) ← Template: Phase 1 REQUIREMENT PROMPT
... (6 more mappings)
```

**Orchestrator ↔ Core Layer**
```
orchestration-engine.md (task graph)
    ↓ implements
core/mission_manager.py (mission state machine)
    ↓ uses
core/agent_spawner.py (spawn agents)
    ↓ coordinate via
core/consultation_bus.py (async message bus)
```

**Governance ↔ Execution**
```
CLAUDE.md (15 principles)
    ↓ enforces
orchestrator/agent-registry.md (authority matrix)
    ↓ implemented by
core/agent_spawner.py (spawn with authority)
    ↓ applied to
core/consultation_bus.py (message validation)
```

---

## 🚀 **Next Steps**

After reading this, read in order:
1. **phase-structure-v4.md** (7 phases overview)
2. **prompt-templates.md** (7 prompts)
3. **orchestration-engine.md** (task execution)
4. **lean-execution-protocol.md** (documentation rules)
5. **core/AGENT_COLLABORATION_LAYER.md** (Python integration)

---

**Version**: 3.0 | **Status**: INTEGRATED | **Last Updated**: 2026-02-25
