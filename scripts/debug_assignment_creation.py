#!/usr/bin/env python3
"""
Debug assignment creation to find where duplicates are coming from
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, and_, func, text
from app.core.database import AsyncSessionLocal
from app.models.data_owner_lob_assignment import DataOwnerLOBAttributeMapping, DataOwnerLOBAttributeVersion
from app.models.workflow import WorkflowPhase
from app.models.sample_selection import SampleSelectionSample, SampleSelectionVersion
from app.models.scoping import ScopingAttribute, ScopingVersion
# Skip PlanningAttribute import - will use direct queries

async def debug_assignment_creation(cycle_id: int, report_id: int):
    """Debug the entire assignment creation process"""
    async with AsyncSessionLocal() as db:
        print(f"\n=== Debugging Assignment Creation for Cycle {cycle_id}, Report {report_id} ===\n")
        
        # 1. Check Data Provider ID phase
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
            print("❌ Data Provider ID phase not found")
            return
            
        print(f"✓ Phase ID: {phase.phase_id}")
        print(f"  State: {phase.state}")
        print(f"  Status: {phase.status}")
        
        # 2. Check approved samples and LOBs
        sample_version_result = await db.execute(
            select(SampleSelectionVersion)
            .join(WorkflowPhase, SampleSelectionVersion.phase_id == WorkflowPhase.phase_id)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Sample Selection',
                SampleSelectionVersion.version_status == 'approved'
            ))
            .order_by(SampleSelectionVersion.version_number.desc())
        )
        sample_version = sample_version_result.scalar_one_or_none()
        
        if sample_version:
            # Get LOBs from approved samples
            lob_query = await db.execute(
                select(SampleSelectionSample.lob_id, func.count(SampleSelectionSample.sample_id))
                .where(and_(
                    SampleSelectionSample.version_id == sample_version.version_id,
                    SampleSelectionSample.report_owner_decision == 'approved'
                ))
                .group_by(SampleSelectionSample.lob_id)
            )
            lobs = lob_query.all()
            print(f"\n✓ Found {len(lobs)} LOBs from approved samples:")
            for lob_id, count in lobs:
                print(f"  - LOB {lob_id}: {count} samples")
        else:
            print("\n❌ No approved sample selection version found")
            
        # 3. Check scoped attributes
        scoping_version_result = await db.execute(
            select(ScopingVersion)
            .join(WorkflowPhase, ScopingVersion.phase_id == WorkflowPhase.phase_id)
            .where(and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == 'Scoping',
                ScopingVersion.version_status == 'approved'
            ))
            .order_by(ScopingVersion.version_number.desc())
        )
        scoping_version = scoping_version_result.scalar_one_or_none()
        
        if scoping_version:
            # Get non-PK scoped attributes
            attrs_query = await db.execute(
                text("""
                    SELECT DISTINCT sa.planning_attribute_id, pa.attribute_name
                    FROM cycle_report_scoping_attributes sa
                    JOIN cycle_report_planning_attributes pa ON sa.planning_attribute_id = pa.id
                    WHERE sa.version_id = :version_id
                    AND sa.tester_decision = 'accept'
                    AND pa.is_primary_key = false
                """),
                {"version_id": scoping_version.version_id}
            )
            attrs = attrs_query.all()
            print(f"\n✓ Found {len(attrs)} non-PK scoped attributes:")
            for attr_id, attr_name in attrs:
                print(f"  - {attr_id}: {attr_name}")
        else:
            print("\n❌ No approved scoping version found")
            
        # 4. Check existing assignments
        print(f"\n=== Checking Existing Assignments ===")
        
        # Get all assignments for this phase
        assignments_query = await db.execute(
            select(
                DataOwnerLOBAttributeMapping.assignment_id,
                DataOwnerLOBAttributeMapping.attribute_id,
                DataOwnerLOBAttributeMapping.lob_id,
                DataOwnerLOBAttributeMapping.version_id,
                DataOwnerLOBAttributeMapping.created_at,
                DataOwnerLOBAttributeMapping.created_by_id
            )
            .where(DataOwnerLOBAttributeMapping.phase_id == phase.phase_id)
            .order_by(
                DataOwnerLOBAttributeMapping.attribute_id,
                DataOwnerLOBAttributeMapping.lob_id,
                DataOwnerLOBAttributeMapping.created_at
            )
        )
        
        assignments = assignments_query.all()
        print(f"\nTotal assignments: {len(assignments)}")
        
        # Check for duplicates
        seen_combinations = {}
        duplicates = []
        
        for assignment in assignments:
            combo_key = (assignment.attribute_id, assignment.lob_id)
            if combo_key in seen_combinations:
                duplicates.append({
                    'first': seen_combinations[combo_key],
                    'duplicate': assignment
                })
            else:
                seen_combinations[combo_key] = assignment
                
        if duplicates:
            print(f"\n❌ Found {len(duplicates)} duplicate assignments:")
            for dup in duplicates:
                first = dup['first']
                duplicate = dup['duplicate']
                print(f"\n  Duplicate for Attribute {first.attribute_id}, LOB {first.lob_id}:")
                print(f"    First assignment:")
                print(f"      - ID: {first.assignment_id}")
                print(f"      - Version: {first.version_id}")
                print(f"      - Created: {first.created_at}")
                print(f"      - Created by: {first.created_by_id}")
                print(f"    Duplicate assignment:")
                print(f"      - ID: {duplicate.assignment_id}")
                print(f"      - Version: {duplicate.version_id}")
                print(f"      - Created: {duplicate.created_at}")
                print(f"      - Created by: {duplicate.created_by_id}")
                print(f"    Time difference: {(duplicate.created_at - first.created_at).total_seconds()} seconds")
        else:
            print("\n✓ No duplicates found")
            
        # 5. Check versions
        print(f"\n=== Checking Versions ===")
        versions_query = await db.execute(
            select(DataOwnerLOBAttributeVersion)
            .where(DataOwnerLOBAttributeVersion.phase_id == phase.phase_id)
            .order_by(DataOwnerLOBAttributeVersion.created_at)
        )
        
        versions = versions_query.scalars().all()
        print(f"\nTotal versions: {len(versions)}")
        
        for version in versions:
            print(f"\n  Version {version.version_id}:")
            print(f"    - Number: {version.version_number}")
            print(f"    - Status: {version.version_status}")
            print(f"    - Created: {version.created_at}")
            print(f"    - Executive: {version.data_executive_id}")
            
            # Count assignments for this version
            count_query = await db.execute(
                select(func.count(DataOwnerLOBAttributeMapping.assignment_id))
                .where(DataOwnerLOBAttributeMapping.version_id == version.version_id)
            )
            count = count_query.scalar()
            print(f"    - Assignments: {count}")
            
        # 6. Check for workflow orchestrator calls
        print(f"\n=== Checking Phase Data ===")
        print(f"Phase data: {phase.phase_data}")

async def main():
    if len(sys.argv) != 3:
        print("Usage: python debug_assignment_creation.py <cycle_id> <report_id>")
        sys.exit(1)
    
    cycle_id = int(sys.argv[1])
    report_id = int(sys.argv[2])
    
    await debug_assignment_creation(cycle_id, report_id)

if __name__ == "__main__":
    asyncio.run(main())