"""Input Validation & Sanitization Module

Provides centralized input validation for all API endpoints.
Prevents XSS, SQL injection patterns, and enforces field constraints.

Usage:
    from backend.input_validator import validate_email, validate_string, sanitize_html, validate_request_data

    # Validate individual fields
    is_valid, error = validate_email(data['email'])

    # Validate an entire request body
    errors = validate_request_data(data, {
        'email': {'type': 'email', 'required': True},
        'name': {'type': 'string', 'required': True, 'min_length': 1, 'max_length': 120},
        'password': {'type': 'password', 'required': True, 'min_length': 8},
    })
"""

import re
import html
from typing import Optional, Tuple, Any


# === Constants ===

# Email regex (RFC 5322 simplified - covers 99.9% of valid emails)
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9]'
    r'(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'
    r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
)

# Common SQL injection patterns to detect
SQL_INJECTION_PATTERNS = [
    re.compile(r"('|\")\s*(OR|AND)\s+.*=", re.IGNORECASE),
    re.compile(r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE)\s+", re.IGNORECASE),
    re.compile(r"UNION\s+(ALL\s+)?SELECT", re.IGNORECASE),
    re.compile(r"--\s*$", re.MULTILINE),
    re.compile(r"/\*.*?\*/", re.DOTALL),
]

# XSS patterns
XSS_PATTERNS = [
    re.compile(r"<script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<iframe", re.IGNORECASE),
    re.compile(r"<object", re.IGNORECASE),
    re.compile(r"<embed", re.IGNORECASE),
]

# Slug pattern (URL-safe identifiers)
SLUG_REGEX = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$')

# Platform whitelist for SNS
VALID_SNS_PLATFORMS = [
    'instagram', 'tiktok', 'twitter', 'linkedin', 'facebook',
    'youtube', 'threads', 'blog', 'naver'
]

# Review platform whitelist
VALID_REVIEW_PLATFORMS = [
    'naver', 'instagram', 'blog', 'youtube', 'tiktok', 'facebook'
]


# === Core Validation Functions ===

def sanitize_html(value: str) -> str:
    """Escape HTML entities to prevent XSS attacks.

    Args:
        value: Raw string input

    Returns:
        HTML-escaped string safe for output
    """
    if not isinstance(value, str):
        return str(value)
    return html.escape(value, quote=True)


def check_sql_injection(value: str) -> bool:
    """Check if a string contains SQL injection patterns.

    Args:
        value: Input string to check

    Returns:
        True if suspicious pattern found, False if clean
    """
    if not isinstance(value, str):
        return False
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            return True
    return False


def check_xss(value: str) -> bool:
    """Check if a string contains XSS attack patterns.

    Args:
        value: Input string to check

    Returns:
        True if XSS pattern found, False if clean
    """
    if not isinstance(value, str):
        return False
    for pattern in XSS_PATTERNS:
        if pattern.search(value):
            return True
    return False


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email format.

    Args:
        email: Email address to validate

    Returns:
        Tuple of (is_valid, error_message_or_None)
    """
    if not email or not isinstance(email, str):
        return False, 'Email is required'

    email = email.strip()

    if len(email) > 254:
        return False, 'Email must be 254 characters or less'

    if not EMAIL_REGEX.match(email):
        return False, 'Invalid email format'

    # Check for dangerous patterns
    if check_sql_injection(email):
        return False, 'Invalid email format'

    return True, None


def validate_password(password: str, min_length: int = 8, max_length: int = 128) -> Tuple[bool, Optional[str]]:
    """Validate password strength.

    Args:
        password: Password to validate
        min_length: Minimum password length (default: 8)
        max_length: Maximum password length (default: 128)

    Returns:
        Tuple of (is_valid, error_message_or_None)
    """
    if not password or not isinstance(password, str):
        return False, 'Password is required'

    if len(password) < min_length:
        return False, f'Password must be at least {min_length} characters'

    if len(password) > max_length:
        return False, f'Password must be {max_length} characters or less'

    return True, None


def validate_string(value: str, field_name: str = 'Field',
                    min_length: int = 0, max_length: int = 500,
                    required: bool = True, allow_html: bool = False) -> Tuple[bool, Optional[str], str]:
    """Validate and sanitize a string field.

    Args:
        value: String to validate
        field_name: Human-readable field name for error messages
        min_length: Minimum string length
        max_length: Maximum string length
        required: Whether the field is required
        allow_html: If False, check for XSS patterns

    Returns:
        Tuple of (is_valid, error_message_or_None, sanitized_value)
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            return False, f'{field_name} is required', ''
        return True, None, ''

    if not isinstance(value, str):
        return False, f'{field_name} must be a string', ''

    value = value.strip()

    if len(value) < min_length:
        return False, f'{field_name} must be at least {min_length} characters', value

    if len(value) > max_length:
        return False, f'{field_name} must be {max_length} characters or less', value

    # Check for dangerous patterns
    if check_sql_injection(value):
        return False, f'{field_name} contains invalid characters', value

    if not allow_html and check_xss(value):
        return False, f'{field_name} contains invalid content', value

    # Sanitize HTML entities
    sanitized = sanitize_html(value)

    return True, None, sanitized


def validate_slug(slug: str) -> Tuple[bool, Optional[str]]:
    """Validate a URL slug.

    Args:
        slug: Slug to validate

    Returns:
        Tuple of (is_valid, error_message_or_None)
    """
    if not slug or not isinstance(slug, str):
        return False, 'Slug is required'

    if not SLUG_REGEX.match(slug):
        return False, 'Slug must contain only letters, numbers, hyphens, and underscores (max 100 chars)'

    return True, None


def validate_platform(platform: str, valid_list: list = None) -> Tuple[bool, Optional[str]]:
    """Validate a platform identifier against whitelist.

    Args:
        platform: Platform name to validate
        valid_list: List of valid platform names (defaults to VALID_SNS_PLATFORMS)

    Returns:
        Tuple of (is_valid, error_message_or_None)
    """
    if valid_list is None:
        valid_list = VALID_SNS_PLATFORMS

    if not platform or not isinstance(platform, str):
        return False, 'Platform is required'

    if platform.lower() not in valid_list:
        return False, f'Invalid platform. Must be one of: {", ".join(valid_list)}'

    return True, None


def validate_integer(value: Any, field_name: str = 'Field',
                     min_val: Optional[int] = None, max_val: Optional[int] = None,
                     required: bool = True) -> Tuple[bool, Optional[str], Optional[int]]:
    """Validate an integer field.

    Args:
        value: Value to validate
        field_name: Human-readable field name
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        required: Whether the field is required

    Returns:
        Tuple of (is_valid, error_message_or_None, parsed_int_or_None)
    """
    if value is None:
        if required:
            return False, f'{field_name} is required', None
        return True, None, None

    try:
        int_val = int(value)
    except (ValueError, TypeError):
        return False, f'{field_name} must be an integer', None

    if min_val is not None and int_val < min_val:
        return False, f'{field_name} must be at least {min_val}', None

    if max_val is not None and int_val > max_val:
        return False, f'{field_name} must be at most {max_val}', None

    return True, None, int_val


def validate_request_data(data: dict, schema: dict) -> list:
    """Validate a request data dictionary against a schema.

    Args:
        data: Request data (from request.get_json())
        schema: Validation schema, e.g.:
            {
                'email': {'type': 'email', 'required': True},
                'name': {'type': 'string', 'required': True, 'min_length': 1, 'max_length': 120},
                'password': {'type': 'password', 'required': True, 'min_length': 8},
                'age': {'type': 'integer', 'required': False, 'min_val': 0, 'max_val': 150},
            }

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if not data or not isinstance(data, dict):
        return ['Request body is required and must be JSON']

    for field_name, rules in schema.items():
        field_type = rules.get('type', 'string')
        required = rules.get('required', True)
        value = data.get(field_name)

        if field_type == 'email':
            if value or required:
                valid, error = validate_email(value or '')
                if not valid:
                    errors.append(error)

        elif field_type == 'password':
            if value or required:
                min_len = rules.get('min_length', 8)
                max_len = rules.get('max_length', 128)
                valid, error = validate_password(value or '', min_len, max_len)
                if not valid:
                    errors.append(error)

        elif field_type == 'string':
            min_len = rules.get('min_length', 0)
            max_len = rules.get('max_length', 500)
            valid, error, _ = validate_string(
                value, field_name, min_len, max_len, required
            )
            if not valid:
                errors.append(error)

        elif field_type == 'slug':
            if value or required:
                valid, error = validate_slug(value or '')
                if not valid:
                    errors.append(error)

        elif field_type == 'platform':
            valid_list = rules.get('valid_list')
            if value or required:
                valid, error = validate_platform(value or '', valid_list)
                if not valid:
                    errors.append(error)

        elif field_type == 'integer':
            min_val = rules.get('min_val')
            max_val = rules.get('max_val')
            valid, error, _ = validate_integer(value, field_name, min_val, max_val, required)
            if not valid:
                errors.append(error)

    return errors
