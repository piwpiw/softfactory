# Role-Based Access Control (RBAC) Implementation

## Overview

Complete RBAC system for granular access control across the SoftFactory platform. Implements role-based and permission-based access control with comprehensive audit logging.

**Implementation Date:** 2026-02-26
**Version:** 1.0
**Status:** Production-Ready

---

## Architecture

### Core Components

#### 1. Database Models (backend/models.py)

##### Role Model
```python
class Role:
    name: str                # 'admin', 'moderator', 'creator', 'user'
    description: str         # Role description
    is_active: bool          # Soft-delete flag
    permissions: [Permission] # Many-to-many relationship
    users: [User]           # Many-to-many relationship
```

##### Permission Model
```python
class Permission:
    name: str               # e.g., 'write:sns_posts'
    resource: str          # e.g., 'sns_posts'
    action: str            # e.g., 'write'
    description: str       # Permission description
    is_active: bool        # Enable/disable permission
    roles: [Role]          # Many-to-many relationship
```

##### Junction Tables
- **UserRole:** Links users to roles with timestamps and expiry support
- **RolePermission:** Links roles to permissions

##### RoleAuditLog Model
Tracks all RBAC changes:
```python
class RoleAuditLog:
    action: str            # assign_role, remove_role, grant_permission, etc.
    user_id: int           # Who performed the action
    target_user_id: int    # User affected
    target_role_id: int    # Role affected
    target_permission_id: int  # Permission affected
    status: str            # success/failure
    ip_address: str        # Request IP
    user_agent: str        # Browser info
    timestamp: datetime    # When it happened
```

#### 2. RBAC Module (backend/rbac.py)

Contains decorators, utility functions, and initialization logic.

**Key Functions:**
- `init_rbac()` - Initialize default roles and permissions
- `require_role(*roles)` - Decorator for role-based access
- `require_permission(*permissions)` - Decorator for permission-based access
- `assign_role_to_user(user_id, role_name)` - Assign role
- `remove_role_from_user(user_id, role_name)` - Remove role
- `grant_permission_to_role(role_name, permission_name)` - Grant permission
- `revoke_permission_from_role(role_name, permission_name)` - Revoke permission
- `has_permission(user_id, permission_name)` - Check permission
- `has_role(user_id, role_name)` - Check role

#### 3. RBAC Routes (backend/services/rbac_routes.py)

REST API endpoints for RBAC management:
```
/api/admin/rbac/roles               [GET, POST]   - List/create roles
/api/admin/rbac/roles/<id>          [PUT, DELETE] - Update/delete role
/api/admin/rbac/permissions         [GET, POST]   - List/create permissions
/api/admin/rbac/users/<id>/roles    [GET, POST]   - Get/assign user roles
/api/admin/rbac/roles/<name>/permissions [GET, POST, DELETE] - Manage role permissions
/api/admin/rbac/audit-log           [GET]         - View audit logs
```

---

## Default Roles

### Admin
Full platform access
- **Permissions:** All permissions including `admin:all`
- **Use Case:** Platform administrators

### Moderator
Content and user moderation
- **Permissions:**
  - `moderate:sns_posts`
  - `moderate:users`
  - `read:analytics`
- **Use Case:** Community moderators, support staff

### Creator
Content creation and management
- **Permissions:**
  - `create:sns_posts`
  - `write:sns_posts`
  - `delete:sns_posts`
  - `read:users`
  - `read:analytics`
- **Use Case:** Content creators, business users

### User
Basic platform access
- **Permissions:**
  - `read:sns_posts`
  - `create:sns_posts`
  - `read:users`
- **Use Case:** Regular platform users

---

## Default Permissions

### SNS Posts
- `read:sns_posts` - View posts
- `create:sns_posts` - Create new posts
- `write:sns_posts` - Edit posts
- `delete:sns_posts` - Delete posts
- `moderate:sns_posts` - Moderate posts

### Users
- `read:users` - View user profiles
- `create:users` - Create new users
- `write:users` - Edit user information
- `delete:users` - Delete user accounts
- `moderate:users` - Moderate users

### Payments
- `read:payments` - View payment info
- `write:payments` - Update payments
- `refund:payments` - Process refunds
- `manage:subscriptions` - Manage subscriptions

### Analytics
- `read:analytics` - View analytics
- `export:analytics` - Export data

### Platform
- `admin:all` - Full platform access

---

## Usage Examples

### 1. Using Decorators

#### Require Role
```python
from backend.rbac import require_role
from backend.auth import require_auth

@app.route('/api/admin/dashboard')
@require_auth
@require_role('admin')
def admin_dashboard():
    return {'message': 'Admin dashboard'}
```

#### Require Permission
```python
from backend.rbac import require_permission

@app.route('/api/posts/<id>', methods=['DELETE'])
@require_auth
@require_permission('delete:sns_posts')
def delete_post(id):
    return {'message': 'Post deleted'}
```

#### Multiple Options
```python
# User must have EITHER role
@require_role('admin', 'moderator')
def moderate_content():
    pass

# User must have EITHER permission
@require_permission('write:sns_posts', 'moderate:sns_posts')
def edit_or_moderate_post():
    pass
```

### 2. Programmatic Access Control

#### Check Permission
```python
from backend.rbac import has_permission

if has_permission(user_id, 'write:sns_posts'):
    allow_edit()
else:
    return {'error': 'Forbidden'}, 403
```

#### Check Role
```python
from backend.rbac import has_role

if has_role(user_id, 'admin'):
    show_admin_panel()
```

#### Get User Permissions
```python
from backend.rbac import get_user_permissions

perms = get_user_permissions(user_id)
# Returns: {'read:users', 'write:sns_posts', ...}
```

### 3. Admin Management

#### Assign Role to User
```python
from backend.rbac import assign_role_to_user

success, message = assign_role_to_user(
    user_id=123,
    role_name='creator',
    assigned_by_id=1  # Admin user ID
)
```

#### Grant Permission to Role
```python
from backend.rbac import grant_permission_to_role

success, message = grant_permission_to_role(
    role_name='moderator',
    permission_name='delete:sns_posts',
    assigned_by_id=1
)
```

---

## REST API Examples

### Get All Roles
```bash
GET /api/admin/rbac/roles?include_permissions=true
Authorization: Bearer <token>

Response:
{
  "success": true,
  "roles": [
    {
      "id": 1,
      "name": "admin",
      "description": "Platform administrator",
      "is_active": true,
      "permissions": [
        {"id": 1, "name": "admin:all", ...},
        ...
      ]
    }
  ]
}
```

### Create Role
```bash
POST /api/admin/rbac/roles
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "supervisor",
  "description": "Supervisory role"
}

Response:
{
  "success": true,
  "message": "Role 'supervisor' created successfully",
  "role": {...}
}
```

### Assign Role to User
```bash
POST /api/admin/rbac/users/123/roles
Authorization: Bearer <token>
Content-Type: application/json

{
  "role_name": "creator"
}

Response:
{
  "success": true,
  "message": "Role 'creator' assigned to user 123",
  "user_roles": [...]
}
```

### Get User Permissions
```bash
GET /api/admin/rbac/users/123/permissions
Authorization: Bearer <token>

Response:
{
  "success": true,
  "user_id": 123,
  "roles": ["creator"],
  "permissions": [
    "read:sns_posts",
    "create:sns_posts",
    "write:sns_posts",
    "delete:sns_posts",
    "read:users",
    "read:analytics"
  ]
}
```

### View Audit Log
```bash
GET /api/admin/rbac/audit-log?action=assign_role&limit=50
Authorization: Bearer <token>

Response:
{
  "success": true,
  "total": 127,
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "action": "assign_role",
      "target_type": "user",
      "target_user_id": 123,
      "target_role_id": 3,
      "status": "success",
      "timestamp": "2026-02-26T10:30:00Z"
    },
    ...
  ]
}
```

---

## Security Features

### 1. Audit Logging
All RBAC changes are logged with:
- Who performed the action (user_id)
- What was changed (role, permission)
- Who was affected (target_user_id)
- When it happened (timestamp)
- Where it came from (IP address, user agent)
- Success/failure status

### 2. Decorator-based Protection
- Uses `@require_auth` (innermost) + `@require_role`/`@require_permission` (outer)
- Prevents unauthorized access at route level
- Returns 403 Forbidden for insufficient permissions

### 3. Database Integrity
- Foreign key constraints
- Cascade deletes (soft delete for roles)
- Indexes for fast permission checks

### 4. Audit Trail
- Immutable audit logs
- Timestamps in UTC
- Full error tracking

---

## Performance Optimization

### Indexes
```sql
CREATE INDEX idx_role_name ON roles(name);
CREATE INDEX idx_role_is_active ON roles(is_active);
CREATE INDEX idx_permission_name ON permissions(name);
CREATE INDEX idx_permission_resource ON permissions(resource);
CREATE INDEX idx_rbac_audit_user_id ON role_audit_logs(user_id);
CREATE INDEX idx_rbac_audit_action ON role_audit_logs(action);
CREATE INDEX idx_rbac_audit_timestamp ON role_audit_logs(timestamp);
```

### Caching Opportunities
- Cache user permissions in Redis (with TTL)
- Cache role->permission mappings
- Invalidate on RBAC changes

### Query Optimization
- Use `selectinload()` for role.permissions
- Use `joinedload()` for user.roles
- Batch permission checks

---

## Testing

### Test Coverage
- Unit tests: 40+ tests covering all functions
- Integration tests: API endpoint testing
- Edge cases: Invalid roles, duplicate assignments, etc.

### Run Tests
```bash
pytest backend/tests/test_rbac.py -v
pytest backend/tests/test_rbac.py::TestRoleManagement -v
pytest backend/tests/test_rbac.py::TestPermissionChecking -v
```

---

## Migration Guide

### For Existing Users with Legacy Role Field

The system supports backward compatibility:
```python
# Old system: user.role = 'admin'
# New system: user.roles = [Role(name='admin')]

# Code works with both:
if has_role(user_id, 'admin'):
    # Checks both user.role AND user.roles
```

### Converting to New System

```python
from backend.rbac import assign_role_to_user

# Get users with legacy role
users = User.query.filter(User.role != 'user').all()

for user in users:
    # Assign corresponding role
    assign_role_to_user(user.id, user.role, assigned_by_id=1)
    # Optionally clear legacy field
    # user.role = 'user'
```

---

## Database Diagram

```
users (id, email, role, ...)
  ├─ has many: roles (via user_roles)
  │   └─ user_roles (user_id, role_id, assigned_at, assigned_by_id)
  │       └─ role (id, name, description)
  │           ├─ has many: permissions (via role_permissions)
  │           │   └─ role_permissions (role_id, permission_id, assigned_at)
  │           │       └─ permission (id, name, resource, action)
  │           └─ has many: audit_logs (via role_audit_logs.target_role_id)

role_audit_logs (id, action, target_type, user_id, target_user_id, target_role_id, target_permission_id, timestamp)
```

---

## Configuration

### Environment Variables
```bash
# Optional: Customize initial roles (comma-separated)
RBAC_ROLES=admin,moderator,creator,user

# Optional: Disable RBAC initialization
RBAC_AUTO_INIT=false
```

### Initialization
```python
from backend.rbac import init_rbac

# Called automatically in app startup
# Or manually:
init_rbac()
```

---

## Troubleshooting

### Issue: User still denied after role assignment

**Solution:**
```python
# Check 1: Role exists and is active
role = Role.query.filter_by(name='creator', is_active=True).first()

# Check 2: User has role
user = User.query.get(user_id)
assert any(r.name == 'creator' for r in user.roles)

# Check 3: Role has permission
perms = {p.name for p in role.permissions}
assert 'write:sns_posts' in perms
```

### Issue: Decorator returns 401 instead of 403

**Solution:**
- Ensure `@require_auth` is the innermost decorator
- Check token validity and user existence

```python
@app.route('/api/endpoint')
@require_permission('write:data')  # Outer
@require_auth                      # Inner (applies first)
def endpoint():
    pass
```

### Issue: Audit logs not appearing

**Solution:**
```python
# Check audit log existence
from backend.models import RoleAuditLog
logs = RoleAuditLog.query.all()

# Verify database commit
db.session.commit()

# Check request context
if request:
    print(request.remote_addr)
```

---

## Future Enhancements

1. **Temporary Role Assignments**
   - Use `expires_at` field in UserRole
   - Auto-expire roles after date

2. **Permission Groups**
   - Group related permissions
   - Assign groups to roles

3. **Resource-level Permissions**
   - User can only moderate their own posts
   - Role-based + resource-based

4. **API Token Scopes**
   - Limit API token permissions
   - Separate from user permissions

5. **Permission Inheritance**
   - Parent-child role hierarchy
   - Inherit permissions from parent

---

## Support & Contact

For issues or questions:
- Check logs: `docker logs softfactory`
- Review audit trail: `/api/admin/rbac/audit-log`
- Test decorators: `pytest backend/tests/test_rbac.py -v`

---

**Implementation Details:**
- **Files Modified:** backend/models.py
- **Files Created:** backend/rbac.py, backend/services/rbac_routes.py, backend/tests/test_rbac.py
- **Lines of Code:** 1,500+ (models, decorators, routes, tests)
- **Test Coverage:** 40+ tests
- **Documentation:** Comprehensive with examples
