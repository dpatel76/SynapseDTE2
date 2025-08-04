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
  Button,
  TableSortLabel,
  TablePagination,
  Badge,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Send as SendIcon,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Description,
  Visibility as VisibilityIcon,
  Storage as DatabaseIcon,
} from '@mui/icons-material';
import { EvidenceModal } from '../shared/EvidenceModal';

interface TestCase {
  test_case_id: string;
  phase_id: string;
  cycle_id: number;
  cycle_name?: string;
  report_id: number;
  report_name?: string;
  sample_id: string;
  sample_identifier: string;
  primary_key_attributes?: any;
  attribute_id?: number;
  attribute_name: string;
  data_owner_id?: number;
  data_owner_name?: string;
  data_owner_email?: string;
  status: 'Pending' | 'Submitted' | 'Overdue' | string;
  submission_deadline?: string | null;
  submitted_at?: string | null;
  expected_evidence_type?: string;
  special_instructions?: string | null;
  submission_count: number;
  latest_submission_at?: string | null;
  document_count?: number; // For backwards compatibility
  has_submissions?: boolean;
}

interface TestCasesTableProps {
  testCases: TestCase[];
  cycleName?: string;
  reportName?: string;
  onUpload?: (testCase: TestCase) => void;
  onSubmit?: (testCase: TestCase) => void;
  onViewEvidence?: (testCase: TestCase) => void;
  onViewDetails?: (testCase: TestCase) => void;
}

type OrderDirection = 'asc' | 'desc';

export const TestCasesTable: React.FC<TestCasesTableProps> = ({
  testCases,
  cycleName,
  reportName,
  onUpload,
  onSubmit,
  onViewEvidence,
  onViewDetails,
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

  const handleEvidenceClick = (event: React.MouseEvent<HTMLElement>, testCaseId: string) => {
    setSelectedTestCaseId(testCaseId);
    setEvidenceModalOpen(true);
  };

  const handleEvidenceModalClose = () => {
    setEvidenceModalOpen(false);
    setSelectedTestCaseId(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Submitted':
      case 'Complete':
        return 'success';
      case 'Overdue':
        return 'error';
      case 'In Progress':
        return 'info';
      case 'Pending':
      default:
        return 'warning';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Submitted':
      case 'Complete':
        return <CheckCircle fontSize="small" />;
      case 'Overdue':
        return <ErrorIcon fontSize="small" />;
      case 'In Progress':
        return <Warning fontSize="small" color="info" />;
      case 'Pending':
      default:
        return <Warning fontSize="small" />;
    }
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

  return (
    <Box>
      {/* Display Cycle and Report info as header */}
      {(cycleName || reportName) && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" color="primary">
            {cycleName && <span>Cycle: {cycleName}</span>}
            {cycleName && reportName && <span> • </span>}
            {reportName && <span>Report: {reportName}</span>}
          </Typography>
        </Box>
      )}
      <TableContainer component={Paper} elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'grey.50' }}>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'test_case_id'}
                  direction={orderBy === 'test_case_id' ? orderDirection : 'asc'}
                  onClick={() => handleSort('test_case_id')}
                >
                  Test Case ID
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'sample_identifier'}
                  direction={orderBy === 'sample_identifier' ? orderDirection : 'asc'}
                  onClick={() => handleSort('sample_identifier')}
                >
                  Sample ID
                </TableSortLabel>
              </TableCell>
              {/* Dynamic PK columns */}
              {primaryKeyColumns.map((pkCol) => (
                <TableCell key={pkCol}>
                  <TableSortLabel active={false} disabled>
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
                  Attribute
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
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'submission_deadline'}
                  direction={orderBy === 'submission_deadline' ? orderDirection : 'asc'}
                  onClick={() => handleSort('submission_deadline')}
                >
                  Deadline
                </TableSortLabel>
              </TableCell>
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
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {testCase.test_case_id}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Tooltip title={testCase.sample_id}>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                      {testCase.sample_identifier}
                    </Typography>
                  </Tooltip>
                </TableCell>
                {/* Dynamic PK value cells */}
                {primaryKeyColumns.map((pkCol) => {
                  const pkValues = testCase.primary_key_attributes || {};
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
                  {testCase.special_instructions && (
                    <Typography variant="caption" color="text.secondary" display="block">
                      {testCase.special_instructions}
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                    <IconButton
                      size="small"
                      onClick={(e) => handleEvidenceClick(e, testCase.test_case_id)}
                      disabled={!testCase.submission_count || testCase.submission_count === 0}
                    >
                      <Badge badgeContent={testCase.submission_count || 0} color="primary" max={9}>
                        <Description />
                      </Badge>
                    </IconButton>
                    <Typography variant="caption" color="text.secondary">
                      {testCase.submission_count && testCase.submission_count > 0 
                        ? `${testCase.submission_count} evidence${testCase.submission_count > 1 ? 's' : ''}` 
                        : 'No evidence'}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="center">
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                    {getStatusIcon(testCase.status)}
                    <Chip
                      label={testCase.status}
                      size="small"
                      color={getStatusColor(testCase.status)}
                      variant="filled"
                    />
                  </Box>
                </TableCell>
                <TableCell>
                  {testCase.submission_deadline ? (
                    <Box>
                      <Typography variant="body2">
                        {new Date(testCase.submission_deadline).toLocaleDateString()}
                      </Typography>
                      {testCase.status === 'Pending' && (
                        <Typography variant="caption" color={
                          new Date(testCase.submission_deadline) < new Date() ? 'error' : 'text.secondary'
                        }>
                          {new Date(testCase.submission_deadline) < new Date() 
                            ? 'Overdue' 
                            : `${Math.ceil((new Date(testCase.submission_deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))} days left`}
                        </Typography>
                      )}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No deadline
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">
                  <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                    {((!testCase.submission_count || testCase.submission_count === 0) || testCase.status === 'In Progress') && (
                      <Tooltip title={testCase.status === 'In Progress' ? "Upload Revised Evidence" : "Upload Evidence"}>
                        <IconButton
                          size="small"
                          onClick={() => onUpload && onUpload(testCase)}
                          color="primary"
                        >
                          <UploadIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => onViewDetails && onViewDetails(testCase)}
                        color="default"
                      >
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
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
      {selectedTestCaseId && (
        <EvidenceModal
          open={evidenceModalOpen}
          onClose={handleEvidenceModalClose}
          testCaseId={selectedTestCaseId}
          testCaseData={testCases.find(tc => tc.test_case_id === selectedTestCaseId)}
        />
      )}
    </Box>
  );
};

export default TestCasesTable;