import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Collapse,
  Tabs,
  Tab,
  Badge,
  Tooltip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControlLabel,
  Radio,
  RadioGroup
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  ExpandMore,
  CheckCircle,
  Cancel,
  Add,
  Remove,
  Info,
  Warning,
  ContentCopy,
  Compare,
  Upload
} from '@mui/icons-material';
import { useWorkflowVersioning } from '../../hooks/useWorkflowVersioning';
import { versioningApi } from '../../api/versioning';
import { 
  SampleDecision, 
  SampleDecisionStatus,
  Sample,
  SampleSelectionVersion 
} from '../../types/versioning';

interface SampleSelectionReviewProps {
  workflowId: string;
  cycleId: number;
  reportId: number;
  versionId: string;
  onComplete: () => void;
}

export const SampleSelectionReview: React.FC<SampleSelectionReviewProps> = ({
  workflowId,
  cycleId,
  reportId,
  versionId,
  onComplete
}) => {
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState<SampleSelectionVersion | null>(null);
  const [samples, setSamples] = useState<SampleDecision[]>([]);
  const [decisions, setDecisions] = useState<Map<string, SampleDecisionStatus>>(new Map());
  const [notes, setNotes] = useState<Map<string, string>>(new Map());
  const [reviewMode, setReviewMode] = useState<'approve' | 'revise'>('approve');
  const [additionalSamples, setAdditionalSamples] = useState<Sample[]>([]);
  const [addSampleDialog, setAddSampleDialog] = useState(false);
  const [selectedTab, setSelectedTab] = useState(0);
  const [bulkAction, setBulkAction] = useState<SampleDecisionStatus | ''>('');
  const [selectedSamples, setSelectedSamples] = useState<Set<string>>(new Set());

  const { submitSampleReview } = useWorkflowVersioning(workflowId);

  useEffect(() => {
    loadVersionData();
  }, [versionId]);

  const loadVersionData = async () => {
    try {
      setLoading(true);
      const [versionData, samplesData] = await Promise.all([
        versioningApi.getSampleSelectionVersion(versionId),
        versioningApi.getSampleDecisions(versionId)
      ]);

      setVersion(versionData.data);
      setSamples(samplesData.data);

      // Initialize decisions based on current status
      const initialDecisions = new Map<string, SampleDecisionStatus>();
      samplesData.data.forEach((sample: SampleDecision) => {
        initialDecisions.set(
          sample.decision_id, 
          sample.decision_status || 'pending'
        );
      });
      setDecisions(initialDecisions);
    } catch (error) {
      console.error('Failed to load version data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDecisionChange = (sampleId: string, status: SampleDecisionStatus) => {
    const newDecisions = new Map(decisions);
    newDecisions.set(sampleId, status);
    setDecisions(newDecisions);
  };

  const handleNoteChange = (sampleId: string, note: string) => {
    const newNotes = new Map(notes);
    newNotes.set(sampleId, note);
    setNotes(newNotes);
  };

  const handleBulkAction = () => {
    if (!bulkAction) return;

    const newDecisions = new Map(decisions);
    selectedSamples.forEach(sampleId => {
      newDecisions.set(sampleId, bulkAction);
    });
    setDecisions(newDecisions);
    setSelectedSamples(new Set());
    setBulkAction('');
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedSamples(new Set(samples.map(s => s.decision_id)));
    } else {
      setSelectedSamples(new Set());
    }
  };

  const handleSampleSelect = (sampleId: string, checked: boolean) => {
    const newSelected = new Set(selectedSamples);
    if (checked) {
      newSelected.add(sampleId);
    } else {
      newSelected.delete(sampleId);
    }
    setSelectedSamples(newSelected);
  };

  const handleAddSample = (sample: Sample) => {
    setAdditionalSamples([...additionalSamples, sample]);
    setAddSampleDialog(false);
  };

  const handleRemoveSample = (index: number) => {
    const newSamples = [...additionalSamples];
    newSamples.splice(index, 1);
    setAdditionalSamples(newSamples);
  };

  const handleSubmitReview = async () => {
    try {
      const decisionArray = Array.from(decisions.entries()).map(([id, status]) => ({
        decision_id: id,
        status,
        notes: notes.get(id)
      }));

      await submitSampleReview(
        versionId,
        decisionArray,
        reviewMode === 'revise',
        reviewMode === 'revise' ? additionalSamples : undefined
      );

      onComplete();
    } catch (error) {
      console.error('Failed to submit review:', error);
    }
  };

  const getStatistics = () => {
    const stats = {
      total: samples.length,
      approved: 0,
      rejected: 0,
      pending: 0,
      needsChanges: 0
    };

    decisions.forEach(status => {
      switch (status) {
        case 'approved':
          stats.approved++;
          break;
        case 'rejected':
          stats.rejected++;
          break;
        case 'needs_changes':
          stats.needsChanges++;
          break;
        default:
          stats.pending++;
      }
    });

    return stats;
  };

  const renderSampleRow = (sample: SampleDecision) => {
    const decision = decisions.get(sample.decision_id) || 'pending';
    const note = notes.get(sample.decision_id) || '';
    const isSelected = selectedSamples.has(sample.decision_id);

    return (
      <TableRow key={sample.decision_id}>
        <TableCell padding="checkbox">
          <Checkbox
            checked={isSelected}
            onChange={(e) => handleSampleSelect(sample.decision_id, e.target.checked)}
          />
        </TableCell>
        <TableCell>{sample.sample_identifier}</TableCell>
        <TableCell>
          <Chip
            label={sample.sample_type}
            size="small"
            variant="outlined"
          />
        </TableCell>
        <TableCell>
          <Chip
            label={sample.recommendation_source}
            size="small"
            color={sample.recommendation_source === 'carried_forward' ? 'secondary' : 'primary'}
          />
        </TableCell>
        <TableCell>
          <FormControl size="small" fullWidth>
            <Select
              value={decision}
              onChange={(e) => handleDecisionChange(
                sample.decision_id, 
                e.target.value as SampleDecisionStatus
              )}
            >
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="approved">Approve</MenuItem>
              <MenuItem value="rejected">Reject</MenuItem>
              <MenuItem value="needs_changes">Needs Changes</MenuItem>
            </Select>
          </FormControl>
        </TableCell>
        <TableCell>
          <TextField
            size="small"
            placeholder="Add notes..."
            value={note}
            onChange={(e) => handleNoteChange(sample.decision_id, e.target.value)}
            multiline
            maxRows={2}
            fullWidth
          />
        </TableCell>
        <TableCell>
          <Tooltip title="View Details">
            <IconButton size="small">
              <Info />
            </IconButton>
          </Tooltip>
        </TableCell>
      </TableRow>
    );
  };

  const renderStatisticsCard = () => {
    const stats = getStatistics();
    const approvalRate = stats.total > 0 ? (stats.approved / stats.total) * 100 : 0;

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Review Statistics
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 3 }}>
              <Box textAlign="center">
                <Typography variant="h4">{stats.total}</Typography>
                <Typography variant="body2" color="textSecondary">
                  Total Samples
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 3 }}>
              <Box textAlign="center">
                <Typography variant="h4" color="success.main">
                  {stats.approved}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Approved
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 3 }}>
              <Box textAlign="center">
                <Typography variant="h4" color="error.main">
                  {stats.rejected}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Rejected
                </Typography>
              </Box>
            </Grid>
            <Grid size={{ xs: 3 }}>
              <Box textAlign="center">
                <Typography variant="h4" color="warning.main">
                  {stats.pending}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Pending
                </Typography>
              </Box>
            </Grid>
          </Grid>
          <Box mt={2}>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Approval Rate
            </Typography>
            <LinearProgress
              variant="determinate"
              value={approvalRate}
              sx={{ height: 10, borderRadius: 5 }}
              color={approvalRate > 80 ? 'success' : approvalRate > 50 ? 'warning' : 'error'}
            />
            <Typography variant="body2" color="textSecondary" align="right">
              {approvalRate.toFixed(1)}%
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return <LinearProgress />;
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Sample Selection Review
      </Typography>
      
      {version && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            Version {version.version_number} - {version.actual_sample_size} samples
            {version.parent_version_id && ' (Revision)'}
          </Typography>
        </Alert>
      )}

      {renderStatisticsCard()}

      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <FormControl component="fieldset">
              <RadioGroup
                row
                value={reviewMode}
                onChange={(e) => setReviewMode(e.target.value as 'approve' | 'revise')}
              >
                <FormControlLabel
                  value="approve"
                  control={<Radio />}
                  label="Approve/Reject Samples"
                />
                <FormControlLabel
                  value="revise"
                  control={<Radio />}
                  label="Request Revision"
                />
              </RadioGroup>
            </FormControl>

            {selectedSamples.size > 0 && (
              <Box display="flex" gap={1} alignItems="center">
                <Typography variant="body2">
                  {selectedSamples.size} selected
                </Typography>
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <Select
                    value={bulkAction}
                    onChange={(e) => setBulkAction(e.target.value as SampleDecisionStatus)}
                    displayEmpty
                  >
                    <MenuItem value="">Bulk Action</MenuItem>
                    <MenuItem value="approved">Approve All</MenuItem>
                    <MenuItem value="rejected">Reject All</MenuItem>
                  </Select>
                </FormControl>
                <Button
                  size="small"
                  variant="contained"
                  onClick={handleBulkAction}
                  disabled={!bulkAction}
                >
                  Apply
                </Button>
              </Box>
            )}
          </Box>

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedSamples.size === samples.length}
                      indeterminate={
                        selectedSamples.size > 0 && 
                        selectedSamples.size < samples.length
                      }
                      onChange={(e) => handleSelectAll(e.target.checked)}
                    />
                  </TableCell>
                  <TableCell>Sample ID</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Source</TableCell>
                  <TableCell>Decision</TableCell>
                  <TableCell>Notes</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {samples.map(sample => renderSampleRow(sample))}
              </TableBody>
            </Table>
          </TableContainer>

          {reviewMode === 'revise' && (
            <Box mt={3}>
              <Typography variant="h6" gutterBottom>
                Additional Samples Required
              </Typography>
              <Box display="flex" gap={2} alignItems="center" mb={2}>
                <Button
                  variant="outlined"
                  startIcon={<Add />}
                  onClick={() => setAddSampleDialog(true)}
                >
                  Add Sample
                </Button>
                <Typography variant="body2" color="textSecondary">
                  {additionalSamples.length} additional samples added
                </Typography>
              </Box>
              
              {additionalSamples.map((sample, index) => (
                <Chip
                  key={index}
                  label={sample.id}
                  onDelete={() => handleRemoveSample(index)}
                  sx={{ mr: 1, mb: 1 }}
                />
              ))}
            </Box>
          )}

          <Box mt={3} display="flex" justifyContent="flex-end" gap={2}>
            <Button variant="outlined" onClick={onComplete}>
              Cancel
            </Button>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSubmitReview}
              disabled={
                reviewMode === 'revise' && additionalSamples.length === 0
              }
            >
              {reviewMode === 'approve' ? 'Submit Review' : 'Request Revision'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Add Sample Dialog */}
      <Dialog
        open={addSampleDialog}
        onClose={() => setAddSampleDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Additional Sample</DialogTitle>
        <DialogContent>
          {/* Add sample form implementation */}
          <Typography>Sample addition form would go here</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddSampleDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => handleAddSample({ 
            sample_id: 'new-sample', 
            sample_identifier: 'New Sample',
            attribute_name: '',
            decision_id: `decision-${Date.now()}`,
            data: {} 
          })}>
            Add Sample
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};