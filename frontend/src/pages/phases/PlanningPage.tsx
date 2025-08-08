import React, { useState, useEffect } from 'react';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';
import { useUniversalAssignments } from '../../hooks/useUniversalAssignments';
import { UniversalAssignmentAlert } from '../../components/UniversalAssignmentAlert';
import { workflowHooks } from '../../services/universalAssignmentWorkflow';
import { useAuth } from '../../contexts/AuthContext';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  FormControlLabel,
  Alert,
  Tab,
  Tabs,
  Stack,
  Switch,
  LinearProgress,
  Pagination,
  InputAdornment,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Search as SearchIcon,
  GetApp as ImportIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Key as KeyIcon,
  Warning as WarningIcon,
  History as HistoryIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Assignment as AssignmentIcon,
  PlayArrow as PlayArrowIcon,
  UploadFile as UploadFileIcon,
  DataArray as DataArrayIcon,
  Checklist as ChecklistIcon,
  Psychology as PsychologyIcon,
  AutoAwesome as AutoAwesomeIcon,
  Security as SecurityIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
  Storage as StorageIcon
} from '@mui/icons-material';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { planningApi, ReportAttribute } from '../../api/planning';
// Removed unified planning import - using only primary planning API
// import WorkflowProgress from '../../components/WorkflowProgress';
import { dataDictionaryAPI, RegulatoryDataDictionaryEntry, DataDictionaryFilter } from '../../api/dataDictionary';
import apiClient from '../../api/client';
import { VersionHistoryViewer } from '../../components/common/VersionHistoryViewer';
import { ReportMetadataCard } from '../../components/common/ReportMetadataCard';
import { BatchProgressIndicator } from '../../components/common/BatchProgressIndicator';
// Removed unused import - using unified status hook instead
import { ActivityStateManager } from '../../components/common/ActivityStateManager';
import { DynamicActivityCards } from '../../components/phase/DynamicActivityCards';
import { AddDataSourceActivity, MapPDEsActivity } from '../../components/planning';
import PhaseDocumentManager from '../../components/documents/PhaseDocumentManager';

interface PlanningPageProps {
  cycleId: number;
  reportId: number;
  reportName: string;
  lobName?: string;
}

interface ReportInfo {
  report_id: number;
  report_name: string;
  lob: string;
  assigned_tester?: string;
  report_owner?: string;
  description?: string;
  regulatory_framework?: string;
  frequency?: string;
  due_date?: string;
  priority?: string;
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
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
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
  },
  info: (message: string) => {
    console.log('INFO:', message);
    alert('Info: ' + message);
  }
};

const PlanningPage: React.FC<PlanningPageProps> = ({ cycleId, reportId, reportName }) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  // Convert props to numbers for unified status
  const cycleIdNum = cycleId ? parseInt(cycleId.toString(), 10) : 0;
  const reportIdNum = reportId ? parseInt(reportId.toString(), 10) : 0;
  
  // Unified status system
  const { data: unifiedPhaseStatus, isLoading: statusLoading, refetch: refetchStatus } = usePhaseStatus('Planning', cycleIdNum, reportIdNum);
  
  // Universal Assignments integration
  const {
    hasAssignment,
    assignment,
    canDirectAccess,
    acknowledgeMutation,
    startMutation,
    completeMutation
  } = useUniversalAssignments({
    phase: 'Planning',
    cycleId: cycleIdNum,
    reportId: reportIdNum,
    assignmentType: 'Attribute Approval'
  });
  
  // State for attributes
  const [attributes, setAttributes] = useState<ReportAttribute[]>([]);
  const [selectedAttributes, setSelectedAttributes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [pdeMappings, setPdeMappings] = useState<any[]>([]);
  
  // Removed unified planning state - using only primary planning API
  
  // State for report info
  const [reportInfo, setReportInfo] = useState<ReportInfo | null>(null);
  const [reportInfoLoading, setReportInfoLoading] = useState(false);
  
  // Legacy state for phase status (kept for backward compatibility)
  const [phaseStatus, setPhaseStatus] = useState<any>(null);
  const [phaseLoading, setPhaseLoading] = useState(false);
  
  // State for data dictionary
  const [dictionaryEntries, setDictionaryEntries] = useState<RegulatoryDataDictionaryEntry[]>([]);
  const [selectedDictEntries, setSelectedDictEntries] = useState<number[]>([]);
  const [dictLoading, setDictLoading] = useState(false);
  const [dictPage, setDictPage] = useState(1);
  const [dictTotal, setDictTotal] = useState(0);
  const [dictFilters, setDictFilters] = useState<DataDictionaryFilter>({});
  
  // Hierarchical selection state
  const [availableReports, setAvailableReports] = useState<string[]>([]);
  const [availableSchedules, setAvailableSchedules] = useState<string[]>([]);
  const [selectedReport, setSelectedReport] = useState<string>('');
  const [selectedSchedule, setSelectedSchedule] = useState<string>('');
  const [reportsLoading, setReportsLoading] = useState(false);
  const [schedulesLoading, setSchedulesLoading] = useState(false);
  
  // UI state
  const [tabValue, setTabValue] = useState(0);
  const [scopingTabValue, setScopingTabValue] = useState(0); // For inner tabs in scoping section
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editingAttribute, setEditingAttribute] = useState<ReportAttribute | null>(null);
  const [editingSecurityClass, setEditingSecurityClass] = useState<{[key: string]: boolean}>({});
  const [generatingLLM, setGeneratingLLM] = useState(false);
  
  // Optional activity dialogs
  const [activeActivityDialog, setActiveActivityDialog] = useState<'add_data_source' | 'map_pdes' | null>(null);
  
  // Form state for manual attribute creation
  const [newAttribute, setNewAttribute] = useState({
    attribute_name: '',
    description: '',
    data_type: 'string' as const, // Updated to match unified planning
    mandatory_flag: 'optional' as const, // Updated to match unified planning
    cde_flag: false,
    historical_issues_flag: false,
    is_primary_key: false,
    tester_notes: '',
    information_security_classification: '' as '' | 'HRCI' | 'Confidential' | 'Proprietary' | 'Public' // Updated to match unified planning
  });
  
  // Version state
  const [versions, setVersions] = useState<any[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  const [currentVersion, setCurrentVersion] = useState<any>(null);

  // Helper function to determine read-only state
  const isReadOnly = (): boolean => {
    // Report Owners don't have access to Planning phase
    if (user?.role === 'Report Owner') return true;
    
    // Get current version
    const version = versions.find(v => v.version_id === selectedVersionId);
    
    // If version exists and is not draft, it's read-only
    // Note: Planning may not have versions, so default to editable if no version
    return version ? version.version_status !== 'draft' : false;
  };

  const loadPdeMappings = async () => {
    console.log('[PlanningPage] Loading PDE mappings...');
    try {
      const response = await apiClient.get(
        `/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings`,
        { timeout: 60000 } // 60 seconds timeout
      );
      // PDE mappings endpoint returns { mappings: [...], total: number }
      console.log('[PlanningPage] PDE mappings loaded:', response.data.mappings?.length || 0);
      setPdeMappings(response.data.mappings || []);
    } catch (error) {
      console.error('Error loading PDE mappings:', error);
      // PDE mappings might not exist yet, this is okay
      setPdeMappings([]); // Set empty array on error
    }
  };
  
  const loadVersions = async () => {
    try {
      // Calculate phase_id as cycleId * 1000 + reportId for planning API
      const phaseId = cycleId * 1000 + reportId;
      const response = await apiClient.get(`/planning/phases/${phaseId}/versions`);
      
      if (response.data.versions && response.data.versions.length > 0) {
        setVersions(response.data.versions);
        // Select the current version
        const currentVer = response.data.versions.find((v: any) => v.is_current) || response.data.versions[0];
        setSelectedVersionId(currentVer.version_id);
        setCurrentVersion(currentVer);
      } else {
        // No versions exist yet
        setVersions([]);
        setSelectedVersionId('');
        setCurrentVersion(null);
      }
    } catch (error) {
      console.error('Error loading planning versions:', error);
      // Planning might not have versioning enabled yet
      setVersions([]);
      setSelectedVersionId('');
      setCurrentVersion(null);
    }
  };

  // Load report info and attributes on component mount
  useEffect(() => {
    loadReportInfo();
    loadAttributes();
    loadPhaseStatus();
    loadPdeMappings();
    loadVersions();
    // Removed unified planning check - using only primary planning API
  }, [cycleId, reportId]);

  // Removed unified planning availability check - using only primary planning API

  // Load data dictionary when import dialog opens
  useEffect(() => {
    if (showImportDialog) {
      loadDataDictionary();
    }
  }, [showImportDialog, dictPage, dictFilters]);

  // Load available reports when import tab is accessed
  useEffect(() => {
    if (tabValue === 1) {
      loadAvailableReports();
    }
  }, [tabValue]);

  // Load schedules when report is selected
  useEffect(() => {
    if (selectedReport) {
      loadAvailableSchedules();
    } else {
      setAvailableSchedules([]);
      setSelectedSchedule('');
    }
  }, [selectedReport]);

  // Load dictionary entries when both report and schedule are selected
  useEffect(() => {
    if (selectedReport && selectedSchedule) {
      const filters = {
        report_name: selectedReport,
        schedule_name: selectedSchedule
      };
      setDictFilters(filters);
      loadDataDictionary(filters);
    } else {
      setDictionaryEntries([]);
      setDictTotal(0);
    }
  }, [selectedReport, selectedSchedule, dictPage]);

  const loadAttributes = async () => {
    try {
      setLoading(true);
      const response = await planningApi.listAttributes(cycleId, reportId);
      
      // Debug log to see what attributes contain
      console.log('Loaded attributes:', response);
      console.log('Response type:', typeof response);
      console.log('Is array?', Array.isArray(response));
      if (response && response.length > 0) {
        console.log('First attribute full object:', response[0]);
        console.log('Object keys:', Object.keys(response[0] || {}));
      }
      
      // Sort attributes by: PK first, then CDE, then Issues, then Line Item #
      const sortedAttributes = response.sort((a, b) => {
        // 1. Primary Keys first
        if (a.is_primary_key && !b.is_primary_key) return -1;
        if (!a.is_primary_key && b.is_primary_key) return 1;
        
        // 2. Then CDE flags
        if (a.cde_flag && !b.cde_flag) return -1;
        if (!a.cde_flag && b.cde_flag) return 1;
        
        // 3. Then Historical Issues
        if (a.historical_issues_flag && !b.historical_issues_flag) return -1;
        if (!a.historical_issues_flag && b.historical_issues_flag) return 1;
        
        // 4. Finally by Line Item # (extract number from string like "Line Item 1")
        const getLineNumber = (lineItem: string) => {
          const match = lineItem?.match(/\d+/);
          return match ? parseInt(match[0]) : 999999;
        };
        
        const lineA = getLineNumber(a.line_item_number || '');
        const lineB = getLineNumber(b.line_item_number || '');
        
        return lineA - lineB;
      });
      
      setAttributes(sortedAttributes);
    } catch (error) {
      console.error('Error loading attributes:', error);
      showToast.error('Failed to load attributes');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableReports = async () => {
    try {
      setReportsLoading(true);
      const reports = await dataDictionaryAPI.getAvailableReports();
      setAvailableReports(reports);
    } catch (error) {
      console.error('Error loading available reports:', error);
      showToast.error('Failed to load available reports');
    } finally {
      setReportsLoading(false);
    }
  };

  const loadAvailableSchedules = async () => {
    try {
      setSchedulesLoading(true);
      const schedules = await dataDictionaryAPI.getAvailableSchedules(selectedReport);
      setAvailableSchedules(schedules);
    } catch (error) {
      console.error('Error loading available schedules:', error);
      showToast.error('Failed to load available schedules');
    } finally {
      setSchedulesLoading(false);
    }
  };

  const loadDataDictionary = async (filters?: DataDictionaryFilter) => {
    try {
      setDictLoading(true);
      const filtersToUse = filters || dictFilters;
      const response = await dataDictionaryAPI.getDataDictionary(dictPage, 20, filtersToUse);
      setDictionaryEntries(response.items);
      setDictTotal(response.total);
    } catch (error) {
      console.error('Error loading data dictionary:', error);
      showToast.error('Failed to load data dictionary');
    } finally {
      setDictLoading(false);
    }
  };

  const loadPhaseStatus = async () => {
    try {
      setPhaseLoading(true);
      const response = await planningApi.getStatus(cycleId, reportId);
      setPhaseStatus(response);
    } catch (error) {
      console.error('Error loading phase status:', error);
      // Phase might not be started yet, this is okay
      setPhaseStatus(null);
    } finally {
      setPhaseLoading(false);
    }
  };

  const loadReportInfo = async () => {
    try {
      setReportInfoLoading(true);
      
      // Get report info from cycle-reports endpoint which includes names
      const response = await apiClient.get(`/cycle-reports/${cycleId}/reports/${reportId}`);
      console.log('📋 Report Info Response:', response.data);
      const reportData = response.data;
      
      // Map the API response to our expected format
      setReportInfo({
        report_id: reportData.report_id,
        report_name: reportData.report_name,
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
      // Fallback to basic info from props
      setReportInfo({
        report_id: reportId,
        report_name: reportName,
        lob: 'Unknown',
        assigned_tester: 'Unknown',
        report_owner: 'Unknown'
      });
    } finally {
      setReportInfoLoading(false);
    }
  };

  const handleStartPhase = async () => {
    try {
      setPhaseLoading(true);
      const response = await planningApi.startPhase(cycleId, reportId, {
        planned_start_date: new Date().toISOString(),
        planned_end_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString() // 7 days from now
      });
      setPhaseStatus(response);
      showToast.success('Planning phase started successfully');
      
      // Create Universal Assignment for phase start
      await workflowHooks.onPhaseStart('Planning', {
        cycleId: cycleIdNum,
        reportId: reportIdNum,
        phase: 'Planning',
        userId: user?.user_id || 0,
        userRole: user?.role || '',
        additionalData: {
          plannedStartDate: new Date().toISOString(),
          plannedEndDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
        }
      });
    } catch (error) {
      console.error('Error starting phase:', error);
      showToast.error('Failed to start planning phase');
    } finally {
      setPhaseLoading(false);
    }
  };

  const handleCompletePhase = async () => {
    try {
      setPhaseLoading(true);
      const response = await planningApi.completePhase(cycleId, reportId, {
        completion_notes: 'Planning phase completed via simplified interface',
        attributes_confirmed: true,
        documents_verified: true
      });
      setPhaseStatus(response);
      
      // Check if we can complete the phase with pending assignments
      await workflowHooks.onPhaseComplete('Planning', {
        cycleId: cycleIdNum,
        reportId: reportIdNum,
        phase: 'Planning',
        userId: user?.user_id || 0,
        userRole: user?.role || '',
        additionalData: {
          completionNotes: 'Planning phase completed via simplified interface',
          attributesConfirmed: true,
          documentsVerified: true
        }
      });
      
      showToast.success('Planning phase completed successfully');
    } catch (error) {
      console.error('Error completing phase:', error);
      showToast.error('Failed to complete planning phase');
    } finally {
      setPhaseLoading(false);
    }
  };

  const handleActivityAction = async (activity: any, action: string) => {
    // Check if this is an optional activity that requires a UI
    const activityCode = activity.metadata?.activity_code;
    
    if (action === 'start' && ['add_data_source', 'map_pdes'].includes(activityCode)) {
      // Open the appropriate dialog for the optional activity
      setActiveActivityDialog(activityCode as any);
      return;
    }
    
    try {
      setLoading(true);
      
      // Use the generic activity management endpoint
      const endpoint = action === 'start' ? 'start' : 'complete';
      const response = await apiClient.post(`/activity-management/activities/${activity.activity_id}/${endpoint}`, {
        cycle_id: cycleId,
        report_id: reportId,
        phase_name: 'Planning'
      });
      
      // Show success message from backend or default
      const message = response.data.message || activity.metadata?.success_message || `${action === 'start' ? 'Started' : 'Completed'} ${activity.name}`;
      showToast.success(message);
      
      // Special handling for START activities - immediately complete them if not already completed
      if (action === 'start' && activity.metadata?.activity_type === 'START') {
        console.log('Auto-completing START activity:', activity.name);
        await new Promise(resolve => setTimeout(resolve, 500)); // Give backend time to process
        
        try {
          await apiClient.post(`/activity-management/activities/${activity.activity_id}/complete`, {
            cycle_id: cycleId,
            report_id: reportId,
            phase_name: 'Planning'
          });
          showToast.success(`${activity.name} completed`);
        } catch (completeError: any) {
          // Check if error is because activity is already completed
          if (completeError.response?.data?.detail?.includes('Cannot complete activity in status')) {
            console.log('START activity already completed, this is expected');
          } else {
            // Ignore "already completed" errors

            if (completeError.response?.status === 400 && 

                completeError.response?.data?.detail?.includes('Cannot complete activity in status')) {

              console.log('START activity already completed, ignoring error');

            } else {

              console.error('Error auto-completing START activity:', completeError);

            }
          }
        }
      }
      
      // Add a small delay to ensure backend has processed the change
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Force refresh of both status systems
      queryClient.invalidateQueries({ queryKey: ['phaseStatus', 'Planning', cycleIdNum, reportIdNum] });
      await refetchStatus();
      await loadPhaseStatus();
    } catch (error) {
      console.error(`Error ${action}ing activity:`, error);
      showToast.error(`Failed to ${action} activity`);
    } finally {
      setLoading(false);
    }
  };

  const handleSetInProgress = async () => {
    try {
      setPhaseLoading(true);
      const response = await planningApi.setInProgress(cycleId, reportId);
      setPhaseStatus(response);
      showToast.success('Planning phase set to In Progress');
    } catch (error) {
      console.error('Error setting phase to In Progress:', error);
      showToast.error('Failed to set planning phase to In Progress');
    } finally {
      setPhaseLoading(false);
    }
  };

  const handleUpdatePhaseStatus = async (newStatus: 'At Risk' | 'Off Track') => {
    try {
      setPhaseLoading(true);
      // For now, we'll just show a toast. In a real implementation, this would call an API
      showToast.warning(`Phase status updated to ${newStatus}`);
      // TODO: Implement actual API call to update phase status
      // await planningApi.updatePhaseStatus(cycleId, reportId, newStatus);
      // loadPhaseStatus();
    } catch (error) {
      console.error('Error updating phase status:', error);
      showToast.error('Failed to update phase status');
    } finally {
      setPhaseLoading(false);
    }
  };

  const handleCreateAttribute = async () => {
    try {
      await planningApi.createAttribute(cycleId, reportId, newAttribute);
      showToast.success('Attribute created successfully');
      setShowAddDialog(false);
      setNewAttribute({
        attribute_name: '',
        description: '',
        data_type: 'string', // Updated to match unified planning
        mandatory_flag: 'optional', // Updated to match unified planning
        cde_flag: false,
        historical_issues_flag: false,
        is_primary_key: false,
        tester_notes: '',
        information_security_classification: 'Public' // Updated to match unified planning
      });
      loadAttributes();
      loadPhaseStatus(); // Reload metrics when attributes are added
      refetchStatus(); // Refetch unified status
    } catch (error) {
      console.error('Error creating attribute:', error);
      showToast.error('Failed to create attribute');
    }
  };

  const handleUpdateAttribute = async () => {
    if (!editingAttribute) return;
    
    try {
      // Transform the data to match the expected types
      const updateData = {
        ...editingAttribute,
        information_security_classification: editingAttribute.information_security_classification === 'public' ? 'Public' as const :
                                           editingAttribute.information_security_classification === 'internal' ? 'Public' as const :
                                           editingAttribute.information_security_classification === 'confidential' ? 'Confidential' as const :
                                           editingAttribute.information_security_classification === 'restricted' ? 'HRCI' as const :
                                           editingAttribute.information_security_classification === 'proprietary' ? 'Proprietary' as const :
                                           undefined
      };
      await planningApi.updateAttribute(cycleId, reportId, editingAttribute.id, updateData);
      showToast.success('Attribute updated successfully');
      setShowEditDialog(false);
      setEditingAttribute(null);
      loadAttributes();
      loadPhaseStatus(); // Reload metrics when attributes are updated
      refetchStatus(); // Refetch unified status
    } catch (error) {
      console.error('Error updating attribute:', error);
      showToast.error('Failed to update attribute');
    }
  };

  const handleDeleteAttributes = async () => {
    if (selectedAttributes.length === 0) return;
    
    setShowDeleteDialog(false);
    
    try {
      await Promise.all(
        selectedAttributes.map(id => planningApi.deleteAttribute(cycleId, reportId, id))
      );
      showToast.success('Attributes deleted successfully');
      setSelectedAttributes([]);
      loadAttributes();
      loadPhaseStatus(); // Reload metrics when attributes are deleted
      refetchStatus(); // Refetch unified status
    } catch (error) {
      console.error('Error deleting attributes:', error);
      showToast.error('Failed to delete attributes');
    }
  };

  const handleBulkApproval = async (status: 'approved' | 'rejected', attributeIds: string[]) => {
    if (attributeIds.length === 0) return;
    
    try {
      // Use bulk update API for better performance
      const result = await planningApi.bulkUpdateAttributes(
        cycleId, 
        reportId, 
        attributeIds,
        { approval_status: status }
      );
      
      showToast.success(`${result.updated} attributes ${status} successfully`);
      setSelectedAttributes([]);
      loadAttributes();
      loadPhaseStatus(); // Reload metrics when approval status changes
      refetchStatus(); // Refetch unified status
    } catch (error) {
      console.error('Error updating approval status:', error);
      showToast.error('Failed to update approval status');
    }
  };

  const handleImportFromDictionary = async () => {
    if (selectedDictEntries.length === 0) {
      showToast.warning('Please select entries to import');
      return;
    }

    try {
      const response = await dataDictionaryAPI.importDataDictionaryEntries({
        selected_dict_ids: selectedDictEntries,
        cycle_id: cycleId,
        report_id: reportId
      });

      if (response.success) {
        showToast.success(
          `Successfully imported ${response.imported_count} attributes. ` +
          `Skipped ${response.skipped_count} (already exist).`
        );
      } else {
        showToast.warning(
          `Imported ${response.imported_count} attributes with ${response.error_count} errors.`
        );
      }

      setShowImportDialog(false);
      setSelectedDictEntries([]);
      loadAttributes();
      loadPhaseStatus(); // Reload metrics when attributes are imported
      refetchStatus(); // Refetch unified status
    } catch (error) {
      console.error('Error importing from dictionary:', error);
      showToast.error('Failed to import from data dictionary');
    }
  };

  const handleToggleFlag = async (attributeId: string, field: string, value: boolean) => {
    // Store current scroll position
    const scrollY = window.scrollY;
    
    try {
      await planningApi.updateAttribute(cycleId, reportId, attributeId, { [field]: value });
      await loadAttributes();
      await loadPhaseStatus();
      refetchStatus(); // Refetch unified status
      
      // Restore scroll position after updates
      requestAnimationFrame(() => {
        window.scrollTo(0, scrollY);
      });
    } catch (error) {
      console.error('Error updating flag:', error);
      showToast.error('Failed to update flag');
    }
  };

  const handleGenerateLLMClassifications = async () => {
    if (selectedAttributes.length === 0) {
      showToast.error('Please select attributes to generate classifications for');
      return;
    }

    setGeneratingLLM(true);
    try {
      // Call LLM API to generate classifications for selected attributes
      const response = await apiClient.post(`/llm/generate-classifications`, {
        cycle_id: cycleId,
        report_id: reportId,
        attribute_ids: selectedAttributes
      });

      if (response.data.classifications) {
        // Update attributes with LLM-generated classifications
        for (const classification of response.data.classifications) {
          await planningApi.updateAttribute(
            cycleId, 
            reportId, 
            classification.id, 
            { 
              information_security_classification: classification.suggested_classification,
              llm_classification_rationale: classification.rationale
            }
          );
        }
        
        await loadAttributes();
        showToast.success('LLM classifications generated successfully');
      }
    } catch (error) {
      console.error('Error generating LLM classifications:', error);
      showToast.error('Failed to generate LLM classifications');
    } finally {
      setGeneratingLLM(false);
    }
  };

  const handleSecurityClassificationChange = async (attributeId: string, value: string) => {
    try {
      await planningApi.updateAttribute(cycleId, reportId, attributeId, { 
        information_security_classification: value as 'HRCI' | 'Confidential' | 'Proprietary' | 'Public' 
      });
      await loadAttributes();
      await loadPhaseStatus();
      refetchStatus();
      setEditingSecurityClass({ ...editingSecurityClass, [attributeId]: false });
    } catch (error) {
      console.error('Error updating security classification:', error);
      showToast.error('Failed to update security classification');
    }
  };

  const resetSelection = () => {
    setSelectedReport('');
    setSelectedSchedule('');
    setAvailableSchedules([]);
    setDictionaryEntries([]);
    setSelectedDictEntries([]);
    setDictTotal(0);
    setDictPage(1);
  };

  const getMandatoryColor = (mandatory: string) => {
    switch (mandatory) {
      case 'Mandatory': return 'error';
      case 'Conditional': return 'warning';
      default: return 'default';
    }
  };

  const getApprovalColor = (status: string) => {
    switch (status) {
      case 'approved': return 'success';
      case 'rejected': return 'error';
      default: return 'default';
    }
  };

  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [activeBatchJob, setActiveBatchJob] = useState<string | null>(null);
  const [activePDEMappingJobId, setActivePDEMappingJobId] = useState<string | null>(null);

  const handleAutoMapPDEs = async () => {
    try {
      setLoading(true);
      showToast.success('Starting automatic PDE mapping with LLM...');
      
      // Start background LLM auto-mapping job
      const response = await apiClient.post(`/planning/cycles/${cycleId}/reports/${reportId}/pde-mappings/auto-map`);
      
      const result = response.data;
      if (result.job_id) {
        showToast.success(`PDE mapping job started! Total attributes: ${result.total_attributes}`);
        setActivePDEMappingJobId(result.job_id);
        setTabValue(5); // Switch to Map PDEs tab to show progress
        
        // Poll for job status
        const pollJobStatus = async () => {
          try {
            const statusResponse = await apiClient.get(`/jobs/${result.job_id}/status`);
            const jobStatus = statusResponse.data;
            
            // Update progress based on job status
            if (jobStatus.status === 'running') {
              // Don't show toast for every progress update - it's shown inline in MapPDEsActivity
              // showToast.info(`${jobStatus.current_step}: ${jobStatus.message} (${jobStatus.progress_percentage}%)`);
              
              // Continue polling
              setTimeout(pollJobStatus, 2000); // Poll every 2 seconds
            } else if (jobStatus.status === 'completed') {
              const mapped_count = jobStatus.result?.mapped_count || 0;
              const total_count = jobStatus.result?.total_count || 0;
              
              if (mapped_count > 0) {
                showToast.success(`✅ PDE mapping completed! Mapped ${mapped_count} out of ${total_count} attributes.`);
              } else {
                showToast.warning(`⚠️ No attributes were mapped automatically. Please use manual mapping.`);
              }
              
              // Navigate to Map PDEs tab to see results
              setTabValue(5);
              
              // Refresh data to show updated mappings
              await loadAttributes();
              await loadPdeMappings();
              setLoading(false);
              
            } else if (jobStatus.status === 'failed') {
              showToast.error(`❌ PDE mapping failed: ${jobStatus.error || 'Unknown error'}`);
              setLoading(false);
            } else {
              // Still pending, continue polling
              setTimeout(pollJobStatus, 2000);
            }
          } catch (error: any) {
            console.error('Error polling job status:', error);
            showToast.error('Failed to get job status. Please check the Map PDEs tab for results.');
            setLoading(false);
          }
        };
        
        // Start polling after a short delay
        setTimeout(pollJobStatus, 1000);
        
      } else {
        // Handle immediate response (no background job needed)
        if (result.mapped_count > 0) {
          showToast.success(`PDE mapping completed! Mapped ${result.mapped_count} out of ${result.total_count} attributes.`);
        } else {
          showToast.warning(`${result.message || 'No attributes were mapped.'}`);
        }
        setTabValue(5);
        await loadAttributes();
        await loadPdeMappings();
        setLoading(false);
      }
      
    } catch (error: any) {
      console.error('Error auto-mapping PDEs:', error);
      if (error.response?.status === 404) {
        showToast.error('Auto-mapping endpoint not found. Please use manual mapping.');
      } else {
        showToast.error('Failed to start auto-mapping. Please try manual mapping.');
      }
      // Navigate to Map PDEs tab for manual mapping
      setTabValue(5);
    } finally {
      setLoading(false);
    }
  };

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

      {/* Report Metadata Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            {/* Left side - Report title and phase info */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <AssignmentIcon color="primary" fontSize="large" />
              <Box>
                <Typography variant="h5" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportInfo?.report_name || reportName || 'Loading...'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Planning Phase - {reportInfo?.description || 'Defining test attributes and scope'}
                </Typography>
              </Box>
            </Box>
            
            {/* Right side - Key metadata */}
            <ReportMetadataCard
              metadata={reportInfo ?? null}
              loading={false}
              variant="compact"
              showFields={['lob', 'tester', 'owner']}
            />
          </Box>
        </CardContent>
      </Card>


      {/* Active Batch Job Progress */}
      {activeBatchJob && (
        <Box sx={{ mb: 3 }}>
          <BatchProgressIndicator
            jobId={activeBatchJob}
            title="Processing attributes..."
            onComplete={() => {
              setActiveBatchJob(null);
              loadAttributes();
              loadPhaseStatus();
              refetchStatus(); // Refetch unified status
            }}
            onError={() => setActiveBatchJob(null)}
            showDetails
          />
        </Box>
      )}

      {/* Read-only Alert if needed */}
      {isReadOnly() && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <strong>Read-only mode:</strong> This version is {currentVersion?.version_status || 'not in draft status'} and cannot be edited.
        </Alert>
      )}

      {/* Planning Metrics Row */}
      <Box sx={{ mb: 3 }}>
        {/* First Row - Primary Metrics */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          {/* Metric: Total Attributes */}
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h3" color="primary" component="div">
                  {attributes.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Attributes
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Metric: Approved Attributes */}
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h3" color="success.main" component="div">
                  {phaseStatus?.approved_count || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Approved for Planning
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Metric: CDEs */}
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h3" color="warning.main" component="div">
                  {attributes.filter(attr => attr.cde_flag).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Critical Data Elements
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Metric: Primary Keys */}
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h3" color="info.main" component="div">
                  {attributes.filter(attr => attr.is_primary_key).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Primary Keys
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Metric: Historical Issues */}
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h3" color="error.main" component="div">
                  {attributes.filter(attr => attr.historical_issues_flag).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Historical Issues
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Metric: Completion Time */}
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h3" color="secondary.main" component="div">
                  {phaseStatus?.started_at && phaseStatus?.status === 'Complete' && phaseStatus?.completed_at ? 
                    Math.ceil((new Date(phaseStatus.completed_at).getTime() - new Date(phaseStatus.started_at).getTime()) / (1000 * 60 * 60 * 24)) :
                    phaseStatus?.started_at ? 
                      Math.ceil((new Date().getTime() - new Date(phaseStatus.started_at).getTime()) / (1000 * 60 * 60 * 24)) :
                    '--'
                  }
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {phaseStatus?.status === 'Complete' ? 'Completion Time (days)' : 'Days Elapsed'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Second Row - Status and Controls */}
        <Grid container spacing={2}>
          {/* Metric: On-Time Status */}
          <Grid size={{ xs: 12, sm: 6, md: 6 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography 
                  variant="h3" 
                  color={
                    phaseStatus?.status === 'Complete' ? 
                      (phaseStatus?.planned_end_date && phaseStatus?.completed_at && 
                       new Date(phaseStatus.completed_at) <= new Date(phaseStatus.planned_end_date) ? 
                       'success.main' : 'error.main') :
                    phaseStatus?.planned_end_date && new Date() <= new Date(phaseStatus.planned_end_date) ?
                      'success.main' : 'warning.main'
                  } 
                  component="div"
                  sx={{ fontSize: '1.5rem' }}
                >
                  {phaseStatus?.status === 'Complete' ? 
                    (phaseStatus?.planned_end_date && phaseStatus?.completed_at && 
                     new Date(phaseStatus.completed_at) <= new Date(phaseStatus.planned_end_date) ? 
                     'Yes - Completed On-Time' : 'No - Completed Late') :
                    phaseStatus?.planned_end_date && new Date() <= new Date(phaseStatus.planned_end_date) ?
                      'On Track' : 'At Risk'
                  }
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {phaseStatus?.status === 'Complete' ? 'On-Time Completion Status' : 'Current Schedule Status'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Phase Controls - Expanded */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6" sx={{ fontSize: '1rem' }}>
                    Phase Controls
                  </Typography>
                  
                  {/* Tester Status Update Controls */}
                  {phaseStatus && phaseStatus.status === 'In Progress' && (
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Chip
                        label="At Risk"
                        size="small"
                        color="warning"
                        variant="outlined"
                        clickable
                        onClick={() => handleUpdatePhaseStatus('At Risk')}
                        disabled={phaseLoading}
                        sx={{ fontSize: '0.7rem' }}
                      />
                      <Chip
                        label="Off Track"
                        size="small"
                        color="error"
                        variant="outlined"
                        clickable
                        onClick={() => handleUpdatePhaseStatus('Off Track')}
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
                      'To complete: Start phase → Add/import attributes → Approve attributes for testing'
                    ) : phaseStatus.status === 'Complete' ? (
                      'Phase completed successfully - all requirements met'
                    ) : phaseStatus.can_complete ? (
                      'Ready to complete - all requirements met'
                    ) : (
                      `To complete: ${phaseStatus.completion_requirements?.join(', ') || 'Add and approve at least one attribute for testing'}`
                    )}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Planning Phase Workflow */}
      <Card sx={{ mb: 3, overflow: 'hidden' }}>
        <CardContent sx={{ overflow: 'hidden' }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssignmentIcon color="primary" />
            Planning Phase Workflow
          </Typography>
          
          <Box sx={{ mt: 2, width: '100%', overflow: 'hidden' }}>
            {unifiedPhaseStatus?.activities ? (
              <DynamicActivityCards
                key={`planning-activities-${unifiedPhaseStatus.last_updated}`}
                activities={unifiedPhaseStatus.activities}
                cycleId={cycleIdNum}
                reportId={reportIdNum}
                phaseName="Planning"
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
                    Loading planning activities...
                  </Typography>
                </Box>
              )}
          </Box>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PlayArrowIcon color="primary" />
            Quick Actions
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Perform common planning activities
          </Typography>
          <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
            <Button
              variant="outlined"
              startIcon={<StorageIcon />}
              onClick={() => setTabValue(4)}
              size="small"
            >
              Add Data Sources
            </Button>
            <Button
              variant="outlined"
              startIcon={<PsychologyIcon />}
              onClick={() => handleAutoMapPDEs()}
              size="small"
            >
              Map PDEs
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Report Attributes" />
          <Tab label="Import from Dictionary" />
          <Tab label="Activity Status" />
          <Tab label="Documents" />
          <Tab label="Data Sources" />
          <Tab label="Map PDEs" />
        </Tabs>
      </Box>

      {/* Report Attributes Tab */}
      <TabPanel value={tabValue} index={0}>
        {/* Inner Tabs for Scoping Section */}
        <Tabs 
          value={scopingTabValue} 
          onChange={(_, newValue) => setScopingTabValue(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
        >
          <Tab label="Scoping Decisions" />
          <Tab label="Documents" />
          <Tab label="Version History" />
        </Tabs>

        {/* Scoping Decisions Tab */}
        {scopingTabValue === 0 && (
          <>
            {/* Actions Card */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setShowAddDialog(true)}
                    disabled={isReadOnly()}
                  >
                    Add Attribute
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<ImportIcon />}
                    onClick={() => setTabValue(1)}
                  >
                    Import from Dictionary
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteIcon />}
                    disabled={selectedAttributes.length === 0 || isReadOnly()}
                    onClick={() => setShowDeleteDialog(true)}
                  >
                    Delete Selected ({selectedAttributes.length})
                  </Button>
                </Stack>

                {selectedAttributes.length > 0 && (
                  <Stack direction="row" spacing={2}>
                    <Button
                      variant="outlined"
                      color="primary"
                      startIcon={generatingLLM ? <CircularProgress size={20} /> : <AutoAwesomeIcon />}
                      onClick={handleGenerateLLMClassifications}
                      disabled={generatingLLM || isReadOnly()}
                    >
                      {generatingLLM ? 'Generating...' : 'Generate Security Classifications'}
                    </Button>
                    <Button
                      variant="outlined"
                      color="primary"
                      startIcon={<PsychologyIcon />}
                      onClick={() => setTabValue(5)}
                    >
                      Map PDEs
                    </Button>
                    <Button
                      variant="outlined"
                      color="primary"
                      startIcon={<StorageIcon />}
                      onClick={() => setActiveActivityDialog('add_data_source')}
                    >
                      Add Data Sources
                    </Button>
                    <Button
                      variant="outlined"
                      color="success"
                      startIcon={<CheckCircleIcon />}
                      onClick={() => handleBulkApproval('approved', selectedAttributes)}
                      disabled={selectedAttributes.length === 0}
                    >
                      Approve Selected
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<CancelIcon />}
                      onClick={() => handleBulkApproval('rejected', selectedAttributes)}
                      disabled={selectedAttributes.length === 0}
                    >
                      Reject Selected
                    </Button>
                  </Stack>
                )}
              </CardContent>
            </Card>

            {/* Attributes Table */}
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Report Attributes ({attributes.length})
            </Typography>
            
            {loading ? (
              <LinearProgress />
            ) : (
              <TableContainer component={Paper} sx={{ overflowX: 'auto' }}>
                <Table sx={{ minWidth: 1200 }}>
                      <TableHead>
                        <TableRow>
                          <TableCell padding="checkbox">
                            <Checkbox
                              checked={selectedAttributes.length === attributes.length && attributes.length > 0}
                              indeterminate={selectedAttributes.length > 0 && selectedAttributes.length < attributes.length}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedAttributes(attributes.map(attr => attr.id));
                                } else {
                                  setSelectedAttributes([]);
                                }
                              }}
                            />
                          </TableCell>
                          <TableCell sx={{ width: '8%' }}>Line Item #</TableCell>
                          <TableCell sx={{ width: '15%' }}>Attribute Name</TableCell>
                          <TableCell sx={{ width: '12%' }}>Technical Name</TableCell>
                          <TableCell sx={{ width: '20%' }}>Description</TableCell>
                          <TableCell sx={{ width: '6%' }}>MDRM</TableCell>
                          <TableCell sx={{ width: '12%' }}>PDE</TableCell>
                          <TableCell sx={{ width: '8%' }}>Data Type</TableCell>
                          <TableCell sx={{ width: '8%' }}>Mandatory</TableCell>
                          <TableCell sx={{ width: '10%' }}>Classification</TableCell>
                          <TableCell sx={{ width: '8%' }}>Approval</TableCell>
                          <TableCell sx={{ width: '5%' }}>Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {attributes.map((attr) => (
                          <TableRow key={attr.id}>
                            <TableCell padding="checkbox">
                              <Checkbox
                                checked={selectedAttributes.includes(attr.id)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedAttributes([...selectedAttributes, attr.id]);
                                  } else {
                                    setSelectedAttributes(selectedAttributes.filter(id => id !== attr.id));
                                  }
                                }}
                              />
                            </TableCell>
                            <TableCell>
                              {attr.line_item_number ? (
                                <Typography variant="body2" fontFamily="monospace" fontWeight="medium">
                                  {attr.line_item_number}
                                </Typography>
                              ) : (
                                <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                  N/A
                                </Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" fontWeight="medium">
                                {attr.attribute_name}
                              </Typography>
                              {/* Interactive badges under attribute name */}
                              <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                <Chip 
                                  size="small" 
                                  label="CDE" 
                                  color={attr.cde_flag ? "warning" : "default"}
                                  variant={attr.cde_flag ? "filled" : "outlined"}
                                  clickable
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    handleToggleFlag(attr.id, 'cde_flag', !attr.cde_flag);
                                  }}
                                  sx={{ fontSize: '0.65rem', height: '20px' }}
                                />
                                <Chip 
                                  size="small" 
                                  label="Issues" 
                                  color={attr.historical_issues_flag ? "error" : "default"}
                                  variant={attr.historical_issues_flag ? "filled" : "outlined"}
                                  clickable
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    handleToggleFlag(attr.id, 'historical_issues_flag', !attr.historical_issues_flag);
                                  }}
                                  sx={{ fontSize: '0.65rem', height: '20px' }}
                                />
                                <Chip 
                                  size="small" 
                                  label="PK" 
                                  color={attr.is_primary_key ? "info" : "default"}
                                  variant={attr.is_primary_key ? "filled" : "outlined"}
                                  clickable
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    handleToggleFlag(attr.id, 'is_primary_key', !attr.is_primary_key);
                                  }}
                                  sx={{ fontSize: '0.65rem', height: '20px' }}
                                />
                              </Box>
                            </TableCell>
                            <TableCell>
                              {attr.technical_line_item_name ? (
                                <Typography variant="body2">
                                  {attr.technical_line_item_name}
                                </Typography>
                              ) : (
                                <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                  N/A
                                </Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              {attr.description ? (
                                <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                                  {attr.description}
                                </Typography>
                              ) : (
                                <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                  No description
                                </Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              {attr.mdrm ? (
                                <Typography variant="body2" fontFamily="monospace">
                                  {attr.mdrm}
                                </Typography>
                              ) : (
                                <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                  N/A
                                </Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              {(() => {
                                const mapping = pdeMappings.find(m => String(m.attribute_id) === String(attr.id));
                                if (mapping) {
                                  // Parse source_field to extract column and table
                                  let columnName = mapping.source_column;
                                  let tableName = mapping.source_table;
                                  
                                  if (!columnName && mapping.source_field) {
                                    const parts = mapping.source_field.split('.');
                                    if (parts.length >= 3) {
                                      // Format: schema.table.column - skip schema if it's "public"
                                      const schema = parts[0];
                                      tableName = parts[1];
                                      columnName = parts[2];
                                    } else if (parts.length === 2) {
                                      // Format: table.column
                                      tableName = parts[0];
                                      columnName = parts[1];
                                    } else {
                                      // Just column name
                                      columnName = mapping.source_field;
                                    }
                                  }
                                  
                                  return (
                                    <Box>
                                      <Typography 
                                        variant="body2" 
                                        fontFamily="monospace" 
                                        fontSize="0.875rem"
                                        sx={{ wordBreak: 'break-word' }}
                                      >
                                        {columnName || mapping.pde_name}
                                      </Typography>
                                      {(mapping.data_source_name || tableName) && (
                                        <Typography 
                                          variant="caption" 
                                          color="text.secondary"
                                          sx={{ wordBreak: 'break-word' }}
                                        >
                                          {mapping.data_source_name}{tableName ? `.${tableName}` : ''}
                                        </Typography>
                                      )}
                                    </Box>
                                  );
                                }
                                return (
                                  <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                    Not mapped
                                  </Typography>
                                );
                              })()}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {attr.data_type}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                size="small"
                                label={attr.mandatory_flag}
                                color={getMandatoryColor(attr.mandatory_flag)}
                              />
                            </TableCell>
                            <TableCell>
                              {(() => {
                                const mapping = pdeMappings.find(m => String(m.attribute_id) === String(attr.id));
                                const classification = mapping?.information_security_classification || attr.information_security_classification;
                                
                                if (editingSecurityClass[attr.id]) {
                                  return (
                                    <FormControl size="small" fullWidth>
                                      <Select
                                        value={classification || ''}
                                        onChange={(e) => handleSecurityClassificationChange(attr.id, e.target.value)}
                                        onBlur={() => setEditingSecurityClass({ ...editingSecurityClass, [attr.id]: false })}
                                        autoFocus
                                        size="small"
                                      >
                                        <MenuItem value="">Not classified</MenuItem>
                                        <MenuItem value="Public">Public</MenuItem>
                                        <MenuItem value="Proprietary">Proprietary</MenuItem>
                                        <MenuItem value="confidential">Confidential</MenuItem>
                                        <MenuItem value="restricted">Restricted</MenuItem>
                                      </Select>
                                    </FormControl>
                                  );
                                }
                                
                                return (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    {classification ? (
                                      <Chip
                                        size="small"
                                        label={classification}
                                        sx={{
                                          backgroundColor: 
                                            classification === 'HRCI' ? '#d32f2f' :
                                            classification === 'Confidential' ? '#f57c00' :
                                            classification === 'Proprietary' ? '#1976d2' :
                                            '#388e3c',
                                          color: 'white',
                                          fontWeight: 'medium'
                                        }}
                                      />
                                    ) : (
                                      <Typography variant="body2" color="text.secondary">
                                        Not classified
                                      </Typography>
                                    )}
                                    <Tooltip title="Click to edit">
                                      <IconButton
                                        size="small"
                                        onClick={() => setEditingSecurityClass({ ...editingSecurityClass, [attr.id]: true })}
                                        sx={{ opacity: 0.6, '&:hover': { opacity: 1 } }}
                                        disabled={isReadOnly()}
                                      >
                                        <EditIcon fontSize="small" />
                                      </IconButton>
                                    </Tooltip>
                                  </Box>
                                );
                              })()}
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'nowrap' }}>
                                {/* Approve button */}
                                <Tooltip title={attr.approval_status === 'approved' ? 'Approved' : 'Click to Approve'}>
                                  <IconButton
                                    size="small"
                                    onClick={() => handleBulkApproval('approved', [attr.id])}
                                    sx={{ 
                                      padding: 0.5,
                                      color: attr.approval_status === 'approved' ? 'success.main' : 'text.secondary',
                                      '&:hover': { color: 'success.main' }
                                    }}
                                    disabled={isReadOnly()}
                                  >
                                    <CheckCircleIcon sx={{ fontSize: 18 }} />
                                  </IconButton>
                                </Tooltip>
                                
                                {/* Reject button */}
                                <Tooltip title={attr.approval_status === 'rejected' ? 'Rejected' : 'Click to Reject'}>
                                  <IconButton
                                    size="small"
                                    onClick={() => handleBulkApproval('rejected', [attr.id])}
                                    sx={{ 
                                      padding: 0.5,
                                      color: attr.approval_status === 'rejected' ? 'error.main' : 'text.secondary',
                                      '&:hover': { color: 'error.main' }
                                    }}
                                    disabled={isReadOnly()}
                                  >
                                    <CancelIcon sx={{ fontSize: 18 }} />
                                  </IconButton>
                                </Tooltip>
                                
                                {/* Pending warning indicator */}
                                {(!attr.approval_status || attr.approval_status === 'pending') && (
                                  <Tooltip title="Pending Approval">
                                    <WarningIcon color="warning" sx={{ fontSize: 16 }} />
                                  </Tooltip>
                                )}
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Tooltip title="Edit Attribute">
                                <IconButton
                                  size="small"
                                  onClick={() => {
                                    setEditingAttribute(attr);
                                    setShowEditDialog(true);
                                  }}
                                  disabled={isReadOnly()}
                                >
                                  <EditIcon />
                                </IconButton>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
          </>
        )}

        {/* Documents Tab */}
        {scopingTabValue === 1 && (
        <PhaseDocumentManager
          cycleId={cycleIdNum}
          reportId={reportIdNum}
          phaseId={1} // Planning phase ID
          phaseName="Planning"
          allowedDocumentTypes={[
            'report_sample_data',
            'report_underlying_transaction_data',
            'report_source_transaction_data',
            'report_source_document'
          ]}
          requiredDocumentTypes={[
            'report_source_document'
          ]}
          title="Scoping Documents"
        />
        )}

        {/* Version History Tab */}
        {scopingTabValue === 2 && (
        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Version History
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            View the history of changes made to report attributes in this phase.
          </Typography>
          <Button 
            variant="contained" 
            onClick={() => setShowVersionHistory(true)}
            startIcon={<HistoryIcon />}
          >
            View Full Version History
          </Button>
        </Box>
        )}
      </TabPanel>

      {/* Import from Dictionary Tab */}
      <TabPanel value={tabValue} index={1}>
        {/* Step 1: Select Report */}
        <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Select Report and Schedule
                </Typography>
                
                {reportsLoading ? (
                  <LinearProgress />
                ) : (
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <FormControl fullWidth>
                        <InputLabel>Available Reports</InputLabel>
                        <Select
                          value={selectedReport}
                          onChange={(e) => {
                            setSelectedReport(e.target.value);
                            setSelectedSchedule(''); // Reset schedule when report changes
                          }}
                        >
                          {availableReports.map((report) => (
                            <MenuItem key={report} value={report}>
                              {report}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <FormControl fullWidth disabled={!selectedReport}>
                        <InputLabel>Available Schedules</InputLabel>
                        <Select
                          value={selectedSchedule}
                          onChange={(e) => setSelectedSchedule(e.target.value)}
                        >
                          {availableSchedules.map((schedule) => (
                            <MenuItem key={schedule} value={schedule}>
                              {schedule}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>
                )}
                
                {selectedReport && (
                  <Box sx={{ mt: 2 }}>
                    <Button
                      variant="outlined"
                      onClick={resetSelection}
                      size="small"
                    >
                      Reset Selection
                    </Button>
                  </Box>
                )}
              </CardContent>
            </Card>

          {/* Step 2: Select Schedule (only show if report is selected) */}
          {selectedReport && selectedSchedule && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Attributes from "{selectedReport}" - "{selectedSchedule}"
                  </Typography>

                  <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Found {dictTotal} attributes
                    </Typography>
                    <Button
                      variant="contained"
                      disabled={selectedDictEntries.length === 0}
                      onClick={handleImportFromDictionary}
                      startIcon={<ImportIcon />}
                    >
                      Import Selected ({selectedDictEntries.length})
                    </Button>
                  </Box>

                  {/* Selection Controls */}
                  <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => {
                        setSelectedDictEntries(dictionaryEntries.map(entry => entry.dict_id));
                      }}
                      disabled={dictionaryEntries.length === 0}
                    >
                      Select All on Page ({dictionaryEntries.length})
                    </Button>
                    
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={async () => {
                        try {
                          // Fetch all entries for current filter to get all dict_ids
                          setDictLoading(true);
                          const filtersForAll = {
                            ...dictFilters,
                            report_name: selectedReport,
                            schedule_name: selectedSchedule
                          };
                          const allPages = Math.ceil(dictTotal / 20);
                          const allEntries: number[] = [];
                          
                          // Fetch all pages to get all dict_ids
                          for (let page = 1; page <= allPages; page++) {
                            const response = await dataDictionaryAPI.getDataDictionary(page, 20, filtersForAll);
                            allEntries.push(...response.items.map(item => item.dict_id));
                          }
                          
                          setSelectedDictEntries(allEntries);
                        } catch (error) {
                          console.error('Error selecting all entries:', error);
                          showToast.error('Failed to select all entries');
                        } finally {
                          setDictLoading(false);
                        }
                      }}
                      disabled={dictTotal === 0 || dictLoading}
                    >
                      Select All ({dictTotal})
                    </Button>
                    
                    <Button
                      variant="outlined"
                      size="small"
                      color="error"
                      onClick={() => setSelectedDictEntries([])}
                      disabled={selectedDictEntries.length === 0}
                    >
                      Clear Selection
                    </Button>
                    
                    {selectedDictEntries.length > 0 && (
                      <Typography variant="body2" color="primary" fontWeight="medium">
                        {selectedDictEntries.length} selected
                      </Typography>
                    )}
                  </Box>

                  {/* Additional search within selected report/schedule */}
                  <Box sx={{ mb: 2 }}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Search within selected report/schedule"
                      value={dictFilters.search || ''}
                      onChange={(e) => {
                        const newFilters = { 
                          ...dictFilters, 
                          search: e.target.value,
                          report_name: selectedReport,
                          schedule_name: selectedSchedule
                        };
                        setDictFilters(newFilters);
                        loadDataDictionary(newFilters);
                      }}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <SearchIcon />
                          </InputAdornment>
                        ),
                      }}
                    />
                  </Box>

                  {/* Data Dictionary Table */}
                  {dictLoading ? (
                    <LinearProgress />
                  ) : dictionaryEntries.length === 0 ? (
                    <Alert severity="info">
                      No attributes found for the selected report and schedule combination.
                    </Alert>
                  ) : (
                    <TableContainer component={Paper} sx={{ overflowX: 'auto' }}>
                      <Table sx={{ width: '100%' }}>
                        <TableHead>
                          <TableRow>
                            <TableCell padding="checkbox">
                              <Checkbox
                                checked={
                                  dictionaryEntries.length > 0 && 
                                  dictionaryEntries.every(entry => selectedDictEntries.includes(entry.dict_id))
                                }
                                indeterminate={
                                  dictionaryEntries.some(entry => selectedDictEntries.includes(entry.dict_id)) &&
                                  !dictionaryEntries.every(entry => selectedDictEntries.includes(entry.dict_id))
                                }
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    // Add all current page items to selection
                                    const currentPageIds = dictionaryEntries.map(entry => entry.dict_id);
                                    const newSelection = Array.from(new Set([...selectedDictEntries, ...currentPageIds]));
                                    setSelectedDictEntries(newSelection);
                                  } else {
                                    // Remove current page items from selection
                                    const currentPageIds = dictionaryEntries.map(entry => entry.dict_id);
                                    setSelectedDictEntries(selectedDictEntries.filter(id => !currentPageIds.includes(id)));
                                  }
                                }}
                              />
                            </TableCell>
                            <TableCell>Line Item #</TableCell>
                            <TableCell>Line Item Name</TableCell>
                            <TableCell>Technical Name</TableCell>
                            <TableCell>MDRM</TableCell>
                            <TableCell>Mandatory</TableCell>
                            <TableCell>Format</TableCell>
                            <TableCell>Description</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {dictionaryEntries.map((entry) => (
                            <TableRow key={entry.dict_id}>
                              <TableCell padding="checkbox">
                                <Checkbox
                                  checked={selectedDictEntries.includes(entry.dict_id)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedDictEntries([...selectedDictEntries, entry.dict_id]);
                                    } else {
                                      setSelectedDictEntries(selectedDictEntries.filter(id => id !== entry.dict_id));
                                    }
                                  }}
                                />
                              </TableCell>
                              <TableCell>
                                {entry.line_item_number ? (
                                  <Typography variant="body2" fontFamily="monospace" fontWeight="medium">
                                    {entry.line_item_number}
                                  </Typography>
                                ) : (
                                  <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                    N/A
                                  </Typography>
                                )}
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2" fontWeight="medium">
                                  {entry.line_item_name}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                {entry.technical_line_item_name ? (
                                  <Typography variant="body2">
                                    {entry.technical_line_item_name}
                                  </Typography>
                                ) : (
                                  <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                    N/A
                                  </Typography>
                                )}
                              </TableCell>
                              <TableCell>
                                {entry.mdrm ? (
                                  <Typography variant="body2" fontFamily="monospace">
                                    {entry.mdrm}
                                  </Typography>
                                ) : (
                                  <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                    N/A
                                  </Typography>
                                )}
                              </TableCell>
                              <TableCell>
                                <Chip
                                  size="small"
                                  label={entry.mandatory_or_optional || 'N/A'}
                                  color={getMandatoryColor(entry.mandatory_or_optional || '')}
                                />
                              </TableCell>
                              <TableCell>
                                {entry.format_specification ? (
                                  <Typography variant="body2">
                                    {entry.format_specification}
                                  </Typography>
                                ) : (
                                  <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                    No format specified
                                  </Typography>
                                )}
                              </TableCell>
                              <TableCell>
                                {entry.description ? (
                                  <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                                    {entry.description}
                                  </Typography>
                                ) : (
                                  <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                    No description available
                                  </Typography>
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  )}

                  {/* Pagination */}
                  {dictTotal > 20 && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                      <Pagination
                        count={Math.ceil(dictTotal / 20)}
                        page={dictPage}
                        onChange={(_, newPage: number) => setDictPage(newPage)}
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
          )}
      </TabPanel>

      {/* Activity Status Tab */}
      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid size={12}>
            <ActivityStateManager
              cycleId={cycleId.toString()}
              reportId={reportId.toString()}
              phaseName="Planning"
              showControls={true}
              onPhaseComplete={() => {
                // Refresh phase status when phase is completed
                loadAttributes();
              }}
            />
          </Grid>
        </Grid>
      </TabPanel>

      {/* Documents Tab */}
      <TabPanel value={tabValue} index={3}>
        <PhaseDocumentManager
          cycleId={cycleIdNum}
          reportId={reportIdNum}
          phaseId={1} // Planning phase ID
          phaseName="Planning"
          allowedDocumentTypes={[
            'report_sample_data',
            'report_underlying_transaction_data',
            'report_source_transaction_data',
            'report_source_document'
          ]}
          requiredDocumentTypes={[
            'report_source_document'
          ]}
          title="Planning Documents"
        />
      </TabPanel>

      {/* Data Sources Tab */}
      <TabPanel value={tabValue} index={4}>
        <AddDataSourceActivity cycleId={cycleId.toString()} reportId={reportId.toString()} />
      </TabPanel>

      {/* Map PDEs Tab */}
      <TabPanel value={tabValue} index={5}>
        <MapPDEsActivity 
          cycleId={cycleId.toString()} 
          reportId={reportId.toString()} 
          activeJobId={activePDEMappingJobId}
        />
      </TabPanel>


      {/* Add Attribute Dialog */}
      <Dialog open={showAddDialog} onClose={() => setShowAddDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Attribute</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Attribute Name"
                value={newAttribute.attribute_name}
                onChange={(e) => setNewAttribute({ ...newAttribute, attribute_name: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Data Type</InputLabel>
                <Select
                  value={newAttribute.data_type}
                  onChange={(e) => setNewAttribute({ ...newAttribute, data_type: e.target.value as any })}
                >
                  <MenuItem value="string">String</MenuItem>
                  <MenuItem value="integer">Integer</MenuItem>
                  <MenuItem value="decimal">Decimal</MenuItem>
                  <MenuItem value="date">Date</MenuItem>
                  <MenuItem value="datetime">DateTime</MenuItem>
                  <MenuItem value="boolean">Boolean</MenuItem>
                  <MenuItem value="text">Text</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Mandatory Flag</InputLabel>
                <Select
                  value={newAttribute.mandatory_flag}
                  onChange={(e) => setNewAttribute({ ...newAttribute, mandatory_flag: e.target.value as any })}
                >
                  <MenuItem value="optional">Optional</MenuItem>
                  <MenuItem value="conditional">Conditional</MenuItem>
                  <MenuItem value="mandatory">Mandatory</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Information Security Classification</InputLabel>
                <Select
                  value={newAttribute.information_security_classification}
                  onChange={(e) => setNewAttribute({ ...newAttribute, information_security_classification: e.target.value as any })}
                >
                  <MenuItem value="">None</MenuItem>
                  <MenuItem value="Public">Public</MenuItem>
                  <MenuItem value="Confidential">Confidential</MenuItem>
                  <MenuItem value="Proprietary">Proprietary</MenuItem>
                  <MenuItem value="HRCI">HRCI - Highly Restricted</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Stack direction="column" spacing={1}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={newAttribute.cde_flag}
                      onChange={(e) => setNewAttribute({ ...newAttribute, cde_flag: e.target.checked })}
                    />
                  }
                  label="Critical Data Element"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={newAttribute.historical_issues_flag}
                      onChange={(e) => setNewAttribute({ ...newAttribute, historical_issues_flag: e.target.checked })}
                    />
                  }
                  label="Historical Issues"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={newAttribute.is_primary_key}
                      onChange={(e) => setNewAttribute({ ...newAttribute, is_primary_key: e.target.checked })}
                    />
                  }
                  label="Primary Key"
                />
              </Stack>
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={newAttribute.description}
                onChange={(e) => setNewAttribute({ ...newAttribute, description: e.target.value })}
              />
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Tester Notes"
                value={newAttribute.tester_notes}
                onChange={(e) => setNewAttribute({ ...newAttribute, tester_notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAddDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleCreateAttribute}
            disabled={!newAttribute.attribute_name}
          >
            Create Attribute
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Attribute Dialog */}
      <Dialog open={showEditDialog} onClose={() => setShowEditDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Attribute</DialogTitle>
        <DialogContent>
          {editingAttribute && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Attribute Name"
                  value={editingAttribute?.attribute_name || ''}
                  onChange={(e) => editingAttribute && setEditingAttribute({ ...editingAttribute, attribute_name: e.target.value })}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Data Type</InputLabel>
                  <Select
                    value={editingAttribute?.data_type || ''}
                    onChange={(e) => editingAttribute && setEditingAttribute({ ...editingAttribute, data_type: e.target.value as any })}
                  >
                    <MenuItem value="String">String</MenuItem>
                    <MenuItem value="Integer">Integer</MenuItem>
                    <MenuItem value="Decimal">Decimal</MenuItem>
                    <MenuItem value="Date">Date</MenuItem>
                    <MenuItem value="Boolean">Boolean</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Mandatory Flag</InputLabel>
                  <Select
                    value={editingAttribute?.mandatory_flag || 'optional'}
                    onChange={(e) => editingAttribute && setEditingAttribute({ ...editingAttribute, mandatory_flag: e.target.value as any })}
                  >
                    <MenuItem value="Optional">Optional</MenuItem>
                    <MenuItem value="Conditional">Conditional</MenuItem>
                    <MenuItem value="Mandatory">Mandatory</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Information Security Classification</InputLabel>
                  <Select
                    value={editingAttribute?.information_security_classification || ''}
                    onChange={(e) => editingAttribute && setEditingAttribute({ ...editingAttribute, information_security_classification: e.target.value as any })}
                  >
                    <MenuItem value="">None</MenuItem>
                    <MenuItem value="HRCI">HRCI - Highly Restricted</MenuItem>
                    <MenuItem value="Confidential">Confidential</MenuItem>
                    <MenuItem value="Proprietary">Proprietary</MenuItem>
                    <MenuItem value="Public">Public</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Approval Status</InputLabel>
                  <Select
                    value={editingAttribute?.approval_status || 'pending'}
                    onChange={(e) => editingAttribute && setEditingAttribute({ ...editingAttribute, approval_status: e.target.value as any })}
                  >
                    <MenuItem value="pending">Pending</MenuItem>
                    <MenuItem value="approved">Approved</MenuItem>
                    <MenuItem value="rejected">Rejected</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={12}>
                <Stack direction="row" spacing={2}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={editingAttribute?.cde_flag || false}
                        onChange={(e) => editingAttribute && setEditingAttribute({ ...editingAttribute, cde_flag: e.target.checked })}
                      />
                    }
                    label="Critical Data Element"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={editingAttribute?.historical_issues_flag || false}
                        onChange={(e) => editingAttribute && setEditingAttribute({ ...editingAttribute, historical_issues_flag: e.target.checked })}
                      />
                    }
                    label="Historical Issues"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={editingAttribute?.is_primary_key || false}
                        onChange={(e) => editingAttribute && setEditingAttribute({ ...editingAttribute, is_primary_key: e.target.checked })}
                      />
                    }
                    label="Primary Key"
                  />
                </Stack>
              </Grid>
              <Grid size={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Description"
                  value={editingAttribute?.description || ''}
                  onChange={(e) => editingAttribute && setEditingAttribute({ ...editingAttribute, description: e.target.value })}
                />
              </Grid>
              <Grid size={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Tester Notes"
                  value={editingAttribute?.tester_notes || ''}
                  onChange={(e) => editingAttribute && setEditingAttribute({ ...editingAttribute, tester_notes: e.target.value })}
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEditDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleUpdateAttribute}
          >
            Update Attribute
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onClose={() => setShowDeleteDialog(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete {selectedAttributes.length} selected attribute{selectedAttributes.length === 1 ? '' : 's'}?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            color="error"
            onClick={handleDeleteAttributes}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Version History Viewer */}
      {showVersionHistory && (
        <VersionHistoryViewer
          entityType="report_attribute"
          entityId={reportId.toString()}
          open={showVersionHistory}
          onClose={() => setShowVersionHistory(false)}
          canRevert={false}
        />
      )}
    </Container>
  );
};

export default PlanningPage; 