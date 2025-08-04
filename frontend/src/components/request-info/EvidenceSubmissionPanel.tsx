import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Alert,
  Stack,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Divider,
  Chip,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  CloudUpload as CloudUploadIcon,
  AttachFile as AttachFileIcon,
  Storage as StorageIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Code as CodeIcon,
  Visibility as VisibilityIcon,
  ExpandMore as ExpandMoreIcon,
  Schedule as ScheduleIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNotifications } from '../../contexts/NotificationContext';
import RequestInfoAPI from '../../api/requestInfo';

interface TestCase {
  test_case_id: string;
  attribute_name: string;
  sample_identifier: string;
  primary_key_attributes: Record<string, any>;
  submission_deadline: string;
  special_instructions: string;
  status: string;
}

interface DataSource {
  id: number;
  name: string;
  description: string;
  data_source_type: string;
}

interface Evidence {
  id: number;
  evidence_type: 'document' | 'data_source';
  version_number: number;
  is_current: boolean;
  validation_status: string;
  validation_notes: string;
  submitted_at: string;
  submission_notes: string;
  // Document fields
  document_name?: string;
  document_size?: number;
  mime_type?: string;
  // Data source fields
  data_source_id?: number;
  query_text?: string;
  query_parameters?: Record<string, any>;
  query_result_sample?: Record<string, any>;
}

interface ValidationResult {
  rule: string;
  result: 'passed' | 'failed' | 'warning';
  message: string;
  validated_at: string;
}

interface TesterDecision {
  decision: 'approved' | 'rejected' | 'requires_revision';
  decision_notes: string;
  decision_date: string;
  decided_by_name: string;
  requires_resubmission: boolean;
  resubmission_deadline?: string;
  follow_up_instructions?: string;
}

interface EvidenceSubmissionPanelProps {
  testCaseId: string;
  onEvidenceSubmitted?: () => void;
}

const EvidenceSubmissionPanel: React.FC<EvidenceSubmissionPanelProps> = ({
  testCaseId,
  onEvidenceSubmitted,
}) => {
  const [evidenceType, setEvidenceType] = useState<'document' | 'data_source'>('document');
  const [submissionNotes, setSubmissionNotes] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedDataSource, setSelectedDataSource] = useState<number | null>(null);
  const [queryText, setQueryText] = useState('');
  const [queryParameters, setQueryParameters] = useState('{}');
  const [showValidationDetails, setShowValidationDetails] = useState(false);
  const { showToast } = useNotifications();
  const queryClient = useQueryClient();

  // Get evidence portal data
  const { data: portalData, isLoading } = useQuery({
    queryKey: ['evidence-portal', testCaseId],
    queryFn: () => RequestInfoAPI.getEvidencePortalData(testCaseId),
  });

  // Submit document evidence
  const documentSubmissionMutation = useMutation({
    mutationFn: (data: FormData) => RequestInfoAPI.submitDocumentEvidence(testCaseId, data),
    onSuccess: () => {
      showToast('success', 'Document evidence submitted successfully');
      queryClient.invalidateQueries({ queryKey: ['evidence-portal', testCaseId] });
      setSelectedFile(null);
      setSubmissionNotes('');
      onEvidenceSubmitted?.();
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Failed to submit document evidence');
    },
  });

  // Submit data source evidence
  const dataSourceSubmissionMutation = useMutation({
    mutationFn: (data: any) => RequestInfoAPI.submitDataSourceEvidence(testCaseId, data),
    onSuccess: () => {
      showToast('success', 'Data source evidence submitted successfully');
      queryClient.invalidateQueries({ queryKey: ['evidence-portal', testCaseId] });
      setSelectedDataSource(null);
      setQueryText('');
      setQueryParameters('{}');
      setSubmissionNotes('');
      onEvidenceSubmitted?.();
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Failed to submit data source evidence');
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleDocumentSubmission = () => {
    if (!selectedFile) {
      showToast('error', 'Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    if (submissionNotes) {
      formData.append('submission_notes', submissionNotes);
    }

    documentSubmissionMutation.mutate(formData);
  };

  const handleDataSourceSubmission = () => {
    if (!selectedDataSource || !queryText) {
      showToast('error', 'Please select a data source and enter a query');
      return;
    }

    let parsedParameters = {};
    try {
      parsedParameters = JSON.parse(queryParameters);
    } catch (error) {
      showToast('error', 'Invalid JSON format for query parameters');
      return;
    }

    const data = {
      data_source_id: selectedDataSource,
      query_text: queryText,
      query_parameters: parsedParameters,
      submission_notes: submissionNotes,
    };

    dataSourceSubmissionMutation.mutate(data);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'valid':
        return 'success';
      case 'invalid':
        return 'error';
      case 'requires_review':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'valid':
        return <CheckCircleIcon />;
      case 'invalid':
        return <ErrorIcon />;
      case 'requires_review':
        return <WarningIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const getValidationIcon = (result: string) => {
    switch (result) {
      case 'passed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography variant="body2" color="text.secondary" mt={2}>
          Loading evidence submission panel...
        </Typography>
      </Box>
    );
  }

  const testCase = portalData?.test_case as TestCase;
  const currentEvidence = portalData?.current_evidence as Evidence;
  const validationResults = portalData?.validation_results as ValidationResult[];
  const testerDecisions = portalData?.tester_decisions as TesterDecision[];
  const availableDataSources = portalData?.available_data_sources as DataSource[];
  const canSubmitEvidence = portalData?.can_submit_evidence;
  const canResubmit = portalData?.can_resubmit;

  return (
    <Box>
      <Typography variant="h6" display="flex" alignItems="center" gap={1} mb={3}>
        <AssignmentIcon />
        Evidence Submission - {testCase?.attribute_name}
      </Typography>

      <Grid container spacing={3}>
        {/* Test Case Information */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Test Case Details
              </Typography>
              
              <Stack spacing={2}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Attribute
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {testCase?.attribute_name}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Sample Identifier
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {testCase?.sample_identifier}
                  </Typography>
                </Box>

                {testCase?.primary_key_attributes && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Primary Key Attributes
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 1, bgcolor: 'grey.50' }}>
                      {Object.entries(testCase.primary_key_attributes).map(([key, value]) => (
                        <Typography key={key} variant="body2" component="div">
                          <strong>{key}:</strong> {String(value)}
                        </Typography>
                      ))}
                    </Paper>
                  </Box>
                )}

                {testCase?.submission_deadline && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Submission Deadline
                    </Typography>
                    <Typography variant="body1" display="flex" alignItems="center" gap={1}>
                      <ScheduleIcon fontSize="small" />
                      {new Date(testCase.submission_deadline).toLocaleDateString()}
                    </Typography>
                  </Box>
                )}

                {testCase?.special_instructions && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Special Instructions
                    </Typography>
                    <Alert severity="info" sx={{ mt: 1 }}>
                      {testCase.special_instructions}
                    </Alert>
                  </Box>
                )}

                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip
                    label={testCase?.status}
                    color={
                      testCase?.status === 'Approved' ? 'success' :
                      testCase?.status === 'Rejected' ? 'error' :
                      testCase?.status === 'Requires Revision' ? 'warning' : 'default'
                    }
                    size="small"
                  />
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Evidence Submission */}
        <Grid size={{ xs: 12, md: 8 }}>
          {/* Current Evidence Display */}
          {currentEvidence && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Current Evidence (Version {currentEvidence.version_number})
                </Typography>

                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <Chip
                    icon={getStatusIcon(currentEvidence.validation_status)}
                    label={currentEvidence.validation_status}
                    color={getStatusColor(currentEvidence.validation_status) as any}
                    size="small"
                  />
                  <Typography variant="body2" color="text.secondary">
                    Submitted: {new Date(currentEvidence.submitted_at).toLocaleDateString()}
                  </Typography>
                </Box>

                {currentEvidence.evidence_type === 'document' && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Document: {currentEvidence.document_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Size: {currentEvidence.document_size ? formatFileSize(currentEvidence.document_size) : 'Unknown'}
                    </Typography>
                  </Box>
                )}

                {currentEvidence.evidence_type === 'data_source' && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Data Source Query
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 1, bgcolor: 'grey.50', fontFamily: 'monospace' }}>
                      <Typography variant="body2" component="pre">
                        {currentEvidence.query_text}
                      </Typography>
                    </Paper>
                  </Box>
                )}

                {currentEvidence.submission_notes && (
                  <Box mt={2}>
                    <Typography variant="body2" color="text.secondary">
                      Submission Notes:
                    </Typography>
                    <Typography variant="body2">
                      {currentEvidence.submission_notes}
                    </Typography>
                  </Box>
                )}

                {/* Validation Results */}
                {validationResults && validationResults.length > 0 && (
                  <Accordion sx={{ mt: 2 }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle2">
                        Validation Results ({validationResults.length})
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List>
                        {validationResults.map((result, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              {getValidationIcon(result.result)}
                            </ListItemIcon>
                            <ListItemText
                              primary={result.rule}
                              secondary={result.message}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                )}

                {/* Tester Decisions */}
                {testerDecisions && testerDecisions.length > 0 && (
                  <Accordion sx={{ mt: 2 }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle2">
                        Tester Decisions ({testerDecisions.length})
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Stack spacing={2}>
                        {testerDecisions.map((decision, index) => (
                          <Card key={index} variant="outlined">
                            <CardContent>
                              <Box display="flex" alignItems="center" gap={2} mb={1}>
                                <Chip
                                  label={decision.decision}
                                  color={
                                    decision.decision === 'approved' ? 'success' :
                                    decision.decision === 'rejected' ? 'error' : 'warning'
                                  }
                                  size="small"
                                />
                                <Typography variant="body2" color="text.secondary">
                                  {decision.decided_by_name}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {new Date(decision.decision_date).toLocaleDateString()}
                                </Typography>
                              </Box>
                              
                              {decision.decision_notes && (
                                <Typography variant="body2" sx={{ mb: 1 }}>
                                  {decision.decision_notes}
                                </Typography>
                              )}

                              {decision.requires_resubmission && (
                                <Alert severity="warning" sx={{ mt: 1 }}>
                                  Resubmission required
                                  {decision.resubmission_deadline && (
                                    <Typography variant="body2">
                                      Deadline: {new Date(decision.resubmission_deadline).toLocaleDateString()}
                                    </Typography>
                                  )}
                                </Alert>
                              )}

                              {decision.follow_up_instructions && (
                                <Alert severity="info" sx={{ mt: 1 }}>
                                  {decision.follow_up_instructions}
                                </Alert>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </Stack>
                    </AccordionDetails>
                  </Accordion>
                )}
              </CardContent>
            </Card>
          )}

          {/* Evidence Submission Form */}
          {(canSubmitEvidence || canResubmit) && (
            <Card>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  {canResubmit ? 'Resubmit Evidence' : 'Submit Evidence'}
                </Typography>

                <Stack spacing={3}>
                  {/* Evidence Type Selection */}
                  <Tabs
                    value={evidenceType}
                    onChange={(e, value) => setEvidenceType(value)}
                    sx={{ borderBottom: 1, borderColor: 'divider' }}
                  >
                    <Tab
                      label="Document Evidence"
                      value="document"
                      icon={<AttachFileIcon />}
                      iconPosition="start"
                    />
                    <Tab
                      label="Data Source Evidence"
                      value="data_source"
                      icon={<StorageIcon />}
                      iconPosition="start"
                    />
                  </Tabs>

                  {/* Document Evidence Form */}
                  {evidenceType === 'document' && (
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Upload document evidence (PDF, Excel, Word, Images)
                      </Typography>
                      
                      <Box
                        display="flex"
                        flexDirection="column"
                        alignItems="center"
                        gap={2}
                        p={3}
                        border={2}
                        borderColor="primary.main"
                        borderRadius={1}
                        sx={{ cursor: 'pointer', borderStyle: 'dashed' }}
                        onClick={() => document.getElementById('file-input')?.click()}
                      >
                        <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main' }} />
                        <Typography variant="h6" color="primary.main">
                          Click to upload file
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          or drag and drop
                        </Typography>
                        <input
                          id="file-input"
                          type="file"
                          hidden
                          onChange={handleFileSelect}
                          accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.bmp,.tiff"
                        />
                      </Box>

                      {selectedFile && (
                        <Alert severity="info" sx={{ mt: 2 }}>
                          Selected: {selectedFile.name} ({formatFileSize(selectedFile.size)})
                        </Alert>
                      )}
                    </Box>
                  )}

                  {/* Data Source Evidence Form */}
                  {evidenceType === 'data_source' && (
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Provide query-based evidence from data sources
                      </Typography>

                      <Stack spacing={2}>
                        <FormControl fullWidth>
                          <InputLabel>Select Data Source</InputLabel>
                          <Select
                            value={selectedDataSource || ''}
                            onChange={(e) => setSelectedDataSource(e.target.value as number)}
                          >
                            {availableDataSources?.map((source) => (
                              <MenuItem key={source.id} value={source.id}>
                                <Box display="flex" alignItems="center" gap={1}>
                                  <StorageIcon fontSize="small" />
                                  {source.name}
                                  <Chip
                                    label={source.data_source_type}
                                    size="small"
                                    variant="outlined"
                                  />
                                </Box>
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>

                        <TextField
                          label="SQL Query"
                          multiline
                          rows={6}
                          value={queryText}
                          onChange={(e) => setQueryText(e.target.value)}
                          placeholder="Enter your SQL query here..."
                          sx={{ fontFamily: 'monospace' }}
                          fullWidth
                        />

                        <TextField
                          label="Query Parameters (JSON)"
                          multiline
                          rows={3}
                          value={queryParameters}
                          onChange={(e) => setQueryParameters(e.target.value)}
                          placeholder='{"parameter1": "value1", "parameter2": "value2"}'
                          sx={{ fontFamily: 'monospace' }}
                          fullWidth
                        />
                      </Stack>
                    </Box>
                  )}

                  {/* Submission Notes */}
                  <TextField
                    label="Submission Notes"
                    multiline
                    rows={3}
                    value={submissionNotes}
                    onChange={(e) => setSubmissionNotes(e.target.value)}
                    placeholder="Add any notes about this evidence submission..."
                    fullWidth
                  />

                  {/* Submit Button */}
                  <Button
                    variant="contained"
                    size="large"
                    startIcon={evidenceType === 'document' ? <AttachFileIcon /> : <StorageIcon />}
                    onClick={evidenceType === 'document' ? handleDocumentSubmission : handleDataSourceSubmission}
                    disabled={
                      (evidenceType === 'document' && !selectedFile) ||
                      (evidenceType === 'data_source' && (!selectedDataSource || !queryText)) ||
                      documentSubmissionMutation.isPending ||
                      dataSourceSubmissionMutation.isPending
                    }
                    fullWidth
                  >
                    {documentSubmissionMutation.isPending || dataSourceSubmissionMutation.isPending
                      ? 'Submitting...'
                      : `Submit ${evidenceType === 'document' ? 'Document' : 'Data Source'} Evidence`}
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          )}

          {!canSubmitEvidence && !canResubmit && (
            <Alert severity="info">
              Evidence submission is not available for this test case.
              {testCase?.status === 'Approved' && ' This test case has already been approved.'}
              {testCase?.status === 'Submitted' && ' Evidence has been submitted and is pending review.'}
            </Alert>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default EvidenceSubmissionPanel;