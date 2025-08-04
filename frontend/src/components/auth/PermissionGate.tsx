import React from 'react';
import { usePermissions } from '../../contexts/PermissionContext';
import { Alert, CircularProgress, Box } from '@mui/material';

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
    return (
      <Box display="flex" justifyContent="center" alignItems="center" p={2}>
        <CircularProgress size={24} />
      </Box>
    );
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