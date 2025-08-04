import React, { useState, useEffect } from 'react';
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
  Grid,
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
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Container
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Edit as RequestChangesIcon,
  History as HistoryIcon,
  Info as InfoIcon,
  Assignment as AssignmentIcon,
  Science as ScienceIcon,
  CloudUpload as UploadIcon,
  Visibility as ViewIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  CheckCircleOutline,
  HighlightOff,
  Warning
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import apiClient from '../../api/client';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';
import { DynamicActivityCards } from '../../components/phase/DynamicActivityCards';

interface SampleSet {
  set_id: string;
  set_name: string;
  description: string;
  generation_method: string;
  sample_type: string;
  status: string;
  target_sample_size: number;
  actual_sample_size: number;
  quality_score: number;
  version_number: number;
  is_latest_version: boolean;
  created_at: string;
  created_by_name?: string;
  generation_rationale?: string;
  approval_notes?: string;
}

interface SampleRecord {
  record_id: string;
  sample_identifier: string;
  primary_key_value: string;
  sample_data: Record<string, any>;
  risk_score?: number;
  validation_status?: string;
  selection_rationale?: string;
  approval_status?: string;
}

interface ApprovalHistory {
  approval_id: string;
  approval_step: string;
  decision: string;
  approved_by_name: string;
  approved_at: string;
  feedback?: string;
  version_number?: number;
}

const SampleReviewPage: React.FC = () => {
  const { cycleId, reportId, setId } = useParams<{ cycleId: string; reportId: string; setId: string }>();
  const { user } = useAuth();
  const { showToast } = useNotifications();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [sampleSet, setSampleSet] = useState<SampleSet | null>(null);
  const [samples, setSamples] = useState<SampleRecord[]>([]);
  const [approvalHistory, setApprovalHistory] = useState<ApprovalHistory[]>([]);
  const [versionHistory, setVersionHistory] = useState<any[]>([]);
  const [approvalStatus, setApprovalStatus] = useState<any>(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [showHistoryDialog, setShowHistoryDialog] = useState(false);
  const [approvalDecision, setApprovalDecision] = useState<'approve' | 'reject' | 'request_changes'>('approve');
  const [feedback, setFeedback] = useState('');
  const [requestedChanges, setRequestedChanges] = useState<string[]>([]);
  const [selectedSamples, setSelectedSamples] = useState<Set<string>>(new Set());
  const [individualApprovals, setIndividualApprovals] = useState<Record<string, string>>({});

  const cycleIdNum = parseInt(cycleId || '0');
  const reportIdNum = parseInt(reportId || '0');
  
  const { data: unifiedPhaseStatus, isLoading: statusLoading, refetch: refetchStatus } = usePhaseStatus('Sample Selection', cycleIdNum, reportIdNum);

  useEffect(() => {
    if (cycleIdNum && reportIdNum && setId) {
      loadSampleSetData();
      checkApprovalStatus();
    }
  }, [cycleIdNum, reportIdNum, setId]);

  const loadSampleSetData = async () => {
    try {
      setLoading(true);

      // Load sample set details using version_id as setId
      const setResponse = await apiClient.get(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/sample-review/${setId}`);
      setSampleSet(setResponse.data);

      // Samples are already included in the review response
      setSamples(setResponse.data.samples || []);

      // TODO: Add approval history and version history endpoints if needed
      setApprovalHistory([]);
      setVersionHistory([]);

    } catch (error: any) {
      console.error('Error loading sample set data:', error);
      showToast('error', 'Failed to load sample set details');
    } finally {
      setLoading(false);
    }
  };

  const checkApprovalStatus = async () => {
    try {
      // Check if already approved based on sample set status
      const response = { data: { can_approve: sampleSet?.status === 'pending_approval' } };
      setApprovalStatus(response.data);
    } catch (error) {
      console.error('Error checking approval status:', error);
    }
  };

  const handleApproval = async () => {
    try {
      const endpoint = `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/sample-review/${setId}/submit`;
      
      let decision = '';
      if (approvalDecision === 'approve') decision = 'Approved';
      else if (approvalDecision === 'reject') decision = 'Rejected';
      else decision = 'Request Changes';

      const response = await apiClient.post(endpoint, {
        approval_decision: decision,
        feedback: feedback,
        requested_changes: approvalDecision === 'request_changes' ? requestedChanges : [],
        conditional_approval: false,
        approval_conditions: []
      });

      showToast('success', `Sample set ${approvalDecision === 'approve' ? 'approved' : approvalDecision === 'reject' ? 'rejected' : 'sent back for revision'} successfully!`);
      setShowApprovalDialog(false);
      
      // Reload data and check approval status
      await loadSampleSetData();
      await checkApprovalStatus();
      refetchStatus();
      
    } catch (error: any) {
      console.error('Error processing approval:', error);
      showToast('error', error.response?.data?.detail || 'Failed to process approval');
    }
  };

  const handleIndividualSampleApproval = async () => {
    try {
      const sampleApprovals = Array.from(selectedSamples).map(sampleId => ({
        sample_id: sampleId,
        decision: individualApprovals[sampleId] || 'Approved',
        feedback: '',
        change_requests: []
      }));

      // Convert to the format expected by our endpoint
      const sampleDecisions: Record<string, any> = {};
      sampleApprovals.forEach((approval: any) => {
        sampleDecisions[approval.sample_id] = {
          decision: approval.decision.toLowerCase().replace(' ', '_'),
          notes: approval.feedback || ''
        };
      });

      await apiClient.post(
        `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/sample-review/${setId}/submit`,
        {
          decision: approvalDecision === 'approve' ? 'approved' : 
                   approvalDecision === 'reject' ? 'rejected' : 'revision_required',
          feedback: feedback,
          sample_decisions: sampleDecisions
        }
      );

      showToast('success', 'Individual sample approvals processed successfully!');
      await loadSampleSetData();
      refetchStatus();
      
    } catch (error: any) {
      console.error('Error approving individual samples:', error);
      showToast('error', 'Failed to process individual sample approvals');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Approved': return 'success';
      case 'Rejected': return 'error';
      case 'Pending Approval': return 'warning';
      case 'Revision Required': return 'warning';
      case 'Draft': return 'default';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
      </Box>
    );
  }

  if (!sampleSet) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Sample set not found</Alert>
      </Box>
    );
  }

  const canApprove = approvalStatus?.can_approve && user?.role === 'Report Owner';

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Sample Set Review
      </Typography>

      {/* Approval Status Alert */}
      {approvalStatus?.has_decision && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Decision Already Made
          </Typography>
          <Typography variant="body2">
            This sample set version has already been {approvalStatus.latest_decision?.decision?.toLowerCase()}.
            {approvalStatus.latest_decision?.decision === 'Request Changes' && 
              ' The tester can create a new version with improvements and resubmit for approval.'}
          </Typography>
        </Alert>
      )}

      {/* Sample Set Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 8 }}>
              <Typography variant="h6" gutterBottom>
                {sampleSet.set_name}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {sampleSet.description}
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
                <Chip 
                  label={sampleSet.status} 
                  color={getStatusColor(sampleSet.status)}
                  size="small"
                />
                <Chip 
                  label={`Version ${sampleSet.version_number}`}
                  variant="outlined"
                  size="small"
                />
                <Chip 
                  icon={<ScienceIcon />}
                  label={sampleSet.generation_method}
                  size="small"
                />
                <Chip 
                  icon={<AssessmentIcon />}
                  label={`Quality: ${Math.round((sampleSet.quality_score || 0) * 100)}%`}
                  size="small"
                  color="primary"
                />
              </Box>
            </Grid>
            
            <Grid size={{ xs: 12, md: 4 }}>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Sample Count
                  </Typography>
                  <Typography variant="h6">
                    {sampleSet.actual_sample_size} samples
                  </Typography>
                </Box>
                
                {sampleSet.created_by_name && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Created By
                    </Typography>
                    <Typography variant="body1">
                      {sampleSet.created_by_name}
                    </Typography>
                  </Box>
                )}
                
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Created Date
                  </Typography>
                  <Typography variant="body1">
                    {new Date(sampleSet.created_at).toLocaleDateString()}
                  </Typography>
                </Box>
              </Stack>
            </Grid>
          </Grid>

          {/* Action Buttons */}
          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            {canApprove && (
              <>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<ApproveIcon />}
                  onClick={() => {
                    setApprovalDecision('approve');
                    setShowApprovalDialog(true);
                  }}
                >
                  Approve
                </Button>
                <Button
                  variant="contained"
                  color="warning"
                  startIcon={<RequestChangesIcon />}
                  onClick={() => {
                    setApprovalDecision('request_changes');
                    setShowApprovalDialog(true);
                  }}
                >
                  Request Changes
                </Button>
                <Button
                  variant="contained"
                  color="error"
                  startIcon={<RejectIcon />}
                  onClick={() => {
                    setApprovalDecision('reject');
                    setShowApprovalDialog(true);
                  }}
                >
                  Reject
                </Button>
              </>
            )}
            
            <Button
              variant="outlined"
              startIcon={<HistoryIcon />}
              onClick={() => setShowHistoryDialog(true)}
            >
              Version History
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Generation Rationale */}
      {sampleSet.generation_rationale && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Generation Rationale
            </Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
              {sampleSet.generation_rationale}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Sample Preview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Sample Preview (First 10)
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Sample ID</TableCell>
                  <TableCell>Primary Key</TableCell>
                  <TableCell>Risk Score</TableCell>
                  <TableCell>Validation Status</TableCell>
                  <TableCell>Sample Data</TableCell>
                  {canApprove && <TableCell>Individual Decision</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {samples.slice(0, 10).map((sample) => (
                  <TableRow key={sample.record_id}>
                    <TableCell>{sample.sample_identifier}</TableCell>
                    <TableCell>{sample.primary_key_value}</TableCell>
                    <TableCell>
                      {sample.risk_score ? (
                        <Chip 
                          label={sample.risk_score.toFixed(2)}
                          size="small"
                          color={sample.risk_score > 0.7 ? 'error' : sample.risk_score > 0.4 ? 'warning' : 'success'}
                        />
                      ) : '-'}
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={sample.validation_status || 'Unknown'}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Tooltip title={JSON.stringify(sample.sample_data, null, 2)}>
                        <IconButton size="small">
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                    {canApprove && (
                      <TableCell>
                        <FormControl size="small" sx={{ minWidth: 120 }}>
                          <Select
                            value={individualApprovals[sample.sample_identifier] || ''}
                            onChange={(e) => {
                              setIndividualApprovals({
                                ...individualApprovals,
                                [sample.sample_identifier]: e.target.value
                              });
                              setSelectedSamples(new Set(Array.from(selectedSamples).concat(sample.sample_identifier)));
                            }}
                          >
                            <MenuItem value="">-</MenuItem>
                            <MenuItem value="Approved">Approve</MenuItem>
                            <MenuItem value="Rejected">Reject</MenuItem>
                            <MenuItem value="Needs Changes">Needs Changes</MenuItem>
                          </Select>
                        </FormControl>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {samples.length > 10 && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Showing 10 of {samples.length} samples
            </Typography>
          )}
        </CardContent>
      </Card>

      {/* Approval History */}
      {approvalHistory.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Approval History
            </Typography>
            <List>
              {approvalHistory.map((history, index) => (
                <ListItem key={history.approval_id} divider={index < approvalHistory.length - 1}>
                  <ListItemIcon>
                    {history.decision === 'Approved' ? (
                      <CheckCircleOutline color="success" />
                    ) : history.decision === 'Rejected' ? (
                      <HighlightOff color="error" />
                    ) : (
                      <Warning color="warning" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={`${history.decision} by ${history.approved_by_name}`}
                    secondary={
                      <>
                        {new Date(history.approved_at).toLocaleString()}
                        {history.feedback && <><br />{history.feedback}</>}
                      </>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Approval Dialog */}
      <Dialog open={showApprovalDialog} onClose={() => setShowApprovalDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {approvalDecision === 'approve' ? 'Approve Sample Set' : 
           approvalDecision === 'reject' ? 'Reject Sample Set' : 
           'Request Changes'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <Alert severity={
              approvalDecision === 'approve' ? 'success' : 
              approvalDecision === 'reject' ? 'error' : 
              'warning'
            }>
              {approvalDecision === 'approve' && 
                'Approving this sample set will allow the testing phase to proceed.'}
              {approvalDecision === 'reject' && 
                'Rejecting this sample set will require the tester to generate new samples.'}
              {approvalDecision === 'request_changes' && 
                'The tester will need to address your feedback and resubmit for approval.'}
            </Alert>
            
            <TextField
              label="Feedback"
              multiline
              rows={4}
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              fullWidth
              required
              helperText="Provide detailed feedback for the tester"
            />
            
            {approvalDecision === 'request_changes' && (
              <TextField
                label="Requested Changes"
                multiline
                rows={3}
                value={requestedChanges.join('\n')}
                onChange={(e) => setRequestedChanges(e.target.value.split('\n').filter(Boolean))}
                fullWidth
                helperText="Enter each requested change on a new line"
              />
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowApprovalDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleApproval} 
            variant="contained" 
            color={
              approvalDecision === 'approve' ? 'success' : 
              approvalDecision === 'reject' ? 'error' : 
              'warning'
            }
            disabled={!feedback}
          >
            Confirm {approvalDecision === 'approve' ? 'Approval' : 
                     approvalDecision === 'reject' ? 'Rejection' : 
                     'Changes Request'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Version History Dialog */}
      <Dialog open={showHistoryDialog} onClose={() => setShowHistoryDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Version History</DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Version</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Samples</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Notes</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {versionHistory.map((version) => (
                  <TableRow key={version.set_id}>
                    <TableCell>
                      <Chip 
                        label={`v${version.version_number}`}
                        size="small"
                        color={version.is_latest ? 'primary' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={version.status}
                        size="small"
                        color={getStatusColor(version.status)}
                      />
                    </TableCell>
                    <TableCell>{version.sample_count}</TableCell>
                    <TableCell>{new Date(version.version_created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {version.version_notes || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {version.set_id !== setId && (
                        <Button
                          size="small"
                          onClick={() => navigate(`/cycles/${cycleId}/reports/${reportId}/sample-review/${version.set_id}`)}
                        >
                          View
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHistoryDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SampleReviewPage;