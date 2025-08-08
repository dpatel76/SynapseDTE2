import asyncio
import sys
sys.path.append('.')
from app.core.database import get_db
from app.models.testing_execution import TestExecution
from sqlalchemy import delete

async def reset_test_executions():
    async for db in get_db():
        try:
            # Delete all test execution records
            result = await db.execute(delete(TestExecution))
            await db.commit()
            print(f'Successfully deleted {result.rowcount} test execution records')
            break
        except Exception as e:
            print(f'Error: {e}')
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(reset_test_executions()) 