import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from datetime import datetime
from app.core.database import get_db
from app.models.testing import DataProviderAssignment
from app.models.report_attribute import ReportAttribute
from app.models.scoping import TesterScopingDecision
from app.models.sample_selection import SampleRecord, SampleSet
from app.models.user import User
from app.models.lob import LOB

async def fix_cdo_assignments_v2():
    """Create proper CDO assignments based on the actual LOB assignment structure"""
    
    async for db in get_db():
        try:
            print("=" * 80)
            print("FIXING CDO ASSIGNMENTS V2")
            print("=" * 80)
            
            cycle_id = 9
            report_id = 156
            created_by = 3  # Tester who started the phase
            
            print(f"\n🔧 STEP 1: Add cdo_id column to data_owner_assignments table")
            
            try:
                # Check if column exists
                result = await db.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'data_owner_assignments' 
                    AND column_name = 'cdo_id'
                """))
                column_exists = result.scalar_one_or_none()
                
                if not column_exists:
                    # Add the column
                    await db.execute(text("""
                        ALTER TABLE data_owner_assignments 
                        ADD COLUMN cdo_id INTEGER REFERENCES users(user_id)
                    """))
                    await db.commit()
                    print("✅ Added cdo_id column to data_owner_assignments table")
                else:
                    print("✅ cdo_id column already exists")
            except Exception as e:
                print(f"⚠️  Column addition failed (might already exist): {e}")
                await db.rollback()
            
            print(f"\n🔍 STEP 2: Get scoped attributes and LOBs from sample data")
            
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
            
            # Extract LOBs from sample data (they apply to all attributes in the sample)
            all_lobs_in_samples = set()
            for sample in samples:
                if sample.data_source_info and 'lob_assignments' in sample.data_source_info:
                    lob_list = sample.data_source_info['lob_assignments']
                    if isinstance(lob_list, list):
                        all_lobs_in_samples.update(lob_list)
            
            print(f"LOBs found in samples: {list(all_lobs_in_samples)}")
            
            # Get all LOBs from database
            all_lobs = await db.execute(select(LOB))
            all_lobs = {lob.lob_name: lob for lob in all_lobs.scalars().all()}
            
            # Get all CDOs
            all_cdos = await db.execute(
                select(User).where(User.role == 'Data Executive')
            )
            all_cdos = {cdo.lob_id: cdo for cdo in all_cdos.scalars().all()}
            
            print(f"Found {len(all_lobs)} LOBs in database and {len(all_cdos)} CDOs")
            
            print(f"\n🏗️  STEP 3: Create proper assignments")
            
            created_count = 0
            
            # For each scoped attribute, create assignments for each LOB found in samples
            for attr in scoped_attributes:
                print(f"\n📋 Processing attribute: {attr.attribute_name} (ID: {attr.attribute_id})")
                
                # Create one assignment per LOB for this attribute
                for lob_name in all_lobs_in_samples:
                    if lob_name in all_lobs:
                        lob = all_lobs[lob_name]
                        cdo = all_cdos.get(lob.lob_id)
                        
                        if cdo:
                            # Create assignment record using raw SQL to avoid model issues
                            await db.execute(text("""
                                INSERT INTO data_owner_assignments 
                                (cycle_id, report_id, attribute_id, lob_id, cdo_id, data_owner_id, assigned_by, assigned_at, status)
                                VALUES (:cycle_id, :report_id, :attribute_id, :lob_id, :cdo_id, NULL, :assigned_by, :assigned_at, 'Assigned')
                            """), {
                                'cycle_id': cycle_id,
                                'report_id': report_id,
                                'attribute_id': attr.attribute_id,
                                'lob_id': lob.lob_id,
                                'cdo_id': cdo.user_id,
                                'assigned_by': created_by,
                                'assigned_at': datetime.utcnow()
                            })
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
            result = await db.execute(text("""
                SELECT assignment_id, attribute_id, lob_id, cdo_id, status
                FROM data_owner_assignments 
                WHERE cycle_id = :cycle_id AND report_id = :report_id
            """), {'cycle_id': cycle_id, 'report_id': report_id})
            
            assignments = result.fetchall()
            print(f"Total assignments now: {len(assignments)}")
            for assignment in assignments:
                print(f"   - Assignment {assignment[0]}: Attribute {assignment[1]}, LOB {assignment[2]}, CDO {assignment[3]}, Status: {assignment[4]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(fix_cdo_assignments_v2()) 