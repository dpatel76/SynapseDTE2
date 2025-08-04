import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from app.core.database import get_db
from app.models.sample_selection import SampleSet, SampleRecord

async def update_lob_assignments():
    """Update LOB assignments from 'Risk Management' to 'GBM' for approved sample sets"""
    
    async for db in get_db():
        try:
            print("=" * 80)
            print("UPDATING LOB ASSIGNMENTS: Risk Management → GBM")
            print("=" * 80)
            
            # Step 1: Find all approved sample sets
            print("\n🔍 STEP 1: Finding approved sample sets")
            
            approved_sample_sets = await db.execute(
                select(SampleSet)
                .where(SampleSet.status == 'Approved')
            )
            approved_sample_sets = approved_sample_sets.scalars().all()
            
            print(f"   Found {len(approved_sample_sets)} approved sample sets")
            
            if not approved_sample_sets:
                print("   No approved sample sets found. Exiting.")
                return
            
            # Step 2: Get all sample records for approved sets
            print(f"\n🔍 STEP 2: Finding sample records in approved sets")
            
            approved_set_ids = [ss.set_id for ss in approved_sample_sets]
            print(f"   Approved set IDs: {approved_set_ids}")
            
            sample_records = await db.execute(
                select(SampleRecord)
                .where(SampleRecord.set_id.in_(approved_set_ids))
            )
            sample_records = sample_records.scalars().all()
            
            print(f"   Found {len(sample_records)} sample records in approved sets")
            
            # Step 3: Identify records that need updating
            print(f"\n🔍 STEP 3: Identifying records with 'Risk Management' LOB")
            
            records_to_update = []
            
            for record in sample_records:
                if record.data_source_info and 'lob_assignments' in record.data_source_info:
                    lob_assignments = record.data_source_info['lob_assignments']
                    
                    # Check if 'Risk Management' is in the LOB assignments
                    if 'Risk Management' in lob_assignments:
                        records_to_update.append({
                            'record': record,
                            'current_lobs': lob_assignments.copy(),
                            'sample_id': record.sample_identifier,
                            'set_id': record.set_id
                        })
                        print(f"   🎯 Sample {record.sample_identifier} (Set: {record.set_id}): {lob_assignments}")
            
            print(f"\n   📊 Summary:")
            print(f"      Total sample records: {len(sample_records)}")
            print(f"      Records with 'Risk Management': {len(records_to_update)}")
            
            if not records_to_update:
                print(f"   ✅ No records need updating. All LOB assignments are already correct.")
                return
            
            # Step 4: Perform the updates
            print(f"\n🔄 STEP 4: Updating LOB assignments")
            
            updated_count = 0
            
            for item in records_to_update:
                record = item['record']
                current_lobs = item['current_lobs']
                sample_id = item['sample_id']
                set_id = item['set_id']
                
                # Replace 'Risk Management' with 'GBM'
                new_lobs = []
                for lob in current_lobs:
                    if lob == 'Risk Management':
                        new_lobs.append('GBM')
                        print(f"      🔄 Sample {sample_id}: '{lob}' → 'GBM'")
                    else:
                        new_lobs.append(lob)
                
                # Update the data_source_info
                new_data_source_info = record.data_source_info.copy()
                new_data_source_info['lob_assignments'] = new_lobs
                
                # Update the record
                record.data_source_info = new_data_source_info
                updated_count += 1
                
                print(f"      ✅ Updated sample {sample_id}: {current_lobs} → {new_lobs}")
            
            # Step 5: Commit the changes
            print(f"\n💾 STEP 5: Committing changes to database")
            
            await db.commit()
            
            print(f"   ✅ Successfully committed {updated_count} updates")
            
            # Step 6: Verify the updates
            print(f"\n🔍 STEP 6: Verifying updates")
            
            # Re-query the updated records to verify
            verification_records = await db.execute(
                select(SampleRecord)
                .where(SampleRecord.set_id.in_(approved_set_ids))
            )
            verification_records = verification_records.scalars().all()
            
            risk_mgmt_count = 0
            gbm_count = 0
            
            for record in verification_records:
                if record.data_source_info and 'lob_assignments' in record.data_source_info:
                    lob_assignments = record.data_source_info['lob_assignments']
                    
                    if 'Risk Management' in lob_assignments:
                        risk_mgmt_count += 1
                    if 'GBM' in lob_assignments:
                        gbm_count += 1
            
            print(f"   📊 Verification Results:")
            print(f"      Records with 'Risk Management': {risk_mgmt_count}")
            print(f"      Records with 'GBM': {gbm_count}")
            
            if risk_mgmt_count == 0:
                print(f"   ✅ SUCCESS: All 'Risk Management' LOBs have been updated to 'GBM'")
            else:
                print(f"   ⚠️  WARNING: {risk_mgmt_count} records still have 'Risk Management'")
            
            # Final summary
            print(f"\n" + "=" * 80)
            print("LOB ASSIGNMENT UPDATE SUMMARY")
            print("=" * 80)
            print(f"✅ Approved sample sets processed: {len(approved_sample_sets)}")
            print(f"✅ Sample records examined: {len(sample_records)}")
            print(f"✅ Records updated: {updated_count}")
            print(f"✅ 'Risk Management' → 'GBM' conversions: {updated_count}")
            
            if risk_mgmt_count == 0 and updated_count > 0:
                print(f"🎉 ALL LOB ASSIGNMENTS SUCCESSFULLY UPDATED!")
            elif updated_count == 0:
                print(f"ℹ️  NO UPDATES NEEDED - All assignments were already correct")
            
        except Exception as e:
            print(f"❌ Error during LOB assignment update: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(update_lob_assignments()) 