import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Chip,
  Stack,
  IconButton,
  Tooltip,
  Paper
} from '@mui/material';
import {
  Dashboard,
  Assessment,
  Schedule,
  CheckCircle,
  Warning,
  TrendingUp,
  Refresh,
  PlayArrow,
  Analytics
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import ObservationGroupsList from './ObservationGroupsList';
import ObservationReviewDialog from './ObservationReviewDialog';
import ObservationStatistics from './ObservationStatistics';
import DetectionRunner from './DetectionRunner';

interface ObservationGroup {
  id: number;
  group_name: string;
  group_description?: string;
  issue_summary: string;
  impact_description?: string;
  proposed_resolution?: string;
  observation_count: number;
  severity_level: 'high' | 'medium' | 'low';
  issue_type: 'data_quality' | 'process_failure' | 'system_error' | 'compliance_gap';
  status: string;
  attribute?: {
    id: number;
    name: string;
  };
  lob?: {
    id: number;
    name: string;
  };
  detector?: {
    id: number;
    name: string;
    email: string;
  };
  created_at: string;
}

interface WorkflowStatus {
  phase_id: number;
  cycle_id: number;
  report_id: number;
  total_groups: number;
  pending_tester_review: number;
  pending_report_owner_approval: number;
  approved_groups: number;
  rejected_groups: number;
  resolved_groups: number;
  workflow_completion_percentage: number;
  next_actions: string[];
  overdue_reviews: number[];
  overdue_approvals: number[];
}

interface ObservationManagementDashboardProps {
  phaseId?: number;
  cycleId?: number;
  reportId?: number;
}

const ObservationManagementDashboard: React.FC<ObservationManagementDashboardProps> = ({
  phaseId,
  cycleId,
  reportId
}) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Review dialog state
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<ObservationGroup | null>(null);
  const [reviewType, setReviewType] = useState<'tester' | 'report_owner'>('tester');
  
  // Detection state
  const [detectionRunning, setDetectionRunning] = useState(false);
  
  useEffect(() => {
    if (phaseId || cycleId || reportId) {
      fetchWorkflowStatus();
    }
  }, [phaseId, cycleId, reportId]);
  
  const fetchWorkflowStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (phaseId) params.append('phase_id', phaseId.toString());
      if (cycleId) params.append('cycle_id', cycleId.toString());
      if (reportId) params.append('report_id', reportId.toString());
      
      const response = await fetch(`/api/v1/observation-management-unified/workflow-status?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch workflow status');
      }
      
      const data = await response.json();
      setWorkflowStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  const handleGroupReview = (group: ObservationGroup) => {
    setSelectedGroup(group);
    setReviewType('tester');
    setReviewDialogOpen(true);
  };
  
  const handleGroupApprove = (group: ObservationGroup) => {
    setSelectedGroup(group);
    setReviewType('report_owner');
    setReviewDialogOpen(true);
  };
  
  const handleReviewSubmit = async (decision: string, notes: string, score?: number) => {
    if (!selectedGroup) return;
    
    const endpoint = reviewType === 'tester' 
      ? `/api/v1/observation-management-unified/groups/${selectedGroup.id}/tester-review`
      : `/api/v1/observation-management-unified/groups/${selectedGroup.id}/report-owner-approval`;
    
    const payload = reviewType === 'tester' 
      ? { review_decision: decision, review_notes: notes, review_score: score }
      : { approval_decision: decision, approval_notes: notes };
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      throw new Error('Failed to submit review');
    }
    
    // Refresh data
    fetchWorkflowStatus();
  };
  
  const handleRunDetection = async () => {
    if (!phaseId) return;
    
    try {
      setDetectionRunning(true);
      
      const response = await fetch(`/api/v1/observation-management-unified/detect/phase/${phaseId}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to run detection');
      }
      
      // Refresh data
      fetchWorkflowStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Detection failed');
    } finally {
      setDetectionRunning(false);
    }
  };
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  if (loading && !workflowStatus) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Observation Management
        </Typography>
        <Stack direction="row" spacing={2}>
          {phaseId && (
            <Button
              variant="contained"
              startIcon={detectionRunning ? <CircularProgress size={20} /> : <PlayArrow />}
              onClick={handleRunDetection}
              disabled={detectionRunning}
            >
              {detectionRunning ? 'Running...' : 'Run Detection'}
            </Button>
          )}
          <Tooltip title="Refresh Data">
            <IconButton onClick={fetchWorkflowStatus}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {/* Workflow Status Cards */}
      {workflowStatus && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Total Groups
                    </Typography>
                    <Typography variant="h4">
                      {workflowStatus.total_groups}
                    </Typography>
                  </Box>
                  <Assessment color="primary" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Pending Review
                    </Typography>
                    <Typography variant="h4">
                      {workflowStatus.pending_tester_review}
                    </Typography>
                  </Box>
                  <Schedule color="warning" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Pending Approval
                    </Typography>
                    <Typography variant="h4">
                      {workflowStatus.pending_report_owner_approval}
                    </Typography>
                  </Box>
                  <Warning color="warning" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Completion
                    </Typography>
                    <Typography variant="h4">
                      {Math.round(workflowStatus.workflow_completion_percentage ?? 0)}%
                    </Typography>
                  </Box>
                  <TrendingUp color="success" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
      
      {/* Next Actions */}
      {workflowStatus && workflowStatus.next_actions.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Next Actions
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {workflowStatus.next_actions.map((action, index) => (
                <Chip
                  key={index}
                  label={action}
                  color="primary"
                  variant="outlined"
                  sx={{ mb: 1 }}
                />
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}
      
      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={activeTab} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
          <Tab label="Observation Groups" icon={<Assessment />} />
          <Tab label="Statistics" icon={<Analytics />} />
          <Tab label="Detection" icon={<PlayArrow />} />
        </Tabs>
      </Paper>
      
      {/* Tab Content */}
      <Box>
        {activeTab === 0 && (
          <ObservationGroupsList
            phaseId={phaseId}
            cycleId={cycleId}
            reportId={reportId}
            onGroupReview={handleGroupReview}
            onGroupApprove={handleGroupApprove}
          />
        )}
        
        {activeTab === 1 && (
          <ObservationStatistics
            phaseId={phaseId}
            cycleId={cycleId}
            reportId={reportId}
          />
        )}
        
        {activeTab === 2 && (
          <DetectionRunner
            phaseId={phaseId}
            cycleId={cycleId}
            reportId={reportId}
          />
        )}
      </Box>
      
      {/* Review Dialog */}
      <ObservationReviewDialog
        open={reviewDialogOpen}
        onClose={() => setReviewDialogOpen(false)}
        group={selectedGroup}
        reviewType={reviewType}
        onSubmit={handleReviewSubmit}
      />
    </Box>
  );
};

export default ObservationManagementDashboard;