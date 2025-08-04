#\!/usr/bin/env python3
"""
Complete the stuck Universal Assignment that was missed during API approval
"""

import asyncio
import sys
import os
sys.path.append('/Users/dineshpatel/code/projects/SynapseDTE')

from app.core.database import AsyncSessionLocal
from sqlalchemy import select, and_
from app.models.universal_assignment import UniversalAssignment
from app.services.universal_assignment_service import UniversalAssignmentService
from datetime import datetime

async def complete_stuck_assignment():
    """Complete the assignment that's stuck in Assigned status"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Find the specific assignment for version 36bb8065-51ad-457d-b1ce-9e813b360b7c
            assignment_query = select(UniversalAssignment).where(
                and_(
                    UniversalAssignment.assignment_type == "Scoping Approval",
                    UniversalAssignment.title == "Review Updated Scoping Decisions",
                    UniversalAssignment.status == "Assigned"
                )
            )
            
            result = await db.execute(assignment_query)
            assignment = result.scalar_one_or_none()
            
            if not assignment:
                print("❌ No stuck assignment found")
                return
                
            print(f"🎯 Found stuck assignment: {assignment.assignment_id}")
            print(f"   Title: {assignment.title}")
            print(f"   Status: {assignment.status}")
            print(f"   Context: {assignment.context_data}")
            
            # Check if this is for the approved version
            context_data = assignment.context_data or {}
            version_id = context_data.get("version_id")
            
            if version_id != "36bb8065-51ad-457d-b1ce-9e813b360b7c":
                print(f"❌ Assignment is for different version: {version_id}")
                return
                
            # Complete the assignment
            assignment_service = UniversalAssignmentService(db)
            
            await assignment_service.complete_assignment(
                assignment_id=assignment.assignment_id,
                user_id=4,  # Report Owner user ID
                completion_notes="Scoping version approved: Version approved via API",
                completion_data={
                    "approval_action": "approved",
                    "version_id": version_id,
                    "version_number": 31,
                    "approved_at": datetime.utcnow().isoformat(),
                    "completed_retroactively": True
                }
            )
            
            print(f"✅ Successfully completed assignment {assignment.assignment_id}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🔧 Completing Stuck Universal Assignment...")
    asyncio.run(complete_stuck_assignment())