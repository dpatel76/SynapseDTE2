import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import AsyncSessionLocal
from app.models.sample_selection import SampleSelectionVersion, SampleSelectionSample

async def check_version_samples():
    async with AsyncSessionLocal() as db:
        # Check for phase 468
        phase_id = 468
        
        # Get all versions
        versions_result = await db.execute(
            select(SampleSelectionVersion)
            .where(SampleSelectionVersion.phase_id == phase_id)
            .order_by(SampleSelectionVersion.version_number)
        )
        versions = versions_result.scalars().all()
        
        print(f"\nVersions for phase {phase_id}:")
        for v in versions:
            # Count samples for each version
            sample_count_result = await db.execute(
                select(func.count(SampleSelectionSample.sample_id))
                .where(SampleSelectionSample.version_id == v.version_id)
            )
            sample_count = sample_count_result.scalar()
            
            status = v.version_status if isinstance(v.version_status, str) else v.version_status.value
            print(f"\n  Version {v.version_number} ({status}):")
            print(f"    - ID: {v.version_id}")
            print(f"    - Sample count: {sample_count}")
            print(f"    - Parent version: {v.parent_version_id}")
            
            # If it's a recent draft version, check sample details
            if v.version_number >= 4 and status == 'draft':
                samples_result = await db.execute(
                    select(SampleSelectionSample)
                    .where(SampleSelectionSample.version_id == v.version_id)
                    .limit(3)
                )
                samples = samples_result.scalars().all()
                if samples:
                    print(f"    - First few samples:")
                    for s in samples:
                        print(f"      • {s.sample_identifier} - RO Decision: {s.report_owner_decision}")
                else:
                    print(f"    - No samples found\!")

from sqlalchemy import func

if __name__ == "__main__":
    asyncio.run(check_version_samples())
