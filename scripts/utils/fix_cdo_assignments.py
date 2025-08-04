import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from datetime import datetime
from app.core.database import get_db
from app.models.testing import DataProviderAssignment
from app.models.report_attribute import ReportAttribute
from app.models.scoping import TesterScopingDecision
from app.models.sample_selection import SampleRecord, SampleSet
from app.models.user import User
from app.models.lob import LOB

async def fix_cdo_assignments():
    """Delete current incorrect assignments and recreate them properly with LOB and CDO assignments"""
    
    async for db in get_db():
        try:
            print("=" * 80)
            print("FIXING CDO ASSIGNMENTS")
            print("=" * 80)
            
            cycle_id = 9
            report_id = 156
            created_by = 3  # Tester who started the phase
            
            print(f"\n🗑️  STEP 1: Delete current incorrect assignments")
            
            # Delete existing assignments
            delete_result = await db.execute(
                delete(DataProviderAssignment).where(and_(
                    DataProviderAssignment.cycle_id == cycle_id,
                    DataProviderAssignment.report_id == report_id
                ))
            )
            print(f"Deleted {delete_result.rowcount} existing assignments")
            
            print(f"\n🔍 STEP 2: Get scoped attributes and their LOBs from sample data")
            
            # Get non-primary key scoped attributes
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
            
            print(f"Found {len(scoped_attributes)} non-primary key scoped attributes")
            
            # Get approved sample records with LOB assignments
            samples = await db.execute(
                select(SampleRecord)
                .join(SampleSet, SampleRecord.set_id == SampleSet.set_id)
                .where(and_(
                    SampleSet.cycle_id == cycle_id,
                    SampleSet.report_id == report_id,
                    SampleRecord.approval_status == 'Approved'
                ))
            )
            samples = samples.scalars().all()
            
            print(f"Found {len(samples)} approved sample records")
            
            # Get all LOBs
            all_lobs = await db.execute(select(LOB))
            all_lobs = {lob.lob_name: lob for lob in all_lobs.scalars().all()}
            
            # Get all CDOs
            all_cdos = await db.execute(
                select(User).where(User.role == 'Data Executive')
            )
            all_cdos = {cdo.lob_id: cdo for cdo in all_cdos.scalars().all()}
            
            print(f"Found {len(all_lobs)} LOBs and {len(all_cdos)} CDOs")
            
            print(f"\n🏗️  STEP 3: Create proper assignments")
            
            created_count = 0
            
            for attr in scoped_attributes:
                print(f"\n📋 Processing attribute: {attr.attribute_name} (ID: {attr.attribute_id})")
                
                # Get LOBs for this attribute from sample data
                attribute_lobs = set()
                for sample in samples:
                    if sample.data_source_info and 'lob_assignments' in sample.data_source_info:
                        lob_assignments = sample.data_source_info['lob_assignments']
                        if attr.attribute_name in lob_assignments:
                            lob_name = lob_assignments[attr.attribute_name]
                            attribute_lobs.add(lob_name)
                
                print(f"   LOBs for this attribute: {list(attribute_lobs)}")
                
                # Create one assignment per LOB for this attribute
                for lob_name in attribute_lobs:
                    if lob_name in all_lobs:
                        lob = all_lobs[lob_name]
                        cdo = all_cdos.get(lob.lob_id)
                        
                        if cdo:
                            # Create assignment record
                            assignment = DataProviderAssignment(
                                cycle_id=cycle_id,
                                report_id=report_id,
                                attribute_id=attr.attribute_id,
                                lob_id=lob.lob_id,
                                cdo_id=cdo.user_id,  # Assign the CDO for this LOB
                                data_owner_id=None,  # Will be set when CDO assigns data provider
                                assigned_by=created_by,
                                assigned_at=datetime.utcnow(),
                                status='Assigned'
                            )
                            db.add(assignment)
                            created_count += 1
                            print(f"   ✅ Created assignment: LOB={lob_name} (ID: {lob.lob_id}), CDO={cdo.first_name} {cdo.last_name} (ID: {cdo.user_id})")
                        else:
                            print(f"   ❌ No CDO found for LOB {lob_name} (ID: {lob.lob_id})")
                    else:
                        print(f"   ❌ LOB '{lob_name}' not found in database")
            
            # Commit the changes
            await db.commit()
            print(f"\n🎉 Successfully created {created_count} proper DataProviderAssignment records")
            
            # Verify the assignments were created
            print(f"\n🔍 STEP 4: Verify assignments")
            all_assignments = await db.execute(
                select(DataProviderAssignment).where(and_(
                    DataProviderAssignment.cycle_id == cycle_id,
                    DataProviderAssignment.report_id == report_id
                ))
            )
            all_assignments = all_assignments.scalars().all()
            
            print(f"Total assignments now: {len(all_assignments)}")
            for assignment in all_assignments:
                print(f"   - Attribute {assignment.attribute_id}, LOB {assignment.lob_id}, CDO {assignment.cdo_id}, Status: {assignment.status}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(fix_cdo_assignments()) 