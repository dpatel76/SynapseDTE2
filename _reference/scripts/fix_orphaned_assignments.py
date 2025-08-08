#!/usr/bin/env python3
"""
Fix orphaned assignments using the DataProfilingAssignmentService.
This script finds any assignments that should have been completed but weren't.
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.services.universal_assignment_service import UniversalAssignmentService


async def fix_orphaned_assignments():
    """Find and fix orphaned assignments"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Find assignments that should be completed
            check_sql = """
            WITH orphaned_assignments AS (
                SELECT 
                    ua.assignment_id,
                    ua.context_data->>'version_id' as version_id,
                    ua.status as assignment_status,
                    ua.approval_notes
                FROM universal_assignments ua
                WHERE 
                    ua.assignment_type = 'Rule Approval'
                    AND ua.status IN ('Assigned', 'Acknowledged', 'In Progress')
            )
            SELECT 
                oa.assignment_id,
                oa.version_id,
                oa.assignment_status,
                v.version_status,
                v.approved_by_id,
                v.approved_at,
                oa.approval_notes,
                v.rejection_reason
            FROM orphaned_assignments oa
            JOIN cycle_report_data_profiling_rule_versions v 
                ON v.version_id::text = oa.version_id
            WHERE v.version_status IN ('approved', 'rejected');
            """
            
            result = await db.execute(text(check_sql))
            orphaned = result.fetchall()
            
            if orphaned:
                print(f"\n🔍 Found {len(orphaned)} assignments that should be completed:")
                
                assignment_service = UniversalAssignmentService(db)
                
                for assignment in orphaned:
                    print(f"\n📋 Assignment: {assignment[0]}")
                    print(f"   Version: {assignment[1]}")
                    print(f"   Assignment Status: {assignment[2]}")
                    print(f"   Version Status: {assignment[3]}")
                    
                    # Get approval notes
                    approval_notes = assignment[6] if assignment[3] == 'approved' else assignment[7]
                    
                    # Complete the assignment using UniversalAssignmentService directly
                    await assignment_service.complete_assignment(
                        assignment_id=str(assignment[0]),
                        user_id=assignment[4] or 1,  # Default to system user if null
                        completion_notes=f"Version {assignment[3]} - Auto-completed by fix script",
                        completion_data={
                            "version_id": assignment[1],
                            "version_status": assignment[3],
                            "version_approved": assignment[3] == "approved",
                            "changes_requested": assignment[3] == "rejected"
                        }
                    )
                    
                    result = True
                    
                    if result:
                        print(f"   ✅ Assignment completed successfully")
                    else:
                        print(f"   ❌ Failed to complete assignment")
                
                print(f"\n✅ Processed {len(orphaned)} orphaned assignments")
            else:
                print("\n✅ No orphaned assignments found")
                
        except Exception as e:
            print(f"❌ Error fixing orphaned assignments: {str(e)}")
            raise


if __name__ == "__main__":
    print("🔧 Orphaned Assignment Fix Script")
    print("=" * 50)
    print("\nThis script uses the proper code-based approach to complete assignments.")
    
    asyncio.run(fix_orphaned_assignments())
    
    print("\n✅ Script completed!")