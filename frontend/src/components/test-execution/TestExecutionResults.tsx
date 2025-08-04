import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  Chip,
  Alert,
  TextField,
  Stack,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Send as SendIcon,
  Visibility as VisibilityIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { TestExecution } from '../../types/test-execution';
import apiClient from '../../api/client';
import { toast } from 'react-toastify';

interface TestExecutionResultsProps {
  execution: TestExecution;
  testCase: any;
  sampleData: any;
  onReviewComplete: () => void;
}

export const TestExecutionResults: React.FC<TestExecutionResultsProps> = ({
  execution,
  testCase,
  sampleData,
  onReviewComplete,
}) => {
  const [open, setOpen] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [resendDialogOpen, setResendDialogOpen] = useState(false);
  const [resendNotes, setResendNotes] = useState('');

  const handleOpen = () => setOpen(true);
  const handleClose = () => {
    setOpen(false);
    setReviewNotes('');
  };

  const handleApprove = async () => {
    setSubmitting(true);
    try {
      await apiClient.post(`/test-execution/executions/${execution.id}/review`, {
        review_status: 'approved',
        review_notes: reviewNotes || 'Test execution results approved',
        accuracy_score: 1.0,
        completeness_score: 1.0,
        consistency_score: 1.0,
      });
      toast.success('Test execution approved successfully');
      handleClose();
      onReviewComplete();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to approve test execution');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    const notes = reviewNotes.trim() || 'Test execution results do not match expected values';
    
    setSubmitting(true);
    try {
      await apiClient.post(`/test-execution/executions/${execution.id}/review`, {
        review_status: 'rejected',
        review_notes: notes,
        requires_retest: true,
        retest_reason: notes,
        accuracy_score: 0.0,
        completeness_score: 0.0,
        consistency_score: 0.0,
      });
      toast.success('Test execution rejected');
      handleClose();
      onReviewComplete();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to reject test execution');
    } finally {
      setSubmitting(false);
    }
  };

  const handleResendToDataOwner = async () => {
    if (!resendNotes.trim()) {
      toast.error('Please provide notes for the data owner');
      return;
    }
    
    setSubmitting(true);
    try {
      // Create revision request for the evidence
      await apiClient.post(`/test-executions/${execution.id}/request-revision`, {
        revision_reason: resendNotes,
        revision_type: 'evidence_update',
        requested_from: 'data_owner',
      });
      toast.success('Revision request sent to data owner');
      setResendDialogOpen(false);
      setResendNotes('');
      onReviewComplete();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to send revision request');
    } finally {
      setSubmitting(false);
    }
  };

  const getComparisonData = () => {
    const analysisResults = execution.analysis_results || {};
    const extractionDetails = analysisResults.extraction_details || {};
    
    // Build comparison rows
    const rows = [];
    
    // Check if we have query results with all columns (like RFI does)
    if (analysisResults.all_rows && analysisResults.all_rows.length > 0) {
      const firstRow = analysisResults.all_rows[0];
      const columns = analysisResults.columns || Object.keys(firstRow);
      
      // Show ALL columns from the query result (like RFI does)
      columns.forEach((columnName: string) => {
        const value = firstRow[columnName];
        if (value === undefined) return; // Skip if not in result
        
        // Determine if this is a primary key
        const primaryKeyList = sampleData?.primary_key_list || 
                              ['Bank ID', 'Period ID', 'Customer ID', 'Reference Number'];
        const isPrimaryKey = primaryKeyList.some((pk: string) => 
          pk.toLowerCase() === columnName.toLowerCase() ||
          pk.toLowerCase().replace(/\s+/g, '') === columnName.toLowerCase().replace(/\s+/g, '')
        );
        
        // Get expected value
        let sampleValue = 'N/A';
        if (isPrimaryKey) {
          // Look for primary key value in various places
          // First check in analysis_results which now includes sample_primary_key_values
          sampleValue = analysisResults.sample_primary_key_values?.[columnName] ||
                       analysisResults.sample_data?.[columnName] ||
                       testCase.primary_key_attributes?.[columnName] || 
                       sampleData?.primary_key_attributes?.[columnName] ||
                       sampleData?.primary_key_values?.[columnName] ||
                       sampleData?.sample_data?.[columnName] || 'N/A';
        } else if (columnName.toLowerCase().includes(testCase.attribute_name?.toLowerCase() || '')) {
          // This might be our target attribute
          sampleValue = analysisResults.expected_value ||
                       analysisResults.sample_data?.[columnName] ||
                       testCase.attribute_sample_value || 
                       sampleData?.sample_data?.[testCase.attribute_name] || 
                       sampleData?.sample_data?.[columnName] ||
                       sampleData?.expected_value || 'N/A';
        } else {
          // Check if it's in the sample data
          sampleValue = analysisResults.sample_data?.[columnName] || 'N/A';
        }
        
        rows.push({
          attributeName: columnName,
          isPrimaryKey: isPrimaryKey,
          sampleValue: sampleValue,
          extractedValue: value,
          isMatch: null, // Don't auto-decide match for display
        });
      });
    } else {
      // Fallback for document evidence - show all primary keys from sample data
      const primaryKeys = analysisResults.primary_key_values || extractionDetails.primary_key_values || {};
      const samplePrimaryKeys = analysisResults.sample_primary_key_values || {};
      
      // Add primary key rows - use sample primary keys to ensure we show all of them
      Object.entries(samplePrimaryKeys).forEach(([key, sampleValue]) => {
        rows.push({
          attributeName: key,
          isPrimaryKey: true,
          sampleValue: sampleValue || 'N/A',
          extractedValue: primaryKeys[key] || 'Not extracted',
          isMatch: null,
        });
      });
      
      // If extracted primary keys exist that aren't in sample, add those too
      Object.entries(primaryKeys).forEach(([key, value]) => {
        if (!samplePrimaryKeys[key]) {
          rows.push({
            attributeName: key,
            isPrimaryKey: true,
            sampleValue: testCase.primary_key_attributes?.[key] || sampleData?.primary_key_attributes?.[key] || 'N/A',
            extractedValue: value,
            isMatch: null,
          });
        }
      });
      
      // Add the main attribute being tested
      if (analysisResults.attribute_name || testCase.attribute_name) {
        const attributeName = analysisResults.attribute_name || testCase.attribute_name;
        const sampleValue = analysisResults.expected_value || 
                           sampleData?.sample_data?.[attributeName] || 
                           testCase.attribute_sample_value || 
                           'N/A';
        const extractedValue = analysisResults.actual_value || 
                              execution.extracted_value || 
                              extractionDetails.extracted_value;
        
        rows.push({
          attributeName: attributeName,
          isPrimaryKey: false,
          sampleValue: sampleValue,
          extractedValue: extractedValue,
          isMatch: null,
        });
      }
    }
    
    return rows;
  };

  const comparisonRows = getComparisonData();

  return (
    <>
      <Button
        variant="outlined"
        size="small"
        startIcon={<VisibilityIcon />}
        onClick={handleOpen}
      >
        View Results
      </Button>

      <Dialog
        open={open}
        onClose={handleClose}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Test Execution Results</Typography>
            <IconButton onClick={handleClose} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <Alert 
              severity="info" 
              sx={{ mb: 2 }}
            >
              <Typography variant="body2">
                Please review the extracted values below and determine if the test passes or fails.
              </Typography>
              {execution.llm_confidence_score && (
                <Typography variant="caption" component="div">
                  Extraction Confidence: {(execution.llm_confidence_score * 100).toFixed(0)}%
                </Typography>
              )}
            </Alert>

            <Typography variant="subtitle2" gutterBottom>
              Extracted Values from Evidence
            </Typography>
            
            <TableContainer component={Paper} sx={{ mb: 2 }}>
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
                  {comparisonRows.map((row, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Typography variant="body2">{row.attributeName}</Typography>
                      </TableCell>
                      <TableCell align="center">
                        {row.isPrimaryKey ? (
                          <Chip label="Yes" size="small" color="secondary" />
                        ) : (
                          <Chip label="No" size="small" variant="outlined" />
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {row.sampleValue || 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            fontWeight: 'medium',
                            color: row.extractedValue !== null && row.extractedValue !== undefined ? 'inherit' : 'text.secondary' 
                          }}
                        >
                          {row.extractedValue !== null && row.extractedValue !== undefined 
                            ? String(row.extractedValue) 
                            : <em style={{ color: '#999' }}>Not found</em>}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {execution.llm_analysis_rationale && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Analysis Details
                </Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="body2">
                    {execution.llm_analysis_rationale}
                  </Typography>
                </Paper>
              </Box>
            )}

            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Tester Review Notes
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={3}
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Add your review notes here (optional for pass, recommended for fail)..."
                variant="outlined"
              />
            </Box>
          </Box>
        </DialogContent>

        <DialogActions sx={{ p: 2 }}>
          <Stack direction="row" spacing={2} sx={{ width: '100%' }}>
            <Button
              variant="outlined"
              color="warning"
              startIcon={<SendIcon />}
              onClick={() => setResendDialogOpen(true)}
              disabled={submitting}
            >
              Request Revision
            </Button>
            <Box sx={{ flexGrow: 1 }} />
            <Button
              variant="outlined"
              color="error"
              startIcon={<CancelIcon />}
              onClick={handleReject}
              disabled={submitting}
            >
              Fail
            </Button>
            <Button
              variant="contained"
              color="success"
              startIcon={<CheckCircleIcon />}
              onClick={handleApprove}
              disabled={submitting}
            >
              Pass
            </Button>
          </Stack>
        </DialogActions>
      </Dialog>

      {/* Resend to Data Owner Dialog */}
      <Dialog
        open={resendDialogOpen}
        onClose={() => setResendDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Request Evidence Revision</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Please provide details about what needs to be corrected or clarified in the evidence.
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={4}
              value={resendNotes}
              onChange={(e) => setResendNotes(e.target.value)}
              placeholder="Explain what needs to be revised..."
              variant="outlined"
              autoFocus
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResendDialogOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={handleResendToDataOwner}
            disabled={submitting || !resendNotes.trim()}
          >
            Send Request
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default TestExecutionResults;