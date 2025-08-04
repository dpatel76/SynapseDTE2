#!/usr/bin/env python3
"""
Simple debug for duplicate assignments
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def debug_duplicates(cycle_id: int, report_id: int):
    """Debug duplicate assignments"""
    async with AsyncSessionLocal() as db:
        print(f"\n=== Checking Assignments for Cycle {cycle_id}, Report {report_id} ===\n")
        
        # Get all assignments with details
        result = await db.execute(
            text("""
                SELECT 
                    a.assignment_id,
                    a.attribute_id,
                    pa.attribute_name,
                    a.lob_id,
                    l.lob_name,
                    a.version_id,
                    a.created_at,
                    a.created_by_id,
                    u.email as created_by_email
                FROM cycle_report_data_owner_lob_attribute_assignments a
                JOIN workflow_phases p ON a.phase_id = p.phase_id
                JOIN cycle_report_planning_attributes pa ON a.attribute_id = pa.id
                JOIN lobs l ON a.lob_id = l.lob_id
                LEFT JOIN users u ON a.created_by_id = u.user_id
                WHERE p.cycle_id = :cycle_id 
                AND p.report_id = :report_id
                AND p.phase_name = 'Data Provider ID'
                ORDER BY a.attribute_id, a.lob_id, a.created_at
            """),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        
        assignments = result.all()
        print(f"Total assignments: {len(assignments)}")
        
        # Check for duplicates
        seen = {}
        duplicates = []
        
        for assignment in assignments:
            key = (assignment.attribute_id, assignment.lob_id)
            if key in seen:
                duplicates.append({
                    'first': seen[key],
                    'duplicate': assignment
                })
            else:
                seen[key] = assignment
                
        if duplicates:
            print(f"\n❌ Found {len(duplicates)} duplicate assignments:\n")
            for i, dup in enumerate(duplicates, 1):
                first = dup['first']
                duplicate = dup['duplicate']
                print(f"{i}. Duplicate for '{first.attribute_name}' (ID: {first.attribute_id}) + LOB '{first.lob_name}':")
                print(f"   First assignment:")
                print(f"     - Assignment ID: {first.assignment_id}")
                print(f"     - Version: {first.version_id}")
                print(f"     - Created: {first.created_at}")
                print(f"     - Created by: {first.created_by_email} (ID: {first.created_by_id})")
                print(f"   Duplicate:")
                print(f"     - Assignment ID: {duplicate.assignment_id}")
                print(f"     - Version: {duplicate.version_id}")
                print(f"     - Created: {duplicate.created_at}")
                print(f"     - Created by: {duplicate.created_by_email} (ID: {duplicate.created_by_id})")
                time_diff = (duplicate.created_at - first.created_at).total_seconds()
                print(f"   Time difference: {time_diff} seconds")
                print()
        else:
            print("\n✓ No duplicates found")
            
        # Check versions
        print("\n=== Checking Versions ===")
        version_result = await db.execute(
            text("""
                SELECT 
                    v.version_id,
                    v.version_number,
                    v.version_status,
                    v.created_at,
                    COUNT(a.assignment_id) as assignment_count
                FROM cycle_report_data_owner_lob_attribute_versions v
                JOIN workflow_phases p ON v.phase_id = p.phase_id
                LEFT JOIN cycle_report_data_owner_lob_attribute_assignments a ON v.version_id = a.version_id
                WHERE p.cycle_id = :cycle_id 
                AND p.report_id = :report_id
                AND p.phase_name = 'Data Provider ID'
                GROUP BY v.version_id, v.version_number, v.version_status, v.created_at
                ORDER BY v.created_at
            """),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        
        versions = version_result.all()
        print(f"\nTotal versions: {len(versions)}")
        for version in versions:
            print(f"\nVersion {version.version_id}:")
            print(f"  - Number: {version.version_number}")
            print(f"  - Status: {version.version_status}")
            print(f"  - Created: {version.created_at}")
            print(f"  - Assignments: {version.assignment_count}")

async def main():
    if len(sys.argv) != 3:
        print("Usage: python debug_duplicates_simple.py <cycle_id> <report_id>")
        sys.exit(1)
    
    cycle_id = int(sys.argv[1])
    report_id = int(sys.argv[2])
    
    await debug_duplicates(cycle_id, report_id)

if __name__ == "__main__":
    asyncio.run(main())