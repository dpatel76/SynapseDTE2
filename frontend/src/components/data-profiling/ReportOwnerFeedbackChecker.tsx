import React, { useEffect } from 'react';
import { dataProfilingApi } from '../../api/dataProfiling';

interface ReportOwnerFeedbackCheckerProps {
  cycleId: number;
  reportId: number;
  versionId?: string;
  onFeedbackCheck: (hasFeedback: boolean) => void;
}

export const ReportOwnerFeedbackChecker: React.FC<ReportOwnerFeedbackCheckerProps> = ({
  cycleId,
  reportId,
  versionId,
  onFeedbackCheck
}) => {
  useEffect(() => {
    checkForFeedback();
  }, [cycleId, reportId, versionId]);

  const checkForFeedback = async () => {
    try {
      console.log('🔍 Checking for report owner feedback:', { cycleId, reportId, versionId });
      
      // First get the latest version if no versionId is provided
      let currentVersionId = versionId;
      if (!currentVersionId) {
        const versions = await dataProfilingApi.getVersions(cycleId, reportId);
        if (versions && versions.length > 0) {
          const currentVersion = versions.find((v: any) => v.is_current) || versions[0];
          currentVersionId = currentVersion.version_id;
          console.log('🎯 Using current version:', currentVersionId);
        }
      }
      
      const rules = await dataProfilingApi.getRules(
        cycleId, 
        reportId, 
        undefined, // status
        currentVersionId,
        undefined, // testerDecision
        undefined  // reportOwnerDecision
      );
      
      console.log('📋 Rules loaded:', rules.length, 'rules');
      
      // Check if any rules have report owner feedback
      const rulesWithFeedback = rules.filter((rule: any) => 
        rule.report_owner_decision !== null && rule.report_owner_decision !== undefined
      );
      
      const hasFeedback = rulesWithFeedback.length > 0;
      console.log('✅ Report owner feedback check:', hasFeedback, 'rules with feedback:', rulesWithFeedback.length);
      
      onFeedbackCheck(hasFeedback);
    } catch (error) {
      console.error('Error checking for report owner feedback:', error);
      onFeedbackCheck(false);
    }
  };

  return null; // This component doesn't render anything
};