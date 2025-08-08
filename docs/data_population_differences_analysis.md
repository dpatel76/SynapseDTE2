# Data Population Differences Analysis: Standalone vs Container
## Column-Level Data Comparison
## Date: 2025-08-06

## Executive Summary
This analysis compares the actual data population within tables between the standalone and container databases, focusing on columns that were populated before but are now empty or have different data formats.

## Key Findings

### 1. Different Data Sets Being Used
- **Standalone DB**: Contains data for cycle_id=55,58 and report_id=156
- **Container DB**: Contains data for cycle_id=2 and report_id=3
- This is not a migration issue but completely different test data sets

### 2. Schema Differences
Several tables have different column structures between versions:

## Table-by-Table Analysis

### 🔴 WORKFLOW_PHASES Table

#### Data Population Differences:
- **Container** has data for cycle 2, report 3 with status='Not Started', state='Complete', progress=100%
- **Standalone** has NO data for cycle 2, report 3 (only has cycles 55 and 58)
- Container shows inconsistent state: status='Not Started' but state='Complete' and progress=100%

#### Column Differences:
Both databases have the same columns but different data organization.

#### Issues Found:
```sql
-- Container has contradictory data:
status = 'Not Started'
state = 'Complete'  
progress_percentage = 100
-- This is logically inconsistent!
```

**FIX NEEDED**: Update workflow phase status management logic to ensure consistency between status, state, and progress fields.

### 🔴 WORKFLOW_ACTIVITIES Table

#### Data Population:
- **Standalone**: No workflow_activities data (0 records)
- **Container**: Has 42 activities with proper metadata, completion timestamps, and completed_by references

#### Key Difference:
Container properly tracks activity execution with:
- `metadata` populated with activity configurations
- `completed_at` timestamps recorded
- `completed_by` user references tracked

**FIX NEEDED**: None - Container implementation is correct.

### 🟡 PLANNING ATTRIBUTES Table

#### Schema Changes:
Container version REMOVED these columns:
- `data_source_id` - **CORRECTION: This exists in PDE mappings table, not lost**
- `source_table` - Not needed in this table per design
- `source_column` - Not needed in this table per design
- `version` - **NEEDS TO BE ADDED BACK**
- `status` - Need clarity on purpose (approval status?)
- `created_by` - **NEEDS TO BE ADDED BACK**
- `updated_by` - **NEEDS TO BE ADDED BACK**

Container version ADDED these columns (BUT SHOULD BE IN SCOPING):
- `llm_rationale` - Already in scoping_attributes table, REMOVE from planning
- `tester_notes` - Keep in planning for now
- `validation_rules` - **MOVE TO SCOPING_ATTRIBUTES**
- `testing_approach` - **MOVE TO SCOPING_ATTRIBUTES**
- `risk_score` - Already in scoping, REMOVE from planning
- `line_item_number` - Keep in planning
- `technical_line_item_name` - Keep in planning
- `mdrm` - Keep in planning
- `typical_source_documents` - **MOVE TO SCOPING_ATTRIBUTES**
- `keywords_to_look_for` - **MOVE TO SCOPING_ATTRIBUTES**

#### Data Population Issues:
1. **Data source linkage EXISTS** - In `cycle_report_planning_pde_mappings` table
2. **Lost versioning** - Cannot track attribute changes over time
3. **Lost audit tracking** - No created_by/updated_by
4. **Misplaced fields** - LLM-generated fields in wrong phase

**FIXES NEEDED**:
```python
# 1. Add version and audit tracking
ALTER TABLE cycle_report_planning_attributes 
ADD COLUMN version INTEGER DEFAULT 1,
ADD COLUMN created_by INTEGER,
ADD COLUMN updated_by INTEGER;

# 2. Remove fields that belong in scoping
ALTER TABLE cycle_report_planning_attributes
DROP COLUMN llm_rationale,
DROP COLUMN validation_rules,
DROP COLUMN testing_approach,
DROP COLUMN risk_score,
DROP COLUMN typical_source_documents,
DROP COLUMN keywords_to_look_for;

# 3. Add missing fields to scoping_attributes
ALTER TABLE cycle_report_scoping_attributes
ADD COLUMN validation_rules TEXT,
ADD COLUMN testing_approach TEXT,
ADD COLUMN typical_source_documents TEXT,
ADD COLUMN keywords_to_look_for TEXT;
```

### ✅ DATA PROFILING RULES Table

#### Schema Changes:
Container version REMOVED:
- `expected_outcome` column - Not needed per design
- `actual_outcome` column - Not needed per design

#### Impact:
None - These columns were not required for the profiling rules functionality.

**FIX NEEDED**: None - removal was intentional.

### ✅ DATA PROFILING RESULTS Table

#### Schema Changes:
Container version REMOVED:
- `error_message` column - Now properly stored in result_details JSON

#### Data Population:
Both versions have the same core columns but organize error information differently.

**FIX NEEDED**: None - error messages are properly captured in result_details JSON.

### 🔴 SAMPLE SELECTION Tables

#### Schema Analysis:
**CORRECTION**: After investigation:
- **Standalone** `cycle_report_sample_selection_versions` HAS `selection_criteria` column (JSONB, NOT NULL)
- **Container** missing this column - **CONFIRMED NEEDED**
- **Standalone** uses `version_status` enum, not `status` column

#### Impact:
- **Standalone** properly tracks selection criteria for each version
- **Container** cannot track the criteria used for sample selection

**FIX NEEDED**:
```python
# Add selection criteria to versions table (critical for audit trail)
ALTER TABLE cycle_report_sample_selection_versions
ADD COLUMN selection_criteria JSONB NOT NULL DEFAULT '{}'::jsonb;
```

### 🔴 CYCLE_REPORT_SCOPING_ATTRIBUTES Table (MISSED IN INITIAL ANALYSIS)

#### Critical Data Population Differences:

##### 1. LLM Rationale Format:
- **Standalone**: Short text format (46-77 chars) - simple descriptions like "Primary key field essential for data integrity"
- **Container**: Long text format (83-95 chars) - detailed business context like "Used in credit risk assessment models and underwriting analysis for regulatory reporting"

##### 2. LLM Request Payload:
- **Standalone**: POPULATED with structured JSON `{"model": "claude-3-5-sonnet-20241022", "temperature": 0.3}`
- **Container**: ALL NULL - **NEEDS TO BE POPULATED**

##### 3. LLM Response Payload:
- **Standalone**: POPULATED (1036 records with payload, 93 without)
- **Container**: Column exists but needs verification if populated correctly

##### 4. Schema Differences:
Container REMOVED:
- `planning_attribute_id` - Intentional change per user request (using attribute_id instead)
- `llm_response_payload` - **CORRECTION: Column exists in container, check if populated**
- `final_status` - Redundant with final_scoping field

Container ADDED:
- `data_quality_score` - new but not populated
- `is_cde`, `has_historical_issues`, `is_primary_key` - **SHOULD NOT BE HERE, use from planning**
- `status` - using enum instead of varchar

**FIXES NEEDED**:
```python
# 1. Populate llm_request_payload in container
UPDATE cycle_report_scoping_attributes
SET llm_request_payload = '{"model": "claude-3-5-sonnet", "temperature": 0.3}'::jsonb
WHERE llm_request_payload IS NULL;

# 2. Remove duplicate fields that should come from planning
ALTER TABLE cycle_report_scoping_attributes
DROP COLUMN is_cde,
DROP COLUMN has_historical_issues,
DROP COLUMN is_primary_key;

# 3. Add fields from planning that belong in scoping
ALTER TABLE cycle_report_scoping_attributes
ADD COLUMN validation_rules TEXT,
ADD COLUMN testing_approach TEXT;
-- Note: typical_source_documents already exists as expected_source_documents
-- Note: keywords_to_look_for already exists as search_keywords
```

### 🟡 SCOPING VERSIONS Table

#### Data Issues:
- **Standalone**: Has data for phase_id=467,476 with proper status tracking (draft, pending_approval, approved, rejected)
- **Container**: Has data for phase_id=14 but missing status columns
- **Standalone** had `version_status` with values: 28 draft, 2 pending_approval, 2 approved, 2 rejected (with rejection_reason populated)
- **Container** uses `version_status` enum but no approval workflow tracking

## Summary of Required Code Fixes

### Priority 1 - Critical Functionality Lost

1. **Fix Workflow Phase State Consistency**
```python
# app/services/workflow_service.py
def update_phase_status(phase_id, new_status):
    # Ensure status, state, and progress are consistent
    if new_status == 'Not Started':
        phase.state = 'Not Started'
        phase.progress_percentage = 0
    elif new_status == 'Complete':
        phase.state = 'Complete'
        phase.progress_percentage = 100
```

2. **Fix Planning and Scoping Attribute Organization**
```python
# app/models/planning.py
class PlanningAttribute(Base):
    # Add versioning and audit fields
    version = Column(Integer, default=1)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    # Remove fields that belong in scoping
    # DROP: llm_rationale, validation_rules, testing_approach, etc.

# app/models/scoping.py  
class ScopingAttribute(Base):
    # Add fields that belong here from planning
    validation_rules = Column(Text)
    testing_approach = Column(Text)
    typical_source_documents = Column(Text)
    keywords_to_look_for = Column(Text)
    # Remove duplicate fields
    # DROP: is_cde, has_historical_issues, is_primary_key
```

3. **Add Sample Selection Criteria Tracking**
```python
# app/models/sample_selection.py
class SampleSelectionSample(Base):
    selection_criteria = Column(JSONB)
    
class SampleSelectionVersion(Base):
    status = Column(String(20), default='draft')
```

### Priority 2 - Data Quality Issues

1. **Calculate Risk Scores**
```python
# app/services/planning_service.py
def calculate_attribute_risk_score(attribute):
    risk_score = 0
    if attribute.is_cde:
        risk_score += 3
    if attribute.data_type in ['Decimal', 'Money']:
        risk_score += 2
    if attribute.is_primary_key:
        risk_score += 1
    attribute.risk_score = risk_score
```

2. **Populate LLM Request Payload**
```python
# app/services/scoping_service.py
def generate_llm_recommendations(attributes):
    for attr in attributes:
        # Ensure we capture the LLM request configuration
        attr.llm_request_payload = {
            "model": "claude-3-5-sonnet",
            "temperature": 0.3,
            "max_tokens": 2000
        }
```

### Priority 3 - Enhanced Tracking

1. **Add Version Tracking**
```python
# app/models/base.py
class VersionedMixin:
    version = Column(Integer, default=1)
    version_notes = Column(Text)
    
    def create_new_version(self):
        self.version += 1
```

2. **Add Approval Workflow**
```python
# app/models/base.py  
class ApprovalMixin:
    approval_status = Column(String(20), default='pending')
    approved_by = Column(Integer, ForeignKey('users.user_id'))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
```

## Testing Requirements

### 1. Data Consistency Tests
```python
def test_workflow_phase_consistency():
    phase = create_phase(status='Not Started')
    assert phase.state == 'Not Started'
    assert phase.progress_percentage == 0
    
def test_planning_attribute_data_source():
    attr = create_attribute(data_source_id=1)
    assert attr.data_source_id is not None
```

### 2. Migration Tests
```python
def test_schema_migration():
    # Verify all required columns exist
    assert 'data_source_id' in PlanningAttribute.__table__.columns
    assert 'selection_criteria' in SampleSelectionSample.__table__.columns
```

## Additional Findings from Re-Analysis

### Data Population Differences Not Initially Caught:

1. **WORKFLOW_PHASES metadata**:
   - **Standalone**: 1 record with metadata populated, 17 without
   - **Container**: ALL records have NULL metadata - This is OK per design

2. **WORKFLOW_ACTIVITIES metadata**:
   - **Standalone**: No activities (different structure)
   - **Container**: ALL 42 activities have metadata populated

3. **SCOPING_ATTRIBUTES llm_request_payload**:
   - **Standalone**: Properly populated with model configuration
   - **Container**: Shows as populated but actually contains "null" values

4. **DATA PROFILING expected/actual outcomes**:
   - These columns don't exist in either database (not needed per user feedback)

## Corrections to Initial Analysis:

1. **Data source linkage is NOT lost** - It exists in `cycle_report_planning_pde_mappings` table
2. **Sample selection criteria** is in the versions table in standalone, not samples table
3. **Many LLM-related fields are in wrong phase** - Should be in Scoping, not Planning
4. **Version tracking already exists** in multiple tables using version_id UUID columns

## Conclusion

Based on user feedback and re-analysis, the container version has the following issues that need to be addressed:

### Critical Issues to Fix:

1. **Misplaced columns** - Multiple LLM-related fields in Planning that belong in Scoping:
   - `validation_rules`, `testing_approach`, `typical_source_documents`, `keywords_to_look_for`
   - These need to be moved to `cycle_report_scoping_attributes`

2. **Duplicate fields** - Scoping attributes duplicating Planning data:
   - `is_cde`, `has_historical_issues`, `is_primary_key` should be removed from scoping
   - These should only exist in planning and be referenced via joins

3. **Missing critical columns**:
   - Planning attributes needs: `version`, `created_by`, `updated_by`
   - Sample selection versions needs: `selection_criteria`

4. **Data not populated**:
   - `llm_request_payload` in scoping attributes is NULL but should have LLM config
   - Workflow phases have inconsistent status/state/progress values

5. **Intentional changes that are OK**:
   - `source_table`, `source_column` removal from planning - not needed
   - `expected_outcome`, `actual_outcome` removal from profiling - not needed
   - `planning_attribute_id` changed to `attribute_id` in scoping - user requested
   - `final_status` removal from scoping - redundant with `final_scoping`

The fixes focus on:
- **Proper phase separation** - Moving fields to their correct phase
- **Removing redundancy** - Eliminating duplicate fields between phases
- **Restoring audit trail** - Adding back version and user tracking
- **Populating required data** - Ensuring LLM config and criteria are captured