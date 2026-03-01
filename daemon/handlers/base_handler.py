"""
Abstract base handler class for all Telegram bot handlers.

Provides common interface and utilities for:
- Message formatting and sending
- Logging and error handling
- State management
- Input validation
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from datetime import datetime


class BaseHandler(ABC):
    """Abstract base class for all bot command handlers."""

    def __init__(self, sender_func, logger_func, bot_context: Optional[Dict[str, Any]] = None):
        """
        Initialize handler.

        Args:
            sender_func: Function to send Telegram messages
            logger_func: Function for logging
            bot_context: Optional context (state, config, etc.)
        """
        self._send_message = sender_func
        self._log = logger_func
        self.context = bot_context or {}

    @abstractmethod
    async def handle(self, chat_id: int, command: str, args: list[str]) -> dict[str, Any]:
        """
        Handle a command.

        Args:
            chat_id: Telegram chat ID
            command: Command name (e.g., 'status', 'deploy')
            args: Command arguments

        Returns:
            Result dict with 'success', 'message', optional 'data'
        """
        pass

    async def send_text(self, chat_id: int, text: str, parse_mode: str = "HTML") -> None:
        """Send text message."""
        try:
            self._send_message(chat_id, text, parse_mode)
        except Exception as e:
            self._log(f"WARN send_text failed: {e}")

    async def send_error(self, chat_id: int, error_msg: str) -> None:
        """Send error message."""
        msg = f"❌ 오류: {error_msg}"
        await self.send_text(chat_id, msg)

    def _format_report(
        self,
        request: str,
        progress: str,
        result: str,
        links: Optional[Dict[str, str]] = None,
        details: str = "",
    ) -> str:
        """Format 3-line report (REQUEST | PROGRESS | RESULT)."""
        msg = f"""
📬 **REQUEST**: {request}
⏳ **PROGRESS**: {progress}
✅ **RESULT**: {result}
"""
        if links:
            msg += "\n*LINKS:*\n"
            for name, url in links.items():
                msg += f"• [{name}]({url})\n"

        if details:
            msg += f"\n*DETAILS:*\n{details}"

        return msg.strip()

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _log_command(self, chat_id: int, command: str, args: list[str]) -> None:
        """Log command execution."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        args_str = " ".join(args) if args else ""
        self._log(f"[{timestamp}] CMD [chat_id={chat_id}] /{command} {args_str}")

    def _log_result(self, result: dict[str, Any]) -> None:
        """Log result."""
        status = "✓" if result.get("success") else "✗"
        msg = result.get("message", "")
        self._log(f"{status} Result: {msg}")
