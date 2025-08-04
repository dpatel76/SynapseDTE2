import React, { useState, useEffect } from 'react';
import {
  Paper,
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Divider,
  Button,
} from '@mui/material';
import {
  CheckCircle as ApprovedIcon,
  Cancel as RejectedIcon,
  Visibility as ViewIcon,
  Comment as CommentIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  BugReport as BugReportIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import apiClient from '../../api/client';

interface ObservationReportOwnerFeedbackProps {
  cycleId: number;
  reportId: number;
  onRefresh?: () => void;
}

interface ObservationWithFeedback {
  observation_id: number;
  observation_title: string;
  observation_type: string;
  severity: string;
  tester_decision: string | null;
  report_owner_decision: string | null;
  report_owner_comments: string | null;
  attribute_name: string;
  created_at: string;
  updated_at: string;
}

export const ObservationReportOwnerFeedback: React.FC<ObservationReportOwnerFeedbackProps> = ({
  cycleId,
  reportId,
  onRefresh,
}) => {
  const [loading, setLoading] = useState(true);
  const [observations, setObservations] = useState<ObservationWithFeedback[]>([]);
  const [summary, setSummary] = useState({
    total: 0,
    approved: 0,
    rejected: 0,
    pending: 0,
  });

  useEffect(() => {
    fetchObservationsWithFeedback();
  }, [cycleId, reportId]);

  const fetchObservationsWithFeedback = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(
        `/observation-enhanced/${cycleId}/reports/${reportId}/observations`
      );
      
      const observationsData = response.data || [];
      
      // Filter observations that have report owner feedback
      const observationsWithFeedback = observationsData.filter((obs: any) => 
        obs.report_owner_decision !== null && obs.report_owner_decision !== undefined
      );
      
      // Calculate summary
      const summaryData = {
        total: observationsWithFeedback.length,
        approved: observationsWithFeedback.filter((obs: any) => obs.report_owner_decision === 'Approved').length,
        rejected: observationsWithFeedback.filter((obs: any) => obs.report_owner_decision === 'Rejected').length,
        pending: observationsWithFeedback.filter((obs: any) => 
          !obs.report_owner_decision || obs.report_owner_decision === 'Pending'
        ).length,
      };
      
      setObservations(observationsWithFeedback);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to fetch observations with feedback:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case 'HIGH':
        return 'error';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'info';
      default:
        return 'default';
    }
  };

  const getDecisionIcon = (decision: string | null) => {
    if (decision === 'Approved') {
      return <ApprovedIcon color="success" fontSize="small" />;
    } else if (decision === 'Rejected') {
      return <RejectedIcon color="error" fontSize="small" />;
    }
    return null;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (observations.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">
          No observations have been reviewed by the Report Owner yet.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mb: 3 }}>
        <Card variant="outlined">
          <CardContent sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="primary">
              {summary.total}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Reviewed
            </Typography>
          </CardContent>
        </Card>

        <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
          <CardContent sx={{ textAlign: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
              <ApprovedIcon color="success" />
              <Typography variant="h4" color="success.main">
                {summary.approved}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Approved
            </Typography>
          </CardContent>
        </Card>

        <Card variant="outlined" sx={{ borderColor: 'error.main' }}>
          <CardContent sx={{ textAlign: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
              <RejectedIcon color="error" />
              <Typography variant="h4" color="error.main">
                {summary.rejected}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Rejected
            </Typography>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="text.secondary">
              {summary.pending}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Pending Review
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Refresh Button */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button
          startIcon={<RefreshIcon />}
          onClick={() => {
            fetchObservationsWithFeedback();
            onRefresh?.();
          }}
          size="small"
        >
          Refresh
        </Button>
      </Box>

      {/* Observations Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Observation</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Attribute</TableCell>
              <TableCell>Tester Decision</TableCell>
              <TableCell>Report Owner Decision</TableCell>
              <TableCell>Report Owner Comments</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {observations.map((obs) => (
              <TableRow key={obs.observation_id}>
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {obs.observation_title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ID: {obs.observation_id}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={obs.observation_type}
                    size="small"
                    icon={<BugReportIcon />}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={obs.severity}
                    size="small"
                    color={getSeverityColor(obs.severity)}
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {obs.attribute_name}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {obs.tester_decision === 'Approved' && <ThumbUpIcon color="success" fontSize="small" />}
                    {obs.tester_decision === 'Rejected' && <ThumbDownIcon color="error" fontSize="small" />}
                    <Typography variant="body2">
                      {obs.tester_decision || 'Pending'}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {getDecisionIcon(obs.report_owner_decision)}
                    <Typography
                      variant="body2"
                      color={
                        obs.report_owner_decision === 'Approved' ? 'success.main' :
                        obs.report_owner_decision === 'Rejected' ? 'error.main' :
                        'text.primary'
                      }
                      fontWeight="medium"
                    >
                      {obs.report_owner_decision || 'Pending'}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell sx={{ maxWidth: 300 }}>
                  {obs.report_owner_comments ? (
                    <Tooltip title={obs.report_owner_comments}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <CommentIcon fontSize="small" color="action" />
                        <Typography
                          variant="body2"
                          sx={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            maxWidth: 250,
                          }}
                        >
                          {obs.report_owner_comments}
                        </Typography>
                      </Box>
                    </Tooltip>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No comments
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Tooltip title="View Details">
                    <IconButton size="small">
                      <ViewIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Summary Note */}
      {(summary.approved > 0 || summary.rejected > 0) && (
        <Box sx={{ mt: 3 }}>
          <Alert severity="info">
            <Typography variant="body2">
              Report Owner has reviewed {summary.total} observation{summary.total !== 1 ? 's' : ''}.
              {summary.rejected > 0 && (
                <> {summary.rejected} observation{summary.rejected !== 1 ? 's require' : ' requires'} further attention.</>
              )}
            </Typography>
          </Alert>
        </Box>
      )}
    </Box>
  );
};

export default ObservationReportOwnerFeedback;