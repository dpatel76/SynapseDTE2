"""
Universal Assignment Migration endpoints
Provides migration endpoints to convert existing assignment systems to universal framework
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.core.logging import get_logger
from app.models.user import User
# DataOwnerAssignment removed - using universal assignments instead
# Create a dummy class to avoid import errors
class DataOwnerAssignment:
    pass
from app.models.universal_assignment import UniversalAssignment
from app.services.universal_assignment_service import UniversalAssignmentService
from app.services.email_service import EmailService

logger = get_logger(__name__)
router = APIRouter()


class MigrationResult(BaseModel):
    total_assignments: int
    migrated_successfully: int
    failed_migrations: int
    migration_errors: List[str]


@router.post("/migration/data-owner-assignments", response_model=MigrationResult)
@require_permission("admin", "migrate")
async def migrate_data_owner_assignments(
    dry_run: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Migrate existing data owner assignments to universal assignment framework"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = UniversalAssignmentService(db, EmailService())
        
        # DEPRECATED: DataOwnerAssignment table doesn't exist
        # result = await db.execute(select(DataOwnerAssignment))
        # data_owner_assignments = result.scalars().all()
        data_owner_assignments = []  # Empty list since table doesn't exist
        
        total_assignments = len(data_owner_assignments)
        migrated_successfully = 0
        failed_migrations = 0
        migration_errors = []
        
        for assignment in data_owner_assignments:
            try:
                if not dry_run:
                    # Create universal assignment equivalent
                    universal_assignment = await service.create_assignment(
                        assignment_type="LOB Assignment",
                        from_role="Tester",  # Typically assigned by Tester
                        to_role="Data Executive",  # CDO role
                        from_user_id=assignment.assigned_by,
                        to_user_id=assignment.cdo_id or assignment.data_owner_id,
                        title=f"[Data Owner Assignment] Attribute {assignment.attribute_id} - Report {assignment.report_id}",
                        description=f"Assign appropriate data owner for attribute {assignment.attribute_id} in Report {assignment.report_id}. This is a migrated assignment from the legacy data owner assignment system.",
                        context_type="Report",
                        context_data={
                            "cycle_id": assignment.cycle_id,
                            "report_id": assignment.report_id,
                            "attribute_id": assignment.attribute_id,
                            "lob_id": assignment.lob_id,
                            "original_assignment_id": assignment.assignment_id,
                            "phase_name": "Data Provider ID",
                            "workflow_phase": "Data Provider ID",
                            "test_cycle_linkage": f"Cycle_{assignment.cycle_id}",
                            "report_linkage": f"Report_{assignment.report_id}",
                            "attribute_linkage": f"Attribute_{assignment.attribute_id}",
                            "lob_linkage": f"LOB_{assignment.lob_id if assignment.lob_id else 'unassigned'}",
                            "assignment_category": "Data Owner Management"
                        },
                        task_instructions="Please identify and assign the appropriate data owner for this attribute.",
                        priority="Medium",
                        due_date=None,  # Calculate from original assignment if available
                        requires_approval=False,
                        assignment_metadata={
                            "migrated_from": "DataOwnerAssignment",
                            "original_status": assignment.status,
                            "migrated_at": datetime.now(timezone.utc).isoformat(),
                            "assignment_category": "Data Owner Management",
                            "workflow_phase": "Data Provider ID",
                            "legacy_assignment_id": assignment.assignment_id
                        }
                    )
                    
                    # Update status based on original assignment
                    if assignment.status == "Completed":
                        await service.complete_assignment(
                            universal_assignment.assignment_id,
                            assignment.data_owner_id or assignment.cdo_id or assignment.assigned_by,
                            "Migrated from legacy data owner assignment system"
                        )
                
                migrated_successfully += 1
                logger.info(f"Migrated data owner assignment {assignment.assignment_id}")
                
            except Exception as e:
                failed_migrations += 1
                error_msg = f"Failed to migrate assignment {assignment.assignment_id}: {str(e)}"
                migration_errors.append(error_msg)
                logger.error(error_msg)
        
        return MigrationResult(
            total_assignments=total_assignments,
            migrated_successfully=migrated_successfully,
            failed_migrations=failed_migrations,
            migration_errors=migration_errors
        )
        
    except Exception as e:
        logger.error(f"Error during data owner assignment migration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.post("/migration/report-owner-assignments", response_model=MigrationResult)
@require_permission("admin", "migrate")
async def migrate_report_owner_assignments(
    dry_run: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Migrate existing report owner assignments to universal assignment framework"""
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = UniversalAssignmentService(db, EmailService())
        
        # Get all existing report owner assignments
        # ReportOwnerAssignment model no longer exists - already migrated
        report_owner_assignments = []
        
        total_assignments = len(report_owner_assignments)
        migrated_successfully = 0
        failed_migrations = 0
        migration_errors = []
        
        for assignment in report_owner_assignments:
            try:
                if not dry_run:
                    # Create universal assignment equivalent
                    universal_assignment = await service.create_assignment(
                        assignment_type=assignment.assignment_type,
                        from_role="Tester",  # Typically assigned by Tester
                        to_role="Report Owner",
                        from_user_id=assignment.assigned_by,
                        to_user_id=assignment.assigned_to,
                        title=f"[{assignment.assignment_type}] {assignment.title}",
                        description=f"{assignment.description} (Migrated from legacy report owner assignment system)",
                        context_type="Report",
                        context_data={
                            "cycle_id": assignment.cycle_id,
                            "report_id": assignment.report_id,
                            "phase_name": assignment.phase_name,
                            "original_assignment_id": assignment.assignment_id,
                            "workflow_phase": assignment.phase_name,
                            "test_cycle_linkage": f"Cycle_{assignment.cycle_id}",
                            "report_linkage": f"Report_{assignment.report_id}",
                            "assignment_category": "Report Owner Tasks",
                            "due_date_original": assignment.due_date.isoformat() if assignment.due_date else None
                        },
                        task_instructions=assignment.description,
                        priority=assignment.priority,
                        due_date=assignment.due_date,
                        requires_approval=False,
                        assignment_metadata={
                            "migrated_from": "ReportOwnerAssignment",
                            "original_status": assignment.status,
                            "migrated_at": datetime.now(timezone.utc).isoformat(),
                            "assignment_category": "Report Owner Tasks",
                            "workflow_phase": assignment.phase_name,
                            "legacy_assignment_id": assignment.assignment_id,
                            "priority_level": assignment.priority
                        }
                    )
                    
                    # Update status and completion based on original assignment
                    if assignment.status == "Completed":
                        await service.complete_assignment(
                            universal_assignment.assignment_id,
                            assignment.completed_by or assignment.assigned_to,
                            assignment.completion_notes or "Migrated from legacy report owner assignment system"
                        )
                
                migrated_successfully += 1
                logger.info(f"Migrated report owner assignment {assignment.assignment_id}")
                
            except Exception as e:
                failed_migrations += 1
                error_msg = f"Failed to migrate assignment {assignment.assignment_id}: {str(e)}"
                migration_errors.append(error_msg)
                logger.error(error_msg)
        
        return MigrationResult(
            total_assignments=total_assignments,
            migrated_successfully=migrated_successfully,
            failed_migrations=failed_migrations,
            migration_errors=migration_errors
        )
        
    except Exception as e:
        logger.error(f"Error during report owner assignment migration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.get("/migration/assignment-types")
async def get_existing_assignment_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary of existing assignment types in the system"""
    
    try:
        # Count data owner assignments
        # DEPRECATED: DataOwnerAssignment table doesn't exist
        # data_owner_result = await db.execute(select(DataOwnerAssignment))
        # data_owner_assignments = data_owner_result.scalars().all()
        data_owner_assignments = []  # Empty list since table doesn't exist
        
        # Count report owner assignments
        # ReportOwnerAssignment model no longer exists - already migrated
        report_owner_assignments = []
        
        # Group by status/type
        data_owner_summary = {}
        for assignment in data_owner_assignments:
            status = assignment.status
            data_owner_summary[status] = data_owner_summary.get(status, 0) + 1
        
        report_owner_summary = {}
        for assignment in report_owner_assignments:
            assignment_type = assignment.assignment_type
            report_owner_summary[assignment_type] = report_owner_summary.get(assignment_type, 0) + 1
        
        return {
            "data_owner_assignments": {
                "total": len(data_owner_assignments),
                "by_status": data_owner_summary
            },
            "report_owner_assignments": {
                "total": len(report_owner_assignments),
                "by_type": report_owner_summary
            },
            "migration_recommendations": [
                "Run dry_run=true first to validate migration",
                "Backup database before actual migration",
                "Migrate during low usage periods",
                "Test universal assignment endpoints after migration"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting assignment type summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get assignment summary: {str(e)}")


@router.post("/assignments/universal/data-owner")
async def create_data_owner_universal_assignment(
    cycle_id: int,
    report_id: int,
    attribute_id: int,
    lob_id: int,
    description: str = "Please identify and assign the appropriate data owner for this attribute.",
    priority: str = "Medium",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a data owner assignment using the universal assignment framework"""
    
    try:
        service = UniversalAssignmentService(db, EmailService())
        
        assignment = await service.create_assignment(
            assignment_type="LOB Assignment",
            from_role=current_user.role,
            to_role="Data Executive",
            from_user_id=current_user.user_id,
            to_user_id=None,  # Auto-assign to appropriate CDO
            title=f"[Data Owner Assignment] Attribute {attribute_id} - Report {report_id}",
            description=f"[Data Provider ID Phase] {description}",
            context_type="Attribute",
            context_data={
                "cycle_id": cycle_id,
                "report_id": report_id,
                "attribute_id": attribute_id,
                "lob_id": lob_id,
                "phase_name": "Data Provider ID",
                "workflow_phase": "Data Provider ID",
                "test_cycle_linkage": f"Cycle_{cycle_id}",
                "report_linkage": f"Report_{report_id}",
                "attribute_linkage": f"Attribute_{attribute_id}",
                "lob_linkage": f"LOB_{lob_id}"
            },
            task_instructions="Please identify and assign the appropriate data owner for this attribute. Consider the attribute's domain, business context, and regulatory requirements.",
            priority=priority,
            requires_approval=False
        )
        
        return {
            "success": True,
            "assignment_id": assignment.assignment_id,
            "message": "Data owner assignment created successfully using universal framework"
        }
        
    except Exception as e:
        logger.error(f"Error creating data owner universal assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create assignment: {str(e)}")


@router.post("/assignments/universal/approval")
async def create_approval_universal_assignment(
    cycle_id: int,
    report_id: int,
    approval_type: str,
    item_description: str,
    approver_role: str,
    priority: str = "Medium",
    requires_review: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create an approval assignment using the universal assignment framework"""
    
    try:
        service = UniversalAssignmentService(db, EmailService())
        
        assignment = await service.create_assignment(
            assignment_type=f"{approval_type} Approval",
            from_role=current_user.role,
            to_role=approver_role,
            from_user_id=current_user.user_id,
            to_user_id=None,  # Auto-assign based on role
            title=f"[{approval_type} Approval] {item_description} - Report {report_id}",
            description=f"[Approval Required] Please review and approve the {item_description} for Report {report_id}.",
            context_type="Report",
            context_data={
                "cycle_id": cycle_id,
                "report_id": report_id,
                "approval_item": item_description,
                "approval_type": approval_type,
                "workflow_phase": "Approval Process",
                "test_cycle_linkage": f"Cycle_{cycle_id}",
                "report_linkage": f"Report_{report_id}",
                "approval_category": approval_type
            },
            task_instructions=f"Please review the {item_description} and provide your approval or feedback. Ensure all requirements are met before approving.",
            priority=priority,
            requires_approval=requires_review,
            approval_role=approver_role
        )
        
        return {
            "success": True,
            "assignment_id": assignment.assignment_id,
            "message": f"{approval_type} approval assignment created successfully using universal framework"
        }
        
    except Exception as e:
        logger.error(f"Error creating approval universal assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create assignment: {str(e)}")