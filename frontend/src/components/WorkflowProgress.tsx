/**
 * Workflow Progress Component
 * Displays workflow status, phase progress, and handles phase transitions with date management
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Button,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  CircularProgress
} from '@mui/material';
import {
  CheckCircle,
  PlayArrow,
  Block,
  Refresh,
  Schedule,
  Warning,
  CalendarToday,
  Edit,
  SwapHoriz,
  RestoreFromTrash,
  OpenInNew
} from '@mui/icons-material';
import { workflowApi, WorkflowStatus, WorkflowPhase, WorkflowPhaseOverride } from '../api/workflow';
import { useApiCache } from '../hooks/useApiCache';
import apiClient from '../api/client';

interface WorkflowProgressProps {
  cycleId: number;
  reportId: number;
  onStatusChange?: (status: WorkflowStatus) => void;
}

const WorkflowProgress: React.FC<WorkflowProgressProps> = ({
  cycleId,
  reportId,
  onStatusChange
}) => {
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [initializationDialog, setInitializationDialog] = useState(false);
  const [completionDialog, setCompletionDialog] = useState<{
    open: boolean;
    phaseName: string;
  }>({
    open: false,
    phaseName: ''
  });
  const [overrideDialog, setOverrideDialog] = useState<{
    open: boolean;
    phaseName: string;
  }>({
    open: false,
    phaseName: ''
  });
  const [dateDialog, setDateDialog] = useState<{
    open: boolean;
    phaseName: string;
    mode: 'start' | 'update_dates';
  }>({
    open: false,
    phaseName: '',
    mode: 'start'
  });
  const [completionNotes, setCompletionNotes] = useState('');
  const [plannedStartDate, setPlannedStartDate] = useState('');
  const [plannedEndDate, setPlannedEndDate] = useState('');
  const [overrideData, setOverrideData] = useState<{
    state_override?: 'Not Started' | 'In Progress' | 'Complete' | null;
    status_override?: 'On Track' | 'At Risk' | 'Past Due' | null;
    override_reason: string;
  }>({
    override_reason: ''
  });

  const navigate = useNavigate();
  
  // Initialize API cache with shorter TTL for development
  const apiCache = useApiCache<any>({
    ttl: 10000, // 10 seconds
    dedupeWindow: 2000 // 2 seconds
  });

  // Map phase names to route-friendly names
  const getPhaseRoute = (phaseName: string): string => {
    const phaseRoutes: Record<string, string> = {
      'Planning': 'planning',
      'Scoping': 'scoping',
      'Sample Selection': 'sample-selection',
      'Data Provider ID': 'data-provider-id',
      'Data Owner ID': 'data-owner',
      'Request Info': 'request-info',
      'Testing': 'test-execution',
      'Test Execution': 'test-execution',
      'Observations': 'observation-management',
      'Observation Management': 'observation-management',
      'Preparing Test Report': 'test-report',
      'Test Report': 'test-report'
    };
    return phaseRoutes[phaseName] || phaseName.toLowerCase().replace(/\s+/g, '-');
  };

  const handleViewPhaseDetails = (phaseName: string) => {
    const phaseRoute = getPhaseRoute(phaseName);
    navigate(`/cycles/${cycleId}/reports/${reportId}/${phaseRoute}`);
  };

  const loadWorkflowStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const cacheKey = `workflow-status-${cycleId}-${reportId}`;
      const status = await apiCache.executeCachedRequest(
        cacheKey,
        () => workflowApi.getWorkflowStatus(cycleId, reportId)
      );
      
      setWorkflowStatus(status);
      setRetryCount(0); // Reset retry count on success
      if (status) {
        onStatusChange?.(status);
      }
    } catch (err: any) {
      // Handle different types of errors gracefully
      const isNotFound = err.response?.status === 404;
      const isServerError = err.response?.status >= 500;
      const isRateLimit = err.response?.status === 429;
      
      if (isRateLimit) {
        // Implement exponential backoff for rate limiting
        const retryDelay = Math.min(1000 * Math.pow(2, retryCount), 10000); // Max 10 seconds
        setError(`Too many requests. Retrying in ${Math.ceil(retryDelay / 1000)} seconds...`);
        
        if (retryCount < 3) {
          setTimeout(() => {
            setRetryCount(prev => prev + 1);
            loadWorkflowStatus();
          }, retryDelay);
        } else {
          setError('Too many requests. Please refresh the page to try again.');
        }
      } else if (isNotFound) {
        setError('Workflow phases not yet initialized for this report. Initialize workflow to track phase progress.');
      } else if (isServerError) {
        setError('Workflow service temporarily unavailable. Core functionality is not affected.');
      } else {
        setError(err.response?.data?.detail || 'Failed to load workflow status');
      }
    } finally {
      setLoading(false);
    }
  }, [cycleId, reportId, onStatusChange, retryCount]);

  const handleRefresh = useCallback(() => {
    // Clear cache and reload
    apiCache.invalidateCache(`workflow-status-${cycleId}-${reportId}`);
    setRetryCount(0);
    loadWorkflowStatus();
  }, [cycleId, reportId, loadWorkflowStatus]);

  const handleInitializeWorkflow = async () => {
    try {
      setActionLoading('initialize');
      await workflowApi.initializeWorkflow(cycleId, reportId);
      setInitializationDialog(false);
      
      // Clear cache and reload with delay
      apiCache.invalidateCache(`workflow-status-${cycleId}-${reportId}`);
      setTimeout(() => {
        loadWorkflowStatus();
      }, 1000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initialize workflow');
    } finally {
      setActionLoading(null);
    }
  };

  const handleStartPhaseWithDates = async () => {
    try {
      setActionLoading(dateDialog.phaseName);
      
      const payload = {
        action: 'start' as const,
        planned_start_date: plannedStartDate || undefined,
        planned_end_date: plannedEndDate || undefined,
      };
      
      await workflowApi.startPhaseWithDates(cycleId, reportId, dateDialog.phaseName, payload);
      setDateDialog({ open: false, phaseName: '', mode: 'start' });
      setPlannedStartDate('');
      setPlannedEndDate('');
      
      // Clear cache and reload with delay
      apiCache.invalidateCache(`workflow-status-${cycleId}-${reportId}`);
      setTimeout(() => {
        loadWorkflowStatus();
      }, 1000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start phase');
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpdatePhaseDates = async () => {
    try {
      setActionLoading(dateDialog.phaseName);
      
      const payload = {
        planned_start_date: plannedStartDate || null,
        planned_end_date: plannedEndDate || null,
      };
      
      await workflowApi.updatePhaseDates(cycleId, reportId, dateDialog.phaseName, payload);
      setDateDialog({ open: false, phaseName: '', mode: 'update_dates' });
      setPlannedStartDate('');
      setPlannedEndDate('');
      
      // Clear cache and reload with delay
      apiCache.invalidateCache(`workflow-status-${cycleId}-${reportId}`);
      setTimeout(() => {
        loadWorkflowStatus();
      }, 1000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update phase dates');
    } finally {
      setActionLoading(null);
    }
  };

  const handleStartPhase = async (phaseName: string) => {
    // Show date dialog for starting phases
    setDateDialog({ open: true, phaseName, mode: 'start' });
    setPlannedStartDate(new Date().toISOString().split('T')[0]); // Default to today
    setPlannedEndDate('');
  };

  const handleCompletePhase = async () => {
    try {
      setActionLoading(completionDialog.phaseName);
      await workflowApi.completePhase(
        cycleId,
        reportId,
        completionDialog.phaseName,
        completionNotes
      );
      setCompletionDialog({ open: false, phaseName: '' });
      setCompletionNotes('');
      // Add delay to avoid rate limiting
      setTimeout(() => {
        loadWorkflowStatus();
      }, 1000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to complete phase');
    } finally {
      setActionLoading(null);
    }
  };

  const handleEditPhaseDates = (phaseName: string, phase: WorkflowPhase) => {
    setDateDialog({ open: true, phaseName, mode: 'update_dates' });
    setPlannedStartDate(phase.planned_start_date || '');
    setPlannedEndDate(phase.planned_end_date || '');
  };

  const handleOverridePhase = (phaseName: string, phase: WorkflowPhase) => {
    setOverrideDialog({ open: true, phaseName });
    setOverrideData({
      state_override: phase.state_override || null,
      status_override: phase.status_override || null,
      override_reason: ''
    });
  };

  const handleSaveOverride = async () => {
    try {
      setActionLoading(overrideDialog.phaseName);
      await workflowApi.overridePhaseStatus(cycleId, reportId, overrideDialog.phaseName, overrideData as WorkflowPhaseOverride);
      setOverrideDialog({ open: false, phaseName: '' });
      setOverrideData({ override_reason: '' });
      // Add delay to avoid rate limiting
      setTimeout(() => {
        loadWorkflowStatus();
      }, 1000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save override');
    } finally {
      setActionLoading(null);
    }
  };

  const handleClearOverrides = async (phaseName: string) => {
    try {
      setActionLoading(phaseName);
      await workflowApi.clearPhaseOverrides(cycleId, reportId, phaseName);
      // Add delay to avoid rate limiting
      setTimeout(() => {
        loadWorkflowStatus();
      }, 1000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to clear overrides');
    } finally {
      setActionLoading(null);
    }
  };

  const getPhaseStatusColor = (status: string): 'success' | 'warning' | 'info' | 'default' => {
    switch (status) {
      case 'Complete': return 'success';
      case 'In Progress': return 'warning';
      case 'Pending Approval': return 'info';
      default: return 'default';
    }
  };

  const getPhaseIcon = (phase: WorkflowPhase) => {
    if (phase.effective_state === 'Complete') {
      return <CheckCircle color="success" />;
    } else if (phase.effective_state === 'In Progress') {
      // Show warning for schedule issues
      if (phase.effective_status === 'Past Due') {
        return <Warning color="error" />;
      } else if (phase.effective_status === 'At Risk') {
        return <Warning color="warning" />;
      }
      return <CircularProgress size={20} />;
    } else if (phase.can_start) {
      return <PlayArrow color="primary" />;
    } else {
      return <Block color="disabled" />;
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString();
  };

  const getDaysUntilDue = (phase: WorkflowPhase) => {
    if (!phase.planned_end_date) return null;
    const today = new Date();
    const endDate = new Date(phase.planned_end_date);
    const diffTime = endDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const renderPhaseCard = (phase: WorkflowPhase) => {
    const daysUntilDue = getDaysUntilDue(phase);
    
    return (
      <Card key={phase.phase_name} sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box display="flex" alignItems="center" gap={2}>
              {getPhaseIcon(phase)}
              <Box>
                <Typography 
                  variant="h6"
                  sx={{ 
                    cursor: 'pointer',
                    color: 'primary.main',
                    textDecoration: 'underline',
                    '&:hover': {
                      color: 'primary.dark',
                    }
                  }}
                  onClick={() => handleViewPhaseDetails(phase.phase_name)}
                >
                  {phase.phase_name}
                </Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  <Chip
                    label={phase.effective_state}
                    size="small"
                    color={getPhaseStatusColor(phase.effective_state)}
                  />
                {(phase.effective_status === 'Past Due' || phase.effective_status === 'At Risk') && (
                  <Chip
                    label={phase.effective_status}
                    size="small"
                    color={phase.effective_status === 'Past Due' ? 'error' : 'warning'}
                    sx={{ ml: 1 }}
                  />
                )}
                {phase.has_overrides && (
                  <Chip
                    label="Override Active"
                    size="small"
                    color="info"
                    sx={{ ml: 1 }}
                  />
                )}
                {phase.progress_percentage !== undefined && (
                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                    {Math.round(phase.progress_percentage)}%
                  </Typography>
                )}
              </Box>
              </Box>
            </Box>
            
            <Box display="flex" gap={1}>
              <IconButton
                size="small"
                onClick={() => handleEditPhaseDates(phase.phase_name, phase)}
                title="Edit Dates"
              >
                <Edit fontSize="small" />
              </IconButton>
              <IconButton
                size="small"
                onClick={() => handleOverridePhase(phase.phase_name, phase)}
                title="Override State/Status"
              >
                <SwapHoriz fontSize="small" />
              </IconButton>
              {phase.has_overrides && (
                <IconButton
                  size="small"
                  onClick={() => handleClearOverrides(phase.phase_name)}
                  title="Clear Overrides"
                  disabled={actionLoading === phase.phase_name}
                >
                  <RestoreFromTrash fontSize="small" />
                </IconButton>
              )}
            </Box>
          </Box>

          {/* Progress Bar for Phase */}
          {phase.progress_percentage !== undefined && phase.effective_state === 'In Progress' && (
            <Box sx={{ mb: 2 }}>
              <Box display="flex" alignItems="center" gap={2}>
                <LinearProgress
                  variant="determinate"
                  value={phase.progress_percentage}
                  sx={{ flex: 1, height: 6, borderRadius: 3 }}
                />
                <Typography variant="body2" color="text.secondary">
                  {Math.round(phase.progress_percentage)}%
                </Typography>
              </Box>
            </Box>
          )}

          {/* Date Information */}
          <Box display="flex" gap={2} sx={{ mb: 2 }}>
            <Box flex={1}>
              <Box display="flex" alignItems="center" gap={1}>
                <CalendarToday fontSize="small" color="action" />
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Planned Start
                  </Typography>
                  <Typography variant="body2">
                    {formatDate(phase.planned_start_date || null)}
                  </Typography>
                </Box>
              </Box>
            </Box>
            <Box flex={1}>
              <Box display="flex" alignItems="center" gap={1}>
                <Schedule fontSize="small" color="action" />
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Planned End
                  </Typography>
                  <Typography variant="body2">
                    {formatDate(phase.planned_end_date || null)}
                    {daysUntilDue !== null && phase.status !== 'Complete' && (
                      <Typography variant="caption" color={daysUntilDue < 0 ? 'error' : daysUntilDue <= 7 ? 'warning.main' : 'text.secondary'} display="block">
                        {daysUntilDue < 0 ? `${Math.abs(daysUntilDue)} days overdue` : 
                         daysUntilDue === 0 ? 'Due today' :
                         `${daysUntilDue} days remaining`}
                      </Typography>
                    )}
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Box>

          {/* Action Buttons */}
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<OpenInNew />}
              onClick={() => handleViewPhaseDetails(phase.phase_name)}
            >
              View Details
            </Button>
            {phase.can_start && phase.status === 'Not Started' && (
              <Button
                variant="contained"
                size="small"
                startIcon={<PlayArrow />}
                onClick={() => handleStartPhase(phase.phase_name)}
                disabled={actionLoading === phase.phase_name}
              >
                {actionLoading === phase.phase_name ? 'Starting...' : 'Start Phase'}
              </Button>
            )}
            {phase.status === 'In Progress' && (
              <Button
                variant="contained"
                color="success"
                size="small"
                startIcon={<CheckCircle />}
                onClick={() => setCompletionDialog({ open: true, phaseName: phase.phase_name })}
                disabled={actionLoading === phase.phase_name}
              >
                Complete Phase
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  };

  useEffect(() => {
    // Only load data if we have valid IDs and haven't loaded recently
    if (cycleId && reportId) {
      loadWorkflowStatus();
    }
  }, [cycleId, reportId]); // Removed function dependencies to prevent loops

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2}>
            <CircularProgress size={20} />
            <Typography>Loading workflow status...</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error" action={
            <IconButton onClick={handleRefresh}>
              <Refresh />
            </IconButton>
          }>
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!workflowStatus) {
    return (
      <Box>
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No Workflow Initialized
              </Typography>
              <Typography color="text.secondary" gutterBottom>
                Initialize workflow phases to start the testing process for this report.
              </Typography>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={() => setInitializationDialog(true)}
                disabled={actionLoading === 'initialize'}
              >
                {actionLoading === 'initialize' ? 'Initializing...' : 'Initialize Workflow'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box>
      {/* Overall Progress */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Workflow Progress
          </Typography>
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <LinearProgress
              variant="determinate"
              value={workflowStatus.overall_progress}
              sx={{ flex: 1, height: 8, borderRadius: 4 }}
            />
            <Typography variant="h6" color="primary">
              {Math.round(workflowStatus.overall_progress)}%
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary">
            Current Phase: {workflowStatus.current_phase || 'Not Started'}
          </Typography>
        </CardContent>
      </Card>

      {/* Phase Cards */}
      <Typography variant="h6" gutterBottom>
        Workflow Phases
      </Typography>
      {workflowStatus.phases.map(renderPhaseCard)}

      {/* Date Dialog */}
      <Dialog open={dateDialog.open} onClose={() => setDateDialog({ open: false, phaseName: '', mode: 'start' })} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dateDialog.mode === 'start' ? `Start Phase: ${dateDialog.phaseName}` : `Update Dates: ${dateDialog.phaseName}`}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" gap={2} sx={{ mt: 1 }}>
            <Box flex={1}>
              <TextField
                label="Planned Start Date"
                type="date"
                value={plannedStartDate}
                onChange={(e) => setPlannedStartDate(e.target.value)}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Box>
            <Box flex={1}>
              <TextField
                label="Planned End Date"
                type="date"
                value={plannedEndDate}
                onChange={(e) => setPlannedEndDate(e.target.value)}
                fullWidth
                InputLabelProps={{ shrink: true }}
                required
              />
            </Box>
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            End date is required. Phases will be marked as "Past Due" if not completed by the end date, 
            and "Watch Item" if still open 1 week before the end date.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDateDialog({ open: false, phaseName: '', mode: 'start' })}>
            Cancel
          </Button>
          <Button
            onClick={dateDialog.mode === 'start' ? handleStartPhaseWithDates : handleUpdatePhaseDates}
            variant="contained"
            disabled={!plannedEndDate || actionLoading === dateDialog.phaseName}
          >
            {actionLoading === dateDialog.phaseName ? 'Saving...' : (dateDialog.mode === 'start' ? 'Start Phase' : 'Update Dates')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Completion Dialog */}
      <Dialog open={completionDialog.open} onClose={() => setCompletionDialog({ open: false, phaseName: '' })} maxWidth="sm" fullWidth>
        <DialogTitle>Complete Phase: {completionDialog.phaseName}</DialogTitle>
        <DialogContent>
          <TextField
            label="Completion Notes (Optional)"
            multiline
            rows={3}
            value={completionNotes}
            onChange={(e) => setCompletionNotes(e.target.value)}
            fullWidth
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompletionDialog({ open: false, phaseName: '' })}>
            Cancel
          </Button>
          <Button
            onClick={handleCompletePhase}
            variant="contained"
            color="success"
            disabled={actionLoading === completionDialog.phaseName}
          >
            {actionLoading === completionDialog.phaseName ? 'Completing...' : 'Complete Phase'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Initialization Dialog */}
      <Dialog open={initializationDialog} onClose={() => setInitializationDialog(false)}>
        <DialogTitle>Initialize Workflow</DialogTitle>
        <DialogContent>
          <Typography>
            This will create all 7 workflow phases for this report. Are you sure you want to continue?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInitializationDialog(false)}>Cancel</Button>
          <Button
            onClick={handleInitializeWorkflow}
            variant="contained"
            disabled={actionLoading === 'initialize'}
          >
            {actionLoading === 'initialize' ? 'Initializing...' : 'Initialize'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Override Dialog */}
      <Dialog open={overrideDialog.open} onClose={() => setOverrideDialog({ open: false, phaseName: '' })} maxWidth="sm" fullWidth>
        <DialogTitle>Override Phase: {overrideDialog.phaseName}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Override the current state and/or status for this phase. This allows you to manually adjust 
            the phase progress when special circumstances require it.
          </Typography>
          
          <Box display="flex" gap={2} sx={{ mt: 2 }}>
            <Box flex={1}>
              <TextField
                select
                label="State Override"
                value={overrideData.state_override || ''}
                onChange={(e) => setOverrideData({
                  ...overrideData,
                  state_override: e.target.value as 'Not Started' | 'In Progress' | 'Complete' || null
                })}
                fullWidth
                SelectProps={{ native: true }}
              >
                <option value="">No Override</option>
                <option value="Not Started">Not Started</option>
                <option value="In Progress">In Progress</option>
                <option value="Complete">Complete</option>
              </TextField>
            </Box>
            <Box flex={1}>
              <TextField
                select
                label="Status Override"
                value={overrideData.status_override || ''}
                onChange={(e) => setOverrideData({
                  ...overrideData,
                  status_override: e.target.value as 'On Track' | 'At Risk' | 'Past Due' || null
                })}
                fullWidth
                SelectProps={{ native: true }}
              >
                <option value="">No Override</option>
                <option value="On Track">On Track</option>
                <option value="At Risk">At Risk</option>
                <option value="Past Due">Past Due</option>
              </TextField>
            </Box>
          </Box>
          
          <TextField
            label="Override Reason (Required)"
            multiline
            rows={3}
            value={overrideData.override_reason}
            onChange={(e) => setOverrideData({
              ...overrideData,
              override_reason: e.target.value
            })}
            fullWidth
            sx={{ mt: 2 }}
            required
            helperText="Please provide a reason for this override"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOverrideDialog({ open: false, phaseName: '' })}>
            Cancel
          </Button>
          <Button
            onClick={handleSaveOverride}
            variant="contained"
            disabled={!overrideData.override_reason.trim() || actionLoading === overrideDialog.phaseName}
          >
            {actionLoading === overrideDialog.phaseName ? 'Saving...' : 'Save Override'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WorkflowProgress; 