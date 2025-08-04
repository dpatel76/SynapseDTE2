#!/usr/bin/env python3
"""
Test script to verify sample feedback visibility for Testers
"""

import asyncio
import sys
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Add the project root to the Python path
sys.path.append('/Users/dineshpatel/code/projects/SynapseDTE')

from app.core.database import AsyncSessionLocal
from app.models.sample_selection import SampleSet, SampleApprovalHistory
from app.models.user import User

async def test_feedback_visibility():
    """Test feedback visibility for a specific cycle/report"""
    
    # Test parameters - update these for your specific test case
    CYCLE_ID = 13  # Update with your cycle ID
    REPORT_ID = 1  # Update with your report ID
    
    async with AsyncSessionLocal() as db:
        print(f"\n🔍 Checking Sample Feedback for Cycle {CYCLE_ID}, Report {REPORT_ID}")
        print("=" * 80)
        
        # Get all sample sets
        result = await db.execute(
            select(SampleSet)
            .where(and_(
                SampleSet.cycle_id == CYCLE_ID,
                SampleSet.report_id == REPORT_ID
            ))
            .order_by(SampleSet.created_at.desc())
        )
        sample_sets = result.scalars().all()
        
        print(f"\n📊 Found {len(sample_sets)} sample sets:")
        
        for sample_set in sample_sets:
            print(f"\n📁 Sample Set: {sample_set.set_id}")
            print(f"   Status: {sample_set.status}")
            print(f"   Created: {sample_set.created_at}")
            print(f"   Created By User ID: {sample_set.created_by_user_id}")
            
            # Check for approval history
            approval_result = await db.execute(
                select(SampleApprovalHistory)
                .options(selectinload(SampleApprovalHistory.approved_by_user))
                .where(SampleApprovalHistory.set_id == sample_set.set_id)
                .order_by(SampleApprovalHistory.approved_at.desc())
            )
            approval_histories = approval_result.scalars().all()
            
            if approval_histories:
                print(f"   📝 Approval History ({len(approval_histories)} entries):")
                for idx, history in enumerate(approval_histories):
                    print(f"      [{idx+1}] Decision: {history.decision}")
                    print(f"          Approved By: {history.approved_by_user.full_name if history.approved_by_user else 'Unknown'}")
                    print(f"          Feedback: {history.feedback or 'No feedback'}")
                    print(f"          Requested Changes: {history.requested_changes or []}")
                    print(f"          Date: {history.approved_at}")
                    
                    # Check if this would trigger feedback alert
                    if sample_set.status == 'Revision Required' and history.decision in ['Needs Changes', 'Revision Required']:
                        print(f"      ⚠️  This should trigger feedback alert for Tester!")
            else:
                print(f"   ❌ No approval history found")
        
        # Summary
        revision_required_count = sum(1 for s in sample_sets if s.status == 'Revision Required')
        print(f"\n📊 Summary:")
        print(f"   Total Sample Sets: {len(sample_sets)}")
        print(f"   Revision Required: {revision_required_count}")
        print(f"   Pending Approval: {sum(1 for s in sample_sets if s.status == 'Pending Approval')}")
        print(f"   Approved: {sum(1 for s in sample_sets if s.status == 'Approved')}")
        print(f"   Rejected: {sum(1 for s in sample_sets if s.status == 'Rejected')}")
        
        if revision_required_count > 0:
            print(f"\n⚠️  {revision_required_count} sample set(s) need revision!")
            print("   The feedback alert should appear for Testers viewing this report.")

if __name__ == "__main__":
    asyncio.run(test_feedback_visibility())