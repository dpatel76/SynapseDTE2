import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Button,
  Stack,
  LinearProgress,
  Divider,
  Tabs,
  Tab
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  CloudUpload as CloudUploadIcon,
  CheckCircle as CheckCircleIcon,
  Pending as PendingIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  OpenInNew as OpenInNewIcon,
  Dashboard as DashboardIcon,
  Description as DescriptionIcon,
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  ViewList as ViewListIcon,
  GridView as GridViewIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'react-hot-toast';
import { TestCasesTable, EvidenceUploadDialog, TestCaseDetailsDialog, AddDataSourceDialog } from '../../components/data-owner';

interface TestCaseAssignment {
  test_case_id: string;
  phase_id: string;
  cycle_id: number;
  cycle_name: string;
  report_id: number;
  report_name: string;
  attribute_name: string;
  sample_identifier: string;
  status: string;
  submission_deadline: string | null;
  submitted_at: string | null;
  primary_key_attributes: Record<string, any>;
  submission_count: number;
  document_count?: number; // For backwards compatibility
  has_submissions: boolean;
  latest_submission_at?: string | null;
}

interface DataProviderMetrics {
  total_test_cases: number;
  submitted_test_cases: number;
  pending_test_cases: number;
  overdue_test_cases: number;
  completion_percentage: number;
  active_phases: number;
}

interface PhaseAssignment {
  phase_id: string;
  cycle_id: number;
  cycle_name: string;
  report_id: number;
  report_name: string;
  phase_status: string;
  total_test_cases: number;
  submitted_test_cases: number;
  pending_test_cases: number;
  completion_percentage: number;
  submission_deadline: string | null;
  days_remaining: number;
}


const DataOwnerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<TestCaseAssignment[]>([]);
  const [phases, setPhases] = useState<PhaseAssignment[]>([]);
  const [metrics, setMetrics] = useState<DataProviderMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTestCase, setSelectedTestCase] = useState<TestCaseAssignment | null>(null);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [addDataSourceDialogOpen, setAddDataSourceDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'grouped'>('table');

  useEffect(() => {
    loadDashboardData();
    
    // Listen for event to open add data source dialog
    const handleOpenAddDataSource = () => {
      setAddDataSourceDialogOpen(true);
    };
    
    window.addEventListener('open-add-data-source', handleOpenAddDataSource);
    
    return () => {
      window.removeEventListener('open-add-data-source', handleOpenAddDataSource);
    };
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('[Data Owner Dashboard] Loading dashboard data...');
      
      // Get all test cases assigned to this data owner
      const testCasesResponse = await apiClient.get('/request-info/data-owner/test-cases');
      const portalData = testCasesResponse.data;
      const testCases = portalData?.test_cases || [];
      
      console.log('[Data Owner Dashboard] Portal data:', portalData);
      console.log('[Data Owner Dashboard] Test cases:', testCases);
      setAssignments(testCases);

      // Debug: Log the first test case to see what data we have
      if (testCases.length > 0) {
        console.log('[Data Owner Dashboard] First test case sample:', testCases[0]);
        // Log all test cases for cycle 58, report 156
        const cycle58Cases = testCases.filter((tc: any) => tc.cycle_id === 58 && tc.report_id === 156);
        console.log('[Data Owner Dashboard] Cycle 58 test cases:', cycle58Cases);
      }

      // Group test cases by phase to create phase summaries
      const phaseMap = new Map<string, PhaseAssignment>();
      
      testCases.forEach((testCase: any) => {
        const phaseKey = testCase.phase_id;
        
        if (!phaseMap.has(phaseKey)) {
          phaseMap.set(phaseKey, {
            phase_id: testCase.phase_id,
            cycle_id: testCase.cycle_id,
            cycle_name: testCase.cycle_name || `Cycle ${testCase.cycle_id}`,
            report_id: testCase.report_id,
            report_name: testCase.report_name || `Report ${testCase.report_id}`,
            phase_status: 'In Progress',
            total_test_cases: 0,
            submitted_test_cases: 0,
            pending_test_cases: 0,
            completion_percentage: 0,
            submission_deadline: testCase.submission_deadline,
            days_remaining: 0
          });
        }
        
        const phase = phaseMap.get(phaseKey)!;
        phase.total_test_cases++;
        
        if (testCase.status === 'Submitted') {
          phase.submitted_test_cases++;
        } else {
          phase.pending_test_cases++;
        }
        
        phase.completion_percentage = (phase.submitted_test_cases / phase.total_test_cases) * 100;
        
        // Calculate days remaining
        if (testCase.submission_deadline) {
          const deadline = new Date(testCase.submission_deadline);
          const now = new Date();
          const diffTime = deadline.getTime() - now.getTime();
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
          phase.days_remaining = Math.max(0, diffDays);
        }
      });
      
      const phasesArray = Array.from(phaseMap.values());
      setPhases(phasesArray);

      // Use metrics from portal data
      setMetrics({
        total_test_cases: portalData?.total_assigned || 0,
        submitted_test_cases: portalData?.total_submitted || 0,
        pending_test_cases: portalData?.total_pending || 0,
        overdue_test_cases: portalData?.total_overdue || 0,
        completion_percentage: (portalData?.total_assigned > 0 && portalData?.total_submitted) 
          ? (portalData.total_submitted / portalData.total_assigned) * 100 
          : 0,
        active_phases: phasesArray.length
      });

    } catch (err: any) {
      console.error('[Data Owner Dashboard] Error loading data:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadDashboardData();
  };

  const handleUploadClick = (testCase: TestCaseAssignment) => {
    setSelectedTestCase(testCase);
    setUploadDialogOpen(true);
  };

  const handleViewDetails = (testCase: TestCaseAssignment) => {
    setSelectedTestCase(testCase);
    setDetailsDialogOpen(true);
  };

  const handleSubmitTestCase = async (testCaseId: string, attributeName: string) => {
    setSubmitting(testCaseId);
    try {
      // Update test case status to submitted
      await apiClient.put(`/request-info/test-cases/${testCaseId}`, {
        status: 'Submitted'
      });

      toast.success(`${attributeName} submitted successfully`);
      loadDashboardData(); // Refresh data
    } catch (err: any) {
      console.error('Submit error:', err);
      toast.error(err.response?.data?.detail || 'Failed to submit test case');
    } finally {
      setSubmitting(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'submitted': return 'success';
      case 'pending': return 'warning';
      case 'overdue': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'submitted': return <CheckCircleIcon />;
      case 'pending': return <PendingIcon />;
      case 'overdue': return <WarningIcon />;
      default: return <AssignmentIcon />;
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'No deadline';
    return new Date(dateString).toLocaleDateString();
  };

  const navigateToPhase = (phase: PhaseAssignment) => {
    navigate(`/cycles/${phase.cycle_id}/reports/${phase.report_id}/request-info`);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mx: -3, px: 3 }}>
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          <Alert severity="error" action={
            <Button color="inherit" size="small" onClick={handleRefresh}>
              <RefreshIcon /> Retry
            </Button>
          }>
            {error}
          </Alert>
        </Container>
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4, mx: -3, px: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DashboardIcon color="primary" />
            Data Owner Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Welcome back, {user?.first_name} {user?.last_name}. Here are your document submission assignments.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => setAddDataSourceDialogOpen(true)}
          >
            Add Data Source
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Metrics Cards */}
      {metrics && (
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3} sx={{ mb: 4 }}>
          <Card sx={{ flex: 1 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    Total Assignments
                  </Typography>
                  <Typography variant="h4">
                    {metrics.total_test_cases}
                  </Typography>
                </Box>
                <AssignmentIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
          
          <Card sx={{ flex: 1 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    Submitted
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {metrics.submitted_test_cases}
                  </Typography>
                </Box>
                <CheckCircleIcon color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
          
          <Card sx={{ flex: 1 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    Pending
                  </Typography>
                  <Typography variant="h4" color="warning.main">
                    {metrics.pending_test_cases}
                  </Typography>
                </Box>
                <PendingIcon color="warning" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
          
          <Card sx={{ flex: 1 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="h6">
                    Completion
                  </Typography>
                  <Typography variant="h4" color="primary.main">
                    {metrics.completion_percentage.toFixed(0)}%
                  </Typography>
                </Box>
                <DescriptionIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={metrics.completion_percentage} 
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Stack>
      )}

      {/* Active Phases */}
      {phases.length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CloudUploadIcon color="primary" />
              Active Request for Information Phases
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Cycle & Report</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell>Test Cases</TableCell>
                    <TableCell>Deadline</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {phases.map((phase) => (
                    <TableRow key={phase.phase_id} hover>
                      <TableCell>
                        <Box>
                          <Typography variant="subtitle2">
                            {phase.cycle_name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {phase.report_name}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={phase.completion_percentage} 
                            sx={{ width: 100 }}
                          />
                          <Typography variant="body2">
                            {phase.completion_percentage.toFixed(0)}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1}>
                          <Chip 
                            label={`${phase.submitted_test_cases} submitted`}
                            color="success"
                            size="small"
                          />
                          <Chip 
                            label={`${phase.pending_test_cases} pending`}
                            color="warning"
                            size="small"
                          />
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2">
                            {formatDate(phase.submission_deadline)}
                          </Typography>
                          {phase.days_remaining > 0 && (
                            <Typography variant="caption" color="text.secondary">
                              {phase.days_remaining} days remaining
                            </Typography>
                          )}
                          {phase.days_remaining === 0 && (
                            <Typography variant="caption" color="error">
                              Due today
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Tooltip title="View Phase Details">
                          <IconButton 
                            color="primary"
                            onClick={() => navigateToPhase(phase)}
                          >
                            <OpenInNewIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Test Cases */}
      {assignments.length > 0 ? (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AssignmentIcon color="primary" />
                Test Case Assignments
              </Typography>
              <Tabs value={viewMode} onChange={(e, newValue) => setViewMode(newValue)}>
                <Tab icon={<ViewListIcon />} iconPosition="start" label="Table View" value="table" />
                <Tab icon={<GridViewIcon />} iconPosition="start" label="Grouped View" value="grouped" />
              </Tabs>
            </Box>
            
            {viewMode === 'table' ? (
              (() => {
                // Group test cases by cycle_id and report_id
                const groupedByCycleReport = assignments.reduce((acc, tc) => {
                  const key = `${tc.cycle_id}_${tc.report_id}`;
                  if (!acc[key]) {
                    acc[key] = {
                      cycle_id: tc.cycle_id,
                      cycle_name: tc.cycle_name || `Cycle ${tc.cycle_id}`,
                      report_id: tc.report_id,
                      report_name: tc.report_name || `Report ${tc.report_id}`,
                      testCases: []
                    };
                  }
                  acc[key].testCases.push(tc);
                  return acc;
                }, {} as Record<string, { cycle_id: number; cycle_name: string; report_id: number; report_name: string; testCases: TestCaseAssignment[] }>);

                // Render a separate table for each cycle/report combination
                return (
                  <Box>
                    {Object.values(groupedByCycleReport).map((group) => (
                      <Box key={`${group.cycle_id}_${group.report_id}`} sx={{ mb: 4 }}>
                        <TestCasesTable 
                          testCases={group.testCases.map(tc => ({
                            ...tc,
                            sample_id: tc.sample_identifier, // Map sample_identifier to sample_id
                            attribute_id: 0, // Default value since it's not in TestCaseAssignment
                            data_owner_id: user?.user_id || 0, // Use current user's ID
                            data_owner_name: user?.first_name + ' ' + user?.last_name || user?.email || '',
                            data_owner_email: user?.email || '',
                            submission_count: tc.submission_count || tc.document_count || 0 // Use submission_count from backend
                          }))}
                          cycleName={group.cycle_name}
                          reportName={group.report_name}
                          onUpload={(testCase: any) => handleUploadClick(testCase)}
                          onSubmit={(testCase: any) => handleSubmitTestCase(testCase.test_case_id, testCase.attribute_name)}
                          onViewEvidence={(testCase: any) => {
                            // TODO: Implement view evidence
                            toast('View evidence coming soon', { icon: 'ℹ️' });
                          }}
                          onViewDetails={(testCase: any) => handleViewDetails(testCase)}
                        />
                      </Box>
                    ))}
                  </Box>
                );
              })()
            ) : (
              (() => {
              // Group assignments by cycle → report → sample
              const groupedAssignments = assignments.reduce((acc, assignment) => {
                const cycleKey = `${assignment.cycle_id}-${assignment.cycle_name}`;
                const reportKey = `${assignment.report_id}-${assignment.report_name}`;
                const sampleKey = assignment.sample_identifier;
                
                if (!acc[cycleKey]) {
                  acc[cycleKey] = {
                    cycle_id: assignment.cycle_id,
                    cycle_name: assignment.cycle_name,
                    reports: {}
                  };
                }
                
                if (!acc[cycleKey].reports[reportKey]) {
                  acc[cycleKey].reports[reportKey] = {
                    report_id: assignment.report_id,
                    report_name: assignment.report_name,
                    samples: {}
                  };
                }
                
                if (!acc[cycleKey].reports[reportKey].samples[sampleKey]) {
                  acc[cycleKey].reports[reportKey].samples[sampleKey] = {
                    sample_identifier: assignment.sample_identifier,
                    primary_key_attributes: assignment.primary_key_attributes,
                    attributes: []
                  };
                }
                
                acc[cycleKey].reports[reportKey].samples[sampleKey].attributes.push(assignment);
                
                return acc;
              }, {} as any);
              
              return Object.values(groupedAssignments).map((cycle: any) => (
                <Box key={cycle.cycle_id} sx={{ mb: 4 }}>
                  {/* Cycle Header */}
                  <Typography variant="h6" sx={{ mb: 2, color: 'primary.main', fontWeight: 'bold' }}>
                    📊 {cycle.cycle_name}
                  </Typography>
                  
                  {Object.values(cycle.reports).map((report: any) => (
                    <Box key={report.report_id} sx={{ mb: 3, ml: 2 }}>
                      {/* Report Header */}
                      <Typography variant="subtitle1" sx={{ mb: 2, color: 'text.primary', fontWeight: 'medium' }}>
                        📋 {report.report_name}
                      </Typography>
                      
                      {Object.values(report.samples).map((sample: any) => (
                        <Card key={sample.sample_identifier} variant="outlined" sx={{ mb: 2, ml: 2 }}>
                          <CardContent sx={{ pb: 2 }}>
                            {/* Sample Header with Primary Key Values */}
                            <Box sx={{ mb: 2 }}>
                              <Typography variant="subtitle2" sx={{ fontFamily: 'monospace', fontWeight: 'bold', mb: 1 }}>
                                🔍 Sample: {sample.sample_identifier}
                              </Typography>
                              
                              {/* Primary Key Values */}
                              {sample.primary_key_attributes && Object.keys(sample.primary_key_attributes).length > 0 && (
                                <Box sx={{ ml: 2 }}>
                                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'medium' }}>
                                    Primary Key Values:
                                  </Typography>
                                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 0.5 }}>
                                    {Object.entries(sample.primary_key_attributes).map(([key, value]) => (
                                      <Chip
                                        key={key}
                                        label={`${key}: ${value}`}
                                        size="small"
                                        variant="outlined"
                                        color="primary"
                                        sx={{ fontSize: '0.75rem' }}
                                      />
                                    ))}
                                  </Box>
                                </Box>
                              )}
                            </Box>
                            
                            {/* Attributes List */}
                            <Box sx={{ ml: 2 }}>
                              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'medium', mb: 1, display: 'block' }}>
                                Attributes to Submit:
                              </Typography>
                              
                              {sample.attributes.map((assignment: any) => (
                                <Box 
                                  key={assignment.test_case_id} 
                                  sx={{ 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    justifyContent: 'space-between',
                                    py: 1,
                                    px: 2,
                                    mb: 1,
                                    backgroundColor: assignment.status === 'Submitted' ? 'success.light' : 'grey.50',
                                    borderRadius: 1,
                                    border: 1,
                                    borderColor: assignment.status === 'Submitted' ? 'success.main' : 'grey.300'
                                  }}
                                >
                                  <Box sx={{ flex: 1 }}>
                                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                                      {assignment.attribute_name}
                                    </Typography>
                                    
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                                      <Chip
                                        icon={getStatusIcon(assignment.status)}
                                        label={assignment.status}
                                        color={getStatusColor(assignment.status)}
                                        size="small"
                                      />
                                      
                                      {assignment.submission_count > 0 && (
                                        <Chip
                                          icon={<AttachFileIcon />}
                                          label={`${assignment.submission_count} file${assignment.submission_count > 1 ? 's' : ''}`}
                                          size="small"
                                          variant="outlined"
                                        />
                                      )}
                                      
                                      {assignment.submission_deadline && (
                                        <Typography variant="caption" color="text.secondary">
                                          Due: {formatDate(assignment.submission_deadline)}
                                        </Typography>
                                      )}
                                      
                                      {assignment.submitted_at && (
                                        <Typography variant="caption" color="success.main">
                                          Submitted: {formatDate(assignment.submitted_at)}
                                        </Typography>
                                      )}
                                    </Box>
                                  </Box>
                                  
                                  {/* Action Buttons */}
                                  <Box sx={{ display: 'flex', gap: 1, ml: 2 }}>
                                    {assignment.status !== 'Submitted' && assignment.status !== 'Complete' && (
                                      <Button
                                        variant="contained"
                                        color="primary"
                                        size="small"
                                        startIcon={<CloudUploadIcon />}
                                        onClick={() => handleUploadClick(assignment)}
                                        sx={{ minWidth: 100 }}
                                      >
                                        Upload
                                      </Button>
                                    )}
                                    
                                    {assignment.status !== 'Submitted' && assignment.submission_count > 0 && (
                                      <Button
                                        variant="outlined"
                                        color="success"
                                        size="small"
                                        startIcon={submitting === assignment.test_case_id ? <CircularProgress size={16} /> : <SendIcon />}
                                        onClick={() => handleSubmitTestCase(assignment.test_case_id, assignment.attribute_name)}
                                        disabled={submitting === assignment.test_case_id}
                                        sx={{ minWidth: 100 }}
                                      >
                                        Submit
                                      </Button>
                                    )}
                                    
                                    {assignment.status === 'Submitted' && (
                                      <Button
                                        variant="outlined"
                                        color="success"
                                        size="small"
                                        startIcon={<CheckCircleIcon />}
                                        onClick={() => navigate(`/cycles/${assignment.cycle_id}/reports/${assignment.report_id}/request-info`)}
                                        sx={{ minWidth: 100 }}
                                      >
                                        View
                                      </Button>
                                    )}
                                  </Box>
                                </Box>
                              ))}
                            </Box>
                          </CardContent>
                        </Card>
                      ))}
                    </Box>
                  ))}
                </Box>
              ));
            })()
            )}
          </CardContent>
        </Card>
      ) : (
        <Alert severity="info">
          <Typography variant="h6" gutterBottom>
            No assignments found
          </Typography>
          <Typography>
            You don't have any test case assignments yet. Assignments will appear here when Request for Information phases are started and test cases are generated.
          </Typography>
        </Alert>
      )}

      {/* Evidence Upload Dialog */}
      <EvidenceUploadDialog
        open={uploadDialogOpen}
        onClose={() => {
          setUploadDialogOpen(false);
          setSelectedTestCase(null);
        }}
        testCase={selectedTestCase}
        onSuccess={() => {
          setUploadDialogOpen(false);
          setSelectedTestCase(null);
          loadDashboardData(); // Refresh data
        }}
      />

      {/* Test Case Details Dialog */}
      <TestCaseDetailsDialog
        open={detailsDialogOpen}
        onClose={() => {
          setDetailsDialogOpen(false);
          setSelectedTestCase(null);
        }}
        testCase={selectedTestCase}
      />
      
      {/* Add Data Source Dialog */}
      <AddDataSourceDialog
        open={addDataSourceDialogOpen}
        onClose={() => setAddDataSourceDialogOpen(false)}
        onSuccess={() => {
          setAddDataSourceDialogOpen(false);
          toast.success('Data source added successfully');
        }}
      />
    </Container>
  );
};

export default DataOwnerDashboard; 