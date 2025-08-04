#!/usr/bin/env python3
"""Fix phase status to allow submission"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import json

# Database connection - ensure asyncpg driver
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://dt_admin:SecurePass123!@localhost:5432/synapse_dt')
if 'postgresql://' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

async def fix_phase_status():
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Import models
            from app.models.workflow import WorkflowPhase
            
            # Get the Sample Selection phase
            result = await session.execute(
                select(WorkflowPhase).where(
                    WorkflowPhase.cycle_id == 13,
                    WorkflowPhase.report_id == 156,
                    WorkflowPhase.phase_name == "Sample Selection"
                )
            )
            phase = result.scalar_one_or_none()
            
            if phase:
                print(f"Current phase status: {phase.status}")
                
                if phase.status == "Pending Approval":
                    phase.status = "In Progress"
                    print("Updated phase status to: In Progress")
                    
                    await session.commit()
                    print("\nChanges committed successfully!")
                else:
                    print("Phase status is already correct")
                
            else:
                print("Phase not found")
                
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_phase_status())