#!/usr/bin/env python3
"""
Script to populate plan dates for workflow phases based on cycle dates
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.workflow import WorkflowPhase
from app.models.test_cycle import TestCycle
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define phase durations in days
PHASE_DURATIONS = {
    'Planning': 7,
    'Data Profiling': 5,
    'Scoping': 7,
    'Sample Selection': 5,
    'Data Provider ID': 3,
    'Request Info': 7,
    'Testing': 14,
    'Test Execution': 14,  # Handle both variants
    'Observations': 7,
    'Finalize Test Report': 5
}

# Define phase order
PHASE_ORDER = [
    'Planning',
    'Data Profiling',
    'Scoping',
    'Sample Selection',
    'Data Provider ID',
    'Request Info',
    'Testing',
    'Test Execution',
    'Observations',
    'Finalize Test Report'
]


async def populate_phase_dates(db: AsyncSession, cycle_id: int, report_id: int = None):
    """Populate plan dates for workflow phases in a specific cycle"""
    
    # Get cycle information
    cycle_result = await db.execute(
        select(TestCycle).where(TestCycle.cycle_id == cycle_id)
    )
    cycle = cycle_result.scalar_one_or_none()
    
    if not cycle:
        print(f"Cycle {cycle_id} not found")
        return
    
    # Use cycle start date as baseline, or current date if not set
    baseline_date = cycle.start_date if cycle.start_date else datetime.now().date()
    
    # Build query for workflow phases
    query = select(WorkflowPhase).where(
        WorkflowPhase.cycle_id == cycle_id
    )
    
    if report_id:
        query = query.where(WorkflowPhase.report_id == report_id)
    
    # Get all workflow phases
    result = await db.execute(query.order_by(WorkflowPhase.phase_id))
    phases = result.scalars().all()
    
    if not phases:
        print(f"No workflow phases found for cycle {cycle_id}")
        return
    
    print(f"Found {len(phases)} phases to update")
    
    # Group phases by report
    phases_by_report = {}
    for phase in phases:
        if phase.report_id not in phases_by_report:
            phases_by_report[phase.report_id] = []
        phases_by_report[phase.report_id].append(phase)
    
    # Update phases for each report
    updated_count = 0
    for report_id, report_phases in phases_by_report.items():
        print(f"\nProcessing report {report_id}...")
        
        # Sort phases by the defined order
        sorted_phases = sorted(report_phases, key=lambda p: PHASE_ORDER.index(p.phase_name) if p.phase_name in PHASE_ORDER else 999)
        
        # Calculate dates for each phase
        current_start = baseline_date
        
        for phase in sorted_phases:
            # Only update if dates are not already set
            if not phase.planned_start_date or not phase.planned_end_date:
                # Get phase duration
                duration = PHASE_DURATIONS.get(phase.phase_name, 7)  # Default 7 days
                
                # Set dates
                phase.planned_start_date = current_start
                phase.planned_end_date = current_start + timedelta(days=duration - 1)
                
                print(f"  - {phase.phase_name}: {phase.planned_start_date} to {phase.planned_end_date} ({duration} days)")
                updated_count += 1
                
                # Next phase starts after this one ends
                current_start = phase.planned_end_date + timedelta(days=1)
            else:
                print(f"  - {phase.phase_name}: Already has dates ({phase.planned_start_date} to {phase.planned_end_date})")
    
    # Commit changes
    if updated_count > 0:
        await db.commit()
        print(f"\nSuccessfully updated {updated_count} phases")
    else:
        print("\nNo phases needed updating")


async def main():
    """Main function"""
    # Create async engine
    database_url = os.getenv('DATABASE_URL', 'postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt')
    async_database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(
        async_database_url,
        echo=False
    )
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # You can modify these values to target specific cycles/reports
        cycle_id = 50  # Target cycle 50
        report_id = 156  # Target specific report, or None for all reports in cycle
        
        print(f"Populating workflow phase dates for cycle {cycle_id}")
        if report_id:
            print(f"Targeting specific report: {report_id}")
        
        await populate_phase_dates(session, cycle_id, report_id)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())