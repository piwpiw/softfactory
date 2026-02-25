# Agent Collaboration Layer — Self-Generating Multi-Agent System
> **Architecture**: Agents spawn agents, coordinate via consultation bus, manage missions autonomously
> **Status**: IMPLEMENTED | **Version**: 1.0 | **Date**: 2026-02-25

---

## 🏗️ **Core Layer Design**

### **Three Pillars**

```
┌─────────────────────────────────────────────────────────────┐
│                   MISSION ORCHESTRATION                      │
│  (core/mission_manager.py)                                   │
│  - Task state machine (PENDING → IN_PROGRESS → COMPLETE)    │
│  - Dependency resolution & cycle detection                   │
│  - Parallel group detection                                  │
│  - Quality metrics & retry logic                             │
└─────────────────────────────────────────────────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
    ┌────┴──────┐           ┌────┴──────┐           ┌────┴──────┐
    │            │           │            │           │            │
    │  AGENT     │           │CONSULTATION│           │MISSION     │
    │  SPAWNER   │◄────────►│   BUS      │◄────────►│ MANAGER    │
    │            │           │            │           │            │
    └────────────┘           └────────────┘           └────────────┘
         Lifecycle                Communication           Coordination
         Management                 & Handoff             & Dependency
```

---

## 1️⃣ **Agent Spawner** (`core/agent_spawner.py`)

### **Purpose**
- Dynamic agent creation (self-generating agents)
- Agent lifecycle management
- Authority matrix enforcement
- Resource allocation (tokens, parallelism limits)

### **Key Classes**

#### **AgentRole (Enum)**
```python
ORCHESTRATOR     # Master coordinator
BUSINESS         # Business strategist
ARCHITECT        # Solution architect
DEVELOPER        # Development lead
QA               # QA engineer
DEVOPS           # DevOps engineer
SECURITY         # Security auditor
SUPPORT          # Generic support
SPECIALIST       # Dynamic roles (spawned as needed)
```

#### **AgentProfile (Dataclass)**
- `id`: Unique identifier
- `role`: AgentRole enum
- `status`: PENDING | ACTIVE | WORKING | BLOCKED | COMPLETED | FAILED | IDLE
- `parent_id`: Agent that spawned this one (enables recursion)
- `capabilities`: List[AgentCapability] (what it can do)
- `authority`: AgentAuthority (what it's allowed to do)
- `token_budget`: Allocated tokens
- `assigned_task_id`: Current mission

#### **AgentSpawner (Class)**
```python
spawner = AgentSpawner(max_agents=20)

# Spawn new agent
profile = spawner.spawn(
    role=AgentRole.DEVELOPER,
    capabilities=[...],
    parent_id="orchestrator-1",  # Can be None for root agents
    token_budget=5000
)

# Find available agents
available = spawner.find_available_agents(role=AgentRole.DEVELOPER)

# Allocate task
spawner.allocate_task(agent_id, task_id)

# Monitor
stats = spawner.get_stats()
# → {"total_agents": 8, "active_agents": 3, "capacity": 0.4}
```

### **Agent Authority Matrix**

Each agent has defined authority:

```python
AgentAuthority(
    max_parallel_agents=4,           # Can manage up to 4 sub-agents
    can_spawn_agents=True,           # Can create new agents
    can_override_decisions=False,    # Cannot override orchestrator
    scoped_to_phases=["4", "5"],     # Allowed phases
    forbidden_actions=[              # Forbidden actions
        "delete_database",
        "merge_main_branch",
        "deploy_production"
    ]
)
```

---

## 2️⃣ **Consultation Bus** (`core/consultation_bus.py`)

### **Purpose**
- Real-time inter-agent communication
- Request-response patterns
- Question escalation to orchestrator
- Alert broadcasting
- Task handoff protocol

### **Message Types**

#### **REQUEST**
Agent A → Agent B (specific task)
```python
bus.request(
    from_agent="dev-lead-1",
    to_agent="qa-engineer-2",
    subject="Code review needed",
    payload={"code_path": "backend/app.py", "priority": "high"}
)
```

#### **QUESTION**
Agent → Orchestrator (decision needed)
```python
bus.ask_question(
    from_agent="architect-1",
    subject="Scope reduction needed?",
    payload={
        "reason": "token_budget_exceeded",
        "current_spend": 28000,
        "budget": 25000,
        "options": ["cut_feature_X", "extend_timeline"]
    },
    requires_decision=True
)
```

#### **ALERT**
Agent → All (escalation)
```python
bus.alert(
    from_agent="security-auditor-1",
    subject="CRITICAL: SQL injection vulnerability found",
    payload={"file": "backend/auth.py", "line": 42},
    is_critical=True
)
```

#### **HANDOFF**
Agent A → Agent B (task transfer)
```python
bus.handoff(
    from_agent="frontend-dev-1",
    to_agent="qa-engineer-2",
    task_id="M-006-phase-5",
    context={"test_cases": 47, "coverage": 0.89}
)
```

#### **DECISION** (response to QUESTION)
Orchestrator → Agent (decision recorded)
```python
bus.reply(
    to_message_id="msg-xyz",
    from_agent="orchestrator-1",
    payload={"decision": "cut_feature_X", "reason": "token_overbudget"},
    is_decision=True
)

bus.record_decision(
    message_id="msg-xyz",
    approver_agent="orchestrator-1",
    choice="cut_feature_X",
    rationale="Token budget constraints",
    impact={"scope_reduction": "15%"}
)
```

### **Message Priority Levels**

```python
CRITICAL  # Requires immediate action (security, failures)
HIGH      # Important (decisions, handoffs)
NORMAL    # Regular communication
LOW       # Informational (updates)
```

### **ConsultationBus (Class)**

```python
bus = get_bus()

# Publish message
message_id = bus.request(...)

# Consume messages
while True:
    msg = bus.consume(agent_id="dev-lead-1", timeout=0.5)
    if msg:
        handle_message(msg)

# Subscribe to events
def on_question_received(msg):
    orchestrator_response(msg)

bus.subscribe("question", on_question_received, agent_id="orchestrator-1")

# Get stats
stats = bus.get_message_stats()
# → {"total_messages": 342, "queue_size": 12, "decisions_recorded": 28}
```

---

## 3️⃣ **Mission Manager** (`core/mission_manager.py`)

### **Purpose**
- Task lifecycle management
- Dependency resolution
- Parallel group detection
- Retry & failure recovery
- Quality metrics tracking

### **Mission Lifecycle**

```
CREATE MISSION
    ↓
PENDING (waiting for dependencies)
    ↓
READY (dependencies met)
    ↓
ACTIVE (assigned to agent, executing)
    ↓
COMPLETED ✓  OR  FAILED (with retry) OR  CANCELLED
    ↓
ARCHIVED (for memory management)
```

### **Key Operations**

```python
manager = get_mission_manager()

# Create mission
mission = manager.create_mission(
    name="Implement API authentication",
    phase=MissionPhase.DEVELOPMENT,
    assigned_agent_id="dev-lead-1",
    token_budget=5000,
    priority=8,
    input_data={"tech_stack": "FastAPI+JWT"}
)

# Add dependencies
manager.add_dependency(
    mission.id,
    "M-006-phase-2",  # This mission depends on phase 2 finishing
    dependency_type="blocks_on",
    severity="hard"
)

# Check if ready
if manager.check_ready(mission.id):
    print("All dependencies met, mission ready")

# Get parallelizable groups
parallel_groups = manager.get_parallelizable_missions()
# → [[M-001, M-002], [M-003, M-004]]  # 2 groups that can run in parallel

# Mark complete
manager.mark_complete(
    mission.id,
    output_data={"endpoints": 5, "tests": 47},
    quality_score=0.95
)

# Or mark failed with retry
if manager.mark_failed(mission.id, "API test failed", retry=True):
    print("Retrying mission...")
else:
    print("Mission gave up after 3 retries")
```

---

## 🔗 **Integration Pattern: Complete Workflow**

### **Scenario: Orchestrator spawns agents, they communicate, manage missions**

```
1. ORCHESTRATOR STARTS NEW PROJECT
   ├─ Mission Manager: Create Phase -1 mission
   └─ Agent Spawner: Spawn Market Analyst, Architect, Security agents (3 parallel)

2. AGENTS RESEARCH (PARALLEL)
   Market Analyst → Consultation Bus: "Market research complete, posting to shared-intelligence"
   Architect → Consultation Bus: "Architecture baseline ready"
   Security → Consultation Bus: "Security baseline ready"

3. ORCHESTRATOR CHECKS SYNC POINT
   Mission Manager: Phase -1 mission complete?
   └─ Check all 3 dependencies met? YES
   └─ Mark Phase -1 complete, Phase 0 ready

4. PHASE 0: PLANNING (SEQUENTIAL)
   ├─ Business Strategist → Consultation Bus: Question
   │  "Should we add OAuth or simple JWT?"
   │  (REQUIRES DECISION)
   │
   └─ Orchestrator → Consultation Bus: Decision
      "Use OAuth for Phase 1, add JWT in Phase 2"
      (RECORDED to shared-intelligence/decisions.md)

5. DEVELOPMENT PHASE
   ├─ Dev Lead spawns: Backend Dev, Frontend Dev (2 agents)
   ├─ Backend Dev → Consultation Bus: Question
   │  "Database schema approved?"
   │  → Architect reviews → "APPROVED"
   │
   └─ They work in parallel
      └─ QA agent monitoring, asking questions when needed

6. WHEN BLOCKED
   Frontend Dev → Consultation Bus: Alert (HIGH)
   "Backend API response format changed, breaking tests"

   Orchestrator → Consultation Bus: Question
   "Can we fix backwards compatibility?"

   Dev Lead → Decision
   "Adding compatibility layer"

7. COMPLETION
   ├─ Mission Manager: All missions complete?
   ├─ Consultation Bus: Decision log recorded
   ├─ Agent Spawner: Terminate temporary agents
   └─ Orchestrator: Generate final report
```

---

## 📊 **Concurrent Execution Limits**

### **Safe Mode (Recommended)**
- **Max agents**: 4-6
- **Token budget**: 200K
- **Phases**: 2-3 parallel groups
- **Throughput**: 1 project/day
- **Cost**: $0.60-$0.90 per project

### **Aggressive Mode**
- **Max agents**: 8-10
- **Token budget**: 300K
- **Phases**: 4-5 parallel groups
- **Throughput**: 2-3 projects/day
- **Cost**: $1.20-$1.50 per project

### **Extreme Mode** (Not recommended)
- **Max agents**: 15-20
- **Token budget**: 500K+
- **Phases**: 6+ parallel groups
- **Throughput**: 5+ projects/day
- **Cost**: $3.00+ per project
- **Risk**: Context fragmentation, coordination overhead

---

## 🎯 **Key Design Principles**

### **1. Recursion Enabled**
- Orchestrator spawns agents
- Agents can spawn sub-agents
- Sub-agents can spawn specialists
- Each level follows authority matrix

### **2. Communication-First**
- No direct database writes (except core/)
- All inter-agent communication via bus
- All decisions recorded in shared-intelligence
- Full audit trail maintained

### **3. Token-Aware**
- Each agent has token budget
- Spawner tracks usage
- Agent rejects work if budget exceeded
- Orchestrator reallocates or pauses

### **4. Failure-Tolerant**
- Max 3 retries per mission
- Fallback agents available
- Conflicts auto-escalate
- No silent failures

### **5. Lean & Efficient**
- Missions auto-parallelize (no manual coordination)
- Dependencies auto-resolve (cycle detection)
- Context auto-compresses (old messages archived)
- Quality gates prevent rework

---

## ⚡ **Performance Metrics**

| Metric | Target | Method |
|--------|--------|--------|
| **Message latency** | <100ms | Consultation bus timing |
| **Dependency resolution** | <50ms | Mission graph traversal |
| **Agent spawn time** | <500ms | Spawner creation |
| **Decision time** | <2min | Orchestrator approval |
| **Context window utilization** | 80-90% | Token tracking |
| **Parallelization efficiency** | 70%+ | Simultaneous agents / max agents |

---

## 🔧 **Usage in Code**

### **In Orchestrator**
```python
from core.agent_spawner import get_spawner, AgentRole, AgentCapability
from core.consultation_bus import get_bus
from core.mission_manager import get_mission_manager, MissionPhase

spawner = get_spawner()
bus = get_bus()
manager = get_mission_manager()

# Spawn initial agents
business = spawner.spawn(
    role=AgentRole.BUSINESS,
    capabilities=[...],
    token_budget=10000
)

# Create mission
mission = manager.create_mission(
    name="CooCook MVP Phase 5",
    phase=MissionPhase.DEVELOPMENT,
    assigned_agent_id=business.id,
    token_budget=25000
)

# Subscribe to questions
bus.subscribe("question", orchestrator_decision_handler, agent_id="orchestrator-1")

# Monitor
print(spawner.get_stats())
print(bus.get_message_stats())
print(manager.get_statistics())
```

### **In Agent (e.g., Dev Lead)**
```python
from core.consultation_bus import get_bus

bus = get_bus()

# Ask question
msg_id = bus.ask_question(
    from_agent="dev-lead-1",
    subject="Do we have token budget for extra tests?",
    payload={"current_spend": 24000, "requested": 3000},
    requires_decision=True
)

# Wait for response
while True:
    response = bus.consume(agent_id="dev-lead-1", timeout=1.0)
    if response and response.message_type.value == "decision":
        if response.payload.get("choice") == "proceed":
            write_extra_tests()
        else:
            skip_extra_tests()
        break
```

---

## 📋 **Next Steps**

1. ✅ **Implement core layer** (agent_spawner.py, consultation_bus.py)
2. ✅ **Integrate with mission_manager.py** (already exists)
3. 🔄 **Test with M-006 project** (verify agent spawning)
4. 🔄 **Monitor token usage** (ensure budget compliance)
5. 🔄 **Add auto-scaling** (spawn agents on demand based on load)
6. 🔄 **Implement decision history** (log all orchestrator decisions)
7. 🔄 **Dashboard for agent coordination** (real-time visualization)

---

**Version**: 1.0 | **Status**: IMPLEMENTED & READY | **Last Updated**: 2026-02-25
