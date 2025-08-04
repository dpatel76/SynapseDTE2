#!/usr/bin/env python3
"""
Reset Data Provider ID phase by:
1. Deleting all universal assignments for this phase
2. Deleting all data owner LOB mappings
3. Resetting the phase state
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal


async def reset_data_owner_phase(cycle_id: int, report_id: int):
    async with AsyncSessionLocal() as db:
        try:
            # Get the Data Provider ID phase
            phase_result = await db.execute(
                text("""
                    SELECT phase_id, state 
                    FROM workflow_phases 
                    WHERE cycle_id = :cycle_id 
                    AND report_id = :report_id 
                    AND phase_name = 'Data Provider ID'
                """),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            phase = phase_result.first()
            
            if not phase:
                print(f"Data Provider ID phase not found for cycle {cycle_id}, report {report_id}")
                return
            
            phase_id = phase.phase_id
            print(f"Found Data Provider ID phase: {phase_id}, current state: {phase.state}")
            
            # 1. Delete universal assignments for this phase
            print("\n1. Deleting universal assignments...")
            delete_assignments = await db.execute(
                text("""
                    DELETE FROM universal_assignments 
                    WHERE context_data->>'cycle_id' = :cycle_id
                    AND context_data->>'report_id' = :report_id
                    AND context_data->>'phase_name' = 'Data Provider ID'
                    RETURNING assignment_id
                """),
                {"cycle_id": str(cycle_id), "report_id": str(report_id)}
            )
            deleted_assignments = delete_assignments.all()
            print(f"   Deleted {len(deleted_assignments)} universal assignments")
            
            # 2. Delete data owner LOB mappings
            print("\n2. Deleting data owner LOB mappings...")
            # First get all version IDs for this phase
            versions_result = await db.execute(
                text("""
                    SELECT version_id 
                    FROM cycle_report_data_owner_lob_attribute_versions 
                    WHERE phase_id = :phase_id
                """),
                {"phase_id": phase_id}
            )
            version_ids = [row.version_id for row in versions_result.all()]
            
            if version_ids:
                # Delete mappings (cascade should handle this, but let's be explicit)
                delete_mappings = await db.execute(
                    text("""
                        DELETE FROM cycle_report_data_owner_lob_mapping 
                        WHERE version_id = ANY(:version_ids)
                        RETURNING mapping_id
                    """),
                    {"version_ids": version_ids}
                )
                deleted_mappings = delete_mappings.all()
                print(f"   Deleted {len(deleted_mappings)} data owner LOB mappings")
                
                # Delete versions
                delete_versions = await db.execute(
                    text("""
                        DELETE FROM cycle_report_data_owner_lob_attribute_versions 
                        WHERE phase_id = :phase_id
                        RETURNING version_id
                    """),
                    {"phase_id": phase_id}
                )
                deleted_versions = delete_versions.all()
                print(f"   Deleted {len(deleted_versions)} data owner LOB versions")
            
            # 3. Delete any phase audit logs
            print("\n3. Deleting phase audit logs...")
            delete_audit = await db.execute(
                text("""
                    DELETE FROM data_owner_phase_audit_logs 
                    WHERE cycle_id = :cycle_id 
                    AND report_id = :report_id
                    RETURNING id
                """),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            deleted_audit = delete_audit.all()
            print(f"   Deleted {len(deleted_audit)} audit log entries")
            
            # 4. Reset the phase state
            print("\n4. Resetting phase state...")
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
                    WHERE phase_id = :phase_id
                """),
                {"phase_id": phase_id}
            )
            
            # 5. Reset workflow activities for this phase
            print("\n5. Resetting workflow activities...")
            await db.execute(
                text("""
                    UPDATE workflow_activities 
                    SET status = 'pending',
                        state = 'idle',
                        started_at = NULL,
                        completed_at = NULL,
                        completed_by = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE phase_id = :phase_id
                """),
                {"phase_id": phase_id}
            )
            
            await db.commit()
            print("\n✅ Data Provider ID phase has been successfully reset!")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error resetting phase: {str(e)}")
            raise


async def main():
    # Cycle 58, Report 156
    cycle_id = 58
    report_id = 156
    
    print(f"Resetting Data Provider ID phase for Cycle {cycle_id}, Report {report_id}")
    print("This will:")
    print("- Delete all universal assignments for this phase")
    print("- Delete all data owner LOB mappings")
    print("- Reset the phase to 'Not Started' state")
    print("\nProceeding with reset...")
    
    await reset_data_owner_phase(cycle_id, report_id)


if __name__ == "__main__":
    asyncio.run(main())