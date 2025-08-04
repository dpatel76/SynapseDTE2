"""
Add Preparing Test Report enum value and phases to existing reports
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.workflow import WorkflowPhase
from datetime import datetime, timedelta

async def add_enum_value_and_phases():
    """Add enum value and create Preparing Test Report phases"""
    
    # First, add the enum value using synchronous connection
    sync_url = settings.database_url.replace('postgresql+asyncpg://', 'postgresql://')
    sync_engine = create_engine(sync_url)
    
    with sync_engine.connect() as conn:
        try:
            # Add the enum value if it doesn't exist
            conn.execute(text("ALTER TYPE workflow_phase_enum ADD VALUE IF NOT EXISTS 'Preparing Test Report'"))
            conn.commit()
            print("Successfully added 'Preparing Test Report' to workflow_phase_enum")
        except Exception as e:
            print(f"Note: {e}")
            # Continue anyway, it might already exist
    
    # Now add the phases using async connection
    async_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(async_url, echo=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        try:
            # Find all unique cycle_id, report_id combinations
            result = await session.execute(
                text("""
                    SELECT DISTINCT cycle_id, report_id 
                    FROM workflow_phases 
                    WHERE cycle_id IS NOT NULL AND report_id IS NOT NULL
                """)
            )
            report_combinations = result.fetchall()
            
            print(f"\nFound {len(report_combinations)} reports to check")
            
            added_count = 0
            for cycle_id, report_id in report_combinations:
                # Check if Preparing Test Report phase exists
                result = await session.execute(
                    text("""
                        SELECT 1 FROM workflow_phases 
                        WHERE cycle_id = :cycle_id 
                        AND report_id = :report_id 
                        AND phase_name = 'Preparing Test Report'
                    """),
                    {"cycle_id": cycle_id, "report_id": report_id}
                )
                exists = result.scalar()
                
                if not exists:
                    # Get the Observations phase to determine dates
                    result = await session.execute(
                        text("""
                            SELECT planned_end_date, actual_end_date 
                            FROM workflow_phases 
                            WHERE cycle_id = :cycle_id 
                            AND report_id = :report_id 
                            AND phase_name = 'Observations'
                        """),
                        {"cycle_id": cycle_id, "report_id": report_id}
                    )
                    obs_phase = result.fetchone()
                    
                    if obs_phase:
                        # Calculate dates based on Observations phase
                        if obs_phase.planned_end_date:
                            planned_start = obs_phase.planned_end_date
                            planned_end = planned_start + timedelta(days=7)
                        else:
                            planned_start = datetime.utcnow()
                            planned_end = planned_start + timedelta(days=7)
                        
                        # Create the phase
                        phase = WorkflowPhase(
                            cycle_id=cycle_id,
                            report_id=report_id,
                            phase_name='Preparing Test Report',
                            status='Not Started',
                            state='Not Started',
                            schedule_status='On Track',
                            planned_start_date=planned_start,
                            planned_end_date=planned_end
                        )
                        session.add(phase)
                        added_count += 1
                        print(f"Added Preparing Test Report phase for cycle {cycle_id}, report {report_id}")
                    else:
                        print(f"Warning: No Observations phase found for cycle {cycle_id}, report {report_id}")
            
            await session.commit()
            print(f"\nSuccessfully added {added_count} Preparing Test Report phases!")
            
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(add_enum_value_and_phases())