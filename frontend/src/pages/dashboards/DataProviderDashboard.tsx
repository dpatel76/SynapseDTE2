import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Alert,
  IconButton,
  Tooltip,
  Tab,
  Tabs,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Snackbar,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Stack
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Schedule,
  Assessment,
  Visibility,
  Refresh as RefreshIcon,
  Business,
  Analytics,
  Timeline as TimelineIcon,
  Assignment as AssignmentIcon,
  Speed as SpeedIcon,
  Star as StarIcon,
  WorkOutline as WorkOutlineIcon,
  AccessTime as AccessTimeIcon,
  BarChart as BarChartIcon,
  Group as GroupIcon,
  HourglassEmpty as HourglassEmptyIcon
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useLocation, useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { MetricBox } from '../../components/metrics/MetricBox';
import { MetricsGrid } from '../../components/metrics/MetricsGrid';

interface DataProviderMetrics {
  role: string;
  user_id: number;
  overview: {
    total_assigned_attributes: number;
    attributes_provided: number;
    attributes_pending: number;
    attributes_overdue: number;
    average_response_time_hours: number;
    sla_compliance_rate: number;
  };
  workload_distribution: {
    by_report: Array<{
      report_name: string;
      lob: string;
      total_attributes: number;
      provided: number;
      pending: number;
      completion_rate: number;
    }>;
    by_lob: Array<{
      lob_name: string;
      total_attributes: number;
      provided: number;
      pending: number;
      overdue: number;
    }>;
  };
  response_metrics: {
    average_response_time_by_lob: Array<{
      lob_name: string;
      avg_hours: number;
      sla_target_hours: number;
      compliance_rate: number;
    }>;
    response_time_trend: Array<{
      week: string;
      avg_response_hours: number;
      total_responses: number;
    }>;
  };
  quality_metrics: {
    data_quality_score: number;
    accuracy_rate: number;
    completeness_rate: number;
    revision_requests: number;
    quality_trend: Array<{
      month: string;
      quality_score: number;
      accuracy_rate: number;
    }>;
  };
  pending_assignments: Array<{
    cycle_id: number;
    cycle_name: string;
    report_id: number;
    report_name: string;
    attribute_name: string;
    lob: string;
    assigned_date: string;
    due_date: string;
    priority: string;
    days_until_due: number;
  }>;
  recent_activity: Array<{
    action: string;
    report_name: string;
    attribute_name: string;
    timestamp: string;
    status: string;
  }>;
  generated_at: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function CustomTabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`dashboard-tabpanel-${index}`}
      aria-labelledby={`dashboard-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const DataProviderDashboard: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<DataProviderMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<any>(null);
  const [timeFilter, setTimeFilter] = useState('current_cycle');
  
  // Add state for navigation messages
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'warning' | 'error'>('success');

  useEffect(() => {
    loadDashboardMetrics();
  }, [timeFilter]);

  // Handle navigation state messages
  useEffect(() => {
    if (location.state?.message) {
      setSnackbarMessage(location.state.message);
      setSnackbarSeverity(location.state.severity || 'success');
      setSnackbarOpen(true);
      
      // Clear the state to prevent the message from showing again on refresh
      navigate(location.pathname, { replace: true });
    }
  }, [location.state, navigate, location.pathname]);

  const loadDashboardMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock data for development - replace with actual API call
      const mockMetrics: DataProviderMetrics = {
        role: 'Data Provider',
        user_id: user?.user_id || 0,
        overview: {
          total_assigned_attributes: 156,
          attributes_provided: 124,
          attributes_pending: 28,
          attributes_overdue: 4,
          average_response_time_hours: 18.5,
          sla_compliance_rate: 92.3
        },
        workload_distribution: {
          by_report: [
            {
              report_name: "FRB Y9-C Schedule",
              lob: "Corporate Finance",
              total_attributes: 42,
              provided: 38,
              pending: 4,
              completion_rate: 90.5
            },
            {
              report_name: "Call Report RC-R",
              lob: "Consumer Banking",
              total_attributes: 35,
              provided: 30,
              pending: 5,
              completion_rate: 85.7
            },
            {
              report_name: "FR Y-14Q",
              lob: "Risk Management",
              total_attributes: 28,
              provided: 25,
              pending: 3,
              completion_rate: 89.3
            }
          ],
          by_lob: [
            {
              lob_name: "Corporate Finance",
              total_attributes: 68,
              provided: 60,
              pending: 6,
              overdue: 2
            },
            {
              lob_name: "Consumer Banking",
              total_attributes: 52,
              provided: 42,
              pending: 8,
              overdue: 2
            },
            {
              lob_name: "Risk Management",
              total_attributes: 36,
              provided: 22,
              pending: 14,
              overdue: 0
            }
          ]
        },
        response_metrics: {
          average_response_time_by_lob: [
            {
              lob_name: "Corporate Finance",
              avg_hours: 16.2,
              sla_target_hours: 24,
              compliance_rate: 95.5
            },
            {
              lob_name: "Consumer Banking",
              avg_hours: 20.8,
              sla_target_hours: 24,
              compliance_rate: 88.2
            },
            {
              lob_name: "Risk Management",
              avg_hours: 18.5,
              sla_target_hours: 24,
              compliance_rate: 91.7
            }
          ],
          response_time_trend: [
            { week: "Week 1", avg_response_hours: 22.5, total_responses: 32 },
            { week: "Week 2", avg_response_hours: 19.8, total_responses: 28 },
            { week: "Week 3", avg_response_hours: 17.2, total_responses: 35 },
            { week: "Week 4", avg_response_hours: 18.5, total_responses: 29 }
          ]
        },
        quality_metrics: {
          data_quality_score: 94.2,
          accuracy_rate: 96.8,
          completeness_rate: 93.5,
          revision_requests: 8,
          quality_trend: [
            { month: "Oct 2024", quality_score: 92.5, accuracy_rate: 95.2 },
            { month: "Nov 2024", quality_score: 93.8, accuracy_rate: 96.1 },
            { month: "Dec 2024", quality_score: 94.2, accuracy_rate: 96.8 }
          ]
        },
        pending_assignments: [
          {
            cycle_id: 4,
            cycle_name: "Q4 2024",
            report_id: 156,
            report_name: "FRB Y9-C Schedule",
            attribute_name: "Total Assets",
            lob: "Corporate Finance",
            assigned_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
            due_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
            priority: "High",
            days_until_due: 3
          },
          {
            cycle_id: 4,
            cycle_name: "Q4 2024",
            report_id: 157,
            report_name: "Call Report RC-R",
            attribute_name: "Risk-Weighted Assets",
            lob: "Consumer Banking",
            assigned_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
            due_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
            priority: "Medium",
            days_until_due: 5
          }
        ],
        recent_activity: [
          {
            action: "Data Provided",
            report_name: "FRB Y9-C Schedule",
            attribute_name: "Tier 1 Capital",
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            status: "Completed"
          },
          {
            action: "Data Updated",
            report_name: "Call Report RC-R",
            attribute_name: "Total Deposits",
            timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
            status: "Revised"
          }
        ],
        generated_at: new Date().toISOString()
      };

      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setMetrics(mockMetrics);
      
      // In production, replace with:
      // const response = await apiClient.get('/metrics/dashboard/data-provider', {
      //   params: { time_filter: timeFilter }
      // });
      // setMetrics(response.data);
      
    } catch (err: any) {
      console.error('Error loading dashboard metrics:', err);
      setError('Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': case 'provided': return 'success';
      case 'pending': case 'in progress': return 'warning';
      case 'overdue': case 'past due': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const formatPercentage = (value: number) => `${Math.round(value)}%`;

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleViewAssignment = (assignment: any) => {
    navigate(`/cycles/${assignment.cycle_id}/reports/${assignment.report_id}/data-provider`);
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          <DashboardIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Data Provider Dashboard
        </Typography>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          <DashboardIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Data Provider Dashboard
        </Typography>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={loadDashboardMetrics}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      </Box>
    );
  }

  if (!metrics) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          <DashboardIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Data Provider Dashboard
        </Typography>
        <Alert severity="info">
          No dashboard data available.
        </Alert>
      </Box>
    );
  }

  // Prepare metrics for MetricsGrid
  const overviewMetrics = [
    {
      id: 'assigned',
      title: 'Assigned Attributes',
      metrics: [{
        value: metrics.overview.total_assigned_attributes,
        label: 'Total Assigned',
        status: 'info' as const,
        description: 'Total attributes assigned to you across all reports'
      }],
      icon: <AssignmentIcon />,
      color: 'info' as const,
      size: 3
    },
    {
      id: 'provided',
      title: 'Data Provision Status',
      metrics: [{
        value: metrics.overview.attributes_provided,
        label: 'Provided',
        status: 'success' as const,
        description: 'Attributes with data successfully provided'
      }],
      icon: <CheckCircle />,
      color: 'success' as const,
      size: 3
    },
    {
      id: 'pending',
      title: 'Pending Responses',
      metrics: [{
        value: metrics.overview.attributes_pending,
        label: 'Pending',
        status: 'warning' as const,
        description: 'Attributes awaiting data provision'
      }],
      icon: <HourglassEmptyIcon />,
      color: 'warning' as const,
      size: 3
    },
    {
      id: 'overdue',
      title: 'Overdue Items',
      metrics: [{
        value: metrics.overview.attributes_overdue,
        label: 'Overdue',
        status: 'error' as const,
        description: 'Attributes past their SLA deadline'
      }],
      icon: <Warning />,
      color: 'error' as const,
      size: 3
    }
  ];

  const performanceMetrics = [
    {
      id: 'response-time',
      title: 'Response Time',
      metrics: [{
        value: metrics.overview.average_response_time_hours,
        label: 'Average Hours',
        unit: 'hours',
        target: 24,
        description: 'Average time to provide requested data'
      }],
      icon: <AccessTimeIcon />,
      size: 4
    },
    {
      id: 'sla-compliance',
      title: 'SLA Compliance',
      metrics: [{
        value: metrics.overview.sla_compliance_rate,
        label: 'Compliance Rate',
        unit: '%',
        target: 95,
        status: metrics.overview.sla_compliance_rate >= 90 ? 'success' as const : 'warning' as const,
        description: 'Percentage of data provided within SLA'
      }],
      icon: <SpeedIcon />,
      size: 4
    },
    {
      id: 'quality-score',
      title: 'Data Quality',
      metrics: [{
        value: metrics.quality_metrics.data_quality_score,
        label: 'Quality Score',
        unit: '%',
        target: 95,
        status: metrics.quality_metrics.data_quality_score >= 90 ? 'success' as const : 'warning' as const,
        description: 'Overall data quality and accuracy score'
      }],
      icon: <StarIcon />,
      size: 4
    }
  ];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header with Filters */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          <DashboardIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Data Provider Dashboard
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Time Filter</InputLabel>
            <Select
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value)}
              label="Time Filter"
            >
              <MenuItem value="current_cycle">Current Cycle</MenuItem>
              <MenuItem value="last_30_days">Last 30 Days</MenuItem>
              <MenuItem value="last_90_days">Last 90 Days</MenuItem>
              <MenuItem value="year_to_date">Year to Date</MenuItem>
            </Select>
          </FormControl>
          <Tooltip title="Refresh Data">
            <IconButton onClick={loadDashboardMetrics}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Urgent Actions Section */}
      {metrics.overview.attributes_overdue > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="h6">
            <Warning sx={{ mr: 1, verticalAlign: 'middle' }} />
            You have {metrics.overview.attributes_overdue} overdue attributes requiring immediate attention
          </Typography>
        </Alert>
      )}

      {/* Overview Metrics */}
      <MetricsGrid
        title="Overview"
        cards={overviewMetrics}
        columnsXs={12}
        columnsSm={6}
        columnsMd={3}
        columnsLg={3}
      />

      {/* Performance Metrics */}
      <MetricsGrid
        title="Performance Metrics"
        cards={performanceMetrics}
        columnsXs={12}
        columnsSm={6}
        columnsMd={4}
        columnsLg={4}
      />

      {/* Tabbed Content */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Pending Assignments" icon={<Schedule />} />
          <Tab label="Workload Analysis" icon={<WorkOutlineIcon />} />
          <Tab label="Response Analytics" icon={<Analytics />} />
          <Tab label="Quality Trends" icon={<TrendingUp />} />
        </Tabs>
      </Box>

      {/* Pending Assignments Tab */}
      <CustomTabPanel value={tabValue} index={0}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Pending Data Requests
          </Typography>
          
          {metrics.pending_assignments.length === 0 ? (
            <Alert severity="success">
              All data requests have been fulfilled. Great job!
            </Alert>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Report Name</TableCell>
                    <TableCell>Attribute</TableCell>
                    <TableCell>LOB</TableCell>
                    <TableCell>Assigned Date</TableCell>
                    <TableCell>Due Date</TableCell>
                    <TableCell>Days Until Due</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {metrics.pending_assignments.map((assignment, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {assignment.report_name}
                        </Typography>
                      </TableCell>
                      <TableCell>{assignment.attribute_name}</TableCell>
                      <TableCell>
                        <Chip label={assignment.lob} size="small" />
                      </TableCell>
                      <TableCell>
                        {new Date(assignment.assigned_date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        {new Date(assignment.due_date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={`${assignment.days_until_due} days`}
                          size="small"
                          color={
                            assignment.days_until_due <= 1 ? 'error' :
                            assignment.days_until_due <= 3 ? 'warning' : 'success'
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={assignment.priority}
                          size="small"
                          color={getPriorityColor(assignment.priority)}
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="contained"
                          color="primary"
                          onClick={() => handleViewAssignment(assignment)}
                        >
                          Provide Data
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Recent Activity */}
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <List>
              {metrics.recent_activity.map((activity, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body1">
                            {activity.action}: {activity.attribute_name}
                          </Typography>
                          <Chip 
                            label={activity.status}
                            size="small"
                            color={getStatusColor(activity.status)}
                          />
                        </Box>
                      }
                      secondary={
                        <>
                          {activity.report_name} • {new Date(activity.timestamp).toLocaleString()}
                        </>
                      }
                    />
                  </ListItem>
                  {index < metrics.recent_activity.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </Box>
        </Box>
      </CustomTabPanel>

      {/* Workload Analysis Tab */}
      <CustomTabPanel value={tabValue} index={1}>
        <Stack spacing={4}>
          {/* Workload by Report */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Workload by Report
            </Typography>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Report Name</TableCell>
                    <TableCell>LOB</TableCell>
                    <TableCell align="center">Total Attributes</TableCell>
                    <TableCell align="center">Provided</TableCell>
                    <TableCell align="center">Pending</TableCell>
                    <TableCell align="center">Completion Rate</TableCell>
                    <TableCell align="center">Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {metrics.workload_distribution.by_report.map((report) => (
                    <TableRow key={report.report_name}>
                      <TableCell>{report.report_name}</TableCell>
                      <TableCell>
                        <Chip label={report.lob} size="small" />
                      </TableCell>
                      <TableCell align="center">{report.total_attributes}</TableCell>
                      <TableCell align="center">
                        <Typography color="success.main" fontWeight="medium">
                          {report.provided}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography color="warning.main" fontWeight="medium">
                          {report.pending}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Box display="flex" alignItems="center" gap={1}>
                          <LinearProgress 
                            variant="determinate" 
                            value={report.completion_rate} 
                            sx={{ width: 60, height: 6 }}
                            color={
                              report.completion_rate >= 90 ? 'success' :
                              report.completion_rate >= 70 ? 'warning' : 'error'
                            }
                          />
                          <Typography variant="body2">
                            {formatPercentage(report.completion_rate)}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Chip 
                          label={report.completion_rate >= 90 ? 'On Track' : 'In Progress'}
                          size="small"
                          color={report.completion_rate >= 90 ? 'success' : 'warning'}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          {/* Workload by LOB */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Workload Distribution by LOB
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 2 }}>
              {metrics.workload_distribution.by_lob.map((lob) => (
                <Card key={lob.lob_name}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {lob.lob_name}
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">Total</Typography>
                        <Typography variant="h6">{lob.total_attributes}</Typography>
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary">Provided</Typography>
                        <Typography variant="h6" color="success.main">{lob.provided}</Typography>
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary">Pending</Typography>
                        <Typography variant="h6" color="warning.main">{lob.pending}</Typography>
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary">Overdue</Typography>
                        <Typography variant="h6" color="error.main">{lob.overdue}</Typography>
                      </Box>
                    </Box>
                    <Box mt={2}>
                      <LinearProgress 
                        variant="determinate" 
                        value={(lob.provided / lob.total_attributes) * 100}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                        {formatPercentage((lob.provided / lob.total_attributes) * 100)} complete
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Box>
        </Stack>
      </CustomTabPanel>

      {/* Response Analytics Tab */}
      <CustomTabPanel value={tabValue} index={2}>
        <Stack spacing={4}>
          {/* Response Time by LOB */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Average Response Time by LOB
            </Typography>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>LOB</TableCell>
                    <TableCell align="center">Avg Response Time</TableCell>
                    <TableCell align="center">SLA Target</TableCell>
                    <TableCell align="center">SLA Compliance</TableCell>
                    <TableCell align="center">Performance</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {metrics.response_metrics.average_response_time_by_lob.map((lob) => (
                    <TableRow key={lob.lob_name}>
                      <TableCell>{lob.lob_name}</TableCell>
                      <TableCell align="center">
                        <Typography 
                          color={lob.avg_hours <= lob.sla_target_hours ? 'success.main' : 'error.main'}
                          fontWeight="medium"
                        >
                          {lob.avg_hours} hours
                        </Typography>
                      </TableCell>
                      <TableCell align="center">{lob.sla_target_hours} hours</TableCell>
                      <TableCell align="center">
                        <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                          <LinearProgress 
                            variant="determinate" 
                            value={lob.compliance_rate} 
                            sx={{ width: 60, height: 6 }}
                            color={
                              lob.compliance_rate >= 90 ? 'success' :
                              lob.compliance_rate >= 75 ? 'warning' : 'error'
                            }
                          />
                          <Typography variant="body2">
                            {formatPercentage(lob.compliance_rate)}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Chip 
                          label={
                            lob.compliance_rate >= 90 ? 'Excellent' :
                            lob.compliance_rate >= 75 ? 'Good' : 'Needs Improvement'
                          }
                          size="small"
                          color={
                            lob.compliance_rate >= 90 ? 'success' :
                            lob.compliance_rate >= 75 ? 'warning' : 'error'
                          }
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          {/* Response Time Trend */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Response Time Trend (Weekly)
            </Typography>
            <Card>
              <CardContent>
                {metrics.response_metrics.response_time_trend.map((week) => (
                  <Box key={week.week} sx={{ mb: 2 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="body2">{week.week}</Typography>
                      <Box display="flex" gap={2}>
                        <Typography variant="body2" color="text.secondary">
                          {week.total_responses} responses
                        </Typography>
                        <Typography 
                          variant="body2" 
                          color={week.avg_response_hours <= 24 ? 'success.main' : 'error.main'}
                          fontWeight="medium"
                        >
                          {week.avg_response_hours} hrs avg
                        </Typography>
                      </Box>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={Math.min((24 / week.avg_response_hours) * 100, 100)}
                      sx={{ height: 8, borderRadius: 4 }}
                      color={week.avg_response_hours <= 24 ? 'success' : 'error'}
                    />
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Box>
        </Stack>
      </CustomTabPanel>

      {/* Quality Trends Tab */}
      <CustomTabPanel value={tabValue} index={3}>
        <Stack spacing={4}>
          {/* Quality Metrics Overview */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Data Quality Metrics
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
              <MetricBox
                title="Overall Quality Score"
                value={metrics.quality_metrics.data_quality_score}
                unit="%"
                target={95}
                status={metrics.quality_metrics.data_quality_score >= 90 ? 'success' : 'warning'}
                icon={<StarIcon />}
                size="medium"
              />
              <MetricBox
                title="Accuracy Rate"
                value={metrics.quality_metrics.accuracy_rate}
                unit="%"
                target={95}
                status={metrics.quality_metrics.accuracy_rate >= 95 ? 'success' : 'warning'}
                icon={<CheckCircle />}
                size="medium"
              />
              <MetricBox
                title="Completeness Rate"
                value={metrics.quality_metrics.completeness_rate}
                unit="%"
                target={95}
                status={metrics.quality_metrics.completeness_rate >= 90 ? 'success' : 'warning'}
                icon={<Assessment />}
                size="medium"
              />
              <MetricBox
                title="Revision Requests"
                value={metrics.quality_metrics.revision_requests}
                status={metrics.quality_metrics.revision_requests <= 5 ? 'success' : 'warning'}
                description="Number of data revisions requested this period"
                icon={<Warning />}
                size="medium"
              />
            </Box>
          </Box>

          {/* Quality Trend Chart */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Quality Score Trend
            </Typography>
            <Card>
              <CardContent>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Month</TableCell>
                        <TableCell align="center">Quality Score</TableCell>
                        <TableCell align="center">Accuracy Rate</TableCell>
                        <TableCell align="center">Trend</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {metrics.quality_metrics.quality_trend.map((month, index) => {
                        const prevMonth = index > 0 ? metrics.quality_metrics.quality_trend[index - 1] : null;
                        const trend = prevMonth ? month.quality_score - prevMonth.quality_score : 0;
                        
                        return (
                          <TableRow key={month.month}>
                            <TableCell>{month.month}</TableCell>
                            <TableCell align="center">
                              <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                                <Typography fontWeight="medium">
                                  {formatPercentage(month.quality_score)}
                                </Typography>
                                <LinearProgress 
                                  variant="determinate" 
                                  value={month.quality_score} 
                                  sx={{ width: 60, height: 6 }}
                                  color={month.quality_score >= 90 ? 'success' : 'warning'}
                                />
                              </Box>
                            </TableCell>
                            <TableCell align="center">
                              {formatPercentage(month.accuracy_rate)}
                            </TableCell>
                            <TableCell align="center">
                              {trend !== 0 && (
                                <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                                  {trend > 0 ? 
                                    <TrendingUp color="success" fontSize="small" /> : 
                                    <TrendingDown color="error" fontSize="small" />
                                  }
                                  <Typography 
                                    variant="caption" 
                                    color={trend > 0 ? 'success.main' : 'error.main'}
                                  >
                                    {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
                                  </Typography>
                                </Box>
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Box>
        </Stack>
      </CustomTabPanel>

      {/* Assignment Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Assignment Details</DialogTitle>
        <DialogContent>
          {selectedAssignment && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedAssignment.attribute_name}
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">Report</Typography>
                  <Typography variant="body1">{selectedAssignment.report_name}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">LOB</Typography>
                  <Typography variant="body1">{selectedAssignment.lob}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Due Date</Typography>
                  <Typography variant="body1">
                    {new Date(selectedAssignment.due_date).toLocaleDateString()}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Priority</Typography>
                  <Chip 
                    label={selectedAssignment.priority}
                    color={getPriorityColor(selectedAssignment.priority)}
                    size="small"
                  />
                </Box>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          <Button 
            variant="contained" 
            color="primary"
            onClick={() => selectedAssignment && handleViewAssignment(selectedAssignment)}
          >
            Go to Assignment
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar for navigation messages */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setSnackbarOpen(false)} 
          severity={snackbarSeverity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default DataProviderDashboard;