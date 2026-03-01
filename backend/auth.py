"""JWT Authentication and Decorators — Security-Hardened"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
import jwt
import os
import time
import threading
import secrets
from functools import wraps
from werkzeug.security import generate_password_hash
from .models import db, User, Subscription, Payment, Product
from .rate_limiter import rate_limit, get_limiter, get_client_ip
from .input_validator import (
    validate_email, validate_password, validate_string, sanitize_html,
    validate_request_data
)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

SECRET_KEY = os.getenv('PLATFORM_SECRET_KEY', 'softfactory-dev-secret-key-2026')
ACCESS_TOKEN_EXPIRE = timedelta(hours=1)
REFRESH_TOKEN_EXPIRE = timedelta(days=30)


# === JWT Token Blacklist ===
# In-memory token blacklist with automatic expiry cleanup.
# In production, use Redis for multi-process/multi-server deployments.

class TokenBlacklist:
    """Thread-safe in-memory JWT token blacklist with auto-expiry."""

    def __init__(self):
        self._blacklist: dict[str, float] = {}  # token_jti -> expiry_timestamp
        self._lock = threading.Lock()
        self._cleanup_interval = 600  # Clean up every 10 minutes
        self._last_cleanup = time.time()

    def revoke(self, token_jti: str, expires_at: float):
        """Add a token to the blacklist.

        Args:
            token_jti: Unique token identifier (we use the token string itself for simplicity)
            expires_at: Unix timestamp when the token naturally expires
        """
        with self._lock:
            self._blacklist[token_jti] = expires_at
            self._maybe_cleanup()

    def is_revoked(self, token_jti: str) -> bool:
        """Check if a token has been revoked."""
        with self._lock:
            return token_jti in self._blacklist

    def _maybe_cleanup(self):
        """Remove expired tokens from blacklist to prevent memory growth."""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            expired_keys = [k for k, exp in self._blacklist.items() if exp < now]
            for k in expired_keys:
                del self._blacklist[k]
            self._last_cleanup = now


# Global blacklist singleton
_token_blacklist = TokenBlacklist()


def create_tokens(user_id, user_role):
    """Create access and refresh tokens with secure claims"""
    now = datetime.utcnow()

    access_payload = {
        'user_id': user_id,
        'role': user_role,
        'exp': now + ACCESS_TOKEN_EXPIRE,
        'iat': now,
        'type': 'access'
    }

    refresh_payload = {
        'user_id': user_id,
        'exp': now + REFRESH_TOKEN_EXPIRE,
        'iat': now,
        'type': 'refresh'
    }

    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256')

    return access_token, refresh_token


def verify_token(token):
    """Verify and decode JWT token, checking blacklist"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        # Check if token has been revoked
        if _token_blacklist.is_revoked(token):
            return None

        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def revoke_token(token):
    """Revoke a JWT token by adding it to the blacklist.

    Args:
        token: The raw JWT token string to revoke
    """
    try:
        # Decode without verification to get expiry (token may already be expired)
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'],
                             options={'verify_exp': False})
        exp = payload.get('exp', 0)
        # Convert datetime-based exp to unix timestamp if needed
        if isinstance(exp, (int, float)):
            expires_at = float(exp)
        else:
            expires_at = time.time() + 3600  # Default 1 hour
        _token_blacklist.revoke(token, expires_at)
    except jwt.InvalidTokenError:
        # If we can't decode, blacklist with a default 1-hour expiry
        _token_blacklist.revoke(token, time.time() + 3600)


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing authorization header'}), 401

        token = auth_header[7:]

        # Demo mode support
        if token == 'demo_token':
            # Set mock user data for demo mode
            g.user_id = 1  # Demo user ID
            g.user_role = 'user'
            class DemoUser:
                id = 1
                email = 'demo@softfactory.com'
                name = 'Demo User'
                role = 'user'
                is_active = True
                def to_dict(self):
                    return {
                        'id': 1,
                        'email': 'demo@softfactory.com',
                        'name': 'Demo User',
                        'role': 'user'
                    }
            g.user = DemoUser()
            return f(*args, **kwargs)

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
            # Demo mode: allow all subscriptions for demo users
            if g.user_id == 1:  # Demo user ID
                return f(*args, **kwargs)

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
@rate_limit(max_requests=10, window_seconds=60, key_func='ip',
            error_message='Too many registration attempts. Please try again later.')
def register():
    """Register new user — with input validation and rate limiting"""
    data = request.get_json()

    # Validate all input fields
    errors = validate_request_data(data, {
        'email': {'type': 'email', 'required': True},
        'password': {'type': 'password', 'required': True, 'min_length': 8, 'max_length': 128},
        'name': {'type': 'string', 'required': True, 'min_length': 1, 'max_length': 120},
    })

    if errors:
        return jsonify({'error': errors[0], 'errors': errors}), 400

    # Sanitize name
    clean_email = data['email'].strip().lower()
    clean_name = sanitize_html(data['name'].strip())

    if User.query.filter_by(email=clean_email).first():
        return jsonify({'error': 'Email already registered'}), 400

    user = User(email=clean_email, name=clean_name)
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    access_token, refresh_token = create_tokens(user.id, user.role)

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=60, key_func='ip',
            error_message='Too many login attempts. Please try again in 1 minute.')
def login():
    """Login user — with rate limiting (5 attempts/min per IP) and input validation"""
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400

    # Basic input validation (don't reveal whether email format is wrong)
    email = data['email'].strip().lower() if isinstance(data.get('email'), str) else ''
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400

    # Check for SQL injection in email
    from .input_validator import check_sql_injection
    if check_sql_injection(email):
        return jsonify({'error': 'Invalid email or password'}), 401

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 403

    # Check account lockout (if fields exist)
    if hasattr(user, 'is_locked') and user.is_locked:
        if hasattr(user, 'locked_until') and user.locked_until:
            if datetime.utcnow() < user.locked_until:
                return jsonify({'error': 'Account temporarily locked. Try again later.'}), 423
            else:
                # Lockout expired, unlock
                user.is_locked = False
                user.locked_until = None

    # Successful login - reset rate limit for this IP on this endpoint
    limiter = get_limiter()
    limiter.reset(f"ip:{get_client_ip()}")

    access_token, refresh_token = create_tokens(user.id, user.role)

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=60, key_func='ip',
            error_message='Too many refresh requests. Please try again later.')
def refresh():
    """Refresh access token — revokes old refresh token"""
    data = request.get_json()

    if not data or not data.get('refresh_token'):
        return jsonify({'error': 'Missing refresh token'}), 400

    old_refresh_token = data['refresh_token']
    payload = verify_token(old_refresh_token)

    if not payload or payload.get('type') != 'refresh':
        return jsonify({'error': 'Invalid refresh token'}), 401

    user = User.query.get(payload['user_id'])
    if not user or not user.is_active:
        return jsonify({'error': 'User not found or inactive'}), 401

    # Revoke the old refresh token (rotation)
    revoke_token(old_refresh_token)

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


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user — revokes the current access token"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        if token != 'demo_token':  # Don't blacklist the demo token
            revoke_token(token)

    # Also revoke refresh token if provided
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')
    if refresh_token:
        revoke_token(refresh_token)

    return jsonify({'message': 'Logged out successfully'}), 200


# ============ GDPR / DATA RIGHTS ENDPOINTS ============

@auth_bp.route('/account', methods=['DELETE'])
@rate_limit(max_requests=3, window_seconds=3600, key_func='ip',
            error_message='Too many account deletion attempts. Please try again later.')
@require_auth
def delete_account():
    """GDPR Article 17 — Right to Erasure (Right to be Forgotten).

    Soft-deletes the user account: anonymises all personal data while
    retaining anonymised transaction records for legal/accounting requirements.

    Request body (JSON):
        password (str): Current password confirmation (required for non-OAuth users)

    Returns:
        200: Account successfully deleted with confirmation message
        400: Missing password
        401: Wrong password or unauthenticated
        403: Demo account cannot be deleted
    """
    # Block demo account deletion
    if g.user_id == 1:
        return jsonify({'error': 'Demo account cannot be deleted.'}), 403

    user = g.user

    # Require password confirmation for password-based accounts
    # OAuth-only users (no usable password) bypass this check
    is_oauth_only = bool(user.oauth_provider and not user.password_hash.startswith('pbkdf2'))
    if not is_oauth_only:
        data = request.get_json() or {}
        password = data.get('password', '')
        if not password:
            return jsonify({'error': 'Password confirmation is required to delete your account.'}), 400
        if not user.check_password(password):
            return jsonify({'error': 'Incorrect password. Account deletion cancelled.'}), 401

    # Cancel any active Stripe subscriptions
    active_subscriptions = Subscription.query.filter_by(
        user_id=user.id, status='active'
    ).all()

    stripe_errors = []
    for sub in active_subscriptions:
        if sub.stripe_subscription_id:
            try:
                import stripe
                stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
                stripe.Subscription.delete(sub.stripe_subscription_id)
            except Exception as e:
                stripe_errors.append(str(e))
        sub.status = 'canceled'

    # Anonymise personal data (soft delete — preserves referential integrity)
    anon_id = f'deleted_{secrets.token_hex(8)}'
    user.email = f'{anon_id}@deleted.invalid'
    user.name = '삭제된 사용자'
    user.password_hash = generate_password_hash(secrets.token_urlsafe(32))
    user.oauth_provider = None
    user.oauth_id = None
    user.avatar_url = None
    user.is_active = False
    user.is_locked = True

    # Revoke the current access token so the session ends immediately
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        revoke_token(auth_header[7:])

    db.session.commit()

    # TODO: Send account deletion confirmation email via EMAIL_PROVIDER
    # send_deletion_confirmation(original_email)

    response_body = {
        'message': '계정이 삭제되었습니다. 이용해 주셔서 감사합니다.',
        'deleted_at': datetime.utcnow().isoformat(),
    }
    if stripe_errors:
        response_body['warnings'] = [
            '일부 구독 취소 중 오류가 발생했습니다. 고객센터에 문의해 주세요.'
        ]

    return jsonify(response_body), 200


@auth_bp.route('/data-export', methods=['GET'])
@rate_limit(max_requests=5, window_seconds=3600, key_func='ip',
            error_message='Too many data export requests. Please wait before requesting again.')
@require_auth
def data_export():
    """GDPR Article 20 — Right to Data Portability.

    Returns all personal data held for the current user as a JSON export.
    Transaction records are included as required by law.

    Returns:
        200: JSON object with all user data
        403: Demo account cannot export data via this endpoint
    """
    if g.user_id == 1:
        return jsonify({'error': 'Data export is not available for the demo account.'}), 403

    user = g.user

    # ---- Profile ----
    profile = {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'oauth_provider': user.oauth_provider,
        'avatar_url': user.avatar_url,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'is_active': user.is_active,
    }

    # ---- Subscriptions ----
    subscriptions = []
    for sub in Subscription.query.filter_by(user_id=user.id).all():
        subscriptions.append({
            'id': sub.id,
            'product_id': sub.product_id,
            'plan_type': sub.plan_type,
            'status': sub.status,
            'created_at': sub.created_at.isoformat() if sub.created_at else None,
            'current_period_end': (
                sub.current_period_end.isoformat() if sub.current_period_end else None
            ),
        })

    # ---- Payment history ----
    payments = []
    for pay in Payment.query.filter_by(user_id=user.id).all():
        payments.append({
            'id': pay.id,
            'product_id': pay.product_id,
            'amount': pay.amount,
            'currency': pay.currency,
            'status': pay.status,
            'created_at': pay.created_at.isoformat() if pay.created_at else None,
        })

    # ---- SNS accounts ----
    sns_accounts = []
    try:
        from .models import SNSAccount
        for acct in SNSAccount.query.filter_by(user_id=user.id).all():
            sns_accounts.append({
                'id': acct.id,
                'platform': getattr(acct, 'platform', None),
                'username': getattr(acct, 'username', None),
                'created_at': (
                    acct.created_at.isoformat()
                    if getattr(acct, 'created_at', None)
                    else None
                ),
            })
    except Exception:
        pass

    # ---- SNS posts ----
    sns_posts = []
    try:
        from .models import SNSPost
        for post in SNSPost.query.filter_by(user_id=user.id).all():
            sns_posts.append({
                'id': post.id,
                'content': getattr(post, 'content', None),
                'platform': getattr(post, 'platform', None),
                'status': getattr(post, 'status', None),
                'created_at': (
                    post.created_at.isoformat()
                    if getattr(post, 'created_at', None)
                    else None
                ),
            })
    except Exception:
        pass

    # ---- Review campaign applications ----
    campaign_applications = []
    try:
        from .models import CampaignApplication
        for app_obj in CampaignApplication.query.filter_by(user_id=user.id).all():
            campaign_applications.append({
                'id': app_obj.id,
                'campaign_id': getattr(app_obj, 'campaign_id', None),
                'status': getattr(app_obj, 'status', None),
                'created_at': (
                    app_obj.created_at.isoformat()
                    if getattr(app_obj, 'created_at', None)
                    else None
                ),
            })
    except Exception:
        pass

    # ---- Bookings (CooCook) ----
    bookings = []
    try:
        from .models import Booking
        for booking in Booking.query.filter_by(user_id=user.id).all():
            bookings.append({
                'id': booking.id,
                'chef_id': booking.chef_id,
                'booking_date': (
                    booking.booking_date.isoformat()
                    if getattr(booking, 'booking_date', None)
                    else None
                ),
                'status': booking.status,
                'total_price': booking.total_price,
                'created_at': (
                    booking.created_at.isoformat()
                    if getattr(booking, 'created_at', None)
                    else None
                ),
            })
    except Exception:
        pass

    export = {
        'export_generated_at': datetime.utcnow().isoformat(),
        'data_controller': 'SoftFactory (소프트팩토리)',
        'legal_basis': 'GDPR Article 20 — Right to Data Portability / 개인정보보호법 제35조',
        'profile': profile,
        'subscriptions': subscriptions,
        'payment_history': payments,
        'sns_accounts': sns_accounts,
        'sns_posts': sns_posts,
        'campaign_applications': campaign_applications,
        'bookings': bookings,
    }

    from flask import make_response
    import json
    response = make_response(
        json.dumps(export, ensure_ascii=False, indent=2),
        200
    )
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = (
        f'attachment; filename="softfactory-data-export-{user.id}.json"'
    )
    return response


# ============ OAUTH ENDPOINTS ============

from .oauth import OAuthProvider

@auth_bp.route('/oauth/<provider>/url', methods=['GET'])
def oauth_auth_url(provider):
    """Get OAuth authorization URL"""
    from .models import SNSOAuthState
    state = OAuthProvider.generate_state_token()

    # Get provider-specific redirect URI
    env_key = f'{provider.upper()}_REDIRECT_URI'
    redirect_uri = os.getenv(env_key, f'http://localhost:9000/api/auth/oauth/{provider}/callback')

    result = OAuthProvider.get_auth_url(provider, state, redirect_uri)

    if 'error' not in result:
        try:
            oauth_state = SNSOAuthState(provider=provider, state=state, created_at=datetime.utcnow())
            db.session.add(oauth_state)
            db.session.commit()
        except:
            pass

    return jsonify(result), 200 if 'error' not in result else 400


@auth_bp.route('/oauth/<provider>/callback', methods=['POST'])
def oauth_callback(provider):
    """Handle OAuth callback"""
    data = request.get_json()
    code = data.get('code')
    state = data.get('state')

    if not code:
        return jsonify({'error': 'Missing authorization code'}), 400

    # Get provider-specific redirect URI
    env_key = f'{provider.upper()}_REDIRECT_URI'
    redirect_uri = os.getenv(env_key, f'http://localhost:9000/api/auth/oauth/{provider}/callback')

    token_result = OAuthProvider.exchange_code_for_token(provider, code, redirect_uri)

    if 'error' in token_result:
        return jsonify(token_result), 400

    # Get user info
    userinfo = OAuthProvider.get_user_info(provider, token_result['access_token'])

    if 'error' in userinfo:
        return jsonify(userinfo), 400

    # Find or create user
    email = userinfo.get('email') or f"{provider}_{userinfo.get('id')}"
    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            email=email,
            name=userinfo.get('name', 'Social User'),
            oauth_provider=provider,
            oauth_id=userinfo.get('id'),
            avatar_url=userinfo.get('picture')
        )
        # Set a random password for OAuth users (they won't use it)
        import secrets
        user.set_password(secrets.token_urlsafe(32))
        db.session.add(user)
    else:
        user.oauth_provider = provider
        user.oauth_id = userinfo.get('id')
        user.avatar_url = userinfo.get('picture')

    user.is_active = True
    db.session.commit()

    # Generate tokens
    access_token, refresh_token = create_tokens(user.id, user.role)

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


# ============ EMAIL VERIFICATION & PASSWORD RESET ============

import secrets as _secrets

_VERIFICATION_EXPIRE_HOURS = 24
_RESET_EXPIRE_HOURS = 1


def _get_email_service():
    """Lazy-import to avoid circular dependency at module load."""
    try:
        from .services.email_service import get_email_service
        return get_email_service()
    except Exception as exc:
        import logging
        logging.getLogger('auth').error('EmailService unavailable: %s', exc)
        return None


@auth_bp.route('/send-verification', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=300, key_func='ip',
            error_message='Too many verification requests. Please wait 5 minutes.')
@require_auth
def send_verification():
    """Send (or re-send) a 6-digit email-verification code to the current user."""
    user = g.user

    if getattr(user, 'id', None) == 1:
        return jsonify({'message': 'Demo user does not require verification'}), 200

    if getattr(user, 'email_verified', False):
        return jsonify({'message': 'Email is already verified'}), 200

    try:
        code = str(_secrets.randbelow(900000) + 100000)
        user.verification_token = code
        user.verification_token_expires = datetime.utcnow() + timedelta(hours=_VERIFICATION_EXPIRE_HOURS)
        db.session.commit()
    except Exception as exc:
        import logging
        logging.getLogger('auth').error('Failed to save verification token: %s', exc)
        return jsonify({'error': 'Failed to generate verification code'}), 500

    svc = _get_email_service()
    if svc:
        svc.send_verification_email(user.email, user.name, code)

    return jsonify({'message': 'Verification email sent'}), 200


@auth_bp.route('/verify-email', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=300, key_func='ip',
            error_message='Too many verification attempts. Please wait 5 minutes.')
def verify_email():
    """Verify email with the 6-digit token. Body: {token} or {email, token}"""
    data = request.get_json() or {}
    token = str(data.get('token', '')).strip()
    email = str(data.get('email', '')).strip().lower()

    if not token:
        return jsonify({'error': 'Verification token is required'}), 400

    if email:
        user = User.query.filter_by(email=email).first()
    else:
        user = User.query.filter_by(verification_token=token).first()

    if not user:
        return jsonify({'error': 'Invalid or expired verification token'}), 400

    if getattr(user, 'email_verified', False):
        return jsonify({'message': 'Email is already verified'}), 200

    stored_token = getattr(user, 'verification_token', None)
    expires = getattr(user, 'verification_token_expires', None)

    if not stored_token or stored_token != token:
        return jsonify({'error': 'Invalid verification token'}), 400

    if expires and datetime.utcnow() > expires:
        return jsonify({'error': 'Verification token has expired. Please request a new one.'}), 400

    try:
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        db.session.commit()
    except Exception as exc:
        import logging
        logging.getLogger('auth').error('Failed to update email_verified: %s', exc)
        return jsonify({'error': 'Verification failed. Please try again.'}), 500

    return jsonify({'message': 'Email verified successfully'}), 200


@auth_bp.route('/resend-verification', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=300, key_func='ip',
            error_message='Too many resend requests. Please wait 5 minutes.')
def resend_verification():
    """Resend verification email. Body: {email}"""
    data = request.get_json() or {}
    email = str(data.get('email', '')).strip().lower()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()
    if user and not getattr(user, 'email_verified', False):
        try:
            code = str(_secrets.randbelow(900000) + 100000)
            user.verification_token = code
            user.verification_token_expires = datetime.utcnow() + timedelta(hours=_VERIFICATION_EXPIRE_HOURS)
            db.session.commit()
            svc = _get_email_service()
            if svc:
                svc.send_verification_email(user.email, user.name, code)
        except Exception as exc:
            import logging
            logging.getLogger('auth').error('resend_verification error: %s', exc)

    return jsonify({'message': 'If the email exists and is unverified, a new code has been sent'}), 200


@auth_bp.route('/forgot-password', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=300, key_func='ip',
            error_message='Too many password reset requests. Please wait 5 minutes.')
def forgot_password():
    """Send a password-reset link. Body: {email}"""
    data = request.get_json() or {}
    email = str(data.get('email', '')).strip().lower()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    user = User.query.filter_by(email=email).first()
    if user and user.is_active:
        try:
            reset_tok = _secrets.token_urlsafe(32)
            user.reset_token = reset_tok
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=_RESET_EXPIRE_HOURS)
            db.session.commit()
            svc = _get_email_service()
            if svc:
                svc.send_password_reset_email(user.email, user.name, reset_tok)
        except Exception as exc:
            import logging
            logging.getLogger('auth').error('forgot_password error: %s', exc)

    return jsonify({'message': 'If that email is registered, a reset link has been sent'}), 200


@auth_bp.route('/reset-password', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=300, key_func='ip',
            error_message='Too many reset attempts. Please wait 5 minutes.')
def reset_password():
    """Set a new password using a valid reset token. Body: {token, password}"""
    data = request.get_json() or {}
    token = str(data.get('token', '')).strip()
    new_password = data.get('password', '')

    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required'}), 400

    pw_errors = validate_request_data({'password': new_password}, {
        'password': {'type': 'password', 'required': True, 'min_length': 8, 'max_length': 128},
    })
    if pw_errors:
        return jsonify({'error': pw_errors[0]}), 400

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return jsonify({'error': 'Invalid or expired reset token'}), 400

    expires = getattr(user, 'reset_token_expires', None)
    if expires and datetime.utcnow() > expires:
        return jsonify({'error': 'Reset token has expired. Please request a new one.'}), 400

    try:
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        user.password_changed_at = datetime.utcnow()
        db.session.commit()
    except Exception as exc:
        import logging
        logging.getLogger('auth').error('reset_password error: %s', exc)
        return jsonify({'error': 'Password reset failed. Please try again.'}), 500

    return jsonify({'message': 'Password has been reset successfully'}), 200


# ============ TWO-FACTOR AUTHENTICATION (2FA/TOTP) ============

@auth_bp.route('/2fa/setup', methods=['GET'])
@rate_limit(max_requests=10, window_seconds=60, key_func='ip',
            error_message='Too many 2FA setup requests. Please try again later.')
@require_auth
def setup_2fa():
    """Initialize 2FA setup for the user.

    Returns:
        200: {
            qr_code: base64 PNG image,
            secret: base32 TOTP secret,
            backup_codes: [list of 10 codes],
            expiry_warning: "These codes expire in 24 hours if not confirmed"
        }
    """
    user = g.user

    # Demo user restriction
    if user.id == 1:
        return jsonify({'error': '2FA is not available for demo accounts'}), 403

    # If already enabled, prevent re-setup without disable first
    if getattr(user, 'totp_enabled', False):
        return jsonify({'error': '2FA is already enabled. Disable it first to re-setup.'}), 400

    try:
        from .services.totp_service import get_totp_service
        service = get_totp_service()

        # Generate secret and backup codes
        secret = service.generate_secret()
        backup_codes = service.generate_backup_codes(10)
        qr_code = service.generate_qr_code(secret, user.email)

        # Encrypt and temporarily store backup codes in session/response
        # (Not saved to DB until user confirms)
        encrypted_codes = service.encrypt_backup_codes(backup_codes)

        return jsonify({
            'qr_code': qr_code,
            'secret': secret,
            'backup_codes': backup_codes,  # Show plaintext ONLY during setup
            'encrypted_backup_codes': encrypted_codes,  # For client to send back
            'expiry_warning': 'Please save these codes in a secure location. They expire if not confirmed within 24 hours.'
        }), 200

    except Exception as exc:
        import logging
        logging.getLogger('auth').error('2fa_setup error: %s', exc)
        return jsonify({'error': 'Failed to initialize 2FA setup'}), 500


@auth_bp.route('/2fa/verify-setup', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=300, key_func='ip',
            error_message='Too many 2FA verification attempts. Please wait 5 minutes.')
@require_auth
def verify_2fa_setup():
    """Confirm 2FA setup by verifying TOTP code.

    Body: {
        secret: base32 secret from setup,
        totp_code: 6-digit code from authenticator app,
        encrypted_backup_codes: encrypted codes from setup
    }

    Returns:
        200: {enabled: true, message: "2FA enabled successfully"}
        400: Invalid TOTP code
    """
    user = g.user
    data = request.get_json() or {}

    secret = str(data.get('secret', '')).strip()
    totp_code = str(data.get('totp_code', '')).strip()
    encrypted_codes = str(data.get('encrypted_backup_codes', '')).strip()

    if not secret or not totp_code or not encrypted_codes:
        return jsonify({'error': 'Secret, TOTP code, and backup codes are required'}), 400

    # Validate TOTP code format
    if not totp_code.isdigit() or len(totp_code) != 6:
        return jsonify({'error': 'TOTP code must be 6 digits'}), 400

    try:
        from .services.totp_service import get_totp_service
        service = get_totp_service()

        # Verify TOTP code
        if not service.verify_totp(secret, totp_code):
            return jsonify({'error': 'Invalid TOTP code. Please check your authenticator app.'}), 400

        # Verify backup codes are decryptable
        backup_codes = service.decrypt_backup_codes(encrypted_codes)
        if not backup_codes or len(backup_codes) < 10:
            return jsonify({'error': 'Invalid backup codes'}), 400

        # Save to user
        user.totp_secret = secret
        user.totp_enabled = True
        user.backup_codes = encrypted_codes
        user.backup_codes_used = '[]'  # Initialize as empty
        db.session.commit()

        return jsonify({
            'enabled': True,
            'message': '2FA has been successfully enabled',
            'backup_codes_remaining': 10
        }), 200

    except Exception as exc:
        import logging
        logging.getLogger('auth').error('verify_2fa_setup error: %s', exc)
        return jsonify({'error': 'Failed to enable 2FA'}), 500


@auth_bp.route('/2fa/status', methods=['GET'])
@require_auth
def get_2fa_status():
    """Get current 2FA status for the user.

    Returns:
        200: {
            enabled: boolean,
            backup_codes_remaining: int
        }
    """
    user = g.user

    if user.id == 1:
        return jsonify({'enabled': False, 'backup_codes_remaining': 0}), 200

    try:
        from .services.totp_service import TOTPService
        enabled = getattr(user, 'totp_enabled', False)
        remaining = 0

        if enabled:
            backup_codes = getattr(user, 'backup_codes', '')
            used_codes = getattr(user, 'backup_codes_used', '[]')
            remaining = TOTPService.get_remaining_backup_codes(backup_codes, used_codes)

        return jsonify({
            'enabled': enabled,
            'backup_codes_remaining': remaining
        }), 200

    except Exception as exc:
        import logging
        logging.getLogger('auth').error('get_2fa_status error: %s', exc)
        return jsonify({'error': 'Failed to retrieve 2FA status'}), 500


@auth_bp.route('/2fa/disable', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=300, key_func='ip',
            error_message='Too many 2FA disable attempts. Please wait 5 minutes.')
@require_auth
def disable_2fa():
    """Disable 2FA (requires password confirmation).

    Body: {password: user's password}

    Returns:
        200: {message: "2FA disabled"}
        401: Invalid password
    """
    user = g.user
    data = request.get_json() or {}

    password = data.get('password', '')

    if not password:
        return jsonify({'error': 'Password is required to disable 2FA'}), 400

    # Verify password
    if not user.check_password(password):
        return jsonify({'error': 'Incorrect password'}), 401

    try:
        user.totp_enabled = False
        user.totp_secret = None
        user.backup_codes = None
        user.backup_codes_used = '[]'
        db.session.commit()

        return jsonify({'message': '2FA has been disabled'}), 200

    except Exception as exc:
        import logging
        logging.getLogger('auth').error('disable_2fa error: %s', exc)
        return jsonify({'error': 'Failed to disable 2FA'}), 500


@auth_bp.route('/2fa/verify', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60, key_func='ip',
            error_message='Too many 2FA verification attempts. Please try again in 1 minute.')
def verify_2fa():
    """Verify 2FA code during login.

    Body: {
        email: user email,
        totp_code: 6-digit code (optional if using backup code),
        backup_code: backup code (optional if using TOTP)
    }

    Returns:
        200: {access_token, refresh_token, user}
        400: Missing email
        401: Invalid email or 2FA code
    """
    data = request.get_json() or {}
    email = str(data.get('email', '')).strip().lower()
    totp_code = str(data.get('totp_code', '')).strip()
    backup_code = str(data.get('backup_code', '')).strip()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    if not totp_code and not backup_code:
        return jsonify({'error': 'TOTP code or backup code is required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not getattr(user, 'totp_enabled', False):
        return jsonify({'error': 'Invalid email or 2FA not enabled'}), 401

    try:
        from .services.totp_service import get_totp_service
        service = get_totp_service()

        is_valid = False
        secret = getattr(user, 'totp_secret', '')

        # Try TOTP code first
        if totp_code:
            if totp_code.isdigit() and len(totp_code) == 6:
                is_valid = service.verify_totp(secret, totp_code)
        # Try backup code if TOTP failed or not provided
        elif backup_code:
            backup_codes = getattr(user, 'backup_codes', '')
            used_codes = getattr(user, 'backup_codes_used', '[]')
            is_valid, updated_used = service.verify_backup_code(backup_codes, used_codes, backup_code)

            if is_valid:
                user.backup_codes_used = updated_used
                db.session.commit()

        if not is_valid:
            return jsonify({'error': 'Invalid TOTP code or backup code'}), 401

        # Issue tokens
        access_token, refresh_token = create_tokens(user.id, user.role)

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200

    except Exception as exc:
        import logging
        logging.getLogger('auth').error('verify_2fa error: %s', exc)
        return jsonify({'error': 'Failed to verify 2FA code'}), 500


@auth_bp.route('/login-check-2fa', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=60, key_func='ip',
            error_message='Too many login attempts. Please try again later.')
def login_check_2fa():
    """Check if user has 2FA enabled (called after successful password login).

    Body: {email, password}

    Returns:
        200: {requires_2fa: true/false}
        401: Invalid credentials
    """
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400

    email = data['email'].strip().lower() if isinstance(data.get('email'), str) else ''
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 403

    # Check if 2FA is enabled
    requires_2fa = getattr(user, 'totp_enabled', False)

    return jsonify({
        'requires_2fa': requires_2fa,
        'email': email
    }), 200
