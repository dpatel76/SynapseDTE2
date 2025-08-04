import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Tabs,
  Tab
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Refresh,
  Speed,
  Timeline,
  Assignment,
  BugReport,
  BarChart,
  PieChart
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart as RechartsBarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { versioningAnalyticsApi } from '../../api/versioningAnalytics';
import { useInterval } from '../../hooks/useInterval';

interface VersioningAnalyticsDashboardProps {
  cycleId: number;
  reportId: number;
  workflowId?: string;
}

const COLORS = {
  primary: '#3f51b5',
  secondary: '#f50057',
  success: '#4caf50',
  warning: '#ff9800',
  error: '#f44336',
  info: '#2196f3'
};

const PHASE_COLORS: Record<string, string> = {
  'Planning': COLORS.primary,
  'Data Profiling': COLORS.info,
  'Scoping': COLORS.warning,
  'Sample Selection': COLORS.secondary,
  'Data Owner ID': '#9c27b0',
  'Request Info': '#00bcd4',
  'Test Execution': '#ff5722',
  'Observation Management': '#795548',
  'Finalize Test Report': COLORS.success
};

export const VersioningAnalyticsDashboard: React.FC<VersioningAnalyticsDashboardProps> = ({
  cycleId,
  reportId,
  workflowId
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedPhase, setSelectedPhase] = useState<string>('');
  const [timeRange, setTimeRange] = useState(30);
  
  // Metrics state
  const [phaseMetrics, setPhaseMetrics] = useState<any>({});
  const [workflowMetrics, setWorkflowMetrics] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [bottlenecks, setBottlenecks] = useState<any[]>([]);
  const [userActivity, setUserActivity] = useState<any>(null);

  useEffect(() => {
    loadAllMetrics();
  }, [cycleId, reportId, workflowId]);

  useEffect(() => {
    if (selectedPhase) {
      loadTrends(selectedPhase, timeRange);
    }
  }, [selectedPhase, timeRange]);

  // Auto-refresh every 5 minutes
  useInterval(() => {
    loadAllMetrics();
  }, 300000);

  const loadAllMetrics = async () => {
    try {
      setLoading(true);
      
      const [phaseData, bottleneckData] = await Promise.all([
        versioningAnalyticsApi.getPhaseMetrics(cycleId, reportId),
        versioningAnalyticsApi.getBottlenecks(cycleId, reportId)
      ]);
      
      setPhaseMetrics(phaseData.data);
      setBottlenecks(bottleneckData.data);
      
      if (workflowId) {
        const workflowData = await versioningAnalyticsApi.getWorkflowMetrics(cycleId, reportId);
        setWorkflowMetrics(workflowData.data);
      }
      
      // Load trends for first phase with data
      const firstPhaseWithData = Object.keys(phaseData.data).find(
        phase => phaseData.data[phase].version_count > 0
      );
      if (firstPhaseWithData) {
        setSelectedPhase(firstPhaseWithData);
      }
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTrends = async (phase: string, days: number) => {
    try {
      const trendData = await versioningAnalyticsApi.getVersionTrends(phase, days);
      setTrends(trendData.data);
    } catch (error) {
      console.error('Failed to load trends:', error);
    }
  };

  const renderMetricCard = (
    title: string,
    value: string | number,
    subtitle?: string,
    trend?: 'up' | 'down' | 'neutral',
    color: string = 'primary'
  ) => (
    <Card>
      <CardContent>
        <Typography color="textSecondary" gutterBottom variant="overline">
          {title}
        </Typography>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h4" component="h2" color={color}>
            {value}
          </Typography>
          {trend && (
            <IconButton size="small" color={trend === 'up' ? 'success' : 'error'}>
              {trend === 'up' ? <TrendingUp /> : <TrendingDown />}
            </IconButton>
          )}
        </Box>
        {subtitle && (
          <Typography variant="body2" color="textSecondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  const renderOverviewTab = () => {
    const totalVersions = Object.values(phaseMetrics).reduce(
      (sum: number, phase: any) => sum + (phase.version_count || 0), 0
    );
    
    const completedPhases = Object.values(phaseMetrics).filter(
      (phase: any) => phase.status === 'complete'
    ).length;
    
    const avgApprovalTime = Object.values(phaseMetrics).reduce(
      (sum: number, phase: any) => sum + (phase.average_approval_time_hours || 0), 0
    ) / Object.keys(phaseMetrics).length;

    return (
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 3 }}>
          {renderMetricCard(
            'Total Versions',
            totalVersions,
            'Across all phases',
            'up',
            'primary'
          )}
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          {renderMetricCard(
            'Completed Phases',
            `${completedPhases}/9`,
            `${Math.round(completedPhases / 9 * 100)}% complete`,
            completedPhases > 5 ? 'up' : 'down',
            'success'
          )}
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          {renderMetricCard(
            'Avg Approval Time',
            `${avgApprovalTime.toFixed(1)}h`,
            'Hours to approval',
            avgApprovalTime < 24 ? 'up' : 'down',
            avgApprovalTime < 24 ? 'success' : 'warning'
          )}
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          {renderMetricCard(
            'Active Bottlenecks',
            bottlenecks.length,
            'Require attention',
            bottlenecks.length === 0 ? 'up' : 'down',
            bottlenecks.length === 0 ? 'success' : 'error'
          )}
        </Grid>

        {/* Phase Progress Chart */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Phase Progress
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <RechartsBarChart
                  data={Object.entries(phaseMetrics).map(([phase, metrics]: [string, any]) => ({
                    phase: phase.split(' ').map(w => w[0]).join(''), // Abbreviate
                    fullName: phase,
                    versions: metrics.version_count || 0,
                    status: metrics.status
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="phase" />
                  <YAxis />
                  <RechartsTooltip 
                    formatter={(value, name) => [value, name === 'versions' ? 'Versions' : name]}
                    labelFormatter={(label) => {
                      const data = Object.entries(phaseMetrics).find(
                        ([phase]) => phase.split(' ').map(w => w[0]).join('') === label
                      );
                      return data ? data[0] : label;
                    }}
                  />
                  <Bar 
                    dataKey="versions" 
                    fill={COLORS.primary}
                    onClick={(data) => setSelectedPhase(data.fullName)}
                  />
                </RechartsBarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Bottlenecks */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Bottlenecks
              </Typography>
              {bottlenecks.length === 0 ? (
                <Box display="flex" alignItems="center" justifyContent="center" height={250}>
                  <Box textAlign="center">
                    <CheckCircle color="success" sx={{ fontSize: 48 }} />
                    <Typography variant="body1" color="textSecondary" sx={{ mt: 1 }}>
                      No bottlenecks detected
                    </Typography>
                  </Box>
                </Box>
              ) : (
                <Box>
                  {bottlenecks.slice(0, 3).map((bottleneck, index) => (
                    <Alert 
                      key={index} 
                      severity={bottleneck.severity} 
                      sx={{ mb: 1 }}
                    >
                      <Typography variant="subtitle2">
                        {bottleneck.phase}
                      </Typography>
                      <Typography variant="body2">
                        {bottleneck.issue}
                      </Typography>
                    </Alert>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  const renderPhaseAnalysisTab = () => (
    <Grid container spacing={3}>
      <Grid size={{ xs: 12 }}>
        <FormControl sx={{ minWidth: 200, mb: 2 }}>
          <InputLabel>Select Phase</InputLabel>
          <Select
            value={selectedPhase}
            onChange={(e) => setSelectedPhase(e.target.value)}
            label="Select Phase"
          >
            {Object.keys(phaseMetrics).map(phase => (
              <MenuItem key={phase} value={phase}>{phase}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Grid>

      {selectedPhase && phaseMetrics[selectedPhase] && (
        <>
          {/* Phase Metrics */}
          <Grid size={{ xs: 12, md: 3 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {selectedPhase} Metrics
                </Typography>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary">
                    Version Count
                  </Typography>
                  <Typography variant="h4">
                    {phaseMetrics[selectedPhase].version_count || 0}
                  </Typography>
                </Box>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary">
                    Avg Approval Time
                  </Typography>
                  <Typography variant="h5">
                    {(phaseMetrics[selectedPhase].average_approval_time_hours || 0).toFixed(1)}h
                  </Typography>
                </Box>
                {phaseMetrics[selectedPhase].revision_count !== undefined && (
                  <Box mb={2}>
                    <Typography variant="body2" color="textSecondary">
                      Revisions
                    </Typography>
                    <Typography variant="h5">
                      {phaseMetrics[selectedPhase].revision_count}
                    </Typography>
                  </Box>
                )}
                <Chip
                  label={phaseMetrics[selectedPhase].status}
                  color={phaseMetrics[selectedPhase].status === 'complete' ? 'success' : 'warning'}
                  size="small"
                />
              </CardContent>
            </Card>
          </Grid>

          {/* Trends Chart */}
          <Grid size={{ xs: 12, md: 9 }}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    Version Creation Trends
                  </Typography>
                  <FormControl size="small">
                    <Select
                      value={timeRange}
                      onChange={(e) => setTimeRange(Number(e.target.value))}
                    >
                      <MenuItem value={7}>Last 7 days</MenuItem>
                      <MenuItem value={30}>Last 30 days</MenuItem>
                      <MenuItem value={90}>Last 90 days</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <RechartsTooltip 
                      labelFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <Legend />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="version_count"
                      stroke={PHASE_COLORS[selectedPhase] || COLORS.primary}
                      fill={PHASE_COLORS[selectedPhase] || COLORS.primary}
                      fillOpacity={0.6}
                      name="Versions Created"
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="approval_rate"
                      stroke={COLORS.success}
                      name="Approval Rate %"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Sample Selection Special Metrics */}
          {selectedPhase === 'Sample Selection' && 
           phaseMetrics[selectedPhase].sample_statistics && (
            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Sample Statistics
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, md: 8 }}>
                      <ResponsiveContainer width="100%" height={200}>
                        <RechartsBarChart
                          data={[
                            {
                              name: 'Samples',
                              approved: phaseMetrics[selectedPhase].sample_statistics.approved,
                              rejected: phaseMetrics[selectedPhase].sample_statistics.rejected,
                              carried: phaseMetrics[selectedPhase].sample_statistics.carried_forward
                            }
                          ]}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <RechartsTooltip />
                          <Legend />
                          <Bar dataKey="approved" stackId="a" fill={COLORS.success} />
                          <Bar dataKey="rejected" stackId="a" fill={COLORS.error} />
                          <Bar dataKey="carried" stackId="a" fill={COLORS.info} />
                        </RechartsBarChart>
                      </ResponsiveContainer>
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Box display="flex" alignItems="center" justifyContent="center" height="100%">
                        <Box textAlign="center">
                          <Typography variant="h2" color="primary">
                            {phaseMetrics[selectedPhase].sample_statistics.approval_rate.toFixed(1)}%
                          </Typography>
                          <Typography variant="body1" color="textSecondary">
                            Approval Rate
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          )}
        </>
      )}
    </Grid>
  );

  const renderWorkflowMetricsTab = () => {
    if (!workflowMetrics) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" height={400}>
          <Typography variant="body1" color="textSecondary">
            No workflow metrics available
          </Typography>
        </Box>
      );
    }

    return (
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Workflow Summary
              </Typography>
              <Box mb={2}>
                <Typography variant="body2" color="textSecondary">
                  Total Operations
                </Typography>
                <Typography variant="h4">
                  {workflowMetrics.total_operations}
                </Typography>
              </Box>
              <Box mb={2}>
                <Typography variant="body2" color="textSecondary">
                  Success Rate
                </Typography>
                <Typography variant="h5" color={
                  workflowMetrics.overall_success_rate > 90 ? 'success' : 'warning'
                }>
                  {workflowMetrics.overall_success_rate.toFixed(1)}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={workflowMetrics.overall_success_rate}
                color={workflowMetrics.overall_success_rate > 90 ? 'success' : 'warning'}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Phase Operations
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Phase</TableCell>
                      <TableCell align="right">Operations</TableCell>
                      <TableCell align="right">Versions</TableCell>
                      <TableCell align="right">Approved</TableCell>
                      <TableCell align="right">Avg Approval (h)</TableCell>
                      <TableCell align="right">Success Rate</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {workflowMetrics.phases_with_versions.map((phase: any) => (
                      <TableRow key={phase.phase}>
                        <TableCell>{phase.phase}</TableCell>
                        <TableCell align="right">{phase.total_operations}</TableCell>
                        <TableCell align="right">{phase.versions_created}</TableCell>
                        <TableCell align="right">{phase.versions_approved}</TableCell>
                        <TableCell align="right">
                          {phase.average_approval_time_hours.toFixed(1)}
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label={`${phase.success_rate.toFixed(0)}%`}
                            size="small"
                            color={phase.success_rate > 90 ? 'success' : 'warning'}
                          />
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
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Versioning Analytics</Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={loadAllMetrics}
        >
          Refresh
        </Button>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
          <Tab label="Overview" />
          <Tab label="Phase Analysis" />
          {workflowId && <Tab label="Workflow Metrics" />}
        </Tabs>
      </Box>

      {activeTab === 0 && renderOverviewTab()}
      {activeTab === 1 && renderPhaseAnalysisTab()}
      {activeTab === 2 && workflowId && renderWorkflowMetricsTab()}
    </Box>
  );
};