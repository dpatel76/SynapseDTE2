import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  History as HistoryIcon,
  Visibility as ViewIcon,
  CheckCircle as ActiveIcon,
  Archive as SupersededIcon,
  Edit as DraftIcon
} from '@mui/icons-material';
import { dataOwnerLobAssignmentApi, DataOwnerLOBAttributeVersion, CreateVersionRequest } from '../../api/dataOwnerLobAssignment';

interface AssignmentVersionManagerProps {
  phaseId: number;
  currentVersion: DataOwnerLOBAttributeVersion | null;
  onVersionCreated: (version: DataOwnerLOBAttributeVersion) => void;
  onRefresh: () => void;
}

const AssignmentVersionManager: React.FC<AssignmentVersionManagerProps> = ({
  phaseId,
  currentVersion,
  onVersionCreated,
  onRefresh
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [versionHistory, setVersionHistory] = useState<DataOwnerLOBAttributeVersion[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showHistoryDialog, setShowHistoryDialog] = useState(false);
  const [newVersionNotes, setNewVersionNotes] = useState('');

  const loadVersionHistory = async () => {
    try {
      const history = await dataOwnerLobAssignmentApi.getVersionHistory(phaseId);
      setVersionHistory(history);
    } catch (err: any) {
      console.error('Error loading version history:', err);
      setError(err.response?.data?.detail || 'Failed to load version history');
    }
  };

  useEffect(() => {
    if (showHistoryDialog) {
      loadVersionHistory();
    }
  }, [showHistoryDialog, phaseId]);

  const handleCreateVersion = async () => {
    try {
      setLoading(true);
      setError(null);

      const request: CreateVersionRequest = {
        phase_id: phaseId,
        assignment_notes: newVersionNotes.trim() || undefined
      };

      const newVersion = await dataOwnerLobAssignmentApi.createVersion(request);
      
      setShowCreateDialog(false);
      setNewVersionNotes('');
      onVersionCreated(newVersion);
      
    } catch (err: any) {
      console.error('Error creating version:', err);
      setError(err.response?.data?.detail || 'Failed to create version');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <ActiveIcon color="success" />;
      case 'draft': return <DraftIcon color="warning" />;
      case 'superseded': return <SupersededIcon color="disabled" />;
      default: return <ActiveIcon color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'draft': return 'warning';
      case 'superseded': return 'default';
      default: return 'default';
    }
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Version Management
              </Typography>
              
              {currentVersion ? (
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Current Active Version
                  </Typography>
                  
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <Chip
                      icon={getStatusIcon(currentVersion.version_status)}
                      label={`Version ${currentVersion.version_number}`}
                      color={getStatusColor(currentVersion.version_status) as any}
                    />
                    <Typography variant="body2">
                      Created: {new Date(currentVersion.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>

                  {currentVersion.assignment_notes && (
                    <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 2 }}>
                      "{currentVersion.assignment_notes}"
                    </Typography>
                  )}

                  <Box display="flex" gap={1}>
                    <Chip 
                      label={`${currentVersion.total_lob_attributes} Total`}
                      variant="outlined"
                      size="small"
                    />
                    <Chip 
                      label={`${currentVersion.assigned_lob_attributes} Assigned`}
                      color="success"
                      variant="outlined"
                      size="small"
                    />
                    <Chip 
                      label={`${currentVersion.unassigned_lob_attributes} Unassigned`}
                      color="warning"
                      variant="outlined"
                      size="small"
                    />
                  </Box>
                </Box>
              ) : (
                <Alert severity="info">
                  No active version exists. Create a new version to start managing assignments.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Actions
              </Typography>
              
              <Box display="flex" flexDirection="column" gap={2}>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setShowCreateDialog(true)}
                  fullWidth
                >
                  Create New Version
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<HistoryIcon />}
                  onClick={() => setShowHistoryDialog(true)}
                  fullWidth
                >
                  View History
                </Button>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Creating a new version will supersede the current active version and allow you to make new assignments.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Create Version Dialog */}
      <Dialog 
        open={showCreateDialog} 
        onClose={() => setShowCreateDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Assignment Version</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            This will create a new version for data owner LOB assignments and supersede any existing active version.
          </Typography>
          
          <TextField
            autoFocus
            margin="dense"
            label="Assignment Notes (Optional)"
            type="text"
            fullWidth
            variant="outlined"
            multiline
            rows={3}
            value={newVersionNotes}
            onChange={(e) => setNewVersionNotes(e.target.value)}
            placeholder="Describe the purpose or changes for this assignment batch..."
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setShowCreateDialog(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleCreateVersion}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <AddIcon />}
          >
            Create Version
          </Button>
        </DialogActions>
      </Dialog>

      {/* Version History Dialog */}
      <Dialog 
        open={showHistoryDialog} 
        onClose={() => setShowHistoryDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Version History</DialogTitle>
        <DialogContent>
          {versionHistory.length > 0 ? (
            <List>
              {versionHistory.map((version) => (
                <ListItem key={version.version_id} divider>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip
                          icon={getStatusIcon(version.version_status)}
                          label={`Version ${version.version_number}`}
                          color={getStatusColor(version.version_status) as any}
                          size="small"
                        />
                        <Typography variant="body2">
                          {new Date(version.created_at).toLocaleDateString()}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        {version.assignment_notes && (
                          <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
                            "{version.assignment_notes}"
                          </Typography>
                        )}
                        <Box display="flex" gap={1}>
                          <Chip 
                            label={`${version.total_lob_attributes} Total`}
                            variant="outlined"
                            size="small"
                          />
                          <Chip 
                            label={`${version.assigned_lob_attributes} Assigned`}
                            color="success"
                            variant="outlined"
                            size="small"
                          />
                        </Box>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Tooltip title="View Details">
                      <IconButton 
                        edge="end"
                        onClick={() => {
                          // Could implement version details view
                          console.log('View version details:', version.version_id);
                        }}
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No version history available.
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHistoryDialog(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AssignmentVersionManager;