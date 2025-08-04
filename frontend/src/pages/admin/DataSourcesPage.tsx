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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  DataObject as DataObjectIcon,
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  CloudUpload as CloudUploadIcon,
  ViewList as DatabaseIcon,
  Api as ApiIcon,
} from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNotifications } from '../../contexts/NotificationContext';

interface DataSource {
  id: string;
  name: string;
  type: 'database' | 'api' | 'file' | 'cloud';
  description: string;
  connection_string?: string;
  api_endpoint?: string;
  file_path?: string;
  credentials_stored: boolean;
  status: 'active' | 'inactive' | 'error';
  last_tested: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  test_result?: string;
}

interface DataSourceCreate {
  name: string;
  type: 'database' | 'api' | 'file' | 'cloud';
  description: string;
  connection_string?: string;
  api_endpoint?: string;
  file_path?: string;
  credentials?: Record<string, string>;
}

interface DataSourceUpdate {
  name?: string;
  description?: string;
  connection_string?: string;
  api_endpoint?: string;
  file_path?: string;
  credentials?: Record<string, string>;
  status?: 'active' | 'inactive';
}

// Mock data for demonstration - in a real app, this would come from the backend
const mockDataSources: DataSource[] = [
  {
    id: '1',
    name: 'Customer Database',
    type: 'database',
    description: 'Primary customer data repository for KYC testing',
    connection_string: 'postgresql://server:5432/customers',
    credentials_stored: true,
    status: 'active',
    last_tested: '2025-06-03T10:30:00Z',
    created_at: '2025-05-01T10:00:00Z',
    updated_at: '2025-06-01T15:30:00Z',
    created_by: 'admin@example.com',
    test_result: 'Connection successful'
  },
  {
    id: '2',
    name: 'Transaction API',
    type: 'api',
    description: 'Real-time transaction data API for transaction monitoring testing',
    api_endpoint: 'https://api.bank.com/v1/transactions',
    credentials_stored: true,
    status: 'active',
    last_tested: '2025-06-03T09:15:00Z',
    created_at: '2025-05-15T14:20:00Z',
    updated_at: '2025-06-02T11:45:00Z',
    created_by: 'dataowner@example.com',
    test_result: 'API responding correctly'
  },
  {
    id: '3',
    name: 'Compliance Files',
    type: 'file',
    description: 'Static compliance data files for regulatory reporting',
    file_path: '/data/compliance/reports/',
    credentials_stored: false,
    status: 'inactive',
    last_tested: '2025-05-28T16:00:00Z',
    created_at: '2025-04-20T09:30:00Z',
    updated_at: '2025-05-28T16:00:00Z',
    created_by: 'compliance@example.com',
    test_result: 'File access denied'
  }
];

// API functions (mock implementations)
const api = {
  getDataSources: async (): Promise<{ sources: DataSource[]; total: number }> => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    return { sources: mockDataSources, total: mockDataSources.length };
  },

  createDataSource: async (source: DataSourceCreate): Promise<DataSource> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    const newSource: DataSource = {
      id: Date.now().toString(),
      ...source,
      credentials_stored: !!source.credentials,
      status: 'active',
      last_tested: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      created_by: 'current@user.com',
      test_result: 'Pending validation'
    };
    return newSource;
  },

  updateDataSource: async (id: string, source: DataSourceUpdate): Promise<DataSource> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    const existing = mockDataSources.find(s => s.id === id);
    if (!existing) throw new Error('Data source not found');
    
    return {
      ...existing,
      ...source,
      updated_at: new Date().toISOString(),
    };
  },

  deleteDataSource: async (id: string): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
  },

  testDataSource: async (id: string): Promise<{ success: boolean; message: string }> => {
    await new Promise(resolve => setTimeout(resolve, 2000));
    return {
      success: Math.random() > 0.3,
      message: Math.random() > 0.3 ? 'Connection successful' : 'Connection failed: Timeout'
    };
  },
};

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'database': return <DatabaseIcon />;
    case 'api': return <ApiIcon />;
    case 'file': return <StorageIcon />;
    case 'cloud': return <CloudUploadIcon />;
    default: return <DataObjectIcon />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'success';
    case 'inactive': return 'default';
    case 'error': return 'error';
    default: return 'default';
  }
};

const DataSourcesPage: React.FC = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<DataSource | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sourceToDelete, setSourceToDelete] = useState<DataSource | null>(null);
  const [testingSource, setTestingSource] = useState<string | null>(null);
  const [formData, setFormData] = useState<DataSourceCreate>({
    name: '',
    type: 'database',
    description: '',
    connection_string: '',
    api_endpoint: '',
    file_path: '',
  });

  const { showToast } = useNotifications();
  const queryClient = useQueryClient();

  // Queries
  const { data: sourcesData, isLoading, error, refetch } = useQuery({
    queryKey: ['data-sources'],
    queryFn: api.getDataSources,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: api.createDataSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-sources'] });
      setDialogOpen(false);
      resetForm();
      showToast('success', 'Data source created successfully');
    },
    onError: (error: Error) => {
      showToast('error', `Failed to create data source: ${error.message}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: DataSourceUpdate }) =>
      api.updateDataSource(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-sources'] });
      setDialogOpen(false);
      setEditingSource(null);
      resetForm();
      showToast('success', 'Data source updated successfully');
    },
    onError: (error: Error) => {
      showToast('error', `Failed to update data source: ${error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteDataSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-sources'] });
      setDeleteDialogOpen(false);
      setSourceToDelete(null);
      showToast('success', 'Data source deleted successfully');
    },
    onError: (error: Error) => {
      showToast('error', `Failed to delete data source: ${error.message}`);
    },
  });

  const testMutation = useMutation({
    mutationFn: api.testDataSource,
    onSuccess: (result, sourceId) => {
      setTestingSource(null);
      queryClient.invalidateQueries({ queryKey: ['data-sources'] });
      showToast(
        result.success ? 'success' : 'error',
        `Test ${result.success ? 'successful' : 'failed'}: ${result.message}`
      );
    },
    onError: (error: Error, sourceId) => {
      setTestingSource(null);
      showToast('error', `Test failed: ${error.message}`);
    },
  });

  const resetForm = () => {
    setFormData({
      name: '',
      type: 'database',
      description: '',
      connection_string: '',
      api_endpoint: '',
      file_path: '',
    });
  };

  const handleCreate = () => {
    setEditingSource(null);
    resetForm();
    setDialogOpen(true);
  };

  const handleEdit = (source: DataSource) => {
    setEditingSource(source);
    setFormData({
      name: source.name,
      type: source.type,
      description: source.description,
      connection_string: source.connection_string || '',
      api_endpoint: source.api_endpoint || '',
      file_path: source.file_path || '',
    });
    setDialogOpen(true);
  };

  const handleDelete = (source: DataSource) => {
    setSourceToDelete(source);
    setDeleteDialogOpen(true);
  };

  const handleTest = (sourceId: string) => {
    setTestingSource(sourceId);
    testMutation.mutate(sourceId);
  };

  const handleSubmit = () => {
    if (!formData.name.trim()) {
      showToast('error', 'Name is required');
      return;
    }

    if (editingSource) {
      updateMutation.mutate({
        id: editingSource.id,
        data: formData,
      });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleConfirmDelete = () => {
    if (sourceToDelete) {
      deleteMutation.mutate(sourceToDelete.id);
    }
  };

  const sources = sourcesData?.sources || [];
  const paginatedSources = sources.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load data sources. Please try again.
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom display="flex" alignItems="center" gap={2}>
          <DataObjectIcon fontSize="large" />
          Data Sources Management
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            disabled={isLoading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Add Data Source
          </Button>
        </Stack>
      </Box>

      {/* Statistics Cards */}
      <Box display="flex" flexWrap="wrap" gap={3} mb={3}>
        <Box flex="1" minWidth="200px">
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Sources
              </Typography>
              <Typography variant="h4">
                {sources.length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box flex="1" minWidth="200px">
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Active Sources
              </Typography>
              <Typography variant="h4" color="success.main">
                {sources.filter(s => s.status === 'active').length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box flex="1" minWidth="200px">
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Database Sources
              </Typography>
              <Typography variant="h4">
                {sources.filter(s => s.type === 'database').length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box flex="1" minWidth="200px">
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                API Sources
              </Typography>
              <Typography variant="h4">
                {sources.filter(s => s.type === 'api').length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Data Sources Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last Tested</TableCell>
                <TableCell>Created By</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : paginatedSources.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No data sources found
                  </TableCell>
                </TableRow>
              ) : (
                paginatedSources.map((source) => (
                  <TableRow key={source.id} hover>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getTypeIcon(source.type)}
                        <Box>
                          <Typography variant="subtitle2" fontWeight="medium">
                            {source.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ID: {source.id}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={source.type.toUpperCase()}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap style={{ maxWidth: 200 }}>
                        {source.description}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={source.status.toUpperCase()}
                        size="small"
                        color={getStatusColor(source.status) as any}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(source.last_tested).toLocaleDateString()}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {source.test_result}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {source.created_by}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={1}>
                        <Tooltip title="Test Connection">
                          <IconButton
                            size="small"
                            onClick={() => handleTest(source.id)}
                            disabled={testingSource === source.id}
                          >
                            {testingSource === source.id ? (
                              <CircularProgress size={16} />
                            ) : (
                              <RefreshIcon fontSize="small" />
                            )}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            onClick={() => handleEdit(source)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={() => handleDelete(source)}
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={sources.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(parseInt(event.target.value, 10));
            setPage(0);
          }}
        />
      </Paper>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingSource ? 'Edit Data Source' : 'Create Data Source'}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <TextField
              label="Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              fullWidth
              required
            />
            
            <FormControl fullWidth required>
              <InputLabel>Type</InputLabel>
              <Select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
              >
                <MenuItem value="database">Database</MenuItem>
                <MenuItem value="api">API</MenuItem>
                <MenuItem value="file">File System</MenuItem>
                <MenuItem value="cloud">Cloud Storage</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              fullWidth
              multiline
              rows={2}
            />

            {formData.type === 'database' && (
              <TextField
                label="Connection String"
                value={formData.connection_string}
                onChange={(e) => setFormData({ ...formData, connection_string: e.target.value })}
                fullWidth
                placeholder="postgresql://user:password@host:port/database"
              />
            )}

            {formData.type === 'api' && (
              <TextField
                label="API Endpoint"
                value={formData.api_endpoint}
                onChange={(e) => setFormData({ ...formData, api_endpoint: e.target.value })}
                fullWidth
                placeholder="https://api.example.com/v1/"
              />
            )}

            {(formData.type === 'file' || formData.type === 'cloud') && (
              <TextField
                label="File Path"
                value={formData.file_path}
                onChange={(e) => setFormData({ ...formData, file_path: e.target.value })}
                fullWidth
                placeholder="/path/to/files/"
              />
            )}
          </Box>
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
            ) : editingSource ? (
              'Update'
            ) : (
              'Create'
            )}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the data source "{sourceToDelete?.name}"?
            This action cannot be undone.
          </Typography>
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

export default DataSourcesPage; 