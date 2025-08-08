#!/usr/bin/env python
"""
Fix START activities that are stuck in IN_PROGRESS state
"""

import asyncio
import logging
from sqlalchemy import select, and_, text
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_start_activities():
    """Fix START activities that are stuck in IN_PROGRESS"""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # Fix all START activities that are IN_PROGRESS - they should be COMPLETED
            result = await db.execute(text("""
                UPDATE workflow_activities
                SET status = 'COMPLETED',
                    completed_at = COALESCE(completed_at, started_at, NOW()),
                    completed_by = COALESCE(completed_by, started_by, 1),
                    can_complete = false
                WHERE activity_type = 'START' 
                AND status = 'IN_PROGRESS'
                RETURNING phase_name, activity_name
            """))
            
            updated = result.fetchall()
            
            if updated:
                logger.info(f"Fixed {len(updated)} START activities:")
                for phase_name, activity_name in updated:
                    logger.info(f"  - {phase_name}: {activity_name}")
                    
                    # Also enable the next activity
                    await db.execute(text("""
                        UPDATE workflow_activities
                        SET can_start = true
                        WHERE phase_name = :phase_name
                        AND activity_order = 2
                    """), {"phase_name": phase_name})
            else:
                logger.info("No START activities needed fixing")
            
            # Also update the workflow phases for these
            await db.execute(text("""
                UPDATE workflow_phases wp
                SET status = 'In Progress',
                    state = 'In Progress',
                    actual_start_date = COALESCE(actual_start_date, NOW())
                FROM workflow_activities wa
                WHERE wa.phase_id = wp.phase_id
                AND wa.activity_type = 'START'
                AND wa.status = 'COMPLETED'
                AND wp.status = 'Not Started'
            """))
            
            await db.commit()
            logger.info("✅ All START activities fixed")
            
        except Exception as e:
            logger.error(f"❌ Error fixing START activities: {str(e)}")
            await db.rollback()


async def main():
    await fix_start_activities()


if __name__ == "__main__":
    asyncio.run(main())