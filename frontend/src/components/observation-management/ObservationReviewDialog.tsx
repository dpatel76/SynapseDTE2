import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Chip,
  Box,
  Alert,
  Slider,
  Stack,
  Divider,
  CircularProgress
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  HelpOutline,
  Warning,
  Assessment
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

interface ObservationGroup {
  id: number;
  group_name: string;
  group_description?: string;
  issue_summary: string;
  impact_description?: string;
  proposed_resolution?: string;
  observation_count: number;
  severity_level: 'high' | 'medium' | 'low';
  issue_type: 'data_quality' | 'process_failure' | 'system_error' | 'compliance_gap';
  status: string;
  attribute?: {
    id: number;
    name: string;
  };
  lob?: {
    id: number;
    name: string;
  };
  detector?: {
    id: number;
    name: string;
    email: string;
  };
  created_at: string;
}

interface ObservationReviewDialogProps {
  open: boolean;
  onClose: () => void;
  group: ObservationGroup | null;
  reviewType: 'tester' | 'report_owner';
  onSubmit: (decision: string, notes: string, score?: number) => Promise<void>;
}

const ObservationReviewDialog: React.FC<ObservationReviewDialogProps> = ({
  open,
  onClose,
  group,
  reviewType,
  onSubmit
}) => {
  const theme = useTheme();
  const [decision, setDecision] = useState('');
  const [notes, setNotes] = useState('');
  const [score, setScore] = useState<number>(75);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!decision) {
      setError('Please select a decision');
      return;
    }

    if (decision === 'needs_clarification' && !notes.trim()) {
      setError('Notes are required when requesting clarification');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      await onSubmit(decision, notes, reviewType === 'tester' ? score : undefined);
      
      // Reset form
      setDecision('');
      setNotes('');
      setScore(75);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setDecision('');
      setNotes('');
      setScore(75);
      setError(null);
      onClose();
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return theme.palette.error.main;
      case 'medium': return theme.palette.warning.main;
      case 'low': return theme.palette.info.main;
      default: return theme.palette.grey[500];
    }
  };

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'approved': return <CheckCircle color="success" />;
      case 'rejected': return <Cancel color="error" />;
      case 'needs_clarification': return <HelpOutline color="warning" />;
      default: return null;
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'approved': return theme.palette.success.main;
      case 'rejected': return theme.palette.error.main;
      case 'needs_clarification': return theme.palette.warning.main;
      default: return theme.palette.grey[500];
    }
  };

  if (!group) return null;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Stack direction="row" alignItems="center" spacing={2}>
          <Assessment />
          <Typography variant="h6">
            {reviewType === 'tester' ? 'Tester Review' : 'Report Owner Approval'}
          </Typography>
        </Stack>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {/* Group Information */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {group.group_name}
            </Typography>
            {group.group_description && (
              <Typography variant="body2" color="text.secondary" paragraph>
                {group.group_description}
              </Typography>
            )}
            
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">Attribute</Typography>
                <Typography variant="body2">{group.attribute?.name || 'N/A'}</Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">LOB</Typography>
                <Typography variant="body2">{group.lob?.name || 'N/A'}</Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">Observations Count</Typography>
                <Typography variant="body2">{group.observation_count}</Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">Severity</Typography>
                <Chip
                  label={group.severity_level.toUpperCase()}
                  size="small"
                  sx={{
                    bgcolor: getSeverityColor(group.severity_level),
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">Issue Type</Typography>
                <Typography variant="body2">
                  {group.issue_type.replace('_', ' ').toUpperCase()}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="subtitle2">Detected By</Typography>
                <Typography variant="body2">
                  {group.detector?.name || 'N/A'}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
        
        {/* Issue Summary */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Issue Summary
            </Typography>
            <Typography variant="body2" paragraph>
              {group.issue_summary}
            </Typography>
            
            {group.impact_description && (
              <>
                <Typography variant="subtitle2" gutterBottom>
                  Impact Description
                </Typography>
                <Typography variant="body2" paragraph>
                  {group.impact_description}
                </Typography>
              </>
            )}
            
            {group.proposed_resolution && (
              <>
                <Typography variant="subtitle2" gutterBottom>
                  Proposed Resolution
                </Typography>
                <Typography variant="body2">
                  {group.proposed_resolution}
                </Typography>
              </>
            )}
          </CardContent>
        </Card>
        
        <Divider sx={{ my: 2 }} />
        
        {/* Review Form */}
        <Typography variant="h6" gutterBottom>
          {reviewType === 'tester' ? 'Tester Review' : 'Report Owner Approval'}
        </Typography>
        
        <Grid container spacing={2}>
          <Grid size={{ xs: 12 }}>
            <FormControl fullWidth required>
              <InputLabel>Decision</InputLabel>
              <Select
                value={decision}
                label="Decision"
                onChange={(e) => setDecision(e.target.value)}
                disabled={loading}
              >
                <MenuItem value="approved">
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <CheckCircle color="success" />
                    <Typography>Approved</Typography>
                  </Stack>
                </MenuItem>
                <MenuItem value="rejected">
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <Cancel color="error" />
                    <Typography>Rejected</Typography>
                  </Stack>
                </MenuItem>
                <MenuItem value="needs_clarification">
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <HelpOutline color="warning" />
                    <Typography>Needs Clarification</Typography>
                  </Stack>
                </MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          {reviewType === 'tester' && (
            <Grid size={{ xs: 12 }}>
              <Typography variant="subtitle2" gutterBottom>
                Review Score (1-100)
              </Typography>
              <Box sx={{ px: 2 }}>
                <Slider
                  value={score}
                  onChange={(_, newValue) => setScore(newValue as number)}
                  min={1}
                  max={100}
                  valueLabelDisplay="auto"
                  marks={[
                    { value: 1, label: '1' },
                    { value: 25, label: '25' },
                    { value: 50, label: '50' },
                    { value: 75, label: '75' },
                    { value: 100, label: '100' }
                  ]}
                  disabled={loading}
                />
              </Box>
            </Grid>
          )}
          
          <Grid size={{ xs: 12 }}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label={decision === 'needs_clarification' ? 'Clarification Request (Required)' : 'Notes'}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={
                decision === 'needs_clarification' 
                  ? 'Please specify what clarification is needed...'
                  : 'Add any additional notes or comments...'
              }
              required={decision === 'needs_clarification'}
              disabled={loading}
            />
          </Grid>
        </Grid>
        
        {/* Decision Preview */}
        {decision && (
          <Card sx={{ mt: 2, bgcolor: theme.palette.grey[50] }}>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                {getDecisionIcon(decision)}
                <Typography variant="subtitle2" sx={{ color: getDecisionColor(decision) }}>
                  {decision === 'approved' && 'This observation group will be approved'}
                  {decision === 'rejected' && 'This observation group will be rejected'}
                  {decision === 'needs_clarification' && 'Clarification will be requested'}
                </Typography>
              </Stack>
              {decision === 'needs_clarification' && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  The group will be returned to draft status and the creator will be notified.
                </Typography>
              )}
            </CardContent>
          </Card>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !decision}
          startIcon={loading ? <CircularProgress size={20} /> : getDecisionIcon(decision)}
          sx={{
            bgcolor: decision ? getDecisionColor(decision) : undefined,
            '&:hover': {
              bgcolor: decision ? getDecisionColor(decision) : undefined,
              opacity: 0.9
            }
          }}
        >
          {loading ? 'Processing...' : 'Submit Review'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ObservationReviewDialog;