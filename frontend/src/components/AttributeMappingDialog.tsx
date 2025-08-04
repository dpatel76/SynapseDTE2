import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  CircularProgress,
  Stack,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import {
  AutoFixHigh as AutoFixHighIcon,
  Security as SecurityIcon,
  Edit as EditIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Link as LinkIcon,
  LinkOff as LinkOffIcon,
} from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNotifications } from '../contexts/NotificationContext';

interface AttributeMapping {
  id: string;
  attribute_id: number;
  data_source_id: string;
  table_name: string;
  column_name: string;
  data_type: string;
  security_classification: 'HRCI' | 'Confidential' | 'Proprietary' | 'Public';
  mapping_confidence: number;
  llm_suggested: boolean;
  manual_override: boolean;
  is_validated: boolean;
  validation_error?: string;
}

interface ReportAttribute {
  attribute_id: number;
  attribute_name: string;
  description: string;
  data_type: string;
  is_primary_key: boolean;
  keywords_to_look_for?: string;
}

interface DataSource {
  data_source_id: string;
  source_name: string;
  source_type: string;
}

interface AttributeMappingDialogProps {
  open: boolean;
  onClose: () => void;
  reportId: number;
  cycleId: number;
}

// Mock API functions
const api = {
  getUnmappedAttributes: async (reportId: number): Promise<ReportAttribute[]> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return [
      {
        attribute_id: 1,
        attribute_name: 'Customer ID',
        description: 'Unique customer identifier',
        data_type: 'String',
        is_primary_key: true,
        keywords_to_look_for: 'customer_id, cust_id, customerid',
      },
      {
        attribute_id: 2,
        attribute_name: 'SSN',
        description: 'Social Security Number',
        data_type: 'String',
        is_primary_key: false,
        keywords_to_look_for: 'ssn, social_security, social_security_number',
      },
      {
        attribute_id: 3,
        attribute_name: 'Account Balance',
        description: 'Current account balance',
        data_type: 'Decimal',
        is_primary_key: false,
        keywords_to_look_for: 'balance, account_balance, current_balance',
      },
    ];
  },

  getDataSources: async (reportId: number): Promise<DataSource[]> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return [
      { data_source_id: '1', source_name: 'Customer Database', source_type: 'POSTGRESQL' },
      { data_source_id: '2', source_name: 'Transaction System', source_type: 'ORACLE' },
    ];
  },

  suggestMappings: async (reportId: number, dataSourceId: string): Promise<AttributeMapping[]> => {
    await new Promise(resolve => setTimeout(resolve, 2000));
    return [
      {
        id: '1',
        attribute_id: 1,
        data_source_id: dataSourceId,
        table_name: 'customers',
        column_name: 'customer_id',
        data_type: 'VARCHAR(50)',
        security_classification: 'Public',
        mapping_confidence: 95,
        llm_suggested: true,
        manual_override: false,
        is_validated: false,
      },
      {
        id: '2',
        attribute_id: 2,
        data_source_id: dataSourceId,
        table_name: 'customer_details',
        column_name: 'ssn_encrypted',
        data_type: 'VARCHAR(255)',
        security_classification: 'HRCI',
        mapping_confidence: 88,
        llm_suggested: true,
        manual_override: false,
        is_validated: false,
      },
      {
        id: '3',
        attribute_id: 3,
        data_source_id: dataSourceId,
        table_name: 'accounts',
        column_name: 'current_balance',
        data_type: 'DECIMAL(15,2)',
        security_classification: 'Confidential',
        mapping_confidence: 92,
        llm_suggested: true,
        manual_override: false,
        is_validated: false,
      },
    ];
  },

  validateMapping: async (mappingId: string): Promise<{ success: boolean; error?: string }> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return Math.random() > 0.2
      ? { success: true }
      : { success: false, error: 'Column not found in table' };
  },

  saveMappings: async (mappings: AttributeMapping[]): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
  },
};

const getSecurityChipColor = (classification: string) => {
  switch (classification) {
    case 'HRCI': return 'error';
    case 'Confidential': return 'warning';
    case 'Proprietary': return 'info';
    case 'Public': return 'success';
    default: return 'default';
  }
};

const AttributeMappingDialog: React.FC<AttributeMappingDialogProps> = ({
  open,
  onClose,
  reportId,
  cycleId,
}) => {
  const [selectedDataSource, setSelectedDataSource] = useState<string>('');
  const [mappings, setMappings] = useState<AttributeMapping[]>([]);
  const [editingMapping, setEditingMapping] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Partial<AttributeMapping>>({});
  const { showToast } = useNotifications();

  // Queries
  const { data: attributes, isLoading: attributesLoading } = useQuery({
    queryKey: ['unmapped-attributes', reportId],
    queryFn: () => api.getUnmappedAttributes(reportId),
    enabled: open,
  });

  const { data: dataSources } = useQuery({
    queryKey: ['data-sources', reportId],
    queryFn: () => api.getDataSources(reportId),
    enabled: open,
  });

  // Mutations
  const suggestMutation = useMutation({
    mutationFn: () => api.suggestMappings(reportId, selectedDataSource),
    onSuccess: (data) => {
      setMappings(data);
      showToast('success', `LLM suggested ${data.length} mappings`);
    },
    onError: (error: Error) => {
      showToast('error', `Failed to suggest mappings: ${error.message}`);
    },
  });

  const validateMutation = useMutation({
    mutationFn: api.validateMapping,
    onSuccess: (result, mappingId) => {
      setMappings(prev => prev.map(m => 
        m.id === mappingId 
          ? { ...m, is_validated: result.success, validation_error: result.error }
          : m
      ));
      showToast(
        result.success ? 'success' : 'error',
        result.success ? 'Mapping validated successfully' : `Validation failed: ${result.error}`
      );
    },
  });

  const saveMutation = useMutation({
    mutationFn: () => api.saveMappings(mappings.filter(m => m.is_validated || m.manual_override)),
    onSuccess: () => {
      showToast('success', 'Mappings saved successfully');
      onClose();
    },
    onError: (error: Error) => {
      showToast('error', `Failed to save mappings: ${error.message}`);
    },
  });

  const handleSuggestMappings = () => {
    if (!selectedDataSource) {
      showToast('error', 'Please select a data source');
      return;
    }
    suggestMutation.mutate();
  };

  const handleEditMapping = (mapping: AttributeMapping) => {
    setEditingMapping(mapping.id);
    setEditValues({
      table_name: mapping.table_name,
      column_name: mapping.column_name,
      security_classification: mapping.security_classification,
    });
  };

  const handleSaveEdit = (mappingId: string) => {
    setMappings(prev => prev.map(m => 
      m.id === mappingId 
        ? { 
            ...m, 
            ...editValues, 
            manual_override: true,
            is_validated: false,
            mapping_confidence: 100,
          }
        : m
    ));
    setEditingMapping(null);
    setEditValues({});
    showToast('info', 'Mapping updated. Please validate before saving.');
  };

  const handleCancelEdit = () => {
    setEditingMapping(null);
    setEditValues({});
  };

  const getAttributeById = (attributeId: number) => {
    return attributes?.find(a => a.attribute_id === attributeId);
  };

  const validMappingsCount = mappings.filter(m => m.is_validated || m.manual_override).length;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={2}>
          <LinkIcon />
          <Typography variant="h6">Map Report Attributes to Data Elements</Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Box display="flex" flexDirection="column" gap={3}>
          {/* Data Source Selection */}
          <Box display="flex" gap={2} alignItems="center">
            <FormControl sx={{ minWidth: 300 }}>
              <InputLabel>Select Data Source</InputLabel>
              <Select
                value={selectedDataSource}
                onChange={(e) => setSelectedDataSource(e.target.value)}
                disabled={suggestMutation.isPending}
              >
                {dataSources?.map(ds => (
                  <MenuItem key={ds.data_source_id} value={ds.data_source_id}>
                    {ds.source_name} ({ds.source_type})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Button
              variant="contained"
              startIcon={<AutoFixHighIcon />}
              onClick={handleSuggestMappings}
              disabled={!selectedDataSource || suggestMutation.isPending}
            >
              {suggestMutation.isPending ? 'Analyzing...' : 'Suggest Mappings with LLM'}
            </Button>
          </Box>

          {/* Progress Indicator */}
          {suggestMutation.isPending && (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Analyzing database schema and suggesting mappings...
              </Typography>
              <LinearProgress />
            </Box>
          )}

          {/* Unmapped Attributes Summary */}
          {attributes && attributes.length > 0 && (
            <Alert severity="info">
              Found {attributes.length} unmapped attributes. 
              {mappings.length > 0 && ` ${validMappingsCount} validated mappings ready to save.`}
            </Alert>
          )}

          {/* Mappings Table */}
          {mappings.length > 0 && (
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Attribute</TableCell>
                    <TableCell>Table</TableCell>
                    <TableCell>Column</TableCell>
                    <TableCell>Security</TableCell>
                    <TableCell align="center">Confidence</TableCell>
                    <TableCell align="center">Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {mappings.map((mapping) => {
                    const attribute = getAttributeById(mapping.attribute_id);
                    const isEditing = editingMapping === mapping.id;
                    
                    return (
                      <TableRow key={mapping.id}>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {attribute?.attribute_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {attribute?.data_type}
                              {attribute?.is_primary_key && ' (PK)'}
                            </Typography>
                          </Box>
                        </TableCell>
                        
                        <TableCell>
                          {isEditing ? (
                            <TextField
                              size="small"
                              value={editValues.table_name || ''}
                              onChange={(e) => setEditValues({ ...editValues, table_name: e.target.value })}
                            />
                          ) : (
                            mapping.table_name
                          )}
                        </TableCell>
                        
                        <TableCell>
                          {isEditing ? (
                            <TextField
                              size="small"
                              value={editValues.column_name || ''}
                              onChange={(e) => setEditValues({ ...editValues, column_name: e.target.value })}
                            />
                          ) : (
                            <Box>
                              <Typography variant="body2">{mapping.column_name}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {mapping.data_type}
                              </Typography>
                            </Box>
                          )}
                        </TableCell>
                        
                        <TableCell>
                          {isEditing ? (
                            <FormControl size="small">
                              <Select
                                value={editValues.security_classification || mapping.security_classification}
                                onChange={(e) => setEditValues({ 
                                  ...editValues, 
                                  security_classification: e.target.value as any 
                                })}
                              >
                                <MenuItem value="HRCI">HRCI</MenuItem>
                                <MenuItem value="Confidential">Confidential</MenuItem>
                                <MenuItem value="Proprietary">Proprietary</MenuItem>
                                <MenuItem value="Public">Public</MenuItem>
                              </Select>
                            </FormControl>
                          ) : (
                            <Chip
                              icon={<SecurityIcon />}
                              label={mapping.security_classification}
                              size="small"
                              color={getSecurityChipColor(mapping.security_classification) as any}
                            />
                          )}
                        </TableCell>
                        
                        <TableCell align="center">
                          <Box display="flex" alignItems="center" gap={1}>
                            <LinearProgress 
                              variant="determinate" 
                              value={mapping.mapping_confidence} 
                              sx={{ width: 60, height: 8, borderRadius: 4 }}
                            />
                            <Typography variant="caption">
                              {mapping.mapping_confidence}%
                            </Typography>
                          </Box>
                        </TableCell>
                        
                        <TableCell align="center">
                          <Stack direction="row" spacing={1} justifyContent="center">
                            {mapping.is_validated && (
                              <Chip 
                                icon={<CheckIcon />} 
                                label="Validated" 
                                size="small" 
                                color="success" 
                              />
                            )}
                            {mapping.validation_error && (
                              <Tooltip title={mapping.validation_error}>
                                <Chip 
                                  icon={<CloseIcon />} 
                                  label="Invalid" 
                                  size="small" 
                                  color="error" 
                                />
                              </Tooltip>
                            )}
                            {mapping.llm_suggested && (
                              <Chip 
                                icon={<AutoFixHighIcon />} 
                                label="LLM" 
                                size="small" 
                                variant="outlined" 
                              />
                            )}
                            {mapping.manual_override && (
                              <Chip 
                                label="Manual" 
                                size="small" 
                                variant="outlined" 
                              />
                            )}
                          </Stack>
                        </TableCell>
                        
                        <TableCell align="right">
                          {isEditing ? (
                            <Stack direction="row" spacing={1}>
                              <IconButton 
                                size="small" 
                                onClick={() => handleSaveEdit(mapping.id)}
                                color="primary"
                              >
                                <CheckIcon />
                              </IconButton>
                              <IconButton 
                                size="small" 
                                onClick={handleCancelEdit}
                                color="error"
                              >
                                <CloseIcon />
                              </IconButton>
                            </Stack>
                          ) : (
                            <Stack direction="row" spacing={1}>
                              <Tooltip title="Edit Mapping">
                                <IconButton 
                                  size="small" 
                                  onClick={() => handleEditMapping(mapping)}
                                >
                                  <EditIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Validate Mapping">
                                <IconButton 
                                  size="small" 
                                  onClick={() => validateMutation.mutate(mapping.id)}
                                  disabled={validateMutation.isPending}
                                  color={mapping.is_validated ? 'success' : 'default'}
                                >
                                  {validateMutation.isPending ? (
                                    <CircularProgress size={16} />
                                  ) : mapping.is_validated ? (
                                    <CheckIcon />
                                  ) : (
                                    <LinkIcon />
                                  )}
                                </IconButton>
                              </Tooltip>
                            </Stack>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={() => saveMutation.mutate()}
          disabled={validMappingsCount === 0 || saveMutation.isPending}
          startIcon={saveMutation.isPending ? <CircularProgress size={16} /> : null}
        >
          Save {validMappingsCount} Validated Mappings
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AttributeMappingDialog;