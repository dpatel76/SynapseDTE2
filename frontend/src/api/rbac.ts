import apiClient from './client';

interface Permission {
  permission_id: number;
  resource: string;
  action: string;
  description?: string;
}

interface Role {
  role_id: number;
  role_name: string;
  description?: string;
  is_system: boolean;
  is_active: boolean;
}

interface UserPermissionsResponse {
  user_id: number;
  roles: string[];
  direct_permissions: string[];
  role_permissions: string[];
  all_permissions: string[];
}

interface RolePermissionsResponse {
  role: Role;
  permissions: Permission[];
}

interface UserRolesResponse {
  user_id: number;
  roles: {
    role_id: number;
    role_name: string;
    assigned_at: string;
    expires_at?: string;
  }[];
}

interface AuditLogEntry {
  audit_id: number;
  user_id: number;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: any;
  timestamp: string;
}

export const rbacApi = {
  // Permissions
  getPermissions: (params?: { skip?: number; limit?: number; resource?: string }) => 
    apiClient.get<Permission[]>('/admin/rbac/permissions/', { params }),
  
  createPermission: (data: { resource: string; action: string; description?: string }) => 
    apiClient.post<Permission>('/admin/rbac/permissions/', data),
  
  deletePermission: (id: number) => 
    apiClient.delete(`/admin/rbac/permissions/${id}`),
  
  // Roles
  getRoles: (params?: { skip?: number; limit?: number }) => 
    apiClient.get<Role[]>('/admin/rbac/roles/', { params }),
  
  createRole: (data: { name: string; description?: string; is_system: boolean }) => 
    apiClient.post<Role>('/admin/rbac/roles/', data),
  
  updateRole: (id: number, data: { name?: string; description?: string }) => 
    apiClient.put<Role>(`/admin/rbac/roles/${id}`, data),
  
  deleteRole: (id: number) => 
    apiClient.delete(`/admin/rbac/roles/${id}`),
  
  // Role Permissions
  getRolePermissions: (roleId: number) => 
    apiClient.get<RolePermissionsResponse>(`/admin/rbac/roles/${roleId}/permissions`),
  
  updateRolePermissions: (roleId: number, permissionIds: number[]) => 
    apiClient.put(`/admin/rbac/roles/${roleId}/permissions`, { permission_ids: permissionIds }),
  
  // User Permissions
  getUserPermissions: (userId: number) => 
    apiClient.get<UserPermissionsResponse>(`/admin/rbac/users/${userId}/permissions`),
  
  getUserRoles: (userId: number) => 
    apiClient.get<UserRolesResponse>(`/admin/rbac/users/${userId}/roles`),
  
  assignUserRole: (userId: number, roleId: number, expiresAt?: string) => 
    apiClient.post(`/admin/rbac/users/${userId}/roles`, { 
      role_id: roleId, 
      expires_at: expiresAt 
    }),
  
  removeUserRole: (userId: number, roleId: number) => 
    apiClient.delete(`/admin/rbac/users/${userId}/roles/${roleId}`),
  
  // Direct Permissions
  grantUserPermission: (userId: number, permissionId: number) => 
    apiClient.post(`/admin/rbac/users/${userId}/permissions`, { 
      permission_id: permissionId,
      is_granted: true 
    }),
  
  denyUserPermission: (userId: number, permissionId: number) => 
    apiClient.post(`/admin/rbac/users/${userId}/permissions`, { 
      permission_id: permissionId,
      is_granted: false 
    }),
  
  removeUserPermission: (userId: number, permissionId: number) =>
    apiClient.delete(`/admin/rbac/users/${userId}/permissions/${permissionId}`),
  
  // Resource Permissions
  getResourcePermissions: (resourceType: string, resourceId: string) => 
    apiClient.get(`/admin/rbac/resources/${resourceType}/${resourceId}/permissions`),
  
  grantResourcePermission: (data: {
    user_id: number;
    permission_id: number;
    resource_type: string;
    resource_id: string;
  }) => apiClient.post('/admin/rbac/resource-permissions/', data),
  
  revokeResourcePermission: (data: {
    user_id: number;
    permission_id: number;
    resource_type: string;
    resource_id: string;
  }) => apiClient.delete('/admin/rbac/resource-permissions/', { data }),
  
  // Audit Log
  getAuditLog: (params?: { 
    skip?: number; 
    limit?: number; 
    user_id?: number;
    action?: string;
    start_date?: string;
    end_date?: string;
  }) => apiClient.get<AuditLogEntry[]>('/admin/rbac/audit-log/', { params }),
};