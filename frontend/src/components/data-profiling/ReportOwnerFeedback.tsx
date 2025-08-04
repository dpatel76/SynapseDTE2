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
  Tooltip,
  CircularProgress,
  Divider,
  Button
} from '@mui/material';
import {
  CheckCircle as ApprovedIcon,
  Cancel as RejectedIcon,
  Help as RequestChangesIcon,
  Info as InfoIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import { dataProfilingApi } from '../../api/dataProfiling';

interface ReportOwnerFeedbackProps {
  cycleId: number;
  reportId: number;
  versionId?: string;
  currentUserRole: string;
  onFeedbackLoaded?: (hasFeedback: boolean) => void;
  onMakeChanges?: () => void;
}

// Extend the ProfilingRule interface from API to ensure we have attribute_name
interface RuleWithFeedback {
  rule_id: string | number;
  rule_name: string;
  attribute_name?: string; // Make optional in case it's missing
  report_owner_decision?: string;
  report_owner_notes?: string;
  report_owner_decided_at?: string;
  report_owner_decided_by?: number;
  tester_decision?: string;
  status: string;
  line_item_number?: string;
  is_primary_key?: boolean;
  is_cde?: boolean;
  has_issues?: boolean;
  version_number?: number; // Track which version this feedback came from
  [key: string]: any; // Allow additional properties from API
}

export const ReportOwnerFeedback: React.FC<ReportOwnerFeedbackProps> = ({
  cycleId,
  reportId,
  versionId,
  currentUserRole,
  onFeedbackLoaded,
  onMakeChanges
}) => {
  const [rulesWithFeedback, setRulesWithFeedback] = useState<RuleWithFeedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasFeedback, setHasFeedback] = useState(false);
  const [feedbackVersionNumber, setFeedbackVersionNumber] = useState<number | null>(null);

  useEffect(() => {
    loadRulesWithFeedback();
  }, [cycleId, reportId, versionId]);

  const loadRulesWithFeedback = async () => {
    try {
      setLoading(true);
      
      console.log('Loading rules to determine which version was reviewed by Report Owner...');
      
      // First get all versions to analyze which one was reviewed
      const versionsResponse = await dataProfilingApi.getVersions(cycleId, reportId);
      const versions = versionsResponse || [];
      
      if (versions.length === 0) {
        setRulesWithFeedback([]);
        setHasFeedback(false);
        return;
      }
      
      // Load rules from all versions to find feedback patterns
      let allRulesWithFeedback: RuleWithFeedback[] = [];
      const versionRulesMap: Record<number, any[]> = {};
      
      for (const version of versions) {
        try {
          const versionRules = await dataProfilingApi.getRules(
            cycleId, 
            reportId, 
            undefined, // status
            version.version_id,
            undefined, // testerDecision
            undefined  // reportOwnerDecision
          );
          
          // Store rules by version
          versionRulesMap[version.version_number] = versionRules;
          
          // Collect rules with Report Owner feedback
          const versionRulesWithFeedback = versionRules
            .filter((rule: any) => 
              rule.report_owner_decision !== null && rule.report_owner_decision !== undefined
            )
            .map((rule: any) => ({
              ...rule,
              rule_id: String(rule.rule_id),
              attribute_name: rule.attribute_name || 'Unknown Attribute',
              version_number: version.version_number,
              version_id: version.version_id
            }));
          
          if (versionRulesWithFeedback.length > 0) {
            allRulesWithFeedback = allRulesWithFeedback.concat(versionRulesWithFeedback);
          }
        } catch (error) {
          console.warn(`Could not load rules for version ${version.version_id}:`, error);
          continue;
        }
      }
      
      if (allRulesWithFeedback.length === 0) {
        setRulesWithFeedback([]);
        setHasFeedback(false);
        if (onFeedbackLoaded) {
          onFeedbackLoaded(false);
        }
        return;
      }
      
      // Determine which version was actually reviewed by analyzing feedback patterns
      let reviewedVersion: number | null = null;
      const versionFeedbackCounts: Record<number, number> = {};
      const versionEarliestTime: Record<number, Date> = {};
      
      // Count feedback per version and find earliest timestamp per version
      allRulesWithFeedback.forEach((rule: any) => {
        const version = rule.version_number;
        versionFeedbackCounts[version] = (versionFeedbackCounts[version] || 0) + 1;
        
        if (rule.report_owner_decided_at) {
          const reviewTime = new Date(rule.report_owner_decided_at);
          if (!versionEarliestTime[version] || reviewTime < versionEarliestTime[version]) {
            versionEarliestTime[version] = reviewTime;
          }
        }
      });
      
      console.log('Version feedback analysis:', versionFeedbackCounts);
      
      // Find the LATEST version that has report owner feedback
      // This ensures we show the most recent feedback
      let latestVersionWithFeedback: number | null = null;
      Object.entries(versionFeedbackCounts).forEach(([versionStr, count]) => {
        const versionNum = parseInt(versionStr);
        if (count > 0) {
          if (latestVersionWithFeedback === null || versionNum > latestVersionWithFeedback) {
            latestVersionWithFeedback = versionNum;
          }
        }
      });
      
      reviewedVersion = latestVersionWithFeedback;
      
      console.log(`Determined Report Owner reviewed version: ${reviewedVersion}`);
      
      // Get only the rules from the reviewed version
      let rulesWithROFeedback: RuleWithFeedback[] = [];
      if (reviewedVersion !== null && versionRulesMap[reviewedVersion]) {
        // Filter to only show rules with Report Owner feedback from the reviewed version
        rulesWithROFeedback = versionRulesMap[reviewedVersion]
          .filter((rule: any) => 
            rule.report_owner_decision !== null && rule.report_owner_decision !== undefined
          )
          .map((rule: any) => ({
            ...rule,
            rule_id: String(rule.rule_id),
            attribute_name: rule.attribute_name || 'Unknown Attribute'
          }));
      }
      
      setRulesWithFeedback(rulesWithROFeedback);
      const feedbackExists = rulesWithROFeedback.length > 0;
      setHasFeedback(feedbackExists);
      setFeedbackVersionNumber(reviewedVersion);
      
      // Notify parent component
      if (onFeedbackLoaded) {
        onFeedbackLoaded(feedbackExists);
      }
    } catch (error) {
      console.error('Error loading rules with feedback:', error);
      setRulesWithFeedback([]);
      setHasFeedback(false);
      if (onFeedbackLoaded) {
        onFeedbackLoaded(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const getDecisionIcon = (decision?: string) => {
    switch (decision?.toLowerCase()) {
      case 'approved':
        return <ApprovedIcon color="success" fontSize="small" />;
      case 'rejected':
        return <RejectedIcon color="error" fontSize="small" />;
      case 'request_changes':
        return <RequestChangesIcon color="warning" fontSize="small" />;
      default:
        return null;
    }
  };

  const getDecisionColor = (decision?: string): "success" | "error" | "warning" | "default" => {
    switch (decision?.toLowerCase()) {
      case 'approved':
        return 'success';
      case 'rejected':
        return 'error';
      case 'request_changes':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatDecision = (decision?: string) => {
    if (!decision) return '';
    return decision.charAt(0).toUpperCase() + decision.slice(1).toLowerCase();
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!hasFeedback) {
    return null;
  }

  const approvedCount = rulesWithFeedback.filter(r => r.report_owner_decision?.toLowerCase() === 'approved').length;
  const rejectedCount = rulesWithFeedback.filter(r => r.report_owner_decision?.toLowerCase() === 'rejected').length;
  const requestChangesCount = rulesWithFeedback.filter(r => r.report_owner_decision?.toLowerCase() === 'request_changes').length;

  const handleMakeChanges = async () => {
    try {
      const response = await dataProfilingApi.resubmitAfterFeedback(cycleId, reportId);
      if (response.success) {
        alert('New version created successfully! You can now make changes based on the report owner feedback.');
        if (onMakeChanges) {
          onMakeChanges();
        }
      }
    } catch (error) {
      console.error('Error creating new version:', error);
      alert('Failed to create new version. Please try again.');
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
          {/* Version indicator and Make Changes button */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {feedbackVersionNumber && (
                <Chip 
                  icon={<InfoIcon />}
                  label={`Showing latest feedback from v${feedbackVersionNumber}`} 
                  size="small" 
                  color="info" 
                />
              )}
            </Box>
            {currentUserRole === 'Tester' && rejectedCount > 0 && (
              <Button
                variant="contained"
                color="primary"
                startIcon={<EditIcon />}
                onClick={handleMakeChanges}
                size="small"
              >
                Make Changes
              </Button>
            )}
          </Box>
          
          {/* Summary Stats */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <Chip 
              icon={<ApprovedIcon />}
              label={`${approvedCount} Approved`} 
              color="success" 
              variant="filled"
              size="small"
            />
            <Chip 
              icon={<RejectedIcon />}
              label={`${rejectedCount} Rejected`} 
              color="error" 
              variant="filled"
              size="small"
            />
            {requestChangesCount > 0 && (
              <Chip 
                icon={<RequestChangesIcon />}
                label={`${requestChangesCount} Changes Requested`} 
                color="warning" 
                variant="filled"
                size="small"
              />
            )}
          </Box>

          {currentUserRole === 'Tester' && rejectedCount > 0 && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              The Report Owner has rejected {rejectedCount} rule{rejectedCount > 1 ? 's' : ''}. 
              Please review the feedback below and update the rules accordingly.
            </Alert>
          )}

          <Divider sx={{ mb: 2 }} />

          {/* Feedback Table */}
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Attribute / Rule</TableCell>
                  <TableCell align="center">Report Owner Decision</TableCell>
                  <TableCell>Feedback Notes</TableCell>
                  <TableCell align="center">Current Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rulesWithFeedback.map((rule) => (
                  <TableRow key={rule.rule_id}>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {rule.attribute_name || 'Unknown Attribute'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {rule.rule_name}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                          {rule.is_primary_key && (
                            <Chip label="PK" size="small" sx={{ height: 16, fontSize: '0.7rem' }} />
                          )}
                          {rule.is_cde && (
                            <Chip label="CDE" size="small" color="warning" sx={{ height: 16, fontSize: '0.7rem' }} />
                          )}
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                        {getDecisionIcon(rule.report_owner_decision)}
                        <Chip 
                          label={formatDecision(rule.report_owner_decision)}
                          color={getDecisionColor(rule.report_owner_decision)}
                          size="small"
                        />
                      </Box>
                    </TableCell>
                    <TableCell>
                      {rule.report_owner_notes ? (
                        <Tooltip title={rule.report_owner_notes} placement="top-start">
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              maxWidth: 300, 
                              overflow: 'hidden', 
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap' 
                            }}
                          >
                            {rule.report_owner_notes}
                          </Typography>
                        </Tooltip>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No feedback provided
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Chip 
                        label={rule.status}
                        size="small"
                        color={rule.status === 'approved' ? 'success' : rule.status === 'rejected' ? 'error' : 'default'}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Decision timestamp */}
          {rulesWithFeedback[0]?.report_owner_decided_at && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
              Feedback provided on {new Date(rulesWithFeedback[0].report_owner_decided_at).toLocaleString()}
            </Typography>
          )}
    </Box>
  );
};