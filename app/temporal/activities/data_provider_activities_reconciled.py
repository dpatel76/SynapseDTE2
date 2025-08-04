"""Data Provider Identification Phase Activities - Reconciled with all existing steps

These activities match the pre-Temporal workflow exactly:
1. Start Data Provider ID Phase
2. Auto-Assign Data Providers (CDO Logic)
3. Manual Assignment Review
4. Send Notifications
5. Complete Data Provider ID Phase
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.workflow_orchestrator import get_workflow_orchestrator
# CDO service import removed - will use direct assignment logic
from app.infrastructure.services.notification_service_impl import NotificationServiceImpl
from app.models import DataOwnerAssignment, User, ReportAttribute, Report
from sqlalchemy import select, and_, update, func

logger = logging.getLogger(__name__)


@activity.defn
async def start_data_provider_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 1: Start data provider identification phase"""
    try:
        async for db in get_db():
            orchestrator = get_workflow_orchestrator(db)
            
            # Start data provider phase
            phase = await orchestrator.update_phase_state(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Data Provider ID",
                new_state="In Progress",
                notes="Started via Temporal workflow",
                user_id=user_id
            )
            
            # Get scoped attributes count
            result = await db.execute(
                select(func.count(ReportAttribute.attribute_id)).where(
                    and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.is_scoped == True
                    )
                )
            )
            attribute_count = result.scalar()
            
            logger.info(f"Started data provider phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "phase_id": phase.phase_id,
                "data": {
                    "phase_name": phase.phase_name,
                    "state": phase.state,
                    "status": phase.schedule_status,
                    "started_at": datetime.utcnow().isoformat(),
                    "scoped_attributes": attribute_count
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to start data provider phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def auto_assign_data_providers_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 2: Auto-assign data providers using CDO logic"""
    try:
        async for db in get_db():
            # Get all scoped attributes
            result = await db.execute(
                select(ReportAttribute).where(
                    and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id,
                        ReportAttribute.is_scoped == True
                    )
                )
            )
            attributes = result.scalars().all()
            
            if not attributes:
                raise ValueError("No scoped attributes found")
            
            # Get report to determine LOB
            report_result = await db.execute(
                select(Report).where(Report.report_id == report_id)
            )
            report = report_result.scalar_one()
            
            # Get CDO for this LOB
            cdo_result = await db.execute(
                select(User).where(
                    and_(
                        User.role == 'CDO',
                        User.lob_id == report.lob_id,
                        User.is_active == True
                    )
                )
            )
            cdo = cdo_result.scalar_one_or_none()
            
            if not cdo:
                raise ValueError(f"No CDO found for LOB {report.lob_id}")
            
            # Auto-assign all attributes to the CDO
            assignment_results = {}
            
            # Create assignment records
            assignments_created = 0
            unassigned_attributes = []
            
            for attr in attributes:
                assignment = assignment_results.get(attr.attribute_id)
                if assignment and assignment.get('data_provider_id'):
                    # Create assignment record
                    dp_assignment = DataOwnerAssignment(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        attribute_id=attr.attribute_id,
                        data_provider_id=assignment['data_provider_id'],
                        assignment_method='auto',
                        assignment_reason=assignment.get('reason', 'CDO LOB mapping'),
                        assigned_by=user_id,
                        status='pending_review'
                    )
                    db.add(dp_assignment)
                    assignments_created += 1
                else:
                    unassigned_attributes.append({
                        'attribute_id': attr.attribute_id,
                        'attribute_name': attr.attribute_name,
                        'reason': 'No matching CDO for LOB'
                    })
            
            await db.commit()
            
            logger.info(f"Auto-assigned {assignments_created} data providers for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "total_attributes": len(attributes),
                    "auto_assigned": assignments_created,
                    "unassigned": len(unassigned_attributes),
                    "unassigned_attributes": unassigned_attributes,
                    "requires_manual_review": True
                }
            }
            
    except Exception as e:
        logger.error(f"Failed in auto-assignment: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def review_data_provider_assignments_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    review_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 3: Manual review of data provider assignments
    
    Human-in-the-loop activity for reviewing and adjusting assignments.
    """
    try:
        async for db in get_db():
            if review_data and review_data.get('assignment_updates'):
                # Process manual assignment updates
                updates = review_data['assignment_updates']
                approved_count = 0
                reassigned_count = 0
                
                for update in updates:
                    assignment_id = update.get('assignment_id')
                    action = update.get('action')  # 'approve', 'reassign', 'create_new'
                    
                    if action == 'approve':
                        # Approve the assignment
                        await db.execute(
                            update(DataOwnerAssignment)
                            .where(DataOwnerAssignment.assignment_id == assignment_id)
                            .values(
                                status='approved',
                                reviewed_by=user_id,
                                reviewed_at=datetime.utcnow()
                            )
                        )
                        approved_count += 1
                        
                    elif action == 'reassign':
                        # Reassign to different data provider
                        new_provider_id = update.get('new_data_provider_id')
                        await db.execute(
                            update(DataOwnerAssignment)
                            .where(DataOwnerAssignment.assignment_id == assignment_id)
                            .values(
                                data_provider_id=new_provider_id,
                                assignment_method='manual',
                                assignment_reason=update.get('reason', 'Manual reassignment'),
                                status='approved',
                                reviewed_by=user_id,
                                reviewed_at=datetime.utcnow()
                            )
                        )
                        reassigned_count += 1
                        
                    elif action == 'create_new':
                        # Create new assignment for unassigned attribute
                        attribute_id = update.get('attribute_id')
                        data_provider_id = update.get('data_provider_id')
                        
                        assignment = DataOwnerAssignment(
                            cycle_id=cycle_id,
                            report_id=report_id,
                            attribute_id=attribute_id,
                            data_provider_id=data_provider_id,
                            assignment_method='manual',
                            assignment_reason=update.get('reason', 'Manual assignment'),
                            assigned_by=user_id,
                            status='approved',
                            reviewed_by=user_id,
                            reviewed_at=datetime.utcnow()
                        )
                        db.add(assignment)
                        approved_count += 1
                
                await db.commit()
                
                # Check if all attributes have approved assignments
                result = await db.execute(
                    select(
                        func.count(ReportAttribute.attribute_id).label('total'),
                        func.count(DataOwnerAssignment.assignment_id).filter(
                            DataOwnerAssignment.status == 'approved'
                        ).label('approved')
                    ).select_from(ReportAttribute)
                    .outerjoin(
                        DataOwnerAssignment,
                        and_(
                            DataOwnerAssignment.attribute_id == ReportAttribute.attribute_id,
                            DataOwnerAssignment.cycle_id == cycle_id,
                            DataOwnerAssignment.report_id == report_id
                        )
                    ).where(
                        and_(
                            ReportAttribute.cycle_id == cycle_id,
                            ReportAttribute.report_id == report_id,
                            ReportAttribute.is_scoped == True
                        )
                    )
                )
                counts = result.first()
                
                return {
                    "success": True,
                    "data": {
                        "assignments_approved": approved_count,
                        "assignments_reassigned": reassigned_count,
                        "total_attributes": counts.total,
                        "total_approved": counts.approved,
                        "all_assigned": counts.total == counts.approved,
                        "ready_for_notifications": counts.total == counts.approved
                    }
                }
            else:
                # Return current assignment status
                result = await db.execute(
                    select(DataOwnerAssignment).where(
                        and_(
                            DataOwnerAssignment.cycle_id == cycle_id,
                            DataOwnerAssignment.report_id == report_id
                        )
                    )
                )
                assignments = result.scalars().all()
                
                pending_review = [a for a in assignments if a.status == 'pending_review']
                approved = [a for a in assignments if a.status == 'approved']
                
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_review",
                        "message": "Waiting for data provider assignment review",
                        "pending_review_count": len(pending_review),
                        "approved_count": len(approved)
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in assignment review: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def send_data_provider_notifications_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 4: Send notifications to assigned data providers"""
    try:
        async for db in get_db():
            notification_service = NotificationServiceImpl(db)
            
            # Get all approved assignments with data provider details
            result = await db.execute(
                select(DataOwnerAssignment, User).join(
                    User,
                    DataOwnerAssignment.data_provider_id == User.user_id
                ).where(
                    and_(
                        DataOwnerAssignment.cycle_id == cycle_id,
                        DataOwnerAssignment.report_id == report_id,
                        DataOwnerAssignment.status == 'approved'
                    )
                )
            )
            assignments = result.all()
            
            if not assignments:
                raise ValueError("No approved assignments found")
            
            # Group assignments by data provider
            provider_assignments = {}
            for assignment, provider in assignments:
                if provider.user_id not in provider_assignments:
                    provider_assignments[provider.user_id] = {
                        'provider': provider,
                        'assignments': []
                    }
                provider_assignments[provider.user_id]['assignments'].append(assignment)
            
            # Send notifications
            notifications_sent = 0
            notification_errors = []
            
            for provider_id, data in provider_assignments.items():
                provider = data['provider']
                assignments = data['assignments']
                
                try:
                    # Send notification using notification service
                    await notification_service.send_notification(
                        user_id=provider.user_id,
                        title=f"Data Provider Assignment for Cycle {cycle_id}",
                        message=f"You have been assigned {len(assignments)} attributes for Report {report_id}. Deadline: {datetime.utcnow() + timedelta(days=14)}",
                        notification_type="data_provider_assignment",
                        priority="high",
                        metadata={
                            "cycle_id": cycle_id,
                            "report_id": report_id,
                            "assignment_count": len(assignments),
                            "deadline": (datetime.utcnow() + timedelta(days=14)).isoformat()
                        }
                    )
                    
                    notifications_sent += 1
                    
                    # Update assignment notification status
                    for assignment in assignments:
                        await db.execute(
                            update(DataOwnerAssignment)
                            .where(DataOwnerAssignment.assignment_id == assignment.assignment_id)
                            .values(
                                notification_sent=True,
                                notification_sent_at=datetime.utcnow()
                            )
                        )
                        
                except Exception as e:
                    notification_errors.append({
                        'provider_id': provider_id,
                        'provider_email': provider.email,
                        'error': str(e)
                    })
            
            await db.commit()
            
            logger.info(f"Sent {notifications_sent} notifications for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "total_providers": len(provider_assignments),
                    "notifications_sent": notifications_sent,
                    "notification_errors": len(notification_errors),
                    "errors": notification_errors,
                    "all_notified": notifications_sent == len(provider_assignments)
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to send notifications: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def complete_data_provider_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    phase_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Step 5: Complete data provider identification phase"""
    try:
        async for db in get_db():
            orchestrator = get_workflow_orchestrator(db)
            
            # Verify all attributes are assigned and notified
            if not phase_data.get('all_notified'):
                raise ValueError("Cannot complete phase - not all data providers notified")
            
            # Get final statistics
            result = await db.execute(
                select(
                    func.count(distinct(DataOwnerAssignment.data_provider_id)).label('unique_providers'),
                    func.count(DataOwnerAssignment.assignment_id).label('total_assignments')
                ).where(
                    and_(
                        DataOwnerAssignment.cycle_id == cycle_id,
                        DataOwnerAssignment.report_id == report_id,
                        DataOwnerAssignment.status == 'approved'
                    )
                )
            )
            stats = result.first()
            
            # Complete data provider phase
            phase = await orchestrator.update_phase_state(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Data Provider ID",
                new_state="Complete",
                notes=f"Completed with {stats.unique_providers} data providers assigned to {stats.total_assignments} attributes",
                user_id=user_id
            )
            
            # Since Data Provider ID and Sample Selection run in parallel,
            # the workflow will handle advancing to Request Info phase
            # when both are complete
            
            logger.info(f"Completed data provider phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "phase_name": "Data Provider ID",
                    "unique_providers": stats.unique_providers,
                    "total_assignments": stats.total_assignments,
                    "completed_at": datetime.utcnow().isoformat(),
                    "parallel_phase": "Sample Selection"  # Runs in parallel
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to complete data provider phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }