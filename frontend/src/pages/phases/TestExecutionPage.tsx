import React, { useState } from 'react';
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
  Grid,
  Badge,
  Container,
  IconButton,
  Tooltip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Link,
} from '@mui/material';
import PhaseDocumentManager from '../../components/documents/PhaseDocumentManager';
import {
  Science,
  CheckCircle,
  PlayArrow,
  BugReport,
  Analytics,
  Assignment,
  Timer,
  TrendingUp,
  Assessment,
  Business,
  Person,
  CloudUpload,
  Visibility,
  GetApp,
  Description,
  Key,
  DataObject,
  Close,
  ExpandMore,
  ExpandLess,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import apiClient from '../../api/client';
import { usePhaseStatus, getStatusColor, formatStatusText } from '../../hooks/useUnifiedStatus';
import { useUniversalAssignments } from '../../hooks/useUniversalAssignments';
import { UniversalAssignmentAlert } from '../../components/UniversalAssignmentAlert';
import { DynamicActivityCards } from '../../components/phase/DynamicActivityCards';
import { ReportMetadataCard } from '../../components/common/ReportMetadataCard';
// import WorkflowProgress from '../../components/WorkflowProgress';
import EnhancedTestExecution from '../../components/testing/EnhancedTestExecution';
import { TestExecutionTable } from '../../components/test-execution/TestExecutionTable';

// Types for Test Execution phase
interface TestExecutionPhaseStatus {
  phase_status: string;
  total_attributes?: number;
  scoped_attributes?: number;
  total_samples?: number;
  total_lobs?: number;
  total_data_providers?: number;
  tested_test_cases?: number;
  complete_test_cases?: number;
  started_at?: string;
}

interface SubmittedTestCase {
  id: number;
  test_case_id: number;
  test_name: string;
  attribute_id: number;
  attribute_name: string;
  data_type?: string;
  data_owner_id: number;
  data_owner_name: string;
  status: string;
  has_evidence: boolean;
  evidence_count: number;
  document_count: number;
  created_at?: string;
  updated_at?: string;
  
  // Additional fields that might be present
  submission_id?: string;
  phase_id?: string;
  cycle_id?: number;
  report_id?: number;
  sample_record_id?: string;
  sample_identifier?: string;
  primary_key_values?: Record<string, any>;
  submission_type?: string;
  evidence_uploaded?: boolean;
  document_ids?: string[];
  expected_value?: string;
  retrieved_value?: string;
  confidence_level?: string;
  notes?: string;
  validation_status?: string;
  validation_messages?: string[];
  submitted_at?: string;
  validated_at?: string;
  last_updated_at?: string;
  evidence_submissions?: any[];
  sample_value?: string;
  is_scoped?: boolean;
  evidence_type?: string;
}

interface TestExecution {
  execution_id: number;
  sample_record_id: string;
  attribute_id: number;
  status: string;
  result?: string;
  retrieved_value?: string;
  confidence_score?: number;
  started_at?: string;
  completed_at?: string;
  processing_time_ms?: number;
  error_message?: string;
}

interface ReportInfo {
  report_id: number;
  report_name: string;
  lob: string;
  assigned_tester?: string;
  report_owner?: string;
  description?: string;
  regulatory_framework?: string;
  frequency?: string;
  due_date?: string;
  priority?: string;
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
      id={`testing-tabpanel-${index}`}
      aria-labelledby={`testing-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const TestExecutionPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const queryClient = useQueryClient();
  
  // State management
  const [tabValue, setTabValue] = useState(0);
  const [selectedCycleId] = useState<number>(cycleId ? parseInt(cycleId) : 9);
  const [selectedReportId] = useState<number>(reportId ? parseInt(reportId) : 156);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [selectedTestCase, setSelectedTestCase] = useState<SubmittedTestCase | null>(null);
  const [selectedTestCaseId, setSelectedTestCaseId] = useState<string | null>(null);
  const [expandedSamples, setExpandedSamples] = useState<Set<string>>(new Set());

  // Unified status hook
  const { data: unifiedPhaseStatus, isLoading: statusLoading, refetch: refetchStatus } = usePhaseStatus('Test Execution', selectedCycleId, selectedReportId);

  // Universal Assignments integration
  const {
    assignments,
    isLoading: assignmentsLoading,
    acknowledgeAssignment,
    startAssignment,
    completeAssignment,
  } = useUniversalAssignments({
    phase: 'Testing',
    cycleId: selectedCycleId,
    reportId: selectedReportId,
  });

  // Fetch report info with cycle context for complete metadata
  const { data: reportInfo, isLoading: reportInfoLoading } = useQuery({
    queryKey: ['report-info', selectedCycleId, selectedReportId],
    queryFn: async () => {
      try {
        // Get cycle report info which has all the metadata
        const response = await apiClient.get(`/cycle-reports/${selectedCycleId}/reports/${selectedReportId}`);
        const data = response.data;
        
        // Map to expected format
        return {
          report_id: data.report_id,
          report_name: data.report_name,
          lob: data.lob_name || 'Unknown',
          assigned_tester: data.tester_name || 'Not assigned',
          report_owner: data.report_owner_name || 'Not specified',
          description: data.description,
          regulation: data.regulation,
          frequency: data.frequency,
        };
      } catch (error) {
        console.error('Error loading report info:', error);
        // Fallback to basic info
        return {
          report_id: selectedReportId,
          report_name: 'Loading...',
          lob: 'Unknown',
          assigned_tester: 'Not assigned',
          report_owner: 'Not specified'
        };
      }
    },
    enabled: !!selectedCycleId && !!selectedReportId,
  });

  // Metrics are now provided by unifiedPhaseStatus
  const metricsData = {};

  // Fetch submitted test cases from Request Info phase (only when phase is started)
  const { data: submittedTestCasesResponse, isLoading: loadingTestCases, error: testCasesError } = useQuery({
    queryKey: ['test-execution', 'submitted-test-cases', selectedCycleId, selectedReportId],
    queryFn: async () => {
      const response = await apiClient.get(`/test-execution/${selectedCycleId}/reports/${selectedReportId}/submitted-test-cases`);
      console.log('Loaded submitted test cases:', response.data);
      return response.data;
    },
    enabled: !!selectedCycleId && !!selectedReportId && unifiedPhaseStatus?.phase_status !== 'not_started',
  });
  
  // Extract test_cases array from response
  const submittedTestCases = submittedTestCasesResponse?.test_cases || [];

  // Fetch test execution results
  const { data: testExecutions = [], isLoading: loadingExecutions, refetch: refetchExecutions } = useQuery({
    queryKey: ['test-execution', 'executions', selectedCycleId, selectedReportId],
    queryFn: async () => {
      const response = await apiClient.get(`/test-execution/${selectedCycleId}/reports/${selectedReportId}/executions`);
      return response.data;
    },
    enabled: !!selectedCycleId && !!selectedReportId,
    staleTime: 0, // Always refetch to get latest data
    refetchInterval: 5000, // Refresh every 5 seconds to check for updates
  });

  // Start test execution phase mutation
  const startPhaseMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/test-execution/${selectedCycleId}/reports/${selectedReportId}/start`, {
        testing_deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days from now
        test_strategy: "Comprehensive testing of submitted documents and database validation",
        instructions: "Execute tests for all submitted test cases and validate against expected values",
        notes: "Test execution phase started automatically"
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phaseStatus'] });
      refetchStatus();
      toast.success('Test Execution phase started successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start Test Execution phase');
    },
  });


  // Event handlers
  const handleStartTest = async (testCase: SubmittedTestCase) => {
    console.log('Starting test for test case:', testCase);
    
    // Directly execute the test without showing dialog
    try {
      // Check if we have evidence
      if (!testCase.has_evidence || testCase.evidence_count === 0) {
        toast.error('No evidence found for this test case');
        return;
      }
      
      // Find the current evidence from evidence_submissions
      let evidenceId = 1; // Default fallback
      let evidenceType = 'document'; // Default fallback
      if (testCase.evidence_submissions && testCase.evidence_submissions.length > 0) {
        // Find the current evidence (is_current = true) or use the first one
        const currentEvidence = testCase.evidence_submissions.find((ev: any) => ev.is_current) || testCase.evidence_submissions[0];
        evidenceId = currentEvidence.evidence_id || currentEvidence.id;
        evidenceType = currentEvidence.evidence_type || 'document';
        console.log('Using evidence ID:', evidenceId, 'from evidence:', currentEvidence);
      }
      
      // Check if this is a retry
      const execution = getTestExecution(testCase);
      const isRetry = execution && (execution.status === 'failed' || execution.result === 'fail');
      
      // Determine test type based on evidence type
      const testType = evidenceType === 'data_source' ? 'database_test' : 'document_analysis';
      const analysisMethod = evidenceType === 'data_source' ? 'database_query' : 'llm_analysis';
      
      // Create test execution request with actual evidence ID
      const testData = {
        test_case_id: String(testCase.id || testCase.test_case_id),
        evidence_id: Number(evidenceId),
        execution_reason: isRetry ? "retry" : "initial",
        test_type: testType,
        analysis_method: analysisMethod,
        execution_method: 'automatic',
        configuration: {
          priority: 'normal',
          timeout_seconds: 300,
          retry_count: 3
        },
        processing_notes: isRetry 
          ? `Retry execution for ${testCase.attribute_name} after previous failure`
          : `Manual execution requested for ${testCase.attribute_name}`
      };
      
      console.log('Executing test with data:', testData);
      
      // First, let's try to get the test case details with evidence from the backend
      try {
        // Call the bulk execution endpoint instead, which handles evidence lookup better
        const bulkResponse = await apiClient.post(
          `/test-execution/${selectedCycleId}/reports/${selectedReportId}/execute`,
          {
            test_case_ids: [String(testCase.id || testCase.test_case_id)],
            execution_reason: isRetry ? "retry" : "initial",
            execution_method: 'automatic',
            configuration: {
              priority: 'normal',
              timeout_seconds: 300,
              retry_count: 3
            }
          }
        );
        
        console.log('Test execution started successfully:', bulkResponse.data);
        
        if (bulkResponse.data.successful_executions > 0) {
          toast.success('Test execution started successfully');
        } else if (bulkResponse.data.errors?.length > 0) {
          toast.error(bulkResponse.data.errors[0].error || 'Failed to start test execution');
        }
      } catch (bulkError: any) {
        // Log the bulk execution error details
        console.error('Bulk execution failed:', bulkError.response?.data);
        
        // If bulk execution fails, try the individual endpoint
        console.log('Bulk execution failed, trying individual endpoint');
        const response = await apiClient.post(
          `/test-execution/test-cases/${testCase.id || testCase.test_case_id}/execute`, 
          testData
        );
        
        console.log('Test execution started successfully:', response.data);
        toast.success('Test execution started successfully');
      }
      
      queryClient.invalidateQueries({ queryKey: ['test-execution', 'executions', selectedCycleId, selectedReportId] });
      
      // Refresh the executions after a short delay to see the update
      setTimeout(() => {
        refetchExecutions();
      }, 2000);
    } catch (error: any) {
      console.error('Test execution failed:', error);
      // Show more detailed error message
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to start test execution';
      toast.error(errorMessage);
      
      // Log the full error for debugging
      if (error.response?.data) {
        console.error('Error details:', error.response.data);
      }
    }
  };

  const handleViewDetails = (testCase: SubmittedTestCase) => {
    setSelectedTestCase(testCase);
    setDetailDialogOpen(true);
  };


  const handleDownloadDocument = (documentId: string) => {
    // Simulate document download
    toast.success(`Downloading document ${documentId}`);
  };

  const toggleSampleExpansion = (sampleId: string) => {
    const newExpanded = new Set(expandedSamples);
    if (newExpanded.has(sampleId)) {
      newExpanded.delete(sampleId);
    } else {
      newExpanded.add(sampleId);
    }
    setExpandedSamples(newExpanded);
  };

  const handleActivityAction = async (activity: any, action: string) => {
    try {
      // Make the API call to start/complete the activity
      const endpoint = action === 'start' ? 'start' : 'complete';
      const response = await apiClient.post(`/activity-management/activities/${activity.activity_id}/${endpoint}`, {
        cycle_id: selectedCycleId,
        report_id: selectedReportId,
        phase_name: 'Test Execution'
      });
      
      // Show success message from backend or default
      const message = response.data.message || activity.metadata?.success_message || `${action === 'start' ? 'Started' : 'Completed'} ${activity.name}`;
      toast.success(message);
      
      // Special handling for phase_start activities - immediately complete them
      if (action === 'start' && activity.metadata?.activity_type === 'phase_start') {
        console.log('Auto-completing phase_start activity:', activity.name);
        await new Promise(resolve => setTimeout(resolve, 200));
        
        try {
          await apiClient.post(`/activity-management/activities/${activity.activity_id}/complete`, {
            cycle_id: selectedCycleId,
            report_id: selectedReportId,
            phase_name: 'Test Execution'
          });
          toast.success(`${activity.name} completed`);
        } catch (completeError: any) {
          // Ignore "already completed" errors

          if (completeError.response?.status === 400 && 

              completeError.response?.data?.detail?.includes('Cannot complete activity in status')) {

            console.log('Phase start activity already completed, ignoring error');

          } else {

            console.error('Error auto-completing phase_start activity:', completeError);

          }
        }
      }
      
      // Add a small delay to ensure backend has processed the change
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Force refresh of both status systems
      refetchStatus();
      queryClient.invalidateQueries({ queryKey: ['phaseStatus', 'Test Execution', selectedCycleId, selectedReportId] });
      queryClient.invalidateQueries({ queryKey: ['unified-status', selectedCycleId, selectedReportId] });
    } catch (error: any) {
      console.error('Error handling activity action:', error);
      toast.error(error.response?.data?.detail || `Failed to ${action} activity`);
    }
  };

  const getTestExecution = (testCase: SubmittedTestCase | any): TestExecution | undefined => {
    // Try multiple ways to match test execution with test case
    return testExecutions.find((exec: any) => {
      // Match by test_case_id (handle both string and number)
      const testCaseId = typeof testCase.test_case_id === 'string' 
        ? testCase.test_case_id 
        : String(testCase.test_case_id || testCase.id);
      
      const testCaseIdMatch = exec.test_case_id && (
        exec.test_case_id === testCaseId ||
        exec.test_case_id === String(testCase.id) ||
        exec.test_case_id === `tc_${testCase.id}` ||
        exec.test_case_id === `tc_${testCaseId}`
      );
      
      // Legacy match by sample_record_id and attribute_id
      const legacyMatch = exec.sample_record_id === testCase.sample_record_id && 
                         exec.attribute_id === testCase.attribute_id;
      
      // Match by sample_id and attribute_id
      const sampleMatch = (exec.sample_id === testCase.sample_identifier || 
                          exec.sample_id === testCase.sample_record_id) &&
                         exec.attribute_id === testCase.attribute_id;
      
      return testCaseIdMatch || legacyMatch || sampleMatch;
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed': return 'success';
      case 'Running': return 'info';
      case 'Failed': return 'error';
      case 'Pending': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Completed': return <CheckCircle />;
      case 'Running': return <Timer />;
      case 'Failed': return <BugReport />;
      default: return <Assignment />;
    }
  };

  const getResultColor = (result?: string) => {
    switch (result) {
      case 'Pass': return 'success';
      case 'Fail': return 'error';
      case 'Inconclusive': return 'warning';
      default: return 'default';
    }
  };

  // Calculate summary metrics
  const testingSummary = {
    totalSubmitted: submittedTestCases?.length || 0,
    testsCompleted: testExecutions.filter((exec: TestExecution) => exec.status === 'Completed').length,
    testsPassed: testExecutions.filter((exec: TestExecution) => exec.result === 'Pass').length,
    testsFailed: testExecutions.filter((exec: TestExecution) => exec.result === 'Fail').length,
    testsInconclusive: testExecutions.filter((exec: TestExecution) => exec.result === 'Inconclusive').length,
    averageConfidence: testExecutions.length > 0 
      ? testExecutions.reduce((sum: number, exec: TestExecution) => sum + (exec.confidence_score || 0), 0) / testExecutions.length 
      : 0,
  };


  return (
    <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
      {/* Universal Assignments Alert */}
      {assignments.length > 0 && assignments[0] && (
        <UniversalAssignmentAlert
          assignment={assignments[0]}
          onAcknowledge={acknowledgeAssignment}
          onStart={startAssignment}
          onComplete={completeAssignment}
        />
      )}
      
      {/* Workflow Progress */}
      {/* Workflow Progress - Removed as it doesn't belong on phase detail pages */}
      
      {/* Report Information Header */}
      <Card sx={{ mb: 3, mt: 3 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            {/* Left side - Report title */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Science color="primary" />
              <Box>
                <Typography variant="h6" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportInfo?.report_name || 'Loading...'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Testing Phase - Execute comprehensive testing on submitted data and evidence
                </Typography>
              </Box>
            </Box>
            
            {/* Right side - Key metadata in compact format */}
            <ReportMetadataCard
              metadata={reportInfo ?? null}
              loading={reportInfoLoading}
              variant="compact"
              showFields={['lob', 'tester', 'owner']}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Test Execution Metrics Row 1 - Six Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="primary.main" fontWeight="bold">
                {unifiedPhaseStatus?.metadata?.total_attributes || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Attributes
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="success.main" fontWeight="bold">
                {unifiedPhaseStatus?.metadata?.scoped_attributes || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Scoped Attributes
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="info.main" fontWeight="bold">
                {unifiedPhaseStatus?.metadata?.total_samples || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Samples
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="warning.main" fontWeight="bold">
                {unifiedPhaseStatus?.metadata?.total_lobs || 0}/{unifiedPhaseStatus?.metadata?.total_data_providers || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                LOBs / Data Owners
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="error.main" fontWeight="bold">
                {testingSummary.testsCompleted}/{testingSummary.totalSubmitted}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Test Cases (Tested/Complete)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="primary.main" fontWeight="bold">
                {(() => {
                  const startDate = unifiedPhaseStatus?.metadata?.started_at;
                  const completedDate = unifiedPhaseStatus?.metadata?.completed_at;
                  if (!startDate) return 0;
                  const end = completedDate ? new Date(completedDate) : new Date();
                  const start = new Date(startDate);
                  return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
                })()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {unifiedPhaseStatus?.metadata?.completed_at ? 'Completion Time (days)' : 'Days Elapsed'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Row 2: On-Time Status + Phase Controls */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 6 }}>
          <Card sx={{ height: 100 }}>
            <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <Typography 
                variant="h3" 
                color="primary.main"
                component="div"
                sx={{ fontSize: '1.5rem' }}
              >
                On Track
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Current Schedule Status
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ height: 100 }}>
            <CardContent sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" sx={{ fontSize: '1rem' }}>
                  Phase Controls
                </Typography>
                
                {/* Status Update Controls */}
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip
                    label="At Risk"
                    size="small"
                    color="warning"
                    variant="outlined"
                    clickable
                    onClick={() => {/* Handle status update */}}
                    sx={{ fontSize: '0.7rem' }}
                  />
                  <Chip
                    label="Off Track"
                    size="small"
                    color="error"
                    variant="outlined"
                    clickable
                    onClick={() => {/* Handle status update */}}
                    sx={{ fontSize: '0.7rem' }}
                  />
                </Box>
              </Box>
              
              {/* Completion Requirements */}
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                  To complete: Execute and complete all test cases
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>


      {/* Test Execution Workflow Visual */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Science color="primary" />
            Test Execution Phase Workflow
          </Typography>
          
          <Box sx={{ mt: 2 }}>
            {unifiedPhaseStatus?.activities ? (
              <DynamicActivityCards
                activities={unifiedPhaseStatus.activities}
                cycleId={selectedCycleId}
                reportId={selectedReportId}
                phaseName="Test Execution"
                onActivityAction={handleActivityAction}
                phaseStatus={unifiedPhaseStatus.phase_status}
                overallCompletion={unifiedPhaseStatus.overall_completion_percentage}
              />
            ) : (
              <Box sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                minHeight: 200, 
                flexDirection: 'column', 
                gap: 2 
              }}>
                <CircularProgress />
                <Typography variant="body2" color="text.secondary">
                  Loading test execution activities...
                </Typography>
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>

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
                  Test Cases
                  <Chip 
                    label={submittedTestCases?.length || 0} 
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
                  <BugReport />
                  Executions
                  <Chip 
                    label={testExecutions.length} 
                    color="secondary" 
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
            <Tab 
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Description />
                  Documents
                </Box>
              } 
            />
          </Tabs>
        </CardContent>

        {/* Test Cases Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Submitted Test Cases ({submittedTestCases?.length || 0})
            </Typography>
            
            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                size="small"
                disabled
              >
                Export
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => queryClient.invalidateQueries({ queryKey: ['test-execution'] })}
              >
                Refresh
              </Button>
            </Stack>
          </Box>

          {unifiedPhaseStatus?.phase_status === 'not_started' ? (
            <Alert severity="info">
              Test Execution phase has not been started yet. Click "Start Test Execution Phase" above to begin loading test cases.
            </Alert>
          ) : loadingTestCases ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : testCasesError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              Failed to load test cases: {testCasesError.message}
            </Alert>
          ) : !submittedTestCases || submittedTestCases.length === 0 ? (
            <Alert severity="info">
              No submitted test cases found. Test cases will appear here after data providers submit evidence in the Request for Information phase.
            </Alert>
          ) : (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Test cases submitted by data providers with supporting documentation. Ready for test execution and validation.
              </Typography>
              
              <TestExecutionTable
                testCases={submittedTestCases.map((tc: any) => {
                  const execution = getTestExecution(tc);
                  return {
                    ...tc,
                    test_case_id: String(tc.submission_id || tc.test_case_id || tc.id),
                    sample_id: tc.sample_identifier || tc.sample_record_id || tc.sample_id,
                    sample_identifier: tc.sample_identifier || tc.sample_record_id || tc.sample_id,
                    primary_key_attributes: tc.primary_key_values,
                    primary_key_values: tc.primary_key_values,
                    sample_value: tc.expected_value || tc.sample_value,
                    expected_value: tc.expected_value || tc.sample_value,
                    execution_status: execution?.status?.toLowerCase(),
                    execution_id: execution?.execution_id,
                    extracted_value: execution?.retrieved_value || (execution as any)?.extracted_value,
                    test_result: execution?.result?.toLowerCase() || (execution as any)?.test_result,
                    confidence_score: execution?.confidence_score,
                    executed_at: execution?.completed_at,
                    analysis_results: (execution as any)?.analysis_results || {},
                    analysis_rationale: (execution as any)?.llm_analysis_rationale,
                  };
                })}
                onExecuteTest={(testCase) => {
                  // Check if test already has an execution
                  const execution = getTestExecution(testCase);
                  
                  // Only prevent re-execution if the test is currently running or completed successfully
                  if (execution && execution.status === 'running') {
                    toast('This test is currently being executed. Please wait for it to complete.', {
                      icon: '⏳',
                    });
                    return;
                  }
                  
                  if (execution && execution.status === 'completed' && execution.result !== 'fail') {
                    toast('This test has already been executed successfully. View results in the comparison view.', {
                      icon: '✅',
                    });
                    return;
                  }
                  
                  // Allow re-execution for failed tests
                  if (execution && (execution.status === 'failed' || execution.result === 'fail')) {
                    console.log('Retrying failed test execution');
                  }
                  
                  const originalTestCase = submittedTestCases.find((tc: any) => 
                    String(tc.submission_id || tc.test_case_id || tc.id) === testCase.test_case_id
                  );
                  if (originalTestCase) {
                    handleStartTest(originalTestCase);
                  }
                }}
                onViewEvidence={(testCase) => {
                  setSelectedTestCaseId(testCase.test_case_id);
                  setDetailDialogOpen(true);
                }}
                onViewComparison={(testCase) => {
                  // View comparison is handled by the table component itself
                }}
                onReviewResult={async (testCase, decision) => {
                  try {
                    const response = await apiClient.post(
                      `/test-execution/executions/${testCase.execution_id}/review`,
                      {
                        review_status: decision === 'pass' ? 'approved' : decision === 'fail' ? 'rejected' : 'requires_revision',
                        review_notes: `Test ${decision === 'pass' ? 'passed' : decision === 'fail' ? 'failed' : 'requires additional information'}`,
                        recommended_action: decision === 'resend' ? 'retest' : 'approve',
                      }
                    );
                    
                    toast.success(`Test case ${decision === 'pass' ? 'passed' : decision === 'fail' ? 'failed' : 'sent for revision'}`);
                    queryClient.invalidateQueries({ queryKey: ['test-execution'] });
                    refetchExecutions();
                  } catch (error: any) {
                    toast.error(error.response?.data?.detail || 'Failed to submit review');
                  }
                }}
                userRole={user?.role}
              />
            </Box>
          )}
        </TabPanel>

        {/* Executions Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Test Executions ({testExecutions.length})
            </Typography>
            
            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                size="small"
                disabled
              >
                Export Results
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => queryClient.invalidateQueries({ queryKey: ['test-execution', 'executions'] })}
              >
                Refresh
              </Button>
            </Stack>
          </Box>

          {loadingExecutions ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : testExecutions.length === 0 ? (
            <Alert severity="info">
              No test executions found. Start executing tests from the Test Cases tab.
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined" sx={{ overflowX: 'auto' }}>
              <Table sx={{ width: '100%' }}>
                <TableHead>
                  <TableRow>
                    <TableCell>Sample ID</TableCell>
                    <TableCell>Attribute</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Result</TableCell>
                    <TableCell>Extracted Value</TableCell>
                    <TableCell>Expected Value</TableCell>
                    <TableCell>Match</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell>Processing Time</TableCell>
                    <TableCell>Started</TableCell>
                    <TableCell>Completed</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {testExecutions.map((execution: TestExecution) => (
                    <TableRow key={execution.execution_id}>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {execution.sample_record_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          Attribute {execution.attribute_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={execution.status}
                          color={getStatusColor(execution.status)}
                          variant="filled"
                          icon={getStatusIcon(execution.status)}
                        />
                      </TableCell>
                      <TableCell>
                        {execution.result ? (
                          <Chip
                            size="small"
                            label={execution.result}
                            color={getResultColor(execution.result)}
                            variant="outlined"
                          />
                        ) : (
                          <Typography variant="body2" color="text.secondary">-</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', color: 'success.main' }}>
                          {(() => {
                            if (!execution.retrieved_value) return '-';
                            // Extract just the dollar amount from messages like "LLM extracted '$15,000' with confidence..."
                            const match = execution.retrieved_value.match(/\$[\d,]+/);
                            return match ? match[0] : execution.retrieved_value;
                          })()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', color: 'primary.main' }}>
                          {(() => {
                            // Find the corresponding test case for this execution to get expected value
                            const testCase = (submittedTestCases || []).find((tc: any) => 
                              tc.sample_record_id == execution.sample_record_id && 
                              tc.attribute_id == execution.attribute_id
                            );
                            return testCase?.expected_value || testCase?.sample_value || '-';
                          })()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {(() => {
                          if (!execution.retrieved_value) return '-';
                          const extractedMatch = execution.retrieved_value.match(/\$[\d,]+/);
                          const extractedValue = extractedMatch ? extractedMatch[0] : execution.retrieved_value;
                          
                          const testCase = (submittedTestCases || []).find((tc: any) => 
                            tc.sample_record_id == execution.sample_record_id && 
                            tc.attribute_id == execution.attribute_id
                          );
                          const expectedValue = testCase?.expected_value || testCase?.sample_value;
                          
                          if (!expectedValue) return '-';
                          
                          const isMatch = extractedValue === expectedValue;
                          return (
                            <Chip
                              size="small"
                              label={isMatch ? "Match" : "No Match"}
                              color={isMatch ? "success" : "error"}
                              variant="outlined"
                              icon={isMatch ? <CheckCircle fontSize="small" /> : <Close fontSize="small" />}
                            />
                          );
                        })()}
                      </TableCell>
                      <TableCell>
                        {execution.confidence_score ? (
                          <Typography variant="body2">
                            {Math.round(execution.confidence_score * 100)}%
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">-</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {execution.processing_time_ms ? (
                          <Typography variant="body2">
                            {execution.processing_time_ms}ms
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">-</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {execution.started_at ? new Date(execution.started_at).toLocaleString() : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {execution.completed_at ? new Date(execution.completed_at).toLocaleString() : '-'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>

        {/* Analytics Tab */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Testing Analytics
          </Typography>
          
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Execution Summary
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography>Total Submitted:</Typography>
                      <Typography fontWeight="bold">{testingSummary.totalSubmitted}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography>Tests Completed:</Typography>
                      <Typography fontWeight="bold" color="success.main">{testingSummary.testsCompleted}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography>Success Rate:</Typography>
                      <Typography fontWeight="bold" color="primary.main">
                        {testingSummary.testsCompleted > 0 
                          ? Math.round((testingSummary.testsPassed / testingSummary.testsCompleted) * 100)
                          : 0}%
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography>Average Confidence:</Typography>
                      <Typography fontWeight="bold" color="info.main">
                        {Math.round(testingSummary.averageConfidence * 100)}%
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Metrics
                  </Typography>
                  <Alert severity="info">
                    Detailed analytics will be available as more tests are executed.
                  </Alert>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>


        {/* Documents Tab */}
        <TabPanel value={tabValue} index={3}>
          <Box sx={{ p: 3 }}>
            <PhaseDocumentManager
              cycleId={selectedCycleId}
              reportId={selectedReportId}
              phaseId={6} // Test Execution phase ID
              phaseName="Test Execution"
              allowedDocumentTypes={[
                'report_sample_data',
                'report_underlying_transaction_data',
                'report_source_transaction_data',
                'report_source_document'
              ]}
              requiredDocumentTypes={[
                'report_sample_data',
                'report_underlying_transaction_data'
              ]}
              title="Test Execution Documents"
            />
          </Box>
        </TabPanel>
      </Card>


      {/* Detail Dialog */}
      <Dialog open={detailDialogOpen} onClose={() => setDetailDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6">Test Case Details</Typography>
          <IconButton onClick={() => setDetailDialogOpen(false)}>
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedTestCase && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {/* Basic Information */}
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Assignment color="primary" />
                    Basic Information
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Typography variant="body2" color="text.secondary">Sample ID</Typography>
                      <Typography variant="body1" fontWeight="medium" fontFamily="monospace">
                        {selectedTestCase.sample_record_id}
                      </Typography>
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Typography variant="body2" color="text.secondary">Attribute</Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {selectedTestCase.attribute_name}
                      </Typography>
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Typography variant="body2" color="text.secondary">Data Type</Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {selectedTestCase.data_type || 'Unknown'}
                      </Typography>
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Typography variant="body2" color="text.secondary">Data Owner</Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {selectedTestCase.data_owner_name}
                      </Typography>
                    </Grid>
                    {/* Attribute description removed as it's not in the API response */}
                  </Grid>
                </CardContent>
              </Card>

              {/* Primary Key Values */}
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Key color="primary" />
                    Primary Key Values
                  </Typography>
                  <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                    <Grid container spacing={2}>
                      {Object.entries(selectedTestCase.primary_key_values || {}).map(([key, value]) => (
                        <Grid key={key} size={{ xs: 12, sm: 6, md: 4 }}>
                          <Typography variant="body2" color="text.secondary">{key}</Typography>
                          <Typography variant="body1" fontWeight="medium" fontFamily="monospace">
                            {String(value)}
                          </Typography>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                </CardContent>
              </Card>

              {/* Expected vs Retrieved Values */}
              {(selectedTestCase.expected_value || selectedTestCase.retrieved_value) && (
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <DataObject color="info" />
                      Data Values
                    </Typography>
                    <Grid container spacing={2}>
                      {selectedTestCase.expected_value && (
                        <Grid size={{ xs: 12, md: 6 }}>
                          <Typography variant="body2" color="text.secondary">Expected Value</Typography>
                          <Box sx={{ bgcolor: 'info.50', p: 1.5, borderRadius: 1, border: 1, borderColor: 'info.main' }}>
                            <Typography variant="body1" fontFamily="monospace">
                              {selectedTestCase.expected_value}
                            </Typography>
                          </Box>
                        </Grid>
                      )}
                      {selectedTestCase.retrieved_value && (
                        <Grid size={{ xs: 12, md: 6 }}>
                          <Typography variant="body2" color="text.secondary">Retrieved Value</Typography>
                          <Box sx={{ bgcolor: 'success.50', p: 1.5, borderRadius: 1, border: 1, borderColor: 'success.main' }}>
                            <Typography variant="body1" fontFamily="monospace">
                              {selectedTestCase.retrieved_value}
                            </Typography>
                          </Box>
                        </Grid>
                      )}
                    </Grid>
                  </CardContent>
                </Card>
              )}

              {/* Evidence Documents */}
              {selectedTestCase.has_evidence && selectedTestCase.evidence_count && selectedTestCase.evidence_count > 0 && (
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Description color="success" />
                      Evidence Documents ({selectedTestCase.document_ids?.length || 0})
                    </Typography>
                    <List>
                      {selectedTestCase.document_ids?.map((docId: string, index: number) => (
                        <ListItem key={docId} sx={{ bgcolor: 'success.50', mb: 1, borderRadius: 1 }}>
                          <ListItemIcon>
                            <Description color="success" />
                          </ListItemIcon>
                          <ListItemText 
                            primary={`Document ${index + 1}`}
                            secondary={`Document ID: ${docId}`}
                          />
                          <Tooltip title="Download Document">
                            <IconButton
                              onClick={() => handleDownloadDocument(docId)}
                              sx={{ color: 'primary.main' }}
                            >
                              <GetApp />
                            </IconButton>
                          </Tooltip>
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              )}

              {/* Submission Information */}
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CloudUpload color="secondary" />
                    Submission Information
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Typography variant="body2" color="text.secondary">Submission Type</Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {selectedTestCase.submission_type}
                      </Typography>
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Typography variant="body2" color="text.secondary">Status</Typography>
                      <Chip 
                        label={selectedTestCase.status}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </Grid>
                    {selectedTestCase.submitted_at && (
                      <Grid size={{ xs: 12, md: 6 }}>
                        <Typography variant="body2" color="text.secondary">Submitted At</Typography>
                        <Typography variant="body1" fontWeight="medium">
                          {new Date(selectedTestCase.submitted_at).toLocaleString()}
                        </Typography>
                      </Grid>
                    )}
                    {selectedTestCase.confidence_level && (
                      <Grid size={{ xs: 12, md: 6 }}>
                        <Typography variant="body2" color="text.secondary">Confidence Level</Typography>
                        <Typography variant="body1" fontWeight="medium">
                          {selectedTestCase.confidence_level}
                        </Typography>
                      </Grid>
                    )}
                    {selectedTestCase.notes && (
                      <Grid size={{ xs: 12 }}>
                        <Typography variant="body2" color="text.secondary">Notes</Typography>
                        <Box sx={{ bgcolor: 'grey.50', p: 1.5, borderRadius: 1, mt: 0.5 }}>
                          <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                            {selectedTestCase.notes}
                          </Typography>
                        </Box>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>

              {/* Validation Information */}
              {(selectedTestCase.validation_status || selectedTestCase.validation_messages?.length) && (
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CheckCircle color="warning" />
                      Validation Information
                    </Typography>
                    <Grid container spacing={2}>
                      {selectedTestCase.validation_status && (
                        <Grid size={{ xs: 12, md: 6 }}>
                          <Typography variant="body2" color="text.secondary">Validation Status</Typography>
                          <Typography variant="body1" fontWeight="medium">
                            {selectedTestCase.validation_status}
                          </Typography>
                        </Grid>
                      )}
                      {selectedTestCase.validated_at && (
                        <Grid size={{ xs: 12, md: 6 }}>
                          <Typography variant="body2" color="text.secondary">Validated At</Typography>
                          <Typography variant="body1" fontWeight="medium">
                            {new Date(selectedTestCase.validated_at).toLocaleString()}
                          </Typography>
                        </Grid>
                      )}
                      {selectedTestCase.validation_messages?.length && (
                        <Grid size={{ xs: 12 }}>
                          <Typography variant="body2" color="text.secondary">Validation Messages</Typography>
                          <Box sx={{ bgcolor: 'warning.50', p: 1.5, borderRadius: 1, mt: 0.5 }}>
                            {selectedTestCase.validation_messages.map((message, index) => (
                              <Typography key={index} variant="body2" sx={{ mb: 0.5 }}>
                                • {message}
                              </Typography>
                            ))}
                          </Box>
                        </Grid>
                      )}
                    </Grid>
                  </CardContent>
                </Card>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)} variant="outlined">
            Close
          </Button>
          {selectedTestCase && !getTestExecution(selectedTestCase) && (
            <Button 
              onClick={() => {
                setDetailDialogOpen(false);
                handleStartTest(selectedTestCase);
              }} 
              variant="contained"
              startIcon={<PlayArrow />}
              disabled={!selectedTestCase.evidence_uploaded}
            >
              Start Test
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TestExecutionPage; 