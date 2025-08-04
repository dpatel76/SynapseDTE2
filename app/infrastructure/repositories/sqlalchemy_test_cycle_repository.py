"""SQLAlchemy implementation of TestCycleRepository"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import TestCycle as TestingCycle, CycleReport
from app.domain.entities.test_cycle import TestCycle
from app.domain.value_objects import CycleStatus, ReportAssignment
from app.application.interfaces.repositories import TestCycleRepository


class SQLAlchemyTestCycleRepository(TestCycleRepository):
    """SQLAlchemy implementation of the test cycle repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, cycle_id: int) -> Optional[TestCycle]:
        """Get a test cycle by ID"""
        result = await self.session.execute(
            select(TestingCycle)
            .options(selectinload(TestingCycle.cycle_reports))
            .where(TestingCycle.cycle_id == cycle_id)
        )
        db_cycle = result.scalar_one_or_none()
        
        if not db_cycle:
            return None
        
        return self._to_domain_entity(db_cycle)
    
    async def get_by_name(self, cycle_name: str) -> Optional[TestCycle]:
        """Get a test cycle by name"""
        result = await self.session.execute(
            select(TestingCycle)
            .options(selectinload(TestingCycle.cycle_reports))
            .where(TestingCycle.cycle_name == cycle_name)
        )
        db_cycle = result.scalar_one_or_none()
        
        if not db_cycle:
            return None
        
        return self._to_domain_entity(db_cycle)
    
    async def save(self, cycle: TestCycle) -> TestCycle:
        """Save a test cycle (create or update)"""
        if cycle.id:
            # Update existing
            db_cycle = await self.session.get(TestingCycle, cycle.id)
            if not db_cycle:
                raise ValueError(f"Test cycle with id {cycle.id} not found")
        else:
            # Create new
            db_cycle = TestingCycle()
        
        # Update fields
        db_cycle.cycle_name = cycle.cycle_name
        db_cycle.start_date = cycle.start_date
        db_cycle.end_date = cycle.end_date
        db_cycle.status = cycle.status.value
        db_cycle.created_by = cycle.created_by
        db_cycle.description = cycle.description
        db_cycle.updated_at = datetime.utcnow()
        
        if not cycle.id:
            db_cycle.created_at = cycle.created_at
            self.session.add(db_cycle)
        
        # Update reports
        # First, remove reports that are no longer in the cycle
        existing_report_ids = {cr.report_id for cr in db_cycle.cycle_reports}
        new_report_ids = {r.report_id for r in cycle.reports}
        
        for cr in list(db_cycle.cycle_reports):
            if cr.report_id not in new_report_ids:
                await self.session.delete(cr)
        
        # Add or update reports
        for report_assignment in cycle.reports:
            existing_cr = next(
                (cr for cr in db_cycle.cycle_reports if cr.report_id == report_assignment.report_id),
                None
            )
            
            if existing_cr:
                existing_cr.tester_id = report_assignment.tester_id
                existing_cr.updated_at = datetime.utcnow()
            else:
                cycle_report = CycleReport(
                    cycle_id=db_cycle.cycle_id,
                    report_id=report_assignment.report_id,
                    tester_id=report_assignment.tester_id,
                    added_at=report_assignment.added_at,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.session.add(cycle_report)
        
        await self.session.commit()
        await self.session.refresh(db_cycle)
        
        # Update the domain entity with the new ID if it was created
        if not cycle.id:
            cycle.id = db_cycle.cycle_id
        
        return cycle
    
    async def delete(self, cycle_id: int) -> None:
        """Delete a test cycle"""
        db_cycle = await self.session.get(TestingCycle, cycle_id)
        if db_cycle:
            await self.session.delete(db_cycle)
            await self.session.commit()
    
    async def find_by_status(self, status: CycleStatus) -> List[TestCycle]:
        """Find all cycles with a specific status"""
        result = await self.session.execute(
            select(TestingCycle)
            .options(selectinload(TestingCycle.cycle_reports))
            .where(TestingCycle.status == status.value)
        )
        db_cycles = result.scalars().all()
        
        return [self._to_domain_entity(db_cycle) for db_cycle in db_cycles]
    
    async def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[TestCycle]:
        """Find cycles within a date range"""
        result = await self.session.execute(
            select(TestingCycle)
            .options(selectinload(TestingCycle.cycle_reports))
            .where(
                and_(
                    TestingCycle.start_date >= start_date,
                    TestingCycle.end_date <= end_date
                )
            )
        )
        db_cycles = result.scalars().all()
        
        return [self._to_domain_entity(db_cycle) for db_cycle in db_cycles]
    
    async def find_by_user(self, user_id: int) -> List[TestCycle]:
        """Find cycles created by a specific user"""
        result = await self.session.execute(
            select(TestingCycle)
            .options(selectinload(TestingCycle.cycle_reports))
            .where(TestingCycle.created_by == user_id)
        )
        db_cycles = result.scalars().all()
        
        return [self._to_domain_entity(db_cycle) for db_cycle in db_cycles]
    
    def _to_domain_entity(self, db_cycle: TestingCycle) -> TestCycle:
        """Convert database model to domain entity"""
        cycle = TestCycle(
            cycle_name=db_cycle.cycle_name,
            start_date=db_cycle.start_date,
            end_date=db_cycle.end_date,
            created_by=db_cycle.created_by,
            description=db_cycle.description
        )
        
        # Set internal state
        cycle.id = db_cycle.cycle_id
        cycle._status = CycleStatus(db_cycle.status)
        cycle.created_at = db_cycle.created_at
        cycle.updated_at = db_cycle.updated_at
        
        # Add reports
        cycle._reports = []
        for cr in db_cycle.cycle_reports:
            report_assignment = ReportAssignment(
                report_id=cr.report_id,
                report_name=cr.report.report_name if cr.report else f"Report {cr.report_id}",
                tester_id=cr.tester_id,
                added_at=cr.added_at or cr.created_at
            )
            cycle._reports.append(report_assignment)
        
        return cycle