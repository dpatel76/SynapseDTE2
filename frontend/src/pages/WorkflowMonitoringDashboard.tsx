import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Button,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Tooltip,
  Divider,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Timer as TimerIcon,
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  FilterList as FilterListIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';

import { useQuery } from '@tanstack/react-query';
import { format, formatDuration, intervalToDuration, subDays } from 'date-fns';
import { Line, Bar, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';
import apiClient from '../api/client';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

interface PhaseMetric {
  phase_name: string;
  average_duration: number;
  min_duration: number;
  max_duration: number;
  total_executions: number;
  success_rate: number;
  current_active: number;
}

interface WorkflowMetrics {
  execution_summary: {
    total_workflows: number;
    active_workflows: number;
    completed_workflows: number;
    failed_workflows: number;
    average_duration: number;
    success_rate: number;
  };
  phase_metrics: PhaseMetric[];
  bottlenecks: Array<{
    phase: string;
    severity: 'high' | 'medium' | 'low';
    issue: string;
    recommendation: string;
  }>;
  trend_data: Array<{
    date: string;
    started: number;
    completed: number;
    failed: number;
    average_duration: number;
  }>;
}

interface ActiveWorkflow {
  workflow_id: string;
  cycle_id: number;
  cycle_name: string;
  current_phase: string;
  status: string;
  started_at: string;
  duration_seconds: number;
  progress_percentage: number;
}

const PHASE_COLORS = {
  'Planning': '#1976d2',
  'Scoping': '#388e3c',
  'Sample Selection': '#7b1fa2',
  'Data Owner Identification': '#f57c00',
  'Request for Information': '#d32f2f',
  'Test Execution': '#0288d1',
  'Observation Management': '#5d4037',
  'Finalize Test Report': '#9c27b0',
};

const WorkflowMonitoringDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState('7d');
  const [selectedPhase, setSelectedPhase] = useState<string>('all');
  const [refreshing, setRefreshing] = useState(false);

  // Fetch workflow metrics
  const { data: metrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
    queryKey: ['workflow-metrics', timeRange],
    queryFn: async () => {
      const endDate = new Date();
      const startDate = timeRange === '7d' ? subDays(endDate, 7) :
                       timeRange === '30d' ? subDays(endDate, 30) :
                       subDays(endDate, 90);
      
      const response = await apiClient.get('/workflow-metrics/metrics', {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
          period: timeRange === '7d' ? 'daily' : 'weekly',
        },
      });
      return response.data as WorkflowMetrics;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch active workflows
  const { data: activeWorkflows, refetch: refetchActive } = useQuery({
    queryKey: ['active-workflows'],
    queryFn: async () => {
      const response = await apiClient.get('/workflow-metrics/active-workflows');
      return response.data.workflows as ActiveWorkflow[];
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([refetchMetrics(), refetchActive()]);
    setRefreshing(false);
  };

  const formatDurationTime = (seconds: number) => {
    if (!seconds) return '-';
    const duration = intervalToDuration({ start: 0, end: seconds * 1000 });
    return formatDuration(duration, { format: ['hours', 'minutes'] });
  };

  const renderSummaryCards = () => {
    if (!metrics) return null;
    const { execution_summary } = metrics;

    return (
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="caption">
                    Total Workflows
                  </Typography>
                  <Typography variant="h4">
                    {execution_summary.total_workflows}
                  </Typography>
                </Box>
                <AssessmentIcon sx={{ color: 'primary.main', fontSize: 40, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="caption">
                    Active Now
                  </Typography>
                  <Typography variant="h4" color="warning.main">
                    {execution_summary.active_workflows}
                  </Typography>
                </Box>
                <CircularProgress
                  variant="determinate"
                  value={100}
                  size={40}
                  thickness={4}
                  sx={{ color: 'warning.main', opacity: 0.3 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="caption">
                    Success Rate
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {Math.round(execution_summary.success_rate)}%
                  </Typography>
                </Box>
                <CheckCircleIcon sx={{ color: 'success.main', fontSize: 40, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="caption">
                    Avg Duration
                  </Typography>
                  <Typography variant="h4">
                    {formatDurationTime(execution_summary.average_duration)}
                  </Typography>
                </Box>
                <TimerIcon sx={{ color: 'info.main', fontSize: 40, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  const renderPhaseMetricsChart = () => {
    if (!metrics || !metrics.phase_metrics) return null;

    const chartData = {
      labels: metrics.phase_metrics.map(p => p.phase_name),
      datasets: [
        {
          label: 'Average Duration (minutes)',
          data: metrics.phase_metrics.map(p => Math.round(p.average_duration / 60)),
          backgroundColor: metrics.phase_metrics.map(p => PHASE_COLORS[p.phase_name as keyof typeof PHASE_COLORS] || '#666'),
        },
      ],
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          display: false,
        },
        title: {
          display: true,
          text: 'Average Phase Duration',
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Duration (minutes)',
          },
        },
      },
    };

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Phase Performance Metrics
          </Typography>
          <Box sx={{ height: 300 }}>
            <Bar data={chartData} options={options} />
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderTrendChart = () => {
    if (!metrics || !metrics.trend_data) return null;

    const chartData = {
      labels: metrics.trend_data.map(d => format(new Date(d.date), 'MMM dd')),
      datasets: [
        {
          label: 'Started',
          data: metrics.trend_data.map(d => d.started),
          borderColor: '#1976d2',
          backgroundColor: 'rgba(25, 118, 210, 0.1)',
          tension: 0.3,
        },
        {
          label: 'Completed',
          data: metrics.trend_data.map(d => d.completed),
          borderColor: '#388e3c',
          backgroundColor: 'rgba(56, 142, 60, 0.1)',
          tension: 0.3,
        },
        {
          label: 'Failed',
          data: metrics.trend_data.map(d => d.failed),
          borderColor: '#d32f2f',
          backgroundColor: 'rgba(211, 47, 47, 0.1)',
          tension: 0.3,
        },
      ],
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: 'Workflow Execution Trends',
        },
      },
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    };

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ height: 300 }}>
            <Line data={chartData} options={options} />
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderActiveWorkflowsTable = () => {
    if (!activeWorkflows || activeWorkflows.length === 0) {
      return (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Active Workflows
            </Typography>
            <Alert severity="info">No active workflows at the moment</Alert>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Active Workflows ({activeWorkflows.length})
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Cycle</TableCell>
                  <TableCell>Current Phase</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Progress</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {activeWorkflows.map((workflow) => (
                  <TableRow key={workflow.workflow_id}>
                    <TableCell>
                      <Typography variant="body2">{workflow.cycle_name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        ID: {workflow.cycle_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={workflow.current_phase}
                        size="small"
                        style={{
                          backgroundColor: PHASE_COLORS[workflow.current_phase as keyof typeof PHASE_COLORS] || '#666',
                          color: 'white',
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={workflow.status}
                        size="small"
                        color={workflow.status === 'running' ? 'primary' : 'default'}
                      />
                    </TableCell>
                    <TableCell>{formatDurationTime(workflow.duration_seconds)}</TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <LinearProgress
                          variant="determinate"
                          value={workflow.progress_percentage}
                          sx={{ width: 100, height: 6 }}
                        />
                        <Typography variant="caption">
                          {workflow.progress_percentage}%
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    );
  };

  const renderBottlenecks = () => {
    if (!metrics || !metrics.bottlenecks || metrics.bottlenecks.length === 0) {
      return null;
    }

    const getSeverityColor = (severity: string) => {
      switch (severity) {
        case 'high': return 'error';
        case 'medium': return 'warning';
        case 'low': return 'info';
        default: return 'default';
      }
    };

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Workflow Bottlenecks & Recommendations
          </Typography>
          <Box display="flex" flexDirection="column" gap={2}>
            {metrics.bottlenecks.map((bottleneck, index) => (
              <Alert
                key={index}
                severity={getSeverityColor(bottleneck.severity) as any}
                icon={<WarningIcon />}
              >
                <Typography variant="subtitle2" fontWeight="bold">
                  {bottleneck.phase} - {bottleneck.issue}
                </Typography>
                <Typography variant="body2" sx={{ mt: 0.5 }}>
                  {bottleneck.recommendation}
                </Typography>
              </Alert>
            ))}
          </Box>
        </CardContent>
      </Card>
    );
  };

  if (metricsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Workflow Monitoring Dashboard</Typography>
        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              label="Time Range"
            >
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
            </Select>
          </FormControl>
          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh} disabled={refreshing}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Summary Cards */}
      {renderSummaryCards()}

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          {renderPhaseMetricsChart()}
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          {renderTrendChart()}
        </Grid>
      </Grid>

      {/* Bottlenecks */}
      {renderBottlenecks()}

      {/* Active Workflows Table */}
      {renderActiveWorkflowsTable()}
    </Box>
  );
};

export default WorkflowMonitoringDashboard;