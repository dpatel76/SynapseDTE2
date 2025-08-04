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
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { reportsApi } from '../../api/reports';
import { AssignedReport } from '../../types/api';

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

const TesterDashboardEnhanced: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const [selectedCycleId, setSelectedCycleId] = useState<string>('all');
  const [refreshing, setRefreshing] = useState(false);

  // Get tester's assigned reports
  const { data: assignedReports, isLoading: reportsLoading, refetch: refetchReports } = useQuery({
    queryKey: ['tester-assigned-reports', user?.user_id],
    queryFn: async () => {
      try {
        const reports = await reportsApi.getByTester(user?.user_id || 0);
        return reports || [];
      } catch (error) {
        console.error('Error fetching assigned reports:', error);
        return [];
      }
    },
    enabled: !!user?.user_id,
  });

  // Extract unique cycles that tester has assignments for
  const assignedCycles = useMemo(() => {
    if (!assignedReports) return [];
    
    const cycleMap = new Map();
    assignedReports.forEach((report: AssignedReport) => {
      if (!cycleMap.has(report.cycle_id)) {
        cycleMap.set(report.cycle_id, {
          cycle_id: report.cycle_id,
          cycle_name: report.cycle_name || `Cycle ${report.cycle_id}`,
          status: 'Active', // Default to Active since they have assignments
        });
      }
    });
    
    return Array.from(cycleMap.values());
  }, [assignedReports]);

  // Calculate tester-specific metrics
  const testerMetrics = useMemo(() => {
    if (!assignedReports) return null;
    
    let filteredReports = assignedReports;
    
    // Filter by selected cycle if not 'all'
    if (selectedCycleId !== 'all') {
      filteredReports = assignedReports.filter(
        (report: AssignedReport) => report.cycle_id.toString() === selectedCycleId
      );
    }
    
    const totalReports = filteredReports.length;
    const activeReports = filteredReports.filter(r => 
      r.status === 'Active' || r.status === 'In Progress'
    ).length;
    const completedReports = filteredReports.filter(r => 
      r.status === 'Completed'
    ).length;
    const pendingReports = filteredReports.filter(r => 
      r.status === 'Pending' || r.status === 'Not Started'
    ).length;
    const atRiskReports = filteredReports.filter(r => 
      r.status === 'At Risk' || r.status === 'Behind Schedule'
    ).length;
    const totalObservations = filteredReports.reduce((sum, r) => 
      sum + (r.issues_count || 0), 0
    );
    
    return {
      totalReports,
      activeReports,
      completedReports,
      pendingReports,
      atRiskReports,
      totalObservations,
      assignedCycles: selectedCycleId === 'all' ? assignedCycles.length : 1,
    };
  }, [assignedReports, selectedCycleId, assignedCycles]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refetchReports();
    } finally {
      setRefreshing(false);
    }
  };

  const getKeyMetrics = () => {
    if (!testerMetrics) return [];

    // Optimized metrics for single row display - 6 most important metrics
    return [
      {
        title: 'Active Cycles',
        value: testerMetrics.assignedCycles,
        icon: <PlayArrow />,
        color: theme.palette.primary.main,
        subtitle: undefined,
        subtitleColor: undefined,
      },
      {
        title: 'Total Reports',
        value: testerMetrics.totalReports,
        icon: <Assignment />,
        color: theme.palette.info.main,
        subtitle: undefined,
        subtitleColor: undefined,
      },
      {
        title: 'Active Reports',
        value: testerMetrics.activeReports,
        icon: <Timer />,
        color: theme.palette.warning.main,
        subtitle: testerMetrics.atRiskReports > 0 ? `${testerMetrics.atRiskReports} at risk` : undefined,
        subtitleColor: 'error.main'
      },
      {
        title: 'Completed',
        value: testerMetrics.completedReports,
        icon: <CheckCircle />,
        color: theme.palette.success.main,
        subtitle: undefined,
        subtitleColor: undefined,
      },
      {
        title: 'Pending',
        value: testerMetrics.pendingReports,
        icon: <Schedule />,
        color: theme.palette.grey[600],
        subtitle: undefined,
        subtitleColor: undefined,
      },
      {
        title: 'Observations',
        value: testerMetrics.totalObservations,
        icon: <BugReport />,
        color: theme.palette.secondary.main,
        subtitle: undefined,
        subtitleColor: undefined,
      },
    ];
  };

  if (reportsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header with Enhanced Styling - Matching Test Executive Dashboard */}
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
              Tester Dashboard
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Welcome back, {user?.first_name || 'Tester'}! 
              {selectedCycleId === 'all' 
                ? ` You have ${testerMetrics?.totalReports || 0} reports assigned across ${assignedCycles.length} active cycles.`
                : ` Viewing metrics for ${assignedCycles.find(c => c.cycle_id.toString() === selectedCycleId)?.cycle_name || 'Unknown Cycle'}`
              }
            </Typography>
          </Box>
          <Box display="flex" gap={2} alignItems="center">
            {/* Year Selector */}
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Year</InputLabel>
              <Select
                value={new Date().getFullYear()}
                label="Year"
                disabled
              >
                <MenuItem value={new Date().getFullYear()}>
                  {new Date().getFullYear()}
                </MenuItem>
              </Select>
            </FormControl>

            {/* Cycle Selector - Enhanced to match Test Executive style */}
            <FormControl size="small" sx={{ minWidth: 250 }}>
              <InputLabel>Test Cycle</InputLabel>
              <Select
                value={selectedCycleId}
                label="Test Cycle"
                onChange={(e) => setSelectedCycleId(e.target.value)}
                disabled={reportsLoading}
              >
                <MenuItem value="all">
                  <Box display="flex" alignItems="center" gap={1}>
                    <DashboardIcon />
                    <span>All My Cycles ({assignedCycles.length})</span>
                  </Box>
                </MenuItem>
                {assignedCycles.map((cycle: any) => (
                  <MenuItem key={cycle.cycle_id} value={cycle.cycle_id.toString()}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        label={cycle.status || 'Active'}
                        size="small"
                        color={cycle.status === 'Active' ? 'success' : 'default'}
                        sx={{ mr: 1 }}
                      />
                      {cycle.cycle_name}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Tooltip title="Refresh metrics">
              <IconButton onClick={handleRefresh} disabled={refreshing}>
                <RefreshIcon className={refreshing ? 'rotating' : ''} />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      {!assignedReports || assignedReports.length === 0 ? (
        <Alert severity="info" sx={{ mb: 4 }}>
          No report assignments found. Contact your test manager if you expect to have assignments.
        </Alert>
      ) : (
        <>
          {/* Key Metrics Row - All 6 metrics in one row matching Test Executive Dashboard */}
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
                        {metric.subtitle && (
                          <Typography 
                            variant="caption" 
                            color={metric.subtitleColor ? `${metric.subtitleColor}` : 'text.secondary'}
                            display="block"
                          >
                            {metric.subtitle}
                          </Typography>
                        )}
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
          <Box mb={4}>
            <Typography variant="h6" gutterBottom fontWeight="medium">
              Quick Actions
            </Typography>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <QuickActionCard
                  title="My Reports"
                  description="View and manage all your assigned testing reports across cycles"
                  icon={<Assignment />}
                  color={theme.palette.primary.main}
                  onClick={() => navigate('/tester/assignments')}
                  badge={testerMetrics?.pendingReports}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <QuickActionCard
                  title="My Assignments"
                  description="View universal assignments and tasks assigned to you"
                  icon={<AssignmentTurnedIn />}
                  color={theme.palette.secondary.main}
                  onClick={() => navigate('/my-assignments')}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <QuickActionCard
                  title="View Test Cycles"
                  description="Browse test cycles and see your assignments in each cycle"
                  icon={<CalendarToday />}
                  color={theme.palette.info.main}
                  onClick={() => navigate('/cycles')}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <QuickActionCard
                  title="Active Observations"
                  description="Review and manage observations that require your attention"
                  icon={<BugReport />}
                  color={theme.palette.warning.main}
                  onClick={() => {
                    // Navigate to my assignments with observation filter if possible
                    // For now, just go to my assignments page
                    navigate('/my-assignments');
                  }}
                  badge={testerMetrics?.totalObservations}
                />
              </Grid>
            </Grid>
          </Box>

          {/* At Risk Reports Section */}
          {testerMetrics && testerMetrics.atRiskReports > 0 && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight="medium" color="error.main">
                  ⚠️ At Risk Reports ({testerMetrics.atRiskReports})
                </Typography>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<Warning />}
                  onClick={() => navigate('/my-assignments')}
                  size="small"
                >
                  View Details
                </Button>
              </Box>
              <Alert severity="warning" sx={{ mb: 2 }}>
                You have {testerMetrics.atRiskReports} reports that are behind schedule or at risk. 
                Immediate attention required to meet deadlines.
              </Alert>
              <Typography variant="body2" color="text.secondary">
                These reports need immediate attention to avoid missing SLA deadlines. 
                Click "View Details" to see which reports require action.
              </Typography>
            </Paper>
          )}

          {/* Observations Section */}
          {testerMetrics && testerMetrics.totalObservations > 0 && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight="medium" color="secondary.main">
                  🔍 Active Observations ({testerMetrics.totalObservations})
                </Typography>
                <Button
                  variant="outlined"
                  color="secondary"
                  startIcon={<BugReport />}
                  onClick={() => navigate('/my-assignments')}
                  size="small"
                >
                  Review All
                </Button>
              </Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                You have {testerMetrics.totalObservations} observations across your assigned reports 
                that require review and action.
              </Alert>
              <Typography variant="body2" color="text.secondary">
                Observations include data quality issues, control gaps, and other findings that need documentation and resolution. 
                Click "Review All" to manage these observations.
              </Typography>
            </Paper>
          )}

          {/* Active Reports Summary - Only show if no at-risk or observations */}
          {testerMetrics && testerMetrics.activeReports > 0 && 
           testerMetrics.atRiskReports === 0 && testerMetrics.totalObservations === 0 && (
            <Paper sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight="medium" color="success.main">
                  ✅ All Reports On Track
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<ArrowForward />}
                  onClick={() => navigate('/my-assignments')}
                >
                  View All Assignments
                </Button>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Great work! You have {testerMetrics.activeReports} active reports and they are all on track. 
                Continue with your testing activities to maintain this progress.
              </Typography>
            </Paper>
          )}
        </>
      )}
    </Box>
  );
};

export default TesterDashboardEnhanced;