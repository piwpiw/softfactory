"""Security middleware for rate limiting and account lockout"""
import logging
from datetime import datetime, timedelta
from flask import request, jsonify, g
from functools import wraps
from typing import Optional
from .models import db, LoginAttempt, User

logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMIT_WINDOW = 60  # seconds
MAX_ATTEMPTS_PER_WINDOW = 5
ACCOUNT_LOCKOUT_THRESHOLD = 5
ACCOUNT_LOCKOUT_DURATION = 15  # minutes


class SecurityEventLogger:
    """Logs security-relevant events for audit trail"""

    SECURITY_LOG_FILE = 'logs/security_audit.log'

    @staticmethod
    def log_event(event_type: str, user_id: Optional[int] = None, email: Optional[str] = None,
                  ip_address: Optional[str] = None, details: Optional[dict] = None):
        """
        Log a security event.

        Args:
            event_type: e.g., 'LOGIN_ATTEMPT', 'LOGIN_FAILURE', 'ACCOUNT_LOCKED', 'PASSWORD_CHANGED'
            user_id: User ID if applicable
            email: Email if applicable
            ip_address: Client IP
            details: Additional context dict
        """
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'user_id': user_id,
                'email': email,
                'ip_address': ip_address or 'UNKNOWN',
                'details': details or {}
            }

            logger.warning(f"SECURITY_EVENT: {log_entry}")
            return log_entry
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")


class LoginAttemptTracker:
    """Tracks login attempts for rate limiting and account lockout"""

    @staticmethod
    def record_attempt(email: str, success: bool = False) -> LoginAttempt:
        """Record a login attempt"""
        ip_address = request.remote_addr if request else 'UNKNOWN'

        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            success=success,
            timestamp=datetime.utcnow()
        )

        db.session.add(attempt)
        db.session.commit()

        logger.info(f"Login attempt recorded: {email} from {ip_address} ({'success' if success else 'failed'})")
        return attempt

    @staticmethod
    def get_recent_attempts(email: str, minutes: int = 1) -> list:
        """Get login attempts in last N minutes"""
        time_threshold = datetime.utcnow() - timedelta(minutes=minutes)
        return LoginAttempt.query.filter(
            LoginAttempt.email == email,
            LoginAttempt.timestamp >= time_threshold
        ).order_by(LoginAttempt.timestamp.desc()).all()

    @staticmethod
    def get_failed_attempt_count(email: str, minutes: int = 1) -> int:
        """Get count of failed login attempts in last N minutes"""
        time_threshold = datetime.utcnow() - timedelta(minutes=minutes)
        return LoginAttempt.query.filter(
            LoginAttempt.email == email,
            LoginAttempt.success == False,
            LoginAttempt.timestamp >= time_threshold
        ).count()

    @staticmethod
    def is_rate_limited(email: str) -> bool:
        """Check if email is rate limited (too many attempts in short window)"""
        failed_count = LoginAttemptTracker.get_failed_attempt_count(email, minutes=1)
        return failed_count >= MAX_ATTEMPTS_PER_WINDOW

    @staticmethod
    def is_account_locked(user: User) -> bool:
        """Check if account is locked due to too many failed attempts"""
        if not user.is_locked:
            return False

        # Check if lockout duration has expired
        if user.locked_until and datetime.utcnow() >= user.locked_until:
            # Unlock the account
            user.is_locked = False
            user.locked_until = None
            db.session.commit()
            SecurityEventLogger.log_event('ACCOUNT_UNLOCKED', user_id=user.id, email=user.email)
            return False

        return True

    @staticmethod
    def lock_account(user: User, duration_minutes: int = ACCOUNT_LOCKOUT_DURATION):
        """Lock account for specified duration"""
        user.is_locked = True
        user.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        db.session.commit()

        SecurityEventLogger.log_event(
            'ACCOUNT_LOCKED',
            user_id=user.id,
            email=user.email,
            details={'duration_minutes': duration_minutes}
        )

        logger.warning(f"Account locked for {user.email}: {user.locked_until}")

    @staticmethod
    def clear_attempts(email: str):
        """Clear all login attempts for email (on successful login)"""
        LoginAttempt.query.filter_by(email=email).delete()
        db.session.commit()


def require_rate_limit(f):
    """Decorator to enforce rate limiting on login endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Only apply to POST requests (login/register)
        if request.method not in ['POST']:
            return f(*args, **kwargs)

        data = request.get_json() or {}
        email = data.get('email', '')

        # Check rate limit
        if LoginAttemptTracker.is_rate_limited(email):
            ip_address = request.remote_addr
            SecurityEventLogger.log_event(
                'RATE_LIMIT_EXCEEDED',
                email=email,
                ip_address=ip_address,
                details={'endpoint': request.endpoint}
            )
            logger.warning(f"Rate limit exceeded for {email} from {ip_address}")
            return jsonify({
                'error': 'Too many login attempts. Please try again in 1 minute.',
                'error_code': 'RATE_LIMITED'
            }), 429

        return f(*args, **kwargs)

    return decorated


def log_security_event_decorator(event_type: str):
    """Decorator to log security events (e.g., password changes, admin actions)"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = g.get('user_id')
            ip_address = request.remote_addr if request else 'UNKNOWN'

            try:
                result = f(*args, **kwargs)
                SecurityEventLogger.log_event(
                    event_type,
                    user_id=user_id,
                    ip_address=ip_address,
                    details={'endpoint': request.endpoint}
                )
                return result
            except Exception as e:
                SecurityEventLogger.log_event(
                    f'{event_type}_FAILED',
                    user_id=user_id,
                    ip_address=ip_address,
                    details={'error': str(e)}
                )
                raise

        return decorated
    return decorator


def sanitize_login_response(user_dict: dict) -> dict:
    """Remove sensitive fields from login response"""
    sensitive_fields = ['password_hash', 'is_locked', 'locked_until']
    for field in sensitive_fields:
        user_dict.pop(field, None)
    return user_dict
