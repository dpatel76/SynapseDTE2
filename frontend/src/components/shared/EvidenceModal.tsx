import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  IconButton,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Tabs,
  Tab,
  Link,
} from '@mui/material';
import {
  Description as DocumentIcon,
  Storage as DatabaseIcon,
  History as HistoryIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Close as CloseIcon,
  Person as PersonIcon,
  CalendarToday as CalendarIcon,
} from '@mui/icons-material';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { EvidenceValidationResults } from './EvidenceValidationResults';

interface EvidenceDetails {
  id: number;
  version_number: number;
  evidence_type: 'document' | 'data_source';
  is_current: boolean;
  submitted_at: string;
  submitted_by_name?: string;
  submission_notes?: string;
  validation_status: 'pending' | 'passed' | 'failed' | 'partial' | 'valid';
  validation_notes?: string;
  validated_at?: string;
  validated_by_name?: string;
  tester_decision?: 'approved' | 'rejected' | 'needs_revision';
  tester_notes?: string;
  decided_at?: string;
  decided_by_name?: string;
  // Document specific
  original_filename?: string;
  file_size_bytes?: number;
  file_path?: string;
  // Query specific
  data_source_id?: string;
  data_source_name?: string;
  query_text?: string;
  query_parameters?: any;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`evidence-tabpanel-${index}`}
      aria-labelledby={`evidence-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
}

interface EvidenceModalProps {
  open: boolean;
  onClose: () => void;
  testCaseId: string;
  testCaseData?: any; // Optional test case data for showing sample values
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({
  open,
  onClose,
  testCaseId,
  testCaseData: initialTestCaseData,
}) => {
  const { user } = useAuth();
  const isDataOwner = user?.role === 'Data Owner';
  const isTester = user?.role === 'Tester';
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [evidenceList, setEvidenceList] = useState<EvidenceDetails[]>([]);
  const [testCase, setTestCase] = useState<any>(initialTestCaseData || null);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    if (open && testCaseId) {
      fetchEvidenceDetails();
      if (!initialTestCaseData) {
        fetchTestCaseDetails();
      }
    }
  }, [open, testCaseId]);

  const fetchEvidenceDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      // For testers, use the evidence-details endpoint which has better formatting
      const endpoint = isTester 
        ? `/request-info/test-cases/${testCaseId}/evidence-details`
        : `/request-info/test-cases/${testCaseId}/evidence`;
      
      const response = await apiClient.get(endpoint);
      const data = response.data;
      console.log('Evidence data received:', data);
      
      // Handle both legacy document submissions and new evidence
      const allEvidence: EvidenceDetails[] = [];
      
      // If tester endpoint, extract test case data and current evidence
      if (isTester && data.test_case) {
        console.log('Tester test case data:', data.test_case);
        console.log('Primary key attributes from API:', data.test_case.primary_key_attributes);
        setTestCase(data.test_case);
        const evidenceArray = data.current_evidence || [];
        evidenceArray.forEach((e: any) => {
          console.log('Processing evidence item:', e);
          allEvidence.push({
            id: e.id || e.evidence_id,
            version_number: e.version_number || e.submission_number || 1,
            evidence_type: e.evidence_type,
            is_current: true, // current_evidence only contains current items
            submitted_at: e.submitted_at,
            submitted_by_name: e.submitted_by_name,
            submission_notes: e.submission_notes,
            validation_status: e.validation_status || 'pending',
            validation_notes: e.validation_notes,
            validated_at: e.validated_at,
            validated_by_name: e.validated_by_name,
            tester_decision: e.tester_decision,
            tester_notes: e.tester_notes,
            decided_at: e.decided_at,
            decided_by_name: e.decided_by_name,
            original_filename: e.original_filename,
            file_size_bytes: e.file_size_bytes,
            file_path: e.file_path,
            data_source_id: e.data_source_id,
            data_source_name: e.data_source_name,
            query_text: e.query_text,
            query_parameters: e.query_parameters,
          });
        });
      } else {
        // Check if response is an array (List endpoint) or object with evidence property (Dict endpoint)
        let evidenceArray = [];
        if (Array.isArray(data)) {
          evidenceArray = data;
        } else if (data.evidence && Array.isArray(data.evidence)) {
          evidenceArray = data.evidence;
        }
        
        // Add new RFI evidence
        if (evidenceArray.length > 0) {
          evidenceArray.forEach((e: any) => {
            console.log('Processing evidence item:', e);
            allEvidence.push({
              id: e.id || e.evidence_id,
              version_number: e.version_number || e.submission_number || 1,
              evidence_type: e.evidence_type,
              is_current: e.is_current,
              submitted_at: e.submitted_at,
              submitted_by_name: e.submitted_by_name,
              submission_notes: e.submission_notes,
              validation_status: e.validation_status || 'pending',
              validation_notes: e.validation_notes,
              validated_at: e.validated_at,
              validated_by_name: e.validated_by_name,
              tester_decision: e.tester_decision,
              tester_notes: e.tester_notes,
              decided_at: e.decided_at,
              decided_by_name: e.decided_by_name,
              original_filename: e.original_filename,
              file_size_bytes: e.file_size_bytes,
              file_path: e.file_path,
              data_source_id: e.data_source_id,
              data_source_name: e.data_source_name,
              query_text: e.query_text,
              query_parameters: e.query_parameters,
            });
          });
        }
      }
      
      // Sort by version number descending (latest first)
      allEvidence.sort((a, b) => b.version_number - a.version_number);
      setEvidenceList(allEvidence);
    } catch (err: any) {
      console.error('Failed to fetch evidence details:', err);
      setError('Failed to load evidence details');
    } finally {
      setLoading(false);
    }
  };

  const fetchTestCaseDetails = async () => {
    try {
      // Skip if already loaded from evidence details
      if (testCase && !initialTestCaseData) {
        return;
      }
      
      // For data owner, try their specific endpoint
      if (isDataOwner) {
        const response = await apiClient.get('/request-info/data-owner/test-cases');
        const data = response.data;
        const testCases = data.test_cases || [];
        
        // Find the specific test case
        const foundTestCase = testCases.find((tc: any) => tc.test_case_id === testCaseId);
        if (foundTestCase) {
          console.log('Data owner test case data:', foundTestCase);
          console.log('Primary key attributes:', foundTestCase.primary_key_attributes);
          setTestCase(foundTestCase);
          return;
        }
      }
    } catch (err) {
      console.error('Failed to fetch test case details:', err);
      // Test case data is optional, so we don't set an error
    }
  };

  const getEvidenceIcon = (type: string) => {
    return type === 'document' ? <DocumentIcon /> : <DatabaseIcon />;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
      case 'approved':
        return <CheckIcon color="success" />;
      case 'failed':
      case 'rejected':
        return <ErrorIcon color="error" />;
      default:
        return <WarningIcon color="warning" />;
    }
  };

  const getStatusColor = (status: string): any => {
    switch (status) {
      case 'passed':
      case 'approved':
        return 'success';
      case 'failed':
      case 'rejected':
        return 'error';
      default:
        return 'warning';
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'N/A';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Always show only the current/latest evidence
  const filteredEvidence = evidenceList.filter(e => e.is_current);

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { 
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column'
        }
      }}
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Evidence Details</Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        ) : evidenceList.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No evidence submitted yet
            </Typography>
          </Box>
        ) : (
          <>
            {/* Test Case Info - Show for both roles but with different content */}
            {testCase && (
              <Paper elevation={0} sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Test Case Information
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Test Case</Typography>
                    <Typography variant="body2">{testCase.test_case_name}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Attribute</Typography>
                    <Typography variant="body2">{testCase.attribute_name}</Typography>
                  </Box>
                  {isTester && (
                    <Box>
                      <Typography variant="caption" color="text.secondary">Data Owner</Typography>
                      <Typography variant="body2">
                        {testCase.data_owner_name} ({testCase.data_owner_email})
                      </Typography>
                    </Box>
                  )}
                  <Box>
                    <Typography variant="caption" color="text.secondary">Status</Typography>
                    <Box>
                      <Chip 
                        label={testCase.status} 
                        size="small" 
                        color={testCase.status === 'Submitted' ? 'success' : 'warning'}
                      />
                    </Box>
                  </Box>
                </Box>
                {testCase.requires_revision && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    <Typography variant="body2" fontWeight="bold">Revision Required</Typography>
                    <Typography variant="body2">{testCase.revision_reason}</Typography>
                    {testCase.revision_deadline && (
                      <Typography variant="caption" color="text.secondary">
                        Deadline: {new Date(testCase.revision_deadline).toLocaleDateString()}
                      </Typography>
                    )}
                  </Alert>
                )}
                {testCase.special_instructions && (
                  <Box mt={2}>
                    <Typography variant="caption" color="text.secondary">Special Instructions</Typography>
                    <Typography variant="body2">{testCase.special_instructions}</Typography>
                  </Box>
                )}
              </Paper>
            )}

            {/* Tabs for Evidence Details */}
            <Tabs value={activeTab} onChange={handleTabChange}>
              <Tab label="Current Evidence" />
              <Tab label="Validation Results" />
              {isTester && <Tab label="Tester Decisions" />}
            </Tabs>

            <TabPanel value={activeTab} index={0}>
              {filteredEvidence.length > 0 ? (
                <Box>
                  {filteredEvidence.map((evidence, index) => (
                    <Box key={evidence.id} mb={3}>
                      <Box display="flex" alignItems="center" gap={1} mb={2}>
                        {evidence.evidence_type === 'document' ? (
                          <DocumentIcon color="primary" />
                        ) : (
                          <DatabaseIcon color="primary" />
                        )}
                        <Typography variant="subtitle2">
                          Evidence Type: {evidence.evidence_type} (Version {evidence.version_number})
                        </Typography>
                        {evidence.is_current && (
                          <Chip label="Current" size="small" color="primary" />
                        )}
                      </Box>
                      
                      {evidence.evidence_type === 'document' && evidence.original_filename && (
                        <List>
                          <ListItem>
                            <ListItemText 
                              primary="File Name" 
                              secondary={evidence.original_filename}
                            />
                          </ListItem>
                          {evidence.file_size_bytes && (
                            <ListItem>
                              <ListItemText 
                                primary="File Size" 
                                secondary={`${(evidence.file_size_bytes / 1024 / 1024).toFixed(2)} MB`}
                              />
                            </ListItem>
                          )}
                          <ListItem>
                            <ListItemText 
                              primary="Submitted By" 
                              secondary={evidence.submitted_by_name || 'Unknown'}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText 
                              primary="Submitted At" 
                              secondary={evidence.submitted_at ? new Date(evidence.submitted_at).toLocaleString() : 'Unknown'}
                            />
                          </ListItem>
                        </List>
                      )}
                      
                      {evidence.evidence_type === 'data_source' && evidence.query_text && (
                        <List>
                          <ListItem>
                            <ListItemText 
                              primary="Data Source" 
                              secondary={evidence.data_source_name || 'Query-based Evidence'}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText 
                              primary="Query" 
                              secondary={
                                <Box component="div">
                                  <Paper 
                                    elevation={0}
                                    sx={{ 
                                      p: 1, 
                                      bgcolor: 'grey.100',
                                      fontFamily: 'monospace',
                                      fontSize: '0.875rem',
                                      overflow: 'auto',
                                      maxHeight: 200
                                    }}
                                  >
                                    <pre style={{ margin: 0 }}>
                                      {evidence.query_text}
                                    </pre>
                                  </Paper>
                                </Box>
                              }
                              secondaryTypographyProps={{ component: 'div' }}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText 
                              primary="Submitted By" 
                              secondary={evidence.submitted_by_name || 'Unknown'}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText 
                              primary="Submitted At" 
                              secondary={evidence.submitted_at ? new Date(evidence.submitted_at).toLocaleString() : 'Unknown'}
                            />
                          </ListItem>
                        </List>
                      )}
                      
                      {evidence.tester_decision && (
                        <Alert 
                          severity={evidence.tester_decision === 'needs_revision' || evidence.tester_decision === 'rejected' ? 'warning' : 'info'}
                          sx={{ mt: 2 }}
                        >
                          <Typography variant="body2">
                            Tester Decision: {evidence.tester_decision}
                          </Typography>
                          {evidence.tester_notes && (
                            <Typography variant="body2">
                              Notes: {evidence.tester_notes}
                            </Typography>
                          )}
                        </Alert>
                      )}
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No evidence submitted yet
                </Typography>
              )}
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              {filteredEvidence.length > 0 && filteredEvidence[0] ? (
                <Box>
                  {/* Show validation results for the most recent evidence */}
                  {(() => {
                    console.log('Passing to EvidenceValidationResults:', {
                      evidenceId: filteredEvidence[0].id,
                      evidenceType: filteredEvidence[0].evidence_type,
                      testCaseId,
                      testCase,
                      testCasePrimaryKeys: testCase?.primary_key_attributes
                    });
                    return null;
                  })()}
                  <EvidenceValidationResults
                    key={`validation-${filteredEvidence[0].id}-${testCaseId}`}
                    evidenceId={filteredEvidence[0].id}
                    evidenceType={filteredEvidence[0].evidence_type}
                    testCaseId={testCaseId}
                    testCaseData={testCase}
                    queryText={filteredEvidence[0].query_text}
                    dataSourceName={filteredEvidence[0].data_source_name}
                  />
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No validation results available
                </Typography>
              )}
            </TabPanel>
            
            {isTester && (
              <TabPanel value={activeTab} index={2}>
                {/* TODO: Add tester decisions from the API */}
                <Typography variant="body2" color="text.secondary">
                  No tester decisions yet
                </Typography>
              </TabPanel>
            )}
          </>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default EvidenceModal;