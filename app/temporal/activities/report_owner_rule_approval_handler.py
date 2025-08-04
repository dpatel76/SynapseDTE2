"""
Report Owner Rule Approval Handler for Data Profiling Phase
Integrates with Universal Assignment Framework and Versioning System
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, and_, or_, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.workflow import WorkflowActivity, WorkflowActivityStatus
from app.models.data_profiling import ProfilingRule, ProfilingRuleStatus
from app.models.universal_assignment import UniversalAssignment, AssignmentType, AssignmentStatus
from app.models.versioning import create_version
from app.services.universal_assignment_service import UniversalAssignmentService
from app.services.workflow_service import WorkflowService
from app.services.email_service import EmailService
from app.temporal.shared.activity_context import ActivityContext

logger = get_logger(__name__)


class ReportOwnerRuleApprovalHandler:
    """Handler for Report Owner approval of data profiling rules"""
    
    def __init__(self):
        self.assignment_service = UniversalAssignmentService()
        self.workflow_service = WorkflowService()
        self.email_service = EmailService()
    
    async def execute(self, context: ActivityContext) -> Dict[str, Any]:
        """
        Execute Report Owner rule approval activity
        
        This handler:
        1. Checks if rules have been sent by Tester for approval
        2. Creates/updates universal assignment for Report Owner
        3. Monitors assignment status
        4. Auto-completes when all rules are approved
        5. Supports versioning for rule resubmissions
        """
        async with get_db_context() as db:
            try:
                activity = await self._get_activity(db, context.activity_id)
                
                # Check if this is the initial trigger or a status check
                if activity.status == WorkflowActivityStatus.NOT_STARTED:
                    # Initial trigger - check if Tester has sent rules
                    return await self._initialize_approval(db, activity, context)
                elif activity.status == WorkflowActivityStatus.IN_PROGRESS:
                    # Status check - monitor assignment progress
                    return await self._check_approval_status(db, activity, context)
                else:
                    logger.warning(f"Unexpected activity status: {activity.status}")
                    return {
                        "status": "error",
                        "message": f"Unexpected activity status: {activity.status}"
                    }
                    
            except Exception as e:
                logger.error(f"Error in Report Owner rule approval: {str(e)}")
                return {
                    "status": "error",
                    "error": str(e)
                }
    
    async def _get_activity(self, db: AsyncSession, activity_id: int) -> WorkflowActivity:
        """Get the workflow activity"""
        result = await db.execute(
            select(WorkflowActivity).where(WorkflowActivity.activity_id == activity_id)
        )
        activity = result.scalar_one_or_none()
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")
        return activity
    
    async def _initialize_approval(self, db: AsyncSession, activity: WorkflowActivity, 
                                 context: ActivityContext) -> Dict[str, Any]:
        """Initialize the Report Owner approval process"""
        # Check if there's an existing assignment from Tester
        existing_assignment = await self._find_existing_assignment(
            db, 
            activity.cycle_id, 
            activity.report_id
        )
        
        if not existing_assignment:
            # No assignment yet - activity should wait
            logger.info(f"No rules sent for approval yet for cycle {activity.cycle_id}, report {activity.report_id}")
            return {
                "status": "waiting",
                "message": "Waiting for Tester to send rules for approval",
                "can_start": False
            }
        
        # Check if assignment has version_id
        version_id = existing_assignment.context_data.get('version_id')
        if not version_id:
            logger.info("Assignment exists but no version_id found")
            return {
                "status": "waiting",
                "message": "Waiting for valid version assignment",
                "can_start": False
            }
        
        # Check if there are approved rules in this version
        from app.models.data_profiling import ProfilingRule, Decision
        approved_rules_query = await db.execute(
            select(func.count(ProfilingRule.rule_id))
            .where(
                and_(
                    ProfilingRule.version_id == version_id,
                    ProfilingRule.tester_decision == Decision.APPROVED
                )
            )
        )
        approved_rules_count = approved_rules_query.scalar() or 0
        
        if approved_rules_count == 0:
            logger.info(f"No tester-approved rules found in version {version_id}")
            return {
                "status": "waiting",
                "message": "Waiting for Tester to approve rules before sending to Report Owner",
                "can_start": False
            }
        
        # Start the activity
        activity.status = WorkflowActivityStatus.IN_PROGRESS
        activity.started_at = datetime.now(timezone.utc)
        activity.started_by = existing_assignment.from_user_id
        
        # Update assignment status if needed
        if existing_assignment.status == AssignmentStatus.CREATED:
            existing_assignment.status = AssignmentStatus.ASSIGNED
        
        await db.commit()
        
        # Send notification to Report Owner
        await self._send_notification(existing_assignment)
        
        return {
            "status": "started",
            "message": f"Report Owner approval started with {approved_rules_count} rules",
            "assignment_id": existing_assignment.assignment_id,
            "rules_for_approval": approved_rules_count
        }
    
    async def _check_approval_status(self, db: AsyncSession, activity: WorkflowActivity,
                                   context: ActivityContext) -> Dict[str, Any]:
        """Check the status of Report Owner approval"""
        assignment = await self._find_existing_assignment(
            db,
            activity.cycle_id,
            activity.report_id
        )
        
        if not assignment:
            return {
                "status": "error",
                "message": "Assignment not found"
            }
        
        # Get version_id from assignment
        version_id = assignment.context_data.get('version_id')
        if not version_id:
            return {
                "status": "error",
                "message": "No version_id found in assignment"
            }
        
        # Get rules statistics from database
        from app.models.data_profiling import ProfilingRule, Decision
        
        # Count total tester-approved rules
        total_rules_query = await db.execute(
            select(func.count(ProfilingRule.rule_id))
            .where(
                and_(
                    ProfilingRule.version_id == version_id,
                    ProfilingRule.tester_decision == Decision.APPROVED
                )
            )
        )
        total_rules = total_rules_query.scalar() or 0
        
        # Count rules with report owner decisions
        decided_rules_query = await db.execute(
            select(func.count(ProfilingRule.rule_id))
            .where(
                and_(
                    ProfilingRule.version_id == version_id,
                    ProfilingRule.tester_decision == Decision.APPROVED,
                    ProfilingRule.report_owner_decision.isnot(None)
                )
            )
        )
        decided_rules = decided_rules_query.scalar() or 0
        
        # Count approved by report owner
        approved_by_owner_query = await db.execute(
            select(func.count(ProfilingRule.rule_id))
            .where(
                and_(
                    ProfilingRule.version_id == version_id,
                    ProfilingRule.tester_decision == Decision.APPROVED,
                    ProfilingRule.report_owner_decision == Decision.APPROVED
                )
            )
        )
        approved_by_owner = approved_by_owner_query.scalar() or 0
        
        # Count rejected by report owner
        rejected_by_owner_query = await db.execute(
            select(func.count(ProfilingRule.rule_id))
            .where(
                and_(
                    ProfilingRule.version_id == version_id,
                    ProfilingRule.tester_decision == Decision.APPROVED,
                    ProfilingRule.report_owner_decision == Decision.REJECTED
                )
            )
        )
        rejected_by_owner = rejected_by_owner_query.scalar() or 0
        
        # Check if all rules have been decided
        if decided_rules == total_rules:
            if rejected_by_owner == 0:
                # All approved - complete the activity
                return await self._complete_approval(db, activity, assignment)
            else:
                # Some rejected - need resubmission
                return await self._handle_rejections(db, activity, assignment)
        
        # Still in progress
        progress_percentage = (decided_rules / total_rules * 100) if total_rules > 0 else 0
        
        return {
            "status": "in_progress",
            "message": f"Report Owner review in progress: {decided_rules}/{total_rules} rules decided",
            "progress": progress_percentage,
            "approved": approved_by_owner,
            "rejected": rejected_by_owner,
            "pending": total_rules - decided_rules
        }
    
    async def _complete_approval(self, db: AsyncSession, activity: WorkflowActivity,
                               assignment: UniversalAssignment) -> Dict[str, Any]:
        """Complete the approval activity when all rules are approved"""
        # Mark activity as completed
        activity.status = WorkflowActivityStatus.COMPLETED
        activity.completed_at = datetime.now(timezone.utc)
        activity.completed_by = assignment.to_user_id
        
        # Update assignment status
        assignment.status = AssignmentStatus.COMPLETED
        assignment.completed_at = datetime.now(timezone.utc)
        
        # Get version_id from assignment
        version_id = assignment.context_data.get('version_id')
        if version_id:
            # Update all tester-approved rules that are also report-owner-approved to final approved status
            from app.models.data_profiling import Decision
            await db.execute(
                update(ProfilingRule)
                .where(
                    and_(
                        ProfilingRule.version_id == version_id,
                        ProfilingRule.tester_decision == Decision.APPROVED,
                        ProfilingRule.report_owner_decision == Decision.APPROVED
                    )
                )
                .values(
                    status=ProfilingRuleStatus.APPROVED,
                    updated_at=datetime.now(timezone.utc),
                    updated_by_id=assignment.to_user_id
                )
            )
            
            # Count how many rules were approved
            approved_count_query = await db.execute(
                select(func.count(ProfilingRule.rule_id))
                .where(
                    and_(
                        ProfilingRule.version_id == version_id,
                        ProfilingRule.status == ProfilingRuleStatus.APPROVED
                    )
                )
            )
            approved_count = approved_count_query.scalar() or 0
        else:
            approved_count = 0
        
        await db.commit()
        
        # Trigger next activity
        await self.workflow_service.trigger_next_activity(activity)
        
        return {
            "status": "completed",
            "message": f"All {approved_count} rules approved by Report Owner",
            "next_activity": "Execute Profiling"
        }
    
    async def _handle_rejections(self, db: AsyncSession, activity: WorkflowActivity,
                                assignment: UniversalAssignment) -> Dict[str, Any]:
        """Handle rejected rules - create new version and assignment for resubmission"""
        version_id = assignment.context_data.get('version_id')
        if not version_id:
            return {
                "status": "error",
                "message": "No version_id found in assignment"
            }
        
        # Get rejected rules from database
        from app.models.data_profiling import Decision
        rejected_rules_query = await db.execute(
            select(ProfilingRule)
            .where(
                and_(
                    ProfilingRule.version_id == version_id,
                    ProfilingRule.tester_decision == Decision.APPROVED,
                    ProfilingRule.report_owner_decision == Decision.REJECTED
                )
            )
        )
        rejected_rules = rejected_rules_query.scalars().all()
        
        # Create new versions for rejected rules
        for rule in rejected_rules:
            # Create new version
            new_version = await create_version(
                db,
                ProfilingRule,
                rule,
                reason_for_change=rule.report_owner_notes or 'Rejected by Report Owner',
                changed_by=assignment.to_user_id
            )
            
            # Update status to indicate revision needed
            new_version.status = ProfilingRuleStatus.NEEDS_REVISION
            new_version.revision_notes = rule.report_owner_notes or ''
        
        # Get report and cycle info for context_data
        from app.models.report import Report
        from app.models.test_cycle import TestCycle
        report_result = await db.execute(select(Report).where(Report.report_id == activity.report_id))
        report = report_result.scalar_one_or_none()
        cycle = await db.get(TestCycle, activity.cycle_id)
        
        # Create feedback assignment for Tester
        feedback_assignment = UniversalAssignment(
            assignment_type=AssignmentType.FEEDBACK,
            from_user_id=assignment.to_user_id,
            from_role=assignment.to_role,
            to_user_id=assignment.from_user_id,
            to_role=assignment.from_role,
            title=f"Data Profiling Rules Feedback - {len(rejected_rules)} rules need revision",
            description=f"The Report Owner has reviewed the rules and {len(rejected_rules)} rules need revision. Please review the feedback and resubmit.",
            context_type="Report",
            context_data={
                "cycle_id": activity.cycle_id,
                "report_id": activity.report_id,
                "report_name": report.report_name if report else None,
                "cycle_name": cycle.cycle_name if cycle else None,
                "phase": "data_profiling",
                "version_id": version_id,
                "rejected_rules_count": len(rejected_rules),
                "original_assignment_id": assignment.assignment_id
            },
            priority="High",
            due_date=datetime.now(timezone.utc)
        )
        
        db.add(feedback_assignment)
        
        # Update original assignment
        assignment.status = AssignmentStatus.REJECTED
        assignment.rejection_reason = f"{len(rejected_rules)} rules rejected"
        
        await db.commit()
        
        return {
            "status": "needs_revision",
            "message": f"{len(rejected_rules)} rules rejected and need revision",
            "feedback_assignment_id": feedback_assignment.assignment_id,
            "rejected_rules": len(rejected_rules)
        }
    
    async def _find_existing_assignment(self, db: AsyncSession, cycle_id: int, 
                                      report_id: int) -> Optional[UniversalAssignment]:
        """Find existing assignment for Report Owner approval"""
        result = await db.execute(
            select(UniversalAssignment)
            .where(
                and_(
                    UniversalAssignment.assignment_type == AssignmentType.RULE_APPROVAL,
                    UniversalAssignment.to_role == 'Report Owner',
                    UniversalAssignment.context_type == 'Report',
                    UniversalAssignment.context_data['cycle_id'].astext == str(cycle_id),
                    UniversalAssignment.context_data['report_id'].astext == str(report_id),
                    UniversalAssignment.context_data['phase'].astext == 'data_profiling',
                    UniversalAssignment.status.in_([
                        AssignmentStatus.CREATED,
                        AssignmentStatus.ASSIGNED,
                        AssignmentStatus.ACKNOWLEDGED,
                        AssignmentStatus.IN_PROGRESS
                    ])
                )
            )
            .order_by(UniversalAssignment.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def _send_notification(self, assignment: UniversalAssignment):
        """Send notification to Report Owner about new assignment"""
        if self.email_service and assignment.to_user:
            try:
                await self.email_service.send_assignment_notification(
                    to_email=assignment.to_user.email,
                    assignment_title=assignment.title,
                    assignment_description=assignment.description,
                    due_date=assignment.due_date
                )
            except Exception as e:
                logger.error(f"Failed to send notification: {str(e)}")


# Activity function for Temporal
async def report_owner_rule_approval_activity(context: ActivityContext) -> Dict[str, Any]:
    """Temporal activity function for Report Owner rule approval"""
    handler = ReportOwnerRuleApprovalHandler()
    return await handler.execute(context)