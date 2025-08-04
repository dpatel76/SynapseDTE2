#!/usr/bin/env python3
"""
Debug data extraction issues
"""

import asyncio
import asyncpg
from pathlib import Path

# Database configuration - READ ONLY
DB_CONFIG = {
    'host': 'localhost',
    'database': 'synapse_dt',
    'user': 'synapse_user',
    'password': 'synapse_password',
    'port': 5432
}

async def debug_table_extraction():
    """Debug table extraction"""
    # Connect directly with asyncpg
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Try a simple table first
        print("Testing with users table...")
        result = await conn.fetch("SELECT * FROM users LIMIT 1")
        
        if result:
            print(f"Row type: {type(result[0])}")
            print(f"Row attributes: {dir(result[0])}")
            
            # Try different ways to convert to dict
            row = result[0]
            
            # Method 1: Direct dict conversion
            try:
                dict1 = dict(row)
                print("Method 1 (dict(row)) worked:", dict1)
            except Exception as e:
                print(f"Method 1 failed: {e}")
                
            # Method 2: Using items()
            try:
                dict2 = dict(row.items())
                print("Method 2 (dict(row.items())) worked:", dict2)
            except Exception as e:
                print(f"Method 2 failed: {e}")
                
            # Method 3: Manual iteration
            try:
                dict3 = {}
                for key in row.keys():
                    dict3[key] = row[key]
                print("Method 3 (manual iteration) worked:", dict3)
            except Exception as e:
                print(f"Method 3 failed: {e}")
                
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(debug_table_extraction())