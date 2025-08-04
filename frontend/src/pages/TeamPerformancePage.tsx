import React, { useState, useEffect } from 'react';
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
  Avatar,
  AvatarGroup,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Tab,
  Tabs,
  Rating,
  Button,
  Stack,
  useTheme,
  alpha,
  Grid,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  People,
  TrendingUp,
  Speed,
  EmojiEvents,
  Assessment,
  Visibility,
  Download,
  CalendarToday,
  Refresh,
} from '@mui/icons-material';
import { Line, Bar } from 'react-chartjs-2';
import { useQuery } from '@tanstack/react-query';
import { cyclesApi } from '../api/cycles';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';

interface TeamMember {
  id: number;
  name: string;
  role: string;
  email: string;
  cycles_completed: number;
  tests_completed: number;
  completion_rate: number;
  quality_score: number;
  avg_cycle_time: number;
  status: string;
  assigned: number;
  completed: number;
  in_progress: number;
  avg_time: string;
}

interface TopPerformer {
  id: number;
  name: string;
  avatar: string;
  score: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const TeamPerformancePage: React.FC = () => {
  const theme = useTheme();
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [selectedPeriod, setSelectedPeriod] = useState('30d');
  const [selectedCycle, setSelectedCycle] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch available cycles
  const { data: cyclesData } = useQuery({
    queryKey: ['cycles-for-team-performance'],
    queryFn: async () => {
      const response = await cyclesApi.getAll(1, 100);
      return response.items.filter((c: any) => c.status === 'Active');
    },
  });

  // Fetch team performance metrics
  const { data: performanceData, isLoading, refetch } = useQuery({
    queryKey: ['team-performance', selectedPeriod, selectedCycle],
    queryFn: async () => {
      const params = new URLSearchParams({
        time_period: selectedPeriod,
      });
      if (selectedCycle) {
        params.append('cycle_id', selectedCycle.toString());
      }
      
      const response = await apiClient.get(`/metrics/team-performance?${params}`);
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

  const teamMetrics = performanceData?.metrics || {
    total_testers: 0,
    active_testers: 0,
    avg_completion_rate: 0,
    avg_quality_score: 0,
    total_tests_completed: 0,
  };

  const topPerformers = performanceData?.top_performers || [];
  const teamMembers = performanceData?.team_members || [];

  const performanceTrendData = {
    labels: performanceData?.performance_trend?.labels || [],
    datasets: [
      {
        label: 'Completion Rate',
        data: performanceData?.performance_trend?.completion_rate || [],
        borderColor: theme.palette.success.main,
        backgroundColor: alpha(theme.palette.success.main, 0.1),
        tension: 0.3,
      },
      {
        label: 'Quality Score',
        data: performanceData?.performance_trend?.quality_score || [],
        borderColor: theme.palette.primary.main,
        backgroundColor: alpha(theme.palette.primary.main, 0.1),
        tension: 0.3,
      },
    ],
  };

  const workloadDistribution = {
    labels: performanceData?.workload_distribution?.labels || [],
    datasets: [
      {
        label: 'Assigned',
        data: performanceData?.workload_distribution?.assigned || [],
        backgroundColor: alpha(theme.palette.primary.main, 0.8),
      },
      {
        label: 'Completed',
        data: performanceData?.workload_distribution?.completed || [],
        backgroundColor: alpha(theme.palette.success.main, 0.8),
      },
    ],
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Team Performance
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor and analyze your testing team's performance and productivity
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Period</InputLabel>
            <Select
              value={selectedPeriod}
              label="Period"
              onChange={(e) => setSelectedPeriod(e.target.value)}
            >
              <MenuItem value="7d">Last 7 Days</MenuItem>
              <MenuItem value="30d">Last 30 Days</MenuItem>
              <MenuItem value="90d">Last 90 Days</MenuItem>
            </Select>
          </FormControl>
          
          {cyclesData && cyclesData.length > 0 && (
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Test Cycle</InputLabel>
              <Select
                value={selectedCycle || ''}
                label="Test Cycle"
                onChange={(e) => setSelectedCycle(e.target.value ? Number(e.target.value) : null)}
              >
                <MenuItem value="">All Cycles</MenuItem>
                {cyclesData.map((cycle: any) => (
                  <MenuItem key={cycle.cycle_id} value={cycle.cycle_id}>
                    {cycle.cycle_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          
          <Tooltip title="Refresh data">
            <IconButton onClick={handleRefresh} disabled={refreshing}>
              <Refresh className={refreshing ? 'rotating' : ''} />
            </IconButton>
          </Tooltip>
          
          <Button variant="outlined" startIcon={<Download />}>
            Export Report
          </Button>
        </Stack>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid  size={{ xs: 12, sm: 6 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Total Team Size
                  </Typography>
                  <Typography variant="h4">{teamMetrics.total_testers}</Typography>
                  <Typography variant="caption" color="success.main">
                    {teamMetrics.active_testers} active
                  </Typography>
                </Box>
                <People sx={{ fontSize: 40, color: theme.palette.primary.main }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid  size={{ xs: 12, sm: 6 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Avg Completion Rate
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {teamMetrics.avg_completion_rate}%
                  </Typography>
                  <Typography variant="caption">+3% from last month</Typography>
                </Box>
                <TrendingUp sx={{ fontSize: 40, color: theme.palette.success.main }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid  size={{ xs: 12, sm: 6 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Quality Score
                  </Typography>
                  <Typography variant="h4" color="primary">
                    {teamMetrics.avg_quality_score}
                  </Typography>
                  <Rating value={4.5} readOnly size="small" sx={{ mt: 0.5 }} />
                </Box>
                <EmojiEvents sx={{ fontSize: 40, color: theme.palette.warning.main }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid  size={{ xs: 12, sm: 6 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Tests Completed
                  </Typography>
                  <Typography variant="h4">{teamMetrics.total_tests_completed}</Typography>
                  <Typography variant="caption">This month</Typography>
                </Box>
                <Assessment sx={{ fontSize: 40, color: theme.palette.info.main }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid  size={{ xs: 12, sm: 6 }}>
          <Card
            sx={{
              background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.primary.main, 0.05)} 100%)`,
              border: `1px solid ${theme.palette.primary.main}`,
            }}
          >
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>
                Top Performers
              </Typography>
              <AvatarGroup max={4}>
                {topPerformers.map((performer: TopPerformer) => (
                  <Tooltip key={performer.id} title={`${performer.name} - Score: ${performer.score}`}>
                    <Avatar>{performer.avatar}</Avatar>
                  </Tooltip>
                ))}
              </AvatarGroup>
              <Typography variant="caption" display="block" mt={1}>
                Based on quality & speed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Team Overview" />
          <Tab label="Performance Trends" />
          <Tab label="Workload Distribution" />
        </Tabs>
      </Paper>

      {/* Team Overview Tab */}
      <TabPanel value={tabValue} index={0}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Team Members Performance
          </Typography>
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Tester</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell align="center">Assigned</TableCell>
                  <TableCell align="center">Completed</TableCell>
                  <TableCell align="center">In Progress</TableCell>
                  <TableCell align="center">Completion Rate</TableCell>
                  <TableCell align="center">Quality Score</TableCell>
                  <TableCell align="center">Avg Time</TableCell>
                  <TableCell align="center">Status</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {teamMembers.map((member: TeamMember) => (
                  <TableRow key={member.id}>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Avatar sx={{ width: 32, height: 32 }}>
                          {member.name.split(' ').map((n: string) => n[0]).join('')}
                        </Avatar>
                        <Typography variant="subtitle2">{member.name}</Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{member.role}</TableCell>
                    <TableCell align="center">{member.assigned}</TableCell>
                    <TableCell align="center">{member.completed}</TableCell>
                    <TableCell align="center">{member.in_progress}</TableCell>
                    <TableCell align="center">
                      <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                        <LinearProgress
                          variant="determinate"
                          value={member.completion_rate}
                          sx={{ width: 60, height: 6 }}
                        />
                        <Typography variant="body2">{member.completion_rate}%</Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={member.quality_score}
                        color={member.quality_score >= 90 ? 'success' : 'primary'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">{member.avg_time}</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={member.status}
                        color="success"
                        size="small"
                        variant="outlined"
                      />
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
      </TabPanel>

      {/* Performance Trends Tab */}
      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Team Performance Trends
          </Typography>
          <Box sx={{ height: 400 }}>
            <Line
              data={performanceTrendData}
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
      </TabPanel>

      {/* Workload Distribution Tab */}
      <TabPanel value={tabValue} index={2}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Workload Distribution
          </Typography>
          <Box sx={{ height: 400 }}>
            <Bar
              data={workloadDistribution}
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
                  },
                },
              }}
            />
          </Box>
        </Paper>
      </TabPanel>
      
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

export default TeamPerformancePage;