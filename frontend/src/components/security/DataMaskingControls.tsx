import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Stack,
  Divider,
  Badge,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Shield as ShieldIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNotifications } from '../../contexts/NotificationContext';
import apiClient from '../../api/client';

interface SecurityClassification {
  classification: 'HRCI' | 'Confidential' | 'Proprietary' | 'Public';
  color: string;
  icon: React.ReactNode;
  requiresApproval: boolean;
}

interface MaskedField {
  fieldName: string;
  tableName: string;
  classification: SecurityClassification['classification'];
  isMasked: boolean;
  maskedValue?: string;
  originalValue?: string;
  lastUnmaskedBy?: string;
  lastUnmaskedAt?: string;
}

interface UnmaskRequest {
  requestId: string;
  fieldName: string;
  tableName: string;
  reason: string;
  requestedAt: string;
  status: 'pending' | 'approved' | 'denied';
  approvedBy?: string;
  approvalNotes?: string;
}

interface DataMaskingControlsProps {
  data: any;
  tableName: string;
  onDataUpdate: (updatedData: any) => void;
  readOnly?: boolean;
}

const SECURITY_CLASSIFICATIONS: Record<string, SecurityClassification> = {
  HRCI: {
    classification: 'HRCI',
    color: '#d32f2f',
    icon: <ShieldIcon />,
    requiresApproval: true,
  },
  Confidential: {
    classification: 'Confidential',
    color: '#f57c00',
    icon: <LockIcon />,
    requiresApproval: true,
  },
  Proprietary: {
    classification: 'Proprietary',
    color: '#1976d2',
    icon: <SecurityIcon />,
    requiresApproval: false,
  },
  Public: {
    classification: 'Public',
    color: '#388e3c',
    icon: <LockOpenIcon />,
    requiresApproval: false,
  },
};

const DataMaskingControls: React.FC<DataMaskingControlsProps> = ({
  data,
  tableName,
  onDataUpdate,
  readOnly = false,
}) => {
  const { user } = useAuth();
  const { showToast } = useNotifications();
  const [maskedFields, setMaskedFields] = useState<MaskedField[]>([]);
  const [showUnmaskDialog, setShowUnmaskDialog] = useState(false);
  const [selectedField, setSelectedField] = useState<MaskedField | null>(null);
  const [unmaskReason, setUnmaskReason] = useState('');
  const [showHistoryDialog, setShowHistoryDialog] = useState(false);
  const [fieldHistory, setFieldHistory] = useState<any[]>([]);

  // Load field security metadata
  const { data: securityMetadata, isLoading } = useQuery({
    queryKey: ['security-metadata', tableName],
    queryFn: async () => {
      const response = await apiClient.get(`/security/tables/${tableName}/fields`);
      return response.data;
    },
  });

  // Check user permissions
  const { data: userPermissions } = useQuery({
    queryKey: ['user-permissions', user?.user_id],
    queryFn: async () => {
      const response = await apiClient.get(`/users/${user?.user_id}/permissions`);
      return response.data;
    },
    enabled: !!user,
  });

  // Unmask field mutation
  const unmaskFieldMutation = useMutation({
    mutationFn: async ({ fieldName, reason }: { fieldName: string; reason: string }) => {
      const response = await apiClient.post(`/security/unmask`, {
        table_name: tableName,
        field_name: fieldName,
        reason: reason,
      });
      return response.data;
    },
    onSuccess: (data, variables) => {
      showToast('success', 'Field unmasked successfully');
      // Update the local data
      const updatedData = { ...data };
      updatedData[variables.fieldName] = data.unmasked_value;
      onDataUpdate(updatedData);
      setShowUnmaskDialog(false);
      setUnmaskReason('');
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Failed to unmask field');
    },
  });

  // Request unmask approval mutation
  const requestUnmaskMutation = useMutation({
    mutationFn: async ({ fieldName, reason }: { fieldName: string; reason: string }) => {
      const response = await apiClient.post(`/security/unmask-requests`, {
        table_name: tableName,
        field_name: fieldName,
        reason: reason,
      });
      return response.data;
    },
    onSuccess: () => {
      showToast('info', 'Unmask request submitted for approval');
      setShowUnmaskDialog(false);
      setUnmaskReason('');
    },
    onError: (error: any) => {
      showToast('error', error.response?.data?.detail || 'Failed to submit unmask request');
    },
  });

  useEffect(() => {
    if (securityMetadata && data) {
      const fields: MaskedField[] = [];
      
      for (const [fieldName, fieldInfo] of Object.entries(securityMetadata)) {
        const classification = (fieldInfo as any).classification;
        if (classification && classification !== 'Public') {
          fields.push({
            fieldName,
            tableName,
            classification,
            isMasked: (data[fieldName] as string)?.includes('*') || false,
            maskedValue: data[fieldName],
            lastUnmaskedBy: (fieldInfo as any).last_unmasked_by,
            lastUnmaskedAt: (fieldInfo as any).last_unmasked_at,
          });
        }
      }
      
      setMaskedFields(fields);
    }
  }, [securityMetadata, data, tableName]);

  const canUnmask = (classification: string) => {
    if (!userPermissions) return false;
    
    const requiredPermission = `view_${classification.toLowerCase()}_data`;
    return userPermissions.permissions?.includes(requiredPermission) || false;
  };

  const handleUnmaskField = (field: MaskedField) => {
    setSelectedField(field);
    
    const security = SECURITY_CLASSIFICATIONS[field.classification];
    
    if (security.requiresApproval && !canUnmask(field.classification)) {
      // Need to request approval
      setShowUnmaskDialog(true);
    } else if (canUnmask(field.classification)) {
      // Can unmask directly
      unmaskFieldMutation.mutate({
        fieldName: field.fieldName,
        reason: 'Direct access permission',
      });
    } else {
      showToast('error', 'You do not have permission to unmask this field');
    }
  };

  const handleSubmitUnmaskRequest = () => {
    if (!selectedField || !unmaskReason.trim()) return;
    
    const security = SECURITY_CLASSIFICATIONS[selectedField.classification];
    
    if (security.requiresApproval) {
      requestUnmaskMutation.mutate({
        fieldName: selectedField.fieldName,
        reason: unmaskReason,
      });
    } else {
      unmaskFieldMutation.mutate({
        fieldName: selectedField.fieldName,
        reason: unmaskReason,
      });
    }
  };

  const loadFieldHistory = async (fieldName: string) => {
    try {
      const response = await apiClient.get(
        `/security/tables/${tableName}/fields/${fieldName}/history`
      );
      setFieldHistory(response.data);
      setShowHistoryDialog(true);
    } catch (error) {
      showToast('error', 'Failed to load field history');
    }
  };

  if (isLoading) {
    return <Typography>Loading security metadata...</Typography>;
  }

  if (maskedFields.length === 0) {
    return null;
  }

  return (
    <Box>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" display="flex" alignItems="center" gap={1} gutterBottom>
            <SecurityIcon />
            Data Security Controls
          </Typography>
          
          <Alert severity="info" sx={{ mb: 2 }}>
            Some fields contain sensitive data and are masked based on their security classification.
            {!readOnly && ' Click the eye icon to request unmasking.'}
          </Alert>

          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Field</TableCell>
                  <TableCell>Classification</TableCell>
                  <TableCell>Current Value</TableCell>
                  <TableCell align="center">Status</TableCell>
                  {!readOnly && <TableCell align="center">Actions</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {maskedFields.map((field) => {
                  const security = SECURITY_CLASSIFICATIONS[field.classification];
                  return (
                    <TableRow key={field.fieldName}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {field.fieldName}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={security.icon as React.ReactElement}
                          label={field.classification}
                          size="small"
                          sx={{
                            backgroundColor: security.color,
                            color: 'white',
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          fontFamily="monospace"
                          color={field.isMasked ? 'text.secondary' : 'text.primary'}
                        >
                          {field.maskedValue || '—'}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Badge
                          color={field.isMasked ? 'warning' : 'success'}
                          variant="dot"
                        >
                          <Typography variant="caption">
                            {field.isMasked ? 'Masked' : 'Visible'}
                          </Typography>
                        </Badge>
                      </TableCell>
                      {!readOnly && (
                        <TableCell align="center">
                          <Stack direction="row" spacing={1} justifyContent="center">
                            <Tooltip title={field.isMasked ? 'Unmask Field' : 'Field is visible'}>
                              <span>
                                <IconButton
                                  size="small"
                                  onClick={() => handleUnmaskField(field)}
                                  disabled={!field.isMasked}
                                >
                                  {field.isMasked ? <VisibilityIcon /> : <VisibilityOffIcon />}
                                </IconButton>
                              </span>
                            </Tooltip>
                            <Tooltip title="View History">
                              <IconButton
                                size="small"
                                onClick={() => loadFieldHistory(field.fieldName)}
                              >
                                <HistoryIcon />
                              </IconButton>
                            </Tooltip>
                          </Stack>
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>

          {userPermissions && (
            <Box mt={2}>
              <Typography variant="caption" color="text.secondary">
                Your permissions: {userPermissions.permissions?.filter((p: string) => p.includes('view_')).join(', ') || 'None'}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Unmask Request Dialog */}
      <Dialog
        open={showUnmaskDialog}
        onClose={() => setShowUnmaskDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Request Field Unmask
          {selectedField && (
            <Typography variant="body2" color="text.secondary">
              Field: {selectedField.fieldName}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedField && (
            <Stack spacing={2}>
              <Alert 
                severity="warning" 
                icon={SECURITY_CLASSIFICATIONS[selectedField.classification].icon}
              >
                This field contains {selectedField.classification} data and requires approval to unmask.
              </Alert>
              
              <TextField
                label="Reason for Unmask Request"
                multiline
                rows={4}
                value={unmaskReason}
                onChange={(e) => setUnmaskReason(e.target.value)}
                fullWidth
                placeholder="Please provide a business justification for accessing this sensitive data..."
                helperText="Your request will be logged and reviewed by authorized personnel"
              />
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowUnmaskDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSubmitUnmaskRequest}
            disabled={!unmaskReason.trim() || requestUnmaskMutation.isPending}
          >
            Submit Request
          </Button>
        </DialogActions>
      </Dialog>

      {/* Field History Dialog */}
      <Dialog
        open={showHistoryDialog}
        onClose={() => setShowHistoryDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Field Access History</DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Date/Time</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Reason</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {fieldHistory.map((entry: any, index: number) => (
                  <TableRow key={index}>
                    <TableCell>
                      {new Date(entry.timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell>{entry.user_name}</TableCell>
                    <TableCell>
                      <Chip
                        label={entry.action}
                        size="small"
                        color={entry.action === 'unmasked' ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell>{entry.reason}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHistoryDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DataMaskingControls;