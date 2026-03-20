"""Generate the canonical documentation catalog for the repository."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from repo_layout_policy import (
    CANONICAL_DOCS,
    DEPRECATED_PATHS,
    FIXED_PATHS,
    ROOT_ALLOWED_DIRS,
    ROOT_ALLOWED_FILES,
    WORKSPACE_LOCAL_PATHS,
    categorize_document,
    is_excluded_document,
)

TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
METADATA_BLOCK_RE = re.compile(r"<!--\s*doc-metadata(.*?)-->", re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--legacy-output", type=Path, default=None)
    return parser.parse_args()


def parse_doc_metadata(text: str) -> dict[str, str]:
    match = METADATA_BLOCK_RE.search(text)
    if not match:
        return {}

    metadata: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip()
    return metadata


def extract_title(text: str, fallback: str) -> str:
    match = TITLE_RE.search(text)
    if match:
        return match.group(1).strip()
    return fallback


def collect_documents(root: Path) -> list[dict[str, object]]:
    docs_root = root / "docs"
    candidates = {root / "README.md", root / "STATUS.md"}
    candidates.update(path for path in docs_root.rglob("*.md"))

    documents: list[dict[str, object]] = []
    for path in sorted(candidates):
        if not path.is_file():
            continue

        rel_path = path.relative_to(root).as_posix()
        if is_excluded_document(rel_path):
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        metadata = parse_doc_metadata(text)
        keywords = [
            token.strip()
            for token in metadata.get("keywords", "").split(",")
            if token.strip()
        ]

        documents.append(
            {
                "path": rel_path,
                "title": extract_title(text, path.stem),
                "category": categorize_document(rel_path),
                "status": metadata.get("status", "active"),
                "updated": metadata.get(
                    "updated",
                    datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d"),
                ),
                "owner": metadata.get("owner", "unassigned"),
                "keywords": keywords,
                "canonical": rel_path in CANONICAL_DOCS,
            }
        )
    return documents


def build_catalog(root: Path) -> dict[str, object]:
    documents = collect_documents(root)
    counts = Counter(doc["category"] for doc in documents)

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "scripts/generate_docs_catalog.py",
        "entrypoints": {
            "root_readme": "README.md",
            "docs_index": "docs/INDEX.md",
            "status": "STATUS.md",
        },
        "canonical_paths": {
            "fixed_paths": list(FIXED_PATHS),
            "deprecated_paths": list(DEPRECATED_PATHS),
            "root_allowed_files": sorted(ROOT_ALLOWED_FILES),
            "root_allowed_dirs": sorted(ROOT_ALLOWED_DIRS),
            "workspace_local_paths": list(WORKSPACE_LOCAL_PATHS),
        },
        "counts": {
            "documents": len(documents),
            "by_category": dict(sorted(counts.items())),
        },
        "documents": documents,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    output = args.output or root / "docs" / "CATALOG.json"
    legacy_output = args.legacy_output or root / "docs" / "doc-index.json"

    catalog = build_catalog(root)
    write_json(output, catalog)

    legacy_catalog = dict(catalog)
    legacy_catalog["legacy_alias_of"] = "docs/CATALOG.json"
    write_json(legacy_output, legacy_catalog)

    print(f"refreshed: {catalog['counts']['documents']} docs -> {output}")
    print(f"legacy: {legacy_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
