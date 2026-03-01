"""RBAC Management Routes — Admin endpoints for role and permission management."""
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from ..models import db, User, Role, Permission, RolePermission, UserRole, RoleAuditLog
from ..auth import require_auth, require_admin
from ..rbac import (
    require_role, require_permission, assign_role_to_user, remove_role_from_user,
    grant_permission_to_role, revoke_permission_from_role, get_user_permissions,
    get_user_roles, has_permission, has_role
)
from ..input_validator import validate_request_data

rbac_bp = Blueprint('rbac', __name__, url_prefix='/api/admin/rbac')


# ============================================================================
# ROLE MANAGEMENT ENDPOINTS
# ============================================================================

@rbac_bp.route('/roles', methods=['GET'])
@require_auth
@require_role('admin')
def list_roles():
    """
    GET /api/admin/rbac/roles
    List all roles with optional permission details.

    Query params:
        include_permissions: bool (default: false)
        is_active: bool (optional, filter by active status)
    """
    try:
        include_permissions = request.args.get('include_permissions', 'false').lower() == 'true'
        is_active_filter = request.args.get('is_active')

        query = Role.query
        if is_active_filter is not None:
            is_active = is_active_filter.lower() == 'true'
            query = query.filter_by(is_active=is_active)

        roles = query.order_by(Role.created_at.desc()).all()

        return jsonify({
            'success': True,
            'roles': [role.to_dict(include_permissions=include_permissions) for role in roles]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rbac_bp.route('/roles', methods=['POST'])
@require_auth
@require_role('admin')
def create_role():
    """
    POST /api/admin/rbac/roles
    Create a new role.

    Request body:
        {
            "name": "supervisor",
            "description": "Supervisory role with elevated permissions"
        }
    """
    try:
        data = request.get_json()

        if not data or 'name' not in data:
            return jsonify({'error': 'Role name is required'}), 400

        name = data['name'].strip()
        description = data.get('description', '').strip()

        # Validate name
        if not name or len(name) < 2 or len(name) > 50:
            return jsonify({'error': 'Role name must be 2-50 characters'}), 400

        # Check if role exists
        if Role.query.filter_by(name=name).first():
            return jsonify({'error': f'Role "{name}" already exists'}), 409

        # Create role
        role = Role(
            name=name,
            description=description,
            is_active=True
        )
        db.session.add(role)
        db.session.commit()

        # Log the action
        from ..rbac import log_rbac_change
        log_rbac_change(
            action='create_role',
            target_type='role',
            target_role_id=role.id,
            actor_user_id=g.user['user_id'],
            status='success',
            details=f'Created role "{name}"'
        )

        return jsonify({
            'success': True,
            'message': f'Role "{name}" created successfully',
            'role': role.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rbac_bp.route('/roles/<int:role_id>', methods=['PUT'])
@require_auth
@require_role('admin')
def update_role(role_id):
    """
    PUT /api/admin/rbac/roles/<role_id>
    Update role details.

    Request body:
        {
            "description": "Updated description",
            "is_active": true
        }
    """
    try:
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Role not found'}), 404

        data = request.get_json()
        if data.get('description') is not None:
            role.description = data['description'].strip()
        if data.get('is_active') is not None:
            role.is_active = data['is_active']

        db.session.commit()

        from ..rbac import log_rbac_change
        log_rbac_change(
            action='update_role',
            target_type='role',
            target_role_id=role.id,
            actor_user_id=g.user['user_id'],
            status='success'
        )

        return jsonify({
            'success': True,
            'message': 'Role updated successfully',
            'role': role.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rbac_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@require_auth
@require_role('admin')
def delete_role(role_id):
    """
    DELETE /api/admin/rbac/roles/<role_id>
    Soft-delete a role (mark as inactive).
    """
    try:
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Role not found'}), 404

        # Prevent deletion of system roles
        system_roles = {'admin', 'user'}
        if role.name in system_roles:
            return jsonify({'error': f'Cannot delete system role "{role.name}"'}), 400

        role.is_active = False
        db.session.commit()

        from ..rbac import log_rbac_change
        log_rbac_change(
            action='delete_role',
            target_type='role',
            target_role_id=role.id,
            actor_user_id=g.user['user_id'],
            status='success'
        )

        return jsonify({'success': True, 'message': 'Role deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PERMISSION MANAGEMENT ENDPOINTS
# ============================================================================

@rbac_bp.route('/permissions', methods=['GET'])
@require_auth
@require_role('admin')
def list_permissions():
    """
    GET /api/admin/rbac/permissions
    List all permissions.

    Query params:
        resource: str (optional, filter by resource)
        action: str (optional, filter by action)
    """
    try:
        resource = request.args.get('resource')
        action = request.args.get('action')

        query = Permission.query.filter_by(is_active=True)
        if resource:
            query = query.filter_by(resource=resource)
        if action:
            query = query.filter_by(action=action)

        permissions = query.order_by(Permission.created_at.desc()).all()

        # Group by resource
        grouped = {}
        for perm in permissions:
            if perm.resource not in grouped:
                grouped[perm.resource] = []
            grouped[perm.resource].append(perm.to_dict())

        return jsonify({
            'success': True,
            'permissions': [p.to_dict() for p in permissions],
            'grouped': grouped
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rbac_bp.route('/permissions', methods=['POST'])
@require_auth
@require_role('admin')
def create_permission():
    """
    POST /api/admin/rbac/permissions
    Create a new permission.

    Request body:
        {
            "name": "approve:invoices",
            "resource": "invoices",
            "action": "approve",
            "description": "Approve invoices"
        }
    """
    try:
        data = request.get_json()

        required = ['name', 'resource', 'action']
        if not all(k in data for k in required):
            return jsonify({'error': f'Required fields: {", ".join(required)}'}), 400

        name = data['name'].strip()
        resource = data['resource'].strip()
        action = data['action'].strip()

        if Permission.query.filter_by(name=name).first():
            return jsonify({'error': f'Permission "{name}" already exists'}), 409

        perm = Permission(
            name=name,
            resource=resource,
            action=action,
            description=data.get('description', '').strip(),
            is_active=True
        )
        db.session.add(perm)
        db.session.commit()

        from ..rbac import log_rbac_change
        log_rbac_change(
            action='create_permission',
            target_type='permission',
            target_permission_id=perm.id,
            actor_user_id=g.user['user_id'],
            status='success'
        )

        return jsonify({
            'success': True,
            'message': f'Permission "{name}" created',
            'permission': perm.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# USER-ROLE ASSIGNMENT ENDPOINTS
# ============================================================================

@rbac_bp.route('/users/<int:user_id>/roles', methods=['GET'])
@require_auth
@require_role('admin')
def get_user_roles_endpoint(user_id):
    """
    GET /api/admin/rbac/users/<user_id>/roles
    Get all roles assigned to a user.
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        roles = [role.to_dict(include_permissions=True) for role in user.roles]

        return jsonify({
            'success': True,
            'user_id': user_id,
            'roles': roles
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rbac_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@require_auth
@require_role('admin')
def assign_role_endpoint(user_id):
    """
    POST /api/admin/rbac/users/<user_id>/roles
    Assign a role to a user.

    Request body:
        {
            "role_name": "moderator"
        }
    """
    try:
        data = request.get_json()
        if not data or 'role_name' not in data:
            return jsonify({'error': 'role_name is required'}), 400

        role_name = data['role_name'].strip()
        success, message = assign_role_to_user(
            user_id=user_id,
            role_name=role_name,
            assigned_by_id=g.user['user_id']
        )

        if not success:
            return jsonify({'error': message}), 400

        user = User.query.get(user_id)
        return jsonify({
            'success': True,
            'message': message,
            'user_roles': [role.to_dict() for role in user.roles]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rbac_bp.route('/users/<int:user_id>/roles/<role_name>', methods=['DELETE'])
@require_auth
@require_role('admin')
def remove_role_endpoint(user_id, role_name):
    """
    DELETE /api/admin/rbac/users/<user_id>/roles/<role_name>
    Remove a role from a user.
    """
    try:
        role_name = role_name.strip()
        success, message = remove_role_from_user(
            user_id=user_id,
            role_name=role_name,
            assigned_by_id=g.user['user_id']
        )

        if not success:
            return jsonify({'error': message}), 400

        user = User.query.get(user_id)
        return jsonify({
            'success': True,
            'message': message,
            'user_roles': [role.to_dict() for role in user.roles]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ROLE-PERMISSION ASSIGNMENT ENDPOINTS
# ============================================================================

@rbac_bp.route('/roles/<role_name>/permissions', methods=['GET'])
@require_auth
@require_role('admin')
def get_role_permissions(role_name):
    """
    GET /api/admin/rbac/roles/<role_name>/permissions
    Get all permissions assigned to a role.
    """
    try:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({'error': 'Role not found'}), 404

        permissions = [p.to_dict() for p in role.permissions]

        return jsonify({
            'success': True,
            'role': role.name,
            'permissions': permissions
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rbac_bp.route('/roles/<role_name>/permissions', methods=['POST'])
@require_auth
@require_role('admin')
def grant_permission_endpoint(role_name):
    """
    POST /api/admin/rbac/roles/<role_name>/permissions
    Grant a permission to a role.

    Request body:
        {
            "permission_name": "write:sns_posts"
        }
    """
    try:
        data = request.get_json()
        if not data or 'permission_name' not in data:
            return jsonify({'error': 'permission_name is required'}), 400

        perm_name = data['permission_name'].strip()
        success, message = grant_permission_to_role(
            role_name=role_name,
            permission_name=perm_name,
            assigned_by_id=g.user['user_id']
        )

        if not success:
            return jsonify({'error': message}), 400

        role = Role.query.filter_by(name=role_name).first()
        return jsonify({
            'success': True,
            'message': message,
            'permissions': [p.to_dict() for p in role.permissions]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rbac_bp.route('/roles/<role_name>/permissions/<permission_name>', methods=['DELETE'])
@require_auth
@require_role('admin')
def revoke_permission_endpoint(role_name, permission_name):
    """
    DELETE /api/admin/rbac/roles/<role_name>/permissions/<permission_name>
    Revoke a permission from a role.
    """
    try:
        permission_name = permission_name.strip()
        success, message = revoke_permission_from_role(
            role_name=role_name,
            permission_name=permission_name,
            assigned_by_id=g.user['user_id']
        )

        if not success:
            return jsonify({'error': message}), 400

        role = Role.query.filter_by(name=role_name).first()
        return jsonify({
            'success': True,
            'message': message,
            'permissions': [p.to_dict() for p in role.permissions]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@rbac_bp.route('/audit-log', methods=['GET'])
@require_auth
@require_role('admin')
def get_audit_log():
    """
    GET /api/admin/rbac/audit-log
    Get RBAC audit log with optional filters.

    Query params:
        action: str (filter by action)
        target_user_id: int (filter by target user)
        target_role_id: int (filter by target role)
        limit: int (default: 100, max: 1000)
        offset: int (default: 0)
    """
    try:
        action = request.args.get('action')
        target_user_id = request.args.get('target_user_id', type=int)
        target_role_id = request.args.get('target_role_id', type=int)
        limit = min(int(request.args.get('limit', 100)), 1000)
        offset = int(request.args.get('offset', 0))

        query = RoleAuditLog.query
        if action:
            query = query.filter_by(action=action)
        if target_user_id:
            query = query.filter_by(target_user_id=target_user_id)
        if target_role_id:
            query = query.filter_by(target_role_id=target_role_id)

        total = query.count()
        logs = query.order_by(RoleAuditLog.timestamp.desc()).limit(limit).offset(offset).all()

        return jsonify({
            'success': True,
            'total': total,
            'limit': limit,
            'offset': offset,
            'logs': [log.to_dict() for log in logs]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rbac_bp.route('/audit-log/user/<int:user_id>', methods=['GET'])
@require_auth
@require_role('admin')
def get_user_audit_log(user_id):
    """
    GET /api/admin/rbac/audit-log/user/<user_id>
    Get audit log for a specific user (showing actions they performed).
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        offset = int(request.args.get('offset', 0))

        total = RoleAuditLog.query.filter_by(user_id=user_id).count()
        logs = RoleAuditLog.query.filter_by(user_id=user_id)\
            .order_by(RoleAuditLog.timestamp.desc())\
            .limit(limit).offset(offset).all()

        return jsonify({
            'success': True,
            'user_id': user_id,
            'total': total,
            'logs': [log.to_dict() for log in logs]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@rbac_bp.route('/users/<int:user_id>/check-permission', methods=['POST'])
@require_auth
def check_user_permission(user_id):
    """
    POST /api/admin/rbac/users/<user_id>/check-permission
    Check if a user has a specific permission.

    Request body:
        {
            "permission_name": "write:sns_posts"
        }
    """
    try:
        data = request.get_json()
        if not data or 'permission_name' not in data:
            return jsonify({'error': 'permission_name is required'}), 400

        perm_name = data['permission_name'].strip()
        has_perm = has_permission(user_id, perm_name)

        return jsonify({
            'success': True,
            'user_id': user_id,
            'permission': perm_name,
            'has_permission': has_perm
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rbac_bp.route('/users/<int:user_id>/permissions', methods=['GET'])
@require_auth
@require_role('admin')
def get_user_all_permissions(user_id):
    """
    GET /api/admin/rbac/users/<user_id>/permissions
    Get all permissions for a user (derived from their roles).
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        permissions = get_user_permissions(user_id)
        roles = get_user_roles(user_id)

        return jsonify({
            'success': True,
            'user_id': user_id,
            'roles': roles,
            'permissions': sorted(list(permissions))
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
