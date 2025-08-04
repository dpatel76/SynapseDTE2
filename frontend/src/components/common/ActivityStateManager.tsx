import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress
} from '@mui/material';
import {
  PlayArrow,
  CheckCircle,
  Error,
  Refresh,
  Info,
  Assignment,
  Send
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { activityApi } from '../../api/metrics';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'react-toastify';

interface ActivityStateManagerProps {
  cycleId: string;
  reportId: string;
  phaseName: string;
  onPhaseComplete?: () => void;
  showControls?: boolean;
}

interface Activity {
  name: string;
  state: 'Not Started' | 'In Progress' | 'Completed' | 'Revision Requested';
  last_updated?: string;
  updated_by?: string;
  can_start?: boolean;
  can_complete?: boolean;
}

interface PhaseData {
  activities: Record<string, Activity>;
  phase_progress: number;
  can_start_phase: boolean;
  can_complete_phase: boolean;
  next_activity?: string;
}

const getStateColor = (state: string) => {
  switch (state) {
    case 'Completed':
      return 'success';
    case 'In Progress':
      return 'info';
    case 'Revision Requested':
      return 'warning';
    default:
      return 'default';
  }
};

const getStateIcon = (state: string) => {
  switch (state) {
    case 'Completed':
      return <CheckCircle fontSize="small" />;
    case 'In Progress':
      return <PlayArrow fontSize="small" />;
    case 'Revision Requested':
      return <Refresh fontSize="small" />;
    default:
      return <Assignment fontSize="small" />;
  }
};

export const ActivityStateManager: React.FC<ActivityStateManagerProps> = ({
  cycleId,
  reportId,
  phaseName,
  onPhaseComplete,
  showControls = true
}) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectDialog, setShowRejectDialog] = useState(false);

  const canManuallyControl = user?.role === 'Tester' || user?.role === 'Test Executive';
  const canApprove = user?.role === 'Report Owner' || user?.role === 'Report Executive';

  // Fetch activity states
  const { data: phaseData, isLoading, error } = useQuery<PhaseData>({
    queryKey: ['activity-states', cycleId, reportId, phaseName],
    queryFn: async () => {
      const response = await activityApi.getActivityStates(cycleId, reportId, phaseName);
      // Transform ActivityState[] to PhaseData format
      const activityStates = response.data;
      const activities: Record<string, Activity> = {};
      
      activityStates.forEach(state => {
        activities[state.activity_name] = {
          name: state.activity_name,
          state: state.state,
          last_updated: state.last_updated,
          updated_by: state.updated_by,
          can_start: state.can_start,
          can_complete: state.can_complete
        };
      });
      
      // Calculate phase progress based on completed activities
      const totalActivities = activityStates.length;
      const completedActivities = activityStates.filter(a => a.state === 'Completed').length;
      const phase_progress = totalActivities > 0 ? (completedActivities / totalActivities) * 100 : 0;
      
      // Determine if phase can be started/completed
      const startActivity = activities[`Start ${phaseName} Phase`];
      const completeActivity = activities[`Complete ${phaseName} Phase`];
      const can_start_phase = startActivity?.can_start || false;
      const can_complete_phase = completeActivity?.can_complete || false;
      
      // Find next activity
      const next_activity = activityStates.find(a => a.state === 'Not Started')?.activity_name;
      
      return {
        activities,
        phase_progress,
        can_start_phase,
        can_complete_phase,
        next_activity
      };
    },
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  // Start phase mutation
  const startPhaseMutation = useMutation({
    mutationFn: async () => {
      return activityApi.startPhase(cycleId, reportId, phaseName);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity-states', cycleId, reportId, phaseName] });
      toast.success('Phase started successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start phase');
    }
  });

  // Complete phase mutation
  const completePhaseMutation = useMutation({
    mutationFn: async () => {
      return activityApi.completePhase(cycleId, reportId, phaseName);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity-states', cycleId, reportId, phaseName] });
      toast.success('Phase completed successfully');
      onPhaseComplete?.();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to complete phase');
    }
  });

  // Update activity state mutation
  const updateStateMutation = useMutation({
    mutationFn: async ({ activity, newState }: { activity: Activity; newState: string }) => {
      return activityApi.updateActivityState(
        activity.name,
        newState,
        cycleId,
        reportId,
        phaseName
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity-states', cycleId, reportId, phaseName] });
      toast.success('Activity state updated');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update activity state');
    }
  });

  // Submit for review mutation
  const submitForReviewMutation = useMutation({
    mutationFn: async () => {
      return activityApi.submitForReview(cycleId, reportId, phaseName);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity-states', cycleId, reportId, phaseName] });
      toast.success('Submitted for review');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to submit for review');
    }
  });

  // Approve submission mutation
  const approveSubmissionMutation = useMutation({
    mutationFn: async () => {
      return activityApi.approveSubmission(cycleId, reportId, phaseName);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity-states', cycleId, reportId, phaseName] });
      toast.success('Submission approved');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to approve submission');
    }
  });

  // Reject submission mutation
  const rejectSubmissionMutation = useMutation({
    mutationFn: async (reason: string) => {
      return activityApi.rejectSubmission(cycleId, reportId, phaseName, reason);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity-states', cycleId, reportId, phaseName] });
      toast.success('Submission rejected');
      setShowRejectDialog(false);
      setRejectReason('');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to reject submission');
    }
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Error loading activity states
      </Alert>
    );
  }

  const activities = phaseData?.activities || {};
  const progress = phaseData?.phase_progress || 0;
  const canStartPhase = phaseData?.can_start_phase;
  const canCompletePhase = phaseData?.can_complete_phase;
  const nextActivity = phaseData?.next_activity;

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">
            {phaseName} Activities
          </Typography>
          
          {showControls && canManuallyControl && (
            <Box display="flex" gap={1}>
              {canStartPhase && (
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<PlayArrow />}
                  onClick={() => startPhaseMutation.mutate()}
                  disabled={startPhaseMutation.isPending}
                >
                  Start Phase
                </Button>
              )}
              
              {canCompletePhase && (
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<CheckCircle />}
                  onClick={() => completePhaseMutation.mutate()}
                  disabled={completePhaseMutation.isPending}
                >
                  Complete Phase
                </Button>
              )}
            </Box>
          )}
        </Box>

        {/* Overall Progress */}
        <Box mb={3}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" color="text.secondary">
              Overall Progress
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {progress}%
            </Typography>
          </Box>
          <LinearProgress variant="determinate" value={progress} />
        </Box>

        {/* Next Activity Hint */}
        {nextActivity && (
          <Alert severity="info" icon={<Info />} sx={{ mb: 2 }}>
            Next: {nextActivity}
          </Alert>
        )}

        {/* Activities List */}
        <Box display="flex" flexDirection="column" gap={2}>
          {Object.entries(activities).map(([name, activity]: [string, Activity]) => (
            <Box
              key={name}
              sx={{
                p: 2,
                border: 1,
                borderColor: 'divider',
                borderRadius: 1,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                '&:hover': {
                  backgroundColor: 'action.hover'
                }
              }}
            >
              <Box display="flex" alignItems="center" gap={2}>
                {getStateIcon(activity.state)}
                <Box>
                  <Typography variant="body1">{name}</Typography>
                  {activity.last_updated && (
                    <Typography variant="caption" color="text.secondary">
                      Updated: {new Date(activity.last_updated).toLocaleString()}
                      {activity.updated_by && ` by ${activity.updated_by}`}
                    </Typography>
                  )}
                </Box>
              </Box>

              <Box display="flex" alignItems="center" gap={1}>
                <Chip
                  label={activity.state}
                  color={getStateColor(activity.state)}
                  size="small"
                />
                
                {showControls && canManuallyControl && (
                  <>
                    {activity.can_start && activity.state === 'Not Started' && (
                      <Tooltip title="Start Activity">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => updateStateMutation.mutate({
                            activity,
                            newState: 'In Progress'
                          })}
                          disabled={updateStateMutation.isPending}
                        >
                          <PlayArrow />
                        </IconButton>
                      </Tooltip>
                    )}
                    
                    {activity.can_complete && activity.state === 'In Progress' && (
                      <Tooltip title="Complete Activity">
                        <IconButton
                          size="small"
                          color="success"
                          onClick={() => updateStateMutation.mutate({
                            activity,
                            newState: 'Completed'
                          })}
                          disabled={updateStateMutation.isPending}
                        >
                          <CheckCircle />
                        </IconButton>
                      </Tooltip>
                    )}
                  </>
                )}
              </Box>
            </Box>
          ))}
        </Box>

        {/* Action Buttons */}
        {showControls && (
          <Box mt={3} display="flex" gap={2} justifyContent="flex-end">
            {canManuallyControl && activities['Tester Review']?.state === 'In Progress' && (
              <Button
                variant="outlined"
                startIcon={<Send />}
                onClick={() => submitForReviewMutation.mutate()}
                disabled={submitForReviewMutation.isPending}
              >
                Submit for Review
              </Button>
            )}
            
            {canApprove && activities['Report Owner Approval']?.state === 'In Progress' && (
              <>
                <Button
                  variant="contained"
                  color="success"
                  onClick={() => approveSubmissionMutation.mutate()}
                  disabled={approveSubmissionMutation.isPending}
                >
                  Approve
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  onClick={() => setShowRejectDialog(true)}
                  disabled={rejectSubmissionMutation.isPending}
                >
                  Reject
                </Button>
              </>
            )}
          </Box>
        )}

        {/* Reject Dialog */}
        <Dialog open={showRejectDialog} onClose={() => setShowRejectDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Reject Submission</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Rejection Reason"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Please provide a reason for rejection..."
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowRejectDialog(false)}>Cancel</Button>
            <Button
              color="error"
              variant="contained"
              onClick={() => rejectSubmissionMutation.mutate(rejectReason)}
              disabled={!rejectReason.trim() || rejectSubmissionMutation.isPending}
            >
              Reject
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default ActivityStateManager;