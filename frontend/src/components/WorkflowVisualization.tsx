import React, { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Chip,
  LinearProgress,
  CircularProgress,
  Alert,
  Button,
  Tooltip,
  IconButton,
  Collapse,
  Card,
  CardContent
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as PendingIcon,
  Error as ErrorIcon,
  PlayArrow as PlayIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Timer as TimerIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import Grid from '@mui/material/Grid';
import { format, formatDuration, intervalToDuration } from 'date-fns';

interface WorkflowPhase {
  order: number;
  name: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  startedAt?: string;
  completedAt?: string;
  duration?: number;
  activities?: ActivityDetail[];
  error?: string;
}

interface ActivityDetail {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  duration?: number;
  message?: string;
}

interface WorkflowStatus {
  workflowId: string;
  executionId?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  currentPhase?: string;
  completedPhases: string[];
  startedAt?: string;
  completedAt?: string;
  durationSeconds?: number;
  phases: WorkflowPhase[];
}

interface WorkflowVisualizationProps {
  cycleId: number;
  reportId?: number;
  workflowId?: string;
  onRefresh?: () => void;
  showMetrics?: boolean;
}

const WORKFLOW_PHASES = [
  'Planning',
  'Scoping',
  'Sample Selection',
  'Data Owner Identification',
  'Request for Information',
  'Test Execution',
  'Observation Management',
  'Finalize Test Report'
];

const WorkflowVisualization: React.FC<WorkflowVisualizationProps> = ({
  cycleId,
  reportId,
  workflowId,
  onRefresh,
  showMetrics = true
}) => {
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (workflowId) {
      fetchWorkflowStatus();
      // Poll for updates every 5 seconds if workflow is running
      const interval = setInterval(() => {
        if (workflowStatus?.status === 'running') {
          fetchWorkflowStatus();
        }
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [workflowId]);

  const fetchWorkflowStatus = async () => {
    try {
      const response = await fetch(`/api/v1/workflow/status/${workflowId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        // Transform data to match our interface
        const phases: WorkflowPhase[] = WORKFLOW_PHASES.map((phaseName, index) => {
          const isCompleted = data.completed_phases?.includes(phaseName);
          const isCurrent = data.current_phase === phaseName;
          const isSkipped = data.skip_phases?.includes(phaseName) || false;
          
          let status: WorkflowPhase['status'] = 'not_started';
          if (isCompleted) status = 'completed';
          else if (isCurrent) status = 'in_progress';
          else if (isSkipped) status = 'skipped';
          else if (data.status === 'failed' && !isCompleted) status = 'failed';
          
          // Get phase timing from phase_timings if available
          const phaseTiming = data.phase_timings?.[phaseName];
          
          return {
            order: index + 1,
            name: phaseName,
            status,
            startedAt: phaseTiming?.started_at,
            completedAt: phaseTiming?.completed_at,
            duration: phaseTiming?.duration_seconds,
            activities: phaseTiming?.activities || [],
            error: phaseTiming?.error
          };
        });
        
        setWorkflowStatus({
          workflowId: data.workflow_id,
          executionId: data.execution_id,
          status: data.status,
          currentPhase: data.current_phase,
          completedPhases: data.completed_phases || [],
          startedAt: data.started_at,
          completedAt: data.completed_at,
          durationSeconds: data.duration_seconds,
          phases
        });
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to fetch workflow status');
      }
    } catch (err: any) {
      setError(err.message || 'Error fetching workflow status');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchWorkflowStatus();
    if (onRefresh) onRefresh();
  };

  const togglePhaseExpanded = (phaseName: string) => {
    const newExpanded = new Set(expandedPhases);
    if (newExpanded.has(phaseName)) {
      newExpanded.delete(phaseName);
    } else {
      newExpanded.add(phaseName);
    }
    setExpandedPhases(newExpanded);
  };

  const getPhaseIcon = (status: WorkflowPhase['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'in_progress':
        return <CircularProgress size={20} />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'skipped':
        return <PendingIcon color="disabled" />;
      default:
        return <PendingIcon />;
    }
  };

  const getStatusColor = (status: WorkflowPhase['status']) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'failed':
        return 'error';
      case 'skipped':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatDurationTime = (seconds?: number) => {
    if (!seconds) return '-';
    const duration = intervalToDuration({ start: 0, end: seconds * 1000 });
    return formatDuration(duration, { format: ['hours', 'minutes'] });
  };

  const calculateProgress = () => {
    if (!workflowStatus) return 0;
    return (workflowStatus.completedPhases.length / WORKFLOW_PHASES.length) * 100;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!workflowStatus) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        No workflow found for this cycle
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Workflow Progress</Typography>
          <Box>
            <Tooltip title="Refresh">
              <IconButton onClick={handleRefresh} disabled={refreshing}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        {/* Overall Progress */}
        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography variant="body2">
              Overall Progress: {workflowStatus.completedPhases.length} of {WORKFLOW_PHASES.length} phases
            </Typography>
            <Typography variant="body2">
              {Math.round(calculateProgress())}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={calculateProgress()}
            sx={{ height: 8, borderRadius: 1 }}
          />
        </Box>
        
        {/* Status Summary */}
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="body2" color="text.secondary">
              Status
            </Typography>
            <Chip
              label={workflowStatus.status.toUpperCase()}
              color={
                workflowStatus.status === 'completed' ? 'success' :
                workflowStatus.status === 'running' ? 'primary' :
                workflowStatus.status === 'failed' ? 'error' : 'default'
              }
              size="small"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="body2" color="text.secondary">
              Started
            </Typography>
            <Typography variant="body2">
              {workflowStatus.startedAt
                ? format(new Date(workflowStatus.startedAt), 'MMM dd, yyyy HH:mm')
                : '-'}
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <Typography variant="body2" color="text.secondary">
              Duration
            </Typography>
            <Typography variant="body2">
              {formatDurationTime(workflowStatus.durationSeconds)}
            </Typography>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Phase Stepper */}
      <Paper sx={{ p: 2 }}>
        <Stepper orientation="vertical">
          {workflowStatus.phases.map((phase, index) => (
            <Step key={phase.name} active={phase.status === 'in_progress'}>
              <StepLabel
                StepIconComponent={() => getPhaseIcon(phase.status)}
                optional={
                  phase.duration && (
                    <Typography variant="caption" color="text.secondary">
                      <TimerIcon sx={{ fontSize: 12, mr: 0.5 }} />
                      {formatDurationTime(phase.duration)}
                    </Typography>
                  )
                }
              >
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography>{phase.name}</Typography>
                  <Chip
                    label={phase.status.replace('_', ' ').toUpperCase()}
                    color={getStatusColor(phase.status)}
                    size="small"
                  />
                </Box>
              </StepLabel>
              <StepContent>
                {phase.activities && phase.activities.length > 0 && (
                  <Box>
                    <Button
                      size="small"
                      onClick={() => togglePhaseExpanded(phase.name)}
                      endIcon={
                        expandedPhases.has(phase.name) ? <ExpandLessIcon /> : <ExpandMoreIcon />
                      }
                    >
                      {expandedPhases.has(phase.name) ? 'Hide' : 'Show'} Activities
                    </Button>
                    <Collapse in={expandedPhases.has(phase.name)}>
                      <Box mt={1}>
                        {phase.activities.map((activity, idx) => (
                          <Box key={idx} display="flex" alignItems="center" gap={1} mb={1}>
                            {activity.status === 'completed' && (
                              <CheckCircleIcon fontSize="small" color="success" />
                            )}
                            {activity.status === 'running' && (
                              <CircularProgress size={16} />
                            )}
                            {activity.status === 'failed' && (
                              <ErrorIcon fontSize="small" color="error" />
                            )}
                            {activity.status === 'pending' && (
                              <PendingIcon fontSize="small" />
                            )}
                            <Typography variant="body2">{activity.name}</Typography>
                            {activity.duration && (
                              <Typography variant="caption" color="text.secondary">
                                ({formatDurationTime(activity.duration)})
                              </Typography>
                            )}
                          </Box>
                        ))}
                      </Box>
                    </Collapse>
                  </Box>
                )}
                {phase.error && (
                  <Alert severity="error" sx={{ mt: 1 }}>
                    {phase.error}
                  </Alert>
                )}
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>
      
      {/* Metrics Summary */}
      {showMetrics && workflowStatus.status === 'completed' && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <AssessmentIcon />
              <Typography variant="h6">Workflow Metrics</Typography>
            </Box>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Total Duration
                </Typography>
                <Typography variant="h6">
                  {formatDurationTime(workflowStatus.durationSeconds)}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Phases Completed
                </Typography>
                <Typography variant="h6">
                  {workflowStatus.completedPhases.length} / {WORKFLOW_PHASES.length}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Success Rate
                </Typography>
                <Typography variant="h6">
                  {workflowStatus.status === 'completed' ? '100%' : 'N/A'}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Workflow ID
                </Typography>
                <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                  {workflowStatus.workflowId}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default WorkflowVisualization;