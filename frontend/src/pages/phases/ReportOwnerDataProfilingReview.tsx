import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
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
  Alert,
  Stack,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Collapse,
  Divider
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as DeclineIcon,
  Comment as CommentIcon,
  Assignment as AssignmentIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Timeline as TimelineIcon,
  Send as SendIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
  Key as KeyIcon,
  Warning as WarningIcon,
  Shield as ShieldIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { dataProfilingApi } from '../../api/dataProfiling';

interface ProfilingRule {
  rule_id: string;  // UUID
  version_id: string;  // UUID of the version this rule belongs to
  attribute_id: number;
  attribute_name: string;
  rule_name: string;
  rule_type: string;
  rule_description: string;
  rule_code?: string;
  llm_rationale?: string;
  regulatory_reference?: string;
  is_executable: boolean;
  status: string;
  tester_decision?: string;  // 'approved', 'rejected', etc.
  tester_notes?: string;
  report_owner_decision?: string;
  report_owner_notes?: string;
  // Attribute metadata from planning
  line_item_number?: string;
  is_primary_key?: boolean;
  cde_flag?: boolean;
  historical_issues_flag?: boolean;
}

interface RuleDecision {
  decision: 'APPROVED' | 'REJECTED';
  reason?: string;
  notes?: string;
}

interface ReportInfo {
  report_id: number;
  report_name: string;
  lob_name: string;  // Changed from 'lob' to 'lob_name' to match backend
  assigned_tester?: string;
  report_owner?: string;
}

interface Assignment {
  assignment_id: string;
  from_user_name: string;
  title: string;
  context_data: {
    approved_rule_ids: number[];
    report_owner_decisions: Record<string, RuleDecision>;
  };
}

const ReportOwnerDataProfilingReview: React.FC = () => {
  const { cycleId, reportId } = useParams<{ cycleId: string; reportId: string }>();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [rules, setRules] = useState<ProfilingRule[]>([]);
  const [reportInfo, setReportInfo] = useState<ReportInfo | null>(null);
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [decisions, setDecisions] = useState<Record<string, RuleDecision>>({});
  const [expandedRules, setExpandedRules] = useState<Set<string>>(new Set());
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [overallComments, setOverallComments] = useState('');
  const [autoSaveStatus, setAutoSaveStatus] = useState<string>('');

  const cycleIdNum = parseInt(cycleId || '0');
  const reportIdNum = parseInt(reportId || '0');
  
  // Debounce timer refs for notes fields
  const notesDebounceRefs = useRef<Record<string, NodeJS.Timeout>>({});

  useEffect(() => {
    if (currentUser?.role !== 'Report Owner') {
      navigate('/dashboard');
      return;
    }
    loadReviewData();

    // Cleanup debounce timers on unmount
    return () => {
      Object.values(notesDebounceRefs.current).forEach(timer => clearTimeout(timer));
    };
  }, [cycleId, reportId]);

  const loadReviewData = async () => {
    try {
      setLoading(true);
      
      // Load report info
      const reportResponse = await apiClient.get(`/reports/${reportIdNum}`);
      setReportInfo(reportResponse.data);

      // Load assignments for the current user
      const assignmentResponse = await apiClient.get('/universal-assignments/assignments', {
        params: {
          status_filter: 'Assigned,Acknowledged,In Progress',
          assignment_type_filter: 'Rule Approval'
        }
      });

      const assignments = assignmentResponse.data;
      // Find the Rule Approval assignment for this specific report
      const ruleApprovalAssignment = assignments.find(
        (a: any) => a.assignment_type === 'Rule Approval' && 
                    a.to_role === 'Report Owner' &&
                    a.context_data?.cycle_id === cycleIdNum &&
                    a.context_data?.report_id === reportIdNum
      );

      if (!ruleApprovalAssignment) {
        console.error('No rule approval assignment found. Assignments:', assignments);
        console.error('Current user:', currentUser);
        throw new Error('No rule approval assignment found');
      }
      
      // Verify the current user is the report owner
      if (ruleApprovalAssignment.to_user_id && ruleApprovalAssignment.to_user_id !== currentUser?.user_id) {
        console.warn('Assignment is for a different user:', ruleApprovalAssignment.to_user_id, 'Current user:', currentUser?.user_id);
      }

      setAssignment(ruleApprovalAssignment);

      // Get the version_id from the assignment
      const versionId = ruleApprovalAssignment.context_data.version_id;
      if (!versionId) {
        throw new Error('No version_id found in assignment');
      }

      // Load all rules from this version that have been approved by the tester
      const rulesResponse = await apiClient.get(
        `/data-profiling/cycles/${cycleIdNum}/reports/${reportIdNum}/rules`
      );
      
      const allRules = rulesResponse.data;
      // Filter rules that:
      // 1. Belong to this version
      // 2. Have been approved by the tester (tester_decision = 'approved')
      const rulesToReview = allRules.filter((rule: ProfilingRule) => 
        rule.version_id === versionId && 
        rule.tester_decision === 'approved'
      );
      
      setRules(rulesToReview);
      
      // Debug: Log first few rules to check line_item_number
      console.log('Sample rules data:', rulesToReview.slice(0, 3).map((r: ProfilingRule) => ({
        rule_id: r.rule_id,
        attribute_name: r.attribute_name,
        line_item_number: r.line_item_number,
        is_primary_key: r.is_primary_key,
        cde_flag: r.cde_flag
      })));

      // Initialize decisions from existing rule data
      const initialDecisions: Record<string, RuleDecision> = {};
      
      rulesToReview.forEach((rule: ProfilingRule) => {
        // Check if the rule already has a report owner decision
        if (rule.report_owner_decision) {
          initialDecisions[rule.rule_id] = {
            decision: rule.report_owner_decision.toUpperCase() as 'APPROVED' | 'REJECTED',
            notes: rule.report_owner_notes || '',
            reason: rule.report_owner_notes || '' // Use notes as reason for rejected rules
          };
        }
      });
      
      setDecisions(initialDecisions);
      
    } catch (error) {
      console.error('Error loading review data:', error);
      setRules([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDecisionChange = async (ruleId: string, decision: 'APPROVED' | 'REJECTED') => {
    // Update local state immediately
    setDecisions(prev => ({
      ...prev,
      [ruleId]: {
        ...prev[ruleId],
        decision
      }
    }));

    // Auto-save the decision to backend
    try {
      setAutoSaveStatus('Saving...');
      await apiClient.put(
        `/data-profiling/cycles/${cycleIdNum}/reports/${reportIdNum}/rules/${ruleId}/report-owner-decision`,
        {
          decision: decision.toLowerCase(),
          reason: decisions[ruleId]?.reason || '',
          notes: decisions[ruleId]?.notes || ''
        }
      );
      console.log(`Auto-saved decision for rule ${ruleId}: ${decision}`);
      setAutoSaveStatus('Saved');
      setTimeout(() => setAutoSaveStatus(''), 2000);
    } catch (error) {
      console.error('Error auto-saving decision:', error);
      setAutoSaveStatus('Error saving');
      setTimeout(() => setAutoSaveStatus(''), 3000);
      // Show error notification but don't revert the UI
      // The user can still submit all decisions at the end
    }
  };

  const handleNotesChange = (ruleId: string, field: 'reason' | 'notes', value: string) => {
    // Update local state immediately
    setDecisions(prev => ({
      ...prev,
      [ruleId]: {
        ...prev[ruleId],
        [field]: value
      }
    }));

    // Clear existing debounce timer for this field
    const debounceKey = `${ruleId}-${field}`;
    if (notesDebounceRefs.current[debounceKey]) {
      clearTimeout(notesDebounceRefs.current[debounceKey]);
    }

    // Only auto-save if there's already a decision made
    const currentDecision = decisions[ruleId]?.decision;
    if (currentDecision) {
      // Set new debounce timer (500ms delay)
      notesDebounceRefs.current[debounceKey] = setTimeout(async () => {
        try {
          setAutoSaveStatus('Saving...');
          await apiClient.put(
            `/data-profiling/cycles/${cycleIdNum}/reports/${reportIdNum}/rules/${ruleId}/report-owner-decision`,
            {
              decision: currentDecision.toLowerCase(),
              reason: field === 'reason' ? value : (decisions[ruleId]?.reason || ''),
              notes: field === 'notes' ? value : (decisions[ruleId]?.notes || '')
            }
          );
          console.log(`Auto-saved ${field} for rule ${ruleId}`);
          setAutoSaveStatus('Saved');
          setTimeout(() => setAutoSaveStatus(''), 2000);
        } catch (error) {
          console.error(`Error auto-saving ${field}:`, error);
          setAutoSaveStatus('Error saving');
          setTimeout(() => setAutoSaveStatus(''), 3000);
        }
      }, 500);
    }
  };

  const toggleRuleExpansion = (ruleId: string) => {
    setExpandedRules(prev => {
      const newSet = new Set(prev);
      if (newSet.has(ruleId)) {
        newSet.delete(ruleId);
      } else {
        newSet.add(ruleId);
      }
      return newSet;
    });
  };

  const getUndecidedRules = () => {
    const undecided = rules.filter(rule => !decisions[rule.rule_id]?.decision);
    console.log('Undecided rules:', undecided.length, 'out of', rules.length, 'total rules');
    console.log('Current decisions:', decisions);
    return undecided;
  };

  const getApprovedRules = () => {
    return rules.filter(rule => decisions[rule.rule_id]?.decision === 'APPROVED');
  };

  const getRejectedRules = () => {
    return rules.filter(rule => decisions[rule.rule_id]?.decision === 'REJECTED');
  };

  const getDimensionChip = (ruleType: string) => {
    const dimensionConfig: Record<string, { color: any; label: string }> = {
      'completeness': { color: 'primary', label: 'Completeness' },
      'validity': { color: 'secondary', label: 'Validity' },
      'uniqueness': { color: 'success', label: 'Uniqueness' },
      'consistency': { color: 'warning', label: 'Consistency' },
      'accuracy': { color: 'info', label: 'Accuracy' }
    };
    
    const config = dimensionConfig[ruleType.toLowerCase()] || 
                   { color: 'default', label: ruleType };
    
    return <Chip size="small" color={config.color} label={config.label} sx={{ fontSize: '0.7rem' }} />;
  };

  const renderAttributeBadges = (rule: ProfilingRule) => {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
          {rule.attribute_name}
        </Typography>
        {rule.is_primary_key && (
          <Tooltip title="Primary Key">
            <KeyIcon sx={{ fontSize: 16, color: 'primary.main' }} />
          </Tooltip>
        )}
        {rule.cde_flag && (
          <Tooltip title="Critical Data Element">
            <ShieldIcon sx={{ fontSize: 16, color: 'warning.main' }} />
          </Tooltip>
        )}
        {rule.historical_issues_flag && (
          <Tooltip title="Historical Issues">
            <WarningIcon sx={{ fontSize: 16, color: 'error.main' }} />
          </Tooltip>
        )}
      </Box>
    );
  };

  const handleSubmitReview = async () => {
    try {
      setLoading(true);
      
      // Update each rule decision
      for (const [ruleId, decision] of Object.entries(decisions)) {
        if (decision.decision) {
          await apiClient.put(
            `/data-profiling/cycles/${cycleIdNum}/reports/${reportIdNum}/rules/${ruleId}/report-owner-decision`,
            {
              decision: decision.decision.toLowerCase(),  // Convert to lowercase to match backend enum
              reason: decision.reason || '',
              notes: decision.notes || ''
            }
          );
        }
      }

      // Check if all decisions match for auto-approval
      let versionProcessed = false;
      try {
        const approvalResponse = await apiClient.post(
          `/data-profiling/cycles/${cycleIdNum}/reports/${reportIdNum}/check-and-approve-version`
        );
        
        if (approvalResponse.data.version_approved) {
          alert(`✅ Version Automatically Approved!\n\n${approvalResponse.data.message}\n\nAll tester and report owner decisions match.`);
          versionProcessed = true;
        } else if (approvalResponse.data.mismatches && approvalResponse.data.mismatches.length > 0) {
          // Check current status from response
          const currentStatus = approvalResponse.data.current_status;
          
          // Only try to approve/reject if version is still pending approval
          if (currentStatus === 'pending_approval' || currentStatus === 'PENDING_APPROVAL') {
            // Show version approval dialog if there are mismatches
            const approve = window.confirm(
              `⚠️ Decision Mismatches Found\n\n${approvalResponse.data.message}\n\nWould you like to approve the version anyway?\n\nClick OK to approve, Cancel to request changes.`
            );
            
            if (approve) {
              const notes = prompt('Please provide approval notes (optional):');
              if (notes !== null) {  // User didn't cancel the prompt
                try {
                  await apiClient.post(
                    `/data-profiling/versions/${approvalResponse.data.version_id}/approve`,
                    {
                      approved: true,
                      approval_notes: notes || 'Approved by report owner despite mismatches'
                    }
                  );
                  alert('✅ Version Approved Successfully!');
                  versionProcessed = true;
                } catch (error: any) {
                  console.error('Error approving version:', error);
                  if (error.response?.status !== 400) {  // Only show error if it's not a status issue
                    alert(`Failed to approve version: ${error.response?.data?.detail || error.message}`);
                  }
                }
              }
            } else {
              const notes = prompt('Please provide feedback for changes needed:');
              if (notes) {
                try {
                  await apiClient.post(
                    `/data-profiling/versions/${approvalResponse.data.version_id}/approve`,
                    {
                      approved: false,
                      approval_notes: notes
                    }
                  );
                  alert('📝 Changes Requested\n\nThe tester will be notified to make the requested changes.');
                  versionProcessed = true;
                } catch (error: any) {
                  console.error('Error requesting changes:', error);
                  if (error.response?.status !== 400) {  // Only show error if it's not a status issue
                    alert(`Failed to request changes: ${error.response?.data?.detail || error.message}`);
                  }
                }
              }
            }
          } else if (currentStatus === 'rejected') {
            // Version was already rejected (possibly by updating rule decisions)
            alert(`📝 Version Already Rejected\n\nThe version has been rejected based on your rule decisions.`);
            versionProcessed = true;
          } else if (currentStatus === 'approved') {
            // Version was already approved
            alert(`✅ Version Already Approved\n\nThe version has been approved.`);
            versionProcessed = true;
          } else {
            // Version is in some other status
            alert(`⚠️ Decision Mismatches Found\n\n${approvalResponse.data.message}\n\nNote: Version status is ${currentStatus} and cannot be modified.`);
          }
        }
      } catch (approvalError: any) {
        console.warn('Could not check version approval:', approvalError);
        // Continue - this is not critical for rule review submission
      }

      // Mark the assignment as completed
      if (assignment) {
        try {
          await apiClient.post(
            `/universal-assignments/assignments/${assignment.assignment_id}/complete`,
            {
              notes: overallComments || `Reviewed ${rules.length} data profiling rules`,
              completion_data: {
                rules_reviewed: rules.length,
                rules_approved: getApprovedRules().length,
                rules_rejected: getRejectedRules().length,
                review_completed_at: new Date().toISOString()
              }
            }
          );
        } catch (completeError: any) {
          console.error('Error completing assignment:', completeError);
          // Continue even if assignment completion fails
        }
      }

      // Navigate back to dashboard with success message
      navigate('/report-owner-dashboard', { 
        state: { 
          message: 'Data profiling rules review submitted successfully',
          severity: 'success'
        }
      });
      
    } catch (error: any) {
      console.error('Error submitting review:', error);
      alert(`Failed to submit review: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !assignment) {
    return (
      <Container maxWidth={false} sx={{ py: 3 }}>
        <Typography variant="h4" gutterBottom>Loading Data Profiling Review...</Typography>
        <LinearProgress />
      </Container>
    );
  }

  if (!assignment || rules.length === 0) {
    return (
      <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
        <Alert severity="warning">
          No data profiling rules found for review.
        </Alert>
        <Button 
          variant="contained" 
          onClick={() => navigate('/report-owner-dashboard')}
          sx={{ mt: 2 }}
        >
          Back to Dashboard
        </Button>
      </Container>
    );
  }

  const undecidedCount = getUndecidedRules().length;
  const approvedCount = getApprovedRules().length;
  const rejectedCount = getRejectedRules().length;

  // Debug logging for version approval visibility
  console.log('Version approval visibility check:', {
    rulesLength: rules.length,
    undecidedCount,
    shouldShowApproval: rules.length > 0 && undecidedCount === 0,
    decisions,
    rules: rules.map(r => ({ id: r.rule_id, name: r.rule_name }))
  });

  return (
    <Container maxWidth={false} sx={{ py: 3, px: 2, overflow: 'hidden' }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          <AssignmentIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Data Profiling Rules Review: {reportInfo?.report_name || `Report ${reportIdNum}`}
        </Typography>
        
        {/* Report Info Card */}
        <Card sx={{ mb: 2 }}>
          <CardContent sx={{ py: 1.5 }}>
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', alignItems: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <BusinessIcon color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">LOB:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportInfo?.lob_name || 'Unknown'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon color="action" fontSize="small" />
                <Typography variant="body2" color="text.secondary">Submitted by:</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {assignment.from_user_name}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color="text.secondary">Total Rules:</Typography>
                <Chip label={rules.length} color="primary" size="small" />
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Decision Summary */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Review Progress</Typography>
            {autoSaveStatus && (
              <Chip 
                label={autoSaveStatus} 
                size="small" 
                color={autoSaveStatus === 'Saved' ? 'success' : autoSaveStatus === 'Error saving' ? 'error' : 'default'}
                variant="outlined"
              />
            )}
          </Box>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Chip 
              label={`${undecidedCount} Pending`} 
              color={undecidedCount > 0 ? "warning" : "default"}
              variant={undecidedCount > 0 ? "filled" : "outlined"}
            />
            <Chip 
              label={`${approvedCount} Approved`} 
              color="success" 
              variant={approvedCount > 0 ? "filled" : "outlined"}
            />
            <Chip 
              label={`${rejectedCount} Rejected`} 
              color="error"
              variant={rejectedCount > 0 ? "filled" : "outlined"}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Rules Table - Single view without tabs */}
      <TableContainer component={Paper}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Line Item</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 250 }}>Attribute</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>DQ Dimension</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 200 }}>Rule</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 300 }}>Rule Description</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 150 }}>Tester Decision</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 120, textAlign: 'center' }}>Your Decision</TableCell>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rules.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <Typography color="textSecondary">
                    No rules found for review.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              rules.map((rule) => {
                const decision = decisions[rule.rule_id];
                const isExpanded = expandedRules.has(rule.rule_id);
                
                return (
                  <React.Fragment key={rule.rule_id}>
                    <TableRow hover>
                      <TableCell>
                        <Typography variant="body2">
                          {rule.line_item_number || '-'}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        {renderAttributeBadges(rule)}
                      </TableCell>
                      
                      <TableCell>
                        {getDimensionChip(rule.rule_type)}
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {rule.rule_name}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Tooltip title={rule.rule_description} arrow>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              maxWidth: 300,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {rule.rule_description}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Chip 
                            size="small" 
                            color="success" 
                            label="Tester Approved" 
                            sx={{ fontSize: '0.7rem' }}
                          />
                          {rule.tester_notes && (
                            <Tooltip title={`Tester Notes: ${rule.tester_notes}`}>
                              <InfoIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                            </Tooltip>
                          )}
                        </Box>
                      </TableCell>
                      
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1 }}>
                          <Tooltip title="Approve Rule">
                            <IconButton
                              size="small"
                              color={decision?.decision === 'APPROVED' ? 'success' : 'default'}
                              onClick={() => handleDecisionChange(rule.rule_id, 'APPROVED')}
                              sx={{
                                border: decision?.decision === 'APPROVED' ? '2px solid' : '1px solid',
                                borderColor: decision?.decision === 'APPROVED' ? 'success.main' : 'divider',
                                bgcolor: decision?.decision === 'APPROVED' ? 'success.light' : 'transparent',
                                '&:hover': {
                                  bgcolor: 'success.light',
                                  borderColor: 'success.main'
                                }
                              }}
                            >
                              <ThumbUpIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          
                          <Tooltip title="Reject Rule">
                            <IconButton
                              size="small"
                              color={decision?.decision === 'REJECTED' ? 'error' : 'default'}
                              onClick={() => handleDecisionChange(rule.rule_id, 'REJECTED')}
                              sx={{
                                border: decision?.decision === 'REJECTED' ? '2px solid' : '1px solid',
                                borderColor: decision?.decision === 'REJECTED' ? 'error.main' : 'divider',
                                bgcolor: decision?.decision === 'REJECTED' ? 'error.light' : 'transparent',
                                '&:hover': {
                                  bgcolor: 'error.light',
                                  borderColor: 'error.main'
                                }
                              }}
                            >
                              <ThumbDownIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                      
                      <TableCell align="center">
                        <IconButton 
                          size="small" 
                          onClick={() => toggleRuleExpansion(rule.rule_id)}
                        >
                          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                      </TableCell>
                    </TableRow>
                    
                    {/* Expanded details */}
                    <TableRow>
                      <TableCell colSpan={8} sx={{ py: 0 }}>
                        <Collapse in={isExpanded}>
                          <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
                            <Typography variant="body2" paragraph>
                              <strong>Full Description:</strong> {rule.rule_description}
                            </Typography>
                            
                            {rule.llm_rationale && (
                              <Typography variant="body2" paragraph>
                                <strong>AI Rationale:</strong> {rule.llm_rationale}
                              </Typography>
                            )}
                            
                            {rule.regulatory_reference && (
                              <Typography variant="body2" paragraph>
                                <strong>Regulatory Reference:</strong> {rule.regulatory_reference}
                              </Typography>
                            )}
                            
                            {decision?.decision === 'REJECTED' && (
                              <Box sx={{ mt: 2 }}>
                                <TextField
                                  fullWidth
                                  label="Reason for Rejection (Required)"
                                  value={decision.reason || ''}
                                  onChange={(e) => handleNotesChange(rule.rule_id, 'reason', e.target.value)}
                                  required
                                  multiline
                                  rows={2}
                                  sx={{ mb: 1 }}
                                />
                                <TextField
                                  fullWidth
                                  label="Additional Notes (Optional)"
                                  value={decision.notes || ''}
                                  onChange={(e) => handleNotesChange(rule.rule_id, 'notes', e.target.value)}
                                  multiline
                                  rows={2}
                                />
                              </Box>
                            )}
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </React.Fragment>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Version Approval Section - Show when all rules have been decided */}
      {rules.length > 0 && undecidedCount === 0 && (
        <Card sx={{ mt: 3, bgcolor: 'info.50' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom color="info.main">
              Version Approval
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Alert severity="info" sx={{ mb: 2 }}>
              All rules have been reviewed. You can now approve or request changes for this version.
            </Alert>
            
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 3 }}>
              <Button
                variant="contained"
                color="success"
                startIcon={<ApproveIcon />}
                onClick={async () => {
                  try {
                    setLoading(true);
                    // Save all decisions first
                    for (const [ruleId, decision] of Object.entries(decisions)) {
                      if (decision.decision) {
                        await apiClient.put(
                          `/data-profiling/cycles/${cycleIdNum}/reports/${reportIdNum}/rules/${ruleId}/report-owner-decision`,
                          {
                            decision: decision.decision.toLowerCase(),
                            reason: decision.reason || '',
                            notes: decision.notes || ''
                          }
                        );
                      }
                    }
                    
                    // Check if all decisions match for auto-approval
                    const checkResponse = await dataProfilingApi.checkAndApproveVersion(cycleIdNum, reportIdNum);
                    
                    if (checkResponse.version_approved) {
                      alert(`✅ Version Approved!\\n\\n${checkResponse.message}`);
                      navigate('/report-owner-dashboard', { 
                        state: { 
                          message: 'Version approved successfully',
                          severity: 'success'
                        }
                      });
                    } else {
                      // If not auto-approved, show manual approval dialog
                      const approvalNotes = prompt('Please provide approval notes (optional):');
                      await dataProfilingApi.approveVersion(
                        checkResponse.version_id,
                        true,
                        approvalNotes || undefined
                      );
                      alert(`✅ Version Approved!`);
                      navigate('/report-owner-dashboard', { 
                        state: { 
                          message: 'Version approved successfully',
                          severity: 'success'
                        }
                      });
                    }
                  } catch (error: any) {
                    console.error('Error approving version:', error);
                    alert(`Failed to approve version: ${error.response?.data?.detail || error.message}`);
                  } finally {
                    setLoading(false);
                  }
                }}
                size="large"
                disabled={loading}
              >
                Approve Version
              </Button>
              
              <Button
                variant="outlined"
                color="warning"
                startIcon={<DeclineIcon />}
                onClick={async () => {
                  const notes = prompt('Please provide feedback for changes needed:');
                  if (notes) {
                    try {
                      setLoading(true);
                      // Save all decisions first
                      for (const [ruleId, decision] of Object.entries(decisions)) {
                        if (decision.decision) {
                          await apiClient.put(
                            `/data-profiling/cycles/${cycleIdNum}/reports/${reportIdNum}/rules/${ruleId}/report-owner-decision`,
                            {
                              decision: decision.decision.toLowerCase(),
                              reason: decision.reason || '',
                              notes: decision.notes || ''
                            }
                          );
                        }
                      }
                      
                      // Get current version ID
                      const versions = await dataProfilingApi.getVersions(cycleIdNum, reportIdNum);
                      const currentVersion = versions.find((v: any) => v.is_current) || versions[0];
                      
                      const response = await dataProfilingApi.approveVersion(
                        currentVersion.version_id,
                        false,
                        notes
                      );
                      alert(`📝 Changes Requested\\n\\nThe tester will be notified to make the requested changes.`);
                      navigate('/report-owner-dashboard', { 
                        state: { 
                          message: 'Changes requested for version',
                          severity: 'warning'
                        }
                      });
                    } catch (error: any) {
                      console.error('Error requesting changes:', error);
                      alert(`Failed to request changes: ${error.response?.data?.detail || error.message}`);
                    } finally {
                      setLoading(false);
                    }
                  }
                }}
                size="large"
                disabled={loading}
              >
                Request Changes
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Submit Button */}
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button
          variant="outlined"
          onClick={() => navigate('/report-owner-dashboard')}
        >
          Cancel
        </Button>
        {undecidedCount > 0 && (
          <Button
            variant="contained"
            color="primary"
            startIcon={<SendIcon />}
            onClick={() => setShowReviewDialog(true)}
            disabled={undecidedCount > 0}
          >
            Submit Review ({rules.length - undecidedCount}/{rules.length} decided)
          </Button>
        )}
      </Box>

      {/* Confirmation Dialog */}
      <Dialog open={showReviewDialog} onClose={() => setShowReviewDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Submit Data Profiling Rules Review</DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            You have reviewed all {rules.length} rules:
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="success.main">
              • {approvedCount} rules approved
            </Typography>
            <Typography variant="body2" color="error.main">
              • {rejectedCount} rules rejected with feedback
            </Typography>
          </Box>
          <TextField
            fullWidth
            label="Overall Comments (Optional)"
            value={overallComments}
            onChange={(e) => setOverallComments(e.target.value)}
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowReviewDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleSubmitReview} 
            variant="contained" 
            color="primary"
            disabled={loading}
          >
            Submit Review
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ReportOwnerDataProfilingReview;