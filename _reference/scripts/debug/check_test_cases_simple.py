#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from sqlalchemy import text
from app.core.database import get_db

async def check_test_cases():
    async for db in get_db():
        result = await db.execute(text('SELECT COUNT(*) FROM test_cases WHERE cycle_id = 9 AND report_id = 156'))
        count = result.scalar()
        print(f'Test cases for cycle 9, report 156: {count}')
        
        if count > 0:
            result = await db.execute(text('SELECT test_case_id, attribute_name, sample_identifier, status FROM test_cases WHERE cycle_id = 9 AND report_id = 156 LIMIT 5'))
            rows = result.fetchall()
            print('Sample test cases:')
            for row in rows:
                print(f'  {row[0]}: {row[1]} - {row[2]} ({row[3]})')
        break

if __name__ == "__main__":
    asyncio.run(check_test_cases()) 