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
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Alert,
  CircularProgress,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  History as HistoryIcon,
  Person as PersonIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { dataOwnerLobAssignmentApi, PhaseAssignmentDashboard, AssignmentChange } from '../../api/dataOwnerLobAssignment';

interface AssignmentHistoryProps {
  phaseId: number;
  dashboard: PhaseAssignmentDashboard;
}

const AssignmentHistory: React.FC<AssignmentHistoryProps> = ({
  phaseId,
  dashboard
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [changes, setChanges] = useState<AssignmentChange[]>([]);
  const [filteredChanges, setFilteredChanges] = useState<AssignmentChange[]>([]);
  
  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  
  // Filters
  const [lobFilter, setLobFilter] = useState<number | ''>('');
  const [versionFilter, setVersionFilter] = useState<number | ''>('');

  const loadHistoryData = async () => {
    try {
      setLoading(true);
      setError(null);

      const historyData = await dataOwnerLobAssignmentApi.getAssignmentHistory(phaseId, {
        lob_id: lobFilter || undefined
      });

      setChanges(historyData.changes);
      setFilteredChanges(historyData.changes);
    } catch (err: any) {
      console.error('Error loading history data:', err);
      setError(err.response?.data?.detail || 'Failed to load assignment history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistoryData();
  }, [phaseId, lobFilter]);

  useEffect(() => {
    applyFilters();
  }, [changes, versionFilter]);

  const applyFilters = () => {
    let filtered = [...changes];

    if (versionFilter) {
      filtered = filtered.filter(change => change.version_number === versionFilter);
    }

    setFilteredChanges(filtered);
    setPage(0);
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

  const getChangeTypeColor = (change: AssignmentChange) => {
    if (change.previous_data_owner_id && change.data_owner_id) {
      return 'info'; // Changed assignment
    } else if (change.data_owner_id && !change.previous_data_owner_id) {
      return 'success'; // New assignment
    } else if (!change.data_owner_id && change.previous_data_owner_id) {
      return 'warning'; // Unassigned
    }
    return 'default';
  };

  const getChangeTypeLabel = (change: AssignmentChange) => {
    if (change.previous_data_owner_id && change.data_owner_id) {
      return 'Changed';
    } else if (change.data_owner_id && !change.previous_data_owner_id) {
      return 'Assigned';
    } else if (!change.data_owner_id && change.previous_data_owner_id) {
      return 'Unassigned';
    }
    return 'Unknown';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
        <CircularProgress />
        <Typography variant="body2" sx={{ ml: 2 }}>
          Loading assignment history...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
        <Button onClick={loadHistoryData} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  // Get unique versions for filter
  const uniqueVersions = Array.from(new Set(changes.map(c => c.version_number))).sort((a, b) => b - a);

  const paginatedChanges = filteredChanges.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Box>
      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <HistoryIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Changes</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {changes.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Across all versions
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TimelineIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">Active Versions</Typography>
              </Box>
              <Typography variant="h4" color="info.main">
                {uniqueVersions.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Version history depth
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <PersonIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Current Assigned</Typography>
              </Box>
              <Typography variant="h4" color="success.main">
                {dashboard.assignment_summary.assigned_count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Currently active assignments
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid size={{ xs: 12, md: 4 }}>
              <FormControl fullWidth>
                <InputLabel>LOB Filter</InputLabel>
                <Select
                  value={lobFilter}
                  label="LOB Filter"
                  onChange={(e) => setLobFilter(e.target.value as number)}
                >
                  <MenuItem value="">All LOBs</MenuItem>
                  {dashboard.lob_breakdown.map((lob) => (
                    <MenuItem key={lob.lob_id} value={lob.lob_id}>
                      {lob.lob_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <FormControl fullWidth>
                <InputLabel>Version Filter</InputLabel>
                <Select
                  value={versionFilter}
                  label="Version Filter"
                  onChange={(e) => setVersionFilter(e.target.value as number)}
                >
                  <MenuItem value="">All Versions</MenuItem>
                  {uniqueVersions.map((version) => (
                    <MenuItem key={version} value={version}>
                      Version {version}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Button
                variant="outlined"
                onClick={() => {
                  setLobFilter('');
                  setVersionFilter('');
                }}
                fullWidth
              >
                Clear Filters
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* History Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Assignment Change History
          </Typography>
          
          {filteredChanges.length === 0 ? (
            <Alert severity="info">
              No assignment history found for the selected filters.
            </Alert>
          ) : (
            <>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Version</TableCell>
                      <TableCell>Date</TableCell>
                      <TableCell>LOB</TableCell>
                      <TableCell>Attribute</TableCell>
                      <TableCell>Change Type</TableCell>
                      <TableCell>Previous Owner</TableCell>
                      <TableCell>Current Owner</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Reason</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {paginatedChanges.map((change, index) => (
                      <TableRow key={`${change.assignment_id}-${index}`}>
                        <TableCell>
                          <Chip
                            label={`V${change.version_number}`}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          {new Date(change.version_date).toLocaleDateString()}
                        </TableCell>
                        <TableCell>{change.lob_name || `LOB ${change.lob_id}`}</TableCell>
                        <TableCell>{change.attribute_name || `Attr ${change.attribute_id}`}</TableCell>
                        <TableCell>
                          <Chip
                            label={getChangeTypeLabel(change)}
                            color={getChangeTypeColor(change) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {change.previous_data_owner_name || 
                            (change.previous_data_owner_id ? `User ${change.previous_data_owner_id}` : '-')}
                        </TableCell>
                        <TableCell>
                          {change.data_owner_name || 
                            (change.data_owner_id ? `User ${change.data_owner_id}` : 'Unassigned')}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={change.assignment_status}
                            color={getStatusColor(change.assignment_status) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ maxWidth: 200 }}>
                            {change.change_reason || change.assignment_rationale || '-'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              
              <TablePagination
                rowsPerPageOptions={[25, 50, 100]}
                component="div"
                count={filteredChanges.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={(_, newPage) => setPage(newPage)}
                onRowsPerPageChange={(e) => {
                  setRowsPerPage(parseInt(e.target.value, 10));
                  setPage(0);
                }}
              />
            </>
          )}
        </CardContent>
      </Card>

      {/* Version Summary Accordion */}
      {uniqueVersions.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Version Summary
          </Typography>
          {uniqueVersions.map((version) => {
            const versionChanges = changes.filter(c => c.version_number === version);
            const assignedCount = versionChanges.filter(c => c.assignment_status === 'assigned').length;
            const unassignedCount = versionChanges.filter(c => c.assignment_status === 'unassigned').length;
            const changedCount = versionChanges.filter(c => c.assignment_status === 'changed').length;
            
            return (
              <Accordion key={version}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Typography variant="subtitle1">
                      Version {version}
                    </Typography>
                    <Chip label={`${versionChanges.length} changes`} size="small" />
                    <Chip label={`${assignedCount} assigned`} color="success" size="small" />
                    <Chip label={`${unassignedCount} unassigned`} color="warning" size="small" />
                    {changedCount > 0 && (
                      <Chip label={`${changedCount} changed`} color="info" size="small" />
                    )}
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" color="text.secondary">
                    Date: {versionChanges.length > 0 ? new Date(versionChanges[0].version_date).toLocaleDateString() : 'N/A'}
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    This version included {versionChanges.length} assignment changes across {Array.from(new Set(versionChanges.map(c => c.lob_id))).length} LOBs.
                  </Typography>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </Box>
      )}
    </Box>
  );
};

export default AssignmentHistory;