import React, { useState } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Typography,
  Stack,
  SelectChangeEvent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert
} from '@mui/material';
import {
  History,
  CheckCircle,
  Cancel,
  Schedule,
  Refresh,
  Add,
  CompareArrows
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { versionApi, VersionHistory } from '../../api/metrics';
import { toast } from 'react-toastify';
import { useAuth } from '../../contexts/AuthContext';

interface VersionSelectorProps {
  entityType: string;
  entityId: string;
  currentVersion?: number;
  onVersionChange?: (version: number) => void;
  onViewHistory?: () => void;
  showCreateButton?: boolean;
  showApprovalStatus?: boolean;
  approvedOnly?: boolean;
}

interface Version {
  version_id: string;
  version_number: number;
  status: 'draft' | 'pending_approval' | 'approved' | 'rejected';
  created_at: string;
  created_by: string;
  change_reason?: string;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'approved':
      return 'success';
    case 'rejected':
      return 'error';
    case 'pending_approval':
      return 'warning';
    default:
      return 'default';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'approved':
      return <CheckCircle fontSize="small" />;
    case 'rejected':
      return <Cancel fontSize="small" />;
    case 'pending_approval':
      return <Schedule fontSize="small" />;
    default:
      return null;
  }
};

export const VersionSelector: React.FC<VersionSelectorProps> = ({
  entityType,
  entityId,
  currentVersion,
  onVersionChange,
  onViewHistory,
  showCreateButton = true,
  showApprovalStatus = true,
  approvedOnly = false
}) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedVersion, setSelectedVersion] = useState<number>(currentVersion || 1);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createReason, setCreateReason] = useState('');
  const [createNotes, setCreateNotes] = useState('');

  const canCreateVersion = ['Tester', 'Test Executive', 'Report Owner'].includes(user?.role || '');
  const canApprove = ['Report Owner', 'Report Executive', 'Test Executive'].includes(user?.role || '');

  // Fetch version history
  const { data: versions, isLoading, refetch } = useQuery<Version[]>({
    queryKey: ['version-history', entityType, entityId],
    queryFn: async () => {
      const response = await versionApi.getVersionHistory(entityType, entityId);
      // Transform VersionHistory[] to Version[]
      const versionHistory: VersionHistory[] = response.data;
      return versionHistory.map(vh => ({
        version_id: vh.id,
        version_number: vh.version_number,
        status: 'approved' as const, // Default to approved since VersionHistory doesn't have status
        created_at: vh.changed_at,
        created_by: vh.changed_by,
        change_reason: vh.change_reason
      }));
    },
    refetchInterval: 60000 // Refresh every minute
  });

  // Create version mutation
  const createVersionMutation = useMutation({
    mutationFn: async () => {
      return versionApi.createVersion({
        entity_type: entityType,
        entity_id: entityId,
        reason: createReason,
        notes: createNotes,
        auto_approve: false
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['version-history', entityType, entityId] });
      toast.success('New version created successfully');
      setShowCreateDialog(false);
      setCreateReason('');
      setCreateNotes('');
      refetch();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create version');
    }
  });

  const handleVersionChange = (event: SelectChangeEvent<number>) => {
    const newVersion = event.target.value as number;
    setSelectedVersion(newVersion);
    onVersionChange?.(newVersion);
  };

  const handleRefresh = () => {
    refetch();
  };

  const filteredVersions = versions?.filter(v => 
    !approvedOnly || v.status === 'approved'
  ) || [];

  return (
    <Box>
      <Stack direction="row" spacing={2} alignItems="center">
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Version</InputLabel>
          <Select
            value={selectedVersion}
            onChange={handleVersionChange}
            label="Version"
            disabled={isLoading}
            startAdornment={
              isLoading ? (
                <Box sx={{ display: 'flex', pl: 1 }}>
                  <CircularProgress size={16} />
                </Box>
              ) : null
            }
          >
            {filteredVersions.map(version => (
              <MenuItem key={version.version_id} value={version.version_number}>
                <Box display="flex" alignItems="center" gap={1} width="100%">
                  <Typography variant="body2">
                    v{version.version_number}
                  </Typography>
                  {showApprovalStatus && (
                    <Chip
                      label={version.status}
                      size="small"
                      color={getStatusColor(version.status)}
                      icon={getStatusIcon(version.status) || undefined}
                    />
                  )}
                  {version.change_reason && (
                    <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                      {version.change_reason}
                    </Typography>
                  )}
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Tooltip title="Refresh versions">
          <IconButton size="small" onClick={handleRefresh}>
            <Refresh />
          </IconButton>
        </Tooltip>

        {onViewHistory && (
          <Tooltip title="View version history">
            <IconButton size="small" onClick={onViewHistory}>
              <History />
            </IconButton>
          </Tooltip>
        )}

        {showCreateButton && canCreateVersion && (
          <Tooltip title="Create new version">
            <IconButton 
              size="small" 
              color="primary" 
              onClick={() => setShowCreateDialog(true)}
            >
              <Add />
            </IconButton>
          </Tooltip>
        )}
      </Stack>

      {/* Current version info */}
      {versions && versions.length > 0 && (
        <Box mt={1}>
          <Typography variant="caption" color="text.secondary">
            Current: v{selectedVersion} • 
            {versions.find(v => v.version_number === selectedVersion)?.created_by} • 
            {new Date(versions.find(v => v.version_number === selectedVersion)?.created_at || '').toLocaleDateString()}
          </Typography>
        </Box>
      )}

      {/* Create Version Dialog */}
      <Dialog 
        open={showCreateDialog} 
        onClose={() => setShowCreateDialog(false)} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>Create New Version</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Creating a new version will increment to v{(versions?.[0]?.version_number || 0) + 1}
          </Alert>
          
          <TextField
            fullWidth
            label="Reason for New Version"
            value={createReason}
            onChange={(e) => setCreateReason(e.target.value)}
            placeholder="e.g., Updated attributes based on regulatory changes"
            required
            sx={{ mb: 2 }}
          />
          
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Additional Notes (Optional)"
            value={createNotes}
            onChange={(e) => setCreateNotes(e.target.value)}
            placeholder="Any additional context or details..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => createVersionMutation.mutate()}
            disabled={!createReason.trim() || createVersionMutation.isPending}
          >
            Create Version
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default VersionSelector;