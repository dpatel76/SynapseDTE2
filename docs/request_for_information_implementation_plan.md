# Request for Information Phase - Simplified Implementation Plan

## Overview

This document outlines the simplification of the Request for Information (RFI) phase database architecture, moving from a complex multi-table system to a clean 2-table versioning pattern consistent with other phases.

## Current Architecture Issues

### Complex Table Structure
- **5 separate tables** with complex relationships
- **Individual test case records** (Sample × Attribute matrix creates thousands of records)
- **Complex document revision tracking** with parent-child relationships
- **Individual notification management** per data owner
- **Multiple status tracking systems** across different entities

### Performance Problems
- **Massive record counts**: 100 samples × 50 attributes = 5,000 individual test cases
- **Complex joins** for progress calculation
- **Slow queries** due to granular record structure

## Proposed Simplified Architecture

### 2-Table Versioning Pattern

#### Table 1: Master Configuration Table
```sql
CREATE TABLE cycle_report_request_info_master (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- Phase configuration
    instructions TEXT,
    submission_deadline TIMESTAMP WITH TIME ZONE,
    auto_notify_data_owners BOOLEAN DEFAULT TRUE,
    escalation_enabled BOOLEAN DEFAULT TRUE,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'not_started',
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    updated_by INTEGER NOT NULL REFERENCES users(user_id),
    
    UNIQUE(cycle_id, report_id)
);
```

#### Table 2: Versioned Assignments and Submissions
```sql
CREATE TABLE cycle_report_request_info_versions (
    id SERIAL PRIMARY KEY,
    master_id INTEGER NOT NULL REFERENCES cycle_report_request_info_master(id),
    version_number INTEGER NOT NULL DEFAULT 1,
    
    -- Version metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    version_notes TEXT,
    is_current BOOLEAN DEFAULT FALSE,
    
    -- Bulk data owner assignments (replaces individual test cases)
    data_owner_assignments JSONB NOT NULL,
    /*
    Structure:
    {
      "assignments": [
        {
          "data_owner_id": 123,
          "data_owner_name": "John Smith",
          "assigned_attributes": [
            {
              "attribute_id": 456,
              "attribute_name": "customer_id",
              "samples_assigned": ["sample1", "sample2", "sample3"]
            }
          ],
          "assignment_date": "2024-01-01T00:00:00Z",
          "notification_sent": true,
          "notification_sent_at": "2024-01-01T09:00:00Z",
          "submissions": [
            {
              "attribute_name": "customer_id",
              "sample_identifier": "sample1",
              "document_name": "customer_id_sample1.pdf",
              "document_path": "/uploads/...",
              "document_size": 1024000,
              "mime_type": "application/pdf",
              "submission_date": "2024-01-05T14:30:00Z",
              "submission_status": "submitted",
              "validation_status": "valid",
              "revision_number": 1,
              "comments": "Initial submission"
            }
          ],
          "progress": {
            "total_required": 15,
            "submitted": 8,
            "pending": 7,
            "completion_percentage": 53.3
          }
        }
      ]
    }
    */
    
    -- Overall phase progress summary
    progress_summary JSONB,
    /*
    Structure:
    {
      "total_data_owners": 5,
      "data_owners_with_assignments": 5,
      "data_owners_completed": 2,
      "total_attribute_sample_pairs": 150,
      "submitted_pairs": 75,
      "pending_pairs": 75,
      "overall_completion_percentage": 50.0,
      "submission_deadline": "2024-01-15T23:59:59Z",
      "days_remaining": 5,
      "sla_status": "on_track"
    }
    */
    
    -- Escalation tracking
    escalation_log JSONB DEFAULT '[]',
    /*
    Structure:
    [
      {
        "escalation_date": "2024-01-10T00:00:00Z",
        "escalation_level": "level_1",
        "data_owner_id": 123,
        "reason": "missed_deadline",
        "action_taken": "email_reminder_sent",
        "resolved": false
      }
    ]
    */
    
    -- Decision tracking (Tester review)
    tester_decision JSONB,
    /*
    Structure:
    {
      "decision": "approved",  // approved, rejected, requires_revision
      "decided_by": 789,
      "decided_at": "2024-01-20T10:00:00Z",
      "decision_notes": "All documents received and validated",
      "validation_results": {
        "total_submissions": 150,
        "valid_submissions": 148,
        "invalid_submissions": 2,
        "missing_submissions": 0
      }
    }
    */
    
    -- Version lifecycle status
    status VARCHAR(50) DEFAULT 'draft',
    /*
    Values:
    - draft: Version being prepared
    - active: Current active version with assignments
    - submitted: All documents received, pending tester review
    - approved: Tester approved all submissions
    - rejected: Tester rejected, needs revision
    - superseded: Replaced by newer version
    */
    
    -- Approval workflow timestamps
    submitted_at TIMESTAMP WITH TIME ZONE,
    submitted_by INTEGER REFERENCES users(user_id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by INTEGER REFERENCES users(user_id),
    
    UNIQUE(master_id, version_number)
);
```

## Simplified Business Logic

### Phase Initialization
1. **Create Master Record**: Basic phase configuration
2. **Generate Initial Version**: Calculate bulk assignments by data owner
3. **Send Notifications**: Notify all data owners of their assignments

### Data Owner Portal
1. **View Assignments**: Data owner sees all their attribute-sample pairs
2. **Bulk Upload**: Upload documents for multiple assignments at once
3. **Progress Tracking**: Real-time progress calculation from JSONB data

### Tester Review
1. **Validate Submissions**: Review all submitted documents
2. **Approve/Reject**: Single decision for entire phase
3. **Request Revisions**: Create new version if changes needed

### Key Simplifications

#### 1. Bulk Assignment Model
**Before**: Individual test case per Sample × Attribute
- 100 samples × 50 attributes = 5,000 test case records
- Complex status tracking per test case

**After**: Bulk assignment per data owner
- Group all assignments by data owner
- Store in JSONB structure
- Single record per data owner with all their assignments

#### 2. Embedded Document Submissions
**Before**: Separate document submission table with revisions
- Complex parent-child relationships
- Multiple status fields
- Revision tracking complexity

**After**: Submissions embedded in version JSONB
- All submissions stored in version record
- Simple revision tracking via version numbers
- No separate document table needed

#### 3. Unified Progress Tracking
**Before**: Complex aggregations across multiple tables
- Count completed test cases
- Calculate percentages
- Track individual statuses

**After**: Calculated progress stored in JSONB
- Progress calculated during submission
- Cached in version record
- Real-time updates without complex queries

#### 4. Single Decision Point
**Before**: Individual test case approvals
- Complex approval workflow
- Multiple decision points

**After**: Single tester decision per version
- Approve/reject entire phase submission
- Single decision workflow
- Clear version lifecycle

## Data Migration Strategy

### Phase 1: Create New Tables
```sql
-- Create new simplified tables
CREATE TABLE cycle_report_request_info_master (...);
CREATE TABLE cycle_report_request_info_versions (...);

-- Create indexes
CREATE INDEX idx_request_info_master_cycle_report ON cycle_report_request_info_master(cycle_id, report_id);
CREATE INDEX idx_request_info_versions_master ON cycle_report_request_info_versions(master_id);
CREATE INDEX idx_request_info_versions_current ON cycle_report_request_info_versions(master_id, is_current);
```

### Phase 2: Migrate Existing Data
```sql
-- Migration script to convert existing data
INSERT INTO cycle_report_request_info_master (cycle_id, report_id, phase_id, ...)
SELECT DISTINCT cycle_id, report_id, phase_id, ...
FROM cycle_report_test_cases;

-- Aggregate test cases by data owner and convert to JSONB
INSERT INTO cycle_report_request_info_versions (master_id, data_owner_assignments, ...)
SELECT 
    master.id,
    jsonb_build_object(
        'assignments',
        jsonb_agg(
            jsonb_build_object(
                'data_owner_id', tc.data_owner_id,
                'assigned_attributes', ...,
                'submissions', ...
            )
        )
    )
FROM cycle_report_request_info_master master
JOIN cycle_report_test_cases tc ON ...
GROUP BY master.id;
```

### Phase 3: Update Application Code
1. **Update Models**: Modify SQLAlchemy models to use new tables
2. **Update Use Cases**: Implement bulk assignment logic
3. **Update Endpoints**: Modify APIs to work with new data structure
4. **Update Frontend**: Adapt UI to work with bulk assignments

### Phase 4: Clean Up
```sql
-- Drop old tables after successful migration
DROP TABLE cycle_report_test_cases;
DROP TABLE document_submissions;
DROP TABLE data_owner_notifications;
```

## Benefits of Simplified Architecture

### 1. Performance Improvements
- **Reduced Record Count**: From thousands of test cases to single version records
- **Faster Queries**: Simple JSONB queries vs complex joins
- **Better Scalability**: Linear growth instead of exponential

### 2. Simplified Maintenance
- **Consistent Pattern**: Same 2-table versioning as other phases
- **Single Data Model**: All phase data in two tables
- **Easier Debugging**: Clear data structure and relationships

### 3. Enhanced Functionality
- **Version History**: Complete history of all assignments and submissions
- **Bulk Operations**: Easier bulk assignment and submission management
- **Real-time Progress**: Cached progress calculations for instant updates

### 4. Architectural Consistency
- **Unified Approach**: Same pattern across all phases
- **Standardized Workflows**: Consistent version lifecycle
- **Easier Integration**: Standard interfaces between phases

## Implementation Timeline

### Week 1: Database Changes
- Create new table structure
- Write migration scripts
- Test data migration

### Week 2: Backend Updates
- Update models and schemas
- Implement new use cases
- Update API endpoints

### Week 3: Frontend Updates
- Modify data owner portal
- Update tester review interface
- Test bulk operations

### Week 4: Testing & Deployment
- Integration testing
- Performance testing
- Production deployment

## Risk Mitigation

### Data Loss Prevention
- **Parallel Tables**: Keep old tables during migration
- **Validation Scripts**: Verify data integrity after migration
- **Rollback Plan**: Ability to revert to old structure if needed

### Performance Monitoring
- **Query Performance**: Monitor JSONB query performance
- **Index Optimization**: Ensure proper indexing on JSONB fields
- **Capacity Planning**: Monitor storage usage with JSONB data

### User Experience
- **Training**: Update documentation for new workflows
- **Support**: Provide user support during transition
- **Feedback**: Collect user feedback on new interface

## Conclusion

The proposed simplification reduces the Request for Information phase from a complex 5-table structure to a clean 2-table versioning pattern. This provides:

1. **90% reduction** in database records
2. **Improved performance** through simplified queries
3. **Architectural consistency** with other phases
4. **Enhanced maintainability** through unified patterns

The new structure maintains all existing functionality while significantly reducing complexity and improving system performance.