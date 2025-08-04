import React, { useState } from 'react';
import {
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Collapse,
  Typography,
  Box,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Assignment as AssignmentIcon,
  Business as BusinessIcon,
  Group as GroupIcon,
  Assessment as AssessmentIcon,
  DataObject as DataObjectIcon,
  Timeline as TimelineIcon,
  BugReport as BugReportIcon,
  Description as DescriptionIcon,
  AccountTree as AccountTreeIcon,
  Settings as SettingsIcon,
  AdminPanelSettings as AdminIcon,
  Schedule as ScheduleIcon,
  Notifications as NotificationsIcon,
  Security as SecurityIcon,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { usePermissions } from '../../contexts/PermissionContext';
import { useAuth } from '../../contexts/AuthContext';

interface MenuItem {
  text: string;
  path: string;
  icon: React.ReactNode;
  permission: [string, string] | null;
}

interface SidebarProps {
  drawerWidth?: number;
}

const Sidebar: React.FC<SidebarProps> = ({ drawerWidth = 240 }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { hasPermission, hasAnyPermission, isLoading } = usePermissions();
  const { user } = useAuth();
  const [phasesOpen, setPhasesOpen] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);

  // Define menu items with permission requirements
  const mainMenuItems: MenuItem[] = [
    { text: 'Dashboard', path: '/dashboard', icon: <DashboardIcon />, permission: null },
    { text: 'Test Cycles', path: '/cycles', icon: <AssignmentIcon />, permission: ['cycles', 'read'] },
    { text: 'Reports', path: '/reports', icon: <DescriptionIcon />, permission: ['reports', 'read'] },
    { text: 'Analytics', path: '/analytics', icon: <AssessmentIcon />, permission: ['reports', 'read'] },
  ];

  const phaseMenuItems: MenuItem[] = [
    { text: 'Planning', path: '/phases/planning', icon: <TimelineIcon />, permission: ['planning', 'read'] },
    { text: 'Scoping', path: '/phases/scoping', icon: <AccountTreeIcon />, permission: ['scoping', 'read'] },
    { text: 'Data Owner', path: '/phases/data-owner', icon: <DataObjectIcon />, permission: ['data_provider', 'read'] },
    { text: 'Sample Selection', path: '/phases/sample-selection', icon: <AssignmentIcon />, permission: ['sample_selection', 'read'] },
    { text: 'Request Info', path: '/phases/request-info', icon: <DescriptionIcon />, permission: ['request_info', 'read'] },
    { text: 'Test Execution', path: '/phases/test-execution', icon: <BugReportIcon />, permission: ['testing', 'read'] },
    { text: 'Observations', path: '/phases/observation-management', icon: <NotificationsIcon />, permission: ['observations', 'read'] },
  ];

  const adminMenuItems: MenuItem[] = [
    { text: 'User Management', path: '/admin/users', icon: <GroupIcon />, permission: ['users', 'create'] },
    { text: 'LOB Management', path: '/admin/lobs', icon: <BusinessIcon />, permission: ['lobs', 'manage'] },
    { text: 'Report Management', path: '/admin/reports', icon: <AssignmentIcon />, permission: ['reports', 'manage'] },
    { text: 'Data Sources', path: '/admin/data-sources', icon: <DataObjectIcon />, permission: ['data_sources', 'read'] },
    { text: 'SLA Configuration', path: '/admin/sla-configuration', icon: <ScheduleIcon />, permission: ['system', 'configure'] },
    { text: 'RBAC Management', path: '/admin/rbac', icon: <SecurityIcon />, permission: ['permissions', 'manage'] },
    { text: 'System Settings', path: '/admin/settings', icon: <SettingsIcon />, permission: ['system', 'configure'] },
  ];

  // Filter menu items based on permissions
  const filterMenuItems = (items: MenuItem[]): MenuItem[] => {
    return items.filter(item => {
      if (!item.permission) return true; // No permission required
      return hasPermission(item.permission[0], item.permission[1]);
    });
  };

  // Check if user has any admin permissions
  const hasAnyAdminPermission = (): boolean => {
    return hasAnyPermission(
      ['users', 'read'],
      ['users', 'manage'],
      ['lobs', 'manage'],
      ['reports', 'manage'],
      ['data_sources', 'read'],
      ['data_sources', 'manage'],
      ['system', 'configure'],
      ['permissions', 'manage']
    );
  };

  // Check if user has any phase permissions
  const hasAnyPhasePermission = (): boolean => {
    return hasAnyPermission(
      ['planning', 'read'],
      ['scoping', 'read'],
      ['data_provider', 'read'],
      ['sample_selection', 'read'],
      ['request_info', 'read'],
      ['testing', 'read'],
      ['observations', 'read']
    );
  };

  const isSelected = (path: string) => location.pathname === path;

  const handlePhasesToggle = () => {
    setPhasesOpen(!phasesOpen);
  };

  const handleAdminToggle = () => {
    setAdminOpen(!adminOpen);
  };

  // Don't render until permissions are loaded
  if (isLoading) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Loading...
        </Typography>
      </Box>
    );
  }

  const filteredMainItems = filterMenuItems(mainMenuItems);
  const filteredPhaseItems = filterMenuItems(phaseMenuItems);
  const filteredAdminItems = filterMenuItems(adminMenuItems);
  const showPhases = hasAnyPhasePermission() && filteredPhaseItems.length > 0;
  const showAdmin = hasAnyAdminPermission() && filteredAdminItems.length > 0;

  return (
    <div>
      <List>
        {filteredMainItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={isSelected(item.path)}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Workflow Phases Section */}
      {showPhases && (
        <>
          <Divider sx={{ my: 1 }} />
          <ListItem disablePadding>
            <ListItemButton onClick={handlePhasesToggle}>
              <ListItemIcon>
                <AccountTreeIcon />
              </ListItemIcon>
              <ListItemText primary="Workflow Phases" />
              {phasesOpen ? <ExpandLess /> : <ExpandMore />}
            </ListItemButton>
          </ListItem>
          <Collapse in={phasesOpen} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {filteredPhaseItems.map((item) => (
                <ListItem key={item.text} disablePadding>
                  <ListItemButton
                    sx={{ pl: 4 }}
                    selected={isSelected(item.path)}
                    onClick={() => navigate(item.path)}
                  >
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.text} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Collapse>
        </>
      )}

      {/* Admin Section */}
      {showAdmin && (
        <>
          <Divider sx={{ my: 1 }} />
          <ListItem disablePadding>
            <ListItemButton onClick={handleAdminToggle}>
              <ListItemIcon>
                <AdminIcon />
              </ListItemIcon>
              <ListItemText primary="Administration" />
              {adminOpen ? <ExpandLess /> : <ExpandMore />}
            </ListItemButton>
          </ListItem>
          <Collapse in={adminOpen} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {filteredAdminItems.map((item) => (
                <ListItem key={item.text} disablePadding>
                  <ListItemButton
                    sx={{ pl: 4 }}
                    selected={isSelected(item.path)}
                    onClick={() => navigate(item.path)}
                  >
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.text} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Collapse>
        </>
      )}
    </div>
  );
};

export default Sidebar;