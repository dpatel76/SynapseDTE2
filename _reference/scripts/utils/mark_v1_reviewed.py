#!/usr/bin/env python3
"""Mark version 1 as reviewed to allow new submission"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime
import json

# Database connection - ensure asyncpg driver
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://dt_admin:SecurePass123!@localhost:5432/synapse_dt')
if 'postgresql://' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

async def mark_v1_reviewed():
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
            
            if phase and phase.phase_data:
                print("Found phase, updating submissions...")
                
                # Mark version 1 as reviewed (simulating that it was already reviewed in the past)
                for i, submission in enumerate(phase.phase_data.get('submissions', [])):
                    if submission.get('version_number') == 1 and submission.get('status') == 'pending':
                        print(f"\nUpdating Version 1 submission...")
                        phase.phase_data['submissions'][i]['status'] = 'revision_required'
                        phase.phase_data['submissions'][i]['reviewed_at'] = datetime.utcnow().isoformat()
                        phase.phase_data['submissions'][i]['reviewed_by'] = 'Report Owner'
                        phase.phase_data['submissions'][i]['review_feedback'] = 'Initial review - changes required'
                        print(f"  -> Marked as revision_required")
                
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(phase, 'phase_data')
                
                await session.commit()
                print("\nChanges committed successfully!")
                
                # Show all submissions
                print("\nCurrent submissions:")
                for submission in phase.phase_data.get('submissions', []):
                    print(f"  Version {submission.get('version_number')}: {submission.get('status')} (Reviewed: {'Yes' if submission.get('reviewed_at') else 'No'})")
                
            else:
                print("Phase not found")
                
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(mark_v1_reviewed())