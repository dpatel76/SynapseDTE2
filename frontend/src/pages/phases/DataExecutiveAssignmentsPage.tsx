import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Stack,
  Button
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Email as EmailIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'react-hot-toast';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';

interface CDOAssignment {
  assignment_id: number;
  attribute_id: number;
  attribute_name: string;
  attribute_description: string;
  data_provider_id: number;
  data_provider_name: string;
  data_provider_email: string;
  lob_name: string;
  assigned_at: string;
  status: 'Assigned' | 'In Progress' | 'Completed' | 'Overdue';
  cycle_id: number;
  report_id: number;
}

const DataExecutiveAssignmentsPage: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<CDOAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cycleIdNum = cycleId ? parseInt(cycleId, 10) : 0;
  const reportIdNum = reportId ? parseInt(reportId, 10) : 0;
  
  const { data: unifiedPhaseStatus, isLoading: statusLoading, refetch: refetchStatus } = usePhaseStatus('Data Provider ID', cycleIdNum, reportIdNum);

  useEffect(() => {
    if (cycleIdNum && reportIdNum) {
      loadAssignments();
    }
  }, [cycleIdNum, reportIdNum]);

  const loadAssignments = async () => {
    setLoading(true);
    setError(null);
    try {
      // Use universal assignments endpoint
      const response = await apiClient.get('/universal-assignments/assignments', {
        params: {
          context_type_filter: 'Report,Attribute',
          assignment_type_filter: 'LOB Assignment,Data Upload Request',
          status_filter: 'Assigned,In Progress,Acknowledged',
          limit: 50
        }
      });
      
      // Filter assignments for this specific cycle/report
      const filteredAssignments = response.data.filter((assignment: any) => 
        assignment.context_data?.cycle_id === cycleIdNum && 
        assignment.context_data?.report_id === reportIdNum
      );
      
      // Transform universal assignments to CDOAssignment format for backward compatibility
      const transformedAssignments = filteredAssignments.map((assignment: any) => ({
        assignment_id: assignment.assignment_id,
        attribute_id: assignment.context_data?.attribute_id || 0,
        attribute_name: `Attribute ${assignment.context_data?.attribute_id || 'N/A'}`,
        attribute_description: assignment.description,
        data_provider_id: assignment.to_user_id || 0,
        data_provider_name: assignment.to_user_name || 'Unknown',
        data_provider_email: 'N/A', // Email not included in universal assignment response
        lob_name: assignment.context_data?.lob_linkage || 'Unknown LOB',
        assigned_at: assignment.assigned_at,
        status: assignment.status,
        cycle_id: assignment.context_data?.cycle_id || cycleIdNum,
        report_id: assignment.context_data?.report_id || reportIdNum
      }));
      
      setAssignments(transformedAssignments);
    } catch (error: any) {
      console.error('Error loading universal assignments:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to load assignments from universal assignment framework';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadAssignments();
    refetchStatus();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed': return 'success';
      case 'In Progress': return 'info';
      case 'Assigned': return 'primary';
      case 'Overdue': return 'error';
      default: return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Stack spacing={3}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton 
              onClick={() => navigate(`/cycles/${cycleId}/reports/${reportId}/data-owner`)}
              color="primary"
            >
              <ArrowBackIcon />
            </IconButton>
            <Box>
              <Typography variant="h4" gutterBottom>
                My Data Owner Assignments
              </Typography>
              <Typography variant="body1" color="text.secondary">
                View all attributes you've assigned data providers for in this testing cycle
              </Typography>
            </Box>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>

        {/* Summary Cards */}
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h4" color="primary.main">
                {assignments.length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Total Assignments
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h4" color="success.main">
                {assignments.filter(a => a.status === 'Completed').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Completed
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h4" color="info.main">
                {assignments.filter(a => a.status === 'In Progress').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                In Progress
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h4" color="error.main">
                {assignments.filter(a => a.status === 'Overdue').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Overdue
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error">
            {error}
          </Alert>
        )}

        {/* Assignments Table */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Assignment Details
            </Typography>
            
            {assignments.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <AssignmentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No Assignments Found
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  You haven't assigned any data providers for this report in this testing cycle yet.
                </Typography>
              </Box>
            ) : (
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Attribute</TableCell>
                      <TableCell>Data Owner</TableCell>
                      <TableCell>LOB</TableCell>
                      <TableCell>Assigned Date</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {assignments.map((assignment) => (
                      <TableRow key={assignment.assignment_id} hover>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {assignment.attribute_name}
                            </Typography>
                            {assignment.attribute_description && (
                              <Typography variant="caption" color="text.secondary" display="block">
                                {assignment.attribute_description}
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <PersonIcon fontSize="small" color="primary" />
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {assignment.data_provider_name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {assignment.data_provider_email}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <BusinessIcon fontSize="small" color="primary" />
                            <Typography variant="body2">
                              {assignment.lob_name}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <ScheduleIcon fontSize="small" color="action" />
                            <Typography variant="body2">
                              {formatDate(assignment.assigned_at)}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={assignment.status}
                            size="small"
                            color={getStatusColor(assignment.status) as any}
                          />
                        </TableCell>
                        <TableCell>
                          <Tooltip title="Send Email">
                            <IconButton 
                              size="small"
                              href={`mailto:${assignment.data_provider_email}?subject=Data Owner Assignment - ${assignment.attribute_name}`}
                            >
                              <EmailIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </Stack>
    </Container>
  );
};

export default DataExecutiveAssignmentsPage;