import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  CardActions,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Visibility as ViewIcon,
  Assignment as AssignmentIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  NavigateNext as NavigateIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';

interface Assignment {
  assignment_id: string;
  assignment_type: string;
  from_role: string;
  to_role: string;
  from_user_name?: string;
  to_user_name?: string;
  title: string;
  description: string;
  task_instructions?: string;
  context_type: string;
  context_data: Record<string, any>;
  status: string;
  priority: string;
  assigned_at: string;
  due_date?: string;
  acknowledged_at?: string;
  started_at?: string;
  completed_at?: string;
  completion_notes?: string;
  requires_approval: boolean;
  approval_role?: string;
  is_overdue: boolean;
  days_until_due: number;
  is_active: boolean;
  is_completed: boolean;
  action_url?: string;
}

const AssignmentsPage: React.FC = () => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'approve' | 'reject' | null>(null);
  const [actionNotes, setActionNotes] = useState('');
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    loadAssignments();
  }, []);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.get('/universal-assignments/assignments', {
        params: {
          limit: 100
        }
      });
      
      setAssignments(response.data || []);
    } catch (error) {
      console.error('Failed to load assignments:', error);
      setError('Failed to load assignments. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusChip = (status: string) => {
    const statusConfig = {
      'Assigned': { color: 'info' as const, label: 'Assigned' },
      'Acknowledged': { color: 'default' as const, label: 'Acknowledged' },
      'In Progress': { color: 'warning' as const, label: 'In Progress' },
      'Completed': { color: 'success' as const, label: 'Completed' },
      'Approved': { color: 'success' as const, label: 'Approved' },
      'Rejected': { color: 'error' as const, label: 'Rejected' },
      'Overdue': { color: 'error' as const, label: 'Overdue' },
      'Escalated': { color: 'secondary' as const, label: 'Escalated' }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || 
                   { color: 'default' as const, label: status };
    
    return <Chip size="small" color={config.color} label={config.label} />;
  };

  const getPriorityChip = (priority: string) => {
    const priorityConfig = {
      'Low': { color: 'default' as const, label: 'Low' },
      'Medium': { color: 'info' as const, label: 'Medium' },
      'High': { color: 'warning' as const, label: 'High' },
      'Critical': { color: 'error' as const, label: 'Critical' },
      'Urgent': { color: 'error' as const, label: 'Urgent' }
    };
    
    const config = priorityConfig[priority as keyof typeof priorityConfig] || 
                   { color: 'default' as const, label: priority };
    
    return <Chip size="small" color={config.color} label={config.label} />;
  };

  const handleViewAssignment = (assignment: Assignment) => {
    setSelectedAssignment(assignment);
    setViewDialogOpen(true);
  };

  const handleNavigateToAssignment = (assignment: Assignment) => {
    console.log('🧭 Navigating to assignment:', assignment);
    console.log('🔗 Action URL:', assignment.action_url);
    console.log('📊 Context data:', assignment.context_data);
    
    if (assignment.action_url) {
      console.log('✅ Using action_url:', assignment.action_url);
      navigate(assignment.action_url);
    } else {
      // Default navigation based on assignment type and context
      const { context_data } = assignment;
      if (context_data?.cycle_id && context_data?.report_id) {
        const defaultUrl = `/cycles/${context_data.cycle_id}/reports/${context_data.report_id}/data-profiling`;
        console.log('🎯 Using default URL:', defaultUrl);
        navigate(defaultUrl);
      } else {
        console.warn('⚠️ No navigation path available for assignment:', assignment);
      }
    }
  };

  const handleApproveAssignment = (assignment: Assignment) => {
    setSelectedAssignment(assignment);
    setActionType('approve');
    setActionNotes('');
    setActionDialogOpen(true);
  };

  const handleRejectAssignment = (assignment: Assignment) => {
    setSelectedAssignment(assignment);
    setActionType('reject');
    setActionNotes('');
    setActionDialogOpen(true);
  };

  const confirmAction = async () => {
    if (!selectedAssignment || !actionType) return;

    try {
      const endpoint = actionType === 'approve' ? 'approve' : 'reject';
      await apiClient.post(`/universal-assignments/assignments/${selectedAssignment.assignment_id}/${endpoint}`, {
        notes: actionNotes || (actionType === 'approve' ? 'Approved' : 'Rejected')
      });

      setActionDialogOpen(false);
      setSelectedAssignment(null);
      setActionType(null);
      setActionNotes('');
      await loadAssignments();
    } catch (error) {
      console.error(`Failed to ${actionType} assignment:`, error);
      setError(`Failed to ${actionType} assignment. Please try again.`);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading assignments...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <AssignmentIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h4" component="h1">
          My Assignments
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {assignments.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <AssignmentIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" color="textSecondary">
            No assignments found
          </Typography>
          <Typography variant="body2" color="textSecondary">
            You don't have any pending assignments at the moment.
          </Typography>
        </Paper>
      ) : (
        <>
          {/* Assignment Cards for better mobile experience */}
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' },
            gap: 3,
            mb: 3 
          }}>
            {assignments.map((assignment) => (
              <Card key={assignment.assignment_id} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="h3" sx={{ flexGrow: 1, pr: 1 }}>
                      {assignment.title}
                    </Typography>
                    {getPriorityChip(assignment.priority)}
                  </Box>
                  
                  <Typography variant="body2" color="textSecondary" paragraph>
                    {assignment.description}
                  </Typography>
                  
                  <Box sx={{ mb: 2 }}>
                    <Chip size="small" label={assignment.assignment_type} sx={{ mr: 1, mb: 1 }} />
                    {getStatusChip(assignment.status)}
                  </Box>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <PersonIcon sx={{ fontSize: 16, mr: 1, color: 'grey.600' }} />
                    <Typography variant="caption" color="textSecondary">
                      From: {assignment.from_user_name || assignment.from_role}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <ScheduleIcon sx={{ fontSize: 16, mr: 1, color: 'grey.600' }} />
                    <Typography variant="caption" color="textSecondary">
                      Assigned: {formatDate(assignment.assigned_at)}
                    </Typography>
                  </Box>
                  
                  {assignment.due_date && (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <ScheduleIcon sx={{ fontSize: 16, mr: 1, color: assignment.is_overdue ? 'error.main' : 'grey.600' }} />
                      <Typography 
                        variant="caption" 
                        color={assignment.is_overdue ? 'error.main' : 'textSecondary'}
                      >
                        Due: {formatDate(assignment.due_date)}
                        {assignment.is_overdue && ' (OVERDUE)'}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
                
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<ViewIcon />}
                    onClick={() => handleViewAssignment(assignment)}
                  >
                    View
                  </Button>
                  <Button
                    size="small"
                    startIcon={<NavigateIcon />}
                    onClick={() => handleNavigateToAssignment(assignment)}
                    variant="contained"
                  >
                    Go to Task
                  </Button>
                  {assignment.status === 'Completed' && assignment.requires_approval && (
                    <>
                      <Button
                        size="small"
                        color="success"
                        startIcon={<ApproveIcon />}
                        onClick={() => handleApproveAssignment(assignment)}
                      >
                        Approve
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        startIcon={<RejectIcon />}
                        onClick={() => handleRejectAssignment(assignment)}
                      >
                        Reject
                      </Button>
                    </>
                  )}
                </CardActions>
              </Card>
            ))}
          </Box>

          {/* Assignment Table for desktop */}
          <TableContainer component={Paper} sx={{ display: { xs: 'none', md: 'block' } }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Assignment</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>From</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Due Date</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {assignments.map((assignment) => (
                  <TableRow key={assignment.assignment_id} hover>
                    <TableCell>
                      <Typography variant="subtitle2">{assignment.title}</Typography>
                      <Typography variant="caption" color="textSecondary">
                        {assignment.description}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip size="small" label={assignment.assignment_type} />
                    </TableCell>
                    <TableCell>{assignment.from_user_name || assignment.from_role}</TableCell>
                    <TableCell>{getPriorityChip(assignment.priority)}</TableCell>
                    <TableCell>{getStatusChip(assignment.status)}</TableCell>
                    <TableCell>
                      <Typography 
                        variant="body2" 
                        color={assignment.is_overdue ? 'error.main' : 'textPrimary'}
                      >
                        {formatDate(assignment.due_date)}
                        {assignment.is_overdue && (
                          <Chip size="small" color="error" label="OVERDUE" sx={{ ml: 1 }} />
                        )}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => handleViewAssignment(assignment)}
                          >
                            <ViewIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Go to Task">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleNavigateToAssignment(assignment)}
                          >
                            <NavigateIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {assignment.status === 'Completed' && assignment.requires_approval && (
                          <>
                            <Tooltip title="Approve">
                              <IconButton
                                size="small"
                                color="success"
                                onClick={() => handleApproveAssignment(assignment)}
                              >
                                <ApproveIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Reject">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleRejectAssignment(assignment)}
                              >
                                <RejectIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}

      {/* View Assignment Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Assignment Details</DialogTitle>
        <DialogContent>
          {selectedAssignment && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedAssignment.title}
              </Typography>
              <Typography variant="body1" paragraph>
                {selectedAssignment.description}
              </Typography>
              
              {selectedAssignment.task_instructions && (
                <>
                  <Typography variant="subtitle2" gutterBottom>
                    Instructions:
                  </Typography>
                  <Typography variant="body2" paragraph>
                    {selectedAssignment.task_instructions}
                  </Typography>
                </>
              )}
              
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Chip label={selectedAssignment.assignment_type} />
                {getStatusChip(selectedAssignment.status)}
                {getPriorityChip(selectedAssignment.priority)}
              </Box>
              
              <Typography variant="caption" color="textSecondary">
                Assigned: {formatDate(selectedAssignment.assigned_at)}
                {selectedAssignment.due_date && ` • Due: ${formatDate(selectedAssignment.due_date)}`}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          {selectedAssignment && (
            <Button
              variant="contained"
              onClick={() => {
                setViewDialogOpen(false);
                handleNavigateToAssignment(selectedAssignment);
              }}
            >
              Go to Task
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Action Dialog */}
      <Dialog open={actionDialogOpen} onClose={() => setActionDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {actionType === 'approve' ? 'Approve Assignment' : 'Reject Assignment'}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to {actionType} the assignment "{selectedAssignment?.title}"?
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            label={actionType === 'approve' ? 'Approval Notes (Optional)' : 'Rejection Reason'}
            multiline
            rows={3}
            fullWidth
            variant="outlined"
            value={actionNotes}
            onChange={(e) => setActionNotes(e.target.value)}
            placeholder={actionType === 'approve' ? 'Add any comments about this approval...' : 'Explain why this assignment is being rejected...'}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmAction}
            variant="contained"
            color={actionType === 'approve' ? 'success' : 'error'}
            startIcon={actionType === 'approve' ? <ApproveIcon /> : <RejectIcon />}
          >
            {actionType === 'approve' ? 'Approve' : 'Reject'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AssignmentsPage;