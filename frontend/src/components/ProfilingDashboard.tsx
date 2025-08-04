import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
  CircularProgress,
  Stack,
  Divider,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Assessment as AssessmentIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNotifications } from '../contexts/NotificationContext';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface ProfilingJob {
  job_id: string;
  job_name: string;
  cycle_id: number;
  report_id: number;
  strategy: 'full_scan' | 'sampling' | 'streaming' | 'partitioned' | 'incremental';
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress_percent: number;
  total_records: number;
  records_processed: number;
  anomalies_found: number;
  partition_count: number;
  start_time?: string;
  end_time?: string;
  estimated_runtime_minutes?: number;
  memory_usage_mb?: number;
  max_memory_gb: number;
}

interface ProfilingPartition {
  partition_id: string;
  partition_index: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  records_processed: number;
  anomalies_found: number;
  execution_time_seconds?: number;
  assigned_worker?: string;
}

interface ProfilingMetrics {
  records_per_second: number;
  memory_usage_history: Array<{ time: string; usage: number }>;
  anomaly_distribution: Array<{ category: string; count: number }>;
  partition_progress: Array<{ partition: number; progress: number }>;
}

interface ProfilingDashboardProps {
  cycleId: number;
  reportId: number;
}

// Mock API
const api = {
  getProfilingJobs: async (cycleId: number, reportId: number): Promise<ProfilingJob[]> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return [
      {
        job_id: '1',
        job_name: 'Customer Data Full Profiling',
        cycle_id: cycleId,
        report_id: reportId,
        strategy: 'partitioned',
        status: 'running',
        progress_percent: 67,
        total_records: 45000000,
        records_processed: 30150000,
        anomalies_found: 125430,
        partition_count: 10,
        start_time: new Date(Date.now() - 3600000).toISOString(),
        estimated_runtime_minutes: 120,
        memory_usage_mb: 6144,
        max_memory_gb: 8,
      },
      {
        job_id: '2',
        job_name: 'Transaction Incremental Profiling',
        cycle_id: cycleId,
        report_id: reportId,
        strategy: 'incremental',
        status: 'completed',
        progress_percent: 100,
        total_records: 5000000,
        records_processed: 5000000,
        anomalies_found: 23450,
        partition_count: 1,
        start_time: new Date(Date.now() - 7200000).toISOString(),
        end_time: new Date(Date.now() - 3600000).toISOString(),
        estimated_runtime_minutes: 60,
        memory_usage_mb: 2048,
        max_memory_gb: 4,
      },
    ];
  },

  getPartitions: async (jobId: string): Promise<ProfilingPartition[]> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return Array.from({ length: 10 }, (_, i) => ({
      partition_id: `${jobId}-${i}`,
      partition_index: i,
      status: i < 7 ? 'completed' : i === 7 ? 'running' : 'pending',
      records_processed: i < 7 ? 4500000 : i === 7 ? 2250000 : 0,
      anomalies_found: i < 7 ? Math.floor(Math.random() * 20000) : 0,
      execution_time_seconds: i < 7 ? 600 + Math.floor(Math.random() * 300) : undefined,
      assigned_worker: i <= 7 ? `worker-${(i % 4) + 1}` : undefined,
    }));
  },

  getMetrics: async (jobId: string): Promise<ProfilingMetrics> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return {
      records_per_second: 8333,
      memory_usage_history: Array.from({ length: 20 }, (_, i) => ({
        time: `${i * 5}m`,
        usage: 2048 + Math.random() * 4096,
      })),
      anomaly_distribution: [
        { category: 'Null Values', count: 45230 },
        { category: 'Format Violations', count: 32450 },
        { category: 'Range Outliers', count: 28760 },
        { category: 'Duplicates', count: 12340 },
        { category: 'Cross-field Issues', count: 6650 },
      ],
      partition_progress: Array.from({ length: 10 }, (_, i) => ({
        partition: i + 1,
        progress: i < 7 ? 100 : i === 7 ? 50 : 0,
      })),
    };
  },

  startJob: async (config: any): Promise<ProfilingJob> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return {
      job_id: Date.now().toString(),
      job_name: config.job_name,
      cycle_id: config.cycle_id,
      report_id: config.report_id,
      strategy: config.strategy,
      status: 'pending',
      progress_percent: 0,
      total_records: config.estimated_records,
      records_processed: 0,
      anomalies_found: 0,
      partition_count: config.partition_count,
      max_memory_gb: config.max_memory_gb,
    };
  },

  pauseJob: async (jobId: string): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 500));
  },

  resumeJob: async (jobId: string): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 500));
  },

  stopJob: async (jobId: string): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 500));
  },
};

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'running': return <PlayIcon color="primary" />;
    case 'completed': return <CheckCircleIcon color="success" />;
    case 'failed': return <ErrorIcon color="error" />;
    default: return <ScheduleIcon color="action" />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'running': return 'primary';
    case 'completed': return 'success';
    case 'failed': return 'error';
    default: return 'default';
  }
};

const ProfilingDashboard: React.FC<ProfilingDashboardProps> = ({ cycleId, reportId }) => {
  const [selectedJob, setSelectedJob] = useState<ProfilingJob | null>(null);
  const [newJobDialogOpen, setNewJobDialogOpen] = useState(false);
  const [newJobConfig, setNewJobConfig] = useState({
    job_name: '',
    strategy: 'partitioned' as const,
    estimated_records: 10000000,
    partition_count: 10,
    max_memory_gb: 8,
    max_cpu_cores: 4,
  });
  const { showToast } = useNotifications();

  // Queries
  const { data: jobs, isLoading: jobsLoading, refetch: refetchJobs } = useQuery({
    queryKey: ['profiling-jobs', cycleId, reportId],
    queryFn: () => api.getProfilingJobs(cycleId, reportId),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  const { data: partitions } = useQuery({
    queryKey: ['profiling-partitions', selectedJob?.job_id],
    queryFn: () => api.getPartitions(selectedJob!.job_id),
    enabled: !!selectedJob,
    refetchInterval: 5000,
  });

  const { data: metrics } = useQuery({
    queryKey: ['profiling-metrics', selectedJob?.job_id],
    queryFn: () => api.getMetrics(selectedJob!.job_id),
    enabled: !!selectedJob && selectedJob.status === 'running',
    refetchInterval: 2000,
  });

  // Mutations
  const startJobMutation = useMutation({
    mutationFn: api.startJob,
    onSuccess: () => {
      refetchJobs();
      setNewJobDialogOpen(false);
      showToast('success', 'Profiling job started successfully');
    },
    onError: (error: Error) => {
      showToast('error', `Failed to start job: ${error.message}`);
    },
  });

  const pauseJobMutation = useMutation({
    mutationFn: api.pauseJob,
    onSuccess: () => {
      refetchJobs();
      showToast('info', 'Job paused');
    },
  });

  const stopJobMutation = useMutation({
    mutationFn: api.stopJob,
    onSuccess: () => {
      refetchJobs();
      showToast('warning', 'Job stopped');
    },
  });

  useEffect(() => {
    if (jobs && jobs.length > 0 && !selectedJob) {
      setSelectedJob(jobs[0]);
    }
  }, [jobs, selectedJob]);

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = end.getTime() - start.getTime();
    const hours = Math.floor(duration / 3600000);
    const minutes = Math.floor((duration % 3600000) / 60000);
    return `${hours}h ${minutes}m`;
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" display="flex" alignItems="center" gap={1}>
          <AssessmentIcon />
          Data Profiling Dashboard
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetchJobs()}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<PlayIcon />}
            onClick={() => setNewJobDialogOpen(true)}
          >
            New Profiling Job
          </Button>
        </Stack>
      </Box>

      {/* Job Selection and Overview */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Active Jobs</Typography>
            {jobsLoading ? (
              <CircularProgress />
            ) : (
              <Stack spacing={2}>
                {jobs?.map(job => (
                  <Card
                    key={job.job_id}
                    sx={{
                      cursor: 'pointer',
                      border: selectedJob?.job_id === job.job_id ? 2 : 0,
                      borderColor: 'primary.main',
                    }}
                    onClick={() => setSelectedJob(job)}
                  >
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="start">
                        <Box>
                          <Typography variant="subtitle1" fontWeight="medium">
                            {job.job_name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {job.strategy} • {job.partition_count} partitions
                          </Typography>
                        </Box>
                        {getStatusIcon(job.status)}
                      </Box>
                      <Box mt={2}>
                        <Box display="flex" justifyContent="space-between" mb={1}>
                          <Typography variant="caption">Progress</Typography>
                          <Typography variant="caption">{job.progress_percent}%</Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={job.progress_percent}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            )}
          </Paper>
        </Grid>

        {/* Job Details */}
        <Grid size={{ xs: 12, md: 8 }}>
          {selectedJob && (
            <Paper sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Box>
                  <Typography variant="h6">{selectedJob.job_name}</Typography>
                  <Chip
                    label={selectedJob.status.toUpperCase()}
                    color={getStatusColor(selectedJob.status) as any}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                </Box>
                <Stack direction="row" spacing={1}>
                  {selectedJob.status === 'running' && (
                    <>
                      <IconButton onClick={() => pauseJobMutation.mutate(selectedJob.job_id)}>
                        <PauseIcon />
                      </IconButton>
                      <IconButton
                        onClick={() => stopJobMutation.mutate(selectedJob.job_id)}
                        color="error"
                      >
                        <StopIcon />
                      </IconButton>
                    </>
                  )}
                </Stack>
              </Box>

              {/* Metrics Cards */}
              <Grid container spacing={2} mb={3}>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom variant="body2">
                        Total Records
                      </Typography>
                      <Typography variant="h6">
                        {formatNumber(selectedJob.total_records)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom variant="body2">
                        Processed
                      </Typography>
                      <Typography variant="h6">
                        {formatNumber(selectedJob.records_processed)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom variant="body2">
                        Anomalies
                      </Typography>
                      <Typography variant="h6" color="warning.main">
                        {formatNumber(selectedJob.anomalies_found)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom variant="body2">
                        Duration
                      </Typography>
                      <Typography variant="h6">
                        {selectedJob.start_time
                          ? formatDuration(selectedJob.start_time, selectedJob.end_time)
                          : '-'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Performance Metrics */}
              {metrics && selectedJob.status === 'running' && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>Performance Metrics</Typography>
                  <Grid container spacing={3}>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Memory Usage
                        </Typography>
                        <ResponsiveContainer width="100%" height={200}>
                          <AreaChart data={metrics.memory_usage_history}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="time" />
                            <YAxis />
                            <ChartTooltip />
                            <Area
                              type="monotone"
                              dataKey="usage"
                              stroke="#8884d8"
                              fill="#8884d8"
                              fillOpacity={0.6}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </Box>
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Anomaly Distribution
                        </Typography>
                        <ResponsiveContainer width="100%" height={200}>
                          <PieChart>
                            <Pie
                              data={metrics.anomaly_distribution}
                              dataKey="count"
                              nameKey="category"
                              cx="50%"
                              cy="50%"
                              outerRadius={80}
                            >
                              {metrics.anomaly_distribution.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <ChartTooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </Box>
                    </Grid>
                  </Grid>
                  
                  <Box display="flex" gap={4} mt={2}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <SpeedIcon color="primary" />
                      <Box>
                        <Typography variant="h6">{formatNumber(metrics.records_per_second)}</Typography>
                        <Typography variant="caption" color="text.secondary">Records/sec</Typography>
                      </Box>
                    </Box>
                    <Box display="flex" alignItems="center" gap={1}>
                      <MemoryIcon color="primary" />
                      <Box>
                        <Typography variant="h6">
                          {(selectedJob.memory_usage_mb! / 1024).toFixed(1)} GB
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Memory / {selectedJob.max_memory_gb} GB max
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </Box>
              )}

              <Divider sx={{ my: 3 }} />

              {/* Partition Progress */}
              {partitions && partitions.length > 0 && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>Partition Progress</Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Partition</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Worker</TableCell>
                          <TableCell align="right">Records</TableCell>
                          <TableCell align="right">Anomalies</TableCell>
                          <TableCell align="right">Time</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {partitions.map(partition => (
                          <TableRow key={partition.partition_id}>
                            <TableCell>#{partition.partition_index + 1}</TableCell>
                            <TableCell>
                              <Chip
                                label={partition.status}
                                size="small"
                                color={getStatusColor(partition.status) as any}
                              />
                            </TableCell>
                            <TableCell>{partition.assigned_worker || '-'}</TableCell>
                            <TableCell align="right">
                              {formatNumber(partition.records_processed)}
                            </TableCell>
                            <TableCell align="right">
                              {formatNumber(partition.anomalies_found)}
                            </TableCell>
                            <TableCell align="right">
                              {partition.execution_time_seconds
                                ? `${Math.floor(partition.execution_time_seconds / 60)}m`
                                : '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
            </Paper>
          )}
        </Grid>
      </Grid>

      {/* New Job Dialog */}
      <Dialog open={newJobDialogOpen} onClose={() => setNewJobDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Profiling Job</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Job Name"
              value={newJobConfig.job_name}
              onChange={(e) => setNewJobConfig({ ...newJobConfig, job_name: e.target.value })}
              fullWidth
              required
            />
            
            <FormControl fullWidth>
              <InputLabel>Strategy</InputLabel>
              <Select
                value={newJobConfig.strategy}
                onChange={(e) => setNewJobConfig({ ...newJobConfig, strategy: e.target.value as any })}
              >
                <MenuItem value="full_scan">Full Scan</MenuItem>
                <MenuItem value="sampling">Sampling</MenuItem>
                <MenuItem value="streaming">Streaming</MenuItem>
                <MenuItem value="partitioned">Partitioned</MenuItem>
                <MenuItem value="incremental">Incremental</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              label="Estimated Records"
              type="number"
              value={newJobConfig.estimated_records}
              onChange={(e) => setNewJobConfig({ ...newJobConfig, estimated_records: parseInt(e.target.value) })}
              fullWidth
            />
            
            {newJobConfig.strategy === 'partitioned' && (
              <TextField
                label="Partition Count"
                type="number"
                value={newJobConfig.partition_count}
                onChange={(e) => setNewJobConfig({ ...newJobConfig, partition_count: parseInt(e.target.value) })}
                fullWidth
              />
            )}
            
            <TextField
              label="Max Memory (GB)"
              type="number"
              value={newJobConfig.max_memory_gb}
              onChange={(e) => setNewJobConfig({ ...newJobConfig, max_memory_gb: parseInt(e.target.value) })}
              fullWidth
            />
            
            <Alert severity="info">
              Estimated runtime: {Math.ceil(newJobConfig.estimated_records / 500000)} minutes
              for {formatNumber(newJobConfig.estimated_records)} records
            </Alert>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewJobDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => startJobMutation.mutate({ ...newJobConfig, cycle_id: cycleId, report_id: reportId })}
            disabled={!newJobConfig.job_name || startJobMutation.isPending}
          >
            {startJobMutation.isPending ? <CircularProgress size={20} /> : 'Start Job'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProfilingDashboard;