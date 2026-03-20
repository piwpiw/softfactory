#!/usr/bin/env python3
"""Classify dirty git worktree entries into actionable buckets."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path


CODE_PREFIXES = (
    "api/",
    "backend/",
    "migrations/",
    "n8n/",
    "scripts/",
    "tests/",
    "web/",
    "wordpress/",
)

DOC_PREFIXES = (
    "docs/",
    "memory/",
    "shared-intelligence/",
)

ROOT_SCRIPT_NAMES = (
    "DEPLOYMENT_EXECUTION_SCRIPT.sh",
    "continuous_improvement.sh",
    "deploy-verify.sh",
    "open_all_pages.bat",
    "verify_m002_phase4_setup.bat",
    "verify_m002_phase4_setup.sh",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def parse_status(root: Path) -> list[dict[str, str]]:
    result = run_git(root, "status", "--porcelain")
    entries: list[dict[str, str]] = []
    for raw_line in result.stdout.splitlines():
        if not raw_line:
            continue
        index_status = raw_line[0]
        worktree_status = raw_line[1]
        payload = raw_line[3:]
        path = payload.split(" -> ", 1)[-1].strip()
        entries.append(
            {
                "raw": raw_line,
                "path": path.replace("\\", "/"),
                "index": index_status,
                "worktree": worktree_status,
            }
        )
    return entries


def parse_diff_check(root: Path) -> dict[str, list[str]]:
    result = run_git(root, "diff", "--check")
    issues: dict[str, list[str]] = defaultdict(list)
    pattern = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+): (?P<message>.+)$")
    for line in result.stdout.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        path = match.group("path").replace("\\", "/")
        message = f"line {match.group('line')}: {match.group('message').strip()}"
        issues[path].append(message)
    return dict(issues)


def top_level(path: str) -> str:
    normalized = path.replace("\\", "/")
    if "/" not in normalized:
        return "<root>"
    return normalized.split("/", 1)[0]


def is_code_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith(CODE_PREFIXES)


def is_doc_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith(DOC_PREFIXES) or normalized in {"README.md", "STATUS.md"}


def build_report(root: Path) -> dict[str, object]:
    status_entries = parse_status(root)
    diff_check = parse_diff_check(root)
    tracked_deletions = []
    modified_code_paths = []
    untracked_feature_paths = []
    modified_docs_and_meta = []
    modified_root_configs = []

    for entry in status_entries:
        path = entry["path"]
        index_status = entry["index"]
        worktree_status = entry["worktree"]
        is_untracked = index_status == "?" and worktree_status == "?"
        is_deleted = index_status == "D" or worktree_status == "D"
        is_modified = any(flag == "M" for flag in (index_status, worktree_status))

        if is_deleted:
            tracked_deletions.append(path)

        if is_untracked and is_code_path(path):
            untracked_feature_paths.append(path)
            continue

        if is_modified and is_code_path(path):
            modified_code_paths.append(path)
            continue

        if (is_modified or is_untracked) and is_doc_path(path):
            modified_docs_and_meta.append(path)
            continue

        if top_level(path) == "<root>" and (is_modified or is_untracked):
            modified_root_configs.append(path)

    root_script_duplicates = []
    for name in ROOT_SCRIPT_NAMES:
        if (root / name).is_file() and (root / "scripts" / name).is_file():
            root_script_duplicates.append(name)

    top_level_counts: dict[str, int] = defaultdict(int)
    for entry in status_entries:
        top_level_counts[top_level(entry["path"])] += 1

    report = {
        "total_dirty_entries": len(status_entries),
        "tracked_deletions": sorted(tracked_deletions),
        "formatting_issue_paths": sorted(diff_check.keys()),
        "formatting_issue_count": len(diff_check),
        "modified_code_paths": sorted(modified_code_paths),
        "untracked_feature_paths": sorted(untracked_feature_paths),
        "modified_docs_and_meta": sorted(modified_docs_and_meta),
        "modified_root_configs": sorted(modified_root_configs),
        "root_script_duplicates": root_script_duplicates,
        "top_level_counts": dict(sorted(top_level_counts.items())),
    }
    return report


def preview(items: list[str], limit: int = 8) -> str:
    if not items:
        return "-"
    shown = items[:limit]
    suffix = "" if len(items) <= limit else f" ... (+{len(items) - limit} more)"
    return ", ".join(shown) + suffix


def print_report(report: dict[str, object]) -> None:
    print("Dirty Worktree Classification")
    print(f"- total dirty entries: {report['total_dirty_entries']}")
    print(f"- formatting issue paths: {report['formatting_issue_count']}")
    print(f"- tracked deletions needing review: {len(report['tracked_deletions'])}")
    print(f"- modified code paths: {len(report['modified_code_paths'])}")
    print(f"- untracked feature paths: {len(report['untracked_feature_paths'])}")
    print(f"- modified docs/meta paths: {len(report['modified_docs_and_meta'])}")
    print(f"- modified root configs/scripts: {len(report['modified_root_configs'])}")
    print(f"- root/script duplicates: {len(report['root_script_duplicates'])}")
    print("")
    print("Formatting Preview")
    print(f"  {preview(report['formatting_issue_paths'])}")
    print("Deletion Review Preview")
    print(f"  {preview(report['tracked_deletions'])}")
    print("Modified Code Preview")
    print(f"  {preview(report['modified_code_paths'])}")
    print("Untracked Feature Preview")
    print(f"  {preview(report['untracked_feature_paths'])}")
    print("Root Duplication Preview")
    print(f"  {preview(report['root_script_duplicates'])}")
    print("Top-level Counts")
    for key, value in report["top_level_counts"].items():
        print(f"  - {key}: {value}")


def main() -> int:
    args = parse_args()
    report = build_report(args.root.resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
