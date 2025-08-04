"""SQLAlchemy implementation of ReportRepository"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, not_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Report, CycleReport
from app.application.interfaces.repositories import ReportRepository


class SQLAlchemyReportRepository(ReportRepository):
    """SQLAlchemy implementation of the report repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Get a report by ID"""
        result = await self.session.execute(
            select(Report).where(Report.report_id == report_id)
        )
        db_report = result.scalar_one_or_none()
        
        if not db_report:
            return None
        
        return self._to_dict(db_report)
    
    async def get_multiple(self, report_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple reports by IDs"""
        result = await self.session.execute(
            select(Report).where(Report.report_id.in_(report_ids))
        )
        db_reports = result.scalars().all()
        
        return [self._to_dict(report) for report in db_reports]
    
    async def find_by_regulation(self, regulation: str) -> List[Dict[str, Any]]:
        """Find reports by regulation type"""
        result = await self.session.execute(
            select(Report).where(Report.regulation == regulation)
        )
        db_reports = result.scalars().all()
        
        return [self._to_dict(report) for report in db_reports]
    
    async def find_available_for_cycle(self) -> List[Dict[str, Any]]:
        """Find reports available for assignment to cycles"""
        # Find reports that are active and not deleted
        result = await self.session.execute(
            select(Report).where(
                and_(
                    Report.is_active == True,
                    Report.deleted_at.is_(None)
                )
            )
        )
        db_reports = result.scalars().all()
        
        return [self._to_dict(report) for report in db_reports]
    
    def _to_dict(self, db_report: Report) -> Dict[str, Any]:
        """Convert database model to dictionary"""
        return {
            "report_id": db_report.report_id,
            "report_name": db_report.report_name,
            "regulation": db_report.regulation,
            "report_type": db_report.report_type,
            "frequency": db_report.frequency,
            "submission_deadline": db_report.submission_deadline,
            "description": db_report.description,
            "is_active": db_report.is_active,
            "created_at": db_report.created_at,
            "updated_at": db_report.updated_at,
            "metadata": {
                "owner_executive_id": db_report.report_owner_executive_id,
                "last_submission_date": db_report.last_submission_date,
                "next_submission_date": db_report.next_submission_date
            }
        }