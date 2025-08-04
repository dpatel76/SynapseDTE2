import React, { useState } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Stack
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  ThumbUp,
  ThumbDown
} from '@mui/icons-material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { versionApi } from '../../api/metrics';
import { toast } from 'react-toastify';
import { useAuth } from '../../contexts/AuthContext';

interface VersionApprovalButtonsProps {
  entityType: string;
  versionId: string;
  versionNumber: number;
  versionStatus: string;
  onStatusChange?: () => void;
}

export const VersionApprovalButtons: React.FC<VersionApprovalButtonsProps> = ({
  entityType,
  versionId,
  versionNumber,
  versionStatus,
  onStatusChange
}) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [approvalNotes, setApprovalNotes] = useState('');
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);

  const canApprove = ['Report Owner', 'Report Executive', 'Test Executive'].includes(user?.role || '');

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: async (notes?: string) => {
      return versionApi.approveVersion(entityType, versionId, notes);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['version-history'] });
      toast.success(`Version ${versionNumber} approved successfully`);
      setShowApprovalDialog(false);
      setApprovalNotes('');
      onStatusChange?.();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to approve version');
    }
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: async (reason: string) => {
      return versionApi.rejectVersion(entityType, versionId, reason);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['version-history'] });
      toast.success(`Version ${versionNumber} rejected`);
      setShowRejectDialog(false);
      setRejectReason('');
      onStatusChange?.();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to reject version');
    }
  });

  if (!canApprove || versionStatus !== 'pending_approval') {
    return null;
  }

  return (
    <>
      <Stack direction="row" spacing={1}>
        <Button
          variant="contained"
          color="success"
          size="small"
          startIcon={<ThumbUp />}
          onClick={() => setShowApprovalDialog(true)}
          disabled={approveMutation.isPending || rejectMutation.isPending}
        >
          Approve
        </Button>
        <Button
          variant="outlined"
          color="error"
          size="small"
          startIcon={<ThumbDown />}
          onClick={() => setShowRejectDialog(true)}
          disabled={approveMutation.isPending || rejectMutation.isPending}
        >
          Reject
        </Button>
      </Stack>

      {/* Approval Dialog */}
      <Dialog
        open={showApprovalDialog}
        onClose={() => setShowApprovalDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Approve Version {versionNumber}</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Approving this version will make it the official version for use.
          </Alert>
          
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Approval Notes (Optional)"
            value={approvalNotes}
            onChange={(e) => setApprovalNotes(e.target.value)}
            placeholder="Any comments about this approval..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowApprovalDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="success"
            onClick={() => approveMutation.mutate(approvalNotes || undefined)}
            disabled={approveMutation.isPending}
            startIcon={<CheckCircle />}
          >
            Approve Version
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog
        open={showRejectDialog}
        onClose={() => setShowRejectDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Reject Version {versionNumber}</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Rejecting this version will require revisions before it can be used.
          </Alert>
          
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Rejection Reason"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Please provide a reason for rejection..."
            required
            error={!rejectReason.trim() && rejectMutation.isPending}
            helperText={!rejectReason.trim() && rejectMutation.isPending ? "Reason is required" : ""}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowRejectDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => rejectMutation.mutate(rejectReason)}
            disabled={!rejectReason.trim() || rejectMutation.isPending}
            startIcon={<Cancel />}
          >
            Reject Version
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default VersionApprovalButtons;