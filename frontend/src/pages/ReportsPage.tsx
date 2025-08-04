import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tooltip,
  Menu,
  MenuItem as MuiMenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Assessment as ReportIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportsApi, CreateReportRequest, UpdateReportRequest } from '../api/reports';
import { lobsApi } from '../api/lobs';
import { usersApi } from '../api/users';
import { Report, LOB, UserRole } from '../types/api';
import { useAuth } from '../contexts/AuthContext';
import { usePermissions } from '../contexts/PermissionContext';
import { PermissionGate } from '../components/auth/PermissionGate';
import apiClient from '../api/client';

const ReportsPage: React.FC = () => {
  const { user } = useAuth();
  const { hasPermission } = usePermissions();
  const queryClient = useQueryClient();
  
  // State for pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // State for dialogs
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  
  // State for forms
  const [formData, setFormData] = useState<CreateReportRequest>({
    report_name: '',
    lob_id: 0,
    report_owner_id: 0,
    description: '',
    frequency: 'quarterly',
    regulation: '',
  });
  
  // State for menu
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuReport, setMenuReport] = useState<Report | null>(null);

  // Query for reports
  // For Test Managers, only show reports in their cycles
  const {
    data: reportsData,
    isLoading: reportsLoading,
    error: reportsError,
  } = useQuery({
    queryKey: ['reports', page + 1, rowsPerPage, user?.role],
    queryFn: async () => {
      // Filter reports for Test Executive to only show their cycle reports
      if ((user?.role as string) === 'Test Executive') {
        try {
          // First get all cycles for this test manager
          const cyclesResponse = await apiClient.get('/cycles/', {
            params: { skip: 0, limit: 100 }
          });
          
          const myCycles = cyclesResponse.data.cycles.filter((cycle: any) => 
            cycle.test_executive_id === user?.user_id
          );
          
          if (myCycles.length === 0) {
            return { items: [], total: 0, page: 1, per_page: rowsPerPage, pages: 0 };
          }
          
          // Get all reports from these cycles
          const allReports: Report[] = [];
          const reportIds = new Set<number>();
          
          for (const cycle of myCycles) {
            const cycleReportsResponse = await apiClient.get(`/cycles/${cycle.cycle_id}/reports`);
            const cycleReports = cycleReportsResponse.data;
            
            for (const report of cycleReports) {
              if (!reportIds.has(report.report_id)) {
                reportIds.add(report.report_id);
                // Fetch full report details
                try {
                  const reportResponse = await apiClient.get(`/reports/${report.report_id}`);
                  allReports.push(reportResponse.data);
                } catch (error) {
                  console.error(`Failed to fetch report ${report.report_id}:`, error);
                }
              }
            }
          }
          
          // Apply pagination
          const start = page * rowsPerPage;
          const paginatedReports = allReports.slice(start, start + rowsPerPage);
          
          return {
            items: paginatedReports,
            total: allReports.length,
            page: page + 1,
            per_page: rowsPerPage,
            pages: Math.ceil(allReports.length / rowsPerPage)
          };
        } catch (error) {
          console.error('Error fetching Test Manager reports:', error);
          throw error;
        }
      }
      
      // For other roles, use the standard API
      return reportsApi.getAll(page + 1, rowsPerPage);
    },
  });

  // Query for LOBs
  const {
    data: lobs,
    isLoading: lobsLoading,
  } = useQuery({
    queryKey: ['lobs', 'active'],
    queryFn: () => lobsApi.getAllActive(),
  });

  // Query for Report Owners
  const {
    data: reportOwners,
    isLoading: reportOwnersLoading,
  } = useQuery({
    queryKey: ['users', 'report-owners'],
    queryFn: () => usersApi.getReportOwners(),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: reportsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      setOpenCreateDialog(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateReportRequest }) => 
      reportsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      setOpenEditDialog(false);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: reportsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      handleCloseMenu();
    },
  });

  const resetForm = () => {
    setFormData({
      report_name: '',
      lob_id: 0,
      report_owner_id: 0,
      description: '',
      frequency: 'quarterly',
      regulation: '',
    });
    setSelectedReport(null);
  };

  const handleCreate = () => {
    setOpenCreateDialog(true);
    resetForm();
  };

  const handleEdit = (report: Report) => {
    setSelectedReport(report);
    setFormData({
      report_name: report.report_name,
      lob_id: report.lob_id,
      report_owner_id: report.report_owner_id,
      description: report.description || '',
      frequency: report.frequency || 'quarterly',
      regulation: report.regulation || '',
    });
    setOpenEditDialog(true);
    handleCloseMenu();
  };

  const handleDelete = (report: Report) => {
    if (window.confirm(`Are you sure you want to delete "${report.report_name}"?`)) {
      deleteMutation.mutate(report.report_id);
    }
  };

  const handleSubmitCreate = () => {
    createMutation.mutate(formData);
  };

  const handleSubmitEdit = () => {
    if (selectedReport) {
      updateMutation.mutate({
        id: selectedReport.report_id,
        data: formData
      });
    }
  };

  const handleMenu = (event: React.MouseEvent<HTMLElement>, report: Report) => {
    setAnchorEl(event.currentTarget);
    setMenuReport(report);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
    setMenuReport(null);
  };

  const getLOBName = (lobId: number) => {
    const lob = lobs?.find(l => l.lob_id === lobId);
    return lob?.lob_name || 'Unknown LOB';
  };

  const getFrequencyColor = (frequency: string) => {
    if (!frequency) return 'default';
    switch (frequency.toLowerCase()) {
      case 'daily':
        return 'error';
      case 'weekly':
        return 'warning';
      case 'monthly':
        return 'info';
      case 'quarterly':
        return 'primary';
      case 'yearly':
        return 'success';
      default:
        return 'default';
    }
  };

  if (reportsLoading || lobsLoading || reportOwnersLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (reportsError) {
    return (
      <Alert severity="error">
        Failed to load reports. Please try again.
      </Alert>
    );
  }

  const reports = reportsData?.items || [];
  const totalCount = reportsData?.total || 0;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Reports</Typography>
        <PermissionGate resource="reports" action="create">
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Create Report
          </Button>
        </PermissionGate>
      </Box>

      {/* Data Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Report Name</TableCell>
                <TableCell>LOB</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Frequency</TableCell>
                <TableCell>Owner</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {reports.map((report) => (
                <TableRow key={report.report_id} hover>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <ReportIcon sx={{ mr: 1, color: 'primary.main' }} />
                      <Typography variant="subtitle2">
                        {report.report_name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <BusinessIcon sx={{ mr: 1, color: 'text.secondary' }} />
                      <Typography variant="body2">
                        {getLOBName(report.lob_id)}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {report.description || 'No description'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {report.frequency ? (
                      <Chip
                        label={report.frequency.toUpperCase()}
                        color={getFrequencyColor(report.frequency)}
                        size="small"
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Not specified
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {report.owner?.first_name || report.owner?.username || 'Not assigned'}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={report.is_active ? 'ACTIVE' : 'INACTIVE'}
                      color={report.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {(hasPermission('reports', 'update') || hasPermission('reports', 'delete')) && (
                      <Tooltip title="More actions">
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenu(e, report)}
                        >
                          <MoreVertIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {reports.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No reports found. Create your first report to get started.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          component="div"
          count={totalCount}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </Paper>

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
      >
        {hasPermission('reports', 'update') && (
          <MuiMenuItem onClick={() => menuReport && handleEdit(menuReport)}>
            <EditIcon fontSize="small" sx={{ mr: 1 }} />
            Edit
          </MuiMenuItem>
        )}
        {hasPermission('reports', 'delete') && (
          <MuiMenuItem onClick={() => menuReport && handleDelete(menuReport)}>
            <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
            Delete
          </MuiMenuItem>
        )}
      </Menu>

      {/* Create Dialog */}
      <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Report</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <TextField
              label="Report Name"
              value={formData.report_name}
              onChange={(e) => setFormData({ ...formData, report_name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Regulation"
              value={formData.regulation}
              onChange={(e) => setFormData({ ...formData, regulation: e.target.value })}
              fullWidth
              placeholder="e.g., SOX, Basel III, GDPR"
            />
            <FormControl fullWidth required>
              <InputLabel>Line of Business</InputLabel>
              <Select
                value={formData.lob_id}
                onChange={(e) => setFormData({ ...formData, lob_id: e.target.value as number })}
                label="Line of Business"
              >
                {lobs?.map((lob) => (
                  <MenuItem key={lob.lob_id} value={lob.lob_id}>
                    {lob.lob_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth required>
              <InputLabel>Report Owner</InputLabel>
              <Select
                value={formData.report_owner_id}
                onChange={(e) => setFormData({ ...formData, report_owner_id: e.target.value as number })}
                label="Report Owner"
              >
                {reportOwners?.map((owner) => (
                  <MenuItem key={owner.user_id} value={owner.user_id}>
                    {owner.first_name} {owner.last_name} ({owner.email})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <FormControl fullWidth required>
              <InputLabel>Frequency</InputLabel>
              <Select
                value={formData.frequency}
                onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                label="Frequency"
              >
                <MenuItem value="daily">Daily</MenuItem>
                <MenuItem value="weekly">Weekly</MenuItem>
                <MenuItem value="monthly">Monthly</MenuItem>
                <MenuItem value="quarterly">Quarterly</MenuItem>
                <MenuItem value="yearly">Yearly</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSubmitCreate}
            variant="contained"
            disabled={!formData.report_name || !formData.lob_id || !formData.report_owner_id || createMutation.isPending}
          >
            {createMutation.isPending ? <CircularProgress size={20} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Report</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <TextField
              label="Report Name"
              value={formData.report_name}
              onChange={(e) => setFormData({ ...formData, report_name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Regulation"
              value={formData.regulation}
              onChange={(e) => setFormData({ ...formData, regulation: e.target.value })}
              fullWidth
              placeholder="e.g., SOX, Basel III, GDPR"
            />
            <FormControl fullWidth required>
              <InputLabel>Line of Business</InputLabel>
              <Select
                value={formData.lob_id}
                onChange={(e) => setFormData({ ...formData, lob_id: e.target.value as number })}
                label="Line of Business"
              >
                {lobs?.map((lob) => (
                  <MenuItem key={lob.lob_id} value={lob.lob_id}>
                    {lob.lob_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth required>
              <InputLabel>Report Owner</InputLabel>
              <Select
                value={formData.report_owner_id}
                onChange={(e) => setFormData({ ...formData, report_owner_id: e.target.value as number })}
                label="Report Owner"
              >
                {reportOwners?.map((owner) => (
                  <MenuItem key={owner.user_id} value={owner.user_id}>
                    {owner.first_name} {owner.last_name} ({owner.email})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <FormControl fullWidth required>
              <InputLabel>Frequency</InputLabel>
              <Select
                value={formData.frequency}
                onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                label="Frequency"
              >
                <MenuItem value="daily">Daily</MenuItem>
                <MenuItem value="weekly">Weekly</MenuItem>
                <MenuItem value="monthly">Monthly</MenuItem>
                <MenuItem value="quarterly">Quarterly</MenuItem>
                <MenuItem value="yearly">Yearly</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSubmitEdit}
            variant="contained"
            disabled={!formData.report_name || !formData.lob_id || !formData.report_owner_id || updateMutation.isPending}
          >
            {updateMutation.isPending ? <CircularProgress size={20} /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ReportsPage; 