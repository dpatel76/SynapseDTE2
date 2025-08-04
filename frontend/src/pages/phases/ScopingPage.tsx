import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  CircularProgress,
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
  AlertTitle,
  Stack,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
} from '@mui/material';
import { ScopingDecisionToggle } from '../../components/scoping/ScopingDecisionToggle';
import { ScopingSubmissionDialog } from '../../components/scoping/ScopingSubmissionDialog';
import ReportOwnerDecisionStatus from '../../components/scoping/ReportOwnerDecisionStatus';
import { 
  ScopingDecisionDisplay,
  ScopingStatusDisplay,
  ScopingTesterDecisionDisplay,
  ScopingReportOwnerDecisionDisplay
} from '../../components/scoping/ScopingDecisionDisplay';
import { VersionHistoryViewer } from '../../components/common/VersionHistoryViewer';
import { DQResultsDialog } from '../../components/scoping/DQResultsDialog';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';
import { DynamicActivityCards } from '../../components/phase/DynamicActivityCards';
import { useUniversalAssignments } from '../../hooks/useUniversalAssignments';
import { UniversalAssignmentAlert } from '../../components/UniversalAssignmentAlert';
import { workflowHooks } from '../../services/universalAssignmentWorkflow';
import {
  PlayArrow as PlayArrowIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  Key as KeyIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Assignment as AssignmentIcon,
  Psychology as RecommendIcon,
  Refresh as RefreshIcon,
  RateReview as ReviewIcon,
  Send as SendIcon,
  Check as CheckIcon,
  Flag as FlagIcon,
  CheckCircle,
  Cancel,
  Edit,
  Search as SearchIcon,
  FilterList as FilterIcon,
  History as HistoryIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { ReportAttribute } from '../../api/planning';
// import WorkflowProgress from '../../components/WorkflowProgress';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import PhaseDocumentManager from '../../components/documents/PhaseDocumentManager';
import { BatchProgressIndicator } from '../../components/common/BatchProgressIndicator';
import ReportOwnerScopingFeedback from '../../components/scoping/ReportOwnerScopingFeedback';
import ReportOwnerScopingFeedbackChecker from '../../components/scoping/ReportOwnerScopingFeedbackChecker';


interface ReportInfo {
  report_id: number;
  report_name: string;
  cycle_id?: number;
  cycle_name?: string;
  lob: string;
  assigned_tester?: string;
  report_owner?: string;
  description?: string;
  regulatory_framework?: string;
  frequency?: string;
  due_date?: string;
  priority?: string;
}

interface ScopingPhaseStatus {
  cycle_id: number;
  report_id: number;
  phase_status: 'Not Started' | 'In Progress' | 'Complete';
  total_attributes: number;
  attributes_with_recommendations: number;
  attributes_with_decisions: number;
  attributes_scoped_for_testing: number;
  submission_status?: string;
  approval_status?: string;
  can_generate_recommendations: boolean;
  started_at?: string;
  completed_at?: string;
  selected_attributes_count?: number;
  total_approved_attributes_count?: number;
  pk_attributes_count?: number;
  cde_attributes_count?: number;
  historical_issues_count?: number;
  attributes_with_anomalies?: number;
  can_complete?: boolean;
  completion_requirements?: string[];
  can_submit_for_approval?: boolean;
  // New fields for proper state management
  has_submission?: boolean;
  has_review?: boolean;
  current_version?: number;
  review_decision?: string;
  needs_revision?: boolean;
  review_comments?: string;
}

interface ScopingVersion {
  version: number;
  submitted_at: string;
  submitted_by: string;
  status: string;
  review_decision?: string;
  review_comments?: string;
  attributes_count: number;
  decisions: Record<number, 'include' | 'exclude'>;
}

interface AttributeForScoping {
  attribute_id: string;
  attribute_name: string;
  mdrm?: string; // MDRM code (e.g., M046)
  description?: string; // Description (e.g., ReferenceNumber)
  line_item_number?: string;
  data_type?: string;
  is_primary_key: boolean;
  is_cde?: boolean;
  cde_flag?: boolean; // From API response
  historical_issues_flag?: boolean;
  selected_for_testing: boolean;
  llm_risk_score?: number;
  llm_confidence_score?: number;
  llm_rationale?: string;
  overall_risk_score?: number;
  approval_status?: string;
  // Additional LLM response fields
  typical_source_documents?: string;
  keywords_to_look_for?: string;
  testing_approach?: string;
  validation_rules?: string;
  // Data Quality Score fields
  composite_dq_score?: number;
  dq_rules_count?: number;
  dq_rules_passed?: number;
  dq_rules_failed?: number;
  has_profiling_data?: boolean;
  // Tester decision fields
  tester_decision?: 'accept' | 'decline' | 'override' | null;
  tester_rationale?: string;
  tester_decided_at?: string;
  tester_decided_by_id?: number;
  // Report Owner decision fields
  report_owner_decision?: 'approved' | 'rejected' | 'pending' | 'needs_revision' | null;
  report_owner_status?: string;
  report_owner_notes?: string;
  report_owner_rejection_reason?: string;
  report_owner_approved_at?: string;
  report_owner_rejected_at?: string;
  report_owner_decided_at?: string;
  report_owner_decided_by_id?: number;
  // Special flags
  is_override?: boolean;
  override_reason?: string;
  final_scoping?: boolean;
  // Status field
  status?: 'pending' | 'submitted' | 'approved' | 'rejected' | 'needs_revision';
}

// Simple toast replacement
const showToast = {
  success: (message: string) => {
    console.log('SUCCESS:', message);
    alert(message);
  },
  error: (message: string) => {
    console.log('ERROR:', message);
    alert('Error: ' + message);
  },
  warning: (message: string) => {
    console.log('WARNING:', message);
    alert('Warning: ' + message);
  }
};

const ScopingPage: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Convert string params to numbers
  const cycleIdNum = cycleId ? parseInt(cycleId, 10) : 0;
  const reportIdNum = reportId ? parseInt(reportId, 10) : 0;
  
  // Use unified status system
  const { data: unifiedPhaseStatus, isLoading: statusLoading, refetch: refetchStatus } = usePhaseStatus('Scoping', cycleIdNum, reportIdNum);

  // Universal Assignments integration
  const {
    hasAssignment,
    assignment,
    canDirectAccess,
    acknowledgeMutation,
    startMutation,
    completeMutation
  } = useUniversalAssignments({
    phase: 'Scoping',
    cycleId: cycleIdNum,
    reportId: reportIdNum,
    assignmentType: 'Scoping Approval'
  });

  // State
  const [attributes, setAttributes] = useState<AttributeForScoping[]>([]);
  const [selectedAttributes, setSelectedAttributes] = useState<string[]>([]); // For scoping decisions (included/excluded)
  const [bulkSelectedAttributes, setBulkSelectedAttributes] = useState<string[]>([]); // For bulk selection UI
  const [loading, setLoading] = useState(true);
  const [autoSaveTimeout, setAutoSaveTimeout] = useState<NodeJS.Timeout | null>(null);
  const [phaseStatus, setPhaseStatus] = useState<ScopingPhaseStatus | null>(null);
  
  // New state for explicit scoping decisions
  const [scopingDecisions, setScopingDecisions] = useState<Record<number, 'include' | 'exclude' | 'pending'>>({});
  const [submissionDialogOpen, setSubmissionDialogOpen] = useState(false);
  const [previousSubmission, setPreviousSubmission] = useState<any>(null);
  const [phaseLoading, setPhaseLoading] = useState(false);
  const [showStartDialog, setShowStartDialog] = useState(false);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false);

  // State for report info
  const [reportInfo, setReportInfo] = useState<ReportInfo | null>(null);
  const [reportInfoLoading, setReportInfoLoading] = useState(false);

  // State for scoping workflow
  const [scopingStep, setScopingStep] = useState(0);

  // State for LLM Analysis dialog
  const [showLLMAnalysisDialog, setShowLLMAnalysisDialog] = useState(false);
  const [showDQResultsDialog, setShowDQResultsDialog] = useState(false);
  const [selectedDQAttribute, setSelectedDQAttribute] = useState<{ id: string; name: string } | null>(null);
  const [selectedAttributeForAnalysis, setSelectedAttributeForAnalysis] = useState<AttributeForScoping | null>(null);

  // State for job tracking
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  // Add state for feedback and versioning
  const [feedback, setFeedback] = useState<any>(null);
  const [versions, setVersions] = useState<ScopingVersion[]>([]);
  const [showFeedbackDetails, setShowFeedbackDetails] = useState(false);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [viewingVersion, setViewingVersion] = useState<ScopingVersion | null>(null);
  
  // Add filter and search states to match data profiling
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filterTesterDecision, setFilterTesterDecision] = useState<string>('all');
  const [filterReportOwnerDecision, setFilterReportOwnerDecision] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  const [versionList, setVersionList] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState(0);
  const [hasReportOwnerFeedback, setHasReportOwnerFeedback] = useState(false);

  // Role-based redirection for Report Owners
  useEffect(() => {
    // @ts-ignore - Role comes from backend as string "Report Owner"
    if (user?.role === 'Report Owner') {
      // Report Owners should use the scoping review page instead
      navigate(`/cycles/${cycleId}/reports/${reportId}/scoping-review`, { replace: true });
      return;
    }
  }, [user, cycleId, reportId, navigate]);

  // Debug selectedAttributes changes removed

  // Cleanup auto-save timeout on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimeout) {
        clearTimeout(autoSaveTimeout);
      }
    };
  }, [autoSaveTimeout]);

  // Check for active jobs related to this report
  const checkForActiveJobs = async () => {
    try {
      console.log('Checking for active jobs...', { cycleIdNum, reportIdNum });
      const response = await apiClient.get('/jobs/active');
      const activeJobs = response.data.active_jobs || [];
      console.log('Active jobs found:', activeJobs.length);
      console.log('Active jobs:', activeJobs);
      
      // Find LLM recommendation job for this cycle/report
      const llmJob = activeJobs.find((job: any) => {
        console.log('Checking job:', {
          job_type: job.job_type,
          metadata: job.metadata,
          status: job.status,
          matches: job.job_type === 'scoping_recommendations' &&
                  Number(job.metadata?.cycle_id) === Number(cycleIdNum) &&
                  Number(job.metadata?.report_id) === Number(reportIdNum) &&
                  ['pending', 'running'].includes(job.status)
        });
        return job.job_type === 'scoping_recommendations' &&
               Number(job.metadata?.cycle_id) === Number(cycleIdNum) &&
               Number(job.metadata?.report_id) === Number(reportIdNum) &&
               ['pending', 'running'].includes(job.status);
      });
      
      if (llmJob) {
        console.log('Found active LLM job:', llmJob);
        setCurrentJobId(llmJob.job_id);
      } else {
        console.log('No active LLM job found for cycle:', cycleIdNum, 'report:', reportIdNum);
      }
    } catch (error) {
      console.error('Error checking for active jobs:', error);
    }
  };

  // Load data on component mount
  useEffect(() => {
    if (cycleIdNum && reportIdNum) {
      loadReportInfo();
      loadAttributes();
      loadLegacyPhaseStatus();
      if (user?.role === 'Tester') {
        loadFeedback();
        loadVersionHistory();
        loadVersionsForDropdown();
        checkForActiveJobs(); // Check for active jobs when loading
      }
    }
  }, [cycleIdNum, reportIdNum, user?.role]);

  // No need for polling effect - BatchProgressIndicator handles its own polling

  // Helper functions to determine read-only state
  const isReadOnly = (): boolean => {
    // Report Owners are always read-only
    if (user?.role === 'Report Owner') return true;
    
    // Get current version from versionList
    const currentVersion = versionList.find(v => v.version_id === selectedVersionId);
    
    // If version is not draft, it's read-only
    return currentVersion && currentVersion.version_status !== 'draft';
  };
  
  const canEditDecisions = (): boolean => {
    // Can edit if:
    // 1. No submission exists yet
    if (!phaseStatus?.has_submission) return true;
    
    // 2. Revision is requested (from either phase status or feedback)
    if (phaseStatus?.needs_revision || feedback?.needs_revision) return true;
    
    // 3. Current version can be edited (e.g., new draft version created after feedback)
    if (phaseStatus?.can_generate_recommendations) return true;
    
    return false;
  };

  // Helper functions for decision counts - memoized for performance and reactivity
  const getDecisionCounts = useMemo(() => {
    // Count actual decisions from attributes (more reliable than scopingDecisions state)
    let included = 0;
    let excluded = 0;
    let pending = 0;
    
    console.log('Calculating decision counts, total attributes:', attributes.length);
    
    attributes.forEach(attr => {
      const attrId = parseInt(attr.attribute_id);
      let decision: 'include' | 'exclude' | 'pending';
      
      // Inline getScopingDecision logic to avoid dependency issues
      if (attr.is_primary_key) {
        decision = 'include';
      } else if (attr.tester_decision === 'accept') {
        decision = 'include';
      } else if (attr.tester_decision === 'decline') {
        decision = 'exclude';
      } else {
        decision = scopingDecisions[attrId] || 'pending';
        if (decision === 'pending') {
          console.log('Pending attribute:', attr.attribute_id, 'tester_decision:', attr.tester_decision, 'scopingDecisions:', scopingDecisions[attrId]);
        }
      }
      
      if (decision === 'include') {
        included++;
      } else if (decision === 'exclude') {
        excluded++;
      } else {
        pending++;
      }
    });
    
    
    // Count primary keys separately for reference
    const pkCount = attributes.filter(attr => attr.is_primary_key).length;
    
    console.log('Decision counts:', { included, excluded, pending, total: attributes.length, pkCount });
    
    return {
      included,
      excluded,
      pending,
      pkCount,
      total: attributes.length
    };
  }, [attributes, scopingDecisions]); // Dependencies: recalculate when attributes or decisions change

  const handleScopingDecision = async (attributeId: string, decision: 'include' | 'exclude') => {
    // Check if editing is allowed
    if (isReadOnly()) {
      showToast.error('This scoping submission is read-only. No changes are allowed.');
      return;
    }
    
    if (!canEditDecisions()) {
      showToast.error('Cannot modify scoping decisions after submission.');
      return;
    }
    
    // Convert to string for selectedAttributes array
    const attrIdString = attributeId.toString();
    
    try {
      // Find the attribute to check if it's a primary key
      const attribute = attributes.find(attr => attr.attribute_id === attributeId);
      if (!attribute) return;
      
      // Primary key attributes cannot be excluded
      if (attribute.is_primary_key && decision === 'exclude') {
        showToast.error('Primary key attributes must be included in scoping');
        return;
      }
      
      // Update UI immediately for responsiveness
      const attrIdNum = parseInt(attributeId);
      setScopingDecisions(prev => ({
        ...prev,
        [attrIdNum]: decision
      }));
      
      // Update selectedAttributes for backward compatibility
      if (decision === 'include') {
        setSelectedAttributes(prev => [...prev.filter(id => id !== attrIdString), attrIdString]);
      } else {
        setSelectedAttributes(prev => prev.filter(id => id !== attrIdString));
      }
      
      // Prepare the API payload for tester decision
      const decisionPayload = {
        decision: decision === 'include' ? 'accept' : 'decline',
        final_scoping: decision === 'include',
        rationale: decision === 'include' 
          ? (attribute.is_primary_key 
              ? 'Primary Key attribute - automatically included for testing'
              : 'Selected for testing based on risk assessment')
          : 'Not selected for testing - lower priority',
        override_reason: null
      };
      
      // Save decision to backend
      await apiClient.post(`/scoping/attributes/${attributeId}/tester-decision`, decisionPayload);
      
      // Update the attribute in local state with the new decision
      setAttributes(prevAttributes => 
        prevAttributes.map(attr => 
          attr.attribute_id === attributeId 
            ? {
                ...attr,
                tester_decision: decisionPayload.decision as 'accept' | 'decline' | 'override',
                final_scoping: decisionPayload.final_scoping,
                tester_rationale: decisionPayload.rationale,
                tester_decided_at: new Date().toISOString()
              }
            : attr
        )
      );
      
    } catch (error: any) {
      console.error('Error saving scoping decision:', error);
      showToast.error(`Failed to save decision: ${error.response?.data?.detail || error.message}`);
      
      // Revert UI state on error
      const attrIdNum = parseInt(attributeId);
      setScopingDecisions(prev => {
        const newState = { ...prev };
        delete newState[attrIdNum];
        return newState;
      });
    }
    
    // Trigger auto-save only if not viewing a version
    if (!viewingVersion) {
      const updatedSelected = decision === 'include' 
        ? [...selectedAttributes.filter(id => id !== attrIdString), attrIdString]
        : selectedAttributes.filter(id => id !== attrIdString);
      saveAllScopingDecisions(updatedSelected);
    }
  };

  const handleBulkAction = async (action: 'include' | 'exclude') => {
    try {
      setPhaseLoading(true);
      
      // Save each decision to backend
      const savePromises = bulkSelectedAttributes.map(async (attrIdStr) => {
        const attribute = attributes.find(attr => attr.attribute_id === attrIdStr);
        if (!attribute || attribute.is_primary_key) return; // Skip PKs
        
        const decisionPayload = {
          decision: action === 'include' ? 'accept' : 'decline',
          final_scoping: action === 'include',
          rationale: action === 'include' 
            ? 'Selected for testing based on bulk approval'
            : 'Not selected for testing - bulk exclusion',
          override_reason: null
        };
        
        // Save to backend
        await apiClient.post(`/scoping/attributes/${attrIdStr}/tester-decision`, decisionPayload);
      });
      
      // Wait for all saves to complete
      await Promise.all(savePromises);
      
      // Update local state
      const updates: Record<number, 'include' | 'exclude'> = {};
      bulkSelectedAttributes.forEach(attrIdStr => {
        const attrId = parseInt(attrIdStr);
        updates[attrId] = action;
      });
      
      setScopingDecisions(prev => ({
        ...prev,
        ...updates
      }));
      
      // Update selectedAttributes
      if (action === 'include') {
        setSelectedAttributes(prev => {
          const combined = Array.from(new Set(prev.concat(bulkSelectedAttributes)));
          return combined;
        });
      } else {
        setSelectedAttributes(prev => prev.filter(id => !bulkSelectedAttributes.includes(id)));
      }
      
      // Update attributes state to reflect saved decisions
      setAttributes(prevAttributes => 
        prevAttributes.map(attr => {
          if (bulkSelectedAttributes.includes(attr.attribute_id.toString())) {
            return {
              ...attr,
              tester_decision: action === 'include' ? 'accept' : 'decline',
              final_scoping: action === 'include',
              tester_rationale: action === 'include' 
                ? 'Selected for testing based on bulk approval'
                : 'Not selected for testing - bulk exclusion',
              tester_decided_at: new Date().toISOString()
            };
          }
          return attr;
        })
      );
      
      showToast.success(`Successfully ${action === 'include' ? 'included' : 'excluded'} ${bulkSelectedAttributes.length} attributes`);
      
      // Clear bulk selection
      setBulkSelectedAttributes([]);
      
    } catch (error: any) {
      console.error('Error saving bulk decisions:', error);
      showToast.error(`Failed to save bulk decisions: ${error.response?.data?.detail || error.message}`);
    } finally {
      setPhaseLoading(false);
    }
  };

  const getScopingDecision = (attributeId: number | string): 'include' | 'exclude' | 'pending' => {
    const attrId = typeof attributeId === 'string' ? parseInt(attributeId) : attributeId;
    const attr = attributes.find(a => parseInt(a.attribute_id) === attrId);
    if (attr?.is_primary_key) return 'include';
    
    // Check the tester_decision field first (persisted decisions)
    if (attr?.tester_decision === 'accept') return 'include';
    if (attr?.tester_decision === 'decline') return 'exclude';
    
    // Fall back to local state (new/unsaved decisions)
    return scopingDecisions[attrId] || 'pending';
  };

  const loadReportInfo = async () => {
    try {
      setReportInfoLoading(true);
      
      // Get report info from cycle-reports endpoint which includes names
      const response = await apiClient.get(`/cycle-reports/${cycleIdNum}/reports/${reportIdNum}`);
      const reportData = response.data;
      
      // Also get cycle info
      let cycleName = `Cycle ${cycleIdNum}`;
      try {
        const cycleResponse = await apiClient.get(`/cycles/${cycleIdNum}`);
        cycleName = cycleResponse.data.cycle_name || cycleName;
      } catch (cycleError) {
        console.error('Error loading cycle info:', cycleError);
      }
      
      // Map the API response to our expected format
      setReportInfo({
        report_id: reportData.report_id,
        report_name: reportData.report_name,
        cycle_id: cycleIdNum,
        cycle_name: cycleName,
        lob: reportData.lob_name || 'Unknown',
        assigned_tester: reportData.tester_name || 'Not assigned',
        report_owner: reportData.report_owner_name || 'Not specified',
        description: reportData.description,
        regulatory_framework: reportData.regulatory_framework,
        frequency: reportData.frequency,
        // These fields don't exist in the current API response
        due_date: undefined,
        priority: undefined
      });
    } catch (error) {
      console.error('Error loading report info:', error);
      // Fallback to basic info
      setReportInfo({
        report_id: reportIdNum,
        report_name: `Report ${reportIdNum}`,
        cycle_id: cycleIdNum,
        cycle_name: `Cycle ${cycleIdNum}`,
        lob: 'Unknown',
        assigned_tester: 'Unknown',
        report_owner: 'Unknown'
      });
    } finally {
      setReportInfoLoading(false);
    }
  };

  const loadAttributes = async () => {
    try {
      setLoading(true);
      // Get ALL attributes from scoping endpoint (includes LLM fields)
      // This endpoint returns attributes with all LLM enhancements
      const response = await apiClient.get(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/attributes`);
      
      // Get LLM recommendations if they exist (optional, since scoping endpoint already includes LLM data)
      let recommendations: any[] = [];
      try {
        const recResponse = await apiClient.get(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/recommendations`);
        // The API returns an object with a recommendations array
        recommendations = recResponse.data.recommendations || [];
      } catch (error) {
        // No LLM recommendations found yet
      }
      
      // Convert to scoping attributes with LLM recommendations
      // The scoping endpoint returns an array directly with all LLM fields
      const scopingAttributes: AttributeForScoping[] = response.data.map((attr: any) => {
        // Find matching LLM recommendation
        const recommendation = recommendations.find((rec: any) => rec.attribute_id === attr.attribute_id);
        
        return {
          ...attr,
          selected_for_testing: attr.is_primary_key || false, // PK attributes selected by default
          // The scoping endpoint already provides all LLM fields
          llm_risk_score: attr.llm_risk_score || recommendation?.recommendation_score || null,
          llm_rationale: attr.llm_rationale || recommendation?.rationale || (attr.is_primary_key ? 'Primary key attribute - required for testing' : null),
          overall_risk_score: attr.risk_score || recommendation?.recommendation_score || null,
          
          // These fields are already in the scoping response
          typical_source_documents: attr.typical_source_documents || recommendation?.expected_source_documents?.join('; '),
          keywords_to_look_for: attr.keywords_to_look_for || recommendation?.search_keywords?.join('; '),
          testing_approach: attr.testing_approach,
          validation_rules: attr.validation_rules,
          
          // Map decision fields from API response
          tester_decision: attr.tester_decision,
          tester_rationale: attr.tester_rationale,
          tester_decided_at: attr.tester_decided_at,
          tester_decided_by_id: attr.tester_decided_by_id,
          
          report_owner_decision: attr.report_owner_decision,
          report_owner_notes: attr.report_owner_notes,
          report_owner_decided_at: attr.report_owner_decided_at,
          report_owner_decided_by_id: attr.report_owner_decided_by_id,
          
          status: attr.status,
          is_cde: attr.is_cde,
          is_override: attr.is_override
        };
      });
      
      // Sort attributes by: PK first, then CDE, then Issues, then Line Item #
      const sortedAttributes = scopingAttributes.sort((a, b) => {
        // 1. Primary Keys first
        if (a.is_primary_key && !b.is_primary_key) return -1;
        if (!a.is_primary_key && b.is_primary_key) return 1;
        
        // 2. CDE flags (check both cde_flag and is_cde)
        const aCDE = a.cde_flag || a.is_cde;
        const bCDE = b.cde_flag || b.is_cde;
        if (aCDE && !bCDE) return -1;
        if (!aCDE && bCDE) return 1;
        
        // 3. Historical Issues
        if (a.historical_issues_flag && !b.historical_issues_flag) return -1;
        if (!a.historical_issues_flag && b.historical_issues_flag) return 1;
        
        // 4. Finally by Line Item # (parse as integer)
        const lineA = parseInt(a.line_item_number || '999999');
        const lineB = parseInt(b.line_item_number || '999999');
        
        return lineA - lineB;
      });
      
      setAttributes(sortedAttributes);
      
      // Try to load existing scoping decisions first
      try {
        await loadScopingDecisions();
      } catch (error) {
        // If no decisions exist yet, set selected attributes (PK attributes are pre-selected)
        const preSelected = scopingAttributes
          .filter(attr => attr.is_primary_key)
          .map(attr => attr.attribute_id);
        setSelectedAttributes(preSelected);
        
        // Initialize scopingDecisions with primary keys as 'include'
        const initialDecisions: Record<number, 'include' | 'exclude' | 'pending'> = {};
        scopingAttributes.forEach(attr => {
          const attrId = parseInt(attr.attribute_id);
          if (attr.is_primary_key) {
            initialDecisions[attrId] = 'include';
          }
          // All other approved attributes start as 'pending' (not in the record)
          // so getScopingDecision will return 'pending' for them
        });
        setScopingDecisions(initialDecisions);
      }
      
    } catch (error) {
      console.error('Error loading attributes:', error);
      showToast.error('Failed to load attributes');
    } finally {
      setLoading(false);
    }
  };

  const loadLegacyPhaseStatus = async () => {
    try {
      const response = await apiClient.get(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/status`);
      console.log('Scoping phase status:', response.data);
      setPhaseStatus(response.data);
    } catch (error: any) {
      console.error('Error loading scoping status:', error);
      showToast.error(`Failed to load scoping status: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Add new functions for feedback and version history
  const loadFeedback = async () => {
    try {
      const response = await apiClient.get(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/feedback`);
      setFeedback(response.data);
    } catch (error: any) {
      console.error('Error loading feedback:', error);
      // Don't show error toast for feedback - it's optional
    }
  };

  const loadVersionHistory = async () => {
    try {
      const response = await apiClient.get(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/versions`);
      const versionsData = response.data.versions || [];
      setVersions(versionsData);
      
      // If there are versions, set the latest as current
      if (versionsData.length > 0 && !selectedVersion) {
        setSelectedVersion(versionsData[0].version);
      }
    } catch (error: any) {
      console.error('Error loading version history:', error);
      // Don't show error toast for version history - it's optional
    }
  };
  
  // Load versions for the dropdown
  const loadVersionsForDropdown = async () => {
    try {
      const response = await apiClient.get(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/versions`);
      const versions = response.data?.versions || response.data || [];
      setVersionList(versions);
      
      // Set the current version as selected
      if (versions.length > 0) {
        const currentVersion = versions.find((v: any) => v.is_current) || versions[0];
        setSelectedVersionId(currentVersion.version_id);
      }
    } catch (error) {
      console.error('Error loading versions for dropdown:', error);
      // Continue without versions if the endpoint doesn't exist yet
    }
  };
  
  const loadSpecificVersion = async (version: number) => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/versions/${version}`);
      const versionData = response.data;
      
      // Set viewing version
      setViewingVersion(versionData);
      
      // Update scoping decisions based on version data
      const versionDecisions: Record<number, 'include' | 'exclude'> = {};
      const versionSelected: string[] = [];
      
      Object.entries(versionData.decisions || {}).forEach(([attrId, decision]) => {
        const id = parseInt(attrId);
        versionDecisions[id] = decision as 'include' | 'exclude';
        if (decision === 'include') {
          versionSelected.push(attrId);
        }
      });
      
      setScopingDecisions(versionDecisions);
      setSelectedAttributes(versionSelected);
      
      showToast.success(`Loaded version ${version} from ${new Date(versionData.submitted_at).toLocaleDateString()}`);
    } catch (error: any) {
      console.error('Error loading version:', error);
      showToast.error('Failed to load version details');
    } finally {
      setLoading(false);
    }
  };

  // Add function to load existing scoping decisions
  const loadScopingDecisions = async () => {
    try {
      const response = await apiClient.get(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/decisions`);
      const decisionsResponse = response.data;
      // Handle both array response and object with decisions field
      const decisions = Array.isArray(decisionsResponse) ? decisionsResponse : (decisionsResponse.decisions || []);
      
      // Build scopingDecisions state from the loaded decisions
      const newScopingDecisions: Record<number, 'include' | 'exclude' | 'pending'> = {};
      const scopedAttributeIds: string[] = [];
      
      decisions.forEach((decision: any) => {
        const attrId = parseInt(decision.attribute_id);
        
        // Set the scoping decision based on final_scoping field
        if (decision.final_scoping === true) {
          newScopingDecisions[attrId] = 'include';
          scopedAttributeIds.push(decision.attribute_id.toString());
        } else if (decision.final_scoping === false) {
          newScopingDecisions[attrId] = 'exclude';
        }
        // If final_scoping is null/undefined, it remains pending (not in newScopingDecisions)
      });
      
      // Update both states
      setScopingDecisions(newScopingDecisions);
      setSelectedAttributes(scopedAttributeIds);
      
    } catch (error: any) {
      console.error('❌ Error loading scoping decisions:', error);
      console.error('❌ Error response:', error.response?.data);
      console.error('❌ Error status:', error.response?.status);
      // If no decisions exist yet, fall back to just primary keys
      throw error; // Re-throw to trigger fallback in calling function
    }
  };

  const handleStartPhase = async () => {
    try {
      setPhaseLoading(true);
      
      const startPayload = {
        planned_start_date: new Date().toISOString(),
        planned_end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days from now
        notes: 'Scoping phase started via simplified interface'
      };
      
      const response = await apiClient.post(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/start`, startPayload);
      
      setPhaseStatus(response.data);
      setShowStartDialog(false);
      showToast.success('Scoping phase started successfully');
      
      // Force reload phase status after a short delay
      setTimeout(() => {
        loadLegacyPhaseStatus();
        refetchStatus(); // Refetch unified status
      }, 1000);
      
    } catch (error: any) {
      console.error('Error starting scoping phase:', error);
      
      // Check if phase is already started
      if (error.response?.status === 400 && error.response?.data?.detail?.includes('already started')) {
        showToast.warning('Scoping phase was already started. Refreshing status...');
        
        // Force reload to get current status
        setTimeout(() => {
          loadLegacyPhaseStatus();
          refetchStatus(); // Refetch unified status
        }, 500);
        
        setShowStartDialog(false);
      } else {
        showToast.error(`Failed to start scoping phase: ${error.response?.data?.detail || error.message}`);
      }
    } finally {
      setPhaseLoading(false);
    }
  };

  const handleCompletePhase = async () => {
    try {
      setPhaseLoading(true);
      const response = await apiClient.post(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/complete`, {
        completion_notes: 'Scoping phase completed via simplified interface',
        selected_attributes: selectedAttributes
      });
      setPhaseStatus(response.data);
      setShowCompleteDialog(false);
      showToast.success('Scoping phase completed successfully');
      loadLegacyPhaseStatus(); // Reload status
      refetchStatus(); // Refetch unified status
    } catch (error) {
      console.error('Error completing phase:', error);
      showToast.error('Failed to complete scoping phase');
    } finally {
      setPhaseLoading(false);
    }
  };

  const handleGenerateRecommendations = async (forceRegenerate: boolean = false, attributeIds?: string[]) => {
    try {
      setPhaseLoading(true);
      
      const requestPayload = {
        force_regenerate: forceRegenerate,
        attribute_ids: attributeIds,
        batch_size: 6
      };
      
      const response = await apiClient.post(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/recommendations`, requestPayload);
      
      // Check if we got a job ID for background processing
      if (response.data.job_id) {
        setCurrentJobId(response.data.job_id);
        setPhaseLoading(false); // Let BatchProgressIndicator handle the loading state
      } else {
        // Fallback for immediate response (shouldn't happen with background jobs)
        showToast.success('LLM recommendations generated successfully');
        setPhaseLoading(false);
        
        // Reload phase status and attributes to show new recommendations
        setTimeout(() => {
          loadLegacyPhaseStatus();
          loadAttributes();
          refetchStatus(); // Refetch unified status
        }, 1000);
      }
      
    } catch (error: any) {
      console.error('Error generating recommendations:', error);
      showToast.error(`Failed to generate recommendations: ${error.response?.data?.detail || error.message}`);
      setPhaseLoading(false);
    }
  };

  // Function to save all scoping decisions to database (auto-save with debouncing)
  const saveAllScopingDecisions = async (updatedSelectedAttributes: string[]) => {
    // Don't auto-save in read-only mode
    if (isReadOnly()) {
      return;
    }
    
    // Clear existing timeout
    if (autoSaveTimeout) {
      clearTimeout(autoSaveTimeout);
    }

    // Set new timeout for debounced auto-save
    const timeoutId = setTimeout(async () => {
      try {
        // Create decisions for all attributes based on current selections
        const decisions = attributes.map(attr => {
          // Primary Key attributes are ALWAYS included (final_scoping: true)
          const isIncluded = attr.is_primary_key || updatedSelectedAttributes.includes(attr.attribute_id.toString());
          
          return {
            attribute_id: attr.attribute_id,
            decision: isIncluded ? 'Accept' : 'Decline',
            final_scoping: isIncluded,
            tester_rationale: isIncluded
              ? (attr.is_primary_key 
                  ? 'Primary Key attribute - automatically included for testing'
                  : 'Selected for testing based on risk assessment and recommendations')
              : 'Not selected for testing - lower priority for current scope',
            override_reason: null
          };
        });

        const submissionPayload = {
          decisions: decisions,
          confirm_submission: false, // Auto-save, not submitting for approval
          submission_notes: 'Auto-saved scoping decisions'
        };

        // Note: Individual decisions are already saved in handleScopingDecision
        // This auto-save was trying to use a non-existent endpoint
        // Just reload the status to reflect saved changes
        loadLegacyPhaseStatus();
        refetchStatus(); // Refetch unified status
        
      } catch (error: any) {
        console.error('Error auto-saving scoping decisions:', error);
        // Don't show error toast for auto-save failures to avoid annoying the user
        console.warn('Auto-save failed, decisions will be saved on manual submission');
      }
    }, 1000); // 1 second debounce

    setAutoSaveTimeout(timeoutId);
  };

  const handleAttributeToggle = async (attributeId: string) => {
    // Check if it's a PK attribute (cannot be deselected)
    const attribute = attributes.find(attr => attr.attribute_id.toString() === attributeId.toString());
    if (attribute?.is_primary_key) {
      showToast.warning('Primary key attributes cannot be removed from scoping');
      return;
    }

    // Check if attribute is approved for testing
    if (attribute?.approval_status !== 'approved') {
      showToast.warning('Only approved attributes can be selected for testing');
      return;
    }

    const attributeIdStr = attributeId.toString();

    // Update UI state immediately for responsiveness
    const updatedSelectedAttributes = selectedAttributes.includes(attributeIdStr)
      ? selectedAttributes.filter(id => id !== attributeIdStr)
      : [...selectedAttributes, attributeIdStr];

    setSelectedAttributes(updatedSelectedAttributes);

    // Save to database in background
    await saveAllScopingDecisions(updatedSelectedAttributes);
  };


  const handleShowLLMAnalysis = (attribute: AttributeForScoping) => {
    setSelectedAttributeForAnalysis(attribute);
    setShowLLMAnalysisDialog(true);
  };
  
  // Filter attributes based on search and filter criteria
  const getFilteredAttributes = () => {
    return attributes.filter(attr => {
      // Search filter
      if (searchTerm && !attr.attribute_name.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      
      // Tester decision filter
      if (filterTesterDecision !== 'all') {
        const decision = attr.tester_decision || (getScopingDecision(attr.attribute_id));
        if (!decision && filterTesterDecision !== 'pending') return false;
        if (decision === 'accept' && filterTesterDecision !== 'approved') return false;
        if (decision === 'decline' && filterTesterDecision !== 'rejected') return false;
        if (!decision && filterTesterDecision === 'pending') return true;
      }
      
      // Report owner decision filter
      if (filterReportOwnerDecision !== 'all') {
        if (!attr.report_owner_decision && filterReportOwnerDecision !== 'pending') return false;
        if (attr.report_owner_decision === 'approved' && filterReportOwnerDecision !== 'approved') return false;
        if (attr.report_owner_decision === 'rejected' && filterReportOwnerDecision !== 'rejected') return false;
        if (attr.report_owner_decision === 'needs_revision' && filterReportOwnerDecision !== 'needs_revision') return false;
      }
      
      // Status filter
      if (filterStatus !== 'all' && attr.status !== filterStatus) {
        return false;
      }
      
      return true;
    });
  };

  // Fixed functions - removing duplicates
  const handleBulkActionFix = async (action: 'include' | 'exclude') => {
    try {
      setPhaseLoading(true);
      
      const endpoint = action === 'include' 
        ? '/scoping/attributes/bulk-approve'
        : '/scoping/attributes/bulk-reject';
      
      const payload = {
        attribute_ids: bulkSelectedAttributes,
        notes: action === 'include' 
          ? 'Bulk approved for testing'
          : 'Bulk excluded from testing'
      };
      
      await apiClient.post(endpoint, payload);
      
      showToast.success(`${bulkSelectedAttributes.length} attributes ${action === 'include' ? 'approved' : 'rejected'} successfully`);
      
      // Clear bulk selection after action
      setBulkSelectedAttributes([]);
      
      // Reload attributes to reflect changes
      await loadAttributes();
      
    } catch (error: any) {
      console.error('Error performing bulk action:', error);
      showToast.error(`Failed to ${action} attributes: ${error.response?.data?.detail || error.message}`);
    } finally {
      setPhaseLoading(false);
    }
  };

  const handleActivityAction = async (activity: any, action: string) => {
    try {
      // Special handling for regenerate action
      if (action === 'regenerate' && activity.name === 'Generate LLM Recommendations') {
        // Always show the dialog to let user choose incremental vs full regeneration
        setShowRegenerateDialog(true);
        return;
      }
      
      // Regular activity handling
      const endpoint = action === 'start' ? 'start' : 'complete';
      const response = await apiClient.post(`/activity-management/activities/${activity.activity_id}/${endpoint}`, {
        cycle_id: cycleIdNum,
        report_id: reportIdNum,
        phase_name: 'Scoping'
      });
      
      // Show success message from backend or default
      const message = response.data.message || activity.metadata?.success_message || `${action === 'start' ? 'Started' : 'Completed'} ${activity.name}`;
      showToast.success(message);
      
      // Note: phase_start activities are automatically completed by the backend
      // when started, so no need to manually complete them
      
      // Add a small delay to ensure backend has processed the change
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Force refresh of both status systems
      await refetchStatus();
      // Reload scoping decisions if needed
      await loadScopingDecisions();
    } catch (error: any) {
      console.error('Error handling activity action:', error);
      showToast.error(error.response?.data?.detail || `Failed to ${action} activity`);
    }
  };

  const handleSubmitDecisions = async () => {
    try {
      setPhaseLoading(true);
      
      // Create scoping decisions based on selected attributes
      const decisions = attributes.map(attr => {
        // Primary Key attributes are ALWAYS included (final_scoping: true)
        const isIncluded = attr.is_primary_key || selectedAttributes.includes(attr.attribute_id.toString());
        
        return {
          attribute_id: attr.attribute_id,
          decision: isIncluded ? 'Accept' : 'Decline',
          final_scoping: isIncluded,
          tester_rationale: isIncluded
            ? (attr.is_primary_key 
                ? 'Primary Key attribute - automatically included for testing'
                : 'Selected for testing based on risk assessment and recommendations')
            : 'Not selected for testing - lower priority for current scope',
          override_reason: null
        };
      });

      // Determine if this is a revision
      const isRevision = feedback?.can_resubmit;
      const nextVersion = (feedback?.submission_version || 0) + 1;
      
      const submissionPayload = {
        decisions: decisions,
        confirm_submission: true,
        submission_notes: isRevision 
          ? `Scoping decisions revised (v${nextVersion}) based on Report Owner feedback. ${selectedAttributes.length} out of ${attributes.length} attributes selected for testing.`
          : `Scoping decisions submitted for ${selectedAttributes.length} out of ${attributes.length} attributes selected for testing.`
      };

      const response = await apiClient.post(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/scoping-submission`, submissionPayload);
      
      const successMessage = response.data.is_revision 
        ? `Scoping decisions resubmitted successfully (v${response.data.version})! ${selectedAttributes.length} attributes selected for testing.`
        : `Scoping decisions submitted successfully! ${selectedAttributes.length} attributes selected for testing.`;
      
      showToast.success(successMessage);
      
      // Create Universal Assignment for submission review
      console.log('Creating Universal Assignment for Scoping submission:', {
        cycleId: cycleIdNum,
        reportId: reportIdNum,
        phase: 'Scoping',
        userId: user?.user_id || 0,
        userRole: user?.role || '',
      });
      
      try {
        await workflowHooks.onSubmitForApproval('Scoping', {
          cycleId: cycleIdNum,
          reportId: reportIdNum,
          phase: 'Scoping',
          userId: user?.user_id || 0,
          userRole: user?.role || '',
          additionalData: {
            selectedAttributesCount: selectedAttributes.length,
            totalAttributesCount: attributes.length,
            isRevision: response.data.is_revision,
            version: response.data.version
          }
        });
        console.log('Universal Assignment created successfully');
      } catch (assignmentError) {
        console.error('Failed to create Universal Assignment:', assignmentError);
        // Don't fail the whole submission, just log the error
        showToast.error('Warning: Report Owner assignment could not be created. Please contact support.');
      }
      
      // Small delay to ensure backend has fully processed
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Reload status and feedback to reflect submission
      await Promise.all([
        loadLegacyPhaseStatus(),
        loadFeedback(),
        loadVersionHistory()
      ]);
      refetchStatus(); // Refetch unified status after legacy call
      
      // Force a re-render to update the workflow cards
      setPhaseLoading(false);
      setPhaseLoading(true);
      setTimeout(() => setPhaseLoading(false), 100);
      
    } catch (error: any) {
      console.error('Error submitting scoping decisions:', error);
      showToast.error(`Failed to submit scoping decisions: ${error.response?.data?.detail || error.message}`);
    } finally {
      setPhaseLoading(false);
    }
  };

  const handleMakeDecisions = () => {
    // Scroll to attributes table and highlight selection controls
    const attributesTable = document.querySelector('[data-testid="attributes-table"]');
    if (attributesTable) {
      attributesTable.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    showToast.warning('Please review the recommendations and select attributes for testing, then submit your decisions.');
  };

  const getRiskColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score < 30) return 'success';
    if (score < 70) return 'warning';
    return 'error';
  };

  const getRiskLabel = (score: number): string => {
    if (score < 30) return 'Low';
    if (score < 70) return 'Medium';
    return 'High';
  };

  // Helper function to check if submission requirements are met
  const canSubmitToReportOwner = (): { canSubmit: boolean; reason?: string } => {
    // Count non-PK attributes that are selected
    const nonPkSelectedCount = selectedAttributes.filter(id => {
      const attr = attributes.find(a => a.attribute_id.toString() === id);
      return attr && !attr.is_primary_key;
    }).length;

    if (nonPkSelectedCount === 0) {
      return {
        canSubmit: false,
        reason: "At least 1 Non-Primary Key attribute must be selected for testing"
      };
    }

    return { canSubmit: true };
  };


  // Early return if redirecting
  // @ts-ignore - Role comes from backend as string "Report Owner"
  if (user?.role === 'Report Owner') {
    return <LinearProgress />;
  }

  if (loading) {
    return (
      <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
        <Typography variant="h4" gutterBottom>Loading Scoping Phase...</Typography>
        <LinearProgress />
      </Container>
    );
  }

  // Add error boundary for debugging
  if (!cycleIdNum || !reportIdNum) {
    return (
      <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
        <Alert severity="error">
          <Typography variant="h6">Invalid Parameters</Typography>
          <Typography>
            CycleId: {cycleId} (parsed: {cycleIdNum})<br/>
            ReportId: {reportId} (parsed: {reportIdNum})
          </Typography>
          <Typography>
            Please check the URL format: /cycles/:cycleId/reports/:reportId/scoping
          </Typography>
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
      
      {/* Universal Assignment Alert */}
      {hasAssignment && assignment && (
        <UniversalAssignmentAlert
          assignment={assignment}
          onAcknowledge={(id) => acknowledgeMutation.mutate(id)}
          onStart={(id) => startMutation.mutate(id)}
          onComplete={(id) => completeMutation.mutate({ assignmentId: id })}
          showActions={true}
        />
      )}

      {/* Report Owner Feedback Checker - Hidden component */}
      <ReportOwnerScopingFeedbackChecker
        cycleId={cycleIdNum}
        reportId={reportIdNum}
        versionId={selectedVersionId}
        onFeedbackStatusChange={setHasReportOwnerFeedback}
      />

      {/* Report Metadata Section - Same as Planning Page */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            {/* Left side - Report title and phase info */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <AssignmentIcon color="primary" fontSize="large" />
              <Box>
                <Typography variant="h5" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportInfo?.report_name || 'Loading...'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {reportInfo?.cycle_name || `Cycle ${cycleIdNum}`} • Scoping Phase - {reportInfo?.description || 'Defining attributes for testing scope'}
                </Typography>
              </Box>
            </Box>
            
            {/* Right side - Key metadata */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
              {reportInfoLoading ? (
                <Box sx={{ width: 200 }}>
                  <LinearProgress />
                </Box>
              ) : (
                <>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BusinessIcon color="action" fontSize="small" />
                    <Typography variant="body2" color="text.secondary">LOB:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {reportInfo?.lob || 'Unknown'}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PersonIcon color="action" fontSize="small" />
                    <Typography variant="body2" color="text.secondary">Tester:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {reportInfo?.assigned_tester || 'Not assigned'}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PersonIcon color="action" fontSize="small" />
                    <Typography variant="body2" color="text.secondary">Owner:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {reportInfo?.report_owner || 'Not specified'}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" color="text.secondary">Cycle:</Typography>
                    <Typography variant="body2" fontWeight="medium" fontFamily="monospace">
                      {reportInfo?.cycle_id || cycleIdNum}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" color="text.secondary">Report:</Typography>
                    <Typography variant="body2" fontWeight="medium" fontFamily="monospace">
                      {reportInfo?.report_id || reportIdNum}
                    </Typography>
                  </Box>
                </>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>


      {/* Scoping Metrics Row 1 - Six Key Metrics */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 3 }}>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(16.66% - 20px)' } }}>
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
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(16.66% - 20px)' } }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="success.main" fontWeight="bold">
                {phaseStatus?.attributes_scoped_for_testing || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Scoped Attributes
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                ({Math.max(0, (phaseStatus?.attributes_scoped_for_testing || 0) - (phaseStatus?.pk_attributes_count || 0))} Non-PK + {phaseStatus?.pk_attributes_count || 0} PK)
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(16.66% - 20px)' } }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="info.main" fontWeight="bold">
                {phaseStatus?.cde_attributes_count || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                CDEs
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(16.66% - 20px)' } }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="error.main" fontWeight="bold">
                {phaseStatus?.historical_issues_count || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Historical Issues
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(16.66% - 20px)' } }}>
          <Card sx={{ textAlign: 'center', height: '100%' }}>
            <CardContent>
              <Typography variant="h4" color="warning.main" fontWeight="bold">
                {phaseStatus?.attributes_with_anomalies || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Attributes with Anomalies
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(16.66% - 20px)' } }}>
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
        </Box>
      </Box>

      {/* Row 2: On-Time Status + Phase Controls */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
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
        </Box>
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
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
                    'To complete: Start phase → Make scoping decisions → Submit for approval'
                  ) : phaseStatus.phase_status === 'Complete' ? (
                    'Phase completed successfully - all requirements met'
                  ) : phaseStatus.can_complete ? (
                    'Ready to complete - all requirements met'
                  ) : (
                    `To complete: ${phaseStatus.completion_requirements?.join(', ') || 'Make scoping decisions for attributes'}`
                  )}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>


      {/* Scoping Workflow Visual */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssignmentIcon color="primary" />
            Scoping Phase Workflow
          </Typography>
          
          <Box sx={{ mt: 2 }}>
            {unifiedPhaseStatus?.activities ? (
              <DynamicActivityCards
                activities={unifiedPhaseStatus.activities}
                cycleId={cycleIdNum}
                reportId={reportIdNum}
                phaseName="Scoping"
                onActivityAction={handleActivityAction}
                phaseStatus={unifiedPhaseStatus.phase_status}
                overallCompletion={unifiedPhaseStatus.overall_completion_percentage}
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
                    Loading scoping activities...
                  </Typography>
                </Box>
              )}
          </Box>
        </CardContent>
      </Card>

      {/* LLM Job Progress Display */}
      {currentJobId && (
        <Box sx={{ mb: 3 }}>
          <BatchProgressIndicator
            jobId={currentJobId}
            title="Generating LLM recommendations..."
            onComplete={() => {
              setCurrentJobId(null);
              loadLegacyPhaseStatus();
              loadAttributes();
              refetchStatus();
            }}
            onError={() => {
              setCurrentJobId(null);
              setPhaseLoading(false);
            }}
            showDetails
          />
        </Box>
      )}

      {/* Report Owner Information Card */}
      {/* @ts-ignore - Role comes from backend as string "Report Owner" */}
      {user?.role === 'Report Owner' && phaseStatus?.submission_status === 'Submitted' && (
        <Card sx={{ mb: 3, bgcolor: 'info.50', border: 2, borderColor: 'info.main' }}>
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <Typography variant="h6" gutterBottom color="info.main">
              Scoping Decisions Submitted for Review
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
              The tester has submitted scoping decisions for your approval. You can review and approve/decline the scoping recommendations.
            </Typography>
            <Button
              variant="contained"
              color="info"
              size="large"
              onClick={() => navigate(`/cycles/${cycleId}/reports/${reportId}/scoping-review`)}
              sx={{ px: 4, py: 1.5 }}
            >
              Review Scoping Decisions
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Report Owner Review Notice for Testers */}
      {user?.role === 'Tester' && feedback?.feedback_id && (
        <Card sx={{ mb: 3, bgcolor: feedback.needs_revision ? 'warning.light' : feedback.review_decision === 'Approved' ? 'success.light' : 'error.light', border: 2, borderColor: feedback.needs_revision ? 'warning.main' : feedback.review_decision === 'Approved' ? 'success.main' : 'error.main' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {feedback.review_decision === 'Approved' && <CheckCircle color="success" />}
                  {feedback.review_decision === 'Declined' && <Cancel color="error" />}
                  {feedback.review_decision === 'Needs Revision' && <Edit color="warning" />}
                  Report Owner Feedback
                  {feedback.is_outdated_feedback && (
                    <Chip 
                      size="small" 
                      label={`Feedback for v${feedback.submission_version}`} 
                      color="info" 
                      variant="outlined"
                    />
                  )}
                </Typography>
                
                {feedback.is_outdated_feedback && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Note:</strong> This feedback is for version {feedback.submission_version}. You have submitted a newer version which is pending review.
                    </Typography>
                  </Alert>
                )}
                
                <Typography variant="body1" fontWeight="medium" gutterBottom component="div">
                  Status: <Chip 
                    label={feedback.review_decision} 
                    color={feedback.review_decision === 'Approved' ? 'success' : feedback.review_decision === 'Declined' ? 'error' : 'warning'}
                    variant="filled"
                  />
                </Typography>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Reviewed by {feedback.provided_by} on {new Date(feedback.provided_at).toLocaleDateString()}
                </Typography>
                
                {feedback.feedback_text && (
                  <Alert severity={feedback.needs_revision ? 'warning' : feedback.review_decision === 'Approved' ? 'success' : 'error'} sx={{ mb: 2 }}>
                    <Typography variant="body2" fontWeight="medium" gutterBottom>
                      Review Comments:
                    </Typography>
                    <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                      "{feedback.feedback_text}"
                    </Typography>
                  </Alert>
                )}
                
                {feedback.requested_changes && Object.keys(feedback.requested_changes).length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" fontWeight="medium" gutterBottom>
                      Requested Changes:
                    </Typography>
                    <Box component="ul" sx={{ mt: 1, pl: 2 }}>
                      {Object.entries(feedback.requested_changes).map(([key, value], index) => (
                        <Box component="li" key={index} sx={{ mb: 1 }}>
                          <Typography variant="body2">
                            {`${key}: ${value}`}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </Box>
                )}
                
                {/* Action required notice */}
                {feedback.needs_revision && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    <Typography variant="body2" fontWeight="medium">
                      Action Required:
                    </Typography>
                    <Typography variant="body2">
                      Please review the feedback above and make the necessary changes to your scoping decisions. 
                      Once you have addressed the feedback, click "Resubmit Scoping Decisions" below.
                    </Typography>
                  </Alert>
                )}
              </Box>
              
              {/* Action Buttons */}
              <Box sx={{ ml: 3, display: 'flex', flexDirection: 'column', gap: 1 }}>
                {feedback.can_resubmit && (
                  <Button
                    variant="contained"
                    color="warning"
                    size="small"
                    onClick={() => {
                      // Switch to Scoping Decisions tab
                      // When report owner feedback exists, Scoping Decisions is tab 1
                      setActiveTab(1);
                      // After a short delay, scroll to the attributes table
                      setTimeout(() => {
                        const element = document.getElementById('attributes-table');
                        if (element) {
                          element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                      }, 100);
                    }}
                    sx={{ minWidth: 120 }}
                  >
                    Make Changes
                  </Button>
                )}
                
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setShowVersionHistory(true)}
                  sx={{ minWidth: 120 }}
                >
                  View History
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Scoping Approved - Ready to Complete */}
      {user?.role === 'Tester' && feedback?.review_decision === 'Approved' && phaseStatus?.phase_status !== 'Complete' && (
        <Card sx={{ mb: 3, bgcolor: 'success.50', border: 2, borderColor: 'success.main' }}>
          <CardContent sx={{ textAlign: 'center', py: 3 }}>
            <Typography variant="h6" gutterBottom color="success.main" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
              <CheckCircle color="success" />
              Scoping Approved - Ready to Complete
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
              The Report Owner has approved your scoping decisions. You can now complete the scoping phase to proceed to the next phase.
            </Typography>
            <Button
              variant="contained"
              color="success"
              size="large"
              onClick={() => setShowCompleteDialog(true)}
              disabled={phaseLoading}
              sx={{ px: 4, py: 1.5 }}
            >
              Complete Scoping Phase
            </Button>
          </CardContent>
        </Card>
      )}


      {/* Scoping Content with Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(_, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          {hasReportOwnerFeedback && <Tab label="Report Owner Feedback" />}
          <Tab label="Scoping Decisions" />
          <Tab label="Documents" />
        </Tabs>
        
        {/* Report Owner Feedback Tab */}
        {hasReportOwnerFeedback && activeTab === 0 && (
          <ReportOwnerScopingFeedback
            cycleId={cycleIdNum}
            reportId={reportIdNum}
            versionId={selectedVersionId}
          />
        )}
        
        {/* Scoping Decisions Tab */}
        {((hasReportOwnerFeedback && activeTab === 1) || (!hasReportOwnerFeedback && activeTab === 0)) && (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Report Attributes for Scoping ({getFilteredAttributes().length} of {attributes.length})
            </Typography>
          
          {/* Show alert when revision is needed */}
          {feedback?.needs_revision && !isReadOnly() && (
            <Alert 
              severity="warning" 
              sx={{ mb: 2 }}
              action={
                <Button 
                  color="inherit" 
                  size="small"
                  startIcon={<SendIcon />}
                  onClick={handleSubmitDecisions}
                  disabled={!canSubmitToReportOwner().canSubmit}
                >
                  Resubmit Decisions
                </Button>
              }
            >
              <AlertTitle>Revision Required</AlertTitle>
              The Report Owner has requested changes to your scoping decisions. Please review their feedback above and make the necessary adjustments below.
            </Alert>
          )}
          
          {/* Filter Controls Section - matching data profiling style */}
          <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
              {/* Version Dropdown */}
              <Box sx={{ minWidth: 150 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Version</InputLabel>
                  <Select
                    value={selectedVersionId}
                    onChange={(e) => {
                      setSelectedVersionId(e.target.value);
                      // Load specific version when changed
                      if (e.target.value) {
                        const version = versionList.find(v => v.version_id === e.target.value);
                        if (version) {
                          loadSpecificVersion(version.version_number);
                        }
                      }
                    }}
                    label="Version"
                  >
                    {Array.isArray(versionList) && versionList.map((version) => (
                      <MenuItem key={version.version_id} value={version.version_id}>
                        v{version.version_number} {version.is_current && '(Current)'}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
              <Tooltip title="View version history">
                <IconButton 
                  size="small"
                  onClick={() => setShowVersionHistory(true)}
                  color="primary"
                >
                  <HistoryIcon />
                </IconButton>
              </Tooltip>
              
              {/* Search Field */}
              <Box sx={{ flexGrow: 1, minWidth: 200 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Search attributes..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
              </Box>
              
              {/* Tester Decision Filter */}
              <Box sx={{ minWidth: 150 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Tester Decision</InputLabel>
                  <Select
                    value={filterTesterDecision}
                    onChange={(e) => setFilterTesterDecision(e.target.value)}
                    label="Tester Decision"
                  >
                    <MenuItem value="all">All</MenuItem>
                    <MenuItem value="pending">Pending</MenuItem>
                    <MenuItem value="approved">Approved</MenuItem>
                    <MenuItem value="rejected">Rejected</MenuItem>
                  </Select>
                </FormControl>
              </Box>
              
              {/* Report Owner Decision Filter */}
              <Box sx={{ minWidth: 150 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>RO Decision</InputLabel>
                  <Select
                    value={filterReportOwnerDecision}
                    onChange={(e) => setFilterReportOwnerDecision(e.target.value)}
                    label="RO Decision"
                  >
                    <MenuItem value="all">All</MenuItem>
                    <MenuItem value="pending">Pending</MenuItem>
                    <MenuItem value="approved">Approved</MenuItem>
                    <MenuItem value="rejected">Rejected</MenuItem>
                    <MenuItem value="needs_revision">Needs Revision</MenuItem>
                  </Select>
                </FormControl>
              </Box>
              
              {/* Status Filter */}
              <Box sx={{ minWidth: 120 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    label="Status"
                  >
                    <MenuItem value="all">All</MenuItem>
                    <MenuItem value="pending">Pending</MenuItem>
                    <MenuItem value="submitted">Submitted</MenuItem>
                    <MenuItem value="approved">Approved</MenuItem>
                    <MenuItem value="rejected">Rejected</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </Box>
          </Box>

          <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            {/* Bulk Action Buttons */}
            <Button
              variant="contained"
              color="success"
              startIcon={<CheckCircleIcon />}
              onClick={() => {
                handleBulkAction('include');
                showToast.success(`Successfully included ${bulkSelectedAttributes.length} attributes for testing`);
              }}
              disabled={bulkSelectedAttributes.length === 0 || isReadOnly()}
            >
              Bulk Include ({bulkSelectedAttributes.length})
            </Button>
            
            <Button
              variant="contained"
              color="error"
              startIcon={<Cancel />}
              onClick={() => {
                handleBulkAction('exclude');
                showToast.success(`Successfully excluded ${bulkSelectedAttributes.length} attributes from testing`);
              }}
              disabled={bulkSelectedAttributes.length === 0 || isReadOnly()}
            >
              Bulk Exclude ({bulkSelectedAttributes.length})
            </Button>
            
            
            <Box sx={{ flexGrow: 1 }} />
            
            {/* Submit/Resubmit Button */}
            {!isReadOnly() && (
              <Tooltip 
                title={getDecisionCounts.pending > 0 
                  ? `Cannot submit: ${getDecisionCounts.pending} attributes still need decisions (Include/Exclude)` 
                  : ''}
                arrow
              >
                <span>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<SendIcon />}
                    onClick={() => setSubmissionDialogOpen(true)}
                    disabled={getDecisionCounts.pending > 0}
                  >
                    {(phaseStatus?.needs_revision || feedback?.needs_revision) ? 'Resubmit Scoping Decisions' : 'Submit Scoping Decisions'}
                  </Button>
                </span>
              </Tooltip>
            )}
          </Box>
          
          {feedback?.needs_revision ? (
            <Alert severity="warning" sx={{ mb: 3 }}>
              <AlertTitle>Revision Required</AlertTitle>
              <Typography variant="body2" sx={{ mb: 1 }}>
                The Report Owner has provided feedback on your scoping decisions. Please review their comments above and make the necessary adjustments.
              </Typography>
              <Typography variant="body2">
                You can now edit your attribute selections below. Decisions are auto-saved as you make changes.
              </Typography>
            </Alert>
          ) : (
            <Alert severity="info" sx={{ mb: 3 }}>
              <strong>Scoping Instructions:</strong> 
              Review LLM recommendations and make Include/Exclude decisions for each attribute. 
              Primary Key attributes are automatically included and cannot be changed. 
              Decisions are auto-saved as you make selections.
            </Alert>
          )}
          

          
          {loading ? (
            <LinearProgress />
          ) : (
            (() => {
              return (
                <TableContainer component={Paper} id="attributes-table" sx={{ overflowX: 'auto' }}>
                  <Table data-testid="attributes-table" sx={{ width: '100%' }}>
                    <TableHead>
                      <TableRow>
                        <TableCell padding="checkbox">
                          <Checkbox
                            checked={(() => {
                              const selectableAttributes = attributes.filter(attr => 
                                !attr.is_primary_key
                              );
                              return selectableAttributes.length > 0 && bulkSelectedAttributes.length === selectableAttributes.length;
                            })()}
                            indeterminate={(() => {
                              const selectableAttributes = attributes.filter(attr => 
                                !attr.is_primary_key
                              );
                              return bulkSelectedAttributes.length > 0 && bulkSelectedAttributes.length < selectableAttributes.length;
                            })()}
                            disabled={isReadOnly()}
                            onChange={(e) => {
                              if (e.target.checked) {
                                // Select all non-PK attributes for bulk operations
                                setBulkSelectedAttributes(attributes
                                  .filter(attr => !attr.is_primary_key)
                                  .map(attr => attr.attribute_id.toString()));
                              } else {
                                // Clear bulk selection
                                setBulkSelectedAttributes([]);
                              }
                            }}
                          />
                        </TableCell>
                        <TableCell sx={{ width: '5%', minWidth: 60 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Line #</Typography>
                        </TableCell>
                        <TableCell sx={{ width: '15%', minWidth: 150 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Attribute Name</Typography>
                        </TableCell>
                        <TableCell sx={{ width: '5%', minWidth: 50 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>MDRM</Typography>
                        </TableCell>
                        <TableCell sx={{ width: '10%', minWidth: 100 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Description</Typography>
                        </TableCell>
                        <TableCell sx={{ width: '7%', minWidth: 80 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Data Type</Typography>
                        </TableCell>
                        <TableCell sx={{ width: '5%', minWidth: 60, textAlign: 'center' }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Risk</Typography>
                        </TableCell>
                        <TableCell sx={{ width: '18%', minWidth: 180 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>LLM Rationale</Typography>
                        </TableCell>
                        <TableCell sx={{ width: '5%', minWidth: 60, textAlign: 'center' }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>DQ</Typography>
                        </TableCell>
                        <TableCell sx={{ width: '8%', minWidth: 80 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Status</Typography>
                        </TableCell>
                        <TableCell sx={{ width: '10%', minWidth: 120 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Tester Decision</Typography>
                        </TableCell>
                        <TableCell sx={{ width: '10%', minWidth: 120 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Report Owner</Typography>
                        </TableCell>
                        <TableCell sx={{ width: '7%', minWidth: 80, textAlign: 'center' }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Actions</Typography>
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {getFilteredAttributes().map((attr, index) => (
                        <TableRow key={attr.attribute_id}>
                          <TableCell padding="checkbox">
                            <Checkbox
                              checked={bulkSelectedAttributes.includes(attr.attribute_id.toString())}
                              disabled={attr.is_primary_key || isReadOnly()} // PK attributes cannot be bulk selected
                              onChange={() => {
                                const attributeId = attr.attribute_id.toString();
                                if (bulkSelectedAttributes.includes(attributeId)) {
                                  setBulkSelectedAttributes(bulkSelectedAttributes.filter(id => id !== attributeId));
                                } else {
                                  setBulkSelectedAttributes([...bulkSelectedAttributes, attributeId]);
                                }
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {index + 1}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {attr.attribute_name || 'N/A'}
                            </Typography>
                            {/* Interactive badges under attribute name */}
                            <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                              {(attr.is_cde || attr.cde_flag) && (
                                <Chip 
                                  size="small" 
                                  label="CDE" 
                                  color="warning"
                                  variant="filled"
                                  sx={{ fontSize: '0.65rem', height: '20px', minWidth: '45px' }}
                                />
                              )}
                              {attr.historical_issues_flag && (
                                <Chip 
                                  size="small" 
                                  label="Issues" 
                                  color="error"
                                  variant="filled"
                                  sx={{ fontSize: '0.65rem', height: '20px', minWidth: '50px' }}
                                />
                              )}
                              {attr.is_primary_key && (
                                <Chip 
                                  size="small" 
                                  label="Key" 
                                  color="info"
                                  variant="filled"
                                  icon={<KeyIcon />}
                                  sx={{ fontSize: '0.65rem', height: '20px', minWidth: '45px' }}
                                />
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography 
                              variant="body2"
                              sx={{ 
                                fontFamily: 'monospace',
                                fontWeight: 'bold'
                              }}
                            >
                              {attr.mdrm || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Tooltip title={attr.description || 'N/A'} arrow>
                              <Typography 
                                variant="body2"
                                sx={{ 
                                  fontSize: '0.875rem',
                                  whiteSpace: 'nowrap',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  maxWidth: '150px'
                                }}
                              >
                                {attr.description || 'N/A'}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {attr.data_type || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell sx={{ textAlign: 'center' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                              <Tooltip
                                title={
                                  <Box sx={{ p: 1 }}>
                                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                      Risk Score Breakdown
                                    </Typography>
                                    <Typography variant="body2" gutterBottom>
                                      <strong>Risk Score:</strong> {Math.round(attr.llm_risk_score || 0)}/100
                                    </Typography>
                                    <Typography variant="body2" gutterBottom>
                                      <strong>Confidence:</strong> {((attr.llm_confidence_score || 0) * 100).toFixed(0)}%
                                    </Typography>
                                    {attr.llm_rationale && (
                                      <Box sx={{ mt: 1 }}>
                                        <Typography variant="body2" component="div">
                                          {attr.llm_rationale.split('\n').map((line, idx) => (
                                            <React.Fragment key={idx}>
                                              {idx > 0 && <br />}
                                              {line.split(/(\*\*[^*]+\*\*)/).map((part, pidx) => {
                                                if (part.startsWith('**') && part.endsWith('**')) {
                                                  return <strong key={pidx}>{part.slice(2, -2)}:</strong>;
                                                }
                                                return part;
                                              })}
                                            </React.Fragment>
                                          ))}
                                        </Typography>
                                      </Box>
                                    )}
                                    {false && (
                                      <Box sx={{ mt: 1 }}>
                                        <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                          {''}
                                        </Typography>
                                      </Box>
                                    )}
                                    {false && (
                                      <Typography variant="body2" gutterBottom>
                                        <strong>Description:</strong> {''}
                                      </Typography>
                                    )}
                                    {attr.typical_source_documents && (
                                      <Typography variant="body2" gutterBottom>
                                        <strong>Source Documents:</strong> {attr.typical_source_documents}
                                      </Typography>
                                    )}
                                    {attr.keywords_to_look_for && (
                                      <Typography variant="body2" gutterBottom>
                                        <strong>Keywords:</strong> {attr.keywords_to_look_for}
                                      </Typography>
                                    )}
                                    {attr.validation_rules && (
                                      <Typography variant="body2" gutterBottom>
                                        <strong>Validation Rules:</strong> {attr.validation_rules}
                                      </Typography>
                                    )}
                                    {attr.testing_approach && (
                                      <Typography variant="body2" gutterBottom>
                                        <strong>Testing Approach:</strong> {attr.testing_approach}
                                      </Typography>
                                    )}
                                    {!attr.llm_risk_score && (
                                      <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                        No LLM analysis available for this attribute
                                      </Typography>
                                    )}
                                  </Box>
                                }
                                arrow
                                placement="top"
                                componentsProps={{
                                  tooltip: {
                                    sx: { 
                                      bgcolor: 'grey.900', 
                                      maxWidth: 400,
                                      fontSize: '0.875rem'
                                    }
                                  }
                                }}
                              >
                                <Chip
                                  size="small"
                                  label={`${Math.round(attr.llm_risk_score || 0)}`}
                                  color={getRiskColor(attr.llm_risk_score || 0)}
                                  variant="filled"
                                  sx={{ cursor: 'help' }}
                                />
                              </Tooltip>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Tooltip 
                              title={attr.llm_rationale || 'N/A'} 
                              arrow 
                              placement="top"
                              componentsProps={{
                                tooltip: {
                                  sx: { 
                                    maxWidth: 500,
                                    whiteSpace: 'pre-wrap'
                                  }
                                }
                              }}
                            >
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  wordBreak: 'break-word', 
                                  whiteSpace: 'normal',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  display: '-webkit-box',
                                  WebkitLineClamp: 3,
                                  WebkitBoxOrient: 'vertical',
                                  cursor: 'help',
                                color: (() => {
                                  const rationale = attr.llm_rationale;
                                  if (!rationale || 
                                      rationale.toLowerCase().includes('local') ||
                                      rationale.toLowerCase().includes('unavailable') ||
                                      rationale.toLowerCase().includes('fallback') ||
                                      rationale === 'No rationale available') {
                                    return 'text.secondary';
                                  }
                                  return 'text.primary';
                                })(),
                                fontStyle: (() => {
                                  const rationale = attr.llm_rationale;
                                  if (!rationale || 
                                      rationale.toLowerCase().includes('local') ||
                                      rationale.toLowerCase().includes('unavailable') ||
                                      rationale.toLowerCase().includes('fallback') ||
                                      rationale === 'No rationale available') {
                                    return 'italic';
                                  }
                                  return 'normal';
                                })()
                              }}
                            >
                              {(() => {
                                const rationale = attr.llm_rationale;
                                if (!rationale || 
                                    rationale.toLowerCase().includes('local') ||
                                    rationale.toLowerCase().includes('unavailable') ||
                                    rationale.toLowerCase().includes('fallback') ||
                                    rationale === 'No rationale available') {
                                  return 'N/A';
                                }
                                // Parse markdown-style bold text and newlines
                                return rationale.split('\n').map((line, idx) => (
                                  <React.Fragment key={idx}>
                                    {idx > 0 && <br />}
                                    {line.split(/(\*\*[^*]+\*\*)/).map((part, pidx) => {
                                      if (part.startsWith('**') && part.endsWith('**')) {
                                        return <strong key={pidx}>{part.slice(2, -2)}</strong>;
                                      }
                                      return part;
                                    })}
                                  </React.Fragment>
                                ));
                              })()}
                            </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell sx={{ textAlign: 'center' }}>
                            {attr.has_profiling_data ? (
                              <Tooltip title="Click to view detailed DQ results" arrow>
                                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                                  <Chip
                                  size="small"
                                  label={`${attr.composite_dq_score?.toFixed(1) || '0.0'}%`}
                                  color={
                                    (attr.composite_dq_score || 0) >= 90 ? 'success' :
                                    (attr.composite_dq_score || 0) >= 70 ? 'warning' : 'error'
                                  }
                                  variant="filled"
                                  sx={{ 
                                    fontSize: '0.75rem', 
                                    fontWeight: 'bold',
                                    cursor: 'pointer',
                                    '&:hover': {
                                      opacity: 0.8,
                                    }
                                  }}
                                  onClick={() => {
                                    setSelectedDQAttribute({ id: attr.attribute_id, name: attr.attribute_name });
                                    setShowDQResultsDialog(true);
                                  }}
                                />
                                <Typography 
                                  variant="caption" 
                                  color="text.secondary"
                                  sx={{ 
                                    fontSize: '0.65rem',
                                    cursor: 'pointer',
                                    '&:hover': {
                                      textDecoration: 'underline',
                                    }
                                  }}
                                  onClick={() => {
                                    setSelectedDQAttribute({ id: attr.attribute_id, name: attr.attribute_name });
                                    setShowDQResultsDialog(true);
                                  }}
                                >
                                  {attr.dq_rules_count || 0} rules
                                </Typography>
                                </Box>
                              </Tooltip>
                            ) : (
                              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                                <Typography 
                                  variant="body2" 
                                  color="text.secondary" 
                                  sx={{ fontStyle: 'italic', fontSize: '0.75rem' }}
                                >
                                  No data
                                </Typography>
                                <Typography 
                                  variant="caption" 
                                  color="text.secondary"
                                  sx={{ fontSize: '0.65rem' }}
                                >
                                  0 rules
                                </Typography>
                              </Box>
                            )}
                          </TableCell>
                          <TableCell>
                            <ScopingStatusDisplay status={attr.status} />
                          </TableCell>
                          <TableCell>
                            <ScopingTesterDecisionDisplay
                              testerDecision={attr.tester_decision || 
                                (getScopingDecision(attr.attribute_id) === 'include' ? 'accept' : 
                                 getScopingDecision(attr.attribute_id) === 'exclude' ? 'decline' : null)}
                              testerNotes={attr.tester_rationale}
                              testerDecidedAt={attr.tester_decided_at}
                              isPrimaryKey={attr.is_primary_key}
                            />
                          </TableCell>
                          <TableCell>
                            <ScopingReportOwnerDecisionDisplay
                              reportOwnerDecision={attr.report_owner_decision}
                              reportOwnerNotes={attr.report_owner_notes}
                              reportOwnerDecidedAt={attr.report_owner_decided_at || attr.report_owner_approved_at || attr.report_owner_rejected_at}
                            />
                          </TableCell>
                          <TableCell sx={{ textAlign: 'center' }}>
                            <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                              {/* Show approve/reject buttons for pending items OR edit button for decided items */}
                              {!attr.is_primary_key && !isReadOnly() && (
                                <>
                                  {(!attr.tester_decision || attr.tester_decision === null) ? (
                                    // No decision yet - show approve/reject buttons
                                    <>
                                      <Tooltip title="Approve (Include in testing)">
                                        <IconButton
                                          size="small"
                                          color="success"
                                          onClick={() => handleScopingDecision(attr.attribute_id, 'include')}
                                          disabled={phaseLoading}
                                        >
                                          <CheckCircle fontSize="small" />
                                        </IconButton>
                                      </Tooltip>
                                      <Tooltip title="Reject (Exclude from testing)">
                                        <IconButton
                                          size="small"
                                          color="error"
                                          onClick={() => handleScopingDecision(attr.attribute_id, 'exclude')}
                                          disabled={phaseLoading}
                                        >
                                          <Cancel fontSize="small" />
                                        </IconButton>
                                      </Tooltip>
                                    </>
                                  ) : (
                                    // Has decision - show edit button to change it
                                    <Tooltip title="Change decision">
                                      <IconButton
                                        size="small"
                                        color="primary"
                                        onClick={() => {
                                          // Toggle the decision
                                          const newDecision = attr.tester_decision === 'accept' ? 'exclude' : 'include';
                                          handleScopingDecision(attr.attribute_id, newDecision);
                                        }}
                                        disabled={phaseLoading}
                                      >
                                        <Edit fontSize="small" />
                                      </IconButton>
                                    </Tooltip>
                                  )}
                                </>
                              )}
                              
                              {/* View details button */}
                              <Tooltip title="View Details">
                                <IconButton 
                                  size="small" 
                                  color="primary"
                                  onClick={() => handleShowLLMAnalysis(attr)}
                                >
                                  <InfoIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              
                              {/* Regenerate LLM recommendation */}
                              <Tooltip title="Regenerate LLM recommendation for this attribute">
                                <IconButton
                                  size="small"
                                  onClick={() => handleGenerateRecommendations(true, [attr.attribute_id.toString()])}
                                  disabled={phaseLoading || isReadOnly()}
                                  color="secondary"
                                >
                                  <RefreshIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              
                              {/* LLM analysis button if available */}
                              {attr.llm_risk_score && (
                                <Tooltip title="View LLM Analysis">
                                  <IconButton 
                                    size="small" 
                                    color="secondary"
                                    onClick={() => handleShowLLMAnalysis(attr)}
                                  >
                                    <RecommendIcon fontSize="small" />
                                  </IconButton>
                                </Tooltip>
                              )}
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              );
            })()
          )}
          </Box>
        )}
        
        {/* Documents Tab */}
        {((hasReportOwnerFeedback && activeTab === 2) || (!hasReportOwnerFeedback && activeTab === 1)) && (
          <Box sx={{ p: 3 }}>
            <PhaseDocumentManager
              cycleId={cycleIdNum}
              reportId={reportIdNum}
              phaseId={2} // Scoping phase ID
              phaseName="Scoping"
              allowedDocumentTypes={[
                'data_dictionary',
                'business_requirements',
                'technical_specifications',
                'scoping_checklist',
                'risk_assessment'
              ]}
              requiredDocumentTypes={[
                'data_dictionary',
                'business_requirements'
              ]}
              title="Scoping Phase Documents"
            />
          </Box>
        )}
      </Paper>

      {/* Start Phase Dialog */}
      <Dialog open={showStartDialog} onClose={() => setShowStartDialog(false)}>
        <DialogTitle>Start Scoping Phase</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to start the scoping phase? This will load all attributes from the planning phase. You can then select approved attributes for testing and make decisions on all attributes as required.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowStartDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleStartPhase}
            disabled={phaseLoading}
          >
            Start Phase
          </Button>
        </DialogActions>
      </Dialog>

      {/* Complete Phase Dialog */}
      <Dialog open={showCompleteDialog} onClose={() => setShowCompleteDialog(false)}>
        <DialogTitle>Complete Scoping Phase</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to complete the scoping phase? You have selected {getDecisionCounts.included} attributes out of {attributes.length} total attributes for testing.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCompleteDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            color="success"
            onClick={handleCompletePhase}
            disabled={phaseLoading}
          >
            Complete Phase
          </Button>
        </DialogActions>
      </Dialog>

      {/* Regenerate Recommendations Dialog */}
      <Dialog open={showRegenerateDialog} onClose={() => setShowRegenerateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate LLM Recommendations</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            {phaseStatus && phaseStatus.attributes_with_recommendations && phaseStatus.attributes_with_recommendations > 0 && (
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  Found {phaseStatus.attributes_with_recommendations} attributes with existing recommendations.
                </Typography>
              </Alert>
            )}
            
            <Typography variant="body1" gutterBottom>
              Choose how to generate recommendations:
            </Typography>
            
            <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => {
                  setShowRegenerateDialog(false);
                  handleGenerateRecommendations(false); // Incremental update
                }}
                disabled={phaseLoading}
                sx={{ justifyContent: 'flex-start', textAlign: 'left', p: 2 }}
              >
                <Box>
                  <Typography variant="subtitle1">Generate for Missing Only</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Generate recommendations only for attributes without existing recommendations
                  </Typography>
                </Box>
              </Button>
              
              <Button
                variant="outlined"
                color="warning"
                fullWidth
                onClick={() => {
                  setShowRegenerateDialog(false);
                  handleGenerateRecommendations(true); // Force regenerate all
                }}
                disabled={phaseLoading}
                sx={{ justifyContent: 'flex-start', textAlign: 'left', p: 2 }}
              >
                <Box>
                  <Typography variant="subtitle1">Regenerate All</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Replace all existing recommendations with new ones
                  </Typography>
                </Box>
              </Button>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowRegenerateDialog(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* LLM Analysis Dialog */}
      <Dialog 
        open={showLLMAnalysisDialog} 
        onClose={() => setShowLLMAnalysisDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <RecommendIcon color="primary" />
          LLM Analysis Details: {selectedAttributeForAnalysis?.attribute_name}
        </DialogTitle>
        <DialogContent>
          {selectedAttributeForAnalysis ? (
            <Box sx={{ pt: 2 }}>
              {/* Basic Information */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom color="primary">
                  Basic Information
                </Typography>
                <Box sx={{ ml: 2 }}>
                  <Typography variant="body1" gutterBottom>
                    <strong>Attribute Name:</strong> {selectedAttributeForAnalysis.attribute_name}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>MDRM Code:</strong> {selectedAttributeForAnalysis.mdrm || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Description:</strong> {selectedAttributeForAnalysis.description || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>LLM Generated:</strong> {'No'}
                  </Typography>
                </Box>
              </Box>

              {/* LLM Risk Assessment */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom color="primary">
                  Risk Assessment
                </Typography>
                <Box sx={{ ml: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography component="span" variant="body1">
                      <strong>LLM Risk Score:</strong>
                    </Typography>
                    <Chip 
                      size="small" 
                      label={`${Math.round(selectedAttributeForAnalysis.llm_risk_score || 0)}/100`}
                      color={getRiskColor(selectedAttributeForAnalysis.llm_risk_score || 0)}
                    />
                    <Typography component="span" variant="body1" sx={{ ml: 2 }}>
                      <strong>Confidence:</strong>
                    </Typography>
                    <Chip 
                      size="small" 
                      label={`${((selectedAttributeForAnalysis.llm_confidence_score || 0) * 100).toFixed(0)}%`}
                      color="info"
                    />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography component="span" variant="body1">
                      <strong>Overall Risk Score:</strong>
                    </Typography>
                    <Chip 
                      size="small" 
                      label={`${Math.round(selectedAttributeForAnalysis.overall_risk_score || 0)}`}
                      color={getRiskColor(selectedAttributeForAnalysis.overall_risk_score || 0)}
                    />
                  </Box>
                </Box>
              </Box>

              {/* LLM Analysis Details */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom color="primary">
                  LLM Analysis
                </Typography>
                <Box sx={{ ml: 2 }}>
                  {false && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Description:</strong> {''}
                    </Typography>
                  )}
                  {false && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Format:</strong> {''}
                    </Typography>
                  )}
                  {selectedAttributeForAnalysis.llm_rationale && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Rationale:</strong> {selectedAttributeForAnalysis.llm_rationale}
                    </Typography>
                  )}
                </Box>
              </Box>

              {/* Testing Guidance */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom color="primary">
                  Testing Guidance
                </Typography>
                <Box sx={{ ml: 2 }}>
                  {selectedAttributeForAnalysis.typical_source_documents && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Typical Source Documents:</strong> {selectedAttributeForAnalysis.typical_source_documents}
                    </Typography>
                  )}
                  {selectedAttributeForAnalysis.keywords_to_look_for && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Keywords to Look For:</strong> {selectedAttributeForAnalysis.keywords_to_look_for}
                    </Typography>
                  )}
                  {selectedAttributeForAnalysis.testing_approach && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Testing Approach:</strong> {selectedAttributeForAnalysis.testing_approach}
                    </Typography>
                  )}
                  {selectedAttributeForAnalysis.validation_rules && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Validation Rules:</strong> {selectedAttributeForAnalysis.validation_rules}
                    </Typography>
                  )}
                </Box>
              </Box>

              {/* Attribute Flags */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom color="primary">
                  Attribute Properties
                </Typography>
                <Box sx={{ ml: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip 
                    size="small" 
                    label={`M/C/O: Optional`}
                    color={'default'}
                  />
                  {/* CDE flag not available in interface */}
                  {false && (
                    <Chip size="small" label="CDE" color="warning" />
                  )}
                  {/* Historical issues flag not available in interface */}
                  {false && (
                    <Chip size="small" label="Historical Issues" color="error" />
                  )}
                  {selectedAttributeForAnalysis.is_primary_key && (
                    <Chip size="small" label="Primary Key" color="info" icon={<KeyIcon />} />
                  )}
                </Box>
              </Box>

              {false && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  This attribute does not have LLM-generated analysis. The information shown is from the planning phase or local scoring.
                </Alert>
              )}
            </Box>
          ) : (
            <Typography>No attribute selected for analysis.</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowLLMAnalysisDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Feedback Details Dialog */}
      <Dialog 
        open={showFeedbackDetails} 
        onClose={() => setShowFeedbackDetails(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Edit color="warning" />
          Address Report Owner Feedback
          {feedback?.is_outdated_feedback ? 
            ` - Feedback for v${feedback.feedback_version}` : 
            ` - Version ${feedback?.submission_version}`
          }
        </DialogTitle>
        <DialogContent>
          {feedback?.has_feedback && feedback.review ? (
            <Box sx={{ pt: 2 }}>
              {feedback.is_outdated_feedback && (
                <Alert severity="warning" sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Outdated Feedback Notice
                  </Typography>
                  <Typography variant="body2">
                    This feedback is for version {feedback.feedback_version}, but you have already submitted version {feedback.submission_version}. 
                    The Report Owner will need to review your latest submission.
                  </Typography>
                </Alert>
              )}
              
              <Alert severity={feedback.needs_revision ? 'warning' : feedback.review_decision === 'Approved' ? 'success' : 'error'} sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Status: {feedback.review_decision}
                </Typography>
                <Typography variant="body2">
                  Reviewed by {feedback.provided_by} on {new Date(feedback.provided_at).toLocaleDateString()}
                </Typography>
              </Alert>

              {feedback.feedback_text && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom color="primary">
                    Review Comments
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                      "{feedback.feedback_text}"
                    </Typography>
                  </Paper>
                </Box>
              )}

              {feedback.requested_changes && feedback.requested_changes.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom color="primary">
                    Requested Changes
                  </Typography>
                  <Box sx={{ ml: 2 }}>
                    {feedback.requested_changes.map((change: string, index: number) => (
                      <Typography component="li" variant="body1" key={index} sx={{ mb: 1, listStyleType: 'disc', display: 'list-item' }}>
                        {change}
                      </Typography>
                    ))}
                  </Box>
                </Box>
              )}

              {feedback.can_resubmit && !feedback.is_outdated_feedback && (
                <Alert severity="info" sx={{ mt: 3 }}>
                  <Typography variant="body2">
                    Please review the feedback above, make the necessary changes to your attribute selections, and resubmit when ready.
                  </Typography>
                </Alert>
              )}
              
              {feedback.is_outdated_feedback && (
                <Alert severity="info" sx={{ mt: 3 }}>
                  <Typography variant="body2">
                    You have already addressed this feedback with version {feedback.submission_version}. Please wait for the Report Owner to review your latest submission.
                  </Typography>
                </Alert>
              )}
            </Box>
          ) : (
            <Typography>No feedback available.</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowFeedbackDetails(false)}>Close</Button>
          {feedback?.can_resubmit && !feedback?.is_outdated_feedback && (
            <Button 
              variant="contained" 
              color="warning" 
              onClick={async () => {
                try {
                  setShowFeedbackDetails(false);
                  
                  // Call resubmission API to create new version
                  const response = await apiClient.post(
                    `/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/resubmit-after-feedback`
                  );
                  
                  showToast.success(`New version created for resubmission (v${response.data.version_number}). Please update decisions based on feedback and resubmit.`);
                  
                  // Refresh the page to load the new version
                  window.location.reload();
                  
                } catch (error: any) {
                  console.error('Error creating resubmission version:', error);
                  showToast.error(`Failed to create resubmission version: ${error.response?.data?.detail || error.message}`);
                }
              }}
            >
              Create New Version to Address Feedback
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Version History Dialog */}
      <Dialog 
        open={showVersionHistory} 
        onClose={() => setShowVersionHistory(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AssignmentIcon color="primary" />
          Scoping Submission Version History
        </DialogTitle>
        <DialogContent>
          {versions.length > 0 ? (
            <Box sx={{ pt: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {versions.length} version{versions.length !== 1 ? 's' : ''} found
              </Typography>
              
              {versions.map((version: any, index: number) => (
                <Card key={version.submission_id} sx={{ mb: 2, border: version.version === feedback?.submission_version ? 2 : 1, borderColor: version.version === feedback?.submission_version ? 'primary.main' : 'grey.300' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        Version {version.version}
                        {version.version === feedback?.submission_version && (
                          <Chip size="small" label="Latest" color="primary" />
                        )}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(version.submitted_at).toLocaleDateString()} at {new Date(version.submitted_at).toLocaleTimeString()}
                      </Typography>
                    </Box>

                    <Typography variant="body2" gutterBottom>
                      <strong>Submitted by:</strong> {version.submitted_by}
                    </Typography>

                    <Typography variant="body2" gutterBottom>
                      <strong>Attributes:</strong> {version.scoped_attributes} selected out of {version.total_attributes} total
                    </Typography>

                    {version.submission_notes && (
                      <Typography variant="body2" gutterBottom>
                        <strong>Notes:</strong> {version.submission_notes}
                      </Typography>
                    )}

                    {version.changes_from_previous && (
                      <Box sx={{ mt: 2, p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
                        <Typography variant="body2" fontWeight="medium" gutterBottom>
                          Changes from v{version.version - 1}:
                        </Typography>
                        <Typography variant="body2">
                          {version.changes_from_previous.total_changes || 0} total changes
                        </Typography>
                        {version.changes_from_previous.newly_selected && version.changes_from_previous.newly_selected.length > 0 && (
                          <Typography variant="body2" color="success.main">
                            +{version.changes_from_previous.newly_selected.length} newly selected
                          </Typography>
                        )}
                        {version.changes_from_previous.newly_declined && version.changes_from_previous.newly_declined.length > 0 && (
                          <Typography variant="body2" color="error.main">
                            -{version.changes_from_previous.newly_declined.length} newly declined
                          </Typography>
                        )}
                      </Box>
                    )}

                    {version.review_status && version.review && (
                      <Box sx={{ mt: 2, p: 2, bgcolor: version.review.approval_status === 'Approved' ? 'success.50' : version.review.approval_status === 'Declined' ? 'error.50' : 'warning.50', borderRadius: 1 }}>
                        <Typography variant="body2" fontWeight="medium" gutterBottom>
                          Report Owner Review:
                        </Typography>
                        <Typography variant="body2" gutterBottom>
                          <strong>Status:</strong> <Chip size="small" label={version.review.approval_status} color={version.review.approval_status === 'Approved' ? 'success' : version.review.approval_status === 'Declined' ? 'error' : 'warning'} />
                        </Typography>
                        <Typography variant="body2" gutterBottom>
                          <strong>Reviewed by:</strong> {version.review.reviewed_by} on {new Date(version.review.reviewed_at).toLocaleDateString()}
                        </Typography>
                        {version.review_comments && (
                          <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                            "{version.review_comments}"
                          </Typography>
                        )}
                      </Box>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Box>
          ) : (
            <Typography>No version history available.</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowVersionHistory(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Submission Dialog */}
      <ScopingSubmissionDialog
        open={submissionDialogOpen}
        onClose={() => setSubmissionDialogOpen(false)}
        onSubmit={async (notes) => {
          try {
            // Get current version
            const versionResponse = await apiClient.get(`/scoping/cycles/${cycleIdNum}/reports/${reportIdNum}/current-version`);
            const currentVersion = versionResponse.data;
            
            if (!currentVersion || !currentVersion.version_id) {
              showToast.error('No scoping version found. Please ensure scoping decisions have been made.');
              return;
            }
            
            // Submit the current version for approval
            const response = await apiClient.post(
              `/scoping/versions/${currentVersion.version_id}/submit`,
              {
                submission_notes: notes
              }
            );
            
            showToast.success('Scoping decisions submitted for approval');
            
            // Create Universal Assignment for submission review
            console.log('Creating Universal Assignment for Scoping submission (from dialog):', {
              cycleId: cycleIdNum,
              reportId: reportIdNum,
              phase: 'Scoping',
              userId: user?.user_id || 0,
              userRole: user?.role || '',
            });
            
            try {
              await workflowHooks.onSubmitForApproval('Scoping', {
                cycleId: cycleIdNum,
                reportId: reportIdNum,
                phase: 'Scoping',
                userId: user?.user_id || 0,
                userRole: user?.role || '',
                additionalData: {
                  version: currentVersion.version_number,
                  versionId: currentVersion.version_id
                }
              });
              console.log('Universal Assignment created successfully');
            } catch (assignmentError) {
              console.error('Failed to create Universal Assignment:', assignmentError);
              // Don't fail the whole submission, just log the error
              showToast.error('Warning: Report Owner assignment could not be created. Please contact support.');
            }
            
            // Wait for all status updates to complete
            await Promise.all([
              loadLegacyPhaseStatus(),
              refetchStatus(), // Refetch unified status
              loadVersionsForDropdown() // Reload version list to update status
            ]);
            setSubmissionDialogOpen(false);
          } catch (error: any) {
            showToast.error(error.response?.data?.detail || 'Failed to submit scoping decisions');
          }
        }}
        includedCount={getDecisionCounts.included}
        excludedCount={getDecisionCounts.excluded}
        totalCount={attributes.length}
        hasChanges={true}
        previousVersion={previousSubmission}
      />

      {/* Version History Dialog */}
      {showVersionHistory && (
        <VersionHistoryViewer
          entityType="ScopingDecision"
          entityId={`${cycleId}_${reportId}`}
          open={showVersionHistory}
          onClose={() => setShowVersionHistory(false)}
          onRevert={async (versionNumber) => {
            setSelectedVersion(versionNumber);
            loadSpecificVersion(versionNumber);
            setShowVersionHistory(false);
          }}
          canRevert={true}
          currentVersion={selectedVersion || undefined}
        />
      )}

      {/* DQ Results Dialog */}
      {showDQResultsDialog && selectedDQAttribute && (
        <DQResultsDialog
          open={showDQResultsDialog}
          onClose={() => {
            setShowDQResultsDialog(false);
            setSelectedDQAttribute(null);
          }}
          attributeId={selectedDQAttribute.id}
          attributeName={selectedDQAttribute.name}
          cycleId={parseInt(cycleId || '0')}
          reportId={parseInt(reportId || '0')}
        />
      )}
    </Container>
  );
};

export default ScopingPage; 