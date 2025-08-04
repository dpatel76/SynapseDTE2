import React from 'react';
import { Box, Typography } from '@mui/material';
import Grid from '@mui/material/Grid';
import { MetricBox } from './MetricBox';

export interface MetricConfig {
  title: string;
  value: number | string;
  unit?: string;
  trend?: number;
  target?: number;
  status?: 'success' | 'warning' | 'error' | 'info';
  description?: string;
  icon?: React.ReactNode;
  color?: string;
  onClick?: () => void;
}

interface MetricsRowProps {
  title?: string;
  subtitle?: string;
  metrics: MetricConfig[];
  loading?: boolean;
  size?: 'small' | 'medium' | 'large';
}

export const MetricsRow: React.FC<MetricsRowProps> = ({
  title,
  subtitle,
  metrics,
  loading = false,
  size = 'medium'
}) => {
  const getGridSize = () => {
    const count = metrics.length;
    if (count <= 3) return 12 / count;
    if (count === 4) return 3;
    if (count <= 6) return 2;
    return 2; // For more than 6, use 2 columns per metric
  };

  return (
    <Box sx={{ mb: 4 }}>
      {(title || subtitle) && (
        <Box sx={{ mb: 2 }}>
          {title && (
            <Typography variant="h6" gutterBottom>
              {title}
            </Typography>
          )}
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
      )}

      <Grid container spacing={2}>
        {metrics.map((metric, index) => (
          <Grid key={index} size={{ xs: 12, sm: 6, md: getGridSize() }}>
            <MetricBox
              title={metric.title}
              value={metric.value}
              unit={metric.unit}
              trend={metric.trend}
              target={metric.target}
              status={metric.status}
              description={metric.description}
              icon={metric.icon}
              color={metric.color}
              loading={loading}
              size={size}
              onClick={metric.onClick}
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default MetricsRow;