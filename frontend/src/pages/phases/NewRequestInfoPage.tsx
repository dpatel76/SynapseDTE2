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
  Error,
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
// import WorkflowProgress from '../../components/WorkflowProgress';
import DataSourceQueryPanel from '../../components/request-info/DataSourceQueryPanel';
import { TestCasesTable } from '../../components/request-info';

// Types for Request for Information phase
interface ReportInfo {
  report_id: number;
  report_name: string;
  lob_name?: string;
  tester_name?: string;
  report_owner_name?: string;
  report_owner_email?: string;
  report_owner_id?: number;
  description?: string;
  regulatory_framework?: string;
  frequency?: string;
  due_date?: string;
  priority?: string;
  cycle_name?: string;
  current_phase?: string;
}

interface RequestInfoPhase {
  phase_id: string;
  cycle_id: number;
  report_id: number;
  phase_status: string;
  instructions?: string;
  submission_deadline?: string;
  started_by?: number;
  started_at?: string;
  completed_by?: number;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  // New metrics fields
  total_attributes?: number;
  scoped_attributes?: number;
  total_samples?: number;
  total_lobs?: number;
  total_data_providers?: number;
  uploaded_test_cases?: number;
  total_test_cases?: number;
}

interface TestCase {
  test_case_id: string;
  test_case_number?: string;
  phase_id: string;
  cycle_id: number;
  report_id: number;
  attribute_id: number;
  attribute_name: string;
  sample_id: string;
  sample_identifier: string;
  data_owner_id: number;
  data_owner_name: string;
  data_owner_email: string;
  primary_key_attributes: Record<string, any>;
  status: 'Pending' | 'Submitted' | 'Overdue';
  validation_status?: 'Pending' | 'Approved' | 'Rejected';
  submission_count: number;
  submission_deadline?: string;
  submitted_at?: string;
  expected_evidence_type: string;
  special_instructions?: string;
  latest_submission_at?: string;
  document_submission?: DocumentSubmission;
  created_at: string;
  updated_at: string;
}

interface DocumentSubmission {
  submission_id: string;
  test_case_id: string;
  document_filename: string;
  document_type: string;
  file_size_bytes: number;
  submission_notes?: string;
  submitted_by: number;
  submitted_at: string;
}

interface PhaseProgressSummary {
  total_test_cases: number;
  submitted_test_cases: number;
  pending_test_cases: number;
  overdue_test_cases: number;
  completion_percentage: number;
  data_owners_count: number;
  data_owners_completed: number;
}

interface DataOwnerSummary {
  data_owner_id: number;
  data_owner_name: string;
  data_owner_email: string;
  assigned_attributes: string[];
  total_test_cases: number;
  submitted_test_cases: number;
  pending_test_cases: number;
  overdue_test_cases: number;
  overall_status: string;
  last_activity?: string;
  notification_sent: boolean;
  portal_accessed: boolean;
}

interface TesterPhaseView {
  phase: RequestInfoPhase;
  cycle_name: string;
  report_name: string;
  progress_summary: PhaseProgressSummary;
  data_owner_summaries: DataOwnerSummary[];
  recent_submissions: DocumentSubmission[];
  overdue_test_cases: TestCase[];
  can_start_phase: boolean;
  can_complete_phase: boolean;
  can_send_reminders: boolean;
}

interface DataOwnerPortalData {
  notification: any;
  test_cases: TestCase[];
  cycle_name: string;
  report_name: string;
  phase_instructions?: string;
  submission_deadline: string;
  days_remaining: number;
  total_test_cases: number;
  submitted_test_cases: number;
  pending_test_cases: number;
  completion_percentage: number;
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
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const NewRequestInfoPage: React.FC = () => {
  const { user } = useAuth();
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const queryClient = useQueryClient();
  
  // Parse IDs
  const cycleIdNum = cycleId ? parseInt(cycleId, 10) : 0;
  const reportIdNum = reportId ? parseInt(reportId, 10) : 0;
  
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
  
  // Separate query for request info status data
  const { data: requestInfoStatus, isLoading: statusLoading, refetch: refetchRequestInfoStatus } = useQuery({
    queryKey: ['request-info-status', cycleIdNum, reportIdNum],
    queryFn: async () => {
      const response = await apiClient.get(`/request-info/${cycleIdNum}/reports/${reportIdNum}/status`);
      return response.data;
    },
    enabled: !!cycleIdNum && !!reportIdNum,
    refetchInterval: 5000, // Poll every 5 seconds
  });
  
  
  // State management
  const [tabValue, setTabValue] = useState(0);
  const [startPhaseDialogOpen, setStartPhaseDialogOpen] = useState(false);
  const [completePhaseDialogOpen, setCompletePhaseDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedTestCase, setSelectedTestCase] = useState<TestCase | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadNotes, setUploadNotes] = useState('');
  const [completionNotes, setCompletionNotes] = useState('');
  const [filterStatus, setFilterStatus] = useState<'All' | 'Pending' | 'Submitted' | 'Overdue'>('All');
  const [filterDataOwner, setFilterDataOwner] = useState<number | 'All'>('All');
  const [sampleDetailsDialogOpen, setSampleDetailsDialogOpen] = useState(false);
  const [selectedSampleDetails, setSelectedSampleDetails] = useState<any | null>(null);

  // Form state for starting phase
  const [startPhaseForm, setStartPhaseForm] = useState({
    instructions: 'Please provide supporting documentation for the assigned attributes. Upload documents that validate the reported values for each sample.',
    submission_deadline: '',
    auto_notify_data_owners: true,
    notify_immediately: true,
  });

  // Report Info Query
  const { 
    data: reportInfo, 
    isLoading: reportInfoLoading 
  } = useQuery({
    queryKey: ['report-info', cycleIdNum, reportIdNum],
    queryFn: async () => {
      try {
        // Get cycle report info which has all the data we need
        const cycleReportResponse = await apiClient.get(`/cycle-reports/${cycleIdNum}/reports/${reportIdNum}`);
        const cycleReportData = cycleReportResponse.data;
        
        // Map the API response to our expected format
        return {
          report_id: cycleReportData.report_id,
          report_name: cycleReportData.report_name,
          lob: cycleReportData.lob_name || 'Unknown',
          assigned_tester: cycleReportData.tester_name || 'Not assigned',
          report_owner: cycleReportData.report_owner_name || 'Not specified',
          description: cycleReportData.description,
          regulatory_framework: cycleReportData.regulation,
          frequency: cycleReportData.frequency,
        } as ReportInfo;
      } catch (error) {
        console.error('Error loading report info:', error);
        // Fallback to basic info
        return {
          report_id: reportIdNum,
          report_name: 'Loading...',
          lob: 'Unknown',
          assigned_tester: 'Unknown',
          report_owner: 'Unknown'
        } as ReportInfo;
      }
    },
    enabled: !!reportIdNum,
  });

  // Phase Data Query
  const { 
    data: phaseData, 
    isLoading: phaseLoading, 
    error: phaseError 
  } = useQuery({
    queryKey: ['request-info-phase', cycleIdNum, reportIdNum],
    queryFn: async () => {
      if (user?.role === UserRole.DATA_OWNER) {
        // Data owner view - get test cases directly
        try {
          const response = await apiClient.get(`/request-info/data-owner/test-cases`);
          return response.data as DataOwnerPortalData;
        } catch (error) {
          console.error('Error loading data owner portal:', error);
          return null;
        }
      } else {
        // Tester/Admin view - combine multiple endpoints
        try {
          // Get phase status
          let status;
          try {
            const statusResponse = await apiClient.get(`/request-info/${cycleIdNum}/reports/${reportIdNum}/status`);
            status = statusResponse.data;
          } catch (statusError: any) {
            if (statusError.response?.status === 404) {
              // Phase not started yet
              return {
                phase: {
                  phase_id: '',
                  cycle_id: cycleIdNum,
                  report_id: reportIdNum,
                  phase_status: 'Not Started',
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString()
                },
                cycle_name: `Cycle ${cycleIdNum}`,
                report_name: `Report ${reportIdNum}`,
                progress_summary: {
                  total_test_cases: 0,
                  submitted_test_cases: 0,
                  pending_test_cases: 0,
                  overdue_test_cases: 0,
                  completion_percentage: 0,
                  data_owners_count: 0,
                  data_owners_completed: 0
                },
                data_owner_summaries: [],
                recent_submissions: [],
                overdue_test_cases: [],
                can_start_phase: true,
                can_complete_phase: false,
                can_send_reminders: false
              } as TesterPhaseView;
            }
            throw statusError;
          }
          
          // Only fetch additional data if phase has started
          let progressData = {
            total_test_cases: status.total_test_cases || 0,
            submitted_test_cases: status.submitted_test_cases || 0,
            pending_test_cases: status.pending_test_cases || 0,
            overdue_test_cases: status.overdue_test_cases || 0,
            completion_percentage: 0,
            data_owners_count: status.data_owners_notified || 0,
            data_owners_completed: 0
          };
          
          let assignmentsData = [];
          let testCasesData = [];
          
          if (status.phase_status !== 'Not Started') {
            try {
              const progressResponse = await apiClient.get(`/request-info/${cycleIdNum}/reports/${reportIdNum}/progress`);
              progressData = progressResponse.data;
            } catch (e) {
              console.warn('Could not fetch progress data:', e);
            }
            
            try {
              const assignmentsResponse = await apiClient.get(`/request-info/${cycleIdNum}/reports/${reportIdNum}/assignments`);
              assignmentsData = assignmentsResponse.data || [];
            } catch (e) {
              console.warn('Could not fetch assignments data:', e);
            }
            
            try {
              const testCasesResponse = await apiClient.get(`/request-info/${cycleIdNum}/reports/${reportIdNum}/test-cases`);
              testCasesData = testCasesResponse.data || [];
            } catch (e) {
              console.warn('Could not fetch test cases data:', e);
            }
          }
          
          // Construct the TesterPhaseView object
          return {
            phase: {
              phase_id: status.phase_id || '',
              cycle_id: status.cycle_id,
              report_id: status.report_id,
              phase_status: status.phase_status,
              created_at: new Date().toISOString(), // Use current time as fallback
              updated_at: new Date().toISOString()
            },
            cycle_name: reportInfo?.cycle_name || `Cycle ${cycleIdNum}`,
            report_name: reportInfo?.report_name || `Report ${reportIdNum}`,
            progress_summary: progressData,
            data_owner_summaries: assignmentsData,
            recent_submissions: [], // Will need another endpoint for this
            overdue_test_cases: testCasesData.filter((tc: any) => tc.status === 'Overdue'),
            can_start_phase: status.phase_status === 'Not Started',
            can_complete_phase: status.can_complete || false,
            can_send_reminders: status.phase_status === 'In Progress'
          } as TesterPhaseView;
        } catch (error) {
          console.error('Error loading tester view:', error);
          return null;
        }
      }
    },
    enabled: !!cycleIdNum && !!reportIdNum && !!user,
  });

  // Queries
  const { data: testCases, isLoading: testCasesLoading } = useQuery({
    queryKey: ['test-cases', (phaseData as TesterPhaseView)?.phase?.phase_id, filterStatus, filterDataOwner],
    queryFn: async () => {
      const testerPhaseData = phaseData as TesterPhaseView;
      const phaseId = testerPhaseData?.phase?.phase_id;
      if (!phaseId) return [];
      
      const params = new URLSearchParams();
      if (filterStatus !== 'All') params.append('status', filterStatus);
      if (filterDataOwner !== 'All') params.append('data_owner_id', filterDataOwner.toString());
      
      // Use the cycle/report endpoint since phase-specific endpoint doesn't exist
      const response = await apiClient.get(`/request-info/${cycleIdNum}/reports/${reportIdNum}/test-cases?${params.toString()}`);
      return response.data || [];
    },
    enabled: !!(phaseData as TesterPhaseView)?.phase?.phase_id && user?.role !== UserRole.DATA_OWNER,
    refetchInterval: 5000, // Poll every 5 seconds to check for new test cases
    staleTime: 2000 // Consider data stale after 2 seconds
  });

  // Mutations
  const startPhaseMutation = useMutation({
    mutationFn: async () => {
      return await apiClient.post(`/request-info/${cycleIdNum}/reports/${reportIdNum}/start`, {
        instructions: startPhaseForm.instructions || '',
        submission_deadline: startPhaseForm.submission_deadline || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request-info-phase'] });
      queryClient.invalidateQueries({ queryKey: ['phaseStatus'] });
      queryClient.invalidateQueries({ queryKey: ['test-cases'] });
      refetchPhaseStatus();
      refetchRequestInfoStatus();
      setStartPhaseDialogOpen(false);
      toast.success('Request for Information phase started successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start phase');
    },
  });

  const completePhaseMutation = useMutation({
    mutationFn: async () => {
      return await apiClient.post(`/request-info/${cycleIdNum}/reports/${reportIdNum}/complete`, {
        completion_notes: completionNotes,
        force_complete: false,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request-info-phase'] });
      queryClient.invalidateQueries({ queryKey: ['phaseStatus'] });
      setCompletePhaseDialogOpen(false);
      setCompletionNotes('');
      toast.success('Request for Information phase completed successfully');
      refetchPhaseStatus();
      refetchRequestInfoStatus();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to complete phase');
    },
  });

  const uploadDocumentMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      if (!selectedTestCase) {
        throw new globalThis.Error('No test case selected');
      }
      return await apiClient.post(`/request-info/test-cases/${selectedTestCase.test_case_id}/submit`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request-info-phase'] });
      queryClient.invalidateQueries({ queryKey: ['test-cases'] });
      queryClient.invalidateQueries({ queryKey: ['phaseStatus'] });
      setUploadDialogOpen(false);
      setUploadFile(null);
      setUploadNotes('');
      setSelectedTestCase(null);
      toast.success('Document uploaded successfully');
      refetchPhaseStatus();
      refetchRequestInfoStatus();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to upload document');
    },
  });

  // Event handlers
  const handleStartPhase = () => {
    setStartPhaseDialogOpen(true);
  };

  const handleCompletePhase = () => {
    setCompletePhaseDialogOpen(true);
  };

  const handleActivityAction = async (activity: any, action: string) => {
    try {
      // Make the API call to start/complete the activity
      const endpoint = action === 'start' ? 'start' : 'complete';
      const response = await apiClient.post(`/activity-management/activities/${activity.activity_id}/${endpoint}`, {
        cycle_id: cycleIdNum,
        report_id: reportIdNum,
        phase_name: 'Request Info'
      });
      
      // Show success message from backend or default
      const message = response.data.message || activity.metadata?.success_message || `${action === 'start' ? 'Started' : 'Completed'} ${activity.name}`;
      toast.success(message);
      
      // Special handling for phase_start activities - immediately complete them
      if (action === 'start' && activity.metadata?.activity_type === 'phase_start') {
        console.log('Auto-completing phase_start activity:', activity.name);
        await new Promise(resolve => setTimeout(resolve, 200));
        
        try {
          await apiClient.post(`/activity-management/activities/${activity.activity_id}/complete`, {
            cycle_id: cycleIdNum,
            report_id: reportIdNum,
            phase_name: 'Request Info'
          });
          toast.success(`${activity.name} completed`);
        } catch (completeError: any) {
          // Ignore "already completed" errors

          if (completeError.response?.status === 400 && 

              completeError.response?.data?.detail?.includes('Cannot complete activity in status')) {

            console.log('Phase start activity already completed, ignoring error');

          } else {

            console.error('Error auto-completing phase_start activity:', completeError);

          }
        }
      }
      
      // Add a small delay to ensure backend has processed the change
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Force refresh of both status systems
      refetchPhaseStatus();
      refetchRequestInfoStatus();
      queryClient.invalidateQueries({ queryKey: ['request-info-phase', cycleIdNum, reportIdNum] });
      queryClient.invalidateQueries({ queryKey: ['test-cases'] });
      queryClient.invalidateQueries({ queryKey: ['phaseStatus', 'Request Info', cycleIdNum, reportIdNum] });
      queryClient.invalidateQueries({ queryKey: ['unified-status', cycleIdNum, reportIdNum] });
    } catch (error: any) {
      console.error('Error handling activity action:', error);
      toast.error(error.response?.data?.detail || `Failed to ${action} activity`);
    }
  };

  const handleUploadDocument = (testCase: TestCase) => {
    setSelectedTestCase(testCase);
    setUploadDialogOpen(true);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type and size
      const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
      const maxSize = 20 * 1024 * 1024; // 20MB
      
      if (!allowedTypes.includes(file.type)) {
        toast.error('Please upload a PDF, image, or Excel file');
        return;
      }
      
      if (file.size > maxSize) {
        toast.error('File size must be less than 20MB');
        return;
      }
      
      setUploadFile(file);
    }
  };

  const handleSubmitUpload = () => {
    if (!selectedTestCase || !uploadFile) return;
    
    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('document_type', 'Source Document'); // Default document type
    formData.append('submission_notes', uploadNotes);
    
    uploadDocumentMutation.mutate(formData);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Submitted': return 'success';
      case 'Pending': return 'warning';
      case 'Overdue': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Submitted': return <CheckCircle />;
      case 'Pending': return <PendingActions />;
      case 'Overdue': return <AccessTime />;
      default: return <QuestionAnswer />;
    }
  };
  
  // Calculate data owners and LOBs from test cases (must be before any conditional returns)
  const uniqueDataOwners = React.useMemo(() => {
    if (!testCases || testCases.length === 0) return 0;
    return new Set(testCases.map((tc: any) => tc.data_owner_id).filter((id: any) => id != null)).size;
  }, [testCases]);
  
  const uniqueLOBs = React.useMemo(() => {
    if (!testCases || testCases.length === 0) return 0;
    // For now, assume each data owner represents a LOB
    // This can be updated if we have actual LOB data in test cases
    return uniqueDataOwners;
  }, [testCases, uniqueDataOwners]);
  
  // Create data owner summaries from test cases
  const dataOwnerSummaries = React.useMemo(() => {
    if (!testCases || testCases.length === 0) return [];
    
    const ownerMap = new Map();
    
    testCases.forEach((tc: any) => {
      if (!tc.data_owner_id) return;
      
      if (!ownerMap.has(tc.data_owner_id)) {
        ownerMap.set(tc.data_owner_id, {
          data_owner_id: tc.data_owner_id,
          data_owner_name: tc.data_owner_name,
          data_owner_email: tc.data_owner_email,
          total_test_cases: 0,
          submitted_test_cases: 0,
          pending_test_cases: 0,
          overdue_test_cases: 0,
          overall_status: 'Pending'
        });
      }
      
      const owner = ownerMap.get(tc.data_owner_id);
      owner.total_test_cases++;
      
      if (tc.status === 'Submitted') {
        owner.submitted_test_cases++;
      } else if (tc.status === 'Overdue') {
        owner.overdue_test_cases++;
      } else {
        owner.pending_test_cases++;
      }
    });
    
    // Update overall status for each owner
    ownerMap.forEach(owner => {
      if (owner.submitted_test_cases === owner.total_test_cases) {
        owner.overall_status = 'Submitted';
      } else if (owner.overdue_test_cases > 0) {
        owner.overall_status = 'Overdue';
      } else {
        owner.overall_status = 'Pending';
      }
    });
    
    return Array.from(ownerMap.values());
  }, [testCases]);

  // Loading state
  if (phaseLoading) {
    return (
      <Container maxWidth={false} sx={{ py: 3 }}>
        <Typography variant="h4" gutterBottom>Loading Request for Information Phase...</Typography>
        <LinearProgress />
      </Container>
    );
  }

  // Error state
  if (phaseError) {
    return (
      <Container maxWidth={false} sx={{ py: 3 }}>
        <Alert severity="error" sx={{ m: 2 }}>
          Failed to load Request for Information phase data
        </Alert>
      </Container>
    );
  }

  // Data owner view
  if (user?.role === UserRole.DATA_OWNER) {
    const portalData = phaseData as DataOwnerPortalData;
    
    return (
      <Container maxWidth={false} sx={{ py: 3 }}>
        {/* Header */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ py: 1.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Assignment color="primary" />
                <Typography variant="h6" component="h1" sx={{ fontWeight: 'medium' }}>
                  {portalData.report_name}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" color="text.secondary">Cycle:</Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {portalData.cycle_name}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" color="text.secondary">Deadline:</Typography>
                  <Typography variant="body2" fontWeight="medium" color={portalData.days_remaining <= 3 ? 'error.main' : 'text.primary'}>
                    {new Date(portalData.submission_deadline).toLocaleDateString()} ({portalData.days_remaining} days)
                  </Typography>
                </Box>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Typography variant="h4" gutterBottom>
          Request for Information - Data Owner Portal
        </Typography>

        {/* Progress Overview */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Your Progress
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Completion Progress</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {portalData.completion_percentage.toFixed(1)}%
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={portalData.completion_percentage} 
                sx={{ height: 8, borderRadius: 4 }}
                color={portalData.completion_percentage === 100 ? 'success' : 'primary'}
              />
            </Box>
            
            <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip 
                  label={`${portalData.total_test_cases} Total`}
                  size="small"
                  variant="outlined"
                  color="info"
                />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip 
                  label={`${portalData.submitted_test_cases} Submitted`}
                  size="small"
                  variant="outlined"
                  color="success"
                />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip 
                  label={`${portalData.pending_test_cases} Pending`}
                  size="small"
                  variant="outlined"
                  color="warning"
                />
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Instructions */}
        {portalData.phase_instructions && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Instructions
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {portalData.phase_instructions}
              </Typography>
            </CardContent>
          </Card>
        )}

        {/* Test Cases */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Your Test Cases ({portalData.test_cases?.length || 0})
            </Typography>
            
            {portalData.test_cases && portalData.test_cases.length > 0 ? (
              <Box sx={{ overflow: 'auto' }}>
                {/* Group test cases by sample */}
                {Object.entries(
                  portalData.test_cases.reduce((acc: any, testCase: any) => {
                    const sampleId = testCase.sample_identifier;
                    if (!acc[sampleId]) {
                      acc[sampleId] = [];
                    }
                    acc[sampleId].push(testCase);
                    return acc;
                  }, {})
                ).map(([sampleId, sampleTestCases]: [string, any]) => (
                  <Card key={sampleId} variant="outlined" sx={{ mb: 3 }}>
                    <CardContent>
                      {/* Sample Header */}
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Typography variant="h6" fontFamily="monospace" color="primary.main">
                            {sampleId}
                          </Typography>
                          <Chip 
                            label={`${sampleTestCases.length} attributes`}
                            size="small"
                            variant="outlined"
                            color="info"
                          />
                        </Box>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Chip 
                            label={`${sampleTestCases.filter((tc: any) => tc.status === 'Submitted').length} submitted`}
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                          <Chip 
                            label={`${sampleTestCases.filter((tc: any) => tc.status === 'Pending').length} pending`}
                            size="small"
                            color="warning"
                            variant="outlined"
                          />
                        </Box>
                      </Box>

                      {/* Attributes for this sample */}
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {sampleTestCases.map((testCase: any) => (
                          <Box 
                            key={testCase.test_case_id}
                            sx={{ 
                              p: 2,
                              bgcolor: testCase.status === 'Submitted' ? 'success.50' : 'grey.50',
                              borderRadius: 1,
                              border: 1,
                              borderColor: testCase.status === 'Submitted' ? 'success.main' : 'grey.200'
                            }}
                          >
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                              <Box sx={{ flex: 1 }}>
                                <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 0.5 }}>
                                  {testCase.attribute_name}
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                  Expected Evidence: {testCase.expected_evidence_type || 'Supporting documentation'}
                                </Typography>
                                {testCase.special_instructions && (
                                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontStyle: 'italic' }}>
                                    Instructions: {testCase.special_instructions}
                                  </Typography>
                                )}
                                {testCase.submission_deadline && (
                                  <Typography variant="caption" color="text.secondary">
                                    Due: {new Date(testCase.submission_deadline).toLocaleDateString()}
                                  </Typography>
                                )}
                              </Box>
                              
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                <Chip 
                                  label={testCase.status || 'Pending'}
                                  size="small"
                                  color={
                                    testCase.status === 'Submitted' ? 'success' :
                                    testCase.status === 'Overdue' ? 'error' : 'warning'
                                  }
                                  variant="filled"
                                />
                              </Box>
                            </Box>

                            {/* Document Upload Section */}
                            {testCase.status !== 'Submitted' ? (
                              <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Upload Supporting Document
                                </Typography>
                                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                                  <Button
                                    variant="outlined"
                                    component="label"
                                    size="small"
                                    startIcon={<CloudUpload />}
                                  >
                                    Choose File
                                    <input
                                      type="file"
                                      hidden
                                      accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                                      onChange={(e) => {
                                        const file = e.target.files?.[0];
                                        if (file) {
                                          console.log('File selected for test case:', testCase.test_case_id, file.name);
                                          // Handle file selection
                                        }
                                      }}
                                    />
                                  </Button>
                                  <Button
                                    variant="contained"
                                    size="small"
                                    disabled
                                    startIcon={<CloudUpload />}
                                  >
                                    Upload
                                  </Button>
                                </Box>
                                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                                  Accepted formats: PDF, JPG, PNG, DOC, DOCX (Max 20MB)
                                </Typography>
                              </Box>
                            ) : (
                              // Show submitted document info
                              testCase.document_submission && (
                                <Box sx={{ mt: 2, p: 2, bgcolor: 'success.50', borderRadius: 1, border: 1, borderColor: 'success.main' }}>
                                  <Typography variant="subtitle2" gutterBottom color="success.main">
                                    Document Submitted
                                  </Typography>
                                  <Typography variant="body2" sx={{ mb: 1 }}>
                                    File: {testCase.document_submission.document_filename}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    Submitted: {new Date(testCase.document_submission.submitted_at).toLocaleString()}
                                  </Typography>
                                  {testCase.document_submission.submission_notes && (
                                    <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                                      Notes: {testCase.document_submission.submission_notes}
                                    </Typography>
                                  )}
                                </Box>
                              )
                            )}
                          </Box>
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                ))}
                
                <Box sx={{ textAlign: 'center', mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Total: {portalData.test_cases.length} test cases across {Object.keys(
                      portalData.test_cases.reduce((acc: any, testCase: any) => {
                        acc[testCase.sample_identifier] = true;
                        return acc;
                      }, {})
                    ).length} samples
                  </Typography>
                </Box>
              </Box>
            ) : (
              <Alert severity="info">
                No test cases assigned to you yet. Please check back later or contact the tester if you believe this is an error.
              </Alert>
            )}
          </CardContent>
        </Card>
      </Container>
    );
  }

  // Workflow steps function

  // Tester/Admin View
  const testerData = phaseData as TesterPhaseView;

  // Show loading state if unified status is still loading  
  if (statusLoading) {
    return (
      <Container maxWidth={false} sx={{ py: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  // If phase hasn't been started yet, show simplified view with unified status workflow
  if (unifiedPhaseStatus?.phase_status === 'not_started') {
    return (
      <Container maxWidth={false} sx={{ py: 3 }}>
        {/* Report Information Header */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ py: 1.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
              {/* Left side - Report title */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Assignment color="primary" />
                <Typography variant="h6" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportInfo?.report_name || 'Loading...'}
                </Typography>
              </Box>
              
              {/* Right side - Key metadata in compact format */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
                {reportInfoLoading ? (
                  <Box sx={{ width: 200 }}>
                    <LinearProgress />
                  </Box>
                ) : (
                  <>
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
                    
                                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Person color="action" fontSize="small" />
                    <Typography variant="body2" color="text.secondary">Owner:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {reportInfo?.report_owner_name || 'Not specified'}
                    </Typography>
                  </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" color="text.secondary">ID:</Typography>
                      <Typography variant="body2" fontWeight="medium" fontFamily="monospace">
                        {reportInfo?.report_id || reportId}
                      </Typography>
                    </Box>
                  </>
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Typography variant="h4" gutterBottom>
          Request for Information Phase
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Request Info Phase - Collecting additional information and documentation from data owners
        </Typography>


        {/* Request Info Workflow Visual */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Assignment color="primary" />
              Request for Information Phase Workflow
            </Typography>
            
            <Box sx={{ mt: 2 }}>
              {unifiedPhaseStatus?.activities ? (
                <DynamicActivityCards
                  activities={unifiedPhaseStatus.activities}
                  cycleId={cycleIdNum}
                  reportId={reportIdNum}
                  phaseName="Request Info"
                  phaseStatus={unifiedPhaseStatus.phase_status}
                  overallCompletion={unifiedPhaseStatus.overall_completion_percentage}
                  onActivityAction={handleActivityAction}
                  />
                ) : (
                  <Box sx={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    minHeight: 200, 
                    flexDirection: 'column', 
                    gap: 2 
                  }}>
                    <CircularProgress />
                    <Typography variant="body2" color="text.secondary">
                      Loading request info activities...
                    </Typography>
                  </Box>
                )}
            </Box>
          </CardContent>
        </Card>

      </Container>
    );
  }

  // Active phase view
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
      
      {/* Workflow Progress */}
      {/* Workflow Progress - Removed as it doesn't belong on phase detail pages */}
      
      {/* Report Information Header */}
      <Card sx={{ mb: 3, mt: 3 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            {/* Left side - Report title and phase description */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Assignment color="primary" />
              <Box>
                <Typography variant="h6" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportInfo?.report_name || 'Loading...'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Request Info Phase - Collecting additional information and documentation from data owners
                </Typography>
              </Box>
            </Box>
            
            {/* Right side - Key metadata in compact format */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
              {reportInfoLoading ? (
                <Box sx={{ width: 200 }}>
                  <LinearProgress />
                </Box>
              ) : (
                <>
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
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Person color="action" fontSize="small" />
                    <Typography variant="body2" color="text.secondary">Owner:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {reportInfo?.report_owner_name || 'Not specified'}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" color="text.secondary">ID:</Typography>
                    <Typography variant="body2" fontWeight="medium" fontFamily="monospace">
                      {reportInfo?.report_id || reportId}
                    </Typography>
                  </Box>
                </>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Request Info Metrics Row 1 - Six Key Metrics */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 3 }}>
        <Box sx={{ flex: '1 1 calc(16.666% - 24px)', minWidth: '200px' }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="primary.main" fontWeight="bold">
                {testerData?.phase?.total_attributes || requestInfoStatus?.total_attributes || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Attributes
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 calc(16.666% - 24px)', minWidth: '200px' }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="success.main" fontWeight="bold">
                {testerData?.phase?.scoped_attributes || requestInfoStatus?.scoped_attributes || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Scoped Attributes
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 calc(16.666% - 24px)', minWidth: '200px' }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="info.main" fontWeight="bold">
                {testerData?.phase?.total_samples || requestInfoStatus?.total_samples || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Samples
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 calc(16.666% - 24px)', minWidth: '200px' }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="warning.main" fontWeight="bold">
                {uniqueLOBs}/{uniqueDataOwners}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                LOBs / Data Owners
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 calc(16.666% - 24px)', minWidth: '200px' }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="error.main" fontWeight="bold">
                {(testerData?.phase?.uploaded_test_cases || requestInfoStatus?.uploaded_test_cases || requestInfoStatus?.submitted_test_cases || 0)}/{(testerData?.phase?.total_test_cases || requestInfoStatus?.total_test_cases || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Test Cases (Uploaded/Total)
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 calc(16.666% - 24px)', minWidth: '200px' }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="primary.main" fontWeight="bold">
                {(() => {
                  const startDate = testerData?.phase?.started_at || requestInfoStatus?.started_at;
                  const completedDate = testerData?.phase?.completed_at || requestInfoStatus?.completed_at;
                  if (!startDate) return 0;
                  const end = completedDate ? new Date(completedDate) : new Date();
                  const start = new Date(startDate);
                  return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
                })()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {(testerData?.phase?.completed_at || requestInfoStatus?.completed_at) ? 'Completion Time (days)' : 'Days Elapsed'}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Row 2: On-Time Status + Phase Controls */}
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3 }}>
        <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '300px' }}>
          <Card sx={{ height: 100 }}>
            <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <Typography 
                variant="h3" 
                color={
                  unifiedPhaseStatus?.phase_status === 'completed' ? 
                    'success.main' :
                  unifiedPhaseStatus?.phase_status === 'in_progress' ?
                    'primary.main' : 'warning.main'
                } 
                component="div"
                sx={{ fontSize: '1.5rem' }}
              >
                {unifiedPhaseStatus?.phase_status === 'completed' ? 
                  'Yes - Completed On-Time' :
                unifiedPhaseStatus?.phase_status === 'in_progress' ?
                  'On Track' : 'Not Started'
                }
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {unifiedPhaseStatus?.phase_status === 'completed' ? 'On-Time Completion Status' : 'Current Schedule Status'}
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '300px' }}>
          <Card sx={{ height: 100 }}>
            <CardContent sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" sx={{ fontSize: '1rem' }}>
                  Phase Controls
                </Typography>
                
                {/* Status Update Controls */}
                {unifiedPhaseStatus?.phase_status === 'in_progress' && (
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip
                      label="At Risk"
                      size="small"
                      color="warning"
                      variant="outlined"
                      clickable
                      onClick={() => {/* Handle status update */}}
                      sx={{ fontSize: '0.7rem' }}
                    />
                    <Chip
                      label="Off Track"
                      size="small"
                      color="error"
                      variant="outlined"
                      clickable
                      onClick={() => {/* Handle status update */}}
                      sx={{ fontSize: '0.7rem' }}
                    />
                  </Box>
                )}
              </Box>
              
              {/* Completion Requirements */}
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                  {(() => {
                    const status = unifiedPhaseStatus?.phase_status as string;
                    if (status === 'not_started') {
                      return 'To complete: Start phase and generate test cases';
                    } else if (status === 'completed') {
                      return 'Phase completed successfully - all requirements met';
                    } else {
                      return 'To complete: Upload and validate all test case documentation';
                    }
                  })()}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>


      {/* Request Info Workflow Visual */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Assignment color="primary" />
            Request for Information Phase Workflow
          </Typography>
          
          <Box sx={{ mt: 2 }}>
            {unifiedPhaseStatus?.activities ? (
              <DynamicActivityCards
                activities={unifiedPhaseStatus.activities}
                cycleId={cycleIdNum}
                reportId={reportIdNum}
                phaseName="Request Info"
                phaseStatus={unifiedPhaseStatus.phase_status}
                overallCompletion={unifiedPhaseStatus.overall_completion_percentage}
                onActivityAction={handleActivityAction}
              />
            ) : (
              <Box sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                minHeight: 200, 
                flexDirection: 'column', 
                gap: 2 
              }}>
                <CircularProgress />
                <Typography variant="body2" color="text.secondary">
                  Loading request info activities...
                </Typography>
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Card>
        <CardContent sx={{ p: 0 }}>
          <Tabs 
            value={tabValue} 
            onChange={(_, newValue) => setTabValue(newValue)}
            sx={{ borderBottom: 1, borderColor: 'divider', px: 3, pt: 2 }}
          >
            <Tab 
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Assignment />
                  Test Cases
                  <Chip 
                    label={testCases?.length || 0} 
                    color="primary" 
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Box>
              } 
            />
            <Tab 
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Person />
                  Data Owners
                  <Chip 
                    label={uniqueDataOwners} 
                    color="primary" 
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Box>
              } 
            />
            <Tab 
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <QuestionAnswer />
                  Data Source Queries
                  <Chip 
                    label="NEW" 
                    color="secondary" 
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Box>
              } 
            />
          </Tabs>
        </CardContent>

        {/* Test Cases Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                Test Cases ({testCases?.length || 0})
              </Typography>
              
              <Stack direction="row" spacing={2}>
                <Button
                  variant="outlined"
                  size="small"
                  disabled
                >
                  Export
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => queryClient.invalidateQueries({ queryKey: ['test-cases'] })}
                >
                  Refresh
                </Button>
              </Stack>
            </Box>

            {testCasesLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <LinearProgress sx={{ width: '100%' }} />
              </Box>
            ) : testCases && testCases.length > 0 ? (
              <Box sx={{ overflow: 'auto' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Test cases generated from data owner assignments and sample data. Data owners will receive notifications to upload supporting documentation.
                </Typography>
                
                <TestCasesTable 
                  testCases={testCases}
                  userRole={user?.role || 'Tester'}
                  onEdit={(testCase) => {
                    // Handle edit action
                    console.log('Edit test case:', testCase);
                    toast('Edit functionality coming soon', { icon: 'ℹ️' });
                  }}
                  onResend={async (testCase) => {
                    // Handle resend action
                    console.log('Resend to data owner:', testCase);
                    try {
                      await apiClient.post(`/request-info/test-cases/${testCase.test_case_id}/resend`, {
                        reason: 'Evidence requires revision',
                        deadline: null,
                        notify_data_owner: true
                      });
                      toast.success(`Notification resent to ${testCase.data_owner_name}`);
                      // Refresh the test cases list
                      queryClient.invalidateQueries({ queryKey: ['test-cases'] });
                    } catch (error: any) {
                      console.error('Failed to resend:', error);
                      toast.error(error.response?.data?.detail || 'Failed to resend notification');
                    }
                  }}
                  onViewEvidence={(testCase) => {
                    // Handle view evidence action - now handled internally by the modal
                    console.log('View evidence for:', testCase);
                  }}
                  onValidate={async (testCase, status) => {
                    // Handle validation action
                    console.log('Validate test case:', testCase, 'Status:', status);
                    
                    try {
                      // First, get the evidence details for this test case
                      const evidenceResponse = await apiClient.get(`/request-info/test-cases/${testCase.test_case_id}/evidence-details`);
                      const currentEvidence = evidenceResponse.data.current_evidence;
                      
                      if (!currentEvidence || currentEvidence.length === 0) {
                        toast.error('No evidence found to approve/reject');
                        return;
                      }
                      
                      // Get the most recent evidence
                      const latestEvidence = currentEvidence[0];
                      
                      // Submit the tester decision
                      await apiClient.post(`/request-info/evidence/${latestEvidence.id}/review`, {
                        decision: status.toLowerCase(), // 'approved' or 'rejected'
                        decision_notes: status === 'Approved' ? 'Evidence approved' : 'Evidence requires revision',
                        requires_resubmission: status === 'Rejected',
                      });
                      
                      toast.success(`Test case ${status.toLowerCase()}`);
                      
                      // Refresh the test cases list
                      queryClient.invalidateQueries({ queryKey: ['request-info-phase', cycleIdNum, reportIdNum] });
                    } catch (error: any) {
                      console.error('Failed to submit decision:', error);
                      toast.error(error.response?.data?.detail || `Failed to ${status.toLowerCase()} test case`);
                    }
                  }}
                  onViewSampleDetails={(testCase) => {
                    // Handle view sample details
                    setSelectedSampleDetails(testCase);
                    setSampleDetailsDialogOpen(true);
                  }}
                />
              </Box>
            ) : (
              <Card sx={{ p: 3, textAlign: 'center', bgcolor: 'warning.50', border: 1, borderColor: 'warning.main' }}>
                <Warning color="warning" sx={{ fontSize: 48, mb: 2 }} />
                <Typography variant="h6" gutterBottom color="warning.main">
                  No Test Cases Available
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Test cases cannot be generated because no sample data is available for this cycle and report.
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Please ensure the Sample Selection phase has been completed and samples have been approved before starting the Request for Information phase.
                </Typography>
              </Card>
            )}
          </Box>
        </TabPanel>

        {/* Data Owners Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                Data Owners ({dataOwnerSummaries.length})
              </Typography>
            </Box>
            
            {dataOwnerSummaries.length > 0 ? (
              <Box sx={{ display: 'grid', gap: 3, gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))' }}>
                {dataOwnerSummaries.map((dp: any) => (
                  <Card key={dp.data_owner_id} variant="outlined">
                    <CardContent>
                      <Stack direction="row" alignItems="center" spacing={2} mb={2}>
                        <Person color="primary" />
                        <Box flex={1}>
                          <Typography variant="h6">{dp.data_owner_name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {dp.data_owner_email}
                          </Typography>
                        </Box>
                        <Chip
                          label={dp.overall_status}
                          color={
                            dp.overall_status === 'Submitted' ? 'success' :
                            dp.overall_status === 'Overdue' ? 'error' : 'warning'
                          }
                          size="small"
                        />
                      </Stack>

                      <Stack spacing={1} mb={2}>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2">Total Test Cases:</Typography>
                          <Typography variant="body2" fontWeight="bold">{dp.total_test_cases}</Typography>
                        </Box>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2">Submitted:</Typography>
                          <Typography variant="body2" fontWeight="bold" color="success.main">{dp.submitted_test_cases}</Typography>
                        </Box>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2">Pending:</Typography>
                          <Typography variant="body2" fontWeight="bold" color="warning.main">{dp.pending_test_cases}</Typography>
                        </Box>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2">Overdue:</Typography>
                          <Typography variant="body2" fontWeight="bold" color="error.main">{dp.overdue_test_cases}</Typography>
                        </Box>
                      </Stack>

                      <Box mb={2}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Assigned Attributes:
                        </Typography>
                        <Box display="flex" flexWrap="wrap" gap={0.5}>
                          {dp.assigned_attributes?.map((attr: string, index: number) => (
                            <Chip key={index} label={attr} size="small" variant="outlined" />
                          )) || (
                            <Typography variant="caption" color="text.secondary" fontStyle="italic">
                              No attributes assigned
                            </Typography>
                          )}
                        </Box>
                      </Box>

                      <Stack direction="row" spacing={1}>
                        <Chip
                          icon={dp.notification_sent ? <CheckCircle /> : <Warning />}
                          label={dp.notification_sent ? 'Notified' : 'Not Notified'}
                          color={dp.notification_sent ? 'success' : 'warning'}
                          size="small"
                        />
                        <Chip
                          icon={dp.portal_accessed ? <CheckCircle /> : <Warning />}
                          label={dp.portal_accessed ? 'Accessed' : 'Not Accessed'}
                          color={dp.portal_accessed ? 'success' : 'warning'}
                          size="small"
                        />
                      </Stack>

                      {dp.last_activity && (
                        <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                          Last Activity: {new Date(dp.last_activity).toLocaleString()}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </Box>
            ) : (
              <Alert severity="info">
                No data owners assigned yet. Data owners will appear here once assignments are made.
              </Alert>
            )}
          </Box>
        </TabPanel>

        {/* Data Source Queries Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ p: 3 }}>
            <DataSourceQueryPanel
              cycleId={cycleIdNum}
              reportId={reportIdNum}
              onQueryResultsReceived={(results) => {
                // Handle query results - could be used to update test cases or generate new ones
                console.log('Query results received:', results);
                toast.success(`Received ${results.length} records from query`);
              }}
            />
          </Box>
        </TabPanel>
      </Card>

      {/* Sample Details Dialog */}
      <Dialog
        open={sampleDetailsDialogOpen}
        onClose={() => {
          setSampleDetailsDialogOpen(false);
          setSelectedSampleDetails(null);
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Visibility />
            Sample Details
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedSampleDetails && (
            <Stack spacing={3} sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
                  <Typography variant="subtitle2" color="text.secondary">Sample ID</Typography>
                  <Typography variant="body1" sx={{ fontFamily: 'monospace', mb: 2 }}>
                    {selectedSampleDetails.sample_id}
                  </Typography>
                </Box>
                <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
                  <Typography variant="subtitle2" color="text.secondary">Test Case ID</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {selectedSampleDetails.test_case_number || selectedSampleDetails.test_case_id}
                  </Typography>
                </Box>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>Primary Key Values</Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Attribute</TableCell>
                        <TableCell>Value</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedSampleDetails.primary_key_attributes && typeof selectedSampleDetails.primary_key_attributes === 'object' ? (
                        Object.entries(selectedSampleDetails.primary_key_attributes).map(([key, value]) => (
                          <TableRow key={key}>
                            <TableCell>{key}</TableCell>
                            <TableCell>{String(value)}</TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={2} align="center">No primary key values</TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
              <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
                  <Typography variant="subtitle2" color="text.secondary">Attribute Name</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {selectedSampleDetails.attribute_name}
                  </Typography>
                </Box>
                <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
                  <Typography variant="subtitle2" color="text.secondary">Data Owner</Typography>
                  <Typography variant="body1" sx={{ mb: 1 }}>
                    {selectedSampleDetails.data_owner_name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {selectedSampleDetails.data_owner_email}
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
                  <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                  <Chip
                    label={selectedSampleDetails.status}
                    color={selectedSampleDetails.status === 'Submitted' ? 'success' : selectedSampleDetails.status === 'Overdue' ? 'error' : 'warning'}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                </Box>
                <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
                  <Typography variant="subtitle2" color="text.secondary">Validation Status</Typography>
                  <Chip
                    label={selectedSampleDetails.validation_status || 'Pending'}
                    color={selectedSampleDetails.validation_status === 'Approved' ? 'success' : selectedSampleDetails.validation_status === 'Rejected' ? 'error' : 'default'}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Box>
              <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                {selectedSampleDetails.submission_deadline && (
                  <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
                    <Typography variant="subtitle2" color="text.secondary">Submission Deadline</Typography>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                      {new Date(selectedSampleDetails.submission_deadline).toLocaleString()}
                    </Typography>
                  </Box>
                )}
                {selectedSampleDetails.submitted_at && (
                  <Box sx={{ flex: '1 1 45%', minWidth: '250px' }}>
                    <Typography variant="subtitle2" color="text.secondary">Submitted At</Typography>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                      {new Date(selectedSampleDetails.submitted_at).toLocaleString()}
                    </Typography>
                  </Box>
                )}
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Evidence Type</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                  {selectedSampleDetails.expected_evidence_type === 'Data Source' ? (
                    <>
                      <Assignment color="action" />
                      <Typography variant="body1">Data Source Query</Typography>
                    </>
                  ) : (
                    <>
                      <Description color="action" />
                      <Typography variant="body1">Document Upload</Typography>
                    </>
                  )}
                </Box>
              </Box>
              {selectedSampleDetails.special_instructions && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Special Instructions</Typography>
                  <Paper variant="outlined" sx={{ p: 2, mt: 1, bgcolor: 'grey.50' }}>
                    <Typography variant="body2">
                      {selectedSampleDetails.special_instructions}
                    </Typography>
                  </Paper>
                </Box>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setSampleDetailsDialogOpen(false);
            setSelectedSampleDetails(null);
          }}>
            Close
          </Button>
          {selectedSampleDetails && (
            <Button
              variant="contained"
              startIcon={<Visibility />}
              onClick={() => {
                // Open evidence viewer
                toast('Evidence viewer coming soon', { icon: 'ℹ️' });
                setSampleDetailsDialogOpen(false);
              }}
              disabled={selectedSampleDetails.submission_count === 0}
            >
              View Evidence
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Start Phase Dialog */}
      <Dialog open={startPhaseDialogOpen} onClose={() => setStartPhaseDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PlayArrow color="primary" />
            Start Request for Information Phase
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Stack spacing={3}>
            <Alert severity="info">
              Starting this phase will generate test cases based on Sample × Non-PK Scoped Attributes matrix and notify data owners to submit supporting documentation.
            </Alert>
            
            <TextField
              label="Instructions for Data Owners"
              multiline
              rows={4}
              fullWidth
              value={startPhaseForm.instructions}
              onChange={(e) => setStartPhaseForm(prev => ({ ...prev, instructions: e.target.value }))}
              placeholder="Provide clear instructions for data owners on what documentation to submit..."
            />
            
            <TextField
              label="Submission Deadline"
              type="datetime-local"
              fullWidth
              value={startPhaseForm.submission_deadline}
              onChange={(e) => setStartPhaseForm(prev => ({ ...prev, submission_deadline: e.target.value }))}
              InputLabelProps={{ shrink: true }}
              helperText="If not set, defaults to 7 days from now"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStartPhaseDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={() => startPhaseMutation.mutate()}
            disabled={startPhaseMutation.isPending}
            startIcon={startPhaseMutation.isPending ? <CircularProgress size={20} /> : <PlayArrow />}
          >
            {startPhaseMutation.isPending ? 'Starting Phase...' : 'Start Phase'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default NewRequestInfoPage; 