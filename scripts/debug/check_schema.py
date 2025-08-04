#!/usr/bin/env python3
"""
Check database schema for submission_deadline column
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from sqlalchemy import text

async def check_schema():
    async for db in get_db():
        try:
            result = await db.execute(text("""
                SELECT column_name, is_nullable, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'request_info_phases' 
                AND column_name = 'submission_deadline'
            """))
            row = result.fetchone()
            if row:
                print(f'Column: {row[0]}, Nullable: {row[1]}, Type: {row[2]}, Default: {row[3]}')
            else:
                print('Column not found')
                
            # Also check all columns in the table
            result = await db.execute(text("""
                SELECT column_name, is_nullable, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'request_info_phases'
                ORDER BY ordinal_position
            """))
            rows = result.fetchall()
            print("\nAll columns in request_info_phases:")
            for row in rows:
                print(f'  {row[0]}: nullable={row[1]}, type={row[2]}, default={row[3]}')
                
        except Exception as e:
            print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(check_schema()) 