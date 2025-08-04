export interface TestExecution {
  id: number;
  test_case_id: string;
  sample_id: string;
  sample_identifier: string;
  primary_key_attributes?: any;
  attribute_id: number;
  attribute_name: string;
  data_type?: string;
  
  // Execution results
  execution_status?: string;
  execution_id?: number;
  extracted_value?: string;
  expected_value?: string;
  comparison_result?: string;
  test_result?: string;
  
  // LLM analysis
  llm_confidence_score?: number;
  llm_analysis_rationale?: string;
  analysis_results?: Record<string, any>;
  confidence_score?: number;
  
  // Timestamps
  executed_at?: string;
  submitted_at?: string;
  
  // Other
  special_instructions?: string;
  evidence_id?: number;
  status?: string;
}

export interface TestExecutionResult {
  execution_id: number;
  test_case_id: string;
  status: string;
  extracted_value?: string;
  comparison_result?: string;
  confidence_score?: number;
  analysis_rationale?: string;
  analysis_results?: Record<string, any>;
  executed_at: string;
}

export interface TestExecutionResponse {
  success: boolean;
  execution?: TestExecutionResult;
  error?: string;
}