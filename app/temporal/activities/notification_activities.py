"""Temporal activities for notifications"""

from temporalio import activity
from typing import List, Dict, Any
import logging
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.services.email_service import EmailService
from app.temporal.shared.types import ActivityResult, NotificationData

logger = logging.getLogger(__name__)


@activity.defn
async def send_email_notification_activity(notification: NotificationData) -> ActivityResult:
    """Send email notification to users"""
    try:
        async with get_db() as db:
            from sqlalchemy import select
            
            # Get user emails
            stmt = select(User).where(User.user_id.in_(notification.recipient_user_ids))
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            if not users:
                return ActivityResult(
                    success=False,
                    data={},
                    error_message="No users found for notification"
                )
            
            # Send emails
            email_service = EmailService()
            sent_count = 0
            failed_count = 0
            
            for user in users:
                try:
                    await email_service.send_email(
                        to_email=user.email,
                        subject=notification.subject,
                        body=notification.message,
                        is_html=True
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send email to {user.email}: {str(e)}")
                    failed_count += 1
            
            return ActivityResult(
                success=True,
                data={
                    "sent_count": sent_count,
                    "failed_count": failed_count,
                    "total_recipients": len(users)
                }
            )
            
    except Exception as e:
        logger.error(f"Error in send_email_notification_activity: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )


@activity.defn
async def create_in_app_notification_activity(notification: NotificationData) -> ActivityResult:
    """Create in-app notifications for users"""
    try:
        async with get_db() as db:
            from app.models.notification import Notification
            
            created_count = 0
            
            for user_id in notification.recipient_user_ids:
                notif = Notification(
                    user_id=user_id,
                    type=notification.notification_type,
                    title=notification.subject,
                    message=notification.message,
                    metadata=notification.metadata,
                    created_at=datetime.utcnow(),
                    is_read=False
                )
                db.add(notif)
                created_count += 1
            
            await db.commit()
            
            return ActivityResult(
                success=True,
                data={
                    "created_count": created_count
                }
            )
            
    except Exception as e:
        logger.error(f"Error creating in-app notifications: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )


@activity.defn
async def send_phase_completion_notification_activity(
    cycle_report_id: int,
    phase_name: str,
    completed_by: int
) -> ActivityResult:
    """Send notification when a phase is completed"""
    try:
        async with get_db() as db:
            from sqlalchemy import select
            from app.models.cycle_report import CycleReport
            from app.models.report import Report
            
            # Get cycle report details
            stmt = select(CycleReport).where(CycleReport.cycle_report_id == cycle_report_id)
            result = await db.execute(stmt)
            cycle_report = result.scalar_one_or_none()
            
            if not cycle_report:
                return ActivityResult(
                    success=False,
                    data={},
                    error_message="Cycle report not found"
                )
            
            # Determine recipients based on phase
            recipient_ids = []
            
            if phase_name == "Test Execution" and cycle_report.data_owner_id:
                # Notify data owner when testing is complete
                recipient_ids.append(cycle_report.data_owner_id)
            elif phase_name == "Request for Information" and cycle_report.tester_id:
                # Notify tester when RFI is complete
                recipient_ids.append(cycle_report.tester_id)
            
            if recipient_ids:
                notification = NotificationData(
                    recipient_user_ids=recipient_ids,
                    notification_type="phase_completed",
                    subject=f"Phase Completed: {phase_name}",
                    message=f"The {phase_name} phase has been completed for report {cycle_report_id}",
                    metadata={
                        "cycle_report_id": cycle_report_id,
                        "phase_name": phase_name,
                        "completed_by": completed_by
                    }
                )
                
                # Send both email and in-app notifications
                email_result = await send_email_notification_activity(notification)
                app_result = await create_in_app_notification_activity(notification)
                
                return ActivityResult(
                    success=True,
                    data={
                        "email_result": email_result.data,
                        "app_result": app_result.data
                    }
                )
            else:
                return ActivityResult(
                    success=True,
                    data={"message": "No recipients for this phase completion"}
                )
                
    except Exception as e:
        logger.error(f"Error sending phase completion notification: {str(e)}")
        return ActivityResult(
            success=False,
            data={},
            error_message=str(e)
        )