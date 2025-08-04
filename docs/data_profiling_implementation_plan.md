# Data Profiling Implementation Plan

## 📋 Executive Summary

This document outlines the comprehensive implementation plan for the new simplified Data Profiling system in SynapseDTE. The plan involves migrating from 23+ legacy tables to a clean 2-table architecture that follows the exact same pattern as sample selection and scoping, eliminating massive redundancy while maintaining all critical functionality for data quality assessment and LLM-driven rule generation.

## 🎯 Objectives

1. **Simplify Database Architecture**: Reduce from 23+ tables to 2 core tables
2. **Eliminate Redundancy**: Consolidate multiple overlapping profiling systems
3. **Improve Performance**: Eliminate complex joins and optimize queries
4. **Maintain Functionality**: Preserve all data profiling capabilities
5. **Ensure Consistency**: Follow exact same patterns as sample selection/scoping
6. **Reduce Technical Debt**: Simplify codebase and maintenance overhead

## 🏗️ Database Design

### New Tables

#### 1. `cycle_report_data_profiling_rule_versions`
- **Purpose**: Rule version management and metadata (same pattern as sample selection/scoping)
- **Key Features**: 
  - Version lifecycle management (draft → pending_approval → approved/rejected → superseded)
  - Temporal workflow integration
  - Reference to planning phase data sources
  - Rule set summary statistics
  - Approval workflow tracking

#### 2. `cycle_report_data_profiling_rules`
- **Purpose**: Individual profiling rules with decisions (NO execution results)
- **Key Features**:
  - LLM-generated rules with metadata
  - Dual decision model (tester + report owner)
  - Rule definitions and parameters only
  - No execution results (tracked separately via background jobs)
  - Single record per rule per version

### Legacy Tables to be Consolidated
- `cycle_report_data_profiling_files` → eliminated (use planning phase files)
- `cycle_report_data_profiling_rules` → `cycle_report_data_profiling_rules` (enhanced)
- `cycle_report_data_profiling_results` → eliminated (use background job system)
- `cycle_report_data_profiling_configurations` → `cycle_report_data_profiling_rule_versions` (metadata)
- `cycle_report_data_profiling_jobs` → eliminated (use universal background job system)
- `cycle_report_attribute_profile_results` → eliminated (use background job system)
- `cycle_report_anomaly_patterns_data_profiling` → eliminated (use background job system)
- `profiling_jobs` → eliminated (use universal background job system)
- `profiling_partitions` → eliminated (use universal background job system)
- `profiling_rule_sets` → `cycle_report_data_profiling_rule_versions` (metadata)
- `partition_results` → eliminated (use background job system)
- `profiling_anomaly_patterns` → eliminated (use background job system)
- `profiling_cache` → eliminated (handled by application layer)
- `profiling_executions` → eliminated (use universal background job system)
- `intelligent_sampling_jobs` → eliminated (separate concern)
- `sample_pools` → eliminated (separate concern)
- `intelligent_samples` → eliminated (separate concern)
- `sampling_rules` → eliminated (separate concern)
- `sample_lineage` → eliminated (separate concern)
- `secure_data_access_logs` → retained (security requirement)
- `cycle_report_data_profiling_rule_versions` → `cycle_report_data_profiling_rule_versions` (consolidated)
- `cycle_report_data_profiling_attribute_scores` → eliminated (deprecated)
- `data_profiling_phases` → eliminated (deprecated)

**Note**: 
- No new audit table needed - existing audit infrastructure will be leveraged
- Execution results tracked via existing universal background job system
- Files referenced from planning phase (no duplication)

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
- [ ] Implement unified data profiling service
- [ ] Create rule management service
- [ ] Build execution workflow service
- [ ] Implement LLM integration service
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

### Database Schema

#### Complete Schema Definitions
```sql
-- Table 1: Rule Version Management
CREATE TABLE cycle_report_data_profiling_rule_versions (
    -- Primary Key
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Phase Integration (only phase_id needed)
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id),
    
    -- Version Management (exact same as sample selection/scoping)
    version_number INTEGER NOT NULL,
    version_status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (version_status IN ('draft', 'pending_approval', 'approved', 'rejected', 'superseded')),
    parent_version_id UUID REFERENCES cycle_report_data_profiling_rule_versions(version_id),
    
    -- Temporal Workflow Context
    workflow_execution_id VARCHAR(255),
    workflow_run_id VARCHAR(255),
    
    -- Rule Set Summary
    total_rules INTEGER DEFAULT 0,
    approved_rules INTEGER DEFAULT 0,
    rejected_rules INTEGER DEFAULT 0,
    
    -- Data Source Reference (from planning phase)
    data_source_type VARCHAR(50) CHECK (data_source_type IN ('file_upload', 'database_source')),
    planning_data_source_id INTEGER, -- References planning phase data source
    
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

-- Table 2: Individual Rules (NO execution results)
CREATE TABLE cycle_report_data_profiling_rules (
    -- Primary Key
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Version Reference
    version_id UUID NOT NULL REFERENCES cycle_report_data_profiling_rule_versions(version_id) ON DELETE CASCADE,
    
    -- Phase Integration
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- Attribute Reference
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
    
    -- Rule Definition (NO execution results here)
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('completeness', 'validity', 'accuracy', 'consistency', 'uniqueness')),
    rule_description TEXT,
    rule_code TEXT NOT NULL,
    rule_parameters JSONB,
    
    -- LLM Metadata
    llm_provider VARCHAR(50),
    llm_rationale TEXT,
    llm_confidence_score DECIMAL(5,2),
    regulatory_reference TEXT,
    
    -- Rule Configuration
    is_executable BOOLEAN DEFAULT TRUE,
    execution_order INTEGER DEFAULT 0,
    severity VARCHAR(50) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high')),
    
    -- Dual Decision Model (same as scoping)
    tester_decision VARCHAR(50) CHECK (tester_decision IN ('approve', 'reject', 'request_changes')),
    tester_decided_by INTEGER REFERENCES users(user_id),
    tester_decided_at TIMESTAMP WITH TIME ZONE,
    tester_notes TEXT,
    
    report_owner_decision VARCHAR(50) CHECK (report_owner_decision IN ('approve', 'reject', 'request_changes')),
    report_owner_decided_by INTEGER REFERENCES users(user_id),
    report_owner_decided_at TIMESTAMP WITH TIME ZONE,
    report_owner_notes TEXT,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'submitted', 'approved', 'rejected')),
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(version_id, attribute_id, rule_name)
);

-- Indexes for Performance
CREATE INDEX idx_cycle_report_data_profiling_rule_versions_phase ON cycle_report_data_profiling_rule_versions(phase_id);
CREATE INDEX idx_cycle_report_data_profiling_rule_versions_status ON cycle_report_data_profiling_rule_versions(version_status);
CREATE INDEX idx_cycle_report_data_profiling_rule_versions_parent ON cycle_report_data_profiling_rule_versions(parent_version_id);

CREATE INDEX idx_cycle_report_data_profiling_rules_version ON cycle_report_data_profiling_rules(version_id);
CREATE INDEX idx_cycle_report_data_profiling_rules_phase ON cycle_report_data_profiling_rules(phase_id);
CREATE INDEX idx_cycle_report_data_profiling_rules_attribute ON cycle_report_data_profiling_rules(attribute_id);
CREATE INDEX idx_cycle_report_data_profiling_rules_status ON cycle_report_data_profiling_rules(status);
```

#### Execution Results Tracking (Via Background Jobs)
```python
# Execution results are tracked via the existing universal background job system
# When rules are executed, a background job is created:

job_id = await background_job_manager.create_job(
    job_type="data_profiling_execution",
    job_name=f"Execute Rules for Version {version_id}",
    metadata={
        "version_id": version_id,
        "rule_count": len(rules),
        "phase_id": phase_id
    }
)

# Results are stored in the job's metadata:
await background_job_manager.update_job_progress(
    job_id=job_id,
    progress=100,
    status="COMPLETED",
    metadata={
        "execution_results": {
            "rule_id_1": {
                "passed_records": 1000,
                "failed_records": 50,
                "pass_rate": 95.2,
                "quality_scores": {...},
                "anomaly_details": {...}
            }
        }
    }
)
```

#### Optional: Persistent Execution Results Table (if needed)
```sql
-- Only if persistent execution result storage is required
CREATE TABLE cycle_report_data_profiling_rule_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES cycle_report_data_profiling_rules(rule_id),
    background_job_id VARCHAR(255), -- Reference to universal background job
    
    -- Execution Results
    execution_status VARCHAR(50) NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms INTEGER,
    total_records_tested INTEGER,
    passed_records INTEGER,
    failed_records INTEGER,
    pass_rate DECIMAL(5,2),
    
    -- Quality Scores
    quality_scores JSONB,
    result_summary JSONB,
    anomaly_details JSONB,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id)
);
```

### Data Consolidation Strategy
```python
async def migrate_data_profiling_data():
    """Consolidate data from 23+ tables into unified 2-table structure"""
    
    # 1. Create versions from profiling jobs and configurations
    async for old_job in get_profiling_jobs():
        old_config = await get_profiling_configuration(old_job.job_id)
        
        new_version = DataProfilingVersion(
            phase_id=old_job.phase_id,
            version_number=1,  # Start fresh
            version_status='approved' if old_job.status == 'completed' else 'draft',
            data_source_type=old_config.source_type if old_config else 'database_source',
            source_table_name=old_config.table_name if old_config else None,
            total_records_processed=old_job.records_processed,
            overall_quality_score=old_job.quality_score,
            submitted_by_id=old_job.created_by,
            submitted_at=old_job.created_at
        )
        await db.add(new_version)
        await db.flush()  # Get version_id
        
        # 2. Create rules for this version
        async for old_rule in get_rules_for_job(old_job.job_id):
            old_result = await get_result_for_rule(old_rule.rule_id)
            old_profile = await get_profile_for_attribute(old_rule.attribute_id)
            
            new_rule = DataProfilingRule(
                version_id=new_version.version_id,
                phase_id=old_rule.phase_id,
                attribute_id=old_rule.attribute_id,
                rule_name=old_rule.rule_name,
                rule_type=old_rule.rule_type,
                rule_code=old_rule.rule_code,
                rule_parameters=old_rule.rule_parameters,
                llm_provider=old_rule.llm_provider,
                llm_rationale=old_rule.llm_rationale,
                regulatory_reference=old_rule.regulatory_reference,
                tester_decision='approve' if old_rule.status == 'approved' else None,
                report_owner_decision='approve' if old_rule.status == 'approved' else None,
                # Embed execution results
                execution_status='completed' if old_result else 'pending',
                total_records_tested=old_result.total_count if old_result else 0,
                passed_records=old_result.passed_count if old_result else 0,
                failed_records=old_result.failed_count if old_result else 0,
                pass_rate=old_result.pass_rate if old_result else None,
                # Embed quality scores
                completeness_score=old_profile.completeness_score if old_profile else None,
                validity_score=old_profile.validity_score if old_profile else None,
                accuracy_score=old_profile.accuracy_score if old_profile else None,
                consistency_score=old_profile.consistency_score if old_profile else None,
                uniqueness_score=old_profile.uniqueness_score if old_profile else None,
                overall_quality_score=old_profile.overall_quality_score if old_profile else None,
                result_summary=old_result.result_summary if old_result else None,
                status='approved' if old_rule.status == 'approved' else 'pending'
            )
            await db.add(new_rule)
        
        # Update version summary
        await update_version_summary(new_version.version_id)
    
    await db.commit()
```

### Model Implementation

#### Data Profiling Rule Version Model (Corrected Pattern)
```python
class DataProfilingRuleVersion(VersionedEntity):
    __tablename__ = 'cycle_report_data_profiling_rule_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    workflow_activity_id = Column(Integer, ForeignKey('workflow_activities.activity_id'))
    
    # Version Management (exact same as sample selection/scoping)
    version_number = Column(Integer, nullable=False)
    version_status = Column(Enum(VersionStatus), default=VersionStatus.DRAFT)
    parent_version_id = Column(UUID, ForeignKey('cycle_report_data_profiling_rule_versions.version_id'))
    
    # Temporal Workflow Context
    workflow_execution_id = Column(String(255))
    workflow_run_id = Column(String(255))
    
    # Rule Set Summary
    total_rules = Column(Integer, default=0)
    approved_rules = Column(Integer, default=0)
    rejected_rules = Column(Integer, default=0)
    
    # Data Source Reference (from planning phase)
    data_source_type = Column(String(50))
    planning_data_source_id = Column(Integer) # References planning phase data source
    
    # Approval Workflow
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'))
    submitted_at = Column(DateTime(timezone=True))
    approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    
    # Relationships
    rules = relationship("DataProfilingRule", back_populates="version")
    phase = relationship("WorkflowPhase")
    parent_version = relationship("DataProfilingRuleVersion", remote_side=[version_id])

#### Data Profiling Rule Model (NO Execution Results)
```python
class DataProfilingRule(CustomPKModel, AuditMixin):
    __tablename__ = 'cycle_report_data_profiling_rules'
    
    rule_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('cycle_report_data_profiling_rule_versions.version_id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    attribute_id = Column(Integer, ForeignKey('cycle_report_planning_attributes.id'), nullable=False)
    
    # Rule Definition (NO execution results)
    rule_name = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)
    rule_description = Column(Text)
    rule_code = Column(Text, nullable=False)
    rule_parameters = Column(JSONB)
    
    # LLM Metadata
    llm_provider = Column(String(50))
    llm_rationale = Column(Text)
    llm_confidence_score = Column(DECIMAL(5,2))
    regulatory_reference = Column(Text)
    
    # Rule Configuration
    is_executable = Column(Boolean, default=True)
    execution_order = Column(Integer, default=0)
    severity = Column(String(50), default='medium')
    
    # Dual Decision Model (same as scoping)
    tester_decision = Column(String(50))
    tester_decided_by = Column(Integer, ForeignKey('users.user_id'))
    tester_decided_at = Column(DateTime(timezone=True))
    tester_notes = Column(Text)
    
    report_owner_decision = Column(String(50))
    report_owner_decided_by = Column(Integer, ForeignKey('users.user_id'))
    report_owner_decided_at = Column(DateTime(timezone=True))
    report_owner_notes = Column(Text)
    
    # Status
    status = Column(String(50), default='pending')
    
    # Relationships
    version = relationship("DataProfilingRuleVersion", back_populates="rules")
    attribute = relationship("PlanningAttribute")
    phase = relationship("WorkflowPhase")

#### Background Job Integration Model
```python
class BackgroundJobResult:
    """Model for accessing execution results from background jobs"""
    
    def __init__(self, job_id: str, background_job_manager: BackgroundJobManager):
        self.job_id = job_id
        self.background_job_manager = background_job_manager
    
    async def get_execution_results(self) -> Dict[str, Any]:
        """Get execution results from background job metadata"""
        job = await self.background_job_manager.get_job(self.job_id)
        return job.metadata.get('execution_results', {})
    
    async def get_rule_result(self, rule_id: str) -> Dict[str, Any]:
        """Get execution result for specific rule"""
        results = await self.get_execution_results()
        return results.get(rule_id, {})
```

### Service Layer Implementation

#### Unified Data Profiling Service (Corrected Pattern)
```python
class DataProfilingService:
    def __init__(self, db: AsyncSession, background_job_manager: BackgroundJobManager):
        self.db = db
        self.background_job_manager = background_job_manager
    
    async def create_profiling_rule_version(self, phase_id: int, attributes: List[PlanningAttribute]) -> DataProfilingRuleVersion:
        """Create initial data profiling rule version with LLM-generated rules"""
        
        # Get data source from planning phase
        planning_data_source = await self.get_planning_data_source(phase_id)
        
        # Create version
        version = DataProfilingRuleVersion(
            phase_id=phase_id,
            version_number=1,
            version_status=VersionStatus.DRAFT,
            data_source_type=planning_data_source.source_type,
            planning_data_source_id=planning_data_source.id
        )
        self.db.add(version)
        await self.db.flush()  # Get version_id
        
        # Create rules with LLM generation
        profiling_rules = []
        for attr in attributes:
            llm_rules = await self.llm_service.generate_profiling_rules(attr, planning_data_source)
            
            for llm_rule in llm_rules:
                profiling_rule = DataProfilingRule(
                    version_id=version.version_id,
                    phase_id=phase_id,
                    attribute_id=attr.id,
                    rule_name=llm_rule.rule_name,
                    rule_type=llm_rule.rule_type,
                    rule_code=llm_rule.rule_code,
                    rule_parameters=llm_rule.parameters,
                    llm_provider=llm_rule.provider,
                    llm_rationale=llm_rule.rationale,
                    regulatory_reference=llm_rule.regulatory_reference,
                    status='pending'
                )
                profiling_rules.append(profiling_rule)
        
        self.db.add_all(profiling_rules)
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(version.version_id)
        return version
    
    async def update_tester_decision(self, rule_id: str, decision_data: TesterDecisionRequest) -> DataProfilingRule:
        """Update tester decision on a profiling rule"""
        rule = await self.db.get(DataProfilingRule, rule_id)
        
        rule.tester_decision = decision_data.tester_decision
        rule.tester_notes = decision_data.notes
        rule.tester_decided_by = decision_data.user_id
        rule.tester_decided_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(rule.version_id)
        return rule
    
    async def submit_for_approval(self, version_id: str, submitted_by: int) -> DataProfilingRuleVersion:
        """Submit profiling rule version for report owner approval"""
        version = await self.db.get(DataProfilingRuleVersion, version_id)
        
        version.version_status = VersionStatus.PENDING_APPROVAL
        version.submitted_by_id = submitted_by
        version.submitted_at = datetime.utcnow()
        
        # Update all rules to submitted status
        await self.db.execute(
            update(DataProfilingRule)
            .where(DataProfilingRule.version_id == version_id)
            .values(status='submitted')
        )
        
        await self.db.commit()
        return version
    
    async def approve_version(self, version_id: str, approved_by: int) -> DataProfilingRuleVersion:
        """Approve profiling rule version (report owner action)"""
        version = await self.db.get(DataProfilingRuleVersion, version_id)
        
        # Mark previous versions as superseded
        await self.db.execute(
            update(DataProfilingRuleVersion)
            .where(DataProfilingRuleVersion.phase_id == version.phase_id)
            .where(DataProfilingRuleVersion.version_status == VersionStatus.APPROVED)
            .values(version_status=VersionStatus.SUPERSEDED)
        )
        
        # Approve current version
        version.version_status = VersionStatus.APPROVED
        version.approved_by_id = approved_by
        version.approved_at = datetime.utcnow()
        
        # Update all rules to approved status
        await self.db.execute(
            update(DataProfilingRule)
            .where(DataProfilingRule.version_id == version_id)
            .values(status='approved')
        )
        
        await self.db.commit()
        return version
    
    async def execute_profiling_rules(self, version_id: str) -> str:
        """Execute all approved rules in a version via background job"""
        version = await self.db.get(DataProfilingRuleVersion, version_id)
        
        # Get all approved rules
        rules = await self.db.execute(
            select(DataProfilingRule)
            .where(DataProfilingRule.version_id == version_id)
            .where(DataProfilingRule.status == 'approved')
            .order_by(DataProfilingRule.execution_order)
        )
        rules = rules.scalars().all()
        
        # Create background job for execution
        job_id = await self.background_job_manager.create_job(
            job_type="data_profiling_execution",
            job_name=f"Execute Data Profiling Rules - Version {version_id}",
            metadata={
                "version_id": version_id,
                "rule_count": len(rules),
                "phase_id": version.phase_id
            }
        )
        
        # Execute via Celery task
        execute_profiling_rules_task.delay(
            job_id=job_id,
            version_id=version_id,
            rule_ids=[str(rule.rule_id) for rule in rules]
        )
        
        return job_id
    
    async def get_execution_results(self, version_id: str) -> Dict[str, Any]:
        """Get execution results for a version from background jobs"""
        # Find the latest execution job for this version
        jobs = await self.background_job_manager.get_jobs_by_type("data_profiling_execution")
        
        for job in jobs:
            if job.metadata.get("version_id") == version_id:
                if job.status == "COMPLETED":
                    return job.metadata.get("execution_results", {})
                elif job.status == "FAILED":
                    return {"error": job.error_message}
                else:
                    return {"status": job.status, "progress": job.progress}
        
        return {"error": "No execution found for this version"}
    
    async def get_planning_data_source(self, phase_id: int) -> PlanningDataSource:
        """Get data source configuration from planning phase"""
        # Get planning phase for same cycle/report
        phase = await self.db.get(WorkflowPhase, phase_id)
        
        # Find planning phase
        planning_phase = await self.db.execute(
            select(WorkflowPhase)
            .where(WorkflowPhase.cycle_id == phase.cycle_id)
            .where(WorkflowPhase.report_id == phase.report_id)
            .where(WorkflowPhase.phase_name == "Planning")
        )
        planning_phase = planning_phase.scalar_one()
        
        # Get data source from planning phase
        data_source = await self.db.execute(
            select(PlanningDataSource)
            .where(PlanningDataSource.phase_id == planning_phase.phase_id)
        )
        
        return data_source.scalar_one()
    
    async def update_version_summary(self, version_id: str):
        """Update version summary statistics"""
        rules = await self.db.execute(
            select(DataProfilingRule)
            .where(DataProfilingRule.version_id == version_id)
        )
        rules = rules.scalars().all()
        
        version = await self.db.get(DataProfilingRuleVersion, version_id)
        version.total_rules = len(rules)
        version.approved_rules = sum(1 for rule in rules if rule.status == 'approved')
        version.rejected_rules = sum(1 for rule in rules if rule.status == 'rejected')
        
        await self.db.commit()

#### Celery Task for Rule Execution
```python
@celery_app.task(bind=True)
def execute_profiling_rules_task(self, job_id: str, version_id: str, rule_ids: List[str]):
    """Execute profiling rules in background"""
    
    # Update job status
    background_job_manager.update_job_status(job_id, "RUNNING")
    
    results = {}
    total_records = 0
    total_anomalies = 0
    
    try:
        for i, rule_id in enumerate(rule_ids):
            # Get rule
            rule = db.get(DataProfilingRule, rule_id)
            
            # Execute rule against data source
            result = execute_single_rule(rule)
            
            # Store results
            results[rule_id] = {
                "passed_records": result.passed_records,
                "failed_records": result.failed_records,
                "total_records": result.total_records,
                "pass_rate": result.pass_rate,
                "quality_scores": result.quality_scores,
                "anomaly_details": result.anomaly_details,
                "execution_time_ms": result.execution_time_ms
            }
            
            total_records += result.total_records
            total_anomalies += result.anomaly_count
            
            # Update progress
            progress = int((i + 1) / len(rule_ids) * 100)
            background_job_manager.update_job_progress(job_id, progress)
        
        # Store final results
        background_job_manager.update_job_status(
            job_id, 
            "COMPLETED",
            metadata={
                "execution_results": results,
                "summary": {
                    "total_records_processed": total_records,
                    "total_anomalies_found": total_anomalies,
                    "rules_executed": len(rule_ids)
                }
            }
        )
        
    except Exception as e:
        background_job_manager.update_job_status(
            job_id, 
            "FAILED",
            error_message=str(e)
        )
        raise
```

### API Endpoints

#### Data Profiling Version Management (Same Pattern as Sample Selection)
```python
@router.post("/data-profiling/versions", response_model=DataProfilingVersionResponse)
async def create_profiling_version(
    request: CreateProfilingVersionRequest,
    service: DataProfilingService = Depends()
):
    """Create initial data profiling version with LLM-generated rules"""
    return await service.create_profiling_version(request.phase_id, request.attributes, request.data_source_config)

@router.get("/data-profiling/versions/{version_id}", response_model=DataProfilingVersionResponse)
async def get_profiling_version(
    version_id: str,
    service: DataProfilingService = Depends()
):
    """Get specific profiling version with all rules"""
    return await service.get_profiling_version(version_id)

@router.post("/data-profiling/versions/{version_id}/submit", response_model=DataProfilingVersionResponse)
async def submit_version_for_approval(
    version_id: str,
    service: DataProfilingService = Depends(),
    current_user: User = Depends()
):
    """Submit profiling version for report owner approval"""
    return await service.submit_for_approval(version_id, current_user.user_id)

@router.post("/data-profiling/versions/{version_id}/approve", response_model=DataProfilingVersionResponse)
async def approve_version(
    version_id: str,
    service: DataProfilingService = Depends(),
    current_user: User = Depends()
):
    """Approve profiling version (report owner action)"""
    return await service.approve_version(version_id, current_user.user_id)

@router.post("/data-profiling/versions/{version_id}/execute", response_model=DataProfilingVersionResponse)
async def execute_profiling_rules(
    version_id: str,
    service: DataProfilingService = Depends()
):
    """Execute all approved rules in a version"""
    return await service.execute_profiling_rules(version_id)

#### Data Profiling Rule Management
@router.put("/data-profiling/rules/{rule_id}", response_model=DataProfilingRuleResponse)
async def update_tester_decision(
    rule_id: str,
    request: TesterDecisionRequest,
    service: DataProfilingService = Depends()
):
    """Update tester decision on a profiling rule"""
    return await service.update_tester_decision(rule_id, request)

@router.post("/data-profiling/rules/{rule_id}/mark-anomaly", response_model=DataProfilingRuleResponse)
async def mark_anomaly(
    rule_id: str,
    request: MarkAnomalyRequest,
    service: DataProfilingService = Depends()
):
    """Mark anomalies in profiling results"""
    return await service.mark_anomaly(rule_id, request)

@router.get("/data-profiling/rules/{version_id}", response_model=List[DataProfilingRuleResponse])
async def get_profiling_rules(
    version_id: str,
    service: DataProfilingService = Depends()
):
    """Get all profiling rules for a version"""
    return await service.get_profiling_rules(version_id)

@router.get("/data-profiling/phases/{phase_id}/current", response_model=DataProfilingVersionResponse)
async def get_current_profiling_version(
    phase_id: int,
    service: DataProfilingService = Depends()
):
    """Get current approved profiling version for a phase"""
    return await service.get_current_version(phase_id)

@router.get("/data-profiling/phases/{phase_id}/history", response_model=List[DataProfilingVersionResponse])
async def get_profiling_version_history(
    phase_id: int,
    service: DataProfilingService = Depends()
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
- [ ] LLM integration tests
- [ ] Rule execution tests

### Integration Tests
- [ ] End-to-end profiling workflow tests
- [ ] Version management tests
- [ ] Approval workflow tests
- [ ] Rule execution integration tests
- [ ] Anomaly detection tests

### Performance Tests
- [ ] Query performance with large datasets
- [ ] Rule execution performance
- [ ] Concurrent user access tests
- [ ] Database indexing effectiveness
- [ ] Memory usage optimization tests

## 🚀 Deployment Strategy

### Pre-Deployment Checklist
- [ ] Database migration scripts tested on staging
- [ ] Data integrity validation scripts ready
- [ ] Backup and rollback procedures documented
- [ ] Performance benchmarks established
- [ ] User training materials prepared
- [ ] Monitoring and alerting configured

### Deployment Steps
1. **Maintenance Window**: Schedule 4-hour maintenance window
2. **Backup**: Complete backup of existing profiling data
3. **Migration**: Execute data consolidation migration
4. **Validation**: Run data integrity checks
5. **Deployment**: Deploy new application code
6. **Testing**: Execute smoke tests
7. **Monitoring**: Enable monitoring and alerting
8. **Go-Live**: Enable new profiling functionality

### Rollback Plan
```python
async def rollback_profiling_migration():
    """Rollback profiling migration if issues occur"""
    # 1. Restore backup tables
    await restore_backup_tables([
        'cycle_report_data_profiling_files',
        'cycle_report_data_profiling_rules',
        'cycle_report_data_profiling_results',
        'cycle_report_data_profiling_configurations',
        'cycle_report_data_profiling_jobs'
    ])
    
    # 2. Update application configuration
    await update_config(use_legacy_profiling_tables=True)
    
    # 3. Restart application services
    await restart_services(['api', 'workers'])
    
    # 4. Validate rollback success
    await validate_rollback()
```

## 📊 Success Metrics

### Technical Metrics
- [ ] Database query performance improvement (target: 90% faster)
- [ ] Storage space reduction (target: 80% less space)
- [ ] Code complexity reduction (target: 85% fewer lines)
- [ ] Migration success rate (target: 100% data integrity)

### Business Metrics
- [ ] User adoption rate (target: 90% within 2 weeks)
- [ ] Data profiling workflow efficiency (target: 60% faster completion)
- [ ] Error rate reduction (target: 70% fewer support tickets)
- [ ] System reliability (target: 99.9% uptime)

## 🔐 Security Considerations

### Data Protection
- [ ] Encryption at rest for profiling data
- [ ] Access control validation for all endpoints
- [ ] Audit logging for all profiling actions
- [ ] Data retention policy compliance

### Privacy
- [ ] Sensitive data handling in profiling rules
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
| LLM integration issues | Medium | Medium | Thorough integration testing |
| Rule execution failures | Low | High | Validation scripts, error handling |

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

*This implementation plan serves as a comprehensive guide for the Data Profiling system consolidation. The plan focuses on reducing complexity by 91% while maintaining all critical functionality and ensuring perfect alignment with the established sample selection and scoping patterns.*