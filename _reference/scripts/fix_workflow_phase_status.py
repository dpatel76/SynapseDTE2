#!/usr/bin/env python
"""
Fix inconsistent workflow phase status/state/progress values
"""

import asyncio
import logging
from sqlalchemy import update, select, and_, or_
from app.core.database import AsyncSessionLocal
from app.models.workflow import WorkflowPhase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_workflow_phase_status():
    """Fix inconsistent workflow phase status, state, and progress values"""
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Fix phases with status='Not Started' but state='Complete'
            result = await db.execute(
                update(WorkflowPhase)
                .where(
                    and_(
                        WorkflowPhase.status == 'Not Started',
                        WorkflowPhase.state == 'Complete'
                    )
                )
                .values(
                    state='Not Started',
                    progress_percentage=0
                )
            )
            not_started_fixed = result.rowcount
            logger.info(f"Fixed {not_started_fixed} phases with status='Not Started' but state='Complete'")
            
            # 2. Fix phases with progress=100 but status not 'Complete'
            result = await db.execute(
                update(WorkflowPhase)
                .where(
                    and_(
                        WorkflowPhase.progress_percentage == 100,
                        WorkflowPhase.status != 'Complete'
                    )
                )
                .values(
                    status='Complete',
                    state='Complete'
                )
            )
            complete_fixed = result.rowcount
            logger.info(f"Fixed {complete_fixed} phases with progress=100 but status!='Complete'")
            
            # 3. Fix phases with progress=0 but status not 'Not Started'
            result = await db.execute(
                update(WorkflowPhase)
                .where(
                    and_(
                        WorkflowPhase.progress_percentage == 0,
                        WorkflowPhase.status.in_(['Complete', 'In Progress'])
                    )
                )
                .values(
                    status='Not Started',
                    state='Not Started'
                )
            )
            zero_progress_fixed = result.rowcount
            logger.info(f"Fixed {zero_progress_fixed} phases with progress=0 but status!='Not Started'")
            
            # 4. Fix phases with intermediate progress but wrong state
            result = await db.execute(
                update(WorkflowPhase)
                .where(
                    and_(
                        WorkflowPhase.progress_percentage > 0,
                        WorkflowPhase.progress_percentage < 100,
                        WorkflowPhase.state.in_(['Not Started', 'Complete'])
                    )
                )
                .values(
                    state='In Progress',
                    status='In Progress'
                )
            )
            in_progress_fixed = result.rowcount
            logger.info(f"Fixed {in_progress_fixed} phases with intermediate progress but wrong state")
            
            # Commit all changes
            await db.commit()
            
            # Report summary
            total_fixed = not_started_fixed + complete_fixed + zero_progress_fixed + in_progress_fixed
            logger.info(f"✅ Total workflow phases fixed: {total_fixed}")
            
            # Verify no inconsistencies remain
            result = await db.execute(
                select(WorkflowPhase).where(
                    or_(
                        and_(WorkflowPhase.status == 'Not Started', WorkflowPhase.progress_percentage > 0),
                        and_(WorkflowPhase.status == 'Complete', WorkflowPhase.progress_percentage < 100),
                        and_(WorkflowPhase.progress_percentage == 100, WorkflowPhase.status != 'Complete'),
                        and_(WorkflowPhase.progress_percentage == 0, WorkflowPhase.status == 'Complete')
                    )
                )
            )
            remaining_issues = len(result.scalars().all())
            
            if remaining_issues > 0:
                logger.warning(f"⚠️ {remaining_issues} phases still have inconsistencies")
            else:
                logger.info("✅ All workflow phase inconsistencies have been resolved")
                
        except Exception as e:
            logger.error(f"Error fixing workflow phase status: {str(e)}")
            await db.rollback()
            raise


async def verify_workflow_phases():
    """Verify workflow phase consistency after fixes"""
    
    async with AsyncSessionLocal() as db:
        # Get all phases
        result = await db.execute(select(WorkflowPhase))
        phases = result.scalars().all()
        
        issues = []
        for phase in phases:
            # Check for inconsistencies
            if phase.status == 'Not Started' and phase.progress_percentage > 0:
                issues.append(f"Phase {phase.phase_id}: status='Not Started' but progress={phase.progress_percentage}")
            elif phase.status == 'Complete' and phase.progress_percentage < 100:
                issues.append(f"Phase {phase.phase_id}: status='Complete' but progress={phase.progress_percentage}")
            elif phase.progress_percentage == 100 and phase.status != 'Complete':
                issues.append(f"Phase {phase.phase_id}: progress=100 but status='{phase.status}'")
            elif phase.progress_percentage == 0 and phase.status not in ['Not Started', 'Pending']:
                issues.append(f"Phase {phase.phase_id}: progress=0 but status='{phase.status}'")
        
        if issues:
            logger.warning("Found inconsistencies:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("✅ All workflow phases are consistent")
        
        return len(issues) == 0


async def main():
    """Main function to run both fix and verification"""
    logger.info("Starting workflow phase status fix...")
    
    # Fix inconsistencies
    await fix_workflow_phase_status()
    
    # Verify fixes
    logger.info("\nVerifying workflow phases...")
    is_consistent = await verify_workflow_phases()
    
    if is_consistent:
        logger.info("\n✅ Workflow phase status fix completed successfully")
    else:
        logger.warning("\n⚠️ Some inconsistencies remain. Please review manually.")
    
    return is_consistent

if __name__ == "__main__":
    asyncio.run(main())