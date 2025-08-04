import React from 'react';
import { Chip, ChipProps } from '@mui/material';
import {
  CheckCircle,
  RadioButtonUnchecked,
  PauseCircle,
  EditNote
} from '@mui/icons-material';

export type ActivityStateType = 'Not Started' | 'In Progress' | 'Completed' | 'Revision Requested';

interface ActivityStateBadgeProps {
  state: ActivityStateType;
  size?: 'small' | 'medium';
  showIcon?: boolean;
  className?: string;
}

const stateConfig: Record<ActivityStateType, {
  color: ChipProps['color'];
  icon: React.ReactElement;
  label: string;
}> = {
  'Not Started': {
    color: 'default',
    icon: <RadioButtonUnchecked fontSize="small" />,
    label: 'Not Started'
  },
  'In Progress': {
    color: 'primary',
    icon: <PauseCircle fontSize="small" />,
    label: 'In Progress'
  },
  'Completed': {
    color: 'success',
    icon: <CheckCircle fontSize="small" />,
    label: 'Completed'
  },
  'Revision Requested': {
    color: 'warning',
    icon: <EditNote fontSize="small" />,
    label: 'Revision Requested'
  }
};

export const ActivityStateBadge: React.FC<ActivityStateBadgeProps> = ({
  state,
  size = 'small',
  showIcon = true,
  className
}) => {
  const config = stateConfig[state];

  if (!config) {
    console.warn(`Unknown activity state: ${state}`);
    return null;
  }

  return (
    <Chip
      label={config.label}
      color={config.color}
      size={size}
      icon={showIcon ? config.icon : undefined}
      className={className}
      sx={{
        fontWeight: 500,
        '& .MuiChip-icon': {
          marginLeft: '4px',
          marginRight: '-2px'
        }
      }}
    />
  );
};

export default ActivityStateBadge;