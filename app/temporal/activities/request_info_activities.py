"""Request for Information Phase Activities for Temporal Workflow

Standard structure:
1. Start Request for Information Phase (Tester initiated)
2. Request for Information-specific activities
3. Complete Request for Information Phase (Tester initiated)
"""

from temporalio import activity
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import uuid
from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import (
    WorkflowPhase, TestCycle, Report, CycleReport,
    ReportAttribute, User, Sample, DataOwnerAssignment
)
from app.temporal.shared import ActivityResult

logger = logging.getLogger(__name__)


@activity.defn
async def start_request_info_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> ActivityResult:
    """Start Request for Information Phase - Initiated by Tester
    
    This is the standard entry point for the Request for Information phase.
    Validates user permissions and initializes phase.
    """
    try:
        async with get_db() as db:
            # Verify user has permission to start phase
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to start Request for Information phase"
                )
            
            # Get or create workflow phase record
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Request for Information"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                # Create phase record
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Request for Information",
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
            
            await db.commit()
            
            logger.info(f"Started Request for Information phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "started_at": phase.actual_start_date.isoformat(),
                    "started_by": user_id
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to start Request for Information phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def create_information_requests_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Create information requests for data owners
    
    Request for Information-specific activity that creates requests
    """
    try:
        async with get_db() as db:
            # Get data owner assignments grouped by owner
            assignments_query = await db.execute(
                select(
                    DataOwnerAssignment.assigned_to,
                    User.full_name,
                    User.email,
                    func.count(DataOwnerAssignment.assignment_id).label("assignment_count"),
                    func.array_agg(DataOwnerAssignment.lob_id).label("lob_ids")
                ).join(
                    User, User.user_id == DataOwnerAssignment.assigned_to
                ).where(
                    and_(
                        DataOwnerAssignment.cycle_id == cycle_id,
                        DataOwnerAssignment.report_id == report_id,
                        DataOwnerAssignment.assignment_status == "Pending"
                    )
                ).group_by(
                    DataOwnerAssignment.assigned_to,
                    User.full_name,
                    User.email
                )
            )
            
            requests_created = []
            for row in assignments_query:
                # Create information request for each data owner
                request = InformationRequest(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    request_identifier=f"REQ-{cycle_id}-{report_id}-{row.assigned_to}",
                    requested_from=row.assigned_to,
                    request_type="data_provision",
                    status="Pending",
                    priority="High",
                    due_date=datetime.utcnow() + timedelta(days=3),  # 3 day SLA
                    created_by=1  # System user
                )
                db.add(request)
                await db.flush()  # Get request_id
                
                # Get attributes for this owner's assignments
                attributes_query = await db.execute(
                    select(
                        ReportAttribute.attribute_id,
                        ReportAttribute.attribute_name,
                        ReportAttribute.description,
                        ReportAttribute.is_critical
                    ).join(
                        DataOwnerAssignment,
                        DataOwnerAssignment.attribute_id == ReportAttribute.attribute_id
                    ).where(
                        and_(
                            DataOwnerAssignment.cycle_id == cycle_id,
                            DataOwnerAssignment.report_id == report_id,
                            DataOwnerAssignment.assigned_to == row.assigned_to
                        )
                    ).distinct()
                )
                
                # Create request items for each attribute
                items_created = 0
                for attr in attributes_query:
                    request_item = InformationRequestItem(
                        request_id=request.request_id,
                        attribute_id=attr.attribute_id,
                        item_description=f"Provide data for: {attr.attribute_name}",
                        data_type="structured",
                        is_mandatory=attr.is_critical,
                        status="Pending"
                    )
                    db.add(request_item)
                    items_created += 1
                
                requests_created.append({
                    "request_id": request.request_id,
                    "request_identifier": request.request_identifier,
                    "assigned_to": row.full_name,
                    "email": row.email,
                    "items_count": items_created,
                    "due_date": request.due_date.isoformat()
                })
            
            await db.commit()
            
            logger.info(f"Created {len(requests_created)} information requests")
            return ActivityResult(
                success=True,
                data={
                    "requests_created": len(requests_created),
                    "request_details": requests_created
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to create information requests: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def send_request_notifications_activity(
    cycle_id: int,
    report_id: int,
    request_data: Dict[str, Any]
) -> ActivityResult:
    """Send notifications to data owners about information requests
    
    Request for Information-specific activity that sends notifications
    """
    try:
        async with get_db() as db:
            notifications_sent = []
            
            # Get report and cycle details
            report = await db.get(Report, report_id)
            cycle = await db.get(TestCycle, cycle_id)
            
            if not report or not cycle:
                return ActivityResult(
                    success=False,
                    error="Report or cycle not found"
                )
            
            for request in request_data.get("request_details", []):
                # Create notification (simplified for demo)
                notification = {
                    "recipient": request["assigned_to"],
                    "email": request["email"],
                    "subject": f"Information Request - {report.report_name}",
                    "message": f"You have a new information request for {request['items_count']} attributes "
                              f"in the {cycle.cycle_name} testing cycle. "
                              f"Request ID: {request['request_identifier']}. "
                              f"Due date: {request['due_date']}",
                    "sent_at": datetime.utcnow().isoformat(),
                    "channel": "email"
                }
                notifications_sent.append(notification)
                
                # Update request status to "Sent"
                await db.execute(
                    update(InformationRequest).where(
                        InformationRequest.request_id == request["request_id"]
                    ).values(
                        status="Sent",
                        sent_date=datetime.utcnow()
                    )
                )
            
            await db.commit()
            
            logger.info(f"Sent {len(notifications_sent)} request notifications")
            return ActivityResult(
                success=True,
                data={
                    "notifications_sent": len(notifications_sent),
                    "notification_details": notifications_sent
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to send request notifications: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def monitor_request_responses_activity(
    cycle_id: int,
    report_id: int
) -> ActivityResult:
    """Monitor status of information requests
    
    Request for Information-specific activity that checks response status
    """
    try:
        async with get_db() as db:
            # Get request statistics
            request_stats = await db.execute(
                select(
                    InformationRequest.status,
                    func.count(InformationRequest.request_id).label("count")
                ).where(
                    and_(
                        InformationRequest.cycle_id == cycle_id,
                        InformationRequest.report_id == report_id
                    )
                ).group_by(InformationRequest.status)
            )
            
            status_summary = {row.status: row.count for row in request_stats}
            
            # Get overdue requests
            overdue_requests = await db.execute(
                select(
                    InformationRequest.request_identifier,
                    InformationRequest.requested_from,
                    User.full_name,
                    InformationRequest.due_date
                ).join(
                    User, User.user_id == InformationRequest.requested_from
                ).where(
                    and_(
                        InformationRequest.cycle_id == cycle_id,
                        InformationRequest.report_id == report_id,
                        InformationRequest.status.in_(["Pending", "Sent"]),
                        InformationRequest.due_date < datetime.utcnow()
                    )
                )
            )
            
            overdue_list = []
            for row in overdue_requests:
                overdue_list.append({
                    "request_id": row.request_identifier,
                    "assigned_to": row.full_name,
                    "due_date": row.due_date.isoformat(),
                    "days_overdue": (datetime.utcnow() - row.due_date).days
                })
            
            # Get response rate by data owner
            response_rates = await db.execute(
                select(
                    User.full_name,
                    func.count(InformationRequest.request_id).label("total_requests"),
                    func.count(
                        func.nullif(InformationRequest.status == "Completed", False)
                    ).label("completed_requests")
                ).join(
                    InformationRequest,
                    InformationRequest.requested_from == User.user_id
                ).where(
                    and_(
                        InformationRequest.cycle_id == cycle_id,
                        InformationRequest.report_id == report_id
                    )
                ).group_by(User.full_name)
            )
            
            owner_response_rates = []
            for row in response_rates:
                response_rate = (row.completed_requests / row.total_requests * 100) if row.total_requests > 0 else 0
                owner_response_rates.append({
                    "owner": row.full_name,
                    "total_requests": row.total_requests,
                    "completed_requests": row.completed_requests,
                    "response_rate": round(response_rate, 1)
                })
            
            logger.info(f"Monitored request responses: {status_summary}")
            return ActivityResult(
                success=True,
                data={
                    "status_summary": status_summary,
                    "overdue_count": len(overdue_list),
                    "overdue_requests": overdue_list,
                    "response_rates": owner_response_rates
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to monitor request responses: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def complete_request_info_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    completion_notes: Optional[str] = None
) -> ActivityResult:
    """Complete Request for Information Phase - Initiated by Tester
    
    This is the standard exit point for the Request for Information phase.
    Validates completion criteria and marks phase as complete.
    """
    try:
        async with get_db() as db:
            # Verify user has permission
            user = await db.get(User, user_id)
            if not user or user.role not in ["Tester", "Test Manager"]:
                return ActivityResult(
                    success=False,
                    error="User does not have permission to complete Request for Information phase"
                )
            
            # Get workflow phase
            result = await db.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Request for Information"
                )
            )
            phase = result.scalar_one_or_none()
            
            if not phase:
                return ActivityResult(
                    success=False,
                    error="Request for Information phase not found"
                )
            
            # Verify completion criteria
            # Get request statistics
            total_requests = await db.execute(
                select(func.count(InformationRequest.request_id)).where(
                    and_(
                        InformationRequest.cycle_id == cycle_id,
                        InformationRequest.report_id == report_id
                    )
                )
            )
            total_count = total_requests.scalar()
            
            if total_count == 0:
                return ActivityResult(
                    success=False,
                    error="Cannot complete Request for Information phase: No information requests created"
                )
            
            # Check pending requests
            pending_requests = await db.execute(
                select(func.count(InformationRequest.request_id)).where(
                    and_(
                        InformationRequest.cycle_id == cycle_id,
                        InformationRequest.report_id == report_id,
                        InformationRequest.status.in_(["Pending", "Sent"])
                    )
                )
            )
            pending_count = pending_requests.scalar()
            
            # Get completion percentage
            completion_rate = ((total_count - pending_count) / total_count * 100) if total_count > 0 else 0
            
            # Allow completion with warning if not all requests are complete
            if completion_rate < 80:
                logger.warning(f"Completing phase with only {completion_rate:.1f}% response rate")
            
            # Mark phase as complete
            phase.state = "Completed"
            phase.actual_end_date = datetime.utcnow()
            phase.completed_by = user_id
            if completion_notes:
                phase.notes = completion_notes
            
            # Calculate if on schedule
            if phase.planned_end_date and phase.actual_end_date > phase.planned_end_date:
                phase.status = "Behind Schedule"
            else:
                phase.status = "Complete"
            
            await db.commit()
            
            logger.info(f"Completed Request for Information phase for cycle {cycle_id}, report {report_id}")
            return ActivityResult(
                success=True,
                data={
                    "phase_id": phase.phase_id,
                    "completed_at": phase.actual_end_date.isoformat(),
                    "completed_by": user_id,
                    "duration_days": (phase.actual_end_date - phase.actual_start_date).days if phase.actual_start_date else 0,
                    "status": phase.status,
                    "total_requests": total_count,
                    "pending_requests": pending_count,
                    "completion_rate": round(completion_rate, 1)
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to complete Request for Information phase: {str(e)}")
        return ActivityResult(success=False, error=str(e))


@activity.defn
async def execute_request_info_activities(
    cycle_id: int,
    report_id: int,
    metadata: Dict[str, Any]
) -> ActivityResult:
    """Execute all Request for Information phase activities in sequence
    
    This orchestrates the request for information-specific activities between
    start and complete.
    """
    try:
        results = {}
        
        # 1. Create information requests
        request_result = await create_information_requests_activity(
            cycle_id, report_id
        )
        if not request_result.success:
            return request_result
        results["request_creation"] = request_result.data
        
        # 2. Send notifications
        notification_result = await send_request_notifications_activity(
            cycle_id, report_id, request_result.data
        )
        if not notification_result.success:
            return notification_result
        results["notifications"] = notification_result.data
        
        # 3. Monitor responses
        monitor_result = await monitor_request_responses_activity(
            cycle_id, report_id
        )
        if not monitor_result.success:
            return monitor_result
        results["response_monitoring"] = monitor_result.data
        
        return ActivityResult(
            success=True,
            data={
                "phase": "Request for Information",
                "activities_completed": 3,
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to execute request for information activities: {str(e)}")
        return ActivityResult(success=False, error=str(e))