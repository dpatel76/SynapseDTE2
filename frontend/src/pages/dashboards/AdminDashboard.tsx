import React, { useState, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Avatar,
  useTheme,
  alpha,
  Stack,
  Grid,
  Badge,
  Alert,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Warning,
  CheckCircle,
  Schedule,
  Assignment,
  Assessment,
  PlayArrow,
  Timer,
  BugReport,
  CalendarToday,
  Visibility,
  ArrowForward,
  Refresh as RefreshIcon,
  Person,
  Error as ErrorIcon,
  AssignmentTurnedIn,
  People,
  Business,
  Description,
  Speed,
  Security,
  Timeline,
  Analytics,
  HourglassEmpty,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { cyclesApi } from '../../api/cycles';
import { metricsApi } from '../../api/metrics';

interface QuickActionCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  onClick: () => void;
  badge?: number;
}

const QuickActionCard: React.FC<QuickActionCardProps> = ({ 
  title, 
  description,
  icon, 
  color,
  onClick,
  badge
}) => {
  const theme = useTheme();
  
  return (
    <Card 
      sx={{ 
        height: '100%',
        cursor: 'pointer',
        transition: 'all 0.3s',
        border: `1px solid ${theme.palette.divider}`,
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: theme.shadows[4],
          borderColor: theme.palette.primary.main,
        },
      }}
      onClick={onClick}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" color="text.primary" gutterBottom fontWeight="medium">
              {title}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {description}
            </Typography>
          </Box>
          <Badge badgeContent={badge} color="error" sx={{ ml: 2 }}>
            <Avatar sx={{ bgcolor: alpha(color, 0.1), color: color, width: 48, height: 48 }}>
              {icon}
            </Avatar>
          </Badge>
        </Box>
      </CardContent>
    </Card>
  );
};

const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const [selectedCycleId, setSelectedCycleId] = useState<string>('all');
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [refreshing, setRefreshing] = useState(false);

  // Get available years for the dropdown
  const availableYears = useMemo(() => {
    const currentYear = new Date().getFullYear();
    const years = [];
    for (let i = currentYear; i >= currentYear - 5; i--) {
      years.push(i);
    }
    return years;
  }, []);

  // Get all test cycles
  const { data: cycles, isLoading: cyclesLoading, refetch: refetchCycles } = useQuery({
    queryKey: ['admin-cycles', selectedYear],
    queryFn: async () => {
      try {
        // Fetch all cycles - we may need to handle pagination if there are many
        const response = await cyclesApi.getAll(1, 100); // Get up to 100 cycles
        // Filter cycles by selected year
        return response.items.filter((cycle: any) => {
          const cycleYear = new Date(cycle.created_at).getFullYear();
          return cycleYear === selectedYear;
        });
      } catch (error) {
        console.error('Error fetching cycles:', error);
        return [];
      }
    },
  });

  // Get admin metrics
  const { data: adminMetrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
    queryKey: ['admin-metrics', selectedCycleId, selectedYear],
    queryFn: async () => {
      try {
        // Build query parameters
        const params: any = { year: selectedYear };
        if (selectedCycleId !== 'all') {
          params.cycle_id = parseInt(selectedCycleId);
        }
        
        // Call the admin dashboard metrics API
        const response = await fetch(`/api/v1/admin/dashboard/metrics?${new URLSearchParams(params)}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch admin metrics');
        }
        
        const data = await response.json();
        return data;
      } catch (error) {
        console.error('Error fetching admin metrics:', error);
        return null;
      }
    },
  });

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([refetchCycles(), refetchMetrics()]);
    } finally {
      setRefreshing(false);
    }
  };

  const getKeyMetrics = () => {
    if (!adminMetrics) return [];

    return [
      {
        title: 'Active Cycles',
        value: adminMetrics.activeCycles,
        icon: <PlayArrow />,
        color: theme.palette.primary.main,
      },
      {
        title: 'Reports Assigned',
        value: adminMetrics.totalReports,
        icon: <Assignment />,
        color: theme.palette.info.main,
      },
      {
        title: 'Active Reports',
        value: adminMetrics.activeReports,
        icon: <Timer />,
        color: theme.palette.warning.main,
      },
      {
        title: 'Completed Reports',
        value: adminMetrics.completedReports,
        icon: <CheckCircle />,
        color: theme.palette.success.main,
      },
      {
        title: 'Pending Reports',
        value: adminMetrics.pendingReports,
        icon: <HourglassEmpty />,
        color: theme.palette.grey[600],
      },
      {
        title: 'Observations',
        value: adminMetrics.totalObservations,
        icon: <BugReport />,
        color: theme.palette.secondary.main,
      },
    ];
  };

  if (cyclesLoading || metricsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header with same styling as Test Executive Dashboard */}
      <Paper 
        sx={{ 
          p: 3, 
          mb: 3,
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.primary.main, 0.02)} 100%)`,
          borderTop: `4px solid ${theme.palette.primary.main}`
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="h4" gutterBottom fontWeight="bold">
              Admin Dashboard
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Welcome back, {user?.first_name || 'Admin'}! 
              {selectedCycleId === 'all' 
                ? ` Viewing all cycles for ${selectedYear}.`
                : ` Viewing ${cycles?.find((c: any) => c.cycle_id.toString() === selectedCycleId)?.cycle_name || 'Unknown Cycle'}`
              }
            </Typography>
          </Box>
          <Box display="flex" gap={2} alignItems="center">
            {/* Year Selector */}
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Year</InputLabel>
              <Select
                value={selectedYear}
                label="Year"
                onChange={(e) => {
                  setSelectedYear(Number(e.target.value));
                  setSelectedCycleId('all'); // Reset cycle when year changes
                }}
              >
                {availableYears.map((year) => (
                  <MenuItem key={year} value={year}>
                    {year}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Cycle Selector */}
            <FormControl size="small" sx={{ minWidth: 250 }}>
              <InputLabel>Test Cycle</InputLabel>
              <Select
                value={selectedCycleId}
                label="Test Cycle"
                onChange={(e) => setSelectedCycleId(e.target.value)}
                disabled={cyclesLoading}
              >
                <MenuItem value="all">
                  <Box display="flex" alignItems="center" gap={1}>
                    <DashboardIcon />
                    <span>All Cycles ({cycles?.length || 0})</span>
                  </Box>
                </MenuItem>
                {cycles?.map((cycle: any) => (
                  <MenuItem key={cycle.cycle_id} value={cycle.cycle_id.toString()}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        label={cycle.is_active ? 'Active' : 'Inactive'}
                        size="small"
                        color={cycle.is_active ? 'success' : 'default'}
                        sx={{ mr: 1 }}
                      />
                      {cycle.cycle_name}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Tooltip title="Refresh data">
              <IconButton onClick={handleRefresh} disabled={refreshing}>
                <RefreshIcon className={refreshing ? 'rotating' : ''} />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      {/* Key Metrics Row */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {getKeyMetrics().map((metric, index) => (
          <Grid key={index} size={{ xs: 12, sm: 6, md: 2 }}>
            <Card 
              sx={{ 
                height: '100%',
                transition: 'all 0.3s',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: theme.shadows[4]
                }
              }}
            >
              <CardContent sx={{ p: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="caption" noWrap>
                      {metric.title}
                    </Typography>
                    <Typography variant="h5" fontWeight="bold" color={metric.color}>
                      {metric.value}
                    </Typography>
                  </Box>
                  <Avatar sx={{ bgcolor: alpha(metric.color, 0.1), color: metric.color, width: 32, height: 32 }}>
                    <Box sx={{ fontSize: 18, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {metric.icon}
                    </Box>
                  </Avatar>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Quick Actions */}
      <Box>
        <Typography variant="h6" gutterBottom fontWeight="medium">
          Quick Actions
        </Typography>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <QuickActionCard
              title="View Test Cycles"
              description="Manage and monitor all test cycles and their progress"
              icon={<CalendarToday />}
              color={theme.palette.primary.main}
              onClick={() => navigate('/cycles')}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <QuickActionCard
              title="Manage Users"
              description="Add, edit, and manage user accounts and permissions"
              icon={<People />}
              color={theme.palette.secondary.main}
              onClick={() => navigate('/admin/users')}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <QuickActionCard
              title="Manage LOBs"
              description="Configure Lines of Business and their settings"
              icon={<Business />}
              color={theme.palette.info.main}
              onClick={() => navigate('/admin/lobs')}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <QuickActionCard
              title="Manage Reports"
              description="Configure report templates and assignments"
              icon={<Description />}
              color={theme.palette.warning.main}
              onClick={() => navigate('/admin/reports')}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <QuickActionCard
              title="Configure SLAs"
              description="Set up Service Level Agreements and deadlines"
              icon={<Speed />}
              color={theme.palette.success.main}
              onClick={() => navigate('/admin/slas')}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <QuickActionCard
              title="Manage Role Based Access"
              description="Configure roles and permissions for system access"
              icon={<Security />}
              color={theme.palette.error.main}
              onClick={() => navigate('/admin/rbac')}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <QuickActionCard
              title="View Workflow Status"
              description="Monitor workflow progress and identify bottlenecks"
              icon={<Timeline />}
              color={theme.palette.grey[700]}
              onClick={() => navigate('/workflow-monitoring')}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <QuickActionCard
              title="View Analytics"
              description="Access detailed analytics and reporting dashboards"
              icon={<Analytics />}
              color={theme.palette.secondary.dark}
              onClick={() => navigate('/analytics')}
            />
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default AdminDashboard;