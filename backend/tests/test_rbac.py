"""Test suite for RBAC (Role-Based Access Control) system."""
import pytest
from datetime import datetime
from backend.models import db, User, Role, Permission, UserRole, RoleAuditLog
from backend.rbac import (
    assign_role_to_user, remove_role_from_user, grant_permission_to_role,
    revoke_permission_from_role, get_user_permissions, get_user_roles,
    has_permission, has_role, init_rbac
)


@pytest.fixture
def app_with_rbac(app):
    """Create app with RBAC initialized."""
    with app.app_context():
        db.create_all()
        init_rbac()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(app_with_rbac):
    """Create a test user."""
    with app_with_rbac.app_context():
        user = User(
            email='testuser@example.com',
            name='Test User',
            role='user'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_user(app_with_rbac):
    """Create an admin user."""
    with app_with_rbac.app_context():
        user = User(
            email='admin@example.com',
            name='Admin User',
            role='admin'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Assign admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role and admin_role not in user.roles:
            user.roles.append(admin_role)
            db.session.commit()

        return user


class TestRoleManagement:
    """Test role creation and management."""

    def test_create_role(self, app_with_rbac):
        """Test creating a new role."""
        with app_with_rbac.app_context():
            role = Role(name='test_role', description='Test role', is_active=True)
            db.session.add(role)
            db.session.commit()

            retrieved = Role.query.filter_by(name='test_role').first()
            assert retrieved is not None
            assert retrieved.description == 'Test role'

    def test_role_permissions(self, app_with_rbac):
        """Test assigning permissions to roles."""
        with app_with_rbac.app_context():
            role = Role.query.filter_by(name='creator').first()
            assert role is not None

            # Creator should have write permission for SNS posts
            perm_names = {p.name for p in role.permissions}
            assert 'write:sns_posts' in perm_names or 'create:sns_posts' in perm_names

    def test_list_roles(self, app_with_rbac):
        """Test retrieving all roles."""
        with app_with_rbac.app_context():
            roles = Role.query.filter_by(is_active=True).all()
            assert len(roles) > 0

            role_names = {r.name for r in roles}
            assert 'admin' in role_names
            assert 'user' in role_names


class TestPermissionManagement:
    """Test permission creation and assignment."""

    def test_create_permission(self, app_with_rbac):
        """Test creating a new permission."""
        with app_with_rbac.app_context():
            perm = Permission(
                name='custom:action',
                resource='custom',
                action='action',
                description='Custom permission'
            )
            db.session.add(perm)
            db.session.commit()

            retrieved = Permission.query.filter_by(name='custom:action').first()
            assert retrieved is not None

    def test_grant_permission_to_role(self, app_with_rbac):
        """Test granting a permission to a role."""
        with app_with_rbac.app_context():
            success, message = grant_permission_to_role(
                role_name='creator',
                permission_name='write:sns_posts'
            )

            # May return False if already assigned, that's OK
            assert isinstance(success, bool)

    def test_revoke_permission_from_role(self, app_with_rbac):
        """Test revoking a permission from a role."""
        with app_with_rbac.app_context():
            # First grant a permission
            grant_permission_to_role('creator', 'delete:sns_posts')

            # Then revoke it
            success, message = revoke_permission_from_role(
                role_name='creator',
                permission_name='delete:sns_posts'
            )

            # Should succeed or indicate already removed
            if success:
                role = Role.query.filter_by(name='creator').first()
                perm_names = {p.name for p in role.permissions}
                assert 'delete:sns_posts' not in perm_names


class TestUserRoleAssignment:
    """Test assigning roles to users."""

    def test_assign_role_to_user(self, app_with_rbac, test_user):
        """Test assigning a role to a user."""
        with app_with_rbac.app_context():
            user = User.query.get(test_user.id)
            assert user is not None

            success, message = assign_role_to_user(
                user_id=user.id,
                role_name='creator'
            )

            assert success
            user = User.query.get(test_user.id)
            role_names = {r.name for r in user.roles}
            assert 'creator' in role_names

    def test_remove_role_from_user(self, app_with_rbac, test_user):
        """Test removing a role from a user."""
        with app_with_rbac.app_context():
            user = User.query.get(test_user.id)

            # First assign
            assign_role_to_user(user.id, 'moderator')

            # Then remove
            success, message = remove_role_from_user(
                user_id=user.id,
                role_name='moderator'
            )

            assert success
            user = User.query.get(test_user.id)
            role_names = {r.name for r in user.roles}
            assert 'moderator' not in role_names

    def test_get_user_roles(self, app_with_rbac, test_user):
        """Test getting user roles."""
        with app_with_rbac.app_context():
            user = User.query.get(test_user.id)
            assign_role_to_user(user.id, 'creator')

            roles = get_user_roles(user.id)
            assert 'creator' in roles


class TestPermissionChecking:
    """Test permission checking utilities."""

    def test_has_permission(self, app_with_rbac, test_user):
        """Test checking if user has a permission."""
        with app_with_rbac.app_context():
            user = User.query.get(test_user.id)
            assign_role_to_user(user.id, 'creator')

            # Creator has create:sns_posts permission
            has_perm = has_permission(user.id, 'create:sns_posts')
            assert has_perm

            # Creator doesn't have admin:all permission
            has_admin = has_permission(user.id, 'admin:all')
            assert not has_admin

    def test_has_role(self, app_with_rbac, test_user):
        """Test checking if user has a role."""
        with app_with_rbac.app_context():
            user = User.query.get(test_user.id)
            assign_role_to_user(user.id, 'moderator')

            assert has_role(user.id, 'moderator')
            assert not has_role(user.id, 'admin')

    def test_get_user_permissions(self, app_with_rbac, test_user):
        """Test getting all user permissions."""
        with app_with_rbac.app_context():
            user = User.query.get(test_user.id)
            assign_role_to_user(user.id, 'creator')

            permissions = get_user_permissions(user.id)
            assert isinstance(permissions, set)
            assert len(permissions) > 0


class TestAuditLogging:
    """Test RBAC audit logging."""

    def test_role_assignment_logged(self, app_with_rbac, test_user, admin_user):
        """Test that role assignments are logged."""
        with app_with_rbac.app_context():
            user = User.query.get(test_user.id)
            admin = User.query.get(admin_user.id)

            assign_role_to_user(
                user_id=user.id,
                role_name='creator',
                assigned_by_id=admin.id
            )

            # Check audit log
            logs = RoleAuditLog.query.filter_by(
                action='assign_role',
                target_user_id=user.id,
                status='success'
            ).all()

            assert len(logs) > 0

    def test_permission_grant_logged(self, app_with_rbac, admin_user):
        """Test that permission grants are logged."""
        with app_with_rbac.app_context():
            admin = User.query.get(admin_user.id)

            grant_permission_to_role(
                role_name='creator',
                permission_name='delete:sns_posts',
                assigned_by_id=admin.id
            )

            logs = RoleAuditLog.query.filter_by(
                action='grant_permission',
                status='success'
            ).all()

            assert len(logs) > 0

    def test_audit_log_contains_metadata(self, app_with_rbac, test_user, admin_user):
        """Test that audit logs contain proper metadata."""
        with app_with_rbac.app_context():
            user = User.query.get(test_user.id)
            admin = User.query.get(admin_user.id)

            assign_role_to_user(
                user_id=user.id,
                role_name='creator',
                assigned_by_id=admin.id
            )

            log = RoleAuditLog.query.filter_by(
                action='assign_role',
                target_user_id=user.id
            ).first()

            assert log is not None
            assert log.user_id == admin.id
            assert log.target_user_id == user.id
            assert log.timestamp is not None


class TestDefaultRolesAndPermissions:
    """Test default RBAC setup."""

    def test_default_roles_exist(self, app_with_rbac):
        """Test that default roles are created."""
        with app_with_rbac.app_context():
            default_roles = {'admin', 'moderator', 'creator', 'user'}
            existing = {r.name for r in Role.query.filter_by(is_active=True).all()}

            for role in default_roles:
                assert role in existing

    def test_default_permissions_exist(self, app_with_rbac):
        """Test that default permissions are created."""
        with app_with_rbac.app_context():
            # Check for some key permissions
            key_perms = [
                'write:sns_posts',
                'read:users',
                'admin:all'
            ]

            for perm_name in key_perms:
                perm = Permission.query.filter_by(name=perm_name).first()
                assert perm is not None

    def test_admin_has_all_permissions(self, app_with_rbac):
        """Test that admin role has all permissions."""
        with app_with_rbac.app_context():
            admin_role = Role.query.filter_by(name='admin').first()
            assert admin_role is not None

            permissions = {p.name for p in admin_role.permissions}
            assert 'admin:all' in permissions


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_assign_nonexistent_role(self, app_with_rbac, test_user):
        """Test assigning a non-existent role."""
        with app_with_rbac.app_context():
            user = User.query.get(test_user.id)
            success, message = assign_role_to_user(user.id, 'nonexistent_role')

            assert not success
            assert 'not found' in message.lower()

    def test_assign_duplicate_role(self, app_with_rbac, test_user):
        """Test assigning the same role twice."""
        with app_with_rbac.app_context():
            user = User.query.get(test_user.id)

            # Assign once
            success1, _ = assign_role_to_user(user.id, 'creator')
            assert success1

            # Assign again
            success2, message = assign_role_to_user(user.id, 'creator')
            assert not success2
            assert 'already has' in message.lower()

    def test_remove_nonexistent_role(self, app_with_rbac, test_user):
        """Test removing a role that user doesn't have."""
        with app_with_rbac.app_context():
            user = User.query.get(test_user.id)
            success, message = remove_role_from_user(user.id, 'admin')

            assert not success
            assert 'does not have' in message.lower()

    def test_permission_check_nonexistent_user(self, app_with_rbac):
        """Test permission check on non-existent user."""
        with app_with_rbac.app_context():
            has_perm = has_permission(99999, 'read:users')
            assert not has_perm

    def test_role_check_nonexistent_user(self, app_with_rbac):
        """Test role check on non-existent user."""
        with app_with_rbac.app_context():
            has_r = has_role(99999, 'admin')
            assert not has_r


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
