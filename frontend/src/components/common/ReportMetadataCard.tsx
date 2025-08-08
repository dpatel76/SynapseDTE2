import React from 'react';
import { Box, Typography, Skeleton, Chip, Paper } from '@mui/material';
import { Business, Person, Assignment, Description } from '@mui/icons-material';

interface ReportMetadata {
  lob_name?: string;
  tester_name?: string;
  test_executive_name?: string;
  report_owner_name?: string;
  data_owner_name?: string;
  report_name?: string;
  report_number?: string;
  cycle_name?: string;
  regulation?: string;
}

interface ReportMetadataCardProps {
  metadata: ReportMetadata | null;
  loading?: boolean;
  variant?: 'compact' | 'full';
  showFields?: ('lob' | 'tester' | 'executive' | 'owner' | 'dataOwner' | 'report' | 'cycle' | 'regulation')[];
}

export const ReportMetadataCard: React.FC<ReportMetadataCardProps> = ({
  metadata,
  loading = false,
  variant = 'compact',
  showFields = ['lob', 'tester', 'owner']
}) => {
  const renderField = (
    icon: React.ReactNode,
    label: string,
    value: string | undefined,
    defaultValue: string
  ) => {
    if (variant === 'compact') {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {icon}
          <Typography variant="body2" color="text.secondary">
            {label}:
          </Typography>
          <Typography variant="body2" fontWeight="medium">
            {value || defaultValue}
          </Typography>
        </Box>
      );
    }

    return (
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          {icon}
          <Typography variant="caption" color="text.secondary">
            {label}
          </Typography>
        </Box>
        <Typography variant="body1">
          {value || defaultValue}
        </Typography>
      </Box>
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        {showFields.map((field) => (
          <Skeleton key={field} variant="text" width={120} height={32} />
        ))}
      </Box>
    );
  }

  const fieldComponents = {
    lob: () => renderField(
      <Business color="action" fontSize="small" />,
      'LOB',
      metadata?.lob_name,
      'Unknown'
    ),
    tester: () => renderField(
      <Person color="action" fontSize="small" />,
      'Tester',
      metadata?.tester_name,
      'Not assigned'
    ),
    executive: () => renderField(
      <Person color="action" fontSize="small" />,
      'Test Executive',
      metadata?.test_executive_name,
      'Not assigned'
    ),
    owner: () => renderField(
      <Person color="action" fontSize="small" />,
      'Report Owner',
      metadata?.report_owner_name,
      'Not specified'
    ),
    dataOwner: () => renderField(
      <Person color="action" fontSize="small" />,
      'Data Owner',
      metadata?.data_owner_name,
      'Not assigned'
    ),
    report: () => renderField(
      <Description color="action" fontSize="small" />,
      'Report',
      metadata?.report_name,
      'Unknown'
    ),
    cycle: () => renderField(
      <Assignment color="action" fontSize="small" />,
      'Cycle',
      metadata?.cycle_name,
      'Unknown'
    ),
    regulation: () => renderField(
      <Assignment color="action" fontSize="small" />,
      'Regulation',
      metadata?.regulation,
      'N/A'
    ),
  };

  if (variant === 'full') {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Report Metadata
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
          {showFields.map((field) => (
            <Box key={field}>
              {fieldComponents[field] && fieldComponents[field]()}
            </Box>
          ))}
        </Box>
      </Paper>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
      {showFields.map((field) => (
        <React.Fragment key={field}>
          {fieldComponents[field] && fieldComponents[field]()}
        </React.Fragment>
      ))}
    </Box>
  );
};

export default ReportMetadataCard;