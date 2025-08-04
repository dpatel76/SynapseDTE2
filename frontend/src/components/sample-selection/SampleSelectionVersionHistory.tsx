import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Divider,
  Paper,
  Stack
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent
} from '@mui/lab';
import {
  History,
  Close,
  CheckCircle,
  Edit,
  Add,
  Person,
  Block,
  RateReview,
  CloudUpload,
  AutoFixHigh
} from '@mui/icons-material';
import { format } from 'date-fns';
import apiClient from '../../api/api';

interface VersionHistoryItem {
  version_id: string;
  version_number: number;
  version_status: string;
  created_at: string;
  created_by: string;
  created_by_name?: string;
  is_current: boolean;
  total_samples: number;
  approved_samples: number;
  rejected_samples: number;
  pending_samples: number;
  change_reason?: string;
  generation_method?: string;
  approved_at?: string;
  approved_by?: string;
  rejected_at?: string;
  rejected_by?: string;
  rejection_reason?: string;
}

interface SampleSelectionVersionHistoryProps {
  cycleId: number;
  reportId: number;
  open: boolean;
  onClose: () => void;
  currentVersion?: number;
}

export const SampleSelectionVersionHistory: React.FC<SampleSelectionVersionHistoryProps> = ({
  cycleId,
  reportId,
  open,
  onClose,
  currentVersion
}) => {
  const [history, setHistory] = useState<VersionHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      fetchHistory();
    }
  }, [open, cycleId, reportId]);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get(
        `/sample-selection/${cycleId}/reports/${reportId}/versions`
      );
      setHistory(response.data || []);
    } catch (err) {
      console.error('Error fetching version history:', err);
      setError('Failed to load version history');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft': return <Edit />;
      case 'pending_approval': return <RateReview />;
      case 'approved': return <CheckCircle />;
      case 'rejected': return <Block />;
      case 'superseded': return <History />;
      default: return <History />;
    }
  };

  const getStatusColor = (status: string): "inherit" | "grey" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    switch (status) {
      case 'draft': return 'grey';
      case 'pending_approval': return 'warning';
      case 'approved': return 'success';
      case 'rejected': return 'error';
      case 'superseded': return 'grey';
      default: return 'grey';
    }
  };

  const getGenerationIcon = (method?: string) => {
    switch (method) {
      case 'generated': return <AutoFixHigh />;
      case 'uploaded': return <CloudUpload />;
      default: return <Add />;
    }
  };

  const formatChangeReason = (version: VersionHistoryItem): string => {
    if (version.change_reason) {
      return version.change_reason;
    }
    
    if (version.version_number === 1) {
      return 'Initial version';
    }
    
    if (version.rejection_reason) {
      return `Previous version rejected: ${version.rejection_reason}`;
    }
    
    return version.generation_method === 'uploaded' 
      ? 'Samples uploaded by user' 
      : 'New samples generated';
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '70vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <History />
            <Typography variant="h6">Sample Selection Version History</Typography>
          </Box>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && !error && history.length === 0 && (
          <Alert severity="info">
            No version history available yet.
          </Alert>
        )}

        {!loading && !error && history.length > 0 && (
          <Timeline position="alternate">
            {history.map((version, index) => (
              <TimelineItem key={version.version_id}>
                <TimelineOppositeContent
                  sx={{ m: 'auto 0' }}
                  align={index % 2 === 0 ? 'right' : 'left'}
                  variant="body2"
                  color="text.secondary"
                >
                  {format(new Date(version.created_at), 'MMM dd, yyyy')}
                  <br />
                  {format(new Date(version.created_at), 'HH:mm:ss')}
                </TimelineOppositeContent>

                <TimelineSeparator>
                  <TimelineConnector sx={{ bgcolor: 'grey.300' }} />
                  <TimelineDot
                    color={getStatusColor(version.version_status)}
                    variant={version.is_current ? 'filled' : 'outlined'}
                  >
                    {getStatusIcon(version.version_status)}
                  </TimelineDot>
                  <TimelineConnector sx={{ bgcolor: 'grey.300' }} />
                </TimelineSeparator>

                <TimelineContent sx={{ py: '12px', px: 2 }}>
                  <Paper elevation={1} sx={{ p: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Chip
                        label={`v${version.version_number}`}
                        size="small"
                        color={version.is_current ? 'primary' : 'default'}
                        variant={version.is_current ? 'filled' : 'outlined'}
                      />
                      <Chip
                        label={version.version_status.replace('_', ' ')}
                        size="small"
                        color={getStatusColor(version.version_status) as any}
                        variant="outlined"
                      />
                      {version.generation_method && (
                        <Chip
                          icon={getGenerationIcon(version.generation_method)}
                          label={version.generation_method}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>

                    <Typography variant="body2" sx={{ mb: 1 }}>
                      {formatChangeReason(version)}
                    </Typography>

                    <Stack spacing={0.5} sx={{ mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Person sx={{ fontSize: 16, color: 'text.secondary' }} />
                        <Typography variant="caption" color="text.secondary">
                          Created by: {version.created_by_name || version.created_by}
                        </Typography>
                      </Box>

                      {version.approved_at && version.approved_by && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <CheckCircle sx={{ fontSize: 16, color: 'success.main' }} />
                          <Typography variant="caption" color="text.secondary">
                            Approved by: {version.approved_by} on {format(new Date(version.approved_at), 'MMM dd, yyyy')}
                          </Typography>
                        </Box>
                      )}

                      {version.rejected_at && version.rejected_by && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Block sx={{ fontSize: 16, color: 'error.main' }} />
                          <Typography variant="caption" color="text.secondary">
                            Rejected by: {version.rejected_by} on {format(new Date(version.rejected_at), 'MMM dd, yyyy')}
                          </Typography>
                        </Box>
                      )}
                    </Stack>

                    <Divider sx={{ my: 1 }} />

                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      <Typography variant="caption" color="text.secondary">
                        Total Samples: <strong>{version.total_samples}</strong>
                      </Typography>
                      {version.approved_samples > 0 && (
                        <Typography variant="caption" color="success.main">
                          Approved: <strong>{version.approved_samples}</strong>
                        </Typography>
                      )}
                      {version.rejected_samples > 0 && (
                        <Typography variant="caption" color="error.main">
                          Rejected: <strong>{version.rejected_samples}</strong>
                        </Typography>
                      )}
                      {version.pending_samples > 0 && (
                        <Typography variant="caption" color="warning.main">
                          Pending: <strong>{version.pending_samples}</strong>
                        </Typography>
                      )}
                    </Box>

                    {version.rejection_reason && (
                      <Alert severity="error" sx={{ mt: 1 }} icon={false}>
                        <Typography variant="caption">
                          <strong>Rejection Reason:</strong> {version.rejection_reason}
                        </Typography>
                      </Alert>
                    )}
                  </Paper>
                </TimelineContent>
              </TimelineItem>
            ))}
          </Timeline>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default SampleSelectionVersionHistory;