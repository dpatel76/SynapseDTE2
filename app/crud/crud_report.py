from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.report import Report
from app.models.test_execution import TestExecutionPhase
from app.schemas.report import ReportCreate, ReportUpdate

class CRUDReport(CRUDBase[Report, ReportCreate, ReportUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Report]:
        return db.query(Report).filter(Report.report_name == name).first()
    
    def get_multi_by_lob(
        self, db: Session, *, lob_id: int, skip: int = 0, limit: int = 100
    ) -> List[Report]:
        return (
            db.query(Report)
            .filter(Report.lob_id == lob_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Report]:
        return (
            db.query(Report)
            .filter(Report.report_owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def search(
        self,
        db: Session,
        *,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[Report]:
        query = db.query(Report)
        
        if filters.get("lob_id"):
            query = query.filter(Report.lob_id == filters["lob_id"])
        
        if filters.get("report_owner_id"):
            query = query.filter(Report.report_owner_id == filters["report_owner_id"])
        
        if filters.get("regulation"):
            query = query.filter(Report.regulation == filters["regulation"])
        
        if filters.get("is_active") is not None:
            query = query.filter(Report.is_active == filters["is_active"])
        
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Report.report_name.ilike(search_term),
                    Report.regulation.ilike(search_term)
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    def create_testing_phase(
        self,
        db: Session,
        *,
        report_id: int,
        cycle_id: int,
        planned_start_date: Optional[datetime] = None,
        planned_end_date: Optional[datetime] = None,
        testing_deadline: datetime,
        test_strategy: Optional[str] = None,
        instructions: Optional[str] = None,
        started_by: int
    ) -> TestExecutionPhase:
        """Create a new testing execution phase"""
        phase = TestExecutionPhase(
            report_id=report_id,
            cycle_id=cycle_id,
            planned_start_date=planned_start_date,
            planned_end_date=planned_end_date,
            testing_deadline=testing_deadline,
            test_strategy=test_strategy,
            instructions=instructions,
            phase_status="In Progress",
            started_at=datetime.utcnow(),
            started_by=started_by
        )
        db.add(phase)
        db.commit()
        db.refresh(phase)
        return phase
    
    def get_testing_phase(
        self,
        db: Session,
        *,
        phase_id: str
    ) -> Optional[TestExecutionPhase]:
        """Get a testing execution phase by ID"""
        return db.query(TestExecutionPhase).filter(
            TestExecutionPhase.phase_id == phase_id
        ).first()
    
    def update_testing_phase(
        self,
        db: Session,
        *,
        phase_id: str,
        planned_start_date: Optional[datetime] = None,
        planned_end_date: Optional[datetime] = None,
        testing_deadline: Optional[datetime] = None,
        test_strategy: Optional[str] = None,
        instructions: Optional[str] = None
    ) -> TestExecutionPhase:
        """Update a testing execution phase"""
        phase = self.get_testing_phase(db, phase_id=phase_id)
        if not phase:
            return None
        
        if planned_start_date is not None:
            phase.planned_start_date = planned_start_date
        if planned_end_date is not None:
            phase.planned_end_date = planned_end_date
        if testing_deadline is not None:
            phase.testing_deadline = testing_deadline
        if test_strategy is not None:
            phase.test_strategy = test_strategy
        if instructions is not None:
            phase.instructions = instructions
        
        db.commit()
        db.refresh(phase)
        return phase

crud_report = CRUDReport(Report) 