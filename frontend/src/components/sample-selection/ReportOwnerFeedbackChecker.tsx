import React, { useEffect } from 'react';
import apiClient from '../../api/api';

interface ReportOwnerFeedbackCheckerProps {
  cycleId: number;
  reportId: number;
  versionId?: string;
  onFeedbackStatusChange: (hasFeedback: boolean) => void;
}

const ReportOwnerFeedbackChecker: React.FC<ReportOwnerFeedbackCheckerProps> = ({
  cycleId,
  reportId,
  versionId,
  onFeedbackStatusChange
}) => {
  useEffect(() => {
    const checkFeedback = async () => {
      try {
        const response = await apiClient.get(
          `/sample-selection/cycles/${cycleId}/reports/${reportId}/feedback`
        );
        
        const feedbackData = response.data.feedback || [];
        // Only consider feedback valid if it has samples_feedback
        const validFeedback = feedbackData.filter((f: any) => f.samples_feedback && f.samples_feedback.length > 0);
        onFeedbackStatusChange(validFeedback.length > 0);
      } catch (error) {
        console.error('Error checking Report Owner feedback:', error);
        onFeedbackStatusChange(false);
      }
    };

    checkFeedback();
  }, [cycleId, reportId, versionId, onFeedbackStatusChange]);

  // This component doesn't render anything
  return null;
};

export default ReportOwnerFeedbackChecker;