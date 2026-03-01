# RBAC Quick Reference

## Decorators

```python
# Require specific role(s)
@require_role('admin')
@require_role('admin', 'moderator')  # OR logic

# Require specific permission(s)
@require_permission('write:sns_posts')
@require_permission('write:sns_posts', 'moderate:sns_posts')  # OR logic

# Shortcut for admin
@require_admin
```

## Utility Functions

```python
from backend.rbac import (
    has_permission, has_role, get_user_permissions,
    get_user_roles, assign_role_to_user, remove_role_from_user
)

# Check permission
if has_permission(user_id, 'write:sns_posts'):
    allow_edit()

# Check role
if has_role(user_id, 'admin'):
    show_admin_panel()

# Get all permissions
perms = get_user_permissions(user_id)  # Returns Set[str]

# Get all roles
roles = get_user_roles(user_id)  # Returns List[str]

# Assign role
success, msg = assign_role_to_user(user_id, 'creator', assigned_by_id=1)

# Remove role
success, msg = remove_role_from_user(user_id, 'creator', assigned_by_id=1)
```

## REST API Endpoints

### Roles
```bash
GET /api/admin/rbac/roles                    # List roles
POST /api/admin/rbac/roles                   # Create role
PUT /api/admin/rbac/roles/<id>               # Update role
DELETE /api/admin/rbac/roles/<id>            # Delete role
```

### Users-Roles
```bash
GET /api/admin/rbac/users/<id>/roles         # Get user roles
POST /api/admin/rbac/users/<id>/roles        # Assign role
DELETE /api/admin/rbac/users/<id>/roles/<name> # Remove role
GET /api/admin/rbac/users/<id>/permissions   # Get user permissions
```

### Permissions
```bash
GET /api/admin/rbac/permissions              # List permissions
POST /api/admin/rbac/permissions             # Create permission
```

### Role-Permissions
```bash
GET /api/admin/rbac/roles/<name>/permissions # Get role permissions
POST /api/admin/rbac/roles/<name>/permissions # Grant permission
DELETE /api/admin/rbac/roles/<name>/permissions/<perm> # Revoke
```

### Audit Log
```bash
GET /api/admin/rbac/audit-log                # View all logs
GET /api/admin/rbac/audit-log/user/<id>     # View user's actions
POST /api/admin/rbac/users/<id>/check-permission # Check permission
```

## Default Roles

| Role | Permissions | Use Case |
|------|-------------|----------|
| admin | All (admin:all) | Platform admins |
| moderator | Moderate posts/users, read analytics | Content moderators |
| creator | Create/edit/delete posts, read analytics | Content creators |
| user | Read posts, create posts, read users | Regular users |

## Default Permissions

| Resource | Actions |
|----------|---------|
| sns_posts | read, create, write, delete, moderate |
| users | read, create, write, delete, moderate |
| payments | read, write, refund, manage_subscriptions |
| analytics | read, export |
| platform | admin_all |

## Common Patterns

### Protect Admin Endpoint
```python
@app.route('/api/admin/users')
@require_auth
@require_role('admin')
def list_all_users():
    return get_users()
```

### Protect Content Endpoint
```python
@app.route('/api/posts/<id>', methods=['DELETE'])
@require_auth
@require_permission('delete:sns_posts')
def delete_post(id):
    return delete_post_by_id(id)
```

### Check Before Action
```python
from backend.rbac import has_permission

@app.route('/api/posts', methods=['POST'])
@require_auth
def create_post():
    if not has_permission(g.user['user_id'], 'create:sns_posts'):
        return {'error': 'No permission'}, 403
    return create_new_post()
```

### Multiple Options
```python
@app.route('/api/posts/<id>', methods=['PATCH'])
@require_auth
@require_permission('write:sns_posts', 'moderate:sns_posts')
def edit_or_moderate_post(id):
    return edit_post(id)
```

## Troubleshooting

```python
# Debug: Check if user has role
from backend.rbac import has_role, get_user_roles
print(f"Roles: {get_user_roles(user_id)}")
print(f"Is admin: {has_role(user_id, 'admin')}")

# Debug: Check if user has permission
from backend.rbac import has_permission, get_user_permissions
print(f"Permissions: {get_user_permissions(user_id)}")
print(f"Can write: {has_permission(user_id, 'write:sns_posts')}")

# Debug: Check audit log
from backend.models import RoleAuditLog
logs = RoleAuditLog.query.filter_by(user_id=admin_id).all()
for log in logs:
    print(f"{log.action}: {log.details} ({log.status})")
```

## Integration Checklist

- [ ] Import RBAC module: `from backend.rbac import ...`
- [ ] Add decorators to protected routes
- [ ] Test with curl or Postman
- [ ] Check audit logs
- [ ] Assign test users to roles
- [ ] Verify permissions work as expected
- [ ] Document new permissions in shared-intelligence/

## Performance Tips

1. **Cache permissions** in Redis with TTL
2. **Batch checks** for multiple permissions
3. **Use indexes** on (user_id, role_id) queries
4. **Avoid N+1** with eager loading: `selectinload()`
5. **Log sparingly** - only critical changes

## Migration Notes

- Old `user.role` field still works (backward compatible)
- New system uses `user.roles` (many-to-many)
- Both are checked in `has_role()`, `get_user_roles()`, etc.
- Migrate gradually - no rush to convert

## Common Errors

```python
# ❌ Decorator order wrong
@require_role('admin')
@require_auth  # Will fail - auth happens after role check

# ✅ Correct order
@require_role('admin')
@require_auth  # Auth checks first

# ❌ Typo in permission name
@require_permission('write:posts')  # Should be 'write:sns_posts'

# ✅ Use exact permission name
@require_permission('write:sns_posts')
```

---

**Quick Commands:**

```bash
# Initialize RBAC
python -c "from backend.rbac import init_rbac; init_rbac()"

# Run tests
pytest backend/tests/test_rbac.py -v

# Check setup
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/admin/rbac/roles
```
