// Mock data for workflow pages when backend returns errors

export const mockSampleSelectionStatus = {
  cycle_id: 9,
  report_id: 156,
  phase_status: 'In Progress' as const,
  total_sample_sets: 3,
  approved_sample_sets: 1,
  pending_approval_sets: 1,
  rejected_sample_sets: 1,
  total_samples: 150,
  sample_quality_score: 85,
  can_proceed_to_testing: false,
  completion_requirements: [
    'All sample sets must be approved',
    'Minimum 100 samples required',
    'Data provider confirmation needed'
  ]
};

export const mockDataProviderStatus = {
  cycle_id: 9,
  report_id: 156,
  phase_status: 'In Progress' as const,
  total_attributes: 25,
  identified_data_owners: 20,
  unassigned_attributes: 5,
  pending_confirmations: 3,
  confirmed_assignments: 17,
  can_proceed: false,
  completion_requirements: [
    'All attributes must have assigned data owners',
    'All assignments must be confirmed'
  ]
};

export const mockRequestInfo = {
  cycle_id: 9,
  report_id: 156,
  phase_status: 'In Progress' as const,
  total_requests: 15,
  completed_submissions: 10,
  pending_submissions: 5,
  overdue_submissions: 2,
  total_documents: 35,
  validation_status: 'Partially Complete',
  can_proceed: false
};

export const mockTestExecutionStatus = {
  cycle_id: 9,
  report_id: 156,
  phase_status: 'In Progress' as const,
  total_tests: 150,
  completed_tests: 120,
  passed_tests: 110,
  failed_tests: 10,
  pending_tests: 30,
  test_coverage: 80,
  can_proceed: false,
  completion_requirements: [
    'All tests must be completed',
    'Failed tests must be reviewed',
    'Test evidence must be uploaded'
  ]
};

export const mockObservations = [
  {
    observation_id: 1,
    phase_id: 'mock-phase-1',
    cycle_id: 9,
    report_id: 156,
    observation_title: 'Data Quality Issue - Customer Address',
    observation_description: 'Customer addresses are not standardized across systems',
    observation_type: 'Data Quality',
    severity: 'HIGH',
    status: 'Open',
    detection_method: 'Automated Testing',
    detection_confidence: 0.85,
    impact_description: 'May affect regulatory reporting accuracy',
    regulatory_risk_level: 'High',
    detected_by: 3,
    detected_at: new Date().toISOString(),
    assigned_to: null,
    assigned_at: null
  },
  {
    observation_id: 2,
    phase_id: 'mock-phase-2',
    cycle_id: 9,
    report_id: 156,
    observation_title: 'Missing Required Field',
    observation_description: 'Loan origination date is missing for 5% of records',
    observation_type: 'Completeness',
    severity: 'MEDIUM',
    status: 'In Review',
    detection_method: 'Manual Review',
    detection_confidence: 1.0,
    impact_description: 'Incomplete data for regulatory submission',
    regulatory_risk_level: 'Medium',
    detected_by: 3,
    detected_at: new Date(Date.now() - 86400000).toISOString(),
    assigned_to: 5,
    assigned_at: new Date(Date.now() - 43200000).toISOString()
  }
];

export const mockSampleSets = [
  {
    set_id: 'set-1',
    set_name: 'Q1 2024 Customer Samples',
    creation_method: 'LLM_GENERATED' as const,
    total_samples: 50,
    status: 'APPROVED' as const,
    created_at: new Date(Date.now() - 172800000).toISOString(),
    created_by: 3,
    approval_status: 'APPROVED' as const,
    approved_by: 2,
    approved_at: new Date(Date.now() - 86400000).toISOString()
  },
  {
    set_id: 'set-2',
    set_name: 'Q1 2024 Transaction Samples',
    creation_method: 'MANUAL_UPLOAD' as const,
    total_samples: 75,
    status: 'PENDING_APPROVAL' as const,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    created_by: 3,
    approval_status: 'PENDING' as const,
    approved_by: null,
    approved_at: null
  },
  {
    set_id: 'set-3',
    set_name: 'Q1 2024 Account Samples',
    creation_method: 'LLM_GENERATED' as const,
    total_samples: 25,
    status: 'REJECTED' as const,
    created_at: new Date(Date.now() - 259200000).toISOString(),
    created_by: 3,
    approval_status: 'REJECTED' as const,
    approved_by: 2,
    approved_at: new Date(Date.now() - 172800000).toISOString(),
    rejection_reason: 'Sample size too small for statistical significance'
  }
];

export const mockTestCases = [
  {
    test_id: 1,
    attribute_name: 'Customer ID',
    test_type: 'Completeness',
    status: 'PASSED',
    expected_value: 'Not Null',
    actual_value: 'CUS-12345',
    test_date: new Date(Date.now() - 3600000).toISOString()
  },
  {
    test_id: 2,
    attribute_name: 'Account Balance',
    test_type: 'Accuracy',
    status: 'FAILED',
    expected_value: '1000.00',
    actual_value: '999.99',
    test_date: new Date(Date.now() - 7200000).toISOString()
  },
  {
    test_id: 3,
    attribute_name: 'Transaction Date',
    test_type: 'Format',
    status: 'PENDING',
    expected_value: 'YYYY-MM-DD',
    actual_value: null,
    test_date: null
  }
];