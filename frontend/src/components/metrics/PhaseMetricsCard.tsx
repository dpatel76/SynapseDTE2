import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Tooltip,
  IconButton,
  Skeleton
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Info,
  CheckCircle,
  Warning,
  Error as ErrorIcon
} from '@mui/icons-material';

interface MetricValue {
  value: number | string;
  label: string;
  unit?: string;
  trend?: number;
  target?: number;
  status?: 'success' | 'warning' | 'error' | 'info';
  description?: string;
}

interface PhaseMetricsCardProps {
  title: string;
  subtitle?: string;
  metrics: MetricValue[];
  loading?: boolean;
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  elevation?: number;
}

const getStatusIcon = (status?: string) => {
  switch (status) {
    case 'success': return <CheckCircle color="success" fontSize="small" />;
    case 'warning': return <Warning color="warning" fontSize="small" />;
    case 'error': return <ErrorIcon color="error" fontSize="small" />;
    default: return null;
  }
};

const getTrendIcon = (trend?: number) => {
  if (!trend) return <TrendingFlat color="action" fontSize="small" />;
  if (trend > 0) return <TrendingUp color="success" fontSize="small" />;
  return <TrendingDown color="error" fontSize="small" />;
};

const formatValue = (value: number | string, unit?: string): string => {
  if (typeof value === 'number') {
    if (unit === '%') return `${Math.round(value)}%`;
    if (unit === 'days') return `${value}d`;
    if (unit === 'hours') return `${value}h`;
    return value.toLocaleString();
  }
  return String(value);
};

export const PhaseMetricsCard: React.FC<PhaseMetricsCardProps> = ({
  title,
  subtitle,
  metrics,
  loading = false,
  icon,
  color = 'primary',
  elevation = 1
}) => {
  if (loading) {
    return (
      <Card elevation={elevation}>
        <CardContent>
          <Skeleton variant="text" width="60%" height={32} />
          <Skeleton variant="text" width="40%" />
          <Box sx={{ mt: 2 }}>
            <Skeleton variant="rectangular" height={60} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card elevation={elevation} sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box>
            <Typography variant="h6" gutterBottom>
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          {icon && (
            <Box sx={{ color: `${color}.main` }}>
              {icon}
            </Box>
          )}
        </Box>

        <Box display="flex" flexDirection="column" gap={2}>
          {metrics.map((metric, index) => (
            <Box key={index}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="body2" color="text.secondary">
                    {metric.label}
                  </Typography>
                  {metric.description && (
                    <Tooltip title={metric.description}>
                      <IconButton size="small" sx={{ p: 0 }}>
                        <Info fontSize="small" color="action" />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
                <Box display="flex" alignItems="center" gap={1}>
                  {metric.trend !== undefined && getTrendIcon(metric.trend)}
                  {metric.status && getStatusIcon(metric.status)}
                </Box>
              </Box>

              <Box display="flex" alignItems="baseline" gap={1}>
                <Typography variant="h5" color={`${color}.main`}>
                  {formatValue(metric.value, metric.unit)}
                </Typography>
                {metric.trend !== undefined && (
                  <Typography variant="caption" color={metric.trend > 0 ? 'success.main' : 'error.main'}>
                    {metric.trend > 0 ? '+' : ''}{metric.trend}%
                  </Typography>
                )}
              </Box>

              {metric.target !== undefined && (
                <Box sx={{ mt: 1 }}>
                  <Box display="flex" justifyContent="space-between" mb={0.5}>
                    <Typography variant="caption" color="text.secondary">
                      Progress to target
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {Math.round((Number(metric.value) / metric.target) * 100)}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min((Number(metric.value) / metric.target) * 100, 100)}
                    sx={{ height: 6, borderRadius: 3 }}
                    color={color}
                  />
                </Box>
              )}
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default PhaseMetricsCard;