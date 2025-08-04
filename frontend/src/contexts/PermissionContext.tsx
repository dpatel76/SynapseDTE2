import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext';
import { rbacApi } from '../api/rbac';
import { UserRole } from '../types/api';
import apiClient from '../api/client';

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
      setIsLoading(true);
      
      // Use the current user permissions endpoint
      const response = await apiClient.get('/users/me/permissions');
      if (response.data.all_permissions) {
        setPermissions(new Set(response.data.all_permissions));
        setRoles(response.data.roles || []);
        console.log('Loaded RBAC permissions successfully');
      } else {
        // No permissions found
        setPermissions(new Set());
        setRoles([]);
        console.warn('No RBAC permissions found for user');
      }
      
    } catch (error: any) {
      console.error('Failed to load RBAC permissions:', error);
      // No fallback - set empty permissions
      setPermissions(new Set());
      setRoles([]);
    } finally {
      setIsLoading(false);
    }
  };

  const hasPermission = (resource: string, action: string): boolean => {
    // Check for wildcard permission (admin access)
    if (permissions.has('*:*')) {
      return true;
    }
    
    // Check for specific permission
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

// Removed legacy role support - using RBAC only