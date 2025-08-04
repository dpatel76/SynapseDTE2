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
  useTheme,
  alpha,
  Grid,
  CircularProgress,
} from '@mui/material';
import {
  Flag,
  Warning,
  CheckCircle,
  Schedule,
  TrendingUp,
  Visibility,
  Refresh,
  Download,
  Timeline,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/client';

const SLATrackingPage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { user } = useAuth();
  const [refreshing, setRefreshing] = useState(false);

  // Fetch SLA metrics from API
  const { data: slaData, isLoading, refetch } = useQuery({
    queryKey: ['sla-tracking-data', user?.user_id],
    queryFn: async () => {
      try {
        // Get SLA compliance data
        const response = await apiClient.get('/admin/sla/compliance');
        return response.data;
      } catch (error) {
        console.error('Error fetching SLA data:', error);
        // Return default structure if API fails
        return {
          metrics: {
            overall_compliance: 0,
            on_track: 0,
            at_risk: 0,
            breached: 0,
            escalations: 0,
          },
          items: []
        };
      }
    },
    enabled: !!user?.user_id,
  });

  const slaMetrics = slaData?.metrics || {
    overall_compliance: 0,
    on_track: 0,
    at_risk: 0,
    breached: 0,
    escalations: 0,
  };

  const slaItems = slaData?.items || [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'on_track':
        return 'success';
      case 'at_risk':
        return 'warning';
      case 'breached':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'on_track':
        return 'On Track';
      case 'at_risk':
        return 'At Risk';
      case 'breached':
        return 'Breached';
      default:
        return status;
    }
  };

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

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            SLA Compliance Tracking
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor and manage SLA compliance across all test cycles and reports
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button variant="outlined" startIcon={<Download />}>
            Export Report
          </Button>
          <Tooltip title="Refresh data">
            <IconButton onClick={handleRefresh} disabled={refreshing}>
              <Refresh className={refreshing ? 'rotating' : ''} />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid  size={{ xs: 12, sm: 6 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Overall Compliance
                  </Typography>
                  <Typography variant="h4" color="primary">
                    {slaMetrics.overall_compliance}%
                  </Typography>
                </Box>
                <CheckCircle sx={{ color: theme.palette.primary.main }} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={slaMetrics.overall_compliance}
                sx={{ mt: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid  size={{ xs: 12, sm: 6 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    On Track
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {slaMetrics.on_track}
                  </Typography>
                </Box>
                <TrendingUp sx={{ color: theme.palette.success.main }} />
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
                    At Risk
                  </Typography>
                  <Typography variant="h4" color="warning.main">
                    {slaMetrics.at_risk}
                  </Typography>
                </Box>
                <Warning sx={{ color: theme.palette.warning.main }} />
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
                    Breached
                  </Typography>
                  <Typography variant="h4" color="error.main">
                    {slaMetrics.breached}
                  </Typography>
                </Box>
                <Flag sx={{ color: theme.palette.error.main }} />
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
                    Escalations
                  </Typography>
                  <Typography variant="h4" color="error.main">
                    {slaMetrics.escalations}
                  </Typography>
                </Box>
                <Schedule sx={{ color: theme.palette.error.main }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* SLA Items Table */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          SLA Status by Report
        </Typography>
        
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Report Name</TableCell>
                <TableCell>Current Phase</TableCell>
                <TableCell>Due Date</TableCell>
                <TableCell>Days Remaining</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Owner</TableCell>
                <TableCell>Progress</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {slaItems.map((item: any) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <Typography variant="subtitle2">{item.report_name}</Typography>
                  </TableCell>
                  <TableCell>{item.phase}</TableCell>
                  <TableCell>{new Date(item.due_date).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <Chip
                      label={item.days_remaining > 0 ? `${item.days_remaining} days` : `${Math.abs(item.days_remaining)} days overdue`}
                      size="small"
                      color={item.days_remaining > 0 ? 'default' : 'error'}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getStatusLabel(item.status)}
                      size="small"
                      color={getStatusColor(item.status)}
                    />
                  </TableCell>
                  <TableCell>{item.owner}</TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <LinearProgress
                        variant="determinate"
                        value={item.completion}
                        sx={{ width: 80, height: 6 }}
                      />
                      <Typography variant="body2">{item.completion}%</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
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

        {slaMetrics.breached > 0 && (
          <Alert severity="error" sx={{ mt: 3 }}>
            <Typography variant="body2">
              <strong>{slaMetrics.breached} SLA breaches detected.</strong> Immediate action required to address overdue items.
            </Typography>
          </Alert>
        )}
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

export default SLATrackingPage;