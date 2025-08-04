import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.sample_selection import SampleRecord, SampleSet

async def check_sample_lob_data():
    """Check what sample data exists and what LOB assignments are available"""
    
    async for db in get_db():
        try:
            print("=" * 80)
            print("CHECKING SAMPLE LOB DATA")
            print("=" * 80)
            
            cycle_id = 9
            report_id = 156
            
            # Get all sample sets for this cycle/report
            sample_sets = await db.execute(
                select(SampleSet).where(and_(
                    SampleSet.cycle_id == cycle_id,
                    SampleSet.report_id == report_id
                ))
            )
            sample_sets = sample_sets.scalars().all()
            
            print(f"Found {len(sample_sets)} sample sets:")
            for sample_set in sample_sets:
                print(f"   - {sample_set.set_name} (ID: {sample_set.set_id}, Status: {sample_set.status})")
                
                # Get sample records for this set
                sample_records = await db.execute(
                    select(SampleRecord).where(SampleRecord.set_id == sample_set.set_id)
                )
                sample_records = sample_records.scalars().all()
                
                print(f"     Sample records: {len(sample_records)}")
                for record in sample_records:
                    print(f"       - {record.sample_identifier} (Status: {record.approval_status})")
                    if record.data_source_info:
                        print(f"         Data source info keys: {list(record.data_source_info.keys())}")
                        if 'lob_assignments' in record.data_source_info:
                            lob_assignments = record.data_source_info['lob_assignments']
                            print(f"         LOB assignments: {lob_assignments}")
                        else:
                            print(f"         No lob_assignments in data_source_info")
                    else:
                        print(f"         No data_source_info")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(check_sample_lob_data()) 