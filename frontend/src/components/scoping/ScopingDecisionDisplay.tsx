import React from 'react';
import { Box, Chip, Tooltip, Typography } from '@mui/material';
import { 
  CheckCircle as CheckCircleIcon, 
  Cancel as CancelIcon,
  HelpOutline as PendingIcon,
  Lock as LockIcon,
  Info as InfoIcon
} from '@mui/icons-material';

interface ScopingDecisionDisplayProps {
  // Tester decision fields
  testerDecision?: 'accept' | 'decline' | 'override' | null;
  testerNotes?: string;
  testerDecidedAt?: string;
  
  // Report owner decision fields
  reportOwnerDecision?: 'approved' | 'rejected' | 'pending' | 'needs_revision' | null;
  reportOwnerNotes?: string;
  reportOwnerDecidedAt?: string;
  
  // Special cases
  isPrimaryKey?: boolean;
  
  // Overall status
  status?: 'pending' | 'submitted' | 'approved' | 'rejected' | 'needs_revision';
}

export const ScopingDecisionDisplay = ({
  testerDecision,
  testerNotes,
  testerDecidedAt,
  reportOwnerDecision,
  reportOwnerNotes,
  reportOwnerDecidedAt,
  isPrimaryKey,
  status
}: ScopingDecisionDisplayProps) => {
  
  // Tester Decision Display
  const getTesterDecisionDisplay = () => {
    // Primary keys are automatically included
    if (isPrimaryKey) {
      return (
        <Chip
          size="small"
          label="Included (PK)"
          color="primary"
          icon={<LockIcon sx={{ fontSize: 16 }} />}
          sx={{ fontSize: '0.7rem' }}
        />
      );
    }

    if (!testerDecision) {
      return <Typography variant="caption" color="textSecondary">Pending</Typography>;
    }

    const decisionConfig = {
      'accept': { 
        color: 'success' as const, 
        label: 'Include',
        icon: <CheckCircleIcon sx={{ fontSize: 16 }} />
      },
      'decline': { 
        color: 'error' as const, 
        label: 'Exclude',
        icon: <CancelIcon sx={{ fontSize: 16 }} />
      },
      'override': { 
        color: 'warning' as const, 
        label: 'Override',
        icon: <InfoIcon sx={{ fontSize: 16 }} />
      }
    };

    const config = decisionConfig[testerDecision] || { 
      color: 'default' as const, 
      label: testerDecision,
      icon: <PendingIcon sx={{ fontSize: 16 }} />
    };

    const chipContent = (
      <Chip 
        size="small" 
        color={config.color} 
        label={config.label}
        icon={config.icon}
        sx={{ fontSize: '0.7rem' }} 
      />
    );

    if (testerNotes || testerDecidedAt) {
      return (
        <Tooltip
          title={
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                Tester Decision
              </Typography>
              {testerDecidedAt && (
                <Typography variant="caption" display="block">
                  Decided: {new Date(testerDecidedAt).toLocaleString()}
                </Typography>
              )}
              {testerNotes && (
                <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                  Notes: {testerNotes}
                </Typography>
              )}
            </Box>
          }
          arrow
        >
          <Box sx={{ display: 'inline-flex', alignItems: 'center', cursor: 'pointer' }}>
            {chipContent}
          </Box>
        </Tooltip>
      );
    }

    return chipContent;
  };

  // Report Owner Decision Display
  const getReportOwnerDecisionDisplay = () => {
    if (!reportOwnerDecision || reportOwnerDecision === 'pending') {
      return <Typography variant="caption" color="textSecondary">-</Typography>;
    }

    const decisionConfig = {
      'approved': { 
        color: 'success' as const, 
        label: 'RO Approved',
        icon: <CheckCircleIcon sx={{ fontSize: 16 }} />
      },
      'rejected': { 
        color: 'error' as const, 
        label: 'RO Rejected',
        icon: <CancelIcon sx={{ fontSize: 16 }} />
      },
      'needs_revision': { 
        color: 'warning' as const, 
        label: 'Needs Revision',
        icon: <InfoIcon sx={{ fontSize: 16 }} />
      }
    };

    const config = decisionConfig[reportOwnerDecision] || { 
      color: 'default' as const, 
      label: reportOwnerDecision,
      icon: <PendingIcon sx={{ fontSize: 16 }} />
    };

    const chipContent = (
      <Chip 
        size="small" 
        color={config.color} 
        label={config.label}
        icon={config.icon}
        sx={{ fontSize: '0.7rem' }} 
      />
    );

    if (reportOwnerNotes || reportOwnerDecidedAt) {
      return (
        <Tooltip
          title={
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                Report Owner Decision
              </Typography>
              {reportOwnerDecidedAt && (
                <Typography variant="caption" display="block">
                  Decided: {new Date(reportOwnerDecidedAt).toLocaleString()}
                </Typography>
              )}
              {reportOwnerNotes && (
                <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                  Notes: {reportOwnerNotes}
                </Typography>
              )}
            </Box>
          }
          arrow
        >
          <Box sx={{ display: 'inline-flex', alignItems: 'center', cursor: 'pointer' }}>
            {chipContent}
          </Box>
        </Tooltip>
      );
    }

    return chipContent;
  };

  // Status Display
  const getStatusDisplay = () => {
    if (!status) return null;

    const statusConfig = {
      'pending': { color: 'default' as const, label: 'Pending' },
      'submitted': { color: 'info' as const, label: 'Submitted' },
      'approved': { color: 'success' as const, label: 'Approved' },
      'rejected': { color: 'error' as const, label: 'Rejected' },
      'needs_revision': { color: 'warning' as const, label: 'Needs Revision' }
    };

    const config = statusConfig[status] || { 
      color: 'default' as const, 
      label: status 
    };

    return (
      <Chip 
        size="small" 
        color={config.color} 
        label={config.label}
        variant="outlined"
        sx={{ fontSize: '0.65rem' }} 
      />
    );
  };

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
      {getTesterDecisionDisplay()}
      {getReportOwnerDecisionDisplay()}
      {getStatusDisplay()}
    </Box>
  );
};

// Export individual display functions for flexible usage
export const ScopingStatusDisplay = (props: Pick<ScopingDecisionDisplayProps, 'status'>) => {
  const { status } = props;
  
  if (!status) return null;

  const statusConfig = {
    'pending': { color: 'default' as const, label: 'Pending' },
    'submitted': { color: 'info' as const, label: 'Submitted' },
    'approved': { color: 'success' as const, label: 'Approved' },
    'rejected': { color: 'error' as const, label: 'Rejected' },
    'needs_revision': { color: 'warning' as const, label: 'Needs Revision' }
  };

  const config = statusConfig[status] || { 
    color: 'default' as const, 
    label: status 
  };

  return (
    <Chip 
      size="small" 
      color={config.color} 
      label={config.label}
      variant="outlined"
      sx={{ fontSize: '0.65rem' }} 
    />
  );
};

export const ScopingTesterDecisionDisplay = (props: Partial<ScopingDecisionDisplayProps>) => {
  const { testerDecision, testerNotes, testerDecidedAt, isPrimaryKey } = props;
  
  // Primary keys are automatically included
  if (isPrimaryKey) {
    return (
      <Chip
        size="small"
        label="Included (PK)"
        color="primary"
        icon={<LockIcon sx={{ fontSize: 16 }} />}
        sx={{ fontSize: '0.7rem' }}
      />
    );
  }

  if (!testerDecision) {
    return <Typography variant="caption" color="textSecondary">Pending</Typography>;
  }

  const decisionConfig = {
    'accept': { 
      color: 'success' as const, 
      label: 'Include',
      icon: <CheckCircleIcon sx={{ fontSize: 16 }} />
    },
    'decline': { 
      color: 'error' as const, 
      label: 'Exclude',
      icon: <CancelIcon sx={{ fontSize: 16 }} />
    },
    'override': { 
      color: 'warning' as const, 
      label: 'Override',
      icon: <InfoIcon sx={{ fontSize: 16 }} />
    }
  };

  const config = decisionConfig[testerDecision] || { 
    color: 'default' as const, 
    label: testerDecision,
    icon: <PendingIcon sx={{ fontSize: 16 }} />
  };

  const chipContent = (
    <Chip 
      size="small" 
      color={config.color} 
      label={config.label}
      icon={config.icon}
      sx={{ fontSize: '0.7rem' }} 
    />
  );

  if (testerNotes || testerDecidedAt) {
    return (
      <Tooltip
        title={
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
              Tester Decision
            </Typography>
            {testerDecidedAt && (
              <Typography variant="caption" display="block">
                Decided: {new Date(testerDecidedAt).toLocaleString()}
              </Typography>
            )}
            {testerNotes && (
              <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                Notes: {testerNotes}
              </Typography>
            )}
          </Box>
        }
        arrow
      >
        <Box sx={{ display: 'inline-flex', alignItems: 'center', cursor: 'pointer' }}>
          {chipContent}
        </Box>
      </Tooltip>
    );
  }

  return chipContent;
};

export const ScopingReportOwnerDecisionDisplay = (props: Partial<ScopingDecisionDisplayProps>) => {
  const { reportOwnerDecision, reportOwnerNotes, reportOwnerDecidedAt } = props;
  
  if (!reportOwnerDecision || reportOwnerDecision === 'pending') {
    return <Typography variant="caption" color="textSecondary">-</Typography>;
  }

  const decisionConfig = {
    'approved': { 
      color: 'success' as const, 
      label: 'RO Approved',
      icon: <CheckCircleIcon sx={{ fontSize: 16 }} />
    },
    'rejected': { 
      color: 'error' as const, 
      label: 'RO Rejected',
      icon: <CancelIcon sx={{ fontSize: 16 }} />
    },
    'needs_revision': { 
      color: 'warning' as const, 
      label: 'Needs Revision',
      icon: <InfoIcon sx={{ fontSize: 16 }} />
    }
  };

  const config = decisionConfig[reportOwnerDecision] || { 
    color: 'default' as const, 
    label: reportOwnerDecision,
    icon: <PendingIcon sx={{ fontSize: 16 }} />
  };

  const chipContent = (
    <Chip 
      size="small" 
      color={config.color} 
      label={config.label}
      icon={config.icon}
      sx={{ fontSize: '0.7rem' }} 
    />
  );

  if (reportOwnerNotes || reportOwnerDecidedAt) {
    return (
      <Tooltip
        title={
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
              Report Owner Decision
            </Typography>
            {reportOwnerDecidedAt && (
              <Typography variant="caption" display="block">
                Decided: {new Date(reportOwnerDecidedAt).toLocaleString()}
              </Typography>
            )}
            {reportOwnerNotes && (
              <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                Notes: {reportOwnerNotes}
              </Typography>
            )}
          </Box>
        }
        arrow
      >
        <Box sx={{ display: 'inline-flex', alignItems: 'center', cursor: 'pointer' }}>
          {chipContent}
        </Box>
      </Tooltip>
    );
  }

  return chipContent;
};