import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  Button
} from '@mui/material';
import {
  CheckCircle as ApprovedIcon,
  Cancel as RejectedIcon,
  Warning as RevisionIcon,
  Info as InfoIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import apiClient from '../../api/api';

interface ReportOwnerFeedbackProps {
  cycleId: number;
  reportId: number;
  versionId?: string;
  currentUserRole: string;
  onFeedbackLoaded?: (hasFeedback: boolean) => void;
  onMakeChanges?: () => void;
}

interface SampleWithFeedback {
  sample_id: string;
  report_owner_decision?: string;
  report_owner_feedback?: string;
  report_owner_reviewed_at?: string;
  report_owner_reviewed_by?: string;
  tester_decision?: string;
  sample_category?: string;
  attribute_focus?: string;
  lob_assignment?: string;
}

interface SubmissionFeedback {
  submission_id: string;
  version_number: number;
  decision: string;
  feedback: string;
  reviewed_at: string;
  reviewed_by: string;
  samples_feedback: SampleWithFeedback[];
}

const ReportOwnerFeedback: React.FC<ReportOwnerFeedbackProps> = ({
  cycleId,
  reportId,
  versionId,
  currentUserRole,
  onFeedbackLoaded,
  onMakeChanges
}) => {
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<SubmissionFeedback[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFeedback();
  }, [cycleId, reportId, versionId]);

  // Check if there's any revision required feedback
  const latestFeedback = feedback[0]; // Assuming feedback is sorted by date, newest first

  const loadFeedback = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get all versions
      console.log('Loading versions to find Report Owner feedback...');
      const versionsResponse = await apiClient.get(`/sample-selection/cycles/${cycleId}/reports/${reportId}/versions`);
      const versions = versionsResponse.data || [];
      
      if (versions.length === 0) {
        setError('No versions found');
        return;
      }
      
      // Sort versions by version_number descending to check latest first
      const sortedVersions = [...versions].sort((a: any, b: any) => b.version_number - a.version_number);
      
      // Find the latest version that has been reviewed by Report Owner
      let reviewedVersion: number | null = null;
      let feedbackVersion = null;
      
      for (const version of sortedVersions) {
        // Skip looking at draft versions for feedback - we want the version that was actually reviewed
        if (version.version_status === 'draft') {
          continue;
        }
        
        // Check if version was reviewed (approved/rejected/pending_approval)
        if (version.version_status === 'approved' || version.version_status === 'rejected' || version.version_status === 'pending_approval') {
          reviewedVersion = version.version_number;
          feedbackVersion = version;
          console.log(`Found version ${version.version_number} with status: ${version.version_status}`);
          break;
        }
        
        // Also check if version has samples with RO feedback
        try {
          const samplesResponse = await apiClient.get(
            `/sample-selection/cycles/${cycleId}/reports/${reportId}/samples?version=${version.version_number}&include_feedback=true`
          );
          const versionSamples = samplesResponse.data.samples || [];
          const hasROFeedback = versionSamples.some((s: any) => s.report_owner_decision);
          
          if (hasROFeedback) {
            reviewedVersion = version.version_number;
            feedbackVersion = version;
            console.log(`Found version ${version.version_number} with sample-level feedback`);
            break;
          }
        } catch (error) {
          console.warn(`Could not load samples for version ${version.version_number}:`, error);
        }
      }
      
      if (!reviewedVersion || !feedbackVersion) {
        setFeedback([]);
        if (onFeedbackLoaded) {
          onFeedbackLoaded(false);
        }
        return;
      }
      
      console.log(`Report Owner reviewed version: ${reviewedVersion}, status: ${feedbackVersion.version_status}`);
      
      // Now load only the samples from the reviewed version
      let feedbackSamples = [];
      
      if (reviewedVersion !== null) {
        try {
          // Load samples for that specific version
          const samplesResponse = await apiClient.get(
            `/sample-selection/cycles/${cycleId}/reports/${reportId}/samples?version=${reviewedVersion}&include_feedback=true`
          );
          const versionSamples = samplesResponse.data.samples || [];
          // Filter to only samples with RO feedback
          feedbackSamples = versionSamples.filter((s: any) => s.report_owner_decision);
          console.log(`Loaded ${feedbackSamples.length} samples with RO feedback from version ${reviewedVersion}`);
        } catch (error) {
          console.warn(`Error loading samples from version ${reviewedVersion}:`, error);
          // Fallback to empty
          feedbackSamples = [];
        }
      } else {
        // If we still couldn't determine the version, show error
        console.log('Could not determine which version was reviewed');
        setError('Could not determine which version was reviewed by Report Owner');
        setFeedback([]);
        if (onFeedbackLoaded) {
          onFeedbackLoaded(false);
        }
        return;
      }
      
      const samples = feedbackSamples;
      
      // Convert samples with report_owner_decision to submission feedback format
      const samplesWithFeedback = samples.filter((sample: any) => sample.report_owner_decision);
      
      if (samplesWithFeedback.length > 0) {
        // Group all sample feedback into a single submission
        const mostRecentSample = samplesWithFeedback[0]; // Use first sample for metadata
        
        // Use Report Owner name (avoiding permissions issue with user API)
        let reviewedByName = 'Report Owner';
        if (mostRecentSample.report_owner_reviewed_by) {
          reviewedByName = `Report Owner (ID: ${mostRecentSample.report_owner_reviewed_by})`;
        }
        
        // Use the determined reviewed version, or fallback to version from sample/feedback
        const displayVersion = reviewedVersion || feedbackVersion?.version_number || mostRecentSample.version_number || mostRecentSample.version_reviewed || 1;
        
        // Simple: Use version metadata to determine decision
        let overallDecision = 'pending';
        let overallFeedback = 'No overall feedback provided';
        
        if (feedbackVersion) {
          const versionStatus = feedbackVersion.version_status;
          console.log('Feedback version status:', versionStatus);
          
          // Check if version has explicit report_owner_decision metadata first
          if (feedbackVersion.report_owner_decision) {
            overallDecision = feedbackVersion.report_owner_decision;
            overallFeedback = feedbackVersion.report_owner_feedback || 'Report Owner provided feedback';
          } else {
            // Otherwise map version status to decision
            if (versionStatus === 'approved') {
              overallDecision = 'approved';
              overallFeedback = feedbackVersion.approval_notes || 'Version approved by Report Owner';
            } else if (versionStatus === 'rejected') {
              overallDecision = 'rejected';
              overallFeedback = feedbackVersion.submission_notes || 'Version rejected by Report Owner';
            }
          }
        }
        
        console.log('Final overall decision:', overallDecision);
        
        const feedbackData = [{
          submission_id: `submission_${cycleId}_${reportId}`,
          version_number: displayVersion,
          decision: overallDecision,
          feedback: overallFeedback,
          reviewed_at: mostRecentSample.report_owner_reviewed_at || new Date().toISOString(),
          reviewed_by: reviewedByName,
          samples_feedback: samplesWithFeedback.map((sample: any) => ({
            sample_id: sample.sample_id,
            report_owner_decision: sample.report_owner_decision,
            report_owner_feedback: sample.report_owner_feedback || '',
            report_owner_reviewed_at: sample.report_owner_reviewed_at,
            report_owner_reviewed_by: sample.report_owner_reviewed_by,
            sample_category: sample.sample_category,
            attribute_focus: sample.attribute_focus,
            lob_assignment: sample.lob_assignment
          }))
        }];
        
        setFeedback(feedbackData);
        
        // Notify parent component about feedback availability
        if (onFeedbackLoaded) {
          onFeedbackLoaded(true);
        }
      } else {
        setFeedback([]);
        
        // Notify parent component about feedback availability
        if (onFeedbackLoaded) {
          onFeedbackLoaded(false);
        }
      }
    } catch (err) {
      console.error('Error loading Report Owner feedback:', err);
      setError('Failed to load Report Owner feedback');
      if (onFeedbackLoaded) {
        onFeedbackLoaded(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const getDecisionIcon = (decision?: string) => {
    switch (decision) {
      case 'approved':
        return <ApprovedIcon color="success" fontSize="small" />;
      case 'rejected':
        return <RejectedIcon color="error" fontSize="small" />;
      case 'revision_required':
        return <RevisionIcon color="warning" fontSize="small" />;
      default:
        return undefined;
    }
  };

  const getDecisionChip = (decision?: string) => {
    if (!decision) return null;

    const config = {
      approved: { color: 'success' as const, label: 'Approved' },
      rejected: { color: 'error' as const, label: 'Rejected' },
      revision_required: { color: 'warning' as const, label: 'Revision Required' }
    };

    const decisionConfig = config[decision as keyof typeof config];
    if (!decisionConfig) return null;

    return (
      <Chip
        icon={getDecisionIcon(decision)}
        label={decisionConfig.label}
        color={decisionConfig.color}
        size="small"
      />
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (feedback.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        No Report Owner feedback available yet.
      </Alert>
    );
  }

  // Check if there's any revision required feedback
  const hasRevisionRequired = feedback.some(f => f.decision === 'revision_required');
  const isLatestRevisionRequired = latestFeedback?.decision === 'revision_required';

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Report Owner Feedback
        </Typography>
        {(() => {
          // Show button for Testers when changes are needed
          const shouldShowButton = currentUserRole === 'Tester' && 
                                 feedback.length > 0 && 
                                 onMakeChanges &&
                                 latestFeedback?.decision !== 'approved';
          
          console.log('Make Changes button conditions:', {
            currentUserRole,
            isTester: currentUserRole === 'Tester',
            feedbackLength: feedback.length,
            hasFeedback: feedback.length > 0,
            onMakeChangesProvided: !!onMakeChanges,
            latestFeedbackDecision: latestFeedback?.decision,
            isNotApproved: latestFeedback?.decision !== 'approved',
            shouldShowButton
          });
          
          return shouldShowButton && (
            <Button
              variant="contained"
              color="primary"
              startIcon={<EditIcon />}
              onClick={onMakeChanges}
            >
              Make Changes
            </Button>
          );
        })()}
      </Box>

      {/* Show alert for revision required */}
      {currentUserRole === 'Tester' && isLatestRevisionRequired && (
        <Alert severity="warning" sx={{ mb: 2 }} icon={<RevisionIcon />}>
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
            Report Owner has requested changes
          </Typography>
          <Typography variant="body2">
            The Report Owner has reviewed Version {latestFeedback.version_number} and requested revisions. 
            Click "Make Changes" to create a new version with the requested modifications.
          </Typography>
        </Alert>
      )}
      
      {feedback.map((submission, index) => (
        <Card 
          key={submission.submission_id} 
          sx={{ 
            mb: 3,
            ...(submission.decision === 'revision_required' && {
              borderLeft: '4px solid',
              borderLeftColor: 'warning.main'
            })
          }}
        >
          <CardContent>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid size={{ xs: 12, md: 3 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Version
                </Typography>
                <Typography variant="body1">
                  Version {submission.version_number}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Decision
                </Typography>
                {getDecisionChip(submission.decision)}
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Reviewed By
                </Typography>
                <Typography variant="body2">
                  {submission.reviewed_by}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Reviewed At
                </Typography>
                <Typography variant="body2">
                  {new Date(submission.reviewed_at).toLocaleString()}
                </Typography>
              </Grid>
            </Grid>

            {submission.feedback && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Overall Feedback
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="body2">
                    {submission.feedback}
                  </Typography>
                </Paper>
              </Box>
            )}

            {submission.samples_feedback && submission.samples_feedback.length > 0 && (
              <>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Individual Sample Feedback
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Sample ID</TableCell>
                        <TableCell>Category</TableCell>
                        <TableCell>Attribute</TableCell>
                        <TableCell>LOB</TableCell>
                        <TableCell>Decision</TableCell>
                        <TableCell>Feedback</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {submission.samples_feedback.map((sample) => (
                        <TableRow key={sample.sample_id}>
                          <TableCell>
                            <Typography variant="body2" fontFamily="monospace">
                              {sample.sample_id}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={sample.sample_category || 'Unknown'}
                              size="small"
                              color={
                                sample.sample_category === 'CLEAN' ? 'success' :
                                sample.sample_category === 'ANOMALY' ? 'warning' :
                                sample.sample_category === 'BOUNDARY' ? 'info' : 'default'
                              }
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {sample.attribute_focus || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {sample.lob_assignment || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {getDecisionChip(sample.report_owner_decision)}
                          </TableCell>
                          <TableCell>
                            {sample.report_owner_feedback ? (
                              <Typography variant="body2" sx={{ maxWidth: 300 }}>
                                {sample.report_owner_feedback}
                              </Typography>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                -
                              </Typography>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};

export default ReportOwnerFeedback;