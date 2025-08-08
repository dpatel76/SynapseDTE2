#!/usr/bin/env python3
"""
Populate workflow_activities for all existing phases
"""

import asyncio
import os
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Activity definitions for each phase
PHASE_ACTIVITIES = {
    "Planning": [
        ("Start Planning Phase", "start", 1),
        ("Generate Attributes", "task", 2),
        ("Review Attributes", "task", 3),
        ("Tester Review", "review", 4),
        ("Report Owner Approval", "approval", 5),
        ("Complete Planning Phase", "complete", 6)
    ],
    "Data Profiling": [
        ("Start Data Profiling", "start", 1),
        ("Profile Data Sources", "task", 2),
        ("Document Findings", "task", 3),
        ("Complete Data Profiling", "complete", 4)
    ],
    "Scoping": [
        ("Start Scoping Phase", "start", 1),
        ("Define Scope", "task", 2),
        ("Tester Review", "review", 3),
        ("Report Owner Approval", "approval", 4),
        ("Complete Scoping Phase", "complete", 5)
    ],
    "Sample Selection": [
        ("Start Sample Selection", "start", 1),
        ("Generate Samples", "task", 2),
        ("Review Samples", "task", 3),
        ("Complete Sample Selection", "complete", 4)
    ],
    "Data Provider ID": [
        ("Start Data Provider ID", "start", 1),
        ("LOB Executive Assignment", "task", 2),
        ("Data Owner Assignment", "task", 3),
        ("Data Provider Assignment", "task", 4),
        ("Complete Provider ID", "complete", 5)
    ],
    "Data Owner ID": [
        ("Start Data Owner ID", "start", 1),
        ("Assign LOB Executives", "task", 2),
        ("Assign Data Owners", "task", 3),
        ("Complete Data Owner ID", "complete", 4)
    ],
    "Request Info": [
        ("Start Request Info", "start", 1),
        ("Generate Test Cases", "task", 2),
        ("Data Provider Upload", "task", 3),
        ("Complete Request Info", "complete", 4)
    ],
    "Test Execution": [
        ("Start Test Execution", "start", 1),
        ("Execute Tests", "task", 2),
        ("Document Results", "task", 3),
        ("Complete Test Execution", "complete", 4)
    ],
    "Observation Management": [
        ("Start Observations", "start", 1),
        ("Create Observations", "task", 2),
        ("Data Provider Response", "task", 3),
        ("Finalize Observations", "task", 4),
        ("Complete Observations", "complete", 5)
    ],
    "Test Report": [
        ("Start Test Report", "start", 1),
        ("Generate Report", "task", 2),
        ("Review Report", "review", 3),
        ("Approve Report", "approval", 4),
        ("Complete Test Report", "complete", 5)
    ]
}


async def populate_phase_activities(session: AsyncSession, cycle_id: int, report_id: int):
    """Populate activities for all phases"""
    
    # Get all workflow phases for this cycle/report
    result = await session.execute(text("""
        SELECT phase_name, state, actual_start_date, actual_end_date, 
               started_by, completed_by
        FROM workflow_phases 
        WHERE cycle_id = :cycle_id AND report_id = :report_id
    """), {
        'cycle_id': cycle_id,
        'report_id': report_id
    })
    
    phases = result.fetchall()
    
    for phase_name, state, start_date, end_date, started_by, completed_by in phases:
        activities = PHASE_ACTIVITIES.get(phase_name, [])
        
        if not activities:
            print(f"No activities defined for phase: {phase_name}")
            continue
        
        print(f"\nProcessing {phase_name} phase (state: {state})...")
        
        # Determine activity states based on phase state
        if state == 'Complete':
            # All activities are completed
            for activity_name, activity_type, order in activities:
                await create_activity(
                    session, cycle_id, report_id, phase_name,
                    activity_name, activity_type, order,
                    'completed', start_date, end_date, started_by, completed_by
                )
        elif state == 'In Progress':
            # Some activities may be completed
            for i, (activity_name, activity_type, order) in enumerate(activities):
                if i == 0:  # First activity is completed
                    await create_activity(
                        session, cycle_id, report_id, phase_name,
                        activity_name, activity_type, order,
                        'completed', start_date, None, started_by, started_by
                    )
                elif i == 1:  # Second activity is in progress
                    await create_activity(
                        session, cycle_id, report_id, phase_name,
                        activity_name, activity_type, order,
                        'in_progress', start_date, None, started_by, None
                    )
                else:  # Rest are not started
                    await create_activity(
                        session, cycle_id, report_id, phase_name,
                        activity_name, activity_type, order,
                        'not_started', None, None, None, None
                    )
        else:  # Not Started
            # All activities are not started
            for activity_name, activity_type, order in activities:
                await create_activity(
                    session, cycle_id, report_id, phase_name,
                    activity_name, activity_type, order,
                    'not_started', None, None, None, None
                )
    
    await session.commit()
    print("\nAll phase activities populated successfully!")


async def create_activity(session, cycle_id, report_id, phase_name, 
                         activity_name, activity_type, order,
                         status, started_at, completed_at, started_by, completed_by):
    """Create a single activity if it doesn't exist"""
    
    # Check if activity already exists
    check_result = await session.execute(text("""
        SELECT COUNT(*) FROM workflow_activities 
        WHERE cycle_id = :cycle_id AND report_id = :report_id 
        AND phase_name = :phase_name AND activity_name = :activity_name
    """), {
        'cycle_id': cycle_id,
        'report_id': report_id,
        'phase_name': phase_name,
        'activity_name': activity_name
    })
    
    if check_result.scalar() > 0:
        print(f"  - Activity '{activity_name}' already exists")
        return
    
    # Determine can_start and can_complete based on status
    can_start = (status == 'not_started' and order == 1)  # Only first activity can start initially
    can_complete = (status == 'in_progress')
    
    # Insert the activity
    await session.execute(text("""
        INSERT INTO workflow_activities (
            cycle_id, report_id, phase_name, activity_name, activity_type,
            activity_order, status, can_start, can_complete, is_manual, is_optional,
            started_at, started_by, completed_at, completed_by, created_at, updated_at
        ) VALUES (
            :cycle_id, :report_id, :phase_name, :activity_name, :activity_type,
            :order, :status, :can_start, :can_complete, true, false,
            :started_at, :started_by, :completed_at, :completed_by, NOW(), NOW()
        )
    """), {
        'cycle_id': cycle_id,
        'report_id': report_id,
        'phase_name': phase_name,
        'activity_name': activity_name,
        'activity_type': activity_type,
        'order': order,
        'status': status,
        'can_start': can_start,
        'can_complete': can_complete,
        'started_at': started_at,
        'started_by': started_by,
        'completed_at': completed_at,
        'completed_by': completed_by
    })
    
    print(f"  + Created {status} activity: {activity_name}")


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
        # Populate activities for cycle 21, report 156
        await populate_phase_activities(session, 21, 156)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())