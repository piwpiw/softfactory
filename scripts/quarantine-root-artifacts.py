"""Move stale root temp/log artifacts into the local workspace quarantine."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from repo_layout_policy import TEMP_ROOT_PREFIXES, TEMP_ROOT_SUFFIXES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--older-than-hours", type=float, default=24.0)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def should_quarantine(path: Path) -> bool:
    return path.name.startswith(TEMP_ROOT_PREFIXES) or path.suffix in TEMP_ROOT_SUFFIXES


def workspace_root(root: Path) -> Path:
    configured = os.getenv("SOFTFACTORY_WORKSPACE_DIR", "").strip()
    if configured:
        candidate = Path(configured)
        if not candidate.is_absolute():
            candidate = root / candidate
        return candidate
    return root / ".workspace"


def root_artifact_quarantine_dir(root: Path, stamp: str) -> Path:
    destination = workspace_root(root) / "root-artifacts" / stamp
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def candidate_files(root: Path, older_than_hours: float) -> list[Path]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
    candidates: list[Path] = []
    for entry in root.iterdir():
        if not entry.is_file():
            continue
        if not should_quarantine(entry):
            continue
        modified = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc)
        if modified <= cutoff:
            candidates.append(entry)
    return sorted(candidates, key=lambda path: path.name.lower())


def unique_destination(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    for index in range(1, 1000):
        numbered = directory / f"{stem}-{index}{suffix}"
        if not numbered.exists():
            return numbered
    raise RuntimeError(f"unable to allocate unique destination for {filename}")


def move_candidates(paths: list[Path], stamp: str) -> list[dict[str, str]]:
    root = paths[0].parent if paths else Path.cwd()
    destination_root = root_artifact_quarantine_dir(root, stamp)
    moved: list[dict[str, str]] = []
    for source in paths:
        destination = unique_destination(destination_root, source.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        moved.append(
            {
                "source": source.name,
                "destination": destination.as_posix(),
                "bytes": str(destination.stat().st_size),
            }
        )

    manifest = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(moved),
        "items": moved,
    }
    (destination_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return moved


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    candidates = candidate_files(root, args.older_than_hours)

    report = {
        "root": str(root),
        "older_than_hours": args.older_than_hours,
        "count": len(candidates),
        "candidates": [path.name for path in candidates],
        "executed": bool(args.execute),
    }

    if args.execute and candidates:
        report["moved"] = move_candidates(candidates, stamp)
        report["quarantine_dir"] = str(root_artifact_quarantine_dir(root, stamp))

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        action = "moved" if args.execute else "candidate"
        print(f"{action}_count={len(candidates)}")
        for path in report["candidates"]:
            print(path)
        if args.execute and candidates:
            print(f"quarantine_dir={report['quarantine_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
