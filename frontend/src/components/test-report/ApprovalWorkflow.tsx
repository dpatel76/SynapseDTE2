import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  Divider,
  Paper,
  LinearProgress
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  Person as PersonIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import apiClient from '../../api/client';
import SectionApprovalCard from './SectionApprovalCard';
import Grid from '@mui/material/Grid';

interface ApprovalWorkflowProps {
  cycleId: number;
  reportId: number;
  userRole: string;
  onPhaseComplete?: () => void;
}

interface Section {
  id: number;
  section_name: string;
  section_title: string;
  section_order: number;
  status: string;
  last_generated_at: string | null;
  requires_refresh: boolean;
  approval_status: string;
  next_approver: string | null;
  is_fully_approved: boolean;
  data_sources: string[];
  approvals: {
    tester: {
      approved: boolean;
      approved_by: number | null;
      approved_at: string | null;
      notes: string | null;
    };
    report_owner: {
      approved: boolean;
      approved_by: number | null;
      approved_at: string | null;
      notes: string | null;
    };
    executive: {
      approved: boolean;
      approved_by: number | null;
      approved_at: string | null;
      notes: string | null;
    };
  };
}

interface ApprovalStatus {
  total_sections: number;
  pending_tester: number;
  pending_report_owner: number;
  pending_executive: number;
  fully_approved: number;
  rejected: number;
  revision_requested: number;
  sections: any[];
}

const ApprovalWorkflow: React.FC<ApprovalWorkflowProps> = ({
  cycleId,
  reportId,
  userRole,
  onPhaseComplete
}) => {
  const [sections, setSections] = useState<Section[]>([]);
  const [approvalStatus, setApprovalStatus] = useState<ApprovalStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch sections with approval details
      const sectionsResponse = await apiClient.get(
        `/test-report/${cycleId}/reports/${reportId}/sections`
      );
      setSections(sectionsResponse.data);

      // Fetch approval status summary
      const statusResponse = await apiClient.get(
        `/test-report/${cycleId}/reports/${reportId}/approvals`
      );
      setApprovalStatus(statusResponse.data);
    } catch (error: any) {
      console.error('Error fetching approval data:', error);
      setError('Failed to load approval data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [cycleId, reportId]);

  const handleCompletePhase = async () => {
    try {
      setCompleting(true);
      
      await apiClient.post(
        `/test-report/${cycleId}/reports/${reportId}/complete`
      );
      
      if (onPhaseComplete) {
        onPhaseComplete();
      }
    } catch (error: any) {
      console.error('Error completing phase:', error);
      alert(error.response?.data?.detail || 'Failed to complete phase');
    } finally {
      setCompleting(false);
    }
  };

  const getCompletionPercentage = () => {
    if (!approvalStatus) return 0;
    return (approvalStatus.fully_approved / approvalStatus.total_sections) * 100;
  };

  const canCompletePhase = () => {
    return approvalStatus?.fully_approved === approvalStatus?.total_sections;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={fetchData}>
          Retry
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  if (!approvalStatus) {
    return (
      <Alert severity="info">
        No approval data available
      </Alert>
    );
  }

  return (
    <Box>
      {/* Approval Status Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AssessmentIcon color="primary" />
              Approval Status Overview
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={<RefreshIcon />}
              onClick={fetchData}
            >
              Refresh
            </Button>
          </Box>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="primary">
                  {approvalStatus.total_sections}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Sections
                </Typography>
              </Paper>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {approvalStatus.fully_approved}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Fully Approved
                </Typography>
              </Paper>
            </Grid>
          </Grid>

          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Completion Progress
            </Typography>
            <LinearProgress
              variant="determinate"
              value={getCompletionPercentage()}
              sx={{ height: 8, borderRadius: 4 }}
            />
            <Typography variant="caption" color="text.secondary">
              {getCompletionPercentage().toFixed(0)}% Complete
            </Typography>
          </Box>

          <Grid container spacing={2}>
            <Grid size={{ xs: 6, md: 3 }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" color="info.main">
                  {approvalStatus.pending_tester}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Pending Tester
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 6, md: 3 }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" color="warning.main">
                  {approvalStatus.pending_report_owner}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Pending Owner
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 6, md: 3 }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" color="error.main">
                  {approvalStatus.pending_executive}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Pending Executive
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 6, md: 3 }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" color="text.secondary">
                  {approvalStatus.rejected + approvalStatus.revision_requested}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Rejected/Revision
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Phase Completion */}
      {canCompletePhase() && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                All sections approved!
              </Typography>
              <Typography variant="body2">
                The test report phase can now be completed.
              </Typography>
            </Box>
            <Button
              variant="contained"
              color="success"
              onClick={handleCompletePhase}
              disabled={completing}
              startIcon={completing ? <CircularProgress size={20} /> : <CheckCircleIcon />}
            >
              {completing ? 'Completing...' : 'Complete Phase'}
            </Button>
          </Box>
        </Alert>
      )}

      {/* Sections List */}
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <PersonIcon color="primary" />
        Section Approvals
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Review and approve each section below. All sections must be approved before the phase can be completed.
      </Typography>

      {sections.length === 0 ? (
        <Alert severity="info">
          No sections available for approval. Generate the report first.
        </Alert>
      ) : (
        sections
          .sort((a, b) => a.section_order - b.section_order)
          .map((section) => (
            <SectionApprovalCard
              key={section.id}
              section={section}
              cycleId={cycleId}
              reportId={reportId}
              userRole={userRole}
              onSectionUpdated={fetchData}
            />
          ))
      )}
    </Box>
  );
};

export default ApprovalWorkflow;