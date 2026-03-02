#!/usr/bin/env python
"""
Subproject Autopilot

Discovers web subprojects and auto-populates orchestrator/task-queue.json with
agent-ready tasks. Includes loop guards and deduplication to avoid runaway
generation and repeated queue spam.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_STREAMS = [
    {"code": "A", "owner_team": "coordination", "type": "planning", "title": "Define scope and acceptance criteria"},
    {"code": "B", "owner_team": "frontend", "type": "frontend", "title": "Implement and align UI surfaces"},
    {"code": "C", "owner_team": "backend", "type": "backend", "title": "Implement service API and validations"},
    {"code": "D", "owner_team": "architecture", "type": "architecture", "title": "Design data model and contracts"},
    {"code": "E", "owner_team": "security", "type": "security", "title": "Apply security and policy controls"},
    {"code": "F", "owner_team": "product", "type": "product", "title": "Refine generation workflows and UX"},
    {"code": "G", "owner_team": "devops", "type": "devops", "title": "Wire deployment and operations guardrails"},
    {"code": "H", "owner_team": "frontend", "type": "frontend", "title": "Tune accessibility and performance UX"},
    {"code": "I", "owner_team": "qa", "type": "qa", "title": "Create automated QA and regression checks"},
    {"code": "J", "owner_team": "ops-communication", "type": "ops", "title": "Publish runbook and reporting docs"},
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9\\-]+", "-", name.strip().lower())
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "subproject"


def discover_web_subprojects(project_root: Path, include: list[str] | None = None) -> list[dict]:
    web_root = project_root / "web"
    include_set = {_slugify(item) for item in (include or []) if str(item).strip()}
    found = []
    if not web_root.exists():
        return found

    for item in sorted(web_root.iterdir()):
        if not item.is_dir():
            continue
        if item.name.startswith("."):
            continue
        if item.name in {"assets", "css", "js", "images"}:
            continue
        index_file = item / "index.html"
        if not index_file.exists():
            continue
        slug = _slugify(item.name)
        if include_set and slug not in include_set:
            continue
        found.append(
            {
                "slug": slug,
                "name": item.name,
                "index": str(index_file.relative_to(project_root)).replace("\\", "/"),
                "mtime": int(index_file.stat().st_mtime),
            }
        )
    return found


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _queue_path(project_root: Path) -> Path:
    return project_root / "orchestrator" / "task-queue.json"


def _registry_path(project_root: Path) -> Path:
    return project_root / "agent_workspaces" / "_memory" / "subproject_autopilot_registry.json"


def _task_id(slug: str, stream_code: str) -> str:
    return f"AUTO-{slug.upper()}-{stream_code}"


def _pending_count(tasks: list[dict]) -> int:
    return sum(1 for task in tasks if str(task.get("status", "")) in {"pending", "in_progress"})


def autopopulate_task_queue(project_root: Path, policy: dict | None = None) -> dict:
    cfg = dict(policy or {})
    enabled = bool(cfg.get("enabled", True))
    if not enabled:
        return {"enabled": False, "generated": 0, "reason": "disabled"}

    include = cfg.get("include_subprojects") if isinstance(cfg.get("include_subprojects"), list) else []
    max_new = int(cfg.get("max_new_tasks_per_cycle", 30))
    max_pending = int(cfg.get("max_pending_tasks", 300))
    generation_cooldown_sec = int(cfg.get("generation_cooldown_sec", 600))
    cycle_key = int(time.time() // max(generation_cooldown_sec, 1))

    registry = _read_json(_registry_path(project_root), {"version": "2026-03-02", "subprojects": {}, "cycles": []})
    # loop guard: skip duplicate generation attempt inside same cooldown window
    cycles = list(registry.get("cycles", []))
    if cycles and cycles[-1] == cycle_key:
        return {"enabled": True, "generated": 0, "reason": "same_cycle_guard", "cycle_key": cycle_key}

    queue_payload = _read_json(_queue_path(project_root), {"schema_version": "2026-03-02", "tasks": []})
    tasks = queue_payload.get("tasks", []) if isinstance(queue_payload, dict) else []
    tasks = [task for task in tasks if isinstance(task, dict)]
    existing_ids = {str(task.get("task_id", "")) for task in tasks}

    if _pending_count(tasks) >= max_pending:
        return {"enabled": True, "generated": 0, "reason": "pending_cap_reached", "pending": _pending_count(tasks)}

    subprojects = discover_web_subprojects(project_root, include=include)
    generated = []
    for sub in subprojects:
        if len(generated) >= max_new:
            break
        sub_state = registry["subprojects"].get(sub["slug"], {})
        changed = int(sub_state.get("mtime", 0)) != sub["mtime"]
        initialized = bool(sub_state.get("initialized"))

        # Generate tasks for first discovery or source change.
        if initialized and not changed:
            continue

        for stream in DEFAULT_STREAMS:
            if len(generated) >= max_new:
                break
            tid = _task_id(sub["slug"], stream["code"])
            if tid in existing_ids:
                continue
            generated.append(
                {
                    "task_id": tid,
                    "title": f"[{sub['slug']}] {stream['title']}",
                    "status": "pending",
                    "type": stream["type"],
                    "owner_team": stream["owner_team"],
                    "priority": 2 if initialized else 1,
                    "created_at_utc": _utc_now(),
                    "updated_at_utc": _utc_now(),
                    "artifacts": [sub["index"]],
                    "notes": "auto-generated by subproject_autopilot",
                    "source": "subproject_autopilot",
                    "subproject": sub["slug"],
                    "cycle_key": cycle_key,
                }
            )
            existing_ids.add(tid)

        registry["subprojects"][sub["slug"]] = {
            "initialized": True,
            "mtime": sub["mtime"],
            "last_generated_cycle": cycle_key,
            "index": sub["index"],
            "updated_at_utc": _utc_now(),
        }

    if generated:
        tasks.extend(generated)
        queue_payload["schema_version"] = "2026-03-02"
        queue_payload["updated_at_utc"] = _utc_now()
        queue_payload["tasks"] = tasks
        _write_json(_queue_path(project_root), queue_payload)

    cycles.append(cycle_key)
    registry["cycles"] = cycles[-50:]
    registry["last_run_utc"] = _utc_now()
    _write_json(_registry_path(project_root), registry)

    return {
        "enabled": True,
        "generated": len(generated),
        "total_tasks": len(tasks),
        "subprojects_seen": len(subprojects),
        "cycle_key": cycle_key,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    result = autopopulate_task_queue(root, policy={"enabled": True})
    print(json.dumps(result, ensure_ascii=True, indent=2))
