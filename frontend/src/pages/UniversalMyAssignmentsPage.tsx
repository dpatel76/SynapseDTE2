/**
 * Universal My Assignments Page
 * Displays all assignments (received and created) for any role with context-aware navigation
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Button,
  Alert,
  Stack,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Badge,
  LinearProgress,
  Grid,
  Divider,
  Avatar,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Visibility as ViewIcon,
  PlayArrow as ActionIcon,
  CheckCircle as CompletedIcon,
  Schedule as PendingIcon,
  Assignment as AssignmentIcon,
  OpenInNew as OpenIcon,
  Timer as TimerIcon,
  TrendingUp as TrendingUpIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  CalendarToday as CalendarIcon,
  ArrowForward as ArrowForwardIcon,
  Dashboard as DashboardIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import { useNotifications } from '../contexts/NotificationContext';

interface UniversalAssignment {
  assignment_id: string;
  assignment_type: string;
  from_role: string;
  to_role: string;
  from_user_id: number;
  to_user_id: number | null;
  title: string;
  description: string;
  task_instructions: string | null;
  context_type: string;
  context_data: {
    cycle_id?: number;
    report_id?: number;
    phase_name?: string;
    workflow_phase?: string;
    test_cycle_linkage?: string;
    report_linkage?: string;
    attribute_id?: number;
    lob_id?: number;
  };
  status: string;
  priority: string;
  assigned_at: string;
  due_date: string | null;
  acknowledged_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  completion_notes: string | null;
  is_overdue: boolean;
  days_until_due: number;
  is_active: boolean;
  is_completed: boolean;
  from_user_name: string | null;
  to_user_name: string | null;
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
      id={`assignments-tabpanel-${index}`}
      aria-labelledby={`assignments-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const UniversalMyAssignmentsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const { showToast } = useNotifications();

  const [tabValue, setTabValue] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');

  // Fetch all assignments for current user
  const { data: allAssignments = [], isLoading, refetch } = useQuery({
    queryKey: ['universal-assignments', user?.user_id],
    queryFn: async () => {
      const response = await apiClient.get('/universal-assignments/assignments', {
        params: {
          status_filter: 'Assigned,Acknowledged,In Progress,Completed,Approved,Rejected',
          limit: 100
        }
      });
      return response.data as UniversalAssignment[];
    },
    enabled: !!user?.user_id,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Separate assignments by direction (received vs created)
  const receivedAssignments = allAssignments.filter(
    (assignment) => assignment.to_user_id === user?.user_id
  );
  
  const createdAssignments = allAssignments.filter(
    (assignment) => assignment.from_user_id === user?.user_id
  );

  // Apply filters
  const applyFilters = (assignments: UniversalAssignment[]) => {
    return assignments.filter((assignment) => {
      const matchesSearch = 
        assignment.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        assignment.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        assignment.assignment_type.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === 'all' || assignment.status === statusFilter;
      const matchesType = typeFilter === 'all' || assignment.assignment_type === typeFilter;
      const matchesPriority = priorityFilter === 'all' || assignment.priority === priorityFilter;

      return matchesSearch && matchesStatus && matchesType && matchesPriority;
    });
  };

  const filteredReceivedAssignments = applyFilters(receivedAssignments);
  const filteredCreatedAssignments = applyFilters(createdAssignments);

  // Get unique values for filter options
  const allTypes = Array.from(new Set(allAssignments.map(a => a.assignment_type)));
  const allStatuses = Array.from(new Set(allAssignments.map(a => a.status)));
  const allPriorities = Array.from(new Set(allAssignments.map(a => a.priority)));

  // Generate context-aware action URL
  const getActionUrl = (assignment: UniversalAssignment): string => {
    const { context_data } = assignment;
    
    if (!context_data.cycle_id || !context_data.report_id) {
      return '/dashboard'; // Fallback if no context
    }

    const baseUrl = `/cycles/${context_data.cycle_id}/reports/${context_data.report_id}`;
    
    // Route based on assignment type and workflow phase
    switch (assignment.assignment_type) {
      case 'Data Upload Request':
        return `${baseUrl}/data-profiling`;
      
      case 'LOB Assignment':
        return `${baseUrl}/data-owner`;
      
      case 'Scoping Approval':
      case 'Scoping Review':
        // Report Owners should go to scoping-review page
        if (user?.role === 'Report Owner') {
          return `${baseUrl}/scoping-review`;
        }
        return `${baseUrl}/scoping`;
      
      case 'Sample Selection Approval':
        return `${baseUrl}/sample-selection`;
      
      case 'Rule Approval':
        // Check if this is a scoping-related rule approval
        if ((context_data.phase_name === 'Scoping' || context_data.workflow_phase === 'Scoping') && user?.role === 'Report Owner') {
          return `${baseUrl}/scoping-review`;
        }
        return `${baseUrl}/data-profiling`;
      
      case 'Observation Approval':
        return `${baseUrl}/observations`;
      
      case 'Report Approval':
        return `${baseUrl}/test-report`;
      
      case 'Phase Review':
      case 'Phase Approval':
        // Route based on phase name
        switch (context_data.phase_name || context_data.workflow_phase) {
          case 'Planning': return `${baseUrl}/planning`;
          case 'Data Profiling': return `${baseUrl}/data-profiling`;
          case 'Scoping': 
            // Report Owners should go to scoping-review page
            if (user?.role === 'Report Owner') {
              return `${baseUrl}/scoping-review`;
            }
            return `${baseUrl}/scoping`;
          case 'Sample Selection': return `${baseUrl}/sample-selection`;
          case 'Data Provider ID': return `${baseUrl}/data-owner`;
          case 'Request Info': return `${baseUrl}/request-info`;
          case 'Testing': return `${baseUrl}/test-execution`;
          case 'Observations': return `${baseUrl}/observations`;
          default: return baseUrl;
        }
      
      default:
        return baseUrl;
    }
  };

  // Handle assignment action
  const handleAssignmentAction = (assignment: UniversalAssignment) => {
    const actionUrl = getActionUrl(assignment);
    navigate(actionUrl);
  };

  // Status color mapping
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Assigned': return 'primary';
      case 'Acknowledged': return 'info';
      case 'In Progress': return 'warning';
      case 'Completed': return 'success';
      case 'Approved': return 'success';
      case 'Rejected': return 'error';
      case 'Cancelled': return 'default';
      case 'Overdue': return 'error';
      case 'Escalated': return 'error';
      default: return 'default';
    }
  };

  // Priority color mapping
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'Urgent': case 'Critical': return 'error';
      case 'High': return 'warning';
      case 'Medium': return 'info';
      case 'Low': return 'success';
      default: return 'default';
    }
  };

  // Format duration
  const formatDuration = (startDate: string, endDate?: string | null) => {
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    if (diffDays > 0) {
      return `${diffDays}d ${diffHours}h`;
    } else if (diffHours > 0) {
      return `${diffHours}h`;
    } else {
      return '<1h';
    }
  };

  // Assignment metrics
  const receivedMetrics = {
    total: receivedAssignments.length,
    pending: receivedAssignments.filter(a => ['Assigned', 'Acknowledged', 'In Progress'].includes(a.status)).length,
    completed: receivedAssignments.filter(a => ['Completed', 'Approved'].includes(a.status)).length,
    overdue: receivedAssignments.filter(a => a.is_overdue).length,
  };

  const createdMetrics = {
    total: createdAssignments.length,
    pending: createdAssignments.filter(a => ['Assigned', 'Acknowledged', 'In Progress'].includes(a.status)).length,
    completed: createdAssignments.filter(a => ['Completed', 'Approved'].includes(a.status)).length,
    overdue: createdAssignments.filter(a => a.is_overdue).length,
  };

  // Render assignment table
  const renderAssignmentTable = (assignments: UniversalAssignment[], isReceived: boolean) => (
    <TableContainer component={Paper} elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
      <Table>
        <TableHead>
          <TableRow sx={{ bgcolor: 'grey.50' }}>
            <TableCell><strong>Assignment</strong></TableCell>
            <TableCell><strong>Type</strong></TableCell>
            <TableCell><strong>Context</strong></TableCell>
            <TableCell><strong>{isReceived ? 'From' : 'To'}</strong></TableCell>
            <TableCell><strong>Status</strong></TableCell>
            <TableCell><strong>Priority</strong></TableCell>
            <TableCell><strong>Due Date</strong></TableCell>
            <TableCell><strong>Duration</strong></TableCell>
            <TableCell><strong>Actions</strong></TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {assignments.map((assignment) => (
            <TableRow key={assignment.assignment_id} hover>
              <TableCell>
                <Box>
                  <Typography variant="body2" fontWeight="medium" gutterBottom>
                    {assignment.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    {assignment.description.length > 100 
                      ? `${assignment.description.substring(0, 100)}...` 
                      : assignment.description
                    }
                  </Typography>
                </Box>
              </TableCell>
              
              <TableCell>
                <Chip 
                  label={assignment.assignment_type} 
                  size="small" 
                  variant="outlined"
                  color="primary"
                />
              </TableCell>
              
              <TableCell>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    {assignment.context_data.test_cycle_linkage || `Cycle ${assignment.context_data.cycle_id}`}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    {assignment.context_data.report_linkage || `Report ${assignment.context_data.report_id}`}
                  </Typography>
                  {assignment.context_data.workflow_phase && (
                    <Typography variant="caption" color="primary" sx={{ display: 'block' }}>
                      {assignment.context_data.workflow_phase}
                    </Typography>
                  )}
                </Box>
              </TableCell>
              
              <TableCell>
                <Typography variant="body2">
                  {isReceived ? assignment.from_user_name : assignment.to_user_name || 'Auto-assigned'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {isReceived ? assignment.from_role : assignment.to_role}
                </Typography>
              </TableCell>
              
              <TableCell>
                <Chip 
                  label={assignment.status} 
                  size="small" 
                  color={getStatusColor(assignment.status) as any}
                  variant={assignment.is_overdue ? "filled" : "outlined"}
                />
              </TableCell>
              
              <TableCell>
                <Chip 
                  label={assignment.priority} 
                  size="small" 
                  color={getPriorityColor(assignment.priority) as any}
                />
              </TableCell>
              
              <TableCell>
                {assignment.due_date ? (
                  <Box>
                    <Typography variant="body2" color={assignment.is_overdue ? 'error' : 'text.primary'}>
                      {new Date(assignment.due_date).toLocaleDateString()}
                    </Typography>
                    {assignment.is_overdue && (
                      <Typography variant="caption" color="error">
                        Overdue
                      </Typography>
                    )}
                    {!assignment.is_overdue && assignment.days_until_due <= 3 && (
                      <Typography variant="caption" color="warning.main">
                        Due soon
                      </Typography>
                    )}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No due date
                  </Typography>
                )}
              </TableCell>
              
              <TableCell>
                <Typography variant="body2">
                  {assignment.completed_at 
                    ? formatDuration(assignment.assigned_at, assignment.completed_at)
                    : formatDuration(assignment.assigned_at)
                  }
                </Typography>
              </TableCell>
              
              <TableCell>
                <Stack direction="row" spacing={1}>
                  <Tooltip title="Go to assignment context">
                    <IconButton 
                      size="small" 
                      onClick={() => handleAssignmentAction(assignment)}
                      color="primary"
                    >
                      <ActionIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="View details">
                    <IconButton size="small">
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>
                </Stack>
              </TableCell>
            </TableRow>
          ))}
          {assignments.length === 0 && (
            <TableRow>
              <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                <Typography color="text.secondary">
                  No assignments found
                </Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );

  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 0, mb: 4, pt: 3 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Stack spacing={2} alignItems="center">
            <LinearProgress sx={{ width: 200 }} />
            <Typography variant="body2" color="text.secondary">
              Loading assignments...
            </Typography>
          </Stack>
        </Box>
      </Container>
    );
  }

  return (
    <Box sx={{ px: 3, py: 3 }}>
      <Stack spacing={3}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <AssignmentIcon />
            </Avatar>
            <Box>
              <Typography variant="h4" gutterBottom>
                {user?.role === 'Tester' ? 'My Tasks' : 'My Assignments'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {user?.role === 'Tester' 
                  ? 'All tasks and assignments received and created by you across all workflows'
                  : 'All assignments received and created by you across all workflows'
                }
              </Typography>
            </Box>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
        </Box>

        {/* Metrics Overview */}
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="primary.main">
                  {receivedMetrics.total}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Received
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="warning.main">
                  {receivedMetrics.pending}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Pending Action
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="success.main">
                  {receivedMetrics.completed}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Completed
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="error.main">
                  {receivedMetrics.overdue}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Overdue
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Filters */}
        <Card>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid size={{ xs: 12, md: 3 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Search assignments..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 2 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={statusFilter}
                    label="Status"
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <MenuItem value="all">All Statuses</MenuItem>
                    {allStatuses.map((status) => (
                      <MenuItem key={status} value={status}>{status}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 2 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Type</InputLabel>
                  <Select
                    value={typeFilter}
                    label="Type"
                    onChange={(e) => setTypeFilter(e.target.value)}
                  >
                    <MenuItem value="all">All Types</MenuItem>
                    {allTypes.map((type) => (
                      <MenuItem key={type} value={type}>{type}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 2 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={priorityFilter}
                    label="Priority"
                    onChange={(e) => setPriorityFilter(e.target.value)}
                  >
                    <MenuItem value="all">All Priorities</MenuItem>
                    {allPriorities.map((priority) => (
                      <MenuItem key={priority} value={priority}>{priority}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Assignment Tabs */}
        <Card>
          <Tabs 
            value={tabValue} 
            onChange={(e, v) => setTabValue(v)}
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab 
              label={
                <Badge badgeContent={receivedMetrics.pending} color="warning">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <PersonIcon />
                    Received ({receivedMetrics.total})
                  </span>
                </Badge>
              } 
            />
            <Tab 
              label={
                <Badge badgeContent={createdMetrics.pending} color="info">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <BusinessIcon />
                    Created ({createdMetrics.total})
                  </span>
                </Badge>
              } 
            />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            {renderAssignmentTable(filteredReceivedAssignments, true)}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {renderAssignmentTable(filteredCreatedAssignments, false)}
          </TabPanel>
        </Card>
      </Stack>
    </Box>
  );
};

export default UniversalMyAssignmentsPage;