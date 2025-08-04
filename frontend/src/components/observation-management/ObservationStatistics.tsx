import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Stack,
  LinearProgress
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts';
import { useTheme } from '@mui/material/styles';

interface ObservationStatistics {
  total_groups: number;
  total_observations: number;
  status_distribution: Record<string, number>;
  severity_distribution: Record<string, number>;
  issue_type_distribution: Record<string, number>;
  average_observations_per_group: number;
}

interface DetectionStatistics {
  total_failed_executions: number;
  failed_with_observations: number;
  failed_without_observations: number;
  detection_coverage: number;
  observation_groups: number;
  total_observations: number;
}

interface ObservationStatisticsProps {
  phaseId?: number;
  cycleId?: number;
  reportId?: number;
}

const ObservationStatistics: React.FC<ObservationStatisticsProps> = ({
  phaseId,
  cycleId,
  reportId
}) => {
  const theme = useTheme();
  const [statistics, setStatistics] = useState<ObservationStatistics | null>(null);
  const [detectionStats, setDetectionStats] = useState<DetectionStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatistics();
  }, [phaseId, cycleId, reportId]);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (phaseId) params.append('phase_id', phaseId.toString());
      if (cycleId) params.append('cycle_id', cycleId.toString());
      if (reportId) params.append('report_id', reportId.toString());

      // Fetch observation statistics
      const statsResponse = await fetch(`/api/v1/observation-management-unified/statistics?${params}`);
      if (!statsResponse.ok) {
        throw new Error('Failed to fetch statistics');
      }
      const statsData = await statsResponse.json();
      setStatistics(statsData);

      // Fetch detection statistics if we have a phase ID
      if (phaseId) {
        const detectionResponse = await fetch(`/api/v1/observation-management-unified/detect/status/phase/${phaseId}`);
        if (detectionResponse.ok) {
          const detectionData = await detectionResponse.json();
          setDetectionStats(detectionData);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!statistics) {
    return (
      <Alert severity="info">
        No statistics available
      </Alert>
    );
  }

  // Prepare chart data
  const statusData = Object.entries(statistics.status_distribution).map(([key, value]) => ({
    name: key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value,
    color: getStatusColor(key)
  }));

  const severityData = Object.entries(statistics.severity_distribution).map(([key, value]) => ({
    name: key.toUpperCase(),
    value,
    color: getSeverityColor(key)
  }));

  const issueTypeData = Object.entries(statistics.issue_type_distribution).map(([key, value]) => ({
    name: key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value,
    color: getIssueTypeColor(key)
  }));

  function getStatusColor(status: string) {
    switch (status) {
      case 'draft': return theme.palette.grey[500];
      case 'pending_tester_review': return theme.palette.warning.main;
      case 'tester_approved': return theme.palette.info.main;
      case 'pending_report_owner_approval': return theme.palette.warning.main;
      case 'report_owner_approved': return theme.palette.success.main;
      case 'rejected': return theme.palette.error.main;
      case 'resolved': return theme.palette.success.main;
      case 'closed': return theme.palette.grey[600];
      default: return theme.palette.grey[500];
    }
  }

  function getSeverityColor(severity: string) {
    switch (severity) {
      case 'high': return theme.palette.error.main;
      case 'medium': return theme.palette.warning.main;
      case 'low': return theme.palette.info.main;
      default: return theme.palette.grey[500];
    }
  }

  function getIssueTypeColor(issueType: string) {
    switch (issueType) {
      case 'data_quality': return theme.palette.primary.main;
      case 'process_failure': return theme.palette.error.main;
      case 'system_error': return theme.palette.warning.main;
      case 'compliance_gap': return theme.palette.info.main;
      default: return theme.palette.grey[500];
    }
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Paper sx={{ p: 1 }}>
          <Typography variant="body2">
            {`${label}: ${payload[0].value}`}
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Observation Statistics
      </Typography>

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Groups
              </Typography>
              <Typography variant="h4">
                {statistics.total_groups}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Observations
              </Typography>
              <Typography variant="h4">
                {statistics.total_observations}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Avg. Observations/Group
              </Typography>
              <Typography variant="h4">
                {statistics.average_observations_per_group.toFixed(1)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {detectionStats && (
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Detection Coverage
                </Typography>
                <Typography variant="h4">
                  {Math.round(detectionStats.detection_coverage * 100)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={detectionStats.detection_coverage * 100}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Detection Statistics */}
      {detectionStats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Detection Statistics
                </Typography>
                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <Typography color="text.secondary" gutterBottom>
                      Failed Executions
                    </Typography>
                    <Typography variant="h5">
                      {detectionStats.total_failed_executions}
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <Typography color="text.secondary" gutterBottom>
                      With Observations
                    </Typography>
                    <Typography variant="h5" color="success.main">
                      {detectionStats.failed_with_observations}
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <Typography color="text.secondary" gutterBottom>
                      Without Observations
                    </Typography>
                    <Typography variant="h5" color="warning.main">
                      {detectionStats.failed_without_observations}
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <Typography color="text.secondary" gutterBottom>
                      Groups Created
                    </Typography>
                    <Typography variant="h5">
                      {detectionStats.observation_groups}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Status Distribution */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Status Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Severity Distribution */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Severity Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={severityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" fill={theme.palette.primary.main}>
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Issue Type Distribution */}
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Issue Type Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={issueTypeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar dataKey="value" fill={theme.palette.primary.main}>
                    {issueTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Status Distribution Table */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Detailed Status Breakdown
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Status</TableCell>
                      <TableCell align="right">Count</TableCell>
                      <TableCell align="right">Percentage</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(statistics.status_distribution).map(([status, count]) => (
                      <TableRow key={status}>
                        <TableCell>
                          <Chip
                            label={status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            size="small"
                            sx={{
                              bgcolor: getStatusColor(status),
                              color: 'white'
                            }}
                          />
                        </TableCell>
                        <TableCell align="right">{count}</TableCell>
                        <TableCell align="right">
                          {statistics.total_groups > 0 
                            ? ((count / statistics.total_groups) * 100).toFixed(1) + '%'
                            : '0%'
                          }
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ObservationStatistics;