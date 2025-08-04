import React, { useEffect } from 'react';
import apiClient from '../../api/client';

interface ReportOwnerScopingFeedbackCheckerProps {
  cycleId: number;
  reportId: number;
  versionId?: string;
  onFeedbackStatusChange: (hasFeedback: boolean) => void;
}

/**
 * Hidden component that checks for Report Owner feedback existence
 * and notifies parent component to show/hide the feedback tab
 */
const ReportOwnerScopingFeedbackChecker: React.FC<ReportOwnerScopingFeedbackCheckerProps> = ({
  cycleId,
  reportId,
  versionId,
  onFeedbackStatusChange
}) => {
  useEffect(() => {
    checkForFeedback();
  }, [cycleId, reportId, versionId]);

  const checkForFeedback = async () => {
    try {
      // Instead of checking just the current version, check all versions for the latest feedback
      // Get all versions for this phase
      const versionsResponse = await apiClient.get(`/scoping/cycles/${cycleId}/reports/${reportId}/versions`);
      const versions = versionsResponse.data?.versions || [];
      
      if (versions.length === 0) {
        onFeedbackStatusChange(false);
        return;
      }
      
      // Check versions from newest to oldest for any report owner feedback
      let hasFeedback = false;
      
      for (const version of versions) {
        // First check if the version itself has been rejected or approved by report owner
        // A rejected version means report owner has provided feedback
        if (version.version_status === 'rejected' || version.rejection_reason) {
          hasFeedback = true;
          break;
        }
        
        // Also check if version has been approved (which means report owner approved it)
        if (version.version_status === 'approved' && version.approved_at) {
          hasFeedback = true;
          break;
        }
        
        // Additionally, check individual attribute decisions
        try {
          // Load attributes for this version
          const response = await apiClient.get(`/scoping/versions/${version.version_id}/attributes`);
          const attributes = response.data || [];
          
          // Check if any attributes have Report Owner feedback
          const attributesWithFeedback = attributes.filter((attr: any) => 
            attr.report_owner_decision !== null && attr.report_owner_decision !== undefined
          );
          
          if (attributesWithFeedback.length > 0) {
            hasFeedback = true;
            break; // Found feedback, no need to check older versions
          }
        } catch (error) {
          // Skip this version if error loading attributes
          console.warn(`Could not load attributes for version ${version.version_id}:`, error);
          continue;
        }
      }
      
      onFeedbackStatusChange(hasFeedback);
      
    } catch (error) {
      console.error('Error checking for Report Owner feedback:', error);
      onFeedbackStatusChange(false);
    }
  };

  // This component doesn't render anything
  return null;
};

export default ReportOwnerScopingFeedbackChecker;