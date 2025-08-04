import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  IconButton,
  Collapse,
  Divider,
  Grid,
} from '@mui/material';
import {
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import apiClient from '../../api/client';

interface DQResult {
  result_id: number;
  rule_id: string;
  rule_name: string;
  rule_description: string;
  rule_type: string;
  criticality: string;
  rule_code: string;
  llm_rationale: string;
  regulatory_reference: string;
  execution_status: string;
  executed_at: string;
  passed_count: number;
  failed_count: number;
  total_count: number;
  pass_rate: number;
  result_summary: any;
  failed_records_sample: any[];
  result_details: string;
  quality_impact: number;
  severity: string;
  execution_time_ms: number;
}

interface DQResultsResponse {
  attribute_id: number | string;
  attribute_name: string;
  is_cde: boolean;
  mdrm: string | null;
  phase_id: number;
  phase_name: string;
  total_rules: number;
  rules_executed: number;
  composite_score: number;
  total_passed: number;
  total_failed: number;
  total_records: number;
  results: DQResult[];
  summary: {
    critical_rules: number;
    high_rules: number;
    medium_rules: number;
    low_rules: number;
    failed_critical: number;
    failed_high: number;
  };
}

interface DQResultsDialogProps {
  open: boolean;
  onClose: () => void;
  attributeId: string;
  attributeName: string;
  cycleId: number;
  reportId: number;
}

export const DQResultsDialog: React.FC<DQResultsDialogProps> = ({
  open,
  onClose,
  attributeId,
  attributeName,
  cycleId,
  reportId,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DQResultsResponse | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (open && attributeId) {
      fetchDQResults();
    }
  }, [open, attributeId]);

  const fetchDQResults = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get(
        `/data-profiling/attributes/${attributeId}/dq-results`,
        {
          params: {
            cycle_id: cycleId,
            report_id: reportId,
          },
        }
      );
      setData(response.data);
    } catch (err: any) {
      console.error('DQ Results Error:', err.response?.data);
      // Handle validation errors from FastAPI
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          setError(err.response.data.detail);
        } else if (Array.isArray(err.response.data.detail)) {
          // Handle array of validation errors
          const errors = err.response.data.detail.map((e: any) => 
            typeof e === 'string' ? e : e.msg || 'Validation error'
          ).join(', ');
          setError(errors);
        } else {
          setError('Failed to fetch DQ results');
        }
      } else {
        setError('Failed to fetch DQ results');
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleRowExpansion = (ruleId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(ruleId)) {
      newExpanded.delete(ruleId);
    } else {
      newExpanded.add(ruleId);
    }
    setExpandedRows(newExpanded);
  };

  const getCriticalityColor = (criticality: string) => {
    switch (criticality.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const getPassRateColor = (passRate: number) => {
    if (passRate >= 95) return 'success.main';
    if (passRate >= 80) return 'warning.main';
    return 'error.main';
  };

  const formatExecutionTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h6">Data Quality Results</Typography>
            <Typography variant="subtitle2" color="text.secondary">
              {attributeName}
            </Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {loading && (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {data && !loading && (
          <>
            {/* Summary Section */}
            <Box mb={3}>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 3 }}>
                  <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color={getPassRateColor(data.composite_score)}>
                      {data.composite_score}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Composite Score
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4">{data.total_rules}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Rules
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main">
                      {data.total_passed}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Records Passed
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="error.main">
                      {data.total_failed}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Records Failed
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>

              {/* Rule Summary */}
              <Box mt={2} display="flex" gap={1} flexWrap="wrap">
                <Chip
                  size="small"
                  label={`Critical: ${data.summary.critical_rules} (${data.summary.failed_critical} failed)`}
                  color="error"
                  variant={data.summary.failed_critical > 0 ? 'filled' : 'outlined'}
                />
                <Chip
                  size="small"
                  label={`High: ${data.summary.high_rules} (${data.summary.failed_high} failed)`}
                  color="warning"
                  variant={data.summary.failed_high > 0 ? 'filled' : 'outlined'}
                />
                <Chip
                  size="small"
                  label={`Medium: ${data.summary.medium_rules}`}
                  color="info"
                  variant="outlined"
                />
                <Chip
                  size="small"
                  label={`Low: ${data.summary.low_rules}`}
                  color="success"
                  variant="outlined"
                />
              </Box>
            </Box>

            <Divider sx={{ mb: 2 }} />

            {/* Rules Table */}
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell width={40}></TableCell>
                    <TableCell>Rule Name</TableCell>
                    <TableCell width={100}>Type</TableCell>
                    <TableCell width={100}>Criticality</TableCell>
                    <TableCell width={120} align="center">
                      Pass Rate
                    </TableCell>
                    <TableCell width={100} align="center">
                      Status
                    </TableCell>
                    <TableCell width={100} align="right">
                      Exec Time
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.results.map((result) => (
                    <React.Fragment key={result.rule_id}>
                      <TableRow
                        hover
                        onClick={() => toggleRowExpansion(result.rule_id)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell>
                          <IconButton size="small">
                            {expandedRows.has(result.rule_id) ? (
                              <ExpandLessIcon />
                            ) : (
                              <ExpandMoreIcon />
                            )}
                          </IconButton>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{result.rule_name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {result.rule_description}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            label={result.rule_type}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            label={result.criticality}
                            color={getCriticalityColor(result.criticality)}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                            {result.pass_rate === 100 ? (
                              <CheckCircleIcon color="success" fontSize="small" />
                            ) : result.pass_rate >= 80 ? (
                              <WarningIcon color="warning" fontSize="small" />
                            ) : (
                              <CancelIcon color="error" fontSize="small" />
                            )}
                            <Typography
                              variant="body2"
                              color={getPassRateColor(result.pass_rate)}
                              fontWeight="bold"
                            >
                              {result.pass_rate}%
                            </Typography>
                          </Box>
                          <Typography variant="caption" color="text.secondary">
                            {result.passed_count}/{result.total_count}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            size="small"
                            label={result.execution_status}
                            color={result.execution_status === 'success' ? 'success' : 'error'}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {formatExecutionTime(result.execution_time_ms)}
                          </Typography>
                        </TableCell>
                      </TableRow>

                      {/* Expanded Details */}
                      <TableRow>
                        <TableCell colSpan={7} sx={{ p: 0 }}>
                          <Collapse
                            in={expandedRows.has(result.rule_id)}
                            timeout="auto"
                            unmountOnExit
                          >
                            <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
                              <Grid container spacing={2}>
                                <Grid size={{ xs: 12, md: 6 }}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Rule Details
                                  </Typography>
                                  {result.llm_rationale && (
                                    <Box mb={1}>
                                      <Typography variant="caption" color="text.secondary">
                                        LLM Rationale:
                                      </Typography>
                                      <Typography variant="body2">
                                        {result.llm_rationale}
                                      </Typography>
                                    </Box>
                                  )}
                                  {result.regulatory_reference && (
                                    <Box mb={1}>
                                      <Typography variant="caption" color="text.secondary">
                                        Regulatory Reference:
                                      </Typography>
                                      <Typography variant="body2">
                                        {result.regulatory_reference}
                                      </Typography>
                                    </Box>
                                  )}
                                </Grid>
                                <Grid size={{ xs: 12, md: 6 }}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Execution Details
                                  </Typography>
                                  <Typography variant="body2">
                                    Executed at:{' '}
                                    {new Date(result.executed_at).toLocaleString()}
                                  </Typography>
                                  {result.failed_count > 0 && (
                                    <Box mt={1}>
                                      <Typography variant="caption" color="text.secondary">
                                        Failed Records: {result.failed_count}
                                      </Typography>
                                      {result.failed_records_sample.length > 0 && (
                                        <Alert severity="warning" sx={{ mt: 1 }}>
                                          <Typography variant="caption">
                                            Sample of failed records available
                                          </Typography>
                                        </Alert>
                                      )}
                                    </Box>
                                  )}
                                </Grid>
                              </Grid>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};