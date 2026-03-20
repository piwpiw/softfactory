"""Repository layout audit for report-only or strict validation runs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from repo_layout_policy import (
    DEPRECATED_PATHS,
    FIXED_PATHS,
    LINK_CHECK_FILES,
    ROOT_ALLOWED_DIRS,
    ROOT_ALLOWED_FILES,
    TEMP_ROOT_PREFIXES,
    TEMP_ROOT_SUFFIXES,
)

LINK_RE = re.compile(r"(?<!\!)\[[^\]]+\]\(([^)]+)\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def git_tracked_root_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []

    tracked = []
    for line in result.stdout.splitlines():
        normalized = line.strip().replace("\\", "/")
        if normalized and "/" not in normalized:
            tracked.append(normalized)
    return sorted(tracked)


def root_files_present(root: Path) -> list[str]:
    present = []
    for entry in root.iterdir():
        if entry.is_file():
            present.append(entry.name)
    return sorted(present)


def load_reclassification_manifest(root: Path) -> dict[str, object]:
    manifest_path = root / "docs" / "reference" / "root-reclassification-manifest-wave-a.json"
    if not manifest_path.is_file():
        return {}

    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def local_links(path: Path, root: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    problems: list[dict[str, str]] = []

    for match in LINK_RE.finditer(text):
        raw_target = match.group(1).strip()
        if not raw_target or raw_target.startswith("#"):
            continue
        if raw_target.startswith(("http://", "https://", "mailto:", "javascript:")):
            continue

        target = raw_target.split()[0].strip("<>").split("#", 1)[0]
        if not target:
            continue

        candidate = (path.parent / target).resolve()
        if not candidate.exists():
            problems.append(
                {
                    "source": path.relative_to(root).as_posix(),
                    "target": raw_target,
                }
            )
    return problems


def build_report(root: Path) -> dict[str, object]:
    root_files = root_files_present(root)
    tracked_root = git_tracked_root_files(root)
    disallowed_root = [name for name in root_files if name not in ROOT_ALLOWED_FILES]
    disallowed_tracked_root = [
        name for name in tracked_root if name not in ROOT_ALLOWED_FILES
    ]
    tracked_root_missing_from_worktree = [
        name for name in tracked_root if name not in root_files
    ]

    temp_root_files = []
    for entry in root.iterdir():
        if not entry.is_file():
            continue
        if entry.name.startswith(TEMP_ROOT_PREFIXES) or entry.suffix in TEMP_ROOT_SUFFIXES:
            temp_root_files.append(entry.name)

    missing_link_targets = []
    for rel_path in LINK_CHECK_FILES:
        path = root / rel_path
        if path.exists():
            missing_link_targets.extend(local_links(path, root))

    missing_allowed_dirs = [
        name for name in sorted(ROOT_ALLOWED_DIRS) if not (root / name).exists()
    ]
    missing_fixed_paths = [
        path for path in FIXED_PATHS if not (root / path.rstrip("/")).exists()
    ]
    deprecated_present = [
        path for path in DEPRECATED_PATHS if (root / path).exists()
    ]
    reclassification_manifest = load_reclassification_manifest(root)
    legacy_root_documents_present: list[str] = []
    if reclassification_manifest:
        for entry in reclassification_manifest.get("entries", []):
            source_path = str(entry.get("source_path", "")).strip()
            if (
                source_path
                and "/" not in source_path
                and source_path not in ROOT_ALLOWED_FILES
                and (root / source_path).is_file()
            ):
                legacy_root_documents_present.append(source_path)

    return {
        "root": str(root),
        "root_files_present": len(root_files),
        "disallowed_root_files_present": disallowed_root,
        "tracked_root_files": len(tracked_root),
        "disallowed_tracked_root_files": disallowed_tracked_root,
        "tracked_root_files_missing_from_worktree": tracked_root_missing_from_worktree,
        "temp_root_files_present": sorted(temp_root_files),
        "missing_link_targets": missing_link_targets,
        "missing_allowed_dirs": missing_allowed_dirs,
        "missing_fixed_paths": missing_fixed_paths,
        "deprecated_paths_present": deprecated_present,
        "has_docs_catalog": (root / "docs" / "CATALOG.json").exists(),
        "has_docs_index": (root / "docs" / "INDEX.md").exists(),
        "reclassification_manifest_present": bool(reclassification_manifest),
        "legacy_root_documents_total": int(reclassification_manifest.get("total_legacy_root_files", 0) or 0),
        "legacy_root_documents_present": sorted(legacy_root_documents_present),
    }


def print_report(report: dict[str, object]) -> None:
    print("Repository layout audit")
    print(f"- root files present: {report['root_files_present']}")
    print(f"- disallowed root files present: {len(report['disallowed_root_files_present'])}")
    print(f"- tracked root files: {report['tracked_root_files']}")
    if report["reclassification_manifest_present"]:
        print(f"- legacy root documents present: {len(report['legacy_root_documents_present'])}")
    print(f"- temp root files present: {len(report['temp_root_files_present'])}")
    print(f"- missing link targets: {len(report['missing_link_targets'])}")
    print(f"- deprecated paths present: {len(report['deprecated_paths_present'])}")

    if report["disallowed_root_files_present"]:
        preview = ", ".join(report["disallowed_root_files_present"][:10])
        print(f"  root preview: {preview}")
    if report["disallowed_tracked_root_files"]:
        preview = ", ".join(report["disallowed_tracked_root_files"][:10])
        print(f"  tracked preview: {preview}")
    if report["tracked_root_files_missing_from_worktree"]:
        preview = ", ".join(report["tracked_root_files_missing_from_worktree"][:10])
        print(f"  missing tracked preview: {preview}")
    if report["legacy_root_documents_present"]:
        preview = ", ".join(report["legacy_root_documents_present"][:10])
        print(f"  legacy doc preview: {preview}")
    if report["temp_root_files_present"]:
        preview = ", ".join(report["temp_root_files_present"][:10])
        print(f"  temp preview: {preview}")
    if report["missing_link_targets"]:
        first = report["missing_link_targets"][0]
        print(f"  first missing link: {first['source']} -> {first['target']}")


def has_core_failures(report: dict[str, object]) -> bool:
    return any(
        (
            report["missing_link_targets"],
            report["missing_fixed_paths"],
            not report["has_docs_catalog"],
            not report["has_docs_index"],
        )
    )


def has_strict_failures(report: dict[str, object]) -> bool:
    return any(
        (
            has_core_failures(report),
            report["disallowed_root_files_present"],
            report["temp_root_files_present"],
        )
    )


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    report = build_report(root)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)

    if has_core_failures(report):
        return 1
    if args.strict and has_strict_failures(report):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
