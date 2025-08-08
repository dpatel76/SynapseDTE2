# Database Optimization Plan for Testing Workflow

## Executive Summary

The current database design has evolved organically, resulting in:
- **3 different versioning systems** across the codebase
- **Redundant phase-specific tables** with similar structures
- **Inconsistent approval tracking** mechanisms
- **Sample selection still using sample sets** instead of versioned decisions

This plan proposes a unified approach that will reduce complexity, improve maintainability, and provide better traceability.

## Current Problems Identified

### 1. Versioning Inconsistency

| Component | Versioning Method | Issues |
|-----------|------------------|---------|
| Report Attributes | Custom (master_attribute_id) | Duplicate code, complex queries |
| Sample Sets | Custom (master_set_id) | Doesn't track individual decisions |
| VersionedMixin | Centralized system | Underutilized despite being well-designed |
| Phase Tables | Various approaches | No standard pattern |

### 2. Sample Selection Problems

**Current State:**
```
sample_sets (entire set versioned)
  └── sample_records (no versioning)
       └── approval tracked at set level only
```

**Problems:**
- Can't track which samples were tester-recommended vs owner-added
- No lineage when creating new versions
- Approvals are all-or-nothing at set level

### 3. Phase Table Proliferation

We have **10+ phase-specific tables** with similar structures:
- data_profiling_phases
- scoping_phases  
- sample_selection_phases
- request_info_phases
- test_execution_phases
- observation_management_phases
- test_report_phases

Each duplicates:
- Status tracking
- Date fields
- Progress tracking
- Approval workflows

## Proposed Optimizations

### 1. Adopt Unified Versioning System

**Use the existing VersionedMixin for ALL versioned entities:**

```python
# Before: Custom versioning
class ReportAttribute(Base):
    master_attribute_id = Column(UUID)
    version_number = Column(Integer)
    is_latest_version = Column(Boolean)
    # ... duplicate versioning logic

# After: Standardized versioning
class ReportAttribute(Base, VersionedMixin):
    __versioned__ = True
    # Inherits all versioning fields and logic
```

### 2. Redesign Sample Selection

**Move from set-based to decision-based versioning:**

```python
# New approach tracks individual sample decisions
class SampleSelectionVersion(Base, VersionedMixin):
    """Represents a version of sample selection for a report"""
    cycle_id = Column(UUID)
    report_id = Column(UUID)
    
class SampleDecision(Base):
    """Individual sample with decision tracking"""
    version_id = Column(UUID, ForeignKey('sample_selection_versions.id'))
    sample_data = Column(JSONB)
    
    # Track recommendation source
    recommendation_source = Column(Enum('tester', 'llm', 'manual', 'carried_forward'))
    recommended_by = Column(Integer, ForeignKey('users.user_id'))
    
    # Track approval decision
    decision_status = Column(Enum('pending', 'approved', 'rejected', 'modified'))
    decided_by = Column(Integer, ForeignKey('users.user_id'))
    
    # Track lineage
    carried_from_version_id = Column(UUID)
    carried_from_decision_id = Column(UUID)
```

**Benefits:**
- Track tester recommendations separately from approvals
- Maintain lineage across versions
- Support partial approvals/rejections
- Clear audit trail of who recommended what

### 3. Consolidate Phase Tables

**Replace 10+ phase tables with flexible structure:**

```python
class WorkflowPhaseData(Base, VersionedMixin):
    """Unified storage for all phase data"""
    cycle_id = Column(UUID)
    report_id = Column(UUID)
    phase_name = Column(String(50))
    
    # Flexible data storage
    phase_data = Column(JSONB)
    
    # Common fields
    phase_status = Column(Enum(PhaseStatus))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    __table_args__ = (
        UniqueConstraint('cycle_id', 'report_id', 'phase_name', 'version_number'),
    )
```

**Phase-specific data stored in JSONB:**
```json
{
  "data_profiling": {
    "files_uploaded": ["file1.csv", "file2.csv"],
    "rules_generated": 25,
    "validation_results": {...}
  }
}
```

### 4. Unified Artifact Tagging

**Create central registry of approved artifacts:**

```python
class ApprovedArtifact(Base):
    """Central registry of all approved artifacts"""
    cycle_id = Column(UUID)
    report_id = Column(UUID)
    phase_name = Column(String(50))
    artifact_type = Column(String(50))  # 'samples', 'attributes', etc.
    
    # Reference to approved version
    reference_table = Column(String(100))
    reference_id = Column(UUID)
    reference_version = Column(Integer)
    
    # Approval metadata
    approved_by = Column(Integer, ForeignKey('users.user_id'))
    approved_at = Column(DateTime)
```

## Implementation Benefits

### 1. Code Reduction
- **Before**: ~3,000 lines of versioning code across models
- **After**: ~300 lines using VersionedMixin
- **Reduction**: 90% less versioning code to maintain

### 2. Query Simplification

**Before**: Complex joins across multiple phase tables
```sql
SELECT * FROM report_attributes ra
JOIN sample_sets ss ON ...
JOIN scoping_phases sp ON ...
JOIN request_info_phases rip ON ...
-- Multiple joins, complex WHERE clauses
```

**After**: Simple, consistent queries
```sql
SELECT * FROM workflow_phase_data
WHERE cycle_id = :cycle_id 
  AND phase_name = :phase_name
  AND version_status = 'approved'
```

### 3. Performance Improvements
- Fewer tables = fewer indexes to maintain
- JSONB allows indexing specific fields as needed
- Consistent query patterns = better optimizer plans

### 4. Maintainability
- Single versioning system to debug
- Consistent patterns across all phases
- Easier to add new phases without schema changes

## Migration Plan

### Phase 1: Preparation (Week 1)
1. Create new tables alongside existing ones
2. Add database triggers to sync data during transition
3. Update VersionedMixin to handle all use cases

### Phase 2: Backend Migration (Weeks 2-3)
1. Update models to use new structure
2. Create compatibility layer for existing APIs
3. Migrate services one phase at a time

### Phase 3: Data Migration (Week 4)
1. Migrate historical data to new structure
2. Verify data integrity
3. Update all foreign key relationships

### Phase 4: Frontend Updates (Week 5)
1. Update API calls to use new endpoints
2. Simplify frontend state management
3. Remove legacy code

### Phase 5: Cleanup (Week 6)
1. Remove old tables
2. Drop compatibility layer
3. Performance optimization

## Risk Mitigation

1. **Data Loss**: Full backups before each migration phase
2. **Downtime**: Use blue-green deployment for zero downtime
3. **Compatibility**: Maintain API compatibility during transition
4. **Performance**: Load test new structure before full rollout

## Specific Sample Selection Example

### Current Problematic Flow:
1. Tester recommends 100 samples (creates sample_set v1)
2. Report owner rejects 20, approves 80, requests 10 more
3. System creates entirely new sample_set v2
4. No clear tracking of which 80 were originally recommended

### New Improved Flow:
1. Version 1 created:
   - 100 samples with `recommendation_source = 'tester'`
   - All have `decision_status = 'pending'`

2. Report owner reviews:
   - 80 samples: `decision_status = 'approved'`
   - 20 samples: `decision_status = 'rejected'`
   - Requests new version for additions

3. Version 2 created:
   - 80 approved samples automatically carried forward
   - `carried_from_version_id` = v1
   - Tester adds 10 new samples
   - Clear lineage and attribution maintained

## Conclusion

This optimization plan addresses the core issues:
1. **Standardizes versioning** across all entities
2. **Fixes sample selection** to track individual decisions
3. **Reduces complexity** by consolidating phase tables
4. **Improves traceability** with unified artifact tagging

The migration can be done incrementally with minimal risk, and the benefits include:
- 90% reduction in versioning code
- Clearer data lineage
- Better performance
- Easier maintenance
- Simplified queries

The investment in this refactoring will pay dividends in reduced bugs, faster feature development, and better data integrity.