/**
 * Execution Results Table Component
 * Shows detailed results of profiling rule execution with drill-down capability
 */
import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Collapse,
  Box,
  Typography,
  Chip,
  Button,
  Card,
  CardContent,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Tooltip,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  KeyboardArrowDown,
  KeyboardArrowRight,
  CheckCircle,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Visibility,
  Assessment,
  BugReport,
  Refresh
} from '@mui/icons-material';
import { dataProfilingApi, ProfilingResult } from '../../api/dataProfiling';

interface ExecutionResultsTableProps {
  cycleId: number;
  reportId: number;
}

interface FailedRecord {
  record_id: string;
  failed_values: Record<string, any>;
  failure_reason: string;
  row_number?: number;
}

interface DetailedResult extends ProfilingResult {
  rule_name?: string;
  rule_type?: string;
  rule_code?: string;
  attribute_name?: string;
  line_item_number?: string;
  is_primary_key?: boolean;
  is_cde?: boolean;
  has_issues?: boolean;
  failed_records?: FailedRecord[];
  primary_key_attributes?: string[];
  total_failed?: number;
  error_message?: string;
  // Additional fields from API that may use different naming
  records_processed?: number;
  records_passed?: number;
  records_failed?: number;
  // Metadata for data source execution
  metadata?: {
    data_source?: string;
    source_type?: string;
    pde_code?: string;
    source_field?: string;
    sql_query?: string;
    execution_mode?: string;
    reason?: string;
    execution_engine?: string;
    dataframe_shape?: string;
    rule_code_executed?: string;
  };
}

const ExecutionResultsTable: React.FC<ExecutionResultsTableProps> = ({
  cycleId,
  reportId
}) => {
  const [results, setResults] = useState<DetailedResult[]>([]);
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [failedRecordsDialog, setFailedRecordsDialog] = useState<{
    open: boolean;
    result: DetailedResult | null;
  }>({ open: false, result: null });

  useEffect(() => {
    loadExecutionResults();
  }, [cycleId, reportId]);

  const loadExecutionResults = async () => {
    try {
      setLoading(true);
      const response = await dataProfilingApi.getResults(cycleId, reportId);
      // Ensure response is an array
      if (Array.isArray(response)) {
        setResults(response);
      } else {
        console.error('Invalid response format, expected array:', response);
        setResults([]);
      }
    } catch (error) {
      console.error('Error loading execution results:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const loadFailedRecords = async (result: DetailedResult) => {
    try {
      // Call API endpoint to get failed records for this result
      const response = await dataProfilingApi.getFailedRecords(result.result_id);
      
      // Transform API response to our FailedRecord format
      const failedRecords: FailedRecord[] = response.failed_records.map((record: any) => ({
        record_id: record.record_id || `ROW_${record.row_number}`,
        row_number: record.row_number,
        failed_values: {
          ...record.primary_key_values,
          [record.tested_attribute.name]: record.tested_attribute.value
        },
        failure_reason: record.failure_reason
      }));
      
      setFailedRecordsDialog({
        open: true,
        result: { 
          ...result, 
          failed_records: failedRecords,
          primary_key_attributes: response.primary_key_attributes,
          total_failed: response.total_failed,
          attribute_name: response.attribute_tested // Map API field to expected field name
        }
      });
    } catch (error) {
      console.error('Error loading failed records:', error);
      // If API fails, show error message
      setFailedRecordsDialog({
        open: true,
        result: {
          ...result,
          failed_records: [],
          error_message: 'Failed to load detailed records. Please try again later.'
        }
      });
    }
  };

  const handleExpandResult = (resultId: number) => {
    const newExpanded = new Set(expandedResults);
    if (expandedResults.has(resultId)) {
      newExpanded.delete(resultId);
    } else {
      newExpanded.add(resultId);
    }
    setExpandedResults(newExpanded);
  };
  
  const handleReExecuteRule = async (ruleId: string | number, ruleName: string) => {
    try {
      // TODO: Call API to re-execute single rule
      console.log(`Re-executing rule ${ruleId}: ${ruleName}`);
      // For now, just reload the results
      await loadExecutionResults();
    } catch (error) {
      console.error('Error re-executing rule:', error);
    }
  };

  const getStatusChip = (result: ProfilingResult) => {
    const passRate = result.pass_rate || 0;
    const hasAnomaly = result.has_anomaly;
    
    if (hasAnomaly) {
      return (
        <Chip
          icon={<WarningIcon />}
          label="Anomaly Detected"
          color="warning"
          size="small"
          sx={{ mr: 1 }}
        />
      );
    }
    
    if (passRate === 100) {
      return (
        <Chip
          icon={<CheckCircle />}
          label="All Passed"
          color="success"
          size="small"
          sx={{ mr: 1 }}
        />
      );
    } else if (passRate >= 95) {
      return (
        <Chip
          icon={<WarningIcon />}
          label="Minor Issues"
          color="warning"
          size="small"
          sx={{ mr: 1 }}
        />
      );
    } else {
      return (
        <Chip
          icon={<ErrorIcon />}
          label="Major Issues"
          color="error"
          size="small"
          sx={{ mr: 1 }}
        />
      );
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'error';
      case 'high': return 'warning'; 
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getDimensionChip = (ruleName: string, ruleType?: string) => {
    // First try to use rule type if available
    if (ruleType) {
      const typeColorMap: Record<string, string> = {
        'completeness': '#1976d2',
        'validity': '#388e3c',
        'consistency': '#7b1fa2',
        'uniqueness': '#f57c00',
        'accuracy': '#d32f2f'
      };
      
      const color = typeColorMap[ruleType.toLowerCase()] || '#616161';
      
      return (
        <Chip 
          size="small" 
          label={ruleType.charAt(0).toUpperCase() + ruleType.slice(1)}
          sx={{ 
            backgroundColor: color, 
            color: 'white',
            fontWeight: 'bold',
            fontSize: '0.75rem'
          }}
        />
      );
    }
    
    // Fallback to rule name analysis
    const name = ruleName.toLowerCase();
    
    let dimension = 'validity'; // Default to validity instead of other
    let color = '#388e3c';
    
    // Completeness: Check for mandatory fields and null values  
    if (name.includes('completeness') || name.includes('mandatory') || name.includes('null') || name.includes('missing')) {
      dimension = 'completeness';
      color = '#1976d2';
    }
    // Validity: Check for valid values and acceptable formats
    else if (name.includes('valid') || name.includes('format') || name.includes('pattern') || name.includes('range')) {
      dimension = 'validity';
      color = '#388e3c';
    }
    // Consistency: Check for standardization and formatting consistency
    else if (name.includes('standardization') || name.includes('consistent') || name.includes('referential')) {
      dimension = 'consistency';
      color = '#7b1fa2';
    }
    // Uniqueness: Check for duplicates and unique constraints
    else if (name.includes('unique') || name.includes('duplicate') || name.includes('distinct')) {
      dimension = 'uniqueness';
      color = '#f57c00';
    }
    // Accuracy: Check for precision and correctness
    else if (name.includes('accuracy') || name.includes('precision') || name.includes('correct')) {
      dimension = 'accuracy';
      color = '#d32f2f';
    }
    
    return (
      <Chip 
        size="small" 
        label={dimension.charAt(0).toUpperCase() + dimension.slice(1)}
        sx={{ 
          backgroundColor: color, 
          color: 'white',
          fontWeight: 'bold',
          fontSize: '0.75rem'
        }}
      />
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  if (!Array.isArray(results) || results.length === 0) {
    return (
      <Alert severity="info">
        No execution results available. Execute profiling rules to see results here.
      </Alert>
    );
  }

  // Calculate statistics from results
  const totalRules = results.length;
  const successfulRules = results.filter(r => r.execution_status === 'success').length;
  const failedRules = results.filter(r => r.execution_status === 'failed').length;
  const rulesWithAnomalies = results.filter(r => r.has_anomaly).length;
  const totalRecordsProcessed = results.reduce((sum, r) => sum + (r.records_processed || r.total_count || 0), 0);
  const totalRecordsPassed = results.reduce((sum, r) => sum + (r.records_passed || r.passed_count || 0), 0);
  const totalRecordsFailed = results.reduce((sum, r) => sum + (r.records_failed || r.failed_count || 0), 0);
  const overallPassRate = totalRecordsProcessed > 0 ? (totalRecordsPassed / totalRecordsProcessed) * 100 : 0;
  const uniqueAttributes = new Set(results.map(r => r.attribute_name)).size;

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Profiling Rule Execution Results
      </Typography>

      {/* Detailed Statistics Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📊 Detailed Statistics
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Box sx={{ flex: '1 1 300px', p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Rule Execution Summary
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">✅ Successful Rules:</Typography>
                  <Chip label={successfulRules} color="success" size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">❌ Failed Rules:</Typography>
                  <Chip label={failedRules} color="error" size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">⚠️ Rules with Anomalies:</Typography>
                  <Chip label={rulesWithAnomalies} color="warning" size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">📝 Total Rules Executed:</Typography>
                  <Chip label={totalRules} color="default" size="small" />
                </Box>
              </Box>
            </Box>

            <Box sx={{ flex: '1 1 300px', p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Data Quality Metrics
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">📋 Unique Attributes:</Typography>
                  <Chip label={uniqueAttributes} color="info" size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">📊 Records Processed:</Typography>
                  <Chip label={totalRecordsProcessed.toLocaleString()} color="primary" size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">✅ Records Passed:</Typography>
                  <Chip label={totalRecordsPassed.toLocaleString()} color="success" size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">📈 Overall Pass Rate:</Typography>
                  <Chip 
                    label={`${overallPassRate.toFixed(1)}%`} 
                    color={
                      overallPassRate >= 95 ? 'success' : 
                      overallPassRate >= 80 ? 'warning' : 'error'
                    } 
                    size="small" 
                  />
                </Box>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>

      <Divider sx={{ mb: 2 }} />
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell width={50}></TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 80 }}>Line Item #</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 250 }}>Attribute</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>DQ Dimension</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 200 }}>Rule</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 300 }}>Rule Logic</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Total Records</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 80 }}>Passed</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 80 }}>Failed</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>DQ Score (%)</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Status</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 150 }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {results.map((result) => (
              <React.Fragment key={result.result_id}>
                {/* Main result row */}
                <TableRow hover>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => handleExpandResult(result.result_id)}
                    >
                      {expandedResults.has(result.result_id) ? (
                        <KeyboardArrowDown />
                      ) : (
                        <KeyboardArrowRight />
                      )}
                    </IconButton>
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {result.line_item_number || '-'}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {result.attribute_name || `Attribute ${result.attribute_id}`}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                        {result.is_primary_key && (
                          <Chip size="small" label="PK" color="primary" sx={{ fontSize: '0.7rem' }} />
                        )}
                        {result.is_cde && (
                          <Chip size="small" label="CDE" color="warning" sx={{ fontSize: '0.7rem' }} />
                        )}
                        {result.has_issues && (
                          <Chip size="small" label="Issues" color="error" sx={{ fontSize: '0.7rem' }} />
                        )}
                      </Box>
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    {getDimensionChip(result.rule_name || '', result.rule_type)}
                  </TableCell>
                  
                  <TableCell>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {result.rule_name || `Rule ${result.rule_id}`}
                      </Typography>
                      <Chip 
                        size="small" 
                        label={result.severity}
                        color={getSeverityColor(result.severity)}
                        sx={{ mt: 0.5 }}
                      />
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Tooltip 
                      title={
                        <Box>
                          <Typography variant="caption" component="div">
                            {result.rule_code || 'No rule logic defined'}
                          </Typography>
                          {(result.metadata?.sql_query || result.metadata?.rule_code_executed) && (
                            <>
                              <Divider sx={{ my: 1, borderColor: 'rgba(255,255,255,0.2)' }} />
                              <Typography variant="caption" component="div" sx={{ mt: 1 }}>
                                <strong>
                                  {result.metadata?.execution_engine === 'pandas' ? 'Executed Code:' : 'Generated SQL:'}
                                </strong>
                              </Typography>
                              <Typography variant="caption" component="div" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                                {result.metadata?.rule_code_executed || result.metadata?.sql_query}
                              </Typography>
                            </>
                          )}
                          {result.metadata?.data_source && (
                            <>
                              <Divider sx={{ my: 1, borderColor: 'rgba(255,255,255,0.2)' }} />
                              <Typography variant="caption" component="div">
                                <strong>Data Source:</strong> {result.metadata.data_source} ({result.metadata.source_type})
                              </Typography>
                              <Typography variant="caption" component="div">
                                <strong>PDE:</strong> {result.metadata.pde_code} - {result.metadata.source_field}
                              </Typography>
                            </>
                          )}
                        </Box>
                      }
                      placement="left"
                      arrow
                    >
                      <Box>
                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            color: 'text.secondary',
                            maxWidth: 300,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {result.rule_code || 'N/A'}
                        </Typography>
                        {result.metadata?.data_source && (
                          <Typography variant="caption" sx={{ color: 'success.main', display: 'block' }}>
                            ✓ Data Source Connected {result.metadata?.execution_engine && `(${result.metadata.execution_engine})`}
                          </Typography>
                        )}
                        {result.metadata?.execution_mode === 'mock' && (
                          <Typography variant="caption" sx={{ color: 'warning.main', display: 'block' }}>
                            ⚠ Mock Execution
                          </Typography>
                        )}
                        {result.metadata?.dataframe_shape && (
                          <Typography variant="caption" sx={{ color: 'info.main', display: 'block' }}>
                            📊 {result.metadata.dataframe_shape}
                          </Typography>
                        )}
                      </Box>
                    </Tooltip>
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {(result.records_processed || result.total_count || 0).toLocaleString()}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <CheckCircle color="success" fontSize="small" sx={{ mr: 0.5 }} />
                      <Typography variant="body2" color="success.main" fontWeight="medium">
                        {(result.records_passed || result.passed_count || 0).toLocaleString()}
                      </Typography>
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      {(result.records_failed || result.failed_count || 0) > 0 && (
                        <>
                          <ErrorIcon color="error" fontSize="small" sx={{ mr: 0.5 }} />
                          <Typography variant="body2" color="error.main" fontWeight="medium">
                            {(result.records_failed || result.failed_count || 0).toLocaleString()}
                          </Typography>
                        </>
                      )}
                      {(result.records_failed || result.failed_count || 0) === 0 && (
                        <Typography variant="body2" color="text.secondary">
                          0
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {(result.pass_rate || 0).toFixed(1)}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={result.pass_rate || 0}
                        color={(result.pass_rate || 0) >= 95 ? 'success' : (result.pass_rate || 0) >= 80 ? 'warning' : 'error'}
                        sx={{ mt: 0.5, height: 4 }}
                      />
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    {getStatusChip(result)}
                  </TableCell>
                  
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <Tooltip title="Re-execute rule">
                        <IconButton
                          size="small"
                          onClick={() => handleReExecuteRule(result.rule_id, result.rule_name || '')}
                          color="primary"
                        >
                          <Refresh />
                        </IconButton>
                      </Tooltip>
                      {(result.records_failed || result.failed_count || 0) > 0 && (
                        <Tooltip title="View failed records">
                          <IconButton
                            size="small"
                            onClick={() => loadFailedRecords(result)}
                          >
                            <BugReport />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="View details">
                        <IconButton
                          size="small"
                          onClick={() => handleExpandResult(result.result_id)}
                        >
                          <Visibility />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
                
                {/* Expanded details section */}
                <TableRow>
                  <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={12}>
                    <Collapse in={expandedResults.has(result.result_id)} timeout="auto" unmountOnExit>
                      <Box margin={2}>
                        <Typography variant="h6" gutterBottom>
                          Execution Details
                        </Typography>
                        
                        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                          <Box sx={{ flex: '1 1 300px' }}>
                            <Card>
                              <CardContent>
                                <Typography variant="subtitle2" gutterBottom>
                                  Execution Summary
                                </Typography>
                                <Typography variant="body2" sx={{ mb: 1 }}>
                                  <strong>Executed:</strong> {new Date(result.executed_at).toLocaleString()}
                                </Typography>
                                <Typography variant="body2" sx={{ mb: 1 }}>
                                  <strong>Status:</strong> {result.execution_status}
                                </Typography>
                                <Typography variant="body2" sx={{ mb: 1 }}>
                                  <strong>Total Records Processed:</strong> {(result.records_processed || result.total_count || 0).toLocaleString()}
                                </Typography>
                                <Typography variant="body2" sx={{ mb: 1 }}>
                                  <strong>Success Rate:</strong> {(result.pass_rate || 0).toFixed(2)}%
                                </Typography>
                                {result.rule_code && (
                                  <Box sx={{ mt: 2 }}>
                                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                                      <strong>Rule Logic:</strong>
                                    </Typography>
                                    <Box sx={{ 
                                      bgcolor: 'grey.100', 
                                      p: 1, 
                                      borderRadius: 1,
                                      maxHeight: 200,
                                      overflow: 'auto'
                                    }}>
                                      <Typography 
                                        variant="body2" 
                                        sx={{ 
                                          fontFamily: 'monospace',
                                          fontSize: '0.85rem',
                                          whiteSpace: 'pre-wrap'
                                        }}
                                      >
                                        {result.rule_code}
                                      </Typography>
                                    </Box>
                                  </Box>
                                )}
                                {result.metadata && (
                                  <Box sx={{ mt: 2 }}>
                                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                                      <strong>Data Source Information:</strong>
                                    </Typography>
                                    {result.metadata.data_source && (
                                      <>
                                        <Typography variant="body2" sx={{ mb: 0.5 }}>
                                          <strong>Source:</strong> {result.metadata.data_source} ({result.metadata.source_type})
                                        </Typography>
                                        <Typography variant="body2" sx={{ mb: 0.5 }}>
                                          <strong>PDE Code:</strong> {result.metadata.pde_code}
                                        </Typography>
                                        <Typography variant="body2" sx={{ mb: 0.5 }}>
                                          <strong>Source Field:</strong> {result.metadata.source_field}
                                        </Typography>
                                      </>
                                    )}
                                    {result.metadata.execution_mode === 'mock' && (
                                      <Alert severity="info" sx={{ mt: 1 }}>
                                        <Typography variant="body2">
                                          <strong>Mock Execution:</strong> {result.metadata.reason || 'No data source configured'}
                                        </Typography>
                                      </Alert>
                                    )}
                                    {result.metadata.execution_engine && (
                                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                                        <strong>Execution Engine:</strong> {result.metadata.execution_engine.toUpperCase()}
                                      </Typography>
                                    )}
                                    {result.metadata.dataframe_shape && (
                                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                                        <strong>DataFrame Shape:</strong> {result.metadata.dataframe_shape}
                                      </Typography>
                                    )}
                                    {(result.metadata.sql_query || result.metadata.rule_code_executed) && (
                                      <Box sx={{ mt: 1 }}>
                                        <Typography variant="body2" sx={{ mb: 0.5 }}>
                                          <strong>
                                            {result.metadata.execution_engine === 'pandas' ? 'Executed Pandas Code:' : 'Generated SQL:'}
                                          </strong>
                                        </Typography>
                                        <Box sx={{ 
                                          bgcolor: 'grey.900', 
                                          color: 'grey.100',
                                          p: 1, 
                                          borderRadius: 1,
                                          maxHeight: 300,
                                          overflow: 'auto'
                                        }}>
                                          <Typography 
                                            variant="body2" 
                                            sx={{ 
                                              fontFamily: 'monospace',
                                              fontSize: '0.85rem',
                                              whiteSpace: 'pre-wrap'
                                            }}
                                          >
                                            {result.metadata.rule_code_executed || result.metadata.sql_query}
                                          </Typography>
                                        </Box>
                                      </Box>
                                    )}
                                  </Box>
                                )}
                              </CardContent>
                            </Card>
                          </Box>
                          
                          <Box sx={{ flex: '1 1 300px' }}>
                            <Card>
                              <CardContent>
                                <Typography variant="subtitle2" gutterBottom>
                                  Quality Assessment
                                </Typography>
                                {result.has_anomaly && (
                                  <Alert severity="warning" sx={{ mb: 2 }}>
                                    <Typography variant="body2">
                                      <strong>Anomaly Detected:</strong> {result.anomaly_description}
                                    </Typography>
                                  </Alert>
                                )}
                                {!result.has_anomaly && (result.pass_rate || 0) === 100 && (
                                  <Alert severity="success" sx={{ mb: 2 }}>
                                    <Typography variant="body2">
                                      All records passed validation. No anomalies detected.
                                    </Typography>
                                  </Alert>
                                )}
                                {!result.has_anomaly && (result.pass_rate || 0) < 100 && (
                                  <Alert severity="info" sx={{ mb: 2 }}>
                                    <Typography variant="body2">
                                      {(result.records_failed || result.failed_count || 0)} records failed validation but no anomalies detected.
                                    </Typography>
                                  </Alert>
                                )}
                              </CardContent>
                            </Card>
                          </Box>
                        </Box>
                        
                        {(result.records_failed || result.failed_count || 0) > 0 && (
                          <Box sx={{ mt: 2 }}>
                            <Button
                              variant="outlined"
                              color="error"
                              startIcon={<BugReport />}
                              onClick={() => loadFailedRecords(result)}
                            >
                              View {(result.records_failed || result.failed_count || 0)} Failed Records
                            </Button>
                          </Box>
                        )}
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Failed Records Dialog */}
      <Dialog 
        open={failedRecordsDialog.open} 
        onClose={() => setFailedRecordsDialog({ open: false, result: null })}
        maxWidth="xl"
        fullWidth
      >
        <DialogTitle>
          <Box>
            <Typography variant="h6">
              Failed Records Details - {failedRecordsDialog.result?.rule_name}
            </Typography>
            <Box display="flex" gap={2} mt={1}>
              <Typography variant="body2" color="text.secondary">
                Rule Type: <Chip size="small" label={failedRecordsDialog.result?.rule_type} />
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Attribute Tested: <Chip size="small" label={failedRecordsDialog.result?.attribute_name} color="primary" />
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Failed: <Chip size="small" label={failedRecordsDialog.result?.total_failed || failedRecordsDialog.result?.failed_records?.length || 0} color="error" />
              </Typography>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          {failedRecordsDialog.result?.error_message ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {failedRecordsDialog.result.error_message}
            </Alert>
          ) : failedRecordsDialog.result?.failed_records && failedRecordsDialog.result.failed_records.length > 0 ? (
            <>
              {failedRecordsDialog.result.primary_key_attributes && failedRecordsDialog.result.primary_key_attributes.length > 0 && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Primary Key Attributes:</strong> {failedRecordsDialog.result.primary_key_attributes.join(', ')}
                  </Typography>
                </Alert>
              )}
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ backgroundColor: 'grey.100' }}>
                      <TableCell><strong>Row #</strong></TableCell>
                      {failedRecordsDialog.result.primary_key_attributes?.map(attr => (
                        <TableCell key={attr}>
                          <strong>{attr}</strong>
                          <Chip size="small" label="PK" color="primary" sx={{ ml: 0.5, fontSize: '0.7rem' }} />
                        </TableCell>
                      ))}
                      <TableCell>
                        <strong>{failedRecordsDialog.result.attribute_name}</strong>
                        <Chip size="small" label="Tested" color="warning" sx={{ ml: 0.5, fontSize: '0.7rem' }} />
                      </TableCell>
                      <TableCell><strong>Failure Reason</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {failedRecordsDialog.result.failed_records.map((record, index) => {
                      // Extract primary key values from failed_values
                      const pkValues: Record<string, any> = {};
                      const testedValue = record.failed_values[failedRecordsDialog.result?.attribute_name || ''];
                      
                      // Separate PK values from the tested attribute value
                      failedRecordsDialog.result?.primary_key_attributes?.forEach(pkAttr => {
                        if (record.failed_values[pkAttr] !== undefined) {
                          pkValues[pkAttr] = record.failed_values[pkAttr];
                        }
                      });
                      
                      return (
                        <TableRow key={index} hover>
                          <TableCell>{record.row_number}</TableCell>
                          {failedRecordsDialog.result?.primary_key_attributes?.map(attr => (
                            <TableCell key={attr}>
                              <Typography variant="body2" fontFamily="monospace">
                                {pkValues[attr] !== undefined ? (
                                  pkValues[attr] === null ? 
                                    <Chip size="small" label="NULL" variant="outlined" /> : 
                                    String(pkValues[attr])
                                ) : '-'}
                              </Typography>
                            </TableCell>
                          ))}
                          <TableCell>
                            <Box>
                              {testedValue === null ? (
                                <Chip size="small" label="NULL" color="error" />
                              ) : testedValue === undefined ? (
                                <Chip size="small" label="UNDEFINED" color="error" />
                              ) : (
                                <Typography variant="body2" fontFamily="monospace" color="error">
                                  {String(testedValue)}
                                </Typography>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="error">
                              {record.failure_reason}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
              {failedRecordsDialog.result.total_failed && failedRecordsDialog.result.total_failed > failedRecordsDialog.result.failed_records.length && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Showing {failedRecordsDialog.result.failed_records.length} of {failedRecordsDialog.result.total_failed} failed records
                </Alert>
              )}
            </>
          ) : (
            <Alert severity="info">
              No failed records to display
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFailedRecordsDialog({ open: false, result: null })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExecutionResultsTable;