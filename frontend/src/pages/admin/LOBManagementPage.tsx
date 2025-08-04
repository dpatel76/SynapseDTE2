import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
  Alert,
  Chip,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Business as BusinessIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNotifications } from '../../contexts/NotificationContext';
import apiClient from '../../api/client';
import { usePermissions } from '../../contexts/PermissionContext';
import { PermissionGate } from '../../components/auth/PermissionGate';

interface LOB {
  lob_id: number;
  lob_name: string;
  created_at: string;
  updated_at: string;
  user_count?: number;
  report_count?: number;
  active_cycles?: number;
}

interface LOBCreate {
  lob_name: string;
}

interface LOBUpdate {
  lob_name?: string;
}

interface StatsData {
  total_lobs: number;
  users_by_lob: Record<string, number>;
  reports_by_lob: Record<string, number>;
  active_cycles_by_lob: Record<string, number>;
}

// API functions
const api = {
  getLOBs: async (): Promise<{ lobs: LOB[]; total: number }> => {
    console.log('LOBManagementPage: Fetching LOBs...');
    const response = await apiClient.get('/lobs/');
    console.log('LOBManagementPage: LOBs response:', response.status, response.statusText);
    console.log('LOBManagementPage: LOBs data:', response.data);
    return response.data;
  },

  createLOB: async (lob: LOBCreate): Promise<LOB> => {
    const response = await apiClient.post('/lobs/', lob);
    return response.data;
  },

  updateLOB: async (lobId: number, lob: LOBUpdate): Promise<LOB> => {
    const response = await apiClient.put(`/lobs/${lobId}`, lob);
    return response.data;
  },

  deleteLOB: async (lobId: number): Promise<void> => {
    await apiClient.delete(`/lobs/${lobId}`);
  },

  getLOBStats: async (): Promise<StatsData> => {
    console.log('LOBManagementPage: Fetching LOB stats...');
    const response = await apiClient.get('/lobs/stats/overview');
    console.log('LOBManagementPage: Stats response:', response.status, response.statusText);
    console.log('LOBManagementPage: Parsed stats data:', response.data);
    return response.data;
  },
};

export const LOBManagementPage: React.FC = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingLOB, setEditingLOB] = useState<LOB | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [lobToDelete, setLobToDelete] = useState<LOB | null>(null);
  const [formData, setFormData] = useState<LOBCreate>({
    lob_name: '',
  });

  const { showToast } = useNotifications();
  const { hasPermission } = usePermissions();
  const queryClient = useQueryClient();

  // Queries
  const { data: lobsData, isLoading, error, refetch } = useQuery({
    queryKey: ['lobs'],
    queryFn: api.getLOBs,
  });

  const { data: statsData, error: statsError } = useQuery({
    queryKey: ['lob-stats'],
    queryFn: api.getLOBStats,
  });

  // Debug logging
  React.useEffect(() => {
    console.log('LOBManagementPage: Query state update - lobsData:', lobsData);
    console.log('LOBManagementPage: Query state update - error:', error);
    console.log('LOBManagementPage: Query state update - isLoading:', isLoading);
  }, [lobsData, error, isLoading]);

  React.useEffect(() => {
    console.log('LOBManagementPage: Stats query state update - statsData:', statsData);
    console.log('LOBManagementPage: Stats query state update - statsError:', statsError);
  }, [statsData, statsError]);

  // Mutations
  const createMutation = useMutation({
    mutationFn: api.createLOB,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lobs'] });
      queryClient.invalidateQueries({ queryKey: ['lob-stats'] });
      setDialogOpen(false);
      setFormData({ lob_name: '' });
      showToast('success', 'LOB created successfully');
    },
    onError: (error: Error) => {
      showToast('error', `Failed to create LOB: ${error.message}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ lobId, data }: { lobId: number; data: LOBUpdate }) =>
      api.updateLOB(lobId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lobs'] });
      queryClient.invalidateQueries({ queryKey: ['lob-stats'] });
      setDialogOpen(false);
      setEditingLOB(null);
      setFormData({ lob_name: '' });
      showToast('success', 'LOB updated successfully');
    },
    onError: (error: Error) => {
      showToast('error', `Failed to update LOB: ${error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteLOB,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lobs'] });
      queryClient.invalidateQueries({ queryKey: ['lob-stats'] });
      setDeleteDialogOpen(false);
      setLobToDelete(null);
      showToast('success', 'LOB deleted successfully');
    },
    onError: (error: Error) => {
      showToast('error', `Failed to delete LOB: ${error.message}`);
    },
  });

  const handleCreate = () => {
    setEditingLOB(null);
    setFormData({ lob_name: '' });
    setDialogOpen(true);
  };

  const handleEdit = (lob: LOB) => {
    setEditingLOB(lob);
    setFormData({ lob_name: lob.lob_name });
    setDialogOpen(true);
  };

  const handleDelete = (lob: LOB) => {
    setLobToDelete(lob);
    setDeleteDialogOpen(true);
  };

  const handleSubmit = () => {
    if (!formData.lob_name.trim()) {
      showToast('error', 'LOB name is required');
      return;
    }

    if (editingLOB) {
      updateMutation.mutate({
        lobId: editingLOB.lob_id,
        data: { lob_name: formData.lob_name },
      });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleConfirmDelete = () => {
    if (lobToDelete) {
      deleteMutation.mutate(lobToDelete.lob_id);
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load LOBs: {(error as Error).message}
        </Alert>
      </Box>
    );
  }

  const lobs = lobsData?.lobs || [];
  const paginatedLOBs = lobs.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        <BusinessIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
        Lines of Business Management
      </Typography>

      {/* Stats Cards - Simplified layout */}
      {statsData && (
        <Box display="flex" gap={2} mb={3} flexWrap="wrap">
          <Card sx={{ minWidth: 200 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total LOBs
              </Typography>
              <Typography variant="h5">
                {statsData.total_lobs}
              </Typography>
            </CardContent>
          </Card>
          <Card sx={{ minWidth: 200 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Users
              </Typography>
              <Typography variant="h5">
                {Object.values(statsData.users_by_lob || {}).reduce((a: number, b: number) => a + b, 0)}
              </Typography>
            </CardContent>
          </Card>
          <Card sx={{ minWidth: 200 }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Reports
              </Typography>
              <Typography variant="h5">
                {Object.values(statsData.reports_by_lob || {}).reduce((a: number, b: number) => a + b, 0)}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">
          Lines of Business ({lobs.length})
        </Typography>
        <Box>
          <Button
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <PermissionGate resource="lobs" action="create">
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreate}
            >
              Add LOB
            </Button>
          </PermissionGate>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>LOB ID</TableCell>
              <TableCell>LOB Name</TableCell>
              <TableCell>Users</TableCell>
              <TableCell>Reports</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : (
              paginatedLOBs.map((lob) => (
                <TableRow key={lob.lob_id}>
                  <TableCell>
                    <Chip label={lob.lob_id} size="small" />
                  </TableCell>
                  <TableCell>
                    <Typography variant="subtitle2">{lob.lob_name}</Typography>
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={lob.user_count || 0} 
                      size="small" 
                      color="primary"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={lob.report_count || 0} 
                      size="small" 
                      color="secondary"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(lob.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="right">
                    {hasPermission('lobs', 'update') && (
                      <Tooltip title="Edit LOB">
                        <IconButton
                          size="small"
                          onClick={() => handleEdit(lob)}
                          color="primary"
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    {hasPermission('lobs', 'delete') && (
                      <Tooltip title="Delete LOB">
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(lob)}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={lobs.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingLOB ? 'Edit LOB' : 'Create New LOB'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="LOB Name"
            fullWidth
            variant="outlined"
            value={formData.lob_name}
            onChange={(e) => setFormData({ ...formData, lob_name: e.target.value })}
            helperText="Enter a unique name for the Line of Business"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending ? (
              <CircularProgress size={20} />
            ) : (
              editingLOB ? 'Update' : 'Create'
            )}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete LOB</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{lobToDelete?.lob_name}"?
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone. The LOB can only be deleted if it has no associated users or reports.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleConfirmDelete}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? <CircularProgress size={20} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}; 