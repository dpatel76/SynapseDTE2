import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Button,
  Stack,
  Tabs,
  Tab,
  LinearProgress,
  Divider,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Pending as PendingIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  OpenInNew as OpenInNewIcon,
  TrendingUp as TrendingUpIcon,
  Dashboard as DashboardIcon,
  Speed as SpeedIcon,
  BarChart as BarChartIcon,
  Assessment as AssessmentIcon,
  Group as GroupIcon,
  Timeline as TimelineIcon,
  CompareArrows as CompareArrowsIcon,
  Map as MapIcon,
  TrendingDown as TrendingDownIcon,
  Star as StarIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'react-hot-toast';
import { MetricBox } from '../../components/metrics/MetricBox';
import { MetricsGrid } from '../../components/metrics/MetricsGrid';

interface DataExecutiveAssignment {
  assignment_id: number;
  cycle_id: number;
  cycle_name: string;
  report_id: number;
  report_name: string;
  attribute_id: number;
  attribute_name: string;
  attribute_description: string;
  data_provider_id: number;
  data_provider_name: string;
  data_provider_email: string;
  lob_name: string;
  assigned_at: string;
  status: string;
}

// Type alias for backward compatibility
type CDOAssignment = DataExecutiveAssignment;

interface DataExecutiveMetrics {
  total_assignments: number;
  active_cycles: number;
  completed_assignments: number;
  pending_assignments: number;
  average_response_time: number;
  completion_rate: number;
}

interface DataExecutiveWorkflowStatus {
  cycle_id: number;
  cycle_name: string;
  report_id: number;
  report_name: string;
  current_phase: string;
  phase_status: string;
  overall_progress: number;
  total_assignments: number;
  completed_assignments: number;
  pending_assignments: number;
  workflow_status: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`cdo-tabpanel-${index}`}
      aria-labelledby={`cdo-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const DataExecutiveDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<DataExecutiveAssignment[]>([]);
  const [metrics, setMetrics] = useState<DataExecutiveMetrics | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<DataExecutiveWorkflowStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [timeFilter, setTimeFilter] = useState('current_cycle');

  useEffect(() => {
    if (user) {
      loadDashboardData();
    }
  }, [timeFilter, user]);

  const loadDashboardData = async () => {
    console.log('[Data Executive Dashboard] loadDashboardData called');
    console.log('[Data Executive Dashboard] User state:', user);
    console.log('[Data Executive Dashboard] User ID:', user?.user_id);
    console.log('[Data Executive Dashboard] User role:', user?.role);
    console.log('[Data Executive Dashboard] User email:', user?.email);
    
    if (!user) {
      console.log('[Data Executive Dashboard] No user authenticated, skipping data load');
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      console.log('[Data Executive Dashboard] Loading dashboard data...');
      console.log('[Data Executive Dashboard] Current user:', user);
      
      // Load universal assignments for Data Executive
      console.log('[Data Executive Dashboard] Current user ID:', user?.user_id);
      console.log('[Data Executive Dashboard] Loading assignments...');
      
      console.log('[Data Executive Dashboard] Making API call to /universal-assignments/assignments');
      const assignmentsResponse = await apiClient.get('/universal-assignments/assignments', {
        params: {
          assignment_type_filter: 'LOB Assignment,Data Upload Request',
          status_filter: 'Assigned,Acknowledged,In Progress,Completed',
          limit: 50
        }
      });
      console.log('[Data Executive Dashboard] API call completed, status:', assignmentsResponse.status);
      
      // Also get assignment metrics
      const metricsResponse = await apiClient.get('/universal-assignments/assignments/metrics', {
        params: {
          role: 'Data Executive',
          assignment_type: 'LOB Assignment'
        }
      });
      
      const assignmentsData = assignmentsResponse.data;
      const metricsData = metricsResponse.data;
      
      console.log('[Data Executive Dashboard] Universal assignments:', assignmentsData);
      console.log('[Data Executive Dashboard] Assignment metrics:', metricsData);

      // Process universal assignments for display
      if (assignmentsData && assignmentsData.length > 0) {
        console.log('[Data Executive Dashboard] Processing universal assignments...');
        
        const processedAssignments = assignmentsData.map((assignment: any) => ({
          assignment_id: assignment.assignment_id,
          cycle_id: assignment.context_data?.cycle_id || 0,
          cycle_name: `Cycle ${assignment.context_data?.cycle_id || 'Unknown'}`,
          report_id: assignment.context_data?.report_id || 0,
          report_name: assignment.title || `Report ${assignment.context_data?.report_id || 'Unknown'}`,
          attribute_id: 0, // Universal assignments are task-level, not attribute-level
          attribute_name: assignment.assignment_type || 'Task Assignment',
          attribute_description: assignment.description || '',
          data_provider_id: assignment.to_user_id || 0,
          data_provider_name: assignment.to_user_name || 'Unknown',
          data_provider_email: 'N/A', // Not included in universal assignment response
          lob_name: assignment.context_data?.phase_name || 'Data Provider ID',
          assigned_at: assignment.assigned_at,
          status: assignment.status
        }));
        
        console.log('[Data Executive Dashboard] Setting assignments:', processedAssignments);
        console.log('[Data Executive Dashboard] Assignment count:', processedAssignments.length);
        setAssignments(processedAssignments);
      } else {
        console.log('[Data Executive Dashboard] No universal assignments found');
        setAssignments([]);
      }

      // Set metrics from universal assignment metrics
      if (metricsData) {
        console.log('[Data Executive Dashboard] Processing universal assignment metrics:', metricsData);
        const dashboardMetrics = {
          total_assignments: metricsData.total_assignments || 0,
          active_cycles: metricsData.active_cycles || 0,
          completed_assignments: metricsData.completed_assignments || 0,
          pending_assignments: metricsData.pending_assignments || 0,
          average_response_time: metricsData.average_response_time || 0,
          completion_rate: metricsData.completion_rate || 0
        };
        console.log('[Data Executive Dashboard] Setting metrics:', dashboardMetrics);
        setMetrics(dashboardMetrics);
      } else {
        console.log('[Data Executive Dashboard] No universal assignment metrics found');
        setMetrics(null);
      }

      // For workflow status, we'll keep it empty for now since this data comes from different source
      // Can be enhanced later to get workflow status from universal assignment context data
      setWorkflowStatus([]);

    } catch (error: any) {
      console.error('[Data Executive Dashboard] Error loading dashboard data:', error);
      console.error('[Data Executive Dashboard] Error response:', error.response);
      console.error('[Data Executive Dashboard] Error data:', error.response?.data);
      const errorMessage = error.response?.data?.detail || 'Failed to load dashboard data';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadDashboardData();
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed': return 'success';
      case 'In Progress': return 'info';
      case 'Assigned': return 'warning';
      case 'Overdue': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Completed': return <CheckCircleIcon color="success" />;
      case 'In Progress': return <PendingIcon color="info" />;
      case 'Assigned': return <WarningIcon color="warning" />;
      case 'Overdue': return <WarningIcon color="error" />;
      default: return <PendingIcon />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const navigateToAssignment = (assignment: CDOAssignment) => {
    // Validate assignment data before navigation
    if (!assignment.cycle_id || !assignment.report_id || assignment.cycle_id === 0 || assignment.report_id === 0) {
      console.error('Invalid assignment data:', assignment);
      console.log('Available assignment data:', assignment);
      
      // Show a more user-friendly message
      toast.error(`Unable to navigate to assignment details. Missing cycle or report information for "${assignment.attribute_name}".`);
      return;
    }
    
    try {
      console.log(`Navigating to: /cycles/${assignment.cycle_id}/reports/${assignment.report_id}/data-owner`);
      navigate(`/cycles/${assignment.cycle_id}/reports/${assignment.report_id}/data-owner`);
    } catch (error) {
      console.error('Navigation error:', error);
      toast.error('Unable to navigate to assignment details');
    }
  };

  const navigateToCycle = (cycleId: number) => {
    // Validate cycle ID before navigation
    if (!cycleId || cycleId === 0) {
      console.error('Invalid cycle ID:', cycleId);
      toast.error('Unable to navigate: Invalid cycle ID');
      return;
    }
    
    try {
      console.log(`Navigating to: /cycles/${cycleId}`);
      navigate(`/cycles/${cycleId}`);
    } catch (error) {
      console.error('Navigation error:', error);
      toast.error('Unable to navigate to cycle details');
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 0 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 0 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={handleRefresh} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    );
  }

  // Group assignments by cycle
  const assignmentsByCycle = assignments.reduce((acc, assignment) => {
    const cycleKey = `${assignment.cycle_id}-${assignment.cycle_name}`;
    if (!acc[cycleKey]) {
      acc[cycleKey] = [];
    }
    acc[cycleKey].push(assignment);
    return acc;
  }, {} as Record<string, CDOAssignment[]>);

  // Prepare metrics for MetricsGrid
  const overviewMetrics = metrics ? [
    {
      id: 'total-assignments',
      title: 'Total Assignments',
      metrics: [{
        value: metrics.total_assignments,
        label: 'Across LOBs',
        description: 'Total data provider assignments under your oversight'
      }],
      icon: <AssignmentIcon />,
      color: 'primary' as const,
      size: 3
    },
    {
      id: 'active-cycles',
      title: 'Active Cycles',
      metrics: [{
        value: metrics.active_cycles,
        label: 'In Progress',
        description: 'Number of active test cycles'
      }],
      icon: <BusinessIcon />,
      color: 'info' as const,
      size: 3
    },
    {
      id: 'completion-rate',
      title: 'Completion Rate',
      metrics: [{
        value: metrics.completion_rate,
        label: 'Overall',
        unit: '%',
        target: 95,
        status: metrics.completion_rate >= 90 ? 'success' as const : 'warning' as const
      }],
      icon: <TrendingUpIcon />,
      color: 'success' as const,
      size: 3
    },
    {
      id: 'response-time',
      title: 'Avg Response Time',
      metrics: [{
        value: metrics.average_response_time,
        label: 'Hours',
        unit: 'hours',
        target: 24,
        status: metrics.average_response_time <= 24 ? 'success' as const : 'warning' as const
      }],
      icon: <SpeedIcon />,
      color: 'warning' as const,
      size: 3
    }
  ] : [];

  const performanceMetrics = [];

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          <DashboardIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Data Executive Dashboard
        </Typography>
        <IconButton onClick={handleRefresh} title="Refresh Data">
          <RefreshIcon />
        </IconButton>
      </Box>

      {/* Overview Cards */}
      {metrics && (
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: 'repeat(1, 1fr)', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: 3,
          mb: 4 
        }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="primary">
                    {metrics.total_assignments || 0}
                  </Typography>
                  <Typography variant="subtitle2">Total Assignments</Typography>
                  <Typography variant="caption" color="text.secondary">
                    LOB assignments
                  </Typography>
                </Box>
                <AssignmentIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="success.main">
                    {metrics.completed_assignments || 0}
                  </Typography>
                  <Typography variant="subtitle2">Completed</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Finished assignments
                  </Typography>
                </Box>
                <CheckCircleIcon color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="warning.main">
                    {metrics.pending_assignments || 0}
                  </Typography>
                  <Typography variant="subtitle2">Pending</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Awaiting action
                  </Typography>
                </Box>
                <PendingIcon color="warning" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="info.main">
                    {Math.round(metrics.completion_rate || 0)}%
                  </Typography>
                  <Typography variant="subtitle2">Completion Rate</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Overall progress
                  </Typography>
                </Box>
                <TrendingUpIcon color="info" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Assignment Progress */}
      {metrics && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3, mb: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Assignment Progress Overview
              </Typography>
              <Box sx={{ mb: 3 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="body2">Overall Completion Rate</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {Math.round(metrics.completion_rate || 0)}%
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={metrics.completion_rate || 0} 
                  sx={{ height: 8, borderRadius: 4 }}
                  color={(metrics.completion_rate || 0) >= 80 ? 'success' : 
                         (metrics.completion_rate || 0) >= 60 ? 'warning' : 'error'}
                />
              </Box>
              
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
                <Box textAlign="center" p={1}>
                  <Typography variant="h6" color="success.main">
                    {metrics.completed_assignments || 0}
                  </Typography>
                  <Typography variant="caption">Completed</Typography>
                </Box>
                <Box textAlign="center" p={1}>
                  <Typography variant="h6" color="warning.main">
                    {metrics.pending_assignments || 0}
                  </Typography>
                  <Typography variant="caption">Pending</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Button
                  variant="outlined"
                  startIcon={<AssignmentIcon />}
                  onClick={() => navigate('/cycles')}
                  fullWidth
                >
                  View Test Cycles
                </Button>
                {assignments.length > 0 && (
                  <Button
                    variant="outlined"
                    startIcon={<OpenInNewIcon />}
                    onClick={() => navigateToAssignment(assignments[0])}
                    fullWidth
                  >
                    Latest Assignment
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Assignments Table */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="Data Executive dashboard tabs">
            <Tab label="My Assignments" icon={<AssignmentIcon />} />
            <Tab label="Assignment Details" icon={<BusinessIcon />} />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          {/* My Assignments Tab */}
          <Stack spacing={4}>
            <Typography variant="h6" gutterBottom>
              Current Assignments
            </Typography>
            
            {assignments.length === 0 ? (
              <Alert severity="info">
                No assignments found. You'll see LOB assignments here when testers start the Data Provider ID phase.
              </Alert>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Assignment</TableCell>
                      <TableCell>Cycle</TableCell>
                      <TableCell>Report</TableCell>
                      <TableCell align="center">Status</TableCell>
                      <TableCell align="center">Assigned Date</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {assignments.map((assignment) => (
                      <TableRow key={assignment.assignment_id}>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {assignment.attribute_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {assignment.attribute_description}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>{assignment.cycle_name}</TableCell>
                        <TableCell>{assignment.report_name}</TableCell>
                        <TableCell align="center">
                          <Chip
                            label={assignment.status}
                            size="small"
                            color={getStatusColor(assignment.status)}
                            icon={getStatusIcon(assignment.status)}
                          />
                        </TableCell>
                        <TableCell align="center">
                          {assignment.assigned_at ? formatDate(assignment.assigned_at) : 'N/A'}
                        </TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            onClick={() => navigateToAssignment(assignment)}
                            disabled={!assignment.cycle_id || !assignment.report_id}
                          >
                            <OpenInNewIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Stack>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* Assignment Details Tab */}
          <Stack spacing={4}>
            <Typography variant="h6" gutterBottom>
              Assignment Details
            </Typography>
            
            {assignments.length === 0 ? (
              <Alert severity="info">
                No assignment details available. Details will appear here once you have active assignments.
              </Alert>
            ) : (
              <Box>
                {Object.entries(assignmentsByCycle).map(([cycleKey, cycleAssignments]) => (
                  <Card key={cycleKey} sx={{ mb: 3 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {cycleAssignments[0].cycle_name} - {cycleAssignments[0].report_name}
                      </Typography>
                      <Divider sx={{ mb: 2 }} />
                      
                      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mb: 2 }}>
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Total Assignments
                          </Typography>
                          <Typography variant="h6">
                            {cycleAssignments.length}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Completed
                          </Typography>
                          <Typography variant="h6" color="success.main">
                            {cycleAssignments.filter(a => a.status === 'Completed').length}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            In Progress
                          </Typography>
                          <Typography variant="h6" color="info.main">
                            {cycleAssignments.filter(a => a.status === 'In Progress').length}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Pending
                          </Typography>
                          <Typography variant="h6" color="warning.main">
                            {cycleAssignments.filter(a => a.status === 'Assigned').length}
                          </Typography>
                        </Box>
                      </Box>

                      <List dense>
                        {cycleAssignments.map((assignment) => (
                          <ListItem 
                            key={assignment.assignment_id}
                            sx={{ 
                              border: 1, 
                              borderColor: 'divider', 
                              borderRadius: 1, 
                              mb: 1,
                              '&:hover': { bgcolor: 'action.hover' }
                            }}
                          >
                            <ListItemIcon>
                              {getStatusIcon(assignment.status)}
                            </ListItemIcon>
                            <ListItemText
                              primary={assignment.attribute_name}
                              secondary={`Assigned: ${assignment.assigned_at ? formatDate(assignment.assigned_at) : 'N/A'}`}
                            />
                            <ListItemSecondaryAction>
                              <Box display="flex" gap={1} alignItems="center">
                                <Chip
                                  label={assignment.status}
                                  size="small"
                                  color={getStatusColor(assignment.status)}
                                />
                                <IconButton
                                  size="small"
                                  onClick={() => navigateToAssignment(assignment)}
                                  disabled={!assignment.cycle_id || !assignment.report_id}
                                >
                                  <OpenInNewIcon />
                                </IconButton>
                              </Box>
                            </ListItemSecondaryAction>
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </Stack>
        </TabPanel>
      </Card>
    </Box>
  );
};

export default DataExecutiveDashboard; 