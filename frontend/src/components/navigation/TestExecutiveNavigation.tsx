import React from 'react';
import {
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Box,
  Chip,
  Collapse,
  Badge,
  Avatar,
  useTheme,
  alpha
} from '@mui/material';
import {
  Dashboard,
  Assignment,
  Timeline,
  People,
  Assessment,
  Settings,
  ExpandLess,
  ExpandMore,
  CheckCircle,
  Schedule,
  Flag,
  BugReport,
  TrendingUp,
  Speed,
  Visibility,
  Add,
  PlayArrow,
  HourglassEmpty
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useQuery } from '@tanstack/react-query';
import { cyclesApi } from '../../api/cycles';
import { metricsApi } from '../../api/metrics';

interface NavigationItem {
  id: string;
  label: string;
  path?: string;
  icon: React.ReactNode;
  badge?: number;
  badgeColor?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
  children?: NavigationItem[];
  dividerAfter?: boolean;
}

const TestExecutiveNavigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const theme = useTheme();
  const [openItems, setOpenItems] = React.useState<Set<string>>(new Set(['cycles']));
  
  // Fetch cycles data
  const { data: cyclesData } = useQuery({
    queryKey: ['cycles', 1, 100],
    queryFn: () => cyclesApi.getAll(1, 100),
  });
  
  // Fetch metrics data
  const { data: metricsData } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: async () => {
      const response = await metricsApi.getDashboardMetrics();
      return response.data;
    },
  });
  
  // Calculate active cycles and SLA compliance
  const activeCycles = cyclesData?.items?.filter(c => c.status === 'Active').length || 0;
  const slaCompliance = metricsData?.aggregate_metrics?.sla_compliance_rate 
    ? Math.round(metricsData.aggregate_metrics.sla_compliance_rate) 
    : 89;

  const navigationItems: NavigationItem[] = [
    {
      id: 'dashboard',
      label: 'Executive Dashboard',
      path: '/dashboard',
      icon: <Dashboard />,
    },
    {
      id: 'cycles',
      label: 'Test Cycles',
      icon: <Timeline />,
      children: [
        {
          id: 'all-cycles',
          label: 'All Cycles',
          path: '/cycles',
          icon: <Assignment />,
        },
        {
          id: 'active-cycles',
          label: 'Active Cycles',
          path: '/cycles?status=active',
          icon: <PlayArrow />,
          badge: activeCycles > 0 ? activeCycles : undefined,
          badgeColor: 'success'
        },
        {
          id: 'completed-cycles',
          label: 'Completed Cycles',
          path: '/cycles?status=completed',
          icon: <CheckCircle />,
        },
        {
          id: 'create-cycle',
          label: 'Create New Cycle',
          path: '/cycles/new',
          icon: <Add />,
        }
      ]
    },
    {
      id: 'monitoring',
      label: 'Monitoring',
      icon: <Speed />,
      children: [
        {
          id: 'sla-tracking',
          label: 'SLA Compliance',
          path: '/sla-tracking',
          icon: <Flag />,
          badge: 5,
          badgeColor: 'warning'
        },
        {
          id: 'team-performance',
          label: 'Team Performance',
          path: '/team-performance',
          icon: <People />,
        },
        {
          id: 'quality-metrics',
          label: 'Quality Metrics',
          path: '/quality-metrics',
          icon: <CheckCircle />,
        },
        {
          id: 'background-jobs',
          label: 'Background Jobs',
          path: '/background-jobs',
          icon: <HourglassEmpty />,
        }
      ]
    },
    {
      id: 'reports',
      label: 'Reports & Analytics',
      icon: <Assessment />,
      children: [
        {
          id: 'analytics',
          label: 'Analytics Dashboard',
          path: '/analytics',
          icon: <Assessment />,
        },
        {
          id: 'all-reports',
          label: 'All Reports',
          path: '/reports',
          icon: <TrendingUp />,
        }
      ],
      dividerAfter: true
    },
    {
      id: 'settings',
      label: 'Settings',
      path: '/settings',
      icon: <Settings />,
    }
  ];

  const handleToggle = (itemId: string) => {
    const newOpenItems = new Set(openItems);
    if (newOpenItems.has(itemId)) {
      newOpenItems.delete(itemId);
    } else {
      newOpenItems.add(itemId);
    }
    setOpenItems(newOpenItems);
  };

  const handleNavigation = (path?: string) => {
    if (path) {
      navigate(path);
    }
  };

  const isItemActive = (item: NavigationItem): boolean => {
    if (item.path) {
      return location.pathname === item.path || location.pathname.startsWith(item.path.split('?')[0]);
    }
    if (item.children) {
      return item.children.some(child => child.path && 
        (location.pathname === child.path || location.pathname.startsWith(child.path.split('?')[0]))
      );
    }
    return false;
  };

  const renderNavigationItem = (item: NavigationItem, depth: number = 0) => {
    const isActive = isItemActive(item);
    const hasChildren = item.children && item.children.length > 0;
    const isOpen = openItems.has(item.id);

    return (
      <React.Fragment key={item.id}>
        <ListItem disablePadding sx={{ display: 'block' }}>
          <ListItemButton
            onClick={() => {
              if (hasChildren) {
                handleToggle(item.id);
              } else {
                handleNavigation(item.path);
              }
            }}
            sx={{
              minHeight: 48,
              justifyContent: 'initial',
              px: depth === 0 ? 2.5 : 4,
              backgroundColor: isActive && !hasChildren 
                ? alpha(theme.palette.primary.main, 0.08) 
                : 'transparent',
              borderLeft: isActive && !hasChildren 
                ? `4px solid ${theme.palette.primary.main}` 
                : '4px solid transparent',
              '&:hover': {
                backgroundColor: alpha(theme.palette.primary.main, 0.04)
              }
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 0,
                mr: 3,
                justifyContent: 'center',
                color: isActive ? theme.palette.primary.main : 'inherit'
              }}
            >
              {item.badge ? (
                <Badge 
                  badgeContent={item.badge} 
                  color={item.badgeColor || 'primary'}
                  max={99}
                >
                  {item.icon}
                </Badge>
              ) : (
                item.icon
              )}
            </ListItemIcon>
            <ListItemText 
              primary={item.label}
              primaryTypographyProps={{
                fontSize: depth === 0 ? 14 : 13,
                fontWeight: isActive ? 600 : 400,
                color: isActive ? theme.palette.primary.main : 'inherit'
              }}
            />
            {hasChildren && (
              isOpen ? <ExpandLess /> : <ExpandMore />
            )}
          </ListItemButton>
        </ListItem>

        {hasChildren && (
          <Collapse in={isOpen} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children!.map(child => renderNavigationItem(child, depth + 1))}
            </List>
          </Collapse>
        )}

        {item.dividerAfter && <Divider sx={{ my: 1 }} />}
      </React.Fragment>
    );
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* User Info */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box display="flex" alignItems="center" gap={2}>
          <Avatar 
            sx={{ 
              bgcolor: theme.palette.primary.main,
              width: 40,
              height: 40
            }}
          >
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </Avatar>
          <Box flex={1}>
            <Typography variant="subtitle2" fontWeight="medium">
              {user?.first_name} {user?.last_name}
            </Typography>
            <Chip 
              label="Test Executive" 
              size="small"
              sx={{ 
                backgroundColor: alpha(theme.palette.primary.main, 0.1),
                color: theme.palette.primary.dark,
                fontWeight: 'medium',
                height: 20
              }}
            />
          </Box>
        </Box>
      </Box>

      {/* Navigation Items */}
      <Box sx={{ flex: 1, overflowY: 'auto' }}>
        <List>
          {navigationItems.map(item => renderNavigationItem(item))}
        </List>
      </Box>

      {/* Quick Stats */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Typography variant="caption" color="textSecondary" gutterBottom>
          Quick Stats
        </Typography>
        <Box display="flex" gap={2} mt={1}>
          <Box textAlign="center" flex={1}>
            <Typography variant="h6" color="primary">
              {activeCycles}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Active Cycles
            </Typography>
          </Box>
          <Divider orientation="vertical" flexItem />
          <Box textAlign="center" flex={1}>
            <Typography variant="h6" color="success.main">
              {slaCompliance}%
            </Typography>
            <Typography variant="caption" color="textSecondary">
              SLA Met
            </Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default TestExecutiveNavigation;