"""SQLAlchemy implementation of TestCycleRepository"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.interfaces.repositories import TestCycleRepository
from app.domain.entities.test_cycle import TestCycle as TestCycleEntity
from app.domain.value_objects import CycleStatus
from app.models import TestCycle, CycleReport, Report, User


class TestCycleRepositoryImpl(TestCycleRepository):
    """SQLAlchemy implementation of test cycle repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, cycle_id: int) -> Optional[TestCycleEntity]:
        """Get a test cycle by ID"""
        result = await self.session.execute(
            select(TestCycle)
            .where(TestCycle.cycle_id == cycle_id)
            .options(
                selectinload(TestCycle.cycle_reports).selectinload(CycleReport.report),
                selectinload(TestCycle.cycle_reports).selectinload(CycleReport.assigned_tester),
                selectinload(TestCycle.created_by_user)
            )
        )
        db_cycle = result.scalar_one_or_none()
        
        if not db_cycle:
            return None
        
        return self._to_entity(db_cycle)
    
    async def get_by_name(self, cycle_name: str) -> Optional[TestCycleEntity]:
        """Get a test cycle by name"""
        result = await self.session.execute(
            select(TestCycle)
            .where(TestCycle.cycle_name == cycle_name)
            .options(
                selectinload(TestCycle.cycle_reports).selectinload(CycleReport.report),
                selectinload(TestCycle.created_by_user)
            )
        )
        db_cycle = result.scalar_one_or_none()
        
        if not db_cycle:
            return None
        
        return self._to_entity(db_cycle)
    
    async def save(self, cycle: TestCycleEntity) -> TestCycleEntity:
        """Save a test cycle (create or update)"""
        # Check if cycle exists
        if hasattr(cycle, 'cycle_id') and cycle.cycle_id:
            # Update existing
            result = await self.session.execute(
                select(TestCycle).where(TestCycle.cycle_id == cycle.cycle_id)
            )
            db_cycle = result.scalar_one_or_none()
            
            if db_cycle:
                # Update fields
                db_cycle.cycle_name = cycle.cycle_name
                db_cycle.status = cycle.status.value
                db_cycle.start_date = cycle.start_date
                db_cycle.end_date = cycle.end_date
                db_cycle.is_active = cycle.is_active
                db_cycle.metadata = cycle.metadata
                db_cycle.updated_at = datetime.utcnow()
            else:
                raise ValueError(f"Test cycle {cycle.cycle_id} not found")
        else:
            # Create new
            db_cycle = TestCycle(
                cycle_name=cycle.cycle_name,
                status=cycle.status.value,
                start_date=cycle.start_date,
                end_date=cycle.end_date,
                created_by=cycle.created_by,
                is_active=cycle.is_active,
                metadata=cycle.metadata,
                created_at=datetime.utcnow()
            )
            self.session.add(db_cycle)
        
        await self.session.commit()
        await self.session.refresh(db_cycle)
        
        return self._to_entity(db_cycle)
    
    async def delete(self, cycle_id: int) -> None:
        """Delete a test cycle"""
        result = await self.session.execute(
            select(TestCycle).where(TestCycle.cycle_id == cycle_id)
        )
        db_cycle = result.scalar_one_or_none()
        
        if db_cycle:
            await self.session.delete(db_cycle)
            await self.session.commit()
    
    async def find_by_status(self, status: CycleStatus) -> List[TestCycleEntity]:
        """Find all cycles with a specific status"""
        result = await self.session.execute(
            select(TestCycle)
            .where(TestCycle.status == status.value)
            .order_by(TestCycle.created_at.desc())
        )
        db_cycles = result.scalars().all()
        
        return [self._to_entity(cycle) for cycle in db_cycles]
    
    async def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[TestCycleEntity]:
        """Find cycles within a date range"""
        result = await self.session.execute(
            select(TestCycle)
            .where(
                or_(
                    and_(TestCycle.start_date >= start_date, TestCycle.start_date <= end_date),
                    and_(TestCycle.end_date >= start_date, TestCycle.end_date <= end_date),
                    and_(TestCycle.start_date <= start_date, TestCycle.end_date >= end_date)
                )
            )
            .order_by(TestCycle.start_date)
        )
        db_cycles = result.scalars().all()
        
        return [self._to_entity(cycle) for cycle in db_cycles]
    
    async def find_by_user(self, user_id: int) -> List[TestCycleEntity]:
        """Find cycles created by a specific user"""
        result = await self.session.execute(
            select(TestCycle)
            .where(TestCycle.created_by == user_id)
            .order_by(TestCycle.created_at.desc())
        )
        db_cycles = result.scalars().all()
        
        return [self._to_entity(cycle) for cycle in db_cycles]
    
    async def find_active_cycles(self) -> List[TestCycleEntity]:
        """Find all active cycles"""
        result = await self.session.execute(
            select(TestCycle)
            .where(TestCycle.is_active == True)
            .order_by(TestCycle.created_at.desc())
        )
        db_cycles = result.scalars().all()
        
        return [self._to_entity(cycle) for cycle in db_cycles]
    
    def _to_entity(self, db_cycle: TestCycle) -> TestCycleEntity:
        """Convert database model to domain entity"""
        # Map report IDs
        report_ids = []
        if hasattr(db_cycle, 'cycle_reports') and db_cycle.cycle_reports:
            report_ids = [cr.report_id for cr in db_cycle.cycle_reports]
        
        return TestCycleEntity(
            cycle_id=db_cycle.cycle_id,
            cycle_name=db_cycle.cycle_name,
            status=CycleStatus(db_cycle.status),
            start_date=db_cycle.start_date,
            end_date=db_cycle.end_date,
            created_by=db_cycle.created_by,
            is_active=db_cycle.is_active,
            report_ids=report_ids,
            metadata=db_cycle.metadata or {}
        )