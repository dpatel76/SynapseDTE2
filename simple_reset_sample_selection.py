#!/usr/bin/env python3
"""
Simple reset of Sample Selection phase
- Removes all samples from version tables
- Removes all versions
- Clears phase data
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.models.workflow import WorkflowPhase
from sqlalchemy import select, and_, text
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reset_sample_selection_phase(cycle_id: int = 55, report_id: int = 156):
    """Reset sample selection phase - simple version"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get sample selection phase
            phase_result = await db.execute(
                select(WorkflowPhase).where(
                    and_(
                        WorkflowPhase.cycle_id == cycle_id,
                        WorkflowPhase.report_id == report_id,
                        WorkflowPhase.phase_name == "Sample Selection"
                    )
                )
            )
            phase = phase_result.scalar_one_or_none()
            
            if not phase:
                logger.error(f"Sample Selection phase not found for cycle {cycle_id}, report {report_id}")
                return
            
            logger.info(f"Found Sample Selection phase: {phase.phase_id}")
            
            # 1. Delete all samples from version tables
            samples_deleted = await db.execute(
                text('DELETE FROM cycle_report_sample_selection_samples WHERE phase_id = :phase_id'),
                {'phase_id': phase.phase_id}
            )
            logger.info(f"Deleted {samples_deleted.rowcount} samples from version tables")
            
            # 2. Delete all versions
            versions_deleted = await db.execute(
                text('DELETE FROM cycle_report_sample_selection_versions WHERE phase_id = :phase_id'),
                {'phase_id': phase.phase_id}
            )
            logger.info(f"Deleted {versions_deleted.rowcount} versions")
            
            # 3. Clear phase data
            phase.phase_data = {
                "cycle_report_sample_selection_samples": [],
                "versions": [],
                "submissions": [],
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # 4. Reset phase state
            phase.state = "Not Started"
            phase.actual_start_date = None
            phase.started_by = None
            phase.updated_at = datetime.utcnow()
            
            # 5. Cancel assignments using raw SQL
            # Cancel Sample context assignments
            await db.execute(
                text("""
                    UPDATE universal_assignments 
                    SET status = 'Cancelled', updated_at = CURRENT_TIMESTAMP
                    WHERE context_type = 'Sample'
                    AND (context_data->>'cycle_id')::int = :cycle_id
                    AND (context_data->>'report_id')::int = :report_id
                    AND status IN ('pending', 'in_progress', 'pending_approval')
                """),
                {'cycle_id': cycle_id, 'report_id': report_id}
            )
            
            # Cancel Report context assignments for Sample Selection
            await db.execute(
                text("""
                    UPDATE universal_assignments 
                    SET status = 'Cancelled', updated_at = CURRENT_TIMESTAMP
                    WHERE context_type = 'Report'
                    AND (context_data->>'cycle_id')::int = :cycle_id
                    AND (context_data->>'report_id')::int = :report_id
                    AND title LIKE '%Sample Selection%'
                    AND status IN ('pending', 'in_progress', 'pending_approval')
                """),
                {'cycle_id': cycle_id, 'report_id': report_id}
            )
            
            # Commit all changes
            await db.commit()
            
            logger.info("\n=== SAMPLE SELECTION PHASE RESET COMPLETE ===")
            logger.info(f"✓ Deleted all samples from version tables")
            logger.info(f"✓ Deleted all versions")
            logger.info(f"✓ Cleared phase data")
            logger.info(f"✓ Reset phase status to 'Not Started'")
            logger.info(f"✓ Cancelled all active assignments")
            logger.info("\nThe sample selection phase is now completely clean!")
            logger.info("You can now test from the UI with a fresh start.")
            
        except Exception as e:
            logger.error(f"Error during reset: {str(e)}", exc_info=True)
            await db.rollback()
            raise

if __name__ == "__main__":
    print("🔄 Resetting Sample Selection Phase (Simple Version)...")
    print("=" * 50)
    
    asyncio.run(reset_sample_selection_phase())