import { useMemo } from 'react';
import {
  planningSteps,
  scopingSteps,
  sampleSelectionSteps,
  dataProviderSteps,
  requestInfoSteps,
  testExecutionSteps,
  observationSteps,
  testReportSteps,
  WorkflowStep,
  calculatePhaseProgress
} from '../utils/temporalWorkflowSteps';

export interface PhaseStep {
  label: string;
  description: string;
  icon?: React.ReactNode;
  status: 'completed' | 'active' | 'pending';
  showButton?: boolean;
  buttonText?: string;
  buttonAction?: () => void;
  temporalActivity: string;
  isWorkActivity: boolean;
}

interface UsePhaseStepsOptions {
  phaseName: string;
  phaseStatus?: any;
  completedActivities?: string[];
  onStepAction?: (step: WorkflowStep) => void;
}

export function usePhaseSteps({
  phaseName,
  phaseStatus,
  completedActivities = [],
  onStepAction
}: UsePhaseStepsOptions) {
  const steps = useMemo(() => {
    let baseSteps: WorkflowStep[] = [];
    
    switch (phaseName) {
      case 'Planning':
        baseSteps = planningSteps;
        break;
      case 'Scoping':
        baseSteps = scopingSteps;
        break;
      case 'Sample Selection':
        baseSteps = sampleSelectionSteps;
        break;
      case 'Data Provider ID':
        baseSteps = dataProviderSteps;
        break;
      case 'Request Info':
        baseSteps = requestInfoSteps;
        break;
      case 'Test Execution':
      case 'Testing':
        baseSteps = testExecutionSteps;
        break;
      case 'Observations':
        baseSteps = observationSteps;
        break;
      case 'Test Report':
      case 'Preparing Test Report':
        baseSteps = testReportSteps;
        break;
      default:
        return [];
    }

    // Map to UI-friendly format with status
    return baseSteps.map((step, index) => {
      const isCompleted = completedActivities.includes(step.temporalActivity);
      const previousCompleted = index === 0 || 
        completedActivities.includes(baseSteps[index - 1].temporalActivity);
      
      let status: 'completed' | 'active' | 'pending' = 'pending';
      if (isCompleted) {
        status = 'completed';
      } else if (previousCompleted && !isCompleted) {
        status = 'active';
      }

      return {
        ...step,
        status,
        showButton: status === 'active' && step.isWorkActivity,
        buttonText: `Execute ${step.label}`,
        buttonAction: () => onStepAction?.(step)
      } as PhaseStep;
    });
  }, [phaseName, completedActivities, onStepAction]);

  const progress = useMemo(() => {
    return calculatePhaseProgress(phaseName, completedActivities);
  }, [phaseName, completedActivities]);

  const workStepsOnly = useMemo(() => {
    return steps.filter(s => s.isWorkActivity);
  }, [steps]);

  const currentStep = useMemo(() => {
    return steps.find(s => s.status === 'active');
  }, [steps]);

  const completedWorkSteps = useMemo(() => {
    return workStepsOnly.filter(s => s.status === 'completed').length;
  }, [workStepsOnly]);

  const totalWorkSteps = workStepsOnly.length;

  return {
    steps,
    workStepsOnly,
    currentStep,
    progress,
    completedWorkSteps,
    totalWorkSteps,
    isPhaseComplete: steps[steps.length - 1]?.status === 'completed'
  };
}