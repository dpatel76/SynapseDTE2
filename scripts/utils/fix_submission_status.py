#!/usr/bin/env python3
"""Fix submission status to allow resubmission"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
import json

# Database connection - ensure asyncpg driver
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://dt_admin:SecurePass123!@localhost:5432/synapse_dt')
if 'postgresql://' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

async def fix_submission_status():
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Import models
            from app.models.workflow import WorkflowPhase
            
            # Get the Sample Selection phase for cycle 13, report 156
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
                print("Number of submissions:", len(phase.phase_data.get('submissions', [])))
                
                # Update all pending submissions to match their review status
                updated = False
                for i, submission in enumerate(phase.phase_data.get('submissions', [])):
                    print(f"\nSubmission {i+1}:")
                    print(f"  Version: {submission.get('version_number')}")
                    print(f"  Status: {submission.get('status')}")
                    print(f"  Reviewed: {submission.get('reviewed_at', 'Not reviewed')}")
                    
                    # If submission was reviewed but still shows as pending, fix it
                    if submission.get('reviewed_at') and submission.get('status') == 'pending':
                        # The review set the status to revision_required but it wasn't saved properly
                        if 'review_feedback' in submission:
                            phase.phase_data['submissions'][i]['status'] = 'revision_required'
                            updated = True
                            print(f"  -> Fixed status to: revision_required")
                
                # Also update the main phase status to allow resubmission
                if phase.status == "Pending Approval":
                    phase.status = "In Progress"
                    print(f"\nUpdated phase status from 'Pending Approval' to 'In Progress'")
                
                if updated:
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(phase, 'phase_data')
                
                await session.commit()
                print("\nChanges committed successfully!")
                
                # Show updated status
                print("\nUpdated submissions:")
                for submission in phase.phase_data.get('submissions', []):
                    print(f"  Version {submission.get('version_number')}: {submission.get('status')}")
                
            else:
                print("Phase not found or no phase data")
                
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_submission_status())