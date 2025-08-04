import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';

interface QueryResult {
  sample_rows: any[];
  column_count: number;
  row_count: number;
  execution_time_ms: number;
  query_valid: boolean;
  error?: string;
  columns?: string[];
}

interface DocumentValidationResult {
  status: 'success' | 'partial' | 'error';
  extracted_values?: {
    primary_key_values: Record<string, any>;
    attribute_value: any;
  };
  confidence_score?: number;
  extraction_details?: string;
  message?: string;
  error?: string;
}

interface EvidenceValidationResultsProps {
  evidenceId: number;
  evidenceType: 'document' | 'data_source';
  testCaseId: string;
  testCaseData?: any;
  queryText?: string;
  dataSourceName?: string;
  phase?: 'request_info' | 'test_execution';
}

export const EvidenceValidationResults: React.FC<EvidenceValidationResultsProps> = ({
  evidenceId,
  evidenceType,
  testCaseId,
  testCaseData,
  queryText,
  dataSourceName,
  phase = 'request_info', // Default to request_info for backward compatibility
}) => {
  const { user } = useAuth();
  const isDataOwner = user?.role === 'Data Owner';
  const [loading, setLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [documentResult, setDocumentResult] = useState<DocumentValidationResult | null>(null);
  
  // Debug: Watch for testCaseData changes
  useEffect(() => {
    console.log('EvidenceValidationResults - testCaseData updated:', {
      testCaseData,
      primaryKeys: testCaseData?.primary_key_attributes,
      attributeName: testCaseData?.attribute_name
    });
  }, [testCaseData]);
  
  // Clear results when evidence changes
  useEffect(() => {
    console.log('Evidence changed, clearing results');
    setQueryResult(null);
    setDocumentResult(null);
  }, [evidenceId, testCaseId]);

  const fetchQueryResult = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get(
        `/request-info/test-cases/${testCaseId}/evidence/${evidenceId}/query-result`
      );
      console.log('Query result response:', response.data);
      console.log('Test case data available:', testCaseData);
      console.log('Primary key attributes:', testCaseData?.primary_key_attributes);
      console.log('Primary key attributes type:', typeof testCaseData?.primary_key_attributes);
      console.log('Primary key attributes keys:', testCaseData?.primary_key_attributes ? Object.keys(testCaseData.primary_key_attributes) : 'undefined');
      setQueryResult(response.data.query_result);
    } catch (err: any) {
      console.error('Failed to fetch query result:', err);
      setQueryResult({
        query_valid: false,
        error: err.response?.data?.detail || err.message || 'Failed to execute query',
        sample_rows: [],
        column_count: 0,
        row_count: 0,
        execution_time_ms: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchDocumentValidation = async () => {
    setLoading(true);
    try {
      // Create FormData for file validation
      const formData = new FormData();
      formData.append('test_case_id', testCaseId);
      
      // Include evidence_id to use the same file as test execution
      formData.append('evidence_id', String(evidenceId));
      
      // Include expected primary keys and attribute
      console.log('testCaseData in fetchDocumentValidation:', testCaseData);
      console.log('primary_key_attributes:', testCaseData?.primary_key_attributes);
      console.log('evidenceId:', evidenceId);
      
      if (testCaseData?.primary_key_attributes) {
        formData.append('expected_primary_keys', JSON.stringify(testCaseData.primary_key_attributes));
        console.log('Sending primary keys:', JSON.stringify(testCaseData.primary_key_attributes));
      } else {
        console.log('No primary keys to send - testCaseData:', testCaseData);
      }
      if (testCaseData?.attribute_name) {
        formData.append('expected_attribute', testCaseData.attribute_name);
      }
      
      // No need to download and re-upload the file when we have evidence_id
      // The backend will read directly from the file path stored in the database
      
      // Always use request-info endpoint for document validation
      // The extract-document-values functionality is shared across phases
      const endpoint = `/request-info/extract-document-values`;
        
      const response = await apiClient.post(
        endpoint,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      
      console.log('Document validation response:', response.data);
      console.log('Extracted values:', response.data.extracted_values);
      console.log('Primary key values:', response.data.extracted_values?.primary_key_values);
      console.log('Setting documentResult to:', response.data);
      setDocumentResult(response.data);
      // Log the state after setting (will be stale, but let's see)
      console.log('documentResult state after set (will be stale):', documentResult);
    } catch (err: any) {
      console.error('Failed to fetch document validation:', err);
      setDocumentResult({
        status: 'error',
        error: err.response?.data?.detail || err.message || 'Failed to validate document',
        message: 'Document validation failed',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = () => {
    if (evidenceType === 'data_source') {
      fetchQueryResult();
    } else {
      fetchDocumentValidation();
    }
  };

  const renderQueryResults = () => {
    if (!queryResult) {
      return (
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Click the button below to execute the query and see results
          </Typography>
          <Button
            variant="contained"
            startIcon={<PlayArrowIcon />}
            onClick={handleValidate}
            color="primary"
            size="small"
          >
            Execute Query
          </Button>
        </Box>
      );
    }

    if (!queryResult.query_valid) {
      const errorMessage = queryResult.error || 'Unknown error';
      const isConnectionError = errorMessage.toLowerCase().includes('connection details');
      
      return (
        <Alert severity="error" sx={{ mt: 2 }}>
          <Typography variant="subtitle2">Query Execution Failed</Typography>
          <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
            {errorMessage}
          </Typography>
          {isConnectionError && (
            <Typography variant="caption" component="div" sx={{ mt: 1, fontStyle: 'italic' }}>
              Note: The data source may have been validated with test/demo connection settings. 
              Please ensure the data source has real database connection details configured.
            </Typography>
          )}
        </Alert>
      );
    }

    return (
      <Box sx={{ mt: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle2">
            Query Results ({queryResult.row_count} rows retrieved in {queryResult.execution_time_ms}ms)
          </Typography>
          <Tooltip title="Re-execute Query">
            <IconButton 
              size="small" 
              onClick={handleValidate}
              color="primary"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        {queryResult.sample_rows && queryResult.sample_rows.length > 0 ? (
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
              Extracted Values from Query
            </Typography>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'grey.100' }}>
                    <TableCell sx={{ fontWeight: 'bold' }}>Attribute Name</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }} align="center">PK?</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Sample Value</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Query Result Value</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {/* Show primary key values first */}
                  {/* Extract primary keys from query result if not provided in testCaseData */}
                  {(() => {
                    // Default primary keys for Request Info phase
                    const primaryKeys = ['Bank ID', 'Period ID', 'Customer ID', 'Reference Number'];
                    const firstRow = queryResult.sample_rows[0];
                    
                    return primaryKeys.map(pkName => {
                      // Check if this column exists in the query result
                      const queryValue = firstRow?.[pkName];
                      if (queryValue === undefined) return null; // Skip if not in query result
                      
                      return (
                        <TableRow key={`pk_${pkName}`}>
                          <TableCell>
                            <Typography variant="body2">{pkName}</Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Chip label="Yes" size="small" color="secondary" />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                              {testCaseData?.primary_key_attributes?.[pkName] || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                              {queryValue !== null && queryValue !== undefined ? String(queryValue) : <em style={{ color: '#999' }}>Not found</em>}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      );
                    }).filter(Boolean);
                  })()}
                  
                  {/* Show target attribute */}
                  {testCaseData?.attribute_name && (() => {
                    // Normalize the attribute name for comparison
                    const attributeNameLower = testCaseData.attribute_name.toLowerCase().trim();
                    
                    // Find matching column - try multiple strategies
                    const matchingColumn = queryResult.sample_rows[0] && Object.keys(queryResult.sample_rows[0]).find(col => {
                      const colLower = col.toLowerCase().trim();
                      
                      // Strategy 1: Exact match (case-insensitive)
                      if (colLower === attributeNameLower) return true;
                      
                      // Strategy 2: Compare without spaces
                      const attributeNoSpaces = attributeNameLower.replace(/\s+/g, '');
                      const colNoSpaces = colLower.replace(/\s+/g, '');
                      if (colNoSpaces === attributeNoSpaces) return true;
                      
                      // Strategy 3: Compare with underscores instead of spaces
                      const attributeUnderscores = attributeNameLower.replace(/\s+/g, '_');
                      const colUnderscores = colLower.replace(/\s+/g, '_');
                      if (colUnderscores === attributeUnderscores) return true;
                      
                      // Strategy 4: Partial match
                      if (colLower.includes(attributeNameLower) || attributeNameLower.includes(colLower)) return true;
                      
                      return false;
                    });
                    
                    const queryValue = matchingColumn ? queryResult.sample_rows[0][matchingColumn] : null;
                    
                    return (
                      <TableRow>
                        <TableCell>
                          <Typography variant="body2">{testCaseData.attribute_name}</Typography>
                          {matchingColumn && matchingColumn !== testCaseData.attribute_name && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              (Column: {matchingColumn})
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell align="center">
                          <Chip label="No" size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          {isDataOwner ? (
                            <Typography variant="body2" color="text.secondary">Not Shown</Typography>
                          ) : (
                            <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                              {testCaseData?.attribute_sample_value || 'N/A'}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 'medium', color: queryValue ? 'success.main' : 'error.main' }}>
                            {queryValue !== null && queryValue !== undefined ? String(queryValue) : <em style={{ color: '#999' }}>Not found</em>}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })()}
                </TableBody>
              </Table>
            </TableContainer>
            {queryResult.sample_rows.length > 1 && (
              <Alert severity="info" sx={{ mt: 1 }}>
                <Typography variant="caption">
                  Showing first row only. Query returned {queryResult.sample_rows.length} total rows.
                </Typography>
              </Alert>
            )}
            {isDataOwner && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="caption">
                  Note: As a Data Owner, sample values for scoped attributes are hidden for data privacy. You can see the values you extracted.
                </Typography>
              </Alert>
            )}
          </Box>
        ) : (
          <Alert severity="info" sx={{ mt: 1 }}>
            No data returned by the query
          </Alert>
        )}
      </Box>
    );
  };

  const renderDocumentResults = () => {
    if (!documentResult) {
      return (
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Click the button below to validate the document and extract values
          </Typography>
          <Button
            variant="contained"
            startIcon={<PlayArrowIcon />}
            onClick={handleValidate}
            color="primary"
            size="small"
          >
            Validate Document
          </Button>
        </Box>
      );
    }

    if (documentResult.status === 'error') {
      return (
        <Alert severity="error" sx={{ mt: 2 }}>
          <Typography variant="subtitle2">Document Validation Failed</Typography>
          <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
            {documentResult.error || documentResult.message || 'Unknown error'}
          </Typography>
        </Alert>
      );
    }

    console.log('Rendering document results with:', {
      documentResult,
      extractedValues: documentResult.extracted_values,
      primaryKeyValues: documentResult.extracted_values?.primary_key_values,
      testCaseData: testCaseData,
      testCasePrimaryKeys: testCaseData?.primary_key_attributes
    });
    
    // Log the actual values being used in the table
    if (documentResult.extracted_values) {
      console.log('Table data:', {
        primaryKeyCount: Object.keys(documentResult.extracted_values.primary_key_values || {}).length,
        primaryKeyValues: documentResult.extracted_values.primary_key_values,
        attributeValue: documentResult.extracted_values.attribute_value,
        status: documentResult.status,
        message: documentResult.message
      });
    }
    
    return (
      <Box sx={{ mt: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle2">
            Document Validation Results
          </Typography>
          <Tooltip title="Re-validate Document">
            <IconButton 
              size="small" 
              onClick={handleValidate}
              color="primary"
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Alert 
          severity={documentResult.status === 'success' ? 'success' : documentResult.status === 'partial' ? 'warning' : 'error'} 
          sx={{ mb: 2 }}
        >
          <Typography variant="body2">
            {documentResult.message || `Validation ${documentResult.status}`}
          </Typography>
          {documentResult.extraction_details && (
            <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
              {documentResult.extraction_details}
            </Typography>
          )}
          {documentResult.confidence_score && (
            <Typography variant="caption" component="div">
              Confidence: {(documentResult.confidence_score * 100).toFixed(0)}%
            </Typography>
          )}
        </Alert>
        

        {documentResult.extracted_values && (
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
              Extracted Values from Document
            </Typography>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'grey.100' }}>
                    <TableCell sx={{ fontWeight: 'bold' }}>Attribute Name</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }} align="center">PK?</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Sample Value</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Extracted Value</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {/* Show all primary key values from test case */}
                  {testCaseData?.primary_key_attributes && Object.entries(testCaseData.primary_key_attributes).map(([key, expectedValue]) => {
                    const extractedValue = documentResult.extracted_values?.primary_key_values?.[key];
                    return (
                      <TableRow key={`pk_${key}`}>
                        <TableCell>
                          <Typography variant="body2">{key}</Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip label="Yes" size="small" color="secondary" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                            {String(expectedValue || 'N/A')}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 'medium', color: extractedValue ? 'inherit' : 'error.main' }}>
                            {extractedValue !== null && extractedValue !== undefined ? String(extractedValue) : <em style={{ color: '#999' }}>Not found</em>}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  
                  {/* Show scoped attribute value */}
                  {testCaseData?.attribute_name && (
                    <TableRow>
                      <TableCell>
                        <Typography variant="body2">{testCaseData.attribute_name}</Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip label="No" size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        {isDataOwner ? (
                          <Typography variant="body2" color="text.secondary">Not Shown</Typography>
                        ) : (
                          <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                            {testCaseData?.attribute_sample_value || 'N/A'}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 'medium', color: documentResult.extracted_values?.attribute_value ? 'success.main' : 'error.main' }}>
                          {documentResult.extracted_values?.attribute_value !== null && documentResult.extracted_values?.attribute_value !== undefined 
                            ? String(documentResult.extracted_values.attribute_value) 
                            : <em style={{ color: '#999' }}>Not found</em>}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            {isDataOwner && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="caption">
                  Note: As a Data Owner, sample values for scoped attributes are hidden for data privacy. You can see the values you extracted.
                </Typography>
              </Alert>
            )}
          </Box>
        )}
      </Box>
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
        <CircularProgress size={24} />
        <Typography variant="body2" sx={{ ml: 1 }}>
          {evidenceType === 'data_source' ? 'Executing query...' : 'Validating document...'}
        </Typography>
      </Box>
    );
  }

  return evidenceType === 'data_source' ? renderQueryResults() : renderDocumentResults();
};

export default EvidenceValidationResults;