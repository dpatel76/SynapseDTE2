import React, { useState } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Chip,
  Collapse,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  Assignment,
  Group,
  Assessment,
  Settings,
  AccountCircle,
  Logout,
  Timeline,
  Person,
  AdminPanelSettings,
  Business as BusinessIcon,
  ExpandLess,
  ExpandMore,
  Schedule as ScheduleIcon,
  DataObject as DataObjectIcon,
  PersonOff as StopImpersonateIcon,
  Security,
  HourglassEmpty,
  Description as DocumentIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { NotificationBell } from '../../contexts/NotificationContext';
import { UserRole } from '../../types/api';
import GlobalSearch from './GlobalSearch';
import TestExecutiveNavigation from '../navigation/TestExecutiveNavigation';
import Sidebar from '../layout/Sidebar';

const drawerWidth = 240;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [adminMenuOpen, setAdminMenuOpen] = useState(false);
  
  const { user, logout, impersonatedUser, isImpersonating, stopImpersonation } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    await logout();
    handleClose();
    navigate('/login');
  };

  const handleAdminMenuToggle = () => {
    setAdminMenuOpen(!adminMenuOpen);
  };

  // Check if user has admin privileges
  const isAdmin = user?.role === UserRole.ADMIN;
  const isManager = user?.role === UserRole.TEST_EXECUTIVE;
  
  // Debug logging to see what role is being detected
  console.log('User role:', user?.role, 'UserRole.ADMIN:', UserRole.ADMIN, 'isAdmin:', isAdmin);

  // Build menu items with proper ordering
  const menuItems = [];
  
  // Dashboard - first for all users
  if (user?.role === UserRole.DATA_EXECUTIVE) {
    menuItems.push({ text: 'Dashboard', icon: <Dashboard />, path: '/data-executive-dashboard' });
  } else if (user?.role === UserRole.ADMIN) {
    menuItems.push({ text: 'Dashboard', icon: <Dashboard />, path: '/admin-dashboard' });
  } else {
    menuItems.push({ text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' });
  }
  
  // Universal assignments - name based on role context (exclude for Admin)
  if (user?.role !== UserRole.ADMIN) {
    menuItems.push({ text: user?.role === UserRole.TESTER ? 'My Tasks' : 'My Assignments', icon: <Assignment />, path: '/my-assignments' });
  }
  
  // Tester specific - My Reports
  if (user?.role === UserRole.TESTER) {
    menuItems.push({ text: 'My Reports', icon: <Assessment />, path: '/tester/assignments' });
    menuItems.push({ text: 'Background Jobs', icon: <HourglassEmpty />, path: '/background-jobs' });
    menuItems.push({ text: 'Documents', icon: <DocumentIcon />, path: '/documents' });
  }
  
  // Report Owner specific dashboard
  if (user?.role === UserRole.REPORT_OWNER) {
    menuItems.push({ text: 'My Reviews', icon: <Assessment />, path: '/report-owner-dashboard' });
    menuItems.push({ text: 'Documents', icon: <DocumentIcon />, path: '/documents' });
  }
  
  // Only show Test Cycles and Reports for non-Tester roles (exclude Reports for Admin)
  if (user?.role !== UserRole.TESTER) {
    menuItems.push({ text: 'Test Cycles', icon: <Assignment />, path: '/cycles' });
    // Temporarily exclude Reports for Data Executive due to permission issues
    // Also exclude Reports for Admin as requested
    if (user?.role !== UserRole.DATA_EXECUTIVE && user?.role !== UserRole.ADMIN) {
      menuItems.push({ text: 'Reports', icon: <Assessment />, path: '/reports' });
    }
  }
  
  // Analytics should only be shown to management roles and Data Executive
  if (user?.role === UserRole.TEST_EXECUTIVE || user?.role === UserRole.DATA_EXECUTIVE || user?.role === UserRole.REPORT_EXECUTIVE || isAdmin) {
    menuItems.push({ text: 'Analytics', icon: <Timeline />, path: '/analytics' });
  }
  
  // Workflow Monitoring only for Test Manager and Report Owner Executive (NOT Data Executive)
  if (user?.role === UserRole.TEST_EXECUTIVE || user?.role === UserRole.REPORT_EXECUTIVE || isAdmin) {
    menuItems.push({ text: 'Workflow Monitoring', icon: <Assessment />, path: '/workflow-monitoring' });
  }
  
  // Users management - exclude for Admin (they'll use User Management under Administration)
  if ((isManager) && user?.role !== UserRole.ADMIN) {
    menuItems.push({ text: 'Users', icon: <Group />, path: '/users' });
  }
  
  // Documents - available to all non-admin roles (admin will have it in the admin menu)
  if (user?.role !== UserRole.ADMIN && user?.role !== UserRole.TESTER && user?.role !== UserRole.REPORT_OWNER) {
    menuItems.push({ text: 'Documents', icon: <DocumentIcon />, path: '/documents' });
  }

  const adminMenuItems = [
    { text: 'User Management', icon: <Group />, path: '/admin/users' },
    { text: 'LOB Management', icon: <BusinessIcon />, path: '/admin/lobs' },
    { text: 'Report Management', icon: <Assignment />, path: '/admin/reports' },
    { text: 'Document Management', icon: <DocumentIcon />, path: '/documents' },
    { text: 'SLA Configuration', icon: <ScheduleIcon />, path: '/admin/sla-configuration' },
    { text: 'RBAC Management', icon: <Security />, path: '/admin/rbac' },
    { text: 'System Settings', icon: <Settings />, path: '/admin/settings' },
  ];

  const isSelected = (path: string) => location.pathname === path;

  // Use role-specific navigation for Test Manager
  const drawer = user?.role === UserRole.TEST_EXECUTIVE ? (
    <TestExecutiveNavigation />
  ) : (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          SynapseDT
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
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
        
        {/* Admin Menu */}
        {isAdmin && (
          <>
            <Divider sx={{ my: 1 }} />
            <ListItem disablePadding>
              <ListItemButton onClick={handleAdminMenuToggle}>
                <ListItemIcon>
                  <AdminPanelSettings />
                </ListItemIcon>
                <ListItemText primary="Administration" />
                {adminMenuOpen ? <ExpandLess /> : <ExpandMore />}
              </ListItemButton>
            </ListItem>
            <Collapse in={adminMenuOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {adminMenuItems.map((item) => (
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
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* Fixed AppBar */}
      <AppBar 
        position="fixed" 
        sx={{ 
          zIndex: (theme) => theme.zIndex.drawer + 1
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerToggle}
            edge="start"
            sx={{ mr: 2, display: { sm: 'none' } }}
            data-testid="mobile-menu-button"
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" component="h1" sx={{ flexGrow: 1 }}>
            SynapseDT
            {user && (
              <>
                <Chip 
                  label={user.role} 
                  size="small" 
                  sx={{ ml: 2 }} 
                  color={isAdmin ? 'secondary' : isManager ? 'primary' : 'default'}
                />
                {isImpersonating && impersonatedUser && (
                  <Box component="span" sx={{ ml: 2, display: 'inline-flex', alignItems: 'center' }}>
                    <Chip 
                      label={`Impersonating: ${impersonatedUser.first_name} ${impersonatedUser.last_name}`}
                      color="warning"
                      size="small"
                      onDelete={stopImpersonation}
                      deleteIcon={<StopImpersonateIcon />}
                    />
                  </Box>
                )}
              </>
            )}
          </Typography>

          {/* Global Search */}
          <Box sx={{ mr: 2, flexGrow: 0.3, maxWidth: 400, display: { xs: 'none', md: 'block' } }}>
            <GlobalSearch />
          </Box>

          {/* Notification Bell */}
          <NotificationBell />

          {/* User Menu */}
          <Box sx={{ ml: 2 }}>
            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls="user-menu"
              aria-haspopup="true"
              onClick={handleMenu}
              color="inherit"
              data-testid="user-menu-button"
            >
              <AccountCircle />
            </IconButton>
            <Menu
              id="user-menu"
              anchorEl={anchorEl}
              anchorOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              open={Boolean(anchorEl)}
              onClose={handleClose}
            >
              <MenuItem onClick={handleClose}>
                <Person sx={{ mr: 1 }} />
                Profile
              </MenuItem>
              <MenuItem onClick={handleClose}>
                <Settings sx={{ mr: 1 }} />
                Settings
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleLogout}>
                <Logout sx={{ mr: 1 }} />
                Logout
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>
      
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': { 
            boxSizing: 'border-box', 
            width: drawerWidth,
            mt: '64px'
          },
        }}
      >
        {drawer}
      </Drawer>
      
      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        open
        sx={{
          display: { xs: 'none', sm: 'block' },
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': { 
            boxSizing: 'border-box', 
            width: drawerWidth,
            mt: '64px',
            height: 'calc(100% - 64px)'
          },
        }}
      >
        {drawer}
      </Drawer>
      
      {/* Main content area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: '64px',
          minHeight: 'calc(100vh - 64px)',
          backgroundColor: 'background.default'
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default Layout; 