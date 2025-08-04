#!/usr/bin/env python
"""Check active cycles in detail"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_active_cycles():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
    
    # Get all Active cycles
    active_cycles = await conn.fetch("""
        SELECT cycle_id, cycle_name, status, test_manager_id, created_at
        FROM test_cycles
        WHERE status = 'Active'
        ORDER BY created_at DESC
    """)
    
    print(f"Found {len(active_cycles)} cycles with status 'Active':")
    for cycle in active_cycles:
        print(f"\nCycle ID: {cycle['cycle_id']}")
        print(f"  Name: {cycle['cycle_name']}")
        print(f"  Status: {cycle['status']}")
        print(f"  Test Manager ID: {cycle['test_manager_id']}")
        print(f"  Created: {cycle['created_at']}")
        
        # Check for cycle_reports
        reports_count = await conn.fetchval("""
            SELECT COUNT(*) FROM cycle_reports WHERE cycle_id = $1
        """, cycle['cycle_id'])
        
        print(f"  Reports: {reports_count}")
        
        # Check for observations via cycle_reports
        try:
            obs_count = await conn.fetchval("""
                SELECT COUNT(DISTINCT oe.observation_id)
                FROM observations_enhanced oe
                JOIN reports r ON oe.report_id = r.report_id
                JOIN cycle_reports cr ON r.report_id = cr.report_id
                WHERE cr.cycle_id = $1
            """, cycle['cycle_id'])
        except:
            obs_count = "Error"
        
        print(f"  Observations: {obs_count}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_active_cycles())