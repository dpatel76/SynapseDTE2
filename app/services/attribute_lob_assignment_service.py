"""
AttributeLOB Assignment Service using Universal Assignment framework
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.universal_assignment import UniversalAssignment
from app.models.report_attribute import ReportAttribute
from app.models.lob import LOB
from app.models.user import User
from app.services.universal_assignment_service import UniversalAssignmentService
from app.services.email_service import EmailService
from app.core.logging import get_logger

logger = get_logger(__name__)


class AttributeLOBAssignmentService:
    """Service for managing Attribute-LOB assignments using Universal Assignment framework"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_service = EmailService()
        self.assignment_service = UniversalAssignmentService(db, self.email_service)
    
    async def create_attribute_lob_assignment(
        self,
        cycle_id: int,
        report_id: int,
        attribute_id: int,
        lob_id: int,
        assigned_by: int,
        assignment_rationale: Optional[str] = None
    ) -> UniversalAssignment:
        """Create a new attribute-LOB assignment"""
        
        # Get attribute and LOB details
        attribute = await self.db.get(ReportAttribute, attribute_id)
        lob = await self.db.get(LOB, lob_id)
        
        if not attribute or not lob:
            raise ValueError("Invalid attribute or LOB ID")
        
        # Get Data Executive for the LOB
        data_executive_result = await self.db.execute(
            select(User).where(
                and_(
                    User.lob_id == lob_id,
                    User.role == "Data Executive",
                    User.is_active == True
                )
            )
        )
        data_executive = data_executive_result.scalar_one_or_none()
        
        # Get report and cycle names
        from app.models.report import Report
        from app.models.test_cycle import TestCycle
        report_result = await self.db.execute(select(Report).where(Report.report_id == report_id))
        report = report_result.scalar_one_or_none()
        cycle = await self.db.get(TestCycle, cycle_id)
        
        context_data = {
            "cycle_id": cycle_id,
            "report_id": report_id,
            "report_name": report.report_name if report else None,
            "cycle_name": cycle.cycle_name if cycle else None,
            "attribute_id": attribute_id,
            "attribute_name": attribute.attribute_name,
            "lob_id": lob_id,
            "lob_name": lob.lob_name,
            "assignment_rationale": assignment_rationale
        }
        
        # Create universal assignment
        assignment = await self.assignment_service.create_assignment(
            assignment_type="ATTRIBUTE_LOB_MAPPING",
            from_role="Tester",
            to_role="Data Executive",
            from_user_id=assigned_by,
            to_user_id=data_executive.user_id if data_executive else None,
            title=f"Identify Data Owner for {attribute.attribute_name}",
            description=f"Please identify the data owner for attribute '{attribute.attribute_name}' "
                       f"assigned to LOB '{lob.lob_name}'",
            task_instructions=assignment_rationale,
            context_type="ATTRIBUTE_LOB_ASSIGNMENT",
            context_data=context_data,
            priority="Medium",
            requires_approval=False
        )
        
        logger.info(f"Created attribute-LOB assignment: {assignment.assignment_id}")
        return assignment
    
    async def get_lob_assignments(
        self,
        cycle_id: int,
        report_id: Optional[int] = None,
        lob_id: Optional[int] = None
    ) -> List[UniversalAssignment]:
        """Get attribute-LOB assignments"""
        
        query = select(UniversalAssignment).where(
            and_(
                UniversalAssignment.assignment_type == "ATTRIBUTE_LOB_MAPPING",
                UniversalAssignment.context_type == "ATTRIBUTE_LOB_ASSIGNMENT"
            )
        )
        
        # Apply filters through context_data
        filters = []
        if cycle_id:
            filters.append(
                UniversalAssignment.context_data['cycle_id'].astext.cast(Integer) == cycle_id
            )
        if report_id:
            filters.append(
                UniversalAssignment.context_data['report_id'].astext.cast(Integer) == report_id
            )
        if lob_id:
            filters.append(
                UniversalAssignment.context_data['lob_id'].astext.cast(Integer) == lob_id
            )
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_assignment_status(
        self,
        cycle_id: int,
        report_id: int
    ) -> Dict[str, Any]:
        """Get attribute-LOB assignment status for a report"""
        
        assignments = await self.get_lob_assignments(cycle_id, report_id)
        
        total = len(assignments)
        assigned = len([a for a in assignments if a.to_user_id is not None])
        completed = len([a for a in assignments if a.status == "Completed"])
        
        return {
            "total_attributes": total,
            "lobs_assigned": assigned,
            "data_owners_identified": completed,
            "pending": total - completed,
            "completion_percentage": (completed / total * 100) if total > 0 else 0
        }
    
    async def complete_data_owner_assignment(
        self,
        assignment_id: str,
        data_owner_id: int,
        completed_by: int,
        notes: Optional[str] = None
    ) -> UniversalAssignment:
        """Complete the data owner assignment for an attribute"""
        
        assignment = await self.assignment_service.get_assignment(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")
        
        # Update context data with data owner
        assignment.context_data["data_owner_id"] = data_owner_id
        assignment.context_data["data_owner_assigned_at"] = datetime.utcnow().isoformat()
        assignment.context_data["data_owner_assigned_by"] = completed_by
        
        # Complete the assignment
        await self.assignment_service.complete_assignment(
            assignment_id,
            completed_by,
            notes
        )
        
        # Create a new assignment for the data owner to provide information
        data_owner = await self.db.get(User, data_owner_id)
        if data_owner:
            context_data = assignment.context_data.copy()
            context_data["parent_assignment_id"] = assignment_id
            # Ensure report_name and cycle_name are propagated
            if "report_name" not in context_data and "report_id" in context_data:
                from app.models.report import Report
                report_result = await self.db.execute(select(Report).where(Report.report_id == context_data["report_id"]))
                report = report_result.scalar_one_or_none()
                if report:
                    context_data["report_name"] = report.report_name
            if "cycle_name" not in context_data and "cycle_id" in context_data:
                from app.models.test_cycle import TestCycle
                cycle = await self.db.get(TestCycle, context_data["cycle_id"])
                if cycle:
                    context_data["cycle_name"] = cycle.cycle_name
            
            await self.assignment_service.create_assignment(
                assignment_type="DATA_PROVISION_REQUEST",
                from_role="Data Executive",
                to_role="Data Owner",
                from_user_id=completed_by,
                to_user_id=data_owner_id,
                title=f"Provide Data for {context_data.get('attribute_name', 'Attribute')}",
                description=f"Please provide the requested data for attribute '{context_data.get('attribute_name', 'Unknown')}' "
                           f"for report '{context_data.get('report_id', 'Unknown')}'",
                context_type="DATA_PROVISION",
                context_data=context_data,
                priority="High",
                requires_approval=False
            )
        
        return assignment