import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Card,
  CardContent,
  Divider
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Visibility as ViewIcon,
  Assignment as AssignmentIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { dataProfilingApi } from '../../api/dataProfiling';

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
}

interface AssignmentContext {
  cycle_id: number;
  report_id: number;
  phase: string;
  total_rules_generated: number;
  approved_by_tester: number;
  rejected_by_tester: number;
  approved_rule_ids: number[];
  workflow_step: string;
}

interface ReportOwnerRulesApprovalProps {
  cycleId: number;
  reportId: number;
  onAssignmentCompleted?: () => void;
}

const ReportOwnerRulesApproval: React.FC<ReportOwnerRulesApprovalProps> = ({
  cycleId,
  reportId,
  onAssignmentCompleted
}) => {
  const [rules, setRules] = useState<Rule[]>([]);
  const [assignmentContext, setAssignmentContext] = useState<AssignmentContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRule, setSelectedRule] = useState<Rule | null>(null);
  
  // Dialog states
  const [approveDialogOpen, setApproveDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [actionNotes, setActionNotes] = useState<string>('');

  useEffect(() => {
    loadAssignedRules();
  }, [cycleId, reportId]);

  const loadAssignedRules = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔍 Loading assigned rules for Report Owner approval');
      
      const response = await dataProfilingApi.getAssignedRulesForApproval(cycleId, reportId);
      
      console.log('📋 Got assigned rules:', response);
      setRules(response.rules || []);
      setAssignmentContext(response.assignment_context);
      
    } catch (error: any) {
      console.error('❌ Failed to load assigned rules:', error);
      if (error.response?.status === 404) {
        setError('No rules have been assigned to you for approval yet.');
      } else {
        setError('Failed to load assigned rules. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleApproveRule = (rule: Rule) => {
    setSelectedRule(rule);
    setActionNotes('');
    setApproveDialogOpen(true);
  };

  const handleRejectRule = (rule: Rule) => {
    setSelectedRule(rule);
    setActionNotes('');
    setRejectDialogOpen(true);
  };

  const handleViewRule = (rule: Rule) => {
    setSelectedRule(rule);
    setViewDialogOpen(true);
  };

  const confirmApproveRule = async () => {
    if (!selectedRule) return;
    
    try {
      const response = await dataProfilingApi.reportOwnerApproveRule(
        cycleId,
        reportId,
        selectedRule.rule_id, 
        actionNotes || 'Approved by Report Owner'
      );
      
      if (response.assignment_completed) {
        console.log('✅ Assignment completed! All rules have been decided upon.');
        if (onAssignmentCompleted) {
          onAssignmentCompleted();
        }
      }
      
      await loadAssignedRules();
      setApproveDialogOpen(false);
      setSelectedRule(null);
      setActionNotes('');
    } catch (error) {
      console.error('Approve failed:', error);
      setError('Failed to approve rule. Please try again.');
    }
  };

  const confirmRejectRule = async () => {
    if (!selectedRule || !actionNotes.trim() || actionNotes.trim().length < 10) {
      setError('Please provide a meaningful rejection reason (at least 10 characters).');
      return;
    }
    
    try {
      const response = await dataProfilingApi.reportOwnerRejectRule(
        cycleId,
        reportId,
        selectedRule.rule_id, 
        'Rule rejected by Report Owner', 
        actionNotes.trim()
      );
      
      if (response.assignment_completed) {
        console.log('✅ Assignment completed! All rules have been decided upon.');
        if (onAssignmentCompleted) {
          onAssignmentCompleted();
        }
      }
      
      await loadAssignedRules();
      setRejectDialogOpen(false);
      setSelectedRule(null);
      setActionNotes('');
      setError(null); // Clear any previous errors
    } catch (error) {
      console.error('Reject failed:', error);
      setError('Failed to reject rule. Please try again.');
    }
  };

  const getStatusChip = (status: string) => {
    const statusConfig = {
      'PENDING': { color: 'warning' as const, label: 'Awaiting Your Decision' },
      'APPROVED': { color: 'success' as const, label: 'Approved by You' },
      'REJECTED': { color: 'error' as const, label: 'Rejected by You' },
      'NEEDS_REVISION': { color: 'info' as const, label: 'Needs Revision' }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || 
                   { color: 'default' as const, label: status };
    
    return <Chip size="small" color={config.color} label={config.label} />;
  };

  const getDimensionChip = (dimension: string) => {
    const dimensionConfig = {
      'completeness': { color: '#1976d2', label: 'Completeness' },
      'validity': { color: '#388e3c', label: 'Validity' },
      'uniqueness': { color: '#f57c00', label: 'Uniqueness' },
      'consistency': { color: '#7b1fa2', label: 'Consistency' },
      'accuracy': { color: '#d32f2f', label: 'Accuracy' }
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

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading assigned rules...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>

      {/* Assignment Context Card */}
      {assignmentContext && (
        <Card sx={{ mb: 3, bgcolor: 'primary.50' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <PersonIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" color="primary.main">
                Assignment from Tester
              </Typography>
            </Box>
            <Typography variant="body2" color="textSecondary" paragraph>
              The tester has reviewed all generated rules and sent you {assignmentContext.approved_by_tester} approved rules for final approval.
            </Typography>
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              <Typography variant="body2" color="textSecondary">
                <strong>Total Generated:</strong> {assignmentContext.total_rules_generated}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                <strong>Approved by Tester:</strong> {assignmentContext.approved_by_tester}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                <strong>Rejected by Tester:</strong> {assignmentContext.rejected_by_tester}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}

      {rules.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <AssignmentIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" color="textSecondary">
            No rules assigned for approval
          </Typography>
        </Paper>
      ) : (
        <>
          {/* Rules Table */}
          <TableContainer component={Paper}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 250 }}>Attribute</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>DQ Dimension</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 200 }}>Rule</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 300 }}>Rule Logic</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rules.map((rule) => (
                  <TableRow key={rule.rule_id} hover>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {rule.attribute_name}
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
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => handleViewRule(rule)}
                          >
                            <ViewIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        
                        {/* Show approve/reject actions for all pending rules */}
                        {rule.status === 'PENDING' && (
                          <>
                            <Tooltip title="Approve Rule">
                              <IconButton
                                size="small"
                                color="success"
                                onClick={() => handleApproveRule(rule)}
                              >
                                <ApproveIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Reject Rule">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleRejectRule(rule)}
                              >
                                <RejectIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}
                        
                        {/* Show status for already decided rules */}
                        {rule.status === 'APPROVED' && (
                          <Chip size="small" color="success" label="Approved by you" />
                        )}
                        
                        {rule.status === 'REJECTED' && (
                          <Chip size="small" color="error" label="Rejected by you" />
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Summary Stats */}
          <Paper sx={{ p: 2, mt: 2 }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, justifyContent: 'space-around' }}>
              <Typography variant="body2" color="textSecondary">
                Total Rules for Approval: <strong>{rules.length}</strong>
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Pending Your Decision: <strong>{rules.filter(r => r.status === 'PENDING').length}</strong>
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Approved by You: <strong>{rules.filter(r => r.status === 'APPROVED').length}</strong>
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Rejected by You: <strong>{rules.filter(r => r.status === 'REJECTED').length}</strong>
              </Typography>
            </Box>
          </Paper>

          {/* Version Approval Section - Show when all rules have been decided */}
          {rules.length > 0 && rules.filter(r => r.status === 'PENDING').length === 0 && (
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
                        // First check if all decisions match for auto-approval
                        const checkResponse = await dataProfilingApi.checkAndApproveVersion(cycleId, reportId);
                        
                        if (checkResponse.version_approved) {
                          alert(`✅ Version Approved!\n\n${checkResponse.message}`);
                          if (onAssignmentCompleted) {
                            onAssignmentCompleted();
                          }
                        } else {
                          // If not auto-approved, show manual approval dialog
                          const approvalNotes = prompt('Please provide approval notes (optional):');
                          const response = await dataProfilingApi.approveVersion(
                            checkResponse.version_id,
                            true,
                            approvalNotes || undefined
                          );
                          alert(`✅ Version Approved!\n\n${response.message}`);
                          if (onAssignmentCompleted) {
                            onAssignmentCompleted();
                          }
                        }
                      } catch (error) {
                        console.error('Error approving version:', error);
                        alert('Failed to approve version. Please try again.');
                      }
                    }}
                    size="large"
                  >
                    Approve Version
                  </Button>
                  
                  <Button
                    variant="outlined"
                    color="warning"
                    startIcon={<RejectIcon />}
                    onClick={async () => {
                      const notes = prompt('Please provide feedback for changes needed:');
                      if (notes) {
                        try {
                          // Get current version ID
                          const versions = await dataProfilingApi.getVersions(cycleId, reportId);
                          const currentVersion = versions.find(v => v.is_current) || versions[0];
                          
                          const response = await dataProfilingApi.approveVersion(
                            currentVersion.version_id,
                            false,
                            notes
                          );
                          alert(`📝 Changes Requested\n\n${response.message}\n\nThe tester will be notified to make the requested changes.`);
                          if (onAssignmentCompleted) {
                            onAssignmentCompleted();
                          }
                        } catch (error) {
                          console.error('Error requesting changes:', error);
                          alert('Failed to request changes. Please try again.');
                        }
                      }
                    }}
                    size="large"
                  >
                    Request Changes
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* View Rule Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Rule Details</DialogTitle>
        <DialogContent>
          {selectedRule && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedRule.rule_name}
              </Typography>
              <Typography variant="body1" paragraph>
                <strong>Attribute:</strong> {selectedRule.attribute_name}
              </Typography>
              <Typography variant="body1" paragraph>
                <strong>Type:</strong> {selectedRule.rule_type}
              </Typography>
              {selectedRule.rule_description && (
                <Typography variant="body1" paragraph>
                  <strong>Description:</strong> {selectedRule.rule_description}
                </Typography>
              )}
              {selectedRule.rule_code && (
                <>
                  <Typography variant="body1" gutterBottom>
                    <strong>Rule Logic:</strong>
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.100', fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{selectedRule.rule_code}</pre>
                  </Paper>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Approve Dialog */}
      <Dialog open={approveDialogOpen} onClose={() => setApproveDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ bgcolor: 'success.50', color: 'success.main' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ApproveIcon />
            Approve Rule
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Typography variant="h6" gutterBottom>
            "{selectedRule?.rule_name}"
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Attribute: {selectedRule?.attribute_name}
          </Typography>
          
          <Typography variant="body1" gutterBottom sx={{ mt: 3 }}>
            You are approving this rule for data profiling execution.
          </Typography>
          
          <Typography variant="body2" color="info.main" paragraph>
            ℹ️ This rule has been reviewed and approved by the tester. Your approval confirms it meets 
            regulatory requirements and business logic standards.
          </Typography>
          
          <TextField
            margin="dense"
            label="Approval Notes (Optional)"
            multiline
            rows={3}
            fullWidth
            variant="outlined"
            value={actionNotes}
            onChange={(e) => setActionNotes(e.target.value)}
            placeholder="Add any comments about this approval (optional)..."
            sx={{ mt: 2 }}
            inputProps={{ maxLength: 300 }}
            helperText={`${actionNotes.length}/300 characters`}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button onClick={() => setApproveDialogOpen(false)} size="large">
            Cancel
          </Button>
          <Button onClick={confirmApproveRule} variant="contained" color="success" startIcon={<ApproveIcon />} size="large">
            Approve Rule
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reject Dialog - Enhanced with required reasoning */}
      <Dialog open={rejectDialogOpen} onClose={() => setRejectDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ bgcolor: 'error.50', color: 'error.main' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <RejectIcon />
            Reject Rule
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Typography variant="h6" gutterBottom>
            "{selectedRule?.rule_name}"
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Attribute: {selectedRule?.attribute_name}
          </Typography>
          
          <Typography variant="body1" gutterBottom sx={{ mt: 3 }}>
            Please provide a clear explanation for why this rule is being rejected:
          </Typography>
          
          <Typography variant="body2" color="warning.main" paragraph>
            ⚠️ Your feedback will be sent to the tester so they can revise the rule accordingly. 
            Be specific about what needs to be changed.
          </Typography>
          
          <TextField
            autoFocus
            margin="dense"
            label="Rejection Reason *"
            multiline
            rows={4}
            fullWidth
            variant="outlined"
            value={actionNotes}
            onChange={(e) => setActionNotes(e.target.value)}
            placeholder="Examples:\n• The rule logic is incorrect because...\n• The validation criteria should be...\n• This conflicts with regulation X because..."
            sx={{ mt: 2 }}
            required
            error={!actionNotes.trim()}
            helperText={!actionNotes.trim() ? "Rejection reason is required" : `${actionNotes.length}/500 characters`}
            inputProps={{ maxLength: 500 }}
          />
          
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            * This feedback will be visible to the tester for rule revision
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button onClick={() => setRejectDialogOpen(false)} size="large">
            Cancel
          </Button>
          <Button 
            onClick={confirmRejectRule} 
            variant="contained" 
            color="error" 
            startIcon={<RejectIcon />}
            disabled={!actionNotes.trim() || actionNotes.trim().length < 10}
            size="large"
          >
            Reject Rule with Feedback
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ReportOwnerRulesApproval;