import React, { useState, useMemo } from 'react';
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
  Chip,
  Box,
  Button,
  Tooltip,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  CloudDownload as DownloadIcon,
  Visibility as ViewIcon,
  Send as SendIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { RFIEvidence, Decision, EvidenceStatus, EvidenceType } from '../../types/rfiVersions';

interface RFIEvidenceTableProps {
  evidence: RFIEvidence[];
  isReadOnly: boolean;
  userRole: string;
  onUpdateTesterDecision?: (evidenceId: string, decision: Decision, notes: string) => void;
  onUpdateReportOwnerDecision?: (evidenceId: string, decision: Decision, notes: string) => void;
  onBulkTesterDecision?: (evidenceIds: string[], decision: Decision, notes: string) => void;
  onViewEvidence?: (evidence: RFIEvidence) => void;
  onDownloadEvidence?: (evidence: RFIEvidence) => void;
}

export const RFIEvidenceTable: React.FC<RFIEvidenceTableProps> = ({
  evidence,
  isReadOnly,
  userRole,
  onUpdateTesterDecision,
  onUpdateReportOwnerDecision,
  onBulkTesterDecision,
  onViewEvidence,
  onDownloadEvidence,
}) => {
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<Set<string>>(new Set());
  const [decisionDialogOpen, setDecisionDialogOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState<RFIEvidence | null>(null);
  const [decisionType, setDecisionType] = useState<'tester' | 'report_owner'>('tester');
  const [decision, setDecision] = useState<Decision>(Decision.APPROVED);
  const [notes, setNotes] = useState('');

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelectedEvidenceIds(new Set(evidence.map(e => e.evidence_id)));
    } else {
      setSelectedEvidenceIds(new Set());
    }
  };

  const handleSelectEvidence = (evidenceId: string) => {
    const newSelected = new Set(selectedEvidenceIds);
    if (newSelected.has(evidenceId)) {
      newSelected.delete(evidenceId);
    } else {
      newSelected.add(evidenceId);
    }
    setSelectedEvidenceIds(newSelected);
  };

  const handleOpenDecisionDialog = (evidence: RFIEvidence, type: 'tester' | 'report_owner') => {
    setSelectedEvidence(evidence);
    setDecisionType(type);
    setDecision(Decision.APPROVED);
    setNotes('');
    setDecisionDialogOpen(true);
  };

  const handleConfirmDecision = () => {
    if (selectedEvidence) {
      if (decisionType === 'tester' && onUpdateTesterDecision) {
        onUpdateTesterDecision(selectedEvidence.evidence_id, decision, notes);
      } else if (decisionType === 'report_owner' && onUpdateReportOwnerDecision) {
        onUpdateReportOwnerDecision(selectedEvidence.evidence_id, decision, notes);
      }
    }
    setDecisionDialogOpen(false);
  };

  const handleBulkApprove = () => {
    if (onBulkTesterDecision && selectedEvidenceIds.size > 0) {
      onBulkTesterDecision(Array.from(selectedEvidenceIds), Decision.APPROVED, 'Bulk approved');
      setSelectedEvidenceIds(new Set());
    }
  };

  const handleBulkReject = () => {
    if (onBulkTesterDecision && selectedEvidenceIds.size > 0) {
      onBulkTesterDecision(Array.from(selectedEvidenceIds), Decision.REJECTED, 'Bulk rejected');
      setSelectedEvidenceIds(new Set());
    }
  };

  const getEvidenceStatusChip = (status: EvidenceStatus) => {
    const config = {
      [EvidenceStatus.PENDING]: { color: 'warning' as const, label: 'Pending' },
      [EvidenceStatus.APPROVED]: { color: 'success' as const, label: 'Approved' },
      [EvidenceStatus.REJECTED]: { color: 'error' as const, label: 'Rejected' },
      [EvidenceStatus.REQUEST_CHANGES]: { color: 'info' as const, label: 'Changes Requested' },
    };
    const { color, label } = config[status] || { color: 'default' as const, label: status };
    return <Chip size="small" color={color} label={label} />;
  };

  const getDecisionChip = (decision?: Decision, prefix?: string) => {
    if (!decision) return null;
    
    const config = {
      [Decision.APPROVED]: { color: 'success' as const, label: 'Approved' },
      [Decision.REJECTED]: { color: 'error' as const, label: 'Rejected' },
      [Decision.REQUEST_CHANGES]: { color: 'warning' as const, label: 'Changes Requested' },
    };
    const { color, label } = config[decision] || { color: 'default' as const, label: decision };
    return <Chip size="small" color={color} label={`${prefix || ''}${label}`} sx={{ fontSize: '0.7rem' }} />;
  };

  const getEvidenceTypeIcon = (type: EvidenceType) => {
    return type === EvidenceType.DOCUMENT ? '📄' : '🗄️';
  };

  const canUpdateTesterDecision = userRole === 'Tester' && !isReadOnly;
  const canUpdateReportOwnerDecision = userRole === 'Report Owner';

  const evidenceNeedingTesterDecision = evidence.filter(e => !e.tester_decision);
  const evidenceNeedingReportOwnerDecision = evidence.filter(e => e.tester_decision && !e.report_owner_decision);

  return (
    <Box>
      {/* Action Bar */}
      {canUpdateTesterDecision && selectedEvidenceIds.size > 0 && (
        <Box sx={{ mb: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
          <Typography variant="body2">{selectedEvidenceIds.size} selected</Typography>
          <Button
            size="small"
            startIcon={<ApproveIcon />}
            onClick={handleBulkApprove}
            color="success"
            variant="contained"
          >
            Bulk Approve
          </Button>
          <Button
            size="small"
            startIcon={<RejectIcon />}
            onClick={handleBulkReject}
            color="error"
            variant="contained"
          >
            Bulk Reject
          </Button>
        </Box>
      )}

      {/* Status Summary */}
      {canUpdateTesterDecision && evidenceNeedingTesterDecision.length > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {evidenceNeedingTesterDecision.length} evidence items need your decision
        </Alert>
      )}

      {canUpdateReportOwnerDecision && evidenceNeedingReportOwnerDecision.length > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {evidenceNeedingReportOwnerDecision.length} evidence items need your review
        </Alert>
      )}

      {/* Evidence Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {canUpdateTesterDecision && (
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={selectedEvidenceIds.size > 0 && selectedEvidenceIds.size < evidence.length}
                    checked={evidence.length > 0 && selectedEvidenceIds.size === evidence.length}
                    onChange={handleSelectAll}
                  />
                </TableCell>
              )}
              <TableCell>Test Case</TableCell>
              <TableCell>Attribute</TableCell>
              <TableCell>Data Owner</TableCell>
              <TableCell>Evidence Type</TableCell>
              <TableCell>Submitted</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Tester Decision</TableCell>
              <TableCell>Report Owner Decision</TableCell>
              <TableCell>Final Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {evidence.length === 0 ? (
              <TableRow>
                <TableCell colSpan={canUpdateTesterDecision ? 11 : 10} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">No evidence submitted yet</Typography>
                </TableCell>
              </TableRow>
            ) : (
              evidence.map((item) => (
                <TableRow key={item.evidence_id} hover>
                  {canUpdateTesterDecision && (
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedEvidenceIds.has(item.evidence_id)}
                        onChange={() => handleSelectEvidence(item.evidence_id)}
                      />
                    </TableCell>
                  )}
                  <TableCell>
                    <Typography variant="body2">TC-{item.test_case_id}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {item.sample_id}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{item.attribute_name}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{item.data_owner_name}</Typography>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Typography>{getEvidenceTypeIcon(item.evidence_type)}</Typography>
                      <Typography variant="body2">
                        {item.evidence_type === EvidenceType.DOCUMENT ? 'Document' : 'Data Source'}
                      </Typography>
                    </Box>
                    {item.evidence_type === EvidenceType.DOCUMENT && item.original_filename && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {item.original_filename}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {item.submitted_at ? (
                      <Typography variant="body2">
                        {new Date(item.submitted_at).toLocaleDateString()}
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="text.secondary">-</Typography>
                    )}
                  </TableCell>
                  <TableCell>{getEvidenceStatusChip(item.evidence_status)}</TableCell>
                  <TableCell>
                    {item.tester_decision ? (
                      <Box>
                        {getDecisionChip(item.tester_decision)}
                        {item.tester_notes && (
                          <Tooltip title={item.tester_notes}>
                            <Typography variant="caption" display="block" sx={{ cursor: 'help' }}>
                              Notes available
                            </Typography>
                          </Tooltip>
                        )}
                      </Box>
                    ) : (
                      canUpdateTesterDecision && (
                        <Button
                          size="small"
                          onClick={() => handleOpenDecisionDialog(item, 'tester')}
                          disabled={isReadOnly}
                        >
                          Decide
                        </Button>
                      )
                    )}
                  </TableCell>
                  <TableCell>
                    {item.report_owner_decision ? (
                      <Box>
                        {getDecisionChip(item.report_owner_decision, 'RO: ')}
                        {item.report_owner_notes && (
                          <Tooltip title={item.report_owner_notes}>
                            <Typography variant="caption" display="block" sx={{ cursor: 'help' }}>
                              Notes available
                            </Typography>
                          </Tooltip>
                        )}
                      </Box>
                    ) : (
                      item.tester_decision && canUpdateReportOwnerDecision && (
                        <Button
                          size="small"
                          onClick={() => handleOpenDecisionDialog(item, 'report_owner')}
                        >
                          Review
                        </Button>
                      )
                    )}
                  </TableCell>
                  <TableCell>
                    {item.final_status && (
                      <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                        {item.final_status.replace('_', ' ')}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Tooltip title="View Evidence">
                        <IconButton size="small" onClick={() => onViewEvidence?.(item)}>
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      {item.evidence_type === EvidenceType.DOCUMENT && (
                        <Tooltip title="Download">
                          <IconButton size="small" onClick={() => onDownloadEvidence?.(item)}>
                            <DownloadIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      {canUpdateTesterDecision && item.tester_decision && !isReadOnly && (
                        <Tooltip title="Edit Decision">
                          <IconButton 
                            size="small" 
                            onClick={() => handleOpenDecisionDialog(item, 'tester')}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Decision Dialog */}
      <Dialog open={decisionDialogOpen} onClose={() => setDecisionDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {decisionType === 'tester' ? 'Tester Decision' : 'Report Owner Review'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            {selectedEvidence && (
              <Box>
                <Typography variant="body2" color="text.secondary">Evidence for:</Typography>
                <Typography variant="body1">{selectedEvidence.attribute_name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  Test Case: TC-{selectedEvidence.test_case_id} | Sample: {selectedEvidence.sample_id}
                </Typography>
              </Box>
            )}
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant={decision === Decision.APPROVED ? 'contained' : 'outlined'}
                color="success"
                onClick={() => setDecision(Decision.APPROVED)}
                startIcon={<ApproveIcon />}
              >
                Approve
              </Button>
              <Button
                variant={decision === Decision.REJECTED ? 'contained' : 'outlined'}
                color="error"
                onClick={() => setDecision(Decision.REJECTED)}
                startIcon={<RejectIcon />}
              >
                Reject
              </Button>
              <Button
                variant={decision === Decision.REQUEST_CHANGES ? 'contained' : 'outlined'}
                color="warning"
                onClick={() => setDecision(Decision.REQUEST_CHANGES)}
              >
                Request Changes
              </Button>
            </Box>

            <TextField
              label="Notes"
              multiline
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              fullWidth
              placeholder="Add any comments about your decision..."
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDecisionDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleConfirmDecision} variant="contained">
            Confirm Decision
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};