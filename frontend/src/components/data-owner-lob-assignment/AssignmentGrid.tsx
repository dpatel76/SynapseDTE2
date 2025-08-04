import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Checkbox,
  FormControlLabel
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Assignment as AssignmentIcon,
  Delete as UnassignIcon,
  Upload as BulkIcon,
  Person as PersonIcon,
  Clear as ClearIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import { dataOwnerLobAssignmentApi, AssignmentWithDetails, AssignmentRequest, BulkAssignmentRequest } from '../../api/dataOwnerLobAssignment';
import { User } from '../../types/api';
import apiClient from '../../api/client';

interface AssignmentGridProps {
  phaseId: number;
  versionId: string;
  onAssignmentChange: () => void;
}

interface AssignmentFilters {
  lob_id?: number;
  data_owner_id?: number;
  assignment_status?: string;
  search?: string;
}

const AssignmentGrid: React.FC<AssignmentGridProps> = ({
  phaseId,
  versionId,
  onAssignmentChange
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [assignments, setAssignments] = useState<AssignmentWithDetails[]>([]);
  const [filteredAssignments, setFilteredAssignments] = useState<AssignmentWithDetails[]>([]);
  const [dataOwners, setDataOwners] = useState<User[]>([]);
  const [lobs, setLobs] = useState<any[]>([]);
  
  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  
  // Filters
  const [filters, setFilters] = useState<AssignmentFilters>({});
  const [showFilters, setShowFilters] = useState(false);
  
  // Bulk operations
  const [selectedAssignments, setSelectedAssignments] = useState<string[]>([]);
  const [showBulkDialog, setShowBulkDialog] = useState(false);
  const [bulkDataOwnerId, setBulkDataOwnerId] = useState<number | ''>('');
  const [bulkRationale, setBulkRationale] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [assignmentsData, dataOwnersData, lobsData] = await Promise.all([
        dataOwnerLobAssignmentApi.getLobAttributeAssignments(phaseId, { version_id: versionId }),
        apiClient.get('/users?role=Data Owner').then(res => res.data),
        apiClient.get('/lobs').then(res => res.data)
      ]);

      setAssignments(assignmentsData);
      setFilteredAssignments(assignmentsData);
      setDataOwners(dataOwnersData);
      setLobs(lobsData);
    } catch (err: any) {
      console.error('Error loading assignment data:', err);
      setError(err.response?.data?.detail || 'Failed to load assignment data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [phaseId, versionId]);

  useEffect(() => {
    applyFilters();
  }, [assignments, filters]);

  const applyFilters = () => {
    let filtered = [...assignments];

    if (filters.lob_id) {
      filtered = filtered.filter(a => a.lob_id === filters.lob_id);
    }

    if (filters.data_owner_id) {
      filtered = filtered.filter(a => a.data_owner_id === filters.data_owner_id);
    }

    if (filters.assignment_status) {
      filtered = filtered.filter(a => a.assignment_status === filters.assignment_status);
    }

    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(a => 
        a.attribute_name?.toLowerCase().includes(searchLower) ||
        a.lob_name?.toLowerCase().includes(searchLower) ||
        a.data_owner_name?.toLowerCase().includes(searchLower)
      );
    }

    setFilteredAssignments(filtered);
    setPage(0);
  };

  const handleAssignDataOwner = async (assignment: AssignmentWithDetails, dataOwnerId: number | null, rationale?: string) => {
    try {
      const request: AssignmentRequest = {
        phase_id: assignment.phase_id,
        sample_id: assignment.sample_id,
        attribute_id: assignment.attribute_id,
        lob_id: assignment.lob_id,
        data_owner_id: dataOwnerId || undefined,
        assignment_rationale: rationale
      };

      await dataOwnerLobAssignmentApi.createAssignment(versionId, request);
      onAssignmentChange();
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update assignment');
    }
  };

  const handleBulkAssign = async () => {
    try {
      if (!bulkDataOwnerId || selectedAssignments.length === 0) return;

      const bulkRequests: AssignmentRequest[] = selectedAssignments.map(assignmentId => {
        const assignment = assignments.find(a => a.assignment_id === assignmentId);
        if (!assignment) throw new Error('Assignment not found');

        return {
          phase_id: assignment.phase_id,
          sample_id: assignment.sample_id,
          attribute_id: assignment.attribute_id,
          lob_id: assignment.lob_id,
          data_owner_id: bulkDataOwnerId as number,
          assignment_rationale: bulkRationale.trim() || undefined
        };
      });

      const request: BulkAssignmentRequest = { assignments: bulkRequests };
      await dataOwnerLobAssignmentApi.bulkAssignDataOwners(versionId, request);
      
      setShowBulkDialog(false);
      setSelectedAssignments([]);
      setBulkDataOwnerId('');
      setBulkRationale('');
      onAssignmentChange();
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to bulk assign');
    }
  };

  const handleSelectAll = () => {
    if (selectedAssignments.length === filteredAssignments.length) {
      setSelectedAssignments([]);
    } else {
      setSelectedAssignments(filteredAssignments.map(a => a.assignment_id));
    }
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

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
        <CircularProgress />
        <Typography variant="body2" sx={{ ml: 2 }}>
          Loading assignments...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
        <Button onClick={loadData} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  const paginatedAssignments = filteredAssignments.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Box>
      {/* Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField
                fullWidth
                placeholder="Search assignments..."
                value={filters.search || ''}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                  endAdornment: filters.search && (
                    <InputAdornment position="end">
                      <IconButton
                        size="small"
                        onClick={() => setFilters({ ...filters, search: '' })}
                      >
                        <ClearIcon />
                      </IconButton>
                    </InputAdornment>
                  )
                }}
              />
            </Grid>

            <Grid size={{ xs: 12, md: 2 }}>
              <FormControl fullWidth>
                <InputLabel>LOB</InputLabel>
                <Select
                  value={filters.lob_id || ''}
                  label="LOB"
                  onChange={(e) => setFilters({ ...filters, lob_id: e.target.value as number || undefined })}
                >
                  <MenuItem value="">All LOBs</MenuItem>
                  {lobs.map((lob) => (
                    <MenuItem key={lob.lob_id} value={lob.lob_id}>
                      {lob.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid size={{ xs: 12, md: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={filters.assignment_status || ''}
                  label="Status"
                  onChange={(e) => setFilters({ ...filters, assignment_status: e.target.value || undefined })}
                >
                  <MenuItem value="">All Statuses</MenuItem>
                  <MenuItem value="assigned">Assigned</MenuItem>
                  <MenuItem value="unassigned">Unassigned</MenuItem>
                  <MenuItem value="changed">Changed</MenuItem>
                  <MenuItem value="confirmed">Confirmed</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Box display="flex" gap={1}>
                <Button
                  variant="outlined"
                  startIcon={<BulkIcon />}
                  onClick={() => setShowBulkDialog(true)}
                  disabled={selectedAssignments.length === 0}
                >
                  Bulk Assign ({selectedAssignments.length})
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => setFilters({})}
                  startIcon={<ClearIcon />}
                >
                  Clear Filters
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Assignment Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedAssignments.length === filteredAssignments.length && filteredAssignments.length > 0}
                    indeterminate={selectedAssignments.length > 0 && selectedAssignments.length < filteredAssignments.length}
                    onChange={handleSelectAll}
                  />
                </TableCell>
                <TableCell>LOB</TableCell>
                <TableCell>Attribute</TableCell>
                <TableCell>Sample</TableCell>
                <TableCell>Data Owner</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Acknowledged</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedAssignments.map((assignment) => (
                <TableRow key={assignment.assignment_id}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedAssignments.includes(assignment.assignment_id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedAssignments([...selectedAssignments, assignment.assignment_id]);
                        } else {
                          setSelectedAssignments(selectedAssignments.filter(id => id !== assignment.assignment_id));
                        }
                      }}
                    />
                  </TableCell>
                  <TableCell>{assignment.lob_name || `LOB ${assignment.lob_id}`}</TableCell>
                  <TableCell>{assignment.attribute_name || `Attribute ${assignment.attribute_id}`}</TableCell>
                  <TableCell>{assignment.sample_id}</TableCell>
                  <TableCell>
                    <FormControl size="small" sx={{ minWidth: 150 }}>
                      <Select
                        value={assignment.data_owner_id || ''}
                        onChange={(e) => handleAssignDataOwner(assignment, e.target.value as number || null)}
                        displayEmpty
                      >
                        <MenuItem value="">
                          <em>Unassigned</em>
                        </MenuItem>
                        {dataOwners.map((owner) => (
                          <MenuItem key={owner.user_id} value={owner.user_id}>
                            {owner.first_name} {owner.last_name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
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
                      <Chip label="No" color="default" size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    {assignment.data_owner_id && (
                      <Tooltip title="Unassign">
                        <IconButton
                          size="small"
                          onClick={() => handleAssignDataOwner(assignment, null, 'Unassigned via grid')}
                        >
                          <UnassignIcon />
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
      </Card>

      {/* Bulk Assignment Dialog */}
      <Dialog open={showBulkDialog} onClose={() => setShowBulkDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Bulk Assign Data Owners</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Assign a data owner to {selectedAssignments.length} selected assignments.
          </Typography>
          
          <FormControl fullWidth sx={{ mt: 2, mb: 2 }}>
            <InputLabel>Data Owner</InputLabel>
            <Select
              value={bulkDataOwnerId}
              label="Data Owner"
              onChange={(e) => setBulkDataOwnerId(e.target.value as number)}
            >
              {dataOwners.map((owner) => (
                <MenuItem key={owner.user_id} value={owner.user_id}>
                  {owner.first_name} {owner.last_name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Assignment Rationale (Optional)"
            multiline
            rows={3}
            value={bulkRationale}
            onChange={(e) => setBulkRationale(e.target.value)}
            placeholder="Reason for this bulk assignment..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowBulkDialog(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleBulkAssign}
            variant="contained"
            disabled={!bulkDataOwnerId}
            startIcon={<SaveIcon />}
          >
            Assign
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AssignmentGrid;