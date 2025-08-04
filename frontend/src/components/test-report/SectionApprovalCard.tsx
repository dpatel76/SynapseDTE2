import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  LinearProgress
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Edit as EditIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import apiClient from '../../api/client';

interface SectionApprovalCardProps {
  section: {
    id: number;
    section_name: string;
    section_title: string;
    section_order: number;
    status: string;
    last_generated_at: string | null;
    requires_refresh: boolean;
    approval_status: string;
    next_approver: string | null;
    is_fully_approved: boolean;
    data_sources: string[];
    approvals: {
      tester: {
        approved: boolean;
        approved_by: number | null;
        approved_at: string | null;
        notes: string | null;
      };
      report_owner: {
        approved: boolean;
        approved_by: number | null;
        approved_at: string | null;
        notes: string | null;
      };
      executive: {
        approved: boolean;
        approved_by: number | null;
        approved_at: string | null;
        notes: string | null;
      };
    };
  };
  cycleId: number;
  reportId: number;
  userRole: string;
  onSectionUpdated: () => void;
}

const SectionApprovalCard: React.FC<SectionApprovalCardProps> = ({
  section,
  cycleId,
  reportId,
  userRole,
  onSectionUpdated
}) => {
  const [approvalDialog, setApprovalDialog] = useState(false);
  const [rejectionDialog, setRejectionDialog] = useState(false);
  const [revisionDialog, setRevisionDialog] = useState(false);
  const [notes, setNotes] = useState('');
  const [approvalLevel, setApprovalLevel] = useState('');
  const [loading, setLoading] = useState(false);

  const canApprove = () => {
    const nextApprover = section.next_approver;
    
    if (userRole === 'Tester' && nextApprover === 'tester') return true;
    if (userRole === 'Report Owner' && nextApprover === 'report_owner') return true;
    if (userRole === 'Executive' && nextApprover === 'executive') return true;
    
    return false;
  };

  const handleApprove = async () => {
    try {
      setLoading(true);
      
      await apiClient.post(
        `/test-report/${cycleId}/reports/${reportId}/sections/${section.id}/approve`,
        {
          approval_level: section.next_approver,
          notes: notes || undefined
        }
      );
      
      setApprovalDialog(false);
      setNotes('');
      onSectionUpdated();
    } catch (error: any) {
      console.error('Error approving section:', error);
      alert(error.response?.data?.detail || 'Failed to approve section');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!notes.trim()) {
      alert('Rejection notes are required');
      return;
    }

    try {
      setLoading(true);
      
      await apiClient.post(
        `/test-report/${cycleId}/reports/${reportId}/sections/${section.id}/reject`,
        {
          approval_level: section.next_approver,
          notes: notes
        }
      );
      
      setRejectionDialog(false);
      setNotes('');
      onSectionUpdated();
    } catch (error: any) {
      console.error('Error rejecting section:', error);
      alert(error.response?.data?.detail || 'Failed to reject section');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestRevision = async () => {
    if (!notes.trim()) {
      alert('Revision notes are required');
      return;
    }

    try {
      setLoading(true);
      
      await apiClient.post(
        `/test-report/${cycleId}/reports/${reportId}/sections/${section.id}/request-revision`,
        {
          revision_level: section.next_approver,
          notes: notes
        }
      );
      
      setRevisionDialog(false);
      setNotes('');
      onSectionUpdated();
    } catch (error: any) {
      console.error('Error requesting revision:', error);
      alert(error.response?.data?.detail || 'Failed to request revision');
    } finally {
      setLoading(false);
    }
  };

  const renderApprovalStatus = () => {
    const { tester, report_owner, executive } = section.approvals;
    
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PersonIcon fontSize="small" />
          <Typography variant="body2">Tester:</Typography>
          <Chip
            size="small"
            icon={tester.approved ? <CheckCircleIcon /> : <ScheduleIcon />}
            label={tester.approved ? 'Approved' : 'Pending'}
            color={tester.approved ? 'success' : 'default'}
          />
          {tester.approved_at && (
            <Typography variant="caption" color="text.secondary">
              {format(new Date(tester.approved_at), 'MMM dd, yyyy')}
            </Typography>
          )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PersonIcon fontSize="small" />
          <Typography variant="body2">Report Owner:</Typography>
          <Chip
            size="small"
            icon={report_owner.approved ? <CheckCircleIcon /> : <ScheduleIcon />}
            label={report_owner.approved ? 'Approved' : 'Pending'}
            color={report_owner.approved ? 'success' : 'default'}
          />
          {report_owner.approved_at && (
            <Typography variant="caption" color="text.secondary">
              {format(new Date(report_owner.approved_at), 'MMM dd, yyyy')}
            </Typography>
          )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PersonIcon fontSize="small" />
          <Typography variant="body2">Executive:</Typography>
          <Chip
            size="small"
            icon={executive.approved ? <CheckCircleIcon /> : <ScheduleIcon />}
            label={executive.approved ? 'Approved' : 'Pending'}
            color={executive.approved ? 'success' : 'default'}
          />
          {executive.approved_at && (
            <Typography variant="caption" color="text.secondary">
              {format(new Date(executive.approved_at), 'MMM dd, yyyy')}
            </Typography>
          )}
        </Box>
      </Box>
    );
  };

  const getStatusColor = () => {
    if (section.is_fully_approved) return 'success';
    if (section.status === 'rejected') return 'error';
    if (section.status === 'revision_requested') return 'warning';
    return 'info';
  };

  return (
    <>
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" gutterBottom>
                {section.section_title}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {section.section_name} • Order: {section.section_order}
              </Typography>
              
              {section.last_generated_at && (
                <Typography variant="caption" color="text.secondary">
                  Last generated: {format(new Date(section.last_generated_at), 'MMM dd, yyyy HH:mm')}
                </Typography>
              )}
            </Box>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1 }}>
              <Chip
                label={section.is_fully_approved ? 'Fully Approved' : section.status}
                color={getStatusColor()}
                size="small"
              />
              {section.requires_refresh && (
                <Chip
                  label="Needs Refresh"
                  color="warning"
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>

          {renderApprovalStatus()}

          {section.data_sources.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Data Sources: {section.data_sources.join(', ')}
              </Typography>
            </Box>
          )}

          {canApprove() && !section.is_fully_approved && (
            <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
              <Button
                variant="contained"
                color="success"
                size="small"
                onClick={() => setApprovalDialog(true)}
                startIcon={<CheckCircleIcon />}
              >
                Approve
              </Button>
              <Button
                variant="outlined"
                color="error"
                size="small"
                onClick={() => setRejectionDialog(true)}
                startIcon={<CancelIcon />}
              >
                Reject
              </Button>
              <Button
                variant="outlined"
                color="warning"
                size="small"
                onClick={() => setRevisionDialog(true)}
                startIcon={<EditIcon />}
              >
                Request Revision
              </Button>
            </Box>
          )}

          {section.is_fully_approved && (
            <Alert severity="success" sx={{ mt: 2 }}>
              This section has been fully approved and is ready for final report generation.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Approval Dialog */}
      <Dialog open={approvalDialog} onClose={() => setApprovalDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Approve Section</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Are you sure you want to approve "{section.section_title}"?
          </Typography>
          <TextField
            fullWidth
            label="Approval Notes (Optional)"
            multiline
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApprovalDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="success"
            onClick={handleApprove}
            disabled={loading}
          >
            {loading ? 'Approving...' : 'Approve'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Rejection Dialog */}
      <Dialog open={rejectionDialog} onClose={() => setRejectionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Reject Section</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Please provide a reason for rejecting "{section.section_title}":
          </Typography>
          <TextField
            fullWidth
            label="Rejection Notes (Required)"
            multiline
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            sx={{ mt: 2 }}
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectionDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleReject}
            disabled={loading || !notes.trim()}
          >
            {loading ? 'Rejecting...' : 'Reject'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Revision Dialog */}
      <Dialog open={revisionDialog} onClose={() => setRevisionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Request Revision</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Please provide details for the revision request for "{section.section_title}":
          </Typography>
          <TextField
            fullWidth
            label="Revision Notes (Required)"
            multiline
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            sx={{ mt: 2 }}
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRevisionDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="warning"
            onClick={handleRequestRevision}
            disabled={loading || !notes.trim()}
          >
            {loading ? 'Requesting...' : 'Request Revision'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default SectionApprovalCard;