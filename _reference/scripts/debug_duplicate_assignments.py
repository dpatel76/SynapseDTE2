#!/usr/bin/env python3
"""
Debug duplicate assignment issue
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, and_, func
from app.core.database import AsyncSessionLocal
from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping, DataOwnerLOBAttributeVersion
from app.models.workflow import WorkflowPhase

async def debug_assignments(cycle_id: int, report_id: int):
    """Debug duplicate assignments"""
    async with AsyncSessionLocal() as db:
        # Get phase
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
            print("Phase not found")
            return
            
        print(f"Phase ID: {phase.phase_id}")
        
        # Check for duplicate assignments
        duplicate_query = await db.execute(
            select(
                DataOwnerLOBAttributeMapping.attribute_id,
                DataOwnerLOBAttributeMapping.lob_id,
                func.count(DataOwnerLOBAttributeMapping.assignment_id).label('count')
            )
            .where(DataOwnerLOBAttributeMapping.phase_id == phase.phase_id)
            .group_by(
                DataOwnerLOBAttributeMapping.attribute_id,
                DataOwnerLOBAttributeMapping.lob_id
            )
            .having(func.count(DataOwnerLOBAttributeMapping.assignment_id) > 1)
        )
        
        duplicates = duplicate_query.all()
        
        if duplicates:
            print(f"\nFound {len(duplicates)} duplicate attribute-LOB combinations:")
            for dup in duplicates:
                print(f"  Attribute: {dup.attribute_id}, LOB: {dup.lob_id}, Count: {dup.count}")
                
                # Get details of duplicates
                details = await db.execute(
                    select(DataOwnerLOBAttributeMapping)
                    .where(and_(
                        DataOwnerLOBAttributeMapping.phase_id == phase.phase_id,
                        DataOwnerLOBAttributeMapping.attribute_id == dup.attribute_id,
                        DataOwnerLOBAttributeMapping.lob_id == dup.lob_id
                    ))
                )
                for assignment in details.scalars():
                    print(f"    Assignment ID: {assignment.assignment_id}")
                    print(f"    Version ID: {assignment.version_id}")
                    print(f"    Sample ID: {assignment.sample_id}")
                    print(f"    Created at: {assignment.created_at}")
                    print(f"    Created by: {assignment.created_by_id}")
                    print()
        else:
            print("\nNo duplicate assignments found")
            
        # Show all assignments
        all_assignments = await db.execute(
            select(DataOwnerLOBAttributeMapping)
            .where(DataOwnerLOBAttributeMapping.phase_id == phase.phase_id)
            .order_by(
                DataOwnerLOBAttributeMapping.attribute_id,
                DataOwnerLOBAttributeMapping.lob_id
            )
        )
        
        assignments = all_assignments.scalars().all()
        print(f"\nTotal assignments: {len(assignments)}")
        
        # Group by attribute
        attr_groups = {}
        for assignment in assignments:
            if assignment.attribute_id not in attr_groups:
                attr_groups[assignment.attribute_id] = []
            attr_groups[assignment.attribute_id].append(assignment)
            
        print(f"\nAssignments by attribute:")
        for attr_id, assigns in attr_groups.items():
            print(f"  Attribute {attr_id}: {len(assigns)} assignment(s)")
            for assign in assigns:
                print(f"    LOB: {assign.lob_id}, Sample: {assign.sample_id}")

async def main():
    if len(sys.argv) != 3:
        print("Usage: python debug_duplicate_assignments.py <cycle_id> <report_id>")
        sys.exit(1)
    
    cycle_id = int(sys.argv[1])
    report_id = int(sys.argv[2])
    
    await debug_assignments(cycle_id, report_id)

if __name__ == "__main__":
    asyncio.run(main())