#!/usr/bin/env python3
"""Generate and persist review-focused task lists for one department.

Each cycle creates:
- <department>_review_list.md
- <department>_review_list.json
- aggregate updates in review_worklist_aggregate.md/json under output root
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import os
import time
from contextlib import contextmanager
import uuid

WORKSTREAM_GUIDE = {
    "Requirements Traceability": "요구사항↔코드↔테스트 간 추적성을 보장하고 근거를 남김",
    "Page Function Audit": "페이지 기능 누락/동작 불일치 포인트를 정리하고 우선순위별 수정안을 제시",
    "API Contract Audit": "API 요청/응답 계약, 상태 코드, 에러 스키마의 일치 여부를 검증",
    "Data Integrity": "데이터 스키마/검증 규칙/예외 케이스를 정리하고 정합성 기준을 제시",
    "Test Automation": "핵심 시나리오를 재현 가능한 테스트 케이스로 분해",
    "Performance and SLO": "성능 임계치, 리소스 사용량 가드레일, 모니터링 포인트를 제시",
    "Security Hardening": "공격면 점검, 인증/권한/입력 검증 리스크를 체크",
    "CI/CD Automation": "파이프라인 게이트와 롤백·승인 조건을 정리",
    "Runbook and Incident": "장애 대응 절차와 책임 경계를 가시화",
    "Metrics and Reporting": "운영 지표 및 보고 산출물 포맷을 표준화",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate review task list for one department")
    parser.add_argument("--department-id", required=True)
    parser.add_argument("--department", default="")
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def read_tasks(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def summarize(tasks: list[dict[str, str]]) -> dict:
    p = Counter()
    w = Counter()
    s = Counter()
    for t in tasks:
        p[t.get("priority", "Unknown")] += 1
        w[t.get("workstream", "Unknown")] += 1
        s[t.get("service_name", "Unknown")] += 1
    return {
        "total_tasks": len(tasks),
        "by_priority": dict(p),
        "by_workstream": dict(w),
        "by_service": dict(s),
    }


def _scan_json_chunks(text: str) -> list[object]:
    chunks: list[object] = []
    idx = 0
    n = len(text)
    while idx < n:
        while idx < n and text[idx].isspace():
            idx += 1
        if idx >= n:
            break

        if text[idx] not in "{[":
            idx += 1
            continue

        start = idx
        in_string = False
        escape = False
        depth = 0
        quote_char = ""

        while idx < n:
            c = text[idx]
            if in_string:
                if escape:
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == quote_char:
                    in_string = False
                idx += 1
                continue

            if c == '"':
                in_string = True
                quote_char = c
            elif c in "{[":
                if depth == 0:
                    start = idx
                depth += 1
            elif c in "}]" :
                depth -= 1
                if depth == 0:
                    idx += 1
                    break
            idx += 1

        if depth != 0:
            break

        chunk = text[start:idx].strip()
        if chunk:
            try:
                chunks.append(json.loads(chunk))
            except Exception:
                pass
    return chunks


def _coerce_records(value: object) -> list[dict[str, str]]:
    if isinstance(value, list):
        return [r for r in value if isinstance(r, dict)]

    if isinstance(value, dict):
        if "items" in value and isinstance(value.get("items"), list):
            return [r for r in value.get("items", []) if isinstance(r, dict)]
        return [value]

    return []


def _read_aggregate_records(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        loaded = json.loads(text)
        return _coerce_records(loaded)
    except Exception:
        try:
            chunks = _scan_json_chunks(text)
            records = []
            for chunk in chunks:
                records.extend(_coerce_records(chunk))
            if records:
                backup = path.with_suffix(f".json.corrupt.{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.bak")
                path.replace(backup)
                return records
        except Exception:
            pass

        return []

    return []


def _dedupe_records(
    records: list[dict[str, str]],
    department: str,
    dept_id: str,
    tasks: list[dict[str, str]],
    now: str,
) -> list[dict]:
    normalized = {f"{r.get('department_id')},{r.get('task_id')}": r for r in records if r.get("department_id") and r.get("task_id")}

    for task in tasks:
        task_id = task.get("task_id", "").strip()
        if not task_id:
            continue
        key = f"{dept_id},{task_id}"
        normalized[key] = {
            "department_id": dept_id,
            "department": department,
            "task_id": task_id,
            "title": task.get("title", ""),
            "priority": task.get("priority", ""),
            "workstream": task.get("workstream", ""),
            "service_name": task.get("service_name", ""),
            "target": task.get("target", ""),
            "reviewed_at": now,
            "status": "requested",
        }

    return list(normalized.values())


@contextmanager
def _file_lock(lock_path: Path, timeout_seconds: int = 20, poll_interval: float = 0.05):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    token = str(uuid.uuid4())
    end_at = time.time() + timeout_seconds

    while True:
        try:
            with lock_path.open("x", encoding="utf-8") as fp:
                fp.write(token)
            break
        except FileExistsError:
            try:
                if time.time() > end_at or (time.time() - lock_path.stat().st_mtime) > timeout_seconds:
                    lock_path.unlink()
                    continue
            except Exception:
                pass
            time.sleep(poll_interval)

    try:
        yield
    finally:
        try:
            if lock_path.exists() and lock_path.read_text(encoding="utf-8").strip() == token:
                lock_path.unlink()
        except Exception:
            pass


def make_review_action(task: dict[str, str]) -> str:
    ws = task.get("workstream", "")
    title = task.get("title", "")
    base = WORKSTREAM_GUIDE.get(ws, "요청 조건을 바탕으로 구현 전 검토 항목을 확정")
    if "개발" in title or "API" in title:
        return f"{base}. 구현 착수 전 요구명세, 예외처리, 동기화 포인트를 검토하고 개발 브랜치별 작업 카드를 작성."
    if "UI" in title or "페이지" in task.get("target", ""):
        return f"{base}. 화면 동작/접근성/반응형까지 검토 항목으로 분해해 우선순위 1개씩 배치."
    return f"{base}. 완료 기준(Definition of Done)과 rollback 조건까지 정의 후 스프린트에 반영."


def render_markdown(department: str, dept_id: str, tasks: list[dict[str, str]], summary: dict, iteration: int, now: str) -> str:
    lines = [
        f"# {department}({dept_id}) 검토 작업리스트",
        "",
        f"- 생성 시각: {now}",
        f"- 사이클: {iteration}",
        "",
        f"- 총 항목: `{summary['total_tasks']}`",
        "",
        "## 우선순위",
    ]
    for k, v in summary["by_priority"].items():
        lines.append(f"- {k}: {v}")

    lines.extend(["", "## 작업 항목", ""])
    for task in tasks:
        task_id = task.get("task_id", "-")
        p = task.get("priority", "P?")
        title = task.get("title", "(untitled)")
        service = task.get("service_name", "")
        target = task.get("target", "")
        criteria = task.get("acceptance_criteria", "")
        ws = task.get("workstream", "")
        src = task.get("source_ref1", "")
        action = make_review_action(task)

        lines.append(f"- [ ] **{task_id}** `{p}` {service} / {ws}")
        lines.append(f"  - 제목: {title}")
        if target:
            lines.append(f"  - 대상: `{target}`")
        if criteria:
            lines.append(f"  - 수락 기준: {criteria}")
        if src:
            lines.append(f"  - 근거 문서: {src}")
        lines.append(f"  - 개발 제안: {action}")
        lines.append("")

    return "\n".join(lines)


def append_aggregate(root: Path, department: str, dept_id: str, now: str, tasks: list[dict[str, str]]) -> None:
    aggregate_json = root / "review_worklist_aggregate.json"
    aggregate_md = root / "review_worklist_aggregate.md"
    lock_file = root / "review_worklist_aggregate.lock"

    with _file_lock(lock_file):
        existing = _read_aggregate_records(aggregate_json)
        updated = _dedupe_records(existing, department, dept_id, tasks, now)
        tmp_json = aggregate_json.with_suffix(".json.tmp")
        tmp_json.write_text(
            json.dumps({"items": updated}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(str(tmp_json), str(aggregate_json))

    by_dept = defaultdict(int)
    by_ws = Counter()
    by_pri = Counter()
    for rec in updated:
        by_dept[f'{rec.get("department_id")}:{rec.get("department") }'] += 1
        by_ws[rec.get("workstream", "Unknown")] += 1
        by_pri[rec.get("priority", "Unknown")] += 1

    md = [
        "# 검토 작업리스트 누적",
        "",
        f"- 누적 항목: `{len(updated)}`",
        f"- 갱신 시각: {now}",
        "",
        "## 부서별",
    ]
    for key in sorted(by_dept):
        md.append(f"- {key}: {by_dept[key]}")
    md.extend(["", "## 우선순위", ""]) 
    for p in sorted(by_pri):
        md.append(f"- {p}: {by_pri[p]}")
    md.extend(["", "## 워크스트림", ""])
    for ws in sorted(by_ws):
        md.append(f"- {ws}: {by_ws[ws]}")

    aggregate_md.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    task_file = Path(args.task_file)
    output_dir = Path(args.output_dir)

    department = args.department or args.department_id
    tasks = read_tasks(task_file)
    summary = summarize(tasks)

    now = datetime.utcnow().isoformat() + "Z"
    iteration = int(datetime.utcnow().timestamp())

    out_json = output_dir / f"{args.department_id}_review_list.json"
    out_md = output_dir / f"{args.department_id}_review_list.md"

    payload = {
        "executed_at": now,
        "department_id": args.department_id,
        "department": department,
        "task_file": str(task_file),
        "iteration": iteration,
        "summary": summary,
        "items": tasks,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(department, args.department_id, tasks, summary, iteration, now), encoding="utf-8")

    append_aggregate(output_dir.parent, department, args.department_id, now, tasks)

    print(
        f"[{args.department_id}] review_list tasks={len(tasks)} "
        f"json={out_json.name}, md={out_md.name}, aggregate_review_worklist"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
