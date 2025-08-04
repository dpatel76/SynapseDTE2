import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Paper,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Divider,
} from '@mui/material';
import {
  Timeline,
  TrendingUp,
  Assessment,
  Warning,
  CheckCircle,
  Schedule,
  Speed,
  Analytics as AnalyticsIcon,
  Insights,
  PieChart,
  Error,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const AnalyticsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  // Query for analytics data
  const {
    data: analyticsData,
    isLoading: analyticsLoading,
    error: analyticsError,
  } = useQuery({
    queryKey: ['analytics', 30],
    queryFn: () => analyticsApi.getAnalytics(30),
  });

  // Query for phase metrics
  const {
    data: phaseMetrics,
    isLoading: phaseMetricsLoading,
  } = useQuery({
    queryKey: ['phase-metrics'],
    queryFn: () => analyticsApi.getPhaseMetrics(),
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (analyticsLoading || phaseMetricsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (analyticsError) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load analytics data. Please try again later.
        </Alert>
      </Box>
    );
  }

  const overview = analyticsData?.overview || {
    total_cycles: 0,
    active_cycles: 0,
    completed_cycles: 0,
    completion_rate: 0,
    total_reports: 0,
    active_reports: 0,
    open_issues: 0,
    critical_issues: 0,
  };

  const performanceMetrics = analyticsData?.performance_metrics || [];
  const recentActivities = analyticsData?.recent_activities || [];
  const trendData = analyticsData?.trend_data || [];

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Analytics Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Comprehensive insights and performance metrics across all testing cycles and reports
        </Typography>
      </Box>

      {/* Key Metrics Overview */}
      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: 'repeat(1, 1fr)', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: 3,
          mb: 4 
        }}
      >
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" color="primary">
                  {overview.total_cycles}
                </Typography>
                <Typography variant="subtitle2">Total Cycles</Typography>
                <Typography variant="caption" color="text.secondary">
                  {overview.active_cycles} active
                </Typography>
              </Box>
              <Timeline color="primary" sx={{ fontSize: 40 }} />
            </Box>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" color="success.main">
                  {overview.completion_rate}%
                </Typography>
                <Typography variant="subtitle2">Completion Rate</Typography>
                <Typography variant="caption" color="text.secondary">
                  {overview.completed_cycles} completed
                </Typography>
              </Box>
              <CheckCircle color="success" sx={{ fontSize: 40 }} />
            </Box>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" color="info.main">
                  {overview.total_reports}
                </Typography>
                <Typography variant="subtitle2">Total Reports</Typography>
                <Typography variant="caption" color="text.secondary">
                  {overview.active_reports} active
                </Typography>
              </Box>
              <Assessment color="info" sx={{ fontSize: 40 }} />
            </Box>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" color="warning.main">
                  {overview.open_issues}
                </Typography>
                <Typography variant="subtitle2">Open Issues</Typography>
                <Typography variant="caption" color="text.secondary">
                  {overview.critical_issues} critical
                </Typography>
              </Box>
              <Warning color="warning" sx={{ fontSize: 40 }} />
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Tabs for detailed analytics */}
      <Paper>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="analytics tabs">
          <Tab label="Performance" icon={<TrendingUp />} />
          <Tab label="Trends" icon={<AnalyticsIcon />} />
          <Tab label="Activity" icon={<Schedule />} />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {/* Performance Metrics */}
          <Typography variant="h6" gutterBottom>
            Performance Metrics
          </Typography>
          <Box 
            sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: 'repeat(1, 1fr)', sm: 'repeat(2, 1fr)' },
              gap: 3 
            }}
          >
            {performanceMetrics.map((metric, index) => (
              <Card key={index}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="subtitle2">{metric.label}</Typography>
                    <Chip
                      label={`${metric.trend === 'up' ? '+' : '-'}${metric.trend_value}`}
                      color={metric.trend === 'up' ? 'success' : 'error'}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                  <Typography variant="h5" color="primary">
                    {metric.value}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* Trends */}
          <Typography variant="h6" gutterBottom>
            Trends Analysis
          </Typography>
          {trendData.length > 0 ? (
            <Box>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Showing cycle completion trends for the last 30 days
              </Typography>
              <Box sx={{ mt: 3 }}>
                {/* Simple trend visualization using progress bars */}
                {trendData.slice(-7).map((point, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                      <Typography variant="caption">
                        {new Date(point.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                      </Typography>
                      <Typography variant="caption" fontWeight="bold">
                        {point.value}
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={Math.min((point.value / Math.max(...trendData.map(d => d.value)) * 100) || 0, 100)}
                      sx={{ height: 8, borderRadius: 1 }}
                    />
                  </Box>
                ))}
              </Box>
              <Alert severity="info" sx={{ mt: 3 }}>
                <Typography variant="subtitle2">Chart Visualization Coming Soon</Typography>
                <Typography variant="body2">
                  Interactive charts with detailed trend analysis will be available in the next update.
                </Typography>
              </Alert>
            </Box>
          ) : (
            <Box textAlign="center" py={4}>
              <PieChart sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Trend Data Available
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Trend data will appear once there are completed cycles to analyze.
              </Typography>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          {/* Recent Activity */}
          <Typography variant="h6" gutterBottom>
            Recent Activity
          </Typography>
          {recentActivities.length > 0 ? (
            <List>
              {recentActivities.map((activity, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemIcon>
                      {activity.type === 'success' && <CheckCircle color="success" />}
                      {activity.type === 'info' && <Assessment color="info" />}
                      {activity.type === 'warning' && <Warning color="warning" />}
                      {activity.type === 'error' && <Error color="error" />}
                    </ListItemIcon>
                    <ListItemText
                      primary={activity.action}
                      secondary={
                        <>
                          <Typography component="span" variant="body2" display="block">
                            {activity.detail}
                          </Typography>
                          <Typography component="span" variant="caption" color="text.secondary" display="block">
                            {activity.time} {activity.user && `• ${activity.user}`}
                          </Typography>
                        </>
                      }
                    />
                  </ListItem>
                  {index < recentActivities.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          ) : (
            <Box textAlign="center" py={4}>
              <Schedule sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Recent Activity
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Activity logs will appear here as users interact with the system.
              </Typography>
            </Box>
          )}
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default AnalyticsPage; 