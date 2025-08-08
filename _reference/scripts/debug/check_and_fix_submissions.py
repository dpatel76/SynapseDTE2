#!/usr/bin/env python3
"""Check and fix all submissions to allow new submission"""

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

async def check_and_fix_submissions():
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
                print("Current phase status:", phase.status)
                print("\nAll submissions:")
                
                # Show all submissions
                submissions = phase.phase_data.get('submissions', [])
                for i, submission in enumerate(submissions):
                    print(f"\nSubmission {i+1}:")
                    print(f"  Version: {submission.get('version_number')}")
                    print(f"  Status: {submission.get('status')}")
                    print(f"  Submission ID: {submission.get('submission_id')}")
                    print(f"  Reviewed: {'Yes' if submission.get('reviewed_at') else 'No'}")
                    
                    # Fix any pending submissions
                    if submission.get('status') == 'pending':
                        print(f"  -> FIXING: Marking as revision_required")
                        phase.phase_data['submissions'][i]['status'] = 'revision_required'
                        phase.phase_data['submissions'][i]['reviewed_at'] = datetime.utcnow().isoformat()
                        phase.phase_data['submissions'][i]['reviewed_by'] = 'System Fix'
                        phase.phase_data['submissions'][i]['review_feedback'] = 'Marked as reviewed to allow new submission'
                
                # Also show sample versions
                print("\n\nSample versions:")
                samples = phase.phase_data.get('samples', [])
                version_counts = {}
                for sample in samples:
                    version = sample.get('version_number', 1)
                    version_counts[version] = version_counts.get(version, 0) + 1
                
                for version, count in sorted(version_counts.items()):
                    print(f"  Version {version}: {count} samples")
                
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(phase, 'phase_data')
                
                await session.commit()
                print("\n\nChanges committed successfully!")
                print("You should now be able to submit new samples.")
                
            else:
                print("Phase not found")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_and_fix_submissions())