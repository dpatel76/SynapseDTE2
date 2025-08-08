"""
Script to update phase names in the database
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from app.core.database import get_db
from app.models.workflow import WorkflowPhase

async def update_phase_names():
    """Update phase names in the database"""
    try:
        async for db in get_db():
            # Update workflow phases
            await db.execute(
                update(WorkflowPhase)
                .where(WorkflowPhase.phase_name == 'Sampling')
                .values(phase_name='Sample Selection')
            )
            await db.commit()
            print('Successfully updated phase names in database')
    except Exception as e:
        print(f'Error updating phase names: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(update_phase_names()) 