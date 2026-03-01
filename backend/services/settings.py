"""Settings Service"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime
import json
from ..models import db, User, SNSAccount, SNSOAuthState
from ..auth import require_auth

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

class OrgSettings:
    _storage = {}
    @classmethod
    def get(cls, user_id, key, default=None):
        if user_id not in cls._storage:
            return default
        return cls._storage[user_id].get(key, default)
    @classmethod
    def set(cls, user_id, key, value):
        if user_id not in cls._storage:
            cls._storage[user_id] = {}
        cls._storage[user_id][key] = value
    @classmethod
    def get_all(cls, user_id):
        return cls._storage.get(user_id, {})
    @classmethod
    def update(cls, user_id, data):
        if user_id not in cls._storage:
            cls._storage[user_id] = {}
        cls._storage[user_id].update(data)

@settings_bp.route('/organization', methods=['GET'])
@require_auth
def get_organization_settings():
    settings = OrgSettings.get_all(g.user_id)
    defaults = {
        'organization_name': g.user.name,
        'organization_email': g.user.email,
        'timezone': 'UTC',
        'language': 'en',
        'currency': 'USD',
        'theme': 'light'
    }
    result = {**defaults, **settings}
    return jsonify(result), 200

@settings_bp.route('/organization', methods=['PUT'])
@require_auth
def update_organization_settings():
    data = request.get_json() or {}
    allowed_keys = {'organization_name', 'timezone', 'language', 'currency', 'theme'}
    filtered = {k: v for k, v in data.items() if k in allowed_keys}
    OrgSettings.update(g.user_id, filtered)
    return jsonify({'message': 'Settings updated', 'settings': OrgSettings.get_all(g.user_id)}), 200

@settings_bp.route('/integrations', methods=['GET'])
@require_auth
def get_integrations():
    sns_accounts = SNSAccount.query.filter_by(user_id=g.user_id).all()
    connected = [{
        'id': a.id,
        'platform': a.platform,
        'account_name': a.account_name,
        'status': 'active' if a.is_active else 'inactive'
    } for a in sns_accounts]
    
    platforms = ['instagram', 'facebook', 'twitter', 'linkedin', 'tiktok', 'youtube', 'pinterest']
    connected_platforms = {a.platform for a in sns_accounts}
    available = [{
        'platform': p,
        'name': p.replace('_', ' ').title(),
        'status': 'available'
    } for p in platforms if p not in connected_platforms]
    
    return jsonify({'connected': connected, 'available': available}), 200

@settings_bp.route('/integrations/<platform>/connect', methods=['POST'])
@require_auth
def connect_integration(platform):
    existing = SNSAccount.query.filter_by(user_id=g.user_id, platform=platform).first()
    if existing:
        return jsonify({'error': f'{platform} already connected'}), 400
    
    import secrets
    state = secrets.token_urlsafe(32)
    oauth_state = SNSOAuthState(user_id=g.user_id, platform=platform, state=state, created_at=datetime.utcnow())
    db.session.add(oauth_state)
    db.session.commit()
    
    return jsonify({'status': 'pending', 'platform': platform, 'state': state}), 200

@settings_bp.route('/integrations/<int:account_id>/disconnect', methods=['POST'])
@require_auth
def disconnect_integration(account_id):
    account = SNSAccount.query.filter_by(id=account_id, user_id=g.user_id).first()
    if not account:
        return jsonify({'error': 'Integration not found'}), 404
    account.is_active = False
    db.session.commit()
    return jsonify({'message': 'Integration disconnected'}), 200

@settings_bp.route('/api-keys', methods=['GET'])
@require_auth
def get_api_keys():
    return jsonify([{
        'id': 'key_1',
        'name': 'Default API Key',
        'key': 'sk_live_' + '*' * 20,
        'created_at': '2026-01-15T10:00:00Z',
        'active': True
    }]), 200

@settings_bp.route('/webhook-endpoints', methods=['GET'])
@require_auth
def get_webhooks():
    return jsonify([{
        'id': 'wh_1',
        'url': 'https://example.com/webhooks',
        'events': ['post.published'],
        'active': True
    }]), 200

@settings_bp.route('/notifications', methods=['GET'])
@require_auth
def get_notification_settings():
    return jsonify({
        'email': {'digest': True, 'security': True},
        'sms': {'enabled': False},
        'in_app': {'enabled': True}
    }), 200

@settings_bp.route('/billing', methods=['GET'])
@require_auth
def get_billing_settings():
    return jsonify({
        'plan': 'Premium',
        'amount': 99.99,
        'auto_renew': True,
        'invoices': [{'id': 'inv_001', 'amount': 99.99, 'status': 'paid'}]
    }), 200
