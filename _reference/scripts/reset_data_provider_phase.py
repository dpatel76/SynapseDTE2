#!/usr/bin/env python3
"""
Reset Data Provider ID phase by removing duplicate assignments and resetting the phase
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, delete, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.workflow import WorkflowPhase
from app.models.data_owner_lob_assignment import (
    DataOwnerLOBAttributeMapping,
    DataOwnerLOBAttributeVersion
)
from app.models.testing import DataOwnerAssignment
from app.models.activity_definition import ActivityState, ActivityDefinition

async def reset_data_provider_phase(cycle_id: int, report_id: int):
    """Reset Data Provider ID phase and remove all assignments"""
    async with AsyncSessionLocal() as db:
        print(f"Resetting Data Provider ID phase for cycle {cycle_id}, report {report_id}")
        
        # 1. Get the Data Provider ID phase
        phase_result = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == 'Data Provider ID'
                )
            )
        )
        phase = phase_result.scalar_one_or_none()
        
        if not phase:
            print("Data Provider ID phase not found!")
            return
        
        print(f"Found phase with ID: {phase.phase_id}")
        
        # 2. Delete all DataOwnerLOBAttributeMappings for this phase
        assignments_result = await db.execute(
            select(DataOwnerLOBAttributeMapping).where(
                DataOwnerLOBAttributeMapping.phase_id == phase.phase_id
            )
        )
        assignments = assignments_result.scalars().all()
        print(f"Found {len(assignments)} DataOwnerLOBAttributeMappings to delete")
        
        if assignments:
            await db.execute(
                delete(DataOwnerLOBAttributeMapping).where(
                    DataOwnerLOBAttributeMapping.phase_id == phase.phase_id
                )
            )
            print(f"Deleted {len(assignments)} DataOwnerLOBAttributeMappings")
        
        # 3. Delete all DataOwnerLOBAttributeVersions for this phase
        versions_result = await db.execute(
            select(DataOwnerLOBAttributeVersion).where(
                DataOwnerLOBAttributeVersion.phase_id == phase.phase_id
            )
        )
        versions = versions_result.scalars().all()
        print(f"Found {len(versions)} DataOwnerLOBAttributeVersions to delete")
        
        if versions:
            await db.execute(
                delete(DataOwnerLOBAttributeVersion).where(
                    DataOwnerLOBAttributeVersion.phase_id == phase.phase_id
                )
            )
            print(f"Deleted {len(versions)} DataOwnerLOBAttributeVersions")
        
        # 4. Skip old DataOwnerAssignments - table doesn't exist anymore
        print("Skipping old DataOwnerAssignments table (deprecated)")
        
        # 5. Reset all activity states for this phase
        # Get all activity definitions for Data Provider ID phase
        activities_result = await db.execute(
            select(ActivityDefinition).where(
                ActivityDefinition.phase_name == 'Data Provider ID'
            )
        )
        activities = activities_result.scalars().all()
        
        for activity in activities:
            # Delete existing activity states
            await db.execute(
                delete(ActivityState).where(
                    and_(
                        ActivityState.cycle_id == cycle_id,
                        ActivityState.report_id == report_id,
                        ActivityState.activity_definition_id == activity.id
                    )
                )
            )
        print(f"Reset activity states for {len(activities)} activities")
        
        # 6. Reset the phase itself
        phase.state = 'Not Started'
        phase.status = 'Not Started'
        phase.actual_start_date = None
        phase.actual_end_date = None
        phase.started_by = None
        phase.completed_by = None
        phase.notes = 'Phase reset for fresh start'
        phase.phase_data = {}
        
        # Commit all changes
        await db.commit()
        print("Phase reset complete!")
        
        # 7. Verify the reset
        print("\nVerification:")
        
        # Check assignments
        check_assignments = await db.execute(
            select(DataOwnerLOBAttributeMapping).where(
                DataOwnerLOBAttributeMapping.phase_id == phase.phase_id
            )
        )
        remaining_assignments = check_assignments.scalars().all()
        print(f"Remaining DataOwnerLOBAttributeMappings: {len(remaining_assignments)}")
        
        # Check versions
        check_versions = await db.execute(
            select(DataOwnerLOBAttributeVersion).where(
                DataOwnerLOBAttributeVersion.phase_id == phase.phase_id
            )
        )
        remaining_versions = check_versions.scalars().all()
        print(f"Remaining DataOwnerLOBAttributeVersions: {len(remaining_versions)}")
        
        # Check phase status
        print(f"Phase state: {phase.state}")
        print(f"Phase status: {phase.status}")
        
        return True

async def main():
    """Main function"""
    if len(sys.argv) != 3:
        print("Usage: python reset_data_provider_phase.py <cycle_id> <report_id>")
        sys.exit(1)
    
    try:
        cycle_id = int(sys.argv[1])
        report_id = int(sys.argv[2])
    except ValueError:
        print("Error: cycle_id and report_id must be integers")
        sys.exit(1)
    
    success = await reset_data_provider_phase(cycle_id, report_id)
    
    if success:
        print(f"\n✓ Successfully reset Data Provider ID phase for cycle {cycle_id}, report {report_id}")
        print("You can now start the phase fresh from the UI")
    else:
        print("\n✗ Failed to reset phase")

if __name__ == "__main__":
    asyncio.run(main())