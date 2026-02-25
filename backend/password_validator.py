"""Password strength validation and policy enforcement"""
import re
from typing import Tuple


class PasswordValidator:
    """Enforces enterprise-grade password policy"""

    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True

    SPECIAL_CHARS = r'!@#$%^&*()_+-=[]{}|;:,.<>?'

    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        """
        Validate password against security policy.

        Returns: (is_valid, error_message)
        """
        if not password:
            return False, "Password cannot be empty"

        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long"

        if PasswordValidator.REQUIRE_UPPERCASE:
            if not re.search(r'[A-Z]', password):
                return False, "Password must contain at least one uppercase letter"

        if PasswordValidator.REQUIRE_DIGIT:
            if not re.search(r'\d', password):
                return False, "Password must contain at least one digit"

        if PasswordValidator.REQUIRE_SPECIAL:
            if not re.search(f'[{re.escape(PasswordValidator.SPECIAL_CHARS)}]', password):
                return False, f"Password must contain at least one special character: {PasswordValidator.SPECIAL_CHARS}"

        # Check for common weak passwords
        weak_patterns = [
            r'123456',
            r'password',
            r'qwerty',
            r'abc123',
            r'111111',
        ]

        for pattern in weak_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                return False, "Password is too common. Choose a stronger password"

        return True, ""

    @staticmethod
    def get_requirements() -> dict:
        """Return password requirements for API responses"""
        return {
            'min_length': PasswordValidator.MIN_LENGTH,
            'require_uppercase': PasswordValidator.REQUIRE_UPPERCASE,
            'require_digit': PasswordValidator.REQUIRE_DIGIT,
            'require_special': PasswordValidator.REQUIRE_SPECIAL,
            'special_chars': PasswordValidator.SPECIAL_CHARS,
        }
