# Data Owner LOB Assignment Implementation Plan (Corrected)

## 📋 Executive Summary

This document outlines the corrected implementation plan for the Data Owner LOB Assignment system in SynapseDTE. The plan involves migrating from 10+ legacy tables to a clean **2-table architecture** that properly reflects the business logic: Data Executives assign Data Owners to LOB-Attribute combinations, with version tracking to see changes over time.

## 🎯 Corrected Objectives

1. **Simplify Database Architecture**: Reduce from 10+ tables to 2 core tables
2. **Eliminate Redundancy**: Consolidate multiple overlapping assignment systems
3. **Proper Business Logic**: Data Executive assigns Data Owner to LOB-Attribute combinations
4. **Version Tracking**: Track changes in data owner assignments over time
5. **Remove Irrelevant Features**: No tester decisions, no dual approval model
6. **Leverage Existing Infrastructure**: Use escalation framework for SLA/escalation

## 🏗️ Corrected Database Design

### Current State Analysis

#### Legacy Tables to be Consolidated
- `data_provider_assignments` → eliminated (legacy, wrong terminology)
- `data_owner_assignments` → `cycle_report_data_owner_lob_attribute_assignments` (enhanced)
- `historical_data_provider_assignments` → eliminated (use versions pattern)
- `historical_data_owner_assignments` → eliminated (use versions pattern)
- `attribute_lob_assignments` → integrated into main assignment table
- `data_provider_sla_violations` → eliminated (use escalation framework)
- `data_owner_sla_violations` → eliminated (use escalation framework)
- `data_provider_escalation_log` → eliminated (use escalation framework)
- `data_owner_escalation_log` → eliminated (use escalation framework)
- `data_provider_phase_audit_log` → eliminated (use existing audit infrastructure)
- `data_owner_phase_audit_log` → eliminated (use existing audit infrastructure)
- `data_executive_notifications` → eliminated (deprecated)

**Impact**: 10+ tables → 2 tables (80% reduction)

#### Key Design Changes Based on Corrected Understanding

1. **Proper Terminology**: "Data Owner" not "Data Provider"
2. **Key Business Logic**: Data Executive assigns Data Owner to LOB-Attribute combination
3. **Version Tracking**: Track changes in data owner assignments over time
4. **Key Fields**: phase_id, sample_id, attribute_id, lob_id, data_owner_id
5. **No Dual Decisions**: Only Data Executive makes assignments (no tester involvement)
6. **Use Escalation Framework**: Remove SLA/escalation tracking from this system
7. **Change Tracking**: Ability to see data owner changes per LOB-attribute

### Corrected Architecture

#### 1. `cycle_report_data_owner_lob_attribute_versions`
- **Purpose**: Version management for data owner assignments
- **Key Features**: 
  - Version lifecycle management
  - Temporal workflow integration
  - Assignment summary statistics
  - Data Executive assignment tracking

#### 2. `cycle_report_data_owner_lob_attribute_assignments`
- **Purpose**: Individual data owner assignments to LOB-Attribute combinations
- **Key Features**:
  - LOB-Attribute-Data Owner mapping
  - Data Executive assignment information
  - Change tracking over time
  - Integration with sample data

## 🔄 Implementation Details

### Database Schema

#### Complete Schema Definitions
```sql
-- Table 1: Data Owner LOB Assignment Version Management
CREATE TABLE cycle_report_data_owner_lob_attribute_versions (
    -- Primary Key
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Phase Integration (only phase_id needed)
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id),
    
    -- Version Management
    version_number INTEGER NOT NULL,
    version_status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (version_status IN ('draft', 'active', 'superseded')),
    parent_version_id UUID REFERENCES cycle_report_data_owner_lob_attribute_versions(version_id),
    
    -- Temporal Workflow Context
    workflow_execution_id VARCHAR(255),
    workflow_run_id VARCHAR(255),
    
    -- Assignment Summary
    total_lob_attributes INTEGER DEFAULT 0,
    assigned_lob_attributes INTEGER DEFAULT 0,
    unassigned_lob_attributes INTEGER DEFAULT 0,
    
    -- Data Executive Information
    data_executive_id INTEGER NOT NULL REFERENCES users(user_id),
    assignment_batch_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assignment_notes TEXT,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(phase_id, version_number)
);

-- Table 2: Individual Data Owner LOB Attribute Assignments
CREATE TABLE cycle_report_data_owner_lob_attribute_assignments (
    -- Primary Key
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Version Reference
    version_id UUID NOT NULL REFERENCES cycle_report_data_owner_lob_attribute_versions(version_id) ON DELETE CASCADE,
    
    -- Core Business Keys
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    sample_id INTEGER NOT NULL REFERENCES cycle_report_sample_selection_samples(sample_id),
    attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(attribute_id),
    lob_id INTEGER NOT NULL REFERENCES lobs(lob_id),
    
    -- Data Owner Assignment
    data_owner_id INTEGER REFERENCES users(user_id), -- Can be NULL if unassigned
    
    -- Data Executive Assignment Information
    data_executive_id INTEGER NOT NULL REFERENCES users(user_id),
    assigned_by_data_executive_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assignment_rationale TEXT,
    
    -- Change Tracking
    previous_data_owner_id INTEGER REFERENCES users(user_id), -- Track changes
    change_reason TEXT,
    
    -- Status
    assignment_status VARCHAR(50) NOT NULL DEFAULT 'assigned' CHECK (assignment_status IN ('assigned', 'unassigned', 'changed', 'confirmed')),
    
    -- Data Owner Response (if applicable)
    data_owner_acknowledged BOOLEAN DEFAULT FALSE,
    data_owner_acknowledged_at TIMESTAMP WITH TIME ZONE,
    data_owner_response_notes TEXT,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(version_id, phase_id, sample_id, attribute_id, lob_id)
);

-- Indexes for Performance
CREATE INDEX idx_cycle_report_data_owner_lob_attribute_versions_phase ON cycle_report_data_owner_lob_attribute_versions(phase_id);
CREATE INDEX idx_cycle_report_data_owner_lob_attribute_versions_status ON cycle_report_data_owner_lob_attribute_versions(version_status);
CREATE INDEX idx_cycle_report_data_owner_lob_attribute_versions_data_executive ON cycle_report_data_owner_lob_attribute_versions(data_executive_id);

CREATE INDEX idx_cycle_report_data_owner_lob_attribute_assignments_version ON cycle_report_data_owner_lob_attribute_assignments(version_id);
CREATE INDEX idx_cycle_report_data_owner_lob_attribute_assignments_phase ON cycle_report_data_owner_lob_attribute_assignments(phase_id);
CREATE INDEX idx_cycle_report_data_owner_lob_attribute_assignments_sample ON cycle_report_data_owner_lob_attribute_assignments(sample_id);
CREATE INDEX idx_cycle_report_data_owner_lob_attribute_assignments_attribute ON cycle_report_data_owner_lob_attribute_assignments(attribute_id);
CREATE INDEX idx_cycle_report_data_owner_lob_attribute_assignments_lob ON cycle_report_data_owner_lob_attribute_assignments(lob_id);
CREATE INDEX idx_cycle_report_data_owner_lob_attribute_assignments_data_owner ON cycle_report_data_owner_lob_attribute_assignments(data_owner_id);
CREATE INDEX idx_cycle_report_data_owner_lob_attribute_assignments_data_executive ON cycle_report_data_owner_lob_attribute_assignments(data_executive_id);
CREATE INDEX idx_cycle_report_data_owner_lob_attribute_assignments_status ON cycle_report_data_owner_lob_attribute_assignments(assignment_status);
```

### Model Implementation

#### Data Owner LOB Assignment Version Model
```python
class DataOwnerLOBAttributeVersion(CustomPKModel, AuditMixin):
    __tablename__ = 'cycle_report_data_owner_lob_attribute_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    workflow_activity_id = Column(Integer, ForeignKey('workflow_activities.activity_id'))
    
    # Version Management
    version_number = Column(Integer, nullable=False)
    version_status = Column(String(50), default='draft')
    parent_version_id = Column(UUID, ForeignKey('cycle_report_data_owner_lob_attribute_versions.version_id'))
    
    # Temporal Workflow Context
    workflow_execution_id = Column(String(255))
    workflow_run_id = Column(String(255))
    
    # Assignment Summary
    total_lob_attributes = Column(Integer, default=0)
    assigned_lob_attributes = Column(Integer, default=0)
    unassigned_lob_attributes = Column(Integer, default=0)
    
    # Data Executive Information
    data_executive_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    assignment_batch_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    assignment_notes = Column(Text)
    
    # Relationships
    assignments = relationship("DataOwnerLOBAttributeAssignment", back_populates="version")
    phase = relationship("WorkflowPhase")
    data_executive = relationship("User", foreign_keys=[data_executive_id])
    parent_version = relationship("DataOwnerLOBAttributeVersion", remote_side=[version_id])

class DataOwnerLOBAttributeAssignment(CustomPKModel, AuditMixin):
    __tablename__ = 'cycle_report_data_owner_lob_attribute_assignments'
    
    assignment_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('cycle_report_data_owner_lob_attribute_versions.version_id'), nullable=False)
    
    # Core Business Keys
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    sample_id = Column(Integer, ForeignKey('cycle_report_sample_selection_samples.sample_id'), nullable=False)
    attribute_id = Column(Integer, ForeignKey('cycle_report_planning_attributes.attribute_id'), nullable=False)
    lob_id = Column(Integer, ForeignKey('lobs.lob_id'), nullable=False)
    
    # Data Owner Assignment
    data_owner_id = Column(Integer, ForeignKey('users.user_id'))  # Can be NULL
    
    # Data Executive Assignment Information
    data_executive_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    assigned_by_data_executive_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    assignment_rationale = Column(Text)
    
    # Change Tracking
    previous_data_owner_id = Column(Integer, ForeignKey('users.user_id'))
    change_reason = Column(Text)
    
    # Status
    assignment_status = Column(String(50), default='assigned')
    
    # Data Owner Response
    data_owner_acknowledged = Column(Boolean, default=False)
    data_owner_acknowledged_at = Column(DateTime(timezone=True))
    data_owner_response_notes = Column(Text)
    
    # Relationships
    version = relationship("DataOwnerLOBAttributeVersion", back_populates="assignments")
    phase = relationship("WorkflowPhase")
    sample = relationship("SampleSelectionSample")
    attribute = relationship("PlanningAttribute")
    lob = relationship("LOB")
    data_owner = relationship("User", foreign_keys=[data_owner_id])
    previous_data_owner = relationship("User", foreign_keys=[previous_data_owner_id])
    data_executive = relationship("User", foreign_keys=[data_executive_id])
```

## Service Layer Implementation

### Data Owner LOB Assignment Service
```python
# app/services/data_owner_lob_assignment_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_owner_lob_assignment import (
    DataOwnerLOBAttributeVersion, 
    DataOwnerLOBAttributeAssignment
)
from app.core.database import get_async_session
from app.core.exceptions import ResourceNotFoundError, ValidationError


class DataOwnerLOBAssignmentService:
    """Service for managing data owner LOB attribute assignments by data executives"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_version(
        self, 
        phase_id: int,
        data_executive_id: int,
        assignment_notes: Optional[str] = None
    ) -> DataOwnerLOBAttributeVersion:
        """Create a new data owner LOB assignment version"""
        
        # Check if active version already exists
        existing_active = await self.db.execute(
            select(DataOwnerLOBAttributeVersion)
            .where(
                and_(
                    DataOwnerLOBAttributeVersion.phase_id == phase_id,
                    DataOwnerLOBAttributeVersion.version_status == 'active'
                )
            )
        )
        
        existing_version = existing_active.scalar_one_or_none()
        parent_version_id = None
        version_number = 1
        
        if existing_version:
            # Mark existing version as superseded
            existing_version.version_status = 'superseded'
            parent_version_id = existing_version.version_id
            version_number = existing_version.version_number + 1
        
        version = DataOwnerLOBAttributeVersion(
            phase_id=phase_id,
            version_number=version_number,
            version_status='active',
            parent_version_id=parent_version_id,
            data_executive_id=data_executive_id,
            assignment_batch_date=datetime.utcnow(),
            assignment_notes=assignment_notes,
            created_by_id=data_executive_id
        )
        
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        
        return version
    
    async def assign_data_owner_to_lob_attribute(
        self,
        version_id: str,
        phase_id: int,
        sample_id: int,
        attribute_id: int,
        lob_id: int,
        data_owner_id: Optional[int],
        assignment_rationale: Optional[str],
        data_executive_id: int
    ) -> DataOwnerLOBAttributeAssignment:
        """Assign a data owner to a LOB-Attribute combination"""
        
        version = await self._get_version_by_id(version_id)
        if version.version_status != 'active':
            raise ValidationError("Can only assign to active versions")
        
        # Check if assignment already exists
        existing_assignment = await self.db.execute(
            select(DataOwnerLOBAttributeAssignment)
            .where(
                and_(
                    DataOwnerLOBAttributeAssignment.version_id == version_id,
                    DataOwnerLOBAttributeAssignment.phase_id == phase_id,
                    DataOwnerLOBAttributeAssignment.sample_id == sample_id,
                    DataOwnerLOBAttributeAssignment.attribute_id == attribute_id,
                    DataOwnerLOBAttributeAssignment.lob_id == lob_id
                )
            )
        )
        
        existing = existing_assignment.scalar_one_or_none()
        
        if existing:
            # Update existing assignment (track change)
            previous_data_owner_id = existing.data_owner_id
            existing.previous_data_owner_id = previous_data_owner_id
            existing.data_owner_id = data_owner_id
            existing.assignment_rationale = assignment_rationale
            existing.data_executive_id = data_executive_id
            existing.assigned_by_data_executive_at = datetime.utcnow()
            existing.assignment_status = 'changed' if previous_data_owner_id != data_owner_id else 'assigned'
            existing.change_reason = f"Changed from {previous_data_owner_id} to {data_owner_id}" if previous_data_owner_id != data_owner_id else None
            
            await self.db.commit()
            assignment = existing
        else:
            # Create new assignment
            assignment = DataOwnerLOBAttributeAssignment(
                version_id=version_id,
                phase_id=phase_id,
                sample_id=sample_id,
                attribute_id=attribute_id,
                lob_id=lob_id,
                data_owner_id=data_owner_id,
                data_executive_id=data_executive_id,
                assigned_by_data_executive_at=datetime.utcnow(),
                assignment_rationale=assignment_rationale,
                assignment_status='assigned' if data_owner_id else 'unassigned',
                created_by_id=data_executive_id
            )
            
            self.db.add(assignment)
            await self.db.commit()
            await self.db.refresh(assignment)
        
        # Update version summary
        await self.update_version_summary(version_id)
        
        return assignment
    
    async def bulk_assign_data_owners(
        self,
        version_id: str,
        assignments: List[Dict[str, Any]],
        data_executive_id: int
    ) -> Dict[str, Any]:
        """Bulk assign data owners to multiple LOB-Attribute combinations"""
        
        version = await self._get_version_by_id(version_id)
        if version.version_status != 'active':
            raise ValidationError("Can only assign to active versions")
        
        created_assignments = []
        updated_assignments = []
        errors = []
        
        for assignment_data in assignments:
            try:
                assignment = await self.assign_data_owner_to_lob_attribute(
                    version_id=version_id,
                    phase_id=assignment_data["phase_id"],
                    sample_id=assignment_data["sample_id"],
                    attribute_id=assignment_data["attribute_id"],
                    lob_id=assignment_data["lob_id"],
                    data_owner_id=assignment_data.get("data_owner_id"),
                    assignment_rationale=assignment_data.get("assignment_rationale"),
                    data_executive_id=data_executive_id
                )
                
                if assignment.assignment_status == 'changed':
                    updated_assignments.append(assignment)
                else:
                    created_assignments.append(assignment)
                    
            except Exception as e:
                errors.append({
                    "assignment_data": assignment_data,
                    "error": str(e)
                })
        
        return {
            "version_id": version_id,
            "created_assignments": len(created_assignments),
            "updated_assignments": len(updated_assignments),
            "errors": len(errors),
            "error_details": errors
        }
    
    async def get_lob_attribute_assignments(
        self,
        phase_id: int,
        version_id: Optional[str] = None
    ) -> List[DataOwnerLOBAttributeAssignment]:
        """Get LOB attribute assignments for a phase"""
        
        if version_id:
            version = await self._get_version_by_id(version_id)
        else:
            # Get current active version
            version_result = await self.db.execute(
                select(DataOwnerLOBAttributeVersion)
                .where(
                    and_(
                        DataOwnerLOBAttributeVersion.phase_id == phase_id,
                        DataOwnerLOBAttributeVersion.version_status == 'active'
                    )
                )
            )
            version = version_result.scalar_one_or_none()
            
            if not version:
                return []
        
        result = await self.db.execute(
            select(DataOwnerLOBAttributeAssignment)
            .where(DataOwnerLOBAttributeAssignment.version_id == version.version_id)
            .order_by(
                DataOwnerLOBAttributeAssignment.lob_id,
                DataOwnerLOBAttributeAssignment.attribute_id
            )
        )
        
        return result.scalars().all()
    
    async def get_data_owner_changes(
        self,
        phase_id: int,
        lob_id: Optional[int] = None,
        attribute_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get history of data owner changes for LOB-Attribute combinations"""
        
        # Get all versions for the phase
        versions_result = await self.db.execute(
            select(DataOwnerLOBAttributeVersion)
            .where(DataOwnerLOBAttributeVersion.phase_id == phase_id)
            .order_by(DataOwnerLOBAttributeVersion.version_number)
        )
        versions = versions_result.scalars().all()
        
        changes = []
        
        for version in versions:
            query = select(DataOwnerLOBAttributeAssignment).where(
                DataOwnerLOBAttributeAssignment.version_id == version.version_id
            )
            
            if lob_id:
                query = query.where(DataOwnerLOBAttributeAssignment.lob_id == lob_id)
            if attribute_id:
                query = query.where(DataOwnerLOBAttributeAssignment.attribute_id == attribute_id)
            
            assignments_result = await self.db.execute(query)
            assignments = assignments_result.scalars().all()
            
            for assignment in assignments:
                changes.append({
                    "version_number": version.version_number,
                    "version_date": version.assignment_batch_date,
                    "data_executive_id": version.data_executive_id,
                    "lob_id": assignment.lob_id,
                    "attribute_id": assignment.attribute_id,
                    "sample_id": assignment.sample_id,
                    "data_owner_id": assignment.data_owner_id,
                    "previous_data_owner_id": assignment.previous_data_owner_id,
                    "change_reason": assignment.change_reason,
                    "assignment_status": assignment.assignment_status
                })
        
        return changes
    
    async def acknowledge_assignment(
        self,
        assignment_id: str,
        data_owner_id: int,
        response_notes: Optional[str] = None
    ) -> DataOwnerLOBAttributeAssignment:
        """Data owner acknowledges their assignment"""
        
        assignment = await self._get_assignment_by_id(assignment_id)
        
        if assignment.data_owner_id != data_owner_id:
            raise ValidationError("Only the assigned data owner can acknowledge this assignment")
        
        assignment.data_owner_acknowledged = True
        assignment.data_owner_acknowledged_at = datetime.utcnow()
        assignment.data_owner_response_notes = response_notes
        assignment.assignment_status = 'confirmed'
        
        await self.db.commit()
        
        return assignment
    
    async def update_version_summary(self, version_id: str):
        """Update version summary statistics"""
        
        assignments = await self.db.execute(
            select(DataOwnerLOBAttributeAssignment)
            .where(DataOwnerLOBAttributeAssignment.version_id == version_id)
        )
        assignments = assignments.scalars().all()
        
        version = await self._get_version_by_id(version_id)
        version.total_lob_attributes = len(assignments)
        version.assigned_lob_attributes = sum(1 for a in assignments if a.data_owner_id)
        version.unassigned_lob_attributes = sum(1 for a in assignments if not a.data_owner_id)
        
        await self.db.commit()
    
    async def _get_version_by_id(self, version_id: str) -> DataOwnerLOBAttributeVersion:
        """Get version by ID with error handling"""
        result = await self.db.execute(
            select(DataOwnerLOBAttributeVersion)
            .where(DataOwnerLOBAttributeVersion.version_id == version_id)
        )
        version = result.scalar_one_or_none()
        if not version:
            raise ResourceNotFoundError(f"Version {version_id} not found")
        return version
    
    async def _get_assignment_by_id(self, assignment_id: str) -> DataOwnerLOBAttributeAssignment:
        """Get assignment by ID with error handling"""
        result = await self.db.execute(
            select(DataOwnerLOBAttributeAssignment)
            .where(DataOwnerLOBAttributeAssignment.assignment_id == assignment_id)
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ResourceNotFoundError(f"Assignment {assignment_id} not found")
        return assignment
```

## 📋 Summary

This corrected implementation plan properly reflects the business logic:

### ✅ **Key Corrections Made**

1. **Proper Terminology**: "Data Owner" not "Data Provider"
2. **Correct Table Names**: `cycle_report_data_owner_lob_attribute_*`
3. **Key Business Fields**: phase_id, sample_id, attribute_id, lob_id, data_owner_id
4. **Data Executive Assignment**: Data Executive assigns Data Owners
5. **Change Tracking**: Track changes in data owner assignments over time
6. **No Dual Decisions**: Only Data Executive makes assignments
7. **Remove SLA/Escalation**: Use existing escalation framework
8. **Version Management**: Track assignment changes with proper versioning

### 🏗️ **Architecture Benefits**

- **80% reduction** in table count (10+ → 2 tables)
- **Proper business logic** reflected in data model
- **Change tracking** for data owner assignments
- **Integration** with sample data and LOB information
- **Simplified workflow** with only Data Executive involvement
- **Leverages existing infrastructure** for escalation and audit

### 📍 **Implementation Location**

**`/Users/dineshpatel/code/projects/SynapseDTE/docs/data_owner_lob_implementation_plan_corrected.md`**

This design now properly reflects the actual system requirements and business logic for Data Owner LOB assignments.

---

*Thank you for the correction. This revised design accurately captures the Data Executive → Data Owner → LOB-Attribute assignment workflow with proper change tracking and versioning.*