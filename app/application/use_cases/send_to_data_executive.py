"""
Use case for sending data owner assignment requests to Data Executives
"""
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
import logging

from app.application.use_cases.base import UseCase
from app.models.workflow import WorkflowPhase
from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping
from app.models.user import User
from app.models.lob import LOB
from app.services.universal_assignment_service import UniversalAssignmentService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class SendToDataExecutiveUseCase(UseCase):
    """Send data owner assignment requests to Data Executives"""
    
    async def execute(
        self,
        cycle_id: int,
        report_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Send assignment requests to Data Executives for their LOBs"""
        
        # Verify user is tester
        user = await db.get(User, user_id)
        if not user or user.role not in ["Tester", "Test Manager"]:
            raise ValueError("Only Tester or Test Manager can send assignments to Data Executives")
        
        # Get Data Provider ID phase
        phase_result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Data Provider ID'
                )
            )
        )
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            raise ValueError("Data Provider ID phase not found")
        
        if phase.state != "In Progress":
            raise ValueError("Data Provider ID phase must be in progress")
        
        # Get all unassigned mappings grouped by LOB (no version needed)
        mappings_result = await db.execute(
            select(
                DataOwnerLOBAttributeMapping.lob_id,
                LOB.lob_name,
                func.count(DataOwnerLOBAttributeMapping.mapping_id).label('attribute_count'),
                func.array_agg(DataOwnerLOBAttributeMapping.attribute_id).label('attribute_ids')
            )
            .join(LOB, DataOwnerLOBAttributeMapping.lob_id == LOB.lob_id)
            .where(
                and_(
                    DataOwnerLOBAttributeMapping.phase_id == phase.phase_id,
                    DataOwnerLOBAttributeMapping.data_owner_id.is_(None)  # Unassigned
                )
            )
            .group_by(DataOwnerLOBAttributeMapping.lob_id, LOB.lob_name)
        )
        
        lob_mappings = mappings_result.all()
        
        if not lob_mappings:
            return {
                "success": True,
                "message": "No unassigned mappings found - all data owners already assigned",
                "assignments_created": 0
            }
        
        # Get Data Executives for each LOB
        assignment_service = UniversalAssignmentService(db, EmailService())
        assignments_created = []
        
        for lob_id, lob_name, attribute_count, attribute_ids in lob_mappings:
            # Find Data Executive for this LOB
            exec_result = await db.execute(
                select(User).where(
                    and_(
                        User.lob_id == lob_id,
                        User.role == 'Data Executive',
                        User.is_active == True
                    )
                )
            )
            data_executive = exec_result.scalar_one_or_none()
            
            if not data_executive:
                logger.warning(f"No Data Executive found for LOB {lob_name} (ID: {lob_id})")
                continue
            
            # Get attribute names for context using text query
            attrs_result = await db.execute(
                text("""
                    SELECT attribute_name 
                    FROM cycle_report_planning_attributes 
                    WHERE id = ANY(:attribute_ids)
                """),
                {"attribute_ids": attribute_ids}
            )
            attribute_names = [row[0] for row in attrs_result.all()]
            
            # Create universal assignment for this Data Executive
            assignment = await assignment_service.create_assignment(
                assignment_type="LOB Assignment",
                from_role="Tester",
                to_role="Data Executive",
                from_user_id=user_id,
                to_user_id=data_executive.user_id,
                title=f"Assign Data Owners - {lob_name}",
                description=f"Please assign data owners for {attribute_count} attributes in {lob_name}",
                context_type="Report",
                context_data={
                    "cycle_id": cycle_id,
                    "report_id": report_id,
                    "phase_name": "Data Provider ID",
                    "lob_id": lob_id,
                    "lob_name": lob_name,
                    "attribute_count": attribute_count,
                    "attribute_ids": attribute_ids,
                    "attribute_names": attribute_names
                },
                task_instructions=(
                    f"Review the {attribute_count} attributes for {lob_name} and assign appropriate data owners. "
                    "Each attribute needs a data owner who will be responsible for providing the required data."
                ),
                priority="High",
                requires_approval=False
            )
            
            assignments_created.append({
                "lob_name": lob_name,
                "data_executive": f"{data_executive.first_name} {data_executive.last_name}",
                "attribute_count": attribute_count,
                "assignment_id": assignment.assignment_id
            })
        
        # Commit the assignments
        await db.commit()
        
        return {
            "success": True,
            "message": f"Successfully sent assignment requests to {len(assignments_created)} Data Executives",
            "assignments_created": len(assignments_created),
            "executives_notified": len(assignments_created),
            "details": assignments_created
        }