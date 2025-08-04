import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  Alert,
  Divider,
  Chip,
  Stack
} from '@mui/material';
import {
  Send as SendIcon,
  CheckCircle as IncludedIcon,
  Cancel as ExcludedIcon,
  Warning as WarningIcon
} from '@mui/icons-material';

interface ScopingSubmissionDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (notes: string) => void;
  includedCount: number;
  excludedCount: number;
  totalCount: number;
  hasChanges: boolean;
  previousVersion?: {
    version: number;
    includedCount: number;
    excludedCount: number;
  };
}

export const ScopingSubmissionDialog: React.FC<ScopingSubmissionDialogProps> = ({
  open,
  onClose,
  onSubmit,
  includedCount,
  excludedCount,
  totalCount,
  hasChanges,
  previousVersion
}) => {
  const [submissionNotes, setSubmissionNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await onSubmit(submissionNotes);
      setSubmissionNotes('');
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const coveragePercentage = Math.round((includedCount / totalCount) * 100);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        Submit Scoping Decisions for Approval
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Decision Summary
          </Typography>
          
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            <Chip
              icon={<IncludedIcon />}
              label={`${includedCount} Included`}
              color="success"
              variant="outlined"
            />
            <Chip
              icon={<ExcludedIcon />}
              label={`${excludedCount} Excluded`}
              color="error"
              variant="outlined"
            />
            <Chip
              label={`${coveragePercentage}% Coverage`}
              color="primary"
              variant="filled"
            />
          </Stack>

          {previousVersion && hasChanges && (
            <>
              <Divider sx={{ my: 2 }} />
              <Alert severity="info" icon={<WarningIcon />}>
                <Typography variant="body2" fontWeight="medium" gutterBottom>
                  Changes from Version {previousVersion.version}:
                </Typography>
                <Typography variant="body2">
                  • Included: {previousVersion.includedCount} → {includedCount} 
                  ({includedCount - previousVersion.includedCount > 0 ? '+' : ''}{includedCount - previousVersion.includedCount})
                </Typography>
                <Typography variant="body2">
                  • Excluded: {previousVersion.excludedCount} → {excludedCount}
                  ({excludedCount - previousVersion.excludedCount > 0 ? '+' : ''}{excludedCount - previousVersion.excludedCount})
                </Typography>
              </Alert>
            </>
          )}
        </Box>

        <TextField
          fullWidth
          multiline
          rows={4}
          label="Submission Notes"
          placeholder="Provide context for your scoping decisions, rationale for exclusions, or any concerns..."
          value={submissionNotes}
          onChange={(e) => setSubmissionNotes(e.target.value)}
          helperText="These notes will be visible to the Report Owner during review"
        />

        <Alert severity="warning" sx={{ mt: 2 }}>
          Once submitted, these decisions will be sent to the Report Owner for approval. 
          You will be notified if any revisions are requested.
        </Alert>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          color="primary"
          startIcon={<SendIcon />}
          disabled={isSubmitting}
        >
          Submit for Approval
        </Button>
      </DialogActions>
    </Dialog>
  );
};