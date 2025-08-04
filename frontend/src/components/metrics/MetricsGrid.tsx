import React from 'react';
import { Box, Typography, Alert } from '@mui/material';
import Grid from '@mui/material/Grid';
import { PhaseMetricsCard } from './PhaseMetricsCard';

export interface MetricCardConfig {
  id: string;
  title: string;
  subtitle?: string;
  metrics: Array<{
    value: number | string;
    label: string;
    unit?: string;
    trend?: number;
    target?: number;
    status?: 'success' | 'warning' | 'error' | 'info';
    description?: string;
  }>;
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: number; // Grid size (1-12)
}

interface MetricsGridProps {
  title?: string;
  subtitle?: string;
  cards: MetricCardConfig[];
  loading?: boolean;
  error?: string;
  columnsXs?: number;
  columnsSm?: number;
  columnsMd?: number;
  columnsLg?: number;
}

export const MetricsGrid: React.FC<MetricsGridProps> = ({
  title,
  subtitle,
  cards,
  loading = false,
  error,
  columnsXs = 12,
  columnsSm = 6,
  columnsMd = 4,
  columnsLg = 3
}) => {
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ mb: 4 }}>
      {(title || subtitle) && (
        <Box sx={{ mb: 3 }}>
          {title && (
            <Typography variant="h5" gutterBottom>
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

      <Grid container spacing={3}>
        {cards.map((card) => (
          <Grid
            key={card.id}
            size={{ 
              xs: card.size || columnsXs, 
              sm: card.size || columnsSm,
              md: card.size || columnsMd,
              lg: card.size || columnsLg
            }}
          >
            <PhaseMetricsCard
              title={card.title}
              subtitle={card.subtitle}
              metrics={card.metrics}
              loading={loading}
              icon={card.icon}
              color={card.color}
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default MetricsGrid;