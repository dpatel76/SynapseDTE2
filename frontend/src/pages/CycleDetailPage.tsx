import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Alert,
  CircularProgress,
  Breadcrumbs,
  Link,
  Badge,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  Grid,
  Stepper,
  Step,
  StepLabel,
  Tooltip,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Visibility as ViewIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  MoreVert as MoreVertIcon,
  PersonAdd as PersonAddIcon,
  Edit as EditIcon,
  Remove as RemoveIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  PlayArrow as PlayArrowIcon,
  Launch as LaunchIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import { UserRole } from '../types/api';
import apiClient from '../api/client';
import WorkflowVisualization from '../components/WorkflowVisualization';

// Real API integration instead of mock data
interface ReportInCycle {
  report_id: number;
  report_name: string;
  tester_id?: number;
  tester?: {
    user_id: number;
    first_name: string;
    last_name: string;
  };
  lob_name: string;
  status: string;
  current_phase: string;
  overall_progress: number;
  started_at?: string;
  estimated_completion?: string;
  issues_count: number;
  workflow_id?: string;
}

interface CycleDetail {
  cycle_id: number;
  cycle_name: string;
  description?: string;
  start_date: string;
  end_date?: string;
  status: string;
  test_manager: {
    first_name: string;
    last_name: string;
  };
  reports: ReportInCycle[];
  overall_progress: number;
  total_reports: number;
  completed_reports: number;
  in_progress_reports: number;
  not_started_reports: number;
}

interface TesterAssignmentDialogProps {
  open: boolean;
  onClose: () => void;
  report: ReportInCycle | null;
  cycleId: number;
}

const TesterAssignmentDialog: React.FC<TesterAssignmentDialogProps> = ({ 
  open, 
  onClose, 
  report, 
  cycleId 
}) => {
  const [selectedTester, setSelectedTester] = useState<number | ''>('');
  const { showToast } = useNotifications();
  const queryClient = useQueryClient();

  // Query for available testers
  const { data: testersData, isLoading: testersLoading } = useQuery({
    queryKey: ['testers'],
    queryFn: async () => {
      const response = await apiClient.get('/users/?role=Tester');
      return response.data;
    },
    enabled: open,
  });

  // Mutation to assign tester
  const assignTesterMutation = useMutation({
    mutationFn: async (testerId: number) => {
      const response = await apiClient.put(`/cycles/${cycleId}/reports/${report?.report_id}/assign-tester`, {
        tester_id: testerId
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycle-detail', cycleId] });
      // Invalidate tester assignments to ensure they see new assignments
      queryClient.invalidateQueries({ queryKey: ['tester-all-assignments'] });
      showToast('success', 'Tester assigned successfully');
      onClose();
      setSelectedTester('');
    },
    onError: (error: any) => {
      showToast('error', `Failed to assign tester: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleSubmit = () => {
    if (typeof selectedTester === 'number') {
      assignTesterMutation.mutate(selectedTester);
    }
  };

  const testers = testersData?.users || [];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {report?.tester ? 'Reassign Tester' : 'Assign Tester'} - {report?.report_name}
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" paragraph>
          {report?.tester 
            ? `Current tester: ${report.tester.first_name} ${report.tester.last_name}`
            : 'No tester currently assigned to this report.'
          }
        </Typography>

        {testersLoading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : (
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Select Tester</InputLabel>
            <Select
              value={selectedTester}
              onChange={(e) => setSelectedTester(e.target.value)}
              label="Select Tester"
            >
              <MenuItem value="">
                <em>Unassign tester</em>
              </MenuItem>
              {testers.map((tester: any) => (
                <MenuItem key={tester.user_id} value={tester.user_id}>
                  {`${tester.first_name} ${tester.last_name} (${tester.email})`}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={assignTesterMutation.isPending}
        >
          {assignTesterMutation.isPending ? <CircularProgress size={20} /> : 'Assign'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Workflow phase definitions - 8 phases including final report
const WORKFLOW_PHASES = [
  { key: 'Planning', label: 'Planning', color: '#1976d2' },
  { key: 'Scoping', label: 'Scoping', color: '#388e3c' },
  { key: 'Sample Selection', label: 'Sample Selection', color: '#7b1fa2' },
  { key: 'Data Owner ID', label: 'Data Owner Identification', color: '#f57c00' },
  { key: 'Data Provider ID', label: 'Data Owner Identification', color: '#f57c00' }, // Handle both names
  { key: 'Request Info', label: 'Request for Information', color: '#d32f2f' },
  { key: 'Testing', label: 'Test Execution', color: '#0288d1' },
  { key: 'Test Execution', label: 'Test Execution', color: '#0288d1' }, // Handle both names
  { key: 'Observations', label: 'Observation Management', color: '#5d4037' },
  { key: 'Observation Management', label: 'Observation Management', color: '#5d4037' }, // Handle both names
  { key: 'Preparing Test Report', label: 'Preparing Test Report', color: '#9c27b0' },
];

// Get unique phases for display - All 9 phases
const DISPLAY_PHASES = [
  { key: 'Planning', label: 'Planning', color: '#1976d2' },
  { key: 'Data Profiling', label: 'Data Profiling', color: '#2e7d32' },
  { key: 'Scoping', label: 'Scoping', color: '#388e3c' },
  { key: 'Sample Selection', label: 'Sample Selection', color: '#7b1fa2' },
  { key: 'Data Owner ID', label: 'Data Owner Identification', color: '#f57c00' },
  { key: 'Request Info', label: 'Request for Information', color: '#d32f2f' },
  { key: 'Testing', label: 'Test Execution', color: '#0288d1' },
  { key: 'Observations', label: 'Observation Management', color: '#5d4037' },
  { key: 'Finalize Test Report', label: 'Finalize Test Report', color: '#9c27b0' },
];

const CycleDetailPage: React.FC = () => {
  const { cycleId } = useParams<{ cycleId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showToast } = useNotifications();
  const queryClient = useQueryClient();
  
  // State for dialogs and menus
  const [testerAssignmentDialog, setTesterAssignmentDialog] = useState<{
    open: boolean;
    report: ReportInCycle | null;
  }>({ open: false, report: null });
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedReport, setSelectedReport] = useState<ReportInCycle | null>(null);
  const [showWorkflowVisualization, setShowWorkflowVisualization] = useState(false);
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>(null);

  // Real API call to get cycle details
  const { data: cycleDetail, isLoading, error } = useQuery({
    queryKey: ['cycle-detail', cycleId],
    queryFn: async (): Promise<CycleDetail> => {
      try {
        const response = await apiClient.get(`/cycles/${cycleId}`);
        const cycleData = response.data;
        
        // Get reports for this cycle
        const reportsResponse = await apiClient.get(`/cycles/${cycleId}/reports`);
        const reportsData = reportsResponse.data;
        console.log('Reports data from API:', reportsData);
        
        // Transform the API response to match our interface
        const transformedReports: ReportInCycle[] = reportsData.map((report: any) => ({
          report_id: report.report_id,
          report_name: report.report_name || `Report ${report.report_id}`,
          tester_id: report.tester_id,
          tester: report.tester_id ? {
            user_id: report.tester_id,
            first_name: report.tester_name?.split(' ')[0] || 'Unknown',
            last_name: report.tester_name?.split(' ')[1] || 'User',
          } : undefined,
          lob_name: report.lob_name || 'Default LOB',
          status: report.status || 'Not Started',
          current_phase: report.current_phase || 'Planning',
          overall_progress: report.overall_progress !== undefined ? report.overall_progress : (
            report.status === 'Complete' ? 100 : 
            report.status === 'In Progress' ? 50 : 0
          ),
          started_at: report.started_at,
          estimated_completion: report.completed_at,
          issues_count: report.issues_count || 0,
          workflow_id: report.workflow_id,
        }));
        
        return {
          cycle_id: cycleData.cycle_id,
          cycle_name: cycleData.cycle_name,
          description: cycleData.description,
          start_date: cycleData.start_date,
          end_date: cycleData.end_date,
          status: cycleData.status,
          test_manager: {
            first_name: cycleData.test_manager_name?.split(' ')[0] || 'Unknown',
            last_name: cycleData.test_manager_name?.split(' ')[1] || 'Manager',
          },
          reports: transformedReports,
          total_reports: transformedReports.length,
          completed_reports: transformedReports.filter(r => r.status === 'Complete').length,
          in_progress_reports: transformedReports.filter(r => r.status === 'In Progress').length,
          not_started_reports: transformedReports.filter(r => r.status === 'Not Started').length,
          overall_progress: transformedReports.length > 0 
            ? Math.round(
                transformedReports.reduce((sum, r) => sum + r.overall_progress, 0) / transformedReports.length
              )
            : 0,
        };
      } catch (error) {
        console.error('API Error:', error);
        throw error;
      }
    },
    enabled: !!cycleId
  });

  // Mutation to remove report from cycle
  const removeReportMutation = useMutation({
    mutationFn: async (reportId: number) => {
      const response = await apiClient.delete(`/cycles/${cycleId}/reports/${reportId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycle-detail', cycleId] });
      showToast('success', 'Report removed from cycle');
      handleCloseMenu();
    },
    onError: (error: any) => {
      showToast('error', `Failed to remove report: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleReportMenu = (event: React.MouseEvent<HTMLElement>, report: ReportInCycle) => {
    console.log('Menu opened for report:', report);
    console.log('Current user:', user);
    console.log('Comparison:', {
      user_id: user?.user_id,
      tester_id: report.tester_id,
      workflow_id: report.workflow_id,
      condition: user?.user_id === report.tester_id && !report.workflow_id
    });
    setAnchorEl(event.currentTarget);
    setSelectedReport(report);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
    setSelectedReport(null);
  };

  const handleViewReport = (reportId: number) => {
    navigate(`/cycles/${cycleId}/reports/${reportId}`);
    handleCloseMenu();
  };

  const handleAssignTester = (report: ReportInCycle) => {
    setTesterAssignmentDialog({ open: true, report });
    handleCloseMenu();
  };

  const handleRemoveReport = (report: ReportInCycle) => {
    if (window.confirm(`Are you sure you want to remove "${report.report_name}" from this cycle?`)) {
      removeReportMutation.mutate(report.report_id);
    }
  };

  // Check if user is Test Executive
  const isTestManager = user?.role === UserRole.TEST_EXECUTIVE;

  // Query for active workflows - disabled as workflow management endpoints are not available
  const cycleWorkflows: { workflows?: any[]; count?: number } | null = null;
  // const { data: cycleWorkflows } = useQuery({
  //   queryKey: ['cycle-workflows', cycleId],
  //   queryFn: async () => {
  //     const response = await apiClient.get(`/workflow/cycle/${cycleId}/workflows`);
  //     return response.data;
  //   },
  //   enabled: !!cycleId && !!cycleDetail,
  //   refetchInterval: 10000, // Refetch every 10 seconds
  // });

  // Query for aggregated workflow metrics
  const { data: workflowMetrics, isLoading: workflowLoading, error: workflowError } = useQuery({
    queryKey: ['cycle-workflow-metrics', cycleId],
    queryFn: async () => {
      if (!cycleDetail?.reports.length) return null;
      
      // Get workflow status for all reports
      const promises = cycleDetail.reports.map(async (report) => {
        try {
          const response = await apiClient.get(`/cycle-reports/${cycleId}/reports/${report.report_id}/workflow-status`);
          return {
            report_id: report.report_id,
            report_name: report.report_name,
            ...response.data
          };
        } catch (error) {
          console.error(`Error fetching workflow for report ${report.report_id}:`, error);
          return null;
        }
      });
      
      const results = await Promise.all(promises);
      const validResults = results.filter(result => result !== null);
      
      // If no valid results, return null to indicate no workflow data available
      if (validResults.length === 0) {
        return null;
      }
      
      // Calculate aggregated metrics
      let totalProgress = 0;
      let pastDueCount = 0;
      let watchItemCount = 0;
      
      // Initialize phase distribution with display phases
      const phaseDistribution: Record<string, number> = {};
      const phaseReports: Record<string, string[]> = {};
      const phaseStatuses: Record<string, { complete: number; inProgress: number; notStarted: number }> = {};
      
      DISPLAY_PHASES.forEach(phase => {
        phaseDistribution[phase.key] = 0;
        phaseReports[phase.key] = [];
        phaseStatuses[phase.key] = { complete: 0, inProgress: 0, notStarted: 0 };
      });
      
      validResults.forEach(workflow => {
        // Count reports by current phase - normalize phase names
        let currentPhase = workflow.current_phase;
        if (currentPhase === 'Data Provider ID') currentPhase = 'Data Owner ID';
        if (currentPhase === 'Test Execution') currentPhase = 'Testing';
        if (currentPhase === 'Observation Management') currentPhase = 'Observations';
        
        if (currentPhase && phaseDistribution.hasOwnProperty(currentPhase)) {
          phaseDistribution[currentPhase] += 1;
          phaseReports[currentPhase].push(workflow.report_name);
        }
        
        // Count phase statuses for each phase
        if (workflow.phases) {
          workflow.phases.forEach((phase: any) => {
            let phaseKey = phase.phase_name;
            if (phaseKey === 'Data Provider ID') phaseKey = 'Data Owner ID';
            if (phaseKey === 'Test Execution') phaseKey = 'Testing';
            if (phaseKey === 'Observation Management') phaseKey = 'Observations';
            
            if (phaseStatuses[phaseKey]) {
              if (phase.effective_state === 'Complete') {
                phaseStatuses[phaseKey].complete += 1;
              } else if (phase.effective_state === 'In Progress') {
                phaseStatuses[phaseKey].inProgress += 1;
              } else {
                phaseStatuses[phaseKey].notStarted += 1;
              }
            }
          });
        }
        
        // Sum up progress
        totalProgress += workflow.overall_progress || 0;
        
        // Count phases with schedule issues
        if (workflow.phases) {
          workflow.phases.forEach((phase: any) => {
            if (phase.effective_status === 'Past Due') pastDueCount += 1;
            if (phase.effective_status === 'At Risk') watchItemCount += 1;
          });
        }
      });
      
      return {
        totalReports: validResults.length,
        averageProgress: validResults.length > 0 ? Math.round(totalProgress / validResults.length) : 0,
        phaseDistribution,
        phaseReports,
        phaseStatuses,
        pastDueCount,
        watchItemCount,
        workflows: validResults
      };
    },
    enabled: !!cycleDetail?.reports.length,
    retry: false, // Don't retry on error
    refetchOnWindowFocus: false, // Don't refetch when window regains focus
  });

  const getPhaseStatusColor = (status: string) => {
    switch (status) {
      case 'Complete': return 'success';
      case 'In Progress': return 'primary';
      case 'Not Started': return 'default';
      default: return 'default';
    }
  };

  const getPhaseIcon = (phase: string) => {
    const phaseConfig = WORKFLOW_PHASES.find(p => p.key === phase);
    return phaseConfig ? (
      <Box
        sx={{
          width: 20,
          height: 20,
          borderRadius: '50%',
          backgroundColor: phaseConfig.color,
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '10px',
          fontWeight: 'bold',
          mr: 1
        }}
      >
        {phaseConfig.label.charAt(0)}
      </Box>
    ) : null;
  };

  const renderWorkflowMetrics = () => {
    if (workflowLoading) {
      return (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="center" p={2}>
              <CircularProgress />
            </Box>
          </CardContent>
        </Card>
      );
    }

    if (workflowError || !workflowMetrics) {
      return (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Workflow Progress Overview
            </Typography>
            <Alert severity="info">
              Workflow metrics are currently unavailable. This feature requires workflow phases to be initialized for reports in this cycle.
            </Alert>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Workflow Progress Overview
          </Typography>
          
          {/* Key Metrics */}
          <Box display="flex" flexWrap="wrap" gap={2} sx={{ mb: 3 }}>
            <Box flex="1 1 200px" textAlign="center">
              <Typography variant="h4" color="primary">
                {workflowMetrics?.averageProgress || 0}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Average Progress
              </Typography>
            </Box>
            <Box flex="1 1 200px" textAlign="center">
              <Typography variant="h4" color="error">
                {workflowMetrics?.pastDueCount || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Past Due Phases
              </Typography>
            </Box>
            <Box flex="1 1 200px" textAlign="center">
              <Typography variant="h4" color="warning.main">
                {workflowMetrics?.watchItemCount || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Watch Items
              </Typography>
            </Box>
            <Box flex="1 1 200px" textAlign="center">
              <Typography variant="h4" color="success.main">
                {workflowMetrics?.totalReports || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Reports
              </Typography>
            </Box>
          </Box>

          {/* Enhanced Phase Progress Grid */}
          <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
            Workflow Phase Progress
          </Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {DISPLAY_PHASES.map((phase, index) => {
              const currentCount = workflowMetrics?.phaseDistribution[phase.key] || 0;
              const phaseStatus = workflowMetrics?.phaseStatuses[phase.key] || { complete: 0, inProgress: 0, notStarted: 0 };
              const totalReports = workflowMetrics?.totalReports || 0;
              const reports = workflowMetrics?.phaseReports[phase.key] || [];
              
              return (
                <Grid key={phase.key} size={{ xs: 12, sm: 6, md: 4 }}>
                  <Card 
                    sx={{ 
                      height: '100%',
                      borderTop: `4px solid ${phase.color}`,
                      transition: 'all 0.3s',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 3,
                      }
                    }}
                  >
                    <CardContent sx={{ p: 1.5 }}>
                      <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                        <Typography variant="subtitle2" fontWeight="medium">
                          {phase.label}
                        </Typography>
                        <Chip 
                          label={`Phase ${index + 1}`} 
                          size="small" 
                          sx={{ 
                            backgroundColor: phase.color,
                            color: 'white',
                            fontSize: '0.7rem'
                          }}
                        />
                      </Box>
                      
                      {/* Phase Statistics */}
                      <Box sx={{ mb: 2 }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                          <Typography variant="caption" color="text.secondary">
                            Current:
                          </Typography>
                          <Tooltip title={reports.length > 0 ? `Reports: ${reports.join(', ')}` : 'No reports currently in this phase'}>
                            <Typography variant="body2" fontWeight="bold" sx={{ cursor: 'pointer' }}>
                              {currentCount} {currentCount === 1 ? 'report' : 'reports'}
                            </Typography>
                          </Tooltip>
                        </Box>
                        
                        <Box display="flex" gap={0.5} mb={1}>
                          {phaseStatus.complete > 0 && (
                            <Tooltip title="Completed">
                              <Chip 
                                size="small" 
                                label={phaseStatus.complete} 
                                color="success" 
                                sx={{ height: 20, fontSize: '0.7rem' }}
                              />
                            </Tooltip>
                          )}
                          {phaseStatus.inProgress > 0 && (
                            <Tooltip title="In Progress">
                              <Chip 
                                size="small" 
                                label={phaseStatus.inProgress} 
                                color="warning" 
                                sx={{ height: 20, fontSize: '0.7rem' }}
                              />
                            </Tooltip>
                          )}
                          {phaseStatus.notStarted > 0 && (
                            <Tooltip title="Not Started">
                              <Chip 
                                size="small" 
                                label={phaseStatus.notStarted} 
                                color="default" 
                                sx={{ height: 20, fontSize: '0.7rem' }}
                              />
                            </Tooltip>
                          )}
                        </Box>
                        
                        {/* Progress Bar */}
                        <Box>
                          <LinearProgress
                            variant="determinate"
                            value={(phaseStatus.complete / totalReports) * 100}
                            sx={{
                              height: 6,
                              borderRadius: 3,
                              backgroundColor: 'grey.300',
                              '& .MuiLinearProgress-bar': {
                                backgroundColor: phase.color,
                              }
                            }}
                          />
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                            {Math.round((phaseStatus.complete / totalReports) * 100)}% complete
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </CardContent>
      </Card>
    );
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !cycleDetail) {
    return (
      <Alert severity="error">
        Failed to load cycle details. Please try again.
      </Alert>
    );
  }

  return (
    <Box p={3}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 3 }}>
        <Link
          component="button"
          variant="body1"
          onClick={() => navigate('/cycles')}
          sx={{ textDecoration: 'none' }}
        >
          Test Cycles
        </Link>
        <Typography variant="body1" color="text.primary">
          {cycleDetail.cycle_name}
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <IconButton onClick={() => navigate('/cycles')}>
          <ArrowBackIcon />
        </IconButton>
        <Box flex={1}>
          <Typography variant="h4">
            {cycleDetail.cycle_name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {cycleDetail.description}
          </Typography>
        </Box>
        <Chip 
          label={cycleDetail.status.toUpperCase()} 
          color="primary" 
          variant="outlined"
        />
        {/* Action buttons for Test Executive */}
        {(user?.role as string) === 'Test Executive' && (
          <>
            {cycleDetail.status === 'Planning' && (
              <>
                <Button
                  variant="outlined"
                  startIcon={<PersonAddIcon />}
                  onClick={() => {
                    // Open add reports dialog
                    navigate(`/cycles?openAddReports=${cycleId}`);
                  }}
                >
                  Add Reports
                </Button>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<PlayArrowIcon />}
                  onClick={async () => {
                    try {
                      await apiClient.put(`/cycles/${cycleId}`, { status: 'Active' });
                      // Invalidate all relevant queries to refresh metrics
                      queryClient.invalidateQueries({ queryKey: ['cycle-detail', cycleId] });
                      queryClient.invalidateQueries({ queryKey: ['cycles'] });
                      queryClient.invalidateQueries({ queryKey: ['cycles-executive'] });
                      queryClient.invalidateQueries({ queryKey: ['test-executive-metrics-redesigned'] });
                      queryClient.invalidateQueries({ queryKey: ['metrics'] });
                      showToast('success', 'Test cycle started successfully');
                    } catch (error: any) {
                      showToast('error', 'Failed to start test cycle');
                    }
                  }}
                >
                  Start Cycle
                </Button>
              </>
            )}
            {cycleDetail.status === 'Active' && (
              <Button
                variant="outlined"
                startIcon={<PersonAddIcon />}
                onClick={() => {
                  navigate(`/cycles?openAddReports=${cycleId}`);
                }}
              >
                Add Reports
              </Button>
            )}
          </>
        )}
      </Box>

      {/* Cycle Overview Cards */}
      <Box display="flex" gap={2} mb={4} flexWrap="wrap">
        <Card sx={{ minWidth: 200 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Overall Progress
            </Typography>
            <Typography variant="h4" color="primary">
              {cycleDetail.overall_progress}%
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={cycleDetail.overall_progress} 
              sx={{ mt: 1, height: 6, borderRadius: 3 }}
            />
          </CardContent>
        </Card>
        
        <Card sx={{ minWidth: 200 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Reports
            </Typography>
            <Typography variant="h4">
              {cycleDetail.total_reports}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ minWidth: 200 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Completed
            </Typography>
            <Typography variant="h4" color="success.main">
              {cycleDetail.completed_reports}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ minWidth: 200 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              In Progress
            </Typography>
            <Typography variant="h4" color="primary.main">
              {cycleDetail.in_progress_reports}
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Workflow Controls for Test Manager - Disabled as workflow endpoints are not available */}
      {/* {isTestManager && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Workflow Management</Typography>
              <Box>
                {cycleWorkflows?.workflows && cycleWorkflows.workflows.length > 0 ? (
                  <Button
                    variant="outlined"
                    startIcon={<ViewIcon />}
                    onClick={() => {
                      const latestWorkflow = cycleWorkflows!.workflows![0];
                      setActiveWorkflowId(latestWorkflow.workflow_id);
                      setShowWorkflowVisualization(true);
                    }}
                  >
                    View Active Workflow
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    startIcon={<PlayArrowIcon />}
                    onClick={async () => {
                      try {
                        const reportIds = cycleDetail?.reports.map(r => r.report_id);
                        const response = await apiClient.post(`/workflow/start/${cycleId}`, {
                          report_ids: reportIds,
                        });
                        showToast('success', 'Workflow started successfully');
                        queryClient.invalidateQueries({ queryKey: ['cycle-workflows', cycleId] });
                        setActiveWorkflowId(response.data.workflow.workflow_id);
                        setShowWorkflowVisualization(true);
                      } catch (error: any) {
                        showToast('error', `Failed to start workflow: ${error.response?.data?.detail || error.message}`);
                      }
                    }}
                    disabled={!cycleDetail?.reports?.length}
                  >
                    Start Workflow
                  </Button>
                )}
              </Box>
            </Box>
            
            {cycleWorkflows?.workflows && cycleWorkflows.workflows.length > 0 && (
              <Alert severity="info" sx={{ mb: 2 }}>
                {cycleWorkflows.count} active workflow{cycleWorkflows.count !== 1 ? 's' : ''} found for this cycle
              </Alert>
            )}
          </CardContent>
        </Card>
      )} */}

      {/* Workflow Visualization */}
      {showWorkflowVisualization && activeWorkflowId && (
        <Box mb={3}>
          <WorkflowVisualization
            cycleId={parseInt(cycleId || '0')}
            workflowId={activeWorkflowId}
            onRefresh={() => {
              queryClient.invalidateQueries({ queryKey: ['cycle-workflows', cycleId] });
            }}
            showMetrics={true}
          />
        </Box>
      )}

      {/* Workflow Metrics */}
      {renderWorkflowMetrics()}

      {/* Reports Table with Phase Information */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Reports in Cycle
          </Typography>
          
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Report</TableCell>
                  <TableCell>Tester</TableCell>
                  <TableCell>Current Phase</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Issues</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {cycleDetail.reports.map((report) => (
                  <TableRow key={report.report_id}>
                    <TableCell>
                      <Box>
                        <Typography variant="subtitle2">
                          {report.report_name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {report.lob_name}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {report.tester ? (
                        <Box>
                          <Typography variant="body2">
                            {`${report.tester.first_name} ${report.tester.last_name}`}
                          </Typography>
                          {isTestManager && (
                            <Button
                              size="small"
                              startIcon={<EditIcon />}
                              onClick={() => handleAssignTester(report)}
                              sx={{ mt: 0.5 }}
                            >
                              Reassign
                            </Button>
                          )}
                        </Box>
                      ) : (
                        <Box>
                          <Chip label="Unassigned" size="small" variant="outlined" />
                          {isTestManager && (
                            <Button
                              size="small"
                              startIcon={<PersonAddIcon />}
                              onClick={() => handleAssignTester(report)}
                              sx={{ mt: 0.5 }}
                            >
                              Assign
                            </Button>
                          )}
                        </Box>
                      )}
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {(() => {
                          // Get workflow status for this specific report
                          const reportWorkflow = workflowMetrics?.workflows?.find(
                            w => w.report_id === report.report_id
                          );
                          const currentPhase = reportWorkflow?.current_phase || report.current_phase;
                          const phaseStatus = reportWorkflow?.phases?.find(
                            (p: any) => p.phase_name === currentPhase
                          );
                          
                          // Normalize phase name for display
                          let displayPhase = currentPhase;
                          if (displayPhase === 'Data Provider ID') displayPhase = 'Data Owner ID';
                          if (displayPhase === 'Test Execution') displayPhase = 'Testing';
                          if (displayPhase === 'Observation Management') displayPhase = 'Observations';
                          
                          const phaseConfig = DISPLAY_PHASES.find(p => p.key === displayPhase);
                          
                          return (
                            <>
                              {phaseConfig && (
                                <Box
                                  sx={{
                                    width: 24,
                                    height: 24,
                                    borderRadius: '50%',
                                    backgroundColor: phaseConfig.color,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'white',
                                    fontSize: '11px',
                                    fontWeight: 'bold',
                                    flexShrink: 0
                                  }}
                                >
                                  {DISPLAY_PHASES.findIndex(p => p.key === displayPhase) + 1}
                                </Box>
                              )}
                              <Box>
                                <Typography variant="body2" fontWeight="medium">
                                  {phaseConfig?.label || displayPhase}
                                </Typography>
                                {phaseStatus && phaseStatus.effective_state !== 'Complete' && (
                                  <Chip
                                    label={phaseStatus.effective_state || phaseStatus.status}
                                    size="small"
                                    color={getPhaseStatusColor(phaseStatus.effective_state || phaseStatus.status)}
                                    sx={{ height: 18, fontSize: '0.7rem' }}
                                  />
                                )}
                              </Box>
                            </>
                          );
                        })()}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <LinearProgress
                          variant="determinate"
                          value={report.overall_progress}
                          sx={{ width: 100, height: 6, borderRadius: 3 }}
                        />
                        <Typography variant="caption">
                          {report.overall_progress}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {report.issues_count > 0 ? (
                        <Badge badgeContent={report.issues_count} color="error">
                          <WarningIcon color="error" fontSize="small" />
                        </Badge>
                      ) : (
                        <CheckCircleIcon color="success" fontSize="small" />
                      )}
                    </TableCell>
                    <TableCell>
                      {report.status !== 'Complete' && (
                        <Chip 
                          label={report.status}
                          size="small"
                          color={getPhaseStatusColor(report.status)}
                        />
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Box display="flex" justifyContent="center" gap={0.5}>
                        <Tooltip title="View Report Details">
                          <IconButton
                            size="small"
                            onClick={() => navigate(`/cycles/${cycleId}/reports/${report.report_id}/planning`)}
                          >
                            <LaunchIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <IconButton
                          size="small"
                          onClick={(e) => handleReportMenu(e, report)}
                        >
                          <MoreVertIcon />
                        </IconButton>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Context Menu for Reports */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
      >
        <MenuItem onClick={() => {
          if (selectedReport) {
            navigate(`/cycles/${cycleId}/reports/${selectedReport.report_id}/planning`);
            handleCloseMenu();
          }
        }}>
          <ViewIcon sx={{ mr: 1 }} />
          View Report Details
        </MenuItem>
        
        {/* Start Workflow option for assigned testers */}
        {selectedReport && user?.user_id === selectedReport.tester_id && !selectedReport.workflow_id && (
          <MenuItem onClick={async () => {
            if (selectedReport) {
              try {
                const response = await apiClient.post(
                  `/api/v1/cycles/${cycleId}/reports/${selectedReport.report_id}/start-workflow`
                );
                
                if (response.data.status === 'started') {
                  showToast('success', 'Testing workflow started successfully!');
                  // Refresh the data
                  queryClient.invalidateQueries({ queryKey: ['cycle-detail', cycleId] });
                  queryClient.invalidateQueries({ queryKey: ['cycle-workflow-metrics', cycleId] });
                  // Navigate to the planning page
                  navigate(`/cycles/${cycleId}/reports/${selectedReport.report_id}/planning`);
                } else if (response.data.status === 'existing') {
                  showToast('info', 'A workflow already exists for this report');
                }
              } catch (error: any) {
                console.error('Error starting workflow:', error);
                showToast('error', error.response?.data?.detail || 'Failed to start workflow');
              }
              handleCloseMenu();
            }
          }}>
            <PlayArrowIcon sx={{ mr: 1, color: 'success.main' }} />
            Start Testing Workflow
          </MenuItem>
        )}
        
        {isTestManager && selectedReport && (
          <>
            <MenuItem onClick={() => selectedReport && handleAssignTester(selectedReport)}>
              <PersonAddIcon sx={{ mr: 1 }} />
              {selectedReport.tester ? 'Reassign Tester' : 'Assign Tester'}
            </MenuItem>
            <MenuItem 
              onClick={() => selectedReport && handleRemoveReport(selectedReport)}
              sx={{ color: 'error.main' }}
              disabled={selectedReport.status !== 'Not Started'}
            >
              <RemoveIcon sx={{ mr: 1 }} />
              Remove from Cycle
            </MenuItem>
          </>
        )}
      </Menu>

      {/* Tester Assignment Dialog */}
      <TesterAssignmentDialog
        open={testerAssignmentDialog.open}
        onClose={() => setTesterAssignmentDialog({ open: false, report: null })}
        report={testerAssignmentDialog.report}
        cycleId={parseInt(cycleId || '0')}
      />
    </Box>
  );
};

export default CycleDetailPage; 