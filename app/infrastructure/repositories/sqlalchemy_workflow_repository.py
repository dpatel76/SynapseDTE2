"""SQLAlchemy implementation of WorkflowRepository"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models import WorkflowPhase
from app.application.interfaces.repositories import WorkflowRepository


class SQLAlchemyWorkflowRepository(WorkflowRepository):
    """SQLAlchemy implementation of the workflow repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_phase_status(self, cycle_id: int, report_id: int, phase_name: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific workflow phase"""
        result = await self.session.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
        )
        db_phase = result.scalar_one_or_none()
        
        if not db_phase:
            return None
        
        return self._to_dict(db_phase)
    
    async def save_phase_status(self, cycle_id: int, report_id: int, phase_name: str, status: Dict[str, Any]) -> None:
        """Save the status of a workflow phase"""
        # Check if phase exists
        result = await self.session.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == phase_name
                )
            )
        )
        existing_phase = result.scalar_one_or_none()
        
        if existing_phase:
            # Update existing phase
            existing_phase.status = status.get('status', 'pending')
            existing_phase.actual_start_date = status.get('started_at')
            existing_phase.actual_end_date = status.get('completed_at')
            existing_phase.phase_data = status.get('metadata', {})
            existing_phase.updated_at = datetime.utcnow()
        else:
            # Create new phase
            new_phase = WorkflowPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name=phase_name,
                status=status.get('status', 'pending'),
                actual_start_date=status.get('started_at'),
                actual_end_date=status.get('completed_at'),
                phase_data=status.get('metadata', {}),
                updated_at=datetime.utcnow()
            )
            self.session.add(new_phase)
        
        await self.session.commit()
    
    async def get_all_phases(self, cycle_id: int, report_id: int) -> List[Dict[str, Any]]:
        """Get all workflow phases for a cycle/report"""
        result = await self.session.execute(
            select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id
                )
            ).order_by(WorkflowPhase.phase_id)
        )
        db_phases = result.scalars().all()
        
        return [self._to_dict(phase) for phase in db_phases]
    
    async def can_advance_to_phase(self, cycle_id: int, report_id: int, target_phase: str) -> bool:
        """Check if workflow can advance to target phase"""
        # Define phase dependencies
        phase_dependencies = {
            "Planning": [],
            "Scoping": ["Planning"],
            "Sample Selection": ["Scoping"],
            "Data Owner Identification": ["Scoping"],
            "Request for Information": ["Sample Selection", "Data Owner Identification"],
            "Test Execution": ["Request for Information"],
            "Observation Management": ["Test Execution"],
            "Testing Report": ["Observation Management"]
        }
        
        # Get dependencies for target phase
        dependencies = phase_dependencies.get(target_phase, [])
        
        if not dependencies:
            # No dependencies, can always advance
            return True
        
        # Check if all dependencies are completed
        for dep in dependencies:
            phase_status = await self.get_phase_status(cycle_id, report_id, dep)
            if not phase_status or phase_status.get('status') != 'completed':
                return False
        
        return True
    
    def _to_dict(self, db_phase: WorkflowPhase) -> Dict[str, Any]:
        """Convert database model to dictionary"""
        return {
            "phase_id": db_phase.phase_id,
            "cycle_id": db_phase.cycle_id,
            "report_id": db_phase.report_id,
            "phase_name": db_phase.phase_name,
            "status": db_phase.status,
            "started_at": db_phase.actual_start_date.isoformat() if db_phase.actual_start_date else None,
            "completed_at": db_phase.actual_end_date.isoformat() if db_phase.actual_end_date else None,
            "metadata": db_phase.phase_data or {},
            "created_at": db_phase.created_at.isoformat() if db_phase.created_at else None,
            "updated_at": db_phase.updated_at.isoformat() if db_phase.updated_at else None
        }