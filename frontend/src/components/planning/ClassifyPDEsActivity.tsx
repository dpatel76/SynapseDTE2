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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Checkbox,
  RadioGroup,
  Radio,
  Badge,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Shield as ShieldIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  ExpandMore as ExpandMoreIcon,
  Psychology as PsychologyIcon,
  Assignment as AssignmentIcon,
  Gavel as GavelIcon,
  Lock as LockIcon,
  Public as PublicIcon,
  Business as BusinessIcon,
  PersonPin as PersonPinIcon,
  HighlightOff as HighlightOffIcon,
  Info as InfoIcon,
  AutoFixHigh as AutoFixHighIcon,
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';

interface PDEMapping {
  pde_mapping_id: number;
  pde_name: string;
  pde_code: string;
  attribute_name: string;
  line_item_number?: string;
  technical_line_item_name?: string;
  description?: string;
  mdrm?: string;
  data_type?: string;
  mandatory_flag?: string;
  cde_flag?: boolean;
  is_primary_key?: boolean;
  historical_issues_flag?: boolean;
  regulatory_flag: boolean;
  pii_flag: boolean;
  information_security_classification?: string;
  classification_count: number;
  is_classified: boolean;
  // Additional fields for enhanced table
  data_source?: string;
  table_name?: string;
  column_name?: string;
  llm_confidence_score?: number;
  llm_classification_confidence?: number;
}

interface LLMClassificationSuggestion {
  pde_mapping_id: number;
  pde_name: string;
  llm_suggested_information_security_classification: string;
  llm_regulatory_references: string[];
  llm_classification_rationale: string;
  regulatory_flag: boolean;
  pii_flag: boolean;
  evidence: any;
  security_controls?: any;
}

interface PDEClassificationDetail {
  id: number;
  pde_mapping_id: number;
  classification_type: string;
  classification_value: string;
  classification_reason?: string;
  evidence_type?: string;
  evidence_reference?: string;
  evidence_details?: any;
  classified_by?: number;
  reviewed_by?: number;
  approved_by?: number;
  review_status?: string;
  review_notes?: string;
  created_at: string;
  updated_at: string;
}



const informationSecurityClassifications = [
  { value: 'HRCI', label: 'HRCI', icon: <LockIcon />, color: '#d32f2f', description: 'Highly Restricted Confidential Information' },
  { value: 'Confidential', label: 'Confidential', icon: <SecurityIcon />, color: '#f57c00', description: 'Confidential business information' },
  { value: 'Proprietary', label: 'Proprietary', icon: <BusinessIcon />, color: '#1976d2', description: 'Proprietary company information' },
  { value: 'Public', label: 'Public', icon: <PublicIcon />, color: '#388e3c', description: 'Public information' },
];

interface ClassifyPDEsActivityProps {
  cycleId?: string;
  reportId?: string;
}

export const ClassifyPDEsActivity: React.FC<ClassifyPDEsActivityProps> = (props) => {
  const params = useParams<{ cycleId: string; reportId: string }>();
  const cycleId = props.cycleId || params.cycleId;
  const reportId = props.reportId || params.reportId;
  const auth = useAuth();
  const [pdeMappings, setPdeMappings] = useState<PDEMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedMapping, setSelectedMapping] = useState<PDEMapping | null>(null);
  const [llmSuggestion, setLlmSuggestion] = useState<LLMClassificationSuggestion | null>(null);
  const [loadingLLM, setLoadingLLM] = useState(false);
  const [expandedAccordion, setExpandedAccordion] = useState<string | false>(false);
  const [jobProgress, setJobProgress] = useState<any>(null);
  
  // Polling interval reference
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    pde_mapping_id: 0,
    classification_type: 'information_security',
    classification_value: '',
    classification_reason: '',
    regulatory_flag: false,
    pii_flag: false,
    information_security_classification: '',
    llm_classification_rationale: '',
    llm_regulatory_references: [],
    evidence_type: '',
    evidence_reference: '',
    evidence_details: {},
  });

  // Load PDE mappings
  const loadPDEMappings = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(
        `/planning/cycles/${cycleId}/reports/${reportId}/pde-classifications`
      );
      setPdeMappings(response.data);
    } catch (err) {
      console.error('Error loading PDE mappings:', err);
      setError('Failed to load PDE mappings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPDEMappings();
    checkForActiveJobs();
  }, [cycleId, reportId]);

  // Check for active classification jobs
  const checkForActiveJobs = async () => {
    try {
      console.log('Checking for active classification jobs...');
      const response = await apiClient.get('/jobs/active');
      const activeJobs = response.data.active_jobs || [];
      console.log('Active jobs response:', activeJobs);
      
      // Find any active PDE classification job for this cycle/report
      const activeClassificationJob = activeJobs.find((job: any) => 
        job.job_type === 'pde_classification' && 
        job.metadata?.cycle_id === parseInt(cycleId!) &&
        job.metadata?.report_id === parseInt(reportId!) &&
        (job.status === 'pending' || job.status === 'running')
      );
      
      if (activeClassificationJob) {
        console.log('Found active PDE classification job:', activeClassificationJob);
        const jobId = activeClassificationJob.job_id || activeClassificationJob.id;
        if (jobId) {
          pollJobStatus(jobId);
        }
      }
    } catch (error) {
      console.error('Error checking for active jobs:', error);
    }
  };

  // Poll job status
  const pollJobStatus = (jobId: string) => {
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
          setSuccess(`Classification completed! ${jobData.result?.classified_count || 0} PDEs classified.`);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          loadPDEMappings(); // Reload to show new classifications
        } else if (jobData.status === 'failed') {
          setError(`Classification failed: ${jobData.error || 'Unknown error'}`);
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

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleGetLLMSuggestion = async (mapping: PDEMapping) => {
    try {
      setLoadingLLM(true);
      const token = localStorage.getItem('token');
      const response = await apiClient.post(
        `/planning/cycles/${cycleId}/reports/${reportId}/pde-classifications/suggest`,
        {},
        {
          params: { pde_mapping_id: mapping.pde_mapping_id },
          timeout: 120000 // 2 minutes timeout for LLM processing
        }
      );
      
      // Response is a single object, not an array
      const suggestion = response.data;
      setLlmSuggestion(suggestion);
      
      // Auto-fill form with suggestion
      setFormData(prev => ({
        ...prev,
        pde_mapping_id: mapping.pde_mapping_id,
        regulatory_flag: suggestion.regulatory_flag,
        pii_flag: suggestion.pii_flag,
        information_security_classification: suggestion.llm_suggested_information_security_classification,
        llm_classification_rationale: suggestion.llm_classification_rationale,
        llm_regulatory_references: suggestion.llm_regulatory_references,
        classification_reason: suggestion.llm_classification_rationale,
      }));
    } catch (err) {
      console.error('Error getting LLM suggestion:', err);
      setError('Failed to get AI classification suggestions');
    } finally {
      setLoadingLLM(false);
    }
  };

  const handleClassify = (mapping: PDEMapping) => {
    setSelectedMapping(mapping);
    setFormData(prev => ({
      ...prev,
      pde_mapping_id: mapping.pde_mapping_id,
      regulatory_flag: mapping.regulatory_flag,
      pii_flag: mapping.pii_flag,
      information_security_classification: mapping.information_security_classification || '',
    }));
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const token = localStorage.getItem('token');
      // Update the classification
      const classificationData = {
        ...formData,
        classification_type: 'comprehensive',
        classification_value: formData.information_security_classification,
      };
      
      await apiClient.post(
        `/planning/cycles/${cycleId}/reports/${reportId}/pde-classifications`,
        classificationData
      );
      
      setSuccess('PDE classification saved successfully');
      setDialogOpen(false);
      resetForm();
      loadPDEMappings();
    } catch (err: any) {
      console.error('Error saving classification:', err);
      setError(err.response?.data?.detail || 'Failed to save classification');
    }
  };

  const handleCompleteActivity = async () => {
    try {
      await apiClient.post(`/activity-management/activities/classify_pdes/complete`, {
        cycle_id: cycleId,
        report_id: reportId,
        phase_name: 'Planning'
      });
      setSuccess('Activity completed successfully');
      // Optionally redirect or update parent component
    } catch (err: any) {
      console.error('Error completing activity:', err);
      setError(err.response?.data?.detail || 'Failed to complete activity');
    }
  };

  const resetForm = () => {
    setFormData({
      pde_mapping_id: 0,
      classification_type: 'information_security',
      classification_value: '',
      classification_reason: '',
      regulatory_flag: false,
      pii_flag: false,
      information_security_classification: '',
      llm_classification_rationale: '',
      llm_regulatory_references: [],
      evidence_type: '',
      evidence_reference: '',
      evidence_details: {},
    });
    setSelectedMapping(null);
    setLlmSuggestion(null);
  };

  const getClassifiedCount = () => {
    return pdeMappings.filter(m => m.is_classified).length;
  };

  // Sort PDEs following the same order as report attributes
  const getSortedPDEMappings = () => {
    return [...pdeMappings].sort((a, b) => {
      // 1. Primary Keys first
      if (a.is_primary_key && !b.is_primary_key) return -1;
      if (!a.is_primary_key && b.is_primary_key) return 1;
      
      // 2. Then CDE flags
      if (a.cde_flag && !b.cde_flag) return -1;
      if (!a.cde_flag && b.cde_flag) return 1;
      
      // 3. Then Historical Issues
      if (a.historical_issues_flag && !b.historical_issues_flag) return -1;
      if (!a.historical_issues_flag && b.historical_issues_flag) return 1;
      
      // 4. Finally by Line Item # (extract number from string like "Line Item 1")
      const getLineNumber = (lineItem: string) => {
        const match = lineItem?.match(/\d+/);
        return match ? parseInt(match[0]) : 999999;
      };
      
      const lineA = getLineNumber(a.line_item_number || '');
      const lineB = getLineNumber(b.line_item_number || '');
      
      return lineA - lineB;
    });
  };



  const handleAccordionChange = (panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedAccordion(isExpanded ? panel : false);
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
        <Typography variant="h5">Classify Physical Data Elements</Typography>
        <Button
          variant="contained"
          color="success"
          startIcon={<CheckCircleIcon />}
          onClick={handleCompleteActivity}
          disabled={getClassifiedCount() === 0}
        >
          Complete Activity
        </Button>
      </Box>

      {/* Instructions */}
      <Alert severity="info" sx={{ mb: 3 }}>
        Classify Physical Data Elements based on information security requirements and regulatory compliance. 
        AI will assist in identifying security-sensitive and compliance-critical elements. Each PDE should 
        be classified based on its data sensitivity and regulatory requirements.
      </Alert>

      {/* Progress */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="subtitle1">Classification Progress</Typography>
            <Typography variant="body2" color="textSecondary">
              {getClassifiedCount()} of {pdeMappings.length} PDEs classified
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={pdeMappings.length > 0 ? (getClassifiedCount() / pdeMappings.length) * 100 : 0} 
          />
        </CardContent>
      </Card>

      {/* Job Progress */}
      {jobProgress && jobProgress.status !== 'completed' && jobProgress.status !== 'failed' && (
        <Card sx={{ mb: 3, bgcolor: 'primary.light' }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="subtitle2" color="primary.contrastText">
                Classification in Progress
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
          </CardContent>
        </Card>
      )}

      {/* Security Classification Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <HighlightOffIcon color="error" />
                <Typography variant="h6">
                  {pdeMappings.filter(m => m.information_security_classification === 'HRCI').length}
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary">
                HRCI
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <ShieldIcon color="warning" />
                <Typography variant="h6">
                  {pdeMappings.filter(m => m.information_security_classification === 'Confidential').length}
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary">
                Confidential
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <GavelIcon color="info" />
                <Typography variant="h6">
                  {pdeMappings.filter(m => m.information_security_classification === 'Proprietary').length}
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary">
                Proprietary
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1}>
                <PersonPinIcon color="success" />
                <Typography variant="h6">
                  {pdeMappings.filter(m => m.information_security_classification === 'Public').length}
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary">
                Public
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Generate Classification Button */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={16} /> : <AutoFixHighIcon />}
          onClick={async () => {
            setLoading(true);
            try {
              // Use the batch classification endpoint
              const response = await apiClient.post(
                `/planning/cycles/${cycleId}/reports/${reportId}/pde-classifications/suggest-batch`,
                {},
                {
                  timeout: 300000 // 5 minutes timeout for bulk LLM processing
                }
              );
              
              if (response.data.mappings_to_process === 0) {
                setSuccess('No unclassified PDEs found');
              } else {
                setSuccess(`Started bulk classification for ${response.data.mappings_to_process} PDEs.`);
                
                // Start polling for job progress
                if (response.data.job_id) {
                  pollJobStatus(response.data.job_id);
                }
              }
            } catch (err) {
              console.error('Error in bulk classification:', err);
              setError('Failed to start bulk classification');
            } finally {
              setLoading(false);
            }
          }}
          disabled={pdeMappings.filter(m => !m.is_classified).length === 0 || loading}
        >
          {loading ? 'Processing... (up to 5 min)' : 'Generate Classifications for All'}
        </Button>
      </Box>

      {/* PDEs Table */}
      {pdeMappings.length > 0 ? (
        <TableContainer component={Paper} sx={{ overflowX: 'auto' }}>
          <Table size="small" sx={{ minWidth: 2000 }}>
            <TableHead>
              <TableRow>
                <TableCell>Line Item #</TableCell>
                <TableCell>Attribute Name</TableCell>
                <TableCell>Data Source</TableCell>
                <TableCell>Table</TableCell>
                <TableCell>Column</TableCell>
                <TableCell>MDRM</TableCell>
                <TableCell>Data Type</TableCell>
                <TableCell>Mandatory</TableCell>
                <TableCell>Classification</TableCell>
                <TableCell>Classification Confidence</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {getSortedPDEMappings().map((mapping: any) => (
                <TableRow key={mapping.pde_mapping_id}>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {mapping.line_item_number || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {mapping.attribute_name}
                      </Typography>
                      <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5 }}>
                        {mapping.cde_flag && (
                          <Chip size="small" label="CDE" color="warning" sx={{ height: '20px' }} />
                        )}
                        {mapping.is_primary_key && (
                          <Chip size="small" label="PK" color="info" sx={{ height: '20px' }} />
                        )}
                        {mapping.historical_issues_flag && (
                          <Chip size="small" label="Issues" color="error" sx={{ height: '20px' }} />
                        )}
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {mapping.data_source || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {mapping.table_name || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {mapping.column_name || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {mapping.mdrm || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {mapping.data_type || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={mapping.mandatory_flag || 'Optional'}
                      color={
                        mapping.mandatory_flag === 'Mandatory' ? 'error' :
                        mapping.mandatory_flag === 'Conditional' ? 'warning' :
                        'default'
                      }
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                      <Select
                        value={mapping.information_security_classification || ''}
                        onChange={async (e) => {
                          // Update classification directly
                          const classificationData = {
                            pde_mapping_id: mapping.pde_mapping_id,
                            classification_type: 'information_security',
                            classification_value: e.target.value,
                            classification_reason: 'Manual information security classification',
                            information_security_classification: e.target.value,
                            regulatory_flag: mapping.regulatory_flag,
                            pii_flag: mapping.pii_flag,
                          };
                          
                          try {
                            const token = localStorage.getItem('token');
                            await apiClient.post(
                              `/planning/cycles/${cycleId}/reports/${reportId}/pde-classifications`,
                              classificationData
                            );
                            await loadPDEMappings();
                            setSuccess('Information security classification updated');
                          } catch (err) {
                            console.error('Error updating classification:', err);
                            setError('Failed to update classification');
                          }
                        }}
                        displayEmpty
                        size="small"
                      >
                        <MenuItem value="">
                          <em>Not classified</em>
                        </MenuItem>
                        <MenuItem value="HRCI">HRCI</MenuItem>
                        <MenuItem value="Confidential">Confidential</MenuItem>
                        <MenuItem value="Proprietary">Proprietary</MenuItem>
                        <MenuItem value="Public">Public</MenuItem>
                      </Select>
                    </FormControl>
                  </TableCell>
                  <TableCell>
                    {mapping.is_classified && mapping.llm_classification_confidence ? (
                      <Chip
                        size="small"
                        label={`${mapping.llm_classification_confidence}%`}
                        color={
                          mapping.llm_classification_confidence >= 90 ? 'success' :
                          mapping.llm_classification_confidence >= 70 ? 'warning' :
                          'error'
                        }
                        variant="outlined"
                      />
                    ) : (
                      <Typography variant="body2" color="textSecondary">-</Typography>
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <Button
                      size="small"
                      variant={mapping.is_classified ? "outlined" : "contained"}
                      onClick={() => handleClassify(mapping)}
                    >
                      {mapping.is_classified ? 'Review' : 'Classify'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="textSecondary">
            No PDE mappings found. Please complete the Map PDEs activity first.
          </Typography>
        </Paper>
      )}

      {/* Classification Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              Classify PDE: {selectedMapping?.pde_name}
            </Typography>
            {selectedMapping && (
              <Button
                variant="outlined"
                startIcon={loadingLLM ? <CircularProgress size={16} /> : <AutoFixHighIcon />}
                onClick={() => handleGetLLMSuggestion(selectedMapping)}
                disabled={loadingLLM}
                size="small"
              >
                {loadingLLM ? 'Analyzing... (up to 2 min)' : 'Get AI Suggestions'}
              </Button>
            )}
          </Box>
        </DialogTitle>
        <DialogContent>
          {/* AI Suggestion Alert */}
          {llmSuggestion && (
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                AI Classification Suggestions:
              </Typography>
              <Typography variant="body2">
                {llmSuggestion.llm_classification_rationale}
              </Typography>
            </Alert>
          )}

          <Grid container spacing={3}>
            {/* Information Security Classification */}
            <Grid size={{ xs: 12 }}>
              <Typography variant="subtitle1" gutterBottom>
                Information Security Classification
              </Typography>
              <RadioGroup
                value={formData.information_security_classification}
                onChange={(e) => handleInputChange('information_security_classification', e.target.value)}
              >
                {informationSecurityClassifications.map((classification) => (
                  <FormControlLabel
                    key={classification.value}
                    value={classification.value}
                    control={<Radio />}
                    label={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Box color={classification.color}>
                          {classification.icon}
                        </Box>
                        <Box>
                          <Typography>{classification.label}</Typography>
                          <Typography variant="caption" color="textSecondary">
                            {classification.description}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                ))}
              </RadioGroup>
            </Grid>

            <Divider />

            {/* Compliance Flags */}
            <Grid size={{ xs: 12 }}>
              <Typography variant="subtitle1" gutterBottom>
                Compliance & Data Sensitivity
              </Typography>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.regulatory_flag}
                    onChange={(e) => handleInputChange('regulatory_flag', e.target.checked)}
                  />
                }
                label={
                  <Box display="flex" alignItems="center" gap={1}>
                    <GavelIcon />
                    <Typography>Subject to Regulatory Requirements</Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.pii_flag}
                    onChange={(e) => handleInputChange('pii_flag', e.target.checked)}
                  />
                }
                label={
                  <Box display="flex" alignItems="center" gap={1}>
                    <PersonPinIcon />
                    <Typography>Contains Personally Identifiable Information (PII)</Typography>
                  </Box>
                }
              />
            </Grid>

            {/* Classification Reason */}
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Classification Rationale"
                multiline
                rows={3}
                value={formData.classification_reason}
                onChange={(e) => handleInputChange('classification_reason', e.target.value)}
                helperText="Explain the reasoning behind this classification"
              />
            </Grid>

            {/* Evidence Section */}
            <Grid size={{ xs: 12 }}>
              <Accordion expanded={expandedAccordion === 'evidence'} onChange={handleAccordionChange('evidence')}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>Supporting Evidence (Optional)</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <FormControl fullWidth>
                        <InputLabel>Evidence Type</InputLabel>
                        <Select
                          value={formData.evidence_type}
                          onChange={(e) => handleInputChange('evidence_type', e.target.value)}
                          label="Evidence Type"
                        >
                          <MenuItem value="">None</MenuItem>
                          <MenuItem value="regulation">Regulation</MenuItem>
                          <MenuItem value="policy">Company Policy</MenuItem>
                          <MenuItem value="historical_issue">Historical Issue</MenuItem>
                          <MenuItem value="business_rule">Business Rule</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <TextField
                        fullWidth
                        label="Evidence Reference"
                        value={formData.evidence_reference}
                        onChange={(e) => handleInputChange('evidence_reference', e.target.value)}
                        placeholder="e.g., GDPR Article 9, SOX Section 404"
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>

            {/* Regulatory References from LLM */}
            {formData.llm_regulatory_references && formData.llm_regulatory_references.length > 0 && (
              <Grid size={{ xs: 12 }}>
                <Alert severity="info">
                  <Typography variant="subtitle2" gutterBottom>
                    AI Identified Regulations:
                  </Typography>
                  <List dense>
                    {formData.llm_regulatory_references.map((ref, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <GavelIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText primary={ref} />
                      </ListItem>
                    ))}
                  </List>
                </Alert>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDialogOpen(false); resetForm(); }}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleSubmit}
            disabled={!formData.information_security_classification}
          >
            Save Classification
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