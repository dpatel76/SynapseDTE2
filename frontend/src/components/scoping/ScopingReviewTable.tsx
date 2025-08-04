import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Box,
  Typography,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Collapse,
  Alert
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import apiClient from '../../api/client';

interface TesterDecision {
  scoped: boolean;
  decision: string;
  rationale: string;
  decided_at: string | null;
  decided_by: number;
}

interface ReportOwnerDecision {
  status: string;
  approved_by: number | null;
  approved_at: string | null;
  approval_notes: string | null;
  rejected_by: number | null;
  rejected_at: string | null;
  rejection_reason: string | null;
}

interface ScopedAttribute {
  attribute_id: number;
  attribute_name: string;
  data_type: string;
  is_primary_key: boolean;
  is_cde: boolean;
  has_issues: boolean;
  line_item_number: string | null;
  mdrm: string | null;
  description: string | null;
  llm_risk_score: number;
  llm_rationale: string | null;
  mandatory_flag: string | null;
  tester_decision: TesterDecision;
  report_owner_decision: ReportOwnerDecision;
  current_version: number;
  can_approve: boolean;
  can_reject: boolean;
}

interface ScopingReviewTableProps {
  cycleId: number;
  reportId: number;
  attributes: ScopedAttribute[];
  onAttributeUpdate: () => void;
  showOnlyPending?: boolean;
}

const ScopingReviewTable: React.FC<ScopingReviewTableProps> = ({
  cycleId,
  reportId,
  attributes,
  onAttributeUpdate,
  showOnlyPending = false
}) => {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [approvalDialog, setApprovalDialog] = useState<{
    open: boolean;
    attribute: ScopedAttribute | null;
    action: 'approve' | 'reject';
  }>({ open: false, attribute: null, action: 'approve' });
  const [notes, setNotes] = useState('');
  const [processing, setProcessing] = useState(false);

  const filteredAttributes = showOnlyPending
    ? attributes.filter(attr => attr.report_owner_decision.status === 'Pending')
    : attributes;

  const toggleRowExpansion = (attributeId: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(attributeId)) {
      newExpanded.delete(attributeId);
    } else {
      newExpanded.add(attributeId);
    }
    setExpandedRows(newExpanded);
  };

  const handleApprove = (attribute: ScopedAttribute) => {
    setApprovalDialog({ open: true, attribute, action: 'approve' });
    setNotes('');
  };

  const handleReject = (attribute: ScopedAttribute) => {
    setApprovalDialog({ open: true, attribute, action: 'reject' });
    setNotes('');
  };

  const submitDecision = async () => {
    if (!approvalDialog.attribute) return;

    setProcessing(true);
    try {
      const endpoint = approvalDialog.action === 'approve'
        ? `/scoping/cycles/${cycleId}/reports/${reportId}/attributes/${approvalDialog.attribute.attribute_id}/approve`
        : `/scoping/cycles/${cycleId}/reports/${reportId}/attributes/${approvalDialog.attribute.attribute_id}/reject`;

      const payload = approvalDialog.action === 'approve'
        ? { notes }
        : { reason: notes };

      await apiClient.post(endpoint, payload);
      
      setApprovalDialog({ open: false, attribute: null, action: 'approve' });
      setNotes('');
      onAttributeUpdate();
    } catch (error: any) {
      console.error('Error submitting decision:', error);
      alert(`Failed to ${approvalDialog.action} attribute: ${error.response?.data?.detail || error.message}`);
    } finally {
      setProcessing(false);
    }
  };

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'Approved':
        return <Chip label="Approved" color="success" size="small" />;
      case 'Rejected':
        return <Chip label="Rejected" color="error" size="small" />;
      default:
        return <Chip label="Pending" color="warning" size="small" />;
    }
  };

  const getRiskColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score < 30) return 'success';
    if (score < 70) return 'warning';
    return 'error';
  };

  return (
    <>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell width={50} />
              <TableCell>Attribute</TableCell>
              <TableCell>Data Type</TableCell>
              <TableCell>Risk Score</TableCell>
              <TableCell>Tester Decision</TableCell>
              <TableCell>Report Owner Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredAttributes.map((attr) => {
              const isExpanded = expandedRows.has(attr.attribute_id);
              
              return (
                <React.Fragment key={attr.attribute_id}>
                  <TableRow>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => toggleRowExpansion(attr.attribute_id)}
                      >
                        {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    </TableCell>
                    
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {attr.attribute_name}
                        </Typography>
                        <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5 }}>
                          {attr.is_primary_key && (
                            <Chip label="PK" size="small" color="primary" />
                          )}
                          {attr.is_cde && (
                            <Chip label="CDE" size="small" color="secondary" />
                          )}
                          {attr.has_issues && (
                            <Chip label="Issues" size="small" color="error" />
                          )}
                        </Box>
                      </Box>
                    </TableCell>
                    
                    <TableCell>{attr.data_type}</TableCell>
                    
                    <TableCell>
                      <Chip
                        label={attr.llm_risk_score}
                        color={getRiskColor(attr.llm_risk_score)}
                        size="small"
                      />
                    </TableCell>
                    
                    <TableCell>
                      <Chip
                        label={attr.tester_decision.scoped ? 'Scoped' : 'Not Scoped'}
                        color={attr.tester_decision.scoped ? 'success' : 'default'}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    
                    <TableCell>
                      {getStatusChip(attr.report_owner_decision.status)}
                    </TableCell>
                    
                    <TableCell>
                      {attr.can_approve && (
                        <Tooltip title="Approve">
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => handleApprove(attr)}
                          >
                            <ApproveIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      {attr.can_reject && (
                        <Tooltip title="Reject">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleReject(attr)}
                          >
                            <RejectIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      {attr.current_version > 1 && (
                        <Tooltip title={`Version ${attr.current_version}`}>
                          <IconButton size="small">
                            <HistoryIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                  
                  <TableRow>
                    <TableCell colSpan={7} sx={{ p: 0 }}>
                      <Collapse in={isExpanded}>
                        <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
                          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 3 }}>
                            {/* Tester Decision Details */}
                            <Box>
                              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                Tester Decision
                              </Typography>
                              <Box sx={{ pl: 2 }}>
                                <Typography variant="body2">
                                  <strong>Decision:</strong> {attr.tester_decision.decision || 'Include'}
                                </Typography>
                                <Typography variant="body2">
                                  <strong>Rationale:</strong> {attr.tester_decision.rationale || 'N/A'}
                                </Typography>
                                {attr.tester_decision.decided_at && (
                                  <Typography variant="body2" color="text.secondary">
                                    <strong>Decided:</strong> {new Date(attr.tester_decision.decided_at).toLocaleString()}
                                  </Typography>
                                )}
                              </Box>
                            </Box>
                            
                            {/* Report Owner Decision Details */}
                            <Box>
                              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                                Report Owner Decision
                              </Typography>
                              <Box sx={{ pl: 2 }}>
                                {attr.report_owner_decision.status !== 'Pending' ? (
                                  <>
                                    <Typography variant="body2">
                                      <strong>Status:</strong> {attr.report_owner_decision.status}
                                    </Typography>
                                    {attr.report_owner_decision.approval_notes && (
                                      <Typography variant="body2">
                                        <strong>Notes:</strong> {attr.report_owner_decision.approval_notes}
                                      </Typography>
                                    )}
                                    {attr.report_owner_decision.rejection_reason && (
                                      <Typography variant="body2">
                                        <strong>Reason:</strong> {attr.report_owner_decision.rejection_reason}
                                      </Typography>
                                    )}
                                    {attr.report_owner_decision.approved_at && (
                                      <Typography variant="body2" color="text.secondary">
                                        <strong>Decided:</strong> {new Date(attr.report_owner_decision.approved_at).toLocaleString()}
                                      </Typography>
                                    )}
                                  </>
                                ) : (
                                  <Typography variant="body2" color="text.secondary">
                                    Awaiting decision
                                  </Typography>
                                )}
                              </Box>
                            </Box>
                          </Box>
                          
                          {/* Additional Details */}
                          <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                              Attribute Details
                            </Typography>
                            <Box sx={{ pl: 2 }}>
                              {attr.description && (
                                <Typography variant="body2">
                                  <strong>Description:</strong> {attr.description}
                                </Typography>
                              )}
                              {attr.mdrm && (
                                <Typography variant="body2">
                                  <strong>MDRM:</strong> {attr.mdrm}
                                </Typography>
                              )}
                              {attr.llm_rationale && (
                                <Typography variant="body2">
                                  <strong>LLM Rationale:</strong> {attr.llm_rationale}
                                </Typography>
                              )}
                            </Box>
                          </Box>
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Approval/Rejection Dialog */}
      <Dialog
        open={approvalDialog.open}
        onClose={() => setApprovalDialog({ open: false, attribute: null, action: 'approve' })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {approvalDialog.action === 'approve' ? 'Approve' : 'Reject'} Attribute
        </DialogTitle>
        <DialogContent>
          {approvalDialog.attribute && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                <strong>Attribute:</strong> {approvalDialog.attribute.attribute_name}
              </Typography>
              <Typography variant="body2">
                <strong>Tester Decision:</strong> {approvalDialog.attribute.tester_decision.scoped ? 'Scoped' : 'Not Scoped'}
              </Typography>
            </Box>
          )}
          
          <TextField
            fullWidth
            multiline
            rows={4}
            label={approvalDialog.action === 'approve' ? 'Approval Notes (optional)' : 'Rejection Reason (required)'}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            required={approvalDialog.action === 'reject'}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApprovalDialog({ open: false, attribute: null, action: 'approve' })}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color={approvalDialog.action === 'approve' ? 'success' : 'error'}
            onClick={submitDecision}
            disabled={processing || (approvalDialog.action === 'reject' && !notes.trim())}
          >
            {approvalDialog.action === 'approve' ? 'Approve' : 'Reject'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ScopingReviewTable;