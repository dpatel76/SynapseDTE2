# Test Execution Phase - Simplified Implementation Plan

## Overview

This document outlines the simplification of the Test Execution phase database architecture, consolidating multiple complex tables into a streamlined system while maintaining test case-level granularity.

## Current Architecture Issues

### Massive Table Redundancy
- **7+ separate tables** with overlapping purposes
- **Duplicate test execution tables** (`cycle_report_test_executions`, `testing_test_executions`, `cycle_report_test_execution_test_executions`)
- **Complex versioning system** that adds unnecessary overhead
- **Inconsistent naming patterns** across tables

### Over-engineered Structure
- Separate tables for document analysis and database tests when they could be unified
- Complex bulk execution tracking with separate table
- Unnecessary versioning system for simple test executions
- Multiple review and approval tables for straightforward workflows

## Business Logic Understanding

### Test Execution Works at Test Case Level
Like the Request for Information phase, test execution operates on **individual test cases**:

1. **Input**: Test cases from `cycle_report_test_cases` with submitted evidence
2. **Process**: Execute each test case individually with different test types:
   - Document analysis using LLM
   - Database query execution  
   - Manual verification
3. **Output**: Test results stored per test case with confidence scores

### Test Types Supported
- **Document Analysis**: LLM extraction and analysis of submitted documents
- **Database Testing**: Query execution against data sources
- **Manual Testing**: User-provided actual values for verification
- **Hybrid Testing**: Combination of multiple test methods

## Proposed Simplified Architecture

### Main Table: Test Execution Results (Multiple Executions per Test Case)
```sql
CREATE TABLE cycle_report_test_execution_results (
    id SERIAL PRIMARY KEY,
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    test_case_id VARCHAR(255) NOT NULL REFERENCES cycle_report_test_cases(test_case_id),
    evidence_id INTEGER REFERENCES cycle_report_request_info_testcase_source_evidence(id),
    
    -- Execution versioning (multiple executions per test case)
    execution_number INTEGER NOT NULL, -- 1, 2, 3... for each re-execution
    is_latest_execution BOOLEAN DEFAULT FALSE, -- Only the most recent execution is TRUE
    execution_reason VARCHAR(100), -- 'initial', 'retry', 'evidence_updated', 'manual_rerun', 'configuration_changed'
    
    -- Test execution configuration
    test_type VARCHAR(50) NOT NULL, -- 'document_analysis', 'database_test', 'manual_test', 'hybrid'
    test_configuration JSONB,
    /*
    Structure based on test_type:
    Document Analysis: {
        "analysis_type": "llm_extraction",
        "extraction_fields": ["field1", "field2"],
        "confidence_threshold": 0.8,
        "llm_model": "gpt-4"
    }
    Database Test: {
        "data_source_id": 123,
        "query": "SELECT * FROM table WHERE id = ?",
        "expected_result_type": "exact_match",
        "validation_rules": {...}
    }
    Manual Test: {
        "expected_value": "ABC123",
        "comparison_type": "exact_match",
        "instructions": "Verify customer ID matches"
    }
    */
    
    -- Execution status and timing
    execution_status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_duration_ms INTEGER,
    
    -- Test results
    test_result VARCHAR(50), -- pass, fail, inconclusive, pending_review
    confidence_score FLOAT,
    actual_value TEXT,
    expected_value TEXT,
    
    -- Analysis results (unified for all test types)
    analysis_results JSONB,
    /*
    Structure:
    {
        "extraction_results": {
            "field1": "extracted_value1",
            "field2": "extracted_value2"
        },
        "confidence_scores": {
            "field1": 0.95,
            "field2": 0.87
        },
        "query_results": {
            "rows_returned": 1,
            "execution_time_ms": 450,
            "result_data": [...]
        },
        "validation_results": {
            "matches_expected": true,
            "variance_percentage": 0.0,
            "issues": []
        },
        "llm_analysis": {
            "model_used": "gpt-4",
            "tokens_used": 1250,
            "processing_time_ms": 3000
        }
    }
    */
    
    -- Evidence and files
    evidence_files JSONB, -- List of file paths and metadata
    output_files JSONB, -- Generated output files (reports, extracts, etc.)
    
    -- Error handling
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    
    -- Review and approval
    review_status VARCHAR(50) DEFAULT 'pending', -- pending, approved, rejected, needs_revision
    review_notes TEXT,
    reviewed_by INTEGER REFERENCES users(user_id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    -- Execution metadata
    executed_by INTEGER NOT NULL REFERENCES users(user_id),
    execution_method VARCHAR(50) NOT NULL, -- 'automatic', 'manual', 'scheduled'
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(test_case_id, execution_number), -- Each execution number is unique per test case
    UNIQUE(test_case_id, is_latest_execution) WHERE is_latest_execution = TRUE -- Only one latest execution per test case
);
```

### Supporting Table: Test Execution Audit Log
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

## Unified Business Logic

### 1. Test Case Processing Flow with Execution History
```sql
-- Flow supporting multiple executions per test case
1. Get test case from cycle_report_test_cases
2. Get evidence from cycle_report_request_info_testcase_source_evidence
3. Determine execution number:
   - Query existing executions for test case: MAX(execution_number) + 1
   - Set execution_reason (initial, retry, evidence_updated, etc.)
4. Create new test execution record with execution_number
5. Execute test based on test_type
6. Store results in unified analysis_results JSONB
7. Update execution status and test result
8. Mark as latest execution (set is_latest_execution = TRUE, others = FALSE)
```

### 2. Test Type Implementations

#### Document Analysis Tests
- **Input**: Document files from evidence submission
- **Process**: LLM extraction and analysis
- **Output**: Extracted values with confidence scores
- **Storage**: Results in `analysis_results.extraction_results`

#### Database Tests
- **Input**: Query configuration and data source
- **Process**: Execute query and validate results
- **Output**: Query results and validation status
- **Storage**: Results in `analysis_results.query_results`

#### Manual Tests
- **Input**: Expected values and comparison rules
- **Process**: User provides actual values
- **Output**: Pass/fail with variance analysis
- **Storage**: Results in `analysis_results.validation_results`

#### Hybrid Tests
- **Input**: Multiple test configurations
- **Process**: Combine multiple test types
- **Output**: Aggregated results with overall confidence
- **Storage**: Combined results in `analysis_results`

### 3. Unified Review Workflow
```sql
-- Single review process for all test types
1. Test execution completes
2. Automatic validation checks
3. Tester reviews results
4. Approve/reject with notes
5. Update review_status
```

## Key Simplifications

### 1. Single Test Execution Table with History
**Before**: 3+ separate execution tables with overlapping data
**After**: Single `cycle_report_test_execution_results` table with execution versioning

### 2. Unified Analysis Results
**Before**: Separate document analysis and database test tables
**After**: Unified `analysis_results` JSONB field supporting all test types

### 3. Simplified Review Process
**Before**: Multiple review tables with complex workflows
**After**: Built-in review fields in main table

### 4. Execution History Management
**Before**: Overwrite previous execution results (losing history)
**After**: Keep complete execution history with versioning

#### Execution History Features:
- **Multiple Executions**: Each test case can have multiple execution records
- **Execution Numbering**: Sequential numbering (1, 2, 3...) for each execution
- **Latest Execution Tracking**: `is_latest_execution` flag marks current result
- **Execution Reasons**: Track why test was re-executed
- **Complete History**: All previous executions preserved for audit/comparison

#### Common Execution Reasons:
- **`initial`**: First execution of test case
- **`retry`**: Retry after failure or inconclusive result
- **`evidence_updated`**: New evidence submitted, re-run test
- **`manual_rerun`**: Tester manually requested re-execution
- **`configuration_changed`**: Test configuration updated

### 5. Consolidated Audit Trail
**Before**: Multiple audit tables per component
**After**: Single audit table for all test execution activities

## Data Migration Strategy

### Phase 1: Create New Tables
```sql
-- Create simplified test execution table
CREATE TABLE cycle_report_test_execution_results (...);

-- Create unified audit table
CREATE TABLE cycle_report_test_execution_audit (...);

-- Create indexes
CREATE INDEX idx_test_execution_test_case ON cycle_report_test_execution_results(test_case_id);
CREATE INDEX idx_test_execution_phase ON cycle_report_test_execution_results(phase_id);
CREATE INDEX idx_test_execution_status ON cycle_report_test_execution_results(execution_status);
```

### Phase 2: Migrate Existing Data
```sql
-- Migrate from main test execution table
INSERT INTO cycle_report_test_execution_results (
    phase_id, cycle_id, report_id, test_case_id, test_type,
    execution_status, test_result, confidence_score,
    analysis_results, started_at, completed_at, executed_by,
    created_by, updated_by
)
SELECT 
    te.phase_id, te.cycle_id, te.report_id, te.test_case_id,
    'document_analysis', -- Default test type
    te.execution_status, te.test_result, te.confidence_score,
    jsonb_build_object(
        'extraction_results', te.analysis_results,
        'confidence_scores', te.confidence_details,
        'llm_analysis', te.llm_metadata
    ),
    te.started_at, te.completed_at, te.executed_by,
    te.created_by, te.updated_by
FROM cycle_report_test_executions te;

-- Migrate document analysis results
UPDATE cycle_report_test_execution_results 
SET analysis_results = analysis_results || jsonb_build_object(
    'document_analysis', da.analysis_results,
    'extraction_confidence', da.confidence_score
)
FROM cycle_report_test_execution_document_analyses da
WHERE test_case_id = da.test_case_id;

-- Migrate database test results
UPDATE cycle_report_test_execution_results 
SET analysis_results = analysis_results || jsonb_build_object(
    'database_test', dt.test_results,
    'query_execution', dt.execution_details
)
FROM cycle_report_test_execution_database_tests dt
WHERE test_case_id = dt.test_case_id;
```

### Phase 3: Update Application Code
1. **Update Models**: Create simplified SQLAlchemy models
2. **Update Services**: Implement unified test execution logic
3. **Update APIs**: Create consolidated endpoints
4. **Update UI**: Simplify test execution interface

### Phase 4: Clean Up
```sql
-- Drop redundant tables after successful migration
DROP TABLE cycle_report_test_execution_document_analyses;
DROP TABLE cycle_report_test_execution_database_tests;
DROP TABLE test_result_reviews;
DROP TABLE test_comparisons;
DROP TABLE bulk_test_executions;
-- Keep main table for backup during transition
-- DROP TABLE cycle_report_test_executions;
```

## API Endpoints Design

### Test Execution Management
```
POST /api/v1/test-execution/{cycle_id}/reports/{report_id}/execute
- Start test execution for all test cases
- Body: { test_type?, configuration?, execution_method? }

GET /api/v1/test-execution/{cycle_id}/reports/{report_id}/results
- Get all test execution results for a report

POST /api/v1/test-execution/test-cases/{test_case_id}/execute
- Execute specific test case
- Body: { test_type, configuration, execution_method }

GET /api/v1/test-execution/test-cases/{test_case_id}/results
- Get test execution results for specific test case
```

### Test Result Review
```
POST /api/v1/test-execution/results/{execution_id}/review
- Review test execution results
- Body: { review_status, review_notes, requires_revision? }

GET /api/v1/test-execution/{cycle_id}/reports/{report_id}/pending-review
- Get all results pending review

POST /api/v1/test-execution/results/bulk-review
- Bulk review multiple test results
- Body: { execution_ids: [], review_status, review_notes }
```

### Execution History Management
```
GET /api/v1/test-execution/test-cases/{test_case_id}/executions
- Get all executions for a test case (history)

GET /api/v1/test-execution/test-cases/{test_case_id}/executions/latest
- Get latest execution for a test case

GET /api/v1/test-execution/executions/{execution_id}
- Get specific execution details

POST /api/v1/test-execution/test-cases/{test_case_id}/re-execute
- Re-execute a test case (creates new execution record)
- Body: { execution_reason, test_configuration?, notes? }
```

### Progress and Status
```
GET /api/v1/test-execution/{cycle_id}/reports/{report_id}/progress
- Get test execution progress and statistics

GET /api/v1/test-execution/{cycle_id}/reports/{report_id}/status
- Get phase status and completion requirements
```

## Benefits of Simplified Architecture

### 1. Reduced Complexity
- **From 7+ tables to 2 tables** (90% reduction)
- **Unified data model** for all test types
- **Simplified queries** and maintenance

### 2. Improved Performance
- **Fewer joins** required for test execution queries
- **JSONB indexing** for fast analysis result searches
- **Reduced storage** through elimination of redundant data

### 3. Enhanced Maintainability
- **Single code path** for all test types
- **Consistent API** across test execution functionality
- **Easier debugging** with unified audit trail

### 4. Better Scalability
- **Horizontal scaling** support through simplified schema
- **Efficient bulk operations** without separate tracking tables
- **Faster test execution** through reduced database overhead

## Migration Timeline

### Week 1: Database Schema Changes
- Create new simplified tables
- Write and test migration scripts
- Set up parallel data writing

### Week 2: Backend Implementation
- Update SQLAlchemy models
- Implement unified test execution service
- Create new API endpoints

### Week 3: Frontend Updates
- Update test execution UI
- Modify review interface
- Test bulk operations

### Week 4: Testing and Deployment
- Integration testing
- Performance testing
- Production deployment with rollback capability

## Conclusion

The proposed simplification reduces the Test Execution phase from a complex 7+ table structure to a clean 2-table system while maintaining all existing functionality. This provides:

1. **90% reduction** in table complexity
2. **Unified test execution** approach for all test types
3. **Improved performance** through simplified queries
4. **Better maintainability** with consistent patterns
5. **Enhanced scalability** for large-scale test execution

The new architecture maintains the test case-level granularity while significantly reducing complexity and improving system performance.