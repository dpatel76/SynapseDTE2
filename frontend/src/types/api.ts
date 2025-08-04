// User & Authentication Types
export interface User {
  user_id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  lob_id?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export enum UserRole {
  ADMIN = 'Admin',
  TEST_EXECUTIVE = 'Test Executive',
  REPORT_OWNER = 'Report Owner', 
  REPORT_EXECUTIVE = 'Report Executive',
  TESTER = 'Tester',
  DATA_OWNER = 'Data Owner',
  DATA_EXECUTIVE = 'Data Executive'
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// LOB Types
export interface LOB {
  lob_id: number;
  lob_name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Report Types
export interface Report {
  report_id: number;
  report_name: string;
  regulation?: string;
  lob_id: number;
  report_owner_id: number;
  description?: string;
  frequency?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  lob?: LOB;
  owner?: User;
  lob_name?: string;
  owner_name?: string;
}

// Test Cycle Types
export interface TestCycle {
  cycle_id: number;
  cycle_name: string;
  description?: string;
  start_date: string;
  end_date?: string;
  status: CycleStatus | string;
  created_by: number;
  created_at: string;
  updated_at: string;
  reports?: Report[];
  creator?: User;
}

export enum CycleStatus {
  PLANNING = 'Planning',
  DRAFT = 'Draft',
  ACTIVE = 'Active',
  COMPLETED = 'Completed',
  CANCELLED = 'Cancelled'
}

// Planning Phase Types
export interface PlanningPhase {
  phase_id: string;
  cycle_id: number;
  report_id: number;
  status: PhaseStatus;
  started_by: number;
  started_at: string;
  completed_at?: string;
  completion_notes?: string;
}

export enum PhaseStatus {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress', 
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export interface ReportAttribute {
  attribute_id: number;
  report_id: number;
  attribute_name: string;
  data_type: string;
  description?: string;
  business_rules?: string;
  source_system?: string;
  sample_values?: string;
  created_at: string;
  updated_at: string;
}

// Scoping Phase Types
export interface ScopingPhase {
  phase_id: string;
  cycle_id: number;
  report_id: number;
  planning_phase_id: string;
  status: PhaseStatus;
  started_by: number;
  started_at: string;
  completed_at?: string;
}

export interface AttributeScopingRecommendation {
  recommendation_id: number;
  phase_id: string;
  attribute_id: number;
  recommendation_type: string;
  recommendation_rationale: string;
  confidence_score: number;
  created_at: string;
}

// Data Provider Types
export interface DataProviderPhase {
  phase_id: string;
  cycle_id: number;
  report_id: number;
  scoping_phase_id: string;
  status: PhaseStatus;
  started_by: number;
  started_at: string;
  completed_at?: string;
}

// Sample Selection Types  
export interface SampleSelectionPhase {
  phase_id: string;
  cycle_id: number;
  report_id: number;
  data_provider_phase_id: string;
  status: PhaseStatus;
  started_by: number;
  started_at: string;
  completed_at?: string;
}

export interface SampleSet {
  set_id: string;
  phase_id: string;
  set_name: string;
  generation_method: string;
  total_records: number;
  status: string;
  created_at: string;
}

// Request Info Types
export interface RequestInfoPhase {
  phase_id: string;
  cycle_id: number;
  report_id: number;
  sample_selection_phase_id: string;
  status: PhaseStatus;
  started_by: number;
  started_at: string;
  completed_at?: string;
  deadline?: string;
}

// Test Execution Types
export interface TestExecutionPhase {
  phase_id: string;
  cycle_id: number;
  report_id: number;
  request_info_phase_id: string;
  status: PhaseStatus;
  testing_strategy: string;
  started_by: number;
  started_at: string;
  completed_at?: string;
}

export interface TestExecution {
  execution_id: number;
  phase_id: string;
  test_name: string;
  test_type: string;
  status: string;
  started_at: string;
  completed_at?: string;
}

// Observation Management Types
export interface ObservationManagementPhase {
  phase_id: string;
  cycle_id: number;
  report_id: number;
  test_execution_phase_id: string;
  status: PhaseStatus;
  detection_strategy: string;
  started_by: number;
  started_at: string;
  completed_at?: string;
}

export interface Observation {
  observation_id: number;
  phase_id: string;
  observation_title: string;
  observation_description: string;
  observation_type: string;
  severity: string;
  status: string;
  detected_at: string;
  assigned_to?: number;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Dashboard Types
export interface DashboardStats {
  total_cycles: number;
  active_cycles: number;
  completed_phases: number;
  pending_tasks: number;
  recent_activities: Activity[];
}

export interface Activity {
  id: number;
  type: string;
  description: string;
  user: string;
  timestamp: string;
  phase?: string;
  cycle?: string;
}

export interface AssignedReport {
  cycle_id: number;
  cycle_name: string;
  report_id: number;
  report_name: string;
  lob_name: string;
  status: string;
  current_phase: string;
  overall_progress: number;
  started_at?: string;
  next_action: string;
  due_date?: string;
  issues_count: number;
  phase_status: 'not_started' | 'in_progress' | 'pending_approval' | 'completed';
  activity_state?: 'Not Started' | 'In Progress' | 'Completed' | 'Revision Requested';
  workflow_id?: string;
} 