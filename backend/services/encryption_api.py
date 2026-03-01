"""
Encryption & API Key Management API Routes

Endpoints:
- POST /api/encryption/keys — Create new API key
- GET /api/encryption/keys — List user's API keys
- DELETE /api/encryption/keys/<id> — Revoke API key
- POST /api/encryption/audit-logs — Get audit logs
- POST /api/encryption/rotate — Initiate key rotation (admin only)
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
import secrets
import string
import logging

from backend.models import db, APIKey, AuditLog, EncryptionKeyRotation
from backend.auth import require_auth, require_admin
from backend.encryption_service import encryption_service

logger = logging.getLogger(__name__)

encryption_bp = Blueprint('encryption', __name__, url_prefix='/api/encryption')


def generate_api_key_pair():
    """Generate a random API key with a memorable prefix"""
    # Generate 32-character random string
    chars = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(32))

    # Create key with prefix (pk_xxx_randompart)
    prefix = 'pk_' + secrets.token_hex(4)[:8]
    full_key = f"{prefix}_{random_part}"

    return prefix, full_key


def log_audit_action(user_id, action, resource_type, resource_id=None, status='success', details=None, ip_address=None):
    """Helper to log audit trail"""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address or request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')[:255],
        status=status,
        details=details
    )
    db.session.add(audit)
    db.session.commit()
    logger.info(f"Audit log: {action} by user {user_id}")


@encryption_bp.route('/keys', methods=['POST'])
@require_auth
def create_api_key():
    """
    Create a new API key for the authenticated user.

    Request:
    {
        "name": "Production API Key",
        "expires_in_days": 30,
        "scopes": "read:projects,write:sns"
    }

    Response:
    {
        "id": 1,
        "name": "Production API Key",
        "key": "pk_abc123_...fullkey...",  // Only returned here!
        "prefix": "pk_abc123",
        "created_at": "2026-02-26T...",
        "expires_at": "2026-03-28T...",
        "scopes": ["read:projects", "write:sns"]
    }
    """
    data = request.get_json() or {}
    user_id = g.user_id

    # Validation
    name = data.get('name', '').strip()
    if not name or len(name) > 100:
        return jsonify({'error': 'Invalid key name (1-100 chars)'}), 400

    expires_in_days = data.get('expires_in_days', 30)
    if not isinstance(expires_in_days, int) or expires_in_days < 1 or expires_in_days > 365:
        return jsonify({'error': 'expires_in_days must be 1-365'}), 400

    scopes = data.get('scopes', '')
    if scopes and len(scopes) > 255:
        return jsonify({'error': 'Scopes too long'}), 400

    try:
        # Generate key
        prefix, full_key = generate_api_key_pair()

        # Encrypt the key before storing
        encrypted_key = encryption_service.encrypt_field(full_key)

        # Create database record
        api_key = APIKey(
            user_id=user_id,
            name=name,
            prefix=prefix,
            encrypted_key=encrypted_key,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            scopes=scopes if scopes else None,
        )

        db.session.add(api_key)
        db.session.commit()

        # Log audit
        log_audit_action(
            user_id, 'api_key_created', 'api_key',
            resource_id=api_key.id,
            details=f"Created API key '{name}' with scopes: {scopes}"
        )

        logger.info(f"API key created: {api_key.id} for user {user_id}")

        # Return key only on creation
        response = api_key.to_dict(include_key=True)
        response['key'] = full_key  # Return plaintext key only once
        return jsonify(response), 201

    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        log_audit_action(user_id, 'api_key_created', 'api_key', status='failure',
                        details=f"Failed: {str(e)}")
        return jsonify({'error': 'Failed to create API key'}), 500


@encryption_bp.route('/keys', methods=['GET'])
@require_auth
def list_api_keys():
    """
    List all API keys for the authenticated user.

    Query params:
    - include_expired: bool (default false) — include expired keys

    Response:
    [
        {
            "id": 1,
            "name": "Production",
            "prefix": "pk_abc123",
            "created_at": "...",
            "last_used_at": "...",
            "expires_at": "...",
            "is_active": true,
            "scopes": ["read:projects"]
        },
        ...
    ]
    """
    user_id = g.user_id
    include_expired = request.args.get('include_expired', 'false').lower() == 'true'

    try:
        query = APIKey.query.filter_by(user_id=user_id)

        if not include_expired:
            query = query.filter(APIKey.expires_at > datetime.utcnow())

        api_keys = query.order_by(APIKey.created_at.desc()).all()

        return jsonify([key.to_dict() for key in api_keys]), 200

    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        return jsonify({'error': 'Failed to list API keys'}), 500


@encryption_bp.route('/keys/<int:key_id>', methods=['DELETE'])
@require_auth
def revoke_api_key(key_id):
    """
    Revoke (soft-delete) an API key.

    Request:
    {
        "reason": "Key compromised"
    }

    Response:
    {
        "message": "Key revoked successfully",
        "id": 1,
        "revoked_at": "2026-02-26T..."
    }
    """
    user_id = g.user_id
    data = request.get_json() or {}

    try:
        api_key = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404

        reason = data.get('reason', 'Manually revoked')
        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        api_key.revocation_reason = reason[:255] if reason else None

        db.session.commit()

        # Log audit
        log_audit_action(
            user_id, 'api_key_revoked', 'api_key',
            resource_id=key_id,
            details=f"Revoked: {reason}"
        )

        logger.info(f"API key revoked: {key_id} by user {user_id}")

        return jsonify({
            'message': 'Key revoked successfully',
            'id': api_key.id,
            'revoked_at': api_key.revoked_at.isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        return jsonify({'error': 'Failed to revoke key'}), 500


@encryption_bp.route('/audit-logs', methods=['GET'])
@require_auth
def get_audit_logs():
    """
    Get audit logs for the authenticated user.

    Query params:
    - limit: int (default 50) — max 100
    - offset: int (default 0)
    - action: str — filter by action
    - resource_type: str — filter by resource type

    Response:
    {
        "total": 150,
        "logs": [
            {
                "id": 1,
                "action": "api_key_created",
                "resource_type": "api_key",
                "timestamp": "2026-02-26T...",
                "status": "success"
            },
            ...
        ]
    }
    """
    user_id = g.user_id
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))
    action_filter = request.args.get('action')
    resource_type_filter = request.args.get('resource_type')

    try:
        query = AuditLog.query.filter_by(user_id=user_id)

        if action_filter:
            query = query.filter_by(action=action_filter)
        if resource_type_filter:
            query = query.filter_by(resource_type=resource_type_filter)

        total = query.count()
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset).all()

        return jsonify({
            'total': total,
            'logs': [log.to_dict() for log in logs],
        }), 200

    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        return jsonify({'error': 'Failed to retrieve audit logs'}), 500


@encryption_bp.route('/rotate', methods=['POST'])
@require_admin
def initiate_key_rotation():
    """
    Initiate encryption key rotation (admin only).

    Request:
    {
        "notes": "Scheduled rotation"
    }

    Response:
    {
        "rotation_id": 1,
        "status": "in_progress",
        "message": "Key rotation started"
    }
    """
    data = request.get_json() or {}
    user_id = g.user_id

    try:
        # Check if rotation is already in progress
        in_progress = EncryptionKeyRotation.query.filter_by(
            rotation_status='in_progress'
        ).first()

        if in_progress:
            return jsonify({'error': 'Key rotation already in progress'}), 409

        # Create rotation record
        rotation = EncryptionKeyRotation(
            old_key_version='v1',
            new_key_version='v2',
            initiated_by_user_id=user_id,
            rotation_status='pending',
            notes=data.get('notes')
        )

        db.session.add(rotation)
        db.session.commit()

        # Log audit
        log_audit_action(
            user_id, 'encryption_key_rotation_initiated', 'encryption',
            resource_id=rotation.id,
            details=data.get('notes', 'Scheduled key rotation')
        )

        logger.info(f"Key rotation initiated by admin {user_id}: ID {rotation.id}")

        return jsonify({
            'rotation_id': rotation.id,
            'status': rotation.rotation_status,
            'message': 'Key rotation initiated'
        }), 201

    except Exception as e:
        logger.error(f"Failed to initiate key rotation: {e}")
        return jsonify({'error': 'Failed to initiate key rotation'}), 500


@encryption_bp.route('/rotation-status/<int:rotation_id>', methods=['GET'])
@require_admin
def get_rotation_status(rotation_id):
    """
    Get the status of an ongoing key rotation (admin only).

    Response:
    {
        "id": 1,
        "rotation_status": "in_progress",
        "total_records": 100,
        "rotated_records": 75,
        "failed_records": 0,
        "progress_percent": 75,
        "error_details": null
    }
    """
    try:
        rotation = EncryptionKeyRotation.query.get(rotation_id)
        if not rotation:
            return jsonify({'error': 'Rotation not found'}), 404

        return jsonify(rotation.to_dict()), 200

    except Exception as e:
        logger.error(f"Failed to get rotation status: {e}")
        return jsonify({'error': 'Failed to get rotation status'}), 500
