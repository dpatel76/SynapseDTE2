import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.sample_selection import SampleSet, SampleRecord
from app.models.report_attribute import ReportAttribute
from app.models.scoping import TesterScopingDecision
from app.models.lob import LOB
from app.schemas.data_owner import AttributeAssignmentStatus, AssignmentStatus

async def test_assignment_matrix_direct():
    """Test the assignment matrix logic directly to see what LOB data is returned"""
    
    async for db in get_db():
        try:
            print("=" * 80)
            print("TESTING ASSIGNMENT MATRIX LOGIC DIRECTLY")
            print("=" * 80)
            
            cycle_id = 9
            report_id = 156
            
            print(f"\n🔍 Testing for cycle_id={cycle_id}, report_id={report_id}")
            
            # Step 1: Get attributes (same logic as in the API)
            print("\n📋 STEP 1: Getting attributes for data provider phase")
            
            # First get primary key attributes
            primary_key_attributes = await db.execute(
                select(ReportAttribute)
                .where(and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id,
                    ReportAttribute.is_primary_key == True
                ))
            )
            primary_key_attributes = primary_key_attributes.scalars().all()
            
            # Then get attributes selected for scoping (final_scoping=True)
            scoped_attributes = await db.execute(
                select(ReportAttribute)
                .join(TesterScopingDecision, ReportAttribute.attribute_id == TesterScopingDecision.attribute_id)
                .where(and_(
                    ReportAttribute.cycle_id == cycle_id,
                    ReportAttribute.report_id == report_id,
                    TesterScopingDecision.cycle_id == cycle_id,
                    TesterScopingDecision.report_id == report_id,
                    TesterScopingDecision.final_scoping == True,
                    ReportAttribute.is_primary_key == False
                ))
            )
            scoped_attributes = scoped_attributes.scalars().all()
            
            # Combine both lists
            attributes = list(primary_key_attributes) + list(scoped_attributes)
            
            print(f"   Primary Key attributes: {len(primary_key_attributes)}")
            print(f"   Scoped non-PK attributes: {len(scoped_attributes)}")
            print(f"   Total attributes: {len(attributes)}")
            
            # Step 2: Process each attribute (same logic as in the API)
            print("\n📋 STEP 2: Processing each attribute for LOB assignments")
            
            assignment_statuses = []
            
            for attribute in attributes:
                print(f"\n   🔍 Processing attribute: {attribute.attribute_name}")
                
                # Get LOB assignments from approved sample records that contain this attribute
                sample_lobs = await db.execute(
                    select(SampleRecord.data_source_info)
                    .join(SampleSet, SampleRecord.set_id == SampleSet.set_id)
                    .where(and_(
                        SampleSet.cycle_id == cycle_id,
                        SampleSet.report_id == report_id,
                        SampleSet.status == 'Approved',
                        SampleRecord.sample_data.has_key(attribute.attribute_name)
                    ))
                )
                sample_lobs = sample_lobs.scalars().all()
                
                print(f"      Found {len(sample_lobs)} sample records containing this attribute")
                
                # Extract unique LOB names from sample records
                unique_lob_names = set()
                for data_source_info in sample_lobs:
                    if data_source_info and 'lob_assignments' in data_source_info:
                        lob_assignments = data_source_info['lob_assignments']
                        if isinstance(lob_assignments, list):
                            unique_lob_names.update(lob_assignments)
                
                print(f"      Unique LOB names found: {list(unique_lob_names)}")
                
                # Convert LOB names to LOB objects
                assigned_lobs = []
                if unique_lob_names:
                    lob_objects = await db.execute(
                        select(LOB)
                        .where(LOB.lob_name.in_(list(unique_lob_names)))
                    )
                    lob_objects = lob_objects.scalars().all()
                    assigned_lobs = [
                        {"lob_id": lob.lob_id, "lob_name": lob.lob_name}
                        for lob in lob_objects
                    ]
                
                print(f"      Final assigned LOBs: {assigned_lobs}")
                
                # Create assignment status (simplified version of API logic)
                if attribute.is_primary_key:
                    assignment_status = AttributeAssignmentStatus(
                        attribute_id=attribute.attribute_id,
                        attribute_name=attribute.attribute_name,
                        is_primary_key=True,
                        assigned_lobs=assigned_lobs,
                        data_owner_id=None,
                        data_owner_name="N/A - Primary Key",
                        assigned_by=None,
                        assigned_at=None,
                        status=AssignmentStatus.COMPLETED,
                        assignment_notes="Primary key attribute - no data provider needed",
                        is_overdue=False,
                        sla_deadline=None,
                        hours_remaining=None
                    )
                else:
                    assignment_status = AttributeAssignmentStatus(
                        attribute_id=attribute.attribute_id,
                        attribute_name=attribute.attribute_name,
                        is_primary_key=False,
                        assigned_lobs=assigned_lobs,
                        data_owner_id=None,
                        data_owner_name=None,
                        assigned_by=None,
                        assigned_at=None,
                        status=AssignmentStatus.ASSIGNED,
                        assignment_notes=None,
                        is_overdue=False,
                        sla_deadline=None,
                        hours_remaining=None
                    )
                
                assignment_statuses.append(assignment_status)
                
                print(f"      ✅ Assignment status created:")
                print(f"         - Is Primary Key: {assignment_status.is_primary_key}")
                print(f"         - Assigned LOBs: {assignment_status.assigned_lobs}")
                print(f"         - Status: {assignment_status.status}")
            
            # Step 3: Summary
            print(f"\n📋 STEP 3: Summary")
            
            assignments_with_lobs = [a for a in assignment_statuses if a.assigned_lobs]
            assignments_without_lobs = [a for a in assignment_statuses if not a.assigned_lobs]
            
            print(f"   Total assignments: {len(assignment_statuses)}")
            print(f"   Assignments WITH LOBs: {len(assignments_with_lobs)}")
            print(f"   Assignments WITHOUT LOBs: {len(assignments_without_lobs)}")
            
            if assignments_without_lobs:
                print(f"\n   ❌ Assignments missing LOBs:")
                for assignment in assignments_without_lobs:
                    print(f"      - {assignment.attribute_name} (PK: {assignment.is_primary_key})")
            
            if assignments_with_lobs:
                print(f"\n   ✅ Assignments with LOBs:")
                for assignment in assignments_with_lobs:
                    lob_names = [lob['lob_name'] for lob in assignment.assigned_lobs]
                    print(f"      - {assignment.attribute_name}: {lob_names}")
            
            print(f"\n" + "=" * 80)
            print("ASSIGNMENT MATRIX LOGIC TEST COMPLETED")
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(test_assignment_matrix_direct()) 