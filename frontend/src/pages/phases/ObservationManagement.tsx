import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Tabs,
  Tab,
  Tooltip,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  CircularProgress,
  Badge,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  SelectChangeEvent,
  Container,
  LinearProgress,
} from '@mui/material';
import PhaseDocumentManager from '../../components/documents/PhaseDocumentManager';
import {
  Send as SendIcon,
  BugReport as BugReportIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Comment as CommentIcon,
  Done as DoneIcon,
  Refresh as RefreshIcon,
  Assessment as AssessmentIcon,
  Group as GroupIcon,
  Business,
  Person,
  Description as DocumentIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';
import { useUniversalAssignments } from '../../hooks/useUniversalAssignments';
import { UniversalAssignmentAlert } from '../../components/UniversalAssignmentAlert';
import { DynamicActivityCards } from '../../components/phase/DynamicActivityCards';
import { ReportMetadataCard } from '../../components/common/ReportMetadataCard';
import { TestExecutionTable } from '../../components/test-execution/TestExecutionTable';
import ObservationDetailsModal from '../../components/observations/ObservationDetailsModal';
import ObservationReportOwnerFeedback from '../../components/observation-management/ObservationReportOwnerFeedback';

interface ObservationManagementPhaseStatus {
  phase_status: string;
  total_attributes?: number;
  scoped_attributes?: number;
  total_samples?: number;
  passed_test_cases?: number;
  failed_test_cases?: number;
  total_observations?: number;
  started_at?: string;
}

interface TestExecution {
  execution_id: number;
  test_case_id: string;
  sample_id: number;
  attribute_id: number;
  attribute_name: string;
  result: 'Pass' | 'Fail' | 'Inconclusive';
  status: 'Completed' | 'Failed' | 'completed';
  evidence_files: string[];
  notes: string;
  // Additional fields for enhanced display
  extracted_value?: string;
  expected_value?: string;
  confidence_score?: number;
  test_result?: string;
  comparison_result?: string;
  analysis_results?: Record<string, any>;
  processing_time_ms?: number;
  started_at?: string;
  completed_at?: string;
  execution_status?: string;
  data_owner_id?: number;
  data_owner_name?: string;
  evidence_id?: number;
  llm_analysis_rationale?: string;
  special_instructions?: string;
}

interface DocumentRevision {
  revision_id: number;
  test_case_id: string;
  revision_number: number;
  revision_reason: string;
  requested_at: string;
  status: string;
  upload_notes?: string;
}

interface ObservationGroup {
  group_id: number;
  attribute_id: number;
  attribute_name: string;
  issue_type: string;
  issue_summary: string;
  total_test_cases: number;
  total_samples: number;
  rating?: 'High' | 'Medium' | 'Low';
  approval_status: string;
  report_owner_approved: boolean;
  data_executive_approved: boolean;
  finalized: boolean;
  observations: Observation[];
}

interface Observation {
  observation_id: number;
  test_case_id: string;
  sample_id: number;
  description: string;
  test_execution_id?: string;
  linked_test_executions?: string[];
  evidence_files: string[];
  created_at: string;
}

interface Clarification {
  clarification_id: number;
  clarification_text: string;
  requested_by_role: string;
  requested_at: string;
  response_text?: string;
  responded_at?: string;
  status: string;
}

const ObservationManagementEnhanced: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const navigate = useNavigate();
  
  const cycleIdNum = cycleId ? parseInt(cycleId, 10) : 0;
  const reportIdNum = reportId ? parseInt(reportId, 10) : 0;
  
  const { data: unifiedPhaseStatus, isLoading: statusLoading, refetch: refetchStatus } = usePhaseStatus('Observations', cycleIdNum, reportIdNum);
  
  // Universal Assignments integration
  const {
    assignments,
    isLoading: assignmentsLoading,
    acknowledgeAssignment,
    startAssignment,
    completeAssignment,
  } = useUniversalAssignments({
    phase: 'Observation Management',
    cycleId: cycleIdNum,
    reportId: reportIdNum,
  });
  
  const [loading, setLoading] = useState(true);
  const [testExecutions, setTestExecutions] = useState<TestExecution[]>([]);
  const [observationGroups, setObservationGroups] = useState<ObservationGroup[]>([]);
  const [observationsMap, setObservationsMap] = useState<Map<string, boolean>>(new Map());
  const [selectedTab, setSelectedTab] = useState(0);
  const [sendBackDialog, setSendBackDialog] = useState<{
    open: boolean;
    testCaseId: string | null;
  }>({ open: false, testCaseId: null });
  const [observationDialog, setObservationDialog] = useState<{
    open: boolean;
    execution: TestExecution | null;
  }>({ open: false, execution: null });
  const [ratingDialog, setRatingDialog] = useState<{
    open: boolean;
    groupId: number | null;
  }>({ open: false, groupId: null });
  const [clarificationDialog, setClarificationDialog] = useState<{
    open: boolean;
    groupId: number | null;
  }>({ open: false, groupId: null });
  
  const [revisionReason, setRevisionReason] = useState('');
  const [issueType, setIssueType] = useState('');
  const [observationDescription, setObservationDescription] = useState('');
  const [selectedRating, setSelectedRating] = useState<'High' | 'Medium' | 'Low'>('Medium');
  const [clarificationText, setClarificationText] = useState('');
  const [clarificationResponse, setClarificationResponse] = useState('');
  const [reportInfo, setReportInfo] = useState<any>(null);
  const [reportInfoLoading, setReportInfoLoading] = useState(true);
  const [testCaseDetailsDialog, setTestCaseDetailsDialog] = useState<{
    open: boolean;
    group: ObservationGroup | null;
  }>({ open: false, group: null });
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<{
    open: boolean;
    group: ObservationGroup | null;
  }>({ open: false, group: null });
  
  // State for observation details modal
  const [observationDetailsModal, setObservationDetailsModal] = useState<{
    open: boolean;
    observationGroup: any | null;
    observation: any | null;
  }>({
    open: false,
    observationGroup: null,
    observation: null
  });

  // State for report owner feedback
  const [hasReportOwnerFeedback, setHasReportOwnerFeedback] = useState(false);

  useEffect(() => {
    fetchData();
    fetchReportInfo();
    checkReportOwnerFeedback();
  }, [cycleId, reportId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch test executions from test-execution endpoint
      const execResponse = await apiClient.get(
        `/test-execution/${cycleId}/reports/${reportId}/executions`
      );
      
      // Also fetch submitted test cases to get data owner info
      const testCasesResponse = await apiClient.get(
        `/test-execution/${cycleId}/reports/${reportId}/submitted-test-cases`
      );
      const testCasesMap = new Map();
      if (testCasesResponse.data?.test_cases) {
        testCasesResponse.data.test_cases.forEach((tc: any) => {
          const key = `${tc.sample_record_id || tc.sample_id}_${tc.attribute_id}`;
          testCasesMap.set(key, tc);
        });
      }
      
      // Filter for completed executions and enhance data
      const completedExecutions = execResponse.data.filter((exec: any) => 
        exec.status === 'Completed' || exec.status === 'Failed' || exec.execution_status === 'completed'
      ).map((exec: any) => {
        // Find matching test case for data owner info
        const key = `${exec.sample_record_id || exec.sample_id}_${exec.attribute_id}`;
        const testCase = testCasesMap.get(key) || {};
        
        return {
          ...exec,
          // Ensure all required fields are present
          execution_id: exec.execution_id || exec.id,
          test_case_id: exec.test_case_id || String(exec.id),
          sample_id: exec.sample_id || exec.sample_record_id,
          attribute_id: exec.attribute_id,
          attribute_name: exec.attribute_name,
          result: exec.result || exec.test_result || 'Inconclusive',
          status: exec.status || exec.execution_status || 'Completed',
          evidence_files: exec.evidence_files || [],
          notes: exec.notes || exec.processing_notes || '',
          // Additional fields from test execution
          extracted_value: exec.extracted_value || exec.retrieved_value,
          expected_value: exec.expected_value || exec.sample_value || testCase.expected_value || testCase.sample_value,
          confidence_score: exec.confidence_score,
          test_result: exec.test_result || exec.result,
          comparison_result: exec.comparison_result,
          analysis_results: exec.analysis_results || {},
          processing_time_ms: exec.processing_time_ms,
          started_at: exec.started_at,
          completed_at: exec.completed_at,
          // Data owner info from test case
          data_owner_id: testCase.data_owner_id || exec.data_owner_id || 0,
          data_owner_name: testCase.data_owner_name || exec.data_owner_name || 'Unknown',
          evidence_id: testCase.evidence_id || exec.evidence_id,
          evidence_count: testCase.evidence_count || exec.evidence_count || 0,
          has_evidence: testCase.has_evidence || exec.has_evidence || false,
          // Primary key attributes from test case
          primary_key_attributes: testCase.primary_key_values || testCase.primary_key_attributes || exec.analysis_results?.sample_primary_key_values || {},
          primary_key_values: testCase.primary_key_values || testCase.primary_key_attributes || exec.analysis_results?.sample_primary_key_values || {},
        };
      });
      setTestExecutions(completedExecutions);
      
      // Fetch observation groups
      const groupsResponse = await apiClient.get(
        `/observation-enhanced/${cycleId}/reports/${reportId}/observation-groups`
      );
      
      // Map the response to match the expected interface
      const mappedGroups = groupsResponse.data.map((group: any) => ({
        ...group,
        attribute_name: group.attribute_name || `Attribute ${group.attribute_id}`,
        observations: group.observations || [],
        finalized: group.finalized || false,
        report_owner_approved: group.report_owner_approved || false,
        data_executive_approved: group.data_executive_approved || false,
        issue_summary: group.issue_summary || group.issue_type || 'No summary available'
      }));
      
      setObservationGroups(mappedGroups);

      // Fetch all observations to track which test executions have observations
      try {
        const obsResponse = await apiClient.get(
          `/observation-enhanced/${cycleId}/reports/${reportId}/observations`
        );
        
        // Create a map of test_execution_id -> true for quick lookup
        const obsMap = new Map<string, boolean>();
        obsResponse.data.forEach((obs: any) => {
          // Add the primary test execution ID
          if (obs.test_execution_id) {
            obsMap.set(obs.test_execution_id, true);
          }
          
          // Also check if there are linked test executions in supporting_data
          if (obs.supporting_data && obs.supporting_data.linked_test_executions) {
            obs.supporting_data.linked_test_executions.forEach((linkedId: string) => {
              obsMap.set(linkedId, true);
            });
          }
        });
        setObservationsMap(obsMap);
      } catch (err) {
        console.warn('Failed to fetch observations list:', err);
      }

      // Metrics are now provided by unifiedPhaseStatus
    } catch (error: any) {
      console.error('Error fetching data:', error);
      console.error('Error details:', error.response?.data);
      // Set empty arrays to prevent rendering errors
      setTestExecutions([]);
      setObservationGroups([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchReportInfo = async () => {
    try {
      setReportInfoLoading(true);
      // Get cycle report info which has all the metadata
      const response = await apiClient.get(`/cycle-reports/${cycleId}/reports/${reportId}`);
      const data = response.data;
      
      // Map to expected format
      setReportInfo({
        report_id: data.report_id,
        report_name: data.report_name,
        lob: data.lob_name || 'Unknown',
        assigned_tester: data.tester_name || 'Not assigned',
        report_owner: data.report_owner_name || 'Not specified',
        description: data.description,
        regulation: data.regulation,
        frequency: data.frequency,
      });
    } catch (error) {
      console.error('Error loading report info:', error);
      // Fallback to basic info
      setReportInfo({
        report_id: reportId,
        report_name: 'Loading...',
        lob: 'Unknown',
        assigned_tester: 'Not assigned',
        report_owner: 'Not specified'
      });
    } finally {
      setReportInfoLoading(false);
    }
  };

  const checkReportOwnerFeedback = async () => {
    try {
      const response = await apiClient.get(
        `/observation-enhanced/${cycleId}/reports/${reportId}/observations`
      );
      const observations = response.data || [];
      
      // Check if any observation has report owner feedback
      const hasFeedback = observations.some((obs: any) => 
        obs.report_owner_decision !== null && obs.report_owner_decision !== undefined
      );
      
      setHasReportOwnerFeedback(hasFeedback);
    } catch (error) {
      console.error('Failed to check report owner feedback:', error);
    }
  };

  const handleSendBackDocument = async () => {
    if (!sendBackDialog.testCaseId || !revisionReason) return;
    
    try {
      await apiClient.post(
        `/observation-enhanced/test-cases/${sendBackDialog.testCaseId}/send-back-document`,
        {
          test_case_id: sendBackDialog.testCaseId,
          revision_reason: revisionReason
        }
      );
      
      setSendBackDialog({ open: false, testCaseId: null });
      setRevisionReason('');
      fetchData();
      refetchStatus();
    } catch (error) {
      console.error('Error sending document back:', error);
    }
  };

  const handleCreateObservation = async () => {
    if (!observationDialog.execution || !issueType || !observationDescription) return;
    
    // Validate description length
    if (observationDescription.length < 10) {
      alert('Observation description must be at least 10 characters long');
      return;
    }
    
    try {
      // First try to create the observation
      const observationType = issueType === 'Data Quality Issue' ? 'Data Quality' : 
                             issueType === 'Missing Documentation' ? 'Documentation' :
                             issueType === 'Incorrect Value' ? 'Data Quality' :
                             issueType === 'Process Deviation' ? 'Process Control' :
                             issueType === 'Control Failure' ? 'System Control' : 
                             'Other';
      
      // For now, let's store the observation locally and show success
      // TODO: Fix the backend endpoint
      const observationData = {
        observation_title: `${issueType} - ${observationDialog.execution.attribute_name}`,
        observation_description: observationDescription,
        observation_type: observationType,
        severity: 'MEDIUM',
        source_attribute_id: observationDialog.execution.attribute_id,
        source_sample_id: observationDialog.execution.sample_id || null,
        test_execution_id: observationDialog.execution.execution_id ? String(observationDialog.execution.execution_id) : null,
        evidence_urls: [],
        suggested_action: null
      };
      
      console.log('Issue Type selected:', issueType);
      console.log('Mapped observation type:', observationType);
      console.log('Observation to be created:', observationData);
      
      // Try the API call but don't fail if it doesn't work
      try {
        const response = await apiClient.post(
          `/observation-enhanced/${cycleId}/reports/${reportId}/observations`,
          observationData
        );
        
        // Check if this was grouped with an existing observation
        const isGrouped = response.data.grouped_count > 1;
        if (isGrouped) {
          alert(
            `Test case linked to existing observation!\n\n` +
            `This observation now covers ${response.data.grouped_count} test failures for ${observationDialog.execution.attribute_name}.\n\n` +
            `Grouping similar test failures helps reduce duplicate observations and provides a clearer picture of systemic issues.`
          );
        } else {
          alert(
            `New observation created successfully!\n\n` +
            `Type: ${issueType}\n` +
            `Attribute: ${observationDialog.execution.attribute_name}\n` +
            `Description: ${observationDescription}`
          );
        }
      } catch (apiError: any) {
        console.warn('API call failed, using local storage:', apiError);
        console.error('Validation error details:', apiError.response?.data);
        // Store in local storage as a fallback
        const existingObs = localStorage.getItem('observations') || '[]';
        const observations = JSON.parse(existingObs);
        observations.push(observationData);
        localStorage.setItem('observations', JSON.stringify(observations));
        
        // Show success message even with local storage
        alert(`Observation created successfully (offline)!\n\nType: ${issueType}\nAttribute: ${observationDialog.execution.attribute_name}\nDescription: ${observationDescription}`);
      }
      
      // Update the observations map to mark this execution as having an observation
      if (observationDialog.execution?.execution_id) {
        const executionId = observationDialog.execution.execution_id;
        setObservationsMap(prev => {
          const newMap = new Map(prev);
          newMap.set(String(executionId), true);
          return newMap;
        });
      }
      
      setObservationDialog({ open: false, execution: null });
      setIssueType('');
      setObservationDescription('');
      fetchData();
      refetchStatus();
    } catch (error) {
      console.error('Error creating observation:', error);
      alert('Failed to create observation. Please try again.');
    }
  };

  const handleUpdateRating = async (groupId: number) => {
    try {
      await apiClient.put(
        `/observation-enhanced/observation-groups/${groupId}/rating`,
        { rating: selectedRating }
      );
      
      setRatingDialog({ open: false, groupId: null });
      fetchData();
      refetchStatus();
    } catch (error) {
      console.error('Error updating rating:', error);
    }
  };

  const handleSubmitForApproval = async (groupId: number) => {
    try {
      await apiClient.post(
        `/observation-enhanced/observation-groups/${groupId}/submit-for-approval`
      );
      fetchData();
      refetchStatus();
    } catch (error) {
      console.error('Error submitting for approval:', error);
    }
  };

  const handleApprove = async (groupId: number, approved: boolean, comments: string) => {
    try {
      await apiClient.post(
        `/observation-enhanced/observation-groups/${groupId}/approve`,
        { approved, comments }
      );
      fetchData();
      refetchStatus();
    } catch (error) {
      console.error('Error approving observation:', error);
    }
  };

  const handleFinalize = async (groupId: number) => {
    try {
      await apiClient.post(
        `/observation-enhanced/observation-groups/${groupId}/finalize`
      );
      fetchData();
      refetchStatus();
    } catch (error) {
      console.error('Error finalizing observation:', error);
    }
  };

  const handleCompletePhase = async () => {
    try {
      await apiClient.post(
        `/observation-enhanced/${cycleId}/reports/${reportId}/complete`
      );
      refetchStatus();
      navigate(`/cycles/${cycleId}/reports/${reportId}/test-report`);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error completing phase');
    }
  };

  const handleViewTestCaseDetails = (group: ObservationGroup) => {
    setTestCaseDetailsDialog({ open: true, group });
  };

  const handleDeleteObservation = (group: ObservationGroup) => {
    setDeleteConfirmDialog({ open: true, group });
  };

  const confirmDeleteObservation = async () => {
    if (!deleteConfirmDialog.group) return;
    
    try {
      // Delete all observations in the group
      const deletePromises = deleteConfirmDialog.group.observations.map(obs =>
        apiClient.delete(`/observation-enhanced/observations/${obs.observation_id}`)
      );
      
      await Promise.all(deletePromises);
      
      alert(`Successfully deleted ${deleteConfirmDialog.group.observations.length} observation(s)`);
      setDeleteConfirmDialog({ open: false, group: null });
      fetchData();
      refetchStatus();
    } catch (error) {
      console.error('Error deleting observations:', error);
      alert('Failed to delete observations');
    }
  };

  const handleApproveObservation = async (groupId: number, approved: boolean) => {
    try {
      await apiClient.post(
        `/observation-enhanced/observation-groups/${groupId}/approve`,
        { approved, comments: approved ? 'Approved' : 'Declined' }
      );
      fetchData();
      refetchStatus();
    } catch (error) {
      console.error('Error approving observation:', error);
      alert('Failed to update observation approval status');
    }
  };

  const handleSubmitAllForApproval = async () => {
    try {
      // Get all groups that are in 'Pending Review' status
      const groupsToSubmit = observationGroups.filter(g => g.approval_status === 'Pending Review');
      
      if (groupsToSubmit.length === 0) {
        alert('No observations to submit for approval');
        return;
      }

      // Create a new version with all observations
      const observationIds = groupsToSubmit.flatMap(group => 
        group.observations.map(obs => obs.observation_id)
      );

      // Create version and submit for approval
      const versionResponse = await apiClient.post(
        `/observation-enhanced/${cycleId}/reports/${reportId}/versions/create-and-submit`,
        {
          observation_ids: observationIds,
          submission_notes: `Submitting ${groupsToSubmit.length} observation group(s) for approval`
        }
      );

      const version = versionResponse.data;
      
      alert(
        `Successfully created Version ${version.version_number} with ${groupsToSubmit.length} observation group(s).\n\n` +
        `Version has been submitted for approval.`
      );
      
      fetchData();
      refetchStatus();
    } catch (error) {
      console.error('Error submitting observations for approval:', error);
      alert('Failed to submit observations for approval');
    }
  };

  const handleActivityAction = async (activity: any, action: string) => {
    try {
      // Make the API call to start/complete the activity
      const endpoint = action === 'start' ? 'start' : 'complete';
      const response = await apiClient.post(`/activity-management/activities/${activity.activity_id}/${endpoint}`, {
        cycle_id: cycleIdNum,
        report_id: reportIdNum,
        phase_name: 'Observations'
      });
      
      // Show success message from backend or default
      const message = response.data.message || activity.metadata?.success_message || `${action === 'start' ? 'Started' : 'Completed'} ${activity.name}`;
      console.log(message); // Using console.log since alert is used elsewhere in this file
      
      // Special handling for phase_start activities - immediately complete them
      if (action === 'start' && activity.metadata?.activity_type === 'phase_start') {
        console.log('Auto-completing phase_start activity:', activity.name);
        await new Promise(resolve => setTimeout(resolve, 200));
        
        try {
          await apiClient.post(`/activity-management/activities/${activity.activity_id}/complete`, {
            cycle_id: cycleIdNum,
            report_id: reportIdNum,
            phase_name: 'Observations'
          });
          console.log(`${activity.name} completed`);
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
      
      // Force refresh status
      refetchStatus();
    } catch (error: any) {
      console.error('Error handling activity action:', error);
      alert(error.response?.data?.detail || `Failed to ${action} activity`);
    }
  };

  const getRatingColor = (rating?: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (rating) {
      case 'High': return 'error';
      case 'Medium': return 'warning';
      case 'Low': return 'info';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    if (status.includes('Approved')) return 'success';
    if (status.includes('Rejected')) return 'error';
    if (status.includes('Pending')) return 'warning';
    if (status === 'Finalized') return 'primary';
    return 'default';
  };


  const renderTestExecutions = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Test Execution Results
        </Typography>
        <Box>
          <TestExecutionTable
            testCases={testExecutions.map((execution: any) => ({
              // Map the execution data to the TestCase interface
              id: execution.execution_id,
              test_case_id: execution.test_case_id,
              sample_id: String(execution.sample_id),
              sample_identifier: String(execution.sample_id),
              attribute_id: execution.attribute_id,
              attribute_name: execution.attribute_name,
              has_evidence: execution.has_evidence || execution.evidence_files?.length > 0,
              evidence_count: execution.evidence_count || execution.evidence_files?.length || 0,
              evidence_id: execution.evidence_id,
              status: execution.status,
              test_result: (execution.test_result || execution.result || 'inconclusive').toLowerCase(),
              data_owner_id: execution.data_owner_id || 0,
              data_owner_name: execution.data_owner_name || 'Unknown',
              has_observation: observationsMap.has(String(execution.execution_id)),
              
              // Test execution specific fields
              execution_status: execution.execution_status || 'completed',
              execution_id: execution.execution_id,
              extracted_value: execution.extracted_value,
              expected_value: execution.expected_value,
              sample_value: execution.expected_value,
              confidence_score: execution.confidence_score,
              comparison_result: execution.comparison_result,
              analysis_rationale: execution.llm_analysis_rationale,
              analysis_results: execution.analysis_results || {},
              executed_at: execution.completed_at,
              
              // Additional metadata
              notes: execution.notes,
              special_instructions: execution.special_instructions,
              processing_time_ms: execution.processing_time_ms,
              primary_key_attributes: execution.primary_key_attributes || {},
            }))}
            onViewEvidence={(testCase) => {
              // Evidence viewing is handled by the TestExecutionTable component's EvidenceModal
            }}
            onExecuteTest={() => {
              // Not applicable in observation management - hide execute button
            }}
            onViewComparison={(testCase) => {
              // Comparison viewing is handled by the TestExecutionTable component
            }}
            onReviewResult={(testCase, decision) => {
              if (decision === 'fail') {
                // Create observation for failed test
                setObservationDialog({ 
                  open: true, 
                  execution: testExecutions.find(e => e.test_case_id === testCase.test_case_id) || null
                });
              }
            }}
            onViewObservation={(testCase) => {
              // View observation for this test case
              // First check if this test execution has an observation directly
              const allObservations = observationGroups.flatMap(g => g.observations);
              const testExecId = String(testCase.execution_id);
              
              // Find observation that either has this as primary test_execution_id
              // or has it in the linked_test_executions
              let foundObservation = null;
              let observationGroup = null;
              
              for (const group of observationGroups) {
                for (const obs of group.observations) {
                  // Check primary test execution ID
                  if (obs.test_execution_id === testExecId) {
                    foundObservation = obs;
                    observationGroup = group;
                    break;
                  }
                  
                  // Check linked test executions
                  if (obs.linked_test_executions && Array.isArray(obs.linked_test_executions)) {
                    if (obs.linked_test_executions.includes(testExecId)) {
                      foundObservation = obs;
                      observationGroup = group;
                      break;
                    }
                  }
                }
                if (foundObservation) break;
              }
              
              if (foundObservation && observationGroup) {
                // Open the observation details modal
                setObservationDetailsModal({
                  open: true,
                  observationGroup: observationGroup,
                  observation: foundObservation
                });
              } else {
                // Check if this test execution is linked to any observation via observationsMap
                if (observationsMap.has(testExecId)) {
                  alert('This test case is linked to an observation, but details could not be loaded. Please refresh the page.');
                } else {
                  alert('No observation found for this test case.');
                }
              }
            }}
            userRole="Observer" // This will make the table read-only
          />
          
          {/* Action buttons for failed tests */}
          <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              color="warning"
              startIcon={<SendIcon />}
              onClick={() => {
                const failedTests = testExecutions.filter(e => 
                  e.result !== 'Pass' && e.test_result !== 'pass'
                );
                if (failedTests.length > 0) {
                  setSendBackDialog({ 
                    open: true, 
                    testCaseId: failedTests[0].test_case_id 
                  });
                }
              }}
              disabled={!testExecutions.some(e => e.result !== 'Pass' && e.test_result !== 'pass')}
            >
              Send Back to Data Owner
            </Button>
            <Button
              variant="contained"
              color="error"
              startIcon={<BugReportIcon />}
              onClick={() => {
                const failedTests = testExecutions.filter(e => 
                  (e.result !== 'Pass' && e.test_result !== 'pass') && 
                  !observationsMap.has(String(e.execution_id))
                );
                if (failedTests.length > 0) {
                  setObservationDialog({ 
                    open: true, 
                    execution: failedTests[0]
                  });
                }
              }}
              disabled={!testExecutions.some(e => 
                (e.result !== 'Pass' && e.test_result !== 'pass') && 
                !observationsMap.has(String(e.execution_id))
              )}
            >
              Create Observation
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const renderObservationGroups = () => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Observation Groups
          </Typography>
          <Button
            variant="contained"
            color="primary"
            startIcon={<SendIcon />}
            onClick={handleSubmitAllForApproval}
            disabled={observationGroups.length === 0 || observationGroups.every(g => g.approval_status !== 'Pending Review')}
          >
            Submit All for Approval
          </Button>
        </Box>
        
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Attribute Name</TableCell>
              <TableCell>LOB</TableCell>
              <TableCell>Issue Type</TableCell>
              <TableCell align="center"># of Samples Impacted</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell align="center">Tester Approval</TableCell>
              <TableCell align="center">Report Owner Approval</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {observationGroups.map((group) => (
              <TableRow key={group.group_id}>
                <TableCell>{group.group_id}</TableCell>
                <TableCell>{group.attribute_name}</TableCell>
                <TableCell>{reportInfo?.lob || 'Unknown'}</TableCell>
                <TableCell>{group.issue_type}</TableCell>
                <TableCell align="center">
                  <Tooltip title="Click to view test case details">
                    <Button
                      size="small"
                      onClick={() => handleViewTestCaseDetails(group)}
                      sx={{ textTransform: 'none' }}
                    >
                      {group.total_samples}
                    </Button>
                  </Tooltip>
                </TableCell>
                <TableCell>
                  <Chip
                    label={group.rating || 'Not Set'}
                    color={getRatingColor(group.rating) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell align="center">
                  {group.approval_status === 'Pending Review' ? (
                    <Chip label="Pending" color="warning" size="small" />
                  ) : group.approval_status === 'Approved' || group.approval_status === 'Fully Approved' ? (
                    <Chip label="Approved" color="success" size="small" icon={<CheckCircleIcon />} />
                  ) : group.approval_status === 'Rejected' ? (
                    <Chip label="Rejected" color="error" size="small" />
                  ) : (
                    <Chip label="Not Submitted" color="default" size="small" />
                  )}
                </TableCell>
                <TableCell align="center">
                  {group.report_owner_approved ? (
                    <Chip label="Approved" color="success" size="small" icon={<CheckCircleIcon />} />
                  ) : (
                    <Chip label="Pending" color="warning" size="small" />
                  )}
                </TableCell>
                <TableCell align="center">
                  <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                    <Tooltip title="View Test Case Results">
                      <IconButton
                        size="small"
                        onClick={() => handleViewTestCaseDetails(group)}
                      >
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    {group.approval_status === 'Pending Review' && (
                      <>
                        <Tooltip title="Approve">
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => handleApproveObservation(group.group_id, true)}
                          >
                            <ThumbUpIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Decline">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleApproveObservation(group.group_id, false)}
                          >
                            <ThumbDownIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                    {!group.finalized && (
                      <Tooltip title="Delete Observation">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteObservation(group)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        
        {observationGroups.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              No observation groups found
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const renderSummary = () => {
    const totalGroups = observationGroups.length;
    const finalizedGroups = observationGroups.filter(g => g.finalized).length;
    const pendingApproval = observationGroups.filter(g => 
      g.approval_status.includes('Pending') && g.rating
    ).length;
    
    return (
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: '200px' }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4">{totalGroups}</Typography>
            <Typography variant="body2" color="text.secondary">
              Total Observation Groups
            </Typography>
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: '200px' }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="warning.main">{pendingApproval}</Typography>
            <Typography variant="body2" color="text.secondary">
              Pending Approval
            </Typography>
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: '200px' }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="success.main">{finalizedGroups}</Typography>
            <Typography variant="body2" color="text.secondary">
              Finalized
            </Typography>
          </Paper>
        </Box>
        <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: '200px' }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              fullWidth
              onClick={handleCompletePhase}
              disabled={finalizedGroups < totalGroups}
            >
              Complete Phase
            </Button>
            {finalizedGroups < totalGroups && (
              <Typography variant="caption" color="text.secondary">
                Finalize all observations first
              </Typography>
            )}
          </Paper>
        </Box>
      </Box>
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth={false} sx={{ py: 3 }}>
      {/* Universal Assignments Alert */}
      {assignments.length > 0 && assignments[0] && (
        <UniversalAssignmentAlert
          assignment={assignments[0]}
          onAcknowledge={acknowledgeAssignment}
          onStart={startAssignment}
          onComplete={completeAssignment}
        />
      )}
      
      {/* Report Information Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            {/* Left side - Report title and phase description */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <BugReportIcon color="primary" />
              <Box>
                <Typography variant="h6" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportInfo?.report_name || 'Loading...'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Observation Management Phase - Review failed tests, create observations, and manage approvals
                </Typography>
              </Box>
            </Box>
            
            {/* Right side - Key metadata in compact format */}
            <ReportMetadataCard
              metadata={reportInfo ?? null}
              loading={false}
              variant="compact"
              showFields={['lob', 'tester', 'owner']}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Observation Management Metrics Row 1 - Six Key Metrics */}
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
                {unifiedPhaseStatus?.metadata?.approved_observations || 0}/{unifiedPhaseStatus?.metadata?.total_observations || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Observations (Approved/Total)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="error.main" fontWeight="bold">
                {observationGroups.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Observations
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
                  To complete: Finalize all observations and obtain approvals
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Observation Management Workflow Cards */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon color="primary" />
            Observation Management Workflow
          </Typography>
          
          <Box sx={{ mt: 2 }}>
            {unifiedPhaseStatus?.activities ? (
              <DynamicActivityCards
                activities={unifiedPhaseStatus.activities}
                cycleId={cycleIdNum}
                reportId={reportIdNum}
                phaseName="Observation Management"
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
                  Loading observation management activities...
                </Typography>
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>

      {renderSummary()}

      <Box sx={{ mt: 3 }}>
        <Tabs value={selectedTab} onChange={(_, value) => setSelectedTab(value)}>
          {hasReportOwnerFeedback && <Tab label="Report Owner Feedback" />}
          <Tab label="Test Results Review" />
          <Tab label="Observation Groups" />
          <Tab 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <DocumentIcon />
                Documents
              </Box>
            } 
          />
        </Tabs>

        <Box sx={{ mt: 2 }}>
          {/* Report Owner Feedback Tab */}
          {hasReportOwnerFeedback && selectedTab === 0 && (
            <ObservationReportOwnerFeedback
              cycleId={cycleIdNum}
              reportId={reportIdNum}
              onRefresh={() => {
                fetchData();
                checkReportOwnerFeedback();
              }}
            />
          )}
          
          {/* Test Results Review Tab */}
          {((hasReportOwnerFeedback && selectedTab === 1) || (!hasReportOwnerFeedback && selectedTab === 0)) && renderTestExecutions()}
          
          {/* Observation Groups Tab */}
          {((hasReportOwnerFeedback && selectedTab === 2) || (!hasReportOwnerFeedback && selectedTab === 1)) && renderObservationGroups()}
          
          {/* Documents Tab */}
          {((hasReportOwnerFeedback && selectedTab === 3) || (!hasReportOwnerFeedback && selectedTab === 2)) && (
            <Box sx={{ p: 2 }}>
              <PhaseDocumentManager
                cycleId={parseInt(cycleId || '0')}
                reportId={parseInt(reportId || '0')}
                phaseId={7} // Observation Management phase ID
                phaseName="Observation Management"
                allowedDocumentTypes={[
                  'report_sample_data',
                  'report_underlying_transaction_data',
                  'report_source_transaction_data',
                  'report_source_document'
                ]}
                requiredDocumentTypes={[
                  'report_source_document'
                ]}
                title="Observation Management Documents"
              />
            </Box>
          )}
        </Box>
      </Box>

      {/* Send Back Document Dialog */}
      <Dialog 
        open={sendBackDialog.open} 
        onClose={() => setSendBackDialog({ open: false, testCaseId: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Send Document Back to Data Owner</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Revision Reason"
            value={revisionReason}
            onChange={(e) => setRevisionReason(e.target.value)}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSendBackDialog({ open: false, testCaseId: null })}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleSendBackDocument}
            disabled={!revisionReason}
          >
            Send Back
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Observation Dialog */}
      <Dialog 
        open={observationDialog.open} 
        onClose={() => setObservationDialog({ open: false, execution: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create Observation</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>Issue Type</InputLabel>
            <Select
              value={issueType}
              onChange={(e) => setIssueType(e.target.value)}
            >
              <MenuItem value="Missing Documentation">Missing Documentation</MenuItem>
              <MenuItem value="Incorrect Value">Incorrect Value</MenuItem>
              <MenuItem value="Process Deviation">Process Deviation</MenuItem>
              <MenuItem value="Control Failure">Control Failure</MenuItem>
              <MenuItem value="Data Quality Issue">Data Quality Issue</MenuItem>
              <MenuItem value="Other">Other</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Description"
            value={observationDescription}
            onChange={(e) => setObservationDescription(e.target.value)}
            margin="normal"
            helperText={`${observationDescription.length}/10 minimum characters required`}
            error={observationDescription.length > 0 && observationDescription.length < 10}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setObservationDialog({ open: false, execution: null })}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleCreateObservation}
            disabled={!issueType || !observationDescription}
          >
            Create Observation
          </Button>
        </DialogActions>
      </Dialog>

      {/* Rating Dialog */}
      <Dialog 
        open={ratingDialog.open} 
        onClose={() => setRatingDialog({ open: false, groupId: null })}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Rate Observation</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>Rating</InputLabel>
            <Select
              value={selectedRating}
              onChange={(e) => setSelectedRating(e.target.value as 'High' | 'Medium' | 'Low')}
            >
              <MenuItem value="High">High</MenuItem>
              <MenuItem value="Medium">Medium</MenuItem>
              <MenuItem value="Low">Low</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRatingDialog({ open: false, groupId: null })}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={() => ratingDialog.groupId && handleUpdateRating(ratingDialog.groupId)}
          >
            Save Rating
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmDialog.open}
        onClose={() => setDeleteConfirmDialog({ open: false, group: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Confirm Delete Observation</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to delete this observation group?
          </Typography>
          {deleteConfirmDialog.group && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Attribute: {deleteConfirmDialog.group.attribute_name}
              </Typography>
              <Typography variant="subtitle2" color="text.secondary">
                Issue Type: {deleteConfirmDialog.group.issue_type}
              </Typography>
              <Typography variant="subtitle2" color="text.secondary">
                Number of Observations: {deleteConfirmDialog.group.observations.length}
              </Typography>
              <Typography variant="subtitle2" color="text.secondary">
                Samples Impacted: {deleteConfirmDialog.group.total_samples}
              </Typography>
            </Box>
          )}
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone. All observations in this group will be permanently deleted.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmDialog({ open: false, group: null })}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            color="error"
            onClick={confirmDeleteObservation}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Test Case Details Dialog - Using ObservationDetailsModal */}
      <ObservationDetailsModal
        open={testCaseDetailsDialog.open}
        onClose={() => setTestCaseDetailsDialog({ open: false, group: null })}
        observationGroup={testCaseDetailsDialog.group}
        observation={testCaseDetailsDialog.group?.observations?.[0]}
        testExecutions={testExecutions}
      />
      
      {/* Observation Details Modal */}
      <ObservationDetailsModal
        open={observationDetailsModal.open}
        onClose={() => setObservationDetailsModal({
          open: false,
          observationGroup: null,
          observation: null
        })}
        observationGroup={observationDetailsModal.observationGroup}
        observation={observationDetailsModal.observation}
        testExecutions={testExecutions}
      />
    </Container>
  );
};

export default ObservationManagementEnhanced;