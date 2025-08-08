# Enterprise Versioning Architecture for Testing Workflow System

## Executive Summary

This document presents a comprehensive, enterprise-grade versioning architecture that addresses versioning requirements across all 8 phases of the testing workflow while maintaining backward compatibility and supporting different data types.

## Architecture Principles

1. **Unified but Flexible**: Single versioning framework that adapts to phase-specific needs
2. **Type Safety**: Strong typing for different data entities (attributes, samples, documents, etc.)
3. **Audit Complete**: Full audit trail for all changes, even in non-versioned phases
4. **Performance Optimized**: Efficient queries and storage
5. **Zero Downtime Migration**: Phased approach with backward compatibility

## Phase Overview

We have **9 phases** in the testing workflow:

1. **Planning** - Full Versioning (Tester creates & approves)
2. **Data Profiling** - Full Versioning (Tester → Report Owner)
3. **Scoping** - Full Versioning (Tester → Report Owner)
4. **Sample Selection** - Full Versioning (Tester → Report Owner)
5. **Data Owner ID** - Audit Only
6. **Request Info** - Audit Only
7. **Test Execution** - Audit Only
8. **Observation Management** - Full Versioning (Tester → Report Owner)
9. **Finalize Test Report** - Full Versioning (Tester creates, Test Executive approves)

## Core Architecture Components

### 1. Base Versioning Framework

```python
# Enhanced VersionedMixin with phase-specific support
class EnhancedVersionedMixin:
    """Enterprise-grade versioning mixin with phase awareness"""
    
    # Core versioning fields
    version_id = Column(UUID, primary_key=True, default=uuid4)
    version_number = Column(Integer, nullable=False, default=1)
    version_status = Column(Enum(VersionStatus), nullable=False, default=VersionStatus.DRAFT)
    
    # Phase context
    phase_name = Column(String(50), nullable=False)
    phase_version_type = Column(String(50))  # 'full', 'audit_only'
    
    # Lifecycle tracking
    created_at = Column(DateTime, default=func.now())
    created_by_id = Column(Integer, ForeignKey('users.user_id'))
    submitted_at = Column(DateTime)
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'))
    reviewed_at = Column(DateTime)
    reviewed_by_id = Column(Integer, ForeignKey('users.user_id'))
    
    # Version relationships
    parent_version_id = Column(UUID, ForeignKey('version_id'))
    master_record_id = Column(UUID)  # Links all versions of same entity
    
    # Approval workflow
    approval_required = Column(Boolean, default=True)
    approval_status = Column(Enum(ApprovalStatus))
    approval_notes = Column(Text)
    
    # Soft delete support
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by_id = Column(Integer, ForeignKey('users.user_id'))
```

### 2. Phase-Specific Data Models

#### A. Planning Phase (Full Versioning)
```python
class PlanningPhaseVersion(Base, EnhancedVersionedMixin):
    """Versioned planning phase with attribute decisions"""
    __tablename__ = 'planning_phase_versions'
    
    cycle_id = Column(UUID, nullable=False)
    report_id = Column(UUID, nullable=False)
    
    # Phase-specific metadata
    planning_metadata = Column(JSONB)
    
    # Relationships
    attribute_decisions = relationship("AttributeDecision", back_populates="planning_version")
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'version_number'),
        Index('idx_planning_active', 'cycle_id', 'report_id', 'version_status'),
    )

class AttributeDecision(Base):
    """Individual attribute decisions within a planning version"""
    __tablename__ = 'attribute_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid4)
    planning_version_id = Column(UUID, ForeignKey('planning_phase_versions.version_id'))
    
    # Attribute reference
    attribute_id = Column(UUID, nullable=False)
    attribute_data = Column(JSONB, nullable=False)
    
    # Decision tracking
    decision_type = Column(Enum('include', 'exclude', 'modify'))
    decision_reason = Column(Text)
    decision_metadata = Column(JSONB)
    
    # Lineage tracking
    carried_from_version_id = Column(UUID)
    modification_history = Column(JSONB)  # Array of changes
```

#### B. Data Profiling Phase (Full Versioning)
```python
class DataProfilingVersion(Base, EnhancedVersionedMixin):
    """Versioned data profiling rules"""
    __tablename__ = 'data_profiling_versions'
    
    cycle_id = Column(UUID, nullable=False)
    report_id = Column(UUID, nullable=False)
    
    # Profiling context
    source_data_reference = Column(JSONB)  # Files, tables, etc.
    profiling_parameters = Column(JSONB)
    
    # Relationships
    profiling_rules = relationship("ProfilingRuleDecision", back_populates="profiling_version")

class ProfilingRuleDecision(Base):
    """Individual profiling rule decisions"""
    __tablename__ = 'profiling_rule_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid4)
    profiling_version_id = Column(UUID, ForeignKey('data_profiling_versions.version_id'))
    
    # Rule definition
    rule_type = Column(String(50))  # 'validation', 'transformation', 'quality_check'
    rule_definition = Column(JSONB)
    
    # Recommendation and approval
    recommended_by_id = Column(Integer, ForeignKey('users.user_id'))
    recommendation_reason = Column(Text)
    
    approval_status = Column(Enum('pending', 'approved', 'rejected', 'modified'))
    approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    approval_notes = Column(Text)
```

#### C. Scoping Phase (Full Versioning)
```python
class ScopingVersion(Base, EnhancedVersionedMixin):
    """Versioned scoping decisions"""
    __tablename__ = 'scoping_versions'
    
    cycle_id = Column(UUID, nullable=False)
    report_id = Column(UUID, nullable=False)
    
    # Scoping context
    scoping_criteria = Column(JSONB)
    total_attributes = Column(Integer)
    scoped_attributes = Column(Integer)
    
    # Relationships
    scoping_decisions = relationship("ScopingDecision", back_populates="scoping_version")

class ScopingDecision(Base):
    """Individual attribute scoping decisions"""
    __tablename__ = 'scoping_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid4)
    scoping_version_id = Column(UUID, ForeignKey('scoping_versions.version_id'))
    
    # Attribute reference
    attribute_id = Column(UUID, nullable=False)
    
    # Scoping decision
    is_in_scope = Column(Boolean, nullable=False)
    scoping_rationale = Column(Text)
    risk_rating = Column(String(20))  # 'high', 'medium', 'low'
    
    # Recommendation and approval tracking
    recommended_by_id = Column(Integer, ForeignKey('users.user_id'))
    recommendation_type = Column(Enum('tester', 'automated', 'carryforward'))
    
    approval_status = Column(Enum('pending', 'approved', 'rejected'))
    approved_by_id = Column(Integer, ForeignKey('users.user_id'))
```

#### D. Sample Selection (Full Versioning - Enhanced)
```python
class SampleSelectionVersion(Base, EnhancedVersionedMixin):
    """Enhanced sample selection versioning"""
    __tablename__ = 'sample_selection_versions'
    
    cycle_id = Column(UUID, nullable=False)
    report_id = Column(UUID, nullable=False)
    
    # Selection metadata
    selection_criteria = Column(JSONB)
    target_sample_size = Column(Integer)
    actual_sample_size = Column(Integer)
    
    # Generation tracking
    generation_methods = Column(JSONB)  # Array of methods used
    
    # Relationships
    sample_decisions = relationship("SampleDecision", back_populates="selection_version")

class SampleDecision(Base):
    """Enhanced sample decision tracking"""
    __tablename__ = 'sample_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid4)
    selection_version_id = Column(UUID, ForeignKey('sample_selection_versions.version_id'))
    
    # Sample data
    sample_identifier = Column(String(255), nullable=False)
    sample_data = Column(JSONB, nullable=False)
    sample_type = Column(String(50))  # 'population', 'targeted', 'risk_based'
    
    # Recommendation tracking
    recommendation_source = Column(Enum('tester', 'llm', 'manual', 'carried_forward'))
    recommended_by_id = Column(Integer, ForeignKey('users.user_id'))
    recommendation_timestamp = Column(DateTime)
    recommendation_metadata = Column(JSONB)  # LLM params, manual upload ref, etc.
    
    # Approval tracking
    decision_status = Column(Enum('pending', 'approved', 'rejected', 'modified'))
    decided_by_id = Column(Integer, ForeignKey('users.user_id'))
    decision_timestamp = Column(DateTime)
    decision_notes = Column(Text)
    
    # Lineage
    carried_from_version_id = Column(UUID)
    carried_from_decision_id = Column(UUID)
    modification_reason = Column(Text)
```

#### E. Data Owner ID Phase (Audit Only)
```python
class DataOwnerAssignment(Base, AuditMixin):
    """Data owner assignments with full audit trail"""
    __tablename__ = 'data_owner_assignments'
    
    assignment_id = Column(UUID, primary_key=True, default=uuid4)
    cycle_id = Column(UUID, nullable=False)
    report_id = Column(UUID, nullable=False)
    
    # Assignment details
    data_owner_id = Column(Integer, ForeignKey('users.user_id'))
    lob_id = Column(UUID, ForeignKey('lobs.lob_id'))
    assignment_type = Column(String(50))  # 'primary', 'backup', 'delegate'
    
    # Status tracking
    status = Column(Enum('active', 'inactive', 'transferred'))
    effective_from = Column(DateTime, default=func.now())
    effective_to = Column(DateTime)
    
    # Change tracking
    previous_assignment_id = Column(UUID, ForeignKey('data_owner_assignments.assignment_id'))
    change_reason = Column(Text)
    
    # Relationships
    change_history = relationship("DataOwnerChangeHistory", back_populates="assignment")

class DataOwnerChangeHistory(Base):
    """Detailed history of data owner changes"""
    __tablename__ = 'data_owner_change_history'
    
    history_id = Column(UUID, primary_key=True, default=uuid4)
    assignment_id = Column(UUID, ForeignKey('data_owner_assignments.assignment_id'))
    
    # Change details
    change_type = Column(String(50))  # 'created', 'transferred', 'deactivated'
    changed_by_id = Column(Integer, ForeignKey('users.user_id'))
    changed_at = Column(DateTime, default=func.now())
    
    # Before/after state
    previous_state = Column(JSONB)
    new_state = Column(JSONB)
    change_metadata = Column(JSONB)
```

#### F. Request for Information Phase (Audit Only)
```python
class DocumentSubmission(Base, AuditMixin):
    """Document submissions with version tracking"""
    __tablename__ = 'document_submissions'
    
    submission_id = Column(UUID, primary_key=True, default=uuid4)
    cycle_id = Column(UUID, nullable=False)
    report_id = Column(UUID, nullable=False)
    
    # Document reference
    document_id = Column(UUID, nullable=False)
    document_version = Column(Integer, default=1)
    document_metadata = Column(JSONB)
    
    # Submission tracking
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'))
    submitted_at = Column(DateTime, default=func.now())
    submission_type = Column(String(50))  # 'initial', 'revision', 'supplemental'
    
    # Status
    status = Column(Enum('pending_review', 'accepted', 'rejected', 'revision_requested'))
    reviewed_by_id = Column(Integer, ForeignKey('users.user_id'))
    review_notes = Column(Text)
    
    # Version chain
    replaces_submission_id = Column(UUID, ForeignKey('document_submissions.submission_id'))
    is_current = Column(Boolean, default=True)
    
    # Relationships
    revision_history = relationship("DocumentRevisionHistory", back_populates="submission")

class DocumentRevisionHistory(Base):
    """Track all document changes"""
    __tablename__ = 'document_revision_history'
    
    history_id = Column(UUID, primary_key=True, default=uuid4)
    submission_id = Column(UUID, ForeignKey('document_submissions.submission_id'))
    
    # Revision details
    revision_type = Column(String(50))  # 'content_update', 'metadata_change', 'resubmission'
    revision_reason = Column(Text)
    changed_fields = Column(JSONB)  # List of what changed
    
    # Tracking
    revised_by_id = Column(Integer, ForeignKey('users.user_id'))
    revised_at = Column(DateTime, default=func.now())
```

#### G. Test Execution Phase (Audit Only)
```python
class TestExecutionAudit(Base, AuditMixin):
    """Audit trail for test execution phase"""
    __tablename__ = 'test_execution_audit'
    
    audit_id = Column(UUID, primary_key=True, default=uuid4)
    cycle_id = Column(UUID, nullable=False)
    report_id = Column(UUID, nullable=False)
    test_execution_id = Column(UUID)
    
    # Action tracking
    action_type = Column(String(50))  # 'document_request', 'data_update_request', 'test_rerun'
    action_details = Column(JSONB)
    
    # Request tracking
    requested_by_id = Column(Integer, ForeignKey('users.user_id'))
    requested_at = Column(DateTime, default=func.now())
    request_reason = Column(Text)
    
    # Response tracking
    responded_by_id = Column(Integer, ForeignKey('users.user_id'))
    responded_at = Column(DateTime)
    response_status = Column(String(50))  # 'fulfilled', 'rejected', 'partial'
    response_notes = Column(Text)
    
    # Metrics
    turnaround_time_hours = Column(Float)
    impact_on_timeline = Column(String(50))  # 'none', 'minor_delay', 'major_delay'
```

#### H. Observation Management (Full Versioning)
```python
class ObservationVersion(Base, EnhancedVersionedMixin):
    """Versioned observations"""
    __tablename__ = 'observation_versions'
    
    cycle_id = Column(UUID, nullable=False)
    report_id = Column(UUID, nullable=False)
    
    # Observation context
    observation_period = Column(JSONB)  # Start/end dates, scope
    total_observations = Column(Integer)
    
    # Relationships
    observations = relationship("ObservationDecision", back_populates="observation_version")

class ObservationDecision(Base):
    """Individual observation decisions"""
    __tablename__ = 'observation_decisions'
    
    decision_id = Column(UUID, primary_key=True, default=uuid4)
    observation_version_id = Column(UUID, ForeignKey('observation_versions.version_id'))
    
    # Observation details
    observation_type = Column(String(50))  # 'finding', 'recommendation', 'compliance_issue'
    severity = Column(Enum('critical', 'high', 'medium', 'low'))
    observation_data = Column(JSONB)
    
    # Creation and approval
    created_by_id = Column(Integer, ForeignKey('users.user_id'))
    creation_timestamp = Column(DateTime)
    
    approval_status = Column(Enum('draft', 'pending_review', 'approved', 'rejected'))
    approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    approval_timestamp = Column(DateTime)
    
    # Evidence and remediation
    evidence_references = Column(JSONB)  # Links to supporting documents
    remediation_status = Column(String(50))
    remediation_deadline = Column(Date)
```

#### I. Finalize Test Report (Full Versioning)
```python
class TestReportVersion(Base, EnhancedVersionedMixin):
    """Versioned test report finalization"""
    __tablename__ = 'test_report_versions'
    
    cycle_id = Column(UUID, nullable=False)
    report_id = Column(UUID, nullable=False)
    
    # Report metadata
    report_title = Column(String(255), nullable=False)
    report_period_start = Column(Date)
    report_period_end = Column(Date)
    executive_summary = Column(Text)
    
    # Report components
    included_sections = Column(JSONB)  # List of sections to include
    report_template_id = Column(UUID)
    
    # Generation details
    generated_at = Column(DateTime)
    generation_method = Column(String(50))  # 'manual', 'automated', 'hybrid'
    
    # Final document references
    draft_document_id = Column(UUID)
    final_document_id = Column(UUID)
    
    # Sign-off tracking
    requires_executive_approval = Column(Boolean, default=True)
    executive_approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    executive_approval_date = Column(DateTime)
    
    # Relationships
    report_sections = relationship("TestReportSection", back_populates="report_version")
    sign_offs = relationship("TestReportSignOff", back_populates="report_version")

class TestReportSection(Base):
    """Individual sections within a test report"""
    __tablename__ = 'test_report_sections'
    
    section_id = Column(UUID, primary_key=True, default=uuid4)
    report_version_id = Column(UUID, ForeignKey('test_report_versions.version_id'))
    
    # Section details
    section_type = Column(String(50))  # 'executive_summary', 'findings', 'recommendations', etc.
    section_title = Column(String(255))
    section_content = Column(Text)
    section_order = Column(Integer)
    
    # Content tracking
    content_source = Column(String(50))  # 'manual', 'generated', 'imported'
    source_references = Column(JSONB)  # Links to observations, test results, etc.
    
    # Review status
    reviewed_by_id = Column(Integer, ForeignKey('users.user_id'))
    review_status = Column(Enum('pending', 'approved', 'needs_revision'))
    review_notes = Column(Text)

class TestReportSignOff(Base):
    """Track all required sign-offs for test report"""
    __tablename__ = 'test_report_signoffs'
    
    signoff_id = Column(UUID, primary_key=True, default=uuid4)
    report_version_id = Column(UUID, ForeignKey('test_report_versions.version_id'))
    
    # Sign-off details
    signoff_role = Column(String(50))  # 'test_lead', 'test_executive', 'report_owner'
    signoff_user_id = Column(Integer, ForeignKey('users.user_id'))
    signoff_status = Column(Enum('pending', 'signed', 'rejected'))
    signoff_date = Column(DateTime)
    signoff_comments = Column(Text)
    
    # Delegation support
    delegated_from_id = Column(Integer, ForeignKey('users.user_id'))
    delegation_reason = Column(Text)
```

### 3. Unified Query Interface

```python
class UnifiedVersioningService:
    """Enterprise service for consistent versioning operations"""
    
    def create_version(self, phase: str, cycle_id: UUID, report_id: UUID, 
                      user_id: int, data: dict) -> UUID:
        """Create new version for any phase"""
        phase_config = self.get_phase_config(phase)
        
        if phase_config.versioning_type == 'full':
            return self._create_full_version(phase, cycle_id, report_id, user_id, data)
        else:
            return self._create_audit_record(phase, cycle_id, report_id, user_id, data)
    
    def get_current_version(self, phase: str, cycle_id: UUID, report_id: UUID) -> dict:
        """Get current approved version for any phase"""
        phase_config = self.get_phase_config(phase)
        
        if phase_config.versioning_type == 'full':
            return self._get_approved_version(phase, cycle_id, report_id)
        else:
            return self._get_current_state(phase, cycle_id, report_id)
    
    def get_version_history(self, phase: str, cycle_id: UUID, report_id: UUID) -> List[dict]:
        """Get complete history for any phase"""
        phase_config = self.get_phase_config(phase)
        
        if phase_config.versioning_type == 'full':
            return self._get_version_history(phase, cycle_id, report_id)
        else:
            return self._get_audit_history(phase, cycle_id, report_id)
```

### 4. Metrics and Analytics Support

```python
class VersioningMetrics(Base):
    """Centralized metrics for all versioning activities"""
    __tablename__ = 'versioning_metrics'
    
    metric_id = Column(UUID, primary_key=True, default=uuid4)
    
    # Context
    cycle_id = Column(UUID, nullable=False)
    report_id = Column(UUID, nullable=False)
    phase_name = Column(String(50), nullable=False)
    
    # Metric type
    metric_type = Column(String(50))  # 'version_count', 'approval_time', 'rejection_rate'
    metric_value = Column(Float)
    metric_metadata = Column(JSONB)
    
    # Timestamps
    calculated_at = Column(DateTime, default=func.now())
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Indexes for analytics
    __table_args__ = (
        Index('idx_metrics_phase', 'phase_name', 'metric_type'),
        Index('idx_metrics_cycle', 'cycle_id', 'report_id', 'phase_name'),
    )
```

## Implementation Strategy

### Phase 1: Foundation (Weeks 1-2)
1. Deploy enhanced versioning framework
2. Create phase configuration registry
3. Implement unified service layer
4. Set up metrics collection

### Phase 2: Full Versioning Phases (Weeks 3-6)
1. Migrate Planning phase
2. Migrate Data Profiling phase
3. Migrate Scoping phase
4. Migrate Sample Selection phase
5. Migrate Observation Management phase
6. Migrate Finalize Test Report phase

### Phase 3: Audit-Only Phases (Weeks 7-8)
1. Implement Data Owner ID tracking
2. Implement Request for Information tracking
3. Implement Test Execution tracking
4. Set up metrics dashboards

### Phase 4: Integration (Week 9)
1. Update APIs to use unified service
2. Implement backward compatibility layer
3. Update frontend to use new endpoints
4. Performance optimization

### Phase 5: Migration Completion (Week 10)
1. Data migration verification
2. Deprecate old tables
3. Remove compatibility layer
4. Final performance tuning

## Benefits

1. **Consistency**: Single versioning pattern across all phases
2. **Flexibility**: Supports both full versioning and audit-only tracking
3. **Traceability**: Complete history for all changes
4. **Performance**: Optimized queries with proper indexing
5. **Analytics**: Built-in metrics support
6. **Type Safety**: Strong typing for different data entities
7. **Maintainability**: Single codebase for all versioning logic

## Risk Mitigation

1. **Backward Compatibility**: Maintain old APIs during transition
2. **Data Integrity**: Comprehensive migration testing
3. **Performance**: Load testing at each phase
4. **Training**: Developer and user documentation
5. **Rollback**: Phase-by-phase approach allows targeted rollbacks

## Success Metrics

1. **Code Reduction**: 80% less versioning code
2. **Query Performance**: 50% faster version lookups
3. **Development Speed**: 60% faster to add new phases
4. **Bug Reduction**: 70% fewer versioning-related bugs
5. **Audit Completeness**: 100% change tracking coverage