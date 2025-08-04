import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Alert,
  CircularProgress,
  Typography,
  IconButton,
  InputAdornment,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import {
  Close as CloseIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import apiClient from '../../api/client';
import { toast } from 'react-hot-toast';

interface AddDataSourceDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const connectionTypes = [
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'mysql', label: 'MySQL' },
  { value: 'oracle', label: 'Oracle' },
  { value: 'sqlserver', label: 'SQL Server' },
  { value: 'csv', label: 'CSV File' },
  { value: 'excel', label: 'Excel File' },
];

export const AddDataSourceDialog: React.FC<AddDataSourceDialogProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [sourceName, setSourceName] = useState('');
  const [connectionType, setConnectionType] = useState('');
  const [description, setDescription] = useState('');
  
  // Connection details
  const [host, setHost] = useState('');
  const [port, setPort] = useState('');
  const [database, setDatabase] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  // Test query
  const [testQuery, setTestQuery] = useState('');
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionTestResult, setConnectionTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const steps = ['Basic Information', 'Connection Details', 'Test Connection'];

  const resetForm = () => {
    setActiveStep(0);
    setSourceName('');
    setConnectionType('');
    setDescription('');
    setHost('');
    setPort('');
    setDatabase('');
    setUsername('');
    setPassword('');
    setTestQuery('');
    setConnectionTestResult(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const createDataSourceMutation = useMutation({
    mutationFn: async (data: any) => {
      return await apiClient.post('/request-info/data-sources', data);
    },
    onSuccess: () => {
      toast.success('Data source created successfully');
      onSuccess();
      handleClose();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create data source');
    },
  });

  const testConnectionMutation = useMutation({
    mutationFn: async (data: any) => {
      return await apiClient.post('/request-info/data-sources/test', data);
    },
    onSuccess: (response) => {
      setConnectionTestResult({
        success: true,
        message: 'Connection successful!',
      });
      toast.success('Connection test successful');
    },
    onError: (error: any) => {
      setConnectionTestResult({
        success: false,
        message: error.response?.data?.detail || 'Connection failed',
      });
      toast.error('Connection test failed');
    },
  });

  const handleTestConnection = () => {
    const connectionDetails = {
      connection_type: connectionType,
      host,
      port: port ? parseInt(port) : undefined,
      database,
      username,
      password,
      test_query: testQuery || 'SELECT 1',
    };
    
    testConnectionMutation.mutate(connectionDetails);
  };

  const handleSubmit = () => {
    const dataSourceData = {
      source_name: sourceName,
      connection_type: connectionType,
      description,
      connection_details: {
        host,
        port: port ? parseInt(port) : undefined,
        database,
        username,
        password,
      },
      test_query: testQuery,
    };
    
    createDataSourceMutation.mutate(dataSourceData);
  };

  const canProceedToNext = () => {
    switch (activeStep) {
      case 0:
        return sourceName && connectionType;
      case 1:
        if (connectionType === 'csv' || connectionType === 'excel') {
          return true; // File-based sources handled differently
        }
        return host && database && username;
      case 2:
        return connectionTestResult?.success;
      default:
        return false;
    }
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Data Source Name"
              value={sourceName}
              onChange={(e) => setSourceName(e.target.value)}
              placeholder="e.g., Production Database"
              required
            />
            
            <FormControl fullWidth required>
              <InputLabel>Connection Type</InputLabel>
              <Select
                value={connectionType}
                onChange={(e) => setConnectionType(e.target.value)}
                label="Connection Type"
              >
                {connectionTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Description (Optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this data source contains..."
            />
          </Box>
        );
        
      case 1:
        if (connectionType === 'csv' || connectionType === 'excel') {
          return (
            <Alert severity="info">
              File-based data sources will be configured when uploading evidence.
            </Alert>
          );
        }
        
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                label="Host"
                value={host}
                onChange={(e) => setHost(e.target.value)}
                placeholder="localhost or IP address"
                required
              />
              
              <TextField
                label="Port"
                value={port}
                onChange={(e) => setPort(e.target.value)}
                placeholder={connectionType === 'postgresql' ? '5432' : '3306'}
                sx={{ width: 150 }}
              />
            </Box>
            
            <TextField
              fullWidth
              label="Database Name"
              value={database}
              onChange={(e) => setDatabase(e.target.value)}
              placeholder="database_name"
              required
            />
            
            <TextField
              fullWidth
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="db_user"
              required
            />
            
            <TextField
              fullWidth
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            
            <Alert severity="info">
              Your credentials will be encrypted and stored securely.
            </Alert>
          </Box>
        );
        
      case 2:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Test your connection with a simple query to ensure everything is configured correctly.
            </Typography>
            
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Test Query"
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              placeholder="SELECT 1"
              sx={{ fontFamily: 'monospace' }}
            />
            
            <Button
              variant="contained"
              onClick={handleTestConnection}
              disabled={testConnectionMutation.isPending}
              startIcon={testConnectionMutation.isPending ? <CircularProgress size={16} /> : null}
            >
              {testConnectionMutation.isPending ? 'Testing...' : 'Test Connection'}
            </Button>
            
            {connectionTestResult && (
              <Alert severity={connectionTestResult.success ? 'success' : 'error'}>
                {connectionTestResult.message}
              </Alert>
            )}
            
            {connectionTestResult?.success && (
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <CheckCircleIcon color="success" sx={{ fontSize: 48 }} />
                <Typography variant="h6" color="success.main" sx={{ mt: 1 }}>
                  Connection Successful!
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Your data source is ready to be saved.
                </Typography>
              </Box>
            )}
          </Box>
        );
        
      default:
        return null;
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose} 
      maxWidth="sm" 
      fullWidth
      PaperProps={{
        sx: { minHeight: 500 }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Add New Data Source</Typography>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        
        {getStepContent(activeStep)}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        
        {activeStep > 0 && (
          <Button onClick={() => setActiveStep(activeStep - 1)}>
            Back
          </Button>
        )}
        
        {activeStep < steps.length - 1 ? (
          <Button
            variant="contained"
            onClick={() => setActiveStep(activeStep + 1)}
            disabled={!canProceedToNext()}
          >
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!connectionTestResult?.success || createDataSourceMutation.isPending}
            startIcon={createDataSourceMutation.isPending ? <CircularProgress size={16} /> : null}
          >
            {createDataSourceMutation.isPending ? 'Creating...' : 'Create Data Source'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default AddDataSourceDialog;