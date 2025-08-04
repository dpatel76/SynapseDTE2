import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepConnector,
  StepContent,
  Chip,
  Tooltip,
  IconButton,
  LinearProgress,
  Paper,
  Divider,
  Button,
  styled
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  CheckCircle,
  RadioButtonUnchecked,
  Schedule,
  Warning,
  Error,
  Info,
  ExpandMore,
  ExpandLess,
  Timeline,
  AccountTree
} from '@mui/icons-material';
import { format } from 'date-fns';
import { colors } from '../../styles/design-system';

interface WorkflowPhase {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'skipped';
  sequence: number;
  parallelWith?: string[];
  dependsOn?: string[];
  startedAt?: Date;
  completedAt?: Date;
  assignedTo?: string;
  slaHours?: number;
  slaStatus?: 'on_track' | 'warning' | 'violated';
  completionPercentage?: number;
}

interface WorkflowVisualizationProps {
  phases: WorkflowPhase[];
  currentPhase?: string;
  onPhaseClick?: (phaseId: string) => void;
  compact?: boolean;
  showDetails?: boolean;
}

// Custom styled connector for parallel phases
const ParallelConnector = styled(StepConnector)(({ theme }) => ({
  '&.MuiStepConnector-root': {
    marginLeft: 0,
  },
  '& .MuiStepConnector-line': {
    borderColor: colors.grey[300],
    borderLeftStyle: 'dashed',
    borderLeftWidth: 2,
  },
}));

// Custom styled connector for sequential phases
const SequentialConnector = styled(StepConnector)(({ theme }) => ({
  '& .MuiStepConnector-line': {
    borderColor: colors.primary.main,
    borderLeftWidth: 3,
  },
}));

const WorkflowVisualization: React.FC<WorkflowVisualizationProps> = ({
  phases,
  currentPhase,
  onPhaseClick,
  compact = false,
  showDetails = true
}) => {
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());

  const togglePhaseExpansion = (phaseId: string) => {
    const newExpanded = new Set(expandedPhases);
    if (newExpanded.has(phaseId)) {
      newExpanded.delete(phaseId);
    } else {
      newExpanded.add(phaseId);
    }
    setExpandedPhases(newExpanded);
  };

  const getPhaseIcon = (phase: WorkflowPhase) => {
    switch (phase.status) {
      case 'completed':
        return <CheckCircle sx={{ color: colors.success.main }} />;
      case 'in_progress':
        return <Schedule sx={{ color: colors.primary.main }} />;
      case 'skipped':
        return <Info sx={{ color: colors.grey[500] }} />;
      default:
        return <RadioButtonUnchecked sx={{ color: colors.grey[400] }} />;
    }
  };

  const getPhaseColor = (phase: WorkflowPhase) => {
    if (phase.id === currentPhase) return colors.primary.main;
    switch (phase.status) {
      case 'completed':
        return colors.success.main;
      case 'in_progress':
        return colors.primary.main;
      case 'skipped':
        return colors.grey[500];
      default:
        return colors.grey[400];
    }
  };

  const getSLAIcon = (slaStatus?: string) => {
    switch (slaStatus) {
      case 'warning':
        return <Warning sx={{ color: colors.warning.main, fontSize: 16 }} />;
      case 'violated':
        return <Error sx={{ color: colors.error.main, fontSize: 16 }} />;
      default:
        return null;
    }
  };

  const groupPhasesByLevel = () => {
    const levels: WorkflowPhase[][] = [];
    const processed = new Set<string>();

    phases.forEach(phase => {
      if (processed.has(phase.id)) return;

      // Find all parallel phases
      const parallelGroup = [phase];
      if (phase.parallelWith) {
        phase.parallelWith.forEach(parallelId => {
          const parallelPhase = phases.find(p => p.id === parallelId);
          if (parallelPhase && !processed.has(parallelId)) {
            parallelGroup.push(parallelPhase);
          }
        });
      }

      // Add all phases in the group to processed
      parallelGroup.forEach(p => processed.add(p.id));
      levels.push(parallelGroup);
    });

    return levels;
  };

  const renderCompactView = () => {
    const levels = groupPhasesByLevel();

    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        {levels.map((level, levelIndex) => (
          <React.Fragment key={levelIndex}>
            {levelIndex > 0 && (
              <Box sx={{ color: colors.grey[400] }}>→</Box>
            )}
            {level.length > 1 ? (
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                gap: 1,
                padding: 1,
                border: `1px dashed ${colors.grey[300]}`,
                borderRadius: 1
              }}>
                {level.map(phase => (
                  <Chip
                    key={phase.id}
                    label={phase.name}
                    icon={getPhaseIcon(phase)}
                    onClick={() => onPhaseClick?.(phase.id)}
                    sx={{
                      backgroundColor: phase.id === currentPhase ? colors.primary.light + '20' : 'default',
                      borderColor: getPhaseColor(phase),
                      borderWidth: 1,
                      borderStyle: 'solid'
                    }}
                    variant="outlined"
                  />
                ))}
              </Box>
            ) : (
              <Chip
                label={level[0].name}
                icon={getPhaseIcon(level[0])}
                onClick={() => onPhaseClick?.(level[0].id)}
                sx={{
                  backgroundColor: level[0].id === currentPhase ? colors.primary.light + '20' : 'default',
                  borderColor: getPhaseColor(level[0]),
                  borderWidth: 1,
                  borderStyle: 'solid'
                }}
                variant="outlined"
              />
            )}
          </React.Fragment>
        ))}
      </Box>
    );
  };

  const renderDetailedView = () => {
    const levels = groupPhasesByLevel();

    return (
      <Stepper orientation="vertical" activeStep={-1}>
        {levels.map((level, levelIndex) => (
          <Step key={levelIndex} expanded>
            <StepLabel
              StepIconComponent={() => (
                level.length > 1 ? (
                  <AccountTree sx={{ color: colors.primary.main }} />
                ) : (
                  getPhaseIcon(level[0])
                )
              )}
            >
              {level.length > 1 ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="subtitle2">Parallel Phases</Typography>
                  <Chip 
                    label={`${level.filter(p => p.status === 'completed').length}/${level.length}`}
                    size="small"
                    color={level.every(p => p.status === 'completed') ? 'success' : 'default'}
                  />
                </Box>
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography 
                    variant="subtitle1"
                    sx={{ 
                      color: getPhaseColor(level[0]),
                      fontWeight: level[0].id === currentPhase ? 600 : 400
                    }}
                  >
                    {level[0].name}
                  </Typography>
                  {getSLAIcon(level[0].slaStatus)}
                  {level[0].completionPercentage !== undefined && level[0].status === 'in_progress' && (
                    <Chip 
                      label={`${level[0].completionPercentage}%`}
                      size="small"
                      color="primary"
                    />
                  )}
                </Box>
              )}
            </StepLabel>
            <StepContent>
              <Grid container spacing={2}>
                {level.map(phase => (
                  <Grid size={{ xs: 12, md: level.length > 1 ? 6 : 12 }} key={phase.id}>
                    <Card 
                      sx={{ 
                        cursor: onPhaseClick ? 'pointer' : 'default',
                        border: phase.id === currentPhase ? `2px solid ${colors.primary.main}` : 'none',
                        '&:hover': onPhaseClick ? {
                          boxShadow: 3,
                          transform: 'translateY(-2px)',
                          transition: 'all 0.2s'
                        } : {}
                      }}
                      onClick={() => onPhaseClick?.(phase.id)}
                    >
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Typography variant="h6">{phase.name}</Typography>
                          <IconButton 
                            size="small" 
                            onClick={(e) => {
                              e.stopPropagation();
                              togglePhaseExpansion(phase.id);
                            }}
                          >
                            {expandedPhases.has(phase.id) ? <ExpandLess /> : <ExpandMore />}
                          </IconButton>
                        </Box>

                        {(showDetails || expandedPhases.has(phase.id)) && (
                          <>
                            <Divider sx={{ my: 1 }} />
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                              {phase.assignedTo && (
                                <Box display="flex" justifyContent="space-between">
                                  <Typography variant="body2" color="textSecondary">Assigned to:</Typography>
                                  <Typography variant="body2">{phase.assignedTo}</Typography>
                                </Box>
                              )}
                              {phase.startedAt && (
                                <Box display="flex" justifyContent="space-between">
                                  <Typography variant="body2" color="textSecondary">Started:</Typography>
                                  <Typography variant="body2">{format(phase.startedAt, 'MMM dd, yyyy')}</Typography>
                                </Box>
                              )}
                              {phase.completedAt && (
                                <Box display="flex" justifyContent="space-between">
                                  <Typography variant="body2" color="textSecondary">Completed:</Typography>
                                  <Typography variant="body2">{format(phase.completedAt, 'MMM dd, yyyy')}</Typography>
                                </Box>
                              )}
                              {phase.slaHours && (
                                <Box display="flex" justifyContent="space-between" alignItems="center">
                                  <Typography variant="body2" color="textSecondary">SLA:</Typography>
                                  <Box display="flex" alignItems="center" gap={0.5}>
                                    <Typography variant="body2">{phase.slaHours}h</Typography>
                                    {getSLAIcon(phase.slaStatus)}
                                  </Box>
                                </Box>
                              )}
                              {phase.completionPercentage !== undefined && phase.status === 'in_progress' && (
                                <Box>
                                  <Box display="flex" justifyContent="space-between" mb={0.5}>
                                    <Typography variant="body2" color="textSecondary">Progress:</Typography>
                                    <Typography variant="body2">{phase.completionPercentage}%</Typography>
                                  </Box>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={phase.completionPercentage}
                                    sx={{ height: 6, borderRadius: 3 }}
                                  />
                                </Box>
                              )}
                            </Box>
                          </>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </StepContent>
          </Step>
        ))}
      </Stepper>
    );
  };

  return (
    <Box>
      {compact ? renderCompactView() : renderDetailedView()}
    </Box>
  );
};

export default WorkflowVisualization;