#!/usr/bin/env python
"""Debug test cycles issue"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def debug_test_cycles():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
    
    # Get test manager user
    test_manager = await conn.fetchrow("""
        SELECT user_id, email, first_name, last_name 
        FROM users 
        WHERE email = 'test.manager@example.com'
    """)
    
    if test_manager:
        print(f"Test Manager: {test_manager['first_name']} {test_manager['last_name']} ({test_manager['email']})")
        print(f"User ID: {test_manager['user_id']}")
        
        # Check test cycles where this user is the test manager
        managed_cycles = await conn.fetch("""
            SELECT cycle_id, cycle_name, status, created_at
            FROM test_cycles
            WHERE test_manager_id = $1
            ORDER BY created_at DESC
        """, test_manager['user_id'])
        
        print(f"\nCycles managed by this user: {len(managed_cycles)}")
        for cycle in managed_cycles[:5]:  # Show first 5
            print(f"  - {cycle['cycle_name']} (Status: {cycle['status']})")
    
    # Check all test cycles
    all_cycles = await conn.fetch("""
        SELECT cycle_id, cycle_name, status, test_manager_id
        FROM test_cycles
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    print(f"\nAll recent test cycles: {len(all_cycles)}")
    for cycle in all_cycles:
        print(f"  - {cycle['cycle_name']} (Manager ID: {cycle['test_manager_id']}, Status: {cycle['status']})")
    
    # Check if there's any permission filtering
    print("\nChecking permissions...")
    permissions = await conn.fetch("""
        SELECT DISTINCT operation, resource
        FROM role_permissions
        WHERE role = 'Test Manager'
        AND resource = 'cycles'
    """)
    
    print("Test Manager permissions on cycles:")
    for perm in permissions:
        print(f"  - {perm['operation']} on {perm['resource']}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(debug_test_cycles())