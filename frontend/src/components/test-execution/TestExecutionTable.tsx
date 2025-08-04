import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Box,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  TableSortLabel,
  TablePagination,
  Badge,
  Grid,
  Card,
  CardContent,
  Divider,
  FormControl,
  FormLabel,
  RadioGroup,
  Radio,
  FormControlLabel,
  Alert,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  CheckCircle,
  Cancel,
  Error as ErrorIcon,
  CompareArrows,
  AssignmentReturn,
  PlayArrow,
  Timer,
  Description,
  Storage as StorageIcon,
  BugReport as BugReportIcon,
} from '@mui/icons-material';
import { EvidenceModal } from '../shared/EvidenceModal';
import { TestExecutionResults } from './TestExecutionResults';
import { TestExecution } from '../../types/test-execution';

interface TestCase {
  // Basic test case info
  id: number;
  test_case_id: string;
  test_name?: string;
  sample_id: string;
  sample_identifier: string;
  primary_key_attributes?: any;
  attribute_id: number;
  attribute_name: string;
  data_type?: string;
  is_scoped?: boolean;
  
  // Data owner info
  data_owner_id: number;
  data_owner_name: string;
  data_owner_email?: string;
  
  // Evidence info
  has_evidence: boolean;
  evidence_count: number;
  document_count?: number;
  evidence_type?: string;
  evidence_id?: number;
  
  // Expected values
  expected_value?: string;
  sample_value?: string;
  
  // Test execution info
  status: string;
  execution_status?: string;
  execution_id?: number;
  extracted_value?: string;
  test_result?: string;
  confidence_score?: number;
  comparison_result?: string;
  analysis_rationale?: string;
  analysis_results?: Record<string, any>;
  
  // Timestamps
  submitted_at?: string;
  executed_at?: string;
  
  // Other
  special_instructions?: string;
  submission_id?: string;
  sample_record_id?: string;
  primary_key_values?: any;
  evidence_uploaded?: boolean;
  has_observation?: boolean;
}

interface TestExecutionTableProps {
  testCases: TestCase[];
  onExecuteTest?: (testCase: TestCase) => void;
  onViewEvidence?: (testCase: TestCase) => void;
  onViewComparison?: (testCase: TestCase) => void;
  onReviewResult?: (testCase: TestCase, decision: 'pass' | 'fail' | 'resend') => void;
  onViewObservation?: (testCase: TestCase) => void;
  userRole?: string;
}

type OrderDirection = 'asc' | 'desc';

export const TestExecutionTable: React.FC<TestExecutionTableProps> = ({
  testCases,
  onExecuteTest,
  onViewEvidence,
  onViewComparison,
  onReviewResult,
  onViewObservation,
  userRole = 'Tester',
}) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [orderBy, setOrderBy] = useState<keyof TestCase>('test_case_id');
  const [orderDirection, setOrderDirection] = useState<OrderDirection>('asc');
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);
  const [selectedTestCaseId, setSelectedTestCaseId] = useState<string | null>(null);
  const [selectedTestCase, setSelectedTestCase] = useState<TestCase | null>(null);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [reviewDecision, setReviewDecision] = useState<'pass' | 'fail' | 'resend'>('pass');
  const [reviewNotes, setReviewNotes] = useState('');
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);

  const handleSort = (property: keyof TestCase) => {
    const isAsc = orderBy === property && orderDirection === 'asc';
    setOrderDirection(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleEvidenceClick = (testCase: TestCase) => {
    // Remove the "tc_" prefix if present
    const testCaseId = testCase.test_case_id.startsWith('tc_') 
      ? testCase.test_case_id.substring(3) 
      : testCase.test_case_id;
    setSelectedTestCaseId(testCaseId);
    setEvidenceModalOpen(true);
  };


  const handleReviewClick = (testCase: TestCase) => {
    setSelectedTestCase(testCase);
    setReviewModalOpen(true);
    setReviewDecision('pass');
    setReviewNotes('');
  };

  const handleReviewSubmit = () => {
    if (selectedTestCase && onReviewResult) {
      onReviewResult(selectedTestCase, reviewDecision);
    }
    setReviewModalOpen(false);
    setSelectedTestCase(null);
  };

  const getExecutionStatusColor = (status?: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'info';
      case 'failed': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const getTestResultColor = (result?: string) => {
    switch (result) {
      case 'pass': return 'success';
      case 'fail': return 'error';
      case 'inconclusive': return 'warning';
      default: return 'default';
    }
  };

  const formatPrimaryKeyValues = (pkAttributes: any) => {
    if (!pkAttributes || typeof pkAttributes !== 'object') {
      return {};
    }
    return pkAttributes;
  };

  // Get unique primary key columns from all test cases
  const primaryKeyColumns = React.useMemo(() => {
    const pkSet = new Set<string>();
    testCases.forEach(tc => {
      const pkData = tc.primary_key_attributes || tc.primary_key_values;
      if (pkData && typeof pkData === 'object') {
        Object.keys(pkData).forEach(key => pkSet.add(key));
      }
    });
    return Array.from(pkSet).sort();
  }, [testCases]);

  const sortedTestCases = [...testCases].sort((a, b) => {
    const aValue = a[orderBy];
    const bValue = b[orderBy];
    
    if (aValue === null || aValue === undefined) return 1;
    if (bValue === null || bValue === undefined) return -1;
    
    if (aValue < bValue) {
      return orderDirection === 'asc' ? -1 : 1;
    }
    if (aValue > bValue) {
      return orderDirection === 'asc' ? 1 : -1;
    }
    return 0;
  });

  const paginatedTestCases = sortedTestCases.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // Calculate execution summary
  const executionSummary = React.useMemo(() => {
    const total = testCases.length;
    const executed = testCases.filter(tc => tc.execution_status === 'completed').length;
    const passed = testCases.filter(tc => tc.test_result === 'pass').length;
    const failed = testCases.filter(tc => tc.test_result === 'fail').length;
    const running = testCases.filter(tc => tc.execution_status === 'running').length;
    const pending = total - executed - running;
    
    return { total, executed, passed, failed, running, pending };
  }, [testCases]);

  return (
    <Box>
      {/* Execution Summary */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Chip 
          label={`Total: ${executionSummary.total}`} 
          color="default" 
          variant="outlined"
        />
        <Chip 
          label={`Executed: ${executionSummary.executed}`} 
          color={executionSummary.executed === executionSummary.total ? "success" : "primary"}
          variant={executionSummary.executed > 0 ? "filled" : "outlined"}
        />
        <Chip 
          label={`Passed: ${executionSummary.passed}`} 
          color="success" 
          icon={<CheckCircle />}
          variant={executionSummary.passed > 0 ? "filled" : "outlined"}
        />
        <Chip 
          label={`Failed: ${executionSummary.failed}`} 
          color="error" 
          icon={<Cancel />}
          variant={executionSummary.failed > 0 ? "filled" : "outlined"}
        />
        {executionSummary.running > 0 && (
          <Chip 
            label={`Running: ${executionSummary.running}`} 
            color="info" 
            icon={<Timer />}
            variant="filled"
          />
        )}
        {executionSummary.pending > 0 && (
          <Chip 
            label={`Pending: ${executionSummary.pending}`} 
            color="warning" 
            variant="outlined"
          />
        )}
      </Box>

      <TableContainer component={Paper} elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'grey.50' }}>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'test_case_id'}
                  direction={orderBy === 'test_case_id' ? orderDirection : 'asc'}
                  onClick={() => handleSort('test_case_id')}
                >
                  Test ID
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'sample_id'}
                  direction={orderBy === 'sample_id' ? orderDirection : 'asc'}
                  onClick={() => handleSort('sample_id')}
                >
                  Sample ID
                </TableSortLabel>
              </TableCell>
              {/* Dynamic PK columns */}
              {primaryKeyColumns.map((pkCol) => (
                <TableCell key={pkCol}>
                  <TableSortLabel
                    active={false}
                    disabled
                  >
                    {pkCol}
                  </TableSortLabel>
                </TableCell>
              ))}
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'attribute_name'}
                  direction={orderBy === 'attribute_name' ? orderDirection : 'asc'}
                  onClick={() => handleSort('attribute_name')}
                >
                  Attribute & Sample Value
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'data_owner_name'}
                  direction={orderBy === 'data_owner_name' ? orderDirection : 'asc'}
                  onClick={() => handleSort('data_owner_name')}
                >
                  Data Owner
                </TableSortLabel>
              </TableCell>
              <TableCell align="center">Evidence</TableCell>
              <TableCell align="center">Comparison</TableCell>
              <TableCell align="center">Execution Status</TableCell>
              <TableCell align="center">Test Result</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedTestCases.map((testCase) => (
              <TableRow
                key={testCase.test_case_id}
                hover
                sx={{
                  '&:hover': { bgcolor: 'action.hover' },
                  borderBottom: 1,
                  borderColor: 'divider',
                  bgcolor: testCase.execution_status === 'completed' 
                    ? testCase.test_result === 'pass' 
                      ? 'success.50' 
                      : testCase.test_result === 'fail'
                        ? 'error.50'
                        : 'grey.50'
                    : testCase.execution_status === 'running'
                      ? 'info.50'
                      : testCase.execution_status === 'failed'
                        ? 'error.100'
                        : 'transparent',
                  opacity: testCase.execution_status === 'completed' && testCase.test_result === 'pass' ? 0.9 : 1,
                }}
              >
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {testCase.test_case_id}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {testCase.sample_id || testCase.sample_identifier || '-'}
                  </Typography>
                </TableCell>
                {/* Dynamic PK value cells */}
                {primaryKeyColumns.map((pkCol) => {
                  const pkValues = formatPrimaryKeyValues(testCase.primary_key_attributes || testCase.primary_key_values);
                  return (
                    <TableCell key={pkCol}>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                        {pkValues[pkCol] || '-'}
                      </Typography>
                    </TableCell>
                  );
                })}
                <TableCell>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {testCase.attribute_name}
                    </Typography>
                    {testCase.data_type && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        Type: {testCase.data_type}
                      </Typography>
                    )}
                    {(testCase.sample_value || testCase.expected_value) && (
                      <Box sx={{ mt: 0.5, p: 1, bgcolor: 'primary.50', borderRadius: 0.5, border: 1, borderColor: 'primary.200' }}>
                        <Typography variant="caption" color="primary.main" sx={{ fontWeight: 'medium' }}>
                          Sample Value:
                        </Typography>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', color: 'primary.dark' }}>
                          {testCase.sample_value || testCase.expected_value}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{testCase.data_owner_name}</Typography>
                </TableCell>
                <TableCell align="center">
                  <IconButton
                    size="small"
                    onClick={() => handleEvidenceClick(testCase)}
                    disabled={!testCase.has_evidence}
                  >
                    <Badge badgeContent={testCase.evidence_count} color="primary" max={9}>
                      {testCase.evidence_type === 'data_source' ? (
                        <StorageIcon />
                      ) : (
                        <Description />
                      )}
                    </Badge>
                  </IconButton>
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="View Sample vs Extracted Comparison">
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedTestCase(testCase);
                        setComparisonModalOpen(true);
                      }}
                      disabled={!testCase.execution_status || testCase.execution_status !== 'completed'}
                      color="primary"
                    >
                      <CompareArrows />
                    </IconButton>
                  </Tooltip>
                </TableCell>
                <TableCell align="center">
                  {testCase.execution_status ? (
                    <Chip
                      label={
                        testCase.execution_status === 'failed' 
                          ? 'Failed - Retry Available'
                          : testCase.execution_status
                      }
                      size="small"
                      color={getExecutionStatusColor(testCase.execution_status)}
                      icon={
                        testCase.execution_status === 'running' ? <Timer /> :
                        testCase.execution_status === 'failed' ? <ErrorIcon /> :
                        undefined
                      }
                    />
                  ) : (
                    <Typography variant="caption" color="text.secondary">
                      Not Executed
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">
                  {testCase.test_result ? (
                    <Chip
                      label={testCase.test_result}
                      size="small"
                      color={getTestResultColor(testCase.test_result)}
                      icon={
                        testCase.test_result === 'pass' ? <CheckCircle /> :
                        testCase.test_result === 'fail' ? <Cancel /> :
                        <ErrorIcon />
                      }
                    />
                  ) : (
                    <Typography variant="caption" color="text.secondary">
                      -
                    </Typography>
                  )}
                  {testCase.confidence_score !== undefined && (
                    <Typography variant="caption" display="block" color="text.secondary">
                      {Math.round(testCase.confidence_score * 100)}% confidence
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">
                  <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                    {!testCase.execution_status || testCase.execution_status === 'failed' ? (
                      <Tooltip title={testCase.execution_status === 'failed' ? "Retry Test Execution" : "Execute Test"}>
                        <IconButton
                          size="small"
                          onClick={() => onExecuteTest && onExecuteTest(testCase)}
                          color="primary"
                          disabled={!testCase.has_evidence}
                        >
                          <PlayArrow />
                        </IconButton>
                      </Tooltip>
                    ) : testCase.execution_status === 'running' ? (
                      <Tooltip title="Test execution in progress">
                        <IconButton size="small" disabled>
                          <Timer />
                        </IconButton>
                      </Tooltip>
                    ) : testCase.execution_status === 'completed' ? (
                      userRole === 'Observer' ? (
                        // Read-only view for Observer role - show create/view observation for failed tests
                        testCase.test_result !== 'pass' ? (
                          testCase.has_observation ? (
                            <Tooltip title="View Observation">
                              <IconButton
                                size="small"
                                onClick={() => {
                                  if (onViewObservation) {
                                    onViewObservation(testCase);
                                  }
                                }}
                                color="primary"
                              >
                                <VisibilityIcon />
                              </IconButton>
                            </Tooltip>
                          ) : (
                            <Tooltip title="Create Observation">
                              <IconButton
                                size="small"
                                onClick={() => {
                                  if (onReviewResult) {
                                    onReviewResult(testCase, 'fail');
                                  }
                                }}
                                color="error"
                              >
                                <BugReportIcon />
                              </IconButton>
                            </Tooltip>
                          )
                        ) : (
                          <Typography variant="caption" color="success.main">
                            Passed
                          </Typography>
                        )
                      ) : (
                        // Full review functionality for Tester role
                        <TestExecutionResults
                          execution={{
                            id: testCase.execution_id || testCase.id,
                            test_case_id: testCase.test_case_id,
                            execution_status: testCase.execution_status,
                            test_result: testCase.test_result,
                            extracted_value: testCase.extracted_value,
                            expected_value: testCase.expected_value || testCase.sample_value,
                            comparison_result: testCase.comparison_result,
                            llm_confidence_score: testCase.confidence_score,
                            llm_analysis_rationale: testCase.analysis_rationale,
                            analysis_results: testCase.analysis_results || {},
                          } as TestExecution}
                          testCase={{
                            ...testCase,
                            primary_key_attributes: testCase.primary_key_attributes || testCase.primary_key_values,
                          }}
                          sampleData={{
                            sample_data: {
                              [testCase.attribute_name]: testCase.sample_value || testCase.expected_value,
                              ...testCase.primary_key_attributes,
                              ...testCase.primary_key_values,
                            }
                          }}
                          onReviewComplete={() => {
                            // Refresh the table data
                            window.location.reload();
                          }}
                        />
                      )
                    ) : null}
                    
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50]}
        component="div"
        count={testCases.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />

      {/* Evidence Modal */}
      <EvidenceModal
        open={evidenceModalOpen}
        testCaseId={selectedTestCaseId || ''}
        onClose={() => {
          setEvidenceModalOpen(false);
          setSelectedTestCaseId(null);
        }}
      />

      {/* Comparison Modal */}
      <Dialog 
        open={comparisonModalOpen} 
        onClose={() => setComparisonModalOpen(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>Sample vs Extracted Value Comparison</DialogTitle>
        <DialogContent>
          {selectedTestCase && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12 }}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle2" gutterBottom>
                        Test Case Information
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Test ID: {selectedTestCase.test_case_id}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Sample ID: {selectedTestCase.sample_id || selectedTestCase.sample_identifier || '-'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Attribute: {selectedTestCase.attribute_name}
                      </Typography>
                      {selectedTestCase.data_type && (
                        <Typography variant="body2" color="text.secondary">
                          Data Type: {selectedTestCase.data_type}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid size={{ xs: 12, md: 6 }}>
                  <Card sx={{ border: 1, borderColor: 'primary.main' }}>
                    <CardContent>
                      <Typography variant="h6" color="primary" gutterBottom>
                        Expected Value
                      </Typography>
                      <Box sx={{ bgcolor: 'primary.50', p: 2, borderRadius: 1, minHeight: 80 }}>
                        <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                          {selectedTestCase.expected_value || selectedTestCase.sample_value || 'No sample value'}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid size={{ xs: 12, md: 6 }}>
                  <Card sx={{ border: 1, borderColor: 'success.main' }}>
                    <CardContent>
                      <Typography variant="h6" color="success.main" gutterBottom>
                        Extracted Value
                      </Typography>
                      <Box sx={{ bgcolor: 'success.50', p: 2, borderRadius: 1, minHeight: 80 }}>
                        <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                          {selectedTestCase.extracted_value || 'No extracted value'}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid size={{ xs: 12 }}>
                  <Alert 
                    severity={
                      selectedTestCase.extracted_value === selectedTestCase.expected_value 
                        ? 'success' 
                        : 'warning'
                    }
                  >
                    {selectedTestCase.extracted_value === selectedTestCase.expected_value 
                      ? 'Values match!' 
                      : 'Values do not match - review required'}
                  </Alert>
                </Grid>
                
                {/* Primary Key Comparison */}
                {(() => {
                  // Check if we have primary key data to display
                  // Match the logic from TestExecutionResults component
                  const analysisResults = selectedTestCase.analysis_results || {};
                  
                  // For data source evidence, the primary key values come from all_rows
                  let extractedPrimaryKeys: Record<string, any> = {};
                  let samplePrimaryKeys: Record<string, any> = {};
                  
                  if (analysisResults.all_rows && analysisResults.all_rows.length > 0) {
                    // This is data source evidence - extract from the first row
                    const firstRow = analysisResults.all_rows[0];
                    const columns = analysisResults.columns || Object.keys(firstRow);
                    
                    // Primary keys are typically: Bank ID, Period ID, Customer ID, Reference Number
                    const primaryKeyList = ['Bank ID', 'Period ID', 'Customer ID', 'Reference Number'];
                    
                    primaryKeyList.forEach(pk => {
                      if (columns.includes(pk) && firstRow[pk] !== undefined) {
                        extractedPrimaryKeys[pk] = firstRow[pk];
                        // For data source, the sample and extracted are the same
                        samplePrimaryKeys[pk] = firstRow[pk];
                      }
                    });
                  } else {
                    // Document evidence - use the original logic
                    extractedPrimaryKeys = analysisResults.primary_key_values || 
                                         analysisResults.extraction_details?.primary_key_values || {};
                    samplePrimaryKeys = analysisResults.sample_primary_key_values || {};
                  }
                  
                  // Also check test case level primary keys
                  const testCasePrimaryKeys = selectedTestCase.primary_key_attributes || 
                                            selectedTestCase.primary_key_values || {};
                  
                  // Merge all available primary keys to get complete list
                  const allPrimaryKeyNames = new Set([
                    ...Object.keys(samplePrimaryKeys),
                    ...Object.keys(extractedPrimaryKeys),
                    ...Object.keys(testCasePrimaryKeys)
                  ]);
                  
                  if (allPrimaryKeyNames.size === 0) {
                    return null;
                  }
                  
                  return (
                    <Grid size={{ xs: 12 }}>
                      <Card variant="outlined" sx={{ mt: 2 }}>
                        <CardContent>
                          <Typography variant="subtitle2" gutterBottom color="text.secondary">
                            Primary Key Values Comparison
                          </Typography>
                          <TableContainer>
                            <Table size="small">
                              <TableHead>
                                <TableRow>
                                  <TableCell sx={{ fontSize: '0.75rem' }}>Primary Key</TableCell>
                                  <TableCell sx={{ fontSize: '0.75rem' }}>Expected</TableCell>
                                  <TableCell sx={{ fontSize: '0.75rem' }}>Extracted</TableCell>
                                  <TableCell align="center" sx={{ fontSize: '0.75rem' }}>Match</TableCell>
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {Array.from(allPrimaryKeyNames).sort().map((key) => {
                                  // Get expected value - check all possible sources
                                  const expectedValue = samplePrimaryKeys[key] || 
                                                      testCasePrimaryKeys[key] || 
                                                      selectedTestCase.primary_key_attributes?.[key] ||
                                                      selectedTestCase.primary_key_values?.[key] ||
                                                      'N/A';
                                  
                                  // Get extracted value
                                  const extractedValue = extractedPrimaryKeys[key] || 'Not extracted';
                                  
                                  
                                  const isMatch = expectedValue !== 'N/A' && 
                                                extractedValue !== 'Not extracted' && 
                                                String(expectedValue) === String(extractedValue);
                                  
                                  return (
                                    <TableRow key={key}>
                                      <TableCell sx={{ fontSize: '0.75rem' }}>{key}</TableCell>
                                      <TableCell sx={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>
                                        {String(expectedValue)}
                                      </TableCell>
                                      <TableCell sx={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>
                                        {String(extractedValue)}
                                      </TableCell>
                                      <TableCell align="center">
                                        {extractedValue === 'Not extracted' ? (
                                          <Typography variant="caption" color="text.secondary">-</Typography>
                                        ) : isMatch ? (
                                          <CheckCircle sx={{ fontSize: 16, color: 'success.main' }} />
                                        ) : (
                                          <Cancel sx={{ fontSize: 16, color: 'error.main' }} />
                                        )}
                                      </TableCell>
                                    </TableRow>
                                  );
                                })}
                              </TableBody>
                            </Table>
                          </TableContainer>
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })()}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setComparisonModalOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Review Modal */}
      <Dialog 
        open={reviewModalOpen} 
        onClose={() => setReviewModalOpen(false)} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>Review Test Execution Result</DialogTitle>
        <DialogContent>
          {selectedTestCase && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                <strong>Test ID:</strong> {selectedTestCase.test_case_id}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Sample ID:</strong> {selectedTestCase.sample_id || selectedTestCase.sample_identifier || '-'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Attribute:</strong> {selectedTestCase.attribute_name}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <FormControl component="fieldset">
                <FormLabel component="legend">Test Result Decision</FormLabel>
                <RadioGroup
                  value={reviewDecision}
                  onChange={(e) => setReviewDecision(e.target.value as 'pass' | 'fail' | 'resend')}
                >
                  <FormControlLabel 
                    value="pass" 
                    control={<Radio />} 
                    label="Pass - Test execution is correct" 
                  />
                  <FormControlLabel 
                    value="fail" 
                    control={<Radio />} 
                    label="Fail - Test execution found issues" 
                  />
                  <FormControlLabel 
                    value="resend" 
                    control={<Radio />} 
                    label="Resend - Request additional information from data owner" 
                  />
                </RadioGroup>
              </FormControl>
              
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Review Notes"
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                margin="normal"
                placeholder="Enter any notes about your decision..."
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewModalOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleReviewSubmit} 
            variant="contained"
            color={reviewDecision === 'pass' ? 'success' : reviewDecision === 'fail' ? 'error' : 'warning'}
          >
            Submit Review
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};