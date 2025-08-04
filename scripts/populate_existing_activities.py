#!/usr/bin/env python3
"""
Populate workflow_activities for existing phases that were completed
This ensures the Planning phase shows correct activity status
"""

import asyncio
import os
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def populate_planning_activities(session: AsyncSession):
    """Populate activities for the Planning phase that's already completed"""
    
    # Get the Planning phase data
    result = await session.execute(text("""
        SELECT phase_id, cycle_id, report_id, actual_start_date, actual_end_date, 
               started_by, completed_by, phase_data
        FROM workflow_phases 
        WHERE cycle_id = 21 AND report_id = 156 AND phase_name = 'Planning'
    """))
    
    phase = result.fetchone()
    if not phase:
        print("Planning phase not found")
        return
    
    phase_id, cycle_id, report_id, start_date, end_date, started_by, completed_by, phase_data = phase
    
    # Define the activities for Planning phase
    activities = [
        ('Start Planning Phase', 'start', 1),
        ('Generate Attributes', 'task', 2),
        ('Review Attributes', 'task', 3),
        ('Tester Review', 'review', 4),
        ('Report Owner Approval', 'approval', 5),
        ('Complete Planning Phase', 'complete', 6)
    ]
    
    # Since the phase is completed, all activities should be completed
    for activity_name, activity_type, order in activities:
        # Check if activity already exists
        check_result = await session.execute(text("""
            SELECT COUNT(*) FROM workflow_activities 
            WHERE cycle_id = :cycle_id AND report_id = :report_id 
            AND phase_name = 'Planning' AND activity_name = :activity_name
        """), {
            'cycle_id': cycle_id,
            'report_id': report_id,
            'activity_name': activity_name
        })
        
        if check_result.scalar() > 0:
            print(f"Activity '{activity_name}' already exists, skipping...")
            continue
        
        # Insert the activity as completed
        await session.execute(text("""
            INSERT INTO workflow_activities (
                cycle_id, report_id, phase_name, activity_name, activity_type,
                activity_order, status, can_start, can_complete, is_manual, is_optional,
                started_at, started_by, completed_at, completed_by, created_at, updated_at
            ) VALUES (
                :cycle_id, :report_id, 'Planning', :activity_name, :activity_type,
                :order, 'completed', false, false, true, false,
                :started_at, :started_by, :completed_at, :completed_by, NOW(), NOW()
            )
        """), {
            'cycle_id': cycle_id,
            'report_id': report_id,
            'activity_name': activity_name,
            'activity_type': activity_type,
            'order': order,
            'started_at': start_date,
            'started_by': started_by or 3,  # Default to tester user
            'completed_at': end_date,
            'completed_by': completed_by or 3
        })
        
        print(f"Created completed activity: {activity_name}")
    
    await session.commit()
    print("Planning phase activities populated successfully!")


async def main():
    # Get database URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        db_url = "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt"
    
    # Convert to async URL
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    # Create engine
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        await populate_planning_activities(session)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())