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
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';
import { useUniversalAssignments } from '../../hooks/useUniversalAssignments';
import { UniversalAssignmentAlert } from '../../components/UniversalAssignmentAlert';
import { DynamicActivityCardsEnhanced as DynamicActivityCards } from '../../components/phase/DynamicActivityCardsEnhanced';

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
  status: 'Completed';
  evidence_files: string[];
  notes: string;
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
  const [selectedTab, setSelectedTab] = useState(0);
  const [metricsData, setMetricsData] = useState<any>({});
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

  useEffect(() => {
    fetchData();
    fetchReportInfo();
  }, [cycleId, reportId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch test executions from test-execution endpoint
      const execResponse = await apiClient.get(
        `/test-execution/${cycleId}/reports/${reportId}/executions`
      );
      // Filter for completed executions
      const completedExecutions = execResponse.data.filter((exec: any) => 
        exec.status === 'Completed' || exec.status === 'Failed'
      );
      setTestExecutions(completedExecutions);
      
      // Fetch observation groups
      const groupsResponse = await apiClient.get(
        `/observation-enhanced/cycles/${cycleId}/reports/${reportId}/observation-groups`
      );
      setObservationGroups(groupsResponse.data);

      // Fetch metrics data
      try {
        const metricsResponse = await apiClient.get(`/test-report/${cycleId}/reports/${reportId}/data`);
        setMetricsData(metricsResponse.data?.metrics || {});
      } catch (metricsError) {
        console.error('Error fetching metrics:', metricsError);
        setMetricsData({});
      }
    } catch (error) {
      console.error('Error fetching data:', error);
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
    
    try {
      await apiClient.post(
        `/observation-enhanced/cycles/${cycleId}/reports/${reportId}/observations`,
        {
          test_execution_id: observationDialog.execution.execution_id,
          test_case_id: observationDialog.execution.test_case_id,
          sample_id: observationDialog.execution.sample_id,
          attribute_id: observationDialog.execution.attribute_id,
          issue_type: issueType,
          description: observationDescription,
          evidence_files: observationDialog.execution.evidence_files
        }
      );
      
      setObservationDialog({ open: false, execution: null });
      setIssueType('');
      setObservationDescription('');
      fetchData();
      refetchStatus();
    } catch (error) {
      console.error('Error creating observation:', error);
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
        `/observation-enhanced/cycles/${cycleId}/reports/${reportId}/complete-observation-phase`
      );
      refetchStatus();
      navigate(`/cycles/${cycleId}/reports/${reportId}/test-report`);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error completing phase');
    }
  };

  const handleActivityAction = async (activity: any, action: string) => {
    try {
      if (action === 'start') {
        // Handle starting the phase if this is the first activity
        if (activity.activity_id === 'start_observation_phase') {
          console.log('Starting observation phase');
          refetchStatus();
        } else {
          console.log(`Starting activity: ${activity.name}`);
        }
      } else if (action === 'complete') {
        // Handle completing the phase if this is the last activity
        if (activity.activity_id === 'complete_observation_phase') {
          await handleCompletePhase();
        } else {
          console.log(`Completing activity: ${activity.name}`);
        }
      }
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

  const getStepColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'active': return 'primary';
      case 'pending': return 'default';
      default: return 'default';
    }
  };

  const getObservationSteps = () => {
    const hasStarted = observationGroups.length > 0 || testExecutions.length > 0;
    const hasObservations = observationGroups.some(g => g.observations.length > 0);
    const hasRatings = observationGroups.some(g => g.rating !== undefined);
    const hasApprovals = observationGroups.some(g => g.approval_status.includes('Approved'));
    const allFinalized = observationGroups.length > 0 && observationGroups.every(g => g.finalized);
    const isNotStarted = unifiedPhaseStatus?.phase_status === 'not_started';
    
    return [
      {
        label: 'Start Observation Phase',
        description: 'Initialize observation management',
        icon: <BugReportIcon color="primary" />,
        status: isNotStarted ? 'pending' : hasStarted ? 'completed' : 'active',
        showButton: isNotStarted,
        buttonText: 'Start Observation Phase',
        buttonAction: () => {
          console.log('Start observation phase');
          refetchStatus();
        },
        buttonIcon: <BugReportIcon />
      },
      {
        label: 'Review Test Results',
        description: 'Analyze failed test cases',
        icon: <AssessmentIcon color="primary" />,
        status: hasObservations ? 'completed' : hasStarted ? 'active' : 'pending',
        showButton: false,
      },
      {
        label: 'Create Observations',
        description: 'Document issues and findings',
        icon: <CommentIcon color="primary" />,
        status: hasRatings ? 'completed' : hasObservations ? 'active' : 'pending',
        showButton: false,
      },
      {
        label: 'Rate & Approve',
        description: 'Assess impact and get approvals',
        icon: <ThumbUpIcon color="primary" />,
        status: hasApprovals ? 'completed' : hasRatings ? 'active' : 'pending',
        showButton: false,
      },
      {
        label: 'Complete Phase',
        description: 'Finalize all observations',
        icon: <CheckCircleIcon color="primary" />,
        status: allFinalized ? 'completed' : hasApprovals ? 'active' : 'pending',
        showButton: allFinalized,
        buttonText: 'Complete Phase',
        buttonAction: handleCompletePhase,
        buttonIcon: <DoneIcon />
      }
    ];
  };

  const renderTestExecutions = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Test Execution Results
        </Typography>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Attribute</TableCell>
              <TableCell>Sample ID</TableCell>
              <TableCell>Result</TableCell>
              <TableCell>Evidence</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {testExecutions.map((execution) => (
              <TableRow key={execution.execution_id}>
                <TableCell>{execution.attribute_name}</TableCell>
                <TableCell>{execution.sample_id}</TableCell>
                <TableCell>
                  <Chip 
                    label={execution.result}
                    color={execution.result === 'Pass' ? 'success' : 'error'}
                    size="small"
                  />
                </TableCell>
                <TableCell>{execution.evidence_files?.length || 0} files</TableCell>
                <TableCell>
                  <Tooltip title="Send Back to Data Owner">
                    <IconButton
                      size="small"
                      onClick={() => setSendBackDialog({ 
                        open: true, 
                        testCaseId: execution.test_case_id 
                      })}
                    >
                      <SendIcon />
                    </IconButton>
                  </Tooltip>
                  {execution.result !== 'Pass' && (
                    <Tooltip title="Create Observation">
                      <IconButton
                        size="small"
                        onClick={() => setObservationDialog({ 
                          open: true, 
                          execution 
                        })}
                      >
                        <BugReportIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );

  const renderObservationGroups = () => (
    <Box>
      {observationGroups.map((group) => (
        <Accordion key={group.group_id}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={2} width="100%">
              <Typography variant="subtitle1" flex={1}>
                {group.attribute_name} - {group.issue_type}
              </Typography>
              <Box display="flex" alignItems="center" gap={1}>
                <Chip
                  icon={<GroupIcon />}
                  label={`${group.total_test_cases} cases`}
                  size="small"
                />
                {group.rating && (
                  <Chip
                    label={group.rating}
                    color={getRatingColor(group.rating) as 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'}
                    size="small"
                  />
                )}
                <Chip
                  label={group.approval_status}
                  color={getStatusColor(group.approval_status) as 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'}
                  size="small"
                />
              </Box>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Observations ({group.observations.length})
              </Typography>
              <List dense>
                {group.observations.map((obs) => (
                  <ListItem key={obs.observation_id}>
                    <ListItemText
                      primary={obs.description}
                      secondary={`Created on ${new Date(obs.created_at).toLocaleDateString()}`}
                    />
                  </ListItem>
                ))}
              </List>
              
              <Divider sx={{ my: 2 }} />
              
              <Box display="flex" gap={1} flexWrap="wrap">
                {!group.rating && (
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => {
                      setRatingDialog({ open: true, groupId: group.group_id });
                      setSelectedRating('Medium');
                    }}
                  >
                    Add Rating
                  </Button>
                )}
                
                {group.rating && !group.finalized && group.approval_status === 'Pending Review' && (
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => handleSubmitForApproval(group.group_id)}
                  >
                    Submit for Approval
                  </Button>
                )}
                
                {group.approval_status === 'Fully Approved' && !group.finalized && (
                  <Button
                    variant="contained"
                    color="primary"
                    size="small"
                    onClick={() => handleFinalize(group.group_id)}
                    startIcon={<DoneIcon />}
                  >
                    Finalize
                  </Button>
                )}
                
                {group.finalized && (
                  <Chip
                    label="Finalized"
                    color="primary"
                    icon={<CheckCircleIcon />}
                  />
                )}
              </Box>
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
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
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
              {reportInfoLoading ? (
                <Box sx={{ width: 200 }}>
                  <LinearProgress />
                </Box>
              ) : (
                <>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Business color="action" fontSize="small" />
                    <Typography variant="body2" color="text.secondary">LOB:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {reportInfo?.lob || 'Unknown'}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Person color="action" fontSize="small" />
                    <Typography variant="body2" color="text.secondary">Tester:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {reportInfo?.assigned_tester || 'Not assigned'}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Person color="action" fontSize="small" />
                    <Typography variant="body2" color="text.secondary">Owner:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {reportInfo?.report_owner || 'Not specified'}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" color="text.secondary">ID:</Typography>
                    <Typography variant="body2" fontWeight="medium" fontFamily="monospace">
                      {reportInfo?.report_id || reportId}
                    </Typography>
                  </Box>
                </>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Observation Management Metrics Row 1 - Six Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="primary.main" fontWeight="bold">
                {unifiedPhaseStatus?.metadata?.total_attributes || metricsData?.coverage_metrics?.total_attributes || 0}
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
                {unifiedPhaseStatus?.metadata?.scoped_attributes || metricsData?.coverage_metrics?.tested_attributes || 0}
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
                {unifiedPhaseStatus?.metadata?.total_samples || metricsData?.efficiency_metrics?.total_test_cases || 0}
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
            {unifiedPhaseStatus?.activities && unifiedPhaseStatus.activities.length > 0 ? (
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
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                {getObservationSteps().map((step, index) => (
                  <Box key={index} sx={{ flex: '1 1 200px', minWidth: 200 }}>
                    <Card 
                      sx={{ 
                        height: '100%',
                        bgcolor: step.status === 'completed' ? 'success.50' : 
                                step.status === 'active' ? 'primary.50' : 'grey.50',
                        border: step.status === 'active' ? 2 : 1,
                        borderColor: step.status === 'completed' ? 'success.main' : 
                                    step.status === 'active' ? 'primary.main' : 'grey.300'
                      }}
                    >
                      <CardContent sx={{ textAlign: 'center', py: 2 }}>
                        <Box sx={{ mb: 1 }}>
                          {step.icon}
                        </Box>
                        <Typography variant="subtitle2" fontWeight="medium" gutterBottom>
                          {step.label}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {step.description}
                        </Typography>
                        {!step.showButton && (
                          <Box sx={{ mt: 1 }}>
                            <Chip 
                              label={step.status.charAt(0).toUpperCase() + step.status.slice(1)}
                              size="small"
                              color={getStepColor(step.status) as any}
                              variant={step.status === 'active' ? 'filled' : 'outlined'}
                            />
                          </Box>
                        )}
                        {step.showButton && step.buttonAction && (
                          <Box sx={{ mt: 2 }}>
                            <Button
                              variant="contained"
                              size="small"
                              color="primary"
                              onClick={step.buttonAction}
                              startIcon={step.buttonIcon}
                            >
                              {step.buttonText}
                            </Button>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>

      {renderSummary()}

      <Box sx={{ mt: 3 }}>
        <Tabs value={selectedTab} onChange={(_, value) => setSelectedTab(value)}>
          <Tab label="Test Results Review" />
          <Tab label="Observation Groups" />
        </Tabs>

        <Box sx={{ mt: 2 }}>
          {selectedTab === 0 && renderTestExecutions()}
          {selectedTab === 1 && renderObservationGroups()}
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
    </Container>
  );
};

export default ObservationManagementEnhanced;