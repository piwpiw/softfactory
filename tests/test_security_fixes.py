"""Comprehensive security tests for authentication and rate limiting"""
import pytest
from datetime import datetime, timedelta
from flask import json
from backend.models import User, LoginAttempt
from backend.password_validator import PasswordValidator
from backend.security_middleware import LoginAttemptTracker, SecurityEventLogger


class TestPasswordValidator:
    """Test password strength validation"""

    def test_password_minimum_length(self):
        """Password must be at least 8 characters"""
        is_valid, msg = PasswordValidator.validate("Short1!")
        assert not is_valid
        assert "8 characters" in msg

    def test_password_requires_uppercase(self):
        """Password must contain uppercase letter"""
        is_valid, msg = PasswordValidator.validate("password1!")
        assert not is_valid
        assert "uppercase" in msg.lower()

    def test_password_requires_digit(self):
        """Password must contain digit"""
        is_valid, msg = PasswordValidator.validate("Password!")
        assert not is_valid
        assert "digit" in msg.lower()

    def test_password_requires_special_char(self):
        """Password must contain special character"""
        is_valid, msg = PasswordValidator.validate("Password1")
        assert not is_valid
        assert "special character" in msg.lower()

    def test_password_valid_strong(self):
        """Valid strong password"""
        is_valid, msg = PasswordValidator.validate("SecurePass123!")
        assert is_valid
        assert msg == ""

    def test_password_rejects_common_patterns(self):
        """Reject common weak passwords"""
        weak_passwords = [
            "Password123!",  # too common
            "Qwerty123!",    # qwerty
            "Abc123456!",    # abc123
            "Admin@123",     # contains 'admin' pattern
        ]
        for pwd in weak_passwords:
            is_valid, msg = PasswordValidator.validate(pwd)
            # Most should be rejected or flagged
            assert not is_valid or "common" in msg.lower()

    def test_password_requirements_returned(self):
        """Get password requirements for API"""
        reqs = PasswordValidator.get_requirements()
        assert reqs['min_length'] == 8
        assert reqs['require_uppercase'] is True
        assert reqs['require_digit'] is True
        assert reqs['require_special'] is True
        assert len(reqs['special_chars']) > 0


class TestRegisterWithPasswordPolicy:
    """Test registration with password validation"""

    def test_register_with_weak_password(self, client, app):
        """Registration fails with weak password"""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@test.com',
            'name': 'Test User',
            'password': 'weak'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'requirements' in data

    def test_register_with_strong_password(self, client, app):
        """Registration succeeds with strong password"""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@test.com',
            'name': 'Test User',
            'password': 'SecurePass123!'
        })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'user' in data
        assert data['user']['email'] == 'newuser@test.com'


class TestDemoTokenBypass:
    """Test that demo token hardcoding vulnerability is fixed"""

    def test_demo_token_rejected(self, client):
        """Demo token no longer bypasses authentication"""
        response = client.get(
            '/api/auth/me',
            headers={'Authorization': 'Bearer demo_token'}
        )
        # Should be rejected, not accepted
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

    def test_valid_jwt_required(self, client, app):
        """Only valid JWT tokens are accepted"""
        # First login to get valid token
        client.post('/api/auth/register', json={
            'email': 'user@test.com',
            'name': 'Test',
            'password': 'SecurePass123!'
        })

        response = client.post('/api/auth/login', json={
            'email': 'user@test.com',
            'password': 'SecurePass123!'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        token = data['access_token']

        # Valid token works
        response = client.get(
            '/api/auth/me',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting on login endpoint"""

    def test_rate_limit_after_5_failures(self, client, app):
        """Rate limiting kicks in after 5 failed attempts"""
        email = 'ratelimit@test.com'

        # Make 5 failed login attempts
        for i in range(5):
            response = client.post('/api/auth/login', json={
                'email': email,
                'password': 'WrongPassword123!'
            })
            assert response.status_code == 401 or response.status_code == 403

        # 6th attempt should be rate limited
        response = client.post('/api/auth/login', json={
            'email': email,
            'password': 'WrongPassword123!'
        })
        assert response.status_code == 429
        data = json.loads(response.data)
        assert 'error' in data
        assert 'RATE_LIMITED' in data.get('error_code', '')

    def test_rate_limit_with_correct_password(self, client, app):
        """Correct password is attempted after rate limit"""
        email = 'user@rate.com'

        # Register valid user
        client.post('/api/auth/register', json={
            'email': email,
            'name': 'Test',
            'password': 'ValidPass123!'
        })

        # Make 5 failed attempts
        for i in range(5):
            response = client.post('/api/auth/login', json={
                'email': email,
                'password': 'WrongPassword123!'
            })

        # Should be locked regardless of correct password
        response = client.post('/api/auth/login', json={
            'email': email,
            'password': 'ValidPass123!'
        })
        # Either locked or rate limited
        assert response.status_code in [403, 429]


class TestAccountLockout:
    """Test account lockout mechanism"""

    def test_account_locks_after_5_failures(self, client, app):
        """Account locks after 5 failed login attempts"""
        email = 'lockout@test.com'

        # Register user
        client.post('/api/auth/register', json={
            'email': email,
            'name': 'Test',
            'password': 'ValidPass123!'
        })

        # Make 5 failed attempts
        for i in range(5):
            response = client.post('/api/auth/login', json={
                'email': email,
                'password': 'WrongPassword123!'
            })

        # Check user is locked in database
        user = User.query.filter_by(email=email).first()
        assert user.is_locked is True
        assert user.locked_until is not None

    def test_locked_account_cannot_login(self, client, app):
        """Locked account cannot login even with correct password"""
        email = 'locked@test.com'

        # Register and lock user
        client.post('/api/auth/register', json={
            'email': email,
            'name': 'Test',
            'password': 'ValidPass123!'
        })

        for i in range(5):
            client.post('/api/auth/login', json={
                'email': email,
                'password': 'Wrong123!'
            })

        # Try with correct password - should still be locked
        response = client.post('/api/auth/login', json={
            'email': email,
            'password': 'ValidPass123!'
        })
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'ACCOUNT_LOCKED' in data.get('error_code', '')

    def test_account_unlocks_after_timeout(self, app):
        """Account unlocks after lockout duration expires"""
        # Create and lock user
        user = User(email='unlock@test.com', name='Test')
        user.set_password('ValidPass123!')
        user.is_locked = True
        user.locked_until = datetime.utcnow() - timedelta(minutes=1)  # Already expired
        from backend.models import db
        db.session.add(user)
        db.session.commit()

        # Check if unlocked
        is_locked = LoginAttemptTracker.is_account_locked(user)
        assert is_locked is False
        assert user.is_locked is False


class TestLoginAttemptTracking:
    """Test login attempt recording and tracking"""

    def test_failed_attempt_recorded(self, app):
        """Failed login attempt is recorded"""
        email = 'tracked@test.com'

        attempt = LoginAttemptTracker.record_attempt(email, success=False)
        assert attempt.email == email
        assert attempt.success is False
        assert attempt.timestamp is not None

    def test_successful_attempt_recorded(self, app):
        """Successful login attempt is recorded"""
        email = 'tracked@test.com'

        attempt = LoginAttemptTracker.record_attempt(email, success=True)
        assert attempt.email == email
        assert attempt.success is True

    def test_get_recent_attempts(self, app):
        """Get recent login attempts"""
        email = 'tracked@test.com'

        for i in range(3):
            LoginAttemptTracker.record_attempt(email, success=False)

        recent = LoginAttemptTracker.get_recent_attempts(email, minutes=1)
        assert len(recent) == 3

    def test_failed_count_in_window(self, app):
        """Count failed attempts in time window"""
        email = 'tracked@test.com'

        for i in range(3):
            LoginAttemptTracker.record_attempt(email, success=False)

        count = LoginAttemptTracker.get_failed_attempt_count(email, minutes=1)
        assert count == 3

    def test_clear_attempts(self, app):
        """Clear login attempts"""
        email = 'tracked@test.com'

        for i in range(3):
            LoginAttemptTracker.record_attempt(email, success=False)

        LoginAttemptTracker.clear_attempts(email)

        count = LoginAttemptTracker.get_failed_attempt_count(email, minutes=1)
        assert count == 0


class TestSecurityEventLogging:
    """Test security event logging"""

    def test_login_success_logged(self, app):
        """Successful login is logged"""
        user_id = 1
        email = 'logged@test.com'

        event = SecurityEventLogger.log_event('LOGIN_SUCCESS', user_id=user_id, email=email)
        assert event['event_type'] == 'LOGIN_SUCCESS'
        assert event['user_id'] == user_id
        assert event['email'] == email
        assert 'timestamp' in event

    def test_failed_login_logged(self, app):
        """Failed login is logged"""
        email = 'failed@test.com'
        ip = '192.168.1.1'

        event = SecurityEventLogger.log_event('LOGIN_FAILED', email=email, ip_address=ip)
        assert event['event_type'] == 'LOGIN_FAILED'
        assert event['email'] == email
        assert event['ip_address'] == ip

    def test_account_locked_logged(self, app):
        """Account lockout is logged"""
        user_id = 1

        event = SecurityEventLogger.log_event(
            'ACCOUNT_LOCKED',
            user_id=user_id,
            details={'duration_minutes': 15}
        )
        assert event['event_type'] == 'ACCOUNT_LOCKED'
        assert event['details']['duration_minutes'] == 15


class TestSubscriptionLockout:
    """Test that subscription bypass is fixed"""

    def test_subscription_requires_valid_subscription(self, client, app):
        """Subscription check requires actual database record"""
        # Register user
        response = client.post('/api/auth/register', json={
            'email': 'sub@test.com',
            'name': 'Test',
            'password': 'ValidPass123!'
        })
        data = json.loads(response.data)
        token = data['access_token']

        # Try to access subscription-only endpoint without subscription
        response = client.get(
            '/api/coocook/bookings',
            headers={'Authorization': f'Bearer {token}'}
        )
        # Should fail - no subscription
        assert response.status_code == 403


class TestSensitiveDataRemoval:
    """Test that sensitive data is not exposed in responses"""

    def test_login_response_no_password_hash(self, client, app):
        """Login response doesn't expose password hash"""
        response = client.post('/api/auth/register', json={
            'email': 'safe@test.com',
            'name': 'Test',
            'password': 'ValidPass123!'
        })
        data = json.loads(response.data)

        assert 'password_hash' not in data['user']
        assert 'is_locked' not in data['user']
        assert 'locked_until' not in data['user']

    def test_login_no_sensitive_fields(self, client, app):
        """Login response doesn't expose sensitive fields"""
        client.post('/api/auth/register', json={
            'email': 'test@test.com',
            'name': 'Test',
            'password': 'ValidPass123!'
        })

        response = client.post('/api/auth/login', json={
            'email': 'test@test.com',
            'password': 'ValidPass123!'
        })
        data = json.loads(response.data)

        user_data = data['user']
        assert 'password_hash' not in user_data
        assert 'is_locked' not in user_data
        assert 'locked_until' not in user_data
