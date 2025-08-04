# Scoping Implementation Plan

## 📋 Executive Summary

This document outlines the comprehensive implementation plan for the new simplified Scoping system in SynapseDTE. The plan involves migrating from 11+ legacy tables to a clean 2-table architecture that follows the exact same pattern as sample selection, eliminating redundancy while maintaining all critical functionality for scoping decisions and approval workflows.

## 🎯 Objectives

1. **Simplify Database Architecture**: Reduce from 11+ tables to 2 core tables
2. **Eliminate Redundancy**: Consolidate multiple decision storage approaches
3. **Improve Performance**: Eliminate complex joins and optimize queries
4. **Maintain Functionality**: Preserve all scoping workflow capabilities
5. **Enhance Data Integrity**: Single source of truth for scoping decisions
6. **Reduce Technical Debt**: Simplify codebase and maintenance overhead

## 🏗️ Database Design

### New Tables

#### 1. `cycle_report_scoping_versions`
- **Purpose**: Version management and metadata (same pattern as sample selection)
- **Key Features**: 
  - Version lifecycle management (draft → pending_approval → approved/rejected → superseded)
  - Temporal workflow integration
  - Scoping summary statistics
  - Approval workflow tracking

#### 2. `cycle_report_scoping_attributes`
- **Purpose**: Individual attribute scoping decisions within versions
- **Key Features**:
  - LLM recommendations and tester/report owner decisions
  - Single record per attribute per version
  - Dual decision model (tester + report owner)
  - CDE and historical issue tracking
  - Override handling

### Legacy Tables to be Consolidated
- `cycle_report_scoping_attribute_recommendations` → `cycle_report_scoping_attributes`
- `cycle_report_scoping_decisions` → `cycle_report_scoping_attributes`
- `cycle_report_scoping_submissions` → `cycle_report_scoping_versions`
- `cycle_report_scoping_report_owner_reviews` → `cycle_report_scoping_versions`
- `cycle_report_scoping_decision_versions` → `cycle_report_scoping_attributes`
- `cycle_report_scoping_attribute_recommendation_versions` → `cycle_report_scoping_attributes`
- `scoping_versions` → `cycle_report_scoping_versions`
- `scoping_decisions` → `cycle_report_scoping_attributes`
- All backup tables (after validation)

**Note**: Existing `scoping_audit_log` table will be retained - no new audit table needed

## 📅 Implementation Timeline

### Phase 1: Foundation (Week 1-2)
- [ ] Create database migration scripts
- [ ] Implement new table schemas
- [ ] Create SQLAlchemy models
- [ ] Set up basic unit tests
- [ ] Create data validation utilities

### Phase 2: Data Migration (Week 3-4)
- [ ] Implement data consolidation logic
- [ ] Create migration scripts with rollback capability
- [ ] Test migration on staging environment
- [ ] Validate data integrity post-migration
- [ ] Create backup and restore procedures

### Phase 3: Service Layer (Week 5-6)
- [ ] Implement unified scoping service
- [ ] Create decision management service
- [ ] Build submission workflow service
- [ ] Implement audit logging service
- [ ] Create data access layer

### Phase 4: API Layer (Week 7-8)
- [ ] Update existing API endpoints
- [ ] Create new simplified endpoints
- [ ] Implement request/response schemas
- [ ] Add authentication and authorization
- [ ] Update API documentation

### Phase 5: Frontend Integration (Week 9-10)
- [ ] Update React components
- [ ] Simplify data fetching logic
- [ ] Update state management
- [ ] Implement new UI workflows
- [ ] Update approval interfaces

### Phase 6: Testing & Validation (Week 11-12)
- [ ] Comprehensive testing
- [ ] Performance validation
- [ ] User acceptance testing
- [ ] Bug fixes and optimization
- [ ] Load testing and monitoring

## 🔄 Implementation Details

### Database Migration Strategy

#### Step 1: Create New Tables
```sql
-- Create new unified tables (same pattern as sample selection)
CREATE TABLE cycle_report_scoping_versions (...);
CREATE TABLE cycle_report_scoping_attributes (...);
```

#### Step 2: Complete Schema Definitions
```sql
-- Table 1: Version Management
CREATE TABLE cycle_report_scoping_versions (
    -- Primary Key
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Phase Integration
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id),
    
    -- Version Management (same as sample selection)
    version_number INTEGER NOT NULL,
    version_status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (version_status IN ('draft', 'pending_approval', 'approved', 'rejected', 'superseded')),
    parent_version_id UUID REFERENCES cycle_report_scoping_versions(version_id),
    
    -- Temporal Workflow Context
    workflow_execution_id VARCHAR(255),
    workflow_run_id VARCHAR(255),
    
    -- Scoping Summary
    total_attributes INTEGER DEFAULT 0,
    scoped_attributes INTEGER DEFAULT 0,
    declined_attributes INTEGER DEFAULT 0,
    override_count INTEGER DEFAULT 0,
    cde_count INTEGER DEFAULT 0,
    
    -- Approval Workflow
    submitted_by_id INTEGER REFERENCES users(user_id),
    submitted_at TIMESTAMP WITH TIME ZONE,
    approved_by_id INTEGER REFERENCES users(user_id),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(phase_id, version_number)
);

-- Table 2: Individual Attribute Decisions
CREATE TABLE cycle_report_scoping_attributes (
    -- Primary Key
    attribute_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Version Reference
    version_id UUID NOT NULL REFERENCES cycle_report_scoping_versions(version_id) ON DELETE CASCADE,
    
    -- Phase Integration
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- Attribute Reference
    planning_attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    
    -- LLM Recommendation (embedded)
    llm_recommendation JSONB NOT NULL,
    llm_provider VARCHAR(50),
    llm_confidence_score DECIMAL(5,2),
    llm_rationale TEXT,
    
    -- Tester Decision
    tester_decision VARCHAR(50) CHECK (tester_decision IN ('accept', 'decline', 'override')),
    final_scoping BOOLEAN NOT NULL, -- True = test, False = skip
    tester_rationale TEXT,
    tester_decided_by INTEGER REFERENCES users(user_id),
    tester_decided_at TIMESTAMP WITH TIME ZONE,
    
    -- Report Owner Decision
    report_owner_decision VARCHAR(50) CHECK (report_owner_decision IN ('approved', 'rejected', 'pending', 'needs_revision')),
    report_owner_notes TEXT,
    report_owner_decided_by INTEGER REFERENCES users(user_id),
    report_owner_decided_at TIMESTAMP WITH TIME ZONE,
    
    -- Special Cases
    is_override BOOLEAN DEFAULT FALSE,
    override_reason TEXT,
    is_cde BOOLEAN DEFAULT FALSE,
    has_historical_issues BOOLEAN DEFAULT FALSE,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'submitted', 'approved', 'rejected', 'needs_revision')),
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(version_id, planning_attribute_id)
);

-- Indexes for Performance
CREATE INDEX idx_cycle_report_scoping_versions_phase ON cycle_report_scoping_versions(phase_id);
CREATE INDEX idx_cycle_report_scoping_versions_status ON cycle_report_scoping_versions(version_status);
CREATE INDEX idx_cycle_report_scoping_versions_parent ON cycle_report_scoping_versions(parent_version_id);

CREATE INDEX idx_cycle_report_scoping_attributes_version ON cycle_report_scoping_attributes(version_id);
CREATE INDEX idx_cycle_report_scoping_attributes_phase ON cycle_report_scoping_attributes(phase_id);
CREATE INDEX idx_cycle_report_scoping_attributes_planning_attr ON cycle_report_scoping_attributes(planning_attribute_id);
CREATE INDEX idx_cycle_report_scoping_attributes_status ON cycle_report_scoping_attributes(status);
```

#### Step 3: Data Consolidation
```python
async def migrate_scoping_data():
    """Consolidate data from multiple tables into unified 2-table structure"""
    
    # 1. Create versions from submissions
    async for old_submission in get_submissions():
        old_review = await get_review_for_submission(old_submission.submission_id)
        
        new_version = ScopingVersion(
            phase_id=old_submission.phase_id,
            version_number=old_submission.version,
            version_status='approved' if old_review and old_review.review_decision == 'approved' else 'draft',
            submitted_by_id=old_submission.submitted_by,
            submitted_at=old_submission.submitted_at,
            approved_by_id=old_review.reviewed_by if old_review else None,
            approved_at=old_review.reviewed_at if old_review else None,
            rejection_reason=old_review.review_comments if old_review and old_review.review_decision == 'rejected' else None
        )
        await db.add(new_version)
        await db.flush()  # Get version_id
        
        # 2. Create attributes for this version
        async for old_rec in get_attribute_recommendations_for_phase(old_submission.phase_id):
            old_decision = await get_decision_for_attribute(old_rec.attribute_id)
            
            new_attribute = ScopingAttribute(
                version_id=new_version.version_id,
                phase_id=old_rec.phase_id,
                planning_attribute_id=old_rec.attribute_id,
                llm_recommendation=jsonb_build_object(
                    'recommendation', old_rec.llm_recommendation,
                    'score', old_rec.recommendation_score,
                    'rationale', old_rec.llm_rationale,
                    'confidence', old_rec.llm_confidence_score
                ),
                tester_decision=old_decision.tester_decision if old_decision else None,
                final_scoping=old_decision.final_scoping if old_decision else None,
                report_owner_decision=old_decision.report_owner_decision if old_decision else None,
                is_cde=old_rec.is_cde,
                has_historical_issues=old_rec.has_historical_issues,
                status='approved' if old_decision and old_decision.report_owner_decision == 'approved' else 'pending'
            )
            await db.add(new_attribute)
        
        # Update version summary
        await update_version_summary(new_version.version_id)
    
    await db.commit()
```

#### Step 4: Rename Legacy Tables
```sql
-- Backup existing tables
ALTER TABLE cycle_report_scoping_attribute_recommendations 
RENAME TO cycle_report_scoping_attribute_recommendations_backup;

ALTER TABLE cycle_report_scoping_decisions 
RENAME TO cycle_report_scoping_decisions_backup;

ALTER TABLE cycle_report_scoping_submissions 
RENAME TO cycle_report_scoping_submissions_backup;

ALTER TABLE cycle_report_scoping_report_owner_reviews 
RENAME TO cycle_report_scoping_report_owner_reviews_backup;

ALTER TABLE cycle_report_scoping_decision_versions 
RENAME TO cycle_report_scoping_decision_versions_backup;

ALTER TABLE cycle_report_scoping_attribute_recommendation_versions 
RENAME TO cycle_report_scoping_attribute_recommendation_versions_backup;

ALTER TABLE scoping_versions 
RENAME TO scoping_versions_backup;

ALTER TABLE scoping_decisions 
RENAME TO scoping_decisions_backup;

-- Note: Keep existing scoping_audit_log table (no changes needed)
```

### Model Implementation

#### Scoping Version Model (Same Pattern as Sample Selection)
```python
class ScopingVersion(VersionedEntity):
    __tablename__ = 'cycle_report_scoping_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    workflow_activity_id = Column(Integer, ForeignKey('workflow_activities.activity_id'))
    
    # Version Management (exact same as sample selection)
    version_number = Column(Integer, nullable=False)
    version_status = Column(Enum(VersionStatus), default=VersionStatus.DRAFT)
    parent_version_id = Column(UUID, ForeignKey('cycle_report_scoping_versions.version_id'))
    
    # Temporal Workflow Context
    workflow_execution_id = Column(String(255))
    workflow_run_id = Column(String(255))
    
    # Scoping Summary
    total_attributes = Column(Integer, default=0)
    scoped_attributes = Column(Integer, default=0)
    declined_attributes = Column(Integer, default=0)
    override_count = Column(Integer, default=0)
    cde_count = Column(Integer, default=0)
    
    # Approval Workflow
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'))
    submitted_at = Column(DateTime(timezone=True))
    approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    
    # Relationships
    attributes = relationship("ScopingAttribute", back_populates="version")
    phase = relationship("WorkflowPhase")
    parent_version = relationship("ScopingVersion", remote_side=[version_id])
```

#### Scoping Attribute Model (Same Pattern as Sample Selection)
```python
class ScopingAttribute(CustomPKModel, AuditMixin):
    __tablename__ = 'cycle_report_scoping_attributes'
    
    attribute_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('cycle_report_scoping_versions.version_id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    planning_attribute_id = Column(Integer, ForeignKey('cycle_report_planning_attributes.id'), nullable=False)
    
    # LLM Recommendation (embedded)
    llm_recommendation = Column(JSONB, nullable=False)
    llm_provider = Column(String(50))
    llm_confidence_score = Column(DECIMAL(5,2))
    llm_rationale = Column(Text)
    
    # Tester Decision
    tester_decision = Column(String(50))
    final_scoping = Column(Boolean, nullable=False)
    tester_rationale = Column(Text)
    tester_decided_by = Column(Integer, ForeignKey('users.user_id'))
    tester_decided_at = Column(DateTime(timezone=True))
    
    # Report Owner Decision
    report_owner_decision = Column(String(50))
    report_owner_notes = Column(Text)
    report_owner_decided_by = Column(Integer, ForeignKey('users.user_id'))
    report_owner_decided_at = Column(DateTime(timezone=True))
    
    # Special Cases
    is_override = Column(Boolean, default=False)
    override_reason = Column(Text)
    is_cde = Column(Boolean, default=False)
    has_historical_issues = Column(Boolean, default=False)
    
    # Status
    status = Column(String(50), default='pending')
    
    # Relationships
    version = relationship("ScopingVersion", back_populates="attributes")
    planning_attribute = relationship("PlanningAttribute")
    phase = relationship("WorkflowPhase")
```

### Service Layer Implementation

#### Unified Scoping Service (Same Pattern as Sample Selection)
```python
class ScopingService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_scoping_version(self, phase_id: int, attributes: List[PlanningAttribute]) -> ScopingVersion:
        """Create initial scoping version with LLM recommendations"""
        # Create version
        version = ScopingVersion(
            phase_id=phase_id,
            version_number=1,
            version_status=VersionStatus.DRAFT
        )
        self.db.add(version)
        await self.db.flush()  # Get version_id
        
        # Create attributes with LLM recommendations
        scoping_attributes = []
        for attr in attributes:
            llm_recommendation = await self.llm_service.generate_scoping_recommendation(attr)
            
            scoping_attr = ScopingAttribute(
                version_id=version.version_id,
                phase_id=phase_id,
                planning_attribute_id=attr.id,
                llm_recommendation=llm_recommendation,
                final_scoping=llm_recommendation.get('recommended_action') == 'test',
                is_cde=attr.is_cde,
                has_historical_issues=attr.has_historical_issues,
                status='pending'
            )
            scoping_attributes.append(scoping_attr)
        
        self.db.add_all(scoping_attributes)
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(version.version_id)
        return version
    
    async def update_tester_decision(self, attribute_id: str, decision_data: TesterDecisionRequest) -> ScopingAttribute:
        """Update tester decision on a scoping attribute"""
        attribute = await self.db.get(ScopingAttribute, attribute_id)
        
        attribute.tester_decision = decision_data.tester_decision
        attribute.final_scoping = decision_data.final_scoping
        attribute.tester_rationale = decision_data.rationale
        attribute.tester_decided_by = decision_data.user_id
        attribute.tester_decided_at = datetime.utcnow()
        
        # Check if this is an override
        llm_recommended = attribute.llm_recommendation.get('recommended_action') == 'test'
        if attribute.final_scoping != llm_recommended:
            attribute.is_override = True
            attribute.override_reason = decision_data.override_reason
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(attribute.version_id)
        return attribute
    
    async def submit_for_approval(self, version_id: str, submitted_by: int) -> ScopingVersion:
        """Submit scoping version for report owner approval"""
        version = await self.db.get(ScopingVersion, version_id)
        
        version.version_status = VersionStatus.PENDING_APPROVAL
        version.submitted_by_id = submitted_by
        version.submitted_at = datetime.utcnow()
        
        # Update all attributes to submitted status
        await self.db.execute(
            update(ScopingAttribute)
            .where(ScopingAttribute.version_id == version_id)
            .values(status='submitted')
        )
        
        await self.db.commit()
        return version
    
    async def approve_version(self, version_id: str, approved_by: int) -> ScopingVersion:
        """Approve scoping version (report owner action)"""
        version = await self.db.get(ScopingVersion, version_id)
        
        # Mark previous versions as superseded
        await self.db.execute(
            update(ScopingVersion)
            .where(ScopingVersion.phase_id == version.phase_id)
            .where(ScopingVersion.version_status == VersionStatus.APPROVED)
            .values(version_status=VersionStatus.SUPERSEDED)
        )
        
        # Approve current version
        version.version_status = VersionStatus.APPROVED
        version.approved_by_id = approved_by
        version.approved_at = datetime.utcnow()
        
        # Update all attributes to approved status
        await self.db.execute(
            update(ScopingAttribute)
            .where(ScopingAttribute.version_id == version_id)
            .values(status='approved')
        )
        
        await self.db.commit()
        return version
    
    async def reject_version(self, version_id: str, rejected_by: int, reason: str) -> ScopingVersion:
        """Reject scoping version (report owner action)"""
        version = await self.db.get(ScopingVersion, version_id)
        
        version.version_status = VersionStatus.REJECTED
        version.rejection_reason = reason
        version.approved_by_id = rejected_by  # Track who rejected
        version.approved_at = datetime.utcnow()
        
        # Update all attributes to rejected status
        await self.db.execute(
            update(ScopingAttribute)
            .where(ScopingAttribute.version_id == version_id)
            .values(status='rejected')
        )
        
        await self.db.commit()
        return version
    
    async def create_revision(self, parent_version_id: str, created_by: int) -> ScopingVersion:
        """Create new version based on previous version (for revisions)"""
        parent_version = await self.db.get(ScopingVersion, parent_version_id)
        
        # Get next version number
        next_version = parent_version.version_number + 1
        
        # Create new version
        new_version = ScopingVersion(
            phase_id=parent_version.phase_id,
            version_number=next_version,
            version_status=VersionStatus.DRAFT,
            parent_version_id=parent_version_id,
            created_by_id=created_by
        )
        self.db.add(new_version)
        await self.db.flush()
        
        # Copy attributes from parent version
        parent_attributes = await self.db.execute(
            select(ScopingAttribute)
            .where(ScopingAttribute.version_id == parent_version_id)
        )
        
        for parent_attr in parent_attributes.scalars():
            new_attr = ScopingAttribute(
                version_id=new_version.version_id,
                phase_id=parent_attr.phase_id,
                planning_attribute_id=parent_attr.planning_attribute_id,
                llm_recommendation=parent_attr.llm_recommendation,
                llm_provider=parent_attr.llm_provider,
                llm_confidence_score=parent_attr.llm_confidence_score,
                llm_rationale=parent_attr.llm_rationale,
                tester_decision=parent_attr.tester_decision,
                final_scoping=parent_attr.final_scoping,
                tester_rationale=parent_attr.tester_rationale,
                is_cde=parent_attr.is_cde,
                has_historical_issues=parent_attr.has_historical_issues,
                status='pending'
            )
            self.db.add(new_attr)
        
        await self.db.commit()
        await self.update_version_summary(new_version.version_id)
        return new_version
    
    async def update_version_summary(self, version_id: str):
        """Update version summary statistics"""
        attributes = await self.db.execute(
            select(ScopingAttribute)
            .where(ScopingAttribute.version_id == version_id)
        )
        attributes = attributes.scalars().all()
        
        version = await self.db.get(ScopingVersion, version_id)
        version.total_attributes = len(attributes)
        version.scoped_attributes = sum(1 for attr in attributes if attr.final_scoping)
        version.declined_attributes = sum(1 for attr in attributes if not attr.final_scoping)
        version.override_count = sum(1 for attr in attributes if attr.is_override)
        version.cde_count = sum(1 for attr in attributes if attr.is_cde)
        
        await self.db.commit()
```

### API Endpoints

#### Scoping Version Management (Same Pattern as Sample Selection)
```python
@router.post("/scoping/versions", response_model=ScopingVersionResponse)
async def create_scoping_version(
    request: CreateScopingVersionRequest,
    service: ScopingService = Depends()
):
    """Create initial scoping version with LLM recommendations"""
    return await service.create_scoping_version(request.phase_id, request.attributes)

@router.get("/scoping/versions/{version_id}", response_model=ScopingVersionResponse)
async def get_scoping_version(
    version_id: str,
    service: ScopingService = Depends()
):
    """Get specific scoping version with all attributes"""
    return await service.get_scoping_version(version_id)

@router.post("/scoping/versions/{version_id}/submit", response_model=ScopingVersionResponse)
async def submit_version_for_approval(
    version_id: str,
    service: ScopingService = Depends(),
    current_user: User = Depends()
):
    """Submit scoping version for report owner approval"""
    return await service.submit_for_approval(version_id, current_user.user_id)

@router.post("/scoping/versions/{version_id}/approve", response_model=ScopingVersionResponse)
async def approve_version(
    version_id: str,
    service: ScopingService = Depends(),
    current_user: User = Depends()
):
    """Approve scoping version (report owner action)"""
    return await service.approve_version(version_id, current_user.user_id)

@router.post("/scoping/versions/{version_id}/reject", response_model=ScopingVersionResponse)
async def reject_version(
    version_id: str,
    request: RejectVersionRequest,
    service: ScopingService = Depends(),
    current_user: User = Depends()
):
    """Reject scoping version (report owner action)"""
    return await service.reject_version(version_id, current_user.user_id, request.reason)

@router.post("/scoping/versions/{parent_version_id}/revise", response_model=ScopingVersionResponse)
async def create_revision(
    parent_version_id: str,
    service: ScopingService = Depends(),
    current_user: User = Depends()
):
    """Create new version based on previous version (for revisions)"""
    return await service.create_revision(parent_version_id, current_user.user_id)

#### Scoping Attribute Management
@router.put("/scoping/attributes/{attribute_id}", response_model=ScopingAttributeResponse)
async def update_tester_decision(
    attribute_id: str,
    request: TesterDecisionRequest,
    service: ScopingService = Depends()
):
    """Update tester decision on a scoping attribute"""
    return await service.update_tester_decision(attribute_id, request)

@router.get("/scoping/attributes/{version_id}", response_model=List[ScopingAttributeResponse])
async def get_scoping_attributes(
    version_id: str,
    service: ScopingService = Depends()
):
    """Get all scoping attributes for a version"""
    return await service.get_scoping_attributes(version_id)

@router.get("/scoping/phases/{phase_id}/current", response_model=ScopingVersionResponse)
async def get_current_scoping_version(
    phase_id: int,
    service: ScopingService = Depends()
):
    """Get current approved scoping version for a phase"""
    return await service.get_current_version(phase_id)

@router.get("/scoping/phases/{phase_id}/history", response_model=List[ScopingVersionResponse])
async def get_scoping_version_history(
    phase_id: int,
    service: ScopingService = Depends()
):
    """Get all historical versions for a phase"""
    return await service.get_version_history(phase_id)
```

## 🧪 Testing Strategy

### Unit Tests
- [ ] Model validation and relationship tests
- [ ] Service layer functionality tests  
- [ ] API endpoint tests
- [ ] Data migration validation tests
- [ ] Performance benchmark tests

### Integration Tests
- [ ] End-to-end scoping workflow tests
- [ ] Submission and approval process tests
- [ ] Version management tests
- [ ] Audit logging integration tests
- [ ] LLM recommendation integration tests

### Performance Tests
- [ ] Query performance with large datasets
- [ ] Concurrent user access tests
- [ ] Database indexing effectiveness
- [ ] Memory usage optimization tests

### Test Data Sets
```python
@pytest.fixture
def scoping_test_data():
    return {
        "attributes": [
            {"id": 1, "name": "customer_id", "is_primary_key": True},
            {"id": 2, "name": "customer_name", "is_cde": True},
            {"id": 3, "name": "account_balance", "has_historical_issues": True}
        ],
        "llm_recommendations": [
            {"attribute_id": 1, "recommendation": "test", "score": 0.95, "rationale": "Primary key"},
            {"attribute_id": 2, "recommendation": "test", "score": 0.88, "rationale": "CDE field"},
            {"attribute_id": 3, "recommendation": "test", "score": 0.92, "rationale": "Historical issues"}
        ],
        "tester_decisions": [
            {"decision_id": 1, "tester_decision": "accept", "final_scoping": True},
            {"decision_id": 2, "tester_decision": "override", "final_scoping": False},
            {"decision_id": 3, "tester_decision": "accept", "final_scoping": True}
        ]
    }
```

## 🚀 Deployment Strategy

### Pre-Deployment Checklist
- [ ] Database migration scripts tested on staging
- [ ] Data integrity validation scripts ready
- [ ] Backup and rollback procedures documented
- [ ] Performance benchmarks established
- [ ] User training materials prepared
- [ ] Monitoring and alerting configured

### Deployment Steps
1. **Maintenance Window**: Schedule 3-hour maintenance window
2. **Backup**: Complete backup of existing scoping data
3. **Migration**: Execute data consolidation migration
4. **Validation**: Run data integrity checks
5. **Deployment**: Deploy new application code
6. **Testing**: Execute smoke tests
7. **Monitoring**: Enable monitoring and alerting
8. **Go-Live**: Enable new scoping functionality

### Rollback Plan
```python
async def rollback_scoping_migration():
    """Rollback scoping migration if issues occur"""
    # 1. Restore backup tables
    await restore_backup_tables([
        'cycle_report_scoping_attribute_recommendations',
        'cycle_report_scoping_decisions',
        'cycle_report_scoping_submissions',
        'cycle_report_scoping_report_owner_reviews'
    ])
    
    # 2. Update application configuration
    await update_config(use_legacy_scoping_tables=True)
    
    # 3. Restart application services
    await restart_services(['api', 'workers'])
    
    # 4. Validate rollback success
    await validate_rollback()
```

## 📊 Success Metrics

### Technical Metrics
- [ ] Database query performance improvement (target: 60% faster)
- [ ] Storage space reduction (target: 40% less space)
- [ ] Code complexity reduction (target: 50% fewer lines)
- [ ] Migration success rate (target: 100% data integrity)

### Business Metrics
- [ ] User adoption rate (target: 90% within 2 weeks)
- [ ] Scoping workflow efficiency (target: 30% faster completion)
- [ ] Error rate reduction (target: 50% fewer support tickets)
- [ ] System reliability (target: 99.9% uptime)

## 🔐 Security Considerations

### Data Protection
- [ ] Encryption at rest for scoping decisions
- [ ] Access control validation for all endpoints
- [ ] Audit logging for all scoping actions
- [ ] Data retention policy compliance

### Privacy
- [ ] Sensitive data handling in scoping decisions
- [ ] User permission validation
- [ ] Data anonymization where required
- [ ] Compliance with data protection regulations

## 📚 Documentation Updates

### Technical Documentation
- [ ] API documentation updates
- [ ] Database schema documentation
- [ ] Migration guide documentation
- [ ] Troubleshooting guide updates

### User Documentation
- [ ] User guide updates for new interface
- [ ] Training materials for simplified workflow
- [ ] FAQ updates for common questions
- [ ] Video tutorials for new features

## 🎯 Risk Mitigation

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data migration failure | Medium | High | Comprehensive testing, staging migration |
| Performance degradation | Low | Medium | Performance testing, query optimization |
| Integration issues | Medium | Medium | Thorough integration testing |
| Data inconsistency | Low | High | Validation scripts, integrity checks |

### Business Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| User resistance | Low | Medium | Training, change management |
| Workflow disruption | Medium | High | Parallel testing, staged rollout |
| Compliance issues | Low | High | Audit trail validation, legal review |

## 🔄 Post-Implementation

### Monitoring
- [ ] Database performance monitoring
- [ ] Application error tracking
- [ ] User behavior analytics
- [ ] System health dashboards

### Optimization
- [ ] Query performance optimization
- [ ] Index tuning based on usage patterns
- [ ] Cache implementation where beneficial
- [ ] Database maintenance procedures

### Continuous Improvement
- [ ] User feedback collection and analysis
- [ ] Performance metrics analysis
- [ ] Feature enhancement planning
- [ ] Technical debt reduction initiatives

## 📞 Support Plan

### Go-Live Support
- [ ] 24/7 support team availability
- [ ] Escalation procedures documented
- [ ] Hot-fix deployment process ready
- [ ] Communication plan for issues

### Training
- [ ] Administrator training sessions
- [ ] End-user training materials
- [ ] Support team knowledge transfer
- [ ] Documentation review sessions

---

## 📝 Approval Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Technical Lead | | | |
| Product Owner | | | |
| Database Administrator | | | |
| QA Lead | | | |
| DevOps Lead | | | |
| Compliance Officer | | | |

---

*This implementation plan serves as a comprehensive guide for the Scoping system consolidation. The plan focuses on reducing complexity while maintaining all critical functionality and ensuring data integrity throughout the migration process.*