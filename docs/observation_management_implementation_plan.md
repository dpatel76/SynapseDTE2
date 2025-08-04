# Observation Management Phase - Simplified Implementation Plan

## Overview

This document outlines the simplification of the Observation Management phase database architecture, consolidating dual systems into a unified, streamlined approach while maintaining all business functionality.

## Current Architecture Issues

### Dual Architecture Problem
- **Two separate observation systems** running in parallel:
  - Original: `ObservationRecord` with complex impact/approval/resolution tables
  - Enhanced: `ObservationGroup` with simplified grouped observations
- **Inconsistent data models** and business logic between systems
- **Duplicate endpoints** and use cases

### Over-Engineered Workflow
- **5+ separate tables** for a single observation workflow
- **Complex approval cascade**: Multiple approval levels with conditional logic
- **Detailed impact assessments** with financial/regulatory/operational breakdowns
- **Comprehensive resolution tracking** with validation requirements

### Granularity Confusion
- **Individual vs. grouped observations**: Unclear business logic
- **Multiple grouping strategies**: Auto vs. manual grouping
- **Mixed granularity**: Some operations work on individuals, others on groups

## Business Logic Understanding

### Observation Management Works at Two Levels

**Individual Observations:**
- **Each observation represents a specific test case failure**
- **Tied to a specific sample and attribute for a given LOB**
- **One observation per failed test execution**
- **Contains detailed failure information and evidence**

**Observation Groups:**
- **Groups multiple observations by attribute and LOB**
- **Approval workflow happens at the group level**
- **Resolution tracking at the group level**
- **Grouping enables efficient bulk processing**

### Workflow:
1. **Observations are created** from failed test execution results (one per failure)
2. **Observations are grouped** by attribute + LOB
3. **Groups go through approval** workflow (Tester → Report Owner)
4. **Resolution is tracked** at the group level
5. **Individual observations** maintain specific failure details

### Integration with Test Execution
- **Observations link to test executions** that failed or were inconclusive
- **Sample-level traceability** via test execution records
- **Attribute-level grouping** for similar issues
- **Evidence attachment** via documents/screenshots

## Proposed Simplified Architecture

### Main Table: Observation Groups (With Built-in Approval Workflow)
```sql
CREATE TABLE cycle_report_observation_groups (
    id SERIAL PRIMARY KEY,
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    
    -- Group identification (grouped by attribute + LOB)
    group_name VARCHAR(255) NOT NULL,
    group_description TEXT,
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    lob_id INTEGER NOT NULL REFERENCES lobs(id),
    
    -- Group metadata
    observation_count INTEGER DEFAULT 0,
    severity_level VARCHAR(50) DEFAULT 'medium', -- 'high', 'medium', 'low'
    issue_type VARCHAR(100) NOT NULL, -- 'data_quality', 'process_failure', 'system_error', 'compliance_gap'
    
    -- Group summary
    issue_summary TEXT NOT NULL,
    impact_description TEXT,
    proposed_resolution TEXT,
    
    -- Status and workflow (embedded approval workflow)
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'pending_tester_review', 'tester_approved', 'pending_report_owner_approval', 'report_owner_approved', 'rejected', 'resolved', 'closed'
    
    -- Tester Review (built-in)
    tester_review_status VARCHAR(50), -- 'approved', 'rejected', 'needs_clarification'
    tester_review_notes TEXT,
    tester_review_score INTEGER, -- 1-100
    tester_reviewed_by INTEGER REFERENCES users(user_id),
    tester_reviewed_at TIMESTAMP WITH TIME ZONE,
    
    -- Report Owner Approval (built-in)
    report_owner_approval_status VARCHAR(50), -- 'approved', 'rejected', 'needs_clarification'
    report_owner_approval_notes TEXT,
    report_owner_approved_by INTEGER REFERENCES users(user_id),
    report_owner_approved_at TIMESTAMP WITH TIME ZONE,
    
    -- Clarification handling (built-in)
    clarification_requested BOOLEAN DEFAULT FALSE,
    clarification_request_text TEXT,
    clarification_response TEXT,
    clarification_due_date TIMESTAMP WITH TIME ZONE,
    
    -- Resolution tracking (built-in)
    resolution_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'deferred'
    resolution_approach TEXT,
    resolution_timeline TEXT,
    resolution_owner INTEGER REFERENCES users(user_id),
    resolution_notes TEXT,
    resolved_by INTEGER REFERENCES users(user_id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Detection information
    detection_method VARCHAR(50) NOT NULL, -- 'auto_detected', 'manual_review', 'escalation'
    detected_by INTEGER NOT NULL REFERENCES users(user_id),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(attribute_id, lob_id, phase_id) -- One group per attribute+LOB combination
);
```

### Supporting Table: Individual Observations (One per Test Case Failure)
```sql
CREATE TABLE cycle_report_observations (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES cycle_report_observation_groups(id),
    
    -- Link to test execution that generated this observation (one-to-one relationship)
    test_execution_id INTEGER NOT NULL REFERENCES cycle_report_test_execution_results(id),
    test_case_id VARCHAR(255) NOT NULL REFERENCES cycle_report_test_cases(test_case_id),
    
    -- Test context (tied to specific sample and attribute for LOB)
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    sample_id VARCHAR(255) NOT NULL,
    lob_id INTEGER NOT NULL REFERENCES lobs(id),
    
    -- Observation details
    observation_title VARCHAR(255) NOT NULL,
    observation_description TEXT NOT NULL,
    
    -- Test failure details
    expected_value TEXT,
    actual_value TEXT,
    variance_details JSONB,
    test_result VARCHAR(50), -- 'fail', 'inconclusive' from test execution
    
    -- Evidence and documentation
    evidence_files JSONB, -- List of file paths, screenshots, etc.
    supporting_documentation TEXT,
    
    -- Individual observation metadata
    confidence_level FLOAT, -- 0.0 to 1.0 - confidence this is a real issue
    reproducible BOOLEAN DEFAULT FALSE,
    frequency_estimate VARCHAR(50), -- 'isolated', 'occasional', 'frequent', 'systematic'
    
    -- Impact assessment
    business_impact TEXT,
    technical_impact TEXT,
    regulatory_impact TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(test_execution_id), -- One observation per test execution
    UNIQUE(test_case_id, sample_id, attribute_id) -- One observation per test case failure
);
```

### Simplified 2-Table Architecture

The observation management phase now uses just **2 tables**:

1. **`cycle_report_observation_groups`** - Groups of observations by attribute + LOB with built-in approval workflow
2. **`cycle_report_observations`** - Individual observations (one per test case failure)

**No separate actions table needed** - all workflow tracking is built into the groups table with dedicated fields for:
- Tester review status and notes
- Report owner approval status and notes  
- Clarification handling
- Resolution tracking

## Simplified Business Logic

### 1. Observation Creation (Auto-Detection)
```python
async def create_observations_from_failed_tests(phase_id: int):
    """Auto-detect observations from failed test executions"""
    
    # Get failed test executions
    failed_tests = get_failed_test_executions(phase_id)
    
    # Group by attribute + LOB (as per your specification)
    grouped_failures = group_failures_by_attribute_and_lob(failed_tests)
    
    for (attribute_id, lob_id), test_failures in grouped_failures.items():
        # Create or get observation group (one per attribute + LOB)
        group = get_or_create_observation_group(
            phase_id=phase_id,
            attribute_id=attribute_id,
            lob_id=lob_id,
            group_name=f"Data Quality Issue - {attribute_name} ({lob_name})",
            issue_type=determine_issue_type(test_failures),
            detection_method='auto_detected'
        )
        
        # Create individual observations (one per test case failure)
        for test_failure in test_failures:
            create_individual_observation(
                group_id=group.id,
                test_execution_id=test_failure.id,
                test_case_id=test_failure.test_case_id,
                attribute_id=attribute_id,
                sample_id=test_failure.sample_id,
                lob_id=lob_id,
                observation_title=f"Test failure for {test_failure.sample_identifier}",
                observation_description=generate_observation_description(test_failure),
                expected_value=test_failure.expected_value,
                actual_value=test_failure.actual_value,
                test_result=test_failure.test_result
            )
    
    return grouped_failures
```

### 2. Tester Review (Built-in to Groups Table)
```python
async def tester_review_observation_group(group_id: int, reviewer_id: int, review_data: dict):
    """Tester reviews observation group - updates built-in fields"""
    
    group = get_observation_group(group_id)
    
    # Update tester review fields directly in the group
    group.tester_review_status = review_data.get('decision')  # 'approved', 'rejected', 'needs_clarification'
    group.tester_review_notes = review_data.get('notes')
    group.tester_review_score = review_data.get('score')
    group.tester_reviewed_by = reviewer_id
    group.tester_reviewed_at = datetime.utcnow()
    
    # Update main status
    if review_data.get('decision') == 'approved':
        group.status = 'tester_approved'
    elif review_data.get('decision') == 'rejected':
        group.status = 'rejected'
    elif review_data.get('decision') == 'needs_clarification':
        group.status = 'pending_clarification'
        group.clarification_requested = True
        group.clarification_request_text = review_data.get('clarification_request')
        group.clarification_due_date = review_data.get('clarification_due_date')
    
    # Save changes
    save_observation_group(group)
    
    return group
```

### 3. Report Owner Approval (Built-in to Groups Table)
```python
async def report_owner_approve_observation_group(group_id: int, approver_id: int, approval_data: dict):
    """Report owner approves observation group - updates built-in fields"""
    
    group = get_observation_group(group_id)
    
    # Update report owner approval fields directly in the group
    group.report_owner_approval_status = approval_data.get('decision')  # 'approved', 'rejected', 'needs_clarification'
    group.report_owner_approval_notes = approval_data.get('notes')
    group.report_owner_approved_by = approver_id
    group.report_owner_approved_at = datetime.utcnow()
    
    # Update main status
    if approval_data.get('decision') == 'approved':
        group.status = 'report_owner_approved'
    elif approval_data.get('decision') == 'rejected':
        group.status = 'rejected'
    elif approval_data.get('decision') == 'needs_clarification':
        group.status = 'pending_clarification'
        group.clarification_requested = True
        group.clarification_request_text = approval_data.get('clarification_request')
        group.clarification_due_date = approval_data.get('clarification_due_date')
    
    # Save changes
    save_observation_group(group)
    
    return group

async def resolve_observation_group(group_id: int, resolution_data: dict):
    """Mark observation group as resolved - updates built-in fields"""
    
    group = get_observation_group(group_id)
    
    # Update resolution fields directly in the group
    group.resolution_status = 'completed'
    group.resolution_approach = resolution_data.get('approach')
    group.resolution_timeline = resolution_data.get('timeline')
    group.resolution_owner = resolution_data.get('owner_id')
    group.resolution_notes = resolution_data.get('notes')
    group.resolved_by = resolution_data.get('resolved_by')
    group.resolved_at = datetime.utcnow()
    group.status = 'resolved'
    
    # Save changes
    save_observation_group(group)
    
    return group
```

## Key Simplifications

### 1. Single Architecture
**Before**: Two separate observation systems with duplicate logic
**After**: One unified system with grouping by attribute + LOB

### 2. Embedded Approval Workflow
**Before**: Complex multi-level approval with separate actions table
**After**: Built-in approval workflow fields directly in groups table

### 3. Streamlined Data Model
**Before**: 5+ tables with complex relationships
**After**: 2 core tables with clear relationships

### 4. Clear Granularity
**Before**: Confusion between individual vs. grouped observations
**After**: Clear definition - observations are per test case failure, grouped by attribute + LOB

### 5. Unified Status Management
**Before**: Multiple status enums across different entities
**After**: Single status workflow with embedded approval tracking

## Integration with Test Execution

### 1. Observation Creation Trigger
```sql
-- Observations created from failed/inconclusive test executions
INSERT INTO cycle_report_observation_groups (...)
SELECT ...
FROM cycle_report_test_execution_results ter
WHERE ter.test_result IN ('fail', 'inconclusive')
AND ter.is_latest_execution = TRUE;
```

### 2. Test Case Context
```sql
-- Each observation links back to specific test execution
-- Provides full traceability: Sample → Test Case → Test Execution → Observation
```

### 3. Evidence Integration
```sql
-- Observations can reference evidence from test execution
-- Evidence files, LLM analysis, confidence scores all available
```

## API Endpoints Design

### Observation Group Management
```
GET /api/v1/observation-mgmt/{cycle_id}/reports/{report_id}/groups
- Get all observation groups for a report

POST /api/v1/observation-mgmt/{cycle_id}/reports/{report_id}/auto-detect
- Auto-detect observations from failed test executions

POST /api/v1/observation-mgmt/groups
- Create new observation group manually
- Body: { group_name, issue_type, description, affected_attributes, affected_samples }

GET /api/v1/observation-mgmt/groups/{group_id}
- Get observation group details with individual observations

PUT /api/v1/observation-mgmt/groups/{group_id}
- Update observation group
- Body: { group_name?, description?, severity_level?, proposed_resolution? }
```

### Review and Approval
```
POST /api/v1/observation-mgmt/groups/{group_id}/review
- Submit review for observation group
- Body: { decision, notes, review_score?, clarification_request? }

GET /api/v1/observation-mgmt/{cycle_id}/reports/{report_id}/pending-review
- Get observation groups pending review

POST /api/v1/observation-mgmt/groups/{group_id}/clarify
- Respond to clarification request
- Body: { clarification_response, supporting_evidence? }
```

### Resolution Management
```
POST /api/v1/observation-mgmt/groups/{group_id}/resolve
- Mark observation group as resolved
- Body: { resolution_approach, timeline, owner_id, notes }

GET /api/v1/observation-mgmt/{cycle_id}/reports/{report_id}/resolution-status
- Get resolution status for all observations

POST /api/v1/observation-mgmt/groups/{group_id}/close
- Close observation group (final state)
- Body: { closure_notes, lessons_learned? }
```

### Individual Observation Management
```
GET /api/v1/observation-mgmt/groups/{group_id}/observations
- Get individual observations within a group

POST /api/v1/observation-mgmt/groups/{group_id}/observations
- Add individual observation to group
- Body: { test_execution_id, observation_title, description, evidence_files? }

PUT /api/v1/observation-mgmt/observations/{observation_id}
- Update individual observation
- Body: { description?, evidence_files?, business_impact?, technical_impact? }
```

## Data Migration Strategy

### Phase 1: Create New Tables
```sql
-- Create simplified observation tables
CREATE TABLE cycle_report_observation_groups (...);
CREATE TABLE cycle_report_observations (...);
CREATE TABLE cycle_report_observation_actions (...);
```

### Phase 2: Migrate Existing Data
```sql
-- Migrate from ObservationRecord to observation groups
-- Consolidate related observations into groups
-- Migrate approval/resolution data to actions table
```

### Phase 3: Update Application Code
- Replace dual observation systems with unified system
- Update all service layers to use new tables
- Modify frontend to work with group-based approach

### Phase 4: Clean Up
```sql
-- Drop old observation tables after successful migration
DROP TABLE cycle_report_observation_mgmt_observation_records;
DROP TABLE cycle_report_observation_mgmt_impact_assessments;
DROP TABLE cycle_report_observation_mgmt_approvals;
DROP TABLE cycle_report_observation_mgmt_resolutions;
```

## Benefits of Simplified Architecture

### 1. Unified System
- **Single observation management** approach
- **Consistent data model** across all functionality
- **Simplified maintenance** and development

### 2. Improved Performance
- **Fewer tables** and simpler queries
- **Reduced join complexity** for observation data
- **Better scalability** with grouped approach

### 3. Clearer Business Logic
- **Group-first approach** matches business thinking
- **Simplified approval workflow** reduces confusion
- **Clear status transitions** easier to understand

### 4. Better Integration
- **Direct links** to test execution results
- **Consistent patterns** with other phases
- **Standardized audit trail** and workflow

## Conclusion

The proposed simplification reduces the Observation Management phase from a complex dual-system architecture to a clean, unified approach. This provides:

1. **Elimination of dual systems** - Single, consistent observation management
2. **90% reduction** in table complexity (from 5+ tables to 3 tables)
3. **Simplified approval workflow** - Clear, predictable process
4. **Better integration** with test execution and other phases
5. **Improved maintainability** - Single codebase, consistent patterns

The new architecture maintains all business functionality while dramatically reducing complexity and improving system performance.