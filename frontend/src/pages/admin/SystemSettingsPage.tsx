import React from 'react';
import { Box, Typography } from '@mui/material';
import { Settings as SettingsIcon } from '@mui/icons-material';

const SystemSettingsPage: React.FC = () => {
  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom display="flex" alignItems="center" gap={2}>
        <SettingsIcon fontSize="large" />
        System Settings
      </Typography>
      <Typography color="text.secondary">
        Configure global system settings and preferences.
      </Typography>
    </Box>
  );
};

export default SystemSettingsPage; 