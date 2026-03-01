"""
Telegram bot handlers - modular architecture for Unified Bot v3.0

This package consolidates:
- Jarvis v1 commands (legacy compatibility)
- Daemon v2 features (Claude integration + task management)
- New reporting and analytics capabilities

Handler structure:
├── base_handler.py        - Abstract base class
├── jarvis_commands.py     - Legacy v1 commands (preserved)
├── task_handler.py        - v2 task management
├── report_handler.py      - Reporting & analytics
├── claude_handler.py      - Claude integration
└── validation.py          - Input validation + security
"""

from .base_handler import BaseHandler
from .jarvis_commands import JarvisCommandsHandler
from .task_handler import TaskHandler
from .report_handler import ReportHandler
from .claude_handler import ClaudeHandler
from .validation import InputValidator, SecurityValidator

__all__ = [
    "BaseHandler",
    "JarvisCommandsHandler",
    "TaskHandler",
    "ReportHandler",
    "ClaudeHandler",
    "InputValidator",
    "SecurityValidator",
]
