import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  People as PeopleIcon,
  Business as BusinessIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { PhaseAssignmentDashboard } from '../../api/dataOwnerLobAssignment';

interface AssignmentAnalyticsProps {
  phaseId: number;
  dashboard: PhaseAssignmentDashboard;
}

const AssignmentAnalytics: React.FC<AssignmentAnalyticsProps> = ({
  phaseId,
  dashboard
}) => {
  const summary = dashboard.assignment_summary;

  // Calculate percentages
  const assignmentProgress = summary.total_assignments > 0 ? 
    (summary.assigned_count / summary.total_assignments) * 100 : 0;
  
  const acknowledgmentProgress = summary.assigned_count > 0 ? 
    (summary.acknowledged_count / summary.assigned_count) * 100 : 0;

  // Calculate workload distribution
  const totalAssignments = dashboard.data_owner_workload.reduce((sum, workload) => sum + workload.total_assignments, 0);
  const avgAssignmentsPerOwner = dashboard.data_owner_workload.length > 0 ? 
    totalAssignments / dashboard.data_owner_workload.length : 0;

  // Find most and least loaded data owners
  const mostLoadedOwner = dashboard.data_owner_workload.reduce((max, owner) => 
    owner.total_assignments > max.total_assignments ? owner : max, 
    dashboard.data_owner_workload[0] || { total_assignments: 0, data_owner_name: 'N/A' }
  );

  const leastLoadedOwner = dashboard.data_owner_workload.reduce((min, owner) => 
    owner.total_assignments < min.total_assignments ? owner : min, 
    dashboard.data_owner_workload[0] || { total_assignments: 0, data_owner_name: 'N/A' }
  );

  // Calculate LOB coverage
  const lobCoverage = dashboard.lob_breakdown.map(lob => ({
    ...lob,
    coverage_percentage: lob.total_attributes > 0 ? (lob.assigned_attributes / lob.total_attributes) * 100 : 0,
    acknowledgment_percentage: lob.assigned_attributes > 0 ? (lob.acknowledged_attributes / lob.assigned_attributes) * 100 : 0
  }));

  if (summary.total_assignments === 0) {
    return (
      <Alert severity="info">
        No assignment data available for analytics. Create assignments to see analytics.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <AssignmentIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Assignment Progress</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {assignmentProgress.toFixed(1)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={assignmentProgress} 
                sx={{ mt: 1, mb: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {summary.assigned_count} of {summary.total_assignments} assigned
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Acknowledgment Rate</Typography>
              </Box>
              <Typography variant="h4" color="success.main">
                {acknowledgmentProgress.toFixed(1)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={acknowledgmentProgress} 
                color="success"
                sx={{ mt: 1, mb: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {summary.acknowledged_count} of {summary.assigned_count} acknowledged
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <PeopleIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">Active Data Owners</Typography>
              </Box>
              <Typography variant="h4" color="info.main">
                {dashboard.data_owner_workload.length}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Avg: {avgAssignmentsPerOwner.toFixed(1)} assignments/owner
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <BusinessIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6">LOB Coverage</Typography>
              </Box>
              <Typography variant="h4" color="warning.main">
                {dashboard.lob_breakdown.length}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Lines of Business involved
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Workload Distribution */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Data Owner Workload Distribution
              </Typography>
              
              {dashboard.data_owner_workload.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Data Owner</TableCell>
                        <TableCell align="right">Total</TableCell>
                        <TableCell align="right">Acknowledged</TableCell>
                        <TableCell align="right">Rate</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {dashboard.data_owner_workload
                        .sort((a, b) => b.total_assignments - a.total_assignments)
                        .map((workload) => {
                          const ackRate = workload.total_assignments > 0 ? 
                            (workload.acknowledged_assignments / workload.total_assignments) * 100 : 0;
                          
                          return (
                            <TableRow key={workload.data_owner_id}>
                              <TableCell>
                                <Typography variant="body2">
                                  {workload.data_owner_name}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">
                                <Chip 
                                  label={workload.total_assignments}
                                  size="small"
                                  color={workload.total_assignments > avgAssignmentsPerOwner ? 'warning' : 'default'}
                                />
                              </TableCell>
                              <TableCell align="right">
                                {workload.acknowledged_assignments}
                              </TableCell>
                              <TableCell align="right">
                                <Chip 
                                  label={`${ackRate.toFixed(0)}%`}
                                  size="small"
                                  color={ackRate >= 80 ? 'success' : ackRate >= 50 ? 'warning' : 'error'}
                                />
                              </TableCell>
                            </TableRow>
                          );
                        })}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No data owner workload data available.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                LOB Assignment Coverage
              </Typography>
              
              {lobCoverage.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>LOB</TableCell>
                        <TableCell align="right">Total</TableCell>
                        <TableCell align="right">Assigned</TableCell>
                        <TableCell align="right">Coverage</TableCell>
                        <TableCell align="right">Ack Rate</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {lobCoverage
                        .sort((a, b) => b.coverage_percentage - a.coverage_percentage)
                        .map((lob) => (
                          <TableRow key={lob.lob_id}>
                            <TableCell>
                              <Typography variant="body2">
                                {lob.lob_name}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              {lob.total_attributes}
                            </TableCell>
                            <TableCell align="right">
                              {lob.assigned_attributes}
                            </TableCell>
                            <TableCell align="right">
                              <Chip 
                                label={`${lob.coverage_percentage.toFixed(0)}%`}
                                size="small"
                                color={lob.coverage_percentage >= 80 ? 'success' : lob.coverage_percentage >= 50 ? 'warning' : 'error'}
                              />
                            </TableCell>
                            <TableCell align="right">
                              <Chip 
                                label={`${lob.acknowledgment_percentage.toFixed(0)}%`}
                                size="small"
                                color={lob.acknowledgment_percentage >= 80 ? 'success' : lob.acknowledgment_percentage >= 50 ? 'warning' : 'default'}
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No LOB breakdown data available.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Summary Insights */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Workload Balance
              </Typography>
              
              <Grid container spacing={2}>
                <Grid size={{ xs: 6 }}>
                  <Box textAlign="center">
                    <Typography variant="body2" color="text.secondary">
                      Most Loaded
                    </Typography>
                    <Typography variant="h6" color="warning.main">
                      {mostLoadedOwner.data_owner_name}
                    </Typography>
                    <Typography variant="body2">
                      {mostLoadedOwner.total_assignments} assignments
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid size={{ xs: 6 }}>
                  <Box textAlign="center">
                    <Typography variant="body2" color="text.secondary">
                      Least Loaded
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      {leastLoadedOwner.data_owner_name}
                    </Typography>
                    <Typography variant="body2">
                      {leastLoadedOwner.total_assignments} assignments
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Consider redistributing assignments if workload imbalance is significant.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Key Metrics
              </Typography>
              
              <Grid container spacing={2}>
                <Grid size={{ xs: 6 }}>
                  <Box textAlign="center">
                    <WarningIcon color="warning" sx={{ fontSize: 40 }} />
                    <Typography variant="h6" color="warning.main">
                      {summary.pending_acknowledgment_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Pending Acknowledgments
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid size={{ xs: 6 }}>
                  <Box textAlign="center">
                    <AnalyticsIcon color="info" sx={{ fontSize: 40 }} />
                    <Typography variant="h6" color="info.main">
                      {summary.unassigned_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Unassigned Items
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Focus on reducing unassigned items and following up on pending acknowledgments.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AssignmentAnalytics;