#!/usr/bin/env python3
"""
Simple reset of Data Provider ID phase
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal


async def reset_phase():
    async with AsyncSessionLocal() as db:
        try:
            cycle_id = 58
            report_id = 156
            
            print(f"Resetting Data Provider ID phase for Cycle {cycle_id}, Report {report_id}")
            
            # Just reset the phase state
            print("\n1. Resetting phase state...")
            result = await db.execute(
                text("""
                    UPDATE workflow_phases 
                    SET state = 'Not Started',
                        status = 'Not Started',
                        progress_percentage = 0,
                        actual_start_date = NULL,
                        actual_end_date = NULL,
                        started_by = NULL,
                        completed_by = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE cycle_id = :cycle_id
                    AND report_id = :report_id
                    AND phase_name = 'Data Provider ID'
                    RETURNING phase_id, phase_name
                """),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            
            phase = result.first()
            if phase:
                print(f"   ✓ Reset phase {phase.phase_name} (ID: {phase.phase_id})")
                
                # Reset workflow activities
                print("\n2. Resetting workflow activities...")
                activity_result = await db.execute(
                    text("""
                        UPDATE workflow_activities 
                        SET status = 'NOT_STARTED',
                            started_at = NULL,
                            completed_at = NULL,
                            completed_by = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE phase_id = :phase_id
                        RETURNING activity_name
                    """),
                    {"phase_id": phase.phase_id}
                )
                
                activities = activity_result.all()
                for activity in activities:
                    print(f"   ✓ Reset activity: {activity.activity_name}")
            else:
                print("   ❌ Phase not found!")
                return
            
            await db.commit()
            print("\n✅ Data Provider ID phase has been successfully reset!")
            print("\nYou can now start the phase again from the UI.")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(reset_phase())