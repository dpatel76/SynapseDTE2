import React, { useState, useEffect, useRef } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  IconButton,
  Typography,
  Chip,
  Box,
  Button,
  Tooltip,
  Grid,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  LinearProgress
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  FilterList as FilterIcon,
  Search as SearchIcon,
  GetApp as ExportIcon,
  SelectAll as SelectAllIcon,
  DeselectOutlined as DeselectIcon,
  Send as SendIcon,
  Person as PersonIcon,
  Undo as UndoIcon,
  Edit as EditIcon,
  Info as InfoIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { dataProfilingApi } from '../../api/dataProfiling';
import apiClient from '../../api/client';

interface Rule {
  rule_id: number;
  attribute_id: number;
  attribute_name?: string;
  rule_name: string;
  rule_type: string;
  rule_code?: string;
  rule_description?: string;
  status: string;
  severity?: string;
  version_number: number;
  is_current_version: boolean;
  business_key: string;
  can_approve: boolean;
  can_reject: boolean;
  can_revise: boolean;
  // Tester decision fields
  tester_decision?: string;
  tester_notes?: string;
  tester_decided_at?: string;
  tester_decided_by?: number;
  // Report owner decision fields
  report_owner_decision?: string;
  report_owner_notes?: string;
  report_owner_reason?: string;
  report_owner_decided_at?: string;
  report_owner_decided_by?: number;
}

interface AttributeWithRules {
  attribute_id: number;
  attribute_name: string;
  attribute_type: string;
  mandatory: boolean;
  total_rules: number;
  approved_count: number;
  rejected_count: number;
  pending_count: number;
  needs_revision_count: number;
  rules: Rule[];
  // Additional metadata for badges
  is_cde: boolean;
  has_issues: boolean;
  is_primary_key: boolean;
  line_item_number?: string;
}

interface CompressedRulesTableProps {
  cycleId: number;
  reportId: number;
  onVersionChange?: (versionId: string) => void;
}

const CompressedRulesTable: React.FC<CompressedRulesTableProps> = ({
  cycleId,
  reportId,
  onVersionChange
}) => {
  const [attributesWithRules, setAttributesWithRules] = useState<AttributeWithRules[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRules, setSelectedRules] = useState<Set<number>>(new Set());
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterDimension, setFilterDimension] = useState<string>('all');
  const [filterTesterDecision, setFilterTesterDecision] = useState<string>('all');
  const [filterReportOwnerDecision, setFilterReportOwnerDecision] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [approveDialogOpen, setApproveDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedRuleForAction, setSelectedRuleForAction] = useState<Rule | null>(null);
  const [actionNotes, setActionNotes] = useState<string>('');
  const [sendToOwnerDialogOpen, setSendToOwnerDialogOpen] = useState(false);
  const [versions, setVersions] = useState<any[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  const [versionsLoaded, setVersionsLoaded] = useState(false);
  
  // Assignment tracking states
  const [hasExistingAssignment, setHasExistingAssignment] = useState(false);
  const [awaitingReportOwnerReview, setAwaitingReportOwnerReview] = useState(false);
  const [reportOwnerAssignment, setReportOwnerAssignment] = useState<any>(null);
  const [reportOwnerCompleted, setReportOwnerCompleted] = useState(false);
  const [hasReportOwnerFeedback, setHasReportOwnerFeedback] = useState(false);
  const [needsResubmission, setNeedsResubmission] = useState(false);
  const [resubmitDialogOpen, setResubmitDialogOpen] = useState(false);
  const [jobProgress, setJobProgress] = useState<any>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Determine if the interface should be read-only based on version status
  const isReadOnly = (): boolean => {
    // Report Owners are always read-only
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user?.role === 'Report Owner') return true;
    
    // Find the currently selected version
    const currentVersion = versions.find(v => v.version_id === selectedVersionId);
    
    // If version is not draft, it's read-only
    return currentVersion && currentVersion.version_status !== 'draft';
  };
  
  // Load versions on mount
  useEffect(() => {
    loadVersions();
  }, [cycleId, reportId]);

  // Load attributes and their rules when version changes
  useEffect(() => {
    // Only load after versions have been checked
    if (!versionsLoaded) return;
    
    // Load if we have a selected version, or if no versions exist (legacy support)
    if (selectedVersionId || versions.length === 0) {
      loadAttributesWithRules();
    }
  }, [cycleId, reportId, selectedVersionId, versionsLoaded]);
  
  // Poll job status function (similar to MapPDEsActivity)
  const pollJobStatus = (jobId: string) => {
    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    const poll = async () => {
      try {
        console.log('📡 Polling job status for:', jobId);
        const response = await apiClient.get(`/jobs/${jobId}/status`);
        const jobData = response.data;
        console.log('📈 Job status response:', jobData);
        
        setJobProgress(jobData);
        
        if (jobData.status === 'completed') {
          // Job completed, reload versions
          await loadVersions();
          localStorage.removeItem(`data-profiling-job-${cycleId}-${reportId}`);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          setJobProgress(null);
        } else if (jobData.status === 'failed') {
          setError(`Rule generation failed: ${jobData.error || 'Unknown error'}`);
          localStorage.removeItem(`data-profiling-job-${cycleId}-${reportId}`);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          setJobProgress(null);
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    };

    // Poll immediately
    poll();
    
    // Then poll every 2 seconds
    pollingIntervalRef.current = setInterval(poll, 2000);
  };

  // Check for active jobs related to this cycle/report
  const checkForActiveJobs = async () => {
    try {
      console.log('🔍 Checking for active data profiling jobs...');
      const response = await apiClient.get('/jobs/active');
      const activeJobs = response.data.active_jobs || [];
      console.log('📊 Active jobs response:', activeJobs);
      
      // Find any active data profiling job for this cycle/report
      const activeProfilingJob = activeJobs.find((job: any) => 
        job.job_type === 'data_profiling_llm_generation' && 
        job.metadata?.cycle_id === cycleId &&
        job.metadata?.report_id === reportId &&
        (job.status === 'pending' || job.status === 'running')
      );
      
      if (activeProfilingJob) {
        console.log('✅ Found active data profiling job:', activeProfilingJob);
        const jobId = activeProfilingJob.job_id || activeProfilingJob.id;
        if (jobId) {
          // Store in localStorage for faster access
          localStorage.setItem(`data-profiling-job-${cycleId}-${reportId}`, jobId);
          pollJobStatus(jobId);
        } else {
          console.error('Active job found but no job_id field:', activeProfilingJob);
        }
      } else {
        console.log('No active data profiling job found for this cycle/report');
        // Clear any stale localStorage entry
        localStorage.removeItem(`data-profiling-job-${cycleId}-${reportId}`);
      }
    } catch (error) {
      console.error('Error checking for active jobs:', error);
    }
  };

  // Check for active job on mount and when cycleId/reportId change
  useEffect(() => {
    // First check localStorage for quick access
    const storedJobId = localStorage.getItem(`data-profiling-job-${cycleId}-${reportId}`);
    console.log('🔍 CompressedRulesTable checking localStorage:', storedJobId, 'for cycle:', cycleId, 'report:', reportId);
    
    // Always check for active jobs to handle browser refresh/reopen
    checkForActiveJobs();
    
    // Cleanup on unmount
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [cycleId, reportId]);


  const loadVersions = async () => {
    try {
      console.log('🔄 Loading versions for cycle:', cycleId, 'report:', reportId);
      const versionList = await dataProfilingApi.getVersions(cycleId, reportId);
      console.log('📦 Versions loaded:', versionList);
      setVersions(versionList);
      
      // Set the latest/current version as default
      if (versionList.length > 0) {
        const currentVersion = versionList.find(v => v.is_current) || versionList[0];
        console.log('✅ Current version selected:', currentVersion);
        setSelectedVersionId(currentVersion.version_id);
        // Notify parent component
        if (onVersionChange) {
          onVersionChange(currentVersion.version_id);
        }
      }
      setVersionsLoaded(true);
    } catch (error) {
      console.error('Error loading versions:', error);
      // Continue without versions if endpoint fails
      setVersions([]);
      setVersionsLoaded(true);
    }
  };

  const loadAttributesWithRules = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔍 CompressedRulesTable loading data for cycle:', cycleId, 'report:', reportId, 'version:', selectedVersionId);
      
      // Get ALL rules at once to preserve backend ordering
      // Pass undefined for versionId if no versions exist (for backward compatibility)
      const versionToUse = versions.length > 0 ? selectedVersionId : undefined;
      const allRules = await dataProfilingApi.getRules(
        cycleId, 
        reportId, 
        undefined, 
        versionToUse,
        undefined,  // No tester decision filter for initial load
        undefined   // No report owner decision filter for initial load
      );
      console.log('📋 Got all rules:', allRules.length, 'rules (backend ordered)');
      
      // Debug: Check for rules with report owner feedback
      const rulesWithRODecision = allRules.filter((rule: any) => 
        rule.report_owner_decision !== null && rule.report_owner_decision !== undefined
      );
      console.log('🔍 Rules with Report Owner feedback:', {
        total: rulesWithRODecision.length,
        approvedByTesterRejectedByRO: rulesWithRODecision.filter((r: any) => 
          r.tester_decision?.toLowerCase() === 'approved' && 
          r.report_owner_decision?.toLowerCase() === 'rejected'
        ).length,
        samples: rulesWithRODecision.slice(0, 5).map((r: any) => ({
          rule_id: r.rule_id,
          attribute_name: r.attribute_name,
          tester_decision: r.tester_decision,
          report_owner_decision: r.report_owner_decision,
          report_owner_notes: r.report_owner_notes
        }))
      });
      
      // Find the specific rule that was approved by tester but rejected by RO
      const testerApprovedRORejectRule = allRules.find((r: any) => 
        r.rule_id === '22b30a90-9282-4057-bc25-cb9865bd6d64'
      );
      if (testerApprovedRORejectRule) {
        console.log('🎯 Found Bank ID Reference Check rule:', {
          rule_id: testerApprovedRORejectRule.rule_id,
          rule_name: testerApprovedRORejectRule.rule_name,
          attribute_id: testerApprovedRORejectRule.attribute_id,
          tester_decision: (testerApprovedRORejectRule as any).tester_decision,
          report_owner_decision: (testerApprovedRORejectRule as any).report_owner_decision,
          status: testerApprovedRORejectRule.status
        });
      }
      
      // Group rules by attribute while preserving order
      const attributeMap = new Map<number, AttributeWithRules>();
      const attributeOrder: number[] = [];
      
      allRules.forEach((rule: any) => {
        const attrId = rule.attribute_id;
        
        if (!attributeMap.has(attrId)) {
          attributeOrder.push(attrId);
          attributeMap.set(attrId, {
            attribute_id: attrId,
            attribute_name: rule.attribute_name,
            attribute_type: 'string', // We'll update this from summaries
            mandatory: false,
            total_rules: 0,
            approved_count: 0,
            rejected_count: 0,
            pending_count: 0,
            needs_revision_count: 0,
            line_item_number: rule.line_item_number || undefined,
            is_cde: rule.is_cde || false,
            has_issues: rule.has_issues || false,
            is_primary_key: rule.is_primary_key || false,
            rules: []
          });
        }
        
        const attr = attributeMap.get(attrId)!;
        attr.rules.push(rule);
        attr.total_rules++;
        
        // Update counts
        const status = rule.status?.toUpperCase();
        if (status === 'APPROVED') attr.approved_count++;
        else if (status === 'REJECTED') attr.rejected_count++;
        else if (status === 'PENDING') attr.pending_count++;
        else if (status === 'NEEDS_REVISION') attr.needs_revision_count++;
      });
      
      // Get attribute summaries to fill in the missing data
      const summaries = await dataProfilingApi.getAttributeRulesSummary(cycleId, reportId);
      console.log('📊 Got attribute summaries:', summaries.length);
      
      // Update attribute data from summaries
      summaries.forEach(summary => {
        const attr = attributeMap.get(summary.attribute_id);
        if (attr) {
          attr.attribute_type = summary.attribute_type;
          attr.mandatory = summary.mandatory;
          attr.line_item_number = summary.line_item_number;
          attr.is_cde = summary.is_cde;
          attr.has_issues = summary.has_issues;
          attr.is_primary_key = summary.is_primary_key;
        }
      });
      
      // Convert to array preserving the order from backend
      const sortedAttributesData = attributeOrder.map(attrId => attributeMap.get(attrId)!);
      
      console.log('✅ Loaded all attributes with rules:', sortedAttributesData.length, 'total attributes');
      setAttributesWithRules(sortedAttributesData);
    } catch (error) {
      console.error('❌ Failed to load attributes with rules:', error);
      setError('Failed to load profiling rules. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Check for report owner feedback and resubmission needs
  useEffect(() => {
    const rulesWithROFeedback = attributesWithRules.flatMap(attr => attr.rules)
      .filter(r => r.report_owner_decision !== null && r.report_owner_decision !== undefined);
    
    const rulesNeedingUpdate = rulesWithROFeedback.filter(r => 
      r.report_owner_decision?.toLowerCase() === 'rejected' || 
      r.report_owner_decision?.toLowerCase() === 'request_changes'
    );
    
    setHasReportOwnerFeedback(rulesWithROFeedback.length > 0);
    setNeedsResubmission(rulesNeedingUpdate.length > 0);
  }, [attributesWithRules]);
  
  // Flatten all rules for table display
  const flattenedRules = attributesWithRules.flatMap(attr => 
    attr.rules.map(rule => ({
      ...rule,
      attribute: attr,
      displayKey: `${attr.attribute_id}-${rule.rule_id}`
    }))
  );
  
  // Debug button state
  useEffect(() => {
    const rulesWithoutTesterDecision = flattenedRules.filter(r => !r.tester_decision);
    const testerApprovedRules = flattenedRules.filter(r => r.tester_decision?.toLowerCase() === 'approve' || r.tester_decision?.toLowerCase() === 'approved');
    const testerRejectedRules = flattenedRules.filter(r => r.tester_decision?.toLowerCase() === 'reject' || r.tester_decision?.toLowerCase() === 'rejected');
    
    console.log('🔍 Button state debug:', {
      totalRules: flattenedRules.length,
      rulesWithoutTesterDecision: rulesWithoutTesterDecision.length,
      testerApprovedRules: testerApprovedRules.length,
      testerRejectedRules: testerRejectedRules.length,
      hasExistingAssignment,
      awaitingReportOwnerReview,
      reportOwnerCompleted,
      isReadOnly: isReadOnly(),
      selectedVersionId,
      versions: versions.length,
      buttonEnabled: rulesWithoutTesterDecision.length === 0 && testerApprovedRules.length > 0 && !hasExistingAssignment && !awaitingReportOwnerReview
    });
    
    // Log sample rules for debugging
    if (flattenedRules.length > 0) {
      console.log('Sample rule:', {
        rule_id: flattenedRules[0].rule_id,
        status: flattenedRules[0].status,
        tester_decision: flattenedRules[0].tester_decision,
        report_owner_decision: flattenedRules[0].report_owner_decision
      });
    }
  }, [flattenedRules, hasExistingAssignment, awaitingReportOwnerReview, reportOwnerCompleted]);

  // Apply filters
  const filteredRules = flattenedRules.filter(item => {
    const rule = item;
    const attr = item.attribute;
    
    // Status filter
    if (filterStatus !== 'all' && rule.status.toLowerCase() !== filterStatus.toLowerCase()) {
      return false;
    }
    
    // Dimension filter
    if (filterDimension !== 'all' && rule.rule_type.toLowerCase() !== filterDimension.toLowerCase()) {
      return false;
    }
    
    // Tester decision filter
    if (filterTesterDecision !== 'all') {
      if (filterTesterDecision === 'none' && rule.tester_decision) {
        return false;
      }
      if (filterTesterDecision !== 'none' && (!rule.tester_decision || rule.tester_decision.toLowerCase() !== filterTesterDecision.toLowerCase())) {
        return false;
      }
    }
    
    // Report owner decision filter
    if (filterReportOwnerDecision !== 'all') {
      if (filterReportOwnerDecision === 'none' && rule.report_owner_decision) {
        return false;
      }
      if (filterReportOwnerDecision !== 'none' && (!rule.report_owner_decision || rule.report_owner_decision.toLowerCase() !== filterReportOwnerDecision.toLowerCase())) {
        return false;
      }
    }
    
    // Search filter
    if (searchTerm && !attr.attribute_name.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !rule.rule_name.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    
    return true;
  });

  // Selection handlers
  const handleSelectAll = () => {
    if (selectedRules.size === filteredRules.length) {
      setSelectedRules(new Set());
    } else {
      setSelectedRules(new Set(filteredRules.map(item => item.rule_id)));
    }
  };

  const handleSelectRule = (ruleId: number) => {
    const newSelected = new Set(selectedRules);
    if (newSelected.has(ruleId)) {
      newSelected.delete(ruleId);
    } else {
      newSelected.add(ruleId);
    }
    setSelectedRules(newSelected);
  };

  // Bulk actions
  const handleBulkApprove = async () => {
    if (selectedRules.size === 0) return;
    
    try {
      // Use the bulk API endpoint
      const ruleIds = Array.from(selectedRules).map(String);
      await dataProfilingApi.bulkApproveRules(ruleIds, 'Bulk approval');
      
      setSelectedRules(new Set());
      await loadAttributesWithRules();
    } catch (error) {
      console.error('Bulk approve failed:', error);
      setError('Failed to approve selected rules. Please try again.');
    }
  };

  const handleBulkReject = async () => {
    if (selectedRules.size === 0) return;
    
    console.log(`🔴 Bulk rejecting ${selectedRules.size} rules:`, Array.from(selectedRules));
    
    try {
      // Use the bulk API endpoint
      const ruleIds = Array.from(selectedRules).map(String);
      await dataProfilingApi.bulkRejectRules(ruleIds, 'Bulk rejection', 'Rejected via bulk action', true);
      
      console.log(`✅ Successfully bulk rejected ${ruleIds.length} rules`);
      
      setSelectedRules(new Set());
      await loadAttributesWithRules();
    } catch (error) {
      console.error('Bulk reject failed:', error);
      setError('Failed to reject selected rules. Please try again.');
    }
  };

  // Individual actions - open dialogs
  const handleApproveRule = (rule: Rule) => {
    setSelectedRuleForAction(rule);
    setActionNotes('');
    setApproveDialogOpen(true);
  };

  const handleRejectRule = (rule: Rule) => {
    setSelectedRuleForAction(rule);
    setActionNotes('');
    setRejectDialogOpen(true);
  };

  // Check if tester should be able to reject after report owner feedback
  const canTesterReject = (rule: Rule): boolean => {
    // If report owner approved, tester cannot reject
    if (rule.report_owner_decision?.toLowerCase() === 'approved') {
      return false;
    }
    // If report owner rejected or requested changes, tester can still reject
    if (rule.report_owner_decision?.toLowerCase() === 'rejected' || 
        rule.report_owner_decision?.toLowerCase() === 'request_changes') {
      return true;
    }
    // If no report owner decision yet, tester can reject
    return true;
  };
  
  // Check if tester can update decision after report owner feedback
  const canTesterUpdateDecision = (rule: Rule): boolean => {
    // If report owner has rejected or requested changes, tester can update
    if (rule.report_owner_decision?.toLowerCase() === 'rejected' || 
        rule.report_owner_decision?.toLowerCase() === 'request_changes') {
      return true;
    }
    // If report owner hasn't provided feedback yet, tester can update
    if (!rule.report_owner_decision) {
      return true;
    }
    // If report owner approved, tester cannot change
    return false;
  };

  const handleDeleteRule = (rule: Rule) => {
    setSelectedRuleForAction(rule);
    setDeleteDialogOpen(true);
  };

  // Confirm individual approval
  const confirmApproveRule = async () => {
    if (!selectedRuleForAction) return;
    
    try {
      await dataProfilingApi.approveRule(
        selectedRuleForAction.rule_id, 
        actionNotes || 'Individual approval'
      );
      await loadAttributesWithRules();
      setApproveDialogOpen(false);
      setSelectedRuleForAction(null);
      setActionNotes('');
    } catch (error) {
      console.error('Approve failed:', error);
      setError('Failed to approve rule. Please try again.');
    }
  };

  // Confirm individual rejection
  const confirmRejectRule = async () => {
    if (!selectedRuleForAction) return;
    
    try {
      await dataProfilingApi.rejectRule(
        selectedRuleForAction.rule_id, 
        'Rule needs revision', 
        actionNotes || 'Individual rejection', 
        true
      );
      await loadAttributesWithRules();
      setRejectDialogOpen(false);
      setSelectedRuleForAction(null);
      setActionNotes('');
    } catch (error) {
      console.error('Reject failed:', error);
      setError('Failed to reject rule. Please try again.');
    }
  };

  // Confirm individual deletion
  const confirmDeleteRule = async () => {
    if (!selectedRuleForAction) return;
    
    try {
      await dataProfilingApi.deleteRule(selectedRuleForAction.rule_id);
      await loadAttributesWithRules();
      setDeleteDialogOpen(false);
      setSelectedRuleForAction(null);
    } catch (error) {
      console.error('Delete failed:', error);
      setError('Failed to delete rule. Please try again.');
    }
  };

  // Reset rule to pending status
  const handleResetToPending = async (rule: Rule) => {
    try {
      // Use the new reset-to-pending endpoint
      await dataProfilingApi.resetRuleToPending(rule.rule_id);
      await loadAttributesWithRules();
    } catch (error) {
      console.error('Reset to pending failed:', error);
      setError('Failed to reset rule to pending. Please try again.');
    }
  };

  // Check for existing assignment when component loads or when rules change or version changes
  useEffect(() => {
    checkForExistingAssignment();
  }, [cycleId, reportId, flattenedRules.length, selectedVersionId]);
  
  const checkForExistingAssignment = async () => {
    try {
      const existingAssignments = await apiClient.get('/universal-assignments/assignments');
      const relevantAssignment = existingAssignments.data.find((assignment: any) => 
        assignment.context_data?.cycle_id === cycleId &&
        assignment.context_data?.report_id === reportId &&
        (assignment.context_data?.phase === 'data_profiling' || assignment.context_data?.phase === undefined) && // Allow undefined phase
        assignment.assignment_type === 'Rule Approval' &&
        ['Assigned', 'Acknowledged', 'In Progress', 'Completed'].includes(assignment.status)
      );
      
      if (relevantAssignment) {
        setReportOwnerAssignment(relevantAssignment);
        const isPending = ['Assigned', 'Acknowledged', 'In Progress'].includes(relevantAssignment.status);
        const isCompleted = relevantAssignment.status === 'Completed';
        
        // Check if this assignment is for the current version
        const assignmentVersionId = relevantAssignment.context_data?.version_id;
        const isCurrentVersionAssignment = !assignmentVersionId || assignmentVersionId === selectedVersionId;
        
        // Check if this is a new version created after report owner feedback
        // We can detect this by checking if we have report owner decisions but no active assignment for this version
        const hasReportOwnerDecisions = flattenedRules.some(rule => 
          rule.report_owner_decision !== null && rule.report_owner_decision !== undefined
        );
        
        // Get current version info
        const currentVersion = versions.find(v => v.version_id === selectedVersionId);
        const isNewerVersion = currentVersion && relevantAssignment.context_data?.version_id && 
                              currentVersion.version_number > (relevantAssignment.context_data?.version_number || 0);
        
        // If this is a completed assignment but we're on a newer version (created after RO feedback)
        if (isCompleted && (isNewerVersion || (hasReportOwnerDecisions && !isCurrentVersionAssignment))) {
          console.log('📌 Found completed assignment for older version, current version needs new assignment', {
            isCompleted,
            isNewerVersion,
            hasReportOwnerDecisions,
            isCurrentVersionAssignment,
            assignmentVersionId,
            selectedVersionId,
            currentVersionNumber: currentVersion?.version_number
          });
          setHasExistingAssignment(false);
          setAwaitingReportOwnerReview(false);
          setReportOwnerCompleted(true); // Keep this true to show "Resend" button
          return;
        }
        
        setHasExistingAssignment(true);
        
        // Check if any rules have report owner feedback to determine if we're still awaiting review
        const rulesWithROFeedback = flattenedRules.filter(rule => 
          rule.report_owner_decision !== null && rule.report_owner_decision !== undefined
        );
        const hasReportOwnerFeedback = rulesWithROFeedback.length > 0;
        
        console.log('🔍 Checking report owner feedback:', {
          totalRules: flattenedRules.length,
          rulesWithFeedback: rulesWithROFeedback.length,
          hasReportOwnerFeedback,
          assignmentVersionId,
          selectedVersionId,
          isCurrentVersionAssignment,
          sampleFeedback: rulesWithROFeedback.slice(0, 3).map(r => ({
            rule_id: r.rule_id,
            report_owner_decision: r.report_owner_decision
          }))
        });
        
        // Only set awaitingReportOwnerReview to true if assignment is pending AND no feedback exists
        setAwaitingReportOwnerReview(isPending && !hasReportOwnerFeedback);
        setReportOwnerCompleted(isCompleted && isCurrentVersionAssignment);
        
        console.log('✅ Found assignment for report owner:', {
          assignment_id: relevantAssignment.assignment_id,
          status: relevantAssignment.status,
          isPending,
          isCompleted,
          hasReportOwnerFeedback,
          awaitingReview: isPending && !hasReportOwnerFeedback,
          flattenedRulesCount: flattenedRules.length,
          completed_at: relevantAssignment.completed_at,
          isCurrentVersionAssignment,
          assignmentVersionId,
          selectedVersionId,
          reportOwnerCompleted
        });
        
        // Refresh rules data if report owner has completed review
        if (isCompleted && !isPending) {
          await loadAttributesWithRules();
        }
      } else {
        // No assignment found - check if we have report owner decisions (indicating a previous assignment)
        const hasReportOwnerDecisions = flattenedRules.some(rule => 
          rule.report_owner_decision !== null && rule.report_owner_decision !== undefined
        );
        
        console.log('📌 No active assignment found, hasReportOwnerDecisions:', hasReportOwnerDecisions);
        setHasExistingAssignment(false);
        setAwaitingReportOwnerReview(false);
        setReportOwnerCompleted(hasReportOwnerDecisions); // If we have RO decisions, show "Resend" button
      }
    } catch (error) {
      console.error('Failed to check existing assignments:', error);
    }
  };

  // Send to Report Owner for approval
  const handleSendToReportOwner = () => {
    setSendToOwnerDialogOpen(true);
  };

  const confirmSendToReportOwner = async () => {
    try {
      const approvedRules = flattenedRules.filter(r => r.tester_decision?.toLowerCase() === 'approve' || r.tester_decision?.toLowerCase() === 'approved');
      const pendingRules = flattenedRules.filter(r => !r.tester_decision);
      
      // Validate workflow requirements
      if (pendingRules.length > 0) {
        setError(`Cannot send to Report Owner. You must make decisions on all ${pendingRules.length} pending rules first.`);
        setSendToOwnerDialogOpen(false);
        return;
      }
      
      if (approvedRules.length === 0) {
        setError('Cannot send to Report Owner. No rules have been approved by the tester.');
        setSendToOwnerDialogOpen(false);
        return;
      }

      // Use the new backend endpoint to send to Report Owner
      const response = await dataProfilingApi.sendToReportOwner(cycleId, reportId);

      if (response) {
        setSendToOwnerDialogOpen(false);
        setError(null);
        setHasExistingAssignment(true); // Update local state immediately
        setAwaitingReportOwnerReview(true); // Mark as awaiting review
        
        // Workflow status is managed by the backend when creating assignments
        // No need to manually update workflow status here
        
        // Show success message
        console.log('✅ Assignment created successfully:', response.data);
        console.log(`📋 Sent ${approvedRules.length} approved rules to Report Owner for final approval`);
        // You might want to show a success toast here
      }
    } catch (error) {
      console.error('❌ Failed to send to report owner:', error);
      setError('Failed to create assignment for report owner. Please try again.');
      setSendToOwnerDialogOpen(false);
    }
  };

  // Utility functions
  const getStatusChip = (status: string) => {
    const statusConfig = {
      'pending': { color: 'warning' as const, label: 'Pending' },
      'approved': { color: 'success' as const, label: 'Approved' },
      'rejected': { color: 'error' as const, label: 'Rejected' },
      'needs_revision': { color: 'info' as const, label: 'Needs Revision' },
      'resubmitted': { color: 'secondary' as const, label: 'Resubmitted' }
    };
    
    const config = statusConfig[status.toLowerCase() as keyof typeof statusConfig] || 
                   { color: 'default' as const, label: status };
    
    return <Chip size="small" color={config.color} label={config.label} />;
  };

  const getTesterDecisionDisplay = (rule: Rule) => {
    if (!rule.tester_decision) {
      return <Typography variant="caption" color="textSecondary">-</Typography>;
    }

    const decisionConfig = {
      'approved': { color: 'success' as const, label: 'Approved' },
      'approve': { color: 'success' as const, label: 'Approved' },  // Support old value
      'rejected': { color: 'error' as const, label: 'Rejected' },
      'reject': { color: 'error' as const, label: 'Rejected' },    // Support old value
      'pending': { color: 'warning' as const, label: 'Pending' },
      'request_changes': { color: 'warning' as const, label: 'Request Changes' }
    };

    const config = decisionConfig[rule.tester_decision.toLowerCase() as keyof typeof decisionConfig] || 
                   { color: 'default' as const, label: rule.tester_decision };

    return (
      <Box>
        <Chip size="small" color={config.color} label={config.label} sx={{ fontSize: '0.7rem' }} />
        {rule.tester_notes && (
          <Tooltip title={`Notes: ${rule.tester_notes}`}>
            <InfoIcon sx={{ fontSize: 12, ml: 0.5, color: 'text.secondary' }} />
          </Tooltip>
        )}
      </Box>
    );
  };

  const getReportOwnerDecisionDisplay = (rule: Rule) => {
    if (!rule.report_owner_decision) {
      return <Typography variant="caption" color="textSecondary">-</Typography>;
    }

    const decisionConfig = {
      'approved': { color: 'success' as const, label: 'RO Approved' },
      'approve': { color: 'success' as const, label: 'RO Approved' },  // Support old value
      'rejected': { color: 'error' as const, label: 'RO Rejected' },
      'reject': { color: 'error' as const, label: 'RO Rejected' },    // Support old value
      'pending': { color: 'warning' as const, label: 'RO Pending' },
      'request_changes': { color: 'warning' as const, label: 'RO Request Changes' }
    };

    const config = decisionConfig[rule.report_owner_decision.toLowerCase() as keyof typeof decisionConfig] || 
                   { color: 'default' as const, label: rule.report_owner_decision };

    return (
      <Box>
        <Chip size="small" color={config.color} label={config.label} sx={{ fontSize: '0.7rem' }} />
        {rule.report_owner_reason && (
          <Tooltip title={`Reason: ${rule.report_owner_reason}${rule.report_owner_notes ? ` - ${rule.report_owner_notes}` : ''}`}>
            <Typography variant="caption" display="block" sx={{ mt: 0.5, cursor: 'help' }}>
              {rule.report_owner_reason}
            </Typography>
          </Tooltip>
        )}
      </Box>
    );
  };

  const getDimensionChip = (dimension: string) => {
    const dimensionConfig = {
      'completeness': { color: '#1976d2', label: 'Completeness' },
      'validity': { color: '#388e3c', label: 'Validity' },
      'uniqueness': { color: '#f57c00', label: 'Uniqueness' },
      'consistency': { color: '#7b1fa2', label: 'Consistency' },
      'accuracy': { color: '#d32f2f', label: 'Accuracy' },
      'timeliness': { color: '#455a64', label: 'Timeliness' }
    };
    
    const config = dimensionConfig[dimension as keyof typeof dimensionConfig] || 
                   { color: '#616161', label: dimension };
    
    return (
      <Chip 
        size="small" 
        label={config.label}
        sx={{ 
          backgroundColor: config.color, 
          color: 'white',
          fontWeight: 'bold',
          fontSize: '0.75rem'
        }} 
      />
    );
  };

  const getCriticalityChip = (severity: string | undefined, mandatory: boolean) => {
    if (severity === 'critical' || (mandatory && !severity)) {
      return <Chip size="small" color="error" label="Critical" />;
    } else if (severity === 'high') {
      return <Chip size="small" color="warning" label="High" />;
    } else if (severity === 'medium') {
      return <Chip size="small" color="info" label="Medium" />;
    } else {
      return <Chip size="small" color="default" label="Low" />;
    }
  };

  const renderAttributeBadges = (attr: AttributeWithRules) => (
    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center' }}>
      <Typography variant="body2" sx={{ fontWeight: 'bold', mr: 1 }}>
        {attr.attribute_name}
      </Typography>
      {attr.is_cde && (
        <Chip size="small" label="CDE" color="primary" sx={{ fontSize: '0.7rem', height: 20 }} />
      )}
      {attr.has_issues && (
        <Chip size="small" label="Issues" color="error" sx={{ fontSize: '0.7rem', height: 20 }} />
      )}
      {attr.is_primary_key && (
        <Chip size="small" label="PK" color="secondary" sx={{ fontSize: '0.7rem', height: 20 }} />
      )}
    </Box>
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Typography>Loading profiling rules...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Show job progress inline (like MapPDEsActivity) */}
      {jobProgress && jobProgress.status !== 'completed' && jobProgress.status !== 'failed' && (
        <Box mb={3} p={2} bgcolor="primary.light" borderRadius={1}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="subtitle2" color="primary.contrastText">
              Generating Profiling Rules...
            </Typography>
            <Typography variant="body2" color="primary.contrastText">
              {jobProgress.progress_percentage || 0}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={jobProgress.progress_percentage || 0}
            sx={{ mb: 1, backgroundColor: 'rgba(255,255,255,0.3)' }}
          />
          <Typography variant="body2" color="primary.contrastText">
            {jobProgress.message || 'Processing...'}
          </Typography>
          {jobProgress.current_step && (
            <Typography variant="caption" color="primary.contrastText" display="block" mt={0.5}>
              Step: {jobProgress.current_step}
            </Typography>
          )}
          {jobProgress.completed_steps !== undefined && jobProgress.total_steps && (
            <Typography variant="caption" color="primary.contrastText" display="block">
              Attributes: {jobProgress.completed_steps} / {jobProgress.total_steps}
            </Typography>
          )}
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {isReadOnly() && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <strong>Read-only mode:</strong> This version is {versions.find(v => v.version_id === selectedVersionId)?.version_status || 'not in draft status'} and cannot be edited.
        </Alert>
      )}

      {awaitingReportOwnerReview && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <strong>Rules are currently under Report Owner review.</strong> You cannot make any changes to rule decisions until the Report Owner completes their review.
          {reportOwnerAssignment && (
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Sent for review on: {new Date(reportOwnerAssignment.assigned_at).toLocaleString()}
            </Typography>
          )}
        </Alert>
      )}

      {reportOwnerAssignment && reportOwnerAssignment.status === 'Completed' && (
        <Alert severity="success" sx={{ mb: 2 }}>
          <strong>Report Owner has completed their review!</strong>
          {reportOwnerAssignment.context_data?.summary && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2">
                • Approved: {reportOwnerAssignment.context_data.summary.approved_count} rules
                {reportOwnerAssignment.context_data.summary.rejected_count > 0 && (
                  <span> • Rejected: {reportOwnerAssignment.context_data.summary.rejected_count} rules</span>
                )}
              </Typography>
              {reportOwnerAssignment.completed_at && (
                <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                  Completed on: {new Date(reportOwnerAssignment.completed_at).toLocaleString()}
                </Typography>
              )}
              {reportOwnerAssignment.context_data.summary.rejected_count > 0 && (
                <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
                  Please review the rejected rules and make necessary adjustments.
                </Typography>
              )}
            </Box>
          )}
        </Alert>
      )}

      {/* Controls Bar */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
          {/* Search */}
          <Box sx={{ flex: '1 1 300px' }}>
            <TextField
              size="small"
              placeholder="Search attributes or rules..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              fullWidth
            />
          </Box>

          {/* Status Filter */}
          <Box sx={{ minWidth: 150 }}>
            <FormControl size="small" fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                label="Status"
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="approved">Approved</MenuItem>
                <MenuItem value="rejected">Rejected</MenuItem>
                <MenuItem value="needs_revision">Needs Revision</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Tester Decision Filter */}
          <Box sx={{ minWidth: 150 }}>
            <FormControl size="small" fullWidth>
              <InputLabel>Tester Decision</InputLabel>
              <Select
                value={filterTesterDecision}
                onChange={(e) => setFilterTesterDecision(e.target.value)}
                label="Tester Decision"
              >
                <MenuItem value="all">All Decisions</MenuItem>
                <MenuItem value="none">Not Decided</MenuItem>
                <MenuItem value="approve">Approved</MenuItem>
                <MenuItem value="reject">Rejected</MenuItem>
                <MenuItem value="request_changes">Request Changes</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Report Owner Decision Filter */}
          <Box sx={{ minWidth: 170 }}>
            <FormControl size="small" fullWidth>
              <InputLabel>Report Owner Decision</InputLabel>
              <Select
                value={filterReportOwnerDecision}
                onChange={(e) => setFilterReportOwnerDecision(e.target.value)}
                label="Report Owner Decision"
              >
                <MenuItem value="all">All Decisions</MenuItem>
                <MenuItem value="none">Not Decided</MenuItem>
                <MenuItem value="approve">Approved</MenuItem>
                <MenuItem value="reject">Rejected</MenuItem>
                <MenuItem value="request_changes">Request Changes</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Dimension Filter */}
          <Box sx={{ minWidth: 150 }}>
            <FormControl size="small" fullWidth>
              <InputLabel>DQ Dimension</InputLabel>
              <Select
                value={filterDimension}
                onChange={(e) => setFilterDimension(e.target.value)}
                label="DQ Dimension"
              >
                <MenuItem value="all">All Dimensions</MenuItem>
                <MenuItem value="completeness">Completeness</MenuItem>
                <MenuItem value="validity">Validity</MenuItem>
                <MenuItem value="uniqueness">Uniqueness</MenuItem>
                <MenuItem value="consistency">Consistency</MenuItem>
                <MenuItem value="accuracy">Accuracy</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Version Filter */}
          <Box sx={{ minWidth: 200 }}>
            <FormControl size="small" fullWidth>
              <InputLabel>Version</InputLabel>
              <Select
                value={selectedVersionId}
                onChange={(e) => {
                  setSelectedVersionId(e.target.value);
                  if (onVersionChange) {
                    onVersionChange(e.target.value);
                  }
                }}
                label="Version"
                disabled={versions.length === 0}
                displayEmpty
              >
                {versions.length === 0 ? (
                  <MenuItem value="" disabled>
                    No versions available
                  </MenuItem>
                ) : (
                  versions.map((version) => (
                    <MenuItem key={version.version_id} value={version.version_id}>
                      v{version.version_number} 
                      {version.is_current && ' (Latest)'}
                      {version.version_status && ` - ${version.version_status}`}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
          </Box>

          {/* Actions */}
          <Box sx={{ display: 'flex', gap: 1, ml: 'auto', alignItems: 'center' }}>
            <Typography variant="body2" sx={{ alignSelf: 'center', mr: 1 }}>
              {selectedRules.size} selected
            </Typography>
            
            {/* Resubmit Button - REMOVED: Now handled by "Make Changes" button in ReportOwnerFeedback component */}
            
            {/* Send to Report Owner - Always show if tester has approved rules */}
            {(() => {
              const rulesWithoutDecision = flattenedRules.filter(r => !r.tester_decision).length;
              const approvedRulesCount = flattenedRules.filter(r => r.tester_decision?.toLowerCase() === 'approve' || r.tester_decision?.toLowerCase() === 'approved').length;
              const isDisabled = isReadOnly() || awaitingReportOwnerReview || rulesWithoutDecision > 0 || approvedRulesCount === 0;
              
              console.log('🔘 Send to RO button state:', {
                isReadOnly: isReadOnly(),
                awaitingReportOwnerReview,
                rulesWithoutDecision,
                approvedRulesCount,
                isDisabled,
                reportOwnerCompleted,
                hasExistingAssignment
              });
              
              return (
                <Button
                  size="small"
                  startIcon={<SendIcon />}
                  onClick={handleSendToReportOwner}
                  disabled={isDisabled}
                  color="primary"
                  variant="outlined"
                >
                  {reportOwnerCompleted ? 'Resend Updated Rules to Report Owner' : 
                   hasExistingAssignment ? 'Already Sent to Report Owner' : 
                   'Send Approved Rules to Report Owner'}
                </Button>
              );
            })()}
            
            {/* Bulk Actions */}
            <Button
              size="small"
              startIcon={<ApproveIcon />}
              onClick={handleBulkApprove}
              disabled={isReadOnly() || selectedRules.size === 0 || awaitingReportOwnerReview}
              color="success"
              variant="contained"
            >
              Bulk Approve
            </Button>
            <Button
              size="small"
              startIcon={<RejectIcon />}
              onClick={handleBulkReject}
              disabled={isReadOnly() || selectedRules.size === 0 || awaitingReportOwnerReview}
              color="error"
              variant="contained"
            >
              Bulk Reject
            </Button>
            <Button
              size="small"
              startIcon={<ExportIcon />}
              variant="outlined"
            >
              Export
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Rules Table */}
      <TableContainer component={Paper}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selectedRules.size > 0 && selectedRules.size < filteredRules.length}
                  checked={filteredRules.length > 0 && selectedRules.size === filteredRules.length}
                  onChange={handleSelectAll}
                  disabled={isReadOnly() || awaitingReportOwnerReview}
                />
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Line Item</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 250 }}>Attribute</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>DQ Dimension</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 200 }}>Rule</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 300 }}>Rule Logic</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Status</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 150 }}>Tester Decision</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 150 }}>Report Owner Decision</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredRules.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                  <Typography color="textSecondary">
                    No rules found matching the current filters.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredRules.map((item) => {
                const rule = item;
                const attr = item.attribute;
                
                return (
                  <TableRow 
                    key={item.displayKey}
                    hover
                    selected={selectedRules.has(rule.rule_id)}
                  >
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedRules.has(rule.rule_id)}
                        onChange={() => handleSelectRule(rule.rule_id)}
                        disabled={isReadOnly() || awaitingReportOwnerReview}
                      />
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2">
                        {attr.line_item_number || '-'}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      {renderAttributeBadges(attr)}
                      <Typography variant="caption" color="textSecondary" display="block">
                        {attr.attribute_type} {attr.mandatory ? '• Required' : '• Optional'}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      {getDimensionChip(rule.rule_type)}
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                        {rule.rule_name}
                      </Typography>
                      {rule.rule_description && (
                        <Typography variant="caption" color="textSecondary" display="block">
                          {rule.rule_description}
                        </Typography>
                      )}
                    </TableCell>
                    
                    <TableCell>
                      <Tooltip title={rule.rule_code} arrow>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            maxWidth: 300,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            cursor: 'help'
                          }}
                        >
                          {rule.rule_code ? (rule.rule_code.split('\n')[1]?.trim() || rule.rule_code.substring(0, 50)) + '...' : 'No code available'}
                        </Typography>
                      </Tooltip>
                    </TableCell>
                    
                    <TableCell>
                      {getStatusChip(rule.status)}
                    </TableCell>
                    
                    <TableCell>
                      {getTesterDecisionDisplay(rule)}
                    </TableCell>
                    
                    <TableCell>
                      {getReportOwnerDecisionDisplay(rule)}
                    </TableCell>
                    
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        {rule.status === 'pending' && (
                          <>
                            <Tooltip title={
                              awaitingReportOwnerReview ? "Actions disabled during report owner review" : 
                              !canTesterUpdateDecision(rule) ? "Cannot update decision after report owner approval" :
                              "Approve Rule"
                            }>
                              <span>
                                <IconButton
                                  size="small"
                                  color="success"
                                  onClick={() => handleApproveRule(rule)}
                                  disabled={isReadOnly() || awaitingReportOwnerReview || !canTesterUpdateDecision(rule)}
                                >
                                  <ApproveIcon fontSize="small" />
                                </IconButton>
                              </span>
                            </Tooltip>
                            <Tooltip title={
                              awaitingReportOwnerReview ? "Actions disabled during report owner review" : 
                              !canTesterReject(rule) ? "Cannot reject after report owner has provided feedback" :
                              "Reject Rule"
                            }>
                              <span>
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => handleRejectRule(rule)}
                                  disabled={isReadOnly() || awaitingReportOwnerReview || !canTesterReject(rule)}
                                >
                                  <RejectIcon fontSize="small" />
                                </IconButton>
                              </span>
                            </Tooltip>
                          </>
                        )}
                        
                        {rule.status === 'approved' && (
                          <>
                            <Tooltip title={
                              awaitingReportOwnerReview ? "Actions disabled during report owner review" : 
                              !canTesterUpdateDecision(rule) ? "Cannot reset after report owner approval" :
                              "Reset to Pending"
                            }>
                              <span>
                                <IconButton
                                  size="small"
                                  color="warning"
                                  onClick={() => handleResetToPending(rule)}
                                  disabled={isReadOnly() || awaitingReportOwnerReview || !canTesterUpdateDecision(rule)}
                                >
                                  <UndoIcon fontSize="small" />
                                </IconButton>
                              </span>
                            </Tooltip>
                            <Tooltip title={
                              awaitingReportOwnerReview ? "Actions disabled during report owner review" : 
                              !canTesterReject(rule) ? "Cannot reject after report owner has provided feedback" :
                              "Reject Rule"
                            }>
                              <span>
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => handleRejectRule(rule)}
                                  disabled={isReadOnly() || awaitingReportOwnerReview || !canTesterReject(rule)}
                                >
                                  <RejectIcon fontSize="small" />
                                </IconButton>
                              </span>
                            </Tooltip>
                          </>
                        )}
                        
                        {rule.status === 'rejected' && (
                          <>
                            <Tooltip title={
                              awaitingReportOwnerReview ? "Actions disabled during report owner review" : 
                              !canTesterUpdateDecision(rule) ? "Cannot update decision after report owner approval" :
                              "Approve Rule"
                            }>
                              <span>
                                <IconButton
                                  size="small"
                                  color="success"
                                  onClick={() => handleApproveRule(rule)}
                                  disabled={isReadOnly() || awaitingReportOwnerReview || !canTesterUpdateDecision(rule)}
                                >
                                  <ApproveIcon fontSize="small" />
                                </IconButton>
                              </span>
                            </Tooltip>
                            <Tooltip title={
                              awaitingReportOwnerReview ? "Actions disabled during report owner review" : 
                              !canTesterUpdateDecision(rule) ? "Cannot reset after report owner approval" :
                              "Reset to Pending"
                            }>
                              <span>
                                <IconButton
                                  size="small"
                                  color="warning"
                                  onClick={() => handleResetToPending(rule)}
                                  disabled={isReadOnly() || awaitingReportOwnerReview || !canTesterUpdateDecision(rule)}
                                >
                                  <UndoIcon fontSize="small" />
                                </IconButton>
                              </span>
                            </Tooltip>
                          </>
                        )}
                        
                        {rule.status === 'submitted' && canTesterUpdateDecision(rule) && (
                          <>
                            <Tooltip title="Update decision based on report owner feedback">
                              <span>
                                <IconButton
                                  size="small"
                                  color="success"
                                  onClick={() => handleApproveRule(rule)}
                                  disabled={awaitingReportOwnerReview}
                                >
                                  <ApproveIcon fontSize="small" />
                                </IconButton>
                              </span>
                            </Tooltip>
                            <Tooltip title="Reject rule">
                              <span>
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => handleRejectRule(rule)}
                                  disabled={isReadOnly() || awaitingReportOwnerReview || !canTesterReject(rule)}
                                >
                                  <RejectIcon fontSize="small" />
                                </IconButton>
                              </span>
                            </Tooltip>
                          </>
                        )}
                        
                        {/* Delete button available for all rules */}
                        <Tooltip title={isReadOnly() ? "Version is read-only" : awaitingReportOwnerReview ? "Actions disabled during report owner review" : "Delete Rule"}>
                          <span>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteRule(rule)}
                              disabled={isReadOnly() || awaitingReportOwnerReview}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </span>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Summary Stats */}
      <Paper sx={{ p: 2, mt: 2 }}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, justifyContent: 'space-around' }}>
          <Typography variant="body2" color="textSecondary">
            Total Rules: <strong>{flattenedRules.length}</strong>
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Pending: <strong>{flattenedRules.filter(r => r.status === 'pending').length}</strong>
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Approved: <strong>{flattenedRules.filter(r => r.status === 'approved').length}</strong>
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Needs Review: <strong>{flattenedRules.filter(r => r.status === 'REJECTED').length}</strong>
          </Typography>
        </Box>
      </Paper>

      {/* Individual Approve Dialog */}
      <Dialog open={approveDialogOpen} onClose={() => setApproveDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Approve Rule</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to approve the rule "{selectedRuleForAction?.rule_name}"?
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            label="Notes (Optional)"
            multiline
            rows={3}
            fullWidth
            variant="outlined"
            value={actionNotes}
            onChange={(e) => setActionNotes(e.target.value)}
            placeholder="Add any comments about this approval..."
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApproveDialogOpen(false)}>Cancel</Button>
          <Button onClick={confirmApproveRule} variant="contained" color="success" startIcon={<ApproveIcon />}>
            Approve Rule
          </Button>
        </DialogActions>
      </Dialog>

      {/* Individual Reject Dialog */}
      <Dialog open={rejectDialogOpen} onClose={() => setRejectDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Reject Rule</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to reject the rule "{selectedRuleForAction?.rule_name}"?
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            label="Rejection Reason (Optional)"
            multiline
            rows={3}
            fullWidth
            variant="outlined"
            value={actionNotes}
            onChange={(e) => setActionNotes(e.target.value)}
            placeholder="Explain why this rule is being rejected..."
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectDialogOpen(false)}>Cancel</Button>
          <Button onClick={confirmRejectRule} variant="contained" color="error" startIcon={<RejectIcon />}>
            Reject Rule
          </Button>
        </DialogActions>
      </Dialog>

      {/* Send to Report Owner Dialog */}
      <Dialog open={sendToOwnerDialogOpen} onClose={() => setSendToOwnerDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PersonIcon color="primary" />
          Send to Report Owner for Approval
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will send the rules you have approved to the Report Owner for final approval. Only approved rules will be sent.
          </DialogContentText>
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>Assignment Details:</Typography>
            <Typography variant="body2" color="textSecondary">
              • Total Rules Generated: {flattenedRules.length}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              • Approved by Tester: {flattenedRules.filter(r => r.tester_decision?.toLowerCase() === 'approve' || r.tester_decision?.toLowerCase() === 'approved').length}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              • Rejected by Tester: {flattenedRules.filter(r => r.tester_decision?.toLowerCase() === 'reject' || r.tester_decision?.toLowerCase() === 'rejected').length}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              • Still Pending Decision: {flattenedRules.filter(r => !r.tester_decision).length}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              • Due Date: {new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toLocaleDateString()}
            </Typography>
            {flattenedRules.filter(r => !r.tester_decision).length > 0 && (
              <Typography variant="body2" color="error.main" sx={{ mt: 1, fontWeight: 'bold' }}>
                ⚠️ You must decide on all pending rules before sending to Report Owner
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSendToOwnerDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={confirmSendToReportOwner} 
            variant="contained" 
            color="primary" 
            startIcon={<SendIcon />}
            disabled={
              flattenedRules.filter(r => !r.tester_decision).length > 0 ||
              flattenedRules.filter(r => r.tester_decision?.toLowerCase() === 'approve' || r.tester_decision?.toLowerCase() === 'approved').length === 0
            }
          >
            Send Approved Rules
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Rule Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Delete Rule</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this rule? This action cannot be undone.
          </DialogContentText>
          {selectedRuleForAction && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="subtitle2">Rule: {selectedRuleForAction.rule_name}</Typography>
              <Typography variant="body2" color="textSecondary">
                Type: {selectedRuleForAction.rule_type}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={confirmDeleteRule} variant="contained" color="error" startIcon={<DeleteIcon />}>
            Delete Rule
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Resubmit Dialog - REMOVED: Now handled by "Make Changes" button in ReportOwnerFeedback component */}
      {/* <Dialog open={resubmitDialogOpen} onClose={() => setResubmitDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <UndoIcon color="warning" />
          Resubmit for Report Owner Review
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            The Report Owner has provided feedback on some rules. Creating a new version will allow you to update your decisions based on their feedback.
          </DialogContentText>
          <Box sx={{ mt: 2, p: 2, bgcolor: 'warning.light', borderRadius: 1, color: 'warning.dark' }}>
            <Typography variant="subtitle2" gutterBottom>What will happen:</Typography>
            <Typography variant="body2">
              • A new version will be created
            </Typography>
            <Typography variant="body2">
              • Rules rejected by Report Owner will be reset for your review
            </Typography>
            <Typography variant="body2">
              • You can update decisions based on Report Owner feedback
            </Typography>
            <Typography variant="body2">
              • Report Owner feedback will be preserved
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResubmitDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={async () => {
              try {
                const response = await dataProfilingApi.resubmitAfterFeedback(cycleId, reportId);
                setResubmitDialogOpen(false);
                // Reload the rules with the new version
                await loadAttributesWithRules();
                setError(null);
                // Show success message
                console.log('Resubmission successful:', response);
              } catch (error) {
                console.error('Failed to resubmit:', error);
                setError('Failed to create new version for resubmission');
                setResubmitDialogOpen(false);
              }
            }} 
            color="warning" 
            variant="contained"
          >
            Create New Version
          </Button>
        </DialogActions>
      </Dialog> */}
    </Box>
  );
};

export default CompressedRulesTable;