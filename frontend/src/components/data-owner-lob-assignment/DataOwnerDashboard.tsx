import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Chip,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Badge,
  Tabs,
  Tab
} from '@mui/material';
import {
  CheckCircle as AcknowledgeIcon,
  Assignment as AssignmentIcon,
  Schedule as PendingIcon,
  FilterList as FilterIcon,
  History as HistoryIcon,
  Notifications as NotificationsIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { dataOwnerLobAssignmentApi, DataOwnerWorkloadDetail, AssignmentWithDetails } from '../../api/dataOwnerLobAssignment';

interface DataOwnerDashboardProps {
  phaseId: number;
  cycleId: number;
  reportId: number;
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
      id={`data-owner-tabpanel-${index}`}
      aria-labelledby={`data-owner-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `data-owner-tab-${index}`,
    'aria-controls': `data-owner-tabpanel-${index}`,
  };
}

const DataOwnerDashboard: React.FC<DataOwnerDashboardProps> = ({
  phaseId,
  cycleId,
  reportId
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workload, setWorkload] = useState<DataOwnerWorkloadDetail | null>(null);
  const [filteredAssignments, setFilteredAssignments] = useState<AssignmentWithDetails[]>([]);
  const [activeTab, setActiveTab] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  
  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [lobFilter, setLobFilter] = useState<string>('');
  
  // Acknowledgment dialog
  const [showAckDialog, setShowAckDialog] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<AssignmentWithDetails | null>(null);
  const [ackNotes, setAckNotes] = useState('');
  const [ackLoading, setAckLoading] = useState(false);

  const loadWorkloadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const workloadData = await dataOwnerLobAssignmentApi.getMyAssignments(phaseId);
      setWorkload(workloadData);
      setFilteredAssignments(workloadData.assignments);
    } catch (err: any) {
      console.error('Error loading workload data:', err);
      setError(err.response?.data?.detail || 'Failed to load your assignments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkloadData();
  }, [phaseId, refreshKey]);

  useEffect(() => {
    applyFilters();
  }, [workload, statusFilter, lobFilter]);

  const applyFilters = () => {
    if (!workload) return;

    let filtered = [...workload.assignments];

    if (statusFilter) {
      filtered = filtered.filter(a => a.assignment_status === statusFilter);
    }

    if (lobFilter) {
      filtered = filtered.filter(a => a.lob_id.toString() === lobFilter);
    }

    setFilteredAssignments(filtered);
    setPage(0);
  };

  const handleAcknowledge = async () => {
    if (!selectedAssignment) return;

    try {
      setAckLoading(true);
      
      await dataOwnerLobAssignmentApi.acknowledgeAssignment(
        selectedAssignment.assignment_id,
        { response_notes: ackNotes.trim() || undefined }
      );

      setShowAckDialog(false);
      setSelectedAssignment(null);
      setAckNotes('');
      setRefreshKey(prev => prev + 1);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to acknowledge assignment');
    } finally {
      setAckLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'assigned': return 'success';
      case 'unassigned': return 'warning';
      case 'changed': return 'info';
      case 'confirmed': return 'primary';
      default: return 'default';
    }
  };

  const getUniqueValues = (key: keyof AssignmentWithDetails) => {
    if (!workload) return [];
    return Array.from(new Set(workload.assignments.map(a => a[key]).filter(Boolean)));
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="body2" sx={{ ml: 2 }}>
          Loading your assignments...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
        <Button onClick={() => setRefreshKey(prev => prev + 1)} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  if (!workload || workload.total_assignments === 0) {
    return (
      <Alert severity="info">
        You have no assignments for this phase currently.
      </Alert>
    );
  }

  const pendingAssignments = workload.assignments.filter(a => !a.data_owner_acknowledged);
  const paginatedAssignments = filteredAssignments.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Box>
      {/* Header Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
          <Typography variant="h5" component="h1">
            My Data Owner Assignments
          </Typography>
          <Badge badgeContent={pendingAssignments.length} color="warning">
            <NotificationsIcon />
          </Badge>
        </Box>

        {/* Summary Cards */}
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 3 }}>
            <Card variant="outlined">
              <CardContent>
                <Box display="flex" alignItems="center">
                  <AssignmentIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Total Assignments</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {workload.total_assignments}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, md: 3 }}>
            <Card variant="outlined">
              <CardContent>
                <Box display="flex" alignItems="center">
                  <AcknowledgeIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6">Acknowledged</Typography>
                </Box>
                <Typography variant="h4" color="success.main">
                  {workload.acknowledged_assignments}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, md: 3 }}>
            <Card variant="outlined">
              <CardContent>
                <Box display="flex" alignItems="center">
                  <PendingIcon color="warning" sx={{ mr: 1 }} />
                  <Typography variant="h6">Pending</Typography>
                </Box>
                <Typography variant="h4" color="warning.main">
                  {workload.pending_assignments}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, md: 3 }}>
            <Card variant="outlined">
              <CardContent>
                <Box display="flex" alignItems="center">
                  <PersonIcon color="info" sx={{ mr: 1 }} />
                  <Typography variant="h6">Completion Rate</Typography>
                </Box>
                <Typography variant="h4" color="info.main">
                  {workload.total_assignments > 0 ? 
                    Math.round((workload.acknowledged_assignments / workload.total_assignments) * 100) : 0}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Main Content */}
      <Paper>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange}>
            <Tab 
              label={
                <Badge badgeContent={pendingAssignments.length} color="warning">
                  <span>Pending Acknowledgments</span>
                </Badge>
              } 
              {...a11yProps(0)} 
            />
            <Tab label="All Assignments" {...a11yProps(1)} />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          {/* Pending Acknowledgments Tab */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Assignments Requiring Your Acknowledgment
            </Typography>
            
            {pendingAssignments.length === 0 ? (
              <Alert severity="success">
                All assignments have been acknowledged! Great job!
              </Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>LOB</TableCell>
                      <TableCell>Attribute</TableCell>
                      <TableCell>Sample</TableCell>
                      <TableCell>Assigned Date</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Rationale</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {pendingAssignments.map((assignment) => (
                      <TableRow key={assignment.assignment_id}>
                        <TableCell>{assignment.lob_name || `LOB ${assignment.lob_id}`}</TableCell>
                        <TableCell>{assignment.attribute_name || `Attribute ${assignment.attribute_id}`}</TableCell>
                        <TableCell>{assignment.sample_id}</TableCell>
                        <TableCell>
                          {new Date(assignment.assigned_by_data_executive_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={assignment.assignment_status}
                            color={getStatusColor(assignment.assignment_status) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ maxWidth: 200 }}>
                            {assignment.assignment_rationale || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Tooltip title="Acknowledge Assignment">
                            <IconButton
                              color="primary"
                              onClick={() => {
                                setSelectedAssignment(assignment);
                                setShowAckDialog(true);
                              }}
                            >
                              <AcknowledgeIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {/* All Assignments Tab */}
          <Box>
            {/* Filters */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid size={{ xs: 12, md: 4 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Status Filter</InputLabel>
                  <Select
                    value={statusFilter}
                    label="Status Filter"
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <MenuItem value="">All Statuses</MenuItem>
                    <MenuItem value="assigned">Assigned</MenuItem>
                    <MenuItem value="changed">Changed</MenuItem>
                    <MenuItem value="confirmed">Confirmed</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid size={{ xs: 12, md: 4 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>LOB Filter</InputLabel>
                  <Select
                    value={lobFilter}
                    label="LOB Filter"
                    onChange={(e) => setLobFilter(e.target.value)}
                  >
                    <MenuItem value="">All LOBs</MenuItem>
                    {getUniqueValues('lob_id').map((lobId) => (
                      <MenuItem key={String(lobId)} value={String(lobId)}>
                        {workload.assignments.find(a => a.lob_id === lobId)?.lob_name || `LOB ${lobId}`}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid size={{ xs: 12, md: 4 }}>
                <Button
                  variant="outlined"
                  onClick={() => {
                    setStatusFilter('');
                    setLobFilter('');
                  }}
                  fullWidth
                >
                  Clear Filters
                </Button>
              </Grid>
            </Grid>

            {/* Assignments Table */}
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>LOB</TableCell>
                    <TableCell>Attribute</TableCell>
                    <TableCell>Sample</TableCell>
                    <TableCell>Assigned Date</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Acknowledged</TableCell>
                    <TableCell>Rationale</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedAssignments.map((assignment) => (
                    <TableRow key={assignment.assignment_id}>
                      <TableCell>{assignment.lob_name || `LOB ${assignment.lob_id}`}</TableCell>
                      <TableCell>{assignment.attribute_name || `Attribute ${assignment.attribute_id}`}</TableCell>
                      <TableCell>{assignment.sample_id}</TableCell>
                      <TableCell>
                        {new Date(assignment.assigned_by_data_executive_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={assignment.assignment_status}
                          color={getStatusColor(assignment.assignment_status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {assignment.data_owner_acknowledged ? (
                          <Chip label="Yes" color="success" size="small" />
                        ) : (
                          <Chip label="No" color="warning" size="small" />
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 200 }}>
                          {assignment.assignment_rationale || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {!assignment.data_owner_acknowledged && (
                          <Tooltip title="Acknowledge Assignment">
                            <IconButton
                              color="primary"
                              onClick={() => {
                                setSelectedAssignment(assignment);
                                setShowAckDialog(true);
                              }}
                            >
                              <AcknowledgeIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            
            <TablePagination
              rowsPerPageOptions={[25, 50, 100]}
              component="div"
              count={filteredAssignments.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={(_, newPage) => setPage(newPage)}
              onRowsPerPageChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
            />
          </Box>
        </TabPanel>
      </Paper>

      {/* Acknowledgment Dialog */}
      <Dialog open={showAckDialog} onClose={() => setShowAckDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Acknowledge Assignment</DialogTitle>
        <DialogContent>
          {selectedAssignment && (
            <Box>
              <Typography variant="body1" gutterBottom>
                Are you confirming your assignment to:
              </Typography>
              
              <Box sx={{ ml: 2, mb: 2 }}>
                <Typography variant="body2">
                  <strong>LOB:</strong> {selectedAssignment.lob_name || `LOB ${selectedAssignment.lob_id}`}
                </Typography>
                <Typography variant="body2">
                  <strong>Attribute:</strong> {selectedAssignment.attribute_name || `Attribute ${selectedAssignment.attribute_id}`}
                </Typography>
                <Typography variant="body2">
                  <strong>Sample:</strong> {selectedAssignment.sample_id}
                </Typography>
              </Box>

              {selectedAssignment.assignment_rationale && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Assignment Rationale:</strong>
                  </Typography>
                  <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                    "{selectedAssignment.assignment_rationale}"
                  </Typography>
                </Box>
              )}

              <TextField
                fullWidth
                label="Response Notes (Optional)"
                multiline
                rows={3}
                value={ackNotes}
                onChange={(e) => setAckNotes(e.target.value)}
                placeholder="Any comments or concerns about this assignment..."
                sx={{ mt: 2 }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAckDialog(false)} disabled={ackLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleAcknowledge}
            variant="contained"
            disabled={ackLoading}
            startIcon={ackLoading ? <CircularProgress size={16} /> : <AcknowledgeIcon />}
          >
            Acknowledge
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DataOwnerDashboard;