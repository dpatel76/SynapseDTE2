import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Stack,
  Grid,
  CircularProgress,
  IconButton,
  Tooltip,
  Divider,
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs, { Dayjs } from 'dayjs';
import {
  PlayArrow,
  Visibility,
  Assignment,
  CheckCircle,
  Timer,
  Schedule,
  TrendingUp,
  TrendingDown,
  CalendarToday,
  Lock,
  LockOpen,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useNotifications } from '../contexts/NotificationContext';
import apiClient from '../api/client';
import { reportsApi } from '../api/reports';
import { AssignedReport } from '../types/api';

interface PhaseDateInput {
  phase_name: string;
  start_date: Dayjs | null;
  end_date: Dayjs | null;
}

const WORKFLOW_PHASES = [
  'Planning',
  'Data Profiling',
  'Scoping',
  'Sample Selection',
  'Data Provider ID',
  'Request Info',
  'Testing',
  'Observations',
  'Finalize Test Report',
];

const TesterAssignmentsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useNotifications();
  const [searchParams] = useSearchParams();
  const highlightedReportId = searchParams.get('report');

  const [selectedReport, setSelectedReport] = useState<AssignedReport | null>(null);
  const [openDateDialog, setOpenDateDialog] = useState(false);
  const [phaseDates, setPhaseDates] = useState<PhaseDateInput[]>(
    WORKFLOW_PHASES.map(phase => ({
      phase_name: phase,
      start_date: null,
      end_date: null,
    }))
  );

  // Get all assigned reports
  const { data: assignedReports, isLoading: reportsLoading } = useQuery({
    queryKey: ['tester-all-assignments', user?.user_id],
    queryFn: async () => {
      try {
        const reports = await reportsApi.getByTester(user?.user_id || 0);
        return reports;
      } catch (error) {
        console.error('Error fetching reports:', error);
        throw error;
      }
    },
    enabled: !!user?.user_id,
  });

  // Calculate metrics
  const metrics = {
    total: assignedReports?.length || 0,
    completed: assignedReports?.filter(r => r.phase_status === 'completed').length || 0,
    inProgress: assignedReports?.filter(r => r.phase_status === 'in_progress').length || 0,
    notStarted: assignedReports?.filter(r => !r.workflow_id).length || 0,
  };

  const completionRate = metrics.total > 0 ? (metrics.completed / metrics.total) * 100 : 0;

  // Start workflow mutation
  const startWorkflowMutation = useMutation({
    mutationFn: async ({ report, dates }: { report: AssignedReport; dates: PhaseDateInput[] }) => {
      // First create the workflow
      const workflowResponse = await apiClient.post(
        `/cycles/${report.cycle_id}/reports/${report.report_id}/start-workflow`
      );

      // Then set the phase dates with retry logic
      const setPhaseDate = async (phase: PhaseDateInput, retries = 3): Promise<any> => {
        for (let i = 0; i < retries; i++) {
          try {
            return await apiClient.post(
              `/cycles/${report.cycle_id}/reports/${report.report_id}/phases/${phase.phase_name}/dates`,
              {
                start_date: phase.start_date?.format('YYYY-MM-DD'),
                end_date: phase.end_date?.format('YYYY-MM-DD'),
              }
            );
          } catch (error: any) {
            if (error.response?.status === 404 && i < retries - 1) {
              // Wait a bit before retrying if phase not found
              await new Promise(resolve => setTimeout(resolve, 1000));
            } else {
              throw error;
            }
          }
        }
      };

      const phasePromises = dates.map(phase => setPhaseDate(phase));
      await Promise.all(phasePromises);
      return workflowResponse.data;
    },
    onSuccess: (data, { report }) => {
      showToast('success', 'Testing workflow started successfully!');
      queryClient.invalidateQueries({ queryKey: ['tester-all-assignments'] });
      setOpenDateDialog(false);
      setSelectedReport(null);
      // Navigate to the report detail page
      navigate(`/cycles/${report.cycle_id}/reports/${report.report_id}`);
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Failed to start workflow');
    },
  });

  const handleStartTesting = (report: AssignedReport) => {
    setSelectedReport(report);
    // Initialize dates with reasonable defaults
    const today = dayjs();
    const updatedDates = WORKFLOW_PHASES.map((phase, index) => ({
      phase_name: phase,
      start_date: today.add(index * 3, 'day'),
      end_date: today.add(index * 3 + 2, 'day'),
    }));
    setPhaseDates(updatedDates);
    setOpenDateDialog(true);
  };

  const handleDateChange = (index: number, field: 'start_date' | 'end_date', value: any) => {
    const updatedDates = [...phaseDates];
    updatedDates[index][field] = value as Dayjs | null;
    setPhaseDates(updatedDates);
  };

  const handleSubmitDates = () => {
    if (!selectedReport) return;

    // Validate dates
    const hasInvalidDates = phaseDates.some(phase => !phase.start_date || !phase.end_date);
    if (hasInvalidDates) {
      showToast('error', 'Please provide start and end dates for all phases');
      return;
    }

    startWorkflowMutation.mutate({ report: selectedReport, dates: phaseDates });
  };

  const handleViewReport = (report: AssignedReport) => {
    if (!report.workflow_id) {
      showToast('warning', 'Please start testing before viewing report details');
      return;
    }
    navigate(`/cycles/${report.cycle_id}/reports/${report.report_id}`);
  };

  if (reportsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          My Test Assignments
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your assigned reports and start testing workflows
        </Typography>
      </Box>

      {/* Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Assignment color="primary" />
                  <Typography variant="h4">{metrics.total}</Typography>
                </Stack>
                <Typography variant="subtitle2" color="text.secondary">
                  Total Assigned
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Timer color="warning" />
                  <Typography variant="h4">{metrics.inProgress}</Typography>
                </Stack>
                <Typography variant="subtitle2" color="text.secondary">
                  In Progress
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <CheckCircle color="success" />
                  <Typography variant="h4">{metrics.completed}</Typography>
                </Stack>
                <Typography variant="subtitle2" color="text.secondary">
                  Completed
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Schedule color="info" />
                  <Typography variant="h4">{metrics.notStarted}</Typography>
                </Stack>
                <Typography variant="subtitle2" color="text.secondary">
                  Not Started
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Completion Rate */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Overall Completion Rate
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ position: 'relative', pt: 1 }}>
                <Box
                  sx={{
                    position: 'absolute',
                    left: 0,
                    right: 0,
                    height: 8,
                    backgroundColor: 'grey.200',
                    borderRadius: 4,
                  }}
                />
                <Box
                  sx={{
                    position: 'absolute',
                    left: 0,
                    width: `${completionRate}%`,
                    height: 8,
                    backgroundColor: 'success.main',
                    borderRadius: 4,
                    transition: 'width 0.3s ease',
                  }}
                />
              </Box>
            </Box>
            <Typography variant="h5" color="success.main">
              {completionRate.toFixed(1)}%
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Reports Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Report Assignments
          </Typography>
          
          {assignedReports && assignedReports.length === 0 ? (
            <Alert severity="info">
              No reports assigned. Reports will appear here once you are assigned to an active test cycle.
            </Alert>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Report Name</TableCell>
                    <TableCell>Test Cycle</TableCell>
                    <TableCell>LOB</TableCell>
                    <TableCell>Current Phase</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {assignedReports?.map((report: AssignedReport) => (
                    <TableRow 
                      key={`${report.cycle_id}-${report.report_id}`}
                      hover
                      sx={{
                        backgroundColor: highlightedReportId === report.report_id.toString() 
                          ? 'action.selected' 
                          : 'inherit'
                      }}
                    >
                      <TableCell>
                        <Typography variant="subtitle2">{report.report_name}</Typography>
                      </TableCell>
                      <TableCell>{report.cycle_name}</TableCell>
                      <TableCell>{report.lob_name}</TableCell>
                      <TableCell>
                        <Chip
                          label={report.current_phase || 'Not Started'}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={report.phase_status || 'not_started'}
                          size="small"
                          color={
                            report.phase_status === 'completed' ? 'success' :
                            report.phase_status === 'in_progress' ? 'warning' :
                            'default'
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ flex: 1, position: 'relative' }}>
                            <Box
                              sx={{
                                height: 6,
                                backgroundColor: 'grey.200',
                                borderRadius: 3,
                              }}
                            />
                            <Box
                              sx={{
                                position: 'absolute',
                                top: 0,
                                left: 0,
                                height: 6,
                                width: `${report.overall_progress || 0}%`,
                                backgroundColor: 'primary.main',
                                borderRadius: 3,
                              }}
                            />
                          </Box>
                          <Typography variant="caption">
                            {report.overall_progress || 0}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={1} justifyContent="center">
                          {!report.workflow_id ? (
                            <Button
                              size="small"
                              variant="contained"
                              startIcon={<PlayArrow />}
                              onClick={() => handleStartTesting(report)}
                              color="success"
                            >
                              Start Testing
                            </Button>
                          ) : (
                            <Tooltip title="View report details">
                              <IconButton
                                size="small"
                                onClick={() => handleViewReport(report)}
                                color="primary"
                              >
                                <Visibility />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title={report.workflow_id ? 'Testing started' : 'Testing not started'}>
                            <span>
                              <IconButton size="small" disabled>
                                {report.workflow_id ? <LockOpen color="success" /> : <Lock />}
                              </IconButton>
                            </span>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Phase Dates Dialog */}
      <Dialog 
        open={openDateDialog} 
        onClose={() => setOpenDateDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Set Testing Schedule for {selectedReport?.report_name}
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3 }}>
            Please provide start and end dates for each testing phase. These dates will be used for SLA tracking and scheduling.
          </Alert>
          
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <Stack spacing={3}>
              {phaseDates.map((phase, index) => (
                <Paper key={phase.phase_name} variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {phase.phase_name}
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <DatePicker
                        label="Start Date"
                        value={phase.start_date}
                        onChange={(value) => handleDateChange(index, 'start_date', value)}
                        sx={{ width: '100%' }}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <DatePicker
                        label="End Date"
                        value={phase.end_date}
                        onChange={(value) => handleDateChange(index, 'end_date', value)}
                        minDate={phase.start_date || undefined}
                        sx={{ width: '100%' }}
                      />
                    </Grid>
                  </Grid>
                </Paper>
              ))}
            </Stack>
          </LocalizationProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDateDialog(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmitDates}
            disabled={startWorkflowMutation.isPending}
          >
            {startWorkflowMutation.isPending ? (
              <CircularProgress size={24} />
            ) : (
              'Start Testing'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TesterAssignmentsPage;