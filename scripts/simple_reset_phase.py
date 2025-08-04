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
            
            # 1. Delete universal assignments
            print("\n1. Deleting universal assignments...")
            delete_assignments = await db.execute(
                text("""
                    DELETE FROM universal_assignments 
                    WHERE context_data->>'cycle_id' = :cycle_id
                    AND context_data->>'report_id' = :report_id
                    AND (context_data->>'phase_name' = 'Data Provider ID' 
                         OR assignment_type = 'Data Owner Assignment Request')
                    RETURNING assignment_id
                """),
                {"cycle_id": str(cycle_id), "report_id": str(report_id)}
            )
            deleted = delete_assignments.all()
            print(f"   Deleted {len(deleted)} universal assignments")
            
            # 2. Delete any existing mappings (if table exists)
            try:
                # Check if table exists
                table_check = await db.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'cycle_report_data_owner_lob_mapping'
                        )
                    """)
                )
                table_exists = table_check.scalar()
                
                if table_exists:
                    print("\n2. Deleting data owner LOB mappings...")
                    delete_mappings = await db.execute(
                        text("""
                            DELETE FROM cycle_report_data_owner_lob_mapping 
                            WHERE phase_id = (
                                SELECT phase_id FROM workflow_phases 
                                WHERE cycle_id = :cycle_id 
                                AND report_id = :report_id 
                                AND phase_name = 'Data Provider ID'
                            )
                            RETURNING mapping_id
                        """),
                        {"cycle_id": cycle_id, "report_id": report_id}
                    )
                    deleted_mappings = delete_mappings.all()
                    print(f"   Deleted {len(deleted_mappings)} mappings")
            except Exception as e:
                print(f"   Note: Could not delete mappings - {str(e)}")
            
            # 3. Reset the phase
            print("\n3. Resetting phase state...")
            await db.execute(
                text("""
                    UPDATE workflow_phases 
                    SET state = 'Not Started',
                        status = 'pending',
                        progress_percentage = 0,
                        actual_start_date = NULL,
                        actual_end_date = NULL,
                        started_by = NULL,
                        completed_by = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE cycle_id = :cycle_id
                    AND report_id = :report_id
                    AND phase_name = 'Data Provider ID'
                """),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            
            # 4. Reset workflow activities
            print("\n4. Resetting workflow activities...")
            await db.execute(
                text("""
                    UPDATE workflow_activities 
                    SET status = 'pending',
                        state = 'idle',
                        started_at = NULL,
                        completed_at = NULL,
                        completed_by = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE phase_id = (
                        SELECT phase_id FROM workflow_phases 
                        WHERE cycle_id = :cycle_id 
                        AND report_id = :report_id 
                        AND phase_name = 'Data Provider ID'
                    )
                """),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            
            await db.commit()
            print("\n✅ Data Provider ID phase has been successfully reset!")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(reset_phase())