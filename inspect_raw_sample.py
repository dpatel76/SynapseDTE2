#!/usr/bin/env python3
"""Inspect raw sample data in phase_data"""
import asyncio
import json
from app.core.database import AsyncSessionLocal
from app.models.workflow import WorkflowPhase
from sqlalchemy import select, and_

async def inspect_raw():
    async with AsyncSessionLocal() as db:
        # Get Sample Selection phase
        phase = await db.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == 55,
                    WorkflowPhase.report_id == 156,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
        )
        phase_obj = phase.scalar_one_or_none()
        
        if phase_obj and phase_obj.phase_data:
            # Look for raw generation results
            if 'intelligent_sampling_raw_result' in phase_obj.phase_data:
                print("Found raw result!")
                raw = phase_obj.phase_data['intelligent_sampling_raw_result']
                if 'samples' in raw and raw['samples']:
                    print(f"\nFirst raw sample:")
                    print(json.dumps(raw['samples'][0], indent=2))
            
            # Check if we have the detailed structure
            samples = phase_obj.phase_data.get("cycle_report_sample_selection_samples", [])
            if samples:
                # Look at internal structure 
                first_sample = samples[0]
                print("\n🔍 First sample structure:")
                for key, value in first_sample.items():
                    print(f"  {key}: {type(value)} = {value if key != 'sample_data' else '...'}")
                
                print("\n📊 Sample data keys:")
                if 'sample_data' in first_sample:
                    for k, v in first_sample['sample_data'].items():
                        print(f"    {k}: {v}")

if __name__ == "__main__":
    asyncio.run(inspect_raw())