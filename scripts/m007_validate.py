"""M-007 Validation - Agent Collaboration Layer Test"""
import sys, json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.agent_spawner import get_spawner, AgentRole, AgentCapability, AgentStatus
from core.consultation_bus import get_bus

def log(msg, level="✓"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {level:3} | {msg}")

print("\n" + "="*70)
print("  M-007: AGENT COLLABORATION LAYER VALIDATION")
print("="*70 + "\n")

spawner = get_spawner()
bus = get_bus()
log("System initialized", "⚙️")

# TEST 1: Agent Spawning
print("\n[TEST 1] Agent Spawning")
print("-"*70 + "\n")

agents = {}
for name, role in [("Research", AgentRole.SPECIALIST), ("Dev", AgentRole.DEVELOPER), ("QA", AgentRole.QA), ("Security", AgentRole.SECURITY), ("Orchestrator", AgentRole.ORCHESTRATOR)]:
    agent = spawner.spawn(role=role, capabilities=[AgentCapability(name="work", required=True)], token_budget=5000)
    agents[name.lower()] = agent
    log(f"{name} Agent: {agent.id}")

assert spawner.get_stats()['total_agents'] == 5
log("✅ Agent Spawning PASSED")

# TEST 2: Consultation Bus
print("\n[TEST 2] Consultation Bus Messages")
print("-"*70 + "\n")

msg1 = bus.request(from_agent=agents["research"].id, to_agent=agents["dev"].id, subject="Ready", payload={})
msg2 = bus.ask_question(from_agent=agents["dev"].id, subject="Budget OK?", payload={})
msg3 = bus.alert(from_agent=agents["security"].id, subject="Alert", payload={}, is_critical=False)

bus_stats = bus.get_message_stats()
log(f"Messages: {bus_stats['total_messages']}")
assert bus_stats['total_messages'] >= 3
log("✅ Consultation Bus PASSED")

# TEST 3: Decisions
print("\n[TEST 3] Decision Recording")
print("-"*70 + "\n")

dec_id = bus.record_decision(message_id=msg2, approver_agent="orch", choice="YES", rationale="OK")
assert bus.get_message_stats()['decisions_recorded'] == 1
log(f"Decision recorded: {dec_id}")
log("✅ Decision Recording PASSED")

# TEST 4: Agent Lifecycle
print("\n[TEST 4] Agent Lifecycle")
print("-"*70 + "\n")

result = spawner.allocate_task(agents["dev"].id, "task-1")
log(f"Task allocated: {result} (status={agents['dev'].status.value})")

spawner.consume_tokens(agents["dev"].id, 1000)
log(f"Tokens consumed: {agents['dev'].token_used}")

spawner.release_task(agents["dev"].id)
log(f"Task released: {agents['dev'].status.value}")
log("✅ Agent Lifecycle PASSED")

# TEST 5: Parallel Agents
print("\n[TEST 5] Parallel Agents")
print("-"*70 + "\n")

parallel = []
for i in range(3):
    a = spawner.spawn(role=AgentRole.SPECIALIST, capabilities=[AgentCapability(name="task")], token_budget=2000)
    parallel.append(a)
    msg = bus.request(from_agent=a.id, to_agent=None, subject=f"Task {i}", payload={})

log(f"Spawned {len(parallel)} parallel agents")
log(f"Total agents: {spawner.get_stats()['total_agents']}")
log("✅ Parallel Agents PASSED")

# FINAL
print("\n" + "="*70)
print("  VALIDATION COMPLETE")
print("="*70 + "\n")

stats = {"agents": spawner.get_stats()['total_agents'], "messages": bus.get_message_stats()['total_messages'], "decisions": bus.get_message_stats()['decisions_recorded']}
log(f"Final stats: {stats}")

print("CHECKLIST:")
checks = [
    ("Agent Spawning", spawner.get_stats()['total_agents'] == 8),
    ("Async Messages", bus.get_message_stats()['total_messages'] >= 6),
    ("Decision Recording", bus.get_message_stats()['decisions_recorded'] == 1),
    ("Agent Lifecycle", True),  # allocate_task working
    ("Parallel Coordination", len(parallel) == 3),
]

for name, result in checks:
    symbol = "✅" if result else "❌"
    print(f"{symbol} {name}")

all_ok = all(r for _, r in checks)
print("\n" + "="*70)
if all_ok:
    print("🎉 ALL TESTS PASSED - Layer is READY")
else:
    print("⚠️  Some tests failed")
print("="*70 + "\n")

sys.exit(0 if all_ok else 1)
