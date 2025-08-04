import React from 'react';
import {
  Paper,
  Box,
  Typography,
  Button,
  Alert,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Divider,
} from '@mui/material';
import {
  CheckCircle as ApprovedIcon,
  Cancel as RejectedIcon,
  Warning as ChangesIcon,
  Refresh as RefreshIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material';
import { RFIVersion } from '../../types/rfiVersions';

interface RFIReportOwnerFeedbackProps {
  version: RFIVersion;
  onMakeChanges?: () => void;
  isReadOnly?: boolean;
}

export const RFIReportOwnerFeedback: React.FC<RFIReportOwnerFeedbackProps> = ({
  version,
  onMakeChanges,
  isReadOnly = false,
}) => {
  if (!version.has_report_owner_feedback || !version.report_owner_feedback_summary) {
    return null;
  }

  const feedback = version.report_owner_feedback_summary;
  const needsChanges = feedback.rejected > 0 || feedback.changes_requested > 0;
  const completedDate = feedback.completed_at ? new Date(feedback.completed_at) : null;

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Report Owner Feedback</Typography>
        {completedDate && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TimeIcon fontSize="small" color="action" />
            <Typography variant="body2" color="text.secondary">
              Completed: {completedDate.toLocaleDateString()}
            </Typography>
          </Box>
        )}
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2, mb: 3 }}>
        <Card variant="outlined">
          <CardContent sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="primary">
              {feedback.total_reviewed}
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
                {feedback.approved}
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
                {feedback.rejected}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Rejected
            </Typography>
          </CardContent>
        </Card>

        <Card variant="outlined" sx={{ borderColor: 'warning.main' }}>
          <CardContent sx={{ textAlign: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
              <ChangesIcon color="warning" />
              <Typography variant="h4" color="warning.main">
                {feedback.changes_requested}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Changes Requested
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Progress Bar */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2">Approval Rate</Typography>
          <Typography variant="body2" fontWeight="bold">
            {Math.round((feedback.approved / feedback.total_reviewed) * 100)}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={(feedback.approved / feedback.total_reviewed) * 100}
          sx={{ height: 8, borderRadius: 1 }}
          color="success"
        />
      </Box>

      {needsChanges && (
        <>
          <Divider sx={{ my: 2 }} />
          
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body2" fontWeight="bold" gutterBottom>
              Action Required
            </Typography>
            <Typography variant="body2">
              The Report Owner has identified {feedback.rejected + feedback.changes_requested} evidence items 
              that need attention. Please review their feedback and make necessary adjustments.
            </Typography>
          </Alert>

          {!isReadOnly && onMakeChanges && (
            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={<RefreshIcon />}
                onClick={onMakeChanges}
                size="large"
              >
                Make Changes
              </Button>
            </Box>
          )}
        </>
      )}

      {!needsChanges && (
        <Alert severity="success">
          All evidence has been approved by the Report Owner. No further action required.
        </Alert>
      )}
    </Paper>
  );
};