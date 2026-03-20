import json
import os
import multiprocessing
import subprocess
import csv
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_HOURS = float(os.environ.get("SOFTFACTORY_LOOP_HOURS", "5"))
RUN_INTERVAL_SECONDS = int(os.environ.get("SOFTFACTORY_LOOP_INTERVAL_SECONDS", "300"))
DEFAULT_PARALLEL = max((os.cpu_count() or 2) * 2, 12)
MAX_WORKERS = int(os.environ.get("SOFTFACTORY_LOOP_MAX_WORKERS", str(DEFAULT_PARALLEL)))
RUN_MODE = os.environ.get("SOFTFACTORY_LOOP_MODE", "review").strip().lower()
COMMAND_TEMPLATE = os.environ.get("SOFTFACTORY_LOOP_COMMAND_TEMPLATE", "").strip()
RETRY_FAILED_DEPARTMENTS = os.environ.get("SOFTFACTORY_LOOP_RETRY_FAILED", "1").strip().lower() not in {"0", "false", "no", "off"}
RETRY_MAX_ATTEMPTS = int(os.environ.get("SOFTFACTORY_LOOP_RETRY_MAX_ATTEMPTS", "1"))

if RUN_MODE == "review":
    DEFAULT_COMMAND_TEMPLATE = (
        'python scripts/department_review_list_worker.py '
        '--department-id "{department_id}" '
        '--department "{department}" '
        '--task-file "{task_file}" '
        '--output-dir "{output_dir}"'
    )
else:
    DEFAULT_COMMAND_TEMPLATE = (
        'python scripts/department_queue_worker.py '
        '--department-id "{department_id}" '
        '--department "{department}" '
        '--task-file "{task_file}" '
        '--output-dir "{output_dir}"'
    )

if not COMMAND_TEMPLATE:
    COMMAND_TEMPLATE = DEFAULT_COMMAND_TEMPLATE


OUT_DIR = ROOT / "docs" / "plans" / "execution" / datetime.now().strftime("%Y-%m-%d") / "auto-5h"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = OUT_DIR / "agent_5h_loop.log"
STATUS_FILE = OUT_DIR / "status.json"
STATUS_MD = OUT_DIR / "status.md"
MANIFEST_FILE = OUT_DIR / "cycle_manifest.jsonl"
HOUR_REPORT_MD = OUT_DIR / "hourly_report.md"
HOUR_REPORT_JSON = OUT_DIR / "hourly_report.json"
MORNING_BRIEF_MD = OUT_DIR / "morning_check_brief.md"
MORNING_BRIEF_JSON = OUT_DIR / "morning_check_brief.json"

BASE_CMD = [
    "python",
    "scripts/enterprise_parallel_runner.py",
    "--mode",
    "run",
    "--include-all",
    "--priorities",
    "P0,P1,P2,P3,P4",
    "--limit-per-dept",
    "100",
    "--max-workers",
    str(MAX_WORKERS),
    "--command-template",
    COMMAND_TEMPLATE,
]


def _safe_json_load(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_status(running: bool, completed: int, planned: int, last_code: int | None = None, note: str = "") -> None:
    status = {
        "started_at": str(start_time),
        "running": running,
        "iterations_completed": completed,
        "iterations_planned": planned,
        "last_return_code": last_code,
        "last_updated": datetime.now().isoformat(),
        "run_hours": RUN_HOURS,
        "interval_seconds": RUN_INTERVAL_SECONDS,
        "max_workers": MAX_WORKERS,
        "run_mode": RUN_MODE,
        "command_template": COMMAND_TEMPLATE,
        "output_dir": str(OUT_DIR),
        "log_file": str(LOG_FILE),
        "note": note,
    }
    STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

    planned = max(planned, 1)
    lines = [
        "# 5h Autonomy Status (Review-List First)",
        "",
        f"- started_at: {start_time:%Y-%m-%d %H:%M:%S}",
        f"- running: {'RUNNING' if running else 'DONE'}",
        f"- progress: {completed}/{planned} ({completed / planned * 100:.1f}%)",
        f"- last_return_code: {last_code if last_code is not None else 'none'}",
        f"- mode: {RUN_MODE}",
        f"- note: {note or 'none'}",
        "",
        f"- log: `{LOG_FILE}`",
        f"- hourly_report: `{HOUR_REPORT_MD}`",
        f"- morning_brief: `{MORNING_BRIEF_MD}`",
        "",
    ]
    STATUS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_csv_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
            return len(rows)
    except Exception:
        return 0


def validate_cycle_outputs(ts: datetime, iteration: int, cycle_dir: Path, return_code: int) -> dict[str, Any]:
    summary = _safe_json_load(cycle_dir / "summary.json", {})
    departments = summary.get("departments", []) if isinstance(summary, dict) else []
    if not isinstance(departments, list):
        departments = []

    issues: list[str] = []
    expected_departments = 0
    expected_tasks = 0
    reviewed_departments = 0
    for item in departments:
        if not isinstance(item, dict):
            continue
        dept_id = item.get("department_id", "").strip()
        task_file = Path(item.get("task_file", "")).resolve()
        if not dept_id:
            continue
        expected_departments += 1
        expected = int(item.get("task_count", 0) or 0)
        expected_tasks += expected
        actual = _read_csv_count(task_file)
        if actual != expected:
            issues.append(f"{dept_id}: task_file_count_mismatch(expected={expected}, actual={actual})")

        out_json = cycle_dir / f"{dept_id}_review_list.json"
        out_md = cycle_dir / f"{dept_id}_review_list.md"
        payload = _safe_json_load(out_json, {})
        if not payload:
            issues.append(f"{dept_id}: missing review_list_json")
        else:
            items = payload.get("items", [])
            if isinstance(items, list) and len(items) != expected:
                issues.append(f"{dept_id}: review_items_mismatch(expected={expected}, actual={len(items)})")
        if not out_md.exists():
            issues.append(f"{dept_id}: missing review_list_md")
        if out_json.exists() or out_md.exists():
            reviewed_departments += 1

    run_results = _safe_json_load(cycle_dir / "run_results.json", [])
    if not isinstance(run_results, list):
        issues.append("run_results.json invalid or missing")
        run_results = []
    failed_depts = [r for r in run_results if int(r.get("returncode", 0) or 0) != 0] if isinstance(run_results, list) else []

    return {
        "iteration": iteration,
        "timestamp": ts.isoformat(),
        "hour": ts.strftime("%Y-%m-%d %H"),
        "cycle_dir": str(cycle_dir.name),
        "run_mode": RUN_MODE,
        "runner_return_code": return_code,
        "departments": len(departments),
        "departments_with_tasks_file": expected_departments,
        "tasks_expected": expected_tasks,
        "departments_review_outputs": reviewed_departments,
        "failed_departments_in_runner": len(failed_depts),
        "issues": issues,
        "status": "ok" if not issues and return_code == 0 and len(failed_depts) == 0 else "failed",
        "departments_detail": [
            {
                "department_id": item.get("department_id", ""),
                "department": item.get("department", ""),
                "task_count": int(item.get("task_count", 0) or 0),
            }
            for item in departments
            if isinstance(item, dict)
        ],
    }


def load_run_results(cycle_dir: Path) -> list[dict[str, Any]]:
    return _safe_json_load(cycle_dir / "run_results.json", [])


def merge_retry_results(results: list[dict[str, Any]], retries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(results, list):
        return retries
    by_dept = {r.get("department_id"): r for r in results if isinstance(r, dict)}
    for r in retries:
        if not isinstance(r, dict):
            continue
        dept_id = r.get("department_id")
        if not dept_id:
            continue
        by_dept[dept_id] = r
    return sorted(by_dept.values(), key=lambda item: item.get("department_id", ""))


def run_department_command(command: str, timeout_sec: int = 120) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            command, cwd=str(ROOT), capture_output=True, text=True, shell=True, check=False, timeout=timeout_sec
        )
        return proc.returncode, (proc.stdout or "")[-8000:], (proc.stderr or "")[-8000:]
    except Exception as exc:
        return 1, "", f"{exc}"


def retry_failed_departments(cycle_dir: Path, failed_codes: list[dict[str, Any]]) -> dict[str, Any]:
    if not failed_codes or not RETRY_FAILED_DEPARTMENTS:
        return {"retried": 0, "remaining_failed": len(failed_codes), "retried_run_results": []}

    attempts = 0
    retried: list[dict[str, Any]] = []
    still_failed: list[str] = []

    for failed in failed_codes:
        dept_id = failed.get("department_id")
        command = failed.get("command", "")
        if not dept_id or not command:
            still_failed.append(dept_id or "unknown")
            continue

        last_rc = int(failed.get("returncode", 0) or 0)
        for attempt_index in range(1, max(RETRY_MAX_ATTEMPTS, 0) + 1):
            attempts += 1
            if last_rc == 0:
                break
            start_at = datetime.utcnow().isoformat() + "Z"
            rc, out, err = run_department_command(command)
            finished_at = datetime.utcnow().isoformat() + "Z"
            last_rc = rc
            retried.append(
                {
                    "department_id": dept_id,
                    "department": failed.get("department", ""),
                    "command": command,
                    "returncode": rc,
                    "started_at": start_at,
                    "finished_at": finished_at,
                    "stdout": out,
                    "stderr": err,
                    "retry": True,
                    "retry_attempt": attempt_index,
                }
            )

        if last_rc != 0:
            still_failed.append(dept_id)

    if retried:
        run_results = load_run_results(cycle_dir)
        merged = merge_retry_results(run_results, retried)
        (cycle_dir / "run_results.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

        rows = [
            {
                "department_id": r["department_id"],
                "department": r["department"],
                "returncode": r["returncode"],
                "started_at": r["started_at"],
                "finished_at": r["finished_at"],
            }
            for r in merged
            if isinstance(r, dict)
        ]
        with (cycle_dir / "run_results.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["department_id", "department", "returncode", "started_at", "finished_at"],
            )
            writer.writeheader()
            writer.writerows(rows)

    return {
        "retried": len(retried),
        "remaining_failed": len(still_failed),
        "retried_run_results": retried,
    }


def collect_cycle_snapshot(ts: datetime, iteration: int, cycle_dir: Path, return_code: int) -> dict[str, Any]:
    summary = _safe_json_load(cycle_dir / "summary.json", {})
    departments = summary.get("departments", []) if isinstance(summary, dict) else []
    if not isinstance(departments, list):
        departments = []

    dept_count = 0
    task_count = 0
    dept_lines: list[dict[str, Any]] = []
    for item in departments:
        if not isinstance(item, dict):
            continue
        dept_count += 1
        c = int(item.get("task_count", 0) or 0)
        task_count += c
        dept_lines.append(
            {
                "department_id": item.get("department_id", ""),
                "department": item.get("department", ""),
                "task_count": c,
            }
        )

    dept_lines.sort(key=lambda x: (x["department_id"], x["department"]))
    run_results = _safe_json_load(cycle_dir / "run_results.json", [])
    if not isinstance(run_results, list):
        run_results = []
    failed_depts = [r for r in run_results if int(r.get("returncode", 0) or 0) != 0] if isinstance(run_results, list) else []
    retry_summary = retry_failed_departments(cycle_dir, failed_depts)
    if retry_summary["remaining_failed"] == 0 and failed_depts:
        validation = validate_cycle_outputs(ts, iteration, cycle_dir, return_code)
    else:
        validation = validate_cycle_outputs(ts, iteration, cycle_dir, return_code)

    return {
        "iteration": iteration,
        "timestamp": ts.isoformat(),
        "hour": ts.strftime("%Y-%m-%d %H"),
        "cycle_dir": str(cycle_dir.name),
        "run_mode": RUN_MODE,
        "return_code": return_code,
        "departments": dept_count,
        "tasks": task_count,
        "departments_detail": dept_lines,
        "validation_status": validation.get("status"),
        "validation_issues": validation.get("issues", []),
        "failed_departments_in_runner": validation.get("failed_departments_in_runner", 0),
        "departments_review_outputs": validation.get("departments_review_outputs", 0),
        "retry_summary": retry_summary,
    }


def append_cycle_manifest(record: dict[str, Any]) -> None:
    with MANIFEST_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def rebuild_hourly_report() -> None:
    if not MANIFEST_FILE.exists():
        return

    rows: list[dict[str, Any]] = []
    for line in MANIFEST_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            rows.append(row)

    rows.sort(key=lambda x: x.get("timestamp", ""))
    if not rows:
        return

    by_hour: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        hour = row.get("hour", "unknown")
        by_hour.setdefault(hour, []).append(row)

    report_rows: list[dict[str, Any]] = []
    for hour in sorted(by_hour.keys()):
        records = by_hour[hour]
        total_cycles = len(records)
        total_departments = sum(int(r.get("departments", 0) or 0) for r in records)
        total_tasks = sum(int(r.get("tasks", 0) or 0) for r in records)

        dept_counter: dict[str, int] = {}
        for r in records:
            for item in r.get("departments_detail", []) or []:
                if not isinstance(item, dict):
                    continue
                key = f"{item.get('department_id', '')} {item.get('department', '')}".strip()
                if not key:
                    continue
                dept_counter[key] = dept_counter.get(key, 0) + int(item.get("task_count", 0) or 0)

        top_depts = sorted(dept_counter.items(), key=lambda kv: kv[1], reverse=True)[:5]

        first_ts = records[0].get("timestamp")
        last_ts = records[-1].get("timestamp")
        report_rows.append(
            {
                "hour": hour,
                "first_timestamp": first_ts,
                "last_timestamp": last_ts,
                "cycles": total_cycles,
                "cycles_ok": sum(1 for r in records if r.get("validation_status", "ok") == "ok"),
                "cycles_failed": sum(
                    1
                    for r in records
                    if r.get("validation_status", "ok") != "ok" or int(r.get("runner_return_code", 0) or 0) != 0
                ),
                "departments": total_departments,
                "tasks": total_tasks,
                "validation_issues": sum(len(r.get("validation_issues", []) or []) for r in records),
                "top_departments": [{"department": k, "tasks": v} for k, v in top_depts],
            }
        )

    HOUR_REPORT_JSON.write_text(
        json.dumps(
            {"generated_at": datetime.now().isoformat(), "items": report_rows},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    total_failed = sum(
        1
        for r in rows
        if r.get("validation_status", "ok") != "ok" or int(r.get("runner_return_code", 0) or 0) != 0
    )
    latest_row = report_rows[-1] if report_rows else {}
    top_departments = latest_row.get("top_departments", [])
    top_departments_text = ", ".join(
        [f"{x['department']}:{x['tasks']}" for x in top_departments[:3]] if top_departments else ["(none)"]
    )

    md_lines = [
        "# Hourly Upgrade Report",
        "",
        f"- generated_at: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"- total_cycles: {len(rows)}",
        f"- total_failed_cycles: {total_failed}",
        f"- total_validation_issues: {sum(len(r.get('validation_issues', []) or []) for r in rows)}",
        "",
        f"## Latest hour ({latest_row.get('hour', '-')})",
        f"- cycles: {latest_row.get('cycles', 0)}",
        f"- cycles_ok: {latest_row.get('cycles_ok', 0)}",
        f"- cycles_failed: {latest_row.get('cycles_failed', 0)}",
        f"- departments_processed: {latest_row.get('departments', 0)}",
        f"- tasks_processed: {latest_row.get('tasks', 0)}",
        f"- window: {latest_row.get('first_timestamp', '-') } ~ {latest_row.get('last_timestamp', '-')}",
        f"- validation_issues: {latest_row.get('validation_issues', 0)}",
        f"- top_departments: {top_departments_text}",
        "",
    ]

    for row in report_rows:
        md_lines.append(f"## {row['hour']}:00")
        md_lines.append(f"- cycles: {row['cycles']}")
        md_lines.append(f"- cycles_ok: {row.get('cycles_ok', 0)}")
        md_lines.append(f"- cycles_failed: {row.get('cycles_failed', 0)}")
        md_lines.append(f"- departments_processed: {row['departments']}")
        md_lines.append(f"- tasks_processed: {row['tasks']}")
        md_lines.append(f"- validation_issues: {row.get('validation_issues', 0)}")
        md_lines.append(f"- window: {row['first_timestamp']} ~ {row['last_timestamp']}")
        if row["top_departments"]:
            top_items = [f"{x['department']}:{x['tasks']}" for x in row["top_departments"]]
            top_line = ", ".join(top_items)
        else:
            top_line = "none"
        md_lines.append(f"- top 5 departments: {top_line}")
        md_lines.append("")

    HOUR_REPORT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    morning_payload = {
        "generated_at": datetime.now().isoformat(),
        "latest_hour": latest_row,
        "total_cycles": len(rows),
        "failed_cycles": total_failed,
        "latest_cycle_return_codes": [r.get("return_code") for r in rows[:3]],
        "status_summary": "review-only",
        "top_departments_latest_hour": top_departments,
    }
    MORNING_BRIEF_JSON.write_text(json.dumps(morning_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MORNING_BRIEF_MD.write_text(
        "\n".join(
            [
                "# Morning Check Brief",
                "",
                f"- Last hour: {latest_row.get('hour', '-')}",
                f"- Tasks this hour: {latest_row.get('tasks', 0)}",
                f"- Cycles this hour: {latest_row.get('cycles', 0)}",
                f"- Departments touched: {latest_row.get('departments', 0)}",
                f"- Run mode: {RUN_MODE}",
                f"- Failed cycles (total): {total_failed}",
                f"- Top departments: {top_departments_text}",
                "- Action today: review lists were auto-generated per department for implementation planning.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


start_time = datetime.now()
end_time = start_time + timedelta(hours=RUN_HOURS)
iteration = 0
planned_cycles = max(1, int((end_time - start_time).total_seconds() // max(RUN_INTERVAL_SECONDS, 1)) + 1)
last_code: int | None = None

with LOG_FILE.open("a", encoding="utf-8") as f:
    f.write(
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] LOOP_START hours={RUN_HOURS} interval={RUN_INTERVAL_SECONDS}s workers={MAX_WORKERS}\n"
    )
    f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] OUTPUT_DIR={OUT_DIR}\n")

write_status(True, 0, planned_cycles, None, "started")

while datetime.now() < end_time:
    iteration += 1
    ts = datetime.now()
    cycle_dir = OUT_DIR / f"cycle_{ts.strftime('%Y%m%d_%H%M%S')}"
    cycle_dir.mkdir(parents=True, exist_ok=True)

    cmd = BASE_CMD + ["--output-dir", str(cycle_dir)]

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts:%Y-%m-%d %H:%M:%S}] ITERATION_START index={iteration}\n")
        f.write(f"[{ts:%Y-%m-%d %H:%M:%S}] ITERATION_DIR={cycle_dir}\n")

    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    last_code = result.returncode

    with LOG_FILE.open("a", encoding="utf-8") as f:
        if result.stdout:
            f.write((result.stdout).strip() + "\n")
        if result.stderr:
            f.write((result.stderr).strip() + "\n")
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ITERATION_DONE index={iteration} RETURN_CODE={result.returncode}\n")

    cycle_snapshot = collect_cycle_snapshot(ts, iteration, cycle_dir, result.returncode)
    append_cycle_manifest(cycle_snapshot)
    rebuild_hourly_report()

    retry_summary = cycle_snapshot.get("retry_summary", {})
    if not isinstance(retry_summary, dict):
        retry_summary = {}
    retried = int(retry_summary.get("retried", 0) or 0)
    remaining_failed = int(retry_summary.get("remaining_failed", 0) or 0)
    note = "OK" if (result.returncode == 0 and remaining_failed == 0) else f"FAIL rc={result.returncode}"
    if retried > 0:
        note = f"{note} | retried={retried} remaining={remaining_failed}"
    write_status(True, iteration, planned_cycles, last_code, note)

    if result.returncode != 0:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] WARN: iteration {iteration} failed, continuing...\n")

    remain_sec = int((end_time - datetime.now()).total_seconds())
    if remain_sec <= 0:
        break
    sleep_sec = min(RUN_INTERVAL_SECONDS, remain_sec)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] SLEEP={sleep_sec}s\n")
    time.sleep(sleep_sec)

with LOG_FILE.open("a", encoding="utf-8") as f:
    f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] LOOP_END iterations={iteration}\n")
write_status(False, iteration, planned_cycles, last_code, "complete")
