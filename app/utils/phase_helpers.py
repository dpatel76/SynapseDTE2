"""
Phase ID Helper Functions

This module provides utilities for converting between phase_id and cycle_id/report_id
to support the hybrid database architecture while maintaining UI compatibility.
"""

from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.workflow import WorkflowPhase


async def get_phase_id(
    db: AsyncSession,
    cycle_id: int,
    report_id: int,
    phase_name: str
) -> Optional[int]:
    """
    Get phase_id from cycle_id, report_id, and phase_name.
    
    Args:
        db: Database session
        cycle_id: Test cycle ID
        report_id: Report ID
        phase_name: Name of the phase (e.g., 'Planning', 'Scoping', 'Data Profiling')
    
    Returns:
        phase_id if found, None otherwise
    """
    result = await db.execute(
        select(WorkflowPhase.phase_id).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id,
                WorkflowPhase.phase_name == phase_name
            )
        )
    )
    phase = result.scalar_one_or_none()
    return phase


async def get_cycle_report_from_phase(
    db: AsyncSession,
    phase_id: int
) -> Optional[Tuple[int, int, str]]:
    """
    Get cycle_id, report_id, and phase_name from phase_id.
    
    Args:
        db: Database session
        phase_id: Phase ID
    
    Returns:
        Tuple of (cycle_id, report_id, phase_name) if found, None otherwise
    """
    result = await db.execute(
        select(
            WorkflowPhase.cycle_id,
            WorkflowPhase.report_id,
            WorkflowPhase.phase_name
        ).where(WorkflowPhase.phase_id == phase_id)
    )
    data = result.first()
    return data if data else None


async def get_all_phases_for_cycle_report(
    db: AsyncSession,
    cycle_id: int,
    report_id: int
) -> list[WorkflowPhase]:
    """
    Get all phases for a specific cycle and report.
    
    Args:
        db: Database session
        cycle_id: Test cycle ID
        report_id: Report ID
    
    Returns:
        List of WorkflowPhase objects
    """
    result = await db.execute(
        select(WorkflowPhase).where(
            and_(
                WorkflowPhase.cycle_id == cycle_id,
                WorkflowPhase.report_id == report_id
            )
        ).order_by(WorkflowPhase.phase_order)
    )
    return result.scalars().all()


async def create_phase_if_not_exists(
    db: AsyncSession,
    cycle_id: int,
    report_id: int,
    phase_name: str,
    phase_order: int = None
) -> int:
    """
    Create a phase if it doesn't exist and return its phase_id.
    
    Args:
        db: Database session
        cycle_id: Test cycle ID
        report_id: Report ID
        phase_name: Name of the phase
        phase_order: Order of the phase (optional)
    
    Returns:
        phase_id of existing or newly created phase
    """
    # First try to get existing phase
    existing_phase_id = await get_phase_id(db, cycle_id, report_id, phase_name)
    if existing_phase_id:
        return existing_phase_id
    
    # Create new phase
    new_phase = WorkflowPhase(
        cycle_id=cycle_id,
        report_id=report_id,
        phase_name=phase_name,
        phase_order=phase_order,
        status='pending',
        state='not_started'
    )
    
    db.add(new_phase)
    await db.flush()  # Get the ID without committing
    return new_phase.phase_id


class PhaseContext:
    """
    Context manager for working with phase-based operations.
    Automatically handles cycle_id/report_id to phase_id conversion.
    """
    
    def __init__(self, db: AsyncSession, cycle_id: int, report_id: int, phase_name: str):
        self.db = db
        self.cycle_id = cycle_id
        self.report_id = report_id
        self.phase_name = phase_name
        self.phase_id: Optional[int] = None
    
    async def __aenter__(self):
        self.phase_id = await get_phase_id(
            self.db, self.cycle_id, self.report_id, self.phase_name
        )
        if not self.phase_id:
            # Create phase if it doesn't exist
            self.phase_id = await create_phase_if_not_exists(
                self.db, self.cycle_id, self.report_id, self.phase_name
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Decorator for API endpoints to automatically convert cycle_id/report_id to phase_id
def with_phase_id(phase_name_param: str = "phase_name"):
    """
    Decorator that automatically converts cycle_id/report_id/phase_name to phase_id.
    
    Usage:
        @with_phase_id()
        async def my_endpoint(cycle_id: int, report_id: int, phase_name: str, phase_id: int, db: AsyncSession):
            # phase_id is automatically injected
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract required parameters
            cycle_id = kwargs.get('cycle_id')
            report_id = kwargs.get('report_id')
            phase_name = kwargs.get(phase_name_param)
            db = kwargs.get('db')
            
            if cycle_id and report_id and phase_name and db:
                # Convert to phase_id
                phase_id = await get_phase_id(db, cycle_id, report_id, phase_name)
                if not phase_id:
                    # Create phase if it doesn't exist
                    phase_id = await create_phase_if_not_exists(
                        db, cycle_id, report_id, phase_name
                    )
                
                # Inject phase_id into kwargs
                kwargs['phase_id'] = phase_id
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator