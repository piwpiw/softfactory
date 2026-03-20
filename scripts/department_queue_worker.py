#!/usr/bin/env python3
"""Worker for executing department task batches from CSV queues.

The worker is intentionally lightweight and execution-agnostic:
- reads today's department tasks
- summarizes by priority/workstream/service
- emits structured artifacts for traceability
- leaves room for future integration with real implementation pipelines
"""

from __future__ import annotations

import argparse
import json
import csv
import fnmatch
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from collections import Counter
from datetime import datetime


ROOT_DIR = Path(__file__).resolve().parents[1]


@dataclass
class TaskExecution:
    task_id: str
    title: str
    service: str
    workstream: str
    priority: str
    target: str
    status: str
    note: str
    found_paths: list[str]


def _is_task_file_like(path_pattern: str) -> bool:
    lowered = (path_pattern or "").strip().lower()
    if not lowered:
        return False
    return any(ch in lowered for ch in ("*", "?", "[", "]"))


def _collect_targets(raw_target: str) -> list[str]:
    if not raw_target:
        return []
    separators = [",", ";", "|"]
    parts = [raw_target]
    for sep in separators:
        new_parts: list[str] = []
        for item in parts:
            new_parts.extend(item.split(sep))
        parts = new_parts
    return [part.strip() for part in parts if part.strip()]


def _expand_targets(target_patterns: list[str]) -> list[Path]:
    output: list[Path] = []
    for pattern in target_patterns:
        expanded = list(ROOT_DIR.glob(pattern))
        if expanded:
            output.extend(expanded)
            continue

        # support patterns like "web/platform/*.html" when cwd differs
        if _is_task_file_like(pattern):
            matched = [p for p in ROOT_DIR.rglob("*") if fnmatch.fnmatch(p.as_posix(), pattern.replace("\\", "/"))]
            output.extend(sorted(set(matched)))
            continue

        fallback = ROOT_DIR / pattern
        if fallback.exists():
            output.append(fallback)
    return sorted(set(output))


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _evaluate_task(row: dict[str, str]) -> TaskExecution:
    task_id = _normalize_text(row.get("task_id"))
    title = _normalize_text(row.get("title"))
    service = _normalize_text(row.get("service_name"))
    workstream = _normalize_text(row.get("workstream"))
    priority = _normalize_text(row.get("priority"))
    target = _normalize_text(row.get("target"))
    target_parts = _collect_targets(target)
    found = _expand_targets(target_parts)
    if found:
        status = "ok"
        note = f"resolved {len(found)} file(s)"
    else:
        status = "blocked"
        note = "target not found"
    if target_parts and not found:
        note = f"missing target: {', '.join(target_parts[:5])}"
    elif target_parts and len(found) >= 1 and "api.js" in target:
        status = "ok"
    return TaskExecution(
        task_id=task_id,
        title=title,
        service=service,
        workstream=workstream,
        priority=priority,
        target=target,
        status=status,
        note=note,
        found_paths=[str(p.relative_to(ROOT_DIR)) for p in found],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute one department's task queue")
    parser.add_argument("--department-id", required=True, help="Department ID, e.g., T1")
    parser.add_argument(
        "--department",
        default="",
        help="Department name (optional; defaults to task file context)",
    )
    parser.add_argument("--task-file", required=True, help="Input department task CSV")
    parser.add_argument("--output-dir", required=True, help="Execution output root directory")
    return parser.parse_args()


def read_tasks(task_file: Path) -> list[dict[str, str]]:
    with task_file.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def summarize_tasks(tasks: list[dict[str, str]]) -> tuple[dict, dict[str, list[str]], list[TaskExecution]]:
    priority_counter = Counter()
    workstream_counter = Counter()
    service_counter = Counter()
    by_service: dict[str, list[str]] = {}
    by_status_counter: Counter[str] = Counter()
    executed_tasks: list[TaskExecution] = []

    for task in tasks:
        execution = _evaluate_task(task)
        executed_tasks.append(execution)

        priority = execution.priority or "Unknown"
        workstream = execution.workstream or "Unknown"
        service = execution.service or "Unknown"
        task_id = execution.task_id

        priority_counter[priority] += 1
        workstream_counter[workstream] += 1
        service_counter[service] += 1
        by_status_counter[execution.status] += 1
        by_service.setdefault(service, []).append(task_id)
        if execution.status != "ok":
            by_service.setdefault(f"{service}:{execution.status}", []).append(task_id)

    return (
        {
            "total_tasks": len(tasks),
            "by_priority": dict(priority_counter),
            "by_workstream": dict(workstream_counter),
            "by_service": dict(service_counter),
            "by_status": dict(by_status_counter),
        },
        by_service,
        executed_tasks,
    )


def main() -> int:
    args = parse_args()
    task_file = Path(args.task_file)
    output_dir = Path(args.output_dir)
    dept = args.department_id
    department_name = args.department or dept

    tasks = read_tasks(task_file)
    summary, by_service, executed_tasks = summarize_tasks(tasks)
    blocked_task_count = summary.get("by_status", {}).get("blocked", 0)
    return_code = 0 if blocked_task_count == 0 else 1
    top_blockers = [task.task_id for task in executed_tasks if task.status == "blocked"][:80]
    blocker_count = len(top_blockers)

    execution_ts = datetime.utcnow().isoformat() + "Z"
    payload: dict[str, Any] = {
        "executed_at": execution_ts,
        "department_id": args.department_id,
        "department": department_name,
        "task_file": str(task_file),
        "task_count": len(tasks),
        "blocked_count": blocker_count,
        "summary": summary,
        "executions": [vars(item) for item in executed_tasks],
        "return_code": return_code,
    }

    out_json = output_dir / f"{dept}_execution_result.json"
    out_md = output_dir / f"{dept}_execution_result.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Department Execution Result",
        "",
        f"- department_id: `{args.department_id}`",
        f"- department: `{department_name}`",
        f"- task_file: `{task_file.name}`",
        f"- executed_at: `{execution_ts}`",
        f"- total_tasks: `{summary['total_tasks']}`",
        "",
        "## Task Distribution",
        "",
        "### By Priority",
    ]

    for k, v in summary["by_priority"].items():
        lines.append(f"- {k}: {v}")

    lines.extend(["", "### By Workstream"])
    for k, v in summary["by_workstream"].items():
        lines.append(f"- {k}: {v}")

    lines.extend(["", "### By Service"])
    for k, v in summary["by_service"].items():
        lines.append(f"- {k}: {v}")

    lines.extend(["", "### By Status"])
    for k, v in summary["by_status"].items():
        lines.append(f"- {k}: {v}")

    if blocked_task_count:
        lines.extend(["", "### Blocked Task IDs"])
        for task_id in top_blockers:
            lines.append(f"- {task_id}")
        if len(top_blockers) < summary["by_status"].get("blocked", 0):
            lines.append(
                f"- ... and {summary['by_status'].get('blocked', 0) - len(top_blockers)} more"
            )
    else:
        lines.extend(["", "### Blocked Task IDs", "- none"])

    lines.extend(["", "## Service Task IDs"])
    for service, task_ids in by_service.items():
        lines.append(f"- {service}")
        lines.extend([f"  - `{task_id}`" for task_id in task_ids])

    lines.extend(["", "### Task Evidence"])
    for item in executed_tasks:
        lines.append(
            f"- {item.task_id} | {item.service} | {item.workstream} | {item.target or '-'} | {item.status} | {item.note}"
        )
        if item.found_paths:
            lines.append(f"  - {', '.join(item.found_paths[:4])}")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[{args.department_id}] executed {summary['total_tasks']} tasks (blocked={blocked_task_count}) -> "
        f"{out_json.name}, {out_md.name}"
    )
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
