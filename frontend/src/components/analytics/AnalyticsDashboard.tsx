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
  Chip,
  LinearProgress,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  ButtonGroup
} from '@mui/material';
import { Grid } from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Schedule,
  CheckCircle,
  Warning,
  Error,
  Info,
  Refresh,
  Download,
  FilterList,
  Timeline,
  Assessment,
  Speed,
  Group
} from '@mui/icons-material';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { format, subDays, startOfWeek, endOfWeek } from 'date-fns';
import { colors } from '../../styles/design-system';

interface MetricCard {
  title: string;
  value: number | string;
  change?: number;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
  color: string;
}

interface ChartData {
  name: string;
  value: number;
  [key: string]: any;
}

const AnalyticsDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState('week');
  const [selectedMetric, setSelectedMetric] = useState('all');
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState<MetricCard[]>([]);
  const [chartData, setChartData] = useState<ChartData[]>([]);

  // Sample metric cards
  const metricCards: MetricCard[] = [
    {
      title: 'Active Test Cycles',
      value: 24,
      change: 12,
      changeType: 'positive',
      icon: <Timeline />,
      color: colors.primary.main
    },
    {
      title: 'Tests Completed',
      value: '89%',
      change: 5,
      changeType: 'positive',
      icon: <CheckCircle />,
      color: colors.success.main
    },
    {
      title: 'SLA Compliance',
      value: '94.5%',
      change: -2.1,
      changeType: 'negative',
      icon: <Speed />,
      color: colors.warning.main
    },
    {
      title: 'Open Observations',
      value: 156,
      change: 23,
      changeType: 'negative',
      icon: <Warning />,
      color: colors.error.main
    }
  ];

  // Sample workflow phase data
  const phaseCompletionData = [
    { name: 'Planning', completed: 95, pending: 5 },
    { name: 'Scoping', completed: 88, pending: 12 },
    { name: 'Sample Selection', completed: 76, pending: 24 },
    { name: 'Data Owner ID', completed: 82, pending: 18 },
    { name: 'Request Info', completed: 70, pending: 30 },
    { name: 'Test Execution', completed: 65, pending: 35 },
    { name: 'Observations', completed: 58, pending: 42 },
    { name: 'Testing Report', completed: 45, pending: 55 }
  ];

  // Sample time series data
  const timeSeriesData = Array.from({ length: 7 }, (_, i) => {
    const date = subDays(new Date(), 6 - i);
    return {
      date: format(date, 'MMM dd'),
      testsStarted: Math.floor(Math.random() * 20) + 10,
      testsCompleted: Math.floor(Math.random() * 15) + 5,
      observations: Math.floor(Math.random() * 30) + 20
    };
  });

  // Sample SLA performance data
  const slaPerformanceData = [
    { phase: 'Planning', onTime: 85, warning: 10, violated: 5 },
    { phase: 'Scoping', onTime: 90, warning: 7, violated: 3 },
    { phase: 'Data Owner ID', onTime: 75, warning: 15, violated: 10 },
    { phase: 'Test Execution', onTime: 80, warning: 12, violated: 8 }
  ];

  // Sample user activity data
  const userActivityData = [
    { role: 'Tester', count: 45, color: colors.primary.main },
    { role: 'Data Owner', count: 32, color: colors.secondary.main },
    { role: 'Test Executive', count: 12, color: colors.success.main },
    { role: 'Data Executive', count: 8, color: colors.warning.main },
    { role: 'Report Owner', count: 15, color: colors.error.main }
  ];

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 1500);
  };

  const handleExport = () => {
    // Export functionality
    console.log('Exporting analytics data...');
  };

  const renderMetricCard = (metric: MetricCard) => (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              {metric.title}
            </Typography>
            <Typography variant="h4" sx={{ mb: 1 }}>
              {metric.value}
            </Typography>
            {metric.change && (
              <Box display="flex" alignItems="center" gap={0.5}>
                {metric.changeType === 'positive' ? (
                  <TrendingUp sx={{ fontSize: 20, color: colors.success.main }} />
                ) : (
                  <TrendingDown sx={{ fontSize: 20, color: colors.error.main }} />
                )}
                <Typography
                  variant="body2"
                  sx={{
                    color: metric.changeType === 'positive' ? colors.success.main : colors.error.main
                  }}
                >
                  {Math.abs(metric.change)}%
                </Typography>
              </Box>
            )}
          </Box>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              backgroundColor: metric.color + '20',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            {React.cloneElement(metric.icon as React.ReactElement<any>, {
              sx: { color: metric.color }
            })}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Analytics Dashboard</Typography>
        <Box display="flex" gap={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              label="Time Range"
            >
              <MenuItem value="day">Today</MenuItem>
              <MenuItem value="week">This Week</MenuItem>
              <MenuItem value="month">This Month</MenuItem>
              <MenuItem value="quarter">This Quarter</MenuItem>
              <MenuItem value="year">This Year</MenuItem>
            </Select>
          </FormControl>
          <ButtonGroup variant="outlined" size="small">
            <Tooltip title="Refresh">
              <Button onClick={handleRefresh}>
                <Refresh />
              </Button>
            </Tooltip>
            <Tooltip title="Export">
              <Button onClick={handleExport}>
                <Download />
              </Button>
            </Tooltip>
          </ButtonGroup>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Metric Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {metricCards.map((metric, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
            {renderMetricCard(metric)}
          </Grid>
        ))}
      </Grid>

      {/* Charts Row 1 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Activity Trend Chart */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Activity Trends
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <ChartTooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="testsStarted"
                    stackId="1"
                    stroke={colors.primary.main}
                    fill={colors.primary.light}
                    name="Tests Started"
                  />
                  <Area
                    type="monotone"
                    dataKey="testsCompleted"
                    stackId="1"
                    stroke={colors.success.main}
                    fill={colors.success.light}
                    name="Tests Completed"
                  />
                  <Area
                    type="monotone"
                    dataKey="observations"
                    stackId="1"
                    stroke={colors.warning.main}
                    fill={colors.warning.light}
                    name="Observations"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* User Activity Pie Chart */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                User Activity by Role
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={userActivityData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.role}: ${entry.count}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {userActivityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <ChartTooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Row 2 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Phase Completion Chart */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Phase Completion Status
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={phaseCompletionData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={100} />
                  <ChartTooltip />
                  <Legend />
                  <Bar dataKey="completed" stackId="a" fill={colors.success.main} name="Completed" />
                  <Bar dataKey="pending" stackId="a" fill={colors.grey[400]} name="Pending" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* SLA Performance Chart */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                SLA Performance by Phase
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={slaPerformanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="phase" />
                  <YAxis />
                  <ChartTooltip />
                  <Legend />
                  <Bar dataKey="onTime" stackId="a" fill={colors.success.main} name="On Time" />
                  <Bar dataKey="warning" stackId="a" fill={colors.warning.main} name="Warning" />
                  <Bar dataKey="violated" stackId="a" fill={colors.error.main} name="Violated" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity Table */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Recent Activity</Typography>
            <Button size="small" startIcon={<FilterList />}>
              Filter
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Cycle</TableCell>
                  <TableCell>Report</TableCell>
                  <TableCell>Phase</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Time</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {[1, 2, 3, 4, 5].map((row) => (
                  <TableRow key={row} hover>
                    <TableCell>TC-2024-{row.toString().padStart(3, '0')}</TableCell>
                    <TableCell>Quarterly Report {row}</TableCell>
                    <TableCell>
                      <Chip 
                        label="Test Execution" 
                        size="small"
                        sx={{ backgroundColor: colors.primary.light + '20' }}
                      />
                    </TableCell>
                    <TableCell>John Doe</TableCell>
                    <TableCell>Completed test case</TableCell>
                    <TableCell>{format(new Date(), 'MMM dd, HH:mm')}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default AnalyticsDashboard;