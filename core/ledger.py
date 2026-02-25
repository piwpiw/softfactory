"""
core/ledger.py
Stable ledger writer with file locking and proper section-based append.
Uses msvcrt (Windows) or fcntl (Unix) for cross-platform file locking.
"""

import re
import os
import sys
import time
from datetime import datetime
from pathlib import Path

LEDGER_PATH = Path(__file__).parent.parent / "CLAUDE.md"

# ---------------------------------------------------------------------------
# Cross-platform file locking
# ---------------------------------------------------------------------------

def _lock(fp):
    if sys.platform == "win32":
        import msvcrt
        msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(fp, fcntl.LOCK_EX)


def _unlock(fp):
    if sys.platform == "win32":
        import msvcrt
        try:
            msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
    else:
        import fcntl
        fcntl.flock(fp, fcntl.LOCK_UN)


def _write_with_lock(path: Path, content: str, retries: int = 5) -> None:
    """Write file content with exclusive lock, retrying on lock contention."""
    for attempt in range(retries):
        try:
            with open(path, "r+", encoding="utf-8") as fp:
                try:
                    _lock(fp)
                    fp.seek(0)
                    fp.write(content)
                    fp.truncate()
                finally:
                    _unlock(fp)
            return
        except (IOError, OSError):
            if attempt < retries - 1:
                time.sleep(0.1 * (attempt + 1))
            else:
                # Last resort: write without lock
                path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Change Log append
# ---------------------------------------------------------------------------

_CHANGELOG_HEADER_RE = re.compile(
    r"(## 📝 Change Log\s*\n(?:\|[^\n]+\n)*\|[-| ]+\|\n)",
    re.MULTILINE,
)


def log_to_ledger(agent_name: str, action: str) -> None:
    """Append a new row to the Change Log table in CLAUDE.md."""
    date = datetime.utcnow().strftime("%Y-%m-%d")
    new_row = f"| {date} | {agent_name} | {action} |\n"

    content = LEDGER_PATH.read_text(encoding="utf-8")

    match = _CHANGELOG_HEADER_RE.search(content)
    if match:
        # Insert row immediately after the separator line
        insert_pos = match.end()
        content = content[:insert_pos] + new_row + content[insert_pos:]
    else:
        # Fallback: append at file end
        content = content.rstrip() + "\n\n" + new_row

    _write_with_lock(LEDGER_PATH, content)
    print(f"[LEDGER] Logged: {agent_name} - {action}")


# ---------------------------------------------------------------------------
# Mission status update
# ---------------------------------------------------------------------------

_MISSION_ROW_RE = re.compile(
    r"(\| {mission_id} \|[^|]+\|[^|]+\|)\s*\S+\s*(\|)",
    re.MULTILINE,
)


def update_mission_status(mission_id: str, new_status: str) -> None:
    """Update a mission row status in the Active Missions table."""
    content = LEDGER_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"(\| {re.escape(mission_id)} \|[^|]+\|[^|]+\|)\s*\w[\w-]*\s*(\|)",
        re.MULTILINE,
    )
    updated, n = pattern.subn(rf"\1 {new_status} \2", content)
    if n == 0:
        print(f"[LEDGER] WARNING: Mission {mission_id} row not found.")
    else:
        _write_with_lock(LEDGER_PATH, updated)
        print(f"[LEDGER] Mission {mission_id} status -> {new_status}")
