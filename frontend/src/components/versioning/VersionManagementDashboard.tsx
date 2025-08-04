import React, { useState, useEffect } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Badge
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot
} from '@mui/lab';
import {
  CheckCircle,
  Cancel,
  History,
  Compare,
  Refresh,
  Info,
  Assignment,
  GroupAdd,
  DocumentScanner,
  Science,
  FilterList,
  Inventory,
  BugReport,
  Assessment,
  Description
} from '@mui/icons-material';
import { useWorkflowVersioning } from '../../hooks/useWorkflowVersioning';
import { usePermissions } from '../../contexts/PermissionContext';
import { PhaseVersionStatus, VersionInfo, ApprovalStatus } from '../../types/versioning';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`version-tabpanel-${index}`}
      aria-labelledby={`version-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const phaseIcons: Record<string, React.ReactElement> = {
  'Planning': <Assignment />,
  'Data Profiling': <Science />,
  'Scoping': <FilterList />,
  'Sample Selection': <Inventory />,
  'Data Owner ID': <GroupAdd />,
  'Request Info': <DocumentScanner />,
  'Test Execution': <BugReport />,
  'Observation Management': <Assessment />,
  'Finalize Test Report': <Description />
};

interface VersionManagementDashboardProps {
  cycleId: number;
  reportId: number;
  workflowId: string;
}

export const VersionManagementDashboard: React.FC<VersionManagementDashboardProps> = ({
  cycleId,
  reportId,
  workflowId
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedPhase, setSelectedPhase] = useState<string>('');
  const [versionDialog, setVersionDialog] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<VersionInfo | null>(null);
  
  const { hasPermission } = usePermissions();
  const {
    phaseVersions,
    phaseStatuses,
    pendingApprovals,
    loading,
    error,
    refreshVersions,
    submitApproval,
    getVersionHistory,
    compareVersions
  } = useWorkflowVersioning(workflowId);

  const phases = [
    'Planning',
    'Data Profiling',
    'Scoping',
    'Sample Selection',
    'Data Owner ID',
    'Request Info',
    'Test Execution',
    'Observation Management',
    'Finalize Test Report'
  ];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleVersionClick = async (phase: string, versionId: string) => {
    // Get the version from phaseVersions which contains VersionInfo objects
    const version = phaseVersions[phase];
    if (version && version.version_id === versionId) {
      setSelectedVersion(version);
      setSelectedPhase(phase);
      setVersionDialog(true);
    }
  };

  const handleApproval = async (phase: string, versionId: string, approved: boolean, notes?: string) => {
    await submitApproval(phase, versionId, approved, notes);
    setVersionDialog(false);
    refreshVersions();
  };

  const getPhaseStatus = (phase: string) => {
    const status = phaseStatuses[phase];
    const version = phaseVersions[phase];
    
    if (!status) return { color: 'default' as const, label: 'Not Started' };
    if (status.status === 'Complete') return { color: 'success' as const, label: 'Complete' };
    if (status.status === 'In Progress') {
      if (pendingApprovals.find(p => p.phase === phase)) {
        return { color: 'warning' as const, label: 'Pending Approval' };
      }
      return { color: 'info' as const, label: 'In Progress' };
    }
    return { color: 'default' as const, label: status.status || 'Unknown' };
  };

  const renderPhaseOverview = () => (
    <Grid container spacing={3}>
      {phases.map((phase) => {
        const status = getPhaseStatus(phase);
        const version = phaseVersions[phase];
        const hasPendingApproval = pendingApprovals.find(p => p.phase === phase);
        
        return (
          <Grid key={phase} size={{ xs: 12, md: 4 }}>
            <Card 
              sx={{ 
                cursor: version ? 'pointer' : 'default',
                '&:hover': version ? { boxShadow: 3 } : {}
              }}
              onClick={() => version && handleVersionClick(phase, version.version_id)}
            >
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box display="flex" alignItems="center">
                    {phaseIcons[phase]}
                    <Typography variant="h6" sx={{ ml: 1 }}>
                      {phase}
                    </Typography>
                  </Box>
                  <Chip
                    label={status.label}
                    color={status.color as any}
                    size="small"
                  />
                </Box>
                
                {version && (
                  <Box mt={2}>
                    <Typography variant="body2" color="textSecondary">
                      Version: {version.version_number}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Status: {version.version_status}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Created: {new Date(version.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                )}
                
                {hasPendingApproval && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    <Typography variant="body2">
                      Awaiting approval from {hasPendingApproval.awaiting}
                    </Typography>
                  </Alert>
                )}
                
                {version && (
                  <Box mt={2} display="flex" gap={1}>
                    <Tooltip title="View History">
                      <IconButton size="small">
                        <History />
                      </IconButton>
                    </Tooltip>
                    {version.parent_version_id && (
                      <Tooltip title="Compare with Previous">
                        <IconButton size="small">
                          <Compare />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        );
      })}
    </Grid>
  );

  const renderVersionTimeline = () => {
    // For now, just use current versions since getVersionHistory is async
    const allVersions = phases
      .filter(phase => phaseVersions[phase])
      .map(phase => ({ 
        ...phaseVersions[phase]!, 
        phase,
        // Map VersionInfo status to match VersionHistory format
        version_status: phaseVersions[phase]!.version_status
      }))
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    return (
      <Timeline position="alternate">
        {allVersions.slice(0, 20).map((version, index) => (
          <TimelineItem key={`${version.phase}-${version.version_id}`}>
            <TimelineSeparator>
              <TimelineDot 
                color={version.version_status === 'approved' ? 'success' : 'primary'}
              >
                {phaseIcons[version.phase]}
              </TimelineDot>
              {index < allVersions.length - 1 && <TimelineConnector />}
            </TimelineSeparator>
            <TimelineContent>
              <Card>
                <CardContent>
                  <Typography variant="h6" component="h1">
                    {version.phase} v{version.version_number}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {new Date(version.created_at).toLocaleString()}
                  </Typography>
                  <Chip
                    label={version.version_status}
                    size="small"
                    color={version.version_status === 'approved' ? 'success' : 'default'}
                    sx={{ mt: 1 }}
                  />
                  {version.created_by && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Created by: {version.created_by}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>
    );
  };

  const renderPendingApprovals = () => {
    if (pendingApprovals.length === 0) {
      return (
        <Box textAlign="center" py={4}>
          <Typography variant="h6" color="textSecondary">
            No pending approvals
          </Typography>
        </Box>
      );
    }

    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Phase</TableCell>
              <TableCell>Version</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Awaiting</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {pendingApprovals.map((approval) => {
              const version = phaseVersions[approval.phase];
              if (!version) return null;
              
              return (
                <TableRow key={approval.phase}>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      {phaseIcons[approval.phase]}
                      <Typography sx={{ ml: 1 }}>{approval.phase}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>v{version.version_number}</TableCell>
                  <TableCell>{new Date(version.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <Chip label={approval.awaiting} size="small" />
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={() => handleVersionClick(approval.phase, approval.version_id)}
                    >
                      Review
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        <Typography>Error loading version information: {error}</Typography>
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Version Management</Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={refreshVersions}
        >
          Refresh
        </Button>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab 
            label={
              <Badge badgeContent={pendingApprovals.length} color="error">
                Overview
              </Badge>
            } 
          />
          <Tab label="Timeline" />
          <Tab 
            label={
              <Badge badgeContent={pendingApprovals.length} color="error">
                Pending Approvals
              </Badge>
            }
          />
        </Tabs>
      </Box>

      <TabPanel value={activeTab} index={0}>
        {renderPhaseOverview()}
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        {renderVersionTimeline()}
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        {renderPendingApprovals()}
      </TabPanel>

      {/* Version Details Dialog */}
      <Dialog
        open={versionDialog}
        onClose={() => setVersionDialog(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedVersion && (
          <>
            <DialogTitle>
              {selectedPhase} - Version {selectedVersion.version_number}
            </DialogTitle>
            <DialogContent>
              <Grid container spacing={2}>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Status
                  </Typography>
                  <Chip
                    label={selectedVersion.version_status}
                    color={selectedVersion.version_status === 'approved' ? 'success' : 'default'}
                  />
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Created
                  </Typography>
                  <Typography>
                    {new Date(selectedVersion.created_at).toLocaleString()}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Created By
                  </Typography>
                  <Typography>{selectedVersion.created_by || 'System'}</Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Workflow ID
                  </Typography>
                  <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                    {selectedVersion.workflow_execution_id}
                  </Typography>
                </Grid>
                
                {selectedVersion.version_status === 'draft' && 
                 hasPermission('version', 'approve') && (
                  <Grid size={{ xs: 12 }}>
                    <Box mt={2} display="flex" gap={2}>
                      <Button
                        variant="contained"
                        color="success"
                        startIcon={<CheckCircle />}
                        onClick={() => handleApproval(
                          selectedPhase,
                          selectedVersion.version_id,
                          true,
                          'Approved via dashboard'
                        )}
                      >
                        Approve
                      </Button>
                      <Button
                        variant="contained"
                        color="error"
                        startIcon={<Cancel />}
                        onClick={() => handleApproval(
                          selectedPhase,
                          selectedVersion.version_id,
                          false,
                          'Rejected via dashboard'
                        )}
                      >
                        Reject
                      </Button>
                    </Box>
                  </Grid>
                )}
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setVersionDialog(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};