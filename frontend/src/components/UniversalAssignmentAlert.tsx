import React from 'react';
import {
  Alert,
  AlertTitle,
  Box,
  Typography,
  Button,
  Chip,
  Stack,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  Assignment,
  Schedule,
  Warning,
  ExpandMore,
  ExpandLess,
  Check,
  PlayArrow,
  CheckCircle,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { UniversalAssignment } from '../hooks/useUniversalAssignments';

interface UniversalAssignmentAlertProps {
  assignment: UniversalAssignment;
  onAcknowledge?: (assignmentId: string) => void;
  onStart?: (assignmentId: string) => void;
  onComplete?: (assignmentId: string) => void;
  showActions?: boolean;
}

export const UniversalAssignmentAlert: React.FC<UniversalAssignmentAlertProps> = ({
  assignment,
  onAcknowledge,
  onStart,
  onComplete,
  showActions = true,
}) => {
  const [expanded, setExpanded] = React.useState(true);

  const getOverdueStatus = () => {
    if (!assignment.due_date || assignment.status === 'completed' || assignment.status === 'approved') {
      return false;
    }
    return new Date(assignment.due_date) < new Date();
  };

  const getPriorityColor = () => {
    const priorityMap: Record<string, 'error' | 'warning' | 'info' | 'success'> = {
      Critical: 'error',
      Urgent: 'error',
      High: 'warning',
      Medium: 'info',
      Low: 'success',
    };
    return priorityMap[assignment.priority] || 'info';
  };

  const isOverdue = getOverdueStatus();

  return (
    <Alert 
      severity={isOverdue ? 'warning' : 'info'}
      icon={<Assignment />}
      sx={{ mb: 3 }}
      action={
        <IconButton
          size="small"
          onClick={() => setExpanded(!expanded)}
          sx={{ alignSelf: 'flex-start', mt: -0.5 }}
        >
          {expanded ? <ExpandLess /> : <ExpandMore />}
        </IconButton>
      }
    >
      <AlertTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {assignment.title}
        <Chip 
          label={assignment.priority} 
          size="small" 
          color={getPriorityColor()}
          sx={{ ml: 1 }}
        />
        {isOverdue && (
          <Chip 
            label="Overdue" 
            size="small" 
            color="error"
            icon={<Warning />}
            sx={{ ml: 1 }}
          />
        )}
      </AlertTitle>
      
      <Collapse in={expanded}>
        <Box>
          {assignment.description && (
            <Typography variant="body2" sx={{ mb: 1 }}>
              {assignment.description}
            </Typography>
          )}
          
          <Stack direction="row" spacing={2} alignItems="center" sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              From: {assignment.from_user_name || assignment.from_role}
            </Typography>
            
            {assignment.due_date && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Schedule fontSize="small" color="action" />
                <Typography 
                  variant="caption" 
                  color={isOverdue ? 'error' : 'text.secondary'}
                >
                  Due: {format(new Date(assignment.due_date), 'MMM dd, yyyy')}
                </Typography>
              </Box>
            )}
            
            <Chip 
              label={assignment.status.replace(/_/g, ' ')} 
              size="small"
              variant="outlined"
            />
          </Stack>
          
          {showActions && (
            <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
              {assignment.status === 'assigned' && onAcknowledge && (
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<Check />}
                  onClick={() => onAcknowledge(assignment.assignment_id)}
                >
                  Acknowledge
                </Button>
              )}
              
              {(assignment.status === 'assigned' || assignment.status === 'acknowledged') && onStart && (
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={() => onStart(assignment.assignment_id)}
                >
                  Start Task
                </Button>
              )}
              
              {assignment.status === 'in_progress' && onComplete && (
                <Button
                  size="small"
                  variant="contained"
                  color="success"
                  startIcon={<CheckCircle />}
                  onClick={() => onComplete(assignment.assignment_id)}
                >
                  Mark Complete
                </Button>
              )}
            </Stack>
          )}
        </Box>
      </Collapse>
    </Alert>
  );
};