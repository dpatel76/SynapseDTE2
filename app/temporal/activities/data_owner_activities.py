"""Data Owner Identification Phase Activities for Temporal Workflow

Standard structure:
1. Start Data Owner Identification Phase (Tester initiated)
2. Data Owner Identification-specific activities
3. Complete Data Owner Identification Phase (Tester initiated)
"""

from temporalio import activity
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import (
    WorkflowPhase, TestCycle, Report, CycleReport,
    ReportAttribute, User, Sample,
    DataOwnerAssignment
)
from app.models.lob import LOB, LineOfBusiness, UserLOB
from app.temporal.shared import ActivityResult

logger = logging.getLogger(__name__)


@activity.defn
async def start_data_owner_identification_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> ActivityResult:
    """Start Data Owner Identification Phase - Initiated by Tester
    
    This is the standard entry point for the Data Owner Identification phase.
    Validates user permissions and initializes phase.
    """
    try:
        async with get_db() as db:
            # Verify user has permission to start phase
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to start Data Owner Identification phase"
                )
            
            # Get or create workflow phase record
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Owner Identification"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                # Create phase record
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Data Owner Identification",
                    state="In Progress",
                    status="On Schedule",
                    actual_start_date=datetime.utcnow(),
                    started_by=user_id
                )
                db.add(phase)
            else:
                # Update existing phase
                phase.state = "In Progress"
                phase.actual_start_date = datetime.utcnow()
                phase.started_by = user_id
                phase.updated_at = datetime.utcnow()
                phase.updated_by_id = user_id
            
            await db.commit()
            
            logger.info(f"Started Data Owner Identification phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "started_at": phase.actual_start_date.isoformat(),
                    "started_by": user_id
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to start Data Owner Identification phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def identify_lobs_from_samples_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Identify LOBs from selected samples
    
    Data Owner Identification-specific activity that determines which LOBs need data owners
    """
    try:
        async with get_db() as db:
            # Get unique LOBs FROM cycle_report_sample_selection_samples
            lob_query = await db.execute(
                select(
                    LineOfBusiness.lob_id,
                    LineOfBusiness.lob_name,
                    func.count(Sample.sample_id).label("sample_count")
                ).join(
                    Sample, Sample.lob_id == LineOfBusiness.lob_id
                ).where(
                    Sample.cycle_id == cycle_id,
                    Sample.report_id == report_id
                ).group_by(
                    LineOfBusiness.lob_id,
                    LineOfBusiness.lob_name
                )
            )
            
            lobs_with_samples = []
            for row in lob_query:
                lobs_with_samples.append({
                    "lob_id": row.lob_id,
                    "lob_name": row.lob_name,
                    "sample_count": row.sample_count
                })
            
            if not lobs_with_samples:
                return ActivityResult(
                    success=False,
                    error="No LOBs found from sample selection"
                )
            
            logger.info(f"Identified {len(lobs_with_samples)} LOBs FROM cycle_report_sample_selection_samples")
            return ActivityResult(
                success=True,
                data={
                    "lobs_identified": len(lobs_with_samples),
                    "lob_details": lobs_with_samples
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to identify LOBs FROM cycle_report_sample_selection_samples: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def identify_data_owners_for_lobs_activity(
    cycle_id: int,
    report_id: int,
    lob_data: Dict[str, Any]
) -> ActivityResult:
    """Identify data owners (Data Executives) for each LOB
    
    Data Owner Identification-specific activity that finds Data Executive users for LOBs
    """
    try:
        async with get_db() as db:
            data_owner_assignments = []
            unassigned_lobs = []
            
            for lob_info in lob_data.get("lob_details", []):
                lob_id = lob_info["lob_id"]
                lob_name = lob_info["lob_name"]
                
                # Find Data Executive users assigned to this LOB
                cdo_query = await db.execute(
                    select(User).join(
                        UserLOB, UserLOB.user_id == User.user_id
                    ).where(
                        and_(
                            UserLOB.lob_id == lob_id,
                            User.role == "Data Executive",
                            User.is_active == True
                        )
                    )
                )
                cdo_users = cdo_query.scalars().all()
                
                if cdo_users:
                    # Select primary Data Executive (first active Data Executive for now)
                    primary_cdo = cdo_users[0]
                    
                    data_owner_assignments.append({
                        "lob_id": lob_id,
                        "lob_name": lob_name,
                        "data_owner_id": primary_cdo.user_id,
                        "data_owner_name": primary_cdo.full_name,
                        "data_owner_email": primary_cdo.email,
                        "sample_count": lob_info["sample_count"]
                    })
                else:
                    unassigned_lobs.append({
                        "lob_id": lob_id,
                        "lob_name": lob_name,
                        "reason": "No Data Executive assigned to this LOB"
                    })
            
            logger.info(f"Identified data owners for {len(data_owner_assignments)} LOBs")
            return ActivityResult(
                success=True,
                data={
                    "assignments_identified": len(data_owner_assignments),
                    "unassigned_lobs": len(unassigned_lobs),
                    "data_owner_assignments": data_owner_assignments,
                    "unassigned_details": unassigned_lobs
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to identify data owners for LOBs: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def create_data_owner_assignments_activity(
    cycle_id: int,
    report_id: int,
    assignment_data: Dict[str, Any]
) -> ActivityResult:
    """Create data owner assignment records
    
    Data Owner Identification-specific activity that creates assignment records
    """
    try:
        async with get_db() as db:
            created_assignments = []
            
            # Get attributes that need assignment
            attributes = await db.execute(
                select(ReportAttribute).where(
                    ReportAttribute.report_id == report_id
                )
            )
            attribute_list = attributes.scalars().all()
            
            for assignment in assignment_data.get("data_owner_assignments", []):
                # Create assignment for each attribute-LOB combination
                for attribute in attribute_list:
                    # Check if assignment already exists
                    existing = await db.execute(
                        select(DataOwnerAssignment).where(
                            and_(
                                DataOwnerAssignment.cycle_id == cycle_id,
                                DataOwnerAssignment.report_id == report_id,
                                DataOwnerAssignment.attribute_id == attribute.attribute_id,
                                DataOwnerAssignment.lob_id == assignment["lob_id"]
                            )
                        )
                    )
                    
                    if not existing.scalar_one_or_none():
                        owner_assignment = DataOwnerAssignment(
                            cycle_id=cycle_id,
                            report_id=report_id,
                            attribute_id=attribute.attribute_id,
                            lob_id=assignment["lob_id"],
                            assigned_to=assignment["data_owner_id"],
                            assignment_status="Pending",
                            assigned_date=datetime.utcnow(),
                            created_by=1  # System user
                        )
                        db.add(owner_assignment)
                        
                        created_assignments.append({
                            "attribute": attribute.attribute_name,
                            "lob": assignment["lob_name"],
                            "assigned_to": assignment["data_owner_name"]
                        })
            
            await db.commit()
            
            # Group assignments by data owner for summary
            assignments_by_owner = {}
            for assignment in assignment_data.get("data_owner_assignments", []):
                owner_name = assignment["data_owner_name"]
                if owner_name not in assignments_by_owner:
                    assignments_by_owner[owner_name] = {
                        "owner_id": assignment["data_owner_id"],
                        "lobs": [],
                        "total_attributes": 0
                    }
                assignments_by_owner[owner_name]["lobs"].append(assignment["lob_name"])
                assignments_by_owner[owner_name]["total_attributes"] += len(attribute_list)
            
            logger.info(f"Created {len(created_assignments)} data owner assignments")
            return ActivityResult(
                success=True,
                data={
                    "total_assignments": len(created_assignments),
                    "assignments_by_owner": assignments_by_owner,
                    "assignment_examples": created_assignments[:10]  # First 10 examples
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to create data owner assignments: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def notify_data_owners_activity(
    cycle_id: int,
    report_id: int,
    assignment_data: Dict[str, Any]
) -> ActivityResult:
    """Send notifications to data owners about their assignments
    
    Data Owner Identification-specific activity that notifies Data Executives
    """
    try:
        async with get_db() as db:
            notifications_sent = []
            
            # Get report details for notification
            report = await db.get(Report, report_id)
            cycle = await db.get(TestCycle, cycle_id)
            
            if not report or not cycle:
                return ActivityResult(
                    success=False,
                    error="Report or cycle not found"
                )
            
            # Send notification to each data owner
            for owner_name, owner_data in assignment_data.get("assignments_by_owner", {}).items():
                # Create notification record (simplified for demo)
                notification_data = {
                    "recipient_id": owner_data["owner_id"],
                    "recipient_name": owner_name,
                    "notification_type": "data_owner_assignment",
                    "subject": f"Data Owner Assignment - {report.report_name}",
                    "message": f"You have been assigned as the Data Owner for {len(owner_data['lobs'])} LOB(s) "
                              f"in the {cycle.cycle_name} testing cycle for {report.report_name}. "
                              f"You are responsible for providing data for {owner_data['total_attributes']} attributes.",
                    "lobs_assigned": owner_data["lobs"],
                    "sent_at": datetime.utcnow().isoformat()
                }
                notifications_sent.append(notification_data)
            
            logger.info(f"Sent notifications to {len(notifications_sent)} data owners")
            return ActivityResult(
                success=True,
                data={
                    "notifications_sent": len(notifications_sent),
                    "notification_details": notifications_sent
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to notify data owners: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def complete_data_owner_identification_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    completion_notes: Optional[str] = None
) -> ActivityResult:
    """Complete Data Owner Identification Phase - Initiated by Tester
    
    This is the standard exit point for the Data Owner Identification phase.
    Validates completion criteria and marks phase as complete.
    """
    try:
        async with get_db() as db:
            # Verify user has permission
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to complete Data Owner Identification phase"
                )
            
            # Get workflow phase
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Data Owner Identification"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                return ActivityResult(
                    success=False,
                    error="Data Owner Identification phase not found"
                )
            
            # Verify completion criteria
            # 1. Check if data owner assignments exist
            assignments = await db.execute(
                select(func.count(DataOwnerAssignment.assignment_id)).where(
                    DataOwnerAssignment.cycle_id == cycle_id,
                    DataOwnerAssignment.report_id == report_id
                )
            )
            assignment_count = assignments.scalar()
            
            if assignment_count == 0:
                return ActivityResult(
                    success=False,
                    error="Cannot complete Data Owner Identification phase: No data owner assignments created"
                )
            
            # 2. Check assignment coverage
            unassigned = await db.execute(
                select(func.count(DataOwnerAssignment.assignment_id)).where(
                    and_(
                        DataOwnerAssignment.cycle_id == cycle_id,
                        DataOwnerAssignment.report_id == report_id,
                        DataOwnerAssignment.assigned_to.is_(None)
                    )
                )
            )
            unassigned_count = unassigned.scalar()
            
            if unassigned_count > 0:
                logger.warning(f"{unassigned_count} assignments without data owners")
            
            # Mark phase as complete
            phase.state = "Completed"
            phase.actual_end_date = datetime.utcnow()
            phase.completed_by = user_id
            phase.updated_at = datetime.utcnow()
            phase.updated_by_id = user_id
            if completion_notes:
                phase.notes = completion_notes
            
            # Calculate if on schedule
            if phase.planned_end_date and phase.actual_end_date > phase.planned_end_date:
                phase.status = "Behind Schedule"
            else:
                phase.status = "Complete"
            
            # Ensure phase is tracked for updates
            db.add(phase)
            
            # Get summary statistics
            owner_stats = await db.execute(
                select(
                    User.full_name,
                    func.count(DataOwnerAssignment.assignment_id).label("assignment_count")
                ).join(
                    DataOwnerAssignment, DataOwnerAssignment.assigned_to == User.user_id
                ).where(
                    and_(
                        DataOwnerAssignment.cycle_id == cycle_id,
                        DataOwnerAssignment.report_id == report_id
                    )
                ).group_by(User.full_name)
            )
            
            owner_distribution = {row.full_name: row.assignment_count for row in owner_stats}
            
            await db.commit()
            
            logger.info(f"Completed Data Owner Identification phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "completed_at": phase.actual_end_date.isoformat(),
                    "completed_by": user_id,
                    "duration_days": (phase.actual_end_date - phase.actual_start_date).days if phase.actual_start_date else 0,
                    "status": phase.status,
                    "total_assignments": assignment_count,
                    "unassigned_count": unassigned_count,
                    "owner_distribution": owner_distribution
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to complete Data Owner Identification phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def execute_data_owner_activities(
    cycle_id: int,
    report_id: int,
    metadata: Dict[str, Any]
) -> ActivityResult:
    """Execute all Data Owner Identification phase activities in sequence
    
    This orchestrates the data owner identification-specific activities between
    start and complete.
    """
    try:
        results = {}
        
        # 1. Identify LOBs from selected samples
        lob_result = await identify_lobs_from_samples_activity(
            cycle_id, report_id
        )
        if not lob_result.success:
            return lob_result
        results["lob_identification"] = lob_result.data
        
        # 2. Identify data owners for LOBs
        owner_result = await identify_data_owners_for_lobs_activity(
            cycle_id, report_id, lob_result.data
        )
        if not owner_result.success:
            return owner_result
        results["data_owner_identification"] = owner_result.data
        
        # 3. Create data owner assignments
        assignment_result = await create_data_owner_assignments_activity(
            cycle_id, report_id, owner_result.data
        )
        if not assignment_result.success:
            return assignment_result
        results["assignment_creation"] = assignment_result.data
        
        # 4. Notify data owners
        notification_result = await notify_data_owners_activity(
            cycle_id, report_id, assignment_result.data
        )
        if not notification_result.success:
            return notification_result
        results["notifications"] = notification_result.data
        
        return ActivityResult(
            success=True,
            data={
                "phase": "Data Owner Identification",
                "activities_completed": 4,
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to execute data owner identification activities: {str(e)}")
        return ActivityResult(success=False, error=str(e))