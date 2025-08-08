#!/usr/bin/env python3
"""
Monitor assignment creation to identify when duplicates are created
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def monitor_assignments(cycle_id: int, report_id: int):
    """Monitor for new assignments being created"""
    print(f"\n=== Monitoring Assignments for Cycle {cycle_id}, Report {report_id} ===")
    print(f"Started monitoring at: {datetime.now()}\n")
    
    last_count = 0
    check_number = 0
    
    while True:
        async with AsyncSessionLocal() as db:
            # Count current assignments
            result = await db.execute(
                text("""
                    SELECT COUNT(*) as total
                    FROM cycle_report_data_owner_lob_attribute_assignments a
                    JOIN workflow_phases p ON a.phase_id = p.phase_id
                    WHERE p.cycle_id = :cycle_id 
                    AND p.report_id = :report_id
                    AND p.phase_name = 'Data Provider ID'
                """),
                {"cycle_id": cycle_id, "report_id": report_id}
            )
            
            current_count = result.scalar()
            
            if current_count != last_count:
                print(f"[{datetime.now()}] Assignment count changed: {last_count} -> {current_count}")
                
                # Get details of new assignments
                if current_count > last_count:
                    new_assignments = await db.execute(
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
                            ORDER BY a.created_at DESC
                            LIMIT :limit
                        """),
                        {"cycle_id": cycle_id, "report_id": report_id, "limit": current_count - last_count}
                    )
                    
                    print("\nNew assignments created:")
                    for assignment in new_assignments:
                        print(f"  - ID: {assignment.assignment_id}")
                        print(f"    Attribute: {assignment.attribute_name} (ID: {assignment.attribute_id})")
                        print(f"    LOB: {assignment.lob_name} (ID: {assignment.lob_id})")
                        print(f"    Version: {assignment.version_id}")
                        print(f"    Created by: {assignment.created_by_email} at {assignment.created_at}")
                
                # Check for duplicates
                duplicate_check = await db.execute(
                    text("""
                        SELECT 
                            attribute_id, 
                            lob_id, 
                            COUNT(*) as count
                        FROM cycle_report_data_owner_lob_attribute_assignments a
                        JOIN workflow_phases p ON a.phase_id = p.phase_id
                        WHERE p.cycle_id = :cycle_id 
                        AND p.report_id = :report_id
                        AND p.phase_name = 'Data Provider ID'
                        GROUP BY attribute_id, lob_id
                        HAVING COUNT(*) > 1
                    """),
                    {"cycle_id": cycle_id, "report_id": report_id}
                )
                
                duplicates = duplicate_check.all()
                if duplicates:
                    print("\n⚠️ DUPLICATES DETECTED:")
                    for dup in duplicates:
                        print(f"  - Attribute {dup.attribute_id} + LOB {dup.lob_id}: {dup.count} assignments")
                
                last_count = current_count
            
            check_number += 1
            if check_number % 10 == 0:
                print(f"[{datetime.now()}] Still monitoring... (check #{check_number}, current count: {current_count})")
        
        # Sleep for 2 seconds before next check
        await asyncio.sleep(2)

async def main():
    if len(sys.argv) != 3:
        print("Usage: python monitor_assignment_creation.py <cycle_id> <report_id>")
        sys.exit(1)
    
    cycle_id = int(sys.argv[1])
    report_id = int(sys.argv[2])
    
    print("Press Ctrl+C to stop monitoring")
    
    try:
        await monitor_assignments(cycle_id, report_id)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    asyncio.run(main())