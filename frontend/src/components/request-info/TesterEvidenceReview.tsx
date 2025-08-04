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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Divider,
  FormControlLabel,
  Switch,
  Badge,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Visibility as VisibilityIcon,
  ExpandMore as ExpandMoreIcon,
  Schedule as ScheduleIcon,
  Assignment as AssignmentIcon,
  RateReview as RateReviewIcon,
  Download as DownloadIcon,
  Code as CodeIcon,
  Storage as StorageIcon,
  AttachFile as AttachFileIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNotifications } from '../../contexts/NotificationContext';
import RequestInfoAPI from '../../api/requestInfo';
import Grid from '@mui/material/Grid';

interface Evidence {
  evidence_id: number;
  test_case_id: string;
  sample_id: string;
  attribute_name: string;
  evidence_type: 'document' | 'data_source';
  submitted_by: string;
  submitted_at: string;
  validation_status: string;
  validation_notes: string;
  submission_notes: string;
  // Document fields
  document_name?: string;
  document_size?: number;
  mime_type?: string;
  // Data source fields
  data_source_id?: number;
  query_text?: string;
  query_result_sample?: Record<string, any>;
  // Validation results
  validation_results: ValidationResult[];
}

interface ValidationResult {
  rule: string;
  result: 'passed' | 'failed' | 'warning';
  message: string;
}

interface TesterEvidenceReviewProps {
  phaseId: number;
  onDecisionSubmitted?: () => void;
}

const TesterEvidenceReview: React.FC<TesterEvidenceReviewProps> = ({
  phaseId,
  onDecisionSubmitted,
}) => {
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [showDecisionDialog, setShowDecisionDialog] = useState(false);
  const [decision, setDecision] = useState<'approved' | 'rejected' | 'requires_revision'>('approved');
  const [decisionNotes, setDecisionNotes] = useState('');
  const [requiresResubmission, setRequiresResubmission] = useState(false);
  const [resubmissionDeadline, setResubmissionDeadline] = useState('');
  const [followUpInstructions, setFollowUpInstructions] = useState('');
  const [showValidationDetails, setShowValidationDetails] = useState(false);
  const [showQueryResults, setShowQueryResults] = useState(false);
  const [queryResults, setQueryResults] = useState<any[]>([]);
  const { showToast } = useNotifications();
  const queryClient = useQueryClient();

  // Get evidence pending review
  const { data: evidenceList, isLoading, refetch } = useQuery({
    queryKey: ['evidence-pending-review', phaseId],
    queryFn: () => RequestInfoAPI.getEvidencePendingReview(phaseId),
  });

  // Get evidence validation details
  const { data: validationData } = useQuery({
    queryKey: ['evidence-validation', selectedEvidence?.evidence_id],
    queryFn: () => RequestInfoAPI.getEvidenceValidation(selectedEvidence!.evidence_id),
    enabled: !!selectedEvidence,
  });

  // Submit tester decision
  const submitDecisionMutation = useMutation({
    mutationFn: (data: any) => RequestInfoAPI.submitTesterDecision(selectedEvidence!.evidence_id, data),
    onSuccess: () => {
      showToast('success', 'Decision submitted successfully');
      queryClient.invalidateQueries({ queryKey: ['evidence-pending-review', phaseId] });
      setShowDecisionDialog(false);
      setSelectedEvidence(null);
      setDecisionNotes('');
      setRequiresResubmission(false);
      setResubmissionDeadline('');
      setFollowUpInstructions('');
      onDecisionSubmitted?.();
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Failed to submit decision');
    },
  });

  // Revalidate evidence
  const revalidateMutation = useMutation({
    mutationFn: (evidenceId: number) => RequestInfoAPI.revalidateEvidence(evidenceId),
    onSuccess: () => {
      showToast('success', 'Evidence revalidated successfully');
      queryClient.invalidateQueries({ queryKey: ['evidence-pending-review', phaseId] });
      queryClient.invalidateQueries({ queryKey: ['evidence-validation', selectedEvidence?.evidence_id] });
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Failed to revalidate evidence');
    },
  });

  const handleSubmitDecision = () => {
    if (!selectedEvidence) return;

    const data = {
      decision,
      decision_notes: decisionNotes,
      requires_resubmission: requiresResubmission,
      resubmission_deadline: resubmissionDeadline ? new Date(resubmissionDeadline).toISOString() : null,
      follow_up_instructions: followUpInstructions,
    };

    submitDecisionMutation.mutate(data);
  };

  const handleViewQueryResults = (evidence: Evidence) => {
    if (evidence.query_result_sample) {
      const sampleData = evidence.query_result_sample;
      if (sampleData.sample_rows) {
        setQueryResults(sampleData.sample_rows);
        setShowQueryResults(true);
      }
    }
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

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'approved':
        return 'success';
      case 'rejected':
        return 'error';
      case 'requires_revision':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (isLoading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography variant="body2" color="text.secondary" mt={2}>
          Loading evidence for review...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6" display="flex" alignItems="center" gap={1}>
          <RateReviewIcon />
          Evidence Review
        </Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
          disabled={isLoading}
        >
          Refresh
        </Button>
      </Box>

      {evidenceList && evidenceList.length > 0 ? (
        <Grid container spacing={3}>
          {/* Evidence List */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Evidence Pending Review ({evidenceList.length})
                </Typography>
                
                <Stack spacing={2}>
                  {evidenceList.map((evidence: Evidence) => (
                    <Card
                      key={evidence.evidence_id}
                      variant="outlined"
                      sx={{
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'action.hover' },
                        border: selectedEvidence?.evidence_id === evidence.evidence_id ? 2 : 1,
                        borderColor: selectedEvidence?.evidence_id === evidence.evidence_id ? 'primary.main' : 'divider',
                      }}
                      onClick={() => setSelectedEvidence(evidence)}
                    >
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="start" mb={1}>
                          <Typography variant="subtitle2" fontWeight="medium">
                            {evidence.attribute_name}
                          </Typography>
                          <Chip
                            icon={getStatusIcon(evidence.validation_status)}
                            label={evidence.validation_status}
                            color={getStatusColor(evidence.validation_status) as any}
                            size="small"
                          />
                        </Box>

                        <Typography variant="body2" color="text.secondary" mb={1}>
                          Sample: {evidence.sample_id}
                        </Typography>

                        <Box display="flex" alignItems="center" gap={1} mb={1}>
                          {evidence.evidence_type === 'document' ? (
                            <AttachFileIcon fontSize="small" />
                          ) : (
                            <StorageIcon fontSize="small" />
                          )}
                          <Typography variant="body2">
                            {evidence.evidence_type === 'document' 
                              ? evidence.document_name 
                              : 'Data Source Query'}
                          </Typography>
                        </Box>

                        <Typography variant="body2" color="text.secondary">
                          Submitted by: {evidence.submitted_by}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(evidence.submitted_at).toLocaleDateString()}
                        </Typography>

                        {evidence.validation_results && (
                          <Box mt={1}>
                            <Typography variant="caption" color="text.secondary">
                              Validation: {evidence.validation_results.filter(r => r.result === 'passed').length} passed, {' '}
                              {evidence.validation_results.filter(r => r.result === 'failed').length} failed, {' '}
                              {evidence.validation_results.filter(r => r.result === 'warning').length} warnings
                            </Typography>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Evidence Details */}
          <Grid size={{ xs: 12, md: 6 }}>
            {selectedEvidence ? (
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="subtitle1">
                      Evidence Details
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      <Tooltip title="Revalidate Evidence">
                        <IconButton
                          onClick={() => revalidateMutation.mutate(selectedEvidence.evidence_id)}
                          disabled={revalidateMutation.isPending}
                        >
                          <RefreshIcon />
                        </IconButton>
                      </Tooltip>
                      <Button
                        variant="contained"
                        startIcon={<RateReviewIcon />}
                        onClick={() => setShowDecisionDialog(true)}
                        size="small"
                      >
                        Review
                      </Button>
                    </Stack>
                  </Box>

                  <Stack spacing={3}>
                    {/* Basic Information */}
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Attribute: {selectedEvidence.attribute_name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Sample: {selectedEvidence.sample_id}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Type: {selectedEvidence.evidence_type}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Submitted: {new Date(selectedEvidence.submitted_at).toLocaleDateString()}
                      </Typography>
                    </Box>

                    {/* Evidence Content */}
                    {selectedEvidence.evidence_type === 'document' && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Document Information
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                          <Typography variant="body2">
                            <strong>File:</strong> {selectedEvidence.document_name}
                          </Typography>
                          <Typography variant="body2">
                            <strong>Size:</strong> {selectedEvidence.document_size ? formatFileSize(selectedEvidence.document_size) : 'Unknown'}
                          </Typography>
                          <Typography variant="body2">
                            <strong>Type:</strong> {selectedEvidence.mime_type}
                          </Typography>
                        </Paper>
                      </Box>
                    )}

                    {selectedEvidence.evidence_type === 'data_source' && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Data Source Query
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                          <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                            {selectedEvidence.query_text}
                          </Typography>
                        </Paper>
                        
                        {selectedEvidence.query_result_sample && (
                          <Box mt={2}>
                            <Button
                              startIcon={<VisibilityIcon />}
                              onClick={() => handleViewQueryResults(selectedEvidence)}
                              variant="outlined"
                              size="small"
                            >
                              View Query Results
                            </Button>
                          </Box>
                        )}
                      </Box>
                    )}

                    {/* Submission Notes */}
                    {selectedEvidence.submission_notes && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Submission Notes
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                          <Typography variant="body2">
                            {selectedEvidence.submission_notes}
                          </Typography>
                        </Paper>
                      </Box>
                    )}

                    {/* Validation Results */}
                    {selectedEvidence.validation_results && selectedEvidence.validation_results.length > 0 && (
                      <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography variant="subtitle2">
                            Validation Results ({selectedEvidence.validation_results.length})
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <List>
                            {selectedEvidence.validation_results.map((result, index) => (
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

                    {/* Overall Validation Status */}
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Overall Validation Status
                      </Typography>
                      <Box display="flex" alignItems="center" gap={2}>
                        <Chip
                          icon={getStatusIcon(selectedEvidence.validation_status)}
                          label={selectedEvidence.validation_status}
                          color={getStatusColor(selectedEvidence.validation_status) as any}
                        />
                        {selectedEvidence.validation_notes && (
                          <Typography variant="body2" color="text.secondary">
                            {selectedEvidence.validation_notes}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent>
                  <Typography variant="body1" color="text.secondary" textAlign="center">
                    Select evidence from the list to view details
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Grid>
        </Grid>
      ) : (
        <Alert severity="info">
          No evidence pending review for this phase.
        </Alert>
      )}

      {/* Decision Dialog */}
      <Dialog
        open={showDecisionDialog}
        onClose={() => setShowDecisionDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Submit Evidence Decision
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Decision</InputLabel>
              <Select
                value={decision}
                onChange={(e) => setDecision(e.target.value as any)}
              >
                <MenuItem value="approved">
                  <Box display="flex" alignItems="center" gap={1}>
                    <ThumbUpIcon color="success" />
                    Approve
                  </Box>
                </MenuItem>
                <MenuItem value="rejected">
                  <Box display="flex" alignItems="center" gap={1}>
                    <ThumbDownIcon color="error" />
                    Reject
                  </Box>
                </MenuItem>
                <MenuItem value="requires_revision">
                  <Box display="flex" alignItems="center" gap={1}>
                    <WarningIcon color="warning" />
                    Requires Revision
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Decision Notes"
              multiline
              rows={4}
              value={decisionNotes}
              onChange={(e) => setDecisionNotes(e.target.value)}
              placeholder="Provide detailed feedback about your decision..."
              fullWidth
              required
            />

            {decision === 'requires_revision' && (
              <>
                <FormControlLabel
                  control={
                    <Switch
                      checked={requiresResubmission}
                      onChange={(e) => setRequiresResubmission(e.target.checked)}
                    />
                  }
                  label="Requires Resubmission"
                />

                {requiresResubmission && (
                  <TextField
                    label="Resubmission Deadline"
                    type="date"
                    value={resubmissionDeadline}
                    onChange={(e) => setResubmissionDeadline(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    fullWidth
                  />
                )}

                <TextField
                  label="Follow-up Instructions"
                  multiline
                  rows={3}
                  value={followUpInstructions}
                  onChange={(e) => setFollowUpInstructions(e.target.value)}
                  placeholder="Provide specific instructions for revision..."
                  fullWidth
                />
              </>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDecisionDialog(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmitDecision}
            disabled={!decisionNotes.trim() || submitDecisionMutation.isPending}
            color={getDecisionColor(decision) as any}
          >
            {submitDecisionMutation.isPending ? 'Submitting...' : 'Submit Decision'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Query Results Dialog */}
      <Dialog
        open={showQueryResults}
        onClose={() => setShowQueryResults(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Query Results Preview</DialogTitle>
        <DialogContent>
          {queryResults.length > 0 && (
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {Object.keys(queryResults[0]).map((key) => (
                      <TableCell key={key}>{key}</TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {queryResults.slice(0, 10).map((row, index) => (
                    <TableRow key={index}>
                      {Object.values(row).map((value: any, cellIndex) => (
                        <TableCell key={cellIndex}>
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
          {queryResults.length > 10 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Showing first 10 records of {queryResults.length} total results
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowQueryResults(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TesterEvidenceReview;