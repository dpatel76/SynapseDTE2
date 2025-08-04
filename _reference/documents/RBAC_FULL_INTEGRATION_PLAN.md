# RBAC Full Integration Plan (Updated)

## Executive Summary

This document outlines a comprehensive plan to complete the Role-Based Access Control (RBAC) integration in the SynapseDT platform. While the backend infrastructure is largely complete, significant work remains to migrate existing endpoints and implement frontend permission management.

## Current State Assessment

### ✅ Already Implemented

1. **Backend Infrastructure (90% Complete)**
   - Full RBAC database models with role hierarchy and resource permissions
   - Comprehensive PermissionService with caching and audit logging
   - Modern permission decorators (@require_permission, @require_any_permission, @require_all_permissions)
   - Complete RBAC configuration with all resources and actions defined
   - Admin API endpoints for RBAC management
   - Database migrations for all RBAC tables

2. **Frontend Infrastructure (30% Complete)**
   - Basic RBACManagementPage component
   - Simple role and permission viewing
   - User role assignment UI

### ❌ Missing Components

1. **Backend Gaps**
   - 90% of API endpoints still use old RoleChecker system
   - Permission and resource data not populated in database
   - No integration with JWT tokens

2. **Frontend Gaps**
   - No permission context or hooks
   - No permission-based UI rendering
   - Missing permission checks in components
   - Limited RBAC management features

## Updated Implementation Plan

### Phase 0: Database Population (Day 1 - Morning)

**Priority: CRITICAL - Must be done first**

1. **Run Resource Population Script**
```bash
python scripts/populate_rbac_resources.py
```

2. **Create Permission Seeding Script**
```python
# scripts/seed_rbac_permissions.py
# Generate all permissions from rbac_config.py
# Create default roles with permissions
# Assign admin role to admin users
```

3. **Verify Population**
```sql
SELECT COUNT(*) FROM resources;
SELECT COUNT(*) FROM permissions;
SELECT COUNT(*) FROM roles;
```

### Phase 1: Frontend Permission Infrastructure (Days 1-2)

**Priority: HIGH - Enables all other frontend work**

#### Day 1: Permission Context and Hooks

1. **Create Permission Context**
```typescript
// frontend/src/contexts/PermissionContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext';
import { rbacApi } from '../api/rbac';

interface PermissionContextType {
  permissions: Set<string>;
  roles: string[];
  hasPermission: (resource: string, action: string) => boolean;
  hasAnyPermission: (...permissions: [string, string][]) => boolean;
  hasAllPermissions: (...permissions: [string, string][]) => boolean;
  hasRole: (role: string) => boolean;
  isLoading: boolean;
  refresh: () => Promise<void>;
}

const PermissionContext = createContext<PermissionContextType | null>(null);

export const PermissionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [permissions, setPermissions] = useState<Set<string>>(new Set());
  const [roles, setRoles] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated && user) {
      loadUserPermissions();
    } else {
      setPermissions(new Set());
      setRoles([]);
      setIsLoading(false);
    }
  }, [isAuthenticated, user]);

  const loadUserPermissions = async () => {
    try {
      const response = await rbacApi.getUserPermissions(user!.user_id);
      setPermissions(new Set(response.data.all_permissions));
      setRoles(response.data.roles || []);
    } catch (error) {
      console.error('Failed to load permissions:', error);
      // Fallback to role-based permissions
      const rolePermissions = getRoleDefaultPermissions(user!.role);
      setPermissions(new Set(rolePermissions));
    } finally {
      setIsLoading(false);
    }
  };

  const hasPermission = (resource: string, action: string): boolean => {
    return permissions.has(`${resource}:${action}`);
  };

  const hasAnyPermission = (...perms: [string, string][]): boolean => {
    return perms.some(([resource, action]) => hasPermission(resource, action));
  };

  const hasAllPermissions = (...perms: [string, string][]): boolean => {
    return perms.every(([resource, action]) => hasPermission(resource, action));
  };

  const hasRole = (role: string): boolean => {
    return roles.includes(role);
  };

  const refresh = async () => {
    await loadUserPermissions();
  };

  return (
    <PermissionContext.Provider value={{
      permissions,
      roles,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      hasRole,
      isLoading,
      refresh
    }}>
      {children}
    </PermissionContext.Provider>
  );
};

export const usePermissions = () => {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error('usePermissions must be used within PermissionProvider');
  }
  return context;
};

// Fallback for legacy role support
function getRoleDefaultPermissions(role: string): string[] {
  const rolePermissions: Record<string, string[]> = {
    'ADMIN': ['*:*'], // All permissions
    'TEST_MANAGER': [
      'cycles:create', 'cycles:read', 'cycles:update', 'cycles:delete',
      'reports:read', 'reports:assign', 'planning:approve', 'scoping:approve'
    ],
    'TESTER': [
      'cycles:read', 'reports:read', 'planning:execute', 'scoping:execute',
      'testing:execute', 'observations:create'
    ],
    'REPORT_OWNER': [
      'reports:read', 'reports:approve', 'planning:read', 'scoping:read'
    ],
    'DATA_PROVIDER': [
      'data_provider:read', 'data_provider:upload'
    ],
    'CDO': [
      'lobs:read', 'dashboards:executive'
    ]
  };
  return rolePermissions[role] || [];
}
```

2. **Create Permission Components**
```typescript
// frontend/src/components/auth/PermissionGate.tsx
import React from 'react';
import { usePermissions } from '../../contexts/PermissionContext';
import { Alert } from '@mui/material';

interface PermissionGateProps {
  resource: string;
  action: string;
  fallback?: React.ReactNode;
  showError?: boolean;
  children: React.ReactNode;
}

export const PermissionGate: React.FC<PermissionGateProps> = ({
  resource,
  action,
  fallback = null,
  showError = false,
  children
}) => {
  const { hasPermission, isLoading } = usePermissions();
  
  if (isLoading) {
    return null; // Or loading spinner
  }
  
  if (hasPermission(resource, action)) {
    return <>{children}</>;
  }
  
  if (showError) {
    return (
      <Alert severity="error">
        You don't have permission to {action} {resource}
      </Alert>
    );
  }
  
  return <>{fallback}</>;
};

// Conditional rendering hook
export const useConditionalRender = (resource: string, action: string) => {
  const { hasPermission } = usePermissions();
  return hasPermission(resource, action);
};
```

3. **Update App.tsx to Include PermissionProvider**
```typescript
// frontend/src/App.tsx
import { PermissionProvider } from './contexts/PermissionContext';

function App() {
  return (
    <AuthProvider>
      <PermissionProvider>
        <Router>
          {/* Routes */}
        </Router>
      </PermissionProvider>
    </AuthProvider>
  );
}
```

#### Day 2: Enhanced RBAC UI Components

4. **Create RBAC API Client**
```typescript
// frontend/src/api/rbac.ts
import apiClient from './client';

export const rbacApi = {
  // Permissions
  getPermissions: (params?: { skip?: number; limit?: number; resource?: string }) => 
    apiClient.get('/api/v1/admin/rbac/permissions', { params }),
  
  createPermission: (data: { resource: string; action: string; description?: string }) => 
    apiClient.post('/api/v1/admin/rbac/permissions', data),
  
  deletePermission: (id: number) => 
    apiClient.delete(`/api/v1/admin/rbac/permissions/${id}`),
  
  // Roles
  getRoles: (params?: { skip?: number; limit?: number }) => 
    apiClient.get('/api/v1/admin/rbac/roles', { params }),
  
  createRole: (data: { name: string; description?: string; is_system: boolean }) => 
    apiClient.post('/api/v1/admin/rbac/roles', data),
  
  updateRole: (id: number, data: { name?: string; description?: string }) => 
    apiClient.put(`/api/v1/admin/rbac/roles/${id}`, data),
  
  deleteRole: (id: number) => 
    apiClient.delete(`/api/v1/admin/rbac/roles/${id}`),
  
  // Role Permissions
  getRolePermissions: (roleId: number) => 
    apiClient.get(`/api/v1/admin/rbac/roles/${roleId}/permissions`),
  
  updateRolePermissions: (roleId: number, permissionIds: number[]) => 
    apiClient.put(`/api/v1/admin/rbac/roles/${roleId}/permissions`, { permission_ids: permissionIds }),
  
  // User Permissions
  getUserPermissions: (userId: number) => 
    apiClient.get(`/api/v1/admin/rbac/users/${userId}/permissions`),
  
  getUserRoles: (userId: number) => 
    apiClient.get(`/api/v1/admin/rbac/users/${userId}/roles`),
  
  assignUserRole: (userId: number, roleId: number, expiresAt?: string) => 
    apiClient.post(`/api/v1/admin/rbac/users/${userId}/roles`, { 
      role_id: roleId, 
      expires_at: expiresAt 
    }),
  
  removeUserRole: (userId: number, roleId: number) => 
    apiClient.delete(`/api/v1/admin/rbac/users/${userId}/roles/${roleId}`),
  
  // Direct Permissions
  grantUserPermission: (userId: number, permissionId: number) => 
    apiClient.post(`/api/v1/admin/rbac/users/${userId}/permissions`, { 
      permission_id: permissionId,
      is_granted: true 
    }),
  
  denyUserPermission: (userId: number, permissionId: number) => 
    apiClient.post(`/api/v1/admin/rbac/users/${userId}/permissions`, { 
      permission_id: permissionId,
      is_granted: false 
    }),
  
  // Resource Permissions
  getResourcePermissions: (resourceType: string, resourceId: string) => 
    apiClient.get(`/api/v1/admin/rbac/resources/${resourceType}/${resourceId}/permissions`),
  
  grantResourcePermission: (data: {
    user_id: number;
    permission_id: number;
    resource_type: string;
    resource_id: string;
  }) => apiClient.post('/api/v1/admin/rbac/resource-permissions', data),
  
  // Audit Log
  getAuditLog: (params?: { 
    skip?: number; 
    limit?: number; 
    user_id?: number;
    action?: string;
    start_date?: string;
    end_date?: string;
  }) => apiClient.get('/api/v1/admin/rbac/audit-log', { params }),
};
```

### Phase 2: Backend API Migration (Days 3-5)

**Priority: HIGH - Critical for security**

#### Day 3: Core Module Migration

1. **Test Cycles Module**
```python
# app/api/v1/endpoints/cycles.py
# Replace all RoleChecker instances with @require_permission

# Before:
if not RoleChecker([UserRoles.TEST_MANAGER])(current_user):
    raise HTTPException(status_code=403)

# After:
@router.post("/", response_model=schemas.TestCycle)
@require_permission("cycles", "create")
async def create_test_cycle(...):
    pass

# Migration for all endpoints:
# - POST /cycles → @require_permission("cycles", "create")
# - GET /cycles → @require_permission("cycles", "read")
# - GET /cycles/{id} → @require_permission("cycles", "read")
# - PUT /cycles/{id} → @require_permission("cycles", "update")
# - DELETE /cycles/{id} → @require_permission("cycles", "delete")
# - POST /cycles/{id}/reports → @require_permission("cycles", "assign")
```

2. **Reports Module**
```python
# app/api/v1/endpoints/reports.py
# Add resource-level permission checks

@router.put("/{report_id}")
@require_permission("reports", "update", resource_id_param="report_id")
async def update_report(
    report_id: int,
    report_update: schemas.ReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    permission_service: PermissionService = Depends(get_permission_service)
):
    # Additional resource-level check
    if not await permission_service.check_resource_permission(
        current_user.user_id, "reports", "update", "report", str(report_id)
    ):
        raise HTTPException(status_code=403, detail="No permission for this report")
    
    # Update logic...
```

#### Day 4: Workflow Phase Modules

3. **Planning Module**
```python
# app/api/v1/endpoints/planning.py
# Migrate all endpoints to use @require_permission

@router.post("/{cycle_id}/reports/{report_id}/start")
@require_permission("planning", "execute")
async def start_planning_phase(...):
    pass

@router.post("/{cycle_id}/reports/{report_id}/attributes/generate")
@require_permission("planning", "generate")
async def generate_attributes(...):
    pass

@router.post("/{cycle_id}/reports/{report_id}/complete")
@require_permission("planning", "complete")
async def complete_planning_phase(...):
    pass
```

4. **Create Migration Helper Script**
```python
# scripts/migrate_endpoints_to_rbac.py
import ast
import os
from pathlib import Path

def migrate_endpoint_file(filepath: Path):
    """Automatically migrate RoleChecker to @require_permission"""
    # Read file
    # Parse AST
    # Find RoleChecker usage
    # Replace with appropriate @require_permission
    # Write updated file
    pass

# Run on all endpoint files
endpoint_dir = Path("app/api/v1/endpoints")
for file in endpoint_dir.glob("*.py"):
    if file.name not in ["__init__.py", "admin_rbac.py"]:
        migrate_endpoint_file(file)
```

#### Day 5: Admin and Special Modules

5. **Admin Endpoints**
```python
# app/api/v1/endpoints/admin.py
# Add granular admin permissions

@router.post("/users")
@require_permission("users", "create")
async def create_user(...):
    pass

@router.put("/system-settings")
@require_permission("system", "configure")
async def update_system_settings(...):
    pass

@router.post("/data-sources")
@require_permission("data_sources", "create")
async def create_data_source(...):
    pass
```

6. **Create Feature Flag for Gradual Rollout**
```python
# app/core/config.py
class Settings(BaseSettings):
    USE_RBAC: bool = Field(default=False, env="USE_RBAC")
    RBAC_FALLBACK_TO_ROLES: bool = Field(default=True, env="RBAC_FALLBACK_TO_ROLES")

# app/core/permissions.py
def require_permission(resource: str, action: str, **kwargs):
    def decorator(func):
        if not settings.USE_RBAC:
            # Use legacy role checking
            return require_role(get_legacy_roles(resource, action))(func)
        
        # Use new RBAC system
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # RBAC logic
            pass
        return wrapper
    return decorator
```

### Phase 3: Frontend Permission Integration (Days 6-7)

#### Day 6: Update Core Components

1. **Protected Route Component**
```typescript
// frontend/src/components/auth/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { usePermissions } from '../../contexts/PermissionContext';

interface ProtectedRouteProps {
  resource?: string;
  action?: string;
  requiredRole?: string;
  fallbackPath?: string;
  children: React.ReactElement;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  resource,
  action,
  requiredRole,
  fallbackPath = '/unauthorized',
  children
}) => {
  const { hasPermission, hasRole, isLoading } = usePermissions();
  
  if (isLoading) {
    return <div>Loading permissions...</div>;
  }
  
  const hasAccess = 
    (resource && action && hasPermission(resource, action)) ||
    (requiredRole && hasRole(requiredRole));
  
  if (!hasAccess) {
    return <Navigate to={fallbackPath} replace />;
  }
  
  return children;
};
```

2. **Update Navigation**
```typescript
// frontend/src/components/layout/Sidebar.tsx
import { usePermissions } from '../../contexts/PermissionContext';

const Sidebar = () => {
  const { hasPermission } = usePermissions();
  
  const navigationItems = [
    {
      title: 'Dashboard',
      path: '/dashboard',
      icon: <Dashboard />,
      show: true // Always show
    },
    {
      title: 'Test Cycles',
      path: '/cycles',
      icon: <Assignment />,
      show: hasPermission('cycles', 'read')
    },
    {
      title: 'Reports',
      path: '/reports',
      icon: <Description />,
      show: hasPermission('reports', 'read')
    },
    {
      title: 'Planning',
      path: '/planning',
      icon: <Timeline />,
      show: hasPermission('planning', 'read')
    },
    {
      title: 'RBAC Management',
      path: '/admin/rbac',
      icon: <Security />,
      show: hasPermission('permissions', 'manage')
    },
    {
      title: 'System Settings',
      path: '/admin/settings',
      icon: <Settings />,
      show: hasPermission('system', 'configure')
    }
  ];
  
  return (
    <Drawer>
      <List>
        {navigationItems
          .filter(item => item.show)
          .map(item => (
            <ListItem key={item.path} button component={Link} to={item.path}>
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.title} />
            </ListItem>
          ))
        }
      </List>
    </Drawer>
  );
};
```

#### Day 7: Update Feature Components

3. **Test Cycles Page**
```typescript
// frontend/src/pages/TestCyclesPage.tsx
import { PermissionGate } from '../components/auth/PermissionGate';
import { usePermissions } from '../contexts/PermissionContext';

const TestCyclesPage = () => {
  const { hasPermission } = usePermissions();
  
  return (
    <Box>
      <Typography variant="h4">Test Cycles</Typography>
      
      <PermissionGate resource="cycles" action="create">
        <Button 
          variant="contained" 
          onClick={handleCreateCycle}
          startIcon={<Add />}
        >
          Create Test Cycle
        </Button>
      </PermissionGate>
      
      <DataGrid
        rows={cycles}
        columns={[
          { field: 'name', headerName: 'Name', flex: 1 },
          { field: 'status', headerName: 'Status', width: 120 },
          {
            field: 'actions',
            headerName: 'Actions',
            width: 200,
            renderCell: (params) => (
              <>
                {hasPermission('cycles', 'update') && (
                  <IconButton onClick={() => handleEdit(params.row)}>
                    <Edit />
                  </IconButton>
                )}
                {hasPermission('cycles', 'delete') && (
                  <IconButton onClick={() => handleDelete(params.row)}>
                    <Delete />
                  </IconButton>
                )}
              </>
            )
          }
        ]}
      />
    </Box>
  );
};
```

4. **Dynamic Dashboard**
```typescript
// frontend/src/pages/DashboardPage.tsx
const DashboardPage = () => {
  const { hasPermission, hasRole } = usePermissions();
  
  // Determine dashboard based on permissions
  if (hasPermission('system', 'admin')) {
    return <AdminDashboard />;
  }
  
  if (hasPermission('cycles', 'create')) {
    return <TestManagerDashboard />;
  }
  
  if (hasPermission('planning', 'execute')) {
    return <TesterDashboard />;
  }
  
  if (hasPermission('reports', 'approve')) {
    return <ReportOwnerDashboard />;
  }
  
  if (hasPermission('data_provider', 'upload')) {
    return <DataProviderDashboard />;
  }
  
  if (hasPermission('lobs', 'manage')) {
    return <CDODashboard />;
  }
  
  // Default dashboard for users with minimal permissions
  return <BasicDashboard />;
};
```

### Phase 4: Testing and Validation (Days 8-9)

#### Day 8: Backend Testing

1. **Permission Service Tests**
```python
# tests/test_rbac_integration.py
import pytest
from app.services.permission_service import PermissionService

@pytest.mark.asyncio
class TestRBACIntegration:
    async def test_permission_check_priority(self, permission_service: PermissionService):
        """Test permission check follows correct priority order"""
        # 1. Admin bypass
        # 2. Direct deny
        # 3. Direct grant
        # 4. Resource-specific
        # 5. Role-based
        pass
    
    async def test_endpoint_permission_enforcement(self, client, test_users):
        """Test that endpoints enforce permissions correctly"""
        # Test each endpoint with different user permissions
        pass
    
    async def test_resource_level_permissions(self):
        """Test resource-specific permission grants"""
        pass
```

2. **API Endpoint Tests**
```python
# tests/test_api_permissions.py
@pytest.mark.asyncio
async def test_cycles_create_requires_permission(client, test_users):
    # User without permission
    response = await client.post(
        "/api/v1/cycles",
        headers={"Authorization": f"Bearer {test_users['tester'].token}"},
        json={"name": "Test Cycle", "description": "Test"}
    )
    assert response.status_code == 403
    
    # User with permission
    response = await client.post(
        "/api/v1/cycles",
        headers={"Authorization": f"Bearer {test_users['test_manager'].token}"},
        json={"name": "Test Cycle", "description": "Test"}
    )
    assert response.status_code == 201
```

#### Day 9: Frontend Testing

3. **Permission Hook Tests**
```typescript
// frontend/src/__tests__/usePermissions.test.tsx
import { renderHook } from '@testing-library/react';
import { usePermissions } from '../contexts/PermissionContext';

describe('usePermissions', () => {
  it('correctly checks single permission', () => {
    const { result } = renderHook(() => usePermissions(), {
      wrapper: createPermissionWrapper(['cycles:read', 'cycles:create'])
    });
    
    expect(result.current.hasPermission('cycles', 'read')).toBe(true);
    expect(result.current.hasPermission('cycles', 'delete')).toBe(false);
  });
  
  it('correctly checks multiple permissions', () => {
    const { result } = renderHook(() => usePermissions(), {
      wrapper: createPermissionWrapper(['cycles:read'])
    });
    
    expect(result.current.hasAnyPermission(
      ['cycles', 'read'],
      ['cycles', 'create']
    )).toBe(true);
    
    expect(result.current.hasAllPermissions(
      ['cycles', 'read'],
      ['cycles', 'create']
    )).toBe(false);
  });
});
```

4. **Component Permission Tests**
```typescript
// frontend/src/__tests__/PermissionGate.test.tsx
describe('PermissionGate', () => {
  it('renders children when permission granted', () => {
    render(
      <PermissionProvider permissions={new Set(['cycles:create'])}>
        <PermissionGate resource="cycles" action="create">
          <button>Create Cycle</button>
        </PermissionGate>
      </PermissionProvider>
    );
    
    expect(screen.getByText('Create Cycle')).toBeInTheDocument();
  });
  
  it('renders fallback when permission denied', () => {
    render(
      <PermissionProvider permissions={new Set()}>
        <PermissionGate 
          resource="cycles" 
          action="create"
          fallback={<div>No permission</div>}
        >
          <button>Create Cycle</button>
        </PermissionGate>
      </PermissionProvider>
    );
    
    expect(screen.queryByText('Create Cycle')).not.toBeInTheDocument();
    expect(screen.getByText('No permission')).toBeInTheDocument();
  });
});
```

### Phase 5: Documentation and Deployment (Day 10)

1. **Update API Documentation**
2. **Create Migration Guide**
3. **Update User Documentation**
4. **Deployment Scripts**

## Migration Strategy

### Gradual Rollout Plan

1. **Week 1: Preparation**
   - Deploy code with USE_RBAC=false
   - Populate RBAC tables
   - Test in staging environment

2. **Week 2: Limited Testing**
   - Enable RBAC for test environment
   - Monitor for issues
   - Gather feedback

3. **Week 3: Canary Deployment**
   - Enable for 10% of users
   - Monitor error rates
   - Compare with control group

4. **Week 4: Full Rollout**
   - Enable for all users
   - Monitor for 48 hours
   - Remove feature flag after stability confirmed

## Risk Mitigation

1. **Backward Compatibility**
   - Maintain dual permission checking
   - Fallback to role-based permissions
   - Gradual migration per endpoint

2. **Performance**
   - Redis caching for permission checks
   - Batch permission loading
   - Database query optimization

3. **User Experience**
   - Clear permission denied messages
   - Permission request workflow
   - Help documentation

## Success Metrics

- Zero increase in 403 errors after migration
- < 10ms latency for permission checks
- 100% test coverage for RBAC code
- Successful migration of all endpoints
- Positive user feedback on flexibility

## Timeline Summary

| Phase | Duration | Status | Key Deliverables |
|-------|----------|--------|------------------|
| Phase 0 | 0.5 days | Not Started | Database population |
| Phase 1 | 2 days | Not Started | Frontend permission infrastructure |
| Phase 2 | 3 days | Not Started | Backend API migration |
| Phase 3 | 2 days | Not Started | Frontend component updates |
| Phase 4 | 2 days | Not Started | Comprehensive testing |
| Phase 5 | 0.5 days | Not Started | Documentation & deployment |
| **Total** | **10 days** | **0% Complete** | **Full RBAC Integration** |

## Next Steps

1. Run permission population scripts
2. Implement frontend permission context
3. Begin systematic endpoint migration
4. Create comprehensive test suite
5. Plan gradual rollout strategy