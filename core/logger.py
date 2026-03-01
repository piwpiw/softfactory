"""
core/logger.py
Standardized logging for all Deca-Agents.
Format: [AGENT-ID][AGENT-NAME] message  (per .clauderules Rule 7)
"""

import logging
import sys
import io
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Windows cp949 콘솔에서 유니코드 깨짐 방지
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def get_logger(agent_id: str, agent_name: str) -> logging.Logger:
    name = f"{agent_id}_{agent_name}"
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(logging.DEBUG)
    prefix = f"[{agent_id}][{agent_name}]"

    formatter = logging.Formatter(f"{prefix} %(levelname)s - %(message)s")

    # Console handler (utf-8 safe)
    try:
        stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except AttributeError:
        stream = sys.stdout
    ch = logging.StreamHandler(stream)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(LOG_DIR / f"{name}.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter(f"%(asctime)s {prefix} %(levelname)s - %(message)s"))
    logger.addHandler(fh)

    return logger
