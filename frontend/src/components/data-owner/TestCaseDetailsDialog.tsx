import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
  IconButton,
} from '@mui/material';
import {
  Close as CloseIcon,
  Assignment as AssignmentIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';

interface TestCase {
  test_case_id: string;
  phase_id: string;
  cycle_id: number;
  cycle_name?: string;
  report_id: number;
  report_name?: string;
  sample_identifier: string;
  primary_key_attributes?: any;
  attribute_name: string;
  status: string;
  submission_deadline?: string | null;
  submitted_at?: string | null;
  document_count?: number;
  has_submissions?: boolean;
  
  // Optional fields that may not be in TestCaseAssignment
  sample_id?: string;
  attribute_id?: number;
  data_owner_id?: number;
  data_owner_name?: string;
  data_owner_email?: string;
  assigned_at?: string | null;
  expected_evidence_type?: string;
  special_instructions?: string | null;
  submission_count?: number;
  latest_submission_at?: string | null;
}

interface TestCaseDetailsDialogProps {
  open: boolean;
  onClose: () => void;
  testCase: TestCase | null;
}

export const TestCaseDetailsDialog: React.FC<TestCaseDetailsDialogProps> = ({
  open,
  onClose,
  testCase,
}) => {
  if (!testCase) return null;

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'submitted':
        return 'success';
      case 'pending':
        return 'warning';
      case 'overdue':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleString();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '60vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <AssignmentIcon color="primary" />
            <Typography variant="h6">Test Case Details</Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Basic Information */}
          <Box>
            <Typography variant="h6" gutterBottom color="primary">
              Basic Information
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell component="th" scope="row" sx={{ fontWeight: 'bold', width: '30%' }}>
                      Test Case ID
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {testCase.test_case_id}
                      </Typography>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row" sx={{ fontWeight: 'bold' }}>
                      Status
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={testCase.status}
                        color={getStatusColor(testCase.status)}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row" sx={{ fontWeight: 'bold' }}>
                      Cycle & Report
                    </TableCell>
                    <TableCell>
                      {testCase.cycle_name || `Cycle ${testCase.cycle_id}`} • {testCase.report_name || `Report ${testCase.report_id}`}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row" sx={{ fontWeight: 'bold' }}>
                      Attribute Name
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {testCase.attribute_name}
                      </Typography>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row" sx={{ fontWeight: 'bold' }}>
                      Evidence Type
                    </TableCell>
                    <TableCell>
                      {testCase.expected_evidence_type || 'Document'}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          {/* Sample Information */}
          <Box>
            <Typography variant="h6" gutterBottom color="primary">
              Sample Information
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell component="th" scope="row" sx={{ fontWeight: 'bold', width: '30%' }}>
                      Sample ID
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {testCase.sample_identifier}
                      </Typography>
                    </TableCell>
                  </TableRow>
                  {testCase.primary_key_attributes && Object.keys(testCase.primary_key_attributes).length > 0 && (
                    <>
                      <TableRow>
                        <TableCell colSpan={2} sx={{ bgcolor: 'grey.50', fontWeight: 'bold' }}>
                          Primary Key Values
                        </TableCell>
                      </TableRow>
                      {Object.entries(testCase.primary_key_attributes).map(([key, value]) => (
                        <TableRow key={key}>
                          <TableCell component="th" scope="row" sx={{ pl: 4 }}>
                            {key}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                              {String(value)}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          {/* Dates & Deadlines */}
          <Box>
            <Typography variant="h6" gutterBottom color="primary">
              <ScheduleIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
              Dates & Deadlines
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell component="th" scope="row" sx={{ fontWeight: 'bold', width: '30%' }}>
                      Assigned At
                    </TableCell>
                    <TableCell>{formatDate(testCase.assigned_at)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th" scope="row" sx={{ fontWeight: 'bold' }}>
                      Submission Deadline
                    </TableCell>
                    <TableCell>
                      {testCase.submission_deadline ? (
                        <Box>
                          {formatDate(testCase.submission_deadline)}
                          {new Date(testCase.submission_deadline) < new Date() && (
                            <Chip
                              label="Overdue"
                              color="error"
                              size="small"
                              sx={{ ml: 1 }}
                            />
                          )}
                        </Box>
                      ) : (
                        'No deadline'
                      )}
                    </TableCell>
                  </TableRow>
                  {testCase.submitted_at && (
                    <TableRow>
                      <TableCell component="th" scope="row" sx={{ fontWeight: 'bold' }}>
                        Submitted At
                      </TableCell>
                      <TableCell>{formatDate(testCase.submitted_at)}</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          {/* Special Instructions */}
          <Box>
            <Typography variant="h6" gutterBottom color="primary">
              <DescriptionIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
              Special Instructions
            </Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                {testCase.special_instructions || `Please provide evidence for ${testCase.attribute_name} for the sample identified by the primary key values shown above.`}
              </Typography>
            </Paper>
          </Box>

          {/* Submission Information */}
          <Box>
            <Typography variant="h6" gutterBottom color="primary">
              Submission Information
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell component="th" scope="row" sx={{ fontWeight: 'bold', width: '30%' }}>
                      Total Submissions
                    </TableCell>
                    <TableCell>{testCase.submission_count || testCase.document_count || 0}</TableCell>
                  </TableRow>
                  {testCase.latest_submission_at && (
                    <TableRow>
                      <TableCell component="th" scope="row" sx={{ fontWeight: 'bold' }}>
                        Latest Submission
                      </TableCell>
                      <TableCell>{formatDate(testCase.latest_submission_at)}</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TestCaseDetailsDialog;