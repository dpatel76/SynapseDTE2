import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  CircularProgress,
  Alert,
  Button,
  LinearProgress,
  IconButton,
} from '@mui/material';
import {
  Assignment,
  Timeline,
  CheckCircle,
  PlayArrow,
  TrendingUp,
  Notifications,
  Assessment,
  Warning,
  Speed,
  Analytics,
  Insights,
  Error,
  People,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useNotifications } from '../contexts/NotificationContext';
import { UserRole } from '../types/api';
import TesterDashboardEnhanced from './dashboards/TesterDashboard';
import TestExecutiveDashboardRedesigned from './dashboards/TestExecutiveDashboard';
import ReportOwnerDashboard from './dashboards/ReportOwnerDashboard';

interface DashboardStats {
  total_cycles: number;
  active_cycles: number;
  completed_phases: number;
  pending_tasks: number;
}

interface Activity {
  id: number;
  type: string;
  description: string;
  user: string;
  timestamp: string;
  phase?: string;
  cycle?: string;
}

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast, addNotification } = useNotifications();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // All hooks must come before any conditional returns
  useEffect(() => {
    // Set default stats and activities immediately
    setStats({
      total_cycles: 0,
      active_cycles: 0,
      completed_phases: 0,
      pending_tasks: 0,
    });
    
    setActivities([
      {
        id: 1,
        type: 'welcome',
        description: 'Welcome to SynapseDT - Your testing platform is ready',
        user: user?.email || 'System',
        timestamp: new Date().toISOString(),
        phase: 'Setup',
        cycle: 'Initial'
      }
    ]);

    setLoading(false);

    // Don't fetch management data for certain roles to avoid 403 errors
    if (user?.role === UserRole.TESTER) {
      return;
    }

    // Try to fetch real data in the background (only for non-Tester roles)
    const fetchDashboardData = async () => {
      try {
        const [cyclesResponse, reportsResponse] = await Promise.allSettled([
          apiClient.get('/cycles/'),
          apiClient.get('/reports/')
        ]);

        const cycles = cyclesResponse.status === 'fulfilled' ? cyclesResponse.value.data?.cycles || [] : [];
        const reports = reportsResponse.status === 'fulfilled' ? reportsResponse.value.data?.reports || [] : [];

        // Update stats with real data (handle both cases for compatibility)
        setStats({
          total_cycles: cycles.length,
          active_cycles: cycles.filter((cycle: any) => cycle.status === 'Active' || cycle.status === 'active').length,
          completed_phases: reports.filter((report: any) => report.status === 'Completed' || report.status === 'completed').length,
          pending_tasks: cycles.filter((cycle: any) => cycle.status === 'Planning' || cycle.status === 'Draft' || cycle.status === 'draft').length,
        });

      } catch (err) {
        console.warn('Failed to fetch dashboard data:', err);
        // Keep the default data
      }
    };

    fetchDashboardData();
  }, [user]);

  // Demo notification functionality
  useEffect(() => {
    // Demo toast on page load
    const timer = setTimeout(() => {
      showToast('info', 'Welcome to the enhanced SynapseDT platform with real-time notifications!', true, 5000);
    }, 1000);

    return () => clearTimeout(timer);
  }, [showToast]);

  // Render role-specific dashboards after all hooks
  if (user?.role === UserRole.TESTER) {
    return <TesterDashboardEnhanced />;
  }
  
  if ((user?.role as string) === 'Test Executive') {
    return <TestExecutiveDashboardRedesigned />;
  }
  
  if (user?.role === UserRole.REPORT_OWNER || user?.role === UserRole.REPORT_EXECUTIVE) {
    return <ReportOwnerDashboard />;
  }

  const handleDemoNotification = () => {
    addNotification({
      type: 'warning',
      title: 'Demo Notification',
      message: 'This is a demonstration of the notification system. New critical observation requires attention.',
      category: 'workflow',
      priority: 'high',
      actionable: true,
      actionText: 'View Details',
      actionUrl: '/phases/observation-management',
      relatedEntityType: 'observation',
      relatedEntityId: 'demo_obs_001',
    });
    showToast('success', 'Demo notification added successfully!');
  };

  const formatRelativeTime = (timestamp: string) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    
    if (minutes < 60) {
      return `${minutes}m ago`;
    } else {
      return `${hours}h ago`;
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'phase_started':
        return <PlayArrow color="primary" />;
      case 'phase_completed':
        return <CheckCircle color="success" />;
      case 'cycle_created':
        return <Assignment color="info" />;
      default:
        return <Notifications color="action" />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  const quickStats = [
    {
      label: 'Active Test Cycles',
      value: stats?.active_cycles?.toString() || '0',
      change: stats?.active_cycles ? '+1' : '0',
      trend: stats?.active_cycles ? 'up' : 'neutral',
      color: 'primary',
      icon: <Assessment />,
    },
    {
      label: 'Total Test Cycles',
      value: stats?.total_cycles?.toString() || '0',
      change: stats?.total_cycles ? '+' + stats.total_cycles : '0',
      trend: stats?.total_cycles ? 'up' : 'neutral',
      color: 'success',
      icon: <Speed />,
    },
    {
      label: 'Completed Phases',
      value: stats?.completed_phases?.toString() || '0',
      change: stats?.completed_phases ? '+' + stats.completed_phases : '0',
      trend: stats?.completed_phases ? 'up' : 'neutral',
      color: 'info',
      icon: <TrendingUp />,
    },
    {
      label: 'Pending Tasks',
      value: stats?.pending_tasks?.toString() || '0',
      change: stats?.pending_tasks ? '-' + stats.pending_tasks : '0',
      trend: stats?.pending_tasks ? 'down' : 'neutral',
      color: 'warning',
      icon: <Warning />,
    },
  ];

  // Default dashboard for Data Executive and Admin roles
  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Executive Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back, {user?.first_name || user?.username}! Here's your organizational overview.
        </Typography>
      </Box>

      {/* Demo Notification Section */}
      {stats && (stats.total_cycles === 0 && stats.active_cycles === 0) && (
        <Alert 
          severity="info" 
          sx={{ mb: 3 }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={() => navigate('/cycles')}
              startIcon={<Assignment />}
            >
              Create First Cycle
            </Button>
          }
        >
          <Typography variant="subtitle2">Welcome to SynapseDT!</Typography>
          <Typography variant="body2">
            You don't have any test cycles yet. Click "Create First Cycle" to get started with your first testing workflow.
          </Typography>
        </Alert>
      )}
      
      <Alert 
        severity="info" 
        sx={{ mb: 3 }}
        action={
          <Button 
            color="inherit" 
            size="small" 
            onClick={handleDemoNotification}
            startIcon={<Notifications />}
          >
            Demo Notification
          </Button>
        }
      >
        <Typography variant="subtitle2">New Features Available!</Typography>
        <Typography variant="body2">
          Try the enhanced notification system, global search, and advanced analytics dashboard.
        </Typography>
      </Alert>

      {/* Quick Stats */}
      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: {
            xs: 'repeat(1, 1fr)',
            sm: 'repeat(2, 1fr)', 
            md: 'repeat(4, 1fr)'
          },
          gap: 3,
          mb: 4 
        }}
      >
        {quickStats.map((stat, index) => (
          <Card key={index}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                <Box sx={{ color: `${stat.color}.main` }}>
                  {stat.icon}
                </Box>
                <Chip
                  label={stat.change}
                  size="small"
                  color={stat.trend === 'up' ? 'success' : stat.trend === 'down' ? 'error' : 'default'}
                  variant="outlined"
                />
              </Box>
              <Typography variant="h4" color={`${stat.color}.main`} gutterBottom>
                {stat.value}
              </Typography>
              <Typography variant="subtitle2">
                {stat.label}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Box>

      {/* Main Content */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' }, gap: 3 }}>
        {/* Recent Activity */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            {activities.length > 0 ? (
              <List>
                {activities.map((activity) => (
                  <ListItem key={activity.id} divider>
                    <ListItemIcon>
                      {getActivityIcon(activity.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={activity.description}
                      secondary={
                        <>
                          <Typography component="span" variant="body2" color="text.secondary" display="block">
                            {activity.phase && `Phase: ${activity.phase}`}
                            {activity.cycle && ` • Cycle: ${activity.cycle}`}
                          </Typography>
                          <Typography component="span" variant="caption" color="text.secondary" display="block">
                            {formatRelativeTime(activity.timestamp)} • {activity.user}
                          </Typography>
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box textAlign="center" py={4}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  No recent activity to display
                </Typography>
                <Button 
                  variant="outlined" 
                  size="small" 
                  onClick={() => navigate('/cycles')}
                  startIcon={<Assignment />}
                >
                  Start Your First Cycle
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions & Analytics */}
        <Box display="flex" flexDirection="column" gap={2}>
          {/* Quick Actions */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button variant="outlined" fullWidth startIcon={<Timeline />} onClick={() => navigate('/cycles')}>
                  Start New Cycle
                </Button>
                <Button variant="outlined" fullWidth startIcon={<Assessment />} onClick={() => navigate('/reports')}>
                  View Reports
                </Button>
                <Button variant="outlined" fullWidth startIcon={<CheckCircle />} onClick={() => navigate('/phases/test-execution')}>
                  Manage Tests
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Advanced Analytics */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Advanced Analytics
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Explore comprehensive insights and performance metrics with our enhanced analytics dashboard.
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button 
                  variant="contained" 
                  fullWidth 
                  startIcon={<Analytics />}
                  color="primary"
                  onClick={() => navigate('/reports')}
                >
                  View Analytics Dashboard
                </Button>
                <Button 
                  variant="outlined" 
                  fullWidth 
                  startIcon={<Insights />}
                  onClick={() => navigate('/cycles')}
                >
                  Performance Insights
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* System Status */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Box mb={2}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="body2">Database</Typography>
                  <Chip label="Healthy" color="success" size="small" />
                </Box>
                <LinearProgress variant="determinate" value={95} color="success" />
              </Box>
              <Box mb={2}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="body2">API Services</Typography>
                  <Chip label="Optimal" color="success" size="small" />
                </Box>
                <LinearProgress variant="determinate" value={98} color="success" />
              </Box>
              <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="body2">Processing Queue</Typography>
                  <Chip label="Normal" color="info" size="small" />
                </Box>
                <LinearProgress variant="determinate" value={75} color="info" />
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

export default DashboardPage; 