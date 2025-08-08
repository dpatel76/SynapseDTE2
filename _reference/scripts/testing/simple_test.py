import sys
sys.path.append('.')
from app.core.database import AsyncSessionLocal
from app.models.request_info import TestCase
from sqlalchemy.orm import selectinload
from sqlalchemy import select
import asyncio

async def test():
    async with AsyncSessionLocal() as db:
        query = select(TestCase).options(
            selectinload(TestCase.cycle),
            selectinload(TestCase.report)
        ).where(TestCase.data_owner_id == 6).limit(1)
        
        result = await db.execute(query)
        test_cases = result.scalars().all()
        
        if test_cases:
            tc = test_cases[0]
            print('Cycle:', tc.cycle.cycle_name if tc.cycle else 'None')
            print('Report:', tc.report.report_name if tc.report else 'None')
            
            # Test the exact API logic
            cycle_name = tc.cycle.cycle_name if tc.cycle else f"Cycle {tc.cycle_id}"
            report_name = tc.report.report_name if tc.report else f"Report {tc.report_id}"
            print(f'API would return cycle_name: {cycle_name}')
            print(f'API would return report_name: {report_name}')
        else:
            print('No test cases found')

asyncio.run(test()) 