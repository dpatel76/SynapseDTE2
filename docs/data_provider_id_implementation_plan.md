# Data Provider ID Phase Implementation Plan

## 📋 Executive Summary

This document outlines the comprehensive implementation plan for the new simplified Data Provider ID Phase system in SynapseDTE. The plan involves migrating from 10+ legacy tables to a clean **2-table architecture** that follows the exact same versioning pattern as planning, scoping, sample selection, and data profiling phases, eliminating massive redundancy while maintaining all critical functionality for data provider assignments and LOB management.

## 🎯 Objectives

1. **Simplify Database Architecture**: Reduce from 10+ tables to 2 core tables
2. **Eliminate Redundancy**: Consolidate multiple overlapping assignment systems
3. **Improve Performance**: Eliminate complex joins and optimize queries
4. **Maintain Functionality**: Preserve all data provider assignment capabilities
5. **Ensure Consistency**: Follow exact same patterns as other phases
6. **Reduce Technical Debt**: Simplify codebase and maintenance overhead

## 🏗️ Database Design

### Current State Analysis

#### Legacy Tables to be Consolidated
- `data_provider_assignments` → eliminated (legacy table)
- `data_owner_assignments` → `cycle_report_data_provider_assignments` (enhanced)
- `historical_data_provider_assignments` → eliminated (use versions pattern)
- `historical_data_owner_assignments` → eliminated (use versions pattern)
- `attribute_lob_assignments` → `cycle_report_data_provider_assignments.lob_id` (derived from sample data)
- `data_provider_sla_violations` → eliminated (legacy)
- `data_owner_sla_violations` → eliminated (use application logic)
- `data_provider_escalation_log` → eliminated (legacy)
- `data_owner_escalation_log` → eliminated (use existing audit infrastructure)
- `data_provider_phase_audit_log` → eliminated (legacy)
- `data_owner_phase_audit_log` → eliminated (use existing audit infrastructure)
- `data_executive_notifications` → eliminated (deprecated)

**Impact**: 10+ tables → 2 tables (80% reduction)

#### Key Design Changes Based on Analysis

1. **Unified Versioning Pattern**: Follow exact same pattern as other phases
2. **Eliminate Intermediate Tables**: LOB assignment derived from sample data
3. **Single Assignment Table**: One table for all data provider assignments
4. **Consistent Naming**: Use "data_provider" terminology throughout
5. **Leverage Existing Infrastructure**: Use universal audit and notification systems
6. **Dual Decision Model**: Tester + report owner approval workflow

### New Simplified Architecture

#### 1. `cycle_report_data_provider_versions`
- **Purpose**: Version management and data provider assignment metadata
- **Key Features**: 
  - Version lifecycle management (draft → pending_approval → approved/rejected → superseded)
  - Temporal workflow integration
  - Assignment summary statistics
  - Dual decision model (tester + report owner)

#### 2. `cycle_report_data_provider_assignments`
- **Purpose**: Individual data provider assignments per attribute
- **Key Features**:
  - Direct attribute-to-data-provider mapping
  - LOB information derived from sample data
  - Dual decision model (tester + report owner)
  - SLA and escalation tracking (embedded)
  - Single record per attribute per version

## 🔄 Implementation Details

### Database Schema

#### Complete Schema Definitions
```sql
-- Table 1: Data Provider Assignment Version Management
CREATE TABLE cycle_report_data_provider_versions (
    -- Primary Key
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Phase Integration (only phase_id needed)
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id),
    
    -- Version Management (exact same as other phases)
    version_number INTEGER NOT NULL,
    version_status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (version_status IN ('draft', 'pending_approval', 'approved', 'rejected', 'superseded')),
    parent_version_id UUID REFERENCES cycle_report_data_provider_versions(version_id),
    
    -- Temporal Workflow Context
    workflow_execution_id VARCHAR(255),
    workflow_run_id VARCHAR(255),
    
    -- Assignment Summary
    total_attributes INTEGER DEFAULT 0,
    assigned_attributes INTEGER DEFAULT 0,
    unassigned_attributes INTEGER DEFAULT 0,
    pending_assignments INTEGER DEFAULT 0,
    approved_assignments INTEGER DEFAULT 0,
    rejected_assignments INTEGER DEFAULT 0,
    
    -- SLA Summary
    total_sla_violations INTEGER DEFAULT 0,
    active_escalations INTEGER DEFAULT 0,
    
    -- Dual Decision Model (same as other phases)
    tester_decision VARCHAR(50) CHECK (tester_decision IN ('approve', 'reject', 'request_changes')),
    tester_decided_by INTEGER REFERENCES users(user_id),
    tester_decided_at TIMESTAMP WITH TIME ZONE,
    tester_notes TEXT,
    
    report_owner_decision VARCHAR(50) CHECK (report_owner_decision IN ('approve', 'reject', 'request_changes')),
    report_owner_decided_by INTEGER REFERENCES users(user_id),
    report_owner_decided_at TIMESTAMP WITH TIME ZONE,
    report_owner_notes TEXT,
    
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

-- Table 2: Individual Data Provider Assignments
CREATE TABLE cycle_report_data_provider_assignments (
    -- Primary Key
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Version Reference
    version_id UUID NOT NULL REFERENCES cycle_report_data_provider_versions(version_id) ON DELETE CASCADE,
    
    -- Phase Integration
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- Assignment Details
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(attribute_id),
    data_provider_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- LOB Information (derived from sample data)
    lob_id INTEGER NOT NULL REFERENCES lobs(lob_id),
    lob_assignment_rationale TEXT,
    
    -- Assignment Details
    assignment_rationale TEXT,
    assignment_priority VARCHAR(20) DEFAULT 'medium' CHECK (assignment_priority IN ('low', 'medium', 'high', 'critical')),
    
    -- SLA Tracking (embedded)
    sla_due_date TIMESTAMP WITH TIME ZONE,
    sla_reminder_sent BOOLEAN DEFAULT FALSE,
    sla_violation_count INTEGER DEFAULT 0,
    last_sla_violation_at TIMESTAMP WITH TIME ZONE,
    
    -- Escalation Tracking (embedded)
    escalation_level VARCHAR(20) DEFAULT 'none' CHECK (escalation_level IN ('none', 'level1', 'level2', 'level3')),
    last_escalation_at TIMESTAMP WITH TIME ZONE,
    escalation_notes TEXT,
    
    -- Data Provider Response
    data_provider_response TEXT,
    data_provider_response_at TIMESTAMP WITH TIME ZONE,
    
    -- Dual Decision Model (same as other phases)
    tester_decision VARCHAR(50) CHECK (tester_decision IN ('approve', 'reject', 'request_changes')),
    tester_decided_by INTEGER REFERENCES users(user_id),
    tester_decided_at TIMESTAMP WITH TIME ZONE,
    tester_notes TEXT,
    
    report_owner_decision VARCHAR(50) CHECK (report_owner_decision IN ('approve', 'reject', 'request_changes')),
    report_owner_decided_by INTEGER REFERENCES users(user_id),
    report_owner_decided_at TIMESTAMP WITH TIME ZONE,
    report_owner_notes TEXT,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'confirmed', 'rejected', 'escalated')),
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(version_id, attribute_id),
    UNIQUE(version_id, attribute_id, data_provider_id)
);

-- Indexes for Performance
CREATE INDEX idx_cycle_report_data_provider_versions_phase ON cycle_report_data_provider_versions(phase_id);
CREATE INDEX idx_cycle_report_data_provider_versions_status ON cycle_report_data_provider_versions(version_status);
CREATE INDEX idx_cycle_report_data_provider_versions_parent ON cycle_report_data_provider_versions(parent_version_id);

CREATE INDEX idx_cycle_report_data_provider_assignments_version ON cycle_report_data_provider_assignments(version_id);
CREATE INDEX idx_cycle_report_data_provider_assignments_phase ON cycle_report_data_provider_assignments(phase_id);
CREATE INDEX idx_cycle_report_data_provider_assignments_attribute ON cycle_report_data_provider_assignments(attribute_id);
CREATE INDEX idx_cycle_report_data_provider_assignments_data_provider ON cycle_report_data_provider_assignments(data_provider_id);
CREATE INDEX idx_cycle_report_data_provider_assignments_lob ON cycle_report_data_provider_assignments(lob_id);
CREATE INDEX idx_cycle_report_data_provider_assignments_status ON cycle_report_data_provider_assignments(status);
CREATE INDEX idx_cycle_report_data_provider_assignments_sla ON cycle_report_data_provider_assignments(sla_due_date);
CREATE INDEX idx_cycle_report_data_provider_assignments_escalation ON cycle_report_data_provider_assignments(escalation_level);
```

### Data Consolidation Strategy
```python
async def migrate_data_provider_data():
    """Consolidate data from 10+ tables into unified 2-table structure"""
    
    # 1. Create versions from existing phase contexts
    async for phase in get_data_provider_phases():
        # Get existing assignments for this phase
        existing_assignments = await get_data_owner_assignments_for_phase(phase.phase_id)
        existing_lob_assignments = await get_lob_assignments_for_phase(phase.phase_id)
        
        if not existing_assignments:
            continue
            
        # Create new version
        new_version = DataProviderVersion(
            phase_id=phase.phase_id,
            version_number=1,  # Start fresh
            version_status='approved',  # Assume existing data is approved
            total_attributes=len(existing_assignments),
            assigned_attributes=sum(1 for a in existing_assignments if a.data_provider_id),
            unassigned_attributes=sum(1 for a in existing_assignments if not a.data_provider_id),
            approved_assignments=sum(1 for a in existing_assignments if a.status == 'approved'),
            created_by_id=phase.created_by_id,
            created_at=phase.created_at
        )
        
        await db.add(new_version)
        await db.flush()  # Get version_id
        
        # 2. Migrate assignments with comprehensive metadata
        for old_assignment in existing_assignments:
            # Get LOB assignment
            lob_assignment = next(
                (la for la in existing_lob_assignments if la.attribute_id == old_assignment.attribute_id), 
                None
            )
            
            # Get SLA violations
            sla_violations = await get_sla_violations_for_assignment(old_assignment.assignment_id)
            
            # Get escalation logs
            escalation_logs = await get_escalation_logs_for_assignment(old_assignment.assignment_id)
            
            # Get historical data
            historical_data = await get_historical_assignments(old_assignment.assignment_id)
            
            # Create new assignment
            new_assignment = DataProviderAssignment(
                version_id=new_version.version_id,
                phase_id=phase.phase_id,
                attribute_id=old_assignment.attribute_id,
                data_provider_id=old_assignment.data_provider_id,
                lob_id=lob_assignment.lob_id if lob_assignment else None,
                lob_assignment_rationale=lob_assignment.assignment_rationale if lob_assignment else None,
                assignment_rationale=old_assignment.assignment_rationale if hasattr(old_assignment, 'assignment_rationale') else None,
                assignment_priority=old_assignment.priority if hasattr(old_assignment, 'priority') else 'medium',
                
                # SLA tracking
                sla_due_date=old_assignment.sla_due_date if hasattr(old_assignment, 'sla_due_date') else None,
                sla_reminder_sent=old_assignment.sla_reminder_sent if hasattr(old_assignment, 'sla_reminder_sent') else False,
                sla_violation_count=len(sla_violations),
                last_sla_violation_at=max(sv.created_at for sv in sla_violations) if sla_violations else None,
                
                # Escalation tracking
                escalation_level=escalation_logs[-1].escalation_level if escalation_logs else 'none',
                last_escalation_at=max(el.created_at for el in escalation_logs) if escalation_logs else None,
                escalation_notes='; '.join(el.notes for el in escalation_logs if el.notes) if escalation_logs else None,
                
                # Data provider response
                data_provider_response=old_assignment.response if hasattr(old_assignment, 'response') else None,
                data_provider_response_at=old_assignment.response_at if hasattr(old_assignment, 'response_at') else None,
                
                # Status
                status=old_assignment.status if old_assignment.status else 'pending',
                
                # Audit fields
                created_by_id=old_assignment.assigned_by,
                created_at=old_assignment.assigned_at
            )
            
            await db.add(new_assignment)
        
        # Update version summary
        await update_version_summary(new_version.version_id)
    
    await db.commit()
```

### Model Implementation

#### Data Provider Version Model
```python
class DataProviderVersion(VersionedEntity):
    __tablename__ = 'cycle_report_data_provider_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    workflow_activity_id = Column(Integer, ForeignKey('workflow_activities.activity_id'))
    
    # Version Management (exact same as other phases)
    version_number = Column(Integer, nullable=False)
    version_status = Column(Enum(VersionStatus), default=VersionStatus.DRAFT)
    parent_version_id = Column(UUID, ForeignKey('cycle_report_data_provider_versions.version_id'))
    
    # Temporal Workflow Context
    workflow_execution_id = Column(String(255))
    workflow_run_id = Column(String(255))
    
    # Assignment Summary
    total_attributes = Column(Integer, default=0)
    assigned_attributes = Column(Integer, default=0)
    unassigned_attributes = Column(Integer, default=0)
    pending_assignments = Column(Integer, default=0)
    approved_assignments = Column(Integer, default=0)
    rejected_assignments = Column(Integer, default=0)
    
    # SLA Summary
    total_sla_violations = Column(Integer, default=0)
    active_escalations = Column(Integer, default=0)
    
    # Dual Decision Model (same as other phases)
    tester_decision = Column(String(50))
    tester_decided_by = Column(Integer, ForeignKey('users.user_id'))
    tester_decided_at = Column(DateTime(timezone=True))
    tester_notes = Column(Text)
    
    report_owner_decision = Column(String(50))
    report_owner_decided_by = Column(Integer, ForeignKey('users.user_id'))
    report_owner_decided_at = Column(DateTime(timezone=True))
    report_owner_notes = Column(Text)
    
    # Approval Workflow
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'))
    submitted_at = Column(DateTime(timezone=True))
    approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    
    # Relationships
    assignments = relationship("DataProviderAssignment", back_populates="version")
    phase = relationship("WorkflowPhase")
    parent_version = relationship("DataProviderVersion", remote_side=[version_id])

class DataProviderAssignment(CustomPKModel, AuditMixin):
    __tablename__ = 'cycle_report_data_provider_assignments'
    
    assignment_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('cycle_report_data_provider_versions.version_id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    
    # Assignment Details
    attribute_id = Column(Integer, ForeignKey('cycle_report_planning_attributes.attribute_id'), nullable=False)
    data_provider_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # LOB Information (derived from sample data)
    lob_id = Column(Integer, ForeignKey('lobs.lob_id'), nullable=False)
    lob_assignment_rationale = Column(Text)
    
    # Assignment Details
    assignment_rationale = Column(Text)
    assignment_priority = Column(String(20), default='medium')
    
    # SLA Tracking (embedded)
    sla_due_date = Column(DateTime(timezone=True))
    sla_reminder_sent = Column(Boolean, default=False)
    sla_violation_count = Column(Integer, default=0)
    last_sla_violation_at = Column(DateTime(timezone=True))
    
    # Escalation Tracking (embedded)
    escalation_level = Column(String(20), default='none')
    last_escalation_at = Column(DateTime(timezone=True))
    escalation_notes = Column(Text)
    
    # Data Provider Response
    data_provider_response = Column(Text)
    data_provider_response_at = Column(DateTime(timezone=True))
    
    # Dual Decision Model (same as other phases)
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
    version = relationship("DataProviderVersion", back_populates="assignments")
    attribute = relationship("PlanningAttribute")
    data_provider = relationship("User", foreign_keys=[data_provider_id])
    lob = relationship("LOB")
    phase = relationship("WorkflowPhase")
```

## Service Layer Implementation

### Unified Data Provider Service
```python
# app/services/data_provider_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_provider import (
    DataProviderVersion, 
    DataProviderAssignment,
    VersionStatus
)
from app.core.database import get_async_session
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.tasks.data_provider_tasks import auto_assign_data_providers_task


class DataProviderService:
    """Service for managing data provider assignments and LOB management"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_version(
        self, 
        phase_id: int,
        created_by: int,
        version_description: Optional[str] = None
    ) -> DataProviderVersion:
        """Create a new data provider assignment version"""
        
        # Check if draft version already exists
        existing_draft = await self.db.execute(
            select(DataProviderVersion)
            .where(
                and_(
                    DataProviderVersion.phase_id == phase_id,
                    DataProviderVersion.version_status == VersionStatus.DRAFT
                )
            )
        )
        
        if existing_draft.scalar_one_or_none():
            raise ValidationError("A draft version already exists for this phase")
        
        version = DataProviderVersion(
            phase_id=phase_id,
            version_number=1,  # Will be auto-calculated
            version_status=VersionStatus.DRAFT,
            created_by_id=created_by
        )
        
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        
        return version
    
    async def auto_assign_data_providers(
        self,
        version_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """Auto-assign data providers based on sample data LOB assignments"""
        
        version = await self._get_version_by_id(version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationError("Can only auto-assign for draft versions")
        
        # Get attributes from planning phase
        planning_attributes = await self._get_planning_attributes(version.phase_id)
        
        # Get sample data to derive LOB assignments
        sample_data = await self._get_sample_data(version.phase_id)
        
        assignments_created = []
        
        for attribute in planning_attributes:
            # Derive LOB from sample data
            lob_id = await self._derive_lob_from_sample_data(attribute.attribute_id, sample_data)
            
            if lob_id:
                # Get recommended data provider for this LOB
                data_provider_id = await self._get_recommended_data_provider(lob_id)
                
                if data_provider_id:
                    assignment = DataProviderAssignment(
                        version_id=version_id,
                        phase_id=version.phase_id,
                        attribute_id=attribute.attribute_id,
                        data_provider_id=data_provider_id,
                        lob_id=lob_id,
                        assignment_rationale="Auto-assigned based on sample data LOB",
                        assignment_priority="medium",
                        sla_due_date=datetime.utcnow() + timedelta(days=7),  # Default 7-day SLA
                        status='assigned',
                        created_by_id=user_id
                    )
                    
                    self.db.add(assignment)
                    assignments_created.append(assignment)
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(version_id)
        
        return {
            "version_id": version_id,
            "assignments_created": len(assignments_created),
            "status": "auto_assignment_completed"
        }
    
    async def manual_assign_data_provider(
        self,
        version_id: str,
        attribute_id: int,
        data_provider_id: int,
        lob_id: int,
        assignment_rationale: str,
        user_id: int,
        assignment_priority: str = "medium"
    ) -> DataProviderAssignment:
        """Manually assign a data provider to an attribute"""
        
        version = await self._get_version_by_id(version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationError("Can only assign data providers to draft versions")
        
        # Check if assignment already exists
        existing_assignment = await self.db.execute(
            select(DataProviderAssignment)
            .where(
                and_(
                    DataProviderAssignment.version_id == version_id,
                    DataProviderAssignment.attribute_id == attribute_id
                )
            )
        )
        
        if existing_assignment.scalar_one_or_none():
            raise ValidationError("Assignment already exists for this attribute")
        
        assignment = DataProviderAssignment(
            version_id=version_id,
            phase_id=version.phase_id,
            attribute_id=attribute_id,
            data_provider_id=data_provider_id,
            lob_id=lob_id,
            assignment_rationale=assignment_rationale,
            assignment_priority=assignment_priority,
            sla_due_date=datetime.utcnow() + timedelta(days=7),
            status='assigned',
            created_by_id=user_id
        )
        
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)
        
        # Update version summary
        await self.update_version_summary(version_id)
        
        return assignment
    
    async def update_tester_decision(
        self, 
        assignment_id: str, 
        decision: str,
        notes: Optional[str],
        user_id: int
    ) -> DataProviderAssignment:
        """Update tester decision on a data provider assignment"""
        
        assignment = await self._get_assignment_by_id(assignment_id)
        
        # Verify version is editable
        version = await self._get_version_by_id(assignment.version_id)
        if version.version_status not in [VersionStatus.DRAFT, VersionStatus.PENDING_APPROVAL]:
            raise ValidationError("Cannot update decisions on finalized versions")
        
        assignment.tester_decision = decision
        assignment.tester_notes = notes
        assignment.tester_decided_by = user_id
        assignment.tester_decided_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(assignment.version_id)
        
        return assignment
    
    async def update_report_owner_decision(
        self, 
        assignment_id: str, 
        decision: str,
        notes: Optional[str],
        user_id: int
    ) -> DataProviderAssignment:
        """Update report owner decision on a data provider assignment"""
        
        assignment = await self._get_assignment_by_id(assignment_id)
        
        # Verify version is in pending approval state
        version = await self._get_version_by_id(assignment.version_id)
        if version.version_status != VersionStatus.PENDING_APPROVAL:
            raise ValidationError("Can only make report owner decisions on pending approval versions")
        
        assignment.report_owner_decision = decision
        assignment.report_owner_notes = notes
        assignment.report_owner_decided_by = user_id
        assignment.report_owner_decided_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(assignment.version_id)
        
        return assignment
    
    async def check_sla_violations(self, version_id: str) -> List[Dict[str, Any]]:
        """Check for SLA violations in assignments"""
        
        current_time = datetime.utcnow()
        
        # Get assignments with SLA violations
        violations = await self.db.execute(
            select(DataProviderAssignment)
            .where(
                and_(
                    DataProviderAssignment.version_id == version_id,
                    DataProviderAssignment.sla_due_date < current_time,
                    DataProviderAssignment.status.in_(['assigned', 'pending'])
                )
            )
        )
        
        violation_list = []
        for assignment in violations.scalars().all():
            # Update SLA violation count
            assignment.sla_violation_count += 1
            assignment.last_sla_violation_at = current_time
            
            violation_list.append({
                "assignment_id": assignment.assignment_id,
                "attribute_id": assignment.attribute_id,
                "data_provider_id": assignment.data_provider_id,
                "sla_due_date": assignment.sla_due_date,
                "days_overdue": (current_time - assignment.sla_due_date).days,
                "violation_count": assignment.sla_violation_count
            })
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(version_id)
        
        return violation_list
    
    async def escalate_assignment(
        self,
        assignment_id: str,
        escalation_level: str,
        escalation_notes: str,
        user_id: int
    ) -> DataProviderAssignment:
        """Escalate a data provider assignment"""
        
        assignment = await self._get_assignment_by_id(assignment_id)
        
        assignment.escalation_level = escalation_level
        assignment.last_escalation_at = datetime.utcnow()
        assignment.escalation_notes = escalation_notes
        assignment.status = 'escalated'
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(assignment.version_id)
        
        return assignment
    
    async def submit_for_approval(
        self, 
        version_id: str, 
        submitted_by: int
    ) -> DataProviderVersion:
        """Submit data provider assignment version for report owner approval"""
        
        version = await self._get_version_by_id(version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationError("Only draft versions can be submitted for approval")
        
        # Check if all assignments have tester decisions
        assignments = await self.get_assignments_by_version(version_id)
        pending_assignments = [a for a in assignments if not a.tester_decision]
        
        if pending_assignments:
            raise ValidationError(f"{len(pending_assignments)} assignments still need tester decisions")
        
        version.version_status = VersionStatus.PENDING_APPROVAL
        version.submitted_by_id = submitted_by
        version.submitted_at = datetime.utcnow()
        
        await self.db.commit()
        return version
    
    async def approve_version(
        self, 
        version_id: str, 
        approved_by: int
    ) -> DataProviderVersion:
        """Approve data provider assignment version (report owner action)"""
        
        version = await self._get_version_by_id(version_id)
        if version.version_status != VersionStatus.PENDING_APPROVAL:
            raise ValidationError("Only pending approval versions can be approved")
        
        # Mark previous versions as superseded
        await self.db.execute(
            update(DataProviderVersion)
            .where(DataProviderVersion.phase_id == version.phase_id)
            .where(DataProviderVersion.version_status == VersionStatus.APPROVED)
            .values(version_status=VersionStatus.SUPERSEDED)
        )
        
        # Approve current version
        version.version_status = VersionStatus.APPROVED
        version.approved_by_id = approved_by
        version.approved_at = datetime.utcnow()
        
        await self.db.commit()
        return version
    
    async def get_assignments_by_version(self, version_id: str) -> List[DataProviderAssignment]:
        """Get all assignments for a version"""
        result = await self.db.execute(
            select(DataProviderAssignment)
            .where(DataProviderAssignment.version_id == version_id)
            .order_by(DataProviderAssignment.created_at)
        )
        return result.scalars().all()
    
    async def get_current_version(self, phase_id: int) -> Optional[DataProviderVersion]:
        """Get current approved version for a phase"""
        result = await self.db.execute(
            select(DataProviderVersion)
            .where(
                and_(
                    DataProviderVersion.phase_id == phase_id,
                    DataProviderVersion.version_status == VersionStatus.APPROVED
                )
            )
            .order_by(DataProviderVersion.version_number.desc())
        )
        return result.scalar_one_or_none()
    
    async def update_version_summary(self, version_id: str):
        """Update version summary statistics"""
        assignments = await self.get_assignments_by_version(version_id)
        
        version = await self._get_version_by_id(version_id)
        version.total_attributes = len(assignments)
        version.assigned_attributes = sum(1 for a in assignments if a.data_provider_id)
        version.unassigned_attributes = sum(1 for a in assignments if not a.data_provider_id)
        version.pending_assignments = sum(1 for a in assignments if a.status == 'pending')
        version.approved_assignments = sum(1 for a in assignments if a.status == 'approved')
        version.rejected_assignments = sum(1 for a in assignments if a.status == 'rejected')
        version.total_sla_violations = sum(a.sla_violation_count for a in assignments)
        version.active_escalations = sum(1 for a in assignments if a.escalation_level != 'none')
        
        await self.db.commit()
    
    async def _get_version_by_id(self, version_id: str) -> DataProviderVersion:
        """Get version by ID with error handling"""
        result = await self.db.execute(
            select(DataProviderVersion)
            .where(DataProviderVersion.version_id == version_id)
        )
        version = result.scalar_one_or_none()
        if not version:
            raise ResourceNotFoundError(f"Version {version_id} not found")
        return version
    
    async def _get_assignment_by_id(self, assignment_id: str) -> DataProviderAssignment:
        """Get assignment by ID with error handling"""
        result = await self.db.execute(
            select(DataProviderAssignment)
            .where(DataProviderAssignment.assignment_id == assignment_id)
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ResourceNotFoundError(f"Assignment {assignment_id} not found")
        return assignment
    
    async def _get_planning_attributes(self, phase_id: int) -> List[PlanningAttribute]:
        """Get planning attributes for the same cycle/report"""
        # Implementation depends on your planning phase structure
        pass
    
    async def _get_sample_data(self, phase_id: int) -> List[SampleData]:
        """Get sample data for LOB derivation"""
        # Implementation depends on your sample selection structure
        pass
    
    async def _derive_lob_from_sample_data(self, attribute_id: int, sample_data: List) -> Optional[int]:
        """Derive LOB ID from sample data"""
        # Implementation depends on your sample data structure
        pass
    
    async def _get_recommended_data_provider(self, lob_id: int) -> Optional[int]:
        """Get recommended data provider for a LOB"""
        # Implementation depends on your LOB-to-data-provider mapping
        pass
```

## API Endpoints

### Data Provider Assignment Management
```python
# app/api/v1/endpoints/data_provider.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.data_provider_service import DataProviderService
from app.schemas.data_provider import (
    DataProviderVersionResponse,
    DataProviderAssignmentResponse,
    CreateDataProviderVersionRequest,
    CreateDataProviderAssignmentRequest,
    UpdateTesterDecisionRequest,
    UpdateReportOwnerDecisionRequest
)
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/data-provider/versions", response_model=DataProviderVersionResponse)
async def create_data_provider_version(
    request: CreateDataProviderVersionRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Create initial data provider assignment version"""
    service = DataProviderService(db)
    return await service.create_version(
        phase_id=request.phase_id,
        created_by=current_user.user_id
    )


@router.get("/data-provider/versions/{version_id}", response_model=DataProviderVersionResponse)
async def get_data_provider_version(
    version_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get specific data provider version with all assignments"""
    service = DataProviderService(db)
    return await service.get_version_by_id(version_id)


@router.post("/data-provider/versions/{version_id}/auto-assign")
async def auto_assign_data_providers(
    version_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Auto-assign data providers based on sample data"""
    service = DataProviderService(db)
    return await service.auto_assign_data_providers(
        version_id=version_id,
        user_id=current_user.user_id
    )


@router.post("/data-provider/versions/{version_id}/assignments", response_model=DataProviderAssignmentResponse)
async def create_data_provider_assignment(
    version_id: str,
    request: CreateDataProviderAssignmentRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Manually assign data provider to attribute"""
    service = DataProviderService(db)
    return await service.manual_assign_data_provider(
        version_id=version_id,
        attribute_id=request.attribute_id,
        data_provider_id=request.data_provider_id,
        lob_id=request.lob_id,
        assignment_rationale=request.assignment_rationale,
        user_id=current_user.user_id,
        assignment_priority=request.assignment_priority
    )


@router.put("/data-provider/assignments/{assignment_id}/tester-decision", response_model=DataProviderAssignmentResponse)
async def update_tester_decision(
    assignment_id: str,
    request: UpdateTesterDecisionRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Update tester decision on data provider assignment"""
    service = DataProviderService(db)
    return await service.update_tester_decision(
        assignment_id=assignment_id,
        decision=request.decision,
        notes=request.notes,
        user_id=current_user.user_id
    )


@router.put("/data-provider/assignments/{assignment_id}/report-owner-decision", response_model=DataProviderAssignmentResponse)
async def update_report_owner_decision(
    assignment_id: str,
    request: UpdateReportOwnerDecisionRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Update report owner decision on data provider assignment"""
    service = DataProviderService(db)
    return await service.update_report_owner_decision(
        assignment_id=assignment_id,
        decision=request.decision,
        notes=request.notes,
        user_id=current_user.user_id
    )


@router.post("/data-provider/versions/{version_id}/submit", response_model=DataProviderVersionResponse)
async def submit_version_for_approval(
    version_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Submit data provider assignment version for report owner approval"""
    service = DataProviderService(db)
    return await service.submit_for_approval(
        version_id=version_id,
        submitted_by=current_user.user_id
    )


@router.post("/data-provider/versions/{version_id}/approve", response_model=DataProviderVersionResponse)
async def approve_version(
    version_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Approve data provider assignment version (report owner action)"""
    service = DataProviderService(db)
    return await service.approve_version(
        version_id=version_id,
        approved_by=current_user.user_id
    )


@router.get("/data-provider/phases/{phase_id}/current", response_model=DataProviderVersionResponse)
async def get_current_data_provider_version(
    phase_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get current approved data provider version for a phase"""
    service = DataProviderService(db)
    return await service.get_current_version(phase_id)


@router.get("/data-provider/versions/{version_id}/assignments", response_model=List[DataProviderAssignmentResponse])
async def get_data_provider_assignments(
    version_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get all data provider assignments for a version"""
    service = DataProviderService(db)
    return await service.get_assignments_by_version(version_id)


@router.get("/data-provider/versions/{version_id}/sla-violations")
async def check_sla_violations(
    version_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Check for SLA violations in assignments"""
    service = DataProviderService(db)
    return await service.check_sla_violations(version_id)


@router.post("/data-provider/assignments/{assignment_id}/escalate")
async def escalate_assignment(
    assignment_id: str,
    escalation_level: str,
    escalation_notes: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Escalate a data provider assignment"""
    service = DataProviderService(db)
    return await service.escalate_assignment(
        assignment_id=assignment_id,
        escalation_level=escalation_level,
        escalation_notes=escalation_notes,
        user_id=current_user.user_id
    )
```

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
- [ ] Implement unified data provider service
- [ ] Create assignment management service
- [ ] Build SLA monitoring service
- [ ] Implement escalation workflow
- [ ] Create auto-assignment logic

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

## 🎯 Success Metrics

### Technical Metrics
- [ ] Database query performance improvement (target: 85% faster)
- [ ] Storage space reduction (target: 80% less space)
- [ ] Code complexity reduction (target: 85% fewer lines)
- [ ] Migration success rate (target: 100% data integrity)

### Business Metrics
- [ ] User adoption rate (target: 90% within 2 weeks)
- [ ] Data provider assignment efficiency (target: 60% faster completion)
- [ ] Error rate reduction (target: 70% fewer support tickets)
- [ ] System reliability (target: 99.9% uptime)

## 📋 Summary

This implementation plan provides a comprehensive blueprint for simplifying the Data Provider ID Phase system from 10+ tables to 2 tables (80% reduction) while maintaining all functionality through the dual decision model and embedded SLA/escalation tracking. The plan ensures perfect consistency with the patterns successfully implemented in planning, scoping, sample selection, and data profiling phases.

**Key Benefits:**
- **Architectural Consistency**: Same 2-table versioning pattern across all phases
- **Massive Reduction**: 80% fewer tables to manage
- **Enhanced Performance**: Fewer JOINs and better query optimization
- **Improved Maintainability**: Consistent patterns and reduced technical debt
- **Better Workflow Integration**: Native temporal workflow support
- **Simplified SLA Management**: Embedded SLA tracking without separate tables

The simplified architecture maintains all critical functionality including auto-assignment, manual assignment, SLA monitoring, escalation workflows, and the dual decision model while significantly reducing complexity and improving system maintainability.

---

**Location**: `/Users/dineshpatel/code/projects/SynapseDTE/docs/data_provider_id_implementation_plan.md`