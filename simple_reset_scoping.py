#!/usr/bin/env python3
"""
Simple scoping reset script for testing
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy import select, and_, Integer
from sqlalchemy.ext.asyncio import AsyncSession

# Add the app directory to Python path
sys.path.append('/Users/dineshpatel/code/projects/SynapseDTE')

from app.core.database import AsyncSessionLocal
from app.models.scoping import ScopingVersion, ScopingAttribute, VersionStatus
from app.models.universal_assignment import UniversalAssignment
from app.models.workflow import WorkflowPhase


async def simple_reset_scoping(cycle_id: int, report_id: int):
    """Simple reset for testing"""
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"🔄 Resetting scoping for Cycle {cycle_id}, Report {report_id}")
            
            # 1. Find the phase first
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Scoping"
                )
            )
            
            phase_result = await db.execute(phase_query)
            phase = phase_result.scalar_one_or_none()
            
            if not phase:
                print(f"❌ No Scoping phase found for Cycle {cycle_id}, Report {report_id}")
                return
                
            print(f"📋 Found phase: {phase.phase_id}")
            
            # 2. Find the scoping version for this phase
            version_query = select(ScopingVersion).where(
                ScopingVersion.phase_id == phase.phase_id
            ).order_by(ScopingVersion.created_at.desc())
            
            result = await db.execute(version_query)
            version = result.scalars().first()
            
            if not version:
                print(f"❌ No scoping version found for phase {phase.phase_id}")
                return
                
            print(f"📋 Found scoping version: {version.version_id} (v{version.version_number})")
            print(f"   Current status: {version.version_status}")
            
            # 3. Reset version to DRAFT status
            version.version_status = VersionStatus.DRAFT
            version.submitted_at = None
            version.submitted_by_id = None
            version.approved_at = None
            version.approved_by_id = None
            version.rejected_at = None
            version.rejected_by_id = None
            version.rejection_reason = None
            version.updated_at = datetime.utcnow()
            
            print(f"✅ Reset version status to: {version.version_status}")
            
            # 4. Clear all Report Owner decisions on individual attributes
            attributes_query = select(ScopingAttribute).where(
                ScopingAttribute.version_id == version.version_id
            )
            
            attributes_result = await db.execute(attributes_query)
            attributes = attributes_result.scalars().all()
            
            cleared_decisions = 0
            for attr in attributes:
                if attr.report_owner_decision is not None:
                    attr.report_owner_decision = None
                    attr.report_owner_notes = None
                    attr.report_owner_decided_at = None
                    attr.report_owner_decided_by_id = None
                    cleared_decisions += 1
            
            print(f"✅ Cleared {cleared_decisions} Report Owner attribute decisions")
            
            # 5. Reset Universal Assignment
            # UniversalAssignment stores cycle_id/report_id in context_data JSONB field
            assignment_query = select(UniversalAssignment).where(
                and_(
                    UniversalAssignment.context_data['cycle_id'].astext.cast(Integer) == cycle_id,
                    UniversalAssignment.context_data['report_id'].astext.cast(Integer) == report_id,
                    UniversalAssignment.context_data['phase_name'].astext == "Scoping",
                    UniversalAssignment.assignment_type == "report_owner_review"
                )
            ).order_by(UniversalAssignment.created_at.desc())
            
            assignment_result = await db.execute(assignment_query)
            assignment = assignment_result.scalars().first()
            
            if assignment:
                assignment.status = "Pending"
                assignment.completed_at = None
                assignment.completed_by_user_id = None
                assignment.completion_notes = None
                assignment.updated_at = datetime.utcnow()
                
                print(f"✅ Reset Universal Assignment {assignment.assignment_id} to Pending")
            else:
                print(f"⚠️  No Universal Assignment found for Report Owner review")
            
            # 6. Commit all changes
            await db.commit()
            
            print(f"\n🎉 Successfully reset scoping system!")
            print(f"📝 Testing Steps:")
            print(f"   1. Tester: http://localhost:3000/cycles/{cycle_id}/reports/{report_id}/scoping")
            print(f"   2. Make scoping decisions and submit for Report Owner review")
            print(f"   3. Report Owner: http://localhost:3000/cycles/{cycle_id}/reports/{report_id}/scoping-review")
            print(f"   4. Review individual attributes and approve/reject with notes")
            print(f"   5. Back to Tester page - check 'Report Owner Feedback' tab")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error resetting scoping: {e}")
            raise


async def main():
    if len(sys.argv) != 3:
        print("Usage: python simple_reset_scoping.py <cycle_id> <report_id>")
        print("Example: python simple_reset_scoping.py 55 156")
        sys.exit(1)
    
    try:
        cycle_id = int(sys.argv[1])
        report_id = int(sys.argv[2])
    except ValueError:
        print("❌ cycle_id and report_id must be integers")
        sys.exit(1)
    
    await simple_reset_scoping(cycle_id, report_id)


if __name__ == "__main__":
    asyncio.run(main())