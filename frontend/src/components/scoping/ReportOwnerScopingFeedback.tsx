import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  Typography,
  Box,
  Tooltip,
  IconButton,
  Stack,
  Card,
  CardContent,
  Button
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../api/client';

interface AttributeWithFeedback {
  attribute_id: number;
  attribute_name: string;
  report_owner_decision?: 'approved' | 'rejected' | 'needs_revision';
  report_owner_notes?: string;
  report_owner_decided_at?: string;
  report_owner_decided_by_id?: number;
  tester_decision?: 'accept' | 'decline' | 'override';
  final_scoping?: boolean;
  is_primary_key?: boolean;
  is_cde?: boolean;
  status: string;
  line_item_number?: string;
}

interface ReportOwnerScopingFeedbackProps {
  cycleId: number;
  reportId: number;
  versionId?: string;
  onFeedbackStatusChange?: (hasFeedback: boolean) => void;
}

const ReportOwnerScopingFeedback: React.FC<ReportOwnerScopingFeedbackProps> = ({
  cycleId,
  reportId,
  versionId,
  onFeedbackStatusChange
}) => {
  const { user } = useAuth();
  const [attributes, setAttributes] = useState<AttributeWithFeedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedbackVersionNumber, setFeedbackVersionNumber] = useState<number | null>(null);
  const [versionStatus, setVersionStatus] = useState<string | null>(null);

  // Calculate feedback statistics (attribute-level)
  const approvedCount = attributes.filter(attr => attr.report_owner_decision === 'approved').length;
  const rejectedCount = attributes.filter(attr => attr.report_owner_decision === 'rejected').length;
  const changesRequestedCount = attributes.filter(attr => attr.report_owner_decision === 'needs_revision').length;
  const totalWithFeedback = attributes.length;

  useEffect(() => {
    loadAttributesWithFeedback();
  }, [cycleId, reportId, versionId]);

  useEffect(() => {
    // Notify parent component about feedback status
    const hasFeedback = totalWithFeedback > 0;
    if (onFeedbackStatusChange) {
      onFeedbackStatusChange(hasFeedback);
    }
  }, [totalWithFeedback, onFeedbackStatusChange]);

  const loadAttributesWithFeedback = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get all versions to analyze which version was actually reviewed
      const versionsResponse = await apiClient.get(`/scoping/cycles/${cycleId}/reports/${reportId}/versions`);
      const versions = versionsResponse.data?.versions || [];
      
      if (versions.length === 0) {
        setError('No scoping versions found');
        return;
      }
      
      console.log('Loading attributes to determine which version was reviewed by Report Owner...');
      
      // Load all attributes across versions to analyze feedback patterns
      let allAttributesWithFeedback: any[] = [];
      const versionAttributesMap: Record<number, any[]> = {};
      
      // Load attributes from all versions to find feedback
      for (const version of versions) {
        try {
          const response = await apiClient.get(`/scoping/versions/${version.version_id}/attributes`);
          const attributesData = response.data || [];
          
          // Store attributes by version
          versionAttributesMap[version.version_number] = attributesData;
          
          // Collect attributes with Report Owner feedback
          const versionAttributesWithFeedback = attributesData.filter((attr: any) => 
            attr.report_owner_decision !== null && 
            attr.report_owner_decision !== undefined &&
            attr.final_scoping === true  // Only show feedback for attributes that were scoped in
          );
          
          if (versionAttributesWithFeedback.length > 0) {
            allAttributesWithFeedback = allAttributesWithFeedback.concat(
              versionAttributesWithFeedback.map((attr: any) => ({
                ...attr,
                version_number: version.version_number,
                version_id: version.version_id
              }))
            );
          }
        } catch (error) {
          console.warn(`Could not load attributes for version ${version.version_id}:`, error);
          continue;
        }
      }
      
      if (allAttributesWithFeedback.length === 0) {
        setAttributes([]);
        setFeedbackVersionNumber(null);
        return;
      }
      
      // Find the latest version with feedback (version-level rejection/approval or attribute-level feedback)
      let reviewedVersion: number | null = null;
      let latestVersionWithFeedback: any = null;
      
      // Sort versions by version_number descending to check latest first
      const sortedVersions = [...versions].sort((a, b) => b.version_number - a.version_number);
      
      // First check for version-level feedback (rejected/approved status)
      for (const version of sortedVersions) {
        
        // Check if version was rejected or approved (version-level feedback)
        if (version.version_status === 'rejected' || version.version_status === 'approved') {
          reviewedVersion = version.version_number;
          latestVersionWithFeedback = version;
          console.log(`Found version ${version.version_number} with status: ${version.version_status}`);
          break;
        }
        
        // Check if version has attribute-level feedback
        const versionAttrs = versionAttributesMap[version.version_number] || [];
        const hasAttributeFeedback = versionAttrs.some((attr: any) => 
          attr.report_owner_decision !== null && attr.report_owner_decision !== undefined
        );
        
        if (hasAttributeFeedback) {
          reviewedVersion = version.version_number;
          latestVersionWithFeedback = version;
          console.log(`Found version ${version.version_number} with attribute-level feedback`);
          break;
        }
      }
      
      console.log(`Determined Report Owner reviewed version: ${reviewedVersion}`);
      
      // Get only the attributes from the reviewed version
      let attributesWithFeedback: any[] = [];
      if (reviewedVersion !== null && versionAttributesMap[reviewedVersion]) {
        // If version was approved/rejected at version level, show all scoped attributes
        if (latestVersionWithFeedback && (latestVersionWithFeedback.version_status === 'approved' || 
            latestVersionWithFeedback.version_status === 'rejected')) {
          // Show all attributes that were scoped in (final_scoping = true)
          attributesWithFeedback = versionAttributesMap[reviewedVersion].filter((attr: any) => 
            attr.final_scoping === true
          );
        } else {
          // Otherwise, filter to only show attributes with individual Report Owner feedback
          attributesWithFeedback = versionAttributesMap[reviewedVersion].filter((attr: any) => 
            attr.report_owner_decision !== null && 
            attr.report_owner_decision !== undefined &&
            attr.final_scoping === true
          );
        }
      }
      
      setAttributes(attributesWithFeedback);
      setFeedbackVersionNumber(reviewedVersion);
      setVersionStatus(latestVersionWithFeedback?.version_status || null);
      
    } catch (err: any) {
      console.error('Error loading attributes with feedback:', err);
      setError('Failed to load Report Owner feedback');
      setAttributes([]);
    } finally {
      setLoading(false);
    }
  };

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'approved':
        return <CheckCircleIcon sx={{ color: 'success.main', fontSize: 20 }} />;
      case 'rejected':
        return <CancelIcon sx={{ color: 'error.main', fontSize: 20 }} />;
      case 'needs_revision':
        return <WarningIcon sx={{ color: 'warning.main', fontSize: 20 }} />;
      default:
        return <InfoIcon sx={{ color: 'info.main', fontSize: 20 }} />;
    }
  };

  const getDecisionChip = (decision: string) => {
    switch (decision) {
      case 'approved':
        return <Chip label="Approved" color="success" size="small" />;
      case 'rejected':
        return <Chip label="Rejected" color="error" size="small" />;
      case 'needs_revision':
        return <Chip label="Changes Requested" color="warning" size="small" />;
      default:
        return <Chip label="Pending" color="default" size="small" />;
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const truncateText = (text: string, maxLength: number = 50) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Typography>Loading Report Owner feedback...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (totalWithFeedback === 0) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        No Report Owner feedback available yet.
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      {/* Summary Statistics */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Report Owner Feedback Summary
            {feedbackVersionNumber && (
              <>
                <Chip 
                  label={`Version ${feedbackVersionNumber}`} 
                  size="small" 
                  color="info" 
                  sx={{ ml: 2 }}
                />
                {versionStatus && (
                  <Chip 
                    label={versionStatus === 'approved' ? 'Approved' : versionStatus === 'rejected' ? 'Rejected' : versionStatus} 
                    size="small" 
                    color={versionStatus === 'approved' ? 'success' : versionStatus === 'rejected' ? 'error' : 'default'}
                    sx={{ ml: 1 }}
                  />
                )}
              </>
            )}
          </Typography>
          <Stack direction="row" spacing={2}>
            <Chip
              icon={<CheckCircleIcon />}
              label={`${approvedCount} Approved`}
              color="success"
            />
            <Chip
              icon={<CancelIcon />}
              label={`${rejectedCount} Rejected`}
              color="error"
            />
            {changesRequestedCount > 0 && (
              <Chip
                icon={<WarningIcon />}
                label={`${changesRequestedCount} Changes Requested`}
                color="warning"
              />
            )}
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {totalWithFeedback} of {attributes.length} attributes have Report Owner feedback
          </Typography>
        </CardContent>
      </Card>

      {/* Make Changes Button for Testers when version is rejected */}
      {user?.role === 'Tester' && versionStatus === 'rejected' && (
        <Card sx={{ mb: 2, bgcolor: 'warning.50', border: 1, borderColor: 'warning.main' }}>
          <CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h6" gutterBottom color="warning.main">
              Action Required
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              The Report Owner has provided feedback. Click below to create a new version where you can update your decisions.
            </Typography>
            <Button
              variant="contained"
              color="warning"
              onClick={async () => {
                try {
                  // Call resubmission API to create new version
                  const response = await apiClient.post(
                    `/scoping/cycles/${cycleId}/reports/${reportId}/resubmit-after-feedback`
                  );
                  
                  // Show success message
                  console.log('SUCCESS:', `New version created for resubmission (v${response.data.version_number}). You can now update your decisions based on feedback.`);
                  alert(`New version created for resubmission (v${response.data.version_number}). You can now update your decisions based on feedback.`);
                  
                  // Refresh the page to load the new version
                  window.location.reload();
                  
                } catch (error: any) {
                  console.error('Error creating resubmission version:', error);
                  console.log('ERROR:', `Failed to create resubmission version: ${error.response?.data?.detail || error.message}`);
                  alert(`Failed to create resubmission version: ${error.response?.data?.detail || error.message}`);
                }
              }}
              sx={{ minWidth: 160 }}
            >
              Make Changes
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Alert for Testers when version is rejected */}
      {user?.role === 'Tester' && versionStatus === 'rejected' && rejectedCount > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          The Report Owner has rejected {rejectedCount} attribute{rejectedCount > 1 ? 's' : ''}. 
          Please review the feedback below and update the scoping decisions accordingly.
        </Alert>
      )}

      {/* Attributes Feedback Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Attribute</TableCell>
              <TableCell>Line Item</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Tester Decision</TableCell>
              <TableCell>Report Owner Decision</TableCell>
              <TableCell>Feedback Notes</TableCell>
              <TableCell>Date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {attributes.map((attribute) => (
              <TableRow key={attribute.attribute_id}>
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {attribute.attribute_name}
                    </Typography>
                    <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }}>
                      {attribute.is_primary_key && (
                        <Chip label="PK" size="small" color="primary" />
                      )}
                      {attribute.is_cde && (
                        <Chip label="CDE" size="small" color="secondary" />
                      )}
                    </Stack>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {attribute.line_item_number || 'N/A'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {attribute.final_scoping ? 'Scoped In' : 'Scoped Out'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    {attribute.tester_decision === 'accept' && (
                      <CheckCircleIcon sx={{ color: 'success.main', fontSize: 16 }} />
                    )}
                    {attribute.tester_decision === 'decline' && (
                      <CancelIcon sx={{ color: 'error.main', fontSize: 16 }} />
                    )}
                    {attribute.tester_decision === 'override' && (
                      <WarningIcon sx={{ color: 'warning.main', fontSize: 16 }} />
                    )}
                    <Typography variant="body2" textTransform="capitalize">
                      {attribute.tester_decision || 'Pending'}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    {attribute.report_owner_decision && 
                      getDecisionIcon(attribute.report_owner_decision)
                    }
                    {attribute.report_owner_decision && 
                      getDecisionChip(attribute.report_owner_decision)
                    }
                  </Box>
                </TableCell>
                <TableCell>
                  {attribute.report_owner_notes ? (
                    <Tooltip title={attribute.report_owner_notes}>
                      <Typography variant="body2" sx={{ cursor: 'pointer' }}>
                        {truncateText(attribute.report_owner_notes)}
                      </Typography>
                    </Tooltip>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No feedback provided
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {formatDate(attribute.report_owner_decided_at)}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default ReportOwnerScopingFeedback;