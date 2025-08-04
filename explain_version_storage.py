#!/usr/bin/env python3
"""Explain how versions are stored"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
import json

async def explain_storage():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        # Check if there's a sample_selection_versions table
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%version%'
            ORDER BY table_name
        """))
        
        print("=== Tables with 'version' in name ===")
        for row in result:
            print(f"  - {row.table_name}")
        
        # Check workflow_phases structure
        result = await db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'workflow_phases'
            AND column_name IN ('phase_data', 'metadata')
        """))
        
        print("\n=== workflow_phases columns ===")
        for row in result:
            print(f"  - {row.column_name}: {row.data_type}")
        
        # Get actual phase_data content
        result = await db.execute(text("""
            SELECT phase_data::text
            FROM workflow_phases
            WHERE cycle_id = 55 AND report_id = 156
            AND phase_name = 'Sample Selection'
        """))
        
        phase = result.fetchone()
        if phase:
            phase_data = json.loads(phase[0])
            
            print("\n=== phase_data structure (keys) ===")
            for key in phase_data.keys():
                if key == 'versions':
                    print(f"  - {key}: [{len(phase_data[key])} items]")
                    print("    Example version structure:")
                    if phase_data[key]:
                        v = phase_data[key][0]
                        for k in v.keys():
                            print(f"      - {k}")
                elif key == 'cycle_report_sample_selection_samples':
                    print(f"  - {key}: [{len(phase_data[key])} samples]")
                else:
                    print(f"  - {key}")
    
    await engine.dispose()

asyncio.run(explain_storage())