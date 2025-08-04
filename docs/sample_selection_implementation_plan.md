# Sample Selection Implementation Plan

## 📋 Executive Summary

This document outlines the comprehensive implementation plan for the new simplified Sample Selection system in SynapseDTE. The plan involves migrating from 15+ legacy tables to a clean 2-table architecture that follows the established versioning framework used in data profiling and scoping phases.

## 🎯 Objectives

1. **Simplify Database Architecture**: Reduce from 15+ tables to 2 core tables
2. **Consistent Framework**: Align with data profiling and scoping patterns
3. **Intelligent Sampling**: Support 30/50/20 distribution (clean/anomaly/boundary)
4. **Version-Based Approval**: Implement submission-based approval workflow
5. **Phase Integration**: Tie all data to phase_id only (eliminate redundant cycle_id/report_id)
6. **Sample-Specific LOB**: Support different LOB per sample

## 🏗️ Database Design

### New Tables

#### 1. `cycle_report_sample_selection_versions`
- **Purpose**: Version management and metadata
- **Key Features**: 
  - Version lifecycle management (draft → pending_approval → approved/rejected → superseded)
  - Temporal workflow integration
  - Data source configuration
  - Intelligent sampling metrics

#### 2. `cycle_report_sample_selection_samples`
- **Purpose**: Individual sample decisions
- **Key Features**:
  - Sample-specific LOB tagging
  - Intelligent categorization (clean/anomaly/boundary)
  - Dual decision model (tester + report owner)
  - Carry-forward support for approved samples

### Legacy Tables to be Removed
- `cycle_report_sample_selection_samples` (current)
- `cycle_report_sample_sets`
- `cycle_report_sample_records`
- `sample_selection_phases`
- `individual_samples`
- `sample_validation_results`
- `sample_validation_issues`
- `sample_submissions`
- `sample_submission_items`
- `sample_approval_history`
- `llm_sample_generations`
- `sample_upload_history`
- `sample_audit_logs`
- `sample_feedback`
- And all other sample-related tables

## 📅 Implementation Timeline

### Phase 1: Foundation (Week 1-2)
- [ ] Create database migration scripts
- [ ] Implement new table schemas
- [ ] Create SQLAlchemy models
- [ ] Set up basic unit tests

### Phase 2: Core Services (Week 3-4)
- [ ] Implement sample selection service
- [ ] Create version management service
- [ ] Build intelligent sampling logic
- [ ] Implement carry-forward functionality

### Phase 3: API Layer (Week 5-6)
- [ ] Create API endpoints
- [ ] Implement request/response schemas
- [ ] Add authentication and authorization
- [ ] Create API documentation

### Phase 4: Frontend Integration (Week 7-8)
- [ ] Update frontend components
- [ ] Implement new UI flows
- [ ] Add version management interface
- [ ] Update approval workflows

### Phase 5: Data Migration (Week 9-10)
- [ ] Create data migration scripts
- [ ] Test migration on staging
- [ ] Backup existing data
- [ ] Execute production migration

### Phase 6: Testing & Validation (Week 11-12)
- [ ] Comprehensive testing
- [ ] Performance validation
- [ ] User acceptance testing
- [ ] Bug fixes and optimization

## 🔄 Implementation Details

### Database Migration Strategy

#### Step 1: Create New Tables
```sql
-- Create new tables with full schema
CREATE TABLE cycle_report_sample_selection_versions (...);
CREATE TABLE cycle_report_sample_selection_samples (...);
```

#### Step 2: Data Migration
```python
# Migrate existing data to new structure
async def migrate_sample_selection_data():
    # 1. Migrate sample sets to versions
    # 2. Migrate individual samples to new structure
    # 3. Preserve approval history
    # 4. Update references
```

#### Step 3: Rename Legacy Tables
```sql
-- Backup existing tables
ALTER TABLE cycle_report_sample_selection_samples RENAME TO cycle_report_sample_selection_samples_backup;
ALTER TABLE cycle_report_sample_sets RENAME TO cycle_report_sample_sets_backup;
-- ... rename all other tables
```

### Model Implementation

#### Version Model
```python
class SampleSelectionVersion(VersionedEntity):
    __tablename__ = 'cycle_report_sample_selection_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'))
    version_number = Column(Integer, nullable=False)
    version_status = Column(Enum(VersionStatus), default=VersionStatus.DRAFT)
    
    # Relationships
    samples = relationship("SampleSelectionSample", back_populates="version")
```

#### Sample Model
```python
class SampleSelectionSample(CustomPKModel, AuditMixin):
    __tablename__ = 'cycle_report_sample_selection_samples'
    
    sample_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('cycle_report_sample_selection_versions.version_id'))
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'))
    lob_id = Column(Integer, ForeignKey('lobs.lob_id'))
    
    # Sample data
    sample_identifier = Column(String(255), nullable=False)
    sample_data = Column(JSONB, nullable=False)
    sample_category = Column(Enum(SampleCategory), nullable=False)
    
    # Relationships
    version = relationship("SampleSelectionVersion", back_populates="samples")
    lob = relationship("LOB")
```

### Service Layer Implementation

#### Sample Selection Service
```python
class SampleSelectionService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_version(self, phase_id: int, **kwargs) -> SampleSelectionVersion:
        """Create a new sample selection version"""
        
    async def add_samples(self, version_id: UUID, samples: List[SampleData]) -> List[SampleSelectionSample]:
        """Add samples to a version"""
        
    async def submit_for_approval(self, version_id: UUID, submitted_by: int) -> SampleSelectionVersion:
        """Submit version for report owner approval"""
        
    async def approve_version(self, version_id: UUID, approved_by: int) -> SampleSelectionVersion:
        """Approve a version (marks previous versions as superseded)"""
        
    async def carry_forward_samples(self, source_version_id: UUID, target_version_id: UUID) -> List[SampleSelectionSample]:
        """Carry forward approved samples to new version"""
```

#### Intelligent Sampling Service
```python
class IntelligentSamplingService:
    async def generate_intelligent_samples(self, 
                                         data_source: DataSource,
                                         target_distribution: SampleDistribution,
                                         profiling_rules: List[ProfilingRule]) -> List[SampleData]:
        """Generate samples with 30/50/20 distribution"""
        
        # 1. Generate clean samples (30%)
        clean_samples = await self._generate_clean_samples(data_source, target_distribution.clean_count)
        
        # 2. Generate anomaly samples (50%)
        anomaly_samples = await self._generate_anomaly_samples(data_source, profiling_rules, target_distribution.anomaly_count)
        
        # 3. Generate boundary samples (20%)
        boundary_samples = await self._generate_boundary_samples(data_source, target_distribution.boundary_count)
        
        return clean_samples + anomaly_samples + boundary_samples
```

### API Endpoints

#### Version Management
```python
@router.post("/sample-selection/versions", response_model=SampleSelectionVersionResponse)
async def create_sample_selection_version(
    request: CreateSampleSelectionVersionRequest,
    service: SampleSelectionService = Depends()
):
    """Create a new sample selection version"""

@router.get("/sample-selection/versions/{version_id}", response_model=SampleSelectionVersionResponse)
async def get_sample_selection_version(
    version_id: UUID,
    service: SampleSelectionService = Depends()
):
    """Get a specific version with all samples"""

@router.post("/sample-selection/versions/{version_id}/submit", response_model=SampleSelectionVersionResponse)
async def submit_version_for_approval(
    version_id: UUID,
    service: SampleSelectionService = Depends()
):
    """Submit version for report owner approval"""

@router.post("/sample-selection/versions/{version_id}/approve", response_model=SampleSelectionVersionResponse)
async def approve_version(
    version_id: UUID,
    request: ApproveVersionRequest,
    service: SampleSelectionService = Depends()
):
    """Approve a version (report owner action)"""
```

#### Sample Management
```python
@router.post("/sample-selection/versions/{version_id}/samples", response_model=List[SampleSelectionSampleResponse])
async def add_samples_to_version(
    version_id: UUID,
    request: AddSamplesRequest,
    service: SampleSelectionService = Depends()
):
    """Add samples to a version"""

@router.post("/sample-selection/versions/{version_id}/generate-intelligent", response_model=List[SampleSelectionSampleResponse])
async def generate_intelligent_samples(
    version_id: UUID,
    request: GenerateIntelligentSamplesRequest,
    service: SampleSelectionService = Depends()
):
    """Generate intelligent samples using 30/50/20 distribution"""

@router.post("/sample-selection/versions/{version_id}/carry-forward", response_model=List[SampleSelectionSampleResponse])
async def carry_forward_samples(
    version_id: UUID,
    request: CarryForwardSamplesRequest,
    service: SampleSelectionService = Depends()
):
    """Carry forward approved samples from previous version"""
```

## 🧪 Testing Strategy

### Unit Tests
- [ ] Model validation tests
- [ ] Service layer tests
- [ ] API endpoint tests
- [ ] Data migration tests

### Integration Tests
- [ ] End-to-end workflow tests
- [ ] Version management tests
- [ ] Approval workflow tests
- [ ] Carry-forward functionality tests

### Performance Tests
- [ ] Large dataset handling
- [ ] Version creation performance
- [ ] Query performance with historical data
- [ ] Concurrent access tests

### Test Data Sets
```python
# Create test fixtures
@pytest.fixture
def sample_test_data():
    return {
        "clean_samples": [...],
        "anomaly_samples": [...],
        "boundary_samples": [...]
    }

@pytest.fixture
def approval_workflow_data():
    return {
        "tester_decisions": [...],
        "report_owner_decisions": [...],
        "feedback_scenarios": [...]
    }
```

## 🚀 Deployment Strategy

### Pre-Deployment Checklist
- [ ] Database migration scripts tested
- [ ] Backup strategy in place
- [ ] Rollback plan prepared
- [ ] Performance benchmarks established
- [ ] User training materials ready

### Deployment Steps
1. **Maintenance Window**: Schedule 4-hour maintenance window
2. **Backup**: Complete backup of existing data
3. **Migration**: Execute database migration
4. **Verification**: Validate data integrity
5. **Deployment**: Deploy new application code
6. **Testing**: Smoke tests and validation
7. **Go-Live**: Enable new functionality

### Rollback Plan
```python
# Rollback script
async def rollback_sample_selection_migration():
    # 1. Restore backup tables
    # 2. Update application configuration
    # 3. Restart services
    # 4. Validate rollback success
```

## 📊 Success Metrics

### Technical Metrics
- [ ] Database query performance (< 100ms for typical queries)
- [ ] Version creation time (< 5 seconds)
- [ ] Data migration success rate (100%)
- [ ] Zero data loss during migration

### Business Metrics
- [ ] User adoption rate (80% within 2 weeks)
- [ ] Approval workflow efficiency (50% reduction in approval time)
- [ ] Sample quality improvement (measurable through audit results)
- [ ] System reliability (99.9% uptime)

## 🔐 Security Considerations

### Data Protection
- [ ] Encryption at rest for sample data
- [ ] Access control validation
- [ ] Audit logging compliance
- [ ] Data retention policy enforcement

### Privacy
- [ ] PII handling in sample data
- [ ] Data anonymization where required
- [ ] Consent management integration
- [ ] Right to deletion compliance

## 📚 Documentation Updates

### Technical Documentation
- [ ] API documentation updates
- [ ] Database schema documentation
- [ ] Architecture documentation
- [ ] Deployment guide updates

### User Documentation
- [ ] User guide updates
- [ ] Training materials
- [ ] FAQ updates
- [ ] Video tutorials

## 🎯 Risk Mitigation

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data migration failure | Medium | High | Comprehensive testing, backup strategy |
| Performance degradation | Low | Medium | Performance testing, monitoring |
| Integration issues | Medium | Medium | Thorough integration testing |

### Business Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| User resistance | Low | Medium | Training, change management |
| Approval workflow disruption | Medium | High | Parallel testing, staged rollout |
| Data quality issues | Low | High | Validation scripts, monitoring |

## 🔄 Post-Implementation

### Monitoring
- [ ] Performance monitoring setup
- [ ] Error tracking implementation
- [ ] User behavior analytics
- [ ] System health dashboards

### Maintenance
- [ ] Regular data cleanup jobs
- [ ] Version history archival
- [ ] Performance optimization reviews
- [ ] Security updates

### Continuous Improvement
- [ ] User feedback collection
- [ ] Performance optimization
- [ ] Feature enhancement planning
- [ ] Technical debt reduction

## 📞 Support Plan

### Go-Live Support
- [ ] 24/7 support team availability
- [ ] Escalation procedures
- [ ] Hot-fix deployment process
- [ ] Communication plan

### Training
- [ ] Administrator training sessions
- [ ] End-user training materials
- [ ] Support team knowledge transfer
- [ ] Documentation reviews

---

## 📝 Approval Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Technical Lead | | | |
| Product Owner | | | |
| Database Administrator | | | |
| QA Lead | | | |
| DevOps Lead | | | |

---

*This implementation plan serves as a comprehensive guide for the Sample Selection system migration. Regular reviews and updates will ensure successful delivery.*