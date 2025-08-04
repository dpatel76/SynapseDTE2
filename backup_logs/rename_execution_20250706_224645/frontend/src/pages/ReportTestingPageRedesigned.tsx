import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Breadcrumbs,
  Link,
  LinearProgress,
  Stack,
  Tooltip,
  Paper,
  Button,
  Grid,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  PlayArrow as PlayArrowIcon,
  PauseCircle as PauseCircleIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  Warning as WarningIcon,
  Assignment as AssignmentIcon,
  CalendarToday as CalendarIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import { workflowApi } from '../api/workflow';

interface PhaseCardData {
  phase_name: string;
  display_name: string;
  status: 'Not Started' | 'Past Due' | 'At Risk' | 'On Track' | 'Complete'; // This is now the status indicator
  state: 'Not Started' | 'In Progress' | 'Complete'; // This is the workflow state
  progress: number;
  planned_start_date?: string;
  planned_end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;
  is_overdue: boolean;
  is_at_risk: boolean;
  metrics?: {
    total_items?: number;
    completed_items?: number;
    pending_items?: number;
    success_rate?: number;
  };
  route_name: string;
}

const phaseRouteMapping: Record<string, string> = {
  'Planning': 'planning',
  'Data Profiling': 'data-profiling',
  'Scoping': 'scoping',
  'Sample Selection': 'sample-selection',
  'Data Owner ID': 'data-owner',
  'Data Provider ID': 'data-owner',  // Handle both variants
  'Request Info': 'request-info',
  'Testing': 'test-execution',
  'Test Execution': 'test-execution',  // Correct phase name
  'Observations': 'observation-management',
  'Finalize Testing Report': 'finalize-report',
  'Finalize Test Report': 'finalize-report'  // Handle both variants
};

const phaseDisplayNames: Record<string, string> = {
  'Planning': 'Planning & Analysis',
  'Data Profiling': 'Data Profiling',
  'Scoping': 'Scoping & Review',
  'Sample Selection': 'Sample Selection',
  'Data Owner ID': 'Data Owner Identification',
  'Data Provider ID': 'Data Owner Identification',
  'Request Info': 'Request for Information',
  'Testing': 'Test Execution',
  'Test Execution': 'Test Execution',  // Correct phase name
  'Observations': 'Observation Management',
  'Finalize Testing Report': 'Finalize Test Report',
  'Finalize Test Report': 'Finalize Test Report'  // Handle both variants
};

const phaseColors: Record<string, string> = {
  'Planning': '#1976d2',
  'Data Profiling': '#2e7d32',
  'Scoping': '#388e3c',
  'Sample Selection': '#7b1fa2',
  'Data Owner ID': '#f57c00',
  'Data Provider ID': '#f57c00',
  'Request Info': '#d32f2f',
  'Testing': '#0288d1',
  'Observations': '#5d4037',
  'Finalize Testing Report': '#9c27b0',
  'Finalize Test Report': '#9c27b0'
};

const ReportTestingPageRedesigned: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(true);

  // Fetch report details
  const { data: reportDetail, isLoading: reportLoading } = useQuery({
    queryKey: ['report-testing', cycleId, reportId],
    queryFn: async () => {
      const response = await apiClient.get(`/cycle-reports/${cycleId}/reports/${reportId}`);
      return response.data;
    },
    enabled: !!cycleId && !!reportId,
  });

  // Fetch workflow status
  const { data: workflowStatus, isLoading: workflowLoading } = useQuery({
    queryKey: ['workflow-status', cycleId, reportId],
    queryFn: async () => {
      const status = await workflowApi.getWorkflowStatus(
        parseInt(cycleId || '0'),
        parseInt(reportId || '0')
      );
      return status;
    },
    enabled: !!cycleId && !!reportId,
  });

  useEffect(() => {
    setLoading(reportLoading || workflowLoading);
  }, [reportLoading, workflowLoading]);

  const getPhaseIcon = (phaseName: string, status: string) => {
    if (status === 'Complete') return <CheckCircleIcon color="success" />;
    if (status === 'In Progress') return <PlayArrowIcon color="warning" />;
    return <PauseCircleIcon color="disabled" />;
  };

  const getPhaseColor = (phase: PhaseCardData): 'error' | 'warning' | 'success' | 'primary' | 'secondary' | 'info' | 'inherit' => {
    if (phase.is_overdue) return 'error';
    if (phase.is_at_risk) return 'warning';
    if (phase.state === 'Complete') return 'success';
    if (phase.state === 'In Progress') return 'primary';
    return 'inherit';
  };

  const getStateChipColor = (state: string): 'error' | 'warning' | 'success' | 'primary' | 'secondary' | 'info' | 'default' => {
    if (state === 'Complete') return 'success';
    if (state === 'In Progress') return 'primary';
    return 'default';
  };

  const getStatusChipColor = (status: string): 'error' | 'warning' | 'success' | 'primary' | 'secondary' | 'info' | 'default' => {
    if (status === 'Past Due') return 'error';
    if (status === 'At Risk') return 'warning';
    if (status === 'On Track') return 'success';
    if (status === 'Complete') return 'success';
    if (status === 'Not Started') return 'default';
    return 'default';
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString();
  };

  const calculateDaysRemaining = (endDate?: string) => {
    if (!endDate) return null;
    const end = new Date(endDate);
    const now = new Date();
    const diffTime = end.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const calculateElapsedDuration = (startDate?: string, endDate?: string) => {
    if (!startDate) return null;
    
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : new Date();
    const diffTime = end.getTime() - start.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "1 day";
    return `${diffDays} days`;
  };

  const formatDateCompact = (dateString?: string) => {
    if (!dateString) return "Not Started";
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  if (loading) {
    return (
      <Container maxWidth={false} sx={{ py: 3 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  const getPhaseStatus = (phase: any): 'Not Started' | 'Past Due' | 'At Risk' | 'On Track' | 'Complete' => {
    // Calculate status based on dates and current state
    const now = new Date();
    const plannedEnd = phase.planned_end_date ? new Date(phase.planned_end_date) : null;
    const actualStart = phase.actual_start_date ? new Date(phase.actual_start_date) : null;
    
    // If phase is complete, return 'Complete' status (no badge will be shown)
    if (phase.state === 'Complete') return 'Complete';
    
    // If phase hasn't started yet, return "Not Started"
    if (phase.state === 'Not Started') {
      return 'Not Started';
    }
    
    // If phase is in progress, check against planned end date
    if (phase.state === 'In Progress' && plannedEnd) {
      const daysUntilDue = Math.ceil((plannedEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      if (daysUntilDue < 0) return 'Past Due';
      if (daysUntilDue <= 2) return 'At Risk';
    }
    
    return 'On Track';
  };

  // Define the correct phase order
  const phaseOrder = [
    'Planning',
    'Data Profiling', 
    'Scoping',
    'Sample Selection',
    'Data Owner ID',
    'Data Provider ID', // Handle both variants
    'Request Info',
    'Test Execution', // Phase 7
    'Testing', // Handle legacy 'Testing' phase name
    'Observations', // Phase 8 - Observation Management  
    'Finalize Testing Report',
    'Finalize Test Report' // Handle both variants
  ];

  const phaseCards: PhaseCardData[] = workflowStatus?.phases?.map((phase: any) => {
    // Normalize phase name to handle both 'Data Provider ID' and 'Data Owner ID'
    const normalizedPhaseName = phase.phase_name === 'Data Provider ID' ? 'Data Owner ID' : phase.phase_name;
    const phaseStatus = getPhaseStatus(phase);
    
    return {
      phase_name: phase.phase_name,
      display_name: phaseDisplayNames[normalizedPhaseName] || phase.phase_name,
      status: phaseStatus, // This is now the calculated status (Past Due, At Risk, On Track)
      state: phase.state,  // This is actual workflow state (Not Started, In Progress, Complete)
      progress: phase.progress || 0,
      planned_start_date: phase.planned_start_date,
      planned_end_date: phase.planned_end_date,
      actual_start_date: phase.actual_start_date,
      actual_end_date: phase.actual_end_date,
      is_overdue: phaseStatus === 'Past Due',
      is_at_risk: phaseStatus === 'At Risk',
      metrics: phase.metrics,
      route_name: phaseRouteMapping[phase.phase_name] || phaseRouteMapping[normalizedPhaseName] || 'data-owner'
    };
  }).sort((a, b) => {
    // Sort by the predefined phase order
    const aIndex = phaseOrder.indexOf(a.phase_name);
    const bIndex = phaseOrder.indexOf(b.phase_name);
    
    // If phase not found in order, put it at the end
    const aOrder = aIndex === -1 ? 999 : aIndex;
    const bOrder = bIndex === -1 ? 999 : bIndex;
    
    return aOrder - bOrder;
  }) || [];

  // Calculate overall metrics
  const totalPhases = phaseCards.length;
  const completedPhases = phaseCards.filter(p => p.state === 'Complete').length;
  const inProgressPhases = phaseCards.filter(p => p.state === 'In Progress').length;
  const overduePhases = phaseCards.filter(p => p.is_overdue).length;
  const atRiskPhases = phaseCards.filter(p => p.is_at_risk).length;

  return (
    <Container maxWidth={false} sx={{ py: 3 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link
          color="inherit"
          href="#"
          onClick={(e: React.MouseEvent) => {
            e.preventDefault();
            navigate('/cycles');
          }}
        >
          Test Cycles
        </Link>
        <Link
          color="inherit"
          href="#"
          onClick={(e: React.MouseEvent) => {
            e.preventDefault();
            navigate(`/cycles/${cycleId}`);
          }}
        >
          {reportDetail?.cycle_name || 'Loading...'}
        </Link>
        <Typography variant="body1" color="text.primary">
          {reportDetail?.report_name || 'Loading...'}
        </Typography>
      </Breadcrumbs>

      {/* Header Section with Report Info */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            {/* Left side - Report title and back button */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <IconButton onClick={() => navigate(`/cycles/${cycleId}`)}>
                <ArrowBackIcon />
              </IconButton>
              <AssignmentIcon color="primary" fontSize="large" />
              <Box>
                <Typography variant="h5" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportDetail?.report_name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {reportDetail?.description}
                </Typography>
              </Box>
            </Box>
            
            {/* Right side - Key metadata */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <BusinessIcon color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">LOB:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportDetail?.lob_name || 'Unknown'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">Tester:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportDetail?.tester_name || 'Not assigned'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">Owner:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportDetail?.report_owner_name || 'Not specified'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="text.secondary">ID:</Typography>
                <Typography variant="body2" fontWeight="medium" fontFamily="monospace">
                  {reportId}
                </Typography>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Start Testing Button - Show if no workflow exists */}
      {!workflowStatus && !workflowLoading && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="h6" gutterBottom>
                No testing workflow has been started for this report
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Click the button below to initialize the testing workflow and create all phases
              </Typography>
              <Button
                variant="contained"
                size="large"
                startIcon={<PlayArrowIcon />}
                onClick={async () => {
                  try {
                    const response = await apiClient.post(
                      `/api/v1/cycles/${cycleId}/reports/${reportId}/start-workflow`
                    );
                    
                    if (response.data.status === 'started') {
                      // Refetch workflow status
                      queryClient.invalidateQueries({ queryKey: ['workflow-status', cycleId, reportId] });
                      // Show success message
                      alert('Testing workflow started successfully!');
                    } else if (response.data.status === 'existing') {
                      alert('A workflow already exists for this report');
                    }
                  } catch (error: any) {
                    console.error('Error starting workflow:', error);
                    alert(error.response?.data?.detail || 'Failed to start workflow');
                  }
                }}
                sx={{ 
                  px: 4,
                  py: 1.5,
                  fontSize: '1.1rem'
                }}
              >
                Start Testing Workflow
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Metrics Overview */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h3" color="primary" component="div">
              {Math.round(workflowStatus?.overall_progress || 0)}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Overall Progress
            </Typography>
            <LinearProgress
              variant="determinate"
              value={workflowStatus?.overall_progress || 0}
              sx={{ mt: 1, height: 6, borderRadius: 3 }}
            />
          </Paper>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Box display="flex" justifyContent="center" alignItems="center" gap={1}>
              <CheckCircleIcon color="success" />
              <Typography variant="h3" component="div">{completedPhases}</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Completed Phases
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {inProgressPhases} in progress
            </Typography>
          </Paper>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Box display="flex" justifyContent="center" alignItems="center" gap={1}>
              <CalendarIcon color="action" />
              <Typography variant="h3" component="div">
                {formatDate(reportDetail?.started_at)}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Started Date
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Target: {formatDate(reportDetail?.estimated_completion)}
            </Typography>
          </Paper>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Box display="flex" justifyContent="center" alignItems="center" gap={1}>
              {overduePhases > 0 ? (
                <WarningIcon color="error" />
              ) : atRiskPhases > 0 ? (
                <WarningIcon color="warning" />
              ) : (
                <TrendingUpIcon color="success" />
              )}
              <Typography variant="h3" component="div" color={overduePhases > 0 ? 'error' : atRiskPhases > 0 ? 'warning' : 'success'}>
                {overduePhases > 0 ? overduePhases : atRiskPhases > 0 ? atRiskPhases : 'On Track'}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {overduePhases > 0 ? 'Overdue Phases' : atRiskPhases > 0 ? 'At Risk Phases' : 'Status'}
            </Typography>
          </Paper>
          </Grid>
        </Grid>
      </Box>

      {/* Workflow Phases Section */}
      <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
        Workflow Phases
      </Typography>
      
      {/* Phase Cards - Responsive grid layout */}
      <Grid container spacing={1.5}>
        {phaseCards.map((phase, index) => {
          const phaseColor = phaseColors[phase.phase_name] || '#757575';
          return (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={phase.phase_name}>
            <Card
              sx={{
                height: 160, // Fixed height for all cards
                cursor: 'pointer',
                transition: 'all 0.3s',
                borderTop: `4px solid ${phaseColor}`,
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: 3,
                },
              }}
              onClick={() => navigate(`/cycles/${cycleId}/reports/${reportId}/${phase.route_name}`)}
            >
              <CardContent sx={{ p: 1.2 }}>
                {/* Header Row: Phase Label and Name */}
                <Box display="flex" alignItems="center" gap={1} mb={0.8}>
                  <Chip 
                    label={`Phase ${index + 1}`} 
                    size="small" 
                    sx={{ 
                      backgroundColor: phaseColor,
                      color: 'white',
                      fontSize: '0.65rem',
                      height: 20
                    }}
                  />
                  <Typography variant="subtitle2" fontWeight="bold" sx={{ fontSize: '0.85rem' }}>
                    {phase.display_name}
                  </Typography>
                </Box>

                {/* Second Row: State Badge and Status Badge on Left (horizontal), Start Date on Right */}
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.6}>
                  <Box display="flex" gap={0.5}>
                    {/* State Badge */}
                    <Chip
                      label={phase.state}
                      size="small"
                      color={getStateChipColor(phase.state)}
                      variant={phase.state === 'In Progress' ? 'filled' : 'outlined'}
                      sx={{ height: 18, fontSize: '0.6rem' }}
                    />
                    {/* Status Badge - Only show if phase has started and is not complete */}
                    {phase.state !== 'Not Started' && phase.state !== 'Complete' && (
                      <Chip
                        label={phase.status}
                        size="small"
                        color={getStatusChipColor(phase.status)}
                        variant="filled"
                        sx={{ height: 18, fontSize: '0.6rem' }}
                      />
                    )}
                  </Box>
                  <Box textAlign="right">
                    <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                      <Box component="span" fontWeight="bold" color="text.secondary">
                        Start:
                      </Box>
                      {' '}
                      <Box component="span" fontWeight="medium">
                        {formatDateCompact(phase.planned_start_date)}
                      </Box>
                      {' / '}
                      <Box component="span" color={phase.actual_start_date ? 'success.main' : 'text.secondary'}>
                        {formatDateCompact(phase.actual_start_date)}
                      </Box>
                    </Typography>
                  </Box>
                </Box>

                {/* Third Row: Empty on Left, End Date on Right */}
                <Box display="flex" justifyContent="flex-end" alignItems="center" mb={0.6}>
                  <Box textAlign="right">
                    <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                      <Box component="span" fontWeight="bold" color="text.secondary">
                        End:
                      </Box>
                      {' '}
                      <Box component="span" fontWeight="medium">
                        {formatDateCompact(phase.planned_end_date)}
                      </Box>
                      {' / '}
                      <Box component="span" color={phase.actual_end_date ? 'success.main' : 'text.secondary'}>
                        {formatDateCompact(phase.actual_end_date)}
                      </Box>
                    </Typography>
                  </Box>
                </Box>

                {/* Fourth Row: Empty on Left, Duration on Right */}
                {phase.actual_start_date && (
                  <Box display="flex" justifyContent="flex-end" alignItems="center" mb={0.6}>
                    <Box textAlign="right">
                      <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                        <Box component="span" fontWeight="bold" color="text.secondary">
                          Duration:
                        </Box>
                        {' '}
                        <Box component="span" fontWeight="medium">
                          {calculateElapsedDuration(phase.actual_start_date, phase.actual_end_date)}
                        </Box>
                      </Typography>
                    </Box>
                  </Box>
                )}



                {/* Compact Metrics - Only show key metrics if available */}
                {phase.metrics && phase.metrics.total_items !== undefined && (
                  <Box display="flex" justifyContent="space-between" alignItems="center" mt={0.5} mb={1}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                      Items:
                    </Typography>
                    <Typography variant="caption" fontWeight="medium" sx={{ fontSize: '0.7rem' }}>
                      {phase.metrics.completed_items || 0}/{phase.metrics.total_items}
                      {phase.metrics.success_rate !== undefined && ` (${phase.metrics.success_rate}%)`}
                    </Typography>
                  </Box>
                )}

                {/* View Details Link */}
                <Box mt={0.5} textAlign="center">
                  <Button
                    size="small"
                    color="primary"
                    variant="text"
                    sx={{ 
                      fontSize: '0.7rem',
                      minHeight: 'auto',
                      py: 0.3,
                      px: 1
                    }}
                  >
                    View Details
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          );
        })}
      </Grid>

    </Container>
  );
};

export default ReportTestingPageRedesigned;