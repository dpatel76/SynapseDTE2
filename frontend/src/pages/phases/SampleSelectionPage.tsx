import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';
import { DynamicActivityCards } from '../../components/phase/DynamicActivityCards';
import { useUniversalAssignments } from '../../hooks/useUniversalAssignments';
import { UniversalAssignmentAlert } from '../../components/UniversalAssignmentAlert';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Checkbox,
  Alert,
  Stack,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  FormControlLabel,
  Switch,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Divider
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  PlayArrow as PlayArrowIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Assignment as AssignmentIcon,
  Psychology as PsychologyIcon,
  Send as SendIcon,
  Edit as EditIcon,
  CloudUpload as CloudUploadIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  ThumbUp as ThumbUpIcon,
  TableView as TableViewIcon,
  History as HistoryIcon,
  Message as MessageIcon,
  Science as ScienceIcon,
  AutoFixHigh as AutoFixHighIcon,
  Info as InfoIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import IntelligentSamplingPanel from '../../components/IntelligentSamplingPanel';
import PhaseDocumentManager from '../../components/documents/PhaseDocumentManager';
import ReportOwnerFeedback from '../../components/sample-selection/ReportOwnerFeedback';
// Removed ReportOwnerFeedbackChecker import - not relevant for sample selection feedback
import SampleSelectionVersionHistory from '../../components/sample-selection/SampleSelectionVersionHistory';

interface Sample {
  sample_id: string;
  primary_key_value: string;
  sample_data: Record<string, any>;
  generation_method: 'LLM Generated' | 'Manual Upload' | 'Intelligent Sampling';
  generated_at: string;
  generated_by: string;
  tester_decision?: 'approved' | 'rejected' | 'pending' | null;
  tester_decision_notes?: string;
  tester_decision_at?: string;
  tester_decision_by?: string;
  lob_assignment?: string | null;
  report_owner_decision?: 'approved' | 'rejected' | 'revision_required' | 'pending' | null;
  report_owner_feedback?: string;
  report_owner_reviewed_at?: string;
  report_owner_reviewed_by?: string;
  version_number?: number;
  version_reviewed?: number;
  is_submitted?: boolean;
  sample_category?: 'CLEAN' | 'ANOMALY' | 'BOUNDARY';
  rationale?: string;
  attribute_focus?: string;
  risk_score?: number;
  confidence_score?: number;
}

interface SampleSubmission {
  submission_id: string;
  version_number: number;
  submitted_at: string;
  submitted_by: string;
  sample_ids: string[];
  status: 'pending' | 'approved' | 'rejected' | 'revision_required';
  feedback?: string;
  approved_version?: boolean;
}

interface SampleSelectionVersion {
  version_id: string;
  version_number: number;
  version_status: 'draft' | 'pending_approval' | 'approved' | 'rejected' | 'superseded';
  created_at: string;
  created_by: string;
  created_by_name?: string;
  is_current: boolean;
  total_samples: number;
  approved_samples: number;
  rejected_samples: number;
  pending_samples: number;
  change_reason?: string;
}

interface ReportInfo {
  report_id: number;
  report_name: string;
  lob_name: string;
  tester_name?: string;
  report_owner_name?: string;
  regulatory_framework?: string;
}

interface SampleSelectionPhaseStatus {
  phase_status: 'Not Started' | 'In Progress' | 'Pending Approval' | 'Complete';
  total_samples: number;
  included_samples: number;
  excluded_samples: number;
  pending_samples: number;
  submitted_samples: number;
  approved_samples: number;
  revision_required_samples: number;
  can_proceed_to_testing: boolean;
  current_version: number;
  has_submissions: boolean;
  // New fields for metrics
  total_attributes?: number;
  scoped_attributes?: number;
  pk_attributes?: number;
  total_lobs?: number;
  total_data_providers?: number;
  started_at?: string;
  completed_at?: string;
}

const SampleSelectionPage: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const cycleIdNum = parseInt(cycleId || '0');
  const reportIdNum = parseInt(reportId || '0');
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showToast: showToastRaw } = useNotifications();

  const showToast = React.useMemo(() => ({
    success: (message: string) => showToastRaw('success', message),
    error: (message: string) => showToastRaw('error', message),
    warning: (message: string) => showToastRaw('warning', message),
    info: (message: string) => showToastRaw('info', message)
  }), [showToastRaw]);

  // Unified status system
  const { data: unifiedPhaseStatus, isLoading: statusLoading, refetch: refetchStatus } = usePhaseStatus('Sample Selection', cycleIdNum, reportIdNum);

  // Universal Assignments integration
  const {
    assignments,
    hasAssignment,
    canDirectAccess,
    acknowledgeAssignment,
    startAssignment,
    completeAssignment,
  } = useUniversalAssignments({
    phase: 'Sample Selection',
    cycleId: cycleIdNum,
    reportId: reportIdNum,
  });

  // State
  const [samples, setSamples] = useState<Sample[]>([]);
  const [submissions, setSubmissions] = useState<SampleSubmission[]>([]);
  const [reportInfo, setReportInfo] = useState<ReportInfo | null>(null);
  const [phaseStatus, setPhaseStatus] = useState<SampleSelectionPhaseStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [phaseLoading, setPhaseLoading] = useState(false);
  const [bulkSelectedSamples, setBulkSelectedSamples] = useState<string[]>([]);
  const [primaryKeyColumns, setPrimaryKeyColumns] = useState<string[]>([]);
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [showEnhancedGenerateDialog, setShowEnhancedGenerateDialog] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showSubmitDialog, setShowSubmitDialog] = useState(false);
  const [showVersionHistoryDialog, setShowVersionHistoryDialog] = useState(false);
  const [submissionNotes, setSubmissionNotes] = useState('');
  const [sampleSize, setSampleSize] = useState(100);
  const [viewingVersion, setViewingVersion] = useState<number | null>(null);
  
  // Enhanced generate dialog state
  const [enhancedSampleSize, setEnhancedSampleSize] = useState(100);
  const [enhancedSamplingStrategy, setEnhancedSamplingStrategy] = useState('intelligent');
  const [enhancedDataSource, setEnhancedDataSource] = useState('');
  const [useAnomalyInsights, setUseAnomalyInsights] = useState(true);
  const [enhancedGenerating, setEnhancedGenerating] = useState(false);
  const [basicGenerating, setBasicGenerating] = useState(false);
  const [dataSources, setDataSources] = useState<any[]>([]);
  const [reportOwnerFeedback, setReportOwnerFeedback] = useState<any>(null);
  const [scopedAttributes, setScopedAttributes] = useState<any[]>([]);
  const [isCreatingNewVersion, setIsCreatingNewVersion] = useState(false);
  const [viewSampleDialog, setViewSampleDialog] = useState<{ open: boolean; sample: Sample | null }>({
    open: false,
    sample: null
  });
  const [currentSubmission, setCurrentSubmission] = useState<any>(null);
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [reviewDecision, setReviewDecision] = useState<'approved' | 'rejected' | 'revision_required'>('approved');
  const [reviewFeedback, setReviewFeedback] = useState('');
  const [individualFeedback, setIndividualFeedback] = useState<{ [sampleId: string]: string }>({});
  const [individualDecisions, setIndividualDecisions] = useState<{ [sampleId: string]: 'approved' | 'rejected' | null }>({});
  const [availableLOBs, setAvailableLOBs] = useState<string[]>([]);
  const [sampleLOBs, setSampleLOBs] = useState<{ [sampleId: string]: string }>({});
  const [samplingMethod, setSamplingMethod] = useState<'random' | 'intelligent'>('random');
  const [profilingJobId, setProfilingJobId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0); // Tab state
  const [hasReportOwnerFeedback, setHasReportOwnerFeedback] = useState(false);
  
  // Version management states
  const [versions, setVersions] = useState<SampleSelectionVersion[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  const [versionsLoaded, setVersionsLoaded] = useState(false);

  // Filter samples by selected version
  const filteredSamples = React.useMemo(() => {
    console.log('Filtering samples:', { 
      totalSamples: samples.length, 
      selectedVersionId, 
      versionsCount: versions.length,
      sampleVersions: Array.from(new Set(samples.map(s => s.version_number)))
    });
    
    // If no versions loaded yet or no version selected, show the latest version samples
    if (!selectedVersionId || !versions.length) {
      // Get the highest version number (latest version)
      const latestVersionNumber = Math.max(...samples.map(s => s.version_number || 1), 1);
      const filtered = samples.filter(sample => (sample.version_number || 1) === latestVersionNumber);
      console.log(`No version selected, showing latest version ${latestVersionNumber}: ${filtered.length} samples`);
      return filtered;
    }
    
    // Find the selected version number
    const selectedVersion = versions.find(v => v.version_id === selectedVersionId);
    if (!selectedVersion) {
      // If selected version not found, show latest version
      const latestVersionNumber = Math.max(...samples.map(s => s.version_number || 1), 1);
      const filtered = samples.filter(sample => (sample.version_number || 1) === latestVersionNumber);
      console.log(`Selected version not found, showing latest version ${latestVersionNumber}: ${filtered.length} samples`);
      return filtered;
    }
    
    // Filter samples by version number
    const filtered = samples.filter(sample => 
      (sample.version_number || 1) === selectedVersion.version_number
    );
    console.log(`Showing version ${selectedVersion.version_number}: ${filtered.length} samples`);
    return filtered;
  }, [samples, selectedVersionId, versions]);

  // Load report info
  const loadReportInfo = useCallback(async () => {
    try {
      const response = await apiClient.get(`/cycle-reports/${cycleIdNum}/reports/${reportIdNum}`);
      setReportInfo(response.data);
    } catch (error) {
      console.error('Error loading report info:', error);
    }
  }, [cycleIdNum, reportIdNum]);

  // Load scoped attributes for sample generation
  const loadScopedAttributes = useCallback(async () => {
    try {
      console.log('Loading scoped attributes for cycle:', cycleIdNum, 'report:', reportIdNum);
      const response = await apiClient.get(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/attributes`);
      console.log('Scoping attributes response:', response.data);
      
      if (!response.data || !Array.isArray(response.data)) {
        console.error('Invalid response format:', response.data);
        setScopedAttributes([]);
        return;
      }
      
      // Debug: Check what fields are available
      if (response.data.length > 0) {
        console.log('Sample attribute fields:', Object.keys(response.data[0]));
        console.log('First attribute:', response.data[0]);
      }
      
      const scoped = response.data.filter((attr: any) => {
        // The API returns selected_for_testing based on tester_decision == 'accept'
        return attr.selected_for_testing === true;
      });
      
      setScopedAttributes(scoped);
      console.log('Loaded scoped attributes:', scoped.length, 'out of', response.data.length, 'total attributes');
      
      // If no scoped attributes found, log more details
      if (scoped.length === 0 && response.data.length > 0) {
        console.log('No scoped attributes found. Sample attribute values:');
        response.data.slice(0, 3).forEach((attr: any, idx: number) => {
          console.log(`  Attr ${idx}: final_scoping=${attr.final_scoping}, selected_for_testing=${attr.selected_for_testing}, tester_decision=${attr.tester_decision}`);
        });
      }
    } catch (error: any) {
      console.error('Error loading scoped attributes:', error);
      console.error('Error details:', error.response?.data || error.message);
      setScopedAttributes([]);
    }
  }, [cycleIdNum, reportIdNum]);

  // Note: Removed loadProfilingJobId as it's not relevant for sample selection

  // Load available LOBs for this report
  const loadAvailableLOBs = useCallback(async () => {
    try {
      // Use report-specific endpoint to get only relevant LOBs
      const response = await apiClient.get(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/available-lobs`);
      console.log('Report-specific LOB response:', response.data);
      
      // Extract LOB names from the available_lobs array
      const lobs = response.data.available_lobs || [];
      const lobNames = lobs.map((lob: any) => lob.lob_name);
      console.log('Available LOBs for this report:', lobNames);
      setAvailableLOBs(lobNames);
    } catch (error) {
      console.error('Error loading LOBs:', error);
      // Fallback to empty array if endpoint fails
      setAvailableLOBs([]);
    }
  }, [cycleIdNum, reportIdNum]);

  // Load versions
  const loadVersions = useCallback(async () => {
    try {
      const response = await apiClient.get(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/versions`);
      console.log('Versions response:', response.data);
      setVersions(response.data || []);
      setVersionsLoaded(true);
      
      // Role-based version selection
      if (user?.role === 'Report Owner') {
        // Report Owner should see the version with the MOST feedback (main submission)
        // Find the version with the most report owner decisions
        let feedbackVersion = null;
        let maxFeedbackCount = 0;
        
        for (const version of response.data || []) {
          // Check if this version has report owner decisions
          try {
            const samplesResp = await apiClient.get(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples?version=${version.version_number}`);
            const samples = samplesResp.data.samples || [];
            const feedbackCount = samples.filter((s: any) => s.report_owner_decision).length;
            
            if (feedbackCount > maxFeedbackCount) {
              maxFeedbackCount = feedbackCount;
              feedbackVersion = version;
            }
            
            console.log(`Version ${version.version_number}: ${feedbackCount} samples with RO decisions`);
          } catch (error) {
            console.warn(`Error checking version ${version.version_number} for RO feedback:`, error);
          }
        }
        
        if (feedbackVersion) {
          console.log(`Report Owner viewing version ${feedbackVersion.version_number} (has their feedback)`);
          setSelectedVersionId(feedbackVersion.version_id);
        } else {
          // Fallback to latest version if no feedback found
          const latestVersion = response.data.reduce((latest: any, v: any) => 
            (v.version_number > latest.version_number) ? v : latest
          );
          setSelectedVersionId(latestVersion.version_id);
        }
      } else {
        // For Testers: Show current version or latest version
        const currentVersion = response.data?.find((v: any) => v.is_current);
        if (currentVersion) {
          setSelectedVersionId(currentVersion.version_id);
        } else if (response.data && response.data.length > 0) {
          // If no current version, select the latest version (highest version number)
          const latestVersion = response.data.reduce((latest: any, v: any) => 
            (v.version_number > latest.version_number) ? v : latest
          );
          setSelectedVersionId(latestVersion.version_id);
        }
      }
    } catch (error) {
      console.error('Error loading versions:', error);
      setVersions([]);
      setVersionsLoaded(true);
    }
  }, [cycleIdNum, reportIdNum]);

  // Load available data sources
  const loadDataSources = useCallback(async () => {
    try {
      console.log('Loading data sources for cycle:', cycleIdNum, 'report:', reportIdNum);
      // Try to get data sources from the planning phase
      const response = await apiClient.get(`/data-sources`, {
        params: {
          cycle_id: cycleIdNum,
          report_id: reportIdNum
        }
      });
      console.log('Data sources response:', response.data);
      const sources = response.data || [];
      setDataSources(sources);
      // Set default data source if available
      if (sources.length > 0 && !enhancedDataSource) {
        setEnhancedDataSource(sources[0].id);
      }
    } catch (error) {
      console.error('Error loading data sources:', error);
      // Fallback - try to get from cycle/report endpoint
      try {
        const fallbackResponse = await apiClient.get(`/cycles/${cycleIdNum}/reports/${reportIdNum}/data-sources`);
        console.log('Fallback data sources response:', fallbackResponse.data);
        const sources = fallbackResponse.data || [];
        setDataSources(sources);
        // Set default data source if available
        if (sources.length > 0 && !enhancedDataSource) {
          setEnhancedDataSource(sources[0].id);
        }
      } catch (fallbackError) {
        console.error('Fallback error loading data sources:', fallbackError);
        setDataSources([]);
      }
    }
  }, [cycleIdNum, reportIdNum]);

  // Load samples
  const loadSamples = useCallback(async () => {
    try {
      // First get the latest phase status to ensure we have current data
      const analyticsResp = await apiClient.get(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/analytics`);
      const currentPhaseStatus = analyticsResp.data.phase_status;
      
      // If Report Owner, check for universal assignments
      console.log('LoadSamples - User role:', user?.role);
      console.log('LoadSamples - Current phase status:', currentPhaseStatus);
      
      if (user?.role === 'Report Owner') {
        console.log('Report Owner loading assignments...');
        
        try {
          // Check for sample selection assignments for this Report Owner
          console.log('Fetching assignments with params:', {
            context_type_filter: 'Report',
            status_filter: 'Assigned'
          });
          
          const assignmentsResp = await apiClient.get('/universal-assignments/assignments', {
            params: {
              context_type_filter: 'Report',
              status_filter: 'Assigned'
            }
          });
          
          console.log('Assignments response:', assignmentsResp.data);
          const assignments = Array.isArray(assignmentsResp.data) ? assignmentsResp.data : (assignmentsResp.data.assignments || []);
          console.log('Total assignments found:', assignments.length);
          console.log('Looking for cycle:', cycleIdNum, 'report:', reportIdNum);
          
          const relevantAssignment = assignments.find((a: any) => {
            console.log('Checking assignment:', a.assignment_id, 'context:', a.context_data);
            return a.context_data?.cycle_id === cycleIdNum && 
                   a.context_data?.report_id === reportIdNum;
          });
          
          if (relevantAssignment) {
            console.log('Found sample selection assignment:', relevantAssignment.assignment_id);
            setCurrentSubmission({
              assignment_id: relevantAssignment.assignment_id,
              title: relevantAssignment.title,
              description: relevantAssignment.description,
              task_instructions: relevantAssignment.task_instructions,
              created_at: relevantAssignment.created_at,
              status: 'pending'
            });
            
            // Load sample IDs from assignment context
            const sampleIds = relevantAssignment.context_data?.sample_ids || [];
            if (sampleIds.length > 0) {
              // Load the specific samples for review with version filtering
              let apiUrl = `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples`;
              
              // Add version parameter if available
              if (selectedVersionId && versions.length > 0) {
                const selectedVersion = versions.find(v => v.version_id === selectedVersionId);
                if (selectedVersion) {
                  apiUrl += `?version=${selectedVersion.version_number}`;
                  console.log(`Report Owner loading samples for version ${selectedVersion.version_number}`);
                }
              }
              
              const response = await apiClient.get(apiUrl);
              const allSamples = response.data.samples || [];
              const assignedSamples = allSamples.filter((s: Sample) => sampleIds.includes(s.sample_id));
              setSamples(assignedSamples);
              
              // Initialize LOB assignments
              const lobAssignments: { [sampleId: string]: string } = {};
              assignedSamples.forEach((sample: Sample) => {
                if (sample.lob_assignment) {
                  lobAssignments[sample.sample_id] = sample.lob_assignment;
                }
              });
              setSampleLOBs(lobAssignments);
              
              console.log('Report Owner viewing assignment samples:', assignedSamples.length);
            } else {
              console.log('No sample IDs in assignment context, loading all approved samples');
              // If no specific samples assigned, load all approved samples with version filtering
              let apiUrl = `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples`;
              
              // Add version parameter if available
              if (selectedVersionId && versions.length > 0) {
                const selectedVersion = versions.find(v => v.version_id === selectedVersionId);
                if (selectedVersion) {
                  apiUrl += `?version=${selectedVersion.version_number}`;
                  console.log(`Report Owner fallback loading samples for version ${selectedVersion.version_number}`);
                }
              }
              
              const response = await apiClient.get(apiUrl);
              const allSamples = response.data.samples || [];
              const approvedSamples = allSamples.filter((s: Sample) => s.tester_decision === 'approved');
              setSamples(approvedSamples);
              
              // Initialize LOB assignments
              const lobAssignments: { [sampleId: string]: string } = {};
              approvedSamples.forEach((sample: Sample) => {
                if (sample.lob_assignment) {
                  lobAssignments[sample.sample_id] = sample.lob_assignment;
                }
              });
              setSampleLOBs(lobAssignments);
            }
          } else {
            console.log('No sample selection assignment found for Report Owner, loading all approved samples');
            // Load all approved samples for review with version filtering
            let apiUrl = `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples`;
            
            // Add version parameter if available
            if (selectedVersionId && versions.length > 0) {
              const selectedVersion = versions.find(v => v.version_id === selectedVersionId);
              if (selectedVersion) {
                apiUrl += `?version=${selectedVersion.version_number}`;
                console.log(`Report Owner no-assignment loading samples for version ${selectedVersion.version_number}`);
              }
            }
            
            const response = await apiClient.get(apiUrl);
            const allSamples = response.data.samples || [];
            const approvedSamples = allSamples.filter((s: Sample) => s.tester_decision === 'approved');
            setSamples(approvedSamples);
            
            // Check for Report Owner decisions in the samples
            const samplesWithActualRODecision = allSamples.filter((s: Sample) => 
              s.report_owner_decision && s.report_owner_decision !== 'pending'
            );
            const hasReportOwnerDecisions = samplesWithActualRODecision.length > 0;
            setHasReportOwnerFeedback(hasReportOwnerDecisions);
            console.log(`Report Owner no-assignment path: Setting hasReportOwnerFeedback to: ${hasReportOwnerDecisions}`);
            
            // Initialize LOB assignments
            const lobAssignments: { [sampleId: string]: string } = {};
            approvedSamples.forEach((sample: Sample) => {
              if (sample.lob_assignment) {
                lobAssignments[sample.sample_id] = sample.lob_assignment;
              }
            });
            setSampleLOBs(lobAssignments);
          }
        } catch (assignmentError) {
          console.warn('Error loading universal assignments, falling back to regular samples:', assignmentError);
          // Fallback to regular sample loading with version filtering
          let apiUrl = `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples`;
          
          // Add version parameter if available
          if (selectedVersionId && versions.length > 0) {
            const selectedVersion = versions.find(v => v.version_id === selectedVersionId);
            if (selectedVersion) {
              apiUrl += `?version=${selectedVersion.version_number}`;
              console.log(`Report Owner error fallback loading samples for version ${selectedVersion.version_number}`);
            }
          }
          
          const response = await apiClient.get(apiUrl);
          const allSamples = response.data.samples || [];
          const approvedSamples = allSamples.filter((s: Sample) => s.tester_decision === 'approved');
          setSamples(approvedSamples);
          
          // Check for Report Owner decisions in the samples
          const samplesWithActualRODecision = allSamples.filter((s: Sample) => 
            s.report_owner_decision && s.report_owner_decision !== 'pending'
          );
          const hasReportOwnerDecisions = samplesWithActualRODecision.length > 0;
          setHasReportOwnerFeedback(hasReportOwnerDecisions);
          console.log(`Report Owner fallback path: Setting hasReportOwnerFeedback to: ${hasReportOwnerDecisions}`);
          
          const lobAssignments: { [sampleId: string]: string } = {};
          approvedSamples.forEach((sample: Sample) => {
            if (sample.lob_assignment) {
              lobAssignments[sample.sample_id] = sample.lob_assignment;
            }
          });
          setSampleLOBs(lobAssignments);
        }
        return;
      } else {
        // Normal loading for Testers and other roles
        // Build API URL with version filter if available
        let apiUrl = `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples?include_feedback=true`;
        
        console.log('loadSamples called with:', { 
          selectedVersionId, 
          versionsLength: versions.length,
          versions: versions.map(v => ({ id: v.version_id, number: v.version_number }))
        });
        
        // Add version parameter if a specific version is selected
        if (selectedVersionId && versions.length > 0) {
          const selectedVersion = versions.find(v => v.version_id === selectedVersionId);
          if (selectedVersion) {
            apiUrl += `&version=${selectedVersion.version_number}`;
            console.log(`API URL with version filter: ${apiUrl}`);
          } else {
            console.log('Selected version not found in versions array');
          }
        } else {
          console.log('No version selected or no versions available - loading all samples');
        }
        
        const response = await apiClient.get(apiUrl);
        console.log('API Response received:', {
          url: apiUrl,
          sampleCount: response.data.samples?.length || 0,
          samples: response.data.samples?.map((s: any) => ({
            id: s.sample_id,
            version: s.version_number
          })) || []
        });
        
        const loadedSamples = response.data.samples || [];
        console.log('Setting samples:', loadedSamples);
        // Debug: Check report_owner_decision in samples
        if (loadedSamples.length > 0) {
          console.log('First sample report_owner_decision:', loadedSamples[0].report_owner_decision);
          const samplesWithRODecision = loadedSamples.filter((s: Sample) => s.report_owner_decision);
          console.log(`Samples with report_owner_decision: ${samplesWithRODecision.length} out of ${loadedSamples.length}`);
          
          // Set Report Owner feedback tab visibility based on actual sample data
          // Only show tab if there are non-pending RO decisions
          const samplesWithActualRODecision = loadedSamples.filter((s: Sample) => 
            s.report_owner_decision && s.report_owner_decision !== 'pending'
          );
          const hasReportOwnerDecisions = samplesWithActualRODecision.length > 0;
          setHasReportOwnerFeedback(hasReportOwnerDecisions);
          console.log(`Setting hasReportOwnerFeedback to: ${hasReportOwnerDecisions} (${samplesWithActualRODecision.length} actual decisions)`);
        }
        setSamples(loadedSamples);
        
        // Extract primary key columns from first sample
        if (loadedSamples.length > 0 && loadedSamples[0].sample_data) {
          const sampleData = loadedSamples[0].sample_data;
          // Common PK field names - could be made configurable
          const potentialPKFields = ['Customer ID', 'Reference Number', 'Bank ID', 'Period ID', 
                                    'customer_id', 'reference_number', 'bank_id', 'period_id'];
          const pkCols = Object.keys(sampleData).filter(key => 
            potentialPKFields.some(pk => pk.toLowerCase() === key.toLowerCase())
          );
          setPrimaryKeyColumns(pkCols);
        }
        
        // Initialize LOB assignments from loaded samples
        const lobAssignments: { [sampleId: string]: string } = {};
        loadedSamples.forEach((sample: Sample) => {
          if (sample.lob_assignment) {
            lobAssignments[sample.sample_id] = sample.lob_assignment;
          }
        });
        setSampleLOBs(lobAssignments);
      }
    } catch (error) {
      console.error('Error loading samples:', error);
      showToast.error('Failed to load samples');
    } finally {
      setLoading(false);
    }
  }, [cycleIdNum, reportIdNum, user?.role, showToast, selectedVersionId, versions]);  // Added version deps to reload samples when version changes

  // Load phase status
  const loadPhaseStatus = useCallback(async () => {
    setPhaseLoading(true);
    try {
      const response = await apiClient.get(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/analytics`);
      const analytics = response.data;
      
      setPhaseStatus({
        phase_status: analytics.phase_status || 'In Progress',
        total_samples: analytics.total_samples || 0,
        included_samples: analytics.included_samples || 0,
        excluded_samples: analytics.excluded_samples || 0,
        pending_samples: analytics.pending_samples || 0,
        submitted_samples: analytics.submitted_samples || 0,
        approved_samples: analytics.approved_samples || 0,
        revision_required_samples: analytics.revision_required_samples || 0,
        can_proceed_to_testing: analytics.can_complete_phase || false,
        current_version: analytics.latest_submission?.version || 1,
        has_submissions: analytics.total_submissions > 0,
        // New metrics fields for layout
        total_attributes: analytics.total_attributes || 0,
        scoped_attributes: analytics.scoped_attributes || 0,
        pk_attributes: analytics.pk_attributes || 0,
        total_lobs: analytics.total_lobs || 0,
        total_data_providers: analytics.total_data_providers || 0,
        started_at: analytics.started_at
      });
    } catch (error) {
      console.error('Error loading phase status:', error);
    } finally {
      setPhaseLoading(false);
    }
  }, [cycleIdNum, reportIdNum]);

  // Load report owner feedback
  const loadFeedback = useCallback(async () => {
    try {
      const response = await apiClient.get(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/feedback`);
      if (response.data) {
        const feedbackData: any = {
          unresolved_count: response.data.unresolved_count || 0,
          samples_with_feedback: response.data.feedback_items || []
        };
        
        // Get overall decision from latest submission
        if (response.data.active_feedback) {
          feedbackData.overall_decision = response.data.active_feedback.status;
          feedbackData.overall_feedback = response.data.active_feedback.feedback_text;
        }
        
        // If we have feedback items, check for overall decision
        if (response.data.feedback_items && response.data.feedback_items.length > 0) {
          const decisions = response.data.feedback_items.map((item: any) => item.decision).filter(Boolean);
          if (decisions.length > 0 && decisions.every((d: string) => d === 'approved')) {
            feedbackData.overall_decision = 'approved';
          } else if (decisions.some((d: string) => d === 'rejected')) {
            feedbackData.overall_decision = 'rejected';
          } else if (decisions.some((d: string) => d === 'revision_required')) {
            feedbackData.overall_decision = 'revision_required';
          }
        }
        
        setReportOwnerFeedback(feedbackData);
        
        // NOTE: Do not set hasReportOwnerFeedback here - it should only be based on sample data
        // Tab visibility is controlled by checking samples for report_owner_decision fields
      }
    } catch (error) {
      // Ignore errors - no feedback yet
      console.log('No scoping feedback found');
      // NOTE: Do not reset hasReportOwnerFeedback here - it's controlled by sample data
    }
  }, [cycleIdNum, reportIdNum]);

  // Initial data loading
  useEffect(() => {
    const loadData = async () => {
      if (cycleIdNum && reportIdNum) {
        // Load phase status first
        await loadPhaseStatus();
        
        // Now load other data including samples
        // Load versions first, then everything else
        await loadVersions();
        
        // Use Promise.allSettled to prevent one failure from stopping all loads
        await Promise.allSettled([
          loadReportInfo(),
          loadSamples(), // Now runs after versions are loaded
          loadScopedAttributes(),
          loadFeedback(),
          loadAvailableLOBs(),
          loadDataSources()
        ]);
      }
    };
    
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cycleIdNum, reportIdNum]);

  // Debug samples state
  useEffect(() => {
    console.log('Samples state updated:', samples);
    console.log('Loading state:', loading);
  }, [samples, loading]);

  // Load phase status when samples change
  useEffect(() => {
    if (samples.length > 0 || phaseStatus) {
      loadPhaseStatus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [samples]);

  // Reload samples when selected version changes
  useEffect(() => {
    if (selectedVersionId && versions.length > 0 && cycleIdNum && reportIdNum) {
      console.log('Selected version changed, reloading samples for version:', selectedVersionId);
      loadSamples();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedVersionId]);

  // Handle sample decision
  const handleSampleDecision = async (sampleId: string, decision: 'approved' | 'rejected') => {
    try {
      console.log('handleSampleDecision called with:', { sampleId, decision });
      console.log('Current user role:', user?.role);
      console.log('Is read only?', isReadOnly());
      
      // Update local state immediately for responsiveness
      setSamples(prev => prev.map(sample => 
        sample.sample_id === sampleId 
          ? { ...sample, tester_decision: decision }
          : sample
      ));
      
      // Persist decision to backend
      const url = `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/${sampleId}/decision`;
      console.log('Making PUT request to:', url);
      
      const response = await apiClient.put(url, {
        decision: decision,
        notes: null  // Add notes field as expected by backend
      });
      
      console.log('Decision update response:', response.data);
      showToast.success(`Sample ${decision === 'approved' ? 'approved' : 'rejected'}`);
      
      // Reload samples to ensure consistency
      await loadSamples();
    } catch (error: any) {
      console.error('Error updating sample decision:', error);
      console.error('Error details:', error.response?.data);
      console.error('Full error response:', error.response);
      showToast.error(error.response?.data?.detail || 'Failed to update sample decision');
      // Revert local state on error
      await loadSamples();
    }
  };

  // Handle sample deletion
  const handleDeleteSample = async (sampleId: string) => {
    try {
      // Confirm deletion
      if (!window.confirm('Are you sure you want to delete this sample? This action cannot be undone.')) {
        return;
      }

      // Call delete API
      await apiClient.delete(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/${sampleId}`);
      
      showToast.success('Sample deleted successfully');
      
      // Reload samples to reflect the deletion
      await loadSamples();
      await loadPhaseStatus();
      
    } catch (error: any) {
      console.error('Error deleting sample:', error);
      showToast.error(error.response?.data?.detail || 'Failed to delete sample');
    }
  };

  // Handle bulk decision
  const handleBulkDecision = async (decision: 'approved' | 'rejected') => {
    try {
      if (user?.role === 'Report Owner') {
        // For Report Owner, update report_owner_decision
        setSamples(prev => prev.map(sample => 
          bulkSelectedSamples.includes(sample.sample_id)
            ? { ...sample, report_owner_decision: decision }
            : sample
        ));
        
        // TODO: Call Report Owner specific endpoint when available
        // For now, we'll need to create a Report Owner review endpoint
        showToast.info('Report Owner decisions are recorded. Submit your review to finalize.');
        
        // Store decisions locally for now
        bulkSelectedSamples.forEach(sampleId => {
          setIndividualDecisions(prev => ({
            ...prev,
            [sampleId]: decision
          }));
        });
      } else {
        // For Tester, update tester_decision
        setSamples(prev => prev.map(sample => 
          bulkSelectedSamples.includes(sample.sample_id)
            ? { ...sample, tester_decision: decision }
            : sample
        ));
        
        // Use the unified bulk operation endpoint
        await apiClient.post(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/bulk-operation`, {
          sample_ids: bulkSelectedSamples,
          action: decision === 'approved' ? 'approve' : 'reject',
          notes: `Bulk ${decision} samples`
        });
        
        showToast.success(`${bulkSelectedSamples.length} samples ${decision === 'approved' ? 'approved' : 'rejected'}`);
      }
      
      setBulkSelectedSamples([]);
    } catch (error: any) {
      console.error('Error updating bulk decisions:', error);
      console.error('Error details:', error.response?.data);
      showToast.error(error.response?.data?.detail || 'Failed to update bulk decisions');
      // Revert on error
      await loadSamples();
    }
  };

  // Handle LOB assignment
  const handleLOBAssignment = async (sampleId: string, lob: string) => {
    try {
      // Update local state
      setSampleLOBs(prev => ({ ...prev, [sampleId]: lob }));
      setSamples(prev => prev.map(sample => 
        sample.sample_id === sampleId 
          ? { ...sample, lob_assignment: lob }
          : sample
      ));
      
      // Persist to backend
      await apiClient.put(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/${sampleId}/lob`, {
        lob_assignment: lob
      });
      
      showToast.success('LOB assignment updated');
    } catch (error: any) {
      console.error('Error updating LOB assignment:', error);
      showToast.error(error.response?.data?.detail || 'Failed to update LOB assignment');
      // Revert on error
      await loadSamples();
    }
  };

  // Start phase
  const handleStartPhase = async () => {
    try {
      const response = await apiClient.post(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/start`, {
        planned_start_date: new Date().toISOString(),
        planned_end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        notes: 'Sample Selection phase started'
      });
      
      showToast.success('Sample Selection phase started successfully');
      await loadPhaseStatus();
      refetchStatus(); // Update unified status
    } catch (error: any) {
      console.error('Error starting phase:', error);
      showToast.error(error.response?.data?.detail || 'Failed to start phase');
    }
  };

  // Generate samples
  const handleGenerateSamples = async () => {
    setBasicGenerating(true);
    try {
      console.log('Generating samples with size:', sampleSize);
      console.log('Scoped attributes:', scopedAttributes);
      const requestData = {
        sample_size: sampleSize,
        strategy: 'intelligent',  // Changed from 'basic' to 'intelligent'
        sample_type: 'Population Sample',
        regulatory_context: reportInfo?.regulatory_framework || 'General Regulatory Compliance',
        scoped_attributes: scopedAttributes.map(attr => ({
          attribute_name: attr.attribute_name,
          is_primary_key: attr.is_primary_key || false,
          data_type: attr.data_type || 'VARCHAR',
          is_mandatory: attr.is_required || false  // Map is_required to is_mandatory
        })),
        // Add distribution for intelligent sampling
        distribution: {
          clean: 0.3,    // 30% clean samples
          anomaly: 0.5,  // 50% anomaly samples
          boundary: 0.2  // 20% boundary samples
        },
        use_data_source: true,  // Use actual data source for realistic samples
        include_file_samples: false
      };
      console.log('Request data being sent:', requestData);
      console.log('Scoped attributes detail:', requestData.scoped_attributes);
      console.log('API URL:', `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/generate-unified`);
      
      console.log('Making API request...');
      const response = await apiClient.post(
        `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/generate-unified`, 
        requestData,
        { timeout: 30000 } // 30 second timeout
      );
      
      console.log('Generate response:', response.data);
      showToast.success(`Generated ${response.data.samples_generated} new samples`);
      setShowGenerateDialog(false);
      setSampleSize(100); // Reset to default
      
      // Show new version created alert
      setIsCreatingNewVersion(true);
      setTimeout(() => setIsCreatingNewVersion(false), 5000);
      
      await loadSamples();
      await loadPhaseStatus(); // Also refresh the status
      await loadVersions(); // Reload versions to show the new one
    } catch (error: any) {
      console.error('Error generating samples:', error);
      console.error('Error response:', error.response);
      showToast.error(error.response?.data?.detail || 'Failed to generate samples');
      setShowGenerateDialog(false); // Close dialog on error
    } finally {
      setBasicGenerating(false);
    }
  };

  // Enhanced generate samples using intelligent sampling
  const handleEnhancedGenerateSamples = async () => {
    setEnhancedGenerating(true);
    try {
      console.log('Enhanced generating samples with params:', {
        sample_size: enhancedSampleSize,
        sampling_strategy: enhancedSamplingStrategy,
        data_source_id: enhancedDataSource,
        use_anomaly_insights: useAnomalyInsights
      });

      const response = await apiClient.post(
        `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/generate-intelligent`,
        {
          target_sample_size: enhancedSampleSize,
          use_data_source: true,
          data_source_id: enhancedDataSource ? parseInt(enhancedDataSource) : undefined,
          distribution: {
            clean: 0.3,
            anomaly: 0.5,
            boundary: 0.2
          },
          include_file_samples: false,
          sampling_strategy: enhancedSamplingStrategy,
          use_anomaly_insights: useAnomalyInsights
        }
      );
      
      console.log('Enhanced generate response:', response.data);
      
      if (response.data.samples && response.data.samples.length > 0) {
        showToast.success(
          `Generated ${response.data.samples.length} samples from ${response.data.data_source_type} source using ${response.data.method} method`
        );
        setShowEnhancedGenerateDialog(false);
        
        // Show new version created alert
        setIsCreatingNewVersion(true);
        setTimeout(() => setIsCreatingNewVersion(false), 5000);
        
        await loadSamples();
        await loadPhaseStatus();
        await loadVersions(); // Reload versions to show the new one
      } else {
        showToast.warning('No samples generated. Check data source configuration.');
      }
    } catch (error: any) {
      console.error('Error generating enhanced samples:', error);
      showToast.error(
        error.response?.data?.detail || 
        'Failed to generate enhanced samples. Check data source connectivity.'
      );
    } finally {
      setEnhancedGenerating(false);
    }
  };

  const handleActivityAction = async (activity: any, action: string) => {
    try {
      // Special handling for generate_samples activity - open the dialog instead
      if (activity.activity_id === 'generate_samples' && action === 'complete') {
        console.log('Opening Generate Samples dialog from activity card');
        setShowGenerateDialog(true);
        return;
      }
      
      // Make the API call to start/complete the activity
      const endpoint = action === 'start' ? 'start' : 'complete';
      const response = await apiClient.post(`/activity-management/activities/${activity.activity_id}/${endpoint}`, {
        cycle_id: cycleIdNum,
        report_id: reportIdNum,
        phase_name: 'Sample Selection'
      });
      
      // Show success message from backend or default
      const message = response.data.message || activity.metadata?.success_message || `${action === 'start' ? 'Started' : 'Completed'} ${activity.name}`;
      showToast.success(message);
      
      // Special handling for phase_start activities - immediately complete them
      if (action === 'start' && activity.metadata?.activity_type === 'phase_start') {
        console.log('Auto-completing phase_start activity:', activity.name);
        await new Promise(resolve => setTimeout(resolve, 200));
        
        try {
          await apiClient.post(`/activity-management/activities/${activity.activity_id}/complete`, {
            cycle_id: cycleIdNum,
            report_id: reportIdNum,
            phase_name: 'Sample Selection'
          });
          showToast.success(`${activity.name} completed`);
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
      await refetchStatus();
      await loadPhaseStatus();
      await loadSamples();
    } catch (error: any) {
      console.error('Error handling activity action:', error);
      showToast.error(error.response?.data?.detail || `Failed to ${action} activity`);
    }
  };

  // Get workflow steps

  const getDecisionColor = (decision: string | null | undefined) => {
    switch (decision) {
      case 'include':
      case 'approved':
        return 'success';
      case 'exclude':
      case 'rejected':
        return 'error';
      case 'revision_required':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Unified status display following data profiling pattern
  const getStatusChip = (sample: Sample) => {
    // Determine overall status based on both decisions
    let status, color, label;
    
    if (sample.tester_decision === 'approved' && sample.report_owner_decision === 'approved') {
      status = 'approved';
      color = 'success' as const;
      label = 'Approved';
    } else if (sample.tester_decision === 'rejected' || sample.report_owner_decision === 'rejected') {
      status = 'rejected';
      color = 'error' as const;
      label = 'Rejected';
    } else if (sample.report_owner_decision === 'revision_required') {
      status = 'revision_required';
      color = 'warning' as const;
      label = 'Needs Revision';
    } else if (sample.tester_decision === 'approved' && !sample.report_owner_decision) {
      status = 'submitted';
      color = 'info' as const;
      label = 'Submitted';
    } else if (!sample.tester_decision || sample.tester_decision === 'pending') {
      status = 'pending';
      color = 'warning' as const;
      label = 'Pending';
    } else {
      status = 'pending';
      color = 'default' as const;
      label = 'Pending';
    }
    
    return <Chip size="small" color={color} label={label} />;
  };

  const getTesterDecisionDisplay = (sample: Sample) => {
    if (!sample.tester_decision) {
      return <Typography variant="caption" color="textSecondary">-</Typography>;
    }

    const decisionConfig = {
      'approved': { color: 'success' as const, label: 'Approved' },
      'rejected': { color: 'error' as const, label: 'Rejected' },
      'pending': { color: 'warning' as const, label: 'Pending' }
    };

    const config = decisionConfig[sample.tester_decision as keyof typeof decisionConfig] || 
                   { color: 'default' as const, label: sample.tester_decision };

    return (
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Chip size="small" color={config.color} label={config.label} sx={{ fontSize: '0.7rem' }} />
        {sample.tester_decision_notes && (
          <Tooltip title={`Notes: ${sample.tester_decision_notes}`}>
            <InfoIcon sx={{ fontSize: 12, ml: 0.5, color: 'text.secondary' }} />
          </Tooltip>
        )}
      </Box>
    );
  };

  const getReportOwnerDecisionDisplay = (sample: Sample) => {
    // Check both the sample's report_owner_decision and the temporary individualDecisions state
    const decision = individualDecisions[sample.sample_id] || sample.report_owner_decision;
    
    if (!decision) {
      return <Typography variant="caption" color="textSecondary">-</Typography>;
    }

    const decisionConfig = {
      'approved': { color: 'success' as const, label: 'RO Approved' },
      'rejected': { color: 'error' as const, label: 'RO Rejected' },
      'revision_required': { color: 'warning' as const, label: 'RO Revision' }
    };

    const config = decisionConfig[decision as keyof typeof decisionConfig] || 
                   { color: 'default' as const, label: decision };

    return (
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Chip size="small" color={config.color} label={config.label} sx={{ fontSize: '0.7rem' }} />
        {sample.report_owner_feedback && (
          <Tooltip title={`Feedback: ${sample.report_owner_feedback}`}>
            <InfoIcon sx={{ fontSize: 12, ml: 0.5, color: 'text.secondary' }} />
          </Tooltip>
        )}
      </Box>
    );
  };

  const isReadOnly = () => {
    // Report Owners are always read-only
    if (user?.role === 'Report Owner') return true;
    
    // Find the currently selected version
    const currentVersion = versions.find(v => v.version_id === selectedVersionId);
    console.log('isReadOnly check - currentVersion:', currentVersion);
    console.log('isReadOnly check - selectedVersionId:', selectedVersionId);
    console.log('isReadOnly check - versions:', versions);
    
    // If version is not draft, it's read-only
    return currentVersion && currentVersion.version_status !== 'draft';
  };

  return (
    <Container maxWidth={false} sx={{ py: 3, px: { xs: 2, md: 3 } }}>
      {/* Removed ReportOwnerFeedbackChecker - not relevant for sample selection feedback */}
      
      {/* Universal Assignments Alerts */}
      {assignments.map((assignment) => (
        <UniversalAssignmentAlert
          key={assignment.assignment_id}
          assignment={assignment}
          onAcknowledge={acknowledgeAssignment}
          onStart={startAssignment}
          onComplete={completeAssignment}
          showActions={true}
        />
      ))}

      {/* Report Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <AssignmentIcon color="primary" />
              <Box>
                <Typography variant="h6" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportInfo?.report_name || 'Loading...'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sample Selection Phase - Generating representative sample datasets for testing
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <BusinessIcon color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">LOB:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportInfo?.lob_name || 'Unknown'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">Tester:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportInfo?.tester_name || 'Not assigned'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">Owner:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportInfo?.report_owner_name || 'Not specified'}
                </Typography>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>


      {/* Sample Selection Metrics Row 1 - Six Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="primary.main" fontWeight="bold">
                {phaseStatus?.total_attributes || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Attributes
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="success.main" fontWeight="bold">
                {(phaseStatus?.scoped_attributes || 0) + (phaseStatus?.pk_attributes || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Scoped Attributes
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                ({phaseStatus?.scoped_attributes || 0} Non-PK + {phaseStatus?.pk_attributes || 0} PK)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="info.main" fontWeight="bold">
                {phaseStatus?.total_samples || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Samples
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="warning.main" fontWeight="bold">
                {phaseStatus?.total_lobs || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total LOBs
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="error.main" fontWeight="bold">
                {phaseStatus?.total_data_providers || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Data Owners
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="primary.main" fontWeight="bold">
                {(() => {
                  const startDate = phaseStatus?.started_at;
                  const completedDate = phaseStatus?.completed_at;
                  if (!startDate) return 0;
                  const end = completedDate ? new Date(completedDate) : new Date();
                  const start = new Date(startDate);
                  return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
                })()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {phaseStatus?.completed_at ? 'Completion Time (days)' : 'Days Elapsed'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Row 2: On-Time Status + Phase Controls */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 6 }}>
          <Card sx={{ height: 100 }}>
            <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <Typography 
                variant="h3" 
                color={
                  phaseStatus?.phase_status === 'Complete' ? 
                    'success.main' :
                  phaseStatus?.phase_status === 'In Progress' ?
                    'primary.main' : 'warning.main'
                } 
                component="div"
                sx={{ fontSize: '1.5rem' }}
              >
                {phaseStatus?.phase_status === 'Complete' ? 
                  'Yes - Completed On-Time' :
                phaseStatus?.phase_status === 'In Progress' ?
                  'On Track' : 'Not Started'
                }
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {phaseStatus?.phase_status === 'Complete' ? 'On-Time Completion Status' : 'Current Schedule Status'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ height: 100 }}>
            <CardContent sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" sx={{ fontSize: '1rem' }}>
                  Phase Controls
                </Typography>
                
                {/* Tester Status Update Controls */}
                {phaseStatus && phaseStatus.phase_status === 'In Progress' && (
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip
                      label="At Risk"
                      size="small"
                      color="warning"
                      variant="outlined"
                      clickable
                      onClick={() => {/* Handle status update */}}
                      disabled={phaseLoading}
                      sx={{ fontSize: '0.7rem' }}
                    />
                    <Chip
                      label="Off Track"
                      size="small"
                      color="error"
                      variant="outlined"
                      clickable
                      onClick={() => {/* Handle status update */}}
                      disabled={phaseLoading}
                      sx={{ fontSize: '0.7rem' }}
                    />
                  </Box>
                )}
              </Box>
              
              {/* Completion Requirements */}
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                  {!phaseStatus ? (
                    'To complete: Start phase → Generate/Upload samples → Review samples → Submit for approval'
                  ) : phaseStatus.phase_status === 'Complete' ? (
                    'Phase completed successfully - all requirements met'
                  ) : phaseStatus.can_proceed_to_testing ? (
                    'Ready to complete - all requirements met'
                  ) : (
                    `To complete: ${phaseStatus.approved_samples > 0 ? 'All samples approved' : 'Generate samples and get approval'}`
                  )}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Phase Workflow Visual */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TableViewIcon color="primary" />
            Sample Selection Phase Workflow
          </Typography>
          
          {phaseLoading ? (
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <CircularProgress />
            </Box>
          ) : (
            <Box sx={{ mt: 2 }}>
              {unifiedPhaseStatus?.activities ? (
                <DynamicActivityCards
                  activities={unifiedPhaseStatus.activities}
                  cycleId={cycleIdNum}
                  reportId={reportIdNum}
                  phaseName="Sample Selection"
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
                    Loading sample selection activities...
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Report Owner Feedback Alert */}
      {user?.role === 'Tester' && reportOwnerFeedback?.needs_revision && (
        <Alert 
          severity="warning" 
          sx={{ mb: 3, border: '2px solid', borderColor: 'warning.main' }}
          icon={<WarningIcon />}
        >
          <Typography variant="h6" sx={{ fontSize: '1.2rem', fontWeight: 'bold', mb: 1 }}>
            Report Owner Feedback Requires Action
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            The Report Owner has reviewed your sample submission and requested changes.
          </Typography>
          {reportOwnerFeedback.feedback && (
            <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
              Feedback: "{reportOwnerFeedback.feedback}"
            </Typography>
          )}
        </Alert>
      )}


      {/* Submission History */}
      {phaseStatus && phaseStatus.has_submissions && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Submission History
              </Typography>
              <Chip 
                label={`Version ${phaseStatus.current_version}`}
                color="primary"
                size="small"
              />
            </Box>
            
            <Alert severity="info" sx={{ mt: 1 }}>
              <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 'bold', mb: 1 }}>
                Current Status: {phaseStatus.phase_status}
              </Typography>
              <Typography variant="body2">
                Total Submissions: {phaseStatus.has_submissions ? phaseStatus.current_version : 0}
              </Typography>
              {phaseStatus.phase_status === 'Pending Approval' && user?.role === 'Tester' && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Your submission is awaiting Report Owner review. You cannot submit new samples until the current submission is reviewed.
                </Typography>
              )}
            </Alert>
          </CardContent>
        </Card>
      )}

      {/* Report Owner Feedback is now shown in the dedicated tab - removed redundant display here */}

      {/* Report Owner Submission Review Header */}
      {user?.role === 'Report Owner' && phaseStatus?.phase_status === 'Pending Approval' && currentSubmission && (
        <Card sx={{ mb: 3, bgcolor: 'warning.50', border: '2px solid', borderColor: 'warning.main' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h6" gutterBottom>
                  Review Submitted Samples
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Version {currentSubmission.version_number} submitted by {currentSubmission.submitted_by} on {new Date(currentSubmission.submitted_at).toLocaleString()}
                </Typography>
                {currentSubmission.submission_notes && (
                  <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                    Notes: {currentSubmission.submission_notes}
                  </Typography>
                )}
              </Box>
              <Box>
                <Chip
                  label={`${samples.length} Samples for Review`}
                  color="warning"
                  icon={<AssignmentIcon />}
                />
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(_, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          {(() => {
            console.log('Tab render check:', { 
              hasReportOwnerFeedback, 
              userRole: user?.role, 
              shouldShowTab: hasReportOwnerFeedback && user?.role === 'Tester' 
            });
            return hasReportOwnerFeedback && user?.role === 'Tester' && <Tab label="Report Owner Feedback" />;
          })()}
          <Tab label="Sample Generation" />
          <Tab label="Sample Review" />
          <Tab label="LOB Assignment" />
          <Tab label="Documents" />
        </Tabs>

        {/* Report Owner Feedback Tab */}
        {hasReportOwnerFeedback && user?.role === 'Tester' && activeTab === 0 && (
          <ReportOwnerFeedback
            cycleId={cycleIdNum}
            reportId={reportIdNum}
            versionId={selectedVersionId}
            currentUserRole={user?.role || ''}
            onMakeChanges={async () => {
              try {
                // Check current version status first
                const latestVersion = versions.length > 0 ? 
                  versions.reduce((latest: any, v: any) => 
                    (v.version_number > latest.version_number) ? v : latest
                  ) : null;
                
                // Only block if version is pending approval (waiting for Report Owner)
                // Allow changes if approved (Report Owner already reviewed) or rejected
                if (latestVersion && latestVersion.version_status === 'pending_approval') {
                  showToast.error('Cannot make changes while version is pending Report Owner approval');
                  return;
                }
                
                // Create a new version from existing samples preserving report owner decisions
                try {
                  const response = await apiClient.post(
                    `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/resubmit-after-feedback`
                  );
                  
                  showToast.success('Created new version preserving report owner decisions');
                } catch (error: any) {
                  // If we get a duplicate key error, it means a draft version already exists
                  if (error.response?.data?.detail?.includes('duplicate key value')) {
                    showToast.info('Using existing draft version');
                  } else {
                    throw error;
                  }
                }
                
                // Reload versions first to ensure we have the new version
                await loadVersions();
                
                // Only switch to new version if user is a Tester
                // Report Owner should stay on the version they provided feedback on
                if (user?.role === 'Tester') {
                  const versionsResponse = await apiClient.get(`/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/versions`);
                  const allVersions = versionsResponse.data || [];
                  if (allVersions.length > 0) {
                    const latestVersion = allVersions.reduce((latest: any, v: any) => 
                      (v.version_number > latest.version_number) ? v : latest
                    );
                    console.log(`Tester selecting newly created version ${latestVersion.version_number}`);
                    
                    // Update state and force immediate reload
                    setSelectedVersionId(latestVersion.version_id);
                    
                    // Manually trigger samples load with the new version
                    // Since state updates are async, we need to manually pass the version
                    const samplesUrl = `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples?version=${latestVersion.version_number}`;
                    const samplesResponse = await apiClient.get(samplesUrl);
                    setSamples(samplesResponse.data.samples || []);
                    console.log(`Loaded ${samplesResponse.data.samples?.length || 0} samples for version ${latestVersion.version_number}`);
                  }
                } else {
                  console.log(`Report Owner staying on current version (has their feedback)`);
                  // For Report Owner, just reload with current version
                  await loadSamples();
                }
                
                // Reload phase status
                await loadPhaseStatus();
                
                // Switch to Sample Review tab to see the new version
                // For Tester with RO feedback visible: 0=RO Feedback, 1=Sample Gen, 2=Sample Review
                // For others: 0=Sample Gen, 1=Sample Review
                const sampleReviewTabIndex = hasReportOwnerFeedback && user?.role === 'Tester' ? 2 : 1;
                setActiveTab(sampleReviewTabIndex);
                
                setIsCreatingNewVersion(true);
                setTimeout(() => setIsCreatingNewVersion(false), 5000);
              } catch (error: any) {
                console.error('Error creating new version:', error);
                showToast.error(error.response?.data?.detail || 'Failed to create new version');
              }
            }}
          />
        )}

        {/* Sample Generation Tab */}
        {((hasReportOwnerFeedback && user?.role === 'Tester' && activeTab === 1) || 
          ((!hasReportOwnerFeedback || user?.role !== 'Tester') && activeTab === 0)) && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                Sample Generation and Upload
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={<PsychologyIcon />}
                  onClick={() => {
                    console.log('Generate Samples clicked');
                    console.log('isReadOnly:', isReadOnly());
                    console.log('phaseStatus:', phaseStatus);
                    console.log('scopedAttributes:', scopedAttributes);
                    console.log('Button disabled?', isReadOnly() || phaseStatus?.phase_status === 'Not Started');
                    // Don't reset sample size - let user keep their preference
                    setShowGenerateDialog(true);
                  }}
                  disabled={isReadOnly() || phaseStatus?.phase_status === 'Not Started'}
                >
                  Generate Samples
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<ScienceIcon />}
                  onClick={() => {
                    // Don't reset sample size - let user keep their preference
                    setShowEnhancedGenerateDialog(true);
                  }}
                  disabled={isReadOnly() || phaseStatus?.phase_status === 'Not Started'}
                >
                  Enhanced Generate
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<CloudUploadIcon />}
                  onClick={() => setShowUploadDialog(true)}
                  disabled={isReadOnly() || phaseStatus?.phase_status === 'Not Started'}
                >
                  Upload CSV
                </Button>
              </Box>
            </Box>
            
            {/* Sample Statistics */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card sx={{ bgcolor: 'primary.50' }}>
                  <CardContent>
                    <Typography variant="h4" color="primary.main">
                      {filteredSamples.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Samples (Current Version)
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card sx={{ bgcolor: 'success.50' }}>
                  <CardContent>
                    <Typography variant="h4" color="success.main">
                      {phaseStatus?.included_samples || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Approved for Testing
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card sx={{ bgcolor: 'warning.50' }}>
                  <CardContent>
                    <Typography variant="h4" color="warning.main">
                      {phaseStatus?.pending_samples || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Pending Review
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Card sx={{ bgcolor: 'error.50' }}>
                  <CardContent>
                    <Typography variant="h4" color="error.main">
                      {phaseStatus?.excluded_samples || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Rejected Samples
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Generation History */}
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                Generate synthetic samples based on scoped attributes or upload existing samples from your test data.
                All samples must be reviewed and approved before proceeding to test execution.
              </Typography>
            </Alert>
          </Box>
        )}

        {/* Sample Review Tab */}
        {((hasReportOwnerFeedback && user?.role === 'Tester' && activeTab === 2) || 
          ((!hasReportOwnerFeedback || user?.role !== 'Tester') && activeTab === 1)) && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="h6">
                  Sample Review ({filteredSamples.length} samples)
                </Typography>
                
                {/* Version Selector */}
                {versions.length > 0 && (
                  <>
                    <FormControl size="small" sx={{ minWidth: 200 }}>
                      <InputLabel>Version</InputLabel>
                      <Select
                        value={selectedVersionId}
                        onChange={(e) => setSelectedVersionId(e.target.value)}
                        label="Version"
                        size="small"
                        disabled={!versionsLoaded || versions.length === 0}
                      >
                        {!versionsLoaded ? (
                          <MenuItem value="" disabled>
                            Loading versions...
                          </MenuItem>
                        ) : versions.length === 0 ? (
                          <MenuItem value="" disabled>
                            No versions available
                          </MenuItem>
                        ) : (
                          versions.map((version: any) => (
                            <MenuItem key={version.version_id} value={version.version_id}>
                              Version {version.version_number}
                              {version.is_current && ' (Current)'}
                              {version.version_status === 'draft' && ' - Draft'}
                              {version.version_status === 'pending_approval' && ' - Pending'}
                              {version.version_status === 'approved' && ' - Approved'}
                              {version.version_status === 'rejected' && ' - Rejected'}
                            </MenuItem>
                          ))
                        )}
                      </Select>
                    </FormControl>
                    
                    {/* Version History Button */}
                    <Tooltip title="View version history">
                      <IconButton 
                        onClick={() => setShowVersionHistoryDialog(true)} 
                        size="small"
                        disabled={versions.length === 0}
                      >
                        <HistoryIcon />
                      </IconButton>
                    </Tooltip>
                  </>
                )}
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {(() => {
                  console.log('Debug - User role:', user?.role);
                  console.log('Debug - Phase status:', phaseStatus?.phase_status);
                  console.log('Debug - Current submission:', currentSubmission);
                  return null;
                })()}
                {user?.role === 'Report Owner' && phaseStatus?.phase_status === 'Pending Approval' && currentSubmission ? (
                  <>
                    <Button
                      variant="contained"
                      color="success"
                      startIcon={<ThumbUpIcon />}
                      onClick={() => {
                        setReviewDecision('approved');
                        setShowReviewDialog(true);
                      }}
                    >
                      Approve Samples
                    </Button>
                    <Button
                      variant="contained"
                      color="warning"
                      startIcon={<EditIcon />}
                      onClick={() => {
                        setReviewDecision('revision_required');
                        setShowReviewDialog(true);
                      }}
                    >
                      Request Changes
                    </Button>
                    <Button
                      variant="contained"
                      color="error"
                      startIcon={<CloseIcon />}
                      onClick={() => {
                        setReviewDecision('rejected');
                        setShowReviewDialog(true);
                      }}
                    >
                      Reject Samples
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="outlined"
                      startIcon={<RefreshIcon />}
                      onClick={async () => {
                        await loadPhaseStatus();
                        await loadSamples();
                      }}
                    >
                      Refresh
                    </Button>
                  </>
                )}
              </Box>
            </Box>

          {/* Alert for new version creation */}
          {isCreatingNewVersion && user?.role === 'Tester' && (
            <Alert severity="info" sx={{ mb: 2 }} onClose={() => setIsCreatingNewVersion(false)}>
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                New Version Created
              </Typography>
              <Typography variant="body2">
                A new version has been created with all samples from the previous version. 
                Review and modify the samples to address the Report Owner's feedback, then resubmit for approval.
              </Typography>
            </Alert>
          )}

          {/* Bulk Actions Bar */}
          <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
            {user?.role === 'Report Owner' ? (
              // Report Owner bulk actions
              <>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<ThumbUpIcon />}
                  onClick={() => handleBulkDecision('approved')}
                  disabled={bulkSelectedSamples.length === 0}
                >
                  Bulk Approve ({bulkSelectedSamples.length})
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<CloseIcon />}
                  onClick={() => handleBulkDecision('rejected')}
                  disabled={bulkSelectedSamples.length === 0}
                >
                  Bulk Reject ({bulkSelectedSamples.length})
                </Button>
              </>
            ) : (
              // Tester bulk actions
              <>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<CheckIcon />}
                  onClick={() => handleBulkDecision('approved')}
                  disabled={bulkSelectedSamples.length === 0 || isReadOnly()}
                >
                  Include Selected ({bulkSelectedSamples.length})
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<CloseIcon />}
                  onClick={() => handleBulkDecision('rejected')}
                  disabled={bulkSelectedSamples.length === 0 || isReadOnly()}
                >
                  Exclude Selected ({bulkSelectedSamples.length})
                </Button>
              </>
            )}
            <Box sx={{ flexGrow: 1 }} />
            {!isReadOnly() && user?.role !== 'Report Owner' && (
              <Button
                variant="contained"
                color="primary"
                startIcon={<SendIcon />}
                onClick={() => setShowSubmitDialog(true)}
                disabled={
                  filteredSamples.filter(s => s.tester_decision === 'approved').length === 0 ||
                  phaseStatus?.phase_status === 'Pending Approval' ||
                  phaseStatus?.phase_status === 'Complete'
                }
              >
                Submit for Approval
              </Button>
            )}
          </Box>

          {filteredSamples.length > 0 && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                Tip: Scroll horizontally to view all columns →
              </Typography>
            </Alert>
          )}

          {/* Samples Table */}
          <Box 
            sx={{ 
              width: '100%', 
              overflowX: 'scroll', 
              overflowY: 'hidden',
              pb: 1,
              '&::-webkit-scrollbar': {
                height: 18,
                backgroundColor: '#f5f5f5',
              },
              '&::-webkit-scrollbar-track': {
                backgroundColor: '#f5f5f5',
                border: '1px solid #e0e0e0',
              },
              '&::-webkit-scrollbar-thumb': {
                backgroundColor: '#888',
                borderRadius: 9,
                border: '2px solid #f5f5f5',
                '&:hover': {
                  backgroundColor: '#555',
                },
              },
            }}
          >
            <TableContainer 
              component={Paper}
              sx={{ 
                width: 'max-content',
                maxHeight: '70vh',
                overflowY: 'auto',
                overflowX: 'visible'
              }}
            >
              <Table stickyHeader size="small" sx={{ minWidth: 1900 }}>
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox" sx={{ minWidth: 50 }}>
                    <Checkbox
                      checked={bulkSelectedSamples.length === filteredSamples.length && filteredSamples.length > 0}
                      indeterminate={bulkSelectedSamples.length > 0 && bulkSelectedSamples.length < filteredSamples.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setBulkSelectedSamples(filteredSamples.map(s => s.sample_id));
                        } else {
                          setBulkSelectedSamples([]);
                        }
                      }}
                      disabled={isReadOnly() && user?.role !== 'Report Owner'}
                    />
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Sample ID</TableCell>
                  {/* Dynamic PK columns */}
                  {primaryKeyColumns.map((pkCol) => (
                    <TableCell key={pkCol} sx={{ fontWeight: 'bold', minWidth: 120 }}>{pkCol}</TableCell>
                  ))}
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 200 }}>Attribute</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 80 }}>Category</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 250 }}>Rationale</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 80 }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>Tester</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 60 }}>LOB</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>Report Owner Decision</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={14 + primaryKeyColumns.length} align="center">
                      <CircularProgress />
                    </TableCell>
                  </TableRow>
                ) : filteredSamples.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={14 + primaryKeyColumns.length} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No samples generated yet. Click "Generate Samples" to begin.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredSamples.map((sample) => {
                    console.log('Rendering sample:', sample);
                    return (
                    <TableRow key={`${sample.sample_id}_v${sample.version_number || 1}`}>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={bulkSelectedSamples.includes(sample.sample_id)}
                          onChange={() => {
                            if (bulkSelectedSamples.includes(sample.sample_id)) {
                              setBulkSelectedSamples(prev => prev.filter(id => id !== sample.sample_id));
                            } else {
                              setBulkSelectedSamples(prev => [...prev, sample.sample_id]);
                            }
                          }}
                          disabled={isReadOnly() && user?.role !== 'Report Owner'}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace" sx={{ fontSize: '0.75rem' }}>
                          {sample.sample_id}
                        </Typography>
                      </TableCell>
                      {/* Dynamic PK values */}
                      {primaryKeyColumns.map((pkCol) => (
                        <TableCell key={pkCol}>
                          <Typography variant="body2" fontFamily="monospace" sx={{ fontSize: '0.75rem' }}>
                            {sample.sample_data?.[pkCol] || '-'}
                          </Typography>
                        </TableCell>
                      ))}
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
                          {sample.attribute_focus ? (
                            sample.sample_data && sample.sample_data[sample.attribute_focus] !== undefined ? 
                              `${sample.attribute_focus} (${sample.sample_data[sample.attribute_focus]})` : 
                              sample.attribute_focus
                          ) : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={sample.sample_category || 'Unknown'} 
                          size="small"
                          color={
                            sample.sample_category === 'CLEAN' ? 'success' :
                            sample.sample_category === 'ANOMALY' ? 'warning' :
                            sample.sample_category === 'BOUNDARY' ? 'info' : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            fontSize: '0.75rem',
                            maxWidth: 250,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            display: 'block'
                          }}
                          title={sample.rationale}
                        >
                          {sample.rationale || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {getStatusChip(sample)}
                      </TableCell>
                      <TableCell>
                        {getTesterDecisionDisplay(sample)}
                      </TableCell>
                      <TableCell>
                        {/* Allow Testers to assign LOBs for approved samples when version is editable */}
                        {(user?.role === 'Tester' && sample.tester_decision === 'approved' && !isReadOnly()) ? (
                          <FormControl size="small" sx={{ minWidth: 120 }}>
                            <Select
                              value={sampleLOBs[sample.sample_id] || sample.lob_assignment || ''}
                              onChange={(e) => handleLOBAssignment(sample.sample_id, e.target.value)}
                              displayEmpty
                            >
                              <MenuItem value="">
                                <em>Not Assigned</em>
                              </MenuItem>
                              {availableLOBs.map((lob) => (
                                <MenuItem key={lob} value={lob}>
                                  {lob}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        ) : (
                          sample.lob_assignment ? (
                            <Chip label={sample.lob_assignment} size="small" color="primary" />
                          ) : (
                            <Typography variant="body2" color="text.secondary">-</Typography>
                          )
                        )}
                      </TableCell>
                      <TableCell>
                        {getReportOwnerDecisionDisplay(sample)}
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1}>
                          {/* Report Owner individual sample decisions */}
                          {user?.role === 'Report Owner' && phaseStatus?.phase_status === 'Pending Approval' && currentSubmission && (
                            <>
                              <Tooltip title="Approve Sample">
                                <IconButton
                                  size="small"
                                  color={individualDecisions[sample.sample_id] === 'approved' ? 'success' : 'default'}
                                  onClick={() => {
                                    const newDecision = individualDecisions[sample.sample_id] === 'approved' ? null : 'approved';
                                    setIndividualDecisions(prev => ({
                                      ...prev,
                                      [sample.sample_id]: newDecision
                                    }));
                                    // Update sample state to show decision immediately
                                    setSamples(prev => prev.map(s => 
                                      s.sample_id === sample.sample_id 
                                        ? { ...s, report_owner_decision: newDecision }
                                        : s
                                    ));
                                  }}
                                >
                                  <ThumbUpIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Reject Sample">
                                <IconButton
                                  size="small"
                                  color={individualDecisions[sample.sample_id] === 'rejected' ? 'error' : 'default'}
                                  onClick={() => {
                                    const newDecision = individualDecisions[sample.sample_id] === 'rejected' ? null : 'rejected';
                                    setIndividualDecisions(prev => ({
                                      ...prev,
                                      [sample.sample_id]: newDecision
                                    }));
                                    // Update sample state to show decision immediately
                                    setSamples(prev => prev.map(s => 
                                      s.sample_id === sample.sample_id 
                                        ? { ...s, report_owner_decision: newDecision }
                                        : s
                                    ));
                                  }}
                                >
                                  <CloseIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Add Feedback">
                                <IconButton
                                  size="small"
                                  color={individualFeedback[sample.sample_id] ? 'primary' : 'default'}
                                  onClick={() => {
                                    const feedback = prompt('Enter feedback for this sample:', individualFeedback[sample.sample_id] || '');
                                    if (feedback !== null) {
                                      setIndividualFeedback(prev => ({
                                        ...prev,
                                        [sample.sample_id]: feedback
                                      }));
                                    }
                                  }}
                                >
                                  <MessageIcon />
                                </IconButton>
                              </Tooltip>
                            </>
                          )}
                          {/* Tester actions */}
                          {!sample.tester_decision && !isReadOnly() && user?.role !== 'Report Owner' && (
                            <>
                              <Tooltip title="Include">
                                <IconButton
                                  size="small"
                                  color="success"
                                  onClick={() => handleSampleDecision(sample.sample_id, 'approved')}
                                >
                                  <CheckIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Exclude">
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => handleSampleDecision(sample.sample_id, 'rejected')}
                                >
                                  <CloseIcon />
                                </IconButton>
                              </Tooltip>
                            </>
                          )}
                          {sample.tester_decision && !isReadOnly() && (
                            <Tooltip title="Change Decision">
                              <IconButton
                                size="small"
                                onClick={() => handleSampleDecision(
                                  sample.sample_id, 
                                  sample.tester_decision === 'approved' ? 'rejected' : 'approved'
                                )}
                              >
                                <EditIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="View Sample Data">
                            <IconButton 
                              size="small"
                              onClick={() => setViewSampleDialog({ open: true, sample })}
                            >
                              <VisibilityIcon />
                            </IconButton>
                          </Tooltip>
                          {user?.role === 'Tester' && !isReadOnly() && selectedVersionId && (
                            <Tooltip title="Delete Sample">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleDeleteSample(sample.sample_id)}
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Stack>
                      </TableCell>
                    </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>
          </Box>
          </Box>
        )}

        {/* LOB Assignment Tab */}
        {((hasReportOwnerFeedback && user?.role === 'Tester' && activeTab === 3) || 
          ((!hasReportOwnerFeedback || user?.role !== 'Tester') && activeTab === 2)) && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              LOB Assignment Management
            </Typography>
            
            {/* LOB Assignment Summary */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h5" color="primary.main">
                      {filteredSamples.filter(s => s.lob_assignment).length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Samples with LOB Assignment
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h5" color="warning.main">
                      {filteredSamples.filter(s => !s.lob_assignment && s.tester_decision === 'approved').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Approved Samples Needing LOB
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h5" color="success.main">
                      {availableLOBs.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Available LOBs
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* LOB Assignment Table */}
            <TableContainer 
              component={Paper} 
              sx={{ 
                overflowX: 'auto',
                overflowY: 'hidden',
                '&::-webkit-scrollbar': {
                  height: 12,
                },
                '&::-webkit-scrollbar-track': {
                  backgroundColor: 'grey.100',
                },
                '&::-webkit-scrollbar-thumb': {
                  backgroundColor: 'grey.400',
                  borderRadius: 2,
                },
              }}
            >
              <Table sx={{ width: '100%' }}>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>Sample ID</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Primary Key</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Sample Status</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Current LOB Assignment</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {samples
                    .filter(s => s.tester_decision === 'approved')
                    .map((sample) => (
                      <TableRow key={`${sample.sample_id}_v${sample.version_number || 1}`}>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {sample.sample_id}
                          </Typography>
                        </TableCell>
                        <TableCell>{sample.primary_key_value}</TableCell>
                        <TableCell>{getStatusChip(sample)}</TableCell>
                        <TableCell>
                          {sample.lob_assignment ? (
                            <Chip label={sample.lob_assignment} size="small" color="primary" />
                          ) : (
                            <Chip label="Not Assigned" size="small" color="warning" variant="outlined" />
                          )}
                        </TableCell>
                        <TableCell>
                          <FormControl size="small" sx={{ minWidth: 150 }}>
                            <Select
                              value={sampleLOBs[sample.sample_id] || sample.lob_assignment || ''}
                              onChange={(e) => handleLOBAssignment(sample.sample_id, e.target.value)}
                              displayEmpty
                              disabled={isReadOnly()}
                            >
                              <MenuItem value="">
                                <em>Not Assigned</em>
                              </MenuItem>
                              {availableLOBs.map((lob) => (
                                <MenuItem key={lob} value={lob}>
                                  {lob}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </TableCell>
                      </TableRow>
                    ))}
                  {filteredSamples.filter(s => s.tester_decision === 'approved').length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Typography variant="body2" color="text.secondary">
                          No approved samples available for LOB assignment
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            {!isReadOnly() && user?.role === 'Tester' && filteredSamples.filter(s => s.tester_decision === 'approved' && !s.lob_assignment).length > 0 && (
              <Alert severity="info" sx={{ mt: 3 }}>
                <Typography variant="body2">
                  {filteredSamples.filter(s => s.tester_decision === 'approved' && !s.lob_assignment).length} approved samples can be assigned to LOBs.
                </Typography>
              </Alert>
            )}
          </Box>
        )}

        {/* Documents Tab */}
        {((hasReportOwnerFeedback && user?.role === 'Tester' && activeTab === 4) || 
          ((!hasReportOwnerFeedback || user?.role !== 'Tester') && activeTab === 3)) && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Sample Selection Documents
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                Upload supporting documents, test data files, and reference materials for the sample selection phase.
              </Typography>
            </Alert>
            <PhaseDocumentManager
              cycleId={cycleIdNum}
              reportId={reportIdNum}
              phaseId={4} // Sample Selection phase ID
              phaseName="Sample Selection"
            />
          </Box>
        )}
      </Paper>

      {/* Generate Samples Dialog */}
      {console.log('Rendering dialogs - showGenerateDialog:', showGenerateDialog)}
      <Dialog 
        open={showGenerateDialog} 
        onClose={() => {
          setShowGenerateDialog(false);
          // Don't reset - keep user's preference
        }} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          Generate New Samples
        </DialogTitle>
        <DialogContent>
          <Tabs 
            value={samplingMethod} 
            onChange={(e, value) => setSamplingMethod(value)}
            sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
          >
            <Tab label="Intelligent Sampling (30/50/20)" value="random" icon={<PsychologyIcon />} iconPosition="start" />
            <Tab label="Intelligent Sampling" value="intelligent" icon={<ScienceIcon />} iconPosition="start" />
          </Tabs>

          {samplingMethod === 'random' ? (
            <>
              <Alert severity="info" sx={{ mb: 2 }}>
                Intelligent sampling will generate samples with the following distribution:
                • 30% Clean samples - typical values near statistical mean
                • 50% Anomaly samples - outliers, DQ rule violations, and edge cases  
                • 20% Boundary samples - minimum/maximum values and regulatory limits
              </Alert>
              <TextField
                label="Number of Samples"
                type="number"
                value={sampleSize}
                onChange={(e) => {
                  const value = e.target.value;
                  const parsed = parseInt(value);
                  if (!isNaN(parsed)) {
                    setSampleSize(parsed);
                  }
                }}
                inputProps={{
                  min: 1,
                  max: 1000,
                  step: 1
                }}
                helperText="Enter a number between 1 and 1000"
                fullWidth
                sx={{ mt: 2 }}
              />
              <Alert severity="info" sx={{ mt: 2 }}>
                Random sampling will generate synthetic samples based on scoped attributes.
                New samples will be added to your existing sample list.
              </Alert>
            </>
          ) : (
            <>
              <Alert severity="info" sx={{ mb: 2 }}>
                Intelligent sampling uses profiling results to select anomaly-based and boundary condition samples with explainability.
              </Alert>
              {!profilingJobId && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  No profiling job found. Please complete data profiling first to use intelligent sampling.
                </Alert>
              )}
              <IntelligentSamplingPanel
                cycleId={cycleIdNum}
                reportId={reportIdNum}
                profilingJobId={profilingJobId || undefined}
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setShowGenerateDialog(false);
            // Don't reset - keep user's preference
          }}>Cancel</Button>
          {samplingMethod === 'random' && (
            <Button 
              onClick={handleGenerateSamples} 
              variant="contained" 
              color="primary"
              disabled={!sampleSize || sampleSize < 1 || sampleSize > 1000 || basicGenerating}
              startIcon={basicGenerating ? <CircularProgress size={20} /> : null}
            >
              {basicGenerating ? 'Generating...' : 'Generate Intelligent Samples'}
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Enhanced Generate Samples Dialog */}
      <Dialog 
        open={showEnhancedGenerateDialog} 
        onClose={() => setShowEnhancedGenerateDialog(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ScienceIcon color="primary" />
            Enhanced Sample Generation
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3 }}>
            Intelligent sampling analyzes your data to select optimal samples based on:
            • Clean data (30%) - typical values near statistical mean
            • Anomalies (50%) - outliers, DQ rule violations, and edge cases
            • Boundaries (20%) - minimum/maximum values and regulatory limits
          </Alert>

          <Grid container spacing={3}>
            {/* Sample Size */}
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label="Sample Size"
                type="number"
                value={enhancedSampleSize}
                onChange={(e) => {
                  const value = parseInt(e.target.value);
                  if (!isNaN(value) && value > 0) {
                    setEnhancedSampleSize(value);
                  }
                }}
                inputProps={{
                  min: 1,
                  max: 10000,
                  step: 1
                }}
                helperText="Number of samples to generate (1-10,000)"
                fullWidth
              />
            </Grid>

            {/* Sampling Strategy */}
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Sampling Strategy</InputLabel>
                <Select
                  value={enhancedSamplingStrategy}
                  onChange={(e) => setEnhancedSamplingStrategy(e.target.value)}
                  label="Sampling Strategy"
                >
                  <MenuItem value="intelligent">Intelligent (Anomaly + Stratified + Random)</MenuItem>
                  <MenuItem value="anomaly_focused">Anomaly Focused</MenuItem>
                  <MenuItem value="stratified">Stratified by Key Attributes</MenuItem>
                  <MenuItem value="random">Random Sampling</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Data Source Selection */}
            <Grid size={{ xs: 12 }}>
              {dataSources.length > 0 ? (
                <FormControl fullWidth>
                  <InputLabel>Data Source</InputLabel>
                  <Select
                    value={enhancedDataSource}
                    onChange={(e) => setEnhancedDataSource(e.target.value)}
                    label="Data Source"
                  >
                    {dataSources.map((ds: any) => (
                      <MenuItem key={ds.id} value={ds.id}>
                        {ds.source_name} ({ds.source_type})
                      </MenuItem>
                    ))}
                  </Select>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                    Select the data source to pull samples from
                  </Typography>
                </FormControl>
              ) : (
                <Alert severity="warning">
                  No data sources found. Please ensure data sources are configured in the Planning phase.
                </Alert>
              )}
            </Grid>

            {/* Use Anomaly Insights */}
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={useAnomalyInsights}
                    onChange={(e) => setUseAnomalyInsights(e.target.checked)}
                  />
                }
                label="Use Anomaly Insights from Data Profiling"
              />
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                When enabled, leverages data quality anomalies to prioritize samples with known issues.
              </Typography>
            </Grid>
          </Grid>

          {enhancedGenerating && (
            <Box sx={{ mt: 3 }}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
                Generating samples from data source...
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setShowEnhancedGenerateDialog(false)}
            disabled={enhancedGenerating}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleEnhancedGenerateSamples} 
            variant="contained" 
            color="primary"
            disabled={enhancedGenerating || !enhancedDataSource}
            startIcon={enhancedGenerating ? <CircularProgress size={16} /> : <ScienceIcon />}
          >
            {enhancedGenerating ? 'Generating...' : 'Generate Enhanced Samples'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Submit for Approval Dialog */}
      <Dialog open={showSubmitDialog} onClose={() => setShowSubmitDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Submit Samples for Approval</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            You are about to submit {filteredSamples.filter(s => s.tester_decision === 'approved').length} samples for report owner approval.
          </Typography>
          <TextField
            label="Submission Notes (Optional)"
            multiline
            rows={3}
            value={submissionNotes}
            onChange={(e) => setSubmissionNotes(e.target.value)}
            fullWidth
            sx={{ mt: 2 }}
          />
          <Alert severity="info" sx={{ mt: 2 }}>
            Only samples marked as "approved" will be submitted for approval.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSubmitDialog(false)}>Cancel</Button>
          <Button 
            onClick={async () => {
              try {
                // Get included sample IDs
                const includedSamples = filteredSamples.filter(s => s.tester_decision === 'approved');
                const includedSampleIds = includedSamples.map(s => s.sample_id);
                
                console.log('Submitting samples:', includedSampleIds);
                console.log('Included samples:', includedSamples);
                
                if (includedSampleIds.length === 0) {
                  showToast.warning('No samples marked as "approved" to submit');
                  return;
                }
                
                // LOB assignment is now optional - testers will assign later
                // No validation needed for LOB assignments
                
                // Use version-based submit endpoint instead of legacy endpoint
                if (!selectedVersionId) {
                  showToast.error('No version selected for submission');
                  return;
                }
                
                console.log('Submitting to endpoint:', `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/submit`);
                console.log('Submit payload:', {
                  sample_ids: includedSampleIds,
                  notes: submissionNotes
                });
                
                const submitResponse = await apiClient.post(
                  `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/samples/submit`,
                  {
                    sample_ids: includedSampleIds,
                    notes: submissionNotes
                  }
                );

                // Universal assignment is now created by the backend automatically
                showToast.success('Samples submitted for Report Owner review');
                setShowSubmitDialog(false);
                setSubmissionNotes('');
                await loadSamples();
                await loadPhaseStatus();
              } catch (error: any) {
                console.error('Error submitting samples:', error);
                console.error('Error response:', error.response);
                console.error('Error data:', error.response?.data);
                console.error('Error status:', error.response?.status);
                showToast.error(error.response?.data?.detail || error.message || 'Failed to submit samples');
              }
            }} 
            variant="contained" 
            color="primary"
          >
            Submit
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Sample Data Dialog */}
      <Dialog 
        open={viewSampleDialog.open} 
        onClose={() => setViewSampleDialog({ open: false, sample: null })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Sample Data - {viewSampleDialog.sample?.sample_id}
        </DialogTitle>
        <DialogContent>
          {viewSampleDialog.sample && (
            <Box>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Sample Category
                  </Typography>
                  <Chip 
                    label={viewSampleDialog.sample.sample_category || 'Unknown'} 
                    color={
                      viewSampleDialog.sample.sample_category === 'CLEAN' ? 'success' :
                      viewSampleDialog.sample.sample_category === 'ANOMALY' ? 'warning' :
                      viewSampleDialog.sample.sample_category === 'BOUNDARY' ? 'info' : 'default'
                    }
                    size="small"
                    sx={{ mt: 0.5 }}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Generation Method
                  </Typography>
                  <Typography variant="body2">
                    {viewSampleDialog.sample.generation_method}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Selection Rationale
                  </Typography>
                  <Typography variant="body2" sx={{ fontStyle: 'italic', mt: 0.5 }}>
                    {viewSampleDialog.sample.rationale || 'No rationale provided'}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Attribute Focus
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500, mt: 0.5 }}>
                    {viewSampleDialog.sample.attribute_focus ? (
                      viewSampleDialog.sample.sample_data && viewSampleDialog.sample.sample_data[viewSampleDialog.sample.attribute_focus] !== undefined ? 
                        `${viewSampleDialog.sample.attribute_focus} (${viewSampleDialog.sample.sample_data[viewSampleDialog.sample.attribute_focus]})` : 
                        viewSampleDialog.sample.attribute_focus
                    ) : '-'}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Risk Score
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 0.5 }}>
                    {viewSampleDialog.sample.risk_score ? `${(viewSampleDialog.sample.risk_score * 100).toFixed(0)}%` : '-'}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Confidence
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 0.5 }}>
                    {viewSampleDialog.sample.confidence_score ? `${(viewSampleDialog.sample.confidence_score * 100).toFixed(0)}%` : '-'}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                    Primary Key Values
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          {primaryKeyColumns.map((col) => (
                            <TableCell key={col} sx={{ fontWeight: 'bold' }}>{col}</TableCell>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          {primaryKeyColumns.map((col) => (
                            <TableCell key={col}>
                              <Typography variant="body2" fontFamily="monospace">
                                {viewSampleDialog.sample?.sample_data?.[col] || '-'}
                              </Typography>
                            </TableCell>
                          ))}
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Generated At
                  </Typography>
                  <Typography variant="body2">
                    {new Date(viewSampleDialog.sample.generated_at).toLocaleString()}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Generated By
                  </Typography>
                  <Typography variant="body2">
                    {viewSampleDialog.sample.generated_by}
                  </Typography>
                </Grid>
                {(viewSampleDialog.sample.risk_score !== undefined || viewSampleDialog.sample.confidence_score !== undefined) && (
                  <>
                    {viewSampleDialog.sample.risk_score !== undefined && (
                      <Grid size={{ xs: 12, md: 6 }}>
                        <Typography variant="subtitle2" color="text.secondary">
                          Risk Score
                        </Typography>
                        <Typography variant="body2">
                          {(viewSampleDialog.sample.risk_score * 100).toFixed(0)}%
                        </Typography>
                      </Grid>
                    )}
                    {viewSampleDialog.sample.confidence_score !== undefined && (
                      <Grid size={{ xs: 12, md: 6 }}>
                        <Typography variant="subtitle2" color="text.secondary">
                          Confidence Score
                        </Typography>
                        <Typography variant="body2">
                          {(viewSampleDialog.sample.confidence_score * 100).toFixed(0)}%
                        </Typography>
                      </Grid>
                    )}
                  </>
                )}
              </Grid>
              
              <Divider sx={{ my: 2 }} />
              
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  Sample Data:
                </Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <pre style={{ margin: 0, overflow: 'auto' }}>
                    {JSON.stringify(viewSampleDialog.sample.sample_data, null, 2)}
                  </pre>
                </Paper>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewSampleDialog({ open: false, sample: null })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Report Owner Review Dialog */}
      <Dialog 
        open={showReviewDialog} 
        onClose={() => setShowReviewDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {reviewDecision === 'approved' ? 'Approve Samples' :
           reviewDecision === 'rejected' ? 'Reject Samples' :
           'Request Changes'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <Alert severity={
              reviewDecision === 'approved' ? 'success' :
              reviewDecision === 'rejected' ? 'error' :
              'warning'
            }>
              {reviewDecision === 'approved' && 
                `You are about to approve ${samples.length} samples for testing.`}
              {reviewDecision === 'rejected' && 
                'Rejecting these samples will require the tester to submit new samples.'}
              {reviewDecision === 'revision_required' && 
                'The tester will need to address your feedback and resubmit samples.'}
            </Alert>
            
            <TextField
              label="Feedback"
              multiline
              rows={4}
              value={reviewFeedback}
              onChange={(e) => setReviewFeedback(e.target.value)}
              fullWidth
              required={reviewDecision !== 'approved'}
              helperText={
                reviewDecision === 'approved' 
                  ? "Optional feedback for the tester"
                  : "Please provide detailed feedback for the tester"
              }
            />

            {currentSubmission && (
              <Box>
                {currentSubmission.assignment_id ? (
                  <>
                    <Typography variant="caption" color="text.secondary">
                      Assignment: {currentSubmission.title}
                    </Typography>
                    <br />
                    <Typography variant="caption" color="text.secondary">
                      Created: {new Date(currentSubmission.created_at).toLocaleDateString()}
                    </Typography>
                  </>
                ) : (
                  <>
                    <Typography variant="caption" color="text.secondary">
                      Submission Version: {currentSubmission.version_number}
                    </Typography>
                    <br />
                    <Typography variant="caption" color="text.secondary">
                      Submitted by: {currentSubmission.submitted_by}
                    </Typography>
                  </>
                )}
                {Object.keys(individualDecisions).length > 0 && (
                  <>
                    <br />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                      Individual Sample Decisions:
                    </Typography>
                    <br />
                    <Typography variant="caption" color="text.secondary">
                      • Approved: {Object.values(individualDecisions).filter(d => d === 'approved').length}
                    </Typography>
                    <br />
                    <Typography variant="caption" color="text.secondary">
                      • Rejected: {Object.values(individualDecisions).filter(d => d === 'rejected').length}
                    </Typography>
                  </>
                )}
              </Box>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowReviewDialog(false)}>Cancel</Button>
          <Button 
            onClick={async () => {
              try {
                if (!currentSubmission) {
                  showToast.error('No assignment to review');
                  return;
                }

                // Check if this is a universal assignment
                if (currentSubmission.assignment_id) {
                  // Handle universal assignment approval/rejection/revision
                  let endpoint;
                  let payload: any = {
                    metadata: {
                      individual_feedback: individualFeedback,
                      individual_decisions: individualDecisions,
                      decision_type: reviewDecision
                    }
                  };
                  
                  if (reviewDecision === 'approved') {
                    endpoint = `/universal-assignments/assignments/${currentSubmission.assignment_id}/approve`;
                    payload.feedback = reviewFeedback;
                  } else if (reviewDecision === 'revision_required') {
                    // For revision, we complete the assignment with revision status
                    endpoint = `/universal-assignments/assignments/${currentSubmission.assignment_id}/complete`;
                    payload.notes = reviewFeedback;
                    payload.completion_data = {
                      decision: 'revision_required',
                      feedback: reviewFeedback,
                      individual_feedback: individualFeedback,
                      individual_decisions: individualDecisions
                    };
                  } else {
                    // For rejection
                    endpoint = `/universal-assignments/assignments/${currentSubmission.assignment_id}/reject`;
                    payload.rejection_reason = reviewFeedback || 'Samples do not meet requirements';
                  }
                  
                  await apiClient.post(endpoint, payload);
                } else {
                  // Fallback to old submission review system
                  await apiClient.post(
                    `/sample-selection/cycles/${cycleIdNum}/reports/${reportIdNum}/submissions/${currentSubmission.submission_id}/review`,
                    {
                      decision: reviewDecision,
                      feedback: reviewFeedback,
                      individual_feedback: individualFeedback,
                      individual_decisions: individualDecisions
                    }
                  );
                }
                
                showToast.success(
                  reviewDecision === 'approved' 
                    ? 'Samples approved successfully!'
                    : reviewDecision === 'rejected'
                    ? 'Samples rejected.'
                    : 'Change request sent to tester.'
                );
                
                setShowReviewDialog(false);
                setReviewFeedback('');
                
                // Clear the current submission for Report Owner since it's now completed
                if (user?.role === 'Report Owner') {
                  setCurrentSubmission(null);
                }
                
                // Reload data
                await loadSamples();
                await loadPhaseStatus();
                
                // If tester, also reload feedback
                if (user?.role === 'Tester') {
                  await loadFeedback();
                }
                
                // For Report Owner, reload the page to refresh assignments
                if (user?.role === 'Report Owner') {
                  window.location.reload();
                }
                
              } catch (error: any) {
                console.error('Error reviewing samples:', error);
                showToast.error(error.response?.data?.detail || 'Failed to submit review');
              }
            }} 
            variant="contained" 
            color={
              reviewDecision === 'approved' ? 'success' :
              reviewDecision === 'rejected' ? 'error' :
              'warning'
            }
            disabled={reviewDecision !== 'approved' && !reviewFeedback}
          >
            Confirm {
              reviewDecision === 'approved' ? 'Approval' :
              reviewDecision === 'rejected' ? 'Rejection' :
              'Change Request'
            }
          </Button>
        </DialogActions>
      </Dialog>

      {/* Version History Dialog */}
      <SampleSelectionVersionHistory
        cycleId={cycleIdNum}
        reportId={reportIdNum}
        open={showVersionHistoryDialog}
        onClose={() => setShowVersionHistoryDialog(false)}
        currentVersion={versions.find(v => v.version_id === selectedVersionId)?.version_number}
      />
    </Container>
  );
};

export default SampleSelectionPage;