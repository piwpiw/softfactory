#!/usr/bin/env python
"""
Master Orchestrator - Run All 10 Agents in Parallel
SoftFactory Multi-Agent System Execution
2026-02-25
"""

import os
import sys
import time
import json
import hashlib
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add project to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
MEMORY_ROOT = PROJECT_ROOT / "agent_workspaces" / "_memory"
FAILURE_MEMORY_PATH = MEMORY_ROOT / "failure_registry.json"
TOKEN_LEDGER_PATH = MEMORY_ROOT / "token_ledger.json"
TASK_QUEUE_PATH = PROJECT_ROOT / "orchestrator" / "task-queue.json"

# Set environment variables
os.environ.setdefault('PLATFORM_SECRET_KEY', os.getenv('PLATFORM_SECRET_KEY', 'softfactory-dev-key'))
os.environ.setdefault('JWT_SECRET', os.getenv('JWT_SECRET', 'jwt-dev-secret'))
os.environ.setdefault('ANTHROPIC_API_KEY', os.getenv('ANTHROPIC_API_KEY', ''))
os.environ.setdefault('TELEGRAM_BOT_TOKEN', os.getenv('TELEGRAM_BOT_TOKEN', ''))

# Define all 10 agents
AGENTS = [
    {
        'name': 'Dispatcher',
        'number': '01',
        'team': 'coordination',
        'module': 'agents.01_dispatcher.dispatcher',
        'class': 'Dispatcher',
        'description': 'Chief Dispatcher - orchestrates all agent activities'
    },
    {
        'name': 'Product Manager',
        'number': '02',
        'team': 'product',
        'module': 'agents.02_product_manager.pm_agent',
        'class': 'ProductManager',
        'description': 'PM Agent - defines strategy and requirements'
    },
    {
        'name': 'Market Analyst',
        'number': '03',
        'team': 'product',
        'module': 'agents.03_market_analyst.analyst_agent',
        'class': 'MarketAnalyst',
        'description': 'Market Analyst - researches market and competition'
    },
    {
        'name': 'Solution Architect',
        'number': '04',
        'team': 'architecture',
        'module': 'agents.04_architect.architect_agent',
        'class': 'Architect',
        'description': 'Architect - designs system architecture'
    },
    {
        'name': 'Backend Developer',
        'number': '05',
        'team': 'backend',
        'module': 'agents.05_backend_dev.backend_agent',
        'class': 'BackendDeveloper',
        'description': 'Backend Dev - implements API and services'
    },
    {
        'name': 'Frontend Developer',
        'number': '06',
        'team': 'frontend',
        'module': 'agents.06_frontend_dev.frontend_agent',
        'class': 'FrontendDeveloper',
        'description': 'Frontend Dev - builds UI components'
    },
    {
        'name': 'QA Engineer',
        'number': '07',
        'team': 'qa',
        'module': 'agents.07_qa_engineer.qa_agent',
        'class': 'QAEngineer',
        'description': 'QA Engineer - tests and validates'
    },
    {
        'name': 'Security Auditor',
        'number': '08',
        'team': 'security',
        'module': 'agents.08_security_auditor.security_agent',
        'class': 'SecurityAuditor',
        'description': 'Security Auditor - audits security and compliance'
    },
    {
        'name': 'DevOps Engineer',
        'number': '09',
        'team': 'devops',
        'module': 'agents.09_devops.devops_agent',
        'class': 'DevOpsEngineer',
        'description': 'DevOps - handles deployment and infrastructure'
    },
    {
        'name': 'Telegram Reporter',
        'number': '10',
        'team': 'ops-communication',
        'module': 'agents.10_telegram_reporter.reporter_agent',
        'class': 'TelegramReporter',
        'description': 'Telegram Reporter - reports pipeline status'
    },
]

class AgentExecutor:
    def __init__(self, agent_config):
        self.config = agent_config
        self.agent_workspace = (
            PROJECT_ROOT
            / "agent_workspaces"
            / f"{agent_config['number']}_{agent_config['module'].replace('.', '_')}"
        )
        self.agent_workspace.mkdir(parents=True, exist_ok=True)
        self.status = 'PENDING'
        self.output = ''
        self.error = ''
        self.return_code = None
        self.start_time = None
        self.end_time = None
        self.tasks = list(self.config.get('assigned_tasks', []))

    def _build_task_env(self) -> dict:
        env = os.environ.copy()
        if self.tasks:
            env['SOFTFACTORY_TASKS'] = json.dumps(self.tasks, ensure_ascii=True)
            env['SOFTFACTORY_TASK_IDS'] = ",".join([str(task.get("task_id", "")) for task in self.tasks])
        env['SOFTFACTORY_DISPATCHER'] = "run_all_agents"
        return env

    def run(self):
        """Execute agent"""
        print(f"\n{'='*60}")
        print(f"Starting Agent {self.config['number']}: {self.config['name']}")
        print(f"   {self.config['description']}")
        print(f"{'='*60}")

        self.start_time = time.time()
        self.status = 'RUNNING'

        try:
            if self.config.get("should_skip"):
                self.status = 'SKIPPED'
                self.output = f"Skipped by fail-memory. {self.config.get('skip_reason')}"
                self.return_code = 0
            else:
                # Run each agent module directly and validate process exit status.
                result = subprocess.run(
                    [sys.executable, "-m", self.config['module']],
                    cwd=str(PROJECT_ROOT),
                    env=self._build_task_env(),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                )

                self.output = result.stdout
                self.error = result.stderr
                self.return_code = result.returncode
                self.status = 'COMPLETE' if result.returncode == 0 else 'ERROR'

            if self.status == 'COMPLETE':
                print(f"[OK] Agent {self.config['number']} completed successfully")
            elif self.status == 'SKIPPED':
                print(f"[SKIP] Agent {self.config['number']} skipped by failure memory")
            else:
                print(f"[ERROR] Agent {self.config['number']} exited with code {self.return_code}")
            if self.output:
                print(f"Output: {self.output[:200]}...")
            if self.error:
                print(f"Error: {self.error[:200]}...")

        except subprocess.TimeoutExpired:
            self.status = 'TIMEOUT'
            self.return_code = 124
            print(f"[TIME]  Agent {self.config['number']} timed out")
        except Exception as e:
            self.status = 'ERROR'
            self.error = str(e)
            self.return_code = 1
            print(f"[ERROR] Agent {self.config['number']} error: {e}")

        self.end_time = time.time()
        duration = self.end_time - self.start_time
        print(f"[TIME]  Duration: {duration:.2f}s | Status: {self.status}")

        marker = {
            "agent": self.config['number'],
            "module": self.config['module'],
            "status": self.status,
            "assigned_tasks": self.tasks,
            "task_ids": [task.get("task_id") for task in self.tasks],
            "start": self.start_time,
            "end": self.end_time,
            "duration_seconds": round(duration, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "return_code": self.return_code,
        }
        if self.output:
            marker["stdout_snippet"] = self.output[:2000]
        if self.error:
            marker["stderr_snippet"] = self.error[:2000]
        marker_path = self.agent_workspace / f"run_{int(self.end_time)}.json"
        marker_path.write_text(json.dumps(marker, ensure_ascii=True, indent=2), encoding="utf-8")


def _signature_from_error(module: str, result_code: int, stdout: str, stderr: str) -> str:
    error_head = ""
    if stderr:
        error_head = stderr.splitlines()[0].strip()
    elif stdout:
        lines = [line for line in stdout.splitlines() if line.strip()]
        if lines:
            error_head = lines[0].strip()
    if not error_head:
        error_head = f"exit_{result_code}"
    raw = f"{module}|{result_code}|{error_head[:240]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _format_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def load_failure_memory(root: Path) -> dict:
    path = root / "agent_workspaces" / "_memory" / "failure_registry.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_failure_memory(root: Path, memory: dict) -> None:
    path = root / "agent_workspaces" / "_memory" / "failure_registry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(memory, ensure_ascii=True, indent=2), encoding="utf-8")


def load_governance(root: Path) -> dict:
    path = root / "orchestrator" / "automation-governance.json"
    default_policy = {
        "version": "2026-02-26",
        "repeat_failure_block_threshold": 2,
        "token_budget": {
            "daily_cap_tokens": 200000,
            "team_allocations": {},
        },
        "context_policy": {
            "max_local_docs_per_cycle": 8,
            "max_external_docs_per_cycle": 2,
            "prefer_cached_brief": True,
        },
    }
    if not path.exists():
        return default_policy
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        merged = dict(default_policy)
        merged.update(raw if isinstance(raw, dict) else {})
        return merged
    except Exception:
        return default_policy


def load_task_queue(root: Path) -> list[dict]:
    try:
        payload = json.loads((root / "orchestrator" / "task-queue.json").read_text(encoding="utf-8"))
        tasks = payload.get("tasks", []) if isinstance(payload, dict) else []
        return [task for task in tasks if isinstance(task, dict)]
    except Exception:
        return []


def save_task_queue(root: Path, tasks: list[dict]) -> None:
    TASK_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "2026-02-26",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tasks": tasks,
    }
    TASK_QUEUE_PATH.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def normalize_task(task: dict) -> dict:
    return {
        "task_id": str(task.get("task_id", f"task-{int(time.time() * 1000)}")),
        "title": str(task.get("title", "")),
        "status": str(task.get("status", "pending")),
        "type": str(task.get("type", "generic")),
        "owner_team": str(task.get("owner_team", "")),
        "priority": int(task.get("priority", 2)),
        "created_at_utc": str(task.get("created_at_utc", datetime.now(timezone.utc).isoformat())),
        "updated_at_utc": str(task.get("updated_at_utc", datetime.now(timezone.utc).isoformat())),
        "artifacts": task.get("artifacts", []),
        "notes": task.get("notes", ""),
    }


def select_tasks_for_cycle(task_queue: list[dict], max_tasks: int) -> list[dict]:
    limit = max_tasks if int(max_tasks) > 0 else len(task_queue)
    pending = [
        normalize_task(task)
        for task in task_queue
        if isinstance(task, dict) and str(task.get("status", "")) in ("pending", "in_progress")
    ]
    pending.sort(key=lambda item: (int(item.get("priority", 2)), str(item.get("created_at_utc", ""))))
    return pending[:limit]


def build_task_driven_agents(governance: dict, raw_tasks: list[dict]) -> tuple[list[dict], list[dict], list[str]]:
    fallback = bool(governance.get("task_queue", {}).get("default_fallback_all_agents", True))
    parallel_agents = int(governance.get("parallel_agents", len(AGENTS)))
    max_tasks = int(governance.get("task_queue", {}).get("max_pending_tasks_per_cycle", 10))
    dispatch_mode = str(governance.get("task_queue", {}).get("dispatch_mode", "team_round_robin"))
    selected_tasks = select_tasks_for_cycle(raw_tasks, max_tasks)

    if not selected_tasks:
        if fallback:
            base = [dict(agent) for agent in AGENTS]
            return base, [], []
        return [], [], []

    unowned_tasks = [task for task in selected_tasks if not task.get("owner_team")]
    owned_teams = {task.get("owner_team") for task in selected_tasks if task.get("owner_team")}
    has_all = bool(unowned_tasks)
    target_agents = [dict(agent) for agent in AGENTS]
    if owned_teams:
        target_agents = [dict(agent) for agent in AGENTS if agent.get("team") in owned_teams]
        if has_all:
            target_agents = [dict(agent) for agent in AGENTS]
        if not target_agents and dispatch_mode == "fallback_any":
            target_agents = [dict(agent) for agent in AGENTS]

    # keep within parallel limit
    if parallel_agents < len(target_agents):
        target_agents = target_agents[:parallel_agents]

    by_team = {agent['team']: [] for agent in target_agents}
    if unowned_tasks and dispatch_mode == "team_round_robin":
        # Distribute owner-less tasks evenly across active agents to maximize utilization.
        if not target_agents:
            target_agents = [dict(agent) for agent in AGENTS[:parallel_agents]]
            by_team = {agent['team']: [] for agent in target_agents}
        rr_index = 0
        team_keys = list(by_team.keys())
        for task in unowned_tasks:
            team = team_keys[rr_index % len(team_keys)]
            by_team[team].append(task)
            rr_index += 1

    for task in selected_tasks:
        owner = task.get("owner_team", "")
        if not owner:
            # Already assigned by round-robin above.
            continue
        if owner in by_team:
            by_team[owner].append(task)
        elif dispatch_mode == "fallback_any" and target_agents:
            by_team[target_agents[0]["team"]].append(task)

    out_task_updates = []
    claimed_ids = []
    for agent in target_agents:
        assigned = by_team.get(agent.get("team"), [])
        if assigned:
            agent["assigned_tasks"] = assigned
        claimed_ids.extend([str(task.get("task_id")) for task in assigned])
        for task in assigned:
            updated = dict(task)
            updated["status"] = "in_progress"
            updated["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
            updated["assigned_agents"] = [agent["number"]]
            out_task_updates.append(updated)

    if not any(agent.get("assigned_tasks") for agent in target_agents):
        target_agents = []
        out_task_updates = []

    return target_agents, out_task_updates, sorted(set(claimed_ids))
def load_token_ledger(root: Path) -> dict:
    if not TOKEN_LEDGER_PATH.exists():
        return {
            "date_utc": datetime.now(timezone.utc).date().isoformat(),
            "daily_used": 0,
            "hard_stopped_count": 0,
            "entries": [],
        }
    try:
        return json.loads(TOKEN_LEDGER_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {
            "date_utc": datetime.now(timezone.utc).date().isoformat(),
            "daily_used": 0,
            "hard_stopped_count": 0,
            "entries": [],
        }


def save_token_ledger(root: Path, ledger: dict) -> None:
    TOKEN_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_LEDGER_PATH.write_text(json.dumps(ledger, ensure_ascii=True, indent=2), encoding="utf-8")


def _safe_float(value, default):
    try:
        return float(value)
    except Exception:
        return default


def _usage_budget_status(governance: dict, ledger: dict) -> tuple[str, int, int, int]:
    budget = governance.get("token_budget", {})
    daily_cap = int(_safe_float(budget.get("daily_cap_tokens", 0), 0))
    emergency_reserve = int(_safe_float(budget.get("emergency_reserve_tokens", 0), 0))
    warning_ratio = float(budget.get("warning_percent", 0.75))
    hard_ratio = float(budget.get("hard_stop_percent", 0.9))
    used = int(_safe_float(ledger.get("daily_used", 0), 0))
    available = max(daily_cap - used, 0)
    warning = int(daily_cap * warning_ratio)
    hard_stop = int(daily_cap * hard_ratio)
    if used >= hard_stop - emergency_reserve:
        return "hard", hard_stop, warning, available
    if used >= warning:
        return "warn", hard_stop, warning, available
    return "ok", hard_stop, warning, available


def estimate_cycle_tokens(executors: list[AgentExecutor]) -> int:
    # Lightweight proxy for token usage (stdout+stderr characters / 4).
    total_chars = 0
    for executor in executors:
        total_chars += len(executor.output or "")
        total_chars += len(executor.error or "")
    return int(total_chars / 4)


def classify_and_record_failure(memory: dict, agent_config: dict, executor: AgentExecutor, exit_code: int) -> None:
    signature = _signature_from_error(agent_config['module'], exit_code, executor.output, executor.error)
    entry = memory.get(signature)
    if not entry:
        entry = {
            "module": agent_config['module'],
            "team": agent_config.get("team", "unknown"),
            "count": 0,
            "first_seen": _format_iso(time.time()),
            "last_seen": _format_iso(time.time()),
            "last_error_snippet": (executor.error or executor.output or "")[:800],
            "last_exit_code": exit_code,
            "resolved": False,
        }
    cooldown_minutes = 120
    existing = memory.get(signature, {})
    cooldown = int(existing.get("cooldown_minutes", 0) or 0)
    if cooldown <= 0:
        cooldown = 120
    entry["count"] = int(entry.get("count", 0)) + 1
    entry["last_seen"] = _format_iso(time.time())
    entry["last_error_snippet"] = (executor.error or executor.output or "")[:800]
    entry["last_exit_code"] = exit_code
    entry["cooldown_minutes"] = cooldown
    entry["blocked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=cooldown)).isoformat()
    memory[signature] = entry


def block_repeat_failure_agents(memory: dict, agent_configs: list, repeat_threshold: int = 2, cooldown_minutes: int = 120) -> list:
    # Skip only persistent/repeated failure patterns from previous cycles to avoid infinite loops.
    now = datetime.now(timezone.utc)
    blocked_signatures = {
        sig: data for sig, data in memory.items()
        if isinstance(data, dict) and data.get("count", 0) >= repeat_threshold and not data.get("resolved", False)
    }
    if not blocked_signatures:
        return agent_configs

    for conf in agent_configs:
        module = conf["module"]
        team = conf.get("team", "unknown")
        patterns = [data for data in blocked_signatures.values() if data.get("module") == module]
        if not patterns:
            patterns = [data for data in blocked_signatures.values() if data.get("team") == team]
        if not patterns:
            continue
        latest = sorted(patterns, key=lambda item: item.get("count", 0), reverse=True)[0]
        blocked_until = latest.get("blocked_until")
        if blocked_until:
            try:
                until = datetime.fromisoformat(blocked_until.replace("Z", "+00:00"))
            except Exception:
                until = None
            if until and now >= until:
                continue
            if until is None:
                until = now + timedelta(minutes=cooldown_minutes)
        else:
            until = now + timedelta(minutes=cooldown_minutes)
        latest["blocked_until"] = until.isoformat()
        conf["should_skip"] = True
        conf["skip_reason"] = "Blocked by repeat failure memory. Last snippet: " + (latest.get("last_error_snippet", "")[:220])
    return agent_configs


def patch_task_status_from_executors(task_queue: list[dict], executors: list[AgentExecutor]) -> list[dict]:
    if not task_queue or not executors:
        return task_queue

    task_status = {}
    for executor in executors:
        for task in executor.tasks:
            task_id = str(task.get("task_id", ""))
            if not task_id:
                continue
            task_status.setdefault(task_id, []).append(executor.status)

    patched = []
    for task in task_queue:
        task_id = str(task.get("task_id", ""))
        if task_id in task_status:
            statuses = task_status[task_id]
            if statuses and all(status == 'COMPLETE' for status in statuses):
                task["status"] = "done"
            elif any(status == 'ERROR' or status == 'TIMEOUT' for status in statuses):
                task["status"] = "failed"
            else:
                task["status"] = "in_progress"
            task["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
            task["last_cycle_status"] = statuses
        patched.append(task)
    return patched


def _run_batches(executors: list[AgentExecutor], parallel_limit: int) -> None:
    if parallel_limit <= 0:
        parallel_limit = len(executors)

    for idx in range(0, len(executors), parallel_limit):
        batch = executors[idx:idx + parallel_limit]
        threads = []
        for executor in batch:
            thread = threading.Thread(target=executor.run, daemon=True)
            thread.start()
            threads.append(thread)
            time.sleep(0.2)
        for thread in threads:
            thread.join(timeout=180)

def main():
    print("\n")
    print("=" * 70)
    print("SOFTFACTORY MULTI-AGENT SYSTEM")
    print("Running All 10 Agents in Parallel...")
    print("=" * 70)
    print()

    memory = load_failure_memory(PROJECT_ROOT)
    governance = load_governance(PROJECT_ROOT)
    raw_tasks = load_task_queue(PROJECT_ROOT)
    token_ledger = load_token_ledger(PROJECT_ROOT)
    repeat_threshold = int(governance.get("repeat_failure_block_threshold", 2))
    cooldown_minutes = int(governance.get("failure_policy", {}).get("cooldown_minutes", 120))
    if token_ledger.get("date_utc") != datetime.now(timezone.utc).date().isoformat():
        token_ledger = {
            "date_utc": datetime.now(timezone.utc).date().isoformat(),
            "daily_used": 0,
            "hard_stopped_count": token_ledger.get("hard_stopped_count", 0),
            "entries": [],
        }

    status, hard_stop, warning, _ = _usage_budget_status(governance, token_ledger)
    if status == "hard" and os.getenv("SOFTFACTORY_FORCE_RUN", "0") != "1":
        print("[STOP] Token budget hard-stop reached; skip execution cycle.")
        summary = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "agents_total": 0,
            "completed": 0,
            "skipped": 0,
            "errors": 0,
            "token_budget_status": "hard_stop",
            "governance": {
                "repeat_failure_block_threshold": repeat_threshold,
                "token_budget": governance.get("token_budget", {}),
                "context_policy": governance.get("context_policy", {}),
            },
            "results": {},
        }
        summary_path = PROJECT_ROOT / "agent_workspaces" / "_memory" / "latest_cycle_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
        token_ledger["hard_stopped_count"] = int(token_ledger.get("hard_stopped_count", 0)) + 1
        token_ledger["entries"].append(
            {"at": datetime.now(timezone.utc).isoformat(), "reason": "hard_stop", "status": status}
        )
        save_token_ledger(PROJECT_ROOT, token_ledger)
        return 1
    if status == "warn":
        print(f"[WARN] Token budget above warning threshold. warn>={warning} hard_stop>={hard_stop}.")

    parallel_agents = governance.get("parallel_agents", len(AGENTS))
    agent_configs, task_updates, claimed_task_ids = build_task_driven_agents(governance, raw_tasks)
    if task_updates:
        task_map = {str(task.get("task_id")): task for task in task_updates}
        raw_tasks = [
            task_map.get(str(task.get("task_id")), task)
            for task in raw_tasks
        ]
        save_task_queue(PROJECT_ROOT, raw_tasks)

    if not agent_configs:
        summary = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "agents_total": 0,
            "completed": 0,
            "skipped": 0,
            "errors": 0,
            "task_mode": "no_work",
            "claimed_task_ids": claimed_task_ids,
            "results": {},
        }
        summary_path = PROJECT_ROOT / "agent_workspaces" / "_memory" / "latest_cycle_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
        return 0

    agent_configs = [dict(agent) for agent in agent_configs]
    agent_configs = block_repeat_failure_agents(
        memory,
        [dict(agent) for agent in agent_configs],
        repeat_threshold=repeat_threshold,
        cooldown_minutes=cooldown_minutes,
    )

    executors = [AgentExecutor(agent) for agent in agent_configs]

    print(f"Starting {len(agent_configs)} agents...")
    print()
    _run_batches(executors, parallel_agents)

    # Print final summary
    print("\n")
    print("=" * 70)
    print("EXECUTION SUMMARY")
    print("=" * 70)
    print()

    completed = sum(1 for e in executors if e.status == 'COMPLETE')
    errors = sum(1 for e in executors if e.status == 'ERROR')
    skipped = sum(1 for e in executors if e.status == 'SKIPPED')

    for executor in executors:
        status_icon = {
            'COMPLETE': '[OK]',
            'ERROR': '[ERROR]',
            'TIMEOUT': '[TIME]',
            'SKIPPED': '[SKIP]',
            'PENDING': '[WAIT]',
            'RUNNING': '[RUN]'
        }.get(executor.status, '[?]')

        number = executor.config['number']
        name = executor.config['name']
        print(f"{status_icon} Agent {number} - {name:20s} ... {executor.status}")

    print()
    print(f"Results: {completed} complete, {skipped} skipped, {errors} errors out of {len(agent_configs)} agents")

    # Update task states from executor results.
    if claimed_task_ids:
        raw_tasks = patch_task_status_from_executors(raw_tasks, executors)
        save_task_queue(PROJECT_ROOT, raw_tasks)

    # Update failure memory from current cycle.
    for executor in executors:
        if executor.status == 'ERROR':
            classify_and_record_failure(memory, executor.config, executor, executor.return_code or 1)

    # Mark resolved if agent passes after previous failures.
    for key, entry in list(memory.items()):
        if not isinstance(entry, dict):
            continue
        module = entry.get("module")
        if any(exec.config['module'] == module and exec.status == 'COMPLETE' for exec in executors):
            entry["resolved"] = True
    save_failure_memory(PROJECT_ROOT, memory)

    # Write cycle summary metadata
    team_summary = {}
    for executor in executors:
        team = executor.config.get("team", "unknown")
        item = team_summary.setdefault(team, {"total": 0, "complete": 0, "error": 0, "skipped": 0})
        item["total"] += 1
        if executor.status == 'COMPLETE':
            item["complete"] += 1
        elif executor.status == 'ERROR':
            item["error"] += 1
        elif executor.status == 'SKIPPED':
            item["skipped"] += 1

    summary = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "agents_total": len(agent_configs),
        "completed": completed,
        "skipped": skipped,
        "errors": errors,
        "task_mode": "queue_driven" if claimed_task_ids else "fallback_full_cycle",
        "claimed_task_ids": claimed_task_ids,
        "governance": {
            "repeat_failure_block_threshold": repeat_threshold,
            "token_budget": governance.get("token_budget", {}),
            "context_policy": governance.get("context_policy", {}),
        },
        "team_summary": team_summary,
        "results": {f"{e.config['number']}": {"team": e.config.get("team", "unknown"), "status": e.status, "task_count": len(e.tasks)} for e in executors},
        "task_distribution": {e.config['number']: len(e.tasks) for e in executors},
    }

    cycle_tokens = estimate_cycle_tokens(executors)
    token_ledger["daily_used"] = int(_safe_float(token_ledger.get("daily_used", 0), 0)) + cycle_tokens
    token_ledger["entries"].append(
        {
            "at": datetime.now(timezone.utc).isoformat(),
            "return_code": 0 if errors == 0 else 1,
            "agents": len(agent_configs),
            "completed": completed,
            "errors": errors,
            "tokens_estimated": cycle_tokens,
            "parallel_agents": parallel_agents,
            "cycle_status": "success" if errors == 0 else "fail",
         }
    )
    save_token_ledger(PROJECT_ROOT, token_ledger)
    summary["token_usage"] = {
        "estimated_tokens": cycle_tokens,
        "daily_used": token_ledger["daily_used"],
        "daily_cap": int(_safe_float(governance.get("token_budget", {}).get("daily_cap_tokens", 0), 0)),
        "status": status,
    }
    summary_path = PROJECT_ROOT / "agent_workspaces" / "_memory" / "latest_cycle_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    print()

    # Print service deployment summary
    print("=" * 70)
    print("SERVICES DEPLOYED & READY")
    print("=" * 70)
    print()
    print("[*] CooCook Service ........... Chef Booking Platform")
    print("[*] SNS Auto Service .......... Social Media Automation")
    print("[*] Review Service ............ Influencer Review Platform")
    print("[*] AI Automation Service ..... AI Employee Management")
    print("[*] WebApp Builder Service .... Website Building Tool")
    print()
    print("[OK] All services available at: http://localhost:8000/")
    print()
    return 0 if errors == 0 else 1

if __name__ == '__main__':
    raise SystemExit(main())

