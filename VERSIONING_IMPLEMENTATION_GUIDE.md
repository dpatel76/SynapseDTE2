# Enterprise Versioning Implementation Guide

## Overview

This guide provides step-by-step implementation instructions for the new versioning architecture while maintaining 100% backward compatibility with the existing system.

## Implementation Approach

### Zero-Downtime Strategy

1. **Parallel Running**: New tables run alongside existing ones
2. **Dual Write**: Write to both old and new tables during transition
3. **Read Migration**: Gradually migrate reads to new tables
4. **Cleanup**: Remove old tables after verification

## Phase 1: Foundation Implementation (Weeks 1-2)

### 1.1 Create Enhanced Versioning Base

```python
# app/models/versioning_enhanced.py
from app.models.versioning import VersionedMixin
from app.models.base import CustomPKModel
from sqlalchemy import Column, String, Boolean, Enum, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
import enum

class VersioningType(str, enum.Enum):
    FULL = "full"
    AUDIT_ONLY = "audit_only"

class PhaseConfig:
    """Configuration for phase-specific versioning"""
    PHASE_CONFIGS = {
        "Planning": {
            "versioning_type": VersioningType.FULL,
            "approval_required": True,
            "approver_role": "tester",
            "data_model": "PlanningPhaseVersion"
        },
        "Data Profiling": {
            "versioning_type": VersioningType.FULL,
            "approval_required": True,
            "approver_role": "report_owner",
            "data_model": "DataProfilingVersion"
        },
        "Scoping": {
            "versioning_type": VersioningType.FULL,
            "approval_required": True,
            "approver_role": "report_owner",
            "data_model": "ScopingVersion"
        },
        "Sample Selection": {
            "versioning_type": VersioningType.FULL,
            "approval_required": True,
            "approver_role": "report_owner",
            "data_model": "SampleSelectionVersion"
        },
        "Data Owner ID": {
            "versioning_type": VersioningType.AUDIT_ONLY,
            "approval_required": False,
            "data_model": "DataOwnerAssignment"
        },
        "Request Info": {
            "versioning_type": VersioningType.AUDIT_ONLY,
            "approval_required": False,
            "data_model": "DocumentSubmission"
        },
        "Test Execution": {
            "versioning_type": VersioningType.AUDIT_ONLY,
            "approval_required": False,
            "data_model": "TestExecutionAudit"
        },
        "Observation Management": {
            "versioning_type": VersioningType.FULL,
            "approval_required": True,
            "approver_role": "report_owner",
            "data_model": "ObservationVersion"
        }
    }

class EnhancedVersionedMixin(VersionedMixin):
    """Enhanced versioning mixin with phase awareness"""
    
    __abstract__ = True
    
    # Phase context
    phase_name = Column(String(50), nullable=False)
    phase_version_type = Column(Enum(VersioningType), nullable=False)
    
    # Enhanced relationships
    master_record_id = Column(UUID)  # Links all versions of same entity
    
    @property
    def phase_config(self):
        return PhaseConfig.PHASE_CONFIGS.get(self.phase_name, {})
    
    def can_be_approved_by(self, user):
        """Check if user can approve this version"""
        if not self.phase_config.get('approval_required'):
            return False
        
        approver_role = self.phase_config.get('approver_role')
        if approver_role == 'tester':
            return user.role in ['Test Lead', 'Test Manager', 'Tester']
        elif approver_role == 'report_owner':
            # Check if user is assigned as report owner
            return self._is_report_owner(user)
        
        return False
```

### 1.2 Create Unified Service Layer

```python
# app/services/versioning_service.py
from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.versioning_enhanced import PhaseConfig, VersioningType
from app.core.database import get_db

class UnifiedVersioningService:
    """Enterprise service for consistent versioning operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.phase_config = PhaseConfig()
    
    async def create_version(
        self, 
        phase: str, 
        cycle_id: UUID, 
        report_id: UUID, 
        user_id: int, 
        data: Dict[str, Any],
        parent_version_id: Optional[UUID] = None
    ) -> UUID:
        """Create new version for any phase"""
        config = self.phase_config.PHASE_CONFIGS.get(phase)
        if not config:
            raise ValueError(f"Unknown phase: {phase}")
        
        if config['versioning_type'] == VersioningType.FULL:
            return await self._create_full_version(
                phase, cycle_id, report_id, user_id, data, parent_version_id
            )
        else:
            return await self._create_audit_record(
                phase, cycle_id, report_id, user_id, data
            )
    
    async def _create_full_version(
        self,
        phase: str,
        cycle_id: UUID,
        report_id: UUID,
        user_id: int,
        data: Dict[str, Any],
        parent_version_id: Optional[UUID] = None
    ) -> UUID:
        """Create a full version with complete versioning support"""
        # Dynamic model loading
        model_name = self.phase_config.PHASE_CONFIGS[phase]['data_model']
        model_class = self._get_model_class(model_name)
        
        # Get current version number
        current_version = await self._get_latest_version(
            model_class, cycle_id, report_id
        )
        version_number = (current_version.version_number + 1) if current_version else 1
        
        # Create new version
        new_version = model_class(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name=phase,
            phase_version_type=VersioningType.FULL,
            version_number=version_number,
            version_status='draft',
            parent_version_id=parent_version_id or (current_version.version_id if current_version else None),
            version_created_by=user_id,
            **data
        )
        
        self.db.add(new_version)
        await self.db.commit()
        
        # Handle version-specific data (e.g., decisions, rules)
        await self._handle_phase_specific_data(phase, new_version, data)
        
        return new_version.version_id
    
    async def approve_version(
        self,
        phase: str,
        version_id: UUID,
        user_id: int,
        notes: Optional[str] = None
    ) -> bool:
        """Approve a version"""
        config = self.phase_config.PHASE_CONFIGS.get(phase)
        if not config or not config.get('approval_required'):
            raise ValueError(f"Phase {phase} does not support approval")
        
        model_class = self._get_model_class(config['data_model'])
        version = await self.db.get(model_class, version_id)
        
        if not version:
            raise ValueError(f"Version {version_id} not found")
        
        # Check permissions
        user = await self.db.get(User, user_id)
        if not version.can_be_approved_by(user):
            raise PermissionError(f"User {user_id} cannot approve this version")
        
        # Update version status
        version.version_status = 'approved'
        version.version_reviewed_by = user_id
        version.version_reviewed_at = datetime.utcnow()
        version.version_review_notes = notes
        
        # Mark previous versions as superseded
        await self._mark_previous_versions_superseded(
            model_class, version.cycle_id, version.report_id, version.version_id
        )
        
        await self.db.commit()
        return True
```

### 1.3 Backward Compatibility Layer

```python
# app/api/v1/compatibility/versioning_adapter.py
from typing import Dict, Any
from app.services.versioning_service import UnifiedVersioningService

class VersioningCompatibilityAdapter:
    """Adapter to maintain backward compatibility with existing APIs"""
    
    def __init__(self, versioning_service: UnifiedVersioningService):
        self.versioning_service = versioning_service
    
    async def create_report_attribute(self, attribute_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibility method for existing report attribute creation"""
        # Map old structure to new
        version_data = {
            'planning_metadata': {
                'attribute_name': attribute_data.get('attribute_name'),
                'attribute_type': attribute_data.get('attribute_type'),
                'description': attribute_data.get('description')
            }
        }
        
        # Create version using new system
        version_id = await self.versioning_service.create_version(
            phase='Planning',
            cycle_id=attribute_data['cycle_id'],
            report_id=attribute_data['report_id'],
            user_id=attribute_data['created_by'],
            data=version_data
        )
        
        # Create attribute decision
        decision_data = {
            'attribute_id': attribute_data.get('attribute_id'),
            'attribute_data': attribute_data,
            'decision_type': 'include',
            'decision_reason': 'Initial creation'
        }
        
        # Return in old format
        return {
            'attribute_id': attribute_data.get('attribute_id'),
            'version_number': 1,
            'is_latest_version': True,
            **attribute_data
        }
    
    async def create_sample_set(self, sample_set_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibility method for existing sample set creation"""
        # Convert sample set to new versioning structure
        samples = sample_set_data.pop('samples', [])
        
        version_data = {
            'selection_criteria': sample_set_data.get('selection_criteria'),
            'target_sample_size': len(samples),
            'generation_methods': [sample_set_data.get('generation_method', 'manual')]
        }
        
        version_id = await self.versioning_service.create_version(
            phase='Sample Selection',
            cycle_id=sample_set_data['cycle_id'],
            report_id=sample_set_data['report_id'],
            user_id=sample_set_data['created_by'],
            data=version_data
        )
        
        # Create sample decisions
        for sample in samples:
            await self._create_sample_decision(version_id, sample, sample_set_data['created_by'])
        
        # Return in old format
        return {
            'set_id': version_id,  # Use version_id as set_id for compatibility
            'version_number': 1,
            'is_latest_version': True,
            **sample_set_data
        }
```

### 1.4 Migration Scripts

```python
# migrations/versioning_migration_001.py
"""
Migration to create new versioning tables alongside existing ones
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create planning phase versions table
    op.create_table(
        'planning_phase_versions',
        sa.Column('version_id', postgresql.UUID(), nullable=False),
        sa.Column('cycle_id', postgresql.UUID(), nullable=False),
        sa.Column('report_id', postgresql.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', sa.String(20), nullable=False),
        sa.Column('phase_name', sa.String(50), nullable=False),
        sa.Column('phase_version_type', sa.String(20), nullable=False),
        sa.Column('parent_version_id', postgresql.UUID()),
        sa.Column('master_record_id', postgresql.UUID()),
        sa.Column('planning_metadata', postgresql.JSONB()),
        # ... other versioning fields
        sa.PrimaryKeyConstraint('version_id'),
        sa.UniqueConstraint('cycle_id', 'report_id', 'version_number')
    )
    
    # Create attribute decisions table
    op.create_table(
        'attribute_decisions',
        sa.Column('decision_id', postgresql.UUID(), nullable=False),
        sa.Column('planning_version_id', postgresql.UUID(), nullable=False),
        sa.Column('attribute_id', postgresql.UUID(), nullable=False),
        sa.Column('attribute_data', postgresql.JSONB(), nullable=False),
        sa.Column('decision_type', sa.String(20)),
        sa.Column('decision_reason', sa.Text()),
        sa.Column('carried_from_version_id', postgresql.UUID()),
        sa.PrimaryKeyConstraint('decision_id'),
        sa.ForeignKeyConstraint(['planning_version_id'], ['planning_phase_versions.version_id'])
    )
    
    # Create indexes
    op.create_index('idx_planning_active', 'planning_phase_versions', 
                    ['cycle_id', 'report_id', 'version_status'])
    
    # Repeat for other phase tables...

def downgrade():
    op.drop_table('attribute_decisions')
    op.drop_table('planning_phase_versions')
    # ... drop other tables
```

## Phase 2: Data Migration Strategy

### 2.1 Dual Write Implementation

```python
# app/services/dual_write_service.py
class DualWriteService:
    """Service to write to both old and new tables during migration"""
    
    def __init__(self, db: Session):
        self.db = db
        self.old_service = LegacyService(db)
        self.new_service = UnifiedVersioningService(db)
    
    async def create_report_attribute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Write to both old and new systems"""
        # Write to old system
        old_result = await self.old_service.create_report_attribute(data)
        
        # Write to new system
        try:
            new_version_id = await self.new_service.create_version(
                phase='Planning',
                cycle_id=data['cycle_id'],
                report_id=data['report_id'],
                user_id=data['created_by'],
                data=self._transform_to_new_format(data)
            )
            
            # Store mapping for reconciliation
            await self._store_migration_mapping(
                old_id=old_result['attribute_id'],
                new_id=new_version_id,
                entity_type='report_attribute'
            )
        except Exception as e:
            # Log error but don't fail - old system is source of truth
            logger.error(f"Failed to write to new system: {e}")
        
        return old_result
```

### 2.2 Progressive Read Migration

```python
# app/services/read_migration_service.py
class ReadMigrationService:
    """Service to progressively migrate reads to new system"""
    
    def __init__(self, db: Session):
        self.db = db
        self.migration_config = self._load_migration_config()
    
    async def get_report_attributes(
        self, 
        cycle_id: UUID, 
        report_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get attributes with progressive migration"""
        
        # Check migration percentage for this phase
        read_from_new = self._should_read_from_new('Planning')
        
        if read_from_new:
            # Read from new system
            versions = await self.new_service.get_current_version(
                'Planning', cycle_id, report_id
            )
            return self._transform_to_old_format(versions)
        else:
            # Read from old system
            return await self.old_service.get_report_attributes(
                cycle_id, report_id
            )
    
    def _should_read_from_new(self, phase: str) -> bool:
        """Determine if we should read from new system"""
        migration_percentage = self.migration_config.get(phase, 0)
        return random.random() < (migration_percentage / 100)
```

## Phase 3: Sample Selection Implementation Example

### 3.1 Enhanced Sample Selection

```python
# app/services/sample_selection_service_v2.py
class SampleSelectionServiceV2:
    """New sample selection service with individual decision tracking"""
    
    async def create_sample_version(
        self,
        cycle_id: UUID,
        report_id: UUID,
        user_id: int,
        samples: List[Dict[str, Any]],
        selection_criteria: Dict[str, Any]
    ) -> UUID:
        """Create new sample selection version"""
        
        # Create the version
        version_data = {
            'selection_criteria': selection_criteria,
            'target_sample_size': len(samples),
            'actual_sample_size': len(samples),
            'generation_methods': self._determine_generation_methods(samples)
        }
        
        version_id = await self.versioning_service.create_version(
            phase='Sample Selection',
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=user_id,
            data=version_data
        )
        
        # Create individual sample decisions
        for sample in samples:
            await self._create_sample_decision(version_id, sample, user_id)
        
        return version_id
    
    async def review_samples(
        self,
        version_id: UUID,
        user_id: int,
        decisions: List[Dict[str, Any]]
    ) -> None:
        """Review and approve/reject individual samples"""
        
        for decision in decisions:
            sample_decision = await self.db.get(
                SampleDecision, decision['decision_id']
            )
            
            sample_decision.decision_status = decision['status']
            sample_decision.decided_by_id = user_id
            sample_decision.decision_timestamp = datetime.utcnow()
            sample_decision.decision_notes = decision.get('notes')
        
        await self.db.commit()
    
    async def create_new_version_from_baseline(
        self,
        cycle_id: UUID,
        report_id: UUID,
        user_id: int,
        parent_version_id: UUID,
        additional_samples: List[Dict[str, Any]]
    ) -> UUID:
        """Create new version carrying forward approved samples"""
        
        # Get approved samples from parent version
        approved_samples = await self._get_approved_samples(parent_version_id)
        
        # Create new version
        version_data = {
            'selection_criteria': await self._get_parent_criteria(parent_version_id),
            'target_sample_size': len(approved_samples) + len(additional_samples),
            'actual_sample_size': len(approved_samples) + len(additional_samples)
        }
        
        new_version_id = await self.versioning_service.create_version(
            phase='Sample Selection',
            cycle_id=cycle_id,
            report_id=report_id,
            user_id=user_id,
            data=version_data,
            parent_version_id=parent_version_id
        )
        
        # Carry forward approved samples
        for sample in approved_samples:
            await self._carry_forward_sample(
                new_version_id, sample, parent_version_id
            )
        
        # Add new samples
        for sample in additional_samples:
            await self._create_sample_decision(
                new_version_id, sample, user_id, 'tester'
            )
        
        return new_version_id
```

## Phase 4: Metrics Implementation

### 4.1 Automatic Metrics Collection

```python
# app/services/metrics_service.py
from app.models.versioning_enhanced import VersioningMetrics

class VersioningMetricsService:
    """Service to automatically collect versioning metrics"""
    
    async def record_version_created(
        self,
        phase: str,
        cycle_id: UUID,
        report_id: UUID,
        version_id: UUID
    ):
        """Record version creation metric"""
        metric = VersioningMetrics(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name=phase,
            metric_type='version_created',
            metric_value=1,
            metric_metadata={
                'version_id': str(version_id),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        self.db.add(metric)
        await self.db.commit()
    
    async def record_approval_time(
        self,
        phase: str,
        cycle_id: UUID,
        report_id: UUID,
        version_id: UUID,
        created_at: datetime,
        approved_at: datetime
    ):
        """Record time taken for approval"""
        time_to_approve = (approved_at - created_at).total_seconds() / 3600  # hours
        
        metric = VersioningMetrics(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_name=phase,
            metric_type='approval_time_hours',
            metric_value=time_to_approve,
            metric_metadata={
                'version_id': str(version_id)
            }
        )
        self.db.add(metric)
        await self.db.commit()
    
    async def get_phase_metrics(
        self,
        phase: str,
        cycle_id: UUID,
        report_id: UUID
    ) -> Dict[str, Any]:
        """Get aggregated metrics for a phase"""
        metrics = await self.db.execute(
            select(VersioningMetrics)
            .where(
                VersioningMetrics.cycle_id == cycle_id,
                VersioningMetrics.report_id == report_id,
                VersioningMetrics.phase_name == phase
            )
        )
        
        return self._aggregate_metrics(metrics.scalars().all())
```

## Phase 5: API Updates

### 5.1 New Unified API Endpoints

```python
# app/api/v1/endpoints/versioning.py
from fastapi import APIRouter, Depends, HTTPException
from app.services.versioning_service import UnifiedVersioningService

router = APIRouter()

@router.post("/phases/{phase_name}/versions")
async def create_version(
    phase_name: str,
    version_data: CreateVersionRequest,
    service: UnifiedVersioningService = Depends(get_versioning_service),
    current_user: User = Depends(get_current_user)
):
    """Create new version for any phase"""
    try:
        version_id = await service.create_version(
            phase=phase_name,
            cycle_id=version_data.cycle_id,
            report_id=version_data.report_id,
            user_id=current_user.user_id,
            data=version_data.data
        )
        
        return {"version_id": version_id, "status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/phases/{phase_name}/versions/current")
async def get_current_version(
    phase_name: str,
    cycle_id: UUID,
    report_id: UUID,
    service: UnifiedVersioningService = Depends(get_versioning_service)
):
    """Get current approved version for a phase"""
    version = await service.get_current_version(
        phase_name, cycle_id, report_id
    )
    
    if not version:
        raise HTTPException(status_code=404, detail="No approved version found")
    
    return version

@router.post("/phases/{phase_name}/versions/{version_id}/approve")
async def approve_version(
    phase_name: str,
    version_id: UUID,
    approval_data: ApprovalRequest,
    service: UnifiedVersioningService = Depends(get_versioning_service),
    current_user: User = Depends(get_current_user)
):
    """Approve a version"""
    try:
        await service.approve_version(
            phase=phase_name,
            version_id=version_id,
            user_id=current_user.user_id,
            notes=approval_data.notes
        )
        
        return {"status": "approved"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
```

## Rollback Procedures

### Emergency Rollback Plan

```python
# scripts/emergency_rollback.py
class EmergencyRollback:
    """Emergency rollback procedures"""
    
    async def rollback_phase(self, phase: str):
        """Rollback a specific phase to old system"""
        # 1. Stop dual writes
        await self.config_service.set_dual_write_enabled(phase, False)
        
        # 2. Switch all reads back to old system
        await self.config_service.set_read_percentage(phase, 0)
        
        # 3. Mark new data as inactive
        await self.mark_new_data_inactive(phase)
        
        # 4. Clear caches
        await self.cache_service.clear_phase_cache(phase)
        
        # 5. Notify monitoring
        await self.notify_rollback(phase)
    
    async def verify_data_integrity(self, phase: str):
        """Verify data integrity between old and new systems"""
        discrepancies = []
        
        # Get all records from both systems
        old_records = await self.get_old_records(phase)
        new_records = await self.get_new_records(phase)
        
        # Compare
        for old_record in old_records:
            new_record = self.find_corresponding_new_record(old_record, new_records)
            if not new_record:
                discrepancies.append({
                    'type': 'missing_in_new',
                    'record': old_record
                })
            elif not self.records_match(old_record, new_record):
                discrepancies.append({
                    'type': 'data_mismatch',
                    'old': old_record,
                    'new': new_record
                })
        
        return discrepancies
```

## Success Criteria

1. **Zero Downtime**: No service interruption during migration
2. **Data Integrity**: 100% data accuracy between old and new systems
3. **Performance**: No degradation in response times
4. **Rollback Ready**: Can rollback any phase within 5 minutes
5. **Audit Complete**: Full audit trail maintained throughout migration

## Monitoring and Alerting

```python
# app/monitoring/versioning_monitor.py
class VersioningMonitor:
    """Monitor versioning system health"""
    
    async def check_dual_write_consistency(self):
        """Ensure dual writes are working correctly"""
        # Check write success rates
        old_writes = await self.get_metric('old_system_writes')
        new_writes = await self.get_metric('new_system_writes')
        
        consistency_rate = new_writes / old_writes if old_writes > 0 else 0
        
        if consistency_rate < 0.99:  # Less than 99% consistency
            await self.alert(
                level='critical',
                message=f'Dual write consistency below threshold: {consistency_rate:.2%}'
            )
    
    async def check_migration_progress(self):
        """Monitor migration progress by phase"""
        for phase in PhaseConfig.PHASE_CONFIGS.keys():
            progress = await self.get_migration_progress(phase)
            
            await self.record_metric(
                f'migration_progress_{phase}',
                progress
            )
```

## Conclusion

This implementation guide provides a complete, enterprise-grade approach to migrating the versioning system while ensuring:

1. **Zero downtime** through parallel running
2. **Data integrity** through dual writes and verification
3. **Rollback capability** at any point
4. **Performance monitoring** throughout migration
5. **Backward compatibility** for all existing APIs

The phased approach allows for careful validation at each step, ensuring a smooth transition to the new versioning architecture.