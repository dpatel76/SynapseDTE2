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
  Autorenew as AutorenewOutlined,
  HourglassEmpty,
  Refresh as RefreshIcon
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
  if (name.includes('generate') || name.includes('create')) return <AutorenewOutlined />;
  if (name.includes('assign')) return <PersonIcon />;
  
  // Default task icon
  return <TaskIcon />;
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return { bg: '#e8f5e9', color: '#2e7d32', border: '#4caf50' };
    case 'active':
      return { bg: '#e3f2fd', color: '#1565c0', border: '#2196f3' };
    case 'blocked':
      return { bg: '#ffebee', color: '#c62828', border: '#f44336' };
    case 'skipped':
      return { bg: '#fff3e0', color: '#e65100', border: '#ff9800' };
    default:
      return { bg: '#f5f5f5', color: '#616161', border: '#bdbdbd' };
  }
};

const formatStatusText = (status: string): string => {
  switch (status) {
    case 'pending':
      return 'Not Started';
    case 'active':
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

export const DynamicActivityCardsEnhanced: React.FC<DynamicActivityCardsProps> = ({
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

  // Reset mutation
  const resetMutation = useMutation({
    mutationFn: async (activityId: string) => {
      const response = await apiClient.post(
        `/activity-states/activities/${activityId}/reset`,
        null,
        {
          params: { cycle_id: cycleId, report_id: reportId, phase_name: phaseName }
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      showToast('success', data.message || 'Activities reset successfully');
      queryClient.invalidateQueries({ 
        queryKey: ['phaseStatus', phaseName, cycleId, reportId] 
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
      resetMutation.mutate(resetDialog.activity.activity_id);
    }
  };

  const handleActivityAction = (activity: ActivityStatus, action: string) => {
    if (action === 'reset' && activity.status === 'completed') {
      handleResetClick(activity);
    } else if (onActivityAction) {
      onActivityAction(activity, action);
    }
  };

  // Filter activities if phase is completed
  const displayActivities = hideCompletedActivities && phaseStatus === 'completed' 
    ? activities.filter(a => a.status !== 'completed')
    : activities;

  const renderActivityCard = (activity: ActivityStatus, index: number) => {
    const canReset = activity.status === 'completed' && activity.can_reset !== false;
    const statusColors = getStatusColor(activity.status);
    const isFirst = index === 0;
    const isLast = index === activities.length - 1;
    
    return (
      <Box
        key={activity.activity_id}
        sx={{
          position: 'relative',
          flex: `1 1 ${100 / activities.length}%`,  // Distribute evenly based on number of activities
          minWidth: 180,  // Reduced minimum width
          height: 140,    // Fixed height for all cards
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

            {/* Activity Name - single line */}
            <Typography 
              variant="body2" 
              sx={{ 
                fontWeight: 'medium',
                mb: 1,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                fontSize: '0.875rem',
              }}
              title={activity.name}
            >
              {activity.name}
            </Typography>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
              {activity.status === 'pending' && activity.can_start && (
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<StartIcon />}
                  onClick={() => handleActivityAction(activity, 'start')}
                  sx={{ flex: 1 }}
                >
                  Start
                </Button>
              )}
              
              {activity.status === 'active' && activity.can_complete && (
                <Button
                  size="small"
                  variant="contained"
                  color="success"
                  startIcon={<CompleteIcon />}
                  onClick={() => handleActivityAction(activity, 'complete')}
                  sx={{ flex: 1 }}
                >
                  Complete
                </Button>
              )}
              
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
          flexWrap: { xs: 'wrap', lg: 'nowrap' },  // Only wrap on smaller screens
          gap: 2,
          width: '100%',
          overflowX: { xs: 'visible', lg: 'auto' },  // Allow horizontal scroll on large screens if needed
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