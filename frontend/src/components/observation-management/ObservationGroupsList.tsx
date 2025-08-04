import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  IconButton,
  Tooltip,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Stack
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Visibility,
  Edit,
  CheckCircle,
  Cancel,
  Warning,
  Schedule,
  Assessment,
  FilterList,
  Refresh
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

interface ObservationGroup {
  id: number;
  group_name: string;
  group_description?: string;
  issue_summary: string;
  observation_count: number;
  severity_level: 'high' | 'medium' | 'low';
  issue_type: 'data_quality' | 'process_failure' | 'system_error' | 'compliance_gap';
  status: 'draft' | 'pending_tester_review' | 'tester_approved' | 'pending_report_owner_approval' | 'report_owner_approved' | 'rejected' | 'resolved' | 'closed';
  created_at: string;
  updated_at: string;
  attribute?: {
    id: number;
    name: string;
    description?: string;
  };
  lob?: {
    id: number;
    name: string;
    description?: string;
  };
  detector?: {
    id: number;
    name: string;
    email: string;
  };
  tester_reviewer?: {
    id: number;
    name: string;
    email: string;
  };
  report_owner_approver?: {
    id: number;
    name: string;
    email: string;
  };
}

interface ObservationGroupsListProps {
  phaseId?: number;
  cycleId?: number;
  reportId?: number;
  onGroupSelect?: (group: ObservationGroup) => void;
  onGroupEdit?: (group: ObservationGroup) => void;
  onGroupReview?: (group: ObservationGroup) => void;
  onGroupApprove?: (group: ObservationGroup) => void;
}

const ObservationGroupsList: React.FC<ObservationGroupsListProps> = ({
  phaseId,
  cycleId,
  reportId,
  onGroupSelect,
  onGroupEdit,
  onGroupReview,
  onGroupApprove
}) => {
  const theme = useTheme();
  const [groups, setGroups] = useState<ObservationGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  
  // Filters
  const [filters, setFilters] = useState({
    status: '',
    severity_level: '',
    assigned_to: '',
    search: ''
  });
  const [showFilters, setShowFilters] = useState(false);
  
  // Dialog states
  const [selectedGroup, setSelectedGroup] = useState<ObservationGroup | null>(null);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  
  useEffect(() => {
    fetchGroups();
  }, [page, rowsPerPage, filters, phaseId, cycleId, reportId]);
  
  const fetchGroups = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (phaseId) params.append('phase_id', phaseId.toString());
      if (cycleId) params.append('cycle_id', cycleId.toString());
      if (reportId) params.append('report_id', reportId.toString());
      if (filters.status) params.append('status', filters.status);
      if (filters.severity_level) params.append('severity_level', filters.severity_level);
      if (filters.assigned_to) params.append('assigned_to', filters.assigned_to);
      params.append('page', (page + 1).toString());
      params.append('page_size', rowsPerPage.toString());
      
      const response = await fetch(`/api/v1/observation-management-unified/groups?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch observation groups');
      }
      
      const data = await response.json();
      setGroups(data.groups || []);
      setTotalCount(data.pagination?.total_count || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
    setPage(0);
  };
  
  const handleViewDetails = (group: ObservationGroup) => {
    setSelectedGroup(group);
    setDetailsDialogOpen(true);
    if (onGroupSelect) {
      onGroupSelect(group);
    }
  };
  
  const handleCloseDetails = () => {
    setDetailsDialogOpen(false);
    setSelectedGroup(null);
  };
  
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return theme.palette.error.main;
      case 'medium': return theme.palette.warning.main;
      case 'low': return theme.palette.info.main;
      default: return theme.palette.grey[500];
    }
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return theme.palette.grey[500];
      case 'pending_tester_review': return theme.palette.warning.main;
      case 'tester_approved': return theme.palette.info.main;
      case 'pending_report_owner_approval': return theme.palette.warning.main;
      case 'report_owner_approved': return theme.palette.success.main;
      case 'rejected': return theme.palette.error.main;
      case 'resolved': return theme.palette.success.main;
      case 'closed': return theme.palette.grey[600];
      default: return theme.palette.grey[500];
    }
  };
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft': return <Edit />;
      case 'pending_tester_review': return <Schedule />;
      case 'tester_approved': return <CheckCircle />;
      case 'pending_report_owner_approval': return <Schedule />;
      case 'report_owner_approved': return <CheckCircle />;
      case 'rejected': return <Cancel />;
      case 'resolved': return <CheckCircle />;
      case 'closed': return <CheckCircle />;
      default: return <Warning />;
    }
  };
  
  const formatStatus = (status: string) => {
    return status.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };
  
  const canReview = (group: ObservationGroup) => {
    return group.status === 'pending_tester_review';
  };
  
  const canApprove = (group: ObservationGroup) => {
    return group.status === 'pending_report_owner_approval';
  };
  
  const canEdit = (group: ObservationGroup) => {
    return group.status === 'draft' || group.status === 'rejected';
  };
  
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }
  
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
        <Button onClick={fetchGroups} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" component="h1">
          Observation Groups
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<FilterList />}
            onClick={() => setShowFilters(!showFilters)}
          >
            Filters
          </Button>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchGroups}
          >
            Refresh
          </Button>
        </Stack>
      </Box>
      
      {/* Filters */}
      {showFilters && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <FormControl fullWidth>
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={filters.status}
                    label="Status"
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="draft">Draft</MenuItem>
                    <MenuItem value="pending_tester_review">Pending Tester Review</MenuItem>
                    <MenuItem value="tester_approved">Tester Approved</MenuItem>
                    <MenuItem value="pending_report_owner_approval">Pending Report Owner Approval</MenuItem>
                    <MenuItem value="report_owner_approved">Report Owner Approved</MenuItem>
                    <MenuItem value="rejected">Rejected</MenuItem>
                    <MenuItem value="resolved">Resolved</MenuItem>
                    <MenuItem value="closed">Closed</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <FormControl fullWidth>
                  <InputLabel>Severity</InputLabel>
                  <Select
                    value={filters.severity_level}
                    label="Severity"
                    onChange={(e) => handleFilterChange('severity_level', e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="low">Low</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 6 }}>
                <TextField
                  fullWidth
                  label="Search"
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  placeholder="Search by group name, description, or issue summary"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}
      
      {/* Groups Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Group Name</TableCell>
              <TableCell>Attribute</TableCell>
              <TableCell>LOB</TableCell>
              <TableCell>Observations</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {groups.map((group) => (
              <TableRow key={group.id} hover>
                <TableCell>
                  <Typography variant="subtitle2" fontWeight="bold">
                    {group.group_name}
                  </Typography>
                  {group.group_description && (
                    <Typography variant="body2" color="text.secondary">
                      {group.group_description}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {group.attribute && (
                    <Typography variant="body2">
                      {group.attribute.name}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {group.lob && (
                    <Typography variant="body2">
                      {group.lob.name}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Badge badgeContent={group.observation_count} color="primary">
                    <Assessment />
                  </Badge>
                </TableCell>
                <TableCell>
                  <Chip
                    label={group.severity_level.toUpperCase()}
                    size="small"
                    sx={{
                      bgcolor: getSeverityColor(group.severity_level),
                      color: 'white',
                      fontWeight: 'bold'
                    }}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    icon={getStatusIcon(group.status)}
                    label={formatStatus(group.status)}
                    size="small"
                    sx={{
                      bgcolor: getStatusColor(group.status),
                      color: 'white'
                    }}
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {new Date(group.created_at).toLocaleDateString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1}>
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => handleViewDetails(group)}
                      >
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    {canEdit(group) && onGroupEdit && (
                      <Tooltip title="Edit Group">
                        <IconButton
                          size="small"
                          onClick={() => onGroupEdit(group)}
                        >
                          <Edit />
                        </IconButton>
                      </Tooltip>
                    )}
                    {canReview(group) && onGroupReview && (
                      <Tooltip title="Review Group">
                        <IconButton
                          size="small"
                          color="warning"
                          onClick={() => onGroupReview(group)}
                        >
                          <Schedule />
                        </IconButton>
                      </Tooltip>
                    )}
                    {canApprove(group) && onGroupApprove && (
                      <Tooltip title="Approve Group">
                        <IconButton
                          size="small"
                          color="success"
                          onClick={() => onGroupApprove(group)}
                        >
                          <CheckCircle />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Pagination */}
      <TablePagination
        rowsPerPageOptions={[10, 20, 50, 100]}
        component="div"
        count={totalCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
      
      {/* Details Dialog */}
      <Dialog
        open={detailsDialogOpen}
        onClose={handleCloseDetails}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Observation Group Details
        </DialogTitle>
        <DialogContent>
          {selectedGroup && (
            <Grid container spacing={2}>
              <Grid size={{ xs: 12 }}>
                <Typography variant="h6" gutterBottom>
                  {selectedGroup.group_name}
                </Typography>
                {selectedGroup.group_description && (
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {selectedGroup.group_description}
                  </Typography>
                )}
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">Attribute</Typography>
                <Typography variant="body2">
                  {selectedGroup.attribute?.name || 'N/A'}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">LOB</Typography>
                <Typography variant="body2">
                  {selectedGroup.lob?.name || 'N/A'}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">Observations Count</Typography>
                <Typography variant="body2">
                  {selectedGroup.observation_count}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">Severity</Typography>
                <Chip
                  label={selectedGroup.severity_level.toUpperCase()}
                  size="small"
                  sx={{
                    bgcolor: getSeverityColor(selectedGroup.severity_level),
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">Status</Typography>
                <Chip
                  icon={getStatusIcon(selectedGroup.status)}
                  label={formatStatus(selectedGroup.status)}
                  size="small"
                  sx={{
                    bgcolor: getStatusColor(selectedGroup.status),
                    color: 'white'
                  }}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">Issue Type</Typography>
                <Typography variant="body2">
                  {selectedGroup.issue_type.replace('_', ' ').toUpperCase()}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12 }}>
                <Typography variant="subtitle2">Detected By</Typography>
                <Typography variant="body2">
                  {selectedGroup.detector?.name || 'N/A'} ({selectedGroup.detector?.email || 'N/A'})
                </Typography>
              </Grid>
              <Grid size={{ xs: 12 }}>
                <Typography variant="subtitle2">Created</Typography>
                <Typography variant="body2">
                  {new Date(selectedGroup.created_at).toLocaleString()}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12 }}>
                <Typography variant="subtitle2">Last Updated</Typography>
                <Typography variant="body2">
                  {new Date(selectedGroup.updated_at).toLocaleString()}
                </Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDetails}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ObservationGroupsList;