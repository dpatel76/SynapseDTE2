#!/usr/bin/env python
"""Check why only one cycle is showing"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_issue():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
    
    # Check test cycles with exact query the API would use
    cycles_query = """
        SELECT tc.*, u.first_name, u.last_name, u.email
        FROM test_cycles tc
        LEFT JOIN users u ON tc.test_manager_id = u.user_id
        ORDER BY tc.created_at DESC
        OFFSET 0 LIMIT 10
    """
    
    cycles = await conn.fetch(cycles_query)
    print(f"Cycles returned by query (limit 10): {len(cycles)}")
    
    # Check total count
    count = await conn.fetchval("SELECT COUNT(*) FROM test_cycles")
    print(f"Total cycles in database: {count}")
    
    # Show first few cycles
    print("\nFirst 3 cycles:")
    for i, cycle in enumerate(cycles[:3]):
        print(f"{i+1}. {cycle['cycle_name']} (ID: {cycle['cycle_id']}, Status: {cycle['status']})")
    
    # Check if there's something unique about the one cycle showing
    print("\nChecking for cycle with name 'Complete 9-Phase Test 20250624_072549'...")
    specific_cycle = await conn.fetchrow("""
        SELECT * FROM test_cycles 
        WHERE cycle_name = 'Complete 9-Phase Test 20250624_072549'
    """)
    
    if specific_cycle:
        print(f"Found cycle ID: {specific_cycle['cycle_id']}")
        
        # Check if this cycle has any special properties
        reports_count = await conn.fetchval("""
            SELECT COUNT(*) FROM cycle_reports
            WHERE cycle_id = $1
        """, specific_cycle['cycle_id'])
        
        print(f"Reports in this cycle: {reports_count}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_issue())