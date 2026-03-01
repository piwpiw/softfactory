"""Role-Based Access Control (RBAC) Module — Decorators, utilities, and management."""
from flask import g, jsonify, request
from functools import wraps
from datetime import datetime
from .models import db, User, Role, Permission, RolePermission, UserRole, RoleAuditLog


# ============================================================================
# RBAC Decorators
# ============================================================================

def require_role(*required_roles):
    """
    Decorator to restrict access to users with specific roles.

    Usage:
        @require_role('admin', 'moderator')
        def admin_endpoint():
            pass
    """
    def decorator(fn):
        @wraps(fn)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated (set by @require_auth)
            if not hasattr(g, 'user') or g.user is None:
                return jsonify({'error': 'Unauthorized'}), 401

            # Load user roles from database
            user = User.query.get(g.user['user_id'])
            if not user:
                return jsonify({'error': 'User not found'}), 404

            # Get user's role names (check both legacy 'role' field and new UserRole table)
            user_roles = {role.name for role in user.roles}

            # Legacy support: check 'role' field for backward compatibility
            if user.role and user.role != 'user':
                user_roles.add(user.role)

            # Check if user has any of the required roles
            if not any(role in user_roles for role in required_roles):
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Requires one of roles: {", ".join(required_roles)}'
                }), 403

            return fn(*args, **kwargs)
        return decorated_function
    return decorator


def require_permission(*required_permissions):
    """
    Decorator to restrict access based on granular permissions.

    Usage:
        @require_permission('write:sns_posts', 'delete:sns_posts')
        def create_sns_post():
            pass

    Args:
        required_permissions: One or more permission names (e.g., 'write:sns_posts', 'read:users')
    """
    def decorator(fn):
        @wraps(fn)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user') or g.user is None:
                return jsonify({'error': 'Unauthorized'}), 401

            user = User.query.get(g.user['user_id'])
            if not user:
                return jsonify({'error': 'User not found'}), 404

            # Get all permissions for user's roles
            user_permissions = set()
            for role in user.roles:
                for perm in role.permissions:
                    if perm.is_active:
                        user_permissions.add(perm.name)

            # Check if user has any of the required permissions
            if not any(perm in user_permissions for perm in required_permissions):
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Requires one of permissions: {", ".join(required_permissions)}'
                }), 403

            return fn(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin(fn):
    """Convenience decorator — requires 'admin' role."""
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        return require_role('admin')(fn)(*args, **kwargs)
    return decorated_function


# ============================================================================
# RBAC Utility Functions
# ============================================================================

def get_user_permissions(user_id):
    """
    Get all permissions for a user based on their roles.

    Returns:
        Set of permission names (e.g., {'write:sns_posts', 'read:users'})
    """
    user = User.query.get(user_id)
    if not user:
        return set()

    permissions = set()
    for role in user.roles:
        for perm in role.permissions:
            if perm.is_active:
                permissions.add(perm.name)

    return permissions


def get_user_roles(user_id):
    """
    Get all roles for a user.

    Returns:
        List of role names
    """
    user = User.query.get(user_id)
    if not user:
        return []

    roles = [role.name for role in user.roles if role.is_active]

    # Legacy support
    if user.role and user.role != 'user':
        if user.role not in roles:
            roles.append(user.role)

    return roles


def has_permission(user_id, permission_name):
    """
    Check if a user has a specific permission.

    Returns:
        Boolean
    """
    user = User.query.get(user_id)
    if not user:
        return False

    for role in user.roles:
        for perm in role.permissions:
            if perm.is_active and perm.name == permission_name:
                return True

    return False


def has_role(user_id, role_name):
    """
    Check if a user has a specific role.

    Returns:
        Boolean
    """
    user = User.query.get(user_id)
    if not user:
        return False

    # Check UserRole table
    for role in user.roles:
        if role.is_active and role.name == role_name:
            return True

    # Legacy support
    if user.role == role_name:
        return True

    return False


def assign_role_to_user(user_id, role_name, assigned_by_id=None):
    """
    Assign a role to a user and log the action.

    Args:
        user_id: ID of user to assign role to
        role_name: Name of role to assign
        assigned_by_id: ID of user making the assignment (for audit log)

    Returns:
        Tuple (success: bool, message: str)
    """
    user = User.query.get(user_id)
    if not user:
        return False, "User not found"

    role = Role.query.filter_by(name=role_name, is_active=True).first()
    if not role:
        return False, f"Role '{role_name}' not found or inactive"

    # Check if user already has this role
    if role in user.roles:
        return False, f"User already has role '{role_name}'"

    try:
        # Add role to user
        user.roles.append(role)
        db.session.commit()

        # Log the action
        log_rbac_change(
            action='assign_role',
            target_type='user',
            target_user_id=user_id,
            target_role_id=role.id,
            actor_user_id=assigned_by_id,
            status='success'
        )

        return True, f"Role '{role_name}' assigned to user {user_id}"
    except Exception as e:
        db.session.rollback()
        log_rbac_change(
            action='assign_role',
            target_type='user',
            target_user_id=user_id,
            target_role_id=role.id,
            actor_user_id=assigned_by_id,
            status='failure',
            details=str(e)
        )
        return False, f"Error assigning role: {str(e)}"


def remove_role_from_user(user_id, role_name, assigned_by_id=None):
    """
    Remove a role from a user and log the action.

    Args:
        user_id: ID of user to remove role from
        role_name: Name of role to remove
        assigned_by_id: ID of user making the change (for audit log)

    Returns:
        Tuple (success: bool, message: str)
    """
    user = User.query.get(user_id)
    if not user:
        return False, "User not found"

    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return False, f"Role '{role_name}' not found"

    # Check if user has this role
    if role not in user.roles:
        return False, f"User does not have role '{role_name}'"

    try:
        user.roles.remove(role)
        db.session.commit()

        log_rbac_change(
            action='remove_role',
            target_type='user',
            target_user_id=user_id,
            target_role_id=role.id,
            actor_user_id=assigned_by_id,
            status='success'
        )

        return True, f"Role '{role_name}' removed from user {user_id}"
    except Exception as e:
        db.session.rollback()
        log_rbac_change(
            action='remove_role',
            target_type='user',
            target_user_id=user_id,
            target_role_id=role.id,
            actor_user_id=assigned_by_id,
            status='failure',
            details=str(e)
        )
        return False, f"Error removing role: {str(e)}"


def grant_permission_to_role(role_name, permission_name, assigned_by_id=None):
    """
    Grant a permission to a role and log the action.

    Args:
        role_name: Name of role
        permission_name: Name of permission (e.g., 'write:sns_posts')
        assigned_by_id: ID of user making the assignment

    Returns:
        Tuple (success: bool, message: str)
    """
    role = Role.query.filter_by(name=role_name, is_active=True).first()
    if not role:
        return False, f"Role '{role_name}' not found or inactive"

    permission = Permission.query.filter_by(name=permission_name, is_active=True).first()
    if not permission:
        return False, f"Permission '{permission_name}' not found or inactive"

    if permission in role.permissions:
        return False, f"Role '{role_name}' already has permission '{permission_name}'"

    try:
        role.permissions.append(permission)
        db.session.commit()

        log_rbac_change(
            action='grant_permission',
            target_type='role',
            target_role_id=role.id,
            target_permission_id=permission.id,
            actor_user_id=assigned_by_id,
            status='success'
        )

        return True, f"Permission '{permission_name}' granted to role '{role_name}'"
    except Exception as e:
        db.session.rollback()
        log_rbac_change(
            action='grant_permission',
            target_type='role',
            target_role_id=role.id,
            target_permission_id=permission.id,
            actor_user_id=assigned_by_id,
            status='failure',
            details=str(e)
        )
        return False, f"Error granting permission: {str(e)}"


def revoke_permission_from_role(role_name, permission_name, assigned_by_id=None):
    """
    Revoke a permission from a role and log the action.

    Args:
        role_name: Name of role
        permission_name: Name of permission
        assigned_by_id: ID of user making the change

    Returns:
        Tuple (success: bool, message: str)
    """
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return False, f"Role '{role_name}' not found"

    permission = Permission.query.filter_by(name=permission_name).first()
    if not permission:
        return False, f"Permission '{permission_name}' not found"

    if permission not in role.permissions:
        return False, f"Role '{role_name}' does not have permission '{permission_name}'"

    try:
        role.permissions.remove(permission)
        db.session.commit()

        log_rbac_change(
            action='revoke_permission',
            target_type='role',
            target_role_id=role.id,
            target_permission_id=permission.id,
            actor_user_id=assigned_by_id,
            status='success'
        )

        return True, f"Permission '{permission_name}' revoked from role '{role_name}'"
    except Exception as e:
        db.session.rollback()
        log_rbac_change(
            action='revoke_permission',
            target_type='role',
            target_role_id=role.id,
            target_permission_id=permission.id,
            actor_user_id=assigned_by_id,
            status='failure',
            details=str(e)
        )
        return False, f"Error revoking permission: {str(e)}"


def log_rbac_change(action, target_type, actor_user_id=None, target_user_id=None,
                    target_role_id=None, target_permission_id=None, status='success', details=None):
    """
    Log an RBAC-related change to the audit log.

    Args:
        action: Type of action ('assign_role', 'remove_role', 'grant_permission', etc.)
        target_type: Type of target ('user' or 'role')
        actor_user_id: User ID who performed the action
        target_user_id: User ID that was affected
        target_role_id: Role ID that was affected
        target_permission_id: Permission ID that was affected
        status: 'success' or 'failure'
        details: Optional details/error message
    """
    try:
        audit_log = RoleAuditLog(
            user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_user_id=target_user_id,
            target_role_id=target_role_id,
            target_permission_id=target_permission_id,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent', '')[:255] if request else None,
            status=status,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging RBAC change: {str(e)}")


# ============================================================================
# Initialize Default Roles and Permissions
# ============================================================================

def init_rbac():
    """Initialize default roles and permissions in database."""
    try:
        # Define default permissions (resource:action format)
        permissions_data = [
            # SNS Posts
            ('read:sns_posts', 'sns_posts', 'read', 'Read SNS posts'),
            ('create:sns_posts', 'sns_posts', 'create', 'Create new SNS posts'),
            ('write:sns_posts', 'sns_posts', 'write', 'Edit SNS posts'),
            ('delete:sns_posts', 'sns_posts', 'delete', 'Delete SNS posts'),
            ('moderate:sns_posts', 'sns_posts', 'moderate', 'Moderate SNS posts'),

            # Users
            ('read:users', 'users', 'read', 'View user profiles'),
            ('create:users', 'users', 'create', 'Create new users'),
            ('write:users', 'users', 'update', 'Edit user information'),
            ('delete:users', 'users', 'delete', 'Delete user accounts'),
            ('moderate:users', 'users', 'moderate', 'Moderate users'),

            # Payments
            ('read:payments', 'payments', 'read', 'View payment information'),
            ('write:payments', 'payments', 'update', 'Update payments'),
            ('refund:payments', 'payments', 'refund', 'Process refunds'),
            ('manage:subscriptions', 'payments', 'manage_subscriptions', 'Manage user subscriptions'),

            # Analytics
            ('read:analytics', 'analytics', 'read', 'View analytics'),
            ('export:analytics', 'analytics', 'export', 'Export analytics data'),

            # Platform Admin
            ('admin:all', 'platform', 'admin_all', 'Full platform access'),
        ]

        # Create permissions
        for name, resource, action, description in permissions_data:
            if not Permission.query.filter_by(name=name).first():
                perm = Permission(
                    name=name,
                    resource=resource,
                    action=action,
                    description=description,
                    is_active=True
                )
                db.session.add(perm)

        db.session.commit()

        # Define default roles
        roles_data = [
            ('admin', 'Platform administrator with full access'),
            ('moderator', 'Can moderate content and users'),
            ('creator', 'Can create and manage own content'),
            ('user', 'Regular user with basic permissions'),
        ]

        # Create roles
        for name, description in roles_data:
            if not Role.query.filter_by(name=name).first():
                role = Role(
                    name=name,
                    description=description,
                    is_active=True
                )
                db.session.add(role)

        db.session.commit()

        # Assign permissions to roles
        role_permissions_map = {
            'admin': [
                'read:sns_posts', 'create:sns_posts', 'write:sns_posts', 'delete:sns_posts', 'moderate:sns_posts',
                'read:users', 'create:users', 'write:users', 'delete:users', 'moderate:users',
                'read:payments', 'write:payments', 'refund:payments', 'manage:subscriptions',
                'read:analytics', 'export:analytics',
                'admin:all'
            ],
            'moderator': [
                'read:sns_posts', 'moderate:sns_posts',
                'read:users', 'moderate:users',
                'read:analytics'
            ],
            'creator': [
                'read:sns_posts', 'create:sns_posts', 'write:sns_posts', 'delete:sns_posts',
                'read:users',
                'read:analytics'
            ],
            'user': [
                'read:sns_posts', 'create:sns_posts',
                'read:users'
            ]
        }

        for role_name, perm_names in role_permissions_map.items():
            role = Role.query.filter_by(name=role_name).first()
            if role:
                for perm_name in perm_names:
                    perm = Permission.query.filter_by(name=perm_name).first()
                    if perm and perm not in role.permissions:
                        role.permissions.append(perm)

        db.session.commit()
        print("RBAC initialized successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing RBAC: {str(e)}")
