# Data Profiling Versioning Implementation

## Overview

The Data Profiling module follows a unified versioning architecture that mirrors the patterns used in Sample Selection and Scoping phases. This ensures consistency across all workflow phases while providing robust version control for profiling rules.

## Architecture

### Two-Table Design

1. **`cycle_report_data_profiling_rule_versions`** - Version management table
2. **`cycle_report_data_profiling_rules`** - Individual rules table

### Version Lifecycle

```
DRAFT → PENDING_APPROVAL → APPROVED/REJECTED → SUPERSEDED
```

- **DRAFT**: Initial state when rules are being generated or modified
- **PENDING_APPROVAL**: Submitted for approval workflow
- **APPROVED**: Accepted by both tester and report owner
- **REJECTED**: Rejected during approval process
- **SUPERSEDED**: Replaced by a newer approved version

## Key Features

### 1. Version Creation

A new version is created when:
- Initial rule generation is triggered (LLM-based)
- Significant changes require a new rule set
- Previous version was rejected and needs revision

```python
# Example: Creating initial version
version = DataProfilingRuleVersion(
    phase_id=phase_id,
    version_number=1,
    version_status=VersionStatus.DRAFT,
    data_source_type="file_upload",
    total_rules=0
)
```

### 2. Rule Management

Each rule is associated with a version and includes:
- `version_id`: Links to the parent version
- `is_current_version`: Boolean flag indicating if this is the active rule
- `rule_id`: Unique identifier for the rule
- Tester and Report Owner decision fields

### 3. Dual Decision Workflow

Each rule tracks two separate decision paths:

**Tester Decision:**
- `tester_decision`: approve/reject/request_changes
- `tester_notes`: Comments from tester
- `tester_decided_by`: User ID
- `tester_decided_at`: Timestamp

**Report Owner Decision:**
- `report_owner_decision`: approve/reject/request_changes
- `report_owner_notes`: Comments from report owner
- `report_owner_decided_by`: User ID
- `report_owner_decided_at`: Timestamp

### 4. Version Tracking

The system maintains:
- **Version Number**: Sequential numbering (1, 2, 3...)
- **Current Version**: Only one version can be active at a time
- **History**: All previous versions are retained for audit trail

### 5. Business Key Pattern

Rules use a business key pattern for tracking across versions:
```
business_key = f"{attribute_id}_{rule_type}_{rule_name_slug}"
```

This allows the same logical rule to exist across multiple versions while maintaining history.

## Workflow Integration

### 1. Rule Generation
- Background job creates rules incrementally
- Rules are persisted after each attribute (for restart capability)
- Job progress is tracked in real-time

### 2. Approval Process
- Tester reviews and approves/rejects individual rules
- Rules can be bulk approved/rejected
- Report Owner performs final approval
- Version status updates based on rule decisions

### 3. Version Transitions
- When all rules in a version are approved → Version becomes APPROVED
- If any rule is rejected → Version may need revision
- New version creation preserves previous version as SUPERSEDED

## Database Schema

### Version Table
```sql
CREATE TABLE cycle_report_data_profiling_rule_versions (
    version_id UUID PRIMARY KEY,
    phase_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    version_status version_status_enum NOT NULL,
    total_rules INTEGER DEFAULT 0,
    approved_rules INTEGER DEFAULT 0,
    rejected_rules INTEGER DEFAULT 0,
    -- ... other fields
);
```

### Rules Table
```sql
CREATE TABLE cycle_report_data_profiling_rules (
    rule_id SERIAL PRIMARY KEY,
    version_id UUID NOT NULL,
    attribute_id INTEGER NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    rule_type rule_type_enum NOT NULL,
    is_current_version BOOLEAN DEFAULT true,
    business_key VARCHAR(500),
    -- ... decision fields
);
```

## Rules History

The system maintains rule history through:

1. **Version History**: Each version preserves a complete snapshot of rules
2. **Business Key Tracking**: Same logical rule tracked across versions
3. **Change Tracking**: Audit fields track who made changes and when
4. **Decision History**: All approval/rejection decisions are preserved

## API Endpoints

### Version Management
- `POST /data-profiling/cycles/{cycle_id}/reports/{report_id}/generate-rules` - Create new version with LLM rules
- `GET /data-profiling/cycles/{cycle_id}/reports/{report_id}/versions` - List all versions
- `PUT /data-profiling/versions/{version_id}/submit` - Submit version for approval

### Rule Operations
- `GET /data-profiling/cycles/{cycle_id}/reports/{report_id}/rules` - Get current rules (filtered by is_current_version)
- `PUT /data-profiling/rules/{rule_id}/approve` - Approve individual rule
- `PUT /data-profiling/rules/{rule_id}/reject` - Reject individual rule
- `DELETE /data-profiling/rules/{rule_id}` - Delete rule (testers only)

## Best Practices

1. **Always filter by `is_current_version=true`** when displaying active rules
2. **Preserve history** - Never hard delete versions or rules
3. **Use transactions** for version state changes
4. **Track all decisions** with user and timestamp
5. **Implement incremental saves** for long-running operations

## Comparison with Legacy System

The legacy system had 23+ tables for data profiling. The new unified architecture:
- Reduces complexity from 23 tables to 2
- Provides consistent versioning across all phases
- Enables better audit trails
- Simplifies the approval workflow
- Improves performance with focused queries