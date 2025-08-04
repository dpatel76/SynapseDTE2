"""
Clean Architecture Reports API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_permission
from app.infrastructure.di import get_repository, get_use_case
from app.domain.entities import ReportEntity
from app.application.dtos import ReportDTO, ReportCreateDTO, ReportUpdateDTO, ReportListResponseDTO

router = APIRouter()


@router.get("/", response_model=ReportListResponseDTO)
@require_permission("reports", "read")
async def get_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all reports with pagination"""
    
    # Get repository
    report_repository = get_repository("report_repository")
    
    if not report_repository:
        # Fallback to direct implementation
        from app.models.report import Report
        from sqlalchemy import func
        from sqlalchemy.orm import selectinload
        
        # Build query with relationships
        query = select(Report).options(
            selectinload(Report.lob),
            selectinload(Report.owner)
        )
        conditions = []
        if active_only:
            conditions.append(Report.is_active == True)
        
        # Get total count
        count_query = select(func.count(Report.report_id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
            query = query.where(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        reports = result.scalars().all()
        
        return ReportListResponseDTO(
            reports=[
                ReportDTO(
                    report_id=r.report_id,
                    report_name=r.report_name,
                    regulation=r.regulation,
                    frequency=r.frequency,
                    description=r.description,
                    lob_id=r.lob_id,
                    report_owner_id=r.report_owner_id,
                    is_active=r.is_active,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                    lob_name=r.lob.lob_name if r.lob else None,
                    owner_name=f"{r.owner.first_name} {r.owner.last_name}" if r.owner else None
                )
                for r in reports
            ],
            total=total,
            skip=skip,
            limit=limit
        )
    
    # Use clean architecture implementation
    reports = await report_repository.get_all(
        skip=skip,
        limit=limit,
        active_only=active_only,
        db=db
    )
    
    # Get total count
    total = await report_repository.count(
        active_only=active_only,
        db=db
    )
    
    return ReportListResponseDTO(
        reports=reports,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{report_id}", response_model=ReportDTO)
@require_permission("reports", "read")
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific report by ID"""
    
    # Get repository
    report_repository = get_repository("report_repository")
    
    if not report_repository:
        # Fallback to direct implementation
        from app.models.report import Report
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(Report).options(
                selectinload(Report.lob),
                selectinload(Report.owner)
            ).where(Report.report_id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        return ReportDTO(
            report_id=report.report_id,
            report_name=report.report_name,
            regulation=report.regulation,
            frequency=report.frequency,
            description=report.description,
            lob_id=report.lob_id,
            report_owner_id=report.report_owner_id,
            is_active=report.is_active,
            created_at=report.created_at,
            updated_at=report.updated_at,
            lob_name=report.lob.lob_name if report.lob else None,
            owner_name=f"{report.owner.first_name} {report.owner.last_name}" if report.owner else None
        )
    
    # Use clean architecture implementation
    report = await report_repository.get_by_id(report_id, db)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return report


@router.post("/", response_model=ReportDTO)
@require_permission("reports", "create")
async def create_report(
    report_data: ReportCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new report"""
    
    # Get use case
    create_report_use_case = get_use_case("create_report")
    
    if not create_report_use_case:
        # Fallback to direct implementation
        from app.models.report import Report
        
        # Check if report name already exists
        result = await db.execute(
            select(Report).where(Report.report_name == report_data.report_name)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report with this name already exists"
            )
        
        # Create report
        report = Report(
            report_name=report_data.report_name,
            lob_id=report_data.lob_id,
            report_owner_id=report_data.report_owner_id,
            regulation=report_data.regulation,
            frequency=report_data.frequency,
            description=report_data.description,
            is_active=True,
            created_by=current_user.user_id
        )
        
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        return ReportDTO(
            report_id=report.report_id,
            report_name=report.report_name,
            regulation=report.regulation,
            frequency=report.frequency,
            description=report.description,
            lob_id=report.lob_id,
            report_owner_id=report.report_owner_id,
            is_active=report.is_active,
            created_at=report.created_at,
            updated_at=report.updated_at
        )
    
    # Use clean architecture implementation
    try:
        report = await create_report_use_case.execute(
            report_data=report_data,
            user_id=current_user.user_id,
            db=db
        )
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{report_id}", response_model=ReportDTO)
@require_permission("reports", "update")
async def update_report(
    report_id: int,
    report_data: ReportUpdateDTO,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing report"""
    
    # Get use case
    update_report_use_case = get_use_case("update_report")
    
    if not update_report_use_case:
        # Fallback to direct implementation
        from app.models.report import Report
        from datetime import datetime
        
        result = await db.execute(
            select(Report).where(Report.report_id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Update fields
        if report_data.report_name is not None:
            report.report_name = report_data.report_name
        if report_data.lob_id is not None:
            report.lob_id = report_data.lob_id
        if report_data.report_owner_id is not None:
            report.report_owner_id = report_data.report_owner_id
        if report_data.regulation is not None:
            report.regulation = report_data.regulation
        if report_data.frequency is not None:
            report.frequency = report_data.frequency
        if report_data.description is not None:
            report.description = report_data.description
        if report_data.is_active is not None:
            report.is_active = report_data.is_active
        
        report.updated_at = datetime.utcnow()
        report.updated_by = current_user.user_id
        
        await db.commit()
        await db.refresh(report)
        
        return ReportDTO(
            report_id=report.report_id,
            report_name=report.report_name,
            regulation=report.regulation,
            frequency=report.frequency,
            description=report.description,
            lob_id=report.lob_id,
            report_owner_id=report.report_owner_id,
            is_active=report.is_active,
            created_at=report.created_at,
            updated_at=report.updated_at
        )
    
    # Use clean architecture implementation
    try:
        report = await update_report_use_case.execute(
            report_id=report_id,
            report_data=report_data,
            user_id=current_user.user_id,
            db=db
        )
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{report_id}")
@require_permission("reports", "delete")
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a report (soft delete)"""
    
    # Get use case
    delete_report_use_case = get_use_case("delete_report")
    
    if not delete_report_use_case:
        # Fallback to direct implementation
        from app.models.report import Report
        from datetime import datetime
        
        result = await db.execute(
            select(Report).where(Report.report_id == report_id)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Soft delete
        report.is_active = False
        report.deleted_at = datetime.utcnow()
        report.deleted_by = current_user.user_id
        
        await db.commit()
        
        return {"message": "Report deleted successfully"}
    
    # Use clean architecture implementation
    try:
        await delete_report_use_case.execute(
            report_id=report_id,
            user_id=current_user.user_id,
            db=db
        )
        return {"message": "Report deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{report_id}/attributes", response_model=List[dict])
@require_permission("reports", "read")
async def get_report_attributes(
    report_id: int,
    cycle_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get attributes for a report"""
    
    from app.models.report_attribute import ReportAttribute
    from app.models.workflow import WorkflowPhase
    from sqlalchemy.orm import selectinload
    
    # Query ReportAttribute through the phase relationship since it doesn't have direct report_id/cycle_id fields
    query = select(ReportAttribute).options(selectinload(ReportAttribute.phase)).join(WorkflowPhase).where(
        WorkflowPhase.report_id == report_id
    )
    
    if cycle_id:
        query = query.where(WorkflowPhase.cycle_id == cycle_id)
    
    result = await db.execute(query)
    attributes = result.scalars().all()
    
    return [
        {
            "id": attr.id,
            "attribute_name": attr.attribute_name,
            "description": attr.description,
            "data_type": attr.data_type,
            "mandatory_flag": attr.mandatory_flag,
            "cde_flag": attr.cde_flag,
            "is_scoped": attr.is_scoped,
            "is_primary_key": attr.is_primary_key,
            "testing_approach": attr.testing_approach,
            "line_item_number": getattr(attr, 'line_item_number', None),
            "technical_line_item_name": getattr(attr, 'technical_line_item_name', None),
            "mdrm": getattr(attr, 'mdrm', None),
            "historical_issues_flag": getattr(attr, 'historical_issues_flag', False)
        }
        for attr in attributes
    ]