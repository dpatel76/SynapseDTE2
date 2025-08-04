/**
 * RFI Version Types
 * 
 * Type definitions for the RFI versioning system
 */

// Enums
export enum VersionStatus {
  DRAFT = 'draft',
  PENDING_APPROVAL = 'pending_approval',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  SUPERSEDED = 'superseded',
}

export enum EvidenceStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  REQUEST_CHANGES = 'request_changes',
}

export enum EvidenceType {
  DOCUMENT = 'document',
  DATA_SOURCE = 'data_source',
}

export enum Decision {
  APPROVED = 'approved',
  REJECTED = 'rejected',
  REQUEST_CHANGES = 'request_changes',
}

// Version interfaces
export interface RFIVersionListItem {
  version_id: string;
  phase_id: number;
  version_number: number;
  version_status: VersionStatus;
  is_current: boolean;
  can_be_edited: boolean;
  
  // Summary
  total_test_cases: number;
  submitted_count: number;
  approved_count: number;
  completion_percentage: number;
  
  // Timestamps
  created_at: string;
  submitted_at?: string;
  approved_at?: string;
}

export interface RFIVersion extends RFIVersionListItem {
  parent_version_id?: string;
  
  // Detailed statistics
  rejected_count: number;
  pending_count: number;
  document_evidence_count: number;
  data_source_evidence_count: number;
  
  // Configuration
  submission_deadline?: string;
  reminder_schedule?: any;
  instructions?: string;
  
  // Approval workflow
  submitted_by_id?: number;
  submitted_by_name?: string;
  approved_by_id?: number;
  approved_by_name?: string;
  rejection_reason?: string;
  
  // Report owner review metadata
  report_owner_review_requested_at?: string;
  report_owner_review_completed_at?: string;
  report_owner_feedback_summary?: {
    total_reviewed: number;
    approved: number;
    rejected: number;
    changes_requested: number;
    completed_at: string;
  };
  
  // Computed properties
  is_latest: boolean;
  approval_percentage: number;
  has_report_owner_feedback: boolean;
  
  // Evidence items
  evidence_items: RFIEvidence[];
  
  // Audit
  updated_at: string;
  created_by_id?: number;
  created_by_name?: string;
  updated_by_id?: number;
  updated_by_name?: string;
}

export interface RFIEvidence {
  evidence_id: string;
  version_id: string;
  phase_id: number;
  test_case_id: number;
  sample_id: string;
  attribute_id: number;
  attribute_name: string;
  
  // Evidence type and status
  evidence_type: EvidenceType;
  evidence_status: EvidenceStatus;
  
  // Submission info
  data_owner_id: number;
  data_owner_name?: string;
  submitted_at?: string;
  submission_notes?: string;
  
  // Document specific fields
  original_filename?: string;
  stored_filename?: string;
  file_path?: string;
  file_size_bytes?: number;
  file_hash?: string;
  mime_type?: string;
  
  // Data source specific fields
  data_source_id?: number;
  query_text?: string;
  query_parameters?: any;
  query_result_sample?: any;
  row_count?: number;
  
  // Decisions
  tester_decision?: Decision;
  tester_notes?: string;
  tester_decided_by?: number;
  tester_decided_by_name?: string;
  tester_decided_at?: string;
  
  report_owner_decision?: Decision;
  report_owner_notes?: string;
  report_owner_decided_by?: number;
  report_owner_decided_by_name?: string;
  report_owner_decided_at?: string;
  
  // Resubmission tracking
  requires_resubmission: boolean;
  resubmission_deadline?: string;
  resubmission_count: number;
  parent_evidence_id?: string;
  
  // Validation
  validation_status?: string;
  validation_notes?: string;
  validated_by?: number;
  validated_by_name?: string;
  validated_at?: string;
  
  // Computed properties
  is_approved: boolean;
  is_rejected: boolean;
  needs_resubmission: boolean;
  final_status?: string;
  
  // Audit
  created_at: string;
  updated_at: string;
  created_by_id?: number;
  created_by_name?: string;
  updated_by_id?: number;
  updated_by_name?: string;
}

// Request/Response interfaces
export interface RFIVersionCreate {
  carry_forward_all: boolean;
  carry_forward_approved_only?: boolean;
  submission_deadline?: string;
  reminder_schedule?: any;
  instructions?: string;
}

export interface RFIEvidenceUpdate {
  submission_notes?: string;
  tester_decision?: Decision;
  tester_notes?: string;
  report_owner_decision?: Decision;
  report_owner_notes?: string;
  validation_status?: string;
  validation_notes?: string;
}

export interface BulkEvidenceDecision {
  evidence_ids: string[];
  decision: Decision;
  notes?: string;
}

export interface SendToReportOwnerRequest {
  message?: string;
  due_date?: string;
}

export interface ResubmitRequest {
  carry_forward_approved: boolean;
  reset_rejected: boolean;
}

// Submission tracking interfaces
export interface TestCaseSubmissionStatus {
  test_case_id: number;
  test_case_number: string;
  test_case_name: string;
  sample_id: string;
  attribute_name: string;
  data_owner_id: number;
  data_owner_name: string;
  
  // Submission status
  has_evidence: boolean;
  evidence_type?: EvidenceType;
  submitted_at?: string;
  evidence_status?: EvidenceStatus;
  
  // Decisions
  tester_decision?: Decision;
  report_owner_decision?: Decision;
  final_status?: string;
  
  // Deadline tracking
  submission_deadline?: string;
  is_overdue: boolean;
  days_until_deadline?: number;
}

export interface DataOwnerSubmissionSummary {
  data_owner_id: number;
  data_owner_name: string;
  data_owner_email: string;
  
  // Assignment counts
  total_assigned: number;
  submitted_count: number;
  pending_count: number;
  approved_count: number;
  rejected_count: number;
  
  // Progress
  submission_percentage: number;
  approval_percentage: number;
  
  // Deadline tracking
  earliest_deadline?: string;
  overdue_count: number;
  
  // Test cases
  test_cases: TestCaseSubmissionStatus[];
}

// Query validation interfaces
export interface QueryValidationRequest {
  test_case_id: number;
  data_source_id: number;
  query_text: string;
  query_parameters?: any;
}

export interface QueryValidationResponse {
  validation_id: string;
  validation_status: string;
  execution_time_ms?: number;
  row_count?: number;
  column_names?: string[];
  sample_rows?: any[];
  error_message?: string;
  has_primary_keys?: boolean;
  has_target_attribute?: boolean;
  missing_columns?: string[];
  validation_warnings?: string[];
}