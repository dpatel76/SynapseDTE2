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
  Tabs,
  Tab,
  Paper,
  Divider
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  Dashboard as DashboardIcon,
  History as HistoryIcon,
  Add as AddIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { dataOwnerLobAssignmentApi, PhaseAssignmentDashboard, DataOwnerLOBAttributeVersion } from '../../api/dataOwnerLobAssignment';
import AssignmentVersionManager from './AssignmentVersionManager';
import AssignmentGrid from './AssignmentGrid';
import AssignmentHistory from './AssignmentHistory';
import AssignmentAnalytics from './AssignmentAnalytics';

interface DataExecutiveDashboardProps {
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

const DataExecutiveDashboard: React.FC<DataExecutiveDashboardProps> = ({
  phaseId,
  cycleId,
  reportId
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<PhaseAssignmentDashboard | null>(null);
  const [currentVersion, setCurrentVersion] = useState<DataOwnerLOBAttributeVersion | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [dashboardData, versionData] = await Promise.all([
        dataOwnerLobAssignmentApi.getPhaseAssignmentDashboard(phaseId),
        dataOwnerLobAssignmentApi.getCurrentVersion(phaseId)
      ]);

      setDashboard(dashboardData);
      setCurrentVersion(versionData);
    } catch (err: any) {
      console.error('Error loading dashboard data:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [phaseId, refreshKey]);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const handleVersionCreated = (newVersion: DataOwnerLOBAttributeVersion) => {
    setCurrentVersion(newVersion);
    handleRefresh();
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="body2" sx={{ ml: 2 }}>
          Loading data owner LOB assignments...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
        <Button onClick={handleRefresh} sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  if (!dashboard) {
    return (
      <Alert severity="info">
        No assignment data available for this phase.
      </Alert>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active': return 'success';
      case 'draft': return 'warning';
      case 'superseded': return 'default';
      default: return 'default';
    }
  };

  return (
    <Box>
      {/* Header Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
          <Typography variant="h5" component="h1" gutterBottom>
            Data Owner LOB Assignment Management
          </Typography>
          <Button
            variant="outlined"
            onClick={handleRefresh}
            startIcon={<DashboardIcon />}
          >
            Refresh
          </Button>
        </Box>

        {/* Current Version Status */}
        {currentVersion ? (
          <Box mb={3}>
            <Typography variant="h6" gutterBottom>
              Current Version
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card variant="outlined">
                  <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="between">
                      <Typography variant="body2" color="text.secondary">
                        Version {currentVersion.version_number}
                      </Typography>
                      <Chip 
                        label={currentVersion.version_status}
                        color={getStatusColor(currentVersion.version_status) as any}
                        size="small"
                      />
                    </Box>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Created: {new Date(currentVersion.created_at).toLocaleDateString()}
                    </Typography>
                    {currentVersion.assignment_notes && (
                      <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                        "{currentVersion.assignment_notes}"
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Assignment Summary
                    </Typography>
                    <Box display="flex" gap={2} flexWrap="wrap">
                      <Chip 
                        label={`${dashboard.assignment_summary.assigned_count} Assigned`}
                        color="success"
                        variant="outlined"
                        size="small"
                      />
                      <Chip 
                        label={`${dashboard.assignment_summary.unassigned_count} Unassigned`}
                        color="warning"
                        variant="outlined"
                        size="small"
                      />
                      <Chip 
                        label={`${dashboard.assignment_summary.acknowledged_count} Acknowledged`}
                        color="info"
                        variant="outlined"
                        size="small"
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        ) : (
          <Alert severity="info" sx={{ mb: 3 }}>
            No active version found. Create a new version to start managing data owner assignments.
          </Alert>
        )}
      </Paper>

      {/* Main Content Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={activeTab} 
            onChange={handleTabChange}
            aria-label="data owner assignment tabs"
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab 
              label="Version Management" 
              icon={<AssignmentIcon />}
              iconPosition="start"
              {...a11yProps(0)} 
            />
            <Tab 
              label="Assignment Grid" 
              icon={<DashboardIcon />}
              iconPosition="start"
              {...a11yProps(1)} 
            />
            <Tab 
              label="History" 
              icon={<HistoryIcon />}
              iconPosition="start"
              {...a11yProps(2)} 
            />
            <Tab 
              label="Analytics" 
              icon={<AnalyticsIcon />}
              iconPosition="start"
              {...a11yProps(3)} 
            />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <AssignmentVersionManager
            phaseId={phaseId}
            currentVersion={currentVersion}
            onVersionCreated={handleVersionCreated}
            onRefresh={handleRefresh}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {currentVersion ? (
            <AssignmentGrid
              phaseId={phaseId}
              versionId={currentVersion.version_id}
              onAssignmentChange={handleRefresh}
            />
          ) : (
            <Alert severity="info">
              Please create a version first to manage assignments.
            </Alert>
          )}
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <AssignmentHistory
            phaseId={phaseId}
            dashboard={dashboard}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <AssignmentAnalytics
            phaseId={phaseId}
            dashboard={dashboard}
          />
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default DataExecutiveDashboard;