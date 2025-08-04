import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
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
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
  LinearProgress,
  Chip,
  Tabs,
  Tab,
  FormControlLabel,
  Switch,
  Stepper,
  Step,
  StepLabel,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  CircularProgress,
  Tooltip,
  Badge,
  FormHelperText,
  InputAdornment,
  Collapse,
  Slider,
  FormLabel,
  RadioGroup,
  Radio,
  Divider,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  CloudUpload as UploadIcon,
  Schedule as ScheduleIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Timer as TimerIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  DataUsage as DataUsageIcon,
  Timeline as TimelineIcon,
  BugReport as BugReportIcon,
  Rule as RuleIcon,
  Preview as PreviewIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { format } from 'date-fns';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

interface ProfilingConfiguration {
  id: number;
  name: string;
  description?: string;
  source_type: 'file_upload' | 'database_direct' | 'api' | 'streaming';
  profiling_mode: 'full_scan' | 'sample_based' | 'incremental' | 'streaming';
  data_source_id?: number;
  file_upload_id?: number;
  use_timeframe: boolean;
  timeframe_start?: string;
  timeframe_end?: string;
  timeframe_column?: string;
  sample_size?: number;
  sample_percentage?: number;
  sample_method: string;
  is_scheduled: boolean;
  schedule_cron?: string;
  last_run_at?: string;
  created_at: string;
}

interface ProfilingJob {
  id: number;
  configuration_id: number;
  job_id: string;
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  total_records?: number;
  records_processed?: number;
  processing_rate?: number;
  data_quality_score?: number;
  anomalies_detected?: number;
  error_message?: string;
}

interface DataSource {
  id: number;
  name: string;
  source_type: string;
  connection_details: any;
}

interface AttributeProfileResult {
  id: number;
  attribute_name: string;
  overall_quality_score: number;
  completeness_score: number;
  validity_score: number;
  consistency_score: number;
  uniqueness_score: number;
  null_percentage: number;
  distinct_count: number;
  anomaly_count: number;
  outliers_detected: number;
}

const profilingModes = [
  { value: 'full_scan', label: 'Full Scan', description: 'Process all records' },
  { value: 'sample_based', label: 'Sample Based', description: 'Process a sample of records' },
  { value: 'incremental', label: 'Incremental', description: 'Process only new/changed records' },
  { value: 'streaming', label: 'Streaming', description: 'Real-time continuous profiling' },
];

const sampleMethods = [
  { value: 'random', label: 'Random', description: 'Random sampling' },
  { value: 'stratified', label: 'Stratified', description: 'Stratified by key columns' },
  { value: 'systematic', label: 'Systematic', description: 'Every Nth record' },
  { value: 'anomaly_based', label: 'Anomaly Based', description: 'Focus on anomalies' },
  { value: 'boundary_conditions', label: 'Boundary Conditions', description: 'Edge cases' },
];

export const EnhancedDataProfiling: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const auth = useAuth();
  const [configurations, setConfigurations] = useState<ProfilingConfiguration[]>([]);
  const [jobs, setJobs] = useState<ProfilingJob[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<ProfilingConfiguration | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [previewData, setPreviewData] = useState<any>(null);
  const [selectedConfig, setSelectedConfig] = useState<ProfilingConfiguration | null>(null);
  const [profileResults, setProfileResults] = useState<AttributeProfileResult[]>([]);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    source_type: 'database_direct' as const,
    profiling_mode: 'sample_based' as const,
    data_source_id: null as number | null,
    file_upload_id: null as number | null,
    use_timeframe: false,
    timeframe_start: null as Date | null,
    timeframe_end: null as Date | null,
    timeframe_column: '',
    sample_size: null as number | null,
    sample_percentage: 10,
    sample_method: 'random',
    partition_column: '',
    partition_count: 10,
    max_memory_mb: 1024,
    custom_query: '',
    table_name: '',
    schema_name: '',
    where_clause: '',
    exclude_columns: [] as string[],
    include_columns: [] as string[],
    profile_relationships: true,
    profile_distributions: true,
    profile_patterns: true,
    detect_anomalies: true,
    is_scheduled: false,
    schedule_cron: '',
  });

  // Load initial data
  useEffect(() => {
    loadData();
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  }, [cycleId, reportId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Load configurations
      const configsResponse = await axios.get(
        `/api/v1/data-profiling-enhanced/cycles/${cycleId}/reports/${reportId}/profiling-configurations`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setConfigurations(configsResponse.data);
      
      // Load jobs
      const jobsResponse = await axios.get(
        `/api/v1/data-profiling-enhanced/cycles/${cycleId}/reports/${reportId}/profiling-jobs`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setJobs(jobsResponse.data);
      
      // Load data sources
      const dataSourcesResponse = await axios.get(
        `/api/v1/planning/cycles/${cycleId}/reports/${reportId}/data-sources`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setDataSources(dataSourcesResponse.data);
      
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handlePreviewData = async () => {
    if (!formData.data_source_id && formData.source_type === 'database_direct') {
      setError('Please select a data source');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      // First save the configuration
      const configData = {
        ...formData,
        timeframe_start: formData.timeframe_start?.toISOString(),
        timeframe_end: formData.timeframe_end?.toISOString(),
      };

      const configResponse = await axios.post(
        `/api/v1/data-profiling-enhanced/cycles/${cycleId}/reports/${reportId}/profiling-configurations`,
        configData,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const configId = configResponse.data.id;

      // Then get preview
      const previewResponse = await axios.post(
        `/api/v1/data-profiling-enhanced/cycles/${cycleId}/reports/${reportId}/profiling-configurations/${configId}/preview`,
        { limit: 10 },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setPreviewData(previewResponse.data);
      setActiveStep(1);
    } catch (err: any) {
      console.error('Error getting preview:', err);
      setError(err.response?.data?.detail || 'Failed to get preview');
    }
  };

  const handleStartProfiling = async (configId: number) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `/api/v1/data-profiling-enhanced/cycles/${cycleId}/reports/${reportId}/profiling-configurations/${configId}/start`,
        { run_async: true },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      setSuccess('Profiling job started successfully');
      loadData();
      
      // Start auto-refresh for job progress
      const interval = setInterval(() => {
        loadData();
      }, 5000);
      setRefreshInterval(interval);
      
    } catch (err: any) {
      console.error('Error starting profiling:', err);
      setError(err.response?.data?.detail || 'Failed to start profiling');
    }
  };

  const handleCancelJob = async (jobId: number) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `/api/v1/data-profiling-enhanced/cycles/${cycleId}/reports/${reportId}/profiling-jobs/${jobId}/cancel`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      setSuccess('Profiling job cancelled');
      loadData();
    } catch (err: any) {
      console.error('Error cancelling job:', err);
      setError(err.response?.data?.detail || 'Failed to cancel job');
    }
  };

  const handleViewResults = async (jobId: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `/api/v1/data-profiling-enhanced/cycles/${cycleId}/reports/${reportId}/profiling-jobs/${jobId}/results`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      setProfileResults(response.data);
      setTabValue(2); // Switch to results tab
    } catch (err: any) {
      console.error('Error loading results:', err);
      setError(err.response?.data?.detail || 'Failed to load results');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      source_type: 'database_direct',
      profiling_mode: 'sample_based',
      data_source_id: null,
      file_upload_id: null,
      use_timeframe: false,
      timeframe_start: null,
      timeframe_end: null,
      timeframe_column: '',
      sample_size: null,
      sample_percentage: 10,
      sample_method: 'random',
      partition_column: '',
      partition_count: 10,
      max_memory_mb: 1024,
      custom_query: '',
      table_name: '',
      schema_name: '',
      where_clause: '',
      exclude_columns: [],
      include_columns: [],
      profile_relationships: true,
      profile_distributions: true,
      profile_patterns: true,
      detect_anomalies: true,
      is_scheduled: false,
      schedule_cron: '',
    });
    setActiveStep(0);
    setPreviewData(null);
    setEditingConfig(null);
  };

  const getJobStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'running':
        return <CircularProgress size={20} />;
      case 'cancelled':
        return <StopIcon color="action" />;
      default:
        return <TimerIcon color="action" />;
    }
  };

  const getQualityScoreColor = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'warning';
    return 'error';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5">Enhanced Data Profiling</Typography>
          <Box>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setDialogOpen(true)}
              sx={{ mr: 2 }}
            >
              New Configuration
            </Button>
            <IconButton onClick={loadData}>
              <RefreshIcon />
            </IconButton>
          </Box>
        </Box>

        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} sx={{ mb: 3 }}>
          <Tab label="Configurations" />
          <Tab label="Jobs" />
          <Tab label="Results" />
        </Tabs>

        {/* Configurations Tab */}
        {tabValue === 0 && (
          <Grid container spacing={3}>
            {configurations.map((config) => (
              <Grid key={config.id} size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          {config.name}
                        </Typography>
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          {config.description}
                        </Typography>
                        <Box display="flex" gap={1} mt={1}>
                          <Chip
                            size="small"
                            label={config.source_type.replace('_', ' ')}
                            icon={<StorageIcon />}
                          />
                          <Chip
                            size="small"
                            label={config.profiling_mode.replace('_', ' ')}
                            icon={<DataUsageIcon />}
                          />
                          {config.is_scheduled && (
                            <Chip
                              size="small"
                              label="Scheduled"
                              icon={<ScheduleIcon />}
                              color="primary"
                            />
                          )}
                        </Box>
                      </Box>
                      <Box>
                        <IconButton
                          size="small"
                          onClick={() => handleStartProfiling(config.id)}
                        >
                          <PlayIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => {
                            setEditingConfig(config);
                            setDialogOpen(true);
                          }}
                        >
                          <EditIcon />
                        </IconButton>
                      </Box>
                    </Box>
                    {config.last_run_at && (
                      <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
                        Last run: {format(new Date(config.last_run_at), 'PPp')}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {/* Jobs Tab */}
        {tabValue === 1 && (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Job ID</TableCell>
                  <TableCell>Configuration</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Quality Score</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {jobs.map((job) => {
                  const config = configurations.find(c => c.id === job.configuration_id);
                  const progress = job.total_records
                    ? (job.records_processed || 0) / job.total_records * 100
                    : 0;

                  return (
                    <TableRow key={job.id}>
                      <TableCell>
                        <Typography variant="caption" fontFamily="monospace">
                          {job.job_id}
                        </Typography>
                      </TableCell>
                      <TableCell>{config?.name || 'Unknown'}</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getJobStatusIcon(job.status)}
                          <Typography variant="body2">
                            {job.status.replace('_', ' ')}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {job.status === 'running' && (
                          <Box sx={{ width: 100 }}>
                            <LinearProgress
                              variant="determinate"
                              value={progress}
                            />
                            <Typography variant="caption">
                              {progress.toFixed(0)}%
                            </Typography>
                          </Box>
                        )}
                      </TableCell>
                      <TableCell>
                        {job.duration_seconds && (
                          <Typography variant="body2">
                            {Math.floor(job.duration_seconds / 60)}m {job.duration_seconds % 60}s
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {job.data_quality_score && (
                          <Chip
                            label={`${job.data_quality_score.toFixed(1)}%`}
                            color={getQualityScoreColor(job.data_quality_score)}
                            size="small"
                          />
                        )}
                      </TableCell>
                      <TableCell align="right">
                        {job.status === 'running' && (
                          <IconButton
                            size="small"
                            onClick={() => handleCancelJob(job.id)}
                          >
                            <StopIcon />
                          </IconButton>
                        )}
                        {job.status === 'completed' && (
                          <Button
                            size="small"
                            onClick={() => handleViewResults(job.id)}
                          >
                            View Results
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {/* Results Tab */}
        {tabValue === 2 && (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell width="40px"></TableCell>
                  <TableCell>Attribute</TableCell>
                  <TableCell>Quality Score</TableCell>
                  <TableCell>Completeness</TableCell>
                  <TableCell>Validity</TableCell>
                  <TableCell>Anomalies</TableCell>
                  <TableCell>Outliers</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {profileResults.map((result) => {
                  const isExpanded = expandedRows.has(result.id);
                  
                  return (
                    <React.Fragment key={result.id}>
                      <TableRow>
                        <TableCell>
                          <IconButton
                            size="small"
                            onClick={() => {
                              const newExpanded = new Set(expandedRows);
                              if (isExpanded) {
                                newExpanded.delete(result.id);
                              } else {
                                newExpanded.add(result.id);
                              }
                              setExpandedRows(newExpanded);
                            }}
                          >
                            {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </IconButton>
                        </TableCell>
                        <TableCell>{result.attribute_name}</TableCell>
                        <TableCell>
                          <Chip
                            label={`${result.overall_quality_score.toFixed(1)}%`}
                            color={getQualityScoreColor(result.overall_quality_score)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <LinearProgress
                            variant="determinate"
                            value={result.completeness_score}
                            sx={{ width: 60, mr: 1, display: 'inline-block' }}
                          />
                          {result.completeness_score.toFixed(0)}%
                        </TableCell>
                        <TableCell>
                          <LinearProgress
                            variant="determinate"
                            value={result.validity_score}
                            sx={{ width: 60, mr: 1, display: 'inline-block' }}
                          />
                          {result.validity_score.toFixed(0)}%
                        </TableCell>
                        <TableCell>
                          <Badge badgeContent={result.anomaly_count} color="warning">
                            <BugReportIcon />
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge badgeContent={result.outliers_detected} color="error">
                            <TimelineIcon />
                          </Badge>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell colSpan={7} sx={{ py: 0 }}>
                          <Collapse in={isExpanded}>
                            <Box p={2} bgcolor="grey.50">
                              <Grid container spacing={2}>
                                <Grid size={{ xs: 12, md: 6 }}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Data Quality Scores
                                  </Typography>
                                  <List dense>
                                    <ListItem>
                                      <ListItemText primary="Completeness" />
                                      <ListItemSecondaryAction>
                                        {result.completeness_score.toFixed(1)}%
                                      </ListItemSecondaryAction>
                                    </ListItem>
                                    <ListItem>
                                      <ListItemText primary="Validity" />
                                      <ListItemSecondaryAction>
                                        {result.validity_score.toFixed(1)}%
                                      </ListItemSecondaryAction>
                                    </ListItem>
                                    <ListItem>
                                      <ListItemText primary="Consistency" />
                                      <ListItemSecondaryAction>
                                        {result.consistency_score.toFixed(1)}%
                                      </ListItemSecondaryAction>
                                    </ListItem>
                                    <ListItem>
                                      <ListItemText primary="Uniqueness" />
                                      <ListItemSecondaryAction>
                                        {result.uniqueness_score.toFixed(1)}%
                                      </ListItemSecondaryAction>
                                    </ListItem>
                                  </List>
                                </Grid>
                                <Grid size={{ xs: 12, md: 6 }}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Statistics
                                  </Typography>
                                  <List dense>
                                    <ListItem>
                                      <ListItemText primary="Null Percentage" />
                                      <ListItemSecondaryAction>
                                        {result.null_percentage.toFixed(2)}%
                                      </ListItemSecondaryAction>
                                    </ListItem>
                                    <ListItem>
                                      <ListItemText primary="Distinct Values" />
                                      <ListItemSecondaryAction>
                                        {result.distinct_count.toLocaleString()}
                                      </ListItemSecondaryAction>
                                    </ListItem>
                                    <ListItem>
                                      <ListItemText primary="Anomalies" />
                                      <ListItemSecondaryAction>
                                        {result.anomaly_count}
                                      </ListItemSecondaryAction>
                                    </ListItem>
                                    <ListItem>
                                      <ListItemText primary="Outliers" />
                                      <ListItemSecondaryAction>
                                        {result.outliers_detected}
                                      </ListItemSecondaryAction>
                                    </ListItem>
                                  </List>
                                </Grid>
                              </Grid>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {/* Configuration Dialog */}
        <Dialog
          open={dialogOpen}
          onClose={() => { setDialogOpen(false); resetForm(); }}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            {editingConfig ? 'Edit Profiling Configuration' : 'Create Profiling Configuration'}
          </DialogTitle>
          <DialogContent>
            <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
              <Step>
                <StepLabel>Configuration</StepLabel>
              </Step>
              <Step>
                <StepLabel>Preview</StepLabel>
              </Step>
              <Step>
                <StepLabel>Confirm</StepLabel>
              </Step>
            </Stepper>

            {activeStep === 0 && (
              <Grid container spacing={3} sx={{ mt: 1 }}>
                <Grid size={{ xs: 12 }}>
                  <TextField
                    fullWidth
                    label="Configuration Name"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    required
                  />
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

                <Grid size={{ xs: 12 }}>
                  <Divider>Data Source</Divider>
                </Grid>

                <Grid size={{ xs: 12, md: 6 }}>
                  <FormControl fullWidth>
                    <InputLabel>Source Type</InputLabel>
                    <Select
                      value={formData.source_type}
                      onChange={(e) => handleInputChange('source_type', e.target.value)}
                      label="Source Type"
                    >
                      <MenuItem value="database_direct">Direct Database</MenuItem>
                      <MenuItem value="file_upload">File Upload</MenuItem>
                      <MenuItem value="api">API</MenuItem>
                      <MenuItem value="streaming">Streaming</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                {formData.source_type === 'database_direct' && (
                  <Grid size={{ xs: 12, md: 6 }}>
                    <FormControl fullWidth required>
                      <InputLabel>Data Source</InputLabel>
                      <Select
                        value={formData.data_source_id || ''}
                        onChange={(e) => handleInputChange('data_source_id', e.target.value)}
                        label="Data Source"
                      >
                        {dataSources.map((ds) => (
                          <MenuItem key={ds.id} value={ds.id}>
                            {ds.name} ({ds.source_type})
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                )}

                <Grid size={{ xs: 12 }}>
                  <Divider>Profiling Settings</Divider>
                </Grid>

                <Grid size={{ xs: 12, md: 6 }}>
                  <FormControl fullWidth>
                    <InputLabel>Profiling Mode</InputLabel>
                    <Select
                      value={formData.profiling_mode}
                      onChange={(e) => handleInputChange('profiling_mode', e.target.value)}
                      label="Profiling Mode"
                    >
                      {profilingModes.map((mode) => (
                        <MenuItem key={mode.value} value={mode.value}>
                          {mode.label}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      {profilingModes.find(m => m.value === formData.profiling_mode)?.description}
                    </FormHelperText>
                  </FormControl>
                </Grid>

                <Grid size={{ xs: 12, md: 6 }}>
                  <FormControl fullWidth>
                    <InputLabel>Sample Method</InputLabel>
                    <Select
                      value={formData.sample_method}
                      onChange={(e) => handleInputChange('sample_method', e.target.value)}
                      label="Sample Method"
                    >
                      {sampleMethods.map((method) => (
                        <MenuItem key={method.value} value={method.value}>
                          {method.label}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      {sampleMethods.find(m => m.value === formData.sample_method)?.description}
                    </FormHelperText>
                  </FormControl>
                </Grid>

                {formData.profiling_mode === 'sample_based' && (
                  <>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <TextField
                        fullWidth
                        label="Sample Size"
                        type="number"
                        value={formData.sample_size || ''}
                        onChange={(e) => handleInputChange('sample_size', e.target.value ? parseInt(e.target.value) : null)}
                        helperText="Number of records to sample"
                      />
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <FormControl fullWidth>
                        <FormLabel>Sample Percentage</FormLabel>
                        <Slider
                          value={formData.sample_percentage}
                          onChange={(e, v) => handleInputChange('sample_percentage', v)}
                          valueLabelDisplay="on"
                          step={5}
                          marks
                          min={5}
                          max={100}
                        />
                      </FormControl>
                    </Grid>
                  </>
                )}

                <Grid size={{ xs: 12 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.use_timeframe}
                        onChange={(e) => handleInputChange('use_timeframe', e.target.checked)}
                      />
                    }
                    label="Use Timeframe"
                  />
                </Grid>

                {formData.use_timeframe && (
                  <>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <TextField
                        fullWidth
                        label="Timeframe Column"
                        value={formData.timeframe_column}
                        onChange={(e) => handleInputChange('timeframe_column', e.target.value)}
                        helperText="Column to use for time filtering"
                      />
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <DateTimePicker
                        label="Start Time"
                        value={formData.timeframe_start}
                        onChange={(v) => handleInputChange('timeframe_start', v)}
                        slotProps={{
                          textField: { fullWidth: true }
                        }}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <DateTimePicker
                        label="End Time"
                        value={formData.timeframe_end}
                        onChange={(v) => handleInputChange('timeframe_end', v)}
                        slotProps={{
                          textField: { fullWidth: true }
                        }}
                      />
                    </Grid>
                  </>
                )}

                <Grid size={{ xs: 12 }}>
                  <Divider>Advanced Options</Divider>
                </Grid>

                <Grid size={{ xs: 12, md: 3 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.profile_relationships}
                        onChange={(e) => handleInputChange('profile_relationships', e.target.checked)}
                      />
                    }
                    label="Profile Relationships"
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.profile_distributions}
                        onChange={(e) => handleInputChange('profile_distributions', e.target.checked)}
                      />
                    }
                    label="Profile Distributions"
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.profile_patterns}
                        onChange={(e) => handleInputChange('profile_patterns', e.target.checked)}
                      />
                    }
                    label="Profile Patterns"
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.detect_anomalies}
                        onChange={(e) => handleInputChange('detect_anomalies', e.target.checked)}
                      />
                    }
                    label="Detect Anomalies"
                  />
                </Grid>
              </Grid>
            )}

            {activeStep === 1 && previewData && (
              <Box>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Preview of data to be profiled. Total records: {previewData.total_records?.toLocaleString()}
                </Alert>
                <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        {previewData.columns?.map((col: any) => (
                          <TableCell key={col.name}>
                            {col.name}
                            <Typography variant="caption" display="block">
                              {col.type}
                            </Typography>
                          </TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {previewData.preview_records?.map((row: any, idx: number) => (
                        <TableRow key={idx}>
                          {previewData.columns?.map((col: any) => (
                            <TableCell key={col.name}>
                              {row[col.name]?.toString() || '-'}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Estimated profiling time: {previewData.estimated_profiling_time} seconds
                </Typography>
              </Box>
            )}

            {activeStep === 2 && (
              <Box>
                <Alert severity="success" sx={{ mb: 2 }}>
                  Configuration is ready. Click "Start Profiling" to begin.
                </Alert>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Configuration Name"
                      secondary={formData.name}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Source Type"
                      secondary={formData.source_type}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Profiling Mode"
                      secondary={formData.profiling_mode}
                    />
                  </ListItem>
                  {previewData && (
                    <ListItem>
                      <ListItemText
                        primary="Total Records"
                        secondary={previewData.total_records?.toLocaleString()}
                      />
                    </ListItem>
                  )}
                </List>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => { setDialogOpen(false); resetForm(); }}>
              Cancel
            </Button>
            {activeStep > 0 && (
              <Button onClick={() => setActiveStep(activeStep - 1)}>
                Back
              </Button>
            )}
            {activeStep === 0 && (
              <Button
                variant="contained"
                onClick={handlePreviewData}
                disabled={!formData.name || (formData.source_type === 'database_direct' && !formData.data_source_id)}
              >
                Next: Preview
              </Button>
            )}
            {activeStep === 1 && (
              <Button
                variant="contained"
                onClick={() => setActiveStep(2)}
              >
                Next: Confirm
              </Button>
            )}
            {activeStep === 2 && (
              <Button
                variant="contained"
                color="primary"
                onClick={() => {
                  // Start profiling with the created config
                  setDialogOpen(false);
                  resetForm();
                  loadData();
                }}
              >
                Start Profiling
              </Button>
            )}
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
    </LocalizationProvider>
  );
};