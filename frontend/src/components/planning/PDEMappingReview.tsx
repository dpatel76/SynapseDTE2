import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Snackbar,
  LinearProgress,
  Tooltip,
  Avatar,
  AvatarGroup,
  Badge,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  ListItemSecondaryAction,
  FormControlLabel,
  Checkbox,
  Divider,
  CircularProgress,
  } from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  AccessTime as PendingIcon,
  Edit as EditIcon,
  Send as SendIcon,
  AutoFixHigh as AutoFixHighIcon,
  RateReview as ReviewIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../api/client';

interface ReviewStatus {
  total_mappings: number;
  pending: number;
  approved: number;
  rejected: number;
  needs_revision: number;
  not_submitted: number;
  auto_approved: number;
}

interface PDEMappingWithReview {
  id: number;
  pde_name: string;
  pde_code: string;
  attribute_name: string;
  llm_confidence_score?: number;
  mapping_confirmed_by_user: boolean;
  
  // Review information
  review_status?: 'pending' | 'approved' | 'rejected' | 'needs_revision';
  review_id?: number;
  submitted_at?: string;
  reviewed_at?: string;
  reviewed_by_name?: string;
  auto_approved: boolean;
  
  // Attribute details
  is_cde: boolean;
  is_primary_key: boolean;
  information_security_classification?: string;
  risk_score?: number;
}

interface ReviewHistory {
  id: number;
  action_type: string;
  action_by_name: string;
  action_at: string;
  previous_status?: string;
  new_status?: string;
  action_notes?: string;
}

export const PDEMappingReview: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const { user } = useAuth();
  const token = localStorage.getItem('token');
  const [reviewSummary, setReviewSummary] = useState<ReviewStatus | null>(null);
  const [mappings, setMappings] = useState<PDEMappingWithReview[]>([]);
  const [selectedMappings, setSelectedMappings] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [currentMapping, setCurrentMapping] = useState<PDEMappingWithReview | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [revisionRequested, setRevisionRequested] = useState('');
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [reviewHistory, setReviewHistory] = useState<ReviewHistory[]>([]);

  const isReportOwnerOrAbove = user?.role && ['REPORT_OWNER', 'REPORT_OWNER_EXECUTIVE', 'TEST_EXECUTIVE', 'ADMIN'].includes(user.role);

  // Load review summary
  const loadReviewSummary = async () => {
    try {
      // For now, since the summary endpoint doesn't exist, we'll skip it
      // TODO: Implement the summary endpoint in the backend
      setReviewSummary({
        total_mappings: 0,
        pending: 0,
        approved: 0,
        rejected: 0,
        needs_revision: 0,
        not_submitted: 0,
        auto_approved: 0,
      });
    } catch (err) {
      console.error('Error loading review summary:', err);
    }
  };

  // Load mappings with review status
  const loadMappings = async () => {
    try {
      setLoading(true);
      // Use apiClient which handles the base URL and auth properly
      const response = await apiClient.get(
        `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings`
      );
      setMappings(response.data?.mappings || []);
    } catch (err) {
      console.error('Error loading mappings:', err);
      setError('Failed to load PDE mappings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReviewSummary();
    loadMappings();
  }, [cycleId, reportId]);

  const handleSubmitForReview = async (mappingId: number) => {
    try {
      await axios.post(
        `/api/v1/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/${mappingId}/submit-for-review`,
        { review_notes: 'Submitted for review' },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setSuccess('Mapping submitted for review');
      loadReviewSummary();
      loadMappings();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit for review');
    }
  };

  const handleReviewMapping = (mapping: PDEMappingWithReview) => {
    setCurrentMapping(mapping);
    setReviewDialogOpen(true);
  };

  const handleSubmitReview = async (status: 'approved' | 'rejected' | 'needs_revision') => {
    if (!currentMapping) return;

    try {
      await axios.put(
        `/api/v1/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/${currentMapping.id}/review`,
        {
          review_status: status,
          review_notes: reviewNotes,
          revision_requested: status === 'needs_revision' ? revisionRequested : null,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      setSuccess(`Mapping ${status === 'approved' ? 'approved' : status === 'rejected' ? 'rejected' : 'sent for revision'}`);
      setReviewDialogOpen(false);
      setReviewNotes('');
      setRevisionRequested('');
      loadReviewSummary();
      loadMappings();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit review');
    }
  };

  const handleBulkAction = async (action: 'approve' | 'reject') => {
    if (selectedMappings.length === 0) {
      setError('Please select mappings to review');
      return;
    }

    try {
      await axios.post(
        `/api/v1/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/reviews/bulk`,
        {
          mapping_ids: selectedMappings,
          action: action,
          review_status: action === 'approve' ? 'approved' : 'rejected',
          review_notes: `Bulk ${action}`,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      setSuccess(`${selectedMappings.length} mappings ${action}d`);
      setSelectedMappings([]);
      loadReviewSummary();
      loadMappings();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to perform bulk action');
    }
  };

  const handleViewHistory = async (mappingId: number) => {
    try {
      const response = await axios.get(
        `/api/v1/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/${mappingId}/review-history`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setReviewHistory(response.data);
      setHistoryDialogOpen(true);
    } catch (err) {
      console.error('Error loading review history:', err);
      setError('Failed to load review history');
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircleIcon color="success" />;
      case 'rejected':
        return <CancelIcon color="error" />;
      case 'pending':
        return <PendingIcon color="warning" />;
      case 'needs_revision':
        return <EditIcon color="info" />;
      default:
        return <SendIcon color="action" />;
    }
  };

  const getStatusColor = (status?: string): any => {
    switch (status) {
      case 'approved':
        return 'success';
      case 'rejected':
        return 'error';
      case 'pending':
        return 'warning';
      case 'needs_revision':
        return 'info';
      default:
        return 'default';
    }
  };

  const filterMappingsByTab = () => {
    switch (tabValue) {
      case 0: // All
        return mappings;
      case 1: // Pending Review
        return mappings.filter(m => m.review_status === 'pending');
      case 2: // Approved
        return mappings.filter(m => m.review_status === 'approved');
      case 3: // Rejected
        return mappings.filter(m => m.review_status === 'rejected');
      case 4: // Not Submitted
        return mappings.filter(m => !m.review_status);
      default:
        return mappings;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        PDE Mapping Review & Approval
      </Typography>

      {/* Review Summary Cards */}
      {reviewSummary && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, md: 2 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4">{reviewSummary.total_mappings}</Typography>
                <Typography variant="body2" color="textSecondary">Total Mappings</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 2 }}>
            <Card sx={{ borderLeft: '4px solid #ff9800' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">{reviewSummary.pending}</Typography>
                <Typography variant="body2" color="textSecondary">Pending Review</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 2 }}>
            <Card sx={{ borderLeft: '4px solid #4caf50' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">{reviewSummary.approved}</Typography>
                <Typography variant="body2" color="textSecondary">Approved</Typography>
                {reviewSummary.auto_approved > 0 && (
                  <Chip
                    size="small"
                    label={`${reviewSummary.auto_approved} auto`}
                    icon={<AutoFixHighIcon />}
                    sx={{ mt: 1 }}
                  />
                )}
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 2 }}>
            <Card sx={{ borderLeft: '4px solid #f44336' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="error.main">{reviewSummary.rejected}</Typography>
                <Typography variant="body2" color="textSecondary">Rejected</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 2 }}>
            <Card sx={{ borderLeft: '4px solid #2196f3' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="info.main">{reviewSummary.needs_revision}</Typography>
                <Typography variant="body2" color="textSecondary">Needs Revision</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 2 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4">{reviewSummary.not_submitted}</Typography>
                <Typography variant="body2" color="textSecondary">Not Submitted</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Action Buttons */}
      {isReportOwnerOrAbove && selectedMappings.length > 0 && (
        <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color="success"
            startIcon={<CheckCircleIcon />}
            onClick={() => handleBulkAction('approve')}
          >
            Bulk Approve ({selectedMappings.length})
          </Button>
          <Button
            variant="contained"
            color="error"
            startIcon={<CancelIcon />}
            onClick={() => handleBulkAction('reject')}
          >
            Bulk Reject ({selectedMappings.length})
          </Button>
        </Box>
      )}

      {/* Tabs */}
      <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} sx={{ mb: 2 }}>
        <Tab label={`All (${mappings.length})`} />
        <Tab label={`Pending (${mappings.filter(m => m.review_status === 'pending').length})`} />
        <Tab label={`Approved (${mappings.filter(m => m.review_status === 'approved').length})`} />
        <Tab label={`Rejected (${mappings.filter(m => m.review_status === 'rejected').length})`} />
        <Tab label={`Not Submitted (${mappings.filter(m => !m.review_status).length})`} />
      </Tabs>

      {/* Mappings Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              {isReportOwnerOrAbove && (
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedMappings.length === filterMappingsByTab().length && filterMappingsByTab().length > 0}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedMappings(filterMappingsByTab().map(m => m.id));
                      } else {
                        setSelectedMappings([]);
                      }
                    }}
                  />
                </TableCell>
              )}
              <TableCell>PDE Name</TableCell>
              <TableCell>Attribute</TableCell>
              <TableCell>LLM Confidence</TableCell>
              <TableCell>Security Class</TableCell>
              <TableCell>Review Status</TableCell>
              <TableCell>Reviewer</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filterMappingsByTab().map((mapping) => (
              <TableRow key={mapping.id}>
                {isReportOwnerOrAbove && (
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedMappings.includes(mapping.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedMappings([...selectedMappings, mapping.id]);
                        } else {
                          setSelectedMappings(selectedMappings.filter(id => id !== mapping.id));
                        }
                      }}
                    />
                  </TableCell>
                )}
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      {mapping.pde_name}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {mapping.pde_code}
                    </Typography>
                    <Box display="flex" gap={0.5} mt={0.5}>
                      {mapping.is_cde && <Chip label="CDE" size="small" color="warning" />}
                      {mapping.is_primary_key && <Chip label="PK" size="small" color="primary" />}
                      {mapping.auto_approved && <Chip label="Auto" size="small" color="success" />}
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>{mapping.attribute_name}</TableCell>
                <TableCell>
                  {mapping.llm_confidence_score ? (
                    <Box display="flex" alignItems="center" gap={1}>
                      <LinearProgress
                        variant="determinate"
                        value={mapping.llm_confidence_score}
                        sx={{ width: 60, height: 8 }}
                        color={
                          mapping.llm_confidence_score >= 85 ? 'success' :
                          mapping.llm_confidence_score >= 70 ? 'warning' : 'error'
                        }
                      />
                      <Typography variant="caption">
                        {mapping.llm_confidence_score}%
                      </Typography>
                    </Box>
                  ) : (
                    '-'
                  )}
                </TableCell>
                <TableCell>
                  {mapping.information_security_classification ? (
                    <Chip
                      size="small"
                      label={mapping.information_security_classification}
                      icon={<SecurityIcon />}
                      sx={{
                        backgroundColor: 
                          mapping.information_security_classification === 'HRCI' ? '#d32f2f' :
                          mapping.information_security_classification === 'Confidential' ? '#f57c00' :
                          mapping.information_security_classification === 'Proprietary' ? '#1976d2' :
                          '#388e3c',
                        color: 'white',
                      }}
                    />
                  ) : (
                    '-'
                  )}
                </TableCell>
                <TableCell>
                  {mapping.review_status ? (
                    <Chip
                      label={mapping.review_status.replace('_', ' ')}
                      color={getStatusColor(mapping.review_status)}
                      size="small"
                      icon={getStatusIcon(mapping.review_status)}
                    />
                  ) : (
                    <Typography variant="body2" color="textSecondary">
                      Not submitted
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {mapping.reviewed_by_name && (
                    <Box>
                      <Typography variant="body2">{mapping.reviewed_by_name}</Typography>
                      {mapping.reviewed_at && (
                        <Typography variant="caption" color="textSecondary">
                          {new Date(mapping.reviewed_at).toLocaleDateString()}
                        </Typography>
                      )}
                    </Box>
                  )}
                </TableCell>
                <TableCell align="right">
                  <Box display="flex" gap={1} justifyContent="flex-end">
                    {!mapping.review_status && (
                      <Tooltip title="Submit for Review">
                        <IconButton
                          size="small"
                          onClick={() => handleSubmitForReview(mapping.id)}
                        >
                          <SendIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    {mapping.review_status === 'pending' && isReportOwnerOrAbove && (
                      <Tooltip title="Review">
                        <IconButton
                          size="small"
                          onClick={() => handleReviewMapping(mapping)}
                          color="primary"
                        >
                          <ReviewIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    {mapping.review_id && (
                      <Tooltip title="View History">
                        <IconButton
                          size="small"
                          onClick={() => handleViewHistory(mapping.id)}
                        >
                          <HistoryIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Review Dialog */}
      <Dialog open={reviewDialogOpen} onClose={() => setReviewDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Review PDE Mapping</DialogTitle>
        <DialogContent>
          {currentMapping && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Mapping Details
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="PDE Name"
                    secondary={`${currentMapping.pde_name} (${currentMapping.pde_code})`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Attribute"
                    secondary={currentMapping.attribute_name}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="LLM Confidence"
                    secondary={`${currentMapping.llm_confidence_score || 0}%`}
                  />
                </ListItem>
              </List>
            </Box>
          )}
          
          <TextField
            fullWidth
            label="Review Notes"
            multiline
            rows={3}
            value={reviewNotes}
            onChange={(e) => setReviewNotes(e.target.value)}
            sx={{ mb: 2 }}
          />
          
          <TextField
            fullWidth
            label="Revision Requested (if applicable)"
            multiline
            rows={2}
            value={revisionRequested}
            onChange={(e) => setRevisionRequested(e.target.value)}
            helperText="Specify changes needed if requesting revision"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => handleSubmitReview('rejected')}
          >
            Reject
          </Button>
          <Button
            variant="contained"
            color="info"
            onClick={() => handleSubmitReview('needs_revision')}
          >
            Request Revision
          </Button>
          <Button
            variant="contained"
            color="success"
            onClick={() => handleSubmitReview('approved')}
          >
            Approve
          </Button>
        </DialogActions>
      </Dialog>

      {/* History Dialog */}
      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Review History</DialogTitle>
        <DialogContent>
          <List>
            {reviewHistory.map((history, index) => (
              <React.Fragment key={history.id}>
                <ListItem>
                  <ListItemAvatar>
                    <Avatar>
                      {getStatusIcon(history.new_status)}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={history.action_type.replace(/_/g, ' ').toUpperCase()}
                    secondary={
                      <Box>
                        <Typography variant="body2" component="span">
                          By {history.action_by_name} on {new Date(history.action_at).toLocaleString()}
                        </Typography>
                        {history.action_notes && (
                          <Typography variant="body2" color="textSecondary">
                            Notes: {history.action_notes}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
                {index < reviewHistory.length - 1 && <Divider variant="inset" component="li" />}
              </React.Fragment>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Notifications */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
      >
        <Alert severity="success" onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};