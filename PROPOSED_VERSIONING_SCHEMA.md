# Proposed Unified Versioning Schema

## Core Versioning Concept

All versioned entities should follow a consistent pattern using the existing `VersionedMixin` from `versioning.py`.

### 1. Base Versioning Structure

```sql
-- Core versioning fields (from VersionedMixin)
version_number INTEGER NOT NULL DEFAULT 1
version_status VARCHAR(20) -- 'draft', 'submitted', 'approved', 'rejected'
version_created_at TIMESTAMP WITH TIME ZONE
version_created_by INTEGER REFERENCES users(user_id)
version_submitted_at TIMESTAMP WITH TIME ZONE
version_submitted_by INTEGER REFERENCES users(user_id)
version_reviewed_at TIMESTAMP WITH TIME ZONE
version_reviewed_by INTEGER REFERENCES users(user_id)
version_review_notes TEXT
parent_version_id UUID -- Reference to previous version
approved_version_id UUID -- Reference to currently approved version
is_deleted BOOLEAN DEFAULT FALSE
deleted_at TIMESTAMP WITH TIME ZONE
deleted_by INTEGER REFERENCES users(user_id)
```

### 2. Sample Selection Versioning Redesign

Instead of versioning entire sample sets, version individual sample decisions:

```sql
-- New table: sample_selection_versions
CREATE TABLE sample_selection_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id UUID NOT NULL,
    report_id UUID NOT NULL,
    
    -- Versioning fields from VersionedMixin
    version_number INTEGER NOT NULL DEFAULT 1,
    version_status VARCHAR(20) NOT NULL DEFAULT 'draft',
    parent_version_id UUID REFERENCES sample_selection_versions(version_id),
    approved_version_id UUID REFERENCES sample_selection_versions(version_id),
    
    -- Version metadata
    version_created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version_created_by INTEGER REFERENCES users(user_id),
    version_notes TEXT,
    
    -- Constraints
    UNIQUE(cycle_id, report_id, version_number)
);

-- New table: sample_decisions
CREATE TABLE sample_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID REFERENCES sample_selection_versions(version_id),
    sample_id UUID NOT NULL,
    
    -- Sample metadata
    sample_data JSONB NOT NULL,
    sample_type VARCHAR(50), -- 'Population', 'Targeted', etc.
    
    -- Decision tracking
    recommendation_source VARCHAR(50), -- 'tester', 'llm', 'manual'
    recommended_by INTEGER REFERENCES users(user_id),
    recommended_at TIMESTAMP WITH TIME ZONE,
    
    -- Approval tracking
    decision_status VARCHAR(20), -- 'pending', 'approved', 'rejected', 'modified'
    decided_by INTEGER REFERENCES users(user_id),
    decided_at TIMESTAMP WITH TIME ZONE,
    decision_notes TEXT,
    
    -- Carry-forward tracking
    carried_from_version_id UUID,
    carried_from_decision_id UUID,
    modification_reason TEXT
);

-- Index for performance
CREATE INDEX idx_sample_decisions_version ON sample_decisions(version_id);
CREATE INDEX idx_sample_decisions_status ON sample_decisions(version_id, decision_status);
```

### 3. Workflow for Sample Selection Versioning

1. **Initial Version (v1)**:
   - Tester recommends samples → creates records with `recommendation_source = 'tester'`
   - LLM generates samples → creates records with `recommendation_source = 'llm'`
   - All have `decision_status = 'pending'`

2. **Report Owner Review**:
   - Approves samples → `decision_status = 'approved'`
   - Rejects samples → `decision_status = 'rejected'`
   - Requests modifications → triggers new version

3. **New Version (v2)**:
   - System automatically carries forward all `approved` samples from v1
   - Sets `carried_from_version_id` and `carried_from_decision_id`
   - Tester adds new recommendations
   - Report owner feedback incorporated

### 4. Unified Phase Data Model

Instead of separate tables for each phase, use a more flexible approach:

```sql
-- Core phase tracking
CREATE TABLE workflow_phase_data (
    data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id UUID NOT NULL,
    report_id UUID NOT NULL,
    phase_name VARCHAR(50) NOT NULL,
    
    -- Versioning (inherits from VersionedMixin)
    version_number INTEGER NOT NULL DEFAULT 1,
    version_status VARCHAR(20) NOT NULL DEFAULT 'draft',
    parent_version_id UUID REFERENCES workflow_phase_data(data_id),
    approved_version_id UUID REFERENCES workflow_phase_data(data_id),
    
    -- Phase data (flexible JSON structure)
    phase_data JSONB NOT NULL,
    
    -- Standard timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(cycle_id, report_id, phase_name, version_number)
);
```

### 5. Tagging Approved Artifacts

Create a unified tagging system:

```sql
-- Approved artifacts registry
CREATE TABLE approved_artifacts (
    artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id UUID NOT NULL,
    report_id UUID NOT NULL,
    phase_name VARCHAR(50) NOT NULL,
    artifact_type VARCHAR(50) NOT NULL, -- 'attributes', 'samples', 'test_cases', etc.
    
    -- Reference to the approved version
    reference_table VARCHAR(100) NOT NULL,
    reference_id UUID NOT NULL,
    reference_version INTEGER NOT NULL,
    
    -- Approval metadata
    approved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    approved_by INTEGER REFERENCES users(user_id),
    approval_notes TEXT,
    
    -- Ensure one approved artifact per type per phase
    UNIQUE(cycle_id, report_id, phase_name, artifact_type)
);
```

## Benefits of This Approach

1. **Consistency**: All versioning follows the same pattern
2. **Traceability**: Clear lineage of how data evolved through versions
3. **Flexibility**: JSON storage allows phase-specific data without new tables
4. **Performance**: Fewer tables, better indexes, simpler queries
5. **Maintainability**: Single versioning logic to maintain

## Migration Strategy

1. **Phase 1**: Implement new versioning tables alongside existing ones
2. **Phase 2**: Migrate data progressively by phase
3. **Phase 3**: Update application code to use new tables
4. **Phase 4**: Deprecate and remove old tables

## Query Examples

### Get current approved samples for a report:
```sql
SELECT sd.* 
FROM sample_decisions sd
JOIN sample_selection_versions ssv ON sd.version_id = ssv.version_id
WHERE ssv.cycle_id = :cycle_id 
  AND ssv.report_id = :report_id
  AND ssv.version_status = 'approved'
  AND sd.decision_status = 'approved';
```

### Get sample lineage across versions:
```sql
WITH RECURSIVE sample_lineage AS (
    -- Base case: current version
    SELECT sd.*, ssv.version_number, 0 as depth
    FROM sample_decisions sd
    JOIN sample_selection_versions ssv ON sd.version_id = ssv.version_id
    WHERE sd.decision_id = :decision_id
    
    UNION ALL
    
    -- Recursive case: previous versions
    SELECT sd.*, ssv.version_number, sl.depth + 1
    FROM sample_decisions sd
    JOIN sample_selection_versions ssv ON sd.version_id = ssv.version_id
    JOIN sample_lineage sl ON sd.decision_id = sl.carried_from_decision_id
)
SELECT * FROM sample_lineage ORDER BY depth;
```