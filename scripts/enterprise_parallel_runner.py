#!/usr/bin/env python3
"""Prepare and run enterprise day-plan tasks in parallel by department.

This script is driven by the generated backlog CSV and supports:
1) Preparing per-department task files for today's execution.
2) Running one command per department in parallel with structured logs.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BACKLOG = ROOT_DIR / "docs" / "plans" / "department_backlog_100x10_2026-03-03.csv"
DEFAULT_OUTPUT_ROOT = ROOT_DIR / "docs" / "plans" / "execution"
DEFAULT_HISTORY_JSONL = DEFAULT_OUTPUT_ROOT / "execution_history.jsonl"
DEFAULT_HISTORY_MD = DEFAULT_OUTPUT_ROOT / "EXECUTION_HISTORY.md"


@dataclass
class DepartmentBatch:
    department_id: str
    department: str
    tasks: list[dict[str, str]]
    task_file: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enterprise parallel day-plan runner")
    parser.add_argument("--backlog", type=Path, default=DEFAULT_BACKLOG, help="Input backlog CSV path")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT / dt.date.today().isoformat(),
        help="Output directory for prepared task files and logs",
    )
    parser.add_argument("--mode", choices=("prepare", "run"), default="prepare", help="prepare or run mode")
    parser.add_argument("--today-only", action="store_true", default=True, help="Filter today_candidate=Yes")
    parser.add_argument(
        "--include-all",
        action="store_true",
        default=False,
        help="Include non-today candidates (today_candidate != Yes)",
    )
    parser.add_argument(
        "--priorities",
        default="P0,P1",
        help="Comma-separated priorities to include (default: P0,P1)",
    )
    parser.add_argument(
        "--limit-per-dept",
        type=int,
        default=12,
        help="Number of tasks to keep per department for daily execution",
    )
    parser.add_argument("--max-workers", type=int, default=10, help="Parallel worker count for run mode")
    parser.add_argument(
        "--command-template",
        default="",
        help=(
            "Command template executed per department in run mode. "
            "Available placeholders: {department_id} {department} {task_file} {output_dir}"
        ),
    )
    parser.add_argument(
        "--history-jsonl",
        type=Path,
        default=DEFAULT_HISTORY_JSONL,
        help="Append-only machine-readable execution history path",
    )
    parser.add_argument(
        "--history-md",
        type=Path,
        default=DEFAULT_HISTORY_MD,
        help="Append-only human-readable execution history path",
    )
    parser.add_argument(
        "--session-label",
        default="",
        help="Optional label for grouping this prepare/run cycle in history",
    )
    return parser.parse_args()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def filter_tasks(
    rows: list[dict[str, str]],
    today_only: bool,
    include_all: bool,
    priorities: set[str],
) -> list[dict[str, str]]:
    filtered: list[dict[str, str]] = []
    for row in rows:
        if today_only and not include_all and row.get("today_candidate", "").strip().lower() != "yes":
            continue
        if priorities and row.get("priority", "").strip().upper() not in priorities:
            continue
        filtered.append(row)
    return filtered


def build_batches(
    rows: list[dict[str, str]],
    output_dir: Path,
    limit_per_dept: int,
) -> list[DepartmentBatch]:
    grouped: dict[str, list[dict[str, str]]] = {}
    dept_name: dict[str, str] = {}

    for row in rows:
        dept_id = row.get("department_id", "").strip()
        if not dept_id:
            continue
        grouped.setdefault(dept_id, []).append(row)
        dept_name[dept_id] = row.get("department", "").strip()

    batches: list[DepartmentBatch] = []
    for dept_id in sorted(grouped):
        tasks = sorted(grouped[dept_id], key=lambda x: x.get("task_id", ""))[:limit_per_dept]
        task_file = output_dir / f"{dept_id}_today_tasks.csv"
        batches.append(
            DepartmentBatch(
                department_id=dept_id,
                department=dept_name.get(dept_id, dept_id),
                tasks=tasks,
                task_file=task_file,
            )
        )
    return batches


def write_batches(batches: list[DepartmentBatch], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for batch in batches:
        if not batch.tasks:
            continue
        fieldnames = list(batch.tasks[0].keys())
        with batch.task_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(batch.tasks)


def write_summary(
    output_dir: Path,
    backlog_path: Path,
    filtered_count: int,
    batches: list[DepartmentBatch],
    args: argparse.Namespace,
) -> dict[str, Any]:
    summary = {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "backlog_path": str(backlog_path),
        "mode": args.mode,
        "today_only": args.today_only,
        "priorities": sorted(
            [p.strip().upper() for p in args.priorities.split(",") if p.strip()]
        ),
        "limit_per_dept": args.limit_per_dept,
        "departments": [
            {
                "department_id": b.department_id,
                "department": b.department,
                "task_count": len(b.tasks),
                "task_file": str(b.task_file),
            }
            for b in batches
        ],
        "filtered_task_count": filtered_count,
        "department_count": len(batches),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Daily Parallel Execution Summary",
        "",
        f"- backlog: `{backlog_path}`",
        f"- filtered tasks: `{filtered_count}`",
        f"- departments: `{len(batches)}`",
        f"- limit per department: `{args.limit_per_dept}`",
        "",
        "## Department Batches",
    ]
    for b in batches:
        lines.append(f"- `{b.department_id}` {b.department}: `{len(b.tasks)}` tasks -> `{b.task_file.name}`")
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def run_department_job(batch: DepartmentBatch, command_template: str, output_dir: Path) -> dict[str, Any]:
    command = command_template.format(
        department_id=batch.department_id,
        department=batch.department,
        task_file=str(batch.task_file),
        output_dir=str(output_dir),
    )
    started_at = dt.datetime.utcnow()
    proc = subprocess.run(
        command,
        cwd=ROOT_DIR,
        capture_output=True,
        shell=True,
        text=False,
        check=False,
    )
    finished_at = dt.datetime.utcnow()

    stdout_text = (proc.stdout or b"").decode("utf-8", errors="replace")
    stderr_text = (proc.stderr or b"").decode("utf-8", errors="replace")
    return {
        "department_id": batch.department_id,
        "department": batch.department,
        "command": command,
        "returncode": proc.returncode,
        "started_at": started_at.isoformat() + "Z",
        "finished_at": finished_at.isoformat() + "Z",
        "stdout": stdout_text[-8000:],
        "stderr": stderr_text[-8000:],
    }


def run_batches(
    batches: list[DepartmentBatch],
    command_template: str,
    output_dir: Path,
    max_workers: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_department_job, batch, command_template, output_dir): batch.department_id
            for batch in batches
        }
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda x: x["department_id"])
    return results


def write_run_results(output_dir: Path, results: list[dict[str, Any]]) -> None:
    (output_dir / "run_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    rows = [
        {
            "department_id": r["department_id"],
            "department": r["department"],
            "returncode": r["returncode"],
            "started_at": r["started_at"],
            "finished_at": r["finished_at"],
        }
        for r in results
    ]
    with (output_dir / "run_results.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["department_id", "department", "returncode", "started_at", "finished_at"],
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_utc(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def summarize_run_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {
            "total_departments": 0,
            "success_count": 0,
            "failed_count": 0,
            "elapsed_seconds": 0.0,
            "started_at": "",
            "finished_at": "",
            "failed_departments": [],
        }

    started_at = min(parse_utc(r["started_at"]) for r in results)
    finished_at = max(parse_utc(r["finished_at"]) for r in results)
    failed = [
        {
            "department_id": r["department_id"],
            "department": r["department"],
            "returncode": r["returncode"],
        }
        for r in results
        if int(r["returncode"]) != 0
    ]
    return {
        "total_departments": len(results),
        "success_count": len(results) - len(failed),
        "failed_count": len(failed),
        "elapsed_seconds": round((finished_at - started_at).total_seconds(), 3),
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "finished_at": finished_at.isoformat().replace("+00:00", "Z"),
        "failed_departments": failed,
    }


def write_completion_summary(
    output_dir: Path,
    session_label: str,
    prepare_summary: dict[str, Any],
    run_summary: dict[str, Any],
) -> None:
    lines = [
        "# Parallel Execution Completion Summary",
        "",
        f"- generated_at: `{dt.datetime.utcnow().isoformat()}Z`",
        f"- session_label: `{session_label or '-'} `",
        f"- mode: `{prepare_summary.get('mode', '-')}`",
        f"- backlog_path: `{prepare_summary.get('backlog_path', '-')}`",
        f"- filtered_task_count: `{prepare_summary.get('filtered_task_count', 0)}`",
        f"- department_count: `{prepare_summary.get('department_count', 0)}`",
        f"- started_at: `{run_summary.get('started_at', '-')}`",
        f"- finished_at: `{run_summary.get('finished_at', '-')}`",
        f"- elapsed_seconds: `{run_summary.get('elapsed_seconds', 0)}`",
        f"- success: `{run_summary.get('success_count', 0)}/{run_summary.get('total_departments', 0)}`",
        f"- failed: `{run_summary.get('failed_count', 0)}`",
        "",
        "## Failed Departments",
    ]
    failed_departments = run_summary.get("failed_departments", [])
    if failed_departments:
        for item in failed_departments:
            lines.append(
                f"- `{item.get('department_id', '-')}` {item.get('department', '-')} "
                f"(returncode={item.get('returncode', '-')})"
            )
    else:
        lines.append("- none")
    (output_dir / "COMPLETION_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_execution_history(
    history_jsonl: Path,
    history_md: Path,
    payload: dict[str, Any],
) -> None:
    history_jsonl.parent.mkdir(parents=True, exist_ok=True)
    history_md.parent.mkdir(parents=True, exist_ok=True)

    with history_jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    if not history_md.exists():
        history_md.write_text("# Parallel Execution History\n\n", encoding="utf-8")

    mode = payload.get("mode", "unknown")
    run = payload.get("run_summary") or {}
    failed = run.get("failed_count", 0)
    entry = [
        f"## {payload.get('generated_at', '-')}",
        f"- mode: `{mode}`",
        f"- session_label: `{payload.get('session_label', '-')}`",
        f"- output_dir: `{payload.get('output_dir', '-')}`",
        f"- backlog_path: `{payload.get('backlog_path', '-')}`",
        f"- filtered_task_count: `{payload.get('filtered_task_count', 0)}`",
        f"- department_count: `{payload.get('department_count', 0)}`",
    ]
    if run:
        entry.extend(
            [
                f"- elapsed_seconds: `{run.get('elapsed_seconds', 0)}`",
                f"- success: `{run.get('success_count', 0)}/{run.get('total_departments', 0)}`",
                f"- failed: `{failed}`",
            ]
        )
        failed_departments = run.get("failed_departments", [])
        if failed_departments:
            failed_ids = ", ".join([str(x.get("department_id", "-")) for x in failed_departments])
            entry.append(f"- failed_departments: `{failed_ids}`")
    entry.append("")
    with history_md.open("a", encoding="utf-8") as f:
        f.write("\n".join(entry))


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_csv(args.backlog)
    priorities = {p.strip().upper() for p in args.priorities.split(",") if p.strip()}
    filtered = filter_tasks(
        rows=rows,
        today_only=args.today_only,
        include_all=args.include_all,
        priorities=priorities,
    )
    batches = build_batches(filtered, output_dir=output_dir, limit_per_dept=args.limit_per_dept)
    write_batches(batches, output_dir=output_dir)
    prepare_summary = write_summary(output_dir, args.backlog, len(filtered), batches, args)
    run_summary: dict[str, Any] | None = None

    if args.mode == "run":
        if not args.command_template.strip():
            raise SystemExit("--mode run requires --command-template")
        results = run_batches(
            batches=batches,
            command_template=args.command_template,
            output_dir=output_dir,
            max_workers=args.max_workers,
        )
        write_run_results(output_dir, results)
        run_summary = summarize_run_results(results)
        write_completion_summary(
            output_dir=output_dir,
            session_label=args.session_label,
            prepare_summary=prepare_summary,
            run_summary=run_summary,
        )

    history_payload = {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "mode": args.mode,
        "session_label": args.session_label,
        "output_dir": str(output_dir),
        "backlog_path": str(args.backlog),
        "filtered_task_count": prepare_summary.get("filtered_task_count", 0),
        "department_count": prepare_summary.get("department_count", 0),
        "run_summary": run_summary,
    }
    append_execution_history(
        history_jsonl=args.history_jsonl,
        history_md=args.history_md,
        payload=history_payload,
    )

    print(f"Prepared {len(batches)} department batches in {output_dir}")
    if run_summary:
        print(
            "Run summary: "
            f"{run_summary['success_count']}/{run_summary['total_departments']} succeeded, "
            f"{run_summary['failed_count']} failed"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
