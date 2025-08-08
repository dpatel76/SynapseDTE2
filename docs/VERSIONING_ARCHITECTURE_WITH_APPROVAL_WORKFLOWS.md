# Versioning Architecture with Approval Workflows - Complete Documentation

## Executive Summary

This document provides comprehensive documentation of the versioning architecture implemented across all phases of the SynapseDTE system, with a focus on approval workflows, editability rules, and the transition away from JSON-based phase_data storage to dedicated version tables.

## Table of Contents

1. [Core Versioning Architecture](#core-versioning-architecture)
2. [Version Status States and Lifecycle](#version-status-states-and-lifecycle)
3. [Editability Rules](#editability-rules)
4. [Report Owner Feedback Display Logic](#report-owner-feedback-display-logic)
5. [Migration from phase_data JSON Storage](#migration-from-phase_data-json-storage)
6. [Phase-Specific Implementations](#phase-specific-implementations)
7. [Frontend Integration Patterns](#frontend-integration-patterns)
8. [Best Practices and Guidelines](#best-practices-and-guidelines)

## Core Versioning Architecture

### 1. The _versions Table Pattern

All versioned phases follow a consistent two-table architecture:

```sql
-- Version table (parent)
cycle_report_{phase}_versions
  - version_id (UUID, primary key)
  - phase_id (foreign key to workflow_phases)
  - version_number (integer, incremental)
  - version_status (enum: draft, pending_approval, approved, rejected, superseded)
  - parent_version_id (self-referential for version history)
  - workflow_execution_id (Temporal integration)
  - workflow_run_id (Temporal integration)
  - submitted_by_id, submitted_at (submission tracking)
  - approved_by_id, approved_at (approval tracking)
  - created_by_id, created_at, updated_by_id, updated_at (audit)

-- Detail table (child)
cycle_report_{phase}_details
  - detail_id (UUID, primary key)
  - version_id (foreign key to versions table)
  - phase_id (for query optimization)
  - [phase-specific fields]
  - tester_decision, tester_decision_by_id, tester_decision_at
  - report_owner_decision, report_owner_decision_by_id, report_owner_decision_at
```

### 2. Key Design Principles

1. **Version Immutability**: Once a version moves beyond draft status, its content becomes immutable
2. **Audit Trail**: Every version maintains complete audit history through created/updated timestamps
3. **Dual Decision Model**: Tester and Report Owner decisions are tracked separately
4. **Workflow Integration**: Each version is linked to Temporal workflow executions for orchestration
5. **Parent-Child Relationships**: New versions can be created from existing versions

## Version Status States and Lifecycle

### Status Definitions

```python
class VersionStatus(str, Enum):
    DRAFT = "draft"                    # Editable by tester
    PENDING_APPROVAL = "pending_approval"  # Submitted, awaiting report owner review
    APPROVED = "approved"              # Approved by report owner, now read-only
    REJECTED = "rejected"              # Rejected by report owner, editable by tester
    SUPERSEDED = "superseded"          # Replaced by a newer approved version
```

### Status Transition Rules

```
DRAFT → PENDING_APPROVAL (via submission)
PENDING_APPROVAL → APPROVED (via report owner approval)
PENDING_APPROVAL → REJECTED (via report owner rejection)
REJECTED → DRAFT (when tester makes changes)
REJECTED → PENDING_APPROVAL (via resubmission)
APPROVED → SUPERSEDED (when new version is approved)
```

## Editability Rules

### Core Editability Logic

```python
@hybrid_property
def can_be_edited(self) -> bool:
    """Version can be edited only in DRAFT or REJECTED status"""
    return self.version_status in [VersionStatus.DRAFT, VersionStatus.REJECTED]
```

### Role-Based Edit Permissions

1. **Tester**:
   - Can edit: DRAFT and REJECTED versions
   - Cannot edit: PENDING_APPROVAL, APPROVED, SUPERSEDED versions

2. **Report Owner**:
   - Can provide feedback on: PENDING_APPROVAL versions
   - Cannot directly edit any version content
   - Can only approve/reject with feedback

### Frontend Editability Implementation

```typescript
// Sample Selection Example
const isEditable = useMemo(() => {
  if (!currentVersion) return false;
  
  // Check version status
  const editableStatuses = ['draft', 'rejected'];
  if (!editableStatuses.includes(currentVersion.version_status)) {
    return false;
  }
  
  // Check user role
  return user?.role?.role_name === 'Tester';
}, [currentVersion, user]);
```

## Report Owner Feedback Display Logic

### When to Show Report Owner Feedback

Report owner feedback should be displayed when:

1. **Version has been submitted** (status is not 'draft')
2. **Report owner has provided feedback** (approval_notes or rejection_reason exists)
3. **Individual item decisions exist** (for phases with item-level decisions)

### Implementation Pattern

```python
# Backend - Sample Selection Example
if version.version_status != VersionStatus.DRAFT:
    # Load report owner decisions from detail records
    samples_with_ro_feedback = await db.execute(
        select(SampleSelectionSample)
        .where(
            and_(
                SampleSelectionSample.version_id == version.version_id,
                SampleSelectionSample.report_owner_decision != SampleDecision.PENDING
            )
        )
    )
```

```typescript
// Frontend - Sample Selection Example
const showReportOwnerFeedback = useMemo(() => {
  if (!currentVersion) return false;
  
  // Version must be submitted (not draft)
  if (currentVersion.version_status === 'draft') return false;
  
  // Check for version-level feedback
  if (currentVersion.approval_notes || currentVersion.rejection_reason) {
    return true;
  }
  
  // Check for item-level feedback
  return samples.some(s => s.report_owner_decision !== 'pending');
}, [currentVersion, samples]);
```

## Migration from phase_data JSON Storage

### Why We Moved Away from phase_data

The `workflow_phases.phase_data` JSONB column was initially used to store all phase-specific data, but this approach had several limitations:

1. **No Version History**: Changes overwrote previous data
2. **Limited Querying**: Difficult to query specific fields efficiently
3. **No Referential Integrity**: Foreign keys couldn't be enforced
4. **Poor Performance**: Large JSON objects slowed down queries
5. **Audit Challenges**: Tracking who changed what and when was complex

### Migration Strategy

```sql
-- Example: Migrating sample selection from phase_data to version tables

-- Step 1: Create version from phase_data
INSERT INTO cycle_report_sample_selection_versions (
    phase_id,
    version_number,
    version_status,
    selection_criteria,
    target_sample_size,
    created_by_id,
    created_at
)
SELECT 
    phase_id,
    1 as version_number,
    'approved' as version_status,
    phase_data->'selection_criteria',
    (phase_data->>'target_sample_size')::int,
    created_by_id,
    created_at
FROM workflow_phases
WHERE phase_name = 'Sample Selection'
AND phase_data IS NOT NULL;

-- Step 2: Migrate samples
INSERT INTO cycle_report_sample_selection_samples (...)
SELECT ... FROM workflow_phases, jsonb_array_elements(phase_data->'samples');

-- Step 3: Clear phase_data
UPDATE workflow_phases 
SET phase_data = NULL 
WHERE phase_name = 'Sample Selection';
```

## Phase-Specific Implementations

### 1. Sample Selection Phase

**Status**: ✅ Fully Implemented with Version Tables

- **Version Table**: `cycle_report_sample_selection_versions`
- **Detail Table**: `cycle_report_sample_selection_samples`
- **Key Features**:
  - Individual sample decisions (tester + report owner)
  - Sample categories (clean, anomaly, boundary)
  - Intelligent sampling integration
  - Carry-forward functionality

### 2. Scoping Phase

**Status**: ✅ Fully Implemented with Version Tables

- **Version Table**: `cycle_report_scoping_versions`
- **Detail Table**: `cycle_report_scoping_attributes`
- **Key Features**:
  - Attribute-level scoping decisions
  - LLM recommendations with confidence scores
  - Override tracking and rationale
  - CDE identification

### 3. Data Profiling Phase

**Status**: ✅ Fully Implemented with Version Tables

- **Version Table**: `cycle_report_data_profiling_rule_versions`
- **Detail Table**: `cycle_report_data_profiling_rules`
- **Key Features**:
  - Rule generation and management
  - Dual decision model (tester + report owner)
  - Background job execution tracking
  - No execution results in tables (uses job system)

### 4. Request for Information (RFI) Phase

**Status**: ⚠️ Partially Implemented

- Uses consolidated tables but may still rely on phase_data for some features
- Needs review for full version table migration

### 5. Planning Phase

**Status**: ❌ Still Uses phase_data

- Complex multi-table structure makes migration challenging
- Would benefit from version table approach for consistency

## Frontend Integration Patterns

### 1. Version Management Hook

```typescript
const useVersionManagement = (phaseId: number) => {
  const [versions, setVersions] = useState<Version[]>([]);
  const [currentVersion, setCurrentVersion] = useState<Version | null>(null);
  
  // Load versions
  useEffect(() => {
    loadVersions(phaseId);
  }, [phaseId]);
  
  // Determine current version
  useEffect(() => {
    const current = versions.find(v => 
      v.version_status === 'approved' && 
      v.version_number === Math.max(...versions
        .filter(v => v.version_status === 'approved')
        .map(v => v.version_number))
    );
    setCurrentVersion(current || versions[0]);
  }, [versions]);
  
  return { versions, currentVersion, isEditable, canSubmit };
};
```

### 2. Conditional Rendering Based on Status

```typescript
// Show different UI based on version status
{currentVersion?.version_status === 'draft' && (
  <EditableForm />
)}

{currentVersion?.version_status === 'pending_approval' && (
  <ReadOnlyView />
)}

{currentVersion?.version_status === 'approved' && (
  <ApprovedView />
)}

{currentVersion?.version_status === 'rejected' && (
  <EditableFormWithFeedback />
)}
```

### 3. Report Owner Feedback Component

```typescript
const ReportOwnerFeedback: React.FC<Props> = ({ version, items }) => {
  // Only show if version has been submitted
  if (version.version_status === 'draft') return null;
  
  return (
    <Card>
      <CardHeader>Report Owner Feedback</CardHeader>
      <CardContent>
        {/* Version-level feedback */}
        {version.approval_notes && (
          <Alert>
            <AlertDescription>{version.approval_notes}</AlertDescription>
          </Alert>
        )}
        
        {/* Item-level feedback */}
        {items.map(item => (
          item.report_owner_decision !== 'pending' && (
            <ItemFeedback key={item.id} item={item} />
          )
        ))}
      </CardContent>
    </Card>
  );
};
```

## Best Practices and Guidelines

### 1. Version Creation

- Always create a new version when starting changes
- Copy relevant data from parent version if needed
- Set appropriate workflow context

### 2. Status Management

- Use service layer methods for status transitions
- Validate business rules before status changes
- Update related metadata (timestamps, user IDs)

### 3. Editability Checks

- Always check `can_be_edited` before allowing modifications
- Implement role-based permissions in addition to status checks
- Provide clear user feedback when editing is disabled

### 4. Report Owner Feedback

- Display feedback prominently but don't obstruct workflow
- Show both version-level and item-level feedback
- Maintain feedback history across versions

### 5. Performance Optimization

- Use phase_id indexes for efficient queries
- Avoid loading all versions when only current is needed
- Implement pagination for large detail sets

### 6. Migration Considerations

- Preserve audit trail during migration
- Validate data integrity after migration
- Provide rollback capability if needed
- Update all dependent code to use new structure

## Conclusion

The versioning architecture with approval workflows provides a robust foundation for managing complex multi-stakeholder processes. By moving away from phase_data JSON storage to dedicated version tables, we've achieved:

1. **Better Data Integrity**: Foreign keys and constraints ensure consistency
2. **Improved Performance**: Indexed columns and normalized data
3. **Complete Audit Trail**: Every change is tracked with who and when
4. **Clear Approval Workflows**: Status transitions enforce business rules
5. **Flexible Editability**: Role and status-based permissions

All new phases should follow this pattern, and existing phases using phase_data should be migrated when feasible.