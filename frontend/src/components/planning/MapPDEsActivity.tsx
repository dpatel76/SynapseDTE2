import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Alert,
  Snackbar,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  FormHelperText,
  LinearProgress,
  Tooltip,
  Divider,
  FormControlLabel,
  Switch,
  CircularProgress,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  // Tabs, // No longer needed
  // Tab, // No longer needed
  // Checkbox, // No longer needed
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  AutoFixHigh as AutoFixHighIcon,
  Psychology as PsychologyIcon,
  Link as LinkIcon,
  Functions as FunctionsIcon,
  Storage as StorageIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  // RateReview as ReviewIcon, // No longer needed
  // Check as CheckIcon, // No longer needed
  // Close as CloseIcon, // No longer needed
  // CheckBox as CheckBoxIcon, // No longer needed
  // CheckBoxOutlineBlank as CheckBoxOutlineBlankIcon, // No longer needed
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
// import { PDEMappingReview } from './PDEMappingReview'; // No longer needed
import { BulkPDEMapping } from './BulkPDEMapping';

interface Attribute {
  id: number;
  attribute_id: number; // Backend sends attribute_id, not id
  attribute_name: string;
  description?: string;
  data_type: string;
  mandatory_flag: string;
  cde_flag: boolean;
  is_scoped: boolean;
  is_primary_key: boolean;
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
  id: number;
  cycle_id: number;
  report_id: number;
  attribute_id: number;
  attribute_name: string;
  data_source_id?: number;
  data_source_name?: string;
  pde_name: string;
  pde_code: string;
  pde_description?: string;
  source_field?: string;
  source_table?: string;
  source_column?: string;
  column_data_type?: string;
  transformation_rule?: any;
  mapping_type?: string;
  llm_suggested_mapping?: any;
  llm_confidence_score?: number;
  llm_mapping_rationale?: string;
  llm_alternative_mappings?: any[];
  mapping_confirmed_by_user: boolean;
  business_process?: string;
  business_owner?: string;
  data_steward?: string;
  is_validated: boolean;
  validation_message?: string;
  created_at: string;
  updated_at: string;
  // Attribute fields included in the mapping response
  data_type?: string;
  is_primary_key?: boolean;
  validation_rules?: string;
  approval_status?: string;
  line_item_number?: string;
  technical_line_item_name?: string;
  description?: string;
  mdrm?: string;
  mandatory_flag?: string;
  cde_flag?: boolean;
  historical_issues_flag?: boolean;
  // Classification fields
  information_security_classification?: string;
  criticality?: string;
  risk_level?: string;
  regulatory_flag?: boolean;
  pii_flag?: boolean;
  llm_classification_rationale?: string;
  llm_regulatory_references?: string[];
}

interface LLMMappingSuggestion {
  attribute_id: number;
  attribute_name: string;
  llm_suggested_mapping: any;
  confidence_score: number;
  rationale: string;
  alternative_mappings: any[];
}

const mappingTypes = [
  { value: 'direct', label: 'Direct Mapping', icon: <LinkIcon /> },
  { value: 'calculated', label: 'Calculated', icon: <FunctionsIcon /> },
  { value: 'lookup', label: 'Lookup', icon: <StorageIcon /> },
  { value: 'conditional', label: 'Conditional', icon: <ExpandMoreIcon /> },
];

interface MapPDEsActivityProps {
  cycleId?: string;
  reportId?: string;
  activeJobId?: string | null;
}

export const MapPDEsActivity: React.FC<MapPDEsActivityProps> = (props) => {
  const params = useParams<{ cycleId: string; reportId: string }>();
  const cycleId = props.cycleId || params.cycleId;
  const reportId = props.reportId || params.reportId;
  const auth = useAuth();
  const [attributes, setAttributes] = useState<Attribute[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [pdeMappings, setPdeMappings] = useState<PDEMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingMapping, setEditingMapping] = useState<PDEMapping | null>(null);
  const [llmSuggestion, setLlmSuggestion] = useState<LLMMappingSuggestion | null>(null);
  const [loadingLLM, setLoadingLLM] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  // const [tabValue, setTabValue] = useState(0); // No longer needed without tabs
  // const [selectedMappings, setSelectedMappings] = useState<Set<number>>(new Set()); // No longer needed
  // const [processingApproval, setProcessingApproval] = useState(false); // No longer needed
  const [jobProgress, setJobProgress] = useState<any>(null);
  const [regeneratingMappingId, setRegeneratingMappingId] = useState<number | null>(null);
  const [regeneratingAll, setRegeneratingAll] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    attribute_id: 0,
    data_source_id: null as number | null,
    pde_name: '',
    pde_code: '',
    pde_description: '',
    source_field: '',
    transformation_rule: {},
    mapping_type: 'direct',
    llm_suggested_mapping: null as any,
    llm_confidence_score: null as number | null,
    llm_mapping_rationale: null as string | null,
    llm_alternative_mappings: null as any[] | null,
    mapping_confirmed_by_user: false,
    business_process: '',
    business_owner: '',
    data_steward: '',
    profiling_criteria: {},
  });

  // Load initial data
  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load attributes
      const attributesResponse = await apiClient.get(
        `/planning/cycles/${cycleId}/reports/${reportId}/attributes`
      );
      setAttributes(Array.isArray(attributesResponse.data) ? attributesResponse.data : []);
      
      // Load data sources
      const dataSourcesResponse = await apiClient.get(
        `/planning/cycles/${cycleId}/reports/${reportId}/data-sources`
      );
      setDataSources(Array.isArray(dataSourcesResponse.data) ? dataSourcesResponse.data : []);
      
      // Load existing mappings with increased timeout
      const mappingsResponse = await apiClient.get(
        `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings`,
        { timeout: 60000 } // 60 seconds timeout
      );
      const mappingsData = mappingsResponse.data?.mappings || [];
      console.log('Loaded PDE mappings:', mappingsData);
      // Log first mapping details to debug
      if (mappingsData.length > 0) {
        console.log('First mapping details:', {
          source_field: mappingsData[0].source_field,
          source_table: mappingsData[0].source_table,
          source_column: mappingsData[0].source_column,
          data_source_name: mappingsData[0].data_source_name
        });
      }
      setPdeMappings(mappingsData);
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load data');
      // Ensure arrays are initialized even on error
      setPdeMappings([]);
      setAttributes([]);
      setDataSources([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Check for any active PDE mapping jobs when component mounts
    checkForActiveJobs();
  }, [cycleId, reportId]);

  // Check for active jobs related to this cycle/report
  const checkForActiveJobs = async () => {
    try {
      console.log('Checking for active jobs...');
      const response = await apiClient.get('/jobs/active');
      const activeJobs = response.data.active_jobs || [];
      console.log('Active jobs response:', activeJobs);
      
      // Find any active PDE mapping job for this cycle/report
      const activePDEJob = activeJobs.find((job: any) => 
        job.job_type === 'pde_auto_mapping' && 
        job.metadata?.cycle_id === parseInt(cycleId!) &&
        job.metadata?.report_id === parseInt(reportId!) &&
        (job.status === 'pending' || job.status === 'running')
      );
      
      if (activePDEJob) {
        console.log('Found active PDE mapping job:', activePDEJob);
        // Start polling this job - use job_id not id
        const jobId = activePDEJob.job_id || activePDEJob.id;
        if (jobId) {
          pollJobStatus(jobId);
        } else {
          console.error('Active job found but no job_id field:', activePDEJob);
        }
      } else {
        console.log('No active PDE mapping job found for this cycle/report');
      }
    } catch (error) {
      console.error('Error checking for active jobs in MapPDEsActivity:', error);
    }
  };

  // Polling interval reference
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Poll job status function
  const pollJobStatus = (jobId: string) => {
    // Validate job ID
    if (!jobId || jobId === 'undefined') {
      console.error('Invalid job ID provided to pollJobStatus:', jobId);
      return;
    }

    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    const poll = async () => {
      try {
        const response = await apiClient.get(`/jobs/${jobId}/status`);
        const jobData = response.data;
        
        setJobProgress(jobData);
        
        if (jobData.status === 'completed') {
          setSuccess(`Auto-mapping completed! ${jobData.result?.mapped_count || 0} attributes mapped.`);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          loadData(); // Reload to show new mappings
        } else if (jobData.status === 'failed') {
          setError(`Auto-mapping failed: ${jobData.error || 'Unknown error'}`);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    };

    // Start polling immediately
    poll();
    
    // Then poll every 2 seconds
    pollingIntervalRef.current = setInterval(poll, 2000);
  };

  // Poll for active job status from props
  useEffect(() => {
    if (props.activeJobId) {
      pollJobStatus(props.activeJobId);
    }
    
    // Cleanup on unmount or when activeJobId changes
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [props.activeJobId]);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleGetLLMSuggestion = async (attributeId?: number) => {
    const targetAttributeId = attributeId || formData.attribute_id;
    if (!targetAttributeId) {
      setError('Please select an attribute first');
      return;
    }
    
    try {
      setLoadingLLM(true);
      const response = await apiClient.post(
        `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/suggest`,
        {},
        {
          params: { attribute_id: targetAttributeId }
        }
      );
      
      setLlmSuggestion(response.data);
      
      // If in dialog, auto-fill form with suggestion
      if (!attributeId && response.data.llm_suggested_mapping) {
        const suggestion = response.data.llm_suggested_mapping;
        setFormData(prev => ({
          ...prev,
          pde_name: suggestion.pde_name || '',
          pde_code: suggestion.pde_code || '',
          pde_description: suggestion.pde_description || '',
          data_source_id: suggestion.data_source_id || null,
          source_field: suggestion.source_field || '',
          transformation_rule: suggestion.transformation_rule || {},
          mapping_type: suggestion.mapping_type || 'direct',
          business_process: suggestion.business_process || '',
          llm_suggested_mapping: suggestion,
          llm_confidence_score: response.data.confidence_score,
          llm_mapping_rationale: response.data.rationale,
          llm_alternative_mappings: response.data.alternative_mappings,
        }));
      }
    } catch (err) {
      console.error('Error getting LLM suggestion:', err);
      setError('Failed to get LLM suggestion');
    } finally {
      setLoadingLLM(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const endpoint = editingMapping
        ? `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/${editingMapping.id}`
        : `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings`;
      
      const method = editingMapping ? 'put' : 'post';
      
      await apiClient[method](endpoint, formData);
      
      setSuccess(editingMapping ? 'PDE mapping updated successfully' : 'PDE mapping created successfully');
      setDialogOpen(false);
      resetForm();
      loadData();
    } catch (err: any) {
      console.error('Error saving PDE mapping:', err);
      setError(err.response?.data?.detail || 'Failed to save PDE mapping');
    }
  };

  const handleEdit = (mapping: PDEMapping) => {
    setEditingMapping(mapping);
    setFormData({
      attribute_id: mapping.attribute_id,
      data_source_id: mapping.data_source_id || null,
      pde_name: mapping.pde_name,
      pde_code: mapping.pde_code,
      pde_description: mapping.pde_description || '',
      source_field: mapping.source_field || '',
      transformation_rule: mapping.transformation_rule || {},
      mapping_type: mapping.mapping_type || 'direct',
      llm_suggested_mapping: mapping.llm_suggested_mapping,
      llm_confidence_score: mapping.llm_confidence_score ?? null,
      llm_mapping_rationale: mapping.llm_mapping_rationale ?? null,
      llm_alternative_mappings: mapping.llm_alternative_mappings ?? null,
      mapping_confirmed_by_user: mapping.mapping_confirmed_by_user,
      business_process: mapping.business_process || '',
      business_owner: mapping.business_owner || '',
      data_steward: mapping.data_steward || '',
      profiling_criteria: {},
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this PDE mapping?')) {
      return;
    }
    
    try {
      await apiClient.delete(
        `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/${id}`
      );
      setSuccess('PDE mapping deleted successfully');
      loadData();
    } catch (err) {
      console.error('Error deleting PDE mapping:', err);
      setError('Failed to delete PDE mapping');
    }
  };

  const handleRegenerateMapping = async (mapping: PDEMapping) => {
    try {
      setRegeneratingMappingId(mapping.id);
      
      // Get new suggestion from LLM
      const response = await apiClient.post(
        `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/suggest`,
        {},
        {
          params: { attribute_id: mapping.attribute_id }
        }
      );
      
      if (response.data.success && response.data.suggestion) {
        const suggestion = response.data.suggestion;
        
        // Build the source_field from the suggestion
        let sourceField = '';
        if (suggestion.table_name && suggestion.column_name) {
          // Check if table_name already includes schema
          if (suggestion.table_name.includes('.')) {
            sourceField = `${suggestion.table_name}.${suggestion.column_name}`;
          } else {
            // Assume public schema if not specified
            sourceField = `public.${suggestion.table_name}.${suggestion.column_name}`;
          }
        }
        
        // Find data source ID by name
        let dataSourceId = mapping.data_source_id;
        if (suggestion.data_source_name) {
          const dataSource = dataSources.find(ds => ds.name === suggestion.data_source_name);
          if (dataSource) {
            dataSourceId = dataSource.id;
          }
        }
        
        // Update the existing mapping with new suggestion
        await apiClient.put(
          `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/${mapping.id}`,
          {
            data_source_id: dataSourceId,
            source_field: sourceField,
            llm_confidence_score: suggestion.confidence,
            llm_mapping_rationale: suggestion.reasoning,
            mapping_confirmed_by_user: false // Reset confirmation since it's regenerated
          }
        );
        
        setSuccess('Mapping regenerated successfully');
        loadData();
      } else {
        setError('No new mapping suggestion available for this attribute');
      }
    } catch (err: any) {
      console.error('Error regenerating mapping:', err);
      setError(err.response?.data?.detail || 'Failed to regenerate mapping');
    } finally {
      setRegeneratingMappingId(null);
    }
  };

  const handleRegenerateAllMappings = async () => {
    if (!window.confirm('This will regenerate all PDE mappings and classifications. Continue?')) {
      return;
    }

    try {
      setRegeneratingAll(true);
      setError(null);
      
      // Call the endpoint to regenerate all mappings
      const url = `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/regenerate-all`;
      console.log('🔄 Calling regenerate-all endpoint:', url);
      console.log('cycleId:', cycleId, 'reportId:', reportId);
      const response = await apiClient.post(url);
      
      if (response.data.job_id) {
        setSuccess('Regeneration started. This may take a few minutes...');
        // Start polling for job progress
        pollJobStatus(response.data.job_id);
      } else {
        setSuccess('All mappings regenerated successfully');
        loadData();
      }
    } catch (err: any) {
      console.error('Error regenerating all mappings:', err);
      console.error('Error details:', {
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        config: err.config
      });
      setError(err.response?.data?.detail || 'Failed to regenerate mappings');
    } finally {
      setRegeneratingAll(false);
    }
  };


  const resetForm = () => {
    setFormData({
      attribute_id: 0,
      data_source_id: null,
      pde_name: '',
      pde_code: '',
      pde_description: '',
      source_field: '',
      transformation_rule: {},
      mapping_type: 'direct',
      llm_suggested_mapping: null as any,
      llm_confidence_score: null as number | null,
      llm_mapping_rationale: null as string | null,
      llm_alternative_mappings: null as any[] | null,
      mapping_confirmed_by_user: false,
      business_process: '',
      business_owner: '',
      data_steward: '',
      profiling_criteria: {},
    });
    setEditingMapping(null);
    setLlmSuggestion(null);
  };

  const toggleRowExpansion = (attributeId: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(attributeId)) {
      newExpanded.delete(attributeId);
    } else {
      newExpanded.add(attributeId);
    }
    setExpandedRows(newExpanded);
  };

  const getUnmappedAttributes = () => {
    if (!pdeMappings || !Array.isArray(pdeMappings)) {
      return attributes;
    }
    const mappedAttributeIds = new Set(pdeMappings.map(m => m.attribute_id));
    return attributes.filter(attr => !mappedAttributeIds.has(attr.attribute_id));
  };

  const getMappingTypeIcon = (type: string) => {
    const mapping = mappingTypes.find(t => t.value === type);
    return mapping?.icon || <LinkIcon />;
  };

  // Removed approval-related functions as they are no longer needed

  const getConfidenceColor = (score?: number) => {
    if (!score) return 'default';
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Map Physical Data Elements (PDEs)</Typography>
        <Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setDialogOpen(true)}
            sx={{ mr: 2 }}
            disabled={getUnmappedAttributes().length === 0}
          >
            Map PDE
          </Button>
        </Box>
      </Box>

      {/* No tabs needed since we removed Review & Approval */}
        <>
          {/* Instructions */}
          <Alert severity="info" sx={{ mb: 3 }}>
            Map report attributes to database columns. Simply select the data source, table, and column for each attribute.
            You can map multiple attributes at once using the bulk mapping feature.
          </Alert>

          {/* Progress */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="subtitle1">Mapping Progress</Typography>
                <Typography variant="body2" color="textSecondary">
                  {pdeMappings?.length || 0} of {attributes.length} attributes mapped
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={attributes.length > 0 ? ((pdeMappings?.length || 0) / attributes.length) * 100 : 0} 
              />
              
              {/* Show job progress inline */}
              {jobProgress && jobProgress.status !== 'completed' && jobProgress.status !== 'failed' && (
                <Box mt={2} p={2} bgcolor="primary.light" borderRadius={1}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="subtitle2" color="primary.contrastText">
                      Auto-Mapping in Progress
                    </Typography>
                    <Typography variant="body2" color="primary.contrastText">
                      {jobProgress.progress_percentage || 0}%
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={jobProgress.progress_percentage || 0}
                    sx={{ mb: 1, backgroundColor: 'rgba(255,255,255,0.3)' }}
                  />
                  <Typography variant="body2" color="primary.contrastText">
                    {jobProgress.message || 'Processing...'}
                  </Typography>
                  {jobProgress.current_step && (
                    <Typography variant="caption" color="primary.contrastText" display="block" mt={0.5}>
                      Step: {jobProgress.current_step}
                    </Typography>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Removed duplicate job progress section */}

          {/* Bulk Mapping Component */}
          <BulkPDEMapping
            cycleId={cycleId!}
            reportId={reportId!}
            attributes={Array.isArray(attributes) ? attributes : []}
            dataSources={Array.isArray(dataSources) ? dataSources : []}
            existingMappings={Array.isArray(pdeMappings) ? pdeMappings : []}
            onMappingsCreated={loadData}
          />

          {/* Existing Mappings Table */}
          {pdeMappings && pdeMappings.length > 0 && (
            <>
              <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mt: 4, mb: 2 }}>
                <Typography variant="h6">Existing Mappings</Typography>
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<RefreshIcon />}
                  onClick={handleRegenerateAllMappings}
                  disabled={regeneratingAll}
                >
                  {regeneratingAll ? 'Regenerating...' : 'Regenerate All Mappings'}
                </Button>
              </Box>
              <TableContainer component={Paper} sx={{ overflowX: 'auto' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ width: '4%' }}>Line #</TableCell>
                      <TableCell sx={{ width: '10%' }}>Attribute Name</TableCell>
                      <TableCell sx={{ width: '14%' }}>Description</TableCell>
                      <TableCell sx={{ width: '5%' }}>MDRM</TableCell>
                      <TableCell sx={{ width: '7%' }}>Data Type</TableCell>
                      <TableCell sx={{ width: '7%' }}>Mandatory</TableCell>
                      <TableCell sx={{ width: '10%' }}>Table</TableCell>
                      <TableCell sx={{ width: '10%' }}>Column</TableCell>
                      <TableCell align="center" sx={{ width: '7%' }}>Confidence</TableCell>
                      <TableCell sx={{ width: '10%' }}>Classification</TableCell>
                      <TableCell align="center" sx={{ width: '5%' }}>Risk</TableCell>
                      <TableCell align="center" sx={{ width: '6%' }}>Status</TableCell>
                      <TableCell align="right" sx={{ width: '5%' }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(pdeMappings || [])
                      .sort((a, b) => {
                        // The mapping objects already contain all attribute fields
                        
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
                      })
                      .map((mapping) => {
                        // The mapping object already contains all attribute fields from the API
                        const dataSource = dataSources.find(ds => ds.id === mapping.data_source_id);
                        
                        return (
                        <TableRow key={mapping.id} hover>
                          <TableCell sx={{ width: '4%' }}>
                            <Typography variant="body2" fontFamily="monospace" fontSize="0.8rem">
                              {mapping.line_item_number || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell sx={{ width: '10%' }}>
                            <Box>
                              <Typography variant="body2" fontWeight="medium" fontSize="0.8rem" sx={{ wordBreak: 'break-word' }}>
                                {mapping.attribute_name}
                              </Typography>
                              <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                {mapping.cde_flag && (
                                  <Chip size="small" label="CDE" color="warning" sx={{ height: '18px', fontSize: '0.7rem' }} />
                                )}
                                {mapping.is_primary_key && (
                                  <Chip size="small" label="PK" color="info" sx={{ height: '18px', fontSize: '0.7rem' }} />
                                )}
                                {mapping.historical_issues_flag && (
                                  <Chip size="small" label="Issues" color="error" sx={{ height: '18px', fontSize: '0.7rem' }} />
                                )}
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell sx={{ width: '14%' }}>
                            <Typography variant="body2" fontSize="0.8rem" sx={{ wordBreak: 'break-word' }}>
                              {mapping.description || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell sx={{ width: '5%' }}>
                            <Typography variant="body2" fontFamily="monospace" fontSize="0.8rem">
                              {mapping.mdrm || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell sx={{ width: '7%' }}>
                            <Typography variant="body2" fontSize="0.8rem">
                              {mapping.data_type || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell sx={{ width: '7%' }}>
                            <Chip
                              size="small"
                              label={mapping.mandatory_flag || 'Optional'}
                              color={
                                mapping.mandatory_flag === 'Mandatory' ? 'error' :
                                mapping.mandatory_flag === 'Conditional' ? 'warning' :
                                'default'
                              }
                              variant="outlined"
                              sx={{ fontSize: '0.7rem' }}
                            />
                          </TableCell>
                          <TableCell sx={{ width: '10%' }}>
                            <Typography variant="body2" fontFamily="monospace" fontSize="0.8rem" sx={{ wordBreak: 'break-word' }}>
                              {mapping.source_table || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell sx={{ width: '10%' }}>
                            <Typography variant="body2" fontFamily="monospace" fontSize="0.8rem" sx={{ wordBreak: 'break-word' }}>
                              {mapping.source_column || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell align="center" sx={{ width: '7%' }}>
                            {mapping.llm_confidence_score !== null && mapping.llm_confidence_score !== undefined ? (
                              <Chip
                                label={`${mapping.llm_confidence_score}%`}
                                size="small"
                                color={getConfidenceColor(mapping.llm_confidence_score) as any}
                                sx={{ fontWeight: 'bold', fontSize: '0.7rem' }}
                              />
                            ) : (
                              <Typography variant="body2" color="textSecondary" fontSize="0.8rem">-</Typography>
                            )}
                          </TableCell>
                          <TableCell sx={{ width: '10%' }}>
                            {mapping.information_security_classification ? (
                              <Chip
                                label={mapping.information_security_classification}
                                size="small"
                                variant="outlined"
                                color={
                                  mapping.information_security_classification === 'HRCI' ? 'error' :
                                  mapping.information_security_classification === 'Confidential' ? 'warning' :
                                  mapping.information_security_classification === 'Proprietary' ? 'info' :
                                  'default'
                                }
                                sx={{ fontSize: '0.7rem' }}
                              />
                            ) : (
                              <Typography variant="body2" color="textSecondary" fontSize="0.8rem">-</Typography>
                            )}
                          </TableCell>
                          <TableCell align="center" sx={{ width: '5%' }}>
                            {mapping.risk_level ? (
                              <Chip
                                label={mapping.risk_level}
                                size="small"
                                color={
                                  mapping.risk_level === 'High' ? 'error' :
                                  mapping.risk_level === 'Medium' ? 'warning' :
                                  'success'
                                }
                                sx={{ fontSize: '0.7rem' }}
                              />
                            ) : (
                              <Typography variant="body2" color="textSecondary" fontSize="0.8rem">-</Typography>
                            )}
                          </TableCell>
                          <TableCell align="center" sx={{ width: '6%' }}>
                            <Chip
                              label="Mapped"
                              size="small"
                              color="success"
                              icon={<CheckCircleIcon sx={{ fontSize: 14 }} />}
                              sx={{ fontSize: '0.7rem' }}
                            />
                          </TableCell>
                          <TableCell align="right" sx={{ width: '5%' }}>
                            <Box display="flex" justifyContent="flex-end" gap={0.25}>
                              <Tooltip title="Regenerate mapping">
                                <IconButton 
                                  onClick={() => handleRegenerateMapping(mapping)} 
                                  size="small" 
                                  color="primary"
                                  disabled={regeneratingMappingId === mapping.id}
                                  sx={{ padding: 0.5 }}
                                >
                                  {regeneratingMappingId === mapping.id ? (
                                    <CircularProgress size={16} />
                                  ) : (
                                    <RefreshIcon sx={{ fontSize: 18 }} />
                                  )}
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Edit mapping">
                                <IconButton onClick={() => handleEdit(mapping)} size="small" sx={{ padding: 0.5 }}>
                                  <EditIcon sx={{ fontSize: 18 }} />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Delete mapping">
                                <IconButton onClick={() => handleDelete(mapping.id)} size="small" color="error" sx={{ padding: 0.5 }}>
                                  <DeleteIcon sx={{ fontSize: 18 }} />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </TableCell>
                        </TableRow>
                        );
                      })}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </>

      {/* Simplified Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit PDE Mapping</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                Map <strong>{editingMapping?.attribute_name || 'attribute'}</strong> to a database column
              </Alert>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth required>
                <InputLabel>Data Source</InputLabel>
                <Select
                  value={formData.data_source_id || ''}
                  onChange={(e) => handleInputChange('data_source_id', e.target.value || null)}
                  label="Data Source"
                >
                  <MenuItem value="">Select a data source</MenuItem>
                  {dataSources.map((ds) => (
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
                value={formData.source_field}
                onChange={(e) => handleInputChange('source_field', e.target.value)}
                placeholder="schema.table_name.column_name"
                helperText="Enter the fully qualified column name (e.g., public.customers.customer_id)"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDialogOpen(false); resetForm(); }}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleSubmit}
            disabled={!formData.data_source_id || !formData.source_field}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notifications */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
      >
        <Alert severity="success" onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};