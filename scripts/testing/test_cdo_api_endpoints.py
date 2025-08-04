import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.testing import DataProviderAssignment
from app.models.user import User
from app.models.lob import LOB
from app.models.report_attribute import ReportAttribute

async def test_cdo_api_endpoints():
    """Test the CDO API endpoints that the frontend calls"""
    
    async for db in get_db():
        try:
            print("=" * 80)
            print("TESTING CDO API ENDPOINTS")
            print("=" * 80)
            
            cycle_id = 9
            report_id = 156
            
            # Get the CDO user (David Brown)
            cdo = await db.execute(
                select(User).where(and_(
                    User.role == 'Data Executive',
                    User.first_name == 'David',
                    User.last_name == 'Brown'
                ))
            )
            cdo = cdo.scalar_one_or_none()
            
            if not cdo:
                print("❌ CDO David Brown not found")
                return
                
            print(f"CDO: {cdo.first_name} {cdo.last_name} (ID: {cdo.user_id}, LOB: {cdo.lob_id})")
            
            print(f"\n🔍 TEST 1: get_cdo_assignments endpoint (specific cycle/report)")
            print(f"Endpoint: GET /api/v1/data-owner/{cycle_id}/reports/{report_id}/my-assignments")
            
            # This simulates the get_cdo_assignments endpoint
            assignments_specific = await db.execute(
                select(DataProviderAssignment)
                .where(and_(
                    DataProviderAssignment.cycle_id == cycle_id,
                    DataProviderAssignment.report_id == report_id,
                    DataProviderAssignment.cdo_id == cdo.user_id
                ))
            )
            assignments_specific = assignments_specific.scalars().all()
            
            print(f"Found {len(assignments_specific)} assignments for cycle {cycle_id}, report {report_id}")
            for assignment in assignments_specific:
                print(f"   - Assignment {assignment.assignment_id}: Attribute {assignment.attribute_id}, LOB {assignment.lob_id}, Status: {assignment.status}")
            
            print(f"\n🔍 TEST 2: get_all_cdo_assignments endpoint (all assignments)")
            print(f"Endpoint: GET /api/v1/data-owner/cdo/all-assignments")
            
            # This simulates the get_all_cdo_assignments endpoint
            assignments_all = await db.execute(
                select(DataProviderAssignment)
                .where(DataProviderAssignment.cdo_id == cdo.user_id)
            )
            assignments_all = assignments_all.scalars().all()
            
            print(f"Found {len(assignments_all)} total assignments for CDO")
            for assignment in assignments_all:
                print(f"   - Assignment {assignment.assignment_id}: Cycle {assignment.cycle_id}, Report {assignment.report_id}, Attribute {assignment.attribute_id}, Status: {assignment.status}")
            
            print(f"\n🔍 TEST 3: Check assignment details with joins")
            
            # Get detailed assignment information like the API would return
            detailed_assignments = await db.execute(
                select(
                    DataProviderAssignment.assignment_id,
                    DataProviderAssignment.cycle_id,
                    DataProviderAssignment.report_id,
                    DataProviderAssignment.status,
                    DataProviderAssignment.assigned_at,
                    ReportAttribute.attribute_name,
                    LOB.lob_name
                )
                .join(ReportAttribute, DataProviderAssignment.attribute_id == ReportAttribute.attribute_id)
                .join(LOB, DataProviderAssignment.lob_id == LOB.lob_id)
                .where(and_(
                    DataProviderAssignment.cycle_id == cycle_id,
                    DataProviderAssignment.report_id == report_id,
                    DataProviderAssignment.cdo_id == cdo.user_id
                ))
            )
            detailed_assignments = detailed_assignments.fetchall()
            
            print(f"Detailed assignments:")
            for assignment in detailed_assignments:
                print(f"   - ID: {assignment[0]}")
                print(f"     Cycle: {assignment[1]}, Report: {assignment[2]}")
                print(f"     Attribute: {assignment[5]}")
                print(f"     LOB: {assignment[6]}")
                print(f"     Status: {assignment[3]}")
                print(f"     Assigned At: {assignment[4]}")
                print()
            
            print(f"\n🔍 TEST 4: Check if CDO has correct LOB assignment")
            
            # Check if CDO's LOB matches the assignment LOBs
            cdo_lob = await db.execute(
                select(LOB).where(LOB.lob_id == cdo.lob_id)
            )
            cdo_lob = cdo_lob.scalar_one_or_none()
            
            print(f"CDO's LOB: {cdo_lob.lob_name if cdo_lob else 'None'} (ID: {cdo.lob_id})")
            
            assignment_lobs = set()
            for assignment in assignments_specific:
                assignment_lob = await db.execute(
                    select(LOB).where(LOB.lob_id == assignment.lob_id)
                )
                assignment_lob = assignment_lob.scalar_one_or_none()
                if assignment_lob:
                    assignment_lobs.add(assignment_lob.lob_name)
            
            print(f"Assignment LOBs: {list(assignment_lobs)}")
            
            if cdo_lob and cdo_lob.lob_name in assignment_lobs:
                print("✅ CDO's LOB matches assignment LOBs")
            else:
                print("❌ CDO's LOB doesn't match assignment LOBs")
            
            if len(assignments_specific) > 0:
                print(f"\n✅ CONCLUSION: CDO should see {len(assignments_specific)} assignments")
                print("If CDO is not seeing assignments in the UI, check:")
                print("1. Frontend is calling the correct API endpoint")
                print("2. CDO authentication/session is working")
                print("3. Frontend is filtering by the correct cycle/report")
                print("4. Check browser console for API errors")
            else:
                print(f"\n❌ ISSUE: No assignments found for CDO")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(test_cdo_api_endpoints()) 