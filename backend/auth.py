"""JWT Authentication and Decorators"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
import jwt
import os
from functools import wraps
from .models import db, User, Subscription, Product
from .password_validator import PasswordValidator
from .security_middleware import (
    LoginAttemptTracker, SecurityEventLogger, require_rate_limit,
    log_security_event_decorator, sanitize_login_response
)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

SECRET_KEY = os.getenv('PLATFORM_SECRET_KEY', 'softfactory-dev-secret-key-2026')
ACCESS_TOKEN_EXPIRE = timedelta(hours=1)
REFRESH_TOKEN_EXPIRE = timedelta(days=30)


def create_tokens(user_id, user_role):
    """Create access and refresh tokens"""
    now = datetime.utcnow()

    access_payload = {
        'user_id': user_id,
        'role': user_role,
        'exp': now + ACCESS_TOKEN_EXPIRE,
        'type': 'access'
    }

    refresh_payload = {
        'user_id': user_id,
        'exp': now + REFRESH_TOKEN_EXPIRE,
        'type': 'refresh'
    }

    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256')

    return access_token, refresh_token


def verify_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Decorator to require authentication (SECURITY: Demo token removed in v2.0)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing authorization header'}), 401

        token = auth_header[7:]

        # SECURITY FIX: Removed hardcoded demo token bypass (CVSS 9.8)
        # All authentication now goes through JWT verification
        payload = verify_token(token)

        if not payload or payload.get('type') != 'access':
            return jsonify({'error': 'Invalid or expired token'}), 401

        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401

        g.user_id = user.id
        g.user_role = user.role
        g.user = user

        return f(*args, **kwargs)

    return decorated


def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'user_role') or g.user_role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)

    return decorated


def require_subscription(product_slug):
    """Decorator to require subscription to a specific product"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # SECURITY FIX: Removed demo user bypass (CVSS 9.8)
            # All subscription checks now verified against database
            product = Product.query.filter_by(slug=product_slug).first()
            if not product:
                return jsonify({'error': 'Product not found'}), 404

            subscription = Subscription.query.filter_by(
                user_id=g.user_id,
                product_id=product.id,
                status='active'
            ).first()

            if not subscription:
                return jsonify({'error': f'Subscription to {product_slug} required'}), 403

            return f(*args, **kwargs)

        return decorated

    return decorator


# ============ ENDPOINTS ============

@auth_bp.route('/register', methods=['POST'])
@require_rate_limit
@log_security_event_decorator('USER_REGISTRATION')
def register():
    """Register new user with password validation"""
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Missing required fields'}), 400

    # SECURITY FIX: Enforce password policy (CVSS 8.6)
    password_valid, error_msg = PasswordValidator.validate(data['password'])
    if not password_valid:
        return jsonify({
            'error': error_msg,
            'requirements': PasswordValidator.get_requirements()
        }), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    user = User(email=data['email'], name=data['name'])
    user.set_password(data['password'])
    user.password_changed_at = datetime.utcnow()

    db.session.add(user)
    db.session.commit()

    access_token, refresh_token = create_tokens(user.id, user.role)

    SecurityEventLogger.log_event('USER_REGISTERED', user_id=user.id, email=user.email)

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
@require_rate_limit
def login():
    """Login user with rate limiting and account lockout"""
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400

    email = data['email']
    user = User.query.filter_by(email=email).first()

    # SECURITY FIX: Account lockout mechanism (CVSS 7.5)
    if user and LoginAttemptTracker.is_account_locked(user):
        SecurityEventLogger.log_event('LOGIN_ATTEMPT_LOCKED_ACCOUNT', email=email)
        minutes_left = (user.locked_until - datetime.utcnow()).seconds // 60
        return jsonify({
            'error': f'Account locked due to too many failed attempts. Try again in {minutes_left} minutes.',
            'error_code': 'ACCOUNT_LOCKED'
        }), 403

    # Authenticate user
    if not user or not user.check_password(data['password']):
        # Record failed attempt
        LoginAttemptTracker.record_attempt(email, success=False)

        failed_count = LoginAttemptTracker.get_failed_attempt_count(email, minutes=1)
        remaining = max(0, 5 - failed_count)

        if user and failed_count >= 5:
            # SECURITY FIX: Lock account after 5 failures (CVSS 7.5)
            LoginAttemptTracker.lock_account(user, duration_minutes=15)
            return jsonify({
                'error': 'Account locked due to too many failed login attempts. Try again in 15 minutes.',
                'error_code': 'ACCOUNT_LOCKED'
            }), 403

        SecurityEventLogger.log_event('LOGIN_FAILED', email=email, details={'remaining_attempts': remaining})
        return jsonify({
            'error': 'Invalid email or password',
            'attempts_remaining': remaining
        }), 401

    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 403

    # Successful login - clear failed attempts
    LoginAttemptTracker.record_attempt(email, success=True)
    LoginAttemptTracker.clear_attempts(email)

    access_token, refresh_token = create_tokens(user.id, user.role)

    SecurityEventLogger.log_event('LOGIN_SUCCESS', user_id=user.id, email=email)

    user_dict = user.to_dict()
    user_dict = sanitize_login_response(user_dict)

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user_dict
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token"""
    data = request.get_json()

    if not data or not data.get('refresh_token'):
        return jsonify({'error': 'Missing refresh token'}), 400

    payload = verify_token(data['refresh_token'])

    if not payload or payload.get('type') != 'refresh':
        return jsonify({'error': 'Invalid refresh token'}), 401

    user = User.query.get(payload['user_id'])
    if not user or not user.is_active:
        return jsonify({'error': 'User not found or inactive'}), 401

    access_token, new_refresh_token = create_tokens(user.id, user.role)

    return jsonify({
        'access_token': access_token,
        'refresh_token': new_refresh_token
    }), 200


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_me():
    """Get current user info"""
    return jsonify(g.user.to_dict()), 200
