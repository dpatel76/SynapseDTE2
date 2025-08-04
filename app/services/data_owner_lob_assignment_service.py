"""
Data Owner LOB Assignment Service

This service manages the unified data owner LOB assignment system according to the business logic:
- Data Executives assign Data Owners to LOB-Attribute combinations
- Version tracking for assignment changes over time
- No dual approval workflow (only Data Executive assignments)
- Integration with sample data and existing escalation framework
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
from sqlalchemy import select, update, delete, and_, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.data_owner_lob_assignment import (
    DataOwnerLOBAttributeVersion, 
    DataOwnerLOBAttributeMapping,
    VersionStatus,
    AssignmentStatus
)
from app.models.user import User
from app.models.lob import LOB
from app.models.report_attribute import ReportAttribute
from app.models.sample_selection import SampleSelectionSample
from app.models.workflow import WorkflowPhase
from app.core.exceptions import (
    ResourceNotFoundError, 
    ValidationError, 
    ConflictError,
    BusinessLogicError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataOwnerLOBAssignmentService:
    """Service for managing data owner LOB attribute assignments by data executives"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    # Version Management
    async def create_version(
        self, 
        phase_id: int,
        data_executive_id: int,
        assignment_notes: Optional[str] = None,
        workflow_activity_id: Optional[int] = None,
        workflow_execution_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None
    ) -> DataOwnerLOBAttributeVersion:
        """Create a new data owner LOB assignment version"""
        
        # Validate phase exists
        phase_result = await self.db.execute(
            select(WorkflowPhase).where(WorkflowPhase.phase_id == phase_id)
        )
        phase = phase_result.scalar_one_or_none()
        if not phase:
            raise ResourceNotFoundError(f"Phase {phase_id} not found")
        
        # Validate data executive
        user_result = await self.db.execute(
            select(User).where(
                and_(
                    User.user_id == data_executive_id,
                    User.role == 'Data Executive'
                )
            )
        )
        data_executive = user_result.scalar_one_or_none()
        if not data_executive:
            raise ValidationError("User must be a Data Executive to create assignment versions")
        
        # Check if active version already exists
        existing_active = await self.db.execute(
            select(DataOwnerLOBAttributeVersion)
            .where(
                and_(
                    DataOwnerLOBAttributeVersion.phase_id == phase_id,
                    DataOwnerLOBAttributeVersion.version_status == VersionStatus.ACTIVE
                )
            )
        )
        
        existing_version = existing_active.scalar_one_or_none()
        parent_version_id = None
        version_number = 1
        
        if existing_version:
            # Mark existing version as superseded
            existing_version.version_status = VersionStatus.SUPERSEDED
            existing_version.updated_by_id = data_executive_id
            existing_version.updated_at = datetime.utcnow()
            parent_version_id = existing_version.version_id
            version_number = existing_version.version_number + 1
        
        # Create new version
        version = DataOwnerLOBAttributeVersion(
            phase_id=phase_id,
            workflow_activity_id=workflow_activity_id,
            version_number=version_number,
            version_status=VersionStatus.ACTIVE,
            parent_version_id=parent_version_id,
            workflow_execution_id=workflow_execution_id,
            workflow_run_id=workflow_run_id,
            data_executive_id=data_executive_id,
            assignment_batch_date=datetime.utcnow(),
            assignment_notes=assignment_notes,
            created_by_id=data_executive_id,
            updated_by_id=data_executive_id
        )
        
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        
        logger.info(f"Created data owner LOB assignment version {version.version_id} for phase {phase_id}")
        return version
    
    async def get_version_by_id(self, version_id: str) -> DataOwnerLOBAttributeVersion:
        """Get version by ID with relationships loaded"""
        result = await self.db.execute(
            select(DataOwnerLOBAttributeVersion)
            .options(
                selectinload(DataOwnerLOBAttributeVersion.assignments),
                joinedload(DataOwnerLOBAttributeVersion.phase),
                joinedload(DataOwnerLOBAttributeVersion.data_executive)
            )
            .where(DataOwnerLOBAttributeVersion.version_id == version_id)
        )
        version = result.scalar_one_or_none()
        if not version:
            raise ResourceNotFoundError(f"Version {version_id} not found")
        return version
    
    async def get_current_version(self, phase_id: int) -> Optional[DataOwnerLOBAttributeVersion]:
        """Get the current active version for a phase"""
        result = await self.db.execute(
            select(DataOwnerLOBAttributeVersion)
            .options(selectinload(DataOwnerLOBAttributeVersion.assignments))
            .where(
                and_(
                    DataOwnerLOBAttributeVersion.phase_id == phase_id,
                    DataOwnerLOBAttributeVersion.version_status == VersionStatus.ACTIVE
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_version_history(self, phase_id: int) -> List[DataOwnerLOBAttributeVersion]:
        """Get all versions for a phase ordered by version number"""
        result = await self.db.execute(
            select(DataOwnerLOBAttributeVersion)
            .where(DataOwnerLOBAttributeVersion.phase_id == phase_id)
            .order_by(desc(DataOwnerLOBAttributeVersion.version_number))
        )
        return result.scalars().all()
    
    # Assignment Management
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
    ) -> DataOwnerLOBAttributeMapping:
        """Assign a data owner to a LOB-Attribute combination"""
        
        # Validate version
        version = await self.get_version_by_id(version_id)
        if version.version_status != VersionStatus.ACTIVE:
            raise ValidationError("Can only assign to active versions")
        
        if version.data_executive_id != data_executive_id:
            raise ValidationError("Only the version's data executive can make assignments")
        
        # Validate Data Executive can only assign to their LOB
        data_executive = await self.db.get(User, data_executive_id)
        if data_executive and data_executive.lob_id != lob_id:
            raise ValidationError(f"Data Executive can only assign data owners to their own LOB. Executive LOB: {data_executive.lob_id}, Assignment LOB: {lob_id}")
        
        # Validate references exist
        await self._validate_assignment_references(phase_id, sample_id, attribute_id, lob_id, data_owner_id)
        
        # Check if assignment already exists
        existing_assignment = await self.db.execute(
            select(DataOwnerLOBAttributeMapping)
            .where(
                and_(
                    DataOwnerLOBAttributeMapping.version_id == version_id,
                    DataOwnerLOBAttributeMapping.phase_id == phase_id,
                    DataOwnerLOBAttributeMapping.sample_id == sample_id,
                    DataOwnerLOBAttributeMapping.attribute_id == attribute_id,
                    DataOwnerLOBAttributeMapping.lob_id == lob_id
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
            existing.updated_by_id = data_executive_id
            existing.updated_at = datetime.utcnow()
            
            # Set status based on change
            if previous_data_owner_id != data_owner_id:
                existing.assignment_status = AssignmentStatus.CHANGED
                existing.change_reason = f"Changed from user {previous_data_owner_id} to user {data_owner_id}"
            else:
                existing.assignment_status = AssignmentStatus.ASSIGNED if data_owner_id else AssignmentStatus.UNASSIGNED
            
            # Reset acknowledgment since assignment changed
            if previous_data_owner_id != data_owner_id:
                existing.data_owner_acknowledged = False
                existing.data_owner_acknowledged_at = None
                existing.data_owner_response_notes = None
            
            await self.db.commit()
            assignment = existing
        else:
            # Create new assignment
            assignment = DataOwnerLOBAttributeMapping(
                version_id=version_id,
                phase_id=phase_id,
                sample_id=sample_id,
                attribute_id=attribute_id,
                lob_id=lob_id,
                data_owner_id=data_owner_id,
                data_executive_id=data_executive_id,
                assigned_by_data_executive_at=datetime.utcnow(),
                assignment_rationale=assignment_rationale,
                assignment_status=AssignmentStatus.ASSIGNED if data_owner_id else AssignmentStatus.UNASSIGNED,
                created_by_id=data_executive_id,
                updated_by_id=data_executive_id
            )
            
            self.db.add(assignment)
            await self.db.commit()
            await self.db.refresh(assignment)
        
        # Update version summary
        await self.update_version_summary(version_id)
        
        logger.info(f"Assigned data owner {data_owner_id} to LOB {lob_id}, attribute {attribute_id} in version {version_id}")
        return assignment
    
    async def bulk_assign_data_owners(
        self,
        version_id: str,
        assignments: List[Dict[str, Any]],
        data_executive_id: int
    ) -> Dict[str, Any]:
        """Bulk assign data owners to multiple LOB-Attribute combinations"""
        
        version = await self.get_version_by_id(version_id)
        if version.version_status != VersionStatus.ACTIVE:
            raise ValidationError("Can only assign to active versions")
        
        if version.data_executive_id != data_executive_id:
            raise ValidationError("Only the version's data executive can make assignments")
        
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
                
                if assignment.assignment_status == AssignmentStatus.CHANGED:
                    updated_assignments.append(assignment)
                else:
                    created_assignments.append(assignment)
                    
            except Exception as e:
                errors.append({
                    "assignment_data": assignment_data,
                    "error": str(e)
                })
                logger.error(f"Failed to process bulk assignment: {e}")
        
        return {
            "version_id": version_id,
            "created_assignments": len(created_assignments),
            "updated_assignments": len(updated_assignments),
            "errors": len(errors),
            "error_details": errors
        }
    
    async def unassign_data_owner(
        self,
        assignment_id: str,
        data_executive_id: int,
        unassignment_reason: Optional[str] = None
    ) -> DataOwnerLOBAttributeMapping:
        """Unassign a data owner from a LOB-Attribute combination"""
        
        assignment = await self.get_assignment_by_id(assignment_id)
        
        # Validate version is active
        version = await self.get_version_by_id(str(assignment.version_id))
        if version.version_status != VersionStatus.ACTIVE:
            raise ValidationError("Can only modify assignments in active versions")
        
        if version.data_executive_id != data_executive_id:
            raise ValidationError("Only the version's data executive can modify assignments")
        
        # Track the change
        assignment.previous_data_owner_id = assignment.data_owner_id
        assignment.data_owner_id = None
        assignment.assignment_status = AssignmentStatus.UNASSIGNED
        assignment.change_reason = unassignment_reason or "Unassigned by data executive"
        assignment.assigned_by_data_executive_at = datetime.utcnow()
        assignment.updated_by_id = data_executive_id
        assignment.updated_at = datetime.utcnow()
        
        # Reset acknowledgment
        assignment.data_owner_acknowledged = False
        assignment.data_owner_acknowledged_at = None
        assignment.data_owner_response_notes = None
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(str(assignment.version_id))
        
        logger.info(f"Unassigned data owner from assignment {assignment_id}")
        return assignment
    
    # Assignment Queries
    async def get_lob_attribute_assignments(
        self,
        phase_id: int,
        version_id: Optional[str] = None,
        lob_id: Optional[int] = None,
        data_owner_id: Optional[int] = None,
        assignment_status: Optional[str] = None,
        data_executive_id: Optional[int] = None
    ) -> List[DataOwnerLOBAttributeMapping]:
        """Get LOB attribute assignments with optional filters"""
        
        if version_id:
            version = await self.get_version_by_id(version_id)
        else:
            # Get current active version
            version = await self.get_current_version(phase_id)
            if not version:
                return []
        
        query = select(DataOwnerLOBAttributeMapping).options(
            joinedload(DataOwnerLOBAttributeMapping.lob),
            joinedload(DataOwnerLOBAttributeMapping.attribute),
            joinedload(DataOwnerLOBAttributeMapping.sample),
            joinedload(DataOwnerLOBAttributeMapping.data_owner),
            joinedload(DataOwnerLOBAttributeMapping.data_executive)
        ).where(DataOwnerLOBAttributeMapping.version_id == version.version_id)
        
        # Apply filters
        if lob_id:
            query = query.where(DataOwnerLOBAttributeMapping.lob_id == lob_id)
        if data_owner_id:
            query = query.where(DataOwnerLOBAttributeMapping.data_owner_id == data_owner_id)
        if assignment_status:
            query = query.where(DataOwnerLOBAttributeMapping.assignment_status == assignment_status)
        
        # Apply Data Executive LOB filtering
        if data_executive_id:
            # Get the Data Executive's LOB
            exec_user = await self.db.get(User, data_executive_id)
            if exec_user and exec_user.lob_id:
                query = query.where(DataOwnerLOBAttributeMapping.lob_id == exec_user.lob_id)
        
        query = query.order_by(
            DataOwnerLOBAttributeMapping.lob_id,
            DataOwnerLOBAttributeMapping.attribute_id
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_data_owner_workload(
        self,
        phase_id: int,
        data_owner_id: int
    ) -> Dict[str, Any]:
        """Get workload summary for a specific data owner"""
        
        current_version = await self.get_current_version(phase_id)
        if not current_version:
            return {
                "data_owner_id": data_owner_id,
                "phase_id": phase_id,
                "total_assignments": 0,
                "acknowledged_assignments": 0,
                "pending_assignments": 0,
                "assignments": []
            }
        
        assignments = await self.get_lob_attribute_assignments(
            phase_id=phase_id,
            version_id=str(current_version.version_id),
            data_owner_id=data_owner_id
        )
        
        acknowledged_count = sum(1 for a in assignments if a.data_owner_acknowledged)
        pending_count = len(assignments) - acknowledged_count
        
        return {
            "data_owner_id": data_owner_id,
            "phase_id": phase_id,
            "version_id": str(current_version.version_id),
            "total_assignments": len(assignments),
            "acknowledged_assignments": acknowledged_count,
            "pending_assignments": pending_count,
            "assignments": assignments
        }
    
    async def get_assignment_changes_history(
        self,
        phase_id: int,
        lob_id: Optional[int] = None,
        attribute_id: Optional[int] = None,
        sample_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get history of assignment changes across versions"""
        
        # Get all versions for the phase
        versions = await self.get_version_history(phase_id)
        
        changes = []
        
        for version in versions:
            query = select(DataOwnerLOBAttributeMapping).options(
                joinedload(DataOwnerLOBAttributeMapping.lob),
                joinedload(DataOwnerLOBAttributeMapping.attribute),
                joinedload(DataOwnerLOBAttributeMapping.data_owner),
                joinedload(DataOwnerLOBAttributeMapping.previous_data_owner)
            ).where(DataOwnerLOBAttributeMapping.version_id == version.version_id)
            
            # Apply filters
            if lob_id:
                query = query.where(DataOwnerLOBAttributeMapping.lob_id == lob_id)
            if attribute_id:
                query = query.where(DataOwnerLOBAttributeMapping.attribute_id == attribute_id)
            if sample_id:
                query = query.where(DataOwnerLOBAttributeMapping.sample_id == sample_id)
            
            assignments_result = await self.db.execute(query)
            assignments = assignments_result.scalars().all()
            
            for assignment in assignments:
                changes.append({
                    "version_number": version.version_number,
                    "version_date": version.assignment_batch_date,
                    "data_executive_id": version.data_executive_id,
                    "assignment_id": str(assignment.assignment_id),
                    "lob_id": assignment.lob_id,
                    "lob_name": assignment.lob.name if assignment.lob else None,
                    "attribute_id": assignment.attribute_id,
                    "attribute_name": assignment.attribute.attribute_name if assignment.attribute else None,
                    "sample_id": assignment.sample_id,
                    "data_owner_id": assignment.data_owner_id,
                    "data_owner_name": f"{assignment.data_owner.first_name} {assignment.data_owner.last_name}" if assignment.data_owner else None,
                    "previous_data_owner_id": assignment.previous_data_owner_id,
                    "previous_data_owner_name": f"{assignment.previous_data_owner.first_name} {assignment.previous_data_owner.last_name}" if assignment.previous_data_owner else None,
                    "change_reason": assignment.change_reason,
                    "assignment_status": assignment.assignment_status,
                    "assignment_rationale": assignment.assignment_rationale
                })
        
        return sorted(changes, key=lambda x: (x["version_number"], x["lob_id"], x["attribute_id"]), reverse=True)
    
    # Data Owner Acknowledgment
    async def acknowledge_assignment(
        self,
        assignment_id: str,
        data_owner_id: int,
        response_notes: Optional[str] = None
    ) -> DataOwnerLOBAttributeMapping:
        """Data owner acknowledges their assignment"""
        
        assignment = await self.get_assignment_by_id(assignment_id)
        
        if assignment.data_owner_id != data_owner_id:
            raise ValidationError("Only the assigned data owner can acknowledge this assignment")
        
        if assignment.assignment_status == AssignmentStatus.UNASSIGNED:
            raise ValidationError("Cannot acknowledge an unassigned assignment")
        
        assignment.data_owner_acknowledged = True
        assignment.data_owner_acknowledged_at = datetime.utcnow()
        assignment.data_owner_response_notes = response_notes
        assignment.assignment_status = AssignmentStatus.CONFIRMED
        assignment.updated_by_id = data_owner_id
        assignment.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(f"Data owner {data_owner_id} acknowledged assignment {assignment_id}")
        return assignment
    
    # Utility Methods
    async def update_version_summary(self, version_id: str):
        """Update version summary statistics"""
        
        assignments_result = await self.db.execute(
            select(DataOwnerLOBAttributeMapping)
            .where(DataOwnerLOBAttributeMapping.version_id == version_id)
        )
        assignments = assignments_result.scalars().all()
        
        version = await self.get_version_by_id(version_id)
        version.total_lob_attributes = len(assignments)
        version.assigned_lob_attributes = sum(1 for a in assignments if a.data_owner_id is not None)
        version.unassigned_lob_attributes = sum(1 for a in assignments if a.data_owner_id is None)
        version.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        logger.debug(f"Updated version {version_id} summary: {version.assigned_lob_attributes}/{version.total_lob_attributes} assigned")
    
    async def get_assignment_by_id(self, assignment_id: str) -> DataOwnerLOBAttributeMapping:
        """Get assignment by ID with error handling"""
        result = await self.db.execute(
            select(DataOwnerLOBAttributeMapping)
            .options(
                joinedload(DataOwnerLOBAttributeMapping.lob),
                joinedload(DataOwnerLOBAttributeMapping.attribute),
                joinedload(DataOwnerLOBAttributeMapping.data_owner),
                joinedload(DataOwnerLOBAttributeMapping.data_executive)
            )
            .where(DataOwnerLOBAttributeMapping.assignment_id == assignment_id)
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise ResourceNotFoundError(f"Assignment {assignment_id} not found")
        return assignment
    
    async def _validate_assignment_references(
        self,
        phase_id: int,
        sample_id: int,
        attribute_id: int,
        lob_id: int,
        data_owner_id: Optional[int]
    ):
        """Validate that all referenced entities exist"""
        
        # Validate sample exists
        sample_result = await self.db.execute(
            select(SampleSelectionSample).where(SampleSelectionSample.sample_id == sample_id)
        )
        if not sample_result.scalar_one_or_none():
            raise ResourceNotFoundError(f"Sample {sample_id} not found")
        
        # Validate attribute exists
        attribute_result = await self.db.execute(
            select(PlanningAttribute).where(PlanningAttribute.attribute_id == attribute_id)
        )
        if not attribute_result.scalar_one_or_none():
            raise ResourceNotFoundError(f"Attribute {attribute_id} not found")
        
        # Validate LOB exists
        lob_result = await self.db.execute(
            select(LOB).where(LOB.lob_id == lob_id)
        )
        if not lob_result.scalar_one_or_none():
            raise ResourceNotFoundError(f"LOB {lob_id} not found")
        
        # Validate data owner exists and has correct role
        if data_owner_id:
            user_result = await self.db.execute(
                select(User).where(
                    and_(
                        User.user_id == data_owner_id,
                        User.role == 'Data Owner'
                    )
                )
            )
            if not user_result.scalar_one_or_none():
                raise ValidationError(f"User {data_owner_id} is not a valid Data Owner")
    
    # Dashboard and Analytics
    async def get_phase_assignment_dashboard(self, phase_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard data for phase assignments"""
        
        current_version = await self.get_current_version(phase_id)
        if not current_version:
            return {
                "phase_id": phase_id,
                "current_version": None,
                "assignment_summary": {
                    "total_assignments": 0,
                    "assigned_count": 0,
                    "unassigned_count": 0,
                    "acknowledged_count": 0,
                    "pending_acknowledgment_count": 0
                },
                "lob_breakdown": [],
                "data_owner_workload": []
            }
        
        assignments = await self.get_lob_attribute_assignments(
            phase_id=phase_id,
            version_id=str(current_version.version_id)
        )
        
        # Calculate summary statistics
        assigned_count = sum(1 for a in assignments if a.data_owner_id is not None)
        unassigned_count = len(assignments) - assigned_count
        acknowledged_count = sum(1 for a in assignments if a.data_owner_acknowledged)
        pending_acknowledgment_count = assigned_count - acknowledged_count
        
        # LOB breakdown
        lob_breakdown = {}
        for assignment in assignments:
            lob_name = assignment.lob.name if assignment.lob else f"LOB {assignment.lob_id}"
            if lob_name not in lob_breakdown:
                lob_breakdown[lob_name] = {
                    "lob_id": assignment.lob_id,
                    "lob_name": lob_name,
                    "total_attributes": 0,
                    "assigned_attributes": 0,
                    "acknowledged_attributes": 0
                }
            
            lob_breakdown[lob_name]["total_attributes"] += 1
            if assignment.data_owner_id:
                lob_breakdown[lob_name]["assigned_attributes"] += 1
            if assignment.data_owner_acknowledged:
                lob_breakdown[lob_name]["acknowledged_attributes"] += 1
        
        # Data owner workload
        data_owner_workload = {}
        for assignment in assignments:
            if assignment.data_owner_id:
                owner_key = assignment.data_owner_id
                if owner_key not in data_owner_workload:
                    owner_name = f"{assignment.data_owner.first_name} {assignment.data_owner.last_name}" if assignment.data_owner else f"User {assignment.data_owner_id}"
                    data_owner_workload[owner_key] = {
                        "data_owner_id": assignment.data_owner_id,
                        "data_owner_name": owner_name,
                        "total_assignments": 0,
                        "acknowledged_assignments": 0
                    }
                
                data_owner_workload[owner_key]["total_assignments"] += 1
                if assignment.data_owner_acknowledged:
                    data_owner_workload[owner_key]["acknowledged_assignments"] += 1
        
        return {
            "phase_id": phase_id,
            "current_version": {
                "version_id": str(current_version.version_id),
                "version_number": current_version.version_number,
                "status": current_version.version_status,
                "created_at": current_version.created_at,
                "data_executive_id": current_version.data_executive_id
            },
            "assignment_summary": {
                "total_assignments": len(assignments),
                "assigned_count": assigned_count,
                "unassigned_count": unassigned_count,
                "acknowledged_count": acknowledged_count,
                "pending_acknowledgment_count": pending_acknowledgment_count
            },
            "lob_breakdown": list(lob_breakdown.values()),
            "data_owner_workload": list(data_owner_workload.values())
        }