import React, { useState, useEffect } from 'react';
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
  MenuList,
  MenuItem as MuiMenuItem,
  Card,
  CardContent,
  LinearProgress,
  Grid,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Collapse,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  FormControlLabel,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Visibility as ViewIcon,
  PlayArrow as StartIcon,
  PlayArrow,
  Stop as StopIcon,
  Assignment as CycleIcon,
  TrendingUp,
  CheckCircle,
  Warning,
  Schedule,
  Assessment,
  ExpandMore,
  Timeline,
  Group,
  PersonAdd as PersonAddIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cyclesApi, CreateTestCycleRequest, UpdateTestCycleRequest } from '../api/cycles';
import { TestCycle, CycleStatus, Report, User, UserRole } from '../types/api';
import { reportsApi } from '../api/reports';
import { usersApi } from '../api/users';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { usePermissions } from '../contexts/PermissionContext';
import { PermissionGate } from '../components/auth/PermissionGate';

interface AddReportsDialogProps {
  open: boolean;
  onClose: () => void;
  cycle: TestCycle | null;
  onReportsAdded?: (cycleId: number) => void;
}

const AddReportsDialog: React.FC<AddReportsDialogProps> = ({ open, onClose, cycle, onReportsAdded }) => {
  const [selectedReports, setSelectedReports] = useState<number[]>([]);
  const [testerAssignments, setTesterAssignments] = useState<Record<number, number | null>>({});
  const { showToast } = useNotifications();
  const queryClient = useQueryClient();

  // Query for available reports
  const { data: reportsData, isLoading: reportsLoading, error: reportsError } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportsApi.getAll(1, 100),
    enabled: open,
  });

  // Query for available testers
  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ['users', 'testers'],
    queryFn: async () => {
      const response = await apiClient.get('/users/?role=Tester');
      return response.data;
    },
    enabled: open,
  });

  // Mutation to add reports to cycle
  const addReportsMutation = useMutation({
    mutationFn: async (data: { cycleId: number; assignments: Array<{ reportId: number; testerId?: number }> }) => {
      // Extract just the report IDs
      const reportIds = data.assignments.map(assignment => assignment.reportId);
      
      // Create assignments array with proper format
      const assignments = data.assignments
        .filter(a => a.testerId !== undefined && a.testerId !== null)
        .map(a => ({
          report_id: a.reportId,
          tester_id: a.testerId
        }));
      
      // Call the API with reports and assignments
      const response = await apiClient.post(`/cycles/${data.cycleId}/reports`, {
        report_ids: reportIds,
        assignments: assignments.length > 0 ? assignments : undefined
      });
      
      return response;
    },
    onSuccess: () => {
      // Invalidate all relevant queries to refresh metrics
      queryClient.invalidateQueries({ queryKey: ['cycles'] });
      queryClient.invalidateQueries({ queryKey: ['cycles-executive'] });
      queryClient.invalidateQueries({ queryKey: ['cycle-reports'] });
      queryClient.invalidateQueries({ queryKey: ['test-executive-metrics-redesigned'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      // Invalidate tester assignments to ensure they see new assignments
      queryClient.invalidateQueries({ queryKey: ['tester-all-assignments'] });
      
      showToast('success', 'Reports added to cycle successfully');
      onClose();
      setSelectedReports([]);
      setTesterAssignments({});
      if (onReportsAdded && cycle) {
        onReportsAdded(cycle.cycle_id);
      }
    },
    onError: (error: any) => {
      showToast('error', `Failed to add reports: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleReportToggle = (reportId: number) => {
    setSelectedReports(prev => 
      prev.includes(reportId) 
        ? prev.filter(id => id !== reportId)
        : [...prev, reportId]
    );
  };

  const handleTesterAssignment = (reportId: number, testerId: number | null) => {
    setTesterAssignments(prev => ({
      ...prev,
      [reportId]: testerId,
    }));
  };

  const handleSubmit = () => {
    if (!cycle || selectedReports.length === 0) return;

    const assignments = selectedReports.map(reportId => ({
      reportId,
      testerId: testerAssignments[reportId] || undefined,
    }));

    addReportsMutation.mutate({
      cycleId: cycle.cycle_id,
      assignments,
    });
  };

  const reports = reportsData?.items || [];
  const testers = usersData?.users || [];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        Add Reports to "{cycle?.cycle_name}"
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" paragraph>
          Select reports from your inventory to add to this test cycle. You can optionally assign testers to each report.
        </Typography>

        {reportsLoading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : reportsError ? (
          <Alert severity="error">
            Failed to load reports: {(reportsError as any)?.message || 'Unknown error'}
          </Alert>
        ) : reports.length === 0 ? (
          <Alert severity="info">
            No reports available to add to this cycle.
          </Alert>
        ) : (
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox" width="5%">Select</TableCell>
                  <TableCell width="35%">Report Name</TableCell>
                  <TableCell width="15%">LOB</TableCell>
                  <TableCell width="20%">Owner</TableCell>
                  <TableCell width="25%">Assign Tester</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {reports.map((report: Report) => (
                  <TableRow key={report.report_id}>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedReports.includes(report.report_id)}
                        onChange={() => handleReportToggle(report.report_id)}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="subtitle2">
                        {report.report_name}
                      </Typography>
                      {report.description && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {report.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={report.lob_name || 'N/A'} 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap>
                        {report.owner_name || 'Unassigned'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <FormControl size="small" sx={{ minWidth: 150 }} disabled={!selectedReports.includes(report.report_id)}>
                        <Select
                          value={testerAssignments[report.report_id] || ''}
                          onChange={(e) => handleTesterAssignment(report.report_id, e.target.value as number || null)}
                          displayEmpty
                        >
                          <MenuItem value="">
                            <em>No tester assigned</em>
                          </MenuItem>
                          {testers.map((tester: User) => (
                            <MenuItem key={tester.user_id} value={tester.user_id}>
                              {`${tester.first_name} ${tester.last_name}`}
                              {/* Show email if there are duplicate names */}
                              {testers.filter((t: User) => 
                                t.first_name === tester.first_name && 
                                t.last_name === tester.last_name
                              ).length > 1 && (
                                <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                  ({tester.email})
                                </Typography>
                              )}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {selectedReports.length > 0 && (
          <Alert severity="info" sx={{ mt: 2 }}>
            {selectedReports.length} report(s) selected for addition to this cycle.
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={selectedReports.length === 0 || addReportsMutation.isPending}
        >
          {addReportsMutation.isPending ? <CircularProgress size={20} /> : `Add ${selectedReports.length} Report(s)`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const TestCyclesPage: React.FC = () => {
  const { user } = useAuth();
  const { hasPermission } = usePermissions();
  const { showToast } = useNotifications();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  
  // State for pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // State for dialogs
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [openAddReportsDialog, setOpenAddReportsDialog] = useState(false);
  const [selectedCycle, setSelectedCycle] = useState<TestCycle | null>(null);
  const [expandedCycle, setExpandedCycle] = useState<number | null>(null);
  
  // State for cycle reports
  const [cycleReports, setCycleReports] = useState<Record<number, any[]>>({});
  
  // State for forms
  const [formData, setFormData] = useState<CreateTestCycleRequest>({
    cycle_name: '',
    description: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
  });
  
  // State for menu
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuCycle, setMenuCycle] = useState<TestCycle | null>(null);

  // Query for test cycles - filtered by role
  const {
    data: cyclesData,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['cycles', page + 1, rowsPerPage, user?.role, user?.user_id],
    queryFn: async () => {
      if (user?.role === 'Tester') {
        // For testers, get cycles where they have assignments
        try {
          const assignedReports = await reportsApi.getByTester(user?.user_id || 0);
          
          // Extract unique cycles from assigned reports
          const cycleMap = new Map();
          assignedReports.forEach((report: any) => {
            if (!cycleMap.has(report.cycle_id)) {
              cycleMap.set(report.cycle_id, {
                cycle_id: report.cycle_id,
                cycle_name: report.cycle_name || `Cycle ${report.cycle_id}`,
                status: 'Active', // Default to Active since they have assignments
                description: `Test cycle with ${assignedReports.filter(r => r.cycle_id === report.cycle_id).length} assigned reports`,
                start_date: null,
                end_date: null,
                created_at: report.created_at,
                updated_at: report.updated_at,
                report_count: assignedReports.filter(r => r.cycle_id === report.cycle_id).length,
              });
            }
          });
          
          const cycles = Array.from(cycleMap.values());
          
          // Apply pagination
          const startIndex = page * rowsPerPage;
          const endIndex = startIndex + rowsPerPage;
          const paginatedCycles = cycles.slice(startIndex, endIndex);
          
          return {
            items: paginatedCycles,
            total: cycles.length,
            page: page + 1,
            per_page: rowsPerPage,
            pages: Math.ceil(cycles.length / rowsPerPage)
          };
        } catch (error) {
          console.error('Error fetching tester cycles:', error);
          return {
            items: [],
            total: 0,
            page: page + 1,
            per_page: rowsPerPage,
            pages: 0
          };
        }
      } else {
        // For other roles, get all cycles
        return cyclesApi.getAll(page + 1, rowsPerPage);
      }
    },
    enabled: !!user?.user_id,
  });

  // Query for aggregated cycle and report metrics
  const { data: aggregatedMetrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['cycles-aggregated-metrics', user?.role, user?.user_id],
    queryFn: async () => {
      try {
        let cycles = [];
        
        if (user?.role === 'Tester') {
          // For testers, only get cycles they have assignments for
          const assignedReports = await reportsApi.getByTester(user?.user_id || 0);
          const cycleMap = new Map();
          assignedReports.forEach((report: any) => {
            if (!cycleMap.has(report.cycle_id)) {
              cycleMap.set(report.cycle_id, {
                cycle_id: report.cycle_id,
                cycle_name: report.cycle_name || `Cycle ${report.cycle_id}`,
                status: 'Active',
              });
            }
          });
          cycles = Array.from(cycleMap.values());
        } else {
          // For other roles, get all cycles
          const cyclesResponse = await cyclesApi.getAll(1, 1000);
          cycles = cyclesResponse.items || [];
        }
        
        // Fetch reports for cycles
        let cycleReportsData = [];
        
        if (user?.role === 'Tester') {
          // For testers, use their assigned reports directly
          const assignedReports = await reportsApi.getByTester(user?.user_id || 0);
          
          // Group assigned reports by cycle
          const cycleReportsMap = new Map();
          assignedReports.forEach((report: any) => {
            if (!cycleReportsMap.has(report.cycle_id)) {
              cycleReportsMap.set(report.cycle_id, {
                cycleId: report.cycle_id,
                cycleName: report.cycle_name || `Cycle ${report.cycle_id}`,
                cycleStatus: 'Active',
                reports: []
              });
            }
            cycleReportsMap.get(report.cycle_id).reports.push(report);
          });
          
          cycleReportsData = Array.from(cycleReportsMap.values());
        } else {
          // For other roles, fetch all reports for all cycles
          const reportPromises = cycles.map(async (cycle) => {
            try {
              const response = await apiClient.get(`/cycles/${cycle.cycle_id}/reports`);
              return {
                cycleId: cycle.cycle_id,
                cycleName: cycle.cycle_name,
                cycleStatus: cycle.status,
                reports: response.data || []
              };
            } catch (error) {
              console.error(`Error fetching reports for cycle ${cycle.cycle_id}:`, error);
              return {
                cycleId: cycle.cycle_id,
                cycleName: cycle.cycle_name,
                cycleStatus: cycle.status,
                reports: []
              };
            }
          });
          
          cycleReportsData = await Promise.all(reportPromises);
        }
        
        // Calculate aggregated metrics
        let totalReports = 0;
        let completedReports = 0;
        let inProgressReports = 0;
        let notStartedReports = 0;
        let totalIssues = 0;
        let assignedReports = 0;
        let unassignedReports = 0;
        
        cycleReportsData.forEach(cycleData => {
          cycleData.reports.forEach((report: any) => {
            totalReports++;
            
            switch (report.status) {
              case 'Complete':
                completedReports++;
                break;
              case 'In Progress':
                inProgressReports++;
                break;
              case 'Not Started':
              default:
                notStartedReports++;
                break;
            }
            
            totalIssues += report.issues_count || 0;
            
            if (report.tester_id) {
              assignedReports++;
            } else {
              unassignedReports++;
            }
          });
        });
        
        return {
          // Cycle metrics
          totalCycles: cycles.length,
          activeCycles: cycles.filter(c => c.status === CycleStatus.ACTIVE).length,
          completedCycles: cycles.filter(c => c.status === CycleStatus.COMPLETED).length,
          
          // Report metrics
          totalReports,
          completedReports,
          inProgressReports,
          notStartedReports,
          totalIssues,
          assignedReports,
          unassignedReports,
          
          // Calculated metrics
          completionRate: totalReports > 0 ? Math.round((completedReports / totalReports) * 100) : 0,
          assignmentRate: totalReports > 0 ? Math.round((assignedReports / totalReports) * 100) : 0
        };
      } catch (error) {
        console.error('Error fetching aggregated metrics:', error);
        return null;
      }
    },
    enabled: !!cyclesData?.items.length,
    refetchOnWindowFocus: false,
  });

  // Query for reports (to show in cycle details)
  const {
    data: reportsData,
  } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportsApi.getAll(1, 100), // Get all reports to match with cycles
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: cyclesApi.create,
    onSuccess: (data) => {
      console.log('Cycle created successfully:', data);
      // Invalidate all relevant queries to refresh metrics
      queryClient.invalidateQueries({ queryKey: ['cycles'] });
      queryClient.invalidateQueries({ queryKey: ['cycles-executive'] });
      queryClient.invalidateQueries({ queryKey: ['test-executive-metrics-redesigned'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
      setOpenCreateDialog(false);
      resetForm();
    },
    onError: (error) => {
      console.error('Error creating cycle:', error);
      // You can add a toast notification here if you have one set up
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateTestCycleRequest }) => 
      cyclesApi.update(id, data),
    onSuccess: () => {
      // Invalidate all relevant queries to refresh metrics
      queryClient.invalidateQueries({ queryKey: ['cycles'] });
      queryClient.invalidateQueries({ queryKey: ['cycles-executive'] });
      queryClient.invalidateQueries({ queryKey: ['test-executive-metrics-redesigned'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      setOpenEditDialog(false);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: cyclesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycles'] });
      handleCloseMenu();
    },
  });

  const resetForm = () => {
    setFormData({
      cycle_name: '',
      description: '',
      start_date: new Date().toISOString().split('T')[0],
      end_date: '',
    });
    setSelectedCycle(null);
  };

  const handleCreate = () => {
    setOpenCreateDialog(true);
    resetForm();
  };

  const handleEdit = (cycle: TestCycle) => {
    setSelectedCycle(cycle);
    setFormData({
      cycle_name: cycle.cycle_name,
      description: cycle.description || '',
      start_date: cycle.start_date.split('T')[0],
      end_date: cycle.end_date ? cycle.end_date.split('T')[0] : '',
    });
    setOpenEditDialog(true);
    handleCloseMenu();
  };

  const handleView = (cycle: TestCycle) => {
    navigate(`/cycles/${cycle.cycle_id}`);
    handleCloseMenu();
  };

  const handleAddReports = (cycle: TestCycle) => {
    setSelectedCycle(cycle);
    setOpenAddReportsDialog(true);
    handleCloseMenu();
  };

  const handleDelete = (cycle: TestCycle) => {
    if (window.confirm(`Are you sure you want to delete "${cycle.cycle_name}"?`)) {
      deleteMutation.mutate(cycle.cycle_id);
    }
  };

  const handleStartCycle = async (cycle: TestCycle) => {
    try {
      await updateMutation.mutateAsync({
        id: cycle.cycle_id,
        data: { status: 'Active' }
      });
      showToast('success', 'Test cycle started successfully');
      handleCloseMenu();
    } catch (error) {
      showToast('error', 'Failed to start test cycle');
    }
  };

  const handleSubmitCreate = () => {
    const submitData = {
      ...formData,
      end_date: formData.end_date || undefined // Convert empty string to undefined
    };
    createMutation.mutate(submitData);
  };

  const handleSubmitEdit = () => {
    if (selectedCycle) {
      const submitData = {
        ...formData,
        end_date: formData.end_date || undefined // Convert empty string to undefined
      };
      updateMutation.mutate({
        id: selectedCycle.cycle_id,
        data: submitData
      });
    }
  };

  const handleMenu = (event: React.MouseEvent<HTMLElement>, cycle: TestCycle) => {
    setAnchorEl(event.currentTarget);
    setMenuCycle(cycle);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
    setMenuCycle(null);
  };

  const getStatusColor = (status: CycleStatus | string) => {
    const statusUpper = status.toUpperCase();
    switch (statusUpper) {
      case 'ACTIVE':
      case CycleStatus.ACTIVE:
        return 'success';
      case 'COMPLETED':
      case CycleStatus.COMPLETED:
        return 'info';
      case 'CANCELLED':
      case CycleStatus.CANCELLED:
        return 'error';
      case 'PLANNING':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: CycleStatus | string) => {
    const statusUpper = status.toUpperCase();
    switch (statusUpper) {
      case 'ACTIVE':
      case CycleStatus.ACTIVE:
        return <StartIcon fontSize="small" />;
      case 'COMPLETED':
      case CycleStatus.COMPLETED:
        return <StopIcon fontSize="small" />;
      case 'PLANNING':
        return <Schedule fontSize="small" />;
      default:
        return undefined;
    }
  };

  // Helper functions for cycle progress and reports
  const getCycleReports = async (cycleId: number) => {
    try {
      const response = await apiClient.get(`/cycles/${cycleId}/reports`);
      return response.data || [];
    } catch (error) {
      console.error('Error fetching cycle reports:', error);
      return [];
    }
  };

  const calculateCycleProgress = (reports: any[]) => {
    if (reports.length === 0) return 0;
    
    // Calculate based on report completion status
    const completedReports = reports.filter((report: any) => report.status === 'Complete').length;
    return Math.round((completedReports / reports.length) * 100);
  };

  const getCycleMetrics = (reports: any[]) => {
    return {
      totalReports: reports.length,
      completedReports: reports.filter((report: any) => report.status === 'Complete').length,
      inProgressReports: reports.filter((report: any) => report.status === 'In Progress').length,
      pendingReports: reports.filter((report: any) => report.status === 'Not Started').length,
      issuesCount: reports.reduce((sum: number, report: any) => sum + (report.issues_count || 0), 0),
      progress: calculateCycleProgress(reports)
    };
  };

  const getDaysRemaining = (endDate: string | null) => {
    if (!endDate) return null;
    const end = new Date(endDate);
    const today = new Date();
    const diffTime = end.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  // Check if user is Test Executive (can manage cycles and add reports)
  const isTestManager = (user?.role as string) === 'Test Executive';

  // Check if we should open create dialog based on route
  useEffect(() => {
    if (location.pathname === '/cycles/new') {
      setOpenCreateDialog(true);
      // Update URL to remove /new without adding to history
      navigate('/cycles', { replace: true });
    }
  }, [location.pathname, navigate]);

  const handleCycleClick = (cycleId: number) => {
    navigate(`/cycles/${cycleId}`);
  };

  // Function to fetch reports for a specific cycle
  const fetchCycleReports = async (cycleId: number) => {
    if (cycleReports[cycleId]) {
      return cycleReports[cycleId]; // Return cached data
    }
    
    const reports = await getCycleReports(cycleId);
    setCycleReports(prev => ({ ...prev, [cycleId]: reports }));
    return reports;
  };
  
  // Get cached reports or return empty array
  const getCachedCycleReports = (cycleId: number) => {
    return cycleReports[cycleId] || [];
  };

  // Effect to fetch cycle reports when cycles change or when a cycle is expanded
  useEffect(() => {
    if (expandedCycle && !cycleReports[expandedCycle]) {
      fetchCycleReports(expandedCycle);
    }
  }, [expandedCycle]);

  // Function to handle cycle expansion and fetch reports
  const handleCycleExpansion = (cycleId: number) => {
    const wasExpanded = expandedCycle === cycleId;
    setExpandedCycle(wasExpanded ? null : cycleId);
    
    // Fetch reports if expanding and not already loaded
    if (!wasExpanded && !cycleReports[cycleId]) {
      fetchCycleReports(cycleId);
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load test cycles. Please try again.
      </Alert>
    );
  }

  const cycles = cyclesData?.items || [];
  const totalCount = cyclesData?.total || 0;
  
  // Debug logging
  console.log('TestCyclesPage Debug:', {
    cyclesData,
    cyclesLength: cycles.length,
    totalCount,
    page,
    rowsPerPage,
    userRole: user?.role
  });

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4">Test Cycles</Typography>
          <Typography variant="body2" color="text.secondary">
            Manage and monitor your testing cycles with real-time progress tracking
          </Typography>
        </Box>
        <PermissionGate resource="cycles" action="create">
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Create Test Cycle
          </Button>
        </PermissionGate>
      </Box>

      {/* Overview Stats - First Row Only */}
      {aggregatedMetrics && !metricsLoading && (
        <Box 
          sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: 'repeat(1, 1fr)', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)', lg: 'repeat(6, 1fr)' },
            gap: 3,
            mb: 4 
          }}
        >
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="success.main">
                    {aggregatedMetrics.activeCycles}
                  </Typography>
                  <Typography variant="subtitle2">Active Cycles</Typography>
                </Box>
                <PlayArrow color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="info.main">
                    {aggregatedMetrics.totalReports}
                  </Typography>
                  <Typography variant="subtitle2">Reports Assigned</Typography>
                </Box>
                <Assessment color="info" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="warning.main">
                    {aggregatedMetrics.inProgressReports}
                  </Typography>
                  <Typography variant="subtitle2">Active Reports</Typography>
                </Box>
                <Timeline color="warning" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="success.main">
                    {aggregatedMetrics.completedReports}
                  </Typography>
                  <Typography variant="subtitle2">Completed Reports</Typography>
                </Box>
                <CheckCircle color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="text.secondary">
                    {aggregatedMetrics.notStartedReports}
                  </Typography>
                  <Typography variant="subtitle2">Pending Reports</Typography>
                </Box>
                <Schedule color="action" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" color="error.main">
                    {aggregatedMetrics.totalIssues}
                  </Typography>
                  <Typography variant="subtitle2">Observations</Typography>
                </Box>
                <Warning color="error" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Cycle Cards */}
      {cycles.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <CycleIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No Test Cycles Found
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Create your first test cycle to start managing your testing workflows and tracking progress.
          </Typography>
          <PermissionGate resource="cycles" action="create">
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreate}
            >
              Create Your First Cycle
            </Button>
          </PermissionGate>
        </Paper>
      ) : (
        <Box display="flex" flexDirection="column" gap={2}>
          {cycles.map((cycle) => {
            const reports = getCachedCycleReports(cycle.cycle_id);
            const metrics = getCycleMetrics(reports);
            const daysRemaining = getDaysRemaining(cycle.end_date || null);
            const isExpanded = expandedCycle === cycle.cycle_id;

            return (
              <Card key={cycle.cycle_id} sx={{ overflow: 'visible' }}>
                {/* Header with Action Button */}
                <Box sx={{ display: 'flex', alignItems: 'center', p: 2, pb: 0 }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography 
                      variant="h6" 
                      sx={{ 
                        cursor: 'pointer',
                        '&:hover': { textDecoration: 'underline' }
                      }}
                      onClick={() => handleCycleClick(cycle.cycle_id)}
                    >
                      {cycle.cycle_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {cycle.description || 'No description provided'}
                    </Typography>
                    {cycle.status === 'Planning' && (
                      <Typography variant="caption" color="warning.main" sx={{ mt: 0.5, display: 'block' }}>
                        ⚡ Add reports and start this cycle to begin testing
                      </Typography>
                    )}
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Chip
                      label={cycle.status.toUpperCase()}
                      color={getStatusColor(cycle.status)}
                      size="medium"
                      icon={getStatusIcon(cycle.status)}
                      sx={{ fontWeight: 'bold' }}
                    />
                    
                    {daysRemaining !== null && (
                      <Chip
                        label={daysRemaining > 0 ? `${daysRemaining} days left` : 'Overdue'}
                        color={daysRemaining > 7 ? 'default' : daysRemaining > 0 ? 'warning' : 'error'}
                        size="small"
                        icon={<Schedule />}
                      />
                    )}
                    
                    {/* Inline action buttons for better visibility */}
                    {cycle.status === 'Planning' && isTestManager && (
                      <>
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<PersonAddIcon />}
                          onClick={() => handleAddReports(cycle)}
                        >
                          Add Reports
                        </Button>
                        <Button
                          size="small"
                          variant="contained"
                          color="success"
                          startIcon={<PlayArrow />}
                          onClick={() => handleStartCycle(cycle)}
                        >
                          Start Cycle
                        </Button>
                      </>
                    )}
                    
                    {cycle.status === 'Active' && isTestManager && (
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<PersonAddIcon />}
                        onClick={() => handleAddReports(cycle)}
                      >
                        Add Reports
                      </Button>
                    )}
                    
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenu(e, cycle)}
                    >
                      <MoreVertIcon />
                    </IconButton>
                  </Box>
                </Box>

                <Accordion 
                  expanded={isExpanded}
                  onChange={() => handleCycleExpansion(cycle.cycle_id)}
                >
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="body2" color="text.secondary">
                      Click to view cycle details and reports
                    </Typography>
                  </AccordionSummary>
                  
                  <AccordionDetails>
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
                      {/* Progress Overview */}
                      <Box>
                        <Typography variant="subtitle1" gutterBottom>
                          Progress Overview
                        </Typography>
                        <Box sx={{ mb: 2 }}>
                          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                            <Typography variant="body2">Overall Progress</Typography>
                            <Typography variant="body2" color="text.secondary">
                              {metrics.progress}%
                            </Typography>
                          </Box>
                          <LinearProgress 
                            variant="determinate" 
                            value={metrics.progress} 
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                        
                        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                          <Box textAlign="center" p={1}>
                            <Typography variant="h6" color="success.main">
                              {metrics.completedReports}
                            </Typography>
                            <Typography variant="caption">Completed</Typography>
                          </Box>
                          <Box textAlign="center" p={1}>
                            <Typography variant="h6" color="info.main">
                              {metrics.inProgressReports}
                            </Typography>
                            <Typography variant="caption">In Progress</Typography>
                          </Box>
                        </Box>
                      </Box>
                      
                      {/* Cycle Details */}
                      <Box>
                        <Typography variant="subtitle1" gutterBottom>
                          Cycle Details
                        </Typography>
                        <List dense>
                          <ListItem>
                            <ListItemIcon><Schedule /></ListItemIcon>
                            <ListItemText
                              primary="Start Date"
                              secondary={new Date(cycle.start_date).toLocaleDateString()}
                            />
                          </ListItem>
                          {cycle.end_date && (
                            <ListItem>
                              <ListItemIcon><Schedule /></ListItemIcon>
                              <ListItemText
                                primary="End Date"
                                secondary={new Date(cycle.end_date).toLocaleDateString()}
                              />
                            </ListItem>
                          )}
                          <ListItem>
                            <ListItemIcon><Assessment /></ListItemIcon>
                            <ListItemText
                              primary="Total Reports"
                              secondary={`${metrics.totalReports} reports assigned`}
                            />
                          </ListItem>
                        </List>
                      </Box>
                    </Box>
                    
                    {/* Reports in Cycle */}
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Reports in This Cycle
                      </Typography>
                      {reports.length === 0 ? (
                        <Box textAlign="center" py={2}>
                          <Typography variant="body2" color="text.secondary">
                            No reports assigned to this cycle yet.
                          </Typography>
                        </Box>
                      ) : (
                        <Box>
                          {reports.map((report: any) => (
                            <Box 
                              key={report.report_id} 
                              sx={{ 
                                display: 'flex', 
                                justifyContent: 'space-between', 
                                alignItems: 'center',
                                p: 1, 
                                mb: 1, 
                                bgcolor: 'grey.50', 
                                borderRadius: 1 
                              }}
                            >
                              <Box>
                                <Typography variant="subtitle2">
                                  {report.report_name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  LOB: {report.lob_name} | Tester: {report.tester_name || 'Unassigned'}
                                </Typography>
                              </Box>
                              <Chip 
                                label={report.status || 'Not Started'} 
                                size="small"
                                color={
                                  report.status === 'Complete' ? 'success' :
                                  report.status === 'In Progress' ? 'primary' : 'default'
                                }
                              />
                            </Box>
                          ))}
                        </Box>
                      )}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              </Card>
            );
          })}
        </Box>
      )}

      {/* Pagination */}
      {totalCount > rowsPerPage && (
        <Box mt={3}>
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
        </Box>
      )}

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
      >
        <MuiMenuItem onClick={() => menuCycle && handleView(menuCycle)}>
          <ViewIcon sx={{ mr: 1 }} />
          View Details
        </MuiMenuItem>
        {hasPermission('cycles', 'update') && (
          <MuiMenuItem onClick={() => menuCycle && handleEdit(menuCycle)}>
            <EditIcon sx={{ mr: 1 }} />
            Edit Cycle
          </MuiMenuItem>
        )}
        {hasPermission('cycles', 'update') && menuCycle && menuCycle.status === 'Planning' && (
          <MuiMenuItem onClick={() => menuCycle && handleStartCycle(menuCycle)}>
            <PlayArrow sx={{ mr: 1 }} />
            Start Cycle
          </MuiMenuItem>
        )}
        {hasPermission('cycles', 'assign') && menuCycle && (
          <MuiMenuItem onClick={() => menuCycle && handleAddReports(menuCycle)}>
            <PersonAddIcon sx={{ mr: 1 }} />
            Add Reports
          </MuiMenuItem>
        )}
        {hasPermission('cycles', 'delete') && (
          <MuiMenuItem 
            onClick={() => menuCycle && handleDelete(menuCycle)}
            sx={{ color: 'error.main' }}
          >
            <DeleteIcon sx={{ mr: 1 }} />
            Delete Cycle
          </MuiMenuItem>
        )}
      </Menu>

      {/* Create Dialog */}
      <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Test Cycle</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <TextField
              label="Cycle Name"
              value={formData.cycle_name}
              onChange={(e) => setFormData({ ...formData, cycle_name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <TextField
              label="Start Date"
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              fullWidth
              required
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="End Date"
              type="date"
              value={formData.end_date}
              onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSubmitCreate}
            variant="contained"
            disabled={!formData.cycle_name || createMutation.isPending}
          >
            {createMutation.isPending ? <CircularProgress size={20} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Test Cycle</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <TextField
              label="Cycle Name"
              value={formData.cycle_name}
              onChange={(e) => setFormData({ ...formData, cycle_name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <TextField
              label="Start Date"
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              fullWidth
              required
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="End Date"
              type="date"
              value={formData.end_date}
              onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSubmitEdit}
            variant="contained"
            disabled={!formData.cycle_name || updateMutation.isPending}
          >
            {updateMutation.isPending ? <CircularProgress size={20} /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Reports Dialog */}
      <AddReportsDialog
        open={openAddReportsDialog}
        onClose={() => setOpenAddReportsDialog(false)}
        cycle={selectedCycle}
        onReportsAdded={(cycleId) => {
          // Refresh cycle reports when reports are added
          fetchCycleReports(cycleId);
        }}
      />
    </Box>
  );
};

export default TestCyclesPage; 