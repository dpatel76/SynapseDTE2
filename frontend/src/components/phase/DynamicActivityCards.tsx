import { useState } from 'react';
import { 
  Card, CardContent, Box, Typography, Chip, Button, IconButton, 
  Tooltip, CircularProgress, Dialog, DialogTitle, DialogContent, 
  DialogActions, List, ListItem, ListItemText, LinearProgress,
  Avatar, Fade, alpha
} from '@mui/material';
import { 
  RestartAlt as ResetIcon, 
  PlayArrow as StartIcon,
  CheckCircle as CompleteIcon,
  Warning as WarningIcon,
  AccessTime as ClockIcon,
  PersonOutline as PersonIcon,
  FlagOutlined as StartActivityIcon,
  TaskAlt as TaskIcon,
  RateReview as ReviewIcon,
  Approval as ApprovalIcon,
  CheckCircleOutline as CompleteActivityIcon,
  Autorenew as AutorenewIcon,
  HourglassEmpty,
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  Link as LinkIcon,
  Shield as ShieldIcon,
  Psychology as PsychologyIcon,
  Replay as ReplayIcon
} from '@mui/icons-material';
import { ActivityStatus } from '../../hooks/useUnifiedStatus';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../api/client';
import { useNotifications } from '../../contexts/NotificationContext';

interface DynamicActivityCardsProps {
  activities: ActivityStatus[];
  cycleId: number;
  reportId: number;
  phaseName: string;
  phaseStatus?: string;
  overallCompletion?: number;
  onActivityAction?: (activity: ActivityStatus, action: string) => void;
  variant?: 'stepper' | 'cards' | 'timeline';
  hideCompletedActivities?: boolean;
}

// Activity type to icon mapping
const getActivityIcon = (activityName: string, status: string) => {
  const name = activityName.toLowerCase();
  
  // Status-based icons
  if (status === 'completed') return <CompleteIcon />;
  if (status === 'active') return <HourglassEmpty />;
  if (status === 'blocked') return <WarningIcon />;
  
  // Activity type based icons
  if (name.includes('start')) return <StartActivityIcon />;
  if (name.includes('complete')) return <CompleteActivityIcon />;
  if (name.includes('review')) return <ReviewIcon />;
  if (name.includes('approval') || name.includes('approve')) return <ApprovalIcon />;
  if (name.includes('generate') || name.includes('create')) return <AutorenewIcon />;
  if (name.includes('assign')) return <PersonIcon />;
  if (name.includes('data source')) return <StorageIcon />;
  if (name.includes('map')) return <LinkIcon />;
  if (name.includes('classify')) return <ShieldIcon />;
  
  // Default task icon
  return <TaskIcon />;
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return { bg: '#e8f5e9', color: '#2e7d32', border: '#4caf50' };
    case 'active':
    case 'in_progress':
      return { bg: '#e3f2fd', color: '#1565c0', border: '#2196f3' };
    case 'blocked':
      return { bg: '#ffebee', color: '#c62828', border: '#f44336' };
    case 'skipped':
      return { bg: '#fff3e0', color: '#e65100', border: '#ff9800' };
    case 'not_started':
    case 'pending':
      return { bg: '#f5f5f5', color: '#616161', border: '#bdbdbd' };
    default:
      return { bg: '#f5f5f5', color: '#616161', border: '#bdbdbd' };
  }
};

const formatStatusText = (status: string): string => {
  switch (status) {
    case 'not_started':
    case 'pending':
      return 'Not Started';
    case 'active':
    case 'in_progress':
      return 'In Progress';
    case 'completed':
      return 'Completed';
    case 'blocked':
      return 'Blocked';
    case 'skipped':
      return 'Skipped';
    default:
      return status;
  }
};

export const DynamicActivityCards: React.FC<DynamicActivityCardsProps> = ({
  activities,
  cycleId,
  reportId,
  phaseName,
  phaseStatus = 'not_started',
  overallCompletion = 0,
  onActivityAction,
  variant = 'cards',
  hideCompletedActivities = false
}) => {
  const queryClient = useQueryClient();
  const { showToast } = useNotifications();
  const [resetDialog, setResetDialog] = useState<{
    open: boolean;
    activity: ActivityStatus | null;
    affectedActivities: string[];
  }>({ open: false, activity: null, affectedActivities: [] });
  
  // Track which activities are currently being processed
  const [processingActivities, setProcessingActivities] = useState<Set<string>>(new Set());

  // Reset mutation
  const resetMutation = useMutation({
    mutationFn: async (activityName: string) => {
      const response = await apiClient.post(
        `/activities/${encodeURIComponent(activityName)}/reset`,
        null,
        {
          params: { cycle_id: cycleId, report_id: reportId, phase_name: phaseName }
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      showToast('success', data.message || 'Activities reset successfully');
      // Invalidate all related queries to ensure fresh data
      queryClient.invalidateQueries({ 
        queryKey: ['phaseStatus', phaseName, cycleId, reportId] 
      });
      queryClient.invalidateQueries({ 
        queryKey: ['allPhasesStatus', cycleId, reportId] 
      });
      queryClient.invalidateQueries({ 
        queryKey: ['activityStatus'] 
      });
      setResetDialog({ open: false, activity: null, affectedActivities: [] });
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Failed to reset activity');
    }
  });

  const handleResetClick = (activity: ActivityStatus) => {
    const activityIndex = activities.findIndex(a => a.activity_id === activity.activity_id);
    const affectedActivities = activities
      .slice(activityIndex + 1)
      .filter(a => a.status === 'completed')
      .map(a => a.name);
    
    setResetDialog({
      open: true,
      activity,
      affectedActivities
    });
  };

  const handleResetConfirm = () => {
    if (resetDialog.activity) {
      resetMutation.mutate(resetDialog.activity.name);
    }
  };

  const handleActivityAction = async (activity: ActivityStatus, action: string) => {
    // Prevent double-clicks
    if (processingActivities.has(activity.activity_id)) {
      console.log('Activity already being processed, ignoring click');
      return;
    }
    
    if (action === 'reset' && activity.status === 'completed') {
      handleResetClick(activity);
    } else if (onActivityAction) {
      try {
        // Mark activity as processing
        setProcessingActivities(prev => new Set(prev).add(activity.activity_id));
        
        // Call the parent's handler
        await onActivityAction(activity, action);
        
        // Always invalidate queries to ensure UI refreshes
        queryClient.invalidateQueries({ 
          queryKey: ['phaseStatus', phaseName, cycleId, reportId] 
        });
        queryClient.invalidateQueries({ 
          queryKey: ['activityStatus'] 
        });
        queryClient.invalidateQueries({ 
          queryKey: ['unifiedStatus'] 
        });
        
        // Add a small delay to ensure backend has processed the change
        await new Promise(resolve => setTimeout(resolve, 200));
        
        // Force refetch all related queries
        queryClient.refetchQueries({ 
          queryKey: ['phaseStatus', phaseName, cycleId, reportId] 
        });
      } finally {
        // Remove from processing set
        setProcessingActivities(prev => {
          const newSet = new Set(prev);
          newSet.delete(activity.activity_id);
          return newSet;
        });
      }
    }
  };

  // Filter activities if phase is completed
  const displayActivities = hideCompletedActivities && phaseStatus === 'completed' 
    ? activities.filter(a => a.status !== 'completed')
    : activities;
  
  // Debug logging for planning phase
  if (phaseName === 'Planning') {
    console.log('Planning Phase Activities:', {
      totalActivities: activities.length,
      activities: activities.map(a => ({
        id: a.activity_id,
        name: a.name,
        status: a.status,
        can_start: a.can_start,
        can_complete: a.can_complete,
        type: a.metadata?.activity_type
      })),
      phaseStatus
    });
  }

  const renderActivityCard = (activity: ActivityStatus, index: number) => {
    const canReset = activity.status === 'completed' && activity.can_reset !== false;
    const statusColors = getStatusColor(activity.status);
    const isFirst = index === 0;
    const isLast = index === activities.length - 1;
    
    // Debug logging
    if (activity.name.includes('LLM') || activity.name.includes('Recommendations')) {
      console.log(`${activity.name} Activity:`, {
        activity_id: activity.activity_id,
        name: activity.name,
        status: activity.status,
        can_start: activity.can_start,
        can_complete: activity.can_complete,
        metadata: activity.metadata,
        isLLMActivity: activity.name === 'Generate LLM Recommendations',
        shouldShowRegenerate: activity.status === 'active' && activity.name === 'Generate LLM Recommendations'
      });
    }
    
    return (
      <Box
        key={activity.activity_id}
        sx={{
          position: 'relative',
          flex: activities.length <= 6 ? '1 1 0' : '0 0 auto',  // Flex grow for fewer cards, fixed width for many
          width: activities.length > 6 ? (activities.length > 8 ? 220 : 250) : 'auto',  // Auto width when flex growing
          minWidth: activities.length > 8 ? 220 : 250,  // Increased min width for better text display
          maxWidth: activities.length <= 6 ? 320 : (activities.length > 8 ? 220 : 250),  // Max width when growing
          height: 150,    // Slightly increased height for better text display
        }}
      >
        {/* Connection line - hidden on smaller screens to avoid visual issues when wrapping */}
        {!isLast && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '100%',
              width: '16px', // 2rem gap = 16px
              height: '2px',
              bgcolor: activity.status === 'completed' ? 'success.main' : 'grey.300',
              zIndex: 0,
              transform: 'translateY(-50%)',
              display: { xs: 'none', md: 'block' }, // Hide on small screens
            }}
          />
        )}
        
        <Card 
          sx={{ 
            position: 'relative',
            zIndex: 1,
            height: '100%',
            border: `2px solid ${statusColors.border}`,
            bgcolor: alpha(statusColors.bg, 0.5),
            transition: 'all 0.3s ease',
            overflow: 'visible', // Ensure borders are not clipped
            '&:hover': {
              transform: 'translateY(-2px)', // Reduced from -4px
              boxShadow: 4,
              bgcolor: statusColors.bg,
              borderColor: statusColors.border, // Ensure border color stays
            }
          }}
        >
          <CardContent sx={{ 
            p: 2, 
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            '&:last-child': { pb: 2 } 
          }}>
            {/* Icon and Status */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Avatar
                sx={{
                  width: 36,
                  height: 36,
                  bgcolor: statusColors.bg,
                  color: statusColors.color,
                  border: `2px solid ${statusColors.border}`,
                }}
              >
                {getActivityIcon(activity.name, activity.status)}
              </Avatar>
              
              {/* Only show status badge for non-active statuses */}
              {activity.status !== 'active' && (
                <Chip
                  label={formatStatusText(activity.status)}
                  size="small"
                  sx={{
                    bgcolor: statusColors.bg,
                    color: statusColors.color,
                    fontWeight: 'medium',
                    fontSize: '0.75rem',
                  }}
                />
              )}
            </Box>

            {/* Activity Name - allow wrapping for long names */}
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, mb: 1, minHeight: '2.5rem' }}>
              <Typography 
                variant="body2" 
                sx={{ 
                  fontWeight: 'medium',
                  fontSize: '0.875rem',
                  lineHeight: 1.3,
                  display: '-webkit-box',
                  WebkitLineClamp: 2,  // Limit to 2 lines
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  wordBreak: 'break-word',
                }}
                title={activity.name}
              >
                {activity.name}
              </Typography>
              {activity.metadata?.can_skip && (
                <Chip
                  label="Optional"
                  size="small"
                  sx={{
                    height: 18,
                    fontSize: '0.625rem',
                    bgcolor: '#e1f5fe',
                    color: '#0277bd',
                    border: '1px solid #81d4fa',
                    flexShrink: 0,
                  }}
                />
              )}
            </Box>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
              {(() => {
                console.log(`Rendering buttons for ${activity.name}:`, {
                  status: activity.status,
                  can_start: activity.can_start,
                  can_complete: activity.can_complete,
                  metadata: activity.metadata
                });
                // Special case for LLM/generation activities and execution activities - show both regenerate and complete buttons when active
                if ((activity.status === 'active' || activity.status === 'in_progress') && activity.can_complete && (
                  activity.name === 'Generate LLM Recommendations' || 
                  activity.name.toLowerCase().includes('llm recommendation') ||
                  activity.name === 'Generate Data Profile' ||
                  activity.name.toLowerCase().includes('generate') ||
                  activity.name === 'Execute Data Profiling' ||
                  activity.name === 'Execute Profiling' ||
                  activity.name.toLowerCase().includes('execute')
                )) {
                  return (
                    <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', width: '100%' }}>
                      <Tooltip title={
                        activity.name.toLowerCase().includes('execute') ? "Re-run Execution" : "Regenerate AI-Generated Content"
                      }>
                        <IconButton
                          size="small"
                          onClick={async () => {
                            console.log(`${activity.name.toLowerCase().includes('execute') ? 'Re-run' : 'Regenerate'} clicked for ${activity.name}`);
                            await handleActivityAction(activity, 'regenerate');
                          }}
                          disabled={processingActivities.has(activity.activity_id)}
                          sx={{
                            color: 'primary.main',
                            border: '1px solid',
                            borderColor: 'primary.main',
                            '&:hover': {
                              bgcolor: 'primary.light',
                              borderColor: 'primary.dark',
                            }
                          }}
                        >
                          {processingActivities.has(activity.activity_id) ? <CircularProgress size={18} /> : 
                           activity.name.toLowerCase().includes('execute') ? <ReplayIcon fontSize="small" /> : <PsychologyIcon fontSize="small" />}
                        </IconButton>
                      </Tooltip>
                      <Button
                        size="small"
                        variant="contained"
                        color="success"
                        startIcon={processingActivities.has(activity.activity_id) ? <CircularProgress size={16} color="inherit" /> : <CompleteIcon />}
                        onClick={async () => {
                          console.log('Complete button clicked for:', activity.name, { status: activity.status });
                          await handleActivityAction(activity, 'complete');
                        }}
                        disabled={processingActivities.has(activity.activity_id)}
                        sx={{ flex: 1 }}
                      >
                        {processingActivities.has(activity.activity_id) ? 'Processing...' : 'Mark as Complete'}
                      </Button>
                    </Box>
                  );
                }
                
                // Regular button logic
                console.log('Button check for:', activity.name, {
                  status: activity.status,
                  can_start: activity.can_start,
                  statusCheck: (activity.status === 'pending' || activity.status === 'not_started'),
                  condition: ((activity.status === 'pending' || activity.status === 'not_started') && activity.can_start)
                });
                if ((activity.status === 'pending' || activity.status === 'not_started') && activity.can_start) {
                  return (
                    <Button
                      size="small"
                      variant="contained"
                      color="primary"
                      startIcon={processingActivities.has(activity.activity_id) ? <CircularProgress size={16} color="inherit" /> : <StartIcon />}
                      onClick={async () => {
                        console.log('Start button clicked for:', activity.name, { status: activity.status });
                        await handleActivityAction(activity, 'start');
                      }}
                      disabled={processingActivities.has(activity.activity_id)}
                      sx={{ flex: 1 }}
                    >
                      {processingActivities.has(activity.activity_id) ? 'Processing...' : (activity.metadata?.button_text || (activity.name.toLowerCase().includes('start') ? 'Start Phase' : 'Start'))}
                    </Button>
                  );
                } else if ((activity.status === 'pending' || activity.status === 'not_started') && activity.can_complete) {
                  // Special case for phase_complete activities that can be completed directly from pending
                  return (
                    <Button
                      size="small"
                      variant="contained"
                      color="success"
                      startIcon={processingActivities.has(activity.activity_id) ? <CircularProgress size={16} color="inherit" /> : <CompleteIcon />}
                      onClick={async () => {
                        console.log('Complete button clicked for phase_complete activity:', activity.name, { status: activity.status });
                        await handleActivityAction(activity, 'complete');
                      }}
                      disabled={processingActivities.has(activity.activity_id)}
                      sx={{ flex: 1 }}
                    >
                      {processingActivities.has(activity.activity_id) ? 'Processing...' : (activity.name.toLowerCase().includes('phase') ? 'Complete Phase' : 'Mark as Complete')}
                    </Button>
                  );
                } else if ((activity.status === 'active' || activity.status === 'in_progress') && activity.can_complete) {
                  // Don't show complete button for START activities in active state (they should auto-complete)
                  if (activity.metadata?.activity_type === 'START') {
                    return (
                      <Typography variant="caption" color="text.secondary">
                        Processing...
                      </Typography>
                    );
                  }
                  return (
                    <Button
                      size="small"
                      variant="contained"
                      color="success"
                      startIcon={processingActivities.has(activity.activity_id) ? <CircularProgress size={16} color="inherit" /> : <CompleteIcon />}
                      onClick={async () => {
                        console.log('Complete button clicked for:', activity.name, { status: activity.status });
                        await handleActivityAction(activity, 'complete');
                      }}
                      disabled={processingActivities.has(activity.activity_id)}
                      sx={{ flex: 1 }}
                    >
                      {processingActivities.has(activity.activity_id) ? 'Processing...' : (activity.name.toLowerCase().includes('phase') ? 'Complete Phase' : 'Mark as Complete')}
                    </Button>
                  );
                } else if (activity.status === 'active' && !activity.can_complete) {
                  // Show disabled button for active activities that can't be completed yet
                  return (
                    <Button
                      size="small"
                      variant="outlined"
                      disabled
                      fullWidth
                      sx={{ flex: 1 }}
                    >
                      {activity.blocking_reason ? 'Waiting...' : 'In Progress'}
                    </Button>
                  );
                }
                // Debug log for unhandled cases
                console.warn('No button rendered for activity:', {
                  name: activity.name,
                  status: activity.status,
                  can_start: activity.can_start,
                  can_complete: activity.can_complete,
                  blocking_reason: activity.blocking_reason
                });
                return null;
              })()}
              
              {/* Removed instructions display - now showing disabled button instead */}
              
              {activity.status === 'completed' && canReset && (
                <Tooltip title="Reset activity">
                  <IconButton
                    size="small"
                    onClick={() => handleResetClick(activity)}
                    sx={{
                      color: 'warning.main',
                      border: '1px solid',
                      borderColor: 'warning.main',
                      '&:hover': {
                        bgcolor: 'warning.light',
                      }
                    }}
                  >
                    <RefreshIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
              
              {activity.status === 'blocked' && activity.blocking_reason && (
                <Tooltip title={activity.blocking_reason}>
                  <IconButton size="small" color="error">
                    <WarningIcon />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  };

  return (
    <Box>
      {/* Phase Progress Bar - Separate Row */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="h6" sx={{ fontWeight: 'medium' }}>
            Phase Progress
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {overallCompletion}% Complete
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={overallCompletion} 
          sx={{ 
            height: 8, 
            borderRadius: 4,
            bgcolor: 'grey.200',
            '& .MuiLinearProgress-bar': {
              borderRadius: 4,
              bgcolor: overallCompletion === 100 ? 'success.main' : 'primary.main',
            }
          }}
        />
      </Box>

      {/* Activities Row */}
      <Box 
        sx={{ 
          display: 'flex',
          flexWrap: 'nowrap',  // Prevent wrapping to keep all cards in one row
          gap: activities.length > 8 ? 1 : 1.5,  // Smaller gap when many activities
          width: '100%',
          overflowX: activities.length > 6 ? 'auto' : 'hidden',  // Only scroll when needed
          overflowY: 'hidden',
          pb: activities.length > 6 ? 1 : 0,  // Add padding for scrollbar only when scrolling
          // Ensure full width usage
          justifyContent: activities.length <= 6 ? 'stretch' : 'flex-start',
          // Custom scrollbar styling
          '&::-webkit-scrollbar': {
            height: 6,
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: 'rgba(0,0,0,0.05)',
            borderRadius: 3,
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(0,0,0,0.2)',
            borderRadius: 3,
            '&:hover': {
              backgroundColor: 'rgba(0,0,0,0.3)',
            },
          },
        }}
      >
        {displayActivities.map((activity, index) => renderActivityCard(activity, index))}
      </Box>

      {/* Reset Confirmation Dialog */}
      <Dialog
        open={resetDialog.open}
        onClose={() => setResetDialog({ open: false, activity: null, affectedActivities: [] })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Reset Activity Status?
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to reset "{resetDialog.activity?.name}"?
          </Typography>
          
          {resetDialog.affectedActivities.length > 0 && (
            <>
              <Typography variant="body2" color="warning.main" sx={{ mt: 2, mb: 1 }}>
                The following activities will also be reset:
              </Typography>
              <List dense>
                {resetDialog.affectedActivities.map((name) => (
                  <ListItem key={name}>
                    <ListItemText 
                      primary={name}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setResetDialog({ open: false, activity: null, affectedActivities: [] })}
            disabled={resetMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleResetConfirm}
            color="warning"
            variant="contained"
            disabled={resetMutation.isPending}
            startIcon={resetMutation.isPending ? <CircularProgress size={16} /> : <ResetIcon />}
          >
            Reset
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};