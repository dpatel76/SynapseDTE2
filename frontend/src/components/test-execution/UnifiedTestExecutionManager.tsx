import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  LinearProgress,
  Stack,
  CircularProgress,
  Container,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  TextField,
  Rating,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Science,
  CheckCircle,
  PlayArrow,
  BugReport,
  Analytics,
  Assignment,
  Timer,
  Assessment,
  Visibility,
  RateReview,
  Close,
  Refresh,
  Download,
  Warning,
  Error,
  Info,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import apiClient from '../../api/client';

interface UnifiedTestExecutionManagerProps {
  cycleId: number;
  reportId: number;
  currentUser: any;
}

interface TestExecutionRequest {
  test_case_id: string;
  evidence_id: number;
  execution_reason?: string;
  test_type: string;
  analysis_method: string;
  execution_method?: string;
  configuration?: Record<string, any>;
  processing_notes?: string;
}

interface TestExecutionResponse {
  id: number;
  test_case_id: string;
  evidence_id: number;
  execution_number: number;
  is_latest_execution: boolean;
  execution_reason?: string;
  test_type: string;
  analysis_method: string;
  sample_value?: string;
  extracted_value?: string;
  expected_value?: string;
  test_result?: string;
  comparison_result?: boolean;
  variance_details?: Record<string, any>;
  llm_confidence_score?: number;
  llm_analysis_rationale?: string;
  execution_status: string;
  started_at?: string;
  completed_at?: string;
  processing_time_ms?: number;
  error_message?: string;
  analysis_results: Record<string, any>;
  execution_summary?: string;
  processing_notes?: string;
}

interface TestExecutionReviewRequest {
  review_status: string;
  review_notes?: string;
  reviewer_comments?: string;
  recommended_action?: string;
  accuracy_score?: number;
  completeness_score?: number;
  consistency_score?: number;
  requires_retest?: boolean;
  retest_reason?: string;
  escalation_required?: boolean;
  escalation_reason?: string;
}

interface TestExecutionDashboard {
  phase_id: number;
  cycle_id: number;
  report_id: number;
  summary: {
    total_executions: number;
    completed_executions: number;
    failed_executions: number;
    pending_executions: number;
    pending_reviews: number;
    approved_reviews: number;
    rejected_reviews: number;
    completion_percentage: number;
    average_processing_time_ms?: number;
    success_rate: number;
  };
  recent_executions: TestExecutionResponse[];
  pending_reviews: TestExecutionResponse[];
  quality_metrics: Record<string, any>;
  performance_metrics: Record<string, any>;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`unified-test-execution-tabpanel-${index}`}
      aria-labelledby={`unified-test-execution-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const UnifiedTestExecutionManager: React.FC<UnifiedTestExecutionManagerProps> = ({
  cycleId,
  reportId,
  currentUser,
}) => {
  const queryClient = useQueryClient();
  const [tabValue, setTabValue] = useState(0);
  const [selectedExecution, setSelectedExecution] = useState<TestExecutionResponse | null>(null);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [executeDialogOpen, setExecuteDialogOpen] = useState(false);
  const [bulkExecuteDialogOpen, setBulkExecuteDialogOpen] = useState(false);
  const [selectedTestCases, setSelectedTestCases] = useState<string[]>([]);
  const [testType, setTestType] = useState<string>('document_analysis');
  const [analysisMethod, setAnalysisMethod] = useState<string>('llm_analysis');
  const [executionMethod, setExecutionMethod] = useState<string>('automatic');
  const [reviewForm, setReviewForm] = useState<TestExecutionReviewRequest>({
    review_status: 'approved',
    review_notes: '',
    reviewer_comments: '',
    recommended_action: 'approve',
    accuracy_score: 1.0,
    completeness_score: 1.0,
    consistency_score: 1.0,
    requires_retest: false,
    retest_reason: '',
    escalation_required: false,
    escalation_reason: '',
  });

  // Fetch dashboard data
  const { data: dashboard, isLoading: dashboardLoading, refetch: refetchDashboard } = useQuery({
    queryKey: ['test-execution-dashboard', cycleId, reportId],
    queryFn: async (): Promise<TestExecutionDashboard> => {
      const response = await apiClient.get(`/test-execution/${cycleId}/reports/${reportId}/dashboard`);
      return response.data;
    },
    enabled: !!cycleId && !!reportId,
  });

  // Fetch pending reviews
  const { data: pendingReviews = [], isLoading: pendingReviewsLoading } = useQuery({
    queryKey: ['test-execution-pending-reviews', cycleId, reportId],
    queryFn: async (): Promise<TestExecutionResponse[]> => {
      const response = await apiClient.get(`/test-execution/${cycleId}/reports/${reportId}/pending-review`);
      return response.data.executions;
    },
    enabled: !!cycleId && !!reportId,
  });

  // Fetch completion status
  const { data: completionStatus, isLoading: completionStatusLoading } = useQuery({
    queryKey: ['test-execution-completion-status', cycleId, reportId],
    queryFn: async () => {
      const response = await apiClient.get(`/test-execution/${cycleId}/reports/${reportId}/completion-status`);
      return response.data;
    },
    enabled: !!cycleId && !!reportId,
  });

  // Fetch configuration
  const { data: configuration } = useQuery({
    queryKey: ['test-execution-configuration'],
    queryFn: async () => {
      const response = await apiClient.get('/test-execution/configuration');
      return response.data;
    },
  });

  // Bulk execute test cases mutation
  const bulkExecuteMutation = useMutation({
    mutationFn: async (data: {
      test_case_ids: string[];
      execution_reason?: string;
      execution_method: string;
      configuration?: Record<string, any>;
    }) => {
      const response = await apiClient.post(`/test-execution/${cycleId}/reports/${reportId}/execute`, data);
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Started ${data.successful_executions} test executions`);
      if (data.failed_executions > 0) {
        toast.error(`${data.failed_executions} executions failed to start`);
      }
      refetchDashboard();
      setBulkExecuteDialogOpen(false);
      setSelectedTestCases([]);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start test executions');
    },
  });

  // Execute specific test case mutation
  const executeTestCaseMutation = useMutation({
    mutationFn: async (data: TestExecutionRequest) => {
      const response = await apiClient.post(`/test-execution/test-cases/${data.test_case_id}/execute`, data);
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('Test execution started successfully');
      refetchDashboard();
      setExecuteDialogOpen(false);
      setSelectedExecution(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start test execution');
    },
  });

  // Submit review mutation
  const submitReviewMutation = useMutation({
    mutationFn: async (data: { executionId: number; review: TestExecutionReviewRequest }) => {
      const response = await apiClient.post(`/test-execution/executions/${data.executionId}/review`, data.review);
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('Review submitted successfully');
      refetchDashboard();
      queryClient.invalidateQueries({ queryKey: ['test-execution-pending-reviews', cycleId, reportId] });
      setReviewDialogOpen(false);
      setSelectedExecution(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to submit review');
    },
  });

  // Complete phase mutation
  const completePhaseMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/test-execution/${cycleId}/reports/${reportId}/complete`);
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('Test execution phase completed successfully');
      refetchDashboard();
      queryClient.invalidateQueries({ queryKey: ['unified-status', cycleId, reportId] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to complete test execution phase');
    },
  });

  const handleExecuteTestCase = (testCaseId: string) => {
    setSelectedExecution({ test_case_id: testCaseId } as TestExecutionResponse);
    setExecuteDialogOpen(true);
  };

  const handleReviewExecution = (execution: TestExecutionResponse) => {
    setSelectedExecution(execution);
    setReviewDialogOpen(true);
  };

  const handleBulkExecute = () => {
    if (selectedTestCases.length === 0) {
      toast.error('Please select test cases to execute');
      return;
    }
    setBulkExecuteDialogOpen(true);
  };

  const handleConfirmBulkExecute = () => {
    bulkExecuteMutation.mutate({
      test_case_ids: selectedTestCases,
      execution_reason: 'initial',
      execution_method: executionMethod,
      configuration: {
        test_type: testType,
        analysis_method: analysisMethod,
      },
    });
  };

  const handleConfirmExecute = () => {
    if (!selectedExecution) return;

    executeTestCaseMutation.mutate({
      test_case_id: selectedExecution.test_case_id,
      evidence_id: selectedExecution.evidence_id || 1, // This should come from evidence selection
      execution_reason: 'initial',
      test_type: testType,
      analysis_method: analysisMethod,
      execution_method: executionMethod,
      configuration: {
        timeout_seconds: 300,
        retry_count: 3,
      },
    });
  };

  const handleConfirmReview = () => {
    if (!selectedExecution) return;

    submitReviewMutation.mutate({
      executionId: selectedExecution.id,
      review: reviewForm,
    });
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'success';
      case 'running': return 'info';
      case 'failed': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return <CheckCircle />;
      case 'running': return <Timer />;
      case 'failed': return <Error />;
      case 'pending': return <Assignment />;
      default: return <Info />;
    }
  };

  const getResultColor = (result?: string) => {
    switch (result?.toLowerCase()) {
      case 'pass': return 'success';
      case 'fail': return 'error';
      case 'inconclusive': return 'warning';
      default: return 'default';
    }
  };

  if (dashboardLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth={false} sx={{ py: 3 }}>
      {/* Dashboard Summary */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Science color="primary" />
            Test Execution Dashboard
          </Typography>
          
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary.main">
                    {dashboard?.summary.total_executions || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Executions
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main">
                    {dashboard?.summary.completed_executions || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Completed
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="warning.main">
                    {dashboard?.summary.pending_reviews || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Pending Reviews
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="info.main">
                    {Math.round(dashboard?.summary.completion_percentage || 0)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Completion
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Progress Bar */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Overall Progress
            </Typography>
            <LinearProgress
              variant="determinate"
              value={dashboard?.summary.completion_percentage || 0}
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Button
          variant="contained"
          startIcon={<PlayArrow />}
          onClick={handleBulkExecute}
          disabled={selectedTestCases.length === 0}
        >
          Execute Selected Tests
        </Button>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={() => refetchDashboard()}
        >
          Refresh
        </Button>
        {completionStatus?.can_complete && (
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

      {/* Completion Status Alert */}
      {completionStatus && !completionStatus.can_complete && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Phase Completion Requirements:
          </Typography>
          <ul>
            {completionStatus.completion_requirements.map((req: string, index: number) => (
              <li key={index}>{req}</li>
            ))}
          </ul>
          {completionStatus.blocking_issues.length > 0 && (
            <>
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 1 }}>
                Blocking Issues:
              </Typography>
              <ul>
                {completionStatus.blocking_issues.map((issue: string, index: number) => (
                  <li key={index}>{issue}</li>
                ))}
              </ul>
            </>
          )}
        </Alert>
      )}

      {/* Main Content Tabs */}
      <Card>
        <CardContent sx={{ p: 0 }}>
          <Tabs
            value={tabValue}
            onChange={(_, newValue) => setTabValue(newValue)}
            sx={{ borderBottom: 1, borderColor: 'divider', px: 3, pt: 2 }}
          >
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Assignment />
                  Recent Executions
                  <Chip
                    label={dashboard?.recent_executions.length || 0}
                    color="primary"
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Box>
              }
            />
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <RateReview />
                  Pending Reviews
                  <Chip
                    label={dashboard?.summary.pending_reviews || 0}
                    color="warning"
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Box>
              }
            />
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Analytics />
                  Analytics
                </Box>
              }
            />
          </Tabs>
        </CardContent>

        {/* Recent Executions Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Recent Test Executions
            </Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={() => refetchDashboard()}
            >
              Refresh
            </Button>
          </Box>

          {dashboard?.recent_executions.length === 0 ? (
            <Alert severity="info">
              No test executions found. Start executing tests to see results here.
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Test Case</TableCell>
                    <TableCell>Execution #</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Result</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell>Processing Time</TableCell>
                    <TableCell>Started</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dashboard?.recent_executions.map((execution) => (
                    <TableRow key={execution.id}>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {execution.test_case_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          #{execution.execution_number}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={execution.execution_status}
                          color={getStatusColor(execution.execution_status)}
                          icon={getStatusIcon(execution.execution_status)}
                        />
                      </TableCell>
                      <TableCell>
                        {execution.test_result ? (
                          <Chip
                            size="small"
                            label={execution.test_result}
                            color={getResultColor(execution.test_result)}
                            variant="outlined"
                          />
                        ) : (
                          <Typography variant="body2" color="text.secondary">-</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {execution.llm_confidence_score ? (
                          <Typography variant="body2">
                            {Math.round(execution.llm_confidence_score * 100)}%
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">-</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {execution.processing_time_ms ? `${execution.processing_time_ms}ms` : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {execution.started_at ? new Date(execution.started_at).toLocaleString() : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1}>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => setSelectedExecution(execution)}
                            >
                              <Visibility />
                            </IconButton>
                          </Tooltip>
                          {execution.execution_status === 'completed' && (
                            <Tooltip title="Review">
                              <IconButton
                                size="small"
                                onClick={() => handleReviewExecution(execution)}
                              >
                                <RateReview />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>

        {/* Pending Reviews Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Executions Pending Review
            </Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={() => queryClient.invalidateQueries({ queryKey: ['test-execution-pending-reviews'] })}
            >
              Refresh
            </Button>
          </Box>

          {pendingReviews.length === 0 ? (
            <Alert severity="info">
              No executions pending review. All completed executions have been reviewed.
            </Alert>
          ) : (
            <Stack spacing={2}>
              {pendingReviews.map((execution) => (
                <Card key={execution.id} variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="h6" gutterBottom>
                          {execution.test_case_id}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Execution #{execution.execution_number} • {execution.analysis_method}
                        </Typography>
                        <Typography variant="body2" gutterBottom>
                          Result: {execution.test_result || 'N/A'}
                        </Typography>
                        {execution.extracted_value && (
                          <Typography variant="body2" gutterBottom>
                            Extracted: {execution.extracted_value}
                          </Typography>
                        )}
                        {execution.llm_confidence_score && (
                          <Typography variant="body2" gutterBottom>
                            Confidence: {Math.round(execution.llm_confidence_score * 100)}%
                          </Typography>
                        )}
                        {execution.execution_summary && (
                          <Typography variant="body2" color="text.secondary">
                            {execution.execution_summary}
                          </Typography>
                        )}
                      </Box>
                      <Box sx={{ ml: 2 }}>
                        <Button
                          variant="contained"
                          startIcon={<RateReview />}
                          onClick={() => handleReviewExecution(execution)}
                        >
                          Review
                        </Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Stack>
          )}
        </TabPanel>

        {/* Analytics Tab */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Test Execution Analytics
          </Typography>
          
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Success Rate
                  </Typography>
                  <Typography variant="h3" color="success.main">
                    {Math.round(dashboard?.summary.success_rate || 0)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Based on {dashboard?.summary.completed_executions || 0} completed executions
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Average Processing Time
                  </Typography>
                  <Typography variant="h3" color="info.main">
                    {dashboard?.summary.average_processing_time_ms 
                      ? `${Math.round(dashboard.summary.average_processing_time_ms)}ms`
                      : 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Per execution average
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>

      {/* Review Dialog */}
      <Dialog open={reviewDialogOpen} onClose={() => setReviewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Review Test Execution</DialogTitle>
        <DialogContent>
          {selectedExecution && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Execution Details
                  </Typography>
                  <Typography variant="body2">
                    Test Case: {selectedExecution.test_case_id}
                  </Typography>
                  <Typography variant="body2">
                    Execution #{selectedExecution.execution_number}
                  </Typography>
                  <Typography variant="body2">
                    Result: {selectedExecution.test_result || 'N/A'}
                  </Typography>
                  {selectedExecution.extracted_value && (
                    <Typography variant="body2">
                      Extracted Value: {selectedExecution.extracted_value}
                    </Typography>
                  )}
                  {selectedExecution.llm_confidence_score && (
                    <Typography variant="body2">
                      Confidence: {Math.round(selectedExecution.llm_confidence_score * 100)}%
                    </Typography>
                  )}
                </CardContent>
              </Card>

              <FormControl fullWidth>
                <InputLabel>Review Status</InputLabel>
                <Select
                  value={reviewForm.review_status}
                  label="Review Status"
                  onChange={(e) => setReviewForm({ ...reviewForm, review_status: e.target.value })}
                >
                  <MenuItem value="approved">Approved</MenuItem>
                  <MenuItem value="rejected">Rejected</MenuItem>
                  <MenuItem value="requires_revision">Requires Revision</MenuItem>
                </Select>
              </FormControl>

              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Quality Assessment
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="body2" sx={{ minWidth: 100 }}>
                      Accuracy:
                    </Typography>
                    <Rating
                      value={reviewForm.accuracy_score}
                      onChange={(_, newValue) => setReviewForm({ ...reviewForm, accuracy_score: newValue || 0 })}
                      max={5}
                      precision={0.1}
                    />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="body2" sx={{ minWidth: 100 }}>
                      Completeness:
                    </Typography>
                    <Rating
                      value={reviewForm.completeness_score}
                      onChange={(_, newValue) => setReviewForm({ ...reviewForm, completeness_score: newValue || 0 })}
                      max={5}
                      precision={0.1}
                    />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="body2" sx={{ minWidth: 100 }}>
                      Consistency:
                    </Typography>
                    <Rating
                      value={reviewForm.consistency_score}
                      onChange={(_, newValue) => setReviewForm({ ...reviewForm, consistency_score: newValue || 0 })}
                      max={5}
                      precision={0.1}
                    />
                  </Box>
                </Box>
              </Box>

              <TextField
                fullWidth
                label="Review Notes"
                multiline
                rows={3}
                value={reviewForm.review_notes}
                onChange={(e) => setReviewForm({ ...reviewForm, review_notes: e.target.value })}
              />

              <TextField
                fullWidth
                label="Reviewer Comments"
                multiline
                rows={3}
                value={reviewForm.reviewer_comments}
                onChange={(e) => setReviewForm({ ...reviewForm, reviewer_comments: e.target.value })}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleConfirmReview}
            variant="contained"
            disabled={submitReviewMutation.isPending}
          >
            {submitReviewMutation.isPending ? 'Submitting...' : 'Submit Review'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default UnifiedTestExecutionManager;