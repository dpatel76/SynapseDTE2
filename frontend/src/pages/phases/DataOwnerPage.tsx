import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  LinearProgress,
  IconButton,
  Tooltip,
  Autocomplete
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  CheckCircle as CheckCircleIcon,
  Business as BusinessIcon,
  Email as EmailIcon,
  Refresh as RefreshIcon,
  Assignment as AssignmentIcon,
  Person as PersonIcon,
  Key as KeyIcon,
  DataUsage as DataUsageIcon,
  Timeline as TimelineIcon,
  Assignment as AttributeIcon,
  Pending as PendingIcon,
  CheckCircleOutline as CompletedIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/api';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';
import { DynamicActivityCards } from '../../components/phase/DynamicActivityCards';
import { useUniversalAssignments } from '../../hooks/useUniversalAssignments';
import { UniversalAssignmentAlert } from '../../components/UniversalAssignmentAlert';
// import WorkflowProgress from '../../components/WorkflowProgress';

interface DataOwnerPhaseStatus {
  cycle_id: number;
  report_id: number;
  phase_status: string;
  total_attributes: number;
  attributes_with_lob_assignments: number;
  attributes_with_data_owners: number;
  pending_cdo_assignments: number;
  overdue_assignments: number;
  can_submit_lob_assignments: boolean;
  can_complete_phase: boolean;
  completion_requirements: string[];
  // New metrics fields
  scoped_attributes?: number;
  total_samples?: number;
  total_lobs?: number;
  assigned_data_providers?: number;
  total_data_providers?: number;
  started_at?: string;
}

interface AttributeAssignment {
  attribute_id: number;
  attribute_name: string;
  is_primary_key: boolean;
  assigned_lobs: Array<{lob_id: number; lob_name: string}>;
  data_owner_id?: number;
  data_owner_name?: string;
  assigned_by?: number;
  assigned_at?: string;
  status: 'Assigned' | 'In Progress' | 'Completed' | 'Overdue';
  assignment_notes?: string;
  is_overdue: boolean;
  sla_deadline?: string;
  hours_remaining?: number;
}

interface ReportInfo {
  cycle_id: number;
  report_id: number;
  report_name: string;
  report_description?: string;
  lob_name: string;
  tester_name: string;
  status: string;
}

// LOB Assignment interfaces
interface LOB {
  lob_id: number;
  lob_name: string;
}

interface AttributeLOBAssignment {
  attribute_id: number;
  lob_ids: number[];
  assignment_rationale?: string;
}

interface LOBAssignmentSubmission {
  assignments: AttributeLOBAssignment[];
  submission_notes?: string;
  confirm_submission: boolean;
}

// Simple toast replacement
const showToast = {
  success: (message: string) => {
    console.log('SUCCESS:', message);
    alert(message);
  },
  error: (message: string) => {
    console.log('ERROR:', message);
    alert('Error: ' + message);
  },
  warning: (message: string) => {
    console.log('WARNING:', message);
    alert('Warning: ' + message);
  }
};

const DataOwnerPage: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Convert string params to numbers
  const cycleIdNum = cycleId ? parseInt(cycleId, 10) : 0;
  const reportIdNum = reportId ? parseInt(reportId, 10) : 0;

  // Unified status system
  const { data: unifiedPhaseStatus, isLoading: statusLoading, refetch: refetchStatus } = usePhaseStatus('Data Provider ID', cycleIdNum, reportIdNum);

  // Universal Assignments integration
  const {
    hasAssignment,
    assignment,
    canDirectAccess,
    acknowledgeMutation,
    startMutation,
    completeMutation
  } = useUniversalAssignments({
    phase: 'Data Owner Identification',
    cycleId: cycleIdNum,
    reportId: reportIdNum,
    assignmentType: 'LOB Assignment'
  });

  // Debug logging
  console.log('DataOwnerPage loaded with:', { cycleId, reportId, cycleIdNum, reportIdNum, user, userRole: user?.role });

  // State
  const [assignments, setAssignments] = useState<AttributeAssignment[]>([]);
  const [reportInfo, setReportInfo] = useState<ReportInfo | null>(null);
  const [reportInfoLoading, setReportInfoLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [phaseStatus, setPhaseStatus] = useState<DataOwnerPhaseStatus | null>(null);
  const [phaseLoading, setPhaseLoading] = useState(false);
  const [showStartDialog, setShowStartDialog] = useState(false);
  const [showNotifyDialog, setShowNotifyDialog] = useState(false);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [sendingToExecutives, setSendingToExecutives] = useState(false);



  // Form state
  const [notificationNotes, setNotificationNotes] = useState('');
  const [completionNotes, setCompletionNotes] = useState('');

  // Role-based redirection for Report Owners
  useEffect(() => {
    // @ts-ignore - Role comes from backend as string "Report Owner"
    if (user?.role === 'Report Owner') {
      // Report Owners should use the data owner review page
      // TODO: Create data-owner-review page
      console.log('Report Owner detected - would redirect to review page');
      // navigate(`/cycles/${cycleId}/reports/${reportId}/data-owner-review`, { replace: true });
      // return;
    }
  }, [user, cycleId, reportId, navigate]);



  // Load report info
  const loadReportInfo = useCallback(async () => {
    setReportInfoLoading(true);
    try {
      const response = await apiClient.get(`/cycle-reports/${cycleIdNum}/reports/${reportIdNum}`);
      setReportInfo(response.data);
    } catch (error) {
      console.error('Error loading report info:', error);
      // Don't show toast error since the main functionality still works
      // showToast.error('Failed to load report information');
    } finally {
      setReportInfoLoading(false);
    }
  }, [cycleIdNum, reportIdNum]);

  // Load phase status
  const loadPhaseStatus = useCallback(async () => {
    setPhaseLoading(true);
    try {
      const response = await apiClient.get(`/data-owner/cycles/${cycleIdNum}/reports/${reportIdNum}/status`);
      console.log('🔍 Phase Status Response:', response.data);
      console.log('🔍 Phase Status Value:', response.data.phase_status);
      setPhaseStatus(response.data);
    } catch (error) {
      console.error('Error loading phase status:', error);
      showToast.error('Failed to load phase status');
    } finally {
      setPhaseLoading(false);
    }
  }, [cycleIdNum, reportIdNum]);

  const loadAssignments = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get(`/data-owner/cycles/${cycleIdNum}/reports/${reportIdNum}/assignment-matrix`);
      // Extract assignments array from the assignment matrix response
      const assignments = response.data.assignments || [];
      setAssignments(assignments);
      

    } catch (error) {
      console.error('Error loading assignments:', error);
      showToast.error('Failed to load assignments');
    } finally {
      setLoading(false);
    }
  }, [cycleIdNum, reportIdNum]);

  useEffect(() => {
    if (cycleIdNum && reportIdNum) {
      loadReportInfo();
      loadPhaseStatus();
      loadAssignments();
    }
  }, [cycleIdNum, reportIdNum, loadReportInfo, loadPhaseStatus, loadAssignments]);

  const handleStartPhase = async () => {
    try {
      await apiClient.post(`/data-owner/cycles/${cycleIdNum}/reports/${reportIdNum}/start`, {
        notes: notificationNotes
      });
      
      showToast.success('Data owner phase started successfully!');
      setShowStartDialog(false);
      await loadPhaseStatus();
      await loadAssignments();
      refetchStatus(); // Update unified status
    } catch (error: any) {
      console.error('Error starting phase:', error);
      
      // Handle specific case where phase is already started
      if (error.response?.status === 409) {
        showToast.warning('Phase has already been started. Updating status...');
        setShowStartDialog(false);
        
        // Force update the phase status to reflect reality since backend status endpoint is inconsistent
        if (phaseStatus) {
          setPhaseStatus({
            ...phaseStatus,
            phase_status: 'In Progress'
          });
        }
        
        await loadPhaseStatus();
        await loadAssignments();
      } else {
        showToast.error(error.response?.data?.detail || 'Failed to start data owner phase');
      }
    }
  };







  const handleSendNotifications = async () => {
    try {
      // For now, show a success message since this is a simplified workflow  
      // In a real implementation, this would send notifications to data owners
      showToast.success('Notification feature is coming soon! Manual coordination available.');
      setShowNotifyDialog(false);
      await loadPhaseStatus();
    } catch (error: any) {
      console.error('Error sending notifications:', error);
      showToast.error('Notification feature coming soon');
    }
  };

  const handleCompletePhase = async () => {
    try {
      await apiClient.post(`/data-owner/cycles/${cycleIdNum}/reports/${reportIdNum}/complete`, {
        completion_notes: completionNotes,
        confirm_completion: true
      });
      
      showToast.success('Data owner phase completed successfully!');
      setShowCompleteDialog(false);
      await loadPhaseStatus();
    } catch (error: any) {
      console.error('Error completing phase:', error);
      showToast.error(error.response?.data?.detail || 'Failed to complete phase');
    }
  };

  const handleSendToDataExecutives = async () => {
    try {
      setSendingToExecutives(true);
      const response = await apiClient.post(`/data-owner/cycles/${cycleIdNum}/reports/${reportIdNum}/send-to-data-executives`);
      
      const message = response.data.message || 'Successfully sent assignments to Data Executives';
      const assignmentsCreated = response.data.assignments_created || 0;
      const executivesNotified = response.data.executives_notified || 0;
      
      showToast.success(`${message}\n${assignmentsCreated} assignments created for ${executivesNotified} Data Executives`);
      
      // Reload assignments to show updated status
      await loadAssignments();
      await loadPhaseStatus();
      refetchStatus();
    } catch (error: any) {
      console.error('Error sending to data executives:', error);
      showToast.error(error.response?.data?.detail || 'Failed to send assignments to Data Executives');
    } finally {
      setSendingToExecutives(false);
    }
  };

  const handleActivityAction = async (activity: any, action: string) => {
    try {
      // Make the API call to start/complete the activity
      const endpoint = action === 'start' ? 'start' : 'complete';
      const response = await apiClient.post(`/activity-management/activities/${activity.activity_id}/${endpoint}`, {
        cycle_id: cycleIdNum,
        report_id: reportIdNum,
        phase_name: 'Data Provider ID'
      });
      
      // Show success message from backend or default
      const message = response.data.message || activity.metadata?.success_message || `${action === 'start' ? 'Started' : 'Completed'} ${activity.name}`;
      showToast.success(message);
      
      // Special handling for phase_start activities - immediately complete them
      if (action === 'start' && activity.metadata?.activity_type === 'phase_start') {
        console.log('Auto-completing phase_start activity:', activity.name);
        await new Promise(resolve => setTimeout(resolve, 200));
        
        try {
          await apiClient.post(`/activity-management/activities/${activity.activity_id}/complete`, {
            cycle_id: cycleIdNum,
            report_id: reportIdNum,
            phase_name: 'Data Provider ID'
          });
          showToast.success(`${activity.name} completed`);
        } catch (completeError: any) {
          // Ignore "already completed" errors

          if (completeError.response?.status === 400 && 

              completeError.response?.data?.detail?.includes('Cannot complete activity in status')) {

            console.log('Phase start activity already completed, ignoring error');

          } else {

            console.error('Error auto-completing phase_start activity:', completeError);

          }
        }
      }
      
      // Add a small delay to ensure backend has processed the change
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Force refresh of both status systems
      await refetchStatus();
      await loadPhaseStatus();
      await loadAssignments();
    } catch (error: any) {
      console.error('Error handling activity action:', error);
      showToast.error(error.response?.data?.detail || `Failed to ${action} activity`);
    }
  };


  // Use unified status system - status functions imported from useUnifiedStatus hook

  if (phaseLoading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
      {/* Universal Assignment Alert */}
      {hasAssignment && assignment && (
        <UniversalAssignmentAlert
          assignment={assignment}
          onAcknowledge={(id) => acknowledgeMutation.mutate(id)}
          onStart={(id) => startMutation.mutate(id)}
          onComplete={(id) => completeMutation.mutate({ assignmentId: id })}
          showActions={true}
        />
      )}
      
      {/* Workflow Progress */}
      {/* <WorkflowProgress cycleId={cycleId} reportId={reportId} /> */}
      {/* Report Information Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            {/* Left side - Report title and phase description */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <AssignmentIcon color="primary" />
              <Box>
                <Typography variant="h5" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportInfo?.report_name || 'Loading...'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Data Owner ID Phase - Identifying and assigning data owners for each testing attribute
                </Typography>
              </Box>
            </Box>
            
            {/* Right side - Key metadata in compact format */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
              {reportInfoLoading ? (
                <Box sx={{ width: 200 }}>
                  <LinearProgress />
                </Box>
              ) : (
                <>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BusinessIcon color="action" fontSize="small" />
                    <Typography variant="body2" color="text.secondary">LOB:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {reportInfo?.lob_name || 'Unknown'}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PersonIcon color="action" fontSize="small" />
                    <Typography variant="body2" color="text.secondary">Tester:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {reportInfo?.tester_name || 'Not assigned'}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" color="text.secondary">ID:</Typography>
                    <Typography variant="body2" fontWeight="medium" fontFamily="monospace">
                      {reportInfo?.report_id || reportIdNum}
                    </Typography>
                  </Box>
                </>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Data Owner Metrics Row 1 - Six Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="primary.main" fontWeight="bold">
                {unifiedPhaseStatus?.metadata?.total_attributes || phaseStatus?.total_attributes || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Attributes
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="success.main" fontWeight="bold">
                {unifiedPhaseStatus?.metadata?.scoped_attributes || phaseStatus?.scoped_attributes || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Scoped Attributes
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="info.main" fontWeight="bold">
                {unifiedPhaseStatus?.metadata?.total_samples || phaseStatus?.total_samples || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Samples
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="warning.main" fontWeight="bold">
                {unifiedPhaseStatus?.metadata?.total_lobs || phaseStatus?.total_lobs || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                LOBs
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="error.main" fontWeight="bold">
                {(unifiedPhaseStatus?.metadata?.assigned_data_providers || phaseStatus?.assigned_data_providers || 0)}/{(unifiedPhaseStatus?.metadata?.total_data_providers || phaseStatus?.total_data_providers || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Data Owners (Assigned/Total)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="primary.main" fontWeight="bold">
                {(() => {
                  const startDate = unifiedPhaseStatus?.metadata?.started_at || phaseStatus?.started_at;
                  const endDate = unifiedPhaseStatus?.metadata?.completed_at;
                  if (!startDate) return 0;
                  const end = endDate ? new Date(endDate) : new Date();
                  const start = new Date(startDate);
                  return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
                })()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Days Elapsed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Row 2: On-Time Status + Phase Controls */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 6 }}>
          <Card sx={{ height: 100 }}>
            <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <Typography 
                variant="h3" 
                color={
                  (unifiedPhaseStatus?.phase_status === 'completed' || phaseStatus?.phase_status === 'Complete') ? 
                    'success.main' :
                  (unifiedPhaseStatus?.phase_status === 'in_progress' || phaseStatus?.phase_status === 'In Progress') ?
                    'primary.main' : 'warning.main'
                } 
                component="div"
                sx={{ fontSize: '1.5rem' }}
              >
                {(unifiedPhaseStatus?.phase_status === 'completed' || phaseStatus?.phase_status === 'Complete') ? 
                  'Yes - Completed On-Time' :
                (unifiedPhaseStatus?.phase_status === 'in_progress' || phaseStatus?.phase_status === 'In Progress') ?
                  'On Track' : 'Not Started'
                }
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {(unifiedPhaseStatus?.phase_status === 'completed' || phaseStatus?.phase_status === 'Complete') ? 'On-Time Completion Status' : 'Current Schedule Status'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ height: 100 }}>
            <CardContent sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" sx={{ fontSize: '1rem' }}>
                  Phase Controls
                </Typography>
                
                {/* Status Update Controls */}
                {phaseStatus && (unifiedPhaseStatus?.phase_status === 'in_progress' || phaseStatus.phase_status === 'In Progress') && (
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip
                      label="At Risk"
                      size="small"
                      color="warning"
                      variant="outlined"
                      clickable
                      onClick={() => {/* Handle status update */}}
                      disabled={phaseLoading}
                      sx={{ fontSize: '0.7rem' }}
                    />
                    <Chip
                      label="Off Track"
                      size="small"
                      color="error"
                      variant="outlined"
                      clickable
                      onClick={() => {/* Handle status update */}}
                      disabled={phaseLoading}
                      sx={{ fontSize: '0.7rem' }}
                    />
                  </Box>
                )}
              </Box>
              
              {/* Completion Requirements */}
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                  {!phaseStatus ? (
                    'To complete: Assign data owners to all attributes'
                  ) : (unifiedPhaseStatus?.phase_status === 'completed' || phaseStatus.phase_status === 'Complete') ? (
                    'Phase completed successfully - all requirements met'
                  ) : phaseStatus.can_complete_phase ? (
                    'Ready to complete - all requirements met'
                  ) : (
                    `To complete: ${phaseStatus.completion_requirements?.[0] || 'Assign data owners to all attributes'}`
                  )}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>


      {/* Data Owner Phase Workflow */}
      {phaseStatus && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <DataUsageIcon color="primary" />
              Data Owner Identification Workflow
            </Typography>
            
            <Box sx={{ mt: 2 }}>
              {unifiedPhaseStatus?.activities ? (
                <DynamicActivityCards
                  activities={unifiedPhaseStatus.activities}
                  cycleId={cycleIdNum}
                  reportId={reportIdNum}
                  phaseName="Data Provider ID"
                  phaseStatus={unifiedPhaseStatus.phase_status}
                  overallCompletion={unifiedPhaseStatus.overall_completion_percentage}
                  onActivityAction={handleActivityAction}
                  />
                ) : (
                  <Box sx={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    minHeight: 200, 
                    flexDirection: 'column', 
                    gap: 2 
                  }}>
                    <CircularProgress />
                    <Typography variant="body2" color="text.secondary">
                      Loading data owner identification activities...
                    </Typography>
                  </Box>
                )}
            </Box>
          </CardContent>
        </Card>
      )}



      {/* Attribute Assignments Table */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Attribute Assignments ({assignments.length})
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              {/* Send to Data Executives Button - Show for Testers */}
              {(user?.role === 'Tester' || user?.role === 'Test Executive') && assignments.length > 0 && (
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<EmailIcon />}
                  onClick={handleSendToDataExecutives}
                  disabled={sendingToExecutives}
                >
                  {sendingToExecutives ? 'Sending...' : 'Send to Data Executives'}
                </Button>
              )}
              
              {/* Data Executive Assignments Button - Only show for Data Executives */}
              {user?.role === 'Data Executive' && (
                <>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<AssignmentIcon />}
                    onClick={() => navigate(`/cycles/${cycleId}/reports/${reportId}/assign-data-owners`)}
                  >
                    Assign Data Owners
                  </Button>
                  <Button
                    variant="outlined"
                    color="secondary"
                    startIcon={<AssignmentIcon />}
                    onClick={() => navigate(`/cycles/${cycleId}/reports/${reportId}/cdo-assignments`)}
                  >
                    My Assignments
                  </Button>
                </>
              )}
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => {
                  loadPhaseStatus();
                  loadAssignments();
                }}
              >
                Refresh
              </Button>
            </Box>
          </Box>
          
          {loading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : assignments.length === 0 ? (
            <Alert severity="info" sx={{ mt: 2 }}>
              No attribute assignments yet. Start the phase to begin identifying data owners.
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Attribute</TableCell>
                    <TableCell>LOB</TableCell>
                    <TableCell>Data Owner</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {assignments.map((assignment, index) => (
                    <TableRow key={`${assignment.attribute_id}-${index}`}>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {assignment.attribute_name}
                          </Typography>
                          {assignment.is_primary_key && (
                            <Typography variant="caption" color="primary">
                              Primary Key
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        {assignment.assigned_lobs?.length > 0 ? (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {assignment.assigned_lobs.map((lob) => (
                              <Chip 
                                key={lob.lob_id}
                                label={lob.lob_name} 
                                size="small" 
                                variant="outlined"
                              />
                            ))}
                          </Box>
                        ) : assignment.is_primary_key ? (
                          <Typography variant="body2" color="text.secondary">
                            N/A (Primary Key)
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="warning.main">
                            LOB Assignment Pending
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {assignment.data_owner_name ? (
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {assignment.data_owner_name}
                            </Typography>
                            {assignment.assigned_by && (
                              <Typography variant="caption" display="block" color="success.main">
                                Assigned by Data Executive ID: {assignment.assigned_by}
                              </Typography>
                            )}
                          </Box>
                        ) : assignment.is_primary_key ? (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <KeyIcon color="primary" fontSize="small" />
                            <Typography variant="body2" color="text.secondary">
                              N/A - Primary Key
                            </Typography>
                          </Box>
                        ) : (
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Awaiting Data Executive Assignment
                            </Typography>
                            <Typography variant="caption" color="info.main">
                              Data Executive will assign from assigned LOB
                            </Typography>
                          </Box>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={
                            assignment.is_primary_key 
                              ? 'Completed'  // Primary keys are always completed (no data owner needed)
                              : (assignment.status === 'Assigned' ? 'Pending Data Executive Assignment' : assignment.status)
                          }
                          size="small"
                          color={
                            assignment.is_primary_key 
                              ? 'success'  // Primary keys are always green
                              : (assignment.status === 'Assigned' ? 'warning' : 
                                 assignment.status === 'Completed' ? 'success' :
                                 assignment.status === 'Overdue' ? 'error' : 'primary')
                          }
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Start Phase Dialog */}
      <Dialog open={showStartDialog} onClose={() => setShowStartDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Start Data Owner Phase</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <Alert severity="info">
              This will initialize the data owner identification process and begin assigning 
              attributes to LOBs and their data owners.
            </Alert>
            <TextField
              label="Notes"
              multiline
              rows={3}
              value={notificationNotes}
              onChange={(e) => setNotificationNotes(e.target.value)}
              fullWidth
              placeholder="Optional: Add notes about the data owner coordination..."
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowStartDialog(false)}>Cancel</Button>
          <Button onClick={handleStartPhase} variant="contained">
            Start Phase
          </Button>
        </DialogActions>
      </Dialog>



      {/* Send Notifications Dialog */}
      <Dialog open={showNotifyDialog} onClose={() => setShowNotifyDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Send Data Owner Notifications</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <Alert severity="info">
              This will send notifications to all assigned data owners requesting sample data 
              for their assigned attributes.
            </Alert>
            <TextField
              label="Notification Notes"
              multiline
              rows={3}
              value={notificationNotes}
              onChange={(e) => setNotificationNotes(e.target.value)}
              fullWidth
              placeholder="Optional: Add specific instructions for data owners..."
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowNotifyDialog(false)}>Cancel</Button>
          <Button onClick={handleSendNotifications} variant="contained" color="info">
            Send Notifications
          </Button>
        </DialogActions>
      </Dialog>

      {/* Complete Phase Dialog */}
      <Dialog open={showCompleteDialog} onClose={() => setShowCompleteDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Complete Data Owner Phase</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Completion Notes"
              multiline
              rows={3}
              value={completionNotes}
              onChange={(e) => setCompletionNotes(e.target.value)}
              fullWidth
              placeholder="Optional: Add notes about the data owner phase completion..."
            />
            <Alert severity="success">
              All requirements have been met. The phase can be completed.
            </Alert>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCompleteDialog(false)}>Cancel</Button>
          <Button onClick={handleCompletePhase} variant="contained" color="success">
            Complete Phase
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DataOwnerPage; 