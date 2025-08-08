/**
 * Enhanced Data Profiling Page with Individual Rule Approval/Decline
 * Attribute-centric view with expandable rules and versioning support
 */
import React, { useState, useEffect } from 'react';
import { usePhaseStatus, getStatusColor, getStatusIcon, formatStatusText } from '../../hooks/useUnifiedStatus';
import { DynamicActivityCards } from '../../components/phase/DynamicActivityCards';
import { ReportMetadataCard } from '../../components/common/ReportMetadataCard';
import { useUniversalAssignments } from '../../hooks/useUniversalAssignments';
import { UniversalAssignmentAlert } from '../../components/UniversalAssignmentAlert';
import { ReportOwnerFeedback } from '../../components/data-profiling/ReportOwnerFeedback';
import { ReportOwnerFeedbackChecker } from '../../components/data-profiling/ReportOwnerFeedbackChecker';
import {
  Box,
  Typography,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Alert,
  LinearProgress,
  Card,
  CardContent,
  Grid,
  Divider,
  Tabs,
  Tab,
  Badge,
  Chip,
  Container,
  CircularProgress
} from '@mui/material';
import {
  Upload,
  Settings,
  PlayArrow,
  Assessment,
  CheckCircle,
  Visibility,
  DataThresholding as DataProfilingIcon,
  BusinessCenter as BusinessIcon,
  Person as PersonIcon,
  Warning as WarningIcon,
  CloudUpload as UploadIcon,
  Analytics as AnalyticsIcon,
  Speed as SpeedIcon,
  Assignment as AssignmentIcon,
  ExpandMore,
  ExpandLess,
  Rule as RuleIcon,
  RateReview as ReviewIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import CompressedRulesTable from '../../components/data-profiling/CompressedRulesTable';
import ReportOwnerRulesApproval from '../../components/data-profiling/ReportOwnerRulesApproval';
import { dataProfilingApi } from '../../api/dataProfiling';
import { BatchProgressIndicator } from '../../components/common/BatchProgressIndicator';
import ExecutionResultsTable from '../../components/data-profiling/ExecutionResultsTable';
import FileUploadSection from '../../components/data-profiling/FileUploadSection';
import PhaseDocumentManager from '../../components/documents/PhaseDocumentManager';
import api from '../../api/client';

interface DataProfilingPhase {
  phase_id: number;
  cycle_id: number;
  report_id: number;
  status: string;
  started_at: string;
  completed_at?: string;
  tester_review_status?: string;
  report_owner_approval_status?: string;
}

interface WorkflowStats {
  total_attributes: number;
  total_rules: number;
  approved_rules: number;
  rejected_rules: number;
  pending_rules: number;
  needs_revision_rules: number;
  completion_percentage: number;
  can_proceed_to_execution: boolean;
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

interface DataProfilingMetrics {
  total_attributes: number;
  attributes_with_rules: number;
  total_profiling_rules: number;
  rules_generated: number;
  attributes_with_anomalies: number;
  cdes_with_anomalies: number;
  days_elapsed: number;
  completion_percentage: number;
  can_start_phase: boolean;
  can_complete_phase: boolean;
  phase_status: string;
  files_uploaded: number;
  started_at?: string;
  completed_at?: string;
}

const DataProfilingEnhanced: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [activeStep, setActiveStep] = useState(0);
  const [activeTab, setActiveTab] = useState(0);
  const [dataProfilingPhase, setDataProfilingPhase] = useState<DataProfilingPhase | null>(null);
  const [workflowStats, setWorkflowStats] = useState<WorkflowStats | null>(null);
  const [reportInfo, setReportInfo] = useState<ReportInfo | null>(null);
  const [phaseMetrics, setPhaseMetrics] = useState<DataProfilingMetrics | null>(null);
  const [activeBatchJob, setActiveBatchJob] = useState<string | null>(null);
  const [hasReportOwnerFeedback, setHasReportOwnerFeedback] = useState(false);
  const [currentVersionId, setCurrentVersionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasReportOwnerAssignment, setHasReportOwnerAssignment] = useState(false);
  const [workflowStepFromAssignment, setWorkflowStepFromAssignment] = useState<string | null>(null);
  const [executionInProgress, setExecutionInProgress] = useState(false); // Track profiling execution
  const [executionProgress, setExecutionProgress] = useState(0); // Execution progress percentage
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set()); // Track expanded workflow cards
  const [resultsRefreshKey, setResultsRefreshKey] = useState(0); // Force refresh of execution results
  const [executionResults, setExecutionResults] = useState<any[]>([]); // Store execution results

  const cycle_id = parseInt(cycleId || '0');
  const report_id = parseInt(reportId || '0');
  
  // Unified status system - Note: Data Profiling maps to "Testing" phase
  const { data: unifiedPhaseStatus, isLoading: statusLoading, refetch: refetchStatus } = usePhaseStatus('Data Profiling', cycle_id, report_id);
  
  // Universal Assignments integration
  const {
    assignments,
    hasAssignment,
    canDirectAccess,
    acknowledgeAssignment,
    startAssignment,
    completeAssignment,
  } = useUniversalAssignments({
    phase: 'Data Profiling',
    cycleId: cycle_id,
    reportId: report_id,
  });
  
  // Use localStorage to persist workflow advancement state across page reloads
  const workflowAdvancedKey = `workflowAdvanced_${cycle_id}_${report_id}`;
  
  // Debug: Check for reset flag in URL
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('resetWorkflow') === 'true') {
    console.log('🔄 RESET: Clearing workflow advanced state from localStorage');
    localStorage.removeItem(workflowAdvancedKey);
  }
  
  const initialWorkflowAdvanced = localStorage.getItem(workflowAdvancedKey) === 'true';
  console.log(`🔋 Initial localStorage state for ${workflowAdvancedKey}: ${initialWorkflowAdvanced}`);
  
  const [workflowAdvanced, setWorkflowAdvancedState] = useState(initialWorkflowAdvanced);
  
  const setWorkflowAdvanced = (value: boolean) => {
    setWorkflowAdvancedState(value);
    localStorage.setItem(workflowAdvancedKey, value.toString());
    console.log(`💾 Workflow advanced state saved to localStorage: ${value}`);
  };

  const toggleCardExpansion = (cardIndex: number) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(cardIndex)) {
      newExpanded.delete(cardIndex);
    } else {
      newExpanded.add(cardIndex);
    }
    setExpandedCards(newExpanded);
  };

  const profilingSteps = [
    {
      label: 'Generate Profiling Rules',
      description: 'LLM generates validation rules for each attribute',
      icon: <Settings />,
      status: 'completed'
    },
    {
      label: 'Review & Approve Rules',
      description: 'Tester and Report Owner review individual rules',
      icon: <Visibility />,
      status: 'active'
    },
    {
      label: 'Execute Profiling',
      description: 'Run approved rules against the dataset',
      icon: <PlayArrow />,
      status: 'pending'
    },
    {
      label: 'Analyze Results',
      description: 'Review data quality findings and violations',
      icon: <Assessment />,
      status: 'pending'
    },
    {
      label: 'Final Approval',
      description: 'Report Owner approves profiling completion',
      icon: <CheckCircle />,
      status: 'pending'
    }
  ];

  useEffect(() => {
    const loadInitialData = async () => {
      // Check localStorage state first
      const storedWorkflowAdvanced = localStorage.getItem(workflowAdvancedKey) === 'true';
      console.log(`📱 localStorage workflow state: ${storedWorkflowAdvanced}`);
      
      // First check phase status directly from API to determine current state
      try {
        const phaseResponse = await dataProfilingApi.getStatus(cycle_id, report_id);
        console.log('🔍 Initial phase status check:', phaseResponse.phase_status);
        
        const shouldSkipAdvancement = phaseResponse.phase_status === 'Ready for Execution' || storedWorkflowAdvanced;
        console.log('🔄 Advancement decision:', {
          phaseStatus: phaseResponse.phase_status,
          storedWorkflowAdvanced,
          currentWorkflowAdvanced: workflowAdvanced,
          shouldSkipAdvancement
        });
        
        if (shouldSkipAdvancement) {
          console.log('🔄 Page load: Workflow already advanced - setting state directly');
          setWorkflowAdvanced(true);
          setActiveStep(2); // Execute Profiling step
          
          // Load all data without advancement checks
          await loadPhaseMetrics();
          await loadWorkflowStats();
          await loadReportInfo();
          await loadExecutionResults();
          // Skip checkReportOwnerAssignment() - workflow already advanced
          
          console.log('✅ Page load complete: Workflow advanced state preserved, no alerts shown');
          return; // Skip normal loading flow completely
        }
      } catch (error) {
        console.log('⚠️ Could not check initial phase status, proceeding with normal flow');
      }
      
      // Normal loading flow for non-advanced workflows
      await loadPhaseMetrics();
      await loadWorkflowStats();
      await loadReportInfo();
      await checkReportOwnerAssignment();
      await checkTesterFeedbackAvailable();
    };
    
    loadInitialData();
  }, [cycle_id, report_id]);

  const loadWorkflowStats = async () => {
    const endpoint = `/data-profiling/cycles/${cycle_id}/reports/${report_id}/workflow-status`;
    console.log('🔗 Calling workflow stats API:', endpoint);
    
    try {
      const response = await api.get(endpoint);
      console.log('✅ Workflow stats API response:', response.data);
      console.log('📊 Approved rules from API:', response.data.approved_rules);
      console.log('🔢 Full API response object:', JSON.stringify(response.data, null, 2));
      setWorkflowStats(response.data);
    } catch (error: any) {
      console.error('❌ Error fetching workflow stats:', error.response?.status, error.response?.data);
      // Don't use hardcoded fallback values - just set empty stats
      setWorkflowStats({
        total_attributes: 0,
        total_rules: 0,
        approved_rules: 0,
        rejected_rules: 0,
        pending_rules: 0,
        needs_revision_rules: 0,
        completion_percentage: 0,
        can_proceed_to_execution: false
      });
    }
  };

  const loadReportInfo = async () => {
    try {
      // Get report info from cycle-reports endpoint which includes names
      const response = await api.get(`/cycle-reports/${cycle_id}/reports/${report_id}`);
      console.log('📋 Data Profiling Report Info Response:', response.data);
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
      // Fallback to basic info
      setReportInfo({
        report_id: report_id,
        report_name: 'Report ' + report_id,
        lob: 'Unknown',
        assigned_tester: 'Unknown',
        report_owner: 'Unknown'
      });
    }
  };

  const loadExecutionResults = async () => {
    try {
      const response = await dataProfilingApi.getResults(cycle_id, report_id);
      setExecutionResults(response || []);
      console.log(`📊 Loaded ${response?.length || 0} execution results`);
    } catch (error) {
      console.error('Error loading execution results:', error);
      setExecutionResults([]);
    }
  };

  const loadPhaseMetrics = async () => {
    try {
      // Use unified status metadata if available
      if (unifiedPhaseStatus?.metadata) {
        console.log('📊 Using unified status metadata:', unifiedPhaseStatus.metadata);
        setPhaseMetrics({
          total_attributes: unifiedPhaseStatus.metadata.total_attributes || 0,
          attributes_with_rules: unifiedPhaseStatus.metadata.attributes_with_rules || 0,
          total_profiling_rules: unifiedPhaseStatus.metadata.total_profiling_rules || 0,
          rules_generated: unifiedPhaseStatus.metadata.rules_generated || 0,
          attributes_with_anomalies: unifiedPhaseStatus.metadata.attributes_with_anomalies || 0,
          cdes_with_anomalies: unifiedPhaseStatus.metadata.cdes_with_anomalies || 0,
          days_elapsed: unifiedPhaseStatus.metadata.days_elapsed || 0,
          completion_percentage: unifiedPhaseStatus.metadata.completion_percentage || 0,
          can_start_phase: unifiedPhaseStatus.can_proceed_to_next || false,
          can_complete_phase: unifiedPhaseStatus.can_proceed_to_next || false,
          phase_status: unifiedPhaseStatus.phase_status || 'Not Started',
          files_uploaded: 0,
        });
        return;
      }
      
      // Fallback to direct API if unified status not available
      const response = await dataProfilingApi.getStatus(cycle_id, report_id);
      console.log('📊 Phase metrics response:', response);
      console.log('🔧 DEBUG can_complete:', response.can_complete);
      console.log('🔧 DEBUG profiling_executed_at:', response.profiling_executed_at);
      console.log('🔧 DEBUG phase_status:', response.phase_status);
      
      setPhaseMetrics({
        total_attributes: response.total_attributes || 0,
        attributes_with_rules: response.attributes_with_rules || 0,
        total_profiling_rules: response.total_profiling_rules || 0,
        rules_generated: response.rules_generated || 0,
        attributes_with_anomalies: response.attributes_with_anomalies || 0,
        cdes_with_anomalies: response.cdes_with_anomalies || 0,
        days_elapsed: response.days_elapsed || 0,
        completion_percentage: response.completion_percentage || 0,
        can_start_phase: response.can_start_phase || false,
        can_complete_phase: response.can_complete || false,
        phase_status: response.phase_status || 'Not Started',
        files_uploaded: response.files_uploaded || 0,
        started_at: response.started_at,
        completed_at: response.completed_at
      });
      
      console.log('🔧 DEBUG set can_complete_phase to:', response.can_complete || false);
      
      // Check if workflow should already be marked as advanced based on phase status
      if (response.phase_status === 'Ready for Execution' && !workflowAdvanced) {
        console.log('🔄 Detected workflow already advanced on page load (silent restoration)');
        setWorkflowAdvanced(true);
        setActiveStep(2); // Move to "Execute Profiling" step
        // No notification popup - this is restoring existing state
      }
    } catch (error) {
      console.error('Error loading phase metrics:', error);
      // Don't use hardcoded fallback values - just set empty metrics
      setPhaseMetrics({
        total_attributes: 0,
        attributes_with_rules: 0,
        total_profiling_rules: 0,
        rules_generated: 0,
        attributes_with_anomalies: 0,
        cdes_with_anomalies: 0,
        days_elapsed: 1,
        completion_percentage: 75,
        can_start_phase: true,
        can_complete_phase: false,
        phase_status: 'In Progress',
        files_uploaded: 1,
        started_at: new Date().toISOString(),
        completed_at: undefined
      });
    }
  };

  const checkReportOwnerAssignment = async () => {
    console.log('🔍 Checking report owner assignment for user:', user?.role, 'cycle:', cycle_id, 'report:', report_id);
    
    // STOP if workflow is already advanced - no need to check assignments
    if (workflowAdvanced) {
      console.log('ℹ️ Workflow already advanced - skipping assignment check');
      return;
    }
    
    // Check for any existing assignments regardless of user role
    try {
      const existingAssignments = await api.get('/universal-assignments/assignments');
      console.log('📋 Total assignments found:', existingAssignments.data.length);
      
      // Debug: Log all assignments for this cycle/report
      const relevantAssignments = existingAssignments.data.filter((a: any) => 
        a.context_data?.cycle_id === cycle_id &&
        a.context_data?.report_id === report_id
      );
      console.log('🔍 Assignments for this cycle/report:', relevantAssignments.length, relevantAssignments);
      
      const assignment = existingAssignments.data.find((a: any) => {
        const matches = a.context_data?.cycle_id === cycle_id &&
          a.context_data?.report_id === report_id &&
          (a.context_data?.phase === 'data_profiling' || a.context_data?.phase === undefined) && // Allow undefined phase
          a.assignment_type === 'Rule Approval' &&
          ['Assigned', 'Acknowledged', 'In Progress', 'Completed'].includes(a.status);
        
        if (!matches && a.context_data?.cycle_id === cycle_id && a.context_data?.report_id === report_id) {
          console.log('❌ Assignment excluded:', {
            phase: a.context_data?.phase,
            type: a.assignment_type,
            status: a.status
          });
        }
        
        return matches;
      });
      
      console.log('🔍 Assignment search result:', assignment ? 'Found' : 'Not found');
      
      if (assignment) {
        setWorkflowStepFromAssignment(assignment.context_data?.workflow_step || null);
        console.log('✅ Found assignment with workflow step:', assignment.context_data?.workflow_step);
        
        // An assignment exists regardless of user role
        setHasReportOwnerAssignment(true);
        console.log('✅ Report Owner assignment exists for this report');
        
        // If user is a Report Owner, check if they have access to this assignment
        if (user?.role === 'Report Owner') {
          console.log('🔍 User is Report Owner, checking assigned rules API...');
          try {
            const rulesResponse = await dataProfilingApi.getAssignedRulesForApproval(cycle_id, report_id);
            console.log('✅ Report Owner has access to assignment, rules count:', rulesResponse.rules?.length || 0);
          } catch (error: any) {
            console.log('❌ Report Owner does not have access to this assignment:', error.response?.status, error.response?.data);
          }
        }
      } else {
        setHasReportOwnerAssignment(false);
        console.log('ℹ️ No active assignment found for this report');
      }
    } catch (error: any) {
      setHasReportOwnerAssignment(false);
      console.log('❌ Error checking assignments:', error);
    }
  };

  const checkTesterFeedbackAvailable = async () => {
    // This function is no longer needed since we removed TesterFeedbackView
    // All functionality is now in CompressedRulesTable
    return;
  };

  const checkAndAdvanceWorkflow = async (feedbackResponse: any) => {
    try {
      console.log('🔄 Checking workflow advancement conditions...');
      
      // IMMEDIATE CHECK: If workflow already advanced, abort completely
      if (workflowAdvanced) {
        console.log('🛑 ABORT: Workflow already advanced - exiting checkAndAdvanceWorkflow immediately');
        return;
      }
      
      // Check current workflow status
      const workflowResponse = await api.get(`/data-profiling/cycles/${cycle_id}/reports/${report_id}/workflow-status`);
      const currentWorkflowStep = workflowStepFromAssignment;
      
      console.log('📊 Current workflow status:', {
        step: currentWorkflowStep,
        stats: workflowResponse.data,
        assignmentCompleted: feedbackResponse.assignment_completed,
        assignmentStatus: feedbackResponse.assignment_status,
        workflowAdvancedState: workflowAdvanced
      });
      
      // Check if we should advance workflow - either in active review step OR assignment already completed
      const shouldAdvanceWorkflow = currentWorkflowStep === 'tester_approved_rules_for_report_owner_review' || 
                                   feedbackResponse.assignment_completed === true;
      
      if (shouldAdvanceWorkflow) {
        // Check rule statuses
        const approvedRules = feedbackResponse.rules.filter((rule: any) => rule.report_owner_status === 'APPROVED');
        const rejectedRules = feedbackResponse.rules.filter((rule: any) => rule.report_owner_status === 'REJECTED');
        const pendingRules = feedbackResponse.rules.filter((rule: any) => rule.report_owner_status === 'PENDING');
        
        // Only advance workflow if ALL rules are approved (no rejected or pending)
        if (approvedRules.length > 0 && rejectedRules.length === 0 && pendingRules.length === 0) {
          console.log(`🚀 All ${approvedRules.length} rules approved by report owner - advancing workflow!`);
          
          // Complete the rule approval assignment
          await completeRuleApprovalAssignment();
          
          // Update workflow step to next phase 
          await advanceToNextWorkflowStep();
          
          // Mark workflow as advanced IMMEDIATELY
          setWorkflowAdvanced(true);
          setActiveStep(2); // Move to "Execute Profiling" step immediately
          
          // Update UI to reflect changes
          setTimeout(() => {
            loadWorkflowStats();
            loadPhaseMetrics();
            loadExecutionResults();
            checkReportOwnerAssignment();
            console.log('✅ UI updated after workflow advancement');
          }, 500); // Reduced timeout
          
          // Show success notification (only if this is the first time advancing)
          if (!workflowAdvanced) {
            console.log('🎉 First time workflow advancement - showing alert');
            alert(`🎉 Workflow Advanced!\n\nAll rules have been approved by the Report Owner.\nData Profiling workflow is now ready for execution.\n\n✅ ${approvedRules.length} rules approved\n🚀 Ready to proceed to profiling execution`);
          } else {
            console.log('⚠️ Workflow already advanced - NOT showing alert');
          }
        } else if (rejectedRules.length > 0) {
          console.log(`⚠️ ${rejectedRules.length} rules rejected by Report Owner - Tester needs to review feedback`);
          // Show different message for rejected rules
          if (!workflowAdvanced) {
            alert(`⚠️ Report Owner Review Complete\n\n${approvedRules.length} rules approved\n${rejectedRules.length} rules rejected\n\nPlease review the Report Owner's feedback and update the rejected rules.`);
          }
          
          console.log('✅ Workflow advanced successfully!');
        } else {
          console.log('⚠️ No approved rules found, cannot advance workflow yet');
        }
      } else {
        console.log('ℹ️ Workflow advancement conditions not met:', {
          currentStep: currentWorkflowStep,
          assignmentCompleted: feedbackResponse.assignment_completed,
          shouldAdvance: shouldAdvanceWorkflow
        });
      }
      
    } catch (error: any) {
      console.error('❌ Error checking/advancing workflow:', error);
    }
  };

  const completeRuleApprovalAssignment = async () => {
    try {
      // Find and complete the active rule approval assignment
      const assignments = await api.get('/universal-assignments/assignments');
      const ruleApprovalAssignment = assignments.data.find((a: any) => 
        a.context_data?.cycle_id === cycle_id &&
        a.context_data?.report_id === report_id &&
        a.context_data?.phase === 'data_profiling' &&
        a.assignment_type === 'Rule Approval' &&
        ['Assigned', 'Acknowledged', 'In Progress'].includes(a.status)
      );
      
      if (ruleApprovalAssignment) {
        console.log('📋 Completing rule approval assignment:', ruleApprovalAssignment.assignment_id);
        
        await api.put(`/universal-assignments/assignments/${ruleApprovalAssignment.assignment_id}/complete`, {
          completion_notes: 'All rules have been reviewed and decided by report owner. Ready to proceed with profiling execution.',
          context_updates: {
            workflow_step: 'ready_for_profiling_execution'
          }
        });
        
        console.log('✅ Rule approval assignment completed');
      }
    } catch (error: any) {
      console.error('❌ Error completing rule approval assignment:', error);
    }
  };

  const advanceToNextWorkflowStep = async () => {
    try {
      console.log('🔄 Advancing to next workflow step...');
      
      // Update the data profiling phase status to indicate readiness for execution
      await api.put(`/data-profiling/cycles/${cycle_id}/reports/${report_id}/advance-workflow`, {
        current_step: 'rule_approval_complete',
        next_step: 'ready_for_execution',
        advancement_reason: 'All rules approved by report owner'
      });
      
      console.log('✅ Workflow step advanced');
    } catch (error: any) {
      console.error('❌ Error advancing workflow step:', error);
      // Don't throw - let the UI continue to update even if this fails
    }
  };

  const handleRuleStatusChange = () => {
    // Refresh workflow stats when rule status changes
    loadWorkflowStats();
    loadPhaseMetrics();
    checkTesterFeedbackAvailable(); // Also check if feedback is now available
    checkReportOwnerAssignment(); // Also check if assignment status has changed
  };

  const canUserApprove = () => {
    return user?.role && ['Report Owner Executive', 'Test Executive', 'Admin'].includes(user.role);
  };

  const canUserEdit = () => {
    return user?.role && ['Tester', 'Test Executive'].includes(user.role);
  };

  const executeProfilingRules = async () => {
    try {
      setLoading(true);
      setExecutionInProgress(true);
      setExecutionProgress(0);
      setError(null);
      
      console.log('🚀 Starting profiling execution...', {
        cycle_id,
        report_id,
        currentVersionId,
        hasVersionId: !!currentVersionId
      });
      
      // Remove the version ID check - the backend can handle finding the appropriate version
      // if (!currentVersionId) {
      //   console.error('❌ No version ID available for execution');
      //   setError('No version ID available. Please ensure rules have been generated.');
      //   return;
      // }
      
      // Start execution - backend will use latest version if no versionId provided
      console.log('📡 Calling executeProfiling API...');
      const response = await dataProfilingApi.executeProfiling(cycle_id, report_id, currentVersionId);
      console.log('📥 Execute profiling response:', response);
      
      if (response.job_id) {
        console.log('📋 Profiling job started:', response.job_id);
        setActiveBatchJob(response.job_id);
        
        // Track progress if job started
        await trackExecutionProgress(response.job_id);
      } else if (response.success) {
        console.log('✅ Profiling completed immediately');
        setExecutionProgress(100);
        
        // Switch to Execution Results tab (accounting for conditional Report Owner Feedback tab)
        const executionResultsTabIndex = hasReportOwnerFeedback ? 3 : 2;
        setActiveTab(executionResultsTabIndex);
        
        // Show success notification
        alert('🎉 Profiling Execution Complete!\n\nAll approved rules have been executed successfully.\nYou can now review the profiling results and quality scores.');
        
        // Refresh workflow stats
        await loadWorkflowStats();
        await loadPhaseMetrics();
        
        // Force refresh of execution results
        setResultsRefreshKey(prev => prev + 1);
      } else {
        setError(response.message || 'Failed to execute profiling rules');
      }
    } catch (error: any) {
      console.error('❌ Error executing profiling rules:', error);
      console.error('Error details:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
        stack: error.stack
      });
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to execute profiling rules';
      setError(errorMessage);
      alert(`Error executing profiling: ${errorMessage}`);
    } finally {
      setLoading(false);
      setExecutionInProgress(false);
    }
  };

  const trackExecutionProgress = async (jobId: string) => {
    console.log('📊 Tracking execution progress for job:', jobId);
    
    const checkProgress = async () => {
      try {
        const jobStatus = await dataProfilingApi.checkJobStatus(jobId);
        console.log('📈 Job status:', jobStatus);
        
        if (jobStatus.status === 'completed') {
          setExecutionProgress(100);
          setActiveBatchJob(null);
          
          // Show success notification (only here, not in immediate path above)
          alert('🎉 Profiling Execution Complete!\n\nAll approved rules have been executed successfully.\nYou can now review the profiling results and quality scores.');
          
          // Switch to Execution Results tab (accounting for conditional Report Owner Feedback tab)
          const executionResultsTabIndex = hasReportOwnerFeedback ? 3 : 2;
          setActiveTab(executionResultsTabIndex);
          
          // Refresh data and force re-render of ExecutionResultsTable
          await loadWorkflowStats();
          await loadPhaseMetrics();
          
          // Force refresh of execution results
          setResultsRefreshKey(prev => prev + 1);
          
          return true; // Stop tracking
        } else if (jobStatus.status === 'failed') {
          setError('Profiling execution failed. Please try again.');
          setActiveBatchJob(null);
          return true; // Stop tracking
        } else if (jobStatus.status === 'cancelled') {
          console.log('Job was cancelled, stopping tracking');
          setActiveBatchJob(null);
          setExecutionProgress(0);
          return true; // Stop tracking
        } else {
          // Update progress based on job status
          const progress = jobStatus.progress || Math.min(95, executionProgress + 10);
          setExecutionProgress(progress);
          return false; // Continue tracking
        }
      } catch (error) {
        console.error('Error checking job status:', error);
        return false; // Continue tracking
      }
    };
    
    // Poll every 5 seconds
    const pollInterval = setInterval(async () => {
      const shouldStop = await checkProgress();
      if (shouldStop) {
        clearInterval(pollInterval);
        setExecutionInProgress(false);
      }
    }, 5000);
    
    // Initial check
    setTimeout(() => checkProgress(), 1000);
  };

  const startDataProfilingPhase = async () => {
    try {
      setLoading(true);
      const response = await dataProfilingApi.startPhase(cycle_id, report_id);
      
      if (response.message) {
        setError(null);
        await loadWorkflowStats();
        await loadPhaseMetrics();
      } else {
        setError('Failed to start data profiling phase');
      }
    } catch (error: any) {
      console.error('Error starting data profiling phase:', error);
      setError(error.response?.data?.detail || 'Failed to start data profiling phase');
    } finally {
      setLoading(false);
    }
  };

  const generateRules = async () => {
    try {
      setLoading(true);
      const response = await dataProfilingApi.generateRules(cycle_id, report_id, 'claude');
      
      if (response.message || response.job_id) {
        setError(null);
        // Show success message and start tracking the job
        console.log('Rule generation started:', response.message);
        setActiveBatchJob(response.job_id);
        
        // Store job ID for version tracking in CompressedRulesTable
        if (response.job_id) {
          const storageKey = `data-profiling-job-${cycle_id}-${report_id}`;
          console.log('📝 Storing job ID in localStorage:', response.job_id, 'with key:', storageKey);
          localStorage.setItem(storageKey, response.job_id);
          // Verify it was stored
          const storedValue = localStorage.getItem(storageKey);
          console.log('✅ Verified stored value:', storedValue);
        }
        
        await loadWorkflowStats();
        await loadPhaseMetrics();
      } else {
        setError('Failed to generate profiling rules');
      }
    } catch (error: any) {
      console.error('Error generating profiling rules:', error);
      setError(error.response?.data?.detail || 'Failed to generate profiling rules');
    } finally {
      setLoading(false);
    }
  };

  const completeDataProfilingPhase = async () => {
    try {
      setLoading(true);
      const response = await dataProfilingApi.completePhase(cycle_id, report_id);
      
      if (response.success) {
        setError(null);
        await loadWorkflowStats();
        await loadPhaseMetrics();
      } else {
        setError(response.message || 'Failed to complete data profiling phase');
      }
    } catch (error: any) {
      console.error('Error completing data profiling phase:', error);
      setError(error.response?.data?.detail || 'Failed to complete data profiling phase');
    } finally {
      setLoading(false);
    }
  };

  const handleActivityAction = async (activity: any, action: string) => {
    console.log('🎯 handleActivityAction called:', {
      activityName: activity.name,
      activityCode: activity.activity_code,
      action: action,
      status: activity.status,
      canComplete: activity.can_complete,
      canStart: activity.can_start
    });
    
    try {
      // Handle regenerate action for Generate LLM Data Profiling Rules
      if (action === 'regenerate' && (
        activity.name === 'Generate LLM Data Profiling Rules' ||
        activity.name === 'Generate Data Profile' ||
        activity.name.toLowerCase().includes('generate') ||
        activity.activity_code === 'generate_profile'
      )) {
        console.log('Regenerating data profiling rules...');
        await generateRules();
        return;
      }
      
      // Handle regenerate (re-run) action for Execute Data Profiling
      if (action === 'regenerate' && (
        activity.name === 'Execute Data Profiling' ||
        activity.name === 'Execute Profiling' ||
        activity.name.toLowerCase().includes('execute') ||
        activity.activity_code === 'execute_profiling'
      )) {
        console.log('Re-running data profiling execution...');
        await executeProfilingRules();
        return;
      }
      
      // Handle complete action for Execute Data Profiling - should trigger execution
      if (action === 'complete' && (
        activity.name === 'Execute Data Profiling' ||
        activity.name === 'Execute Profiling' ||
        activity.name.toLowerCase().includes('execute') ||
        activity.activity_code === 'execute_profiling'
      )) {
        console.log('Executing data profiling rules...');
        await executeProfilingRules();
        return;
      }
      
      // Handle start action for Generate LLM Data Profiling Rules
      if (action === 'start' && (
        activity.name === 'Generate LLM Data Profiling Rules' ||
        activity.name === 'Generate Data Profile' ||
        activity.name.toLowerCase().includes('generate')
      )) {
        console.log('Starting data profiling rules generation...');
        // First mark the activity as started
        const response = await api.post(`/activity-management/activities/${activity.activity_id}/start`, {
          cycle_id: cycle_id,
          report_id: report_id,
          phase_name: 'Data Profiling'
        });
        console.log('Activity started:', response.data);
        
        // Then trigger the rule generation
        await generateRules();
        return;
      }
      
      // Check if activity is already in the target state to avoid errors
      if (action === 'start' && activity.status === 'active') {
        console.log(`Activity ${activity.name} is already active, skipping start action`);
        return;
      }
      if (action === 'complete' && activity.status === 'completed') {
        console.log(`Activity ${activity.name} is already completed, skipping complete action`);
        return;
      }
      
      // Make the API call to start/complete the activity
      const endpoint = action === 'start' ? 'start' : 'complete';
      const response = await api.post(`/activity-management/activities/${activity.activity_id}/${endpoint}`, {
        cycle_id: cycle_id,
        report_id: report_id,
        phase_name: 'Data Profiling'
      });
      
      // Special handling: If completing "Review and Approve Rules" activity, check if version should be approved
      if (action === 'complete' && (
        activity.name === 'Review and Approve Rules' ||
        activity.name.toLowerCase().includes('review') ||
        activity.activity_code === 'review_approve_rules'
      )) {
        console.log('📋 Completing Review and Approve Rules activity - checking if version should be approved');
        try {
          // Call endpoint to check and approve version if all decisions match
          const approvalResponse = await api.post(`/data-profiling/cycles/${cycle_id}/reports/${report_id}/check-and-approve-version`);
          if (approvalResponse.data.version_approved) {
            console.log('✅ Version automatically approved - all tester and report owner decisions match');
            alert('✅ Version Approved!\n\nAll tester and report owner decisions match.\nThe version has been automatically approved and is ready for execution.');
          } else if (approvalResponse.data.mismatches) {
            console.log('⚠️ Version not approved - decisions do not match', approvalResponse.data);
          }
        } catch (error) {
          console.error('Error checking version approval:', error);
          // Don't fail the activity completion if version approval check fails
        }
      }
      
      // Show success message from backend or default
      const message = response.data.message || activity.metadata?.success_message || `${action === 'start' ? 'Started' : 'Completed'} ${activity.name}`;
      console.log('SUCCESS:', message);
      setError(null);
      
      // Special handling for phase_start activities - immediately complete them
      if (action === 'start' && activity.metadata?.activity_type === 'phase_start') {
        console.log('Auto-completing phase_start activity:', activity.name);
        await new Promise(resolve => setTimeout(resolve, 200));
        
        try {
          await api.post(`/activity-management/activities/${activity.activity_id}/complete`, {
            cycle_id: cycle_id,
            report_id: report_id,
            phase_name: 'Data Profiling'
          });
          console.log('SUCCESS:', `${activity.name} completed`);
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
      
      // Force refresh of all data
      await loadWorkflowStats();
      await loadPhaseMetrics();
      await refetchStatus(); // Refresh unified phase status to update activity cards
    } catch (error: any) {
      console.error('Error handling activity action:', error);
      setError(error.response?.data?.detail || `Failed to ${action} activity`);
    } finally {
      setLoading(false);
    }
  };

  const markExecutionComplete = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔧 Manually marking execution as complete...');
      const response = await dataProfilingApi.markExecutionComplete(cycle_id, report_id);
      
      if (response.success) {
        console.log('✅ Execution marked as complete');
        
        // Show success notification
        alert(`✅ Execution Marked Complete!\n\n${response.message}\nResults: ${response.results_count} profiling results available\n\nYou can now complete the Data Profiling Phase.`);
        
        // Reload metrics to update UI
        await loadWorkflowStats();
        await loadPhaseMetrics();
        await loadExecutionResults();
      } else {
        setError(response.message || 'Failed to mark execution as complete');
      }
    } catch (error: any) {
      console.error('❌ Error marking execution complete:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to mark execution as complete';
      setError(errorMessage);
      alert(`❌ Error: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };


  if (loading && !dataProfilingPhase) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
      </Box>
    );
  }

  // Report Owner Assignment View - Show only rule approval interface
  console.log('📊 Render decision - User role:', user?.role, 'hasReportOwnerAssignment:', hasReportOwnerAssignment);
  
  if (user?.role === 'Report Owner' && hasReportOwnerAssignment) {
    console.log('✅ Rendering Report Owner Assignment View');
    return (
      <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
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

        {/* Report Metadata Section - Simplified for Report Owner */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ py: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
              {/* Left side - Report title and assignment info */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <AssignmentIcon color="primary" fontSize="large" />
                <Box>
                  <Typography variant="h5" component="h1" sx={{ fontWeight: 'medium' }}>
                    Rules Approval Assignment
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Review and approve data profiling rules for {reportInfo?.report_name || `Report ${report_id}`}
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

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Report Owner Rules Approval - No tabs, no workflow, just the assignment */}
        <ReportOwnerRulesApproval
          cycleId={cycle_id}
          reportId={report_id}
          onAssignmentCompleted={() => {
            // Navigate back to dashboard with success message when assignment is completed
            navigate('/dashboard', {
              state: {
                message: 'Assignment completed successfully! All rules have been reviewed.',
                severity: 'success'
              }
            });
          }}
        />

        {/* Back Button */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-start', mt: 3 }}>
          <Button variant="outlined" onClick={() => window.history.back()}>
            Back to Dashboard
          </Button>
        </Box>
      </Container>
    );
  }

  // Regular Data Profiling View for Testers and other roles
  console.log('🔧 Rendering Regular Data Profiling View');
  return (
    <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
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

      {/* Report Metadata Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            {/* Left side - Report title and phase info */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <DataProfilingIcon color="primary" fontSize="large" />
              <Box>
                <Typography variant="h5" component="h1" sx={{ fontWeight: 'medium' }}>
                  {reportInfo?.report_name || 'Loading...'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Data Profiling Phase - {reportInfo?.description || 'Validating data quality and generating profiling rules'}
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
            title="Processing data profiling..."
            onComplete={() => {
              setActiveBatchJob(null);
              loadWorkflowStats();
              loadPhaseMetrics();
            }}
            onError={() => setActiveBatchJob(null)}
            showDetails
          />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}


      {/* Data Profiling Metrics Row */}
      {phaseMetrics && (
        <Box sx={{ mb: 3 }}>
          {/* First Row - Primary Metrics */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            {/* Metric: Total Attributes */}
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <Card sx={{ height: 100 }}>
                <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                  <Typography variant="h3" color="primary" component="div">
                    {phaseMetrics?.total_attributes || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Attributes
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

          {/* Metric: Attributes with Profiling Rules */}
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h3" color="success.main" component="div">
                  {phaseMetrics?.attributes_with_rules || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Attributes with Profiling Rules
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Metric: Total Profiling Rules */}
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h3" color="info.main" component="div">
                  {phaseMetrics?.total_profiling_rules || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Profiling Rules
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Metric: Attributes with Anomalies */}
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h3" color="warning.main" component="div">
                  {phaseMetrics?.attributes_with_anomalies || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Attributes with Anomalies
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Metric: CDEs with Anomalies */}
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h3" color="error.main" component="div">
                  {phaseMetrics?.cdes_with_anomalies || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  CDEs with Anomalies
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Metric: Days Elapsed */}
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <Card sx={{ height: 100 }}>
              <CardContent sx={{ p: 2, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h3" color="secondary.main" component="div">
                  {phaseMetrics?.days_elapsed || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Days Elapsed
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
                    phaseMetrics?.phase_status === 'Complete' ? 
                      'success.main' :
                    phaseMetrics?.started_at ?
                      'success.main' : 'warning.main'
                  } 
                  component="div"
                  sx={{ fontSize: '1.5rem' }}
                >
                  {phaseMetrics?.phase_status === 'Complete' ? 
                    'Yes - Completed On-Time' :
                    phaseMetrics?.started_at ?
                      'On Track' : 'Not Started'
                  }
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {phaseMetrics?.phase_status === 'Complete' ? 'On-Time Completion Status' : 'Current Schedule Status'}
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
                  {phaseMetrics && phaseMetrics.phase_status === 'In Progress' && (
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Chip
                        label="At Risk"
                        size="small"
                        color="warning"
                        variant="outlined"
                        clickable
                        onClick={() => console.log('Phase marked as At Risk')}
                        disabled={loading}
                        sx={{ fontSize: '0.7rem' }}
                      />
                      <Chip
                        label="Off Track"
                        size="small"
                        color="error"
                        variant="outlined"
                        clickable
                        onClick={() => console.log('Phase marked as Off Track')}
                        disabled={loading}
                        sx={{ fontSize: '0.7rem' }}
                      />
                    </Box>
                  )}
                </Box>
                
                {/* Completion Requirements */}
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                    {!phaseMetrics ? (
                      'To complete: Start phase → Upload data → Generate rules → Approve rules → Execute profiling'
                    ) : phaseMetrics.phase_status === 'Complete' ? (
                      'Phase completed successfully - all requirements met'
                    ) : phaseMetrics.can_complete_phase ? (
                      'Ready to complete - all requirements met'
                    ) : (
                      'To complete: Generate and approve profiling rules, then execute profiling'
                    )}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
      )}

      {/* Data Profiling Phase Workflow */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DataProfilingIcon color="primary" />
            Data Profiling Phase Workflow
          </Typography>
          
          <Box sx={{ mt: 2 }}>
            {unifiedPhaseStatus?.activities ? (
              <DynamicActivityCards
                activities={unifiedPhaseStatus.activities}
                cycleId={cycle_id}
                reportId={report_id}
                phaseName="Data Profiling"
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
                  Loading data profiling activities...
                </Typography>
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>
      
      {/* Check for Report Owner Feedback - only check after we have a version */}
      {(currentVersionId || !loading) && (
        <ReportOwnerFeedbackChecker
          cycleId={cycle_id}
          reportId={report_id}
          versionId={currentVersionId}
          onFeedbackCheck={(hasFeedback) => {
            console.log('🔄 Setting hasReportOwnerFeedback:', hasFeedback);
            setHasReportOwnerFeedback(hasFeedback);
          }}
        />
      )}

      {/* Main Content Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(_, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          {hasReportOwnerFeedback && <Tab label="Report Owner Feedback" />}
          <Tab label="Rule Approval" />
          <Tab label="File Upload" />
          <Tab label="Execution Results" />
          <Tab label="Documents" />
        </Tabs>

        {/* Report Owner Feedback Tab (only shown when feedback exists) */}
        {hasReportOwnerFeedback && activeTab === 0 && (
          <Box sx={{ p: 3 }}>
            <ReportOwnerFeedback 
              cycleId={cycle_id}
              reportId={report_id}
              versionId={currentVersionId}
              currentUserRole={user?.role || ''}
              onMakeChanges={async () => {
                // Refresh the page to show the new version
                await loadWorkflowStats();
                await loadPhaseMetrics();
                // Keep report owner feedback visible - they should see their previous decisions
                // Switch to Rule Approval tab to show the new version
                setActiveTab(hasReportOwnerFeedback ? 1 : 0);
                // Clear the current version ID to force CompressedRulesTable to reload versions
                setCurrentVersionId(undefined);
              }}
            />
          </Box>
        )}

        {/* Rule Approval Tab */}
        {((hasReportOwnerFeedback && activeTab === 1) || (!hasReportOwnerFeedback && activeTab === 0)) && (
          <Box sx={{ p: 3 }}>
            <CompressedRulesTable
              key={`rules-table-${currentVersionId || 'initial'}`}
              cycleId={cycle_id}
              reportId={report_id}
              onVersionChange={(versionId) => {
                console.log('🔄 Version changed in DataProfiling:', versionId);
                setCurrentVersionId(versionId);
              }}
            />
            
            {workflowStats && workflowStats.can_proceed_to_execution && (
              <Box sx={{ mt: 3, p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                <Typography variant="body2" color="success.dark">
                  ✅ All critical rules have been approved. Ready to execute profiling.
                </Typography>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={executeProfilingRules}
                  sx={{ mt: 1 }}
                  disabled={loading}
                >
                  Execute {workflowStats?.approved_rules || 0} Profiling Rules
                </Button>
              </Box>
            )}
            
            {workflowStats && workflowStats.pending_rules > 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                {workflowStats.pending_rules} rules are still pending approval. 
                {canUserApprove() ? ' Please review and approve them above.' : ' Waiting for management approval.'}
              </Alert>
            )}
            
            {workflowStats && workflowStats.needs_revision_rules > 0 && canUserEdit() && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                {workflowStats.needs_revision_rules} rules need revision. Please update them and resubmit for approval.
              </Alert>
            )}
          </Box>
        )}

        {/* File Upload Tab */}
        {((hasReportOwnerFeedback && activeTab === 2) || (!hasReportOwnerFeedback && activeTab === 1)) && (
          <Box sx={{ p: 3 }}>
            <FileUploadSection
              cycleId={cycle_id}
              reportId={report_id}
              onFilesChange={() => {
                loadWorkflowStats();
                loadPhaseMetrics();
              }}
            />
          </Box>
        )}

        {/* Execution Results Tab */}
        {((hasReportOwnerFeedback && activeTab === 3) || (!hasReportOwnerFeedback && activeTab === 2)) && (
          <Box sx={{ p: 3 }}>
            <ExecutionResultsTable
              cycleId={cycle_id}
              reportId={report_id}
              key={`execution-results-${resultsRefreshKey}`}
            />
          </Box>
        )}

        {/* Documents Tab */}
        {((hasReportOwnerFeedback && activeTab === 4) || (!hasReportOwnerFeedback && activeTab === 3)) && (
          <Box sx={{ p: 3 }}>
            <PhaseDocumentManager
              cycleId={cycle_id}
              reportId={report_id}
              phaseId={2} // Data Profiling phase ID
              phaseName="Data Profiling"
              allowedDocumentTypes={[
                'report_sample_data',
                'report_underlying_transaction_data',
                'report_source_transaction_data',
                'report_source_document'
              ]}
              requiredDocumentTypes={[
                'report_sample_data',
                'report_underlying_transaction_data'
              ]}
              title="Data Profiling Documents"
            />
          </Box>
        )}

        {/* Execution Details Tab - Removed: functionality moved to Execution Results tab */}
      </Paper>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button variant="outlined" onClick={() => window.history.back()}>
          Back to Workflow
        </Button>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          {canUserEdit() && workflowStats && workflowStats.needs_revision_rules > 0 && (
            <Button variant="outlined" color="warning">
              Review Rejections ({workflowStats.needs_revision_rules})
            </Button>
          )}
          
          {canUserApprove() && workflowStats && workflowStats.pending_rules > 0 && (
            <Button variant="contained" color="primary">
              Review Pending ({workflowStats.pending_rules})
            </Button>
          )}
          
          {workflowStats?.can_proceed_to_execution && (
            <Button 
              variant="contained" 
              color="success"
              onClick={executeProfilingRules}
              disabled={loading}
            >
              Execute Profiling
            </Button>
          )}
        </Box>
      </Box>
    </Container>
  );
};

export default DataProfilingEnhanced;
