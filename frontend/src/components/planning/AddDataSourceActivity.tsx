import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Alert,
  Snackbar,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  FormHelperText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  CloudUpload as CloudUploadIcon,
  Storage as StorageIcon,
  Api as ApiIcon,
  FolderOpen as FolderOpenIcon,
  PlayArrow as PlayArrowIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';

interface DataSource {
  id: number;
  name: string;
  description?: string;
  source_type: string;
  is_active: boolean;
  connection_config: any;
  auth_type?: string;
  auth_config?: any;
  refresh_schedule?: string;
  last_sync_at?: string;
  last_sync_status?: string;
  last_sync_message?: string;
  validation_rules?: any;
  created_at: string;
  updated_at: string;
}

const dataSourceTypes = [
  { value: 'postgresql', label: 'PostgreSQL', icon: <StorageIcon /> },
  { value: 'mysql', label: 'MySQL', icon: <StorageIcon /> },
  { value: 'oracle', label: 'Oracle', icon: <StorageIcon /> },
  { value: 'sqlserver', label: 'SQL Server', icon: <StorageIcon /> },
  { value: 'mongodb', label: 'MongoDB', icon: <StorageIcon /> },
  { value: 'csv', label: 'CSV File', icon: <FolderOpenIcon /> },
  { value: 'excel', label: 'Excel File', icon: <FolderOpenIcon /> },
  { value: 'api', label: 'REST API', icon: <ApiIcon /> },
  { value: 'sftp', label: 'SFTP', icon: <CloudUploadIcon /> },
  { value: 's3', label: 'Amazon S3', icon: <CloudUploadIcon /> },
];

const authTypes = [
  { value: 'basic', label: 'Basic Authentication' },
  { value: 'oauth', label: 'OAuth 2.0' },
  { value: 'api_key', label: 'API Key' },
  { value: 'certificate', label: 'Certificate' },
];

interface AddDataSourceActivityProps {
  cycleId?: string;
  reportId?: string;
}

export const AddDataSourceActivity: React.FC<AddDataSourceActivityProps> = (props) => {
  const params = useParams<{ cycleId: string; reportId: string }>();
  const cycleId = props.cycleId || params.cycleId;
  const reportId = props.reportId || params.reportId;
  const auth = useAuth();
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingDataSource, setEditingDataSource] = useState<DataSource | null>(null);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionTestResult, setConnectionTestResult] = useState<{success: boolean; message: string} | null>(null);
  const [activityStatus, setActivityStatus] = useState<string | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    source_type: 'postgresql',
    auth_type: 'basic',
    connection_config: {
      host: '',
      port: '',
      database: '',
      schema: '',
      table_name: '',
    },
    auth_config: {
      username: '',
      password: '',
    },
    refresh_schedule: '',
    validation_rules: {},
  });

  // Load data sources
  const loadDataSources = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(
        `/planning/cycles/${cycleId}/reports/${reportId}/data-sources`
      );
      setDataSources(response.data);
      
      // Load activity status
      try {
        const statusResponse = await apiClient.get(
          `/status/cycles/${cycleId}/reports/${reportId}/phases/Planning/status`
        );
        const activities = statusResponse.data?.activities || [];
        const addDataSourceActivity = activities.find((a: any) => a.activity_code === 'add_data_source');
        if (addDataSourceActivity) {
          setActivityStatus(addDataSourceActivity.status);
        }
      } catch (statusErr) {
        console.error('Error loading activity status:', statusErr);
        // Non-critical error, continue
      }
    } catch (err: any) {
      console.error('Error loading data sources:', err);
      console.error('Error response:', err.response);
      if (err.response?.status === 404) {
        setError('Data sources endpoint not found. Please ensure backend is running.');
      } else if (err.response?.status === 403) {
        setError('Authentication failed. Please login again.');
      } else {
        setError(err.response?.data?.detail || 'Failed to load data sources');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDataSources();
  }, [cycleId, reportId]);

  const handleInputChange = (field: string, value: any) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...(prev as any)[parent],
          [child]: value,
        },
      }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
  };

  const getConnectionFields = () => {
    switch (formData.source_type) {
      case 'postgresql':
      case 'mysql':
      case 'oracle':
      case 'sqlserver':
        return (
          <>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Host"
                value={(formData.connection_config as any).host}
                onChange={(e) => handleInputChange('connection_config.host', e.target.value)}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Port"
                type="number"
                value={(formData.connection_config as any).port}
                onChange={(e) => handleInputChange('connection_config.port', e.target.value)}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Database"
                value={(formData.connection_config as any).database}
                onChange={(e) => handleInputChange('connection_config.database', e.target.value)}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Schema (optional)"
                value={(formData.connection_config as any).schema}
                onChange={(e) => handleInputChange('connection_config.schema', e.target.value)}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Table Name"
                value={(formData.connection_config as any).table_name || ''}
                onChange={(e) => handleInputChange('connection_config.table_name', e.target.value)}
                helperText="The table containing data to be profiled"
                required
              />
            </Grid>
          </>
        );
      case 'api':
        return (
          <>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Base URL"
                value={(formData.connection_config as any).base_url || ''}
                onChange={(e) => handleInputChange('connection_config.base_url', e.target.value)}
                required
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Headers (JSON)"
                multiline
                rows={3}
                value={(formData.connection_config as any).headers || '{}'}
                onChange={(e) => handleInputChange('connection_config.headers', e.target.value)}
                helperText="Custom headers as JSON object"
              />
            </Grid>
          </>
        );
      case 'csv':
      case 'excel':
        return (
          <Grid size={{ xs: 12 }}>
            <TextField
              fullWidth
              label="File Path"
              value={(formData.connection_config as any).file_path || ''}
              onChange={(e) => handleInputChange('connection_config.file_path', e.target.value)}
              required
              helperText="Path to the file on the server"
            />
          </Grid>
        );
      case 's3':
        return (
          <>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Bucket Name"
                value={(formData.connection_config as any).bucket || ''}
                onChange={(e) => handleInputChange('connection_config.bucket', e.target.value)}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Region"
                value={(formData.connection_config as any).region || ''}
                onChange={(e) => handleInputChange('connection_config.region', e.target.value)}
                required
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Key Prefix (optional)"
                value={(formData.connection_config as any).prefix || ''}
                onChange={(e) => handleInputChange('connection_config.prefix', e.target.value)}
              />
            </Grid>
          </>
        );
      default:
        return null;
    }
  };

  const getAuthFields = () => {
    switch (formData.auth_type) {
      case 'basic':
        return (
          <>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Username"
                value={(formData.auth_config as any).username}
                onChange={(e) => handleInputChange('auth_config.username', e.target.value)}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={(formData.auth_config as any).password}
                onChange={(e) => handleInputChange('auth_config.password', e.target.value)}
                required
              />
            </Grid>
          </>
        );
      case 'api_key':
        return (
          <>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="API Key"
                value={(formData.auth_config as any).api_key || ''}
                onChange={(e) => handleInputChange('auth_config.api_key', e.target.value)}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Key Location"
                select
                value={(formData.auth_config as any).key_location || 'header'}
                onChange={(e) => handleInputChange('auth_config.key_location', e.target.value)}
              >
                <MenuItem value="header">Header</MenuItem>
                <MenuItem value="query">Query Parameter</MenuItem>
              </TextField>
            </Grid>
          </>
        );
      case 'oauth':
        return (
          <>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Client ID"
                value={(formData.auth_config as any).client_id || ''}
                onChange={(e) => handleInputChange('auth_config.client_id', e.target.value)}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Client Secret"
                type="password"
                value={(formData.auth_config as any).client_secret || ''}
                onChange={(e) => handleInputChange('auth_config.client_secret', e.target.value)}
                required
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Token URL"
                value={(formData.auth_config as any).token_url || ''}
                onChange={(e) => handleInputChange('auth_config.token_url', e.target.value)}
                required
              />
            </Grid>
          </>
        );
      default:
        return null;
    }
  };

  const handleTestConnection = async () => {
    try {
      setTestingConnection(true);
      setConnectionTestResult(null);
      
      const url = `/planning/cycles/${cycleId}/reports/${reportId}/data-sources/test-connection`;
      console.log('Testing connection with URL:', url);
      console.log('Request data:', {
        source_type: formData.source_type,
        connection_config: formData.connection_config,
        auth_type: formData.auth_type,
        auth_config: formData.auth_config
      });
      
      const response = await apiClient.post(
        url,
        {
          source_type: formData.source_type,
          connection_config: formData.connection_config,
          auth_type: formData.auth_type,
          auth_config: formData.auth_config
        }
      );
      
      setConnectionTestResult({
        success: response.data.success,
        message: response.data.message || (response.data.success ? 'Connection successful!' : 'Connection failed')
      });
    } catch (err: any) {
      console.error('Error testing connection:', err);
      console.error('Error response:', err.response);
      setConnectionTestResult({
        success: false,
        message: err.response?.data?.detail || 'Failed to test connection'
      });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const endpoint = editingDataSource
        ? `/planning/cycles/${cycleId}/reports/${reportId}/data-sources/${editingDataSource.id}`
        : `/planning/cycles/${cycleId}/reports/${reportId}/data-sources`;
      
      const method = editingDataSource ? 'put' : 'post';
      
      await apiClient[method](endpoint, formData);
      
      setSuccess(editingDataSource ? 'Data source updated successfully' : 'Data source created successfully');
      setDialogOpen(false);
      resetForm();
      loadDataSources();
    } catch (err) {
      console.error('Error saving data source:', err);
      setError('Failed to save data source');
    }
  };

  const handleEdit = (dataSource: DataSource) => {
    setEditingDataSource(dataSource);
    setFormData({
      name: dataSource.name,
      description: dataSource.description || '',
      source_type: dataSource.source_type,
      auth_type: dataSource.auth_type || 'basic',
      connection_config: dataSource.connection_config || {},
      auth_config: dataSource.auth_config || {},
      refresh_schedule: dataSource.refresh_schedule || '',
      validation_rules: dataSource.validation_rules || {},
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this data source?')) {
      return;
    }
    
    try {
      await apiClient.delete(
        `/planning/cycles/${cycleId}/reports/${reportId}/data-sources/${id}`
      );
      setSuccess('Data source deleted successfully');
      loadDataSources();
    } catch (err) {
      console.error('Error deleting data source:', err);
      setError('Failed to delete data source');
    }
  };

  const handleCompleteActivity = async () => {
    try {
      await apiClient.post(`/activity-management/activities/add_data_source/complete`, {
        cycle_id: cycleId,
        report_id: reportId,
        phase_name: 'Planning'
      });
      setSuccess('Activity completed successfully');
      setActivityStatus('completed');
      // Reload to get updated status
      loadDataSources();
    } catch (err: any) {
      console.error('Error completing activity:', err);
      setError(err.response?.data?.detail || 'Failed to complete activity');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      source_type: 'postgresql',
      auth_type: 'basic',
      connection_config: {
        host: '',
        port: '',
        database: '',
        schema: '',
        table_name: '',
      },
      auth_config: {
        username: '',
        password: '',
      },
      refresh_schedule: '',
      validation_rules: {},
    });
    setEditingDataSource(null);
    setConnectionTestResult(null);
  };

  const getSourceTypeIcon = (sourceType: string) => {
    const type = dataSourceTypes.find(t => t.value === sourceType);
    return type?.icon || <StorageIcon />;
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Data Source Configuration</Typography>
        <Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setDialogOpen(true)}
            sx={{ mr: 2 }}
          >
            Add Data Source
          </Button>
          <Button
            variant="contained"
            color="success"
            startIcon={<CheckCircleIcon />}
            onClick={handleCompleteActivity}
            disabled={dataSources.length === 0 || activityStatus === 'completed'}
          >
            {activityStatus === 'completed' ? 'Activity Completed' : 'Complete Activity'}
          </Button>
        </Box>
      </Box>

      {/* Instructions */}
      <Alert severity="info" sx={{ mb: 3 }}>
        Configure data source connections for this report. You can set up database connections, 
        file locations, or API endpoints that will be used for data validation and testing.
      </Alert>

      {/* Data Sources Table */}
      {dataSources.length > 0 ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last Sync</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {dataSources.map((dataSource) => (
                <TableRow key={dataSource.id}>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      {getSourceTypeIcon(dataSource.source_type)}
                      <Typography>{dataSource.name}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={dataSourceTypes.find(t => t.value === dataSource.source_type)?.label || dataSource.source_type}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{dataSource.description || '-'}</TableCell>
                  <TableCell>
                    {dataSource.last_sync_status ? (
                      <Chip
                        label={dataSource.last_sync_status}
                        size="small"
                        color={dataSource.last_sync_status === 'success' ? 'success' : 'error'}
                      />
                    ) : (
                      <Chip label="Not synced" size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    {dataSource.last_sync_at ? new Date(dataSource.last_sync_at).toLocaleString() : '-'}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton onClick={() => handleEdit(dataSource)} size="small">
                      <EditIcon />
                    </IconButton>
                    <IconButton onClick={() => handleDelete(dataSource.id)} size="small" color="error">
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="textSecondary">
            No data sources configured yet. Click "Add Data Source" to get started.
          </Typography>
        </Paper>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingDataSource ? 'Edit Data Source' : 'Add New Data Source'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            {/* Basic Information */}
            <Grid size={{ xs: 12 }}>
              <Typography variant="h6" gutterBottom>
                Basic Information
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth required>
                <InputLabel>Source Type</InputLabel>
                <Select
                  value={formData.source_type}
                  onChange={(e) => handleInputChange('source_type', e.target.value)}
                  label="Source Type"
                >
                  {dataSourceTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      <Box display="flex" alignItems="center" gap={1}>
                        {type.icon}
                        {type.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={2}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
              />
            </Grid>

            {/* Connection Configuration */}
            <Grid size={{ xs: 12 }}>
              <Typography variant="h6" gutterBottom>
                Connection Configuration
              </Typography>
            </Grid>
            {getConnectionFields()}

            {/* Authentication */}
            <Grid size={{ xs: 12 }}>
              <Typography variant="h6" gutterBottom>
                Authentication
              </Typography>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>Authentication Type</InputLabel>
                <Select
                  value={formData.auth_type}
                  onChange={(e) => handleInputChange('auth_type', e.target.value)}
                  label="Authentication Type"
                >
                  {authTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            {getAuthFields()}

            {/* Test Connection */}
            <Grid size={{ xs: 12 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={testingConnection ? <CircularProgress size={16} /> : <PlayArrowIcon />}
                  onClick={handleTestConnection}
                  disabled={testingConnection}
                >
                  {testingConnection ? 'Testing...' : 'Test Connection'}
                </Button>
                {connectionTestResult && (
                  <Alert
                    severity={connectionTestResult.success ? 'success' : 'error'}
                    icon={connectionTestResult.success ? <CheckCircleIcon /> : <ErrorIcon />}
                    sx={{ flex: 1 }}
                  >
                    {connectionTestResult.message}
                  </Alert>
                )}
              </Box>
            </Grid>

            {/* Advanced Settings */}
            <Grid size={{ xs: 12 }}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>Advanced Settings</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12 }}>
                      <TextField
                        fullWidth
                        label="Refresh Schedule (Cron Expression)"
                        value={formData.refresh_schedule}
                        onChange={(e) => handleInputChange('refresh_schedule', e.target.value)}
                        helperText="e.g., 0 0 * * * for daily at midnight"
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDialogOpen(false); resetForm(); }}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSubmit}>
            {editingDataSource ? 'Update' : 'Create'}
          </Button>
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