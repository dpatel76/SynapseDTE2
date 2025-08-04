"""
Universal Assignment Service
Handles all role-to-role interactions, approvals, and task assignments across the system
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, update
from sqlalchemy.orm import selectinload

from app.models.universal_assignment import (
    UniversalAssignment, UniversalAssignmentHistory, AssignmentTemplate
)
from app.models.user import User
from app.models.report import Report
from app.models.test_cycle import TestCycle
from app.services.email_service import EmailService
from app.models.audit import AuditLog
from app.core.logging import get_logger

logger = get_logger(__name__)


class UniversalAssignmentService:
    """Service for managing universal assignments across all role interactions"""
    
    def __init__(self, db: AsyncSession, email_service: EmailService = None):
        self.db = db
        self.email_service = email_service or EmailService()
    
    async def create_assignment(
        self,
        assignment_type: str,
        from_role: str,
        to_role: str,
        from_user_id: int,
        to_user_id: Optional[int],
        title: str,
        description: str,
        context_type: str,
        context_data: Dict[str, Any],
        task_instructions: Optional[str] = None,
        priority: str = "Medium",
        due_date: Optional[datetime] = None,
        requires_approval: bool = False,
        approval_role: Optional[str] = None,
        assignment_metadata: Optional[Dict[str, Any]] = None
    ) -> UniversalAssignment:
        """Create a new universal assignment"""
        
        # Auto-assign to appropriate user if to_user_id not specified
        if not to_user_id:
            to_user_id = await self._find_user_by_role(to_role, context_data)
        
        # Set default due date based on assignment type
        if not due_date:
            due_date = await self._calculate_default_due_date(assignment_type)
        
        # Create assignment
        assignment = UniversalAssignment(
            assignment_type=assignment_type,
            from_role=from_role,
            to_role=to_role,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            title=title,
            description=description,
            task_instructions=task_instructions,
            context_type=context_type,
            context_data=context_data,
            priority=priority,
            due_date=due_date,
            requires_approval=requires_approval,
            approval_role=approval_role,
            assignment_metadata=assignment_metadata or {}
        )
        
        self.db.add(assignment)
        await self.db.flush()  # Get the assignment_id
        
        # Create audit log
        await self._create_audit_log(
            assignment.assignment_id,
            from_user_id,
            "created",
            None,
            {
                "title": title,
                "type": assignment_type,
                "from_role": from_role,
                "to_role": to_role,
                "priority": priority
            },
            "Assignment created"
        )
        
        # Load user info before commit for notification
        await self.db.refresh(assignment, ["to_user", "from_user"])
        
        await self.db.commit()
        
        # Send notification
        await self._send_assignment_notification(assignment)
        
        logger.info(f"Created universal assignment {assignment.assignment_id}: {title}")
        return assignment
    
    async def get_assignment(self, assignment_id: str) -> Optional[UniversalAssignment]:
        """Get assignment by ID"""
        query = await self.db.execute(
            select(UniversalAssignment)
            .options(
                selectinload(UniversalAssignment.from_user),
                selectinload(UniversalAssignment.to_user),
                selectinload(UniversalAssignment.completed_by_user),
                selectinload(UniversalAssignment.approved_by_user)
            )
            .where(UniversalAssignment.assignment_id == assignment_id)
        )
        return query.scalar_one_or_none()
    
    async def get_assignments_for_user(
        self,
        user_id: int,
        status_filter: Optional[List[str]] = None,
        assignment_type_filter: Optional[Union[str, List[str]]] = None,
        context_type_filter: Optional[str] = None,
        role_filter: Optional[str] = None,  # Filter by to_role or from_role
        limit: int = 50
    ) -> List[UniversalAssignment]:
        """Get assignments for a specific user"""
        
        # User can be involved as receiver or creator
        user_conditions = or_(
            UniversalAssignment.to_user_id == user_id,
            UniversalAssignment.from_user_id == user_id
        )
        
        query = select(UniversalAssignment).options(
            selectinload(UniversalAssignment.from_user),
            selectinload(UniversalAssignment.to_user)
        ).where(user_conditions)
        
        if status_filter:
            query = query.where(UniversalAssignment.status.in_(status_filter))
        
        if assignment_type_filter:
            if isinstance(assignment_type_filter, list):
                query = query.where(UniversalAssignment.assignment_type.in_(assignment_type_filter))
            else:
                query = query.where(UniversalAssignment.assignment_type == assignment_type_filter)
        
        if context_type_filter:
            # Handle comma-separated context types
            if ',' in context_type_filter:
                context_type_list = [s.strip() for s in context_type_filter.split(",")]
                query = query.where(UniversalAssignment.context_type.in_(context_type_list))
            else:
                query = query.where(UniversalAssignment.context_type == context_type_filter)
        
        if role_filter:
            query = query.where(
                or_(
                    UniversalAssignment.to_role == role_filter,
                    UniversalAssignment.from_role == role_filter
                )
            )
        
        query = query.order_by(desc(UniversalAssignment.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_assignments_by_context(
        self,
        context_type: str,
        context_data: Dict[str, Any],
        status_filter: Optional[List[str]] = None
    ) -> List[UniversalAssignment]:
        """Get assignments for a specific context (e.g., all assignments for a cycle/report)"""
        
        # Build context filter based on provided data
        context_conditions = []
        if "cycle_id" in context_data:
            context_conditions.append(
                UniversalAssignment.context_data['cycle_id'].astext == str(context_data["cycle_id"])
            )
        if "report_id" in context_data:
            context_conditions.append(
                UniversalAssignment.context_data['report_id'].astext == str(context_data["report_id"])
            )
        if "phase_name" in context_data:
            context_conditions.append(
                UniversalAssignment.context_data['phase_name'].astext == context_data["phase_name"]
            )
        
        query = select(UniversalAssignment).options(
            selectinload(UniversalAssignment.from_user),
            selectinload(UniversalAssignment.to_user)
        ).where(
            and_(
                UniversalAssignment.context_type == context_type,
                *context_conditions
            )
        )
        
        if status_filter:
            query = query.where(UniversalAssignment.status.in_(status_filter))
        
        query = query.order_by(desc(UniversalAssignment.created_at))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def acknowledge_assignment(
        self,
        assignment_id: str,
        user_id: int
    ) -> UniversalAssignment:
        """Mark assignment as acknowledged"""
        
        assignment = await self.get_assignment(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        
        if assignment.to_user_id != user_id:
            raise ValueError("Only the assigned user can acknowledge the assignment")
        
        old_status = assignment.status
        assignment.acknowledge(user_id)
        
        await self._create_audit_log(
            assignment_id,
            user_id,
            "acknowledged",
            {"status": old_status},
            {"status": assignment.status, "acknowledged_at": assignment.acknowledged_at.isoformat()},
            "Assignment acknowledged"
        )
        
        await self.db.commit()
        
        logger.info(f"Assignment {assignment_id} acknowledged by user {user_id}")
        return assignment
    
    async def start_assignment(
        self,
        assignment_id: str,
        user_id: int
    ) -> UniversalAssignment:
        """Mark assignment as in progress"""
        
        assignment = await self.get_assignment(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        
        if assignment.to_user_id != user_id:
            raise ValueError("Only the assigned user can start the assignment")
        
        old_status = assignment.status
        assignment.start_work(user_id)
        
        await self._create_audit_log(
            assignment_id,
            user_id,
            "started",
            {"status": old_status},
            {"status": assignment.status, "started_at": assignment.started_at.isoformat()},
            "Assignment started"
        )
        
        await self.db.commit()
        
        logger.info(f"Assignment {assignment_id} started by user {user_id}")
        return assignment
    
    async def complete_assignment(
        self,
        assignment_id: str,
        user_id: int,
        completion_notes: Optional[str] = None,
        completion_data: Optional[Dict[str, Any]] = None,
        completion_attachments: Optional[List[Dict[str, Any]]] = None
    ) -> UniversalAssignment:
        """Mark assignment as completed"""
        
        assignment = await self.get_assignment(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        
        if assignment.to_user_id != user_id and assignment.delegated_to_user_id != user_id:
            raise ValueError("Only the assigned user can complete the assignment")
        
        old_status = assignment.status
        assignment.complete(user_id, completion_notes, completion_data)
        
        if completion_attachments:
            assignment.completion_attachments = completion_attachments
        
        await self._create_audit_log(
            assignment_id,
            user_id,
            "completed",
            {"status": old_status},
            {
                "status": assignment.status,
                "completed_at": assignment.completed_at.isoformat(),
                "completion_notes": completion_notes
            },
            f"Assignment completed: {completion_notes or 'No notes'}"
        )
        
        await self.db.commit()
        
        # Handle phase-specific updates
        if assignment.assignment_type == "Sample Selection Approval":
            from app.services.sample_selection_phase_handler import SampleSelectionPhaseHandler
            await SampleSelectionPhaseHandler.handle_assignment_completion(self.db, assignment)
        
        # Update version metadata for all phase reviews
        if assignment.assignment_type in [
            "Sample Selection Approval",
            "Scoping Approval", 
            "Rule Approval"
        ]:
            from app.services.version_metadata_updater import VersionMetadataUpdater
            await VersionMetadataUpdater.handle_assignment_completion(self.db, assignment)
        
        # Send completion notification to originator
        await self._send_completion_notification(assignment)
        
        logger.info(f"Assignment {assignment_id} completed by user {user_id}")
        return assignment
    
    async def approve_assignment(
        self,
        assignment_id: str,
        user_id: int,
        approval_notes: Optional[str] = None
    ) -> UniversalAssignment:
        """Approve a completed assignment"""
        
        assignment = await self.get_assignment(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        
        if not assignment.requires_approval:
            raise ValueError("Assignment does not require approval")
        
        if assignment.status != "Completed":
            raise ValueError("Assignment must be completed before approval")
        
        # Check if user has approval authority
        user_query = await self.db.execute(select(User).where(User.user_id == user_id))
        user = user_query.scalar_one_or_none()
        
        if not user or (assignment.approval_role and user.role != assignment.approval_role):
            raise ValueError("User does not have approval authority for this assignment")
        
        old_status = assignment.status
        assignment.approve(user_id, approval_notes)
        
        await self._create_audit_log(
            assignment_id,
            user_id,
            "approved",
            {"status": old_status},
            {
                "status": assignment.status,
                "approved_at": assignment.approved_at.isoformat(),
                "approval_notes": approval_notes
            },
            f"Assignment approved: {approval_notes or 'No notes'}"
        )
        
        await self.db.commit()
        
        # Send approval notification
        await self._send_approval_notification(assignment)
        
        logger.info(f"Assignment {assignment_id} approved by user {user_id}")
        return assignment
    
    async def reject_assignment(
        self,
        assignment_id: str,
        user_id: int,
        rejection_reason: str
    ) -> UniversalAssignment:
        """Reject a completed assignment"""
        
        assignment = await self.get_assignment(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        
        if assignment.status != "Completed":
            raise ValueError("Assignment must be completed before rejection")
        
        old_status = assignment.status
        assignment.reject(user_id, rejection_reason)
        
        await self._create_audit_log(
            assignment_id,
            user_id,
            "rejected",
            {"status": old_status},
            {
                "status": assignment.status,
                "approved_at": assignment.approved_at.isoformat(),
                "approval_notes": rejection_reason
            },
            f"Assignment rejected: {rejection_reason}"
        )
        
        await self.db.commit()
        
        # Send rejection notification
        await self._send_rejection_notification(assignment)
        
        logger.info(f"Assignment {assignment_id} rejected by user {user_id}")
        return assignment
    
    async def escalate_assignment(
        self,
        assignment_id: str,
        user_id: int,
        escalation_reason: str,
        escalated_to_user_id: Optional[int] = None
    ) -> UniversalAssignment:
        """Escalate an assignment"""
        
        assignment = await self.get_assignment(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        
        old_status = assignment.status
        assignment.escalate(user_id, escalation_reason, escalated_to_user_id)
        
        await self._create_audit_log(
            assignment_id,
            user_id,
            "escalated",
            {"status": old_status, "escalated": False},
            {
                "status": assignment.status,
                "escalated": True,
                "escalation_reason": escalation_reason,
                "escalated_to_user_id": escalated_to_user_id
            },
            f"Assignment escalated: {escalation_reason}"
        )
        
        await self.db.commit()
        
        # Send escalation notification
        await self._send_escalation_notification(assignment)
        
        logger.info(f"Assignment {assignment_id} escalated by user {user_id}")
        return assignment
    
    async def delegate_assignment(
        self,
        assignment_id: str,
        user_id: int,
        delegated_to_user_id: int,
        delegation_reason: Optional[str] = None
    ) -> UniversalAssignment:
        """Delegate an assignment to another user"""
        
        assignment = await self.get_assignment(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        
        if assignment.to_user_id != user_id:
            raise ValueError("Only the assigned user can delegate the assignment")
        
        old_status = assignment.status
        assignment.delegate(user_id, delegated_to_user_id, delegation_reason)
        
        await self._create_audit_log(
            assignment_id,
            user_id,
            "delegated",
            {"status": old_status, "delegated_to_user_id": None},
            {
                "status": assignment.status,
                "delegated_to_user_id": delegated_to_user_id,
                "delegation_reason": delegation_reason
            },
            f"Assignment delegated: {delegation_reason or 'No reason provided'}"
        )
        
        await self.db.commit()
        
        # Send delegation notification
        await self._send_delegation_notification(assignment)
        
        logger.info(f"Assignment {assignment_id} delegated by user {user_id} to user {delegated_to_user_id}")
        return assignment
    
    async def get_assignment_metrics(
        self,
        user_id: Optional[int] = None,
        role: Optional[str] = None,
        assignment_type: Optional[str] = None,
        context_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get assignment metrics"""
        
        base_query = select(UniversalAssignment)
        
        # Apply filters
        conditions = []
        if user_id:
            conditions.append(
                or_(
                    UniversalAssignment.to_user_id == user_id,
                    UniversalAssignment.from_user_id == user_id
                )
            )
        
        if role:
            conditions.append(
                or_(
                    UniversalAssignment.to_role == role,
                    UniversalAssignment.from_role == role
                )
            )
        
        if assignment_type:
            conditions.append(UniversalAssignment.assignment_type == assignment_type)
        
        if context_type:
            conditions.append(UniversalAssignment.context_type == context_type)
        
        if date_from:
            conditions.append(UniversalAssignment.created_at >= date_from)
        
        if date_to:
            conditions.append(UniversalAssignment.created_at <= date_to)
        
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # Get total count
        total_query = await self.db.execute(
            select(func.count(UniversalAssignment.assignment_id)).select_from(base_query.subquery())
        )
        total_assignments = total_query.scalar() or 0
        
        # Get status counts
        status_query = await self.db.execute(
            select(
                UniversalAssignment.status,
                func.count(UniversalAssignment.assignment_id)
            ).select_from(base_query.subquery()).group_by(UniversalAssignment.status)
        )
        status_counts = dict(status_query.fetchall())
        
        # Calculate completion metrics
        completed = status_counts.get('Completed', 0) + status_counts.get('Approved', 0)
        completion_rate = (completed / total_assignments * 100) if total_assignments > 0 else 0
        
        # Get overdue count
        now = datetime.now(timezone.utc)
        overdue_query = await self.db.execute(
            base_query.where(
                and_(
                    UniversalAssignment.due_date < now,
                    UniversalAssignment.status.in_(['Assigned', 'Acknowledged', 'In Progress'])
                )
            )
        )
        overdue_assignments = len(overdue_query.scalars().all())
        
        return {
            "total_assignments": total_assignments,
            "pending_assignments": status_counts.get('Assigned', 0),
            "acknowledged_assignments": status_counts.get('Acknowledged', 0),
            "in_progress_assignments": status_counts.get('In Progress', 0),
            "completed_assignments": status_counts.get('Completed', 0),
            "approved_assignments": status_counts.get('Approved', 0),
            "rejected_assignments": status_counts.get('Rejected', 0),
            "escalated_assignments": status_counts.get('Escalated', 0),
            "overdue_assignments": overdue_assignments,
            "completion_rate": completion_rate,
            "status_breakdown": status_counts
        }
    
    # Helper methods
    async def _find_user_by_role(self, role: str, context_data: Dict[str, Any]) -> Optional[int]:
        """Find appropriate user by role and context"""
        
        # For Report Owner roles, try to find specific report owner
        if role in ["Report Owner", "Report Owner Executive"] and "report_id" in context_data:
            report_query = await self.db.execute(
                select(Report).where(Report.report_id == context_data["report_id"])
            )
            report = report_query.scalar_one_or_none()
            if report and report.report_owner_id:
                return report.report_owner_id
        
        # Otherwise, find any user with the role
        user_query = await self.db.execute(
            select(User.user_id).where(User.role == role).limit(1)
        )
        user = user_query.scalar_one_or_none()
        return user
    
    async def _calculate_default_due_date(self, assignment_type: str) -> Optional[datetime]:
        """Calculate default due date based on assignment type"""
        
        now = datetime.now(timezone.utc)
        
        # Default due dates by assignment type
        due_date_map = {
            "Data Upload Request": 7,
            "File Review": 3,
            "File Approval": 2,
            "Document Review": 5,
            "Data Validation": 3,
            "Scoping Approval": 2,
            "CycleReportSampleSelectionSamples Selection Approval": 2,
            "Rule Approval": 1,
            "Observation Approval": 1,
            "Report Approval": 3,
            "Version Approval": 1,
            "Phase Review": 2,
            "Phase Approval": 1,
            "Phase Completion": 1,
            "Workflow Progression": 1,
            "Information Request": 5,
            "Clarification Required": 3,
            "Additional Data Required": 7
        }
        
        days = due_date_map.get(assignment_type, 5)  # Default 5 days
        return now + timedelta(days=days)
    
    async def _create_audit_log(
        self,
        assignment_id: str,
        user_id: int,
        action: str,
        old_values: Optional[Dict[str, Any]],
        new_values: Optional[Dict[str, Any]],
        change_reason: str
    ):
        """Create audit log entry"""
        
        # Create assignment history
        from app.models.universal_assignment import UniversalAssignmentHistory
        history = UniversalAssignmentHistory(
            assignment_id=assignment_id,
            changed_by_user_id=user_id,
            action=action,
            old_value=str(old_values) if old_values else None,
            new_value=str(new_values) if new_values else None,
            change_reason=change_reason,
            change_metadata={"old_values": old_values, "new_values": new_values}
        )
        self.db.add(history)
        
        # Create general audit log
        # Note: record_id is INTEGER but assignment_id is UUID string, so we store it in new_values
        enhanced_new_values = (new_values or {}).copy()
        enhanced_new_values["assignment_id"] = assignment_id
        
        now = datetime.now(timezone.utc)
        audit_log = AuditLog(
            user_id=user_id,
            action=f"UNIVERSAL_ASSIGNMENT_{action.upper()}",
            table_name="universal_assignments",
            record_id=None,  # Cannot store UUID string in integer field
            old_values=old_values,
            new_values=enhanced_new_values,
            timestamp=now,
            created_at=now,
            updated_at=now
        )
        self.db.add(audit_log)
    
    async def _send_assignment_notification(self, assignment: UniversalAssignment):
        """Send notification for new assignment"""
        if not self.email_service or not assignment.to_user:
            return
        
        try:
            subject = f"New Assignment: {assignment.title}"
            body = f"""
You have been assigned a new task:

Title: {assignment.title}
Type: {assignment.assignment_type}
From: {assignment.from_role}
Priority: {assignment.priority}
Due Date: {assignment.due_date.strftime('%Y-%m-%d %H:%M') if assignment.due_date else 'No due date'}

Description:
{assignment.description or 'No description provided'}

Task Instructions:
{assignment.task_instructions or 'No specific instructions provided'}

Context: {assignment.context_type}
Assignment ID: {assignment.assignment_id}

Please log into the system to view and complete this assignment.
"""
            
            await self.email_service.send_email(
                to_emails=[assignment.to_user.email],  # Changed to list with plural parameter name
                subject=subject,
                body=body
            )
            
        except Exception as e:
            logger.error(f"Failed to send assignment notification: {str(e)}")
    
    async def _send_completion_notification(self, assignment: UniversalAssignment):
        """Send completion notification to assignment originator"""
        if not self.email_service or not assignment.from_user:
            return
        
        try:
            subject = f"Assignment Completed: {assignment.title}"
            completer_name = assignment.completed_by_user.full_name if assignment.completed_by_user else "Unknown User"
            
            body = f"""
Your assignment has been completed by {completer_name}:

Assignment: {assignment.title}
Type: {assignment.assignment_type}
Completed At: {assignment.completed_at.strftime('%Y-%m-%d %H:%M') if assignment.completed_at else 'Unknown'}

Completion Notes:
{assignment.completion_notes or 'No notes provided'}

Assignment ID: {assignment.assignment_id}
Context: {assignment.context_type}

You can now proceed with the next steps in your workflow.
"""
            
            await self.email_service.send_email(
                to_email=assignment.from_user.email,
                subject=subject,
                body=body
            )
            
        except Exception as e:
            logger.error(f"Failed to send completion notification: {str(e)}")
    
    async def _send_approval_notification(self, assignment: UniversalAssignment):
        """Send approval notification"""
        # TODO: Implement approval notification logic
        pass
    
    async def _send_rejection_notification(self, assignment: UniversalAssignment):
        """Send rejection notification"""
        # TODO: Implement rejection notification logic
        pass
    
    async def _send_escalation_notification(self, assignment: UniversalAssignment):
        """Send escalation notification"""
        # TODO: Implement escalation notification logic
        pass
    
    async def _send_delegation_notification(self, assignment: UniversalAssignment):
        """Send delegation notification"""
        # TODO: Implement delegation notification logic
        pass


# Convenience functions for common assignment patterns
async def create_data_upload_assignment(
    db: AsyncSession,
    cycle_id: int,
    report_id: int,
    from_user_id: int,
    description: str,
    priority: str = "High",
    email_service: EmailService = None
) -> UniversalAssignment:
    """Create a data upload assignment using the universal framework"""
    
    service = UniversalAssignmentService(db, email_service)
    
    return await service.create_assignment(
        assignment_type="Data Upload Request",
        from_role="Tester",
        to_role="Report Owner",
        from_user_id=from_user_id,
        to_user_id=None,  # Auto-assign to report owner
        title=f"Data Upload Required for Report {report_id}",
        description=description,
        context_type="Report",
        context_data={
            "cycle_id": cycle_id,
            "report_id": report_id,
            "phase_name": "Data Profiling"
        },
        task_instructions="Please upload the necessary data files for profiling analysis. Ensure files are in the correct format and contain all required attributes.",
        priority=priority,
        requires_approval=False
    )


async def create_approval_assignment(
    db: AsyncSession,
    cycle_id: int,
    report_id: int,
    from_user_id: int,
    approval_type: str,
    item_description: str,
    approver_role: str,
    priority: str = "Medium",
    email_service: EmailService = None
) -> UniversalAssignment:
    """Create an approval assignment using the universal framework"""
    
    service = UniversalAssignmentService(db, email_service)
    
    return await service.create_assignment(
        assignment_type=approval_type,
        from_role="Tester",  # Usually from Tester
        to_role=approver_role,
        from_user_id=from_user_id,
        to_user_id=None,  # Auto-assign based on role
        title=f"{approval_type} Required for {item_description}",
        description=f"Please review and approve the {item_description} for Report {report_id}.",
        context_type="Report",
        context_data={
            "cycle_id": cycle_id,
            "report_id": report_id,
            "approval_item": item_description
        },
        priority=priority,
        requires_approval=True,
        approval_role=approver_role
    )