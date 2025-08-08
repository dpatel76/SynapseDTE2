# Implementation Plan: Data Structure Fixes
## Based on Data Population Analysis
## Date: 2025-08-07

## Overview
This implementation plan provides specific actions to fix the data structure and population issues identified in the container database.

## Priority 1: Critical Schema Fixes

### 1.1 Fix Planning Attributes Table

#### Migration: Add Missing Audit Columns
```python
# alembic/versions/2025_08_07_fix_planning_attributes.py
"""Add version and audit tracking to planning attributes

Revision ID: fix_planning_attrs_001
Revises: <current_head>
Create Date: 2025-08-07
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add version and audit tracking
    op.add_column('cycle_report_planning_attributes',
                  sa.Column('version', sa.Integer(), default=1))
    op.add_column('cycle_report_planning_attributes',
                  sa.Column('created_by', sa.Integer()))
    op.add_column('cycle_report_planning_attributes',
                  sa.Column('updated_by', sa.Integer()))
    
    # Remove fields that belong in scoping
    op.drop_column('cycle_report_planning_attributes', 'llm_rationale')
    op.drop_column('cycle_report_planning_attributes', 'validation_rules')
    op.drop_column('cycle_report_planning_attributes', 'testing_approach')
    op.drop_column('cycle_report_planning_attributes', 'risk_score')
    op.drop_column('cycle_report_planning_attributes', 'typical_source_documents')
    op.drop_column('cycle_report_planning_attributes', 'keywords_to_look_for')

def downgrade():
    # Reverse the changes
    pass
```

### 1.2 Fix Scoping Attributes Table

#### Migration: Reorganize Scoping Fields
```python
# alembic/versions/2025_08_07_fix_scoping_attributes.py
"""Fix scoping attributes organization

Revision ID: fix_scoping_attrs_001
Revises: fix_planning_attrs_001
Create Date: 2025-08-07
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Remove duplicate fields that exist in planning
    op.drop_column('cycle_report_scoping_attributes', 'is_cde')
    op.drop_column('cycle_report_scoping_attributes', 'has_historical_issues')
    op.drop_column('cycle_report_scoping_attributes', 'is_primary_key')
    
    # Add fields from planning that belong here
    op.add_column('cycle_report_scoping_attributes',
                  sa.Column('validation_rules', sa.Text()))
    op.add_column('cycle_report_scoping_attributes',
                  sa.Column('testing_approach', sa.Text()))
    # Note: expected_source_documents and search_keywords already exist

def downgrade():
    pass
```

### 1.3 Fix Sample Selection Versions Table

#### Migration: Add Selection Criteria
```python
# alembic/versions/2025_08_07_fix_sample_selection.py
"""Add selection criteria to sample selection versions

Revision ID: fix_sample_selection_001
Revises: fix_scoping_attrs_001
Create Date: 2025-08-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Add selection criteria for audit trail
    op.add_column('cycle_report_sample_selection_versions',
                  sa.Column('selection_criteria', postgresql.JSONB(), 
                           nullable=False, server_default='{}'))

def downgrade():
    op.drop_column('cycle_report_sample_selection_versions', 'selection_criteria')
```

## Priority 2: Data Population Fixes

### 2.1 Fix Workflow Phase Inconsistencies

#### Script: Fix Workflow Phase Status Consistency
```python
# scripts/fix_workflow_phase_status.py
"""Fix inconsistent workflow phase status/state/progress values"""

import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import update
from app.models.workflow import WorkflowPhase

async def fix_workflow_phase_status():
    async with AsyncSessionLocal() as db:
        # Fix phases with inconsistent status
        await db.execute(
            update(WorkflowPhase)
            .where(WorkflowPhase.status == 'Not Started')
            .where(WorkflowPhase.state == 'Complete')
            .values(
                state='Not Started',
                progress_percentage=0
            )
        )
        
        # Fix completed phases
        await db.execute(
            update(WorkflowPhase)
            .where(WorkflowPhase.progress_percentage == 100)
            .where(WorkflowPhase.status != 'Complete')
            .values(
                status='Complete',
                state='Complete'
            )
        )
        
        await db.commit()
        print("✅ Fixed workflow phase status inconsistencies")

if __name__ == "__main__":
    asyncio.run(fix_workflow_phase_status())
```

### 2.2 Populate LLM Request Payload

#### Update Scoping Service
```python
# app/services/scoping_service.py
# Update the generate_llm_recommendations method

async def generate_llm_recommendations(self, version_id: str):
    """Generate LLM recommendations for scoping"""
    
    # ... existing code ...
    
    for attribute in attributes:
        # Capture LLM request configuration
        llm_request_payload = {
            "model": self.llm_model,
            "temperature": 0.3,
            "max_tokens": 2000,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Generate recommendation
        recommendation = await self._call_llm(attribute, llm_request_payload)
        
        # Save with request payload
        scoping_attr = ScopingAttribute(
            version_id=version_id,
            attribute_id=attribute.id,
            llm_recommendation=recommendation,
            llm_request_payload=llm_request_payload,  # Now properly saved
            llm_rationale=recommendation.get('rationale'),
            # ... other fields ...
        )
        
        db.add(scoping_attr)
```

### 2.3 Data Migration Script

#### Script: Migrate Existing Data
```python
# scripts/migrate_scoping_data.py
"""Migrate data from planning to scoping where appropriate"""

import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, update
from app.models.planning import PlanningAttribute
from app.models.scoping import ScopingAttribute

async def migrate_fields_to_scoping():
    async with AsyncSessionLocal() as db:
        # Get planning attributes with LLM fields
        result = await db.execute(
            select(PlanningAttribute)
            .where(PlanningAttribute.validation_rules.isnot(None))
        )
        planning_attrs = result.scalars().all()
        
        for p_attr in planning_attrs:
            # Find corresponding scoping attribute
            result = await db.execute(
                select(ScopingAttribute)
                .where(ScopingAttribute.attribute_id == p_attr.id)
            )
            s_attr = result.scalar_one_or_none()
            
            if s_attr:
                # Move fields from planning to scoping
                s_attr.validation_rules = p_attr.validation_rules
                s_attr.testing_approach = p_attr.testing_approach
                # expected_source_documents maps to typical_source_documents
                s_attr.expected_source_documents = p_attr.typical_source_documents
                # search_keywords maps to keywords_to_look_for
                s_attr.search_keywords = p_attr.keywords_to_look_for
                
                # Populate missing llm_request_payload
                if not s_attr.llm_request_payload:
                    s_attr.llm_request_payload = {
                        "model": "claude-3-5-sonnet",
                        "temperature": 0.3,
                        "migrated": True
                    }
        
        await db.commit()
        print("✅ Migrated fields from planning to scoping")

if __name__ == "__main__":
    asyncio.run(migrate_fields_to_scoping())
```

## Priority 3: Model Updates

### 3.1 Update Planning Model
```python
# app/models/planning.py

class PlanningAttribute(Base):
    __tablename__ = "cycle_report_planning_attributes"
    
    # Core fields
    id = Column(Integer, primary_key=True)
    phase_id = Column(Integer, ForeignKey("workflow_phases.phase_id"))
    attribute_name = Column(String(255), nullable=False)
    description = Column(Text)
    data_type = Column(Enum(DataTypeEnum))
    
    # Audit fields (ADDED)
    version = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey("users.user_id"))
    updated_by = Column(Integer, ForeignKey("users.user_id"))
    
    # Planning-specific fields (KEEP)
    line_item_number = Column(String(20))
    technical_line_item_name = Column(String(255))
    mdrm = Column(String(50))
    tester_notes = Column(Text)
    
    # Classification fields
    is_cde = Column(Boolean, default=False)
    has_issues = Column(Boolean, default=False)
    is_primary_key = Column(Boolean, default=False)
    information_security_classification = Column(Enum(SecurityClassificationEnum))
    
    # REMOVED: llm_rationale, validation_rules, testing_approach, 
    #          risk_score, typical_source_documents, keywords_to_look_for
```

### 3.2 Update Scoping Model
```python
# app/models/scoping.py

class ScopingAttribute(Base):
    __tablename__ = "cycle_report_scoping_attributes"
    
    # Core fields
    version_id = Column(UUID, ForeignKey("cycle_report_scoping_versions.version_id"))
    phase_id = Column(Integer, ForeignKey("workflow_phases.phase_id"))
    attribute_id = Column(Integer, ForeignKey("cycle_report_planning_attributes.id"))
    
    # LLM fields
    llm_recommendation = Column(JSONB, nullable=False)
    llm_request_payload = Column(JSONB)  # Must be populated
    llm_rationale = Column(Text)
    llm_confidence_score = Column(Numeric(5, 2))
    
    # Scoping-specific fields (ADDED from planning)
    validation_rules = Column(Text)
    testing_approach = Column(Text)
    expected_source_documents = Column(Text)  # was typical_source_documents
    search_keywords = Column(Text)  # was keywords_to_look_for
    
    # Decision fields
    tester_decision = Column(Enum(ScopingTesterDecisionEnum))
    tester_rationale = Column(Text)
    report_owner_decision = Column(Enum(ScopingReportOwnerDecisionEnum))
    report_owner_notes = Column(Text)
    
    # Status fields
    final_scoping = Column(Boolean)
    is_override = Column(Boolean, default=False)
    
    # REMOVED: is_cde, has_historical_issues, is_primary_key (use from planning via join)
```

## Testing Plan

### 1. Schema Validation Tests
```python
# tests/test_schema_fixes.py

def test_planning_attributes_schema():
    """Verify planning attributes has correct columns"""
    assert 'version' in PlanningAttribute.__table__.columns
    assert 'created_by' in PlanningAttribute.__table__.columns
    assert 'llm_rationale' not in PlanningAttribute.__table__.columns
    
def test_scoping_attributes_schema():
    """Verify scoping attributes has correct columns"""
    assert 'validation_rules' in ScopingAttribute.__table__.columns
    assert 'is_cde' not in ScopingAttribute.__table__.columns
```

### 2. Data Population Tests
```python
# tests/test_data_population.py

async def test_llm_request_payload_populated():
    """Verify LLM request payload is populated"""
    scoping_attrs = await db.query(ScopingAttribute).all()
    for attr in scoping_attrs:
        assert attr.llm_request_payload is not None
        assert 'model' in attr.llm_request_payload

async def test_workflow_phase_consistency():
    """Verify workflow phases have consistent status"""
    phases = await db.query(WorkflowPhase).all()
    for phase in phases:
        if phase.status == 'Not Started':
            assert phase.progress_percentage == 0
        if phase.progress_percentage == 100:
            assert phase.status == 'Complete'
```

## Rollout Plan

### Week 1: Schema Changes
1. **Day 1-2**: Create and test migrations locally
2. **Day 3**: Deploy to staging environment
3. **Day 4-5**: Run data migration scripts in staging

### Week 2: Code Updates
1. **Day 1-2**: Update models and services
2. **Day 3**: Update API endpoints
3. **Day 4-5**: Testing and validation

### Week 3: Production Deployment
1. **Day 1**: Backup production database
2. **Day 2**: Deploy schema migrations
3. **Day 3**: Run data migration scripts
4. **Day 4-5**: Monitor and validate

## Success Criteria

- [ ] All planning attributes have version, created_by, updated_by columns
- [ ] No LLM fields remain in planning attributes table
- [ ] All scoping attributes have validation_rules and testing_approach
- [ ] No duplicate fields (is_cde, etc.) in scoping attributes
- [ ] Sample selection versions have selection_criteria column
- [ ] All scoping attributes have populated llm_request_payload
- [ ] All workflow phases have consistent status/state/progress
- [ ] All tests pass
- [ ] No data loss during migration

## Monitoring

### Post-Deployment Checks
```sql
-- Check planning attributes
SELECT COUNT(*) FROM cycle_report_planning_attributes 
WHERE version IS NULL OR created_by IS NULL;

-- Check scoping attributes
SELECT COUNT(*) FROM cycle_report_scoping_attributes 
WHERE llm_request_payload IS NULL;

-- Check workflow phase consistency
SELECT * FROM workflow_phases 
WHERE (status = 'Not Started' AND progress_percentage > 0)
   OR (progress_percentage = 100 AND status != 'Complete');
```