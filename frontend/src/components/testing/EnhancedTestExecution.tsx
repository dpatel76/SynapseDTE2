import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  LinearProgress,
  Grid,
  Badge,
  Divider,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  Storage as StorageIcon,
  PlayArrow as PlayArrowIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Psychology as PsychologyIcon,
  Code as CodeIcon,
  CompareArrows as CompareArrowsIcon,
  Visibility as VisibilityIcon,
  CloudUpload as CloudUploadIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNotifications } from '../../contexts/NotificationContext';
import apiClient from '../../api/client';

interface TestCase {
  test_case_id: string;
  sample_id: string;
  attribute_name: string;
  attribute_type: string;
  source_type: 'document' | 'query' | 'hybrid';
  source_reference?: string;
  expected_value?: any;
  actual_value?: any;
  test_method: 'llm_extraction' | 'query_comparison' | 'rule_based' | 'manual';
  status: 'pending' | 'in_progress' | 'passed' | 'failed' | 'skipped';
  confidence_score?: number;
  evidence?: {
    document_id?: string;
    query_id?: string;
    extracted_text?: string;
    query_result?: any;
  };
  test_results?: {
    match_percentage?: number;
    differences?: string[];
    llm_explanation?: string;
  };
}

interface EnhancedTestExecutionProps {
  cycleId: number;
  reportId: number;
  testCases: TestCase[];
  onTestComplete: (testCaseId: string, result: any) => void;
}

const EnhancedTestExecution: React.FC<EnhancedTestExecutionProps> = ({
  cycleId,
  reportId,
  testCases,
  onTestComplete,
}) => {
  const [selectedTestCase, setSelectedTestCase] = useState<TestCase | null>(null);
  const [testMethod, setTestMethod] = useState<'automatic' | 'manual'>('automatic');
  const [manualValue, setManualValue] = useState('');
  const [showComparisonDialog, setShowComparisonDialog] = useState(false);
  const [executionProgress, setExecutionProgress] = useState(0);
  const { showToast } = useNotifications();

  // Filter test cases by source type
  const documentBasedCases = testCases.filter(tc => tc.source_type === 'document');
  const queryBasedCases = testCases.filter(tc => tc.source_type === 'query');
  const hybridCases = testCases.filter(tc => tc.source_type === 'hybrid');

  // Execute test mutation
  const executeTestMutation = useMutation({
    mutationFn: async (testCase: TestCase) => {
      const response = await apiClient.post(
        `/test-execution/cycles/${cycleId}/reports/${reportId}/test-cases/${testCase.test_case_id}/execute`,
        {
          test_method: testCase.test_method,
          manual_value: testMethod === 'manual' ? manualValue : undefined,
        }
      );
      return response.data;
    },
    onSuccess: (data, variables) => {
      showToast('success', `Test case ${variables.test_case_id} executed successfully`);
      onTestComplete(variables.test_case_id, data);
      setSelectedTestCase(null);
      setShowComparisonDialog(false);
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Test execution failed');
    },
  });

  // Batch execution mutation
  const batchExecuteMutation = useMutation({
    mutationFn: async (testCaseIds: string[]) => {
      const response = await apiClient.post(
        `/test-execution/cycles/${cycleId}/reports/${reportId}/test-cases/batch-execute`,
        {
          test_case_ids: testCaseIds,
          test_method: 'automatic',
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      showToast('success', `Batch execution completed for ${data.executed_count} test cases`);
      data.results.forEach((result: any) => {
        onTestComplete(result.test_case_id, result);
      });
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Batch execution failed');
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'in_progress':
        return <PlayArrowIcon color="primary" />;
      case 'skipped':
        return <WarningIcon color="warning" />;
      default:
        return undefined;
    }
  };

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'document':
        return <DescriptionIcon />;
      case 'query':
        return <StorageIcon />;
      case 'hybrid':
        return <CompareArrowsIcon />;
      default:
        return null;
    }
  };

  const handleExecuteTest = (testCase: TestCase) => {
    setSelectedTestCase(testCase);
    if (testCase.source_type === 'document' && testCase.test_method === 'llm_extraction') {
      // For document-based LLM extraction, show comparison dialog
      setShowComparisonDialog(true);
    } else {
      // For query-based or rule-based, execute directly
      executeTestMutation.mutate(testCase);
    }
  };

  const handleBatchExecute = (sourceType: 'document' | 'query' | 'hybrid') => {
    const casesToExecute = testCases
      .filter(tc => tc.source_type === sourceType && tc.status === 'pending')
      .map(tc => tc.test_case_id);
    
    if (casesToExecute.length === 0) {
      showToast('info', 'No pending test cases to execute');
      return;
    }

    batchExecuteMutation.mutate(casesToExecute);
  };

  const renderTestCaseTable = (cases: TestCase[], title: string, sourceType: 'document' | 'query' | 'hybrid') => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6" display="flex" alignItems="center" gap={1}>
          {getSourceIcon(sourceType)}
          {title} ({cases.length})
        </Typography>
        <Button
          variant="contained"
          startIcon={<PlayArrowIcon />}
          onClick={() => handleBatchExecute(sourceType)}
          disabled={batchExecuteMutation.isPending || cases.filter(tc => tc.status === 'pending').length === 0}
        >
          Execute All Pending
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Sample ID</TableCell>
              <TableCell>Attribute</TableCell>
              <TableCell>Test Method</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Confidence</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {cases.map((testCase) => (
              <TableRow key={testCase.test_case_id}>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace">
                    {testCase.sample_id}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{testCase.attribute_name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {testCase.attribute_type}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={testCase.test_method.replace('_', ' ')}
                    size="small"
                    icon={testCase.test_method === 'llm_extraction' ? <PsychologyIcon /> : <CodeIcon />}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={testCase.status}
                    size="small"
                    icon={getStatusIcon(testCase.status)}
                    color={
                      testCase.status === 'passed' ? 'success' :
                      testCase.status === 'failed' ? 'error' :
                      testCase.status === 'in_progress' ? 'primary' : 'default'
                    }
                  />
                </TableCell>
                <TableCell>
                  {testCase.confidence_score && (
                    <Box display="flex" alignItems="center" gap={1}>
                      <LinearProgress
                        variant="determinate"
                        value={testCase.confidence_score * 100}
                        sx={{ width: 60, height: 6 }}
                        color={testCase.confidence_score >= 0.8 ? 'success' : 'warning'}
                      />
                      <Typography variant="caption">
                        {(testCase.confidence_score * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                  )}
                </TableCell>
                <TableCell align="center">
                  <Stack direction="row" spacing={1} justifyContent="center">
                    {testCase.status === 'pending' && (
                      <Tooltip title="Execute Test">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleExecuteTest(testCase)}
                        >
                          <PlayArrowIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedTestCase(testCase);
                          setShowComparisonDialog(true);
                        }}
                      >
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  return (
    <Box>
      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Test Cases
              </Typography>
              <Typography variant="h4">{testCases.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Passed
              </Typography>
              <Typography variant="h4" color="success.main">
                {testCases.filter(tc => tc.status === 'passed').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Failed
              </Typography>
              <Typography variant="h4" color="error.main">
                {testCases.filter(tc => tc.status === 'failed').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Pending
              </Typography>
              <Typography variant="h4" color="warning.main">
                {testCases.filter(tc => tc.status === 'pending').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Test Cases by Source Type */}
      <Stack spacing={3}>
        {documentBasedCases.length > 0 && (
          <Card>
            <CardContent>
              {renderTestCaseTable(documentBasedCases, 'Document-Based Tests (LLM)', 'document')}
            </CardContent>
          </Card>
        )}

        {queryBasedCases.length > 0 && (
          <Card>
            <CardContent>
              {renderTestCaseTable(queryBasedCases, 'Query-Based Tests', 'query')}
            </CardContent>
          </Card>
        )}

        {hybridCases.length > 0 && (
          <Card>
            <CardContent>
              {renderTestCaseTable(hybridCases, 'Hybrid Tests', 'hybrid')}
            </CardContent>
          </Card>
        )}
      </Stack>

      {/* Test Comparison Dialog */}
      <Dialog
        open={showComparisonDialog}
        onClose={() => setShowComparisonDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Test Case Execution
          {selectedTestCase && (
            <Typography variant="body2" color="text.secondary">
              {selectedTestCase.sample_id} - {selectedTestCase.attribute_name}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedTestCase && (
            <Stack spacing={3}>
              {/* Test Method Selection */}
              <FormControl fullWidth>
                <InputLabel>Test Method</InputLabel>
                <Select
                  value={testMethod}
                  onChange={(e) => setTestMethod(e.target.value as 'automatic' | 'manual')}
                >
                  <MenuItem value="automatic">
                    Automatic ({selectedTestCase.test_method})
                  </MenuItem>
                  <MenuItem value="manual">Manual Entry</MenuItem>
                </Select>
              </FormControl>

              {/* Expected vs Actual Values */}
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Expected Value
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="body1" fontFamily="monospace">
                      {selectedTestCase.expected_value || 'Not specified'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Actual Value
                  </Typography>
                  {testMethod === 'manual' ? (
                    <TextField
                      fullWidth
                      value={manualValue}
                      onChange={(e) => setManualValue(e.target.value)}
                      placeholder="Enter the actual value..."
                      multiline
                      rows={3}
                    />
                  ) : (
                    <Paper variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="body1" fontFamily="monospace">
                        {selectedTestCase.actual_value || 'To be extracted'}
                      </Typography>
                    </Paper>
                  )}
                </Grid>
              </Grid>

              {/* Evidence Section */}
              {selectedTestCase.evidence && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Evidence
                  </Typography>
                  {selectedTestCase.evidence.document_id && (
                    <Alert severity="info" icon={<DescriptionIcon />}>
                      Document ID: {selectedTestCase.evidence.document_id}
                    </Alert>
                  )}
                  {selectedTestCase.evidence.query_id && (
                    <Alert severity="info" icon={<StorageIcon />}>
                      Query ID: {selectedTestCase.evidence.query_id}
                    </Alert>
                  )}
                </Box>
              )}

              {/* Test Results Preview */}
              {selectedTestCase.test_results && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Test Results
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    {selectedTestCase.test_results.match_percentage !== undefined && (
                      <Typography variant="body2">
                        Match: {selectedTestCase.test_results.match_percentage}%
                      </Typography>
                    )}
                    {selectedTestCase.test_results.differences && (
                      <Typography variant="body2" color="error">
                        Differences: {selectedTestCase.test_results.differences.join(', ')}
                      </Typography>
                    )}
                    {selectedTestCase.test_results.llm_explanation && (
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {selectedTestCase.test_results.llm_explanation}
                      </Typography>
                    )}
                  </Paper>
                </Box>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowComparisonDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => {
              if (selectedTestCase) {
                executeTestMutation.mutate(selectedTestCase);
              }
            }}
            disabled={executeTestMutation.isPending}
          >
            Execute Test
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EnhancedTestExecution;