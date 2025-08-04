import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Tabs,
  Tab,
  TextField,
  Input,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tooltip,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Storage as StorageIcon,
  PlayArrow as PlayArrowIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Code as CodeIcon,
  AttachFile as AttachFileIcon,
  Visibility as VisibilityIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../api/client';
import { toast } from 'react-hot-toast';
import AddDataSourceDialog from './AddDataSourceDialog';

interface TestCase {
  test_case_id: string;
  attribute_name: string;
  sample_identifier: string;
  primary_key_attributes?: Record<string, any>;
  cycle_id: number;
  report_id: number;
}

interface DataSource {
  data_source_id: string;
  source_name: string;
  connection_type: string;
  description?: string;
  is_active: boolean;
}

interface QueryValidation {
  validation_status: string;
  row_count?: number;
  sample_data?: any[];
  execution_time_ms?: number;
  validation_message?: string;
  validation_errors?: string[];
  validation_warnings?: string[];
  has_primary_keys?: boolean;
  has_target_attribute?: boolean;
  missing_columns?: string[];
}

interface DocumentValidation {
  status: 'pending' | 'success' | 'error';
  extracted_values?: {
    primary_key_values: Record<string, any>;
    attribute_value: any;
  };
  confidence_score?: number;
  message?: string;
  extraction_details?: string;
}

interface EvidenceUploadDialogProps {
  open: boolean;
  onClose: () => void;
  testCase: TestCase | null;
  onSuccess: () => void;
}

export const EvidenceUploadDialog: React.FC<EvidenceUploadDialogProps> = ({
  open,
  onClose,
  testCase,
  onSuccess,
}) => {
  const [evidenceType, setEvidenceType] = useState<'document' | 'data_source'>('document');
  const [activeStep, setActiveStep] = useState(0);
  
  // Document upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submissionNotes, setSubmissionNotes] = useState('');
  const [uploading, setUploading] = useState(false);
  const [documentValidation, setDocumentValidation] = useState<any | null>(null);
  const [extracting, setExtracting] = useState(false);
  
  // Data source state
  const [selectedDataSource, setSelectedDataSource] = useState('');
  const [queryText, setQueryText] = useState('');
  const [queryValidation, setQueryValidation] = useState<QueryValidation | null>(null);
  const [validating, setValidating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [addDataSourceOpen, setAddDataSourceOpen] = useState(false);
  
  const queryClient = useQueryClient();

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (!open) {
      setEvidenceType('document');
      setActiveStep(0);
      setSelectedFile(null);
      setSubmissionNotes('');
      setSelectedDataSource('');
      setQueryText('');
      setQueryValidation(null);
      setDocumentValidation(null);
    }
  }, [open]);

  // Load available data sources
  const { data: dataSources, isLoading: sourcesLoading } = useQuery({
    queryKey: ['data-sources', testCase?.cycle_id, testCase?.report_id],
    queryFn: async () => {
      if (!testCase) return [];
      const response = await apiClient.get(`/request-info/data-sources?cycle_id=${testCase.cycle_id}&report_id=${testCase.report_id}`);
      return response.data.data_sources || [];
    },
    enabled: !!testCase, // Always load data sources when dialog opens
  });

  // Reset selected data source if it's not in the list
  React.useEffect(() => {
    if (dataSources && selectedDataSource) {
      const validSource = dataSources.find((ds: DataSource) => ds.data_source_id === selectedDataSource);
      if (!validSource) {
        console.log('Selected data source not found in list, resetting');
        setSelectedDataSource('');
      }
    }
  }, [dataSources, selectedDataSource]);

  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setDocumentValidation(null); // Reset validation when new file is selected
    }
  };

  // Handle document value extraction for validation
  const handleExtractValues = async () => {
    if (!selectedFile || !testCase) {
      toast.error('Please select a file to validate');
      return;
    }

    // Debug log to check testCase structure
    console.log('Test case data:', testCase);
    console.log('Test case ID:', testCase.test_case_id);

    setExtracting(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('test_case_id', testCase.test_case_id);
      
      // Include expected primary keys and attribute
      if (testCase.primary_key_attributes) {
        // Send the full primary key dictionary, not just the keys
        formData.append('expected_primary_keys', JSON.stringify(testCase.primary_key_attributes));
      }
      formData.append('expected_attribute', testCase.attribute_name);

      const response = await apiClient.post('/request-info/extract-document-values', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const extractionResult = response.data;
      
      // Check if extraction was successful
      if (extractionResult.status === 'success' && extractionResult.extracted_values) {
        // Just show the extracted values without validation
        const extractedPKs = extractionResult.extracted_values.primary_key_values || {};
        
        setDocumentValidation({
          status: 'success',
          extracted_values: {
            primary_key_values: extractedPKs,
            attribute_value: extractionResult.extracted_values.attribute_value
          },
          confidence_score: extractionResult.confidence_score,
          message: 'Values extracted successfully',
          extraction_details: extractionResult.extraction_details
        });
        
        // Only require attribute value to proceed
        if (extractionResult.extracted_values.attribute_value) {
          toast.success('Document values extracted successfully');
          setActiveStep(2);
        } else {
          toast('Attribute value not found in document', { icon: '⚠️' });
        }
      } else {
        setDocumentValidation({
          status: 'error',
          message: extractionResult.message || 'Failed to extract values from document',
          extraction_details: extractionResult.extraction_details
        });
        toast.error('Failed to extract values from document');
      }
    } catch (err: any) {
      console.error('Extraction error:', err);
      setDocumentValidation({
        status: 'error',
        message: err.response?.data?.detail || 'Failed to extract document values'
      });
      toast.error(err.response?.data?.detail || 'Failed to extract document values');
    } finally {
      setExtracting(false);
    }
  };

  // Handle document upload
  const handleDocumentUpload = async () => {
    if (!selectedFile || !testCase) {
      toast.error('Please select a file to upload');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('document_type', 'Source Document');
      if (submissionNotes) {
        formData.append('submission_notes', submissionNotes);
      }
      
      // Include validated values if available
      if (documentValidation?.extracted_values) {
        formData.append('validated_values', JSON.stringify(documentValidation.extracted_values));
      }

      await apiClient.post(`/request-info/test-cases/${testCase.test_case_id}/submit`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success('Document uploaded successfully');
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error('Upload error:', err);
      toast.error(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  // Generate sample query based on primary keys
  const generateSampleQuery = () => {
    if (!testCase?.primary_key_attributes || Object.keys(testCase.primary_key_attributes).length === 0) {
      return '';
    }
    
    const conditions = Object.entries(testCase.primary_key_attributes)
      .map(([key, value]) => {
        if (typeof value === 'string') {
          return `${key} = '${value}'`;
        }
        return `${key} = ${value}`;
      })
      .join(' AND ');
    
    return `-- Query for ${testCase.attribute_name}\nSELECT * FROM your_table_name\nWHERE ${conditions}\n-- Add additional conditions as needed`;
  };

  // Handle query validation
  const handleValidateQuery = async () => {
    if (!selectedDataSource || !queryText || !testCase) {
      toast.error('Please select a data source and enter a query');
      return;
    }

    // Log for debugging
    console.log('Validating query with data source ID:', selectedDataSource);
    console.log('Available data sources:', dataSources);

    setValidating(true);
    try {
      const response = await apiClient.post('/request-info/query-validation', {
        test_case_id: testCase.test_case_id,
        data_source_id: selectedDataSource,
        query_text: queryText,
        execute_query: true,  // Add flag to execute query and get results
      });
      
      // Map API response to component's QueryValidation interface
      setQueryValidation({
        validation_status: response.data.validation_status,
        row_count: response.data.row_count,
        sample_data: response.data.sample_rows || response.data.query_results?.sample_rows,
        execution_time_ms: response.data.execution_time_ms,
        validation_message: response.data.error_message,
        validation_warnings: response.data.validation_warnings,
        has_primary_keys: response.data.has_primary_keys,
        has_target_attribute: response.data.has_target_attribute,
        missing_columns: response.data.missing_columns,
      });
      
      if (response.data.validation_status === 'success') {
        toast.success(`Query validated successfully! Found ${response.data.row_count} records`);
        // Only auto-advance if there are no warnings
        if (!response.data.validation_warnings || response.data.validation_warnings.length === 0) {
          setActiveStep(2);
        }
      } else {
        toast.error('Query validation failed');
      }
    } catch (err: any) {
      console.error('Validation error:', err);
      toast.error(err.response?.data?.detail || 'Failed to validate query');
    } finally {
      setValidating(false);
    }
  };

  // Handle data source evidence submission
  const handleDataSourceSubmit = async () => {
    if (!queryValidation || queryValidation.validation_status !== 'success' || !testCase) {
      toast.error('Please validate your query before submitting');
      return;
    }

    setSubmitting(true);
    try {
      await apiClient.post('/request-info/query-evidence', {
        test_case_id: testCase.test_case_id,
        data_source_id: selectedDataSource,
        query_text: queryText,
        submission_notes: submissionNotes,
      });

      toast.success('Data source evidence submitted successfully');
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error('Submit error:', err);
      toast.error(err.response?.data?.detail || 'Failed to submit data source evidence');
    } finally {
      setSubmitting(false);
    }
  };

  const getStepContent = (step: number) => {
    if (evidenceType === 'document') {
      switch (step) {
        case 0:
          return (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Upload a document as evidence for this test case
              </Typography>
              <Input
                type="file"
                onChange={handleFileSelect}
                sx={{ width: '100%', mt: 2 }}
                inputProps={{
                  accept: '.pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.csv'
                }}
              />
              {selectedFile && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
                </Alert>
              )}
              
              {/* Navigation button to proceed to validation */}
              {selectedFile && (
                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    variant="contained"
                    endIcon={<PlayArrowIcon />}
                    onClick={() => setActiveStep(1)}
                  >
                    Next: Validate Document
                  </Button>
                </Box>
              )}
            </Box>
          );
        case 1:
          return (
            <Box>
              {!documentValidation ? (
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Extract values from the document to validate content
                  </Typography>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={extracting ? <CircularProgress size={16} /> : <PlayArrowIcon />}
                    onClick={handleExtractValues}
                    disabled={extracting || !selectedFile}
                    sx={{ mt: 2 }}
                  >
                    {extracting ? 'Extracting Values...' : 'Extract & Validate'}
                  </Button>
                </Box>
              ) : (
                <Box>
                  {documentValidation.status === 'success' ? (
                    <Alert severity="success" sx={{ mb: 2 }}>
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Values Extracted Successfully
                        </Typography>
                        {documentValidation.extracted_values && (
                          <Box sx={{ mt: 1 }}>
                            <TableContainer component={Paper} sx={{ mt: 1 }}>
                              <Table size="small">
                                <TableHead>
                                  <TableRow>
                                    <TableCell>Attribute Name</TableCell>
                                    <TableCell align="center">PK?</TableCell>
                                    <TableCell>Sample Value</TableCell>
                                    <TableCell>Extracted Value</TableCell>
                                  </TableRow>
                                </TableHead>
                                <TableBody>
                                  {/* Primary Key Rows */}
                                  {Object.entries(documentValidation.extracted_values.primary_key_values || {}).map(([key, extractedValue]) => (
                                    <TableRow key={key}>
                                      <TableCell>{key}</TableCell>
                                      <TableCell align="center">
                                        <Chip label="Yes" size="small" color="secondary" />
                                      </TableCell>
                                      <TableCell>
                                        {testCase?.primary_key_attributes?.[key] || 'N/A'}
                                      </TableCell>
                                      <TableCell>
                                        <strong>{extractedValue ? String(extractedValue) : 'Not found'}</strong>
                                      </TableCell>
                                    </TableRow>
                                  ))}
                                  
                                  {/* Non-PK Attribute Row */}
                                  {testCase?.attribute_name && (
                                    <TableRow>
                                      <TableCell>{testCase.attribute_name}</TableCell>
                                      <TableCell align="center">
                                        <Chip label="No" size="small" variant="outlined" />
                                      </TableCell>
                                      <TableCell>
                                        <Typography variant="body2" color="text.secondary">Not Shown</Typography>
                                      </TableCell>
                                      <TableCell>
                                        <strong>{documentValidation.extracted_values.attribute_value ? String(documentValidation.extracted_values.attribute_value) : 'Not found'}</strong>
                                      </TableCell>
                                    </TableRow>
                                  )}
                                </TableBody>
                              </Table>
                            </TableContainer>
                            
                            {documentValidation.confidence_score && (
                              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                                Confidence: {(documentValidation.confidence_score * 100).toFixed(0)}%
                              </Typography>
                            )}
                            
                            <Alert severity="info" sx={{ mt: 2 }}>
                              <Typography variant="body2">
                                Please verify that the extracted values match your expected data before submitting.
                              </Typography>
                            </Alert>
                          </Box>
                        )}
                      </Box>
                    </Alert>
                  ) : (
                    <Alert severity="error" sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">Extraction Failed</Typography>
                      <Typography variant="body2">{documentValidation.message}</Typography>
                    </Alert>
                  )}
                  
                  {documentValidation.extraction_details && (
                    <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Extraction Details:
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 0.5, fontFamily: 'monospace', fontSize: '0.85rem' }}>
                        {documentValidation.extraction_details}
                      </Typography>
                    </Box>
                  )}
                  
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                      variant="outlined"
                      onClick={() => {
                        setDocumentValidation(null);
                        setSelectedFile(null);
                        setActiveStep(0);
                      }}
                    >
                      Try Different Document
                    </Button>
                    {documentValidation.status === 'success' && (
                      <Button
                        variant="contained"
                        onClick={() => setActiveStep(2)}
                        color="primary"
                      >
                        Continue
                      </Button>
                    )}
                  </Box>
                </Box>
              )}
            </Box>
          );
        case 2:
          return (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                Document validated and ready for submission
              </Alert>
              
              {documentValidation?.extracted_values && (
                <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>Extracted Values:</Typography>
                  
                  <TableContainer component={Paper} sx={{ mt: 1 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Attribute Name</TableCell>
                          <TableCell align="center">PK?</TableCell>
                          <TableCell>Sample Value</TableCell>
                          <TableCell>Extracted Value</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {/* Primary Key Rows */}
                        {Object.entries(documentValidation.extracted_values.primary_key_values || {}).map(([key, extractedValue]) => (
                          <TableRow key={key}>
                            <TableCell>{key}</TableCell>
                            <TableCell align="center">
                              <Chip label="Yes" size="small" color="secondary" />
                            </TableCell>
                            <TableCell>
                              {testCase?.primary_key_attributes?.[key] || 'N/A'}
                            </TableCell>
                            <TableCell>
                              <strong>{extractedValue ? String(extractedValue) : 'Not found'}</strong>
                            </TableCell>
                          </TableRow>
                        ))}
                        
                        {/* Non-PK Attribute Row */}
                        {testCase?.attribute_name && (
                          <TableRow>
                            <TableCell>{testCase.attribute_name}</TableCell>
                            <TableCell align="center">
                              <Chip label="No" size="small" variant="outlined" />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" color="text.secondary">Not Shown</Typography>
                            </TableCell>
                            <TableCell>
                              <strong>{documentValidation.extracted_values.attribute_value || 'Not found'}</strong>
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
              
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Submission Notes (Optional)"
                value={submissionNotes}
                onChange={(e) => setSubmissionNotes(e.target.value)}
                placeholder="Add any notes about this submission..."
                sx={{ mb: 2 }}
              />
              <Button
                fullWidth
                variant="contained"
                startIcon={uploading ? <CircularProgress size={16} /> : <CloudUploadIcon />}
                onClick={handleDocumentUpload}
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Upload Document'}
              </Button>
            </Box>
          );
        default:
          return null;
      }
    } else {
      // Data source evidence steps
      switch (step) {
        case 0:
          return (
            <Box>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', gap: 2, mb: 1 }}>
                  <FormControl fullWidth>
                    <InputLabel>Select Data Source</InputLabel>
                    <Select
                      value={selectedDataSource}
                      onChange={(e) => setSelectedDataSource(e.target.value)}
                      disabled={sourcesLoading}
                    >
                      {dataSources?.map((source: DataSource) => (
                        <MenuItem key={source.data_source_id} value={source.data_source_id}>
                          <Box display="flex" alignItems="center" gap={1}>
                            <StorageIcon fontSize="small" />
                            {source.source_name}
                            <Chip
                              label={source.connection_type}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    onClick={() => setAddDataSourceOpen(true)}
                    sx={{ minWidth: 150 }}
                  >
                    Add Data Source
                  </Button>
                </Box>
              </Box>
              
              {testCase?.primary_key_attributes && Object.keys(testCase.primary_key_attributes).length > 0 && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>Primary Key Values:</Typography>
                  {Object.entries(testCase.primary_key_attributes).map(([key, value]) => (
                    <Chip
                      key={key}
                      label={`${key}: ${value}`}
                      size="small"
                      sx={{ mr: 1, mb: 0.5 }}
                    />
                  ))}
                </Alert>
              )}
              
              <TextField
                fullWidth
                multiline
                rows={8}
                label="SQL Query"
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
                placeholder="Enter your SQL query here..."
                sx={{ fontFamily: 'monospace' }}
              />
              
              {selectedDataSource && (
                <Button
                  size="small"
                  startIcon={<CodeIcon />}
                  onClick={() => setQueryText(generateSampleQuery())}
                  sx={{ mt: 1 }}
                >
                  Generate Sample Query
                </Button>
              )}
              
              {/* Navigation button to proceed to validation */}
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  endIcon={<PlayArrowIcon />}
                  onClick={() => setActiveStep(1)}
                  disabled={!selectedDataSource || !queryText.trim()}
                >
                  Next: Validate Query
                </Button>
              </Box>
            </Box>
          );
        case 1:
          return (
            <Box>
              <Button
                fullWidth
                variant="contained"
                startIcon={validating ? <CircularProgress size={16} /> : <PlayArrowIcon />}
                onClick={handleValidateQuery}
                disabled={validating || !selectedDataSource || !queryText}
                sx={{ mb: 2 }}
              >
                {validating ? 'Validating...' : 'Validate Query'}
              </Button>
              
              {queryValidation && (
                <Box>
                  {queryValidation.validation_status === 'success' ? (
                    <>
                      <Alert severity="success" sx={{ mb: 2 }}>
                        <Box display="flex" alignItems="center" gap={1}>
                          <CheckCircleIcon />
                          <Box>
                            <Typography variant="subtitle2">Query Validated Successfully</Typography>
                            <Typography variant="body2">
                              Found {queryValidation.row_count} records • 
                              Execution time: {queryValidation.execution_time_ms}ms
                            </Typography>
                          </Box>
                        </Box>
                      </Alert>
                      
                      {/* Display validation warnings if any */}
                      {queryValidation.validation_warnings && queryValidation.validation_warnings.length > 0 && (
                        <Alert severity="warning" sx={{ mb: 2 }}>
                          <Box>
                            <Typography variant="subtitle2" gutterBottom>
                              Validation Warnings
                            </Typography>
                            {queryValidation.validation_warnings.map((warning, idx) => (
                              <Typography key={idx} variant="body2" sx={{ mb: 0.5 }}>
                                • {warning}
                              </Typography>
                            ))}
                          </Box>
                        </Alert>
                      )}
                    </>
                  ) : (
                    <Alert severity="error" sx={{ mb: 2 }}>
                      <Box>
                        <Typography variant="subtitle2">Validation Failed</Typography>
                        <Typography variant="body2">{queryValidation.validation_message}</Typography>
                        {queryValidation.validation_errors?.map((error, idx) => (
                          <Typography key={idx} variant="caption" display="block">
                            • {error}
                          </Typography>
                        ))}
                      </Box>
                    </Alert>
                  )}
                  
                  {queryValidation.sample_data && queryValidation.sample_data.length > 0 && (
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
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
                            {testCase?.primary_key_attributes && Object.entries(testCase.primary_key_attributes).map(([pkName, sampleValue]) => {
                              // Find the query value for this primary key
                              const queryValue = queryValidation.sample_data?.[0]?.[pkName];
                              
                              return (
                                <TableRow key={`pk_${pkName}`}>
                                  <TableCell>{pkName}</TableCell>
                                  <TableCell align="center">
                                    <Chip label="Yes" size="small" color="secondary" />
                                  </TableCell>
                                  <TableCell>
                                    <strong>{sampleValue || 'N/A'}</strong>
                                  </TableCell>
                                  <TableCell>
                                    <strong style={{ color: queryValue ? 'inherit' : 'red' }}>
                                      {queryValue !== null && queryValue !== undefined ? String(queryValue) : 'Not found'}
                                    </strong>
                                  </TableCell>
                                </TableRow>
                              );
                            })}
                            
                            {/* Show target attribute */}
                            {testCase?.attribute_name && (() => {
                              // Normalize the attribute name for comparison
                              const attributeNameLower = testCase.attribute_name.toLowerCase().trim();
                              
                              // Find matching column - try multiple strategies
                              const matchingColumn = queryValidation.sample_data?.[0] && Object.keys(queryValidation.sample_data[0]).find(col => {
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
                              
                              const queryValue = matchingColumn && queryValidation.sample_data?.[0] ? queryValidation.sample_data[0][matchingColumn] : null;
                              
                              return (
                                <TableRow>
                                  <TableCell>
                                    {testCase.attribute_name}
                                    {matchingColumn && matchingColumn !== testCase.attribute_name && (
                                      <Typography variant="caption" color="text.secondary" display="block">
                                        (Column: {matchingColumn})
                                      </Typography>
                                    )}
                                  </TableCell>
                                  <TableCell align="center">
                                    <Chip label="No" size="small" variant="outlined" />
                                  </TableCell>
                                  <TableCell>
                                    <Typography variant="body2" color="text.secondary">Not Shown</Typography>
                                  </TableCell>
                                  <TableCell>
                                    <strong style={{ color: queryValue ? 'green' : 'red' }}>
                                      {queryValue !== null && queryValue !== undefined ? String(queryValue) : 'Not found'}
                                    </strong>
                                  </TableCell>
                                </TableRow>
                              );
                            })()}
                          </TableBody>
                        </Table>
                      </TableContainer>
                      <Alert severity="info" sx={{ mt: 2 }}>
                        <Typography variant="body2">
                          Please verify that the extracted values match your expected data before submitting.
                        </Typography>
                      </Alert>
                    </Box>
                  )}
                </Box>
              )}
              
              {/* Navigation controls */}
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Button
                  variant="outlined"
                  onClick={() => setActiveStep(0)}
                >
                  Back
                </Button>
                {queryValidation?.validation_status === 'success' && (
                  <Button
                    variant="contained"
                    onClick={() => setActiveStep(2)}
                    color="primary"
                  >
                    Next: Submit Evidence
                  </Button>
                )}
              </Box>
            </Box>
          );
        case 2:
          return (
            <Box>
              <Alert severity="success" sx={{ mb: 2 }}>
                Query validated and ready for submission
              </Alert>
              
              {/* Show validation results summary */}
              {queryValidation?.sample_data && queryValidation.sample_data.length > 0 && (
                <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>Validation Results Summary:</Typography>
                  
                  <TableContainer component={Paper} sx={{ mt: 1 }}>
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
                        {testCase?.primary_key_attributes && Object.entries(testCase.primary_key_attributes).map(([pkName, sampleValue]) => {
                          const queryValue = queryValidation.sample_data?.[0]?.[pkName];
                          return (
                            <TableRow key={`pk_${pkName}`}>
                              <TableCell>{pkName}</TableCell>
                              <TableCell align="center">
                                <Chip label="Yes" size="small" color="secondary" />
                              </TableCell>
                              <TableCell>
                                <strong>{sampleValue || 'N/A'}</strong>
                              </TableCell>
                              <TableCell>
                                <strong style={{ color: queryValue ? 'inherit' : 'red' }}>
                                  {queryValue !== null && queryValue !== undefined ? String(queryValue) : 'Not found'}
                                </strong>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                        
                        {/* Show target attribute */}
                        {testCase?.attribute_name && (() => {
                          // Normalize the attribute name for comparison
                          const attributeNameLower = testCase.attribute_name.toLowerCase().trim();
                          
                          // Find matching column - try multiple strategies
                          const matchingColumn = queryValidation.sample_data?.[0] && Object.keys(queryValidation.sample_data[0]).find(col => {
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
                          
                          const queryValue = matchingColumn && queryValidation.sample_data?.[0] ? queryValidation.sample_data[0][matchingColumn] : null;
                          
                          return (
                            <TableRow>
                              <TableCell>
                                {testCase.attribute_name}
                                {matchingColumn && matchingColumn !== testCase.attribute_name && (
                                  <Typography variant="caption" color="text.secondary" display="block">
                                    (Column: {matchingColumn})
                                  </Typography>
                                )}
                              </TableCell>
                              <TableCell align="center">
                                <Chip label="No" size="small" variant="outlined" />
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2" color="text.secondary">Not Shown</Typography>
                              </TableCell>
                              <TableCell>
                                <strong style={{ color: queryValue ? 'green' : 'red' }}>
                                  {queryValue !== null && queryValue !== undefined ? String(queryValue) : 'Not found'}
                                </strong>
                              </TableCell>
                            </TableRow>
                          );
                        })()}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
              
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Submission Notes (Optional)"
                value={submissionNotes}
                onChange={(e) => setSubmissionNotes(e.target.value)}
                placeholder="Add any notes about this submission..."
                sx={{ mb: 2 }}
              />
              
              {/* Navigation controls */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                <Button
                  variant="outlined"
                  onClick={() => setActiveStep(1)}
                >
                  Back
                </Button>
                <Button
                  fullWidth
                  variant="contained"
                  color="success"
                  startIcon={submitting ? <CircularProgress size={16} /> : <CheckCircleIcon />}
                  onClick={handleDataSourceSubmit}
                  disabled={submitting}
                >
                  {submitting ? 'Submitting...' : 'Submit Data Source Evidence'}
                </Button>
              </Box>
            </Box>
          );
        default:
          return null;
      }
    }
  };

  const getSteps = () => {
    if (evidenceType === 'document') {
      return ['Select Document', 'Validate Content', 'Upload & Submit'];
    }
    return ['Configure Query', 'Validate Query', 'Submit Evidence'];
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Submit Evidence</Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {/* Test Case Details */}
        {testCase && (
          <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom color="primary">
              Test Case Details
            </Typography>
            
            <Stack spacing={1}>
              {/* Attribute Name (Scoped Attribute) */}
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Scoped Attribute:
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {testCase.attribute_name}
                </Typography>
              </Box>

              {/* Sample Identifier */}
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Sample ID:
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  {testCase.sample_identifier}
                </Typography>
              </Box>

              {/* Primary Key Values */}
              {testCase.primary_key_attributes && Object.keys(testCase.primary_key_attributes).length > 0 && (
                <Box>
                  <Typography variant="caption" color="text.secondary" gutterBottom>
                    Primary Key Values:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 0.5 }}>
                    {Object.entries(testCase.primary_key_attributes).map(([key, value]) => (
                      <Chip
                        key={key}
                        label={`${key}: ${value}`}
                        size="small"
                        variant="outlined"
                        color="primary"
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </Stack>
            
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="caption">
                Please provide evidence that contains the value for "{testCase.attribute_name}" 
                corresponding to the sample identified by the primary key values shown above.
              </Typography>
            </Alert>
          </Box>
        )}

        <Tabs
          value={evidenceType}
          onChange={(e, value) => {
            setEvidenceType(value);
            setActiveStep(0);
          }}
          sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
        >
          <Tab
            icon={<AttachFileIcon />}
            iconPosition="start"
            label="Upload Document"
            value="document"
          />
          <Tab
            icon={<StorageIcon />}
            iconPosition="start"
            label={sourcesLoading ? "Loading..." : "Connect Data Source"}
            value="data_source"
            disabled={sourcesLoading}
          />
        </Tabs>
        
        {evidenceType === 'data_source' && (!dataSources || dataSources.length === 0) && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Box>
              <Typography variant="body2" gutterBottom>
                No data sources available yet.
              </Typography>
              <Button
                size="small"
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={() => {
                  onClose();
                  // Trigger the add data source dialog
                  // This assumes the parent component has a way to open the add data source dialog
                  window.dispatchEvent(new CustomEvent('open-add-data-source'));
                }}
                sx={{ mt: 1 }}
              >
                Add Data Source
              </Button>
            </Box>
          </Alert>
        )}
        
        <Stepper activeStep={activeStep} orientation="vertical">
          {getSteps().map((label, index) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
              <StepContent>
                {getStepContent(index)}
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
      </DialogActions>
      
      {/* Add Data Source Dialog */}
      <AddDataSourceDialog
        open={addDataSourceOpen}
        onClose={() => setAddDataSourceOpen(false)}
        onSuccess={() => {
          setAddDataSourceOpen(false);
          // Refetch data sources
          queryClient.invalidateQueries({ queryKey: ['data-sources', testCase?.cycle_id, testCase?.report_id] });
        }}
      />
    </Dialog>
  );
};

export default EvidenceUploadDialog;