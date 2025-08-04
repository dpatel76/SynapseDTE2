import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  Stack,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  ArrowBack as ArrowBackIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'react-hot-toast';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';

interface PendingAssignment {
  assignment_id: number;
  attribute_id: number;
  attribute_name: string;
  attribute_description: string;
  lob_name: string;
  status: string;
}

interface DataProvider {
  user_id: number;
  first_name: string;
  last_name: string;
  email: string;
  lob_name: string;
}

interface AssignmentSelection {
  attribute_id: number;
  data_owner_id: number | null;  // Match API field name
  assignment_notes: string;
}

const DataExecutiveAssignmentInterface: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [pendingAssignments, setPendingAssignments] = useState<PendingAssignment[]>([]);
  const [dataProviders, setDataProviders] = useState<DataProvider[]>([]);
  const [assignments, setAssignments] = useState<AssignmentSelection[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmDialog, setConfirmDialog] = useState(false);
  const [submissionNotes, setSubmissionNotes] = useState('');

  const cycleIdNum = cycleId ? parseInt(cycleId, 10) : 0;
  const reportIdNum = reportId ? parseInt(reportId, 10) : 0;
  
  const { data: unifiedPhaseStatus, isLoading: statusLoading, refetch: refetchStatus } = usePhaseStatus('Data Provider ID', cycleIdNum, reportIdNum);

  useEffect(() => {
    if (cycleIdNum && reportIdNum) {
      loadAssignmentData();
    }
  }, [cycleIdNum, reportIdNum]);

  const loadAssignmentData = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('[Data Executive Assignment] Loading assignment data...');
      
      // Load universal assignments for this cycle/report
      const assignmentsResponse = await apiClient.get('/universal-assignments/assignments', {
        params: {
          context_type_filter: 'Report,Attribute',
          assignment_type_filter: 'LOB Assignment',
          status_filter: 'Assigned,In Progress,Acknowledged',
          limit: 100
        }
      });
      
      // Log all assignments before filtering
      console.log('[Data Executive Assignment] All universal assignments:', assignmentsResponse.data);
      
      // Filter for this specific cycle/report
      const relevantAssignments = assignmentsResponse.data.filter((assignment: any) => {
        const matches = assignment.context_data?.cycle_id === cycleIdNum && 
                       assignment.context_data?.report_id === reportIdNum;
        console.log(`[Data Executive Assignment] Assignment ${assignment.assignment_id} - cycle: ${assignment.context_data?.cycle_id} (want ${cycleIdNum}), report: ${assignment.context_data?.report_id} (want ${reportIdNum}) - matches: ${matches}`);
        return matches;
      });
      
      // Get the assignment matrix which contains attribute-LOB combinations from sample data
      const matrixResponse = await apiClient.get(`/data-owner/cycles/${cycleIdNum}/reports/${reportIdNum}/assignment-matrix`);
      
      // Also get available data providers (users with Data Owner role)
      const usersResponse = await apiClient.get('/users', {
        params: {
          role: 'Data Owner',
          is_active: true
        }
      });
      
      console.log('[Data Executive Assignment] Relevant assignments:', relevantAssignments);
      console.log('[Data Executive Assignment] Assignment matrix:', matrixResponse.data);
      console.log('[Data Executive Assignment] Available data providers:', usersResponse.data);
      
      // Debug: Log the assigned_lobs for each attribute
      if (matrixResponse.data && matrixResponse.data.assignments) {
        matrixResponse.data.assignments.forEach((attr: any) => {
          console.log(`[Data Executive Assignment] Attribute ${attr.attribute_name} has LOBs:`, attr.assigned_lobs);
        });
      }
      
      // Extract pending assignments from assignment matrix
      const pending: PendingAssignment[] = [];
      
      console.log('[Data Executive Assignment] Creating pending assignments...');
      console.log('[Data Executive Assignment] Relevant assignments count:', relevantAssignments.length);
      
      // Check if we have relevant universal assignments (indicates CDO should assign data providers)
      if (relevantAssignments.length > 0) {
        const lobAssignment = relevantAssignments[0]; // Should be one LOB Assignment per report
        console.log('[Data Executive Assignment] Using LOB Assignment:', lobAssignment);
        
        // Get attributes from assignment matrix and create individual assignments for each attribute-LOB combination
        if (matrixResponse.data && matrixResponse.data.assignments) {
          console.log('[Data Executive Assignment] Total attributes in matrix:', matrixResponse.data.assignments.length);
          let attributesWithOwners = 0;
          let attributesWithoutOwners = 0;
          
          matrixResponse.data.assignments.forEach((attributeStatus: any) => {
            // Count attributes with and without owners
            if (attributeStatus.data_owner_id) {
              attributesWithOwners++;
              console.log(`[Data Executive Assignment] Attribute ${attributeStatus.attribute_name} already has owner: ${attributeStatus.data_owner_name}`);
            } else {
              attributesWithoutOwners++;
            }
            
            // Only include attributes that don't have data owners assigned yet
            if (!attributeStatus.data_owner_id) {
              // Check if LOBs are assigned
              if (attributeStatus.assigned_lobs && attributeStatus.assigned_lobs.length > 0) {
                // Create a separate assignment for each LOB associated with this attribute
                attributeStatus.assigned_lobs.forEach((lob: any) => {
                  pending.push({
                    assignment_id: lobAssignment.assignment_id,
                    attribute_id: attributeStatus.attribute_id,
                    attribute_name: attributeStatus.attribute_name,
                    attribute_description: attributeStatus.attribute_description || '',
                    lob_name: lob.lob_name,
                    status: lobAssignment.status
                  });
                });
              } else {
                // If no LOBs are assigned, still create an assignment entry
                pending.push({
                  assignment_id: lobAssignment.assignment_id,
                  attribute_id: attributeStatus.attribute_id,
                  attribute_name: attributeStatus.attribute_name,
                  attribute_description: attributeStatus.attribute_description || '',
                  lob_name: 'No LOB Assigned',
                  status: lobAssignment.status
                });
              }
            }
          });
          
          console.log(`[Data Executive Assignment] Attributes with owners: ${attributesWithOwners}`);
          console.log(`[Data Executive Assignment] Attributes without owners: ${attributesWithoutOwners}`);
        }
      } else {
        console.log('[Data Executive Assignment] No relevant assignments found - check if Data Executive has been assigned');
      }
      
      console.log('[Data Executive Assignment] Final pending assignments:', pending);
      console.log('[Data Executive Assignment] Pending assignments count:', pending.length);
      setPendingAssignments(pending);
      
      // Extract available data providers from users response
      const providers: DataProvider[] = [];
      if (usersResponse.data && usersResponse.data.users) {
        usersResponse.data.users.forEach((dp: any) => {
          providers.push({
            user_id: dp.user_id,
            first_name: dp.first_name,
            last_name: dp.last_name,
            email: dp.email,
            lob_name: dp.lob_name || 'Default LOB'
          });
        });
      }
      
      console.log('[Data Executive Assignment] Available data providers:', providers);
      setDataProviders(providers);
      
      // Initialize assignment selections
      const initialAssignments = pending.map(pa => ({
        attribute_id: pa.attribute_id,
        data_owner_id: null,
        assignment_notes: ''
      }));
      setAssignments(initialAssignments);
      
    } catch (error: any) {
      console.error('[Data Executive Assignment] Error loading assignment data:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to load assignment data';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleAssignmentChange = (attributeId: number, dataProviderId: number | null) => {
    setAssignments(prev => prev.map(assignment => 
      assignment.attribute_id === attributeId 
        ? { ...assignment, data_owner_id: dataProviderId }
        : assignment
    ));
  };

  const handleNotesChange = (attributeId: number, notes: string) => {
    setAssignments(prev => prev.map(assignment => 
      assignment.attribute_id === attributeId 
        ? { ...assignment, assignment_notes: notes }
        : assignment
    ));
  };

  const handleSubmit = async () => {
    // Validate that all assignments have data providers selected
    const incompleteAssignments = assignments.filter(a => !a.data_owner_id);
    if (incompleteAssignments.length > 0) {
      toast.error(`Please select data providers for all ${incompleteAssignments.length} attributes`);
      return;
    }

    setSubmitting(true);
    try {
      console.log('[Data Executive Assignment] Submitting assignments:', assignments);
      
      const submissionData = {
        assignments: assignments.map(a => {
          // Find the pending assignment to get the attribute name
          const pending = pendingAssignments.find(p => p.attribute_id === a.attribute_id);
          return {
            attribute_id: a.attribute_id,
            attribute_name: pending?.attribute_name || '',  // Include attribute name for backend fallback
            data_owner_id: a.data_owner_id!,  // API expects data_owner_id
            assignment_notes: a.assignment_notes,
            use_historical_assignment: false
          };
        }),
        submission_notes: submissionNotes
      };
      
      const response = await apiClient.post(
        `/data-owner/cycles/${cycleIdNum}/reports/${reportIdNum}/cdo-assignments`,
        submissionData
      );
      
      console.log('[Data Executive Assignment] Submission response:', response.data);
      toast.success(`Successfully assigned ${assignments.length} data providers!`);
      
      refetchStatus();
      // Navigate back to data provider page
      navigate(`/cycles/${cycleIdNum}/reports/${reportIdNum}/data-owner`);
      
    } catch (error: any) {
      console.error('[Data Executive Assignment] Error submitting assignments:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to submit assignments';
      toast.error(errorMessage);
    } finally {
      setSubmitting(false);
      setConfirmDialog(false);
    }
  };

  const getDataProviderName = (userId: number) => {
    const provider = dataProviders.find(dp => dp.user_id === userId);
    return provider ? `${provider.first_name} ${provider.last_name}` : '';
  };

  if (loading) {
    return (
      <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={loadAssignmentData} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
      <Stack spacing={3}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton 
              onClick={() => navigate(`/cycles/${cycleIdNum}/reports/${reportIdNum}/data-owner`)}
              color="primary"
            >
              <ArrowBackIcon />
            </IconButton>
            <Box>
              <Typography variant="h4" gutterBottom>
                Assign Data Owners
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Select data providers for attributes that require assignment
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={loadAssignmentData}
              disabled={loading}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={() => setConfirmDialog(true)}
              disabled={submitting || pendingAssignments.length === 0}
            >
              Submit Assignments
            </Button>
          </Box>
        </Box>

        {/* Summary */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <AssignmentIcon color="primary" />
              <Typography variant="h6">
                Assignment Summary
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              You have {pendingAssignments.length} attributes that need data provider assignments.
              Select a data provider from your LOB for each attribute.
            </Typography>
          </CardContent>
        </Card>

        {/* Assignments Table */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Pending Assignments ({pendingAssignments.length})
            </Typography>
            
            {pendingAssignments.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  All Assignments Complete
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  All attributes have been assigned data providers.
                </Typography>
              </Box>
            ) : (
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Attribute</TableCell>
                      <TableCell>LOB</TableCell>
                      <TableCell>Data Owner</TableCell>
                      <TableCell>Notes</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {pendingAssignments.map((pending) => {
                      const assignment = assignments.find(a => a.attribute_id === pending.attribute_id);
                      return (
                        <TableRow key={pending.attribute_id} hover>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {pending.attribute_name}
                              </Typography>
                              {pending.attribute_description && (
                                <Typography variant="caption" color="text.secondary" display="block">
                                  {pending.attribute_description}
                                </Typography>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <BusinessIcon fontSize="small" color="primary" />
                              <Typography variant="body2">
                                {pending.lob_name}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <FormControl fullWidth size="small" sx={{ minWidth: 200 }}>
                              <InputLabel>Select Data Owner</InputLabel>
                              <Select
                                value={assignment?.data_owner_id || ''}
                                label="Select Data Owner"
                                onChange={(e) => handleAssignmentChange(pending.attribute_id, e.target.value as number)}
                              >
                                {dataProviders.map((provider) => (
                                  <MenuItem key={provider.user_id} value={provider.user_id}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                      <PersonIcon fontSize="small" />
                                      <Box>
                                        <Typography variant="body2">
                                          {provider.first_name} {provider.last_name}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                          {provider.email}
                                        </Typography>
                                      </Box>
                                    </Box>
                                  </MenuItem>
                                ))}
                              </Select>
                            </FormControl>
                          </TableCell>
                          <TableCell>
                            <TextField
                              size="small"
                              placeholder="Assignment notes..."
                              value={assignment?.assignment_notes || ''}
                              onChange={(e) => handleNotesChange(pending.attribute_id, e.target.value)}
                              sx={{ minWidth: 150 }}
                            />
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={assignment?.data_owner_id ? 'Ready' : 'Pending'}
                              size="small"
                              color={assignment?.data_owner_id ? 'success' : 'warning'}
                            />
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </Stack>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog} onClose={() => setConfirmDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Confirm Data Owner Assignments</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            You are about to assign data providers to {assignments.length} attributes:
          </Typography>
          <Box sx={{ mt: 2, mb: 2 }}>
            {assignments.map((assignment) => {
              const pending = pendingAssignments.find(p => p.attribute_id === assignment.attribute_id);
              return (
                <Box key={assignment.attribute_id} sx={{ mb: 1 }}>
                  <Typography variant="body2">
                    <strong>{pending?.attribute_name}</strong> → {getDataProviderName(assignment.data_owner_id!)}
                  </Typography>
                </Box>
              );
            })}
          </Box>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Submission Notes (Optional)"
            value={submissionNotes}
            onChange={(e) => setSubmissionNotes(e.target.value)}
            placeholder="Add any notes about these assignments..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={20} /> : <SaveIcon />}
          >
            {submitting ? 'Submitting...' : 'Confirm Assignments'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DataExecutiveAssignmentInterface; 