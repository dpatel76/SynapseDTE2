/**
 * Temporal Workflow Steps Configuration
 * Maps UI steps to Temporal activities for each phase
 * Excludes start/complete activities from progress calculations
 */

export interface WorkflowStep {
  label: string;
  description: string;
  temporalActivity: string;
  isWorkActivity: boolean; // true for work activities, false for start/complete
}

export interface PhaseSteps {
  phaseName: string;
  steps: WorkflowStep[];
}

// Phase 1: Planning
export const planningSteps: WorkflowStep[] = [
  {
    label: 'Start Planning Phase',
    description: 'Initialize planning phase',
    temporalActivity: 'start_planning_phase_activity',
    isWorkActivity: false
  },
  {
    label: 'Upload Documents',
    description: 'Upload regulatory spec, CDE list, and historical issues',
    temporalActivity: 'upload_planning_documents_activity',
    isWorkActivity: true
  },
  {
    label: 'Import/Create Attributes',
    description: 'Import attributes from data dictionary or create manually',
    temporalActivity: 'import_create_attributes_activity',
    isWorkActivity: true
  },
  {
    label: 'Review Planning Checklist',
    description: 'Verify all planning requirements are met',
    temporalActivity: 'review_planning_checklist_activity',
    isWorkActivity: true
  },
  {
    label: 'Complete Planning Phase',
    description: 'Finalize planning and advance to scoping',
    temporalActivity: 'complete_planning_phase_activity',
    isWorkActivity: false
  }
];

// Phase 2: Scoping
export const scopingSteps: WorkflowStep[] = [
  {
    label: 'Start Scoping Phase',
    description: 'Initialize scoping phase and load attributes',
    temporalActivity: 'start_scoping_phase_activity',
    isWorkActivity: false
  },
  {
    label: 'Generate LLM Recommendations',
    description: 'AI analyzes attributes and provides testing recommendations',
    temporalActivity: 'generate_llm_recommendations_activity',
    isWorkActivity: true
  },
  {
    label: 'Tester Review & Decisions',
    description: 'Review AI recommendations and make scoping decisions',
    temporalActivity: 'tester_review_attributes_activity',
    isWorkActivity: true
  },
  {
    label: 'Report Owner Approval',
    description: 'Report Owner reviews and approves scoping decisions',
    temporalActivity: 'report_owner_approval_activity',
    isWorkActivity: true
  },
  {
    label: 'Complete Scoping Phase',
    description: 'Finalize scoping and proceed to next phase',
    temporalActivity: 'complete_scoping_phase_activity',
    isWorkActivity: false
  }
];

// Phase 3: Sample Selection
export const sampleSelectionSteps: WorkflowStep[] = [
  {
    label: 'Start Sample Selection',
    description: 'Initialize sample selection phase',
    temporalActivity: 'start_sample_selection_phase_activity',
    isWorkActivity: false
  },
  {
    label: 'Define Selection Criteria',
    description: 'Define criteria for sample selection',
    temporalActivity: 'define_selection_criteria_activity',
    isWorkActivity: true
  },
  {
    label: 'Generate/Upload Samples',
    description: 'Generate samples using LLM or upload manually',
    temporalActivity: 'generate_sample_sets_activity',
    isWorkActivity: true
  },
  {
    label: 'Review & Approve Samples',
    description: 'Review and approve sample sets',
    temporalActivity: 'review_approve_samples_activity',
    isWorkActivity: true
  },
  {
    label: 'Complete Sample Selection',
    description: 'Finalize sample selection',
    temporalActivity: 'complete_sample_selection_phase_activity',
    isWorkActivity: false
  }
];

// Phase 4: Data Provider Identification
export const dataProviderSteps: WorkflowStep[] = [
  {
    label: 'Start Data Provider ID',
    description: 'Initialize data provider identification',
    temporalActivity: 'start_data_provider_phase_activity',
    isWorkActivity: false
  },
  {
    label: 'Auto-Assign Data Providers',
    description: 'Automatically assign data providers based on LOB',
    temporalActivity: 'auto_assign_data_providers_activity',
    isWorkActivity: true
  },
  {
    label: 'Review Assignments',
    description: 'Review and adjust data provider assignments',
    temporalActivity: 'review_data_provider_assignments_activity',
    isWorkActivity: true
  },
  {
    label: 'Send Notifications',
    description: 'Send notifications to assigned data providers',
    temporalActivity: 'send_data_provider_notifications_activity',
    isWorkActivity: true
  },
  {
    label: 'Complete Data Provider ID',
    description: 'Finalize data provider assignments',
    temporalActivity: 'complete_data_provider_phase_activity',
    isWorkActivity: false
  }
];

// Phase 5: Request for Information
export const requestInfoSteps: WorkflowStep[] = [
  {
    label: 'Start Request Info',
    description: 'Initialize request for information phase',
    temporalActivity: 'start_request_info_phase_activity',
    isWorkActivity: false
  },
  {
    label: 'Generate Test Cases',
    description: 'Generate test cases from attributes and samples',
    temporalActivity: 'generate_test_cases_activity',
    isWorkActivity: true
  },
  {
    label: 'Create Information Requests',
    description: 'Create RFI packages for data providers',
    temporalActivity: 'create_information_requests_activity',
    isWorkActivity: true
  },
  {
    label: 'Send RFI Emails',
    description: 'Send RFI emails to data providers',
    temporalActivity: 'send_rfi_emails_activity',
    isWorkActivity: true
  },
  {
    label: 'Track Responses',
    description: 'Monitor and track RFI responses',
    temporalActivity: 'track_rfi_responses_activity',
    isWorkActivity: true
  },
  {
    label: 'Complete Request Info',
    description: 'Finalize RFI phase',
    temporalActivity: 'complete_request_info_phase_activity',
    isWorkActivity: false
  }
];

// Phase 6: Test Execution
export const testExecutionSteps: WorkflowStep[] = [
  {
    label: 'Start Test Execution',
    description: 'Initialize test execution phase',
    temporalActivity: 'start_test_execution_phase_activity',
    isWorkActivity: false
  },
  {
    label: 'Create Test Records',
    description: 'Create test execution records',
    temporalActivity: 'create_test_execution_records_activity',
    isWorkActivity: true
  },
  {
    label: 'Execute Document Tests',
    description: 'Execute document-based tests',
    temporalActivity: 'execute_document_tests_activity',
    isWorkActivity: true
  },
  {
    label: 'Execute Database Tests',
    description: 'Execute database tests',
    temporalActivity: 'execute_database_tests_activity',
    isWorkActivity: true
  },
  {
    label: 'Record Test Results',
    description: 'Record and consolidate test results',
    temporalActivity: 'record_test_results_activity',
    isWorkActivity: true
  },
  {
    label: 'Generate Test Summary',
    description: 'Generate test execution summary',
    temporalActivity: 'generate_test_summary_activity',
    isWorkActivity: true
  },
  {
    label: 'Complete Test Execution',
    description: 'Finalize test execution phase',
    temporalActivity: 'complete_test_execution_phase_activity',
    isWorkActivity: false
  }
];

// Phase 7: Observation Management
export const observationSteps: WorkflowStep[] = [
  {
    label: 'Start Observations',
    description: 'Initialize observation phase',
    temporalActivity: 'start_observation_phase_activity',
    isWorkActivity: false
  },
  {
    label: 'Create Observations',
    description: 'Create observations from test failures',
    temporalActivity: 'create_observations_activity',
    isWorkActivity: true
  },
  {
    label: 'Auto-Group Observations',
    description: 'Group similar observations using AI',
    temporalActivity: 'auto_group_observations_activity',
    isWorkActivity: true
  },
  {
    label: 'Review & Approve',
    description: 'Review and approve observations',
    temporalActivity: 'review_approve_observations_activity',
    isWorkActivity: true
  },
  {
    label: 'Generate Impact Assessment',
    description: 'Generate impact assessment report',
    temporalActivity: 'generate_impact_assessment_activity',
    isWorkActivity: true
  },
  {
    label: 'Complete Observations',
    description: 'Finalize observation phase',
    temporalActivity: 'complete_observation_phase_activity',
    isWorkActivity: false
  }
];

// Phase 8: Test Report
export const testReportSteps: WorkflowStep[] = [
  {
    label: 'Start Test Report',
    description: 'Initialize test report phase',
    temporalActivity: 'start_test_report_phase_activity',
    isWorkActivity: false
  },
  {
    label: 'Generate Report Sections',
    description: 'Generate standard report sections',
    temporalActivity: 'generate_report_sections_activity',
    isWorkActivity: true
  },
  {
    label: 'Generate Executive Summary',
    description: 'Generate executive summary using AI',
    temporalActivity: 'generate_executive_summary_activity',
    isWorkActivity: true
  },
  {
    label: 'Review & Edit Report',
    description: 'Review and edit report content',
    temporalActivity: 'review_edit_report_activity',
    isWorkActivity: true
  },
  {
    label: 'Finalize Report',
    description: 'Generate final PDF report',
    temporalActivity: 'finalize_report_activity',
    isWorkActivity: true
  },
  {
    label: 'Complete Test Report',
    description: 'Complete test report and cycle',
    temporalActivity: 'complete_test_report_phase_activity',
    isWorkActivity: false
  }
];

// All phases configuration
export const allPhases: PhaseSteps[] = [
  { phaseName: 'Planning', steps: planningSteps },
  { phaseName: 'Scoping', steps: scopingSteps },
  { phaseName: 'Sample Selection', steps: sampleSelectionSteps },
  { phaseName: 'Data Provider ID', steps: dataProviderSteps },
  { phaseName: 'Request Info', steps: requestInfoSteps },
  { phaseName: 'Test Execution', steps: testExecutionSteps },
  { phaseName: 'Observations', steps: observationSteps },
  { phaseName: 'Test Report', steps: testReportSteps }
];

// Progress calculation utilities
export function calculatePhaseProgress(
  phaseName: string,
  completedSteps: string[]
): number {
  const phase = allPhases.find(p => p.phaseName === phaseName);
  if (!phase) return 0;

  const workSteps = phase.steps.filter(s => s.isWorkActivity);
  const completedWorkSteps = workSteps.filter(s => 
    completedSteps.includes(s.temporalActivity)
  );

  return workSteps.length > 0 
    ? (completedWorkSteps.length / workSteps.length) * 100 
    : 0;
}

export function calculateWorkflowProgress(
  completedSteps: string[]
): number {
  let totalWorkSteps = 0;
  let completedWorkSteps = 0;

  allPhases.forEach(phase => {
    const workSteps = phase.steps.filter(s => s.isWorkActivity);
    totalWorkSteps += workSteps.length;
    
    workSteps.forEach(step => {
      if (completedSteps.includes(step.temporalActivity)) {
        completedWorkSteps++;
      }
    });
  });

  return totalWorkSteps > 0 
    ? (completedWorkSteps / totalWorkSteps) * 100 
    : 0;
}

export function getPhaseWorkSteps(phaseName: string): WorkflowStep[] {
  const phase = allPhases.find(p => p.phaseName === phaseName);
  return phase ? phase.steps.filter(s => s.isWorkActivity) : [];
}

export function getTotalWorkSteps(): number {
  return allPhases.reduce((total, phase) => 
    total + phase.steps.filter(s => s.isWorkActivity).length, 0
  );
}