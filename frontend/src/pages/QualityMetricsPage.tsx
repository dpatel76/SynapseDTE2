import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Alert,
  Button,
  Stack,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  useTheme,
  alpha,
  Grid,
  CircularProgress,
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Warning,
  BugReport,
  TrendingUp,
  TrendingDown,
  Assessment,
  Visibility,
  Download,
  FilterList,
  Refresh,
} from '@mui/icons-material';
import { Pie, Line, Doughnut } from 'react-chartjs-2';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';

interface LobMetric {
  lob: string;
  total_issues: number;
  high_severity: number;
  medium_severity: number;
  low_severity: number;
  resolved_issues: number;
  resolution_rate: number;
  avg_resolution_time: number;
  quality_score: number;
  critical: number;
  major: number;
  minor: number;
}

const QualityMetricsPage: React.FC = () => {
  const theme = useTheme();
  const { user } = useAuth();
  const [timeFilter, setTimeFilter] = useState('30d');
  const [lobFilter, setLobFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  // Fetch quality metrics from API
  const { data: qualityData, isLoading, refetch } = useQuery({
    queryKey: ['quality-metrics', timeFilter, lobFilter],
    queryFn: async () => {
      const params = new URLSearchParams({
        time_period: timeFilter,
        lob_filter: lobFilter,
      });
      
      const response = await apiClient.get(`/metrics/quality-metrics?${params}`);
      return response.data;
    },
  });

  const handleRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  const qualityMetrics = qualityData?.metrics || {
    overall_quality_score: 0,
    error_rate: 0,
    first_pass_rate: 0,
    rework_rate: 0,
    critical_issues: 0,
    major_issues: 0,
    minor_issues: 0,
    avg_resolution_time: '0 days',
  };

  const issuesByType = {
    labels: Object.keys(qualityData?.issue_categories || {}),
    datasets: [
      {
        data: Object.values(qualityData?.issue_categories || {}),
        backgroundColor: [
          theme.palette.error.main,
          theme.palette.warning.main,
          theme.palette.info.main,
          theme.palette.success.main,
          theme.palette.grey[400],
        ],
      },
    ],
  };

  const issuesByLOB = qualityData?.lob_metrics || [];

  const qualityTrend = {
    labels: qualityData?.quality_trend?.labels || [],
    datasets: [
      {
        label: 'Quality Score',
        data: qualityData?.quality_trend?.quality_scores || [],
        borderColor: theme.palette.primary.main,
        backgroundColor: alpha(theme.palette.primary.main, 0.1),
        tension: 0.3,
      },
      {
        label: 'First Pass Rate',
        data: qualityData?.quality_trend?.first_pass_rates || [],
        borderColor: theme.palette.success.main,
        backgroundColor: alpha(theme.palette.success.main, 0.1),
        tension: 0.3,
      },
    ],
  };

  const severityDistribution = {
    labels: ['Critical', 'Major', 'Minor'],
    datasets: [
      {
        data: [
          qualityData?.severity_distribution?.critical || 0,
          qualityData?.severity_distribution?.major || 0,
          qualityData?.severity_distribution?.minor || 0
        ],
        backgroundColor: [
          theme.palette.error.main,
          theme.palette.warning.main,
          theme.palette.info.main,
        ],
      },
    ],
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Quality Metrics
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor quality indicators and issue trends across testing cycles
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Period</InputLabel>
            <Select
              value={timeFilter}
              label="Time Period"
              onChange={(e) => setTimeFilter(e.target.value)}
            >
              <MenuItem value="7d">Last 7 Days</MenuItem>
              <MenuItem value="30d">Last 30 Days</MenuItem>
              <MenuItem value="90d">Last 90 Days</MenuItem>
              <MenuItem value="ytd">Year to Date</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>LOB Filter</InputLabel>
            <Select
              value={lobFilter}
              label="LOB Filter"
              onChange={(e) => setLobFilter(e.target.value)}
            >
              <MenuItem value="all">All LOBs</MenuItem>
              <MenuItem value="Corporate Banking">Corporate Banking</MenuItem>
              <MenuItem value="Retail Banking">Retail Banking</MenuItem>
              <MenuItem value="Investment Banking">Investment Banking</MenuItem>
            </Select>
          </FormControl>
          <Tooltip title="Refresh data">
            <IconButton onClick={handleRefresh} disabled={refreshing}>
              <Refresh className={refreshing ? 'rotating' : ''} />
            </IconButton>
          </Tooltip>
          <Button variant="outlined" startIcon={<Download />}>
            Export
          </Button>
        </Stack>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Quality Score
                  </Typography>
                  <Typography variant="h3" color="primary">
                    {qualityMetrics.overall_quality_score}
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <TrendingUp sx={{ fontSize: 16, color: 'success.main', mr: 0.5 }} />
                    <Typography variant="caption" color="success.main">
                      +2% from last period
                    </Typography>
                  </Box>
                </Box>
                <Assessment sx={{ fontSize: 40, color: theme.palette.primary.main }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Error Rate
                  </Typography>
                  <Typography variant="h3" color="error">
                    {qualityMetrics.error_rate}%
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <TrendingDown sx={{ fontSize: 16, color: 'success.main', mr: 0.5 }} />
                    <Typography variant="caption" color="success.main">
                      -0.5% improvement
                    </Typography>
                  </Box>
                </Box>
                <Error sx={{ fontSize: 40, color: theme.palette.error.main }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    First Pass Rate
                  </Typography>
                  <Typography variant="h3" color="success.main">
                    {qualityMetrics.first_pass_rate}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Tests passed on first attempt
                  </Typography>
                </Box>
                <CheckCircle sx={{ fontSize: 40, color: theme.palette.success.main }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Total Issues
                  </Typography>
                  <Typography variant="h3">
                    {qualityMetrics.critical_issues + qualityMetrics.major_issues + qualityMetrics.minor_issues}
                  </Typography>
                  <Stack direction="row" spacing={1} mt={1}>
                    <Chip label={`${qualityMetrics.critical_issues} Critical`} size="small" color="error" />
                    <Chip label={`${qualityMetrics.major_issues} Major`} size="small" color="warning" />
                  </Stack>
                </Box>
                <BugReport sx={{ fontSize: 40, color: theme.palette.warning.main }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Quality Trend Analysis
            </Typography>
            <Box sx={{ height: 300 }}>
              <Line
                data={qualityTrend}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'top' as const,
                    },
                  },
                  scales: {
                    y: {
                      beginAtZero: true,
                      max: 100,
                    },
                  },
                }}
              />
            </Box>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Issue Severity Distribution
            </Typography>
            <Box sx={{ height: 300, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <Doughnut
                data={severityDistribution}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom' as const,
                    },
                  },
                }}
              />
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Quality by LOB Table */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Quality Metrics by Line of Business
        </Typography>
        
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Line of Business</TableCell>
                <TableCell align="center">Quality Score</TableCell>
                <TableCell align="center">Critical Issues</TableCell>
                <TableCell align="center">Major Issues</TableCell>
                <TableCell align="center">Minor Issues</TableCell>
                <TableCell align="center">Total Issues</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {issuesByLOB.map((lob: LobMetric) => (
                <TableRow key={lob.lob}>
                  <TableCell>
                    <Typography variant="subtitle2">{lob.lob}</Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                      <LinearProgress
                        variant="determinate"
                        value={lob.quality_score}
                        sx={{ width: 80, height: 8 }}
                        color={lob.quality_score >= 90 ? 'success' : 'primary'}
                      />
                      <Typography variant="body2" fontWeight="medium">
                        {lob.quality_score}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={lob.critical}
                      size="small"
                      color={lob.critical > 0 ? 'error' : 'default'}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={lob.major}
                      size="small"
                      color={lob.major > 5 ? 'warning' : 'default'}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip label={lob.minor} size="small" />
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" fontWeight="medium">
                      {lob.critical + lob.major + lob.minor}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="View Details">
                      <IconButton size="small">
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Issue Categories */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Issues by Category
        </Typography>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Box sx={{ height: 300 }}>
              <Pie
                data={issuesByType}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'right' as const,
                    },
                  },
                }}
              />
            </Box>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Box sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Key Insights
              </Typography>
              <Stack spacing={2}>
                <Alert severity="warning">
                  <Typography variant="body2">
                    <strong>Data Quality Issues</strong> account for 35% of all issues. Consider implementing additional data validation checks.
                  </Typography>
                </Alert>
                <Alert severity="info">
                  <Typography variant="body2">
                    <strong>Average Resolution Time</strong> is {qualityMetrics.avg_resolution_time}, which is within the target SLA.
                  </Typography>
                </Alert>
                <Alert severity="success">
                  <Typography variant="body2">
                    <strong>First Pass Rate</strong> has improved by 3% compared to last quarter.
                  </Typography>
                </Alert>
              </Stack>
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      <style>{`
        @keyframes rotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .rotating {
          animation: rotate 1s linear infinite;
        }
      `}</style>
    </Box>
  );
};

export default QualityMetricsPage;