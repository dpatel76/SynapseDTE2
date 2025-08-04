"""Production implementation of Email service"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.application.interfaces.external_services import IEmailService
from app.services.email_service import EmailService
from app.models import User, Notification
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


class EmailServiceImpl(IEmailService):
    """Production implementation of email service using existing EmailService"""
    
    def __init__(self, db_session: AsyncSession = None):
        # Use the existing email service
        self.email_service = EmailService()
        self.db_session = db_session
    
    async def send_email(self, to: List[str], subject: str, body: str, 
                        cc: Optional[List[str]] = None, attachments: Optional[List[str]] = None) -> bool:
        """Send an email"""
        try:
            # Use the existing service method
            success = await self.email_service.send_email(
                to_emails=to,
                subject=subject,
                body=body,
                cc_emails=cc,
                attachments=attachments
            )
            
            return success
        
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    async def send_notification(self, user_id: int, notification_type: str, 
                               data: Dict[str, Any]) -> bool:
        """Send a notification to a user"""
        try:
            if not self.db_session:
                logger.error("No database session available for notifications")
                return False
            
            # Get user details
            user_result = await self.db_session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            # Create notification record
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=data.get('title', 'System Notification'),
                message=data.get('message', ''),
                data=data,
                is_read=False,
                created_at=datetime.utcnow()
            )
            
            self.db_session.add(notification)
            
            # Send email notification based on type
            email_subject = f"[SynapseDTE] {data.get('title', notification_type)}"
            email_body = self._format_notification_email(notification_type, data)
            
            # Send email
            email_sent = await self.send_email(
                to=[user.email],
                subject=email_subject,
                body=email_body
            )
            
            if email_sent:
                notification.email_sent = True
                notification.email_sent_at = datetime.utcnow()
            
            await self.db_session.commit()
            
            return True
        
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def _format_notification_email(self, notification_type: str, data: Dict[str, Any]) -> str:
        """Format notification data into email body"""
        
        # Base template
        body = f"""
        <html>
        <body>
            <h2>{data.get('title', 'Notification')}</h2>
            <p>{data.get('message', '')}</p>
        """
        
        # Add type-specific content
        if notification_type == 'sample_approval_required':
            body += f"""
            <h3>Sample Approval Required</h3>
            <p>A sample set requires your approval:</p>
            <ul>
                <li>Cycle: {data.get('cycle_name', 'N/A')}</li>
                <li>Report: {data.get('report_name', 'N/A')}</li>
                <li>Sample Set: {data.get('sample_set_name', 'N/A')}</li>
                <li>Submitted By: {data.get('submitted_by', 'N/A')}</li>
            </ul>
            <p>Please log in to review and approve the samples.</p>
            """
        
        elif notification_type == 'sample_approved':
            body += f"""
            <h3>Samples Approved</h3>
            <p>Your sample set has been approved:</p>
            <ul>
                <li>Sample Set: {data.get('sample_set_name', 'N/A')}</li>
                <li>Approved By: {data.get('approved_by', 'N/A')}</li>
                <li>Comments: {data.get('comments', 'None')}</li>
            </ul>
            """
        
        elif notification_type == 'sample_rejected':
            body += f"""
            <h3>Samples Rejected</h3>
            <p>Your sample set has been rejected:</p>
            <ul>
                <li>Sample Set: {data.get('sample_set_name', 'N/A')}</li>
                <li>Rejected By: {data.get('rejected_by', 'N/A')}</li>
                <li>Reason: {data.get('reason', 'No reason provided')}</li>
            </ul>
            <p>Please review the feedback and resubmit.</p>
            """
        
        elif notification_type == 'phase_completed':
            body += f"""
            <h3>Phase Completed</h3>
            <p>A workflow phase has been completed:</p>
            <ul>
                <li>Phase: {data.get('phase_name', 'N/A')}</li>
                <li>Cycle: {data.get('cycle_name', 'N/A')}</li>
                <li>Report: {data.get('report_name', 'N/A')}</li>
                <li>Completed By: {data.get('completed_by', 'N/A')}</li>
            </ul>
            """
        
        elif notification_type == 'task_assigned':
            body += f"""
            <h3>New Task Assigned</h3>
            <p>You have been assigned a new task:</p>
            <ul>
                <li>Task: {data.get('task_name', 'N/A')}</li>
                <li>Phase: {data.get('phase_name', 'N/A')}</li>
                <li>Due Date: {data.get('due_date', 'N/A')}</li>
                <li>Priority: {data.get('priority', 'Normal')}</li>
            </ul>
            <p>Please log in to view task details.</p>
            """
        
        elif notification_type == 'sla_warning':
            body += f"""
            <h3>SLA Warning</h3>
            <p>An SLA deadline is approaching:</p>
            <ul>
                <li>Task: {data.get('task_name', 'N/A')}</li>
                <li>Time Remaining: {data.get('time_remaining', 'N/A')}</li>
                <li>SLA Deadline: {data.get('sla_deadline', 'N/A')}</li>
            </ul>
            <p>Please complete the task before the deadline.</p>
            """
        
        elif notification_type == 'sla_breach':
            body += f"""
            <h3>SLA Breach Alert</h3>
            <p style="color: red;">An SLA has been breached:</p>
            <ul>
                <li>Task: {data.get('task_name', 'N/A')}</li>
                <li>Breached At: {data.get('breach_time', 'N/A')}</li>
                <li>Assigned To: {data.get('assigned_to', 'N/A')}</li>
            </ul>
            <p>Immediate action required.</p>
            """
        
        # Close template
        body += """
            <hr>
            <p style="font-size: 0.9em; color: #666;">
                This is an automated notification from SynapseDTE. 
                Please do not reply to this email.
            </p>
        </body>
        </html>
        """
        
        return body