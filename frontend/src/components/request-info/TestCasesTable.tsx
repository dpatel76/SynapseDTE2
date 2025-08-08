import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Box,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  TableSortLabel,
  TablePagination,
  Popover,
  List,
  ListItem,
  ListItemText,
  Badge,
} from '@mui/material';
import {
  Edit as EditIcon,
  Send as SendIcon,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Visibility as VisibilityIcon,
  Storage as StorageIcon,
  Description,
  CloudUpload as CloudUploadIcon,
} from '@mui/icons-material';
import { EvidenceModal } from '../shared/EvidenceModal';

interface TestCase {
  test_case_id: string;
  test_case_number?: string;
  sample_id: string;
  sample_identifier: string;
  primary_key_attributes?: any;
  attribute_id: number;
  attribute_name: string;
  data_owner_id: number;
  data_owner_name: string;
  data_owner_email: string;
  status: 'Pending' | 'Submitted' | 'Overdue' | 'Complete' | 'In Progress';
  validation_status?: 'Pending' | 'Approved' | 'Rejected';
  approval_status?: 'Pending' | 'Approved' | 'Rejected' | 'Requires Revision';
  submission_count: number;
  submission_deadline?: string;
  submitted_at?: string;
  expected_evidence_type?: string;
  special_instructions?: string;
  latest_submission_at?: string;
}

interface TestCasesTableProps {
  testCases: TestCase[];
  onEdit?: (testCase: TestCase) => void;
  onResend?: (testCase: TestCase) => void;
  onViewEvidence?: (testCase: TestCase) => void;
  onValidate?: (testCase: TestCase, status: 'Approved' | 'Rejected') => void;
  onViewSampleDetails?: (testCase: TestCase) => void;
  onUploadEvidence?: (testCase: TestCase) => void;
  userRole?: string;
}

type OrderDirection = 'asc' | 'desc';

export const TestCasesTable: React.FC<TestCasesTableProps> = ({
  testCases,
  onEdit,
  onResend,
  onViewEvidence,
  onValidate,
  onViewSampleDetails,
  onUploadEvidence,
  userRole = 'Tester',
}) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [orderBy, setOrderBy] = useState<keyof TestCase>('test_case_id');
  const [orderDirection, setOrderDirection] = useState<OrderDirection>('asc');
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);
  const [selectedTestCaseId, setSelectedTestCaseId] = useState<string | null>(null);

  const handleSort = (property: keyof TestCase) => {
    const isAsc = orderBy === property && orderDirection === 'asc';
    setOrderDirection(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };


  const handleEvidenceClick = (event: React.MouseEvent<HTMLElement>, testCase: TestCase) => {
    setSelectedTestCaseId(testCase.test_case_id);
    setEvidenceModalOpen(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Submitted':
        return 'success';
      case 'Overdue':
        return 'error';
      case 'Pending':
      default:
        return 'warning';
    }
  };

  const getValidationIcon = (status?: string) => {
    switch (status) {
      case 'Approved':
        return <CheckCircle fontSize="small" color="success" />;
      case 'Rejected':
        return <ErrorIcon fontSize="small" color="error" />;
      default:
        return <Warning fontSize="small" color="warning" />;
    }
  };

  const formatPrimaryKeyValues = (pkAttributes: any) => {
    if (!pkAttributes || typeof pkAttributes !== 'object') {
      return {};
    }
    return pkAttributes;
  };

  // Get unique primary key columns from all test cases
  const primaryKeyColumns = React.useMemo(() => {
    const pkSet = new Set<string>();
    testCases.forEach(tc => {
      if (tc.primary_key_attributes && typeof tc.primary_key_attributes === 'object') {
        Object.keys(tc.primary_key_attributes).forEach(key => pkSet.add(key));
      }
    });
    return Array.from(pkSet).sort();
  }, [testCases]);

  const sortedTestCases = [...testCases].sort((a, b) => {
    const aValue = a[orderBy];
    const bValue = b[orderBy];
    
    if (aValue === null || aValue === undefined) return 1;
    if (bValue === null || bValue === undefined) return -1;
    
    if (aValue < bValue) {
      return orderDirection === 'asc' ? -1 : 1;
    }
    if (aValue > bValue) {
      return orderDirection === 'asc' ? 1 : -1;
    }
    return 0;
  });

  const paginatedTestCases = sortedTestCases.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // Calculate summary statistics
  const totalTestCases = testCases.length;
  const submittedCount = testCases.filter(tc => tc.status === 'Submitted').length;
  const pendingCount = testCases.filter(tc => tc.status === 'Pending').length;
  const overdueCount = testCases.filter(tc => tc.status === 'Overdue').length;
  const uniqueSamples = new Set(testCases.map(tc => tc.sample_id)).size;
  const uniqueDataOwners = new Set(testCases.map(tc => tc.data_owner_id)).size;

  return (
    <Box>
      <TableContainer component={Paper} elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'grey.50' }}>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'sample_id'}
                  direction={orderBy === 'sample_id' ? orderDirection : 'asc'}
                  onClick={() => handleSort('sample_id')}
                >
                  Sample ID
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'test_case_number'}
                  direction={orderBy === 'test_case_number' ? orderDirection : 'asc'}
                  onClick={() => handleSort('test_case_number')}
                >
                  Test Case ID
                </TableSortLabel>
              </TableCell>
              {/* Dynamic PK columns */}
              {primaryKeyColumns.map((pkCol) => (
                <TableCell key={pkCol}>
                  <TableSortLabel
                    active={false}
                    disabled
                  >
                    {pkCol}
                  </TableSortLabel>
                </TableCell>
              ))}
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'attribute_name'}
                  direction={orderBy === 'attribute_name' ? orderDirection : 'asc'}
                  onClick={() => handleSort('attribute_name')}
                >
                  Attribute Name
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'data_owner_name'}
                  direction={orderBy === 'data_owner_name' ? orderDirection : 'asc'}
                  onClick={() => handleSort('data_owner_name')}
                >
                  Data Owner Name
                </TableSortLabel>
              </TableCell>
              <TableCell align="center">Evidence</TableCell>
              <TableCell align="center">
                <TableSortLabel
                  active={orderBy === 'status'}
                  direction={orderBy === 'status' ? orderDirection : 'asc'}
                  onClick={() => handleSort('status')}
                >
                  Status
                </TableSortLabel>
              </TableCell>
              <TableCell align="center">Approval Status</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedTestCases.map((testCase) => (
              <TableRow
                key={testCase.test_case_id}
                hover
                sx={{
                  '&:hover': { bgcolor: 'action.hover' },
                  borderBottom: 1,
                  borderColor: 'divider',
                }}
              >
                <TableCell>
                  <Tooltip title={testCase.sample_id}>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem', cursor: 'pointer' }}>
                      {testCase.sample_id}
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {testCase.test_case_number || testCase.test_case_id}
                  </Typography>
                </TableCell>
                {/* Dynamic PK value cells */}
                {primaryKeyColumns.map((pkCol) => {
                  const pkValues = formatPrimaryKeyValues(testCase.primary_key_attributes);
                  return (
                    <TableCell key={pkCol}>
                      <Typography variant="body2">
                        {pkValues[pkCol] || '-'}
                      </Typography>
                    </TableCell>
                  );
                })}
                <TableCell>
                  <Typography variant="body2">{testCase.attribute_name}</Typography>
                </TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2">{testCase.data_owner_name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {testCase.data_owner_email}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="center">
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                    <IconButton
                      size="small"
                      onClick={(e) => handleEvidenceClick(e, testCase)}
                      disabled={testCase.submission_count === 0}
                    >
                      <Badge badgeContent={testCase.submission_count} color="primary" max={9}>
                        {testCase.expected_evidence_type === 'Data Source' ? (
                          <StorageIcon />
                        ) : (
                          <Description />
                        )}
                      </Badge>
                    </IconButton>
                    <Typography variant="caption" color="text.secondary">
                      {testCase.submission_count > 0 ? `${testCase.submission_count} submission${testCase.submission_count > 1 ? 's' : ''}` : 'No evidence'}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="center">
                  <Chip
                    label={testCase.status}
                    size="small"
                    color={getStatusColor(testCase.status)}
                    variant="filled"
                  />
                  {testCase.submission_deadline && (
                    <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 0.5 }}>
                      Due: {new Date(testCase.submission_deadline).toLocaleDateString()}
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">
                  {testCase.approval_status === 'Approved' ? (
                    <Chip
                      label="Approved"
                      size="small"
                      color="success"
                      icon={<CheckCircle />}
                    />
                  ) : testCase.approval_status === 'Rejected' ? (
                    <Chip
                      label="Rejected"
                      size="small"
                      color="error"
                      icon={<ErrorIcon />}
                    />
                  ) : testCase.approval_status === 'Requires Revision' ? (
                    <Chip
                      label="Revision Required"
                      size="small"
                      color="warning"
                      icon={<Warning />}
                    />
                  ) : testCase.status === 'Submitted' && testCase.submission_count > 0 ? (
                    <Chip
                      label="Pending Review"
                      size="small"
                      color="info"
                      variant="outlined"
                    />
                  ) : (
                    <Typography variant="caption" color="text.secondary">
                      Not Submitted
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">
                  <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                    {userRole === 'Data Owner' ? (
                      <>
                        {/* Data Owner can upload evidence */}
                        <Tooltip title="Upload Evidence">
                          <IconButton
                            size="small"
                            onClick={() => onUploadEvidence && onUploadEvidence(testCase)}
                            color="primary"
                            disabled={testCase.status === 'Submitted'}
                          >
                            <CloudUploadIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {/* Data Owner can view evidence */}
                        {testCase.submission_count > 0 && (
                          <Tooltip title="View Evidence">
                            <IconButton
                              size="small"
                              onClick={() => onViewEvidence && onViewEvidence(testCase)}
                              color="default"
                            >
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        {/* Data Owner can view sample details */}
                        <Tooltip title="View Sample Details">
                          <IconButton
                            size="small"
                            onClick={() => onViewSampleDetails && onViewSampleDetails(testCase)}
                            color="default"
                          >
                            <Description fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </>
                    ) : (
                      <>
                        {/* Tester can edit test cases */}
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            onClick={() => onEdit && onEdit(testCase)}
                            color="primary"
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {/* Tester can resend to data owner */}
                        <Tooltip title="Resend to Data Owner">
                          <IconButton
                            size="small"
                            onClick={() => {
                              console.log('🔄 RESEND button clicked for test case:', testCase.test_case_id);
                              onResend && onResend(testCase);
                            }}
                            color="info"
                          >
                            <SendIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {/* Tester can view sample details */}
                        <Tooltip title="View Sample Details">
                          <IconButton
                            size="small"
                            onClick={() => onViewSampleDetails && onViewSampleDetails(testCase)}
                            color="default"
                          >
                            <VisibilityIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {/* Tester can approve/reject evidence if there are submissions and no approval decision yet */}
                        {(testCase.submission_count > 0 && !testCase.approval_status) && (
                          <>
                            <Tooltip title="Approve Evidence">
                              <IconButton
                                size="small"
                                onClick={() => onValidate && onValidate(testCase, 'Approved')}
                                color="success"
                              >
                                <CheckCircle fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Reject Evidence">
                              <IconButton
                                size="small"
                                onClick={() => {
                                  console.log('❌ REJECT button clicked for test case:', testCase.test_case_id);
                                  onValidate && onValidate(testCase, 'Rejected');
                                }}
                                color="error"
                              >
                                <ErrorIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}
                      </>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50]}
        component="div"
        count={testCases.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />


      {/* Evidence Details Modal */}
      <EvidenceModal
        open={evidenceModalOpen}
        testCaseId={selectedTestCaseId || ''}
        onClose={() => {
          setEvidenceModalOpen(false);
          setSelectedTestCaseId(null);
        }}
      />
    </Box>
  );
};