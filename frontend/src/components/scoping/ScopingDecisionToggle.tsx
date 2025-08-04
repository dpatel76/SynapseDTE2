import React from 'react';
import {
  ToggleButton,
  ToggleButtonGroup,
  Chip,
  Typography
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Lock as LockIcon
} from '@mui/icons-material';

interface ScopingDecisionToggleProps {
  attributeId: string; // Updated to string (UUID) to match unified planning
  isPrimaryKey: boolean;
  isPlanningApproved: boolean;  // Not used for toggle display - kept for backward compatibility
  currentDecision: 'include' | 'exclude' | 'pending';
  onChange: (attributeId: string, decision: 'include' | 'exclude') => void; // Updated to string (UUID)
  disabled?: boolean;
}

export const ScopingDecisionToggle: React.FC<ScopingDecisionToggleProps> = ({
  attributeId,
  isPrimaryKey,
  isPlanningApproved,
  currentDecision,
  onChange,
  disabled = false
}) => {
  // Primary keys are always included
  if (isPrimaryKey) {
    return (
      <Chip
        label="Included (PK)"
        color="primary"
        size="small"
        icon={<LockIcon />}
        sx={{ minWidth: 120 }}
      />
    );
  }

  // Remove the planning approval check - tester can make decisions on all non-PK attributes
  // The toggle will be disabled if the page is in read-only mode

  // Show pending state with interactive buttons
  if (currentDecision === 'pending') {
    return (
      <ToggleButtonGroup
        value={null}
        exclusive
        onChange={(e, value) => {
          if (value !== null) {
            onChange(attributeId, value);
          }
        }}
        size="small"
        disabled={disabled}
        sx={{ 
          '& .MuiToggleButton-root': { 
            border: '1px solid #orange',
            '&:hover': { 
              backgroundColor: 'rgba(255, 152, 0, 0.1)' 
            }
          }
        }}
      >
        <ToggleButton value="include" color="success">
          <CheckCircleIcon sx={{ mr: 0.5, fontSize: 18 }} />
          Include
        </ToggleButton>
        <ToggleButton value="exclude" color="error">
          <CancelIcon sx={{ mr: 0.5, fontSize: 18 }} />
          Exclude
        </ToggleButton>
      </ToggleButtonGroup>
    );
  }

  return (
    <ToggleButtonGroup
      value={currentDecision}
      exclusive
      onChange={(e, value) => {
        if (value !== null) {
          onChange(attributeId, value);
        }
      }}
      size="small"
      disabled={disabled}
    >
      <ToggleButton value="include" color="success">
        <CheckCircleIcon sx={{ mr: 0.5, fontSize: 18 }} />
        Include
      </ToggleButton>
      <ToggleButton value="exclude" color="error">
        <CancelIcon sx={{ mr: 0.5, fontSize: 18 }} />
        Exclude
      </ToggleButton>
    </ToggleButtonGroup>
  );
};