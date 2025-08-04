#!/usr/bin/env python3
"""Reset sample selection phase for a specific cycle/report"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from app.core.database import AsyncSessionLocal
from app.models.workflow import WorkflowPhase
from app.models.sample_individual import IndividualSample, SampleSubmission, SampleSubmissionItem, SampleFeedback, SampleAuditLog
from app.models.cycle_report import CycleReport
import sys

async def reset_sample_selection(cycle_id: int, report_id: int):
    """Reset sample selection phase to start state"""
    async with AsyncSessionLocal() as db:
        try:
            print(f"Resetting sample selection for cycle {cycle_id}, report {report_id}...")
            
            # 1. Delete all individual samples and related data
            # Delete feedback first (foreign key constraint)
            feedback_result = await db.execute(
                delete(SampleFeedback)
                .where(
                    SampleFeedback.sample_id.in_(
                        select(IndividualSample.id)
                        .where(
                            and_(
                                IndividualSample.cycle_id == cycle_id,
                                IndividualSample.report_id == report_id
                            )
                        )
                    )
                )
            )
            print(f"Deleted {feedback_result.rowcount} feedback records")
            
            # Delete audit logs for samples
            audit_result = await db.execute(
                delete(SampleAuditLog)
                .where(
                    SampleAuditLog.sample_id.in_(
                        select(IndividualSample.id)
                        .where(
                            and_(
                                IndividualSample.cycle_id == cycle_id,
                                IndividualSample.report_id == report_id
                            )
                        )
                    )
                )
            )
            print(f"Deleted {audit_result.rowcount} sample audit log records")
            
            # Delete audit logs for submissions
            submission_audit_result = await db.execute(
                delete(SampleAuditLog)
                .where(
                    SampleAuditLog.submission_id.in_(
                        select(SampleSubmission.id)
                        .where(
                            and_(
                                SampleSubmission.cycle_id == cycle_id,
                                SampleSubmission.report_id == report_id
                            )
                        )
                    )
                )
            )
            print(f"Deleted {submission_audit_result.rowcount} submission audit log records")
            
            # First, clear submission_id references in individual_samples
            await db.execute(
                select(IndividualSample)
                .where(
                    and_(
                        IndividualSample.cycle_id == cycle_id,
                        IndividualSample.report_id == report_id
                    )
                )
                .execution_options(synchronize_session="fetch")
            )
            
            # UPDATE cycle_report_sample_selection_samples to remove submission references
            update_result = await db.execute(
                select(IndividualSample)
                .where(
                    and_(
                        IndividualSample.cycle_id == cycle_id,
                        IndividualSample.report_id == report_id
                    )
                )
            )
            samples = update_result.scalars().all()
            for sample in samples:
                sample.submission_id = None
                sample.is_submitted = False
            await db.flush()
            
            # Delete submission items first
            submission_items_result = await db.execute(
                delete(SampleSubmissionItem)
                .where(
                    SampleSubmissionItem.submission_id.in_(
                        select(SampleSubmission.id)
                        .where(
                            and_(
                                SampleSubmission.cycle_id == cycle_id,
                                SampleSubmission.report_id == report_id
                            )
                        )
                    )
                )
            )
            print(f"Deleted {submission_items_result.rowcount} submission item records")
            
            # Now delete submissions
            submission_result = await db.execute(
                delete(SampleSubmission)
                .where(
                    and_(
                        SampleSubmission.cycle_id == cycle_id,
                        SampleSubmission.report_id == report_id
                    )
                )
            )
            print(f"Deleted {submission_result.rowcount} submission records")
            
            # Delete samples
            sample_result = await db.execute(
                delete(IndividualSample)
                .where(
                    and_(
                        IndividualSample.cycle_id == cycle_id,
                        IndividualSample.report_id == report_id
                    )
                )
            )
            print(f"Deleted {sample_result.rowcount} sample records")
            
            # 2. Reset workflow phase status
            workflow_phase = await db.execute(
                select(WorkflowPhase)
                .where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == "Sample Selection"
                    )
                )
            )
            phase = workflow_phase.scalar_one_or_none()
            
            if phase:
                phase.phase_state = "Not Started"
                phase.phase_status = "Pending"
                phase.completion_percentage = 0
                phase.started_at = None
                phase.completed_at = None
                phase.completed_by = None
                print("Reset workflow phase to 'Not Started'")
            else:
                print("Warning: Workflow phase record not found")
            
            # 3. Update cycle report status if needed
            cycle_report = await db.execute(
                select(CycleReport)
                .where(
                    and_(
                        CycleReport.cycle_id == cycle_id,
                        CycleReport.report_id == report_id
                    )
                )
            )
            cr = cycle_report.scalar_one_or_none()
            if cr:
                print(f"Cycle report status: {cr.status}")
            
            # Commit all changes
            await db.commit()
            print("✅ Sample selection phase has been reset successfully!")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error resetting sample selection: {str(e)}")
            raise

async def main():
    """Main function"""
    if len(sys.argv) != 3:
        print("Usage: python reset_sample_selection.py <cycle_id> <report_id>")
        print("Example: python reset_sample_selection.py 13 156")
        sys.exit(1)
    
    try:
        cycle_id = int(sys.argv[1])
        report_id = int(sys.argv[2])
    except ValueError:
        print("Error: cycle_id and report_id must be integers")
        sys.exit(1)
    
    await reset_sample_selection(cycle_id, report_id)

if __name__ == "__main__":
    asyncio.run(main())