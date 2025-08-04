import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Divider
} from '@mui/material';
import {
  BugReport as BugReportIcon,
  Description as DescriptionIcon,
  Assignment as AssignmentIcon,
  Schedule as ScheduleIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';

interface ObservationDetailsModalProps {
  open: boolean;
  onClose: () => void;
  observationGroup: any;
  observation: any;
  testExecutions: any[];
}

const ObservationDetailsModal: React.FC<ObservationDetailsModalProps> = ({
  open,
  onClose,
  observationGroup,
  observation,
  testExecutions
}) => {
  if (!observationGroup || !observation) {
    return null;
  }

  // Get all test execution IDs for this observation
  const getLinkedTestExecutionIds = () => {
    const ids: string[] = [];
    if (observation.test_execution_id) {
      ids.push(String(observation.test_execution_id));
    }
    if (observation.linked_test_executions && Array.isArray(observation.linked_test_executions)) {
      observation.linked_test_executions.forEach((id: string) => {
        if (id && !ids.includes(String(id))) {
          ids.push(String(id));
        }
      });
    }
    return ids;
  };

  const linkedTestExecutionIds = getLinkedTestExecutionIds();
  const linkedTestExecutions = testExecutions.filter(exec => 
    linkedTestExecutionIds.includes(String(exec.execution_id))
  );

  const getSeverityColor = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case 'HIGH':
      case 'CRITICAL':
        return 'error';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'approved':
      case 'finalized':
        return 'success';
      case 'rejected':
        return 'error';
      case 'pending review':
      case 'pending approval':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { minHeight: '80vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <BugReportIcon color="error" />
          <Typography variant="h6">Observation Details</Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        {/* Overview Section */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon />
            Overview
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
            <Box sx={{ flex: '1 1 45%', minWidth: 250 }}>
              <Box mb={2}>
                <Typography variant="subtitle2" color="text.secondary">Attribute</Typography>
                <Typography variant="body1">{observationGroup.attribute_name}</Typography>
              </Box>
              <Box mb={2}>
                <Typography variant="subtitle2" color="text.secondary">Issue Type</Typography>
                <Typography variant="body1">{observationGroup.issue_type}</Typography>
              </Box>
            </Box>
            <Box sx={{ flex: '1 1 45%', minWidth: 250 }}>
              <Box mb={2}>
                <Typography variant="subtitle2" color="text.secondary">Severity</Typography>
                <Chip 
                  label={observationGroup.rating || 'MEDIUM'} 
                  color={getSeverityColor(observationGroup.rating)}
                  size="small"
                />
              </Box>
              <Box mb={2}>
                <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                <Chip 
                  label={observationGroup.approval_status} 
                  color={getStatusColor(observationGroup.approval_status)}
                  size="small"
                />
              </Box>
            </Box>
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Description Section */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DescriptionIcon />
            Description
          </Typography>
          <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Typography variant="body1">
              {observation.description || 'No description available'}
            </Typography>
          </Paper>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Impact Section */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssignmentIcon />
            Impact Summary
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', flex: '1 1 30%', minWidth: 150 }}>
              <Typography variant="h4" color="primary">
                {observationGroup.total_samples || 0}
              </Typography>
              <Typography variant="subtitle2" color="text.secondary">
                Samples Impacted
              </Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', flex: '1 1 30%', minWidth: 150 }}>
              <Typography variant="h4" color="primary">
                {linkedTestExecutionIds.length}
              </Typography>
              <Typography variant="subtitle2" color="text.secondary">
                Test Cases Linked
              </Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', flex: '1 1 30%', minWidth: 150 }}>
              <Typography variant="h4" color="primary">
                {observationGroup.observations?.length || 1}
              </Typography>
              <Typography variant="subtitle2" color="text.secondary">
                Grouped Observations
              </Typography>
            </Paper>
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Test Executions Section */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssignmentIcon />
            Linked Test Executions
          </Typography>
          
          {linkedTestExecutions.length > 0 ? (
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Test Case ID</TableCell>
                    <TableCell>Sample ID</TableCell>
                    <TableCell>Expected Value</TableCell>
                    <TableCell>Actual Value</TableCell>
                    <TableCell>Result</TableCell>
                    <TableCell>Evidence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {linkedTestExecutions.map((exec) => (
                    <TableRow key={exec.execution_id}>
                      <TableCell>{exec.test_case_id}</TableCell>
                      <TableCell>{exec.sample_id || 'N/A'}</TableCell>
                      <TableCell>{exec.expected_value || 'N/A'}</TableCell>
                      <TableCell>{exec.extracted_value || exec.retrieved_value || 'N/A'}</TableCell>
                      <TableCell>
                        <Chip 
                          label={exec.result || exec.test_result || 'Unknown'} 
                          color={exec.result === 'Pass' || exec.test_result === 'pass' ? 'success' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {exec.evidence_files?.length > 0 || exec.has_evidence ? (
                          <Chip label="Available" color="info" size="small" />
                        ) : (
                          <Chip label="None" variant="outlined" size="small" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography color="text.secondary" align="center">
                No test executions linked to this observation
              </Typography>
            </Paper>
          )}
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Timeline Section */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ScheduleIcon />
            Timeline
          </Typography>
          <Box>
            <Typography variant="body2">
              <strong>Created:</strong> {new Date(observation.created_at).toLocaleString()}
            </Typography>
            {observationGroup.report_owner_approved && (
              <Typography variant="body2" color="success.main">
                <strong>Approved by Report Owner</strong>
              </Typography>
            )}
            {observationGroup.data_executive_approved && (
              <Typography variant="body2" color="success.main">
                <strong>Approved by Data Executive</strong>
              </Typography>
            )}
          </Box>
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ObservationDetailsModal;