import React from 'react';
import { Box, Switch, FormControlLabel, Chip } from '@mui/material';
import { toggleMockData, isMockDataEnabled } from '../../api/mockInterceptor';

const MockDataToggle: React.FC = () => {
  const [enabled, setEnabled] = React.useState(isMockDataEnabled());

  const handleToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.checked;
    setEnabled(newValue);
    toggleMockData(newValue);
    // Reload the page to apply changes
    window.location.reload();
  };

  // Only show in development mode
  if (process.env.NODE_ENV === 'production') {
    return null;
  }

  return (
    <Box 
      sx={{ 
        position: 'fixed', 
        bottom: 16, 
        right: 16, 
        backgroundColor: 'background.paper',
        padding: 2,
        borderRadius: 2,
        boxShadow: 3,
        zIndex: 9999
      }}
    >
      <FormControlLabel
        control={
          <Switch 
            checked={enabled} 
            onChange={handleToggle}
            color="primary"
          />
        }
        label={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <span>Mock Data</span>
            {enabled && <Chip label="ON" color="success" size="small" />}
          </Box>
        }
      />
    </Box>
  );
};

export default MockDataToggle;