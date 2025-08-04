import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.sample_selection import SampleRecord, SampleSet

async def check_sample_data_structure():
    """Check the actual structure of sample data to understand LOB assignments"""
    
    async for db in get_db():
        try:
            print("=" * 80)
            print("CHECKING SAMPLE DATA STRUCTURE")
            print("=" * 80)
            
            cycle_id = 9
            report_id = 156
            
            # Get approved sample records
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
            
            print(f"Found {len(samples)} approved sample records:")
            
            for i, sample in enumerate(samples):
                print(f"\n📋 Sample {i+1}: {sample.sample_identifier}")
                print(f"   Primary Key Value: {sample.primary_key_value}")
                print(f"   Approval Status: {sample.approval_status}")
                
                if sample.data_source_info:
                    print(f"   Data Source Info Keys: {list(sample.data_source_info.keys())}")
                    print(f"   Data Source Info: {json.dumps(sample.data_source_info, indent=2)}")
                else:
                    print(f"   ❌ No data_source_info")
                
                if sample.sample_data:
                    print(f"   Sample Data Keys: {list(sample.sample_data.keys())}")
                    # Look for LOB-related fields in sample_data
                    for key, value in sample.sample_data.items():
                        if 'lob' in key.lower() or 'LOB' in key:
                            print(f"   LOB-related field: {key} = {value}")
                else:
                    print(f"   ❌ No sample_data")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(check_sample_data_structure()) 