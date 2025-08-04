# Database-Driven RBAC Enhancement Proposal

## Executive Summary

Transform the current hardcoded role-based access control into a flexible, database-driven RBAC system that allows dynamic permission management through an admin UI.

## Proposed Architecture

### 1. Database Schema

```sql
-- Core RBAC Tables
CREATE TABLE permissions (
    permission_id SERIAL PRIMARY KEY,
    resource VARCHAR(100) NOT NULL,      -- e.g., 'cycles', 'reports', 'planning'
    action VARCHAR(50) NOT NULL,         -- e.g., 'create', 'read', 'update', 'delete', 'execute'
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(resource, action)
);

CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,     -- System roles cannot be deleted
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(permission_id) ON DELETE CASCADE,
    granted_by INTEGER REFERENCES users(user_id),
    granted_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(role_id) ON DELETE CASCADE,
    assigned_by INTEGER REFERENCES users(user_id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,                -- For temporary role assignments
    PRIMARY KEY (user_id, role_id)
);

-- Direct user permissions (overrides role permissions)
CREATE TABLE user_permissions (
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(permission_id) ON DELETE CASCADE,
    granted BOOLEAN DEFAULT TRUE,        -- Can be used to explicitly deny
    granted_by INTEGER REFERENCES users(user_id),
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    PRIMARY KEY (user_id, permission_id)
);

-- Resource-level permissions
CREATE TABLE resource_permissions (
    resource_permission_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,  -- e.g., 'report', 'cycle', 'lob'
    resource_id INTEGER NOT NULL,
    permission_id INTEGER REFERENCES permissions(permission_id) ON DELETE CASCADE,
    granted BOOLEAN DEFAULT TRUE,
    granted_by INTEGER REFERENCES users(user_id),
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(user_id, resource_type, resource_id, permission_id)
);

-- Role hierarchy for inheritance
CREATE TABLE role_hierarchy (
    parent_role_id INTEGER REFERENCES roles(role_id) ON DELETE CASCADE,
    child_role_id INTEGER REFERENCES roles(role_id) ON DELETE CASCADE,
    PRIMARY KEY (parent_role_id, child_role_id)
);

-- Permission audit log
CREATE TABLE permission_audit_log (
    audit_id SERIAL PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,    -- 'grant', 'revoke', 'expire'
    target_type VARCHAR(50) NOT NULL,    -- 'user', 'role'
    target_id INTEGER NOT NULL,
    permission_id INTEGER REFERENCES permissions(permission_id),
    role_id INTEGER REFERENCES roles(role_id),
    performed_by INTEGER REFERENCES users(user_id),
    performed_at TIMESTAMP DEFAULT NOW(),
    reason TEXT
);
```

### 2. Core Components

#### A. Permission Service (`app/services/permission_service.py`)

```python
from typing import List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rbac import Permission, Role, UserRole, UserPermission

class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache = {}  # Permission cache
    
    async def check_permission(
        self, 
        user_id: int, 
        resource: str, 
        action: str,
        resource_id: Optional[int] = None
    ) -> bool:
        """Check if user has permission for resource:action"""
        # Check cache first
        cache_key = f"{user_id}:{resource}:{action}:{resource_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Check direct user permissions (highest priority)
        if await self._check_user_permission(user_id, resource, action):
            self._cache[cache_key] = True
            return True
        
        # Check resource-level permissions
        if resource_id and await self._check_resource_permission(
            user_id, resource, action, resource_id
        ):
            self._cache[cache_key] = True
            return True
        
        # Check role permissions (with inheritance)
        if await self._check_role_permission(user_id, resource, action):
            self._cache[cache_key] = True
            return True
        
        self._cache[cache_key] = False
        return False
    
    async def get_user_permissions(self, user_id: int) -> Set[str]:
        """Get all permissions for a user"""
        permissions = set()
        
        # Get direct permissions
        user_perms = await self._get_direct_user_permissions(user_id)
        permissions.update(user_perms)
        
        # Get role permissions
        role_perms = await self._get_role_permissions(user_id)
        permissions.update(role_perms)
        
        return permissions
    
    async def grant_permission_to_role(
        self, 
        role_id: int, 
        permission_id: int, 
        granted_by: int
    ):
        """Grant permission to role"""
        # Implementation
        pass
    
    async def grant_permission_to_user(
        self, 
        user_id: int, 
        permission_id: int, 
        granted_by: int,
        expires_at: Optional[datetime] = None
    ):
        """Grant permission directly to user"""
        # Implementation
        pass
```

#### B. Permission Decorator (`app/core/permissions.py`)

```python
from functools import wraps
from typing import Optional, List, Union

def require_permission(
    resource: str, 
    action: str, 
    resource_id_param: Optional[str] = None
):
    """Decorator to check permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from request context
            request = kwargs.get('request')
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise AuthorizationException("User not authenticated")
            
            # Get resource ID if specified
            resource_id = None
            if resource_id_param:
                resource_id = kwargs.get(resource_id_param)
            
            # Check permission
            permission_service = get_permission_service()
            has_permission = await permission_service.check_permission(
                current_user.user_id,
                resource,
                action,
                resource_id
            )
            
            if not has_permission:
                raise AuthorizationException(
                    f"Permission denied: {resource}:{action}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage example:
@router.post("/cycles")
@require_permission("cycles", "create")
async def create_cycle(...):
    pass

@router.put("/reports/{report_id}")
@require_permission("reports", "update", resource_id_param="report_id")
async def update_report(report_id: int, ...):
    pass
```

#### C. Migration Strategy

```python
# Migration script to convert existing roles
ROLE_PERMISSION_MAPPING = {
    "Admin": ["*:*"],  # All permissions
    "Test Manager": [
        "cycles:create", "cycles:read", "cycles:update",
        "reports:read", "reports:assign",
        "users:read", "users:assign",
        "workflow:approve"
    ],
    "Tester": [
        "planning:execute", "planning:upload", "planning:create_attributes",
        "scoping:execute", "scoping:submit",
        "testing:execute", "testing:submit",
        "observations:create", "observations:submit"
    ],
    "Report Owner": [
        "reports:read", "reports:approve",
        "scoping:approve",
        "testing:review",
        "observations:approve"
    ],
    "Report Owner Executive": [
        "reports:read", "reports:override",
        "workflow:override",
        "observations:override"
    ],
    "Data Provider": [
        "data_provider:read", "data_provider:upload",
        "request_info:provide"
    ],
    "CDO": [
        "lobs:read", "lobs:manage",
        "data_provider:assign", "data_provider:escalate"
    ]
}
```

### 3. Admin UI Components

#### A. Permission Management Page

```typescript
// PermissionManagement.tsx
interface Permission {
  id: number;
  resource: string;
  action: string;
  description: string;
}

interface Role {
  id: number;
  name: string;
  description: string;
  permissions: Permission[];
  userCount: number;
}

const PermissionManagement: React.FC = () => {
  return (
    <Box>
      <Tabs>
        <Tab label="Roles" />
        <Tab label="Permissions" />
        <Tab label="Users" />
        <Tab label="Audit Log" />
      </Tabs>
      
      <TabPanel value={0}>
        <RoleManagement />
      </TabPanel>
      
      <TabPanel value={1}>
        <PermissionList />
      </TabPanel>
      
      <TabPanel value={2}>
        <UserPermissionAssignment />
      </TabPanel>
      
      <TabPanel value={3}>
        <PermissionAuditLog />
      </TabPanel>
    </Box>
  );
};
```

#### B. Role Management Interface

```typescript
const RoleManagement: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  
  return (
    <Grid container spacing={3}>
      <Grid item xs={4}>
        <Paper>
          <Typography variant="h6">Roles</Typography>
          <List>
            {roles.map(role => (
              <ListItem 
                key={role.id}
                button
                onClick={() => setSelectedRole(role)}
              >
                <ListItemText 
                  primary={role.name}
                  secondary={`${role.userCount} users`}
                />
              </ListItem>
            ))}
          </List>
          <Button
            variant="contained"
            onClick={handleCreateRole}
          >
            Create New Role
          </Button>
        </Paper>
      </Grid>
      
      <Grid item xs={8}>
        {selectedRole && (
          <RolePermissionEditor 
            role={selectedRole}
            onUpdate={handleRoleUpdate}
          />
        )}
      </Grid>
    </Grid>
  );
};
```

### 4. API Endpoints

```python
# app/api/v1/endpoints/admin_rbac.py

@router.get("/permissions", response_model=List[PermissionSchema])
async def list_permissions(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all available permissions"""
    pass

@router.post("/roles", response_model=RoleSchema)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new role"""
    pass

@router.post("/roles/{role_id}/permissions")
async def assign_permissions_to_role(
    role_id: int,
    permission_ids: List[int],
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Assign permissions to role"""
    pass

@router.post("/users/{user_id}/roles")
async def assign_role_to_user(
    user_id: int,
    role_id: int,
    expires_at: Optional[datetime] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Assign role to user"""
    pass

@router.get("/audit-log", response_model=List[PermissionAuditSchema])
async def get_permission_audit_log(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get permission change audit log"""
    pass
```

### 5. Implementation Benefits

1. **Flexibility**: Create custom roles with specific permissions
2. **Granularity**: Control access at resource level
3. **Auditability**: Complete audit trail of permission changes
4. **Scalability**: Easy to add new permissions without code changes
5. **Security**: Principle of least privilege, temporary permissions
6. **Usability**: Admin UI for permission management
7. **Performance**: Caching for permission checks
8. **Maintainability**: Centralized permission logic

### 6. Migration Plan

1. **Phase 1**: Create database schema and models
2. **Phase 2**: Implement permission service
3. **Phase 3**: Create migration script for existing roles
4. **Phase 4**: Update endpoints to use new permission system
5. **Phase 5**: Build admin UI
6. **Phase 6**: Gradual rollout with fallback to old system
7. **Phase 7**: Remove old hardcoded system

### 7. Example Usage

```python
# Before (hardcoded)
@router.post("/cycles")
async def create_cycle(
    current_user: User = Depends(require_roles([UserRoles.TEST_MANAGER]))
):
    pass

# After (flexible)
@router.post("/cycles")
@require_permission("cycles", "create")
async def create_cycle(
    current_user: User = Depends(get_current_user)
):
    pass

# Resource-level permission
@router.put("/reports/{report_id}")
@require_permission("reports", "update", resource_id_param="report_id")
async def update_report(
    report_id: int,
    current_user: User = Depends(get_current_user)
):
    pass
```

This enhancement provides a complete, flexible RBAC system that can grow with your application's needs.