import React from 'react';
import {
  Box,
  Paper,
  Typography,
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
  Info
} from '@mui/icons-material';

interface MetricBoxProps {
  title: string;
  value: number | string;
  unit?: string;
  trend?: number;
  target?: number;
  status?: 'success' | 'warning' | 'error' | 'info';
  description?: string;
  icon?: React.ReactNode;
  color?: string;
  loading?: boolean;
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
}

const getTrendIcon = (trend?: number) => {
  if (!trend) return <TrendingFlat fontSize="small" />;
  if (trend > 0) return <TrendingUp color="success" fontSize="small" />;
  return <TrendingDown color="error" fontSize="small" />;
};

const getStatusColor = (status?: string): string => {
  switch (status) {
    case 'success': return '#4caf50';
    case 'warning': return '#ff9800';
    case 'error': return '#f44336';
    case 'info': return '#2196f3';
    default: return '#1976d2';
  }
};

export const MetricBox: React.FC<MetricBoxProps> = ({
  title,
  value,
  unit = '',
  trend,
  target,
  status,
  description,
  icon,
  color,
  loading = false,
  size = 'medium',
  onClick
}) => {
  const formatValue = (val: number | string): string => {
    if (typeof val === 'number') {
      if (unit === '%') return `${Math.round(val)}%`;
      if (unit === 'days') return `${val}d`;
      if (unit === 'hours') return `${val}h`;
      return val.toLocaleString();
    }
    return String(val);
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return { p: 2, minHeight: 120 };
      case 'large':
        return { p: 4, minHeight: 200 };
      default:
        return { p: 3, minHeight: 160 };
    }
  };

  const getValueSize = () => {
    switch (size) {
      case 'small': return 'h5';
      case 'large': return 'h3';
      default: return 'h4';
    }
  };

  if (loading) {
    return (
      <Paper 
        elevation={2} 
        sx={{ 
          ...getSizeStyles(),
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}
      >
        <Skeleton variant="text" width="60%" height={24} />
        <Skeleton variant="text" width="40%" height={40} />
        <Skeleton variant="rectangular" height={8} sx={{ mt: 2 }} />
      </Paper>
    );
  }

  const displayColor = color || getStatusColor(status);

  return (
    <Paper
      elevation={2}
      sx={{
        ...getSizeStyles(),
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s ease',
        '&:hover': onClick ? {
          elevation: 4,
          transform: 'translateY(-2px)',
          boxShadow: 3
        } : {}
      }}
      onClick={onClick}
    >
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
        <Box display="flex" alignItems="center" gap={1}>
          {icon && (
            <Box sx={{ color: displayColor }}>
              {icon}
            </Box>
          )}
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            {description && (
              <Tooltip title={description}>
                <IconButton size="small" sx={{ p: 0, ml: 0.5 }}>
                  <Info fontSize="small" color="action" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
        {trend !== undefined && (
          <Box display="flex" alignItems="center" gap={0.5}>
            {getTrendIcon(trend)}
            <Typography 
              variant="caption" 
              color={trend > 0 ? 'success.main' : 'error.main'}
            >
              {trend > 0 ? '+' : ''}{trend}%
            </Typography>
          </Box>
        )}
      </Box>

      {/* Value */}
      <Box sx={{ my: 2 }}>
        <Typography 
          variant={getValueSize()} 
          sx={{ 
            color: displayColor,
            fontWeight: 'bold'
          }}
        >
          {formatValue(value)}
        </Typography>
        {status && (
          <Chip
            label={status}
            size="small"
            sx={{
              backgroundColor: displayColor,
              color: 'white',
              mt: 1
            }}
          />
        )}
      </Box>

      {/* Progress to Target */}
      {target !== undefined && typeof value === 'number' && (
        <Box>
          <Box display="flex" justifyContent="space-between" mb={0.5}>
            <Typography variant="caption" color="text.secondary">
              Target: {formatValue(target)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {Math.round((value / target) * 100)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={Math.min((value / target) * 100, 100)}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: 'rgba(0,0,0,0.1)',
              '& .MuiLinearProgress-bar': {
                backgroundColor: displayColor
              }
            }}
          />
        </Box>
      )}
    </Paper>
  );
};

export default MetricBox;