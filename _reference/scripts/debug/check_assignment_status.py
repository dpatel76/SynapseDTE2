import asyncio
import sys
sys.path.append('.')
from app.database import get_db
from app.models.data_owner import DataProviderAssignment
from sqlalchemy import select

async def check_assignments():
    async for db in get_db():
        result = await db.execute(
            select(DataProviderAssignment)
            .where(DataProviderAssignment.cycle_id == 9)
            .where(DataProviderAssignment.report_id == 156)
            .where(DataProviderAssignment.attribute_id.in_([274, 306]))
        )
        assignments = result.scalars().all()
        for assignment in assignments:
            print(f'Attribute {assignment.attribute_id}: status="{assignment.status}", data_owner_id={assignment.data_owner_id}')
        break

if __name__ == "__main__":
    asyncio.run(check_assignments()) 