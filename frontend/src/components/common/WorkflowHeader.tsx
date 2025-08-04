import React, { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Button,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import {
  History,
  Refresh,
  CheckCircle,
  Warning,
  Schedule,
  PlayArrow,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useQuery } from '@tanstack/react-query';
import { activityApi, ActivityState } from '../../api/metrics';
import { ActivityStateBadge } from './ActivityStateBadge';

interface WorkflowHeaderProps {
  cycleId: string;
  reportId: string;
  phaseName: string;
  reportName: string;
  lobName?: string;
  onRefresh?: () => void;
  onViewHistory?: () => void;
  showActivities?: boolean;
}

const phaseOrder = [
  'Planning',
  'Data Profiling',
  'Scoping',
  'Sample Selection',
  'Data Provider ID',
  'Request Info',
  'Test Execution',
  'Observations',
  'Finalize Test Report'
];

export const WorkflowHeader: React.FC<WorkflowHeaderProps> = ({
  cycleId,
  reportId,
  phaseName,
  reportName,
  lobName,
  onRefresh,
  onViewHistory,
  showActivities = true
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update time every minute
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  // Fetch activity states
  const { data: activityStates, isLoading, refetch } = useQuery({
    queryKey: ['activity-states', cycleId, reportId, phaseName],
    queryFn: async () => {
      try {
        const response = await activityApi.getActivityStates(cycleId, reportId, phaseName);
        return response.data;
      } catch (error) {
        console.error('Error fetching activity states:', error);
        return [];
      }
    },
    enabled: showActivities,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const handleRefresh = () => {
    refetch();
    if (onRefresh) onRefresh();
  };

  const getPhaseStatus = (activities: ActivityState[]) => {
    if (!activities || activities.length === 0) return 'Not Started';
    
    const allCompleted = activities.every(a => a.state === 'Completed');
    const anyInProgress = activities.some(a => a.state === 'In Progress');
    const anyRevisionRequested = activities.some(a => a.state === 'Revision Requested');
    
    if (allCompleted) return 'Completed';
    if (anyRevisionRequested) return 'Revision Requested';
    if (anyInProgress) return 'In Progress';
    return 'Not Started';
  };

  const getPhaseIcon = (status: string) => {
    switch (status) {
      case 'Completed': return <CheckCircle color="success" />;
      case 'In Progress': return <Schedule color="primary" />;
      case 'Revision Requested': return <Warning color="warning" />;
      default: return <PlayArrow color="action" />;
    }
  };

  const phaseStatus = getPhaseStatus(activityStates || []);
  const currentPhaseIndex = phaseOrder.indexOf(phaseName);

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      {/* Header Section */}
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
        <Box>
          <Typography variant="h5" gutterBottom>
            {phaseName}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {reportName} {lobName && `• ${lobName}`}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Last updated: {format(currentTime, 'MMM dd, yyyy HH:mm')}
          </Typography>
        </Box>
        
        <Box display="flex" gap={1} alignItems="center">
          <Chip
            icon={getPhaseIcon(phaseStatus)}
            label={phaseStatus}
            color={phaseStatus === 'Completed' ? 'success' : 
                   phaseStatus === 'In Progress' ? 'primary' : 
                   phaseStatus === 'Revision Requested' ? 'warning' : 'default'}
          />
          
          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh} size="small">
              <Refresh />
            </IconButton>
          </Tooltip>
          
          {onViewHistory && (
            <Tooltip title="View History">
              <IconButton onClick={onViewHistory} size="small">
                <History />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {/* Phase Progress Stepper */}
      <Box sx={{ mb: 3 }}>
        <Stepper activeStep={currentPhaseIndex} orientation="horizontal">
          {phaseOrder.map((phase, index) => (
            <Step key={phase} completed={index < currentPhaseIndex}>
              <StepLabel
                optional={
                  index === currentPhaseIndex && (
                    <Typography variant="caption" color="primary">
                      Current Phase
                    </Typography>
                  )
                }
              >
                {phase}
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Box>

      {/* Activity States Section */}
      {showActivities && (
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Phase Activities
          </Typography>
          
          {isLoading ? (
            <Box display="flex" alignItems="center" gap={1}>
              <CircularProgress size={16} />
              <Typography variant="caption" color="text.secondary">
                Loading activities...
              </Typography>
            </Box>
          ) : activityStates && activityStates.length > 0 ? (
            <Box display="flex" flexWrap="wrap" gap={1}>
              {activityStates.map((activity, index) => (
                <Box key={index} display="flex" alignItems="center" gap={0.5}>
                  <Typography variant="caption" color="text.secondary">
                    {activity.activity_name}:
                  </Typography>
                  <ActivityStateBadge
                    state={activity.state}
                    size="small"
                  />
                </Box>
              ))}
            </Box>
          ) : (
            <Alert severity="info" sx={{ py: 0.5 }}>
              No activities defined for this phase
            </Alert>
          )}
        </Box>
      )}
    </Paper>
  );
};

export default WorkflowHeader;