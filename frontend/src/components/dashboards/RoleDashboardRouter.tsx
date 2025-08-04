import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { CircularProgress, Box } from '@mui/material';

// Import role-specific dashboards
import TesterDashboardEnhanced from '../../pages/dashboards/TesterDashboard';
import TestExecutiveDashboardRedesigned from '../../pages/dashboards/TestExecutiveDashboard';
import DataOwnerDashboard from '../../pages/dashboards/DataOwnerDashboard';
import DataExecutiveDashboard from '../../pages/dashboards/DataExecutiveDashboard';
import ReportOwnerDashboard from '../../pages/dashboards/ReportOwnerDashboard';
import AdminDashboard from '../../pages/dashboards/AdminDashboard';

/**
 * Smart router that automatically directs users to their role-specific dashboard
 */
const RoleDashboardRouter: React.FC = () => {
  const { user, isLoading: loading } = useAuth();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Get user role
  const primaryRole = user.role?.toLowerCase();

  // Route based on role
  switch (primaryRole) {
    case 'admin':
      return <AdminDashboard />;
    
    case 'tester':
      return <TesterDashboardEnhanced />;
    
    case 'test executive':
      return <TestExecutiveDashboardRedesigned />;
    
    case 'data owner':
      return <DataOwnerDashboard />;
    
    case 'data executive':
      return <DataExecutiveDashboard />;
    
    case 'report owner':
    case 'report owner executive':
      return <ReportOwnerDashboard />;
    
    default:
      // Fallback to a generic dashboard or unauthorized page
      return <Navigate to="/unauthorized" replace />;
  }
};

export default RoleDashboardRouter;