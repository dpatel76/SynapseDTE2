"""SQLAlchemy implementation of ReportRepository"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.interfaces.repositories import ReportRepository
from app.models import Report, ReportOwner, CycleReport, LOB, TestCycle


class ReportRepositoryImpl(ReportRepository):
    """SQLAlchemy implementation of report repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Get a report by ID"""
        result = await self.session.execute(
            select(Report)
            .where(Report.report_id == report_id)
            .options(
                selectinload(Report.lob_relation),
                selectinload(Report.report_owners).selectinload(ReportOwner.owner)
            )
        )
        report = result.scalar_one_or_none()
        
        if not report:
            return None
        
        return self._to_dict(report)
    
    async def get_multiple(self, report_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple reports by IDs"""
        result = await self.session.execute(
            select(Report)
            .where(Report.report_id.in_(report_ids))
            .options(
                selectinload(Report.lob_relation),
                selectinload(Report.report_owners).selectinload(ReportOwner.owner)
            )
        )
        reports = result.scalars().all()
        
        return [self._to_dict(report) for report in reports]
    
    async def find_by_regulation(self, regulation: str) -> List[Dict[str, Any]]:
        """Find reports by regulation type"""
        result = await self.session.execute(
            select(Report)
            .where(Report.regulation == regulation)
            .order_by(Report.report_name)
        )
        reports = result.scalars().all()
        
        return [self._to_dict(report) for report in reports]
    
    async def find_available_for_cycle(self) -> List[Dict[str, Any]]:
        """Find reports available for assignment to cycles"""
        # Get reports that are active and not already in an active cycle
        subquery = select(CycleReport.report_id).join(
            TestCycle
        ).where(
            TestCycle.is_active == True
        ).subquery()
        
        result = await self.session.execute(
            select(Report)
            .where(
                and_(
                    Report.is_active == True,
                    Report.report_id.notin_(subquery)
                )
            )
            .order_by(Report.report_name)
        )
        reports = result.scalars().all()
        
        return [self._to_dict(report) for report in reports]
    
    async def find_by_owner(self, owner_id: int) -> List[Dict[str, Any]]:
        """Find reports owned by a specific user"""
        result = await self.session.execute(
            select(Report)
            .join(ReportOwner)
            .where(ReportOwner.owner_id == owner_id)
            .order_by(Report.report_name)
        )
        reports = result.scalars().all()
        
        return [self._to_dict(report) for report in reports]
    
    async def find_by_lob(self, lob_id: int) -> List[Dict[str, Any]]:
        """Find reports by line of business"""
        result = await self.session.execute(
            select(Report)
            .where(Report.lob_id == lob_id)
            .order_by(Report.report_name)
        )
        reports = result.scalars().all()
        
        return [self._to_dict(report) for report in reports]
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search reports by name or description"""
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(Report)
            .where(
                or_(
                    Report.report_name.ilike(search_pattern),
                    Report.report_description.ilike(search_pattern)
                )
            )
            .order_by(Report.report_name)
        )
        reports = result.scalars().all()
        
        return [self._to_dict(report) for report in reports]
    
    async def get_report_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics about reports"""
        # Total reports
        total_result = await self.session.execute(
            select(func.count(Report.report_id))
        )
        total_count = total_result.scalar() or 0
        
        # Reports by regulation
        regulation_result = await self.session.execute(
            select(
                Report.regulation,
                func.count(Report.report_id)
            ).group_by(Report.regulation)
        )
        regulation_counts = {row[0]: row[1] for row in regulation_result}
        
        # Reports by LOB
        lob_result = await self.session.execute(
            select(
                LOB.lob_name,
                func.count(Report.report_id)
            ).join(LOB).group_by(LOB.lob_name)
        )
        lob_counts = {row[0]: row[1] for row in lob_result}
        
        return {
            "total_reports": total_count,
            "by_regulation": regulation_counts,
            "by_lob": lob_counts
        }
    
    def _to_dict(self, report: Report) -> Dict[str, Any]:
        """Convert database model to dictionary"""
        return {
            "report_id": report.report_id,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "report_description": report.report_description,
            "regulation": report.regulation,
            "lob_id": report.lob_id,
            "lob_name": report.lob_relation.lob_name if report.lob_relation else None,
            "frequency": report.frequency,
            "submission_deadline": report.submission_deadline,
            "data_sources": report.data_sources,
            "complexity_level": report.complexity_level,
            "is_active": report.is_active,
            "metadata": report.metadata or {},
            "created_at": report.created_at,
            "updated_at": report.updated_at,
            "owners": [
                {
                    "owner_id": ro.owner_id,
                    "owner_name": ro.owner.full_name if ro.owner else None,
                    "owner_email": ro.owner.email if ro.owner else None
                }
                for ro in report.report_owners
            ] if hasattr(report, 'report_owners') else []
        }