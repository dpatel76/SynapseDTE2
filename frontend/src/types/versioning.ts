export interface PhaseVersions {
  [phase: string]: VersionInfo | null;
}

export interface PhaseStatuses {
  [phase: string]: PhaseStatus;
}

export interface PhaseStatus {
  phase: string;
  status: string;
  currentStep?: string;
  completedSteps?: number;
  totalSteps?: number;
  lastUpdated?: string;
}

export interface VersionInfo {
  version_id: string;
  version_number: number;
  created_at: string;
  created_by?: string;
  approved_at?: string;
  approved_by?: string;
  version_status: 'draft' | 'approved' | 'rejected';
  workflow_execution_id: string;
  phase: string;
  metadata?: any;
  parent_version_id?: string;
}

export interface VersionHistory {
  version_id: string;
  version_number: number;
  created_at: string;
  created_by?: string;
  approved_at?: string;
  approved_by?: string;
  version_status: string;
  changes?: any;
}

export interface VersionComparison {
  phase: string;
  oldVersion: VersionInfo;
  newVersion: VersionInfo;
  differences: any[];
}

export type PhaseVersionStatus = 'current' | 'pending' | 'outdated' | 'none';

export type ApprovalStatus = 'draft' | 'approved' | 'rejected' | 'pending';

export interface SampleDecision {
  decision_id: string;
  sample_id: string;
  decision_status: SampleDecisionStatus;
  decision_rationale?: string;
  decided_by?: string;
  decided_at?: string;
  sample_identifier?: string;
  sample_type?: string;
  recommendation_source?: string;
}

export type SampleDecisionStatus = 'pending' | 'approved' | 'rejected' | 'carried_forward' | 'needs_changes';

export interface Sample {
  sample_id: string;
  sample_identifier: string;
  attribute_name: string;
  sample_data?: any;
  data?: any;
  decision_id: string;
  decision_status?: SampleDecisionStatus;
  id?: string;
}

export interface SampleSelectionVersion {
  version_id: string;
  version_number: number;
  samples: Sample[];
  approved_count: number;
  rejected_count: number;
  pending_count: number;
  actual_sample_size?: number;
  parent_version_id?: string;
}

export interface PendingApproval {
  phase: string;
  version_id: string;
  created_at: string;
  created_by?: string;
  awaiting?: string;
}