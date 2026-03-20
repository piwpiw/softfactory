"""Shared runtime/workspace paths for local operational outputs."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def workspace_root() -> Path:
    """Return the local workspace root, defaulting to ``.workspace/``."""
    if os.getenv("VERCEL", "").strip() == "1":
        return Path(tempfile.gettempdir()) / "softfactory-workspace"

    configured = os.getenv("SOFTFACTORY_WORKSPACE_DIR", "").strip()
    if configured:
        root = Path(configured)
        if not root.is_absolute():
            root = PROJECT_ROOT / root
        return root
    return PROJECT_ROOT / ".workspace"


def workspace_path(*parts: str, create: bool = False) -> Path:
    """Return a path under the local workspace root."""
    path = workspace_root().joinpath(*parts)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent(path: Path) -> Path:
    """Ensure the parent directory exists for a file path."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "softfactory-workspace" / path.name
        fallback.parent.mkdir(parents=True, exist_ok=True)
        return fallback


def default_app_log_path() -> Path:
    """Canonical local app log file."""
    return ensure_parent(workspace_root() / "logs" / "app.log")


def root_artifact_quarantine_dir(stamp: str) -> Path:
    """Return the quarantine directory for stale root artifacts."""
    return workspace_path("root-artifacts", stamp, create=True)
