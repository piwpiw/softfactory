#!/usr/bin/env python3
"""
Team Work Manager — Automated task orchestration for SNS Automation Global-Level Upgrade
Manages 14 interdependent tasks across 9 teams with dependency resolution and parallel execution.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import sys


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    team: str
    name: str
    depends_on: List[str]
    deliverable: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self):
        d = asdict(self)
        d['status'] = d['status'].value
        return d


class WorkManager:
    """Centralized task orchestrator with dependency resolution"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._init_tasks()

    def _init_tasks(self):
        """Initialize all 14 tasks with dependencies"""
        tasks_def = [
            # Phase 1: Parallel
            Task("T01", "Team B", "DB models expansion (SNSCampaign, SNSAccount, SNSPost, 5 new models)",
                 [], "backend/models.py"),
            Task("T02", "Team A", "PRD + Platform Matrix + API Spec",
                 [], "docs/sns-auto/SNS_PRD_v2.md, PLATFORM_MATRIX.md"),

            # Phase 2: After T01, T02
            Task("T03", "Team E", "APScheduler installation + requirements.txt",
                 ["T01"], "requirements.txt updated"),
            Task("T04", "Team C", "Create sns_platforms/ package with 9 clients",
                 ["T01"], "backend/services/sns_platforms/"),

            # Phase 3: After T03, T04
            Task("T05", "Team C", "Create scheduler.py with background job",
                 ["T03", "T04"], "backend/scheduler.py"),
            Task("T06", "Team C", "Rewrite sns_auto.py (32 endpoints, ~900 lines)",
                 ["T01", "T04"], "backend/services/sns_auto.py"),

            # Phase 4: After T06 (+ T05 for Telegram)
            Task("T07", "Team F", "Security audit (OAuth, upload, OWASP)",
                 ["T06"], "Security audit completed"),
            Task("T08", "Team C", "Frontend modifications (5 pages)",
                 ["T06"], "create.html, schedule.html, analytics.html, accounts.html, settings.html"),
            Task("T09", "Team C", "Frontend new pages (2 pages)",
                 ["T06"], "inbox.html, campaigns.html"),
            Task("T10", "Team C", "api.js expansion (25 new functions)",
                 ["T06"], "web/platform/api.js updated"),
            Task("T11", "Team D", "Integration tests (sns_advanced.py)",
                 ["T06"], "tests/integration/test_sns_advanced.py"),
            Task("T12", "Team G", "Caching layer (redis-ready)",
                 ["T06"], "backend/services/sns_cache.py"),
            Task("T13", "Team H", "Telegram SNS integration (handlers)",
                 ["T05", "T06"], "daemon/handlers/sns_handler.py"),

            # Phase 5: Final validation
            Task("T14", "Team A", "Final validation + TEAM_WORK_STATUS.md",
                 ["T07", "T08", "T09", "T10", "T11", "T12", "T13"], "Project completion report"),
        ]

        for task in tasks_def:
            self.tasks[task.id] = task

    def get_ready_tasks(self) -> List[Task]:
        """Return tasks that can start (no blocking dependencies)"""
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            if all(self.tasks[dep].status == TaskStatus.COMPLETED for dep in task.depends_on):
                ready.append(task)
        return sorted(ready, key=lambda t: t.id)

    def get_blocked_tasks(self) -> List[Task]:
        """Return tasks blocked by unfinished dependencies"""
        blocked = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                blocking_deps = [dep for dep in task.depends_on
                                 if self.tasks[dep].status != TaskStatus.COMPLETED]
                if blocking_deps:
                    task.status = TaskStatus.BLOCKED
                    blocked.append(task)
        return blocked

    def mark_completed(self, task_id: str, error: Optional[str] = None):
        """Mark task as completed or failed"""
        if task_id not in self.tasks:
            print(f"[ERROR] Task {task_id} not found")
            return

        task = self.tasks[task_id]
        now = datetime.utcnow().isoformat()

        if error:
            task.status = TaskStatus.FAILED
            task.error_message = error
            task.completed_at = now
            print(f"[FAILED] {task_id} ({task.team}): {error}")
        else:
            task.status = TaskStatus.COMPLETED
            task.completed_at = now
            print(f"[OK] {task_id} ({task.team}): COMPLETED - {task.name}")

    def start_task(self, task_id: str):
        """Mark task as in-progress"""
        if task_id not in self.tasks:
            return
        task = self.tasks[task_id]
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow().isoformat()

    def status(self) -> str:
        """Return formatted status report"""
        output = []
        output.append("\n" + "=" * 80)
        output.append("TEAM WORK MANAGER - SNS Automation Global-Level Upgrade")
        output.append("=" * 80)

        # Summary stats
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        blocked = sum(1 for t in self.tasks.values() if t.status == TaskStatus.BLOCKED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)

        output.append(f"\n[PROGRESS] {completed}/{total} completed | {in_progress} in-progress | {blocked} blocked | {failed} failed")
        output.append(f"   Completion: {int(completed/total*100)}%")

        # Ready tasks
        ready = self.get_ready_tasks()
        if ready:
            output.append(f"\n[READY] {len(ready)} tasks ready to start:")
            for task in ready:
                output.append(f"   {task.id} | {task.team:10} | {task.name}")

        # In-progress
        in_prog = [t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]
        if in_prog:
            output.append(f"\n[IN_PROGRESS] {len(in_prog)} tasks:")
            for task in in_prog:
                output.append(f"   {task.id} | {task.team:10} | {task.name}")

        # Blocked
        blocked_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.BLOCKED]
        if blocked_tasks:
            output.append(f"\n[BLOCKED] {len(blocked_tasks)} tasks:")
            for task in blocked_tasks:
                deps = ", ".join(task.depends_on)
                output.append(f"   {task.id} | waiting for: {deps}")

        # Completed
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        if completed_tasks:
            output.append(f"\n[COMPLETED] {len(completed_tasks)} tasks:")
            for task in completed_tasks:
                output.append(f"   {task.id} | {task.team:10} | {task.name}")

        # Failed
        failed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]
        if failed_tasks:
            output.append(f"\n[FAILED] {len(failed_tasks)} tasks:")
            for task in failed_tasks:
                output.append(f"   {task.id} | {task.team:10} | {task.error_message}")

        output.append("\n" + "=" * 80 + "\n")
        return "\n".join(output)

    def to_markdown(self) -> str:
        """Generate TEAM_WORK_STATUS.md"""
        lines = []
        lines.append("# Team Work Manager - SNS Automation v2.0")
        lines.append(f"\n**Last updated:** {datetime.utcnow().isoformat()}")

        # Summary
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        lines.append(f"\n## Progress Summary")
        lines.append(f"**{completed}/{total} tasks completed ({int(completed/total*100)}%)**\n")

        # Tasks by status
        for status in [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.PENDING, TaskStatus.FAILED]:
            tasks = [t for t in self.tasks.values() if t.status == status]
            if not tasks:
                continue

            icon = {"completed": "[OK]", "in_progress": "[>>]", "blocked": "[!!]", "pending": "[  ]", "failed": "[XX]"}[status.value]
            lines.append(f"## {icon} {status.value.upper()} ({len(tasks)})\n")

            lines.append("| Task | Team | Deliverable | Status |")
            lines.append("|------|------|-------------|--------|")

            for task in sorted(tasks, key=lambda t: t.id):
                lines.append(f"| {task.id} | {task.team} | {task.deliverable[:40]}... | {task.status.value} |")

            lines.append("")

        return "\n".join(lines)

    def save_status(self):
        """Save status to JSON and Markdown"""
        with open("D:/Project/TEAM_WORK_STATUS.json", "w") as f:
            data = {task_id: task.to_dict() for task_id, task in self.tasks.items()}
            json.dump(data, f, indent=2)

        with open("D:/Project/TEAM_WORK_STATUS.md", "w") as f:
            f.write(self.to_markdown())


def main():
    manager = WorkManager()

    if len(sys.argv) < 2:
        print(manager.status())
        return

    cmd = sys.argv[1]

    if cmd == "--status":
        print(manager.status())
    elif cmd == "--markdown":
        print(manager.to_markdown())
    elif cmd == "--save":
        manager.save_status()
        print("✅ Status saved to TEAM_WORK_STATUS.json and TEAM_WORK_STATUS.md")
    elif cmd == "--ready":
        ready = manager.get_ready_tasks()
        print(f"🟢 {len(ready)} tasks ready to start:")
        for task in ready:
            print(f"  - {task.id}: {task.name}")
    elif cmd.startswith("--mark-complete="):
        task_id = cmd.split("=")[1]
        manager.mark_completed(task_id)
        manager.save_status()
        print(manager.status())
    elif cmd.startswith("--mark-failed="):
        parts = cmd.split("=", 1)
        task_id = parts[0].split("=")[1]
        error = parts[1] if len(parts) > 1 else "Unknown error"
        manager.mark_completed(task_id, error)
        manager.save_status()
        print(manager.status())
    else:
        print(f"Unknown command: {cmd}")
        print("Usage:")
        print("  python team_work_manager.py --status      # Show current status")
        print("  python team_work_manager.py --ready       # Show tasks ready to start")
        print("  python team_work_manager.py --mark-complete=T01")
        print("  python team_work_manager.py --mark-failed=T01=Error message")
        print("  python team_work_manager.py --save        # Save status files")


if __name__ == "__main__":
    main()
