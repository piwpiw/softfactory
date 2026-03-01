"""
Input validation and security utilities for all handlers.

Provides:
- Command validation
- Argument sanitization
- Security checks
- Rate limiting
"""

import re
from typing import Optional, List, Tuple
from datetime import datetime, timedelta


class InputValidator:
    """Validates user input for commands."""

    # Allowed command patterns
    ALLOWED_COMMANDS = {
        # v1 commands
        "start",
        "status",
        "deploy",
        "mission",
        "report",
        "progress",
        "timeline",
        "breakdown",
        "pages",
        "help",
        # v2 commands
        "task-new",
        "task-list",
        "task-activate",
        # report commands
        "s",
        "summary",
        "export",
        "logs",
        "remind",
        # short forms
        "h",
    }

    # Max argument lengths
    MAX_ARG_LENGTH = 1000
    MAX_COMMAND_LENGTH = 50

    @staticmethod
    def validate_command(command: str) -> Tuple[bool, str]:
        """
        Validate command name.

        Returns:
            (is_valid, error_message)
        """
        if not command:
            return False, "명령어가 비어 있습니다"

        if len(command) > InputValidator.MAX_COMMAND_LENGTH:
            return False, f"명령어가 너무 깁니다 (max: {InputValidator.MAX_COMMAND_LENGTH})"

        # Remove leading slash if present
        cmd = command.lstrip("/")

        if cmd not in InputValidator.ALLOWED_COMMANDS:
            return False, f"알 수 없는 명령어: {cmd}"

        return True, ""

    @staticmethod
    def validate_args(args: List[str]) -> Tuple[bool, str]:
        """
        Validate arguments list.

        Returns:
            (is_valid, error_message)
        """
        if not args:
            return True, ""  # No args is valid

        for i, arg in enumerate(args):
            if len(arg) > InputValidator.MAX_ARG_LENGTH:
                return False, f"인자 {i}가 너무 깁니다 (max: {InputValidator.MAX_ARG_LENGTH})"

        return True, ""

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Remove/escape potentially dangerous characters."""
        # Remove null bytes
        text = text.replace("\x00", "")
        # Limit length
        text = text[: InputValidator.MAX_ARG_LENGTH]
        return text


class SecurityValidator:
    """Security checks and rate limiting."""

    def __init__(self):
        """Initialize with rate limit tracking."""
        self._rate_limits: dict[int, list[datetime]] = {}  # chat_id -> [timestamps]
        self.RATE_LIMIT_WINDOW_SEC = 60
        self.RATE_LIMIT_MAX_CALLS = 30  # 30 calls per 60 seconds

    def check_rate_limit(self, chat_id: int) -> Tuple[bool, str]:
        """
        Check if chat_id is rate limited.

        Returns:
            (is_allowed, error_message)
        """
        now = datetime.now()

        # Initialize if not present
        if chat_id not in self._rate_limits:
            self._rate_limits[chat_id] = []

        # Remove old entries (older than window)
        cutoff = now - timedelta(seconds=self.RATE_LIMIT_WINDOW_SEC)
        self._rate_limits[chat_id] = [ts for ts in self._rate_limits[chat_id] if ts > cutoff]

        # Check limit
        if len(self._rate_limits[chat_id]) >= self.RATE_LIMIT_MAX_CALLS:
            return False, "Rate limit exceeded. Please wait a moment."

        # Add current request
        self._rate_limits[chat_id].append(now)
        return True, ""

    def check_injection_patterns(self, text: str) -> Tuple[bool, str]:
        """
        Check for common injection patterns.

        Returns:
            (is_safe, error_message)
        """
        dangerous_patterns = [
            r"<script[^>]*>",  # Script tags
            r"javascript:",  # Javascript protocol
            r"on\w+\s*=",  # Event handlers
            r"[\r\n]\s*exec\s*\(",  # Exec calls
            r"[\r\n]\s*eval\s*\(",  # Eval calls
            r"\$\{.*\}",  # Template injection
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Invalid characters detected"

        return True, ""

    def validate_chat_id(self, chat_id: int) -> Tuple[bool, str]:
        """
        Validate chat_id format.

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(chat_id, int):
            return False, "Invalid chat_id format"

        if chat_id <= 0:
            return False, "chat_id must be positive"

        return True, ""

    def check_command_permission(self, chat_id: int, command: str) -> Tuple[bool, str]:
        """
        Check if user has permission for command.

        In real implementation, would check against user database.

        Returns:
            (is_allowed, error_message)
        """
        # For now, allow all commands for all users
        # In production, would check against permission matrix
        return True, ""


class CommandValidator:
    """Combined validator for commands."""

    def __init__(self):
        """Initialize validators."""
        self.input_validator = InputValidator()
        self.security_validator = SecurityValidator()

    def validate(self, chat_id: int, command: str, args: List[str]) -> Tuple[bool, str]:
        """
        Validate complete command request.

        Returns:
            (is_valid, error_message)
        """
        # Check chat_id
        is_valid, error = self.security_validator.validate_chat_id(chat_id)
        if not is_valid:
            return False, error

        # Check rate limit
        is_allowed, error = self.security_validator.check_rate_limit(chat_id)
        if not is_allowed:
            return False, error

        # Validate command
        is_valid, error = self.input_validator.validate_command(command)
        if not is_valid:
            return False, error

        # Validate arguments
        is_valid, error = self.input_validator.validate_args(args)
        if not is_valid:
            return False, error

        # Check for injection patterns
        command_text = f"/{command} " + " ".join(args)
        is_safe, error = self.security_validator.check_injection_patterns(command_text)
        if not is_safe:
            return False, error

        # Check permissions
        is_allowed, error = self.security_validator.check_command_permission(chat_id, command)
        if not is_allowed:
            return False, error

        return True, ""

    def sanitize_args(self, args: List[str]) -> List[str]:
        """Sanitize arguments."""
        return [self.input_validator.sanitize_text(arg) for arg in args]
