#!/usr/bin/env python3
"""Get the correct sample selection version ID"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

async def get_version():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        # Get sample selection phase
        phase_result = await db.execute(text('''
            SELECT phase_id 
            FROM workflow_phases 
            WHERE cycle_id = 55 
            AND report_id = 156 
            AND phase_name = 'Sample Selection'
            AND status = 'Complete'
        '''))
        
        phase_id = phase_result.scalar()
        print(f"Sample Selection phase ID: {phase_id}")
        
        # Get approved version
        version_result = await db.execute(text('''
            SELECT 
                version_id, 
                version_number,
                version_status
            FROM cycle_report_sample_selection_versions 
            WHERE phase_id = :phase_id 
            AND version_status = 'approved'
            ORDER BY version_number DESC 
            LIMIT 1
        '''), {'phase_id': phase_id})
        
        version = version_result.first()
        if version:
            print(f"\nApproved sample selection version:")
            print(f"  Version {version.version_number}")
            print(f"  ID: {version.version_id}")
            print(f"  Status: {version.version_status}")
            
            # Check samples in this version
            samples_result = await db.execute(text('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT lob_id) as unique_lobs,
                    COUNT(CASE WHEN report_owner_decision = 'approved' THEN 1 END) as approved_samples
                FROM cycle_report_sample_selection_samples
                WHERE version_id = :version_id
            '''), {'version_id': version.version_id})
            
            stats = samples_result.first()
            print(f"\n  Sample statistics:")
            print(f"    Total samples: {stats.total}")
            print(f"    Unique LOBs: {stats.unique_lobs}")
            print(f"    Approved samples: {stats.approved_samples}")
            
            # Get the LOB details
            lob_result = await db.execute(text('''
                SELECT DISTINCT 
                    s.lob_id,
                    l.lob_name
                FROM cycle_report_sample_selection_samples s
                JOIN lobs l ON s.lob_id = l.lob_id
                WHERE s.version_id = :version_id
                AND s.report_owner_decision = 'approved'
            '''), {'version_id': version.version_id})
            
            print(f"\n  LOBs in approved samples:")
            for lob in lob_result:
                print(f"    - {lob.lob_name} (ID: {lob.lob_id})")
    
    await engine.dispose()

asyncio.run(get_version())