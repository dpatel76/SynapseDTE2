import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.testing import DataProviderAssignment
from app.models.user import User
from app.models.lob import LOB
from app.models.report_attribute import ReportAttribute

async def test_cdo_can_see_assignments():
    """Test if the CDO can see their assignments"""
    
    async for db in get_db():
        try:
            print("=" * 80)
            print("TESTING CDO ASSIGNMENT VISIBILITY")
            print("=" * 80)
            
            cycle_id = 9
            report_id = 156
            
            # Get the CDO user
            cdo = await db.execute(
                select(User).where(User.role == 'Data Executive')
            )
            cdo = cdo.scalar_one_or_none()
            
            if not cdo:
                print("❌ No CDO found")
                return
                
            print(f"CDO: {cdo.first_name} {cdo.last_name} (ID: {cdo.user_id}, LOB: {cdo.lob_id})")
            
            # Get assignments for this CDO
            assignments = await db.execute(
                select(DataProviderAssignment)
                .join(ReportAttribute, DataProviderAssignment.attribute_id == ReportAttribute.attribute_id)
                .join(LOB, DataProviderAssignment.lob_id == LOB.lob_id)
                .where(and_(
                    DataProviderAssignment.cycle_id == cycle_id,
                    DataProviderAssignment.report_id == report_id,
                    DataProviderAssignment.cdo_id == cdo.user_id
                ))
            )
            assignments = assignments.scalars().all()
            
            print(f"\n📋 Assignments for CDO {cdo.first_name} {cdo.last_name}:")
            print(f"Found {len(assignments)} assignments")
            
            for assignment in assignments:
                # Get attribute and LOB details
                attribute = await db.execute(
                    select(ReportAttribute).where(ReportAttribute.attribute_id == assignment.attribute_id)
                )
                attribute = attribute.scalar_one_or_none()
                
                lob = await db.execute(
                    select(LOB).where(LOB.lob_id == assignment.lob_id)
                )
                lob = lob.scalar_one_or_none()
                
                print(f"   - Assignment {assignment.assignment_id}:")
                print(f"     Attribute: {attribute.attribute_name if attribute else 'Unknown'} (ID: {assignment.attribute_id})")
                print(f"     LOB: {lob.lob_name if lob else 'Unknown'} (ID: {assignment.lob_id})")
                print(f"     Status: {assignment.status}")
                print(f"     Data Provider: {assignment.data_owner_id or 'Not assigned yet'}")
                print(f"     Assigned At: {assignment.assigned_at}")
            
            if len(assignments) > 0:
                print(f"\n✅ SUCCESS: CDO can see {len(assignments)} assignment(s)")
                print("The CDO should now be able to log in and see tasks for assigning data providers!")
            else:
                print(f"\n❌ ISSUE: CDO has no assignments visible")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(test_cdo_can_see_assignments()) 