import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  LinearProgress,
  Chip,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Divider,
  Checkbox,
  FormControl,
  Select,
  MenuItem,
  Container,
  TablePagination,
  Collapse,
  useTheme
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Edit as RequestChangesIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Assignment as AssignmentIcon,
  AccountTree as AccountTreeIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircleOutline,
  HighlightOff,
  ThumbUp,
  ThumbDown,
  EditNote,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import apiClient from '../../api/client';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';

interface Sample {
  sample_id: string;
  sample_identifier: string;
  primary_attribute_name: string;
  primary_attribute_value: string;
  sample_category: string;
  sample_data: any;
  data_columns: Record<string, any>;
  tester_decision: 'approved' | 'rejected' | 'pending';
  tester_decision_notes?: string;
  tester_decision_at?: string;
  tester_decision_by?: string;
  report_owner_decision?: 'approved' | 'rejected' | 'revision_required' | 'pending' | null;
  report_owner_decision_notes?: string;
  dq_rule_id?: string;
  dq_rule_result?: string;
  lob_assignment?: string;
  attribute_focus?: string;
  rationale?: string;
  generated_by?: string;
}

interface SampleReviewData {
  set_id: string;
  version_number: number;
  created_at: string;
  submitted_at: string;
  submission_notes?: string;
  status: string;
  report_name: string;
  total_samples: number;
  samples: Sample[];
}

const ReportOwnerSampleReview: React.FC = () => {
  const { cycleId, reportId, setId: versionId } = useParams<{ cycleId: string; reportId: string; setId: string }>();
  const { user } = useAuth();
  const { showToast } = useNotifications();
  const navigate = useNavigate();
  const theme = useTheme();

  const cycleIdNum = parseInt(cycleId || '0');
  const reportIdNum = parseInt(reportId || '0');

  // State
  const [loading, setLoading] = useState(true);
  const [reviewData, setReviewData] = useState<SampleReviewData | null>(null);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [individualDecisions, setIndividualDecisions] = useState<Record<string, string>>({});
  const [individualNotes, setIndividualNotes] = useState<Record<string, string>>({});
  const [bulkSelectedSamples, setBulkSelectedSamples] = useState<string[]>([]);
  const [overallDecision, setOverallDecision] = useState<'approved' | 'rejected' | 'revision_required' | ''>('');
  const [overallFeedback, setOverallFeedback] = useState('');
  const [confirmDialog, setConfirmDialog] = useState(false);
  const [availableLOBs, setAvailableLOBs] = useState<any[]>([]);
  const [sampleLOBs, setSampleLOBs] = useState<Record<string, string>>({});
  const [expandedSamples, setExpandedSamples] = useState<Set<string>>(new Set());
  const [primaryKeyColumns, setPrimaryKeyColumns] = useState<string[]>([]);
  const [viewSampleDialog, setViewSampleDialog] = useState<{ open: boolean; sample: Sample | null }>({
    open: false,
    sample: null
  });
  
  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const { data: unifiedPhaseStatus, isLoading: statusLoading, refetch: refetchStatus } = usePhaseStatus('Sample Selection', cycleIdNum, reportIdNum);

  useEffect(() => {
    if (cycleIdNum && reportIdNum && versionId) {
      loadReviewData();
      loadAvailableLOBs();
    }
  }, [cycleIdNum, reportIdNum, versionId]);

  const loadReviewData = async () => {
    try {
      setLoading(true);

      // Load sample review data
      const response = await apiClient.get(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/sample-review/${versionId}`);
      const data = response.data;
      
      setReviewData(data);
      setSamples(data.samples || []);
      
      // Extract primary key columns from first sample
      if (data.samples.length > 0 && data.samples[0].sample_data) {
        const sampleData = data.samples[0].sample_data;
        // Common PK field names - could be made configurable
        const potentialPKFields = ['Customer ID', 'Reference Number', 'Bank ID', 'Period ID', 
                                  'customer_id', 'reference_number', 'bank_id', 'period_id'];
        const pkCols = Object.keys(sampleData).filter(key => 
          potentialPKFields.some(pk => pk.toLowerCase() === key.toLowerCase())
        );
        setPrimaryKeyColumns(pkCols);
      }
      
      // Initialize individual decisions and LOB assignments
      const decisions: Record<string, string> = {};
      const notes: Record<string, string> = {};
      const lobAssignments: Record<string, string> = {};
      
      data.samples.forEach((sample: Sample) => {
        if (sample.report_owner_decision && sample.report_owner_decision !== 'pending') {
          decisions[sample.sample_id] = sample.report_owner_decision;
        }
        if (sample.report_owner_decision_notes) {
          notes[sample.sample_id] = sample.report_owner_decision_notes;
        }
        if (sample.lob_assignment) {
          lobAssignments[sample.sample_id] = sample.lob_assignment;
        }
      });
      
      setIndividualDecisions(decisions);
      setIndividualNotes(notes);
      setSampleLOBs(lobAssignments);
      
    } catch (error: any) {
      console.error('Error loading review data:', error);
      showToast('error', 'Failed to load sample review data');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableLOBs = async () => {
    try {
      const response = await apiClient.get(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/available-lobs`);
      setAvailableLOBs(response.data.available_lobs || []);
    } catch (error) {
      console.error('Error loading LOBs:', error);
    }
  };

  const handleIndividualDecision = (sampleId: string, decision: 'approved' | 'rejected') => {
    setIndividualDecisions(prev => ({ ...prev, [sampleId]: decision }));
  };

  const handleIndividualNote = (sampleId: string, note: string) => {
    setIndividualNotes(prev => ({ ...prev, [sampleId]: note }));
  };

  const handleBulkDecision = (decision: 'approved' | 'rejected') => {
    const decisions: Record<string, string> = {};
    bulkSelectedSamples.forEach(sampleId => {
      decisions[sampleId] = decision;
    });
    setIndividualDecisions(prev => ({ ...prev, ...decisions }));
    setBulkSelectedSamples([]);
    showToast('success', `${bulkSelectedSamples.length} samples marked as ${decision}`);
  };

  const handleSubmitReview = async () => {
    try {
      // Prepare sample decisions
      const sampleDecisions: Record<string, any> = {};
      Object.keys(individualDecisions).forEach(sampleId => {
        sampleDecisions[sampleId] = {
          decision: individualDecisions[sampleId],
          notes: individualNotes[sampleId] || ''
        };
      });

      // Get assignment ID from URL params or context
      const assignmentId = new URLSearchParams(window.location.search).get('assignmentId');

      await apiClient.post(
        `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/sample-review/${versionId}/submit`,
        {
          decision: overallDecision,
          feedback: overallFeedback,
          sample_decisions: sampleDecisions,
          assignment_id: assignmentId
        }
      );

      showToast('success', 'Review submitted successfully!');
      setConfirmDialog(false);
      
      // Navigate back to dashboard or assignments
      navigate(`/cycles/${cycleId}/reports/${reportId}`);
      
    } catch (error: any) {
      console.error('Error submitting review:', error);
      showToast('error', 'Failed to submit review');
    }
  };

  const toggleSampleExpansion = (sampleId: string) => {
    setExpandedSamples(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sampleId)) {
        newSet.delete(sampleId);
      } else {
        newSet.add(sampleId);
      }
      return newSet;
    });
  };

  const getDecisionIcon = (decision?: string) => {
    switch (decision) {
      case 'approved':
        return <CheckCircleOutline sx={{ color: 'success.main', fontSize: 20 }} />;
      case 'rejected':
        return <HighlightOff sx={{ color: 'error.main', fontSize: 20 }} />;
      case 'revision_required':
        return <EditNote sx={{ color: 'warning.main', fontSize: 20 }} />;
      default:
        return null;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category.toUpperCase()) {
      case 'CLEAN':
        return 'success';
      case 'ANOMALY':
        return 'warning';
      case 'BOUNDARY':
        return 'info';
      default:
        return 'default';
    }
  };
  
  const getStatusChip = (sample: Sample) => {
    if (sample.tester_decision === 'approved') {
      return <Chip label="Included" size="small" color="success" />;
    } else if (sample.tester_decision === 'rejected') {
      return <Chip label="Excluded" size="small" color="error" />;
    }
    return <Chip label="Pending" size="small" color="default" />;
  };
  
  const getTesterDecisionDisplay = (sample: Sample) => {
    if (sample.tester_decision === 'approved') {
      return (
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <CheckCircleOutline sx={{ fontSize: 16, color: 'success.main' }} />
          <Typography variant="caption" color="success.main">Approved</Typography>
        </Stack>
      );
    } else if (sample.tester_decision === 'rejected') {
      return (
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <HighlightOff sx={{ fontSize: 16, color: 'error.main' }} />
          <Typography variant="caption" color="error.main">Rejected</Typography>
        </Stack>
      );
    }
    return <Typography variant="caption" color="text.secondary">Pending</Typography>;
  };

  if (loading || statusLoading) {
    return (
      <Container maxWidth="xl">
        <Box sx={{ mt: 4 }}>
          <LinearProgress />
          <Typography variant="h6" sx={{ mt: 2, textAlign: 'center' }}>
            Loading sample review...
          </Typography>
        </Box>
      </Container>
    );
  }

  if (!reviewData) {
    return (
      <Container maxWidth="xl">
        <Alert severity="error" sx={{ mt: 4 }}>
          Failed to load sample review data
        </Alert>
      </Container>
    );
  }

  const paginatedSamples = samples.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 3 }}>
        {/* Header */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" component="h1">
                Sample Review - {reviewData.report_name}
              </Typography>
              <Chip
                label={`Version ${reviewData.version_number}`}
                color="primary"
                icon={<AccountTreeIcon />}
              />
            </Box>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="caption" color="text.secondary">Cycle</Typography>
                <Typography variant="body1">{cycleId}</Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="caption" color="text.secondary">Report</Typography>
                <Typography variant="body1">{reviewData.report_name}</Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="caption" color="text.secondary">Submitted At</Typography>
                <Typography variant="body1">
                  {reviewData.submitted_at ? new Date(reviewData.submitted_at).toLocaleString() : 'Not submitted'}
                </Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="caption" color="text.secondary">Total Samples</Typography>
                <Typography variant="body1">{reviewData.total_samples}</Typography>
              </Box>
            </Box>

            {reviewData.submission_notes && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Submission Notes:</strong> {reviewData.submission_notes}
                </Typography>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Review Summary */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Review Summary
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
              <Box sx={{ flex: '1 1 200px' }}>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <CheckCircleOutline sx={{ color: 'success.main' }} />
                  <Typography>
                    Approved: {samples.filter(s => individualDecisions[s.sample_id] === 'approved').length}
                  </Typography>
                </Stack>
              </Box>
              <Box sx={{ flex: '1 1 200px' }}>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <HighlightOff sx={{ color: 'error.main' }} />
                  <Typography>
                    Rejected: {samples.filter(s => individualDecisions[s.sample_id] === 'rejected').length}
                  </Typography>
                </Stack>
              </Box>
              <Box sx={{ flex: '1 1 200px' }}>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <InfoIcon sx={{ color: 'info.main' }} />
                  <Typography>
                    Pending: {samples.filter(s => !individualDecisions[s.sample_id]).length}
                  </Typography>
                </Stack>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Bulk Actions */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              <Typography variant="subtitle1">Bulk Actions:</Typography>
              <Button
                variant="contained"
                size="small"
                color="success"
                startIcon={<ThumbUp />}
                onClick={() => handleBulkDecision('approved')}
                disabled={bulkSelectedSamples.length === 0}
              >
                Bulk Approve ({bulkSelectedSamples.length})
              </Button>
              <Button
                variant="outlined"
                size="small"
                color="error"
                startIcon={<ThumbDown />}
                onClick={() => handleBulkDecision('rejected')}
                disabled={bulkSelectedSamples.length === 0}
              >
                Bulk Reject ({bulkSelectedSamples.length})
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Samples Table with horizontal scroll */}
        <Card>
          <CardContent>
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                Tip: Scroll horizontally to view all columns →
              </Typography>
            </Alert>
            <Box 
              sx={{ 
                width: '100%', 
                overflowX: 'scroll', 
                overflowY: 'hidden',
                pb: 1,
                '&::-webkit-scrollbar': {
                  height: 18,
                  backgroundColor: '#f5f5f5',
                },
                '&::-webkit-scrollbar-track': {
                  backgroundColor: '#f5f5f5',
                  border: '1px solid #e0e0e0',
                },
                '&::-webkit-scrollbar-thumb': {
                  backgroundColor: '#888',
                  borderRadius: 9,
                  border: '2px solid #f5f5f5',
                  '&:hover': {
                    backgroundColor: '#555',
                  },
                },
              }}
            >
            <TableContainer 
              component={Paper}
              sx={{ 
                width: 'max-content',
                maxHeight: '70vh',
                overflowY: 'auto',
                overflowX: 'visible'
              }}>
              <Table stickyHeader size="small" sx={{ minWidth: 1900 }}>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        indeterminate={bulkSelectedSamples.length > 0 && bulkSelectedSamples.length < samples.length}
                        checked={samples.length > 0 && bulkSelectedSamples.length === samples.length}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setBulkSelectedSamples(samples.map(s => s.sample_id));
                          } else {
                            setBulkSelectedSamples([]);
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Sample ID</TableCell>
                    {/* Dynamic PK columns */}
                    {primaryKeyColumns.map((pkCol) => (
                      <TableCell key={pkCol} sx={{ fontWeight: 'bold', minWidth: 120 }}>{pkCol}</TableCell>
                    ))}
                    <TableCell sx={{ fontWeight: 'bold', minWidth: 200 }}>Attribute</TableCell>
                    <TableCell sx={{ fontWeight: 'bold', minWidth: 80 }}>Category</TableCell>
                    <TableCell sx={{ fontWeight: 'bold', minWidth: 250 }}>Rationale</TableCell>
                    <TableCell sx={{ fontWeight: 'bold', minWidth: 80 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>Tester</TableCell>
                    <TableCell sx={{ fontWeight: 'bold', minWidth: 60 }}>LOB</TableCell>
                    <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>Tester Decision</TableCell>
                    <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>Report Owner Decision</TableCell>
                    <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedSamples.map((sample) => (
                    <React.Fragment key={sample.sample_id}>
                      <TableRow>
                        <TableCell padding="checkbox">
                          <Checkbox
                            checked={bulkSelectedSamples.includes(sample.sample_id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setBulkSelectedSamples(prev => [...prev, sample.sample_id]);
                              } else {
                                setBulkSelectedSamples(prev => prev.filter(id => id !== sample.sample_id));
                              }
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace" sx={{ fontSize: '0.75rem' }}>
                            {sample.sample_id}
                          </Typography>
                        </TableCell>
                        {/* Dynamic PK values */}
                        {primaryKeyColumns.map((pkCol) => (
                          <TableCell key={pkCol}>
                            <Typography variant="body2" fontFamily="monospace" sx={{ fontSize: '0.75rem' }}>
                              {sample.sample_data?.[pkCol] || '-'}
                            </Typography>
                          </TableCell>
                        ))}
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
                            {sample.attribute_focus ? (
                              sample.sample_data && sample.sample_data[sample.attribute_focus] !== undefined ? 
                                `${sample.attribute_focus} (${sample.sample_data[sample.attribute_focus]})` : 
                                sample.attribute_focus
                            ) : '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={sample.sample_category || 'Unknown'}
                            size="small"
                            color={getCategoryColor(sample.sample_category)}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontSize: '0.75rem',
                              maxWidth: 250,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              display: 'block'
                            }}
                            title={sample.rationale || ''}
                          >
                            {sample.rationale || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {getStatusChip(sample)}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption">
                            {sample.tester_decision_by || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {sample.lob_assignment ? (
                            <Chip label={sample.lob_assignment} size="small" color="primary" />
                          ) : (
                            <Typography variant="body2" color="text.secondary">-</Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          {getTesterDecisionDisplay(sample)}
                        </TableCell>
                        <TableCell>
                          <Stack direction="row" alignItems="center" spacing={1}>
                            {getDecisionIcon(individualDecisions[sample.sample_id])}
                            <Typography variant="caption">
                              {individualDecisions[sample.sample_id] || 'Pending'}
                            </Typography>
                          </Stack>
                        </TableCell>
                        <TableCell>
                          <Stack direction="row" spacing={1}>
                            <Tooltip title="Approve">
                              <IconButton
                                size="small"
                                color={individualDecisions[sample.sample_id] === 'approved' ? 'success' : 'default'}
                                onClick={() => handleIndividualDecision(sample.sample_id, 'approved')}
                              >
                                <ThumbUp fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Reject">
                              <IconButton
                                size="small"
                                color={individualDecisions[sample.sample_id] === 'rejected' ? 'error' : 'default'}
                                onClick={() => handleIndividualDecision(sample.sample_id, 'rejected')}
                              >
                                <ThumbDown fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="View Sample Data">
                              <IconButton 
                                size="small"
                                onClick={() => setViewSampleDialog({ open: true, sample })}
                              >
                                <VisibilityIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Stack>
                        </TableCell>
                      </TableRow>
                      
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            </Box>
            
            <TablePagination
              component="div"
              count={samples.length}
              page={page}
              onPageChange={(_, newPage) => setPage(newPage)}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
            />
          </CardContent>
        </Card>

        {/* Overall Review Section */}
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Overall Review Decision
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box>
                <FormControl fullWidth>
                  <Typography variant="subtitle2" gutterBottom>
                    Overall Decision *
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant={overallDecision === 'approved' ? 'contained' : 'outlined'}
                      color="success"
                      onClick={() => setOverallDecision('approved')}
                      startIcon={<CheckCircleOutline />}
                    >
                      Approve All
                    </Button>
                    <Button
                      variant={overallDecision === 'rejected' ? 'contained' : 'outlined'}
                      color="error"
                      onClick={() => setOverallDecision('rejected')}
                      startIcon={<HighlightOff />}
                    >
                      Reject
                    </Button>
                    <Button
                      variant={overallDecision === 'revision_required' ? 'contained' : 'outlined'}
                      color="warning"
                      onClick={() => setOverallDecision('revision_required')}
                      startIcon={<EditNote />}
                    >
                      Request Changes
                    </Button>
                  </Box>
                </FormControl>
              </Box>
              
              <Box>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Overall Feedback"
                  value={overallFeedback}
                  onChange={(e) => setOverallFeedback(e.target.value)}
                  placeholder="Provide overall feedback for the tester..."
                  helperText="This feedback will help the tester understand what changes are needed"
                />
              </Box>
            </Box>

            <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                onClick={() => navigate(`/cycles/${cycleId}/reports/${reportId}`)}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                color="primary"
                onClick={() => setConfirmDialog(true)}
                disabled={!overallDecision}
                startIcon={<AssignmentIcon />}
              >
                Submit Review
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Confirmation Dialog */}
        <Dialog open={confirmDialog} onClose={() => setConfirmDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Confirm Review Submission</DialogTitle>
          <DialogContent>
            <Alert severity={overallDecision === 'approved' ? 'success' : overallDecision === 'rejected' ? 'error' : 'warning'} sx={{ mb: 2 }}>
              You are about to submit your review with an overall decision of: <strong>{overallDecision}</strong>
            </Alert>
            
            <Typography variant="body2" paragraph>
              Summary of individual sample decisions:
            </Typography>
            <Box sx={{ pl: 2 }}>
              <Typography variant="body2">
                • Approved: {samples.filter(s => individualDecisions[s.sample_id] === 'approved').length}
              </Typography>
              <Typography variant="body2">
                • Rejected: {samples.filter(s => individualDecisions[s.sample_id] === 'rejected').length}
              </Typography>
              <Typography variant="body2">
                • No Decision: {samples.filter(s => !individualDecisions[s.sample_id]).length}
              </Typography>
            </Box>
            
            {overallDecision === 'revision_required' && (
              <Alert severity="info" sx={{ mt: 2 }}>
                The tester will need to address your feedback and create a new version for re-review.
              </Alert>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setConfirmDialog(false)}>Cancel</Button>
            <Button onClick={handleSubmitReview} variant="contained" color="primary">
              Confirm & Submit
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
      
      {/* View Sample Data Dialog */}
      <Dialog 
        open={viewSampleDialog.open} 
        onClose={() => setViewSampleDialog({ open: false, sample: null })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Sample Data - {viewSampleDialog.sample?.sample_id}
        </DialogTitle>
        <DialogContent>
          {viewSampleDialog.sample && (
            <Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
                <Box sx={{ flex: '1 1 200px' }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Sample Category
                  </Typography>
                  <Chip 
                    label={viewSampleDialog.sample.sample_category || 'Unknown'} 
                    color={getCategoryColor(viewSampleDialog.sample.sample_category)}
                    size="small"
                    sx={{ mt: 0.5 }}
                  />
                </Box>
                <Box sx={{ flex: '1 1 300px' }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Attribute Focus
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500, mt: 0.5 }}>
                    {viewSampleDialog.sample.attribute_focus ? (
                      viewSampleDialog.sample.sample_data && viewSampleDialog.sample.sample_data[viewSampleDialog.sample.attribute_focus] !== undefined ? 
                        `${viewSampleDialog.sample.attribute_focus} (${viewSampleDialog.sample.sample_data[viewSampleDialog.sample.attribute_focus]})` : 
                        viewSampleDialog.sample.attribute_focus
                    ) : '-'}
                  </Typography>
                </Box>
              </Box>
              
              {viewSampleDialog.sample.rationale && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Selection Rationale
                  </Typography>
                  <Typography variant="body2" sx={{ fontStyle: 'italic', mt: 0.5 }}>
                    {viewSampleDialog.sample.rationale}
                  </Typography>
                </Box>
              )}
              
              {primaryKeyColumns.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                    Primary Key Values
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          {primaryKeyColumns.map((col) => (
                            <TableCell key={col} sx={{ fontWeight: 'bold' }}>{col}</TableCell>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          {primaryKeyColumns.map((col) => (
                            <TableCell key={col}>
                              <Typography variant="body2" fontFamily="monospace">
                                {viewSampleDialog.sample?.sample_data?.[col] || '-'}
                              </Typography>
                            </TableCell>
                          ))}
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
              
              {viewSampleDialog.sample.tester_decision_notes && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Tester Notes
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'info.50' }}>
                    <Typography variant="body2">{viewSampleDialog.sample.tester_decision_notes}</Typography>
                  </Paper>
                </Box>
              )}
              
              {viewSampleDialog.sample.dq_rule_id && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    DQ Rule Information
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'warning.50' }}>
                    <Typography variant="body2">Rule ID: {viewSampleDialog.sample.dq_rule_id}</Typography>
                    <Typography variant="body2">Result: {viewSampleDialog.sample.dq_rule_result || 'N/A'}</Typography>
                  </Paper>
                </Box>
              )}
              
              <Divider sx={{ my: 2 }} />
              
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  Sample Data:
                </Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <pre style={{ margin: 0, overflow: 'auto', maxHeight: '300px' }}>
                    {JSON.stringify(viewSampleDialog.sample.sample_data, null, 2)}
                  </pre>
                </Paper>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewSampleDialog({ open: false, sample: null })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ReportOwnerSampleReview;