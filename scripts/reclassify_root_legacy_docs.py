"""Reclassify safe root legacy docs into canonical docs zones."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


DOC_SUFFIXES = (".md", ".txt")
REFERENCE_SUFFIXES = (".md", ".txt", ".json", ".jsonl")
PROTECTED_PREFIXES = (
    ".github/workflows/",
    "scripts/",
    "backend/",
    "web/",
    "tests/",
    "docker-compose",
    "Dockerfile",
    "Makefile",
    "start_server.py",
    "start_platform.py",
    "run.py",
    "team_work_manager.py",
)
EXCLUDED_DIR_NAMES = {
    ".git",
    ".workspace",
    "node_modules",
    "nodejs",
    "nvm",
    "htmlcov",
}
EXCLUDED_PREFIXES = (
    "docs/plans/execution/",
)
START_PAGE_EXCLUDES = {
    "README.md",
    "STATUS.md",
}
MARKDOWN_LINK_RE = re.compile(r"(?<!\!)\[(?P<label>[^\]]+)\]\((?P<target>[^)]+)\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=None,
        help="Existing manifest used as the eligibility source.",
    )
    parser.add_argument(
        "--output-manifest",
        type=Path,
        default=None,
        help="Manifest to write for the executed or proposed wave.",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_ref(value: str) -> str:
    return value.replace("\\", "/")


def is_protected_reference(value: str) -> bool:
    normalized = normalize_ref(value)
    return normalized in START_PAGE_EXCLUDES or normalized.startswith(PROTECTED_PREFIXES)


def is_doc_reference(value: str) -> bool:
    return normalize_ref(value).lower().endswith(REFERENCE_SUFFIXES)


def is_eligible_entry(root: Path, entry: dict[str, object]) -> bool:
    source_path = normalize_ref(str(entry.get("source_path", "")))
    if not source_path or not source_path.lower().endswith(DOC_SUFFIXES):
        return False
    if not (root / source_path).is_file():
        return False

    references = [normalize_ref(str(item)) for item in entry.get("reference_sources", [])]
    if any(is_protected_reference(item) for item in references):
        return False
    if any(not is_doc_reference(item) for item in references):
        return False
    return True


def collect_wave_entries(root: Path, manifest: dict[str, object]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for entry in manifest.get("entries", []):
        if is_eligible_entry(root, entry):
            entries.append(
                {
                    "source_path": normalize_ref(str(entry["source_path"])),
                    "target_path": normalize_ref(str(entry["target_path"])),
                    "destination_class": entry.get("destination_class", ""),
                    "reference_count": int(entry.get("reference_count", 0) or 0),
                    "reference_sources": [normalize_ref(str(item)) for item in entry.get("reference_sources", [])],
                    "reason": "doc-only-safe-wave-b",
                }
            )
    return sorted(entries, key=lambda item: (item["reference_count"], item["source_path"]))


def write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def move_entries(root: Path, entries: list[dict[str, object]]) -> None:
    for entry in entries:
        source = root / entry["source_path"]
        target = root / entry["target_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))


def should_scan_text(rel_path: str) -> bool:
    normalized = normalize_ref(rel_path)
    if any(normalized.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    parts = normalized.split("/")
    if any(part in EXCLUDED_DIR_NAMES for part in parts[:-1]):
        return False
    return normalized.lower().endswith(DOC_SUFFIXES)


def text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_path = path.relative_to(root).as_posix()
        if should_scan_text(rel_path):
            files.append(path)
    return sorted(files)


def rewrite_links(text: str, file_path: Path, root: Path, mapping: dict[str, str]) -> str:
    relative_targets: dict[str, str] = {}
    for source_rel, target_rel in mapping.items():
        target_abs = (root / target_rel).resolve()
        relative_targets[source_rel] = Path(
            os.path.relpath(target_abs, file_path.parent.resolve())
        ).as_posix()

    def replace_match(match: re.Match[str]) -> str:
        raw_target = match.group("target").strip()
        target_only = raw_target.split()[0].strip("<>").split("#", 1)[0]
        if not target_only or raw_target.startswith(("http://", "https://", "mailto:", "javascript:", "#")):
            return match.group(0)

        resolved = (file_path.parent / target_only).resolve()
        for source_rel, target_rel in mapping.items():
            source_abs = (root / source_rel).resolve()
            if resolved != source_abs:
                continue
            return match.group(0).replace(target_only, relative_targets[source_rel])
        return match.group(0)

    updated = MARKDOWN_LINK_RE.sub(replace_match, text)

    for source_rel, target_rel in mapping.items():
        relative_token = f"`{relative_targets[source_rel]}`"
        basename_token = f"`{Path(source_rel).name}`"
        source_token = f"`{source_rel}`"
        updated = updated.replace(source_token, relative_token)
        updated = updated.replace(basename_token, relative_token)

    return updated


def update_text_references(root: Path, mapping: dict[str, str]) -> list[str]:
    changed: list[str] = []
    for path in text_files(root):
        original = path.read_text(encoding="utf-8", errors="ignore")
        updated = rewrite_links(original, path, root, mapping)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path.relative_to(root).as_posix())
    return changed


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    source_manifest = args.source_manifest or root / "docs" / "reference" / "root-reclassification-manifest-wave-a.json"
    output_manifest = args.output_manifest or root / "docs" / "reference" / "root-reclassification-manifest-wave-b.json"

    manifest = load_manifest(source_manifest)
    entries = collect_wave_entries(root, manifest)
    mapping = {entry["source_path"]: entry["target_path"] for entry in entries}

    report: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "wave": "wave-b",
        "source_manifest": source_manifest.relative_to(root).as_posix(),
        "entry_count": len(entries),
        "entries": entries,
        "executed": bool(args.execute),
    }

    if args.execute and entries:
        move_entries(root, entries)
        changed_files = update_text_references(root, mapping)
        report["updated_text_files"] = changed_files
        write_manifest(output_manifest, report)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"entry_count={len(entries)}")
        for entry in entries:
            print(f"{entry['source_path']} -> {entry['target_path']}")
        if args.execute:
            print(f"output_manifest={output_manifest.relative_to(root).as_posix()}")
            print(f"updated_text_files={len(report.get('updated_text_files', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
