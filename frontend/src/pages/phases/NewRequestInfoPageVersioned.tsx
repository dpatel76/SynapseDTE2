import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  LinearProgress,
  Stack,
  CircularProgress,
  Divider,
  Badge,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Container,
} from '@mui/material';
import {
  QuestionAnswer,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  PlayArrow,
  CloudUpload,
  Download,
  Description,
  Upload,
  Refresh,
  ExpandMore,
  Person,
  Business,
  Assignment,
  Schedule,
  Visibility,
  GetApp,
  AttachFile,
  CheckCircleOutline,
  PendingActions,
  AccessTime,
  Notifications,
  Send as SendIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { useParams } from 'react-router-dom';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';
import { DynamicActivityCards } from '../../components/phase/DynamicActivityCards';
import { useUniversalAssignments } from '../../hooks/useUniversalAssignments';
import { UniversalAssignmentAlert } from '../../components/UniversalAssignmentAlert';
import { toast } from 'react-hot-toast';
import apiClient from '../../api/client';
import { UserRole } from '../../types/api';
import DataSourceQueryPanel from '../../components/request-info/DataSourceQueryPanel';

// Import new versioning components and API
import { rfiVersionsApi } from '../../api/rfiVersions';
import { RFIVersionSelector } from '../../components/request-info/RFIVersionSelector';
import { RFIEvidenceTable } from '../../components/request-info/RFIEvidenceTable';
import { RFIReportOwnerFeedback } from '../../components/request-info/RFIReportOwnerFeedback';
import { 
  RFIVersion, 
  RFIVersionListItem, 
  RFIEvidence,
  VersionStatus,
  Decision,
  SendToReportOwnerRequest,
  ResubmitRequest,
} from '../../types/rfiVersions';

// ... (keep existing types and interfaces)

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
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const NewRequestInfoPageVersioned: React.FC = () => {
  const { user } = useAuth();
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const queryClient = useQueryClient();
  
  // Parse IDs
  const cycleIdNum = cycleId ? parseInt(cycleId, 10) : 0;
  const reportIdNum = reportId ? parseInt(reportId, 10) : 0;
  
  // Version state
  const [versions, setVersions] = useState<RFIVersionListItem[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  const [currentVersion, setCurrentVersion] = useState<RFIVersion | null>(null);
  const [isLoadingVersions, setIsLoadingVersions] = useState(true);
  
  // State management
  const [tabValue, setTabValue] = useState(0);
  const [createVersionDialogOpen, setCreateVersionDialogOpen] = useState(false);
  const [sendToReportOwnerDialogOpen, setSendToReportOwnerDialogOpen] = useState(false);
  const [makeChangesDialogOpen, setMakeChangesDialogOpen] = useState(false);
  
  // Load versions
  useEffect(() => {
    loadVersions();
  }, [cycleIdNum, reportIdNum]);
  
  // Load current version details when selection changes
  useEffect(() => {
    if (selectedVersionId) {
      loadVersionDetails(selectedVersionId);
    }
  }, [selectedVersionId]);
  
  const loadVersions = async () => {
    if (!cycleIdNum || !reportIdNum) return;
    
    try {
      setIsLoadingVersions(true);
      const versionList = await rfiVersionsApi.getVersions(cycleIdNum, reportIdNum);
      setVersions(versionList);
      
      // Select the current/latest version
      if (versionList.length > 0) {
        const currentVersion = versionList.find(v => v.is_current) || versionList[0];
        setSelectedVersionId(currentVersion.version_id);
      } else {
        // No versions exist, might need to create initial version
        setCurrentVersion(null);
      }
    } catch (error) {
      console.error('Error loading versions:', error);
      toast.error('Failed to load versions');
    } finally {
      setIsLoadingVersions(false);
    }
  };
  
  const loadVersionDetails = async (versionId: string) => {
    try {
      const version = await rfiVersionsApi.getVersion(versionId);
      setCurrentVersion(version);
    } catch (error) {
      console.error('Error loading version details:', error);
      toast.error('Failed to load version details');
    }
  };
  
  // Version management mutations
  const createVersionMutation = useMutation({
    mutationFn: async (data: { carryForward: boolean; approvedOnly: boolean }) => {
      return await rfiVersionsApi.createVersion(cycleIdNum, reportIdNum, {
        carry_forward_all: data.carryForward,
        carry_forward_approved_only: data.approvedOnly,
      });
    },
    onSuccess: () => {
      toast.success('New version created successfully');
      loadVersions();
      setCreateVersionDialogOpen(false);
    },
    onError: (error) => {
      console.error('Error creating version:', error);
      toast.error('Failed to create version');
    },
  });
  
  const sendToReportOwnerMutation = useMutation({
    mutationFn: async () => {
      if (!currentVersion) throw new Error('No version selected');
      return await rfiVersionsApi.sendToReportOwner(currentVersion.version_id);
    },
    onSuccess: () => {
      toast.success('Evidence sent to Report Owner for review');
      loadVersionDetails(selectedVersionId);
      setSendToReportOwnerDialogOpen(false);
    },
    onError: (error) => {
      console.error('Error sending to report owner:', error);
      toast.error('Failed to send to report owner');
    },
  });
  
  const makeChangesMutation = useMutation({
    mutationFn: async () => {
      if (!currentVersion) throw new Error('No version selected');
      return await rfiVersionsApi.resubmitAfterFeedback(currentVersion.version_id);
    },
    onSuccess: (newVersion) => {
      toast.success('New version created for changes');
      loadVersions();
      setMakeChangesDialogOpen(false);
    },
    onError: (error) => {
      console.error('Error creating new version:', error);
      toast.error('Failed to create new version');
    },
  });
  
  // Evidence decision mutations
  const updateTesterDecisionMutation = useMutation({
    mutationFn: async ({ evidenceId, decision, notes }: { evidenceId: string; decision: Decision; notes: string }) => {
      return await rfiVersionsApi.updateTesterDecision(evidenceId, {
        tester_decision: decision,
        tester_notes: notes,
      });
    },
    onSuccess: () => {
      toast.success('Tester decision updated');
      loadVersionDetails(selectedVersionId);
    },
    onError: (error) => {
      console.error('Error updating tester decision:', error);
      toast.error('Failed to update decision');
    },
  });
  
  const updateReportOwnerDecisionMutation = useMutation({
    mutationFn: async ({ evidenceId, decision, notes }: { evidenceId: string; decision: Decision; notes: string }) => {
      return await rfiVersionsApi.updateReportOwnerDecision(evidenceId, {
        report_owner_decision: decision,
        report_owner_notes: notes,
      });
    },
    onSuccess: () => {
      toast.success('Report Owner decision updated');
      loadVersionDetails(selectedVersionId);
    },
    onError: (error) => {
      console.error('Error updating report owner decision:', error);
      toast.error('Failed to update decision');
    },
  });
  
  const bulkTesterDecisionMutation = useMutation({
    mutationFn: async ({ evidenceIds, decision, notes }: { evidenceIds: string[]; decision: Decision; notes: string }) => {
      if (!currentVersion) throw new Error('No version selected');
      return await rfiVersionsApi.bulkTesterDecision(currentVersion.version_id, {
        evidence_ids: evidenceIds,
        decision,
        notes,
      });
    },
    onSuccess: () => {
      toast.success('Bulk decision applied successfully');
      loadVersionDetails(selectedVersionId);
    },
    onError: (error) => {
      console.error('Error applying bulk decision:', error);
      toast.error('Failed to apply bulk decision');
    },
  });
  
  // Helper functions
  const isReadOnly = (): boolean => {
    // Report Owners are always read-only
    if (user?.role === 'Report Owner') return true;
    
    // Check version status
    return currentVersion ? !currentVersion.can_be_edited : true;
  };
  
  const canSendToReportOwner = (): boolean => {
    if (!currentVersion || isReadOnly()) return false;
    
    // Check if all evidence has tester decisions
    const evidenceWithoutDecision = currentVersion.evidence_items.filter(e => !e.tester_decision);
    return evidenceWithoutDecision.length === 0 && currentVersion.evidence_items.length > 0;
  };
  
  const needsMakeChanges = (): boolean => {
    return currentVersion?.has_report_owner_feedback === true &&
           currentVersion?.report_owner_feedback_summary !== undefined &&
           (currentVersion.report_owner_feedback_summary.rejected > 0 ||
            currentVersion.report_owner_feedback_summary.changes_requested > 0) || false;
  };
  
  // Handlers
  const handleVersionChange = (versionId: string) => {
    setSelectedVersionId(versionId);
  };
  
  const handleUpdateTesterDecision = (evidenceId: string, decision: Decision, notes: string) => {
    updateTesterDecisionMutation.mutate({ evidenceId, decision, notes });
  };
  
  const handleUpdateReportOwnerDecision = (evidenceId: string, decision: Decision, notes: string) => {
    updateReportOwnerDecisionMutation.mutate({ evidenceId, decision, notes });
  };
  
  const handleBulkTesterDecision = (evidenceIds: string[], decision: Decision, notes: string) => {
    bulkTesterDecisionMutation.mutate({ evidenceIds, decision, notes });
  };
  
  const handleMakeChanges = () => {
    setMakeChangesDialogOpen(true);
  };
  
  // Unified status system
  const { data: unifiedPhaseStatus, refetch: refetchPhaseStatus } = usePhaseStatus('Request Info', cycleIdNum, reportIdNum);
  
  // Universal Assignments integration
  const {
    assignments,
    isLoading: assignmentsLoading,
    acknowledgeAssignment,
    startAssignment,
    completeAssignment,
  } = useUniversalAssignments({
    phase: 'Request Info',
    cycleId: cycleIdNum,
    reportId: reportIdNum,
  });

  // Report Info Query
  const { 
    data: reportInfo, 
    isLoading: reportInfoLoading 
  } = useQuery({
    queryKey: ['report-info', cycleIdNum, reportIdNum],
    queryFn: async () => {
      try {
        const cycleReportResponse = await apiClient.get(`/cycle-reports/${cycleIdNum}/reports/${reportIdNum}`);
        const cycleReportData = cycleReportResponse.data;
        
        return {
          report_id: cycleReportData.report_id,
          report_name: cycleReportData.report_name,
          lob_name: cycleReportData.lob_name || 'Unknown',
          tester_name: cycleReportData.tester_name || 'Not assigned',
          report_owner_name: cycleReportData.report_owner_name || 'Not specified',
        };
      } catch (error) {
        console.error('Error fetching report info:', error);
        return null;
      }
    },
    enabled: !!cycleIdNum && !!reportIdNum,
  });
  
  // Show loading state
  if (isLoadingVersions) {
    return (
      <Container maxWidth={false} sx={{ py: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }
  
  // Show create initial version if no versions exist
  if (versions.length === 0) {
    return (
      <Container maxWidth={false} sx={{ py: 3 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            No versions exist for this RFI phase
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create an initial version to start collecting evidence
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateVersionDialogOpen(true)}
          >
            Create Initial Version
          </Button>
        </Paper>
        
        {/* Create Version Dialog */}
        <Dialog open={createVersionDialogOpen} onClose={() => setCreateVersionDialogOpen(false)}>
          <DialogTitle>Create Initial Version</DialogTitle>
          <DialogContent>
            <Typography variant="body2">
              This will create the first version for the RFI phase. 
              You can configure submission deadlines and instructions after creation.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateVersionDialogOpen(false)}>Cancel</Button>
            <Button 
              onClick={() => createVersionMutation.mutate({ carryForward: false, approvedOnly: false })}
              variant="contained"
            >
              Create Version
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    );
  }
  
  return (
    <Container maxWidth={false} sx={{ py: 3 }}>
      {/* Universal Assignments Alert */}
      {assignments.length > 0 && assignments[0] && (
        <UniversalAssignmentAlert
          assignment={assignments[0]}
          onAcknowledge={acknowledgeAssignment}
          onStart={startAssignment}
          onComplete={completeAssignment}
        />
      )}
      
      {/* Report Information Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Assignment color="primary" />
              <Box>
                <Typography variant="h6" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportInfo?.report_name || 'Loading...'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Request Info Phase - Collecting additional information and documentation
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Business color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">LOB:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportInfo?.lob_name || 'Unknown'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Person color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">Tester:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportInfo?.tester_name || 'Not assigned'}
                </Typography>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>
      
      {/* Version Selection and Actions */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <RFIVersionSelector
            versions={versions}
            selectedVersionId={selectedVersionId}
            onVersionChange={handleVersionChange}
            disabled={false}
          />
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            {!isReadOnly() && (
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() => setCreateVersionDialogOpen(true)}
                variant="outlined"
              >
                New Version
              </Button>
            )}
            
            {canSendToReportOwner() && (
              <Button
                size="small"
                startIcon={<SendIcon />}
                onClick={() => setSendToReportOwnerDialogOpen(true)}
                variant="contained"
                color="primary"
              >
                Send to Report Owner
              </Button>
            )}
          </Box>
        </Box>
      </Paper>
      
      {/* Read-only Alert */}
      {isReadOnly() && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <strong>Read-only mode:</strong> This version is {currentVersion?.version_status} and cannot be edited.
        </Alert>
      )}
      
      {/* Report Owner Feedback */}
      {currentVersion?.has_report_owner_feedback && (
        <RFIReportOwnerFeedback
          version={currentVersion}
          onMakeChanges={handleMakeChanges}
          isReadOnly={isReadOnly()}
        />
      )}
      
      {/* Version Summary */}
      {currentVersion && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 3, mb: 3 }}>
          <Card sx={{ textAlign: 'center' }}>
            <CardContent>
              <Typography variant="h4" color="primary.main">
                {currentVersion.total_test_cases}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Test Cases
              </Typography>
            </CardContent>
          </Card>
          
          <Card sx={{ textAlign: 'center' }}>
            <CardContent>
              <Typography variant="h4" color="info.main">
                {currentVersion.submitted_count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Evidence Submitted
              </Typography>
            </CardContent>
          </Card>
          
          <Card sx={{ textAlign: 'center' }}>
            <CardContent>
              <Typography variant="h4" color="success.main">
                {currentVersion.approved_count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Approved
              </Typography>
            </CardContent>
          </Card>
          
          <Card sx={{ textAlign: 'center' }}>
            <CardContent>
              <Typography variant="h4" color="warning.main">
                {Math.round(currentVersion.completion_percentage ?? 0)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Complete
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}
      
      {/* Main Content Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Evidence Review" />
          <Tab label="Data Source Queries" />
          <Tab label="Submission Status" />
        </Tabs>
        
        <TabPanel value={tabValue} index={0}>
          {currentVersion && (
            <RFIEvidenceTable
              evidence={currentVersion.evidence_items}
              isReadOnly={isReadOnly()}
              userRole={user?.role || ''}
              onUpdateTesterDecision={handleUpdateTesterDecision}
              onUpdateReportOwnerDecision={handleUpdateReportOwnerDecision}
              onBulkTesterDecision={handleBulkTesterDecision}
              onViewEvidence={(evidence) => {
                // TODO: Implement view evidence
                console.log('View evidence:', evidence);
              }}
              onDownloadEvidence={(evidence) => {
                // TODO: Implement download evidence
                console.log('Download evidence:', evidence);
              }}
            />
          )}
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <DataSourceQueryPanel 
            cycleId={cycleIdNum}
            reportId={reportIdNum}
            onQueryResultsReceived={(results) => {
              // Handle query results if needed
              console.log('Query results received:', results);
            }}
          />
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          {/* TODO: Implement submission status view */}
          <Typography>Submission status by data owner coming soon...</Typography>
        </TabPanel>
      </Paper>
      
      {/* Dialogs */}
      
      {/* Create Version Dialog */}
      <Dialog open={createVersionDialogOpen} onClose={() => setCreateVersionDialogOpen(false)}>
        <DialogTitle>Create New Version</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Create a new version to make changes or start fresh.
          </Typography>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Carry Forward Options</InputLabel>
            <Select defaultValue="all" label="Carry Forward Options">
              <MenuItem value="all">Carry forward all evidence</MenuItem>
              <MenuItem value="approved">Carry forward only approved evidence</MenuItem>
              <MenuItem value="none">Start with no evidence</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateVersionDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={() => createVersionMutation.mutate({ carryForward: true, approvedOnly: false })}
            variant="contained"
          >
            Create Version
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Send to Report Owner Dialog */}
      <Dialog open={sendToReportOwnerDialogOpen} onClose={() => setSendToReportOwnerDialogOpen(false)}>
        <DialogTitle>Send to Report Owner</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            This will send all evidence to the Report Owner for final review.
          </Typography>
          {currentVersion && (
            <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>Summary:</Typography>
              <Typography variant="body2">
                • Total Evidence: {currentVersion.evidence_items.length}
              </Typography>
              <Typography variant="body2">
                • Approved by Tester: {currentVersion.evidence_items.filter(e => e.tester_decision === Decision.APPROVED).length}
              </Typography>
              <Typography variant="body2">
                • Rejected by Tester: {currentVersion.evidence_items.filter(e => e.tester_decision === Decision.REJECTED).length}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSendToReportOwnerDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={() => sendToReportOwnerMutation.mutate()}
            variant="contained"
            color="primary"
            startIcon={<SendIcon />}
          >
            Send for Review
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Make Changes Dialog */}
      <Dialog open={makeChangesDialogOpen} onClose={() => setMakeChangesDialogOpen(false)}>
        <DialogTitle>Make Changes</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            The Report Owner has requested changes to some evidence items.
          </Alert>
          <Typography variant="body2">
            Creating a new version will:
          </Typography>
          <Box component="ul" sx={{ mt: 1 }}>
            <Typography component="li" variant="body2">
              Carry forward all approved evidence
            </Typography>
            <Typography component="li" variant="body2">
              Reset rejected evidence for resubmission
            </Typography>
            <Typography component="li" variant="body2">
              Preserve all decision history
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMakeChangesDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={() => makeChangesMutation.mutate()}
            variant="contained"
            color="primary"
            startIcon={<Refresh />}
          >
            Create New Version
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default NewRequestInfoPageVersioned;