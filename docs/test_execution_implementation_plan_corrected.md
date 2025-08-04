# Test Execution Phase - Corrected Implementation Plan

## Overview

This document outlines the corrected implementation of the Test Execution phase database architecture, properly integrating with the Request for Information evidence and maintaining all current functionality while simplifying the structure.

## Understanding the Current Data Flow

### Request for Information → Test Execution Integration

The test execution phase receives inputs from the Request for Information phase:

1. **Test Cases**: From `cycle_report_test_cases` table
2. **Source Evidence**: From `cycle_report_request_info_testcase_source_evidence` table
3. **Sample Data**: Expected values from sample records
4. **Tester Approval**: Evidence must be approved before test execution

### Current Test Execution Data Storage

Based on the existing implementation, test execution stores:

- **Sample Value**: Expected value from sample data
- **Source Document Value**: Extracted value from evidence documents
- **Test Result**: Pass/Fail/Inconclusive based on comparison
- **LLM Rationale**: Explanation of extraction and analysis
- **Confidence Scores**: LLM confidence levels
- **Processing Metrics**: Timing, tokens used, etc.

## Corrected Architecture

### Main Table: Test Execution Results (With Evidence Integration)
```sql
CREATE TABLE cycle_report_test_execution_results (
    id SERIAL PRIMARY KEY,
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    test_case_id VARCHAR(255) NOT NULL REFERENCES cycle_report_test_cases(test_case_id),
    
    -- CRITICAL: Link to approved evidence from Request for Information
    evidence_id INTEGER NOT NULL REFERENCES cycle_report_request_info_testcase_source_evidence(id),
    
    -- Execution versioning (multiple executions per test case)
    execution_number INTEGER NOT NULL, -- 1, 2, 3... for each re-execution
    is_latest_execution BOOLEAN DEFAULT FALSE,
    execution_reason VARCHAR(100), -- 'initial', 'retry', 'evidence_updated', 'manual_rerun'
    
    -- Test execution configuration
    test_type VARCHAR(50) NOT NULL, -- 'document_analysis', 'database_test', 'manual_test', 'hybrid'
    analysis_method VARCHAR(50) NOT NULL, -- 'llm_analysis', 'database_query', 'manual_review'
    
    -- CORE TEST DATA (as per current implementation)
    sample_value TEXT, -- Expected value from sample data
    extracted_value TEXT, -- Actual value extracted from evidence
    expected_value TEXT, -- Business rule expected value (may differ from sample)
    
    -- Test results
    test_result VARCHAR(50), -- 'pass', 'fail', 'inconclusive', 'pending_review'
    comparison_result BOOLEAN, -- Direct comparison: extracted_value == expected_value
    variance_details JSONB, -- Details of any variance found
    
    -- LLM Analysis Results (matching current DocumentAnalysis model)
    llm_confidence_score FLOAT, -- 0.0 to 1.0
    llm_analysis_rationale TEXT, -- LLM explanation
    llm_model_used VARCHAR(100), -- e.g., 'gpt-4', 'claude-3'
    llm_tokens_used INTEGER,
    llm_response_raw JSONB, -- Raw LLM response
    llm_processing_time_ms INTEGER,
    
    -- Database Test Results (for database evidence)
    database_query_executed TEXT,
    database_result_count INTEGER,
    database_execution_time_ms INTEGER,
    database_result_sample JSONB, -- Sample of query results
    
    -- Execution status and timing
    execution_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    
    -- Comprehensive analysis results (unified storage)
    analysis_results JSONB NOT NULL,
    /*
    Structure:
    {
        "test_execution": {
            "sample_value": "expected_from_sample",
            "extracted_value": "found_in_evidence",
            "comparison_result": true,
            "variance_percentage": 0.0
        },
        "llm_analysis": {
            "confidence_score": 0.95,
            "rationale": "Clear match found in document section 3.2",
            "model_used": "gpt-4",
            "tokens_used": 1250,
            "processing_time_ms": 3000,
            "extraction_method": "pattern_matching"
        },
        "database_analysis": {
            "query_executed": "SELECT value FROM table WHERE id = ?",
            "result_count": 1,
            "execution_time_ms": 150,
            "connection_validated": true
        },
        "validation_results": {
            "format_valid": true,
            "business_rule_valid": true,
            "data_quality_score": 0.92,
            "completeness_score": 1.0
        },
        "accuracy_metrics": {
            "extraction_accuracy": 0.95,
            "comparison_accuracy": 1.0,
            "overall_confidence": 0.93
        }
    }
    */
    
    -- Evidence context (from Request for Information phase)
    evidence_validation_status VARCHAR(50), -- Status of evidence when test was executed
    evidence_version_number INTEGER, -- Version of evidence used
    
    -- Test execution summary
    execution_summary TEXT, -- Human-readable summary
    processing_notes TEXT, -- Additional processing notes
    
    -- Execution metadata
    executed_by INTEGER NOT NULL REFERENCES users(user_id),
    execution_method VARCHAR(50) NOT NULL, -- 'automatic', 'manual', 'scheduled'
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(test_case_id, execution_number),
    UNIQUE(test_case_id, is_latest_execution) WHERE is_latest_execution = TRUE,
    
    -- Ensure evidence is approved before test execution
    CHECK (evidence_validation_status IN ('valid', 'approved'))
);
```

### Tester Approval Table: Test Execution Reviews
```sql
CREATE TABLE cycle_report_test_execution_reviews (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES cycle_report_test_execution_results(id),
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- Review details
    review_status VARCHAR(50) NOT NULL, -- 'approved', 'rejected', 'requires_revision'
    review_notes TEXT,
    reviewer_comments TEXT,
    recommended_action VARCHAR(100), -- 'approve', 'retest', 'escalate', 'manual_review'
    
    -- Quality assessment (matching current implementation)
    accuracy_score FLOAT, -- 0.0 to 1.0
    completeness_score FLOAT, -- 0.0 to 1.0  
    consistency_score FLOAT, -- 0.0 to 1.0
    overall_score FLOAT, -- Calculated overall score
    
    -- Review criteria
    review_criteria_used JSONB,
    /*
    Structure:
    {
        "criteria_version": "1.0",
        "accuracy_weight": 0.4,
        "completeness_weight": 0.3,
        "consistency_weight": 0.3,
        "minimum_threshold": 0.8,
        "auto_approve_threshold": 0.95
    }
    */
    
    -- Follow-up actions
    requires_retest BOOLEAN DEFAULT FALSE,
    retest_reason TEXT,
    escalation_required BOOLEAN DEFAULT FALSE,
    escalation_reason TEXT,
    
    -- Approval workflow
    reviewed_by INTEGER NOT NULL REFERENCES users(user_id),
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(execution_id, reviewed_by) -- One review per execution per reviewer
);
```

### Audit Trail Table
```sql
CREATE TABLE cycle_report_test_execution_audit (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES cycle_report_test_execution_results(id),
    action VARCHAR(100) NOT NULL, -- 'started', 'completed', 'failed', 'reviewed', 'approved', 'rejected'
    action_details JSONB,
    performed_by INTEGER NOT NULL REFERENCES users(user_id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Context information
    previous_status VARCHAR(50),
    new_status VARCHAR(50),
    change_reason TEXT,
    system_info JSONB -- IP, user agent, etc.
);
```

## Integration with Request for Information Phase

### 1. Evidence Dependency
```sql
-- Test execution can only proceed with approved evidence
-- Evidence must be in 'valid' or 'approved' status
-- Evidence version is captured for audit trail
```

### 2. Data Flow Process
```
1. Request for Information Phase:
   - Test cases created in cycle_report_test_cases
   - Evidence submitted in cycle_report_request_info_testcase_source_evidence
   - Tester approves evidence (status = 'valid')

2. Test Execution Phase:
   - Gets approved evidence as input
   - Extracts sample_value from sample data
   - Extracts extracted_value from evidence documents/queries
   - Compares values and generates test_result
   - Stores LLM rationale and confidence scores
   - Creates execution record with all analysis

3. Tester Review:
   - Tester reviews test execution results
   - Approves/rejects based on quality criteria
   - Test case marked as complete only after approval
   - Approved test cases can proceed to Observation Management
```

### 3. Test Case Completion Requirements
```sql
-- Test case is complete when:
-- 1. Evidence is approved (from Request for Information)
-- 2. Test execution is successful (status = 'completed')
-- 3. Tester has approved the test results (review_status = 'approved')
-- 4. No retests are required

-- Only completed test cases can proceed to Observation Management phase
```

## Business Logic Implementation

### 1. Evidence-Based Test Execution
```python
async def execute_test_case(test_case_id: str, evidence_id: int):
    # 1. Verify evidence is approved
    evidence = get_evidence(evidence_id)
    if evidence.validation_status != 'valid':
        raise ValueError("Evidence must be approved before test execution")
    
    # 2. Get sample data for expected values
    sample_data = get_sample_data(test_case.sample_id)
    sample_value = sample_data.get_attribute_value(test_case.attribute_name)
    
    # 3. Extract value from evidence
    if evidence.evidence_type == 'document':
        extracted_value = llm_service.extract_value_from_document(
            evidence.document_path, 
            test_case.attribute_name
        )
    else:  # data_source
        extracted_value = database_service.execute_query(
            evidence.data_source_id,
            evidence.query_text
        )
    
    # 4. Compare and generate result
    test_result = compare_values(sample_value, extracted_value)
    
    # 5. Store execution record
    execution = create_execution_record(
        test_case_id=test_case_id,
        evidence_id=evidence_id,
        sample_value=sample_value,
        extracted_value=extracted_value,
        test_result=test_result,
        analysis_results=analysis_results
    )
    
    return execution
```

### 2. Tester Approval Process
```python
async def approve_test_execution(execution_id: int, reviewer_id: int):
    # 1. Get execution results
    execution = get_execution(execution_id)
    
    # 2. Calculate quality scores
    scores = calculate_quality_scores(execution)
    
    # 3. Determine approval status
    if scores.overall_score >= 0.8:
        review_status = 'approved'
    else:
        review_status = 'requires_revision'
    
    # 4. Create review record
    review = create_review_record(
        execution_id=execution_id,
        review_status=review_status,
        scores=scores,
        reviewed_by=reviewer_id
    )
    
    # 5. Update test case status if approved
    if review_status == 'approved':
        update_test_case_status(execution.test_case_id, 'completed')
    
    return review
```

### 3. Phase Completion Logic
```python
async def check_phase_completion(phase_id: int):
    # Phase is complete when all test cases are approved
    test_cases = get_test_cases_for_phase(phase_id)
    
    for test_case in test_cases:
        # Check if test case has approved execution
        latest_execution = get_latest_execution(test_case.test_case_id)
        if not latest_execution:
            return False, f"Test case {test_case.test_case_id} not executed"
        
        review = get_latest_review(latest_execution.id)
        if not review or review.review_status != 'approved':
            return False, f"Test case {test_case.test_case_id} not approved"
    
    return True, "All test cases completed and approved"
```

## API Endpoints Design

### Test Execution Management
```
POST /api/v1/test-execution/{cycle_id}/reports/{report_id}/execute
- Start test execution for all approved test cases
- Body: { execution_method?, configuration? }

POST /api/v1/test-execution/test-cases/{test_case_id}/execute
- Execute specific test case with approved evidence
- Body: { evidence_id, execution_reason?, configuration? }

GET /api/v1/test-execution/test-cases/{test_case_id}/results
- Get latest execution results for test case

GET /api/v1/test-execution/test-cases/{test_case_id}/executions
- Get all executions for test case (history)
```

### Tester Review Interface
```
GET /api/v1/test-execution/{cycle_id}/reports/{report_id}/pending-review
- Get executions pending tester review

POST /api/v1/test-execution/executions/{execution_id}/review
- Submit tester review for execution
- Body: { review_status, review_notes, quality_scores?, requires_retest? }

GET /api/v1/test-execution/executions/{execution_id}/review
- Get review details for execution
```

### Phase Management
```
GET /api/v1/test-execution/{cycle_id}/reports/{report_id}/completion-status
- Check if phase can be completed (all test cases approved)

POST /api/v1/test-execution/{cycle_id}/reports/{report_id}/complete
- Mark phase as complete (requires all test cases approved)
```

## Key Benefits

### 1. Proper Evidence Integration
- **Evidence Dependency**: Tests can only run with approved evidence
- **Version Tracking**: Captures which version of evidence was used
- **Audit Trail**: Complete traceability from evidence to test results

### 2. Comprehensive Test Data Storage
- **Sample Values**: Expected values from sample data
- **Extracted Values**: Actual values from evidence
- **LLM Rationale**: Explanation of extraction and analysis
- **Quality Metrics**: Confidence scores and validation results

### 3. Tester Approval Workflow
- **Quality Assessment**: Accuracy, completeness, consistency scoring
- **Approval Gates**: Test cases must be approved to proceed
- **Review Comments**: Detailed feedback for quality improvement

### 4. Execution History
- **Multiple Executions**: Support for retests and re-executions
- **Reason Tracking**: Why tests were re-executed
- **Latest Execution**: Clear current state identification

## Migration from Current Implementation

### Phase 1: Create New Tables
```sql
-- Create simplified execution table
CREATE TABLE cycle_report_test_execution_results (...);

-- Create review table
CREATE TABLE cycle_report_test_execution_reviews (...);

-- Create audit table
CREATE TABLE cycle_report_test_execution_audit (...);
```

### Phase 2: Migrate Existing Data
```sql
-- Migrate from current TestExecution table
INSERT INTO cycle_report_test_execution_results (...)
SELECT ... FROM cycle_report_test_executions te
JOIN cycle_report_test_execution_document_analyses da ON te.id = da.execution_id
...;

-- Migrate reviews
INSERT INTO cycle_report_test_execution_reviews (...)
SELECT ... FROM test_result_reviews trr
...;
```

### Phase 3: Update Application Logic
- Update test execution service to use new tables
- Modify tester approval workflow
- Update phase completion logic

## Conclusion

The corrected implementation maintains all current functionality while simplifying the architecture:

1. **Evidence Integration**: Proper linkage to Request for Information evidence
2. **Test Data Storage**: All key fields (sample value, extracted value, LLM rationale)
3. **Tester Approval**: Complete review workflow with quality scoring
4. **Phase Completion**: Clear requirements for proceeding to Observation Management
5. **Execution History**: Support for multiple executions with reason tracking

This design ensures test execution works seamlessly with the evidence collection process while maintaining the comprehensive data capture and approval workflows required for the system.