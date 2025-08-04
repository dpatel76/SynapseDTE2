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
  Tooltip,
  Divider,
  Paper
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
  Compare,
  Restore,
  Person,
  Close,
  CheckCircle,
  Edit,
  Add
} from '@mui/icons-material';
import { format } from 'date-fns';
import { versionApi, VersionHistory } from '../../api/metrics';

interface VersionHistoryViewerProps {
  entityType: string;
  entityId: string;
  open: boolean;
  onClose: () => void;
  onRevert?: (versionNumber: number) => Promise<void>;
  canRevert?: boolean;
  currentVersion?: number;
}

export const VersionHistoryViewer: React.FC<VersionHistoryViewerProps> = ({
  entityType,
  entityId,
  open,
  onClose,
  onRevert,
  canRevert = false,
  currentVersion
}) => {
  const [history, setHistory] = useState<VersionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reverting, setReverting] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);

  useEffect(() => {
    if (open) {
      fetchHistory();
    }
  }, [open, entityType, entityId]);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await versionApi.getVersionHistory(entityType, entityId);
      setHistory(response.data);
    } catch (err) {
      console.error('Error fetching version history:', err);
      setError('Failed to load version history');
    } finally {
      setLoading(false);
    }
  };

  const handleRevert = async (versionNumber: number) => {
    if (!onRevert) return;
    
    setReverting(true);
    setError(null);
    try {
      await onRevert(versionNumber);
      await fetchHistory(); // Refresh history
    } catch (err) {
      console.error('Error reverting version:', err);
      setError('Failed to revert to selected version');
    } finally {
      setReverting(false);
    }
  };

  const handleCompare = async () => {
    if (selectedVersions.length !== 2) return;

    try {
      const response = await versionApi.compareVersions(
        entityType,
        selectedVersions[0],
        selectedVersions[1]
      );
      // Open comparison in new dialog or panel
      console.log('Comparison result:', response.data);
    } catch (err) {
      console.error('Error comparing versions:', err);
      setError('Failed to compare versions');
    }
  };

  const toggleVersionSelection = (versionId: string) => {
    setSelectedVersions(prev => {
      if (prev.includes(versionId)) {
        return prev.filter(id => id !== versionId);
      }
      if (prev.length >= 2) {
        return [prev[1], versionId];
      }
      return [...prev, versionId];
    });
  };

  const getChangeIcon = (changeType: string) => {
    switch (changeType) {
      case 'created': return <Add />;
      case 'updated': return <Edit />;
      case 'approved': return <CheckCircle />;
      default: return <History />;
    }
  };

  const getChangeColor = (changeType: string) => {
    switch (changeType) {
      case 'created': return 'primary';
      case 'updated': return 'info';
      case 'approved': return 'success';
      case 'rejected': return 'error';
      default: return 'grey';
    }
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
            <Typography variant="h6">Version History</Typography>
            <Chip
              label={`${entityType}`}
              size="small"
              variant="outlined"
            />
          </Box>
          <Box>
            {canRevert && (
              <Tooltip title="Compare versions">
                <IconButton
                  onClick={() => setCompareMode(!compareMode)}
                  color={compareMode ? 'primary' : 'default'}
                >
                  <Compare />
                </IconButton>
              </Tooltip>
            )}
            <IconButton onClick={onClose}>
              <Close />
            </IconButton>
          </Box>
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

        {compareMode && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Select two versions to compare. {selectedVersions.length}/2 selected.
          </Alert>
        )}

        {!loading && !error && (
          <Timeline position="alternate">
            {history.map((version, index) => (
              <TimelineItem key={version.id}>
                <TimelineOppositeContent
                  sx={{ m: 'auto 0' }}
                  align={index % 2 === 0 ? 'right' : 'left'}
                  variant="body2"
                  color="text.secondary"
                >
                  {format(new Date(version.changed_at), 'MMM dd, yyyy')}
                  <br />
                  {format(new Date(version.changed_at), 'HH:mm:ss')}
                </TimelineOppositeContent>

                <TimelineSeparator>
                  <TimelineConnector sx={{ bgcolor: 'grey.300' }} />
                  <TimelineDot
                    color={getChangeColor(version.change_type)}
                    variant={version.version_number === currentVersion ? 'filled' : 'outlined'}
                  >
                    {getChangeIcon(version.change_type)}
                  </TimelineDot>
                  <TimelineConnector sx={{ bgcolor: 'grey.300' }} />
                </TimelineSeparator>

                <TimelineContent sx={{ py: '12px', px: 2 }}>
                  <Paper
                    elevation={compareMode && selectedVersions.includes(version.id) ? 3 : 1}
                    sx={{
                      p: 2,
                      cursor: compareMode ? 'pointer' : 'default',
                      border: compareMode && selectedVersions.includes(version.id) 
                        ? '2px solid primary.main' 
                        : 'none'
                    }}
                    onClick={() => compareMode && toggleVersionSelection(version.id)}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Chip
                        label={`v${version.version_number}`}
                        size="small"
                        color={version.version_number === currentVersion ? 'primary' : 'default'}
                        variant={version.version_number === currentVersion ? 'filled' : 'outlined'}
                      />
                      <Typography variant="subtitle2" component="span">
                        {version.change_type.charAt(0).toUpperCase() + version.change_type.slice(1)}
                      </Typography>
                    </Box>

                    <Typography variant="body2" sx={{ mb: 1 }}>
                      {version.change_reason}
                    </Typography>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                      <Person sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">
                        {version.changed_by}
                      </Typography>
                    </Box>

                    {version.change_details && (
                      <Box sx={{ mt: 1 }}>
                        <Divider sx={{ mb: 1 }} />
                        <Typography variant="caption" color="text.secondary">
                          Changes: {Object.keys(version.change_details).length} fields modified
                        </Typography>
                      </Box>
                    )}

                    {canRevert && version.version_number !== currentVersion && !compareMode && (
                      <Box sx={{ mt: 1 }}>
                        <Button
                          size="small"
                          startIcon={<Restore />}
                          onClick={() => handleRevert(version.version_number)}
                          disabled={reverting}
                        >
                          Revert to this version
                        </Button>
                      </Box>
                    )}
                  </Paper>
                </TimelineContent>
              </TimelineItem>
            ))}
          </Timeline>
        )}
      </DialogContent>

      <DialogActions>
        {compareMode && selectedVersions.length === 2 && (
          <Button
            onClick={handleCompare}
            color="primary"
            variant="contained"
            startIcon={<Compare />}
          >
            Compare Selected
          </Button>
        )}
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default VersionHistoryViewer;