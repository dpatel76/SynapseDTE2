# RBAC Implementation Analysis for SynapseDTE

## Executive Summary

The SynapseDTE project has a comprehensive RBAC (Role-Based Access Control) system built, but it is **currently disabled** via a feature flag (`use_rbac: bool = False` in config.py). The system currently relies on hardcoded role-based checks throughout the codebase, creating maintenance challenges and security risks.

## Current State Analysis

### 1. RBAC Feature Flag Status

**Location**: `/app/core/config.py` (lines 123-126)
```python
# RBAC Configuration
use_rbac: bool = False  # Feature flag for RBAC system
rbac_fallback_to_roles: bool = True  # Fallback to role-based checks if RBAC fails
rbac_cache_ttl: int = 300  # Cache TTL in seconds for permission checks
```

The RBAC system is **disabled by default**, causing all permission checks to fall back to legacy role-based authentication.

### 2. Hardcoded Roles Throughout Codebase

The system defines 6 primary roles that are hardcoded in multiple locations:

1. **Tester** - Executes test procedures
2. **Test Manager** - Manages test cycles and assignments
3. **Report Owner** - Owns and approves reports
4. **Report Owner Executive** - Executive oversight of reports
5. **Data Provider** - Provides data for testing
6. **CDO** - Chief Data Officer role for LOB management

### 3. Duplicate Permission Logic

#### Backend Duplication

1. **`app/core/security.py`** (lines 25-51) - Hardcoded role permissions:
```python
ROLE_PERMISSIONS = {
    "Admin": ["*"],
    "Test Manager": ["cycles.*", "reports.read", "users.read", ...],
    "Tester": ["planning.*", "scoping.*", "testing.*", ...],
    // ... more hardcoded permissions
}
```

2. **`app/core/auth.py`** (lines 166-194) - UserRoles class with hardcoded values:
```python
class UserRoles:
    TESTER = "Tester"
    TEST_MANAGER = "Test Manager"
    REPORT_OWNER = "Report Owner"
    // ... etc
```

3. **`app/core/permissions.py`** (lines 217-356) - Legacy role mapping:
```python
role_permission_map = {
    "Admin": True,
    "Test Manager": {
        "cycles": ["create", "read", "update", "delete"],
        // ... more mappings
    }
}
```

4. **API Endpoints** - Inline role checks (example from `scoping.py`):
```python
async def require_tester(current_user: Any = Depends(get_current_user)) -> Any:
    if current_user.role != "Tester":
        raise HTTPException(status_code=403, detail="Access denied. Tester role required.")
```

#### Frontend Duplication

1. **`frontend/src/types/api.ts`** (lines 15-24) - Hardcoded enum:
```typescript
export enum UserRole {
  ADMIN = 'Admin',
  TEST_MANAGER = 'Test Manager',
  REPORT_OWNER = 'Report Owner',
  // ... etc
}
```

2. **`frontend/src/contexts/PermissionContext.tsx`** (lines 121-165) - Fallback permissions:
```typescript
function getRoleDefaultPermissions(role: UserRole): string[] {
    const rolePermissions: Record<string, string[]> = {
        [UserRole.ADMIN]: ['*:*'],
        [UserRole.TEST_MANAGER]: ['cycles:create', 'cycles:read', ...],
        // ... more hardcoded permissions
    }
}
```

### 4. RBAC System Architecture (Currently Unused)

Despite being disabled, the system has a complete RBAC implementation:

#### Database Models (`app/models/rbac.py`)
- `Permission` - Defines resource:action pairs
- `Role` - Groups of permissions
- `RolePermission` - Many-to-many role-permission mapping
- `UserRole` - User-role assignments with expiration support
- `UserPermission` - Direct user permissions (override capability)
- `ResourcePermission` - Resource-level permissions (e.g., specific report access)
- `RoleHierarchy` - Role inheritance support
- `PermissionAuditLog` - Audit trail for permission changes

#### RBAC API Endpoints (`app/api/v1/endpoints/admin_rbac.py`)
- Full CRUD for permissions and roles
- Role-permission management with validation
- User permission queries (direct + role-based)
- Resource-level permission grants
- Audit log access

#### Permission Service (`app/services/permission_service.py`)
- Centralized permission checking with caching
- Priority order: Admin → Direct User → Resource Level → Role
- TTL cache for performance

### 5. Missing or Incomplete RBAC Data

1. **No seed data execution** - The `seed_rbac_permissions.py` script exists but appears not to be run during setup
2. **Empty permission tables** - RBAC tables are created but not populated
3. **No migration from roles to RBAC** - Users have roles but no corresponding RBAC entries
4. **Frontend expects RBAC for admin only** - Non-admin users always fall back to hardcoded permissions

### 6. Security Vulnerabilities

1. **Inconsistent enforcement** - Different endpoints use different permission checking methods
2. **No resource-level checks** - Users can access any report/cycle if they have the role
3. **Missing validation** - Some endpoints lack any permission checks
4. **Hardcoded role names** - Changes require code modifications in multiple files
5. **No permission inheritance** - Role hierarchy exists but unused

### 7. Why RBAC is Disabled

Based on the analysis, RBAC is likely disabled because:

1. **Incomplete data migration** - No automated migration from role-based to RBAC system
2. **Frontend integration issues** - Frontend falls back to hardcoded permissions for non-admin users
3. **Missing seed data** - RBAC tables exist but aren't populated with initial permissions
4. **Testing concerns** - Switching to RBAC would break existing role-based tests
5. **Backward compatibility** - Existing deployments rely on role-based checks

## Recommendations

### Immediate Actions

1. **Enable RBAC for new deployments**:
   - Set `use_rbac: true` in config for new environments
   - Run seed scripts during deployment
   - Maintain backward compatibility with feature flag

2. **Create migration scripts**:
   - Map existing roles to RBAC roles
   - Generate user-role assignments from current user.role field
   - Populate permission tables from rbac_config.py

3. **Fix frontend integration**:
   - Remove hardcoded role checks in PermissionContext
   - Always use RBAC API when enabled
   - Cache permissions appropriately

### Long-term Improvements

1. **Remove duplicate permission logic**:
   - Centralize all permission definitions in RBAC system
   - Remove hardcoded role arrays
   - Use permission decorators consistently

2. **Implement resource-level security**:
   - Add report/cycle ownership checks
   - Use ResourcePermission for fine-grained access
   - Implement LOB-based access controls

3. **Enhance audit capabilities**:
   - Log all permission checks (not just changes)
   - Add permission denial reasons
   - Create compliance reports

4. **Testing strategy**:
   - Create RBAC-specific test suites
   - Add permission boundary tests
   - Validate role restrictions work correctly

## Conclusion

The SynapseDTE project has a well-designed RBAC system that is currently disabled due to incomplete implementation and data migration challenges. The reliance on hardcoded roles creates significant technical debt and security risks. Enabling RBAC would provide better security, easier maintenance, and more flexible access control, but requires careful migration planning and testing to avoid breaking existing functionality.