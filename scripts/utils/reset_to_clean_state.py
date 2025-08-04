#!/usr/bin/env python3
"""Reset to a clean state with proper versioning"""

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

async def reset_to_clean_state():
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
                print("Resetting to clean state...")
                
                # Reset all samples to version 1
                samples = phase.phase_data.get('samples', [])
                print(f"\nResetting {len(samples)} samples to version 1...")
                for i, sample in enumerate(samples):
                    phase.phase_data['samples'][i]['version_number'] = 1
                    # Keep the Report Owner decisions that were made
                    # but mark them as version 1 decisions
                    if sample.get('version_reviewed'):
                        phase.phase_data['samples'][i]['version_reviewed'] = 1
                
                # Keep only the first submission and mark it as reviewed
                submissions = phase.phase_data.get('submissions', [])
                if submissions:
                    print(f"\nFound {len(submissions)} submissions, cleaning up...")
                    
                    # Keep first submission, update it to be reviewed
                    first_submission = submissions[0]
                    first_submission['version_number'] = 1
                    first_submission['status'] = 'revision_required'
                    first_submission['reviewed_at'] = first_submission.get('reviewed_at') or datetime.utcnow().isoformat()
                    first_submission['reviewed_by'] = 'Report Owner'
                    first_submission['review_feedback'] = 'Some samples need additional work. Please see individual feedback.'
                    
                    # Replace all submissions with just the cleaned first one
                    phase.phase_data['submissions'] = [first_submission]
                    
                    print("Kept version 1 submission and marked as reviewed")
                
                # Set phase status to In Progress
                phase.status = "In Progress"
                print("\nSet phase status to: In Progress")
                
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(phase, 'phase_data')
                
                await session.commit()
                print("\n✅ Changes committed successfully!")
                
                # Show final state
                print("\nFinal state:")
                print(f"  Phase status: {phase.status}")
                print(f"  Submissions: {len(phase.phase_data.get('submissions', []))}")
                print(f"  Sample versions: All at version 1")
                print("\nThe Tester can now:")
                print("  1. See Report Owner feedback on version 1")
                print("  2. Make changes to samples")
                print("  3. Submit version 2 for approval")
                
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
    asyncio.run(reset_to_clean_state())