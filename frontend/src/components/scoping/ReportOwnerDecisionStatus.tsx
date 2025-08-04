import React from 'react';
import { Box, Chip, Tooltip, Typography } from '@mui/material';
import { CheckCircle, Cancel, HelpOutline } from '@mui/icons-material';

interface ReportOwnerDecisionStatusProps {
  status?: string;
  notes?: string;
  rejectionReason?: string;
  approvedAt?: string;
  rejectedAt?: string;
}

const ReportOwnerDecisionStatus: React.FC<ReportOwnerDecisionStatusProps> = ({
  status = 'Pending',
  notes,
  rejectionReason,
  approvedAt,
  rejectedAt
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'Approved':
        return {
          color: 'success' as const,
          icon: <CheckCircle fontSize="small" />,
          label: 'RO Approved'
        };
      case 'Rejected':
        return {
          color: 'error' as const,
          icon: <Cancel fontSize="small" />,
          label: 'RO Rejected'
        };
      default:
        return {
          color: 'default' as const,
          icon: <HelpOutline fontSize="small" />,
          label: 'RO Pending'
        };
    }
  };

  const config = getStatusConfig();
  const hasDetails = notes || rejectionReason || approvedAt || rejectedAt;

  if (!hasDetails) {
    return (
      <Chip
        size="small"
        label={config.label}
        color={config.color}
        icon={config.icon}
        variant="outlined"
      />
    );
  }

  return (
    <Tooltip
      title={
        <Box sx={{ p: 1 }}>
          <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
            Report Owner Decision
          </Typography>
          <Typography variant="body2" gutterBottom>
            <strong>Status:</strong> {status}
          </Typography>
          {approvedAt && (
            <Typography variant="body2" gutterBottom>
              <strong>Approved:</strong> {new Date(approvedAt).toLocaleString()}
            </Typography>
          )}
          {rejectedAt && (
            <Typography variant="body2" gutterBottom>
              <strong>Rejected:</strong> {new Date(rejectedAt).toLocaleString()}
            </Typography>
          )}
          {notes && (
            <Typography variant="body2" gutterBottom>
              <strong>Notes:</strong> {notes}
            </Typography>
          )}
          {rejectionReason && (
            <Typography variant="body2">
              <strong>Rejection Reason:</strong> {rejectionReason}
            </Typography>
          )}
        </Box>
      }
      arrow
    >
      <Chip
        size="small"
        label={config.label}
        color={config.color}
        icon={config.icon}
        variant="outlined"
        sx={{ cursor: 'pointer' }}
      />
    </Tooltip>
  );
};

export default ReportOwnerDecisionStatus;