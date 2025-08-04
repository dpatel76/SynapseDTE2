import React, { useEffect, useState } from 'react';
import {
  Box,
  LinearProgress,
  Typography,
  Paper,
  IconButton,
  Chip,
  Collapse,
  Grid
} from '@mui/material';
import {
  Cancel,
  ExpandMore,
  ExpandLess,
  Speed,
  Timer
} from '@mui/icons-material';
import { batchApi, BatchProgress } from '../../api/metrics';

interface BatchProgressIndicatorProps {
  jobId: string;
  title?: string;
  onComplete?: () => void;
  onError?: (error: any) => void;
  onCancel?: () => void;
  pollInterval?: number;
  showDetails?: boolean;
}

export const BatchProgressIndicator: React.FC<BatchProgressIndicatorProps> = ({
  jobId,
  title = 'Processing',
  onComplete,
  onError,
  onCancel,
  pollInterval = 2000,
  showDetails = false
}) => {
  const [progress, setProgress] = useState<BatchProgress | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const fetchProgress = async () => {
      try {
        const response = await batchApi.getBatchProgress(jobId);
        const data = response.data;
        setProgress(data);
        setLoading(false);

        if (data.status === 'completed' && onComplete) {
          onComplete();
        } else if (data.status === 'failed' && onError) {
          onError(new Error('Batch processing failed'));
        }

        // Stop polling if completed or failed
        if (['completed', 'failed', 'cancelled'].includes(data.status)) {
          clearInterval(intervalId);
        }
      } catch (err) {
        console.error('Error fetching batch progress:', err);
        setError('Failed to fetch progress');
        setLoading(false);
        if (onError) onError(err);
      }
    };

    // Initial fetch
    fetchProgress();

    // Set up polling
    intervalId = setInterval(fetchProgress, pollInterval);

    return () => clearInterval(intervalId);
  }, [jobId, pollInterval, onComplete, onError]);

  const handleCancel = async () => {
    try {
      await batchApi.cancelBatch(jobId);
      if (onCancel) onCancel();
    } catch (err) {
      console.error('Error cancelling batch:', err);
      setError('Failed to cancel batch');
    }
  };

  const formatTime = (seconds?: number): string => {
    if (!seconds || seconds < 0) return '--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'primary';
      case 'partial': return 'warning';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Paper sx={{ p: 2 }}>
        <LinearProgress />
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 2, bgcolor: 'error.light' }}>
        <Typography color="error">{error}</Typography>
      </Paper>
    );
  }

  if (!progress) return null;

  const canCancel = progress.status === 'running' || progress.status === 'pending';

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
          {title}
        </Typography>
        <Chip
          label={progress.status}
          color={getStatusColor(progress.status)}
          size="small"
          sx={{ mr: 1 }}
        />
        {showDetails && (
          <IconButton
            size="small"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        )}
        {canCancel && onCancel && (
          <IconButton
            size="small"
            color="error"
            onClick={handleCancel}
            title="Cancel batch"
          >
            <Cancel />
          </IconButton>
        )}
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Box sx={{ width: '100%', mr: 1 }}>
          <LinearProgress
            variant="determinate"
            value={progress.progress_percentage}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>
        <Box sx={{ minWidth: 35 }}>
          <Typography variant="body2" color="text.secondary">
            {Math.round(progress.progress_percentage)}%
          </Typography>
        </Box>
      </Box>

      <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="caption" color="text.secondary">
          {progress.completed_steps} / {progress.total_steps} steps
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {progress.current_step}
        </Typography>
      </Box>

      <Collapse in={expanded && showDetails}>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid size={{ xs: 6 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Speed sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Status
                </Typography>
                <Typography variant="body2">
                  {progress.message || 'Processing...'}
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid size={{ xs: 6 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Timer sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Started At
                </Typography>
                <Typography variant="body2">
                  {progress.started_at ? new Date(progress.started_at).toLocaleTimeString() : 'Not started'}
                </Typography>
              </Box>
            </Box>
          </Grid>
          {progress.error && (
            <Grid size={{ xs: 12 }}>
              <Typography variant="caption" color="error">
                Error: {progress.error}
              </Typography>
            </Grid>
          )}
        </Grid>
      </Collapse>
    </Paper>
  );
};

export default BatchProgressIndicator;