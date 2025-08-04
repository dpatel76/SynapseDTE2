import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Chip,
  IconButton,
  Tooltip,
  Divider,
  CircularProgress,
  TextField,
  FormHelperText,
} from '@mui/material';
import {
  AutoFixHigh as AutoFixHighIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import apiClient from '../../api/client';

interface Attribute {
  id: number;
  attribute_name: string;
  description?: string;
  data_type: string;
  mandatory_flag: string;
  cde_flag: boolean;
  is_primary_key: boolean;
  is_scoped?: boolean;
  testing_approach?: string;
  line_item_number?: string;
  technical_line_item_name?: string;
  mdrm?: string;
  historical_issues_flag?: boolean;
}

interface DataSource {
  id: number;
  name: string;
  source_type: string;
}

interface PDEMapping {
  id?: number;
  attribute_id: number;
  attribute_name: string;
  pde_name: string;
  pde_code: string;
  pde_description?: string;
  data_source_id?: number;
  source_field?: string;
  source_table?: string;
  source_column?: string;
  column_data_type?: string;
  transformation_rule?: any;
  mapping_type?: string;
  llm_confidence_score?: number;
  llm_mapping_rationale?: string;
  business_process?: string;
  mapping_confirmed_by_user: boolean;
}

interface BulkMappingResult {
  attribute_id: number;
  success: boolean;
  mapping?: PDEMapping;
  error?: string;
}

interface BulkPDEMappingProps {
  cycleId: string;
  reportId: string;
  attributes: Attribute[];
  dataSources: DataSource[];
  existingMappings: PDEMapping[];
  onMappingsCreated: () => void;
}

export const BulkPDEMapping: React.FC<BulkPDEMappingProps> = ({
  cycleId,
  reportId,
  attributes,
  dataSources,
  existingMappings,
  onMappingsCreated,
}) => {
  // Ensure all props are arrays to prevent runtime errors
  const safeAttributes = Array.isArray(attributes) ? attributes : [];
  const safeDataSources = Array.isArray(dataSources) ? dataSources : [];
  const safeExistingMappings = Array.isArray(existingMappings) ? existingMappings : [];
  const [selectedAttributes, setSelectedAttributes] = useState<Set<number>>(new Set());
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<BulkMappingResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [editingMapping, setEditingMapping] = useState<PDEMapping | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  // Get unmapped attributes and sort them
  const unmappedAttributes = safeAttributes
    .filter(attr => !safeExistingMappings.some(m => m.attribute_id === attr.id))
    .sort((a, b) => {
      // First, sort by primary key flag (PK first)
      if (a.is_primary_key && !b.is_primary_key) return -1;
      if (!a.is_primary_key && b.is_primary_key) return 1;
      
      // Then, sort by badges (CDE, then historical issues)
      const aBadgeScore = (a.cde_flag ? 2 : 0) + (a.historical_issues_flag ? 1 : 0);
      const bBadgeScore = (b.cde_flag ? 2 : 0) + (b.historical_issues_flag ? 1 : 0);
      if (aBadgeScore !== bBadgeScore) return bBadgeScore - aBadgeScore;
      
      // Finally, sort by line item number (numeric sort)
      const aLineNum = parseInt(a.line_item_number || '999999');
      const bLineNum = parseInt(b.line_item_number || '999999');
      return aLineNum - bLineNum;
    });

  const handleSelectAll = () => {
    if (selectedAttributes.size === unmappedAttributes.length) {
      setSelectedAttributes(new Set());
    } else {
      setSelectedAttributes(new Set(unmappedAttributes.map(a => a.id)));
    }
  };

  const handleSelectAttribute = (attrId: number) => {
    const newSelected = new Set(selectedAttributes);
    if (newSelected.has(attrId)) {
      newSelected.delete(attrId);
    } else {
      newSelected.add(attrId);
    }
    setSelectedAttributes(newSelected);
  };

  const handleBulkMapping = async () => {
    if (selectedAttributes.size === 0) return;

    setProcessing(true);
    setProgress(0);
    setResults([]);

    const selectedAttrs = unmappedAttributes.filter(a => selectedAttributes.has(a.id));
    const batchSize = 5; // Process 5 attributes at a time
    const totalBatches = Math.ceil(selectedAttrs.length / batchSize);
    const allResults: BulkMappingResult[] = [];

    for (let i = 0; i < selectedAttrs.length; i += batchSize) {
      const batch = selectedAttrs.slice(i, i + batchSize);
      const batchResults = await Promise.all(
        batch.map(async (attr) => {
          try {
            // Get AI suggestion with increased timeout
            const suggestionResponse = await apiClient.post(
              `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/suggest`,
              {},
              { 
                params: { attribute_id: attr.id },
                timeout: 120000 // 2 minutes timeout for LLM processing
              }
            );

            const suggestion = suggestionResponse.data;
            
            // Log the LLM response for debugging
            console.log(`LLM suggestion for ${attr.attribute_name}:`, suggestion.llm_suggested_mapping);
            
            // Create the simplified mapping - PDE name/code will be auto-generated from attribute
            const mappingData = {
              attribute_id: attr.id,
              pde_name: attr.attribute_name, // Use attribute name as PDE name
              pde_code: `${attr.attribute_name.toUpperCase().replace(/\s+/g, '_')}`, // Simple code generation
              pde_description: attr.description || `Physical data element for ${attr.attribute_name}`,
              data_source_id: suggestion.llm_suggested_mapping?.data_source_id,
              source_field: (() => {
                // Try to construct source_field from various possible formats
                const llm = suggestion.llm_suggested_mapping;
                if (!llm) return null;
                
                // If source_field is already properly formatted, use it
                if (llm.source_field && llm.source_field.includes('.')) {
                  return llm.source_field;
                }
                
                // If we have table_name and column_name, combine them
                if (llm.table_name && llm.column_name) {
                  return `${llm.table_name}.${llm.column_name}`;
                }
                
                // If we have table_column, use it
                if (llm.table_column && llm.table_column.includes('.')) {
                  return llm.table_column;
                }
                
                // If we only have column_name or source_field without table, try to find table from data source
                const columnName = llm.column_name || llm.source_field || llm.table_column;
                if (columnName && !columnName.includes('.')) {
                  // For now, just return the column name - the backend should handle finding the table
                  return columnName;
                }
                
                return llm.source_field || llm.table_column || null;
              })(),
              transformation_rule: null, // Simplified - no transformation rules
              mapping_type: 'direct', // Always direct mapping for simplicity
              llm_suggested_mapping: suggestion.llm_suggested_mapping,
              llm_confidence_score: suggestion.confidence_score,
              llm_mapping_rationale: suggestion.rationale,
              llm_alternative_mappings: suggestion.alternative_mappings,
              mapping_confirmed_by_user: false,
              business_process: null, // Simplified - remove business process
            };

            console.log(`Mapping data for ${attr.attribute_name}:`, mappingData);

            const createResponse = await apiClient.post(
              `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings`,
              mappingData
            );

            console.log(`Created PDE mapping for ${attr.attribute_name}:`, createResponse.data);

            return {
              attribute_id: attr.id,
              success: true,
              mapping: createResponse.data,
            };
          } catch (error: any) {
            console.error(`Failed to map attribute ${attr.attribute_name}:`, error);
            return {
              attribute_id: attr.id,
              success: false,
              error: error.response?.data?.detail || error.message,
            };
          }
        })
      );

      allResults.push(...batchResults);
      setProgress(((i + batch.length) / selectedAttrs.length) * 100);

      // Small delay between batches to avoid rate limiting
      if (i + batchSize < selectedAttrs.length) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }

    setResults(allResults);
    setShowResults(true);
    setProcessing(false);
    setSelectedAttributes(new Set());

    // Refresh the parent component
    const successCount = allResults.filter(r => r.success).length;
    if (successCount > 0) {
      onMappingsCreated();
    }
  };

  const handleEditMapping = (mapping: PDEMapping) => {
    setEditingMapping(mapping);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!editingMapping) return;

    try {
      await apiClient.put(
        `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/${editingMapping.id}`,
        editingMapping
      );
      setEditDialogOpen(false);
      setEditingMapping(null);
      onMappingsCreated();
    } catch (error) {
      console.error('Failed to update mapping:', error);
    }
  };

  const getConfidenceIcon = (score?: number) => {
    if (!score) return <WarningIcon color="disabled" />;
    if (score >= 80) return <CheckCircleIcon color="success" />;
    if (score >= 60) return <WarningIcon color="warning" />;
    return <ErrorIcon color="error" />;
  };

  return (
    <Box>
      {/* Selection Interface */}
      {unmappedAttributes.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Bulk PDE Mapping</Typography>
              <Box display="flex" gap={2}>
                <Button
                  variant="outlined"
                  onClick={handleSelectAll}
                  disabled={processing}
                >
                  {selectedAttributes.size === unmappedAttributes.length ? 'Deselect All' : 'Select All'}
                </Button>
                <Button
                  variant="contained"
                  startIcon={<AutoFixHighIcon />}
                  onClick={handleBulkMapping}
                  disabled={selectedAttributes.size === 0 || processing}
                >
                  Map {selectedAttributes.size} Attributes with AI
                </Button>
              </Box>
            </Box>

            <Alert severity="info" sx={{ mb: 2 }}>
              Select multiple attributes below to map them to Physical Data Elements (PDEs) in bulk using AI suggestions.
              The system will map report attributes to columns in your configured data sources.
            </Alert>

            {processing && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Processing {selectedAttributes.size} attributes...
                </Typography>
                <LinearProgress variant="determinate" value={progress} />
              </Box>
            )}

            <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox" width="40px">
                      <Checkbox
                        checked={selectedAttributes.size === unmappedAttributes.length && unmappedAttributes.length > 0}
                        indeterminate={selectedAttributes.size > 0 && selectedAttributes.size < unmappedAttributes.length}
                        onChange={handleSelectAll}
                        disabled={processing}
                      />
                    </TableCell>
                    <TableCell>Line Item #</TableCell>
                    <TableCell>Attribute Name</TableCell>
                    <TableCell>Technical Name</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>MDRM</TableCell>
                    <TableCell>Data Type</TableCell>
                    <TableCell>Mandatory</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {unmappedAttributes.map((attr) => (
                    <TableRow
                      key={attr.id}
                      hover
                      selected={selectedAttributes.has(attr.id)}
                      onClick={() => handleSelectAttribute(attr.id)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedAttributes.has(attr.id)}
                          disabled={processing}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {attr.line_item_number || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {attr.attribute_name}
                          </Typography>
                          <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5 }}>
                            {attr.cde_flag && (
                              <Chip size="small" label="CDE" color="warning" sx={{ height: '20px' }} />
                            )}
                            {attr.is_primary_key && (
                              <Chip size="small" label="PK" color="info" sx={{ height: '20px' }} />
                            )}
                            {attr.historical_issues_flag && (
                              <Chip size="small" label="Issues" color="error" sx={{ height: '20px' }} />
                            )}
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {attr.technical_line_item_name || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {attr.description || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {attr.mdrm || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {attr.data_type || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={attr.mandatory_flag || 'Optional'}
                          color={
                            attr.mandatory_flag === 'Mandatory' ? 'error' :
                            attr.mandatory_flag === 'Conditional' ? 'warning' :
                            'default'
                          }
                          variant="outlined"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Results Dialog */}
      <Dialog
        open={showResults}
        onClose={() => setShowResults(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box>
            <Typography component="div">Bulk Mapping Results</Typography>
            <Typography variant="body2" color="textSecondary" component="div">
              Successfully mapped {results.filter(r => r.success).length} of {results.length} attributes
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>Attribute</TableCell>
                  <TableCell>PDE Name</TableCell>
                  <TableCell>Confidence</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {results.map((result) => {
                  const attr = safeAttributes.find(a => a.id === result.attribute_id);
                  return (
                    <TableRow key={result.attribute_id}>
                      <TableCell>
                        {result.success ? (
                          <CheckCircleIcon color="success" />
                        ) : (
                          <Tooltip title={result.error}>
                            <ErrorIcon color="error" />
                          </Tooltip>
                        )}
                      </TableCell>
                      <TableCell>{attr?.attribute_name}</TableCell>
                      <TableCell>
                        {result.mapping?.pde_name || '-'}
                      </TableCell>
                      <TableCell>
                        {result.mapping && (
                          <Box display="flex" alignItems="center" gap={1}>
                            {getConfidenceIcon(result.mapping.llm_confidence_score)}
                            <Typography variant="caption">
                              {result.mapping.llm_confidence_score}%
                            </Typography>
                          </Box>
                        )}
                      </TableCell>
                      <TableCell>
                        {result.mapping && (
                          <IconButton
                            size="small"
                            onClick={() => handleEditMapping(result.mapping!)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowResults(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Mapping Dialog - Simplified */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Edit PDE Mapping</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                Map <strong>{editingMapping?.attribute_name}</strong> to a database column
              </Alert>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth required>
                <InputLabel>Data Source</InputLabel>
                <Select
                  value={editingMapping?.data_source_id || ''}
                  onChange={(e) => setEditingMapping(prev => prev ? {...prev, data_source_id: e.target.value as number} : null)}
                  label="Data Source"
                >
                  <MenuItem value="">Select a data source</MenuItem>
                  {safeDataSources.map((ds) => (
                    <MenuItem key={ds.id} value={ds.id}>
                      {ds.name} ({ds.source_type})
                    </MenuItem>
                  ))}
                </Select>
                <FormHelperText>Select the database connection</FormHelperText>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                required
                label="Table.Column"
                value={editingMapping?.source_field || ''}
                onChange={(e) => setEditingMapping(prev => prev ? {...prev, source_field: e.target.value} : null)}
                placeholder="schema.table_name.column_name"
                helperText="Enter the fully qualified column name (e.g., public.customers.customer_id)"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleSaveEdit} 
            variant="contained"
            disabled={!editingMapping?.data_source_id || !editingMapping?.source_field}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};