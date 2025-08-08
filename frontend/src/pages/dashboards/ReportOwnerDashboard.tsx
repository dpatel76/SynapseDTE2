import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
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
  Stack,
  Divider,
  Badge
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
  FilterList,
  Business,
  Analytics,
  Timeline as TimelineIcon,
  Person as PersonIcon,
  RateReview as ReviewIcon,
  Timer as TimerIcon,
  ThumbDown as ThumbDownIcon,
  Replay as ReplayIcon,
  Speed as SpeedIcon,
  BarChart as BarChartIcon
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useLocation, useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { MetricBox } from '../../components/metrics/MetricBox';
import { MetricsGrid } from '../../components/metrics/MetricsGrid';

interface ReportOwnerMetrics {
  role: string;
  user_id: number;
  overview: {
    total_reports: number;
    active_cycles: number;
    pending_approvals: number;
    reports_on_track: number;
    reports_at_risk: number;
    reports_past_due: number;
  };
  approval_metrics: {
    scoping_pending: number;
    sampling_pending: number;
    observations_pending: number;
    average_approval_time_hours: number;
    approval_sla_compliance: number;
  };
  testing_progress: {
    reports_by_phase: {
      planning: number;
      scoping: number;
      sampling: number;
      testing: number;
      observations: number;
      completed: number;
    };
    completion_rates: {
      current_cycle: number;
      previous_cycle: number;
      trend: string;
    };
  };
  quality_trends: {
    observations_by_month: Array<{
      month: string;
      total_observations: number;
      critical_observations: number;
      resolved_observations: number;
    }>;
    quality_score_trend: Array<{
      cycle: string;
      quality_score: number;
    }>;
  };
  cross_lob_analysis: {
    reports_by_lob: Array<{
      lob_name: string;
      total_reports: number;
      completed_reports: number;
      completion_rate: number;
      average_cycle_time_days: number;
    }>;
  };
  escalations: {
    pending_escalations: number;
    escalations_by_type: Array<{
      escalation_type: string;
      count: number;
    }>;
  };
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

// Add interface for pending reviews
interface PendingReview {
  cycle_id: number;
  report_id: number;
  report_name: string;
  lob: string;
  submitted_by: string;
  submitted_date: string;
  attributes_selected: number;
  total_attributes: number;
  priority: 'High' | 'Medium' | 'Low';
}

const ReportOwnerDashboard: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<ReportOwnerMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [assignmentTabValue, setAssignmentTabValue] = useState(0); // 0 = pending, 1 = completed
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedLOB, setSelectedLOB] = useState<any>(null);
  const [timeFilter, setTimeFilter] = useState('current_cycle');
  
  // Add state for pending reviews
  const [pendingReviews, setPendingReviews] = useState<PendingReview[]>([]);
  const [pendingReviewsLoading, setPendingReviewsLoading] = useState(false);
  
  // Add state for pending sample selection reviews
  const [pendingSampleReviews, setPendingSampleReviews] = useState<any[]>([]);
  const [pendingSampleReviewsLoading, setPendingSampleReviewsLoading] = useState(false);
  
  // Add state for pending assignments
  const [pendingAssignments, setPendingAssignments] = useState<any[]>([]);
  const [pendingAssignmentsLoading, setPendingAssignmentsLoading] = useState(false);
  
  // Add state for completed assignments
  const [completedAssignments, setCompletedAssignments] = useState<any[]>([]);
  const [completedAssignmentsLoading, setCompletedAssignmentsLoading] = useState(false);
  
  // Add state for navigation messages
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'warning' | 'error'>('success');

  useEffect(() => {
    loadDashboardMetrics();
    loadPendingReviews(); // Load pending reviews
    loadPendingSampleReviews(); // Load pending sample reviews
    loadPendingAssignments(); // Load pending assignments
    loadCompletedAssignments(); // Load completed assignments
  }, [timeFilter]);

  // Refresh assignments when window regains focus (user returns from assignment)
  useEffect(() => {
    const handleFocus = () => {
      // Refresh assignments when user returns to dashboard
      loadPendingAssignments();
      loadCompletedAssignments();
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);

  // Handle navigation state messages
  useEffect(() => {
    if (location.state?.message) {
      setSnackbarMessage(location.state.message);
      setSnackbarSeverity(location.state.severity || 'success');
      setSnackbarOpen(true);
      
      // Refresh pending reviews when returning from a review submission
      loadPendingReviews();
      loadPendingSampleReviews();
      loadPendingAssignments();
      loadCompletedAssignments();
      
      // Clear the state to prevent the message from showing again on refresh
      navigate(location.pathname, { replace: true });
    }
  }, [location.state, navigate, location.pathname]);

  const loadDashboardMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/metrics/dashboard/current-user', {
        params: { time_filter: timeFilter }
      });
      setMetrics(response.data);
    } catch (err: any) {
      console.error('Error loading dashboard metrics:', err);
      setError('Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  // Add function to load pending reviews
  const loadPendingReviews = async () => {
    try {
      setPendingReviewsLoading(true);
      
      // Use Universal Assignments to get pending scoping reviews
      const response = await apiClient.get('/universal-assignments/assignments', {
        params: {
          assignment_type_filter: 'Scoping Approval',
          status_filter: 'Assigned'
          // No need for to_user_id - API uses current authenticated user
        }
      });
      
      // Transform Universal Assignments to PendingReview format
      const pendingReviews = response.data.map((assignment: any) => {
        const contextData = assignment.context_data || {};
        
        // Use actual user data from the enhanced API response
        const submitterName = assignment.from_user 
          ? `${assignment.from_user.first_name} ${assignment.from_user.last_name}`
          : 'Unknown';
          
        // Use submission date from context data if available, otherwise use assignment creation date
        const submissionDate = contextData.submitted_at || assignment.created_at;
        
        return {
          cycle_id: contextData.cycle_id,
          report_id: contextData.report_id,
          report_name: contextData.report_name || `Report ${contextData.report_id}`,
          cycle_name: contextData.cycle_name || `Cycle ${contextData.cycle_id}`,
          lob: contextData.lob || 'Unknown', // Still needs enhancement but better fallback
          submitted_by: submitterName,
          submitted_date: submissionDate,
          attributes_selected: contextData.scoped_attributes || 0,
          total_attributes: contextData.total_attributes || 0,
          priority: assignment.priority || 'Medium',
          assignment_id: assignment.assignment_id
        };
      });
      
      setPendingReviews(pendingReviews);
      
    } catch (error: any) {
      console.error('Error loading pending reviews:', error);
      // Set empty array on error
      setPendingReviews([]);
      
    } finally {
      setPendingReviewsLoading(false);
    }
  };

  // Add function to load pending sample selection reviews
  const loadPendingSampleReviews = async () => {
    try {
      setPendingSampleReviewsLoading(true);
      
      // Use Universal Assignments to get pending sample selection reviews
      const response = await apiClient.get('/universal-assignments/assignments', {
        params: {
          assignment_type_filter: 'Sample Selection Approval',
          status_filter: 'Assigned'
          // No need for to_user_id - API uses current authenticated user
        }
      });
      
      // Transform Universal Assignments to PendingSampleReview format
      const pendingSampleReviews = response.data.map((assignment: any) => ({
        cycle_id: assignment.context_data?.cycle_id,
        report_id: assignment.context_data?.report_id,
        report_name: assignment.context_data?.report_name || `Report ${assignment.context_data?.report_id}`,
        cycle_name: assignment.context_data?.cycle_name || `Cycle ${assignment.context_data?.cycle_id}`,
        lob: assignment.context_data?.lob || 'Unknown',
        submitted_by: assignment.from_user 
          ? `${assignment.from_user.first_name} ${assignment.from_user.last_name}`
          : 'Unknown',
        submitted_date: assignment.created_at,
        samples_selected: assignment.context_data?.samples_selected || 0,
        total_samples: assignment.context_data?.total_samples || 0,
        priority: assignment.priority || 'Medium',
        assignment_id: assignment.assignment_id
      }));
      
      setPendingSampleReviews(pendingSampleReviews);
      
    } catch (error: any) {
      console.error('Error loading pending sample reviews:', error);
      setPendingSampleReviews([]);
    } finally {
      setPendingSampleReviewsLoading(false);
    }
  };

  // Add function to load pending assignments
  const loadPendingAssignments = async () => {
    setPendingAssignmentsLoading(true);
    try {
      // Use universal assignments endpoint with filtering for current user
      console.log('🔄 Loading pending assignments...');
      const response = await apiClient.get('/universal-assignments/assignments', {
        params: {
          status_filter: 'Assigned,Acknowledged,In Progress',
          limit: 20
        }
      });
      console.log('✅ Pending assignments loaded successfully:', response.data);
      
      // Filter out Scoping Approval and Sample Selection Approval assignments as they're already shown in pendingReviews/pendingSampleReviews
      const filteredAssignments = response.data.filter((assignment: any) => 
        assignment.assignment_type !== 'Scoping Approval' && 
        assignment.assignment_type !== 'Sample Selection Approval'
      );
      
      setPendingAssignments(filteredAssignments);
      
    } catch (error: any) {
      console.error('Error loading universal assignments:', error);
      console.error('Full error details:', error.response?.data);
      setPendingAssignments([]);
    } finally {
      setPendingAssignmentsLoading(false);
    }
  };

  // Add function to load completed assignments
  const loadCompletedAssignments = async () => {
    setCompletedAssignmentsLoading(true);
    try {
      // First check all assignments to see what statuses exist
      console.log('🔍 Loading all assignments to check statuses...');
      const allResponse = await apiClient.get('/universal-assignments/assignments', {
        params: { limit: 100 }
      });
      console.log('📋 All assignments:', allResponse.data);
      console.log('📊 Assignment statuses found:', Array.from(new Set(allResponse.data.map((a: any) => a.status))));
      
      // Use universal assignments endpoint with filtering for completed assignments
      console.log('🔍 Loading completed assignments...');
      const response = await apiClient.get('/universal-assignments/assignments', {
        params: {
          status_filter: 'Completed,Approved,Rejected,Cancelled,Escalated',
          limit: 50 // Show more completed assignments for history
        }
      });
      console.log('📋 Completed assignments response:', response.data);
      setCompletedAssignments(response.data);
      
    } catch (error: any) {
      console.error('Error loading completed assignments:', error);
      console.error('Full error details:', error.response?.data);
      setCompletedAssignments([]);
    } finally {
      setCompletedAssignmentsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'on track': case 'completed': return 'success';
      case 'at risk': return 'warning';
      case 'past due': return 'error';
      default: return 'default';
    }
  };

  const getTrendIcon = (trend: string) => {
    return trend === 'up' ? <TrendingUp color="success" /> : 
           trend === 'down' ? <TrendingDown color="error" /> : 
           <TimelineIcon color="action" />;
  };

  const formatPercentage = (value: number) => `${Math.round(value)}%`;

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          <DashboardIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Report Owner Dashboard
        </Typography>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Typography>Loading dashboard metrics...</Typography>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          <DashboardIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Report Owner Dashboard
        </Typography>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={() => { loadDashboardMetrics(); loadPendingReviews(); }}>
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
          Report Owner Dashboard
        </Typography>
        <Alert severity="info">
          No dashboard data available.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header with Filters */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          <DashboardIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Report Owner Dashboard
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
            <IconButton onClick={() => { loadDashboardMetrics(); loadPendingReviews(); loadPendingSampleReviews(); }}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Quick Access Section for Pending Reviews */}
      <Card sx={{ mb: 3, border: 2, borderColor: 'warning.main', bgcolor: 'warning.50' }}>
        <CardContent>
          <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Schedule color="warning" />
            Quick Access - Pending Reviews ({pendingReviews.length + pendingSampleReviews.length + pendingAssignments.length})
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Reports with scoping decisions and sample selections awaiting your approval. Click "Review Now" to approve or decline.
          </Typography>
          
          {(pendingReviewsLoading || pendingSampleReviewsLoading || pendingAssignmentsLoading) ? (
            <LinearProgress />
          ) : (pendingReviews.length === 0 && pendingSampleReviews.length === 0 && pendingAssignments.length === 0) ? (
            <Alert severity="info">
              <Typography variant="h6">✅ All Caught Up!</Typography>
              <Typography>No reviews are pending at this time.</Typography>
            </Alert>
          ) : (
            <Box sx={{ display: 'grid', gap: 2 }}>
              {pendingReviews.map((review) => (
                <Card key={`${review.cycle_id}-${review.report_id}`} sx={{ border: 1, borderColor: 'grey.300' }}>
                  <CardContent sx={{ py: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      {/* Left side - Report info */}
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="h6" fontWeight="bold" gutterBottom>
                          {review.report_name}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 2 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Business fontSize="small" color="action" />
                            <Typography variant="body2">{review.lob}</Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <PersonIcon fontSize="small" color="action" />
                            <Typography variant="body2">Submitted by {review.submitted_by}</Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <TimelineIcon fontSize="small" color="action" />
                            <Typography variant="body2">
                              {new Date(review.submitted_date).toLocaleDateString()}
                            </Typography>
                          </Box>
                        </Box>
                        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                          <Typography variant="body1" fontWeight="medium">
                            {review.attributes_selected} of {review.total_attributes} attributes selected
                          </Typography>
                          <Chip 
                            size="small" 
                            label={`${Math.round((review.attributes_selected / review.total_attributes) * 100)}% scoped`}
                            color="info"
                          />
                          <Chip 
                            size="small" 
                            label={review.priority}
                            color={review.priority === 'High' ? 'error' : review.priority === 'Medium' ? 'warning' : 'success'}
                          />
                        </Box>
                      </Box>
                      
                      {/* Right side - Action button */}
                      <Box sx={{ ml: 2 }}>
                        <Button
                          variant="contained"
                          color="warning"
                          size="large"
                          startIcon={<ReviewIcon />}
                          onClick={() => {
                            window.location.href = `/cycles/${review.cycle_id}/reports/${review.report_id}/scoping-review`;
                          }}
                          sx={{ 
                            px: 3, 
                            py: 1.5,
                            fontSize: '1.1rem',
                            fontWeight: 'bold'
                          }}
                        >
                          Review Now
                        </Button>
                      </Box>
                    </Box>
                  </CardContent>
                                  </Card>
                ))}
                
                {/* Sample Selection Reviews */}
                {pendingSampleReviews.map((review) => (
                  <Card key={`sample-${review.cycle_id}-${review.report_id}-${review.set_id}`} sx={{ border: 1, borderColor: 'blue.300', bgcolor: 'blue.50' }}>
                    <CardContent sx={{ py: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        {/* Left side - Report info */}
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="subtitle2" color="blue.main" sx={{ mb: 1 }}>
                            SAMPLE SELECTION REVIEW
                          </Typography>
                          <Typography variant="h6" fontWeight="bold" gutterBottom>
                            {review.report_name} - {review.set_name}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 2 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Business fontSize="small" color="action" />
                              <Typography variant="body2">{review.lob}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <PersonIcon fontSize="small" color="action" />
                              <Typography variant="body2">Submitted by {review.submitted_by}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <TimelineIcon fontSize="small" color="action" />
                              <Typography variant="body2">
                                {new Date(review.submitted_date).toLocaleDateString()}
                              </Typography>
                            </Box>
                          </Box>
                          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                            <Chip 
                              label={`${review.sample_count} samples`}
                              size="small" 
                              variant="outlined" 
                              color="primary"
                            />
                            <Chip 
                              label={review.submission_type}
                              size="small" 
                              variant="outlined" 
                              color="info"
                            />
                          </Box>
                        </Box>
                        
                        {/* Right side - Actions */}
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 120 }}>
                          <Button
                            size="small"
                            variant="contained"
                            color="primary"
                            sx={{ minWidth: 100 }}
                            onClick={() => {
                              // Navigate to sample selection review page
                              window.location.href = `/cycles/${review.cycle_id}/reports/${review.report_id}/sample-selection`;
                            }}
                          >
                            Review Now
                          </Button>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
                
                {/* Pending Assignments */}
                {pendingAssignments.map((assignment) => (
                  <Card key={`assignment-${assignment.assignment_id}`} sx={{ border: 1, borderColor: 'orange.300', bgcolor: 'orange.50' }}>
                    <CardContent sx={{ py: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        {/* Left side - Assignment info */}
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600, mb: 1 }}>
                            📋 {assignment.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            Report: {assignment.context_data?.report_name || `Report ${assignment.context_data?.report_id}`} • Cycle: {assignment.context_data?.cycle_name || `Cycle ${assignment.context_data?.cycle_id}`}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            <Chip 
                              label={assignment.assignment_type}
                              size="small" 
                              variant="outlined" 
                              color="warning"
                            />
                            <Chip 
                              label={`Priority: ${assignment.priority}`}
                              size="small" 
                              variant="outlined" 
                              color={assignment.priority === 'High' ? 'error' : 'default'}
                            />
                            <Chip 
                              label={assignment.is_overdue ? 'Overdue' : `Due in ${assignment.days_until_due} days`}
                              size="small" 
                              variant="outlined" 
                              color={assignment.is_overdue ? 'error' : 'success'}
                            />
                          </Box>
                        </Box>
                        
                        {/* Right side - Actions */}
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 120 }}>
                          <Button
                            size="small"
                            variant="contained"
                            color="warning"
                            sx={{ minWidth: 100 }}
                            onClick={() => {
                              // Navigate to assignment page
                              window.location.href = assignment.action_url;
                            }}
                          >
                            Complete Task
                          </Button>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
        </CardContent>
      </Card>

      {/* Overview Metrics using MetricsGrid */}
      <MetricsGrid
        title="Overview Metrics"
        cards={[
          {
            id: 'pending-approvals',
            title: 'Pending Approvals',
            metrics: [{
              value: (metrics?.overview?.pending_approvals || 0) + pendingSampleReviews.length,
              label: 'Total Pending',
              status: ((metrics?.overview?.pending_approvals || 0) + pendingSampleReviews.length) > 10 ? 'warning' : 'info',
              description: 'Total approvals awaiting your review across all phases'
            }],
            icon: <Schedule />,
            color: 'primary',
            size: 3
          },
          {
            id: 'reports-on-track',
            title: 'Reports On Track',
            metrics: [{
              value: metrics?.overview?.reports_on_track || 0,
              label: 'On Schedule',
              status: 'success',
              description: `Out of ${metrics?.overview?.total_reports || 0} total reports`
            }],
            icon: <CheckCircle />,
            color: 'success',
            size: 3
          },
          {
            id: 'reports-at-risk',
            title: 'Reports At Risk',
            metrics: [{
              value: metrics?.overview?.reports_at_risk || 0,
              label: 'Need Attention',
              status: 'warning',
              description: 'Reports requiring close monitoring to avoid delays'
            }],
            icon: <Warning />,
            color: 'warning',
            size: 3
          },
          {
            id: 'escalations',
            title: 'Active Escalations',
            metrics: [{
              value: metrics?.escalations?.pending_escalations || 0,
              label: 'Urgent Items',
              status: metrics?.escalations?.pending_escalations > 0 ? 'error' : 'success',
              description: 'Escalations requiring immediate attention'
            }],
            icon: <Assessment />,
            color: 'error',
            size: 3
          }
        ]}
        columnsXs={12}
        columnsSm={6}
        columnsMd={3}
        columnsLg={3}
      />

      {/* Approval Performance Metrics */}
      <MetricsGrid
        title="Approval Performance"
        subtitle="Key metrics for approval efficiency and quality"
        cards={[
          {
            id: 'avg-approval-time',
            title: 'Avg Approval Time',
            metrics: [{
              value: metrics?.approval_metrics?.average_approval_time_hours || 0,
              label: 'Hours',
              unit: 'hours',
              target: 24,
              status: (metrics?.approval_metrics?.average_approval_time_hours || 0) <= 24 ? 'success' : 'warning',
              description: 'Average time to review and approve submissions'
            }],
            icon: <TimerIcon />,
            size: 3
          },
          {
            id: 'approval-sla',
            title: 'SLA Compliance',
            metrics: [{
              value: metrics?.approval_metrics?.approval_sla_compliance || 0,
              label: 'Compliance Rate',
              unit: '%',
              target: 95,
              status: (metrics?.approval_metrics?.approval_sla_compliance || 0) >= 90 ? 'success' : 'warning',
              description: 'Percentage of approvals completed within SLA'
            }],
            icon: <SpeedIcon />,
            size: 3
          },
          {
            id: 'rejection-rate',
            title: 'Rejection Rate',
            metrics: [{
              value: 8.5, // This would come from actual metrics
              label: 'Rejected',
              unit: '%',
              status: 'info',
              description: 'Percentage of submissions requiring revision'
            }],
            icon: <ThumbDownIcon />,
            size: 3
          },
          {
            id: 'revision-cycles',
            title: 'Avg Revision Cycles',
            metrics: [{
              value: 1.3, // This would come from actual metrics
              label: 'Cycles',
              status: 'success',
              description: 'Average number of revisions before approval'
            }],
            icon: <ReplayIcon />,
            size: 3
          }
        ]}
        columnsXs={12}
        columnsSm={6}
        columnsMd={3}
        columnsLg={3}
      />

      {/* Tabbed Content */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Approval Queue" icon={<Schedule />} />
          <Tab label="My Assignments" icon={<ReviewIcon />} />
          <Tab label="Progress Analytics" icon={<Analytics />} />
          <Tab label="Quality Trends" icon={<TrendingUp />} />
          <Tab label="Cross-LOB Analysis" icon={<Business />} />
          <Tab label="Historical Trends" icon={<BarChartIcon />} />
        </Tabs>
      </Box>

      {/* Approval Queue Tab */}
      <CustomTabPanel value={tabValue} index={0}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Pending Approvals
          </Typography>
          
          {/* Scoping Approvals Section */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" color="warning.main">
                  Scoping Phase Approvals
                </Typography>
                <Chip 
                  label={`${metrics?.approval_metrics?.scoping_pending || 0} Pending`}
                  color="warning"
                  variant="filled"
                />
              </Box>
              
              <Alert severity="info" sx={{ mb: 2 }}>
                Review tester scoping decisions and approve attributes for testing.
              </Alert>
              
              {/* Real pending scoping reviews */}
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Report Name</TableCell>
                      <TableCell>LOB</TableCell>
                      <TableCell>Submitted By</TableCell>
                      <TableCell>Submitted Date</TableCell>
                      <TableCell>Attributes Selected</TableCell>
                      <TableCell>Priority</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {pendingReviewsLoading ? (
                      <TableRow>
                        <TableCell colSpan={7} align="center">
                          <CircularProgress size={24} />
                        </TableCell>
                      </TableRow>
                    ) : pendingReviews.length > 0 ? (
                      pendingReviews.map((review) => (
                        <TableRow key={`${review.cycle_id}-${review.report_id}`}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {review.report_name}
                            </Typography>
                          </TableCell>
                          <TableCell>{review.lob}</TableCell>
                          <TableCell>{review.submitted_by}</TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {new Date(review.submitted_date).toLocaleDateString()}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body2" fontWeight="medium">
                                {review.attributes_selected} / {review.total_attributes}
                              </Typography>
                              <Chip 
                                label={`${Math.round((review.attributes_selected / review.total_attributes) * 100)}%`} 
                                size="small" 
                                color="info" 
                              />
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={review.priority} 
                              color={review.priority === 'High' ? 'error' : 'warning'} 
                              size="small" 
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              size="small"
                              variant="contained"
                              color="primary"
                              onClick={() => {
                                // Navigate to scoping review page
                                window.location.href = `/cycles/${review.cycle_id}/reports/${review.report_id}/scoping-review`;
                              }}
                            >
                              Review
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={7}>
                          <Box sx={{ textAlign: 'center', py: 3 }}>
                            <Typography variant="body2" color="text.secondary">
                              No scoping approvals pending
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          {/* Sample Selection Phase Approvals */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" color="info.main">
                  Sample Selection Phase Approvals
                </Typography>
                <Chip 
                  label={`${pendingSampleReviews.length} Pending`}
                  color="info"
                  variant="filled"
                />
              </Box>
              
              <Alert severity="info" sx={{ mb: 2 }}>
                Review tester sample selections and approve samples for testing.
              </Alert>
              
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Report</TableCell>
                      <TableCell>Sample Set</TableCell>
                      <TableCell>LOB</TableCell>
                      <TableCell>Submitted By</TableCell>
                      <TableCell>Submission Type</TableCell>
                      <TableCell>Sample Count</TableCell>
                      <TableCell>Submitted Date</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {pendingSampleReviews.map((review) => (
                      <TableRow key={`sample-${review.cycle_id}-${review.report_id}-${review.set_id}`}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {review.report_name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {review.set_name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={review.lob} size="small" color="primary" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {review.submitted_by}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={review.submission_type} 
                            size="small" 
                            color="info" 
                            variant="outlined" 
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {review.sample_count}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {new Date(review.submitted_date).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Button
                            size="small"
                            variant="contained"
                            color="primary"
                            onClick={() => {
                              // Navigate to sample review page
                              window.location.href = `/cycles/${review.cycle_id}/reports/${review.report_id}/sample-review/${review.set_id}`;
                            }}
                          >
                            Review
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                    
                    {/* Show empty state if no pending sample reviews */}
                    {pendingSampleReviews.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={8}>
                          <Box sx={{ textAlign: 'center', py: 3 }}>
                            <Typography variant="body2" color="text.secondary">
                              No sample selection approvals pending
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom color="success.main">
                Observation Reviews
              </Typography>
              <Alert severity="info">
                No observation reviews pending.
              </Alert>
            </CardContent>
          </Card>
        </Box>
      </CustomTabPanel>

      {/* My Assignments Tab */}
      <CustomTabPanel value={tabValue} index={1}>
        <Box>
          <Typography variant="h6" gutterBottom>
            My Assignments
          </Typography>
          
          {/* Assignment Sub-tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={assignmentTabValue} onChange={(e, newValue) => setAssignmentTabValue(newValue)}>
              <Tab 
                label={
                  <Badge badgeContent={pendingAssignments.length} color="warning">
                    Pending
                  </Badge>
                } 
              />
              <Tab 
                label={
                  <Badge badgeContent={completedAssignments.length} color="success">
                    Completed
                  </Badge>
                } 
              />
            </Tabs>
          </Box>

          {/* Pending Assignments */}
          {assignmentTabValue === 0 && (
            <Box>
              {pendingAssignmentsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : pendingAssignments.length > 0 ? (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Assignment</TableCell>
                        <TableCell>Report</TableCell>
                        <TableCell>Priority</TableCell>
                        <TableCell>Due Date</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {pendingAssignments.map((assignment) => (
                        <TableRow key={assignment.assignment_id}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {assignment.title}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {assignment.assignment_type}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {assignment.context_data?.report_name || `Report ${assignment.context_data?.report_id}`}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {assignment.context_data?.cycle_name || `Cycle ${assignment.context_data?.cycle_id}`}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={assignment.priority}
                              size="small"
                              color={assignment.priority === 'High' ? 'error' : assignment.priority === 'Medium' ? 'warning' : 'default'}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : 'No due date'}
                            </Typography>
                            <Typography variant="caption" color={assignment.is_overdue ? 'error.main' : 'text.secondary'}>
                              {assignment.is_overdue ? 'Overdue' : `${assignment.days_until_due} days left`}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={assignment.status}
                              size="small"
                              color="info"
                            />
                          </TableCell>
                          <TableCell align="center">
                            <Button
                              size="small"
                              variant="contained"
                              color="primary"
                              onClick={() => {
                                window.location.href = assignment.action_url;
                              }}
                            >
                              Complete Task
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">
                  <Typography variant="h6">✅ No Pending Assignments</Typography>
                  <Typography>You have no pending assignments at this time.</Typography>
                </Alert>
              )}
            </Box>
          )}

          {/* Completed Assignments */}
          {assignmentTabValue === 1 && (
            <Box>
              {completedAssignmentsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : completedAssignments.length > 0 ? (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Assignment</TableCell>
                        <TableCell>Report</TableCell>
                        <TableCell>Priority</TableCell>
                        <TableCell>Completed Date</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {completedAssignments.map((assignment) => (
                        <TableRow key={assignment.assignment_id}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {assignment.title}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {assignment.assignment_type}
                            </Typography>
                            {assignment.completion_notes && (
                              <Typography variant="caption" display="block" sx={{ mt: 0.5, fontStyle: 'italic' }}>
                                Notes: {assignment.completion_notes}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {assignment.context_data?.report_name || `Report ${assignment.context_data?.report_id}`}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {assignment.context_data?.cycle_name || `Cycle ${assignment.context_data?.cycle_id}`}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={assignment.priority}
                              size="small"
                              color={assignment.priority === 'High' ? 'error' : assignment.priority === 'Medium' ? 'warning' : 'default'}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {assignment.completed_at ? new Date(assignment.completed_at).toLocaleDateString() : 'N/A'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {assignment.completed_at ? new Date(assignment.completed_at).toLocaleTimeString() : ''}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={assignment.status}
                              size="small"
                              color="success"
                            />
                          </TableCell>
                          <TableCell align="center">
                            <Button
                              size="small"
                              variant="outlined"
                              color="primary"
                              onClick={() => {
                                window.location.href = assignment.action_url;
                              }}
                            >
                              View Details
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">
                  <Typography variant="h6">📋 No Completed Assignments</Typography>
                  <Typography>You haven't completed any assignments yet.</Typography>
                </Alert>
              )}
            </Box>
          )}
        </Box>
      </CustomTabPanel>

      {/* Progress Analytics Tab */}
      <CustomTabPanel value={tabValue} index={2}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
          {/* Phase Distribution */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Reports by Phase
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
                {Object.entries(metrics?.testing_progress?.reports_by_phase || {}).map(([phase, count]) => (
                  <Box key={phase} textAlign="center" p={2}>
                    <Typography variant="h6" color="primary">
                      {count || 0}
                    </Typography>
                    <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                      {phase}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Completion Rate Trends */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Completion Rate Trends
              </Typography>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Box>
                  <Typography variant="h4" color="primary">
                    {formatPercentage(metrics?.testing_progress?.completion_rates?.current_cycle || 0)}
                  </Typography>
                  <Typography variant="subtitle2">Current Cycle</Typography>
                </Box>
                {getTrendIcon(metrics?.testing_progress?.completion_rates?.trend || 'flat')}
              </Box>
              <Typography variant="body2" color="text.secondary">
                Previous cycle: {formatPercentage(metrics?.testing_progress?.completion_rates?.previous_cycle || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </CustomTabPanel>

      {/* Quality Trends Tab */}
      <CustomTabPanel value={tabValue} index={3}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
          {/* Observations Trend */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Observations Trend (Monthly)
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Month</TableCell>
                      <TableCell align="center">Total</TableCell>
                      <TableCell align="center">Critical</TableCell>
                      <TableCell align="center">Resolved</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(metrics?.quality_trends?.observations_by_month || []).slice(-6).map((month) => (
                      <TableRow key={month.month}>
                        <TableCell>{month.month}</TableCell>
                        <TableCell align="center">{month.total_observations}</TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={month.critical_observations} 
                            size="small" 
                            color={month.critical_observations > 0 ? 'error' : 'success'}
                          />
                        </TableCell>
                        <TableCell align="center">{month.resolved_observations}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          {/* Quality Score Trend */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quality Score Trend
              </Typography>
              {(metrics?.quality_trends?.quality_score_trend || []).slice(-5).map((cycle, index) => (
                <Box key={cycle.cycle} display="flex" justifyContent="space-between" alignItems="center" py={1}>
                  <Typography variant="body2">{cycle.cycle}</Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body2" color={
                      cycle.quality_score >= 90 ? 'success.main' :
                      cycle.quality_score >= 75 ? 'warning.main' : 'error.main'
                    }>
                      {cycle.quality_score}
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={cycle.quality_score} 
                      sx={{ width: 60, height: 6 }}
                      color={
                        cycle.quality_score >= 90 ? 'success' :
                        cycle.quality_score >= 75 ? 'warning' : 'error'
                      }
                    />
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Box>
      </CustomTabPanel>

      {/* Cross-LOB Analysis Tab */}
      <CustomTabPanel value={tabValue} index={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Performance by Line of Business
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>LOB</TableCell>
                    <TableCell align="center">Total Reports</TableCell>
                    <TableCell align="center">Completed</TableCell>
                    <TableCell align="center">Completion Rate</TableCell>
                    <TableCell align="center">Avg Cycle Time (Days)</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(metrics?.cross_lob_analysis?.reports_by_lob || []).map((lob) => (
                    <TableRow key={lob.lob_name}>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Business fontSize="small" color="action" />
                          {lob.lob_name}
                        </Box>
                      </TableCell>
                      <TableCell align="center">{lob.total_reports}</TableCell>
                      <TableCell align="center">{lob.completed_reports}</TableCell>
                      <TableCell align="center">
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2" color={
                            lob.completion_rate >= 80 ? 'success.main' :
                            lob.completion_rate >= 60 ? 'warning.main' : 'error.main'
                          }>
                            {formatPercentage(lob.completion_rate)}
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={lob.completion_rate} 
                            sx={{ width: 60, height: 6 }}
                            color={
                              lob.completion_rate >= 80 ? 'success' :
                              lob.completion_rate >= 60 ? 'warning' : 'error'
                            }
                          />
                        </Box>
                      </TableCell>
                      <TableCell align="center">{Math.round(lob.average_cycle_time_days)}</TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Details">
                          <IconButton 
                            size="small" 
                            onClick={() => {
                              setSelectedLOB(lob);
                              setDetailsOpen(true);
                            }}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </CustomTabPanel>

      {/* Historical Trends Tab */}
      <CustomTabPanel value={tabValue} index={5}>
        <Stack spacing={4}>
          {/* Approval Turnaround Time Trend */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Approval Turnaround Time Trend
            </Typography>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Average time to approve submissions over the last 6 months
                </Typography>
                <Box sx={{ mt: 2 }}>
                  {/* Mock data for demonstration */}
                  {['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((month, index) => {
                    const hours = 24 - (index * 2) + Math.random() * 4;
                    return (
                      <Box key={month} sx={{ mb: 2 }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Typography variant="body2">{month} 2024</Typography>
                          <Typography 
                            variant="body2" 
                            color={hours <= 24 ? 'success.main' : 'error.main'}
                            fontWeight="medium"
                          >
                            {hours.toFixed(1)} hours
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={Math.min((24 / hours) * 100, 100)}
                          sx={{ height: 8, borderRadius: 4 }}
                          color={hours <= 24 ? 'success' : 'error'}
                        />
                      </Box>
                    );
                  })}
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Quality Metrics Over Time */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Quality Metrics Trend
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    Rejection Rate Trend
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Month</TableCell>
                          <TableCell align="center">Rate</TableCell>
                          <TableCell align="center">Trend</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {[{month: 'Oct', rate: 12.5}, {month: 'Nov', rate: 10.2}, {month: 'Dec', rate: 8.5}].map((data, index, arr) => {
                          const prevRate = index > 0 ? arr[index - 1].rate : data.rate;
                          const trend = data.rate - prevRate;
                          return (
                            <TableRow key={data.month}>
                              <TableCell>{data.month} 2024</TableCell>
                              <TableCell align="center">
                                <Chip 
                                  label={`${data.rate}%`}
                                  size="small"
                                  color={data.rate <= 10 ? 'success' : 'warning'}
                                />
                              </TableCell>
                              <TableCell align="center">
                                {trend !== 0 && (
                                  <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                                    {trend < 0 ? 
                                      <TrendingDown color="success" fontSize="small" /> : 
                                      <TrendingUp color="error" fontSize="small" />
                                    }
                                    <Typography 
                                      variant="caption" 
                                      color={trend < 0 ? 'success.main' : 'error.main'}
                                    >
                                      {Math.abs(trend).toFixed(1)}%
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

              <Card>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    Revision Cycles Trend
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Phase</TableCell>
                          <TableCell align="center">Avg Cycles</TableCell>
                          <TableCell align="center">Status</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>Scoping</TableCell>
                          <TableCell align="center">1.2</TableCell>
                          <TableCell align="center">
                            <Chip label="Excellent" size="small" color="success" />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Sample Selection</TableCell>
                          <TableCell align="center">1.5</TableCell>
                          <TableCell align="center">
                            <Chip label="Good" size="small" color="success" />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Observations</TableCell>
                          <TableCell align="center">2.1</TableCell>
                          <TableCell align="center">
                            <Chip label="Monitor" size="small" color="warning" />
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Box>
          </Box>

          {/* SLA Compliance History */}
          <Box>
            <Typography variant="h6" gutterBottom>
              SLA Compliance History
            </Typography>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Monthly SLA compliance rates for approval processes
                </Typography>
                <Box sx={{ mt: 3 }}>
                  <MetricBox
                    title="Current Month SLA"
                    value={metrics?.approval_metrics?.approval_sla_compliance || 92.3}
                    unit="%"
                    target={95}
                    trend={2.5}
                    status={(metrics?.approval_metrics?.approval_sla_compliance || 92.3) >= 95 ? 'success' : 'warning'}
                    description="December 2024 performance"
                    size="large"
                  />
                </Box>
                <Divider sx={{ my: 3 }} />
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 2 }}>
                  {['Jul', 'Aug', 'Sep', 'Oct', 'Nov'].map((month, index) => {
                    const compliance = 88 + (index * 2) + Math.random() * 3;
                    return (
                      <Box key={month} textAlign="center">
                        <Typography variant="caption" color="text.secondary">
                          {month} 2024
                        </Typography>
                        <Typography 
                          variant="h6" 
                          color={compliance >= 95 ? 'success.main' : compliance >= 90 ? 'warning.main' : 'error.main'}
                        >
                          {compliance.toFixed(1)}%
                        </Typography>
                      </Box>
                    );
                  })}
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Stack>
      </CustomTabPanel>

      {/* LOB Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>LOB Performance Details</DialogTitle>
        <DialogContent>
          {selectedLOB && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedLOB.lob_name}
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">Total Reports</Typography>
                  <Typography variant="h6">{selectedLOB.total_reports}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Completed Reports</Typography>
                  <Typography variant="h6">{selectedLOB.completed_reports}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Completion Rate</Typography>
                  <Typography variant="h6">{formatPercentage(selectedLOB.completion_rate)}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Average Cycle Time</Typography>
                  <Typography variant="h6">{Math.round(selectedLOB.average_cycle_time_days)} days</Typography>
                </Box>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
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

export default ReportOwnerDashboard; 