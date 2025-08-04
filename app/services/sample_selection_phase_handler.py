"""
Sample Selection Phase Handler
Handles phase status updates based on Report Owner decisions
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.workflow import WorkflowPhase
from app.models.universal_assignment import UniversalAssignment
from app.core.logging import get_logger
from datetime import datetime

logger = get_logger(__name__)


class SampleSelectionPhaseHandler:
    """Handle phase status updates for Sample Selection"""
    
    @staticmethod
    async def handle_assignment_completion(
        db: AsyncSession,
        assignment: UniversalAssignment
    ) -> None:
        """Handle phase updates when a Sample Selection assignment is completed"""
        
        if assignment.assignment_type != "Sample Selection Approval":
            return
            
        completion_data = assignment.completion_data or {}
        decision = completion_data.get('decision')
        
        if decision not in ['approved', 'rejected', 'revision_required']:
            return
            
        # Get the workflow phase
        context_data = assignment.context_data or {}
        cycle_id = context_data.get('cycle_id')
        report_id = context_data.get('report_id')
        
        if not cycle_id or not report_id:
            logger.warning(f"Missing cycle_id or report_id in assignment {assignment.assignment_id}")
            return
            
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase = phase_query.scalar_one_or_none()
        
        if not phase:
            logger.warning(f"Sample Selection phase not found for cycle {cycle_id}, report {report_id}")
            return
            
        # Update phase based on decision
        if decision == 'approved':
            phase.status = "Complete"
            phase.completed_by = assignment.completed_by_user_id
            phase.actual_end_date = datetime.utcnow()
            
            # Update the submission status in phase data
            if phase.phase_data and 'submissions' in phase.phase_data:
                submission_id = context_data.get('submission_id')
                for submission in phase.phase_data['submissions']:
                    if submission.get('submission_id') == submission_id:
                        submission['status'] = 'approved'
                        submission['reviewed_at'] = datetime.utcnow().isoformat()
                        submission['reviewed_by'] = assignment.completed_by_user_id
                        submission['review_decision'] = 'approved'
                        submission['review_feedback'] = completion_data.get('feedback', '')
                        break
                        
        elif decision == 'rejected':
            phase.status = "In Progress"  # Allow resubmission
            
            # Update the submission status
            if phase.phase_data and 'submissions' in phase.phase_data:
                submission_id = context_data.get('submission_id')
                for submission in phase.phase_data['submissions']:
                    if submission.get('submission_id') == submission_id:
                        submission['status'] = 'rejected'
                        submission['reviewed_at'] = datetime.utcnow().isoformat()
                        submission['reviewed_by'] = assignment.completed_by_user_id
                        submission['review_decision'] = 'rejected'
                        submission['review_feedback'] = completion_data.get('feedback', '')
                        break
                        
        elif decision == 'revision_required':
            phase.status = "In Progress"  # Allow revision
            
            # Update the submission status
            if phase.phase_data and 'submissions' in phase.phase_data:
                submission_id = context_data.get('submission_id')
                for submission in phase.phase_data['submissions']:
                    if submission.get('submission_id') == submission_id:
                        submission['status'] = 'revision_required'
                        submission['reviewed_at'] = datetime.utcnow().isoformat()
                        submission['reviewed_by'] = assignment.completed_by_user_id
                        submission['review_decision'] = 'revision_required'
                        submission['review_feedback'] = completion_data.get('feedback', '')
                        break
                        
                # Update individual sample decisions
                samples = phase.phase_data.get('cycle_report_sample_selection_samples', [])
                individual_decisions = completion_data.get('individual_decisions', {})
                individual_feedback = completion_data.get('individual_feedback', {})
                
                for sample in samples:
                    sample_id = sample.get('sample_id')
                    if sample_id in individual_decisions:
                        sample['report_owner_decision'] = individual_decisions[sample_id]
                        sample['report_owner_feedback'] = individual_feedback.get(sample_id, '')
                        sample['report_owner_reviewed_at'] = datetime.utcnow().isoformat()
                        sample['report_owner_reviewed_by'] = assignment.completed_by_user_id
        
        # Flag the phase data as modified
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(phase, 'phase_data')
        
        phase.updated_at = datetime.utcnow()
        phase.updated_by_id = assignment.completed_by_user_id
        
        await db.commit()
        
        logger.info(
            f"Updated Sample Selection phase status to {phase.status} "
            f"for cycle {cycle_id}, report {report_id} based on {decision} decision"
        )